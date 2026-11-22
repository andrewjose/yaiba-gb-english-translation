# force.py rom state out_prefix pc frames [addr=val ...]: load state, poke, jump PC, run, screenshot x1/x4 + state
import sys
from pyboy import PyBoy
from PIL import Image
rom,st,out,pc,frames=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4],16),int(sys.argv[5])
pb=PyBoy(rom,window="null",sound_emulated=False)
with open(st,'rb') as fh: pb.load_state(fh)
for kv in sys.argv[6:]:
    a,v=kv.split('='); pb.memory[int(a,16)]=int(v,16)
pb.register_file.PC=pc
for f in range(frames): pb.tick()
im=pb.screen.image.convert('RGB'); im.save(out+'.png'); im.resize((640,576),Image.NEAREST).save(out+'_x4.png')
with open(out+'.state','wb') as fh: pb.save_state(fh)
