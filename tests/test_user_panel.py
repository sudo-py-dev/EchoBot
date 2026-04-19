import pytest
from mock import AsyncMock, patch, MagicMock
from src.plugins.user_panel.panel import (
    mych_callback,
    handle_chat_shared,
    handle_user_input,
)


@pytest.mark.asyncio
async def test_mych_select_callback(
    mock_client, mock_callback_query, mock_app_context, mock_session
):
    mock_callback_query.data = "mych_select_-1001"
    with (
        patch(
            "src.plugins.user_panel.panel.get_context", return_value=mock_app_context
        ),
        patch(
            "src.plugins.user_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("src.plugins.user_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("src.plugins.user_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MockRepo.return_value
        mock_repo.get_or_create = AsyncMock()

        mock_admin_repo = MockAdminRepo.return_value
        mock_admin_repo.get_chat_title = AsyncMock(return_value="Source Channel")
        mock_admin_repo.get_user_channels = AsyncMock(
            return_value=[{"chat_id": -1001, "chat_title": "Source Channel"}]
        )

        await mych_callback(mock_client, mock_callback_query)
        assert mock_callback_query.message.edit_text.called
        args, kwargs = mock_callback_query.message.edit_text.call_args
        assert "Configuration:" in args[0]
        assert "Source Channel" in args[0]
        assert "mych_cat_forward_-1001" in str(kwargs["reply_markup"])
        assert "mych_leave_-1001" in str(kwargs["reply_markup"])


@pytest.mark.asyncio
async def test_mych_category_forward(
    mock_client, mock_callback_query, mock_app_context, mock_session
):
    mock_callback_query.data = "mych_cat_forward_-1001"
    with (
        patch(
            "src.plugins.user_panel.panel.get_context", return_value=mock_app_context
        ),
        patch(
            "src.plugins.user_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("src.plugins.user_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("src.plugins.user_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MockRepo.return_value
        mock_repo.get_or_create = AsyncMock()
        mock_repo.get_destinations_list.return_value = [{"id": -1002, "title": "Dest"}]

        mock_admin_repo = MockAdminRepo.return_value
        mock_admin_repo.get_chat_title = AsyncMock(return_value="Source Channel")
        mock_admin_repo.get_user_channels = AsyncMock(
            return_value=[{"chat_id": -1001, "chat_title": "Source Channel"}]
        )

        await mych_callback(mock_client, mock_callback_query)
        assert mock_callback_query.message.edit_text.called
        args, kwargs = mock_callback_query.message.edit_text.call_args
        assert "Mirroring Controls" in args[0]
        assert "Dest" in str(kwargs["reply_markup"])
        assert "btn_leave_channel" not in str(kwargs["reply_markup"])


@pytest.mark.asyncio
async def test_handle_chat_shared_add_dest(
    mock_client, mock_message, mock_app_context, mock_session
):
    mock_message.chat_shared = MagicMock()
    mock_message.chat_shared.chat = MagicMock()
    mock_message.chat_shared.chat.id = -1002
    mock_message.chat_shared.chat.title = "Target Channel"

    mock_message.input_state = {
        "field": "add_dest",
        "channel_id": -1001,
        "prompt_msg_id": 999,
        "kb_msg_id": 888,
    }
    mock_message.from_user.id = 123

    with (
        patch(
            "src.plugins.user_panel.panel.get_context", return_value=mock_app_context
        ),
        patch(
            "src.plugins.user_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("src.plugins.user_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("src.plugins.user_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MagicMock()
        MockRepo.return_value = mock_repo
        mock_repo.get_or_create = AsyncMock()
        mock_repo.get_by_channel_id = AsyncMock(return_value=None)
        mock_repo.add_destination = AsyncMock(return_value=0)

        mock_admin_repo = MockAdminRepo.return_value
        mock_admin_repo.get_chat_title = AsyncMock(return_value="Source Channel")

        await handle_chat_shared(mock_client, mock_message)

        mock_repo.add_destination.assert_called()
        mock_client.edit_message_text.assert_called()
        edit_kwargs = mock_client.edit_message_text.call_args.kwargs
        assert "Mirroring" in edit_kwargs["text"]
        # Verify keyboard deletion
        mock_client.delete_messages.assert_called_with(123, 888)


@pytest.mark.asyncio
async def test_handle_user_input_set_credit(
    mock_client, mock_message, mock_app_context, mock_session
):
    mock_message.text = "Source: @echo"
    mock_message.input_state = {
        "field": "set_credit",
        "channel_id": -1001,
        "prompt_msg_id": 999,
    }
    mock_message.from_user.id = 123
    with (
        patch(
            "src.plugins.user_panel.panel.get_context", return_value=mock_app_context
        ),
        patch(
            "src.plugins.user_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("src.plugins.user_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("src.plugins.user_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MagicMock()
        MockRepo.return_value = mock_repo
        mock_repo.get_or_create = AsyncMock()
        mock_repo.update = AsyncMock()

        mock_admin_repo = MockAdminRepo.return_value
        mock_admin_repo.get_chat_title = AsyncMock(return_value="Source Channel")

        await handle_user_input(mock_client, mock_message)

        mock_repo.update.assert_called_with(
            mock_repo.get_or_create.return_value, credit_text="Source: @echo"
        )

        mock_client.edit_message_text.assert_called()
        edit_kwargs = mock_client.edit_message_text.call_args.kwargs
        assert "Mirroring" in edit_kwargs["text"]


@pytest.mark.asyncio
async def test_mych_leave_callback(
    mock_client, mock_callback_query, mock_app_context, mock_session
):
    mock_callback_query.data = "mych_leave_-1001"
    with (
        patch(
            "src.plugins.user_panel.panel.get_context", return_value=mock_app_context
        ),
        patch(
            "src.plugins.user_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("src.plugins.user_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("src.plugins.user_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MockRepo.return_value
        mock_repo.get_or_create = AsyncMock()
        mock_repo.delete_settings = AsyncMock(return_value=True)

        mock_admin_repo = MockAdminRepo.return_value
        # For leave success, it needs to check access first, then deactivate
        mock_admin_repo.get_user_channels = AsyncMock(
            side_effect=[
                [{"chat_id": -1001, "chat_title": "Source Channel"}],  # Access check
                [],  # Post-leave refresh
            ]
        )
        mock_admin_repo.deactivate_chat = AsyncMock()

        await mych_callback(mock_client, mock_callback_query)

        mock_client.leave_chat.assert_called_with(-1001)
        mock_admin_repo.deactivate_chat.assert_called_with(-1001)
        assert mock_callback_query.message.edit_text.called
        args, _ = mock_callback_query.message.edit_text.call_args
        assert "Dashboard" in args[0]


@pytest.mark.asyncio
async def test_mych_access_guard(
    mock_client, mock_callback_query, mock_app_context, mock_session
):
    # Test that a user cannot access a channel the bot has left
    mock_callback_query.data = "mych_select_-1001"
    with (
        patch(
            "src.plugins.user_panel.panel.get_context", return_value=mock_app_context
        ),
        patch(
            "src.plugins.user_panel.panel.get_lang_for_user",
            new_callable=AsyncMock,
            return_value="en",
        ),
        patch("src.plugins.user_panel.panel.ChannelSettingsRepository") as MockRepo,
        patch("src.plugins.user_panel.panel.AdminRepository") as MockAdminRepo,
    ):
        mock_repo = MockRepo.return_value
        mock_repo.get_or_create = AsyncMock()

        mock_admin_repo = MockAdminRepo.return_value
        # Return empty list, implying -1001 is not active for this user
        mock_admin_repo.get_user_channels = AsyncMock(return_value=[])

        await mych_callback(mock_client, mock_callback_query)

        # Should answer with error alert
        assert mock_callback_query.answer.called
        assert "Bot Inactive" in mock_callback_query.answer.call_args[0][0]
        assert mock_callback_query.message.edit_text.called
        args, _ = mock_callback_query.message.edit_text.call_args
        assert "Dashboard" in args[0]
