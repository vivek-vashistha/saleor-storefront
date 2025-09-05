"""This module initializes the REST API Server."""

import logging
from logging import config as logging_config

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.presentation.api.containers import Container
from backend.presentation.api.middlewares import ExceptionHandlingMiddleware
from backend.presentation.api.routes import v1_router, welcome_router
from backend.presentation.api.routes.copilot import router as copilot_router
from backend.settings.logging import LoggerSettings


def create_app() -> FastAPI:
    """Creates a FastAPI application with the necessary routes and middleware.

    Returns:
        FastAPI: The FastAPI application instance.

    """
    container = Container()
    container.wire()

    application = FastAPI(
        title="Conversational Commerce API",
        description="API for the conversational commerce application",
        version="1.0.0",
    )

    # Add middlewares
    application.add_middleware(ExceptionHandlingMiddleware)  # type: ignore
    application.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],  # Expose headers for CopilotKit
    )

    application.container = container
    application.include_router(welcome_router, tags=["Welcome"])
    application.include_router(v1_router)
    
    # Include CopilotKit routes at root level (no /v1 prefix)
    application.include_router(copilot_router, tags=["CopilotKit"])

    return application


app = create_app()
logger = logging.getLogger("conversational_commerce")
logging_config.dictConfig(LoggerSettings.get_config())

if __name__ == "__main__":
    uvicorn.run("conversational_commerce_backend.main:app", host="127.0.0.1", port=8000, workers=1, reload=True)
