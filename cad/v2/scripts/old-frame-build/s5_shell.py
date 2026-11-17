# Stage 5: the printed smoked-PETG shell.
# One rounded solid (vertical corners corner_r, top edges top_r) is shelled to pwall and then
# cut into pieces that each fit a 256 mm bed, with real seam gaps (seam_gap):
#   2 top halves (split at x = 0, notched round the plinth and the lidar pod),
#   4 upper walls with a rounded top lip, 4 corner posts, 4 lower skirts
#   (the right skirt is the battery door).
# Retention: 6 x 3 mm magnet pairs at the tops, drop-in tabs at the wall/skirt bottoms.

PARAMS5 = [
    ('seam_gap', '0.4 mm', 'Gap between shell pieces'),
    ('seam_a', 'shell_x - corner_r', 'Seam line: corners and top centre start here'),
    ('skirt_x', 'wheel_x_out - wheel_w - 4 mm', 'Front/rear skirt half-width (clears the wheels)'),
    ('skirt_y', 'wheel_y - wheel_d/2 - 4 mm', 'Side skirt half-width (clears the wheels)'),
    ('plinth_d', '64 mm', 'Head joint plinth diameter (holds 2x 6805)'),
    ('pod_w', '72 mm', 'Lidar pod width X'),
    ('pod_d', '64 mm', 'Lidar pod depth Y'),
    ('mag_d', '6 mm', 'Magnet diameter (6 x 3 mm N52 disc)'),
    ('mag_t', '3 mm', 'Magnet thickness'),
]


def define():
    for n, e, cm in PARAMS5:
        param(n, e, cm)


def smoked():
    a = appearance('SB Smoked PETG', 'Glass (Grey)')
    for pid, val in (('transparent_color', (120, 124, 132)), ('transparent_distance', 4.0), ('surface_roughness', 0.15)):
        p = a.appearanceProperties.itemById(pid)
        if p is None:
            continue
        if isinstance(val, tuple):
            p.value = adsk.core.Color.create(val[0], val[1], val[2], 255)
        else:
            p.value = val
    return a


def master(c):
    b = B(c, 'shell master', '0 mm', '0 mm', 'plate_z', 'body_w', 'body_d', 'body_top - plate_z', 'PET Plastic')
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
    B(c, 'region ' + name, '((%s) + (%s))/2' % (x0, x1), '((%s) + (%s))/2' % (y0, y1), z0,
      '(%s) - (%s)' % (x1, x0), '(%s) - (%s)' % (y1, y0), '(%s) - (%s)' % (z1, z0), op=INTER, bodies=[cp])
    cp = [b for b in c.bRepBodies if b.name == cp.name][0]
    cp.name = name
    finish(cp, 'PET Plastic', look)
    return cp


def shell():
    look = smoked()
    c = fresh('Shell (printed smoked PETG)')
    m = master(c)
    g = 'seam_gap/2'
    A = 'seam_a'
    Z0, ZS, ZT = 'plate_z - 1 mm', 'fender_z', 'body_top + 1 mm'
    out = {}
    # top halves
    out['top L'] = piece(c, m, 'top half left', '-(%s) + %s' % (A, g), '-(%s)' % g, '-(%s) + %s' % (A, g), '(%s) - %s' % (A, g), 'body_top - 12 mm', ZT, look)
    out['top R'] = piece(c, m, 'top half right', g, '(%s) - %s' % (A, g), '-(%s) + %s' % (A, g), '(%s) - %s' % (A, g), 'body_top - 12 mm', ZT, look)
    # upper walls (with the rounded top lip)
    for tag, sy in (('front', 1), ('rear', -1)):
        y0, y1 = ('(%s) + %s' % (A, g), 'shell_y + 1 mm') if sy > 0 else ('-shell_y - 1 mm', '-(%s) - %s' % (A, g))
        out['wall ' + tag] = piece(c, m, 'upper wall %s' % tag, '-(%s) + %s' % (A, g), '(%s) - %s' % (A, g), y0, y1, '(%s) + %s' % (ZS, g), ZT, look)
    for tag, sx in (('right', 1), ('left', -1)):
        x0, x1 = ('(%s) + %s' % (A, g), 'shell_x + 1 mm') if sx > 0 else ('-shell_x - 1 mm', '-(%s) - %s' % (A, g))
        out['wall ' + tag] = piece(c, m, 'upper wall %s' % tag, x0, x1, '-(%s) + %s' % (A, g), '(%s) - %s' % (A, g), '(%s) + %s' % (ZS, g), ZT, look)
    # corner posts
    for tag, sx, sy in (('FR', 1, 1), ('FL', -1, 1), ('RR', 1, -1), ('RL', -1, -1)):
        x0, x1 = ('(%s) + %s' % (A, g), 'shell_x + 1 mm') if sx > 0 else ('-shell_x - 1 mm', '-(%s) - %s' % (A, g))
        y0, y1 = ('(%s) + %s' % (A, g), 'shell_y + 1 mm') if sy > 0 else ('-shell_y - 1 mm', '-(%s) - %s' % (A, g))
        out['corner ' + tag] = piece(c, m, 'corner post %s' % tag, x0, x1, y0, y1, '(%s) + %s' % (ZS, g), ZT, look)
    # lower skirts between the wheels
    for tag, sy in (('front', 1), ('rear', -1)):
        y0, y1 = ('(%s) + %s' % (A, g), 'shell_y + 1 mm') if sy > 0 else ('-shell_y - 1 mm', '-(%s) - %s' % (A, g))
        out['skirt ' + tag] = piece(c, m, 'lower skirt %s' % tag, '-skirt_x', 'skirt_x', y0, y1, Z0, '(%s) - %s' % (ZS, g), look)
    for tag, sx in (('right', 1), ('left', -1)):
        x0, x1 = ('(%s) + %s' % (A, g), 'shell_x + 1 mm') if sx > 0 else ('-shell_x - 1 mm', '-(%s) - %s' % (A, g))
        nm = 'lower skirt right = battery door' if sx > 0 else 'lower skirt left'
        out['skirt ' + tag] = piece(c, m, nm, x0, x1, '-skirt_y', 'skirt_y', Z0, '(%s) - %s' % (ZS, g), look)
    # drop the master
    c.features.removeFeatures.add(m)
    log('pieces', len(out))
    return c, out


def openings(c, P_):
    T = 'body_top'
    tz = '%s - pwall - 1 mm' % T
    # top halves: plinth hole, pod hole, chimney vents
    for k in ('top L', 'top R'):
        b = P_[k]
        C(c, 'plinth hole', 'z', '0 mm', 'pan_y', '%s + 0.5 mm' % tz, 'plinth_d + 1 mm', 'pwall + 3 mm', op=CUT, bodies=[b])
        B(c, 'pod hole', '0 mm', 'lidar_y', tz, 'pod_w + 1 mm', 'pod_d + 1 mm', 'pwall + 3 mm', op=CUT, bodies=[b])
        for j in range(9):
            if (j - 4) * (1 if k == 'top R' else -1) < 0:
                continue  # that vent is over the other half
            B(c, 'vent', '%d*22 mm' % (j - 4), '(vent_y0 + vent_y1)/2', tz, '6 mm', 'vent_y1 - vent_y0', 'pwall + 3 mm', op=CUT, bodies=[b])
    # front wall: mic pinhole; rear wall: loop key; left wall: speaker grille
    C(c, 'mic hole', 'y', '36 mm', 'shell_y - pwall/2', 'cpx_z + 12 mm', '2 mm', 'pwall + 2 mm', op=CUT, bodies=[P_['wall front']])
    B(c, 'loop key hole', 'key_x', '-(shell_y - pwall/2)', 'key_z - 5 mm', '17 mm', 'pwall + 2 mm', '10 mm', op=CUT, bodies=[P_['wall rear']])
    for iy in range(-3, 4):
        for iz in range(-3, 4):
            if iy * iy + iz * iz > 10:
                continue
            C(c, 'grille hole', 'x', '-(shell_x - pwall/2)', '-20 mm + %d*4.5 mm' % iy, 'l1_top + 34 mm + %d*4.5 mm' % iz, '3 mm', 'pwall + 2 mm',
              op=CUT, bodies=[P_['wall left']])
    # skirts: charge jack hole, intake slots, HC-SR04P knock-outs (0.6 mm skin left)
    C(c, 'charge jack hole', 'y', '0 mm', '-(shell_y - pwall/2)', 'plate_top + 26 mm', '12 mm', 'pwall + 2 mm', op=CUT, bodies=[P_['skirt rear']])
    for tx in (-1, 1):
        C(c, 'HC-SR04P knock-out', 'y', '%d*13 mm' % tx, 'shell_y - pwall/2 - 0.3 mm', 'plate_top + 24 mm', '16.6 mm', 'pwall - 0.6 mm',
          op=CUT, bodies=[P_['skirt front']])
    for tag in ('skirt front', 'skirt rear'):
        sy = 1 if 'front' in tag else -1
        for j in range(-5, 6):
            if abs(j) < 2:
                continue
            B(c, 'intake slot', '%d*14 mm' % j, S(sy, 'shell_y - pwall/2'), 'plate_top + 34 mm', '5 mm', 'pwall + 2 mm', '36 mm', op=CUT, bodies=[P_[tag]])
    B(c, 'finger pull', 'shell_x', '0 mm', 'plate_top + 50 mm', '2 mm', '40 mm', '12 mm', op=CUT, bodies=[P_['skirt right']])
    for yy in ('-20 mm', '20 mm'):
        C(c, 'M3 door screw', 'x', 'shell_x - pwall/2', yy, 'plate_top + 40 mm', '3.4 mm', 'pwall + 2 mm', op=CUT, bodies=[P_['skirt right']])
    log('openings ok')


def magnet_pair(c, body, x, y, z, axis, sign, frame_base, tag):
    """Magnet boss on the panel (joined) + magnet, and a printed frame block + magnet.
    (x,y,z) = panel inner-surface point; axis/sign = direction from panel into the robot.
    frame_base = distance from the panel inner surface to the frame surface the block sits on."""
    def at(d):
        p = {'x': x, 'y': y, 'z': z}
        p[axis] = '(%s) + %d*(%s)' % (p[axis], sign, d)
        return p
    bp = at('2 mm')
    boss = cyl(c, 'boss', axis, bp, 'mag_d + 4 mm', '4 mm')
    combine(c, body, [boss], JOIN)
    cp = at('2.5 mm')
    cyl(c, 'magnet pocket', axis, cp, 'mag_d + 0.2 mm', 'mag_t + 0.01 mm', op=CUT, bodies=[body])
    m1 = cyl(c, 'magnet 6x3 (panel) %s' % tag, axis, at('2.5 mm'), 'mag_d', 'mag_t')
    finish(m1, 'Steel', 'Chrome')
    fb = at('4.2 mm + ((%s) - 4.2 mm)/2' % frame_base)
    blk = cyl(c, 'magnet block (printed) %s' % tag, axis, fb, 'mag_d + 6 mm', '(%s) - 4.2 mm' % frame_base)
    finish(blk, 'PET Plastic', BLACK)
    cyl(c, 'magnet pocket', axis, at('4.2 mm + mag_t/2'), 'mag_d + 0.2 mm', 'mag_t + 0.01 mm', op=CUT, bodies=[blk])
    m2 = cyl(c, 'magnet 6x3 (frame) %s' % tag, axis, at('4.2 mm + mag_t/2'), 'mag_d', 'mag_t')
    finish(m2, 'Steel', 'Chrome')


def tab_clip(c, body, x, y, axis, sign, tag):
    """Drop-in tab on the wall's inner face + a printed clip with an open-top pocket on the L1 deck."""
    def pt(d):
        p = {'x': x, 'y': y}
        p[axis] = '(%s) + %d*(%s)' % (p[axis], sign, d)
        return p
    tp = pt('2.5 mm')
    sz = {'x': '14 mm', 'y': '14 mm'}
    sz[axis] = '5 mm'
    t = box(c, 'tab', {'x': tp['x'], 'y': tp['y'], 'z': 'l1_top + 7 mm'}, {'x': sz['x'], 'y': sz['y'], 'z': '10 mm'})
    combine(c, body, [t], JOIN)
    cp = pt('4 mm')
    cs = {'x': '22 mm', 'y': '22 mm'}
    cs[axis] = '8 mm'
    clip = box(c, 'clip', {'x': cp['x'], 'y': cp['y'], 'z': 'l1_top + 5 mm'}, {'x': cs['x'], 'y': cs['y'], 'z': '10 mm'})
    ps = {'x': '14.6 mm', 'y': '14.6 mm'}
    ps[axis] = '5.6 mm'
    box(c, 'pocket', {'x': tp['x'], 'y': tp['y'], 'z': 'l1_top + 7 mm'}, {'x': ps['x'], 'y': ps['y'], 'z': '10.4 mm'}, op=CUT, bodies=[clip])
    clip.name = 'panel clip (printed) %s' % tag
    finish(clip, 'PET Plastic', BLACK)


def hook(c, body, x, y, axis, sign):
    """Hook on a skirt's inner face that tucks under the chassis plate edge."""
    p = {'x': x, 'y': y}
    p[axis] = '(%s) + %d*3.5 mm' % (p[axis], sign)
    sz = {'x': '20 mm', 'y': '20 mm'}
    sz[axis] = '7 mm'
    h = box(c, 'hook', {'x': p['x'], 'y': p['y'], 'z': 'plate_z - 3 mm'}, {'x': sz['x'], 'y': sz['y'], 'z': '4 mm'})
    combine(c, body, [h], JOIN)


def retention(c, P_):
    lip = 'body_top - pwall'                    # underside of the top surface
    fd = '(body_top - pwall) - top_deck_top'   # panel underside to top deck top
    # top halves: 3 magnets each, down onto the top deck
    for k, sx in (('top L', -1), ('top R', 1)):
        for (x, y) in (('%d*60 mm' % sx, '-100 mm'), ('%d*95 mm' % sx, '0 mm'), ('%d*60 mm' % sx, '85 mm')):
            magnet_pair(c, P_[k], x, y, lip, 'z', -1, fd, k)
    # upper walls: 2 magnets each on the lip, down onto the top deck; 2 drop-in tabs at the bottom
    for k, ax, sg in (('wall front', 'y', 1), ('wall rear', 'y', -1), ('wall right', 'x', 1), ('wall left', 'x', -1)):
        for off in ('-70 mm', '70 mm'):
            if ax == 'y':
                magnet_pair(c, P_[k], off, S(sg, 'seam_a + 8 mm'), lip, 'z', -1, fd, k)
                tab_clip(c, P_[k], off, S(sg, 'shell_y - pwall'), 'y', -sg, k)
            else:
                magnet_pair(c, P_[k], S(sg, 'seam_a + 8 mm'), off, lip, 'z', -1, fd, k)
                tab_clip(c, P_[k], S(sg, 'shell_x - pwall'), off, 'x', -sg, k)
    # corner posts: 2 magnets each, pointing at the corner tie rod (printed clamp blocks)
    for k, sx, sy in (('corner FR', 1, 1), ('corner FL', -1, 1), ('corner RR', 1, -1), ('corner RL', -1, -1)):
        for z in ('fender_z + 40 mm', 'top_deck_z - 30 mm'):
            magnet_pair(c, P_[k], S(sx, 'shell_x - pwall'), S(sy, 'seam_a + 9 mm'), z, 'x', -sx,
                        '(shell_x - pwall) - (rod_xy + 5 mm)', k)
    # lower skirts: 2 magnets at the top (blocks under the L1 deck edge), hooks under the plate edge.
    # The right skirt is the battery door: 2x M3 into the sled end plate instead.
    for k, ax, sg in (('skirt front', 'y', 1), ('skirt rear', 'y', -1), ('skirt left', 'x', -1)):
        offs = ('-40 mm', '40 mm') if ax == 'y' else ('-24 mm', '24 mm')
        hoffs = ('-60 mm', '60 mm') if ax == 'y' else ('-30 mm', '30 mm')
        for off, ho in zip(offs, hoffs):
            if ax == 'y':
                magnet_pair(c, P_[k], off, S(sg, 'shell_y - pwall'), 'fender_z - 6 mm', 'y', -sg, '16 mm', k)
                hook(c, P_[k], ho, S(sg, 'shell_y - pwall'), 'y', -sg)
            else:
                magnet_pair(c, P_[k], S(sg, 'shell_x - pwall'), off, 'fender_z - 6 mm', 'x', -sg, '16 mm', k)
                hook(c, P_[k], S(sg, 'shell_x - pwall'), ho, 'x', -sg)
    log('retention ok')


def main(parts=('shell', 'open', 'ret')):
    define()
    c, P_ = shell()
    if 'open' in parts:
        openings(c, P_)
    if 'ret' in parts:
        retention(c, P_)
    done()
