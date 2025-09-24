# Hybrid Memory Implementation

This document describes the implementation of persistent semantic memory using a hybrid storage approach with MongoDB and Qdrant.

## Overview

The semantic memory system has been upgraded from using `InMemoryStore` (temporary RAM storage) to a persistent hybrid storage solution that combines:

- **MongoDB**: For structured data, metadata, and relationships
- **Qdrant**: For vector embeddings and semantic search
- **Hybrid Service**: Orchestrates both stores for comprehensive memory management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Semantic Memory Service                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │  Hybrid Memory  │    │     Memory Extraction          │  │
│  │     Service     │◄───┤   (User Preferences,          │  │
│  │                 │    │    Interactions, Themes)      │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
│           │                                                │
│           ▼                                                │
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │    MongoDB      │    │           Qdrant                │  │
│  │  (Structured)   │    │        (Vectors)               │  │
│  │                 │    │                                │  │
│  │ • User Profiles │    │ • Memory Embeddings            │  │
│  │ • Metadata      │    │ • Conversation Embeddings      │  │
│  │ • Insights      │    │ • Semantic Search              │  │
│  │ • Relationships │    │ • Similarity Matching          │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Storage Strategy

### MongoDB Collections

#### 1. `user_profiles`

```json
{
	"_id": "user_123",
	"user_id": "user_123",
	"basic_info": {
		"name": "John Doe",
		"email": "john@example.com",
		"location": "Seattle, WA"
	},
	"preferences": {
		"activity_preferences": ["hiking", "camping"],
		"product_preferences": ["Osprey", "Patagonia"],
		"budget_range": "$200-500"
	},
	"semantic_context": {
		"conversation_themes": ["weekend trips", "gear recommendations"],
		"interaction_patterns": { "communication_style": "direct" },
		"decision_factors": ["price", "quality", "brand"]
	},
	"memory_stats": {
		"total_memories": 45,
		"last_consolidation": "2024-01-15T10:30:00Z",
		"memory_health_score": 0.85
	},
	"last_updated": "2024-01-15T10:30:00Z"
}
```

#### 2. `memory_metadata`

```json
{
	"_id": "mem_123",
	"user_id": "user_123",
	"session_id": "session_456",
	"memory_type": "user_preference",
	"content": {
		"content": "User prefers hiking backpacks for weekend trips",
		"confidence": 0.9,
		"extracted_at": "2024-01-15T10:30:00Z"
	},
	"qdrant_vector_id": "vec_789",
	"created_at": "2024-01-15T10:30:00Z",
	"last_accessed": "2024-01-20T14:22:00Z",
	"access_count": 5,
	"importance_score": 0.8,
	"confidence": 0.9
}
```

#### 3. `consolidated_insights`

```json
{
	"_id": "insights_user_123",
	"user_id": "user_123",
	"consolidated_patterns": {
		"themes": ["hiking", "outdoor gear", "weekend trips"],
		"preferences": ["Osprey brand", "65L capacity"],
		"interaction_patterns": { "communication_style": "direct and specific" },
		"decision_factors": ["price", "quality", "brand"]
	},
	"memory_summary": "User prefers hiking gear for weekend trips, values quality over price",
	"last_updated": "2024-01-15T10:30:00Z",
	"confidence_score": 0.85
}
```

### Qdrant Collections

#### 1. `user_memories`

- **Purpose**: Vector embeddings of memory content
- **Metadata**: user_id, memory_type, confidence, timestamps
- **Payload**: Full memory content for retrieval

#### 2. `conversation_embeddings`

- **Purpose**: Vector embeddings of conversation chunks
- **Metadata**: user_id, session_id, message_type
- **Payload**: Conversation context for semantic search

## Implementation Components

### 1. MongoDB Memory Repository

**File**: `backend/infrastructure/repositories/memory_repository/mongodb_memory_repository.py`

**Responsibilities**:

- Store structured memory metadata
- Manage user profiles
- Handle consolidated insights
- Track memory statistics
- Clean up old memories

**Key Methods**:

- `store_memory_metadata()`: Store memory metadata with Qdrant vector ID reference
- `get_user_profile()`: Retrieve user profile data
- `store_consolidated_insights()`: Store consolidated memory insights
- `get_memory_stats()`: Get memory statistics for a user

### 2. Qdrant Memory Repository

**File**: `backend/infrastructure/repositories/memory_repository/qdrant_memory_repository.py`

**Responsibilities**:

- Store vector embeddings of memories
- Perform semantic search
- Store conversation embeddings
- Handle vector operations

**Key Methods**:

- `store_memory_embedding()`: Store memory as vector embedding
- `search_similar_memories()`: Semantic search for similar memories
- `store_conversation_embedding()`: Store conversation chunks as vectors
- `search_conversation_context()`: Find relevant conversation context

### 3. Hybrid Memory Service

**File**: `backend/application/services/hybrid_memory_service.py`

**Responsibilities**:

- Orchestrate both MongoDB and Qdrant operations
- Provide unified interface for memory operations
- Handle data synchronization between stores
- Manage memory consolidation

**Key Methods**:

- `store_memory()`: Store memory in both stores
- `search_memories()`: Semantic search with metadata enhancement
- `get_user_profile_with_memories()`: Comprehensive user profile
- `consolidate_user_memories()`: Memory consolidation and insights

### 4. Updated Semantic Memory Service

**File**: `backend/application/services/semantic_memory_service.py`

**Changes**:

- Now uses `HybridMemoryService` instead of `InMemoryStore`
- Persistent storage for all memory operations
- Enhanced memory extraction and storage
- Better error handling and logging

## Usage Examples

### 1. Store Memory

```python
# Store a user preference
memory_result = await hybrid_memory.store_memory(
    user_id="user_123",
    memory_content="User prefers hiking backpacks for weekend trips",
    memory_type="user_preference",
    session_id="session_456",
    confidence=0.9,
    importance_score=0.8
)

# Returns: {"mongodb_id": "mem_123", "qdrant_id": "vec_789", "memory_type": "user_preference"}
```

### 2. Search Memories

```python
# Semantic search for relevant memories
memories = await hybrid_memory.search_memories(
    user_id="user_123",
    query="hiking preferences",
    memory_type="user_preference",
    limit=5,
    include_metadata=True
)

# Returns list of memories with scores and metadata
```

### 3. Get User Profile

```python
# Get comprehensive user profile
profile = await hybrid_memory.get_user_profile_with_memories(
    user_id="user_123",
    include_semantic_context=True
)

# Returns structured profile with memory insights
```

### 4. Consolidate Memories

```python
# Consolidate user memories
consolidation = await hybrid_memory.consolidate_user_memories(
    user_id="user_123",
    force_consolidation=False
)

# Returns consolidation results and insights
```

## Decision Matrix

| Operation             | Use MongoDB | Use Qdrant | Use Both |
| --------------------- | ----------- | ---------- | -------- |
| Get user profile      | ✅          | ❌         | ❌       |
| Find similar memories | ❌          | ✅         | ❌       |
| Memory consolidation  | ✅          | ✅         | ✅       |
| Search by metadata    | ✅          | ❌         | ❌       |
| Semantic search       | ❌          | ✅         | ❌       |
| Get memory insights   | ✅          | ✅         | ✅       |
| Store conversation    | ❌          | ✅         | ❌       |
| Store memory metadata | ✅          | ❌         | ❌       |

## Benefits

### 1. **Persistent Storage**

- No data loss on application restart
- Long-term memory retention
- Reliable user profile persistence

### 2. **Optimal Performance**

- MongoDB: Fast structured queries with indexes
- Qdrant: Efficient vector similarity search
- Hybrid: Best of both worlds

### 3. **Scalability**

- MongoDB: Horizontal scaling, sharding by user_id
- Qdrant: Vector clustering, distributed search
- Independent scaling of each store

### 4. **Flexibility**

- Easy to add new memory types
- Configurable retention policies
- Support for different query patterns

## Migration from InMemoryStore

The system maintains backward compatibility while providing persistent storage:

1. **Gradual Migration**: Existing code continues to work
2. **Data Persistence**: New memories are stored persistently
3. **Enhanced Features**: Access to advanced memory operations
4. **Performance**: Better query performance with proper indexing

## Configuration

### Environment Variables

```bash
# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PASS=password
MONGODB_NAME=conversational_commerce

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your_api_key
QDRANT_PREFER_GRPC=true
QDRANT_TIMEOUT=10
```

### Docker Compose

The system uses the existing MongoDB and Qdrant services defined in `docker-compose.yml`:

```yaml
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
```

## Monitoring and Maintenance

### 1. **Memory Statistics**

- Track memory counts by type
- Monitor user engagement
- Identify consolidation opportunities

### 2. **Cleanup Operations**

- Automatic cleanup of old memories
- Configurable retention policies
- Memory health monitoring

### 3. **Performance Monitoring**

- Query performance metrics
- Storage utilization
- Search accuracy tracking

## Testing

Run the test script to verify the implementation:

```bash
cd backend
python test_hybrid_memory.py
```

## Future Enhancements

1. **Advanced Analytics**: Memory pattern analysis
2. **Personalization**: Dynamic memory weighting
3. **Integration**: Connect with recommendation systems
4. **Privacy**: User data anonymization options
5. **Performance**: Caching and optimization

## Conclusion

The hybrid memory implementation provides a robust, scalable, and persistent solution for semantic memory management. By combining MongoDB's structured data capabilities with Qdrant's vector search power, the system delivers comprehensive memory management while maintaining excellent performance and scalability.
