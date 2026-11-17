# Stage 6: head joint and head.
# Fixed: printed plinth (bolted to the top deck through the shell) with 2x 6805 bearings;
#        pan MG90S in a printed cradle under the top deck; 1:1 printed 36T m1 gear pair.
# Pan rotor (component, rotates about the pan axis): 25x1 alu tube shaft, shaft gear,
#        thrust collar, turret with the tilt MG90S, 2x 6800 bearings, tilt hubs.
# Tilt rotor (nested in the pan rotor, rotates about the tilt axis): fork, head shell
#        halves, internal frame, Camera Module 3, 1.3" TFT + window, eye bezel, face graphic.
# The camera ribbon runs down the hollow shaft, through the gear and out of the bottom.

PARAMS6 = [
    ('scan_h', '27 mm', 'LD19 scan plane above its mounting ears (EST from the datasheet figure)'),
    ('plinth_h', '44 mm', 'Plinth height above the shell top'),
    ('stem_gap', '12 mm', 'Exposed stem between plinth and turret (the lidar plane passes here)'),
    ('scan_z', 'body_top + plinth_h + stem_gap/2', 'Lidar scan plane Z'),
    ('turret_z', 'body_top + plinth_h + stem_gap', 'Turret bottom Z'),
    ('tilt_z', 'turret_z + 24 mm', 'Tilt axis Z'),
    ('turret_hw', '31 mm', 'Turret half-width X'),
    ('turret_hd', '22 mm', 'Turret half-depth Y'),
    ('head_w', '92 mm', 'Head width'),
    ('head_h', '48 mm', 'Head height'),
    ('head_d', '38 mm', 'Head depth'),
    ('head_z0', 'tilt_z + 30 mm', 'Head bottom Z (clears the turret at any tilt)'),
    ('head_zc', 'head_z0 + head_h/2', 'Head centre Z'),
    ('gear_z', 'top_deck_z - 10 mm', 'Pan gear pair bottom Z (under the top deck)'),
    ('shaft_z0', 'gear_z - 4 mm', 'Pan shaft bottom Z'),
    ('cam_x', '23 mm', 'Camera Module 3 centre X'),
    ('tft_x', '-12 mm', 'TFT centre X'),
]

ROT = 'Plastic - Matte (Black)'


def define():
    for n, e, cm in PARAMS6:
        param(n, e, cm)


def V3(d, k):
    """unit vector string pieces: d like '+x' -> multiplier for axis k"""
    return (1 if d[0] == '+' else -1) if d[1] == k else 0


def servo(c, tag, sx, sy, sz, sdir, ldir):
    """MG90S at shaft base point (sx,sy,sz) = top of the gear top. sdir = shaft direction ('+z', '-x', ...),
    ldir = direction of the body's long axis away from the shaft. Sizes (SRC TowerPro): body 22.8 x 12.2 x 22.7,
    tabs 32.5, gear top 5.8."""
    s = sub(c, 'Servo MG90S %s' % tag)
    S0 = {'x': sx, 'y': sy, 'z': sz}
    wdir = [k for k in 'xyz' if k not in (sdir[1], ldir[1])][0]

    def part(name, along_s, along_l, ds, dl, dw, mat, look):
        ctr, size = {}, {}
        for k in 'xyz':
            ctr[k] = '(%s) + (%d)*(%s) + (%d)*(%s)' % (S0[k], V3(sdir, k), along_s, V3(ldir, k), along_l)
        size[sdir[1]] = ds
        size[ldir[1]] = dl
        size[wdir] = dw
        b = box(s, name, ctr, size)
        finish(b, mat, look)
        return b
    part('MG90S body', '-(5.8 mm + 22.7 mm/2)', '5.4 mm', '22.7 mm', '22.8 mm', '12.2 mm', 'ABS Plastic', BLACK)
    part('MG90S tabs', '-(28.5 mm - 17.25 mm)', '5.4 mm', '2.5 mm', '32.5 mm', '12.2 mm', 'ABS Plastic', BLACK)
    part('MG90S gear top', '-2.9 mm', '2.5 mm', '5.8 mm', '15 mm', '12.2 mm', 'ABS Plastic', BLACK)
    sp = {k: '(%s) + (%d)*1.5 mm' % (S0[k], V3(sdir, k)) for k in 'xyz'}
    b = cyl(s, 'MG90S spline', sdir[1], sp, '4.8 mm', '3 mm')
    finish(b, 'Steel', STEEL)
    return s


def gear(c, name, x, y, z0, teeth, m, bore, th, mat, look):
    """Spur gear as a base feature (involute approximated by trapezoid teeth), z0 = bottom."""
    pd = teeth * m
    ro, rr = pd / 2 + m, pd / 2 - 1.25 * m
    pts = []
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        da = 2 * math.pi / teeth
        for frac, r in ((0.0, rr), (0.18, rr), (0.32, ro), (0.5, ro), (0.64, rr)):
            a = a0 + frac * da
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    sk = sketch(c, 'z', name)
    poly(sk, [{'x': px, 'y': py, 'z': z0} for px, py in pts])
    sk.isComputeDeferred = False
    prof = max(sk.profiles, key=lambda p: p.areaProperties().area)
    col = OC.create()
    col.add(prof)
    inp = c.features.extrudeFeatures.createInput(col, NEWB)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V.createByReal(z0 / 10.0))
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V.createByReal(th / 10.0)), adsk.fusion.ExtentDirections.PositiveExtentDirection)
    b = c.features.extrudeFeatures.add(inp).bodies.item(0)
    b.name = name
    if bore:
        C(c, 'bore', 'z', '%.3f mm' % x, '%.3f mm' % y, '%.3f mm' % (z0 + th / 2), '%.3f mm' % bore, '%.3f mm' % (th + 2), op=CUT, bodies=[b])
    finish(b, mat, look)
    return b


def fixed():
    c = fresh('Head joint fixed (plinth, pan servo, gears)')
    T = 'body_top'
    # plinth: Ø plinth_d x plinth_h above the shell, base flange on the top deck (under the shell)
    pl = C(c, 'plinth body', 'z', '0 mm', 'pan_y', '(top_deck_top + %s + plinth_h)/2' % T, 'plinth_d', '(%s + plinth_h) - top_deck_top' % T, 'PET Plastic', 'SB Smoked PETG')
    fl = C(c, 'plinth flange', 'z', '0 mm', 'pan_y', 'top_deck_top + 2 mm', '80 mm', '4 mm', 'PET Plastic', 'SB Smoked PETG')
    join(c, pl, [fl])
    top = zfaces(pl, True)
    col = OC.create()
    for e in top.edges:
        col.add(e)
    fillet(c, col, '6 mm')
    # bores: lip hole on top (collar passes), upper bearing seat, middle shoulder, lower bearing seat, open bottom
    C(c, 'lip hole', 'z', '0 mm', 'pan_y', '%s + plinth_h - 2 mm' % T, '32 mm', '6 mm', op=CUT, bodies=[pl])
    C(c, 'upper bearing seat', 'z', '0 mm', 'pan_y', '%s + plinth_h - 3 mm - 3.5 mm' % T, '37.1 mm', '7 mm', op=CUT, bodies=[pl])
    C(c, 'shoulder', 'z', '0 mm', 'pan_y', '(top_deck_top + %s + plinth_h)/2' % T, '31 mm', '(%s + plinth_h) - top_deck_top + 1 mm' % T, op=CUT, bodies=[pl])
    C(c, 'lower bearing seat', 'z', '0 mm', 'pan_y', 'top_deck_top + 4 mm + 3.5 mm', '37.1 mm', '7 mm', op=CUT, bodies=[pl])
    C(c, 'retaining ring recess', 'z', '0 mm', 'pan_y', 'top_deck_top + 2 mm', '44 mm', '4.2 mm', op=CUT, bodies=[pl])
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        C(c, 'M4 flange bolt', 'z', '%.4f*34 mm' % math.cos(r), '(pan_y) + %.4f*34 mm' % math.sin(r), 'top_deck_top + 2 mm', '4.4 mm', '5 mm', op=CUT, bodies=[pl])
    pl.name = 'plinth (printed, smoked)'
    rr = ring(c, 'bearing retaining ring (printed)', 'z', '0 mm', 'pan_y', 'top_deck_top + 2 mm', '43.6 mm', '31 mm', '4 mm', 'PET Plastic', BLACK)
    for k, zc in (('lower', 'top_deck_top + 4 mm + 3.5 mm'), ('upper', '%s + plinth_h - 6.5 mm' % T)):
        ring(c, '6805 bearing 25x37x7 %s' % k, 'z', '0 mm', 'pan_y', zc, '37 mm', 'shaft_od', '7 mm', 'Steel', STEEL)
    # pan servo (shaft up) in a printed cradle hanging from the top deck; 1:1 gear pair under the deck
    sz = 'gear_z - 0.5 mm'
    servo(c, 'pan', 'pan_servo_x', 'pan_y', sz, '+z', '+x')
    cr = B(c, 'pan servo cradle wall', 'pan_servo_x + 5 mm', '(pan_y) - 23 mm', '(%s) - 16 mm' % sz, '44 mm', '4 mm', 'top_deck_z - ((%s) - 16 mm)' % sz, 'PET Plastic', BLACK)
    w2 = B(c, 'cradle wall 2', 'pan_servo_x + 5 mm', '(pan_y) + 23 mm', '(%s) - 16 mm' % sz, '44 mm', '4 mm', 'top_deck_z - ((%s) - 16 mm)' % sz)
    tools = [w2]
    for tx in ('pan_servo_x + 5.4 mm - 14.5 mm', 'pan_servo_x + 5.4 mm + 14.5 mm'):
        tools.append(B(c, 'tab rail', tx, 'pan_y', '(%s) - 16 mm' % sz, '5 mm', '50 mm', '3.5 mm'))
    for ty in ('(pan_y) - 23 mm', '(pan_y) + 23 mm'):
        tools.append(B(c, 'deck flange', 'pan_servo_x + 5 mm', ty, 'top_deck_z - 4 mm', '44 mm', '12 mm', '4 mm'))
    join(c, cr, tools, 'pan servo cradle (printed)')
    gz = mm('gear_z')
    gear(c, 'pan servo gear 36T m1 (printed)', mm('pan_servo_x'), mm('pan_y'), gz, 36, 1.0, 4.8, 6.0, 'PET Plastic', BLACK)
    log('fixed ok')


def pan_rotor():
    c = fresh('Head pan rotor')
    T = 'body_top'
    tb = ring(c, 'pan shaft 25x1 alu tube', 'z', '0 mm', 'pan_y', '(shaft_z0 + turret_z + 7 mm)/2', 'shaft_od', 'shaft_od - 2 mm',
              '(turret_z + 7 mm) - shaft_z0', 'Aluminum 6061', 'Chrome - Black')
    gb = gear(c, 'pan shaft gear 36T m1 (printed)', 0.0, mm('pan_y'), mm('gear_z'), 36, 1.0, mm('shaft_od') + 0.2, 6.0, 'PET Plastic', BLACK)
    ring(c, 'thrust collar 25 mm (on the upper bearing)', 'z', '0 mm', 'pan_y', '%s + plinth_h - 1.5 mm' % T, '30 mm', 'shaft_od', '3 mm', 'Aluminum 6061', ALU)
    # turret: rounded knuckle, top edges along X rounded so the head clears it at any tilt
    t = B(c, 'turret', '0 mm', 'pan_y', 'turret_z', '2*turret_hw', '2*turret_hd', 'tilt_z + 12 mm - turret_z', 'PET Plastic', 'SB Smoked PETG')
    fillet(c, edges_where(t, lambda e: is_axis_line(e, 'z')), '8 mm')
    ztop = mm('tilt_z + 12 mm') / 10.0
    fillet(c, edges_where(t, lambda e: is_axis_line(e, 'x') and abs(e.startVertex.geometry.z - ztop) < 1e-4), '11 mm')
    bc = OC.create()
    bc.add(t)
    si = c.features.shellFeatures.createInput(bc, False)
    si.insideThickness = V.createByString('pwall')
    c.features.shellFeatures.add(si)
    # shaft socket (clamps the tube top), wall bosses for the 6800 bearings
    so = C(c, 'shaft socket', 'z', '0 mm', 'pan_y', 'turret_z + 6 mm', 'shaft_od + 8 mm', '12 mm')
    for sx in (1, -1):
        bo = C(c, 'bearing boss', 'x', S(sx, 'turret_hw - 4 mm'), 'pan_y', 'tilt_z', '25 mm', '8 mm')
        so = join(c, t, [bo]) if False else so
        combine(c, t, [bo], JOIN)
    combine(c, t, [so], JOIN)
    C(c, 'socket bore', 'z', '0 mm', 'pan_y', 'turret_z + 6 mm', 'shaft_od + 0.2 mm', '14 mm', op=CUT, bodies=[t])
    B(c, 'ribbon window', '0 mm', '(pan_y) - 11 mm', 'turret_z + 4 mm', '14 mm', '8 mm', '10 mm', op=CUT, bodies=[t])
    B(c, 'ribbon exit (rear, at the tilt axis)', '0 mm', '(pan_y) - turret_hd', 'tilt_z - 6 mm', '14 mm', '8 mm', '6 mm', op=CUT, bodies=[t])
    for sx in (1, -1):
        C(c, '6800 seat', 'x', S(sx, 'turret_hw - 2.5 mm'), 'pan_y', 'tilt_z', '19.1 mm', '5 mm', op=CUT, bodies=[t])
        C(c, 'hub hole', 'x', S(sx, 'turret_hw - 6 mm'), 'pan_y', 'tilt_z', '11 mm', '12 mm', op=CUT, bodies=[t])
        ring(c, '6800 bearing 10x19x5 %s' % ('right' if sx > 0 else 'left'), 'x', S(sx, 'turret_hw - 2.5 mm'), 'pan_y', 'tilt_z', '19 mm', '10 mm', '5 mm', 'Steel', STEEL)
    t.name = 'turret (printed, smoked)'
    # tilt servo inside the turret: shaft along -X into the left hub, body standing up
    servo(c, 'tilt', '-(turret_hw - 5 mm - 2 mm)', 'pan_y', 'tilt_z', '-x', '-z')
    log('pan rotor ok')
    return c


def tilt_rotor(pc):
    c = sub(pc, 'Head tilt rotor')
    # hubs (printed) through the bearings, fork arms outside the turret, crossbar under the head
    hubs = []
    for sx in (1, -1):
        h = C(c, 'tilt hub %s' % ('right' if sx > 0 else 'left (servo spline inside)'), 'x', S(sx, 'turret_hw - 1 mm'), 'pan_y', 'tilt_z', '10 mm', '9 mm', 'PET Plastic', BLACK)
        f = C(c, 'hub flange', 'x', S(sx, 'turret_hw + 2 mm'), 'pan_y', 'tilt_z', '18 mm', '3 mm', 'PET Plastic', BLACK)
        join(c, h, [f])
        hubs.append(h)
    fk = B(c, 'fork arm', 'turret_hw + 5.5 mm', 'pan_y', 'tilt_z - 10 mm', '4 mm', '20 mm', 'head_z0 - tilt_z + 10 mm', 'PET Plastic', BLACK)
    a2 = B(c, 'fork arm L', '-(turret_hw + 5.5 mm)', 'pan_y', 'tilt_z - 10 mm', '4 mm', '20 mm', 'head_z0 - tilt_z + 10 mm')
    cb = B(c, 'crossbar', '0 mm', 'pan_y', 'head_z0 - 4 mm', '2*turret_hw + 15 mm', '20 mm', '4 mm')
    join(c, fk, [a2, cb], 'tilt fork (printed)')
    for sx in (1, -1):
        C(c, 'M3 hub screw', 'x', S(sx, 'turret_hw + 5.5 mm'), 'pan_y', 'tilt_z', '3.4 mm', '6 mm', op=CUT, bodies=[fk])
    C(c, 'ribbon slot', 'z', '0 mm', '(pan_y) - 6 mm', 'head_z0 - 2 mm', '10 mm', '6 mm', op=CUT, bodies=[fk])
    head(c)
    log('tilt rotor ok')


def head(c):
    hy = 'pan_y'
    smoked = appearance('SB Smoked PETG', 'Glass (Grey)')
    h = B(c, 'head shell', '0 mm', hy, 'head_z0', 'head_w', 'head_d', 'head_h', 'PET Plastic', smoked)
    fillet(c, edges_where(h, lambda e: is_axis_line(e, 'y')), 'head_h/2 - 0.05 mm')
    fy, by = mm('(%s) + head_d/2' % hy) / 10.0, mm('(%s) - head_d/2' % hy) / 10.0
    fe = OC.create()
    for e in h.edges:
        bb = e.boundingBox
        if abs(bb.minPoint.y - bb.maxPoint.y) < 1e-6 and (abs(bb.minPoint.y - fy) < 1e-6 or abs(bb.minPoint.y - by) < 1e-6):
            fe.add(e)
    fillet(c, fe, '7 mm')
    bc = OC.create()
    bc.add(h)
    si = c.features.shellFeatures.createInput(bc, False)
    si.insideThickness = V.createByString('pwall')
    c.features.shellFeatures.add(si)
    front = '(%s) + head_d/2' % hy
    zc = 'head_zc'
    # openings: TFT window, camera lens hole, ribbon slot at the back-bottom, 2x M3 to the crossbar
    B(c, 'TFT window', 'tft_x', '(%s) - 1.5 mm' % front, '(%s) - 13 mm' % zc, '26 mm', '6 mm', '26 mm', op=CUT, bodies=[h])
    C(c, 'lens hole', 'y', 'cam_x', '(%s) - 1.5 mm' % front, '(%s) + 2.5 mm' % zc, '9 mm', '6 mm', op=CUT, bodies=[h])
    B(c, 'ribbon slot', '0 mm', '(pan_y) - 6 mm', 'head_z0 - 1 mm', '14 mm', '4 mm', '4 mm', op=CUT, bodies=[h])
    for sx in (1, -1):
        C(c, 'M3 to crossbar', 'z', S(sx, '24 mm'), hy, 'head_z0 + 1 mm', '3.4 mm', '4 mm', op=CUT, bodies=[h])
    er = C(c, 'eye ring bezel (printed)', 'y', 'cam_x', '(%s) + 0.75 mm' % front, '(%s) + 2.5 mm' % zc, '20 mm', '1.5 mm', 'PET Plastic', 'Plastic - Glossy (Black)')
    C(c, 'eye ring bore', 'y', 'cam_x', '(%s) + 0.75 mm' % front, '(%s) + 2.5 mm' % zc, '9 mm', '3 mm', op=CUT, bodies=[er])
    # split into front and back halves at the frame plane
    pi_ = c.constructionPlanes.createInput()
    pi_.setByOffset(c.xZConstructionPlane, V.createByString('pan_y + 4 mm'))
    pl = c.constructionPlanes.add(pi_)
    if abs(pl.geometry.origin.y * 10 - mm('pan_y + 4 mm')) > 0.01:
        pl.deleteMe()
        pi_ = c.constructionPlanes.createInput()
        pi_.setByOffset(c.xZConstructionPlane, V.createByString('-(pan_y + 4 mm)'))
        pl = c.constructionPlanes.add(pi_)
    pl.isLightBulbOn = False
    sf = c.features.splitBodyFeatures.add(c.features.splitBodyFeatures.createInput(h, pl, True))
    for b in sf.bodies:
        b.name = 'head shell front (printed)' if b.boundingBox.maxPoint.y * 10 > mm('pan_y') + 10 else 'head shell back (printed)'
    w = B(c, 'TFT window 1 mm clear acrylic', 'tft_x', '(%s) - pwall - 0.5 mm' % front, '(%s) - 15 mm' % zc, '30 mm', '1 mm', '30 mm', 'Acrylic', 'Acrylic (Clear)')
    # internal frame (printed) carrying the TFT and the camera, foot onto the crossbar screws
    fyb = '(%s) - pwall - 1 mm - 5 mm - 4 mm - 2.5 mm' % front
    fr = B(c, 'head frame (printed)', '5 mm', fyb, '(%s) - 18 mm' % zc, '72 mm', '2.5 mm', '38 mm', 'PET Plastic', BLACK)
    ft = B(c, 'frame foot', '0 mm', '(%s) - 3 mm' % hy, 'head_z0 + pwall', '56 mm', '14 mm', '2.5 mm', 'PET Plastic', BLACK)
    join(c, fr, [ft], 'head frame (printed)')
    # Camera Module 3 (SRC: 25 x 23.86 x 1.12 PCB, 11.3 overall, lens base 10.8, barrel 5.75, holes 21 x 12.5)
    cm = sub(c, 'Raspberry Pi Camera Module 3')
    cy0 = '(%s) - pwall - 0.6 mm' % front           # lens barrel front
    lz = '(%s) + 2.5 mm' % zc                         # lens axis Z
    pcb_front = '(%s) - 11.3 mm + 1.12 mm' % cy0
    B(cm, 'CM3 PCB', 'cam_x', '(%s) - 0.56 mm' % pcb_front, '(%s) - 14.5 mm' % lz, '25 mm', '1.12 mm', '23.86 mm', 'FR4', GREEN)
    B(cm, 'CM3 lens base', 'cam_x', '(%s) + 2.5 mm' % pcb_front, '(%s) - 5.4 mm' % lz, '10.8 mm', '5 mm', '10.8 mm', 'ABS Plastic', BLACK)
    C(cm, 'CM3 lens barrel', 'y', 'cam_x', '(%s) - 2.6 mm' % cy0, lz, '5.75 mm', '5.2 mm', 'ABS Plastic', 'Chrome - Black')
    C(cm, 'CM3 lens glass', 'y', 'cam_x', '(%s) - 0.1 mm' % cy0, lz, '4 mm', '0.2 mm', 'Glass', 'Glass (Blue)')
    B(cm, 'CM3 FPC connector', 'cam_x', '(%s) - 1.12 mm - 1.65 mm' % pcb_front, '(%s) - 14.5 mm' % lz, '19.6 mm', '3.3 mm', '5.7 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    for hx in (-10.5, 10.5):
        for hz in (0.0, -12.5):
            C(cm, 'M2 standoff', 'y', '(cam_x) + %.1f mm' % hx, '((%s) - 1.12 mm + (%s) + 1.25 mm)/2' % (pcb_front, fyb), '(%s) + %.1f mm' % (lz, hz),
              '3.5 mm', '((%s) - 1.12 mm) - ((%s) + 1.25 mm)' % (pcb_front, fyb), 'Copper, Alloy', BRASS)
    # TFT (Adafruit 4313: 35.56 x 38.1 board, 4x M2.5 on 30.48 x 33.02)
    tf = sub(c, 'TFT 1.3in 240x240 ST7789 (Adafruit 4313)')
    ty0 = '(%s) - pwall - 1 mm' % front
    B(tf, 'TFT PCB', 'tft_x', '(%s) - 4.2 mm' % ty0, '(%s) - 19.05 mm' % zc, '35.56 mm', '1.6 mm', '38.1 mm', 'FR4', BLACK)
    B(tf, 'TFT glass module', 'tft_x', '(%s) - 1.7 mm' % ty0, '(%s) - 15 mm' % zc, '28 mm', '3.4 mm', '30 mm', 'Glass', GLOSSB)
    for hx in (-15.24, 15.24):
        for hz in (-16.51, 16.51):
            C(tf, 'M2.5 standoff', 'y', '(tft_x) + %.2f mm' % hx, '((%s) - 5 mm + (%s) + 1.25 mm)/2' % (ty0, fyb), '(%s) + %.2f mm' % (zc, hz), '4.5 mm',
              '((%s) - 5 mm) - ((%s) + 1.25 mm)' % (ty0, fyb), 'Copper, Alloy', BRASS)
    # face on the TFT (display content, not a part)
    g = appearance('SB Eye glow cyan', 'LED - SMD 5050 - 20lm (White)')
    fg = sub(c, 'Face graphic on TFT (display content, not a part)')
    fy_ = '(%s) + 0.08 mm' % ty0
    for nm, ex in (('eye left', '-5.5 mm'), ('eye right', '5.5 mm')):
        e = C(fg, nm, 'y', '(tft_x) + (%s)' % ex, fy_, '(%s) + 3 mm' % zc, '5.6 mm', '0.15 mm')
        e.appearance = g
    sk = sketch(fg, 'y', 'smile')
    circle(sk, {'x': 'tft_x', 'z': '(%s) - 1 mm' % zc}, '14 mm')
    circle(sk, {'x': 'tft_x', 'z': '(%s) + 0.4 mm' % zc}, '14 mm')

    def lowest(p):
        cz = sk.sketchToModelSpace(p.areaProperties().centroid).z
        return all(cz <= sk.sketchToModelSpace(q.areaProperties().centroid).z + 1e-9 for q in sk.profiles)
    sm = extrude(fg, sk, ty0, '0.15 mm', which=lowest, name='smile').bodies.item(0)
    sm.appearance = g
    log('head ok, head top z =', mm('head_z0 + head_h'))


def main(parts=('fixed', 'pan')):
    define()
    if 'fixed' in parts:
        fixed()
    if 'pan' in parts:
        pc = pan_rotor()
        tilt_rotor(pc)
    done()
