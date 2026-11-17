"""callout_annotate.py: technical-manual style callouts for the images from callouts.py.

usage: python3 callout_annotate.py <in_dir> <out_dir>
Each label sits in a side margin and a leader line runs to a dot on the part.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MARGIN = 470
TOP = 64
ACCENT = (255, 159, 28)
BG = (24, 26, 32)


def spread(ys, lo, hi, gap):
    """Keep the order, push labels apart so they are at least `gap` apart and inside [lo, hi]."""
    ys = list(ys)
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + gap)
    if ys and ys[-1] > hi:
        ys[-1] = hi
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - gap)
    return [max(lo, y) for y in ys]


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def draw(src, meta, dst):
    im = Image.open(src).convert('RGB')
    W, H = im.width + 2 * MARGIN, im.height + TOP
    can = Image.new('RGB', (W, H), BG)
    can.paste(im, (MARGIN, TOP))
    d = ImageDraw.Draw(can)
    f = ImageFont.truetype(FONT, 19)
    fb = ImageFont.truetype(FONTB, 19)
    ft = ImageFont.truetype(FONTB, 26)
    d.text((24, 16), meta['title'], font=ft, fill=(240, 240, 240))
    labs = [dict(l, ax=l['x'] + MARGIN, ay=l['y'] + TOP, n=i + 1) for i, l in enumerate(meta['labels'])]
    mid = MARGIN + im.width / 2
    left = sorted([l for l in labs if l['ax'] < mid], key=lambda l: l['ay'])
    right = sorted([l for l in labs if l['ax'] >= mid], key=lambda l: l['ay'])
    for side, group in (('L', left), ('R', right)):
        ys = spread([l['ay'] for l in group], TOP + 30, H - 40, 62)
        for l, y in zip(group, ys):
            lines = wrap(d, l['text'], fb, MARGIN - 90)  # measure with the bold font (widest)
            if side == 'L':
                tx, ex = 20, MARGIN - 18
            else:
                tx, ex = W - MARGIN + 46, W - MARGIN + 18
            # leader: label edge -> elbow at the image border -> part
            d.line([(ex, y), (MARGIN - 4 if side == 'L' else W - MARGIN + 4, y), (l['ax'], l['ay'])], fill=ACCENT, width=2)
            d.ellipse([l['ax'] - 5, l['ay'] - 5, l['ax'] + 5, l['ay'] + 5], fill=ACCENT, outline=(10, 10, 10), width=2)
            th = 24 * len(lines)
            for k, line in enumerate(lines):
                d.text((tx if side == 'L' else tx, y - th / 2 + k * 24), line, font=fb if k == 0 else f, fill=(238, 238, 238))
    can.save(dst, optimize=True)


def main(src, out):
    os.makedirs(out, exist_ok=True)
    for fn in sorted(os.listdir(src)):
        if fn.startswith('co-') and fn.endswith('.json'):
            name = fn[3:-5]
            meta = json.load(open(os.path.join(src, fn)))
            draw(os.path.join(src, 'co-' + name + '.png'), meta, os.path.join(out, name + '.png'))
            print('wrote', name, len(meta['labels']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
