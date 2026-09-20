@echo off
setlocal
cd /d "%~dp0\.."
python -m pip install -r requirements-dev.txt
python -m pytest -q
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "GPT-Image-Studio" main.py
echo.
echo Build complete: dist\GPT-Image-Studio.exe
pause
