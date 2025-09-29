import asyncio
import csv
import json
import logging
import sys
from pathlib import Path

from backend.domain.entities import Product
from backend.infrastructure.connections import Neo4jConfig, Neo4jConnection
from backend.infrastructure.repositories import IProductRepository, Neo4jProductRepository
from backend.settings import AISettings, Neo4jSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("load_products_neo4j")

def split_list(s: str) -> list[str]:
    if not s:
        return []
    seps = ["|", ",", ";"]
    parts = [s]
    for sep in seps:
        parts = [p for chunk in parts for p in chunk.split(sep)]
    # strip, dedupe, drop empties
    cleaned = []
    for p in (x.strip() for x in parts):
        if p and p not in cleaned:
            cleaned.append(p)
    return cleaned

# def normalize_string_to_list(string: str) -> list[str]:
#     """Convert a string to a list of strings."""
#     return [item.strip().lower() for item in string.strip().lower().split() if item.strip()]


def get_repository() -> IProductRepository:
    """Create a Neo4j product repository."""
    # Create settings with environment variables
    settings = Neo4jSettings()
    api_settings = AISettings()

    # Log the configuration
    logger.info(f"Neo4j URI: {settings.NEO4J_URI}")
    logger.info(f"Neo4j Database: {settings.NEO4J_DATABASE}")
    logger.info(f"Vector Index: {settings.NEO4J_VECTOR_INDEX_NAME}")
    logger.info(f"Fulltext Index: {settings.NEO4J_FULLTEXT_INDEX_NAME}")

    # Create a Neo4j connection
    config = Neo4jConfig(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE,
        vector_index_name=settings.NEO4J_VECTOR_INDEX_NAME,
        fulltext_index_name=settings.NEO4J_FULLTEXT_INDEX_NAME,
    )

    connection = Neo4jConnection(config)

    # Create a product repository
    return Neo4jProductRepository(connection)


# def load_products_from_csv(csv_path: Path) -> list[Product]:
#     """Load products from a CSV file.

#     Args:
#         csv_path: Path to the CSV file

#     Returns:
#         List of Product objects
#     """
#     products = []

#     with open(csv_path, encoding="latin1") as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             try:
#                 # Parse embedding if it exists
#                 embedding = None
#                 if "embedding" in row and row["embedding"]:
#                     try:
#                         embedding = json.loads(row["embedding"])
#                     except json.JSONDecodeError:
#                         logger.warning(f"Failed to parse embedding for product {row['id']}")
                
#                 product = Product(
#                     product_id=int(row["id"]),
#                     name=row["name"].strip(),
#                     price=float(row["price"].replace(",", "")),
#                     category=row["category"].strip().lower(),
#                     description=row["description"].strip(),
#                     review_score=float(row["review_score"]),
#                     best_for=normalize_string_to_list(row["best_for"]),
#                     image_url=row["image_url"].strip(),
#                     breadcrumbs=normalize_string_to_list(row["breadcrumbs"]),
#                     embedding=embedding,
#                 )
#                 products.append(product)
#             except (ValueError, KeyError) as e:
#                 logger.warning(f"Skipping row due to error: {e}")
#                 continue

#     return products

def load_products_from_csv(csv_path: Path) -> list[Product]:
    products: list[Product] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                embedding = None
                if row.get("embedding"):
                    try:
                        embedding = json.loads(row["embedding"])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse embedding for row with product {row.get('saleor_product_id')}")

                products.append(
                    Product(
                        # IDs
                        product_id=str(row["saleor_product_id"]).strip(),
                        variant_id=str(row["saleor_variant_id"]).strip(),
                        # product core
                        name=row.get("name", "").strip(),
                        brand=row.get("brand", "") or None,
                        url=row.get("url", "") or None,
                        slug=row.get("slug", "") or None,
                        image_url=row.get("image_url", "") or None,
                        # categories (3 levels)
                        main_category=row.get("main_category") or None,
                        main_category_slug=row.get("main_category_slug") or None,
                        sub_category=row.get("sub_category") or None,
                        sub_category_slug=row.get("sub_category_slug") or None,
                        category_name=row.get("category_name") or None,
                        category_slug=row.get("category_slug") or None,
                        # attrs
                        review_score=float(row["review_score"]) if row.get("review_score") else None,
                        review_count=int(row["review_count"]) if row.get("review_count") else None,
                        product_type_name=row.get("product_type_name") or None,
                        product_type_slug=row.get("product_type_slug") or None,
                        tax_class=row.get("tax_class") or None,
                        collections=row.get("collections") or None,
                        breadcrumbs=split_list(row.get("breadcrumbs", "")),
                        short_description=row.get("short_description") or None,
                        description_text=row.get("description_text") or None,
                        best_for=[b.lower() for b in split_list(row.get("best_for", ""))],
                        embedding=embedding,
                    )
                )
            except Exception as e:
                logger.warning(f"Skipping row due to error: {e}")
                continue
    # from pprint import pprint
    # pprint(products)
    return products

async def setup_db():
    """Load products into a Neo4j product repository with enhanced graph relationships."""
    repository = get_repository()
    
    # Clear existing products and all related nodes
    await repository.delete_all_products()
    logger.info("Deleted all products and related nodes from the Neo4j repository")

    # Get configuration from environment variables or use defaults
    # products_csv = Path(__file__).parent.parent.joinpath("data/rei_products.csv")

    # 👉 point to your iHerb CSV
    products_csv = Path(__file__).parent.parent.joinpath(
        # "data/iherb_product_data - for_Neo4j_push_v3_with_saleor_ID.csv"
        "data/iherb_data_for_neo4j/iherb_product_data - for_Neo4j_push_v3_with_saleor_ID.csv"
    )

    logger.info(f"Products CSV: {products_csv}")

    # Check if the products CSV file exists
    if not products_csv.exists():
        logger.error(f"Products CSV file not found: {products_csv}")
        sys.exit(1)

    # Load the products from the CSV file
    logger.info(f"Loading products from {products_csv}")
    products = load_products_from_csv(products_csv)
    logger.info(f"Loaded {len(products)} products")

    # Initialize the repository with the products (now with enhanced batch processing and graph relationships)
    logger.info("Initializing Neo4j repository with enhanced graph relationships...")
    logger.info("This will create:")
    logger.info("  - Product nodes with embeddings")
    logger.info("  - Category nodes and BELONGS_TO relationships")
    logger.info("  - Collection nodes and IN_COLLECTION relationships")
    logger.info("  - Attribute nodes and HAS_ATTRIBUTE relationships")
    logger.info("  - SIMILAR_TO relationships based on embeddings")
    logger.info("  - RECOMMENDED_WITH relationships for cross-category recommendations")
    
    await repository.insert_products(products)
    logger.info(f"✅ Successfully initialized Neo4j repository with {len(products)} products/variants with 3-level categories and attributes")
    logger.info("🎉 Enhanced graph relationships created! You can now use:")
    logger.info("  - Graph-aware search with relationship scoring")
    logger.info("  - Related products discovery")
    logger.info("  - Cross-category recommendations")
    logger.info("  - Attribute-based filtering")

    logger.info("Done!")


async def get_products(query: str, categories: list[str] | None = None):
    """Search for products using a Neo4j product repository.

    Args:
        query: The search query
        categories: Optional list of categories to filter by
    """
    repository = get_repository()

    logger.info(f"Searching for products: {query}")
    if categories:
        logger.info(f"Filtering by categories: {categories}")
        products = await repository.get_products_by_query(query, num_results=5, categories=categories)
    else:
        products = await repository.get_products_by_query(query, num_results=5)

    if not products:
        logger.info("No products found")
        return []

    logger.info(f"Found {len(products)} products")
    for product in products:
        logger.info(f"- {product.name}: ${product.price} ({product.category})")
    return products


async def get_products_by_ids(product_ids: list[int]):
    """Get products by their IDs using Neo4j repository.

    Args:
        product_ids: List of product IDs to retrieve
    """
    repository = get_repository()

    logger.info(f"Retrieving products by IDs: {product_ids}")
    products = await repository.get_products_by_ids(product_ids)

    if not products:
        logger.info("No products found")
        return []

    logger.info(f"Found {len(products)} products")
    for product in products:
        logger.info(f"- {product.name}: ${product.price} ({product.category})")
    return products


async def test_neo4j_search():
    """Test various search capabilities of the Neo4j repository."""
    logger.info("Testing Neo4j search capabilities...")
    
    # Test semantic search
    logger.info("\n1. Testing semantic search:")
    await get_products("comfortable hiking boots for beginners")
    
    # Test category filtering
    logger.info("\n2. Testing category filtering:")
    await get_products("waterproof", categories=["clothing"])
    
    # Test specific product retrieval
    logger.info("\n3. Testing product retrieval by IDs:")
    await get_products_by_ids([1, 2, 3])
    
    # Test outdoor gear search
    logger.info("\n4. Testing outdoor gear search:")
    await get_products("tents for camping in cold weather")
    
    # Test related products (new enhanced feature)
    logger.info("\n5. Testing related products (enhanced feature):")
    await test_related_products()
    
    logger.info("\nNeo4j search tests completed!")


async def test_related_products():
    """Test the new related products functionality."""
    repository = get_repository()
    
    # Get a sample product first
    products = await repository.get_products_by_query("hiking boots", num_results=1)
    if not products:
        logger.info("No products found for related products test")
        return
    
    sample_product = products[0]
    logger.info(f"Finding related products for: {sample_product.name}")
    
    # Get related products using the new graph relationships
    related_products = await repository.get_related_products(sample_product.product_id, num_results=5)
    
    if not related_products:
        logger.info("No related products found")
        return
    
    logger.info(f"Found {len(related_products)} related products:")
    for product in related_products:
        logger.info(f"- {product.name}: ${product.price} ({product.category})")


if __name__ == "__main__":
    # Uncomment the function you want to run:
    
    # Load products into Neo4j (with enhanced batch processing and graph relationships)
    asyncio.run(setup_db())
    
    # Test search capabilities (including new graph-aware features)
    # asyncio.run(test_neo4j_search())
    
    # Test specific queries
    # asyncio.run(get_products("Show me tents to camp in yosemite"))
    # asyncio.run(get_products("waterproof jackets", categories=["clothing"]))
    # asyncio.run(get_products_by_ids([1, 5, 10]))
    
    # Test the new related products feature
    # asyncio.run(test_related_products())
