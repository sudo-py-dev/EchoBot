import pytest
from mock import AsyncMock, patch, MagicMock
from plugins.admin_panel.panel import settings_callback, handle_credit_input


@pytest.mark.asyncio
async def test_admin_settings_nav_cat(
    mock_client, mock_callback_query, mock_app_context, mock_session
):
    mock_callback_query.data = "settings_nav_cat_forward_-1001"
    with (
        patch("plugins.admin_panel.panel.get_context", return_value=mock_app_context),
        patch(
            "plugins.admin_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("plugins.admin_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("plugins.admin_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MockRepo.return_value
        mock_repo.get_or_create = AsyncMock()
        mock_repo.get_destinations_list.return_value = []

        mock_admin_repo = MockAdminRepo.return_value
        mock_admin_repo.get_chat_title = AsyncMock(return_value="Source Channel")

        await settings_callback(mock_client, mock_callback_query)
        assert mock_callback_query.message.edit_text.called
        args, kwargs = mock_callback_query.message.edit_text.call_args
        assert "Mirroring Controls" in args[0]


@pytest.mark.asyncio
async def test_admin_nav_add_redirect(
    mock_client, mock_callback_query, mock_app_context, mock_session
):
    mock_callback_query.data = "settings_nav_add_dest_-1001"
    mock_client.me = MagicMock()
    mock_client.me.username = "EchoBot"
    with (
        patch("plugins.admin_panel.panel.get_context", return_value=mock_app_context),
        patch(
            "plugins.admin_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("plugins.admin_panel.panel.ChannelSettingsRepository") as MockRepo,
    ):
        mock_repo = MockRepo.return_value
        mock_repo.get_or_create = AsyncMock()

        await settings_callback(mock_client, mock_callback_query)
        assert mock_callback_query.message.edit_text.called
        args, kwargs = mock_callback_query.message.edit_text.call_args
        assert "Bot Settings" in str(kwargs["reply_markup"])
        assert "t.me/EchoBot?start=settings_-1001" in str(kwargs["reply_markup"])


@pytest.mark.asyncio
async def test_admin_handle_credit_input(
    mock_client, mock_message, mock_app_context, mock_session
):
    mock_message.text = "New Credit"
    mock_message.chat.id = -1001
    mock_message.chat.type = "channel"
    mock_message.reply_to_message = MagicMock()
    mock_message.reply_to_message.id = 555

    with (
        patch("plugins.admin_panel.panel.get_context", return_value=mock_app_context),
        patch(
            "plugins.admin_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("plugins.admin_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("plugins.admin_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MagicMock()
        MockRepo.return_value = mock_repo
        mock_repo.get_or_create = AsyncMock()
        mock_repo.update = AsyncMock()
        mock_repo.get_destinations_list.return_value = []

        mock_admin_repo = MockAdminRepo.return_value
        mock_admin_repo.get_chat_title = AsyncMock(return_value="Source Channel")

        await handle_credit_input(mock_client, mock_message)

        mock_repo.update.assert_called()
        mock_client.edit_message_text.assert_called()
        edit_kwargs = mock_client.edit_message_text.call_args.kwargs
        assert edit_kwargs["message_id"] == 555
        assert "Mirroring" in edit_kwargs["text"]
