from dependency_injector import containers, providers

from backend.presentation.api.containers.application import ApplicationContainer
from backend.presentation.api.containers.infrastructure import InfrastructureContainer


class Container(containers.DeclarativeContainer):
    """Main container that composes all layer containers with explicit dependencies."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "backend.presentation.api.routes.v1.chat",
            "backend.presentation.api.routes.v1.session",
            "backend.presentation.api.routes.welcome_router",
        ]
    )

    # Infrastructure layer container
    infrastructure = providers.Container(InfrastructureContainer)
    infrastructure.check_dependencies()

    # Application layer container with explicit dependencies
    application = providers.Container(
        ApplicationContainer,
        agent_factory=infrastructure.agent_factory,
        product_repository=infrastructure.neo4j_product_repository,
        order_repository=infrastructure.order_repository,
        chat_session_repository=infrastructure.chat_session_repository,
        saleor_connection=infrastructure.saleor_connection,
    )
    application.check_dependencies()
