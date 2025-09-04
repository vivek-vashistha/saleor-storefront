import asyncio
import logging
from collections import defaultdict

from backend.domain.entities import Product, ProductBundle, SearchQuery
from backend.infrastructure.repositories import IProductRepository

logger = logging.getLogger("conversational_commerce")


class ProductService:
    """Service for handling product-related functionality."""

    def __init__(self, product_repository: IProductRepository, saleor_service=None):
        """Initialize the ProductService with the provided product repository.

        Args:
            product_repository: Product repository for accessing products
            saleor_service: Optional Saleor service for enriching products
        """
        self.product_repository = product_repository
        self.saleor_service = saleor_service

    async def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        """Get products by their IDs.

        Args:
            product_ids: List of product IDs to retrieve

        Returns:
            List of Product objects matching the provided IDs
        """
        if not product_ids:
            return []

        try:
            # Get the products by their IDs from the repository
            products = await self.product_repository.get_products_by_ids(product_ids)
            
            # Enrich products with Saleor data if service is available
            if self.saleor_service and products:
                logger.info("Enriching products with Saleor data")
                products = await self.saleor_service.enrich_products_with_saleor_data(products)
            
            return products
        except Exception as e:
            logger.error(f"Error getting products by IDs: {e}")
            return []

    async def get_products_for_query(self, search_query: SearchQuery, max_num_results: int = 3) -> list[Product]:
        """Get products for a specific search query.

        Args:
            search_query: Search query to find products for
            max_num_results: Maximum number of results to return

        Returns:
            List of products
        """
        if not search_query:
            return []

        try:
            logger.info(f"Searching for products with query: '{search_query.query}'")
            logger.info(f"Search categories: {search_query.categories}")
            logger.info(f"Max results requested: {max_num_results}")
            
            # Get products for the search query
            products = await self.product_repository.get_products_by_query(
                query=search_query.query,
                categories=search_query.categories,
                num_results=max_num_results,
            )
            
            logger.info(f"Retrieved {len(products)} products for query: '{search_query.query}'")
            
            # Remove duplicates based on product_id
            unique_products = []
            seen_product_ids = set()
            
            for product in products:
                if product.product_id not in seen_product_ids:
                    unique_products.append(product)
                    seen_product_ids.add(product.product_id)
                else:
                    logger.info(f"Removed duplicate product '{product.name}' (ID: {product.product_id})")
            
            logger.info(f"After deduplication: {len(unique_products)} unique products")
            
            # Log detailed product information
            for i, product in enumerate(unique_products):
                logger.info(f"Product {i+1}: ID={product.product_id}, Name='{product.name}', Category='{product.category}', Price=${product.price}")
            
            # Enrich products with Saleor data if service is available
            if self.saleor_service and unique_products:
                logger.info("Enriching products with Saleor data")
                unique_products = await self.saleor_service.enrich_products_with_saleor_data(unique_products)
                logger.info("Product enrichment with Saleor data completed")
            
            return unique_products
        except Exception as e:
            logger.error(f"Error getting products for query '{search_query.query}': {e}")
            return []

    async def get_product_bundles_for_queries(
        self, search_queries: list[SearchQuery], max_num_results: int = 3
    ) -> list[ProductBundle]:
        """Get product bundles for multiple search queries.

        Args:
            search_queries: List of search queries to find products for
            max_num_results: Maximum number of results per query

        Returns:
            List of product bundles
        """
        if not search_queries:
            return []

        try:
            logger.info(f"Creating product bundles for {len(search_queries)} search queries")
            
            # Get products for each search query
            all_products = []
            for i, search_query in enumerate(search_queries):
                logger.info(f"Processing search query {i+1}/{len(search_queries)}: '{search_query.query}'")
                products = await self.get_products_for_query(search_query, max_num_results)
                all_products.extend(products)
                logger.info(f"Added {len(products)} products from query {i+1}")

            # Group products by category and remove duplicates
            products_by_category = defaultdict(list)
            seen_product_ids = set()
            
            for product in all_products:
                # Only add product if we haven't seen it before
                if product.product_id not in seen_product_ids:
                    products_by_category[product.category].append(product)
                    seen_product_ids.add(product.product_id)
                    logger.info(f"Grouped product '{product.name}' into category '{product.category}'")
                else:
                    logger.info(f"Skipped duplicate product '{product.name}' (ID: {product.product_id})")

            # Create product bundles

            # return self.create_product_bundles(products_by_category)
            bundles = []
            for category, products in products_by_category.items():
                if products:
                    bundle = ProductBundle(
                        category=category,
                        products=products[:max_num_results],  # Limit products per bundle
                        description=f"Products for {category}",
                    )
                    bundles.append(bundle)
                    logger.info(f"Created bundle for category '{category}' with {len(products[:max_num_results])} products")

            logger.info(f"Created {len(bundles)} product bundles with total {len(all_products)} products")
            return bundles

        except Exception as e:
            logger.error(f"Error creating product bundles: {e}")
            return []

    def create_product_bundles(self, products_by_category: dict[str, list[Product]]) -> list[ProductBundle]:
        """Create product bundles from products grouped by category.

        Args:
            products_by_category: Dictionary mapping categories to lists of products

        Returns:
            List of ProductBundle objects
        """
        if not products_by_category:
            return []

        # Determine the maximum number of bundles we can create
        max_bundles = max(len(products) for products in products_by_category.values())

        # Create the bundles
        bundles = [ProductBundle(products=[]) for _ in range(max_bundles)]

        for category, products in products_by_category.items():
            for i, product in enumerate(products):
                if i < max_bundles:  # Ensure we don't go out of bounds
                    bundles[i].products.append(product)

        return bundles
