#!/usr/bin/env python3
"""Headless scene tests for Yaiba builds. usage: shots.py ROM OUTDIR TAG [scenario ...]
Scenarios: intro (boot -> chapter_intro_00 -> gameplay), clearN (stage-clear path for chapter N:
chapter_end_N, power-up messages, next scene / chapter intro N+1), rival (= clear9 -> ending).
Every text page (game waiting for A at $0A0B) is saved as TAG_<scenario>_wait<k>.png (x2),
plus the frame 6 frames after A (box cleared / next page starting) and a contact strip of the
scenario (every 30 frames). Prints frames spent typing each page."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from emu import boot,boot_gameplay,stage_clear,sheet
from PIL import Image
def save(img,path,s=2): img.convert('RGB').resize((160*s,144*s),Image.NEAREST).save(path)
def scenario(pb,out,name,maxwaits=12,frames=6000,hold_a=False):
    waits=[];shots=[];k=0;f=0;last=0
    st={'hit':False}
    pb.hook_register(0,0x0a0b,lambda _:st.__setitem__('hit',True),None)
    while f<frames and k<maxwaits:
        st['hit']=False
        if hold_a: pb.button_press('a')
        pb.tick(); f+=1
        if f%30==0: shots.append(pb.screen.image.copy().convert('RGB'))
        if st['hit']:
            if hold_a: pb.button_release('a'); pb.tick(); f+=1
            k+=1; waits.append(f-last)
            save(pb.screen.image,os.path.join(out,'%s_wait%d.png'%(name,k)))
            pb.button('a',3)
            for _ in range(8): pb.tick(); f+=1
            save(pb.screen.image,os.path.join(out,'%s_wait%d_after.png'%(name,k)))
            last=f
    for _ in range(240):
        pb.tick(); f+=1
        if f%30==0: shots.append(pb.screen.image.copy().convert('RGB'))
    save(pb.screen.image,os.path.join(out,'%s_end.png'%name))
    sheet(shots,os.path.join(out,'%s_strip.png'%name),cols=10)
    print(name,'frames between A-waits:',waits)
if __name__=='__main__':
    rom,out,tag=sys.argv[1],sys.argv[2],sys.argv[3]
    os.makedirs(out,exist_ok=True)
    for sc in sys.argv[4:] or ['intro','clear2','clear3','clear6','clear10','rival']:
        if sc=='intro':
            pb,_=boot(rom); scenario(pb,out,tag+'_intro',maxwaits=1,frames=1200)
        elif sc=='introA':
            pb,_=boot(rom); scenario(pb,out,tag+'_introA',maxwaits=1,frames=1200,hold_a=True)
        elif sc.startswith('clear'):
            n=int(sc[5:]); pb=boot_gameplay(rom); stage_clear(pb,n)
            scenario(pb,out,'%s_clear%02d'%(tag,n),maxwaits=6,frames=4000)
        elif sc=='crawl':
            from emu import sheet as _sh
            from pyboy import PyBoy
            pb=PyBoy(rom,window="null",sound_emulated=False); fr=[]
            for f in range(2500):
                if f==300: pb.button('start',3)
                pb.tick()
                if f in (700,1000,1250,1500,1800,2100): save(pb.screen.image,os.path.join(out,'%s_crawl_f%d.png'%(tag,f)))
                if f%80==0: fr.append(pb.screen.image.copy().convert('RGB'))
            _sh(fr,os.path.join(out,'%s_crawl_strip.png'%tag),cols=8)
        elif sc=='swsel':
            pb=boot_gameplay(rom)
            for a_,v in ((0xd812,1),(0xd813,2),(0xd814,3),(0xd815,4),(0xd816,5),(0xd869,1),(0xd86a,2),(0xd86b,4),(0xd817,0x48)):
                pb.memory[a_]=v
            for f in range(1000):
                if f==10: pb.button('select',3)
                if f in (250,350): pb.button('right',3)
                if f==450: pb.button('down',3)
                if f in (650,750,850): pb.button('right',3)
                pb.tick()
                if f in (240,340,440,540,640,740,840,940): save(pb.screen.image,os.path.join(out,'%s_swsel_f%d.png'%(tag,f)),3)
        elif sc=='swsel2':     # orb/move names: A on a sword, then toggle the orb choice
            pb=boot_gameplay(rom)
            for a_,v in ((0xd812,1),(0xd813,2),(0xd814,3),(0xd815,4),(0xd816,5),(0xd869,1),(0xd86a,2),(0xd86b,4),(0xd817,0x48)):
                pb.memory[a_]=v
            ev={10:'select',250:'a',400:'right',550:'right',700:'b',800:'right',900:'a',1050:'right',1200:'b',1300:'right',1400:'a',1550:'right'}
            for f in range(1700):
                if f in ev: pb.button(ev[f],3)
                pb.tick()
                if f in (240,390,540,690,890,1040,1190,1390,1540,1690): save(pb.screen.image,os.path.join(out,'%s_swsel2_f%d.png'%(tag,f)),3)
        elif sc=='gameover':
            pb=boot_gameplay(rom); pb.memory[0xffd0]=3; pb.register_file.PC=0x0249
            for f in range(400): pb.tick()
            save(pb.screen.image,os.path.join(out,'%s_gameover.png'%tag),3)
        elif sc.startswith('card'):
            n=int(sc[4:]); pb,_=boot(rom)
            from emu import redirect
            redirect(pb,0x03b3,n)
            scenario(pb,out,'%s_card%d'%(tag,n),maxwaits=1,frames=1500)
        elif sc=='hud':
            pb=boot_gameplay(rom); fr=[]
            for f in range(1500):
                if f%60<40: pb.button_press('right')
                else: pb.button_release('right')
                if f%50==0: pb.button('a',3)
                if f%70==0: pb.button('b',3)
                pb.tick()
                if f%100==0: fr.append(pb.screen.image.copy().convert('RGB'))
            sheet(fr,os.path.join(out,'%s_hud_strip.png'%tag),cols=5)
        elif sc=='rival':
            pb=boot_gameplay(rom); stage_clear(pb,9)
            scenario(pb,out,tag+'_rival',maxwaits=8,frames=5000)
        pb.stop()
