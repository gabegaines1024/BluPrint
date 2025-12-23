#!/bin/bash
# Quick start script for BluPrint FastAPI application

echo "🚀 Starting BluPrint FastAPI Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

# Create instance directory if it doesn't exist
mkdir -p instance

# Set default environment variables if not set
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export RELOAD=${RELOAD:-true}
export LOG_LEVEL=${LOG_LEVEL:-info}

echo "📊 Configuration:"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Auto-reload: $RELOAD"
echo "   Log level: $LOG_LEVEL"
echo ""
echo "📚 API Documentation will be available at:"
echo "   http://localhost:$PORT/api/docs"
echo ""
echo "🏥 Health check endpoint:"
echo "   http://localhost:$PORT/health"
echo ""

# Run the application
python main.py

