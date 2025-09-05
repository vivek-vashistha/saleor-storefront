# CopilotKit Frontend Setup Guide

## Quick Fix for "No content" Error

The issue you're experiencing is likely due to the missing environment variable. Here's how to fix it:

### 1. Create Environment File

Create a `.env.local` file in your project root with the following content:

```bash
# CopilotKit Configuration
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=http://localhost:8000/v1/chat/completions
```

### 2. Restart Your Frontend

After creating the `.env.local` file, restart your Next.js development server:

```bash
# Stop the current server (Ctrl+C)
# Then restart
pnpm dev
```

### 3. Verify Backend is Running

Make sure your backend is running on port 8000:

```bash
cd backend
uv run uvicorn backend.presentation.api.main:app --reload --port 8000
```

### 4. Test the Integration

1. Open your frontend at `http://localhost:3000`
2. Look for the CopilotKit chat popup (usually a chat icon in the bottom right)
3. Click on it and try asking: "I'm looking for hiking boots"

## Troubleshooting

### If you still get "No content" error:

1. **Check browser console** for any CORS or network errors
2. **Verify backend is accessible** by visiting `http://localhost:8000/health` in your browser
3. **Check the runtime URL** in your browser's network tab when the popup loads

### If the popup doesn't appear:

1. **Check if CopilotKit is properly imported** in your layout
2. **Verify the ChatPopup component** is included in your providers
3. **Check browser console** for any JavaScript errors

### Common Issues:

1. **CORS errors**: The backend should already have CORS configured, but if you see CORS errors, make sure the backend is running
2. **Wrong port**: Make sure both frontend (3000) and backend (8000) are running on the correct ports
3. **Environment variable**: Make sure `NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL` is set correctly

## Expected Behavior

When working correctly, you should see:

1. A chat popup icon in your frontend
2. The popup opens when clicked
3. You can ask questions like "I'm looking for hiking boots"
4. The AI responds with product recommendations from your backend

## Next Steps

Once the basic integration is working:

1. Customize the chat instructions in `CopilotPopup.tsx`
2. Add more specific actions for your use case
3. Style the popup to match your design
4. Add user authentication if needed

## Files Modified

The following files have been updated to fix the integration:

1. `src/app/providers.tsx` - Fixed runtime URL configuration
2. `backend/backend/presentation/api/routes/copilot.py` - Fixed validation errors
3. `backend/backend/presentation/api/main.py` - Added CORS configuration
4. `backend/backend/presentation/api/containers/container.py` - Updated wiring

## Support

If you continue to have issues, check:

1. Backend logs for any errors
2. Browser console for frontend errors
3. Network tab to see if requests are being made correctly
