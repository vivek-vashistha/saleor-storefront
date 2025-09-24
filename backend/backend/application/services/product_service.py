import asyncio
import logging
from collections import defaultdict

from backend.domain.entities import Product, ProductBundle, SearchQuery
from backend.infrastructure.repositories import IProductRepository

logger = logging.getLogger("conversational_commerce")


class ProductService:
    """Service for handling product-related functionality."""

    def __init__(self, product_repository: IProductRepository, saleor_service=None, llm=None):
        """Initialize the ProductService with the provided product repository.

        Args:
            product_repository: Product repository for accessing products
            saleor_service: Optional Saleor service for enriching products
            llm: Language model instance for LLM operations
        """
        self.product_repository = product_repository
        self.saleor_service = saleor_service
        self.llm = llm

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

            logger.info(f"Created {len(bundles)} product bundles with total products: {sum(len(bundle.products) for bundle in bundles)}")
            return bundles

        except Exception as e:
            logger.error(f"Error creating product bundles: {e}")
            return []

    async def get_intelligent_product_bundles(
        self, search_queries: list[SearchQuery], user_profile=None, max_bundles: int = 3
    ) -> list[ProductBundle]:
        """Create intelligent product bundles based on user intent and needs.
        
        Args:
            search_queries: List of search queries
            user_profile: User profile with preferences and budget
            max_bundles: Maximum number of bundles to create
            
        Returns:
            List of intelligent ProductBundle objects
        """
        if not search_queries:
            return []

        try:
            logger.info(f"Creating intelligent product bundles for {len(search_queries)} search queries")
            
            # Get products for each search query
            all_products = []
            for i, search_query in enumerate(search_queries):
                logger.info(f"Processing search query {i+1}/{len(search_queries)}: '{search_query.query}'")
                products = await self.get_products_for_query(search_query, max_num_results=5)
                all_products.extend(products)
                logger.info(f"Added {len(products)} products from query {i+1}")

            if not all_products:
                logger.warning("No products found for intelligent bundling")
                return []

            # Remove duplicates
            unique_products = []
            seen_product_ids = set()
            for product in all_products:
                if product.product_id not in seen_product_ids:
                    unique_products.append(product)
                    seen_product_ids.add(product.product_id)

            logger.info(f"After deduplication: {len(unique_products)} unique products")

            # Create intelligent bundles based on user needs
            bundles = await self._create_intelligent_bundles(unique_products, user_profile, max_bundles)
            
            logger.info(f"Created {len(bundles)} intelligent product bundles")
            return bundles

        except Exception as e:
            logger.error(f"Error creating intelligent product bundles: {e}")
            return []

    async def _create_intelligent_bundles(self, products: list[Product], user_profile=None, max_bundles: int = 3) -> list[ProductBundle]:
        """Create intelligent bundles using LLM to understand product relationships and user needs.
        
        Args:
            products: List of unique products
            user_profile: User profile with preferences and budget
            max_bundles: Maximum number of bundles to create
            
        Returns:
            List of intelligent ProductBundle objects
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            from pydantic import BaseModel, Field
            
            # Define the bundle structure
            class ProductBundleSuggestion(BaseModel):
                bundle_name: str = Field(description="Name of the bundle")
                description: str = Field(description="Description of what this bundle provides")
                product_ids: list[int] = Field(description="List of product IDs to include in this bundle")
                reasoning: str = Field(description="Why these products work well together")
            
            class BundleSuggestions(BaseModel):
                bundles: list[ProductBundleSuggestion] = Field(description="List of suggested bundles")
            
            # Prepare product information for LLM
            product_info = []
            for product in products:
                product_info.append({
                    "id": product.product_id,
                    "name": product.name,
                    "category": product.category,
                    "price": product.price,
                    "description": product.description,
                    "best_for": product.best_for
                })
            
            # Get user context
            user_context = ""
            if user_profile:
                if user_profile.budget_range:
                    user_context += f"Budget: {user_profile.budget_range}\n"
                if user_profile.health_conditions:
                    user_context += f"Health conditions: {', '.join(user_profile.health_conditions)}\n"
                if user_profile.product_preferences:
                    user_context += f"Product preferences: {', '.join(user_profile.product_preferences)}\n"
                if user_profile.activity_preferences:
                    user_context += f"Activity preferences: {', '.join(user_profile.activity_preferences)}\n"
            
            # Create the prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert e-commerce assistant that creates intelligent product bundles.

Your task is to analyze the available products and create meaningful bundles that:
1. Work well together functionally
2. Respect the user's budget and preferences
3. Provide complete solutions for specific needs
4. Offer good value and complementarity

Create bundles that make sense for the user's needs, not just random groupings.
Consider product categories, functionality, and user preferences.

Respond with JSON format containing up to {max_bundles} bundle suggestions. Use this EXACT structure:

{{
  "bundles": [
    {{
      "bundle_name": "Bundle Name Here",
      "description": "Bundle description here",
      "product_ids": [1, 2, 3]
    }}
  ]
}}

IMPORTANT: Use "bundles" as the key, not "bundle_suggestions" or any other key name."""),
                ("human", """Available Products:
{product_info}

User Profile:
{user_context}

Create intelligent product bundles that work well together and meet the user's needs.""")
            ])
            
            # Use the injected LLM instance or create a new one with proper API key
            if self.llm:
                llm = self.llm
            else:
                # Fallback: try to get API key from environment
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)
            
            parser = JsonOutputParser(pydantic_object=BundleSuggestions)
            
            # Create the chain
            chain = prompt | llm | parser
            
            # Get the result
            result = await chain.ainvoke({
                "product_info": product_info,
                "user_context": user_context,
                "max_bundles": max_bundles
            })
            
            # Convert LLM suggestions to ProductBundle objects
            bundles = []

            # Support both dict and Pydantic outputs from the parser
            try:
                if hasattr(result, "bundles"):
                    suggestions = result.bundles  # Pydantic model instance
                elif isinstance(result, dict):
                    suggestions = result.get("bundles")
                    # Be defensive about alternate keys or nesting
                    if suggestions is None:
                        alt = result.get("bundle_suggestions") or result.get("suggestions")
                        if isinstance(alt, dict):
                            suggestions = alt.get("bundles")
                        elif isinstance(alt, list):
                            suggestions = alt
                else:
                    suggestions = None
            except Exception as parse_err:
                logger.error(f"Unexpected format from LLM parser: {parse_err}")
                suggestions = None

            if not suggestions:
                logger.warning("LLM returned no 'bundles' data; falling back to simple bundling")
                return self._create_fallback_bundles(products, max_bundles)

            for suggestion in suggestions:
                # Extract product_ids defensively from dict or Pydantic object
                if isinstance(suggestion, dict):
                    product_ids = suggestion.get("product_ids", [])
                    bundle_name = suggestion.get("bundle_name", "")
                else:
                    product_ids = getattr(suggestion, "product_ids", [])
                    bundle_name = getattr(suggestion, "bundle_name", "")

                # Find the actual products by ID
                bundle_products = []
                for product_id in product_ids:
                    for product in products:
                        if product.product_id == product_id:
                            bundle_products.append(product)
                            break

                if bundle_products:  # Only create bundle if we found the products
                    bundle = ProductBundle(
                        products=bundle_products,
                        bundle_id=f"llm_bundle_{len(bundles) + 1}"
                    )
                    bundles.append(bundle)
                    logger.info(f"Created LLM bundle: {bundle_name} with {len(bundle_products)} products")
            
            logger.info(f"Created {len(bundles)} LLM-based intelligent bundles")
            return bundles[:max_bundles]
            
        except Exception as e:
            logger.error(f"Error in LLM bundle creation: {e}")
            # Fallback to simple category-based bundling
            return self._create_fallback_bundles(products, max_bundles)

    def _create_budget_based_bundles(self, products: list[Product], user_profile, max_bundles: int) -> list[ProductBundle]:
        """Create bundles that respect user's budget constraints."""
        bundles = []
        
        # Parse budget range (simple implementation)
        budget_text = user_profile.budget_range.lower()
        max_budget = None
        
        if 'under' in budget_text:
            try:
                max_budget = float(budget_text.split('under')[1].replace('$', '').strip())
            except:
                pass
        
        if max_budget:
            # Create bundles within budget
            sorted_products = sorted(products, key=lambda p: p.price)
            current_bundle = []
            current_total = 0
            
            for product in sorted_products:
                if current_total + product.price <= max_budget:
                    current_bundle.append(product)
                    current_total += product.price
                else:
                    if current_bundle:
                        bundle = ProductBundle(
                            products=current_bundle,
                            bundle_id=f"budget_bundle_{len(bundles) + 1}",
                            description=f"Complete solution within ${max_budget:.2f} budget (Total: ${current_total:.2f})"
                        )
                        bundles.append(bundle)
                    current_bundle = [product]
                    current_total = product.price
            
            # Add final bundle if it exists
            if current_bundle:
                bundle = ProductBundle(
                    products=current_bundle,
                    bundle_id=f"budget_bundle_{len(bundles) + 1}",
                    description=f"Complete solution within ${max_budget:.2f} budget (Total: ${current_total:.2f})"
                )
                bundles.append(bundle)
        
        return bundles

    def _create_complementary_bundles(self, products_by_category: dict, max_bundles: int) -> list[ProductBundle]:
        """Create bundles with complementary products from different categories."""
        bundles = []
        
        # Find complementary category combinations
        complementary_combinations = [
            (['sleep', 'supplements'], 'Sleep Support Bundle'),
            (['fitness', 'nutrition'], 'Fitness & Nutrition Bundle'),
            (['outdoor', 'gear'], 'Outdoor Adventure Bundle'),
        ]
        
        for categories, description in complementary_combinations:
            bundle_products = []
            for category in categories:
                if category in products_by_category:
                    # Take the best product from each category
                    best_product = max(products_by_category[category], key=lambda p: p.review_score)
                    bundle_products.append(best_product)
            
            if len(bundle_products) >= 2:  # Need at least 2 products for a bundle
                bundle = ProductBundle(
                    products=bundle_products,
                    bundle_id=f"complementary_{len(bundles) + 1}",
                    description=description
                )
                bundles.append(bundle)
        
        return bundles

    def _create_category_specific_bundles(self, products_by_category: dict, max_bundles: int) -> list[ProductBundle]:
        """Create bundles with multiple products from the same category for comprehensive solutions."""
        bundles = []
        
        for category, products in products_by_category.items():
            if len(products) >= 2:  # Need at least 2 products for a bundle
                # Sort by review score and take top products
                sorted_products = sorted(products, key=lambda p: p.review_score, reverse=True)
                bundle_products = sorted_products[:3]  # Take top 3 products
                
                bundle = ProductBundle(
                    products=bundle_products,
                    bundle_id=f"category_{category}_{len(bundles) + 1}",
                    description=f"Complete {category.title()} Solution - Multiple Options"
                )
                bundles.append(bundle)
        
        return bundles

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

    def _create_fallback_bundles(self, products: list[Product], max_bundles: int) -> list[ProductBundle]:
        """Fallback method to create simple category-based bundles when LLM fails."""
        from collections import defaultdict
        
        # Group products by category
        products_by_category = defaultdict(list)
        for product in products:
            products_by_category[product.category].append(product)

        bundles = []
        
        # Create simple category-based bundles
        for category, category_products in products_by_category.items():
            if len(category_products) >= 2:  # Need at least 2 products for a bundle
                # Sort by review score and take top products
                sorted_products = sorted(category_products, key=lambda p: p.review_score, reverse=True)
                bundle_products = sorted_products[:3]  # Take top 3 products
                
                bundle = ProductBundle(
                    products=bundle_products,
                    bundle_id=f"fallback_{category}_{len(bundles) + 1}",
                    description=f"Complete {category.title()} Solution - Multiple Options"
                )
                bundles.append(bundle)
        
        return bundles[:max_bundles]
