from enum import Enum, auto


class AgentType(str, Enum):
    """Enum for different types of agents."""

    SEARCH_QUERY = auto()
    SUFFICIENT_DETAIL = auto()
    CONVERSATION_ENRICHMENT = auto()
    CONVERSATION_SATURATION = auto()
    GREETING_DETECTION = auto()
    PRODUCT_REFERENCE = auto()
    USER_PROFILE_EXTRACTION = auto()
