# insert.py orig.gb strings.json [trans.json] out.gb [--tbl table.tbl] [--report]
#  trans.json: {id: text}. Missing ids are rebuilt from strings.json 'jp' (round trip).
#  Dialogue (bank 1) is repacked in original order into the original text regions, then into free
#  bank-1 space; all pointers (tables + code immediates) are rewritten. Menu fields are fixed-length.
#  Compressed tilemaps are re-encoded (simple codec subset) and relocated to free space if changed;
#  the bank0 $3DE5 graphics table record (bank, src) is repointed.
import sys,os,json,argparse,unicodedata
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from yaiba_text import *
from gfxdec import decompress
import tbl as T
ap=argparse.ArgumentParser(); ap.add_argument('orig'); ap.add_argument('strings'); ap.add_argument('rest',nargs='+')
ap.add_argument('--tbl'); ap.add_argument('--expand',action='store_true',help='bump ROM to 512KB (0x148=4)')
a=ap.parse_args()
trans=json.load(open(a.rest[0])) if len(a.rest)>1 else {}
out=a.rest[-1]
rom=bytearray(open(a.orig,'rb').read()); orig=bytes(rom)
if a.expand and len(rom)==0x40000:
    rom+=b'\xff'*0x40000; rom[0x148]=4
S=json.load(open(a.strings))
# --- table: load .tbl (XX=char lines) if given, else built-in
REV=dict(T.REV)
if a.tbl:
    REV={}
    for ln in open(a.tbl,encoding='utf-8'):
        ln=ln.rstrip('\n')
        if not ln or ln.startswith('#') or '=' not in ln: continue
        k,v=ln.split('=',1)
        if k[0] in '/*$': continue
        if len(k)==2: REV.setdefault(v,int(k,16))
def enc(s):
    o=bytearray(); i=0
    while i<len(s):
        if s[i]=='[': j=s.index(']',i); o.append(int(s[i+1:j],16)); i=j+1; continue
        if s[i]=='\n': o.append(0xff); i+=1; continue
        ch=s[i]
        if ch in REV: o.append(REV[ch])
        else:
            d=unicodedata.normalize('NFD',ch)
            if len(d)==2 and d[0] in REV and d[1] in '゙゚': o+=bytes([REV[d[0]],0x7c if d[1]=='゙' else 0x7d])
            else: raise SystemExit('unencodable char %r in %r'%(ch,s))
        i+=1
    return bytes(o)
def txt(s): return trans.get(s['id'],s['jp'])
def pages_bytes(t,maxcells,sid):
    pages=[[enc(l) for l in p.split('\n')] for p in t.split('\n<page>\n')]
    for p in pages:
        for l in p:
            cells=len([c for c in l if c not in (0x7c,0x7d)])
            if cells>maxcells: print('WARN %s: line %d cells > %d: %r'%(sid,cells,maxcells,l.hex()))
    return pages
def put16(loc,v):
    b,ad=loc.split(':'); b=int(b,16); ad=int(ad,16)
    o=ad if ad<0x4000 else b*0x4000+ad-0x4000
    rom[o]=v&0xff; rom[o+1]=v>>8
# ---------------- dialogue repack
dlg=sorted([s for s in S if s['kind'] in ('single','multi')],key=lambda s:int(s['addr'],16))
regions=[list(r) for r in ORIG_REGIONS+FREE_REGIONS]
for r0,r1 in ORIG_REGIONS:
    for x in range(r0,r1): rom[off(x)]=0
blobs=[(s,bytes.fromhex(s['header'])+serialize(b'',pages_bytes(txt(s),s['max_line_cells'],s['id']),s['kind'])) for s in dlg]
ri=0; pos=regions[0][0]; pending=False; report=[]
def close_pending(pos,rend):
    # multi-page string needs a non-FF byte after it
    if pos<rend: rom[off(pos)]=0x00; return pos+1
    if rom[off(pos)]!=0xff: return pos      # byte beyond region end (original layout) acts as terminator
    raise SystemExit('no room for terminator at %04x'%pos)
for s,b in blobs:
    while True:
        rend=regions[ri][1]
        need=len(b)+(1 if s['kind']=='multi' else 0)
        if pending and b[:1]==b'\xff': need+=1
        if pos+len(b)<=rend and (s['kind']!='multi' or pos+len(b)<rend or rom[off(rend)]!=0xff):
            if pending and b[0]==0xff: pos=close_pending(pos,rend)
            break
        if pending: close_pending(pos,rend); pending=False
        ri+=1
        if ri>=len(regions): raise SystemExit('bank 1 text space exhausted at %s'%s['id'])
        pos=regions[ri][0]
    rom[off(pos):off(pos)+len(b)]=b
    for l in s['ptr_locs']: put16(l,pos)
    report.append((s['id'],pos,len(b),s['max_bytes']))
    pos+=len(b); pending=(s['kind']=='multi')
if pending: close_pending(pos,regions[ri][1])
# ---------------- fixed menu fields
def split_dk(bs):
    cells=bytearray(); dk=bytearray()
    for c in bs:
        if c in (0x7c,0x7d) and cells: dk[-1]=c
        else: cells.append(c); dk.append(0)
    return bytes(cells),bytes(dk)
for s in [s for s in S if s['kind']=='fixed']:
    cells,dk=split_dk(enc(txt(s))); n=s['max_bytes']
    if len(cells)>n: raise SystemExit('%s too long (%d>%d)'%(s['id'],len(cells),n))
    o=int(s['off'],16)+3  # 'off' = script command start [n][lo][hi]
    new=cells+bytes(n-len(cells))
    rom[o:o+n]=new
    if s['dakuten_off']:
        d=int(s['dakuten_off'],16); dn=rom[d]; base=d+3
        row=(dk+bytes(n))[:dn]
        rom[base:base+dn]=row
    elif any(dk): raise SystemExit('%s: dakuten but no dakuten row'%s['id'])
# ---------------- tilemaps
def compress(data,typ):
    n=typ&0xf; S_=16<<n; nb=len(data)//S_
    ctl=bytearray(); stream=bytearray(); codes=[]
    for k in range(nb):
        blk=data[k*S_:(k+1)*S_]
        if n and not any(blk): codes.append(0); continue
        codes.append(1)
        d=2<<n; mask=bytearray(d); lits=bytearray()
        for i,v in enumerate(blk):
            if v: mask[i//8]|=1<<(i%8); lits.append(v)
        if n==3: assert not any(blk[64:]) or True
        stream+=mask+lits
    if n:
        for k in range(0,len(codes),4):
            v=0
            for j,c in enumerate(codes[k:k+4]): v|=c<<(2*j)
            ctl.append(v)
    else:
        for k in range(0,len(codes),8):
            v=0
            for j,c in enumerate(codes[k:k+8]): v|=c<<j
            ctl.append(v)
    hdr=bytes([typ,nb&0xff,nb>>8])+(5+len(stream)).to_bytes(2,'little')
    return hdr+bytes(stream)+bytes(ctl)
FREE_GFX={5:[0x5492,0x8000],0xd:[0x58a2,0x8000],9:[0x6c59,0x8000],3:[0x7535,0x8000]}  # FF-filled tails (static)
for idx in sorted(set(s['map_index'] for s in S if s['kind']=='tilemap')):
    r=0x3de5+idx*5; b=rom[r]; src=rom[r+1]|rom[r+2]<<8
    data,clen=decompress(orig,b,src); m=bytearray(data)
    for s in [s for s in S if s['kind']=='tilemap' and s['map_index']==idx]:
        cells,dk=split_dk(enc(txt(s))); row,col=s['row'],s['col']
        on=len(bytes.fromhex(s['raw_hex']))
        if len(cells)>s['max_bytes']: raise SystemExit('%s too long'%s['id'])
        w=max(on,len(cells))
        m[row*32+col:row*32+col+w]=(cells+bytes(w))[:w]
        if row:
            prev=m[(row-1)*32+col:(row-1)*32+col+w]
            if all(v in (0,0x7c,0x7d) for v in prev): m[(row-1)*32+col:(row-1)*32+col+w]=(dk+bytes(w))[:w]
            elif any(dk): raise SystemExit('%s: row above is not a dakuten row'%s['id'])
    if bytes(m)==data: continue
    typ=orig[b*0x4000+src-0x4000]
    if typ&0xf==3: typ=(typ&0xf0)|2
    c=compress(bytes(m),typ)
    # verify
    tmp=bytearray(0x4000*2); tmp[0x4000:0x4000+len(c)]=c
    assert decompress(bytes(tmp),1,0x4000)[0][:len(m)]==bytes(m), 'codec self-test failed'
    for fb,(p0,p1) in FREE_GFX.items():
        if p1-p0>=len(c):
            o=fb*0x4000+p0-0x4000; rom[o:o+len(c)]=c
            rom[r]=fb; rom[r+1]=p0&0xff; rom[r+2]=p0>>8
            FREE_GFX[fb][0]+=len(c); print('tilemap %02x relocated -> %02x:%04x (%d bytes)'%(idx,fb,p0,len(c))); break
    else: raise SystemExit('no gfx space')
# header checksum
cs=0
for i in range(0x134,0x14d): cs=(cs-rom[i]-1)&0xff
rom[0x14d]=cs
g=0
for i,v in enumerate(rom if bytes(rom)!=orig else b''):
    if i not in (0x14e,0x14f): g+=v
if bytes(rom[:0x14e])+bytes(rom[0x150:])!=orig[:0x14e]+orig[0x150:]: g&=0xffff; rom[0x14e]=g>>8; rom[0x14f]=g&0xff
open(out,'wb').write(rom)
used=sum(x[2] for x in report)
print('dialogue bytes %d; last pos %04x (region %d)'%(used,pos,ri))
