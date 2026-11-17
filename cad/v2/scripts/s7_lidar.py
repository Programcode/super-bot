# Stage 7: lidar pod + LDROBOT LD19 at the top rear.
# The pod is a rounded, vented printed box bolted to the top deck through a hole in the shell.
# The LD19 sits on a shelf inside it, so only its rotating cap shows above the pod, like the
# round cap in the target photo. The scan plane (scan_z) passes between the plinth top and the
# turret bottom; the pod rim stays 5 mm under the LD19 window band.

PARAMS7 = [
    ('ld_z', 'scan_z - scan_h', 'LD19 ear underside Z'),
    ('pod_top', 'scan_z - 8 mm', 'Pod rim Z (5 mm under the LD19 window band)'),
]


def pod():
    for n, e, cm in PARAMS7:
        param(n, e, cm)
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
    B(c, 'LD19 opening', 'lidar_x', 'lidar_y', 'pod_top - 4 mm', '40 mm', '40 mm', '6 mm', op=CUT, bodies=[b])
    shelf = B(c, 'LD19 shelf', 'lidar_x', 'lidar_y', 'top_deck_top', 'pod_w - 2*pwall - 0.1 mm', 'pod_d - 2*pwall - 0.1 mm', 'ld_z - top_deck_top')
    B(c, 'shelf opening', 'lidar_x', 'lidar_y', 'top_deck_top - 1 mm', '28 mm', '28 mm', 'ld_z - top_deck_top + 2 mm', op=CUT, bodies=[shelf])
    join(c, b, [shelf], 'lidar pod (printed, smoked)')
    for (hx, hy) in ((-24, -22), (24, -22), (-24, 22), (24, 22)):
        C(c, 'M3 deck bolt', 'z', '(lidar_x) + %d mm' % hx, '(lidar_y) + %d mm' % hy, '(top_deck_top + ld_z)/2', '3.4 mm', 'ld_z - top_deck_top + 1 mm', op=CUT, bodies=[b])
    for (hx, hy) in (('-23.4 mm', '16 mm'), ('23.4 mm', '16 mm'), ('0 mm', '16 mm - 31.92 mm')):
        C(c, 'M2.5 LD19', 'z', '(lidar_x) + (%s)' % hx, '(lidar_y) + %s' % hy, 'ld_z - 2 mm', '2.7 mm', '5 mm', op=CUT, bodies=[b])
    # front grille (like the photo) + side vents
    for k in range(6):
        B(c, 'front vent', '(lidar_x) - 17.5 mm + %d*7 mm' % k, '(lidar_y) + pod_d/2', 'body_top + 1 mm', '3.5 mm', '6 mm', 'pod_top - body_top - 6 mm', op=CUT, bodies=[b])
    for sx in (1, -1):
        for k in range(3):
            B(c, 'side vent', '(lidar_x) + %s' % S(sx, 'pod_w/2'), '(lidar_y) - 10 mm + %d*10 mm' % k, 'body_top + 1 mm', '6 mm', '4 mm', 'pod_top - body_top - 6 mm', op=CUT, bodies=[b])
    l = fresh('Lidar LDROBOT LD19')
    ears = B(l, 'LD19 ear plate', 'lidar_x', 'lidar_y', 'ld_z', '54 mm', '46.29 mm', '2.5 mm', 'ABS Plastic', BLACK)
    fillet(l, edges_where(ears, lambda e: is_axis_line(e, 'z')), '6 mm')
    for (hx, hy) in (('-23.4 mm', '16 mm'), ('23.4 mm', '16 mm'), ('0 mm', '16 mm - 31.92 mm')):
        C(l, 'ear hole', 'z', '(lidar_x) + (%s)' % hx, '(lidar_y) + %s' % hy, 'ld_z + 1.25 mm', '2.5 mm', '3 mm', op=CUT, bodies=[ears])
    RB(l, 'LD19 body', 'lidar_x', 'lidar_y', 'ld_z + 2.5 mm', '38.59 mm', '38.59 mm', '34.8 mm - 12.6 mm - 2.5 mm', '6 mm', 'ABS Plastic', BLACK)
    C(l, 'LD19 rotating head', 'z', 'lidar_x', 'lidar_y', 'ld_z + 34.8 mm - 6.3 mm', '35.29 mm', '12.6 mm', 'ABS Plastic', GLOSSB)
    C(l, 'LD19 window band (scan plane)', 'z', 'lidar_x', 'lidar_y', 'scan_z', '35.4 mm', '6 mm', 'Glass', 'Glass (Grey)')
    log('lidar ok, scan z =', mm('scan_z'), 'pod top', mm('pod_top'), 'LD19 top', mm('ld_z + 34.8 mm'))
    done()


def main():
    pod()
