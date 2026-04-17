"""
Configuration management for the EchoBot application.
"""

from dataclasses import dataclass, field
from os import environ
from dotenv import load_dotenv

load_dotenv()


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

    DATA_DIR: str = field(default_factory=lambda: environ.get("DATA_DIR", "data"))
    SESSIONS_DIR: str = field(
        default_factory=lambda: environ.get("SESSIONS_DIR", "sessions")
    )
    LOG_DIR: str = field(default_factory=lambda: environ.get("LOG_DIR", "logs"))

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

    VERSION: str = "v1.0.0"
    DEV_NAME: str = "sudo-py-dev"
    GITHUB_URL: str = "https://github.com/sudo-py-dev/EchoBot"

    TECH_STACK: dict[str, str] = field(
        default_factory=lambda: {
            "engine": "Python 3.13 (Pyrogram 2.0)",
            "database": "SQLAlchemy 2.0 (SQLite/PostgreSQL)",
            "framework": "Plugin-based Async Architecture",
            "performance": "Optimized MTProto Forwarding",
        }
    )

    @property
    def async_db_url(self) -> str:
        url = self.db_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url


config = Config()
"""Global configuration instance."""
