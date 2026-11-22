# harness: python3 -I run.py rom out.png frames [frame:btn ...]; also dumps vram sheet, bg map text
import sys
from pyboy import PyBoy
from PIL import Image
def sheet(pb,out):
    v=[pb.memory[0x8000+i] for i in range(0x1800)]
    img=Image.new('L',(16*8,24*8))
    for t in range(384):
        for y in range(8):
            lo,hi=v[t*16+y*2],v[t*16+y*2+1]
            for x in range(8):
                c=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
                img.putpixel(((t%16)*8+x,(t//16)*8+y),255-c*85)
    img.resize((256,384),Image.NEAREST).save(out)
def bgmap(pb,base=0x9800):
    return [[pb.memory[base+r*32+c] for c in range(32)] for r in range(32)]
if __name__=='__main__':
    rom,out,frames=sys.argv[1],sys.argv[2],int(sys.argv[3])
    pb=PyBoy(rom,window="null",sound_emulated=False)
    seq=[(int(x.split(':')[0]),x.split(':')[1]) for x in sys.argv[4:]]
    f=0
    for t,btn in seq+[(frames,None)]:
        while f<t: pb.tick(); f+=1
        if btn: pb.button(btn,3)
    pb.screen.image.save(out)
    sheet(pb,out.replace('.png','_vram.png'))
    print('LCDC %02x WX %d WY %d'%(pb.memory[0xff40],pb.memory[0xff4b],pb.memory[0xff4a]))
    for name,b in (('9800',0x9800),('9C00',0x9C00)):
        print(name)
        for r,row in enumerate(bgmap(pb,b)[:18]): print('%2d '%r+' '.join('%02x'%x for x in row[:20]))
    pb.stop()
