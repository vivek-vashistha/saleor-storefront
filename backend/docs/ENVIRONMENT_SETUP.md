# Environment Configuration for Hybrid Memory System

## Required Environment Variables

You need to create a `.env` file in the `backend/` directory with the following environment variables for the hybrid memory system to work properly.

## Create .env File

Create a file named `.env` in the `backend/` directory with the following content:

```bash
# =============================================================================
# HYBRID MEMORY SYSTEM ENVIRONMENT CONFIGURATION
# =============================================================================

# =============================================================================
# AI SERVICES CONFIGURATION (REQUIRED)
# =============================================================================
# OpenAI API configuration for LLM and embeddings
OPENAI_API_KEY=your_openai_api_key_here

# LLM Model configuration
MODEL_NAME=GPT4o
EMBEDDING_MODEL_NAME=OPENAI_SMALL

# =============================================================================
# MONGODB CONFIGURATION (REQUIRED)
# =============================================================================
# MongoDB connection settings for structured data storage
# These match the docker-compose.yml MongoDB service configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PASS=password
MONGODB_NAME=conversational_commerce

# =============================================================================
# QDRANT CONFIGURATION (REQUIRED)
# =============================================================================
# Qdrant vector database settings for semantic search
# These match the docker-compose.yml Qdrant service configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_PREFER_GRPC=true
QDRANT_TIMEOUT=10
QDRANT_API_KEY=

# =============================================================================
# NEO4J CONFIGURATION (Optional - for existing product graph)
# =============================================================================
# Neo4j graph database settings (if using Neo4j for product relationships)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
NEO4J_VECTOR_INDEX_NAME=productEmbedding
NEO4J_FULLTEXT_INDEX_NAME=productFulltext

# =============================================================================
# SALEOR CONFIGURATION
# =============================================================================
# Saleor e-commerce API settings
SALEOR_HOST=localhost
SALEOR_PORT=8002
SALEOR_TIMEOUT=30

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
# Redis settings for Celery background tasks and caching
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================
# Celery background task configuration for memory processing
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_TASK_TRACK_STARTED=true
CELERY_TASK_TIME_LIMIT=300
CELERY_TASK_SOFT_TIME_LIMIT=240
CELERY_WORKER_PREFETCH_MULTIPLIER=1

# =============================================================================
# WEATHER API CONFIGURATION (Optional)
# =============================================================================
# Weather API settings for location-based recommendations
WEATHER_API_KEY=your_weather_api_key_here

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================
# Application server settings
APP_HOST=0.0.0.0
APP_PORT=4003
DEBUG=false
LOG_LEVEL=INFO

# =============================================================================
# MEMORY SYSTEM CONFIGURATION
# =============================================================================
# Semantic memory system settings
MEMORY_RETENTION_DAYS=90
MAX_MEMORIES_PER_USER=1000
CONSOLIDATION_THRESHOLD=10
MEMORY_CLEANUP_INTERVAL_HOURS=24

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
# Security settings for production
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# =============================================================================
# DEVELOPMENT CONFIGURATION
# =============================================================================
# Development-specific settings
ENVIRONMENT=development
ENABLE_DEBUG_TOOLBAR=false
ENABLE_SWAGGER_UI=true
```

## Environment Variables Explanation

### Required Variables

#### 1. **AI Services (REQUIRED)**

- `OPENAI_API_KEY`: Your OpenAI API key for LLM and embeddings
- `MODEL_NAME`: LLM model to use (default: GPT4o)
- `EMBEDDING_MODEL_NAME`: Embedding model to use (default: OPENAI_SMALL)

#### 2. **MongoDB (REQUIRED)**

- `MONGODB_HOST`: MongoDB host (default: localhost)
- `MONGODB_PORT`: MongoDB port (default: 27017)
- `MONGODB_USER`: MongoDB username (default: admin)
- `MONGODB_PASS`: MongoDB password (default: password)
- `MONGODB_NAME`: Database name (default: conversational_commerce)

#### 3. **Qdrant (REQUIRED)**

- `QDRANT_HOST`: Qdrant host (default: localhost)
- `QDRANT_PORT`: Qdrant port (default: 6333)
- `QDRANT_PREFER_GRPC`: Use gRPC protocol (default: true)
- `QDRANT_TIMEOUT`: Connection timeout (default: 10)
- `QDRANT_API_KEY`: Qdrant API key (optional for local development)

### Optional Variables

#### 4. **Neo4j (Optional)**

- Only needed if you're using Neo4j for product relationships
- All variables have defaults for local development

#### 5. **Redis & Celery (Optional)**

- Only needed for background memory processing
- Defaults work with your docker-compose.yml setup

#### 6. **Application Settings (Optional)**

- Server configuration and logging settings
- Memory system configuration
- Security settings

## Quick Setup

### 1. **Minimum Required Configuration**

For the hybrid memory system to work, you only need these variables:

```bash
# Required for AI functionality
OPENAI_API_KEY=your_actual_openai_api_key

# MongoDB (matches docker-compose.yml)
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PASS=password
MONGODB_NAME=conversational_commerce

# Qdrant (matches docker-compose.yml)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_PREFER_GRPC=true
QDRANT_TIMEOUT=10
```

### 2. **Create the .env file**

```bash
cd backend
cp ENVIRONMENT_SETUP.md .env
# Then edit .env and replace the template values with your actual values
```

### 3. **Verify Configuration**

The environment variables are automatically loaded by the application. You can verify they're working by:

1. Starting the services: `docker-compose up -d`
2. Running the test: `python test_hybrid_memory.py`
3. Checking the logs for any connection errors

## Docker Compose Integration

Your existing `docker-compose.yml` already has the correct service configurations:

- **MongoDB**: Port 27017, user: admin, password: password
- **Qdrant**: Port 6333, no authentication required for local development
- **Redis**: Port 6379 for Celery background tasks

The environment variables match these service configurations, so no changes to docker-compose.yml are needed.

## Production Considerations

For production deployment:

1. **Change default passwords** in both `.env` and `docker-compose.yml`
2. **Set secure API keys** for all services
3. **Use environment-specific values** for hosts and ports
4. **Enable authentication** for Qdrant and MongoDB
5. **Set up proper secrets management**

## Troubleshooting

### Common Issues:

1. **Missing OPENAI_API_KEY**: The application will fail to start
2. **MongoDB connection failed**: Check if MongoDB service is running
3. **Qdrant connection failed**: Check if Qdrant service is running
4. **Port conflicts**: Ensure ports 27017, 6333, 6379 are available

### Verification Commands:

```bash
# Check if services are running
docker-compose ps

# Check MongoDB connection
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check Qdrant connection
curl http://localhost:6333/

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## Next Steps

1. Create the `.env` file with your actual values
2. Start the services: `docker-compose up -d`
3. Test the hybrid memory system: `python test_hybrid_memory.py`
4. Your semantic memory is now persistent! 🎉
