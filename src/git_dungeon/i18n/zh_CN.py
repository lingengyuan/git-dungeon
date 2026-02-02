# Chinese translations for Git Dungeon
# 中文翻译

ZH_CN_TRANSLATIONS = {
    # Game name
    "Git Dungeon": "Git 地牢",
    "Battle through your commits!": "在提交历史中战斗!",
    
    # CLI help
    "Git Dungeon - Battle through your commits!": "Git 地牢 - 在提交历史中战斗!",
    "Repository path or user/repo": "仓库路径或用户名/仓库名",
    "Random seed for reproducibility": "随机种子(用于复现)",
    "Enable verbose output": "启用详细输出",
    "show program's version number and exit": "显示版本号并退出",
    "Disable colored output": "禁用彩色输出",
    "Write plain text log to file": "写入纯文本日志到文件",
    "Write JSON log to file (JSONL format)": "写入 JSON 日志到文件(JSONL 格式)",
    "Auto-battle mode (automatic combat)": "自动战斗模式",
    "Repository not found": "仓库未找到",
    "Failed to load": "加载失败",
    "Loaded": "已加载",
    "commits": "次提交",
    "Divided into": "分为",
    "chapters": "个章节",
    
    # Chapter names
    "混沌初开": "混沌初开",
    "功能涌现": "功能涌现",
    "架构重构": "架构重构",
    "优化迭代": "优化迭代",
    "成熟稳定": "成熟稳定",
    "开疆拓土": "开疆拓土",
    "登峰造极": "登峰造极",
    
    # Enemy types
    "Feature": "功能",
    "Bug": "Bug",
    "Docs": "文档",
    "Merge": "合并",
    "Refactor": "重构",
    "Test": "测试",
    "Chore": "杂项",
    "Style": "样式",
    "Perf": "性能",
    
    # Combat
    "BOSS BATTLE": "BOSS 战",
    "Chapter": "章节",
    "You attack": "你攻击",
    "for": "造成",
    "damage": "伤害",
    "CRIT!": "暴击!",
    "defeated": "已击败",
    "Defensive stance": "防御姿态",
    "Need": "需要",
    "MP, have": "MP, 当前",
    "Escaped": "逃跑成功",
    "Escape failed": "逃跑失败",
    "Defense": "防御",
    "damage taken": "伤害",
    "IS ENRAGED": "被激怒",
    "DEFEATED": "已被击败",
    
    # Rewards
    "EXP": "经验",
    "Gold": "金币",
    "LEVEL UP": "升级",
    
    # Shop
    "商店": "商店",
    "Welcome to the shop": "欢迎来到商店",
    "Purchased": "已购买",
    "Not enough gold": "金币不足",
    "Invalid choice": "无效选择",
    
    # Chapter complete
    "CHAPTER COMPLETE": "章节完成",
    "Enemies": "敌人",
    
    # Victory
    "VICTORY": "胜利",
    "All commits defeated": "所有提交已击败",
    "FINAL STATISTICS": "最终统计",
    "Level": "等级",
    "Enemies defeated": "击败敌人",
    "Items": "物品",
    "Congratulations": "恭喜",
    
    # Defeat
    "GAME OVER": "游戏结束",
    
    # Menu
    "Attack": "攻击",
    "Defend": "防御",
    "Skill": "技能",
    "Run/Shop": "逃跑/商店",
    "Invalid input": "无效输入",
    
    # Actions
    "Choose your action": "选择你的行动",
    "Invalid input, try again": "无效输入,请重试",
}

# Simple translation function
def translate(text: str, lang: str = 'zh_CN') -> str:
    """Simple translation function"""
    if lang == 'zh_CN' or lang == 'zh':
        return ZH_CN_TRANSLATIONS.get(text, text)
    return text

# Convenience
def _(text: str, lang: str = 'zh_CN') -> str:
    """Translation shortcut"""
    return translate(text, lang)
