from dependency_injector import containers, providers

from backend.application.services import OrderGraphService, OrderService, ProductService, SaleorService
from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
from backend.application.services.background_memory_manager import BackgroundMemoryManager
from backend.application.use_cases import (
    CreateChatSessionUseCase,
    CreateOrderUseCase,
    DeleteChatSessionUseCase,
    DeleteOrderUseCase,
    GetChatSessionUseCase,
    GetOrdersUseCase,
    GetProductsFromChatUseCase,
    GetUserSessionsUseCase,
    ProcessChatMessageUseCase,
    UpdateChatSessionUseCase,
    UpdateOrderUseCase,
)
from backend.application.use_cases.memory_management import (
    GetMemoryInsightsUseCase,
    ConsolidateUserMemoriesUseCase,
    InitializeUserMemoryUseCase,
    RetrieveRelevantMemoriesUseCase,
    UpdateUserProfileWithMemoriesUseCase,
    ScheduleMemoryConsolidationUseCase
)
from backend.application.workflows import SearchQueryWorkflow
from backend.application.workflows.enhanced_search_query_workflow import EnhancedSearchQueryWorkflow


class ApplicationContainer(containers.DeclarativeContainer):
    """Container for application layer components."""

    # Required dependencies from infrastructure layer
    agent_factory = providers.Dependency()
    product_repository = providers.Dependency()
    order_repository = providers.Dependency()
    chat_session_repository = providers.Dependency()
    saleor_connection = providers.Dependency()
    llm = providers.Dependency()
    ai_settings = providers.Dependency()

    # Memory Services
    semantic_memory_config = providers.Factory(
        SemanticMemoryConfig.from_ai_settings,
        ai_settings=ai_settings
    )

    semantic_memory_service = providers.Singleton(
        SemanticMemoryService,
        config=semantic_memory_config
    )

    background_memory_manager = providers.Singleton(
        BackgroundMemoryManager,
        semantic_memory_service=semantic_memory_service,
        chat_session_repository=chat_session_repository
    )

    # Workflows
    search_query_workflow = providers.Singleton(
        SearchQueryWorkflow,
        agent_factory=agent_factory,
    )

    enhanced_search_query_workflow = providers.Singleton(
        EnhancedSearchQueryWorkflow,
        llm=llm,
        semantic_memory_service=semantic_memory_service,
        background_memory_manager=background_memory_manager,
        agent_factory=agent_factory
    )

    # Services
    saleor_service = providers.Factory(
        SaleorService,
        saleor_connection=saleor_connection,
    )

    product_service = providers.Factory(
        ProductService,
        product_repository=product_repository,
        saleor_service=saleor_service,
        llm=llm,
    )

    order_service = providers.Factory(
        OrderService,
        order_repository=order_repository,
    )

    order_graph_service = providers.Factory(
        OrderGraphService,
        order_service=order_service,
    )

    # Use Cases
    get_products_from_chat_use_case = providers.Factory(
        GetProductsFromChatUseCase,
        product_repository=product_repository,
        workflow=search_query_workflow,
        product_service=product_service,
    )

    # Order Use Cases
    get_orders_use_case = providers.Factory(
        GetOrdersUseCase,
        order_repository=order_repository,
        order_service=order_service,
    )

    create_order_use_case = providers.Factory(
        CreateOrderUseCase,
        order_repository=order_repository,
        order_service=order_service,
    )

    update_order_use_case = providers.Factory(
        UpdateOrderUseCase,
        order_repository=order_repository,
        order_service=order_service,
    )

    delete_order_use_case = providers.Factory(
        DeleteOrderUseCase,
        order_repository=order_repository,
        order_service=order_service,
    )

    # Chat Session Use Cases
    create_chat_session_use_case = providers.Factory(
        CreateChatSessionUseCase,
        chat_session_repository=chat_session_repository,
    )

    get_chat_session_use_case = providers.Factory(
        GetChatSessionUseCase,
        chat_session_repository=chat_session_repository,
    )

    update_chat_session_use_case = providers.Factory(
        UpdateChatSessionUseCase,
        chat_session_repository=chat_session_repository,
    )

    get_user_sessions_use_case = providers.Factory(
        GetUserSessionsUseCase,
        chat_session_repository=chat_session_repository,
    )

    delete_chat_session_use_case = providers.Factory(
        DeleteChatSessionUseCase,
        chat_session_repository=chat_session_repository,
    )

    process_chat_message_use_case = providers.Factory(
        ProcessChatMessageUseCase,
        chat_session_repository=chat_session_repository,
        workflow=enhanced_search_query_workflow,  # Changed from search_query_workflow to enhanced_search_query_workflow
        product_service=product_service,
        order_graph_service=order_graph_service,
        llm=llm,
    )

    # Memory Management Use Cases
    get_memory_insights_use_case = providers.Factory(
        GetMemoryInsightsUseCase,
        background_memory_manager=background_memory_manager
    )

    consolidate_user_memories_use_case = providers.Factory(
        ConsolidateUserMemoriesUseCase,
        background_memory_manager=background_memory_manager
    )

    initialize_user_memory_use_case = providers.Factory(
        InitializeUserMemoryUseCase,
        semantic_memory_service=semantic_memory_service,
        chat_session_repository=chat_session_repository
    )

    retrieve_relevant_memories_use_case = providers.Factory(
        RetrieveRelevantMemoriesUseCase,
        chat_session_repository=chat_session_repository,
        semantic_memory_service=semantic_memory_service
    )

    update_user_profile_with_memories_use_case = providers.Factory(
        UpdateUserProfileWithMemoriesUseCase,
        chat_session_repository=chat_session_repository
    )

    schedule_memory_consolidation_use_case = providers.Factory(
        ScheduleMemoryConsolidationUseCase,
        background_memory_manager=background_memory_manager
    )
