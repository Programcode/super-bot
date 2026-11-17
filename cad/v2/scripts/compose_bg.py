"""compose_bg.py: put transparent viewport captures on a dark studio gradient like the target photo.
usage: python3 compose_bg.py <in.png> <out.png>"""
import sys
from PIL import Image


def main(src, dst):
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    bg = Image.new('RGBA', (w, h))
    px = bg.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = (int(52 - 14 * t), int(56 - 14 * t), int(66 - 14 * t), 255)
        for x in range(w):
            px[x, y] = c
    bg.alpha_composite(im)
    bg.convert('RGB').save(dst, optimize=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
