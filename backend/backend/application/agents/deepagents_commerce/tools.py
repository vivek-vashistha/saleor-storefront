# deepagents_commerce/tools.py
from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool

# --- Import your domain models & services, with fallbacks for local runs ---
try:
    from backend.domain.entities.product import Product
    from backend.domain.entities.product_bundle import ProductBundle
    from backend.domain.entities.search_query import SearchQuery
except Exception:
    # Fallback if running this module alongside your uploaded files
    from product import Product  # type: ignore
    from product_bundle import ProductBundle  # type: ignore
    from search_query import SearchQuery  # type: ignore

try:
    from backend.application.services.product_service import ProductService
except Exception:
    from product_service import ProductService  # type: ignore

try:
    from backend.application.services.order_service import OrderService
except Exception:
    from order_service import OrderService  # type: ignore

try:
    from backend.application.services.semantic_memory_service import SemanticMemoryService
    from backend.application.services.hybrid_memory_service import HybridMemoryService
except Exception:
    from semantic_memory_service import SemanticMemoryService  # type: ignore
    from hybrid_memory_service import HybridMemoryService  # type: ignore

# Services will be injected at runtime
product_service = None
order_service = None
hybrid_memory = None
semantic_memory = None
llm = None

def configure_services(
    product_svc=None,
    order_svc=None, 
    hybrid_mem=None,
    semantic_mem=None,
    llm_model=None
):
    """Configure services for the deep agent tools."""
    global product_service, order_service, hybrid_memory, semantic_memory, llm
    product_service = product_svc
    order_service = order_svc
    hybrid_memory = hybrid_mem
    semantic_memory = semantic_mem
    llm = llm_model

# -------------------------
# TOOL: get user profile + insights (personalization bootstrap)
# -------------------------
@tool("get_user_profile_with_memories", return_direct=False)
def get_user_profile_with_memories(user_id: str, include_semantic_context: bool = True) -> Dict[str, Any]:
    """
    Return structured user profile + consolidated insights + (optionally) recent semantic memories.
    Mirrors HybridMemoryService.get_user_profile_with_memories(...).
    """
    if not hybrid_memory:
        return {"user_id": user_id, "preferences": {}, "health_conditions": [], "budget_range": None}
    
    # Run async function in sync context
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(hybrid_memory.get_user_profile_with_memories(
            user_id=user_id,
            include_semantic_context=include_semantic_context
        ))
    except RuntimeError:
        # If no event loop is running, create a new one
        return asyncio.run(hybrid_memory.get_user_profile_with_memories(
            user_id=user_id,
            include_semantic_context=include_semantic_context
        ))

# -------------------------
# TOOL: memory retrieval & write
# -------------------------
@tool("search_memories", return_direct=False)
def search_memories(user_id: str, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Vector search across user's semantic memories (Qdrant)."""
    if not hybrid_memory:
        return []
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(hybrid_memory.search_memories(user_id=user_id, query=query, limit=limit))
    except RuntimeError:
        return asyncio.run(hybrid_memory.search_memories(user_id=user_id, query=query, limit=limit))

@tool("store_memory", return_direct=False)
def store_memory(
    user_id: str,
    content: str,
    memory_type: str = "preference",
    session_id: Optional[str] = None,
    confidence: float = 0.8,
    importance_score: float = 0.5,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Persist a single memory item via HybridMemoryService."""
    if not hybrid_memory:
        return {"stored": False, "error": "Memory service not available"}
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(hybrid_memory.store_memory(
            user_id=user_id,
            memory_content=content,
            memory_type=memory_type,
            session_id=session_id,
            confidence=confidence,
            importance_score=importance_score,
            additional_metadata=metadata or {}
        ))
    except RuntimeError:
        return asyncio.run(hybrid_memory.store_memory(
            user_id=user_id,
            memory_content=content,
            memory_type=memory_type,
            session_id=session_id,
            confidence=confidence,
            importance_score=importance_score,
            additional_metadata=metadata or {}
        ))

@tool("record_conversation_memory", return_direct=False)
def record_conversation_memory(user_id: str, messages: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
    """
    Analyze a full chat turn and store extracted preferences/themes/interactions via SemanticMemoryService.record_conversation.
    """
    if not semantic_memory:
        return "Memory service not available"
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(semantic_memory.record_conversation(user_id=user_id, messages=messages, context=context))
        return "ok"
    except RuntimeError:
        asyncio.run(semantic_memory.record_conversation(user_id=user_id, messages=messages, context=context))
        return "ok"

# -------------------------
# TOOL: product search & bundling (backed by your ProductService)
# -------------------------
@tool("product_search_for_query", return_direct=False)
def product_search_for_query(query: str, categories: Optional[List[str]] = None, max_num_results: int = 6) -> List[Dict[str, Any]]:
    """
    Search catalog: turns free text + categories into your SearchQuery and returns Product[] as dicts.
    """
    if not product_service:
        return []
    
    import asyncio
    sq = SearchQuery(query=query, categories=categories or [])
    try:
        loop = asyncio.get_event_loop()
        products: List[Product] = loop.run_until_complete(product_service.get_products_for_query(sq, max_num_results=max_num_results))
        return [p.model_dump() for p in products]
    except RuntimeError:
        products: List[Product] = asyncio.run(product_service.get_products_for_query(sq, max_num_results=max_num_results))
        return [p.model_dump() for p in products]

@tool("intelligent_product_bundles", return_direct=False)
def intelligent_product_bundles(
    queries: List[str],
    categories_per_query: Optional[List[List[str]]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
    max_bundles: int = 3
) -> List[Dict[str, Any]]:
    """
    Compose bundles using ProductService.get_intelligent_product_bundles.
    user_profile expects keys like: budget_range, health_conditions, product_preferences, activity_preferences.
    """
    if not product_service:
        return []
    
    import asyncio
    sqs = []
    for i, q in enumerate(queries):
        cats = (categories_per_query[i] if categories_per_query and i < len(categories_per_query) else [])
        sqs.append(SearchQuery(query=q, categories=cats))

    # Create a minimal shape compatible with ProductService's attribute access
    class _ProfileShim:
        def __init__(self, d: Dict[str, Any]):
            self.budget_range = d.get("budget_range")
            self.health_conditions = d.get("health_conditions") or []
            self.product_preferences = d.get("product_preferences") or []
            self.activity_preferences = d.get("activity_preferences") or []

    profile_obj = _ProfileShim(user_profile or {}) if user_profile else None
    try:
        loop = asyncio.get_event_loop()
        bundles: List[ProductBundle] = loop.run_until_complete(product_service.get_intelligent_product_bundles(
            search_queries=sqs, user_profile=profile_obj, max_bundles=max_bundles
        ))
        return [b.model_dump() for b in bundles]
    except RuntimeError:
        bundles: List[ProductBundle] = asyncio.run(product_service.get_intelligent_product_bundles(
            search_queries=sqs, user_profile=profile_obj, max_bundles=max_bundles
        ))
        return [b.model_dump() for b in bundles]

# -------------------------
# TOOL: orders (optional, for reorder/history experiences)
# -------------------------
@tool("get_user_orders", return_direct=False)
def get_user_orders(user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Return user's past orders for personalization / replenishment."""
    if not order_service:
        return []
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        orders = loop.run_until_complete(order_service.get_user_orders(user_id=user_id, limit=limit, offset=offset))
        return [o.model_dump() for o in orders] if orders else []
    except RuntimeError:
        orders = asyncio.run(order_service.get_user_orders(user_id=user_id, limit=limit, offset=offset))
        return [o.model_dump() for o in orders] if orders else []

# -------------------------
# TOOL: final emitter (UI contract)
# -------------------------
@tool("emit_recommendations", return_direct=True)
def emit_recommendations(message: str, bundles: List[Dict[str, Any]], assumptions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Final payload for your UI: concise assistant message plus a list of ProductBundle dicts.
    """
    return {
        "message": message,
        "bundles": bundles,
        "assumptions": assumptions or []
    }
