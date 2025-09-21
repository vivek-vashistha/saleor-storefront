# Langmem Integration for Long-Term Memory

This document describes the integration of Langmem for long-term memory capabilities in the conversational commerce system.

## Overview

Langmem has been integrated to provide sophisticated long-term memory capabilities that enhance the conversational commerce system with:

- **User State Memory**: Structured profiles that learn and evolve over time
- **Semantic Memory**: Unstructured memory that captures conversation context and patterns
- **Background Processing**: Automatic memory consolidation and cleanup
- **Memory Retrieval**: Context-aware memory recall for better recommendations

## Architecture

### Core Components

1. **Enhanced Chat State** (`EnhancedChatState`)

   - Extends the original `ChatState` with Langmem components
   - Includes `MemoryManager`, `UserState`, and `SemanticMemory`
   - Provides methods for memory recording and retrieval

2. **Semantic Memory Service** (`SemanticMemoryService`)

   - Manages semantic memory operations
   - Extracts conversation themes, patterns, and affinities
   - Handles memory consolidation and cleanup

3. **Background Memory Manager** (`BackgroundMemoryManager`)

   - Manages background memory processing
   - Schedules memory consolidation tasks
   - Handles memory cleanup and maintenance

4. **Enhanced Agents**

   - `EnhancedUserProfileExtractionAgent`: Extracts both structured and semantic profile information
   - All agents can now access and utilize memory context

5. **Enhanced Workflow** (`EnhancedSearchQueryWorkflow`)
   - Integrates memory components into the conversation flow
   - Provides memory context to all agents
   - Schedules background memory processing

## Features

### 1. User State Memory (Structured)

- **Enhanced User Profile**: Extends the original profile with semantic fields
- **Conversation Themes**: Tracks recurring topics and interests
- **Interaction Patterns**: Learns user communication and decision patterns
- **Product Affinities**: Identifies preferred categories and brands
- **Communication Style**: Adapts to user's preferred communication approach
- **Decision Factors**: Learns what influences user's purchasing decisions

### 2. Semantic Memory (Unstructured)

- **Conversation Context**: Captures important conversation context
- **Product Interactions**: Records user interactions with products
- **Behavioral Patterns**: Identifies patterns in user behavior
- **Memory Search**: Enables semantic search across all memories
- **Memory Consolidation**: Automatically consolidates related memories

### 3. Background Processing

- **Memory Consolidation**: Automatically consolidates memories across sessions
- **Memory Cleanup**: Removes old memories based on retention policy
- **Background Tasks**: Celery-based background processing
- **Scheduled Tasks**: Periodic memory maintenance

### 4. Memory Retrieval

- **Context-Aware Search**: Retrieves relevant memories for current context
- **Memory Insights**: Provides insights into user's memory patterns
- **Relevant Memories**: Returns memories relevant to current query

## API Endpoints

### Memory Management

- `GET /memory/users/{user_id}/insights` - Get memory insights
- `POST /memory/users/{user_id}/consolidate` - Consolidate user memories
- `POST /memory/users/{user_id}/initialize` - Initialize user memory
- `GET /memory/users/{user_id}/memories` - Retrieve relevant memories
- `PUT /memory/users/{user_id}/profile` - Update profile with memory insights
- `POST /memory/users/{user_id}/consolidation/schedule` - Schedule memory consolidation

## Configuration

### Environment Variables

The Langmem integration uses the existing environment configuration. Make sure you have the following environment variables set:

```env
# OpenAI API Key (already configured in your system)
OPENAI_API_KEY=your-openai-api-key

# Redis Configuration for Celery (new)
REDIS_URL=redis://localhost:6379/0

# Memory Configuration (optional, with defaults)
MEMORY_RETENTION_DAYS=90
MAX_MEMORIES_PER_USER=1000
MEMORY_CONSOLIDATION_THRESHOLD=10
```

**Note**: The system automatically reads the `OPENAI_API_KEY` from your existing environment configuration, so no additional setup is required for the API key.

### Docker Services

The integration includes additional Docker services:

- **Redis**: For Celery message broker and result backend
- **Celery Worker**: For background memory processing
- **Celery Beat**: For scheduled memory tasks

## Usage Examples

### 1. Initialize User Memory

```python
# Initialize memory components for a new user
memory_components = await semantic_memory_service.initialize_user_memory(user_id)
```

### 2. Record Conversation

```python
# Record conversation in semantic memory
await state.record_conversation_memory()
```

### 3. Retrieve Relevant Memories

```python
# Get memories relevant to current context
memories = await state.retrieve_relevant_memories("user preferences")
```

### 4. Schedule Memory Consolidation

```python
# Schedule background memory consolidation
await background_memory_manager.schedule_memory_consolidation(
    user_id=user_id,
    session_id=session_id,
    priority=1
)
```

## Benefits

### 1. Enhanced Personalization

- **Learning User Preferences**: System learns from user interactions over time
- **Adaptive Recommendations**: Recommendations improve based on learned preferences
- **Context Awareness**: Better understanding of user context across sessions

### 2. Improved User Experience

- **Conversation Continuity**: Maintains context across multiple sessions
- **Personalized Responses**: Responses adapt to user's communication style
- **Better Recommendations**: Product recommendations improve over time

### 3. Business Value

- **Increased Engagement**: Users get more personalized experiences
- **Higher Conversion**: Better recommendations lead to higher conversion rates
- **Customer Retention**: Personalized experiences improve customer retention

## Migration Guide

### From Original System

1. **Update Dependencies**: Install new dependencies (langmem, celery, redis)
2. **Update Docker Compose**: Add Redis and Celery services
3. **Update Environment**: Add new environment variables
4. **Gradual Migration**: Start with enhanced workflow alongside original
5. **A/B Testing**: Compare performance with and without Langmem

### Backward Compatibility

- Original `ChatState` and workflow remain functional
- Enhanced components are additive, not replacing
- Gradual migration path available

## Monitoring and Maintenance

### 1. Memory Health

- Monitor memory usage and growth
- Track consolidation success rates
- Monitor background task performance

### 2. Performance Metrics

- Memory retrieval response times
- Background task completion rates
- User engagement improvements

### 3. Maintenance Tasks

- Regular memory cleanup
- Consolidation task monitoring
- Performance optimization

## Troubleshooting

### Common Issues

1. **Memory Initialization Failures**

   - Check OpenAI API key configuration
   - Verify Redis connection
   - Check user session existence

2. **Background Task Failures**

   - Check Celery worker status
   - Verify Redis connectivity
   - Monitor task logs

3. **Memory Retrieval Issues**
   - Check semantic memory initialization
   - Verify user session state
   - Monitor memory service logs

### Debugging

- Enable debug logging for memory operations
- Monitor Celery task execution
- Check Redis queue status
- Verify memory component initialization

## Future Enhancements

### Planned Features

1. **Advanced Memory Analytics**

   - Memory usage patterns
   - User engagement metrics
   - Memory effectiveness analysis

2. **Memory Optimization**

   - Automatic memory pruning
   - Smart consolidation algorithms
   - Memory compression techniques

3. **Enhanced Retrieval**
   - Multi-modal memory search
   - Temporal memory queries
   - Cross-user memory insights

## Conclusion

The Langmem integration provides a robust foundation for long-term memory in the conversational commerce system. It enables sophisticated personalization, improved user experiences, and better business outcomes through enhanced memory capabilities.

The system is designed to be scalable, maintainable, and extensible, providing a solid foundation for future enhancements and optimizations.
