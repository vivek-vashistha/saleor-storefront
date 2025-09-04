# Others Folder - Saleor GraphQL Integration

Basic setup and running instructions for the Saleor GraphQL integration.

## 🚀 Quick Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file with:

```
OPENAI_API_KEY=your_openai_api_key
SALEOR_ENDPOINT=https://your-saleor-instance.com/graphql/
SALEOR_TOKEN=your_saleor_api_token
CHANNEL_SLUG=default-channel
```

## 🏃‍♂️ Running the Application

### Terminal 1: Start the API Server

```bash
python new_salor_api_server.py
```

Server will run on http://localhost:8002 with auto-reload enabled.

### Terminal 2: Run Test Client

```bash
python test_salor_graph_api.py
```

## 📁 Files

- `new_salor_graph.py` - Main LangGraph implementation
- `new_salor_api_server.py` - FastAPI server (port 8002)
- `test_salor_graph_api.py` - Test client for orders endpoint
- `new_graph_test_client.py` - Test client for chat bot endpoint
- `requirements.txt` - Python dependencies
