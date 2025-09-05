"""
CopilotKit Actions for Conversational Commerce Backend
These actions provide specific functionality that CopilotKit can use
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from dependency_injector.wiring import Provide, inject

from backend.presentation.api.containers import Container
from backend.application.services import ProductService, OrderGraphService
from backend.domain.entities import Product, ProductBundle, SearchQuery

logger = logging.getLogger("conversational_commerce")

router = APIRouter()


class ProductSearchRequest(BaseModel):
    """Request model for product search action"""
    query: str = Field(description="Search query for products")
    categories: Optional[List[str]] = Field(default=None, description="Product categories to filter by")
    max_results: Optional[int] = Field(default=5, description="Maximum number of results to return")


class ProductSearchResponse(BaseModel):
    """Response model for product search action"""
    products: List[Product]
    total_found: int
    search_query: str


class OrderStatusRequest(BaseModel):
    """Request model for order status action"""
    user_email: str = Field(description="User's email address")
    order_id: Optional[str] = Field(default=None, description="Specific order ID to check")


class OrderStatusResponse(BaseModel):
    """Response model for order status action"""
    orders: List[Dict[str, Any]]
    total_orders: int
    user_email: str


class ProductRecommendationRequest(BaseModel):
    """Request model for product recommendation action"""
    user_preferences: Dict[str, Any] = Field(description="User preferences and profile")
    activity_type: Optional[str] = Field(default=None, description="Type of activity")
    budget_range: Optional[str] = Field(default=None, description="Budget range")


class ProductRecommendationResponse(BaseModel):
    """Response model for product recommendation action"""
    recommendations: List[ProductBundle]
    reasoning: str
    user_profile_used: Dict[str, Any]


@router.post("/actions/search-products", response_model=ProductSearchResponse)
@inject
async def search_products(
    request: ProductSearchRequest,
    product_service: ProductService = Depends(
        Provide[Container.application.product_service]
    ),
) -> ProductSearchResponse:
    """
    CopilotKit action for searching products.
    This allows the copilot to search for products based on user queries.
    """
    try:
        logger.info(f"CopilotKit action: Searching products with query: '{request.query}'")
        
        # Create a search query object
        search_query = SearchQuery(
            query=request.query,
            categories=request.categories or []
        )
        
        # Get products using the product service
        products = await product_service.get_products_for_query(
            search_query=search_query,
            max_num_results=request.max_results
        )
        
        logger.info(f"Found {len(products)} products for query: '{request.query}'")
        
        return ProductSearchResponse(
            products=products,
            total_found=len(products),
            search_query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error in search_products action: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")


@router.post("/actions/check-order-status", response_model=OrderStatusResponse)
@inject
async def check_order_status(
    request: OrderStatusRequest,
    order_graph_service: OrderGraphService = Depends(
        Provide[Container.application.order_graph_service]
    ),
) -> OrderStatusResponse:
    """
    CopilotKit action for checking order status.
    This allows the copilot to check user order status and details.
    """
    try:
        logger.info(f"CopilotKit action: Checking order status for email: '{request.user_email}'")
        
        if not order_graph_service:
            raise HTTPException(status_code=503, detail="Order service not available")
        
        # Get user orders
        orders = await order_graph_service.order_service.get_user_orders(request.user_email)
        
        # Filter by specific order ID if provided
        if request.order_id:
            orders = [order for order in orders if order.order_id == request.order_id]
        
        # Convert orders to dictionary format for response
        order_dicts = []
        for order in orders:
            order_dict = {
                "order_id": order.order_id,
                "status": order.status.value,
                "total_amount": order.total_amount,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "item_count": order.item_count,
                "is_active": order.is_active,
                "items": [
                    {
                        "product_id": item.product_id,
                        "name": item.name,
                        "price": item.price,
                        "quantity": item.quantity,
                        "category": item.category
                    }
                    for item in order.items
                ]
            }
            order_dicts.append(order_dict)
        
        logger.info(f"Found {len(order_dicts)} orders for email: '{request.user_email}'")
        
        return OrderStatusResponse(
            orders=order_dicts,
            total_orders=len(order_dicts),
            user_email=request.user_email
        )
        
    except Exception as e:
        logger.error(f"Error in check_order_status action: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking order status: {str(e)}")


@router.post("/actions/get-product-recommendations", response_model=ProductRecommendationResponse)
@inject
async def get_product_recommendations(
    request: ProductRecommendationRequest,
    product_service: ProductService = Depends(
        Provide[Container.application.product_service]
    ),
) -> ProductRecommendationResponse:
    """
    CopilotKit action for getting personalized product recommendations.
    This allows the copilot to provide tailored product suggestions.
    """
    try:
        logger.info(f"CopilotKit action: Getting product recommendations for user preferences")
        
        # Create search queries based on user preferences
        search_queries = []
        
        # Add activity-based search if specified
        if request.activity_type:
            search_queries.append(SearchQuery(
                query=f"{request.activity_type} gear equipment",
                categories=[]
            ))
        
        # Add budget-based search if specified
        if request.budget_range:
            search_queries.append(SearchQuery(
                query=f"affordable {request.budget_range} outdoor gear",
                categories=[]
            ))
        
        # Add general preferences search
        if request.user_preferences:
            preferences = request.user_preferences.get("activity_preferences", [])
            for preference in preferences[:2]:  # Limit to 2 preferences
                search_queries.append(SearchQuery(
                    query=f"{preference} equipment gear",
                    categories=[]
                ))
        
        # If no specific queries, create a general one
        if not search_queries:
            search_queries.append(SearchQuery(
                query="outdoor gear equipment recommendations",
                categories=[]
            ))
        
        # Get product bundles
        recommendations = await product_service.get_product_bundles_for_queries(
            search_queries=search_queries,
            max_num_results=3
        )
        
        # Generate reasoning
        reasoning_parts = []
        if request.activity_type:
            reasoning_parts.append(f"Based on your interest in {request.activity_type}")
        if request.budget_range:
            reasoning_parts.append(f"considering your {request.budget_range} budget")
        if request.user_preferences.get("activity_preferences"):
            reasoning_parts.append("matching your activity preferences")
        
        reasoning = "These recommendations are " + ", ".join(reasoning_parts) + "."
        
        logger.info(f"Generated {len(recommendations)} product bundles for recommendations")
        
        return ProductRecommendationResponse(
            recommendations=recommendations,
            reasoning=reasoning,
            user_profile_used=request.user_preferences
        )
        
    except Exception as e:
        logger.error(f"Error in get_product_recommendations action: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


@router.get("/actions/available-actions")
async def get_available_actions():
    """
    Get list of available CopilotKit actions.
    This helps the frontend understand what actions are available.
    """
    return {
        "actions": [
            {
                "name": "search_products",
                "description": "Search for products based on a query and optional categories",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Search query for products"},
                    "categories": {"type": "array", "required": False, "description": "Product categories to filter by"},
                    "max_results": {"type": "integer", "required": False, "description": "Maximum number of results"}
                }
            },
            {
                "name": "check_order_status",
                "description": "Check the status and details of user orders",
                "parameters": {
                    "user_email": {"type": "string", "required": True, "description": "User's email address"},
                    "order_id": {"type": "string", "required": False, "description": "Specific order ID to check"}
                }
            },
            {
                "name": "get_product_recommendations",
                "description": "Get personalized product recommendations based on user preferences",
                "parameters": {
                    "user_preferences": {"type": "object", "required": True, "description": "User preferences and profile"},
                    "activity_type": {"type": "string", "required": False, "description": "Type of activity"},
                    "budget_range": {"type": "string", "required": False, "description": "Budget range"}
                }
            }
        ]
    }
