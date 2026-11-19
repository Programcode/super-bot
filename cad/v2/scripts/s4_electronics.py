# Stage 4: the Pi stack, front light, IMU and speaker. 19 Nov 2026 (Adam): v2 uses off-the-shelf modules,
# not the custom main board (hw/main-board stays parked as a future option); the module blocks are in
# s4c_modules.py. Spine front (the chimney, seen through the front wall): DRV8874 perfboard + ESP32-S3 low
# (s4c), Raspberry Pi 5 + Active Cooler + AI HAT+ 2 above them, and the Circuit Playground Express on a
# printed bracket right behind the front wall, so its 10 NeoPixels show through the smoked shell.
# Spine back: BNO085 (5 V buck: s4c). Right cheek: empty cradle for a second ESP32-S3. Rear plate: 40 mm speaker.

OLD = ['Main board rev A (hw-main-board)', 'Main board keep-outs (plug + cable bend)', 'Main power XT30 loop key']

PARAMS4 = [
    ('pi_xc', '-5 mm', 'Pi 5 PCB centre X (module layout: USB/Ethernet edge faces +X)'),
    ('pi_z0', 'plate_top + 104 mm', 'Pi 5 PCB bottom (GPIO) edge Z, above the driver board and ESP32 (pose B)'),
    ('pi_so', '6 mm', 'Pi standoffs off the spine'),
    ('pi_y0', 'spine_y + pi_so', 'Pi PCB back face Y'),
    ('hat_so', '16 mm', 'AI HAT+ 2 spacer height (SRC)'),
    ('cpx_z', 'top_deck_z - 26 mm', 'CPX centre Z (front status light)'),
    ('cpx_yf', 'shell_y - pwall - 2.5 mm', 'CPX NeoPixel tops, 2.5 mm behind the front wall'),
]


def define():
    for n, e, cm in PARAMS4:
        param(n, e, cm)


def remove_old():
    n = 0
    for nm in OLD:
        o = find_occ(nm)
        if o:
            o.deleteMe()
            n += 1
    log('removed old module components', n)


def pi_box(c, name, u, v, wu, hv, t, yb, mat, look, op=NEWB, bodies=None):
    """Box in Pi board coordinates (real Pi 5 frame: component side up, GPIO edge on top, u to the right
    from the USB-C end, v up from the HDMI edge). Pose B (19 Nov, matches the official Pi 5 STEP):
    components face the front wall, u -> +X (USB/Ethernet toward the right wall), v -> -Z, so the
    GPIO header + AI HAT+ 2 sit along the BOTTOM edge (pi_z0) and USB-C / HDMI along the top (pi_z0 + 56).
    yb from the PCB front face -> +Y. u, v = the box's low corner. (Before 19 Nov v ran -> +Z: a mirror image.)"""
    x = '(pi_xc - 42.5 mm) + (%s) + (%s)/2' % (u, wu)
    z = 'pi_z0 + 56 mm - (%s) - (%s)/2' % (v, hv)
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
    pi_box(c, 'PCIe FFC', '0.5 mm', '24.6 mm', '3 mm', '10.7 mm', '1.2 mm', '0 mm', 'ABS Plastic', 'Plastic - Matte (White)')   # official drawing
    pi_box(c, 'fan connector (JST-SH 4)', '65.25 mm', '48.85 mm', '3.1 mm', '6.1 mm', '4.25 mm', '0 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    pi_box(c, 'Active Cooler', '3.5 mm', '17 mm', '57 mm', '31 mm', '13.7 mm', '0 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    for hu in ('3.5 mm', '61.5 mm'):
        for hv in ('3.5 mm', '52.5 mm'):
            x = '(pi_xc - 42.5 mm) + %s' % hu
            z = 'pi_z0 + 56 mm - %s' % hv
            C(c, 'M2.5 standoff 6', 'y', x, 'spine_y + pi_so/2', z, '5 mm', 'pi_so', 'Copper, Alloy', BRASS)
            C(c, 'M2.5 spacer 16', 'y', x, 'pi_y0 + 1.4 mm + hat_so/2', z, '5 mm', 'hat_so', 'Copper, Alloy', BRASS)
    h = fresh('Raspberry Pi AI HAT+ 2 (Hailo-10H)')
    hb = 'hat_so'
    hp = pi_box(h, 'AI HAT+ 2 PCB', '0 mm', '56 mm - 56.5 mm', '65 mm', '56.5 mm', '1.6 mm', hb, 'FR4', GREEN)
    pi_box(h, 'ribbon cut-out', '47.5 mm', '-1 mm', '10 mm', '17 mm', '4 mm', '(%s) - 1 mm' % hb, None, None, op=CUT, bodies=[hp])
    hs = pi_box(h, 'HAT heatsink (EST 42x37)', '3 mm', '10 mm', '42 mm', '37 mm', '14 mm', '(%s) + 1.6 mm' % hb, 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    for k in range(5):
        pi_box(h, 'fin slot', '3 mm + 4 mm + %d*8 mm' % k, '9 mm', '4 mm', '44 mm', '12 mm', '(%s) + 3.6 mm' % hb, None, None, op=CUT, bodies=[hs])
    pi_box(h, 'GPIO stacking header', '7 mm', '56 mm - 6 mm', '51 mm', '5 mm', '8.5 mm', '(%s) + 1.6 mm' % hb, 'ABS Plastic', BLACK)
    log('pi ok, stack front y =', mm('pi_y0 + 1.4 mm + hat_so + 1.6 mm + 14 mm'))


def cpx_front():
    """Adafruit Circuit Playground Express (~50.6 mm round board, 10 NeoPixels on r 17.15 at
    0/30/60/120/150/180/210/240/300/330 deg), LEDs facing the front wall, on a printed bracket hung
    from the top deck. Cable from the main board CPX connector J404 (+5V, GND, CPX_RX, CPX_KILL):
    +5V/GND into the CPX's JST-PH battery input (3.5-6 V), CPX_RX to pad A6 (RX), CPX_KILL from pad A1."""
    c = fresh('Circuit Playground Express (front status light)')
    yp = 'cpx_yf - 0.5 mm - 1.6 mm'                 # PCB back face
    C(c, 'CPX PCB', 'y', '0 mm', '(%s) + 0.8 mm' % yp, 'cpx_z', '50.6 mm', '1.6 mm', 'FR4', GLOSSB)
    led = appearance('SB NeoPixel glow', 'LED - SMD 5050 - 20lm (White)')
    for a in (0, 30, 60, 120, 150, 180, 210, 240, 300, 330):
        r = math.radians(a)
        b = B(c, 'NeoPixel', '%.4f*17.15 mm' % math.cos(r), '(%s) + 1.6 mm + 0.25 mm' % yp, 'cpx_z - 1.75 mm + %.4f*17.15 mm' % math.sin(r),
              '3.5 mm', '0.5 mm', '3.5 mm', 'ABS Plastic')
        finish(b, None, led)
    B(c, 'USB micro', '0 mm', '(%s) + 1.6 mm + 1.5 mm' % yp, 'cpx_z + 19 mm', '7.5 mm', '3 mm', '5 mm', 'Steel', STEEL)
    B(c, 'JST-PH battery input (rear)', '0 mm', '(%s) - 3 mm' % yp, 'cpx_z - 22 mm', '8 mm', '6 mm', '6 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    for bx in (-1, 1):
        B(c, 'button', '%d*13 mm' % bx, '(%s) + 1.6 mm + 1 mm' % yp, 'cpx_z - 3 mm', '6 mm', '2 mm', '6 mm', 'ABS Plastic', BLACK)
    # plate behind the CPX; two 9 mm legs up to the top deck, landing between the chimney vent slots
    br = B(c, 'CPX bracket (printed)', '0 mm', '(%s) - 4 mm - 2 mm' % yp, 'cpx_z - 14 mm', '60 mm', '4 mm', '34 mm', 'PET Plastic', BLACK)   # 19 Nov: bottom raised 6 mm, clear of the CPX battery JST plug
    legs = []
    for sx in (1, -1):
        legs.append(B(c, 'leg', S(sx, '9 mm'), '(%s) - 4 mm - 2 mm' % yp, 'cpx_z + 20 mm', '9 mm', '4 mm', 'top_deck_z - (cpx_z + 20 mm)'))
        legs.append(B(c, 'foot', S(sx, '9 mm'), '(%s) - 6 mm - 6 mm' % yp, 'top_deck_z - 4 mm', '9 mm', '12 mm', '4 mm'))
    join(c, br, legs, 'CPX bracket (printed)')
    C(c, 'pad cable hole', 'y', '0 mm', '(%s) - 4 mm' % yp, 'cpx_z', '14 mm', '6 mm', op=CUT, bodies=[br])
    for k in (-1, 1):
        C(c, 'M3 standoff 4', 'y', '%d*21.6 mm' % k, '(%s) - 2 mm' % yp, 'cpx_z', '5 mm', '4 mm', 'Copper, Alloy', BRASS)
    log('cpx ok')


def spare_cradle():
    c = fresh('ESP32-S3 spare cradle (empty)')
    cr = B(c, 'printed cradle (empty, for a second ESP32-S3 later)', 'cheek_x + ply_t + 4.5 mm', '-8 mm', 'plate_top + 54 mm', '9 mm', '66 mm', '29.4 mm', 'PET Plastic', BLACK)
    B(c, 'header pocket', 'cheek_x + ply_t + 6.5 mm', '-8 mm', 'plate_top + 56 mm', '8 mm', '64 mm', '25.4 mm', op=CUT, bodies=[cr])
    cr.name = 'printed cradle (empty, for a second ESP32-S3 later)'


def back_side():
    i = fresh('BNO085 IMU (Adafruit 4754)')
    yb = 'spine_y - ply_t - 5 mm'
    B(i, 'BNO085 PCB', '0 mm', '(%s) - 0.8 mm' % yb, 'plate_top + 82 mm', '25.4 mm', '1.6 mm', '22.86 mm', 'FR4', GLOSSB)
    B(i, 'BNO085 chip', '0 mm', '(%s) - 2.1 mm' % yb, 'plate_top + 91 mm', '5.2 mm', '1.1 mm', '3.8 mm', 'Steel', BLACK)
    for hx in (-1, 1):
        for hz in (-1, 1):
            C(i, 'M2.5 standoff 5', 'y', '%d*10.16 mm' % hx, 'spine_y - ply_t - 2.5 mm', 'plate_top + 82 mm + 11.43 mm + %d*8.89 mm' % hz, '4.5 mm', '5 mm', 'Copper, Alloy', BRASS)
    a = fresh('Speaker 40 mm (Adafruit 3968)')
    C(a, 'speaker 40 mm 4 ohm (Adafruit 3968)', 'y', '-45 mm', '-(shell_y - pwall - 11 mm)', 'body_top - 70 mm', '40 mm', '20 mm', 'Steel', BLACK)
    C(a, 'speaker cone', 'y', '-45 mm', '-(shell_y - pwall - 0.6 mm)', 'body_top - 70 mm', '34 mm', '1 mm', 'Paper', 'Plastic - Matte (Gray)')
    br = B(a, 'speaker bracket (printed)', '-45 mm', '-(shell_y - pwall - 23 mm)', 'body_top - 96 mm', '50 mm', '4 mm', '52 mm', 'PET Plastic', BLACK)
    bf = B(a, 'bracket foot', '-45 mm', '(rear_y - ply_t + (-(shell_y - pwall - 21 mm)))/2', 'body_top - 96 mm', '50 mm',
           '(rear_y - ply_t) - (-(shell_y - pwall - 21 mm))', '4 mm', 'PET Plastic', BLACK)
    join(a, br, [bf], 'speaker bracket (printed)')
    C(a, 'magnet clearance', 'y', '-45 mm', '-(shell_y - pwall - 23 mm)', 'body_top - 70 mm', '24 mm', '6 mm', op=CUT, bodies=[br])
    log('back side ok')


def main(parts=('old', 'pi', 'cpx', 'spare', 'back')):
    define()
    if 'old' in parts:
        remove_old()
    if 'pi' in parts:
        pi_stack()
    if 'cpx' in parts:
        cpx_front()
    if 'spare' in parts:
        spare_cradle()
    if 'back' in parts:
        back_side()
    done()
