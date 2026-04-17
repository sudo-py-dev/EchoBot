"""
Repository for managing user data and preferences.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from db.repos.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for managing User entities.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Retrieves a user by their Telegram ID.

        Args:
            telegram_id (int): The user's Telegram ID.

        Returns:
            User | None: The user instance or None if not found.
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self, telegram_id: int, username: Optional[str] = None
    ) -> User:
        """
        Gets a user by Telegram ID or creates a new one if it doesn't exist.
        Also updates the username if it has changed.

        Args:
            telegram_id (int): The user's Telegram ID.
            username (str, optional): The user's current Telegram username.

        Returns:
            User: The found or created user instance.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            if username and user.username != username:
                await self.update(user, username=username)
            return user
        return await self.create(telegram_id=telegram_id, username=username)

    async def set_language(self, user: User, language_code: str) -> User:
        """
        Updates the user's preferred language.

        Args:
            user (User): The user instance to update.
            language_code (str): The new ISO 639-1 language code.

        Returns:
            User: The updated user instance.
        """
        return await self.update(user, language_code=language_code)
