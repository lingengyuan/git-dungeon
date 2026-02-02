"""
M3 功能测试集 - 角色系统

覆盖:
1. m3_character_starters_happy - 3 角色起手差异
2. m3_character_invalid_edge - 非法角色 id
3. m3_character_abilities_effect - 角色能力生效

运行命令:
    PYTHONPATH=src python3 -m pytest tests/functional/test_m3_characters.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from git_dungeon.engine import Engine, GameState, Action, DefaultRNG
from git_dungeon.engine.route import build_route, NodeKind
from git_dungeon.content.loader import load_content
from tests.harness.scenario import Scenario, ScenarioStep, ScenarioExpect, ScenarioRunner, RepoFactory


# ==================== Fixtures ====================

@pytest.fixture
def runner():
    return ScenarioRunner()


@pytest.fixture
def content():
    return load_content("src/git_dungeon/content")


# ==================== M3.2 角色系统测试 ====================

class TestCharacterStartersHappy:
    """M3.2 测试: 3 角色起手差异验证"""
    
    def test_developer_starters(self, content):
        """Developer 起始配置"""
        dev = content.characters["developer"]
        
        # 验证 Developer 属性
        assert dev.stats.hp == 100, "Developer should have 100 HP"
        assert dev.stats.energy == 3, "Developer should have 3 energy"
        
        # 验证起始卡
        assert "strike" in dev.starter_cards, "Developer should have strike"
        assert "defend" in dev.starter_cards, "Developer should have defend"
        assert len(dev.starter_cards) >= 5, "Developer should have >= 5 starter cards"
        
        # 验证起始遗物
        assert len(dev.starter_relics) >= 1, "Developer should have starter relic"
        
        print("✅ Developer 起始配置正确")
    
    def test_reviewer_starters(self, content):
        """Reviewer 起始配置"""
        rev = content.characters["reviewer"]
        
        # 验证 Reviewer 属性
        assert rev.stats.hp == 110, "Reviewer should have 110 HP"
        assert rev.stats.energy == 3, "Reviewer should have 3 energy"
        
        # 验证起始卡
        assert "test_guard" in rev.starter_cards, "Reviewer should have test_guard"
        assert len(rev.starter_cards) >= 5, "Reviewer should have >= 5 starter cards"
        
        # 验证起始遗物
        assert "test_framework" in rev.starter_relics, "Reviewer should have test_framework"
        
        print("✅ Reviewer 起始配置正确")
    
    def test_devops_starters(self, content):
        """DevOps 起始配置"""
        ops = content.characters["devops"]
        
        # 验证 DevOps 属性
        assert ops.stats.hp == 90, "DevOps should have 90 HP"
        assert ops.stats.energy == 3, "DevOps should have 3 energy"
        
        # 验证起始卡
        assert "ci_pipeline" in ops.starter_cards, "DevOps should have ci_pipeline"
        assert len(ops.starter_cards) >= 5, "DevOps should have >= 5 starter cards"
        
        # 验证起始遗物
        assert "ci_badge" in ops.starter_relics, "DevOps should have ci_badge"
        
        print("✅ DevOps 起始配置正确")
    
    def test_character_starter_differences(self, content):
        """3 角色起手差异"""
        dev = content.characters["developer"]
        rev = content.characters["reviewer"]
        ops = content.characters["devops"]
        
        # HP 差异
        assert dev.stats.hp == 100
        assert rev.stats.hp == 110
        assert ops.stats.hp == 90
        
        # 能量相同
        assert dev.stats.energy == rev.stats.energy == ops.stats.energy == 3
        
        # 起始遗物不同
        assert dev.starter_relics[0] != rev.starter_relics[0]
        assert rev.starter_relics[0] != ops.starter_relics[0]
        
        print("✅ 3 角色起手差异验证通过")


class TestCharacterAbilities:
    """M3.2 测试: 角色能力"""
    
    def test_developer_no_ability(self, content):
        """Developer 无特殊能力"""
        dev = content.characters["developer"]
        assert len(dev.abilities) == 0, "Developer should have no abilities"
        print("✅ Developer 无特殊能力")
    
    def test_reviewer_purify_ability(self, content):
        """Reviewer 回合开始净化能力"""
        rev = content.characters["reviewer"]
        assert len(rev.abilities) == 1, "Reviewer should have 1 ability"
        
        ability = rev.abilities[0]
        assert ability.trigger == "on_turn_start", "Reviewer ability should trigger on turn start"
        assert "purify" in ability.effect or "clear" in ability.effect.lower(), \
            "Reviewer ability should involve purifying"
        
        print("✅ Reviewer 回合开始净化能力验证通过")
    
    def test_devops_resource_ability(self, content):
        """DevOps 回合结束资源生成"""
        ops = content.characters["devops"]
        assert len(ops.abilities) == 1, "DevOps should have 1 ability"
        
        ability = ops.abilities[0]
        assert ability.trigger == "on_turn_end", "DevOps ability should trigger on turn end"
        
        print("✅ DevOps 回合结束资源生成验证通过")


class TestCharacterInvalidEdge:
    """M3.2 测试: 非法角色处理"""
    
    def test_invalid_character_id(self, content):
        """非法角色 id 应该 fail"""
        invalid_id = "invalid_character_xyz"
        
        # 获取不存在的角色应该返回 None
        char = content.characters.get(invalid_id)
        assert char is None, f"Invalid character '{invalid_id}' should return None"
        
        print("✅ 非法角色 id 返回 None")


class TestCharacterInitialization:
    """M3.2 测试: 角色初始化到游戏状态"""
    
    def test_init_developer_state(self, content):
        """Developer 初始化"""
        char = content.characters["developer"]
        state = GameState(seed=42)
        state.character_id = "developer"
        state.player.character.current_hp = char.stats.hp
        state.player.energy.max_energy = char.stats.energy
        
        assert state.player.character.current_hp == 100
        assert state.player.energy.max_energy == 3
        print("✅ Developer 状态初始化正确")
    
    def test_init_reviewer_state(self, content):
        """Reviewer 初始化"""
        char = content.characters["reviewer"]
        state = GameState(seed=42)
        state.character_id = "reviewer"
        state.player.character.current_hp = char.stats.hp
        state.player.energy.max_energy = char.stats.energy
        
        assert state.player.character.current_hp == 110
        assert state.player.energy.max_energy == 3
        print("✅ Reviewer 状态初始化正确")
    
    def test_init_devops_state(self, content):
        """DevOps 初始化"""
        char = content.characters["devops"]
        state = GameState(seed=42)
        state.character_id = "devops"
        state.player.character.current_hp = char.stats.hp
        state.player.energy.max_energy = char.stats.energy
        
        assert state.player.character.current_hp == 90
        assert state.player.energy.max_energy == 3
        print("✅ DevOps 状态初始化正确")


# ==================== 运行入口 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
