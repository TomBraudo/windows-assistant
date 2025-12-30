#!/bin/bash

echo "📊 Disk Usage Analysis"
echo ""

# Overall disk usage
echo "=== Overall Disk Usage ==="
df -h / | tail -1
echo ""

# Top 20 largest directories
echo "=== Top 20 Largest Directories ==="
du -h / 2>/dev/null | sort -rh | head -20 | awk '{printf "%-8s %s\n", $1, $2}'
echo ""

# Python packages size
echo "=== Python Packages Size ==="
du -sh /usr/local/lib/python3.11/dist-packages/* 2>/dev/null | sort -rh | head -15
echo ""

# Cache directories
echo "=== Cache Directories ==="
echo "HuggingFace:"
du -sh /root/.cache/huggingface 2>/dev/null || echo "  Not found"
echo "Pip:"
du -sh /root/.cache/pip 2>/dev/null || echo "  Not found"
echo "EasyOCR:"
du -sh ~/.EasyOCR 2>/dev/null || echo "  Not found"
echo "PaddleOCR:"
du -sh ~/.paddleocr 2>/dev/null || echo "  Not found"
echo ""

# Workspace breakdown
echo "=== Workspace Breakdown ==="
if [ -d "/workspace/OmniParser" ]; then
    du -sh /workspace/OmniParser/* 2>/dev/null | sort -rh | head -10
fi
echo ""

# Large files (>100MB)
echo "=== Large Files (>100MB) ==="
find / -type f -size +100M 2>/dev/null | head -20 | while read file; do
    size=$(du -h "$file" 2>/dev/null | cut -f1)
    echo "$size  $file"
done
echo ""

# Model files specifically
echo "=== Model Files ==="
find / -type f \( -name "*.pt" -o -name "*.pth" -o -name "*.safetensors" -o -name "*.bin" \) -size +50M 2>/dev/null | while read file; do
    size=$(du -h "$file" 2>/dev/null | cut -f1)
    echo "$size  $file"
done | head -20
echo ""

echo "💡 Tips to free space:"
echo "  - Remove unused Python packages"
echo "  - Clear model caches (EasyOCR, PaddleOCR download cache)"
echo "  - Remove duplicate model files"
echo "  - Uninstall packages you don't need"
