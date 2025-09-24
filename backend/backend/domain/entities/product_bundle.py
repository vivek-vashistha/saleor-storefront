from pydantic import BaseModel, Field

from backend.domain.entities.product import Product


class ProductBundle(BaseModel):
    """Represents a bundle of products from different categories.

    A product bundle is a collection of products across multiple categories,
    where each product in the bundle comes from a different category.

    Attributes:
        products: List of products in the bundle
        bundle_id: Optional identifier for the bundle
    """

    products: list[Product] = Field(
        default_factory=list, description="List of products in this bundle, each from a different category"
    )
    bundle_id: str | None = Field(default=None, description="Identifier for the bundle")
