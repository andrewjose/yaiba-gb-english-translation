"""Draws the Yaiba English fonts (original pixel art, no third-party font data).
VWF metrics (8 px cell): cap height 6 (rows 0-5), x-height 4 (rows 2-5), baseline under row 5,
descenders rows 6-7. Advance = ink width + 1 (1 px right bearing). Space advance 3.
Outputs (work/engine/font/):
  vwf.bin     95 glyphs x 8 bytes, 1bpp, MSB = leftmost pixel, ASCII 0x20-0x7E
  widths.bin  95 advances (bytes)
  widths.json {char: advance}  (used by build.py / typeset_check.py)
  fixed.bin   128 x 16 bytes 2bpp tiles: the fixed 8x8 font loaded to VRAM $9000 by $0A13
  fixed8.tbl  tile code table for the fixed font
  font_vwf.png / font_fixed.png  glyph sheets (x4)"""
import os,json,sys
from PIL import Image,ImageDraw
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'..','font')
ORIG='/root/gbtl/yaiba/orig/Kenyuu Densetsu Yaiba (Japan).gb'
G={}
def g(ch,rows,top=0):
    """rows: list of strings ('#' ink), placed starting at row `top`."""
    w=max(len(r) for r in rows) if rows else 0
    bm=['']*8
    full=['.'*w]*8
    for i,r in enumerate(rows): full[top+i]=r.ljust(w,'.')
    G[ch]=(w,full)
U=lambda ch,*r:g(ch,list(r),0)          # caps/digits/ascenders: rows from 0
X=lambda ch,*r:g(ch,list(r),2)          # x-height glyphs: rows from 2
U('A','.##.','#..#','#..#','####','#..#','#..#')
U('B','###.','#..#','###.','#..#','#..#','###.')
U('C','.##.','#..#','#...','#...','#..#','.##.')
U('D','###.','#..#','#..#','#..#','#..#','###.')
U('E','####','#...','###.','#...','#...','####')
U('F','####','#...','###.','#...','#...','#...')
U('G','.##.','#..#','#...','#.##','#..#','.###')
U('H','#..#','#..#','####','#..#','#..#','#..#')
U('I','###','.#.','.#.','.#.','.#.','###')
U('J','...#','...#','...#','...#','#..#','.##.')
U('K','#..#','#.#.','##..','#.#.','#..#','#..#')
U('L','#...','#...','#...','#...','#...','####')
U('M','#...#','##.##','#.#.#','#.#.#','#...#','#...#')
U('N','#...#','##..#','#.#.#','#..##','#...#','#...#')
U('O','.##.','#..#','#..#','#..#','#..#','.##.')
U('P','###.','#..#','#..#','###.','#...','#...')
U('Q','.##.','#..#','#..#','#..#','#..#','.##.','...#')
U('R','###.','#..#','#..#','###.','#.#.','#..#')
U('S','.###','#...','.##.','...#','...#','###.')
U('T','#####','..#..','..#..','..#..','..#..','..#..')
U('U','#..#','#..#','#..#','#..#','#..#','.##.')
U('V','#...#','#...#','#...#','.#.#.','.#.#.','..#..')
U('W','#...#','#...#','#.#.#','#.#.#','##.##','#...#')
U('X','#...#','.#.#.','..#..','..#..','.#.#.','#...#')
U('Y','#...#','#...#','.#.#.','..#..','..#..','..#..')
U('Z','####','...#','..#.','.#..','#...','####')
X('a','.###','#..#','#..#','.###')
U('b','#...','#...','###.','#..#','#..#','###.')
X('c','.##','#..','#..','.##')
U('d','...#','...#','.###','#..#','#..#','.###')
X('e','.##.','####','#...','.###')
U('f','.##','#..','###','#..','#..','#..')
X('g','.###','#..#','#..#','.###','...#','.##.')
U('h','#...','#...','###.','#..#','#..#','#..#')
U('i','#','.','#','#','#','#')
U('j','.#','..','.#','.#','.#','.#','.#','#.')
U('k','#...','#...','#.#.','##..','#.#.','#..#')
U('l','#','#','#','#','#','#')
X('m','####.','#.#.#','#.#.#','#.#.#')
X('n','###.','#..#','#..#','#..#')
X('o','.##.','#..#','#..#','.##.')
X('p','###.','#..#','#..#','###.','#...','#...')
X('q','.###','#..#','#..#','.###','...#','...#')
X('r','#.#','##.','#..','#..')
X('s','.###','##..','..##','###.')
U('t','...','#..','###','#..','#..','.##')
X('u','#..#','#..#','#..#','.###')
X('v','#...#','#...#','.#.#.','..#..')
X('w','#...#','#.#.#','#.#.#','.#.#.')
X('x','#..#','.##.','.##.','#..#')
X('y','#..#','#..#','#..#','.###','...#','.##.')
X('z','####','..#.','.#..','####')
U('0','.##.','#..#','#.##','##.#','#..#','.##.')
U('1','.#.','##.','.#.','.#.','.#.','###')
U('2','.##.','#..#','...#','..#.','.#..','####')
U('3','###.','...#','.##.','...#','...#','###.')
U('4','..#.','.##.','#.#.','####','..#.','..#.')
U('5','####','#...','###.','...#','...#','###.')
U('6','.##.','#...','###.','#..#','#..#','.##.')
U('7','####','...#','..#.','.#..','.#..','.#..')
U('8','.##.','#..#','.##.','#..#','#..#','.##.')
U('9','.##.','#..#','#..#','.###','...#','.##.')
G[' ']=(2,['..']*8)
U('!','#','#','#','#','.','#')
U('?','.##.','#..#','..#.','.#..','....','.#..')
U('.','.','.','.','.','.','#')
U(',','..','..','..','..','..','.#','#.')
U("'",'#','#')
U('"','#.#','#.#')
U('-','...','...','...','###')
U(':','.','.','#','.','.','#')
U(';','..','..','.#','..','..','.#','#.')
U('(','.#','#.','#.','#.','#.','.#')
U(')','#.','.#','.#','.#','.#','#.')
U('[','##','#.','#.','#.','#.','##')
U(']','##','.#','.#','.#','.#','##')
U('/','...#','..#.','..#.','.#..','.#..','#...')
U('\\','#...','.#..','.#..','..#.','..#.','...#')
U('&','.#...','#.#..','.#...','#.#.#','#..#.','.##.#')
U('+','...','...','.#.','###','.#.')
U('=','...','...','###','...','###')
U('*','...','#.#','.#.','#.#')
U('<','...','..#','.#.','#..','.#.','..#')
U('>','...','#..','.#.','..#','.#.','#..')
U('_','....','....','....','....','....','....','####')
U('#','.#.#.','#####','.#.#.','#####','.#.#.')
U('%','#...#','...#.','..#..','.#...','#...#')
U('$','.###','#.#.','.##.','..##','###.','.#..')
U('@','.##.','#..#','#.##','#.##','#...','.##.')
U('^','.#.','#.#')
U('`','#.','.#')
U('{','.#','.#','#.','.#','.#')   # repurposed? keep simple
U('|','#','#','#','#','#','#','#')
U('}','#.','#.','.#','#.','#.')
U('~','.#.#','#.#.')   # tilde
ASCII=[chr(c) for c in range(0x20,0x7f)]
missing=[c for c in ASCII if c not in G]
assert not missing,missing
def rowbits(r): 
    v=0
    for i,ch in enumerate(r):
        if ch=='#': v|=0x80>>i
    return v
vwf=bytearray(); widths=bytearray()
for c in ASCII:
    w,rows=G[c]
    for r in rows: vwf.append(rowbits(r))
    widths.append(w+1 if c!=' ' else 3)
os.makedirs(OUT,exist_ok=True)
open(os.path.join(OUT,'vwf.bin'),'wb').write(vwf)
open(os.path.join(OUT,'widths.bin'),'wb').write(widths)
json.dump({c:widths[i] for i,c in enumerate(ASCII)},open(os.path.join(OUT,'widths.json'),'w'),indent=0)
# ---- glyph sheet (real advances)
S=4
img=Image.new('RGB',(16*10*S,6*12*S),(255,255,255)); d=ImageDraw.Draw(img)
for i,c in enumerate(ASCII):
    cx,cy=(i%16)*10*S,(i//16)*12*S
    w,rows=G[c]
    d.rectangle([cx,cy,cx+widths[i]*S-1,cy+8*S-1],fill=(230,230,255))
    for y,r in enumerate(rows):
        for x,ch in enumerate(r):
            if ch=='#': d.rectangle([cx+x*S,cy+y*S,cx+x*S+S-1,cy+y*S+S-1],fill=(0,0,0))
    d.line([cx,cy+6*S,cx+8*S,cy+6*S],fill=(255,120,120))
img.save(os.path.join(OUT,'font_vwf.png'))
# ---- fixed 8x8 font: original font with Latin glyphs in the kana slots
rom=open(ORIG,'rb').read(); fixed=bytearray(rom[0x8000:0x8800])
# Layout constraints (runtime/static, see NOTES.md): digits stay at 40-49 (game over "xn" = $40+n);
# sword select copies bank 2 $4400-$47FF (codes 40-7F) only, so every glyph used by sword/orb names
# and the sword-select labels must sit in 40-7F. Uppercase letters never used there go low (0A-0F).
FIX={0x00:' '}
for i in range(26): FIX[0x4a+i]=chr(97+i)
for i,c in enumerate('ABCDEFHIJLMOPQRSTWXY'): FIX[0x64+i]=c
for i,c in enumerate(".-,':/"): FIX[0x78+i]=c
FIX[0x7e]='!'; FIX[0x7f]='?'
for i,c in enumerate('GKNUVZ'): FIX[0x0a+i]=c
for i,c in enumerate('"();&+='): FIX[0x10+i]=c
DUP={2:[],3:[1],4:[1,2],5:[1,3]}   # interior columns duplicated for the wider fixed-pitch font
DUP_CH={'I':[0,2],'1':[]}   # keep 1 px stems
def widen(w,rows,ch=None):
    d=DUP_CH.get(ch,DUP.get(w,[]))
    out=[]
    for r in rows:
        n=''
        for i,ch in enumerate(r.ljust(w,'.')):
            n+=ch*(2 if i in d else 1)
        out.append(n)
    return w+len(d),out
def tile8(c):
    w,rows=widen(*G[c],ch=c) if c.isalnum() else G[c]; ox=(8-w)//2 if w<8 else 0
    t=bytearray()
    for r in rows:
        v=rowbits(r)>>ox; t+=bytes([v,v])
    return t
for code,c in FIX.items(): fixed[code*16:code*16+16]=tile8(c)
open(os.path.join(OUT,'fixed.bin'),'wb').write(fixed)
with open(os.path.join(OUT,'fixed8.tbl'),'w',encoding='utf-8') as f:
    f.write('# Yaiba English fixed 8x8 font: ROM bank 2 $4000-$47FF (loaded to VRAM $9000 by $0A13; sword select copies 40-7F)\n')
    f.write('# 01-03,08,09 box/cursor gfx; 40-49 = original digits 0-9; 3F = original heart\n')
    for code in sorted(FIX): f.write('%02X=%s\n'%(code,FIX[code]))
    for i in range(10): f.write('%02X=%d\n'%(0x40+i,i))
    f.write('3F=♥\n')
im=Image.new('L',(16*9,8*9),200)
for t in range(128):
    for y in range(8):
        lo,hi=fixed[t*16+y*2],fixed[t*16+y*2+1]
        for x in range(8):
            c=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
            im.putpixel(((t%16)*9+x,(t//16)*9+y),255-c*85)
im.resize((im.width*4,im.height*4),Image.NEAREST).save(os.path.join(OUT,'font_fixed.png'))
print('glyphs',len(ASCII),'vwf bytes',len(vwf))
