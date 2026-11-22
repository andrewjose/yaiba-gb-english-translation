# Yaiba GB - English text engine (VWF) and fonts

Tags: **[runtime]** = seen in PyBoy on the built ROM, **[static]** = from code/data reading, **[guess]** = unproven.

## Build
```
python3 build.py --rom orig.gb [--out build/] [--rgbds DIR]   # full pipeline (see README); intermediates in build/work/
# individual steps, as run by build.py (env: YAIBA_ROM, YAIBA_WORK=build/work, YAIBA_FONT_DIR=build/work/font, RGBDS_DIR):
python3 -I tools/re/extract.py orig.gb build/work/re                     # strings.json: ids, pointer locations, headers, field sizes
python3 -I tools/engine/mkfont.py --rom orig.gb --out build/work/font    # vwf.bin, widths.bin/json, fixed.bin, fixed8.tbl, PNG sheets
python3 -I tools/engine/build.py --rom orig.gb --tl build/work/tl/out_all.json --out build/work/engine/yaiba_en.gb --gfx
python3 tools/engine/typeset_check.py     # per-page widths/flags + build/typeset_contact.png (exit 1 on hard problems)
python3 tools/engine/shots.py ROM shots TAG [intro introA crawl swsel swsel2 gameover cardN clearNN rival hud]
```
- The fonts are regenerated on every build: fixed.bin starts from the original ROM's font page (bank 2 $4000), so it is never committed. tools/engine/font/ holds reference copies of the ROM-independent outputs (font_vwf.png, widths.json, fixed8.tbl).
- engine build.py inputs: out_all.json (`[{id,jp,en}]`, made by build.py from translation/en.json + extracted jp; "\n\n" = page, "\n" = hard break), strings.json (pointer locations). `--override x.json` ({id: en}) for test refits.
- rgbasm is run with `-I <font dir>`; src/vwf.asm INCBINs vwf.bin/widths.bin from there.
- It errors (exit 1, no ROM) on: page overflow, rival line-slot overflow, rival tile budget, fixed field too long or past the visible cells, glyph not in the fixed font, sword-select glyph outside codes 40-7F.
- rgbds: `src/vwf.asm` is assembled and overlaid with `rgblink -O base.gb`, then `rgbfix -v -p 0xff` (header and global checksums). Map/sym in `build/`.
- The chained ROM passes build_gfx.py's pristine-byte asserts (no overlap) **[runtime: built, booted, all scenes below]**.

## Hooks (all [static], behaviour [runtime])
| where | original | new |
|---|---|---|
| 1:$4324 | box printer (chapter_intro $9947, chapter_end $9923, powerup $9947) | `jp VwfPrintBox` (1:$77F0) |
| 1:$41F0 | rival/ending printer (BG $9C00, 8 f/char) | `jp VwfPrintRival` |
| 0:$0CDE | VBlank char writer (called from the VBlank chain when $D81F bit 6) | `jp VwfVBlank` (0:$3E76) |
| bank 2 $4000-$47FF | kana font (loaded by $0A13 to $9000; sword select copies $4400-$47FF to $9400 via $06C3) | 00-3F/40-49: fixed 8x8 font + original digits; 4A-7F: the sword-select page (precomposed labels + reserved name tiles). $0A13 itself is unchanged |
| 0:$0309 | `call $0A13` in the intro-crawl scene | `call CrawlFont`: same copy, from the precomposed crawl page $17:$5000 |
| 0:$0752 | `call $0A48` (queue sword record script) | `call SwordNameHook`: upload that sword's name tiles to codes 6E-72, then `jp $0A48` |
| 0:$07C1 | `call $0A48` (queue orb record script) | `call OrbNameHook`: upload orb name (73-78) + move name (79-7F) tiles, then `jp $0A48` |
Bank-0 callers ($03FE, $04E7, $0538) are untouched: the printer returns HL = stub+2, so their `inc hl / ld a,(hl+) / cp $FF / jp nz,$0069` page check reads the stub's flags byte and exits. Pages are handled inside the new printer.

## Space used
- Bank 0 $3E76-$3F68 (VwfVBlank, FarByte, CrawlFont, name hooks, NameUpload; 243 of 394 bytes).
- Bank 1 $77F0-$7A2x code (~560 bytes), $7C40-$7F96 VWF font (760 bytes glyphs + 95 widths). Stubs reuse the old text regions $6BAA-$6D8F, $6DA6-$7122, $75EB-$7753 (box-clear VRAM scripts $7123-$7226 and the menus at $7227+ are kept).
- Bank $10 $4000+: English messages (all of them fit: ~2.6 KB, end $4A19). Banks $11-$16 are reserved for text overflow. Bank $17: $4000+ relocated tilemaps #07 (intro crawl) and #0F (sword select) with $3DE5 records repointed; $5000-$57FF crawl tile page; $5800 sword-name tiles (6 x 40 bytes 1bpp); $5900 orb/move-name tiles (10 x 104 bytes 1bpp).
- WRAM $D900-$D92F (engine state) and $D930-$D997 (name-tile staging buffer); see the DEFs at the top of vwf.asm. D8A0-D99F stays zero in the original through boot, intro, stage, stage clear and ending **[runtime]**, and no `ld (nn)` in the ROM references D8A0-DC7F except 2 likely-noise hits at $DA7x/$DAFx **[static]**.

## Message format
- Far message (bank $10-$16): ASCII $20-$7E glyphs, `$FF` new line, `$FE` page break (wait for A, clear box, restart at line 0), `$00` end.
- Bank-1 stub at the address the game's pointer/immediate holds: `[original header bytes][bank][lo][hi][flags]`; flags bit 0 = reset the rival tile allocator (set on rival_00).
- Wrapping is done offline by `tools/textfit.py` (shared by build.py and typeset_check.py): pixel widths from font/widths.json, balanced breaking (DP over the greedy line count, squared slack, last line weighted 0.5, huge penalty for a single stranded word), no breaks inside NOBREAK names (Yaiba Kurogane, Thunder Orb, Dragon God Orb, Two-Sword Style, Cedar Pollen Soldier's, ...) or between a number and the next word, pyphen en_US hyphenation only when a word alone is wider than the line (>=3 chars each side), sentence-boundary page splitting when a page exceeds 8 lines, error if one sentence exceeds a page.

## Geometry
| block | printer DE | English line 0 | lines | tiles/px | delay |
|---|---|---|---|---|---|
| chapter_intro, powerup | $9947 | $9927 (row 9, col 7) | 8 x 1 row | 12 tiles, ink <= 95 px | 2 f/char, 1 with A held |
| chapter_end | $9923 | $9903 (row 8, col 3) | 8 x 1 row | 14 tiles, ink <= 111 px | same |
| rival (ending) | caller's DE ($9C23, $9CE3, $9DA3, $9DE3, $9E63) | same | fixed slots 3/3/1/2/2, 2-row spacing | box shows cols 3-17: ink <= 118 px | 4 f/char, no skip |
Left margin 1 px. English uses the dakuten row too, so an 8-row box gets 8 lines. Page clears reuse the game's VRAM scripts (1:$7123/$7168 for the 14-wide box, 1:$71AD/$71EA for the 12-wide box), which zero exactly the 8 box rows **[static+runtime]**.

## How the VWF works
- Canvas: tile codes $0A-$7F of the $9000 block (signed addressing, LCDC.4=0). $01-$03, $08, $09 are frame tiles in the ending scene (**[runtime]**: `InIn` garbage on the frame when the canvas started at $01), so the canvas starts at $0A.
- Box mode: fixed grid, code = $0A + line*W + col (max $79 for 14x8). Rival mode: lines packed (next line starts after the highest mapped code); a ring wrap to $0A when fewer than 17 codes remain ($80-17); the old lines have scrolled out of the 3-line box by then. All 5 rival strings fit without wrapping today.
- Composition: 2-tile 1bpp WRAM buffer (left = current tile, right = overflow). Per glyph: lazy shift (while pen >= 8: left <- right, right <- 0, col++), OR the 8 glyph rows shifted right by pen (srl/rr into the right tile), queue the flush, pen += advance. Spaces only advance.
- VBlank (VwfVBlank): copies the 16 buffer bytes as 32 bytes 2bpp (both planes) to $9000+code*16 (2 contiguous tiles) and writes the two BG map cells (the right one is clamped to the left cell at a box's right edge). Runs at LY 145 and ends at LY 147 **[runtime]** (~250 M-cycles; VBlank ends at 153). The VRAM-script handler (bit 5) zeroes A, so the two never run in the same frame **[static]**.
- Map cells start blank (box rows are $00 in the scene maps and after the clear scripts) and become canvas codes only when a tile is flushed, so stale tile data from a previous page is never visible.
- FarByte (bank 0): `di`, switch to the text bank, read, switch back to [$FFC7], `ei`. Called once per character.
- Per-character blip $8E is kept (not on spaces).

## Fonts
- VWF (tools/engine/mkfont.py, drawn as ASCII art in the script; no external font data): 8 px cell, cap height 6 (rows 0-5), x-height 4 (rows 2-5), descenders rows 6-7, advance = ink + 1, space 3. Sheet: tools/engine/font/font_vwf.png.
- Fixed 8x8 (font/fixed.bin -> bank 2 $4000, table font/fixed8.tbl): VWF glyphs widened to 6 px. Only its digits 40-49 (original tiles; game over `xn` = $40+n at $056C, sword-select stats) are still shown; build.py overwrites codes 4A-7F with the sword-select page, so the letters listed in fixed8.tbl for 4A-7F are not in the ROM.
- 7C/7D are now `:` and `/`, so build.py clears any dakuten row left above a translated tilemap line.

## Precomposed proportional text (no fixed-pitch text is left)
All former 8x8 fixed-font text is now rendered with the VWF glyphs at build time (tools/compose.py) **[runtime]**:
- **Intro crawl** (map #07): each line is rendered into 16 tiles (cols 2-17), centred, identical/blank tiles deduped (blank -> 00). 103 of 118 codes used (0A-7F; 01-03/08/09 are the box-frame tiles on map $9800 and are copied from the original font). The page is loaded to $9000 by CrawlFont instead of the font. Glyph fragments at the top/bottom edge of the box are the neighbouring lines scrolling in/out (same as the original).
- **Sword select static text** (map #0F): "Yaiba!" / "Which one?" (speech box, col 9, 1 px margin), "Pow:" / "Spd:" right-aligned in cols 14-17 (the label carries its own colon, replacing tile $DB; the stat digit $40+n stays at col 18), "Move:" right-aligned in cols 1-7 with a 3 px gap before the move name at col 8. 20 tiles (4A-5D of the 4A-6D budget).
- **Sword names** (records 1:$7227, field $990D): cells = 00, 6E-72; the name is right-aligned in 5 tiles. **Orb names** ($99AA) cells 73-78 + 00 00, **move names** ($9A08) cells 79-7F + 00..; left-aligned with 1 px margin. Dakuten rows zeroed. Tile data per value lives in bank $17; the hooks at $0752/$07C1 stage it through WRAM (8-byte chunks with interrupts off, bank restored from $FFC7) and write it with STAT mode 0/1 checks (2 bytes per check, interrupts off only around each write), then queue the game's own script. Orb record index = (sword-1)*2 + $D861, as the game computes it at $079C **[static+runtime]**.
- Stale orb/move names after leaving the orb choice with B are original behaviour (the JP ROM shows the same).
- The fixed font in bank 2 is now only used for the digits 40-49 (game over `xn`, sword-select stats).

## Tests run (shots/, `jp_*` = original, `full_*` = chained build)
- Title and crawl (full_crawl_strip.png, full_crawl_f*.png), chapter cards 1-9 with their intro dialogue (full_cardN_wait1.png), stage-clear paths for chapters 1-8 and 10 (chapter_end pages, multi-page clears `*_wait*_after.png`, power-ups), ending/rival scene (full_rival_strip.png, rival_before_after.png), sword select incl. orb/move names (full_swsel_f*.png, full_swsel2_f*.png), before/after pairs shots/ba_*.png, game over (full_gameover.png), a stretch of gameplay with the HUD (full_hud_strip.png). Contact sheet of all in-game pages: shots/contact_ingame_pages.png. Offline typesetting: shots/typeset_contact.png.
- Typewriter: chapter_intro_00 180 frames (A held: 92) vs 412 in the original.
- Scene forcing (tools/emu.py): `boot` stops at the first intro printer call; `boot_gameplay` presses A through the intro and boss card until the stage loop ($01D6); `stage_clear(pb,n)` jumps to $0206 with $D810=n, which runs the real chapter_end -> power-up -> next-scene sequence with the stage graphics loaded (jumping straight to $04AC from the intro state gives garbage graphics in both ROMs).

## Known issues / open
- rival_00: "Impressive," alone on line 1 because "Yaiba Kurogane" may not break and the full line is 1 px too wide; a rephrase would balance it.
- chapter_end_09 ("The End") is in the table, but $04AC returns early for chapter 9; no path that prints it was found **[guess]**.
- Power-up screens still show the kanji orb icons in the left frame (gfx agent's area).
- VBlank timing is verified only in PyBoy (LY 145-147), and PyBoy does not block VRAM writes in mode 3, so NameUpload's STAT gating is verified by reading only. Real-hardware/flash-cart check pending.
