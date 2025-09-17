# CopilotKit Frontend Setup Guide

## Correct runtime endpoint for SearchQueryWorkflow

Your backend already exposes the official CopilotKit runtime at `/copilotkit_remote`, wired to your `SearchQueryWorkflow` via the adapter:

- Backend SDK wiring: `add_fastapi_endpoint(application, sdk, "/copilotkit_remote")`
- Agent name: `conversational_commerce_agent`

The frontend must point to that endpoint (NOT `/v1/chat/completions`).

### 1) Create `.env.local`

```bash
# CopilotKit Configuration (use the SDK endpoint)
NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL=http://localhost:8000/copilotkit_remote
```

Note: If you leave this unset, `src/app/providers.tsx` already defaults to `http://localhost:8000/copilotkit_remote`.

### 2) Start backend

```bash
cd backend
uv run uvicorn backend.presentation.api.main:app --reload --port 8000
```

Ensure CORS is enabled (it is in the app) and backend `/health` returns OK.

### 3) Start frontend

```bash
pnpm dev
```

Visit `http://localhost:3000` and open the chat popup.

## Troubleshooting

- **Popup loads but replies fail**: Verify the runtime URL is `/copilotkit_remote` (Network tab). Using `/v1/chat/completions` will not work with the CopilotKit SDK UI.
- **CORS/network errors**: Confirm backend runs on `:8000` and allows `*` origins in development.
- **No popup**: Check `ClientProviders` includes `CopilotKit` and renders `<ChatPopup />`.

## Expected behavior

You should see the chat popup, and messages will be processed by the `SearchQueryWorkflow` through the `ConversationalCommerceAdapter` and returned to the UI.

## Relevant files

- `src/app/providers.tsx` – sets `runtimeUrl` and agent name
- `backend/backend/presentation/api/main.py` – registers CopilotKit SDK endpoint `/copilotkit_remote`
- `backend/backend/presentation/api/copilotkit_adapter.py` – adapts `SearchQueryWorkflow` to CopilotKit
