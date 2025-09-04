#!/usr/bin/env python3
"""
Simple test script for Saleor connection.
This script tests the Saleor API server connectivity without importing backend modules.
"""

import asyncio
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_saleor_api_health():
    """Test if the Saleor API server is accessible."""
    logger.info("Testing Saleor API server health...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            url = "http://localhost:8002/health"
            logger.info(f"Testing health endpoint: {url}")
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed - Status: {response.status}")
                    logger.info(f"   Response: {data}")
                    return True
                else:
                    logger.warning(f"⚠️ Health check failed - Status: {response.status}")
                    return False
                    
    except asyncio.TimeoutError:
        logger.error("❌ Health check timed out after 10 seconds")
        return False
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("   Make sure the Saleor API server is running on port 8002")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


async def test_saleor_orders_endpoint():
    """Test the orders endpoint with a sample product query."""
    logger.info("Testing Saleor orders endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8002/orders"
            
            # Test data for product lookup
            test_data = {
                "question": "Get product details for Apple Ginger Zest (Sugar-Free)",
                "session_id": "test_session",
                "mode": "product_lookup"
            }
            
            logger.info(f"Testing orders endpoint: {url}")
            logger.info(f"Test data: {test_data}")
            
            async with session.post(url, data=test_data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Orders endpoint test passed - Status: {response.status}")
                    logger.info(f"   Response: {data}")
                    
                    # Check if we got a successful response
                    if data.get("status") == "Success":
                        logger.info("✅ Saleor API returned successful response")
                        return True
                    else:
                        logger.warning(f"⚠️ Saleor API returned status: {data.get('status')}")
                        return False
                else:
                    logger.warning(f"⚠️ Orders endpoint test failed - Status: {response.status}")
                    try:
                        error_text = await response.text()
                        logger.warning(f"   Error response: {error_text}")
                    except:
                        pass
                    return False
                    
    except asyncio.TimeoutError:
        logger.error("❌ Orders endpoint test timed out after 30 seconds")
        return False
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting simple Saleor API tests...")
    
    # Test health endpoint
    health_ok = await test_saleor_api_health()
    if not health_ok:
        logger.error("❌ Health check failed. Make sure the Saleor API server is running on port 8002")
        return
    
    # Test orders endpoint
    orders_ok = await test_saleor_orders_endpoint()
    if not orders_ok:
        logger.warning("⚠️ Orders endpoint test had issues, but health check passed")
        logger.info("   The Saleor API server is accessible but may have configuration issues")
        return
    
    logger.info("✅ All tests passed! Saleor API server is working correctly.")
    logger.info("   You can now use the full backend integration.")


if __name__ == "__main__":
    asyncio.run(main())
