from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import config


def make_engine(url: str, echo: bool = False):
    kwargs = {"echo": echo}
    if not url.startswith("sqlite"):
        kwargs.update(
            {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 300,
                "pool_use_lifo": True,
            }
        )
    return create_async_engine(url, **kwargs)


try:
    engine = make_engine(config.async_db_url, echo=False)
except Exception as e:
    logger.critical(f"🛑 Failed to create database engine: {e}")
    raise

Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def run_migrations() -> None:
    """
    Programmatic entry point for Alembic's 'upgrade head'.
    Should be called before the main event loop starts.
    """
    from alembic import command
    from alembic.config import Config

    logger.info("🛠️ Checking database version and running migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations applied successfully.")
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise
