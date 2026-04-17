"""
Repository for managing channel-specific settings and forwarding destinations.
"""

import json
from typing import List, Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.channel_settings import ChannelSettings
from db.repos.base import BaseRepository


class ChannelSettingsRepository(BaseRepository[ChannelSettings]):
    """
    Repository for managing channel-specific settings, including forwarding destinations.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ChannelSettings)

    async def get_by_channel_id(self, channel_id: int) -> Optional[ChannelSettings]:
        """
        Retrieves settings for a specific channel.

        Args:
            channel_id (int): The Telegram chat ID of the channel.

        Returns:
            ChannelSettings | None: The settings instance or None if not found.
        """
        stmt = select(ChannelSettings).where(ChannelSettings.channel_id == channel_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, channel_id: int) -> ChannelSettings:
        """
        Gets channel settings or creates default ones if they don't exist.

        Args:
            channel_id (int): The Telegram chat ID.

        Returns:
            ChannelSettings: The found or created settings instance.
        """
        settings = await self.get_by_channel_id(channel_id)
        if settings:
            return settings
        return await self.create(channel_id=channel_id)

    async def add_destination(
        self, settings: ChannelSettings, dest_id: int, title: str
    ) -> int:
        """
        Adds a forwarding destination to the channel settings.

        Args:
            settings (ChannelSettings): The settings instance to update.
            dest_id (int): The ID of the target channel.
            title (str): Friendly title for the target channel.

        Returns:
            int: Status code:
                0: Success
                1: Destination already exists
                2: Destination limit reached (max 3)
        """
        try:
            dests: List[Dict] = json.loads(settings.destinations or "[]")
        except Exception:
            dests = []

        if any(d["id"] == dest_id for d in dests):
            return 1

        if len(dests) >= 3:
            return 2

        dests.append({"id": dest_id, "title": title, "target_lang": None})
        await self.update(settings, destinations=json.dumps(dests))
        return 0

    async def remove_destination(self, settings: ChannelSettings, dest_id: int) -> bool:
        """
        Removes a forwarding destination.

        Args:
            settings (ChannelSettings): The settings instance.
            dest_id (int): The ID of the target channel to remove.

        Returns:
            bool: True if removed, False if not found.
        """
        try:
            dests: List[Dict] = json.loads(settings.destinations or "[]")
        except Exception:
            return False

        updated = [d for d in dests if d["id"] != dest_id]
        if len(updated) == len(dests):
            return False

        await self.update(settings, destinations=json.dumps(updated))
        return True

    def get_destinations_list(self, settings: ChannelSettings) -> List[Dict]:
        """
        Parses the JSON destinations string into a list of dictionaries.

        Args:
            settings (ChannelSettings): The settings instance.

        Returns:
            List[Dict]: List of destination objects.
        """
        if not settings.destinations:
            return []
        try:
            data = json.loads(settings.destinations)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    async def set_dest_language(
        self, settings: ChannelSettings, dest_id: int, target_lang: str | None
    ) -> bool:
        """
        Sets the target translation language for a specific destination.

        Args:
            settings (ChannelSettings): The settings instance.
            dest_id (int): The ID of the destination channel.
            target_lang (str, optional): ISO 639-1 language code or None to disable.

        Returns:
            bool: True if updated, False if destination not found.
        """
        try:
            dests: List[Dict] = json.loads(settings.destinations or "[]")
        except json.JSONDecodeError:
            return False

        updated = False
        for d in dests:
            if d["id"] == dest_id:
                d["target_lang"] = target_lang
                updated = True
                break

        if not updated:
            return False

        await self.update(settings, destinations=json.dumps(dests))
        return True

    async def delete_settings(self, channel_id: int) -> bool:
        """
        Deletes settings for a channel.

        Args:
            channel_id (int): The channel chat ID.

        Returns:
            bool: True if deleted, False if settings not found.
        """
        settings = await self.get_by_channel_id(channel_id)
        if not settings:
            return False
        await self.session.delete(settings)
        await self.session.commit()
        return True
