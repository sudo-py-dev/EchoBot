"""
Translation utility for cross-language message forwarding.
"""

import asyncio
from typing import Optional

from deep_translator import GoogleTranslator
from loguru import logger

from utils.cache import get_cache
from config import config


class TranslationService:
    """
    Service for translating text using Google Translate with local caching.
    """

    def __init__(self) -> None:
        self.cache = get_cache(ttl=config.cache_ttl)

    async def translate(self, text: str, target_lang: str) -> Optional[str]:
        """
        Translates text to the target language, utilizing cache for repeated queries.
        """
        if not text or not target_lang:
            return text

        if target_lang.lower() == "he":
            target_lang = "iw"

        cache_key = f"translate:{target_lang}:{hash(text)}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        try:
            translator = GoogleTranslator(source="auto", target=target_lang)
            translated = await asyncio.to_thread(translator.translate, text)

            if translated:
                await self.cache.set(cache_key, translated)
                return translated

            return text
        except (RuntimeError, ConnectionError, ValueError) as e:
            logger.error(f"Translation failed for lang {target_lang}: {e}")
            return text
        except Exception as e:
            logger.error(f"Unexpected translation error for lang {target_lang}: {e}")
            return text

    async def close(self) -> None:
        """
        Closes any resources used by the translation service.
        """


# Singleton instance
TRANSLATOR_INSTANCE: Optional[TranslationService] = None


def get_translator() -> TranslationService:
    """
    Returns the singleton TranslationService instance.
    """
    global TRANSLATOR_INSTANCE
    if TRANSLATOR_INSTANCE is None:
        TRANSLATOR_INSTANCE = TranslationService()
    return TRANSLATOR_INSTANCE
