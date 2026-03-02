#!/bin/bash

# Start the invoice tool backend with OpenAI API key

cd "$(dirname "$0")"

# Source the zshrc to get the API key
if [ -f ~/.zshrc ]; then
    source ~/.zshrc
fi

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY not found!"
    echo ""
    echo "Please set your OpenAI API key:"
    echo "  export OPENAI_API_KEY='sk-your-key-here'"
    echo ""
    echo "Or run: ./setup_openai.sh"
    exit 1
fi

echo "✅ OpenAI API Key detected: ${OPENAI_API_KEY:0:10}...${OPENAI_API_KEY: -4}"
echo ""

# Activate virtual environment
source venv/bin/activate

# Stop any existing backend
pkill -f "python.*app.py" 2>/dev/null

echo "🚀 Starting backend with AI features enabled..."
echo ""

# Start the backend
python3 backend/app.py

