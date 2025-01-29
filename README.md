# Keyswitch Tester App

A full-stack application for testing mechanical keyboard switches, featuring real-time monitoring and data collection.

## Features

- Real-time monitoring of switch testing stations
- Customizable test parameters
- Current and voltage monitoring
- Failure detection for both mechanical and electrical issues
- Test cycle counting and limits
- Dark/Light theme support
- Timer functionality for test duration control

## Project Structure

- `frontend/` - SvelteKit web application
- `backend/` - Python backend server
- `.venv/` - Python virtual environment

## Prerequisites

- Node.js (v18 or higher)
- Python 3.8+
- pip (Python package manager)

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

## License

MIT License - See LICENSE file for details 