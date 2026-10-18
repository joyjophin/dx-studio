"""dx_studio.captions: phrase captions on a rounded backing, one highlighted phrase at most."""
from functools import lru_cache
from .core import *
from .text import tw, text
from .draw import rrect, fillp, stroke

def wrap_words(words, size, maxw):
    lines = [[]]; sp = tw(' ', size, 'semi')
    for wd in words:
        trial = lines[-1]+[wd]
        wsum = sum(tw(x, size, 'semi') for x in trial)+sp*(len(trial)-1)
        if lines[-1] and wsum > maxw: lines.append([wd])
        else: lines[-1] = trial
    return lines

@lru_cache(128)
def caption_layout(txt, hl, size=50, maxw=720):
    words = txt.split(' ')
    hlset = set()
    if hl and hl in txt:                     # a highlight that no longer matches the text is ignored
        start = txt.index(hl); end = start+len(hl); pos = 0
        for i, w in enumerate(words):
            if pos < end and pos+len(w) > start: hlset.add(i)
            pos += len(w)+1
    lines = wrap_words(words, size, maxw)
    if len(lines) == 2 and len(lines[1]) == 1 and len(words) > 3:  # avoid an orphan word
        lines = [words[:len(words)//2+1], words[len(words)//2+1:]]
    return size, lines, hlset

def prepare(caps):
    """adds prev_gap / next_gap so back-to-back captions swap without flicker"""
    for i, c in enumerate(caps):
        c['prev_gap'] = c['start']-caps[i-1]['show_end'] if i else 1
        c['next_gap'] = caps[i+1]['start']-c['show_end'] if i+1 < len(caps) else 1
    return caps

def draw_captions(c, t, caps, cx=540, cy=1462, backing=(0.094, 0.059, 0.169, 1), edge=None, color=WHITE, highlight=None, size=50, maxw=720, maxh=None):
    edge = edge or highlight or color
    highlight = highlight or color
    for cap in caps:
        s0, s1 = cap['start'], cap['show_end']
        if not (s0-0.001 <= t < s1): continue
        prev_gap = cap.get('prev_gap', 1); next_gap = cap.get('next_gap', 1)
        fin = P(t, s0, s0+0.12, lin) if prev_gap > 0.05 else 1.0
        fout = (1-P(t, s1-0.1, s1, lin)) if next_gap > 0.05 else 1.0
        a = fin*fout
        dy = 8*(1-P(t, s0, s0+0.16)) if prev_gap > 0.05 else 0
        size_, lines, hlset = caption_layout(cap['text'], cap.get('hl'), size, maxw)
        while maxh and size_ > 4 and (1.28*len(lines)+.64)*size_ > maxh:
            size_,lines,hlset=caption_layout(cap['text'],cap.get('hl'),size_-1,maxw)
        sp = tw(' ', size_, 'semi'); lh = size_*1.28; pad=size_*.32
        widths = [sum(tw(w, size_, 'semi') for w in L)+sp*(len(L)-1) for L in lines]
        bw = max(widths)+size_*1.2; bh = lh*len(lines)+2*pad
        bx = cx-bw/2; by = cy-bh/2+dy
        rrect(c, bx, by, bw, bh, size_*.48); fillp(c, backing, 0.93*a); stroke(c, edge, 1.5, 0.22*a)
        wi = 0
        for li, L in enumerate(lines):
            x = cx-widths[li]/2; y = by+pad+lh*li+lh/2+size_*0.36
            for w in L:
                timed=cap.get('words',[])
                active=next((index for index,word in enumerate(timed) if word['start']<=t<word['end']),None) if cap.get('word_highlight') else None
                col = highlight if (wi==active if cap.get('word_highlight') else wi in hlset) else color
                wd = text(c, w, x, y, size_, 'semi', col, a)
                x += wd+sp; wi += 1
