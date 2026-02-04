"""
AI Prompt Templates

Prompt templates for each text generation kind.
"""

from typing import Dict
from .types import TextKind


# Prompt templates for each text kind
PROMPTS: Dict[TextKind, Dict[str, str]] = {
    TextKind.ENEMY_INTRO: {
        "en": """You are writing a flavor introduction for a game enemy.

The enemy is a Git commit of type: {commit_type}

Context:
- Repository: {repo_id}
- Commit SHA: {commit_sha}
- Enemy ID: {enemy_id}
- Random seed: {seed}

Write ONE sentence (max 60 characters) introducing this enemy.
Use {tone} tone.

Rules:
- NO numbers or statistics
- NO suggestions for actions
- Pure flavor text only
- Output single line, no markdown
- Must be under 60 characters

Example:
"A bug fix lurks, ready to strike."
"A feature emerges, glowing with potential."

Your introduction:""",
        
        "zh_CN": """你正在为一个游戏敌人写一句 Flavor 介绍。

这个敌人是一个 Git 提交，类型是：{commit_type}

背景：
- 仓库：{repo_id}
- 提交 SHA：{commit_sha}
- 敌人 ID：{enemy_id}
- 随机种子：{seed}

用 {tone} 语气写一句话（最多 30 个中文字符）来介绍这个敌人。

规则：
- 不要包含数字或统计信息
- 不要建议玩家行动
- 纯 Flavor 文本
- 输出单行，不要 Markdown
- 必须少于 30 个中文字符

示例：
"一个 BUG 潜伏在此。"
"新功能散发着潜力的光芒。"

你的介绍：""",
    },
    
    TextKind.BATTLE_START: {
        "en": """You are writing battle narration for a roguelike card game.

Battle context:
- Player class: {player_class}
- Enemy: {commit_type}
- Enemy tier: {tier} (normal/elite/boss)
- Current HP: player {player_hp}, enemy {enemy_hp}
- Seed: {seed}

Write ONE sentence (max 80 characters) describing the battle start.
Use {tone} tone.

Rules:
- NO damage numbers or stat comparisons
- NO strategic suggestions
- Pure flavor narration
- Output single line, no markdown
- Must be under 80 characters

Your narration:""",
        
        "zh_CN": """你正在为一个 Roguelike 卡牌游戏写战斗叙述。

战斗背景：
- 玩家职业：{player_class}
- 敌人：{commit_type}
- 敌人层级：{tier}（普通/精英/BOSS）
- 当前生命值：玩家 {player_hp}，敌人 {enemy_hp}
- 随机种子：{seed}

用 {tone} 语气写一句话（最多 40 个中文字符）描述战斗开始。

规则：
- 不要包含伤害数字或属性对比
- 不要建议策略
- 纯 Flavor 叙述
- 输出单行，不要 Markdown
- 必须少于 40 个中文字符

你的叙述：""",
    },
    
    TextKind.BATTLE_END: {
        "en": """You are writing battle conclusion narration.

Battle result: {result}
- Victory: {victory}
- Enemy: {commit_type}
- Loot obtained: {loot}
- Seed: {seed}

Write ONE sentence (max 80 characters) describing the outcome.
Use {tone} tone.

Rules:
- NO specific numbers (damage, HP, gold amount)
- NO experience points mentioned
- Pure flavor text
- Output single line, no markdown
- Must be under 80 characters

Your conclusion:""",
        
        "zh_CN": """你正在写战斗结果叙述。

战斗结果：{result}
- 胜利：{victory}
- 敌人：{commit_type}
- 获得战利品：{loot}
- 随机种子：{seed}

用 {tone} 语气写一句话（最多 40 个中文字符）描述战斗结果。

规则：
- 不要包含具体数字（伤害、金币数量）
- 不要提及经验值
- 纯 Flavor 文本
- 输出单行，不要 Markdown
- 必须少于 40 个中文字符

你的叙述：""",
    },
    
    TextKind.EVENT_FLAVOR: {
        "en": """You are writing atmospheric flavor text for a game event.

Event location: {event_location}
Event type: {event_type}
Event tags: {event_tags}
Seed: {seed}

Write ONE sentence (max 80 characters) describing the atmosphere.
Use {tone} tone.

Rules:
- NO choice options or effects
- NO numerical modifiers mentioned
- Pure atmosphere description
- Output single line, no markdown
- Must be under 80 characters

Your atmosphere:""",
        
        "zh_CN": """你正在为一个游戏事件写氛围 Flavor 文本。

事件地点：{event_location}
事件类型：{event_type}
事件标签：{event_tags}
随机种子：{seed}

用 {tone} 语气写一句话（最多 40 个中文字符）描述氛围。

规则：
- 不要包含选项或效果
- 不要提及数值修改
- 纯氛围描述
- 输出单行，不要 Markdown
- 必须少于 40 个中文字符

你的氛围描述：""",
    },
    
    TextKind.BOSS_PHASE: {
        "en": """You are writing boss phase transition narration.

Boss: {boss_name}
Phase: {phase}
Previous phase ability: {prev_ability}
Seed: {seed}

Write ONE sentence (max 80 characters) announcing the phase change.
Use {tone} tone.

Rules:
- NO damage numbers or stat changes
- NO strategic warnings
- Pure flavor transition line
- Output single line, no markdown
- Must be under 80 characters

Your phase line:""",
        
        "zh_CN": """你正在写 Boss 阶段转换叙述。

Boss：{boss_name}
阶段：{phase}
上一个阶段能力：{prev_ability}
随机种子：{seed}

用 {tone} 语气写一句话（最多 40 个中文字符）宣布阶段转换。

规则：
- 不要包含伤害数字或属性变化
- 不要警告策略
- 纯 Flavor 转换台词
- 输出单行，不要 Markdown
- 必须少于 40 个中文字符

你的阶段台词：""",
    },
}


def get_prompt(kind: TextKind, lang: str, **kwargs) -> str:
    """
    Get the prompt template for a given text kind and language.
    
    Args:
        kind: Type of text to generate
        lang: Language code ('en' or 'zh_CN')
        **kwargs: Template variables
        
    Returns:
        Formatted prompt string
    """
    lang_prompts = PROMPTS.get(kind, {})
    template = lang_prompts.get(lang, lang_prompts.get("en", ""))
    
    # Set default tone if not provided
    kwargs.setdefault("tone", "neutral")
    
    return template.format(**kwargs)


def get_system_prompt(lang: str) -> str:
    """Get the system prompt for the AI."""
    if lang == "zh_CN":
        return """你是一个专业的游戏叙事作家，擅长写简洁有力的 Flavor 文本。
你的任务是根据给定的上下文，写出沉浸式的游戏描述。
记住：
- 只写描述，不给建议
- 不要包含数字或统计
- 输出必须简洁
- 不要使用 Markdown 格式"""
    else:
        return """You are a professional game narrative writer, skilled at writing 
concise and immersive flavor text.

Your task is to write immersive game descriptions based on given context.

Remember:
- Only describe, never suggest
- Don't include numbers or statistics
- Output must be concise
- Don't use Markdown formatting"""
