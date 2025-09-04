#!/usr/bin/env python3
"""
Test script to verify that the search functionality is working with case-insensitive category matching
"""

import asyncio
import logging
from backend.infrastructure.connections import Neo4jConfig, Neo4jConnection
from backend.infrastructure.repositories import Neo4jProductRepository
from backend.settings import Neo4jSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search_fix():
    """Test that the search functionality is working with case-insensitive category matching."""
    
    settings = Neo4jSettings()
    config = Neo4jConfig(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE
    )
    
    connection = Neo4jConnection(config)
    repository = Neo4jProductRepository(connection)
    
    # Test search with category filtering
    print('Testing search for hiking footwear...')
    products = await repository.get_products_by_query('hiking boots', num_results=3, categories=['hiking footwear'])
    print(f'Found {len(products)} products')
    for product in products:
        print(f'- {product.name}: ${product.price} ({product.category})')
    
    print('\nTesting search for hiking clothing...')
    products = await repository.get_products_by_query('hiking clothing', num_results=3, categories=['hiking clothing'])
    print(f'Found {len(products)} products')
    for product in products:
        print(f'- {product.name}: ${product.price} ({product.category})')
    
    print('\nTesting search for camp kitchen...')
    products = await repository.get_products_by_query('camp kitchen', num_results=3, categories=['camp kitchen'])
    print(f'Found {len(products)} products')
    for product in products:
        print(f'- {product.name}: ${product.price} ({product.category})')

if __name__ == "__main__":
    asyncio.run(test_search_fix())
