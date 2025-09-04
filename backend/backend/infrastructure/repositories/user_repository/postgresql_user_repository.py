import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.infrastructure.connections import IPostgresConnection
from backend.infrastructure.repositories.user_repository.interface import IUserRepository

logger = logging.getLogger("conversational_commerce")


class PostgreSQLUserRepository(IUserRepository):
    """PostgreSQL implementation of user repository."""

    def __init__(self, db_connection: IPostgresConnection):
        """Initialize the user repository.

        Args:
            db_connection: Database connection
        """
        self.db_connection = db_connection

    async def get_purchase_history(self, user_id: int) -> list[int]:
        """Get the product IDs that a user has purchased.

        Args:
            user_id: The user ID

        Returns:
            List of product IDs the user has purchased
        """

        async def execute_query(session: Session):
            query = f"SELECT product_id FROM orders WHERE user_id = {user_id};"
            result = session.execute(text(query))
            purchased_products = result.fetchall()
            return [int(row[0]) for row in purchased_products] if purchased_products else []

        try:
            return await self.db_connection.execute_db_operation(
                execute_query, error_message=f"Error fetching purchase history for user {user_id}"
            )
        except Exception as e:
            logger.error(f"Error fetching purchase history: {e}")
            return []

    async def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        """Get user information by ID.

        Args:
            user_id: The user ID

        Returns:
            Dictionary containing user information
        """

        async def execute_query(session: Session):
            query = f"SELECT * FROM users WHERE id = {user_id};"
            result = session.execute(text(query))
            user = result.fetchone()
            if user:
                return dict(user._mapping)
            return {}

        try:
            return await self.db_connection.execute_db_operation(
                execute_query, error_message=f"Error fetching user with ID {user_id}"
            )
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return {}
