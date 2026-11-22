# Decompressor for Yaiba's graphics/tilemap codec (bank0 $3B7E). Table of 5-byte records at $3DE5:
# [bank][src lo hi][dst lo hi]. Stream header: type(1) blocks(2 LE) ctl_off(2 LE, from header start).
# Block size S = 16<<(type&0xF). Per block a mode from ctl stream (2-bit LSB-first if type&0xF else 1-bit: 1->mode1, 0->mode2).
# mode0 zeros; mode1 bitmask literal; mode2 bitmask + row-xor (tile bitplanes); mode3 raw (type<0x10) or bitmask+running xor.
import sys
def entries(rom):
    out=[]
    for i in range(0x100):
        o=0x3de5+i*5
        if o+5>0x4000: break
        b,s,dst=rom[o],rom[o+1]|rom[o+2]<<8,rom[o+3]|rom[o+4]<<8
        out.append((i,b,s,dst))
    return out
def off(bank,a): return bank*0x4000+a-0x4000 if a>=0x4000 else a
def decompress(rom,bank,src):
    p=off(bank,src)
    typ=rom[p]; blocks=rom[p+1]|rom[p+2]<<8; ctl=p+(rom[p+3]|rom[p+4]<<8)
    hl=p+5; n=typ&0xf; S=(8<<(n+1))&0xff or 256
    if n>=4: raise ValueError('n')
    c95=1; out=bytearray(); carry=0
    hram=[0]*16  # ff98..ffa7
    for blk in range(blocks):
        # get mode
        if n:
            if c95==5: ctl+=1; c95=1
            mode=(rom[ctl]>>(2*(c95-1)))&3; c95+=1
        else:
            if c95==9: ctl+=1; c95=1
            mode=1 if (rom[ctl]>>(c95-1))&1 else 2; c95+=1
        if mode==0: out+=bytes(S); continue
        if mode==3 and typ<0x10: out+=rom[hl:hl+S]; hl+=S; continue
        # bitmask unpack
        d=2<<n
        for k in range(d): hram[k]=rom[hl+k]
        hl+=d
        buf=bytearray()
        carry=0
        for k in range(S):
            for idx in range(7,-1,-1):  # ff9f down to ff98
                v=hram[idx]; nc=v&1; hram[idx]=(v>>1)|(carry<<7); carry=nc
            if carry: buf.append(rom[hl]); hl+=1
            else: buf.append(0)
        buf+=bytes(64)
        if mode==2:
            if n==0:
                for i in range(0,14,2): buf[i+2]^=buf[i]; buf[i+3]^=buf[i+1]
            elif not (n&2):
                for i in range(0,14,2):
                    for t in (0,16): buf[t+i+2]^=buf[t+i]; buf[t+i+3]^=buf[t+i+1]
            else:
                for i in range(0,14,2):
                    for t in (0,16,32,48): buf[t+i+2]^=buf[t+i]; buf[t+i+3]^=buf[t+i+1]
        elif mode==3:
            c=0x0f if n==0 else (0x3f if n&2 else 0x1f)
            for i in range(c): buf[i+1]^=buf[i]
        out+=buf[:S]
    return bytes(out), hl-p
if __name__=='__main__':
    rom=open(sys.argv[1],'rb').read()
    for i,b,s,dst in entries(rom):
        if b>=16 or not(0x4000<=s<0x8000): break
        try:
            data,clen=decompress(rom,b,s)
            print('%02x bank %02x src %04x (off %05x) dst %04x type %02x out %d'%(i,b,s,off(b,s),dst,rom[off(b,s)],len(data)))
        except Exception as e: print(i,'err',e)
