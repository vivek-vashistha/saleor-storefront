#!/bin/bash

# Install WebSocket dependencies for the backend
echo "Installing WebSocket dependencies..."

# Update dependencies using uv
uv sync

# Verify WebSocket support
echo "Verifying WebSocket support..."
python -c "import websockets; print('WebSocket support installed successfully')"

echo "WebSocket dependencies installed successfully!"
echo "You can now start the backend with WebSocket support."
