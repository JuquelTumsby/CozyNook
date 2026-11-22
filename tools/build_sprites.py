#!/usr/bin/env python3
"""
CozyNook sprite builder
=======================
Builds the layered pixel-art sprite sheets in assets/sprites/ from the
hand-drawn pixel grids in this file.

Run it from the project folder:   python3 tools/build_sprites.py

How the grids work
------------------
* Every character cell is 48 x 64 pixels, every cat cell is 40 x 34.
* Shapes are built from simple geometry (ellipses, rectangles) plus
  hand-placed pixels, then outlined and shaded automatically.
* A grid written with 16 characters per line is a HALF grid: it is mirrored
  to make a symmetric 32-pixel-wide shape (great for heads, bodies, outfits).
* Each "part" gets an automatic dark outline and automatic shading
  (light from the top-left), which keeps every layer consistent.
* Colours marked "recolourable" are KEY colours.  assets/sprites.js swaps
  them in the browser for the colours the player picks (skin tone, hair,
  outfit, cat coat).  They are also the default palette, so the PNGs look
  right on their own.
"""
from PIL import Image
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'sprites')

W, H = 48, 64          # character cell
CW, CH = 40, 34        # cat cell

PAL = {
    # outline
    'O': '#3a2630',
    # skin (recolourable)
    's': '#efbd9d', 'S': '#d9977a', 'q': '#f9d8c0', 'b': '#ec8f8f',
    # hair (recolourable)
    'h': '#67483d', 'H': '#4a3129', 'l': '#8f6a58',
    # outfit cloth (recolourable)
    'c': '#91a477', 'C': '#6f8659', 'L': '#b4c79b',
    # cat fur (recolourable)
    'f': '#f2a65a', 'F': '#c97a3a', 'g': '#ffd09a', 'd': '#b0612c', 'z': '#fff3e2', 'Z': '#e8d2bd',
    # fixed colours
    'p': '#4d5f93', 'P': '#3b4a78',            # denim
    'k': '#6b4434', 'K': '#94634c',            # shoes
    'w': '#fff6e8', 'W': '#e0cfc0',            # white cloth
    'e': '#2b1f2a', 'm': '#b2505e', 't': '#ef8a95',
    'r': '#ec5f7e', 'R': '#b8405c',            # red / pink
    'y': '#f7d154', 'Y': '#d39b2c',            # yellow
    'n': '#2f3350', 'N': '#8c9bd3',            # sunglasses
    'v': '#8e78bd', 'V': '#66539a',            # headphones
    'u': '#f6a7b8', 'U': '#e07b95',            # flower petals
    'i': '#ffffff',                             # pure sparkle
    'x': '#7cc4e8', 'X': '#4f97c2',            # light blue (tears, zz)
    'j': '#6d4c6b',                             # lower iris
}
# fill colour -> (shade, light or None)
SHADE = {'s': ('S', None), 'h': ('H', 'l'), 'c': ('C', 'L'), 'p': ('P', None),
         'k': ('k', 'K'), 'w': ('W', None), 'v': ('V', None), 'r': ('R', None),
         'y': ('Y', None), 'u': ('U', None), 'f': ('F', 'g'), 'z': ('Z', None)}


def hex2rgba(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def grid(rows, start=0, width=W, height=H):
    """Turn a list of strings into a full width x height grid of chars."""
    g = [['.'] * width for _ in range(height)]
    for j, line in enumerate(rows):
        y = start + j
        if len(line) == width // 2:
            line = line + line[::-1]
        if len(line) != width:
            raise ValueError(f'row {y} has width {len(line)}: {line!r}')
        for x, ch in enumerate(line):
            if ch != '.':
                g[y][x] = ch
    return g


def outline(g, shade=True, light=True):
    h, w = len(g), len(g[0])
    filled = lambda x, y: 0 <= x < w and 0 <= y < h and g[y][x] != '.'
    out = [row[:] for row in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] == '.':
                continue
            if not all(filled(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'O'
    if shade:
        res = [row[:] for row in out]
        for y in range(h):
            for x in range(w):
                ch = out[y][x]
                if ch not in SHADE:
                    continue
                sh, li = SHADE[ch]
                isO = lambda xx, yy: 0 <= xx < w and 0 <= yy < h and out[yy][xx] == 'O'
                if isO(x + 1, y) or isO(x, y + 1):
                    res[y][x] = sh
                elif light and li and (isO(x - 1, y) or isO(x, y - 1)):
                    res[y][x] = li
        out = res
    return out


def stack(*layers):
    h, w = len(layers[0]), len(layers[0][0])
    out = [['.'] * w for _ in range(h)]
    for g in layers:
        for y in range(h):
            for x in range(w):
                if g[y][x] != '.':
                    out[y][x] = g[y][x]
    return out


def put(g, pts, ch):
    for x, y in pts:
        g[y][x] = ch
    return g


def mirror_pts(pts, width=W):
    return pts + [(width - 1 - x, y) for x, y in pts]


def empty(width=W, height=H):
    return [['.'] * width for _ in range(height)]


def flip(g):
    return [row[::-1] for row in g]

# ---------------------------------------------------------------- shape helpers
CX = (W - 1) / 2      # horizontal centre (23.5)


def recolor(g, pts, ch):
    """Like put(), but only paints pixels that are already part of the shape."""
    for x, y in pts:
        if g[y][x] not in ('.', 'O'):
            g[y][x] = ch
    return g


def shape(test, ch, w=W, h=H):
    g = empty(w, h)
    for y in range(h):
        for x in range(w):
            if test(x, y):
                g[y][x] = ch
    return g


def inell(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def sym(test, w=W):
    """Mirror a left-side test to both sides."""
    return lambda x, y: test(x, y) or test(w - 1 - x, y)


def stamp(g, x0, y0, rows, mapping=None):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.':
                g[y0 + j][x0 + i] = mapping.get(ch, ch) if mapping else ch
    return g

# ---------------------------------------------------------------- BODY (48 x 64)
HEAD_T = lambda x, y: inell(x, y, CX, 17, 14.6, 13.2)
EAR_T = sym(lambda x, y: inell(x, y, 8.6, 19.5, 2.2, 3.0))
NECK_T = lambda x, y: 21 <= x <= 26 and 28 <= y <= 33
TORSO_T = lambda x, y: 31 <= y <= 47 and abs(x - CX) <= 7.5
LEG_T = sym(lambda x, y: 46 <= y <= 58 and 18 <= x <= 22)


def arm_test(top=32, bottom=47):
    def t(x, y):
        if not (top <= y <= bottom):
            return False
        sh = (y - top) // 8
        return 12 - sh <= x <= 15 - sh
    return sym(t)


HAND_T = sym(lambda x, y: inell(x, y, 12.2, 46.5, 2.4, 2.4))


def body_layer():
    g = stack(outline(shape(NECK_T, 's')), outline(shape(TORSO_T, 's')), outline(shape(LEG_T, 's')),
              outline(shape(arm_test(), 's')), outline(shape(HAND_T, 's'), light=False),
              outline(shape(EAR_T, 's'), light=False), outline(shape(HEAD_T, 's'), light=False))
    put(g, mirror_pts([(8, 19), (8, 20)]), 'S')               # inner ear
    put(g, mirror_pts([(21, 31), (22, 31), (23, 31)]), 'S')  # shadow under the chin
    put(g, [(13, 9), (14, 8), (15, 8), (12, 10)], 'q')       # forehead shine
    return g

# ---------------------------------------------------------------- FACES
EYE_L, EYE_R, EYE_Y = 14, 30, 19
EYE_OPEN = ['.ee.', 'eeee', 'eiee', 'eeee', 'ejje', '.ee.']
EYE_DOWN = ['....', '.ee.', 'eeee', 'eeee', 'eije', '.ee.']


def eyes_open(g, sparkle=False, down=False):
    for x0 in (EYE_L, EYE_R):
        stamp(g, x0, EYE_Y, EYE_DOWN if down else EYE_OPEN)
        if sparkle:
            g[EYE_Y + 4][x0 + 2] = 'i'
            g[EYE_Y + 1][x0 + 2] = 'i'
    return g


def eyes_closed(g, droop=False):
    for x0 in (EYE_L, EYE_R):
        if droop:
            put(g, [(x0 - 1, 22), (x0, 23), (x0 + 1, 23), (x0 + 2, 23), (x0 + 3, 23), (x0 + 4, 22)], 'e')
        else:
            put(g, [(x0 - 1, 23), (x0, 22), (x0 + 1, 21), (x0 + 2, 21), (x0 + 3, 22), (x0 + 4, 23)], 'e')
    return g


def brows(g, kind='soft'):
    for x0 in (EYE_L, EYE_R):
        if kind == 'worried':
            pts = [(x0, 16), (x0 + 1, 16), (x0 + 2, 15), (x0 + 3, 15)] if x0 == EYE_L else [(x0, 15), (x0 + 1, 15), (x0 + 2, 16), (x0 + 3, 16)]
        else:
            pts = [(x0, 16), (x0 + 1, 15), (x0 + 2, 15), (x0 + 3, 16)]
        put(g, pts, 'H')
    return g


def blush(g, wide=False):
    rx = 2.8 if wide else 2.1
    for y in range(24, 28):
        for x in range(8, 40):
            if inell(x, y, 12.8, 25.6, rx, 1.2) or inell(x, y, W - 1 - 12.8, 25.6, rx, 1.2):
                g[y][x] = 'b'
    if wide:
        put(g, [(11, 25), (13, 25), (34, 25), (36, 25)], 'R')
    return g


def lashes(g):
    put(g, [(13, 19), (12, 18), (34, 19), (35, 18)], 'e')
    return g


def mouth(g, kind):
    m = {
        'smile': [(22, 26), (25, 26), (23, 27), (24, 27)],
        'open': [(22, 26), (23, 26), (24, 26), (25, 26), (22, 27), (25, 27), (23, 28), (24, 28)],
        'small': [(23, 27), (24, 27)],
        'o': [(23, 26), (24, 26), (23, 27), (24, 27)],
        'smirk': [(23, 27), (24, 27), (25, 26)],
        'wavy': [(21, 27), (22, 26), (23, 27), (24, 26), (25, 27)],
    }[kind]
    put(g, m, 'm')
    if kind == 'open':
        put(g, [(23, 27), (24, 27)], 't')
    return g


def heart_eyes(g):
    for x0 in (EYE_L - 1, EYE_R - 1):
        stamp(g, x0, EYE_Y, ['.r.r.', 'rrrrr', 'rrrrr', '.rrr.', '..r..'])
        g[EYE_Y + 1][x0] = 'i'
        g[EYE_Y + 1][x0 + 4] = 'R'
    return g


def shades(g):
    for x0 in (12, 28):
        stamp(g, x0, 18, ['nnnnnnnn', 'nNNnnnnn', 'nnNnnnnn', 'nnnnnnnn', '.nnnnnn.'])
    put(g, [(x, 19) for x in range(20, 28)] + [(9, 19), (10, 19), (11, 19), (36, 19), (37, 19), (38, 19)], 'O')
    return g


EXPRESSIONS = ['happy', 'love', 'excited', 'sleepy', 'cool', 'shy']


def face(expr, blink=False, girl=False):
    g = empty()
    if expr == 'happy':
        eyes_closed(g) if blink else eyes_open(g)
        brows(g); mouth(g, 'smile'); blush(g)
    elif expr == 'love':
        eyes_closed(g) if blink else heart_eyes(g)
        brows(g); mouth(g, 'open'); blush(g, wide=True)
    elif expr == 'excited':
        eyes_closed(g) if blink else eyes_open(g, sparkle=True)
        brows(g); mouth(g, 'open'); blush(g)
    elif expr == 'sleepy':
        eyes_closed(g, droop=True)
        brows(g, 'worried'); mouth(g, 'o')
    elif expr == 'cool':
        shades(g); brows(g); mouth(g, 'smirk')
    elif expr == 'shy':
        eyes_closed(g) if blink else eyes_open(g, down=True)
        brows(g, 'worried'); mouth(g, 'wavy'); blush(g, wide=True)
    if girl and not blink and expr in ('happy', 'excited', 'shy'):
        lashes(g)
    return g

# ---------------------------------------------------------------- OUTFITS
def torso_test(top=31, bottom=48):
    def t(x, y):
        if not (top <= y <= bottom):
            return False
        half = 6.5 if y == top else (8.0 if y == top + 1 else 8.6)
        return abs(x - CX) <= half
    return t


def sleeve_test(bottom):
    def t(x, y):
        if not (32 <= y <= bottom):
            return False
        sh = (y - 32) // 8
        return 11 - sh <= x <= 16 - sh
    return sym(t)


PANTS_T = lambda x, y: (45 <= y <= 49 and 17 <= x <= 30) or (49 <= y <= 57 and (17 <= x <= 22 or 25 <= x <= 30))
SHOE_T = sym(lambda x, y: 56 <= y <= 62 and inell(x, y, 18.6, 59.6, 4.4, 2.9))


def outfit(style):
    shoes = outline(shape(SHOE_T, 'k'))
    put(shoes, [(x, 61) for x in range(15, 33) if shoes[61][x] not in ('.', 'O')], 'w')
    pants_ch = 'c' if style == 'overalls' else 'p'
    pants = outline(shape(PANTS_T, pants_ch))
    put(pants, [(23, y) for y in range(49, 58)] + [(24, y) for y in range(49, 58)], '.')
    pants = outline(pants)
    if style == 'hoodie':
        hood = outline(shape(lambda x, y: inell(x, y, CX, 31, 9.5, 3.2) and y <= 32, 'c'))
        t = outline(shape(torso_test(), 'c'))
        put(t, [(21, y) for y in range(33, 38)] + [(26, y) for y in range(33, 38)], 'w')
        put(t, [(21, 38), (26, 38)], 'W')
        put(t, [(x, 40) for x in range(18, 30)] + [(18, y) for y in range(41, 45)] + [(29, y) for y in range(41, 45)], 'C')
        put(t, [(x, 47) for x in range(16, 32)], 'C')
        g = stack(pants, hood, t, outline(shape(sleeve_test(44), 'c')), shoes)
        recolor(g, [(x, 44) for x in range(8, 17)] + [(x, 44) for x in range(31, 40)], 'C')
        put(g, [(x, 31) for x in range(19, 29)], 'C')
    elif style == 'tee':
        t = outline(shape(torso_test(), 'c'))
        put(t, [(20, 31), (21, 32), (22, 33), (23, 33), (24, 33), (25, 33), (26, 32), (27, 31)], 'C')
        stamp(t, 21, 37, ['..y..', '.yyy.', 'yyyyy', '.y.y.'], {})
        g = stack(pants, t, outline(shape(sleeve_test(37), 'c')), shoes)
        recolor(g, [(x, 37) for x in range(9, 17)] + [(x, 37) for x in range(31, 39)], 'C')
    elif style == 'cardigan':
        t = outline(shape(torso_test(), 'c'))
        inner = outline(shape(lambda x, y: torso_test()(x, y) and 20 <= x <= 27, 'w'))
        t = stack(t, inner)
        put(t, [(19, y) for y in range(32, 48)] + [(28, y) for y in range(32, 48)], 'C')
        put(t, [(19, 36), (19, 40), (19, 44)], 'y')
        put(t, [(15, 41), (16, 41), (17, 41), (30, 41), (31, 41), (32, 41)], 'C')   # pockets
        g = stack(pants, t, outline(shape(sleeve_test(44), 'c')), shoes)
        recolor(g, [(x, 44) for x in range(8, 17)] + [(x, 44) for x in range(31, 40)], 'L')
    else:  # overalls
        shirt = outline(shape(torso_test(), 'w'))
        bib = outline(shape(lambda x, y: 38 <= y <= 48 and 17 <= x <= 30, 'c'))
        g = stack(pants, shirt, outline(shape(sleeve_test(37), 'w')), bib, shoes)
        put(g, [(18, y) for y in range(31, 39)] + [(29, y) for y in range(31, 39)], 'c')
        put(g, [(19, y) for y in range(31, 38)] + [(28, y) for y in range(31, 38)], 'C')
        put(g, [(18, 38), (19, 38), (28, 38), (29, 38)], 'y')
        put(g, [(x, 41) for x in range(21, 27)] + [(21, 42), (26, 42), (21, 43), (26, 43)], 'C')
    return g

# ---------------------------------------------------------------- HAIR
CAP_T = lambda x, y: inell(x, y, CX, 15.4, 16.2, 13.6)
FACE_T = lambda x, y: inell(x, y, CX, 21.5, 12.4, 11.2)


def bang_cut(bang, sides_to=29, side_w=4):
    """Hair cap minus the face window below the bang line."""
    def t(x, y):
        if not CAP_T(x, y):
            return False
        if FACE_T(x, y) and y > bang(x):
            return False
        if y > sides_to:
            return False
        return True
    return t


def shine(g):
    for y in range(2, 14):
        for x in range(6, 42):
            if g[y][x] in ('h',) and inell(x, y, 19, 11, 11, 7.5) and not inell(x, y, 19, 12.5, 9.5, 6.0) and x < 28:
                g[y][x] = 'l'
    return g


def jagged(base, amp, period=6, phase=0):
    pattern = [0, 1, 2, 3, 2, 1][:period]
    return lambda x: base + amp * pattern[(x + phase) % len(pattern)] / 3


def hair(style, gender):
    back = empty()
    if style == 'default':
        style = 'bob' if gender == 'girl' else 'tousled'
    if style == 'bob':
        back = outline(shape(lambda x, y: inell(x, y, CX, 20, 16.6, 14.5) and y <= 34, 'h'))
        locks = sym(lambda x, y: 18 <= y <= 33 and 7 <= x <= 11 + (1 if y < 26 else 0))
        front = outline(shape(lambda x, y: bang_cut(jagged(12, 3))(x, y) or locks(x, y), 'h'))
    elif style == 'tousled':
        spikes = lambda x, y: inell(x, y, 16.5, 3.2, 2.4, 3.0) or inell(x, y, 23.5, 2.0, 2.6, 3.0) or inell(x, y, 30.5, 3.2, 2.4, 3.0)
        side = sym(lambda x, y: 16 <= y <= 22 and 8 <= x <= 10)
        front = outline(shape(lambda x, y: bang_cut(jagged(13, 4, phase=2), sides_to=22)(x, y) or spikes(x, y) or side(x, y), 'h'))
    elif style == 'short':
        side = sym(lambda x, y: 16 <= y <= 21 and 8 <= x <= 10)
        front = outline(shape(lambda x, y: bang_cut(lambda x: 8 + (x - 8) * 0.22, sides_to=21)(x, y) or side(x, y), 'h'))
    elif style == 'bun':
        bun = outline(shape(lambda x, y: inell(x, y, CX, 3.2, 6.2, 4.4), 'h'))
        side = sym(lambda x, y: 16 <= y <= 24 and 8 <= x <= 10)
        front = stack(bun, outline(shape(lambda x, y: bang_cut(jagged(12, 3, phase=1), sides_to=24)(x, y) or side(x, y), 'h')))
    elif style == 'curly':
        import math
        def bumpy(x, y, cx, cy, rx, ry):
            a = math.atan2(y - cy, x - cx)
            k = 1 + 0.07 * math.sin(a * 9)
            return inell(x, y, cx, cy, rx * k, ry * k)
        back = outline(shape(lambda x, y: bumpy(x, y, CX, 22, 19, 17) and y <= 40, 'h'))
        front = outline(shape(lambda x, y: bumpy(x, y, CX, 15, 18, 14.5) and not (FACE_T(x, y) and y > jagged(13, 3)(x)) and y <= 28, 'h'))
        for y in range(1, 41):
            for x in range(W):
                if (x * 3 + y * 5) % 11 == 0:
                    for gg in (front, back):
                        if gg[y][x] == 'h':
                            gg[y][x] = 'H'
    else:  # long
        back = outline(shape(lambda x, y: (inell(x, y, CX, 20, 16.6, 14.5) or (20 <= y <= 50 and 8 <= x <= 39)) and not (y > 47 and abs(x - CX) > 13 - (y - 47) * 2), 'h'))
        locks = sym(lambda x, y: 18 <= y <= 42 and 7 <= x <= 11)
        front = outline(shape(lambda x, y: bang_cut(jagged(12, 3, phase=3))(x, y) or locks(x, y), 'h'))
        put(back, [(x, y) for y in range(36, 50, 4) for x in (12, 20, 27, 35) if back[y][x] == 'h'], 'H')
    shine(front)
    # a few strands at the fringe
    for x in range(10, 38, 5):
        for y in range(8, 16):
            if front[y][x] == 'h' and front[y + 1][x] in ('h', 'H'):
                front[y][x] = 'H'
                break
    return back, front

# ---------------------------------------------------------------- ACCESSORIES

def accessory(kind):
    g = empty()
    if kind == 'glasses':
        for x0 in (12, 28):
            put(g, [(x, 18) for x in range(x0 + 1, x0 + 7)] + [(x, 25) for x in range(x0 + 1, x0 + 7)] +
                [(x0, y) for y in range(19, 25)] + [(x0 + 7, y) for y in range(19, 25)], 'O')
            put(g, [(x0 + 5, 19), (x0 + 6, 20)], 'i')
        put(g, [(x, 20) for x in range(20, 28)] + [(9, 20), (10, 20), (11, 20), (36, 20), (37, 20), (38, 20)], 'O')
    elif kind == 'bow':
        b = outline(shape(lambda x, y: inell(x, y, 31, 5, 4.2, 3.2) or inell(x, y, 39, 5, 4.2, 3.2), 'r'))
        put(b, [(35, 4), (35, 5), (35, 6)], 'y'); put(b, [(34, 5), (36, 5)], 'Y')
        g = b
    elif kind == 'cap':
        dome = outline(shape(lambda x, y: inell(x, y, CX, 10.5, 16.8, 9.5) and y <= 10, 'c'))
        brim = outline(shape(lambda x, y: 10 <= y <= 12 and 5 <= x <= 42, 'c'), light=False)
        g = stack(dome, brim)
        put(g, [(23, 1), (24, 1)], 'w')
        stamp(g, 21, 4, ['.ww.', 'wwww', '.ww.'])
    elif kind == 'headphones':
        band = shape(lambda x, y: y <= 14 and inell(x, y, CX, 17, 18.5, 16.5) and not inell(x, y, CX, 17, 16.5, 14.5), 'v')
        cups = shape(sym(lambda x, y: inell(x, y, 7.8, 20, 3.2, 5.2)), 'v')
        g = stack(outline(band), outline(cups))
    elif kind == 'flower':
        f = shape(lambda x, y: any(inell(x, y, 34 + dx, 6 + dy, 1.9, 1.9) for dx, dy in ((0, -2.5), (2.5, 0), (0, 2.5), (-2.5, 0))), 'u')
        f = outline(f)
        put(f, [(34, 6), (33, 6), (34, 5), (33, 5)], 'y')
        g = f
    return g


# ---------------------------------------------------------------- EMOTE ICONS (12x12)
ICONS = {
    'happy': ['............', '......OO....', '......OyO...', '......OyO...', '......O.O...', '......O.....',
              '...OOOO.....', '..OyyyO.....', '..OyyyO.....', '...OOO......', '............', '............'],
    'love': ['............', '..OOO..OOO..', '.OrirOOrrrO.', '.OirrrrrrRO.', '.OrrrrrrrRO.', '..OrrrrrRO..',
             '...OrrrRO...', '....OrRO....', '.....OO.....', '............', '............', '............'],
    'excited': ['............', '.....OO.....', '.....OyO....', '....OyyO....', 'OOOOOyyyOOOO', '.OyyyyyyyyO.',
                '..OYyyyyYO..', '...OyyyyO...', '..OyyOOyyO..', '..OYO..OYO..', '..OO....OO..', '............'],
    'sleepy': ['............', '.......OOOOO', '.......OxxXO', '.........OO.', '........OO..', '.......OxxxO',
               '.OOOO..OOOOO', '.OxXO.......', '...O........', '..O.........', '.OxxO.......', '.OOOO.......'],
    'cool': ['....O.......', '...OiO......', '..OiyiO.....', '.OiyyyiO....', '..OiyiO.....', '...OiO...O..',
             '....O...OiO.', '.......OiyiO', '........OiO.', '.........O..', '............', '............'],
    'shy': ['............', '............', '..OO....OO..', '.OuuO..OuuO.', 'OuuuuOOuuuuO', 'OuuuuuuuuuUO',
            '.OuuuuuuuUO.', '..OuuuuuUO..', '...OuuuUO...', '....OuUO....', '.....OO.....', '............'],
}

# ---------------------------------------------------------------- CAT (40 x 34)
KX = (CW - 1) / 2     # 19.5


def cshape(test, ch):
    return shape(test, ch, CW, CH)


def ear_test(dx=0, dy=0):
    def t(x, y):
        x, y = x - dx, y - dy
        if not (1 <= y <= 9):
            return False
        lx = (x >= 10 - (y - 1) * 0.25) and (x <= 11 + (y - 1) * 0.95)
        rx = (x <= CW - 1 - 10 + (y - 1) * 0.25) and (x >= CW - 1 - 11 - (y - 1) * 0.95)
        return lx or rx
    return t


def cat_head(dx=0, dy=0):
    head = outline(cshape(lambda x, y: inell(x - dx, y - dy, KX, 13, 10.6, 8.6) or inell(x - dx, y - dy, KX, 15.5, 12.2, 5.2), 'f'))
    ears = outline(cshape(ear_test(dx, dy), 'f'))
    inner = cshape(lambda x, y: ear_test(dx, dy)(x, y) and 3 <= y - dy <= 8 and abs(x - dx - KX) > 6.5 and abs(x - dx - KX) < 8.6, 't')
    g = stack(ears, inner, head)
    muzzle = cshape(lambda x, y: inell(x - dx, y - dy, KX, 17, 4.2, 2.6), 'z')
    for y in range(CH):
        for x in range(CW):
            if muzzle[y][x] != '.' and g[y][x] not in ('O', '.'):
                g[y][x] = 'z'
    put(g, [(19 + dx, 6 + dy), (20 + dx, 6 + dy), (17 + dx, 7 + dy), (22 + dx, 7 + dy), (19 + dx, 8 + dy), (20 + dx, 8 + dy)], 'd')
    return g


def cat_face(g, kind, dx=0, dy=0):
    ex = [(12, 24)]
    for x0 in (12 + dx, 24 + dx):
        y0 = 11 + dy
        if kind == 'open':
            stamp(g, x0, y0, ['.ee.', 'eiee', 'eeee', '.ee.'])
        elif kind == 'blink' or kind == 'sleep':
            put(g, [(x0, y0 + 2), (x0 + 1, y0 + 3), (x0 + 2, y0 + 3), (x0 + 3, y0 + 2)] if kind == 'sleep' else [(x0, y0 + 2), (x0 + 1, y0 + 2), (x0 + 2, y0 + 2), (x0 + 3, y0 + 2)], 'e')
        elif kind == 'happy':
            put(g, [(x0, y0 + 2), (x0 + 1, y0 + 1), (x0 + 2, y0 + 1), (x0 + 3, y0 + 2)], 'e')
    put(g, [(19 + dx, 15 + dy), (20 + dx, 15 + dy)], 'r')
    put(g, [(18 + dx, 16 + dy), (21 + dx, 16 + dy), (19 + dx, 17 + dy), (20 + dx, 17 + dy)], 'e')
    if kind == 'happy':
        put(g, [(19 + dx, 18 + dy), (20 + dx, 18 + dy)], 't')
    put(g, [(10 + dx, 15 + dy), (11 + dx, 15 + dy), (28 + dx, 15 + dy), (29 + dx, 15 + dy)], 'b')
    return g


def tail_chain(points, r=2.3):
    t = cshape(lambda x, y: any(inell(x, y, px, py, r, r) for px, py in points), 'f')
    t = outline(t)
    for px, py in points[-2:]:
        for y in range(CH):
            for x in range(CW):
                if t[y][x] not in ('O', '.') and inell(x, y, px, py, r, r):
                    t[y][x] = 'd'
    return t


def bez(p0, p1, p2, n=10):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [k / n for k in range(n + 1)]]


TAILS = {0: bez((27, 29), (37, 28), (35, 15)), 1: bez((27, 29), (39, 26), (38, 17)), 2: bez((27, 29), (38, 31), (37, 23))}


def cat_sit(tail, kind):
    body = outline(cshape(lambda x, y: inell(x, y, KX, 24.5, 9.6, 8.2), 'f'))
    chest = cshape(lambda x, y: inell(x, y, KX, 25, 4.6, 6.2), 'z')
    for y in range(CH):
        for x in range(CW):
            if chest[y][x] != '.' and body[y][x] not in ('O', '.'):
                body[y][x] = 'z'
    put(body, [(11, 22), (12, 22), (11, 25), (12, 25), (28, 22), (27, 22), (28, 25), (27, 25)], 'd')
    paws = outline(cshape(lambda x, y: inell(x, y, 15.5, 31.5, 2.9, 1.9) or inell(x, y, 23.5, 31.5, 2.9, 1.9), 'z'), light=False)
    g = stack(tail_chain(TAILS[tail]), body, cat_head(), paws)
    return cat_face(g, kind)


def cat_loaf(breath):
    b = 1 if breath else 0
    body = outline(cshape(lambda x, y: inell(x, y, 23, 26 - b * 0.5, 14.5, 6.6 + b * 0.5), 'f'))
    put(body, [(22, 20), (23, 21), (28, 20), (29, 21), (33, 22), (34, 23)], 'd')
    tail = tail_chain(bez((36, 29), (30, 34), (16, 32)), r=2.0)
    head = cat_head(-8, 7)
    g = stack(body, head, tail)
    return cat_face(g, 'sleep', -8, 7)


def cat_frames():
    frames = {}
    for t in (0, 1, 2):
        frames[f'sit{t}'] = cat_sit(t, 'open')
    frames['blink'] = cat_sit(0, 'blink')
    frames['happy'] = cat_sit(1, 'happy')
    frames['happy2'] = cat_sit(2, 'happy')
    frames['loaf0'] = cat_loaf(False)
    frames['loaf1'] = cat_loaf(True)
    return frames


# ---------------------------------------------------------------- SHEET WRITER

def to_image(cells, cw, ch, cols):
    rows = (len(cells) + cols - 1) // cols
    img = Image.new('RGBA', (cw * cols, ch * rows), (0, 0, 0, 0))
    px = img.load()
    for i, g in enumerate(cells):
        ox, oy = (i % cols) * cw, (i // cols) * ch
        for y in range(len(g)):
            for x in range(len(g[0])):
                c = g[y][x]
                if c != '.':
                    px[ox + x, oy + y] = hex2rgba(PAL[c])
    return img


def walk_pose(g, side):
    """Lift one foot by a pixel (side 0 = left leg, 1 = right leg) for walk frames."""
    out = [row[:] for row in g]
    cols = range(0, W // 2) if side == 0 else range(W // 2, W)
    for x in cols:
        for y in range(52, H - 2):
            out[y][x] = g[y + 2][x]
        out[H - 2][x] = '.'
        out[H - 1][x] = '.'
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    cells, index = [], {}

    def add(name, g):
        index[name] = len(cells)
        cells.append(g)

    add('body', body_layer())
    for side in (0, 1):
        add(f'body@w{side + 1}', walk_pose(body_layer(), side))
    for e in EXPRESSIONS:
        for girl in (False, True):
            add(f'face-{e}{"-girl" if girl else ""}', face(e, False, girl))
        add(f'face-{e}-blink', face(e, True))
    for s in ('hoodie', 'tee', 'cardigan', 'overalls'):
        add(f'outfit-{s}', outfit(s))
        for side in (0, 1):
            add(f'outfit-{s}@w{side + 1}', walk_pose(outfit(s), side))
    for s in ('default', 'short', 'bun', 'curly', 'long'):
        for gender in ('girl', 'boy'):
            if s != 'default' and gender == 'boy':
                continue
            back, front = hair(s, gender)
            key = s if s != 'default' else f'default-{gender}'
            add(f'hairback-{key}', back)
            add(f'hairfront-{key}', front)
    for a in ('glasses', 'bow', 'cap', 'headphones', 'flower'):
        add(f'acc-{a}', accessory(a))
    cols = 8
    to_image(cells, W, H, cols).save(os.path.join(OUT, 'character-layers.png'))

    icon_cells = [grid(ICONS[e], width=12, height=12) for e in EXPRESSIONS]
    to_image(icon_cells, 12, 12, len(icon_cells)).save(os.path.join(OUT, 'emote-icons.png'))

    cf = cat_frames()
    to_image(list(cf.values()), CW, CH, len(cf)).save(os.path.join(OUT, 'cat.png'))

    meta = {'cell': [W, H], 'cols': cols, 'layers': index, 'split': 31, 'feet': 62, 'head': [6, 0, 36, 33],
            'cat': {'cell': [CW, CH], 'frames': list(cf.keys()), 'feet': 33, 'loafBottom': 32},
            'icons': {'cell': [12, 12], 'order': EXPRESSIONS},
            'keys': {k: PAL[k] for k in 'sSqbhHlcCLfFgdzZ'}}
    with open(os.path.join(OUT, 'sprites.json'), 'w') as fh:
        json.dump(meta, fh, indent=1)
    with open(os.path.join(OUT, 'sprites-meta.js'), 'w') as fh:
        fh.write('/* Generated by tools/build_sprites.py - do not edit by hand. */\n')
        fh.write('window.COZY_SPRITE_META = ' + json.dumps(meta) + ';\n')
    print('built', len(cells), 'character layers,', len(cf), 'cat frames')


if __name__ == '__main__':
    main()
