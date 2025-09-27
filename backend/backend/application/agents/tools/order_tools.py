"""Order-related tools for Deep Agents."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.application.services.order_graph_service import OrderGraphService

logger = logging.getLogger("conversational_commerce.order_tools")


class OrderTools:
    """Order-related tools for Deep Agents."""

    def __init__(self, order_graph_service: OrderGraphService):
        """Initialize order tools.

        Args:
            order_graph_service: Order graph service for operations
        """
        self.order_graph_service = order_graph_service

    async def check_order_status_tool(
        self,
        user_email: str,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check order status with comprehensive information.

        Args:
            user_email: User's email address
            order_id: Optional specific order ID

        Returns:
            Dictionary with order status information
        """
        try:
            logger.info(f"Checking order status for email: {user_email}")
            
            if order_id:
                # Get specific order
                order = await self.order_graph_service.order_service.get_order_by_id(order_id)
                if order:
                    order_details = await self.order_graph_service.order_service.get_order_details(order.id)
                    return {
                        "order": order_details,
                        "status": "found",
                        "order_id": order_id,
                        "email": user_email
                    }
                else:
                    return {
                        "order": None,
                        "status": "not_found",
                        "order_id": order_id,
                        "email": user_email,
                        "error": "Order not found"
                    }
            else:
                # Get user's orders
                orders = await self.order_graph_service.order_service.get_user_orders(user_email)
                if orders:
                    # Get details for the most recent order
                    most_recent_order = max(orders, key=lambda x: x.created_at)
                    order_details = await self.order_graph_service.order_service.get_order_details(most_recent_order.id)
                    return {
                        "order": order_details,
                        "status": "found",
                        "order_id": most_recent_order.id,
                        "email": user_email,
                        "total_orders": len(orders)
                    }
                else:
                    return {
                        "order": None,
                        "status": "not_found",
                        "email": user_email,
                        "error": "No orders found"
                    }
            
        except Exception as e:
            logger.error(f"Error checking order status for {user_email}: {e}")
            return {
                "order": None,
                "status": "error",
                "email": user_email,
                "error": str(e)
            }

    async def track_shipment_tool(
        self,
        order_id: str
    ) -> Dict[str, Any]:
        """Track shipment for an order.

        Args:
            order_id: The order ID to track

        Returns:
            Dictionary with tracking information
        """
        try:
            logger.info(f"Tracking shipment for order: {order_id}")
            
            # Get shipment tracking information
            tracking_info = await self.order_graph_service.order_service.get_shipment_tracking(order_id)
            
            if tracking_info:
                return {
                    "tracking": tracking_info,
                    "status": "found",
                    "order_id": order_id
                }
            else:
                return {
                    "tracking": None,
                    "status": "not_found",
                    "order_id": order_id,
                    "error": "Tracking information not available"
                }
            
        except Exception as e:
            logger.error(f"Error tracking shipment for order {order_id}: {e}")
            return {
                "tracking": None,
                "status": "error",
                "order_id": order_id,
                "error": str(e)
            }

    async def process_refund_tool(
        self,
        order_id: str,
        items: List[Dict[str, Any]],
        reason: str
    ) -> Dict[str, Any]:
        """Process refund with proper validation.

        Args:
            order_id: The order ID
            items: List of items to refund
            reason: Reason for refund

        Returns:
            Dictionary with refund processing results
        """
        try:
            logger.info(f"Processing refund for order: {order_id}")
            
            # Check refund eligibility
            eligibility = await self.order_graph_service.order_service.check_refund_eligibility(
                order_id, items
            )
            
            if eligibility.get("eligible", False):
                # Process the refund
                refund = await self.order_graph_service.order_service.process_refund(
                    order_id, items, reason
                )
                return {
                    "refund": refund,
                    "status": "processed",
                    "order_id": order_id,
                    "items": items,
                    "reason": reason
                }
            else:
                return {
                    "refund": None,
                    "status": "not_eligible",
                    "order_id": order_id,
                    "items": items,
                    "reason": reason,
                    "eligibility_reason": eligibility.get("reason", "Unknown")
                }
            
        except Exception as e:
            logger.error(f"Error processing refund for order {order_id}: {e}")
            return {
                "refund": None,
                "status": "error",
                "order_id": order_id,
                "items": items,
                "reason": reason,
                "error": str(e)
            }

    async def get_order_history_tool(
        self,
        user_email: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get user's order history.

        Args:
            user_email: User's email address
            limit: Maximum number of orders to return

        Returns:
            Dictionary with order history
        """
        try:
            logger.info(f"Getting order history for email: {user_email}")
            
            # Get user's orders
            orders = await self.order_graph_service.order_service.get_user_orders(user_email)
            
            if orders:
                # Sort by creation date (most recent first)
                sorted_orders = sorted(orders, key=lambda x: x.created_at, reverse=True)
                limited_orders = sorted_orders[:limit]
                
                # Get details for each order
                order_details = []
                for order in limited_orders:
                    details = await self.order_graph_service.order_service.get_order_details(order.id)
                    order_details.append(details)
                
                return {
                    "orders": order_details,
                    "status": "found",
                    "email": user_email,
                    "total_orders": len(orders),
                    "returned_orders": len(order_details)
                }
            else:
                return {
                    "orders": [],
                    "status": "not_found",
                    "email": user_email,
                    "total_orders": 0,
                    "returned_orders": 0
                }
            
        except Exception as e:
            logger.error(f"Error getting order history for {user_email}: {e}")
            return {
                "orders": [],
                "status": "error",
                "email": user_email,
                "error": str(e)
            }

    async def update_order_tool(
        self,
        order_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update order information.

        Args:
            order_id: The order ID
            updates: Dictionary of updates to apply

        Returns:
            Dictionary with update results
        """
        try:
            logger.info(f"Updating order: {order_id}")
            
            # Update order using the service
            updated_order = await self.order_graph_service.order_service.update_order(
                order_id, updates
            )
            
            if updated_order:
                return {
                    "order": updated_order,
                    "status": "updated",
                    "order_id": order_id,
                    "updates": updates
                }
            else:
                return {
                    "order": None,
                    "status": "not_found",
                    "order_id": order_id,
                    "updates": updates,
                    "error": "Order not found"
                }
            
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return {
                "order": None,
                "status": "error",
                "order_id": order_id,
                "updates": updates,
                "error": str(e)
            }

    async def get_order_summary_tool(
        self,
        user_email: str
    ) -> Dict[str, Any]:
        """Get order summary for a user.

        Args:
            user_email: User's email address

        Returns:
            Dictionary with order summary
        """
        try:
            logger.info(f"Getting order summary for email: {user_email}")
            
            # Get user's orders
            orders = await self.order_graph_service.order_service.get_user_orders(user_email)
            
            if orders:
                # Calculate summary statistics
                total_orders = len(orders)
                total_spent = sum(order.total_amount for order in orders)
                
                # Get status counts
                status_counts = {}
                for order in orders:
                    status = order.status.value
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # Get most recent order
                most_recent = max(orders, key=lambda x: x.created_at)
                
                return {
                    "summary": {
                        "total_orders": total_orders,
                        "total_spent": total_spent,
                        "status_counts": status_counts,
                        "most_recent_order": {
                            "id": most_recent.id,
                            "status": most_recent.status.value,
                            "total": most_recent.total_amount,
                            "created_at": most_recent.created_at
                        }
                    },
                    "status": "found",
                    "email": user_email
                }
            else:
                return {
                    "summary": {
                        "total_orders": 0,
                        "total_spent": 0,
                        "status_counts": {},
                        "most_recent_order": None
                    },
                    "status": "not_found",
                    "email": user_email
                }
            
        except Exception as e:
            logger.error(f"Error getting order summary for {user_email}: {e}")
            return {
                "summary": None,
                "status": "error",
                "email": user_email,
                "error": str(e)
            }
