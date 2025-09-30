import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import math

import neo4j
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.retrievers import HybridCypherRetriever

import asyncio
from backend.domain.entities import Product
from backend.infrastructure.connections.neo4j import INeo4jConnection
from backend.infrastructure.repositories.product_repository.interface import IProductRepository

logger = logging.getLogger("conversational_commerce")


class Neo4jProductRepository(IProductRepository):
    """Repository for product operations using Neo4j graph database with enhanced graph relationships."""

    def __init__(self, connection: INeo4jConnection, embedding_model=None):
        """Initialize the Neo4jProductRepository with the provided connection.

        Args:
            connection: The Neo4j connection.
            embedding_model: The embedding model to use for vector search.

        """
        self.connection = connection
        self.embedding_model = embedding_model
        self.vector_index_name = "productEmbedding"
        self.fulltext_index_name = "productFulltext"
        self.batch_size = 100  # Batch size for bulk operations
        
        # Define the enhanced retrieval query for graph-aware search
        # self.retrieval_query = """
        # RETURN  node.product_id as product_id,
        #         node.name as name,
        #         node.price as price,
        #         node.category as category,
        #         node.description as description,
        #         node.review_score as review_score,
        #         node.best_for as best_for,
        #         node.image_url as image_url,
        #         node.breadcrumbs as breadcrumbs,
        #         score as similarityScore,
        #         size([(node)-[:BELONGS_TO]->(c:Category) | c]) as category_count,
        #         size([(node)-[:IN_COLLECTION]->(col:Collection) | col]) as collection_count
        # """
        
        self.retrieval_query = """
            CALL db.index.fulltext.queryNodes($fulltext, $query) YIELD node, score
            WITH node AS prod, score
            OPTIONAL MATCH (prod)-[:HAS_VARIANT]->(v:Variant)
            OPTIONAL MATCH (v)-[:HAS_ATTR]->(bf:AttrValue {key:'best_for'})
            OPTIONAL MATCH (v)-[:HAS_ATTR]->(descAV:AttrValue {key:'description_text'})
            RETURN prod.productId AS product_id,
                prod.name      AS name,
                coalesce(prod.image, prod.image_url) AS image_url,
                collect(distinct bf.value_str) AS best_for,
                coalesce(descAV.value_str,'')  AS description,
                score AS similarityScore
        """


    # async def insert_products(self, products: list[Product]) -> None:
    #     """Initialize the product repository from a list of products with enhanced graph relationships.

    #     Args:
    #         products: List of Product objects.

    #     """
    #     def _operation(driver: neo4j.Driver):
    #         with driver.session() as session:
    #             # Create indexes if they don't exist
    #             self._create_vector_index(session)
    #             self._create_fulltext_index(session)
    #             self._create_constraints(session)
                
    #             # Process products in batches
    #             total_products = len(products)
    #             batches = math.ceil(total_products / self.batch_size)
                
    #             logger.info(f"Processing {total_products} products in {batches} batches of {self.batch_size}")
                
    #             for batch_idx in range(batches):
    #                 start_idx = batch_idx * self.batch_size
    #                 end_idx = min(start_idx + self.batch_size, total_products)
    #                 batch_products = products[start_idx:end_idx]
                    
    #                 logger.info(f"Processing batch {batch_idx + 1}/{batches} (products {start_idx + 1}-{end_idx})")
                    
    #                 # Create batch transaction
    #                 with session.begin_transaction() as tx:
    #                     # 1. Create Product nodes first (they need to exist before relationships)
    #                     self._create_products_batch(tx, batch_products)
                        
    #                     # 2. Create Category nodes and BELONGS_TO relationships
    #                     self._create_categories_batch(tx, batch_products)
                        
    #                     # 3. Create Collection nodes and IN_COLLECTION relationships  
    #                     self._create_collections_batch(tx, batch_products)
                        
    #                     # 4. Create attribute relationships
    #                     self._create_attribute_relationships_batch(tx, batch_products)
                        
    #                     # 5. Create attribute relationships
    #                     self._create_attribute_relationships_batch(tx, batch_products)
                    
    #                 logger.info(f"Completed batch {batch_idx + 1}/{batches}")
                
    #             logger.info(f"Successfully initialized {total_products} products with graph relationships in Neo4j")
    #             return total_products

    #     return await asyncio.get_event_loop().run_in_executor(
    #         None, 
    #         self.connection.execute_db_operation,
    #         _operation, 
    #         "Failed to initialize products in Neo4j"
    #     )
        
    async def insert_products(self, products: list[Product]) -> None:
        """Upsert products with 3-level categories and AttrValues."""
        def _operation(driver: neo4j.Driver):
            with driver.session() as session:
                # Create indexes first - this is crucial for search functionality
                self._create_vector_index(session)
                self._create_fulltext_index(session)
                self._create_constraints(session)

                total = len(products)
                batches = math.ceil(total / self.batch_size)
                logger.info(f"Processing {total} rows in {batches} batches")

                for i in range(batches):
                    batch = products[i * self.batch_size : (i + 1) * self.batch_size]
                    with session.begin_transaction() as tx:
                        self._create_products_batch(tx, batch)
                        self._create_categories_batch(tx, batch)
                        self._create_attr_values_batch(tx, batch)

                logger.info(f"Inserted/updated {total} products")
                return total

        return await asyncio.get_event_loop().run_in_executor(
            None,
            self.connection.execute_db_operation,
            _operation,
            "Failed to initialize products in Neo4j",
        )


    # def _create_categories_batch(self, tx, products: List[Product]) -> None:
    #     """Create Category nodes and BELONGS_TO relationships in batch."""
    #     # Extract unique categories
    #     categories = set()
    #     category_products = {}
        
    #     for product in products:
    #         if product.category:
    #             categories.add(product.category)
    #             if product.category not in category_products:
    #                 category_products[product.category] = []
    #             category_products[product.category].append(product.product_id)
        
    #     # Create Category nodes
    #     for category in categories:
    #         tx.run("""
    #             MERGE (c:Category {name: $category})
    #             SET c.slug = $slug,
    #                 c.product_count = size([(c)<-[:BELONGS_TO]-(p:Product) | p]) + $new_count
    #         """, {
    #             'category': category,
    #             'slug': self._slugify(category),
    #             'new_count': len(category_products[category])
    #         })
        
    #     # Create BELONGS_TO relationships
    #     for category, product_ids in category_products.items():
    #         for product_id in product_ids:
    #             tx.run("""
    #                 MATCH (p:Product {product_id: $product_id})
    #                 MATCH (c:Category {name: $category})
    #                 MERGE (p)-[:BELONGS_TO]->(c)
    #             """, {
    #                 'product_id': product_id,
    #                 'category': category
    #             })
    
    def _create_categories_batch(self, tx, products: list[Product]) -> None:
        """Create 3-level categories and link products to leaf Category."""
        for p in products:
            if not p.category_slug and not p.category_name:
                continue

            # tx.run(
            #     """
            #     // Create/Upsert the three levels
            #     MERGE (mc:MainCategory {code: coalesce($main_slug, $main_name)})
            #     ON CREATE SET mc.name = $main_name
            #     SET mc.name = coalesce($main_name, mc.name)

            #     MERGE (sc:SubCategory {code: coalesce($sub_slug, $sub_name)})
            #     ON CREATE SET sc.name = $sub_name
            #     SET sc.name = coalesce($sub_name, sc.name)

            #     MERGE (c:Category {code: coalesce($cat_slug, $cat_name)})
            #     ON CREATE SET c.name = $cat_name
            #     SET c.name = coalesce($cat_name, c.name)

            #     MERGE (c)-[:CHILD_OF]->(sc)
            #     MERGE (sc)-[:CHILD_OF]->(mc)

            #     MATCH (prod:Product {productId: $product_id})
            #     MERGE (prod)-[:IN_CATEGORY]->(c)
            #     """,
            #     {
            #         "product_id": p.product_id,
            #         "main_slug": p.main_category_slug,
            #         "main_name": p.main_category,
            #         "sub_slug": p.sub_category_slug,
            #         "sub_name": p.sub_category,
            #         "cat_slug": p.category_slug,
            #         "cat_name": p.category_name,
            #     },
            # )
            tx.run(
                """
                // Compute codes/names up front (treat empty strings as null)
                WITH
                CASE WHEN $main_slug IS NOT NULL AND $main_slug <> '' THEN $main_slug ELSE $main_name END AS mc_code,
                $main_name AS mc_name,
                CASE WHEN $sub_slug  IS NOT NULL AND $sub_slug  <> '' THEN $sub_slug  ELSE $sub_name  END AS sc_code,
                $sub_name  AS sc_name,
                CASE WHEN $cat_slug  IS NOT NULL AND $cat_slug  <> '' THEN $cat_slug  ELSE $cat_name  END AS c_code,
                $cat_name  AS c_name,
                $product_id AS pid

                // Require a leaf Category code
                WHERE c_code IS NOT NULL AND c_code <> ''

                // Category (leaf)
                MERGE (c:Category {code: c_code})
                ON CREATE SET c.name = c_name
                SET c.name = coalesce(c_name, c.name)

                // If MainCategory code exists, create it and attach
                FOREACH (_ IN CASE WHEN mc_code IS NOT NULL AND mc_code <> '' THEN [1] ELSE [] END |
                MERGE (mc:MainCategory {code: mc_code})
                    ON CREATE SET mc.name = mc_name
                    SET mc.name = coalesce(mc_name, mc.name)

                // If SubCategory code exists, create sc and chain c->sc->mc
                FOREACH (__ IN CASE WHEN sc_code IS NOT NULL AND sc_code <> '' THEN [1] ELSE [] END |
                    MERGE (sc:SubCategory {code: sc_code})
                    ON CREATE SET sc.name = sc_name
                    SET sc.name = coalesce(sc_name, sc.name)
                    MERGE (c)-[:CHILD_OF]->(sc)
                    MERGE (sc)-[:CHILD_OF]->(mc)
                )

                // Else (no sub), link c directly to mc
                FOREACH (__ IN CASE WHEN sc_code IS NULL OR sc_code = '' THEN [1] ELSE [] END |
                    MERGE (c)-[:CHILD_OF]->(mc)
                )
                )

                // Finally, link Product to the leaf Category
                WITH c, pid
                MATCH (prod:Product {productId: pid})
                MERGE (prod)-[:IN_CATEGORY]->(c)
                """,
                {
                    "product_id": p.product_id,
                    "main_slug": p.main_category_slug,
                    "main_name": p.main_category,
                    "sub_slug":  p.sub_category_slug,
                    "sub_name":  p.sub_category,
                    "cat_slug":  p.category_slug,
                    "cat_name":  p.category_name,
                },
            )



    def _create_attr_values_batch(self, tx, products: list[Product]) -> None:
        """
        Create Attribute & AttrValue nodes and link them to the Variant.
        Only values present in the CSV are created.
        """
        for p in products:
            key_to_value = [
                ("review_score", p.review_score, "num"),
                ("review_count", p.review_count, "num"),
                ("product_type_name", p.product_type_name, "str"),
                ("product_type_slug", p.product_type_slug, "str"),
                ("tax_class", p.tax_class, "str"),
                ("collections", p.collections, "str"),
                ("breadcrumbs", "|".join(p.breadcrumbs) if p.breadcrumbs else None, "str"),
                ("short_description", p.short_description, "str"),
                ("description_text", p.description_text, "str"),
            ]

            # best_for is a list: create one AttrValue per item
            for bf in (p.best_for or []):
                tx.run(
                    """
                    MERGE (a:Attribute {key: 'best_for'})
                    CREATE (av:AttrValue {key:'best_for', value_str:$val, norm: toLower($val), confidence: 1.0})
                    WITH a, av
                    MATCH (v:Variant {variantId: $variant_id})
                    MERGE (v)-[:HAS_ATTR]->(av)
                    MERGE (av)-[:OF]->(a)
                    """,
                    {"variant_id": p.variant_id, "val": bf},
                )

            # scalar attributes
            for key, val, typ in key_to_value:
                if val in (None, "", []):
                    continue

                tx.run(
                    """
                    MERGE (a:Attribute {key: $key})
                    CREATE (av:AttrValue {
                        key:$key,
                        value_str: CASE WHEN $type='str' THEN $s END,
                        value_num: CASE WHEN $type='num' THEN $n END,
                        confidence: 1.0
                    })
                    WITH a, av
                    MATCH (v:Variant {variantId: $variant_id})
                    MERGE (v)-[:HAS_ATTR]->(av)
                    MERGE (av)-[:OF]->(a)
                    """,
                    {
                        "key": key,
                        "type": typ,
                        "s": str(val) if typ == "str" else None,
                        "n": float(val) if typ == "num" else None,
                        "variant_id": p.variant_id,
                    },
                )



    def _create_collections_batch(self, tx, products: List[Product]) -> None:
        """Create Collection nodes and IN_COLLECTION relationships in batch."""
        # Extract collections from breadcrumbs
        collection_products = {}
        
        for product in products:
            if product.breadcrumbs:
                for breadcrumb in product.breadcrumbs:
                    if breadcrumb not in collection_products:
                        collection_products[breadcrumb] = []
                    collection_products[breadcrumb].append(product.product_id)
        
        # Create Collection nodes and relationships
        for collection, product_ids in collection_products.items():
            # Create collection node
            tx.run("""
                MERGE (col:Collection {name: $collection})
                SET col.slug = $slug,
                    col.product_count = size([(col)<-[:IN_COLLECTION]-(p:Product) | p]) + $new_count
            """, {
                'collection': collection,
                'slug': self._slugify(collection),
                'new_count': len(product_ids)
            })
            
            # Create IN_COLLECTION relationships
            for product_id in product_ids:
                tx.run("""
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (col:Collection {name: $collection})
                    MERGE (p)-[:IN_COLLECTION]->(col)
                """, {
                    'product_id': product_id,
                    'collection': collection
                })

    # def _create_products_batch(self, tx, products: List[Product]) -> None:
    #     """Create Product nodes with attributes in batch."""
    #     for product in products:
    #         # Create product node
    #         cypher_query = """
    #         MERGE (p:Product {product_id: $product_id})
    #         SET p.name = $name,
    #             p.price = $price,
    #             p.category = $category,
    #             p.description = $description,
    #             p.review_score = $review_score,
    #             p.best_for = $best_for,
    #             p.image_url = $image_url,
    #             p.breadcrumbs = $breadcrumbs,
    #             p.created_at = datetime(),
    #             p.updated_at = datetime()
    #         """
            
    #         params = {
    #             'product_id': product.product_id,
    #             'name': product.name,
    #             'price': product.price,
    #             'category': product.category,
    #             'description': product.description,
    #             'review_score': product.review_score,
    #             'best_for': product.best_for,
    #             'image_url': product.image_url,
    #             'breadcrumbs': product.breadcrumbs
    #         }
            
    #         # Add embedding if it exists
    #         if product.embedding:
    #             cypher_query = cypher_query.replace(
    #                 "p.updated_at = datetime()",
    #                 "p.updated_at = datetime(), p.embedding = $embedding"
    #             )
    #             params['embedding'] = product.embedding
            
    #         tx.run(cypher_query, params)

    def _create_products_batch(self, tx, products: list[Product]) -> None:
        """Create Product + Variant nodes and link them."""
        for p in products:
            tx.run(
                """
                MERGE (prod:Product {productId: $product_id})
                ON CREATE SET prod.created_at = datetime()
                SET  prod.name = $name,
                    prod.brand = $brand,
                    prod.canonicalUrl = $url,
                    prod.slug = $slug,
                    prod.image = $image_url,
                    prod.updated_at = datetime()

                MERGE (v:Variant {variantId: $variant_id})
                MERGE (prod)-[:HAS_VARIANT]->(v)
                """,
                {
                    "product_id": p.product_id,
                    "variant_id": p.variant_id,
                    "name": p.name,
                    "brand": p.brand,
                    "url": p.url,
                    "slug": p.slug,
                    "image_url": p.image_url,
                },
            )

            # optional embedding on Product (kept compatible with your retriever)
            if p.embedding:
                tx.run(
                    """
                    MATCH (prod:Product {productId: $product_id})
                    SET prod.embedding = $embedding
                    """,
                    {"product_id": p.product_id, "embedding": p.embedding},
                )

            

    def _create_attribute_relationships_batch(self, tx, products: List[Product]) -> None:
        """Create Attribute nodes and HAS_ATTRIBUTE relationships in batch."""
        for product in products:
            if product.best_for:
                for attribute in product.best_for:
                    # Create attribute node
                    tx.run("""
                        MERGE (attr:Attribute {name: $attribute})
                        SET attr.slug = $slug
                    """, {
                        'attribute': attribute,
                        'slug': self._slugify(attribute)
                    })
                    
                    # Create HAS_ATTRIBUTE relationship
                    tx.run("""
                        MATCH (p:Product {product_id: $product_id})
                        MATCH (attr:Attribute {name: $attribute})
                        MERGE (p)-[:HAS_ATTRIBUTE]->(attr)
                    """, {
                        'product_id': product.product_id,
                        'attribute': attribute
                    })


    def _create_similarity_relationships_batch(self, tx, products: List[Product]) -> None:
        """Create SIMILAR_TO relationships based on embeddings and categories."""
        # For products with embeddings, create similarity relationships
        products_with_embeddings = [p for p in products if p.embedding]
        
        if len(products_with_embeddings) < 2:
            return
        
        # Create similarity relationships within same category
        for i, product1 in enumerate(products_with_embeddings):
            for j, product2 in enumerate(products_with_embeddings[i+1:], i+1):
                if product1.category == product2.category:
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(product1.embedding, product2.embedding)
                    
                    # Only create relationship if similarity is above threshold
                    if similarity > 0.7:  # Adjust threshold as needed
                        tx.run("""
                            MATCH (p1:Product {product_id: $product_id1})
                            MATCH (p2:Product {product_id: $product_id2})
                            MERGE (p1)-[:SIMILAR_TO {similarity: $similarity, type: 'embedding'}]->(p2)
                        """, {
                            'product_id1': product1.product_id,
                            'product_id2': product2.product_id,
                            'similarity': similarity
                        })

    def _create_recommendation_relationships_batch(self, tx, products: List[Product]) -> None:
        """Create RECOMMENDED_WITH relationships for cross-category recommendations."""
        # Group products by category
        category_products = {}
        for product in products:
            if product.category not in category_products:
                category_products[product.category] = []
            category_products[product.category].append(product)
        
        # Create cross-category recommendations based on attributes
        categories = list(category_products.keys())
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                # Find products with common attributes
                for product1 in category_products[cat1]:
                    for product2 in category_products[cat2]:
                        common_attrs = set(product1.best_for) & set(product2.best_for)
                        if len(common_attrs) >= 2:  # At least 2 common attributes
                            tx.run("""
                                MATCH (p1:Product {product_id: $product_id1})
                                MATCH (p2:Product {product_id: $product_id2})
                                MERGE (p1)-[:RECOMMENDED_WITH {common_attributes: $common_attrs, strength: $strength}]->(p2)
                            """, {
                                'product_id1': product1.product_id,
                                'product_id2': product2.product_id,
                                'common_attrs': list(common_attrs),
                                'strength': len(common_attrs)
                            })

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        if not text:
            return ""
        # Simple slugification - replace spaces with hyphens and lowercase
        return re.sub(r'[^\w\s-]', '', text.lower()).strip().replace(' ', '-')

    # def _create_constraints(self, session: neo4j.Session) -> None:
    #     """Create database constraints for data integrity."""
    #     try:
    #         # Create unique constraints
    #         session.run("CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE")
    #         session.run("CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
    #         session.run("CREATE CONSTRAINT collection_name_unique IF NOT EXISTS FOR (col:Collection) REQUIRE col.name IS UNIQUE")
    #         session.run("CREATE CONSTRAINT attribute_name_unique IF NOT EXISTS FOR (attr:Attribute) REQUIRE attr.name IS UNIQUE")
    #         logger.info("Created database constraints")
    #     except Exception as e:
    #         logger.warning(f"Constraint creation failed (might already exist): {e}")

    def _create_constraints(self, session: neo4j.Session) -> None:
        """Create database constraints for data integrity."""
        try:
            # Create unique constraints
            session.run("CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.productId IS UNIQUE")
            session.run("CREATE CONSTRAINT variant_id_unique IF NOT EXISTS FOR (v:Variant) REQUIRE v.variantId IS UNIQUE")
            session.run("CREATE CONSTRAINT category_code_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.code IS UNIQUE")
            session.run("CREATE CONSTRAINT subcategory_code_unique IF NOT EXISTS FOR (sc:SubCategory) REQUIRE sc.code IS UNIQUE")
            session.run("CREATE CONSTRAINT maincategory_code_unique IF NOT EXISTS FOR (mc:MainCategory) REQUIRE mc.code IS UNIQUE")
            session.run("CREATE CONSTRAINT attribute_key_unique IF NOT EXISTS FOR (a:Attribute) REQUIRE a.key IS UNIQUE")
            logger.info("Created database constraints")
        except Exception as e:
            logger.warning(f"Constraint creation failed (might already exist): {e}")


    async def get_products_by_query(
        self, query: str, num_results: int = 10, user_id: int | None = None, categories: list[str] | None = None
    ) -> list[Product]:
        """Get products based on a natural language query with enhanced graph-aware search.

        Args:
            query: Natural language query describing the products to retrieve
            num_results: Number of products to return
            user_id: Optional user ID to filter out products the user has already purchased
            categories: Optional list of product categories to filter by

        Returns:
            List of Product objects

        """
        def _operation(driver: neo4j.Driver):
            # Build enhanced Cypher query with graph relationships
            cypher_query = self._build_enhanced_search_query(query, num_results, categories)
            
            with driver.session() as session:
                result = session.run(cypher_query, {
                    'query': query,
                    'num_results': num_results,
                    'categories': categories or []
                })
                
                products = []
                for record in result:
                    try:
                        product = Product(
                            product_id=str(record.get('product_id')),
                            variant_id=str(record.get('variant_id') or ''),
                            name=record.get('name') or '',
                            brand=record.get('brand'),
                            url=record.get('url'),
                            slug=record.get('slug'),
                            image_url=record.get('image_url'),
                            # categories will be resolved via relations; not projected directly
                            main_category=None,
                            main_category_slug=None,
                            sub_category=None,
                            sub_category_slug=None,
                            category_name=record.get('category_name') or None,
                            category_slug=record.get('category_slug') or None,
                            # attrs
                            review_score=None,
                            review_count=None,
                            product_type_name=None,
                            product_type_slug=None,
                            tax_class=None,
                            collections=None,
                            breadcrumbs=[],
                            short_description=None,
                            description_text=record.get('description_text') or None,
                            best_for=[b for b in (record.get('best_for') or []) if b],
                            embedding=record.get('embedding'),
                        )
                        products.append(product)
                    except Exception as e:
                        logger.warning(f"Failed to create Product from record: {e}")
                        continue
                
                logger.info(f"Retrieved {len(products)} products with enhanced graph search")
                return products

        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.connection.execute_db_operation,
            _operation, 
            "Failed to fetch products from Neo4j"
        )

    def _build_enhanced_search_query(self, query: str, num_results: int, categories: List[str] | None) -> str:
        """Build a Cypher query aligned with the current graph schema.

        Current schema highlights:
        - Product nodes use property `productId` (camelCase), not `product_id`
        - Category relation is `(:Product)-[:IN_CATEGORY]->(:Category)`
        - Variants exist: `(:Product)-[:HAS_VARIANT]->(:Variant)`
        - Attributes are stored as `(:Variant)-[:HAS_ATTR]->(:AttrValue)-[:OF]->(:Attribute)`
        - Product has `name`, `image` (not `image_url`)
        - Descriptions/"best_for" live in AttrValues with keys `description_text` and `best_for`
        """

        cypher_query = f"""
        CALL db.index.fulltext.queryNodes('{self.fulltext_index_name}', $query) YIELD node, score
        WITH node AS prod, score
        """
        
        # Category filtering and projection (works whether categories provided or not)
        cypher_query += """
        OPTIONAL MATCH (prod)-[:IN_CATEGORY]->(c:Category)
        WITH prod, score,
             collect(distinct c.name) AS c_names,
             collect(distinct c.code) AS c_codes
        WITH prod, score, c_names, c_codes,
             CASE
               WHEN size($categories) = 0 THEN true
               ELSE any(cat IN $categories WHERE any(n IN c_names WHERE toLower(n) = toLower(cat))
                                         OR any(cd IN c_codes WHERE toLower(cd) = toLower(cat)))
             END AS cat_ok
        WHERE cat_ok
        """

        cypher_query += """
        OPTIONAL MATCH (prod)-[:HAS_VARIANT]->(v:Variant)
        OPTIONAL MATCH (v)-[:HAS_ATTR]->(bf:AttrValue {key:'best_for'})
        OPTIONAL MATCH (v)-[:HAS_ATTR]->(descAV:AttrValue {key:'description_text'})
        OPTIONAL MATCH (v)-[:HAS_ATTR]->(shortAV:AttrValue {key:'short_description'})

        WITH prod, score, c_names, c_codes,
             collect(distinct bf.value_str) AS best_for,
             coalesce(
                 head(collect(distinct descAV.value_str)),
                 head(collect(distinct shortAV.value_str)),
                 ''
             ) AS description_text,
             head(collect(distinct v.variantId)) AS variant_id,
             coalesce(head(c_names), '') AS category_name,
             coalesce(head(c_codes), '') AS category_slug

        RETURN DISTINCT prod.productId AS product_id,
               variant_id AS variant_id,
               prod.name AS name,
               prod.brand AS brand,
               prod.canonicalUrl AS url,
               prod.slug AS slug,
               coalesce(prod.image, prod.image_url) AS image_url,
               prod.embedding AS embedding,
               description_text AS description_text,
               category_name AS category_name,
               category_slug AS category_slug,
               best_for AS best_for,
               score AS similarityScore
        ORDER BY similarityScore DESC
        LIMIT $num_results
        """
        
        return cypher_query

    # async def get_related_products(self, product_id: int, num_results: int = 5) -> list[Product]:
    #     """Get related products using graph relationships."""
        
    #     def _operation(driver: neo4j.Driver):
    #         with driver.session() as session:
    #             cypher_query = """
    #             MATCH (p:Product {product_id: $product_id})
    #             OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(category_products:Product)
    #             OPTIONAL MATCH (p)-[:HAS_ATTRIBUTE]->(attr:Attribute)<-[:HAS_ATTRIBUTE]-(attr_products:Product)
                
    #             WITH p, category_products, attr_products
    #             UNWIND [category_products, attr_products] as related
    #             WITH DISTINCT related
    #             WHERE related IS NOT NULL AND related.product_id <> $product_id
                
    #             RETURN related.product_id as product_id,
    #                    related.name as name,
    #                    related.price as price,
    #                    related.category as category,
    #                    related.description as description,
    #                    related.review_score as review_score,
    #                    related.best_for as best_for,
    #                    related.image_url as image_url,
    #                    related.breadcrumbs as breadcrumbs,
    #                    related.embedding as embedding
    #             LIMIT $num_results
    #             """
                
    #             result = session.run(cypher_query, {
    #                 'product_id': product_id,
    #                 'num_results': num_results
    #             })
                
    #             products = []
    #             for record in result:
    #                 try:
    #                     product = Product(
    #                         product_id=record['product_id'],
    #                         name=record['name'],
    #                         price=record['price'],
    #                         category=record['category'],
    #                         description=record['description'],
    #                         review_score=record['review_score'],
    #                         best_for=record['best_for'],
    #                         image_url=record['image_url'],
    #                         breadcrumbs=record.get('breadcrumbs', []),
    #                         embedding=record.get('embedding')
    #                     )
    #                     products.append(product)
    #                 except Exception as e:
    #                     logger.warning(f"Failed to create related Product: {e}")
    #                     continue
                
    #             logger.info(f"Retrieved {len(products)} related products for product {product_id}")
    #             return products

    #     return await asyncio.get_event_loop().run_in_executor(
    #         None, 
    #         self.connection.execute_db_operation,
    #         _operation, 
    #         "Failed to fetch related products from Neo4j"
    #     )

    async def get_related_products(self, product_id: str, num_results: int = 5) -> list[Product]:
        def _operation(driver: neo4j.Driver):
            with driver.session() as session:
                cypher_query = """
                // anchor product
                MATCH (p:Product {productId: $product_id})

                // same leaf category
                OPTIONAL MATCH (p)-[:IN_CATEGORY]->(c:Category)<-[:IN_CATEGORY]-(q:Product)

                // overlap on best_for via variants/attrvalues
                OPTIONAL MATCH (p)-[:HAS_VARIANT]->(:Variant)-[:HAS_ATTR]->(:AttrValue {key:'best_for'})<-[:HAS_ATTR]-(:Variant)<-[:HAS_VARIANT]-(q)

                WITH q, count(*) AS relScore
                WHERE q IS NOT NULL AND q <> p
                // pull display fields + desc/best_for for results
                OPTIONAL MATCH (q)-[:HAS_VARIANT]->(qv:Variant)-[:HAS_ATTR]->(qbf:AttrValue {key:'best_for'})
                OPTIONAL MATCH (qv)-[:HAS_ATTR]->(qdesc:AttrValue {key:'description_text'})

                RETURN q.productId AS product_id,
                    q.name      AS name,
                    coalesce(q.image, q.image_url) AS image_url,
                    collect(distinct qbf.value_str) AS best_for,
                    coalesce(qdesc.value_str,'')    AS description
                ORDER BY relScore DESC, name ASC
                LIMIT $num_results
                """
                result = session.run(cypher_query, {
                    'product_id': product_id,
                    'num_results': num_results
                })
                
                products = []
                for r in result:
                    products.append(Product(
                        product_id=r['product_id'],
                        variant_id="",  # not needed here
                        name=r['name'],
                        brand=None,
                        url=None,
                        slug=None,
                        image_url=r['image_url'],
                        # categories resolved elsewhere
                        # attributes:
                        review_score=None,
                        review_count=None,
                        product_type_name=None,
                        product_type_slug=None,
                        tax_class=None,
                        collections=None,
                        breadcrumbs=[],
                        short_description=None,
                        description_text=r['description'],
                        best_for=r['best_for'] or [],
                        embedding=None
                    ))
                logger.info(f"Retrieved {len(products)} related products for product {product_id}")
                return products

        return await asyncio.get_event_loop().run_in_executor(
            None, self.connection.execute_db_operation, _operation,
            "Failed to fetch related products from Neo4j"
        )


    # async def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
    #     """Get products by their IDs.

    #     Args:
    #         product_ids: List of product IDs to retrieve

    #     Returns:
    #         List of Product objects matching the provided IDs
    #     """
    #     if not product_ids:
    #         return []

    #     def _operation(driver: neo4j.Driver):
    #         with driver.session() as session:
    #             cypher_query = """
    #             MATCH (p:Product)
    #             WHERE p.product_id IN $product_ids
    #             RETURN p
    #             """
                
    #             result = session.run(cypher_query, {'product_ids': product_ids})
                
    #             products = []
    #             for record in result:
    #                 node = record['p']
    #                 try:
    #                     product = Product(
    #                         product_id=node['product_id'],
    #                         name=node['name'],
    #                         price=node['price'],
    #                         category=node['category'],
    #                         description=node['description'],
    #                         review_score=node['review_score'],
    #                         best_for=node['best_for'],
    #                         image_url=node['image_url'],
    #                         breadcrumbs=node.get('breadcrumbs', []),
    #                         embedding=node.get('embedding')
    #                     )
    #                     products.append(product)
    #                 except Exception as e:
    #                     logger.warning(f"Failed to create Product from node: {e}")
    #                     continue
                
    #             logger.info(f"Retrieved {len(products)} products by IDs from Neo4j")
    #             return products

    #     return await asyncio.get_event_loop().run_in_executor(
    #         None, 
    #         self.connection.execute_db_operation,
    #         _operation, 
    #         "Failed to fetch products by IDs from Neo4j"
    #     )

    async def get_products_by_ids(self, product_ids: list[str]) -> list[Product]:
        if not product_ids:
            return []
        def _operation(driver: neo4j.Driver):
            with driver.session() as session:
                cypher_query = """
                MATCH (p:Product)
                WHERE p.productId IN $product_ids
                OPTIONAL MATCH (p)-[:HAS_VARIANT]->(v:Variant)-[:HAS_ATTR]->(d:AttrValue {key:'description_text'})
                OPTIONAL MATCH (v)-[:HAS_ATTR]->(bf:AttrValue {key:'best_for'})
                RETURN p, collect(distinct bf.value_str) AS best_for, coalesce(d.value_str,'') AS description
                """
                result = session.run(cypher_query, {'product_ids': product_ids})
                
                products = []
                for record in result:
                    node = record['p']
                    products.append(Product(
                        product_id=node['productId'],
                        variant_id="",
                        name=node.get('name'),
                        brand=node.get('brand'),
                        url=node.get('canonicalUrl'),
                        slug=node.get('slug'),
                        image_url=node.get('image') or node.get('image_url'),
                        # categories handled elsewhere
                        review_score=None, review_count=None,
                        product_type_name=None, product_type_slug=None,
                        tax_class=None, collections=None,
                        breadcrumbs=[],
                        short_description=None,
                        description_text=record['description'],
                        best_for=record['best_for'] or [],
                            embedding=node.get('embedding')
                    ))
                logger.info(f"Retrieved {len(products)} products by IDs from Neo4j")
                return products

        return await asyncio.get_event_loop().run_in_executor(
            None, self.connection.execute_db_operation, _operation,
            "Failed to fetch products by IDs from Neo4j"
        )


    async def delete_all_products(self) -> None:
        """Delete all products and related nodes from the repository.

        This method removes all product records and related graph nodes from the repository.
        """

        def _operation(driver: neo4j.Driver):
            with driver.session() as session:
                # Delete all nodes and relationships
                cypher_query = """
                MATCH (n)
                DETACH DELETE n
                """
                session.run(cypher_query)
                
                logger.info("Deleted all products and related nodes from Neo4j")
                return None

        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.connection.execute_db_operation,
            _operation, 
            "Failed to delete products from Neo4j"
        )

    def _create_vector_index(self, session: neo4j.Session) -> None:
        """Create vector index for product embeddings."""
        try:
            cypher_query = f"""
            CREATE VECTOR INDEX {self.vector_index_name} IF NOT EXISTS
            FOR (p:Product) ON (p.embedding)
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
            session.run(cypher_query)
            logger.info(f"Created vector index: {self.vector_index_name}")
        except Exception as e:
            # Index might already exist
            logger.warning(f"Vector index creation failed (might already exist): {e}")

    # def _create_fulltext_index(self, session: neo4j.Session) -> None:
    #     """Create fulltext index for product search."""
    #     try:
    #         cypher_query = f"""
    #         CREATE FULLTEXT INDEX {self.fulltext_index_name} IF NOT EXISTS
    #         FOR (p:Product) ON EACH [p.name, p.description, p.category]
    #         """
    #         session.run(cypher_query)
    #         logger.info(f"Created fulltext index: {self.fulltext_index_name}")
    #     except Exception as e:
    #         # Index might already exist
    #         logger.warning(f"Fulltext index creation failed (might already exist): {e}")

    def _create_fulltext_index(self, session: neo4j.Session) -> None:
        try:
            cypher_query = f"""
            CREATE FULLTEXT INDEX {self.fulltext_index_name} IF NOT EXISTS
            FOR (p:Product) ON EACH [p.name, p.slug]
            """
            session.run(cypher_query)
            logger.info(f"Created fulltext index: {self.fulltext_index_name}")
        except Exception as e:
            logger.warning(f"Fulltext index creation failed (might already exist): {e}")
    