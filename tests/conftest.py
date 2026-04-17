import asyncio
import pytest
from mock import AsyncMock, patch, MagicMock
from pyrogram import Client
from pyrogram.types import User, Chat, Message, CallbackQuery


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_client():
    client = MagicMock(spec=Client)
    client.me = MagicMock(spec=User)
    client.me.id = 12345
    client.me.username = "EchoBot"
    client.get_chat = AsyncMock()
    client.get_chat_member = AsyncMock()
    client.edit_message_text = AsyncMock()
    client.send_message = AsyncMock()
    client.leave_chat = AsyncMock()
    client.delete_messages = AsyncMock()
    return client


@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.id = 999
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 67890
    message.chat = MagicMock(spec=Chat)
    message.chat.id = -100111
    message.chat.type = "channel"
    message.reply_text = AsyncMock()
    message.edit_text = AsyncMock()
    message.reply = AsyncMock()
    return message


@pytest.fixture
def mock_callback_query():
    cb = MagicMock(spec=CallbackQuery)
    cb.from_user = MagicMock(spec=User)
    cb.from_user.id = 67890
    cb.message = MagicMock(spec=Message)
    cb.message.id = 999
    cb.message.chat = MagicMock(spec=Chat)
    cb.message.chat.id = -100111
    cb.message.edit_text = AsyncMock()
    cb.message.reply = AsyncMock()
    cb.answer = AsyncMock()
    return cb


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_app_context(mock_session):
    mock_ctx = MagicMock()
    mock_ctx.db.return_value.__aenter__.return_value = mock_session
    return mock_ctx


@pytest.fixture(autouse=True)
def autouse_mock_context(mock_app_context):
    with (
        patch("core.context.get_context", return_value=mock_app_context),
        patch(
            "utils.i18n.get_lang_for_user", new_callable=AsyncMock, return_value="en"
        ),
    ):
        yield mock_app_context
