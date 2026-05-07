"""Small translation helpers for pixel screens."""

from __future__ import annotations

PIXEL_TEXT = {
    "zh_CN": {
        "Press Enter to load repository": "按确认键载入仓库",
        "Enter: Start   S: Settings   Esc/Q: Quit": "确认 开始  S 设置  Esc/Q 退出",
        "Start": "开始",
        "Settings": "设置",
        "LOADING REPOSITORY": "正在载入仓库",
        "Load failed": "载入失败",
        "Enter/Esc: Quit": "确认/Esc 退出",
        "Reading git history...": "正在读取提交历史...",
        "Repository loaded": "仓库已载入",
        "DUNGEON": "地牢",
        "Move to the current room": "移动到当前房间",
        "Press Enter to enter": "按确认键进入",
        "Enter Room": "进入",
        "Claim": "领取",
        "Move": "移动",
        "Arrows/WASD: Move": "方向键移动",
        "Confirm: enter current room": "确认键：进入当前房间",
        "Confirm: claim reward": "确认键：领取奖励",
        "Move to the glowing room": "前往发光房间",
        "Click adjacent room to move": "点击相邻房间移动",
        "Selected room is too far": "选中的房间太远",
        "Current room": "当前房间",
        "Visited room": "已访问房间",
        "Route room": "主线房间",
        "Trap": "陷阱",
        "Trap blocks this path": "陷阱挡住了路",
        "Trap already spent": "陷阱已触发",
        "Trap hit": "触发陷阱",
        "Trap hit: no damage": "触发陷阱：未受伤",
        "Trap defeated you": "你被陷阱击倒了",
        "Press Enter to claim": "按确认键领取",
        "Cache already claimed": "补给已领取",
        "Cache unavailable": "补给不可用",
        "Cache": "补给",
        "Key already claimed": "钥匙已领取",
        "Key unavailable": "钥匙不可用",
        "Key found": "找到钥匙",
        "Key": "钥匙",
        "Vault already claimed": "宝库已领取",
        "Vault unavailable": "宝库不可用",
        "Vault": "宝库",
        "Locked": "锁住了",
        "need": "需要",
        "Iron Key": "铁钥匙",
        "No door there": "那里没有门",
        "No current room": "没有当前房间",
        "No room there": "那里没有房间",
        "PAUSED": "暂停",
        "Resume": "继续",
        "Close Game": "关闭游戏",
        "Esc/Enter: Resume": "Esc/确认：继续",
        "Press Q again to close game": "再次按 Q 关闭游戏",
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
        "Level up": "升级",
        "Escaped battle": "已逃离战斗",
        "REST NODE": "休息点",
        "Pick one real state change": "选择一个实际变化",
        "Heal": "治疗",
        "Focus": "专注",
        "Restore": "恢复",
        "Rest": "休息",
        "Rest result": "休息结果",
        "Attack +2, Max HP +5, HP +5": "攻击+2 生命上限+5 生命+5",
        "1/H: Heal   2/F: Focus": "1/H 治疗  2/F 专注",
        "EVENT": "事件",
        "Dungeon Encounter": "地牢事件",
        "A strange room asks for a choice": "这个房间里出现了一个选择",
        "Safe choice": "稳妥选择",
        "Risky choice": "冒险选择",
        "Treasure choice": "收益选择",
        "Battle choice": "战斗选择",
        "Card choice": "卡牌选择",
        "Relic choice": "遗物选择",
        "Status choice": "状态选择",
        "Unknown choice": "未知选择",
        "restore health": "恢复生命",
        "lose health": "损失生命",
        "gain gold": "获得金币",
        "lose gold": "失去金币",
        "gain card": "获得卡牌",
        "remove card": "移除卡牌",
        "gain relic": "获得遗物",
        "upgrade card": "升级卡牌",
        "change build direction": "改变构筑方向",
        "gain status": "获得状态",
        "start battle": "进入战斗",
        "Event result": "事件结果",
        "No visible change": "没有明显变化",
        "No event definition": "没有事件定义",
        "Choose visibly; effects apply once": "选择后立即生效",
        "Pick": "选择",
        "no effect": "无效果",
        "SHOP": "商店",
        "Unavailable items are disabled": "买不起的物品会灰显",
        "not enough gold": "金币不足",
        "Shop result": "商店结果",
        "Cost": "价格",
        "Health": "生命",
        "Energy": "魔力",
        "Experience": "经验",
        "Max Health": "生命上限",
        "Skip shop": "离开商店",
        "Buy": "购买",
        "Skip": "跳过",
        "Not enough gold": "金币不足",
        "VICTORY": "胜利",
        "GAME OVER": "游戏结束",
        "Enter/Esc/Q: Quit": "确认/Esc/Q 退出",
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

STAT_LABELS = {
    "zh_CN": {
        "hp": "生命",
        "mp": "魔力",
        "attack": "攻击",
        "gold": "金币",
        "exp": "经验",
    },
    "en": {
        "hp": "Health",
        "mp": "Energy",
        "attack": "Attack",
        "gold": "Gold",
        "exp": "Experience",
    },
}


def tr(text: str, lang: str) -> str:
    if lang != "zh_CN":
        return text
    if text == "Trap hit: no HP lost":
        return f"{PIXEL_TEXT['zh_CN']['Trap hit']}: 未损失生命"
    if text.startswith("Trap hit: "):
        return text.replace("Trap hit", PIXEL_TEXT["zh_CN"]["Trap hit"], 1).replace(" HP", " 生命")
    if text.startswith("Cache: "):
        return text.replace("Cache", PIXEL_TEXT["zh_CN"]["Cache"], 1)
    if text.startswith("Vault: "):
        return text.replace("Vault", PIXEL_TEXT["zh_CN"]["Vault"], 1)
    if text.startswith("Key found: "):
        return text.replace("Key found", PIXEL_TEXT["zh_CN"]["Key found"], 1)
    if text.startswith("Locked: need "):
        return text.replace("Locked", PIXEL_TEXT["zh_CN"]["Locked"], 1).replace(
            "need", PIXEL_TEXT["zh_CN"]["need"], 1
        )
    return PIXEL_TEXT["zh_CN"].get(text, text)


def audio_label(label: str, lang: str) -> str:
    if label.startswith("Audio: "):
        return ""
    if lang != "zh_CN":
        return label
    if label.startswith("Audio muted: "):
        return label.replace("Audio muted", tr("Audio muted", lang), 1)
    return label


def stat_label(stat: str, lang: str) -> str:
    labels = STAT_LABELS.get(lang, STAT_LABELS["en"])
    return labels.get(stat, stat)


def stat_value(stat: str, current: int, lang: str, maximum: int | None = None) -> str:
    label = stat_label(stat, lang)
    if maximum is None:
        return f"{label} {current}"
    return f"{label} {current}/{maximum}"


def stat_delta(stat: str, amount: int, lang: str) -> str:
    return f"{stat_label(stat, lang)} {amount:+d}"


def key_label(key_id: str | None, lang: str) -> str:
    if not key_id:
        return ""
    if key_id == "iron_key":
        return tr("Iron Key", lang)
    return key_id.replace("_", " ").title() if lang != "zh_CN" else key_id


def reward_feedback(label: str, heal: int, gold: int, lang: str) -> str:
    display_label = tr(label, lang)
    if lang == "zh_CN":
        zh_parts: list[str] = []
        if heal:
            zh_parts.append(f"+{heal} {stat_label('hp', lang)}")
        if gold:
            zh_parts.append(f"+{gold} {stat_label('gold', lang)}")
        return f"{display_label}：" + (" ".join(zh_parts) if zh_parts else "已领取")
    parts: list[str] = []
    if heal:
        parts.append(f"+{heal} {stat_label('hp', lang)}")
    if gold:
        parts.append(f"+{gold} {stat_label('gold', lang)}")
    return f"{label}: " + (" ".join(parts) if parts else "claimed")


def trap_feedback(damage: int, lang: str) -> str:
    if damage <= 0:
        return tr("Trap hit: no damage", lang)
    return f"{tr('Trap hit', lang)}: {stat_delta('hp', -damage, lang)}"


def battle_reward_feedback(exp: int, gold: int, lang: str, *, level_up: bool = False) -> str:
    parts: list[str] = []
    if exp:
        parts.append(f"+{exp} {stat_label('exp', lang)}")
    if gold:
        parts.append(f"+{gold} {stat_label('gold', lang)}")
    if level_up:
        parts.append(tr("Level up", lang))
    if not parts:
        return tr("Won battle.", lang)
    return f"{tr('Won battle.', lang)} {' '.join(parts)}"


def battle_reward_float(exp: int, gold: int, lang: str) -> str:
    parts: list[str] = []
    if exp:
        parts.append(f"+{exp} {stat_label('exp', lang)}")
    if gold:
        parts.append(f"+{gold} {stat_label('gold', lang)}")
    return " ".join(parts) if parts else tr("Won battle.", lang)


def locked_message(key_id: str | None, lang: str) -> str:
    if lang == "zh_CN":
        return f"{tr('Locked', lang)}：{tr('need', lang)}{key_label(key_id, lang)}"
    return f"Locked: need {key_label(key_id, lang)}"


def skill_cost_text(cost: int, lang: str) -> str:
    return f"{tr('Need', lang)} {cost} {stat_label('mp', lang)}"


def rest_detail(detail: str, lang: str) -> str:
    if detail.startswith("Restore ") and detail.endswith(" HP"):
        amount = detail.removeprefix("Restore ").removesuffix(" HP")
        return f"{tr('Restore', lang)} {amount} {stat_label('hp', lang)}"
    if detail == "Attack +2, Max HP +5, HP +5":
        if lang == "zh_CN":
            return f"{stat_label('attack', lang)}+2  上限+5  {stat_label('hp', lang)}+5"
        return (
            f"{stat_label('attack', lang)} +2  "
            f"{tr('Max Health', lang)} +5  "
            f"{stat_label('hp', lang)} +5"
        )
    return tr(detail, lang)


def rest_result_feedback(message: str, lang: str) -> str:
    if lang == "zh_CN":
        return f"{tr('Rest result', lang)}：{rest_detail(message, lang)}"
    return f"{tr('Rest result', lang)}: {rest_detail(message, lang)}"


def shop_offer_detail(offer: object, lang: str) -> str:
    cost = getattr(offer, "cost")
    heal = getattr(offer, "heal")
    attack = getattr(offer, "attack")
    mp = getattr(offer, "mp")
    max_hp = getattr(offer, "max_hp")
    if lang == "zh_CN":
        zh_parts = [f"{cost}{stat_label('gold', lang)}"]
        if heal:
            zh_parts.append(f"{stat_label('hp', lang)}+{heal}")
        if attack:
            zh_parts.append(f"{stat_label('attack', lang)}+{attack}")
        if mp:
            zh_parts.append(f"{stat_label('mp', lang)}+{mp}")
        if max_hp:
            zh_parts.append(f"上限+{max_hp}")
        return " / ".join(zh_parts)
    parts = [f"{tr('Cost', lang)} {cost} {stat_label('gold', lang)}"]
    if heal:
        parts.append(f"{stat_label('hp', lang)} +{heal}")
    if attack:
        parts.append(f"{stat_label('attack', lang)} +{attack}")
    if mp:
        parts.append(f"{stat_label('mp', lang)} +{mp}")
    if max_hp:
        parts.append(f"{tr('Max Health', lang)} +{max_hp}")
    return " / ".join(parts)


def shop_result_feedback(message: str, lang: str) -> str:
    if message == "skip":
        return tr("Skip shop", lang)
    if lang == "zh_CN":
        return f"{tr('Shop result', lang)}：{tr(message, lang)}"
    return f"{tr('Shop result', lang)}: {tr(message, lang)}"


def event_title(_event_id: str, lang: str) -> str:
    return tr("Dungeon Encounter", lang)


def event_description(_event_id: str, lang: str) -> str:
    return tr("A strange room asks for a choice", lang)


def event_choice_label(index: int, effects: tuple[str, ...], lang: str) -> str:
    label = "Unknown choice"
    if any(effect in effects for effect in ("heal", "upgrade_card")):
        label = "Safe choice"
    if any(effect in effects for effect in ("take_damage", "lose_gold")):
        label = "Risky choice"
    if any(effect in effects for effect in ("gain_gold", "add_relic")):
        label = "Treasure choice"
    if "trigger_battle" in effects:
        label = "Battle choice"
    if "add_card" in effects:
        label = "Card choice"
    if "add_relic" in effects:
        label = "Relic choice"
    return f"{index + 1}. {tr(label, lang)}"


def event_effect_preview(effects: tuple[str, ...], lang: str) -> str:
    labels = {
        "heal": "restore health",
        "take_damage": "lose health",
        "gain_gold": "gain gold",
        "lose_gold": "lose gold",
        "add_card": "gain card",
        "remove_card": "remove card",
        "add_relic": "gain relic",
        "upgrade_card": "upgrade card",
        "modify_bias": "change build direction",
        "apply_status": "gain status",
        "trigger_battle": "start battle",
    }
    parts = [tr(labels[effect], lang) for effect in effects if effect in labels]
    return " / ".join(parts) if parts else tr("No visible change", lang)


def event_result_feedback(hp_delta: int, gold_delta: int, lang: str) -> str:
    if lang == "zh_CN":
        parts: list[str] = []
        if hp_delta:
            parts.append(f"{stat_label('hp', lang)} {hp_delta:+d}")
        if gold_delta:
            parts.append(f"{stat_label('gold', lang)} {gold_delta:+d}")
        return f"{tr('Event result', lang)}：" + (
            " ".join(parts) if parts else tr("No visible change", lang)
        )
    parts = []
    if hp_delta:
        parts.append(f"Health {hp_delta:+d}")
    if gold_delta:
        parts.append(f"Gold {gold_delta:+d}")
    return "Event result: " + (" ".join(parts) if parts else "No visible change")
