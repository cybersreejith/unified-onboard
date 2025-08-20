# LangGraph Setup Solutions for Windows

## Problem
LangGraph dependencies require Rust compilation on Windows, causing installation failures.

## Solution 1: Install Pre-compiled Wheels (Recommended)

### Step 1: Upgrade pip and install wheel
```bash
python -m pip install --upgrade pip setuptools wheel
```

### Step 2: Install specific versions with pre-compiled wheels
```bash
pip install --only-binary=all pydantic==2.5.2
pip install --only-binary=all pydantic-core==2.14.6
pip install --only-binary=all langchain-core==0.1.52
pip install --only-binary=all langchain==0.1.20
pip install --only-binary=all langgraph==0.0.69
```

### Step 3: Install remaining dependencies
```bash
pip install fastapi==0.104.1 uvicorn==0.24.0 requests==2.31.0
```

## Solution 2: Use Conda Environment (Highly Recommended)

### Step 1: Install Miniconda
Download from: https://docs.conda.io/en/latest/miniconda.html

### Step 2: Create conda environment
```bash
conda create -n langgraph-env python=3.11
conda activate langgraph-env
```

### Step 3: Install from conda-forge
```bash
conda install -c conda-forge pydantic
conda install -c conda-forge langchain
pip install langgraph==0.0.69
pip install fastapi uvicorn
```

## Solution 3: Use Docker (Production Ready)

### Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 12001

CMD ["python", "api/server.py"]
```

### Run with Docker
```bash
docker build -t langgraph-migration .
docker run -p 12001:12001 langgraph-migration
```

## Solution 4: Install Rust Toolchain Properly

### Step 1: Install Visual Studio Build Tools
Download and install: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Select "C++ build tools"
- Include Windows 10/11 SDK

### Step 2: Install Rust
```bash
# Download and run rustup-init.exe from https://rustup.rs/
# Or use chocolatey:
choco install rust
```

### Step 3: Restart terminal and install LangGraph
```bash
pip install langgraph langchain langchain-core
```

## Solution 5: Use WSL2 (Windows Subsystem for Linux)

### Step 1: Install WSL2
```bash
wsl --install
```

### Step 2: Install Python in WSL2
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 3: Install LangGraph in WSL2
```bash
pip3 install langgraph langchain langchain-core fastapi uvicorn
```

## Solution 6: Alternative LangGraph Installation

### Try different LangGraph versions
```bash
# Try older version first
pip install langgraph==0.0.55

# Or try latest pre-release
pip install --pre langgraph
```

### Use specific index URL
```bash
pip install -i https://pypi.org/simple/ langgraph
```

## Solution 7: Manual Dependency Resolution

### Create requirements-manual.txt
```txt
# Install these in order
pydantic==2.5.2
pydantic-core==2.14.6
typing-extensions==4.8.0
langchain-core==0.1.52
langchain-community==0.0.38
langchain==0.1.20
langgraph==0.0.69
fastapi==0.104.1
uvicorn==0.24.0
```

### Install one by one
```bash
pip install pydantic==2.5.2
pip install pydantic-core==2.14.6
pip install typing-extensions==4.8.0
pip install langchain-core==0.1.52
pip install langchain-community==0.0.38
pip install langchain==0.1.20
pip install langgraph==0.0.69
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
```

## Recommended Approach for Windows

**I recommend Solution 2 (Conda) as the most reliable:**

1. Install Miniconda
2. Create conda environment with Python 3.11
3. Use conda-forge for core packages
4. Use pip only for LangGraph-specific packages

This approach avoids most compilation issues and provides a clean environment.

## Verification

After successful installation, verify with:
```python
import langgraph
import langchain
import langchain_core
print("LangGraph installation successful!")
print(f"LangGraph version: {langgraph.__version__}")
```

## Troubleshooting

If you still encounter issues:
1. Clear pip cache: `pip cache purge`
2. Use virtual environment: `python -m venv venv && venv\Scripts\activate`
3. Try Python 3.11 instead of 3.12/3.13
4. Check Windows version compatibility

Choose the solution that best fits your development environment!