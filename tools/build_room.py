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
RW, RH = 320, 180
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


# --------------------------------------------------------------------- the room
# A 3/4 view (looking into the room from slightly above): back wall at the
# top, a deep wooden floor below, and short side walls for depth.
# The room starts mostly empty on purpose - players fill it from the shop.
WALL_Y = 72          # where the back wall meets the floor
SIDE = 20            # width of the left side wall
SIDE_R = 46          # the right wall is wider: it has the door

RAMP.update({
    'rose':  ('#7a4a6a', '#c98fae', '#e7b3c4', '#f4cfdb'),
    'mauve': ('#5e3a5a', '#9a6a92', '#b98aa8', '#d2a7c2'),
    'oak':   ('#5e3823', '#94613d', '#c08552', '#dca06c'),
    'sheet': ('#9a8aa8', '#ddd0e8', '#fbf6ff', '#ffffff'),
    'chair': ('#5e2f52', '#b65d8f', '#e083b3', '#f6a9cf'),
})


def shade_of(col):
    r, g, b, _ = hexc(col)
    return '#%02x%02x%02x' % (int(r * .72), int(g * .68), int(b * .78))


def side_bottom(x):
    """y of the floor line on the side walls (it slopes towards the viewer)."""
    if x < SIDE:
        return WALL_Y + int((SIDE - x) * 1.6)
    if x >= RW - SIDE_R:
        return WALL_Y + int((x - (RW - SIDE_R - 1)) * 1.25)
    return WALL_Y


def walls(c):
    # back wall: dusty rose wallpaper with soft stripes
    for x in range(RW):
        col = RAMP['rose'][2] if (x // 6) % 2 == 0 else '#ebbccb'
        c.vline(x, 0, WALL_Y, col)
    # little dotted motif
    for y in range(8, 44, 12):
        for x in range((y // 12) % 2 * 6 + 3, RW, 12):
            c.px(x, y, RAMP['rose'][3])
    # lower panelling
    c.rect(0, 46, RW, WALL_Y - 46, RAMP['mauve'][2])
    c.hline(0, 44, RW, RAMP['mauve'][3]); c.hline(0, 45, RW, RAMP['mauve'][1]); c.hline(0, 43, RW, O)
    for x in range(10, RW, 26):
        c.frame(x, 49, 18, 17, RAMP['mauve'][1]); c.hline(x + 1, 50, 16, RAMP['mauve'][3]); c.vline(x + 1, 50, 15, RAMP['mauve'][3])
    # skirting
    c.rect(0, WALL_Y - 4, RW, 4, '#fbf2ff'); c.hline(0, WALL_Y - 4, RW, O); c.hline(0, WALL_Y - 1, RW, '#cdb8d8')
    # ceiling trim
    c.rect(0, 0, RW, 3, RAMP['mauve'][1]); c.hline(0, 3, RW, O)


def side_walls(c):
    for x in list(range(SIDE)) + list(range(RW - SIDE_R, RW)):
        bottom = side_bottom(x)
        left = x < SIDE
        base = '#c993ab' if left else '#d8a2b9'
        c.vline(x, 0, bottom, base)
        c.vline(x, bottom - 4, 4, '#e6d6ee')
        c.px(x, bottom - 5, O)
        c.px(x, 46 + (bottom - WALL_Y), RAMP['mauve'][1])
    # corner lines
    c.vline(SIDE, 0, WALL_Y, O); c.vline(RW - SIDE_R - 1, 0, WALL_Y, O)


def floor(c):
    c.rect(0, WALL_Y, RW, RH - WALL_Y, RAMP['oak'][2])
    y, i = WALL_Y, 0
    while y < RH:
        h = 6 + (y - WALL_Y) // 28            # planks look a bit deeper near the viewer
        c.hline(0, y, RW, RAMP['oak'][0] if i == 0 else RAMP['oak'][1])
        c.hline(0, y + 1, RW, RAMP['oak'][3])
        off = (i * 29) % 46
        for x in range(off, RW, 46):
            c.vline(x, y + 1, h - 1, RAMP['oak'][1]); c.vline(x + 1, y + 1, h - 1, RAMP['oak'][3])
        r = random.Random(i)
        for _ in range(9):
            gx = r.randrange(0, RW); gy = y + r.randrange(2, max(3, h))
            c.hline(gx, gy, r.randrange(2, 6), RAMP['oak'][1])
        y += h; i += 1
    # contact shadow along the wall
    c.dither(0, WALL_Y + 1, RW, 2, RAMP['oak'][1], RAMP['oak'][2])


WIN = {'x': 120, 'y': 9, 'w': 62, 'h': 40}


def window(c, night=False):
    x, y, w, h = WIN['x'], WIN['y'], WIN['w'], WIN['h']
    c.box(x, y, w, h, 'cream')
    sx, sy, sw, sh = x + 4, y + 4, w - 8, h - 8
    if night:
        bands = ['#1b2150', '#232b63', '#2d3874', '#3a4785']
    else:
        bands = ['#6ab8e6', '#7fc6ee', '#96d4f3', '#b2e2f7']
    for k, col in enumerate(bands):
        c.rect(sx, sy + k * 5, sw, sh - k * 5, col)
        if k:
            c.dither(sx, sy + k * 5, sw, 1, bands[k - 1], col)
    if night:
        c.ellipse(sx + 41, sy + 8, 5, 5, '#fff2c2', '#f3d98a')
        c.ellipse(sx + 44, sy + 6, 4, 4, bands[0])
        for px_, py_ in ((sx + 5, sy + 4), (sx + 16, sy + 10), (sx + 27, sy + 3), (sx + 33, sy + 15), (sx + 10, sy + 17), (sx + 50, sy + 20)):
            c.px(px_, py_, '#ffffff')
            if (px_ + py_) % 2 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c.px(px_ + dx, py_ + dy, '#9fb0ff')
        hill1, hill2, tree = '#2f5b5a', '#244848', '#1a3a3a'
    else:
        c.ellipse(sx + 42, sy + 8, 4, 4, '#ffe58a', '#ffcf4d')
        for cx, cy in ((sx + 12, sy + 7), (sx + 32, sy + 13)):
            c.ellipse(cx, cy, 5, 2, '#ffffff'); c.ellipse(cx - 3, cy + 1, 3, 2, '#ffffff'); c.ellipse(cx + 4, cy + 1, 3, 2, '#ffffff')
        hill1, hill2, tree = '#8fd07a', '#5fae5c', '#3f8a45'
    import math
    for xx in range(sx, sx + sw):
        t = xx - sx
        top1 = sy + 20 + int(3 * math.sin(t / 8.0))
        top2 = sy + 26 + int(2 * math.sin(t / 5.0 + 2))
        c.vline(xx, top1, sy + sh - top1, hill1)
        c.vline(xx, top2, sy + sh - top2, hill2)
    for tx in (sx + 6, sx + 18, sx + 40):
        c.rect(tx, sy + 20, 3, 4, tree); c.rect(tx - 1, sy + 22, 5, 2, tree)
    # frame bars
    c.rect(x + w // 2 - 1, y + 2, 3, h - 4, RAMP['cream'][2]); c.vline(x + w // 2 + 1, y + 4, h - 8, RAMP['cream'][1])
    c.rect(x + 2, y + h // 2 - 1, w - 4, 3, RAMP['cream'][2]); c.hline(x + 4, y + h // 2 + 1, w - 8, RAMP['cream'][1])
    c.frame(sx - 1, sy - 1, sw + 2, sh + 2, RAMP['cream'][0])


def window_extras(c):
    x, y, w, h = WIN['x'], WIN['y'], WIN['w'], WIN['h']
    c.box(x - 5, y + h - 1, w + 10, 5, 'cream')            # sill
    c.rect(x - 14, y - 4, w + 28, 3, RAMP['yellow'][1]); c.hline(x - 14, y - 4, w + 28, RAMP['yellow'][3])
    c.frame(x - 15, y - 5, w + 30, 5, O)
    for side in (0, 1):
        cx0 = x - 12 if side == 0 else x + w - 2
        for yy in range(y - 1, y + h + 8):
            t = yy - y
            width = 14 if t < 18 else (8 if t < 24 else min(13, 9 + (t - 24) // 3))
            xs = cx0 if side == 0 else cx0 + 14 - width
            for k in range(width):
                fold = (k + side) % 4
                col = RAMP['purple'][3] if fold == 1 else RAMP['purple'][1] if fold == 3 else RAMP['purple'][2]
                c.px(xs + k, yy, col)
            c.px(xs, yy, O); c.px(xs + width - 1, yy, O)
        c.hline(cx0 if side == 0 else cx0 + 14 - 13, y + h + 8, 13, O)
        tx = cx0 + 1 if side == 0 else cx0 + 4
        c.rect(tx, y + 20, 9, 3, RAMP['yellow'][2]); c.frame(tx - 1, y + 19, 11, 5, O)


def door(c):
    """Door on the right-hand wall, drawn in perspective (it slants like the wall)."""
    x0, x1 = RW - SIDE_R + 8, RW - SIDE_R + 30
    for x in range(x0 - 2, x1 + 3):
        bottom = side_bottom(x) - 4
        top = bottom - 52 - int((x - x0) * 1.55)
        frame = x < x0 or x > x1
        for y in range(top - (2 if frame else 0), bottom):
            if frame:
                col = '#fbf2ff' if x in (x0 - 2, x1 + 2) else '#e6d6ee'
            else:
                t = x - x0
                col = RAMP['oak'][2] if 3 < t < 19 else RAMP['oak'][1]
                rel = (y - top) / max(1, bottom - top)
                if t in (5, 17) and (0.08 < rel < 0.45 or 0.52 < rel < 0.92):
                    col = RAMP['oak'][1]
                if t in (6,) and (0.08 < rel < 0.45 or 0.52 < rel < 0.92):
                    col = RAMP['oak'][3]
            c.px(x, y, col)
        c.px(x, top - (3 if frame else 1), O)
        c.px(x, bottom, O)
    for xx in (x0 - 3, x1 + 3):
        b = side_bottom(xx) - 4
        for y in range(b - 54 - int((xx - x0) * 1.55), b):
            c.px(xx, y, O)
    kx = x0 + 3
    ky = side_bottom(kx) - 30
    c.ellipse(kx, ky, 1, 1, '#f7c948', O)


BED = {'x': 22, 'y': 50, 'w': 120, 'h': 68}
BLANKET = {'x': 58, 'y': 74, 'w': 76, 'h': 37, 'top': 22, 'fold': 'left'}


def bed(c):
    """The bed sits sideways along the back wall, pillow end on the left."""
    # headboard (left end)
    c.box(24, 52, 12, 64, 'oak')
    c.rect(23, 50, 14, 4, RAMP['oak'][3]); c.frame(22, 49, 16, 5, O)
    c.frame(27, 60, 6, 44, RAMP['oak'][1]); c.vline(28, 61, 42, RAMP['oak'][3])
    # mattress top
    c.rect(36, 74, 98, 22, RAMP['sheet'][2]); c.frame(35, 73, 100, 24, O)
    c.hline(36, 74, 98, RAMP['sheet'][3])
    # front of the mattress + frame
    c.rect(36, 96, 98, 10, RAMP['sheet'][1]); c.frame(35, 96, 100, 11, O)
    c.box(35, 106, 102, 9, 'oak')
    # footboard (right end, lower)
    c.box(133, 80, 8, 36, 'oak')
    c.rect(132, 78, 10, 3, RAMP['oak'][3]); c.frame(131, 77, 12, 4, O)
    # legs
    c.rect(37, 115, 5, 4, RAMP['oak'][0]); c.rect(128, 115, 5, 4, RAMP['oak'][0])
    # pillow at the head end
    c.ellipse(47, 83, 10, 7, '#ffffff', O)
    c.hline(40, 87, 14, '#e9def3'); c.px(42, 79, '#ffffff'); c.px(41, 80, '#ffffff')
    c.hline(43, 85, 6, '#e9def3')


DESK = {'x': 196, 'y': 48, 'w': 74}
LAMP = {'x': 250, 'y': 26, 'w': 16, 'h': 26}
COMPUTER = {'x': 208, 'y': 22, 'w': 34, 'h': 30}


def desk(c):
    x, w = DESK['x'], DESK['w']
    # legs (behind)
    c.rect(x + 3, 70, 4, 26, RAMP['oak'][0]); c.rect(x + w - 7, 70, 4, 26, RAMP['oak'][0])
    # top surface + front edge
    c.rect(x, 50, w, 16, RAMP['oak'][3]); c.frame(x, 49, w, 17, O)
    c.hline(x + 1, 50, w - 2, '#f0bf8a')
    c.box(x, 65, w, 7, 'oak')
    # drawer unit
    c.box(x + w - 26, 71, 22, 22, 'oak')
    for k in range(2):
        c.frame(x + w - 24, 73 + k * 10, 18, 8, RAMP['oak'][1])
        c.rect(x + w - 17, 76 + k * 10, 4, 2, RAMP['yellow'][2])
    # shadow on the floor
    c.dither(x + 2, 96, w - 4, 2, RAMP['oak'][1], RAMP['oak'][2])


def computer(c):
    x, y = COMPUTER['x'], COMPUTER['y']
    c.box(x, y, 34, 24, 'beige')
    c.rect(x + 3, y + 3, 28, 17, '#2b3555')
    c.dither(x + 3, y + 3, 28, 17, '#2b3555', '#2f3a5c')
    c.rect(x + 3, y + 3, 28, 3, '#6b5bb5')
    for k, col in enumerate(('#7fe0c0', '#f7c948', '#ef8db0')):
        c.rect(x + 5, y + 8 + k * 4, 2, 2, col); c.hline(x + 9, y + 8 + k * 4, 10 - k * 2, '#c9d4f0')
    c.sprite(x + 22, y + 9, ['.r.r.', 'rrrrr', '.rrr.', '..r..'], {'r': '#ef6b8a'})
    c.rect(x + 13, y + 24, 8, 3, RAMP['beige'][1]); c.box(x + 9, y + 26, 16, 3, 'beige', light=False)
    c.box(x + 4, 56, 26, 4, 'beige', light=False)      # keyboard on the desk top
    for k in range(5):
        c.hline(x + 7 + k * 4, 57, 2, RAMP['beige'][3])
    c.px(x + 30, y + 21, '#7fe0c0')


def desk_lamp(c):
    x, y = LAMP['x'], LAMP['y']
    c.rect(x + 7, y + 10, 2, 14, RAMP['plum'][2]); c.vline(x + 6, y + 10, 14, O); c.vline(x + 9, y + 10, 14, O)
    c.box(x + 2, y + 22, 12, 4, 'plum')
    rows = ['...OOOOOOOO...', '..OyyyyyyyyO..', '.OyYyyyyyyyyO.', 'OyYyyyyyyyyydO', 'OOOOOOOOOOOOOO']
    c.sprite(x + 1, y + 5, rows, {'O': O, 'y': RAMP['yellow'][2], 'Y': RAMP['yellow'][3], 'd': RAMP['yellow'][1]})
    c.rect(x + 6, y + 10, 4, 1, '#fff6c2')


def chair(c):
    x, y = 220, 76
    c.rect(x + 3, y + 24, 3, 10, RAMP['plum'][1]); c.rect(x + 18, y + 24, 3, 10, RAMP['plum'][1])
    c.rect(x + 10, y + 26, 4, 8, RAMP['plum'][2])
    c.box(x + 1, y + 20, 22, 6, 'chair')                # seat
    c.box(x + 3, y, 18, 22, 'chair')                    # back rest (facing us)
    c.ellipse(x + 7, y + 3, 3, 3, RAMP['chair'][2], O); c.ellipse(x + 17, y + 3, 3, 3, RAMP['chair'][2], O)  # cat ears!
    c.box(x + 3, y + 4, 18, 18, 'chair')
    c.hline(x + 6, y + 12, 12, RAMP['chair'][1])


def paint(night=False):
    c = Pix(RW, RH)
    walls(c)
    floor(c)
    side_walls(c)
    window(c, night)
    window_extras(c)
    door(c)
    desk(c)
    computer(c)
    desk_lamp(c)
    chair(c)
    bed(c)
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
    wx, wy, ww, wh = WIN['x'], WIN['y'], WIN['w'], WIN['h']
    overlay = Image.new('RGBA', (RW, RH), (0, 0, 0, 0))
    overlay.paste(night.img.crop((wx, wy, wx + ww, wy + wh)), (wx, wy))
    overlay.save(os.path.join(OUT, 'window-night.png'))
    build_decor()
    build_sheet(GARDEN_ORDER, 'garden_', 32, 32, 'garden.png')
    meta = {'size': [RW, RH], 'decor': DECOR_ORDER, 'garden': GARDEN_ORDER, 'blanket': BLANKET, 'lamp': LAMP,
            'bed': BED, 'computer': COMPUTER, 'window': WIN, 'wallY': WALL_Y,
            'lampGlow': {'x': LAMP['x'] + 8, 'y': LAMP['y'] + 12}}
    with open(os.path.join(OUT, 'room-meta.js'), 'w') as fh:
        fh.write('/* Generated by tools/build_room.py - do not edit by hand. */\n')
        fh.write('window.COZY_ROOM_META = ' + json.dumps(meta) + ';\n')
    print('room painted', RW, 'x', RH)


if __name__ == '__main__':
    main()
