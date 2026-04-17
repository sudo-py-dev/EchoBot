"""Reusable handler decorators for all plugins."""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pyrogram import Client, ContinuePropagation, StopPropagation
from pyrogram.enums import ChatType
from pyrogram.types import Message

from custom_filters.channel_admin import is_channel_admin
from utils.i18n import at

Handler = Callable[..., Awaitable[None]]


def admin_only(func: Handler) -> Handler:
    """Silently ignore the command if the sender is not a group admin."""

    @functools.wraps(func)
    async def wrapper(
        client: Client, message: Message, *args: Any, **kwargs: Any
    ) -> None:
        if not message.from_user:
            return
        if message.chat.type == ChatType.PRIVATE:
            await func(client, message, *args, **kwargs)
            return
        if not await is_channel_admin(client, message.chat.id, message.from_user.id):
            await message.reply_text(await at(message.from_user.id, "err_no_admin"))
            return
        await func(client, message, *args, **kwargs)

    return wrapper


def safe_handler(func: Handler) -> Handler:
    """Catch all unhandled exceptions inside a handler — never crash the bot."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            await func(*args, **kwargs)
        except (StopPropagation, ContinuePropagation):
            raise
        except Exception as e:
            logger.error(f"Handler {func.__name__} failed: {e}")

    return wrapper
