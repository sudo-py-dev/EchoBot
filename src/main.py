import os
import sys
import asyncio
from loguru import logger
from pyrogram import Client, idle

# Add the parent directory to sys.path to allow running from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import config
from src.core.context import AppContext, set_context
from src.db.engine import Session

os.makedirs(config.DATA_DIR, exist_ok=True)
os.makedirs(config.SESSIONS_DIR, exist_ok=True)

bot = Client(
    name=os.path.join(config.SESSIONS_DIR, "echobot"),
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
    plugins={"root": "src.plugins"},
)


async def start_bot() -> None:
    logger.remove()
    logger.add(sys.stderr, level=config.log_level)

    ctx = AppContext(db=Session)
    set_context(ctx)

    await bot.start()
    logger.info(f"🚀 Bot @{bot.me.username} started successfully!")

    try:
        await idle()
    finally:
        await bot.stop()


def main() -> None:
    logger.info("--- 🚀 Bot Early Boot Sequence Starting ---")

    from src.db.engine import run_migrations

    try:
        run_migrations()
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception("--- ❌ CRITICAL BOOT ERROR ---")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Shutting down... (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        msg = str(e)
        if "database is locked" in msg.lower():
            logger.critical(
                "🛑 Database is Busy: The bot database is currently locked by another process."
            )
        else:
            logger.critical(f"Critical error: {e}")
        sys.exit(1)
