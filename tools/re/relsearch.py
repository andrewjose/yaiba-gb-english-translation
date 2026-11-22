import sys
SEION="あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
rom=open(sys.argv[1],'rb').read()
def rs(word,order=SEION):
    idx=[order.index(c) for c in word]
    d=[(b-a)%256 for a,b in zip(idx,idx[1:])]
    out=[]
    for o in range(len(rom)-len(d)):
        if all((rom[o+k+1]-rom[o+k])%256==d[k] for k in range(len(d))):
            out.append((hex(o),hex((rom[o]-idx[0])%256)))
    return out
for w in sys.argv[2:]: print(w,rs(w)[:20])
