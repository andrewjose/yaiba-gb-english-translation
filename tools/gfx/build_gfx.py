#!/usr/bin/env python3
"""build_gfx.py in.gb out.gb --orig pristine.gb   (or $YAIBA_ROM)
Applies the English graphics of the Yaiba GB translation on top of an input ROM (e.g. the text build).
- Compressed entries (records at bank0 $3DE5) #00 title tiles, #08 chapter-card tiles, #09 chapter-card map,
  #0E sword-select tiles, #17 game-over tiles are rebuilt, recompressed and placed in bank $18 (512 KB ROM);
  only the record's bank/src bytes are changed.
- Raw tiles edited in place: bank 7 $4480-$47BF/$4800-$4BFF (dragon-orb icon, chapter numerals, orb kanji),
  bank 2 $4D00-$4D8F (HUD LIFE/KI), bank 6 $62C0-$63FF and $66C0-$67FF (pickup orbs).
- Boss-card names in banks 0E (asset repack, offsets table at 0E:$4000).
Every input byte that is changed is first asserted to equal the pristine ROM."""
import os,sys,hashlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from codec import decompress_at,compress
import designs as D

GFX_BANK=0x18           # owned banks: $18-$1F
REC=0x3de5
def main():
    args=sys.argv[1:]
    orig_path=os.environ.get('YAIBA_ROM')
    if '--orig' in args:
        i=args.index('--orig'); orig_path=args[i+1]; del args[i:i+2]
    inp,outp=args
    if not orig_path: raise SystemExit('build_gfx.py: --orig (or $YAIBA_ROM) is required')
    orig=open(orig_path,'rb').read()
    assert hashlib.md5(orig).hexdigest()=='7d76d2a9eaada93dc846efe1b2a815cc','pristine ROM MD5 mismatch'
    rom=bytearray(open(inp,'rb').read())
    if len(rom)==0x40000:
        rom+=b'\xff'*0x40000; rom[0x148]=4
    assert len(rom)==0x80000 and rom[0x148]==4,'need 256 KB or 512 KB input'

    def orig_entry(i):
        o=REC+i*5; b,s=orig[o],orig[o+1]|orig[o+2]<<8
        return decompress_at(orig,b*0x4000+s-0x4000)[0], orig[b*0x4000+s-0x4000]
    def cur_entry(i):
        o=REC+i*5; b,s=rom[o],rom[o+1]|rom[o+2]<<8
        assert rom[o+3:o+5]==orig[o+3:o+5],'record %02x dst changed'%i
        d,_=decompress_at(bytes(rom),b*0x4000+s-0x4000)
        od,typ=orig_entry(i)
        assert d==od,'entry %02x in input differs from the original graphics'%i
        return d,typ

    t00,ty00=cur_entry(0x00); m01,_=cur_entry(0x01)
    t08,ty08=cur_entry(0x08); m09,ty09=cur_entry(0x09)
    t0e,ty0e=cur_entry(0x0e)
    t17,ty17=cur_entry(0x17); m18,_=cur_entry(0x18)

    new={}
    new[0x00]=(D.title(t00,m01),ty00)
    nt8,nm9,_=D.card(t08,m09); new[0x08]=(nt8,ty08); new[0x09]=(nm9,ty09)
    new[0x0e]=(D.orb_tiles(t0e,[0xe0,0xe2,0xe4,0xe6,0xe8],D.ORB_LABELS,lambda c:c-0x80),ty0e)
    px=D.gameover(t17,m18,t00); new[0x17]=(D.gameover_apply(t17,m18,px),ty17)

    # place recompressed entries in bank $18
    base=GFX_BANK*0x4000; p=base
    for i in sorted(new):
        data,typ=new[i]
        c=compress(data,typ)
        assert decompress_at(c,0)[0]==data
        assert all(v==0xff for v in rom[p:p+len(c)]),'bank %02x not free at %05x'%(GFX_BANK,p)
        rom[p:p+len(c)]=c
        o=REC+i*5; a=0x4000+(p-base)
        rom[o]=GFX_BANK; rom[o+1]=a&0xff; rom[o+2]=a>>8
        print('entry %02x -> %02x:%04x (%d bytes, orig %d)'%(i,GFX_BANK,a,len(c),len(compress(orig_entry(i)[0],typ))))
        p+=len(c)
    assert p<=base+0x4000

    # raw edits
    def patch(off,newb):
        for k,v in enumerate(newb):
            if rom[off+k]!=v:
                assert rom[off+k]==orig[off+k],'raw byte %05x was changed by an earlier build step'%(off+k)
                rom[off+k]=v
    b7=bytes(rom[7*0x4000:7*0x4000+0x1000])
    n7=D.numerals(b7)
    n7=D.orb_tiles(n7,[0xa6,0xa8,0xaa,0xac,0xae],D.ORB_LABELS,lambda c:c)
    n7=D.dragon_icon(n7)
    patch(7*0x4000,n7)
    o=7*0x4000+0x2000
    patch(o,D.powerup_icons(bytes(rom[o:o+0x1000])))     # power-up orb icons, bank 7 $6000-$6FFF
    for blk in (0x6000,0x6400):      # two copies of the object-tile set in bank 6 (pickup orbs at tiles 2C-2F/3C-3F)
        o=6*0x4000+blk-0x4000; raw=bytes(rom[o:o+0x400])
        for tl,lab in D.PICKUPS: raw=D.pickup(raw,tl,lab)
        patch(o,raw)
    patch(2*0x4000+0xd00,D.hud(bytes(rom[2*0x4000+0xd00:2*0x4000+0xd90])))

    # boss cards: assets in banks 0E/0F (bank-relative offset table at $4000; bank is hard-coded in bank0 $0411)
    # rebuilt in place when the new stream fits, otherwise appended to the bank's $FF tail and the table repointed
    assets={}
    for bank in (0xe,0xf):
        base=bank*0x4000; n=(orig[base]|orig[base+1]<<8)//2
        assert rom[base:base+2*n]==orig[base:base+2*n],'boss table of bank %02x changed by an earlier step'%bank
        for k in range(n):
            rel=orig[base+2*k]|orig[base+2*k+1]<<8
            d,cl=decompress_at(orig,base+rel)
            assert rom[base+rel:base+rel+cl]==orig[base+rel:base+rel+cl],'boss asset %02x/%d changed'%(bank,k)
            assets[(bank,k)]=(d,cl,rel)
    font=D.boss_font({k:v[0] for k,v in assets.items()})
    # repack each bank's assets contiguously (unchanged ones byte-identical), then repoint the table
    for bank in (0xe,0xf):
        base=bank*0x4000; n=(orig[base]|orig[base+1]<<8)//2
        end=max(assets[(bank,k)][2]+assets[(bank,k)][1] for k in range(n))
        streams=[]
        for k in range(n):
            d,cl,rel=assets[(bank,k)]
            if (bank,k) in D.BOSS_EN:
                c=compress(D.boss_rename(d,font,D.BOSS_EN[(bank,k)]),orig[base+rel])
                assert decompress_at(c,0)[0]==D.boss_rename(d,font,D.BOSS_EN[(bank,k)])
                print('boss %02x/%d %-22s %d bytes (orig %d)'%(bank,k,D.BOSS_EN[(bank,k)],len(c),cl))
            else: c=orig[base+rel:base+rel+cl]
            streams.append(c)
        if all(len(streams[k])==assets[(bank,k)][1] and streams[k]==orig[base+assets[(bank,k)][2]:][:len(streams[k])] for k in range(n)): continue
        p=assets[(bank,0)][2]
        assert p==2*n or p>=2*n
        region_end=0x4000
        total=p+sum(len(c) for c in streams)
        assert all(v==0xff for v in rom[base+end:base+max(end,total)]),'bank %02x tail not free'%bank
        for k in range(n):
            c=streams[k]
            rom[base+p:base+p+len(c)]=c; rom[base+2*k]=p&0xff; rom[base+2*k+1]=p>>8; p+=len(c)
        assert p<=region_end
        # fill the rest of the old asset area + tail with $FF
        for q in range(p,max(end,p)): rom[base+q]=0xff
        print('bank %02x assets repacked, end %04x (orig %04x), free %d bytes'%(bank,0x4000+p,0x4000+end,0x4000-p))

    cs=0
    for i in range(0x134,0x14d): cs=(cs-rom[i]-1)&0xff
    rom[0x14d]=cs
    g=(sum(rom)-rom[0x14e]-rom[0x14f])&0xffff
    rom[0x14e]=g>>8; rom[0x14f]=g&0xff
    open(outp,'wb').write(rom)
    print('wrote',outp,hashlib.md5(rom).hexdigest())
if __name__=='__main__': main()
