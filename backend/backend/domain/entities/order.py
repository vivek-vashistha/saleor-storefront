from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class OrderStatus(str, Enum):
    """Enum for order status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class OrderItem(BaseModel):
    """Represents an item in an order."""
    
    product_id: int
    name: str
    price: float
    quantity: int
    image_url: str
    category: str


class Order(BaseModel):
    """Represents a customer order."""
    
    order_id: str
    user_id: str
    items: List[OrderItem] = Field(default_factory=list)
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    payment_method: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def item_count(self) -> int:
        """Get the total number of items in the order."""
        return sum(item.quantity for item in self.items)
    
    @property
    def is_active(self) -> bool:
        """Check if the order is in an active state."""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED]
