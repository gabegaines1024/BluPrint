@echo off
REM Quick start script for BluPrint FastAPI application (Windows)

echo 🚀 Starting BluPrint FastAPI Server...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    if not exist ".venv" (
        echo ⚠️  No virtual environment found. Creating one...
        python -m venv venv
        call venv\Scripts\activate.bat
        echo 📦 Installing dependencies...
        pip install -r requirements.txt
    ) else (
        call .venv\Scripts\activate.bat
    )
) else (
    call venv\Scripts\activate.bat
)

REM Create instance directory if it doesn't exist
if not exist "instance" mkdir instance

REM Set default environment variables if not set
if "%HOST%"=="" set HOST=0.0.0.0
if "%PORT%"=="" set PORT=8000
if "%RELOAD%"=="" set RELOAD=true
if "%LOG_LEVEL%"=="" set LOG_LEVEL=info

echo 📊 Configuration:
echo    Host: %HOST%
echo    Port: %PORT%
echo    Auto-reload: %RELOAD%
echo    Log level: %LOG_LEVEL%
echo.
echo 📚 API Documentation will be available at:
echo    http://localhost:%PORT%/api/docs
echo.
echo 🏥 Health check endpoint:
echo    http://localhost:%PORT%/health
echo.

REM Run the application
python main.py

