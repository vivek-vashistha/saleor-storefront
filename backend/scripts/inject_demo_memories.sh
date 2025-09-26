#!/bin/bash

# Demo Memory Injection Script for iHerb Conversational Commerce
# This script injects fake memories for user "VXNlcjo0OA==" to demonstrate personalization

set -e  # Exit on any error

# Configuration
USER_ID="VXNlcjo0OA=="
API_BASE_URL="http://localhost:4003/v1"
NUM_MEMORIES=25
NUM_ORDERS=8
NUM_REVIEWS=6

echo "🚀 Starting Demo Memory Injection for User: $USER_ID"
echo "=================================================="

# Function to make API calls with error handling
make_api_call() {
    local endpoint="$1"
    local data="$2"
    local description="$3"
    
    echo "📝 $description..."
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        echo "✅ Success: $description"
        echo "   Response: $(echo "$body" | jq -r '.message // .status // "OK"' 2>/dev/null || echo "OK")"
    else
        echo "❌ Error: $description (HTTP $http_code)"
        echo "   Response: $body"
        return 1
    fi
    echo ""
}

# Check if jq is available for JSON parsing
if ! command -v jq &> /dev/null; then
    echo "⚠️  Warning: jq not found. Install with 'brew install jq' for better output formatting"
fi

# Check if server is running
echo "🔍 Checking if server is running..."
if ! curl -s "$API_BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ Server is not running at $API_BASE_URL"
    echo "   Please start your server first with: python -m uvicorn backend.presentation.api.main:app --host 0.0.0.0 --port 4003"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Step 1: Inject comprehensive fake memories
echo "📊 Step 1: Injecting comprehensive fake memories..."
make_api_call "/fake-memories/users/$USER_ID/inject?num_memories=$NUM_MEMORIES&memory_types=user_preference&memory_types=product_interaction&memory_types=conversation_theme&memory_types=order_history" \
    "" \
    "Injecting $NUM_MEMORIES fake memories with real iHerb products"

# Step 2: Inject fake order history
echo "🛒 Step 2: Injecting fake order history..."
make_api_call "/fake-memories/users/$USER_ID/inject-orders?num_orders=$NUM_ORDERS" \
    "" \
    "Injecting $NUM_ORDERS fake order memories with real products"

# Step 3: Inject fake product reviews
echo "⭐ Step 3: Injecting fake product reviews..."
make_api_call "/fake-memories/users/$USER_ID/inject-reviews?num_reviews=$NUM_REVIEWS" \
    "" \
    "Injecting $NUM_REVIEWS fake review memories"

# Step 4: Verify memories were created
echo "🔍 Step 4: Verifying memories were created..."
echo "📊 Checking hybrid memory system..."

response=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/memory/debug/hybrid/$USER_ID")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    mongodb_count=$(echo "$body" | jq -r '.memory_counts.mongodb_memories // 0' 2>/dev/null || echo "Unknown")
    qdrant_count=$(echo "$body" | jq -r '.memory_counts.qdrant_memories // 0' 2>/dev/null || echo "Unknown")
    echo "✅ Hybrid memory verification successful"
    echo "   MongoDB memories: $mongodb_count"
    echo "   Qdrant memories: $qdrant_count"
    
    # Show system status
    mongodb_status=$(echo "$body" | jq -r '.system_status.mongodb // "unknown"' 2>/dev/null || echo "unknown")
    qdrant_status=$(echo "$body" | jq -r '.system_status.qdrant // "unknown"' 2>/dev/null || echo "unknown")
    echo "   MongoDB status: $mongodb_status"
    echo "   Qdrant status: $qdrant_status"
else
    echo "❌ Error verifying hybrid memory system (HTTP $http_code)"
    echo "   Response: $body"
fi

echo ""

# Step 5: Get memory insights
echo "🧠 Step 5: Getting memory insights..."
echo "📈 Retrieving consolidated memory insights..."

response=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/memory/users/$USER_ID/insights")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo "✅ Memory insights retrieved successfully"
    if command -v jq &> /dev/null; then
        echo "   Insights: $(echo "$body" | jq -r '.message // "Available"' 2>/dev/null)"
    else
        echo "   Insights: Available"
    fi
else
    echo "⚠️  Could not retrieve insights (HTTP $http_code)"
fi

echo ""

# Summary
echo "🎉 Demo Memory Injection Complete!"
echo "=================================="
echo "✅ User ID: $USER_ID"
echo "✅ Total memories injected: $NUM_MEMORIES"
echo "✅ Order memories: $NUM_ORDERS"
echo "✅ Review memories: $NUM_REVIEWS"
echo ""
echo "🚀 Ready for Demo!"
echo "=================="
echo "You can now test the personalization by:"
echo "1. Opening your frontend chat interface"
echo "2. Using user ID: $USER_ID"
echo "3. Asking questions like:"
echo "   - 'I have digestive issues and need help with gut health'"
echo "   - 'I'm having trouble sleeping and feel stressed'"
echo "   - 'I'm training for a marathon and need energy support'"
echo "   - 'I want to support healthy aging and skin health'"
echo ""
echo "The system should now reference your fake memories and provide"
echo "personalized recommendations using real iHerb products!"
echo ""
echo "🔗 API Endpoints for testing:"
echo "   - Debug store: $API_BASE_URL/memory/debug/store/$USER_ID"
echo "   - Memory insights: $API_BASE_URL/memory/users/$USER_ID/insights"
echo "   - Retrieve memories: $API_BASE_URL/memory/users/$USER_ID/memories?query=your_query"
