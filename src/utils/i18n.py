"""
Internationalization utility for managing multi-language support.
"""

import json
import os
from typing import Any, Dict, Optional

from loguru import logger


class I18n:
    """
    Handles translation loading and retrieval.
    """

    def __init__(self, locales_dir: Optional[str] = None, default_lang: str = "en"):
        if locales_dir is None:
            # src/utils/i18n.py -> parent is src/utils -> parent is src/
            locales_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "locales"
            )
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()

    def load_translations(self):
        """
        Loads all JSON translation files from the locales directory.
        """
        if not os.path.exists(self.locales_dir):
            logger.warning(f"Locales directory {self.locales_dir} not found.")
            return

        for filename in os.listdir(self.locales_dir):
            if filename.endswith(".json"):
                lang = filename[:-5]
                try:
                    with open(
                        os.path.join(self.locales_dir, filename), encoding="utf-8"
                    ) as f:
                        self.translations[lang] = json.load(f)
                except (OSError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to load {filename}: {e}")

    def t(self, key: str, locale: Optional[str] = None, **kwargs: Any) -> str:
        """
        Translates a key into the specified locale.
        """
        locale = locale or self.default_lang

        if locale not in self.translations:
            locale = self.default_lang

        text = self.translations.get(locale, {}).get(key)
        if text is None and locale != self.default_lang:
            text = self.translations.get(self.default_lang, {}).get(key)

        if text is None:
            logger.warning(f"Translation key not found: {key}")
            return key

        try:
            return text.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing placeholder in translation for {key}: {e}")
            return text


# Singleton instance
I18N_INSTANCE: Optional[I18n] = None


def get_i18n() -> I18n:
    """
    Returns the singleton I18n instance.
    """
    global I18N_INSTANCE
    if I18N_INSTANCE is None:
        I18N_INSTANCE = I18n()
    return I18N_INSTANCE


def t(key: str, locale: Optional[str] = None, **kwargs: Any) -> str:
    """
    Shortcut for translating a key.
    """
    return get_i18n().t(key, locale, **kwargs)


async def at(user_id: int, key: str, **kwargs: Any) -> str:
    """
    Fetch the translation using the AppContext implicitly for a specific user.
    """
    from src.core.context import get_context
    from src.db.repos.user_repo import UserRepository

    ctx = get_context()
    async with ctx.db() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(user_id)
        locale = user.language_code or "en"

    return t(key, locale=locale, **kwargs)


async def get_lang_for_user(user_id: int) -> str:
    """
    Retrieves the language preference for a user from the database.
    """
    from src.core.context import get_context
    from src.db.repos.user_repo import UserRepository

    ctx = get_context()
    async with ctx.db() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(user_id)
        return user.language_code or "en"
