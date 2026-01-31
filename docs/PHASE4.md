# Phase 4: 性能优化与打包

> 开始日期: 2026-02-01  
> 状态: 🔄 进行中

## 目标
提升游戏性能，优化打包方案，准备发布。

---

## 1. 性能分析

### 1.1 待优化项

| 组件 | 当前耗时 | 目标耗时 | 状态 |
|------|---------|---------|------|
| Git 解析 | ? | <100ms | ⏳ |
| 战斗计算 | ? | <10ms | ⏳ |
| 存档加载 | ? | <50ms | ⏳ |

### 1.2 分析工具

```python
# 使用 cProfile 分析
python -m cProfile -s cumulative src/main.py

# 使用 line_profiler
@profile
def hot_function():
    ...
```

---

## 2. 优化策略

### 2.1 代码级优化

- [ ] **缓存优化**: 使用 `@lru_cache` 装饰频繁计算
- [ ] **惰性加载**: 按需导入模块
- [ ] **减少对象创建**: 复用 Entity/Component 对象

### 2.2 数据结构优化

- [ ] 使用 `__slots__` 减少内存占用
- [ ] 使用 `array.array` 替代列表存储数值
- [ ] 预分配集合大小

### 2.3 I/O 优化

- [ ] 批量读取 Git diff
- [ ] 异步存档写入
- [ ] SQLite 替代 JSON (可选)

---

## 3. 打包方案

### 3.1 PyInstaller 配置

```python
# pyinstaller.spec
a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('assets', 'assets'), ('content', 'content')],
    hiddenimports=['pkg_resources.py2_warn'],
)
```

### 3.2 打包命令

```bash
# 创建虚拟环境
python -m venv .venv
.source .venv/bin/activate
pip install -e .

# PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed src/main.py

# 或使用 Nuitka (更快)
pip install nuitka
python -m nuitka --standalone --onefile src/main.py
```

### 3.3 目标平台

| 平台 | 格式 | 状态 |
|------|------|------|
| Linux | .AppImage | ⏳ |
| macOS | .dmg | ⏳ |
| Windows | .exe | ⏳ |

---

## 4. 基准测试

### 4.1 基准脚本

```python
# benchmarks/run_benchmarks.py
import time
from src.core.game_engine import GameState

def benchmark_loading():
    start = time.perf_counter()
    state = GameState()
    state.load_repository("test_repo")
    return time.perf_counter() - start

def benchmark_combat():
    # ...
    pass
```

### 4.2 CI 集成

```yaml
# .github/workflows/benchmarks.yml
name: Benchmarks
on: [push]
jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python benchmarks/run_benchmarks.py
      - uses: benchmark-action/github-action@v1
```

---

## 5. 任务清单

### Week 1: 性能分析
- [ ] 运行 profiler，识别热点
- [ ] 实现缓存优化
- [ ] 实现惰性加载

### Week 2: 内存优化
- [ ] 添加 `__slots__`
- [ ] 优化数据结构
- [ ] 基准测试验证

### Week 3: 打包
- [ ] 配置 PyInstaller
- [ ] 测试各平台
- [ ] 创建安装脚本

### Week 4: 发布准备
- [ ] 编写 README
- [ ] 创建截图/视频
- [ ] 发布到 GitHub

---

## 文件清单

```
docs/
└── PHASE4.md              # 本文档

benchmarks/
└── run_benchmarks.py      # 基准测试

scripts/
├── build.sh               # Linux 构建
├── build.sh               # macOS 构建
└── build.ps1              # Windows 构建

pyinstaller.spec           # 打包配置
```

---

## 参考

- [Python 性能优化指南](https://docs.python.org/3/library/profile.html)
- [PyInstaller 文档](https://pyinstaller.org/)
- [Nuitka 文档](https://nuitka.net/)
