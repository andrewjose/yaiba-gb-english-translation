# filmstate.py rom state out.png frames step [frame:btn ...] [--save f:path]
import sys
from pyboy import PyBoy
from PIL import Image
rom,st,out,frames,step=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5])
seq={}; saves={}
for x in sys.argv[6:]:
    f,b=x.split(':',1)
    if b.startswith('save='): saves[int(f)]=b[5:]
    else: seq.setdefault(int(f),[]).append(b)
pb=PyBoy(rom,window="null",sound_emulated=False)
with open(st,'rb') as fh: pb.load_state(fh)
shots=[]
for f in range(frames):
    for b in seq.get(f,[]):
        if b[0]=='+': pb.button_press(b[1:])
        elif b[0]=='-': pb.button_release(b[1:])
        else: pb.button(b,3)
    pb.tick()
    if f in saves:
        with open(saves[f],'wb') as fh: pb.save_state(fh)
        pb.screen.image.save(saves[f]+'.png')
    if f%step==0: shots.append(pb.screen.image.copy().convert('RGB'))
cols=8; rows=(len(shots)+cols-1)//cols
sh=Image.new('RGB',(cols*162,rows*146),'red')
for i,s in enumerate(shots): sh.paste(s,((i%cols)*162,(i//cols)*146))
sh.save(out)
