"""
Fallback Templates

Template-based fallback text when AI fails or is disabled.
"""

from typing import Dict, Optional
from .types import TextKind, TextRequest


# Fallback templates by text kind, commit type/tier, and language
FALLBACKS: Dict[TextKind, Dict[str, Dict[str, str]]] = {
    TextKind.ENEMY_INTRO: {
        "feat": {
            "en": "A new feature emerges, glowing with potential.",
            "zh_CN": "一个新功能出现，散发着潜力的光芒。",
        },
        "fix": {
            "en": "A bug fix lurks, ready to strike.",
            "zh_CN": "一个 BUG 修复潜伏在此。",
        },
        "docs": {
            "en": "Documentation floats nearby, ancient and wise.",
            "zh_CN": "文档漂浮在周围，古老而睿智。",
        },
        "refactor": {
            "en": "Refactored code reshapes itself before you.",
            "zh_CN": "重构的代码在你面前重塑形态。",
        },
        "test": {
            "en": "Tests surround the area, vigilant and precise.",
            "zh_CN": "测试用例环绕四周，警惕而精确。",
        },
        "chore": {
            "en": "Maintenance tasks hum quietly in the background.",
            "zh_CN": "维护任务在背景中轻轻嗡鸣。",
        },
        "perf": {
            "en": "Performance optimizations pulse with hidden power.",
            "zh_CN": "性能优化脉冲着隐藏的力量。",
        },
        "style": {
            "en": "Style changes drift like autumn leaves.",
            "zh_CN": "代码格式的更改如落叶般飘动。",
        },
        "merge": {
            "en": "A merge conflict looms, complex and tangled.",
            "zh_CN": "合并冲突笼罩于此，复杂而纠缠。",
        },
        "ci": {
            "en": "CI pipelines whir with automated precision.",
            "zh_CN": "CI 流水线以自动化的精确性嗡嗡作响。",
        },
        "default": {
            "en": "A mysterious commit hovers before you.",
            "zh_CN": "一个神秘的提交悬浮在你面前。",
        },
    },
    
    TextKind.BATTLE_START: {
        "normal": {
            "en": "The battle begins!",
            "zh_CN": "战斗开始！",
        },
        "elite": {
            "en": "An elite enemy approaches!",
            "zh_CN": "精英敌人来袭！",
        },
        "boss": {
            "en": "A boss encounter begins!",
            "zh_CN": "BOSS 遭遇战开始！",
        },
        "default": {
            "en": "Your opponent readies itself.",
            "zh_CN": "你的对手准备就绪。",
        },
    },
    
    TextKind.BATTLE_END: {
        "victory": {
            "en": "Victory!",
            "zh_CN": "胜利！",
        },
        "defeat": {
            "en": "Defeat...",
            "zh_CN": "失败...",
        },
        "default": {
            "en": "The battle concludes.",
            "zh_CN": "战斗结束。",
        },
    },
    
    TextKind.EVENT_FLAVOR: {
        "rest": {
            "en": "A peaceful haven for weary travelers.",
            "zh_CN": "疲惫旅人的宁静避风港。",
        },
        "shop": {
            "en": "Mysterious wares line the shelves.",
            "zh_CN": "神秘的商品陈列在货架上。",
        },
        "treasure": {
            "en": "Something valuable gleams within reach.",
            "zh_CN": "有价值的东西在触手可及处闪烁。",
        },
        "mystery": {
            "en": "The unknown awaits your choice.",
            "zh_CN": "未知等待你的选择。",
        },
        "challenge": {
            "en": "A test of skill lies ahead.",
            "zh_CN": "前方有技能考验。",
        },
        "default": {
            "en": "Strange energies swirl around you.",
            "zh_CN": "奇怪的能量在你周围旋转。",
        },
    },
    
    TextKind.BOSS_PHASE: {
        "default": {
            "en": "The boss shifts to a new phase!",
            "zh_CN": "BOSS 转换到新阶段！",
        },
    },
}


def get_fallback_text(request: TextRequest) -> str:
    """
    Get fallback template text for a request.
    
    Args:
        request: The text generation request
        
    Returns:
        Fallback text string
    """
    kind_fallbacks = FALLBACKS.get(request.kind, {})
    lookup_key = _get_lookup_key(request)
    lang = request.lang if request.lang in ["en", "zh_CN"] else "en"
    
    if lookup_key in kind_fallbacks:
        fallback_dict = kind_fallbacks[lookup_key]
        if lang in fallback_dict:
            return fallback_dict[lang]
    
    if "default" in kind_fallbacks:
        fallback_dict = kind_fallbacks["default"]
        if lang in fallback_dict:
            return fallback_dict[lang]
    
    return _ultimate_fallback(request.kind, lang)


def _get_lookup_key(request: TextRequest) -> str:
    """Determine the lookup key based on request type."""
    kind = request.kind
    
    if kind == TextKind.ENEMY_INTRO:
        return request.extra_context.get("commit_type", "default")
    elif kind == TextKind.BATTLE_START:
        return request.extra_context.get("tier", "default")
    elif kind == TextKind.BATTLE_END:
        return "victory" if request.extra_context.get("victory", False) else "defeat"
    elif kind == TextKind.EVENT_FLAVOR:
        event_type = request.extra_context.get("event_type")
        if event_type:
            return event_type
        tags = request.extra_context.get("event_tags", [])
        for tag in tags:
            if tag in FALLBACKS[TextKind.EVENT_FLAVOR]:
                return tag
        return "default"
    elif kind == TextKind.BOSS_PHASE:
        return "default"
    return "default"


def _ultimate_fallback(kind: TextKind, lang: str) -> str:
    """Language-agnostic ultimate fallback."""
    fallbacks = {
        TextKind.ENEMY_INTRO: {"en": "An enemy appears.", "zh_CN": "敌人出现。"},
        TextKind.BATTLE_START: {"en": "Battle begins!", "zh_CN": "战斗开始！"},
        TextKind.BATTLE_END: {"en": "Battle ends.", "zh_CN": "战斗结束。"},
        TextKind.EVENT_FLAVOR: {"en": "Something happens.", "zh_CN": "发生了什么。"},
        TextKind.BOSS_PHASE: {"en": "Phase change!", "zh_CN": "阶段转换！"},
    }
    return fallbacks.get(kind, {}).get(lang, "...")
