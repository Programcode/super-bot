"""annotate.py: draw numbered part badges on the Fusion images made by diag.py.

usage: python3 annotate.py <in_dir> <out_dir>
Reads <name>.png + <name>.json (label anchors in pixels) and writes <name>.png with
badges, leader lines and a caption.
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

CAPTIONS = {
    'diag-level0-top': 'Level 0, on the chassis plate (seen from above, everything else hidden)',
    'diag-level1-top': 'Level 1, the upper deck (seen from above, everything else hidden)',
    'diag-neck-base': 'Neck base: pan bearings and pan servo (body hidden)',
    'diag-head': 'Head and tilt joint (body hidden)',
    'diag-exploded': 'Exploded view: base, upper deck, shell, neck and head pulled apart',
    'diag-front': 'Assembled, from the front',
}
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R = 15


def place(labels, w, h):
    placed = []
    for lab in labels:
        ax, ay = lab['x'], lab['y']
        best = (ax, ay)
        ok = all(math.hypot(ax - px, ay - py) > 2 * R + 4 for px, py, _ in placed)
        if not ok:
            found = False
            for ring in range(1, 14):
                for k in range(16):
                    a = k * math.pi / 8
                    x, y = ax + math.cos(a) * ring * 18, ay + math.sin(a) * ring * 18
                    if R < x < w - R and 40 < y < h - R and all(math.hypot(x - px, y - py) > 2 * R + 4 for px, py, _ in placed):
                        best, found = (x, y), True
                        break
                if found:
                    break
        placed.append((best[0], best[1], lab))
    return placed


def draw(src, meta, dst, caption):
    im = Image.open(src).convert('RGB')
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 15)
    fc = ImageFont.truetype(FONT, 22)
    placed = place(meta['labels'], im.width, im.height)
    for x, y, lab in placed:
        if math.hypot(x - lab['x'], y - lab['y']) > 1:
            d.line([(lab['x'], lab['y']), (x, y)], fill=(255, 255, 255), width=2)
        d.ellipse([lab['x'] - 3, lab['y'] - 3, lab['x'] + 3, lab['y'] + 3], fill=(255, 159, 28))
    for x, y, lab in placed:
        d.ellipse([x - R, y - R, x + R, y + R], fill=(255, 159, 28), outline=(20, 20, 20), width=2)
        t = str(lab['n'])
        tw = d.textlength(t, font=f)
        d.text((x - tw / 2, y - 9), t, font=f, fill=(15, 15, 15))
    d.rectangle([0, 0, im.width, 36], fill=(20, 22, 28))
    d.text((12, 6), caption, font=fc, fill=(235, 235, 235))
    im.save(dst, optimize=True)


def main(src_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, cap in CAPTIONS.items():
        meta = json.load(open(os.path.join(src_dir, name + '.json')))
        draw(os.path.join(src_dir, name + '.png'), meta, os.path.join(out_dir, name + '.png'), cap)
        print('wrote', name, len(meta['labels']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
