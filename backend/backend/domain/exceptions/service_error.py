"""Service error exceptions for the conversational commerce application."""

from typing import Any

from fastapi import status
from starlette.responses import JSONResponse


class ServiceError(Exception):
    """Base class for all service errors in the application.

    Attributes:
        status_code (int): HTTP status code to return
        detail (str): Error detail message
        headers (Optional[Dict[str, Any]]): Optional HTTP headers to include in the response
    """

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal Server Error",
        headers: dict[str, Any] | None = None,
    ):
        """Initialize the service error.

        Args:
            status_code (int, optional): HTTP status code. Defaults to 500.
            detail (str, optional): Error detail message. Defaults to "Internal Server Error".
            headers (Optional[Dict[str, Any]], optional): Optional HTTP headers. Defaults to None.
        """
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)

    def get_error_response(self) -> JSONResponse:
        """Get a JSON response for this error.

        Returns:
            JSONResponse: A JSON response with the error details
        """
        return JSONResponse(
            status_code=self.status_code,
            content={"detail": self.detail},
            headers=self.headers,
        )
