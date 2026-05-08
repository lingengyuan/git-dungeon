# Phase 16 Non-Combat Location Sprite Sheet Prompt

Create a pixel-art sprite sheet for a 2D dungeon roguelike game's non-combat locations. Use case: game sprite sheet. Asset type: 32x32 pixel sprites for runtime use. Style: crisp readable 16-bit pixel art, limited palette, high contrast silhouettes, no antialiasing, no text, no labels, no watermark.

Canvas layout: exactly 4 columns x 2 rows, each cell contains one centered sprite with generous padding. The background must be perfectly flat solid #00ff00 chroma-key green across the whole sheet, with no shadows, gradients, texture, borders, grid lines, or lighting variation. Do not use #00ff00 in any sprite.

Sprites in reading order, left to right, top to bottom:

1. `event_shrine`: small mysterious dungeon shrine with glowing commit shard altar.
2. `event_terminal_ruin`: broken ancient terminal ruin with faint code glyph glow, no readable letters.
3. `shopkeeper`: friendly compact dungeon merchant with hood, coin pouch, readable silhouette.
4. `shop_counter`: small wooden shop counter with potions, coins, and item display.
5. `rest_campfire`: cozy campfire with bedroll and soft orange light, no smoke crossing cell boundary.
6. `rest_shrine`: quiet healing shrine with blue-green light and small stone steps.
7. `choice_icon_risk`: compact warning/risk icon, red-orange danger symbol without text.
8. `choice_icon_reward`: compact reward icon, gold sparkle/treasure symbol without text.

Important: each sprite must be isolated inside its own cell; no sprite may cross cell boundaries. Keep the sheet orthographic/front-facing, game-ready, and easy to cut into cells. Every asset must remain readable when downscaled or displayed at 24-36 pixels.
