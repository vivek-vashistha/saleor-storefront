from pydantic import BaseModel, Field
from typing import List, Optional

from backend.domain.entities import ChatSession


class CartSummaryItem(BaseModel):
    """Single cart line summary coming from the frontend."""


    id: Optional[str] = None
    quantity: int = 0
    product_name: str = Field(default="", alias="productName")
    product_slug: str = Field(default="", alias="productSlug")
    variant_id: str = Field(default="", alias="variantId")
    variant_name: str = Field(default="", alias="variantName")
    currency: str = ""
    unit_price: float = Field(default=0.0, alias="unitPrice")
    total_price: float = Field(default=0.0, alias="totalPrice")
    image: Optional[str] = None


class CartSummary(BaseModel):
    """Cart summary payload sent during session initialization."""

    checkout_id: Optional[str] = Field(default=None, alias="checkoutId")
    items: List[CartSummaryItem] = Field(default_factory=list)
    line_count: int = Field(default=0, alias="lineCount")
    currency: str = ""


class ChatMessage(BaseModel):
    """Model for chat message requests."""

    content: str
    user_id: str
    referenced_product_ids: list[int] = Field(default_factory=list)
    cart_summary: Optional[CartSummary] = None


class ChatSessionResponse(BaseModel):
    """Model for chat session responses."""

    id: str
    user_id: str
    messages: list[dict]
    created_at: str
    updated_at: str
    metadata: dict

    @classmethod
    def from_entity(cls, session: ChatSession) -> "ChatSessionResponse":
        """Create a ChatSessionResponse from a ChatSession entity.

        Args:
            session: The ChatSession entity

        Returns:
            A ChatSessionResponse instance
        """
        return cls(
            id=session.id,
            user_id=session.user_id,
            messages=session.state.messages,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            metadata=session.metadata,
        )


class ChatMessageResponse(BaseModel):
    """Model for chat message responses that only returns new messages."""

    id: str
    messages: list[dict]

    @classmethod
    def from_entity(cls, session: ChatSession, message_index: int) -> "ChatMessageResponse":
        """Create a ChatMessageResponse from a ChatSession entity with only new messages.

        Args:
            session: The ChatSession entity
            message_index: The index from which to return messages (inclusive)

        Returns:
            A ChatMessageResponse instance with only the new messages
        """
        return cls(
            id=session.id,
            messages=session.state.messages[message_index:],
        )
