# Stage 8: harness routes. Every run starts at its real connector on the main board (positions from
# main_board_parts.json, the board's own KiCad footprints) and ends at the part it feeds, through the
# frame slots and cable holes made for it. Modelled as pipes along the route (not every wire).
# Fixed waypoints (mm) between the two ends: rerun this stage after moving parts.
import json

RED, BLK, WHT, GRY = 'Plastic - Matte (Red)', 'Plastic - Matte (Black)', 'Plastic - Matte (White)', 'Plastic - Matte (Gray)'
H = dict(JST_XH=9.8, JST_PH=6.0, JST_SH=4.25, IDC=9.0, USB_C=3.3, XT60=8.3, XT30=5.9, PinHeader=8.5)


def connectors():
    parts = json.loads(urllib.request.urlopen(BRIDGE + 'main_board_parts.json', timeout=30).read().decode())
    xr, top, yf = mm('mb_xr'), mm('mb_top'), mm('mb_y0') + 1.6
    out = {}
    for p in parts:
        if not p['ref'].startswith('J'):
            continue
        h = next((v for k, v in H.items() if k in p['fp']), 5.0)
        kx, ky = (p['x0'] + p['x1']) / 2, (p['y0'] + p['y1']) / 2
        out[p['ref']] = (xr - (kx - 50.0), yf + h + 1.0, top - (ky - 50.0))
    return out


def runs(J):
    def at(ref, dy=0.0, dz=0.0):
        x, y, z = J[ref]
        return (x, y + dy, z + dz)
    xr = mm('mb_xr')
    pi_usb = (mm('pi_xc') - 42.5 + 11.2, mm('pi_y0') + 3.0, mm('pi_z0') - 4.0)
    disp0 = (mm('pi_xc') - 42.5 + 55.0, mm('pi_y0') + 5.0, mm('pi_z0') + 8.0)
    hat_hdr = (mm('pi_xc') - 42.5 + 32.5, mm('pi_y0') + 1.4 + mm('hat_so') + 1.6 + 9.0, mm('pi_z0') + 53.0)
    cpx = (0.0, mm('cpx_yf') - 6.0, mm('cpx_z') - 6.0)
    bulk = (0.0, mm('sled_y1') + 30.0, mm('plate_top') + 12.4)
    key = (50.0, -(mm('shell_y') - mm('pwall')) + 12.0, mm('body_top') - 40.0)
    shaft_bot = (0.0, mm('pan_y'), mm('shaft_z0') - 2.0)
    shaft_top = (0.0, mm('pan_y'), mm('turret_z') + 1.0)
    head_in = (14.0, mm('pan_y') + 10.0, mm('head_z0') + 1.0)
    pan_servo = (mm('pan_servo_x'), mm('pan_y') - 8.0, mm('gear_z') - 20.0)
    lidar = (mm('ld_x'), mm('ld_y'), mm('ld_z') - 1.0)
    slot_c = (0.0, mm('spine_y') - 2.0, mm('top_deck_z') - 44.0)       # spine ribbon slot
    slot_l = (-85.0, mm('spine_y') - 2.0, mm('plate_top') + 129.0)     # left spine harness slot
    slot_r = (85.0, mm('spine_y') - 2.0, mm('plate_top') + 129.0)      # right spine harness slot
    sw = mm('shell_y') - mm('pwall') - 2.9 - 3.2 - 2.9                 # bumper switch body centre |Y|
    R = [
        # power
        ('battery 12 V 16 AWG: sled XT60 bulkhead -> J101 BAT IN (XT60, mates from the board edge)', 5, RED,
         [bulk, (0, 74, 60), (20, 72, 80), (70, 70, 84), (xr + 2.5, 56, at('J101')[2])]),
        ('main switch loop 16 AWG pair: J102 (XT30) -> XT30 loop key, upper back', 5, RED,
         [(xr + 2.5, 56, at('J102')[2]), (90, 50, at('J102')[2] + 10), slot_r, (88, 30, 175), (88, -45, 220), (85, -53, 220), (60, -80, 230), key]),
        ('Pi 5 V: J103 PI 5V OUT -> Pi USB-C (short right-angle USB-C cable)', 4, BLK,
         [at('J103', -3, 2), (at('J103')[0], 56, mm('mb_top') + 4), (pi_usb[0], 56, mm('mb_top') + 4), pi_usb]),
        # Pi link
        ('GPIO 40-way IDC ribbon: J401 -> AI HAT+ 2 pass-through header', 3, GRY,
         [at('J401'), (at('J401')[0], 88, mm('mb_top') + 6), (hat_hdr[0], 88, hat_hdr[2] - 10), hat_hdr]),
        ('TFT cable (SPI0 + DC/RST/BL, 3V3, GND) from a 2nd IDC socket crimped on the ribbon -> head TFT', 2.5, BLK,
         [(hat_hdr[0] + 10, 88, hat_hdr[2] - 20), (-10, 82, slot_c[2]), slot_c, (0, 30, slot_c[2]), shaft_bot, shaft_top, (10, 26, mm('tilt_z')), head_in]),
        ('camera ribbon 500 mm: Pi DISP0 -> Camera Module 3 (up the hollow pan shaft)', 3, WHT,
         [disp0, (disp0[0], 84, disp0[2] + 4), (disp0[0], 84, slot_c[2] - 10), (0, 76, slot_c[2]), slot_c, (0, 30, slot_c[2] + 2), shaft_bot, shaft_top,
          (14, 22, mm('turret_z') + 4), (14, 40, mm('tilt_z') - 3), (14, 32, mm('head_z0') - 8), head_in]),
        # sensors and outputs
        ('LD19 cable: J403 LIDAR -> LD19 (left spine slot, side channel, upper cheek slot, deck hole)', 3, BLK,
         [at('J403'), (at('J403')[0] - 2, 52, slot_l[2] - 5), slot_l, (-88, 30, 200), (-88, -40, mm('top_deck_z') - 20), (-70, -45, mm('top_deck_z') - 12),
          (mm('lidar_x'), mm('lidar_y'), mm('top_deck_z') - 2), lidar]),
        ('CPX cable: J404 CPX -> Circuit Playground Express pads (VOUT, GND, TX, kill)', 3, BLK,
         [at('J404'), (at('J404')[0], 72, at('J404')[2] + 40), (-40, cpx[1] - 4, cpx[2] - 10), cpx]),
        ('IMU cable: J411 IMU -> BNO085 (spine slot)', 2.5, BLK,
         [at('J411'), (-30, 52, mm('plate_top') + 125), (-30, 40, mm('plate_top') + 125), (-10, 36, mm('plate_top') + 98), (0, 36, mm('plate_top') + 93)]),
        ('bumper harness: J410 BUMPERS -> front switches', 2.5, BLK,
         [at('J410'), (at('J410')[0], 72, mm('mb_z0') + 4), (24, 84, 52), (36, sw, 40)]),
        ('bumper harness: front left switch', 2.5, BLK, [(24, 84, 52), (-24, 84, 52), (-36, sw, 40)]),
        ('bumper harness: rear switches (through the spine notch, along the tunnel)', 2.5, BLK,
         [(24, 84, 52), (24, 46, 52), (28, -40, 44), (28, -80, 42), (36, -sw, 40)]),
        ('bumper harness: rear left switch', 2.5, BLK, [(28, -80, 42), (-28, -80, 42), (-36, -sw, 40)]),
        ('servo leads: J413 PAN + J414 TILT -> pan servo; tilt lead on up the shaft', 3, BLK,
         [at('J413'), (at('J413')[0], 70, slot_c[2] - 30), (-20, 72, slot_c[2]), slot_c, (20, 30, slot_c[2] - 4), pan_servo]),
        ('speaker cable: J501 SPEAKER -> 40 mm speaker (left slot, side channel, cheek, rear plate slot)', 2.5, BLK,
         [at('J501'), (at('J501')[0] - 4, 52, slot_l[2] - 2), slot_l, (-88, 20, 200), (-88, -40, mm('top_deck_z') - 20), (-62, -46, 210),
          (-40, -53, mm('plate_top') + 155), (-45, -70, mm('body_top') - 70)]),
        ('mic cable (6 wire): J502 MIC -> INMP441 in the head (up the shaft)', 2.5, BLK,
         [at('J502'), (at('J502')[0], 70, slot_c[2] - 20), (-8, 72, slot_c[2]), slot_c, (0, 32, slot_c[2] + 2), shaft_bot]),
        # cliff sensors: down the front channel, through the spine notch, cable holes in the plate
        ('cliff cable: J405 -> front VL53L0X', 2.5, BLK, [at('J405'), (at('J405')[0], 70, mm('mb_z0') - 2), (24, 72, 42), (24, 72, 30), (8, 80, 28.5)]),
        ('cliff cable: J406 -> right VL53L0X', 2.5, BLK, [at('J406'), (at('J406')[0], 70, mm('mb_z0') - 2), (20, 64, 70), (22, 42, 70), (45, 12, 45), (62, 14, 40), (62, 14, 30), (72, 0, 28.5)]),
        ('cliff cable: J407 -> rear VL53L0X', 2.5, BLK, [at('J407'), (at('J407')[0], 70, mm('mb_z0') - 2), (18, 64, 68), (20, 42, 68), (36, -10, 45), (40, -40, 40), (40, -40, 30), (8, -72, 28.5)]),
        ('cliff cable: J408 -> left VL53L0X', 2.5, BLK, [at('J408'), (at('J408')[0], 70, mm('mb_z0') - 2), (-20, 64, 70), (-22, 42, 70), (-45, 12, 45), (-62, 14, 40), (-62, 14, 30), (-72, 0, 28.5)]),
        # motors (JGB37 6-wire: M+, GND, A, B, VCC, M-)
        ('motor cable: front left JGB37 -> J601 MOTOR A', 4, BLK, [(-32, 76, 57), (-22, 66, 76), (at('J601')[0], 66, mm('mb_z0') + 2), at('J601', 0, -3)]),
        ('motor cable: front right JGB37 -> J701 MOTOR B', 4, BLK, [(32, 76, 57), (22, 66, 76), (at('J701')[0], 66, mm('mb_z0') + 2), at('J701', 0, -3)]),
        ('motor cable: rear left JGB37 -> J801 MOTOR C', 4, BLK, [(-32, -76, 57), (-28, -40, 45), (-26, 30, 45), (-24, 46, 60), (at('J801')[0], 66, mm('mb_z0') + 2), at('J801', 0, -3)]),
        ('motor cable: rear right JGB37 -> J901 MOTOR D', 4, BLK, [(32, -76, 57), (28, -40, 45), (26, 30, 45), (24, 46, 60), (at('J901')[0], 66, mm('mb_z0') + 2), at('J901', 0, -3)]),
    ]
    return R


def main():
    J = connectors()
    c = fresh('Wiring harness (paths)')
    n = 0
    for name, d, look, pts in runs(J):
        sk = c.sketches.add(c.xYConstructionPlane)
        sk.name = 'route: ' + name[:40]
        sk.isVisible = False
        lines = OC.create()
        prev = None
        for (x, y, z) in pts:
            p = P(x, y, z)
            if prev is not None:
                ln = sk.sketchCurves.sketchLines.addByTwoPoints(prev, p)
                lines.add(ln)
                prev = ln.endSketchPoint
            else:
                prev = p
        path = c.features.createPath(lines.item(0), True)
        pi = c.features.pipeFeatures.createInput(path, NEWB)
        pi.sectionSize = V.createByReal(d / 10.0)
        f = c.features.pipeFeatures.add(pi)
        for b in f.bodies:
            b.name = name
            finish(b, 'Copper', look)
        n += 1
    tap = B(c, 'TFT tap: 2nd 2x20 IDC socket crimped on the ribbon', '(pi_xc) - 42.5 mm + 32.5 mm', '86 mm', 'pi_z0 + 26 mm', '51 mm', '6 mm', '9 mm', 'ABS Plastic', BLACK)
    log('wiring runs', n)
    done()
