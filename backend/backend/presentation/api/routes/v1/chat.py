from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from backend.application.use_cases import (
    GetProductsFromChatUseCase,
)
from backend.domain.entities import ChatState, ProductBundle
from backend.presentation.api.containers import Container

router = APIRouter()


@router.post("/products", response_model=list[ProductBundle])
@inject
async def chat(
    query: ChatState,
    get_products_from_chat_use_case: GetProductsFromChatUseCase = Depends(
        Provide[Container.application.get_products_from_chat_use_case]
    ),
) -> list[ProductBundle]:
    """Retrieve product bundles based on a chat query.

    Args:
        query: The current chat state containing the conversation history
        get_products_from_chat_use_case: The GetProductsUseCase for retrieving products

    Returns:
        List of ProductBundle objects retrieved from the database based on the conversation query

    """
    _, bundles = await get_products_from_chat_use_case.execute(query)
    return bundles
