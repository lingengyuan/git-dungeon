# Generated Asset Staging

This directory tracks AI-generated pixel art candidates before they are accepted into the runtime sprite manifest.

Generated images do not count as in-game assets until all of these are true:

1. The image was generated with the declared model in an asset card.
2. The source prompt is stored in `assets/source_prompts/`.
3. The output is postprocessed with transparent background, crop, nearest-neighbor downscale, and palette cleanup.
4. A contact-sheet check confirms the sprite reads clearly at final size.
5. `assets/manifest_sprites.json` points to the processed sprite.

Current accepted generated asset batches:

- Phase 14B dungeon tiles:
  - Prompt: `assets/source_prompts/phase14b/dungeon_sheet.md`
  - Raw output: `assets/generated/raw/phase14b/dungeon_sheet.png`
  - Processed sprites: `assets/generated/processed/phase14b/`
  - Contact sheet: `assets/generated/contact_sheets/phase14b_dungeon.png`
  - Asset card: `assets/generated/phase14b/asset_plan.json`
- Phase 15 battle sprites:
  - Prompt: `assets/source_prompts/phase15/battle_sheet.md`
  - Raw output: `assets/generated/raw/phase15/battle_sheet.png`
  - Processed sprites: `assets/generated/processed/phase15/`
  - Contact sheet: `assets/generated/contact_sheets/phase15_battle.png`
  - Asset card: `assets/generated/phase15/asset_plan.json`
- Phase 16 non-combat location sprites:
  - Prompt: `assets/source_prompts/phase16/noncombat_sheet.md`
  - Raw output: `assets/generated/raw/phase16/noncombat_sheet.png`
  - Processed sprites: `assets/generated/processed/phase16/`
  - Contact sheet: `assets/generated/contact_sheets/phase16_noncombat.png`
  - Asset card: `assets/generated/phase16/asset_plan.json`
- Phase 17 theme sprites:
  - Prompt: `assets/source_prompts/phase17/theme_sheet.md`
  - Raw output: `assets/generated/raw/phase17/theme_sheet.png`
  - Processed sprites: `assets/generated/processed/phase17/`
  - Contact sheet: `assets/generated/contact_sheets/phase17_theme.png`
  - Asset card: `assets/generated/phase17/asset_plan.json`

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/postprocess_pixel_assets.py --config assets/generated/phase14b/asset_plan.json
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase14b/asset_plan.json
PYTHONPATH=src .venv/bin/python scripts/postprocess_pixel_assets.py --config assets/generated/phase15/asset_plan.json
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase15/asset_plan.json
PYTHONPATH=src .venv/bin/python scripts/postprocess_pixel_assets.py --config assets/generated/phase16/asset_plan.json
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase16/asset_plan.json
PYTHONPATH=src .venv/bin/python scripts/postprocess_pixel_assets.py --config assets/generated/phase17/asset_plan.json
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase17/asset_plan.json
```
