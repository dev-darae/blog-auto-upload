@echo off
SETLOCAL EnableDelayedExpansion

TITLE Blog Auto Upload - Windows Launcher

echo ========================================================
echo        Blog Auto Upload Automation - Windows Setup
echo ========================================================
echo.

:: 1. Check for Python Installation
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [INFO] Python is not found in PATH.
    echo [INFO] Attempting to install Python 3.11 using Winget...
    
    winget install -e --id Python.Python.3.11
    
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Winget installation failed.
        echo [ACTION REQUIRED] Please install Python 3.11+ manually from: https://www.python.org/downloads/
        echo [INFO] Ensure you check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    
    echo [INFO] Python installed successfully. Please restart this script to pick up the new PATH.
    pause
    exit /b 0
)

:: 1.5 Check for Google Chrome Installation
echo [INFO] Checking for Google Chrome...
set "CHROME_FOUND=0"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"

if "!CHROME_FOUND!"=="0" (
    echo [WARNING] Google Chrome not found in standard locations!
    echo [ACTION REQUIRED] This automation requires Google Chrome.
    echo [INFO] If you have a custom installation, you can ignore this warning.
    echo [INFO] Otherwise, please install it from: https://www.google.com/chrome/
    echo.
    echo Press any key to continue anyway...
    pause >nul
) else (
    echo [INFO] Google Chrome found.
)

:: 2. Setup Virtual Environment
echo [INFO] Checking virtual environment...
if not exist "venv" (
    echo [INFO] Creating virtual environment 'venv'...
    python -m venv venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created.
)

:: 3. Activate Virtual Environment
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

:: 4. Install Dependencies
echo [INFO] Installing/Updating dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 5. Check for .env file
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo [INFO] Please create a .env file with your DATABASE_URL and configurations.
    echo [INFO] You can copy .env.example if it exists.
    echo.
)

:: 6. Run the Automation
echo.
echo ========================================================
echo        Starting Automation Script...
echo ========================================================
echo.

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Script finished with errors.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Script finished successfully.
pause
