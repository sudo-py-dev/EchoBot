import asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import config
from db.models import Base

def make_engine(url: str, echo: bool = False):
    kwargs = {"echo": echo}
    if not url.startswith("sqlite"):
        kwargs.update(
            {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
        )
    return create_async_engine(url, **kwargs)

try:
    engine = make_engine(config.async_db_url, echo=False)
except Exception as e:
    logger.critical(f"🛑 Failed to create database engine: {e}")
    raise

Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db() -> None:
    logger.info("🛠️ Initializing database schema (create_all)...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config
    logger.info("🛠️ Running database migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Migrations applied successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to run migrations: {e}")
        raise
