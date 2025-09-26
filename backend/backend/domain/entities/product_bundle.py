from pydantic import BaseModel, Field

from backend.domain.entities.product import Product


class ProductBundle(BaseModel):
    """Represents a bundle of products from different categories.

    A product bundle is a collection of products across multiple categories,
    where each product in the bundle comes from a different category.

    Attributes:
        products: List of products in the bundle
        bundle_id: Optional identifier for the bundle
        bundle_name: Optional name for the bundle
        description: Optional description of what this bundle provides
        rationale: Optional explanation of why this bundle is recommended
    """

    products: list[Product] = Field(
        default_factory=list, description="List of products in this bundle, each from a different category"
    )
    bundle_id: str | None = Field(default=None, description="Identifier for the bundle")
    bundle_name: str | None = Field(default=None, description="Name of the bundle")
    description: str | None = Field(default=None, description="Description of what this bundle provides")
    rationale: str | None = Field(default=None, description="Explanation of why this bundle is recommended")
