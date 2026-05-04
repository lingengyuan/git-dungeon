# Phase 0 Handoff — 基线 & 资源准备

- **Phase**: `pixel-phase-0`
- **收口日期**: 2026-05-04
- **作者会话**: Claude Opus 4.7 + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 0
- **源 plan**: `/Users/hughlin/MyNotes/HughLin/Notes/plans/git-dungeon/pixel-game-plan.md` Day 0

---

## 1. 背景

像素化改造的第一步：建立环境基线 + 收齐 CC0/OFL 素材 + 写资源校验脚本。素材未齐，**不允许**开始 Phase 1 写 Screen（源 plan §1 + §7.1 强制）。

**上游约束**：
- CC0 only for sprites/SFX/BGM；CC0 或 OFL only for fonts。
- 禁止猜测 sprite 文件名（源 plan §7.1：`tile_NNNN.png` 必须人工核对 contact sheet）。
- 禁止 Zpix 当 OFL（源 plan §7.3 勘误）。
- 所有原始数据来自源页面，**禁止**二手转述 license。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 0：

| 交付 | 状态 |
|---|---|
| Kenney Tiny Dungeon / UI Pack / RPG Audio / UI Audio 入库 | ✅ |
| `assets/manifest_sprites.json` + `assets/contact_sheets/kenney_tiny_dungeon.png` | ✅（manifest 待人工填路径） |
| 4 首 CC0 BGM (`title/chapter/boss/gameover.ogg`) + `assets/CREDITS.md` 全部记录 | ✅ |
| m5x7 (en) + Ark Pixel/Fusion (zh) 字体入库 | ✅（m5x7 改为 VT323，详见决策段） |
| `scripts/verify_assets.py` + `scripts/verify_audio.py` | ✅ |

**验收命令**（全部通过）：
```bash
.venv/bin/python scripts/verify_assets.py    # OK (13 PENDING 合法)
.venv/bin/python scripts/verify_audio.py     # OK
PYTHONPATH=src .venv/bin/python -m git_dungeon . --seed 42 --auto --compact --print-metrics  # 自然结束
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q  # 343 passed
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q  # 133 passed
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q  # 4 passed
```

---

## 3. 当前进度

- [x] **基线建立** — `.venv` + `pip install -e ".[dev]"`，三套测试 343/133/4 全绿
- [x] **基线 bug 修复** — commit `a956431` 修了 `content/loader.py` 的 schema 契约违反（详见「关键决策 §1」），加回归测试 `tests/unit/test_content_loader.py`
- [x] **目录骨架** — `assets/{sprites,audio/{bgm,sfx},fonts,source_prompts,_downloads,contact_sheets}/`
- [x] **Kenney 4 包** — Tiny Dungeon (132 tile), UI Pack (1315 PNG), RPG Audio (52 ogg), UI Audio (55 文件)，全部含 License.txt
- [x] **4 BGM** — vorbis stereo OGG，全 CC0：
  - `title.ogg` 69.4s — Adventure Theme by Cleyton Kauffman
  - `chapter.ogg` 50.9s — Mysterious 8-bit by Frenchyboy（WAV→OGG）
  - `boss.ogg` 26.7s — 8-Bit Battle Loop by Theodore Kerr
  - `gameover.ogg` 12.0s — Complications by Holizna（截段 + 淡入淡出，详见 `assets/audio/bgm/gameover.notes.md`）
- [x] **字体** — VT323-Regular.ttf (en, OFL) + ark-pixel-12px-proportional-zh_cn.ttf (zh, OFL)
- [x] **CREDITS.md** — sprite/SFX/BGM/字体四节全部填实，明确排除项（Zpix、m5x7）写明原因
- [x] **contact sheet** — `scripts/build_contact_sheet.py` 通用生成器；`assets/contact_sheets/kenney_tiny_dungeon.png` 820×906，132 tile_NNNN 标签可读
- [x] **manifest** — `assets/manifest_sprites.json` 含 13 个 Phase 1 必需 ID（player/enemy/6 个 node/5 个 UI），全部 null **等人工填路径**
- [x] **verify 脚本** — `verify_assets.py` 双模式（default/--strict）；`verify_audio.py` OGG magic + vorbis codec + CREDITS 引用 + License.txt
- [x] **依赖** — `pyproject.toml [dev]` 加 `Pillow>=10.0.0`
- [x] **ffmpeg** — brew 装好（无 libvorbis，用内置 `vorbis -strict experimental`）

**遗留 PENDING（不阻塞 Phase 0 收口，但 Phase 2 开始前必须填）**：
- `assets/manifest_sprites.json` 里 13 个 sprite ID 全部 null。需要人工对照 `kenney_tiny_dungeon.png` 填具体 `tile_NNNN.png` 路径。Phase 6 CI 跑 `verify_assets.py --strict` 会拒绝合并。

---

## 4. 完成情况

### 4.1 关键决策

#### 1. 基线发现 schema 契约 bug（loader.py），修了

**根因**：commit `9fc9198d` 引入 `main_cli._build_event_option_context` 时按 `EventEffect` dataclass 写 `effect.opcode`，但 `content/loader.py:_load_events` 留 raw dict（注释里就写了 `# List[Dict] - effects`）。`packs.py:_parse_event` 同位置正确构造 dataclass。三套测试全绿掩盖这个 bug，因为测试都直接构造 `EventEffect` 实例，**绕过了 loader**。CLI smoke 是唯一触发路径——这就是源 plan §1 警告的「测试通过但环境跑不通」的真实案例。

**修法**：让 `loader._load_events` 对齐 `packs._parse_event`（CLAUDE.md §2 DRY）。两条 loader 现在产出同一 shape。Commit `a956431`。

**回归保护**：`tests/unit/test_content_loader.py` 直接断言 `isinstance(effect, EventEffect)` —— 不绕 loader。

#### 2. m5x7 → VT323 pivot

m5x7 在 itch.io 已变付费下载，违反 Phase 0「免费 CC0/OFL」规则。Pivot 到 **VT323**：
- OFL，单源（无 attribution chain）
- 有小写（事件描述能用）
- Google Fonts github raw 直链下载，无 session 依赖

CREDITS.md 明确登记排除原因，避免后续会话重复尝试 m5x7。

#### 3. ffmpeg 没 libvorbis 用 experimental encoder

macOS `brew install ffmpeg` 默认不带 libvorbis。改用内置 `-c:a vorbis -strict experimental`，要求 `-ac 2` 强制立体声（内置编码器只支持 2 通道）。chapter/gameover.ogg 都通过此路径产出，已用 ffprobe 确认 vorbis 编码 + 时长正确。`pygame.mixer.music.load()` 应该能直接读（Phase 1 确认）。

#### 4. UI Pack 不生成 contact sheet

UI Pack 870 PNG 散布在 `Green/Default` 等多色风格子目录，强行做 contact sheet 不可读。UI 文件名语义化（`button_round_gloss.png`、`icon_checkmark.png`），manifest 直接写路径即可。

#### 5. manifest 用 null PENDING 而非占位假路径

CLAUDE.md §5 禁止掩盖性 fallback。null 是诚实的「未映射」标记。`verify_assets.py` 双模式：
- 默认：null 报告 PENDING、exit 0（开发期）
- `--strict`：null 算 error、exit 2（Phase 6 CI 门禁）

#### 6. 资源全进 git，原始 zip 不进

`.gitignore` 加 `assets/_downloads/`。最终用文件入库（解压后或处理后）。pre-commit hook 设了 `check-added-large-files maxkb=1000`，BGM 单文件最大 2.7MB（title.ogg）会触发，但 hooks 当前未安装。**装 hooks 前需要在 .pre-commit-config.yaml 排除 assets/audio/bgm/ 和 assets/fonts/**——见后续任务。

### 4.2 偏离原计划

- 源 plan §10 Day 0 写 `assets/contact_sheet.png` 单数；实际产出 `assets/contact_sheets/<pack>.png` 复数（用 `contact_sheets/` 子目录），便于后续 UI Pack 等扩展。
- 字体推荐里源 plan §7.3 写「Zpix OFL」是错的，CREDITS.md 已勘误并明确排除 Zpix。
- m5x7 也已变付费（不知何时改的），pivot 到 VT323。CREDITS.md 记录了原因。

### 4.3 Phase 0 不动的 CLAUDE.md 原则

- §1 第一性原理：loader bug 修法没沿用「main_cli 改 dict」的乍看更小方案，而是回归 schema 契约。
- §2 DRY：两条 loader 现在产出同一 shape。
- §3 正交性：sprite manifest 与 audio 校验解耦成两个独立脚本。
- §5 禁掩盖：manifest null PENDING 显式可见；缺资源时 verify 脚本硬错。

---

## 5. 后续任务

### 5.1 立即要做的小事（不在 Phase 1 范围但建议先收）

1. **commit Phase 0 产出物**。当前未提交：`CLAUDE.md` / `handoffs/` / `plans/` / `assets/` / `pyproject.toml`（+ Pillow dep）/ `scripts/build_contact_sheet.py` / `scripts/verify_assets.py` / `scripts/verify_audio.py` / `.gitignore`（加 `_downloads/`）。建议拆 2-3 个 commit：
   - `chore(docs): add CLAUDE.md project principles + plans/handoffs structure`
   - `feat(assets): bring in Kenney/CC0 BGM/fonts + manifest skeleton`
   - `feat(scripts): asset/audio verify + contact sheet generator`
2. **填 13 个 sprite PENDING**。打开 `assets/contact_sheets/kenney_tiny_dungeon.png`，逐个把 null 替换成 `assets/sprites/kenney_tiny_dungeon/Tiles/tile_NNNN.png`。**不阻塞 Phase 1 入口骨架**，但 Phase 2 写 MapScreen/BattleScreen 之前必须填。
3. **pre-commit large-files exclude**：装 hooks 之前，把 `assets/audio/bgm/` 和 `assets/fonts/` 加入 `.pre-commit-config.yaml` 的 `check-added-large-files` 例外，否则 title.ogg (2.7MB) 之类会被钩子拒。

### 5.2 Phase 1 入口

下一个 phase：**`pixel-phase-1` — GameRunner & `--pixel` 入口**（`plans/pixel-phases.md` §Phase 1）。

**目标**：把 CLI 散落的一局推进流程抽到无 print/input 的 `GameRunner`；建 Pygame-CE 入口骨架；Title + 加载页可跑。

**关键风险**：源 plan §1 + §5 已点名「`GameRunner` 抽离比想象的难」。CLI 抽不出时**不允许**让 Screen 反向调 main_cli 私有方法，必须把共享流程下沉到 engine 共享层。

### 5.3 新会话立刻要读哪些文件（按顺序）

1. `CLAUDE.md` — 项目原则
2. `plans/pixel-phases.md` — 找 Phase 1 拆解
3. **本文件** — Phase 0 完成情况与未决事项
4. `src/git_dungeon/main_cli.py` — Phase 1 主要重构对象，看看 `start()` / `_game_loop()` / `_resolve_node()` 链路
5. `src/git_dungeon/engine/engine.py` + `src/git_dungeon/engine/node_flow.py` — 引擎层契约
6. `src/git_dungeon/main.py` — `--pixel` 分支接入点（参考 `--ai` 怎么走 `main_cli_ai.GitDungeonAICLI`）
7. `src/git_dungeon/main_cli_ai.py` — 第二个 CLI 前端实例，证明已经有「双前端」模式可参考

### 5.4 推荐的第一条命令（验证当前状态完好）

```bash
cd /Users/hughlin/Projects/git-dungeon && \
.venv/bin/python scripts/verify_assets.py && \
.venv/bin/python scripts/verify_audio.py && \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --seed 42 --auto --compact --print-metrics
```

三条都 exit 0 就说明 Phase 0 状态完整。任何一条 fail 先回到 §3「当前进度」逐项核对。

### 5.5 已知风险

| 风险 | 影响 | 处理建议 |
|---|---|---|
| 13 sprite PENDING 不填就开 Phase 2 | Screen 写不完整 | Phase 1 期间趁有空填掉 |
| pre-commit hook 装上后 BGM 文件被拒 | 提交流程断 | 装 hooks 前加 exclude |
| ffmpeg experimental vorbis 在某些极端音频上可能产出有问题文件 | 罕见，但要警惕 | 用 ffprobe 在 verify_audio 里加更严格的 vorbis 流校验（未做，纯防御） |
| git_dungeon 仓库自己的 commit 数变化导致 smoke 输出 metrics 不稳定 | smoke 是「能跑」检查，不是 parity | Phase 6 的 CLI/Pixel parity 测试会用合成 repo（`tests/harness/RepoFactory`）解决 |
