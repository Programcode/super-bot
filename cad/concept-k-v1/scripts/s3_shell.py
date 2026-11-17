# Stage 3: body shell. Flat panels are laser-cut 3 mm smoked acrylic; the four
# corner fenders above the wheels and the lidar backpack are printed in smoked
# translucent PETG and each fit a 256 x 256 bed.

PARAMS3 = [
    ('neck_y', '40 mm', 'Neck axis Y (forward of centre, like concept K)'),
    ('lidar_y', '-125 mm', 'Lidar centre Y on the rear backpack'),
    ('pack_h_ped', '18 mm', 'Lidar backpack height above the top panel'),
    ('door_w', 'pack_x + 8 mm', 'Battery door width'),
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


def looks():
    a = appearance('SB Smoked acrylic', 'Glass (Grey)')
    p = appearance('SB Smoked PETG v2', 'Glass (Grey)')
    return a, p


def panels():
    smoked, spetg = looks()
    c = fresh('Shell - acrylic panels (laser cut)')
    ptop = 'body_top - wall_t'
    H = '(%s) - plate_z' % ptop
    # front
    f = B(c, 'front panel', '0 mm', 'shell_y - wall_t/2', 'plate_z', '2*gb_face', 'wall_t', H, 'Acrylic', smoked)
    for tx in (-1, 1):
        C(c, 'HC-SR04 hole', 'y', '%d*13 mm' % tx, 'shell_y - wall_t/2', '46 mm', '16.6 mm', 'wall_t + 1 mm', op=CUT, bodies=[f])
    # rear: battery door opening, rear HC-SR04, service I/O window
    r = B(c, 'rear panel', '0 mm', '-(shell_y - wall_t/2)', 'plate_z', '2*gb_face', 'wall_t', H, 'Acrylic', smoked)
    B(c, 'battery door opening', '0 mm', '-(shell_y - wall_t/2)', 'plate_z - 1 mm', 'door_w + 1 mm', 'wall_t + 1 mm', '42 mm', op=CUT, bodies=[r])
    for tx in (-1, 1):
        C(c, 'HC-SR04 hole', 'y', '%d*13 mm' % tx, '-(shell_y - wall_t/2)', '74 mm', '16.6 mm', 'wall_t + 1 mm', op=CUT, bodies=[r])
    B(c, 'I/O service window', '-12 mm', '-(shell_y - wall_t/2)', 'deck_top + 3 mm', '176 mm', 'wall_t + 1 mm', '16 mm', op=CUT, bodies=[r])
    # sides
    for sx in (1, -1):
        B(c, 'side panel', S(sx, 'shell_x - wall_t/2'), '0 mm', 'plate_z', 'wall_t', '2*(notch_y - 3 mm)', H, 'Acrylic', smoked)
    # top
    sk = sketch(c, 'z', 'top outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': '2*shell_x', 'y': '2*shell_y'})
    t = extrude(c, sk, ptop, 'wall_t', name='top panel').bodies.item(0)
    fillet(c, edges_where(t, lambda e: is_axis_line(e, 'z')), 'corner_r')
    C(c, 'neck hub hole', 'z', '0 mm', 'neck_y', 'body_top - wall_t/2', 'neck_od + 14.5 mm', 'wall_t + 1 mm', op=CUT, bodies=[t])
    C(c, 'lidar cable hole', 'z', '0 mm', 'lidar_y', 'body_top - wall_t/2', '14 mm', 'wall_t + 1 mm', op=CUT, bodies=[t])
    for k in range(7):
        B(c, 'Pi exhaust vent', '(pi_xc - 36 mm) + %d*6 mm' % k, 'pi_yc', 'body_top - wall_t - 1 mm', '3 mm', '44 mm', 'wall_t + 2 mm', op=CUT, bodies=[t])
    finish(t, 'Acrylic', smoked)
    log('panels ok')


def fenders():
    smoked, spetg = looks()
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        c = fresh('Shell - corner fender %s (printed)' % tag)
        x = S(sx, '(gb_face + shell_x)/2')
        y = S(sy, '(notch_y - 3 mm + shell_y)/2')
        h = 'body_top - wall_t - fender_z'
        b = B(c, 'fender %s' % tag, x, y, 'fender_z', 'shell_x - gb_face', 'shell_y - notch_y + 3 mm', h, 'PET Plastic', spetg)
        cx, cy = mm(S(sx, 'shell_x')) / 10.0, mm(S(sy, 'shell_y')) / 10.0
        corner = edges_where(b, lambda e: is_axis_line(e, 'z') and abs(e.startVertex.geometry.x - cx) < 1e-4 and abs(e.startVertex.geometry.y - cy) < 1e-4)
        fillet(c, corner, 'corner_r')
        # small soft radius on the arch lip (bottom outer edges)
        lip = edges_where(b, lambda e: (is_axis_line(e, 'x') or is_axis_line(e, 'y')) and abs(e.startVertex.geometry.z * 10 - mm('fender_z')) < 1e-3
                          and (abs(e.startVertex.geometry.x - cx) < 1e-4 or abs(e.startVertex.geometry.y - cy) < 1e-4))
        fillet(c, lip, '3 mm')
        # hollow: open toward the body interior, 2.4 mm walls
        inner = OC.create()
        ix, iy = mm(S(sx, 'gb_face')) / 10.0, mm(S(sy, 'notch_y - 3 mm')) / 10.0
        for fc in b.faces:
            if fc.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
                continue
            n, p = fc.geometry.normal, fc.pointOnFace
            if (abs(abs(n.x) - 1) < 1e-6 and abs(p.x - ix) < 1e-4) or (abs(abs(n.y) - 1) < 1e-6 and abs(p.y - iy) < 1e-4):
                inner.add(fc)
        si = c.features.shellFeatures.createInput(inner, False)
        si.insideThickness = V.createByString('pwall')
        c.features.shellFeatures.add(si)
    log('fenders ok')


def clips():
    c = fresh('Shell - panel clips (printed)')
    pts = []
    for x in (-110, 0, 110):
        pts.append((x, 1))
        pts.append((x, -1))
    for (x, sy) in pts:
        if x == 0:
            continue  # HC-SR04 at the front, battery door at the rear
        B(c, 'clip', '%d mm' % x, S(sy, 'plate_d/2 - 4 mm'), 'plate_top', '20 mm', '8 mm', '14 mm', 'PET Plastic', 'Plastic - Matte (Black)')
    for sx in (1, -1):
        for y in (-60, 60):
            B(c, 'clip', S(sx, 'plate_w/2 - 4 mm'), '%d mm' % y, 'plate_top', '8 mm', '20 mm', '14 mm', 'PET Plastic', 'Plastic - Matte (Black)')
    log('clips ok')


def backpack():
    smoked, spetg = looks()
    c = fresh('Lidar backpack (printed)')
    b = B(c, 'backpack', '0 mm', 'lidar_y', 'body_top', '72 mm', '62 mm', 'pack_h_ped', 'PET Plastic', 'Plastic - Matte (Black)')
    fillet(c, edges_where(b, lambda e: is_axis_line(e, 'z')), '14 mm')
    top = zfaces(b, True)
    col = OC.create()
    for e in top.edges:
        col.add(e)
    fillet(c, col, '4 mm')
    bot = OC.create()
    bot.add(zfaces(b, False))
    si = c.features.shellFeatures.createInput(bot, False)
    si.insideThickness = V.createByString('pwall')
    c.features.shellFeatures.add(si)
    C(c, 'cable hole', 'z', '0 mm', 'lidar_y', 'body_top + pack_h_ped - 1 mm', '12 mm', '4 mm', op=CUT, bodies=[b])
    for k in range(4):
        B(c, 'side vent', '0 mm', '(lidar_y) - 15 mm + %d*10 mm' % k, 'body_top + 5 mm', '80 mm', '4 mm', '8 mm', op=CUT, bodies=[b])
    l = fresh('Lidar LDROBOT LD19')
    LZ = 'body_top + pack_h_ped'
    base = B(l, 'LD19 base', '0 mm', 'lidar_y', LZ, '46.29 mm', '54 mm', '22.2 mm', 'ABS Plastic', 'Plastic - Matte (Black)')
    fillet(l, edges_where(base, lambda e: is_axis_line(e, 'z')), '8 mm')
    C(l, 'LD19 head ring', 'z', '0 mm', 'lidar_y', '%s + 22.2 mm + 1.3 mm' % LZ, '35.29 mm', '2.6 mm', 'ABS Plastic', 'Plastic - Matte (Black)')
    C(l, 'LD19 optical window', 'z', '0 mm', 'lidar_y', '%s + 22.2 mm + 2.6 mm + 5 mm' % LZ, '35.29 mm', '10 mm', 'ABS Plastic', 'Plastic - Glossy (Black)')
    log('backpack ok')


def main():
    for n, e, cm in PARAMS3:
        param(n, e, cm)
    panels()
    fenders()
    clips()
    backpack()
    done()
