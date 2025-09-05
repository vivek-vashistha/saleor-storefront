# Frontend Integration Guide for CopilotKit

This guide will help you integrate the Conversational Commerce Backend with CopilotKit in your frontend application.

## Prerequisites

- Node.js and npm installed
- Your backend server running on `http://localhost:8000`
- A React/Next.js frontend application

## Installation

1. Install CopilotKit packages:

```bash
npm install @copilotkit/react-core @copilotkit/react-ui
```

## Basic Setup

### 1. Configure CopilotKit Provider

Wrap your app with the CopilotKit provider:

```tsx
// app/layout.tsx or your main app component
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en">
			<body>
				<CopilotKit runtimeUrl="http://localhost:8000/v1/chat/completions">
					{children}
					<CopilotPopup />
				</CopilotKit>
			</body>
		</html>
	);
}
```

### 2. Alternative: Manual Integration

If you prefer more control, you can integrate manually:

```tsx
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

function App() {
	return (
		<CopilotKit
			runtimeUrl="http://localhost:8000/v1/chat/completions"
			publicApiKey="your-api-key" // Optional
		>
			<div className="app">
				{/* Your app content */}
				<h1>My Shopping App</h1>

				{/* Add the chat popup */}
				<CopilotPopup />
			</div>
		</CopilotKit>
	);
}
```

## Advanced Configuration

### Custom Actions Integration

If you want to use the custom actions (search_products, check_order_status, etc.), you can define them in your frontend:

```tsx
import { useCopilotAction } from "@copilotkit/react-core";

function ProductSearch() {
	const { execute } = useCopilotAction({
		name: "search_products",
		description: "Search for products",
		parameters: [
			{
				name: "query",
				type: "string",
				description: "Search query",
				required: true,
			},
			{
				name: "max_results",
				type: "number",
				description: "Maximum results",
				required: false,
			},
		],
		handler: async ({ query, max_results }) => {
			const response = await fetch("http://localhost:8000/v1/actions/search_products", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ query, max_results }),
			});
			return await response.json();
		},
	});

	return <button onClick={() => execute({ query: "hiking boots" })}>Search Products</button>;
}
```

### Custom Chat Interface

You can also create a custom chat interface:

```tsx
import { useCopilotChat } from "@copilotkit/react-core";

function CustomChat() {
	const { messages, appendMessage, isLoading } = useCopilotChat();

	return (
		<div className="chat-container">
			<div className="messages">
				{messages.map((message, index) => (
					<div key={index} className={`message ${message.role}`}>
						{message.content}
					</div>
				))}
			</div>
			<form
				onSubmit={async (e) => {
					e.preventDefault();
					const input = e.target.message.value;
					await appendMessage({ role: "user", content: input });
					e.target.message.value = "";
				}}
			>
				<input name="message" placeholder="Ask about products..." />
				<button type="submit" disabled={isLoading}>
					{isLoading ? "Sending..." : "Send"}
				</button>
			</form>
		</div>
	);
}
```

## Environment Configuration

### Development

For development, make sure your backend is running on `http://localhost:8000` and configure CORS properly.

### Production

For production, update the `runtimeUrl` to point to your production backend:

```tsx
<CopilotKit runtimeUrl="https://your-backend-domain.com/v1/chat/completions">
```

## Troubleshooting

### Common Issues

1. **"No content" error**: This usually means the backend endpoints are not responding correctly. Check:

   - Backend server is running
   - CORS is configured properly
   - Endpoints are accessible

2. **CORS errors**: Make sure your backend has CORS configured to allow your frontend domain.

3. **Connection refused**: Check that the backend URL is correct and the server is running.

### Testing the Integration

1. Start your backend server:

   ```bash
   cd backend
   python -m uvicorn backend.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Test the endpoints manually:

   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/v1/models
   ```

3. Start your frontend and test the chat popup.

## Available Endpoints

Your backend provides these endpoints for CopilotKit:

- `GET /health` - Health check
- `GET /v1/models` - Available AI models
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/chat/completions/stream` - Streaming chat
- `GET /v1/actions` - Available actions
- `POST /v1/actions/search_products` - Search products
- `POST /v1/actions/check_order_status` - Check order status
- `POST /v1/actions/get_product_recommendations` - Get recommendations

## Example Usage

Once integrated, users can:

1. **Ask about products**: "I'm looking for hiking boots for winter camping"
2. **Get recommendations**: "What hiking gear do you recommend for beginners?"
3. **Check orders**: "What's the status of my recent order?"
4. **Get product details**: "Tell me more about the Mountain 600 hiking boots"

The AI will automatically use the appropriate backend actions to provide relevant responses with real product data from your Neo4j database and Saleor integration.

## Next Steps

1. Customize the chat interface styling
2. Add more specific actions for your use case
3. Implement user authentication if needed
4. Add product images and rich content to responses
5. Set up monitoring and analytics

For more information, refer to the [CopilotKit documentation](https://docs.copilotkit.ai/).
