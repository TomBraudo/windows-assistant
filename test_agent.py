from gradio_client import Client, file
import os
import shutil
import platform
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
GRADIO_URL = os.getenv("RUNPOD_URL")
if not GRADIO_URL:
    raise ValueError("RUNPOD_URL not found in .env file!")
IMAGE_PATH = r"C:\Users\tombr\OneDrive\Desktop\screenshots\test.png"

def test_omniparser():
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Error: Could not find image at: {IMAGE_PATH}")
        return

    print(f"Connecting to {GRADIO_URL}...")
    client = Client(GRADIO_URL)
    
    print(f"Sending image: {IMAGE_PATH}")
    
    try:
        # The API returns a tuple: (temporary_file_path_to_image, json_string)
        result = client.predict(
            image_input=file(IMAGE_PATH),
            box_threshold=0.05,
            iou_threshold=0.1,
            api_name="/process"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 2. HANDLE THE RESULT
    if len(result) >= 2:
        # result[0] is the path to the labeled image (downloaded to a temp folder)
        temp_image_path = result[0]
        # result[1] is the text/coordinates
        json_output = result[1]

        # 3. SAVE THE IMAGE TO YOUR DESKTOP
        # We rename it to 'labeled_result.png' so you can find it easily
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labeled_result.png")
        
        # Move the file from temp folder to your current folder
        shutil.move(temp_image_path, save_path)
        
        print(f"\n✅ SUCCESS! Labeled image saved to: {save_path}")
        print(f"--- Parsed Text Preview ---\n{json_output[:200]}... (truncated)")

        # 4. AUTO-OPEN THE IMAGE
        print("\nOpening image now...")
        if platform.system() == "Windows":
            os.startfile(save_path)
        elif platform.system() == "Darwin": # macOS
            os.system(f"open '{save_path}'")
        else: # Linux
            os.system(f"xdg-open '{save_path}'")

    else:
        print("❌ Unexpected result format:", result)

if __name__ == "__main__":
    test_omniparser()