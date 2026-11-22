# decompress every known compressed asset and render tile sheets into tmp/gfx/
import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from gfxdec import decompress, entries
from PIL import Image
rom=open(sys.argv[1],'rb').read(); od=sys.argv[2]; os.makedirs(od,exist_ok=True)
def sheet(data,out,w=16):
    n=len(data)//16; h=(n+w-1)//w
    img=Image.new('L',(w*8,h*8),255)
    for t in range(n):
        for y in range(8):
            lo,hi=data[t*16+y*2],data[t*16+y*2+1]
            for x in range(8):
                c=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
                img.putpixel(((t%w)*8+x,(t//w)*8+y),255-c*85)
    img.resize((img.width*2,img.height*2)).save(out)
assets=[]
for i,b,s,dst in entries(rom)[:0x1d]: assets.append(('t%02x'%i,b,s,dst))
for bank in (8,0xe,0xf):
    base=bank*0x4000
    first=rom[base]|rom[base+1]<<8; n=first//2
    for k in range(n):
        rel=rom[base+2*k]|rom[base+2*k+1]<<8
        assets.append(('b%02x_%02d'%(bank,k),bank,0x4000+rel,0))
for name,b,s,dst in assets:
    try: data,cl=decompress(rom,b,s)
    except Exception as e: print(name,'ERR',e); continue
    print(name,'bank %02x src %04x off %05x dst %04x out %d comp %d'%(b,s,b*0x4000+s-0x4000,dst,len(data),cl))
    open(f'{od}/{name}.bin','wb').write(data)
    if dst in (0x9800,0x9c00): continue
    sheet(data,f'{od}/{name}.png')
