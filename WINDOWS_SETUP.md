# 🪟 Windows Setup Guide

This guide helps you run the Unified Onboard IDP Migration System on Windows without Rust compilation issues.

## 🚨 Issue Resolution

The original LangGraph implementation requires Rust compilation which can be problematic on Windows. This setup provides a **Windows-compatible version** that maintains all functionality without the compilation issues.

## 📋 Prerequisites

- Python 3.8+ installed
- Node.js 16+ installed
- Git installed

## 🛠️ Backend Setup (Windows Compatible)

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Windows-Compatible Dependencies
```bash
pip install -r requirements-windows.txt
```

### 4. Run Windows-Compatible Server
```bash
python api/server_windows.py
```

The backend will start on: `http://localhost:12001`

## 🎨 Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
npm start
```

The frontend will start on: `http://localhost:3000`

## 🔧 What's Different in Windows Version?

### ✅ **Maintained Features:**
- ✅ Complete migration workflow (9 steps)
- ✅ OneTime and Runtime migration agents
- ✅ Data transformation between AUTHE1.0, AUTHE2.0, AUTHENG
- ✅ Real-time progress tracking
- ✅ Error handling and validation
- ✅ All 3 React pages (Setup, Status, Dashboard)
- ✅ Interactive charts and statistics
- ✅ REST API endpoints

### 🔄 **Technical Changes:**
- **Simple Agents**: Uses `simple_agents.py` instead of LangGraph
- **No Rust Dependencies**: Avoids compilation issues
- **Same Workflow**: Maintains identical 9-step migration process
- **Compatible API**: Same endpoints and responses
- **Async Support**: Full async/await support maintained

## 🚀 Usage

### 1. **Access the Application**
Open your browser and go to: `http://localhost:3000`

### 2. **Migration Setup Page**
- Select source system (AUTHE1.0, AUTHE2.0, AUTHENG)
- Select destination system
- Choose migration type (One Time or Runtime)
- Click "Start Migration"

### 3. **Migration Status Page**
- View real-time progress
- Monitor success/failure rates
- Auto-refresh functionality

### 4. **Dashboard Page**
- Overall statistics
- Migration trends
- Success rate charts
- Recent job history

## 🧪 Testing

### Test Migration via API
```bash
# Create migration
curl -X POST "http://localhost:12001/migrations" \
  -H "Content-Type: application/json" \
  -d '{
    "source_system": "AUTHE1.0",
    "destination_system": "AUTHE2.0",
    "migration_type": "onetime"
  }'

# Check status (replace JOB_ID with actual ID)
curl "http://localhost:12001/migrations/JOB_ID"
```

## 📊 Expected Results

### **Migration Metrics:**
- **Success Rate**: ~98% (realistic simulation)
- **OneTime Migration**: 100 records (98 success, 2 failures)
- **Runtime Migration**: 1 record (100% success)
- **Processing Time**: Near-instant for demo data

### **Dashboard Statistics:**
- Total jobs tracking
- Success rate visualization
- Migration trends over time
- System-specific patterns

## 🔍 Troubleshooting

### **Port Conflicts**
If ports 3000 or 12001 are in use:
```bash
# Frontend - change port
set PORT=3001 && npm start

# Backend - edit server_windows.py line with port=12002
```

### **Python Path Issues**
Make sure you're in the backend directory when running:
```bash
cd backend
python api/server_windows.py
```

### **Module Import Errors**
Ensure virtual environment is activated:
```bash
venv\Scripts\activate
```

## 🎯 Production Deployment

For production deployment on Windows:

1. **Use Production WSGI Server:**
```bash
pip install gunicorn
gunicorn api.server_windows:app --bind 0.0.0.0:12001
```

2. **Build React for Production:**
```bash
cd frontend
npm run build
```

3. **Serve Static Files:**
Use IIS or nginx to serve the built React files.

## 🔄 Switching Back to LangGraph

If you want to use the full LangGraph version later (after resolving Rust issues):

1. Install Rust: https://rustup.rs/
2. Use original `requirements.txt`
3. Use original `api/server.py`

## 📞 Support

If you encounter any issues with the Windows setup:

1. Check Python version: `python --version`
2. Check Node version: `node --version`
3. Verify virtual environment is activated
4. Check port availability: `netstat -an | findstr :12001`

---

**🎉 This Windows-compatible version provides the same functionality as the LangGraph version without compilation issues!**