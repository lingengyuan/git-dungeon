"""Tests for M4 difficulty scaling system."""

from git_dungeon.engine.rules.difficulty import (
    DifficultyLevel,
    get_difficulty,
    apply_enemy_scaling,
    apply_reward_scaling,
    should_spawn_elite,
    should_spawn_boss,
    EnemyScaling,
    RewardScaling,
    EventScaling,
    DifficultyParams,
)


class TestDifficultyPresets:
    """Test difficulty presets are properly initialized."""
    
    def test_normal_difficulty_has_chapters(self):
        """Normal difficulty should have entries for all chapters."""
        for chapter in range(5):
            params = get_difficulty(chapter, DifficultyLevel.NORMAL)
            assert params.chapter_index == chapter
            assert params.difficulty == DifficultyLevel.NORMAL
    
    def test_hard_difficulty_has_chapters(self):
        """Hard difficulty should have entries for all chapters."""
        for chapter in range(5):
            params = get_difficulty(chapter, DifficultyLevel.HARD)
            assert params.chapter_index == chapter
            assert params.difficulty == DifficultyLevel.HARD
    
    def test_chapter_scaling_increases(self):
        """Later chapters should have higher difficulty."""
        normal_ch0 = get_difficulty(0, DifficultyLevel.NORMAL)
        normal_ch4 = get_difficulty(4, DifficultyLevel.NORMAL)
        
        # Enemy HP should scale up
        assert normal_ch4.enemy_scaling.hp_multiplier > normal_ch0.enemy_scaling.hp_multiplier
        
        # Elite and boss chances should increase
        assert normal_ch4.elite_chance > normal_ch0.elite_chance
        assert normal_ch4.boss_chance > normal_ch0.boss_chance
    
    def test_hard_is_harder_than_normal(self):
        """Hard difficulty should be harder than normal at same chapter."""
        for chapter in range(5):
            normal = get_difficulty(chapter, DifficultyLevel.NORMAL)
            hard = get_difficulty(chapter, DifficultyLevel.HARD)
            
            assert hard.enemy_scaling.hp_multiplier > normal.enemy_scaling.hp_multiplier
            assert hard.enemy_scaling.damage_multiplier > normal.enemy_scaling.damage_multiplier
            assert hard.elite_chance > normal.elite_chance
            assert hard.boss_chance > normal.boss_chance


class TestEnemyScaling:
    """Test enemy stat scaling."""
    
    def test_apply_scaling(self):
        """Test enemy HP and damage are scaled correctly."""
        params = DifficultyParams(
            chapter_index=0,
            difficulty=DifficultyLevel.NORMAL,
            enemy_scaling=EnemyScaling(hp_multiplier=1.5, damage_multiplier=1.2),
            reward_scaling=RewardScaling(),
            event_scaling=EventScaling(),
            elite_chance=0.1,
            boss_chance=0.05,
        )
        
        scaled_hp, scaled_damage = apply_enemy_scaling(100, 10, params)
        
        assert scaled_hp == 150  # 100 * 1.5
        assert scaled_damage == 12  # 10 * 1.2
    
    def test_apply_scaling_rounds_down(self):
        """Scaling should result in integers."""
        params = DifficultyParams(
            chapter_index=0,
            difficulty=DifficultyLevel.NORMAL,
            enemy_scaling=EnemyScaling(hp_multiplier=1.33, damage_multiplier=1.17),
            reward_scaling=RewardScaling(),
            event_scaling=EventScaling(),
            elite_chance=0.1,
            boss_chance=0.05,
        )
        
        scaled_hp, scaled_damage = apply_enemy_scaling(100, 10, params)
        
        assert scaled_hp == 133  # int(100 * 1.33)
        assert scaled_damage == 11  # int(10 * 1.17)


class TestRewardScaling:
    """Test reward scaling."""
    
    def test_apply_gold_scaling(self):
        """Test gold rewards are scaled."""
        params = DifficultyParams(
            chapter_index=0,
            difficulty=DifficultyLevel.NORMAL,
            enemy_scaling=EnemyScaling(),
            reward_scaling=RewardScaling(gold_multiplier=1.5),
            event_scaling=EventScaling(),
            elite_chance=0.1,
            boss_chance=0.05,
        )
        
        scaled_gold = apply_reward_scaling(100, params)
        
        assert scaled_gold == 150


class TestSpawnChance:
    """Test elite/boss spawn chance determination."""
    
    def test_elite_spawn_below_threshold(self):
        """Should spawn elite when RNG is below chance."""
        params = DifficultyParams(
            chapter_index=0,
            difficulty=DifficultyLevel.NORMAL,
            enemy_scaling=EnemyScaling(),
            reward_scaling=RewardScaling(),
            event_scaling=EventScaling(),
            elite_chance=0.3,
            boss_chance=0.05,
        )
        
        # Mock RNG that always returns 0.2 (below 0.3)
        class MockRNG:
            def random(self) -> float:
                return 0.2
        
        assert should_spawn_elite(MockRNG(), params) is True
    
    def test_elite_spawn_above_threshold(self):
        """Should not spawn elite when RNG is above chance."""
        params = DifficultyParams(
            chapter_index=0,
            difficulty=DifficultyLevel.NORMAL,
            enemy_scaling=EnemyScaling(),
            reward_scaling=RewardScaling(),
            event_scaling=EventScaling(),
            elite_chance=0.3,
            boss_chance=0.05,
        )
        
        # Mock RNG that always returns 0.5 (above 0.3)
        class MockRNG:
            def random(self) -> float:
                return 0.5
        
        assert should_spawn_elite(MockRNG(), params) is False
    
    def test_boss_spawn(self):
        """Test boss spawn determination."""
        params = DifficultyParams(
            chapter_index=0,
            difficulty=DifficultyLevel.NORMAL,
            enemy_scaling=EnemyScaling(),
            reward_scaling=RewardScaling(),
            event_scaling=EventScaling(),
            elite_chance=0.1,
            boss_chance=0.1,
        )
        
        # Mock RNG that returns 0.05 (below 0.1)
        class MockRNG:
            def random(self) -> float:
                return 0.05
        
        assert should_spawn_boss(MockRNG(), params) is True


class TestNodeCountScaling:
    """Test route node count scales with chapter."""
    
    def test_node_count_increases_with_chapter(self):
        """Later chapters should have more nodes."""
        ch0 = get_difficulty(0, DifficultyLevel.NORMAL)
        ch4 = get_difficulty(4, DifficultyLevel.NORMAL)
        
        assert ch4.node_count > ch0.node_count
    
    def test_elite_max_increases(self):
        """Max elite count should increase with chapter."""
        ch0 = get_difficulty(0, DifficultyLevel.NORMAL)
        ch4 = get_difficulty(4, DifficultyLevel.NORMAL)
        
        assert ch4.elite_max > ch0.elite_max
