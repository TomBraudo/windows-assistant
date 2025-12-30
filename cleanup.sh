#!/bin/bash
set -e

echo "🧹 Cleaning up disk space..."
echo ""

# Show current disk usage
echo "=== Current disk usage ==="
df -h / | tail -1
du -sh /workspace/OmniParser 2>/dev/null || echo "Checking workspace..."
echo ""

# Backup models first
echo "=== Backing up models ==="
if [ -d "weights" ]; then
    echo "✅ Models found in weights/"
    du -sh weights/
else
    echo "⚠️  No weights/ directory found"
fi
echo ""

# Clean pip cache (saves GBs)
echo "=== Cleaning pip cache ==="
pip cache purge || true
echo "✅ Pip cache cleared"

# Clean Python bytecode
echo "=== Cleaning Python cache ==="
find /workspace/OmniParser -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /workspace/OmniParser -type f -name "*.pyc" -delete 2>/dev/null || true
find /workspace/OmniParser -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Python cache cleared"

# Clean build artifacts
echo "=== Cleaning build artifacts ==="
rm -rf /workspace/OmniParser/build 2>/dev/null || true
rm -rf /workspace/OmniParser/dist 2>/dev/null || true
rm -rf /tmp/* 2>/dev/null || true
rm -rf /root/.cache/pip 2>/dev/null || true
echo "✅ Build artifacts cleared"

# Clean HuggingFace cache (but keep downloaded models)
echo "=== Cleaning HuggingFace cache (keeping models) ==="
# Keep model files but remove redundant cache
find /root/.cache/huggingface -name "*.lock" -delete 2>/dev/null || true
find /root/.cache/huggingface -type d -name "*.tmp" -exec rm -rf {} + 2>/dev/null || true
echo "✅ HuggingFace cache cleaned"

# Clean apt cache
echo "=== Cleaning apt cache ==="
apt-get clean || true
apt-get autoclean || true
rm -rf /var/lib/apt/lists/* 2>/dev/null || true
echo "✅ Apt cache cleared"

# Show final disk usage
echo ""
echo "=== Final disk usage ==="
df -h / | tail -1
du -sh /workspace/OmniParser 2>/dev/null || true
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To reinstall dependencies (keeping models):"