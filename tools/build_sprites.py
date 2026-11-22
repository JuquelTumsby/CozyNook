#!/usr/bin/env python3
"""
CozyNook sprite builder
=======================
Builds the layered pixel-art sprite sheets in assets/sprites/ from the
hand-drawn pixel grids in this file.

Run it from the project folder:   python3 tools/build_sprites.py

How the grids work
------------------
* Every character cell is 32 x 44 pixels, every cat cell is 32 x 28.
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

W, H = 32, 44          # character cell
CW, CH = 32, 28        # cat cell

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

# ---------------------------------------------------------------- BODY
HEAD = grid([
    '..........ssssss',   # 4
    '........ssssssss',
    '.......sssssssss',
    '......ssssssssss',
    '.....sssssssssss',   # 8
    '.....sssssssssss',
    '.....sssssssssss',
    '.....sssssssssss',
    '....ssssssssssss',   # 12
    '...sssssssssssss',
    '...sssssssssssss',
    '....ssssssssssss',
    '.....sssssssssss',   # 16
    '.....sssssssssss',
    '......ssssssssss',
    '.......sssssssss',
    '.........sssssss',   # 20
    '...........sssss',
], start=4)
NECK = grid(['............ssss'] * 3, start=20)
TORSO = grid(['..........ssssss'] + ['.........sssssss'] * 10, start=23)
LEG = grid(['...........sss..'] * 7, start=34)
ARM = grid([
    '.........ss.....',  # 24
    '........sss.....',
    '.......ssss.....',
    '.......ssss.....',
    '.......ssss.....',
    '......ssss......',
    '......ssss......',  # 30
    '......ssss......',
    '......ssss......',
    '......ssss......',
    '.......ss.......',  # 34
], start=24)


def body_layer():
    g = stack(outline(NECK), outline(TORSO), outline(LEG), outline(ARM), outline(HEAD, light=False))
    # ear detail + neck shadow
    put(g, mirror_pts([(4, 14), (4, 15)]), 'S')
    put(g, mirror_pts([(13, 22), (14, 22), (15, 22)]), 'S')
    # soft cheek highlight
    put(g, [(8, 9), (9, 8)], 'q')
    return g

# ---------------------------------------------------------------- FACES
EYE_OPEN = [(10, 13), (11, 13), (10, 14), (11, 14), (10, 15), (11, 15)]
EYE_R = [(x + 10, y) for x, y in EYE_OPEN]


def eyes_open(g, sparkle=False, look=0):
    for pts in (EYE_OPEN, EYE_R):
        for x, y in pts:
            g[y][x + look] = 'e'
        x0 = pts[0][0] + look
        g[13][x0] = 'i'
        if sparkle:
            g[15][x0 + 1] = 'i'
    return g


def eyes_closed(g, droop=False):
    for x0 in (10, 20):
        if droop:
            put(g, [(x0 - 1, 15), (x0, 15), (x0 + 1, 15), (x0 + 2, 15)], 'e')
        else:   # happy ^ ^
            put(g, [(x0 - 1, 15), (x0, 14), (x0 + 1, 14), (x0 + 2, 15)], 'e')
    return g


def blush(g, wide=False):
    pts = [(7, 16), (8, 16)] + ([(9, 16), (7, 17), (8, 17)] if wide else [])
    put(g, mirror_pts(pts), 'b')
    return g


def lashes(g):
    put(g, [(9, 12), (22, 12)], 'e')
    return g


def mouth(g, kind):
    if kind == 'smile':
        put(g, [(14, 17), (17, 17), (15, 18), (16, 18)], 'm')
    elif kind == 'open':
        put(g, [(14, 17), (15, 17), (16, 17), (17, 17), (14, 18), (17, 18), (15, 19), (16, 19)], 'm')
        put(g, [(15, 18), (16, 18)], 't')
    elif kind == 'small':
        put(g, [(15, 18), (16, 18)], 'm')
    elif kind == 'o':
        put(g, [(15, 17), (16, 17), (15, 18), (16, 18)], 'm')
    elif kind == 'smirk':
        put(g, [(15, 18), (16, 18), (17, 17)], 'm')
    elif kind == 'wavy':
        put(g, [(14, 18), (15, 17), (16, 18), (17, 17)], 'm')
    elif kind == 'cat':
        put(g, [(14, 17), (15, 18), (16, 17), (17, 18)], 'm')
    return g


def heart_eyes(g):
    for x0 in (9, 19):
        put(g, [(x0, 13), (x0 + 2, 13), (x0, 14), (x0 + 1, 14), (x0 + 2, 14), (x0 + 1, 15)], 'r')
        put(g, [(x0 + 1, 13)], 'R')
        put(g, [(x0, 13)], 'i')
    return g


def shades(g):
    for x0 in (8, 18):
        for y in (13, 14, 15):
            for x in range(x0, x0 + 5):
                if not (y == 15 and x in (x0, x0 + 4)):
                    g[y][x] = 'n'
        put(g, [(x0 + 1, 13), (x0 + 2, 14)], 'N')
    put(g, [(13, 13), (14, 13), (15, 13), (16, 13), (17, 13), (6, 13), (7, 13), (25, 13), (24, 13)], 'O')
    return g


EXPRESSIONS = ['happy', 'love', 'excited', 'sleepy', 'cool', 'shy']


def face(expr, blink=False, girl=False):
    g = empty()
    if expr == 'happy':
        eyes_closed(g) if blink else eyes_open(g)
        mouth(g, 'smile'); blush(g)
    elif expr == 'love':
        eyes_closed(g) if blink else heart_eyes(g)
        mouth(g, 'cat'); blush(g, wide=True)
    elif expr == 'excited':
        eyes_closed(g) if blink else eyes_open(g, sparkle=True)
        mouth(g, 'open'); blush(g)
    elif expr == 'sleepy':
        eyes_closed(g, droop=True)
        mouth(g, 'o')
    elif expr == 'cool':
        shades(g); mouth(g, 'smirk')
    elif expr == 'shy':
        eyes_closed(g) if blink else eyes_open(g, look=-1)
        mouth(g, 'wavy'); blush(g, wide=True)
    if girl and not blink and expr in ('happy', 'excited', 'shy'):
        lashes(g)
    return g

# ---------------------------------------------------------------- OUTFITS
PANTS = grid(['..........cccccc'] * 2 + ['..........ccccc.'] * 6, start=33)
SHOE = grid(['..........kkkkk.', '.........kkkkkk.', '.........kkkkkk.', '.........kkkkkk.'], start=40)


def shirt_torso(ch='c', start=22):
    return grid(['..........' + ch * 6, '.........' + ch * 7] + ['........' + ch * 8] * 11, start=start)


def sleeve(rows, ch='c'):
    shape = ['.........cc.....', '........ccc.....', '.......cccc.....', '.......cccc.....',
             '.......cccc.....', '......cccc......', '......cccc......', '......cccc......']
    return grid([r.replace('c', ch) for r in shape[:rows]], start=24)


def pants(ch='p'):
    return outline(grid([r.replace('c', ch) for r in ['..........cccccc'] * 2 + ['..........ccccc.'] * 6], start=33))


def outfit(style):
    shoes = outline(SHOE)
    if style == 'hoodie':
        t = outline(shirt_torso())
        put(t, mirror_pts([(14, 24), (14, 25), (14, 26)]), 'w')          # strings
        put(t, mirror_pts([(11, 30), (12, 29), (13, 29), (14, 29), (15, 29)]), 'C')   # pocket
        put(t, [(x, 33) for x in range(9, 23)], 'C')                       # ribbed hem
        hood = outline(grid(['........cccccccc', '.........ccccccc'], start=21))
        t = stack(hood, t)
        put(t, [(x, 22) for x in range(11, 21)], 'C')
        g = stack(pants(), t, outline(sleeve(8)), shoes)
        put(g, mirror_pts([(7, 31), (8, 31)]), 'C')                        # cuffs
    elif style == 'tee':
        t = outline(shirt_torso())
        put(t, mirror_pts([(13, 22), (14, 23), (15, 23)]), 'C')             # neckline
        put(t, mirror_pts([(13, 27), (14, 27)]), 'L')                       # little print
        put(t, [(15, 27), (16, 27), (15, 28), (16, 28)], 'y')
        g = stack(pants(), t, outline(sleeve(4)), shoes)
    elif style == 'cardigan':
        inner = outline(shirt_torso('w'))
        t = outline(shirt_torso())
        for y in range(22, 35):
            for x in range(13, 19):
                t[y][x] = inner[y][x]
        put(t, [(12, y) for y in range(23, 35)], 'C')
        put(t, [(19, y) for y in range(23, 35)], 'C')
        put(t, [(12, 26), (12, 29), (12, 32)], 'y')                         # buttons
        g = stack(pants(), t, outline(sleeve(8)), shoes)
        put(g, mirror_pts([(7, 31), (8, 31)]), 'L')
    elif style == 'overalls':
        shirt = outline(shirt_torso('w'))
        bib = outline(grid(['...........ccccc'] * 8, start=27))
        straps = grid(['..........cc....'] * 4, start=23)
        g = stack(pants('c'), shirt, outline(sleeve(4, 'w')), bib, shoes)
        put(g, mirror_pts([(11, y) for y in range(22, 27)]), 'c')
        put(g, mirror_pts([(12, y) for y in range(22, 27)]), 'C')
        put(g, mirror_pts([(11, 27)]), 'y')                                 # buckles
        put(g, [(14, 30), (15, 30), (16, 30), (17, 30)], 'C')               # bib pocket
        put(g, [(14, 31), (17, 31)], 'C')
    return g

# ---------------------------------------------------------------- HAIR
# Each style has a "back" layer (behind the head) and a "front" layer.

def hair(style, gender):
    back = empty()
    if style == 'default':
        style = 'bob' if gender == 'girl' else 'tousled'
    if style == 'bob':
        back = outline(grid(['.....hhhhhhhhhhh'] * 13 + ['......hhhhhhhhhh', '.......hhhhhhhhh'], start=8))
        front = outline(grid([
            '...........hhhhh',  # 2
            '.........hhhhhhh',
            '.......hhhhhhhhh',
            '......hhhhhhhhhh',
            '.....hhhhhhhhhhh',  # 6
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',  # 10
            '...hhhhh.hhhhhh.',
            '...hhhh...hhhh..',
            '...hhh..........',
            '...hhh..........',  # 14
            '...hhh..........',
            '...hhh..........',
            '...hhhh.........',
            '...hhhh.........',  # 18
            '....hhh.........',
            '.....h..........',
        ], start=2))
        put(front, [(8, 5), (9, 4), (10, 4), (7, 6)], 'l')
        put(front, [(15, 8), (16, 8), (15, 9), (21, 7), (10, 9)], 'H')
    elif style == 'tousled':
        front = outline(grid([
            '..........h..hh.',  # 1
            '.........hhhhhhh',
            '........hhhhhhhh',
            '......hhhhhhhhhh',
            '.....hhhhhhhhhhh',  # 5
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',  # 9
            '....hhhhhhhhhhhh',
            '....hhhhhhh.hhhh',
            '....hhh.hh...hh.',
            '....hh..........',  # 13
            '....h...........',
        ], start=1))
        put(front, [(8, 5), (9, 4), (10, 4), (11, 3), (7, 6)], 'l')
        put(front, [(14, 7), (15, 8), (20, 7), (19, 8), (11, 8)], 'H')
    elif style == 'short':
        front = outline(grid([
            '..........hhhhhh',  # 3
            '........hhhhhhhh',
            '......hhhhhhhhhh',
            '.....hhhhhhhhhhh',
            '....hhhhhhhhhhhh',  # 7
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhh......',  # 11
            '....hhh.........',
            '....hh..........',
        ], start=3))
        # side-swept fringe
        for x in range(16, 22):
            front[11][x] = 'h'
        front[11][22] = 'O'; front[12][21] = 'O'; front[12][20] = 'O'
        put(front, [(8, 6), (9, 5), (10, 5), (7, 7)], 'l')
        put(front, [(17, 9), (18, 10), (13, 9)], 'H')
    elif style == 'bun':
        bun = outline(grid(['............hhhh', '...........hhhhh', '...........hhhhh', '............hhhh'], start=0))
        front = stack(bun, outline(grid([
            '..........hhhhhh',  # 3
            '........hhhhhhhh',
            '......hhhhhhhhhh',
            '.....hhhhhhhhhhh',
            '....hhhhhhhhhhhh',  # 7
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhh.hhhhhh',  # 11
            '....hhh....hhhh.',
            '....hh..........',
            '....hh..........',
            '.....h..........',
        ], start=3)))
        put(front, [(13, 1), (14, 1), (9, 5), (10, 5), (8, 6)], 'l')
        put(front, [(15, 4), (16, 4), (16, 9), (21, 8)], 'H')
    elif style == 'curly':
        back = outline(grid(['....hhhhhhhhhhhh'] * 12 + ['.....hhhhhhhhhhh', '......hhh.hhh.hh'], start=9))
        front = outline(grid([
            '.........hh.hhhh',  # 1
            '.......hhhhhhhhh',
            '.....hhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '...hhhhhhhhhhhhh',  # 5
            '..hhhhhhhhhhhhhh',
            '..hhhhhhhhhhhhhh',
            '..hhhhhhhhhhhhhh',
            '..hhhhhhhhhhhhhh',  # 9
            '..hhhhh.hhh.hhh.',
            '..hhhh.....h....',
            '..hhhh..........',
            '..hhhh..........',  # 13
            '..hhh...........',
            '...hhh..........',
            '..hhhh..........',
            '...hh...........',  # 17
        ], start=1))
        curls = [(6, 4), (9, 3), (12, 2), (5, 7), (8, 6), (11, 5), (14, 4), (4, 10), (7, 9), (10, 8), (13, 7),
                 (17, 3), (20, 4), (23, 6), (18, 6), (21, 7), (25, 9), (16, 8), (19, 9), (22, 10)]
        put(front, curls, 'H')
        put(front, [(7, 4), (10, 3), (6, 7), (9, 6), (12, 5)], 'l')
    elif style == 'long':
        back = outline(grid(['.....hhhhhhhhhhh'] * 22 + ['......hhhhhhhhhh', '.......hhhhhhhhh'], start=8))
        put(back, mirror_pts([(8, 30), (9, 31), (11, 29)]), 'H')
        front = outline(grid([
            '...........hhhhh',  # 2
            '.........hhhhhhh',
            '.......hhhhhhhhh',
            '......hhhhhhhhhh',
            '.....hhhhhhhhhhh',  # 6
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhhhh',
            '....hhhhhhhhhh.h',  # 10
            '...hhhhhhhhhh...',
            '...hhhh.hhh.....',
            '...hhh..........',
            '...hhh..........',  # 14
            '...hhh..........',
            '...hhh..........',
            '...hhh..........',
            '...hhh..........',  # 18
            '...hhh..........',
            '...hhh..........',
            '....hh..........',
        ], start=2))
        put(front, [(8, 5), (9, 4), (10, 4), (7, 6)], 'l')
        put(front, [(15, 6), (15, 7), (16, 8), (14, 9)], 'H')
    return back, front

# ---------------------------------------------------------------- ACCESSORIES

def accessory(kind):
    g = empty()
    if kind == 'glasses':
        for x0 in (8, 18):
            put(g, [(x, 12) for x in range(x0, x0 + 5)] + [(x, 16) for x in range(x0, x0 + 5)] +
                [(x0, y) for y in range(12, 17)] + [(x0 + 4, y) for y in range(12, 17)], 'O')
            put(g, [(x0 + 3, 13)], 'i')
        put(g, [(13, 13), (14, 13), (17, 13), (18, 13), (15, 13), (16, 13)], 'O')
        put(g, [(6, 13), (7, 13), (24, 13), (25, 13)], 'O')
    elif kind == 'bow':
        b = outline(grid(['.....................rrr.rrr....', '....................rrrrrrrrr...',
                          '....................rrrrrrrrr...', '.....................rrr.rrr....'], start=2))
        put(b, [(24, 3), (24, 4)], 'y')
        g = b
    elif kind == 'cap':
        cap = outline(grid([
            '..........cccccc', '........cccccccc', '......cccccccccc', '.....ccccccccccc',
            '.....ccccccccccc', '....cccccccccccc'], start=1))
        brim = outline(grid(['...ccccccccccccc'] * 2, start=7), light=False)
        g = stack(cap, brim)
        put(g, [(15, 1), (16, 1)], 'w')
        put(g, [(18, 3), (19, 3), (18, 4), (19, 4)], 'w')
    elif kind == 'headphones':
        band = grid(['.........ooooooo'], start=3)
        put(g, [(x, y) for y in (2,) for x in range(9, 23)], 'O')
        put(g, [(7, 3), (8, 3), (23, 3), (24, 3), (5, 4), (6, 4), (25, 4), (26, 4), (4, 5), (27, 5)], 'O')
        put(g, [(4, y) for y in range(6, 11)] + [(27, y) for y in range(6, 11)], 'O')
        cups = outline(grid(['.vvvv...........'] * 6, start=10))
        g = stack(g, cups)
    elif kind == 'flower':
        f = grid(['.....................u...', '....................uuu..', '.....................u...'], start=4) if False else empty()
        put(f, [(23, 3), (22, 4), (24, 4), (23, 5), (21, 3), (25, 3), (21, 5), (25, 5)], 'O')
        put(f, [(22, 3), (24, 3), (22, 5), (24, 5), (21, 4), (25, 4), (23, 2), (23, 6)], 'u')
        put(f, [(23, 4)], 'y')
        put(f, [(20, 4), (26, 4), (23, 1), (23, 7)], 'O')
        put(f, [(22, 4), (24, 4), (23, 3), (23, 5)], 'U')
        put(f, [(23, 4)], 'y')
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

# ---------------------------------------------------------------- CAT (32x28)
def cat_grid(half_rows, start=0):
    """Cat half-grids are 10 wide, mirrored to 20, then padded to 32."""
    rows = [(r + r[::-1]).ljust(CW, '.') for r in half_rows]
    return grid(rows, start=start, width=CW, height=CH)


CAT_HEAD = [
    '...f......',  # 1
    '..fgf.....',
    '..fggf....',
    '..fgggffff',
    '.fffffffff',  # 5
    '.fffffffff',
    '.fffffffff',
    'ffffffffff',  # 8
    '.fffffffff',
    '..ffffffzz',  # 10
    '...ffffzzz',
]
CAT_BODY = [
    '....ffzzzz',  # 11
    '...fffzzzz',
    '..ffffzzzz',
    '..ffffzzzz',
    '.fffffzzzz',  # 15
    '.fffffzzzz',
    '.ffffffzzz',
    '.fffffffff',
    '.fffffffff',
    '.fffffffff',  # 20
    '..ffffffff',
]
CAT_PAWS = ['...zzz....', '..zzzzz...', '..zzzzz...']
CAT_TAILS = {
    0: [(10, '......................ffff'), (11, '.....................ffff'), (12, '.....................fff'),
        (13, '....................ffff'), (14, '...................ffff'), (15, '..................ffff'),
        (16, '.................ffff'), (17, '................ffff')],
    1: [(11, '........................fff'), (12, '.......................ffff'), (13, '.......................fff'),
        (14, '......................ffff'), (15, '.....................ffff'), (16, '...................fffff'),
        (17, '.................fffff')],
    2: [(15, '........................fff'), (16, '.......................ffff'), (17, '......................ffff'),
        (18, '....................fffff'), (19, '..................fffff'), (20, '................fffff')],
}


def cat_base(tail):
    body = outline(cat_grid(CAT_BODY, start=11))
    head = outline(cat_grid(CAT_HEAD, start=1))
    paws = outline(cat_grid(CAT_PAWS, start=21), light=False)
    t = empty(CW, CH)
    for y, row in CAT_TAILS[tail]:
        for x, ch in enumerate(row):
            if ch != '.':
                t[y][x] = ch
    t = outline(t)
    tip = [(x, y) for y, row in CAT_TAILS[tail][:2] for x, ch in enumerate(row) if ch == 'f']
    g = stack(t, body, head, paws)
    put(g, [p for p in tip if t[p[1]][p[0]] != 'O'], 'd')
    # tabby stripes
    put(g, [(9, 4), (10, 4), (7, 5), (12, 5), (9, 6), (10, 6)], 'd')
    put(g, [(2, 14), (3, 14), (2, 16), (3, 16), (17, 14), (16, 14), (17, 16), (16, 16)], 'd')
    return g


def cat_face(g, kind):
    if kind == 'open':
        put(g, [(5, 6), (6, 6), (5, 7), (6, 7), (13, 6), (14, 6), (13, 7), (14, 7)], 'e')
        put(g, [(5, 6), (13, 6)], 'i')
    elif kind == 'blink':
        put(g, [(4, 7), (5, 7), (6, 7), (13, 7), (14, 7), (15, 7)], 'e')
    elif kind == 'happy':
        put(g, [(4, 7), (5, 6), (6, 6), (7, 7), (12, 7), (13, 6), (14, 6), (15, 7)], 'e')
    put(g, [(9, 8), (10, 8)], 'r')                                    # nose
    put(g, [(8, 9), (11, 9), (9, 10), (10, 10)], 'e')                 # mouth
    if kind == 'happy':
        put(g, [(9, 11), (10, 11)], 't')                              # little open mouth
    put(g, [(3, 8), (4, 8), (15, 8), (16, 8)], 'b')                   # blush
    return g


LOAF_BODY = [
    '.........fffffffffffff',          # 12
    '.......fffffffffffffffff',
    '......ffffffffffffffffffff',
    '.....ffffffffffffffffffffff',
    '.....fffffffffffffffffffffff',    # 16
    '.....fffffffffffffffffffffff',
    '.....fffffffffffffffffffffff',
    '.....fffffffffffffffffffffff',
    '.....fffffffffffffffffffffff',    # 20
    '.....ffffffffffffffffffffff',
    '......ffffffffffffffffffff',
    '.......ffffffffffffffffff',       # 23
]
LOAF_TAIL = ['..............................', '...........fffffffffffffffff', '..........fffffffffffffffff']


def cat_loaf(breath):
    oy = 7
    rows = [r.ljust(CW, '.') for r in LOAF_BODY]
    body = outline(grid(rows, start=12 - (1 if breath else 0), width=CW, height=CH))
    put(body, [(14, 15 - breath), (15, 14 - breath), (19, 15 - breath), (20, 14 - breath), (24, 16 - breath), (25, 15 - breath)], 'd')
    head = outline(cat_grid(CAT_HEAD, start=1 + oy))
    paws = outline(cat_grid(['...zzz....', '..zzzzz...'], start=19), light=False)
    g = stack(body, head, paws)
    put(g, [(9, 4 + oy), (10, 4 + oy), (7, 5 + oy), (12, 5 + oy), (9, 6 + oy), (10, 6 + oy)], 'd')
    put(g, [(4, 7 + oy), (5, 7 + oy), (6, 7 + oy), (13, 7 + oy), (14, 7 + oy), (15, 7 + oy)], 'e')   # sleepy eyes
    put(g, [(9, 8 + oy), (10, 8 + oy)], 'r')
    put(g, [(9, 9 + oy), (10, 9 + oy)], 'e')
    put(g, [(3, 8 + oy), (4, 8 + oy), (15, 8 + oy), (16, 8 + oy)], 'b')
    return g


def cat_frames():
    frames = {}
    for t in (0, 1, 2):
        frames[f'sit{t}'] = cat_face(cat_base(t), 'open')
    frames['blink'] = cat_face(cat_base(0), 'blink')
    frames['happy'] = cat_face(cat_base(1), 'happy')
    frames['happy2'] = cat_face(cat_base(2), 'happy')
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
    cols = range(0, 16) if side == 0 else range(16, 32)
    for x in cols:
        for y in range(37, H - 1):
            out[y][x] = g[y + 1][x]
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

    meta = {'cell': [W, H], 'cols': cols, 'layers': index,
            'cat': {'cell': [CW, CH], 'frames': list(cf.keys())},
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
