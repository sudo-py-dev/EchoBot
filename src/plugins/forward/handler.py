import asyncio
import json
from typing import Dict, Optional
from loguru import logger
from pyrogram import Client, enums, filters
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired, ChatWriteForbidden, FloodWait, Forbidden

from src.core.context import get_context
from src.db.models.channel_settings import ChannelSettings
from src.db.repos.channel_settings_repo import ChannelSettingsRepository
from src.utils.translator import get_translator
from src.utils.rate_limit import global_limiter
from src.utils.decorators import safe_handler

forward_queue: asyncio.Queue = asyncio.Queue()
_worker_task: Optional[asyncio.Task] = None


async def _remove_failed_destination(source_channel_id: int, dest_id: int):
    ctx = get_context()
    async with ctx.db() as session:
        try:
            repo = ChannelSettingsRepository(session)
            settings = await repo.get_by_channel_id(source_channel_id)
            if settings:
                removed = await repo.remove_destination(settings, dest_id)
                if removed:
                    logger.debug(
                        f"Automatically removed destination {dest_id} from "
                        f"source {source_channel_id} due to permission errors."
                    )
        except Exception as e:
            logger.error(f"Failed to auto-remove destination {dest_id}: {e}")


async def forward_worker(client: Client):
    while True:
        task = await forward_queue.get()
        try:
            await global_limiter.wait_for_token()

            dest_id = task["dest_id"]
            settings = task["settings"]
            is_media_group = task.get("is_media_group", False)

            if is_media_group:
                success = await perform_forward_media_group(
                    client,
                    task["messages"],
                    settings,
                    task["pre_translated"],
                    dest_id,
                )
            else:
                success = await perform_forward(
                    client,
                    task["message"],
                    settings,
                    task["pre_translated"],
                    dest_id,
                )

            if not success:
                logger.debug(f"Task for {dest_id} failed.")
        except FloodWait as e:
            logger.warning(f"FloodWait: sleeping {e.value}s")
            await asyncio.sleep(e.value)
            await forward_queue.put(task)
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            forward_queue.task_done()


async def perform_forward_media_group(
    client: Client,
    messages: list,
    settings: ChannelSettings,
    pre_translated_group: list,
    dest_id: int,
) -> bool:
    try:
        from pyrogram.types import (
            InputMediaPhoto,
            InputMediaVideo,
            InputMediaAudio,
            InputMediaDocument,
            InputMediaAnimation,
        )

        media = []
        for msg, pre in zip(messages, pre_translated_group):
            caption = msg.caption.markdown if msg.caption else None
            if pre and pre.get("caption"):
                caption = pre["caption"]

            if settings.add_credit and settings.credit_text:
                credit = settings.credit_text
                if caption:
                    if len(caption) + len(credit) + 2 <= 1024:
                        caption = f"{caption}\n\n{credit}"
                else:
                    if len(credit) <= 1024:
                        caption = credit

            if msg.photo:
                media.append(
                    InputMediaPhoto(
                        msg.photo.file_id,
                        caption=caption,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                )
            elif msg.video:
                media.append(
                    InputMediaVideo(
                        msg.video.file_id,
                        caption=caption,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                )
            elif msg.audio:
                media.append(
                    InputMediaAudio(
                        msg.audio.file_id,
                        caption=caption,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                )
            elif msg.document:
                media.append(
                    InputMediaDocument(
                        msg.document.file_id,
                        caption=caption,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                )
            elif msg.animation:
                media.append(
                    InputMediaAnimation(
                        msg.animation.file_id,
                        caption=caption,
                        parse_mode=enums.ParseMode.MARKDOWN,
                    )
                )

        if media:
            await client.send_media_group(chat_id=dest_id, media=media)
        return True
    except (ChatAdminRequired, ChatWriteForbidden, Forbidden) as e:
        logger.debug(f"Permission error in media group forward to {dest_id}: {e}")
        await _remove_failed_destination(messages[0].chat.id, dest_id)
        return False
    except Exception as e:
        logger.error(f"Error in media group forward to {dest_id}: {e}")
        return False


async def start_worker_if_needed(client: Client):
    global _worker_task
    if _worker_task is None:
        _worker_task = asyncio.create_task(forward_worker(client))


media_group_buffer: Dict[str, list] = {}
media_group_lock = asyncio.Lock()


@safe_handler
async def process_media_group(client: Client, media_group_id: str):
    await asyncio.sleep(1.0)
    async with media_group_lock:
        messages = media_group_buffer.pop(media_group_id, [])

    if not messages:
        return

    message = messages[0]
    source_channel_id = message.chat.id

    ctx = get_context()
    async with ctx.db() as session:
        repo = ChannelSettingsRepository(session)
        settings = await repo.get_by_channel_id(source_channel_id)

    if not settings or not settings.forward_enabled or not settings.destinations:
        return

    try:
        destinations = json.loads(settings.destinations)
    except Exception:
        return

    if not destinations:
        return

    translator = get_translator()
    target_langs = {d.get("target_lang") for d in destinations if d.get("target_lang")}

    translations_cache = {}
    for msg in messages:
        translations_cache[msg.id] = {}
        for lang in target_langs:
            try:
                translated_text = (
                    await translator.translate(msg.text.markdown, lang)
                    if msg.text
                    else None
                )
                translated_caption = (
                    await translator.translate(msg.caption.markdown, lang)
                    if msg.caption
                    else None
                )
                translations_cache[msg.id][lang] = {
                    "text": translated_text,
                    "caption": translated_caption,
                }
            except Exception as e:
                logger.error(f"Translation failed for msg {msg.id} ({lang}): {e}")

    await start_worker_if_needed(client)

    for dest in destinations:
        dest_id = dest["id"]
        dest_lang = dest.get("target_lang")

        pre_translated_group = []
        for msg in messages:
            pre_translated_group.append(
                translations_cache.get(msg.id, {}).get(dest_lang) if dest_lang else None
            )

        await forward_queue.put(
            {
                "client": client,
                "messages": messages,
                "settings": settings,
                "pre_translated": pre_translated_group,
                "dest_id": dest_id,
                "is_media_group": True,
            }
        )


@Client.on_message(filters.channel & ~filters.service, group=1)
@safe_handler
async def handle_channel_post(client: Client, message: Message) -> None:
    if message.chat is None:
        return

    if not (message.text or message.media):
        return

    if message.media_group_id:
        async with media_group_lock:
            is_new = message.media_group_id not in media_group_buffer
            if is_new:
                media_group_buffer[message.media_group_id] = []
            media_group_buffer[message.media_group_id].append(message)

        if is_new:
            asyncio.create_task(process_media_group(client, message.media_group_id))
        return

    source_channel_id = message.chat.id

    ctx = get_context()
    async with ctx.db() as session:
        repo = ChannelSettingsRepository(session)
        settings = await repo.get_by_channel_id(source_channel_id)

    if not settings or not settings.forward_enabled or not settings.destinations:
        return

    try:
        destinations = json.loads(settings.destinations)
    except Exception:
        return

    if not destinations:
        return

    translator = get_translator()
    target_langs = {d.get("target_lang") for d in destinations if d.get("target_lang")}
    translations_cache = {}
    for lang in target_langs:
        try:
            translated_text = (
                await translator.translate(message.text.markdown, lang)
                if message.text
                else None
            )
            translated_caption = (
                await translator.translate(message.caption.markdown, lang)
                if message.caption
                else None
            )
            translations_cache[lang] = {
                "text": translated_text,
                "caption": translated_caption,
            }
        except Exception as e:
            logger.error(f"Translation failed ({lang}): {e}")

    await start_worker_if_needed(client)

    for dest in destinations:
        dest_id = dest["id"]
        dest_lang = dest.get("target_lang")
        pre_translated = translations_cache.get(dest_lang) if dest_lang else None

        await forward_queue.put(
            {
                "client": client,
                "message": message,
                "settings": settings,
                "pre_translated": pre_translated,
                "dest_id": dest_id,
                "is_media_group": False,
            }
        )


async def perform_forward(
    client: Client,
    message: Message,
    settings: ChannelSettings,
    pre_translated: Optional[dict],
    dest_id: int,
) -> bool:
    if not settings.forward_media and not settings.forward_text:
        return False

    caption = message.caption.markdown if message.caption else None
    text = message.text.markdown if message.text else None

    if pre_translated:
        if caption and pre_translated.get("caption"):
            caption = pre_translated["caption"]
        if text and pre_translated.get("text"):
            text = pre_translated["text"]

    if settings.add_credit and settings.credit_text:
        credit = settings.credit_text
        if text:
            if len(text) + len(credit) + 2 <= 4096:
                text = f"{text}\n\n{credit}"
        elif caption:
            if len(caption) + len(credit) + 2 <= 1024:
                caption = f"{caption}\n\n{credit}"

    try:
        NON_CAPTIONABLE = {
            enums.MessageMediaType.POLL,
            enums.MessageMediaType.STICKER,
            enums.MessageMediaType.DICE,
            enums.MessageMediaType.LOCATION,
            enums.MessageMediaType.VENUE,
            enums.MessageMediaType.CONTACT,
            enums.MessageMediaType.GAME,
            enums.MessageMediaType.VIDEO_NOTE,
        }

        if message.media:
            if message.media in NON_CAPTIONABLE:
                await client.copy_message(
                    chat_id=dest_id,
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                )
            else:
                await client.copy_message(
                    chat_id=dest_id,
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                    caption=caption,
                    parse_mode=enums.ParseMode.MARKDOWN,
                )
        else:
            await client.send_message(
                chat_id=dest_id,
                text=text or "",
                parse_mode=enums.ParseMode.MARKDOWN,
            )
        return True
    except (ChatAdminRequired, ChatWriteForbidden, Forbidden) as e:
        logger.debug(f"Permission error in forward_message to {dest_id}: {e}")
        await _remove_failed_destination(message.chat.id, dest_id)
        return False
    except Exception as e:
        logger.error(f"Error in forward_message to {dest_id}: {e}")
        return False
