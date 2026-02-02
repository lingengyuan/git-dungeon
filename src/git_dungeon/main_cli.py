#!/usr/bin/env python3
"""
Git Dungeon - Main CLI Entry Point

Features:
- M0: Event-driven architecture
- M1: Chapter system + Shop
- M2: Boss battles
- M3: Economy/Shop system
- M4: Skill system
"""

import os
import re
import subprocess
import tempfile
import argparse
from typing import Optional, Any

from git_dungeon.engine import (
    Engine, GameState, EnemyState,
    create_rng, EventType,
)
from git_dungeon.engine.rules import (
    ChapterSystem, ShopSystem, PlayerInventory,
    CombatRules, ProgressionRules,
    BossSystem, BossState,
)
from git_dungeon.config import GameConfig
from git_dungeon.core.git_parser import GitParser, CommitInfo
from git_dungeon.i18n import i18n
from git_dungeon.i18n.translations import get_translation


class GitDungeonCLI:
    """Main CLI game with chapter and shop support."""
    
    def __init__(self, seed: Optional[int] = None, verbose: bool = False, auto_mode: bool = False, lang: str = "en"):
        self.seed = seed
        self.lang = lang
        self.verbose = verbose
        
        # Load language
        i18n.load_language(lang)
        
        self.rng = create_rng(seed)
        self.engine = Engine(rng=self.rng)
        self.combat_rules = CombatRules(rng=self.rng)
        self.progression_rules = ProgressionRules(rng=self.rng)
        self.chapter_system = ChapterSystem(rng=self.rng)
        self.shop_system = ShopSystem(rng=self.rng)
        self.boss_system = BossSystem(rng=self.rng)
        
        self.state: GameState | None = None
        self.repo_info: Any = None
        self.inventory = PlayerInventory()
        self.current_shop: Any = None
        self.current_boss: Optional[BossState] = None
        self.verbose = verbose
        self.auto_mode = auto_mode
    
    def _t(self, text: str) -> str:
        """Translate text based on current language."""
        if self.lang == "zh_CN":
            return get_translation(text, "zh_CN")  # type: ignore[no-any-return]
        return text
    
    def start(self, repo_input: str) -> bool:
        """Start game with chapter system."""
        # Handle GitHub URL or local path
        if self._is_github_url(repo_input):
            repo_path = self._clone_github_repo(repo_input)
            if not repo_path:
                return False
        else:
            repo_path = repo_input
            if not os.path.exists(repo_path):
                print(f"❌ Repository not found: {repo_path}")
                return False
        
        # Load repository
        print(self._t("Loading repository..."))
        config = GameConfig()
        parser = GitParser(config)
        
        try:
            parser.load_repository(repo_path)
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            return False
        
        commits = parser.get_commit_history()
        if not commits:
            print("❌ No commits found")
            return False
        
        print(f"{self._t('Loaded')} {len(commits)} {self._t('commits')}!")
        
        # Parse chapters
        self.chapter_system.parse_chapters(commits)
        
        print(f"{self._t('Divided into')} {len(self.chapter_system.chapters)} {self._t('chapters')}:")
        print(self.chapter_system.get_chapter_summary())
        
        # Initialize state
        self.state = GameState(
            seed=self.seed,
            repo_path=repo_path,
            total_commits=len(commits),
            current_commit_index=0,
            difficulty="normal"
        )
        self.state.player.character.current_hp = 100
        self.state.player.character.current_mp = 50
        
        # Show banner
        self._print_banner()
        
        # Show chapter intro
        chapter = self.chapter_system.get_current_chapter()
        if chapter:
            self._print_chapter_intro(chapter)
        
        # Start game loop
        return self._game_loop()
    
    def _game_loop(self) -> bool:
        """Main game loop with chapter progression."""
        while self.state and not self.state.is_game_over:
            # Get current chapter
            chapter = self.chapter_system.get_current_chapter()
            
            if not chapter:
                # No more chapters - Victory!
                self._print_victory()
                return True
            
            # Check if we need to fight the boss
            if chapter.enemies_defeated >= chapter.enemy_count and chapter.is_boss_chapter:
                if not self._boss_combat(chapter):
                    self._print_defeat()
                    return False
                # Boss defeated, complete chapter
                if not self._complete_chapter():
                    return False
                continue
            
            # Get current commit
            if self.state.current_commit_index >= self.state.total_commits:
                # Chapter complete!
                if not self._complete_chapter():
                    return False
                continue
            
            commit = self._get_current_commit()
            if not commit:
                break
            
            # Create enemy
            enemy = self._create_enemy(commit)
            
            # Combat
            if not self._combat(enemy, chapter):
                self._print_defeat()
                return False
            
            # Enemy defeated
            self.state.current_commit_index += 1
            self.state.enemies_defeated.append(commit.hexsha[:7])
            chapter.enemies_defeated += 1
            
            # Rewards
            self._grant_rewards(enemy, chapter)
            
            # Check chapter complete
            if chapter.enemies_defeated >= chapter.enemy_count:
                if not self._complete_chapter():
                    return False
        
        return True
    
    def _combat(self, enemy: EnemyState, chapter: Any) -> bool:
        """Combat with chapter context."""
        if not self.state:
            return False
        self.state.in_combat = True
        self.state.current_enemy = enemy
        
        print(f"\n{'─'*50}")
        
        # Show chapter context
        if chapter.is_boss_chapter:
            print(f"{self._t('BOSS BATTLE')}: {enemy.name}")
            print(f"📖 Chapter: {chapter.name}")
        else:
            print(f"⚔️  {chapter.name}: {enemy.name}")
        
        print(f"{'─'*50}")
        
        turn = 0
        while self.state and self.state.in_combat:
            turn += 1
            
            self._print_combat_status(enemy)
            choice = self._get_combat_choice()
            
            player = self.state.player.character
            
            if choice == "1":  # Attack
                is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 1.5)
                damage = int((player.stats.attack.value + 5) * mult)
                actual = enemy.take_damage(damage)
                
                crit_str = " ⚡CRITICAL!" if is_crit else ""
                print(f"   ⚔️  You attack {enemy.name} for {actual} damage{crit_str}!")
                
                if not enemy.is_alive:
                    print(f"   💀 {enemy.name} defeated!")
                    return True
            
            elif choice == "2":  # Defend
                player.is_defending = True
                print("   🛡️  Defensive stance!")
            
            elif choice == "3":  # Skill
                if player.current_mp >= 10:
                    player.current_mp -= 10
                    is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 2.0)
                    damage = int((player.stats.attack.value + 5) * 2 * mult)
                    actual = enemy.take_damage(damage)
                    print(f"   ✨ Skill! {enemy.name} takes {actual} damage!")
                    if not enemy.is_alive:
                        print(f"   💀 {enemy.name} defeated!")
                        return True
                else:
                    print(f"   ⚠️  Need 10 MP, have {player.current_mp}")
                    continue
            
            elif choice == "4":  # Escape/Shop
                if chapter.config.shop_enabled and turn % 3 == 0:
                    self._open_shop(chapter)
                elif self.combat_rules.roll_escape(0.7):
                    print("   🏃  Escaped!")
                    self.state.in_combat = False
                    return False
                else:
                    print("   ❌  Escape failed!")
            
            else:
                damage = player.stats.attack.value + 5
                actual = enemy.take_damage(damage)
                print(f"   ⚔️  Attack for {actual} damage!")
                if not enemy.is_alive:
                    print(f"   💀 {enemy.name} defeated!")
                    return True
            
            # Enemy turn
            if enemy.is_alive:
                damage = enemy.attack
                if getattr(player, 'is_defending', False):
                    damage = damage // 2
                    player.is_defending = False
                    print(f"   🛡️  Defense: {damage} damage!")
                
                actual = player.take_damage(damage)
                print(f"   💥 {enemy.name} attacks for {actual} damage!")
                
                if not player.is_alive:
                    print("   💀 Defeated!")
                    return False
        
        return False
    
    def _boss_combat(self, chapter: Any) -> bool:
        """Boss battle."""
        # Create boss
        self.current_boss = self.chapter_system.get_chapter_boss(chapter, self.boss_system)
        if not self.current_boss:
            return True
        
        boss = self.current_boss
        
        # Print boss intro
        print(self.boss_system.render_boss_intro(boss))
        
        if not self.auto_mode:
            input("\n按回车开始 Boss 战...")
        
        if not self.state:
            return False
        self.state.in_combat = True
        turn = 0
        
        while self.state and self.state.in_combat and boss.is_alive:
            turn += 1
            
            # Tick abilities
            boss.tick_abilities()
            
            print(self.boss_system.render_boss_status(boss))
            self._print_combat_status_for_boss()
            choice = self._get_combat_choice()
            
            player = self.state.player.character
            
            if choice == "1":  # Attack
                is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 1.5)
                damage = int((player.stats.attack.value + 10) * mult)
                actual = boss.take_damage(damage)
                
                crit_str = " ⚡CRITICAL!" if is_crit else ""
                print(f"   ⚔️  You attack {boss.name} for {actual} damage{crit_str}!")
                
                # Show phase change
                if boss.is_enraged and not hasattr(self, '_enrage_announced'):
                    print(f"\n   🔥 {boss.name} IS ENRAGED! 🔥")
                    self._enrage_announced = True
                
                if not boss.is_alive:
                    print(f"\n   💀 {boss.name} DEFEATED!")
                    print(self.boss_system.render_victory(boss))
                    self._grant_boss_rewards(boss)
                    self.current_boss = None
                    if hasattr(self, '_enrage_announced'):
                        del self._enrage_announced
                    return True
            
            elif choice == "2":  # Defend
                player.is_defending = True
                print("   🛡️  Defensive stance!")
            
            elif choice == "3":  # Skill
                if player.current_mp >= 15:
                    player.current_mp -= 15
                    is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 2.0)
                    damage = int((player.stats.attack.value + 15) * 2 * mult)
                    actual = boss.take_damage(damage)
                    print(f"   ✨ Skill! {boss.name} takes {actual} damage!")
                    if not boss.is_alive:
                        print(f"\n   💀 {boss.name} DEFEATED!")
                        print(self.boss_system.render_victory(boss))
                        self._grant_boss_rewards(boss)
                        self.current_boss = None
                        return True
                else:
                    print(f"   ⚠️  Need 15 MP, have {player.current_mp}")
                    continue
            
            elif choice == "4":  # Escape (not allowed in boss fight)
                print("   ⚠️  Cannot escape from Boss battle!")
                continue
            
            else:
                damage = player.stats.attack.value + 10
                actual = boss.take_damage(damage)
                print(f"   ⚔️  Attack for {actual} damage!")
                if not boss.is_alive:
                    print(f"\n   💀 {boss.name} DEFEATED!")
                    print(self.boss_system.render_victory(boss))
                    self._grant_boss_rewards(boss)
                    self.current_boss = None
                    return True
            
            # Boss turn
            if boss.is_alive:
                # Get boss action
                player_hp_percent = player.current_hp / player.stats.hp.value
                action = boss.get_next_action(self.rng, player_hp_percent)
                
                if action == "attack":
                    base_damage = self.boss_system.calculate_boss_damage(boss, "attack")
                else:
                    base_damage = self.boss_system.calculate_boss_damage(boss, action)
                
                # Apply defense
                damage = max(1, base_damage - player.stats.defense.value)
                
                if getattr(player, 'is_defending', False):
                    damage = damage // 2
                    player.is_defending = False
                    print(f"   🛡️  Defended: {damage} damage!")
                else:
                    print(f"   💥 {boss.name} attacks for {damage} damage!")
                
                # Check for ability description
                for ability in boss.abilities:
                    if ability.ability_id == action and ability.description:
                        print(f"   📝 {ability.name}: {ability.description}")
                
                actual = player.take_damage(damage)
                
                if not player.is_alive:
                    print(f"\n   💀 你被 {boss.name} 击败了!")
                    self.current_boss = None
                    return False
        
        self.current_boss = None
        return False
    
    def _print_combat_status_for_boss(self) -> None:
        """Print player status during boss combat."""
        player = self.state.player.character  # type: ignore[union-attr]
        p_bar = self._render_hp_bar(player.current_hp, player.stats.hp.value)
        
        print(f"""
{'─'*50}
👤 {player.name} (Lv.{player.level})
{p_bar}
MP: {player.current_mp}/{player.stats.mp.value}
{'─'*50}""")
    
    def _grant_boss_rewards(self, boss: BossState) -> None:
        """Grant rewards for defeating a boss."""
        rewards = self.boss_system.get_boss_rewards(boss)
        
        self.state.player.gold += rewards['gold']  # type: ignore[union-attr]
        self.inventory.gold += rewards['gold']  # Sync to inventory for shop
        
        did_level_up, new_level = self.state.player.character.gain_experience(rewards['exp'])  # type: ignore[union-attr]
        
        print(f"\n   💰 +{rewards['gold']} Gold")
        print(f"   ⭐ +{rewards['exp']} EXP")
        
        if did_level_up:
            stats = self.progression_rules.calculate_level_up_stats(new_level)
            print(f"   🆙 LEVEL UP! Level {new_level}")
            print(f"      HP +{stats['hp_gain']}, MP +{stats['mp_gain']}, ATK +{stats['atk_gain']}")
        
        if rewards['items']:
            items_str = ", ".join(rewards['items'])
            print(f"   🎁 获得物品: {items_str}")
    
    def _complete_chapter(self) -> bool:
        """Handle chapter completion and shop."""
        chapter = self.chapter_system.complete_current_chapter()
        
        # Calculate rewards
        gold_reward = int(50 * chapter.config.gold_bonus * (1 + chapter.chapter_index * 0.2))
        exp_reward = int(100 * chapter.config.exp_bonus * (1 + chapter.chapter_index * 0.2))
        
        self.state.player.gold += gold_reward  # type: ignore[union-attr]
        self.inventory.gold += gold_reward  # Sync to inventory for shop
        
        did_level_up, new_level = self.state.player.character.gain_experience(exp_reward)  # type: ignore[union-attr]
        
        print(f"""
{'='*50}
🎉 CHAPTER COMPLETE: {chapter.name}
{'='*50}
   Enemies: {chapter.enemies_defeated}/{chapter.enemy_count}
   💰 +{gold_reward} Gold
   ⭐ +{exp_reward} EXP
""")
        
        if did_level_up:
            stats = self.progression_rules.calculate_level_up_stats(new_level)
            print(f"   🆙 LEVEL UP! Level {new_level}")
            print(f"      HP +{stats['hp_gain']}, MP +{stats['mp_gain']}, ATK +{stats['atk_gain']}")
        
        # Open shop if enabled
        if chapter.config.shop_enabled:
            print()
            self._open_shop(chapter)
        
        # Advance to next chapter
        if self.chapter_system.advance_chapter():
            next_chapter = self.chapter_system.get_current_chapter()
            if next_chapter:
                print()
                self._print_chapter_intro(next_chapter)
        else:
            # No more chapters - Victory!
            self._print_victory()
            return False
        
        return True
    
    def _open_shop(self, chapter: Any) -> None:
        """Open shop for chapter."""
        if self.auto_mode:
            # Auto mode: skip shop
            return
        
        if not self.state:
            return
        
        print(f"\n{self._t('Welcome to the shop')}")
        print(f"💰 Gold: {self.state.player.gold}")
        
        self.current_shop = self.shop_system.generate_shop_inventory(
            chapter_index=chapter.chapter_index,
            base_gold=self.state.player.gold
        )
        
        while True:
            print(self.shop_system.render_shop_menu(self.current_shop, self.inventory))
            choice = input("> ").strip()
            
            if choice == "0":
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.current_shop.items):
                    item = self.current_shop.items[idx]
                    success, events = self.shop_system.purchase_item(
                        self.current_shop, self.inventory, item.item_id
                    )
                    if success:
                        print(f"   ✅ Purchased {item.name}!")
                    else:
                        for e in events:
                            if e.type == EventType.ERROR:
                                print(f"   ❌ {e.data.get('message', 'Error')}")
                else:
                    print("   ❌ Invalid choice")
            except ValueError:
                print("   ❌ Invalid input")
    
    def _grant_rewards(self, enemy: EnemyState, chapter: Any) -> None:
        """Grant combat rewards with chapter bonuses."""
        # Apply chapter bonuses
        exp = int(enemy.exp_reward * chapter.config.exp_bonus)
        gold = int(enemy.gold_reward * chapter.config.gold_bonus)
        
        self.state.player.gold += gold  # type: ignore[union-attr]
        self.inventory.gold += gold  # Sync to inventory for shop
        
        did_level_up, new_level = self.state.player.character.gain_experience(exp)  # type: ignore[union-attr]
        
        print(f"   ⭐ +{exp} EXP  |  💰 +{gold} Gold")
        
        if did_level_up:
            self.progression_rules.calculate_level_up_stats(new_level)
            print(f"   🆙 LEVEL UP! Level {new_level}")
    
    def _create_enemy(self, commit: CommitInfo) -> EnemyState:
        """Create enemy from commit with chapter scaling."""
        msg = commit.message.lower()
        chapter = self.chapter_system.get_current_chapter()
        
        # Determine type
        if "merge" in msg:
            enemy_type = "merge"
        elif msg.startswith("fix") or "bug" in msg:
            enemy_type = "bug"
        elif msg.startswith("feat"):
            enemy_type = "feature"
        elif msg.startswith("docs"):
            enemy_type = "docs"
        else:
            enemy_type = "general"
        
        # Calculate stats with chapter scaling
        diff = self.progression_rules.calculate_enemy_difficulty(
            commit.total_changes or 10,
            enemy_type,
            chapter.chapter_index if chapter else 0
        )
        
        # Apply chapter multipliers
        hp = int(diff["hp"] * chapter.config.enemy_hp_multiplier) if chapter else diff["hp"]
        atk = int(diff["attack"] * chapter.config.enemy_atk_multiplier) if chapter else diff["attack"]
        
        name = self._generate_name(commit)
        
        return EnemyState(
            entity_id=f"enemy_{self.state.current_commit_index}",  # type: ignore[union-attr]
            name=name,
            enemy_type=enemy_type,
            commit_hash=commit.hexsha[:7],
            commit_message=commit.message[:30],
            current_hp=hp,
            max_hp=hp,
            attack=atk,
            defense=diff["defense"],
            exp_reward=diff["exp_reward"],
            gold_reward=diff["gold_reward"],
            is_boss="merge" in msg
        )
    
    def _generate_name(self, commit: CommitInfo) -> str:
        """Generate enemy name from commit."""
        msg = commit.message
        if msg.startswith("feat:"):
            return f"Feature: {msg[5:].strip()[:20]}"
        elif msg.startswith("fix:"):
            return f"Bug: {msg[4:].strip()[:20]}"
        elif msg.startswith("docs:"):
            return f"Docs: {msg[5:].strip()[:15]}"
        elif msg.startswith("merge"):
            return "Merge Conflict"
        else:
            return msg[:25] if msg else "Unknown"
    
    def _get_current_commit(self) -> Any:
        """Get current commit from parser."""
        if not hasattr(self, '_parser'):
            if not self.state:
                return None
            config = GameConfig()
            self._parser = GitParser(config)
            self._parser.load_repository(self.state.repo_path)
        
        if not self.state:
            return None
        commits = self._parser.get_commit_history()
        idx = self.state.current_commit_index
        
        if 0 <= idx < len(commits):
            return commits[idx]
        return None
    
    def _print_banner(self) -> None:
        """Print banner."""
        if not self.state:
            return
        print(f"""
╔══════════════════════════════════════════════════════════╗
║              G I T   D U N G E O N                     ║
║         Battle through your commits!                   ║
╚══════════════════════════════════════════════════════════╝

📊 Repository: {self.state.repo_path}
📍 Total Commits: {self.state.total_commits}
📖 Chapters: {len(self.chapter_system.chapters)}
🎯 Objective: Defeat all commits!
""")
    
    def _print_chapter_intro(self, chapter: Any) -> None:
        """Print chapter introduction."""
        print(f"""
{'='*50}
📖 第 {chapter.chapter_index + 1} 章：{chapter.name}
{'='*50}
📝 {chapter.description}

⚔️  敌人数量: {chapter.enemy_count}
🏆 Boss: {"是" if chapter.is_boss_chapter else "否"}
🏪 商店: {"有" if chapter.config.shop_enabled else "无"}
{'='*50}
""")
    
    def _print_combat_status(self, enemy: EnemyState) -> None:
        """Print combat status."""
        if not self.state:
            return
        player = self.state.player.character
        p_bar = self._render_hp_bar(player.current_hp, player.stats.hp.value)
        e_bar = self._render_hp_bar(enemy.current_hp, enemy.max_hp)
        
        print(f"""
{'─'*50}
👤 DEVELOPER (Lv.{player.level})          👾 {enemy.name}
{p_bar}          {e_bar}
MP: {player.current_mp}/{player.stats.mp.value}                 
{'─'*50}""")
    
    def _render_hp_bar(self, current: int, maximum: int, width: int = 20) -> str:
        """Render HP bar."""
        if maximum <= 0:
            return " " * (width + 10)
        
        ratio = current / maximum
        filled = int(ratio * width)
        color = "🟢" if ratio > 0.6 else "🟡" if ratio > 0.3 else "🔴"
        bar = "█" * filled + "░" * (width - filled)
        return f"{color} HP:{current:3}/{maximum:3}|{bar}|"
    
    def _get_combat_choice(self) -> str:
        """Get combat choice."""
        if self.auto_mode:
            return "1"  # Auto-attack
        
        print("""
🎯 YOUR TURN!
   [1] ⚔️  Attack    [2] 🛡️  Defend
   [3] ✨  Skill     [4] 🏃  Escape/Shop
""")
        print("> ", end="", flush=True)
        try:
            return input().strip().lower()
        except EOFError:
            return "1"
    
    def _print_victory(self) -> None:
        """Print victory."""
        if not self.state:
            return
        player = self.state.player.character
        print(f"""
{'='*60}
🏆 VICTORY! All commits defeated!
{'='*60}

📊 FINAL STATISTICS
   Level: {player.level}
   EXP: {player.experience}
   Enemies: {len(self.state.enemies_defeated)}
   Gold: {self.state.player.gold}
   Items: {len(self.inventory.items)}
{'='*60}
🎉 Congratulations!
""")
    
    def _print_defeat(self) -> None:
        """Print defeat."""
        if not self.state:
            return
        print(f"""
{'='*60}
💀 GAME OVER
{'='*60}
   Level: {self.state.player.character.level}
   Enemies: {len(self.state.enemies_defeated)}
   HP: {self.state.player.character.current_hp}
{'='*60}
💡 Tip: Use Defend to reduce damage!
""")
    
    def _is_github_url(self, input_str: str) -> bool:
        """Check if input is GitHub URL."""
        return "/" in input_str and not os.path.exists(input_str)
    
    def _clone_github_repo(self, repo_input: str) -> Optional[str]:
        """Clone GitHub repository."""
        if repo_input.startswith("https://github.com/"):
            match = re.search(r'github\.com/([^/]+/[^/]+)', repo_input)
            if match:
                repo_path = match.group(1)
            else:
                return None
        else:
            repo_path = repo_input
        
        repo_path = repo_path.rstrip('/').rstrip('.git')
        temp_dir = tempfile.mkdtemp(prefix='git-dungeon-')
        clone_path = os.path.join(temp_dir, repo_path.split('/')[-1])
        
        url = f"https://github.com/{repo_path}.git"
        print(f"🔽 Cloning {url}...")
        
        try:
            result = subprocess.run(
                ['git', 'clone', url, clone_path],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print("✅ Cloned!")
                return clone_path
            print(f"❌ {result.stderr}")
        except Exception as e:
            print(f"❌ {e}")
        return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Git Dungeon - Battle through your commits!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repository", nargs="?", default=None, help="Repository path or user/repo")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    parser.add_argument("--lang", "-l", type=str, default="en", 
                        choices=["en", "zh", "zh_CN"],
                        help="Language (en/zh_CN)")
    
    args = parser.parse_args()
    
    if not args.repository:
        print("""
🎮 Git Dungeon - CLI

Usage:
    python src/main_cli_new.py <repo> [options]

Examples:
    python src/main_cli_new.py username/repo --lang zh_CN
    python src/main_cli_new.py . --seed 12345 --lang zh_CN
""")
        return
    
    game = GitDungeonCLI(seed=args.seed, verbose=args.verbose, lang=args.lang)
    
    try:
        game.start(args.repository)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
