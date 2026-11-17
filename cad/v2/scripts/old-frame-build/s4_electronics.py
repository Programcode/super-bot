# Stage 4: electronics.
# Spine front (the chimney, seen through the front panel): Raspberry Pi 5 + Active Cooler
# + AI HAT+ 2 standing vertical (heatsink fins vertical), 5 V 5 A buck beside its USB-C,
# ESP32-S3 A in a printed cradle + an empty cradle for a second ESP32, CPX status ring +
# INMP441 mic on a bracket under the top deck.
# Spine back: servo buck. L1 deck: PDB + INA226, BNO085 at the centre, MAX98357A, speaker.
# Upper back: XT60 loop key (main power).

PARAMS4 = [
    ('pi_xc', '52 mm', 'Pi 5 PCB centre X (USB/Ethernet edge faces the right panel)'),
    ('pi_z0', '190 mm', 'Pi 5 PCB bottom (port) edge Z'),
    ('pi_so', '6 mm', 'Pi standoffs off the spine'),
    ('pi_y0', 'spine_y + pi_so', 'Pi PCB back face Y'),
    ('hat_so', '16 mm', 'AI HAT+ 2 spacer height'),
    ('esp_z', '128 mm', 'ESP32 cradles bottom Z'),
    ('cpx_z', '300 mm', 'CPX status ring centre Z'),
    ('cpx_y', 'shell_y - pwall - 6 mm', 'CPX PCB front face Y'),
    ('key_x', '60 mm', 'XT60 loop key X on the upper back'),
    ('key_z', 'body_top - 52 mm', 'XT60 loop key Z'),
]


def define():
    for n, e, cm in PARAMS4:
        param(n, e, cm)


def pi_box(c, name, u, v, wu, hv, t, yb, mat, look, op=NEWB, bodies=None):
    """Box in Pi board coordinates: u from the left edge (-> +X), v from the port edge (-> +Z),
    yb = offset from the PCB front face (-> +Y). u, v are the box's low corner."""
    x = '(pi_xc - 42.5 mm) + (%s) + (%s)/2' % (u, wu)
    z = 'pi_z0 + (%s) + (%s)/2' % (v, hv)
    y = 'pi_y0 + 1.4 mm + (%s) + (%s)/2' % (yb, t)
    b = box(c, name, {'x': x, 'y': y, 'z': z}, {'x': wu, 'y': t, 'z': hv}, op=op, bodies=bodies)
    if op == NEWB:
        finish(b, mat, look)
    return b


def pi_stack():
    c = fresh('Raspberry Pi 5 8GB + Active Cooler')
    pi_box(c, 'Pi 5 PCB', '0 mm', '0 mm', '85 mm', '56 mm', '1.4 mm', '-1.4 mm', 'FR4', GREEN)
    pi_box(c, 'Ethernet RJ45', '85 mm - 21.5 mm + 2 mm', '10.2 mm - 8 mm', '21.5 mm', '16 mm', '13.7 mm', '0 mm', 'Steel', STEEL)
    for vv in ('29.1 mm', '47 mm'):
        pi_box(c, 'USB-A stack', '85 mm - 17.5 mm + 2 mm', '(%s) - 6.55 mm' % vv, '17.5 mm', '13.1 mm', '16.8 mm', '0 mm', 'Steel', STEEL)
    pi_box(c, 'USB-C power', '11.2 mm - 4.5 mm', '-1 mm', '9 mm', '7.5 mm', '3.3 mm', '0 mm', 'Steel', STEEL)
    for uu in ('25.8 mm', '39.2 mm'):
        pi_box(c, 'micro HDMI', '(%s) - 3.25 mm' % uu, '-1 mm', '6.5 mm', '7.5 mm', '3.2 mm', '0 mm', 'Steel', STEEL)
    for k, uu in (('1', '47.3 mm'), ('0', '53.5 mm')):
        pi_box(c, 'MIPI CAM-DISP%s 22p' % k, uu, '0.5 mm', '3 mm', '15.8 mm', '3 mm', '0 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    pi_box(c, 'GPIO 2x20 header', '32.5 mm - 25.5 mm', '56 mm - 6 mm', '51 mm', '5 mm', '8.5 mm', '0 mm', 'ABS Plastic', BLACK)
    pi_box(c, 'PCIe FFC', '0.5 mm', '20 mm', '3 mm', '15 mm', '1.2 mm', '0 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    pi_box(c, 'Active Cooler', '3.5 mm', '28 mm - 21.25 mm + 2 mm', '63.5 mm', '42.5 mm', '13.7 mm', '0 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    for hu in ('3.5 mm', '61.5 mm'):
        for hv in ('3.5 mm', '52.5 mm'):
            x = '(pi_xc - 42.5 mm) + %s' % hu
            z = 'pi_z0 + %s' % hv
            C(c, 'M2.5 standoff 6', 'y', x, 'spine_y + pi_so/2', z, '5 mm', 'pi_so', 'Copper, Alloy', BRASS)
            C(c, 'M2.5 spacer 16', 'y', x, 'pi_y0 + 1.4 mm + hat_so/2', z, '5 mm', 'hat_so', 'Copper, Alloy', BRASS)
    h = fresh('Raspberry Pi AI HAT+ 2 (Hailo-10H)')
    hb = 'hat_so'
    hp = pi_box(h, 'AI HAT+ 2 PCB', '0 mm', '56 mm - 56.5 mm', '65 mm', '56.5 mm', '1.6 mm', hb, 'FR4', GREEN)
    # camera/display ribbon cut-out (SRC AI HAT+ drawing: x 47.5-57.5, 16 deep)
    pi_box(h, 'ribbon cut-out', '47.5 mm', '-1 mm', '10 mm', '17 mm', '4 mm', '(%s) - 1 mm' % hb, None, None, op=CUT, bodies=[hp])
    hs = pi_box(h, 'HAT heatsink (EST 42x42)', '3 mm', '8 mm', '42 mm', '42 mm', '14 mm', '(%s) + 1.6 mm' % hb, 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    # fins run vertically (along Z) so the chimney draft goes straight through them
    for k in range(5):
        pi_box(h, 'fin slot', '3 mm + 4 mm + %d*8 mm' % k, '7 mm', '4 mm', '44 mm', '12 mm', '(%s) + 3.6 mm' % hb, None, None, op=CUT, bodies=[hs])
    pi_box(h, 'GPIO stacking header', '7 mm', '56 mm - 6 mm', '51 mm', '5 mm', '8.5 mm', '(%s) + 1.6 mm' % hb, 'ABS Plastic', BLACK)
    log('pi ok, stack front y =', mm('pi_y0 + 1.4 mm + hat_so + 1.6 mm + 14 mm'))


def pi_buck():
    c = fresh('Pi 5 V 5.5 A buck (Pololu D36V50F5)')
    x, z = '-15 mm', 'pi_z0 - 18 mm'
    y0 = 'spine_y + 5 mm'
    B(c, 'D36V50F5 PCB', x, '(%s) + 0.8 mm' % y0, '(%s) - 12.7 mm' % z, '25.4 mm', '1.6 mm', '25.4 mm', 'FR4', GREEN)
    B(c, 'inductor', x, '(%s) + 1.6 mm + 3.95 mm' % y0, '(%s) - 6 mm' % z, '12 mm', '7.9 mm', '12 mm', 'Steel', BLACK)
    for hx in (-1, 1):
        C(c, 'M2 standoff 5', 'y', '(%s) + %d*10.2 mm' % (x, hx), 'spine_y + 2.5 mm', '(%s) + %d*10.2 mm' % (z, hx), '4 mm', '5 mm', 'Copper, Alloy', BRASS)
    # short USB-C pigtail from the buck to the Pi's USB-C (right-angle plug)
    B(c, 'USB-C right-angle plug', '(pi_xc - 42.5 mm) + 11.2 mm', 'pi_y0 + 1.4 mm + 1.65 mm', 'pi_z0 - 15 mm', '12 mm', '6.5 mm', '14 mm', 'ABS Plastic', BLACK)
    log('pi buck ok')


def esp32():
    for tag, xc, fitted in (('A', '62 mm', True), ('B spare', '-31 mm', False)):
        c = fresh('ESP32-S3-DevKitC-1 %s' % tag)
        zc = 'esp_z + 14.7 mm'
        cr = B(c, 'printed cradle', xc, 'spine_y + 4.5 mm', 'esp_z', '66 mm', '9 mm', '29.4 mm', 'PET Plastic', BLACK)
        B(c, 'header pocket', xc, 'spine_y + 6.5 mm', 'esp_z + 2 mm', '64 mm', '8 mm', '25.4 mm', op=CUT, bodies=[cr])
        for hx in (-1, 1):
            C(c, 'M3 hole', 'y', '(%s) + %d*29 mm' % (xc, hx), 'spine_y + 1 mm', zc, '3.4 mm', '3 mm', op=CUT, bodies=[cr])
        cr.name = 'printed cradle' if fitted else 'printed cradle (empty, for a second ESP32-S3 later)'
        if not fitted:
            continue
        pz = 'spine_y + 9 mm'
        for dz in ('-11.43 mm', '11.43 mm'):
            B(c, 'pin header', xc, 'spine_y + 5.5 mm', '(%s) + %s - 1.27 mm' % (zc, dz), '55 mm', '7 mm', '2.54 mm', 'ABS Plastic', BLACK)
        B(c, 'DevKitC PCB', xc, '(%s) + 0.8 mm' % pz, '(%s) - 12.7 mm' % zc, '62.74 mm', '1.6 mm', '25.4 mm', 'FR4', GLOSSB)
        B(c, 'WROOM-1 module', '(%s) - 62.74 mm/2 + 25.5 mm/2' % xc, '(%s) + 1.6 mm + 1.55 mm' % pz, '(%s) - 9 mm' % zc, '25.5 mm', '3.1 mm', '18 mm', 'Steel', STEEL)
        for oz in ('-4.5 mm', '4.5 mm'):
            B(c, 'USB-C', '(%s) + 62.74 mm/2 - 7.4 mm/2 + 1 mm' % xc, '(%s) + 1.6 mm + 1.6 mm' % pz, '(%s) + %s - 4.45 mm' % (zc, oz), '7.4 mm', '3.2 mm', '8.9 mm', 'Steel', STEEL)
    log('esp ok')


def cpx_mic():
    c = fresh('Circuit Playground Express status ring')
    yb = 'cpx_y - 1.6 mm'
    C(c, 'CPX PCB', 'y', '0 mm', '(%s) + 0.8 mm' % yb, 'cpx_z', '50.8 mm', '1.6 mm', 'FR4', GLOSSB)
    led = appearance('SB NeoPixel glow', 'LED - SMD 5050 - 20lm (White)')
    for a in (0, 30, 60, 120, 150, 180, 210, 240, 300, 330):
        r = math.radians(a)
        b = B(c, 'NeoPixel', '%.4f*17.15 mm' % math.cos(r), '(%s) + 1.6 mm + 0.5 mm' % yb, 'cpx_z - 1.75 mm + %.4f*17.15 mm' % math.sin(r),
              '3.5 mm', '1 mm', '3.5 mm', 'ABS Plastic')
        finish(b, None, led)
    B(c, 'USB micro', '0 mm', '(%s) - 1.5 mm' % yb, 'cpx_z + 19 mm', '7.5 mm', '3 mm', '5 mm', 'Steel', STEEL)
    for bx in (-1, 1):
        B(c, 'button', '%d*13 mm' % bx, '(%s) + 1.6 mm + 1.5 mm' % yb, 'cpx_z - 3 mm', '6 mm', '3 mm', '6 mm', 'ABS Plastic', BLACK)
    # printed hanger from the top deck: plate behind the CPX, two M3 through CPX pads
    m = B(c, 'CPX + mic hanger (printed)', '0 mm', '(%s) - 4 mm' % yb, 'cpx_z - 20 mm', '90 mm', '4 mm', 'top_deck_z - (cpx_z - 20 mm)', 'PET Plastic', BLACK)
    f = B(c, 'hanger flange', '0 mm', '(%s) - 12 mm' % yb, 'top_deck_z - 4 mm', '90 mm', '16 mm', '4 mm', 'PET Plastic', BLACK)
    join(c, m, [f], 'CPX + mic hanger (printed)')
    C(c, 'cable hole', 'y', '0 mm', '(%s) - 4 mm' % yb, 'cpx_z', '14 mm', '6 mm', op=CUT, bodies=[m])
    for k in (-1, 1):
        C(c, 'M3 pad screw', 'y', '%d*21.6 mm' % k, '(%s) - 2 mm' % yb, 'cpx_z', '3.2 mm', '8 mm', op=CUT, bodies=[m])
        C(c, 'M3 standoff 3', 'y', '%d*21.6 mm' % k, '(%s) - 1 mm' % yb, 'cpx_z', '5 mm', '2 mm', 'Copper, Alloy', BRASS)
    mic = fresh('Mic INMP441 (I2S)')
    B(mic, 'INMP441 PCB (EST 14x14)', '36 mm', 'cpx_y - 0.8 mm', 'cpx_z + 5 mm', '14 mm', '1.6 mm', '14 mm', 'FR4', 'Plastic - Matte (Blue)')
    C(mic, 'mic port', 'y', '36 mm', 'cpx_y + 0.5 mm', 'cpx_z + 12 mm', '3.5 mm', '1 mm', 'Steel', STEEL)
    C(mic, 'M2 standoff', 'y', '36 mm', '(cpx_y - 1.6 mm) - 1 mm - 0.5 mm', 'cpx_z + 12 mm', '4 mm', '3 mm', 'Copper, Alloy', BRASS)
    log('cpx ok')


def l1_boards():
    c = fresh('Power distribution board + INA226')
    x, y = '-62 mm', '-78 mm'
    z = 'l1_top + 6 mm'
    B(c, 'PDB perfboard 80x50', x, y, z, '80 mm', '50 mm', '1.6 mm', 'FR4', GREEN)
    for hx in (-1, 1):
        for hy in (-1, 1):
            C(c, 'M3 standoff 6', 'z', '(%s) + %d*36 mm' % (x, hx), '(%s) + %d*21 mm' % (y, hy), 'l1_top + 3 mm', '5.5 mm', '6 mm', 'Copper, Alloy', BRASS)
    pz = '(%s) + 1.6 mm' % z
    B(c, 'XT60 in (from loop key)', '(%s) - 30 mm' % x, '(%s) - 16 mm' % y, pz, '16 mm', '15.6 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    for k in range(4):
        B(c, 'XT30 out', '(%s) - 8 mm + %d*14 mm' % (x, k), '(%s) + 18 mm' % y, pz, '10.2 mm', '8 mm', '5.5 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    B(c, 'INA226 20 A module (26x22, 2 mOhm shunt)', '(%s) - 8 mm' % x, '(%s) - 10 mm' % y, pz, '26 mm', '22 mm', '1.6 mm', 'FR4', 'Plastic - Matte (Blue)')
    B(c, 'shunt', '(%s) - 8 mm' % x, '(%s) - 16 mm' % y, '(%s) + 1.6 mm' % pz, '12 mm', '4 mm', '2 mm', 'Copper', 'Copper - Polished')
    B(c, 'bus bar 12 V', '(%s) + 4 mm' % x, '(%s) + 6 mm' % y, pz, '60 mm', '4 mm', '3 mm', 'Copper', 'Copper - Polished')
    i = fresh('BNO085 IMU (Adafruit 4754)')
    B(i, 'BNO085 PCB', '0 mm', '-10 mm', 'l1_top + 5 mm', '25.4 mm', '22.86 mm', '1.6 mm', 'FR4', GLOSSB)
    B(i, 'BNO085 chip', '0 mm', '-10 mm', 'l1_top + 6.6 mm', '5.2 mm', '3.8 mm', '1.1 mm', 'Steel', BLACK)
    for hx in (-1, 1):
        for hy in (-1, 1):
            C(i, 'M2.5 standoff 5', 'z', '%d*10.16 mm' % hx, '-10 mm + %d*8.89 mm' % hy, 'l1_top + 2.5 mm', '4.5 mm', '5 mm', 'Copper, Alloy', BRASS)
    a = fresh('Audio MAX98357A + speaker')
    B(a, 'MAX98357A PCB (Adafruit 3006)', '-100 mm', '30 mm', 'l1_top + 4 mm', '17.8 mm', '19.3 mm', '1.6 mm', 'FR4', GLOSSB)
    for hy in (-1, 1):
        C(a, 'M2.5 standoff 4', 'z', '-100 mm', '30 mm + %d*7 mm' % hy, 'l1_top + 2 mm', '4.5 mm', '4 mm', 'Copper, Alloy', BRASS)
    # 40 mm speaker facing the left wall grille
    sx = '-(shell_x - pwall - 1 mm)'
    C(a, 'speaker 40 mm 4 ohm (Adafruit 3968)', 'x', '(%s) + 11 mm' % sx, '-20 mm', 'l1_top + 34 mm', '40 mm', '20 mm', 'Steel', BLACK)
    C(a, 'speaker cone', 'x', '(%s) + 0.6 mm' % sx, '-20 mm', 'l1_top + 34 mm', '34 mm', '1 mm', 'Paper', 'Plastic - Matte (Gray)')
    br = B(a, 'speaker bracket (printed)', '(%s) + 24 mm' % sx, '-20 mm', 'l1_top', '6 mm', '46 mm', '62 mm', 'PET Plastic', BLACK)
    bf = B(a, 'bracket foot', '(%s) + 32 mm' % sx, '-20 mm', 'l1_top', '18 mm', '46 mm', '4 mm', 'PET Plastic', BLACK)
    join(a, br, [bf], 'speaker bracket (printed)')
    C(a, 'magnet clearance', 'x', '(%s) + 24 mm' % sx, '-20 mm', 'l1_top + 34 mm', '24 mm', '8 mm', op=CUT, bodies=[br])
    log('L1 boards ok')


def servo_buck():
    c = fresh('Servo 6 V buck (Pololu D36V28F6)')
    x, z = '-60 mm', 'top_deck_z - 40 mm'
    y0 = 'spine_y - deck_t - 5 mm'
    B(c, 'D36V28F6 PCB (EST 17.8x20.3)', x, '(%s) - 0.8 mm' % y0, '(%s) - 10 mm' % z, '17.8 mm', '1.6 mm', '20.3 mm', 'FR4', GREEN)
    B(c, 'inductor', x, '(%s) - 1.6 mm - 2.5 mm' % y0, '(%s) - 5 mm' % z, '7 mm', '5 mm', '7 mm', 'Steel', BLACK)
    C(c, 'M2 standoff 5', 'y', x, 'spine_y - deck_t - 2.5 mm', '(%s) + 6 mm' % z, '4 mm', '5 mm', 'Copper, Alloy', BRASS)
    log('servo buck ok')


def loop_key():
    c = fresh('Main power XT60 loop key')
    yw = '-(shell_y - pwall)'
    hb = B(c, 'loop key bracket (printed)', 'key_x', '(%s) + 10 mm' % yw, 'key_z - 14 mm', '34 mm', '4 mm', 'top_deck_z - (key_z - 14 mm)', 'PET Plastic', BLACK)
    hf = B(c, 'bracket flange', 'key_x', '(%s) + 18 mm' % yw, 'top_deck_z - 4 mm', '34 mm', '16 mm', '4 mm', 'PET Plastic', BLACK)
    join(c, hb, [hf], 'loop key bracket (printed)')
    B(c, 'XT60 window', 'key_x', '(%s) + 10 mm' % yw, 'key_z - 4.3 mm', '16.4 mm', '6 mm', '8.6 mm', op=CUT, bodies=[hb])
    B(c, 'XT60 female panel socket', 'key_x', '(%s) + 4 mm' % yw, 'key_z - 4.1 mm', '16 mm', '16 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    k = B(c, 'loop key (XT60 male + wire loop)', 'key_x', '(%s) - 8 mm' % yw, 'key_z - 4.1 mm', '16 mm', '16 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Red)')
    g = B(c, 'loop key grip', 'key_x', '(%s) - 20 mm' % yw, 'key_z - 6 mm', '20 mm', '8 mm', '12 mm', 'ABS Plastic', 'Plastic - Matte (Red)')
    join(c, k, [g], 'loop key (XT60 male + wire loop)')
    log('loop key ok')


def main(parts=('pi', 'buck', 'esp', 'cpx', 'l1', 'servo', 'key')):
    define()
    if 'pi' in parts:
        pi_stack()
    if 'buck' in parts:
        pi_buck()
    if 'esp' in parts:
        esp32()
    if 'cpx' in parts:
        cpx_mic()
    if 'l1' in parts:
        l1_boards()
    if 'servo' in parts:
        servo_buck()
    if 'key' in parts:
        loop_key()
    done()
