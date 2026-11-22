# preview.py rom outdir : static previews (4x) of the redesigned screens from original data
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from codec import decompress_at
from gbgfx import idx_to_img
import designs as D
rom=open(sys.argv[1],'rb').read(); od=sys.argv[2]; os.makedirs(od,exist_ok=True)
def ent(i):
    o=0x3de5+i*5; b,s=rom[o],rom[o+1]|rom[o+2]<<8
    return decompress_at(rom,b*0x4000+s-0x4000)[0]
t00,m01=ent(0),ent(1)
nt=D.title(t00,m01)
idx_to_img(D.render(t00,m01,0,12,0,20),4).save(od+'/title_before.png')
idx_to_img(D.render(nt,m01,0,12,0,20),4).save(od+'/title_after.png')
t08,m09=ent(8),ent(9); b7=rom[7*0x4000:7*0x4000+0x1000]
nb7=D.numerals(b7)
nt8,nm9,used=D.card(t08,m09); print('card tiles used',used)
for k in (0,4,8):
    base=[0x80+2*j for j in range(8)]+[0xa0]
    def tf(c,k=k,bs=base[k]):
        if c in (0x85,0x86,0x95,0x96):
            i={0x85:0,0x86:1,0x95:16,0x96:17}[c]; return nb7[(bs+i)*16:(bs+i)*16+16]
        return nt8[D.toff(c):D.toff(c)+16]
    idx_to_img(D.render(nt8,nm9,0,8,0,20,tf),4).save(od+'/card_after_%d.png'%(k+1))
px=D.gameover(ent(0x17),ent(0x18),t00)
nt17=D.gameover_apply(ent(0x17),ent(0x18),px)
idx_to_img(D.render(nt17,ent(0x18),0,10,0,20),4).save(od+'/gameover_after.png')
b2=rom[2*0x4000+0xd00:2*0x4000+0xd90]
h=D.hud(b2)
from gbgfx import sheet
sheet(h,3,8).save(od+'/hud_after.png'); sheet(b2,3,8).save(od+'/hud_before.png')
t0e=ent(0x0e)
tl=[0xe0,0xe2,0xe4,0xe6,0xe8]
n0e=D.orb_tiles(t0e,tl,D.ORB_LABELS,lambda c:(c-0x80))
sheet(n0e[0x600:0x800],16,4).save(od+'/orbs_t0e_after.png')
n7=D.orb_tiles(nb7,[0xa6,0xa8,0xaa,0xac,0xae],D.ORB_LABELS,lambda c:c)
sheet(n7[:0x1000],16,4).save(od+'/bank7_after.png')
