"""finish.py: post-process the Cycles renders (VPS, plain python3 + Pillow).

usage: python3 cad/v2/render/finish.py <render dir>
  - <name>-labels.json + <name>.png -> <name>.png with callouts (scripts/callout_annotate.py style)
  - side-by-side: docs/concepts/v2-target-photo.png next to photo.png -> vs-target-photo.png
  - contact sheet of every PNG -> contact-sheet.png
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'cad', 'v2', 'scripts'))
import callout_annotate  # noqa: E402

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG = (24, 26, 32)

ORDER = ['hero', 'front', 'side', 'rear', 'top', 'rear34', 'photo', 'apartment', 'cutaway', 'insides-front', 'insides-rear',
         'exploded', 'exploded-labels', 'close-head', 'close-board', 'close-battery', 'close-wheel', 'close-lidar',
         'vs-target-photo']
TITLES = {
    'hero': 'Hero, 3/4 front', 'front': 'Front', 'side': 'Side (right)', 'rear': 'Rear', 'top': 'Top',
    'rear34': '3/4 rear', 'photo': 'Target-photo viewpoint', 'apartment': 'On an apartment floor', 'cutaway': 'Cut-away (front, right wall, top off)',
    'insides-front': 'Shell off, front 3/4', 'insides-rear': 'Shell off, rear 3/4', 'exploded': 'Exploded',
    'exploded-labels': 'Exploded, labelled', 'close-head': 'Head and gimbal', 'close-board': 'Main board bay',
    'close-battery': 'Battery sled', 'close-wheel': 'Wheel corner', 'close-lidar': 'Lidar pod',
    'vs-target-photo': 'Target photo vs render',
}


def draw_balanced(src, meta, dst):
    """callout_annotate's look, but the labels split evenly by anchor x so the leaders don't cross."""
    C = callout_annotate
    im = Image.open(src).convert('RGB')
    M, TOP = C.MARGIN, C.TOP
    W, H = im.width + 2 * M, im.height + TOP
    can = Image.new('RGB', (W, H), C.BG)
    can.paste(im, (M, TOP))
    d = ImageDraw.Draw(can)
    f, fb, ft = ImageFont.truetype(FONT, 19), ImageFont.truetype(FONTB, 19), ImageFont.truetype(FONTB, 26)
    d.text((24, 16), meta['title'], font=ft, fill=(240, 240, 240))
    labs = sorted([dict(l, ax=l['x'] + M, ay=l['y'] + TOP) for l in meta['labels']], key=lambda l: l['ax'])
    half = (len(labs) + 1) // 2
    for side, group in (('L', labs[:half]), ('R', labs[half:])):
        group = sorted(group, key=lambda l: l['ay'])
        ys = C.spread([l['ay'] for l in group], TOP + 30, H - 40, 62)
        for l, y in zip(group, ys):
            lines = C.wrap(d, l['text'], fb, M - 90)
            tx, ex = (20, M - 18) if side == 'L' else (W - M + 46, W - M + 18)
            d.line([(ex, y), (M - 4 if side == 'L' else W - M + 4, y), (l['ax'], l['ay'])], fill=C.ACCENT, width=2)
            d.ellipse([l['ax'] - 5, l['ay'] - 5, l['ax'] + 5, l['ay'] + 5], fill=C.ACCENT, outline=(10, 10, 10), width=2)
            th = 24 * len(lines)
            for k, line in enumerate(lines):
                d.text((tx, y - th / 2 + k * 24), line, font=fb if k == 0 else f, fill=(238, 238, 238))
    can.save(dst, optimize=True)


def labels(d):
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json') and os.path.exists(os.path.join(d, fn[:-5] + '.png')):
            meta = json.load(open(os.path.join(d, fn)))
            if 'labels' not in meta:
                continue
            src = os.path.join(d, fn[:-5] + '.png')
            os.makedirs(os.path.join(d, 'raw'), exist_ok=True)
            raw = os.path.join(d, 'raw', fn[:-5] + '.png')
            if not os.path.exists(raw):
                os.rename(src, raw)
            draw_balanced(raw, meta, src)
            print('labelled', fn[:-5], len(meta['labels']))


def side_by_side(d, h=1600):
    photo = os.path.join(REPO, 'docs', 'concepts', 'v2-target-photo.png')
    rnd = os.path.join(d, 'photo.png')
    if not os.path.exists(rnd):
        return
    a = Image.open(photo).convert('RGB')
    b = Image.open(rnd).convert('RGB')
    a = a.resize((int(a.width * h / a.height), h), Image.LANCZOS)
    b = b.resize((int(b.width * h / b.height), h), Image.LANCZOS)
    pad, top = 32, 76
    can = Image.new('RGB', (a.width + b.width + 3 * pad, h + top + pad), BG)
    can.paste(a, (pad, top))
    can.paste(b, (2 * pad + a.width, top))
    dr = ImageDraw.Draw(can)
    f = ImageFont.truetype(FONTB, 32)
    dr.text((pad, 22), 'Target photo', font=f, fill=(235, 235, 235))
    dr.text((2 * pad + a.width, 22), 'Super bot v2, Cycles render (same viewpoint)', font=f, fill=(235, 235, 235))
    can.save(os.path.join(d, 'vs-target-photo.png'), optimize=True)
    print('side-by-side', can.size)


def contact(d, cols=4, tw=640):
    names = [n for n in ORDER if os.path.exists(os.path.join(d, n + '.png'))]
    names += sorted(f[:-4] for f in os.listdir(d) if f.endswith('.png')
                    and f[:-4] not in names and f != 'contact-sheet.png')
    th = 480
    cap = 36
    rows = (len(names) + cols - 1) // cols
    pad = 16
    W = cols * (tw + pad) + pad
    H = 90 + rows * (th + cap + pad) + pad
    can = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(can)
    dr.text((pad, 24), 'Super bot v2: photoreal renders (Blender Cycles, from the Fusion STEP)',
            font=ImageFont.truetype(FONTB, 34), fill=(240, 240, 240))
    f = ImageFont.truetype(FONT, 20)
    for i, n in enumerate(names):
        im = Image.open(os.path.join(d, n + '.png')).convert('RGB')
        im.thumbnail((tw, th), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad)
        y = 90 + (i // cols) * (th + cap + pad)
        can.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        dr.text((x, y + th + 6), '%s  (%s.png)' % (TITLES.get(n, n), n), font=f, fill=(210, 210, 210))
    can.save(os.path.join(d, 'contact-sheet.png'), optimize=True)
    print('contact sheet', len(names), can.size)


if __name__ == '__main__':
    d = sys.argv[1]
    labels(d)
    side_by_side(d)
    contact(d)
