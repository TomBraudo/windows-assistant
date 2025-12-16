@echo off
echo ======================================================================
echo MOUSE DPI DEBUG - AUTOMATED TEST SUITE
echo ======================================================================
echo.
echo This will run all DPI tests in sequence to verify the fix works.
echo.
pause

echo.
echo ======================================================================
echo TEST 1/3: DPI Detection
echo ======================================================================
echo.
python tests\mouse_dpi_debug\01_dpi_detection.py
if errorlevel 1 (
    echo.
    echo [FAILED] Test 1 failed
    pause
    exit /b 1
)
echo.
echo [PASSED] Test 1 completed
pause

echo.
echo ======================================================================
echo TEST 2/3: Comprehensive DPI Fix Test
echo ======================================================================
echo.
python tests\mouse_dpi_debug\04_comprehensive_dpi_fix.py
if errorlevel 1 (
    echo.
    echo [FAILED] Test 2 failed
    pause
    exit /b 1
)
echo.
echo [PASSED] Test 2 completed
pause

echo.
echo ======================================================================
echo TEST 3/3: Visual Click Test (Manual)
echo ======================================================================
echo.
echo This test requires manual verification.
echo Click the target circles and verify red X marks land on target centers.
echo.
pause
python tests\mouse_dpi_debug\02_visual_click_test.py

echo.
echo ======================================================================
echo ALL AUTOMATED TESTS COMPLETE
echo ======================================================================
echo.
echo Summary:
echo - Test 1: DPI Detection [PASSED]
echo - Test 2: Comprehensive Fix [PASSED]
echo - Test 3: Visual Verification [Manual Check Required]
echo.
echo If all tests passed:
echo   ✓ DPI fix is working correctly
echo   ✓ Coordinates should be accurate
echo   ✓ Ready to use in main app
echo.
echo If any test failed:
echo   Read tests\mouse_dpi_debug\README.md for troubleshooting
echo.
pause

