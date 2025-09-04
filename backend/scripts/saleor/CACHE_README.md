# Saleor Product Loading Cache System

This document describes the caching system implemented for the Saleor product loading script to reduce API calls and improve performance.

## Overview

The caching system stores API responses in JSON files to avoid redundant API calls for the same data. This is particularly useful when loading multiple products that share common categories, collections, product types, and attributes.

## Cache Types

The system maintains separate caches for different types of data:

- **categories**: Category IDs mapped by slug
- **collections**: Collection IDs mapped by slug
- **product_types**: Product type IDs mapped by slug
- **attributes**: Attribute IDs mapped by slug
- **attribute_values**: Attribute values mapped by attribute ID
- **channels**: Channel data (ID and currency) mapped by slug

## Cache Location

All cache files are stored in the `cache/` directory:

```
cache/
├── categories_cache.json
├── collections_cache.json
├── product_types_cache.json
├── attributes_cache.json
├── attribute_values_cache.json
└── channels_cache.json
```

## How It Works

### Before Caching

```python
# Each call would make an API request
category_id = get_or_create_category("electronics")
category_id = get_or_create_category("electronics")  # Duplicate API call!
```

### After Caching

```python
# First call makes API request and caches result
category_id = get_or_create_category("electronics")  # API call + cache

# Subsequent calls use cached result
category_id = get_or_create_category("electronics")  # Uses cache, no API call
```

## Cache Management

### Using the Cache Utility Script

The `cache_utils.py` script provides commands to manage the cache:

```bash
# View cache statistics
python cache_utils.py stats

# Clear all caches
python cache_utils.py clear

# Clear specific cache
python cache_utils.py clear categories

# View contents of specific cache
python cache_utils.py view categories
```

### Programmatic Cache Management

You can also manage caches programmatically:

```python
from load_products_to_saleor import clear_cache, print_cache_stats

# Clear all caches
clear_cache()

# Clear specific cache
clear_cache("categories")

# Print cache statistics
print_cache_stats()
```

## Benefits

1. **Reduced API Calls**: Eliminates duplicate requests for the same data
2. **Improved Performance**: Faster execution when processing multiple products
3. **Reduced Load**: Less strain on the Saleor API server
4. **Cost Savings**: Fewer API calls mean lower costs if using paid API services
5. **Fault Tolerance**: Cached data persists between script runs

## Cache Invalidation

The cache is automatically updated when:

- New entities are created (they're immediately cached)
- Existing entities are found (they're cached for future use)

To manually invalidate cache:

- Use `clear_cache()` function
- Delete cache files manually
- Use the cache utility script

## Example Performance Improvement

**Before caching:**

- Loading 100 products with 10 unique categories
- API calls: 100 category lookups (10 unique + 90 duplicates)
- Total: 100 API calls

**After caching:**

- Loading 100 products with 10 unique categories
- API calls: 10 category lookups (only unique ones)
- Total: 10 API calls
- **90% reduction in API calls!**

## Cache File Format

Each cache file contains a JSON object mapping keys to values:

```json
{
	"electronics": "Q2F0ZWdvcnk6MQ==",
	"clothing": "Q2F0ZWdvcnk6Mg==",
	"books": "Q2F0ZWdvcnk6Mw=="
}
```

## Best Practices

1. **Run with cache first**: Always run the script once to populate the cache
2. **Monitor cache stats**: Use `print_cache_stats()` to see cache effectiveness
3. **Clear cache when needed**: Clear cache if you suspect stale data
4. **Backup cache files**: Cache files can be backed up and restored
5. **Version control**: Consider adding cache files to `.gitignore` if they contain sensitive data

## Troubleshooting

### Cache Not Working

- Check if `cache/` directory exists
- Verify file permissions
- Check for JSON syntax errors in cache files

### Stale Data

- Clear cache: `python cache_utils.py clear`
- Re-run the script to rebuild cache

### Cache File Corruption

- Delete corrupted cache file
- Re-run script to recreate cache

## Migration from Non-Cached Version

The caching system is backward compatible. Simply run the updated script and it will:

1. Create cache directory if it doesn't exist
2. Start caching results from the first run
3. Use cached data in subsequent runs

No changes to your existing workflow are required!
