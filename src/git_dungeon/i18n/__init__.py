# i18n module for Git Dungeon

from typing import Dict, Optional

# Import translations
from .zh_CN import ZH_CN_TRANSLATIONS


class I18n:
    """Internationalization support for Git Dungeon"""
    
    _instance: Optional['I18n'] = None
    _translations: Dict[str, Dict[str, str]] = {}
    _current_lang: str = 'en'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._translations = {
                'en': {},
                'zh_CN': ZH_CN_TRANSLATIONS,
                'zh': ZH_CN_TRANSLATIONS,
            }
            self._current_lang = 'en'
            self._initialized = True
    
    def load_language(self, lang: str) -> bool:
        """
        Load translation for given language.
        
        Args:
            lang: Language code ('en', 'zh', 'zh_CN')
            
        Returns:
            True if loaded successfully
        """
        if lang in self._translations:
            self._current_lang = lang
            return True
        return False
    
    def get(self, text: str, lang: Optional[str] = None) -> str:
        """
        Get translation for a text string.
        
        Args:
            text: Original English text
            lang: Language code (uses current if not specified)
            
        Returns:
            Translated string
        """
        if lang is None:
            lang = self._current_lang
        
        trans = self._translations.get(lang, {})
        return trans.get(text, text)
    
    def _(self, text: str, lang: Optional[str] = None) -> str:
        """Shortcuts for get()"""
        return self.get(text, lang)
    
    @property
    def current_lang(self) -> str:
        return self._current_lang
    
    @property
    def available_languages(self) -> list:
        return list(self._translations.keys())


# Global instance
i18n = I18n()

# Convenience function
def _(text: str, lang: Optional[str] = None) -> str:
    """Translation function for use in code."""
    return i18n.get(text, lang)
