# Pure functions that turn original graphics data into the English versions.
# All take/return bytes; no ROM I/O here (build_gfx.py does that).
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from gbgfx import tile_px,px_tile
from glyphs import BIG,HUD,SMALL,width,draw

def toff(code):            # signed tile mode, tileset loaded at $8800 (4 KB)
    return (code-0x80)*16 if code>=0x80 else 0x800+code*16

def render(t,m,r0,r1,c0,c1,tilefn=None):
    tf=tilefn or (lambda c:t[toff(c):toff(c)+16])
    px=[[0]*((c1-c0)*8) for _ in range((r1-r0)*8)]
    for r in range(r0,r1):
        for c in range(c0,c1):
            p=tile_px(tf(m[r*32+c]),0)
            for y in range(8):
                for x in range(8): px[(r-r0)*8+y][(c-c0)*8+x]=p[y][x]
    return px

def writeback(t,m,px,r0,r1,c0,c1,vis_rows=18):
    """write edited pixels back into the tiles the map uses; a changed tile must be used once on screen"""
    t=bytearray(t)
    uses={}
    for r in range(vis_rows):
        for c in range(20): uses[m[r*32+c]]=uses.get(m[r*32+c],0)+1
    for r in range(r0,r1):
        for c in range(c0,c1):
            code=m[r*32+c]
            nb=px_tile([row[(c-c0)*8:(c-c0)*8+8] for row in px[(r-r0)*8:(r-r0)*8+8]])
            o=toff(code)
            if bytes(t[o:o+16])!=nb:
                assert uses[code]==1,'tile %02x used %d times'%(code,uses[code])
                t[o:o+16]=nb
    return bytes(t)

def shadow(px,ink,dx,dy,color,bg):
    for (x,y) in ink:
        X,Y=x+dx,y+dy
        if 0<=Y<len(px) and 0<=X<len(px[0]) and (X,Y) not in ink and px[Y][X] in bg: px[Y][X]=color

# ---------------------------------------------------------------- title (#00 tiles, #01 map)
TITLE_TEXT='SAMURAI LEGEND'
def title(t00,m01):
    r0,r1,c0,c1=1,4,0,20
    px=render(t00,m01,r0,r1,c0,c1)
    # banner: black bar x21..143, y11..24 (screen); kanji are white (0) pixels inside it
    for y in range(12,25):
        for x in range(22,143):
            if px[y-8][x]==0: px[y-8][x]=3
    w=width(BIG,TITLE_TEXT,gap=1,space=4)
    x0=22+(121-w)//2
    draw(px,BIG,TITLE_TEXT,x0,13-8,0,gap=1,space=4)
    return writeback(t00,m01,px,r0,r1,c0,c1)

# ---------------------------------------------------------------- chapter card (#08 tiles, #09 map, bank 7 numerals)
CARD_FREE=[0x87,0x88,0x97,0x98,0xa5,0xa6,0xa7,0xa8,0xb5,0xb6,0xb7,0xb8,0xe6,0xe7,0xf6,0xf7,0xe8,0xe9,0xf8,0xf9]
GRAY=0x99
def card_map(m09):
    m=bytearray(m09)
    def put(r,c,old,new):
        assert m[r*32+c]==old,(r,c,hex(m[r*32+c]),hex(old)); m[r*32+c]=new
    # remove circle 1 (cols 4-7) and circle 2 (cols 8-11); circle 3 (cols 12-15) shows the numeral
    for c,o in ((5,0xea),(6,0xeb),(9,0xea),(10,0xeb)): put(2,c,o,GRAY)
    for c,o in ((4,0xec),(5,0xe6),(6,0xe7),(7,0xed),(8,0xec),(9,0x85),(10,0x86),(11,0xed)): put(3,c,o,GRAY)
    for c,o in ((4,0xfc),(5,0xf6),(6,0xf7),(7,0xfd),(8,0xfc),(9,0x95),(10,0x96),(11,0xfd)): put(4,c,o,GRAY)
    for c,o in ((5,0xfa),(6,0xfb),(9,0xfa),(10,0xfb)): put(5,c,o,GRAY)
    put(3,13,0xe8,0x85); put(3,14,0xe9,0x86); put(4,13,0xf8,0x95); put(4,14,0xf9,0x96)
    return bytes(m)

def card(t08,m09):
    m=bytearray(card_map(m09)); t=bytearray(t08)
    for code in CARD_FREE: t[toff(code):toff(code)+16]=bytes(16)
    r0,r1,c0,c1=3,5,1,12
    px=render(t,m,r0,r1,c0,c1)
    word='CHAPTER'
    w=width(BIG,word)
    x0=(c1-c0)*8-w-6          # right part of the band, 6 px before the numeral circle
    y0=3
    # 1 px white outline, light-gray body shadow, black letters
    tmp=[[None]*len(px[0]) for _ in px]
    ink=draw(tmp,BIG,word,x0,y0,3)
    for (x,y) in ink:
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                X,Y=x+dx,y+dy
                if (X,Y) not in ink: px[Y][X]=0
    for (x,y) in ink:
        X,Y=x+1,y+1
        if (X,Y) not in ink: px[Y][X]=2
        for dx,dy in ((2,1),(1,2),(2,2)):
            X,Y=x+dx,y+dy
            if (X,Y) not in ink and 0<=Y<len(px) and px[Y][X]!=2 and not any((X+a,Y+b) in ink for a in (-1,0,1) for b in (-1,0,1)): pass
    for (x,y) in ink: px[y][x]=3
    # allocate free tiles to cells that differ from plain gray
    gray=bytes(t[toff(GRAY):toff(GRAY)+16]); free=list(CARD_FREE)
    for r in range(r0,r1):
        for c in range(c0,c1):
            nb=px_tile([row[(c-c0)*8:(c-c0)*8+8] for row in px[(r-r0)*8:(r-r0)*8+8]])
            if nb==gray: continue
            assert m[r*32+c]==GRAY,(r,c)
            code=free.pop(0); t[toff(code):toff(code)+16]=nb; m[r*32+c]=code
    return bytes(t),bytes(m),len(CARD_FREE)-len(free)

def numerals(b7):
    """bank 7 tiles: numeral k (0..8 = 1..9) is a 2x2 block at tiles base,base+1,base+16,base+17,
    base = 0x80+2k for k<8, 0xA0 for k=8. Returns new bank-7 bytes (first $1000)."""
    b=bytearray(b7)
    bases=[0x80+2*k for k in range(8)]+[0xa0]
    def get(base):
        px=[[0]*16 for _ in range(16)]
        for i,(tx,ty) in enumerate(((0,0),(1,0),(0,1),(1,1))):
            p=tile_px(b,base+tx+16*ty)
            for y in range(8):
                for x in range(8): px[ty*8+y][tx*8+x]=p[y][x]
        return px
    def put(base,px):
        for (tx,ty) in ((0,0),(1,0),(0,1),(1,1)):
            o=(base+tx+16*ty)*16
            b[o:o+16]=px_tile([row[tx*8:tx*8+8] for row in px[ty*8:ty*8+8]])
    # background of the circle interior = per-pixel mode across the nine kanji (strokes differ, shading doesn't)
    all_px=[get(bs) for bs in bases]
    bg=[[0]*16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            vals=[p[y][x] for p in all_px]; bg[y][x]=max(set(vals),key=vals.count)
            if bg[y][x]==3: bg[y][x]=0
    for k,bs in enumerate(bases):
        px=[row[:] for row in bg]
        ch=str(k+1); w=len(BIG[ch][0])
        x0=(16-w+1)//2; y0=3
        tmp=[[0]*16 for _ in range(16)]
        ink=draw(tmp,BIG,ch,x0,y0,3)
        shadow(px,ink,1,1,2,(0,1))
        for (x,y) in ink: px[y][x]=3
        put(bs,px)
    return bytes(b)

# ---------------------------------------------------------------- orb icons (2x2 "kanji" tiles)
ORB_LABELS=['T','W','St','Ov','Dk']   # orb level 1-5: rai Thunder, fuu Wind, fuurai Storm, ha Overlord, an Dark
def orb_block(orig_px,label):
    """orig_px 16x16 of a kanji tile block; keep its background colour, redraw the label centred"""
    vals=[v for row in orig_px for v in row if v!=3]
    bgc=max(set(vals),key=vals.count)
    px=[[bgc]*16 for _ in range(16)]
    w=width(BIG,label); x0=(16-w+1)//2; y0=3
    if label=='Dk': y0=3
    tmp=[[0]*16 for _ in range(16)]
    ink=draw(tmp,BIG,label,x0,y0,3)
    for (x,y) in ink: px[y][x]=3
    return px

def orb_tiles(data,codes_tl,labels,tileoff):
    """codes_tl: list of top-left tile indices (block = tl,tl+1,tl+16,tl+17 in a 16-tile-wide layout)"""
    b=bytearray(data)
    for tl,lab in zip(codes_tl,labels):
        px=[[0]*16 for _ in range(16)]
        for (tx,ty) in ((0,0),(1,0),(0,1),(1,1)):
            p=tile_px(b,tileoff(tl+tx+16*ty))
            for y in range(8):
                for x in range(8): px[ty*8+y][tx*8+x]=p[y][x]
        npx=orb_block(px,lab)
        for (tx,ty) in ((0,0),(1,0),(0,1),(1,1)):
            o=tileoff(tl+tx+16*ty)*16
            b[o:o+16]=px_tile([row[tx*8:tx*8+8] for row in npx[ty*8:ty*8+8]])
    return bytes(b)

# ---------------------------------------------------------------- HUD (bank 2 $4D00, tiles d0-d8 as 3x3)
def hud(raw9):
    """raw9: 9 tiles (144 bytes) laid out 3x3 (d0 d1 d2 / d3 d4 d5 / d6 d7 d8)"""
    px=[[0]*24 for _ in range(24)]
    for i in range(9):
        p=tile_px(raw9,i)
        for y in range(8):
            for x in range(8): px[(i//3)*8+y][(i%3)*8+x]=p[y][x]
    for y in range(0,23):
        for x in range(24): px[y][x]=1          # light-gray HUD background; row 23 = frame line stays
    for word,y0 in (('LIFE',0),('KI',11)):
        tmp=[[0]*24 for _ in range(24)]
        ink=draw(tmp,HUD,word,1,y0,3)
        shadow(px,ink,-1,1,2,(1,))
        for (x,y) in ink: px[y][x]=3
    out=bytearray()
    for i in range(9): out+=px_tile([row[(i%3)*8:(i%3)*8+8] for row in px[(i//3)*8:(i//3)*8+8]])
    return bytes(out)

# ---------------------------------------------------------------- game over (#17 tiles, #18 map)
def gameover(t17,m18,t00):
    """CONTINUE (row 5, cols 5-13) / QUIT (row 7, cols 5-13); letters from the title-screen 8x8 Latin font
    (tileset #00, A-N = codes a2-af, O-Z = b2-bd), with the menu's dark-gray up-left shadow."""
    def latin(ch):
        code=(0xa2+ord(ch)-65) if ch<='N' else (0xb2+ord(ch)-ord('O'))
        return tile_px(t00,code-0x80)
    r0,r1,c0,c1=5,8,4,15
    m=m18
    px=render(t17,m,r0,r1,c0,c1)
    for y in range(24):
        for x in range(8,88): px[y][x]=0        # cols 5-14 (exclude col 4)… col 14 is blank tile 80 anyway
    for word,row in (('CONTINUE',0),('QUIT',2)):
        ink=set()
        x=8+1
        for ch in word:
            g=latin(ch)
            for gy in range(8):
                for gx in range(8):
                    if g[gy][gx]==3: ink.add((x+gx,row*8+gy))
            x+=8
        # glyphs have an empty top row; shift ink so a 1-px up-left shadow fits
        for (X,Y) in ink: px[Y][X]=3
        shadow(px,ink,-1,-1,2,(0,))
    # only cols 5..13 (tiles bf/ce.. and f0..f8) + f9 (row 6 col 6) may change; tile 80 is the blank background
    return px

def gameover_apply(t17,m18,px):
    r0,r1,c0,c1=5,8,4,15
    m=bytearray(m18); t=bytearray(t17)
    # row 6 col 6 (dakuten of 'ge', tile f9) is not needed any more
    return writeback(t,m,px,r0,r1,c0,c1)

# ---------------------------------------------------------------- bank 7 dragon-orb 4x4 icon (tiles 48-4B,58-5B,68-6B,78-7B)
def dragon_icon(b7,label='Dr'):
    b=bytearray(b7)
    px=[[0]*32 for _ in range(32)]
    for ty in range(4):
        for tx in range(4):
            p=tile_px(b,0x48+ty*16+tx)
            for y in range(8):
                for x in range(8): px[ty*8+y][tx*8+x]=p[y][x]
    for y in range(8,24):
        for x in range(7,24):
            if px[y][x]==3: px[y][x]=1
    w=width(BIG,label); x0=16-(w+1)//2; y0=10
    tmp=[[0]*32 for _ in range(32)]
    ink=draw(tmp,BIG,label,x0,y0,3)
    for (x,y) in ink: px[y][x]=3
    for ty in range(4):
        for tx in range(4):
            o=(0x48+ty*16+tx)*16
            b[o:o+16]=px_tile([row[tx*8:tx*8+8] for row in px[ty*8:ty*8+8]])
    return bytes(b)

# ---------------------------------------------------------------- boss cards (banks 0E/0F, assets decompressed to $8800)
# name row = map #1C row 14, tile codes 01..14 (tileset offset $800+16*code), text right-aligned in 20 cells
BOSS_JP={(0xe,0):'GANSEKI SOLDIER',(0xe,1):'SUGI KAFUN SOLDIER',(0xe,2):'YUKI DARUMA SOLDIER',(0xe,3):'ARI SOLDIER',
         (0xe,4):'BUDOU SOLDIER',(0xe,5):'KINOKO SOLDIER',(0xe,6):'RUBY SOLDIER',(0xe,7):'MUKADE SOLDIER',
         (0xf,0):'SILVER',(0xf,1):'SAPPHIRE SOLDIER',(0xf,2):'DIAMOND SOLDIER',(0xf,3):'EMERALD SOLDIER',
         (0xf,4):'JEWEL',(0xf,5):'GOLD',(0xf,6):'ONIMARU'}
BOSS_EN={(0xe,0):'BOULDER SOLDIER',(0xe,1):'CEDAR POLLEN SOLDIER',(0xe,2):'SNOWMAN SOLDIER',(0xe,3):'ANT SOLDIER',
         (0xe,4):'GRAPE SOLDIER',(0xe,5):'MUSHROOM SOLDIER',(0xe,7):'CENTIPEDE SOLDIER'}
EXTRA={'C':[".@@@@@..","@@...@@.","@@......","@@......","@@......","@@...@@.",".@@@@@.."],
       'T':["@@@@@@..","..@@....","..@@....","..@@....","..@@....","..@@....","..@@...."]}
def boss_name_cells(d):
    return [d[0x800+c*16:0x800+c*16+16] for c in range(1,0x15)]
def boss_font(assets):
    """assets: {(bank,k): decompressed bytes}; returns {char: 16-byte tile}, asserting consistency"""
    f={' ':bytes(16)}
    for key,txt in BOSS_JP.items():
        cells=boss_name_cells(assets[key]); txt=txt.rjust(20)
        for ch,tb in zip(txt,cells):
            if ch in f: assert f[ch]==tb,(key,ch)
            else: f[ch]=tb
    for ch,rows in EXTRA.items():
        assert ch not in f
        px=[[0]*8]+[[3 if c=='@' else 0 for c in r] for r in rows]
        f[ch]=px_tile(px)
    return f
def boss_rename(d,font,txt):
    assert len(txt)<=20
    b=bytearray(d)
    for i,ch in enumerate(txt.rjust(20)):
        b[0x800+(i+1)*16:0x800+(i+2)*16]=font[ch]
    return bytes(b)

# ---------------------------------------------------------------- pickup orbs chikara / ki (bank 6, object tiles, 2x2 at tl, tl+1, tl+16, tl+17)
PICKUPS=[(0x2e,'K'),(0x2c,'P')]   # ki first: the template orb 0x2c must still be original     # chikara = power, ki
def pickup(raw,tl,label,frame_tl=0x2c):
    """frame_tl: the orb whose clean outline is used as the template for every pickup"""
    b=bytearray(raw)
    px=[[0]*16 for _ in range(16)]
    for (tx,ty) in ((0,0),(1,0),(0,1),(1,1)):
        p=tile_px(b,frame_tl+tx+16*ty)
        for y in range(8):
            for x in range(8): px[ty*8+y][tx*8+x]=p[y][x]
    for y in range(2,14):
        xs=[x for x in range(16) if px[y][x]!=0]
        for x in range(xs[0]+1,xs[-1]-1): px[y][x]=1
    tmp=[[0]*16 for _ in range(16)]
    ink=draw(tmp,SMALL,label,5,3,3)
    for (x,y) in ink: px[y][x]=3
    for (tx,ty) in ((0,0),(1,0),(0,1),(1,1)):
        o=(tl+tx+16*ty)*16
        b[o:o+16]=px_tile([row[tx*8:tx*8+8] for row in px[ty*8:ty*8+8]])
    return bytes(b)

# ---------------------------------------------------------------- power-up screen orb icons: bank 7 $6000, 5x5 blocks
# (tiles base+16*row+col), chosen by the powerup header byte (bank0 $051D-$052C: bank 7, d=$60, bc=$0505)
POWERUP_ICONS=[(0x50,'T'),(0x55,'W'),(0x5a,'St'),(0xa0,'Ov'),(0xa5,'Dk'),(0xaa,'Dr')]
def powerup_icons(b7_6000):
    b=bytearray(b7_6000)
    for base,label in POWERUP_ICONS:
        px=[[0]*40 for _ in range(40)]
        for ty in range(5):
            for tx in range(5):
                p=tile_px(b,base+ty*16+tx)
                for y in range(8):
                    for x in range(8): px[ty*8+y][tx*8+x]=p[y][x]
        for y in range(12,29):
            for x in range(11,28):
                if px[y][x]==3: px[y][x]=1
        w=width(BIG,label); x0=20-(w+1)//2; y0=14
        tmp=[[0]*40 for _ in range(40)]
        ink=draw(tmp,BIG,label,x0,y0,3)
        for (x,y) in ink: px[y][x]=3
        for ty in range(5):
            for tx in range(5):
                o=(base+ty*16+tx)*16
                b[o:o+16]=px_tile([row[tx*8:tx*8+8] for row in px[ty*8:ty*8+8]])
    return bytes(b)
