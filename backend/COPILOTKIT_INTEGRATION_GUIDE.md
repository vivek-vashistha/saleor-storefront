# CopilotKit Integration Guide

This guide explains how to integrate your Conversational Commerce Backend with CopilotKit's chat popup.

## 🚀 Quick Start

### 1. Backend Setup

Your backend is now ready for CopilotKit integration! The following endpoints are available:

- **Chat Completions**: `POST /v1/chat/completions`
- **Streaming Chat**: `POST /v1/chat/completions/stream`
- **Models**: `GET /v1/models`
- **Health Check**: `GET /health`

### 2. Frontend Setup

Install CopilotKit dependencies in your frontend:

```bash
npm install @copilotkit/react-core @copilotkit/react-ui
```

### 3. Configure CopilotKit Provider

Wrap your main application with the CopilotKit provider:

```jsx
import { CopilotKit } from "@copilotkit/react-core";

function App() {
	return (
		<CopilotKit runtimeUrl="http://localhost:8000/v1/chat/completions">
			{/* Your application components */}
			<CopilotPopup />
		</CopilotKit>
	);
}
```

### 4. Add Chat Popup

```jsx
import { CopilotPopup } from "@copilotkit/react-ui";

function App() {
	return (
		<CopilotKit runtimeUrl="http://localhost:8000/v1/chat/completions">
			{/* Your application components */}
			<CopilotPopup />
		</CopilotKit>
	);
}
```

## 🔧 Available Endpoints

### Chat Completions

- **URL**: `POST /v1/chat/completions`
- **Description**: Main chat endpoint for CopilotKit
- **Request Format**: OpenAI-compatible chat completions format
- **Response**: Chat response with AI-generated content

### Streaming Chat

- **URL**: `POST /v1/chat/completions/stream`
- **Description**: Streaming version for real-time responses
- **Request Format**: Same as chat completions with `stream: true`
- **Response**: Server-sent events stream

### Models

- **URL**: `GET /v1/models`
- **Description**: Available models for CopilotKit
- **Response**: List of available models (gpt-4, gpt-4o)

## 🎯 CopilotKit Actions

Your backend provides several actions that CopilotKit can use:

### 1. Product Search

- **Endpoint**: `POST /v1/actions/search-products`
- **Description**: Search for products based on queries
- **Parameters**:
  - `query` (string, required): Search query
  - `categories` (array, optional): Product categories
  - `max_results` (integer, optional): Maximum results

### 2. Order Status Check

- **Endpoint**: `POST /v1/actions/check-order-status`
- **Description**: Check user order status
- **Parameters**:
  - `user_email` (string, required): User's email
  - `order_id` (string, optional): Specific order ID

### 3. Product Recommendations

- **Endpoint**: `POST /v1/actions/get-product-recommendations`
- **Description**: Get personalized recommendations
- **Parameters**:
  - `user_preferences` (object, required): User preferences
  - `activity_type` (string, optional): Activity type
  - `budget_range` (string, optional): Budget range

## 🔄 How It Works

1. **User sends message** through CopilotKit chat popup
2. **CopilotKit forwards** the message to your backend at `/v1/chat/completions`
3. **Backend processes** the message using your existing conversational AI workflow
4. **AI agents analyze** the message and determine appropriate actions
5. **Product search/order check** happens if needed
6. **Response is generated** and sent back to CopilotKit
7. **User sees response** in the chat popup

## 🎨 Frontend Integration Examples

### Basic Integration

```jsx
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

function App() {
	return (
		<CopilotKit runtimeUrl="http://localhost:8000/v1/chat/completions">
			<div className="app">
				<h1>My E-commerce Store</h1>
				{/* Your store content */}
				<CopilotPopup />
			</div>
		</CopilotKit>
	);
}
```

### With Custom Styling

```jsx
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

function App() {
	return (
		<CopilotKit runtimeUrl="http://localhost:8000/v1/chat/completions">
			<div className="app">
				<h1>My E-commerce Store</h1>
				{/* Your store content */}
				<CopilotPopup
					instructions="You are a helpful shopping assistant for an outdoor gear store. Help users find products, check orders, and get recommendations."
					labels={{
						title: "Shopping Assistant",
						initial: "Hi! I'm here to help you find the perfect outdoor gear. What are you looking for?",
					}}
				/>
			</div>
		</CopilotKit>
	);
}
```

### With State Sharing

```jsx
import { CopilotKit, useCopilotReadable } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";

function ProductList({ products }) {
	// Share product data with CopilotKit
	useCopilotReadable({
		description: "Current products displayed on the page",
		value: products,
	});

	return (
		<div>
			{products.map((product) => (
				<div key={product.id}>{product.name}</div>
			))}
		</div>
	);
}

function App() {
	const [products, setProducts] = useState([]);

	return (
		<CopilotKit runtimeUrl="http://localhost:8000/v1/chat/completions">
			<div className="app">
				<h1>My E-commerce Store</h1>
				<ProductList products={products} />
				<CopilotPopup />
			</div>
		</CopilotKit>
	);
}
```

## 🔧 Configuration Options

### Environment Variables

Make sure these environment variables are set in your backend:

```env
# OpenAI API Key (required for AI agents)
OPENAI_API_KEY=your_openai_api_key

# Database connections
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Saleor integration
SALEOR_HOST=localhost
SALEOR_PORT=8002

# MongoDB for chat sessions
MONGODB_HOST=localhost
MONGODB_PORT=27017
```

### CORS Configuration

Your backend is configured to allow all origins for development. For production, update the CORS settings in `main.py`:

```python
application.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Your frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

## 🧪 Testing

### Test the Backend

1. Start your backend:

```bash
cd backend
uv run uvicorn backend.presentation.api.main:app --reload --port 8000
```

2. Test the CopilotKit endpoint:

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I need hiking boots for winter camping"}
    ],
    "model": "gpt-4"
  }'
```

3. Test streaming:

```bash
curl -X POST "http://localhost:8000/v1/chat/completions/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are your best tent recommendations?"}
    ],
    "model": "gpt-4",
    "stream": true
  }'
```

### Test CopilotKit Actions

```bash
# Test product search
curl -X POST "http://localhost:8000/v1/actions/search-products" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hiking boots",
    "max_results": 3
  }'

# Test order status
curl -X POST "http://localhost:8000/v1/actions/check-order-status" \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "user@example.com"
  }'
```

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure your frontend domain is allowed in CORS settings
2. **Connection Refused**: Ensure your backend is running on the correct port
3. **Authentication Errors**: Check that OpenAI API key is set correctly
4. **Database Connection**: Verify Neo4j, MongoDB, and other databases are running

### Debug Mode

Enable debug logging in your backend:

```python
import logging
logging.getLogger("conversational_commerce").setLevel(logging.DEBUG)
```

### Check Logs

Monitor your backend logs for CopilotKit requests:

```bash
# Look for these log messages:
# "Created new CopilotKit session: {session_id}"
# "Processing message: '{message}' for session {session_id}"
# "Found {count} products for query: '{query}'"
```

## 🎉 You're Ready!

Your backend is now fully integrated with CopilotKit! Users can:

- ✅ Chat with your AI shopping assistant
- ✅ Search for products through conversation
- ✅ Check their order status
- ✅ Get personalized recommendations
- ✅ Have their preferences remembered across sessions

The integration leverages all your existing conversational AI capabilities while providing a modern chat interface through CopilotKit.
