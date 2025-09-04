# Backend Scripts

This directory contains utility scripts for managing and testing the conversational commerce backend.

## Available Scripts

### Configuration Testing

#### `test_config.py`

Tests that Neo4j configuration is properly reading from environment variables.

```bash
python scripts/test_config.py
```

### Product Repository Testing

#### `test_neo4j_repository.py`

Tests the Neo4jProductRepository implementation with sample data.

```bash
python scripts/test_neo4j_repository.py
```

### Data Loading Scripts

#### `load_products_to_qdrant.py`

Loads products from CSV into Qdrant vector database.

```bash
python scripts/load_products_to_qdrant.py
```

#### `load_products_to_neo4j.py`

Loads products from CSV into Neo4j knowledge graph.

```bash
python scripts/load_products_to_neo4j.py
```

#### `load_products_comparison.py`

Loads products into both Qdrant and Neo4j for comparison testing.

```bash
# Load products into both databases
python scripts/load_products_comparison.py --setup both

# Run comparison tests
python scripts/load_products_comparison.py --setup both --compare

# Test specific query
python scripts/load_products_comparison.py --setup both --query "hiking boots"

# Test with category filter
python scripts/load_products_comparison.py --setup both --query "waterproof" --categories clothing
```

## Usage Examples

### 1. Test Configuration

First, verify your configuration is working:

```bash
cd backend
python scripts/test_config.py
```

### 2. Load Products to Neo4j

Load products into the Neo4j knowledge graph:

```bash
cd backend
python scripts/load_products_to_neo4j.py
```

OR

```bash
cd backend
uv run python -m scripts.load_products_to_neo4j
```

### 3. Compare Search Results

Compare search results between Qdrant and Neo4j:

```bash
cd backend
python scripts/load_products_comparison.py --setup both --compare
```

### 4. Test Specific Queries

Test specific search queries:

```bash
# Test hiking boots search
python scripts/load_products_comparison.py --setup both --query "comfortable hiking boots"

# Test waterproof clothing
python scripts/load_products_comparison.py --setup both --query "waterproof" --categories clothing

# Test camping gear
python scripts/load_products_comparison.py --setup both --query "tents for camping"
```

## Prerequisites

### Environment Setup

Make sure you have the following environment variables set in your `.env` file:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your-api-key

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
```

### Data Files

Ensure you have the product data file:

- `data/rei_products.csv` - Product data in CSV format

### Database Services

Make sure the following services are running:

- **Neo4j**: For knowledge graph storage
- **Qdrant**: For vector storage (optional, for comparison)

## Script Features

### Neo4j Scripts

- **Hybrid Search**: Combines vector similarity and fulltext search
- **Graph Structure**: Stores products as nodes with relationships
- **Category Filtering**: Filter products by categories
- **ID-based Retrieval**: Get products by specific IDs

### Qdrant Scripts

- **Vector Search**: Pure semantic similarity search
- **Fast Retrieval**: Optimized for vector operations
- **Category Filtering**: Filter products by categories

### Comparison Scripts

- **Performance Metrics**: Compare search speed between databases
- **Result Analysis**: Compare search result quality
- **Common Products**: Identify products found by both systems
- **Timing Analysis**: Measure query execution times

## Troubleshooting

### Common Issues

1. **Configuration Errors**

   - Run `test_config.py` to verify environment variables
   - Check that `.env` file exists and has correct values

2. **Database Connection Errors**

   - Verify Neo4j server is running
   - Check connection credentials
   - Ensure database exists

3. **Data Loading Errors**

   - Verify CSV file exists and has correct format
   - Check file encoding (should be latin1)
   - Ensure all required columns are present

4. **Search Performance Issues**
   - Check that indexes are created properly
   - Verify OpenAI API key is valid
   - Monitor database resource usage

### Debug Mode

Enable debug logging by modifying the logging level in scripts:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. **Batch Operations**: Scripts handle large datasets efficiently
2. **Index Creation**: Neo4j indexes are created automatically
3. **Connection Pooling**: Database connections are managed efficiently
4. **Async Operations**: All database operations are asynchronous

## Contributing

When adding new scripts:

1. Follow the existing naming convention
2. Include proper logging
3. Add error handling
4. Document usage in this README
5. Test with sample data
