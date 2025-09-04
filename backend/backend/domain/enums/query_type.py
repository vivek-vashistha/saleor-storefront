from enum import Enum


class QueryType(str, Enum):
    """Enum representing the types of queries that can be processed."""

    PRODUCT = "product"
    PLANNING = "planning"
    UNKNOWN = "unknown"
