"""
API routes for injecting fake memories for testing and development.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject

from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.presentation.api.containers import Container
from backend.presentation.api.schemas.memory import MemoryConsolidationResponse

logger = logging.getLogger("conversational_commerce")

router = APIRouter(prefix="/fake-memories", tags=["fake-memories"])


@router.post("/users/{user_id}/inject")
@inject
async def inject_fake_memories(
    user_id: str,
    num_memories: int = 20,
    memory_types: Optional[List[str]] = None,
    hybrid_memory_service: HybridMemoryService = Depends(
        Provide[Container.application.hybrid_memory_service]
    ),
) -> Dict[str, Any]:
    """Inject fake memories for a specific user.
    
    Args:
        user_id: The user's ID
        num_memories: Number of memories to create (default: 20)
        memory_types: List of memory types to create (optional)
        hybrid_memory_service: The hybrid memory service
        
    Returns:
        Dictionary containing injection results
    """
    try:
        # Default memory types if not specified
        if not memory_types:
            memory_types = ["user_preference", "product_interaction", "conversation_theme", "order_history"]
        
        logger.info(f"Injecting {num_memories} fake memories for user {user_id}")
        
        # Sample data for generating realistic fake memories (based on actual iHerb products)
        sample_products = [
            "NOW Foods, Probiotic-10, 100 Billion, 30 Veg Capsules",
            "California Gold Nutrition, Probiotics with Lactobacillus acidophilus, 25 Billion CFU",
            "Jarrow Formulas, Jarro-Dophilus EPS, 60 Veggie Caps",
            "Doctor's Best, L-Citrulline Powder, 7 oz",
            "Doctor's Best, Pure L-Arginine Powder, 10.6 oz",
            "California Gold Nutrition, Sport, Creatine Monohydrate, 1 lb",
            "ALLMAX, Melatonin, 60 Capsules",
            "Super Nutrition, Stress Support with L-Theanine, Ashwagandha, 60 Veggie Capsules",
            "Swanson, Sleep Essentials, 60 Vegan Capsules",
            "NATURELO, Sleep Formula, 60 Vegetarian Capsules",
            "NOW Foods, CoQ10, 400 mg, 60 Softgels",
            "Life Extension, Vitamin B12, Methylcobalamin, 500 mcg, 100 Vegetarian Lozenges",
            "NutraBio, KSM-66®, Ashwagandha, 60 Capsules",
            "Primaforce, KSM-66, Ashwagandha Root Extract, 600 mg, 60 Capsules",
            "NOW Foods, Ubiquinol CoQH-CF, 50 mg, 60 Softgels",
            "Vital Proteins, Collagen Peptides, Unflavored, 20 oz",
            "California Gold Nutrition, CollagenUP®, Hydrolyzed Marine Collagen Peptides",
            "Sports Research, Marine Collagen, Unflavored, 12 oz"
        ]
        
        sample_health_conditions = [
            "diabetes", "high blood pressure", "arthritis", "depression", "anxiety",
            "heart disease", "osteoporosis", "thyroid issues", "digestive problems"
        ]
        
        sample_dietary_restrictions = [
            "vegetarian", "vegan", "gluten-free", "dairy-free", "keto", "paleo",
            "low-sodium", "diabetic-friendly", "halal", "kosher"
        ]
        
        injected_memories = []
        
        # Create memories based on requested types
        for memory_type in memory_types:
            memories_per_type = num_memories // len(memory_types)
            
            for i in range(memories_per_type):
                memory_content = _generate_fake_memory_content(
                    memory_type, sample_products, sample_health_conditions, sample_dietary_restrictions
                )
                
                try:
                    result = await hybrid_memory_service.store_memory(
                        user_id=user_id,
                        memory_content=memory_content["content"],
                        memory_type=memory_type,
                        session_id=memory_content.get("session_id"),
                        confidence=memory_content.get("confidence", 0.8),
                        importance_score=memory_content.get("importance_score", 0.6),
                        additional_metadata=memory_content.get("metadata", {})
                    )
                except Exception as e:
                    # Fallback: create a simple result without Qdrant
                    logger.warning(f"Hybrid memory service failed, using fallback: {e}")
                    result = {
                        "mongodb_id": f"fallback_{i}_{memory_type}",
                        "qdrant_id": f"fallback_vector_{i}",
                        "memory_type": memory_type,
                        "status": "fallback"
                    }
                injected_memories.append(result)
        
        logger.info(f"Successfully injected {len(injected_memories)} memories for user {user_id}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_memories": len(injected_memories),
            "memory_types": memory_types,
            "injected_memories": injected_memories
        }
        
    except Exception as e:
        logger.error(f"Error injecting fake memories for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error injecting fake memories: {str(e)}"
        )


@router.post("/users/{user_id}/inject-orders")
@inject
async def inject_fake_order_memories(
    user_id: str,
    num_orders: int = 5,
    hybrid_memory_service: HybridMemoryService = Depends(
        Provide[Container.application.hybrid_memory_service]
    ),
) -> Dict[str, Any]:
    """Inject fake order history memories for a specific user.
    
    Args:
        user_id: The user's ID
        num_orders: Number of order memories to create (default: 5)
        hybrid_memory_service: The hybrid memory service
        
    Returns:
        Dictionary containing injection results
    """
    try:
        logger.info(f"Injecting {num_orders} fake order memories for user {user_id}")
        
        sample_products = [
            "NOW Foods, Probiotic-10, 100 Billion, 30 Veg Capsules",
            "California Gold Nutrition, Probiotics with Lactobacillus acidophilus, 25 Billion CFU",
            "Jarrow Formulas, Jarro-Dophilus EPS, 60 Veggie Caps",
            "ALLMAX, Melatonin, 60 Capsules",
            "Swanson, Sleep Essentials, 60 Vegan Capsules",
            "NOW Foods, CoQ10, 400 mg, 60 Softgels",
            "Life Extension, Vitamin B12, Methylcobalamin, 500 mcg, 100 Vegetarian Lozenges",
            "NutraBio, KSM-66®, Ashwagandha, 60 Capsules",
            "Vital Proteins, Collagen Peptides, Unflavored, 20 oz"
        ]
        
        injected_memories = []
        
        for i in range(num_orders):
            # Create realistic order data
            products = sample_products[:3]  # Take first 3 products
            order_date = f"2024-{i+1:02d}-15"  # Different months
            
            order_content = f"User placed an order on {order_date} containing: {', '.join(products)}. Order was delivered successfully and user was satisfied with the quality."
            
            try:
                result = await hybrid_memory_service.store_memory(
                    user_id=user_id,
                    memory_content=order_content,
                    memory_type="order_history",
                    session_id=f"order_session_{i+1}",
                    confidence=0.95,
                    importance_score=0.8,
                    additional_metadata={
                        "order_date": order_date,
                        "products": products,
                        "order_status": "delivered",
                        "satisfaction": "satisfied",
                        "order_value": 75 + (i * 10)
                    }
                )
            except Exception as e:
                logger.warning(f"Hybrid memory service failed for order, using fallback: {e}")
                result = {
                    "mongodb_id": f"fallback_order_{i+1}",
                    "qdrant_id": f"fallback_order_vector_{i+1}",
                    "memory_type": "order_history",
                    "status": "fallback"
                }
            injected_memories.append(result)
        
        logger.info(f"Successfully injected {len(injected_memories)} order memories for user {user_id}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_orders": len(injected_memories),
            "injected_memories": injected_memories
        }
        
    except Exception as e:
        logger.error(f"Error injecting fake order memories for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error injecting fake order memories: {str(e)}"
        )


@router.post("/users/{user_id}/inject-reviews")
@inject
async def inject_fake_review_memories(
    user_id: str,
    num_reviews: int = 5,
    hybrid_memory_service: HybridMemoryService = Depends(
        Provide[Container.application.hybrid_memory_service]
    ),
) -> Dict[str, Any]:
    """Inject fake review memories for a specific user.
    
    Args:
        user_id: The user's ID
        num_reviews: Number of review memories to create (default: 5)
        hybrid_memory_service: The hybrid memory service
        
    Returns:
        Dictionary containing injection results
    """
    try:
        logger.info(f"Injecting {num_reviews} fake review memories for user {user_id}")
        
        sample_products = [
            "NOW Foods, Probiotic-10, 100 Billion, 30 Veg Capsules",
            "California Gold Nutrition, Probiotics with Lactobacillus acidophilus, 25 Billion CFU",
            "Jarrow Formulas, Jarro-Dophilus EPS, 60 Veggie Caps",
            "ALLMAX, Melatonin, 60 Capsules",
            "Swanson, Sleep Essentials, 60 Vegan Capsules",
            "NOW Foods, CoQ10, 400 mg, 60 Softgels",
            "Life Extension, Vitamin B12, Methylcobalamin, 500 mcg, 100 Vegetarian Lozenges",
            "NutraBio, KSM-66®, Ashwagandha, 60 Capsules",
            "Vital Proteins, Collagen Peptides, Unflavored, 20 oz"
        ]
        
        review_templates = [
            "User left a 5-star review for {product}: 'Excellent quality, fast shipping, highly recommend!'",
            "User reviewed {product}: 'Great results after 2 weeks of use, will definitely buy again.'",
            "User gave {product} a positive review: 'Good value for money, works as advertised.'",
            "User wrote a review for {product}: 'Helped with my health goals, very satisfied.'",
            "User left feedback for {product}: 'High quality product, exceeded expectations.'"
        ]
        
        injected_memories = []
        
        for i in range(num_reviews):
            product = sample_products[i % len(sample_products)]
            review_template = review_templates[i % len(review_templates)]
            review_content = review_template.format(product=product)
            
            try:
                result = await hybrid_memory_service.store_memory(
                    user_id=user_id,
                    memory_content=review_content,
                    memory_type="product_interaction",
                    session_id=f"review_session_{i+1}",
                    confidence=0.9,
                    importance_score=0.7,
                    additional_metadata={
                        "product_name": product,
                        "review_rating": 5,
                        "review_type": "positive",
                        "review_date": f"2024-{i+1:02d}-10"
                    }
                )
            except Exception as e:
                logger.warning(f"Hybrid memory service failed for review, using fallback: {e}")
                result = {
                    "mongodb_id": f"fallback_review_{i+1}",
                    "qdrant_id": f"fallback_review_vector_{i+1}",
                    "memory_type": "product_interaction",
                    "status": "fallback"
                }
            injected_memories.append(result)
        
        logger.info(f"Successfully injected {len(injected_memories)} review memories for user {user_id}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_reviews": len(injected_memories),
            "injected_memories": injected_memories
        }
        
    except Exception as e:
        logger.error(f"Error injecting fake review memories for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error injecting fake review memories: {str(e)}"
        )


def _generate_fake_memory_content(
    memory_type: str, 
    sample_products: List[str], 
    sample_health_conditions: List[str], 
    sample_dietary_restrictions: List[str]
) -> Dict[str, Any]:
    """Generate fake memory content based on type."""
    import random
    from datetime import datetime, timedelta
    
    if memory_type == "user_preference":
        health_condition = random.choice(sample_health_conditions)
        dietary_restriction = random.choice(sample_dietary_restrictions)
        content = f"User prefers {dietary_restriction} supplements and is interested in {health_condition} management. Values quality and research-backed products."
        
        return {
            "content": content,
            "session_id": f"pref_session_{random.randint(1000, 9999)}",
            "confidence": 0.8,
            "importance_score": 0.7,
            "metadata": {
                "health_condition": health_condition,
                "dietary_restriction": dietary_restriction,
                "created_date": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            }
        }
    
    elif memory_type == "product_interaction":
        product = random.choice(sample_products)
        interactions = [
            f"User purchased {product} and was satisfied with the results",
            f"User asked about {product} for their health condition",
            f"User compared {product} with other supplements",
            f"User left a positive review for {product}",
            f"User recommended {product} to a friend"
        ]
        content = random.choice(interactions)
        
        return {
            "content": content,
            "session_id": f"interaction_session_{random.randint(1000, 9999)}",
            "confidence": 0.85,
            "importance_score": 0.6,
            "metadata": {
                "product_name": product,
                "interaction_type": "purchase" if "purchased" in content else "inquiry",
                "satisfaction": "positive",
                "created_date": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat()
            }
        }
    
    elif memory_type == "conversation_theme":
        themes = [
            "User is focused on immune system support and prevention",
            "User is interested in natural and organic supplements",
            "User prefers high-quality, research-backed products",
            "User is budget-conscious but values quality",
            "User is interested in personalized supplement recommendations"
        ]
        content = random.choice(themes)
        
        return {
            "content": content,
            "session_id": f"theme_session_{random.randint(1000, 9999)}",
            "confidence": 0.75,
            "importance_score": 0.5,
            "metadata": {
                "theme_category": "preference" if "prefers" in content else "interest",
                "created_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            }
        }
    
    elif memory_type == "order_history":
        products = random.sample(sample_products, random.randint(1, 3))
        order_date = datetime.now() - timedelta(days=random.randint(1, 120))
        content = f"User placed an order on {order_date.strftime('%Y-%m-%d')} containing: {', '.join(products)}. Order was delivered successfully and user was satisfied."
        
        return {
            "content": content,
            "session_id": f"order_session_{random.randint(1000, 9999)}",
            "confidence": 0.95,
            "importance_score": 0.8,
            "metadata": {
                "order_date": order_date.isoformat(),
                "products": products,
                "order_status": "delivered",
                "satisfaction": "satisfied",
                "order_value": random.randint(25, 150)
            }
        }
    
    else:
        # Default fallback
        content = f"User has shown interest in {memory_type} related topics."
        return {
            "content": content,
            "session_id": f"default_session_{random.randint(1000, 9999)}",
            "confidence": 0.7,
            "importance_score": 0.5,
            "metadata": {"created_date": datetime.now().isoformat()}
        }
