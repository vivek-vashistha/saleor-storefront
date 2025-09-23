# WebSocket Debug Guide

## Issues Fixed

### 1. **Missing Initial Message**

- ✅ Added the initial bot welcome message
- ✅ Added personalized message logic for users
- ✅ Matches original chat experience

### 2. **Missing State Variables**

- ✅ Added `messageType` state with correct typing
- ✅ Added `productMessageTimestamp` state
- ✅ Added proper product handling logic

### 3. **WebSocket Message Processing**

- ✅ Fixed message type handling
- ✅ Added proper product recommendation processing
- ✅ Added error handling

### 4. **Debug Capabilities**

- ✅ Created debug WebSocket hook with logging
- ✅ Created debug chat session hook
- ✅ Created debug container with debug log display

## How to Test

### 1. **Enable WebSocket Mode**

```bash
export NEXT_PUBLIC_ENABLE_WEBSOCKET=true
npm run dev
```

### 2. **Check Debug Log**

The debug version will show:

- WebSocket connection status
- Debug log with connection attempts
- Real-time message processing
- Tool call updates

### 3. **Test WebSocket Connection**

1. Open the chat
2. Check the debug log section
3. Look for connection messages
4. Send a test message

### 4. **Expected Behavior**

- ✅ Initial welcome message appears
- ✅ WebSocket connects successfully
- ✅ Messages are sent via WebSocket
- ✅ Real-time updates are received
- ✅ Product recommendations work
- ✅ Same experience as original chat

## Debug Information

The debug version shows:

- **Connection Status**: Green/Red indicator
- **Debug Log**: Last 5 log entries
- **Tool Calls**: Active tool executions
- **Thinking Updates**: Current processing status
- **Streaming Messages**: Real-time message chunks

## Troubleshooting

### If WebSocket Doesn't Connect:

1. Check backend is running on port 4003
2. Check browser console for errors
3. Look at debug log for connection attempts
4. Verify WebSocket URL in debug log

### If Messages Don't Appear:

1. Check WebSocket connection status
2. Look for error messages in debug log
3. Check if session is being created
4. Verify message format in debug log

### If Products Don't Show:

1. Check if product recommendations are received
2. Look for product message type changes
3. Verify product data structure
4. Check product panel rendering

## Files Created/Modified

### New Debug Files:

- `useWebSocketDebug.ts` - Debug WebSocket hook
- `useChatSessionWebSocketDebug.ts` - Debug chat session hook
- `ChatbotContainerWebSocketDebug.tsx` - Debug container

### Modified Files:

- `useChatSessionWebSocket.ts` - Fixed to match original experience
- `ChatbotContainer.tsx` - Uses debug version when WebSocket enabled

## Next Steps

1. **Test the Debug Version**: Enable WebSocket and test functionality
2. **Check Debug Log**: Look for connection and message issues
3. **Verify Experience**: Ensure it matches original chat behavior
4. **Switch to Production**: Once working, switch back to non-debug version

The debug version will help identify exactly where the WebSocket communication is failing!
