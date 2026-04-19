import os
from unittest.mock import patch
from src.config import Config


def test_config_default_paths():
    """Test that Config uses default paths when no environment variables are set."""
    with patch.dict(os.environ, {}, clear=True):
        c = Config()
        assert c.DATA_DIR == "data"
        assert c.SESSIONS_DIR == "sessions"
        assert c.LOG_DIR == "logs"


def test_config_env_overrides():
    """Test that Config correctly picks up environment variable overrides."""
    with patch.dict(
        os.environ,
        {
            "DATA_DIR": "/tmp/data",
            "SESSIONS_DIR": "/tmp/sessions",
            "LOG_DIR": "/tmp/logs",
        },
        clear=True,
    ):
        c = Config()
        assert c.DATA_DIR == "/tmp/data"
        assert c.SESSIONS_DIR == "/tmp/sessions"
        assert c.LOG_DIR == "/tmp/logs"


def test_config_db_url_construction():
    """Test that the default DATABASE_URL uses the DATA_DIR."""
    with patch.dict(os.environ, {"DATA_DIR": "var/data"}, clear=True):
        c = Config()
        assert "var/data" in c.db_url
        assert "sqlite+aiosqlite" in c.db_url


def test_config_postgres_url():
    """Test that an explicit DATABASE_URL environment variable is respected."""
    pg_url = "postgresql://user:pass@host/db"
    with patch.dict(os.environ, {"DATABASE_URL": pg_url}, clear=True):
        c = Config()
        assert c.db_url == pg_url
