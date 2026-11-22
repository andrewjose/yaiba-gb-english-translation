# Kenyuu Densetsu Yaiba (Game Boy) - English fan translation

English translation of *Kenyuu Densetsu YAIBA* (Banpresto, 1994, Game Boy), the Pyramid-arc action game
based on Gosho Aoyama's *Yaiba*. Names follow the official English anime (*YAIBA: Samurai Legend*) and
Viz's English manga; terms without an official English form are marked in [docs/glossary.md](docs/glossary.md).

This repository holds **tools, English text and documentation only**. It contains no ROM and no game data.

## Features (v0.1)
- Every text system translated: chapter intros/endings, Onimaru scenes, power-ups, intro crawl, sword select.
- Variable-width font in all dialogue boxes (8 lines per box instead of 4), typewriter effect kept.
- Graphics redrawn: title banner, chapter cards, HUD, game over, boss cards, orb icons.
- ROM expanded to 512 KB (MBC1).

## Patch
Patches are published as release assets (BPS). Required source ROM:
`Kenyuu Densetsu Yaiba (Japan).gb` - CRC32 `CC19768E`, MD5 `7d76d2a9eaada93dc846efe1b2a815cc`.

## Building from source
Requirements: Python 3, Pillow, pyphen, rgbds (rgbasm/rgblink/rgbfix), and your own copy of the original ROM
(MD5 `7d76d2a9eaada93dc846efe1b2a815cc`). PyBoy is only needed for the screenshot/test harnesses.
```
python3 build.py --rom "Kenyuu Densetsu Yaiba (Japan).gb"            # rgbds on PATH
python3 build.py --rom orig.gb --out build/ --rgbds /path/to/rgbds   # or set RGBDS_DIR
```
Outputs: `build/yaiba_en.gb` and `build/yaiba_en.bps`; the script prints their MD5s. v0.1 builds to
MD5 `eabe8ecd55aa2cb289dacb0109c22291`. Intermediate files (extracted string table, generated fonts,
merged translation, engine build, maps/symbols) go to `build/work/`. Nothing from the ROM is stored in
this repository: the string table and the fixed font are regenerated from your ROM on every build.
Optional: `python3 tools/engine/typeset_check.py` after a build for a line-fit report and contact sheet.
Step-by-step details: [docs/technical/engine-notes.md](docs/technical/engine-notes.md).

## Documentation
- [Plain-language overview](docs/overview.md)
- [Engineer-level explanation](docs/engineer.md)
- Deep technical: [reverse engineering](docs/technical/re-notes.md), [engine/VWF](docs/technical/engine-notes.md), [graphics](docs/technical/graphics-notes.md)
- [Translation notes](docs/translation-notes.md), [glossary](docs/glossary.md), [changelog](CHANGELOG.md)
