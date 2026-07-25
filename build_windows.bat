@echo off
REM Build script for Windows - Visualisateur Psychedelique
REM Requires: Python 3.12+, PyInstaller, NSIS (optional)

echo ========================================
echo Visualisateur Psychedelique - Windows Build
echo ========================================

echo.
echo [1/5] Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 ( echo FAILED & exit /b 1 )

pip install pyinstaller
if %ERRORLEVEL% neq 0 ( echo FAILED & exit /b 1 )

echo.
echo [2/5] Downloading ffmpeg...
python scripts\download_ffmpeg_windows.py ffmpeg_bin
if %ERRORLEVEL% neq 0 ( echo FAILED & exit /b 1 )

echo.
echo [3/5] Building portable EXE with PyInstaller...
python -m PyInstaller build_windows.spec --clean
if %ERRORLEVEL% neq 0 ( echo FAILED & exit /b 1 )

echo.
echo [4/5] Build complete!
echo    Portable: dist\Visualisateur_Psychedelique_portable\

echo.
echo [5/5] To create installer (requires NSIS installed):
echo    "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
echo.
echo Done!
