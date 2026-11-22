# Yaiba GB - translation notes

73 entries in translation/en.json (joined with the extracted Japanese into build/work/tl/out_all.json at build time), 0 validator errors. Build: `python3 build.py --rom ...` at the repo root.

## Format
- JP page separator in strings.json is "\n<page>\n"; en uses "\n\n" as instructed. The inserter must map "\n\n" -> page break.
- chapter_end_03 / _05 keep one hard "\n" after the animal cry (as in JP layout).
- Heart symbol (JP ♥) dropped everywhere (ASCII only): chapter_end_03, _05, _09. Quotation brackets  dropped (no " in charset); names capitalized instead.

## Speakers (from portraits at bank 2 $5000, see portraits.png)
00 Sayaka, 05 young man (unidentified; neutral male voice used), 0a Yaiba, 50 Kagetora, 55 Shonosuke,
5a Jubei (eyepatch; matches "family art passed down"), a0 Musashi, a5 Geroda, aa young swordsman with archaic -de gozaru (unidentified; possibly Goemon or Kojiro).

## Uncertain readings
- `koryuurin` (orb_menu_07): kanji unknown (`toraryuuwa` / `koryuuwa`?). Rendered "Wyrm Ring".
- portrait 05 / aa speaker identity unconfirmed; lines written speaker-neutral.
- chapter_intro_08 `chikushou` softened to "Darn it".
- Intro crawl lines 13-17 and 20-24 restructured across lines to fit 17 cells ("girl" dropped from "mysterious girl Emerald" -> "enigmatic Emerald").

## Abbreviations (fixed 8x8 fields)
- Sword menu (6): Raijin (Raijinken), Fujin (Fujinken), Ankoku (Ankokuken), Dual (ryoutou), Haoken.
- Orb names (8): "Orb" dropped: Thunder, Dragon (= Dragon God Orb), Wind, Storm, Overlord, Dark.
- Moves: Lt.Slash (Lightning Slash, official), X-Slash (Cross Slash), DarkSlash (no space, 9 cells), Dark Wyrm (Black Dragon Spin).

## New names
All added to [glossary.md](glossary.md), marked as unofficial (translator's choice).
