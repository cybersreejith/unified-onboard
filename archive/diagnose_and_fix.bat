@echo off
echo 🔍 LangGraph Installation Diagnostics and Auto-Fix
echo.

echo === SYSTEM DIAGNOSTICS ===
echo.

echo Python Version:
python --version
echo.

echo Pip Version:
pip --version
echo.

echo Checking for Rust/Cargo:
cargo --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Rust/Cargo is installed:
    cargo --version
    set RUST_AVAILABLE=1
) else (
    echo ❌ Rust/Cargo not found
    set RUST_AVAILABLE=0
)
echo.

echo Checking for Conda:
conda --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Conda is available:
    conda --version
    set CONDA_AVAILABLE=1
) else (
    echo ❌ Conda not found
    set CONDA_AVAILABLE=0
)
echo.

echo Checking for Docker:
docker --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Docker is available:
    docker --version
    set DOCKER_AVAILABLE=1
) else (
    echo ❌ Docker not found
    set DOCKER_AVAILABLE=0
)
echo.

echo === RECOMMENDED SOLUTION ===
echo.

if %CONDA_AVAILABLE%==1 (
    echo 🥇 BEST OPTION: Use Conda environment
    echo This avoids all Rust compilation issues.
    echo.
    choice /C YN /M "Do you want to setup Conda environment now"
    if !ERRORLEVEL!==1 (
        call setup_conda_langgraph.bat
        goto :end
    )
)

if %RUST_AVAILABLE%==1 (
    echo 🥈 GOOD OPTION: Install LangGraph with Rust support
    echo.
    choice /C YN /M "Do you want to install LangGraph with Rust now"
    if !ERRORLEVEL!==1 (
        pip install langgraph langchain langchain-core fastapi uvicorn
        python -c "import langgraph; print('✅ Success!')"
        goto :end
    )
)

if %DOCKER_AVAILABLE%==1 (
    echo 🥉 DOCKER OPTION: Use containerized environment
    echo.
    choice /C YN /M "Do you want to use Docker"
    if !ERRORLEVEL!==1 (
        docker-compose up -d
        echo Docker containers started. Access at http://localhost:12000
        goto :end
    )
)

echo 🔧 FALLBACK OPTION: Force binary-only installation
echo This tries to install pre-compiled wheels only.
echo.
choice /C YN /M "Do you want to try binary-only installation"
if !ERRORLEVEL!==1 (
    call fix_rust_error.bat
    goto :end
)

echo.
echo 🆘 LAST RESORT: Use simple agents (no LangGraph)
echo This provides identical functionality without Rust dependencies.
echo.
choice /C YN /M "Do you want to use simple agents instead"
if !ERRORLEVEL!==1 (
    echo Starting simple agent server...
    python api/server_windows.py
    goto :end
)

echo.
echo 📋 MANUAL STEPS NEEDED:
echo.
echo 1. Install Miniconda: https://docs.conda.io/en/latest/miniconda.html
echo 2. Run: setup_conda_langgraph.bat
echo.
echo OR
echo.
echo 1. Install Rust: https://rustup.rs/
echo 2. Restart terminal
echo 3. Run: pip install langgraph
echo.
echo OR
echo.
echo 1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
echo 2. Run: docker-compose up

:end
echo.
echo Script completed.
pause