# Yaiba GB - graphics translation (gfx agent)

Tags: **[runtime]** = seen in PyBoy on the built ROM, **[static]** = from code/data reading, **[guess]** = unproven.

## Usage
```
python3 -I tools/gfx/build_gfx.py in.gb out.gb --orig pristine.gb    # or $YAIBA_ROM; normally chained by build.py
```
- The input can be 256 KB or 512 KB. A 256 KB input is expanded the same way insert.py does it: $FF padding, 0x148=4.
- Every byte the script changes is first asserted to equal the pristine ROM (MD5 7d76d2a9...). For compressed entries, the decompressed input data must equal the original data. So running it twice fails, and so does running it after another step that touched the same graphics.
- It fixes the header checksum and the global checksum.
- Tested on its own (orig -> tmp/en.gb) and chained after `insert.py ... tests/test_trans.json --expand` (tmp/txt_en.gb). Both boot, and the title, chapter card and HUD render. **[runtime]**

## Codec (tools/codec.py)
- `decompress_at(buf, off)` is an independent copy of re/tools/gfxdec.py. It asserts that it matches gfxdec on all 29 $3DE5 entries.
- `compress(data, type)` picks the smallest mode per block. Modes: 0 zero, 1 bitmask, 2 bitmask + per-tile row XOR, 3 raw (type<$10) or running XOR.
- It re-creates **all 29 $3DE5 entries and all 15 boss + 9 stage assets (banks 08/0E/0F) byte-identically**. It self-checks decompress(compress(x)) == x on every call. **[static, verified]**
- Mask bits are read LSB-first per byte. hram $FF98-$FF9F works as a 65-bit rotate. Only the low 2<<n bytes matter for n=1/2. Type n=3 (128-byte blocks) is not used by the game and is not supported.

## What changed
| screen | data | location after build | change |
|---|---|---|---|
| Title | tileset #00 (record $3DE5+0) | 18:4000 | `tsurugiisamidensetsu` -> "SAMURAI LEGEND", white 7x11 2px-stroke caps in the black banner (x22-142, y12-24). Only unique tiles in map rows 1-3 are edited, YAIBA logo untouched. Same tileset also feeds the ending map #1B; no #1B tile changed **[static]** |
| Chapter card | tileset #08 (+$3DE5+8) / map #09 (+9) | 18:461D / 18:4B17 | Circles 1 and 2 removed (gray $99). "CHAPTER" (black, white outline, dark-gray drop shadow) on 16 new tiles (free/kanji codes 87 88 97 98 A5-A8 B5-B8 E6 E7 F6 F7 E8 E9 F8 F9). Circle 3 now shows the numeral tiles 85/86/95/96 |
| Chapter numerals | bank 7 raw, numeral k at tiles $80+2k (+1, +16, +17), 9th at $A0 = ROM $1C800-$1CA1F | in place | `ichi`..`kyuu` -> 1..9. Circle shading = per-pixel mode of the 9 originals. All 9 seen **[runtime]** (shots/card_all) |
| Orb kanji icons `raifuuryuuhaan` | tileset #0E codes E0/E2/E4/E6/E8 (2x2) **and** the bank-7 copy, tiles $A6-$AF/$B6-$BF | 18:4C20 / in place | T, W, St, Ov, Dk = orb level 1-5: Thunder, Wind, Storm (`fuurai` fuurai, the combined glyph; earlier mislabelled Dr), Overlord, Dark (tl/out_all.json names). Shown via icon scripts 1:752B (index = orb level at $D812+sword-1). Both copies patched; which one the game reads was not isolated |
| Dragon-orb 4x4 icon | bank 7 tiles $48-$4B,$58-$5B,$68-$6B,$78-$7B (ROM $1C480..) | in place | `ryuu` -> "Dr". Drawn by bank0 $0719 from $D817 **[runtime]** |
| Power-up orb icons | bank 7 $6000-$6FFF raw, 5x5 blocks at tiles base+16*row+col; base = powerup header byte (bank0 $051D-$052C: bank 7, d=$60, bc=$0505). 50 `kaminari`, 55 `kaze`, 5A `fuurai`, A0 `ha`, A5 `an`, AA `ryuu` (00/05/0A are sword icons, untouched) | in place | T / W / St / Ov / Dk / Dr, same font and orb treatment as sword select. All 6 seen **[runtime]** on the engine build (shots/powerup_icons_*: chapter-1 clear path with icon byte forced by hook at $051F); T, W, Dr and the L2 sword also seen on the natural chapter 1/3/4/5 clear paths (shots/powerup_*) |
| HUD | bank 2 $4D00-$4D8F raw (window tiles D0-D8, 3x3) | in place | `inochi`/`kiai` -> "LIFE"/"KI", 5x7 font, dark-gray down-left shadow, frame line kept **[runtime]** |
| Game over | tileset #17 (+$3DE5+$17), map #18 unchanged | 18:516C | `konteinyuu` -> "CONTINUE" (tiles BF CE CF DE DF EE EF FE FF), `geemuwoyameru` -> "QUIT" (F0-F8). `ge`'s dakuten tile F9 blanked. Letters come from the title-screen 8x8 Latin font with the menu's up-left dark-gray shadow. "×n" uses font tile $40+n at $98B0, so the engine's English font must keep digits at codes 40-49 **[runtime]** |
| Pickup orbs `chikara`/`ki` (sprites) | bank 6 object-tile sets $6000 and $6400 (two identical copies), tiles 2C/2D/3C/3D and 2E/2F/3E/3F | in place | -> "P" (power) and "K" (ki), 6x9 font, outline of the `chikara` orb used as a clean template. Loaded into VRAM $82C0 in stage 1 **[runtime]**. Never seen on screen: no pickup dropped in 12,000 frames of scripted play |
| Boss cards | bank 0E assets 0-5 and 7 (table of bank-relative offsets at 0E:$4000; bank hard-coded at bank0 $0411, `ld b,$0e`, 0F for chapter >= 9) | bank 0E repacked | Name row = map #1C row 14, tile codes 01-14 (asset offset $800+16*code), right-aligned. New: BOULDER / CEDAR POLLEN / SNOWMAN / ANT / GRAPE / MUSHROOM / CENTIPEDE SOLDIER. RUBY and the bank-0F cards (SILVER, SAPPHIRE, DIAMOND, EMERALD, JEWEL, GOLD, ONIMARU) are unchanged. The font comes from the existing name tiles; C and T are hand-drawn in the same style. All 8 bank-0E cards seen **[runtime]** (shots/bosscards) |

### Bank usage
- **Bank $18:** $4000-$5702, 5,891 bytes. $18:5703 onward and banks $19-$1F are still free.
- **Bank 0E:** repacked. All 8 boss assets are rewritten back to back from $4010 and the offset table is updated. Unchanged assets are copied byte-identical. The new end is $73B5 (originally $73A1). This ate 20 bytes of the original $FF tail, so 3,147 bytes are left. The repack is needed because 4 of the renamed streams grew by 6-18 bytes.
- **Outside my banks:** the repack is the only data move outside $18-$1F. It is graphics-only and limited to bank 0E's own asset area and $FF tail. The other changes outside $18-$1F are in-place raw tile edits (banks 2, 6, 7) and the bank-0 $3DE5 records (bank and src bytes only, for #00 #08 #09 #0E #17).

## Not changed / notes
- The `yaiba` hiragana in the YAIBA logo's three circles are part of the logo art; kept.
- The ending (map #1B, title tileset) is already English ("PRESENTED BY BANPRESTO / END"), as is GAME OVER. **[runtime]**
- Text-font screens (sword-select labels `chikara`/`hayasa`/`hissatsuwaza`, sword and orb names, intro crawl) belong to the text/engine agents.
- Sword select also copies bank 2 $4400-$47FF (font codes 40-7F) to $9400 (bank0 $06C3). An English font must be complete in that range for this screen. **[static]**
- Boss card #1C uses tileset-#08 tile codes, but the boss asset overwrites all of $8800-$97FF. So the new CHAPTER tiles cannot leak into it; the card is pixel-identical before and after. **[runtime]**

## Tools
- `codec.py`: codec, with a self-test (`python3 -I tools/codec.py rom`).
- `designs.py`: all redraws, as pure functions.
- `glyphs.py`: fonts BIG 7x11, HUD 5x7, SMALL 6x9.
- `gbgfx.py`: 2bpp and PNG helpers.
- `preview.py`: static 4x previews.
- `shots.py rom tag`: runtime screenshots into shots/*_{before,after}.png. These cover the title, the chapter-1 card, all 9 numerals, the HUD, the game over screen, sword select (all 5 orb icons and the dragon icon) and the 8 bank-0E boss cards. Boss cards are reached with a PyBoy hook on $0407 that sets $D810.
- `shot_powerup.py` / `shot_powerup_forced.py`: power-up screens via engine/tools/emu.py (natural clear paths / forced icon).
- `film/filmstate/mkstate/inspect_state/force/shot_swsel/find_pickup.py`: harness helpers.
- Scene forcing: card = $03B3 from the chapter-1 dialogue state with $D810 = chapter; game over = $0249 from stage, with $FFD0 = continues. Jumping straight to $039F or $0407 corrupts VRAM, because writes happen while the LCD is on.
