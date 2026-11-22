"""Headless PyBoy harness for Yaiba engine tests.
scene(rom, target_pc, d810, frames, presses, shots_every) -> list of PIL frames.
Boots, presses START, waits for the chapter-1 intro printer call (bank0 $0401, main thread,
sane stack), then redirects PC to target_pc with $D810 = d810."""
import sys
from pyboy import PyBoy
from PIL import Image

def boot(rom):
    pb=PyBoy(rom,window="null",sound_emulated=False)
    hit=[False]
    def cb(_):
        hit[0]=True
    pb.hook_register(0,0x0401,cb,None)
    f=0
    while not hit[0] and f<6000:
        if f==300: pb.button('start',3)
        pb.tick(); f+=1
    pb.hook_deregister(0,0x0401)
    # step until main thread is idle in a frame wait (halt loop of rst $08/$10)
    for _ in range(3): pb.tick()
    return pb,f

def redirect(pb,pc,d810=None,regs=None,fade=True):
    """Main thread is idle in a frame wait - redirect to pc. With fade=True the game's own
    fade-out/LCD routine $0069 runs first and 'returns' into pc (scene loads then happen
    exactly as in the normal flow)."""
    if d810 is not None: pb.memory[0xd810]=d810
    rf=pb.register_file
    for k,v in (regs or {}).items(): setattr(rf,k,v)
    if fade:
        sp=(rf.SP-2)&0xffff; pb.memory[sp]=pc&0xff; pb.memory[sp+1]=pc>>8; rf.SP=sp; rf.PC=0x0069
    else: rf.PC=pc

def run(pb,frames,presses=(),hold=None,every=0,shots=None):
    presses=set(presses)
    for f in range(frames):
        if f in presses: pb.button('a',3)
        if hold and hold[0]<=f<hold[1]: pb.button_press('a')
        if hold and f==hold[1]: pb.button_release('a')
        pb.tick()
        if every and shots is not None and f%every==0: shots.append(pb.screen.image.copy().convert('RGB'))
    return shots

def sheet(shots,out,cols=8,scale=1):
    rows=(len(shots)+cols-1)//cols
    sh=Image.new('RGB',(cols*162,rows*146),'red')
    for i,s in enumerate(shots): sh.paste(s,((i%cols)*162,(i//cols)*146))
    if scale!=1: sh=sh.resize((sh.width*scale,sh.height*scale),Image.NEAREST)
    sh.save(out)

def big(img,out,scale=3):
    img.convert('RGB').resize((160*scale,144*scale),Image.NEAREST).save(out)

def boot_gameplay(rom,extra=60):
    """Boot and press A at every A-wait ($0A0B: chapter-1 intro box, boss card) until the stage
    main loop runs (bank0 $01D6 idle loop); return the PyBoy paused there."""
    pb,f=boot(rom)
    st={'w':False,'g':False}
    pb.hook_register(0,0x0a0b,lambda _:st.__setitem__('w',True),None)
    pb.hook_register(0,0x01d6,lambda _:st.__setitem__('g',True),None)
    n=0
    while not st['g'] and n<6000:
        st['w']=False; pb.tick(); n+=1
        if st['w']:
            pb.button('a',3)
            for _ in range(10): pb.tick()
    pb.hook_deregister(0,0x0a0b); pb.hook_deregister(0,0x01d6)
    for _ in range(extra): pb.tick()
    return pb

def stage_clear(pb,d810):
    """From the stage main loop: jump to the level-clear path ($0206) for chapter d810
    -> chapter_end text ($04AC), power-up texts (1:$4233/$42F5), next chapter intro."""
    pb.memory[0xd810]=d810
    pb.register_file.PC=0x0206
