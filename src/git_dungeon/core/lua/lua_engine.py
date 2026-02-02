"""Lua content system for Git Dungeon."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from git_dungeon.utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import lupa, but allow graceful degradation
try:
    import lupa
    from lupa import LuaRuntime
    LUA_AVAILABLE = True
except ImportError:
    LUA_AVAILABLE = False
    LuaRuntime = None
    lupa = None


@dataclass
class MonsterTemplate:
    """Template for generating monster entities."""

    name: str
    base_hp: int = 50
    base_attack: int = 10
    base_defense: int = 5
    base_mp: int = 0
    speed: int = 10
    critical: int = 10
    evasion: int = 5
    luck: int = 5
    experience: int = 20
    skills: list[str] = field(default_factory=list)
    drop_table: Optional[str] = None
    theme: str = "default"
    description: str = ""
    difficulty_factor: float = 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "base_mp": self.base_mp,
            "speed": self.speed,
            "critical": self.critical,
            "evasion": self.evasion,
            "luck": self.luck,
            "experience": self.experience,
            "skills": self.skills,
            "drop_table": self.drop_table,
            "theme": self.theme,
            "description": self.description,
            "difficulty_factor": self.difficulty_factor,
        }


@dataclass
class DropEntry:
    """Single entry in a drop table."""

    item_id: str
    chance: float = 1.0  # 0.0 to 1.0
    min_quantity: int = 1
    max_quantity: int = 1
    conditions: list[str] = field(default_factory=list)  # e.g., ["boss", "rare_only"]


@dataclass
class DropTable:
    """Drop table for monsters."""

    name: str
    entries: list[DropEntry] = field(default_factory=list)
    guaranteed: list[DropEntry] = field(default_factory=list)  # Always drop

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "entries": [
                {
                    "item_id": e.item_id,
                    "chance": e.chance,
                    "min_quantity": e.min_quantity,
                    "max_quantity": e.max_quantity,
                }
                for e in self.entries
            ],
            "guaranteed": [
                {
                    "item_id": e.item_id,
                    "min_quantity": e.min_quantity,
                    "max_quantity": e.max_quantity,
                }
                for e in self.guaranteed
            ],
        }


@dataclass
class Theme:
    """Game theme configuration."""

    id: str
    name: str
    description: str = ""
    color_scheme: str = "default"
    icon: str = "🎮"
    monster_prefixes: list[str] = field(default_factory=list)
    item_prefixes: list[str] = field(default_factory=list)
    commit_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color_scheme": self.color_scheme,
            "icon": self.icon,
            "monster_prefixes": self.monster_prefixes,
            "item_prefixes": self.item_prefixes,
            "commit_messages": self.commit_messages,
        }


class LuaEngine:
    """Lua scripting engine for game content."""

    def __init__(self, content_dir: Optional[str] = None):
        """Initialize the Lua engine.

        Args:
            content_dir: Directory for Lua content scripts
        """
        self.content_dir = Path(content_dir) if content_dir else None
        
        # Content storage
        self.monsters: dict[str, MonsterTemplate] = {}
        self.drop_tables: dict[str, DropTable] = {}
        self.themes: dict[str, Theme] = {}
        
        # Lua runtime (only if lupa is available)
        self.lua: Optional[Any] = None
        if LUA_AVAILABLE and LuaRuntime:
            try:
                self.lua = LuaRuntime(unpack_returned_tuples=True)
                self._setup_apis()
            except Exception as e:
                logger.warning(f"Failed to initialize Lua runtime: {e}")
                self.lua = None
        else:
            logger.warning("Lua runtime not available - using JSON mode only")
        
        # Built-in content
        self._setup_builtins()
        
        logger.info(f"LuaEngine initialized (Lua available: {LUA_AVAILABLE})")

    def _setup_builtins(self) -> None:
        """Set up built-in content."""
        # Default theme
        self.themes["default"] = Theme(
            id="default",
            name="Default",
            description="Classic Git Dungeon",
            color_scheme="default",
            icon="🎮",
            monster_prefixes=["Bug", "Feature", "Crash", "Glitch"],
            item_prefixes=["Item", "Tool"],
            commit_messages=[
                "feat: Add new feature",
                "fix: Fix bug",
                "docs: Update documentation",
                "chore: Maintenance",
            ],
        )

    def _setup_apis(self) -> None:
        """Set up Lua APIs."""
        if self.lua is None:
            return
            
        # Monster API
        self.lua.globals()["Monster"] = self._create_monster_api()
        
        # DropTable API
        self.lua.globals()["DropTable"] = self._create_droptable_api()
        
        # Theme API
        self.lua.globals()["Theme"] = self._create_theme_api()
        
        # Utility functions
        self.lua.globals()["log"] = self._log_function
        self.lua.globals()["print"] = self._log_function

    def _log_function(self, *args) -> None:
        """Log function for Lua scripts."""
        message = " ".join(str(arg) for arg in args)
        logger.debug(f"[Lua] {message}")

    def _create_monster_api(self) -> dict:
        """Create Monster API for Lua scripts."""
        api = {}

        def define(data: dict) -> str:
            """Define a new monster template."""
            name = data.get("name", "Unknown")
            
            monster = MonsterTemplate(
                name=name,
                base_hp=data.get("hp", 50),
                base_attack=data.get("attack", 10),
                base_defense=data.get("defense", 5),
                base_mp=data.get("mp", 0),
                speed=data.get("speed", 10),
                critical=data.get("critical", 10),
                evasion=data.get("evasion", 5),
                luck=data.get("luck", 5),
                experience=data.get("experience", 20),
                skills=data.get("skills", []),
                drop_table=data.get("drop_table"),
                theme=data.get("theme", "default"),
                description=data.get("description", ""),
                difficulty_factor=data.get("difficulty_factor", 1.0),
            )
            
            self.monsters[name] = monster
            logger.info(f"[Lua] Defined monster: {name}")
            return name

        def get(name: str) -> Optional[dict]:
            """Get a monster template."""
            monster = self.monsters.get(name)
            return monster.to_dict() if monster else None

        def all_monsters() -> list:
            """Get all monster names."""
            return list(self.monsters.keys())

        def random() -> Optional[dict]:
            """Get a random monster."""
            if not self.monsters:
                return None
            import random as random_module
            name = random_module.choice(list(self.monsters.keys()))
            return self.monsters[name].to_dict()

        api["define"] = define
        api["get"] = get
        api["all"] = all_monsters
        api["random"] = random

        return api

    def _create_droptable_api(self) -> dict:
        """Create DropTable API for Lua scripts."""
        api = {}

        def define(name: str, entries: list) -> str:
            """Define a new drop table."""
            drop_table = DropTable(name=name)
            
            for entry in entries:
                drop_table.entries.append(DropEntry(
                    item_id=entry.get("item", ""),
                    chance=entry.get("chance", 1.0),
                    min_quantity=entry.get("min_quantity", 1),
                    max_quantity=entry.get("max_quantity", 1),
                ))
            
            self.drop_tables[name] = drop_table
            logger.info(f"[Lua] Defined drop table: {name}")
            return name

        def add_guaranteed(name: str, item: str, quantity: int = 1) -> bool:
            """Add a guaranteed drop to a table."""
            table = self.drop_tables.get(name)
            if not table:
                return False
            
            table.guaranteed.append(DropEntry(
                item_id=item,
                min_quantity=quantity,
                max_quantity=quantity,
            ))
            return True

        def get(name: str) -> Optional[dict]:
            """Get a drop table."""
            table = self.drop_tables.get(name)
            return table.to_dict() if table else None

        def all_tables() -> list:
            """Get all drop table names."""
            return list(self.drop_tables.keys())

        api["define"] = define
        api["add_guaranteed"] = add_guaranteed
        api["get"] = get
        api["all"] = all_tables

        return api

    def _create_theme_api(self) -> dict:
        """Create Theme API for Lua scripts."""
        api = {}

        def define(data: dict) -> str:
            """Define a new theme."""
            theme_id = data.get("id", data.get("name", "unknown").lower().replace(" ", "_"))
            
            theme = Theme(
                id=theme_id,
                name=data.get("name", theme_id),
                description=data.get("description", ""),
                color_scheme=data.get("color_scheme", "default"),
                icon=data.get("icon", "🎮"),
                monster_prefixes=data.get("monster_prefixes", []),
                item_prefixes=data.get("item_prefixes", []),
                commit_messages=data.get("commit_messages", []),
            )
            
            self.themes[theme_id] = theme
            logger.info(f"[Lua] Defined theme: {theme_id}")
            return theme_id

        def get(theme_id: str) -> Optional[dict]:
            """Get a theme."""
            theme = self.themes.get(theme_id)
            return theme.to_dict() if theme else None

        def all_themes() -> list:
            """Get all theme IDs."""
            return list(self.themes.keys())

        def current() -> dict:
            """Get default theme."""
            theme = self.themes.get("default")
            return theme.to_dict() if theme else {}

        api["define"] = define
        api["get"] = get
        api["all"] = all_themes
        api["current"] = current

        return api

    def execute(self, code: str) -> tuple[bool, Any]:
        """Execute Lua code.

        Args:
            code: Lua code to execute

        Returns:
            Tuple of (success, result)
        """
        if self.lua is None:
            return False, "Lua runtime not available"
        
        try:
            result = self.lua.execute(code)
            return True, result
        except Exception as e:
            logger.error(f"[Lua] Execution error: {e}")
            return False, str(e)

    def load_file(self, file_path: str) -> tuple[bool, str]:
        """Load and execute a Lua script file.
        
        Args:
            file_path: Path to Lua script or JSON content file
            
        Returns:
            Tuple of (success, message)
        """
        path = Path(file_path)
        if not path.exists():
            return False, f"File not found: {file_path}"
        
        # Handle JSON files directly (regardless of Lua availability)
        if path.suffix == ".json":
            return self._load_json_file(path)
        
        # For non-JSON files, require Lua
        if self.lua is None:
            return False, f"Lua not available for: {file_path}"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            success, result = self.execute(code)
            if success:
                return True, f"Loaded: {path.name}"
            else:
                return False, f"Error: {result}"
        except Exception as e:
            return False, f"Failed to load: {e}"

    def _load_json_file(self, path: Path) -> tuple[bool, str]:
        """Load content from a JSON file (fallback when Lua unavailable)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Determine content type from structure
            # Check if it's a monster file
            if isinstance(data, dict):
                first_key = next(iter(data.keys()), "")
                first_value = data.get(first_key, {})
                
                # Detect type based on content structure
                if isinstance(first_value, dict):
                    # Check for monster (has hp, base_hp, or attack)
                    if "hp" in first_value or "base_hp" in first_value or "attack" in first_value:
                        self._parse_json_monsters(data)
                    # Check for drop table (has entries)
                    elif "entries" in first_value or "guaranteed" in first_value:
                        self._parse_json_droptables(data)
                    # Check for theme (has monster_prefixes or color_scheme)
                    elif "monster_prefixes" in first_value or "color_scheme" in first_value:
                        self._parse_json_themes(data)
            
            return True, f"Loaded JSON: {path.name}"
        except Exception as e:
            return False, f"Failed to load JSON: {e}"

    def _parse_json_monsters(self, data: dict) -> None:
        """Parse monsters from JSON data."""
        for name, info in data.items():
            if isinstance(info, dict):
                monster = MonsterTemplate(
                    name=name,
                    base_hp=info.get("hp", info.get("base_hp", 50)),
                    base_attack=info.get("attack", info.get("base_attack", 10)),
                    base_defense=info.get("defense", info.get("base_defense", 5)),
                    base_mp=info.get("mp", info.get("base_mp", 0)),
                    speed=info.get("speed", 10),
                    critical=info.get("critical", 10),
                    evasion=info.get("evasion", 5),
                    luck=info.get("luck", 5),
                    experience=info.get("experience", 20),
                    skills=info.get("skills", []),
                    drop_table=info.get("drop_table"),
                    theme=info.get("theme", "default"),
                    description=info.get("description", ""),
                    difficulty_factor=info.get("difficulty_factor", 1.0),
                )
                self.monsters[name] = monster

    def _parse_json_droptables(self, data: dict) -> None:
        """Parse drop tables from JSON data."""
        for name, info in data.items():
            if isinstance(info, dict):
                table = DropTable(name=name)
                for entry in info.get("entries", []):
                    table.entries.append(DropEntry(
                        item_id=entry.get("item", ""),
                        chance=entry.get("chance", 1.0),
                        min_quantity=entry.get("min_quantity", 1),
                        max_quantity=entry.get("max_quantity", 1),
                    ))
                self.drop_tables[name] = table

    def _parse_json_themes(self, data: dict) -> None:
        """Parse themes from JSON data."""
        for theme_id, info in data.items():
            if isinstance(info, dict):
                theme = Theme(
                    id=theme_id,
                    name=info.get("name", theme_id),
                    description=info.get("description", ""),
                    color_scheme=info.get("color_scheme", "default"),
                    icon=info.get("icon", "🎮"),
                    monster_prefixes=info.get("monster_prefixes", []),
                    item_prefixes=info.get("item_prefixes", []),
                    commit_messages=info.get("commit_messages", []),
                )
                self.themes[theme_id] = theme

    def load_directory(self, directory: str) -> tuple[int, int]:
        """Load all content files from a directory (Lua and JSON).

        Args:
            directory: Directory containing content files

        Returns:
            Tuple of (loaded, failed)
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return 0, 0
        
        loaded = 0
        failed = 0
        
        # Load Lua files
        for lua_file in dir_path.glob("*.lua"):
            success, _ = self.load_file(str(lua_file))
            if success:
                loaded += 1
            else:
                failed += 1
        
        # Load JSON files
        for json_file in dir_path.glob("*.json"):
            success, _ = self.load_file(str(json_file))
            if success:
                loaded += 1
            else:
                failed += 1
        
        logger.info(f"Loaded {loaded} content files, {failed} failed")
        return loaded, failed

    def get_monster(self, name: str) -> Optional[MonsterTemplate]:
        """Get a monster template by name."""
        return self.monsters.get(name)

    def get_drop_table(self, name: str) -> Optional[DropTable]:
        """Get a drop table by name."""
        return self.drop_tables.get(name)

    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """Get a theme by ID."""
        return self.themes.get(theme_id)

    def get_all_content(self) -> dict:
        """Get all loaded content as a dictionary."""
        return {
            "monsters": {k: v.to_dict() for k, v in self.monsters.items()},
            "drop_tables": {k: v.to_dict() for k, v in self.drop_tables.items()},
            "themes": {k: v.to_dict() for k, v in self.themes.items()},
        }

    def export_content(self, output_dir: str) -> bool:
        """Export all content to JSON files.

        Args:
            output_dir: Output directory

        Returns:
            True if successful
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        content = self.get_all_content()
        
        for category, data in content.items():
            file_path = output_path / f"{category}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported content to {output_dir}")
        return True


def parse_lua_table(lua_table: Any) -> dict:
    """Convert a Lua table to a Python dictionary."""
    if lupa is None:
        return {}
    result = {}
    for key, value in lua_table.items():
        if isinstance(value, lupa.LuaTable):
            value = parse_lua_table(value)
        result[key] = value
    return result


def lua_table_to_list(lua_table: Any) -> list:
    """Convert a Lua table to a Python list."""
    if lupa is None:
        return []
    result = []
    for value in lua_table.values():
        if isinstance(value, lupa.LuaTable):
            value = parse_lua_table(value)
        result.append(value)
    return result
