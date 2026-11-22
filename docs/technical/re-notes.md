# Kenyuu Densetsu Yaiba (GB, J) - reverse-engineering notes

ROM: `Kenyuu Densetsu Yaiba (Japan).gb`, CRC32 CC19768E, MD5 7d76d2a9eaada93dc846efe1b2a815cc.
MBC1 (0x147=01), 256 KB (0x148=03), no RAM. The header global checksum (0x14E) is wrong in the original. insert.py only recalculates it if the ROM changed.
Tags used below: **[runtime]** = confirmed at runtime in PyBoy, **[static]** = found by reading code or data, **[guess]** = not proven.

## 1. Encoding (yaiba.tbl)
- The code is the tile index into the font at VRAM $9000. LCDC.4=0, so the BG uses signed tile data: codes 00-7F are the font and 80-FF are $8800-$8FFF scene graphics. **[runtime]**
- 4A-77: hiragana `a`..`n` in gojūon order, without `i`/`e`. Proven by a relative search for `osoikakaru` / `osoikakararete` / `korerano` / `nihonwoosou`; every hit gave base 0x4A. **[runtime]**
- 0A-37: katakana `a`..`n` in the same order. 38-3B: `tsuyayuyo`. 06/07: `i` `u` (the only small katakana). 3C `-`, 3D , 3E , 3F ♥. 40-49: 0-9. 78-7B: `tsuyayuyo`. 7E `!`, 7F ``, 04 ‥, 05 , 00 space. **[runtime]** render test
- 7C `"` and 7D `` are **postfix** bytes. The printer peeks at the next byte. If it is 7C or 7D, the printer writes that byte to the tile directly above (addr-$20). Every text line therefore takes two BG rows: a diacritic row, then the glyph row. **[static+runtime]**
- 01-03, 08, 09: box/cursor graphics, not text.
- The font has no Latin letters, no kanji, no  and no small `aiueo`/`aeo`. **[static]**
- Control bytes: FF = end of line (the printer moves down +$40, i.e. 2 rows). FF FF = end of page/message. In multi-page blocks, a further FF after FF FF means another page follows (the box is cleared by a VRAM script and the game waits for A). Any other byte ends the message; in the original that byte is the next string's header. **[static]**, page change **[runtime]**
- Header bytes come before the text but are not text: chapter_intro has 2 (portrait tile offset into bank 2 $5000+16n as a 5x5 block, then chapter numeral offset into bank 7 $4000+16n as a 2x2 block). chapter_end and powerup have 1 (image offset). rival has none.

## 2. Text bank map (all script text is in bank 1)
| block | where | pointers | format | strings | chars (JP) | bytes |
|---|---|---|---|---|---|---|
| chapter_intro (chapter card dialogue) | 1:6BAA-6D8F | table 1:6B96, 10 ptrs (0 and 1 share a pointer); bank0 $03CA | 2-byte hdr, 1 page, 12 cols x 4 lines at $9947 | 9 | 387 | 486 |
| chapter_end (after boss / rescue / item / ending "`owari`") | 1:6DA6-7087 | table 1:6D90, 11 ptrs (0 and 1 shared); bank0 $04C9 | 1-byte hdr, multi-page, **14** cols x 4 lines at $9923 **[runtime]** | 10 | 585 | 738 |
| rival (Onimaru) | 1:7088-7122 | code immediates 1:4146/415E/416C/4184/41BE (`ld hl,nn`) | no hdr, printer 1:$41F0 (fixed 8 frames/char, no A-skip), BG $9C23/$9CE3/$9DA3/$9DE3/$9E63 | 5 | 121 | 155 |
| powerup (orb/sword/HP messages) | 1:75EB-7753 | code immediates 1:4291/4306/42E3/4258/426F/4282+42A9/42B8; bank0 $0509 | 1-byte hdr, multi-page, 12x4 at $9947 | 7 | 284 | 361 |
| sword_menu (sword names) | 1:7233-7300 | table 1:7227, 6 ptrs (#0 empty) | record = 3 hdr bytes + VRAM script; name field 6 cells at $990D, dakuten row $98ED | 5 | 28 | 30 |
| orb_menu (orb + special-move names) | 1:7315-752A | table 1:7301, 10 ptrs | VRAM script; orb name 8 cells at $99AA (dakuten $998A); move name 8-9 cells at $9A08 (dakuten $99E8) | 20 | 139 | 164 |
| intro_scroll (opening crawl) | compressed tilemap #07, bank 5 $46CF -> $9C00 | gfx table bank0 $3DE5+7*5 | 9 lines (2 rows each), cols 3-19 | 12 | 157 | 204 cells |
| sword_select_screen labels (`yaiba!`/`dorewo` `erabuno`/`chikara`/`hayasa`/`hissatsuwaza`) | compressed tilemap #0F, bank 5 $4CCD -> $9800 | $3DE5+0x0F*5 | fixed cells | 5 | 25 | 48 cells |

Totals: 73 extractable entries, about 1,726 JP characters. Dialogue uses 1,740 bytes in bank 1.
- VRAM script format (interpreter bank0 $0CC1, run from VBlank): `[n][lo][hi][n bytes]...[00]`. Used for menus and for clearing boxes: 1:7123/7168 (chapter_end box), 1:71AD/71EA (powerup box), cursor scripts at 1:7754. **[static]**
- Other bank-1 data: 1:752B (icon scripts), 1:776A-77EF (OAM tables). These are not text.
- No other printer exists: `cp $7C` appears only in 1:$420D and 1:$4343. The other kana-like byte runs in banks 2, 5, 7 and 10 are graphics. No password screen, VS mode or credits text was found. The ending is chapter_end_09 ("`o` `wa` `ri` ♥"). **[static]**

## 3. Tools (tools/)
- `extract.py rom outdir` -> `strings.json` + `all_strings.csv`. It follows the live pointers: tables, code immediates and the $3DE5 gfx records.
- `insert.py orig.gb strings.json [trans.json] out.gb [--tbl X.tbl] [--expand]`:
  - Dialogue is repacked in original order into the original regions and then into the free bank-1 tail (77F0-7BFF, 7C40-7FFF). Every pointer and code immediate is repointed. When a multi-page message needs one, a 00 terminator is added. Lines longer than the box width produce a warning.
  - Menu fields are fixed-length; dakuten rows are rebuilt.
  - Tilemaps are decompressed, edited, re-compressed (codec subset: modes 0/1, self-tested), placed in free space in banks 5/0D/09/03, and the $3DE5 record (bank, src) is repointed. Since the record holds the bank, a tilemap can live in any bank.
  - `--expand` makes a 512 KB ROM (0x148=4). The header checksum is fixed.
- **Round trip:** `insert.py orig strings.json out.gb` gives MD5 7d76d2a9eaada93dc846efe1b2a815cc, byte-identical, also with `--tbl yaiba.tbl`. **[verified]**
- **Relocation test** (`tests/test_trans.json`): every chapter_end message was lengthened by one page and the intro line was changed. This pushed rival and powerup text to 1:78CB+ and the intro tilemap to 05:5492. Re-extraction matches the input exactly. The relocated chapter_end_02 was displayed with all its pages (tmp/ff.png). **[runtime]**
- Other tools: `gfxdec.py` (decompressor, matches VRAM), `dumpgfx.py`, `sm83dis.py` (disassembler), `hooklog.py` (PyBoy exec hooks), `snap/film/forcefilm.py` (screenshots, scene forcing), `freespace.py`, `fontsheet.py`, `rendermap.py`, `relsearch.py`.

## 4. Font, printer, graphics text
- **Font:** ROM 0x08000-0x087FF (bank 2 $4000-$47FF). 128 tiles, raw 2bpp, **uncompressed**. Glyphs are 1-colour (both planes equal, apart from a few graphic tiles). The font is loaded by bank0 `$0A13: bank2 $4000 -> VRAM $9000, $800 bytes` before each text scene, which makes it a clean hook point. Sheet: `font_sheet.png`. **[runtime]**
- **Printer 1:$4324** (bank-0 callers at $0401, $04EA and $053B; `de` = VRAM address of the line start):
  1. Per character it waits 8 frames. Holding A makes it 1 frame (`rst $10` frame wait, `$FFFA` bit 0).
  2. It reads a char and peeks for 7C/7D, then stores char/diacritic in $D88C/$D88D and the address in $D88A/B. It sets $D81F bit 6 and queues SFX $8E via $3DCE (a sound queue).
  3. The VBlank writer **$0CDE** writes the char at [$D88A], the diacritic (or 00) at [$D88A]-$20, and increments only the low byte of $D88A. It runs at LY=145. **[runtime]**
  4. FF -> next line (de += $40). FF FF -> return. The caller then waits for A ($0A0B) and handles pages.
- 1:$41F0 is the same printer without the A speed-up (rival scene).
- **Graphics codec** (bank0 $3B7E by id, or $3B9D with hl/de/bank already set). The table at $3DE5 holds 29 records `[bank][src][dst]`. Header: `type, blocks(16), ctl_offset(16)`. Block = 16<<(type&F) bytes. The per-block 2-bit mode (1-bit if type&F==0) selects zero / bitmask-literal / bitmask + row-XOR (bitplane delta) / raw or running-XOR. Implemented in `gfxdec.py`; matches VRAM **[runtime]**.
  - Boss portraits/names are in banks 0E/0F (tables at $4000, bank-relative offsets).
  - Stage tiles are in bank 8 ($4000 table).
- **Graphics-text inventory:**
  - Title (tileset #00, bank 4 $4000, compressed): `tsurugiisamidensetsu` banner and YAIBA logo. It also contains an **8x8 Latin font A-Z, 0-9, = × `.` / © h ^**, used for PUSH START and the © lines. Useful as a base for an English font.
  - Chapter card: `dai` and `shou` are in tileset #08 (bank 4 $554A, compressed). The numerals `hifumi`… are raw 2x2 tiles in **bank 7 $4080-$40AF** (uncompressed; selected by chapter_intro header byte 2). Bank 7 $46A0-$4BFF holds more 2-tile-wide kanji (last-chapter title?) **[guess]**.
  - Sword select (map #0F + tileset #0E, bank 4 $5D5B, compressed): kanji `raifuuryuuhaan` drawn into a 12x4 canvas (tiles 04-3F overwritten at runtime **[guess]**). The colon is tile DB.
  - HUD labels `inochi` / `kiai`: raw 3x3 tiles at **bank 2 $4D00-$4D8F** (uncompressed). Map #10 -> $9C00. **[runtime]**
  - Game over (map #18 + tileset #17, bank 4 $73F7, compressed): "GAME OVER" (already English), `konteinyuu` ×, `geemuwoyameru`.
  - Boss intro cards: names are already romaji (GANSEKI SOLDIER … ONIMARU) as compressed tile art in banks 0E/0F. Translating them (e.g. SUGI KAFUN) means redrawing tiles and re-compressing them into relocated space.
  - Bank 7 $4C00-$4CFF holds a hex 0-F font, probably debug **[guess]**.
  - Inventory PNGs are in `gfx_inventory/`.

## 5. VWF feasibility
**Verdict: feasible.** The plan:
1. **Tiles.** In every dialogue scene the BG uses only 00 (blank), the text codes, and 80-FF (frame and portrait). The font area 01-7F (127 tiles) is therefore free while a box is shown. A 12x8 canvas needs 96 tiles; chapter_end at 14x8 needs 112. **[runtime]**, from tilemap dumps of the chapter card scene.
2. **Hook the page start.** At the first char of each page, fill the box tilemap with sequential canvas codes. This can be done through a VRAM script; the interpreter $0CC1 already exists.
3. **Hook 1:$4324 and 1:$41F0.** Instead of storing a char code, compose the glyph into a 2-tile WRAM buffer (shift by pen_x&7, OR across the boundary). Write the buffer pointer and the VRAM tile address into $D88A-D, then set $D81F bit 6 as now.
4. **Replace the VBlank writer $0CDE.** Copy 32 bytes (2 tiles) from WRAM to VRAM, about 200 M-cycles unrolled. It already runs at LY 145, and VBlank has about 1,100 M-cycles. Typing speed is at most 1 char per frame (A held), so one 2-tile flush per VBlank is always enough.
5. **Use all 8 rows.** Diacritic rows are not needed in English, so line advance can become $20, giving **8 lines x 96 px**. That is about 160 characters per box, versus 48 kana. Alternatively keep 4 lines with 16 px spacing (about 80 characters).
6. **Space.** Code goes in the bank-1 tail or bank 0 $3E76-$3FFF (394 bytes). The widths table and VWF font can go into bank 2 $789E-$7C04 (871 bytes) or a new 512 KB bank.
7. **Menus, intro, sword and orb names** stay on the fixed 8x8 font: replace the kana tiles at bank 2 $4000 with an English 8x8 font. The title-screen Latin font is a starting point. Scenes that need it reload it, because $0A13 runs per scene.

**Fallback without VWF (2-byte patch):**
- 1:$4366 `add a,$40` -> `$20` (and the same at 1:$4227), so line advance is 1 row.
- NOP `ld (hl),a` at $0CED so the diacritic clear no longer wipes the line above.
- Result: 8 lines x 12 (or 14) chars with an 8x8 English font. **[static, untested]**

## 6. Free space (runs >= 64 bytes, `freespace.txt`)
- Bank 1: 77F0-7BFF (1,039 bytes) and 7C40-7FFF (960) are the zero-filled tail. insert.py uses both. 7C00-7C3F is a 0x52 fill and is kept.
- Bank 1 also has 48D7-4FFF (about 1,830 zeros after the end of code). It sits before 256-aligned tables at $5000+, so it is probably free **[guess]**. The other interior zero runs at 50CC-6005 are inside aligned tables; do not use them.
- Bank 0: 3E76-3FFF (394). Bank 2: 789E-7C04 (871), 69F6-6C04 (527), plus smaller runs.
- FF tails: bank 3 7535-7FFF (2,763), bank 5 5492-7FFF (11,118), bank 8 7E0C (500), bank 9 6C59 (5,031), bank 0A 7E31 (463), bank 0B 79A2 (1,630), bank 0D 58A2 (10,078), bank 0E 73A1 (3,167), bank 0F 6DC6 (4,666).
- Bank 0C 7119-7FFF (3,815) is zeros, probably free **[guess]**.
- **512 KB: yes.** MBC1 supports it, and the game writes full bank numbers to $2100.
  - `--expand` builds boot and display the same as the 256 KB build.
  - With the intro tilemap moved to **bank $1F** and its $3DE5 record repointed, the intro renders identically. **[runtime]**

## 7. Render test
`render_test/dialog_before.png` / `dialog_after.png` / `*_before_after.png`. The first chapter-1 line was replaced, same length, with `tesutotesuto`012345. The intro line became `tesuto`0123456789, which went through tilemap re-compression and relocation. Both render correctly. **[runtime]**
The font has no Latin glyphs, so no Latin test was possible.

## 8. Open items
- Read-coverage of the free runs (bank 1 48D7-4FFF, bank 0C) has not been verified.
- The pause menu (if any) was not seen. Start during the stage did not open a menu in the test run.
- The sword-select kanji canvas source (0A6F calls into bank 7) is unproven.
- The scenes for the 11 chapter_end entries (index = $D810 chapter) were only checked for entry 2 (forced via PC=$04AC).
