"""API version routing configuration."""

from fastapi import APIRouter

from backend.presentation.api.routes.v1 import chat_router, orders_router, session_router

v1_router = APIRouter(prefix="/v1")

# Include all v1 routers with appropriate tags
v1_router.include_router(session_router, tags=["Session"])
v1_router.include_router(chat_router, tags=["Chat"])
v1_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
