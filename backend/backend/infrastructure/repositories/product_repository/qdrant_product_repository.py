import logging

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models as qdrant_models
from qdrant_client.grpc import Filter

from backend.domain.entities import Product
from backend.infrastructure.connections import IQdrantConnection
from backend.infrastructure.repositories.product_repository.interface import IProductRepository

logger = logging.getLogger("conversational_commerce")


class QdrantProductRepository(IProductRepository):
    """Repository for product operations using Qdrant vector database."""

    def __init__(self, connection: IQdrantConnection):
        """Initialize the QdrantProductRepository with the provided connection and embedding service.

        Args:
            connection: The Qdrant connection.

        """
        self.connection = connection
        self.collection_name = "products"

    async def insert_products(self, products: list[Product]) -> None:
        """Initialize the product repository from a list of products.

        Args:
            products: List of Product objects.

        """

        async def _operation(store: QdrantVectorStore):
            # Convert products to list of documents
            ids = []
            documents = []

            for product in products:
                product_id = product.product_id
                name = product.name
                category = product.category
                description = product.description
                best_for = product.best_for

                document = Document(
                    page_content=f"""
                    Name:{name}
                    Category:{category}
                    Description:{description}
                    Best For:{', '.join(best_for) if isinstance(best_for, list) else best_for}""".strip(),
                    metadata=product.model_dump(),
                )
                documents.append(document)
                ids.append(product_id)

            store.add_documents(documents=documents, ids=ids)
            logger.info(f"Initialized {len(documents)} products in Qdrant collection {self.collection_name}")
            return len(documents)

        return await self.connection.execute_db_operation(
            _operation, error_message="Failed to initialize products in Qdrant"
        )

    async def get_products_by_query(
        self, query: str, num_results: int = 10, user_id: int | None = None, categories: list[str] | None = None
    ) -> list[Product]:
        """Get products based on a natural language query.

        Args:
            query: Natural language query describing the products to retrieve
            num_results: Number of products to return
            user_id: Optional user ID to filter out products the user has already purchased
            categories: Optional list of product categories to filter by

        Returns:
            List of Product objects

        """

        async def _operation(store: QdrantVectorStore):
            # Create filter if categories are provided
            filter_condition = None
            if categories and len(categories) > 0:
                logger.info(f"Filtering by categories: {categories}")
                filter_condition = qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="metadata.category", match=qdrant_models.MatchAny(any=categories)
                        )
                    ]
                )

            # Perform similarity search with optional filter
            results = await store.asimilarity_search(query=query, k=num_results, filter=filter_condition)
            return [Product.model_validate(product.metadata) for product in results]

        return await self.connection.execute_db_operation(
            _operation, error_message="Failed to fetch products from Qdrant"
        )

    async def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        """Get products by their IDs.

        Args:
            product_ids: List of product IDs to retrieve

        Returns:
            List of Product objects matching the provided IDs
        """
        if not product_ids:
            return []

        async def _operation(store: QdrantVectorStore):
            results = store.get_by_ids(product_ids)

            # Extract products from the documents using their metadata
            products = [Product.model_validate(document.metadata) for document in results]

            logger.info(f"Retrieved {len(products)} products by IDs from Qdrant")
            return products

        return await self.connection.execute_db_operation(
            _operation, error_message="Failed to fetch products by IDs from Qdrant"
        )

    async def delete_all_products(self) -> None:
        """Delete all products from the repository.

        This method removes all product records from the repository.
        """

        async def _operation(store: QdrantVectorStore):
            # Access the underlying client to delete all points in the collection
            client = store.client

            # Delete all points in the collection using filter that matches all points
            client.delete(collection_name=self.collection_name, points_selector=Filter())

            logger.info(f"Deleted all products from Qdrant collection {self.collection_name}")
            return None

        return await self.connection.execute_db_operation(
            _operation, error_message="Failed to delete products from Qdrant"
        )
