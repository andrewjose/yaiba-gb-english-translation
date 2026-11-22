"""Render a BG map from a live PyBoy VRAM (signed $8800 addressing as LCDC.4=0 in this game)."""
from PIL import Image
def tile_px(mem,code,signed=True):
    base=(0x9000+((code^0x80)-0x80)*16) if signed else 0x8000+code*16
    out=[]
    for y in range(8):
        lo,hi=mem[base+y*2],mem[base+y*2+1]
        out.append([((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1) for x in range(8)])
    return out
def render_map(pb,base=0x9c00,rows=32,cols=32,signed=True,scale=2):
    mem=pb.memory
    img=Image.new('L',(cols*8,rows*8))
    pal=[255,170,85,0]
    for r in range(rows):
        for c in range(cols):
            t=tile_px(mem,mem[base+r*32+c],signed)
            for y in range(8):
                for x in range(8): img.putpixel((c*8+x,r*8+y),pal[t[y][x]])
    return img.resize((cols*8*scale,rows*8*scale),Image.NEAREST)
