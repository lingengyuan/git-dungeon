#!/usr/bin/env python3
"""
Git Dungeon - Smart Auto-play to Boss
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from git_dungeon.main_cli import GitDungeonCLI
from git_dungeon.config import GameConfig
from git_dungeon.core.git_parser import GitParser
from git_dungeon.engine import GameState


class SmartPlayer:
    """Auto-player with smart decisions."""
    
    def __init__(self, seed=12345):
        self.seed = seed
        self.game = None
        self.commits = []
    
    def play(self):
        """Play through to the boss."""
        print("🎮 Starting smart auto-play to Boss!")
        print(f"   Seed: {self.seed}")
        print()
        
        repo_path = "/root/projects/git-dungeon"
        print(f"📦 Loading repository...")
        
        config = GameConfig()
        parser = GitParser(config)
        parser.load_repository(repo_path)
        self.commits = parser.get_commit_history()
        print(f"✅ Loaded {len(self.commits)} commits!")
        
        # Initialize game state
        self.game = GitDungeonCLI(seed=self.seed, verbose=False, auto_mode=False)
        self.game.chapter_system.parse_chapters(self.commits)
        self.game.state = GameState(
            seed=self.seed,
            repo_path=repo_path,
            total_commits=len(self.commits),
            current_commit_index=0,
            difficulty="normal"
        )
        self.game.state.player.character.current_hp = 100
        self.game.state.player.character.current_mp = 50
        
        print(f"\n📖 Chapters: {len(self.game.chapter_system.chapters)}")
        print(f"🎯 Starting...\n")
        
        # Play through chapters
        self._play_all_chapters()
    
    def _get_commit(self, idx):
        """Get commit by index."""
        if 0 <= idx < len(self.commits):
            return self.commits[idx]
        return None
    
    def _create_enemy(self, commit):
        """Create enemy from commit."""
        enemy = self.game._create_enemy(commit)
        return enemy
    
    def _play_all_chapters(self):
        """Play through all chapters to the boss."""
        chapters = self.game.chapter_system.chapters
        
        for chapter_idx, chapter in enumerate(chapters):
            if chapter.is_boss_chapter:
                print(f"\n{'='*60}")
                print(f"👹 BOSS CHAPTER: {chapter.name}")
                print(f"{'='*60}\n")
                self._play_boss(chapter)
                return
            
            self._play_chapter(chapter)
        
        print("\n🎉 All chapters completed!")
    
    def _play_chapter(self, chapter):
        """Play through a chapter."""
        print(f"\n{'='*60}")
        print(f"📖 Chapter {chapter.chapter_index + 1}: {chapter.name}")
        print(f"   Enemies: {chapter.enemy_count}")
        print(f"{'='*60}")
        
        player = self.game.state.player.character
        
        for i in range(chapter.enemy_count):
            # Get commit and create enemy
            commit = self._get_commit(i)
            if not commit:
                break
            enemy = self._create_enemy(commit)
            
            # Combat loop
            while enemy.current_hp > 0 and player.current_hp > 0:
                # Smart decision: defend if low HP
                if player.current_hp < 30:
                    action = "2"  # Defend
                else:
                    action = "1"  # Attack
                
                # Execute action
                if action == "1":
                    damage = player.stats.attack.value + 5
                    is_crit, mult = self.game.combat_rules.roll_critical(
                        player.stats.critical.value, 1.5
                    )
                    damage = int(damage * mult)
                    enemy.take_damage(damage)
                    crit_str = " ⚡CRIT!" if is_crit else ""
                    print(f"   ⚔️ Attack → {enemy.name}: {damage}{crit_str}")
                else:
                    player.is_defending = True
                    print(f"   🛡️ Defend stance")
                
                if enemy.current_hp <= 0:
                    print(f"   💀 {enemy.name} defeated!")
                    break
                
                # Enemy attack
                enemy_damage = enemy.attack
                if player.current_hp > 0 and getattr(player, 'is_defending', False):
                    enemy_damage = max(1, enemy_damage // 2)
                    player.is_defending = False
                
                player.take_damage(enemy_damage)
                print(f"   💥 {enemy.name} attacks: {enemy_damage}")
            
            if player.current_hp <= 0:
                print(f"\n💀 DEFEATED! Level {player.level}")
                return
            
            # Progress update
            if (i + 1) % 10 == 0:
                print(f"   📊 {i+1}/{chapter.enemy_count} | HP: {player.current_hp}/{player.stats.hp.value}")
        
        # Chapter complete
        print(f"\n✅ Chapter {chapter.chapter_index + 1} Complete!")
        print(f"   Level: {player.level} | HP: {player.current_hp}/{player.stats.hp.value}")
        print(f"   EXP: {player.experience}/{player.experience_to_next}")
    
    def _play_boss(self, chapter):
        """Play the boss battle."""
        boss = self.game.chapter_system.get_chapter_boss(chapter, self.game.boss_system)
        if not boss:
            print("   No boss found!")
            return
        
        print(f"👹 BOSS: {boss.name}")
        print(f"   HP: {boss.max_hp} | ATK: {boss.attack} | DEF: {boss.defense}")
        print()
        
        player = self.game.state.player.character
        turn = 0
        
        print("⚔️  BOSS BATTLE START!")
        print("-" * 40)
        
        while boss.current_hp > 0 and player.current_hp > 0:
            turn += 1
            
            # Smart boss fighting
            if player.current_hp < 30:
                action = "2"  # Defend
            elif player.current_mp >= 15:
                action = "3"  # Skill
            else:
                action = "1"  # Attack
            
            # Execute action
            if action == "1":
                is_crit, mult = self.game.combat_rules.roll_critical(
                    player.stats.critical.value, 1.5
                )
                damage = int((player.stats.attack.value + 10) * mult)
                boss.take_damage(damage)
                crit_str = " ⚡CRIT!" if is_crit else ""
                print(f"Turn {turn}: ⚔️ Attack → {boss.name}: {damage}{crit_str}")
            elif action == "3":
                player.current_mp -= 15
                is_crit, mult = self.game.combat_rules.roll_critical(
                    player.stats.critical.value, 2.0
                )
                damage = int((player.stats.attack.value + 15) * 2 * mult)
                boss.take_damage(damage)
                crit_str = " ⚡CRIT!" if is_crit else ""
                print(f"Turn {turn}: ✨ Skill → {boss.name}: {damage}{crit_str}")
            else:
                player.is_defending = True
                print(f"Turn {turn}: 🛡️ Defend stance")
            
            if boss.current_hp <= 0:
                print(f"\n{'='*60}")
                print(f"💀 👹 BOSS {boss.name} DEFEATED! 👹")
                print(f"{'='*60}")
                print(f"\n🎉 VICTORY!")
                print(f"   You defeated the final boss!")
                return
            
            # Boss turn
            boss_damage = boss.attack
            if player.current_hp > 0 and getattr(player, 'is_defending', False):
                boss_damage = max(1, boss_damage // 2)
                player.is_defending = False
            
            boss.tick_abilities()
            player.take_damage(boss_damage)
            
            print(f"   💥 {boss.name} attacks: {boss_damage}")
            print(f"   📊 You: {player.current_hp}/{player.stats.hp.value} HP | Boss: {boss.current_hp}/{boss.max_hp} HP")
            print()
        
        print(f"\n💀 DEFEATED BY BOSS!")
        print(f"   Level: {player.level}")
        print(f"   Enemies: {len(self.game.state.enemies_defeated)}")


if __name__ == "__main__":
    player = SmartPlayer(seed=12345)
    player.play()
