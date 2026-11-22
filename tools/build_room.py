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

    def shadow(self, x, y, w, h, alpha=70):
        """Soft see-through shadow, so it looks right on every floor theme."""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if 0 <= xx < self.w and 0 <= yy < self.h and (xx + yy) % 2 == 0 or alpha > 90:
                    if 0 <= xx < self.w and 0 <= yy < self.h:
                        self.p[xx, yy] = (40, 16, 36, alpha)

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


# ------------------------------------------------------------------ themes
# Wallpapers and floors are painted on their own see-through layers so the
# game can swap them (shop themes). Everything else lives on the objects layer.
WALLPAPERS = {
    #          stripe A    stripe B    motif       panel ramp (dark, shade, base, light)                 side L     side R     motif kind
    'rose':   ('#e7b3c4', '#ebbccb', '#f4cfdb', ('#5e3a5a', '#9a6a92', '#b98aa8', '#d2a7c2'), '#c993ab', '#d8a2b9', 'dots'),
    'starry': ('#2f3a78', '#34407f', '#ffe58a', ('#161b3d', '#232a5a', '#2c3468', '#3d4782'), '#262f66', '#2b3570', 'stars'),
    'mint':   ('#bfe8d6', '#d3f1e3', '#8fd0b4', ('#2f5e55', '#4f8f80', '#6fae9c', '#93c9b8'), '#a5d6c1', '#b2dfcb', 'gingham'),
    'sunny':  ('#ffd66e', '#ffe08d', '#ff9f43', ('#7a3d1c', '#c0612b', '#e3803d', '#f4a35e'), '#efbf55', '#f6ca63', 'stripes'),
    'ocean':  ('#7cc3ea', '#8ccdef', '#e9f8ff', ('#1d3c66', '#2c5a92', '#3c74b4', '#5a92d0'), '#6aaedb', '#73b9e3', 'waves'),
    'forest': ('#9ccc7a', '#a8d486', '#5f9e4a', ('#4a2a1d', '#6e4029', '#8f5a3a', '#ad7550'), '#86b866', '#90c270', 'leaves'),
}
WALL_ORDER = list(WALLPAPERS)

FLOORS = {
    #           (dark, shade, base, light)                        kind
    'oak':     (('#5e3823', '#94613d', '#c08552', '#dca06c'), 'planks'),
    'birch':   (('#8a6a45', '#c9a77a', '#e8cfa4', '#f7e6c4'), 'planks'),
    'cherry':  (('#3a1a1a', '#6a2e2a', '#8e4436', '#ad5c48'), 'planks'),
    'checker': (('#3f6a5c', '#9fd6c0', '#fff6e8', '#ffffff'), 'checker'),
    'carpet':  (('#1f4f57', '#2f7480', '#3f929c', '#5fb3b8'), 'carpet'),
    'cloud':   (('#5b4a86', '#9483c9', '#b9a8ea', '#d6c9fb'), 'carpet'),
}
FLOOR_ORDER = list(FLOORS)


def side_bottom_f(x):
    if x < SIDE:
        return WALL_Y + (SIDE - x) * 1.6
    return WALL_Y + (x - (RW - SIDE_R - 1)) * 1.25


def wall_y(x, frac):
    """y on a side wall at `frac` of the wall height above the floor.
    Lines on the side walls fan out towards the viewer (true perspective)."""
    return int(round(side_bottom_f(x) * (1 - frac)))


def wall_line(c, xs, frac, col, thick=1):
    """A gap-free line across a side wall at a given height."""
    for x in xs:
        a, b = wall_y(x, frac), wall_y(x + 1, frac)
        lo, hi = min(a, b), max(a, b)
        for y in range(lo, max(lo + thick, hi)):
            c.px(x, y, col)


def walls(c, theme='rose'):
    a, b, motif, panel, _, _, kind = WALLPAPERS[theme]
    for x in range(RW):
        col = a if (x // 6) % 2 == 0 else b
        if kind == 'gingham':
            col = a
        c.vline(x, 0, WALL_Y, col)
    if kind == 'dots':
        for y in range(8, 44, 12):
            for x in range((y // 12) % 2 * 6 + 3, RW, 12):
                c.px(x, y, motif)
    elif kind == 'stars':
        r = random.Random(3)
        for _ in range(70):
            x, y = r.randrange(RW), r.randrange(5, 41)
            c.px(x, y, motif if r.random() < .5 else '#c9d4ff')
        for x, y in ((30, 14), (95, 30), (215, 12), (300, 28), (160, 6)):
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px(x + dx, y + dy, motif)
    elif kind == 'gingham':
        for x in range(RW):
            for y in range(4, 43):
                bx, by = (x // 5) % 2, (y // 5) % 2
                if bx and by:
                    c.px(x, y, motif)
                elif bx or by:
                    c.px(x, y, b)
    elif kind == 'stripes':
        for x in range(0, RW, 12):
            c.vline(x, 4, 39, motif); c.vline(x + 1, 4, 39, motif)
    elif kind == 'waves':
        import math
        for row in range(10, 42, 9):
            for x in range(RW):
                c.px(x, row + int(round(1.5 * math.sin(x / 3.0))), motif)
    elif kind == 'leaves':
        for y in range(9, 42, 11):
            for x in range((y // 11) % 2 * 9 + 4, RW, 18):
                c.sprite(x, y, ['.gg', 'ggg', 'gg.', '.d.'], {'g': motif, 'd': panel[0]})
    # lower panelling
    c.rect(0, 46, RW, WALL_Y - 46, panel[2])
    c.hline(0, 44, RW, panel[3]); c.hline(0, 45, RW, panel[1]); c.hline(0, 43, RW, O)
    for x in range(10, RW, 26):
        c.frame(x, 49, 18, 17, panel[1]); c.hline(x + 1, 50, 16, panel[3]); c.vline(x + 1, 50, 15, panel[3])
    # skirting
    c.rect(0, WALL_Y - 4, RW, 4, '#fbf2ff'); c.hline(0, WALL_Y - 4, RW, O); c.hline(0, WALL_Y - 1, RW, '#cdb8d8')
    # ceiling trim
    c.rect(0, 0, RW, 3, panel[1]); c.hline(0, 3, RW, O)


def side_walls(c, theme='rose'):
    _, _, _, panel, left_col, right_col, _ = WALLPAPERS[theme]
    left, right = range(SIDE), range(RW - SIDE_R, RW)
    for x in list(left) + list(right):
        c.vline(x, 0, side_bottom(x), left_col if x < SIDE else right_col)
        # lower panelling, in perspective
        top = wall_y(x, (WALL_Y - 44) / WALL_Y)
        c.vline(x, top, side_bottom(x) - top, panel[2] if x >= SIDE else panel[1])
    for xs in (left, right):
        wall_line(c, xs, (WALL_Y - 43) / WALL_Y, O)
        wall_line(c, xs, (WALL_Y - 44.5) / WALL_Y, panel[3])
        # skirting board
        for x in xs:
            t, bt = wall_y(x, 4.5 / WALL_Y), side_bottom(x)
            c.vline(x, t, bt - t, '#e6d6ee')
        wall_line(c, xs, 4.5 / WALL_Y, O)
        # the line where the side wall meets the floor
        for x in xs:
            a, b = side_bottom(x), side_bottom(x + 1 if x >= SIDE else x - 1)
            for y in range(min(a, b) - 1, max(a, b)):
                c.px(x, y, '#cdb8d8')
    c.px(0, 3, O)
    wall_line(c, left, 1 - 3.5 / WALL_Y, O)
    wall_line(c, right, 1 - 3.5 / WALL_Y, O)
    # corner lines
    c.vline(SIDE, 0, WALL_Y, O); c.vline(RW - SIDE_R - 1, 0, WALL_Y, O)


def floor(c, theme='oak'):
    ramp, kind = FLOORS[theme]
    d, s, b, l = ramp
    c.rect(0, WALL_Y, RW, RH - WALL_Y, b)
    if kind == 'planks':
        y, i = WALL_Y, 0
        while y < RH:
            h = 6 + (y - WALL_Y) // 28            # planks look a bit deeper near the viewer
            c.hline(0, y, RW, d if i == 0 else s)
            c.hline(0, y + 1, RW, l)
            off = (i * 29) % 46
            for x in range(off, RW, 46):
                c.vline(x, y + 1, h - 1, s); c.vline(x + 1, y + 1, h - 1, l)
            r = random.Random(i)
            for _ in range(9):
                gx = r.randrange(0, RW); gy = y + r.randrange(2, max(3, h))
                c.hline(gx, gy, r.randrange(2, 6), s)
            y += h; i += 1
    elif kind == 'checker':
        y, i = WALL_Y, 0
        while y < RH:
            h = 9 + (y - WALL_Y) // 14
            w = 18 + (y - WALL_Y) // 8
            for x in range(-(i % 2) * w, RW, w * 2):
                c.rect(x, y, w, h, s)
            c.hline(0, y, RW, d)
            y += h; i += 1
    else:   # soft carpet
        r = random.Random(11)
        for y in range(WALL_Y, RH):
            for x in range(RW):
                v = r.random()
                if v < .08:
                    c.px(x, y, s)
                elif v > .94:
                    c.px(x, y, l)
    # contact shadow along the wall
    c.dither(0, WALL_Y + 1, RW, 2, s, b)



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
    """Door on the right-hand wall. It follows the wall's perspective: its
    bottom runs along the floor line and its top fans out a little, so the
    side nearer to us is taller."""
    x0, x1 = RW - SIDE_R + 9, RW - SIDE_R + 31
    TOP, FRAME = .74, .79
    d, s, b, l = RAMP['oak']
    for x in range(x0 - 3, x1 + 4):
        bot = side_bottom(x) - 1
        if x0 <= x <= x1:
            top = wall_y(x, TOP)
            c.vline(x, top, bot - top, b if 2 < x - x0 < x1 - x0 - 1 else s)
            for y in range(wall_y(x, FRAME), top):
                c.px(x, y, '#fbf2ff')
        else:
            for y in range(wall_y(x, FRAME), bot):
                c.px(x, y, '#fbf2ff' if x in (x0 - 3, x1 + 3) else '#e6d6ee')
    # outlines (gap-free)
    wall_line(c, range(x0 - 3, x1 + 4), FRAME + .01, O)
    wall_line(c, range(x0, x1 + 1), TOP, O)
    for x in (x0 - 4, x1 + 4):
        c.vline(x, wall_y(x, FRAME + .01), side_bottom(x) - wall_y(x, FRAME + .01), O)
    for x in (x0 - 1, x1 + 1):
        c.vline(x, wall_y(x, TOP), side_bottom(x) - wall_y(x, TOP), O)
    # two recessed panels
    px0, px1 = x0 + 4, x1 - 4
    for lo, hi in ((.40, .66), (.09, .33)):
        for x in range(px0, px1 + 1):
            for y in range(wall_y(x, hi), wall_y(x, lo)):
                c.px(x, y, s)
            c.px(x, wall_y(x, lo), l)
        wall_line(c, range(px0, px1 + 1), hi, d)
        c.vline(px0, wall_y(px0, hi), wall_y(px0, lo) - wall_y(px0, hi), d)
        c.vline(px1, wall_y(px1, hi), wall_y(px1, lo) - wall_y(px1, hi) + 1, l)
    # brass knob on the far side
    kx = x0 + 2
    ky = wall_y(kx, .37)
    c.rect(kx, ky, 2, 2, '#f7c948'); c.px(kx, ky, '#fff1a8'); c.px(kx + 1, ky + 1, '#a8701f')


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
    c.shadow(x + 2, 96, w - 4, 3, 80)


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


def paint(night=False, wall='rose', flr='oak', layer='all'):
    """layer: 'all' (full picture), 'floor', 'walls' or 'objects'."""
    c = Pix(RW, RH)
    if layer in ('all', 'floor'):
        floor(c, flr)
    if layer in ('all', 'walls'):
        walls(c, wall)
        side_walls(c, wall)
    if layer in ('all', 'objects'):
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
DECOR_ORDER = ['lights', 'plush', 'books', 'flower', 'moon', 'plant', 'catbed', 'rug', 'poster', 'beanbag', 'fishtank', 'guitar',
               'dresser', 'shelf', 'clock', 'monstera', 'cushion', 'record', 'lava', 'arcade']


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



def decor_dresser(c):
    c.box(4, 4, 24, 18, 'oak')
    c.rect(3, 3, 26, 3, RAMP['oak'][3]); c.frame(3, 3, 26, 3, O)
    for k in range(3):
        y = 7 + k * 5
        c.frame(6, y, 20, 4, RAMP['oak'][1]); c.hline(7, y + 1, 18, RAMP['oak'][3])
        c.rect(15, y + 1, 2, 2, RAMP['yellow'][2]); c.px(15, y + 1, RAMP['yellow'][3])
    c.rect(5, 22, 3, 2, RAMP['oak'][0]); c.rect(24, 22, 3, 2, RAMP['oak'][0])
    # tiny frame on top
    c.rect(19, 0, 6, 3, RAMP['blue'][2]); c.frame(19, 0, 6, 4, O)


def decor_shelf(c):
    c.box(2, 15, 28, 4, 'oak')
    c.rect(5, 19, 2, 4, RAMP['oak'][0]); c.rect(25, 19, 2, 4, RAMP['oak'][0])
    # trophy
    c.sprite(5, 5, ['OOOOOOO', 'OyYyyyO', '.OyyyO.', '..OyO..', '...O...', '..OOO..', '.OyyyO.', '.OOOOO.', '.......', '.......'],
             {'O': O, 'y': RAMP['yellow'][2], 'Y': RAMP['yellow'][3]})
    # mini cactus
    c.box(15, 7, 5, 6, 'leaf'); c.box(13, 9, 3, 3, 'leaf'); c.box(14, 12, 7, 3, 'pot')
    c.px(17, 6, '#ef8db0')
    # little books
    for i, col in enumerate(('#e2554e', '#4f8fd0', '#9a6bc9')):
        c.rect(23 + i * 2, 8 + (i % 2), 2, 7 - (i % 2), col); c.vline(23 + i * 2, 8 + (i % 2), 7 - (i % 2), O)
    c.vline(29, 8, 7, O); c.hline(23, 7, 7, O)


def decor_clock(c):
    c.ellipse(16, 12, 10, 10, RAMP['teal'][2], O)
    c.ellipse(16, 12, 8, 8, '#fff4e4', RAMP['teal'][1])
    for dx, dy in ((0, -6), (6, 0), (0, 6), (-6, 0)):
        c.px(16 + dx, 12 + dy, O)
    c.vline(16, 7, 6, O); c.hline(16, 12, 4, '#e2554e'); c.px(16, 12, O)
    c.px(11, 7, '#ffffff'); c.px(12, 6, '#ffffff')
    c.rect(9, 1, 4, 3, RAMP['yellow'][2]); c.frame(9, 1, 4, 3, O)
    c.rect(20, 1, 4, 3, RAMP['yellow'][2]); c.frame(20, 1, 4, 3, O)


def decor_monstera(c):
    for cx, cy, rx, ry in ((10, 7, 6, 4), (22, 6, 6, 4), (16, 3, 5, 3), (8, 12, 5, 3), (24, 12, 5, 3)):
        c.ellipse(cx, cy, rx, ry, RAMP['leaf'][2], O)
        c.hline(cx - rx + 2, cy, rx * 2 - 3, RAMP['leaf'][1])
        c.px(cx - 2, cy - 1, RAMP['leaf'][3]); c.px(cx + 1, cy - 2, RAMP['leaf'][3])
    for x in (14, 16, 18):
        c.vline(x, 9, 8, RAMP['leaf'][1])
    c.box(9, 16, 14, 8, 'teal')
    c.rect(8, 16, 16, 2, RAMP['teal'][3]); c.frame(8, 16, 16, 2, O)


def decor_cushion(c):
    c.ellipse(16, 16, 13, 6, RAMP['teal'][2], O)
    c.ellipse(16, 14, 11, 4, RAMP['teal'][3])
    c.ellipse(16, 16, 2, 1, RAMP['teal'][1], O)
    for x in (4, 28):
        c.px(x, 12, O); c.px(x, 13, RAMP['teal'][1])
    c.hline(6, 20, 20, RAMP['teal'][1])
    c.px(9, 12, '#ffffff'); c.px(10, 12, '#ffffff')


def decor_record(c):
    c.box(2, 10, 28, 12, 'dwood')
    c.rect(4, 11, 24, 8, RAMP['dwood'][3])
    c.ellipse(13, 15, 7, 4, '#2a2230', O)
    c.ellipse(13, 15, 2, 1, '#ef5b6b')
    c.hline(9, 14, 3, '#4e4558'); c.hline(14, 17, 4, '#4e4558')
    c.vline(25, 11, 4, '#c4baa6'); c.hline(21, 15, 5, '#c4baa6'); c.px(25, 11, O)
    c.rect(24, 18, 3, 2, RAMP['yellow'][2])
    # music notes floating
    c.sprite(4, 1, ['.OO', '.OO', '.O.', 'OO.', 'OO.'], {'O': RAMP['purple'][2]})
    c.sprite(24, 0, ['.OOO', '.O.O', 'OO.O', 'OOOO', '...O'], {'O': '#ef8db0'})


def decor_lava(c):
    c.box(11, 16, 10, 6, 'purple')
    c.sprite(10, 2, ['...OOOOOO...', '..OaaaaaaO..', '..OaaaaaaO..', '.OaaaaaaaaO.', '.OaaaaaaaaO.', '.OaaaaaaaaO.',
                     '.OaaaaaaaaO.', 'OaaaaaaaaaaO', 'OaaaaaaaaaaO', 'OaaaaaaaaaaO', 'OaaaaaaaaaaO', 'OaaaaaaaaaaO',
                     'OaaaaaaaaaaO', '.OaaaaaaaaO.', '..OOOOOOOO..'], {'O': O, 'a': '#ffb36b'})
    for cx, cy, r in ((15, 6, 1), (17, 10, 2), (14, 13, 1), (16, 15, 1)):
        c.ellipse(cx, cy, r, r, '#ef4b7a')
    c.vline(12, 6, 8, '#ffe0b8')
    c.box(12, 0, 8, 3, 'purple')


def decor_arcade(c):
    c.box(8, 1, 16, 23, 'blue')
    c.rect(10, 4, 12, 8, '#1b2150'); c.frame(9, 3, 14, 10, O)
    c.sprite(12, 6, ['.y.r', 'yyy.', '.y..'], {'y': '#f7c948', 'r': '#ef5b6b'})
    c.px(19, 9, '#7fe0c0'); c.px(20, 9, '#7fe0c0')
    c.rect(9, 13, 14, 4, RAMP['blue'][3]); c.frame(8, 13, 16, 4, O)
    c.px(12, 14, '#ef5b6b'); c.px(12, 15, O); c.px(17, 15, '#f7c948'); c.px(19, 15, '#7fe0c0')
    c.rect(10, 1, 12, 2, '#ef8db0'); c.hline(11, 1, 10, '#ffd0e4')


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
    # theme sheets: one 320x180 band per theme, stacked top to bottom
    for name, order, key in (('room-floors.png', FLOOR_ORDER, 'floor'), ('room-walls.png', WALL_ORDER, 'walls')):
        sheet = Image.new('RGBA', (RW, RH * len(order)), (0, 0, 0, 0))
        for i, t in enumerate(order):
            kw = {'flr': t} if key == 'floor' else {'wall': t}
            sheet.paste(paint(layer=key, **kw).img, (0, i * RH))
        sheet.save(os.path.join(OUT, name))
    paint(layer='objects').img.save(os.path.join(OUT, 'room-objects.png'))
    paint().img.save(os.path.join(OUT, 'room-day.png'))      # preview of the default look
    night = paint(True)
    wx, wy, ww, wh = WIN['x'], WIN['y'], WIN['w'], WIN['h']
    overlay = Image.new('RGBA', (RW, RH), (0, 0, 0, 0))
    overlay.paste(night.img.crop((wx, wy, wx + ww, wy + wh)), (wx, wy))
    overlay.save(os.path.join(OUT, 'window-night.png'))
    build_decor()
    build_sheet(GARDEN_ORDER, 'garden_', 32, 32, 'garden.png')
    meta = {'size': [RW, RH], 'decor': DECOR_ORDER, 'garden': GARDEN_ORDER, 'blanket': BLANKET, 'lamp': LAMP,
            'bed': BED, 'computer': COMPUTER, 'walls': WALL_ORDER, 'floors': FLOOR_ORDER, 'window': WIN, 'wallY': WALL_Y,
            'lampGlow': {'x': LAMP['x'] + 8, 'y': LAMP['y'] + 12}}
    with open(os.path.join(OUT, 'room-meta.js'), 'w') as fh:
        fh.write('/* Generated by tools/build_room.py - do not edit by hand. */\n')
        fh.write('window.COZY_ROOM_META = ' + json.dumps(meta) + ';\n')
    print('room painted', RW, 'x', RH)


if __name__ == '__main__':
    main()
