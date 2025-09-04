import os
import json
import requests
from typing import Optional, List, Dict, Any
from pprint import pprint

def ask_graph(
    question: str,
    additional_details: Optional[str] = None,
    kg_products: Optional[Any] = None,
    kg_response: Optional[Any] = None,
    session_id: str = "test",
    model: str = "openai_gpt_4o",
    mode: str = "graph",
    uri: Optional[str] = None,
    userName: Optional[str] = None,
    password: Optional[str] = None,
    database: str = "neo4j",
    document_names: Optional[List[str]] = None,
    backend_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call the new Saleor graph API with the given parameters.
    
    Example:
        response = ask_graph(
            question="What juices are there?",
            additional_details="USD prices",
            kg_products=["Carrot Juice", "Banana Juice"],
            session_id="demo"
        )
        print(json.dumps(response, indent=2))
    """
    # url = backend_url or os.getenv("BACKEND_URL", "http://localhost:8002/chat_bot")
    url = backend_url or os.getenv("BACKEND_URL", "http://localhost:8002/orders")
    
    # Prepare form data
    data = {
        "question": question,
        "session_id": session_id,
        "model": model,
        "mode": mode,
        "database": database,
        "document_names": json.dumps(document_names or [])
    }
    
    # Optional fields
    if additional_details:
        data["additional_details"] = additional_details
    if uri:
        data["uri"] = uri
    if userName:
        data["userName"] = userName
    if password:
        data["password"] = password
    
    # Handle KG inputs
    if kg_products is not None:
        if isinstance(kg_products, (dict, list, str)):
            data["kg_products"] = json.dumps(kg_products) if isinstance(kg_products, (dict, list)) else kg_products
    
    if kg_response is not None:
        if isinstance(kg_response, (dict, list, str)):
            data["kg_response"] = json.dumps(kg_response) if isinstance(kg_response, (dict, list)) else kg_response

    # Make the request
    response = requests.post(url, data=data, timeout=120)
    response.raise_for_status()
    return response.json()

# Example usage
if __name__ == "__main__":
    # Example with KG inputs
    result = ask_graph(
        question="fetch product data based on the ids",
        # additional_details="steven.walsh@example.com",
        kg_products= [
            "UHJvZHVjdDoxNTc=",
            "UHJvZHVjdDoxNTM=",
            "UHJvZHVjdDoxNTU="
        ],
        session_id="demo"
    )
    # print(json.dumps(result, indent=2))
    pprint(result)

    if result and isinstance(result, dict):
        data = result.get("data", {})
    answer_block = data.get("answer", "")

    # Extract the "Final response" part if present
    final_answer = None
    if "### Final response" in answer_block:
        final_answer = answer_block.split("### Final response", 1)[1].strip()

    if final_answer:
        print(f"Sending answer to user:\n{final_answer}")
    else:
        print("Full answer block:\n", answer_block)
