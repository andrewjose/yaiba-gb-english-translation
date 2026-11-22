# film.py rom out.png frames step [frame:btn ...] -> contact sheet of screenshots
import sys
from pyboy import PyBoy
from PIL import Image
rom,out,frames,step=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
seq={}
for x in sys.argv[5:]:
    f,b=x.split(':'); seq.setdefault(int(f),[]).append(b)
pb=PyBoy(rom,window="null",sound_emulated=False)
shots=[]
for f in range(frames):
    for b in seq.get(f,[]): pb.button(b,3)
    pb.tick()
    if f%step==0: shots.append((f,pb.screen.image.copy().convert('RGB')))
cols=8; rows=(len(shots)+cols-1)//cols
sh=Image.new('RGB',(cols*162,rows*146),'red')
for i,(f,s) in enumerate(shots): sh.paste(s,((i%cols)*162,(i//cols)*146))
sh.save(out); print(len(shots))
