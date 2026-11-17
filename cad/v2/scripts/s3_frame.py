# Stage 3: frame, a closed ply box inside the shell (no corner rods):
#   spine (front rack, boards on its front face = the view through the front wall),
#   rear plate, two side cheeks (boards on their outer faces = the view through the side walls),
#   top deck. Spine and rear plate are notched at the bottom for the battery tunnel.
# All 4 mm birch ply, laser cut; joined by printed brackets.

PARAMS3 = [
    ('ply_t', '4 mm', 'Frame ply thickness (4 mm birch ply)'),
    ('spine_y', '44 mm', 'Spine front face Y'),
    ('rear_y', '-51 mm', 'Rear plate front face Y'),
    ('cheek_x', '76 mm', 'Side cheek inner face |X|'),
    ('in_x', 'shell_x - pwall - 1 mm', 'Frame half-width (inside the shell)'),
    ('top_deck_z', 'body_top - 14 mm', 'Top deck underside'),
    ('top_deck_top', 'top_deck_z + ply_t', 'Top deck top'),
    ('pan_y', '20 mm', 'Head pan axis Y (forward of centre; the pan gear clears the spine)'),
    ('pan_servo_x', '36 mm', 'Pan servo shaft X (1:1 gear pair, 36 mm centre distance)'),
    ('shaft_od', '25 mm', 'Pan shaft: 25 x 1 mm aluminium tube (fits 6805 bearings)'),
    ('lidar_x', '-50 mm', 'Lidar centre X (rear left, as in the target photo)'),
    ('lidar_y', '-58 mm', 'Lidar centre Y (rear)'),
    ('notch_z', 'plate_top + 44 mm', 'Spine notch top (XT60 + sled front pass under)'),
    ('rnotch_z', 'body_z0 + 96 mm', 'Rear plate notch top (pack + BMS + fuse pass under)'),
    ('frame_z1', 'plate_top + 46 mm', 'Bottom of the cheeks and rear plate (clear of the motor mounts)'),
]


def define():
    for n, e, cm in PARAMS3:
        param(n, e, cm)


def ply(b):
    finish(b, 'Birch', appearance('SB Dark grey ply', 'Plastic - Matte (Gray)', color=(70, 72, 78)))


def frame():
    c = fresh('Frame (4 mm ply)')
    H = 'top_deck_z - plate_top'
    sp = B(c, 'spine', '0 mm', 'spine_y - ply_t/2', 'plate_top', '2*in_x', 'ply_t', H)
    B(c, 'tunnel notch', '0 mm', 'spine_y - ply_t/2', 'plate_top - 1 mm', '2*tun_hw', 'ply_t + 2 mm', 'notch_z - plate_top + 1 mm', op=CUT, bodies=[sp])
    for (x, z, w, h) in (('-30 mm', 'plate_top + 120 mm', '12 mm', '10 mm'),   # 5 V lead: buck (back) to Pi USB-C (front)
                         ('0 mm', 'top_deck_z - 50 mm', '24 mm', '12 mm'),       # camera ribbon + head wiring
                         ('40 mm', 'plate_top + 56 mm', '30 mm', '10 mm')):      # driver board / ESP32 logic loom
        B(c, 'slot', x, 'spine_y - ply_t/2', z, w, 'ply_t + 2 mm', h, op=CUT, bodies=[sp])
    sp.name = 'spine 4 mm birch ply'
    H1 = 'top_deck_z - frame_z1'
    rp = B(c, 'rear plate', '0 mm', 'rear_y - ply_t/2', 'frame_z1', '2*in_x', 'ply_t', H1)
    B(c, 'tunnel notch', '0 mm', 'rear_y - ply_t/2', 'frame_z1 - 1 mm', '2*tun_hw', 'ply_t + 2 mm', 'rnotch_z - frame_z1 + 1 mm', op=CUT, bodies=[rp])
    B(c, 'housing notch', '0 mm', 'spine_y - ply_t/2', 'top_deck_z - 26 mm', '50 mm', 'ply_t + 2 mm', '27 mm', op=CUT, bodies=[sp])
    B(c, 'speaker + PDB loom slot', '-40 mm', 'rear_y - ply_t/2', 'plate_top + 150 mm', '16 mm', 'ply_t + 2 mm', '10 mm', op=CUT, bodies=[rp])
    rp.name = 'rear plate 4 mm birch ply'
    for sx in (1, -1):
        ch = B(c, 'side cheek', S(sx, 'cheek_x + ply_t/2'), '(spine_y - ply_t + rear_y)/2', 'frame_z1', 'ply_t', '(spine_y - ply_t) - rear_y', H1)
        pl_ = B(c, 'cheek pillar (printed)', S(sx, 'cheek_x + ply_t/2'), '0 mm', 'plate_top', '10 mm', '20 mm', 'frame_z1 - plate_top', 'PET Plastic', BLACK)
        B(c, 'loom slot', S(sx, 'cheek_x + ply_t/2'), '-25 mm', 'frame_z1 + 24 mm', 'ply_t + 2 mm', '30 mm', '10 mm', op=CUT, bodies=[ch])
        ch.name = 'side cheek %s 4 mm birch ply' % ('right' if sx > 0 else 'left')
        ply(ch)
    ply(sp)
    ply(rp)
    # top deck
    sk = sketch(c, 'z', 'top deck outline')
    rect(sk, {'x': '0 mm', 'y': '0 mm'}, {'x': '2*in_x', 'y': '2*(shell_y - pwall - 1 mm)'})
    d = extrude(c, sk, 'top_deck_z', 'ply_t', name='top deck 4 mm birch ply').bodies.item(0)
    fillet(c, edges_where(d, lambda e: is_axis_line(e, 'z')), 'corner_r - pwall - 1 mm')
    C(c, 'pan shaft hole', 'z', '0 mm', 'pan_y', 'top_deck_z + ply_t/2', 'shaft_od + 2 mm', 'ply_t + 2 mm', op=CUT, bodies=[d])
    for (hx, hy) in ((-24, -24), (24, -24), (-24, 24), (24, 24)):
        C(c, 'plinth M3', 'z', '%d mm' % hx, '(pan_y) + %d mm' % hy, 'top_deck_z + ply_t/2', '3.4 mm', 'ply_t + 2 mm', op=CUT, bodies=[d])
    for (hx, hy) in ((-24, -22), (24, -22), (-24, 22), (24, 22)):
        C(c, 'pod M3', 'z', '(lidar_x) + %d mm' % hx, '(lidar_y) + %d mm' % hy, 'top_deck_z + ply_t/2', '3.4 mm', 'ply_t + 2 mm', op=CUT, bodies=[d])
    C(c, 'lidar cable hole', 'z', 'lidar_x', 'lidar_y', 'top_deck_z + ply_t/2', '12 mm', 'ply_t + 2 mm', op=CUT, bodies=[d])
    for k in range(7):
        B(c, 'chimney vent', '%d*18 mm' % (k - 3), '(spine_y + 6 mm + shell_y - pwall - 6 mm)/2', 'top_deck_z - 1 mm', '7 mm',
          '(shell_y - pwall - 6 mm) - (spine_y + 6 mm)', 'ply_t + 2 mm', op=CUT, bodies=[d])
    ply(d)
    # printed brackets: spine/rear plate/cheeks to the plate and to the top deck
    br = []
    for (x, y, zs) in (('-50 mm', 'spine_y - ply_t - 5 mm', ('plate_top', 'top_deck_z - 10 mm')), ('50 mm', 'spine_y - ply_t - 5 mm', ('plate_top', 'top_deck_z - 10 mm')),
                       ('-50 mm', 'rear_y + 5 mm', ('top_deck_z - 10 mm',)), ('50 mm', 'rear_y + 5 mm', ('top_deck_z - 10 mm',))):
        for z in zs:
            br.append(B(c, 'frame bracket (printed)', x, y, z, '14 mm', '10 mm', '10 mm', 'PET Plastic', BLACK))
    for sx in (1, -1):
        for y in ('spine_y - ply_t - 5 mm', 'rear_y + 5 mm'):
            for z in ('plate_top + 100 mm', 'top_deck_z - 10 mm'):
                br.append(B(c, 'frame bracket (printed)', S(sx, 'cheek_x - 5 mm'), y, z, '10 mm', '10 mm', '10 mm', 'PET Plastic', BLACK))
    log('frame ok')


def main():
    define()
    frame()
    done()
