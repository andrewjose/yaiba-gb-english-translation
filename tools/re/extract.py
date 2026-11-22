# extract.py rom outdir -> strings.json + all_strings.csv
import sys,os,json,csv
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from yaiba_text import *
from gfxdec import decompress
rom=open(sys.argv[1],'rb').read(); od=sys.argv[2]
S=[]
def add(**k): S.append(k)
# tables
for block,taddr,cnt,hdr,kind,ctx in TABLES:
    ptrs=[u16(rom,off(taddr)+2*i) for i in range(cnt)]
    seen={}
    for i,p in enumerate(ptrs):
        loc=taddr+2*i
        if p in seen: S[seen[p]]['ptr_locs'].append('%02x:%04x'%(BANK,loc)); continue
        h,pages,end=parse_dialogue(rom,p,hdr,kind)
        raw=rom[off(p):off(end)]
        seen[p]=len(S)
        add(id='%s_%02d'%(block,i),block=block,bank=BANK,ptr_locs=['%02x:%04x'%(BANK,loc)],addr='%04x'%p,off='%05x'%off(p),
            kind=kind,header=h.hex(),raw_hex=raw.hex(),jp=pages_to_text(pages),max_bytes=len(raw),
            max_line_cells=12 if block=='chapter_intro' else 14,ctx=ctx+' ; pages=%d'%len(pages))
n=0
for block,locs,addr,hdr,kind in DIRECT:
    addr=u16(rom,off(locs[0]))  # follow the code immediate (ld hl,nn)
    h,pages,end=parse_dialogue(rom,addr,hdr,kind); raw=rom[off(addr):off(end)]
    add(id='%s_%02d'%(block,sum(1 for s in S if s['block']==block)),block=block,bank=BANK,ptr_locs=['%02x:%04x'%(BANK,l) for l in locs],
        addr='%04x'%addr,off='%05x'%off(addr),kind=kind,header=h.hex(),raw_hex=raw.hex(),jp=pages_to_text(pages),max_bytes=len(raw),
        max_line_cells=12 if block=='powerup' else 16,
        ctx=('rival Onimaru scene, printer 1:$41F0 on BG $9C00 (no A-skip), ' if block=='rival' else 'power-up/orb message, bank0 $0509 -> 1:$4324 at $9947, hdr=[image tile ofs bank7 $6000+16n 5x5], ')+'pages=%d'%len(pages))
# menus (fixed-length VRAM script fields)
for block,taddr,cnt,hdr in MENUS:
    for i in range(cnt):
        p=u16(rom,off(taddr)+2*i); cmds,end=parse_script(rom,off(p)+hdr)
        # pair dakuten rows with text rows (dakuten row addr = text addr - 0x20)
        byaddr={a:(o,nn,dat) for o,nn,a,dat in cmds}
        for o,nn,a,dat in cmds:
            if nn<4: continue
            if all(c in (0,0x7c,0x7d) for c in dat): continue  # dakuten row (or blank)
            dk=byaddr.get(a-0x20)
            if dk and dk[1]>nn: dk=None
            merged=bytearray()
            for k,c in enumerate(dat):
                merged.append(c)
                if dk and k<dk[1] and dk[2][k] in (0x7c,0x7d): merged.append(dk[2][k])
            add(id='%s_%02d_%04x'%(block,i,a),block=block,bank=BANK,ptr_locs=['%02x:%04x'%(BANK,taddr+2*i)],addr='%04x'%(o-0x4000+0x4000),
                off='%05x'%o,kind='fixed',vram='%04x'%a,dakuten_off='%05x'%(dk[0]) if dk else '',raw_hex=dat.hex(),
                jp=decode(bytes(merged)).rstrip('\u3000'),max_bytes=nn,max_line_cells=nn,
                ctx='VRAM script field (n=%d at $%04x), menu record %d; dakuten row separate at $%04x'%(nn,a,i,a-0x20))
# tilemaps
for block,idx in TILEMAPS:
    r=0x3de5+idx*5; b=rom[r]; src=u16(rom,r+1); dst=u16(rom,r+3)
    data,clen=decompress(rom,b,src)
    for row in range(len(data)//32):
        line=data[row*32:row*32+32]
        dk=data[(row-1)*32:(row-1)*32+32] if row else bytes(32)
        # segments of font codes (0x00 space allowed singly) separated by 2+ spaces or non-font tiles
        segs=[];cur=[]
        for c in range(21):
            v=line[c] if c<20 else 0x100
            if block=='sword_select_screen' and 7<=row<=10 and c<13: v=0x100  # 12x4 sword-kanji canvas (tiles 04-3F reused)
            if 0x01<=v<=0x7f and v not in (0x7c,0x7d): cur.append(c)
            elif v==0 and cur and c+1<20 and not (block=='sword_select_screen' and 7<=row<=10 and c<13) and 0x01<=line[c+1]<=0x7f and line[c+1] not in (0,0x7c,0x7d): cur.append(c)
            else:
                if cur: segs.append(cur); cur=[]
        for seg in segs:
            if not any(0x4a<=line[c]<=0x7f or 0x0a<=line[c]<=0x3f and line[c]!=0 for c in seg): continue
            if not any(0x4a<=line[c]<=0x7f for c in seg) and block=='sword_select_screen': continue
            c0,c1=seg[0],seg[-1]+1
            merged=bytearray()
            for c in range(c0,c1):
                merged.append(line[c])
                if dk[c] in (0x7c,0x7d): merged.append(dk[c])
            add(id='%s_r%02dc%02d'%(block,row,c0),block=block,bank=b,ptr_locs=['00:%04x'%(r)],addr='%04x'%src,off='%05x'%(b*0x4000+src-0x4000),
                kind='tilemap',map_index=idx,row=row,col=c0,raw_hex=bytes(line[c0:c1]).hex(),jp=decode(bytes(merged)),
                max_bytes=(20 if block=='intro_scroll' else 19)-c0,max_line_cells=(20 if block=='intro_scroll' else 19)-c0,
                ctx='compressed tilemap #%02x -> $%04x (codec bank0 $3B7E), row %d col %d; dakuten on row-1'%(idx,dst,row,c0))
os.makedirs(od,exist_ok=True)
json.dump(S,open(os.path.join(od,'strings.json'),'w'),ensure_ascii=False,indent=1)
with open(os.path.join(od,'all_strings.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['id','block','bank','addr','off','ptr_locs','max_bytes','raw_hex','jp','english'])
    for s in S: w.writerow([s['id'],s['block'],s['bank'],s['addr'],s['off'],' '.join(s['ptr_locs']),s['max_bytes'],s['raw_hex'],s['jp'],''])
from collections import Counter
c=Counter(s['block'] for s in S)
for k,v in c.items():
    chars=sum(len(s['jp'].replace('\n','').replace('<page>','')) for s in S if s['block']==k)
    print('%-22s strings %3d  chars %5d'%(k,v,chars))
