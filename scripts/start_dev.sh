#!/bin/bash

# Start development server

echo "Starting TechBridge development server..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the server
echo "Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000