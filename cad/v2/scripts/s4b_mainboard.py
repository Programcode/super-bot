# Stage 4b: the main board (hw/main-board rev A) as a lightweight block, built from its own KiCad
# footprint data (main_board_parts.json, extracted with pcbnew): the 186 x 70 mm outline with the
# 24 x 8 mm notch, 4x M3 holes on brass standoffs off the spine, and every connector and large part
# at its real position with an estimated height. Plus, in a separate hidden component, a keep-out
# volume per connector for the mated plug and its cable bend: the interference check against those
# volumes is what proves (or disproves) connector access in the bay.
# Board mounting: flat on the spine front, components facing the front wall. KiCad x -> robot -X
# (the battery/power end at kx = 50 is on the robot's right), KiCad y (down) -> robot -Z.
import json

PARAMS4B = [
    ('mb_xr', '93 mm', 'Main board right edge X (KiCad x = 50, the battery end)'),
    ('mb_z0', 'plate_top + 42 mm', 'Main board bottom edge Z (above the front motors, top z 75.5)'),
    ('mb_top', 'mb_z0 + 70 mm', 'Main board top edge Z'),
    ('mb_so', '6 mm', 'Main board standoffs off the spine (M3 brass)'),
    ('mb_y0', 'spine_y + mb_so', 'Main board back face Y'),
]

# estimated component heights above the board (mm) by footprint family
HEIGHT = [('JST_XH', 9.8), ('JST_PH', 6.0), ('JST_SH', 4.25), ('IDC', 9.0), ('USB_C', 3.3), ('XT60', 8.3), ('XT30', 5.9),
          ('FUSE', 14.0), ('CP_Elec', 10.5), ('IND-SMD', 3.0), ('TO-252', 2.4), ('WIRELM', 3.1), ('SOT-223', 1.8),
          ('SW-SMD', 2.5), ('PinHeader', 8.5), ('SOIC', 1.7), ('TSSOP', 1.2), ('MSOP', 1.1), ('QFN', 1.0), ('SOT-23', 1.1), ('VSSOP', 1.0)]
# keep-out depth in front of a vertical connector (mated plug + cable bend), mm
KEEPOUT = [('JST_XH', 22.0), ('JST_PH', 16.0), ('JST_SH', 14.0), ('IDC', 18.0), ('PinHeader', 20.0)]
UNUSED = ('J412',)       # LED BAR: no LED bar on v2 (Adam, 18 Nov) -> connector stays empty
SERVICE = ('J301',)      # ESP32 USB: service only (the Pi flashes the ESP32 over UART0)


def _h(fp, table):
    for k, v in table:
        if k in fp:
            return v
    return None


def X(kx):
    return '(mb_xr) - (%.3f mm)' % (kx - 50.0)


def Z(ky):
    return '(mb_top) - (%.3f mm)' % (ky - 50.0)


def look(fp):
    if any(k in fp for k in ('JST_XH', 'JST_PH', 'JST_SH')):
        return 'ABS Plastic', 'Plastic - Matte (White)'
    if any(k in fp for k in ('XT60', 'XT30')):
        return 'Nylon 6/6', 'Plastic - Matte (Yellow)'
    if 'USB_C' in fp or 'WIRELM' in fp:
        return 'Steel', STEEL
    if 'CP_Elec' in fp:
        return 'Aluminum 6061', ALU
    return 'ABS Plastic', BLACK


def board():
    for n, e, cm in PARAMS4B:
        param(n, e, cm)
    parts = json.loads(urllib.request.urlopen(BRIDGE + 'main_board_parts.json', timeout=30).read().decode())
    c = fresh('Main board rev A (hw-main-board)')
    # outline (KiCad Edge.Cuts), extruded 1.6 mm from the board back face
    edge = [(50, 50), (198, 50), (198, 58), (222, 58), (222, 50), (236, 50), (236, 120), (50, 120)]
    sk = sketch(c, 'y', 'main board outline')
    # profile on the XZ plane itself (y = 0); the extrude offsets it to mb_y0 (see the s6 gear fix)
    poly(sk, [{'x': mm(X(kx)), 'y': 0.0, 'z': mm(Z(ky))} for kx, ky in edge])
    pcb = extrude(c, sk, 'mb_y0', '1.6 mm', name='main board PCB 4-layer 1.6 mm').bodies.item(0)
    finish(pcb, 'FR4', GREEN)
    holes = [p for p in parts if p['ref'].startswith('H')]
    for p in holes:
        kx, ky = (p['x0'] + p['x1']) / 2, (p['y0'] + p['y1']) / 2
        C(c, 'M3 hole', 'y', X(kx), 'mb_y0 + 0.8 mm', Z(ky), '3.2 mm', '3 mm', op=CUT, bodies=[pcb])
        C(c, 'M3 brass standoff 6', 'y', X(kx), 'spine_y + mb_so/2', Z(ky), '5.5 mm', 'mb_so', 'Copper, Alloy', BRASS)
    yf = 'mb_y0 + 1.6 mm'
    ko = fresh('Main board keep-outs (plug + cable bend)')
    nko = 0
    for p in parts:
        ref, fp = p['ref'], p['fp']
        if ref.startswith('H') or 'SolderJumper' in fp:
            continue
        h = _h(fp, HEIGHT)
        if h is None:
            continue
        kx0, kx1, ky0, ky1 = p['x0'], p['x1'], p['y0'], p['y1']
        xc, zc = X((kx0 + kx1) / 2), Z((ky0 + ky1) / 2)
        w, ht = '%.2f mm' % (kx1 - kx0), '%.2f mm' % (ky1 - ky0)
        mat, lk = look(fp)
        nm = '%s %s' % (ref, p['val'][:30])
        if ref in UNUSED:
            nm += ' (not used on v2)'
        box_part(c, nm, xc, '(%s) + %.3f mm' % (yf, h / 2), zc, w, '%.2f mm' % h, ht, mat, lk)
        if not ref.startswith('J') or ref in UNUSED:
            continue
        d = _h(fp, KEEPOUT)
        if d is not None:     # vertical connector: plug + cable leave toward the front wall
            box_part(ko, 'keep-out %s %s' % (ref, p['val'][:20]), xc, '(%s) + %.3f mm' % (yf, h + d / 2), zc, w, '%.2f mm' % d, ht, None, None)
        elif 'USB_C' in fp:   # top-edge receptacle: plug goes up out of the board edge
            up = 7.5 if ref not in SERVICE else 20.0
            box_part(ko, 'keep-out %s %s' % (ref, p['val'][:20]), xc, '(%s) + 4 mm' % yf, '(mb_top) + %.2f mm' % (up / 2), '12 mm', '8 mm', '%.2f mm' % up, None, None)
        elif 'XT60' in fp or 'XT30' in fp:   # right-angle power connector: mates from the board's side edge
            box_part(ko, 'keep-out %s %s (plug from the side edge)' % (ref, p['val'][:20]), '(mb_xr) + 15 mm', '(%s) + %.3f mm' % (yf, h / 2), zc,
                     '30 mm', '%.2f mm' % h, ht, None, None)
        nko += 1
    # Option (a) for rev B (Pip, 18 Nov): vertical PCB-mount XT60 / XT30 at the same spots, mating toward the
    # front wall. Modelled in the keep-out component: connector body, mated plug, and the 16 AWG cable bend
    # (wires leave toward the front wall, then bend up). EST sizes: XT60 vertical male 8.2 x 16 x 16 mm,
    # mated stack 26 mm, bend 15 mm; XT30 vertical male 10.2 x 5.2 x 11.6 mm, mated 19 mm, bend 12 mm.
    for ref, kx, ky, wx, hz, body_h, mated, bend in (('J101 XT60', 59.0, 103.5, 8.2, 16.0, 16.0, 26.0, 15.0),
                                                     ('J102 XT30', 57.0, 60.0, 10.2, 5.2, 11.6, 19.0, 12.0)):
        xc, zc = X(kx), Z(ky)
        box_part(ko, 'option (a) %s vertical connector body' % ref, xc, '(%s) + %.2f mm' % (yf, body_h / 2), zc,
                 '%.1f mm' % wx, '%.1f mm' % body_h, '%.1f mm' % hz, None, None)
        box_part(ko, 'option (a) %s mated plug' % ref, xc, '(%s) + %.2f mm' % (yf, body_h + (mated - body_h) / 2), zc,
                 '%.1f mm' % (wx + 1), '%.1f mm' % (mated - body_h), '%.1f mm' % (hz + 1), None, None)
        box_part(ko, 'option (a) %s cable bend (16 AWG, up)' % ref, xc, '(%s) + %.2f mm' % (yf, mated + bend / 2), '(%s) + %.2f mm' % (zc, bend / 2),
                 '%.1f mm' % (wx + 2), '%.1f mm' % bend, '%.1f mm' % (hz + bend), None, None)
    # kill loop J201 is normally closed: with nothing plugged in the motors never run -> shorting plug
    kl = [p for p in parts if p['ref'] == 'J201'][0]
    kx, ky = (kl['x0'] + kl['x1']) / 2, (kl['y0'] + kl['y1']) / 2
    box_part(c, 'kill loop shorting plug (JST PH-2 + wire loop)', X(kx), '(%s) + 6 mm + 5 mm' % yf, Z(ky), '8 mm', '10 mm', '6 mm', 'Nylon 6/6', 'Plastic - Matte (Red)')
    find_occ('Main board keep-outs (plug + cable bend)').isLightBulbOn = False
    log('main board ok, parts', len(parts), 'keep-outs', nko, 'top z', mm('mb_top'))


def box_part(c, name, x, y, z, w, d, h, mat, lk):
    b = box(c, name, {'x': x, 'y': y, 'z': z}, {'x': w, 'y': d, 'z': h})
    if mat:
        finish(b, mat, lk)
    return b


def main():
    board()
    done()
