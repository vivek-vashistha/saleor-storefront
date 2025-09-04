import logging
import aiohttp
from typing import Dict, List, Optional, Any

from backend.infrastructure.connections.saleor.config import SaleorConfig
from backend.infrastructure.connections.saleor.interface import ISaleorConnection

logger = logging.getLogger("conversational_commerce")


class SaleorConnection(ISaleorConnection):
    """Connection to Saleor API server for fetching product details."""

    def __init__(self, config: SaleorConfig):
        """Initialize the Saleor connection.

        Args:
            config: Saleor configuration settings
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure aiohttp session is available."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make a request to the Saleor API.

        Args:
            endpoint: API endpoint to call
            data: Data to send in the request

        Returns:
            Response data if successful, None otherwise
        """
        try:
            session = await self._ensure_session()
            url = f"{self.config.base_url}/{endpoint}"
            
            logger.info(f"Making request to Saleor API: {url}")
            logger.info(f"Request data: {data}")
            
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully received response from Saleor API: {endpoint}")
                    logger.info(f"Response: {result}")
                    return result
                else:
                    logger.warning(f"Saleor API request failed with status {response.status}: {endpoint}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error making request to Saleor API {endpoint}: {e}")
            return None

    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details by ID from Saleor.

        Args:
            product_id: The product ID to fetch

        Returns:
            Product details dictionary if found, None otherwise
        """
        logger.info(f"Fetching product by ID from Saleor: {product_id}")
        
        # Use the orders endpoint to get product details
        data = {
            "question": f"Get product details for product ID: {product_id}",
            "session_id": "product_lookup",
            "mode": "product_lookup"
        }
        
        result = await self._make_request("orders", data)
        if result and result.get("status") == "Success":
            return result.get("data")
        
        return None

    async def get_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get product details by name from Saleor.

        Args:
            product_name: The product name to search for

        Returns:
            Product details dictionary if found, None otherwise
        """
        logger.info(f"Fetching product by name from Saleor: {product_name}")
        
        # Use the orders endpoint to get product details
        data = {
            "question": f"Get product details for product: {product_name}",
            "session_id": "product_lookup",
            "mode": "product_lookup"
        }
        
        result = await self._make_request("orders", data)
        if result and result.get("status") == "Success":
            return result.get("data")
        
        return None

    async def get_products_by_ids(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple products by IDs from Saleor.

        Args:
            product_ids: List of product IDs to fetch

        Returns:
            List of product details dictionaries
        """
        logger.info(f"Fetching {len(product_ids)} products by IDs from Saleor")
        
        products = []
        for product_id in product_ids:
            product = await self.get_product_by_id(product_id)
            if product:
                products.append(product)
            else:
                logger.warning(f"Failed to fetch product with ID: {product_id}")
        
        logger.info(f"Successfully fetched {len(products)} products from Saleor")
        return products

    async def get_products_by_names(self, product_names: List[str]) -> List[Dict[str, Any]]:
        """Get multiple products by names from Saleor.

        Args:
            product_names: List of product names to search for

        Returns:
            List of product details dictionaries
        """
        logger.info(f"Fetching {len(product_names)} products by names from Saleor")
        
        products = []
        for product_name in product_names:
            product = await self.get_product_by_name(product_name)
            if product:
                products.append(product)
            else:
                logger.warning(f"Failed to fetch product with name: {product_name}")
        
        logger.info(f"Successfully fetched {len(products)} products from Saleor")
        return products

    async def get_products_batch(self, product_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Batch method for fetching multiple products by IDs.

        Args:
            product_ids: List of product IDs to fetch

        Returns:
            Saleor response data if successful, None otherwise
        """
        logger.info(f"Fetching batch details for {len(product_ids)} products")
        
        # Use the orders endpoint with just product IDs (like test script)
        data = {
            "question": f"fetch product data based on the ids",
            "session_id": "product_lookup",
            "kg_products": product_ids  # Send as JSON string like test script
        }
        
        logger.info(f"Sending batch request to Saleor with {len(product_ids)} product IDs: {product_ids}")
        
        result = await self._make_request("orders", data)
        if result and result.get("status") == "Success":
            logger.info(f"Successfully received batch response from Saleor for {len(product_ids)} products")
            return result.get("data")
        
        logger.warning(f"Batch request to Saleor failed for {len(product_ids)} products")
        return None

    async def get_products_batch_simple(self, product_ids: List[str], session_id: str = "product_lookup", use_names: bool = False) -> Optional[Dict[str, Any]]:
        """Simplified batch method that just sends product IDs or names (like test script).

        Args:
            product_ids: List of product IDs or names to fetch
            session_id: Session ID for the request
            use_names: Whether we're using product names (True) or IDs (False)

        Returns:
            Saleor response data if successful, None otherwise
        """
        import json
        logger.info(f"Fetching batch details for {len(product_ids)} products using simplified method")
        
        # Adjust question based on whether we're using IDs or names
        if use_names:
            question = "fetch product data based on the product names"
            logger.info("Using product names for Saleor API call")
        else:
            question = "fetch product data based on the ids"
            logger.info("Using product IDs for Saleor API call")
        
        data = {
            "question": question,
            "session_id": session_id,
            "kg_products": json.dumps(product_ids)  # Send as JSON string like test script
        }
        
        if use_names:
            logger.info(f"Sending simplified batch request to Saleor with {len(product_ids)} product names: {product_ids}")
        else:
            logger.info(f"Sending simplified batch request to Saleor with {len(product_ids)} product IDs: {product_ids}")
        
        result = await self._make_request("orders", data)
        if result and result.get("status") == "Success":
            logger.info(f"Successfully received simplified batch response from Saleor for {len(product_ids)} products")
            return result.get("data")
        
        logger.warning(f"Simplified batch request to Saleor failed for {len(product_ids)} products")
        return None

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Saleor connection session closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
