"""dx_studio.core: time, easing and colour helpers shared by every scene."""
import math
PI = math.pi

def hexc(h, a=1.0):
    h = h.lstrip('#'); return (int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255, a)

WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)

# ---- easing: every animation is "value goes from A to B between time X and Y"
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x

def eo(x): x = clamp(x); return 1-(1-x)**3

def eio(x): x = clamp(x); return 4*x**3 if x < .5 else 1-(-2*x+2)**3/2

def ei(x): x = clamp(x); return x**3

def lin(x): return clamp(x)

def P(t, a, b, f=eo): return f((t-a)/(b-a))

def lerp(a, b, u): return a+(b-a)*u

def mixc(c1, c2, u): return tuple(lerp(c1[i], c2[i], u) for i in range(4))

def window(t, a, b, c, d, f=eo):  # rise a..b, fall c..d
    return P(t, a, b, f)*(1-P(t, c, d, f))

def back_ease(x, s=1.7):
    x = clamp(x); return 1 + (s+1)*(x-1)**3 + s*(x-1)**2

def hex_of(col):
    return '#%02X%02X%02X' % tuple(int(round(v*255)) for v in col[:3])
