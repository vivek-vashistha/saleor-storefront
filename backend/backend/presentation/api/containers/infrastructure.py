from dependency_injector import containers, providers

from backend.infrastructure.connections import (
    MongoDBConfig,
    MongoDBConnection,
    Neo4jConfig,
    Neo4jConnection,
    QdrantConfig,
    QdrantConnection,
    SaleorConfig,
    SaleorConnection,
)
from backend.infrastructure.factories import AgentFactory, EmbeddingFactory, LLMFactory
from backend.infrastructure.repositories import MongoDBChatSessionRepository, SaleorOrderRepository, Neo4jProductRepository, QdrantProductRepository
from backend.settings import AISettings, MongoDBSettings, Neo4jSettings, QdrantSettings, SaleorSettings, WeatherSettings


class InfrastructureContainer(containers.DeclarativeContainer):
    """Container for infrastructure layer components."""

    # Settings Injections
    config = providers.Configuration(
        pydantic_settings=[
            AISettings(),
            WeatherSettings(),
            QdrantSettings(),
            MongoDBSettings(),
            Neo4jSettings(),
            SaleorSettings(),
        ]
    )

    # External services
    llm = providers.Factory(
        LLMFactory.create_llm,
        llm_type=config.MODEL_NAME,
        api_key=config.OPENAI_API_KEY,
    )
    open_ai_small_embedding_model = providers.Singleton(
        EmbeddingFactory.create_embedding_model,
        model_type=config.EMBEDDING_MODEL_NAME,
        api_key=config.OPENAI_API_KEY,
    )

    # Qdrant Connection Config
    products_qdrant_config = providers.Singleton(
        QdrantConfig,
        host=config.QDRANT_HOST,
        port=config.QDRANT_PORT,
        api_key=config.QDRANT_API_KEY,
        collection="products",
        vector_size=open_ai_small_embedding_model.provided.dimension,
        prefer_grpc=config.QDRANT_PREFER_GRPC,
        timeout=config.QDRANT_TIMEOUT,
    )
    qdrant_connection = providers.Singleton(
        QdrantConnection,
        config=products_qdrant_config,
        embeddings_model=open_ai_small_embedding_model,
    )

    # MongoDB Connection Config
    mongodb_config = providers.Singleton(
        MongoDBConfig,
        host=config.MONGODB_HOST,
        port=config.MONGODB_PORT,
        user=config.MONGODB_USER,
        password=config.MONGODB_PASS,
        database=config.MONGODB_NAME,
    )
    mongodb_connection = providers.Singleton(
        MongoDBConnection,
        config=mongodb_config,
    )

    # Neo4j Connection Config
    neo4j_config = providers.Singleton(
        Neo4jConfig,
        uri=config.NEO4J_URI,
        username=config.NEO4J_USERNAME,
        password=config.NEO4J_PASSWORD,
        database=config.NEO4J_DATABASE,
        vector_index_name=config.NEO4J_VECTOR_INDEX_NAME,
        fulltext_index_name=config.NEO4J_FULLTEXT_INDEX_NAME,
    )
    neo4j_connection = providers.Singleton(
        Neo4jConnection,
        config=neo4j_config,
    )

    # Saleor Connection Config
    saleor_config = providers.Singleton(
        SaleorConfig,
        host=config.SALEOR_HOST,
        port=config.SALEOR_PORT,
        timeout=config.SALEOR_TIMEOUT,
    )
    saleor_connection = providers.Singleton(
        SaleorConnection,
        config=saleor_config,
    )

    # Repositories
    # Vector-based product repository (Qdrant)
    qdrant_product_repository = providers.Singleton(
        QdrantProductRepository,
        connection=qdrant_connection,
    )

    # Graph-based product repository (Neo4j)
    neo4j_product_repository = providers.Singleton(
        Neo4jProductRepository,
        connection=neo4j_connection,
        embedding_model=open_ai_small_embedding_model,
    )

    # Chat session repository
    chat_session_repository = providers.Singleton(
        MongoDBChatSessionRepository,
        connection=mongodb_connection,
    )

    # Order repository
    order_repository = providers.Singleton(
        SaleorOrderRepository,
        connection=mongodb_connection,
    )

    # Agent Factory
    agent_factory = providers.Singleton(AgentFactory, llm=llm)
