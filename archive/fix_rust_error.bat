@echo off
echo 🛠️ Fixing Rust/Cargo Error for LangGraph Installation
echo.

echo Step 1: Clearing pip cache...
pip cache purge
echo.

echo Step 2: Upgrading pip tools...
python -m pip install --upgrade pip setuptools wheel
echo.

echo Step 3: Installing pydantic with binary-only flag...
pip install --only-binary=:all: --upgrade pydantic==2.5.2
echo.

echo Step 4: Installing pydantic-core with binary-only flag...
pip install --only-binary=:all: --upgrade pydantic-core==2.14.6
echo.

echo Step 5: Installing typing-extensions...
pip install --only-binary=:all: typing-extensions==4.8.0
echo.

echo Step 6: Installing langchain-core...
pip install --only-binary=:all: langchain-core==0.1.52
echo.

echo Step 7: Installing langchain...
pip install --only-binary=:all: langchain==0.1.20
echo.

echo Step 8: Installing langgraph...
pip install --only-binary=:all: langgraph==0.0.69
echo.

echo Step 9: Installing FastAPI and other dependencies...
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install requests==2.31.0
pip install python-multipart==0.0.6
echo.

echo Step 10: Verifying installation...
python -c "import langgraph; import langchain; import langchain_core; print('✅ LangGraph installation successful!')"
echo.

if %ERRORLEVEL% EQU 0 (
    echo ✅ SUCCESS! LangGraph is now installed and working.
    echo.
    echo You can now run:
    echo python api/server.py
) else (
    echo ❌ Installation failed. Try these alternatives:
    echo.
    echo 1. Use conda: setup_conda_langgraph.bat
    echo 2. Use Docker: docker-compose up
    echo 3. Use simple agents: python api/server_windows.py
)

echo.
pause