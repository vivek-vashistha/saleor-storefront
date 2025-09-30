from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Any


# class Product(BaseModel):
#     """Represents a product recommendation."""

#     product_id: int
#     name: str
#     price: float
#     category: str
#     description: str
#     review_score: float
#     best_for: list[str]
#     image_url: str
#     breadcrumbs: list[str] = Field(default_factory=list)
#     embedding: Optional[List[float]] = None
    
#     # Allow additional fields for enrichment
#     model_config = {"extra": "allow"}

class Product(BaseModel):
    """
    A single CSV row → what we need to upsert Product, Variant, Category(3 levels),
    and AttrValues. (No price here—you'll fetch from Saleor.)
    """

    # IDs
    product_id: str                     # = saleor_product_id
    variant_id: str                     # = saleor_variant_id

    # Product core
    name: str
    brand: str | None = None
    url: str | None = None
    slug: str | None = None
    image_url: str | None = None

    # 3-level category (leaf is Category)
    main_category: str | None = None
    main_category_slug: str | None = None
    sub_category: str | None = None
    sub_category_slug: str | None = None
    category_name: str | None = None
    category_slug: str | None = None

    # Attributes (stored as AttrValues on Variant)
    review_score: float | None = None
    review_count: int | None = None
    product_type_name: str | None = None
    product_type_slug: str | None = None
    tax_class: str | None = None
    collections: str | None = None
    breadcrumbs: List[str] = Field(default_factory=list)
    short_description: str | None = None
    description_text: str | None = None
    best_for: List[str] = Field(default_factory=list)

    # Optional vector for future search (unchanged behavior if missing)
    embedding: Optional[List[float]] = None

    # allow extra for forward compatibility
    model_config = {"extra": "allow"}

    # Backward-compatible fields expected by frontend
    @computed_field
    def description(self) -> Optional[str]:
        return self.description_text

    @computed_field
    def category(self) -> Optional[str]:
        return self.category_name or self.category_slug
