# Asset Credits

> 本文件按 CLAUDE.md「Project Principles」#5 的要求维护。所有进 `assets/` 的资源必须在此登记：来源、作者、license、下载日期、文件路径。
>
> **首版规则（Phase 0）**：BGM/SFX/sprite 仅收 **CC0**；字体仅收 **CC0 或 OFL**。其他授权一律不进。

## Sprites

| 资源包 | 作者 | License | 下载日期 | 来源 | 本地路径 | 说明 |
|---|---|---|---|---|---|---|
| Kenney Tiny Dungeon | Kenney (kenney.nl) | CC0 1.0 | 2026-05-03 | https://kenney.nl/assets/tiny-dungeon | `assets/sprites/kenney_tiny_dungeon/` | 16×16 地牢 tile + 角色 + 怪物 + 道具，含 `License.txt` |
| Kenney UI Pack | Kenney (kenney.nl) | CC0 1.0 | 2026-05-03 | https://kenney.nl/assets/ui-pack | `assets/sprites/kenney_ui/` | 按钮、面板、滑条、图标 |

## Audio — SFX

| 资源包 | 作者 | License | 下载日期 | 来源 | 本地路径 |
|---|---|---|---|---|---|
| Kenney RPG Audio | Kenney (kenney.nl) | CC0 1.0 | 2026-05-03 | https://kenney.nl/assets/rpg-audio | `assets/audio/sfx/kenney_rpg_audio/` |
| Kenney UI Audio | Kenney (kenney.nl) | CC0 1.0 | 2026-05-03 | https://kenney.nl/assets/ui-audio | `assets/audio/sfx/kenney_ui_audio/` |

## Audio — BGM

每首 BGM 均为 vorbis 立体声 OGG（44.1kHz）。Phase 0 规则：仅收 CC0；CC-BY/CC-BY-SA/GPL/非商用一律不进。

| 槽位 | 文件 | 时长 | 曲名 | 作者 | License | 下载日期 | 来源 | 处理 |
|---|---|---:|---|---|---|---|---|---|
| title | `assets/audio/bgm/title.ogg` | 69.4s | Adventure Theme — SuperHero_original_no_Intro | Cleyton Kauffman | CC0 1.0 | 2026-05-03 | https://opengameart.org/content/adventure-theme | 从 `Superhero_pack.zip` 取 `SuperHero_original_no_Intro.ogg`（无 intro 版本，可循环），文件原样未改 |
| chapter | `assets/audio/bgm/chapter.ogg` | 50.9s | Mysterious, Futuristic 8-bit Music Loop | Frenchyboy | CC0 1.0 | 2026-05-03 | https://opengameart.org/content/mysterious-futuristic-8-bit-music-loop | 原文件为 mono WAV (4.5MB)，用 ffmpeg 转码为 stereo OGG vorbis @128k |
| boss | `assets/audio/bgm/boss.ogg` | 26.7s | 8-Bit Battle Loop | Theodore Kerr (Wolfgang_) | CC0 1.0 | 2026-05-03 | https://opengameart.org/content/8-bit-battle-loop | 直接来自 `8BitBattleLoop_0.ogg`，文件原样未改 |
| gameover | `assets/audio/bgm/gameover.ogg` | 12.0s | Chill Chiptunes Collection — "Complications" | Holizna | CC0 1.0 | 2026-05-03 | https://opengameart.org/content/chill-chiptunes-collection | 从合集中取 `05 HoliznaCC0 - Complications.ogg`，截 0:08-0:20 段并加 1s 淡入/淡出，详见 `assets/audio/bgm/gameover.notes.md` |

## Fonts

| 用途 | 字体 | 文件 | 作者 | License | 下载日期 | 来源 | 备注 |
|---|---|---|---|---|---|---|---|
| 英文（拉丁） | VT323 | `assets/fonts/vt323/VT323-Regular.ttf` | Peter Hull (The VT323 Project, Google Fonts) | OFL 1.1 | 2026-05-03 | https://github.com/google/fonts/raw/main/ofl/vt323/VT323-Regular.ttf | 单源 OFL，含小写、终端复古风；替代付费的 m5x7 |
| 中文 | Ark Pixel 12px Proportional zh_CN | `assets/fonts/ark_pixel/ark-pixel-12px-proportional-zh_cn.ttf` | TakWolf | OFL 1.1 (`assets/fonts/ark_pixel/OFL.txt`) | 2026-05-03 | https://github.com/TakWolf/ark-pixel-font/releases/tag/2026.02.27 | release 版本 `2026.02.27`，下载 zip 内仅取 `proportional-zh_cn` 与 `OFL.txt` |

> **明确排除**：
>
> - **Zpix**：实际为「个人/教育免费」，非 OFL，不可用于发布作品（源 plan §7.3 标注勘误）。
> - **m5x7** (Daniel Linssen / Managore)：itch.io 当前页面要求付费下载，不符合 Phase 0「免费 CC0/OFL」规则。改用 VT323。

## AI 生成资源（gpt-image-2）

Phase 4 建立生成清单；当前生成路径优先使用 Codex 内置 GPT Image 2。素材在生成、后处理、contact sheet 核对和 manifest 接入前，**不计入已接入 sprite**。每个素材必须先有 asset card：

```yaml
id: <id>
source: gpt-image-2
prompt_file: assets/source_prompts/<id>.md
generated_at: YYYY-MM-DD
postprocess: [...]
license_note: generated project asset, keep source prompt and output
```

当前清单：

| ID | 状态 | Prompt | Asset card |
|---|---|---|---|
| title_banner | pending_generation | `assets/source_prompts/title_banner.md` | `assets/generated/asset_cards.yml` |
| player_pixel | pending_generation | `assets/source_prompts/player_pixel.md` | `assets/generated/asset_cards.yml` |
| boss_fix | pending_generation | `assets/source_prompts/boss_fix.md` | `assets/generated/asset_cards.yml` |
| boss_refactor | pending_generation | `assets/source_prompts/boss_refactor.md` | `assets/generated/asset_cards.yml` |
| boss_merge_conflict | pending_generation | `assets/source_prompts/boss_merge_conflict.md` | `assets/generated/asset_cards.yml` |
| boss_ci_sentinel | pending_generation | `assets/source_prompts/boss_ci_sentinel.md` | `assets/generated/asset_cards.yml` |
| boss_secret_leak | pending_generation | `assets/source_prompts/boss_secret_leak.md` | `assets/generated/asset_cards.yml` |
| boss_release_gate | pending_generation | `assets/source_prompts/boss_release_gate.md` | `assets/generated/asset_cards.yml` |

**接入规则**：只有生成、后处理、contact sheet 人工核对、再写入 `assets/manifest_sprites.json` 后，才能算作运行时美术资源。

## 新增资源步骤

1. 下载到 `assets/_downloads/`（由 `.gitignore` 排除，不入库）。
2. 在**源页面**逐文件确认 license——禁止凭二手转述。
3. 解压/移动到 `assets/<分类>/<包名>/`。
4. 在本文件对应表追加一行（**禁止**只写"待补充"或留空 license）。
5. 跑 `python scripts/verify_assets.py` 与 `python scripts/verify_audio.py`。
