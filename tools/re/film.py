# film: run with inputs, save screenshot every N frames into a contact sheet
import sys
from pyboy import PyBoy
from PIL import Image
rom,out,frames,step=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
seq=dict((int(x.split(':')[0]),x.split(':')[1]) for x in sys.argv[5:])
pb=PyBoy(rom,window="null",sound_emulated=False)
shots=[]
for f in range(frames):
    if f in seq: pb.button(seq[f],3)
    pb.tick()
    if f%step==0: shots.append(pb.screen.image.copy().convert('RGB'))
cols=8; rows=(len(shots)+cols-1)//cols
sh=Image.new('RGB',(cols*162,rows*146),'red')
for i,s in enumerate(shots): sh.paste(s,((i%cols)*162,(i//cols)*146))
sh.save(out)
