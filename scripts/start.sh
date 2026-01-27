#!/bin/bash

# Nihongo Dojo Startup Script
# This script starts both the backend and frontend servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Nihongo Dojo..."
echo "Project directory: $PROJECT_DIR"

# Check if Python virtual environment exists
if [ ! -d "$PROJECT_DIR/backend/venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$PROJECT_DIR/backend/venv"
    source "$PROJECT_DIR/backend/venv/bin/activate"
    pip install -r "$PROJECT_DIR/backend/requirements.txt"
else
    source "$PROJECT_DIR/backend/venv/bin/activate"
fi

# Check if .env exists
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    echo ""
    echo "WARNING: No .env file found in backend/"
    echo "Please copy .env.example to .env and configure your settings:"
    echo "  cp backend/.env.example backend/.env"
    echo ""
fi

# Check if node_modules exists
if [ ! -d "$PROJECT_DIR/node_modules" ]; then
    echo "Installing npm dependencies..."
    cd "$PROJECT_DIR"
    npm install
fi

# Start both servers
echo ""
echo "Starting servers..."
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo ""

cd "$PROJECT_DIR"
npm run dev
