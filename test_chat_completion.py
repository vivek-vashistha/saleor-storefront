#!/usr/bin/env python3
"""
Test script to verify CopilotKit chat completion with LangGraph agents
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chat_completion():
    """Test the chat completion endpoint."""
    
    base_url = "http://localhost:8000"
    
    # Test chat completion with product search
    logger.info("🧪 Testing chat completion with product search")
    
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
            
            # Extract the response content
            choices = result.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', 'No content')
                logger.info(f"Response: {content}")
                
                # Check if product recommendations are included
                if "Product Recommendations:" in content:
                    logger.info("✅ Product recommendations included in response!")
                else:
                    logger.warning("⚠️ No product recommendations found in response")
            else:
                logger.error("❌ No choices in response")
        else:
            logger.error(f"❌ Chat completion failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Chat completion error: {e}")

if __name__ == "__main__":
    print("🚀 Testing CopilotKit Chat Completion")
    print("=" * 50)
    test_chat_completion()
    print("\n✨ Test completed!")
