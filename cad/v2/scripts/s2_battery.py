# Stage 2: battery and level 0.
# 3S4P 18650 block, cells lying along Y: 2 across (X) x 3 high (Z) x 2 long (Y). It rides on a
# printed sled that slides out of the BACK between the rear motors; the battery door (a shell
# piece, added in s5) screws to the sled's rear wall and carries the charge jack, so charging
# works with the loop key out. At the front the sled blind-mates an XT60 in a bulkhead that
# sits in a notch under the spine. BMS and the 15 A blade fuse ride on top of the pack.
# 4x VL53L0X cliff sensors under the plate. (The optional HC-SR04P spot was dropped on 19 Nov 2026 to make
# room for the sled XT60 nose; ultrasonic_spot() now only deletes its old component.)

PARAMS2 = [
    ('cell_d', '18.6 mm', '18650 cell diameter'),
    ('cell_l', '65.2 mm', '18650 cell length (flat top, unprotected)'),
    ('pack_x', '2*cell_d + 1 mm', 'Pack width X (2 cells)'),
    ('pack_z', '3*cell_d + 2 mm', 'Pack height Z (3 cells)'),
    ('pack_y', '2*cell_l + 4 mm', 'Pack length Y (2 cells end to end + nickel)'),
    ('sled_wall', '2.4 mm', 'Battery sled wall'),
    ('sled_y0', '-(shell_y - pwall)', 'Sled rear face (the door screws on here)'),
    ('pack_y0', 'sled_y0 + sled_wall + 0.5 mm', 'Pack rear end Y'),
    ('pack_y1', 'pack_y0 + pack_y', 'Pack front end Y'),
    ('sled_nose', '14 mm', 'Sled nose in front of the pack: room for the XT60 male wires (19 Nov: sonar spot dropped for it)'),
    ('sled_y1', 'pack_y1 + sled_wall + 0.3 mm + sled_nose', 'Sled front face Y (XT60 male sticks out here; pack + wall + nose)'),
    ('sled_hw', 'pack_x/2 + sled_wall + 0.5 mm', 'Sled half-width'),
    ('tun_hw', 'sled_hw + 4.5 mm', 'Battery tunnel half-width (notches in the spine and rear plate)'),
    ('tof_r', '80 mm', 'Cliff sensor distance from the centre (under the plate)'),
]


def define():
    for n, e, cm in PARAMS2:
        param(n, e, cm)


def battery():
    """Cells packed tight (welded and shrink-wrapped in reality): touching each other and the sled floor,
    nickel strips on the cell ends, BMS and fuse holders on the top cells. pack_x/pack_z keep wrap clearance."""
    c = fresh('Battery 3S4P 18650 + BMS + fuse')
    z0 = 'plate_top + 2 mm'
    for ix in (-1, 1):
        for iz in range(3):
            for iy in range(2):
                C(c, 'cell', 'y', '%d*cell_d/2' % ix, 'pack_y0 + 1.5 mm + cell_l/2 + %d*(cell_l + 1 mm)' % iy,
                  '(%s) + cell_d/2 + %d*cell_d' % (z0, iz), 'cell_d', 'cell_l', 'Steel', 'Plastic - Matte (Blue)')
    for ys in ('pack_y0 + 1.2 mm', 'pack_y0 + 1.5 mm + cell_l + 0.5 mm', 'pack_y0 + 1.5 mm + 2*cell_l + 1.3 mm'):
        B(c, 'nickel strip', '0 mm', ys, '(%s) + 1 mm' % z0, '2*cell_d - 3 mm', '0.6 mm', '3*cell_d - 2 mm', 'Steel', STEEL)
    top = '(%s) + 3*cell_d' % z0
    B(c, 'BMS 3S 20A (64x20x3.4, check yours)', '0 mm', '(pack_y0 + pack_y1)/2 - 20 mm', top, '20 mm', '64 mm', '3.4 mm', 'FR4', 'Plastic - Matte (Blue)')
    B(c, 'fuse holder 15A mini blade', '0 mm', 'pack_y1 - 18 mm', top, '14 mm', '30 mm', '11 mm', 'ABS Plastic', 'Plastic - Matte (Red)')
    B(c, 'charge fuse holder 5A', '0 mm', 'pack_y0 + 22 mm', top, '12 mm', '26 mm', '7 mm', 'ABS Plastic', 'Plastic - Matte (Red)')
    # reverse-blocking ideal-diode module in the charge path (jack -> 5 A fuse -> diode -> pack P+, as wired in w_routes S06-S08): blocks a
    # live jack and back-feeding; ~20 mV drop, so a 12.6 V CC/CV charger still fills the pack (a Schottky's
    # ~0.5 V would stop it at about 12.1 V). EST size: LM74700-class module 22 x 16 x 5 mm.
    B(c, 'ideal diode module (LM74700-class, EST 22x16x5)', '14 mm', 'pack_y0 + 13 mm', top, '16 mm', '22 mm', '5 mm', 'FR4', GREEN)
    log('battery ok, pack top z', mm(top))


def sled():
    c = fresh('Battery sled (printed)')
    L = 'sled_y1 - sled_y0'
    yc = '(sled_y0 + sled_y1)/2'
    s = B(c, 'sled tray', '0 mm', yc, 'plate_top', '2*sled_hw', L, '30 mm', 'PET Plastic', BLACK)
    B(c, 'pocket', '0 mm', '(pack_y0 + pack_y1)/2', 'plate_top + 2 mm', 'pack_x + 1 mm', 'pack_y + 0.6 mm', '30 mm', op=CUT, bodies=[s])
    rw = B(c, 'rear wall', '0 mm', 'sled_y0 + sled_wall/2', 'plate_top', '2*sled_hw', 'sled_wall', 'body_z0 + 92 mm - plate_top', 'PET Plastic', BLACK)
    fw = B(c, 'front wall', '0 mm', 'sled_y1 - sled_wall/2', 'plate_top', '2*sled_hw', 'sled_wall', '40 mm', 'PET Plastic', BLACK)
    join(c, s, [rw, fw], 'battery sled (printed)')
    # nose cavity between the pack front and the front wall: the XT60 male's 16 AWG leads bend up here
    B(c, 'nose cavity', '0 mm', '(pack_y1 + sled_y1 - sled_wall)/2', 'plate_top + 2 mm', 'pack_x + 1 mm', '(sled_y1 - sled_wall) - pack_y1', '40 mm', op=CUT, bodies=[s])
    B(c, 'XT60 window', '0 mm', 'sled_y1 - sled_wall/2', 'plate_top + 8 mm', '16.2 mm', '4 mm', '8.8 mm', op=CUT, bodies=[s])
    C(c, 'charge jack hole', 'y', '0 mm', 'sled_y0 + sled_wall/2', 'body_z0 + 82 mm', '11 mm', '4 mm', op=CUT, bodies=[s])
    for xx in ('-12 mm', '12 mm'):
        C(c, 'M3 door screw', 'y', xx, 'sled_y0 + sled_wall/2', 'body_z0 + 60 mm', '2.9 mm', '4 mm', op=CUT, bodies=[s])
    for sx in (1, -1):
        B(c, 'sled rail (printed)', S(sx, 'sled_hw + 2.5 mm'), '(sled_y0 + sled_y1)/2 + 6 mm', 'plate_top', '4 mm', '(%s) - 20 mm' % L, '8 mm',
          'PET Plastic', BLACK)
    # charge jack on the sled rear wall (pack side of the loop key)
    p = fresh('Power connectors')
    C(p, 'DC jack 5.5x2.1 panel (5 A), charge input', 'y', '0 mm', 'sled_y0 + 9 mm', 'body_z0 + 82 mm', '10.8 mm', '20 mm', 'Steel', BLACK)
    B(p, 'XT60 male on sled', '0 mm', 'sled_y1 + 6 mm', 'plate_top + 8.3 mm', '16 mm', '16 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    B(p, 'XT60 female in bulkhead', '0 mm', 'sled_y1 + 22 mm', 'plate_top + 8.3 mm', '16 mm', '16 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    # bulkhead (printed), between the front motors, under the spine notch
    bh = B(c, 'XT60 bulkhead (printed)', '0 mm', 'sled_y1 + 22 mm', 'plate_top', '34 mm', '10 mm', '30 mm', 'PET Plastic', BLACK)
    B(c, 'XT60 pocket', '0 mm', 'sled_y1 + 22 mm', 'plate_top + 8 mm', '16.4 mm', '12 mm', '8.8 mm', op=CUT, bodies=[bh])
    log('sled ok, sled y', mm('sled_y0'), mm('sled_y1'))


def cliff():
    c = fresh('Cliff sensors 4x VL53L0X')
    for tag, (fx, fy) in (('front', (0, 1)), ('rear', (0, -1)), ('right', (1, 0)), ('left', (-1, 0))):
        x = '%d*tof_r' % fx
        y = '%d*tof_r' % fy
        long_x = fy != 0
        pk = B(c, 'VL53L0X %s pocket (printed)' % tag, x, y, 'plate_z - 3 mm', '31 mm' if long_x else '24 mm', '24 mm' if long_x else '31 mm', '3 mm', 'PET Plastic', BLACK)
        B(c, 'window', x, y, 'plate_z - 3.5 mm', '10 mm', '6 mm', '4 mm', op=CUT, bodies=[pk])
        B(c, 'VL53L0X %s PCB (Adafruit 3317)' % tag, x, y, 'plate_z - 1.6 mm', '25.4 mm' if long_x else '17.78 mm', '17.78 mm' if long_x else '25.4 mm', '1.6 mm', 'FR4', GLOSSB)
        B(c, 'VL53L0X %s sensor' % tag, x, y, 'plate_z - 2.6 mm', '4.4 mm', '2.4 mm', '1 mm', 'Steel', BLACK)
    log('cliff ok')


def ultrasonic_spot():
    """Dropped 19 Nov 2026 (Pip/Adam): the sled XT60 nose and the battery feed need the space. Removes the old component."""
    o = find_occ('Front ultrasonic spot (optional HC-SR04P)')
    if o:
        o.deleteMe()
    log('ultrasonic spot removed')


def main(parts=('battery', 'sled', 'cliff', 'us')):
    define()
    if 'battery' in parts:
        battery()
    if 'sled' in parts:
        sled()
    if 'cliff' in parts:
        cliff()
    if 'us' in parts:
        ultrasonic_spot()
    done()
