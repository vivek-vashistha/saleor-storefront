"""This module contains all the V1 routes for the REST API."""

from backend.presentation.api.routes.v1.chat import router as chat_router
from backend.presentation.api.routes.v1.orders import router as orders_router
from backend.presentation.api.routes.v1.session import router as session_router

__all__ = ["chat_router", "orders_router", "session_router"]
