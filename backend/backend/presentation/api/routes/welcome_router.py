"""Welcome router for the API."""


from fastapi import APIRouter

router = APIRouter()


@router.get("/", response_model=dict[str, str])
async def welcome() -> dict[str, str]:
    """Welcome endpoint for the API.

    Returns:
        A welcome message with API information
    """
    return {"message": "Welcome to the Conversational Commerce API", "documentation": "/docs"}
