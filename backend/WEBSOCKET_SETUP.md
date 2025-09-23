# WebSocket Setup Guide

This guide will help you set up WebSocket support for your conversational commerce application.

## Quick Fix for the Error

The error you're seeing indicates that uvicorn doesn't have WebSocket support. Here's how to fix it:

### 1. Install WebSocket Dependencies

```bash
# Navigate to the backend directory
cd backend

# Install the updated dependencies
uv sync

# Or run the installation script
./install_websocket_deps.sh
```

### 2. Verify Installation

```bash
# Test WebSocket support
python -c "import websockets; print('WebSocket support installed!')"
```

### 3. Start the Backend

```bash
# Start with WebSocket support
uv run uvicorn backend.presentation.api.main:app --host 0.0.0.0 --port 4003 --reload
```

## What Was Fixed

1. **Updated pyproject.toml**:

   - Changed `uvicorn>=0.34.0` to `uvicorn[standard]>=0.34.0`
   - Added `websockets>=12.0` dependency

2. **WebSocket Support**: The `[standard]` extra includes WebSocket support for uvicorn

## Testing WebSocket

### 1. Test Backend WebSocket Endpoint

```bash
# Run the test script (make sure backend is running)
python test_websocket.py
```

### 2. Test from Browser Console

```javascript
// Open browser console and test WebSocket connection
const ws = new WebSocket("ws://localhost:4003/v1/sessions/test-session/ws");
ws.onopen = () => console.log("Connected!");
ws.onmessage = (event) => console.log("Message:", JSON.parse(event.data));
ws.onerror = (error) => console.error("Error:", error);
```

### 3. Enable Frontend WebSocket

```bash
# Set environment variable to enable WebSocket in frontend
export NEXT_PUBLIC_ENABLE_WEBSOCKET=true

# Start the frontend
npm run dev
```

## Docker Setup

If you're using Docker, the dependencies will be automatically installed when you rebuild:

```bash
# Rebuild the Docker image
docker-compose build backend

# Start the services
docker-compose up backend
```

## Troubleshooting

### Common Issues

1. **"No supported WebSocket library detected"**

   - Solution: Run `uv sync` to install the updated dependencies

2. **Connection refused**

   - Make sure the backend is running on port 4003
   - Check if the WebSocket endpoint is accessible

3. **CORS errors**
   - The WebSocket endpoint should work with the existing CORS configuration

### Debug Steps

1. **Check if WebSocket dependencies are installed**:

   ```bash
   python -c "import websockets, uvicorn; print('Dependencies OK')"
   ```

2. **Verify backend is running**:

   ```bash
   curl http://localhost:4003/health
   ```

3. **Test WebSocket endpoint**:
   ```bash
   python test_websocket.py
   ```

## Production Deployment

For production deployment, make sure to:

1. **Use HTTPS/WSS**: Change `ws://` to `wss://` for secure connections
2. **Load Balancer**: Ensure your load balancer supports WebSocket connections
3. **Environment Variables**: Set `NEXT_PUBLIC_ENABLE_WEBSOCKET=true` in production

## Next Steps

Once WebSocket is working:

1. **Enable in Frontend**: Set the environment variable
2. **Test Real-time Features**: Send messages and watch for streaming updates
3. **Monitor Performance**: Check connection stability and reconnection logic

The WebSocket implementation provides real-time message streaming, tool call updates, and enhanced user experience!
