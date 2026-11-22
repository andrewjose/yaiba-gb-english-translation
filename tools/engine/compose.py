"""Precompose VWF text into 8x8 tiles at build time (static screens: intro crawl, sword select)."""
import os,json
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..')
VWF=open(os.path.join(ROOT,'font','vwf.bin'),'rb').read()
ADV=json.load(open(os.path.join(ROOT,'font','widths.json')))
def text_width(s): return max(0,sum(ADV[c] for c in s)-1) if s else 0
def render(s,ntiles,x0=0,align='left'):
    """returns list of ntiles 1bpp tiles (8 bytes each). x0: pixel offset (left) or right margin (right)."""
    W=ntiles*8; rows=[[0]*W for _ in range(8)]
    w=text_width(s)
    x=x0 if align=='left' else (W-x0-w if align=='right' else (W-w)//2)
    if x<0 or x+w>W: raise ValueError('%r (%d px) does not fit %d tiles'%(s,w,ntiles))
    for ch in s:
        g=VWF[(ord(ch)-32)*8:(ord(ch)-32)*8+8]
        for r in range(8):
            for b in range(8):
                if g[r]&(0x80>>b) and 0<=x+b<W: rows[r][x+b]=1
        x+=ADV[ch]
    tiles=[]
    for t in range(ntiles):
        tb=bytearray()
        for r in range(8):
            v=0
            for b in range(8): v|=rows[r][t*8+b]<<(7-b)
            tb.append(v)
        tiles.append(bytes(tb))
    return tiles
def to2bpp(t1): return bytes(b for v in t1 for b in (v,v))
