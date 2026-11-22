# shots.py rom tag : runtime screenshots (PyBoy) of every graphics-text screen -> shots/<screen>_<tag>.png (2x)
# needs states made from the ORIGINAL ROM boot path; states are re-created per ROM so the build is exercised.
import sys,os
from pyboy import PyBoy
from PIL import Image
rom,tag=sys.argv[1],sys.argv[2]
od=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','shots'); os.makedirs(od,exist_ok=True)
def new(): return PyBoy(rom,window="null",sound_emulated=False)
def save(img,name): img.convert('RGB').resize((img.width*2,img.height*2),Image.NEAREST).save(f'{od}/{name}_{tag}.png')
def run(pb,n,presses=()):
    for f in range(n):
        if f in presses: pb.button(presses[f] if isinstance(presses,dict) else 'a',3)
        pb.tick()
# title
pb=new(); run(pb,400); save(pb.screen.image,'title')
# chapter 1 card + boss card + HUD (normal play path)
run(pb,2900,{f:'start' for f in [0]} if False else {})
pb=new()
seq={300:'start'}; seq.update({f:'a' for f in range(3200,3500,30)})
card=boss=None; cf=bf=None
M=lambda r,c: pb.memory[0x9800+r*32+c]
for f in range(3900):
    if f in seq: pb.button(seq[f],3)
    pb.tick()
    if cf is None and pb.memory[0xff40]&0x80 and M(3,12)==0xec and M(0,19)==0xc9: cf=f
    if cf is not None and f==cf+60:
        card=pb.screen.image.copy(); cst='/tmp/_card_%s.state'%tag
        with open(cst,'wb') as fh: pb.save_state(fh)
    if bf is None and pb.memory[0xff40]&0x80 and M(4,7)==0x85 and M(4,8)==0x86 and M(5,7)==0x95: bf=f
    if bf is not None and f==bf+40: boss=pb.screen.image.copy()
print('card frame',cf,'boss frame',bf)
save(card,'card_ch1'); save(pb.screen.image,'hud')
st='/tmp/_stage_%s.state'%tag
with open(st,'wb') as fh: pb.save_state(fh)
# chapter cards 1-9: from stage state, set chapter $D810, jump to card routine $03B3
imgs=[]
for ch in range(1,10):
    pb=new(); pb.load_state(open(cst,'rb')); pb.memory[0xd810]=ch; pb.register_file.PC=0x03b3; run(pb,120)
    imgs.append(pb.screen.image.convert('RGB').crop((0,0,160,64)))
sh=Image.new('RGB',(160*3,64*3)); [sh.paste(im,((i%3)*160,(i//3)*64)) for i,im in enumerate(imgs)]
save(sh,'card_all')
# game over (continues=3): jump to $0249
pb=new(); pb.load_state(open(st,'rb')); pb.memory[0xffd0]=3; pb.register_file.PC=0x0249; run(pb,200); save(pb.screen.image,'gameover')
# sword select with all orb icons
pb=new(); pb.load_state(open(st,'rb'))
for a,v in ((0xd812,1),(0xd813,2),(0xd814,3),(0xd815,4),(0xd816,5),(0xd869,1),(0xd86a,2),(0xd86b,4),(0xd817,0x48)): pb.memory[a]=v
ims=[]
for f in range(600):
    if f==10: pb.button('select',3)
    if f in (250,350): pb.button('right',3)
    pb.tick()
    if f in (240,340,440): ims.append(pb.screen.image.convert('RGB'))
sh=Image.new('RGB',(160*3+8,144),'red'); [sh.paste(im,(i*164,0)) for i,im in enumerate(ims)]
save(sh,'swordselect')
# Dark orb (level 5) on slot 1 + dragon orb (level 3)
pb=new(); pb.load_state(open(st,'rb'))
for a,v in ((0xd812,5),(0xd813,3),(0xd869,1),(0xd86a,2),(0xd86b,0),(0xd817,0x48)): pb.memory[a]=v
for f in range(400):
    if f==10: pb.button('select',3)
    if f==250: pb.button('right',3)
    pb.tick()
    if f==240: a1=pb.screen.image.convert('RGB')
sh=Image.new('RGB',(160*2+4,144),'red'); sh.paste(a1,(0,0)); sh.paste(pb.screen.image.convert('RGB'),(164,0))
save(sh,'swordselect2')
# boss cards: chapter $D810=1..8 -> bank 0E asset d810-1. Natural play to chapter 1's boss card; a PyBoy hook
# on bank0 $0407 (boss-card entry) sets $D810 just before the asset is chosen.
imgs=[]
for ch in range(1,9):
    pb=new()
    def hk(ctx): pb.memory[0xd810]=ctx
    pb.hook_register(0,0x0407,hk,ch)
    seq={300:'start'}; seq.update({f:'a' for f in range(3200,3500,30)})
    ok=0; shot=None
    for f in range(3700):
        if f in seq: pb.button(seq[f],3)
        pb.tick()
        M=lambda r,c: pb.memory[0x9800+r*32+c]
        ok=ok+1 if (pb.memory[0xff40]&0x80 and M(4,7)==0x85 and M(14,0)==0x01 and pb.memory[0xff47]==0xe4) else 0
        if ok==10: shot=pb.screen.image.convert('RGB'); break
    imgs.append(shot or Image.new('RGB',(160,144),'red'))
sh=Image.new('RGB',(160*4,144*2)); [sh.paste(im,((i%4)*160,(i//4)*144)) for i,im in enumerate(imgs)]
save(sh,'bosscards')
