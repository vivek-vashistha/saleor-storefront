import asyncio
import csv
import logging
import sys
from pathlib import Path

from backend.domain.entities import Product
from backend.infrastructure.connections import QdrantConfig, QdrantConnection
from backend.infrastructure.factories import EmbeddingFactory
from backend.infrastructure.repositories import IProductRepository, QdrantProductRepository
from backend.settings import AISettings, QdrantSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("load_products")


def normalize_string_to_list(string: str) -> list[str]:
    """Convert a string to a list of strings."""
    return [item.strip().lower() for item in string.strip().lower().split() if item.strip()]


def get_repository() -> IProductRepository:
    """Create a Qdrant product repository."""
    # Create settings with environment variables
    settings = QdrantSettings()
    api_settings = AISettings()
    collection = "products"

    # Log the configuration
    logger.info(f"Qdrant Host: {settings.QDRANT_HOST}")
    logger.info(f"Qdrant Port: {settings.QDRANT_PORT}")
    logger.info(f"Collection Name: {collection}")

    embeddings_model = EmbeddingFactory.create_embedding_model(
        api_settings.EMBEDDING_MODEL_NAME,
        api_key=api_settings.OPENAI_API_KEY,
    )

    # Create a Qdrant connection
    config = QdrantConfig(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY,
        collection=collection,
        vector_size=embeddings_model.dimension,
        prefer_grpc=settings.QDRANT_PREFER_GRPC,
        timeout=settings.QDRANT_TIMEOUT,
    )

    connection = QdrantConnection(config, embeddings_model)

    # Create a product repository
    return QdrantProductRepository(connection)


def load_products_from_csv(csv_path: Path) -> list[Product]:
    """Load products from a CSV file.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of dictionaries containing product data
    """
    products = []

    with open(csv_path, encoding="latin1") as file:
        reader = csv.DictReader(file)
        for row in reader:
            product = Product(
                product_id=row["id"],
                name=row["name"].strip(),
                price=float(row["price"].replace(",", "")),
                category=row["category"].strip().lower(),
                description=row["description"].strip(),
                review_score=row["review_score"],
                best_for=normalize_string_to_list(row["best_for"]),
                image_url=row["image_url"].strip(),
                breadcrumbs=normalize_string_to_list(row["breadcrumbs"]),
            )
            products.append(product)

    return products


async def setup_db():
    """Load products into a Qdrant product repository."""
    repository = get_repository()
    await repository.delete_all_products()
    logger.info("Deleted all products from the repository")

    # Get configuration from environment variables or use defaults
    products_csv = Path(__file__).parent.parent.joinpath("data/rei_products.csv")

    logger.info(f"Products CSV: {products_csv}")

    # Check if the products CSV file exists
    if not products_csv.exists():
        logger.error(f"Products CSV file not found: {products_csv}")
        sys.exit(1)

    # Load the products from the CSV file
    logger.info(f"Loading products from {products_csv}")
    products = load_products_from_csv(products_csv)
    logger.info(f"Loaded {len(products)} products")

    # Initialize the repository with the products
    logger.info("Initializing repository with products")
    count = await repository.insert_products(products)
    logger.info(f"Initialized repository with {count} products")

    logger.info("Done!")


async def get_products(query: str, categories: list[str] | None = None):
    """Search for products using a Qdrant product repository.

    Args:
        query: The search query
        categories: Optional list of categories to filter by
    """
    repository = get_repository()

    logger.info(f"Searching for products: {query}")
    if categories:
        logger.info(f"Filtering by categories: {categories}")
        products = await repository.get_products_by_query(query, num_results=2, categories=categories)
    else:
        products = await repository.get_products_by_query(query, num_results=2)

    if not products:
        logger.info("No products found")
        return []

    logger.info(f"Found {len(products)} products")
    logger.info(products)
    return products


if __name__ == "__main__":
    asyncio.run(setup_db())
    # asyncio.run(get_products("Show me tents to camp in yosemite"))
