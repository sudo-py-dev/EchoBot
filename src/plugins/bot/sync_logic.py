from datetime import datetime
from loguru import logger
from pyrogram import Client, ContinuePropagation, filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType
from pyrogram.types import ChatMemberUpdated, Message
from sqlalchemy import delete, select

from src.core.context import get_context
from src.utils.decorators import safe_handler
from src.db.models.admin import Admin
from src.db.repos.admin_repo import AdminRepository


@Client.on_message(
    (filters.group | filters.channel) & (filters.text | filters.new_chat_members),
    group=-90,
)
@safe_handler
async def auto_register_chat(client: Client, message: Message):
    if message.chat is None:
        raise ContinuePropagation

    chat = message.chat
    logger.debug(f"Auto-registering chat {chat.id}, type: {chat.type}")

    ctx = get_context()
    async with ctx.db() as session:
        repo = AdminRepository(session)
        is_stale = await repo.is_check_stale(chat.id)
        if is_stale:
            logger.debug(f"Admin list stale for {chat.id}, fetching...")
            await fetch_chat_admins(client, chat)

    raise ContinuePropagation


@Client.on_chat_member_updated(group=-90)
@safe_handler
async def on_chat_member_updated(client: Client, update: ChatMemberUpdated):
    if update.chat.type == ChatType.PRIVATE:
        raise ContinuePropagation

    chat_id = update.chat.id
    user_id = (
        update.new_chat_member.user.id
        if update.new_chat_member
        else update.old_chat_member.user.id
    )

    new_status = update.new_chat_member.status if update.new_chat_member else None
    old_status = update.old_chat_member.status if update.old_chat_member else None

    if user_id == client.me.id:
        # Detected a change in the bot's own membership status
        if new_status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ] and old_status not in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ]:
            logger.debug(
                f"✨ Bot joined new {update.chat.type.name.lower()}: '{update.chat.title}' ({chat_id})"
            )
            await fetch_chat_admins(client, update.chat)
            raise ContinuePropagation

        if old_status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ] and new_status in [
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED,
        ]:
            logger.debug(f"Bot removed from chat {chat_id}, deleting admin records...")
            ctx = get_context()
            async with ctx.db() as session:
                repo = AdminRepository(session)
                await repo.delete_old_chat_admins(chat_id)

        raise ContinuePropagation

    was_admin = old_status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
    is_admin = new_status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}

    if not was_admin and is_admin:
        logger.debug(f"User {user_id} promoted to admin in chat {chat_id}")
        m = update.new_chat_member
        permissions = {}
        if m.privileges:
            permissions = {
                attr: getattr(m.privileges, attr, False)
                for attr in dir(m.privileges)
                if attr.startswith("can_")
            }
        await upsert_admin(
            chat_id,
            user_id,
            m.status.name.lower(),
            m.user.first_name,
            m.user.username,
            permissions,
            update.chat.title,
        )
        raise ContinuePropagation

    if was_admin and not is_admin:
        logger.debug(f"User {user_id} demoted/left/banned in chat {chat_id}")
        await remove_admin(chat_id, user_id)
        raise ContinuePropagation

    if was_admin and is_admin:
        logger.debug(f"User {user_id} admin privileges updated in chat {chat_id}")
        m = update.new_chat_member
        permissions = {}
        if m.privileges:
            permissions = {
                attr: getattr(m.privileges, attr, False)
                for attr in dir(m.privileges)
                if attr.startswith("can_")
            }
        await upsert_admin(
            chat_id,
            user_id,
            m.status.name.lower(),
            m.user.first_name,
            m.user.username,
            permissions,
            update.chat.title,
        )
        raise ContinuePropagation

    raise ContinuePropagation


async def upsert_admin(
    chat_id, user_id, status_name, first_name, username, permissions, chat_title
):
    ctx = get_context()
    async with ctx.db() as session:
        repo = AdminRepository(session)
        stmt = select(Admin).where(
            Admin.telegram_id == user_id,
            Admin.chat_id == chat_id,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.permissions = permissions
            existing.is_owner = status_name == "owner"
            existing.last_check = datetime.utcnow()
            existing.chat_title = chat_title
            existing.username = username
            session.add(existing)
        else:
            await repo.create(
                telegram_id=user_id,
                username=username,
                chat_id=chat_id,
                chat_title=chat_title,
                permissions=permissions,
                is_owner=status_name == "owner",
                is_active=True,
                last_check=datetime.utcnow(),
            )
        await session.commit()
        logger.debug(f"Upserted admin {user_id} for chat {chat_id}")


async def remove_admin(chat_id, user_id):
    ctx = get_context()
    async with ctx.db() as session:
        stmt = delete(Admin).where(
            Admin.telegram_id == user_id,
            Admin.chat_id == chat_id,
        )
        await session.execute(stmt)
        await session.commit()
        logger.debug(f"Removed admin {user_id} from chat {chat_id}")


async def fetch_chat_admins(client: Client, chat) -> None:
    try:
        logger.debug(f"Starting fetch_chat_admins for {chat.id}")
        ctx = get_context()
        async with ctx.db() as session:
            repo = AdminRepository(session)
            await repo.delete_old_chat_admins(chat.id)
            logger.debug(f"Cleared old admins for {chat.id}")

            count = 0
            async for member in client.get_chat_members(
                chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                permissions = {}
                if hasattr(member, "privileges") and member.privileges:
                    privileges = member.privileges
                    permissions = {
                        "can_change_info": getattr(
                            privileges, "can_change_info", False
                        ),
                        "can_post_messages": getattr(
                            privileges, "can_post_messages", False
                        ),
                        "can_edit_messages": getattr(
                            privileges, "can_edit_messages", False
                        ),
                        "can_delete_messages": getattr(
                            privileges, "can_delete_messages", False
                        ),
                        "can_invite_users": getattr(
                            privileges, "can_invite_users", False
                        ),
                        "can_restrict_members": getattr(
                            privileges, "can_restrict_members", False
                        ),
                        "can_pin_messages": getattr(
                            privileges, "can_pin_messages", False
                        ),
                        "can_manage_topics": getattr(
                            privileges, "can_manage_topics", False
                        ),
                        "can_promote_members": getattr(
                            privileges, "can_promote_members", False
                        ),
                        "can_manage_video_chats": getattr(
                            privileges, "can_manage_video_chats", False
                        ),
                        "is_anonymous": getattr(privileges, "is_anonymous", False),
                    }

                await repo.create(
                    telegram_id=member.user.id,
                    username=member.user.username,
                    chat_id=chat.id,
                    chat_title=chat.title,
                    permissions=permissions,
                    is_owner=member.status == ChatMemberStatus.OWNER,
                    is_active=True,
                    last_check=datetime.utcnow(),
                )
                count += 1
                logger.debug(f"Stored admin {member.user.id} for chat {chat.id}")

            logger.debug(f"Finished fetching {count} admins for chat {chat.id}")
    except Exception as e:
        logger.error(f"Error fetching admins for chat {chat.id}: {e}")
