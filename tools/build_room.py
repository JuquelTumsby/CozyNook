#!/usr/bin/env python3
"""
CozyNook room painter
=====================
Paints the pixel-art bedroom used on the My Room page.

Run it from the project folder:   python3 tools/build_room.py

Outputs (assets/room/):
  room-day.png       the full room, 320 x 140 pixels
  window-night.png   a night-time window that is laid over the day window
  room-meta.js       positions of the bed, blanket, lamp, computer ... used
                     by assets/sprites.js and the clickable hotspots

The room is drawn at a tiny size and the browser scales it up with crisp
"pixelated" rendering, so every pixel here becomes a chunky pixel on screen.
"""
from PIL import Image
import json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'room')
RW, RH = 320, 140
random.seed(7)

O = '#3a2630'    # outline used everywhere

# colour ramps: base -> (dark, shade, base, light)
RAMP = {
    'wood':    ('#5e3823', '#8a5636', '#b0764a', '#cf9562'),
    'dwood':   ('#4a2a1d', '#6e4029', '#8f5a3a', '#ad7550'),
    'teal':    ('#33585a', '#457876', '#5e9c94', '#7cb8ae'),
    'curtain': ('#8e3534', '#b84a3d', '#e2664f', '#f48c6c'),
    'leaf':    ('#2f6b3a', '#3f8a45', '#5fb35a', '#8bd36f'),
    'pot':     ('#7c3d2a', '#a9563a', '#d8794a', '#ef9d68'),
    'cream':   ('#b8a48c', '#e3d3c0', '#fff4e4', '#ffffff'),
    'beige':   ('#8f8573', '#c4baa6', '#e6dfcf', '#fbf7ee'),
    'yellow':  ('#a8701f', '#d39b2c', '#f7c948', '#ffe28a'),
    'purple':  ('#3c2f6e', '#54449a', '#6b5bb5', '#8d7fd6'),
    'blue':    ('#2c4778', '#355a96', '#4f7fc4', '#79a5e0'),
    'cork':    ('#8a5a33', '#b07a45', '#d29a5f', '#e6b67c'),
    'plum':    ('#3d2b45', '#4e3a5a', '#66507a', '#816a96'),
}


class Pix:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.p = self.img.load()

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            if c is None:
                return
            self.p[x, y] = hexc(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def box(self, x, y, w, h, ramp, outline=True, light=True):
        """Outlined, shaded box (light from the top-left)."""
        d, s, b, l = RAMP[ramp]
        self.rect(x, y, w, h, b)
        if light:
            self.hline(x + 1, y + 1, w - 2, l)
            self.vline(x + 1, y + 1, h - 2, l)
        self.hline(x + 1, y + h - 2, w - 2, s)
        self.vline(x + w - 2, y + 1, h - 2, s)
        if outline:
            self.frame(x, y, w, h, O)

    def frame(self, x, y, w, h, c):
        self.hline(x, y, w, c); self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c); self.vline(x + w - 1, y, h, c)

    def dither(self, x, y, w, h, c1, c2, mode='check'):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, c1 if (xx + yy) % 2 == 0 else c2)

    def ellipse(self, cx, cy, rx, ry, c, edge=None):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                v = ((xx - cx) / (rx + .5)) ** 2 + ((yy - cy) / (ry + .5)) ** 2
                if v <= 1:
                    self.px(xx, yy, c)
        if edge:
            for yy in range(cy - ry, cy + ry + 1):
                for xx in range(cx - rx, cx + rx + 1):
                    inside = lambda a, b: ((a - cx) / (rx + .5)) ** 2 + ((b - cy) / (ry + .5)) ** 2 <= 1
                    if inside(xx, yy) and not all(inside(xx + dx, yy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        self.px(xx, yy, edge)

    def sprite(self, x, y, rows, pal):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != '.':
                    self.px(x + i, y + j, pal[ch])


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# --------------------------------------------------------------------- pieces
FLOOR_Y = 104


def wall(c):
    # upper wallpaper: warm butter with a tiny diamond motif
    c.rect(0, 0, RW, FLOOR_Y, '#f6e2b8')
    for y in range(4, 66, 10):
        for x in range((y // 10) % 2 * 8 + 4, RW, 16):
            c.px(x, y, '#e9cf9c'); c.px(x - 1, y + 1, '#e9cf9c'); c.px(x + 1, y + 1, '#e9cf9c'); c.px(x, y + 2, '#e9cf9c')
            c.px(x, y + 1, '#fff2d3')
    # top crown moulding
    c.rect(0, 0, RW, 3, '#d9b98a'); c.hline(0, 3, RW, '#c7a271')
    # teal wainscoting
    c.rect(0, 70, RW, FLOOR_Y - 70, RAMP['teal'][2])
    c.hline(0, 68, RW, RAMP['teal'][3]); c.hline(0, 69, RW, RAMP['teal'][3])
    c.hline(0, 67, RW, O); c.hline(0, 70, RW, RAMP['teal'][1])
    for x in range(6, RW, 22):
        c.frame(x, 74, 16, 25, RAMP['teal'][1])
        c.hline(x + 1, 75, 14, RAMP['teal'][3])
        c.vline(x + 1, 75, 23, RAMP['teal'][3])
    # skirting board
    c.rect(0, FLOOR_Y - 4, RW, 4, '#fff4e4'); c.hline(0, FLOOR_Y - 4, RW, O); c.hline(0, FLOOR_Y - 1, RW, '#c9b49a')


def floor(c):
    c.rect(0, FLOOR_Y, RW, RH - FLOOR_Y, RAMP['wood'][2])
    row_h = 6
    for i, y in enumerate(range(FLOOR_Y, RH, row_h)):
        c.hline(0, y, RW, RAMP['wood'][0] if i == 0 else RAMP['wood'][1])
        c.hline(0, y + 1, RW, RAMP['wood'][3])
        off = (i * 23) % 40
        for x in range(off, RW, 40):
            c.vline(x, y + 1, row_h - 1, RAMP['wood'][1])
            c.vline(x + 1, y + 1, row_h - 1, RAMP['wood'][3])
        # wood grain flecks
        for _ in range(10):
            gx = random.randrange(0, RW); gy = y + random.randrange(2, row_h)
            c.hline(gx, gy, random.randrange(2, 6), RAMP['wood'][1])
    # soft shadow under the wall
    c.dither(0, FLOOR_Y + 1, RW, 1, RAMP['wood'][1], RAMP['wood'][2])


def window(c, night=False):
    x, y, w, h = 98, 10, 76, 52
    # frame
    c.box(x, y, w, h, 'wood')
    sx, sy, sw, sh = x + 4, y + 4, w - 8, h - 8
    if not night:
        bands = ['#6ab8e6', '#7fc6ee', '#96d4f3', '#b2e2f7']
        for i, col in enumerate(bands):
            c.rect(sx, sy + i * 6, sw, sh - i * 6, col)
            if i:
                c.dither(sx, sy + i * 6, sw, 1, bands[i - 1], col)
        # sun
        c.ellipse(sx + 54, sy + 9, 4, 4, '#ffe58a', '#ffcf4d')
        # clouds
        for cx, cy in ((sx + 14, sy + 8), (sx + 40, sy + 16)):
            c.ellipse(cx, cy, 6, 2, '#ffffff'); c.ellipse(cx - 4, cy + 1, 4, 2, '#ffffff'); c.ellipse(cx + 5, cy + 1, 4, 2, '#ffffff')
            c.hline(cx - 7, cy + 3, 16, '#d6edf8')
        hill1, hill2, tree = '#8fd07a', '#5fae5c', '#3f8a45'
    else:
        bands = ['#1b2150', '#232b63', '#2d3874', '#3a4785']
        for i, col in enumerate(bands):
            c.rect(sx, sy + i * 6, sw, sh - i * 6, col)
            if i:
                c.dither(sx, sy + i * 6, sw, 1, bands[i - 1], col)
        # moon
        c.ellipse(sx + 52, sy + 9, 5, 5, '#fff2c2', '#f3d98a')
        c.ellipse(sx + 55, sy + 7, 4, 4, bands[0])
        for (px_, py_) in ((sx + 6, sy + 5), (sx + 18, sy + 12), (sx + 30, sy + 4), (sx + 40, sy + 15), (sx + 12, sy + 20), (sx + 62, sy + 22), (sx + 25, sy + 25)):
            c.px(px_, py_, '#ffffff')
            if (px_ + py_) % 3 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c.px(px_ + dx, py_ + dy, '#9fb0ff')
        hill1, hill2, tree = '#2f5b5a', '#244848', '#1a3a3a'
    # hills
    for xx in range(sx, sx + sw):
        t = xx - sx
        top1 = sy + 26 + int(4 * __import__('math').sin(t / 9.0))
        top2 = sy + 34 + int(3 * __import__('math').sin(t / 6.0 + 2))
        c.vline(xx, top1, sy + sh - top1, hill1)
        c.vline(xx, top2, sy + sh - top2, hill2)
    for tx in (sx + 8, sx + 21, sx + 50, sx + 60):
        c.rect(tx, sy + 27, 3, 5, tree); c.rect(tx - 1, sy + 29, 5, 3, tree); c.vline(tx + 1, sy + 32, 3, '#5e3823')
    # glass shine
    if not night:
        for k in range(6):
            c.px(sx + 4 + k, sy + 12 - k, '#e7f6ff'); c.px(sx + 5 + k, sy + 12 - k, '#e7f6ff')
    # mullions
    c.rect(x + w // 2 - 2, y + 2, 4, h - 4, RAMP['wood'][2]); c.vline(x + w // 2 - 2, y + 4, h - 8, RAMP['wood'][3])
    c.vline(x + w // 2 + 1, y + 4, h - 8, RAMP['wood'][1])
    c.rect(x + 2, y + h // 2 - 1, w - 4, 3, RAMP['wood'][2]); c.hline(x + 4, y + h // 2 - 1, w - 8, RAMP['wood'][3])
    c.hline(x + 4, y + h // 2 + 1, w - 8, RAMP['wood'][1])
    c.frame(sx - 1, sy - 1, sw + 2, sh + 2, RAMP['wood'][0])


def window_extras(c):
    x, y, w, h = 98, 10, 76, 52
    # sill
    c.box(x - 5, y + h - 1, w + 10, 5, 'cream')
    # curtain rod
    c.rect(x - 14, y - 4, w + 28, 3, RAMP['yellow'][1]); c.hline(x - 14, y - 4, w + 28, RAMP['yellow'][3])
    c.frame(x - 15, y - 5, w + 30, 5, O)
    c.ellipse(x - 16, y - 3, 2, 2, RAMP['yellow'][2], O); c.ellipse(x + w + 15, y - 3, 2, 2, RAMP['yellow'][2], O)
    # curtains with folds, tied back
    for side in (0, 1):
        cx0 = x - 12 if side == 0 else x + w - 4
        for yy in range(y - 1, y + h + 10):
            t = yy - y
            width = 16 if t < 22 else (10 if t < 28 else 13 + (t - 28) // 3)
            width = min(width, 18)
            xs = cx0 if side == 0 else cx0 + 16 - width
            for k in range(width):
                xx = xs + k
                fold = (k + (0 if side == 0 else 1)) % 5
                col = RAMP['curtain'][3] if fold == 1 else RAMP['curtain'][1] if fold == 4 else RAMP['curtain'][2]
                c.px(xx, yy, col)
            c.px(xs, yy, O); c.px(xs + width - 1, yy, O)
        c.hline(cx0 if side == 0 else cx0 + 16 - 14, y + h + 10, 14, O)
        # tie-back
        tx = cx0 + 2 if side == 0 else cx0 + 4
        c.rect(tx, y + 24, 10, 3, RAMP['yellow'][2]); c.frame(tx - 1, y + 23, 12, 5, O)
    # flowers on the sill
    for i, (fx, col) in enumerate(((x + 6, '#ef6b8a'), (x + 62, '#f7c948'))):
        c.box(fx, y + h - 7, 8, 7, 'pot')
        c.vline(fx + 3, y + h - 12, 5, RAMP['leaf'][1]); c.px(fx + 2, y + h - 10, RAMP['leaf'][2]); c.px(fx + 5, y + h - 9, RAMP['leaf'][2])
        c.px(fx + 4, y + h - 10, RAMP['leaf'][2])
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            c.px(fx + 3 + dx, y + h - 14 + dy, col)
        c.px(fx + 3, y + h - 14, '#fff4b8')


def books_row(c, x, y, w, h, seed):
    r = random.Random(seed)
    cols = ['#e2554e', '#f2b33d', '#4f8fd0', '#6cbf6a', '#9a6bc9', '#ef8db0', '#3c6e9e', '#f08a3e']
    xx = x
    while xx < x + w - 3:
        bw = r.choice((3, 3, 4, 4, 5))
        bh = h - r.choice((0, 1, 2, 3))
        if xx + bw > x + w:
            break
        col = r.choice(cols)
        if r.random() < 0.15 and xx + bw + 4 < x + w:   # leaning book
            for k in range(bh - 1):
                c.hline(xx + k // 4, y + h - 1 - k, bw, col)
            xx += bw + 3
            continue
        c.rect(xx, y + h - bh, bw, bh, col)
        c.vline(xx, y + h - bh, bh, O)
        c.hline(xx, y + h - bh, bw, O)
        c.hline(xx + 1, y + h - bh + 2, bw - 1, '#fff4e4')
        c.vline(xx + bw - 1, y + h - bh + 1, bh - 1, shade_of(col))
        xx += bw
    c.vline(xx, y, h, O)


def shade_of(col):
    r, g, b, _ = hexc(col)
    return '#%02x%02x%02x' % (int(r * .72), int(g * .68), int(b * .78))


def bookshelf(c):
    x, y, w, h = 10, 26, 46, FLOOR_Y - 26 + 2
    c.box(x, y, w, h, 'dwood')
    c.rect(x + 3, y + 3, w - 6, h - 6, RAMP['dwood'][0])
    shelves = [y + 3, y + 21, y + 39, y + 57]
    for i, sy in enumerate(shelves):
        sh = 16
        if i == 3:
            sh = h - 6 - 54
        c.rect(x + 3, sy, w - 6, sh, '#4a2a1d')
        c.dither(x + 3, sy, w - 6, 1, '#3a2018', '#4a2a1d')
        if i == 1:
            books_row(c, x + 3, sy + 3, 24, sh - 3, 11)
            # little trophy
            c.rect(x + 32, sy + 12, 6, 2, RAMP['yellow'][1]); c.rect(x + 34, sy + 9, 2, 3, RAMP['yellow'][2])
            c.rect(x + 31, sy + 4, 8, 5, RAMP['yellow'][2]); c.hline(x + 32, sy + 5, 2, RAMP['yellow'][3]); c.frame(x + 31, sy + 4, 8, 5, O)
            c.px(x + 30, sy + 5, O); c.px(x + 39, sy + 5, O)
        elif i == 2:
            books_row(c, x + 13, sy + 3, w - 16, sh - 3, 21)
            # globe
            c.ellipse(x + 8, sy + 8, 4, 4, '#4f8fd0', O); c.rect(x + 6, sy + 6, 3, 2, '#6cbf6a'); c.px(x + 9, sy + 9, '#6cbf6a')
            c.rect(x + 6, sy + 13, 5, 2, RAMP['wood'][1])
        elif i == 0:
            books_row(c, x + 3, sy + 3, w - 6, sh - 3, 5)
        else:
            # storage boxes
            c.box(x + 5, sy + 3, 16, sh - 3, 'blue'); c.rect(x + 11, sy + 6, 4, 2, '#fff4e4')
            c.box(x + 23, sy + 3, 16, sh - 3, 'curtain'); c.rect(x + 29, sy + 6, 4, 2, '#fff4e4')
        # shelf board
        c.rect(x + 2, sy + sh, w - 4, 2, RAMP['dwood'][3]); c.hline(x + 2, sy + sh + 1, w - 4, RAMP['dwood'][1])
    # plant on top
    plant(c, x + 30, y - 2, big=False)


def leaf(c, cx, cy, dirx, size):
    """A pointed pixel leaf. dirx = -1 (points left) / 1 (points right)."""
    rx, ry = size + 1, size - 1
    c.ellipse(cx, cy, rx, ry, RAMP['leaf'][2], O)
    c.px(cx + dirx * (rx + 1), cy - 1, O)
    c.hline(cx - rx + 2 if dirx > 0 else cx, cy, rx - 1, RAMP['leaf'][1])   # vein
    c.px(cx - dirx, cy - ry + 1, RAMP['leaf'][3]); c.px(cx, cy - ry + 1, RAMP['leaf'][3])


def plant(c, x, y, big=False):
    """x, y = bottom-left of the pot."""
    pw, ph = (13, 11) if big else (10, 8)
    mid = x + pw // 2
    if big:
        leaves = [(0, -25, 1, 4), (-7, -19, -1, 5), (7, -17, 1, 5), (-9, -9, -1, 5), (9, -8, 1, 5), (-2, -12, -1, 4), (3, -4, 1, 4), (-5, -2, -1, 4)]
    else:
        leaves = [(0, -11, 1, 3), (-5, -6, -1, 4), (5, -5, 1, 4), (-1, -2, -1, 3)]
    for lx, ly, d, sz in leaves:
        cx, cy = mid + lx, y - ph + ly
        # stem from the pot to the leaf
        c.vline(mid + lx // 2, cy + 1, max(0, y - ph - cy - 1), RAMP['leaf'][1])
    for lx, ly, d, sz in leaves:
        leaf(c, mid + lx, y - ph + ly, d, sz)
    c.box(x, y - ph, pw, ph, 'pot')
    c.rect(x - 1, y - ph, pw + 2, 3, RAMP['pot'][2]); c.hline(x, y - ph + 1, pw, RAMP['pot'][3]); c.frame(x - 1, y - ph, pw + 2, 3, O)


def hanging_plant(c, x):
    c.vline(x, 3, 14, '#8a6a4a')
    c.vline(x - 4, 3, 13, '#8a6a4a'); c.vline(x + 4, 3, 13, '#8a6a4a')
    c.box(x - 6, 16, 13, 8, 'cream')
    for k, (dx, ln) in enumerate(((-5, 16), (-2, 22), (2, 18), (5, 12), (0, 10))):
        for t in range(ln):
            yy = 22 + t
            xx = x + dx + (1 if (t // 3) % 2 else 0)
            if t % 3 == 0:
                c.px(xx - 1, yy, RAMP['leaf'][2]); c.px(xx + 1, yy, RAMP['leaf'][3])
                c.px(xx - 2, yy, O); c.px(xx + 2, yy, O)
            c.px(xx, yy, RAMP['leaf'][1])
    for dx in (-5, -2, 2, 5):
        c.ellipse(x + dx, 22, 2, 2, RAMP['leaf'][2], O)


def bed(c):
    # headboard
    hx, hy = 66, 64
    c.box(hx, hy, 9, FLOOR_Y + 12 - hy, 'wood')
    c.rect(hx - 1, hy - 2, 11, 3, RAMP['wood'][3]); c.frame(hx - 1, hy - 2, 11, 3, O)
    c.ellipse(hx + 4, hy + 8, 2, 2, RAMP['wood'][3], RAMP['wood'][1])
    # footboard
    fx = 186
    c.box(fx, 82, 7, FLOOR_Y + 12 - 82, 'wood')
    c.rect(fx - 1, 80, 9, 3, RAMP['wood'][3]); c.frame(fx - 1, 80, 9, 3, O)
    # frame + legs
    c.box(74, 100, fx - 74, 9, 'wood')
    c.rect(77, 109, 4, 6, RAMP['wood'][0]); c.rect(fx - 5, 109, 4, 6, RAMP['wood'][0])
    # mattress
    c.rect(74, 88, fx - 74, 12, '#fff4e4'); c.hline(74, 88, fx - 74, O)
    c.hline(74, 98, fx - 74, '#e3d3c0'); c.hline(74, 99, fx - 74, '#c9b49a')
    # pillow
    c.ellipse(86, 86, 10, 5, '#fffaf0', O)
    c.hline(80, 88, 12, '#e8dccb'); c.px(83, 84, '#ffffff'); c.px(84, 84, '#ffffff')
    c.px(86, 87, '#e8dccb'); c.px(87, 88, '#e8dccb')


# blanket area (drawn live in the browser so its colour/pattern can change)
BLANKET = {'x': 96, 'y': 85, 'w': 90, 'h': 22}


def rug(c):
    cx, cy, rx, ry = 244, 124, 52, 11
    c.ellipse(cx, cy, rx, ry, RAMP['blue'][1], O)
    c.ellipse(cx, cy, rx - 3, ry - 2, RAMP['blue'][2])
    c.ellipse(cx, cy, rx - 8, ry - 4, '#f2c35a')
    c.ellipse(cx, cy, rx - 11, ry - 5, RAMP['blue'][2])
    c.ellipse(cx, cy, rx - 17, ry - 7, '#e2664f')
    c.ellipse(cx, cy, rx - 20, ry - 8, RAMP['blue'][3])
    # tassels
    for x in range(cx - rx + 6, cx + rx - 5, 3):
        pass
    for x in (cx - rx - 1, cx + rx + 1):
        for dy in (-2, 0, 2):
            c.px(x, cy + dy, '#fff4e4')


def desk(c):
    x, y, w = 214, 74, 96
    # desk top
    c.box(x, y, w, 6, 'wood')
    # left drawer unit
    c.box(x + 3, y + 6, 26, FLOOR_Y + 14 - (y + 6), 'wood')
    for k in range(3):
        dy = y + 8 + k * 11
        c.frame(x + 5, dy, 22, 10, RAMP['wood'][1])
        c.hline(x + 6, dy + 1, 20, RAMP['wood'][3])
        c.rect(x + 14, dy + 4, 4, 2, RAMP['yellow'][2]); c.frame(x + 13, dy + 3, 6, 4, O)
    # right leg
    c.box(x + w - 8, y + 6, 6, FLOOR_Y + 14 - (y + 6), 'wood')
    c.rect(x + 29, y + 6, w - 37, 2, RAMP['wood'][0])
    # chair (behind character area, tucked under desk)
    c.box(x + 44, y + 12, 22, 6, 'curtain')
    c.box(x + 52, y + 18, 6, 16, 'plum')
    c.rect(x + 46, y + 34, 18, 2, RAMP['plum'][1]); c.frame(x + 45, y + 33, 20, 4, O)


def monitor(c):
    x, y = 236, 44
    c.box(x, y, 40, 28, 'beige')
    c.rect(x + 3, y + 3, 34, 20, '#2b3555')
    # screen content: a little task list + heart
    c.dither(x + 3, y + 3, 34, 20, '#2b3555', '#2f3a5c')
    c.rect(x + 3, y + 3, 34, 3, '#6b5bb5')
    for k, col in enumerate(('#7fe0c0', '#f7c948', '#ef8db0')):
        c.rect(x + 6, y + 9 + k * 4, 2, 2, col)
        c.hline(x + 10, y + 9 + k * 4, 12 - k * 2, '#c9d4f0')
        c.hline(x + 10, y + 10 + k * 4, 8, '#7d8ab0')
    c.sprite(x + 26, y + 10, ['.rr.rr.', 'rrrrrrr', 'rrrrrrr', '.rrrrr.', '..rrr..', '...r...'], {'r': '#ef6b8a'})
    c.px(x + 27, y + 11, '#ffd0dc')
    c.px(x + 4, y + 7, '#ffffff')
    # stand
    c.rect(x + 16, y + 28, 8, 2, RAMP['beige'][1]); c.box(x + 11, y + 29, 18, 3, 'beige', light=False)
    c.px(x + 34, y + 25, '#7fe0c0')    # power light
    # keyboard + mug
    c.box(x - 2, 70, 26, 4, 'beige', light=False)
    for k in range(5):
        c.hline(x + 1 + k * 4, 71, 2, RAMP['beige'][3])
    c.box(x + 30, 66, 7, 8, 'curtain'); c.vline(x + 37, 68, 3, O); c.px(x + 38, 68, O); c.px(x + 38, 70, O)
    c.px(x + 32, 63, '#ffffff'); c.px(x + 33, 62, '#ffffff'); c.px(x + 34, 64, '#ffffff')


LAMP = {'x': 288, 'y': 48, 'w': 18, 'h': 26}


def desk_lamp(c):
    x, y = LAMP['x'], LAMP['y']
    # arm
    c.rect(x + 8, y + 10, 2, 14, RAMP['plum'][2]); c.vline(x + 8, y + 10, 14, O); c.vline(x + 10, y + 10, 14, O)
    c.box(x + 3, y + 22, 12, 4, 'plum')
    # shade (yellow cone)
    rows = ['....OOOOOOOO....', '...OyyyyyyyyO...', '..OyYyyyyyyyyO..', '.OyYyyyyyyyyyyO.', 'OyYyyyyyyyyyyydO', 'OOOOOOOOOOOOOOOO']
    c.sprite(x + 1, y + 4, rows, {'O': O, 'y': RAMP['yellow'][2], 'Y': RAMP['yellow'][3], 'd': RAMP['yellow'][1]})
    c.rect(x + 7, y + 10, 4, 1, '#fff6c2')


def poster(c):
    x, y, w, h = 190, 14, 22, 30
    c.box(x, y, w, h, 'cream')
    c.rect(x + 3, y + 3, w - 6, h - 6, RAMP['purple'][2])
    c.dither(x + 3, y + 3, w - 6, 6, RAMP['purple'][1], RAMP['purple'][2])
    # mountains + stars
    for k in range(w - 6):
        top = y + h - 10 - max(0, 6 - abs(k - 6)) - max(0, 4 - abs(k - 13))
        c.vline(x + 3 + k, top, y + h - 3 - top, '#3c6e9e')
        c.px(x + 3 + k, top, '#fff4e4' if abs(k - 6) < 2 else '#79a5e0')
    for sx_, sy_ in ((x + 6, y + 6), (x + 14, y + 9), (x + 10, y + 13), (x + 16, y + 5)):
        c.px(sx_, sy_, '#ffe28a')
    c.ellipse(x + 15, y + 9, 2, 2, '#ffe28a')
    c.px(x + 10, y - 2, O); c.vline(x + 10, y - 1, 1, O)


def corkboard(c):
    x, y, w, h = 240, 10, 40, 26
    c.box(x, y, w, h, 'wood')
    c.rect(x + 2, y + 2, w - 4, h - 4, RAMP['cork'][2])
    r = random.Random(3)
    for _ in range(40):
        c.px(x + 2 + r.randrange(w - 4), y + 2 + r.randrange(h - 4), RAMP['cork'][1])
    notes = [(x + 4, y + 4, '#ffe36b'), (x + 15, y + 6, '#ff9fb8'), (x + 27, y + 3, '#8fd3ff'), (x + 6, y + 14, '#a8e07a'), (x + 25, y + 14, '#ffbf6b')]
    for nx, ny, col in notes:
        c.rect(nx, ny, 9, 8, col)
        c.hline(nx + 1, ny + 3, 6, shade_of(col)); c.hline(nx + 1, ny + 5, 4, shade_of(col))
        c.px(nx + 4, ny, '#e2554e'); c.px(nx + 4, ny - 1, '#8e3534')
    # photo
    c.rect(x + 16, y + 15, 8, 8, '#fff4e4'); c.rect(x + 17, y + 16, 6, 4, '#79a5e0'); c.rect(x + 17, y + 19, 6, 1, '#6cbf6a')


def clock(c):
    cx, cy = 225, 26
    c.ellipse(cx, cy, 7, 7, RAMP['curtain'][2], O)
    c.ellipse(cx, cy, 5, 5, '#fff4e4')
    for dx, dy in ((0, -4), (4, 0), (0, 4), (-4, 0)):
        c.px(cx + dx, cy + dy, RAMP['plum'][2])
    c.vline(cx, cy - 3, 3, O); c.hline(cx, cy, 3, O)
    c.px(cx - 2, cy - 7, O); c.px(cx + 2, cy - 7, O); c.px(cx - 3, cy - 8, RAMP['yellow'][2]); c.px(cx + 3, cy - 8, RAMP['yellow'][2])


def big_plant(c):
    x = 306
    plant(c, x - 7, FLOOR_Y + 14, big=True)


def baseboard_shadows(c):
    # contact shadows under furniture on the floor
    for x0, x1 in ((10, 56), (217, 244), (300, 308)):
        c.dither(x0, FLOOR_Y + 2, x1 - x0, 1, '#8a5636', RAMP['wood'][2])


def paint(night=False):
    c = Pix(RW, RH)
    wall(c)
    floor(c)
    window(c, night)
    window_extras(c)
    hanging_plant(c, 70)
    bookshelf(c)
    poster(c)
    clock(c)
    corkboard(c)
    rug(c)
    desk(c)
    monitor(c)
    desk_lamp(c)
    big_plant(c)
    bed(c)
    baseboard_shadows(c)
    return c


# --------------------------------------------------------------------- shop decorations (32 x 24 each)
DECOR_ORDER = ['lights', 'plush', 'books', 'flower', 'moon', 'plant', 'catbed', 'rug', 'poster', 'beanbag', 'fishtank', 'guitar']


def decor_lights(c):
    import math
    bulbs = ['#ef5b6b', '#f7c948', '#4f8fd0', '#6cbf6a', '#ef8db0', '#f08a3e']
    pts = []
    for x in range(1, 31):
        y = 3 + int(round(5 * math.sin(math.pi * (x - 1) / 29)))
        c.px(x, y, '#5e3823'); pts.append((x, y))
    c.px(0, 2, O); c.px(31, 2, O)
    for k, x in enumerate(range(3, 30, 5)):
        y = pts[x - 1][1] + 1
        col = bulbs[k % len(bulbs)]
        c.rect(x, y, 2, 1, '#8f8573')
        c.rect(x - 1, y + 1, 4, 4, col); c.frame(x - 1, y + 1, 4, 4, O)
        c.px(x - 1, y + 1, None)
        c.px(x, y + 2, '#ffffff')
        c.px(x, y + 5, O); c.px(x + 1, y + 5, O)
        # glow
        for dx, dy in ((-2, 3), (3, 3), (0, 6), (1, 6)):
            c.px(x + dx, y + dy, None)


def decor_plush(c):
    pink, pd, pl = '#f4a6b8', '#d27b93', '#ffd0dc'
    c.ellipse(16, 18, 7, 5, pink, O)          # body
    c.ellipse(16, 10, 8, 6, pink, O)          # head
    for ex in (10, 21):                        # ears
        c.sprite(ex - 1, 2, ['.O..', 'OpO.', 'OppO'], {'O': O, 'p': pink})
    c.px(10, 4, pl); c.px(21, 4, pl)
    c.hline(11, 10, 3, O); c.hline(18, 10, 3, O)   # sleepy eyes
    c.px(16, 12, '#b2505e')
    c.px(9, 12, '#ef7b95'); c.px(23, 12, '#ef7b95')
    c.px(12, 7, pl); c.px(13, 6, pl)
    c.ellipse(16, 19, 3, 2, pl)               # tummy
    c.ellipse(11, 22, 2, 1, pd, O); c.ellipse(21, 22, 2, 1, pd, O)   # feet
    c.hline(11, 15, 11, '#4f8fd0'); c.hline(11, 16, 11, '#79a5e0'); c.rect(18, 17, 2, 3, '#4f8fd0')   # little scarf


def decor_books(c):
    for (x, y, w, col) in ((5, 18, 22, '#4f8fd0'), (7, 13, 19, '#e2554e'), (4, 8, 20, '#f7c948')):
        c.rect(x, y, w, 5, col); c.frame(x, y, w, 5, O)
        c.hline(x + 1, y + 1, w - 2, '#ffffff' if col == '#f7c948' else '#fff4e4')
        c.rect(x + w - 4, y + 1, 3, 3, '#fff4e4'); c.vline(x + w - 4, y + 1, 3, O)
        c.hline(x + 2, y + 3, w - 7, shade_of(col))
    # apple on top
    c.ellipse(19, 5, 2, 2, '#e2554e', O); c.px(18, 4, '#ffb0a0'); c.px(19, 1, '#5e3823'); c.px(20, 1, RAMP['leaf'][2])


def decor_flower(c):
    stems = [(12, 9, '#ef5b6b'), (16, 5, '#f7c948'), (20, 8, '#9a6bc9')]
    for x, top, col in stems:
        c.vline(x, top + 3, 16 - top - 2, RAMP['leaf'][1])
        c.sprite(x - 2, top, ['O.O.O', 'OcOcO', 'OcccO', '.OcO.'], {'O': O, 'c': col})
        c.px(x - 1, top + 1, '#ffffff')
    c.ellipse(10, 13, 2, 1, RAMP['leaf'][2], O); c.ellipse(22, 12, 2, 1, RAMP['leaf'][2], O)
    c.box(9, 16, 14, 8, 'pot')
    c.rect(8, 16, 16, 3, RAMP['pot'][2]); c.hline(9, 17, 14, RAMP['pot'][3]); c.frame(8, 16, 16, 3, O)


def decor_moon(c):
    c.ellipse(16, 9, 7, 7, '#ffe28a', O)
    c.ellipse(19, 7, 6, 6, None)
    # carve the crescent: clear inner circle
    for yy in range(0, 24):
        for xx in range(0, 32):
            if ((xx - 20) / 6.2) ** 2 + ((yy - 7) / 6.2) ** 2 <= 1:
                c.p[xx, yy] = (0, 0, 0, 0)
    # re-outline the inner edge
    for yy in range(1, 17):
        for xx in range(9, 24):
            if c.p[xx, yy][3] and c.p[xx, yy][:3] != hexc(O)[:3]:
                for dx, dy in ((1, 0), (0, 1), (0, -1), (-1, 0)):
                    if c.p[xx + dx, yy + dy][3] == 0:
                        c.p[xx, yy] = hexc(O)
                        break
    c.px(11, 7, '#fff6c2'); c.px(11, 8, '#fff6c2'); c.px(12, 5, '#fff6c2')
    c.vline(15, 16, 4, RAMP['plum'][2]); c.vline(14, 16, 4, O); c.vline(16, 16, 4, O)
    c.box(10, 20, 12, 4, 'plum')
    for sx, sy in ((25, 3), (27, 11), (5, 4)):
        c.px(sx, sy, '#ffe28a'); c.px(sx - 1, sy, '#f7c948'); c.px(sx + 1, sy, '#f7c948'); c.px(sx, sy - 1, '#f7c948'); c.px(sx, sy + 1, '#f7c948')


def decor_plant(c):
    leaves = [(12, 4), (15, 1), (18, 3), (21, 7), (10, 8)]
    for x, top in leaves:
        for yy in range(top, 17):
            w = 1 if yy < top + 2 else 2
            c.rect(x, yy, w + 1, 1, RAMP['leaf'][2])
            c.px(x - 1, yy, O); c.px(x + w + 1, yy, O)
            if (yy - top) % 4 == 2:
                c.px(x + 1, yy, '#d6f0a0')
        c.px(x, top - 1, O); c.px(x + 1, top - 1, O)
    c.box(9, 16, 15, 8, 'blue')
    c.rect(8, 16, 17, 3, RAMP['blue'][2]); c.hline(9, 17, 15, RAMP['blue'][3]); c.frame(8, 16, 17, 3, O)
    c.rect(14, 20, 5, 2, '#fff4e4')



def decor_catbed(c):
    c.ellipse(16, 17, 14, 6, RAMP['purple'][2], O)
    c.ellipse(16, 15, 11, 3, '#ffd0dc', RAMP['purple'][1])
    c.hline(6, 14, 20, '#ffe3ea')
    c.hline(4, 19, 24, RAMP['purple'][1]); c.hline(5, 20, 22, RAMP['purple'][1])
    c.hline(5, 16, 3, RAMP['purple'][3])
    # paw print on the front
    c.rect(15, 18, 3, 2, '#ffd0dc'); c.px(14, 17, '#ffd0dc'); c.px(16, 16, None); c.px(18, 17, '#ffd0dc')
    # fish toy
    c.sprite(24, 9, ['.bb.b', 'bbbbb', '.bb.b'], {'b': '#4f8fd0'}); c.px(25, 9, '#ffffff')


def decor_rug(c):
    c.ellipse(16, 18, 15, 5, RAMP['yellow'][1], O)
    c.ellipse(16, 18, 12, 3, RAMP['yellow'][2])
    c.ellipse(16, 18, 8, 2, '#ef8db0')
    c.sprite(14, 16, ['..y..', '.yyy.', '..y..'], {'y': '#fff4b8'})
    for x in (1, 30):
        c.px(x - (1 if x < 16 else -1), 17, '#fff4e4'); c.px(x - (1 if x < 16 else -1), 19, '#fff4e4')


def decor_poster(c):
    c.box(7, 1, 18, 22, 'cream')
    c.rect(9, 3, 14, 18, '#1f2752')
    c.dither(9, 3, 14, 5, '#1f2752', '#2d3874')
    c.ellipse(16, 12, 4, 4, '#f08a3e', O); c.px(15, 10, '#ffc28a'); c.px(14, 11, '#ffc28a')
    c.hline(10, 13, 13, '#f7c948'); c.px(10, 12, '#f7c948'); c.px(22, 14, '#f7c948')
    for sx, sy in ((11, 5), (20, 6), (12, 18), (21, 18), (18, 4)):
        c.px(sx, sy, '#ffffff')
    c.px(16, 0, O)


def decor_beanbag(c):
    c.ellipse(16, 17, 13, 6, RAMP['curtain'][2], O)
    c.ellipse(15, 11, 9, 6, RAMP['curtain'][2], O)
    c.ellipse(16, 17, 12, 5, RAMP['curtain'][2])
    c.hline(8, 9, 6, RAMP['curtain'][3]); c.hline(7, 10, 3, RAMP['curtain'][3])
    c.hline(10, 13, 10, RAMP['curtain'][1]); c.px(9, 14, RAMP['curtain'][1]); c.px(20, 14, RAMP['curtain'][1])
    c.hline(6, 21, 20, RAMP['curtain'][1])
    c.vline(23, 12, 6, RAMP['curtain'][1])


def decor_fishtank(c):
    c.rect(3, 6, 26, 15, '#8fd3ff'); c.rect(3, 8, 26, 13, '#5fb6ea')
    c.dither(3, 8, 26, 1, '#8fd3ff', '#5fb6ea')
    c.rect(3, 18, 26, 3, '#f2c35a'); c.px(8, 18, '#d39b2c'); c.px(20, 19, '#d39b2c')
    for x, h in ((6, 7), (8, 5), (24, 8)):
        c.vline(x, 18 - h, h, RAMP['leaf'][2]); c.px(x + 1, 18 - h + 2, RAMP['leaf'][3])
    c.sprite(13, 11, ['..oo.o', '.ooooo', 'oowoo.', '.ooooo', '..oo.o'], {'o': '#f08a3e', 'w': '#ffffff'})
    c.sprite(20, 14, ['.yy.y', 'yyyyy', '.yy.y'], {'y': '#f7c948'})
    for bx, by in ((12, 9), (11, 7), (22, 10)):
        c.px(bx, by, '#e7f6ff')
    c.frame(2, 5, 28, 17, O); c.rect(2, 4, 28, 2, RAMP['plum'][2]); c.frame(2, 4, 28, 2, O)
    c.rect(4, 7, 1, 8, '#e7f6ff')
    c.box(1, 21, 30, 3, 'plum', light=False)


def decor_guitar(c):
    c.rect(15, 1, 3, 3, RAMP['dwood'][1]); c.frame(14, 0, 5, 4, O)
    c.px(13, 1, '#d6d6d6'); c.px(19, 1, '#d6d6d6'); c.px(13, 3, '#d6d6d6'); c.px(19, 3, '#d6d6d6')
    c.rect(15, 4, 3, 9, RAMP['dwood'][2]); c.vline(14, 4, 9, O); c.vline(18, 4, 9, O)
    for y in (6, 8, 10):
        c.hline(15, y, 3, '#d6d6d6')
    c.ellipse(16, 14, 5, 3, '#f08a3e', O)
    c.ellipse(16, 19, 7, 4, '#f08a3e', O)
    c.rect(11, 15, 11, 3, '#f08a3e')
    c.ellipse(16, 16, 2, 1, '#5e3823')
    c.hline(14, 20, 5, '#8a3f1e'); c.px(11, 13, '#ffb07a'); c.px(10, 18, '#ffb07a')
    c.vline(16, 4, 16, '#fff4e4')
    c.box(9, 22, 15, 2, 'plum', light=False)


# --------------------------------------------------------------------- garden (32 x 32 each)
GARDEN_ORDER = ['soil', 'sprout', 'daisy', 'tulip', 'sunflower', 'can']


def soil(c):
    c.ellipse(16, 25, 13, 5, '#7a4a2e', O)
    c.ellipse(16, 24, 11, 3, '#9a6440')
    for x, y in ((9, 25), (21, 26), (14, 27), (24, 24)):
        c.px(x, y, '#c2a07a')
    c.hline(8, 23, 4, '#b07a50')


def stem(c, top, x=16):
    c.vline(x, top, 23 - top, RAMP['leaf'][1])
    c.vline(x + 1, top + 1, 22 - top, RAMP['leaf'][2])


def garden_soil(c):
    soil(c)
    c.hline(12, 22, 8, '#5e3823')   # little seed row


def garden_sprout(c):
    soil(c); stem(c, 15)
    c.ellipse(12, 15, 3, 2, RAMP['leaf'][2], O); c.px(11, 14, RAMP['leaf'][3])
    c.ellipse(21, 13, 3, 2, RAMP['leaf'][2], O); c.px(20, 12, RAMP['leaf'][3])


def garden_daisy(c):
    soil(c); stem(c, 10)
    c.ellipse(12, 18, 3, 1, RAMP['leaf'][2], O); c.ellipse(21, 16, 3, 1, RAMP['leaf'][2], O)
    for dx, dy in ((0, -5), (4, -3), (5, 1), (2, 5), (-2, 5), (-5, 1), (-4, -3)):
        c.ellipse(16 + dx, 8 + dy, 2, 2, '#ffffff', '#c9c0d8')
    c.ellipse(16, 8, 3, 3, '#f7c948', RAMP['yellow'][0]); c.px(15, 7, '#fff4b8')


def garden_tulip(c):
    soil(c); stem(c, 9)
    c.ellipse(12, 19, 2, 4, RAMP['leaf'][2], O); c.ellipse(21, 18, 2, 4, RAMP['leaf'][2], O)
    c.sprite(10, 3, ['O..O..O..O..', 'OrrOrrOrrrO.', 'OrrrrrrrrrO.', 'OrRrrrrrrrO.', 'OrRrrrrrrRO.', '.OrrrrrrRO..', '..OOOOOOO...'],
             {'O': O, 'r': '#ef5b6b', 'R': '#ff9aa6'})
    c.px(12, 5, '#ffffff')


def garden_sunflower(c):
    soil(c); stem(c, 11)
    c.ellipse(11, 17, 3, 2, RAMP['leaf'][2], O); c.ellipse(22, 15, 3, 2, RAMP['leaf'][2], O)
    import math
    for k in range(10):
        a = k * math.pi / 5
        c.ellipse(16 + round(6 * math.cos(a)), 8 + round(6 * math.sin(a)), 2, 2, '#f7c948', RAMP['yellow'][0])
    c.ellipse(16, 8, 4, 4, '#7a4a2e', O)
    c.px(15, 7, '#a8703f'); c.px(17, 9, '#5e3823'); c.px(14, 9, '#5e3823'); c.px(17, 6, '#a8703f')


def garden_can(c):
    c.box(9, 14, 14, 12, 'blue')
    c.rect(11, 17, 10, 2, RAMP['blue'][3])
    # handle
    c.frame(12, 9, 8, 6, O); c.frame(13, 10, 6, 5, RAMP['blue'][2])
    # spout
    for k in range(7):
        c.rect(22 + k, 19 - k, 2, 2, RAMP['blue'][2]); c.px(22 + k, 21 - k, O); c.px(24 + k, 18 - k, O)
    c.rect(28, 10, 3, 3, RAMP['blue'][1]); c.frame(28, 10, 3, 3, O)
    for x, y in ((30, 15), (29, 18), (31, 21)):
        c.px(x, y, '#8fd3ff')


def build_sheet(order, prefix, cw, ch, filename):
    sheet = Image.new('RGBA', (cw * len(order), ch), (0, 0, 0, 0))
    for i, name in enumerate(order):
        c = Pix(cw, ch)
        globals()[prefix + name](c)
        sheet.paste(c.img, (i * cw, 0))
    sheet.save(os.path.join(OUT, filename))


def build_decor():
    sheet = Image.new('RGBA', (32 * len(DECOR_ORDER), 24), (0, 0, 0, 0))
    for i, name in enumerate(DECOR_ORDER):
        c = Pix(32, 24)
        globals()['decor_' + name](c)
        sheet.paste(c.img, (i * 32, 0))
    sheet.save(os.path.join(OUT, 'decor.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    day = paint(False)
    day.img.save(os.path.join(OUT, 'room-day.png'))
    night = paint(True)
    # night overlay = just the window region of the night painting
    wx, wy, ww, wh = 98, 10, 76, 52
    overlay = Image.new('RGBA', (RW, RH), (0, 0, 0, 0))
    overlay.paste(night.img.crop((wx, wy, wx + ww, wy + wh)), (wx, wy))
    overlay.save(os.path.join(OUT, 'window-night.png'))
    build_decor()
    build_sheet(GARDEN_ORDER, 'garden_', 32, 32, 'garden.png')
    meta = {'size': [RW, RH], 'decor': DECOR_ORDER, 'garden': GARDEN_ORDER, 'blanket': BLANKET, 'lamp': LAMP,
            'bed': {'x': 66, 'y': 64, 'w': 128, 'h': 52},
            'computer': {'x': 236, 'y': 44, 'w': 40, 'h': 32},
            'lampGlow': {'x': 297, 'y': 56}}
    with open(os.path.join(OUT, 'room-meta.js'), 'w') as fh:
        fh.write('/* Generated by tools/build_room.py - do not edit by hand. */\n')
        fh.write('window.COZY_ROOM_META = ' + json.dumps(meta) + ';\n')
    print('room painted', RW, 'x', RH)


if __name__ == '__main__':
    main()
