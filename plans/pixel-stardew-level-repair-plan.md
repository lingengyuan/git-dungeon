# Pixel Stardew-Level 修复计划

> 日期：2026-05-07
> 输入：`plans/pixel-game-issues.md`、`plans/pixel-ui-event-stardew-gap-review.md`、Phase 13 review findings、OpenAI 官方图像生成文档。
> 目标：把 Pixel mode 从“像素 UI 原型”推进到“核心循环可以按成熟像素 RPG 标准验收”的版本。

## 0. 质量定义

这里的“达到《星露谷物语》的水平”不是复制它的美术、玩法或内容体量，也不承诺一次修复达到同等商业产能。当前项目的可执行标准是：

- **第一眼像游戏地点**：标题、地牢、战斗、商店、休息、事件都先呈现地点、角色和物件，UI 只做辅助。
- **玩家语言统一**：普通界面不出现内部 ID、slot、opcode、`HP/MP/EXP/Gold` 这类混杂字段。
- **交互语义可信**：暂停、退出本局、返回标题、关闭游戏是不同动作，按键规则在运行中所有页面一致。
- **像素素材达标**：所有新素材有 prompt、原图、后处理、contact sheet、asset card、manifest 记录；禁止未经核对直接进游戏。
- **反馈进入画面**：奖励、陷阱、锁门、钥匙、攻击、受击、购买、休息、事件结果都要有可见状态，不只靠一行文字。
- **验收靠截图和试玩**：每个核心屏幕必须有中英文、常见窗口尺寸、玩家流程截图/像素边界检查。

## 1. 当前必须先承认的问题

### 1.1 Phase 13 遗留 review findings

| ID | 优先级 | 问题 | 修复归属 |
|---|---:|---|---|
| RF-001 | P1 | 暂停页“退出本局”实际关闭整个游戏 | Phase 13R 立即修 |
| RF-002 | P1 | 战斗胜利反馈仍混 `EXP`、`Gold` | Phase 13R 立即修 |
| RF-003 | P2 | 事件、休息、商店没有统一支持 `Q` 暂停 | Phase 13R 立即修 |
| RF-004 | P2 | 事件页仍暴露 `event_id`、`choice_id`、`HP`、`Gold` | Phase 13R 止血，Phase 16 重做 |
| RF-005 | P2 | 计划索引状态过时 | 已纳入文档索引检查，后续每 phase 继续校验 |

### 1.2 当前路线最大偏差

旧路线把“真正的 tile 房间表现”放在 Phase 14，把统一美术和音乐放在 Phase 17。这会导致一个问题：先画更多地图，但界面语言、素材标准、事件表达仍然不统一。

新的修复路线改为：

1. 先修会误导玩家的行为和文案。
2. 再建立统一 UI kit、玩家文案 formatter、素材生成流水线。
3. 再把地牢、战斗、事件、商店、休息逐个改成场景。
4. 最后用截图和试玩保护质量。

## 2. 统一界面 UI 方案

### 2.1 唯一 UI 来源

新增或重构一个 Pixel UI kit，作为所有 screen 的共同界面来源：

- 屏幕布局：标题区、状态区、主场景区、动作区、日志/提示区。
- 控件：按钮、禁用按钮、选中按钮、图标按钮、滑杆、开关、面板、对话框、toast、tooltip、确认弹窗。
- 游戏组件：钥匙槽、金币牌、生命/魔力条、房间说明牌、事件选择卡、商品卡、战斗动作条。
- 文字规则：所有玩家可见属性和结果都从统一 formatter 输出，screen 禁止自己拼 `HP/Gold/EXP`。

### 2.2 UI 视觉标准

- 基准画布仍使用 320x180，最终窗口用整数倍放大，nearest-neighbor 渲染。
- 面板边距、按钮高度、文字行高和图标尺寸固定，不随内容撑坏布局。
- HUD 缩小，主场景放大；玩家注意力优先落在角色、房间、物件和敌人上。
- 每个可点击物件必须有 hover/选中/禁用状态。
- 禁止把路径、音频 slot、内部配置、数据字段放在普通玩家界面。

### 2.3 输入和暂停规则

运行中所有页面必须一致：

- `Esc/Q`：打开暂停菜单。
- 暂停菜单：继续、设置、返回标题、关闭游戏。
- “退出本局”必须回标题或结束本局，不得关闭整个程序。
- 鼠标点击看起来可点击的物件时，要么执行动作，要么给出明确原因。

## 3. gpt-image-2 素材生成方案

### 3.1 当前生成路径

本项目当前优先使用 **Codex 内置的 GPT Image 2 能力**生成像素素材，不把 OpenAI API、`OPENAI_API_KEY` 或组织验证作为本轮修复前置条件。

执行方式：

- 由 Codex 直接生成单张或一组候选图。
- 每次生成前先写入 prompt 文件。
- 生成结果保存到 `assets/generated/raw/<phase>/`。
- 后处理、contact sheet、asset card、manifest 校验仍走项目本地流程。
- 若未来需要批量自动化生成，再另行设计 API 脚本；该脚本不是当前 Phase 14B 的验收前提。

API 文档只作为未来自动化路径的参考，不作为当前生成方式。

参考：

- https://developers.openai.com/api/docs/models/gpt-image-2
- https://developers.openai.com/api/docs/guides/image-generation#choosing-the-right-api
- https://developers.openai.com/api/docs/guides/tools-image-generation#supported-models

### 3.2 生成不是接入

AI 图生成出来不等于游戏素材。每个素材必须经过完整流水线：

1. 写 prompt：`assets/source_prompts/<phase>/<asset_id>.md`
2. 生成原图：`assets/generated/raw/<phase>/<asset_id>.png`
3. 后处理：透明背景、裁切、nearest-neighbor 缩放、调色板清理、边缘清理。
4. 输出成标准尺寸：`assets/generated/processed/<phase>/<asset_id>.png`
5. 生成 contact sheet：`assets/generated/contact_sheets/<phase>.png`
6. 写 asset card：模型、日期、prompt、原图、处理方式、用途、license note。
7. 人工核对小尺寸可读性。
8. 通过 `scripts/verify_pixel_assets.py` 后，才写入 `assets/manifest_sprites.json`。

任何一步缺失，都只能保持 `pending_generation`，禁止进入 runtime manifest。

### 3.3 像素素材硬标准

| 类型 | 最终尺寸 | 要求 |
|---|---:|---|
| 地砖/墙/门/陷阱/道具 | 16x16 | 小尺寸能一眼识别，透明或 tile 背景明确 |
| 玩家/普通敌人 | 32x32 | idle/attack/hit 至少可扩展成帧序列 |
| Boss | 48x48 或 64x64 | 和普通敌人明显区分，有主题 silhouette |
| 商品/事件图标 | 16x16 或 24x24 | 读得清，不靠文字解释 |
| 标题 banner | 320x90 | 第一屏建立 Git Dungeon 主题 |
| 场景背景 | 320x120 或 tile 组合 | 不能喧宾夺主，不压文字 |

通用要求：

- 像素边缘清楚，不要平滑插值或照片质感。
- 色板受控，避免整套画面只有琥珀/深蓝一种情绪。
- 不能直接模仿《星露谷物语》的具体角色、建筑、UI 或素材。
- 生成图如果不够像像素素材，必须重新生成或手动后处理，不得硬塞进游戏。

### 3.4 第一批 gpt-image-2 资产清单

Phase 14 必须先生成并接入地牢基础资产：

- `tile_floor_stone`
- `tile_wall_stone`
- `tile_corridor`
- `door_open`
- `door_locked`
- `chest_closed`
- `chest_open`
- `trap_spikes_armed`
- `trap_spikes_spent`
- `key_iron`
- `vault_locked`
- `vault_open`
- `room_marker_current`
- `room_marker_available`
- `boss_gate`

Phase 15 再生成战斗资产：

- `player_idle`
- `player_attack`
- `player_defend`
- `enemy_default_git_goblin`
- `boss_fix`
- `boss_refactor`
- `boss_merge_conflict`
- `boss_ci_sentinel`
- `boss_secret_leak`
- `boss_release_gate`
- `fx_slash`
- `fx_shield`
- `fx_reward_drop`

Phase 16 生成非战斗场景资产：

- `event_shrine`
- `event_terminal_ruin`
- `shopkeeper`
- `shop_counter`
- `rest_campfire`
- `rest_shrine`
- `choice_icon_risk`
- `choice_icon_reward`

Phase 17 生成标题和主题资产：

- `title_background`
- `title_banner`
- `commit_shard`
- `branch_door`
- `merge_conflict_trap`
- `release_gate`

## 4. 音乐和音效标准

当前已有 CC0 BGM/SFX，版权上可以继续用，但听感还不统一。修复标准是：

- 不先盲目找更多曲子，先完整试听现有 title/chapter/boss/gameover。
- 统一响度、起止点、循环点和淡入淡出。
- 每首曲子在 `assets/CREDITS.md` 写清楚用途和处理方式。
- 新增音乐优先 CC0；如果使用 AI 生成音乐，必须同样记录生成工具、prompt、日期、授权说明、原始文件、处理文件。
- 普通 HUD 不显示 `audio: chapter` 这类内部槽位；静音或错误才显示玩家可理解提示。

## 5. Phase 执行计划

### Phase 13R：遗留 review finding 立即修复

> 状态：已完成（2026-05-07，见 `handoffs/2026-05-07-pixel-phase-13r-handoff.md`）。

目标：先消除会误导玩家或破坏中文体验的问题。

交付：

- “退出本局”不再关闭程序，改为返回标题或明确改成“关闭游戏”。
- 战斗胜利奖励不再显示 `EXP/Gold`。
- 事件、休息、商店统一支持 `Esc/Q` 暂停。
- 事件页短期止血：不显示 event/choice 原始 ID，结果反馈用玩家语言。
- `plans/README.md` 和 phase 索引保持最新。

验收：

- 单元测试覆盖上述行为。
- 中文 smoke 不出现 `EXP`、`Gold`、`HP`、`choice_id`、`event_id`。
- 手动试玩确认暂停语义正确。

### Phase 14A：统一 UI kit 和玩家语言层

> 状态：已完成（2026-05-07，见 `handoffs/2026-05-07-pixel-phase-14a-handoff.md`）。

目标：先让所有界面共用同一套 UI 规则。

交付：

- Pixel UI kit：按钮、面板、对话框、toast、tooltip、action bar、choice card、item card。
- 玩家语言 formatter：属性、奖励、损失、钥匙、锁门、陷阱、控制提示统一输出。
- 运行中页面共用 pause/action/log 布局。
- 中英文文本不压边，不靠 screen 自己拼字段。

验收：

- 标题、地牢、战斗、事件、商店、休息、设置在中英文下可读。
- `rg` 检查 screen 中不再直接拼接玩家可见 `HP/MP/EXP/Gold`。
- 视觉 smoke 截图无明显重叠。

### Phase 14B：gpt-image-2 地牢素材流水线

> 状态：已完成（2026-05-08，见 `handoffs/2026-05-08-pixel-phase-14b-handoff.md`）。

目标：先把素材生产变成可复用、可验证、可追溯的流程。

交付：

- `scripts/postprocess_pixel_assets.py`
- `scripts/build_contact_sheet.py`
- `scripts/verify_pixel_assets.py`
- 使用 Codex GPT Image 2 生成 Phase 14 第一批地牢素材。
- Phase 14 第一批地牢素材完成 prompt/raw/processed/contact sheet/asset card。
- 通过人工核对后写入 manifest。

验收：

- Codex 生成失败时必须保持素材 `pending_generation`，不得写入假文件或空白图。
- 所有 processed 素材尺寸、透明背景、manifest 路径、asset card 完整。
- contact sheet 小尺寸可读。

### Phase 14C：地牢 tile 场景重做

> 状态：已完成（2026-05-08，见 `handoffs/2026-05-08-pixel-phase-14c-handoff.md`）。

目标：地牢从路线节点图变成可探索的 tile 场景。

交付：

- 地面、墙、门、走廊替换抽象连线。
- 当前房间、可进入房间、锁门、陷阱、已领取奖励、宝库状态用物件表达。
- 陷阱靠近/选中时显示预计损失。
- 奖励领取后保留打开宝箱或空补给箱。
- 首次进入地牢有短引导。

验收：

- 固定 seed 截图能看出入口、道路、当前房间、可互动对象和危险。
- 鼠标点击房间、锁门、陷阱、奖励都有正确行为或说明。
- CLI/Pixel 自动结果不被 tile 表现改动破坏。

### Phase 15：战斗场景和 Boss 身份

> 状态：已完成（2026-05-08，见 `handoffs/2026-05-08-pixel-phase-15-handoff.md`）。

目标：战斗不再是按钮面板，而是角色和敌人在场景里互动。

交付：

- 战斗画面拆成角色区、敌人区、动作区、日志区。
- 玩家攻击、防御、技能、受击、胜利有短动画或状态变化。
- 6 个 Boss 使用独立 sprite、入场提示、气氛色和战斗音乐。
- 胜利掉落用金币/经验/道具画面反馈，不只是一行文字。

验收：

- 普通战斗和 Boss 战各有截图和输入回放。
- 中文胜利反馈无英文属性混杂。
- Boss 和普通敌人第一眼可区分。

### Phase 16：事件、商店、休息重做

> 状态：已完成（2026-05-08，见 `handoffs/2026-05-08-pixel-phase-16-handoff.md`）。

目标：非战斗页面从数据面板变成游戏地点。

交付：

- 事件页有地点背景、标题、描述、自然语言选项、后果预览。
- 商店有店主、柜台、商品图标、价格牌、买不起原因。
- 休息点有营火/神龛/安全屋场景，回血/恢复有可见效果。
- 事件完成后回地牢的提示不出现 ID 或原始字段。

验收：

- `event_id`、`choice_id`、opcode 不出现在玩家界面。
- 商店商品不是 `cost hp atk mp maxhp` 数据表。
- 休息点一眼像地点，不像设置面板。

### Phase 17：标题、主题、美术、音乐统一

> 状态：已完成（2026-05-08，见 `handoffs/2026-05-08-pixel-phase-17-handoff.md`）。

目标：形成 Git Dungeon 自己的世界识别度。

交付：

- 标题页有正式背景、banner、角色或地牢入口。
- Git 主题物件进入世界：commit shard、branch door、merge conflict trap、CI sentinel、release gate。
- 每章有轻量 palette 和地砖变化。
- BGM 完成试听、响度统一、循环处理和用途记录。
- 基础待机动画：火把、陷阱、奖励、按钮、角色 idle。

验收：

- 标题页第一眼能看出这是 Git Dungeon，不是通用地牢模板。
- 音乐切换不突兀，普通界面不显示音频调试文字。
- 资产 manifest、CREDITS、asset cards 完整。

### Phase 18：视觉回归和最终试玩验收

> 状态：已完成（2026-05-08，见 `handoffs/2026-05-08-pixel-phase-18-handoff.md` 和 `plans/pixel-phase18-final-playtest.md`）。

目标：防止后续改动把画面、文案、暂停语义再次改坏。

交付：

- 中英文标题、地牢、战斗、事件、商店、休息、设置截图检查。
- 常见窗口尺寸检查：960x540、1280x720、全屏整数倍。
- 禁止内部 ID/英文属性混杂的界面文本测试。
- 高对比、文字大小、减少动画的基础选项。
- 完整手动试玩记录和最终问题清单。

验收：

- 新玩家从标题进入一局，能在不看代码/文档的情况下理解移动、奖励、陷阱、钥匙、商店、事件、战斗和暂停。
- 所有本计划 P1/P2 项关闭或有明确延期理由。
- 每个完成 phase 都有 handoff 文档。

## 6. 完成标准

本轮修复完成前，不能再只用“能运行”验收。必须同时满足：

- 运行中所有页面暂停行为一致。
- 中文玩家界面没有明显英文属性词、内部 ID、调试槽位。
- 地牢是 tile 场景，不是节点图。
- 至少一套 gpt-image-2 生成素材真正通过流水线接入游戏。
- 标题、地牢、战斗、事件、商店、休息都有统一 UI 和场景感。
- 美术、音乐、字体、UI 控件有来源记录和 manifest。
- 截图/试玩验收能证明它接近成熟像素 RPG 的第一分钟体验。

## 7. 立即执行顺序

1. Phase 13R 已完成。
2. Phase 14A 已完成：统一 UI kit 和玩家语言层。
3. Phase 14B 已完成：打通 gpt-image-2 生成、后处理、contact sheet 和 manifest。
4. Phase 14C 已完成：把地牢改成 tile 场景。
5. Phase 15 已完成：补强战斗场景和 Boss 身份。
6. Phase 16 已完成：重做事件、商店、休息场景。
7. Phase 17 已完成：统一标题、主题、美术、音乐。
8. Phase 18 已完成：视觉回归、可访问性基础选项和最终试玩验收。

## 8. 变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-05-07 | 初始创建 | 用户要求统一 UI、使用 gpt-image-2 标准像素素材，并把修复验收提高到成熟像素游戏标准 |
| 2026-05-07 | 标记 Phase 13R 完成 | 暂停语义、中文奖励/事件反馈、Q 暂停和事件 ID 暴露已修复 |
| 2026-05-07 | 标记 Phase 14A 完成 | UI kit、玩家语言 formatter、运行页 action bar 和截图/测试验收已完成 |
| 2026-05-08 | 标记 Phase 14B 完成 | Codex GPT Image 2 地牢素材流水线、asset card、contact sheet、manifest 和校验脚本已完成 |
| 2026-05-08 | 标记 Phase 14C 完成 | 地牢 tile 场景、门/走廊/交互物件、陷阱损失提示和截图验收已完成 |
| 2026-05-08 | 标记 Phase 15 完成 | 战斗 sprite sheet、普通战/首领战差异、攻击/防御/奖励效果和中文字段清理已完成 |
| 2026-05-08 | 标记 Phase 16 完成 | 非战斗地点 sprite sheet、事件/商店/休息场景、商品标题和风险标签清理已完成 |
| 2026-05-08 | 标记 Phase 17 完成 | 主题 sprite sheet、标题场景、Git 主题地牢物件、基础动效和 BGM 响度记录已完成 |
| 2026-05-08 | 标记 Phase 18 完成 | 中英文截图脚本、整数倍缩放、可访问性基础设置、最终试玩记录和问题关闭/延期清单已完成 |
