"""Product-related tools for Deep Agents."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.application.services.product_service import ProductService
from backend.application.services.hybrid_memory_service import HybridMemoryService

logger = logging.getLogger("conversational_commerce.product_tools")


class ProductTools:
    """Product-related tools for Deep Agents."""

    def __init__(self, product_service: ProductService, memory_service: HybridMemoryService):
        """Initialize product tools.

        Args:
            product_service: Product service for operations
            memory_service: Memory service for user context
        """
        self.product_service = product_service
        self.memory_service = memory_service

    async def search_products_tool(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Enhanced product search with memory context.

        Args:
            query: The search query
            categories: Optional product categories
            user_id: The user's ID for personalization
            memories: Retrieved memories for context
            limit: Maximum number of products to return

        Returns:
            Dictionary with search results and context
        """
        try:
            logger.info(f"Searching products: {query[:50]}...")
            
            # Use memory to enhance search if available
            if user_id and not memories:
                memories = await self.memory_service.search_memories(
                    user_id=user_id,
                    query=query,
                    memory_type="product_preference",
                    limit=3
                )
            
            # Generate search queries with memory context
            search_queries = await self._generate_search_queries_with_memory(
                query, categories, memories or []
            )
            
            # Execute search using product service
            products = await self.product_service.search_products(
                query=search_queries[0] if search_queries else query,
                categories=categories,
                limit=limit
            )
            
            logger.info(f"Found {len(products)} products for query: {query}")
            
            return {
                "products": products,
                "search_queries": search_queries,
                "memory_context": memories or [],
                "query": query,
                "categories": categories
            }
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return {
                "products": [],
                "search_queries": [],
                "memory_context": memories or [],
                "query": query,
                "categories": categories,
                "error": str(e)
            }

    async def get_product_details_tool(
        self,
        product_id: str,
        user_id: Optional[str] = None,
        memories: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Get detailed product information.

        Args:
            product_id: The product ID
            user_id: The user's ID for personalization
            memories: Retrieved memories for context

        Returns:
            Dictionary with product details
        """
        try:
            logger.info(f"Getting product details for product {product_id}")
            
            # Get product details from service
            product = await self.product_service.get_product_by_id(product_id)
            
            if not product:
                return {
                    "product": None,
                    "error": "Product not found",
                    "product_id": product_id
                }
            
            # Enhance with memory context if available
            personalized_info = {}
            if user_id and memories:
                personalized_info = await self._get_personalized_product_info(
                    product, memories
                )
            
            logger.info(f"Retrieved product details for product {product_id}")
            
            return {
                "product": product,
                "personalized_info": personalized_info,
                "product_id": product_id,
                "memory_context": memories or []
            }
            
        except Exception as e:
            logger.error(f"Error getting product details for product {product_id}: {e}")
            return {
                "product": None,
                "error": str(e),
                "product_id": product_id
            }

    async def create_product_bundles_tool(
        self,
        products: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
        max_bundles: int = 3
    ) -> Dict[str, Any]:
        """Create intelligent product bundles using memory context.

        Args:
            products: List of products to bundle
            user_id: The user's ID for personalization
            memories: Retrieved memories for context
            max_bundles: Maximum number of bundles to create

        Returns:
            Dictionary with product bundles
        """
        try:
            logger.info(f"Creating product bundles for {len(products)} products")
            
            # Create intelligent bundles using product service
            bundles = await self.product_service.get_intelligent_product_bundles(
                search_queries=[],  # We already have products
                user_profile=None,  # Would need to get from memories
                max_bundles=max_bundles
            )
            
            # Enhance bundles with memory context if available
            if user_id and memories:
                bundles = await self._enhance_bundles_with_memory(
                    bundles, memories
                )
            
            logger.info(f"Created {len(bundles)} product bundles")
            
            return {
                "bundles": bundles,
                "count": len(bundles),
                "memory_context": memories or [],
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error creating product bundles: {e}")
            return {
                "bundles": [],
                "count": 0,
                "error": str(e),
                "memory_context": memories or []
            }

    async def check_availability_tool(
        self,
        product_id: str,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Check product availability.

        Args:
            product_id: The product ID
            quantity: Quantity to check

        Returns:
            Dictionary with availability information
        """
        try:
            logger.info(f"Checking availability for product {product_id}, quantity {quantity}")
            
            # Check availability using product service
            availability = await self.product_service.check_product_availability(
                product_id, quantity
            )
            
            logger.info(f"Availability check for product {product_id}: {availability}")
            
            return {
                "available": availability.get("available", False),
                "quantity_available": availability.get("quantity", 0),
                "product_id": product_id,
                "requested_quantity": quantity
            }
            
        except Exception as e:
            logger.error(f"Error checking availability for product {product_id}: {e}")
            return {
                "available": False,
                "quantity_available": 0,
                "product_id": product_id,
                "requested_quantity": quantity,
                "error": str(e)
            }

    async def _generate_search_queries_with_memory(
        self,
        query: str,
        categories: Optional[List[str]],
        memories: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate search queries using memory context.

        Args:
            query: The original query
            categories: Product categories
            memories: Retrieved memories

        Returns:
            List of enhanced search queries
        """
        try:
            # Extract relevant information from memories
            preferences = []
            health_conditions = []
            
            for memory in memories:
                content = memory.get("content", "")
                if "preference" in content.lower():
                    preferences.append(content)
                elif "health" in content.lower() or "condition" in content.lower():
                    health_conditions.append(content)
            
            # Generate enhanced queries
            enhanced_queries = [query]
            
            # Add preference-based queries
            if preferences:
                for pref in preferences[:2]:  # Limit to 2 preferences
                    enhanced_queries.append(f"{query} {pref}")
            
            # Add health-based queries
            if health_conditions:
                for condition in health_conditions[:2]:  # Limit to 2 conditions
                    enhanced_queries.append(f"{query} for {condition}")
            
            return enhanced_queries[:3]  # Limit to 3 queries
            
        except Exception as e:
            logger.error(f"Error generating search queries with memory: {e}")
            return [query]

    async def _get_personalized_product_info(
        self,
        product: Dict[str, Any],
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get personalized product information based on memories.

        Args:
            product: The product information
            memories: Retrieved memories

        Returns:
            Dictionary with personalized information
        """
        try:
            personalized_info = {
                "recommended": False,
                "reason": "",
                "personalized_notes": []
            }
            
            # Analyze memories for personalization
            for memory in memories:
                content = memory.get("content", "").lower()
                
                # Check for product preferences
                if any(keyword in content for keyword in ["prefer", "like", "favorite"]):
                    if any(keyword in product.get("name", "").lower() for keyword in content.split()):
                        personalized_info["recommended"] = True
                        personalized_info["reason"] = "Matches your preferences"
                        personalized_info["personalized_notes"].append("Based on your preferences")
                
                # Check for health conditions
                if any(keyword in content for keyword in ["health", "condition", "medication"]):
                    if any(keyword in product.get("description", "").lower() for keyword in content.split()):
                        personalized_info["personalized_notes"].append("May help with your health goals")
            
            return personalized_info
            
        except Exception as e:
            logger.error(f"Error getting personalized product info: {e}")
            return {"recommended": False, "reason": "", "personalized_notes": []}

    async def _enhance_bundles_with_memory(
        self,
        bundles: List[Dict[str, Any]],
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance bundles with memory context.

        Args:
            bundles: List of product bundles
            memories: Retrieved memories

        Returns:
            Enhanced bundles with memory context
        """
        try:
            enhanced_bundles = []
            
            for bundle in bundles:
                enhanced_bundle = bundle.copy()
                
                # Add memory-based recommendations
                enhanced_bundle["memory_enhanced"] = True
                enhanced_bundle["personalization_notes"] = []
                
                # Analyze memories for bundle personalization
                for memory in memories:
                    content = memory.get("content", "").lower()
                    
                    if "budget" in content:
                        enhanced_bundle["personalization_notes"].append("Fits your budget preferences")
                    
                    if "health" in content:
                        enhanced_bundle["personalization_notes"].append("Supports your health goals")
                
                enhanced_bundles.append(enhanced_bundle)
            
            return enhanced_bundles
            
        except Exception as e:
            logger.error(f"Error enhancing bundles with memory: {e}")
            return bundles
