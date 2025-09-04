"""This module contains all the routes for the REST API."""

from backend.presentation.api.routes.versions import v1_router
from backend.presentation.api.routes.welcome_router import router as welcome_router

__all__ = ["v1_router", "welcome_router"]
