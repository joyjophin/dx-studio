"""Regenerate the derived images after swapping a photo in assets/img/.

Usage:  python3 scripts/prepare_images.py <project> name1 name2 ... [--blur name]
(images live in <project>/assets/img/<name>.png). Run it again whenever you swap a photo.
It resizes them, rebuilds aurora_blur.png (used for the glass / backdrop effects) and the *_deut.png red-green
colour-blindness simulations (Machado et al. 2009, deuteranopia, severity 1.0) used in the "color as the only signal" chapter.
"""
import os
import numpy as np
from PIL import Image, ImageFilter
import sys
args = [a for a in sys.argv[1:] if not a.startswith('--')]
if not args: sys.exit(__doc__)
D = os.path.join(args[0], 'assets', 'img'); NAMES = args[1:] or [f[:-4] for f in os.listdir(D) if f.endswith('.png') and '_' not in f]
BLUR = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == '--blur' and i + 1 < len(sys.argv)]
M = np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]])
def lin(c): return np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
def gam(c): return np.where(c <= 0.0031308, c*12.92, 1.055*np.power(np.clip(c, 0, 1), 1/2.4) - 0.055)
for name in NAMES:
    path = os.path.join(D, f'{name}.png'); im = Image.open(path).convert('RGB')
    if max(im.size) > 1600: im.thumbnail((1600, 1600), Image.LANCZOS); im.save(path)
    a = np.asarray(im, dtype=float)/255
    Image.fromarray((np.clip(gam(np.clip(lin(a) @ M.T, 0, 1)), 0, 1)*255).astype('uint8')).save(os.path.join(D, f'{name}_deut.png'))
for b in BLUR: Image.open(os.path.join(D, f'{b}.png')).filter(ImageFilter.GaussianBlur(28)).save(os.path.join(D, f'{b}_blur.png'))
print('images ready')
