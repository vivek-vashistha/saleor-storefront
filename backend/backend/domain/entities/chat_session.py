from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.domain.entities.chat import ChatState
from backend.domain.entities.product import Product
from backend.domain.entities.product_bundle import ProductBundle


class ChatSession(BaseModel):
    """Represents a chat session with persistent state."""

    id: str | None = Field(
        default=None,
        description="Unique identifier for the chat session",
    )
    user_id: str = Field(
        description="ID of the user in the conversation",
    )
    state: ChatState = Field(
        default_factory=ChatState,
        description="Current state of the chat conversation",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Time when the session was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Time when the session was last updated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the session",
    )

    def add_message(self, message_content: str, is_human: bool = True) -> None:
        """Add a message to the chat state.

        Args:
            message_content: The content of the message
            is_human: Whether the message is from the human (True) or AI (False)
        """
        self.state.add_message(message_content, is_human)
        self.updated_at = datetime.now()

    def add_ai_message_with_products(self, products: list[Product]) -> None:
        """Add an AI message with product recommendations to the chat state.

        Args:
            products: List of products to recommend with this message
        """
        self.state.add_ai_message_with_products(products)
        self.updated_at = datetime.now()

    def add_ai_message_with_product_bundles(self, bundles: list["ProductBundle"]) -> None:
        """Add an AI message with product bundle recommendations to the chat state.

        Args:
            bundles: List of product bundles to recommend with this message
        """
        self.state.add_ai_message_with_product_bundles(bundles)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert the session to a dictionary for storage.

        Returns:
            A dictionary representation of the session
        """
        session_dict = self.model_dump(exclude={"id"})
        return session_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatSession":
        """Create a ChatSession from a dictionary.

        Args:
            data: Dictionary representation of a ChatSession

        Returns:
            A ChatSession instance
        """
        # Make a copy to avoid modifying the input
        data_copy = data.copy()

        # Extract the ID field if it exists (MongoDB _id)
        _id = data_copy.pop("_id", None)

        if _id:
            data_copy["id"] = str(_id)

        # No need for special message handling since ChatState.model_validate takes care of it
        return cls.model_validate(data_copy)
