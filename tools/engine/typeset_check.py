#!/usr/bin/env python3
"""Typesetting report + contact sheet for the Yaiba VWF text.
usage: typeset_check.py [--tl out_all.json] [--override x.json] [--sheet shots/typeset_contact.png]
Lists, per dialogue page: line count, per-line width/slack, overflow, stranded last word, hyphenated
breaks, auto page splits. Renders every page with the real VWF glyphs/advances in its box geometry."""
import os,sys,json,argparse
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..')
sys.path.insert(0,HERE)
from textfit import layout,width,Overflow,W as ADV
from build import GEO,RIVAL_LINES,STRINGS
from PIL import Image,ImageDraw
VWF=open(os.path.join(ROOT,'font','vwf.bin'),'rb').read()
def render_page(lines,tiles,nlines,stride_rows=1,scale=3):
    w,h=tiles*8,nlines*8*stride_rows
    im=Image.new('L',(w+4,h+4),255); px=im.load()
    for x in range(w+4): px[x,0]=px[x,h+3]=0
    for y in range(h+4): px[0,y]=px[w+3,y]=0
    for li,l in enumerate(lines):
        pen=1; y0=2+li*8*stride_rows
        for ch in l:
            g=VWF[(ord(ch)-32)*8:(ord(ch)-32)*8+8]
            for r in range(8):
                for b in range(8):
                    if g[r]&(0x80>>b) and pen+b<w: px[2+pen+b,y0+r]=0
                    elif g[r]&(0x80>>b): px[2+pen+b if 2+pen+b<w+4 else w+3,y0+r]=128   # overflow marker
            pen+=ADV[ch]
    return im.resize((im.width*scale,im.height*scale),Image.NEAREST)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tl',default='/root/gbtl/yaiba/work/tl/out_all.json')
    ap.add_argument('--override'); ap.add_argument('--sheet',default=os.path.join(ROOT,'shots','typeset_contact.png'))
    a=ap.parse_args()
    tl={e['id']:e['en'] for e in json.load(open(a.tl))}
    if a.override: tl.update(json.load(open(a.override)))
    S=json.load(open(STRINGS)); tiles={'chapter_intro':12,'powerup':12,'chapter_end':14,'rival':15}
    problems=0; cells=[]
    for s in S:
        if s['kind'] not in ('single','multi'): continue
        blk=s['block']; maxw,maxl,canpage=GEO[blk]
        if blk=='rival': maxl=RIVAL_LINES[s['id']]
        try: pages,notes=layout(tl[s['id']],maxw,maxl if canpage else 99)
        except Overflow as e: print('%-18s OVERFLOW %s'%(s['id'],e)); problems+=1; continue
        for pi,p in enumerate(pages):
            flags=[]
            if len(p)>maxl: flags.append('TOO MANY LINES %d>%d'%(len(p),maxl))
            if len(p)>1 and len(p[-1].split())==1 and len(tl[s['id']].split())>1: flags.append('stranded last word')
            if any(l.endswith('-') and not l.endswith(' -') for l in p[:-1]): flags.append('hyphen break')
            ws=[width(l) for l in p]
            if any(x>maxw for x in ws): flags.append('OVER WIDTH')
            print('%-18s p%d %d lines  widths %s  max %d%s'%(s['id'],pi+1,len(p),ws,maxw,('  ** '+', '.join(flags)) if flags else ''))
            problems+=any(f.isupper() for f in flags)
            cells.append(('%s p%d'%(s['id'],pi+1),render_page(p,tiles[blk],maxl if blk!='rival' else 3,2 if blk=='rival' else 1)))
        for n in notes: print('%-18s note: %s'%(s['id'],n))
    # contact sheet
    cw=max(c[1].width for c in cells)+20; ch=max(c[1].height for c in cells)+30; cols=4
    sh=Image.new('L',(cols*cw,((len(cells)+cols-1)//cols)*ch),255); d=ImageDraw.Draw(sh)
    for i,(t,im) in enumerate(cells):
        x,y=(i%cols)*cw+10,(i//cols)*ch+4; d.text((x,y),t,fill=0); sh.paste(im,(x,y+14))
    os.makedirs(os.path.dirname(a.sheet),exist_ok=True); sh.save(a.sheet)
    print('pages %d, hard problems %d, sheet %s'%(len(cells),problems,a.sheet))
    sys.exit(1 if problems else 0)
if __name__=='__main__': main()
