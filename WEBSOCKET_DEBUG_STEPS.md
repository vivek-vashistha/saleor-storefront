# WebSocket Debug Steps

## Current Issue

- Backend is processing messages (logs show "Message processing completed")
- Frontend is not receiving messages
- No final message is generated from backend

## Debug Steps

### 1. **Test WebSocket Connection**

Open the test file in browser:

```
file:///path/to/src/features/chatbot/test-websocket-connection.html
```

### 2. **Check Browser Console**

Look for these debug messages:

- `🔌 WebSocket connection opened`
- `🔔 WebSocket message received:`
- `📤 Sending message:`

### 3. **Check Backend Logs**

Look for these in the backend terminal:

- `WebSocket connected for existing session`
- `[WEBSOCKET] Processing message for session`
- `[WEBSOCKET] Message processing completed for session`

### 4. **Test Session Creation**

Check if session is being created:

- Look for "Session initialized:" in browser console
- Check if conversationId is set
- Verify WebSocket connects after session creation

### 5. **Check Message Flow**

1. **Frontend sends message** → Look for `📤 Sending message:` in console
2. **Backend receives message** → Look for `[WEBSOCKET] Processing message` in backend logs
3. **Backend processes message** → Look for `[WEBSOCKET] Message processing completed`
4. **Backend sends response** → Look for WebSocket send operations
5. **Frontend receives response** → Look for `🔔 WebSocket message received:` in console

## Potential Issues

### Issue 1: Session Not Created

**Symptoms:** No session ID, WebSocket doesn't connect
**Fix:** Check session initialization in browser console

### Issue 2: WebSocket Not Connecting

**Symptoms:** Connection fails, no debug logs
**Fix:** Check WebSocket URL, backend running on port 4003

### Issue 3: Messages Not Sent

**Symptoms:** No `📤 Sending message:` logs
**Fix:** Check if WebSocket is connected before sending

### Issue 4: Backend Not Processing

**Symptoms:** No backend logs for message processing
**Fix:** Check WebSocket endpoint, message format

### Issue 5: Backend Not Sending Response

**Symptoms:** Backend processes but no response sent
**Fix:** Check WebSocket manager, message sending logic

### Issue 6: Frontend Not Receiving

**Symptoms:** Backend sends but frontend doesn't receive
**Fix:** Check WebSocket message handler, message format

## Debug Commands

### Test WebSocket Connection:

```bash
cd backend && python test_websocket_simple.py
```

### Test Session WebSocket:

```bash
cd backend && python test_session_websocket.py
```

### Check Backend Logs:

Look for these patterns in backend terminal:

- `WebSocket connected for existing session`
- `[WEBSOCKET] Processing message for session`
- `[WEBSOCKET] Message processing completed for session`

## Next Steps

1. **Open test HTML file** in browser
2. **Check browser console** for debug messages
3. **Check backend terminal** for processing logs
4. **Identify where the flow breaks**
5. **Fix the specific issue**

The debug version will show exactly where the WebSocket communication is failing!
