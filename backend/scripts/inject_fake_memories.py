#!/usr/bin/env python3
"""
Script to inject fake memories for testing and development.
This script creates realistic fake memories about past orders, reviews, and user preferences.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.infrastructure.repositories.memory_repository.mongodb_memory_repository import MongoDBMemoryRepository
from backend.infrastructure.repositories.memory_repository.qdrant_memory_repository import QdrantMemoryRepository
from backend.infrastructure.connections.mongodb.connection import MongoDBConnection
from backend.infrastructure.connections.qdrant.connection import QdrantConnection
from backend.settings.mongodb import MongoDBConfig
from backend.settings.qdrant import QdrantConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeMemoryInjector:
    """Injector for creating fake memories for testing."""
    
    def __init__(self, hybrid_memory_service: HybridMemoryService):
        self.hybrid_memory = hybrid_memory_service
        
        # Sample data for generating realistic fake memories (based on actual iHerb products)
        self.sample_products = [
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
        
        self.sample_health_conditions = [
            "diabetes", "high blood pressure", "arthritis", "depression", "anxiety",
            "heart disease", "osteoporosis", "thyroid issues", "digestive problems",
            "sleep disorders", "migraines", "allergies", "asthma", "autoimmune"
        ]
        
        self.sample_dietary_restrictions = [
            "vegetarian", "vegan", "gluten-free", "dairy-free", "keto", "paleo",
            "low-sodium", "diabetic-friendly", "halal", "kosher", "nut-free"
        ]
        
        self.sample_activities = [
            "hiking", "running", "cycling", "swimming", "yoga", "weightlifting",
            "pilates", "dancing", "tennis", "basketball", "soccer", "martial arts"
        ]
        
        self.sample_locations = [
            "California", "New York", "Texas", "Florida", "Washington", "Oregon",
            "Colorado", "Arizona", "Nevada", "Utah", "Montana", "Wyoming"
        ]

    async def inject_user_memories(self, user_id: str, num_memories: int = 20) -> Dict[str, Any]:
        """Inject fake memories for a specific user.
        
        Args:
            user_id: The user ID to inject memories for
            num_memories: Number of memories to create
            
        Returns:
            Dictionary with injection results
        """
        logger.info(f"Injecting {num_memories} fake memories for user {user_id}")
        
        injected_memories = []
        
        try:
            # Create different types of memories
            memory_types = [
                ("user_preference", self._create_preference_memories, 5),
                ("product_interaction", self._create_product_interaction_memories, 8),
                ("conversation_theme", self._create_theme_memories, 4),
                ("order_history", self._create_order_memories, 3)
            ]
            
            for memory_type, create_func, count in memory_types:
                memories = create_func(user_id, count)
                for memory in memories:
                    result = await self.hybrid_memory.store_memory(
                        user_id=user_id,
                        memory_content=memory["content"],
                        memory_type=memory_type,
                        session_id=memory.get("session_id"),
                        confidence=memory.get("confidence", 0.8),
                        importance_score=memory.get("importance_score", 0.6),
                        additional_metadata=memory.get("metadata", {})
                    )
                    injected_memories.append(result)
                    logger.info(f"Created {memory_type} memory: {result['mongodb_id']}")
            
            logger.info(f"Successfully injected {len(injected_memories)} memories for user {user_id}")
            return {
                "status": "success",
                "user_id": user_id,
                "total_memories": len(injected_memories),
                "memory_types": [mt[0] for mt in memory_types],
                "injected_memories": injected_memories
            }
            
        except Exception as e:
            logger.error(f"Error injecting memories for user {user_id}: {e}")
            return {"status": "error", "user_id": user_id, "error": str(e)}

    def _create_preference_memories(self, user_id: str, count: int) -> List[Dict[str, Any]]:
        """Create fake user preference memories."""
        memories = []
        
        for _ in range(count):
            # Random health condition
            health_condition = random.choice(self.sample_health_conditions)
            
            # Random dietary restriction
            dietary_restriction = random.choice(self.sample_dietary_restrictions)
            
            # Random activity preference
            activity = random.choice(self.sample_activities)
            
            # Create preference memory
            preference_content = f"User prefers {dietary_restriction} supplements and is interested in {health_condition} management. Enjoys {activity} and needs products that support this lifestyle."
            
            memories.append({
                "content": preference_content,
                "session_id": f"session_{random.randint(1000, 9999)}",
                "confidence": random.uniform(0.7, 0.9),
                "importance_score": random.uniform(0.5, 0.8),
                "metadata": {
                    "health_condition": health_condition,
                    "dietary_restriction": dietary_restriction,
                    "activity": activity,
                    "created_date": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
                }
            })
        
        return memories

    def _create_product_interaction_memories(self, user_id: str, count: int) -> List[Dict[str, Any]]:
        """Create fake product interaction memories."""
        memories = []
        
        for _ in range(count):
            product = random.choice(self.sample_products)
            
            # Random interaction types
            interaction_types = [
                f"User purchased {product} and was satisfied with the results",
                f"User asked about {product} for their health condition",
                f"User compared {product} with other supplements",
                f"User left a positive review for {product}",
                f"User recommended {product} to a friend",
                f"User had questions about {product} dosage",
                f"User experienced benefits from {product} after 2 weeks"
            ]
            
            interaction = random.choice(interaction_types)
            
            memories.append({
                "content": interaction,
                "session_id": f"session_{random.randint(1000, 9999)}",
                "confidence": random.uniform(0.8, 0.95),
                "importance_score": random.uniform(0.6, 0.9),
                "metadata": {
                    "product_name": product,
                    "interaction_type": "purchase" if "purchased" in interaction else "inquiry",
                    "satisfaction": random.choice(["positive", "neutral", "positive"]),
                    "created_date": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat()
                }
            })
        
        return memories

    def _create_theme_memories(self, user_id: str, count: int) -> List[Dict[str, Any]]:
        """Create fake conversation theme memories."""
        memories = []
        
        themes = [
            "User is focused on immune system support and prevention",
            "User is interested in natural and organic supplements",
            "User prefers high-quality, research-backed products",
            "User is budget-conscious but values quality",
            "User is interested in personalized supplement recommendations",
            "User prefers products with minimal side effects",
            "User is interested in supplements for energy and vitality",
            "User prefers products that are easy to take"
        ]
        
        for _ in range(count):
            theme = random.choice(themes)
            
            memories.append({
                "content": theme,
                "session_id": f"session_{random.randint(1000, 9999)}",
                "confidence": random.uniform(0.7, 0.9),
                "importance_score": random.uniform(0.5, 0.8),
                "metadata": {
                    "theme_category": "preference" if "prefers" in theme else "interest",
                    "created_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                }
            })
        
        return memories

    def _create_order_memories(self, user_id: str, count: int) -> List[Dict[str, Any]]:
        """Create fake order history memories."""
        memories = []
        
        for _ in range(count):
            # Create a realistic order scenario
            products = random.sample(self.sample_products, random.randint(1, 3))
            order_date = datetime.now() - timedelta(days=random.randint(1, 120))
            
            order_content = f"User placed an order on {order_date.strftime('%Y-%m-%d')} containing: {', '.join(products)}. Order was delivered successfully and user was satisfied."
            
            memories.append({
                "content": order_content,
                "session_id": f"session_{random.randint(1000, 9999)}",
                "confidence": 0.95,  # High confidence for order data
                "importance_score": random.uniform(0.7, 0.9),
                "metadata": {
                    "order_date": order_date.isoformat(),
                    "products": products,
                    "order_status": "delivered",
                    "satisfaction": random.choice(["satisfied", "very_satisfied"]),
                    "order_value": random.randint(25, 150)
                }
            })
        
        return memories

    async def create_test_users_with_memories(self, num_users: int = 5) -> Dict[str, Any]:
        """Create multiple test users with fake memories.
        
        Args:
            num_users: Number of test users to create
            
        Returns:
            Dictionary with creation results
        """
        logger.info(f"Creating {num_users} test users with fake memories")
        
        results = []
        
        for i in range(num_users):
            user_id = f"test_user_{i+1}"
            num_memories = random.randint(15, 25)
            
            result = await self.inject_user_memories(user_id, num_memories)
            results.append(result)
            
            logger.info(f"Created user {user_id} with {num_memories} memories")
        
        return {
            "status": "success",
            "total_users": num_users,
            "results": results
        }


async def main():
    """Main function to run the memory injection."""
    try:
        # Initialize connections (you'll need to set up your config)
        mongodb_config = MongoDBConfig(
            uri="mongodb://localhost:27017",
            database="conversational_commerce"
        )
        mongodb_connection = MongoDBConnection(mongodb_config)
        
        qdrant_config = QdrantConfig(
            url="http://localhost:6333",
            api_key=None
        )
        qdrant_connection = QdrantConnection(qdrant_config)
        
        # Initialize repositories
        mongodb_repository = MongoDBMemoryRepository(mongodb_connection)
        qdrant_repository = QdrantMemoryRepository(qdrant_connection)
        
        # Initialize hybrid memory service
        hybrid_memory_service = HybridMemoryService(mongodb_repository, qdrant_repository)
        
        # Initialize injector
        injector = FakeMemoryInjector(hybrid_memory_service)
        
        # Create test users with memories
        result = await injector.create_test_users_with_memories(num_users=3)
        
        logger.info(f"Memory injection completed: {result}")
        
        # Also inject memories for a specific user
        specific_user_result = await injector.inject_user_memories("demo_user_123", 15)
        logger.info(f"Specific user memory injection: {specific_user_result}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
