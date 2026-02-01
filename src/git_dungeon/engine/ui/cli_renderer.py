# cli_renderer.py - CLI renderer for game events

"""
CLI renderer that displays GameEvents in a human-readable format.
This is the "output" side of the event-driven architecture.
"""

from typing import List, Optional
from datetime import datetime

from git_dungeon.engine import GameEvent, EventType, GameState, Action


class CLIRenderer:
    """Render game events and state to CLI output."""
    
    # Theme characters
    BOX_HORIZONTAL = "─"
    BOX_VERTICAL = "│"
    BOX_CORNER = "┌"
    BOX_CORNER_END = "└"
    BOX_CORNER_RIGHT = "┐"
    BOX_CORNER_END_RIGHT = "┘"
    BOX_T_LEFT = "├"
    BOX_T_RIGHT = "┤"
    BOX_T_DOWN = "┬"
    BOX_T_UP = "┴"
    BOX_CROSS = "┼"
    
    # Emoji mappings
    EMOJI = {
        EventType.GAME_STARTED: "🎮",
        EventType.GAME_SAVED: "💾",
        EventType.GAME_LOADED: "📂",
        EventType.GAME_ENDED: "🏁",
        EventType.BATTLE_STARTED: "⚔️",
        EventType.BATTLE_ENDED: "✅",
        EventType.PLAYER_ACTION: "👤",
        EventType.ENEMY_ACTION: "👾",
        EventType.DAMAGE_DEALT: "💥",
        EventType.STATUS_APPLIED: "✨",
        EventType.STATUS_REMOVED: "💨",
        EventType.CRITICAL_HIT: "💥",
        EventType.EVADED: "💨",
        EventType.EXP_GAINED: "⭐",
        EventType.LEVEL_UP: "🆙",
        EventType.STAT_CHANGED: "📊",
        EventType.ITEM_DROPPED: "🎁",
        EventType.ITEM_PICKED_UP: "📥",
        EventType.ITEM_EQUIPPED: "⚔️",
        EventType.ITEM_CONSUMED: "🧪",
        EventType.GOLD_GAINED: "💰",
        EventType.GOLD_SPENT: "💸",
        EventType.CHAPTER_STARTED: "📖",
        EventType.CHAPTER_COMPLETED: "🎉",
        EventType.ENEMY_DEFEATED: "💀",
        EventType.SHOP_ENTERED: "🏪",
        EventType.SHOP_EXITED: "🚪",
        EventType.ITEM_PURCHASED: "🛒",
        EventType.ITEM_SOLD: "💱",
        EventType.BOSS_SPAWNED: "👹",
        EventType.BOSS_DEFEATED: "👑",
        EventType.BOSS_ABILITY: "🌀",
        EventType.ERROR: "❌",
        EventType.WARNING: "⚠️",
    }
    
    def __init__(self, verbose: bool = False, compact: bool = False):
        self.verbose = verbose
        self.compact = compact
    
    def render_banner(self) -> str:
        """Render game banner."""
        return f"""
{self.BOX_CORNER}{self.BOX_HORIZONTAL * 46}{self.BOX_CORNER_RIGHT}
{self.BOX_VERTICAL}  {'G I T   D U N G E O N':^44}  {self.BOX_VERTICAL}
{self.BOX_VERTICAL}  {'Battle through your commits!':^44}  {self.BOX_VERTICAL}
{self.BOX_CORNER_END}{self.BOX_HORIZONTAL * 46}{self.BOX_CORNER_END_RIGHT}
"""
    
    def render_status(self, state: GameState) -> str:
        """Render current game status."""
        player = state.player.character
        
        lines = [
            f"",
            f"{self.BOX_HORIZONTAL * 40}",
            f"📍 Location: {'Game Over' if state.is_game_over else f'Commit #{state.current_commit_index}'}",
            f"💀 Enemies defeated: {len(state.enemies_defeated)}",
            f"{self.BOX_HORIZONTAL * 40}",
            f"👤 {player.name} (Level {player.level})",
            f"   HP: {player.current_hp}/{player.stats.hp.value} | MP: {player.current_mp}/{player.stats.mp.value}",
            f"   ATK: {player.stats.attack.value} | DEF: {player.stats.defense.value}",
            f"   EXP: {player.experience}/{player.experience_to_next}",
            f"   Gold: {state.player.gold}",
            f"{self.BOX_HORIZONTAL * 40}",
        ]
        
        if state.current_enemy:
            enemy = state.current_enemy
            lines.extend([
                f"👾 Enemy: {enemy.name}",
                f"   HP: {enemy.current_hp}/{enemy.max_hp} | ATK: {enemy.attack} | DEF: {enemy.defense}",
            ])
        
        return "\n".join(lines)
    
    def render_events(self, events: List[GameEvent]) -> str:
        """Render a list of events."""
        if not events:
            return ""
        
        lines = []
        
        for event in events:
            rendered = self.render_event(event)
            if rendered:
                lines.append(rendered)
        
        return "\n".join(lines)
    
    def render_event(self, event: GameEvent) -> Optional[str]:
        """Render a single event."""
        emoji = self.EMOJI.get(event.type, "📌")
        
        if self.compact:
            return self._render_event_compact(event, emoji)
        else:
            return self._render_event_verbose(event, emoji)
    
    def _render_event_verbose(self, event: GameEvent, emoji: str) -> str:
        """Render event with full details."""
        data = event.data
        
        if event.type == EventType.BATTLE_STARTED:
            return f"""
{self.BOX_HORIZONTAL * 40}
{emoji} BATTLE STARTED!
   Enemy: {data.get('enemy_name', 'Unknown')}
   HP: {data.get('enemy_hp', 0)}/{data.get('enemy_max_hp', 0)}
{self.BOX_HORIZONTAL * 40}"""
        
        elif event.type == EventType.DAMAGE_DEALT:
            src = data.get('src_type', 'unknown')
            dst = data.get('dst_type', 'unknown')
            amount = data.get('amount', 0)
            is_crit = data.get('is_critical', False)
            is_evaded = data.get('is_evaded', False)
            
            if is_evaded:
                return f"{emoji} {src.upper()} attacked but was EVADED!"
            elif is_crit:
                return f"{emoji} ⚡ CRITICAL! {src.upper()} deals {amount} damage to {dst.upper()}!"
            else:
                return f"{emoji} {src.upper()} deals {amount} damage to {dst.upper()}."
        
        elif event.type == EventType.ENEMY_DEFEATED:
            return f"""
💀 ENEMY DEFEATED: {data.get('enemy_name', 'Unknown')}
   EXP: +{data.get('exp_reward', 0)} | Gold: +{data.get('gold_reward', 0)}"""
        
        elif event.type == EventType.EXP_GAINED:
            return f"⭐ Gained {data.get('amount', 0)} EXP ({data.get('reason', '')})"
        
        elif event.type == EventType.LEVEL_UP:
            return f"""
🆙 LEVEL UP!
   Level: {data.get('old_level', 0)} → {data.get('new_level', 0)}
   HP: +{data.get('hp_gain', 0)} | MP: +{data.get('mp_gain', 0)}
   ATK: +{data.get('atk_gain', 0)} | DEF: +{data.get('def_gain', 0)}"""
        
        elif event.type == EventType.GOLD_GAINED:
            return f"💰 +{data.get('amount', 0)} Gold ({data.get('reason', '')})"
        
        elif event.type == EventType.ITEM_DROPPED:
            rarity_colors = {
                "common": "⚪",
                "rare": "🔵",
                "epic": "🟣",
                "legendary": "🟡",
                "corrupted": "🔴",
            }
            color = rarity_colors.get(data.get('rarity', 'common'), "⚪")
            return f"{color} Dropped: {data.get('item_name', 'Unknown')} ({data.get('rarity', '')})"
        
        elif event.type == EventType.STATUS_APPLIED:
            return f"✨ {data.get('target', '')} gained {data.get('status', '')} ({data.get('duration', 1)} turns)"
        
        elif event.type == EventType.CHAPTER_STARTED:
            return f"""
📖 CHAPTER STARTED: {data.get('chapter_name', 'Unknown')}
{self.BOX_HORIZONTAL * 40}"""
        
        elif event.type == EventType.CHAPTER_COMPLETED:
            return f"""
🎉 CHAPTER COMPLETE: {data.get('chapter_name', 'Unknown')}
   Enemies: {data.get('enemies_defeated', 0)}
   Gold: +{data.get('gold_reward', 0)} | EXP: +{data.get('exp_reward', 0)}"""
        
        elif event.type == EventType.GAME_ENDED:
            result = data.get('result', '')
            if result == 'victory':
                return """
🏆 VICTORY!
   All enemies have been defeated!
   Congratulations, brave developer!"""
            elif result == 'defeat':
                return """
💀 GAME OVER
   You have been defeated...
   But your journey continues! Try again!"""
            else:
                return f"🏁 Game Ended: {result}"
        
        elif event.type == EventType.ERROR:
            return f"❌ ERROR: {data.get('message', 'Unknown error')}"
        
        elif event.type == EventType.WARNING:
            return f"⚠️  WARNING: {data.get('message', '')}"
        
        elif self.verbose:
            return f"{emoji} {event.type.value}: {event.summary()}"
        
        return None
    
    def _render_event_compact(self, event: GameEvent, emoji: str) -> str:
        """Render event in compact single-line format."""
        data = event.data
        
        if event.type == EventType.BATTLE_STARTED:
            return f"{emoji} ⚔️  vs {data.get('enemy_name', '?')} (HP:{data.get('enemy_hp', 0)})"
        elif event.type == EventType.DAMAGE_DEALT:
            if data.get('is_evaded'):
                return f"{emoji} {data.get('src_type', '')} evaded!"
            return f"{emoji} {data.get('src_type', '')}→{data.get('dst_type', '')} {data.get('amount', 0)} dmg"
        elif event.type == EventType.ENEMY_DEFEATED:
            return f"💀 Defeated! +{data.get('exp_reward', 0)} EXP"
        elif event.type == EventType.LEVEL_UP:
            return f"🆙 LVL {data.get('old_level', 0)}→{data.get('new_level', 0)}"
        elif event.type == EventType.EXP_GAINED:
            return f"⭐ +{data.get('amount', 0)} EXP"
        elif event.type == EventType.GOLD_GAINED:
            return f"💰 +{data.get('amount', 0)} gold"
        elif event.type == EventType.ERROR:
            return f"❌ {data.get('message', '')[:50]}"
        else:
            return f"{emoji} {event.type.value}"
    
    def render_combat_menu(self) -> str:
        """Render combat action menu."""
        return """
🎯 YOUR TURN!
   [1] ⚔️  Attack    [2] 🛡️  Defend
   [3] ✨  Skill     [4] 🏃  Escape
   
> """
    
    def render_combat_status(
        self,
        player_hp: int, player_max_hp: int,
        player_mp: int, player_max_mp: int,
        enemy_name: str, enemy_hp: int, enemy_max_hp: int
    ) -> str:
        """Render combat status display."""
        # HP bar
        player_hp_bar = self._render_hp_bar(player_hp, player_max_hp)
        enemy_hp_bar = self._render_hp_bar(enemy_hp, enemy_max_hp)
        
        return f"""
{self.BOX_HORIZONTAL * 40}
👤 DEVELOPER              👾 {enemy_name}
{player_hp_bar}          {enemy_hp_bar}
MP: {player_mp}/{player_max_mp}
{self.BOX_HORIZONTAL * 40}"""
    
    def _render_hp_bar(self, current: int, maximum: int, width: int = 15) -> str:
        """Render HP bar."""
        if maximum <= 0:
            return " " * width
        
        ratio = current / maximum
        filled = int(ratio * width)
        
        # Color indicators
        if ratio > 0.6:
            color = "🟢"
        elif ratio > 0.3:
            color = "🟡"
        else:
            color = "🔴"
        
        bar = "█" * filled + "░" * (width - filled)
        return f"{color} HP:{current:3}/{maximum:3} |{bar}|"
    
    def render_save_confirmation(self, save_id: str) -> str:
        """Render save confirmation."""
        return f"""
💾 Game Saved!
   Save ID: {save_id}
   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    def render_help(self) -> str:
        """Render help message."""
        return """
🗡️  GIT DUNGEON - COMMANDS
════════════════════════════════════
   start          - Start a new game
   load <save>    - Load a saved game
   save           - Save current game
   quit           - Quit the game
   help           - Show this message
   
🎮 COMBAT COMMANDS
   attack         - Attack the enemy
   defend         - Enter defensive stance
   skill <name>   - Use a skill
   escape         - Try to escape
"""
