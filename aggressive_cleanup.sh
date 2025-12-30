#!/bin/bash
set -e

echo "🔥 Aggressive Cleanup (Target: 4-6GB)"
echo ""

# Show before
echo "=== Before ==="
df -h / | tail -1
echo ""

# Remove EasyOCR models (will re-download on first use, ~500MB)
echo "=== Removing EasyOCR cache ==="
rm -rf ~/.EasyOCR 2>/dev/null || true
echo "✅ EasyOCR cache removed (~500MB)"

# Remove PaddleOCR download cache (will re-download on first use, ~20MB)
echo "=== Removing PaddleOCR download cache ==="
rm -rf ~/.paddleocr/whl 2>/dev/null || true
echo "✅ PaddleOCR cache removed"

# Remove HuggingFace transformers cache (keeps models but removes redundant files)
echo "=== Cleaning HuggingFace transformers cache ==="
find ~/.cache/huggingface/transformers -type f -name "*.json" ! -name "config.json" -delete 2>/dev/null || true
find ~/.cache/huggingface/transformers -type f -name "*.txt" -delete 2>/dev/null || true
find ~/.cache/huggingface -name "*.lock" -delete 2>/dev/null || true
find ~/.cache/huggingface -type d -empty -delete 2>/dev/null || true
echo "✅ HuggingFace cache cleaned"

# Remove unnecessary Python packages (keep only essentials)
echo "=== Removing optional packages ==="
pip uninstall -y gradio-client fastapi uvicorn starlette pydantic-settings 2>/dev/null || true
echo "✅ Optional packages removed"

# Remove documentation and test files from packages
echo "=== Removing package docs/tests ==="
find /usr/local/lib/python3.11/dist-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.11/dist-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.11/dist-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /usr/local/lib/python3.11/dist-packages -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Package docs/tests removed"

# Remove build tools if not needed
echo "=== Removing build tools ==="
apt-get remove -y --purge build-essential gcc g++ make 2>/dev/null || true
apt-get autoremove -y 2>/dev/null || true
apt-get clean 2>/dev/null || true
echo "✅ Build tools removed"

# Remove logs
echo "=== Removing logs ==="
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

echo "✅ Aggressive cleanup complete!"
echo ""
echo "⚠️  Note: EasyOCR and PaddleOCR will re-download models on first use"
echo "   This is normal and will only happen once"
