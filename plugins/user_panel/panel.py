"""
User panel plugin for managing personal channels and forwarding settings.
"""

import contextlib
from loguru import logger
from pyrogram import Client, filters
from pyrogram.errors import RPCError, MessageNotModified
from pyrogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)

from custom_filters.channel_admin import is_channel_admin
from core.context import get_context
from db.repos.admin_repo import AdminRepository
from db.repos.channel_settings_repo import ChannelSettingsRepository
from db.repos.user_repo import UserRepository
from utils.i18n import t, get_lang_for_user
from utils.decorators import safe_handler
from utils.commands import update_user_commands
from utils.ui import (
    edit_or_reply,
    get_forwarding_keyboard,
    get_languages_keyboard,
    get_main_keyboard,
    get_user_dashboard_keyboard,
    get_request_chat_keyboard,
    get_cancel_keyboard,
)

input_capture_state = {}


def is_waiting_for_input(fields: str | list[str] | None = None):
    """
    Filter to check if a user is currently being prompted for input.

    Args:
        fields (str or list[str], optional): specific input fields to filter for.
    """

    async def func(flt, client, message: Message) -> bool:
        if not message.from_user:
            return False
        state = input_capture_state.get(message.from_user.id)
        if not state:
            return False

        current_field = state.get("field")
        filter_fields = getattr(flt, "fields", None)
        if filter_fields:
            allowed = (
                [filter_fields] if isinstance(filter_fields, str) else filter_fields
            )
            if current_field not in allowed:
                return False
        message.input_state = state
        return True

    return filters.create(func, fields=fields)


async def capture_next_input(
    user_id: int, channel_id: int, field: str, prompt_msg_id: int, kb_msg_id: int = None
) -> None:
    """
    Sets the state to capture the next message from the user as input.
    """
    input_capture_state[user_id] = {
        "channel_id": channel_id,
        "field": field,
        "prompt_msg_id": prompt_msg_id,
        "kb_msg_id": kb_msg_id,
    }


async def clear_input_capture(user_id: int) -> None:
    """Clears the input capture state for a user."""
    if user_id in input_capture_state:
        del input_capture_state[user_id]


@Client.on_message(filters.private & filters.command("start"))
@safe_handler
async def cmd_start(client: Client, message: Message) -> None:
    """
    Handles the /start command. Onboards new users by asking for language
    and shows the dashboard to returning users.
    """
    lang = await get_lang_for_user(message.from_user.id)
    ctx = get_context()
    async with ctx.db() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            message.from_user.id, message.from_user.username
        )
        # If user has no language set yet, show language selector
        if not user.language_code:
            await message.reply_text(
                t("welcome_start", bot_name=client.me.first_name),
                reply_markup=get_languages_keyboard(prefix="set_user_lang_"),
            )
            return

        if len(message.command) > 1:
            param = message.command[1]
            if param.startswith("settings_"):
                try:
                    channel_id = int(param.split("_")[1])
                    is_admin = await is_channel_admin(
                        client, channel_id, message.from_user.id
                    )
                    if not is_admin:
                        await message.reply_text(t("err_no_admin", lang))
                        return

                    admin_repo = AdminRepository(session)
                    title = await admin_repo.get_chat_title(channel_id) or str(
                        channel_id
                    )

                    await message.reply_text(
                        t("menu_main", lang, title=title, channel_id=channel_id),
                        reply_markup=get_main_keyboard(channel_id, lang),
                    )
                    return
                except Exception:
                    pass

        repo = AdminRepository(session)
        channels = await repo.get_user_channels(message.from_user.id)
        await message.reply_text(
            t("menu_user_dashboard", lang),
            reply_markup=get_user_dashboard_keyboard(
                channels, lang, bot_username=client.me.username
            ),
        )


@Client.on_callback_query(filters.regex("^set_user_lang_"))
@safe_handler
async def set_user_lang_callback(client: Client, callback: CallbackQuery) -> None:
    new_lang = callback.data.split("_")[-1]
    logger.debug(f"Setting user language to {new_lang}")

    ctx = get_context()
    async with ctx.db() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            callback.from_user.id, callback.from_user.username
        )
        await user_repo.set_language(user, new_lang)

        # Update bot commands in the new language
        await update_user_commands(client, callback.from_user.id, new_lang)

        admin_repo = AdminRepository(session)
        channels = await admin_repo.get_user_channels(callback.from_user.id)

    await callback.answer(t("language_set", new_lang, lang=new_lang.upper()))

    is_settings = bool(
        callback.message.reply_markup
        and any(
            btn.callback_data == "user_dash"
            for row in getattr(callback.message.reply_markup, "inline_keyboard", [])
            for btn in row
        )
    )

    if is_settings:
        try:
            await callback.message.edit_text(
                t("select_language", new_lang),
                reply_markup=get_languages_keyboard(
                    prefix="set_user_lang_",
                    back_callback="user_dash",
                    lang=new_lang,
                    current_lang=new_lang,
                ),
            )
        except MessageNotModified:
            pass
    else:
        try:
            await callback.message.edit_text(
                t("menu_user_dashboard", new_lang),
                reply_markup=get_user_dashboard_keyboard(
                    channels, new_lang, bot_username=client.me.username
                ),
            )
        except MessageNotModified:
            pass


@Client.on_callback_query(filters.regex("^user_"))
@safe_handler
async def user_callback(client: Client, callback: CallbackQuery) -> None:
    data = callback.data.split("_")
    action = data[1]
    lang = await get_lang_for_user(callback.from_user.id)
    ctx = get_context()
    async with ctx.db() as session:
        if action == "settings":
            try:
                await callback.message.edit_text(
                    t("select_language", lang),
                    reply_markup=get_languages_keyboard(
                        prefix="set_user_lang_",
                        back_callback="user_dash",
                        lang=lang,
                        current_lang=lang,
                    ),
                )
            except MessageNotModified:
                pass
        elif action == "dash":
            page = 1
            if len(data) > 2:
                try:
                    page = int(data[2])
                except ValueError:
                    page = 1

            repo = AdminRepository(session)
            channels = await repo.get_user_channels(callback.from_user.id)
            try:
                await callback.message.edit_text(
                    t("menu_user_dashboard", lang),
                    reply_markup=get_user_dashboard_keyboard(
                        channels, lang, bot_username=client.me.username, page=page
                    ),
                )
            except MessageNotModified:
                pass
        elif action == "dash_none":
            await callback.answer()


@Client.on_callback_query(filters.regex("^mych_"))
@safe_handler
async def mych_callback(client: Client, callback: CallbackQuery) -> None:
    """
    Handles callbacks related to specific channel settings (e.g., info, toggle, nav).
    """
    data = callback.data.split("_")
    action = data[1]
    lang = await get_lang_for_user(callback.from_user.id)
    ctx = get_context()
    async with ctx.db() as session:
        if action == "dash":
            repo = AdminRepository(session)
            channels = await repo.get_user_channels(callback.from_user.id)
            await callback.message.edit_text(
                t("menu_user_dashboard", lang),
                reply_markup=get_user_dashboard_keyboard(
                    channels, lang, bot_username=client.me.username
                ),
            )
            return

        # Ensure we have enough parts for channel_id extraction
        if len(data) < 3:
            await callback.answer("❌ Invalid Callback", show_alert=True)
            return

        channel_id_str = data[-1]
        channel_id = (
            int(channel_id_str)
            if channel_id_str.isdigit()
            or (channel_id_str.startswith("-") and channel_id_str[1:].isdigit())
            else None
        )

        if channel_id is None:
            await callback.answer("❌ Invalid Channel ID", show_alert=True)
            return

        repo = ChannelSettingsRepository(session)
        settings = await repo.get_or_create(channel_id)

        if action == "info":
            admin_repo = AdminRepository(session)
            title = await admin_repo.get_chat_title(int(data[3])) or "Channel"
            await callback.answer(f"📍 {title}", show_alert=True)
            return

        admin_repo = AdminRepository(session)
        is_active = False
        channels = await admin_repo.get_user_channels(callback.from_user.id)
        if any(c["chat_id"] == channel_id for c in channels):
            is_active = True

        if not is_active:
            await callback.answer(t("err_bot_left", lang), show_alert=True)
            await callback.message.edit_text(
                t("menu_user_dashboard", lang),
                reply_markup=get_user_dashboard_keyboard(
                    channels, lang, bot_username=client.me.username
                ),
            )
            return

        if action == "select" or (action == "nav" and data[2] == "main"):
            admin_repo = AdminRepository(session)
            title = await admin_repo.get_chat_title(channel_id) or str(channel_id)
            await callback.message.edit_text(
                t("menu_main", lang, title=title, channel_id=channel_id),
                reply_markup=get_main_keyboard(channel_id, lang),
            )

        elif action == "cat":
            cat = data[2]
            if cat == "forward":
                admin_repo = AdminRepository(session)
                title = await admin_repo.get_chat_title(channel_id) or str(channel_id)
                dests = repo.get_destinations_list(settings)
                await callback.message.edit_text(
                    t("menu_forwarding", lang, title=title, channel_id=channel_id),
                    reply_markup=get_forwarding_keyboard(
                        settings, dests, lang, prefix="mych_"
                    ),
                )

        elif action == "toggle":
            field = data[2]
            if field == "forward":
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
                        settings, dests, lang, prefix="mych_"
                    )
                )

        elif action == "nav":
            sub = data[2]
            if sub == "cat" and data[3] == "forward":
                admin_repo = AdminRepository(session)
                title = await admin_repo.get_chat_title(channel_id) or str(channel_id)
                dests = repo.get_destinations_list(settings)
                await callback.message.edit_text(
                    t("menu_forwarding", lang, title=title, channel_id=channel_id),
                    reply_markup=get_forwarding_keyboard(
                        settings, dests, lang, prefix="mych_"
                    ),
                )
                return

            if sub == "add":
                msg = await callback.message.reply_text(
                    t("msg_add_dest", lang),
                    reply_markup=get_request_chat_keyboard(lang),
                )
                await capture_next_input(
                    callback.from_user.id,
                    channel_id,
                    "add_dest",
                    callback.message.id,
                    msg.id,
                )
                await callback.answer()
            elif sub == "credit":
                await callback.message.edit_text(
                    t("msg_set_credit", lang),
                    reply_markup=get_cancel_keyboard(
                        lang, f"mych_cat_forward_{channel_id}"
                    ),
                )
                await capture_next_input(
                    callback.from_user.id, channel_id, "set_credit", callback.message.id
                )
            elif sub == "dest":
                if data[3] == "lang":
                    dest_id = int(data[4])
                    settings = await repo.get_or_create(channel_id)
                    dests = repo.get_destinations_list(settings)
                    current_dest_lang = next(
                        (d.get("target_lang") for d in dests if d["id"] == dest_id),
                        None,
                    )

                    await callback.message.edit_text(
                        t("menu_select_translation_lang", lang),
                        reply_markup=get_languages_keyboard(
                            channel_id,
                            lang,
                            current_lang=current_dest_lang,
                            dest_id=dest_id,
                            prefix="mych_",
                        ),
                    )
                return

        elif action == "set" and data[2] == "dest" and data[3] == "lang":
            lang_code = data[4]
            dest_id = int(data[5])
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
                prefix="mych_",
            )
            try:
                await callback.message.edit_reply_markup(reply_markup=kb)
            except RPCError:
                pass
            return

        elif action == "del" and data[2] == "dest":
            await repo.remove_destination(settings, int(data[3]))
            await callback.answer("🗑️")
            dests = repo.get_destinations_list(settings)
            await callback.message.edit_reply_markup(
                get_forwarding_keyboard(settings, dests, lang, prefix="mych_")
            )

        elif action == "leave":
            try:
                with contextlib.suppress(RPCError):
                    await client.leave_chat(channel_id)

                admin_repo = AdminRepository(session)
                await admin_repo.deactivate_chat(channel_id)

                await repo.delete_settings(channel_id)

                await callback.answer(t("msg_left_channel", lang), show_alert=True)

                channels = await admin_repo.get_user_channels(callback.from_user.id)
                await callback.message.edit_text(
                    t("menu_user_dashboard", lang),
                    reply_markup=get_user_dashboard_keyboard(
                        channels, lang, bot_username=client.me.username
                    ),
                )
            except Exception as e:
                await callback.answer(
                    t("err_error", lang, error=str(e)), show_alert=True
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
    """
    Common logic to cancel the current input state and return to settings.
    """
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
            reply_markup=get_forwarding_keyboard(settings, dests, lang, prefix="mych_"),
            original_message=message,
        )
    if state.get("kb_msg_id"):
        try:
            await client.delete_messages(message.from_user.id, state["kb_msg_id"])
        except RPCError:
            pass
    await clear_input_capture(message.from_user.id)
    try:
        await message.delete()
    except (RPCError, Exception):
        pass


@Client.on_message(
    filters.private & filters.chat_shared & is_waiting_for_input("add_dest")
)
@safe_handler
async def handle_chat_shared(client: Client, message: Message) -> None:
    state = message.input_state
    user_id = message.from_user.id
    channel_id = state["channel_id"]

    shared_chat = message.chat_shared.chat
    shared_chat_id = shared_chat.id
    shared_chat_title = shared_chat.title or f"Channel {shared_chat_id}"

    lang = await get_lang_for_user(message.from_user.id)
    status_text = ""
    ctx = get_context()
    async with ctx.db() as session:
        try:
            repo = ChannelSettingsRepository(session)
            settings = await repo.get_or_create(channel_id)

            success = False
            if shared_chat_id == channel_id:
                status_text = t("err_self_forward", lang)
            else:
                dest_settings = await repo.get_by_channel_id(shared_chat_id)
                is_circular = False
                if dest_settings:
                    dest_destinations = repo.get_destinations_list(dest_settings)
                    if any(d["id"] == channel_id for d in dest_destinations):
                        is_circular = True

                if is_circular:
                    status_text = t("err_circular_forward", lang)
                else:
                    status = await repo.add_destination(
                        settings, shared_chat_id, shared_chat_title
                    )
                    if status == 1:
                        status_text = t("err_already_exists", lang)
                    elif status == 2:
                        status_text = t("err_limit_reached", lang)
                    else:
                        status_text = t("msg_added", lang, title=shared_chat_title)
                        success = True

            try:
                await message.delete()
            except RPCError:
                pass

            if not success:
                await client.send_message(
                    chat_id=user_id,
                    text=status_text,
                    reply_to_message_id=state["prompt_msg_id"],
                )

            if success:
                admin_repo = AdminRepository(session)
                source_title = await admin_repo.get_chat_title(channel_id) or str(
                    channel_id
                )

                dests = repo.get_destinations_list(settings)
                await edit_or_reply(
                    client,
                    user_id,
                    state["prompt_msg_id"],
                    t("menu_forwarding", lang, title=source_title),
                    reply_markup=get_forwarding_keyboard(
                        settings, dests, lang, prefix="mych_"
                    ),
                    original_message=message,
                )
                if state.get("kb_msg_id"):
                    try:
                        await client.delete_messages(user_id, state["kb_msg_id"])
                    except RPCError:
                        pass
                await clear_input_capture(user_id)
        except Exception as e:
            logger.error(f"Error in handle_chat_shared: {e}")
            await client.send_message(
                user_id,
                t("err_error", lang, error=str(e)),
                reply_markup=ReplyKeyboardRemove(),
            )
            await clear_input_capture(user_id)


@Client.on_message(filters.private & filters.text & is_waiting_for_input("set_credit"))
@safe_handler
async def handle_user_input(client: Client, message: Message) -> None:
    state = message.input_state
    user_id = message.from_user.id
    channel_id = state["channel_id"]

    lang = await get_lang_for_user(message.from_user.id)
    ctx = get_context()
    async with ctx.db() as session:
        repo = ChannelSettingsRepository(session)
        settings = await repo.get_or_create(channel_id)
        admin_repo = AdminRepository(session)
        source_title = await admin_repo.get_chat_title(channel_id) or str(channel_id)
        await repo.update(
            settings,
            credit_text=getattr(message.text, "markdown", message.text).strip()
            if message.text
            else "",
        )

        try:
            await message.delete()
        except RPCError:
            pass

        dests = repo.get_destinations_list(settings)
        await edit_or_reply(
            client,
            user_id,
            state["prompt_msg_id"],
            t("menu_forwarding", lang, title=source_title),
            reply_markup=get_forwarding_keyboard(settings, dests, lang, prefix="mych_"),
            original_message=message,
        )

    await clear_input_capture(user_id)
