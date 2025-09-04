from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from backend.domain.entities import Order, OrderStatus


class IOrderRepository(ABC):
    """Interface for order repository operations."""

    @abstractmethod
    async def create_order(self, order: Order) -> Order:
        """Create a new order.

        Args:
            order: Order object to create

        Returns:
            The created Order object
        """
        pass

    @abstractmethod
    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get an order by its ID.

        Args:
            order_id: The order ID to retrieve

        Returns:
            Order object if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_orders_by_user_id(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders for a specific user.

        Args:
            user_id: The user ID to get orders for
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            List of Order objects for the user
        """
        pass

    @abstractmethod
    async def get_orders_by_status(self, status: OrderStatus, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders by status.

        Args:
            status: The order status to filter by
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            List of Order objects with the specified status
        """
        pass

    @abstractmethod
    async def get_orders_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            List of Order objects within the date range
        """
        pass

    @abstractmethod
    async def update_order_status(self, order_id: str, status: OrderStatus) -> Optional[Order]:
        """Update the status of an order.

        Args:
            order_id: The order ID to update
            status: The new status

        Returns:
            Updated Order object if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_order(self, order: Order) -> Optional[Order]:
        """Update an existing order.

        Args:
            order: The order object with updated information

        Returns:
            Updated Order object if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_order(self, order_id: str) -> bool:
        """Delete an order.

        Args:
            order_id: The order ID to delete

        Returns:
            True if the order was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def get_order_statistics(self, user_id: Optional[str] = None) -> dict:
        """Get order statistics.

        Args:
            user_id: Optional user ID to get statistics for

        Returns:
            Dictionary containing order statistics
        """
        pass

    @abstractmethod
    async def get_orders_for_graph_api(self, user_email: Optional[str] = None, order_id: Optional[str] = None) -> List[dict]:
        """Get orders in a format suitable for the graph API.

        Args:
            user_email: User's email to filter orders
            order_id: Specific order ID to retrieve

        Returns:
            List of order dictionaries formatted for graph API
        """
        pass
