#!/bin/bash

echo "🔧 Fixing PaddleOCR 3.x compatibility"
echo ""

# Fix util/utils.py - remove unsupported parameter
if [ -f "util/utils.py" ]; then
    echo "Fixing util/utils.py..."
    
    # Fix PaddleOCR initialization properly
    python3 << 'PYEOF'
import re

with open('util/utils.py', 'r') as f:
    lines = f.readlines()

# Find and fix PaddleOCR initialization
in_paddleocr = False
paddleocr_start = -1
fixed_lines = []

for i, line in enumerate(lines):
    if 'PaddleOCR(' in line:
        in_paddleocr = True
        paddleocr_start = i
        # Start of PaddleOCR call
        fixed_lines.append(line)
    elif in_paddleocr:
        # Remove unsupported parameters
        if 'det_db_score_mode' in line or 'use_dilation' in line:
            continue  # Skip these lines
        elif ')' in line:
            # End of PaddleOCR call - clean up trailing comma if needed
            if fixed_lines and fixed_lines[-1].rstrip().endswith(','):
                fixed_lines[-1] = fixed_lines[-1].rstrip().rstrip(',') + '\n'
            fixed_lines.append(line)
            in_paddleocr = False
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

with open('util/utils.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed PaddleOCR initialization")
PYEOF
    
    # Ensure proper PaddleOCR 3.x initialization
    if grep -q "det_db_score_mode" util/utils.py; then
        echo "Manual fix needed - removing det_db_score_mode lines..."
        # More aggressive fix
        python3 << 'PYEOF'
import re

with open('util/utils.py', 'r') as f:
    content = f.read()

# Remove det_db_score_mode parameter
content = re.sub(r',\s*det_db_score_mode=[\'"]slow[\'"]', '', content)
content = re.sub(r'det_db_score_mode=[\'"]slow[\'"],\s*', '', content)

# Fix PaddleOCR initialization to match 3.x API
old_pattern = r'paddle_ocr = PaddleOCR\([^)]+\)'
new_init = """paddle_ocr = PaddleOCR(
    lang='en',
    use_angle_cls=False,
    use_gpu=True,
    device='gpu:0'
)"""

# Replace if we find the old pattern
if re.search(old_pattern, content):
    content = re.sub(old_pattern, new_init, content, flags=re.DOTALL)

with open('util/utils.py', 'w') as f:
    f.write(content)

print("✅ Fixed util/utils.py")
PYEOF
    fi
    
    echo "✅ util/utils.py fixed"
else
    echo "❌ util/utils.py not found"
    exit 1
fi

echo ""
echo "✅ PaddleOCR 3.x compatibility fix complete!"
echo "Run: python server_2.py"
