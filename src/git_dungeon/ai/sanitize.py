"""
Text Sanitization

Cleans and validates AI-generated text output.
"""

import re
from typing import Dict, Tuple
from .types import TextKind


# Length limits by text kind (characters)
LENGTH_LIMITS: Dict[TextKind, int] = {
    TextKind.ENEMY_INTRO: 60,
    TextKind.BATTLE_START: 80,
    TextKind.BATTLE_END: 80,
    TextKind.EVENT_FLAVOR: 80,
    TextKind.BOSS_PHASE: 80,
}

# Keywords that indicate the AI is trying to break rules
BLOCKED_KEYWORDS = [
    r"\d+\s*(damage|hp|gold|attack|defense|armor|buff|debuff)",
    r"\+\d+",
    r"\-\d+",
    r"\d+\s*points",
    r"\d+\s*percent",
    r"you should",
    r"you must",
    r"i recommend",
    r"try to",
    r"consider",
    r"don't forget",
    r"modify",
    r"change the",
    r"increase.*damage",
    r"decrease.*hp",
    r"add.*card",
    r"remove.*card",
]


def sanitize_text(text: str, kind: TextKind) -> Tuple[str, dict]:
    """
    Sanitize AI-generated text.
    
    Args:
        text: Raw text from AI
        kind: Type of text (for length limits)
        
    Returns:
        Tuple of (sanitized_text, metadata_dict)
    """
    if not text:
        return "", {"reason": "empty_input"}
    
    # Step 1: Remove markdown formatting
    text = _remove_markdown(text)
    
    # Step 2: Remove excessive whitespace
    text = _normalize_whitespace(text)
    
    # Step 3: Remove multiple lines (should be single line)
    text = _single_line(text)
    
    # Step 4: Check for blocked keywords
    if _contains_blocked_keywords(text):
        text = _remove_blocked_content(text)
        if _contains_blocked_keywords(text):
            return "", {"reason": "blocked_keywords", "original_length": len(text)}
    
    # Step 5: Check length limits
    limit = LENGTH_LIMITS.get(kind, 80)
    trimmed = False
    if len(text) > limit:
        text = _trim_to_limit(text, limit)
        trimmed = True
    
    # Step 6: Remove emoji and special characters
    text = _clean_special_chars(text)
    
    # Final validation
    if not text or len(text) < 3:
        return "", {"reason": "too_short_after_cleaning"}
    
    meta = {"trimmed": trimmed, "sanitized": True}
    if trimmed:
        meta["original_length"] = len(text)
    
    return text.strip(), meta


def _remove_markdown(text: str) -> str:
    """Remove markdown formatting."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    return text


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _single_line(text: str) -> str:
    """Convert to single line."""
    return text.replace("\n", " ").replace("\r", " ")


def _contains_blocked_keywords(text: str) -> bool:
    """Check if text contains blocked keywords."""
    text_lower = text.lower()
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, text_lower):
            return True
    return False


def _remove_blocked_content(text: str) -> str:
    """Attempt to remove blocked content."""
    text_lower = text.lower()
    for pattern in BLOCKED_KEYWORDS:
        match = re.search(pattern, text_lower)
        if match:
            sentence_end = match.end()
            for i in range(sentence_end, min(sentence_end + 100, len(text))):
                if text[i] in ".!?。！？":
                    return text[:i].strip()
            return text[:match.start()].strip()
    return text


def _trim_to_limit(text: str, limit: int) -> str:
    """Trim text to character limit."""
    if len(text) <= limit:
        return text
    trimmed = text[:limit - 3]
    last_space = trimmed.rfind(" ")
    if last_space > limit * 0.5:
        trimmed = trimmed[:last_space]
    return trimmed.rstrip(" ,.。！？") + "..."


def _clean_special_chars(text: str) -> str:
    """Remove problematic special characters."""
    zh_punctuation = set("，。！？；：（）《》【】、“”‘’—…·「」『』")
    result = []
    for char in text:
        code = ord(char)
        if code < 128:
            result.append(char)
            continue
        if _is_cjk_char(code) or char in zh_punctuation:
            result.append(char)
            continue
        if char.isspace():
            result.append(" ")
    return "".join(result)


def _is_cjk_char(codepoint: int) -> bool:
    """Return True for common CJK blocks used by zh_CN output."""
    return (
        0x4E00 <= codepoint <= 0x9FFF  # CJK Unified Ideographs
        or 0x3400 <= codepoint <= 0x4DBF  # CJK Extension A
        or 0x20000 <= codepoint <= 0x2A6DF  # CJK Extension B
        or 0x2A700 <= codepoint <= 0x2B73F  # CJK Extension C
        or 0x2B740 <= codepoint <= 0x2B81F  # CJK Extension D
        or 0x2B820 <= codepoint <= 0x2CEAF  # CJK Extension E/F
        or 0xF900 <= codepoint <= 0xFAFF  # CJK Compatibility Ideographs
    )
