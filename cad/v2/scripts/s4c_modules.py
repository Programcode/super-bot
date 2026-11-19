# Stage 4c: the off-the-shelf module blocks (19 Nov 2026: v2 goes back to modules; the custom main board is
# parked). Positions are the 17 Nov module layout, which passed the clearance and chimney review:
#   spine front, low: perfboard with 4x Pololu DRV8874 carriers (left) and the ESP32-S3-DevKitC-1 in a
#     printed cradle (right), both under the Pi 5 stack (s4_electronics)
#   spine back: Pololu D36V50F5 5 V 5.5 A buck behind the Pi's USB-C (top-left in pose B; lead via the centre slot)
#   right cheek outer face: power distribution perfboard (XT60 in, 4x XT30 out, 12 V bus bar) + INA226 module,
#     above the empty spare-ESP32 cradle and next to the loop key (short main feed)
#   left cheek outer face: MAX98357A amp and the Pololu D36V28F6 6 V servo buck, next to the speaker
#   upper back: XT60 loop key (XT60E-F panel socket + male key with a wire loop)
PARAMS4C = [('drv_z', 'plate_top + 46 mm', 'Driver perfboard bottom Z (above the front motors)')]


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
    for tag, fitted in (('A', True),):
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


def modules_back():
    c = fresh('Pi 5 V 5.5 A buck (Pololu D36V50F5)')
    x, z = '(pi_xc - 42.5 mm) + 22 mm', 'pi_z0 + 44 mm'   # behind the Pi's USB-C, which is at the top in pose B
    yb = 'spine_y - ply_t - 4 mm'
    B(c, 'D36V50F5 PCB', x, '(%s) - 0.8 mm' % yb, '(%s) - 12.7 mm' % z, '25.4 mm', '1.6 mm', '25.4 mm', 'FR4', GREEN)
    B(c, 'inductor', x, '(%s) - 1.6 mm - 3.95 mm' % yb, '(%s) - 6 mm' % z, '12 mm', '7.9 mm', '12 mm', 'Steel', BLACK)
    C(c, 'M2 standoff 4', 'y', '(%s) - 10.55 mm' % x, 'spine_y - ply_t - 2 mm', '(%s) + 10.55 mm' % z, '4 mm', '4 mm', 'Copper, Alloy', BRASS)
    C(c, 'M2 standoff 4 b', 'y', '(%s) + 10.55 mm' % x, 'spine_y - ply_t - 2 mm', '(%s) - 10.55 mm' % z, '4 mm', '4 mm', 'Copper, Alloy', BRASS)
    # right cheek (19 Nov: moved from the left, next to the loop key, above the spare ESP32 cradle):
    # PDB + INA226, board in the YZ plane, connectors toward the right wall
    p = fresh('Power distribution board + INA226')
    xb = 'cheek_x + ply_t + 5 mm'
    yc, z0 = '-5 mm', 'plate_top + 130 mm'
    B(p, 'PDB perfboard 80x50', '(%s) + 0.8 mm' % xb, yc, z0, '1.6 mm', '80 mm', '50 mm', 'FR4', GREEN)
    for hy in (-1, 1):
        for hz in (-1, 1):
            C(p, 'M3 standoff 5', 'x', 'cheek_x + ply_t + 2.5 mm', '(%s) + %d*36 mm' % (yc, hy), '(%s) + 25 mm + %d*21 mm' % (z0, hz), '5.5 mm', '5 mm', 'Copper, Alloy', BRASS)
    px = '(%s) + 1.6 mm' % xb
    B(p, 'XT60 in (from the loop key)', '(%s) + 4.1 mm' % px, '(%s) - 26 mm' % yc, '(%s) + 2 mm' % z0, '8.2 mm', '16 mm', '16 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')   # mates from below
    for k in range(4):
        B(p, 'XT30 out', '(%s) + 2.75 mm' % px, '(%s) - 12 mm + %d*12.5 mm' % (yc, k), '(%s) + 38 mm' % z0, '5.5 mm', '10.2 mm', '8 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    B(p, 'INA226 20 A module (26x22, 2 mOhm shunt)', '(%s) + 0.8 mm' % px, '(%s) + 9 mm' % yc, '(%s) + 2 mm' % z0, '1.6 mm', '26 mm', '22 mm', 'FR4', 'Plastic - Matte (Blue)')
    B(p, 'bus bar 12 V', '(%s) + 1.5 mm' % px, '(%s) + 5 mm' % yc, '(%s) + 28 mm' % z0, '3 mm', '60 mm', '4 mm', 'Copper', 'Copper - Polished')
    # left cheek (19 Nov: moved from the right, next to the speaker): MAX98357A + servo buck
    a = fresh('Audio MAX98357A (Adafruit 3006)')
    xr = '-(cheek_x + ply_t + 4 mm)'
    B(a, 'MAX98357A PCB (Adafruit 3006)', '(%s) - 0.8 mm' % xr, '20 mm', 'plate_top + 150 mm', '1.6 mm', '17.8 mm', '19.3 mm', 'FR4', GLOSSB)
    C(a, 'M2.5 standoff 4', 'x', '-(cheek_x + ply_t + 2 mm)', '20 mm', 'plate_top + 160 mm', '4.5 mm', '4 mm', 'Copper, Alloy', BRASS)
    s = fresh('Servo 6 V buck (Pololu D36V28F6)')
    B(s, 'D36V28F6 PCB (20.3x17.8)', '(%s) - 0.8 mm' % xr, '-30 mm', 'plate_top + 150 mm', '1.6 mm', '20.3 mm', '17.8 mm', 'FR4', GREEN)
    B(s, 'inductor', '(%s) - 1.6 mm - 2.5 mm' % xr, '-30 mm', 'plate_top + 155 mm', '5 mm', '7 mm', '7 mm', 'Steel', BLACK)
    C(s, 'M2 standoff 4', 'x', '-(cheek_x + ply_t + 2 mm)', '-30 mm', 'plate_top + 159 mm', '4 mm', '4 mm', 'Copper, Alloy', BRASS)
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


def main(parts=('drv', 'esp', 'back')):
    for n, e, cm in PARAMS4C:
        param(n, e, cm)
    if 'drv' in parts:
        driver_board()
    if 'esp' in parts:
        esp32()
    if 'back' in parts:
        modules_back()
    done()
