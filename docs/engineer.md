# How it works (for software engineers new to Game Boy hacking)

**The ROM and banking.** The cartridge is 256 KB, but the Game Boy CPU only sees 32 KB of it at a time:
a fixed 16 KB window (bank 0) plus a 16 KB window that the program switches between "banks" by writing
a number to the mapper chip (MBC1) - like paging in a memory-mapped file. We doubled the ROM to 512 KB
(one header byte) to get empty banks for English text, new code and redrawn graphics.

**Text encoding.** The game doesn't use ASCII or Shift-JIS; each text byte is simply the number of an
8x8 picture ("tile") in the font. A table file maps byte -> character, like a custom code page. Dakuten
marks (dakuten, the two small strokes that voice a kana) were separate bytes drawn on the row above, so every Japanese line used two screen rows.

**Pointers.** Messages are found through tables of 16-bit addresses (pointers). English is longer, so
the messages were rewritten into a new bank and every pointer (including some hard-coded in code) was
updated - like relinking after moving functions.

**Variable-width font (VWF).** The screen is a grid of 8x8 tiles, so by default every letter takes a full
cell, which makes English look spaced out. We replaced the game's "put character" routine with one that
draws each letter's pixels into a small bitmap buffer at a pixel position (like a canvas), then copies
the affected tiles to video memory during VBlank (the short window when the screen isn't being drawn).
English needs no dakuten row, so each box now holds 8 lines instead of 4.

**Line breaking.** A build script measures each word in pixels with the real font widths and picks line
breaks that keep lines even (minimal squared slack, like TeX), hyphenating only if a word can't fit.

**Graphics text.** Titles, chapter cards and icons are pictures, stored compressed. We reimplemented
the game's decompressor and wrote a matching compressor (verified byte-identical on every original asset),
redrew the images in English and stored them in a new bank, updating the asset table.

**Static menus.** Text that never changes (opening crawl, sword-select labels) is pre-rendered at build
time into tiles, so it gets proportional spacing without code changes; dynamic names on sword select are
pre-rendered per value and uploaded when the menu updates.

**Trade-offs.** Abbreviations only where a field is physically tiny (orb icons, 6-8 cell name fields).
Timing was verified in an emulator; real hardware is stricter about VBlank, so a flash-cart test is pending.
