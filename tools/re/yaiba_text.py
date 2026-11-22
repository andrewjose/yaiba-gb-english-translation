# Shared definitions for Yaiba text blocks (bank 1). All addresses are bank-1 CPU addresses ($4000-$7FFF).
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from tbl import decode, encode
BANK=1
def off(a): return BANK*0x4000+(a-0x4000)
def u16(r,o): return r[o]|r[o+1]<<8

# Dialogue blocks. kind: 'single' = one page (lines FF.. FF); 'multi' = pages, FF between pages, any non-FF ends.
# hdr = number of header bytes before text (portrait/graphic tile offsets, NOT text).
TABLES=[  # (block, table_addr, count, hdr, kind, printer/notes)
 ('chapter_intro',0x6b96,10,2,'single','bank0 $03CA; printed by 1:$4324 at $9947 (12 cols x 4 lines, dakuten row above each line); hdr=[portrait tile ofs (bank2 $5000+16*n, 5x5)] [chapter numeral tile ofs (bank7 $4000+16*n, 2x2)]'),
 ('chapter_end',0x6d90,11,1,'multi','bank0 $04C9; 1:$4324 at $9923; hdr=[portrait tile ofs]'),
]
DIRECT=[  # (block, [code locations of 'ld hl,nn' operand], addr, hdr, kind)
 ('rival',[0x4146],0x7088,0,'single'),
 ('rival',[0x415e],0x70b9,0,'single'),
 ('rival',[0x416c],0x70e3,0,'single'),
 ('rival',[0x4184],0x70ef,0,'single'),
 ('rival',[0x41be],0x710e,0,'single'),
 ('powerup',[0x4291],0x75eb,1,'multi'),
 ('powerup',[0x4306],0x760b,1,'multi'),
 ('powerup',[0x42e3],0x7662,1,'multi'),
 ('powerup',[0x4258],0x7685,1,'multi'),
 ('powerup',[0x426f],0x76ab,1,'multi'),
 ('powerup',[0x4282,0x42a9],0x76d1,1,'multi'),
 ('powerup',[0x42b8],0x772d,1,'multi'),
]
# packing regions for repacking dialogue (bank1 CPU addr ranges, end exclusive), in order
ORIG_REGIONS=[(0x6baa,0x6d90),(0x6da6,0x7123),(0x75eb,0x7754)]
FREE_REGIONS=[(0x77f0,0x7c00),(0x7c40,0x8000)]   # static: zero-filled bank-1 tail (7C00-7C3F is a $52 fill, kept)

def parse_dialogue(rom,addr,hdr,kind):
    """returns (header bytes, list of pages(list of line bytes), end_addr_exclusive_of_terminator)"""
    o=off(addr); h=rom[o:o+hdr]; o+=hdr; pages=[]
    while True:
        lines=[]
        while True:
            j=rom.index(0xff,o); lines.append(rom[o:j]); o=j+1
            if rom[o]==0xff: o+=1; break
        pages.append(lines)
        if kind=='multi' and rom[o]==0xff: o+=1; continue
        break
    return h,pages,o-off(0x4000)+0x4000  # CPU addr after page end (terminator is the next byte, not consumed)

def pages_to_text(pages):
    return '\n<page>\n'.join('\n'.join(decode(l) for l in p) for p in pages)
def text_to_pages(t):
    return [[encode(l) for l in p.split('\n')] for p in t.split('\n<page>\n')]
def serialize(h,pages,kind):
    out=bytearray(h)
    for i,p in enumerate(pages):
        if i: out.append(0xff)          # continue marker
        for l in p: out+=l; out.append(0xff)
        out.append(0xff)
    return bytes(out)

# VRAM-script menus: records = [hdr bytes] + script ([n][lo][hi][n bytes])* 00 ; interpreter bank0 $0CC1
MENUS=[('sword_menu',0x7227,6,3),('orb_menu',0x7301,10,0)]
def parse_script(rom,o):
    cmds=[]
    while rom[o]:
        n=rom[o]; a=u16(rom,o+1); cmds.append((o,n,a,rom[o+3:o+3+n])); o+=3+n
    return cmds,o

# compressed tilemaps containing font text: (block, gfx table index) - table bank0 $3DE5, 5-byte recs [bank][src][dst]
TILEMAPS=[('intro_scroll',0x07),('sword_select_screen',0x0f)]
