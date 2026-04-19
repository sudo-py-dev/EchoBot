from sqlalchemy.ext.asyncio import AsyncEngine
from src.db.engine import make_engine


def test_make_engine_sqlite():
    """Test that make_engine returns a valid engine for SQLite."""
    url = "sqlite+aiosqlite:///test.db"
    engine = make_engine(url)
    assert isinstance(engine, AsyncEngine)
    assert str(engine.url).startswith("sqlite")


def test_make_engine_postgres_dialect_fix():
    """Test that make_engine fixes the postgresql:// dialect prefix."""
    url = "postgresql://user:pass@localhost/db"
    engine = make_engine(url)
    assert isinstance(engine, AsyncEngine)
    assert str(engine.url).startswith("postgresql+asyncpg")


def test_make_engine_postgres_pooling():
    """Test that make_engine sets pooling parameters for PostgreSQL."""
    url = "postgresql+asyncpg://user:pass@localhost/db"
    engine = make_engine(url)

    assert engine.pool.size() == 10
    assert "postgresql+asyncpg" in str(engine.url)
