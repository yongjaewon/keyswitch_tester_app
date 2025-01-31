# Ignition Switch Tester App

A full-stack application for testing ignition switches (key-operated rotary switches), featuring real-time monitoring and data collection.

## Features

- Real-time monitoring of up to 4 testing stations
- Customizable test parameters:
  - Motor current threshold
  - Switch current threshold
  - Cycle limits
  - Cycles per minute
  - Supply voltage cutoff
- Automatic failure detection:
  - Motor current monitoring
  - Switch current monitoring
  - Cycle counting
- Test control features:
  - Master enable/disable
  - Individual station control
  - Timer functionality (up to 99 hours)
  - Auto-stop on failures or limits
- Real-time data collection and history tracking
- Dark/Light theme support
- WebSocket-based real-time updates
- Automatic reconnection handling

## Project Structure

- `frontend/` - SvelteKit web application with TypeScript
  - Real-time monitoring interface
  - Test control panel
  - Settings management
  - Connection state handling
- `backend/` - Python FastAPI server
  - WebSocket communication
  - Arduino serial communication
  - SQLite database for state and history
  - Background tasks for monitoring
- `.venv/` - Python virtual environment

## Prerequisites

- Node.js (v18 or higher)
- Python 3.8+
- pip (Python package manager)
- Arduino-compatible microcontroller
- USB serial connection to Arduino

## Setup

### Backend

1. Create and activate the virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Start the backend server:
```bash
python main.py
```
The database will be automatically created and initialized with default settings:
- Default PIN: "1234"
- Default cycles per minute: 6
- Default cutoff voltage: 11.1V
- Default current thresholds: 100A (motor), 5A (switch)
- Default cycle limit: 100,000
- Default failure thresholds: 10 (both motor and switch)

Note: If you need to reset the database to default values at any time:
```bash
python init_database.py --reset
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

Or build for production:
```bash
npm run build
```

## Development

- Frontend runs on http://localhost:5173 by default
- Backend API runs on http://localhost:8000 by default
- WebSocket connection on ws://localhost:8000/ws
- Arduino communication on /dev/ttyUSB0 (default) at 115200 baud

## Hardware Requirements

- Arduino-compatible microcontroller
- Current sensors for each station (motor and switch)
- Voltage sensor for supply monitoring
- Servo motors for key rotation
- USB serial connection to host computer

## License

MIT License - See LICENSE file for details 