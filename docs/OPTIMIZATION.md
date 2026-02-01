#!/usr/bin/env python3
"""
Git Dungeon Performance Optimization Guide
基于业界最佳实践的性能优化策略
"""

# ============================================================
# 1. GitPython 性能优化
# ============================================================

"""
问题: GitPython 的 Repo 对象创建开销大
解决方案:
"""

# A. 缓存 Repository 对象
class GitRepositoryCache:
    """缓存 Git 仓库对象，避免重复创建"""
    
    _cache = {}
    _max_size = 10
    
    @classmethod
    def get_repo(cls, path: str):
        """获取缓存的仓库对象"""
        path = str(path)
        
        if path in cls._cache:
            # 验证仓库是否仍然有效
            try:
                if cls._cache[path].head.is_valid():
                    return cls._cache[path]
            except:
                del cls._cache[path]
        
        # 创建新仓库 (使用 no_mmap 避免内存映射问题)
        from git import Repo
        try:
            repo = Repo(path, search_parent_directories=True)
        except:
            repo = Repo.init(path)
        
        # LRU 缓存
        if len(cls._cache) >= cls._max_size:
            # 移除最旧的
            cls._cache.pop(next(iter(cls._cache)))
        
        cls._cache[path] = repo
        return repo


# B. 使用批量命令减少进程启动开销
def get_commits_batch(repo_path: str, limit: int = 100):
    """使用 git log --batch 批量获取 commits"""
    import subprocess
    import shlex
    
    cmd = f"git log --oneline -n {limit}"
    result = subprocess.run(
        shlex.split(cmd),
        capture_output=True,
        text=True,
        cwd=repo_path,
        creationflags=subprocess.CREATE_NO_WINDOW  # Windows 优化
    )
    
    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            hash_part, msg = line.split(' ', 1)
            commits.append({'hash': hash_part, 'message': msg})
    
    return commits


# ============================================================
# 2. Python 数据结构优化
# ============================================================

"""
问题: dataclass 默认使用 __dict__ 存储，内存开销大
解决方案: 使用 __slots__
"""

from dataclasses import dataclass
from typing import Optional

# A. 使用 __slots__ 的优化版本
@dataclass(slots=True)
class OptimizedCharacterStats:
    """使用 __slots__ 减少内存占用"""
    hp: int = 100
    mp: int = 50
    attack: int = 10
    defense: int = 5
    speed: int = 10
    critical: int = 10
    evasion: int = 5
    luck: int = 5


# B. 使用 namedtuple 或 RecordClass (更快)
from typing import NamedTuple

class CharacterStatsNamed(NamedTuple):
    """使用 NamedTuple (比 dataclass 更快，内存更少)"""
    hp: int = 100
    mp: int = 50
    attack: int = 10
    defense: int = 5
    speed: int = 10
    critical: int = 10
    evasion: int = 5
    luck: int = 5


# ============================================================
# 3. 缓存优化
# ============================================================

from functools import lru_cache
import hashlib

# A. LRU Cache 装饰器
@lru_cache(maxsize=128)
def get_monster_stats(monster_type: str, level: int) -> dict:
    """缓存怪物属性计算"""
    base = {
        'hp': 100 + level * 10,
        'attack': 20 + level * 2,
    }
    return base


# B. 基于路径的缓存
def cached_repo_load(path: str):
    """装饰器: 缓存仓库加载结果"""
    _cache = {}
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = (path, args)
            if key in _cache:
                return _cache[key]
            result = func(*args, **kwargs)
            _cache[key] = result
            return result
        return wrapper
    return decorator


# ============================================================
# 4. 惰性加载 (Lazy Loading)
# ============================================================

"""
问题: 启动时加载所有模块导致启动慢
解决方案: 按需导入
"""

class LazyLoader:
    """惰性加载器"""
    
    _modules = {
        'combat': 'src.core.combat:CombatSystem',
        'character': 'src.core.character:CharacterComponent',
        'lua': 'src.core.lua:LuaEngine',
    }
    
    _instances = {}
    
    @classmethod
    def get(cls, name: str):
        """按需加载模块"""
        if name not in cls._instances:
            from importlib import import_module
            module_path, class_name = cls._modules[name].split(':')
            module = import_module(module_path)
            cls._instances[name] = getattr(module, class_name)
        return cls._instances[name]


# ============================================================
# 5. 对象池 (Object Pool)
# ============================================================

"""
问题: 频繁创建/销毁对象导致 GC 压力
解决方案: 复用对象
"""

class ObjectPool:
    """通用对象池"""
    
    def __init__(self, factory_func, max_size: int = 100):
        self._pool = []
        self._factory = factory_func
        self._max_size = max_size
    
    def get(self):
        """从池中获取对象"""
        if self._pool:
            return self._pool.pop()
        return self._factory()
    
    def release(self, obj):
        """归还对象到池"""
        if len(self._pool) < self._max_size:
            # 重置对象状态
            self._pool.append(obj)


class CombatEntityPool(ObjectPool):
    """战斗实体对象池"""
    
    def __init__(self):
        super().__init__(self._create_entity, max_size=50)
    
    def _create_entity(self):
        from src.core.character import CharacterComponent, CharacterType
        entity = CharacterComponent(CharacterType.MONSTER, "Pooled")
        return entity


# ============================================================
# 6. 字符串interning
# ============================================================

"""
问题: 重复的字符串占用额外内存
解决方案: 使用 intern() 复用字符串
"""

import sys

def intern_strings(obj):
    """递归 intern 所有字符串"""
    if isinstance(obj, str):
        return sys.intern(obj)
    elif isinstance(obj, dict):
        return {k: intern_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [intern_strings(i) for i in obj]
    return obj


# ============================================================
# 7. 使用 __slots__ 的 Entity/Component
# ============================================================

class FastComponent:
    """使用 __slots__ 的快速组件"""
    __slots__ = ('name', 'data')
    
    def __init__(self, name: str, data: dict = None):
        self.name = name
        self.data = data or {}


class FastEntity:
    """使用 __slots__ 的快速实体"""
    __slots__ = ('id', 'name', '_components')
    
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self._components = {}
    
    def add_component(self, component: FastComponent):
        self._components[component.name] = component
    
    def get_component(self, name: str):
        return self._components.get(name)


# ============================================================
# 8. 使用 array.array 替代列表存储数值
# ============================================================

from array import array

class StatArray:
    """使用 array.array 存储属性 (更省内存)"""
    
    def __init__(self, hp=100, mp=50, attack=10, defense=5):
        # typecode 'i' = signed int, 'f' = float
        self._data = array('i', [hp, mp, attack, defense, 10, 10, 5, 5])
    
    @property
    def hp(self):
        return self._data[0]
    
    @hp.setter
    def hp(self, value):
        self._data[0] = value
    
    @property
    def attack(self):
        return self._data[2]
    
    # ...


# ============================================================
# 优化后的 Git Parser 示例
# ============================================================

class OptimizedGitParser:
    """优化后的 Git Parser"""
    
    def __init__(self, config):
        self.config = config
        self._repo = None
        self._commits_cache = {}  # 路径 -> commits
    
    def load_repository(self, path: str):
        """使用缓存的 Repo 对象"""
        # 使用缓存
        self._repo = GitRepositoryCache.get_repo(path)
        
        # 批量加载 commits
        self._commits = self._get_commits_fast(path)
    
    def _get_commits_fast(self, path: str):
        """快速获取 commits (使用缓存)"""
        if path in self._commits_cache:
            return self._commits_cache[path]
        
        # 批量处理
        commits = []
        for line in self._run_git_command(path, 'log --oneline -n 100').split('\n'):
            if line:
                commits.append(self._parse_commit_line(line))
        
        self._commits_cache[path] = commits
        return commits
    
    def _run_git_command(self, path: str) -> str str, cmd::
        """运行 git 命令"""
        import subprocess
        result = subprocess.run(
            ['git'] + cmd.split(),
            capture_output=True,
            text=True,
            cwd=path
        )
        return result.stdout


# ============================================================
# 性能对比测试
# ============================================================

def benchmark_comparison():
    """对比优化前后的性能"""
    import time
    
    # 测试 dataclass vs NamedTuple vs __slots__
    from dataclasses import dataclass
    
    @dataclass
    class DCStats:
        hp: int = 100
        mp: int = 50
    
    class NamedStats(NamedTuple):
        hp: int = 100
        mp: int = 50
    
    @dataclass(slots=True)
    class SlotsStats:
        hp: int = 100
        mp: int = 50
    
    n = 100000
    
    # dataclass
    start = time.perf_counter()
    for _ in range(n):
        s = DCStats(hp=100, mp=50)
    t1 = time.perf_counter() - start
    
    # NamedTuple
    start = time.perf_counter()
    for _ in range(n):
        s = NamedStats(hp=100, mp=50)
    t2 = time.perf_counter() - start
    
    # __slots__
    start = time.perf_counter()
    for _ in range(n):
        s = SlotsStats(hp=100, mp=50)
    t3 = time.perf_counter() - start
    
    print(f"dataclass:    {t1*1000:.1f}ms")
    print(f"NamedTuple:   {t2*1000:.1f}ms")
    print(f"__slots__:    {t3*1000:.1f}ms")
    print(f"Speedup: {(t1/t3):.1f}x")


if __name__ == "__main__":
    benchmark_comparison()
