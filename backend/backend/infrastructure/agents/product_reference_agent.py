import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.domain.entities import ChatState
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent

logger = logging.getLogger("conversational_commerce")


class ProductReferenceAgent(IAgent[ChatState]):
    """Agent for handling referenced products in the conversation context."""

    async def process(self, state: ChatState) -> ChatState:
        """Process the state with referenced products to provide relevant responses.

        Args:
            state: The current chat state with referenced products

        Returns:
            The updated chat state with potentially new messages or search queries
        """
        if not state.has_referenced_products:
            logger.info("No referenced products found in state, skipping ProductReferenceAgent")
            return state

        # Extract messages for context
        messages = state.messages
        products = state.referenced_products

        # Log the number of referenced products
        logger.info(f"Processing {len(products)} referenced products")

        # Create a formatted representation of the products for the prompt
        product_descriptions = "\n\n".join(
            [
                f"Product ID: {product.product_id}\n"
                f"Name: {product.name}\n"
                f"Category: {product.category}\n"
                f"Price: {product.price}\n"
                f"Description: {product.description}\n"
                f"Best For: {', '.join(product.best_for) if isinstance(product.best_for, list) else product.best_for}"
                for product in products
            ]
        )

        # Create prompt to generate a response based on the referenced products
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a helpful product expert (vitamins, supplements, sports nutrition, beauty, personal care, grocery).
                    You are given a conversation history and a list of products that have been referenced in the conversation.
                    Your task is to provide helpful context about these products and how they relate to the user's needs.

                    When responding, please follow these guidelines:
                    1. Acknowledge the products the user is referring to
                    2. Point out relevant features of the products that relate to the user's needs
                    3. If there are multiple products, compare them if appropriate
                    4. If you can identify any constraints or requirements from the conversation, mention how the products meet them
                    5. Do not invent features or specifications that aren't mentioned
                    6. Be concise but informative

                    Referenced products:
                    {product_descriptions}

                    DO NOT explicitly mention the concept of "referenced products" in your response. Simply incorporate the product information naturally in the context of the conversation.
                    Respond in a casual, helpful manner.
                    """,
                )
            ]
            + [(message["type"], message["content"]) for message in messages if message["type"] in {"human", "ai"}]
        )

        try:
            chain = prompt | self.llm | StrOutputParser()
            response = await chain.ainvoke({"product_descriptions": product_descriptions})
            # Add the response as an AI message
            state.add_message(response.strip(), is_human=False)

            return state
        except Exception as e:
            raise ServiceError(detail=f"Error in ProductReferenceAgent: {e}")
