#!/usr/bin/env python3
"""
Cross-platform server startup script for Unified Onboard IDP Migration System
"""
import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_langgraph():
    """Check if LangGraph is available"""
    try:
        import langgraph
        print("✅ LangGraph available")
        return True
    except ImportError:
        print("❌ LangGraph not available")
        return False

def check_dependencies():
    """Check if basic dependencies are available"""
    required = ['fastapi', 'uvicorn', 'requests']
    missing = []
    
    for dep in required:
        if importlib.util.find_spec(dep) is None:
            missing.append(dep)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        return False
    
    print("✅ Basic dependencies available")
    return True

def start_langgraph_server():
    """Start the LangGraph-powered server"""
    print("\n🚀 Starting LangGraph-powered server...")
    print("Server will be available at: http://localhost:12001")
    print("API documentation at: http://localhost:12001/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        os.chdir('api')
        subprocess.run([sys.executable, 'server.py'])
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def start_simple_server():
    """Start the Windows-compatible simple server"""
    print("\n🚀 Starting Windows-compatible server (simple agents)...")
    print("Server will be available at: http://localhost:12001")
    print("API documentation at: http://localhost:12001/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        os.chdir('api')
        subprocess.run([sys.executable, 'server_windows.py'])
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    print("🚀 Unified Onboard IDP Migration Server Startup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not os.path.exists('api/server.py'):
        print("❌ Please run this script from the backend directory")
        print(f"Current directory: {os.getcwd()}")
        print("Expected files: api/server.py")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n📋 Install dependencies with:")
        print("pip install -r requirements.txt")
        print("or")
        print("pip install -r requirements-windows.txt")
        sys.exit(1)
    
    # Check LangGraph availability
    has_langgraph = check_langgraph()
    
    if has_langgraph:
        print("\n✅ All systems ready!")
        start_langgraph_server()
    else:
        print("\n⚠️  LangGraph not available. Using simple agents.")
        print("\nTo install LangGraph:")
        print("- Windows: run fix_rust_error.bat or setup_conda_langgraph.bat")
        print("- Linux/Mac: pip install langgraph langchain langchain-core")
        print("\nStarting with simple agents for now...")
        
        try:
            input("\nPress Enter to continue with simple agents, or Ctrl+C to exit...")
            start_simple_server()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()