"""Tests for Lua content system."""

import pytest
import tempfile
import os
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.lua import (
    LuaEngine,
    MonsterTemplate,
    DropTable,
    DropEntry,
    Theme,
)


# Check if Lua is available
LUA_AVAILABLE = False
try:
    import importlib.util
    if importlib.util.find_spec("lupa") is not None:
        LUA_AVAILABLE = True
except ImportError:
    LUA_AVAILABLE = False


class TestLuaEngine:
    """Tests for LuaEngine class."""

    def test_engine_creation(self):
        """Test engine initialization."""
        engine = LuaEngine()
        assert engine is not None
        assert "default" in engine.themes

    @pytest.mark.skipif(LUA_AVAILABLE, reason="Lua is available, skip Lua-unavailable test")
    def test_engine_no_lua_fallback(self):
        """Test engine works without Lua runtime."""
        engine = LuaEngine()
        # Even without Lua, basic operations should work
        assert "default" in engine.themes
        
        # execute should fail gracefully
        success, result = engine.execute("return 1 + 1")
        assert success is False
        assert "not available" in result

    @pytest.mark.skipif(LUA_AVAILABLE, reason="Lua is available, skip Python-only test")
    def test_monster_via_python_fallback(self):
        """Test adding monsters via Python API when Lua unavailable."""
        engine = LuaEngine()
        
        # Define a monster via Python API
        monster = MonsterTemplate(
            name="TestMonster",
            base_hp=100,
            base_attack=10,
            base_defense=5,
            base_mp=0,
            speed=10,
            critical=10,
            evasion=5,
            luck=5,
            experience=20,
            skills=[],
            drop_table=None,
            theme="default",
            description="A test monster",
            difficulty_factor=1.0,
        )
        engine.monsters["TestMonster"] = monster
        assert "TestMonster" in engine.monsters
        
        monster = MonsterTemplate(
            name="DirectMonster",
            base_hp=100,
            base_attack=20,
            experience=50,
        )
        engine.monsters["DirectMonster"] = monster
        
        assert "DirectMonster" in engine.monsters
        retrieved = engine.get_monster("DirectMonster")
        assert retrieved is not None
        assert retrieved.base_hp == 100

    def test_droptable_via_python(self):
        """Test creating drop tables via Python API."""
        engine = LuaEngine()
        
        table = DropTable(
            name="test_loot",
            entries=[
                DropEntry(item_id="Health Potion", chance=0.3),
                DropEntry(item_id="Mana Potion", chance=0.2),
            ],
        )
        engine.drop_tables["test_loot"] = table
        
        assert "test_loot" in engine.drop_tables
        retrieved = engine.get_drop_table("test_loot")
        assert retrieved is not None
        assert len(retrieved.entries) == 2

    def test_theme_via_python(self):
        """Test creating themes via Python API."""
        engine = LuaEngine()
        
        theme = Theme(
            id="python",
            name="Python",
            icon="🐍",
            monster_prefixes=["SyntaxError", "TypeError"],
        )
        engine.themes["python"] = theme
        
        assert "python" in engine.themes
        retrieved = engine.get_theme("python")
        assert retrieved is not None
        assert retrieved.icon == "🐍"

    def test_load_json_monsters(self):
        """Test loading monsters from JSON file."""
        engine = LuaEngine()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "JsonMonster1": {"hp": 100, "attack": 20, "experience": 50},
                "JsonMonster2": {"hp": 200, "attack": 30, "experience": 100},
            }, f)
            temp_path = f.name
        
        try:
            success, message = engine.load_file(temp_path)
            assert success is True
            assert "JsonMonster1" in engine.monsters
            assert "JsonMonster2" in engine.monsters
        finally:
            os.unlink(temp_path)

    def test_load_json_droptables(self):
        """Test loading drop tables from JSON file."""
        engine = LuaEngine()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "loot_table": {
                    "entries": [
                        {"item": "Potion", "chance": 0.5},
                        {"item": "Sword", "chance": 0.1},
                    ]
                }
            }, f)
            temp_path = f.name
        
        try:
            success, message = engine.load_file(temp_path)
            assert success is True
            assert "loot_table" in engine.drop_tables
        finally:
            os.unlink(temp_path)

    def test_load_json_themes(self):
        """Test loading themes from JSON file."""
        engine = LuaEngine()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "js_theme": {
                    "name": "JavaScript",
                    "icon": "📜",
                    "monster_prefixes": ["TypeError", "undefined"],
                }
            }, f)
            temp_path = f.name
        
        try:
            success, message = engine.load_file(temp_path)
            assert success is True
            assert "js_theme" in engine.themes
        finally:
            os.unlink(temp_path)

    def test_load_directory_json(self):
        """Test loading all JSON files from a directory."""
        engine = LuaEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create JSON files with proper structure
            with open(os.path.join(tmpdir, "monsters.json"), "w") as f:
                json.dump({"DirMonster": {"hp": 100, "attack": 20, "experience": 50}}, f)
            
            with open(os.path.join(tmpdir, "themes.json"), "w") as f:
                json.dump({"DirTheme": {"name": "Dir Theme", "icon": "🎯", "monster_prefixes": ["Test"]}}, f)
            
            loaded, failed = engine.load_directory(tmpdir)
            assert loaded == 2
            assert failed == 0
            
            assert "DirMonster" in engine.monsters
            assert "DirTheme" in engine.themes

    def test_get_monster(self):
        """Test get_monster method."""
        engine = LuaEngine()
        
        engine.monsters["GetMonster"] = MonsterTemplate(
            name="GetMonster", 
            base_hp=100
        )
        
        monster = engine.get_monster("GetMonster")
        assert monster is not None
        assert monster.base_hp == 100

    def test_get_drop_table(self):
        """Test get_drop_table method."""
        engine = LuaEngine()
        
        engine.drop_tables["get_test"] = DropTable(
            name="get_test",
            entries=[DropEntry(item_id="TestItem", chance=0.5)],
        )
        
        table = engine.get_drop_table("get_test")
        assert table is not None
        assert len(table.entries) == 1

    def test_get_theme(self):
        """Test get_theme method."""
        engine = LuaEngine()
        
        theme = engine.get_theme("default")
        assert theme is not None
        assert theme.id == "default"

    def test_get_all_content(self):
        """Test getting all content."""
        engine = LuaEngine()
        
        # Add some content
        engine.monsters["ContentMonster"] = MonsterTemplate(
            name="ContentMonster", 
            base_hp=100
        )
        engine.drop_tables["content_loot"] = DropTable(
            name="content_loot",
            entries=[DropEntry(item_id="ContentItem", chance=0.5)],
        )
        engine.themes["test_theme"] = Theme(
            id="test_theme",
            name="Test Theme",
        )
        
        content = engine.get_all_content()
        
        assert "monsters" in content
        assert "drop_tables" in content
        assert "themes" in content
        assert "ContentMonster" in content["monsters"]
        assert "content_loot" in content["drop_tables"]
        assert "test_theme" in content["themes"]

    def test_export_content(self):
        """Test exporting content to JSON."""
        engine = LuaEngine()
        
        engine.monsters["ExportMonster"] = MonsterTemplate(
            name="ExportMonster",
            base_hp=100,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success = engine.export_content(tmpdir)
            assert success is True
            
            assert os.path.exists(os.path.join(tmpdir, "monsters.json"))
            assert os.path.exists(os.path.join(tmpdir, "drop_tables.json"))
            assert os.path.exists(os.path.join(tmpdir, "themes.json"))
            
            # Verify content
            with open(os.path.join(tmpdir, "monsters.json")) as f:
                data = json.load(f)
                assert "ExportMonster" in data


class TestMonsterTemplate:
    """Tests for MonsterTemplate class."""

    def test_monster_creation(self):
        """Test creating a monster template."""
        monster = MonsterTemplate(
            name="TestMonster",
            base_hp=100,
            base_attack=20,
            base_defense=10,
            experience=50,
        )
        
        assert monster.name == "TestMonster"
        assert monster.base_hp == 100
        assert monster.experience == 50

    def test_monster_to_dict(self):
        """Test converting monster to dictionary."""
        monster = MonsterTemplate(
            name="DictMonster",
            base_hp=75,
            skills=["attack", "defend"],
        )
        
        data = monster.to_dict()
        
        assert data["name"] == "DictMonster"
        assert data["base_hp"] == 75
        assert "attack" in data["skills"]


class TestDropTable:
    """Tests for DropTable class."""

    def test_droptable_creation(self):
        """Test creating a drop table."""
        table = DropTable(
            name="test_table",
            entries=[
                DropEntry(item_id="item1", chance=0.3),
                DropEntry(item_id="item2", chance=0.2),
            ],
        )
        
        assert table.name == "test_table"
        assert len(table.entries) == 2

    def test_droptable_with_guaranteed(self):
        """Test drop table with guaranteed drops."""
        table = DropTable(
            name="guaranteed_table",
            entries=[DropEntry(item_id="random_item", chance=0.5)],
            guaranteed=[DropEntry(item_id="guaranteed_item", min_quantity=2)],
        )
        
        assert len(table.entries) == 1
        assert len(table.guaranteed) == 1
        assert table.guaranteed[0].item_id == "guaranteed_item"

    def test_droptable_to_dict(self):
        """Test converting drop table to dictionary."""
        table = DropTable(
            name="dict_table",
            entries=[DropEntry(item_id="dict_item", chance=0.5, min_quantity=1, max_quantity=3)],
        )
        
        data = table.to_dict()
        
        assert data["name"] == "dict_table"
        assert len(data["entries"]) == 1
        assert data["entries"][0]["item_id"] == "dict_item"


class TestTheme:
    """Tests for Theme class."""

    def test_theme_creation(self):
        """Test creating a theme."""
        theme = Theme(
            id="python",
            name="Python",
            icon="🐍",
            monster_prefixes=["SyntaxError", "TypeError"],
        )
        
        assert theme.id == "python"
        assert theme.icon == "🐍"
        assert "SyntaxError" in theme.monster_prefixes

    def test_theme_to_dict(self):
        """Test converting theme to dictionary."""
        theme = Theme(
            id="js",
            name="JavaScript",
            color_scheme="yellow",
        )
        
        data = theme.to_dict()
        
        assert data["id"] == "js"
        assert data["color_scheme"] == "yellow"


class TestLuaIntegration:
    """Integration tests for Lua content system."""

    def test_full_monster_definition(self):
        """Test defining a complete monster via Python API."""
        engine = LuaEngine()
        
        # Define monster directly
        monster = MonsterTemplate(
            name="BossMonster",
            base_hp=500,
            base_attack=50,
            base_defense=30,
            base_mp=100,
            speed=15,
            critical=20,
            evasion=10,
            luck=15,
            experience=500,
            skills=["power_strike", "heal", "buff"],
            drop_table="boss_loot",
            theme="boss",
            description="A powerful boss monster",
            difficulty_factor=2.0,
        )
        engine.monsters["BossMonster"] = monster
        
        # Verify
        retrieved = engine.monsters["BossMonster"]
        assert retrieved.base_hp == 500
        assert retrieved.base_attack == 50
        assert len(retrieved.skills) == 3
        assert retrieved.drop_table == "boss_loot"
        assert retrieved.difficulty_factor == 2.0

    def test_full_drop_table(self):
        """Test defining a complete drop table."""
        engine = LuaEngine()
        
        # Define drop table
        table = DropTable(name="epic_loot")
        table.entries = [
            DropEntry(item_id="Legendary Sword", chance=0.05),
            DropEntry(item_id="Rare Shield", chance=0.15),
            DropEntry(item_id="Common Potion", chance=0.5),
        ]
        table.guaranteed = [
            DropEntry(item_id="Gold Coins", min_quantity=10, max_quantity=10)
        ]
        engine.drop_tables["epic_loot"] = table
        
        # Verify
        retrieved = engine.drop_tables["epic_loot"]
        assert len(retrieved.entries) == 3
        assert len(retrieved.guaranteed) == 1
        
        # Check probabilities
        total = sum(e.chance for e in retrieved.entries)
        assert 0.6 < total < 0.8  # 0.05 + 0.15 + 0.5 = 0.7

    def test_multi_theme_setup(self):
        """Test setting up multiple themes."""
        engine = LuaEngine()
        
        # Default already exists
        assert "default" in engine.themes
        
        # Add Python theme
        python_theme = Theme(
            id="python",
            name="Python",
            icon="🐍",
            color_scheme="blue",
            monster_prefixes=["SyntaxError", "ImportError"],
            commit_messages=["feat: Add feature", "fix: Fix bug"],
        )
        engine.themes["python"] = python_theme
        
        # Add JavaScript theme
        js_theme = Theme(
            id="javascript",
            name="JavaScript",
            icon="📜",
            color_scheme="yellow",
            monster_prefixes=["TypeError", "undefined"],
        )
        engine.themes["javascript"] = js_theme
        
        assert len(engine.themes) >= 3
        
        retrieved = engine.themes["python"]
        assert retrieved.icon == "🐍"
        assert "SyntaxError" in retrieved.monster_prefixes

    def test_complex_content_loading(self):
        """Test loading complex content from multiple sources."""
        engine = LuaEngine()
        
        # Inline definitions (Python API)
        engine.monsters["Inline1"] = MonsterTemplate(name="Inline1", base_hp=100)
        engine.monsters["Inline2"] = MonsterTemplate(name="Inline2", base_hp=200)
        
        # File loading (JSON)
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "content.json"), "w") as f:
                json.dump({"FileMonster": {"hp": 300, "attack": 25}}, f)
            
            engine.load_directory(tmpdir)
        
        # Verify all loaded
        assert "Inline1" in engine.monsters
        assert "Inline2" in engine.monsters
        assert "FileMonster" in engine.monsters
        
        content = engine.get_all_content()
        assert len(content["monsters"]) == 3

    def test_content_export_import_cycle(self):
        """Test export and reload cycle."""
        engine = LuaEngine()
        
        # Add content
        engine.monsters["CycleMonster"] = MonsterTemplate(
            name="CycleMonster",
            base_hp=150,
            base_attack=25,
        )
        engine.drop_tables["CycleLoot"] = DropTable(
            name="CycleLoot",
            entries=[DropEntry(item_id="CycleItem", chance=0.5)],
        )
        
        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            engine.export_content(tmpdir)
            
            # Create new engine and reload
            new_engine = LuaEngine()
            new_engine.load_directory(tmpdir)
            
            # Verify monsters loaded
            assert "CycleMonster" in new_engine.monsters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
