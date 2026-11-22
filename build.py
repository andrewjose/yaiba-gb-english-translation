#!/usr/bin/env python3
"""Build the Yaiba GB English translation from your own copy of the original ROM.

usage: python3 build.py --rom "Kenyuu Densetsu Yaiba (Japan).gb" [--out build/] [--rgbds DIR]

Steps (all intermediate files go to <out>/work/):
  1. verify the ROM (MD5 7d76d2a9eaada93dc846efe1b2a815cc)
  2. tools/re/extract.py        -> work/re/strings.json (string table: pointers, headers, field sizes)
  3. tools/engine/mkfont.py     -> work/font/ (VWF + fixed 8x8 font; the fixed font starts from the ROM's font page)
  4. translation/en.json + extracted strings -> work/tl/out_all.json ([{id, jp, en}])
  5. tools/engine/build.py --gfx (text + VWF engine, then tools/gfx/build_gfx.py)
  6. <out>/yaiba_en.gb and <out>/yaiba_en.bps (tools/common/mkbps.py)
rgbds (rgbasm/rgblink/rgbfix) is taken from --rgbds, $RGBDS_DIR or PATH."""
import argparse, hashlib, json, os, shutil, subprocess, sys

REPO = os.path.dirname(os.path.abspath(__file__))
ROM_MD5 = '7d76d2a9eaada93dc846efe1b2a815cc'
TOOLS = os.path.join(REPO, 'tools')


def md5(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def run(args, env):
    print('+', ' '.join(os.path.relpath(x, REPO) if os.path.isabs(x) and x.startswith(REPO) else x for x in args), flush=True)
    subprocess.check_call([sys.executable, '-I'] + args, env=env, cwd=REPO)


def find_rgbds(opt):
    d = opt or os.environ.get('RGBDS_DIR', '')
    if d:
        missing = [t for t in ('rgbasm', 'rgblink', 'rgbfix') if not shutil.which(t, path=d)]
        if missing: sys.exit('rgbds: %s not found in %s' % (', '.join(missing), d))
        return os.path.abspath(d)
    missing = [t for t in ('rgbasm', 'rgblink', 'rgbfix') if not shutil.which(t)]
    if missing: sys.exit('rgbds: %s not on PATH (install rgbds or pass --rgbds DIR)' % ', '.join(missing))
    return ''


def merge(en_path, strings_path, out_path):
    S = json.load(open(strings_path, encoding='utf-8'))
    jp = {s['id']: s['jp'] for s in S}
    en = json.load(open(en_path, encoding='utf-8'))
    if isinstance(en, dict): en = [{'id': k, 'en': v} for k, v in en.items()]
    unknown = [e['id'] for e in en if e['id'] not in jp]
    if unknown: sys.exit('translation/en.json has ids not found in the ROM: %s' % ', '.join(unknown))
    out = [{'id': e['id'], 'jp': jp[e['id']], 'en': e['en']} for e in en]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(out, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('merged %d translated strings (%d extracted) -> %s' % (len(out), len(S), os.path.relpath(out_path, REPO)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--rom', required=True, help='original Kenyuu Densetsu Yaiba (Japan).gb')
    ap.add_argument('--out', default=os.path.join(REPO, 'build'), help='output directory (default: build/)')
    ap.add_argument('--rgbds', help='directory containing rgbasm/rgblink/rgbfix (default: $RGBDS_DIR or PATH)')
    a = ap.parse_args()

    rom = os.path.abspath(a.rom)
    if not os.path.isfile(rom): sys.exit('ROM not found: %s' % rom)
    h = md5(rom)
    if h != ROM_MD5: sys.exit('ROM MD5 %s does not match the required %s (Kenyuu Densetsu Yaiba (Japan).gb)' % (h, ROM_MD5))
    print('ROM ok:', h)
    rgbds = find_rgbds(a.rgbds)

    out = os.path.abspath(a.out); work = os.path.join(out, 'work')
    os.makedirs(work, exist_ok=True)
    env = dict(os.environ, YAIBA_ROM=rom, YAIBA_WORK=work, YAIBA_FONT_DIR=os.path.join(work, 'font'),
               YAIBA_STRINGS=os.path.join(work, 're', 'strings.json'), RGBDS_DIR=rgbds)

    run([os.path.join(TOOLS, 're', 'extract.py'), rom, os.path.join(work, 're')], env)
    run([os.path.join(TOOLS, 'engine', 'mkfont.py'), '--rom', rom, '--out', os.path.join(work, 'font')], env)
    tl = os.path.join(work, 'tl', 'out_all.json')
    merge(os.path.join(REPO, 'translation', 'en.json'), os.path.join(work, 're', 'strings.json'), tl)
    text_gb = os.path.join(work, 'engine', 'yaiba_en.gb')
    run([os.path.join(TOOLS, 'engine', 'build.py'), '--rom', rom, '--tl', tl, '--out', text_gb, '--gfx'], env)

    final = os.path.join(out, 'yaiba_en.gb'); bps = os.path.join(out, 'yaiba_en.bps')
    shutil.copyfile(os.path.splitext(text_gb)[0] + '_full.gb', final)
    run([os.path.join(TOOLS, 'common', 'mkbps.py'), 'make', rom, final, bps], env)
    print('\n%s  %s\n%s  %s' % (md5(final), final, md5(bps), bps))


if __name__ == '__main__':
    main()
