# Stage 2: level 0 on the chassis plate.
# Battery 3S4P (2 x 3 x 2 cell block) + BMS + 15 A blade fuse on a printed sled that slides
# out the RIGHT side between the wheels and blind-mates an XT60 at a bulkhead; motor-driver
# board with 4x Pololu DRV8874; 4x VL53L0X cliff sensors under the plate; charge jack and
# charge fuse at the rear; optional front HC-SR04P holder; L0 posts.

PARAMS2 = [
    ('cell_d', '18.6 mm', '18650 cell diameter'),
    ('cell_l', '65.2 mm', '18650 cell length (flat top, unprotected)'),
    ('pack_x', '2*cell_l + 4 mm', '3S4P block X: 2 cells end to end + nickel'),
    ('pack_y', '3*cell_d + 3 mm', '3S4P block Y: 3 cells side by side + wrap'),
    ('pack_h', '2*cell_d + 2.5 mm', '3S4P block Z: 2 layers + wrap'),
    ('pack_xc', '0 mm', 'Pack centre X'),
    ('sled_floor', '2 mm', 'Battery sled floor'),
    ('sled_wall', '2.4 mm', 'Battery sled wall'),
    ('sled_h', '24 mm', 'Battery sled wall height'),
    ('bulk_x', '-(pack_x/2 + 34 mm)', 'XT60 bulkhead face X (sled blind-mates here)'),
    ('l1_z', 'fender_z', 'L1 deck underside'),
    ('deck_t', '4 mm', 'Deck thickness (4 mm birch ply)'),
    ('l1_top', 'l1_z + deck_t', 'L1 deck top'),
    ('post_x', '95 mm', 'L0 post |X|'),
    ('post_y', '58 mm', 'L0 post |Y|'),
    ('drvb_y', '59 mm', 'Motor-driver board centre Y (front bay)'),
    ('tof_r', '128 mm', 'Cliff sensor distance from the centre (under the plate)'),
]


def define():
    for n, e, cm in PARAMS2:
        param(n, e, cm)


def battery():
    c = fresh('Battery 3S4P 18650 + BMS + fuse')
    z0 = 'plate_top + sled_floor'
    for ix in (-1, 1):
        for iy in (-1, 0, 1):
            for iz in (0, 1):
                C(c, 'cell', 'x', '(pack_xc) + %d*(cell_l/2 + 1 mm)' % ix, '%d*(cell_d + 0.4 mm)' % iy,
                  '(%s) + 1 mm + cell_d/2 + %d*(cell_d + 0.5 mm)' % (z0, iz), 'cell_d', 'cell_l', 'Steel', 'Plastic - Matte (Blue)')
    for xs in ('-(cell_l + 1.5 mm)', '0 mm', '(cell_l + 1.5 mm)'):
        B(c, 'nickel strip', '(pack_xc) + %s' % xs, '0 mm', '(%s) + 1 mm' % z0, '0.6 mm' if xs != '0 mm' else '1.2 mm', 'pack_y - 4 mm',
          '2*cell_d + 0.5 mm', 'Steel', STEEL)
    top = '(%s) + pack_h' % z0
    B(c, 'BMS 3S 20A (64x20x3.4, check yours)', '(pack_xc) - 12 mm', '0 mm', top, '64 mm', '20 mm', '3.4 mm', 'FR4', 'Plastic - Matte (Blue)')
    B(c, 'fuse holder 15A mini blade', '(pack_xc) + 42 mm', '0 mm', top, '30 mm', '14 mm', '11 mm', 'ABS Plastic', 'Plastic - Matte (Red)')
    B(c, 'balance + main leads', '(pack_xc) - pack_x/2 - 6 mm', '0 mm', '(%s) + 4 mm' % z0, '8 mm', '30 mm', '8 mm', 'Copper', BLACK)
    log('battery ok')


def sled():
    c = fresh('Battery sled (printed)')
    x0 = 'bulk_x + 6 mm'                 # inner (left) end, carries the XT60 male
    x1 = 'shell_x - pwall - 1 mm'        # outer end, the right lower skirt screws on here
    L = '(%s) - (%s)' % (x1, x0)
    xc = '((%s) + (%s))/2' % (x0, x1)
    W = 'pack_y + 2*sled_wall + 1 mm'
    s = B(c, 'sled tray', xc, '0 mm', 'plate_top', L, W, 'sled_h', 'PET Plastic', BLACK)
    B(c, 'pocket', 'pack_xc', '0 mm', 'plate_top + sled_floor', 'pack_x + 1 mm', 'pack_y + 1 mm', 'sled_h', op=CUT, bodies=[s])
    B(c, 'lead pocket', '((%s) + pack_xc - pack_x/2)/2 + 2 mm' % x0, '0 mm', 'plate_top + sled_floor', '(pack_xc - pack_x/2) - (%s) - 4 mm' % x0,
      '34 mm', 'sled_h', op=CUT, bodies=[s])
    # end plate on the right: screw bosses for the skirt door, finger pull
    ep = B(c, 'door end plate', '(%s) - 2 mm' % x1, '0 mm', 'plate_top', '4 mm', W, 'l1_z - plate_top - 3 mm', 'PET Plastic', BLACK)
    join(c, s, [ep], 'battery sled (printed)')
    for yy in ('-20 mm', '20 mm'):
        C(c, 'M3 door screw', 'x', '(%s) - 2 mm' % x1, yy, 'plate_top + 40 mm', '2.9 mm', '6 mm', op=CUT, bodies=[s])
    # XT60 male on the sled (blind mate)
    p = fresh('Power connectors + fuse')
    B(c, 'XT60 window', x0, '0 mm', 'plate_top + 6 mm', '12 mm', '16.2 mm', '8.8 mm', op=CUT, bodies=[s])
    B(p, 'XT60 male on sled', 'bulk_x + 8 mm', '0 mm', 'plate_top + 6 mm', '16 mm', '15.6 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    # rails guide the sled (printed, screwed to the plate)
    for sy in (1, -1):
        r = B(c, 'sled rail', '((%s) + (%s))/2 + 10 mm' % (x0, x1), S(sy, 'pack_y/2 + sled_wall + 0.5 mm + 3.5 mm'), 'plate_top',
              '(%s) - 30 mm' % L, '6 mm', '10 mm', 'PET Plastic', BLACK)
        r.name = 'sled rail (printed)'
    # bulkhead with the XT60 female (blind mate), screwed to the plate
    bh = B(c, 'XT60 bulkhead (printed)', 'bulk_x - 4 mm', '0 mm', 'plate_top', '8 mm', '60 mm', '40 mm', 'PET Plastic', BLACK)
    B(c, 'XT60 window', 'bulk_x - 4 mm', '0 mm', 'plate_top + 6 mm', '10 mm', '16.4 mm', '8.6 mm', op=CUT, bodies=[bh])
    ft = B(c, 'bulkhead foot', 'bulk_x - 14 mm', '0 mm', 'plate_top', '20 mm', '60 mm', '4 mm', 'PET Plastic', BLACK)
    join(c, bh, [ft], 'XT60 bulkhead (printed)')
    B(p, 'XT60 female at bulkhead', 'bulk_x - 8 mm', '0 mm', 'plate_top + 6 mm', '16 mm', '15.6 mm', '8.2 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    log('sled ok')


def driver_board():
    c = fresh('Motor driver board 4x DRV8874')
    y = 'drvb_y'
    B(c, 'perfboard 70x40', '0 mm', y, 'plate_top + 8 mm', '70 mm', '40 mm', '1.6 mm', 'FR4', GREEN)
    for hx in (-1, 1):
        for hy in (-1, 1):
            C(c, 'M3 standoff 8', 'z', '%d*31 mm' % hx, '(%s) + %d*16 mm' % (y, hy), 'plate_top + 4 mm', '5.5 mm', '8 mm', 'Copper, Alloy', BRASS)
    pz = 'plate_top + 9.6 mm'
    for i in range(4):
        x = '(%d - 1.5)*16.5 mm' % i
        B(c, 'female headers', x, '(%s) - 2 mm' % y, pz, '15 mm', '15 mm', '8.5 mm', 'ABS Plastic', BLACK)
        B(c, 'DRV8874 carrier (Pololu 4035)', x, '(%s) - 2 mm' % y, '(%s) + 8.5 mm' % pz, '15.2 mm', '17.8 mm', '1.6 mm', 'FR4', GREEN)
        B(c, 'DRV8874 chip', x, '(%s) - 2 mm' % y, '(%s) + 10.1 mm' % pz, '5 mm', '5 mm', '1 mm', 'Steel', BLACK)
    B(c, 'motor terminals', '0 mm', '(%s) + 15 mm' % y, pz, '64 mm', '7.5 mm', '10 mm', 'ABS Plastic', 'Plastic - Matte (Green)')
    B(c, 'XT30 12V in', '-30 mm', '(%s) - 14 mm' % y, pz, '10 mm', '8 mm', '5.5 mm', 'Nylon 6/6', 'Plastic - Matte (Yellow)')
    B(c, 'JST-XH logic 10p', '8 mm', '(%s) - 17 mm' % y, pz, '27 mm', '6 mm', '7 mm', 'ABS Plastic', 'Plastic - Matte (White)')
    log('driver board ok')


def cliff():
    c = fresh('Cliff sensors 4x VL53L0X')
    for tag, (fx, fy) in (('front', (0, 1)), ('rear', (0, -1)), ('right', (1, 0)), ('left', (-1, 0))):
        x = '%d*tof_r' % fx
        y = '%d*tof_r' % fy
        pk = B(c, 'VL53L0X %s pocket (printed)' % tag, x, y, 'plate_z - 3 mm', '31 mm' if fy else '24 mm', '24 mm' if fy else '31 mm', '3 mm', 'PET Plastic', BLACK)
        B(c, 'window', x, y, 'plate_z - 3.5 mm', '10 mm', '6 mm', '4 mm', op=CUT, bodies=[pk])
        B(c, 'VL53L0X %s PCB (Adafruit 3317)' % tag, x, y, 'plate_z - 1.6 mm', '25.4 mm' if fy else '17.78 mm', '17.78 mm' if fy else '25.4 mm', '1.6 mm', 'FR4', GLOSSB)
        B(c, 'VL53L0X %s sensor' % tag, x, y, 'plate_z - 2.6 mm', '4.4 mm', '2.4 mm', '1 mm', 'Steel', BLACK)
    log('cliff ok')


def rear_and_front():
    c = fresh('Charge port + charge fuse')
    # 5.5x2.1 panel jack on a printed bracket at the rear, through the rear skirt
    br = B(c, 'charge jack bracket (printed)', '0 mm', '-(shell_y - pwall - 6 mm)', 'plate_top', '30 mm', '4 mm', '40 mm', 'PET Plastic', BLACK)
    ft = B(c, 'bracket foot', '0 mm', '-(shell_y - pwall - 14 mm)', 'plate_top', '30 mm', '16 mm', '4 mm', 'PET Plastic', BLACK)
    join(c, br, [ft], 'charge jack bracket (printed)')
    C(c, 'jack hole', 'y', '0 mm', '-(shell_y - pwall - 6 mm)', 'plate_top + 26 mm', '11 mm', '6 mm', op=CUT, bodies=[br])
    C(c, 'DC jack 5.5x2.1 panel (5 A)', 'y', '0 mm', '-(shell_y - pwall - 11.2 mm)', 'plate_top + 26 mm', '10.8 mm', '22 mm', 'Steel', BLACK)
    B(c, 'charge fuse holder 5A inline', '0 mm', '-(shell_y - 40 mm)', 'plate_top', '30 mm', '12 mm', '10 mm', 'ABS Plastic', 'Plastic - Matte (Red)')
    # optional front ultrasonic: holder stays empty unless the HC-SR04P is fitted
    h = fresh('Front ultrasonic spot (optional HC-SR04P)')
    hb = B(h, 'HC-SR04P holder (printed)', '0 mm', 'shell_y - pwall - 16 mm', 'plate_top', '48 mm', '5 mm', '38 mm', 'PET Plastic', BLACK)
    hf = B(h, 'holder foot', '0 mm', 'shell_y - pwall - 24 mm', 'plate_top', '48 mm', '16 mm', '4 mm', 'PET Plastic', BLACK)
    join(h, hb, [hf], 'HC-SR04P holder (printed)')
    for tx in (-1, 1):
        C(h, 'transducer hole', 'y', '%d*13 mm' % tx, 'shell_y - pwall - 16 mm', 'plate_top + 24 mm', '16.6 mm', '6 mm', op=CUT, bodies=[hb])
    log('rear/front ok')


def posts():
    c = fresh('L0 posts (M4 rod + 8 mm alu tube)')
    for sx in (1, -1):
        for sy in (1, -1):
            ring(c, 'L0 post tube', 'z', S(sx, 'post_x'), S(sy, 'post_y'), '(plate_top + l1_z)/2', '8 mm', '4.2 mm', 'l1_z - plate_top',
                 'Aluminum 6061', ALU)
            C(c, 'M4 rod', 'z', S(sx, 'post_x'), S(sy, 'post_y'), '(plate_z + l1_top)/2', '4 mm', 'l1_top - plate_z', 'Steel', STEEL)
    log('posts ok')


def main(parts=('battery', 'sled', 'driver', 'cliff', 'rear', 'posts')):
    define()
    if 'battery' in parts:
        battery()
    if 'sled' in parts:
        sled()
    if 'driver' in parts:
        driver_board()
    if 'cliff' in parts:
        cliff()
    if 'rear' in parts:
        rear_and_front()
    if 'posts' in parts:
        posts()
    done()
