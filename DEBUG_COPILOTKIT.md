# CopilotKit Debug Guide

## Current Status

✅ **Backend Processing**: Working correctly - LangGraph agents process messages and generate responses
✅ **GraphQL Response Format**: Fixed to include proper `__typename` fields and structure
❌ **Frontend Display**: Messages not appearing in CopilotKit chat popup

## Debug Steps

### 1. Test Backend Directly

Open `debug_frontend.html` in your browser to test the backend GraphQL endpoint directly.

### 2. Check Browser Console

1. Open your frontend at `http://localhost:3000`
2. Open browser Developer Tools (F12)
3. Go to Console tab
4. Look for any errors when you try to send a message

### 3. Check Network Tab

1. In Developer Tools, go to Network tab
2. Try sending a message in the chat popup
3. Look for requests to `http://localhost:8000/v1/chat/completions`
4. Check if the request is being made and what the response looks like

### 4. CopilotKit Configuration

Current configuration:

- Runtime URL: `http://localhost:8000/v1/chat/completions`
- Show Dev Console: `true` (should show debug info)

### 5. Expected vs Actual Flow

**Expected:**

1. User types message in CopilotKit popup
2. CopilotKit sends GraphQL `generateCopilotResponse` mutation to backend
3. Backend processes with LangGraph agents
4. Backend returns GraphQL response with message content
5. CopilotKit displays the response in chat

**Check each step:**

- ✅ Step 1: Chat popup appears and accepts input
- ❓ Step 2: Check Network tab for outgoing requests
- ✅ Step 3: Backend logs show processing
- ✅ Step 4: Backend returns proper GraphQL format
- ❌ Step 5: Response not displayed

## Potential Issues

### Issue 1: CORS

Check if there are CORS errors in browser console.

### Issue 2: Response Format

CopilotKit might expect streaming responses due to `@stream` directive in query.

### Issue 3: Version Compatibility

CopilotKit version 1.10.3 might have specific requirements.

### Issue 4: Runtime URL

CopilotKit might expect different endpoint format.

## Testing Commands

```bash
# Test backend health
curl http://localhost:8000/health

# Test GraphQL endpoint (PowerShell)
Invoke-RestMethod -Uri "http://localhost:8000/v1/chat/completions" -Method POST -ContentType "application/json" -Body '{"operationName":"generateCopilotResponse","query":"mutation generateCopilotResponse($data: GenerateCopilotResponseInput!) { generateCopilotResponse(data: $data) { threadId runId status { code } messages { __typename ... on TextMessageOutput { content role } } } }","variables":{"data":{"messages":[{"textMessage":{"content":"test","role":"user"}}],"threadId":"test"}}}'
```

## Next Steps

1. **Check browser console** for any JavaScript errors
2. **Check network requests** to see if they're reaching the backend
3. **Try different CopilotKit configuration** options
4. **Test with simplified response** to isolate the issue

## Logs to Watch

**Backend logs should show:**

```
INFO :: Detected CopilotKit GraphQL request
INFO :: Handling generateCopilotResponse mutation
INFO :: Extracted user message: '[message]'
INFO :: Using LangGraph agent response: [response]
INFO :: Returning GraphQL response with content length: [number]
```

**Browser console should show:**

- No CORS errors
- Successful network requests to backend
- CopilotKit debug messages (if showDevConsole=true)

The issue is likely in the frontend-backend communication or CopilotKit configuration, not in the LangGraph processing itself.
