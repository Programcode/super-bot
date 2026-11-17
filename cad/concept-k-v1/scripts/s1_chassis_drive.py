# Stage 1: user parameters, chassis plate, 4x drive corner (JGB37 motor, printed
# motor mount / wheel-well liner, 80 mm mecanum wheel).
# Run through the loader: exec(sblib.py) then exec(this) then main().

PARAMS = [
    # name, expression, comment
    ('plate_w', '400 mm', 'Chassis plate X (DIY 40x40 plate, birch ply)'),
    ('plate_d', '400 mm', 'Chassis plate Y'),
    ('plate_t', '6 mm', 'Plate thickness (6 mm birch ply)'),
    ('plate_z', '20 mm', 'Ground clearance under the plate'),
    ('plate_top', 'plate_z + plate_t', 'Top of plate'),
    ('wall_t', '3 mm', 'Shell panel thickness (3 mm smoked acrylic)'),
    ('pwall', '2.4 mm', 'Printed part wall (6 perimeters @0.4)'),
    ('shell_x', 'plate_w/2 + wall_t', 'Outer half-width of body'),
    ('shell_y', 'plate_d/2 + wall_t', 'Outer half-depth of body'),
    ('body_top', '140 mm', 'Top of body above ground'),
    ('corner_r', '40 mm', 'Plan-view corner radius of the body'),
    ('wheel_d', '80 mm', 'Mecanum wheel OD (SRC handsontec/dfrobot)'),
    ('wheel_w', '37.5 mm', 'Mecanum wheel width (SRC)'),
    ('wheel_y', '150 mm', 'Wheel centre |Y| = half wheelbase'),
    ('wheel_x_out', 'shell_x - 2 mm', 'Wheel outer face |X| (tucked 2 mm inside body)'),
    ('wheel_xc', 'wheel_x_out - wheel_w/2', 'Wheel centre |X|'),
    ('well_gap', '2 mm', 'Wheel to wheel-well wall gap'),
    ('mount_wall', '5 mm', 'Printed motor mount wall'),
    ('notch_x', 'wheel_x_out - wheel_w - well_gap', 'Plate wheel notch starts at |X|'),
    ('notch_y', 'wheel_y - wheel_d/2 - 5 mm', 'Plate wheel notch starts at |Y|'),
    ('gb_face', 'notch_x - mount_wall', 'JGB37 gearbox face |X|'),
    ('axle_z', 'wheel_d/2', 'Wheel axle height'),
    ('shaft_off', '7 mm', 'JGB37 output shaft offset from motor axis (SRC, M)'),
    ('motor_z', 'axle_z + shaft_off', 'Motor axis height (shaft below axis)'),
    ('gb_d', '37 mm', 'JGB37 gearbox dia (SRC)'),
    ('gb_len', '24 mm', 'JGB37 gearbox length, 56:1-90:1 (SRC)'),
    ('can_d', '33 mm', 'JGB37 motor can dia (SRC)'),
    ('can_len', '22.7 mm', 'JGB37 motor can length (SRC)'),
    ('cap_len', '3.5 mm', 'JGB37 rear cap (SRC)'),
    ('enc_len', '13 mm', 'Hall encoder length (EST)'),
    ('collar_len', '6 mm', 'Shaft collar (SRC)'),
    ('shaft_len', '15.5 mm', '6 mm D-shaft length (SRC)'),
    ('fender_z', 'wheel_d + 8 mm', 'Underside of the wheel fender'),
]


def define_params():
    for n, e, cmt in PARAMS:
        param(n, e, cmt)


def chassis():
    c = fresh('Chassis plate')
    sk = sketch(c, 'z', 'plate outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': 'plate_w', 'y': 'plate_d'})
    f = extrude(c, sk, 'plate_z', 'plate_t', name='Chassis plate')
    plate = f.bodies.item(0)
    # wheel notches
    for sx in (1, -1):
        for sy in (1, -1):
            X = '%s(notch_x + plate_w/2)/2' % ('' if sx > 0 else '-')
            Y = '%s(notch_y + plate_d/2)/2' % ('' if sy > 0 else '-')
            box(c, 'notch', {'x': X, 'y': Y, 'z': 'plate_z + plate_t/2'},
                {'x': '(plate_w/2 - notch_x) + 0.02 mm', 'y': '(plate_d/2 - notch_y) + 0.02 mm', 'z': 'plate_t + 1 mm'},
                op=CUT, bodies=[plate])
    finish(plate, 'Birch', 'Bamboo Light - Semigloss')
    log('plate ok', plate.volume)


def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def drive_corner(sx, sy, tag):
    c = fresh('Drive %s' % tag)
    # ---- motor (JGB37-520 + Hall encoder)
    m = sub(c, 'Motor JGB37-520 %s' % tag)
    yc = S(sy, 'wheel_y')
    zc = 'motor_z'
    gb = cyl(m, 'gearbox', 'x', {'x': S(sx, 'gb_face - gb_len/2'), 'y': yc, 'z': zc}, 'gb_d', 'gb_len')
    can = cyl(m, 'motor can', 'x', {'x': S(sx, 'gb_face - gb_len - can_len/2'), 'y': yc, 'z': zc}, 'can_d', 'can_len')
    cap = cyl(m, 'rear cap', 'x', {'x': S(sx, 'gb_face - gb_len - can_len - cap_len/2'), 'y': yc, 'z': zc}, 'can_d - 3 mm', 'cap_len')
    enc = cyl(m, 'encoder', 'x', {'x': S(sx, 'gb_face - gb_len - can_len - cap_len - enc_len/2'), 'y': yc, 'z': zc}, 'can_d', 'enc_len')
    col = cyl(m, 'shaft collar', 'x', {'x': S(sx, 'gb_face + collar_len/2'), 'y': yc, 'z': 'axle_z'}, '12 mm', 'collar_len')
    sh = cyl(m, 'shaft', 'x', {'x': S(sx, 'gb_face + collar_len + shaft_len/2'), 'y': yc, 'z': 'axle_z'}, '6 mm', 'shaft_len')
    for b in (gb, col, sh):
        finish(b, 'Steel', 'Aluminum - Satin')
    finish(can, 'Steel', 'Chrome')
    finish(cap, 'ABS Plastic', 'Plastic - Matte (Black)')
    finish(enc, 'FR4', 'Plastic - Matte (Green)')

    # ---- wheel: hub plates + 9 rollers at 45 deg (rollers as base feature)
    w = sub(c, 'Wheel mecanum 80 %s' % tag)
    hub = cyl(w, 'hub', 'x', {'x': S(sx, 'wheel_xc'), 'y': yc, 'z': 'axle_z'}, '22 mm', 'wheel_w - 4 mm')
    p1 = cyl(w, 'side plate in', 'x', {'x': S(sx, 'wheel_xc - wheel_w/2 + 1.5 mm'), 'y': yc, 'z': 'axle_z'}, '52 mm', '3 mm')
    p2 = cyl(w, 'side plate out', 'x', {'x': S(sx, 'wheel_xc + wheel_w/2 - 1.5 mm'), 'y': yc, 'z': 'axle_z'}, '52 mm', '3 mm')
    for b in (hub, p1, p2):
        finish(b, 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    cyl(w, 'shaft bore', 'x', {'x': S(sx, 'wheel_xc'), 'y': yc, 'z': 'axle_z'}, '6 mm', 'wheel_w + 2 mm', op=CUT, bodies=[hub, p1, p2])
    R = mm('wheel_d') / 2
    rr = 8.5
    rc = R - rr
    L = 32.0
    xw, yw, zw = mm(S(sx, 'wheel_xc')), mm(yc), mm('axle_z')
    hand = 1 if sx * sy > 0 else -1  # X-configuration: FR/RL one hand, FL/RR the other
    tbs = []
    for i in range(9):
        th = math.radians(i * 40.0)
        cy_, cz_ = yw + rc * math.cos(th), zw + rc * math.sin(th)
        t = (0.0, -math.sin(th), math.cos(th))
        a = (hand * 0.7071, t[1] * 0.7071, t[2] * 0.7071)
        h = L / 2
        e1 = P(xw - a[0] * h, cy_ - a[1] * h, cz_ - a[2] * h)
        mid = P(xw, cy_, cz_)
        e2 = P(xw + a[0] * h, cy_ + a[1] * h, cz_ + a[2] * h)
        c1 = TB.createCylinderOrCone(e1, 0.45, mid, rr / 10.0)
        c2 = TB.createCylinderOrCone(mid, rr / 10.0, e2, 0.45)
        TB.booleanOperation(c1, c2, adsk.fusion.BooleanTypes.UnionBooleanType)
        tbs.append(c1)
    rollers = base_bodies(w, 'rollers', tbs, ['roller %d' % (i + 1) for i in range(9)])
    for b in rollers:
        finish(b, 'Rubber, Black', 'Rubber - Soft')

    # ---- printed motor mount + wheel-well liner (PETG)
    mt = sub(c, 'Motor mount + well liner %s' % tag)
    yo = S(sy, '(notch_y - 3 mm + shell_y)/2')
    wall = box(mt, 'mount wall', {'x': S(sx, 'gb_face + mount_wall/2'), 'y': yo, 'z': '(plate_top + fender_z)/2'},
               {'x': 'mount_wall', 'y': 'shell_y - notch_y + 3 mm', 'z': 'fender_z - plate_top'})
    yw_ = box(mt, 'liner y-wall', {'x': S(sx, '(gb_face + shell_x)/2'), 'y': S(sy, 'notch_y - 1.5 mm'), 'z': '(plate_top + fender_z)/2'},
              {'x': 'shell_x - gb_face', 'y': '3 mm', 'z': 'fender_z - plate_top'})
    combine(mt, wall, [yw_], adsk.fusion.FeatureOperations.JoinFeatureOperation)
    # gussets beside the gearbox, and a saddle under the motor can
    for gy in (1, -1):
        g = box(mt, 'gusset', {'x': S(sx, 'gb_face - 14 mm'), 'y': '(%s) + (%d)*(gb_d/2 + 4 mm)' % (yc, gy), 'z': 'plate_top + 17 mm'},
                {'x': '28 mm', 'y': '4 mm', 'z': '34 mm'})
        combine(mt, wall, [g], adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ft = box(mt, 'foot', {'x': S(sx, 'gb_face - 14 mm'), 'y': '(%s) + (%d)*(gb_d/2 + 8 mm)' % (yc, gy), 'z': 'plate_top + 2.5 mm'},
                 {'x': '28 mm', 'y': '12 mm', 'z': '5 mm'})
        combine(mt, wall, [ft], adsk.fusion.FeatureOperations.JoinFeatureOperation)
    sad = box(mt, 'saddle', {'x': S(sx, 'gb_face - gb_len - can_len/2'), 'y': yc, 'z': '(plate_top + motor_z)/2'},
              {'x': '14 mm', 'y': 'can_d - 4 mm', 'z': 'motor_z - plate_top'})
    # cradle cut for the can (on the saddle before joining), collar hole and 6x M3 on PCD 31
    cyl(mt, 'can cradle', 'x', {'x': S(sx, 'gb_face - gb_len - can_len/2'), 'y': yc, 'z': 'motor_z'}, 'can_d + 0.4 mm', '16 mm', op=CUT, bodies=[sad])
    sad.name = 'motor saddle (printed)'
    finish(sad, 'PET Plastic', 'Plastic - Matte (Black)')
    cyl(mt, 'collar hole', 'x', {'x': S(sx, 'gb_face + mount_wall/2'), 'y': yc, 'z': 'axle_z'}, '13 mm', 'mount_wall + 1 mm', op=CUT, bodies=[wall])
    for k in range(6):
        a = math.radians(30 + 60 * k)
        cyl(mt, 'M3', 'x', {'x': S(sx, 'gb_face + mount_wall/2'), 'y': '(%s) + %.4f*15.5 mm' % (yc, math.cos(a)),
                            'z': 'motor_z + %.4f*15.5 mm' % math.sin(a)}, '3.4 mm', 'mount_wall + 1 mm', op=CUT, bodies=[wall])
    wall.name = 'motor mount + well liner'
    finish(wall, 'PET Plastic', 'Plastic - Matte (Black)')
    log('corner', tag, 'ok')


def main():
    define_params()
    chassis()
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        drive_corner(sx, sy, tag)
    done()
