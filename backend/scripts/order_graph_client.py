#!/usr/bin/env python3
"""
Client function for calling the order graph API.

This module provides a function similar to ask_graph but specifically for order-related queries.
"""

import os
import json
import requests
from typing import Optional, Dict, Any


def ask_orders_graph(
    question: str,
    user_email: Optional[str] = None,
    order_id: Optional[str] = None,
    additional_details: Optional[str] = None,
    session_id: str = "default",
    model: str = "openai_gpt_4o",
    mode: str = "graph",
    backend_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call the order graph API with the given parameters.
    
    Example:
        response = ask_orders_graph(
            question="What are my recent orders?",
            user_email="user@example.com",
            session_id="demo"
        )
        print(json.dumps(response, indent=2))
    """
    url = backend_url or os.getenv("BACKEND_URL", "http://localhost:8002/orders")
    
    # Prepare form data
    data = {
        "question": question,
        "session_id": session_id,
        "model": model,
        "mode": mode,
        "database": "mongodb",  # Using MongoDB for orders
        "document_names": json.dumps([])
    }
    
    # Optional fields
    if user_email:
        data["user_email"] = user_email
    if order_id:
        data["order_id"] = order_id
    if additional_details:
        data["additional_details"] = additional_details

    # Make the request
    response = requests.post(url, data=data, timeout=120)
    response.raise_for_status()
    return response.json()


def extract_final_answer(api_response: Dict[str, Any]) -> str:
    """Extract the final answer from the API response.

    Args:
        api_response: Response from the graph API

    Returns:
        Extracted final answer or full response
    """
    try:
        if not api_response or not isinstance(api_response, dict):
            return "No response received from the API."
        
        data = api_response.get("data", {})
        answer_block = data.get("answer", "")
        
        # Extract the "Final response" part if present
        if "### Final response" in answer_block:
            final_answer = answer_block.split("### Final response", 1)[1].strip()
            return final_answer
        else:
            return answer_block
            
    except Exception as e:
        print(f"Error extracting final answer: {e}")
        return str(api_response)


# Example usage
if __name__ == "__main__":
    # Example 1: General order question
    print("=== Example 1: General Order Question ===")
    result = ask_orders_graph(
        question="What are the most recent orders and their status?",
        session_id="demo"
    )
    print(json.dumps(result, indent=2))
    
    final_answer = extract_final_answer(result)
    print(f"Final Answer: {final_answer}")
    print()
    
    # Example 2: User-specific question
    print("=== Example 2: User-Specific Question ===")
    result = ask_orders_graph(
        question="What are my recent orders and their total value?",
        user_email="user@example.com",
        session_id="demo"
    )
    print(json.dumps(result, indent=2))
    
    final_answer = extract_final_answer(result)
    print(f"Final Answer: {final_answer}")
    print()
    
    # Example 3: Specific order question
    print("=== Example 3: Specific Order Question ===")
    result = ask_orders_graph(
        question="What is the status of this order and when was it created?",
        order_id="507f1f77bcf86cd799439011",
        session_id="demo"
    )
    print(json.dumps(result, indent=2))
    
    final_answer = extract_final_answer(result)
    print(f"Final Answer: {final_answer}")
    print()
    
    # Example 4: Complex analysis question
    print("=== Example 4: Complex Analysis Question ===")
    result = ask_orders_graph(
        question="Analyze my order history and suggest products I might be interested in based on my previous purchases",
        user_email="user@example.com",
        additional_details="Focus on categories and price ranges from previous orders",
        session_id="demo"
    )
    print(json.dumps(result, indent=2))
    
    final_answer = extract_final_answer(result)
    print(f"Final Answer: {final_answer}")
