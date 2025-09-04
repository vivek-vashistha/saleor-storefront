from enum import Enum


class LLMType(str, Enum):
    """Enum for different types of LLMs.

    Attributes:
        GPT4 (str): The type of GPT-4 LLM.
        GPT4o (str): The type of GPT-4o LLM.

    """

    GPT4 = "gpt-4"
    GPT4o = "gpt-4o"
