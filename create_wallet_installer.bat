@echo off
echo ==================================================
echo    TORCOIN WALLET INSTALLER CREATOR
echo ==================================================
echo.
echo Creating a distributable TorCOIN Wallet installer...
echo.

:: Create installer directory
if exist "TorCOIN_Wallet_Installer" rmdir /s /q "TorCOIN_Wallet_Installer"
mkdir "TorCOIN_Wallet_Installer"

:: Copy required files
echo 📁 Copying wallet files...
copy "torcoin_wallet.py" "TorCOIN_Wallet_Installer\" >nul
copy "README.md" "TorCOIN_Wallet_Installer\" >nul

:: Create launcher script
echo 📄 Creating launcher script...
(
echo @echo off
echo echo ==================================================
echo echo         TORCOIN WALLET LAUNCHER
echo echo ==================================================
echo echo.
echo echo Starting TorCOIN Wallet...
echo echo.
echo python torcoin_wallet.py
echo.
echo echo Wallet closed.
echo pause
) > "TorCOIN_Wallet_Installer\Run_TorCOIN_Wallet.bat"

:: Create desktop shortcut creator
echo 🔗 Creating desktop shortcut...
(
echo @echo off
echo echo Creating desktop shortcut for TorCOIN Wallet...
echo.
echo set SCRIPT="%TEMP%\CreateShortcut.vbs"
echo.
echo ^(
echo echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo echo sLinkFile = oWS.ExpandEnvironmentStrings^("%%USERPROFILE%%\Desktop\TorCOIN Wallet.lnk"^)
echo echo Set oLink = oWS.CreateObject^("WScript.Shell"^).CreateShortcut^(sLinkFile^)
echo echo oLink.TargetPath = "%%~dp0Run_TorCOIN_Wallet.bat"
echo echo oLink.WorkingDirectory = "%%~dp0"
echo echo oLink.Description = "TorCOIN Wallet - Privacy-First Digital Currency"
echo echo oLink.IconLocation = "%%SystemRoot%%\System32\SHELL32.dll,13"
echo echo oLink.Save
echo ^) ^> %%SCRIPT%%
echo.
echo cscript //nologo %%SCRIPT%%
echo del %%SCRIPT%%
echo.
echo echo ✅ Desktop shortcut created!
echo echo You can now double-click "TorCOIN Wallet" on your desktop.
echo pause
) > "TorCOIN_Wallet_Installer\Create_Desktop_Shortcut.bat"

:: Create requirements file
echo 📋 Creating requirements file...
(
echo TorCOIN Wallet Requirements:
echo ==============================
echo.
echo Minimum Requirements:
echo • Windows 10 or later
echo • Python 3.8 or higher
echo • 100 MB free disk space
echo • 512 MB RAM
echo.
echo Recommended:
echo • Windows 11
echo • Python 3.9+
echo • 1 GB RAM
echo • Fast internet connection
echo.
echo Installation:
echo 1. Ensure Python is installed
echo 2. Run: Run_TorCOIN_Wallet.bat
echo 3. Optional: Create_Desktop_Shortcut.bat
echo.
echo For help, visit: https://www.torcoin.cnet/support
) > "TorCOIN_Wallet_Installer\README.txt"

:: Create uninstaller
echo 🗑️ Creating uninstaller...
(
echo @echo off
echo echo ==================================================
echo echo      TORCOIN WALLET UNINSTALLER
echo echo ==================================================
echo echo.
echo echo This will remove TorCOIN Wallet from your system.
echo echo Your wallet files will NOT be deleted.
echo echo.
echo pause
echo.
echo echo Removing desktop shortcut...
echo if exist "%%USERPROFILE%%\Desktop\TorCOIN Wallet.lnk" del "%%USERPROFILE%%\Desktop\TorCOIN Wallet.lnk"
echo.
echo echo Removing start menu entry...
echo if exist "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TorCOIN Wallet.lnk" del "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TorCOIN Wallet.lnk"
echo.
echo echo ✅ TorCOIN Wallet uninstalled successfully!
echo echo.
echo echo Your wallet files are safe in the installation folder.
echo pause
) > "TorCOIN_Wallet_Installer\Uninstall.bat"

:: Create version info
echo 📅 Creating version info...
(
echo TorCOIN Wallet v1.3.0
echo Released: November 2024
echo.
echo What's New in v1.3.0:
echo • 💳 FREE Virtual Debit Cards - Get instant virtual cards
echo • 🏦 Bank Integration - Connect bank accounts using Plaid
echo • 💳 Bank Transfers - Transfer funds between bank and TorCOIN
echo • 🏦 Bank Account Management - View connected bank accounts
echo • 💰 Bank Balance Display - Real-time bank account balances
echo • 🔄 Seamless Transfers - Bank ↔ TorCOIN wallet transfers
echo • 📱 Virtual Card App - Dedicated card management application
echo • 🎁 Free Card Generation - AI-powered unique card creation
echo • 💳 Card Transactions - Full send/receive and reporting
echo.
echo What's New in v1.0:
echo • Complete GUI wallet interface
echo • Send & receive TorCOIN
echo • Transaction history
echo • Address management
echo • Security features
echo • Dark theme UI
echo • Cross-platform compatibility
echo.
echo System Requirements:
echo • Python 3.8+
echo • Windows 10+
echo • 100MB disk space
echo.
echo For updates, visit: https://www.torcoin.cnet/downloads
) > "TorCOIN_Wallet_Installer\version.txt"

:: Create ZIP archive
echo 📦 Creating installer package...
if exist "TorCOIN_Wallet_v1.3.0.zip" del "TorCOIN_Wallet_v1.3.0.zip"
powershell "Compress-Archive -Path 'TorCOIN_Wallet_Installer\*' -DestinationPath 'TorCOIN_Wallet_v1.3.0.zip' -Force"

echo.
echo ==================================================
echo ✅ TORCOIN WALLET INSTALLER CREATED!
echo ==================================================
echo.
echo 📁 Files created in: TorCOIN_Wallet_Installer\
echo 📦 Archive created: TorCOIN_Wallet_v1.3.0.zip
echo.
echo 📋 Installer Contents:
echo • torcoin_wallet.py - Main wallet application
echo • Run_TorCOIN_Wallet.bat - Launcher script
echo • Create_Desktop_Shortcut.bat - Desktop shortcut creator
echo • README.txt - Installation instructions
echo • Uninstall.bat - Uninstaller script
echo • version.txt - Version information
echo.
echo 🌐 Ready for download at:
echo https://www.torcoin.cnet/downloads/TorCOIN_Wallet_v1.3.0.zip
echo.
echo 📊 Package size: 
dir /b TorCOIN_Wallet_v1.0.zip | for %%A in (TorCOIN_Wallet_v1.0.zip) do echo %%~zA bytes
echo.
echo 🎉 TorCOIN Wallet is ready for distribution!
echo.

pause
