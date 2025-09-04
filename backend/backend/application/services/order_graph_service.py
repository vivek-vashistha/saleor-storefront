import logging
import os
import json
import requests
from typing import Optional, List, Dict, Any

from backend.application.services.order_service import OrderService

logger = logging.getLogger("conversational_commerce")


class OrderGraphService:
    """Service for handling order-related graph API interactions."""

    def __init__(self, order_service: OrderService):
        """Initialize the OrderGraphService.

        Args:
            order_service: Order service for accessing order data
        """
        self.order_service = order_service

    async def ask_orders_question(
        self,
        question: str,
        user_email: Optional[str] = None,
        order_id: Optional[str] = None,
        additional_details: Optional[str] = None,
        session_id: str = "default",
        model: str = "openai_gpt_4o",
        mode: str = "graph",
        backend_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ask questions about orders using the external graph API.

        Args:
            question: The question about orders
            user_email: User's email for filtering orders
            order_id: Specific order ID to focus on
            additional_details: Additional context or details
            session_id: Session identifier
            model: AI model to use
            mode: API mode
            backend_url: External API URL

        Returns:
            Dictionary containing the API response
        """
        try:
            logger.info(f"Processing order question: '{question}' for user: {user_email}")
            
            # Get order data from local database
            orders_data = await self.order_service.get_orders_for_graph_api(user_email, order_id)
            logger.info(f"Retrieved {len(orders_data) if orders_data else 0} orders from database")
            
            # Try external API first
            try:
                url = backend_url or os.getenv("ORDER_GRAPH_API_URL", "http://localhost:8002/orders")
                logger.info(f"Attempting to call external API: {url}")
                
                # Prepare form data
                data = {
                    "question": question,
                    "session_id": session_id,
                    "model": model,
                    "mode": mode,
                    "database": "mongodb",
                    "document_names": json.dumps([])
                }
                
                # Add user-specific information
                if user_email:
                    data["user_email"] = user_email
                if order_id:
                    data["order_id"] = order_id
                if additional_details:
                    data["additional_details"] = additional_details
                
                # Add order data as context if available
                if orders_data:
                    data["kg_products"] = json.dumps(orders_data)
                    data["kg_response"] = json.dumps([f"Available order data: {len(orders_data)} orders found"])
                
                # Make the request
                response = requests.post(url, data=data, timeout=30)
                response.raise_for_status()
                result = response.json()
                logger.info(f"External API response received: {result}")
                return result
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"External API failed, falling back to local processing: {e}")
                # Fallback to local processing
                return await self._process_order_question_locally(question, user_email, order_id, orders_data)
                
        except Exception as e:
            logger.error(f"Unexpected error in ask_orders_question: {e}", exc_info=True)
            return {
                "error": f"Unexpected error: {str(e)}",
                "final_answer": "Sorry, an unexpected error occurred while processing your request."
            }

    async def get_orders_context(self, user_email: Optional[str] = None, order_id: Optional[str] = None) -> Dict[str, Any]:
        """Get order context data for the graph API.

        Args:
            user_email: User's email to filter orders
            order_id: Specific order ID to retrieve

        Returns:
            Dictionary containing order context data
        """
        try:
            orders = await self.order_service.get_orders_for_graph_api(user_email, order_id)
            
            # Create a summary of the orders
            total_orders = len(orders)
            total_amount = sum(order.get("total_amount", 0) for order in orders)
            status_breakdown = {}
            
            for order in orders:
                status = order.get("status", "unknown")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            context = {
                "total_orders": total_orders,
                "total_amount": total_amount,
                "status_breakdown": status_breakdown,
                "orders": orders[:10]  # Limit to first 10 orders for context
            }
            
            logger.info(f"Generated order context for {total_orders} orders")
            return context
            
        except Exception as e:
            logger.error(f"Error generating order context: {e}")
            return {
                "total_orders": 0,
                "total_amount": 0,
                "status_breakdown": {},
                "orders": []
            }

    def extract_final_answer(self, api_response: Dict[str, Any]) -> str:
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
            logger.error(f"Error extracting final answer: {e}")
            return str(api_response)

    async def _process_order_question_locally(
        self, 
        question: str, 
        user_email: Optional[str], 
        order_id: Optional[str], 
        orders_data: List[dict]
    ) -> Dict[str, Any]:
        """
        Process order questions locally when external API is not available.
        
        Args:
            question: The question about orders
            user_email: User's email
            order_id: Specific order ID
            orders_data: List of order data from database
            
        Returns:
            Dictionary with processed response
        """
        try:
            logger.info(f"Processing order question locally: '{question}'")
            
            if not orders_data:
                return {
                    "final_answer": f"I couldn't find any orders for the email {user_email}. Please check your email address or contact customer support if you believe this is an error."
                }
            
            # Simple keyword-based response generation
            question_lower = question.lower()
            
            if "status" in question_lower:
                # Generate status summary
                status_counts = {}
                for order in orders_data:
                    status = order.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                status_summary = ", ".join([f"{count} {status}" for status, count in status_counts.items()])
                return {
                    "final_answer": f"You have {len(orders_data)} orders with the following statuses: {status_summary}."
                }
            
            elif "recent" in question_lower or "latest" in question_lower:
                # Show recent orders
                recent_orders = sorted(orders_data, key=lambda x: x.get("created_at", ""), reverse=True)[:3]
                order_summary = []
                for order in recent_orders:
                    order_summary.append(f"Order {order.get('order_id')} - {order.get('status')} - ${order.get('total_amount')}")
                
                return {
                    "final_answer": f"Your recent orders: {'; '.join(order_summary)}"
                }
            
            elif "total" in question_lower or "amount" in question_lower or "spent" in question_lower:
                # Calculate total spent
                total_amount = sum(order.get("total_amount", 0) for order in orders_data)
                return {
                    "final_answer": f"You have spent a total of ${total_amount:.2f} across {len(orders_data)} orders."
                }
            
            else:
                # General order summary
                total_amount = sum(order.get("total_amount", 0) for order in orders_data)
                return {
                    "final_answer": f"You have {len(orders_data)} orders with a total value of ${total_amount:.2f}. Your most recent order is {orders_data[0].get('order_id') if orders_data else 'N/A'} with status {orders_data[0].get('status') if orders_data else 'N/A'}."
                }
                
        except Exception as e:
            logger.error(f"Error in local order processing: {e}", exc_info=True)
            return {
                "final_answer": "I'm sorry, I'm having trouble processing your order information right now."
            }
