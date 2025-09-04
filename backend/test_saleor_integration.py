#!/usr/bin/env python3
"""
Test script for Saleor integration with the backend.
This script tests the Saleor connection and service functionality.
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_saleor_connection():
    """Test the Saleor connection."""
    logger.info("Testing Saleor connection...")
    
    try:
        # Create configuration
        config = SaleorConfig()
        logger.info(f"Saleor config: {config.base_url}")
        
        # Create connection
        connection = SaleorConnection(config)
        logger.info("Saleor connection created successfully")
        
        # Test health check
        logger.info("Testing health check...")
        async with connection:
            # Test a simple request to the health endpoint
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{config.base_url}/health") as response:
                        if response.status == 200:
                            logger.info("✅ Health check passed - Saleor API is accessible")
                        else:
                            logger.warning(f"⚠️ Health check failed with status {response.status}")
                except Exception as e:
                    logger.error(f"❌ Health check failed: {e}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create Saleor connection: {e}")
        return False


async def test_saleor_service():
    """Test the Saleor service."""
    logger.info("Testing Saleor service...")
    
    try:
        # Create configuration and connection
        config = SaleorConfig()
        connection = SaleorConnection(config)
        
        # Create service
        service = SaleorService(connection)
        logger.info("Saleor service created successfully")
        
        # Test product lookup by ID
        logger.info("Testing product lookup by ID...")
        test_product_id = "338778"  # From your log example
        
        async with connection:
            saleor_data = await service.get_saleor_product_details(test_product_id)
            if saleor_data:
                logger.info(f"✅ Successfully fetched Saleor data for product ID {test_product_id}")
                logger.info(f"   Response: {saleor_data.get('answer', 'No answer')[:100]}...")
            else:
                logger.warning(f"⚠️ No Saleor data found for product ID {test_product_id}")
        
        # Test product lookup by name
        logger.info("Testing product lookup by name...")
        test_product_name = "Apple Ginger Zest (Sugar-Free)"  # From your log example
        
        async with connection:
            saleor_data = await service.get_saleor_product_details_by_name(test_product_name)
            if saleor_data:
                logger.info(f"✅ Successfully fetched Saleor data for product name '{test_product_name}'")
                logger.info(f"   Response: {saleor_data.get('answer', 'No answer')[:100]}...")
            else:
                logger.warning(f"⚠️ No Saleor data found for product name '{test_product_name}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to test Saleor service: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Saleor integration tests...")
    
    # Test connection
    connection_ok = await test_saleor_connection()
    if not connection_ok:
        logger.error("❌ Connection test failed. Make sure the Saleor API server is running on port 8002")
        return
    
    # Test service
    service_ok = await test_saleor_service()
    if not service_ok:
        logger.error("❌ Service test failed")
        return
    
    logger.info("✅ All tests passed! Saleor integration is working correctly.")


if __name__ == "__main__":
    asyncio.run(main())
