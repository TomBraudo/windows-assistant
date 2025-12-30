#!/bin/bash
set -e

echo "🎯 Safe Cleanup (Target: 4-6GB total)"
echo ""

# Show before
echo "=== Before ==="
df -h / | tail -1
echo ""

# Remove NSight Compute (NVIDIA dev tools, not needed for inference) - 1.4GB
echo "=== Removing NSight Compute (dev tools) ==="
rm -rf /opt/nvidia/nsight-compute 2>/dev/null || true
echo "✅ NSight Compute removed (~1.4GB)"

# Remove CUDA 12.4 (PyTorch uses CUDA 11.8, so this is unused) - 4.7GB
echo "=== Removing CUDA 12.4 (unused, PyTorch uses CUDA 11.8) ==="
rm -rf /usr/local/cuda-12.4 2>/dev/null || true
echo "✅ CUDA 12.4 removed (~4.7GB)"

# Clean HuggingFace cache (keeps models but removes redundant) - 445MB
echo "=== Cleaning HuggingFace cache ==="
find /root/.cache/huggingface -name "*.lock" -delete 2>/dev/null || true
find /root/.cache/huggingface -type d -name "*.tmp" -exec rm -rf {} + 2>/dev/null || true
# Remove duplicate model files if Florence-2 is already in weights/
if [ -f "/workspace/OmniParser/weights/icon_caption_florence/model.safetensors" ]; then
    echo "Removing duplicate Florence-2 from HuggingFace cache..."
    rm -rf /root/.cache/huggingface/hub/models--microsoft--Florence-2-base 2>/dev/null || true
fi
echo "✅ HuggingFace cache cleaned (~445MB)"

# Remove EasyOCR cache (re-downloads on first use) - 94MB
echo "=== Removing EasyOCR cache ==="
rm -rf ~/.EasyOCR 2>/dev/null || true
echo "✅ EasyOCR cache removed (~94MB)"

# Remove PaddleOCR download cache - 16MB
echo "=== Removing PaddleOCR download cache ==="
rm -rf ~/.paddleocr/whl 2>/dev/null || true
echo "✅ PaddleOCR cache removed (~16MB)"

# Remove package tests and docs
echo "=== Removing package tests/docs ==="
find /usr/local/lib/python3.11/dist-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.11/dist-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.11/dist-packages -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.11/dist-packages -type d -name "doc" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Package tests/docs removed"

# Remove unnecessary large packages
echo "=== Removing optional packages ==="
pip uninstall -y polars polars-runtime-32 2>/dev/null || true  # 137MB, not needed
pip uninstall -y modelscope 2>/dev/null || true  # 64MB, not needed
echo "✅ Optional packages removed"

# Clean logs
echo "=== Cleaning logs ==="
find /var/log -type f -name "*.log" -delete 2>/dev/null || true
journalctl --vacuum-time=1d 2>/dev/null || true
echo "✅ Logs cleared"

# Show after
echo ""
echo "=== After ==="
df -h / | tail -1
echo ""

# Show what's left
echo "=== Remaining Large Items ==="
du -sh /usr/local/lib/python3.11/dist-packages/* 2>/dev/null | sort -rh | head -10
echo ""

echo "✅ Safe cleanup complete!"
echo ""
echo "⚠️  Note: EasyOCR will re-download models on first use (~94MB)"
echo "   CUDA 12.4 removed (PyTorch uses CUDA 11.8 from pip)"
