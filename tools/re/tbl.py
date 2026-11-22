# yaiba table builder/loader
HIRA="あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
T={0x00:'　',0x04:'‥',0x05:'、',0x06:'ィ',0x07:'ゥ',0x38:'ッ',0x39:'ャ',0x3a:'ュ',0x3b:'ョ',0x3c:'ー',0x3d:'「',0x3e:'」',0x3f:'♥',
   0x78:'っ',0x79:'ゃ',0x7a:'ゅ',0x7b:'ょ',0x7c:'゛',0x7d:'゜',0x7e:'！',0x7f:'？'}
for i,c in enumerate(KATA): T[0x0a+i]=c
for i in range(10): T[0x40+i]=str(i)
for i,c in enumerate(HIRA): T[0x4a+i]=c
for c in (1,2,3,8,9): T[c]='[%02X]'%c
DAK={}
import unicodedata
def combine(s):
    # compose kana+゛/゜ for readability
    out=''
    for ch in s:
        if ch in '゛゜' and out:
            n=unicodedata.normalize('NFC',out[-1]+('゙' if ch=='゛' else '゚'))
            if len(n)==1: out=out[:-1]+n; continue
        out+=ch
    return out
def decode(bs):
    return combine(''.join(T.get(b,'[%02X]'%b) for b in bs))
REV={v:k for k,v in T.items()}
def encode(s):
    import re
    out=bytearray(); i=0
    while i<len(s):
        if s[i]=='[':
            j=s.index(']',i); out.append(int(s[i+1:j],16)); i=j+1; continue
        if s[i]=='\n': out.append(0xff); i+=1; continue
        ch=s[i]
        if ch in REV: out.append(REV[ch])
        else:
            dcmp=unicodedata.normalize('NFD',ch)
            if len(dcmp)==2 and dcmp[0] in REV:
                out.append(REV[dcmp[0]]); out.append(0x7c if dcmp[1]=='゙' else 0x7d)
            else: raise ValueError('unencodable %r'%ch)
        i+=1
    return bytes(out)
