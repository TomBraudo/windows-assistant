@echo off
echo ======================================================================
echo OMNIPARSER TEST - CHROME ICON DETECTION
echo ======================================================================
echo.
echo This test will:
echo 1. Capture your screen
echo 2. Send to OmniParser API (10-20 seconds)
echo 3. Find Chrome icon coordinates
echo 4. Show visualization
echo 5. Optionally click to verify
echo.
echo Prerequisites:
echo - REPLICATE_API_TOKEN in .env file
echo - pip install replicate
echo - Internet connection
echo.
pause

python tests\mouse_dpi_debug\05_omniparser_test.py

echo.
echo ======================================================================
echo Test complete! Check the visualization:
echo   tests\mouse_dpi_debug\omniparser_output\chrome_target_visualization.png
echo.
echo If green box is around Chrome icon ^→ OmniParser works!
echo If not ^→ Try adjusting box_threshold or search terms
echo ======================================================================
pause

