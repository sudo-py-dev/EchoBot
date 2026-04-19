from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.all, group=-2)
async def log_message(client: Client, message: Message) -> None:
    """
    Middleware to log all incoming messages for debugging purposes.
    Has a negative group priority to ensure it runs before other handlers.
    """
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id if message.chat else None
    logger.debug(
        f"Incoming Update | User: {user_id}, Chat: {chat_id}, Msg: {message.id}"
    )
