# WebSocket Implementation for Conversational Commerce

This document describes the WebSocket implementation that enables real-time communication between the frontend and backend for the conversational commerce application.

## Overview

The WebSocket implementation provides:

- Real-time message streaming
- Intermediate tool call updates
- Connection health monitoring
- Automatic reconnection
- Fallback to HTTP API

## Architecture

### Backend Components

1. **Connection Manager** (`backend/presentation/api/websocket/connection_manager.py`)

   - Manages WebSocket connections per session
   - Handles message broadcasting
   - Provides utility methods for different message types

2. **WebSocket Endpoint** (`backend/presentation/api/routes/v1/session.py`)

   - `/v1/sessions/{session_id}/ws` - WebSocket endpoint
   - Handles connection lifecycle
   - Processes real-time messages

3. **Message Processing**
   - Integrates with existing `ProcessChatMessageUseCase`
   - Sends intermediate updates during processing
   - Streams response content in chunks

### Frontend Components

1. **WebSocket Hook** (`src/features/chatbot/hooks/useWebSocket.ts`)

   - Manages WebSocket connection
   - Handles reconnection logic
   - Provides message sending/receiving

2. **Enhanced Chat Session Hook** (`src/features/chatbot/hooks/useChatSessionWebSocket.ts`)

   - Extends existing chat session functionality
   - Integrates WebSocket communication
   - Maintains backward compatibility

3. **UI Components**
   - `WebSocketStatus` - Shows connection status and tool calls
   - `StreamingMessage` - Displays real-time message updates
   - `ChatbotContainerWebSocket` - Enhanced chatbot container

## Message Types

### Client to Server

- `ping` - Health check
- `message` - Chat message with content and metadata

### Server to Client

- `connection_established` - Connection confirmation
- `thinking_update` - Current processing status
- `tool_call_update` - Tool execution updates
- `message_chunk` - Streaming message content
- `product_recommendations` - Product suggestions
- `error` - Error messages
- `pong` - Health check response

## Configuration

### Environment Variables

```bash
# Enable WebSocket support in frontend
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
```

### WebSocket Settings

```typescript
export const WEBSOCKET_CONFIG = {
  RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY: 1000,
  PING_INTERVAL: 30000,
  CHUNK_SIZE: 50,
  STREAMING_DELAY: 50,
  TOOL_CALL_TIMEOUT: 30000,
  HEALTH_CHECK_INTERVAL: 10000,
};
```

## Usage

### Enabling WebSocket Support

1. **Backend**: WebSocket endpoints are automatically available
2. **Frontend**: Set environment variable:
   ```bash
   NEXT_PUBLIC_ENABLE_WEBSOCKET=true
   ```

### API Endpoints

- **WebSocket**: `ws://localhost:4003/v1/sessions/{session_id}/ws`
- **HTTP Fallback**: Existing REST endpoints remain available

### Message Flow

1. **Connection**: Client connects to WebSocket endpoint
2. **Authentication**: Session validation
3. **Message Sending**: Real-time message processing
4. **Updates**: Intermediate tool call and thinking updates
5. **Streaming**: Response content streamed in chunks
6. **Products**: Product recommendations sent separately

## Features

### Real-time Updates

- **Thinking Status**: Shows current processing state
- **Tool Calls**: Displays active tool executions
- **Message Streaming**: Content appears as it's generated
- **Product Recommendations**: Real-time product suggestions

### Connection Management

- **Auto-reconnect**: Automatic reconnection on connection loss
- **Health Checks**: Ping/pong for connection monitoring
- **Error Handling**: Graceful fallback to HTTP API
- **Connection Status**: Visual indicators for connection state

### Backward Compatibility

- **Feature Flag**: WebSocket can be enabled/disabled
- **HTTP Fallback**: Falls back to REST API if WebSocket fails
- **Same Interface**: Maintains existing chat interface

## Development

### Testing WebSocket Connection

```javascript
const ws = new WebSocket("ws://localhost:4003/v1/sessions/session_id/ws");
ws.onopen = () => console.log("Connected");
ws.onmessage = (event) => console.log("Message:", JSON.parse(event.data));
```

### Debugging

- Check browser console for WebSocket messages
- Monitor backend logs for connection events
- Use browser dev tools Network tab for WebSocket traffic

## Deployment Considerations

### Production Setup

1. **Load Balancer**: Ensure WebSocket support
2. **SSL/TLS**: Use `wss://` for secure connections
3. **Scaling**: Consider Redis for multi-instance WebSocket management
4. **Monitoring**: Track connection metrics and errors

### Security

- Session validation on connection
- User ID verification for messages
- Rate limiting for WebSocket connections
- CORS configuration for WebSocket origins

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check WebSocket URL and CORS settings
2. **Reconnection Loops**: Verify backend WebSocket endpoint
3. **Message Loss**: Ensure proper error handling and reconnection
4. **Performance**: Monitor connection count and message frequency

### Debug Steps

1. Check browser console for WebSocket errors
2. Verify backend logs for connection events
3. Test WebSocket endpoint directly
4. Check network connectivity and firewall settings
