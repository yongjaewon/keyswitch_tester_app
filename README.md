# Keyswitch Tester App

A web application for testing and monitoring keyswitch durability across multiple testing stations.

## Features

- Real-time monitoring of up to 4 testing stations
- Current monitoring for both motor and switch circuits
- Failure detection and automatic shutdown
- Cycle counting and limits
- Timer-based testing
- Dark mode support
- Touch-friendly interface

## Project Structure

- `backend/`: FastAPI backend server
  - REST API endpoints
  - WebSocket for real-time updates
  - SQLite database
  - UART communication with Arduino
- `frontend/`: SvelteKit frontend application
  - Real-time dashboard
  - Settings management
  - Responsive design
  - DaisyUI components

## Setup

### Backend

1. Create a Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_database.py
```

4. Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

## Development

- Backend API runs on: http://localhost:8000
- Frontend development server runs on: http://localhost:5173
- API documentation available at: http://localhost:8000/docs 