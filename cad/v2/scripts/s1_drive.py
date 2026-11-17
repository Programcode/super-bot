# Stage 1: user parameters, chassis plate, 4 drive corners.
# JGB37-520 19:1 motors sit inside the body at the corners against printed mounts; the
# 100 mm mecanum wheels sit OUTSIDE the body sides, at the corners, like the target photo.

PARAMS = [
    ('body_w', '200 mm', 'Body box width X (shell outside)'),
    ('body_d', '200 mm', 'Body box depth Y'),
    ('body_h', '1.25 * body_w', 'Body box height (1.25 x width, as in the target photo)'),
    ('body_z0', '28 mm', 'Body box bottom Z'),
    ('body_top', 'body_z0 + body_h', 'Body box top Z (T)'),
    ('pwall', '2.4 mm', 'Printed shell wall (6 perimeters at 0.4)'),
    ('corner_r', '14 mm', 'Vertical corner radius of the body'),
    ('top_r', '12 mm', 'Radius of the rounded top edges'),
    ('shell_x', 'body_w/2', 'Body outer half-width'),
    ('shell_y', 'body_d/2', 'Body outer half-depth'),
    ('plate_z', '30 mm', 'Ground clearance under the chassis plate'),
    ('plate_t', '6 mm', 'Chassis plate thickness (6 mm birch ply)'),
    ('plate_top', 'plate_z + plate_t', 'Top of the chassis plate'),
    ('plate_w', 'body_w - 2*pwall - 1 mm', 'Chassis plate X'),
    ('plate_d', 'body_d - 2*pwall - 1 mm', 'Chassis plate Y'),
    ('gb_d', '37 mm', 'JGB37 gearbox diameter (SRC)'),
    ('gb_len', '22 mm', 'JGB37 gearbox length, 19:1 (SRC)'),
    ('can_d', '33 mm', 'JGB37 motor can diameter (SRC)'),
    ('can_len', '22.7 mm', 'JGB37 motor can length (SRC)'),
    ('cap_len', '3.5 mm', 'JGB37 rear cap (SRC)'),
    ('enc_len', '12 mm', 'Hall encoder length (EST, measure)'),
    ('collar_len', '6 mm', 'Gearbox pilot boss (SRC 12 x 6)'),
    ('shaft_len', '15.5 mm', '6 mm D-shaft length (SRC)'),
    ('shaft_off', '7 mm', 'Output shaft offset from the motor axis (SRC drawing)'),
    ('mount_wall', '5 mm', 'Printed motor mount wall'),
    ('gb_face', 'shell_x - pwall - 0.5 mm - mount_wall', 'Gearbox face |X|'),
    ('wheel_d', '100 mm', 'Mecanum wheel OD (SRC)'),
    ('wheel_w', '50 mm', 'Mecanum wheel width (SRC Studica/Nexus 100 mm)'),
    ('wheel_gap', '3 mm', 'Body side to wheel inner face'),
    ('wheel_xc', 'shell_x + wheel_gap + wheel_w/2', 'Wheel centre |X| (half track)'),
    ('wheel_y', 'shell_y - pwall - gb_d/2 - 3 mm', 'Wheel centre |Y| (half wheelbase); motors just inside the front/rear walls'),
    ('axle_z', 'wheel_d/2', 'Wheel axle height'),
    ('motor_z', 'axle_z + shaft_off', 'Motor axis height (shaft below the axis)'),
]


def define_params():
    for n, e, cmt in PARAMS:
        param(n, e, cmt)


def chassis():
    c = fresh('Chassis plate')
    sk = sketch(c, 'z', 'plate outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': 'plate_w', 'y': 'plate_d'})
    plate = extrude(c, sk, 'plate_z', 'plate_t', name='chassis plate 6 mm birch ply').bodies.item(0)
    fillet(c, edges_where(plate, lambda e: is_axis_line(e, 'z')), 'corner_r - pwall - 1 mm')
    finish(plate, 'Birch', appearance('SB Dark grey ply', 'Plastic - Matte (Gray)', color=(70, 72, 78)))
    log('plate ok')


def drive_corner(sx, sy, tag):
    c = fresh('Drive %s' % tag)
    m = sub(c, 'Motor JGB37-520 19to1 %s' % tag)
    yc = S(sy, 'wheel_y')
    zc = 'motor_z'
    C(m, 'gearbox', 'x', S(sx, 'gb_face - gb_len/2'), yc, zc, 'gb_d', 'gb_len', 'Steel', ALU)
    C(m, 'motor can', 'x', S(sx, 'gb_face - gb_len - can_len/2'), yc, zc, 'can_d', 'can_len', 'Steel', 'Chrome')
    C(m, 'rear cap', 'x', S(sx, 'gb_face - gb_len - can_len - cap_len/2'), yc, zc, 'can_d - 3 mm', 'cap_len', 'ABS Plastic', BLACK)
    C(m, 'encoder', 'x', S(sx, 'gb_face - gb_len - can_len - cap_len - enc_len/2'), yc, zc, 'can_d', 'enc_len', 'FR4', GREEN)
    C(m, 'pilot boss', 'x', S(sx, 'gb_face + collar_len/2'), yc, 'axle_z', '12 mm', 'collar_len', 'Steel', ALU)
    C(m, 'shaft', 'x', S(sx, 'gb_face + collar_len + shaft_len/2'), yc, 'axle_z', '6 mm', 'shaft_len', 'Steel', ALU)

    w = sub(c, 'Wheel mecanum 100 %s' % tag)
    hub = C(w, 'hub', 'x', S(sx, 'wheel_xc'), yc, 'axle_z', '26 mm', 'wheel_w - 4 mm', 'Aluminum 6061', 'Aluminum - Anodized Rough (Grey)')
    p1 = C(w, 'side plate in', 'x', S(sx, 'wheel_xc - wheel_w/2 + 1.5 mm'), yc, 'axle_z', '66 mm', '3 mm', 'Aluminum 6061', 'Plastic - Matte (Black)')
    p2 = C(w, 'side plate out', 'x', S(sx, 'wheel_xc + wheel_w/2 - 1.5 mm'), yc, 'axle_z', '66 mm', '3 mm', 'Aluminum 6061', 'Plastic - Matte (Black)')
    C(w, 'hub cap', 'x', S(sx, 'wheel_xc + wheel_w/2 + 0.5 mm'), yc, 'axle_z', '16 mm', '1 mm', 'Steel', 'Chrome')
    C(w, 'shaft bore', 'x', S(sx, 'wheel_xc'), yc, 'axle_z', '6 mm', 'wheel_w + 2 mm', op=CUT, bodies=[hub, p1])
    R = mm('wheel_d') / 2
    rr = 10.5
    rc = R - rr
    L = 42.0
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
        c1 = TB.createCylinderOrCone(e1, 0.55, mid, rr / 10.0)
        c2 = TB.createCylinderOrCone(mid, rr / 10.0, e2, 0.55)
        TB.booleanOperation(c1, c2, adsk.fusion.BooleanTypes.UnionBooleanType)
        tbs.append(c1)
    for b in base_bodies(w, 'rollers', tbs, ['roller %d' % (i + 1) for i in range(n)]):
        finish(b, 'Rubber, Black', 'Rubber - Soft')

    # printed motor mount: wall against the shell side with 6x M3 on PCD 31 + pilot hole, feet, gussets
    mt = sub(c, 'Motor mount %s (printed)' % tag)
    y0, y1 = '(wheel_y - 24 mm)', '(shell_y - corner_r + 2 mm)'
    yo = S(sy, '(%s + %s)/2' % (y0, y1))
    wall = B(mt, 'mount wall', S(sx, 'gb_face + mount_wall/2'), yo, 'plate_top', 'mount_wall', '%s - %s' % (y1, y0), 'motor_z + 22 mm - plate_top', 'PET Plastic', BLACK)
    tools = []
    for gy in (1, -1):
        gyy = '(%s) + (%d)*(gb_d/2 + 4 mm)' % (yc, gy)
        if gy * sy > 0:
            continue  # the outer side is up against the front/rear wall
        tools.append(B(mt, 'gusset', S(sx, 'gb_face - 12 mm'), gyy, 'plate_top', '24 mm', '4 mm', '30 mm'))
        tools.append(B(mt, 'foot', S(sx, 'gb_face - 12 mm'), '(%s) + (%d)*(gb_d/2 + 7 mm)' % (yc, gy), 'plate_top', '24 mm', '10 mm', '5 mm'))
    join(mt, wall, tools)
    C(mt, 'pilot hole', 'x', S(sx, 'gb_face + mount_wall/2'), yc, 'axle_z', '12.4 mm', 'mount_wall + 1 mm', op=CUT, bodies=[wall])
    for k in range(6):
        a = math.radians(30 + 60 * k)
        C(mt, 'M3', 'x', S(sx, 'gb_face + mount_wall/2'), '(%s) + %.4f*15.5 mm' % (yc, math.cos(a)),
          'motor_z + %.4f*15.5 mm' % math.sin(a), '3.4 mm', 'mount_wall + 1 mm', op=CUT, bodies=[wall])
    wall.name = 'motor mount (printed)'
    sad = B(mt, 'motor saddle (printed)', S(sx, 'gb_face - gb_len - can_len/2'), yc, 'plate_top', '14 mm', 'can_d - 4 mm', 'motor_z - plate_top', 'PET Plastic', BLACK)
    C(mt, 'can cradle', 'x', S(sx, 'gb_face - gb_len - can_len/2'), yc, 'motor_z', 'can_d + 0.4 mm', '16 mm', op=CUT, bodies=[sad])
    log('corner', tag, 'ok')


def main():
    define_params()
    chassis()
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        drive_corner(sx, sy, tag)
    done()
