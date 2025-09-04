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
        self.retrieval_query = """
        RETURN  node.product_id as product_id,
                node.name as name,
                node.price as price,
                node.category as category,
                node.description as description,
                node.review_score as review_score,
                node.best_for as best_for,
                node.image_url as image_url,
                node.breadcrumbs as breadcrumbs,
                score as similarityScore,
                size([(node)-[:BELONGS_TO]->(c:Category) | c]) as category_count,
                size([(node)-[:IN_COLLECTION]->(col:Collection) | col]) as collection_count
        """

    async def insert_products(self, products: list[Product]) -> None:
        """Initialize the product repository from a list of products with enhanced graph relationships.

        Args:
            products: List of Product objects.

        """
        def _operation(driver: neo4j.Driver):
            with driver.session() as session:
                # Create indexes if they don't exist
                self._create_vector_index(session)
                self._create_fulltext_index(session)
                self._create_constraints(session)
                
                # Process products in batches
                total_products = len(products)
                batches = math.ceil(total_products / self.batch_size)
                
                logger.info(f"Processing {total_products} products in {batches} batches of {self.batch_size}")
                
                for batch_idx in range(batches):
                    start_idx = batch_idx * self.batch_size
                    end_idx = min(start_idx + self.batch_size, total_products)
                    batch_products = products[start_idx:end_idx]
                    
                    logger.info(f"Processing batch {batch_idx + 1}/{batches} (products {start_idx + 1}-{end_idx})")
                    
                    # Create batch transaction
                    with session.begin_transaction() as tx:
                        # 1. Create Product nodes first (they need to exist before relationships)
                        self._create_products_batch(tx, batch_products)
                        
                        # 2. Create Category nodes and BELONGS_TO relationships
                        self._create_categories_batch(tx, batch_products)
                        
                        # 3. Create Collection nodes and IN_COLLECTION relationships  
                        self._create_collections_batch(tx, batch_products)
                        
                        # 4. Create attribute relationships
                        self._create_attribute_relationships_batch(tx, batch_products)
                        
                        # 5. Create attribute relationships
                        self._create_attribute_relationships_batch(tx, batch_products)
                    
                    logger.info(f"Completed batch {batch_idx + 1}/{batches}")
                
                logger.info(f"Successfully initialized {total_products} products with graph relationships in Neo4j")
                return total_products

        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.connection.execute_db_operation,
            _operation, 
            "Failed to initialize products in Neo4j"
        )

    def _create_categories_batch(self, tx, products: List[Product]) -> None:
        """Create Category nodes and BELONGS_TO relationships in batch."""
        # Extract unique categories
        categories = set()
        category_products = {}
        
        for product in products:
            if product.category:
                categories.add(product.category)
                if product.category not in category_products:
                    category_products[product.category] = []
                category_products[product.category].append(product.product_id)
        
        # Create Category nodes
        for category in categories:
            tx.run("""
                MERGE (c:Category {name: $category})
                SET c.slug = $slug,
                    c.product_count = size([(c)<-[:BELONGS_TO]-(p:Product) | p]) + $new_count
            """, {
                'category': category,
                'slug': self._slugify(category),
                'new_count': len(category_products[category])
            })
        
        # Create BELONGS_TO relationships
        for category, product_ids in category_products.items():
            for product_id in product_ids:
                tx.run("""
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (c:Category {name: $category})
                    MERGE (p)-[:BELONGS_TO]->(c)
                """, {
                    'product_id': product_id,
                    'category': category
                })

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

    def _create_products_batch(self, tx, products: List[Product]) -> None:
        """Create Product nodes with attributes in batch."""
        for product in products:
            # Create product node
            cypher_query = """
            MERGE (p:Product {product_id: $product_id})
            SET p.name = $name,
                p.price = $price,
                p.category = $category,
                p.description = $description,
                p.review_score = $review_score,
                p.best_for = $best_for,
                p.image_url = $image_url,
                p.breadcrumbs = $breadcrumbs,
                p.created_at = datetime(),
                p.updated_at = datetime()
            """
            
            params = {
                'product_id': product.product_id,
                'name': product.name,
                'price': product.price,
                'category': product.category,
                'description': product.description,
                'review_score': product.review_score,
                'best_for': product.best_for,
                'image_url': product.image_url,
                'breadcrumbs': product.breadcrumbs
            }
            
            # Add embedding if it exists
            if product.embedding:
                cypher_query = cypher_query.replace(
                    "p.updated_at = datetime()",
                    "p.updated_at = datetime(), p.embedding = $embedding"
                )
                params['embedding'] = product.embedding
            
            tx.run(cypher_query, params)
            

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

    def _create_constraints(self, session: neo4j.Session) -> None:
        """Create database constraints for data integrity."""
        try:
            # Create unique constraints
            session.run("CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT collection_name_unique IF NOT EXISTS FOR (col:Collection) REQUIRE col.name IS UNIQUE")
            session.run("CREATE CONSTRAINT attribute_name_unique IF NOT EXISTS FOR (attr:Attribute) REQUIRE attr.name IS UNIQUE")
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
                            product_id=record['product_id'],
                            name=record['name'],
                            price=record['price'],
                            category=record['category'],
                            description=record['description'],
                            review_score=record['review_score'],
                            best_for=record['best_for'],
                            image_url=record['image_url'],
                            breadcrumbs=record.get('breadcrumbs', []),
                            embedding=record.get('embedding')
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
        """Build an enhanced Cypher query that leverages graph relationships."""
        
        # Base query with graph traversal
        cypher_query = f"""
        CALL db.index.fulltext.queryNodes('{self.fulltext_index_name}', $query) YIELD node, score
        WITH node, score
        """
        
        # Add category filtering if specified
        if categories:
            cypher_query += """
            MATCH (node)-[:BELONGS_TO]->(c:Category)
            WHERE any(cat IN $categories WHERE toLower(c.name) = toLower(cat))
            """
        
        # Add graph-aware scoring
        cypher_query += """
        OPTIONAL MATCH (node)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        OPTIONAL MATCH (node)-[:IN_COLLECTION]->(col:Collection)
        
        WITH node, score,
             size([(node)-[:HAS_ATTRIBUTE]->(a) | a]) as attribute_count,
             size([(node)-[:IN_COLLECTION]->(c) | c]) as collection_count
        
        // Calculate enhanced score combining text similarity and graph metrics
        WITH node, score,
             (score * 0.8 + 
              attribute_count * 0.1 + 
              collection_count * 0.1) as enhanced_score
        
        RETURN DISTINCT node.product_id as product_id,
               node.name as name,
               node.price as price,
               node.category as category,
               node.description as description,
               node.review_score as review_score,
               node.best_for as best_for,
               node.image_url as image_url,
               node.breadcrumbs as breadcrumbs,
               node.embedding as embedding,
               enhanced_score as similarityScore
        ORDER BY enhanced_score DESC
        LIMIT $num_results
        """
        
        return cypher_query

    async def get_related_products(self, product_id: int, num_results: int = 5) -> list[Product]:
        """Get related products using graph relationships."""
        
        def _operation(driver: neo4j.Driver):
            with driver.session() as session:
                cypher_query = """
                MATCH (p:Product {product_id: $product_id})
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(category_products:Product)
                OPTIONAL MATCH (p)-[:HAS_ATTRIBUTE]->(attr:Attribute)<-[:HAS_ATTRIBUTE]-(attr_products:Product)
                
                WITH p, category_products, attr_products
                UNWIND [category_products, attr_products] as related
                WITH DISTINCT related
                WHERE related IS NOT NULL AND related.product_id <> $product_id
                
                RETURN related.product_id as product_id,
                       related.name as name,
                       related.price as price,
                       related.category as category,
                       related.description as description,
                       related.review_score as review_score,
                       related.best_for as best_for,
                       related.image_url as image_url,
                       related.breadcrumbs as breadcrumbs,
                       related.embedding as embedding
                LIMIT $num_results
                """
                
                result = session.run(cypher_query, {
                    'product_id': product_id,
                    'num_results': num_results
                })
                
                products = []
                for record in result:
                    try:
                        product = Product(
                            product_id=record['product_id'],
                            name=record['name'],
                            price=record['price'],
                            category=record['category'],
                            description=record['description'],
                            review_score=record['review_score'],
                            best_for=record['best_for'],
                            image_url=record['image_url'],
                            breadcrumbs=record.get('breadcrumbs', []),
                            embedding=record.get('embedding')
                        )
                        products.append(product)
                    except Exception as e:
                        logger.warning(f"Failed to create related Product: {e}")
                        continue
                
                logger.info(f"Retrieved {len(products)} related products for product {product_id}")
                return products

        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.connection.execute_db_operation,
            _operation, 
            "Failed to fetch related products from Neo4j"
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

        def _operation(driver: neo4j.Driver):
            with driver.session() as session:
                cypher_query = """
                MATCH (p:Product)
                WHERE p.product_id IN $product_ids
                RETURN p
                """
                
                result = session.run(cypher_query, {'product_ids': product_ids})
                
                products = []
                for record in result:
                    node = record['p']
                    try:
                        product = Product(
                            product_id=node['product_id'],
                            name=node['name'],
                            price=node['price'],
                            category=node['category'],
                            description=node['description'],
                            review_score=node['review_score'],
                            best_for=node['best_for'],
                            image_url=node['image_url'],
                            breadcrumbs=node.get('breadcrumbs', []),
                            embedding=node.get('embedding')
                        )
                        products.append(product)
                    except Exception as e:
                        logger.warning(f"Failed to create Product from node: {e}")
                        continue
                
                logger.info(f"Retrieved {len(products)} products by IDs from Neo4j")
                return products

        return await asyncio.get_event_loop().run_in_executor(
            None, 
            self.connection.execute_db_operation,
            _operation, 
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

    def _create_fulltext_index(self, session: neo4j.Session) -> None:
        """Create fulltext index for product search."""
        try:
            cypher_query = f"""
            CREATE FULLTEXT INDEX {self.fulltext_index_name} IF NOT EXISTS
            FOR (p:Product) ON EACH [p.name, p.description, p.category]
            """
            session.run(cypher_query)
            logger.info(f"Created fulltext index: {self.fulltext_index_name}")
        except Exception as e:
            # Index might already exist
            logger.warning(f"Fulltext index creation failed (might already exist): {e}")
            
    