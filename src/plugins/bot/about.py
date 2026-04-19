"""
Plugin for informational commands like /about.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, LinkPreviewOptions

from src.config import config
from src.utils.decorators import safe_handler
from src.utils.i18n import t, get_lang_for_user


@Client.on_message(filters.command("about"))
@safe_handler
async def cmd_about(client: Client, message: Message) -> None:
    """
    Shows information about the bot, its version, developer, and tech stack.
    """
    lang = await get_lang_for_user(message.from_user.id)

    # Format the tech stack localized
    tech_stack = "\n".join(
        [
            f"• **{t(f'tech_{key}', lang)}**: {value}"
            for key, value in config.TECH_STACK.items()
        ]
    )

    text = t(
        "menu_about",
        lang,
        version=config.VERSION,
        dev_name=config.DEV_NAME,
        repo_url=config.GITHUB_URL,
        tech_stack=tech_stack,
        bot_name=client.me.first_name,
    )

    await message.reply_text(
        text,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
