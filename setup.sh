#!/bin/bash
set -e

echo "🚀 RTX 4000 Ada GPU Setup for OmniParser"
echo ""

echo "=== System dependencies ==="
apt-get update && apt-get install -y git wget curl libgl1-mesa-glx libglib2.0-0
apt-get clean && rm -rf /var/lib/apt/lists/*

echo "=== Python environment ==="
python -m pip install --upgrade pip setuptools wheel
pip install 'numpy<2'

echo "=== PyTorch GPU (CUDA 11.8) ==="
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu118

echo "=== PaddlePaddle GPU + PaddleOCR ==="
pip uninstall paddlepaddle paddlepaddle-gpu -y || true
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
pip install "paddleocr>=3.0.0"

echo "Verifying PaddlePaddle GPU installation..."
python3 -c "
import paddle
print('PaddlePaddle version:', paddle.__version__)
print('CUDA compiled:', paddle.device.is_compiled_with_cuda())
if paddle.device.is_compiled_with_cuda():
    paddle.set_device('gpu:0')
    print('✅ PaddlePaddle GPU ready')
else:
    print('❌ PaddlePaddle GPU not detected - reinstalling...')
    import sys
    sys.exit(1)
"

echo "=== OmniParser dependencies ==="
pip install transformers==4.45.0 Pillow opencv-python-headless==4.10.0.84 accelerate timm einops \
    gradio ultralytics supervision scipy shapely matplotlib huggingface_hub runpod openai easyocr

echo "=== Install flash_attn (CUDA 11.8 wheel) ==="
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.5.8/flash_attn-2.5.8+cu118torch2.1cxx11abiFALSE-cp311-cp311-linux_x86_64.whl || {
    echo "⚠️  Pre-built wheel failed, trying pip install..."
    MAX_JOBS=4 pip install flash-attn==2.5.8 --no-build-isolation || {
        echo "❌ flash_attn installation failed"
        echo "Florence-2 requires flash_attn. You may need to:"
        echo "  1. Use a pod with CUDA 11.8 (matching PyTorch)"
        echo "  2. Or rebuild PyTorch for CUDA 12.4"
        exit 1
    }
}

echo "=== Force NumPy <2 (compatibility fix) ==="
pip install --force-reinstall 'numpy<2'

echo "=== Cleaning pip cache ==="
pip cache purge || true
echo "✅ Pip cache cleared"

echo "=== Verify models ==="
if [ ! -d "weights" ]; then
    echo "❌ weights/ directory not found!"
    echo ""
    echo "Required structure:"
    echo "  weights/icon_detect/model.pt          (or best.pt)"
    echo "  weights/icon_caption_florence/        (Florence-2 model files)"
    echo ""
    echo "Copy your existing OmniParser weights to this location."
    exit 1
fi

# Check for YOLO model
if [ -f "weights/icon_detect/model.pt" ]; then
    echo "✅ YOLO model found: weights/icon_detect/model.pt"
elif [ -f "weights/icon_detect/best.pt" ]; then
    echo "✅ YOLO model found: weights/icon_detect/best.pt"
    ln -sf best.pt weights/icon_detect/model.pt
else
    echo "❌ YOLO model not found in weights/icon_detect/"
    exit 1
fi

# Check for Florence-2
if [ -f "weights/icon_caption_florence/config.json" ]; then
    echo "✅ Florence-2 model found"
elif [ -f "weights/icon_caption/config.json" ]; then
    echo "⚠️  Found icon_caption/, symlinking to icon_caption_florence/"
    ln -sf icon_caption weights/icon_caption_florence
else
    echo "❌ Florence-2 model not found in weights/icon_caption_florence/"
    exit 1
fi

echo ""
echo "=== Verify GPU ==="
python3 -c "
import torch
import paddle

assert torch.cuda.is_available(), '❌ PyTorch GPU not available!'

print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
print(f'✅ PyTorch CUDA: {torch.version.cuda}')

# Test PaddlePaddle GPU
paddle.set_device('gpu:0')
device = paddle.device.get_device()
print(f'✅ PaddlePaddle GPU: {device}')

# Quick GPU test
x = paddle.randn([2, 3])
print(f'✅ PaddlePaddle GPU test: tensor on {x.place}')

print('')
print('🚀 Setup complete! Run: python runpod_server.py')
"
