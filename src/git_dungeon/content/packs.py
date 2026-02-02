"""
M3.3 内容包系统

支持 packs/ 目录加载、按解锁过滤、冲突检测
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from .schema import (
    ContentRegistry, ContentPack, CardDef, RelicDef, EventDef,
    CardType, CardRarity, RelicTier, Effect, EventChoice, EventEffect
)


@dataclass
class PackLoader:
    """内容包加载器"""
    packs_dir: Path
    
    def load_pack(self, pack_id: str) -> Optional[ContentPack]:
        """加载单个内容包"""
        pack_path = self.packs_dir / pack_id / "cards.yml"
        if not pack_path.exists():
            return None
        
        try:
            with open(pack_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            pack_info = data.get("pack_info", {})
            
            # 解析卡牌
            cards = []
            for card_data in data.get("cards", []):
                card = self._parse_card(card_data)
                if card:
                    cards.append(card)
            
            # 解析遗物
            relics = []
            for relic_data in data.get("relics", []):
                relic = self._parse_relic(relic_data)
                if relic:
                    relics.append(relic)
            
            # 解析事件
            events = []
            for event_data in data.get("events", []):
                event = self._parse_event(event_data)
                if event:
                    events.append(event)
            
            pack = ContentPack(
                id=pack_id,
                name_key=pack_info.get("name_key", f"pack.{pack_id}.name"),
                desc_key=pack_info.get("desc_key", f"pack.{pack_id}.desc"),
                archetype=pack_info.get("archetype", ""),
                rarity=pack_info.get("rarity", "uncommon"),
                points_cost=pack_info.get("points_cost", 150),
                cards=cards,
                relics=relics,
                events=events
            )
            
            return pack
            
        except Exception as e:
            print(f"⚠️  加载内容包 {pack_id} 失败: {e}")
            return None
    
    def load_all_packs(self) -> Dict[str, ContentPack]:
        """加载所有内容包"""
        packs: Dict[str, ContentPack] = {}
        
        if not self.packs_dir.exists():
            return packs
        
        for item in self.packs_dir.iterdir():
            if item.is_dir():
                pack = self.load_pack(item.name)
                if pack:
                    packs[pack.id] = pack
        
        return packs
    
    def _parse_card(self, data: Dict) -> Optional[CardDef]:
        """解析卡牌定义"""
        try:
            effects = []
            for effect_data in data.get("effects", []):
                effects.append(Effect(
                    type=effect_data.get("type", "damage"),
                    value=effect_data.get("value", 0),
                    target=effect_data.get("target", "enemy"),
                    status=effect_data.get("status"),
                    status_value=effect_data.get("status_value", 0)
                ))
            
            return CardDef(
                id=data["id"],
                name_key=data.get("name_key", f"card.{data['id']}.name"),
                desc_key=data.get("desc_key", f"card.{data['id']}.desc"),
                card_type=CardType(data.get("type", "attack")),
                cost=data.get("cost", 1),
                rarity=CardRarity(data.get("rarity", "common")),
                effects=effects,
                tags=data.get("tags", []),
                upgrade_id=data.get("upgrade_id")
            )
        except Exception as e:
            print(f"⚠️  解析卡牌失败: {e}")
            return None
    
    def _parse_relic(self, data: Dict) -> Optional[RelicDef]:
        """解析遗物定义"""
        try:
            return RelicDef(
                id=data["id"],
                name_key=data.get("name_key", f"relic.{data['id']}.name"),
                desc_key=data.get("desc_key", f"relic.{data['id']}.desc"),
                tier=RelicTier(data.get("tier", "common")),
                effects=data.get("effects", {})
            )
        except Exception as e:
            print(f"⚠️  解析遗物失败: {e}")
            return None
    
    def _parse_event(self, data: Dict) -> Optional[EventDef]:
        """解析事件定义"""
        try:
            choices = []
            for choice_data in data.get("choices", []):
                effects = []
                for effect_data in choice_data.get("effects", []):
                    effects.append(EventEffect(
                        opcode=effect_data.get("opcode", ""),
                        value=effect_data.get("value", 0),
                        target=effect_data.get("target", "player"),
                        condition=effect_data.get("condition")
                    ))
                
                choices.append(EventChoice(
                    id=choice_data.get("id", "default"),
                    text_key=choice_data.get("text_key", ""),
                    effects=effects,
                    condition=choice_data.get("condition")
                ))
            
            return EventDef(
                id=data["id"],
                name_key=data.get("name_key", f"event.{data['id']}.name"),
                desc_key=data.get("desc_key", f"event.{data['id']}.desc"),
                choices=choices,
                conditions=data.get("conditions", {}),
                weights=data.get("weights", {}),
                route_tags=data.get("route_tags", [])
            )
        except Exception as e:
            print(f"⚠️  解析事件失败: {e}")
            return None


def merge_content_with_packs(
    base_registry: ContentRegistry,
    packs_dir: str,
    unlocked_packs: List[str]
) -> ContentRegistry:
    """
    合并基础内容和已解锁内容包
    
    Args:
        base_registry: 基础内容注册表
        packs_dir: packs 目录路径
        unlocked_packs: 已解锁的内容包 ID 列表
    
    Returns:
        合并后的内容注册表
    """
    pack_loader = PackLoader(Path(packs_dir))
    all_packs = pack_loader.load_all_packs()
    
    # 检测 ID 冲突
    conflicts = []
    for pack_id in unlocked_packs:
        if pack_id not in all_packs:
            continue
        pack = all_packs[pack_id]
        
        # 检查卡牌冲突
        for card in pack.cards:
            if card.id in base_registry.cards:
                conflicts.append(f"card:{card.id}")
        
        # 检查遗物冲突
        for relic in pack.relics:
            if relic.id in base_registry.relics:
                conflicts.append(f"relic:{relic.id}")
        
        # 检查事件冲突
        for event in pack.events:
            if event.id in base_registry.events:
                conflicts.append(f"event:{event.id}")
    
    if conflicts:
        print(f"⚠️  内容包 ID 冲突: {conflicts}")
        # 可以选择 fail 或者 warn，这里选择 warn 但继续
    
    # 合并内容
    merged = ContentRegistry(
        cards=base_registry.cards.copy(),
        relics=base_registry.relics.copy(),
        statuses=base_registry.statuses.copy(),
        enemies=base_registry.enemies.copy(),
        archetypes=base_registry.archetypes.copy(),
        events=base_registry.events.copy(),
        characters=base_registry.characters.copy(),
        packs=all_packs
    )
    
    # 添加已解锁包的内容
    for pack_id in unlocked_packs:
        if pack_id not in all_packs:
            continue
        pack = all_packs[pack_id]
        
        # 添加卡牌
        for card in pack.cards:
            merged.cards[card.id] = card
        
        # 添加遗物
        for relic in pack.relics:
            merged.relics[relic.id] = relic
        
        # 添加事件
        for event in pack.events:
            merged.events[event.id] = event
        
        print(f"✅ 已加载内容包: {pack_id} ({len(pack.cards)} 卡, {len(pack.relics)} 遗物)")
    
    return merged


def get_pack_info(packs_dir: str) -> Dict[str, Dict[str, Any]]:
    """获取所有内容包信息（用于显示解锁预览）"""
    pack_loader = PackLoader(Path(packs_dir))
    all_packs = pack_loader.load_all_packs()
    
    info = {}
    for pack_id, pack in all_packs.items():
        info[pack_id] = {
            "name_key": pack.name_key,
            "desc_key": pack.desc_key,
            "archetype": pack.archetype,
            "rarity": pack.rarity,
            "points_cost": pack.points_cost,
            "cards_count": len(pack.cards),
            "relics_count": len(pack.relics),
            "events_count": len(pack.events)
        }
    
    return info
