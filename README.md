# Unified Onboard - IDP Migration System

An agentic automation solution for seamless data migration between different Identity Provider (IDP) systems including AUTHE1.0, AUTHE2.0, and AUTHENG.

## Architecture

### Components
- **Frontend**: React.js application with 3 main pages
  - Source/Destination Selection
  - Migration Status Monitoring
  - Analytics Dashboard
- **Backend**: Python-based agents using LangGraph
  - One-time Migrator Agent (bulk migration)
  - Runtime Migrator Agent (real-time transaction migration)
- **Mock API**: REST API server for user migration endpoints
- **Data Transformers**: Schema transformation logic between IDP systems

### Supported IDP Systems
- AUTHE1.0
- AUTHE2.0
- AUTHENG

## Project Structure
```
unified-onboard/
├── frontend/          # React.js UI application
├── backend/
│   ├── agents/        # LangGraph-based migration agents
│   ├── api/           # Mock API server
│   ├── schemas/       # Data schemas for different IDP systems
│   └── transformers/  # Data transformation logic
└── docs/              # Documentation
```

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- npm or yarn

### Installation
1. Clone the repository
2. Install frontend dependencies: `cd frontend && npm install`
3. Install backend dependencies: `cd backend && pip install -r requirements.txt`
4. Start the mock API server: `cd backend/api && python server.py`
5. Start the React application: `cd frontend && npm start`

## Features
- Multi-IDP system support with automatic schema detection
- Real-time migration status monitoring
- Bulk and incremental data migration
- Data transformation with validation
- Analytics dashboard with migration metrics
