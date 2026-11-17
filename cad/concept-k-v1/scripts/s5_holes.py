# Stage 5: mounting holes. Cuts M3 / M2.5 clearance holes in the chassis plate,
# the upper deck and the printed feet so every bought board has a real fixing.
# Re-run after re-running stage 1 or the deck in stage 2.


def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def _body(cname, bname):
    o = find_occ(cname)
    if o is None:
        raise Exception('missing component ' + cname)
    c = o.component
    for b in c.bRepBodies:
        if b.name == bname:
            return c, b
    raise Exception('missing body %s/%s' % (cname, bname))


def holes(c, body, pts, dia, z0, h, name):
    n = 0
    for (x, y) in pts:
        cyl(c, name, 'z', {'x': x, 'y': y, 'z': '(%s) + (%s)/2' % (z0, h)}, dia, '(%s) + 2 mm' % h, op=CUT, bodies=[body])
        n += 1
    return n


def main(feet=True):
    pc, plate = _body('Chassis plate', 'Chassis plate')
    PZ, PT = 'plate_z - 1 mm', 'plate_t'
    n = 0
    # deck standoffs
    pts = []
    for sx in (1, -1):
        for (x, y) in ((80, 174), (145, 95), (145, -95), (80, -174)):
            pts.append(('%d mm' % (sx * x), '%d mm' % y))
    n += holes(pc, plate, pts, '3.4 mm', PZ, PT, 'M3 deck standoff')
    # BTS7960 standoffs
    pts = []
    for sx in (1, -1):
        for sy in (1, -1):
            for hx in (1, -1):
                for hy in (1, -1):
                    pts.append(('%s + %d*22.5 mm' % (S(sx, 'drv_x'), hx), '%s + %d*22.5 mm' % (S(sy, 'drv_y'), hy)))
    n += holes(pc, plate, pts, '3.4 mm', PZ, PT, 'M3 driver')
    # motor mount feet (plate + the printed feet)
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        pts = [(S(sx, 'gb_face - 14 mm'), '%s + %d*(gb_d/2 + 8 mm)' % (S(sy, 'wheel_y'), gy)) for gy in (1, -1)]
        spts = [(S(sx, 'gb_face - gb_len - can_len/2'), '%s + %d*10 mm' % (S(sy, 'wheel_y'), gy)) for gy in (1, -1)]
        n += holes(pc, plate, pts + spts, '3.4 mm', PZ, PT, 'M3 motor mount')
        if not feet:
            continue
        mo = find_occ('Motor mount + well liner %s' % tag, find_occ('Drive %s' % tag).component)
        mb = mo.component.bRepBodies.itemByName('motor mount + well liner')
        holes(mo.component, mb, pts, '3.4 mm', 'plate_top - 1 mm', '7 mm', 'M3 foot')
        sb = mo.component.bRepBodies.itemByName('motor saddle (printed)')
        holes(mo.component, sb, spts, '2.5 mm', 'plate_top - 1 mm', '6 mm', 'M3 insert pilot')
    # panel clips, sled rails, CPX mount, buck
    pts = [('%d mm' % x, S(sy, 'plate_d/2 - 4 mm')) for x in (-110, 110) for sy in (1, -1)]
    pts += [(S(sx, 'plate_w/2 - 4 mm'), '%d mm' % y) for sx in (1, -1) for y in (-60, 60)]
    pts += [(S(sx, 'pack_x/2 + 1 mm + pwall + 3 mm'), '%d mm' % y) for sx in (1, -1) for y in (-150, -80, -10)]
    pts += [('%s mm' % x, '%s mm' % y) for (x, y) in ((-10.2, 99.8), (10.2, 120.2))]
    pts += [('%d*17 mm' % k, 'shell_y - 16.6 mm') for k in (1, -1)]  # front HC-SR04 holder
    n += holes(pc, plate, pts, '3.4 mm', PZ, PT, 'M3 misc')
    # VL53L0X sensing window (sensor looks down through the plate)
    cyl(pc, 'VL53L0X window', 'z', {'x': '0 mm', 'y': '170 mm', 'z': 'plate_z + plate_t/2'}, '10 mm', 'plate_t + 2 mm', op=CUT, bodies=[plate])
    holes(pc, plate, [('%d*8.25 mm' % k, '170 mm') for k in (1, -1)], '2.7 mm', PZ, PT, 'M2.5 VL53L0X (EST spacing)')
    # upper deck: Pi 5 (58 x 49), BNO085, ESP32 cradles
    dc, deck = _body('Upper deck (acrylic) + standoffs', 'upper deck 3 mm acrylic')
    pts = [('pi_xc - 42.5 mm + 3.5 mm + %s' % dx, 'pi_yc - 28 mm + 3.5 mm + %s' % dy) for dx in ('0 mm', '58 mm') for dy in ('0 mm', '49 mm')]
    pts += [('%d*10.16 mm' % hx, '-20 mm + %d*8.89 mm' % hy) for hx in (1, -1) for hy in (1, -1)]
    n += holes(dc, deck, pts, '2.7 mm', 'deck_z - 1 mm', 'deck_t', 'M2.5')
    pts = [('%s mm' % x, '(-deck_y + 62.74 mm/2) + %d*22 mm' % k) for x in (60, 95) for k in (1, -1)]
    pts += [('%d*17 mm' % k, '-175 mm') for k in (1, -1)]  # rear HC-SR04 holder arm
    pts += [('0 mm', 'neck_y - 5.4 mm + %d*14 mm' % k) for k in (1, -1)]
    pts += [('%d*12 mm' % k, 'deck_y - 9 mm') for k in (1, -1)]
    n += holes(dc, deck, pts, '3.4 mm', 'deck_z - 1 mm', 'deck_t', 'M3 deck')
    log('holes cut', n)
    done()
