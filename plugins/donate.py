"""
Plugin for handling donations via Telegram Stars and external links.
"""

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from config import config
from utils.decorators import safe_handler
from utils.i18n import t, get_lang_for_user


async def get_donate_kb(lang: str) -> InlineKeyboardMarkup:
    """Generate the main donation keyboard with Stars and external links."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("donate_stars_btn", lang), callback_data="donate:stars"
                )
            ],
            [InlineKeyboardButton(t("donate_bmc_btn", lang), url=config.SUPPORT_URL)],
            [
                InlineKeyboardButton(
                    t("donate_github_btn", lang), url=config.GITHUB_SPONSORS_URL
                )
            ],
            [InlineKeyboardButton(t("btn_back", lang), callback_data="donate:back")],
        ]
    )


@Client.on_message(filters.command(["donate", "support"]))
@safe_handler
async def cmd_donate(client: Client, message: Message) -> None:
    """Display the main donation menu."""
    lang = await get_lang_for_user(message.from_user.id)
    bot_name = client.me.first_name if client.me else "EchoBot"

    await message.reply_text(
        t("donate_text", lang, bot_name=bot_name),
        reply_markup=await get_donate_kb(lang),
    )


@Client.on_callback_query(filters.regex(r"^donate:"))
@safe_handler
async def donate_callback_handler(
    client: Client, callback_query: CallbackQuery
) -> None:
    """Handle donation menu navigation and Stars payment flow."""
    data = callback_query.data
    user_id = callback_query.from_user.id
    lang = await get_lang_for_user(user_id)

    if data == "donate:main":
        bot_name = client.me.first_name if client.me else "EchoBot"
        await callback_query.message.edit_text(
            t("donate_text", lang, bot_name=bot_name),
            reply_markup=await get_donate_kb(lang),
        )

    elif data == "donate:stars":
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        t("donate_stars_amount", lang, amount=50),
                        callback_data="donate:pay:50",
                    ),
                    InlineKeyboardButton(
                        t("donate_stars_amount", lang, amount=250),
                        callback_data="donate:pay:250",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        t("donate_stars_amount", lang, amount=500),
                        callback_data="donate:pay:500",
                    )
                ],
                [
                    InlineKeyboardButton(
                        t("btn_back", lang), callback_data="donate:main"
                    )
                ],
            ]
        )
        await callback_query.message.edit_text(
            t("donate_stars_select_text", lang),
            reply_markup=kb,
        )

    elif data.startswith("donate:pay:"):
        amount = int(data.split(":")[-1])
        bot_name = client.me.first_name if client.me else "EchoBot"
        title = t("donate_invoice_title", lang, bot_name=bot_name)
        description = t("donate_invoice_desc", lang, amount=amount)

        try:
            await client.send_invoice(
                chat_id=user_id,
                title=title,
                description=description,
                payload=f"donate_{amount}",
                currency="XTR",
                prices=[LabeledPrice(label="XTR", amount=amount)],
                start_parameter="donate",
            )
            await callback_query.answer()
        except Exception as e:
            await callback_query.answer(
                t("donate_error", lang, error=str(e)), show_alert=True
            )

    elif data == "donate:back":
        await callback_query.message.delete()


@Client.on_pre_checkout_query()
@safe_handler
async def pre_checkout_handler(client: Client, query: PreCheckoutQuery) -> None:
    """Approve checkout queries for Telegram Stars."""
    await query.answer(ok=True)


@Client.on_message(filters.successful_payment)
@safe_handler
async def successful_payment_handler(client: Client, message: Message) -> None:
    """Handle successful donation payments and notify admin."""
    payment = message.successful_payment
    amount = payment.total_amount
    currency = payment.currency
    lang = await get_lang_for_user(message.from_user.id)

    await message.reply_text(t("donate_thanks", lang, amount=amount, currency=currency))

    # Notify owner if configured
    if config.owner_ids:
        from core.context import get_context
        from db.repos.user_repo import UserRepository

        ctx = get_context()
        async with ctx.db() as session:
            repo = UserRepository(session)
            owner_id = next(iter(config.owner_ids))
            owner = await repo.get_or_create(owner_id)
            owner_lang = owner.language_code or "en"

            mention = (
                message.from_user.mention
                if message.from_user
                else f"User {message.from_user.id}"
            )
            admin_msg = t(
                "donate_admin_notify",
                owner_lang,
                mention=mention,
                amount=amount,
                currency=currency,
                payload=payment.invoice_payload,
            )
            try:
                await client.send_message(owner_id, admin_msg)
            except Exception:
                pass
