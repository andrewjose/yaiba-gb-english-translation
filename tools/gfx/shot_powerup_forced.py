# shot_powerup_forced.py rom out.png : chapter-1 stage-clear power-up screen with the icon byte forced
# (hook bank0 $051F, register A = icon offset) for every orb icon: T W St Ov Dk Dr
import sys
import os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','engine'))
import emu
from PIL import Image
rom,out=sys.argv[1],sys.argv[2]
shots=[]
for icon in (0x50,0x55,0x5a,0xa0,0xa5,0xaa):
    pb=emu.boot_gameplay(rom)
    def hk(v): pb.register_file.A=v
    pb.hook_register(0,0x051f,hk,icon)
    hit=[]
    pb.hook_register(0,0x052f,lambda _:hit.append(1),None)
    emu.stage_clear(pb,1)
    wait=None
    for f in range(3000):
        if f%40==0 and not hit: pb.button('a',3)
        pb.tick()
        if hit and wait is None: wait=60
        if wait is not None:
            wait-=1
            if wait==0: break
    shots.append(pb.screen.image.convert('RGB').crop((0,64,160,144))); pb.stop()
sh=Image.new('RGB',(3*164,2*84),'red')
for i,s in enumerate(shots): sh.paste(s,((i%3)*164,(i//3)*84))
sh.resize((sh.width*2,sh.height*2),Image.NEAREST).save(out)
