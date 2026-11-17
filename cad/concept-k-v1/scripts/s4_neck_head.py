# Stage 4: neck (pan bearing hub, tube, pan servo, tilt yoke + servo) and head
# (printed stadium shell in two halves, internal frame, C270, 1.3" TFT, face).

PARAMS4 = [
    ('neck_od', '25 mm', 'Neck tube OD (25x1 aluminium tube, cables inside)'),
    ('neck_id', '23 mm', 'Neck tube ID (C270 USB-A plug passes)'),
    ('neck_len', '480 mm', 'Neck: top panel to tilt axis. Sets overall height'),
    ('tilt_z', 'body_top + neck_len', 'Head tilt axis height'),
    ('head_w', '136 mm', 'Head width (C270 + TFT side by side, inside the straight section)'),
    ('head_h', '56 mm', 'Head height'),
    ('head_d', '50 mm', 'Head depth'),
    ('head_yc', 'neck_y + 8 mm', 'Head centre Y'),
    ('head_zc', 'tilt_z + 27 mm + head_h/2', 'Head centre Z'),
    ('c270_w', '72.9 mm', 'C270 body width without clip (SRC 72.91)'),
    ('c270_h', '31.9 mm', 'C270 body height (SRC 31.91)'),
    ('c270_d', '25 mm', 'C270 body depth without clip (EST)'),
    ('tft_s', '35.8 mm', 'Adafruit 4313 1.3in 240x240 TFT board (SRC)'),
    ('tft_t', '5.3 mm', 'TFT board thickness (SRC)'),
]


def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def B(c, name, x, y, z, w, d, h, mat=None, look=None, op=NEWB, bodies=None):
    b = box(c, name, {'x': x, 'y': y, 'z': '(%s) + (%s)/2' % (z, h)}, {'x': w, 'y': d, 'z': h}, op=op, bodies=bodies)
    if op == NEWB:
        finish(b, mat, look)
    return b


def C(c, name, axis, x, y, z, dia, ln, mat=None, look=None, op=NEWB, bodies=None):
    b = cyl(c, name, axis, {'x': x, 'y': y, 'z': z}, dia, ln, op=op, bodies=bodies)
    if op == NEWB:
        finish(b, mat, look)
    return b


BLK = 'Plastic - Matte (Black)'
NECK = 'Chrome - Black'


def servo(c, tag, x, y, z, axis):
    """MG90S (22.8 x 12.2 x 28.5 incl. gear top). axis: 'z' = shaft up, 'x' = shaft +X. x,y,z = shaft base point."""
    s = sub(c, 'Servo MG90S %s (placeholder)' % tag)
    if axis == 'z':
        B(s, 'MG90S body', x, '(%s) - 5.4 mm' % y, '(%s) - 28.5 mm' % z, '12.2 mm', '22.8 mm', '22.7 mm', 'ABS Plastic', BLK)
        B(s, 'MG90S tabs', x, '(%s) - 5.4 mm' % y, '(%s) - 28.5 mm + 16 mm' % z, '12.2 mm', '32.5 mm', '2.5 mm', 'ABS Plastic', BLK)
        B(s, 'MG90S gear top', x, '(%s) - 2.5 mm' % y, '(%s) - 5.8 mm' % z, '12.2 mm', '15 mm', '5.8 mm', 'ABS Plastic', BLK)
        C(s, 'MG90S shaft', 'z', x, y, '(%s) + 1.5 mm' % z, '5 mm', '3 mm', 'Steel', 'Steel - Satin')
    else:
        B(s, 'MG90S body', '(%s) - 28.5 mm + 22.7 mm/2' % x, '(%s) - 5.4 mm' % y, '(%s) - 6.1 mm' % z, '22.7 mm', '22.8 mm', '12.2 mm', 'ABS Plastic', BLK)
        B(s, 'MG90S tabs', '(%s) - 28.5 mm + 16 mm + 1.25 mm' % x, '(%s) - 5.4 mm' % y, '(%s) - 6.1 mm' % z, '2.5 mm', '32.5 mm', '12.2 mm', 'ABS Plastic', BLK)
        B(s, 'MG90S gear top', '(%s) - 2.9 mm' % x, '(%s) - 2.5 mm' % y, '(%s) - 6.1 mm' % z, '5.8 mm', '15 mm', '12.2 mm', 'ABS Plastic', BLK)
        C(s, 'MG90S shaft', 'x', '(%s) + 1.5 mm' % x, y, z, '5 mm', '3 mm', 'Steel', 'Steel - Satin')
    return s


def neck():
    c = fresh('Neck (pan + tilt)')
    # pan bearing hub through the top panel, 2x 6804 bearings
    hub = C(c, 'pan hub flange (printed)', 'z', '0 mm', 'neck_y', 'body_top + 2.5 mm', 'neck_od + 36 mm', '5 mm', 'PET Plastic', BLK)
    hb = C(c, 'pan hub body', 'z', '0 mm', 'neck_y', 'body_top - 11 mm', 'neck_od + 14 mm', '22 mm', 'PET Plastic', BLK)
    combine(c, hub, [hb], JOIN)
    C(c, 'bore', 'z', '0 mm', 'neck_y', 'body_top - 11 mm', 'neck_od + 12.1 mm', '24 mm', op=CUT, bodies=[hub])  # open bottom; printed retaining ring holds the lower bearing
    C(c, 'tube hole', 'z', '0 mm', 'neck_y', 'body_top + 2 mm', 'neck_od + 1 mm', '8 mm', op=CUT, bodies=[hub])
    hub.name = 'pan bearing hub (printed)'
    for k, zz in enumerate(('body_top - 7 mm', 'body_top - 18 mm')):
        b = C(c, '6805 bearing 25x37x7 %d (placeholder)' % (k + 1), 'z', '0 mm', 'neck_y', zz, 'neck_od + 12 mm', '7 mm', 'Steel', 'Steel - Satin')
        C(c, 'bore', 'z', '0 mm', 'neck_y', zz, 'neck_od', '8 mm', op=CUT, bodies=[b])
    # tube: from the pan coupler (below the bearings) to the tilt yoke
    t0 = 'deck_top + 16.5 mm'  # servo tabs on the deck top -> shaft top -> tube bottom
    tb = tube(c, 'neck tube 25x1 aluminium', 'z', {'x': '0 mm', 'y': 'neck_y', 'z': '((%s) + tilt_z - 12 mm)/2' % t0}, 'neck_od', 'neck_id',
              '(tilt_z - 12 mm) - (%s)' % t0)
    finish(tb, 'Aluminum 6061', NECK)
    B(c, 'cable exit slot', '0 mm', '(neck_y) - neck_od/2', '(%s) + 4 mm' % t0, '8 mm', '4 mm', '12 mm', op=CUT, bodies=[tb])  # below the hub
    col = tube(c, 'neck thrust collar 25 mm bore (placeholder)', 'z', {'x': '0 mm', 'y': 'neck_y', 'z': 'body_top - 1.4 mm'}, '30 mm', 'neck_od', '4 mm')
    finish(col, 'Aluminum 6061', 'Aluminum - Satin')
    rr = tube(c, 'bearing retaining ring (printed)', 'z', {'x': '0 mm', 'y': 'neck_y', 'z': 'body_top - 23 mm'}, 'neck_od + 14 mm', 'neck_od + 5 mm', '2 mm')
    finish(rr, 'PET Plastic', BLK)
    cp = C(c, 'pan coupler (printed)', 'z', '0 mm', 'neck_y', '(%s) - 2 mm' % t0, 'neck_od + 6 mm', '4 mm', 'PET Plastic', BLK)
    C(c, 'horn spline', 'z', '0 mm', 'neck_y', '(%s) - 2 mm' % t0, '5.2 mm', '5 mm', op=CUT, bodies=[cp])
    # pan servo standing on the deck in a printed tower
    servo(c, 'pan', '0 mm', 'neck_y', '(%s) - 4 mm' % t0, 'z')
    # the pan servo drops through a deck cut-out; its tabs screw to the deck top
    # tilt yoke: sleeve on the tube top + servo housing, servo shaft along +X
    sl = C(c, 'tilt yoke sleeve', 'z', '0 mm', 'neck_y', 'tilt_z - 23 mm', 'neck_od + 6 mm', '32 mm', 'PET Plastic', BLK)
    hs = B(c, 'tilt servo housing', '-2 mm', '(neck_y) - 5.4 mm', 'tilt_z - 8.5 mm', '32 mm', '36 mm', '17 mm', 'PET Plastic', BLK)
    combine(c, sl, [hs], JOIN)
    C(c, 'sleeve bore', 'z', '0 mm', 'neck_y', 'tilt_z - 26 mm', 'neck_od + 0.3 mm', '28 mm', op=CUT, bodies=[sl])
    # open-top pockets: servo drops in from above, the head bracket closes it
    B(c, 'servo pocket', '14 mm - 17.3 mm', '(neck_y) - 5.4 mm', 'tilt_z - 6.3 mm', '23.4 mm', '23.2 mm', '20 mm', op=CUT, bodies=[sl])
    B(c, 'tab slot', '14 mm - 11.25 mm', '(neck_y) - 5.4 mm', 'tilt_z - 6.3 mm', '3.1 mm', '33 mm', '20 mm', op=CUT, bodies=[sl])
    B(c, 'gear opening', '14 mm - 2.6 mm', '(neck_y) - 2.5 mm', 'tilt_z - 6.3 mm', '7.4 mm', '15.4 mm', '20 mm', op=CUT, bodies=[sl])
    sl.name = 'tilt yoke (printed)'
    servo(c, 'tilt', '14 mm', 'neck_y', 'tilt_z', 'x')
    # head bracket: horn plate on +X, rising to a plate under the head
    hp = B(c, 'head bracket horn plate', '17.5 mm', 'neck_y', 'tilt_z - 10 mm', '3 mm', '24 mm', '37 mm', 'PET Plastic', BLK)
    hp2 = B(c, 'head bracket top plate', '-2 mm', 'head_yc', 'tilt_z + 24 mm', '42 mm', '30 mm', '3 mm', 'PET Plastic', BLK)
    combine(c, hp, [hp2], JOIN)
    C(c, 'horn spline', 'x', '17.5 mm', 'neck_y', 'tilt_z', '5.2 mm', '4 mm', op=CUT, bodies=[hp])
    hp.name = 'head tilt bracket (printed)'
    log('neck ok, head top z =', mm('head_zc + head_h/2'))


def head():
    smoked = appearance('SB Smoked PETG v2', 'Glass (Grey)')
    c = fresh('Head (printed shell + C270 + TFT)')
    # outer solid -> stadium in front view -> soft front/back edges -> hollow
    h = B(c, 'head shell', '0 mm', 'head_yc', 'head_zc - head_h/2', 'head_w', 'head_d', 'head_h', 'PET Plastic', smoked)
    fillet(c, edges_where(h, lambda e: is_axis_line(e, 'y')), 'head_h/2 - 0.05 mm')
    fy = mm('head_yc + head_d/2') / 10.0
    by = mm('head_yc - head_d/2') / 10.0
    fe = OC.create()
    for e in h.edges:
        ys = [e.startVertex.geometry.y if e.startVertex else None, e.endVertex.geometry.y if e.endVertex else None]
        bb = e.boundingBox
        if abs(bb.minPoint.y - bb.maxPoint.y) < 1e-6 and (abs(bb.minPoint.y - fy) < 1e-6 or abs(bb.minPoint.y - by) < 1e-6):
            fe.add(e)
    fillet(c, fe, '8 mm')
    bc = OC.create()
    bc.add(h)
    si = c.features.shellFeatures.createInput(bc, False)
    si.insideThickness = V.createByString('pwall')
    c.features.shellFeatures.add(si)
    # openings in the front: TFT window and C270 lens
    # C270 + 4 mm gap + TFT centred as a group so their corners clear the rounded ends
    tx = '-((c270_w + 4 mm + tft_s)/2 - tft_s/2)'
    cx = '((c270_w + 4 mm + tft_s)/2 - c270_w/2)'
    B(c, 'TFT window', tx, 'head_yc + head_d/2 - 1.5 mm', 'head_zc - 14.5 mm', '29 mm', '6 mm', '29 mm', op=CUT, bodies=[h])
    C(c, 'lens hole', 'y', cx, 'head_yc + head_d/2 - 1.5 mm', 'head_zc', '15 mm', '6 mm', op=CUT, bodies=[h])
    er = C(c, 'eye ring bezel (printed)', 'y', cx, 'head_yc + head_d/2 + 0.75 mm', 'head_zc', '31 mm', '1.5 mm', 'PET Plastic', 'Plastic - Glossy (Black)')
    C(c, 'eye ring bore', 'y', cx, 'head_yc + head_d/2 + 0.75 mm', 'head_zc', '15 mm', '3 mm', op=CUT, bodies=[er])
    C(c, 'bracket hole', 'z', '-2 mm', 'head_yc', 'head_zc - head_h/2 + 1 mm', '14 mm', '4 mm', op=CUT, bodies=[h])
    # split into front and back halves (each prints flat on a 256 bed)
    pi = c.constructionPlanes.createInput()
    pi.setByOffset(c.xZConstructionPlane, V.createByString('head_yc - 6 mm'))
    pl = c.constructionPlanes.add(pi)
    if abs(pl.geometry.origin.y * 10 - mm('head_yc - 6 mm')) > 0.01:
        pl.deleteMe()
        pi = c.constructionPlanes.createInput()
        pi.setByOffset(c.xZConstructionPlane, V.createByString('-(head_yc - 6 mm)'))
        pl = c.constructionPlanes.add(pi)
    pl.isLightBulbOn = False
    sp = c.features.splitBodyFeatures.createInput(h, pl, True)
    sf = c.features.splitBodyFeatures.add(sp)
    for b in sf.bodies:
        b.name = 'head shell front (printed)' if b.boundingBox.maxPoint.y * 10 > mm('head_yc') + 1 else 'head shell back (printed)'
    # TFT window insert (clear)
    w = B(c, 'TFT window insert 1 mm clear acrylic', tx, 'head_yc + head_d/2 - pwall - 0.75 mm', 'head_zc - 16 mm', '32 mm', '1 mm', '32 mm', 'Acrylic', 'Acrylic (Clear)')
    # internal frame (printed) with TFT standoffs and C270 strap
    fyb = 'head_yc + head_d/2 - pwall - 0.6 mm - c270_d - 1 mm - 3 mm'
    fr = B(c, 'head frame (printed)', '-2 mm', fyb, 'head_zc - 15 mm', 'c270_w + 4 mm + tft_s', '3 mm', '30 mm', 'PET Plastic', BLK)
    ft = B(c, 'frame foot', '-2 mm', 'head_yc', 'head_zc - head_h/2 + pwall', '30 mm', '24 mm', '3 mm', 'PET Plastic', BLK)
    combine(c, fr, [ft], JOIN)
    fr.name = 'head frame (printed)'
    # C270 (no clip), clamped between the front shell and the frame by a foam pad
    cam = sub(c, 'Logitech C270 (clip removed)')
    cy0 = 'head_yc + head_d/2 - pwall - 0.6 mm'
    B(c, 'C270 foam pad (EVA 2.5 mm)', cx, '(%s) - c270_d - 1.25 mm' % cy0, 'head_zc - 10 mm', '50 mm', '2.5 mm', '20 mm', 'Rubber', 'Rubber - Soft')
    cb = B(cam, 'C270 body', cx, '(%s) - c270_d/2' % cy0, 'head_zc - c270_h/2', 'c270_w', 'c270_d', 'c270_h', 'ABS Plastic', 'Plastic - Glossy (Black)')
    fillet(cam, edges_where(cb, lambda e: is_axis_line(e, 'y')), '10 mm')
    C(cam, 'C270 lens bezel', 'y', cx, '(%s) + 1 mm' % cy0, 'head_zc', '13 mm', '2 mm', 'Aluminum 6061', 'Chrome - Black')
    C(cam, 'C270 lens', 'y', cx, '(%s) + 2.2 mm' % cy0, 'head_zc', '7 mm', '0.6 mm', 'Glass', 'Glass (Blue)')
    C(cam, 'C270 activity LED', 'y', '(%s) + 22 mm' % cx, '(%s) + 0.3 mm' % cy0, 'head_zc', '2 mm', '0.6 mm', 'ABS Plastic', 'Glass (Clear)')
    # TFT
    tf = sub(c, 'TFT 1.3in 240x240 ST7789 (Adafruit 4313)')
    ty0 = 'head_yc + head_d/2 - pwall - 1.5 mm'
    B(tf, 'TFT PCB', tx, '(%s) - tft_t + 1.6 mm/2' % ty0, 'head_zc - tft_s/2', 'tft_s', '1.6 mm', 'tft_s', 'FR4', 'Plastic - Matte (Black)')
    B(tf, 'TFT module', tx, '(%s) - 3.7 mm/2' % ty0, 'head_zc - 16 mm', '30 mm', '3.7 mm', '32 mm', 'Glass', 'Plastic - Glossy (Black)')
    for hx in (-1, 1):
        for hz in (-1, 1):
            C(tf, 'M2.5 standoff', 'y', '(%s) + %d*15 mm' % (tx, hx), '((%s) - tft_t + (%s) + 3 mm)/2' % (ty0, fyb), 'head_zc + %d*15 mm' % hz,
              '4.5 mm', '((%s) - tft_t) - ((%s) + 1.5 mm)' % (ty0, fyb), 'Copper, Alloy', 'Brass - Polished')
    # face graphic on the display (non-physical, shown so the robot reads as alive)
    g = appearance('SB Eye glow cyan', 'LED - SMD 5050 - 20lm (White)')
    fg = sub(c, 'Face graphic on TFT (display content, not a part)')
    fy = '(%s) + 0.075 mm' % ty0
    for nm, ex in (('eye left', '-5.5 mm'), ('eye right', '5.5 mm')):
        e = C(fg, nm, 'y', '(%s) + (%s)' % (tx, ex), fy, 'head_zc + 3 mm', '5.4 mm', '0.15 mm')
        e.appearance = g
    sk = sketch(fg, 'y', 'smile')
    circle(sk, {'x': tx, 'z': 'head_zc - 1 mm'}, '15 mm')
    circle(sk, {'x': tx, 'z': 'head_zc + 0.3 mm'}, '15 mm')

    def lowest(p):
        cz = sk.sketchToModelSpace(p.areaProperties().centroid).z
        return all(cz <= sk.sketchToModelSpace(q.areaProperties().centroid).z + 1e-9 for q in sk.profiles)
    sm = extrude(fg, sk, ty0, '0.15 mm', which=lowest, name='smile').bodies.item(0)
    sm.appearance = g
    log('head ok')


def main(parts=('neck', 'head')):
    for n, e, cm in PARAMS4:
        param(n, e, cm)
    if 'neck' in parts:
        neck()
    if 'head' in parts:
        head()
    done()
