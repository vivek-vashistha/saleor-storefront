# Corrected Langmem Integration Example

This document shows how to use the corrected Langmem integration based on the [official documentation](https://langchain-ai.github.io/langmem/guides/extract_semantic_memories/).

## Key Changes Made

### 1. Correct API Usage

- **Before**: Used `MemoryManager`, `UserState`, `SemanticMemory` (incorrect)
- **After**: Uses `create_memory_manager`, `create_memory_store_manager`, and `InMemoryStore` (correct)

### 2. Proper Memory Schemas

The integration now uses structured schemas for semantic memory extraction:

```python
class UserPreference(BaseModel):
    """Schema for user preferences and interests."""
    subject: str = Field(description="The user or entity")
    preference: str = Field(description="The preference or interest")
    context: str = Field(description="Context for the preference")
    confidence: float = Field(default=1.0, description="Confidence in this preference")

class ProductInteraction(BaseModel):
    """Schema for product interactions and feedback."""
    user: str = Field(description="The user")
    product: str = Field(description="The product or product category")
    interaction_type: str = Field(description="Type of interaction (viewed, liked, purchased, etc.)")
    feedback: str = Field(description="User feedback or sentiment")
    context: str = Field(description="Context of the interaction")

class ConversationTheme(BaseModel):
    """Schema for conversation themes and topics."""
    theme: str = Field(description="The main theme or topic")
    sentiment: str = Field(description="Overall sentiment (positive, negative, neutral)")
    importance: str = Field(description="Importance level (high, medium, low)")
    context: str = Field(description="Context and details")
```

### 3. Memory Store with Namespaces

Memories are stored with user-specific namespaces:

```python
# Store memories
self.store.put(
    key=memory.id,
    value=memory.content.model_dump(),
    namespace=("conversations", user_id, "memories")
)

# Search memories
memories = self.store.search(
    namespace=("conversations", user_id, "memories"),
    query=query,
    limit=limit
)
```

## Usage Example

### 1. Initialize Memory Service

```python
from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
from backend.settings import AISettings

# Get AI settings from environment
ai_settings = AISettings()
config = SemanticMemoryConfig.from_ai_settings(ai_settings)

# Create semantic memory service
semantic_service = SemanticMemoryService(config)
```

### 2. Record Conversation

```python
# Record a conversation
await semantic_service.record_conversation(
    user_id="user123",
    messages=[
        {"role": "user", "content": "I love hiking and need a good backpack for weekend trips"},
        {"role": "assistant", "content": "I'd recommend the Osprey Atmos 65L for weekend hiking trips"}
    ],
    context={"products": [{"name": "Osprey Atmos 65L", "category": "backpacks"}]}
)
```

### 3. Retrieve Relevant Memories

```python
# Get memories relevant to a query
memories = await semantic_service.retrieve_relevant_memories(
    user_id="user123",
    query="hiking preferences",
    limit=5
)

# Returns structured memories like:
# [
#   {
#     "id": "mem_123",
#     "content": {
#       "subject": "user123",
#       "preference": "hiking",
#       "context": "weekend trips",
#       "confidence": 1.0
#     },
#     "created_at": "2024-01-15T10:30:00Z",
#     "score": 0.95
#   }
# ]
```

### 4. Consolidate Memories

```python
# Consolidate user memories
consolidation_result = await semantic_service.consolidate_memories("user123")

# Returns insights like:
# {
#   "status": "success",
#   "consolidated_patterns": {
#     "themes": ["hiking", "outdoor gear", "weekend trips"],
#     "preferences": ["Osprey brand", "65L capacity", "hiking backpacks"],
#     "communication_style": "direct and specific"
#   }
# }
```

## API Endpoints

The corrected integration provides these API endpoints:

- `GET /v1/memory/users/{user_id}/insights` - Get memory insights
- `POST /v1/memory/users/{user_id}/consolidate` - Consolidate user memories
- `POST /v1/memory/users/{user_id}/initialize` - Initialize user memory
- `GET /v1/memory/users/{user_id}/memories?query=hiking&limit=5` - Retrieve relevant memories
- `PUT /v1/memory/users/{user_id}/profile` - Update profile with memory insights
- `POST /v1/memory/users/{user_id}/consolidation/schedule` - Schedule memory consolidation

## Benefits of Corrected Implementation

### 1. **Structured Memory Extraction**

- Uses proper Pydantic schemas for consistent memory structure
- Extracts specific types of information (preferences, interactions, themes)
- Provides context and confidence scores

### 2. **Efficient Storage and Retrieval**

- Uses LangGraph's InMemoryStore with proper namespacing
- Enables semantic search across user memories
- Supports memory updates and deletions

### 3. **Background Processing**

- Automatic memory consolidation
- Scheduled cleanup of old memories
- Non-blocking memory operations

### 4. **Integration with Existing System**

- Works with your existing environment configuration
- Integrates with current chat workflow
- Maintains backward compatibility

## Testing the Integration

### 1. Start the Services

```bash
# Start Redis and Celery
docker-compose up redis celery-worker celery-beat

# Start the main application
docker-compose up backend
```

### 2. Test Memory Operations

```bash
# Initialize memory for a user
curl -X POST "http://localhost:8000/v1/memory/users/user123/initialize"

# Record a conversation (this happens automatically in chat)
# Send a message through the chat API

# Get memory insights
curl "http://localhost:8000/v1/memory/users/user123/insights"

# Search for specific memories
curl "http://localhost:8000/v1/memory/users/user123/memories?query=hiking&limit=5"
```

The corrected implementation now properly follows the [official Langmem documentation](https://langchain-ai.github.io/langmem/guides/extract_semantic_memories/) and provides robust semantic memory capabilities for your conversational commerce system.
