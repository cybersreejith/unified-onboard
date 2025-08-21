@echo off
echo Setting up LangGraph with Conda (Recommended for Windows)...
echo.

echo Step 1: Creating conda environment...
conda create -n langgraph-env python=3.11 -y
echo.

echo Step 2: Activating environment...
call conda activate langgraph-env
echo.

echo Step 3: Installing core dependencies via conda-forge...
conda install -c conda-forge pydantic -y
conda install -c conda-forge fastapi -y
conda install -c conda-forge uvicorn -y
conda install -c conda-forge requests -y
conda install -c conda-forge numpy -y
conda install -c conda-forge pandas -y
echo.

echo Step 4: Installing LangGraph via pip...
pip install langgraph==0.0.69
pip install langchain==0.1.20
pip install langchain-core==0.1.52
pip install langchain-community==0.0.38
echo.

echo Step 5: Installing additional dependencies...
pip install python-multipart==0.0.6
echo.

echo Step 6: Verifying installation...
python -c "import langgraph; import langchain; import langchain_core; print('LangGraph installation successful!')"
echo.

echo Setup complete! 
echo.
echo To use this environment:
echo 1. conda activate langgraph-env
echo 2. cd backend
echo 3. python api/server.py
echo.
pause