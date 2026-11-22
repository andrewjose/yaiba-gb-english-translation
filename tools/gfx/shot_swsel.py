# shot_swsel.py rom out_prefix : sword select with all swords/orb levels poked, cursor on each slot
import sys
from pyboy import PyBoy
from PIL import Image
rom,out=sys.argv[1],sys.argv[2]
pb=PyBoy(rom,window="null",sound_emulated=False)
pb.load_state(open(sys.argv[3] if len(sys.argv)>3 else 'tmp/stage1.state','rb'))
for a,v in ((0xd812,1),(0xd813,2),(0xd814,3),(0xd815,4),(0xd816,5),(0xd869,1),(0xd86a,2),(0xd86b,4),(0xd817,0x48)):
    pb.memory[a]=v
shots=[]
for f in range(600):
    if f==10: pb.button('select',3)
    if f in (250,350): pb.button('right',3)
    pb.tick()
    if f in (240,340,440): shots.append(pb.screen.image.convert('RGB').resize((640,576),Image.NEAREST))
sh=Image.new('RGB',(640*3+20,576),'red')
for i,s in enumerate(shots): sh.paste(s,(i*650,0))
sh.save(out+'.png')
