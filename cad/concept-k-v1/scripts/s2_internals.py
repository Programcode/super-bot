# Stage 2: battery 3S4P + BMS on a rear slide-out sled, power parts, 4x BTS7960,
# upper deck with standoffs, Pi 5 + Active Cooler + AI HAT+ 2, 2x ESP32-S3,
# BNO085, CPX status ring, HC-SR04 front/rear, VL53L0X.

PARAMS2 = [
    ('cell_d', '18.6 mm', '18650 cell dia (SRC 18.3-18.6)'),
    ('cell_l', '65.2 mm', '18650 cell length, unprotected flat-top (SRC)'),
    ('pack_x', '2*cell_l + 4 mm', '3S4P pack X: 2 cells end to end + nickel/holders'),
    ('pack_y', '6*cell_d + 3 mm', '3S4P pack Y: 6 cells side by side + wrap'),
    ('pack_h', 'cell_d + 2.5 mm', '3S4P pack height (single flat layer, lowest CoG)'),
    ('pack_yc', '-12 mm', 'Pack centre Y (sled must fit a 256 mm bed)'),
    ('sled_floor', '2 mm', 'Battery sled floor'),
    ('deck_z', '80 mm', 'Upper deck underside'),
    ('deck_t', '3 mm', 'Upper deck (3 mm clear acrylic)'),
    ('deck_top', 'deck_z + deck_t', 'Upper deck top'),
    ('deck_x', '152 mm', 'Upper deck half-width'),
    ('deck_y', '178 mm', 'Upper deck half-depth'),
    ('drv_x', '125 mm', 'BTS7960 centre |X|'),
    ('drv_y', '32 mm', 'BTS7960 centre |Y|'),
    ('drv_so', '6 mm', 'BTS7960 standoff height'),
    ('pi_xc', '-55 mm', 'Pi 5 PCB centre X'),
    ('pi_yc', '-150 mm', 'Pi 5 PCB centre Y'),
    ('pi_so', '6 mm', 'Pi 5 standoffs on deck'),
    ('pi_z', 'deck_top + pi_so', 'Pi 5 PCB underside'),
    ('hat_so', '16 mm', 'AI HAT+ 2 stacking header / spacer height (SRC)'),
    ('cpx_z', '100 mm', 'CPX status ring centre height on the front face'),
]


def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def define_params2():
    for n, e, cmt in PARAMS2:
        param(n, e, cmt)


def B(c, name, x, y, z, w, d, h, mat=None, look=None, op=NEWB, bodies=None):
    """box by centre x,y and BOTTOM z (expressions)."""
    b = box(c, name, {'x': x, 'y': y, 'z': '(%s) + (%s)/2' % (z, h)}, {'x': w, 'y': d, 'z': h}, op=op, bodies=bodies)
    if op == NEWB:
        finish(b, mat, look)
    return b


def C(c, name, axis, x, y, z, dia, ln, mat=None, look=None, op=NEWB, bodies=None):
    b = cyl(c, name, axis, {'x': x, 'y': y, 'z': z}, dia, ln, op=op, bodies=bodies)
    if op == NEWB:
        finish(b, mat, look)
    return b


GREEN = 'Plastic - Matte (Green)'
BLACK = 'Plastic - Matte (Black)'
GLOSSB = 'Plastic - Glossy (Black)'
ALU = 'Aluminum - Satin'
PETG = 'Plastic - Matte (Gray)'


def battery():
    c = fresh('Battery 3S4P 18650 + BMS')
    z0 = 'plate_top + sled_floor'
    cz = '(%s) + cell_d/2 + 1 mm' % z0
    for ix in (-1, 1):
        for iy in range(6):
            y = '(pack_yc) + (%d - 2.5)*(cell_d + 0.4 mm)' % iy
            x = '%d*(cell_l/2 + 1 mm)' % ix
            b = C(c, 'cell', 'x', x, y, cz, 'cell_d', 'cell_l', 'Steel', 'Plastic - Matte (Blue)')
    # nickel strips at both ends and the middle, holder frames
    for xs in ('-(cell_l + 1.5 mm)', '0 mm', '(cell_l + 1.5 mm)'):
        B(c, 'nickel strip', xs, 'pack_yc', '(%s) + 1 mm' % z0, '0.6 mm' if xs != '0 mm' else '1.2 mm', 'pack_y - 4 mm', 'cell_d', 'Steel', 'Steel - Satin')
    B(c, 'BMS 3S 40A', '0 mm', '(pack_yc) - pack_y/2 - 8 mm - 41 mm/2', z0, '60 mm', '41 mm', '3.4 mm', 'FR4', 'Plastic - Matte (Blue)')
    log('battery ok')


def sled():
    c = fresh('Battery sled (printed PETG)')
    front = '(pack_yc) + pack_y/2 + 1 mm + pwall'
    back = '-(shell_y)'
    L = '(%s) - (%s)' % (front, back)
    yc = '((%s) + (%s))/2' % (front, back)
    W = 'pack_x + 2 mm + 2*pwall'
    s = B(c, 'sled', '0 mm', yc, 'plate_top', W, L, '15 mm', 'PET Plastic', PETG)
    B(c, 'pocket', '0 mm', yc, 'plate_top + sled_floor', 'pack_x + 2 mm', '(%s) - 2*pwall' % L, '20 mm', op=CUT, bodies=[s])
    # battery door: fills the rear panel opening, finger recess
    d = B(c, 'battery door', '0 mm', '-(shell_y) + wall_t/2', 'plate_z + 0.5 mm', 'pack_x + 8 mm', 'wall_t', '40 mm', 'PET Plastic', GLOSSB)
    B(c, 'finger recess', '0 mm', '-(shell_y) + 0.8 mm', 'plate_z + 26 mm', '40 mm', '2 mm', '8 mm', op=CUT, bodies=[d])
    combine(c, s, [d], JOIN)
    B(c, 'switch cutout KCD1', '45 mm', '-(shell_y) + 6 mm', 'plate_z + 14 mm', '19.2 mm', '14 mm', '13.2 mm', op=CUT, bodies=[s])
    s.name = 'battery sled + door'
    for sx in (1, -1):
        B(c, 'sled rail', S(sx, 'pack_x/2 + 1 mm + pwall + 3 mm'), '(-(plate_d/2) + 1 mm + (%s) - 40 mm)/2' % front, 'plate_top', '5 mm',
          '(%s) - 40 mm + plate_d/2 - 1 mm' % front, '8 mm', 'PET Plastic', PETG)
    # placeholders: main switch on the door, XT60 inside
    p = fresh('Power placeholders')
    sw = B(p, 'main rocker switch (placeholder KCD1 21x15)', '45 mm', '-(shell_y) - 1 mm', 'plate_z + 13 mm', '21 mm', '2 mm', '15 mm', 'ABS Plastic', 'Plastic - Matte (Red)')
    swb = B(p, 'switch body', '45 mm', '-(shell_y) + 7 mm', 'plate_z + 14.1 mm', '19 mm', '14 mm', '13 mm', 'ABS Plastic', 'Plastic - Matte (Black)')
    combine(p, sw, [swb], JOIN)
    B(p, 'XT60 pair (placeholder)', '-35 mm', '(pack_yc) - pack_y/2 - 8 mm - 41 mm - 14 mm', 'plate_top + sled_floor', '16 mm', '20 mm', '8 mm', 'ABS Plastic', 'Plastic - Matte (Yellow)')
    bk = B(p, 'buck Pololu D36V50F5 5V 5.5A', '0 mm', '110 mm', 'plate_top + 4 mm', '25.4 mm', '25.4 mm', '1.6 mm', 'FR4', GREEN)
    B(p, 'buck inductor', '0 mm', '110 mm', 'plate_top + 5.6 mm', '12 mm', '12 mm', '7.9 mm', 'Steel', BLACK)
    log('sled ok')


def drivers():
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        c = fresh('Motor driver BTS7960 %s' % tag)
        x, y = S(sx, 'drv_x'), S(sy, 'drv_y')
        z = 'plate_top + drv_so'
        B(c, 'IBT-2 PCB', x, y, z, '50 mm', '50 mm', '1.6 mm', 'FR4', GREEN)
        hs = B(c, 'heatsink', x, y, '(%s) + 4.6 mm' % z, '46 mm', '40 mm', '38.4 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
        for k in range(5):
            B(c, 'fin slot', x, '(%s) + (%d - 2)*7.5 mm' % (y, k), '(%s) + 14.6 mm' % z, '47 mm', '3 mm', '29 mm', op=CUT, bodies=[hs])
        B(c, 'screw terminals', '(%s) + %d*(25 mm - 4 mm)' % (x, sx), y, '(%s) + 1.6 mm' % z, '8 mm', '30 mm', '10 mm', 'ABS Plastic', 'Plastic - Matte (Blue)')
        B(c, 'logic header', '(%s) - %d*(25 mm - 2 mm)' % (x, sx), y, '(%s) + 1.6 mm' % z, '3 mm', '20 mm', '8.5 mm', 'ABS Plastic', BLACK)
        for hx in (-1, 1):
            for hy in (-1, 1):
                C(c, 'standoff', 'z', '(%s) + %d*22.5 mm' % (x, hx), '(%s) + %d*22.5 mm' % (y, hy), 'plate_top + drv_so/2', '5.5 mm', 'drv_so', 'Copper, Alloy', 'Brass - Polished')
    log('drivers ok')


DECK_SO = [(80, 174), (145, 95), (145, -95), (80, -174)]


def deck():
    c = fresh('Upper deck (acrylic) + standoffs')
    sk = sketch(c, 'z', 'deck outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': '2*deck_x', 'y': '2*deck_y'})
    f = extrude(c, sk, 'deck_z', 'deck_t', name='upper deck 3 mm acrylic')
    d = f.bodies.item(0)
    fillet(c, edges_where(d, lambda e: is_axis_line(e, 'z')), '12 mm')
    # wiring pass-through slots (cable path between decks) and standoff holes
    for (x, y, w, h) in ((100, 75, 30, 10), (-100, 75, 30, 10), (100, -75, 30, 10), (-100, -75, 30, 10), (0, -95, 60, 10), (0, 140, 60, 10)):
        B(c, 'wire slot', '%d mm' % x, '%d mm' % y, 'deck_z - 1 mm', '%d mm' % w, '%d mm' % h, 'deck_t + 2 mm', op=CUT, bodies=[d])
    for sxv in (1, -1):
        for (x, y) in DECK_SO:
            xx = '%d mm' % (sxv * x)
            C(c, 'M3 hole', 'z', xx, '%d mm' % y, 'deck_z + deck_t/2', '3.2 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
            C(c, 'M3 standoff', 'z', xx, '%d mm' % y, '(plate_top + deck_z)/2', '5.5 mm', 'deck_z - plate_top', 'Copper, Alloy', 'Brass - Polished')
    finish(d, 'Acrylic', 'Acrylic (Clear)')
    log('deck ok')


def pi_stack():
    c = fresh('Raspberry Pi 5 8GB + Active Cooler')
    X, Y, Z = 'pi_xc', 'pi_yc', 'pi_z'
    L, R = '(pi_xc - 42.5 mm)', '(pi_xc + 42.5 mm)'      # left/right edges (X)
    BOT, TOP = '(pi_yc - 28 mm)', '(pi_yc + 28 mm)'      # port edge (rear) / GPIO edge (front)
    B(c, 'Pi 5 PCB', X, Y, Z, '85 mm', '56 mm', '1.4 mm', 'FR4', GREEN)
    PT = '(pi_z + 1.4 mm)'
    B(c, 'Ethernet RJ45', '%s - 21.5 mm/2 + 2 mm' % R, '%s + 10.2 mm' % BOT, PT, '21.5 mm', '16 mm', '13.7 mm', 'Steel', 'Steel - Satin')
    for yy in ('29.1 mm', '47 mm'):
        B(c, 'USB-A stack', '%s - 17.5 mm/2 + 2 mm' % R, '%s + %s' % (BOT, yy), PT, '17.5 mm', '13.1 mm', '16.8 mm', 'Steel', 'Steel - Satin')
    B(c, 'USB-C power', '%s + 11.2 mm' % L, '%s + 7.5 mm/2 - 1 mm' % BOT, PT, '9 mm', '7.5 mm', '3.3 mm', 'Steel', 'Steel - Satin')
    for xx in ('25.8 mm', '39.2 mm'):
        B(c, 'micro HDMI', '%s + %s' % (L, xx), '%s + 7.5 mm/2 - 1 mm' % BOT, PT, '6.5 mm', '7.5 mm', '3.2 mm', 'Steel', 'Steel - Satin')
    B(c, 'GPIO 2x20 header', '%s + 32.5 mm' % L, '%s - 3.5 mm' % TOP, PT, '51 mm', '5 mm', '8.5 mm', 'ABS Plastic', BLACK)
    B(c, 'Active Cooler', '%s + 3.5 mm + 29 mm' % L, '%s + 2 mm' % Y, PT, '63.5 mm', '42.5 mm', '13.7 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    C(c, 'cooler fan', 'z', '%s + 3.5 mm + 29 mm + 14 mm' % L, '%s + 2 mm' % Y, '%s + 13.8 mm' % PT, '28 mm', '0.4 mm', 'ABS Plastic', BLACK)
    for hx in (-1, 1):
        for hy in (-1, 1):
            hxp = '%s + 3.5 mm + %s' % (L, '58 mm' if hx > 0 else '0 mm')
            hyp = '%s + 3.5 mm + %s' % (BOT, '49 mm' if hy > 0 else '0 mm')
            C(c, 'M2.5 standoff 6', 'z', hxp, hyp, 'deck_top + pi_so/2', '5 mm', 'pi_so', 'Copper, Alloy', 'Brass - Polished')
            C(c, 'M2.5 spacer 16', 'z', hxp, hyp, 'pi_z + 1.4 mm + hat_so/2', '5 mm', 'hat_so', 'Copper, Alloy', 'Brass - Polished')
    h = fresh('Raspberry Pi AI HAT+ 2 (Hailo-10H)')
    HZ = '(pi_z + 1.4 mm + hat_so)'
    B(h, 'AI HAT+ 2 PCB', '%s + 32.5 mm' % L, '%s - 56.5 mm/2' % TOP, HZ, '65 mm', '56.5 mm', '1.6 mm', 'FR4', GREEN)
    hs = B(h, 'HAT heatsink', '%s + 32.5 mm' % L, '%s - 56.5 mm/2' % TOP, '%s + 1.6 mm' % HZ, '64 mm', '42.5 mm', '14 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    for k in range(7):
        B(h, 'fin slot', '%s + 32.5 mm + (%d - 3)*8.5 mm' % (L, k), '%s - 56.5 mm/2' % TOP, '%s + 4.6 mm' % HZ, '4.5 mm', '44 mm', '12 mm', op=CUT, bodies=[hs])
    log('pi ok', 'stack top z', mm('pi_z + 1.4 mm + hat_so + 1.6 mm + 14 mm'))


def esp32s():
    for i, xc in enumerate(('22 mm', '57 mm')):
        tag = 'AB'[i]
        c = fresh('ESP32-S3-DevKitC-1 %s' % tag)
        y = '(-deck_y + 62.74 mm/2)'
        cr = B(c, 'printed cradle', xc, y, 'deck_top', '29.4 mm', '58 mm', '9 mm', 'PET Plastic', PETG)
        B(c, 'header pocket', xc, y, 'deck_top + 2 mm', '25.4 mm', '60 mm', '8 mm', op=CUT, bodies=[cr])
        pz = 'deck_top + 9 mm'
        B(c, 'pin headers', '%s - 11.43 mm' % xc, '%s + 2 mm' % y, 'deck_top + 2 mm', '2.54 mm', '55 mm', '7 mm', 'ABS Plastic', BLACK)
        B(c, 'pin headers 2', '%s + 11.43 mm' % xc, '%s + 2 mm' % y, 'deck_top + 2 mm', '2.54 mm', '55 mm', '7 mm', 'ABS Plastic', BLACK)
        B(c, 'DevKitC PCB', xc, y, pz, '25.4 mm', '62.74 mm', '1.6 mm', 'FR4', GLOSSB)
        B(c, 'WROOM-1 module', xc, '%s + 62.74 mm/2 - 25.5 mm/2' % y, '%s + 1.6 mm' % pz, '18 mm', '25.5 mm', '3.1 mm', 'Steel', 'Steel - Satin')
        for ox in ('-4.5 mm', '4.5 mm'):
            B(c, 'USB-C', '%s + %s' % (xc, ox), '-deck_y + 7.4 mm/2 - 1 mm', '%s + 1.6 mm' % pz, '8.9 mm', '7.4 mm', '3.2 mm', 'Steel', 'Steel - Satin')
    log('esp ok')


def bno():
    c = fresh('BNO085 IMU (Adafruit 4754)')
    B(c, 'BNO085 PCB', '0 mm', '-20 mm', 'deck_top + 5 mm', '25.6 mm', '22.7 mm', '1.6 mm', 'FR4', GLOSSB)
    B(c, 'BNO085 chip', '0 mm', '-20 mm', 'deck_top + 6.6 mm', '5.2 mm', '3.8 mm', '1.1 mm', 'Steel', BLACK)
    for hx in (-1, 1):
        for hy in (-1, 1):
            C(c, 'M2.5 standoff 5', 'z', '%d*10.16 mm' % hx, '-20 mm + %d*8.89 mm' % hy, 'deck_top + 2.5 mm', '4.5 mm', '5 mm', 'Copper, Alloy', 'Brass - Polished')


def cpx():
    c = fresh('Circuit Playground Express status ring')
    yb = '(shell_y - wall_t - 5.5 mm)'  # PCB back face
    C(c, 'CPX PCB', 'y', '0 mm', '%s + 0.8 mm' % yb, 'cpx_z', '50.8 mm', '1.6 mm', 'FR4', GLOSSB)
    led = appearance('SB NeoPixel glow', 'LED - SMD 5050 - 20lm (White)')
    for a in (0, 30, 60, 120, 150, 180, 210, 240, 300, 330):
        r = math.radians(a)
        b = B(c, 'NeoPixel', '%.4f*17.15 mm' % math.cos(r), '%s + 1.6 mm + 0.5 mm' % yb, 'cpx_z - 1.75 mm + %.4f*17.15 mm' % math.sin(r),
              '3.5 mm', '1 mm', '3.5 mm', 'ABS Plastic')
        finish(b, None, led)
    B(c, 'USB micro', '0 mm', '%s + 1.6 mm + 1.5 mm' % yb, 'cpx_z + 20 mm', '7.5 mm', '3 mm', '5 mm', 'Steel', 'Steel - Satin')
    for bx in (-1, 1):
        B(c, 'button', '%d*13 mm' % bx, '%s + 1.6 mm + 1.5 mm' % yb, 'cpx_z - 3 mm', '6 mm', '3 mm', '6 mm', 'ABS Plastic', BLACK)
    B(c, 'speaker + mic', '0 mm', '%s + 1.6 mm + 1 mm' % yb, 'cpx_z - 4 mm', '8 mm', '2 mm', '8 mm', 'ABS Plastic', BLACK)
    # printed ring mount (bolts through two of the CPX pads, stands on the plate)
    # printed L-bracket hung from the deck front edge; CPX bolts through two pads
    m = B(c, 'CPX mount (printed)', '0 mm', '%s - 2.5 mm' % yb, 'deck_top', '40 mm', '5 mm', 'cpx_z - deck_top + 22 mm', 'PET Plastic', PETG)
    arm = B(c, 'CPX mount arm', '0 mm', '((%s) - 5 mm + deck_y - 18 mm)/2' % yb, 'deck_top', '40 mm', '(%s) - 5 mm - deck_y + 18 mm' % yb, '5 mm', 'PET Plastic', PETG)
    combine(c, m, [arm], JOIN)
    m.name = 'CPX mount (printed)'
    C(c, 'cable hole', 'y', '0 mm', '%s - 2.5 mm' % yb, 'cpx_z', '14 mm', '6 mm', op=CUT, bodies=[m])
    for k in (-1, 1):
        C(c, 'M3 hole', 'z', '%d*12 mm' % k, 'deck_y - 9 mm', 'deck_top + 2.5 mm', '3.4 mm', '7 mm', op=CUT, bodies=[m])
    log('cpx ok')


def ultrasonics():
    for tag, sy, zc in (('front', 1, '46 mm'), ('rear', -1, '74 mm')):
        c = fresh('HC-SR04 %s' % tag)
        pcb_y = S(sy, 'shell_y - 12 mm - 0.8 mm')
        B(c, 'HC-SR04 PCB', '0 mm', pcb_y, '(%s) - 10 mm' % zc, '45 mm', '1.6 mm', '20 mm', 'FR4', 'Plastic - Matte (Blue)')
        for tx in (-1, 1):
            C(c, 'transducer', 'y', '%d*13 mm' % tx, S(sy, 'shell_y - 6 mm'), zc, '16 mm', '12 mm', 'Aluminum 6061', ALU)
        B(c, 'crystal + pins', '0 mm', S(sy, 'shell_y - 12 mm - 1.6 mm - 3 mm'), '(%s) - 10 mm' % zc, '10.2 mm', '6 mm', '3 mm', 'Steel', BLACK)
    c = fresh('VL53L0X cliff ToF (Adafruit 3317)')
    B(c, 'VL53L0X PCB', '0 mm', '175 mm', 'plate_top', '21 mm', '18 mm', '1.6 mm', 'FR4', GLOSSB)
    log('ultrasonics ok')


def main():
    define_params2()
    battery()
    sled()
    drivers()
    deck()
    pi_stack()
    esp32s()
    bno()
    cpx()
    ultrasonics()
    done()
