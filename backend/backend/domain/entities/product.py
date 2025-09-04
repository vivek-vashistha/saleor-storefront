from pydantic import BaseModel, Field
from typing import List, Optional, Any


class Product(BaseModel):
    """Represents a product recommendation."""

    product_id: int
    name: str
    price: float
    category: str
    description: str
    review_score: float
    best_for: list[str]
    image_url: str
    breadcrumbs: list[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    
    # Allow additional fields for enrichment
    model_config = {"extra": "allow"}
