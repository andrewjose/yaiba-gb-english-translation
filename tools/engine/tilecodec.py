"""Tilemap codec subset (modes 0/1), copied from work/re/tools/insert.py."""
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
