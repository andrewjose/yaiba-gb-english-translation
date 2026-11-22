# find_pickup.py rom out.png : play stage 1 (hold right, mash B/A) until an object uses tiles 2C-2F/3C-3F
import sys
from pyboy import PyBoy
from PIL import Image
pb=PyBoy(sys.argv[1],window="null",sound_emulated=False)
seq={300:'start'}; seq.update({f:'a' for f in range(3200,3500,30)})
for f in range(3700):
    if f in seq: pb.button(seq[f],3)
    pb.tick()
pb.button_press('right')
for f in range(12000):
    if f%12==0: pb.button('b',3)
    if f%90==0: pb.button('a',6)
    if f%600==300: pb.button_release('right'); pb.button_press('left')
    if f%600==0: pb.button_release('left'); pb.button_press('right')
    pb.tick()
    oam=[pb.memory[0xfe00+i] for i in range(160)]
    if any(oam[i*4+2] in (0x2c,0x2d,0x2e,0x2f,0x3c,0x3d,0x3e,0x3f) and 0<oam[i*4]<160 for i in range(40)):
        for _ in range(2): pb.tick()
        im=pb.screen.image.convert('RGB'); im.resize((480,432),Image.NEAREST).save(sys.argv[2]); print('found at',f); break
else: pb.screen.image.save(sys.argv[2]); print('not found')
