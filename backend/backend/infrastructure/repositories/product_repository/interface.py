from abc import ABC, abstractmethod

from backend.domain.entities import Product


class IProductRepository(ABC):
    """Interface for product repository operations."""

    @abstractmethod
    async def insert_products(self, products: list[Product]) -> None:
        """Initialize the product repository from a list of products.

        Args:
            products: List of Product objects.

        """
        pass

    @abstractmethod
    async def get_products_by_query(
        self, query: str, num_results: int = 10, user_id: int | None = None, categories: list[str] | None = None
    ) -> list[Product]:
        """Get products based on a natural language query.

        Args:
            query: Natural language query describing the products to retrieve
            num_results: Number of products to return
            user_id: Optional user ID to filter out products the user has already purchased
            categories: Optional list of product categories to filter by

        Returns:
            List of Product objects

        """
        pass

    @abstractmethod
    async def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        """Get products by their IDs.

        Args:
            product_ids: List of product IDs to retrieve

        Returns:
            List of Product objects matching the provided IDs
        """
        pass

    @abstractmethod
    async def delete_all_products(self) -> None:
        """Delete all products from the repository.

        This method removes all product records from the repository.
        """
        pass
