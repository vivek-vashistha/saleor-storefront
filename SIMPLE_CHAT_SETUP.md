# Simple Chat Setup Guide

## Quick Start - Basic Chat Functionality

This guide will help you get the CopilotKit chat popup working with basic Q&A functionality, without the complex LangGraph integration.

### 1. Environment Setup

Create a `.env.local` file in your project root:

```bash
# CopilotKit Configuration
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=/api/copilotkit
```

### 2. Start the Frontend

```bash
pnpm dev
```

The frontend will run on `http://localhost:3000`

### 3. Test the Chat

1. Open your browser to `http://localhost:3000`
2. Look for the chat popup icon (usually in the bottom right corner)
3. Click on it to open the chat
4. Try these test messages:
   - "Hello"
   - "I need help"
   - "I'm looking for products"
   - "What about pricing?"
   - "Tell me about orders"

### 4. How It Works

The simplified implementation:

- **Frontend**: CopilotKit popup sends messages to `/api/copilotkit`
- **API Route**: `src/app/api/copilotkit/route.ts` handles the chat logic
- **Response Logic**: Simple keyword-based responses for common queries
- **Format**: Returns OpenAI-compatible responses that CopilotKit understands

### 5. Current Response Patterns

The chat currently responds to:

- **Greetings**: "hello", "hi" → Welcome message
- **Help requests**: "help" → Lists capabilities
- **Product queries**: "product", "find", "search" → Asks for more details
- **Order questions**: "order", "shipping" → Offers order assistance
- **Pricing**: "price", "cost" → Pricing information help
- **General**: Any other message → Generic helpful response

### 6. Troubleshooting

#### Chat popup doesn't appear:

- Check browser console for JavaScript errors
- Verify CopilotKit styles are loaded
- Make sure `ClientProviders` wraps your app

#### Chat popup appears but doesn't respond:

- Check browser Network tab for failed requests
- Look at browser console for error messages
- Verify the API route is accessible at `/api/copilotkit`

#### Error messages in chat:

- Check the browser console for detailed error logs
- Verify the request/response format in Network tab

### 7. Next Steps

Once basic chat is working, you can:

1. **Enhance responses**: Add more sophisticated logic in `route.ts`
2. **Connect to backend**: Integrate with your LangGraph system
3. **Add actions**: Implement CopilotKit actions for specific tasks
4. **Customize UI**: Style the popup to match your design

### 8. Integration with LangGraph (Future)

When ready to connect to your existing LangGraph system:

1. Modify the API route to call your backend at `http://localhost:8000`
2. Use the existing `/v1/chat/completions` endpoint
3. Handle the complex response format from your agents
4. Add product search and recommendation features

### 9. Files Modified

- `src/app/api/copilotkit/route.ts` - Simplified chat logic
- `src/components/CopilotPopup.tsx` - Removed complex actions
- `.env.local` - Environment configuration

### 10. Testing Commands

```bash
# Test the API route directly
curl -X POST http://localhost:3000/api/copilotkit \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

This should return a JSON response with the assistant's reply.
