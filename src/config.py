"""
Configuration management for the EchoBot application.
"""

import os
from dataclasses import dataclass, field
from os import environ
from dotenv import load_dotenv

import tomllib
from pathlib import Path

load_dotenv()


def _load_metadata():
    path = Path(__file__).parent.parent / "pyproject.toml"
    try:
        data = tomllib.loads(path.read_text()) if path.exists() else {}
        proj = data.get("project", {})
        deps = {
            d.split(">")[0].split("=")[0].lower(): d
            for d in proj.get("dependencies", [])
        }
        return proj, deps
    except Exception:
        return {}, {}


_project, _deps = _load_metadata()


@dataclass(frozen=True)
class Config:
    """
    Application configuration and environment variables.

    Attributes:
        api_id (int): Telegram API ID.
        api_hash (str): Telegram API Hash.
        bot_token (str): Telegram Bot Token from @BotFather.
        db_url (str): Database connection URL.
        owner_ids (frozenset[int]): Set of user IDs with full access.
        admin_ids (frozenset[int]): Set of user IDs with admin access.
        cache_ttl (int): Time-to-live for cache entries in seconds.
        log_level (str): Logging level (DEBUG, INFO, etc.).
    """

    @property
    def ROOT_DIR(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def DATA_DIR(self) -> str:
        path = environ.get("DATA_DIR", "data")
        return str((self.ROOT_DIR / path).resolve())

    @property
    def SESSIONS_DIR(self) -> str:
        path = environ.get("SESSIONS_DIR", "sessions")
        return str((self.ROOT_DIR / path).resolve())

    @property
    def LOG_DIR(self) -> str:
        path = environ.get("LOG_DIR", "logs")
        return str((self.ROOT_DIR / path).resolve())

    api_id: int = field(default_factory=lambda: int(environ.get("API_ID", "123")))
    api_hash: str = field(default_factory=lambda: environ.get("API_HASH", ""))
    bot_token: str = field(default_factory=lambda: environ.get("BOT_TOKEN", ""))
    db_url: str = field(
        default_factory=lambda: environ.get(
            "DATABASE_URL",
            f"sqlite+aiosqlite:///{environ.get('DATA_DIR', 'data')}/bot.db?timeout=20",
        )
    )

    owner_ids: frozenset[int] = field(
        default_factory=lambda: frozenset(
            int(x) for x in environ.get("OWNER_IDS", "").split(",") if x.strip()
        )
    )

    admin_ids: frozenset[int] = field(
        default_factory=lambda: frozenset(
            int(x) for x in environ.get("ADMIN_IDS", "").split(",") if x.strip()
        )
    )

    cache_ttl: int = field(default_factory=lambda: int(environ.get("CACHE_TTL", "300")))
    log_level: str = field(default_factory=lambda: environ.get("LOG_LEVEL", "INFO"))

    SUPPORT_URL: str = field(
        default_factory=lambda: environ.get(
            "SUPPORT_URL", "https://buymeacoffee.com/chatmagen"
        )
    )
    GITHUB_SPONSORS_URL: str = field(
        default_factory=lambda: environ.get(
            "GITHUB_SPONSORS_URL", "https://github.com/sponsors/sudo-py-dev"
        )
    )

    VERSION: str = f"v{_project.get('version', '0.0.1')}"
    DEV_NAME: str = "sudo-py-dev"
    GITHUB_URL: str = "https://github.com/sudo-py-dev/EchoBot"

    TECH_STACK: dict[str, str] = field(
        default_factory=lambda: {
            "engine": f"Python {_project.get('requires-python', '3.13')} ({_deps.get('kurigram', 'Kurigram')})",
            "database": f"SQLAlchemy ({_deps.get('sqlalchemy[asyncio]', 'SQLAlchemy')})",
            "framework": "Plugin-based Async Architecture",
            "performance": "Optimized MTProto Forwarding",
        }
    )

    @property
    def async_db_url(self) -> str:
        url = self.db_url.replace("postgres://", "postgresql+asyncpg://", 1).replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
        if url.startswith("sqlite+aiosqlite:///"):
            path = url.split("sqlite+aiosqlite:///")[1]
            if not os.path.isabs(path) and not path.startswith("./"):
                abs_path = (self.ROOT_DIR / path).resolve().as_posix()
                return f"sqlite+aiosqlite:///{abs_path}"
        return url


config = Config()
"""Global configuration instance."""
