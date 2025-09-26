# Memory and Personalization Guide

This document explains how the memory system works for personalizing conversations in the conversational commerce application.

## Overview

The system uses a hybrid memory approach combining:

- **MongoDB**: For structured data, metadata, and relationships
- **Qdrant**: For vector embeddings and semantic search
- **Langmem**: For conversation memory extraction and management

## How Personalization Works

### 1. Memory Types

The system stores several types of memories:

#### User Preferences (`user_preference`)

- Health conditions (diabetes, high blood pressure, etc.)
- Dietary restrictions (vegetarian, vegan, gluten-free, etc.)
- Activity preferences (hiking, running, yoga, etc.)
- Product preferences (brands, materials, quality levels)

#### Product Interactions (`product_interaction`)

- Past purchases and satisfaction levels
- Product reviews and ratings
- Questions asked about specific products
- Product comparisons and recommendations

#### Conversation Themes (`conversation_theme`)

- Recurring topics of interest
- Communication style preferences
- Decision-making patterns
- Budget considerations

#### Order History (`order_history`)

- Past order details
- Delivery satisfaction
- Product performance over time
- Purchase frequency patterns

### 2. Memory Storage and Retrieval

```python
# Memory is stored in both MongoDB and Qdrant
await hybrid_memory_service.store_memory(
    user_id="user_123",
    memory_content="User prefers organic supplements and has diabetes",
    memory_type="user_preference",
    confidence=0.9,
    importance_score=0.8,
    additional_metadata={
        "health_condition": "diabetes",
        "preference_type": "organic"
    }
)
```

### 3. Personalization in Conversations

The system personalizes conversations through several mechanisms:

#### A. Enhanced User Profile Extraction

The `OptimizedUserProfileExtractionAgent` extracts and updates user profiles with:

- Basic information (name, age, location)
- Health conditions and dietary restrictions
- Activity preferences and fitness goals
- Product preferences and budget ranges
- Communication style and decision factors

#### B. Semantic Context Integration

The system maintains semantic context including:

- Conversation themes and patterns
- Product affinities and preferences
- Communication style preferences
- Decision-making factors

#### C. Memory-Enhanced Search

When users ask questions, the system:

1. Retrieves relevant memories using semantic search
2. Incorporates past preferences and interactions
3. Provides personalized product recommendations
4. References previous conversations and orders

### 4. Memory Consolidation

The system periodically consolidates memories to:

- Identify patterns in user behavior
- Generate insights about preferences
- Update user profiles with consolidated information
- Remove redundant or outdated memories

## How to Use Fake Memories for Testing

### 1. Using the API Endpoints

#### Inject General Fake Memories

```bash
curl -X POST "http://localhost:4003/v1/fake-memories/users/demo_user_123/inject" \
  -H "Content-Type: application/json" \
  -d '{
    "num_memories": 20,
    "memory_types": ["user_preference", "product_interaction", "conversation_theme", "order_history"]
  }'
```

#### Inject Fake Order Memories

```bash
curl -X POST "http://localhost:4003/v1/fake-memories/users/demo_user_123/inject-orders" \
  -H "Content-Type: application/json" \
  -d '{"num_orders": 5}'
```

#### Inject Fake Review Memories

```bash
curl -X POST "http://localhost:4003/v1/fake-memories/users/demo_user_123/inject-reviews" \
  -H "Content-Type: application/json" \
  -d '{"num_reviews": 5}'
```

### 2. Using the Python Script

```bash
cd backend
python scripts/inject_fake_memories.py
```

This will create test users with realistic fake memories.

### 3. Example Fake Memories Created

#### User Preference Memory

```json
{
	"content": "User prefers vegetarian supplements and is interested in diabetes management. Enjoys hiking and needs products that support this lifestyle.",
	"memory_type": "user_preference",
	"metadata": {
		"health_condition": "diabetes",
		"dietary_restriction": "vegetarian",
		"activity": "hiking"
	}
}
```

#### Product Interaction Memory

```json
{
	"content": "User purchased Vitamin D3 5000 IU and was satisfied with the results",
	"memory_type": "product_interaction",
	"metadata": {
		"product_name": "Vitamin D3 5000 IU",
		"interaction_type": "purchase",
		"satisfaction": "positive"
	}
}
```

#### Order History Memory

```json
{
	"content": "User placed an order on 2024-01-15 containing: Vitamin D3 5000 IU, Omega-3 Fish Oil, Multivitamin. Order was delivered successfully and user was satisfied.",
	"memory_type": "order_history",
	"metadata": {
		"order_date": "2024-01-15",
		"products": ["Vitamin D3 5000 IU", "Omega-3 Fish Oil", "Multivitamin"],
		"order_status": "delivered",
		"satisfaction": "satisfied"
	}
}
```

## How Personalization Appears in Conversations

### 1. Profile-Aware Responses

When a user asks about supplements, the system considers:

- Their health conditions (e.g., "Since you have diabetes, I recommend...")
- Their dietary restrictions (e.g., "Here are some vegan options...")
- Their activity level (e.g., "For your hiking routine, consider...")

### 2. Memory-Enhanced Recommendations

The system references past interactions:

- "Based on your previous order of Vitamin D3, you might also like..."
- "You mentioned before that you prefer organic products, so here are some options..."
- "Since you had a positive experience with Omega-3, here are similar products..."

### 3. Contextual Understanding

The system maintains conversation context:

- Remembers previous questions and answers
- Builds on past conversations
- Provides consistent recommendations
- Avoids repeating the same questions

## Memory API Endpoints

### Debug Memory Store

```bash
curl "http://localhost:4003/v1/memory/debug/store/demo_user_123"
```

### Get Memory Insights

```bash
curl "http://localhost:4003/v1/memory/users/demo_user_123/insights"
```

### Retrieve Relevant Memories

```bash
curl "http://localhost:4003/v1/memory/users/demo_user_123/memories?query=vitamin%20supplements&limit=5"
```

### Consolidate Memories

```bash
curl -X POST "http://localhost:4003/v1/memory/users/demo_user_123/consolidate"
```

## Best Practices for Testing

### 1. Create Realistic User Personas

- Create different user types (health-focused, budget-conscious, premium buyers)
- Vary the number and types of memories
- Include both positive and negative experiences

### 2. Test Memory Retrieval

- Ask questions that should trigger specific memories
- Verify that past interactions influence recommendations
- Check that user preferences are respected

### 3. Monitor Memory Consolidation

- Watch how memories are consolidated over time
- Verify that patterns are correctly identified
- Ensure redundant memories are handled properly

## Troubleshooting

### Common Issues

1. **Memories not being retrieved**: Check if the user has memories stored and if the query is semantically similar
2. **Personalization not working**: Verify that the enhanced workflow is being used and memory components are initialized
3. **Memory consolidation failing**: Check if there are enough memories (minimum 10) for consolidation

### Debug Steps

1. Check memory store contents:

   ```bash
   curl "http://localhost:4003/v1/memory/debug/store/{user_id}"
   ```

2. Verify memory injection:

   ```bash
   curl "http://localhost:4003/v1/memory/users/{user_id}/insights"
   ```

3. Test memory retrieval:
   ```bash
   curl "http://localhost:4003/v1/memory/users/{user_id}/memories?query=your_test_query"
   ```

## Conclusion

The memory system provides comprehensive personalization by:

- Storing user preferences and interactions
- Retrieving relevant context for conversations
- Consolidating insights over time
- Maintaining conversation continuity

This creates a more engaging and personalized shopping experience that learns from each interaction.
