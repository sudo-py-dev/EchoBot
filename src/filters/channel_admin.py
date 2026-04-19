from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import Message
from src.core.context import get_context
from src.db.repos.admin_repo import AdminRepository


async def is_channel_admin(client: Client, chat_id: int, user_id: int) -> bool:
    ctx = get_context()
    async with ctx.db() as session:
        from sqlalchemy import select

        stmt = select(AdminRepository.model).where(
            AdminRepository.model.telegram_id == user_id,
            AdminRepository.model.chat_id == chat_id,
            AdminRepository.model.is_active,
        )
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        if admin:
            logger.debug(f"Admin cache hit for user {user_id} in chat {chat_id}")
            return True

    logger.debug(
        f"Admin cache miss for user {user_id} in chat {chat_id}, calling API..."
    )
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status.name in ["ADMINISTRATOR", "OWNER"]
        return is_admin
    except Exception as e:
        logger.error(
            f"Error checking admin status for user {user_id} in chat {chat_id}: {e}"
        )
        return False


async def async_channel_admin_filter(_, client: Client, message: Message) -> bool:
    if message.chat is None or message.from_user is None:
        return False
    return await is_channel_admin(client, message.chat.id, message.from_user.id)


filters.channel_admin = filters.create(async_channel_admin_filter, "ChannelAdminFilter")
