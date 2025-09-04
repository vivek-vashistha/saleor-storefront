# Neo4j Product Repository Implementation

This document describes the Neo4j implementation for the product repository in the conversational commerce backend.

## Overview

The `Neo4jProductRepository` provides a graph-based approach to product storage and retrieval using Neo4j database. It implements hybrid search capabilities combining vector similarity and fulltext search using the `neo4j-graphrag` library.

## Features

- **Hybrid Search**: Combines vector similarity search with fulltext search for better product discovery
- **Graph Structure**: Stores products as nodes with properties for flexible querying
- **Vector Embeddings**: Uses OpenAI embeddings for semantic search
- **Fulltext Indexing**: Indexes product name, description, and category for text-based search
- **Category Filtering**: Supports filtering by product categories
- **CRUD Operations**: Full create, read, update, and delete operations

## Architecture

### Components

1. **Neo4jConnection**: Manages connection to Neo4j database
2. **Neo4jConfig**: Configuration settings for Neo4j connection
3. **Neo4jProductRepository**: Main repository implementation
4. **IProductRepository**: Async interface for product operations

### Database Schema

Products are stored as nodes with the following structure:

```
(Product {
  product_id: int,
  name: string,
  price: float,
  category: string,
  description: string,
  review_score: float,
  best_for: list[string],
  image_url: string,
  breadcrumbs: list[string],
  embedding: vector[1536]  // OpenAI embedding vector
})
```

### Indexes

- **Vector Index**: `productEmbedding` - for similarity search using embeddings
- **Fulltext Index**: `productFulltext` - for text-based search on name, description, category

## Configuration

### Environment Variables

The Neo4j configuration automatically reads from environment variables. Add the following to your `.env` file:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
NEO4J_VECTOR_INDEX_NAME=productEmbedding
NEO4J_FULLTEXT_INDEX_NAME=productFulltext
```

**Note**: All environment variables are optional and have sensible defaults. The configuration will:

1. First try to read from environment variables
2. Fall back to default values if environment variables are not set
3. Automatically load from `.env` file if present in the backend directory

### Dependencies

The implementation requires the following packages:

```toml
neo4j>=5.20.0
neo4j-graphrag>=0.1.0
langchain-openai>=0.3.12
```

## Usage

### Basic Usage

```python
from backend.infrastructure.connections.neo4j import Neo4jConfig, Neo4jConnection
from backend.infrastructure.repositories.product_repository import Neo4jProductRepository

# Create configuration
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password",
    database="neo4j"
)

# Create connection
connection = Neo4jConnection(config)

# Create repository
repository = Neo4jProductRepository(connection)

# Insert products
products = [product1, product2, product3]
await repository.insert_products(products)

# Search products
results = await repository.get_products_by_query("wireless headphones", num_results=10)

# Get products by IDs
products = await repository.get_products_by_ids([1, 2, 3])

# Delete all products
await repository.delete_all_products()
```

### Search Capabilities

#### Semantic Search

```python
# Find products similar to a natural language query
results = await repository.get_products_by_query("comfortable running shoes for beginners")
```

#### Category Filtering

```python
# Search within specific categories
results = await repository.get_products_by_query(
    "wireless",
    num_results=10,
    categories=["Electronics", "Audio"]
)
```

#### ID-based Retrieval

```python
# Get specific products by their IDs
products = await repository.get_products_by_ids([1, 2, 3, 4, 5])
```

## Testing

### Test Configuration

First, test that the configuration is working correctly:

```bash
cd backend
python scripts/test_config.py
```

This will verify that environment variables are being read properly.

### Test Repository

Then test the repository implementation:

```bash
cd backend
python scripts/test_neo4j_repository.py
```

### Load Products to Neo4j

Load products from CSV into Neo4j knowledge graph:

```bash
cd backend
python scripts/load_products_to_neo4j.py
```

### Compare Qdrant vs Neo4j

Load products into both databases and compare search results:

```bash
# Load products into both databases
cd backend
python scripts/load_products_comparison.py --setup both

# Run comparison tests
python scripts/load_products_comparison.py --setup both --compare

# Test specific query
python scripts/load_products_comparison.py --setup both --query "hiking boots"

# Test with category filter
python scripts/load_products_comparison.py --setup both --query "waterproof" --categories clothing
```

## Integration with Dependency Injection

The repository is integrated into the dependency injection container:

```python
# In infrastructure.py
neo4j_config = providers.Singleton(
    Neo4jConfig,
    uri=config.NEO4J_URI,
    username=config.NEO4J_USERNAME,
    password=config.NEO4J_PASSWORD,
    database=config.NEO4J_DATABASE,
    vector_index_name=config.NEO4J_VECTOR_INDEX_NAME,
    fulltext_index_name=config.NEO4J_FULLTEXT_INDEX_NAME,
)

neo4j_connection = providers.Singleton(
    Neo4jConnection,
    config=neo4j_config,
)

neo4j_product_repository = providers.Singleton(
    Neo4jProductRepository,
    connection=neo4j_connection,
)
```

## Comparison with QdrantProductRepository

| Feature          | Neo4jProductRepository        | QdrantProductRepository     |
| ---------------- | ----------------------------- | --------------------------- |
| Database Type    | Graph Database                | Vector Database             |
| Search Type      | Hybrid (Vector + Fulltext)    | Vector Similarity           |
| Query Language   | Cypher                        | Vector Operations           |
| Relationships    | Native Graph Support          | Limited                     |
| Scalability      | Good for Complex Queries      | Excellent for Vector Search |
| Use Case         | Complex Product Relationships | Pure Semantic Search        |
| Async Operations | Yes (using asyncio)           | Yes (native)                |

## Performance Considerations

1. **Vector Index**: Ensure Neo4j has sufficient memory for vector operations
2. **Fulltext Index**: Monitor index size and query performance
3. **Connection Pooling**: Neo4j driver handles connection pooling automatically
4. **Batch Operations**: For large datasets, consider batching insert operations

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify Neo4j server is running and credentials are correct
2. **Index Creation**: Ensure Neo4j version supports vector and fulltext indexes
3. **Memory Issues**: Increase Neo4j heap size for large vector operations
4. **Embedding Errors**: Verify OpenAI API key is set and accessible

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("conversational_commerce").setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Relationship Modeling**: Add product relationships (similar products, categories, etc.)
2. **User Preferences**: Store user preferences as graph relationships
3. **Recommendation Engine**: Implement graph-based recommendation algorithms
4. **Performance Optimization**: Add caching layer for frequently accessed products
