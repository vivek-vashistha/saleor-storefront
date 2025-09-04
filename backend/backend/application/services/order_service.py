import logging
from datetime import datetime, timedelta
from typing import List, Optional

from backend.domain.entities import Order, OrderStatus
from backend.infrastructure.repositories.orders_repository.interface import IOrderRepository

logger = logging.getLogger("conversational_commerce")


class OrderService:
    """Service for handling order-related functionality."""

    def __init__(self, order_repository: IOrderRepository):
        """Initialize the OrderService with the provided order repository.

        Args:
            order_repository: Order repository for accessing orders
        """
        self.order_repository = order_repository

    async def create_order(self, order: Order) -> Order:
        """Create a new order.

        Args:
            order: Order object to create

        Returns:
            The created Order object
        """
        try:
            created_order = await self.order_repository.create_order(order)
            logger.info(f"Created order {created_order.order_id} for user {created_order.user_id}")
            return created_order
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get an order by its ID.

        Args:
            order_id: The order ID to retrieve

        Returns:
            Order object if found, None otherwise
        """
        try:
            order = await self.order_repository.get_order_by_id(order_id)
            if order:
                logger.info(f"Retrieved order {order_id}")
            else:
                logger.warning(f"Order {order_id} not found")
            return order
        except Exception as e:
            logger.error(f"Error getting order by ID {order_id}: {e}")
            return None

    async def get_user_orders(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders for a specific user.

        Args:
            user_id: The user ID to get orders for
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            List of Order objects for the user
        """
        try:
            orders = await self.order_repository.get_orders_by_user_id(user_id, limit, offset)
            logger.info(f"Retrieved {len(orders)} orders for user {user_id}")
            return orders
        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            return []

    async def get_orders_by_status(self, status: OrderStatus, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders by status.

        Args:
            status: The order status to filter by
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            List of Order objects with the specified status
        """
        try:
            orders = await self.order_repository.get_orders_by_status(status, limit, offset)
            logger.info(f"Retrieved {len(orders)} orders with status {status.value}")
            return orders
        except Exception as e:
            logger.error(f"Error getting orders by status {status.value}: {e}")
            return []

    async def get_recent_orders(self, days: int = 30, limit: int = 50) -> List[Order]:
        """Get recent orders within a specified number of days.

        Args:
            days: Number of days to look back
            limit: Maximum number of orders to return

        Returns:
            List of recent Order objects
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            orders = await self.order_repository.get_orders_by_date_range(start_date, end_date, limit)
            logger.info(f"Retrieved {len(orders)} recent orders from the last {days} days")
            return orders
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []

    async def update_order_status(self, order_id: str, status: OrderStatus) -> Optional[Order]:
        """Update the status of an order.

        Args:
            order_id: The order ID to update
            status: The new status

        Returns:
            Updated Order object if found, None otherwise
        """
        try:
            updated_order = await self.order_repository.update_order_status(order_id, status)
            if updated_order:
                logger.info(f"Updated order {order_id} status to {status.value}")
            else:
                logger.warning(f"Order {order_id} not found for status update")
            return updated_order
        except Exception as e:
            logger.error(f"Error updating order status for {order_id}: {e}")
            return None

    async def update_order(self, order: Order) -> Optional[Order]:
        """Update an existing order.

        Args:
            order: The order object with updated information

        Returns:
            Updated Order object if found, None otherwise
        """
        try:
            updated_order = await self.order_repository.update_order(order)
            if updated_order:
                logger.info(f"Updated order {order.order_id}")
            else:
                logger.warning(f"Order {order.order_id} not found for update")
            return updated_order
        except Exception as e:
            logger.error(f"Error updating order {order.order_id}: {e}")
            return None

    async def delete_order(self, order_id: str) -> bool:
        """Delete an order.

        Args:
            order_id: The order ID to delete

        Returns:
            True if the order was deleted, False otherwise
        """
        try:
            success = await self.order_repository.delete_order(order_id)
            if success:
                logger.info(f"Deleted order {order_id}")
            else:
                logger.warning(f"Order {order_id} not found for deletion")
            return success
        except Exception as e:
            logger.error(f"Error deleting order {order_id}: {e}")
            return False

    async def get_user_order_statistics(self, user_id: str) -> dict:
        """Get order statistics for a specific user.

        Args:
            user_id: The user ID to get statistics for

        Returns:
            Dictionary containing order statistics for the user
        """
        try:
            stats = await self.order_repository.get_order_statistics(user_id)
            logger.info(f"Retrieved order statistics for user {user_id}")
            return stats
        except Exception as e:
            logger.error(f"Error getting order statistics for user {user_id}: {e}")
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_order_value": 0.0,
                "status_breakdown": {}
            }

    async def get_global_order_statistics(self) -> dict:
        """Get global order statistics.

        Returns:
            Dictionary containing global order statistics
        """
        try:
            stats = await self.order_repository.get_order_statistics()
            logger.info("Retrieved global order statistics")
            return stats
        except Exception as e:
            logger.error(f"Error getting global order statistics: {e}")
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_order_value": 0.0,
                "status_breakdown": {}
            }

    async def get_user_active_orders(self, user_id: str) -> List[Order]:
        """Get active orders for a specific user.

        Args:
            user_id: The user ID to get active orders for

        Returns:
            List of active Order objects for the user
        """
        try:
            all_orders = await self.get_user_orders(user_id, limit=100)
            active_orders = [order for order in all_orders if order.is_active]
            logger.info(f"Retrieved {len(active_orders)} active orders for user {user_id}")
            return active_orders
        except Exception as e:
            logger.error(f"Error getting active orders for user {user_id}: {e}")
            return []

    async def get_orders_for_graph_api(self, user_email: Optional[str] = None, order_id: Optional[str] = None) -> List[dict]:
        """Get orders in a format suitable for the graph API.

        Args:
            user_email: User's email to filter orders
            order_id: Specific order ID to retrieve

        Returns:
            List of order dictionaries formatted for graph API
        """
        try:
            orders = await self.order_repository.get_orders_for_graph_api(user_email, order_id)
            logger.info(f"Retrieved {len(orders)} orders for graph API")
            return orders
        except Exception as e:
            logger.error(f"Error getting orders for graph API: {e}")
            return []
