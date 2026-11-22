# snap.py rom frames out [frame:btn...] -> png + vram.bin(8000-9FFF) + oam
import sys
from pyboy import PyBoy
rom,frames,out=sys.argv[1],int(sys.argv[2]),sys.argv[3]
seq=dict((int(x.split(':')[0]),x.split(':')[1]) for x in sys.argv[4:])
pb=PyBoy(rom,window="null",sound_emulated=False)
for f in range(frames):
    if f in seq: pb.button(seq[f],3)
    pb.tick()
pb.screen.image.save(out+'.png')
open(out+'.vram','wb').write(bytes(pb.memory[0x8000+i] for i in range(0x2000)))
open(out+'.wram','wb').write(bytes(pb.memory[0xc000+i] for i in range(0x2000)))
print('LCDC %02x bank %02x'%(pb.memory[0xff40],pb.memory[0xffc7]))
