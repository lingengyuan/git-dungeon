# 用游戏的方式打开你的 Git 历史：Git Dungeon 诞生记

> 从枯燥的 commit 记录到热血的战斗之旅

---

你有没有想过，如果你每天写的代码是一条条「怪物」，而你是一名「开发者战士」，每天的工作就是刷怪升级，那会是什么样子？

**Git Dungeon** 就是这样一个项目——它把你的 Git 仓库变成一款 RPG 游戏，每一個 commit 都是一个敌人，每一次 push 都是一场战斗。

这篇文章分享一下我们做了什么，以及背后的技术实现。

---

## 缘起：被 Git log 逼疯的下午

这个项目的诞生，源于一个普通的下午。

我盯着屏幕上密密麻麻的 `git log` 输出，试图理解一个开源项目的演进历史：

```
commit 76f7841
feat: feature 49

commit 6a94d93
feat: feature 48

commit 6e08667
feat: feature 47

... (翻不到底的 feat)
```

**这谁看得懂啊？**

我想知道：

- 这个项目经历了几个阶段？
- 谁是核心贡献者？
- 什么时候做了重大重构？
- 为什么某个时间段 commit 激增？

传统的 `git log` 只是冷冰冰地展示「做了什么」，但无法回答「为什么」和「怎么演变的」。

> ![](./images/001.png)
> 传统的 git log 输出

于是我想到：**如果能把 Git 历史变成游戏呢？**

- 项目发展阶段 → 游戏章节
- 贡献者 → 武林高手
- 版本发布 → BOSS 战
- 代码重构 → 技能升级

用玩游戏的方式「通关」整个项目，岂不是既有趣又能理解项目历史？

---

## Git Dungeon 是什么？

**Git Dungeon** 是一款基于 Git 历史的命令行 RPG 游戏。

### 核心玩法

```
输入 GitHub 仓库 URL
        ↓
游戏自动克隆并分析仓库
        ↓
每个 commit 变成一个敌人
        ↓
战斗、升级、获取金币
        ↓
通关整个项目!
```

### 游戏特色

| 特性 | 说明 |
|------|------|
| 🎮 **自动战斗** | 输入 `--auto` 自动刷怪，适合演示 |
| 🏪 **商店系统** | 战斗获取金币，购买装备和药水 |
| 📊 **章节系统** | 根据 commit 自动划分章节 |
| 🎯 **BOSS 战** | 合并提交(merge)变成强大敌人 |
| 🌐 **任意仓库** | 支持任意 GitHub 仓库 |

> ![](./images/002.png)
> 游戏主界面

---

## 技术架构

### 核心技术栈

| 技术 | 用途 |
|------|------|
| Python 3.11 | 开发语言 |
| GitPython | Git 仓库操作 |
| Rich | 终端美化输出 |
| Typer | CLI 框架 |
| PyInstaller | 打包成可执行文件 |

### 项目结构

```
git-dungeon/
├── src/git_dungeon/
│   ├── core/          # 核心逻辑
│   │   ├── git_parser.py    # Git 数据提取
│   │   └── inventory.py     # 背包系统
│   ├── engine/        # 游戏引擎
│   │   ├── model.py         # 数据模型
│   │   ├── combat.py        # 战斗系统
│   │   └── rules/           # 规则系统
│   └── main_cli.py    # CLI 入口
├── tests/             # 测试用例
├── pyproject.toml     # 项目配置
└── README.md          # 文档
```

---

## 核心实现

### 1. Git 数据提取

使用 GitPython 提取多维度数据：

```python
from git import Repo

def parse_commits(repo_path: str) -> List[CommitInfo]:
    repo = Repo(repo_path)
    commits = []
    
    for commit in repo.iter_commits():
        commits.append(CommitInfo(
            hexsha=commit.hexsha[:7],
            message=commit.message,
            author=commit.author.name,
            committed_date=commit.committed_datetime,
            total_changes=commit.stats.total.get('files', 0)
        ))
    
    return commits
```

### 2. 敌人生成规则

根据 commit 类型生成不同敌人：

```python
ENEMY_TYPES = {
    "feat": {"hp": 1.0, "atk": 1.2, "def": 1.0, "exp": 1.2},    # 新功能
    "fix": {"hp": 0.8, "atk": 1.5, "def": 0.8, "exp": 1.5},    # Bug 修复
    "docs": {"hp": 0.5, "atk": 0.3, "def": 0.5, "exp": 0.5},   # 文档
    "merge": {"hp": 2.0, "atk": 1.5, "def": 1.5, "exp": 2.0},  # 合并 → BOSS
    "refactor": {"hp": 1.2, "atk": 0.8, "def": 1.5, "exp": 1.0}, # 重构
}
```

**为什么这样设计？**

- `merge` 提交通常涉及多方代码合并 → 血厚攻高 → BOSS 级敌人
- `fix` 提交是「修复问题」→ 高攻击 → 需要小心应对
- `docs` 提交是「写文档」→ 弱 → 新手村小怪

### 3. 章节划分算法

```python
def divide_into_chapters(commits: List[CommitInfo]) -> List[Chapter]:
    total = len(commits)
    
    chapters = [
        Chapter(0, "混沌初开", min_commits=1, max_commits=3),
        Chapter(1, "功能涌现", min_commits=20, max_commits=40),
        Chapter(2, "功能涌现", min_commits=20, max_commits=40),
        # ... 更多章节
    ]
    
    return chapters
```

### 4. 战斗系统

```python
def combat_round(player: Player, enemy: Enemy) -> CombatResult:
    # 玩家攻击
    damage = player.attack - enemy.defense
    enemy.take_damage(damage)
    
    if enemy.is_defeated:
        return CombatResult.VICTORY
    
    # 敌人反击
    player.take_damage(enemy.attack)
    
    if player.is_defeated:
        return CombatResult.DEFEAT
    
    return CombatResult.CONTINUE
```

> ![](./images/003.png)
> 战斗界面

---

## 几个有意思的实现细节

### 1. GitHub 浅克隆问题

**问题：** 最初使用 `--depth 1` 克隆，只能获取最新 1 个 commit

**解决：** 移除深度限制，完整克隆

```python
# 错误做法
subprocess.run(['git', 'clone', '--depth', '1', url, path])

# 正确做法
subprocess.run(['git', 'clone', url, path])
```

### 2. 金币不同步 Bug

**问题：** 战斗奖励写入 `state.player.gold`，但商店读取 `inventory.gold`

**解决：** 同步写入两个地方

```python
def _grant_rewards(self, enemy: EnemyState, chapter):
    gold = int(enemy.gold_reward * chapter.config.gold_bonus)
    
    self.state.player.gold += gold
    self.inventory.gold += gold  # 同步到商店
```

### 3. 章节与敌人数量映射

根据 commit 总数动态生成章节：

| Commit 数量 | 章节数 | 每章敌人 |
|------------|--------|---------|
| < 10 | 1 | 全部 |
| 10-50 | 2 | 动态分配 |
| 50-200 | 4-6 | 每章 20-40 |
| 200+ | 8+ | 每章 30+ |

> ![](./images/004.png)
> 章节进度显示

---

## 使用演示

### 快速开始

```bash
# 克隆项目
git clone https://github.com/lingengyuan/git-dungeon.git
cd git-dungeon

# 安装依赖
pip install -r requirements.txt

# 运行游戏 (当前仓库)
./dist/GitDungeon .

# 运行游戏 (任意 GitHub 仓库)
./dist/GitDungeon sindresorhus/awesome
```

### 交互模式

```
⚔️  [1] 攻击    🛡️  [2] 防御
✨  [3] 技能    🏃  [4] 逃跑/商店
```

### 自动战斗模式

```bash
./GitDungeon . --auto
```

适合演示和测试!

> ![](./images/005.png)
> 自动战斗演示

---

## 打通不同仓库的体验

### 小仓库 (10-50 commits)

```
📖 Chapter 1: 混沌初开      ✅ 5/5 敌人
📖 Chapter 2: 功能涌现      ✅ 10/10 敌人

🎉 通关! 体验时长: 2 分钟
```

### 中等仓库 (100-500 commits)

```
📖 Chapter 1: 混沌初开      ✅ 3/3 敌人
📖 Chapter 2: 功能涌现      ✅ 30/30 敌人
📖 Chapter 3: 功能涌现      ✅ 30/30 敌人
📖 Chapter 4: 功能涌现      ✅ 30/30 敌人

🎉 通关! 体验时长: 15 分钟
```

### 大仓库 (1000+ commits)

```
📖 Chapter 1: 混沌初开      ✅ 2/2 敌人
📖 Chapter 8: ...           ✅ ...

🎉 通关! 建议使用 --auto 模式
```

---

## 自定义你的游戏

### 修改敌人名称

在 `src/git_dungeon/names.py` 中自定义:

```python
ENEMY_PREFIXES = {
    "feat": ["功能怪", "特性兽", "新特性"],
    "fix": ["Bug 精", "漏洞魔", "问题怪"],
    "docs": ["文档精灵", "说明仙"],
}
```

### 调整游戏难度

```python
# 敌人属性倍率
ENEMY_HP_MULTIPLIER = 1.0    # 血量
ENEMY_ATK_MULTIPLIER = 1.0   # 攻击
PLAYER_ATK_MULTIPLIER = 1.0  # 玩家攻击
```

---

## 项目已开源

GitHub 仓库：https://github.com/lingengyuan/git-dungeon

### 安装方式

**方式一：pip 安装**
```bash
pip install git-dungeon
git-dungeon .
```

**方式二：下载二进制**
```bash
# 从 Releases 下载
./GitDungeon .
```

**方式三：从源码运行**
```bash
git clone https://github.com/lingengyuan/git-dungeon.git
cd git-dungeon
pip install -e .
python -m git_dungeon .
```

---

## 写在最后

从枯燥的 Git log 到有趣的游戏体验，我们的目标是：

**让理解项目历史变得有趣。**

不只是「知道」项目有多少个 commit，而是能「感受」项目的成长历程：

- 看到项目的诞生阶段
- 追踪功能的逐步完善
- 发现关键的技术转折
- 理解贡献者的角色演变

用玩游戏的方式「通关」整个项目，既能了解历史，又能解压放松!

---

**技术延伸：**

这个项目展示了几个有趣的技术点：

1. **Git 数据结构化** - 将 Git 历史转换为游戏数据
2. **游戏循环设计** - 状态机控制游戏流程
3. **CLI 美化** - 用 Rich 库实现炫酷终端输出
4. **跨平台打包** - PyInstaller 生成各平台可执行文件

**Git Dungeon 只是一个开始。**

如果你也对游戏化开发工具感兴趣，欢迎：

1. 用 Git Dungeon 分析你的项目
2. 自定义游戏规则和敌人类型
3. 贡献代码，添加新功能
4. 分享你打通仓库的截图!

---

**关注作者**

- GitHub: @lingengyuan
- 项目地址: https://github.com/lingengyuan/git-dungeon

**往期文章**

- [让 AI 当考古学家，给你的项目写一部"武侠传"](链接)

---

*本文首发于公众号，扫码关注获取更多技术文章*
