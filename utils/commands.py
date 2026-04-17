"""
Utility functions for managing Telegram bot commands.
"""

from loguru import logger
from pyrogram import Client
from pyrogram.types import BotCommand, BotCommandScopeChat
from utils.i18n import t


async def update_user_commands(client: Client, user_id: int, lang: str) -> None:
    """
    Updates the bot commands for a specific user based on their language.
    """
    commands = [
        BotCommand("start", t("cmd_start", lang)),
        BotCommand("about", t("cmd_about", lang)),
        BotCommand("donate", t("cmd_donate", lang)),
    ]

    try:
        await client.set_bot_commands(
            commands=commands, scope=BotCommandScopeChat(chat_id=user_id)
        )
    except Exception as e:
        logger.error(f"Failed to set bot commands for user {user_id}: {e}")
