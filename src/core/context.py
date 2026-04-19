"""
Application context management for EchoBot.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_context_var: ContextVar[AppContext] = ContextVar("app_context")


@dataclass(frozen=True)
class AppContext:
    """
    Application-wide context holding shared resources.

    Attributes:
        db (async_sessionmaker[AsyncSession]): SQLAlchemy session factory.
    """

    db: async_sessionmaker[AsyncSession]


def set_context(ctx: AppContext) -> None:
    """
    Sets the global application context using a ContextVar.

    Args:
        ctx (AppContext): The context instance to set.
    """
    _context_var.set(ctx)


def get_context() -> AppContext:
    """
    Retrieves the current application context.

    Returns:
        AppContext: The current context.

    Raises:
        RuntimeError: If the context has not been initialized.
    """
    try:
        return _context_var.get()
    except LookupError:
        raise RuntimeError("AppContext is not initialized") from None
