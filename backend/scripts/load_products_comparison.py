import asyncio
import csv
import logging
import sys
from pathlib import Path
from typing import Literal

from backend.domain.entities import Product
from backend.infrastructure.connections import Neo4jConfig, Neo4jConnection, QdrantConfig, QdrantConnection
from backend.infrastructure.factories import EmbeddingFactory
from backend.infrastructure.repositories import IProductRepository, Neo4jProductRepository, QdrantProductRepository
from backend.settings import AISettings, Neo4jSettings, QdrantSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("load_products_comparison")


def normalize_string_to_list(string: str) -> list[str]:
    """Convert a string to a list of strings."""
    return [item.strip().lower() for item in string.strip().lower().split() if item.strip()]


def get_qdrant_repository() -> IProductRepository:
    """Create a Qdrant product repository."""
    settings = QdrantSettings()
    api_settings = AISettings()
    collection = "products"

    logger.info(f"Qdrant Host: {settings.QDRANT_HOST}")
    logger.info(f"Qdrant Port: {settings.QDRANT_PORT}")
    logger.info(f"Collection Name: {collection}")

    embeddings_model = EmbeddingFactory.create_embedding_model(
        api_settings.EMBEDDING_MODEL_NAME,
        api_key=api_settings.OPENAI_API_KEY,
    )

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
    return QdrantProductRepository(connection)


def get_neo4j_repository() -> IProductRepository:
    """Create a Neo4j product repository."""
    settings = Neo4jSettings()

    logger.info(f"Neo4j URI: {settings.NEO4J_URI}")
    logger.info(f"Neo4j Database: {settings.NEO4J_DATABASE}")

    config = Neo4jConfig(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE,
        vector_index_name=settings.NEO4J_VECTOR_INDEX_NAME,
        fulltext_index_name=settings.NEO4J_FULLTEXT_INDEX_NAME,
    )

    connection = Neo4jConnection(config)
    return Neo4jProductRepository(connection)


def load_products_from_csv(csv_path: Path) -> list[Product]:
    """Load products from a CSV file."""
    products = []

    with open(csv_path, encoding="latin1") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                product = Product(
                    product_id=int(row["id"]),
                    name=row["name"].strip(),
                    price=float(row["price"].replace(",", "")),
                    category=row["category"].strip().lower(),
                    description=row["description"].strip(),
                    review_score=float(row["review_score"]),
                    best_for=normalize_string_to_list(row["best_for"]),
                    image_url=row["image_url"].strip(),
                    breadcrumbs=normalize_string_to_list(row["breadcrumbs"]),
                )
                products.append(product)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping row due to error: {e}")
                continue

    return products


async def setup_database(db_type: Literal["qdrant", "neo4j", "both"]):
    """Load products into the specified database(s)."""
    products_csv = Path(__file__).parent.parent.joinpath("data/rei_products.csv")

    if not products_csv.exists():
        logger.error(f"Products CSV file not found: {products_csv}")
        sys.exit(1)

    logger.info(f"Loading products from {products_csv}")
    products = load_products_from_csv(products_csv)
    logger.info(f"Loaded {len(products)} products")

    if db_type in ["qdrant", "both"]:
        logger.info("Setting up Qdrant database...")
        qdrant_repo = get_qdrant_repository()
        await qdrant_repo.delete_all_products()
        await qdrant_repo.insert_products(products)
        logger.info("Qdrant database setup completed!")

    if db_type in ["neo4j", "both"]:
        logger.info("Setting up Neo4j database...")
        neo4j_repo = get_neo4j_repository()
        await neo4j_repo.delete_all_products()
        await neo4j_repo.insert_products(products)
        logger.info("Neo4j database setup completed!")

    logger.info("Database setup completed!")


async def compare_search_results(query: str, categories: list[str] | None = None):
    """Compare search results between Qdrant and Neo4j."""
    logger.info(f"Comparing search results for query: '{query}'")
    if categories:
        logger.info(f"Filtering by categories: {categories}")

    # Get repositories
    qdrant_repo = get_qdrant_repository()
    neo4j_repo = get_neo4j_repository()

    # Search in Qdrant
    logger.info("\n--- Qdrant Results ---")
    start_time = asyncio.get_event_loop().time()
    qdrant_results = await qdrant_repo.get_products_by_query(
        query, num_results=5, categories=categories
    )
    qdrant_time = asyncio.get_event_loop().time() - start_time

    logger.info(f"Found {len(qdrant_results)} products in {qdrant_time:.3f}s")
    for product in qdrant_results:
        logger.info(f"- {product.name}: ${product.price} ({product.category})")

    # Search in Neo4j
    logger.info("\n--- Neo4j Results ---")
    start_time = asyncio.get_event_loop().time()
    neo4j_results = await neo4j_repo.get_products_by_query(
        query, num_results=5, categories=categories
    )
    neo4j_time = asyncio.get_event_loop().time() - start_time

    logger.info(f"Found {len(neo4j_results)} products in {neo4j_time:.3f}s")
    for product in neo4j_results:
        logger.info(f"- {product.name}: ${product.price} ({product.category})")

    # Compare results
    logger.info("\n--- Comparison ---")
    logger.info(f"Qdrant: {len(qdrant_results)} products in {qdrant_time:.3f}s")
    logger.info(f"Neo4j: {len(neo4j_results)} products in {neo4j_time:.3f}s")
    
    # Find common products
    qdrant_ids = {p.product_id for p in qdrant_results}
    neo4j_ids = {p.product_id for p in neo4j_results}
    common_ids = qdrant_ids.intersection(neo4j_ids)
    
    logger.info(f"Common products: {len(common_ids)}")
    if common_ids:
        logger.info(f"Common product IDs: {sorted(common_ids)}")


async def run_comparison_tests():
    """Run a series of comparison tests."""
    logger.info("Running comparison tests between Qdrant and Neo4j...")
    
    test_queries = [
        ("comfortable hiking boots", None),
        ("waterproof jackets", ["clothing"]),
        ("tents for camping", ["camping"]),
        ("backpacks for hiking", None),
        ("sleeping bags for cold weather", None),
    ]
    
    for query, categories in test_queries:
        logger.info(f"\n{'='*60}")
        await compare_search_results(query, categories)
        await asyncio.sleep(1)  # Small delay between tests
    
    logger.info(f"\n{'='*60}")
    logger.info("Comparison tests completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load products and compare Qdrant vs Neo4j")
    parser.add_argument(
        "--setup", 
        choices=["qdrant", "neo4j", "both"], 
        default="both",
        help="Which database(s) to set up (default: both)"
    )
    parser.add_argument(
        "--compare", 
        action="store_true",
        help="Run comparison tests after setup"
    )
    parser.add_argument(
        "--query", 
        type=str,
        help="Specific query to test"
    )
    parser.add_argument(
        "--categories", 
        nargs="+",
        help="Categories to filter by"
    )
    
    args = parser.parse_args()
    
    async def main():
        # Setup database(s)
        await setup_database(args.setup)
        
        # Run specific query if provided
        if args.query:
            await compare_search_results(args.query, args.categories)
        
        # Run comparison tests if requested
        elif args.compare:
            await run_comparison_tests()
    
    asyncio.run(main())
