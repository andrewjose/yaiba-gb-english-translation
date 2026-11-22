# inspect_state.py rom state outprefix [frames] [frame:btn..]: screenshot x4, vram sheet, bg maps print
import sys
from pyboy import PyBoy
from PIL import Image
rom,st,out=sys.argv[1],sys.argv[2],sys.argv[3]
frames=int(sys.argv[4]) if len(sys.argv)>4 else 1
seq={}
for x in sys.argv[5:]:
    f,b=x.split(':'); seq.setdefault(int(f),[]).append(b)
pb=PyBoy(rom,window="null",sound_emulated=False)
with open(st,'rb') as fh: pb.load_state(fh)
for f in range(frames):
    for b in seq.get(f,[]): pb.button(b,3)
    pb.tick()
im=pb.screen.image.convert('RGB'); im.resize((640,576),Image.NEAREST).save(out+'_x4.png')
v=[pb.memory[0x8000+i] for i in range(0x1800)]
img=Image.new('L',(16*8,24*8))
for t in range(384):
    for y in range(8):
        lo,hi=v[t*16+y*2],v[t*16+y*2+1]
        for x in range(8):
            c=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
            img.putpixel(((t%16)*8+x,(t//16)*8+y),255-c*85)
img.resize((512,768),Image.NEAREST).save(out+'_vram.png')
print('LCDC %02x SCX %d SCY %d WX %d WY %d BGP %02x OBP0 %02x OBP1 %02x'%tuple(pb.memory[a] for a in (0xff40,0xff43,0xff42,0xff4b,0xff4a,0xff47,0xff48,0xff49)))
for name,b in (('9800',0x9800),('9C00',0x9C00)):
    print(name)
    for r in range(18): print('%2d '%r+' '.join('%02x'%pb.memory[b+r*32+c] for c in range(20)))
with open(out+'.state','wb') as fh: pb.save_state(fh)
