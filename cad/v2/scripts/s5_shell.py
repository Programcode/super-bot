# Stage 5: the printed smoked-PETG shell (every piece fits a 256 mm bed).
# One rounded box (vertical corners corner_r, top edges top_r), shelled to pwall, open at the
# bottom, cut with seam_gap into:
#   front wall and rear wall (each includes both vertical corner rounds),
#   left and right side walls (flat, U-slots let them lift off over the wheel shafts),
#   top half left / right (split at x = 0, notched round the plinth and the lidar pod),
#   battery door (bottom centre of the rear wall, screwed to the sled, carries the charge jack).
# Removal order: slide the top halves out sideways, then lift the walls straight up.
# Retention: drop-in tabs into printed clips on the plate edge at the bottom, 6 x 3 mm magnet
# pairs at the top (frame blocks under the top deck edge), 2 magnets per top half.

PARAMS5 = [
    ('seam_gap', '0.4 mm', 'Gap between shell pieces'),
    ('wall_top', 'body_top - top_r - 2 mm', 'Seam between the walls and the top halves'),
    ('wall_seam_y', 'shell_y - corner_r', 'Seam between the front/rear walls and the side walls'),
    ('door_hw', 'tun_hw - 2 mm', 'Battery door half-width'),
    ('door_top', 'body_z0 + 100 mm', 'Battery door top'),
    ('plinth_s', '64 mm', 'Head plinth size (square)'),
    ('pod_w', '70 mm', 'Lidar pod width X'),
    ('pod_d', '64 mm', 'Lidar pod depth Y'),
    ('top_seam_y', '(pan_y - plinth_s/2 + lidar_y + pod_d/2)/2', 'Seam between the front and rear top halves'),
    ('bar_z', 'body_top - 40 mm', 'LED bar centre Z'),
    ('bar_w', '140 mm', 'LED bar slot length'),
    ('mag_d', '6 mm', 'Magnet diameter (6 x 3 mm N52 disc)'),
    ('mag_t', '3 mm', 'Magnet thickness'),
]


def define():
    for n, e, cm in PARAMS5:
        param(n, e, cm)


def smoked():
    a = appearance('SB Smoked PETG', 'Glass (Grey)')
    for pid, val in (('transparent_color', (150, 155, 165)), ('transparent_distance', 30.0), ('surface_roughness', 0.08)):
        p = a.appearanceProperties.itemById(pid)
        if p is not None:
            p.value = adsk.core.Color.create(val[0], val[1], val[2], 255) if isinstance(val, tuple) else val
    return a


def master_ring(c):
    """Walls master: a 2.4 mm rounded-rectangle ring (outer corner_r) extruded from the body bottom
    to the wall seam. Light prism geometry: no full-body fillet or shell op."""
    sk = sketch(c, 'z', 'wall ring')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': 'body_w', 'y': 'body_d'})
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': 'body_w - 2*pwall', 'y': 'body_d - 2*pwall'})
    f = extrude(c, sk, 'body_z0', 'wall_top - body_z0', which='outer', name='wall master')
    b = f.bodies.item(0)
    fillet(c, edges_where(b, lambda e: is_axis_line(e, 'z') and max(abs(e.startVertex.geometry.x), abs(e.startVertex.geometry.y)) * 10 > mm('shell_x - pwall') + 0.5), 'corner_r')
    fillet(c, edges_where(b, lambda e: is_axis_line(e, 'z')), 'corner_r - pwall')
    return b


def master_cap(c):
    """Top master: a small rounded cap (wall seam to the top), shelled open at the bottom."""
    b = B(c, 'cap master', '0 mm', '0 mm', 'wall_top', 'body_w', 'body_d', 'body_top - wall_top', 'PET Plastic')
    fillet(c, edges_where(b, lambda e: is_axis_line(e, 'z')), 'corner_r')
    top = zfaces(b, True)
    col = OC.create()
    for e in top.edges:
        col.add(e)
    fillet(c, col, 'top_r')
    bot = OC.create()
    bot.add(zfaces(b, False))
    si = c.features.shellFeatures.createInput(bot, False)
    si.insideThickness = V.createByString('pwall')
    c.features.shellFeatures.add(si)
    return b


def piece(c, src, name, x0, x1, y0, y1, z0, z1, look):
    cp = c.features.copyPasteBodies.add(src).bodies.item(0)
    nm = cp.name
    B(c, 'region ' + name, '((%s) + (%s))/2' % (x0, x1), '((%s) + (%s))/2' % (y0, y1), z0,
      '(%s) - (%s)' % (x1, x0), '(%s) - (%s)' % (y1, y0), '(%s) - (%s)' % (z1, z0), op=INTER, bodies=[cp])
    cp = [b for b in c.bRepBodies if b.name == nm][0]
    cp.name = name
    finish(cp, 'PET Plastic', look)
    return cp


def shell():
    look = smoked()
    c = fresh('Shell (printed smoked PETG)')
    m = master_ring(c)
    cap = master_cap(c)
    g = 'seam_gap/2'
    BIG = '150 mm'
    Z0, ZT = 'body_z0 - 1 mm', 'body_top + 1 mm'
    WT = 'wall_top - %s' % g
    Ys = 'wall_seam_y'
    P_ = {}
    P_['top F'] = piece(c, cap, 'top half front', '-' + BIG, BIG, 'top_seam_y + %s' % g, BIG, 'wall_top + %s' % g, ZT, look)
    P_['top B'] = piece(c, cap, 'top half rear', '-' + BIG, BIG, '-' + BIG, 'top_seam_y - %s' % g, 'wall_top + %s' % g, ZT, look)
    P_['front'] = piece(c, m, 'front wall', '-' + BIG, BIG, '(%s) + %s' % (Ys, g), BIG, Z0, WT, look)
    P_['rear'] = piece(c, m, 'rear wall', '-' + BIG, BIG, '-' + BIG, '-(%s) - %s' % (Ys, g), Z0, WT, look)
    P_['right'] = piece(c, m, 'side wall right', '0 mm', BIG, '-(%s) + %s' % (Ys, g), '(%s) - %s' % (Ys, g), Z0, WT, look)
    P_['left'] = piece(c, m, 'side wall left', '-' + BIG, '0 mm', '-(%s) + %s' % (Ys, g), '(%s) - %s' % (Ys, g), Z0, WT, look)
    P_['door'] = piece(c, m, 'battery door', '-door_hw + %s' % g, 'door_hw - %s' % g, '-' + BIG, '-(%s) - %s' % (Ys, g), Z0, 'door_top - %s' % g, look)
    B(c, 'door opening', '0 mm', '-shell_y', Z0, '2*door_hw + seam_gap', '2*corner_r', '(door_top + %s) - (%s)' % (g, Z0), op=CUT, bodies=[P_['rear']])
    c.features.removeFeatures.add(m)
    c.features.removeFeatures.add(cap)
    log('pieces', len(P_))
    return c, P_


def openings(c, P_):
    tz = 'body_top - pwall - 1 mm'
    # front half: plinth notch open to the seam (slides forward off the plinth);
    # rear half: pod notch open to the seam (slides backward off the pod)
    B(c, 'plinth notch', '0 mm', '(top_seam_y + pan_y + plinth_s/2 + 0.5 mm)/2', tz, 'plinth_s + 1 mm',
      '(pan_y + plinth_s/2 + 0.5 mm) - top_seam_y + 1 mm', 'pwall + 3 mm', op=CUT, bodies=[P_['top F']])
    B(c, 'pod notch', 'lidar_x', '(top_seam_y + lidar_y - pod_d/2 - 0.5 mm)/2', tz, 'pod_w + 1 mm',
      'top_seam_y - (lidar_y - pod_d/2 - 0.5 mm) + 1 mm', 'pwall + 3 mm', op=CUT, bodies=[P_['top B']])
    for j in range(7):
        B(c, 'chimney vent', '%d*18 mm' % (j - 3), '(spine_y + 6 mm + shell_y - top_r - 2 mm)/2', tz, '5 mm',
          '(shell_y - top_r - 2 mm) - (spine_y + 6 mm)', 'pwall + 3 mm', op=CUT, bodies=[P_['top F']])
    f = P_['front']
    # LED bar slot (bezel + diffuser added in s4), intake slots above the front motors, HC-SR04P knock-outs
    B(c, 'LED bar slot', '0 mm', 'shell_y - pwall/2', 'bar_z - 6 mm', 'bar_w', 'pwall + 2 mm', '12 mm', op=CUT, bodies=[f])
    for j in range(-4, 5):
        B(c, 'intake slot', '%d*16 mm' % j, 'shell_y - pwall/2', 'plate_top + 50 mm', '4 mm', 'pwall + 2 mm', '24 mm', op=CUT, bodies=[f])
    for tx in (-1, 1):
        C(c, 'HC-SR04P knock-out', 'y', '%d*13 mm' % tx, 'shell_y - pwall/2 - 0.3 mm', 'plate_top + 24 mm', '16.6 mm', 'pwall - 0.6 mm', op=CUT, bodies=[f])
    # side walls: U-slots over the wheel shafts so the walls lift off
    for k, sx in (('right', 1), ('left', -1)):
        for sy in (1, -1):
            B(c, 'shaft U-slot', S(sx, 'shell_x - pwall/2'), S(sy, 'wheel_y'), 'body_z0 - 1 mm', 'pwall + 2 mm', '14 mm', 'axle_z + 8 mm - body_z0 + 1 mm',
              op=CUT, bodies=[P_[k]])
    # rear: speaker grille, loop key hole; door: charge jack hole, finger pull
    r = P_['rear']
    for ix in range(-3, 4):
        for iz in range(-3, 4):
            if ix * ix + iz * iz > 10:
                continue
            C(c, 'grille hole', 'y', '-45 mm + %d*4.5 mm' % ix, '-(shell_y - pwall/2)', 'body_top - 70 mm + %d*4.5 mm' % iz, '3 mm', 'pwall + 2 mm', op=CUT, bodies=[r])
    B(c, 'loop key hole', '50 mm', '-(shell_y - pwall/2)', 'body_top - 45 mm', '17 mm', 'pwall + 2 mm', '10 mm', op=CUT, bodies=[r])
    C(c, 'charge jack hole', 'y', '0 mm', '-(shell_y - pwall/2)', 'body_z0 + 82 mm', '12 mm', 'pwall + 2 mm', op=CUT, bodies=[P_['door']])
    B(c, 'finger pull', '0 mm', '-shell_y', 'body_z0 + 20 mm', '30 mm', '2 mm', '10 mm', op=CUT, bodies=[P_['door']])
    for xx in ('-12 mm', '12 mm'):
        C(c, 'M3 door screw', 'y', xx, '-(shell_y - pwall/2)', 'body_z0 + 60 mm', '3.4 mm', 'pwall + 2 mm', op=CUT, bodies=[P_['door']])
    log('openings ok')


def magnet_pair(c, body, x, y, z, axis, sign, frame_base, tag):
    """Magnet boss joined to the panel + magnet, and a printed frame block + magnet.
    (x,y,z) = panel inner-surface point; axis/sign = from the panel into the robot;
    frame_base = distance from the panel inner surface to where the frame block ends."""
    def at(d):
        p = {'x': x, 'y': y, 'z': z}
        p[axis] = '(%s) + %d*(%s)' % (p[axis], sign, d)
        return p
    boss = cyl(c, 'boss', axis, at('2 mm'), 'mag_d + 4 mm', '4 mm')
    combine(c, body, [boss], JOIN)
    cyl(c, 'magnet pocket', axis, at('2.5 mm'), 'mag_d + 0.2 mm', 'mag_t + 0.01 mm', op=CUT, bodies=[body])
    finish(cyl(c, 'magnet 6x3 (panel) %s' % tag, axis, at('2.5 mm'), 'mag_d', 'mag_t'), 'Steel', 'Chrome')
    blk = cyl(c, 'magnet block (printed) %s' % tag, axis, at('4.2 mm + ((%s) - 4.2 mm)/2' % frame_base), 'mag_d + 6 mm', '(%s) - 4.2 mm' % frame_base)
    finish(blk, 'PET Plastic', BLACK)
    cyl(c, 'magnet pocket', axis, at('4.2 mm + mag_t/2'), 'mag_d + 0.2 mm', 'mag_t + 0.01 mm', op=CUT, bodies=[blk])
    finish(cyl(c, 'magnet 6x3 (frame) %s' % tag, axis, at('4.2 mm + mag_t/2'), 'mag_d', 'mag_t'), 'Steel', 'Chrome')


def tab_clip(c, body, x, y, axis, sign, tag, w='12 mm'):
    """Drop-in tab on the wall's inner face + a printed clip (open-top pocket) on the plate edge."""
    def pt(d):
        p = {'x': x, 'y': y}
        p[axis] = '(%s) + %d*(%s)' % (p[axis], sign, d)
        return p
    tp = pt('2.5 mm')
    other = 'y' if axis == 'x' else 'x'
    sz = {axis: '5 mm', other: w}
    t = box(c, 'tab', {'x': tp['x'], 'y': tp['y'], 'z': 'plate_top + 8 mm'}, {'x': sz['x'], 'y': sz['y'], 'z': '10 mm'})
    combine(c, body, [t], JOIN)
    cp = pt('4.5 mm')
    cs = {axis: '9 mm', other: '(%s) + 4 mm' % w}
    clip = box(c, 'clip', {'x': cp['x'], 'y': cp['y'], 'z': 'plate_top + 5 mm'}, {'x': cs['x'], 'y': cs['y'], 'z': '10 mm'})
    ps = {axis: '5.6 mm', other: '(%s) + 0.6 mm' % w}
    box(c, 'pocket', {'x': tp['x'], 'y': tp['y'], 'z': 'plate_top + 8 mm'}, {'x': ps['x'], 'y': ps['y'], 'z': '10.4 mm'}, op=CUT, bodies=[clip])
    clip.name = 'panel clip (printed) %s' % tag
    finish(clip, 'PET Plastic', BLACK)


def retention(c, P_):
    lip = 'body_top - pwall'
    fd = '(body_top - pwall) - top_deck_top'
    for k, x, y in (('top F', '-70 mm', '72 mm'), ('top F', '70 mm', '72 mm'), ('top F', '-70 mm', '5 mm'), ('top F', '70 mm', '5 mm'),
                    ('top B', '30 mm', '-60 mm'), ('top B', '70 mm', '-60 mm')):
        magnet_pair(c, P_[k], x, y, lip, 'z', -1, fd, k)
    mz = 'top_deck_z - 6 mm'
    for k, ax, sg, offs, toffs, tw in (('front', 'y', 1, ('-60 mm', '60 mm'), ('-26 mm', '26 mm'), '5 mm'),
                                        ('rear', 'y', -1, ('-60 mm', '20 mm'), ('-28.4 mm', '28.4 mm'), '2.6 mm'),
                                        ('right', 'x', 1, ('-30 mm', '30 mm'), ('-30 mm', '30 mm'), '12 mm'),
                                        ('left', 'x', -1, ('-30 mm', '30 mm'), ('-30 mm', '30 mm'), '12 mm')):
        for off, toff in zip(offs, toffs):
            if ax == 'y':
                magnet_pair(c, P_[k], off, S(sg, 'shell_y - pwall'), mz, 'y', -sg, '16 mm', k)
                tab_clip(c, P_[k], toff, S(sg, 'shell_y - pwall'), 'y', -sg, k, tw)
            else:
                magnet_pair(c, P_[k], S(sg, 'shell_x - pwall'), off, mz, 'x', -sg, '14 mm', k)
                tab_clip(c, P_[k], S(sg, 'shell_x - pwall'), toff, 'x', -sg, k, tw)
    log('retention ok')


def main(parts=('shell', 'open', 'ret')):
    define()
    c, P_ = shell()
    if 'open' in parts:
        openings(c, P_)
    if 'ret' in parts:
        retention(c, P_)
    done()
