@echo off
echo Setting up LangGraph on Windows...
echo.

echo Step 0: Clearing pip cache...
pip cache purge
echo.

echo Step 1: Upgrading pip and setuptools...
python -m pip install --upgrade pip setuptools wheel
echo.


echo Step 2: Installing dependencies from requirements.txt...
@REM ISSUE IN NUMPY - C++ / VISUAL STUDIO DEPENDENCY
pip install --no-deps --only-binary=:all: numpy
pip install --only-binary=all -r requirements.txt
echo.

echo Step 3: Verifying installation...
python -c "import langgraph; import langchain; import langchain_core; print('LangGraph installation successful!')"
echo.

echo Setup complete! You can now run:
echo python api/server.py
pause