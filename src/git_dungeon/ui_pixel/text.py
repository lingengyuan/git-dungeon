"""Small translation helpers for pixel screens."""

from __future__ import annotations

PIXEL_TEXT = {
    "zh_CN": {
        "Press Enter to load repository": "按 Enter 载入仓库",
        "Enter: Start   S: Settings   Esc/Q: Quit": "Enter 开始  S 设置  Esc/Q 退出",
        "Start": "开始",
        "Settings": "设置",
        "LOADING REPOSITORY": "正在载入仓库",
        "Load failed": "载入失败",
        "Enter/Esc: Quit": "Enter/Esc 退出",
        "Reading git history...": "正在读取提交历史...",
        "Repository loaded": "仓库已载入",
        "ROUTE": "路线",
        "DUNGEON": "地牢",
        "Choose the current non-combat node": "选择当前节点",
        "Move to the current room": "移动到当前房间",
        "Press Enter to enter": "按 Enter 进入",
        "Enter Room": "进入",
        "Arrows/WASD: Move": "方向键/WASD 移动",
        "Trap blocks this path": "陷阱挡住了路",
        "Trap already spent": "陷阱已触发",
        "Trap hit": "触发陷阱",
        "No door there": "那里没有门",
        "No current room": "没有当前房间",
        "Open Node": "打开节点",
        "Open Battle": "进入战斗",
        "Open Elite": "进入精英战",
        "Open Boss": "进入 Boss",
        "Open Event": "打开事件",
        "Open Rest": "休息",
        "Open Shop": "进入商店",
        "No current node": "没有当前节点",
        "Node is not playable yet": "当前节点暂不可用",
        "BATTLE": "战斗",
        "ELITE": "精英",
        "BOSS": "Boss",
        "Turn": "回合",
        "Developer": "开发者",
        "Attack": "攻击",
        "Defend": "防御",
        "Skill": "技能",
        "Escape": "逃跑",
        "Need": "需要",
        "Cannot escape from Boss battle": "Boss 战不能逃跑",
        "Battle started": "战斗开始",
        "Dealt": "造成",
        "Took": "受到",
        "Critical": "暴击",
        "Defended": "防御",
        "Escaped": "已逃跑",
        "Won battle.": "战斗胜利。",
        "Escaped battle": "已逃离战斗",
        "REST NODE": "休息点",
        "Pick one real state change": "选择一个实际变化",
        "Heal": "治疗",
        "Focus": "专注",
        "Restore": "恢复",
        "Attack +2, Max HP +5, HP +5": "攻击+2 生命上限+5 生命+5",
        "1/H: Heal   2/F: Focus": "1/H 治疗  2/F 专注",
        "EVENT": "事件",
        "No event definition": "没有事件定义",
        "Choose visibly; effects apply once": "选择后立即生效",
        "Pick": "选择",
        "no effect": "无效果",
        "SHOP": "商店",
        "Unavailable items are disabled": "买不起的物品会灰显",
        "not enough gold": "金币不足",
        "Buy": "购买",
        "Skip": "跳过",
        "Not enough gold": "金币不足",
        "VICTORY": "胜利",
        "GAME OVER": "游戏结束",
        "Enter/Esc/Q: Quit": "Enter/Esc/Q 退出",
        "Audio muted": "音频静音",
        "Audio": "音频",
        "ready": "就绪",
        "SETTINGS": "设置",
        "BGM Volume": "音乐音量",
        "SFX Volume": "音效音量",
        "Language": "语言",
        "Window": "窗口",
        "Windowed": "窗口",
        "Fullscreen": "全屏",
        "Save": "保存",
        "Back": "返回",
        "Saved": "已保存",
        "Save failed": "保存失败",
        "Restart applies window mode": "窗口模式重启后生效",
        "settings damaged": "设置损坏",
        "settings write failed": "设置写入失败",
    }
}


def tr(text: str, lang: str) -> str:
    if lang != "zh_CN":
        return text
    if text == "Trap hit: no HP lost":
        return f"{PIXEL_TEXT['zh_CN']['Trap hit']}: 未损失生命"
    if text.startswith("Trap hit: "):
        return text.replace("Trap hit", PIXEL_TEXT["zh_CN"]["Trap hit"], 1)
    return PIXEL_TEXT["zh_CN"].get(text, text)


def audio_label(label: str, lang: str) -> str:
    if lang != "zh_CN":
        return label
    if label.startswith("Audio muted: "):
        return label.replace("Audio muted", tr("Audio muted", lang), 1)
    if label.startswith("Audio: "):
        return label.replace("Audio", tr("Audio", lang), 1).replace("ready", tr("ready", lang))
    return label
