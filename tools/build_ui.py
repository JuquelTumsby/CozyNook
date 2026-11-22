#!/usr/bin/env python3
"""
CozyNook UI art builder
=======================
Draws the pixel-art interface pieces: icons, panel/button frames and the
starry page background.

Run it from the project folder:   python3 tools/build_ui.py

Outputs (assets/ui/):
  icons.png        16x16 icons in a row (order in ICON_ORDER / ui-meta below)
  panel.png        frame for big panels   (CSS border-image, slice 12)
  card.png         frame for small cards  (slice 9)
  btn-*.png        button frames          (slice 9)
  bg-stars.png     tiling page background
Frames are saved already scaled x3 so browsers keep the pixels crisp.
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_room import Pix, RAMP, hexc   # reuse the room painter's pixel helpers

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'ui')
O = '#2e2240'
RAMP.update({
    'pink':  ('#8a3a62', '#d9739f', '#f7a8c8', '#ffd3e5'),
    'lav':   ('#3c2f6e', '#8f78cf', '#b9a3e6', '#ddd0f7'),
    'skin':  ('#9b5a42', '#d9977a', '#efbd9d', '#f9d8c0'),
    'red':   ('#7c2a33', '#c9404f', '#ef5b6b', '#ff98a2'),
})

PAL = {'O': O, 'y': '#f7c948', 'Y': '#fff0a8', 'd': '#d39b2c', 'r': '#ef6b8a', 'R': '#c24d70', 'w': '#ffffff',
       'p': '#f7a8c8', 'P': '#d9739f', 'g': '#6cbf6a', 'G': '#3f8a45', 'b': '#79a5e0', 'k': '#6b4434'}


def ascii_icon(c, rows):
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                c.px(x, y, PAL[ch])


ICONS = {}


def icon(fn):
    ICONS[fn.__name__[2:]] = fn
    return fn


@icon
def i_home(c):
    ascii_icon(c, ['................', '.......OO.......', '......OrrO......', '.....OrrrrO.....', '....OrrrrrrO....',
                   '...OrrrrrrrrO...', '..OrrrrrrrrrrO..', '.OOOOOOOOOOOOOO.', '..OwwwwwwwwwwO..', '..OwOOOwOOOwwO..',
                   '..OwObOwOkOwwO..', '..OwOOOwOkOwwO..', '..OwwwwwOkOwwO..', '..OOOOOOOOOOOO..', '.gggggggggggggg.'])
    c.px(6, 4, '#ffb3c8'); c.px(5, 5, '#ffb3c8'); c.px(10, 10, '#f7c948')


@icon
def i_planner(c):
    c.box(2, 2, 12, 13, 'cream')
    c.rect(5, 1, 6, 3, RAMP['lav'][2]); c.frame(5, 1, 6, 3, O)
    for k, col in enumerate(('#ef6b8a', '#6cbf6a', '#79a5e0')):
        y = 6 + k * 3
        c.rect(4, y, 2, 2, col); c.hline(7, y, 5, '#b9a3e6'); c.hline(7, y + 1, 3, '#ddd0f7')


@icon
def i_focus(c):
    c.ellipse(3, 3, 2, 2, RAMP['pink'][2], O); c.ellipse(12, 3, 2, 2, RAMP['pink'][2], O)
    c.ellipse(8, 9, 6, 6, '#ffffff', O)
    c.ellipse(8, 9, 4, 4, '#f4eefc')
    c.vline(8, 5, 5, O); c.hline(8, 9, 3, O); c.px(8, 9, '#ef6b8a')
    c.px(4, 15, O); c.px(12, 15, O)


@icon
def i_garden(c):
    c.ellipse(5, 6, 3, 2, RAMP['leaf'][2], O); c.ellipse(11, 4, 3, 2, RAMP['leaf'][2], O)
    c.px(4, 5, RAMP['leaf'][3]); c.px(10, 3, RAMP['leaf'][3])
    c.vline(8, 5, 5, RAMP['leaf'][1])
    c.box(3, 9, 10, 6, 'pot'); c.rect(2, 9, 12, 2, RAMP['pot'][2]); c.frame(2, 9, 12, 2, O)


@icon
def i_character(c):
    c.ellipse(8, 7, 6, 6, '#7a4a3a', O)
    c.ellipse(8, 9, 5, 4, RAMP['skin'][2])
    c.rect(3, 4, 10, 3, '#7a4a3a'); c.px(4, 7, '#7a4a3a'); c.px(12, 7, '#7a4a3a')
    c.px(6, 9, O); c.px(10, 9, O); c.px(5, 11, '#ef8f8f'); c.px(11, 11, '#ef8f8f'); c.hline(7, 11, 3, '#b2505e')
    c.px(5, 4, '#a8705a'); c.px(6, 3, '#a8705a')
    c.rect(12, 2, 2, 2, '#f7c948')


@icon
def i_shop(c):
    for x in range(1, 15):
        col = '#ef6b8a' if (x // 2) % 2 == 0 else '#ffffff'
        c.vline(x, 3, 4, col)
    c.frame(1, 2, 14, 5, O)
    for x in range(1, 15, 2):
        c.px(x, 7, O)
    c.box(2, 7, 12, 8, 'cream')
    c.rect(4, 9, 3, 6, '#79a5e0'); c.frame(3, 9, 5, 6, O)
    c.rect(9, 9, 4, 3, '#bde6f7'); c.frame(8, 9, 6, 4, O)


@icon
def i_reset(c):
    for cx, cy, rx, ry in ((8, 6, 2, 4), (4, 9, 3, 2), (12, 9, 3, 2), (6, 8, 2, 3), (10, 8, 2, 3)):
        c.ellipse(cx, cy, rx, ry, '#f7a8c8', O)
    c.ellipse(8, 7, 1, 3, '#ffd3e5')
    c.hline(2, 12, 12, RAMP['leaf'][2]); c.hline(3, 13, 10, RAMP['leaf'][1])
    c.px(1, 12, O); c.px(14, 12, O)


@icon
def i_coin(c):
    c.ellipse(8, 8, 6, 6, '#f7c948', O)
    c.ellipse(8, 8, 4, 4, '#ffd966', '#d39b2c')
    c.vline(8, 6, 5, '#d39b2c'); c.px(5, 4, '#fff0a8'); c.px(4, 5, '#fff0a8')


@icon
def i_star(c):
    ascii_icon(c, ['.......OO.......', '......OyyO......', '......OyyO......', '.....OyYyyO.....', 'OOOOOOyYyyOOOOOO',
                   'OyyyyyYyyyyyyydO', '.OyyyyyyyyyyydO.', '..OyyyyyyyyydO..', '...OyyyyyyyydO..'[:16],
                   '...OyyyyyyyyO...', '..OyyyyOOyyyyO..', '..OyyyOO.OOyydO.', '.OyyyO.....OyydO', '.OyyO.......OydO',
                   '.OOO.........OOO'])


@icon
def i_heart(c):
    ascii_icon(c, ['................', '..OOOO....OOOO..', '.OrrrrO..OrrrrO.', 'OrwwrrrOOrrrrrRO', 'OrwrrrrrrrrrrrRO',
                   'OrrrrrrrrrrrrrRO', '.OrrrrrrrrrrrRO.', '..OrrrrrrrrrRO..', '...OrrrrrrrRO...', '....OrrrrrRO....',
                   '.....OrrrRO.....', '......OrRO......', '.......OO.......'])


@icon
def i_moon(c):
    c.ellipse(8, 8, 6, 6, '#ffe28a', O)
    for y in range(16):
        for x in range(16):
            if ((x - 11) / 5.2) ** 2 + ((y - 5) / 5.2) ** 2 <= 1:
                c.p[x, y] = (0, 0, 0, 0)
    for y in range(1, 15):
        for x in range(1, 15):
            if c.p[x, y][3] and c.p[x, y][:3] != hexc(O)[:3]:
                if any(c.p[x + dx, y + dy][3] == 0 for dx, dy in ((1, 0), (0, 1), (0, -1), (-1, 0))):
                    c.p[x, y] = hexc(O)
    c.px(4, 8, '#fff6c2'); c.px(4, 9, '#fff6c2')
    c.px(13, 12, '#f7c948'); c.px(14, 2, '#f7c948')


@icon
def i_sun(c):
    for dx, dy in ((0, -7), (0, 7), (-7, 0), (7, 0), (5, 5), (-5, -5), (5, -5), (-5, 5)):
        c.px(8 + dx, 8 + dy, '#f7a33c'); c.px(8 + dx - (dx > 0) + (dx < 0), 8 + dy - (dy > 0) + (dy < 0), '#f7c948')
    c.ellipse(8, 8, 4, 4, '#ffd23f', O); c.px(6, 6, '#fff0a8'); c.px(7, 6, '#fff0a8')


@icon
def i_bulb(c):
    c.ellipse(8, 6, 5, 5, '#ffe28a', O)
    c.px(6, 4, '#ffffff'); c.px(6, 5, '#ffffff')
    c.box(5, 10, 6, 5, 'lav', light=False); c.hline(6, 12, 4, RAMP['lav'][1])
    c.px(8, 15, O)


@icon
def i_paw(c):
    c.ellipse(8, 11, 4, 3, '#f7a8c8', O)
    for x, y in ((3, 6), (6, 3), (10, 3), (13, 6)):
        c.ellipse(x, y, 1, 2, '#f7a8c8', O)
    c.px(7, 10, '#ffd3e5')


@icon
def i_bolt(c):
    ascii_icon(c, ['.........OOOO...', '........OyyyO...', '.......OyYyO....', '......OyYyO.....', '.....OyyyO......',
                   '....OyyyyOOOO...', '...OyyyyyyyyO...', '...OOOOyyyydO...', '......OyyydO....'[:16], '.....OyydO......',
                   '....OyydO.......', '...OydO.........', '...OyO..........', '...OO...........'])


@icon
def i_gift(c):
    c.box(2, 7, 12, 8, 'red')
    c.rect(1, 5, 14, 3, RAMP['red'][2]); c.frame(1, 5, 14, 3, O)
    c.rect(7, 5, 2, 10, '#f7c948'); c.vline(7, 5, 10, '#ffe28a')
    c.ellipse(5, 3, 2, 1, '#f7c948', O); c.ellipse(11, 3, 2, 1, '#f7c948', O)
    c.hline(1, 7, 14, O)


@icon
def i_cup(c):
    c.box(3, 6, 9, 8, 'cream')
    c.rect(4, 7, 7, 2, '#a8703f')
    c.frame(11, 8, 3, 4, O)
    c.hline(2, 14, 11, O)
    for x, y in ((5, 4), (6, 3), (5, 2), (9, 4), (8, 3), (9, 2)):
        c.px(x, y, '#ddd0f7')


@icon
def i_brush(c):
    for k in range(8):
        c.px(14 - k, 1 + k, O); c.px(13 - k, 1 + k, '#a8703f'); c.px(12 - k, 1 + k, O)
    c.ellipse(4, 12, 3, 3, '#79a5e0', O)
    c.px(3, 11, '#bde6f7')
    c.px(6, 9, '#d6d6d6'); c.px(7, 9, O)


@icon
def i_right(c):
    rows = ['....OO..........', '....OpO.........', '....OppO........', '....OpppO.......', '....OppppO......',
            '....OpppppO.....', '....OppppppO....', '....OppppppO....', '....OpppppPO....', '....OppppPO.....',
            '....OpppPO......', '....OppPO.......', '....OpPO........', '....OPO.........', '....OO..........']
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                c.px(x + 1, y, PAL[ch])


@icon
def i_left(c):
    tmp = Pix(16, 16)
    i_right(tmp)
    for y in range(16):
        for x in range(16):
            c.p[x, y] = tmp.p[15 - x, y]


@icon
def i_check(c):
    pts = [(2, 8), (3, 9), (4, 10), (5, 11), (6, 12), (7, 11), (8, 10), (9, 9), (10, 8), (11, 7), (12, 6), (13, 5), (14, 4)]
    for x, y in pts:
        c.rect(x - 1, y - 2, 3, 4, O)
    for x, y in pts:
        c.rect(x, y - 1, 1, 2, '#6cbf6a')
    c.px(13, 4, '#a8e07a')


@icon
def i_sparkle(c):
    ascii_icon(c, ['.......OO.......', '......OwwO......', '......OwwO......', '.....OwyywO.....', '.....OwyywO.....',
                   '.OOOOwyyyywOOOO.', 'OwwwyyyyyyyywwwO', 'OwwwyyyyyyyywwwO', '.OOOOwyyyywOOOO.', '.....OwyywO.....',
                   '.....OwyywO.....', '......OwwO......', '......OwwO......', '.......OO.......'])


@icon
def i_bed(c):
    c.box(1, 4, 3, 11, 'wood'); c.box(1, 9, 14, 4, 'wood')
    c.rect(4, 7, 11, 3, '#b9a3e6'); c.frame(4, 7, 11, 3, O)
    c.ellipse(6, 7, 2, 1, '#ffffff', O)
    c.px(2, 15, O); c.px(13, 13, O); c.px(13, 14, O)


@icon
def i_cat(c):
    c.ellipse(8, 9, 6, 5, '#f2a65a', O)
    c.sprite(2, 2, ['O....', 'OO...', 'OfO..', 'OffO.'], {'O': O, 'f': '#f2a65a'})
    c.sprite(10, 2, ['....O', '...OO', '..OfO', '.OffO'], {'O': O, 'f': '#f2a65a'})
    c.hline(4, 9, 2, O); c.hline(10, 9, 2, O); c.px(8, 10, '#ef6b8a'); c.px(4, 11, '#ef8f8f'); c.px(12, 11, '#ef8f8f')
    c.px(7, 5, '#b0612c'); c.px(9, 5, '#b0612c')


ICON_ORDER = list(ICONS.keys())


def build_icons():
    sheet = Image.new('RGBA', (16 * len(ICON_ORDER), 16), (0, 0, 0, 0))
    for i, name in enumerate(ICON_ORDER):
        c = Pix(16, 16)
        ICONS[name](c)
        sheet.paste(c.img, (i * 16, 0))
    sheet.save(os.path.join(OUT, 'icons.png'))


def frame(w, h, outline, band, band_dark, fill, band_w=2, highlight=None, shade=None):
    c = Pix(w, h)
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            corner = (x in (0, w - 1)) and (y in (0, h - 1))
            if corner:
                continue
            inner_corner = (x in (1, w - 2)) and (y in (1, h - 2))
            if d == 0 or inner_corner:
                col = outline
            elif d <= band_w:
                col = band_dark if (y >= h - 1 - band_w or x >= w - 1 - band_w) else band
            else:
                col = fill
            c.px(x, y, col)
    if highlight:
        c.hline(band_w + 1, band_w + 1, w - 2 * band_w - 2, highlight)
    if shade:
        c.hline(band_w + 1, h - band_w - 2, w - 2 * band_w - 2, shade)
    return c


def button(w, h, outline, light, base, dark):
    c = Pix(w, h)
    for y in range(h):
        for x in range(w):
            corner = (x in (0, w - 1)) and (y in (0, h - 1))
            if corner:
                continue
            if x in (0, w - 1) or y in (0, h - 1):
                col = outline
            elif y == 1:
                col = light
            elif y >= h - 3:
                col = dark
            else:
                col = base
            c.px(x, y, col)
    c.px(1, 1, light); c.px(w - 2, 1, light)
    return c


def save_scaled(c, name, scale=3):
    c.img.resize((c.w * scale, c.h * scale), Image.NEAREST).save(os.path.join(OUT, name))


def build_frames():
    save_scaled(frame(12, 12, O, '#c9b6f0', '#a58fdc', '#fffaff', highlight=None), 'panel.png')
    save_scaled(frame(9, 9, '#8f78cf', '#efe6ff', '#ddd0f7', '#fffaff', band_w=1), 'card.png')
    save_scaled(frame(9, 9, '#8f78cf', '#f4ecff', '#e6dafa', '#f8f3ff', band_w=1), 'inset.png')
    save_scaled(button(9, 9, O, '#ffd3e5', '#f7a8c8', '#d9739f'), 'btn-pink.png')
    save_scaled(button(9, 9, O, '#ffffff', '#f6f0ff', '#cfc0ee'), 'btn-cream.png')
    save_scaled(button(9, 9, O, '#a8e8c8', '#6ccf9c', '#3f9a6c'), 'btn-green.png')
    save_scaled(button(9, 9, O, '#7a67ad', '#5a4790', '#3f306e'), 'btn-nav.png')
    save_scaled(button(9, 9, O, '#ffe0ee', '#ffb3d1', '#e07fab'), 'btn-nav-active.png')
    # starry background tile
    c = Pix(48, 48)
    c.rect(0, 0, 48, 48, '#30254f')
    import random
    r = random.Random(4)
    for _ in range(14):
        c.px(r.randrange(48), r.randrange(48), '#463a73')
    for x, y in ((7, 9), (31, 4), (40, 30), (18, 37)):
        c.px(x, y, '#8f7fc9')
    c.px(24, 20, '#cbbcf7'); c.px(23, 20, '#6c5ca8'); c.px(25, 20, '#6c5ca8'); c.px(24, 19, '#6c5ca8'); c.px(24, 21, '#6c5ca8')
    save_scaled(c, 'bg-stars.png')


def main():
    os.makedirs(OUT, exist_ok=True)
    build_icons()
    build_frames()
    with open(os.path.join(OUT, 'ui-icons.css'), 'w') as fh:
        fh.write('/* Generated by tools/build_ui.py - do not edit by hand. */\n')
        fh.write(".px-icon{display:inline-block;width:24px;height:24px;flex:none;vertical-align:middle;"
                 "background-image:url('icons.png');background-repeat:no-repeat;"
                 f"background-size:{len(ICON_ORDER) * 100}% 100%;image-rendering:pixelated;image-rendering:crisp-edges}}\n")
        for i, name in enumerate(ICON_ORDER):
            fh.write(f".i-{name}{{background-position:{i * 100 / (len(ICON_ORDER) - 1):.4f}% 0}}\n")
    print('ui built:', len(ICON_ORDER), 'icons')


if __name__ == '__main__':
    main()
