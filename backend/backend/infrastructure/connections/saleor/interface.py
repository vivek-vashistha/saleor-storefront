from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class ISaleorConnection(ABC):
    """Interface for Saleor API connection."""

    @abstractmethod
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details by ID from Saleor.

        Args:
            product_id: The product ID to fetch

        Returns:
            Product details dictionary if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get product details by name from Saleor.

        Args:
            product_name: The product name to search for

        Returns:
            Product details dictionary if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_products_by_ids(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple products by IDs from Saleor.

        Args:
            product_ids: List of product IDs to fetch

        Returns:
            List of product details dictionaries
        """
        pass

    @abstractmethod
    async def get_products_by_names(self, product_names: List[str]) -> List[Dict[str, Any]]:
        """Get multiple products by names from Saleor.

        Args:
            product_names: List of product names to search for

        Returns:
            List of product details dictionaries
        """
        pass

    @abstractmethod
    async def get_products_batch(self, product_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Batch method for fetching multiple products by IDs.

        Args:
            product_ids: List of product IDs to fetch

        Returns:
            Saleor response data if successful, None otherwise
        """
        pass

    @abstractmethod
    async def get_products_batch_simple(self, product_ids: List[str], session_id: str = "product_lookup", use_names: bool = False) -> Optional[Dict[str, Any]]:
        """Simplified batch method that just sends product IDs or names (like test script).

        Args:
            product_ids: List of product IDs or names to fetch
            session_id: Session ID for the request
            use_names: Whether we're using product names (True) or IDs (False)

        Returns:
            Saleor response data if successful, None otherwise
        """
        pass
