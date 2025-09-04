from abc import ABC, abstractmethod

from langgraph.graph.state import CompiledStateGraph

from backend.infrastructure.factories import AgentFactory


class IWorkflow(ABC):
    """Base interface for all workflows.

    This interface defines the basic methods that all workflows should implement.
    It is parameterized with a state type to allow for different state structures
    in different workflows.
    """

    def __init__(self, agent_factory: AgentFactory):
        """Initialize the workflow with a default graph."""
        self.agent_factory = agent_factory
        self.graph = self._build_graph()

    @abstractmethod
    def _build_graph(self) -> CompiledStateGraph:
        """Build the workflow graph.

        This method should define the nodes and edges of the workflow graph,
        including the entry point and any conditional branches.

        Returns:
            The compiled workflow graph
        """
        pass
