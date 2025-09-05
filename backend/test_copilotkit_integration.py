#!/usr/bin/env python3
"""
Test script for CopilotKit integration
This script tests the CopilotKit endpoints to ensure they work correctly
"""

import asyncio
import json
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "http://localhost:8000"

async def test_copilotkit_endpoints():
    """Test all CopilotKit endpoints"""
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing CopilotKit Integration...")
        print("=" * 50)
        
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        try:
            response = await client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test 2: Models Endpoint
        print("\n2. Testing Models Endpoint...")
        try:
            response = await client.get(f"{BACKEND_URL}/v1/models")
            if response.status_code == 200:
                print("✅ Models endpoint passed")
                models = response.json()
                print(f"   Available models: {[model['id'] for model in models['data']]}")
            else:
                print(f"❌ Models endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Models endpoint error: {e}")
        
        # Test 3: Chat Completions
        print("\n3. Testing Chat Completions...")
        try:
            chat_data = {
                "messages": [
                    {"role": "user", "content": "Hello! I'm looking for hiking boots for winter camping."}
                ],
                "model": "gpt-4"
            }
            
            response = await client.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=chat_data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                print("✅ Chat completions passed")
                result = response.json()
                print(f"   Response ID: {result.get('id')}")
                print(f"   Model: {result.get('model')}")
                if result.get('choices'):
                    content = result['choices'][0]['message']['content']
                    print(f"   AI Response: {content[:100]}...")
            else:
                print(f"❌ Chat completions failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Chat completions error: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
        
        # Test 4: Product Search Action
        print("\n4. Testing Product Search Action...")
        try:
            search_data = {
                "query": "hiking boots",
                "max_results": 3
            }
            
            response = await client.post(
                f"{BACKEND_URL}/v1/actions/search-products",
                json=search_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                print("✅ Product search action passed")
                result = response.json()
                print(f"   Found {result.get('total_found', 0)} products")
                if result.get('products'):
                    for i, product in enumerate(result['products'][:2]):
                        print(f"   Product {i+1}: {product.get('name', 'Unknown')} - ${product.get('price', 0)}")
            else:
                print(f"❌ Product search action failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Product search action error: {e}")
        
        # Test 5: Order Status Action
        print("\n5. Testing Order Status Action...")
        try:
            order_data = {
                "user_email": "vanessa.bird@example.com"
            }
            
            response = await client.post(
                f"{BACKEND_URL}/v1/actions/check-order-status",
                json=order_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                print("✅ Order status action passed")
                result = response.json()
                print(f"   Found {result.get('total_orders', 0)} orders for {result.get('user_email')}")
            else:
                print(f"❌ Order status action failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Order status action error: {e}")
        
        # Test 6: Available Actions
        print("\n6. Testing Available Actions...")
        try:
            response = await client.get(f"{BACKEND_URL}/v1/actions")
            if response.status_code == 200:
                print("✅ Available actions endpoint passed")
                result = response.json()
                actions = result.get('actions', [])
                print(f"   Available actions: {[action['name'] for action in actions]}")
            else:
                print(f"❌ Available actions failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Available actions error: {e}")
        
        # Test 7: Root Endpoint (CopilotKit Discovery)
        print("\n7. Testing Root Endpoint...")
        try:
            response = await client.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                print("✅ Root endpoint passed")
                result = response.json()
                print(f"   Service: {result.get('name', 'Unknown')}")
                print(f"   Version: {result.get('version', 'Unknown')}")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
        
        # Test 8: Action Execution
        print("\n8. Testing Action Execution...")
        try:
            action_data = {
                "query": "hiking boots",
                "max_results": 2
            }
            
            response = await client.post(
                f"{BACKEND_URL}/v1/actions/search_products",
                json=action_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                print("✅ Action execution passed")
                result = response.json()
                if result.get('success'):
                    products = result.get('result', {}).get('products', [])
                    print(f"   Found {len(products)} products via action")
                else:
                    print(f"   Action failed: {result.get('error')}")
            else:
                print(f"❌ Action execution failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Action execution error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 CopilotKit Integration Test Complete!")
        print("\nNext Steps:")
        print("1. Install CopilotKit in your frontend:")
        print("   npm install @copilotkit/react-core @copilotkit/react-ui")
        print("\n2. Configure CopilotKit provider:")
        print(f"   <CopilotKit runtimeUrl=\"{BACKEND_URL}/v1/chat/completions\">")
        print("\n3. Add CopilotPopup component to your app")
        print("\n4. Test the chat popup in your frontend!")

if __name__ == "__main__":
    asyncio.run(test_copilotkit_endpoints())
