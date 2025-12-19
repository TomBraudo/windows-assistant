"""
MEMORY-OPTIMIZED OmniParser Server for RunPod
Includes aggressive memory cleanup to prevent leaks
"""

import torch
import gc
import io
import base64
import gradio as gr
from PIL import Image
from util.utils import check_ocr_box, get_yolo_model, get_caption_model_processor, get_som_labeled_img
import time

# --- GLOBAL SETTINGS ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 STARTING SERVER ON DEVICE: {DEVICE}")

# --- LOAD MODELS ONCE (Global Scope) ---
print("⏳ Loading YOLO Model...")
yolo_model = get_yolo_model(model_path="weights/icon_detect/model.pt")
yolo_model.to(DEVICE)

print("⏳ Loading Florence-2 Model...")
caption_model_processor = get_caption_model_processor(
    model_name="florence2",
    model_name_or_path="weights/icon_caption_florence"
)

# Ensure Florence model is on GPU
if hasattr(caption_model_processor, 'model'):
    caption_model_processor['model'].to(DEVICE)

print("✅ ALL MODELS LOADED! READY FOR REQUESTS.")

# --- MEMORY TRACKING ---
def log_memory():
    """Log current memory usage"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**3  # GB
        reserved = torch.cuda.memory_reserved(0) / 1024**3    # GB
        print(f"🧠 GPU Memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")

def aggressive_cleanup():
    """Aggressively clear memory"""
    # Clear Python garbage
    gc.collect()
    
    # Clear CUDA cache if available
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    
    print("🧹 Memory cleanup completed")

def process_image(image_input, box_threshold, iou_threshold):
    """
    Process image with OmniParser and return labeled image + JSON.
    Includes aggressive memory cleanup to prevent leaks.
    """
    start_time = time.time()
    use_paddleocr = True
    imgsz = 640
    
    # Variables to track for cleanup
    ocr_bbox_rslt = None
    text = None
    ocr_bbox = None
    dino_labled_img = None
    label_coordinates = None
    parsed_content_list = None
    output_image = None
    
    try:
        log_memory()  # Log initial state
        
        # 1. CONFIGURATION
        # Calculate dynamic box thickness based on image width
        box_overlay_ratio = image_input.size[0] / 3200
        draw_bbox_config = {
            'text_scale': 0.8 * box_overlay_ratio,
            'text_thickness': max(int(2 * box_overlay_ratio), 1),
            'text_padding': max(int(3 * box_overlay_ratio), 1),
            'thickness': max(int(3 * box_overlay_ratio), 1),
        }
        
        # 2. STEP 1: RUN OCR
        print("🔍 Running OCR...")
        ocr_bbox_rslt, _ = check_ocr_box(
            image_input,
            display_img=False,
            output_bb_format='xyxy',
            goal_filtering=None,
            easyocr_args={'paragraph': False, 'text_threshold': 0.9},
            use_paddleocr=use_paddleocr
        )
        text, ocr_bbox = ocr_bbox_rslt
        
        # 3. STEP 2: RUN OMNIPARSER
        print("👀 Running OmniParser...")
        with torch.no_grad():  # Disable gradient computation
            dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
                image_input,
                yolo_model,
                BOX_TRESHOLD=box_threshold,
                output_coord_in_ratio=True,
                ocr_bbox=ocr_bbox,
                draw_bbox_config=draw_bbox_config,
                caption_model_processor=caption_model_processor,
                ocr_text=text,
                iou_threshold=iou_threshold,
                imgsz=imgsz,
            )
        
        # 4. DECODE OUTPUT IMAGE
        output_image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))
        
        # 5. FORMAT JSON RESULT
        json_output = '\n'.join([f'icon {i}: ' + str(v) for i, v in enumerate(parsed_content_list)])
        
        elapsed = time.time() - start_time
        print(f"✅ Processing completed in {elapsed:.2f}s")
        
        return output_image, json_output
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a red error image so the client doesn't hang
        error_image = Image.new('RGB', (100, 100), color='red')
        return error_image, f"Error: {str(e)}"
    
    finally:
        # 6. AGGRESSIVE MEMORY CLEANUP
        print("🧹 Starting memory cleanup...")
        
        # Delete all large objects explicitly
        try:
            if ocr_bbox_rslt is not None:
                del ocr_bbox_rslt
            if text is not None:
                del text
            if ocr_bbox is not None:
                del ocr_bbox
            if dino_labled_img is not None:
                del dino_labled_img
            if label_coordinates is not None:
                del label_coordinates
            if parsed_content_list is not None:
                del parsed_content_list
            
            # Close input image if it's still open
            if hasattr(image_input, 'close'):
                try:
                    image_input.close()
                except:
                    pass
        except:
            pass
        
        # Run aggressive cleanup
        aggressive_cleanup()
        log_memory()  # Log final state

# --- DEFINE API ---
with gr.Blocks() as demo:
    gr.Markdown("""
    # OmniParser for Pure Vision Based General GUI Agent 🔥
    ### Memory-Optimized Version
    """)
    
    with gr.Row():
        with gr.Column():
            img_input = gr.Image(label="Upload Screenshot", type="pil")
            box_thresh = gr.Slider(
                label="Box Threshold",
                minimum=0.01,
                maximum=1.0,
                value=0.05,
                step=0.01
            )
            iou_thresh = gr.Slider(
                label="IOU Threshold",
                minimum=0.01,
                maximum=1.0,
                value=0.1,
                step=0.01
            )
            process_btn = gr.Button("🚀 Analyze", variant="primary")
        
        with gr.Column():
            output_img = gr.Image(label="Labeled Output", type="pil")
            output_json = gr.Textbox(
                label="JSON Result",
                lines=10,
                max_lines=20
            )
    
    # Define the processing action
    process_btn.click(
        fn=process_image,
        inputs=[img_input, box_thresh, iou_thresh],
        outputs=[output_img, output_json],
        api_name="process"
    )
    
    # Also trigger on image upload for immediate analysis
    img_input.change(
        fn=process_image,
        inputs=[img_input, box_thresh, iou_thresh],
        outputs=[output_img, output_json]
    )

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 STARTING GRADIO SERVER")
    print("="*70)
    
    # Clear memory before starting
    aggressive_cleanup()
    
    demo.queue(
        max_size=10,        # Limit queue size
        default_concurrency_limit=2  # Limit concurrent requests
    )
    
    demo.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7865,
        share=True,
        max_threads=4,  # Limit threads to reduce memory
        show_error=True,
        debug=False  # Disable debug mode in production
    )

