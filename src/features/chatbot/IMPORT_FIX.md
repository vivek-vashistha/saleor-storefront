# WebSocket Import Error Fix

## The Problem

The error `'sendMessage' is not exported from '../api/sessionApi'` occurred because:

1. **Wrong Import**: The code was trying to import `sendMessage` from `sessionApi.ts`
2. **Correct Location**: The `sendMessage` function is actually in `messageApi.ts`
3. **Missing Import**: The import statement was incorrect

## The Fix

### Before (Broken)

```typescript
import { initializeSession, sendMessage as sendMessageApi } from "../api/sessionApi";
```

### After (Fixed)

```typescript
import { initializeSession } from "../api/sessionApi";
import { sendMessage as sendMessageApi } from "../api/messageApi";
```

## File Structure

```
src/features/chatbot/api/
├── sessionApi.ts     # Contains: initializeSession, deleteSession, resetUserMemory
├── messageApi.ts     # Contains: sendMessage
└── client.ts         # Contains: getApiClient
```

## What Was Fixed

1. **Corrected Import**: Moved `sendMessage` import to the correct file
2. **Maintained Functionality**: All WebSocket features still work
3. **Added Test File**: Created HTML test page for WebSocket testing

## Testing the Fix

### 1. Frontend Test

Open the test page in your browser:

```
src/features/chatbot/test-websocket.html
```

### 2. Backend Test

```bash
cd backend
python test_websocket_simple.py
```

### 3. Browser Console Test

```javascript
// Test the simple endpoint
const ws = new WebSocket("ws://localhost:4003/v1/test-ws");
ws.onopen = () => console.log("Connected!");
ws.onmessage = (event) => console.log("Message:", JSON.parse(event.data));

// Send test message
ws.send(JSON.stringify({ type: "test", message: "Hello!" }));
```

## Available Endpoints

1. **Test Endpoint**: `ws://localhost:4003/v1/test-ws`

   - Simple echo server
   - No session validation
   - Good for testing basic functionality

2. **Session Endpoint**: `ws://localhost:4003/v1/sessions/{session_id}/ws`
   - Full chat functionality
   - Session validation and creation
   - Real-time message processing

## Next Steps

1. **Test the Fix**: The import error should be resolved
2. **Enable WebSocket**: Set `NEXT_PUBLIC_ENABLE_WEBSOCKET=true`
3. **Test Real-time Features**: Send messages and watch for streaming updates

The WebSocket implementation should now work without import errors!
