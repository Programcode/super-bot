# Stage 1: user parameters, chassis plate, 4 drive corners (JGB37-520 19:1 motor,
# printed motor mount / wheel-well liner, 100 mm mecanum wheel).
# Loader: exec(v2lib.py), exec(this), main().

PARAMS = [
    # name, expression, comment
    ('body_w', '300 mm', 'Torso shell outer width X (footprint parameter)'),
    ('body_d', '300 mm', 'Torso shell outer depth Y (footprint parameter)'),
    ('body_top', '340 mm', 'Top of the torso shell above the floor'),
    ('pwall', '2.4 mm', 'Printed shell wall (6 perimeters at 0.4)'),
    ('corner_r', '30 mm', 'Plan-view radius of the vertical torso corners'),
    ('top_r', '20 mm', 'Radius of the rounded top edges'),
    ('shell_x', 'body_w/2', 'Outer half-width of the torso'),
    ('shell_y', 'body_d/2', 'Outer half-depth of the torso'),
    ('plate_z', '30 mm', 'Ground clearance under the chassis plate'),
    ('plate_t', '6 mm', 'Chassis plate thickness (6 mm birch ply)'),
    ('plate_top', 'plate_z + plate_t', 'Top of the chassis plate'),
    ('plate_w', 'body_w - 2*pwall - 1 mm', 'Chassis plate X (inside the skirts)'),
    ('plate_d', 'body_d - 2*pwall - 1 mm', 'Chassis plate Y'),
    ('wheel_d', '100 mm', 'Mecanum wheel OD (SRC)'),
    ('wheel_w', '50 mm', 'Mecanum wheel width (SRC Studica/Nexus 100 mm: 50)'),
    ('wheel_y', '100 mm', 'Wheel centre |Y| (half wheelbase)'),
    ('wheel_proud', '4 mm', 'Wheel outer face sticks out past the shell side'),
    ('wheel_x_out', 'shell_x + wheel_proud', 'Wheel outer face |X|'),
    ('wheel_xc', 'wheel_x_out - wheel_w/2', 'Wheel centre |X| (half track)'),
    ('well_gap', '3 mm', 'Wheel inner face to motor-mount wall gap'),
    ('mount_wall', '5 mm', 'Printed motor mount wall'),
    ('notch_x', 'wheel_x_out - wheel_w - well_gap', 'Plate wheel notch starts at |X|'),
    ('notch_y', 'wheel_y - wheel_d/2 - 5 mm', 'Plate wheel notch starts at |Y|'),
    ('gb_face', 'notch_x - mount_wall', 'JGB37 gearbox face |X|'),
    ('axle_z', 'wheel_d/2', 'Wheel axle height'),
    ('shaft_off', '7 mm', 'JGB37 output shaft offset from the motor axis'),
    ('motor_z', 'axle_z + shaft_off', 'Motor axis height (shaft below the axis)'),
    ('gb_d', '37 mm', 'JGB37 gearbox diameter'),
    ('gb_len', '22 mm', 'JGB37 gearbox length, 19:1 (530 rpm)'),
    ('can_d', '33 mm', 'JGB37 motor can diameter'),
    ('can_len', '22.7 mm', 'JGB37 motor can length'),
    ('cap_len', '3.5 mm', 'JGB37 rear cap'),
    ('enc_len', '12 mm', 'Hall encoder length (EST, measure)'),
    ('collar_len', '6 mm', 'Shaft coupler collar'),
    ('shaft_len', '15.5 mm', '6 mm D-shaft length'),
    ('fender_z', 'wheel_d + 12 mm', 'Underside of the corner fenders = L1 deck underside'),
]


def define_params():
    for n, e, cmt in PARAMS:
        param(n, e, cmt)


def chassis():
    c = fresh('Chassis plate')
    sk = sketch(c, 'z', 'plate outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': 'plate_w', 'y': 'plate_d'})
    plate = extrude(c, sk, 'plate_z', 'plate_t', name='chassis plate 6 mm birch ply').bodies.item(0)
    fillet(c, edges_where(plate, lambda e: is_axis_line(e, 'z')), '6 mm')
    for sx in (1, -1):
        for sy in (1, -1):
            X = S(sx, '(notch_x + plate_w/2)/2')
            Y = S(sy, '(notch_y + plate_d/2)/2')
            box(c, 'wheel notch', {'x': X, 'y': Y, 'z': 'plate_z + plate_t/2'},
                {'x': '(plate_w/2 - notch_x) + 0.02 mm', 'y': '(plate_d/2 - notch_y) + 0.02 mm', 'z': 'plate_t + 1 mm'},
                op=CUT, bodies=[plate])
    finish(plate, 'Birch', 'Bamboo Light - Semigloss')
    log('plate ok')


def drive_corner(sx, sy, tag):
    c = fresh('Drive %s' % tag)
    m = sub(c, 'Motor JGB37-520 19to1 %s' % tag)
    yc = S(sy, 'wheel_y')
    zc = 'motor_z'
    gb = C(m, 'gearbox', 'x', S(sx, 'gb_face - gb_len/2'), yc, zc, 'gb_d', 'gb_len', 'Steel', ALU)
    can = C(m, 'motor can', 'x', S(sx, 'gb_face - gb_len - can_len/2'), yc, zc, 'can_d', 'can_len', 'Steel', 'Chrome')
    C(m, 'rear cap', 'x', S(sx, 'gb_face - gb_len - can_len - cap_len/2'), yc, zc, 'can_d - 3 mm', 'cap_len', 'ABS Plastic', BLACK)
    C(m, 'encoder', 'x', S(sx, 'gb_face - gb_len - can_len - cap_len - enc_len/2'), yc, zc, 'can_d', 'enc_len', 'FR4', GREEN)
    C(m, 'shaft coupler', 'x', S(sx, 'gb_face + collar_len/2'), yc, 'axle_z', '12 mm', 'collar_len', 'Steel', ALU)
    C(m, 'shaft', 'x', S(sx, 'gb_face + collar_len + shaft_len/2'), yc, 'axle_z', '6 mm', 'shaft_len', 'Steel', ALU)

    # ---- wheel: hub + side plates + rollers (rollers are a base feature)
    w = sub(c, 'Wheel mecanum 100 %s' % tag)
    hub = C(w, 'hub', 'x', S(sx, 'wheel_xc'), yc, 'axle_z', '26 mm', 'wheel_w - 4 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    p1 = C(w, 'side plate in', 'x', S(sx, 'wheel_xc - wheel_w/2 + 1.5 mm'), yc, 'axle_z', '66 mm', '3 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    p2 = C(w, 'side plate out', 'x', S(sx, 'wheel_xc + wheel_w/2 - 1.5 mm'), yc, 'axle_z', '66 mm', '3 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    C(w, 'shaft bore', 'x', S(sx, 'wheel_xc'), yc, 'axle_z', '6 mm', 'wheel_w + 2 mm', op=CUT, bodies=[hub, p1, p2])
    R = mm('wheel_d') / 2
    rr = 10.5
    rc = R - rr
    L = 40.0
    xw, yw, zw = mm(S(sx, 'wheel_xc')), mm(yc), mm('axle_z')
    # X configuration: seen from above, the TOP rollers point at the robot centre
    # (ground rollers perpendicular to the centre lines, so the robot can spin and strafe).
    hand = -1 if sx * sy > 0 else 1
    n = 9
    tbs = []
    for i in range(n):
        th = math.radians(i * 360.0 / n)
        cy_, cz_ = yw + rc * math.cos(th), zw + rc * math.sin(th)
        t = (0.0, -math.sin(th), math.cos(th))
        a = (hand * 0.7071, t[1] * 0.7071, t[2] * 0.7071)
        h = L / 2
        e1 = P(xw - a[0] * h, cy_ - a[1] * h, cz_ - a[2] * h)
        mid = P(xw, cy_, cz_)
        e2 = P(xw + a[0] * h, cy_ + a[1] * h, cz_ + a[2] * h)
        c1 = TB.createCylinderOrCone(e1, 0.5, mid, rr / 10.0)
        c2 = TB.createCylinderOrCone(mid, rr / 10.0, e2, 0.5)
        TB.booleanOperation(c1, c2, adsk.fusion.BooleanTypes.UnionBooleanType)
        tbs.append(c1)
    for b in base_bodies(w, 'rollers', tbs, ['roller %d' % (i + 1) for i in range(n)]):
        finish(b, 'Rubber, Black', 'Rubber - Soft')

    # ---- printed motor mount + wheel-well liner (PETG)
    mt = sub(c, 'Motor mount + well liner %s (printed)' % tag)
    yo = S(sy, '(notch_y - 3 mm + shell_y - pwall - 0.5 mm)/2')
    ylen = 'shell_y - pwall - 0.5 mm - notch_y + 3 mm'
    wall = B(mt, 'mount wall', S(sx, 'gb_face + mount_wall/2'), yo, 'plate_top', 'mount_wall', ylen, 'fender_z - plate_top', 'PET Plastic', BLACK)
    yw_ = B(mt, 'liner y-wall', S(sx, '(gb_face + shell_x - pwall - 0.5 mm)/2'), S(sy, 'notch_y - 1.5 mm'), 'plate_top',
            'shell_x - pwall - 0.5 mm - gb_face', '3 mm', 'fender_z - plate_top')
    tools = [yw_]
    for gy in (1, -1):
        tools.append(B(mt, 'gusset', S(sx, 'gb_face - 12 mm'), '(%s) + (%d)*(gb_d/2 + 4 mm)' % (yc, gy), 'plate_top', '24 mm', '4 mm', '32 mm'))
        tools.append(B(mt, 'foot', S(sx, 'gb_face - 12 mm'), '(%s) + (%d)*(gb_d/2 + 8 mm)' % (yc, gy), 'plate_top', '24 mm', '12 mm', '5 mm'))
    join(mt, wall, tools)
    # gearbox: 6x M3 on PCD 31, coupler hole; feet: 2x M3 each into the plate
    C(mt, 'coupler hole', 'x', S(sx, 'gb_face + mount_wall/2'), yc, 'axle_z', '14 mm', 'mount_wall + 1 mm', op=CUT, bodies=[wall])
    for k in range(6):
        a = math.radians(30 + 60 * k)
        C(mt, 'M3', 'x', S(sx, 'gb_face + mount_wall/2'), '(%s) + %.4f*15.5 mm' % (yc, math.cos(a)),
          'motor_z + %.4f*15.5 mm' % math.sin(a), '3.4 mm', 'mount_wall + 1 mm', op=CUT, bodies=[wall])
    for gy in (1, -1):
        for ox in ('-6 mm', '6 mm'):
            C(mt, 'M3 foot', 'z', '%s + %s' % (S(sx, 'gb_face - 12 mm'), ox), '(%s) + (%d)*(gb_d/2 + 10 mm)' % (yc, gy), 'plate_top + 2.5 mm',
              '3.4 mm', '6 mm', op=CUT, bodies=[wall])
    wall.name = 'motor mount + well liner (printed)'
    sad = B(mt, 'motor saddle (printed)', S(sx, 'gb_face - gb_len - can_len/2'), yc, 'plate_top', '14 mm', 'can_d - 4 mm', 'motor_z - plate_top', 'PET Plastic', BLACK)
    C(mt, 'can cradle', 'x', S(sx, 'gb_face - gb_len - can_len/2'), yc, 'motor_z', 'can_d + 0.4 mm', '16 mm', op=CUT, bodies=[sad])
    log('corner', tag, 'ok')


def main():
    define_params()
    chassis()
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        drive_corner(sx, sy, tag)
    done()
