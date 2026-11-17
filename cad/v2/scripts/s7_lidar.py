# Stage 7: lidar backpack pod + LDROBOT LD19.
# The pod is printed, bolted to the top deck through a hole in the shell, vented on all
# sides. Its top sits at scan_z - scan_h so the LD19 scan plane passes through the exposed
# stem gap between the plinth top and the turret bottom.

PARAMS7 = [
    ('pod_top', 'scan_z - scan_h', 'Lidar pod top (LD19 ears sit here)'),
]


def pod():
    for n, e, cm in PARAMS7:
        param(n, e, cm)
    c = fresh('Lidar backpack pod (printed)')
    b = RB(c, 'pod', '0 mm', 'lidar_y', 'top_deck_top', 'pod_w', 'pod_d', 'pod_top - top_deck_top', '14 mm', 'PET Plastic', 'SB Smoked PETG')
    top = zfaces(b, True)
    col = OC.create()
    for e in top.edges:
        col.add(e)
    fillet(c, col, '5 mm')
    bot = OC.create()
    bot.add(zfaces(b, False))
    si = c.features.shellFeatures.createInput(bot, False)
    si.insideThickness = V.createByString('pwall')
    c.features.shellFeatures.add(si)
    # base flange inside (bolts to the deck), LD19 holes (SRC: 2 on a 46.8 row, 3rd 31.92 behind), cable hole
    fl = B(c, 'pod flange', '0 mm', 'lidar_y', 'top_deck_top', 'pod_w - 2*pwall - 0.1 mm', 'pod_d - 2*pwall - 0.1 mm', '3 mm')
    B(c, 'flange opening', '0 mm', 'lidar_y', 'top_deck_top - 1 mm', 'pod_w - 18 mm', 'pod_d - 18 mm', '5 mm', op=CUT, bodies=[fl])
    join(c, b, [fl], 'lidar pod (printed, smoked)')
    for (hx, hy) in ((-26, -24), (26, -24), (-26, 24), (26, 24)):
        C(c, 'M3 deck bolt', 'z', '%d mm' % hx, '(lidar_y) + %d mm' % hy, 'top_deck_top + 1.5 mm', '3.4 mm', '4 mm', op=CUT, bodies=[b])
    for (hx, hy) in (('-23.4 mm', '16 mm'), ('23.4 mm', '16 mm'), ('0 mm', '16 mm - 31.92 mm')):
        C(c, 'M2.5 LD19', 'z', hx, '(lidar_y) + %s' % hy, 'pod_top - 1.2 mm', '2.7 mm', '4 mm', op=CUT, bodies=[b])
    C(c, 'cable hole', 'z', '0 mm', '(lidar_y) - 4 mm', 'pod_top - 1.2 mm', '10 mm', '4 mm', op=CUT, bodies=[b])
    # vents: slots on the sides and back (the LD19 motor makes a little heat; the pod also breathes)
    for k in range(5):
        for sx in (1, -1):
            B(c, 'side vent', S(sx, 'pod_w/2'), '(lidar_y) - 20 mm + %d*10 mm' % k, 'body_top + 4 mm', '8 mm', '4 mm', 'pod_top - body_top - 12 mm', op=CUT, bodies=[b])
        B(c, 'rear vent', '-20 mm + %d*10 mm' % k, '(lidar_y) - pod_d/2', 'body_top + 4 mm', '4 mm', '8 mm', 'pod_top - body_top - 12 mm', op=CUT, bodies=[b])
    l = fresh('Lidar LDROBOT LD19')
    LZ = 'pod_top'
    ears = B(l, 'LD19 ear plate', '0 mm', 'lidar_y', LZ, '54 mm', '46.29 mm', '2.5 mm', 'ABS Plastic', BLACK)
    fillet(l, edges_where(ears, lambda e: is_axis_line(e, 'z')), '6 mm')
    for (hx, hy) in (('-23.4 mm', '16 mm'), ('23.4 mm', '16 mm'), ('0 mm', '16 mm - 31.92 mm')):
        C(l, 'ear hole', 'z', hx, '(lidar_y) + %s' % hy, '%s + 1.25 mm' % LZ, '2.5 mm', '3 mm', op=CUT, bodies=[ears])
    base = RB(l, 'LD19 body', '0 mm', 'lidar_y', '%s + 2.5 mm' % LZ, '38.59 mm', '38.59 mm', '34.8 mm - 12.6 mm - 2.5 mm', '6 mm', 'ABS Plastic', BLACK)
    C(l, 'LD19 rotating head', 'z', '0 mm', 'lidar_y', '%s + 34.8 mm - 6.3 mm' % LZ, '35.29 mm', '12.6 mm', 'ABS Plastic', GLOSSB)
    C(l, 'LD19 window band (scan plane)', 'z', '0 mm', 'lidar_y', 'scan_z', '35.4 mm', '6 mm', 'Glass', 'Glass (Grey)')
    log('lidar ok, scan z =', mm('scan_z'), 'pod top', mm('pod_top'), 'LD19 top', mm('pod_top + 34.8 mm'))
    done()


def main():
    pod()
