#!/bin/bash
set -e

echo "🔄 Minimal Reinstall (keeping models)"
echo ""

# Backup models location
if [ -d "weights" ]; then
    echo "✅ Models preserved in weights/"
    du -sh weights/
else
    echo "⚠️  No weights/ directory - models will be lost!"
    exit 1
fi

echo ""
echo "=== Uninstalling packages (keeping models) ==="
pip uninstall -y torch torchvision torchaudio paddlepaddle paddlepaddle-gpu paddleocr \
    transformers ultralytics supervision opencv-python-headless easyocr \
    gradio accelerate timm einops scipy shapely matplotlib huggingface_hub runpod openai \
    flash-attn 2>/dev/null || true

echo ""
echo "=== Running cleanup ==="
bash cleanup.sh

echo ""
echo "=== Reinstalling (minimal) ==="
python -m pip install --upgrade pip setuptools wheel
pip install 'numpy<2'

# Core GPU stack
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu118

# PaddlePaddle GPU
pip uninstall paddlepaddle paddlepaddle-gpu -y || true
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
pip install "paddleocr>=3.0.0"

# Essential only
pip install transformers==4.45.0 Pillow opencv-python-headless==4.10.0.84 \
    accelerate timm einops ultralytics supervision scipy shapely matplotlib \
    huggingface_hub runpod openai easyocr

# Flash attention (if needed)
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.5.8/flash_attn-2.5.8+cu118torch2.1cxx11abiFALSE-cp311-cp311-linux_x86_64.whl 2>/dev/null || {
    echo "⚠️  flash_attn wheel not available, skipping"
}

# Force numpy
pip install --force-reinstall 'numpy<2'

echo ""
echo "=== Verifying models ==="
if [ -f "weights/icon_detect/model.pt" ] || [ -f "weights/icon_detect/best.pt" ]; then
    echo "✅ YOLO model preserved"
else
    echo "❌ YOLO model missing!"
fi

if [ -f "weights/icon_caption_florence/config.json" ] || [ -f "weights/icon_caption/config.json" ]; then
    echo "✅ Florence-2 model preserved"
else
    echo "❌ Florence-2 model missing!"
fi

echo ""
echo "✅ Minimal reinstall complete!"
echo "Disk usage:"
df -h / | tail -1
