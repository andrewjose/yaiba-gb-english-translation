# forcescene.py rom out.png chapter_index entry_pc [frames_after] [presses]: boot to chapter-1 card, then jump to a scene routine
import sys
from pyboy import PyBoy
rom,out,ch,pc=sys.argv[1],sys.argv[2],int(sys.argv[3],0),int(sys.argv[4],16)
after=int(sys.argv[5]) if len(sys.argv)>5 else 400
pb=PyBoy(rom,window="null",sound_emulated=False)
for f in range(3150):
    if f==300: pb.button('start',3)
    pb.tick()
pb.memory[0xd810]=ch
pb.register_file.PC=pc
shots=[]
for f in range(after):
    if f in [int(x) for x in sys.argv[6:]]: pb.button('a',3)
    pb.tick()
pb.screen.image.save(out)
