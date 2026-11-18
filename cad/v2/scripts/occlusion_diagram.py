"""occlusion_diagram.py: top-down LD19 occlusion diagram for lidar options A and B.

usage: python3 occlusion_diagram.py <out.png>
Geometry comes from the v2 parameters (mm, +Y = front, +X = robot right). Option A: the low pod,
scan plane between the plinth and the turret; the only thing in the plane is the 30 mm knuckle.
Option B: the tall pod (lidar_rise), scan plane above the head at every pan/tilt; nothing of the
robot is in the plane.
"""
import math, sys
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG, FG, MUTED, ACC, BLOCK = (24, 26, 32), (236, 236, 236), (150, 155, 165), (255, 159, 28), (230, 70, 70)

P = dict(body=200.0, corner_r=14.0, wheel_xc=128.0, wheel_y=76.1, wheel_d=100.0, wheel_w=50.0,
         pan_x=0.0, pan_y=20.0, knuckle_d=30.0, plinth_s=64.0, lidar_x=-50.0, lidar_y=-58.0, ld19_d=35.3,
         pod_w=70.0, pod_d=64.0, head_w=190.0, head_d=64.0, T=278.0, scan_a=301.0, scan_b=467.0, head_top_max=434.0, mast_x=-70.0, mast_y=-72.0, sweep_r=98.0)


def blocked(p):
    dx, dy = p['pan_x'] - p['lidar_x'], p['pan_y'] - p['lidar_y']
    d = math.hypot(dx, dy)
    half = math.degrees(math.asin((p['knuckle_d'] / 2) / d))
    bearing = math.degrees(math.atan2(dx, dy))   # clockwise from forward (+Y), positive toward +X
    return d, 2 * half, bearing


def panel(d, ox, oy, s, title, sub, option, p):
    def W(x, y):  # model mm -> image px (top view: +Y up, +X right)
        return ox + x * s, oy - y * s
    f = ImageFont.truetype(FONT, 18)
    fb = ImageFont.truetype(FONTB, 22)
    fbig = ImageFont.truetype(FONTB, 40)
    d.text((ox - 330, oy - 470), title, font=fb, fill=FG)
    d.text((ox - 330, oy - 440), sub, font=f, fill=MUTED)
    # range ring 1 m around the lidar
    lx, ly = (p['lidar_x'], p['lidar_y']) if option == 'A' else (p['mast_x'], p['mast_y'])
    R = 380.0
    # blocked wedge
    dist, ang, brg = blocked(p)
    if option == 'A':
        a0, a1 = brg - ang / 2, brg + ang / 2
        pts = [W(lx, ly)]
        for k in range(41):
            a = math.radians(a0 + (a1 - a0) * k / 40)
            pts.append(W(lx + R * math.sin(a), ly + R * math.cos(a)))
        d.polygon(pts, fill=(120, 40, 46))
        for a in (a0, a1):
            r = math.radians(a)
            d.line([W(lx, ly), W(lx + R * math.sin(r), ly + R * math.cos(r))], fill=BLOCK, width=2)
    # body, wheels, plinth, pod
    b = p['body'] / 2
    d.rounded_rectangle([W(-b, b), W(b, -b)], radius=int(p['corner_r'] * s), outline=MUTED, width=2)
    for sx in (1, -1):
        for sy in (1, -1):
            cx, cy = sx * p['wheel_xc'], sy * p['wheel_y']
            d.rectangle([W(cx - p['wheel_w'] / 2, cy + p['wheel_d'] / 2), W(cx + p['wheel_w'] / 2, cy - p['wheel_d'] / 2)], outline=MUTED, width=2)
    ps = p['plinth_s'] / 2
    d.rectangle([W(p['pan_x'] - ps, p['pan_y'] + ps), W(p['pan_x'] + ps, p['pan_y'] - ps)], outline=(110, 115, 125), width=1)
    d.rounded_rectangle([W(p['lidar_x'] - p['pod_w'] / 2, p['lidar_y'] + p['pod_d'] / 2), W(p['lidar_x'] + p['pod_w'] / 2, p['lidar_y'] - p['pod_d'] / 2)], radius=int(16 * s), outline=(110, 115, 125), width=1)
    hw, hd = p['head_w'] / 2, p['head_d'] / 2
    d.rounded_rectangle([W(p['pan_x'] - hw, p['pan_y'] + hd), W(p['pan_x'] + hw, p['pan_y'] - hd)], radius=int(hd * s), outline=(90, 140, 200), width=2)
    d.text(W(p['pan_x'] + hw + 4, p['pan_y'] + 10), 'head (pan 0)', font=f, fill=(90, 140, 200))
    sr = p['sweep_r']
    d.ellipse([W(p['pan_x'] - sr, p['pan_y'] + sr), W(p['pan_x'] + sr, p['pan_y'] - sr)], outline=(90, 140, 200), width=1)
    d.text(W(p['pan_x'] - 60, p['pan_y'] - sr - 6), 'head sweep r %.0f' % sr, font=f, fill=(90, 140, 200))
    if option == 'B':
        md = math.hypot(lx - p['pan_x'], ly - p['pan_y'])
        d.text(W(lx - 120, ly - 40), 'mast %.0f mm from the pan axis' % md, font=f, fill=ACC)
    kr = p['knuckle_d'] / 2
    d.ellipse([W(p['pan_x'] - kr, p['pan_y'] + kr), W(p['pan_x'] + kr, p['pan_y'] - kr)], fill=BLOCK if option == 'A' else (70, 74, 84),
              outline=FG, width=1)
    rr = p['ld19_d'] / 2
    d.ellipse([W(lx - rr, ly + rr), W(lx + rr, ly - rr)], fill=ACC, outline=FG, width=1)
    d.text(W(lx - 60, ly - 26), 'LD19', font=f, fill=ACC)
    # forward arrow
    d.line([W(0, b + 20), W(0, b + 60)], fill=MUTED, width=2)
    d.polygon([W(-6, b + 60), W(6, b + 60), W(0, b + 72)], fill=MUTED)
    d.text(W(10, b + 74), 'front (+Y)', font=f, fill=MUTED)
    if option == 'A':
        d.text((ox - 330, oy + 330), '%.1f deg blocked' % ang, font=fbig, fill=BLOCK)
        d.text((ox - 330, oy + 380), 'Knuckle (30 mm) %.0f mm from the lidar, centred %.0f deg' % (dist, brg), font=f, fill=FG)
        d.text((ox - 330, oy + 404), 'right of forward. Fixed sector: mask it in software.', font=f, fill=FG)
        d.text((ox - 330, oy + 428), 'Scan plane %.0f mm above the floor.' % p['scan_a'], font=f, fill=MUTED)
    else:
        d.text((ox - 330, oy + 330), '0 deg blocked', font=fbig, fill=(90, 200, 120))
        d.text((ox - 330, oy + 380), 'Scan plane %.0f mm above the floor, above the head' % p['scan_b'], font=f, fill=FG)
        d.text((ox - 330, oy + 404), '(head top reaches %.0f mm at full tilt). A 20 mm mast from' % p['head_top_max'], font=f, fill=FG)
        d.text((ox - 330, oy + 428), 'the pod, outside the head sweep. Misses more low obstacles.', font=f, fill=MUTED)


def main(out):
    w, h = 1500, 1080
    im = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(im)
    ft = ImageFont.truetype(FONTB, 28)
    d.text((30, 20), 'LD19 lidar occlusion, top view (robot outline, both options)', font=ft, fill=FG)
    d.text((30, 58), 'Shaded wedge = what the robot itself hides from the lidar. v1 for comparison: about 9 deg (neck tube).',
           font=ImageFont.truetype(FONT, 18), fill=MUTED)
    s = 1.35
    panel(d, 380, 560, s, 'Option A: low pod (current)', 'lidar_rise = 0 mm', 'A', P)
    panel(d, 1130, 560, s, 'Option B: mast, LD19 above the head', 'lidar_rise = %.0f mm' % (P['scan_b'] - P['scan_a']), 'B', P)
    im.save(out, optimize=True)
    print('A: d=%.1f mm, blocked %.2f deg, bearing %.1f deg' % blocked(P))


if __name__ == '__main__':
    main(sys.argv[1])
