"""sidebyside.py: target photo next to a render, same height, labelled.
usage: python3 sidebyside.py <photo> <render> <out>"""
import sys
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def main(photo, render, out, h=900):
    a = Image.open(photo).convert('RGB')
    b = Image.open(render).convert('RGB')
    a = a.resize((int(a.width * h / a.height), h))
    b = b.resize((int(b.width * h / b.height), h))
    pad, top = 24, 56
    can = Image.new('RGB', (a.width + b.width + 3 * pad, h + top + pad), (24, 26, 32))
    can.paste(a, (pad, top))
    can.paste(b, (2 * pad + a.width, top))
    d = ImageDraw.Draw(can)
    f = ImageFont.truetype(FONT, 24)
    d.text((pad, 16), 'Target photo', font=f, fill=(235, 235, 235))
    d.text((2 * pad + a.width, 16), 'Super bot v2 in Fusion (same viewpoint)', font=f, fill=(235, 235, 235))
    can.save(out, optimize=True)


if __name__ == '__main__':
    main(*sys.argv[1:4])
