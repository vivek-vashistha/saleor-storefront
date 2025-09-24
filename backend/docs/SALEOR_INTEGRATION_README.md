# Saleor Integration for Conversational Commerce Backend

This document describes the integration between the Conversational Commerce Backend and the Saleor API server for enriching product data with additional information from Saleor.

## Overview

The integration automatically fetches additional product details from Saleor after products are retrieved from the main product repositories (Neo4j/Qdrant). This enrichment happens transparently and adds Saleor data to each product object.

## Architecture

### Components

1. **SaleorConnection** (`backend/infrastructure/connections/saleor/`)

   - Handles HTTP communication with the Saleor API server
   - Supports both ID-based and name-based product lookups
   - Implements async context manager for proper resource management

2. **SaleorService** (`backend/application/services/saleor_service.py`)

   - Orchestrates product enrichment with Saleor data
   - Falls back from ID lookup to name lookup if needed
   - Logs all enrichment activities for debugging

3. **ProductService Integration**
   - Automatically enriches products with Saleor data
   - Works with both individual product queries and product bundles
   - Maintains backward compatibility

### Data Flow

```
Product Query → Product Repository (Neo4j/Qdrant) → Products Retrieved → Saleor Enrichment → Enriched Products Returned
```

## Configuration

### Environment Variables

The Saleor connection can be configured using these environment variables:

```bash
# Saleor API server configuration
SALEOR_HOST=localhost          # Default: localhost
SALEOR_PORT=8002              # Default: 8002
SALEOR_TIMEOUT=30             # Default: 30 seconds
```

### Default Configuration

If no environment variables are set, the system defaults to:

- **Host**: `localhost`
- **Port**: `8002` (matches your Saleor API server)
- **Timeout**: `30 seconds`

## Usage

### Automatic Enrichment

Product enrichment happens automatically when you use the `ProductService`:

```python
# Products are automatically enriched with Saleor data
products = await product_service.get_products_for_query(search_query)
product_bundles = await product_service.get_product_bundles_for_queries(search_queries)
products_by_ids = await product_service.get_products_by_ids(product_ids)
```

### Manual Enrichment

You can also manually enrich products using the Saleor service:

```python
from backend.application.services.saleor_service import SaleorService
from backend.infrastructure.connections.saleor.connection import SaleorConnection, SaleorConfig

# Create connection and service
config = SaleorConfig()
connection = SaleorConnection(config)
service = SaleorService(connection)

# Enrich products
enriched_products = await service.enrich_products_with_saleor_data(products)
```

### Direct API Calls

For direct access to Saleor data:

```python
# Get product by ID
saleor_data = await service.get_saleor_product_details("338778")

# Get product by name
saleor_data = await service.get_saleor_product_details_by_name("Apple Ginger Zest (Sugar-Free)")
```

## Enriched Product Structure

After enrichment, each product object contains a `saleor_data` attribute:

```python
product = Product(
    product_id=338778,
    name="Apple Ginger Zest (Sugar-Free)",
    category="beverages",
    price=5.29
)

# After enrichment:
product.saleor_data = {
    "answer": "Product details from Saleor...",
    "session_id": "product_lookup",
    "info": {
        "response_time": 1.23,
        "model": "gpt-4o-mini"
    }
}
```

## Logging

The integration provides comprehensive logging:

```
INFO :: Enriching 5 products with Saleor data
INFO :: Fetching product by ID from Saleor: 338778
INFO :: Making request to Saleor API: http://localhost:8002/orders
INFO :: Successfully received response from Saleor API: orders
INFO :: Successfully enriched product: Apple Ginger Zest (Sugar-Free) (ID: 338778)
INFO :: Enriched product 'Apple Ginger Zest (Sugar-Free)' with Saleor data:
INFO ::   - Saleor response: Product details from Saleor...
INFO ::   - Session ID: product_lookup
INFO ::   - Response time: 1.23s
INFO :: Successfully enriched 5 out of 5 products
```

## Error Handling

The integration is designed to be fault-tolerant:

- **Connection failures**: Products are returned without enrichment
- **API errors**: Individual product enrichment failures are logged, others continue
- **Missing data**: Products without Saleor data are returned unchanged
- **Timeouts**: Configurable timeout prevents hanging requests

## Testing

### Prerequisites

1. Ensure the Saleor API server is running on port 8002
2. The server should have the `/health` endpoint available

### Run Tests

```bash
cd backend
python test_saleor_integration.py
```

### Expected Output

```
🚀 Starting Saleor integration tests...
Testing Saleor connection...
Saleor config: http://localhost:8002
Saleor connection created successfully
Testing health check...
✅ Health check passed - Saleor API is accessible
Testing Saleor service...
Saleor service created successfully
Testing product lookup by ID...
✅ Successfully fetched Saleor data for product ID 338778
   Response: Product details from Saleor...
Testing product lookup by name...
✅ Successfully fetched Saleor data for product name 'Apple Ginger Zest (Sugar-Free)'
   Response: Product details from Saleor...
✅ All tests passed! Saleor integration is working correctly.
```

## Troubleshooting

### Common Issues

1. **Connection Refused**

   - Ensure Saleor API server is running on port 8002
   - Check firewall settings

2. **Timeout Errors**

   - Increase `SALEOR_TIMEOUT` environment variable
   - Check network latency

3. **No Enrichment Data**
   - Verify Saleor API endpoints are working
   - Check API server logs for errors

### Debug Mode

Enable debug logging to see detailed request/response data:

```python
import logging
logging.getLogger("conversational_commerce").setLevel(logging.DEBUG)
```

## Performance Considerations

- **Async Operations**: All Saleor API calls are asynchronous
- **Connection Pooling**: HTTP sessions are reused when possible
- **Fallback Strategy**: ID lookup failure triggers name lookup
- **Batch Processing**: Multiple products are processed sequentially (can be optimized if needed)

## Future Enhancements

Potential improvements for the integration:

1. **Batch API Calls**: Send multiple product IDs in a single request
2. **Caching**: Cache Saleor responses to reduce API calls
3. **Retry Logic**: Implement exponential backoff for failed requests
4. **Metrics**: Add performance monitoring and alerting
5. **Rate Limiting**: Implement request rate limiting to respect API quotas
