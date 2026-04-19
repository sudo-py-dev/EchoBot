"""
Repository for managing administrative actions and channel titles.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.admin import Admin
from src.db.models.channel_settings import ChannelSettings
from src.db.repos.base import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    """
    Repository for managing Admin entities, representing bot administrators
    and their permissions in chats.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Admin)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Admin]:
        """
        Retrieves an admin by their Telegram ID.

        Args:
            telegram_id (int): The admin's Telegram ID.

        Returns:
            Admin | None: The admin instance or None if not found.
        """
        stmt = select(Admin).where(Admin.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self, telegram_id: int, username: Optional[str] = None
    ) -> Admin:
        """
        Gets an admin or creates a new one if it doesn't exist.

        Args:
            telegram_id (int): The admin's Telegram ID.
            username (str, optional): The current Telegram username.

        Returns:
            Admin: The found or created admin instance.
        """
        admin = await self.get_by_telegram_id(telegram_id)
        if admin:
            return admin
        return await self.create(telegram_id=telegram_id, username=username)

    async def get_chat_title(self, chat_id: int) -> Optional[str]:
        """
        Retrieves the title of a chat from the admin records.

        Args:
            chat_id (int): The Telegram chat ID.

        Returns:
            str | None: The chat title or None if no record exists.
        """
        stmt = select(Admin.chat_title).where(Admin.chat_id == chat_id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_admins(self) -> list[Admin]:
        """
        Retrieves all active admins across all managed chats.

        Returns:
            list[Admin]: List of active admin records.
        """
        stmt = select(Admin).where(Admin.is_active)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_channels(self, user_id: int) -> list[dict]:
        """
        Retrieves a list of channels where the user is an admin and the bot is active.

        Args:
            user_id (int): The Telegram user ID.

        Returns:
            list[dict]: List of dictionaries containing chat_id, chat_title,
                       last_check, and forward_enabled status.
        """
        stmt = (
            select(
                Admin.chat_id,
                Admin.chat_title,
                Admin.last_check,
                ChannelSettings.forward_enabled,
            )
            .join(
                ChannelSettings,
                Admin.chat_id == ChannelSettings.channel_id,
                isouter=True,
            )
            .where(Admin.telegram_id == user_id, Admin.is_active)
            .distinct()
        )
        result = await self.session.execute(stmt)
        return [
            {
                "chat_id": row[0],
                "chat_title": row[1],
                "last_check": row[2],
                "forward_enabled": row[3] if row[3] is not None else True,
            }
            for row in result.all()
        ]

    async def delete_old_chat_admins(self, chat_id: int) -> None:
        """
        Removes all admin records for a specific chat.

        Args:
            chat_id (int): The Telegram chat ID.
        """
        stmt = delete(Admin).where(Admin.chat_id == chat_id)
        await self.session.execute(stmt)

    async def is_check_stale(self, chat_id: int, hours: int = 5) -> bool:
        """
        Checks if the admin status for a chat needs refreshing.

        Args:
            chat_id (int): The Telegram chat ID.
            hours (int): Number of hours after which a check is considered stale.

        Returns:
            bool: True if check is stale or missing, False otherwise.
        """

        stmt = (
            select(Admin.last_check)
            .where(Admin.chat_id == chat_id)
            .order_by(Admin.last_check.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        last_check = result.scalar_one_or_none()
        if not last_check:
            return True

        # Assume last_check is UTC
        if last_check.tzinfo is None:
            last_check = last_check.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) - last_check > timedelta(hours=hours)

    async def deactivate_chat(self, chat_id: int) -> None:
        """
        Marks all admin records for a chat as inactive.

        Args:
            chat_id (int): The Telegram chat ID.
        """
        stmt = update(Admin).where(Admin.chat_id == chat_id).values(is_active=False)
        await self.session.execute(stmt)
