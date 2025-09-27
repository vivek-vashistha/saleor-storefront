"""Health-related tools for Deep Agents."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.application.services.hybrid_memory_service import HybridMemoryService

logger = logging.getLogger("conversational_commerce.health_tools")


class HealthTools:
    """Health-related tools for Deep Agents."""

    def __init__(self, memory_service: HybridMemoryService):
        """Initialize health tools.

        Args:
            memory_service: Memory service for user context
        """
        self.memory_service = memory_service

    async def get_health_advice_tool(
        self,
        user_query: str,
        user_id: str,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Provide health advice with full context.

        Args:
            user_query: The user's health query
            user_id: The user's ID
            memories: Retrieved memories for context

        Returns:
            Dictionary with health advice and context
        """
        try:
            logger.info(f"Getting health advice for user {user_id}: {user_query[:50]}...")
            
            # Analyze user's health context from memories
            health_context = await self._analyze_health_context(user_id, memories)
            
            # Generate health advice based on query and context
            advice = await self._generate_health_advice(user_query, health_context)
            
            # Check for potential drug interactions if medications are mentioned
            interactions = []
            if health_context.get("medications"):
                interactions = await self._check_drug_interactions(
                    health_context["medications"],
                    advice.get("supplements", [])
                )
            
            logger.info(f"Generated health advice for user {user_id}")
            
            return {
                "advice": advice,
                "interactions": interactions,
                "health_context": health_context,
                "user_id": user_id,
                "query": user_query
            }
            
        except Exception as e:
            logger.error(f"Error getting health advice for user {user_id}: {e}")
            return {
                "advice": {"message": "I'm sorry, I couldn't process your health inquiry. Please consult a healthcare provider."},
                "interactions": [],
                "health_context": {},
                "user_id": user_id,
                "query": user_query,
                "error": str(e)
            }

    async def check_drug_interactions_tool(
        self,
        medications: List[str],
        supplements: List[str]
    ) -> Dict[str, Any]:
        """Check for drug interactions between medications and supplements.

        Args:
            medications: List of medications
            supplements: List of supplements

        Returns:
            Dictionary with interaction information
        """
        try:
            logger.info(f"Checking drug interactions for {len(medications)} medications and {len(supplements)} supplements")
            
            # Check for known interactions
            interactions = await self._check_drug_interactions(medications, supplements)
            
            logger.info(f"Found {len(interactions)} potential interactions")
            
            return {
                "interactions": interactions,
                "medications": medications,
                "supplements": supplements,
                "interaction_count": len(interactions)
            }
            
        except Exception as e:
            logger.error(f"Error checking drug interactions: {e}")
            return {
                "interactions": [],
                "medications": medications,
                "supplements": supplements,
                "interaction_count": 0,
                "error": str(e)
            }

    async def get_dosage_advice_tool(
        self,
        supplement_name: str,
        user_id: str,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get dosage advice for a supplement.

        Args:
            supplement_name: Name of the supplement
            user_id: The user's ID
            memories: Retrieved memories for context

        Returns:
            Dictionary with dosage advice
        """
        try:
            logger.info(f"Getting dosage advice for {supplement_name} for user {user_id}")
            
            # Analyze user's health context
            health_context = await self._analyze_health_context(user_id, memories)
            
            # Generate dosage advice
            dosage_advice = await self._generate_dosage_advice(
                supplement_name, health_context
            )
            
            logger.info(f"Generated dosage advice for {supplement_name}")
            
            return {
                "dosage_advice": dosage_advice,
                "supplement_name": supplement_name,
                "health_context": health_context,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting dosage advice for {supplement_name}: {e}")
            return {
                "dosage_advice": {"message": "Please consult a healthcare provider for dosage advice."},
                "supplement_name": supplement_name,
                "health_context": {},
                "user_id": user_id,
                "error": str(e)
            }

    async def get_wellness_recommendations_tool(
        self,
        user_id: str,
        memories: List[Dict[str, Any]],
        wellness_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get personalized wellness recommendations.

        Args:
            user_id: The user's ID
            memories: Retrieved memories for context
            wellness_goals: Optional specific wellness goals

        Returns:
            Dictionary with wellness recommendations
        """
        try:
            logger.info(f"Getting wellness recommendations for user {user_id}")
            
            # Analyze user's health context
            health_context = await self._analyze_health_context(user_id, memories)
            
            # Generate wellness recommendations
            recommendations = await self._generate_wellness_recommendations(
                health_context, wellness_goals
            )
            
            logger.info(f"Generated wellness recommendations for user {user_id}")
            
            return {
                "recommendations": recommendations,
                "wellness_goals": wellness_goals,
                "health_context": health_context,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting wellness recommendations for user {user_id}: {e}")
            return {
                "recommendations": [],
                "wellness_goals": wellness_goals,
                "health_context": {},
                "user_id": user_id,
                "error": str(e)
            }

    async def _analyze_health_context(
        self,
        user_id: str,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze health context from memories and user profile.

        Args:
            user_id: The user's ID
            memories: Retrieved memories

        Returns:
            Dictionary with health context
        """
        try:
            health_context = {
                "medications": [],
                "health_conditions": [],
                "allergies": [],
                "dietary_restrictions": [],
                "activity_level": None,
                "age_group": None
            }
            
            # Analyze memories for health information
            for memory in memories:
                content = memory.get("content", "").lower()
                
                # Extract medications
                if "medication" in content or "medicine" in content:
                    # This would need more sophisticated extraction
                    health_context["medications"].append(content)
                
                # Extract health conditions
                if any(keyword in content for keyword in ["condition", "health", "medical", "diagnosis"]):
                    health_context["health_conditions"].append(content)
                
                # Extract allergies
                if "allergy" in content or "allergic" in content:
                    health_context["allergies"].append(content)
                
                # Extract dietary restrictions
                if any(keyword in content for keyword in ["diet", "restriction", "intolerance", "vegetarian", "vegan"]):
                    health_context["dietary_restrictions"].append(content)
                
                # Extract activity level
                if any(keyword in content for keyword in ["active", "exercise", "fitness", "workout"]):
                    health_context["activity_level"] = "active"
                elif any(keyword in content for keyword in ["sedentary", "inactive", "desk"]):
                    health_context["activity_level"] = "sedentary"
            
            return health_context
            
        except Exception as e:
            logger.error(f"Error analyzing health context for user {user_id}: {e}")
            return {
                "medications": [],
                "health_conditions": [],
                "allergies": [],
                "dietary_restrictions": [],
                "activity_level": None,
                "age_group": None
            }

    async def _generate_health_advice(
        self,
        query: str,
        health_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate health advice based on query and context.

        Args:
            query: The user's health query
            health_context: User's health context

        Returns:
            Dictionary with health advice
        """
        try:
            # This would typically use an LLM to generate advice
            # For now, we'll provide a basic structure
            
            advice = {
                "message": f"Based on your query about {query}, here are some general wellness recommendations:",
                "recommendations": [
                    "Always consult with a healthcare provider before starting new supplements",
                    "Consider your current medications and health conditions",
                    "Start with lower doses and monitor your body's response"
                ],
                "supplements": [],
                "warnings": []
            }
            
            # Add context-specific advice
            if health_context.get("medications"):
                advice["warnings"].append("Be aware of potential interactions with your current medications")
            
            if health_context.get("health_conditions"):
                advice["warnings"].append("Consider your existing health conditions when choosing supplements")
            
            return advice
            
        except Exception as e:
            logger.error(f"Error generating health advice: {e}")
            return {
                "message": "Please consult a healthcare provider for personalized advice.",
                "recommendations": [],
                "supplements": [],
                "warnings": []
            }

    async def _check_drug_interactions(
        self,
        medications: List[str],
        supplements: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for drug interactions.

        Args:
            medications: List of medications
            supplements: List of supplements

        Returns:
            List of potential interactions
        """
        try:
            interactions = []
            
            # This would typically use a drug interaction database
            # For now, we'll provide a basic structure
            
            for medication in medications:
                for supplement in supplements:
                    # Basic interaction check (this would be more sophisticated in practice)
                    if any(keyword in supplement.lower() for keyword in ["blood", "pressure", "heart"]):
                        if any(keyword in medication.lower() for keyword in ["blood", "pressure", "heart"]):
                            interactions.append({
                                "medication": medication,
                                "supplement": supplement,
                                "interaction_type": "potential",
                                "severity": "moderate",
                                "description": "Potential interaction between cardiovascular medications and supplements"
                            })
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error checking drug interactions: {e}")
            return []

    async def _generate_dosage_advice(
        self,
        supplement_name: str,
        health_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate dosage advice for a supplement.

        Args:
            supplement_name: Name of the supplement
            health_context: User's health context

        Returns:
            Dictionary with dosage advice
        """
        try:
            dosage_advice = {
                "supplement": supplement_name,
                "general_dosage": "Please consult a healthcare provider for specific dosage recommendations",
                "considerations": [],
                "warnings": []
            }
            
            # Add context-specific considerations
            if health_context.get("medications"):
                dosage_advice["considerations"].append("Consider potential interactions with your current medications")
            
            if health_context.get("health_conditions"):
                dosage_advice["considerations"].append("Your health conditions may affect appropriate dosage")
            
            if health_context.get("age_group"):
                dosage_advice["considerations"].append("Age may affect appropriate dosage")
            
            return dosage_advice
            
        except Exception as e:
            logger.error(f"Error generating dosage advice for {supplement_name}: {e}")
            return {
                "supplement": supplement_name,
                "general_dosage": "Please consult a healthcare provider for dosage advice",
                "considerations": [],
                "warnings": []
            }

    async def _generate_wellness_recommendations(
        self,
        health_context: Dict[str, Any],
        wellness_goals: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Generate wellness recommendations.

        Args:
            health_context: User's health context
            wellness_goals: Optional specific wellness goals

        Returns:
            List of wellness recommendations
        """
        try:
            recommendations = []
            
            # Generate recommendations based on context
            if health_context.get("activity_level") == "sedentary":
                recommendations.append({
                    "category": "exercise",
                    "recommendation": "Consider adding light exercise to your routine",
                    "priority": "high"
                })
            
            if health_context.get("health_conditions"):
                recommendations.append({
                    "category": "health_monitoring",
                    "recommendation": "Regular monitoring of your health conditions is important",
                    "priority": "high"
                })
            
            # Add goal-specific recommendations
            if wellness_goals:
                for goal in wellness_goals:
                    recommendations.append({
                        "category": "goal_specific",
                        "recommendation": f"Focus on {goal} as part of your wellness plan",
                        "priority": "medium"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating wellness recommendations: {e}")
            return []
