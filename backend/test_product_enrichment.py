#!/usr/bin/env python3
"""
Test script for Saleor product enrichment.
This script tests the product enrichment functionality without requiring MongoDB.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.infrastructure.connections.saleor.config import SaleorConfig
from backend.infrastructure.connections.saleor.connection import SaleorConnection
from backend.application.services.saleor_service import SaleorService
from backend.domain.entities import Product

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_product_enrichment():
    """Test the product enrichment functionality."""
    logger.info("🚀 Testing Saleor product enrichment...")
    
    try:
        # Create configuration and connection
        config = SaleorConfig()
        connection = SaleorConnection(config)
        
        # Create service
        service = SaleorService(connection)
        logger.info("✅ Saleor service created successfully")
        
        # Create test products (similar to what you'd get from Neo4j/Qdrant)
        test_products = [
            Product(
                product_id=338778,
                name="Apple Ginger Zest (Sugar-Free)",
                category="beverages",
                price=5.29,
                description="Refreshing apple ginger drink",
                review_score=4.5,
                best_for=["health", "energy", "digestion"],
                image_url="https://example.com/apple-ginger.jpg"
            ),
            Product(
                product_id=350895,
                name="Green Vitality Juice (Sugar-Free)",
                category="beverages",
                price=5.99,
                description="Nutrient-rich green juice",
                review_score=4.8,
                best_for=["immunity", "detox", "energy"],
                image_url="https://example.com/green-vitality.jpg"
            ),
            Product(
                product_id=320185,
                name="Citrus Glow Juice (Sugar-Free)",
                category="beverages",
                price=4.79,
                description="Bright citrus blend",
                review_score=4.3,
                best_for=["vitamin_c", "skin_health", "refreshment"],
                image_url="https://example.com/citrus-glow.jpg"
            )
        ]
        
        logger.info(f"📦 Created {len(test_products)} test products")
        
        # Test enrichment
        async with connection:
            logger.info("🔄 Starting product enrichment...")
            enriched_products = await service.enrich_products_with_saleor_data(test_products)
            
            # Check results
            enriched_count = 0
            for product in enriched_products:
                if hasattr(product, 'saleor_data') and product.saleor_data:
                    enriched_count += 1
                    logger.info(f"✅ Product '{product.name}' enriched with Saleor data")
                    logger.info(f"   - Saleor response: {product.saleor_data.get('answer', 'No answer')[:100]}...")
                    logger.info(f"   - Session ID: {product.saleor_data.get('session_id', 'N/A')}")
                    logger.info(f"   - Response time: {product.saleor_data.get('info', {}).get('response_time', 'N/A')}s")
                else:
                    logger.warning(f"⚠️ Product '{product.name}' not enriched")
            
            logger.info(f"📊 Enrichment Summary: {enriched_count}/{len(test_products)} products enriched")
            
            if enriched_count > 0:
                logger.info("🎉 Saleor product enrichment is working correctly!")
                return True
            else:
                logger.warning("⚠️ No products were enriched - check Saleor API server")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing product enrichment: {e}")
        return False


async def test_individual_product_lookup():
    """Test individual product lookup functionality."""
    logger.info("🔍 Testing individual product lookup...")
    
    try:
        # Create configuration and connection
        config = SaleorConfig()
        connection = SaleorConnection(config)
        
        # Create service
        service = SaleorService(connection)
        
        # Test product lookup by ID
        test_product_id = "338778"
        logger.info(f"🔍 Looking up product by ID: {test_product_id}")
        
        async with connection:
            saleor_data = await service.get_saleor_product_details(test_product_id)
            if saleor_data:
                logger.info(f"✅ Successfully fetched Saleor data for product ID {test_product_id}")
                logger.info(f"   Response: {saleor_data.get('answer', 'No answer')[:100]}...")
                return True
            else:
                logger.warning(f"⚠️ No Saleor data found for product ID {test_product_id}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing individual product lookup: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Saleor product enrichment tests...")
    
    # Test product enrichment
    enrichment_ok = await test_product_enrichment()
    if not enrichment_ok:
        logger.error("❌ Product enrichment test failed")
        return
    
    # Test individual product lookup
    lookup_ok = await test_individual_product_lookup()
    if not lookup_ok:
        logger.warning("⚠️ Individual product lookup test had issues")
        return
    
    logger.info("🎉 All tests passed! Saleor product enrichment is working correctly.")
    logger.info("   Your backend is ready to enrich products with Saleor data!")


if __name__ == "__main__":
    asyncio.run(main())
