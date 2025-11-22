@echo off
echo ==================================================
echo    TORCOIN WALLET EXECUTABLE BUILDER
echo ==================================================
echo.

echo Building TorCOIN Wallet executable...
echo This may take a few minutes...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller --quiet

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

REM Build the executable
pyinstaller --onefile --windowed --name "TorCOIN_Wallet_v1.3.0" "..\torcoin_wallet.py"

REM Check if build was successful
if exist "dist\TorCOIN_Wallet_v1.3.0.exe" (
    echo.
    echo ==================================================
    echo ✅ EXECUTABLE BUILD SUCCESSFUL!
    echo ==================================================
    echo.
    echo 📁 Executable created: dist\TorCOIN_Wallet_v1.3.0.exe
    echo 📊 File size:

    REM Copy to downloads directory
    if not exist "torcoin-website\public\downloads" mkdir "torcoin-website\public\downloads"
    copy "dist\TorCOIN_Wallet_v1.3.0.exe" "torcoin-website\public\downloads\"

    echo.
    echo ✅ Copied to website downloads: torcoin-website\public\downloads\TorCOIN_Wallet_v1.3.0.exe
    echo.
    echo 🎉 TorCOIN Wallet executable is ready for distribution!
) else (
    echo.
    echo ==================================================
    echo ❌ EXECUTABLE BUILD FAILED!
    echo ==================================================
    echo.
    echo Please check the error messages above and try again.
)

echo.
pause
