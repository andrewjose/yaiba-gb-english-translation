# rendermap.py map.bin tiles8800.bin out.png rom.gb  - signed tile mode, font from ROM bank2 for codes<0x80
import sys
from PIL import Image
m=open(sys.argv[1],'rb').read(); ts=open(sys.argv[2],'rb').read(); out=sys.argv[3]
rom=open(sys.argv[4],'rb').read(); font=rom[0x8000:0x8800]
rows=len(m)//32
img=Image.new('L',(256,rows*8))
for r in range(rows):
    for c in range(32):
        code=m[r*32+c]
        t=font[code*16:code*16+16] if code<0x80 else ts[(code-0x80)*16:(code-0x80)*16+16]
        for y in range(8):
            lo,hi=t[y*2],t[y*2+1]
            for x in range(8):
                v=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
                img.putpixel((c*8+x,r*8+y),255-v*85)
img.resize((512,rows*16)).save(out)
