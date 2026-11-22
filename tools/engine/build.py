#!/usr/bin/env python3
"""Yaiba English build: VWF engine + fixed 8x8 font + text insertion.
Normally run via the repo-root build.py, which prepares build/work/ (strings, fonts, out_all.json).
usage: build.py --rom orig.gb [--tl out_all.json] [--strings strings.json] [--font-dir DIR] [--rgbds DIR]
                [--out build/work/engine/yaiba_en.gb] [--gfx]
  defaults come from $YAIBA_ROM, $YAIBA_WORK (default <repo>/build/work), $YAIBA_FONT_DIR, $RGBDS_DIR / PATH
  --gfx: chain tools/gfx/build_gfx.py afterwards -> <out>_full.gb
Steps: expand to 512 KB -> fixed 8x8 font over the kana font (bank 2 $4000) -> wrap/encode dialogue into banks $10-$16 ->
bank-1 stubs + repointing -> fixed-font menus/tilemaps -> rgbasm/rgblink -O (src/vwf.asm) -> rgbfix -v."""
import os,sys,json,argparse,subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,'..','..'))
WORK=os.path.abspath(os.environ.get('YAIBA_WORK',os.path.join(REPO,'build','work')))
FONT=os.path.abspath(os.environ.get('YAIBA_FONT_DIR',os.path.join(WORK,'font')))
os.environ['YAIBA_FONT_DIR']=FONT          # textfit/compose read the generated font from here
ORIG=os.environ.get('YAIBA_ROM')
STRINGS=os.environ.get('YAIBA_STRINGS',os.path.join(WORK,'re','strings.json'))
RGB=os.environ.get('RGBDS_DIR','')         # empty: rgbasm/rgblink/rgbfix from PATH
sys.path.insert(0,HERE)
from textfit import layout,width,W as ADV,Overflow
from gfxdec import decompress
# box geometry: (max ink width px, max lines per page, can page)
GEO={'chapter_intro':(12*8-1,8,True),'powerup':(12*8-1,8,True),'chapter_end':(14*8-1,8,True),'rival':(15*8-2,None,False)}   # ending box shows cols 3-17
RIVAL_LINES={'rival_00':3,'rival_01':3,'rival_02':1,'rival_03':2,'rival_04':2}
ORIG_REGIONS=[(0x6baa,0x6d90),(0x6da6,0x7123),(0x75eb,0x7754)]   # bank-1 text regions (stubs go here)
TEXT_BANKS=[(0x10,0x4000,0x8000)]+[(b,0x4000,0x8000) for b in range(0x11,0x17)]
GFX_FREE=[0x17,0x4000,0x8000]     # relocated font-text tilemaps (engine-owned bank $17)
MARGIN=1
# intro crawl: the box shows cols 2-17 [runtime]; lines are precomposed into 16 tiles from col 2, centred
CRAWL_COL=2
# bank $17 layout (must match src/vwf.asm)
CRAWL_PAGE=0x5000; SWORD_TILES=0x5800; ORB_TILES=0x5900
SS_STATIC0,SS_STATIC_END,SS_RES0=0x4a,0x6d,0x6e
SS_SWORD0,SS_ORB0,SS_MOVE0=0x6e,0x73,0x79
# sword-select static labels: id -> (tiles, x0 px, align, first column)
#   labels carry their own colon (it replaces the map's colon tile $DB at col 17 / col 7)
SWSEL_LAYOUT={'sword_select_screen_r02c09':(9,1,'left',9,''),'sword_select_screen_r04c09':(9,1,'left',9,''),
              'sword_select_screen_r09c14':(4,2,'right',14,':'),'sword_select_screen_r10c14':(4,2,'right',14,':'),
              'sword_select_screen_r16c01':(7,3,'right',1,':')}

def off(bank,a): return a if a<0x4000 else bank*0x4000+(a-0x4000)
def load_tbl(path):
    rev={}
    for ln in open(path,encoding='utf-8'):
        ln=ln.rstrip('\n')
        if not ln or ln.startswith('#') or '=' not in ln: continue
        k,v=ln.split('=',1); rev.setdefault(v,int(k,16))
    return rev

def encode_msg(pages):
    out=bytearray()
    for pi,p in enumerate(pages):
        if pi: out.append(0xfe)
        for li,l in enumerate(p):
            if li: out.append(0xff)
            for ch in l:
                c=ord(ch)
                if not 0x20<=c<0x7f: raise SystemExit('non-ASCII char %r'%ch)
                out.append(c)
    out.append(0)
    return bytes(out)

def rival_tiles(lines,start):
    """simulate the engine's packed tile allocation; returns next free tile and max tile used"""
    nxt=start; mx=start
    for l in lines:
        if nxt>=0x80-17: nxt=0x0a          # engine RingWrap
        ls=nxt; pen=MARGIN; col=0; mx=ls
        for ch in l:
            while pen>=8: pen-=8; col+=1
            if ch!=' ': mx=max(mx,ls+col+1)
            pen+=ADV[ch]
        nxt=mx+1
    return nxt,mx

def main():
    ap=argparse.ArgumentParser()
    global ORIG,STRINGS,RGB
    ap.add_argument('--rom',default=ORIG,help='original ROM (MD5 7d76d2a9eaada93dc846efe1b2a815cc)')
    ap.add_argument('--strings',default=STRINGS,help='tools/re/extract.py output')
    ap.add_argument('--rgbds',default=RGB,help='directory with rgbasm/rgblink/rgbfix (default: PATH)')
    ap.add_argument('--tl',default=os.path.join(WORK,'tl','out_all.json'))
    ap.add_argument('--out',default=os.path.join(WORK,'engine','yaiba_en.gb'))
    ap.add_argument('--override',help='JSON {id: en} applied over --tl (test refits)')
    ap.add_argument('--gfx',action='store_true',help='chain the gfx agent build (writes <out stem>_full.gb)')
    a=ap.parse_args()
    if not a.rom: raise SystemExit('build.py: --rom (or $YAIBA_ROM) is required')
    ORIG,STRINGS,RGB=a.rom,a.strings,a.rgbds
    os.makedirs(os.path.dirname(os.path.abspath(a.out)),exist_ok=True)
    tl=json.load(open(a.tl)); tl={e['id']:e['en'] for e in tl} if isinstance(tl,list) else tl
    if a.override: tl.update(json.load(open(a.override)))
    S=json.load(open(STRINGS))
    orig=open(ORIG,'rb').read(); rom=bytearray(orig)+b'\xff'*0x40000; rom[0x148]=4
    # fixed font
    fixed=open(os.path.join(FONT,'fixed.bin'),'rb').read(); rom[off(2,0x4000):off(2,0x4000)+0x800]=fixed   # replaces the kana font in place
    # ---- dialogue
    report=[]; errors=[]
    tb=0; tpos=TEXT_BANKS[0][1]
    def far_put(blob):
        nonlocal tb,tpos
        while tpos+len(blob)>TEXT_BANKS[tb][2]:
            tb+=1; tpos=TEXT_BANKS[tb][1]
            if tb>=len(TEXT_BANKS): raise SystemExit('text banks full')
        b=TEXT_BANKS[tb][0]; p=tpos; rom[off(b,p):off(b,p)+len(blob)]=blob; tpos+=len(blob); return b,p
    for r0,r1 in ORIG_REGIONS:
        for x in range(r0,r1): rom[off(1,x)]=0
    regions=[list(r) for r in ORIG_REGIONS]; ri=0
    def stub_put(blob):
        nonlocal ri
        while regions[ri][0]+len(blob)>regions[ri][1]:
            ri+=1
            if ri>=len(regions): raise SystemExit('bank 1 stub space full')
        p=regions[ri][0]; rom[off(1,p):off(1,p)+len(blob)]=blob; regions[ri][0]+=len(blob); return p
    def put16(loc,v):
        b,ad=loc.split(':'); o=off(int(b,16),int(ad,16)); rom[o]=v&0xff; rom[o+1]=v>>8
    dlg=[s for s in S if s['kind'] in ('single','multi')]
    nxt_tile=1
    for s in dlg:
        blk=s['block']; maxw,maxl,canpage=GEO[blk]
        if s['id'] not in tl: errors.append('%s: no translation'%s['id']); continue
        text=tl[s['id']]
        if blk=='rival': maxl=RIVAL_LINES[s['id']]
        try:
            pages,notes=layout(text,maxw,maxl if canpage else 99)
        except Overflow as e:
            errors.append('%s: %s'%(s['id'],e)); continue
        if not canpage and (len(pages)>1 or len(pages[0])>maxl):
            errors.append('%s: %d lines > %d (rival scene has fixed line slots)'%(s['id'],sum(len(p) for p in pages),maxl))
        flags=0
        if blk=='rival':
            if s['id']=='rival_00': nxt_tile=0x0a; flags=1
            nxt_tile,mx=rival_tiles([l for p in pages for l in p],nxt_tile)
            if mx>0x7f: errors.append('%s: rival scene tile budget exceeded (tile %02X)'%(s['id'],mx))
        msg=encode_msg(pages)
        fb,fp=far_put(msg)
        stub=bytes.fromhex(s['header'])+bytes([fb,fp&0xff,fp>>8,flags])
        sp=stub_put(stub)
        for l in s['ptr_locs']: put16(l,sp)
        report.append({'id':s['id'],'block':blk,'pages':pages,'notes':notes,'maxw':maxw,'maxl':maxl,
                       'far':'%02x:%04x'%(fb,fp),'bytes':len(msg),'stub':'01:%04x'%sp})
    # ---- static/precomposed proportional text (no fixed-pitch text is left in the game)
    from compose import render,to2bpp,text_width
    from tilecodec import compress
    def T(sid):
        if sid not in tl: errors.append('%s: no translation'%sid); return ''
        return tl[sid]
    def safe_render(sid,s,n,x0=1,align='left'):
        try: return render(s,n,x0,align)
        except ValueError as e: errors.append('%s: %s'%(sid,e)); return [bytes(8)]*n
    BLANK=bytes(8)
    # (a) sword select page: codes 4A-6D static text, 6E-72 sword name, 73-78 orb name, 79-7F move name.
    #     bank 2 $4400-$47FF is copied to VRAM $9400 by bank0 $06C3 (codes 40-7F); digits 40-49 stay.
    page={}            # tile bytes -> code
    nextc=[SS_STATIC0]
    def alloc(t):
        if t==BLANK: return 0
        if t not in page:
            if nextc[0]>SS_STATIC_END: errors.append('sword-select static tile budget exceeded'); return 0
            page[t]=nextc[0]; nextc[0]+=1
        return page[t]
    swsel_cells={}     # id -> (row, col, [codes])
    for sid,(n,x0,align,col,suf) in SWSEL_LAYOUT.items():
        tiles=safe_render(sid,T(sid)+suf,n,x0,align)
        swsel_cells[sid]=(col,[alloc(t) for t in tiles],n)
    for t,c in page.items(): o=off(2,0x4000)+c*16; rom[o:o+16]=to2bpp(t)
    for c in range(SS_RES0,0x80): o=off(2,0x4000)+c*16; rom[o:o+16]=bytes(16)
    report.append({'swsel_static_tiles':len(page)})
    # (b) sword names (records 1:$7227) and orb/move names (records 1:$7301): fixed reserved codes in the
    #     VRAM scripts; per-value tile data in bank $17, uploaded by the engine hooks at $0752 / $07C1.
    def field(sid): return [s for s in S if s['id']==sid][0]
    sw=bytearray(6*40)
    for k in range(1,6):
        sid='sword_menu_%02d_990d'%k; s=field(sid)
        tiles=safe_render(sid,T(sid),5,1,'right')
        sw[k*40:k*40+40]=b''.join(tiles)
        o=int(s['off'],16)+3; rom[o:o+6]=bytes([0]+list(range(SS_SWORD0,SS_SWORD0+5)))
        d=int(s['dakuten_off'],16); rom[d+3:d+3+rom[d]]=bytes(rom[d])
        report.append({'id':sid,'block':'sword_menu','precomposed':T(sid)})
    orb=bytearray(10*104)
    for k in range(10):
        so=field('orb_menu_%02d_99aa'%k); sm=field('orb_menu_%02d_9a08'%k)
        to=safe_render(so['id'],T(so['id']),6,1); tm=safe_render(sm['id'],T(sm['id']),7,1)
        orb[k*104:k*104+104]=b''.join(to+tm)
        o=int(so['off'],16)+3; rom[o:o+8]=bytes(list(range(SS_ORB0,SS_ORB0+6))+[0,0])
        n=so['max_bytes']; assert n==8
        o=int(sm['off'],16)+3; n=sm['max_bytes']; rom[o:o+n]=bytes(list(range(SS_MOVE0,SS_MOVE0+7))+[0]*(n-7))
        for x in (so,sm):
            d=int(x['dakuten_off'],16); rom[d+3:d+3+rom[d]]=bytes(rom[d])
            report.append({'id':x['id'],'block':'orb_menu','precomposed':T(x['id'])})
    o=off(0x17,SWORD_TILES); rom[o:o+len(sw)]=sw
    o=off(0x17,ORB_TILES); rom[o:o+len(orb)]=orb
    # (c) intro crawl page: codes 0A-7F precomposed lines (01-03,08,09 = frame tiles, kept); loaded to $9000
    #     by the engine's CrawlFont (hook at $0309 instead of $0A13)
    font0=orig[0x8000:0x8800]
    crawl=bytearray(0x800)
    for c in (1,2,3,8,9): crawl[c*16:c*16+16]=font0[c*16:c*16+16]
    cpage={}; cnext=[0x0a]
    def calloc(t):
        if t==BLANK: return 0
        if t not in cpage:
            if cnext[0]>0x7f: errors.append('intro crawl tile budget exceeded (118 tiles)'); return 0
            cpage[t]=cnext[0]; cnext[0]+=1
        return cpage[t]
    crawl_cells={}
    for s in [s for s in S if s['block']=='intro_scroll']:
        tiles=safe_render(s['id'],T(s['id']),16,0,'center')
        crawl_cells[s['id']]=[calloc(t) for t in tiles]
    for t,c in cpage.items(): crawl[c*16:c*16+16]=to2bpp(t)
    o=off(0x17,CRAWL_PAGE); rom[o:o+0x800]=crawl
    report.append({'crawl_tiles':len(cpage)})
    # (d) tilemaps #07 / #0F
    gpos=GFX_FREE[1]
    for idx in (7,0x0f):
        r=0x3de5+idx*5; b=orig[r]; src=orig[r+1]|orig[r+2]<<8
        data,_=decompress(orig,b,src); m=bytearray(data)
        for s in [s for s in S if s['kind']=='tilemap' and s['map_index']==idx]:
            row,col=s['row'],s['col']
            if idx==7:
                m[row*32+CRAWL_COL:row*32+col+s['max_bytes']]=bytes(col+s['max_bytes']-CRAWL_COL)
                cells=crawl_cells[s['id']]; m[row*32+CRAWL_COL:row*32+CRAWL_COL+16]=bytes(cells)
                c0,c1=CRAWL_COL,col+s['max_bytes']
            else:
                c,cells,n=swsel_cells[s['id']]
                on=len(bytes.fromhex(s['raw_hex']))
                m[row*32+col:row*32+col+on]=bytes(on)          # old kana cells
                m[row*32+c:row*32+c+n]=bytes(cells)
                c0,c1=min(c,col),max(c+n,col+on)
            if row:   # dakuten row above
                prev=m[(row-1)*32+c0:(row-1)*32+c1]
                if all(v in (0,0x7c,0x7d) for v in prev): m[(row-1)*32+c0:(row-1)*32+c1]=bytes(c1-c0)
            report.append({'id':s['id'],'block':s['block'],'precomposed':T(s['id'])})
        typ=orig[off(b,src)]
        if typ&0xf==3: typ=(typ&0xf0)|2
        c=compress(bytes(m),typ)
        tmp=bytearray(0x8000); tmp[0x4000:0x4000+len(c)]=c
        assert decompress(bytes(tmp),1,0x4000)[0][:len(m)]==bytes(m),'codec self-test failed'
        if gpos+len(c)>CRAWL_PAGE: raise SystemExit('tilemap space full')
        o=off(GFX_FREE[0],gpos); rom[o:o+len(c)]=c
        rom[r]=GFX_FREE[0]; rom[r+1]=gpos&0xff; rom[r+2]=gpos>>8
        print('tilemap %02x -> %02x:%04x (%d bytes)'%(idx,GFX_FREE[0],gpos,len(c))); gpos+=len(c)
    if errors:
        print('\n'.join('ERROR '+e for e in errors)); sys.exit(1)
    # ---- assemble + overlay
    bdir=os.path.dirname(os.path.abspath(a.out)); base=os.path.join(bdir,'base.gb')
    open(base,'wb').write(rom)
    obj=os.path.join(bdir,'vwf.o')
    src=os.path.join(HERE,'src')
    subprocess.check_call([os.path.join(RGB,'rgbasm'),'-I',FONT+os.sep,'-o',obj,os.path.join(src,'vwf.asm')],cwd=src)
    subprocess.check_call([os.path.join(RGB,'rgblink'),'-O',base,'-o',a.out,'-m',os.path.join(bdir,'vwf.map'),'-n',os.path.join(bdir,'vwf.sym'),obj])
    subprocess.check_call([os.path.join(RGB,'rgbfix'),'-v','-p','0xff',a.out])
    json.dump(report,open(os.path.join(bdir,'layout.json'),'w'),indent=1)
    out=open(a.out,'rb').read()
    if a.gfx:
        full=os.path.splitext(a.out)[0]+'_full.gb'
        subprocess.check_call([sys.executable,'-I',os.path.join(REPO,'tools','gfx','build_gfx.py'),a.out,full,'--orig',ORIG])
        print('chained gfx build ->',full)
    print('built %s (%d KB); text bank %02x up to %04x; stub space left %s'%(a.out,len(out)//1024,TEXT_BANKS[tb][0],tpos,[hex(r[1]-r[0]) for r in regions]))
if __name__=='__main__': main()
