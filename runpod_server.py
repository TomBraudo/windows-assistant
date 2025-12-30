import os
import sys
import torch
import gc
import io
import base64
import numpy as np
import traceback
from PIL import Image
import runpod

# Add util directory to path if needed
sys.path.insert(0, os.path.dirname(__file__))

from util.utils import get_yolo_model, get_caption_model_processor, get_som_labeled_img
from paddleocr import PaddleOCR

# --- GLOBAL GPU SETTINGS ---
assert torch.cuda.is_available(), "❌ GPU required! No CUDA device found."
DEVICE = torch.device('cuda:0')
print(f"🚀 GPU: {torch.cuda.get_device_name(0)} | CUDA: {torch.version.cuda}")

# --- LOAD ALL MODELS ON GPU ---
print("⏳ Loading YOLO...")
yolo_model = get_yolo_model(model_path="weights/icon_detect/model.pt").to(DEVICE).eval()
print("✅ YOLO ready")

print("⏳ Loading Florence-2...")
caption_model_processor = get_caption_model_processor(
    model_name="florence2", 
    model_name_or_path="weights/icon_caption_florence",
    device="cuda"
)
caption_model_processor['model'] = caption_model_processor['model'].to(DEVICE).half().eval()
print("✅ Florence-2 ready (FP16)")

print("⏳ Loading PaddleOCR...")
ocr_reader = PaddleOCR(use_angle_cls=False, lang="en", use_gpu=True, device='gpu:0')
print("✅ PaddleOCR ready")

print("🚀 All models on GPU - Ready for inference!")

def optimized_ocr_gpu(image, ocr_model):
    """Fast GPU OCR - no memory leaks"""
    img_np = np.array(image)
    result = ocr_model.ocr(img_np, cls=False)
    
    texts, boxes = [], []
    if result and result[0]:
        for line in result[0]:
            if line[1]:
                points = line[0]
                text = line[1][0]
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                boxes.append([min(xs), min(ys), max(xs), max(ys)])
                texts.append(text)
    
    return texts, boxes

@torch.inference_mode()
def process_image(image_input, box_threshold=0.05, iou_threshold=0.1, imgsz=640):
    """Full GPU processing pipeline for OmniParser
    
    Args:
        image_input: PIL Image object
        box_threshold: Detection confidence threshold (default: 0.05)
        iou_threshold: IOU threshold for NMS (default: 0.1)
        imgsz: Image size for YOLO (default: 640)
        
    Returns:
        tuple: (annotated_image_base64, parsed_content_list, label_coordinates)
    """
    # Dynamic scaling config
    box_overlay_ratio = image_input.size[0] / 3200
    draw_bbox_config = {
        'text_scale': 0.8 * box_overlay_ratio,
        'text_thickness': max(int(2 * box_overlay_ratio), 1),
        'text_padding': max(int(3 * box_overlay_ratio), 1),
        'thickness': max(int(3 * box_overlay_ratio), 1),
    }

    # 1. GPU OCR (replaces CPU bottleneck)
    print("🔍 Running GPU OCR...")
    text, ocr_bbox = optimized_ocr_gpu(image_input, ocr_reader)
    print(f"✅ OCR: {len(text)} elements found")

    # 2. Full GPU OmniParser pipeline
    print("🔍 Running YOLO + Florence...")
    with torch.cuda.amp.autocast():
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

    # 3. GPU memory cleanup
    del text, ocr_bbox
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()

    print("✅ Processing complete")
    return dino_labled_img, parsed_content_list, label_coordinates


def handler(job):
    """RunPod serverless handler function
    
    Expected input format:
    {
        "input": {
            "image": "base64_encoded_image_string",
            "box_threshold": 0.05,  # optional
            "iou_threshold": 0.1,   # optional
            "imgsz": 640,           # optional
            "return_image": true    # optional, return annotated image
        }
    }
    
    Returns:
    {
        "output": {
            "parsed_content": [...],
            "label_coordinates": {...},
            "annotated_image": "base64_string"  # if return_image=true
        }
    }
    """
    try:
        job_input = job.get("input", {})
        
        # Validate input
        if "image" not in job_input:
            return {"error": "Missing required field: 'image' (base64 encoded image)"}
        
        # Get parameters with defaults
        box_threshold = job_input.get("box_threshold", 0.05)
        iou_threshold = job_input.get("iou_threshold", 0.1)
        imgsz = job_input.get("imgsz", 640)
        return_image = job_input.get("return_image", True)
        
        # Validate thresholds
        if not (0.01 <= box_threshold <= 1.0):
            return {"error": "box_threshold must be between 0.01 and 1.0"}
        if not (0.01 <= iou_threshold <= 1.0):
            return {"error": "iou_threshold must be between 0.01 and 1.0"}
        
        # Decode image from base64
        print("📥 Decoding image...")
        image_data = base64.b64decode(job_input["image"])
        image_input = Image.open(io.BytesIO(image_data)).convert("RGB")
        print(f"✅ Image loaded: {image_input.size}")
        
        # Process the image
        annotated_img_base64, parsed_content_list, label_coordinates = process_image(
            image_input,
            box_threshold=box_threshold,
            iou_threshold=iou_threshold,
            imgsz=imgsz
        )
        
        # Prepare response
        output = {
            "parsed_content": parsed_content_list,
            "label_coordinates": label_coordinates,
            "status": "success",
            "image_size": list(image_input.size)
        }
        
        if return_image:
            output["annotated_image"] = annotated_img_base64
        
        # Cleanup
        del image_input, image_data
        gc.collect()
        
        return {"output": output}
        
    except ValueError as e:
        error_trace = traceback.format_exc()
        print(f"❌ Validation Error: {e}")
        return {
            "error": f"Invalid input: {str(e)}",
            "error_type": "ValueError"
        }
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Processing Error: {e}")
        print(error_trace)
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_trace
        }

def start_gradio_demo():
    """Optional Gradio UI for local testing"""
    try:
        import gradio as gr
    except ImportError:
        print("⚠️ Gradio not installed. Skipping UI.")
        return
    
    def gradio_wrapper(image_input, box_threshold, iou_threshold):
        """Wrapper for Gradio UI"""
        try:
            if image_input is None:
                return Image.new('RGB', (200, 100), color='gray'), "Please upload an image"
            
            annotated_img_base64, parsed_content_list, _ = process_image(
                image_input,
                box_threshold=box_threshold,
                iou_threshold=iou_threshold
            )
            
            # Decode image for display
            image_out = Image.open(io.BytesIO(base64.b64decode(annotated_img_base64)))
            
            # Format parsed content
            parsed_content_str = '\n'.join([
                f"[{i}] {elem.get('type', 'unknown')}: {elem.get('content', 'N/A')}"
                for i, elem in enumerate(parsed_content_list)
            ])
            
            return image_out, parsed_content_str
            
        except Exception as e:
            print(f"❌ Gradio Error: {e}")
            traceback.print_exc()
            return Image.new('RGB', (200, 100), color='red'), f"ERROR: {str(e)}"
    
    # --- GRADIO UI ---
    with gr.Blocks(title="OmniParser GPU", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🚀 OmniParser V2 - FULL GPU ACCELERATION")
        gr.Markdown("**YOLO + Florence + PaddleOCR all on RTX 4000 Ada** | No CPU bottleneck")
        
        with gr.Row():
            with gr.Column(scale=1):
                img_in = gr.Image(type='pil', label='📁 Upload Screenshot', height=400)
                with gr.Row():
                    box_thresh = gr.Slider(0.01, 1.0, 0.05, step=0.01, label='🎯 Box Threshold')
                    iou_thresh = gr.Slider(0.01, 1.0, 0.1, step=0.01, label='🔗 IOU Threshold')
                analyze_btn = gr.Button('🚀 ANALYZE WITH GPU', variant='primary', scale=2)
            
            with gr.Column(scale=1):
                img_out = gr.Image(type='pil', label='🎨 Detected Elements', height=400)
                txt_out = gr.Textbox(label='📋 Parsed Content', lines=10, max_lines=20)

        analyze_btn.click(
            fn=gradio_wrapper,
            inputs=[img_in, box_thresh, iou_thresh],
            outputs=[img_out, txt_out],
            api_name="omniparser_gpu"
        )
    
    demo.queue(max_size=10, concurrency_count=2)
    demo.launch(
        share=True,
        server_port=7865,
        server_name="0.0.0.0",
        show_error=True,
        quiet=False
    )


if __name__ == "__main__":
    # Check if running in RunPod serverless mode or local testing
    if "--test_input" in sys.argv or os.environ.get("RUNPOD_SERVERLESS"):
        print("🚀 Starting RunPod Serverless Worker...")
        runpod.serverless.start({"handler": handler})
    else:
        print("🖥️ Starting Gradio UI for local testing...")
        print("💡 To start as RunPod worker, use: python runpod_server.py --test_input '{...}'")
        start_gradio_demo()
