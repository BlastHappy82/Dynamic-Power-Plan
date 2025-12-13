@echo off
echo ========================================
echo Building Dynamic Power Plan Tray App
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --clean DynamicPowerPlan.spec

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo The executable is located at: dist\DynamicPowerPlan.exe
echo.
echo To distribute, copy the following to a folder:
echo   - dist\DynamicPowerPlan.exe
echo   - config.json
echo   - MB_on\ folder
echo   - MB_off\ folder
echo   - backup\ folder (optional)
echo.
pause
