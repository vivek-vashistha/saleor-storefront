#!/usr/bin/env python3
"""
Test script to verify CopilotKit integration with LangGraph agents
"""

import asyncio
import json
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_copilotkit_langgraph_integration():
    """Test the CopilotKit integration with LangGraph agents."""
    
    base_url = "http://localhost:8000"
    
    # Test 1: Basic chat completion with LangGraph agents
    logger.info("🧪 Test 1: Basic chat completion with LangGraph agents")
    
    chat_payload = {
        "messages": [
            {"role": "user", "content": "I need hiking boots for winter camping"}
        ],
        "model": "gpt-4",
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=chat_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Chat completion successful!")
            logger.info(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
        else:
            logger.error(f"❌ Chat completion failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Chat completion error: {e}")
    
    # Test 2: Product search action with LangGraph agents
    logger.info("\n🧪 Test 2: Product search action with LangGraph agents")
    
    search_payload = {
        "query": "waterproof hiking boots for winter",
        "max_results": 3
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/actions/search_products",
            json=search_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Product search successful!")
            if result.get("success"):
                products = result.get("result", {}).get("products", [])
                logger.info(f"Found {len(products)} products:")
                for i, product in enumerate(products, 1):
                    logger.info(f"  {i}. {product.get('name', 'Unknown')} - ${product.get('price', 'N/A')}")
            else:
                logger.error(f"❌ Product search failed: {result.get('error', 'Unknown error')}")
        else:
            logger.error(f"❌ Product search failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Product search error: {e}")
    
    # Test 3: Order status check
    logger.info("\n🧪 Test 3: Order status check")
    
    order_payload = {
        "user_email": "test@example.com"
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/actions/check_order_status",
            json=order_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Order status check successful!")
            if result.get("success"):
                orders = result.get("result", {}).get("orders", [])
                logger.info(f"Found {len(orders)} orders for user")
            else:
                logger.info(f"ℹ️ No orders found or error: {result.get('error', 'No orders')}")
        else:
            logger.error(f"❌ Order status check failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Order status check error: {e}")
    
    # Test 4: Health check
    logger.info("\n🧪 Test 4: Health check")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Health check successful!")
            logger.info(f"Status: {result.get('status', 'Unknown')}")
        else:
            logger.error(f"❌ Health check failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🚀 Testing CopilotKit + LangGraph Integration")
    print("=" * 50)
    asyncio.run(test_copilotkit_langgraph_integration())
    print("\n✨ Test completed!")
