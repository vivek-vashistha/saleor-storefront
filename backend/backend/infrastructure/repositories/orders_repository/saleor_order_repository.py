import logging
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

from backend.domain.entities import Order, OrderItem, OrderStatus
from backend.infrastructure.connections.mongodb import IMongoDBConnection
from backend.infrastructure.repositories.orders_repository.interface import IOrderRepository

logger = logging.getLogger("conversational_commerce")


class SaleorOrderRepository(IOrderRepository):
    """Saleor implementation of the order repository using MongoDB as the underlying storage."""

    def __init__(self, connection: IMongoDBConnection):
        """Initialize the Saleor order repository.

        Args:
            connection: MongoDB connection
        """
        self.connection = connection
        self.collection_name = "orders"

    async def create_order(self, order: Order) -> Order:
        """Create a new order.

        Args:
            order: Order object to create

        Returns:
            The created Order object
        """
        try:
            # Convert order to dictionary
            order_dict = order.model_dump()
            order_dict["_id"] = ObjectId()  # Generate MongoDB ObjectId
            order_dict["created_at"] = datetime.now()
            order_dict["updated_at"] = datetime.now()

            # Insert into MongoDB
            result = await self.connection.insert_one(self.collection_name, order_dict)
            
            if result.inserted_id:
                order.order_id = str(result.inserted_id)
                logger.info(f"Created order with ID: {order.order_id}")
                return order
            else:
                raise Exception("Failed to create order")
                
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
            # Convert string ID to ObjectId
            object_id = ObjectId(order_id)
            
            # Query MongoDB
            result = await self.connection.find_one(self.collection_name, {"_id": object_id})
            
            if result:
                # Convert MongoDB document to Order object
                result["order_id"] = str(result["_id"])
                del result["_id"]
                return Order(**result)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting order by ID {order_id}: {e}")
            return None

    async def get_orders_by_user_id(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders for a specific user.

        Args:
            user_id: The user ID to get orders for
            limit: Maximum number of orders to return
            offset: Number of orders to skip

        Returns:
            List of Order objects for the user
        """
        try:
            # Query MongoDB
            cursor = await self.connection.find(
                self.collection_name,
                {"user_id": user_id},
                limit=limit,
                skip=offset,
                sort=[("created_at", -1)]  # Sort by creation date, newest first
            )
            
            orders = []
            async for doc in cursor:
                doc["order_id"] = str(doc["_id"])
                del doc["_id"]
                orders.append(Order(**doc))
            
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
            # Query MongoDB
            cursor = await self.connection.find(
                self.collection_name,
                {"status": status.value},
                limit=limit,
                skip=offset,
                sort=[("created_at", -1)]
            )
            
            orders = []
            async for doc in cursor:
                doc["order_id"] = str(doc["_id"])
                del doc["_id"]
                orders.append(Order(**doc))
            
            logger.info(f"Retrieved {len(orders)} orders with status {status.value}")
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders by status {status.value}: {e}")
            return []

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
        try:
            # Query MongoDB
            cursor = await self.connection.find(
                self.collection_name,
                {
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                },
                limit=limit,
                skip=offset,
                sort=[("created_at", -1)]
            )
            
            orders = []
            async for doc in cursor:
                doc["order_id"] = str(doc["_id"])
                del doc["_id"]
                orders.append(Order(**doc))
            
            logger.info(f"Retrieved {len(orders)} orders between {start_date} and {end_date}")
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders by date range: {e}")
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
            object_id = ObjectId(order_id)
            
            # Update in MongoDB
            result = await self.connection.update_one(
                self.collection_name,
                {"_id": object_id},
                {
                    "$set": {
                        "status": status.value,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated order {order_id} status to {status.value}")
                return await self.get_order_by_id(order_id)
            else:
                logger.warning(f"Order {order_id} not found for status update")
                return None
                
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
            object_id = ObjectId(order.order_id)
            
            # Convert order to dictionary
            order_dict = order.model_dump()
            order_dict["updated_at"] = datetime.now()
            del order_dict["order_id"]  # Remove order_id as it's stored as _id
            
            # Update in MongoDB
            result = await self.connection.update_one(
                self.collection_name,
                {"_id": object_id},
                {"$set": order_dict}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated order {order.order_id}")
                return await self.get_order_by_id(order.order_id)
            else:
                logger.warning(f"Order {order.order_id} not found for update")
                return None
                
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
            object_id = ObjectId(order_id)
            
            # Delete from MongoDB
            result = await self.connection.delete_one(self.collection_name, {"_id": object_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted order {order_id}")
                return True
            else:
                logger.warning(f"Order {order_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting order {order_id}: {e}")
            return False

    async def get_order_statistics(self, user_id: Optional[str] = None) -> dict:
        """Get order statistics.

        Args:
            user_id: Optional user ID to get statistics for

        Returns:
            Dictionary containing order statistics
        """
        try:
            match_filter = {"user_id": user_id} if user_id else {}
            
            # Aggregate pipeline for statistics
            pipeline = [
                {"$match": match_filter},
                {
                    "$group": {
                        "_id": None,
                        "total_orders": {"$sum": 1},
                        "total_revenue": {"$sum": "$total_amount"},
                        "avg_order_value": {"$avg": "$total_amount"},
                        "status_counts": {
                            "$push": "$status"
                        }
                    }
                }
            ]
            
            result = await self.connection.aggregate(self.collection_name, pipeline)
            
            stats = {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_order_value": 0.0,
                "status_breakdown": {}
            }
            
            async for doc in result:
                stats["total_orders"] = doc.get("total_orders", 0)
                stats["total_revenue"] = doc.get("total_revenue", 0.0)
                stats["avg_order_value"] = doc.get("avg_order_value", 0.0)
                
                # Count statuses
                status_counts = {}
                for status in doc.get("status_counts", []):
                    status_counts[status] = status_counts.get(status, 0) + 1
                stats["status_breakdown"] = status_counts
            
            logger.info(f"Retrieved order statistics for user {user_id or 'all'}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}")
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "avg_order_value": 0.0,
                "status_breakdown": {}
            }

    async def get_orders_for_graph_api(self, user_email: Optional[str] = None, order_id: Optional[str] = None) -> List[dict]:
        """Get orders in a format suitable for the graph API.

        Args:
            user_email: User's email to filter orders
            order_id: Specific order ID to retrieve

        Returns:
            List of order dictionaries formatted for graph API
        """
        try:
            # Build query filter
            filter_query = {}
            if user_email:
                filter_query["user_id"] = user_email  # Assuming user_id stores email
            if order_id:
                filter_query["_id"] = ObjectId(order_id)
            
            # Query MongoDB
            cursor = await self.connection.find(
                self.collection_name,
                filter_query,
                limit=100,  # Limit for graph API context
                sort=[("created_at", -1)]
            )
            
            orders = []
            async for doc in cursor:
                # Convert MongoDB document to a clean dictionary
                order_dict = {
                    "order_id": str(doc["_id"]),
                    "user_id": doc.get("user_id"),
                    "total_amount": doc.get("total_amount"),
                    "status": doc.get("status"),
                    "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                    "updated_at": doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
                    "shipping_address": doc.get("shipping_address"),
                    "billing_address": doc.get("billing_address"),
                    "payment_method": doc.get("payment_method"),
                    "tracking_number": doc.get("tracking_number"),
                    "notes": doc.get("notes"),
                    "items": []
                }
                
                # Add order items
                for item in doc.get("items", []):
                    order_dict["items"].append({
                        "product_id": item.get("product_id"),
                        "name": item.get("name"),
                        "price": item.get("price"),
                        "quantity": item.get("quantity"),
                        "image_url": item.get("image_url"),
                        "category": item.get("category")
                    })
                
                orders.append(order_dict)
            
            logger.info(f"Retrieved {len(orders)} orders for graph API")
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders for graph API: {e}")
            return []
