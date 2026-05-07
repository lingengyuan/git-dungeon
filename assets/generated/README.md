# Generated Asset Staging

This directory tracks AI-generated pixel art candidates before they are accepted into the runtime sprite manifest.

Phase 4 does not count a generated image as an in-game asset until all of these are true:

1. The image was generated with the declared model in `asset_cards.yml`.
2. The source prompt is stored in `assets/source_prompts/`.
3. The output is postprocessed with transparent background, crop, nearest-neighbor downscale, and palette cleanup.
4. A contact-sheet check confirms the sprite reads clearly at final size.
5. `assets/manifest_sprites.json` points to the processed sprite.

Current `gpt-image-2` entries stay `pending_generation` until Codex-generated raw outputs, processed sprites, contact sheets, and asset cards are present and verified.
