"""Pixel-width text fitting for the Yaiba VWF: balanced line breaking, sentence-boundary paging,
pyphen hyphenation fallback. Shared by build.py and typeset_check.py."""
import os,json,re
HERE=os.path.dirname(os.path.abspath(__file__))
W=json.load(open(os.path.join(HERE,'..','font','widths.json')))
NBSP=' '
# multi-word names / terms that must never be split across lines (glossary + translation)
NOBREAK=['Yaiba Kurogane','Thunder Orb','Wind Orb','Dragon God Orb','Two-Sword Style','Cross Slash',
         'Cedar Pollen Soldier',"Cedar Pollen Soldier's",'Ki art','Dual mode','The End']
try:
    import pyphen; _HY=pyphen.Pyphen(lang='en_US')
except Exception: _HY=None

def width(s):
    """ink width in px: sum of advances minus the trailing 1 px bearing."""
    s=s.replace(NBSP,' ')
    return max(0,sum(W[c] for c in s)-1) if s else 0

def protect(text):
    for n in sorted(NOBREAK,key=len,reverse=True):
        text=text.replace(n,n.replace(' ',NBSP))
    # never split numbers like "2 orbs"? keep digit groups attached to the next word
    text=re.sub(r'(\b\d+) ',lambda m:m.group(1)+NBSP,text)
    return text

class Overflow(Exception): pass

def _hyphen_split(word,maxw):
    """split an over-wide word with pyphen (>=3 chars each side); returns list of pieces."""
    if _HY is None: raise Overflow('word too wide and no pyphen: %r'%word)
    pieces=[]; rest=word
    while width(rest)>maxw:
        best=None
        for pos in _HY.positions(rest):
            if pos>=3 and len(rest)-pos>=3 and width(rest[:pos]+'-')<=maxw: best=pos
        if best is None: raise Overflow('cannot hyphenate %r into %d px'%(word,maxw))
        pieces.append(rest[:best]+'-'); rest=rest[best:]
    pieces.append(rest); return pieces

def _tokens(para,maxw):
    """words with flag 'hy' if the word is a hyphenated fragment (joins without space)."""
    out=[]
    for w in para.split(' '):
        if not w: continue
        if width(w)<=maxw: out.append((w,False)); continue
        ps=_hyphen_split(w,maxw)
        for i,p in enumerate(ps): out.append((p,i<len(ps)-1))
    return out

def _join(toks):
    s=''
    for i,(w,hy) in enumerate(toks):
        s+=w
        if i<len(toks)-1 and not hy: s+=' '
    return s

def wrap(para,maxw):
    """balanced wrap of one paragraph -> list of lines (NBSP restored to spaces)."""
    toks=_tokens(protect(para),maxw); n=len(toks)
    if n==0: return ['']
    lw=lambda i,j:width(_join(toks[i:j]))
    # greedy line count
    cnt=0;i=0
    while i<n:
        j=i+1
        while j<n and lw(i,j+1)<=maxw: j+=1
        cnt+=1;i=j
    INF=float('inf')
    # DP over exactly `cnt` lines: cost = squared slack (last line weighted 0.5) + penalties
    best={(n,0):(0,None)}
    from functools import lru_cache
    @lru_cache(None)
    def f(i,k):
        if i==n: return (0,None) if k==0 else (INF,None)
        if k==0: return (INF,None)
        res=(INF,None)
        for j in range(i+1,n+1):
            w=lw(i,j)
            if w>maxw: break
            slack=maxw-w
            last=(j==n)
            c=(slack*slack)*(0.5 if last else 1.0)
            if last and j-i==1 and n>1: c+=10**6          # stranded single word
            if toks[j-1][1] and not last: c+=150          # hyphenated break
            if not last and toks[j-1][0].endswith('-') and not toks[j-1][1]: c+=60  # break after hard hyphen
            sub=f(j,k-1)[0]
            if c+sub<res[0]: res=(c+sub,j)
        return res
    lines=[];i=0;k=cnt
    if f(0,cnt)[0]==INF: raise Overflow('no layout for %r'%para)
    while i<n:
        j=f(i,k)[1]; lines.append(_join(toks[i:j]).replace(NBSP,' ')); i=j; k-=1
    return lines

def sentences(text):
    parts=re.split(r'(?<=[.!?])\s+(?=[A-Z"\'(.])',text)
    return [p for p in parts if p]

def layout(text,maxw,maxlines):
    """text: pages separated by blank line ('\\n\\n'), hard breaks '\\n'. Returns list of pages (list of lines)
    and a list of notes (auto page splits)."""
    pages=[];notes=[]
    for ptxt in text.split('\n\n'):
        lines=[]
        for para in ptxt.split('\n'): lines+=wrap(para,maxw)
        if len(lines)<=maxlines: pages.append(lines); continue
        # split at sentence boundaries (hard-break paragraphs kept as units)
        sents=[]
        for para in ptxt.split('\n'): sents+= [(s,True) for s in sentences(para)]
        cur=[]
        def lay(ss): 
            out=[]
            for s in ss: pass
            return wrap(' '.join(ss),maxw) if ss else []
        for s,_ in sents:
            if len(wrap(s,maxw))>maxlines: raise Overflow('sentence longer than a page: %r'%s)
            if cur and len(lay(cur+[s]))>maxlines:
                pages.append(lay(cur)); cur=[s]; notes.append('auto page split before %r'%s[:30])
            else: cur.append(s)
        if cur: pages.append(lay(cur))
    return pages,notes
