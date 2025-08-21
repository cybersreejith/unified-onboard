@echo off
echo 🚀 Starting Unified Onboard IDP Migration Server
echo.

echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found. Please install Python first.
    pause
    exit /b 1
)
echo.

echo Checking if we're in the correct directory...
if not exist "api\server.py" (
    echo ❌ Please run this script from the backend directory
    echo Current directory: %CD%
    echo Expected files: api\server.py
    pause
    exit /b 1
)
echo.

echo Checking for virtual environment...
if exist "venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found. Activating...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found. Using system Python.
    echo Consider creating one with: python -m venv venv
)
echo.

echo Checking LangGraph installation...
python -c "import langgraph; print('✅ LangGraph available')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ LangGraph not installed. 
    echo.
    echo Choose an option:
    echo 1. Install LangGraph with Rust support
    echo 2. Use Windows-compatible simple agents
    echo 3. Exit and install manually
    echo.
    choice /C 123 /M "Select option"
    
    if !ERRORLEVEL!==1 (
        echo Installing LangGraph...
        REM call fix_rust_error.bat
        call setup_langgraph_windows.bat

        if !ERRORLEVEL! NEQ 0 (
            echo ❌ LangGraph installation failed. Using simple agents.
            goto :simple_agents
        )
    )
    if !ERRORLEVEL!==2 (
        goto :simple_agents
    )
    if !ERRORLEVEL!==3 (
        echo Please install dependencies and try again.
        pause
        exit /b 1
    )
)

echo.
echo 🚀 Starting LangGraph-powered server...
echo Server will be available at: http://localhost:12001
echo API documentation at: http://localhost:12001/docs
echo.
echo Press Ctrl+C to stop the server
echo.
cd api
python server.py
goto :end

:simple_agents
echo.
echo 🚀 Starting Windows-compatible server (simple agents)...
echo Server will be available at: http://localhost:12001
echo API documentation at: http://localhost:12001/docs
echo.
echo Press Ctrl+C to stop the server
echo.
cd api
python server_windows.py

:end
echo.
echo Server stopped.
pause