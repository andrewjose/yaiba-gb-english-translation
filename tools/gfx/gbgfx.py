# shared helpers: 2bpp tile <-> pixel arrays, sheets, PNG I/O (4 shades, index 0 = white)
from PIL import Image
SH=[255,170,85,0]
def tile_px(data,t):
    o=t*16; px=[]
    for y in range(8):
        lo,hi=data[o+2*y],data[o+2*y+1]
        px.append([((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1) for x in range(8)])
    return px
def px_tile(px):
    out=bytearray()
    for y in range(8):
        lo=hi=0
        for x in range(8):
            c=px[y][x]; lo|=(c&1)<<(7-x); hi|=((c>>1)&1)<<(7-x)
        out+=bytes([lo,hi])
    return bytes(out)
def sheet(data,w=16,scale=1,grid=False):
    n=len(data)//16; h=(n+w-1)//w
    img=Image.new('L',(w*8,h*8),255)
    for t in range(n):
        p=tile_px(data,t)
        for y in range(8):
            for x in range(8): img.putpixel(((t%w)*8+x,(t//w)*8+y),SH[p[y][x]])
    img=img.resize((img.width*scale,img.height*scale),Image.NEAREST)
    return img
def render_map(tilemap,tiles_fn,w,h,stride=32):
    """tiles_fn(code)->16 bytes"""
    img=Image.new('L',(w*8,h*8))
    for r in range(h):
        for c in range(w):
            p=tile_px(tiles_fn(tilemap[r*stride+c]),0)
            for y in range(8):
                for x in range(8): img.putpixel((c*8+x,r*8+y),SH[p[y][x]])
    return img
def img_to_idx(img):
    """greyscale/RGB PNG -> 2D list of indices 0..3 (nearest shade)"""
    img=img.convert('L'); W,H=img.size
    return [[min(range(4),key=lambda i:abs(SH[i]-img.getpixel((x,y)))) for x in range(W)] for y in range(H)]
def idx_to_img(px,scale=1):
    H=len(px); W=len(px[0]); img=Image.new('L',(W,H))
    for y in range(H):
        for x in range(W): img.putpixel((x,y),SH[px[y][x]])
    return img.resize((W*scale,H*scale),Image.NEAREST)
def blit_tiles(px,ox,oy):
    """region of pixel grid -> bytes of tiles at tile coords"""
    return px_tile([row[ox*8:ox*8+8] for row in px[oy*8:oy*8+8]])
