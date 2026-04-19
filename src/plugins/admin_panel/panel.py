"""
Admin panel plugin for managing channel settings directly from the chat.
"""

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    Message,
    ForceReply,
    ReplyKeyboardRemove,
)
from pyrogram.errors import RPCError

from src.core.context import get_context
from src.db.repos.admin_repo import AdminRepository
from src.db.repos.channel_settings_repo import ChannelSettingsRepository
from src.utils.i18n import t, get_lang_for_user
from src.utils.decorators import safe_handler, admin_only
from src.utils.ui import (
    edit_or_reply,
    get_forwarding_keyboard,
    get_languages_keyboard,
    get_settings_keyboard,
    get_add_target_keyboard,
)
from src.plugins.user_panel.panel import (
    input_capture_state,
    clear_input_capture,
)


@Client.on_message(filters.command("settings"))
@safe_handler
@admin_only
async def cmd_settings(client: Client, message: Message) -> None:
    """
    Handles the /settings command in groups/channels.
    Only accessible to admins.
    """
    if message.chat is None or message.from_user is None:
        return

    lang = await get_lang_for_user(message.from_user.id)
    ctx = get_context()
    async with ctx.db() as session:
        repo = ChannelSettingsRepository(session)
        settings = await repo.get_or_create(message.chat.id)
        keyboard = get_settings_keyboard(settings, lang)
        await message.reply_text(
            t(
                "menu_main",
                lang,
                title=message.chat.title or str(message.chat.id),
                channel_id=message.chat.id,
            ),
            reply_markup=keyboard,
        )


@Client.on_callback_query(filters.regex("^settings_"))
@safe_handler
async def settings_callback(client: Client, callback: CallbackQuery) -> None:
    """
    Handles callbacks from the settings menu.
    """
    if callback.from_user is None or callback.message is None:
        return

    data = callback.data
    parts = data.split("_")
    action = parts[1]

    sub_action = parts[2] if len(parts) > 2 else None
    channel_id = (
        int(parts[-1])
        if parts[-1].isdigit()
        or (parts[-1].startswith("-") and parts[-1][1:].isdigit())
        else None
    )

    lang = await get_lang_for_user(callback.from_user.id)
    ctx = get_context()
    async with ctx.db() as session:
        repo = ChannelSettingsRepository(session)

        # Handle close action first as it doesn't need channel_id
        if action == "close":
            await callback.message.delete()
            return

        if channel_id is None:
            await callback.answer("❌ Invalid Callback data", show_alert=True)
            return

        settings = await repo.get_or_create(channel_id)

        if action == "info":
            admin_repo = AdminRepository(session)
            dest_id = int(parts[3])
            title = await admin_repo.get_chat_title(dest_id) or "Channel"
            await callback.answer(f"📍 {title}", show_alert=True)
            return

        if action == "toggle":
            if sub_action == "forward":
                await repo.update(
                    settings, forward_enabled=not settings.forward_enabled
                )
                await callback.answer(
                    t(
                        "status_enabled"
                        if not settings.forward_enabled
                        else "status_disabled",
                        lang,
                    )
                )
                dests = repo.get_destinations_list(settings)
                await callback.message.edit_reply_markup(
                    reply_markup=get_forwarding_keyboard(
                        settings, dests, lang, prefix="settings_"
                    )
                )
            return

        elif action == "nav":
            if sub_action == "cat" and parts[3] == "forward":
                admin_repo = AdminRepository(session)
                source_title = await admin_repo.get_chat_title(channel_id) or str(
                    channel_id
                )
                dests = repo.get_destinations_list(settings)
                kb = get_forwarding_keyboard(settings, dests, lang, prefix="settings_")
                await callback.message.edit_text(
                    t("menu_forwarding", lang, title=source_title), reply_markup=kb
                )
                return

            elif sub_action == "main":
                admin_repo = AdminRepository(session)
                source_title = await admin_repo.get_chat_title(channel_id) or str(
                    channel_id
                )
                kb = get_settings_keyboard(settings, lang)
                await callback.message.edit_text(
                    t("menu_main", lang, title=source_title, channel_id=channel_id),
                    reply_markup=kb,
                )
                return

            elif sub_action == "add":
                await callback.message.edit_text(
                    t("msg_add_dest", lang),
                    reply_markup=get_add_target_keyboard(
                        client.me.username,
                        channel_id,
                        lang,
                        f"settings_nav_cat_forward_{channel_id}",
                    ),
                )
                return
            elif sub_action == "credit":
                await callback.message.edit_text(
                    t("msg_set_credit", lang),
                    reply_markup=ForceReply(selective=True),
                )
                return
            elif sub_action == "dest":
                if parts[3] == "lang":
                    dest_id = int(parts[4])
                    dests = repo.get_destinations_list(settings)
                    current_dest_lang = next(
                        (d.get("target_lang") for d in dests if d["id"] == dest_id),
                        None,
                    )
                    kb = get_languages_keyboard(
                        channel_id,
                        lang,
                        current_lang=current_dest_lang,
                        dest_id=dest_id,
                        prefix="settings_",
                    )
                    await callback.message.edit_text(
                        t("menu_select_translation_lang", lang),
                        reply_markup=kb,
                    )
                return

        elif action == "set":
            if sub_action == "dest":
                if parts[3] == "lang":
                    lang_code = parts[4]
                    dest_id = int(parts[5])
                    target_lang = None if lang_code.lower() == "none" else lang_code
                    await repo.set_dest_language(settings, dest_id, target_lang)
                    await callback.answer(
                        t(
                            "msg_lang_set_to",
                            lang,
                            lang=(target_lang.upper() if target_lang else "OFF"),
                        )
                    )
                    kb = get_languages_keyboard(
                        channel_id,
                        lang,
                        current_lang=target_lang,
                        dest_id=dest_id,
                        prefix="settings_",
                    )
                    try:
                        await callback.message.edit_reply_markup(reply_markup=kb)
                    except RPCError:
                        pass
            return

        elif action == "del":
            if sub_action == "dest":
                dest_id = int(parts[3])
                await repo.remove_destination(settings, dest_id)
                await callback.answer("🗑️")
                admin_repo = AdminRepository(session)
                source_title = await admin_repo.get_chat_title(channel_id) or str(
                    channel_id
                )
                dests = repo.get_destinations_list(settings)
                kb = get_forwarding_keyboard(settings, dests, lang, prefix="settings_")
                await callback.message.edit_text(
                    t("menu_forwarding", lang, title=source_title), reply_markup=kb
                )
                return

        elif action == "close":
            await callback.message.delete()
            return

        admin_repo = AdminRepository(session)
        source_title = await admin_repo.get_chat_title(channel_id) or str(channel_id)
        kb = get_settings_keyboard(settings, lang)
        await callback.message.edit_text(
            t("menu_main", lang, title=source_title, channel_id=channel_id),
            reply_markup=kb,
        )


@Client.on_message(filters.text & filters.reply)
@safe_handler
async def handle_settings_input(client: Client, message: Message) -> None:
    if message.reply_to_message is None or message.from_user is None:
        return

    reply_text = message.reply_to_message.text
    if not reply_text:
        return

    if any(
        t("msg_set_credit", lang_code) in reply_text
        for lang_code in ["en", "ar", "iw", "ru", "es", "fr", "de", "tr"]
    ):
        await handle_credit_input(client, message)


@safe_handler
async def handle_credit_input(client: Client, message: Message) -> None:
    """
    Processes the custom credit text input from the user.
    """
    credit_text = (
        getattr(message.text, "markdown", message.text).strip() if message.text else ""
    )
    lang = await get_lang_for_user(message.from_user.id)

    if message.chat.type == "private":
        await message.reply_text(t("err_only_in_chat", lang))
        return

    ctx = get_context()
    async with ctx.db() as session:
        repo = ChannelSettingsRepository(session)
        settings = await repo.get_or_create(message.chat.id)
        await repo.update(settings, credit_text=credit_text)

        admin_repo = AdminRepository(session)
        source_title = await admin_repo.get_chat_title(message.chat.id) or str(
            message.chat.id
        )

        try:
            await message.delete()
        except RPCError:
            pass

        dests = repo.get_destinations_list(settings)
        await edit_or_reply(
            client,
            message.chat.id,
            message.reply_to_message.id,
            t("menu_forwarding", lang, title=source_title),
            reply_markup=get_forwarding_keyboard(
                settings, dests, lang, prefix="settings_"
            ),
            original_message=message,
        )


@Client.on_message(filters.private & filters.text & filters.regex("^/cancel$"))
@safe_handler
async def handle_cancel_cmd(client: Client, message: Message) -> None:
    await handle_cancel(client, message)


@Client.on_message(filters.private & filters.text)
@safe_handler
async def handle_cancel_text(client: Client, message: Message) -> None:
    lang = await get_lang_for_user(message.from_user.id)
    if message.text == t("btn_cancel", lang):
        await handle_cancel(client, message)
        return
    message.continue_propagation()


@safe_handler
async def handle_cancel(client: Client, message: Message) -> None:
    state = input_capture_state.get(message.from_user.id)
    if not state:
        return

    lang = await get_lang_for_user(message.from_user.id)
    ctx = get_context()
    async with ctx.db() as session:
        repo = ChannelSettingsRepository(session)
        settings = await repo.get_or_create(state["channel_id"])
        admin_repo = AdminRepository(session)
        source_title = await admin_repo.get_chat_title(state["channel_id"]) or str(
            state["channel_id"]
        )
        dests = repo.get_destinations_list(settings)
        await edit_or_reply(
            client,
            message.from_user.id,
            state["prompt_msg_id"],
            t("menu_forwarding", lang, title=source_title),
            reply_markup=get_forwarding_keyboard(
                settings, dests, lang, prefix="settings_"
            ),
            original_message=message,
        )

    await clear_input_capture(message.from_user.id)
    try:
        await message.delete()
    except (RPCError, Exception):
        pass
    msg = await message.reply_text(
        t("input_mode_closed", lang), reply_markup=ReplyKeyboardRemove()
    )
    await msg.delete()
