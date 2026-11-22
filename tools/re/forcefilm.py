# forcefilm.py rom out.png chapter pc frames step [a-press frames...] : boot to ch1 dialogue, set d810, jump PC, film
import sys
from pyboy import PyBoy
from PIL import Image
rom,out,ch,pc,frames,step=sys.argv[1],sys.argv[2],int(sys.argv[3],0),int(sys.argv[4],16),int(sys.argv[5]),int(sys.argv[6])
presses=set(int(x) for x in sys.argv[7:])
pb=PyBoy(rom,window="null",sound_emulated=False)
for f in range(3150):
    if f==300: pb.button('start',3)
    pb.tick()
pb.memory[0xd810]=ch
pb.register_file.PC=pc
shots=[]
for f in range(frames):
    if f in presses: pb.button('a',3)
    pb.tick()
    if f%step==0: shots.append(pb.screen.image.copy().convert('RGB'))
cols=8; rows=(len(shots)+cols-1)//cols
sh=Image.new('RGB',(cols*162,rows*146),'red')
for i,s in enumerate(shots): sh.paste(s,((i%cols)*162,(i//cols)*146))
sh.save(out)
