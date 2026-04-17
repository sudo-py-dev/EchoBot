from pyrogram import filters
from pyrogram.types import Message
from config import config


def owner_filter(_, __, message: Message) -> bool:
    if message.from_user is None:
        return False
    return message.from_user.id in config.owner_ids


def admin_filter(_, __, message: Message) -> bool:
    if message.from_user is None:
        return False
    return (
        message.from_user.id in config.owner_ids
        or message.from_user.id in config.admin_ids
    )


filters.owner = filters.create(owner_filter, "OwnerFilter")
filters.bot_admin = filters.create(admin_filter, "BotAdminFilter")
