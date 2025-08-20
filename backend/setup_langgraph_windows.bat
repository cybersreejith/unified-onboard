@echo off
echo Setting up LangGraph on Windows...
echo.

echo Step 1: Upgrading pip and setuptools...
python -m pip install --upgrade pip setuptools wheel
echo.

echo Step 2: Installing pre-compiled wheels for core dependencies...
pip install --only-binary=all pydantic==2.5.2
pip install --only-binary=all pydantic-core==2.14.6
pip install --only-binary=all typing-extensions==4.8.0
echo.

echo Step 3: Installing LangChain dependencies...
pip install --only-binary=all langchain-core==0.1.52
pip install --only-binary=all langchain-community==0.0.38
pip install --only-binary=all langchain==0.1.20
echo.

echo Step 4: Installing LangGraph...
pip install langgraph==0.0.69
echo.

echo Step 5: Installing FastAPI and other dependencies...
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install requests==2.31.0
pip install python-multipart==0.0.6
echo.

echo Step 6: Verifying installation...
python -c "import langgraph; import langchain; import langchain_core; print('LangGraph installation successful!')"
echo.

echo Setup complete! You can now run:
echo python api/server.py
pause