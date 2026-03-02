#!/bin/bash

echo "🚀 Setting up Invoice Tool for Future Fabrik..."
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    deactivate
    exit 1
fi

deactivate

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

cd ..

# Create necessary directories
mkdir -p output
mkdir -p templates

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the application:"
echo "  Use the start script: ./start.sh"
echo ""
echo "Or manually:"
echo "  1. Activate venv:      source venv/bin/activate"
echo "  2. Start backend:      python backend/app.py"
echo "  3. Start frontend:     cd frontend && npm run dev"
