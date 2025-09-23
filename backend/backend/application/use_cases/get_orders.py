"""Use cases for order-related operations."""

import logging
import os
import json
import requests
from typing import Optional, List, Dict, Any

from backend.application.services import OrderService
from backend.domain.entities import Order

logger = logging.getLogger("conversational_commerce")


class CreateOrderUseCase:
    """Use case for creating a new order."""

    def __init__(self, order_service: OrderService):
        """Initialize the CreateOrderUseCase.

        Args:
            order_service: Order service for order operations
        """
        self.order_service = order_service

    async def execute(self, order: Order) -> Order:
        """Execute the use case to create a new order.

        Args:
            order: The order to create

        Returns:
            The created order
        """
        return await self.order_service.create_order(order)


class GetOrdersUseCase:
    """Use case for retrieving orders."""

    def __init__(self, order_service: OrderService):
        """Initialize the GetOrdersUseCase.

        Args:
            order_service: Order service for order operations
        """
        self.order_service = order_service

    async def execute(self, user_id: Optional[str] = None) -> List[Order]:
        """Execute the use case to retrieve orders.

        Args:
            user_id: Optional user ID to filter orders

        Returns:
            List of orders
        """
        if user_id:
            return await self.order_service.get_user_orders(user_id)
        else:
            return await self.order_service.get_all_orders()

    async def ask_orders_graph(
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
        """Ask questions about orders using the external graph API."""
        try:
            logger.info(f"Processing order question: '{question}' for user: {user_email}")
            
            # Get order data from local database
            orders_data = await self.order_service.get_orders_for_graph_api(user_email, order_id)
            logger.info(f"Retrieved {len(orders_data) if orders_data else 0} orders from database")
            
            # Try external API first
            try:
                url = backend_url or os.getenv("ORDER_GRAPH_API_URL", "http://localhost:8000/v1/saleor/orders")
                timeout_seconds = float(os.getenv("ORDER_GRAPH_TIMEOUT", "60"))
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
                    data["additional_details"] = user_email
                if order_id:
                    data["order_id"] = order_id
                if additional_details:
                    data["additional_details"] = additional_details
                
                # Add order data as context if available
                if orders_data:
                    data["kg_products"] = json.dumps(orders_data)
                    data["kg_response"] = json.dumps([f"Available order data: {len(orders_data)} orders found"])
                
                # Make the request
                response = requests.post(url, data=data, timeout=timeout_seconds)
                response.raise_for_status()
                result = response.json()
                logger.info(f"External API response received: {result}")
                return result
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"External API failed, falling back to local processing: {e}")
                # Fallback to local processing
                return await self._process_order_question_locally(question, user_email, order_id, orders_data)
                
        except Exception as e:
            logger.error(f"Unexpected error in ask_orders_graph: {e}", exc_info=True)
            return {
                "error": f"Unexpected error: {str(e)}",
                "final_answer": "Sorry, an unexpected error occurred while processing your request."
            }

    async def _process_order_question_locally(
        self, 
        question: str, 
        user_email: Optional[str], 
        order_id: Optional[str], 
        orders_data: List[dict]
    ) -> Dict[str, Any]:
        """Process order questions locally when external API is not available."""
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


class UpdateOrderUseCase:
    """Use case for updating an order."""

    def __init__(self, order_service: OrderService):
        """Initialize the UpdateOrderUseCase.

        Args:
            order_service: Order service for order operations
        """
        self.order_service = order_service

    async def execute(self, order: Order) -> Order:
        """Execute the use case to update an order.

        Args:
            order: The order to update

        Returns:
            The updated order
        """
        return await self.order_service.update_order(order)


class DeleteOrderUseCase:
    """Use case for deleting an order."""

    def __init__(self, order_service: OrderService):
        """Initialize the DeleteOrderUseCase.

        Args:
            order_service: Order service for order operations
        """
        self.order_service = order_service

    async def execute(self, order_id: str) -> bool:
        """Execute the use case to delete an order.

        Args:
            order_id: The ID of the order to delete

        Returns:
            True if the order was successfully deleted
        """
        return await self.order_service.delete_order(order_id)
