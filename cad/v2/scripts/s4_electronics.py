# Stage 4: electronics, packed flat on the frame plates.
# Spine front (seen through the front wall, the chimney): motor-driver board (4x DRV8874) and
#   ESP32-S3 low, Raspberry Pi 5 + Active Cooler + AI HAT+ 2 in the middle (ports face +X),
#   CPX on top, LED bar (8x WS2812B behind a diffuser slot in the front wall) at the top.
# Spine back: 5 V 5.5 A buck right behind the Pi's USB-C, BNO085.
# Left cheek: power distribution board + INA226. Right cheek: empty cradle for a 2nd ESP32,
#   MAX98357A, servo 6 V buck. Rear plate back: 40 mm speaker (rear grille), XT60 loop key.

PARAMS4 = [
    ('pi_xc', '-5 mm', 'Pi 5 PCB centre X (USB/Ethernet edge faces +X, ~40 mm plug room)'),
    ('pi_z0', 'plate_top + 104 mm', 'Pi 5 PCB bottom (HDMI/USB-C) edge Z'),
    ('pi_so', '6 mm', 'Pi standoffs off the spine'),
    ('pi_y0', 'spine_y + pi_so', 'Pi PCB back face Y'),
    ('hat_so', '16 mm', 'AI HAT+ 2 spacer height (SRC)'),
    ('drv_z', 'plate_top + 46 mm', 'Driver board bottom Z (above the front motors)'),
    ('cpx_z', 'pi_z0 + 92 mm', 'CPX centre Z'),
]


def define():
    for n, e, cm in PARAMS4:
        param(n, e, cm)


def pi_box(c, name, u, v, wu, hv, t, yb, mat, look, op=NEWB, bodies=None):
    """Box in Pi board coordinates: u from the left (USB-C) edge -> +X, v from the HDMI edge -> +Z,
    yb from the PCB front face -> +Y. u, v = the box's low corner."""
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
    pi_box(c, 'GPIO 2x20 header', '7 mm', '56 mm - 6 mm', '51 mm', '5 mm', '8.5 mm', '0 mm', 'ABS Plastic', BLACK)
    pi_box(c, 'PCIe FFC', '0.5 mm', '20 mm', '3 mm', '15 mm', '1.2 mm', '0 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    pi_box(c, 'Active Cooler', '3.5 mm', '8 mm', '57 mm', '40 mm', '13.7 mm', '0 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    for hu in ('3.5 mm', '61.5 mm'):
        for hv in ('3.5 mm', '52.5 mm'):
            x = '(pi_xc - 42.5 mm) + %s' % hu
            z = 'pi_z0 + %s' % hv
            C(c, 'M2.5 standoff 6', 'y', x, 'spine_y + pi_so/2', z, '5 mm', 'pi_so', 'Copper, Alloy', BRASS)
            C(c, 'M2.5 spacer 16', 'y', x, 'pi_y0 + 1.4 mm + hat_so/2', z, '5 mm', 'hat_so', 'Copper, Alloy', BRASS)
    h = fresh('Raspberry Pi AI HAT+ 2 (Hailo-10H)')
    hb = 'hat_so'
    hp = pi_box(h, 'AI HAT+ 2 PCB', '0 mm', '56 mm - 56.5 mm', '65 mm', '56.5 mm', '1.6 mm', hb, 'FR4', GREEN)
    pi_box(h, 'ribbon cut-out', '47.5 mm', '-1 mm', '10 mm', '17 mm', '4 mm', '(%s) - 1 mm' % hb, None, None, op=CUT, bodies=[hp])
    hs = pi_box(h, 'HAT heatsink (EST 42x42)', '3 mm', '10 mm', '42 mm', '42 mm', '14 mm', '(%s) + 1.6 mm' % hb, 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    for k in range(5):
        pi_box(h, 'fin slot', '3 mm + 4 mm + %d*8 mm' % k, '9 mm', '4 mm', '44 mm', '12 mm', '(%s) + 3.6 mm' % hb, None, None, op=CUT, bodies=[hs])
    C(h, 'heatsink fan hub (look)', 'y', '(pi_xc - 42.5 mm) + 24 mm', 'pi_y0 + 1.4 mm + hat_so + 1.6 mm + 14.2 mm', 'pi_z0 + 31 mm', '14 mm', '0.4 mm', 'ABS Plastic', BLACK)
    pi_box(h, 'GPIO stacking header', '7 mm', '56 mm - 6 mm', '51 mm', '5 mm', '8.5 mm', '(%s) + 1.6 mm' % hb, 'ABS Plastic', BLACK)
    log('pi ok, stack front y =', mm('pi_y0 + 1.4 mm + hat_so + 1.6 mm + 14 mm'))


def driver_board():
    c = fresh('Motor driver board 4x DRV8874')
    xc, z0 = '-45 mm', 'drv_z'
    yb = 'spine_y + 8 mm'
    B(c, 'perfboard 70x40', xc, '(%s) + 0.8 mm' % yb, z0, '70 mm', '1.6 mm', '40 mm', 'FR4', GREEN)
    for hx in (-1, 1):
        for hz in (-1, 1):
            C(c, 'M3 standoff 8', 'y', '(%s) + %d*31 mm' % (xc, hx), 'spine_y + 4 mm', '(%s) + 20 mm + %d*16 mm' % (z0, hz), '5.5 mm', '8 mm', 'Copper, Alloy', BRASS)
    py = '(%s) + 1.6 mm' % yb
    for i in range(4):
        x = '(%s) + (%d - 1.5)*16.5 mm' % (xc, i)
        B(c, 'female headers', x, '(%s) + 4.25 mm' % py, '(%s) + 14 mm' % z0, '15 mm', '8.5 mm', '15 mm', 'ABS Plastic', BLACK)
        B(c, 'DRV8874 carrier (Pololu 4035)', x, '(%s) + 8.5 mm + 0.8 mm' % py, '(%s) + 12 mm' % z0, '15.2 mm', '1.6 mm', '17.8 mm', 'FR4', GREEN)
        B(c, 'DRV8874 chip', x, '(%s) + 8.5 mm + 1.6 mm + 0.5 mm' % py, '(%s) + 18 mm' % z0, '5 mm', '1 mm', '5 mm', 'Steel', BLACK)
    B(c, 'motor terminals', xc, '(%s) + 5 mm' % py, '(%s) + 1 mm' % z0, '64 mm', '10 mm', '7.5 mm', 'ABS Plastic', 'Plastic - Matte (Green)')
    B(c, 'XT30 12V in', '(%s) + 28 mm' % xc, '(%s) + 2.75 mm' % py, '(%s) + 32 mm' % z0, '10 mm', '5.5 mm', '8 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    B(c, 'JST-XH logic 10p', '(%s) - 10 mm' % xc, '(%s) + 3.5 mm' % py, '(%s) + 33 mm' % z0, '27 mm', '7 mm', '6 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    log('driver ok')


def esp32():
    for tag, fitted in (('A', True), ('B spare', False)):
        c = fresh('ESP32-S3-DevKitC-1 %s' % tag)
        if fitted:   # on the spine front, horizontal, USB-C toward +X
            xc, zc = '50 mm', 'drv_z + 20 mm'
            cr = B(c, 'printed cradle', xc, 'spine_y + 4.5 mm', '(%s) - 14.7 mm' % zc, '66 mm', '9 mm', '29.4 mm', 'PET Plastic', BLACK)
            B(c, 'header pocket', xc, 'spine_y + 6.5 mm', '(%s) - 12.7 mm' % zc, '64 mm', '8 mm', '25.4 mm', op=CUT, bodies=[cr])
            cr.name = 'printed cradle'
            pz = 'spine_y + 9 mm'
            for dz in ('-11.43 mm', '11.43 mm'):
                B(c, 'pin header', xc, 'spine_y + 5.5 mm', '(%s) + %s - 1.27 mm' % (zc, dz), '55 mm', '7 mm', '2.54 mm', 'ABS Plastic', BLACK)
            B(c, 'DevKitC PCB', xc, '(%s) + 0.8 mm' % pz, '(%s) - 12.7 mm' % zc, '62.74 mm', '1.6 mm', '25.4 mm', 'FR4', GLOSSB)
            B(c, 'WROOM-1 module', '(%s) - 62.74 mm/2 + 25.5 mm/2' % xc, '(%s) + 1.6 mm + 1.55 mm' % pz, '(%s) - 9 mm' % zc, '25.5 mm', '3.1 mm', '18 mm', 'Steel', STEEL)
            for oz in ('-4.5 mm', '4.5 mm'):
                B(c, 'USB-C', '(%s) + 62.74 mm/2 - 7.4 mm/2 + 1 mm' % xc, '(%s) + 1.6 mm + 1.6 mm' % pz, '(%s) + %s - 4.45 mm' % (zc, oz), '7.4 mm', '3.2 mm', '8.9 mm', 'Steel', STEEL)
        else:        # on the right cheek, outer face, along Y
            cr = B(c, 'printed cradle (empty, for a second ESP32-S3 later)', 'cheek_x + ply_t + 4.5 mm', '-8 mm', 'plate_top + 92 mm', '9 mm', '66 mm', '29.4 mm', 'PET Plastic', BLACK)
            B(c, 'header pocket', 'cheek_x + ply_t + 6.5 mm', '-8 mm', 'plate_top + 94 mm', '8 mm', '64 mm', '25.4 mm', op=CUT, bodies=[cr])
            cr.name = 'printed cradle (empty, for a second ESP32-S3 later)'
    log('esp ok')


def cpx_bar():
    c = fresh('Circuit Playground Express + LED bar')
    yb = 'spine_y + 6 mm'
    C(c, 'CPX PCB', 'y', 'pi_xc', '(%s) + 0.8 mm' % yb, 'cpx_z', '50.8 mm', '1.6 mm', 'FR4', GLOSSB)
    led = appearance('SB NeoPixel glow', 'LED - SMD 5050 - 20lm (White)')
    for a in (0, 30, 60, 120, 150, 180, 210, 240, 300, 330):
        r = math.radians(a)
        b = B(c, 'CPX NeoPixel', '(pi_xc) + %.4f*17.15 mm' % math.cos(r), '(%s) + 1.6 mm + 0.5 mm' % yb, 'cpx_z - 1.75 mm + %.4f*17.15 mm' % math.sin(r), '3.5 mm', '1 mm', '3.5 mm', 'ABS Plastic')
        finish(b, None, led)
    for k in (-1, 1):
        C(c, 'M3 standoff 6', 'y', '(pi_xc) + %d*21.6 mm' % k, 'spine_y + 3 mm', 'cpx_z', '5 mm', '6 mm', 'Copper, Alloy', BRASS)
    # LED bar: 8x WS2812B (133 mm of 60 LED/m strip) on a printed carrier hung from the top deck,
    # a frosted diffuser in the wall slot and a black bezel on the outside
    sy = 'shell_y - pwall - 3.5 mm'
    car = B(c, 'LED bar carrier (printed)', '0 mm', '(%s) - 1.5 mm' % sy, 'bar_z - 9 mm', '144 mm', '3 mm', '18 mm', 'PET Plastic', BLACK)
    legs = [B(c, 'carrier leg', S(sx, '30 mm'), '(%s) - 1.5 mm' % sy, 'bar_z + 9 mm', '8 mm', '3 mm', 'top_deck_z - (bar_z + 9 mm)') for sx in (1, -1)]
    legs += [B(c, 'carrier foot', S(sx, '30 mm'), '(%s) - 6 mm' % sy, 'top_deck_z - 3 mm', '8 mm', '12 mm', '3 mm') for sx in (1, -1)]
    join(c, car, legs, 'LED bar carrier (printed)')
    B(c, 'WS2812B strip 8 LEDs (133 mm, 60/m)', '0 mm', '(%s) + 0.15 mm' % sy, 'bar_z - 5 mm', '133 mm', '0.3 mm', '10 mm', 'FR4', BLACK)
    for i in range(8):
        b = B(c, 'bar LED', '(%d - 3.5)*16.67 mm' % i, '(%s) + 1.6 mm' % sy, 'bar_z - 2.5 mm', '5 mm', '2.5 mm', '5 mm', 'ABS Plastic')
        finish(b, None, led)
    d = B(c, 'LED bar diffuser (printed, frosted white)', '0 mm', 'shell_y - pwall/2', 'bar_z - 5.8 mm', 'bar_w - 0.4 mm', 'pwall', '11.6 mm', 'PET Plastic', 'SB Smoked PETG')
    bz = B(c, 'LED bar bezel (printed)', '0 mm', 'shell_y + 0.8 mm', 'bar_z - 10 mm', 'bar_w + 12 mm', '1.6 mm', '20 mm', 'PET Plastic', GLOSSB)
    fillet(c, edges_where(bz, lambda e: is_axis_line(e, 'y')), '9.9 mm')
    B(c, 'bezel opening', '0 mm', 'shell_y + 0.8 mm', 'bar_z - 5 mm', 'bar_w - 4 mm', '3 mm', '10 mm', op=CUT, bodies=[bz])
    log('cpx + bar ok')


def back_side():
    c = fresh('Pi 5 V 5.5 A buck (Pololu D36V50F5)')
    x, z = '(pi_xc - 42.5 mm) + 22 mm', 'pi_z0 + 14 mm'
    yb = 'spine_y - ply_t - 4 mm'
    B(c, 'D36V50F5 PCB', x, '(%s) - 0.8 mm' % yb, '(%s) - 12.7 mm' % z, '25.4 mm', '1.6 mm', '25.4 mm', 'FR4', GREEN)
    B(c, 'inductor', x, '(%s) - 1.6 mm - 3.95 mm' % yb, '(%s) - 6 mm' % z, '12 mm', '7.9 mm', '12 mm', 'Steel', BLACK)
    C(c, 'M2 standoff 4', 'y', '(%s) - 10.55 mm' % x, 'spine_y - ply_t - 2 mm', '(%s) + 10.55 mm' % z, '4 mm', '4 mm', 'Copper, Alloy', BRASS)
    C(c, 'M2 standoff 4 b', 'y', '(%s) + 10.55 mm' % x, 'spine_y - ply_t - 2 mm', '(%s) - 10.55 mm' % z, '4 mm', '4 mm', 'Copper, Alloy', BRASS)
    i = fresh('BNO085 IMU (Adafruit 4754)')
    yb = 'spine_y - ply_t - 5 mm'
    B(i, 'BNO085 PCB', '0 mm', '(%s) - 0.8 mm' % yb, 'plate_top + 82 mm', '25.4 mm', '1.6 mm', '22.86 mm', 'FR4', GLOSSB)
    B(i, 'BNO085 chip', '0 mm', '(%s) - 2.1 mm' % yb, 'plate_top + 91 mm', '5.2 mm', '1.1 mm', '3.8 mm', 'Steel', BLACK)
    for hx in (-1, 1):
        for hz in (-1, 1):
            C(i, 'M2.5 standoff 5', 'y', '%d*10.16 mm' % hx, 'spine_y - ply_t - 2.5 mm', 'plate_top + 82 mm + 11.43 mm + %d*8.89 mm' % hz, '4.5 mm', '5 mm', 'Copper, Alloy', BRASS)
    # left cheek: PDB + INA226 (board in the YZ plane, connectors toward the left wall)
    p = fresh('Power distribution board + INA226')
    xb = '-(cheek_x + ply_t + 5 mm)'
    yc, z0 = '-5 mm', 'plate_top + 88 mm'
    B(p, 'PDB perfboard 80x50', '(%s) - 0.8 mm' % xb, yc, z0, '1.6 mm', '80 mm', '50 mm', 'FR4', GREEN)
    for hy in (-1, 1):
        for hz in (-1, 1):
            C(p, 'M3 standoff 5', 'x', '-(cheek_x + ply_t + 2.5 mm)', '(%s) + %d*36 mm' % (yc, hy), '(%s) + 25 mm + %d*21 mm' % (z0, hz), '5.5 mm', '5 mm', 'Copper, Alloy', BRASS)
    px = '(%s) - 1.6 mm' % xb
    B(p, 'XT60 in (from the loop key)', '(%s) - 4.1 mm' % px, '(%s) - 26 mm' % yc, '(%s) + 32 mm' % z0, '8.2 mm', '16 mm', '16 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    for k in range(4):
        B(p, 'XT30 out', '(%s) - 2.75 mm' % px, '(%s) - 12 mm + %d*12.5 mm' % (yc, k), '(%s) + 4 mm' % z0, '5.5 mm', '10.2 mm', '8 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    B(p, 'INA226 20 A module (26x22, 2 mOhm shunt)', '(%s) - 0.8 mm' % px, '(%s) + 24 mm' % yc, '(%s) + 26 mm' % z0, '1.6 mm', '26 mm', '22 mm', 'FR4', 'Plastic - Matte (Blue)')
    B(p, 'bus bar 12 V', '(%s) - 1.5 mm' % px, '(%s) + 5 mm' % yc, '(%s) + 16 mm' % z0, '3 mm', '60 mm', '4 mm', 'Copper', 'Copper - Polished')
    # right cheek: MAX98357A + servo buck
    a = fresh('Audio MAX98357A + speaker')
    xr = 'cheek_x + ply_t + 4 mm'
    B(a, 'MAX98357A PCB (Adafruit 3006)', '(%s) + 0.8 mm' % xr, '20 mm', 'plate_top + 150 mm', '1.6 mm', '17.8 mm', '19.3 mm', 'FR4', GLOSSB)
    C(a, 'M2.5 standoff 4', 'x', 'cheek_x + ply_t + 2 mm', '20 mm', 'plate_top + 160 mm', '4.5 mm', '4 mm', 'Copper, Alloy', BRASS)
    # speaker on the rear plate's back face, firing through the rear grille
    C(a, 'speaker 40 mm 4 ohm (Adafruit 3968)', 'y', '-45 mm', '-(shell_y - pwall - 11 mm)', 'body_top - 70 mm', '40 mm', '20 mm', 'Steel', BLACK)
    C(a, 'speaker cone', 'y', '-45 mm', '-(shell_y - pwall - 0.6 mm)', 'body_top - 70 mm', '34 mm', '1 mm', 'Paper', 'Plastic - Matte (Gray)')
    br = B(a, 'speaker bracket (printed)', '-45 mm', '-(shell_y - pwall - 23 mm)', 'body_top - 96 mm', '50 mm', '4 mm', '52 mm', 'PET Plastic', BLACK)
    bf = B(a, 'bracket foot', '-45 mm', '(rear_y - ply_t + (-(shell_y - pwall - 21 mm)))/2', 'body_top - 96 mm', '50 mm',
           '(rear_y - ply_t) - (-(shell_y - pwall - 21 mm))', '4 mm', 'PET Plastic', BLACK)
    join(a, br, [bf], 'speaker bracket (printed)')
    C(a, 'magnet clearance', 'y', '-45 mm', '-(shell_y - pwall - 23 mm)', 'body_top - 70 mm', '24 mm', '6 mm', op=CUT, bodies=[br])
    s = fresh('Servo 6 V buck (Pololu D36V28F6)')
    B(s, 'D36V28F6 PCB (20.3x17.8)', '(%s) + 0.8 mm' % xr, '-30 mm', 'plate_top + 150 mm', '1.6 mm', '20.3 mm', '17.8 mm', 'FR4', GREEN)
    B(s, 'inductor', '(%s) + 1.6 mm + 2.5 mm' % xr, '-30 mm', 'plate_top + 155 mm', '5 mm', '7 mm', '7 mm', 'Steel', BLACK)
    C(s, 'M2 standoff 4', 'x', 'cheek_x + ply_t + 2 mm', '-30 mm', 'plate_top + 159 mm', '4 mm', '4 mm', 'Copper, Alloy', BRASS)
    # loop key on the upper back
    k = fresh('Main power XT60 loop key')
    yw = '-(shell_y - pwall)'
    kz = 'body_top - 40 mm'
    hb = B(k, 'loop key bracket (printed)', '50 mm', '(%s) + 9 mm' % yw, '(%s) - 14 mm' % kz, '34 mm', '4 mm', 'top_deck_z - ((%s) - 14 mm)' % kz, 'PET Plastic', BLACK)
    hf = B(k, 'bracket flange', '50 mm', '(%s) + 15 mm' % yw, 'top_deck_z - 4 mm', '34 mm', '12 mm', '4 mm', 'PET Plastic', BLACK)
    join(k, hb, [hf], 'loop key bracket (printed)')
    B(k, 'XT60 window', '50 mm', '(%s) + 9 mm' % yw, '(%s) - 4.3 mm' % kz, '16.4 mm', '6 mm', '8.6 mm', op=CUT, bodies=[hb])
    B(k, 'XT60 female panel socket (XT60E-F)', '50 mm', '(%s) + 4 mm' % yw, '(%s) - 4.1 mm' % kz, '16 mm', '16 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    kk = B(k, 'loop key (XT60 male + wire loop)', '50 mm', '(%s) - 6 mm' % yw, '(%s) - 4.1 mm' % kz, '16 mm', '12 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Red)')
    g = B(k, 'loop key grip', '50 mm', '(%s) - 16 mm' % yw, '(%s) - 6 mm' % kz, '20 mm', '8 mm', '12 mm', 'ABS Plastic', 'Plastic - Matte (Red)')
    join(k, kk, [g], 'loop key (XT60 male + wire loop)')
    log('back side ok')


def main(parts=('pi', 'drv', 'esp', 'cpx', 'back')):
    define()
    if 'pi' in parts:
        pi_stack()
    if 'drv' in parts:
        driver_board()
    if 'esp' in parts:
        esp32()
    if 'cpx' in parts:
        cpx_bar()
    if 'back' in parts:
        back_side()
    done()
