# shot_powerup.py rom out.png : stage-clear paths (engine harness emu.py) for chapters 1-8, screenshot every power-up
# screen 60 frames after its icon is drawn (hook bank0 $052F), holding A to page through text.
import sys
import os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','engine'))
import emu
from PIL import Image
rom,out=sys.argv[1],sys.argv[2]
shots=[]
for ch in range(1,9):
    pb=emu.boot_gameplay(rom)
    hit=[]
    pb.hook_register(0,0x052f,lambda _:hit.append(1),None)
    emu.stage_clear(pb,ch)
    n=len(hit); wait=None
    for f in range(4000):
        if f%40==0: pb.button('a',3)
        pb.tick()
        if len(hit)>n: n=len(hit); wait=60
        if wait is not None:
            wait-=1
            if wait==0: shots.append(pb.screen.image.convert('RGB')); wait=None
    print('chapter',ch,'power-up screens',len(hit))
    pb.stop()
cols=4; rows=max(1,(len(shots)+cols-1)//cols)
sh=Image.new('RGB',(cols*164,rows*148),'red')
for i,s in enumerate(shots): sh.paste(s,((i%cols)*164,(i//cols)*148))
sh=sh.resize((sh.width*2,sh.height*2),Image.NEAREST); sh.save(out)
