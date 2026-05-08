# Phase 15 Battle Sprite Sheet Prompt

Create a pixel-art sprite sheet for a 2D dungeon roguelike game. Use case: game sprite sheet. Asset type: 16x16 pixel sprites for runtime use. Style: crisp readable 16-bit pixel art, limited palette, high contrast silhouettes, no antialiasing, no text, no labels, no watermark.

Canvas layout: exactly a 5 columns x 3 rows grid, each cell contains one centered sprite with generous padding. The background must be perfectly flat solid #00ff00 chroma-key green across the whole sheet, with no shadows, gradients, texture, borders, grid lines, or lighting variation. Do not use #00ff00 in any sprite.

Sprites in reading order, left to right, top to bottom:

1. `player_idle`: small developer adventurer with cloak, satchel, glowing commit shard.
2. `player_attack`: same adventurer lunging with short glowing code blade.
3. `player_defend`: same adventurer behind small shield with terminal glyph motif.
4. `enemy_default_git_goblin`: small mischievous git-themed goblin enemy, distinct from player.
5. `boss_fix`: bug-like boss with red warning eyes and broken patch marks.
6. `boss_refactor`: armored ancient code golem with tangled scrolls.
7. `boss_merge_conflict`: two-headed branch monster with split red/blue colors.
8. `boss_ci_sentinel`: mechanical sentinel with checkmark/cross lights.
9. `boss_secret_leak`: shadowy vault wraith with keyhole glow.
10. `boss_release_gate`: heavy gate guardian with gold lock and crown shape.
11. `fx_slash`: diagonal bright sword slash effect.
12. `fx_shield`: circular shield shimmer effect.
13. `fx_reward_drop`: small falling gold/experience reward sparkle.
14. Empty transparent-style placeholder: tiny dim dust sparkle only.
15. Empty transparent-style placeholder: tiny dim dust sparkle only.

Important: each sprite must be isolated inside its own cell; no sprite may cross cell boundaries. Make every boss visually different at 16x16 size. Keep the sheet orthographic/front-facing, game-ready, and easy to cut into cells.
