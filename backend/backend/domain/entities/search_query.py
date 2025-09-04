from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Represents a search query with associated product categories.

    Attributes:
        query (str): The search query text
        categories (List[str]): List of product categories associated with the query

    """

    query: str = Field(description="The search query text")
    categories: list[str] = Field(
        default_factory=list, description="List of product categories associated with the query"
    )
