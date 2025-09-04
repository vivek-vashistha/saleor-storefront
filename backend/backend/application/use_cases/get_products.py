import logging

from backend.application.interfaces import IChatWorkflow
from backend.application.services import ProductService
from backend.domain.entities import ChatState, ProductBundle
from backend.infrastructure.repositories import IProductRepository

logger = logging.getLogger("conversational_commerce")


class GetProductsFromChatUseCase:
    """Use case for retrieving products from the database based on conversation."""

    def __init__(
        self,
        product_repository: IProductRepository,
        workflow: IChatWorkflow[ChatState],
        product_service: ProductService,
    ):
        """Initialize the GetProductsUseCase with the provided dependencies.

        Args:
            product_repository: Product repository
            workflow: Chat workflow for processing user queries
            product_service: Service for product-related functionality

        """
        self.product_repository = product_repository
        self.workflow = workflow
        self.product_service = product_service

    async def execute(self, chat_state: ChatState) -> tuple[ChatState, list[ProductBundle]]:
        """Execute the use case to retrieve product bundles based on conversation.

        Args:
            chat_state: The current chat state containing the conversation history

        Returns:
            A tuple of (ChatState, list of ProductBundle objects) where each bundle
            contains products from different categories

        This method is now simplified as the product-related logic is moved to ProductService
        """
        # Process the chat query using the workflow
        updated_state = await self.workflow.run(chat_state)

        # If there are no search queries, return empty list
        if not updated_state.has_search_query:
            return updated_state, []

        # Get product bundles using the ProductService
        bundles = await self.product_service.get_product_bundles_for_queries(updated_state.search_queries)

        return updated_state, bundles

    async def get_products_by_ids(self, product_ids: list[int]):
        """Get products by their IDs.

        Args:
            product_ids: List of product IDs to retrieve

        Returns:
            List of Product objects matching the provided IDs
        """
        return await self.product_service.get_products_by_ids(product_ids)
