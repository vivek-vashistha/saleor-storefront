# Backend Scripts

This directory contains utility scripts for managing and testing the conversational commerce backend.

## Available Scripts

### Configuration Testing

- **`test_config.py`**

  Tests that Neo4j configuration is properly reading from environment variables.

  ```bash
  python scripts/test_config.py
  ```

### Product Repository Testing

- **`test_neo4j_repository.py`**

  Tests the Neo4jProductRepository implementation with sample data.

  ```bash
  python scripts/test_neo4j_repository.py
  ```

### Data Loading Scripts

- **`load_products_to_qdrant.py`**

  Loads products from CSV into Qdrant vector database.

  ```bash
  python scripts/load_products_to_qdrant.py
  ```

- **`load_products_to_neo4j.py`**

  Loads products from CSV into Neo4j knowledge graph with enhanced graph relationships.

- **Data Mapping Structure:**

  ```bash
     # Product node (from CSV columns only)
     Product.productId     → saleor_product_id
     Product.name          → name
     Product.brand         → brand
     Product.canonicalUrl  → url
     Product.slug          → slug
     Product.image         → image_url

     # Variant node (from CSV columns only)
     Variant.variantId     → saleor_variant_id

     # Category hierarchy (exactly 3 levels from your CSV)
     MainCategory.code     → main_category_slug
     MainCategory.name     → main_category

     SubCategory.code      → sub_category_slug
     SubCategory.name      → sub_category

     Category.code         → category_slug
     Category.name         → category_name

     # Attribute keys/values (attach to Variant; all come from CSV)
     AttrValue(key="best_for").value_str            ← best_for
     AttrValue(key="review_score").value_num        ← review_score
     AttrValue(key="review_count").value_num        ← review_count
     AttrValue(key="product_type_name").value_str   ← product_type_name
     AttrValue(key="product_type_slug").value_str   ← product_type_slug
     AttrValue(key="tax_class").value_str           ← tax_class
     AttrValue(key="collections").value_str         ← collections
     AttrValue(key="breadcrumbs").value_str         ← breadcrumbs
     AttrValue(key="short_description").value_str   ← short_description
     AttrValue(key="description_text").value_str    ← description_text

     # Core relationships (only using data present in CSV)
     (Product)-[:HAS_VARIANT]->(Variant)                          # link by saleor_product_id ↔ saleor_variant_id
     (Product)-[:IN_CATEGORY]->(Category)                         # leaf category from category_*
     (Category)-[:CHILD_OF]->(SubCategory)
     (SubCategory)-[:CHILD_OF]->(MainCategory)
     (Variant)-[:HAS_ATTR]->(AttrValue)
     (AttrValue)-[:OF]->(Attribute {key:<same as above>})         # one Attribute node per distinct key
  ```

- #### Usage:

  ```bash
     cd backend
     uv run python -m scripts.load_products_to_neo4j
  ```

- `load_products_comparison.py`

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

Load products into the Neo4j knowledge graph with enhanced graph relationships:

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

- `data/iherb_data_for_neo4j/iherb_product_data - for_Neo4j_push_v3_with_saleor_ID.csv` - iHerb product data with Saleor IDs in CSV format

### Database Services

Make sure the following services are running:

- **Neo4j**: For knowledge graph storage
- **Qdrant**: For vector storage (optional, for comparison)

## Script Features

### Neo4j Scripts

- **Hybrid Search**: Combines vector similarity and fulltext search
- **Enhanced Graph Structure**: Stores products as nodes with comprehensive relationships
- **3-Level Category Hierarchy**: MainCategory → SubCategory → Category relationships
- **Product-Variant Relationships**: Links products to their variants
- **Attribute Management**: Stores product attributes as separate nodes
- **Similarity Relationships**: SIMILAR_TO relationships based on embeddings
- **Cross-Category Recommendations**: RECOMMENDED_WITH relationships
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
   - Check file encoding (should be utf-8)
   - Ensure all required columns are present (saleor_product_id, saleor_variant_id, etc.)

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
