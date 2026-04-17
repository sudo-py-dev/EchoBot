import os
import sys
import asyncio
from loguru import logger
from pyrogram import Client
from config import config
from core.context import AppContext, set_context
from db.engine import Session, init_db

os.makedirs(config.SESSIONS_DIR, exist_ok=True)

bot = Client(
    name=os.path.join(config.SESSIONS_DIR, "echobot"),
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
    plugins={"root": "plugins"},
)

def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=config.log_level)

    asyncio.run(init_db())

    ctx = AppContext(db=Session)
    set_context(ctx)

    logger.info("🚀 Bot started!")
    bot.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Shutting down... (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        msg = str(e)
        if "database is locked" in msg.lower():
            logger.critical("🛑 Database is Busy: The bot database is currently locked by another process.")
        else:
            logger.critical(f"Critical error: {e}")
        sys.exit(1)
