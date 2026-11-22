# hooklog.py rom frames addr[,addr..] [frame:btn ...] : log register state at hooks (bank 0 addrs or bank:addr)
import sys
from pyboy import PyBoy
rom,frames=sys.argv[1],int(sys.argv[2])
addrs=sys.argv[3].split(',')
seq=dict((int(x.split(':')[0]),x.split(':')[1]) for x in sys.argv[4:])
pb=PyBoy(rom,window="null",sound_emulated=False)
F=[0]
def cb(tag):
    r=pb.register_file
    print('f%d %s A=%02x BC=%04x DE=%04x HL=%04x bank=%02x SP=%04x ret=%02x%02x'%(F[0],tag,r.A,(r.B<<8)|r.C,(r.D<<8)|r.E,r.HL,pb.memory[0xffc7],r.SP,pb.memory[r.SP+1],pb.memory[r.SP]))
for a in addrs:
    if ':' in a: b,ad=a.split(':'); b=int(b,16); ad=int(ad,16)
    else: b,ad=0,int(a,16)
    pb.hook_register(b,ad,cb,a)
for f in range(frames):
    F[0]=f
    if f in seq: pb.button(seq[f],3)
    pb.tick()
