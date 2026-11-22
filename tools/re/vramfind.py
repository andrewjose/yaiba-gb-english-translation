# run to frame, dump VRAM 0x9000-0x97FF font tiles, find each tile in ROM
import sys
from pyboy import PyBoy
rom=sys.argv[1]
pb=PyBoy(rom,window="null",sound_emulated=False)
for f in range(3150):
    if f==300: pb.button('start',3)
    pb.tick()
v=bytes(pb.memory[0x9000+i] for i in range(0x800))
open('tmp/vram9000.bin','wb').write(v)
open('tmp/vram8000.bin','wb').write(bytes(pb.memory[0x8000+i] for i in range(0x1000)))
d=open(rom,'rb').read()
for t in range(0,128):
    tile=v[t*16:t*16+16]
    if tile==bytes(16): continue
    i=d.find(tile)
    print('%02x'%t, hex(i) if i>=0 else '-', end='; ')
