# mkstate.py rom out.state frames [frame:btn ...]  (btn may be '+btn'/'-btn' for press/release hold)
import sys
from pyboy import PyBoy
rom,out,frames=sys.argv[1],sys.argv[2],int(sys.argv[3])
seq={}
for x in sys.argv[4:]:
    f,b=x.split(':'); seq.setdefault(int(f),[]).append(b)
pb=PyBoy(rom,window="null",sound_emulated=False)
for f in range(frames):
    for b in seq.get(f,[]):
        if b[0]=='+': pb.button_press(b[1:])
        elif b[0]=='-': pb.button_release(b[1:])
        else: pb.button(b,3)
    pb.tick()
with open(out,'wb') as fh: pb.save_state(fh)
pb.screen.image.save(out+'.png')
