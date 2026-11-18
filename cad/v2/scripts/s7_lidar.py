# Stage 7: lidar pod + LDROBOT LD19, with the two options Adam wants to compare.
#   lidar_rise = 0 mm   -> option A: low rounded pod at the rear left; the LD19 sits inside on a shelf
#                          and its scan plane (301 mm) passes between the plinth top and the turret, so
#                          only the 30 mm gimbal knuckle is in the plane (~19 deg, masked in software).
#   lidar_rise = 166 mm -> option B: the same pod as a base, plus a 20 mm aluminium mast from the pod
#                          shelf at (mast_x, mast_y), outside the head's sweep circle (~100 mm round the
#                          pan axis), carrying the LD19 above the head's highest swept point (434 mm):
#                          scan plane 467 mm, nothing of the robot in it.
# The LD19 position and height follow the parameters directly; the mast is built when lidar_rise > 0
# (switch the option by changing lidar_rise and rerunning this stage, about 30 s).

PARAMS7 = [
    ('lidar_rise', '0 mm', 'Lidar option: 0 mm = A (low pod, ~19 deg masked), 166 mm = B (mast, plane above the head)'),
    ('mast_x', '-70 mm', 'Option B mast X (outside the head sweep circle, inside the pod)'),
    ('mast_y', '-72 mm', 'Option B mast Y'),
    ('pod_ld_z', 'body_top + plinth_h + knuckle_h/2 - scan_h', 'Pod shelf top Z (LD19 ears in option A)'),
    ('pod_top', 'pod_ld_z + scan_h - 8 mm', 'Pod rim Z (5 mm under the LD19 window band in option A)'),
    ('ld_x', 'lidar_x + (mast_x - lidar_x)*(lidar_rise/166 mm)', 'LD19 centre X (follows the option)'),
    ('ld_y', 'lidar_y + (mast_y - lidar_y)*(lidar_rise/166 mm)', 'LD19 centre Y (follows the option)'),
    ('ld_z', 'scan_z - scan_h', 'LD19 ear underside Z'),
]


def pod():
    for n, e, cm in PARAMS7:
        param(n, e, cm)
    param('scan_z', 'body_top + plinth_h + knuckle_h/2 + lidar_rise', 'Lidar scan plane Z (option A 301 mm, B 467 mm)')
    opt_b = mm('lidar_rise') > 0.5
    smoked = design.appearances.itemByName('SB Smoked PETG')
    c = fresh('Lidar pod (printed)')
    b = RB(c, 'pod', 'lidar_x', 'lidar_y', 'top_deck_top', 'pod_w', 'pod_d', 'pod_top - top_deck_top', '16 mm', 'PET Plastic', smoked)
    top = zfaces(b, True)
    col = OC.create()
    for e in top.edges:
        col.add(e)
    fillet(c, col, '6 mm')
    bot = OC.create()
    bot.add(zfaces(b, False))
    si = c.features.shellFeatures.createInput(bot, False)
    si.insideThickness = V.createByString('pwall')
    c.features.shellFeatures.add(si)
    if not opt_b:
        B(c, 'LD19 opening', 'lidar_x', 'lidar_y', 'pod_top - 4 mm', '40 mm', '40 mm', '6 mm', op=CUT, bodies=[b])
    else:
        C(c, 'mast hole', 'z', 'mast_x', 'mast_y', 'pod_top - 2 mm', '20.6 mm', '6 mm', op=CUT, bodies=[b])
    shelf = B(c, 'LD19 shelf', 'lidar_x', 'lidar_y', 'top_deck_top', 'pod_w - 2*pwall - 0.1 mm', 'pod_d - 2*pwall - 0.1 mm', 'pod_ld_z - top_deck_top')
    B(c, 'shelf opening', 'lidar_x', 'lidar_y', 'top_deck_top - 1 mm', '24 mm', '24 mm', 'pod_ld_z - top_deck_top + 2 mm', op=CUT, bodies=[shelf])
    join(c, b, [shelf], 'lidar pod (printed, smoked)')
    for (hx, hy) in ((-24, -22), (24, -22), (-24, 22), (24, 22)):
        C(c, 'M3 deck bolt', 'z', '(lidar_x) + %d mm' % hx, '(lidar_y) + %d mm' % hy, '(top_deck_top + pod_ld_z)/2', '3.4 mm', 'pod_ld_z - top_deck_top + 1 mm', op=CUT, bodies=[b])
    if not opt_b:
        for (hx, hy) in (('-23.4 mm', '16 mm'), ('23.4 mm', '16 mm'), ('0 mm', '16 mm - 31.92 mm')):
            C(c, 'M2.5 LD19', 'z', '(lidar_x) + (%s)' % hx, '(lidar_y) + %s' % hy, 'pod_ld_z - 2 mm', '2.7 mm', '5 mm', op=CUT, bodies=[b])
    for k in range(6):
        B(c, 'front vent', '(lidar_x) - 17.5 mm + %d*7 mm' % k, '(lidar_y) + pod_d/2', 'body_top + 1 mm', '3.5 mm', '6 mm', 'pod_top - body_top - 6 mm', op=CUT, bodies=[b])
    for sx in (1, -1):
        for k in range(3):
            B(c, 'side vent', '(lidar_x) + %s' % S(sx, 'pod_w/2'), '(lidar_y) - 10 mm + %d*10 mm' % k, 'body_top + 1 mm', '6 mm', '4 mm', 'pod_top - body_top - 6 mm', op=CUT, bodies=[b])
    if opt_b:
        m = fresh('Lidar mast (option B)')
        ring(m, 'mast 20x1.5 aluminium tube', 'z', 'mast_x', 'mast_y', '(pod_ld_z + 0.5 mm + ld_z - 3 mm)/2', '20 mm', '17 mm',
             '(ld_z - 3 mm) - (pod_ld_z + 0.5 mm)', 'Aluminum 6061', 'Chrome - Black')
        base = C(m, 'mast foot (printed)', 'z', 'mast_x', 'mast_y', 'pod_ld_z + 4 mm', '24 mm', '8 mm', 'PET Plastic', BLACK)
        C(m, 'mast socket', 'z', 'mast_x', 'mast_y', 'pod_ld_z + 4.5 mm', '20.2 mm', '8 mm', op=CUT, bodies=[base])
        tp = RB(m, 'LD19 top plate (printed)', 'ld_x', 'ld_y', 'ld_z - 3 mm', '56 mm', '48 mm', '3 mm', '6 mm', 'PET Plastic', BLACK)
        C(m, 'mast plug (printed)', 'z', 'mast_x', 'mast_y', 'ld_z - 3 mm - 6 mm', '17 mm', '12 mm', 'PET Plastic', BLACK)
    l = fresh('Lidar LDROBOT LD19')
    ears = B(l, 'LD19 ear plate', 'ld_x', 'ld_y', 'ld_z', '54 mm', '46.29 mm', '2.5 mm', 'ABS Plastic', BLACK)
    fillet(l, edges_where(ears, lambda e: is_axis_line(e, 'z')), '6 mm')
    for (hx, hy) in (('-23.4 mm', '16 mm'), ('23.4 mm', '16 mm'), ('0 mm', '16 mm - 31.92 mm')):
        C(l, 'ear hole', 'z', '(ld_x) + (%s)' % hx, '(ld_y) + %s' % hy, 'ld_z + 1.25 mm', '2.5 mm', '3 mm', op=CUT, bodies=[ears])
    RB(l, 'LD19 body', 'ld_x', 'ld_y', 'ld_z + 2.5 mm', '38.59 mm', '38.59 mm', '34.8 mm - 12.6 mm - 2.5 mm', '6 mm', 'ABS Plastic', BLACK)
    C(l, 'LD19 rotating head', 'z', 'ld_x', 'ld_y', 'ld_z + 34.8 mm - 6.3 mm', '35.29 mm', '12.6 mm', 'ABS Plastic', GLOSSB)
    C(l, 'LD19 window band (scan plane)', 'z', 'ld_x', 'ld_y', 'scan_z', '35.4 mm', '6 mm', 'Glass', 'Glass (Grey)')
    log('lidar ok, option', 'B' if opt_b else 'A', 'scan z =', mm('scan_z'), 'LD19 at', mm('ld_x'), mm('ld_y'), mm('ld_z'))
    done()


def set_option(rise_mm):
    param('lidar_rise', '%g mm' % rise_mm, PARAMS7[0][2])
    pod()


def main():
    pod()
