@echo off
echo 🦀 Installing Rust on Windows for LangGraph
echo.

echo Checking if Rust is already installed...
cargo --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Rust is already installed!
    cargo --version
    goto :install_langgraph
)

echo Rust not found. Installing Rust...
echo.

echo Option 1: Installing via Chocolatey (if available)...
choco --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Chocolatey found. Installing Rust...
    choco install rust -y
    goto :verify_rust
)

echo Option 2: Downloading rustup-init.exe...
echo Please wait while downloading Rust installer...

powershell -Command "& {Invoke-WebRequest -Uri 'https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe' -OutFile 'rustup-init.exe'}"

if exist rustup-init.exe (
    echo Running Rust installer...
    rustup-init.exe -y --default-toolchain stable
    del rustup-init.exe
) else (
    echo ❌ Failed to download Rust installer.
    echo Please manually install from: https://rustup.rs/
    goto :manual_install
)

:verify_rust
echo.
echo Refreshing environment variables...
call refreshenv >nul 2>&1

echo Verifying Rust installation...
cargo --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Rust installed successfully!
    cargo --version
    rustc --version
    goto :install_langgraph
) else (
    echo ❌ Rust installation failed or not in PATH.
    echo Please restart your terminal and try again.
    goto :manual_install
)

:install_langgraph
echo.
echo 🐍 Now installing LangGraph with Rust support...
pip install --upgrade pip setuptools wheel
pip install langgraph langchain langchain-core fastapi uvicorn requests

echo.
echo Verifying LangGraph installation...
python -c "import langgraph; import langchain; print('✅ LangGraph with Rust support installed successfully!')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 🎉 SUCCESS! Everything is installed and working.
    echo You can now run: python api/server.py
) else (
    echo ❌ LangGraph installation failed.
    echo Try the binary-only approach: fix_rust_error.bat
)
goto :end

:manual_install
echo.
echo 📋 MANUAL INSTALLATION STEPS:
echo.
echo 1. Go to: https://rustup.rs/
echo 2. Download and run rustup-init.exe
echo 3. Follow the installation prompts
echo 4. Restart your terminal
echo 5. Run this script again
echo.
echo OR use our binary-only approach:
echo fix_rust_error.bat

:end
echo.
pause