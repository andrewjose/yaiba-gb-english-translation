# Yaiba GB graphics codec (bank0 $3B7E). decompress() is an independent copy of tools/re/gfxdec.py
# logic operating on a flat buffer; compress() is its inverse, choosing the smallest mode per block.
# Stream: type(1) blocks(2 LE) ctl_off(2 LE, from stream start) | data | ctl
# S = 16<<(type&F) bytes per block. ctl: 2 bits/block LSB-first (type&F != 0) or 1 bit/block (1->mode1, 0->mode2).
# mode0 zeros | mode1 bitmask(2<<n bytes, LSB-first)+literals | mode2 as 1 then per-tile row XOR undo
# mode3: raw S bytes (type<0x10) or as 1 then running XOR undo.
import os,sys

def decompress_at(buf,p):
    """decompress stream at flat offset p of buf -> (data, compressed_len)"""
    typ=buf[p]; blocks=buf[p+1]|buf[p+2]<<8; ctl=p+(buf[p+3]|buf[p+4]<<8)
    n=typ&0xf; S=16<<n; hl=p+5; c95=1; out=bytearray(); maxp=hl
    assert n<3
    for blk in range(blocks):
        if n:
            if c95==5: ctl+=1; c95=1
            mode=(buf[ctl]>>(2*(c95-1)))&3; c95+=1
        else:
            if c95==9: ctl+=1; c95=1
            mode=1 if (buf[ctl]>>(c95-1))&1 else 2; c95+=1
        if mode==0: out+=bytes(S); continue
        if mode==3 and typ<0x10: out+=buf[hl:hl+S]; hl+=S; continue
        d=2<<n; mask=buf[hl:hl+d]; hl+=d; b=bytearray()
        for k in range(S):
            if (mask[k>>3]>>(k&7))&1: b.append(buf[hl]); hl+=1
            else: b.append(0)
        b+=bytes(64)
        if mode==2:
            ts=(0,) if n==0 else ((0,16) if n==1 else (0,16,32,48))
            for i in range(0,14,2):
                for t in ts: b[t+i+2]^=b[t+i]; b[t+i+3]^=b[t+i+1]
        elif mode==3:
            c=0x0f if n==0 else (0x3f if n&2 else 0x1f)
            for i in range(c): b[i+1]^=b[i]
        out+=b[:S]
    end=max(hl,ctl+1)
    return bytes(out),end-p

def _mask_enc(blk):
    d=(len(blk)+7)//8; mask=bytearray(d); lits=bytearray()
    for i,v in enumerate(blk):
        if v: mask[i>>3]|=1<<(i&7); lits.append(v)
    return bytes(mask)+bytes(lits)

def encode_block(blk,typ,mode):
    n=typ&0xf; S=16<<n
    if mode==0: return b'' if not any(blk) else None
    if mode==3 and typ<0x10: return bytes(blk)
    e=bytearray(blk)
    if mode==2:
        ts=(0,) if n==0 else ((0,16) if n==1 else (0,16,32,48))
        for t in ts:
            for i in range(12,-1,-2):
                e[t+i+2]^=blk[t+i]; e[t+i+3]^=blk[t+i+1]
    elif mode==3:
        c=0x0f if n==0 else (0x3f if n&2 else 0x1f)
        for i in range(c): e[i+1]=blk[i+1]^blk[i]
    return _mask_enc(e)

def compress(data,typ):
    n=typ&0xf; S=16<<n; assert n<3 and len(data)%S==0
    nb=len(data)//S; stream=bytearray(); codes=[]
    modes=(1,2) if n==0 else (0,1,2,3)
    for k in range(nb):
        blk=data[k*S:(k+1)*S]; best=None
        for m in modes:
            e=encode_block(blk,typ,m)
            if e is None: continue
            if best is None or len(e)<len(best[1]): best=(m,e)
        codes.append(best[0]); stream+=best[1]
    ctl=bytearray()
    if n:
        for k in range(0,nb,4): ctl.append(sum(c<<(2*j) for j,c in enumerate(codes[k:k+4])))
    else:
        for k in range(0,nb,8): ctl.append(sum((1 if c==1 else 0)<<j for j,c in enumerate(codes[k:k+8])))
    out=bytes([typ,nb&0xff,nb>>8])+(5+len(stream)).to_bytes(2,'little')+bytes(stream)+bytes(ctl)
    assert decompress_at(out,0)[0]==bytes(data)
    return out

if __name__=='__main__':
    from gfxdec import decompress as refdec
    rom=open(sys.argv[1],'rb').read()
    for i in range(0x1d):
        o=0x3de5+i*5; b,s=rom[o],rom[o+1]|rom[o+2]<<8; p=b*0x4000+s-0x4000
        d,cl=decompress_at(rom,p); r,_=refdec(rom,b,s); assert d==r
        c=compress(d,rom[p])
        print('%02x type %02x orig %5d mine %5d identical=%s'%(i,rom[p],cl,len(c),c==rom[p:p+cl]))
