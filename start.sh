#!/bin/bash

echo "🚀 Starting Invoice Tool..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start backend in background
echo "Starting backend server on http://localhost:5001..."
python backend/app.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend
echo "Starting frontend on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for Ctrl+C
echo ""
echo "✅ Application is running!"
echo "   Backend:  http://localhost:5001"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop..."

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    deactivate
    exit
}

# Trap Ctrl+C and kill both processes
trap cleanup INT

wait
