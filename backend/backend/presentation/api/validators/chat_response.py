from pydantic import BaseModel

from backend.domain.entities import Product


class ChatResponse(BaseModel):
    """Represents a response to a chat query."""

    message: str
    product_recommendations: list[Product] | None = None
