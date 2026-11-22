# render 2bpp tiles from ROM as labeled sheet: fontsheet.py rom off ntiles out.png [base_code]
import sys
from PIL import Image, ImageDraw
rom=open(sys.argv[1],'rb').read(); off=int(sys.argv[2],0); n=int(sys.argv[3]); out=sys.argv[4]
base=int(sys.argv[5],0) if len(sys.argv)>5 else 0
S=3; cw=8*S+14
img=Image.new('RGB',(16*cw+14, ((n+15)//16)*cw+14),'white'); dr=ImageDraw.Draw(img)
for c in range(16): dr.text((14+c*cw+6,0),'%X'%c,fill='blue')
for t in range(n):
    x0=14+(t%16)*cw; y0=14+(t//16)*cw
    if t%16==0: dr.text((0,y0+6),'%X'%((base+t)>>4),fill='blue')
    for y in range(8):
        lo,hi=rom[off+t*16+y*2],rom[off+t*16+y*2+1]
        for x in range(8):
            c=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
            if c: dr.rectangle([x0+x*S,y0+y*S,x0+x*S+S-1,y0+y*S+S-1],fill=(255-c*85,)*3)
    dr.rectangle([x0-1,y0-1,x0+8*S,y0+8*S],outline=(220,220,220))
img.save(out)
