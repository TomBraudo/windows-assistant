# Mouse DPI Debug & Testing Suite

This folder contains comprehensive tests to fix and verify DPI-aware mouse clicking.

## 🎯 Problem

On high-DPI displays (125%, 150%, 200% scaling), mouse clicks land at wrong coordinates because:
1. Windows reports **scaled coordinates** (logical pixels)
2. Screenshots capture **physical pixels**  
3. Vision model returns physical coordinates
4. PyAutoGUI clicks at logical coordinates
5. **Result**: Clicks miss by scaling factor

Example: On 150% DPI display
- Vision says "click at (600, 400)"
- Windows thinks 600px = 400px logical
- Click lands at (400, 267) - WRONG!

## ✅ Solution

Set **DPI awareness** BEFORE importing PyAutoGUI:
```python
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Now aware of real pixels
import pyautogui  # Will use real coordinates
```

## 📋 Test Scripts (Run in Order)

### 1. `01_dpi_detection.py` - Diagnostic
**Purpose**: Check current DPI awareness status

**What it does**:
- Checks if process is DPI aware
- Shows current DPI scaling (100%, 125%, 150%, etc.)
- Detects resolution mismatch
- Verifies PyAutoGUI compatibility

**Run**:
```bash
python tests/mouse_dpi_debug/01_dpi_detection.py
```

**Expected output**:
```
✓ DPI awareness set
✓ Scaling Factor: 1.50x
✓ PyAutoGUI matches system metrics
```

**If you see**:
- ❌ "Process is NOT DPI aware" → DPI awareness not set
- ❌ "PyAutoGUI mismatch" → Wrong import order

---

### 2. `02_visual_click_test.py` - Visual Verification
**Purpose**: See where clicks actually land

**What it does**:
- Creates target circles on canvas
- You click the targets
- Shows where click actually landed (red X)
- Calculates error distance

**Run**:
```bash
python tests/mouse_dpi_debug/02_visual_click_test.py
```

**How to use**:
1. Window opens with red circle targets
2. Click the center of a target
3. Red X shows where click registered
4. Blue dashed line shows error

**Success criteria**:
- ✓ Red X lands within 10 pixels of center
- ✓ Error distance < 20 pixels
- ✓ "PyAutoGUI Click" button clicks target accurately

**If clicks are offset**: DPI fix not working, check import order

---

### 3. `03_screenshot_coordinate_test.py` - Full Pipeline Test
**Purpose**: Test the complete screenshot → coordinates → click pipeline

**What it does**:
1. Captures your screen
2. Creates grid overlay for reference
3. You specify coordinates to click
4. Clicks at those coordinates  
5. Marks click location on screenshot

**Run**:
```bash
python tests/mouse_dpi_debug/03_screenshot_coordinate_test.py
```

**How to use**:
1. Script captures screenshot
2. Choose option:
   - Option 1: Enter custom coordinates
   - Option 2: Test center click
   - Option 3: Test all corners
3. Watch where click lands
4. Check marked screenshot in `test_output/`

**Success criteria**:
- ✓ Clicks land where intended
- ✓ Marked screenshots show accurate positions
- ✓ No systematic offset

---

### 4. `04_comprehensive_dpi_fix.py` - All-in-One Test
**Purpose**: Try all DPI fix methods and verify

**What it does**:
- Tests all known DPI awareness methods
- Checks which one works
- Verifies screen resolution detection
- Tests PyAutoGUI compatibility
- Provides recommendations

**Run**:
```bash
python tests/mouse_dpi_debug/04_comprehensive_dpi_fix.py
```

**Expected output**:
```
✓✓✓ ALL TESTS PASSED!
Your DPI fix is working correctly.
```

**If tests fail**: Follow recommendations in output

---

## 🔧 Applying the Fix to Main App

Once all tests pass:

### Step 1: Verify Fix Works
```bash
# Run all tests
python tests/mouse_dpi_debug/01_dpi_detection.py
python tests/mouse_dpi_debug/02_visual_click_test.py
python tests/mouse_dpi_debug/04_comprehensive_dpi_fix.py
```

All should show ✓ success.

### Step 2: Check Current Implementation
The fix is ALREADY in `app/tools/computer_control.py`:

```python
# Line 18-31 in computer_control.py
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()
```

### Step 3: Verify Import Order
**CRITICAL**: DPI awareness must be set BEFORE importing pyautogui.

Check `app/tools/computer_control.py`:
- ✓ Line 1-31: DPI awareness code
- ✓ Line 33: `import pyautogui`  ← Must be AFTER

If pyautogui is imported BEFORE setting DPI awareness, coordinates will be wrong!

### Step 4: Test in Main App
```bash
# Test in GUI
python main_gui.py
```

Try Agent Mode with: "click the Chrome icon"

Watch if clicks land accurately.

---

## 🐛 Troubleshooting

### Issue: "Process is NOT DPI aware"
**Cause**: DPI awareness not set

**Solution**: 
- Run `04_comprehensive_dpi_fix.py` to find working method
- Ensure code runs before any GUI imports

### Issue: "PyAutoGUI mismatch"
**Cause**: PyAutoGUI imported before setting DPI awareness

**Solution**:
1. Check import order
2. Set DPI awareness FIRST
3. Import pyautogui AFTER

### Issue: Clicks offset by ~50%
**Cause**: 150% DPI scaling not handled

**Solution**:
- Run `01_dpi_detection.py`
- Check if awareness is set
- Verify scaling factor detected

### Issue: Clicks accurate in test, wrong in app
**Cause**: Different DPI awareness in test vs app

**Solution**:
- Check if main app sets DPI awareness
- Verify it's set before pyautogui import
- Check if multiple imports reset it

### Issue: Works on one monitor, fails on another
**Cause**: Multi-monitor with different DPI

**Solution**:
- Use `SetProcessDpiAwareness(2)` for per-monitor awareness
- Test on both monitors
- Consider which monitor app runs on

---

## 📊 Understanding DPI Awareness Levels

| Level | Name | Description | Use Case |
|-------|------|-------------|----------|
| 0 | UNAWARE | Windows lies about coordinates | ❌ Don't use |
| 1 | SYSTEM_AWARE | Aware of system DPI | ✓ Good for single monitor |
| 2 | PER_MONITOR_AWARE | Aware of each monitor's DPI | ✓ Best for multi-monitor |

**Current app uses**: Level 1 (System Aware)
**Recommended**: Level 1 (sufficient for most cases)
**For multi-monitor**: Upgrade to Level 2

---

## 🎓 How DPI Scaling Works

### Without DPI Awareness (BROKEN):
```
Physical screen: 2560 x 1440 (actual pixels)
Windows tells app: 1707 x 960 (scaled @ 150%)
Vision sees: 2560 x 1440
Agent clicks: 1707 x 960
Result: Clicks miss!
```

### With DPI Awareness (FIXED):
```
Physical screen: 2560 x 1440
Windows tells app: 2560 x 1440 (truth!)
Vision sees: 2560 x 1440
Agent clicks: 2560 x 1440
Result: Clicks accurate! ✓
```

---

## ✅ Success Checklist

Before integrating into main app, verify:

- [ ] `01_dpi_detection.py` shows "DPI aware"
- [ ] `01_dpi_detection.py` shows "PyAutoGUI matches system"
- [ ] `02_visual_click_test.py` clicks land on targets
- [ ] `03_screenshot_coordinate_test.py` clicks accurate
- [ ] `04_comprehensive_dpi_fix.py` shows "ALL TESTS PASSED"
- [ ] Import order verified: DPI awareness → pyautogui
- [ ] Test in main app shows accurate clicks

When all checked ✓ → DPI fix is working!

---

## 📚 Additional Resources

**Windows DPI Awareness**:
- https://docs.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows

**PyAutoGUI + DPI**:
- https://github.com/asweigart/pyautogui/issues/

**Scaling Issues**:
- https://github.com/python-pillow/Pillow/issues/

---

## 🎯 Quick Start

**Just want to test if it works?**

```bash
# Run comprehensive test
python tests/mouse_dpi_debug/04_comprehensive_dpi_fix.py

# If it shows "ALL TESTS PASSED" → You're good!
# If not → Follow recommendations in output
```

**Want visual confirmation?**

```bash
# Open visual tester
python tests/mouse_dpi_debug/02_visual_click_test.py

# Click targets - red X should land on target centers
```

**That's it!** If both pass, your DPI fix works correctly.

