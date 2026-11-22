# free space map: runs (>=64 bytes) of 0x00 or 0xFF per bank
import sys
rom=open(sys.argv[1],'rb').read(); MIN=int(sys.argv[2]) if len(sys.argv)>2 else 64
tot={}
for bank in range(len(rom)//0x4000):
    b=rom[bank*0x4000:(bank+1)*0x4000]; i=0; runs=[]
    while i<len(b):
        v=b[i]
        if v in (0,0xff):
            j=i
            while j<len(b) and b[j]==v: j+=1
            if j-i>=MIN: runs.append((i,j-i,v))
            i=j
        else: i+=1
    base=0 if bank==0 else 0x4000
    tot[bank]=sum(r[1] for r in runs)
    print('bank %02x total %5d: '%(bank,tot[bank])+', '.join('%04x-%04x(%d,%02x)'%(base+s,base+s+n-1,n,v) for s,n,v in runs))
