# Stage 3: frame. L1 deck (4 mm ply) over the battery and motors, 4 corner tie rods
# (M5 rod in 10 mm alu tube) up to the top deck (4 mm ply), and the spine: a vertical
# 4 mm ply plate across the torso that carries the ESP32 and Pi on its front face and
# the bucks on its back. The channel between the spine and the front panel is the chimney.

PARAMS3 = [
    ('deck_half', 'shell_x - pwall - 3.6 mm', 'L1 deck half-size'),
    ('top_deck_z', 'body_top - 14 mm', 'Top deck underside'),
    ('top_deck_top', 'top_deck_z + deck_t', 'Top deck top'),
    ('top_half', 'shell_x - 10 mm', 'Top deck half-size'),
    ('rod_xy', '128 mm', 'Corner tie rod |X| = |Y|'),
    ('spine_y', '96 mm', 'Spine front face Y'),
    ('spine_half', '118 mm', 'Spine half-width'),
    ('pan_y', '35 mm', 'Head pan axis Y (forward, far from the lidar)'),
    ('lidar_y', '-90 mm', 'Lidar centre Y on the rear pod'),
    ('vent_y0', 'spine_y + 6 mm', 'Chimney vent slots start Y'),
    ('vent_y1', 'shell_y - top_r - 8 mm', 'Chimney vent slots end Y'),
]


def define():
    for n, e, cm in PARAMS3:
        param(n, e, cm)


def l1_deck():
    c = fresh('L1 deck (4 mm ply)')
    sk = sketch(c, 'z', 'L1 outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': '2*deck_half', 'y': '2*deck_half'})
    d = extrude(c, sk, 'l1_z', 'deck_t', name='L1 deck 4 mm birch ply').bodies.item(0)
    fillet(c, edges_where(d, lambda e: is_axis_line(e, 'z')), 'corner_r - pwall - 3 mm')
    cuts = []
    # chimney intake: slots in front of the spine
    for k in range(9):
        cuts.append(('%d*22 mm' % (k - 4), '(spine_y + 6 mm + shell_y - pwall - 8 mm)/2', '8 mm', '(shell_y - pwall - 8 mm) - (spine_y + 6 mm)'))
    # cable pass-throughs (rounded slots would be nicer; rectangles are what gets cut)
    cuts += [('-112 mm', '0 mm', '16 mm', '40 mm'),     # main power: bulkhead up to the PDB / loop key
             ('60 mm', '86 mm', '40 mm', '10 mm'),      # driver board logic + encoders up to the ESP32
             ('0 mm', '-104 mm', '40 mm', '10 mm'),     # rear: cliff sensors, charge
             ('112 mm', '-70 mm', '16 mm', '30 mm')]    # right: right cliff sensor, sled bay sensing
    for (x, y, w, h) in cuts:
        B(c, 'slot', x, y, 'l1_z - 1 mm', w, h, 'deck_t + 2 mm', op=CUT, bodies=[d])
    for sx in (1, -1):
        for sy in (1, -1):
            C(c, 'M4 hole', 'z', S(sx, 'post_x'), S(sy, 'post_y'), 'l1_z + deck_t/2', '4.4 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
            C(c, 'M5 hole', 'z', S(sx, 'rod_xy'), S(sy, 'rod_xy'), 'l1_z + deck_t/2', '5.4 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
    finish(d, 'Birch', 'Bamboo Light - Semigloss')
    log('L1 ok')


def rods():
    c = fresh('Corner tie rods (M5 rod + 10 mm alu tube)')
    for sx in (1, -1):
        for sy in (1, -1):
            ring(c, 'tie tube', 'z', S(sx, 'rod_xy'), S(sy, 'rod_xy'), '(l1_top + top_deck_z)/2', '10 mm', '5.4 mm', 'top_deck_z - l1_top',
                 'Aluminum 6061', ALU)
            C(c, 'M5 rod', 'z', S(sx, 'rod_xy'), S(sy, 'rod_xy'), '(l1_z - 2 mm + top_deck_top + 4 mm)/2', '5 mm',
              '(top_deck_top + 4 mm) - (l1_z - 2 mm)', 'Steel', STEEL)
            for zz in ('l1_z - 2 mm', 'top_deck_top + 2 mm'):
                C(c, 'M5 dome nut', 'z', S(sx, 'rod_xy'), S(sy, 'rod_xy'), zz, '8 mm', '4 mm', 'Steel', STEEL)
    log('rods ok')


def spine():
    c = fresh('Spine (4 mm ply)')
    s = B(c, 'spine 4 mm birch ply', '0 mm', 'spine_y - deck_t/2', 'l1_top', '2*spine_half', 'deck_t', 'top_deck_z - l1_top', 'Birch', 'Bamboo Light - Semigloss')
    # camera ribbon + head wiring slot near the top, Pi buck lead slot, ESP32/driver cable slot
    B(c, 'ribbon slot', '0 mm', 'spine_y - deck_t/2', 'top_deck_z - 26 mm', '24 mm', 'deck_t + 2 mm', '14 mm', op=CUT, bodies=[s])
    B(c, 'Pi power slot', '-30 mm', 'spine_y - deck_t/2', 'l1_top + 112 mm', '14 mm', 'deck_t + 2 mm', '8 mm', op=CUT, bodies=[s])
    B(c, 'ESP32 cable slot', '60 mm', 'spine_y - deck_t/2', 'l1_top + 6 mm', '30 mm', 'deck_t + 2 mm', '8 mm', op=CUT, bodies=[s])
    finish(s, 'Birch', 'Bamboo Light - Semigloss')
    # printed L brackets, 2 at the bottom and 2 at the top
    for sx in (1, -1):
        for (z, up) in (('l1_top', 1), ('top_deck_z', -1)):
            zb = z if up > 0 else '(%s) - 20 mm' % z
            v = B(c, 'spine bracket (printed)', S(sx, '80 mm'), 'spine_y - deck_t - 2 mm', zb, '20 mm', '4 mm', '20 mm', 'PET Plastic', BLACK)
            hz = z if up > 0 else '(%s) - 4 mm' % z
            h = B(c, 'bracket flange', S(sx, '80 mm'), 'spine_y - deck_t - 10 mm', hz, '20 mm', '16 mm', '4 mm', 'PET Plastic', BLACK)
            join(c, v, [h], 'spine bracket (printed)')
    log('spine ok')


def top_deck():
    c = fresh('Top deck (4 mm ply)')
    sk = sketch(c, 'z', 'top outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': '2*top_half', 'y': '2*top_half'})
    d = extrude(c, sk, 'top_deck_z', 'deck_t', name='top deck 4 mm birch ply').bodies.item(0)
    fillet(c, edges_where(d, lambda e: is_axis_line(e, 'z')), '22 mm')
    # chimney exhaust slots over the front channel
    for k in range(9):
        B(c, 'vent', '%d*22 mm' % (k - 4), '(vent_y0 + vent_y1)/2', 'top_deck_z - 1 mm', '8 mm', 'vent_y1 - vent_y0', 'deck_t + 2 mm', op=CUT, bodies=[d])
    # head joint: ribbon hole under the pan axis, pan servo cut-out, plinth bolts (4x M4 on r 34)
    C(c, 'pan shaft hole', 'z', '0 mm', 'pan_y', 'top_deck_z + deck_t/2', 'shaft_od + 2 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
    for (hx, hy) in (('pan_servo_x + 5 mm', '(pan_y) - 23 mm'), ('pan_servo_x + 5 mm', '(pan_y) + 23 mm')):
        C(c, 'servo cradle M3', 'z', hx, hy, 'top_deck_z + deck_t/2', '3.4 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        C(c, 'plinth M4', 'z', '%.4f*34 mm' % math.cos(r), '(pan_y) + %.4f*34 mm' % math.sin(r), 'top_deck_z + deck_t/2', '4.4 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
    # lidar pod: 4x M3 + cable hole
    for (hx, hy) in ((-26, -24), (26, -24), (-26, 24), (26, 24)):
        C(c, 'pod M3', 'z', '%d mm' % hx, '(lidar_y) + %d mm' % hy, 'top_deck_z + deck_t/2', '3.4 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
    C(c, 'lidar cable hole', 'z', '0 mm', 'lidar_y', 'top_deck_z + deck_t/2', '12 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
    for sx in (1, -1):
        for sy in (1, -1):
            C(c, 'M5 hole', 'z', S(sx, 'rod_xy'), S(sy, 'rod_xy'), 'top_deck_z + deck_t/2', '5.4 mm', 'deck_t + 2 mm', op=CUT, bodies=[d])
    finish(d, 'Birch', 'Bamboo Light - Semigloss')
    log('top deck ok')


def main(parts=('l1', 'rods', 'spine', 'top')):
    define()
    param('pan_servo_x', '36 mm', 'Pan servo shaft X (1:1 gear pair, 36 mm centre distance)')
    param('shaft_od', '25 mm', 'Pan shaft: 25 x 1 mm aluminium tube (fits 6805 bearings)')
    if 'l1' in parts:
        l1_deck()
    if 'rods' in parts:
        rods()
    if 'spine' in parts:
        spine()
    if 'top' in parts:
        top_deck()
    done()
