"""
UI utility functions and shared keyboard components for the EchoBot.
"""

from typing import Optional, List, Dict, Any

from loguru import logger
from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    KeyboardButtonRequestChat,
    Message,
    ReplyKeyboardMarkup,
    ChatAdministratorRights,
)

from src.utils.i18n import t

LANG_EMOJI = {
    "en": "🇺🇸",
    "ar": "🇸🇦",
    "he": "🇮🇱",
    "ru": "🇷🇺",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
    "tr": "🇹🇷",
    "it": "🇮🇹",
    "pt": "🇵🇹",
    "id": "🇮🇩",
    "hi": "🇮🇳",
    "uk": "🇺🇦",
    "pl": "🇵🇱",
    "nl": "🇳🇱",
    "zh": "🇨🇳",
    "ja": "🇯🇵",
    "ko": "🇰🇷",
    "vi": "🇻🇳",
    "th": "🇹🇭",
    "fa": "🇮🇷",
    "el": "🇬🇷",
    "ro": "🇷🇴",
    "hu": "🇭🇺",
    "cs": "🇨🇿",
}


def get_lang_emoji(lang_code: Optional[str]) -> str:
    """
    Returns the emoji flag corresponding to a language code.
    """
    if not lang_code:
        return "🌐"
    return LANG_EMOJI.get(lang_code.lower(), "🌐")


async def edit_or_reply(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    client: Client,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup = None,
    original_message: Message = None,
) -> None:
    """
    Attempts to edit a message, or sends a new one if editing fails.
    """
    try:
        await client.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup
        )
    except MessageNotModified:
        pass
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.debug(f"Failed to edit message {message_id} in {chat_id}: {e}")
        if original_message:
            await original_message.reply_text(text, reply_markup=reply_markup)
        else:
            await client.send_message(chat_id, text, reply_markup=reply_markup)


def get_forwarding_keyboard(
    settings: Any,
    dests: List[Dict[str, Any]],
    lang: str = "en",
    prefix: str = "mych_",
) -> InlineKeyboardMarkup:
    """
    Generates a keyboard for managing forwarding destinations.
    """
    buttons = [
        [
            InlineKeyboardButton(
                t(
                    "btn_service",
                    lang,
                    status=(
                        t("status_enabled", lang)
                        if settings.forward_enabled
                        else t("status_disabled", lang)
                    ),
                ),
                callback_data=f"{prefix}toggle_forward_{settings.channel_id}",
            )
        ]
    ]

    for d in dests:
        buttons.append(
            [
                InlineKeyboardButton(
                    get_lang_emoji(d.get("target_lang")),
                    callback_data=f"{prefix}nav_dest_lang_{d['id']}_{settings.channel_id}",
                ),
                InlineKeyboardButton(
                    f"📍 {d['title']}",
                    callback_data=f"{prefix}info_dest_{d['id']}_{settings.channel_id}",
                ),
                InlineKeyboardButton(
                    "🗑️",
                    callback_data=f"{prefix}del_dest_{d['id']}_{settings.channel_id}",
                ),
            ]
        )

    action_row = []
    if len(dests) < 3:
        action_row.append(
            InlineKeyboardButton(
                t("btn_add_dest", lang),
                callback_data=f"{prefix}nav_add_dest_{settings.channel_id}",
            )
        )

    action_row.append(
        InlineKeyboardButton(
            t("btn_set_credit", lang),
            callback_data=f"{prefix}nav_credit_{settings.channel_id}",
        )
    )
    buttons.append(action_row)

    buttons.append(
        [
            InlineKeyboardButton(
                t("btn_back", lang),
                callback_data=f"{prefix}nav_main_{settings.channel_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(buttons)


def get_languages_keyboard(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    channel_id: int | str | None = None,
    lang: str = "en",
    current_lang: Optional[str] = None,
    dest_id: Optional[int] = None,
    prefix: str = "mych_",
    back_callback: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Generates a language selection keyboard.
    """
    if isinstance(channel_id, str) and not channel_id.isdigit():
        prefix = channel_id
        channel_id = 0

    langs = [
        ("🇺🇸 English", "en"),
        ("🇦🇪 العربية", "ar"),
        ("🇮🇱 עברית", "he"),
        ("🇷🇺 Русский", "ru"),
        ("🇪🇸 Español", "es"),
        ("🇫🇷 Français", "fr"),
        ("🇩🇪 Deutsch", "de"),
        ("🇹🇷 Türkçe", "tr"),
        ("🇮🇹 Italiano", "it"),
        ("🇵🇹 Português", "pt"),
        ("🇮🇩 Indonesia", "id"),
        ("🇮🇳 हिन्दी", "hi"),
        ("🇺🇦 Українська", "uk"),
        ("🇵🇱 Polski", "pl"),
        ("🇳🇱 Nederlands", "nl"),
        ("🇨🇳 中文", "zh"),
        ("🇯🇵 日本語", "ja"),
        ("🇰🇷 한국어", "ko"),
        ("🇻🇳 Tiếng Việt", "vi"),
        ("🇹🇭 ไทย", "th"),
        ("🇮🇷 فارسی", "fa"),
        ("🇬🇷 Ελληνικά", "el"),
        ("🇷🇴 Română", "ro"),
        ("🇭🇺 Magyar", "hu"),
        ("🇨🇿 Čeština", "cs"),
        ("🇸🇪 Svenska", "sv"),
        ("🇩🇰 Dansk", "da"),
        ("🇫🇮 Suomi", "fi"),
        ("🇳🇴 Norsk", "no"),
        ("🇧🇬 Български", "bg"),
        ("🇸🇰 Slovenčina", "sk"),
        ("🇧🇩 বাংলা", "bn"),
        ("🇲🇾 Bahasa Melayu", "ms"),
        ("🇵🇭 Filipino", "tl"),
        ("🇮🇳 தமிழ்", "ta"),
    ]

    buttons = []

    if dest_id is not None:
        buttons.append(
            [
                InlineKeyboardButton(
                    t("btn_disable_translation", lang),
                    callback_data=f"{prefix}set_dest_lang_none_{dest_id}_{channel_id}",
                )
            ]
        )

    for i in range(0, len(langs), 2):
        pair = langs[i : i + 2]
        row = []
        for text, code in pair:
            display_text = f"✅ {text}" if code == current_lang else text

            # Determine callback data based on prefix and context
            if dest_id is not None:
                cb_data = f"{prefix}set_dest_lang_{code}_{dest_id}_{channel_id}"
            elif prefix == "set_user_lang_":
                cb_data = f"{prefix}{code}"
            else:
                cb_data = f"{prefix}set_lang_{code}_{channel_id}"

            row.append(InlineKeyboardButton(display_text, callback_data=cb_data))
        buttons.append(row)

    # Determine back button callback
    if back_callback:
        back_cb = back_callback
    elif prefix == "mych_" and dest_id is None:
        back_cb = "user_dash"
    elif prefix == "set_user_lang_":
        back_cb = "user_dash"
    else:
        back_cb = (
            f"{prefix}nav_cat_forward_{channel_id}"
            if dest_id is not None
            else f"{prefix}nav_main_{channel_id}"
        )

    buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data=back_cb)])
    return InlineKeyboardMarkup(buttons)


def get_settings_keyboard(settings, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Returns the settings keyboard for the admin panel.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("btn_forwarding", lang),
                    callback_data=f"settings_nav_cat_forward_{settings.channel_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    t("btn_cancel", lang), callback_data="settings_close"
                ),
            ],
        ]
    )


def get_main_keyboard(channel_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Returns the main keyboard for channel-specific settings in the user panel.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("btn_forwarding", lang),
                    callback_data=f"mych_cat_forward_{channel_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    t("btn_leave_channel", lang),
                    callback_data=f"mych_leave_{channel_id}",
                )
            ],
            [InlineKeyboardButton(t("btn_back_list", lang), callback_data="user_dash")],
        ]
    )


def get_user_dashboard_keyboard(
    channels: list[dict], lang: str, bot_username: str, page: int = 1, per_page: int = 5
) -> InlineKeyboardMarkup:
    """
    Returns the main user dashboard keyboard with a paginated list of channels.
    """
    total_channels = len(channels)
    total_pages = (total_channels + per_page - 1) // per_page
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1

    start = (page - 1) * per_page
    end = start + per_page
    current_channels = channels[start:end]

    buttons = []
    for c in current_channels:
        status_emoji = "✅" if c.get("forward_enabled", True) else "❌"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{status_emoji} {c['chat_title']}",
                    callback_data=f"mych_select_{c['chat_id']}",
                )
            ]
        )

    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    t("btn_prev", lang), callback_data=f"user_dash_{page - 1}"
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                f"{page}/{total_pages}", callback_data="user_dash_none"
            )
        )

        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    t("btn_next", lang), callback_data=f"user_dash_{page + 1}"
                )
            )
        buttons.append(nav_row)

    buttons.append(
        [
            InlineKeyboardButton(
                t("btn_refresh", lang),
                callback_data=f"user_refresh_{page}",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                t("btn_add_bot", lang),
                url=f"https://t.me/{bot_username}?startchannel=true&admin=post_messages",
            ),
            InlineKeyboardButton(
                t("btn_user_settings", lang),
                callback_data="user_settings",
            ),
        ]
    )
    return InlineKeyboardMarkup(buttons)


def get_add_target_keyboard(
    bot_username: str, channel_id: int, lang: str, back_callback: str
) -> InlineKeyboardMarkup:
    """
    Returns a keyboard for adding a target destination with an 'Open Private' button.
    """
    deep_link = f"https://t.me/{bot_username}?start=settings_{channel_id}"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("btn_open_private", lang), url=deep_link)],
            [InlineKeyboardButton(t("btn_back", lang), callback_data=back_callback)],
        ]
    )


def get_request_chat_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Returns a reply keyboard with a 'Select Channel' request chat button.
    """
    req_rights = ChatAdministratorRights(can_post_messages=True)
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(
                    t("btn_select_channel", lang),
                    request_chat=KeyboardButtonRequestChat(
                        button_id=1,
                        chat_is_channel=True,
                        user_administrator_rights=req_rights,
                        bot_administrator_rights=req_rights,
                        request_title=True,
                    ),
                )
            ],
            [KeyboardButton(t("btn_cancel", lang))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_cancel_keyboard(lang: str, back_callback: str) -> InlineKeyboardMarkup:
    """
    Returns an inline keyboard with a single 'Cancel' button.
    """
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("btn_cancel", lang), callback_data=back_callback)]]
    )
