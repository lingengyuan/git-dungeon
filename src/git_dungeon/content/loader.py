"""
Content loader - 加载 content/*.yml 文件到 ContentRegistry。
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from .schema import (
    CardDef, RelicDef, EnemyDef, ArchetypeDef, EventDef, StatusDef,
    CardType, CardRarity, RelicTier, EnemyType, EnemyTier, IntentType, StatusType,
    ContentRegistry, Effect, EventChoice, EventEffect
)


class ContentLoader:
    """内容加载器"""
    
    def __init__(self, content_dir: Optional[str] = None):
        """
        初始化加载器
        
        Args:
            content_dir: content 目录路径，默认从项目根目录查找
        """
        if content_dir is None:
            # 默认路径：项目根目录下的 content/
            root = Path(__file__).parent.parent.parent
            content_dir = root / "content"
        self.content_dir = Path(content_dir)
        self.errors: List[str] = []
    
    def load(self) -> ContentRegistry:
        """
        加载所有内容文件
        
        Returns:
            ContentRegistry 实例
        """
        registry = ContentRegistry()
        self.errors = []
        
        # 加载各类内容
        self._load_cards(registry)
        self._load_relics(registry)
        self._load_enemies(registry)
        self._load_archetypes(registry)
        self._load_events(registry)
        self._load_statuses(registry)
        
        return registry
    
    def _load_yaml(self, filename: str) -> Optional[Dict]:
        """加载单个 YAML 文件"""
        filepath = self.content_dir / filename
        if not filepath.exists():
            self.errors.append(f"File not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Error loading {filepath}: {e}")
            return None
    
    def _validate_required_fields(
        self,
        data: Dict,
        required_fields: List[str],
        item_id: str,
        item_type: str
    ) -> bool:
        """验证必填字段"""
        missing = [f for f in required_fields if f not in data]
        if missing:
            self.errors.append(
                f"[{item_type}] {item_id}: Missing required fields: {missing}"
            )
            return False
        return True
    
    def _load_cards(self, registry: ContentRegistry) -> None:
        """加载卡牌定义"""
        data = self._load_yaml("defaults/cards.yml")
        if data is None:
            return
        
        if "cards" not in data:
            self.errors.append("[cards] No 'cards' key found")
            return
        
        for i, card_data in enumerate(data.get("cards", [])):
            card_id = card_data.get("id", f"card_{i}")
            
            if not self._validate_required_fields(
                card_data, ["id", "name_key", "desc_key", "cost"], card_id, "card"
            ):
                continue
            
            # 解析卡牌类型
            card_type_str = card_data.get("type", "skill")
            try:
                card_type = CardType(card_type_str)
            except ValueError:
                self.errors.append(f"[card] {card_id}: Invalid type '{card_type_str}'")
                continue
            
            # 解析稀有度
            rarity_str = card_data.get("rarity", "common")
            try:
                rarity = CardRarity(rarity_str)
            except ValueError:
                self.errors.append(f"[card] {card_id}: Invalid rarity '{rarity_str}'")
                continue
            
            # 解析效果列表
            effects = []
            for effect_data in card_data.get("effects", []):
                effect = Effect(
                    type=effect_data.get("type", "damage"),
                    value=effect_data.get("value", 0),
                    target=effect_data.get("target", "enemy"),
                    status=effect_data.get("status"),
                    status_value=effect_data.get("status_value", 0)
                )
                effects.append(effect)
            
            card = CardDef(
                id=card_id,
                name_key=card_data["name_key"],
                desc_key=card_data["desc_key"],
                card_type=card_type,
                cost=card_data["cost"],
                rarity=rarity,
                effects=effects,
                tags=card_data.get("tags", []),
                upgrade_id=card_data.get("upgrade_id")
            )
            
            # 检查重复 ID
            if card_id in registry.cards:
                self.errors.append(f"[card] Duplicate ID: {card_id}")
            else:
                registry.cards[card_id] = card
    
    def _load_relics(self, registry: ContentRegistry) -> None:
        """加载遗物定义"""
        data = self._load_yaml("defaults/relics.yml")
        if data is None:
            return
        
        if "relics" not in data:
            self.errors.append("[relics] No 'relics' key found")
            return
        
        for i, relic_data in enumerate(data.get("relics", [])):
            relic_id = relic_data.get("id", f"relic_{i}")
            
            if not self._validate_required_fields(
                relic_data, ["id", "name_key", "desc_key"], relic_id, "relic"
            ):
                continue
            
            # 解析稀有度
            tier_str = relic_data.get("tier", "common")
            try:
                tier = RelicTier(tier_str)
            except ValueError:
                self.errors.append(f"[relic] {relic_id}: Invalid tier '{tier_str}'")
                continue
            
            relic = RelicDef(
                id=relic_id,
                name_key=relic_data["name_key"],
                desc_key=relic_data["desc_key"],
                tier=tier,
                effects=relic_data.get("effects", {})
            )
            
            if relic_id in registry.relics:
                self.errors.append(f"[relic] Duplicate ID: {relic_id}")
            else:
                registry.relics[relic_id] = relic
    
    def _load_enemies(self, registry: ContentRegistry) -> None:
        """加载敌人定义"""
        data = self._load_yaml("defaults/enemies.yml")
        if data is None:
            return
        
        if "enemies" not in data:
            self.errors.append("[enemies] No 'enemies' key found")
            return
        
        for i, enemy_data in enumerate(data.get("enemies", [])):
            enemy_id = enemy_data.get("id", f"enemy_{i}")
            
            if not self._validate_required_fields(
                enemy_data, ["id", "name_key", "type", "base_hp", "base_damage"],
                enemy_id, "enemy"
            ):
                continue
            
            # 解析敌人类型
            type_str = enemy_data.get("type", "feat")
            try:
                enemy_type = EnemyType(type_str)
            except ValueError:
                self.errors.append(f"[enemy] {enemy_id}: Invalid type '{type_str}'")
                continue
            
            # 解析敌人层级
            tier_str = enemy_data.get("tier", "normal")
            try:
                tier = EnemyTier(tier_str)
            except ValueError:
                self.errors.append(f"[enemy] {enemy_id}: Invalid tier '{tier_str}'")
                tier = EnemyTier.NORMAL
            
            enemy = EnemyDef(
                id=enemy_id,
                name_key=enemy_data["name_key"],
                enemy_type=enemy_type,
                base_hp=enemy_data["base_hp"],
                base_damage=enemy_data["base_damage"],
                base_block=enemy_data.get("base_block", 0),
                tier=tier,
                ai_pattern=enemy_data.get("ai_pattern", "basic"),
                status_resist=enemy_data.get("status_resist", []),
                status_vulnerable=enemy_data.get("status_vulnerable", []),
                intent_preference=enemy_data.get("intent_preference", []),
                is_boss=tier == EnemyTier.BOSS,
                gold_multiplier=enemy_data.get("gold_multiplier", 1.0),
                exp_multiplier=enemy_data.get("exp_multiplier", 1.0)
            )
            
            if enemy_id in registry.enemies:
                self.errors.append(f"[enemy] Duplicate ID: {enemy_id}")
            else:
                registry.enemies[enemy_id] = enemy
    
    def _load_archetypes(self, registry: ContentRegistry) -> None:
        """加载流派定义"""
        data = self._load_yaml("defaults/archetypes.yml")
        if data is None:
            return
        
        if "archetypes" not in data:
            self.errors.append("[archetypes] No 'archetypes' key found")
            return
        
        for i, arch_data in enumerate(data.get("archetypes", [])):
            arch_id = arch_data.get("id", f"archetype_{i}")
            
            if not self._validate_required_fields(
                arch_data, ["id", "name_key", "desc_key"], arch_id, "archetype"
            ):
                continue
            
            archetype = ArchetypeDef(
                id=arch_id,
                name_key=arch_data["name_key"],
                desc_key=arch_data["desc_key"],
                tags=arch_data.get("tags", []),
                starter_cards=arch_data.get("starter_cards", []),
                starter_relics=arch_data.get("starter_relics", [])
            )
            
            if arch_id in registry.archetypes:
                self.errors.append(f"[archetype] Duplicate ID: {arch_id}")
            else:
                registry.archetypes[arch_id] = archetype
    
    def _load_events(self, registry: ContentRegistry) -> None:
        """加载事件定义"""
        data = self._load_yaml("defaults/events.yml")
        if data is None:
            return
        
        if "events" not in data:
            self.errors.append("[events] No 'events' key found")
            return
        
        for i, event_data in enumerate(data.get("events", [])):
            event_id = event_data.get("id", f"event_{i}")
            
            if not self._validate_required_fields(
                event_data, ["id", "name_key", "desc_key"], event_id, "event"
            ):
                continue
            
            # 解析 choices 为 EventChoice 对象列表
            choices = []
            for j, choice_data in enumerate(event_data.get("choices", [])):
                choice_id = choice_data.get("id", f"choice_{j}")
                choice = EventChoice(
                    id=choice_id,
                    text_key=choice_data.get("text_key", ""),
                    effects=choice_data.get("effects", []),  # List[Dict] - effects
                    condition=choice_data.get("condition")
                )
                choices.append(choice)
            
            event = EventDef(
                id=event_id,
                name_key=event_data["name_key"],
                desc_key=event_data["desc_key"],
                choices=choices,
                conditions=event_data.get("conditions", {}),
                weights=event_data.get("weights", {}),
                route_tags=event_data.get("route_tags", [])
            )
            
            if event_id in registry.events:
                self.errors.append(f"[event] Duplicate ID: {event_id}")
            else:
                registry.events[event_id] = event
    
    def _load_statuses(self, registry: ContentRegistry) -> None:
        """加载状态定义"""
        data = self._load_yaml("defaults/statuses.yml")
        if data is None:
            return
        
        if "statuses" not in data:
            self.errors.append("[statuses] No 'statuses' key found")
            return
        
        for i, status_data in enumerate(data.get("statuses", [])):
            status_id = status_data.get("id", f"status_{i}")
            
            if not self._validate_required_fields(
                status_data, ["id", "name_key", "desc_key", "type"], status_id, "status"
            ):
                continue
            
            # 解析状态类型
            type_str = status_data.get("type", "block")
            try:
                status_type = StatusType(type_str)
            except ValueError:
                self.errors.append(f"[status] {status_id}: Invalid type '{type_str}'")
                continue
            
            status = StatusDef(
                id=status_id,
                name_key=status_data["name_key"],
                desc_key=status_data["desc_key"],
                status_type=status_type,
                max_stacks=status_data.get("max_stacks", 999),
                duration_type=status_data.get("duration_type", "indefinite")
            )
            
            if status_id in registry.statuses:
                self.errors.append(f"[status] Duplicate ID: {status_id}")
            else:
                registry.statuses[status_id] = status
    
    def validate_i18n_keys(
        self,
        i18n_keys: Dict[str, str]
    ) -> List[str]:
        """
        验证所有内容定义的 i18n key 是否存在
        
        Args:
            i18n_keys: 已加载的翻译 key 字典
            
        Returns:
            缺失的 key 列表
        """
        missing_keys = []
        
        for card in registry.cards.values():
            if card.name_key not in i18n_keys:
                missing_keys.append(f"card.{card.id}.name")
            if card.desc_key not in i18n_keys:
                missing_keys.append(f"card.{card.id}.desc")
        
        for relic in registry.relics.values():
            if relic.name_key not in i18n_keys:
                missing_keys.append(f"relic.{relic.id}.name")
            if relic.desc_key not in i18n_keys:
                missing_keys.append(f"relic.{relic.id}.desc")
        
        return missing_keys
    
    def get_errors(self) -> List[str]:
        """获取加载过程中的错误"""
        return self.errors.copy()


def load_content(content_dir: Optional[str] = None) -> ContentRegistry:
    """
    便捷函数：加载所有内容
    
    Args:
        content_dir: content 目录路径
        
    Returns:
        ContentRegistry 实例
    """
    loader = ContentLoader(content_dir)
    registry = loader.load()
    
    if loader.get_errors():
        raise ValueError(f"Content loading errors: {loader.get_errors()}")
    
    return registry
