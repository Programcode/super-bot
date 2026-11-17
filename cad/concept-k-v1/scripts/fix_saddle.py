# One-off: name the separate saddle bodies and cut their two plate holes.
def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def main():
    pc = find_occ('Chassis plate').component
    plate = pc.bRepBodies.itemByName('Chassis plate')
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        c = find_occ('Motor mount + well liner %s' % tag, find_occ('Drive %s' % tag).component).component
        for b in c.bRepBodies:
            if b.name != 'motor mount + well liner':
                b.name = 'motor saddle (printed)'
        for gy in (1, -1):
            cyl(pc, 'M3 saddle', 'z', {'x': S(sx, 'gb_face - gb_len - can_len/2'), 'y': '%s + %d*10 mm' % (S(sy, 'wheel_y'), gy), 'z': 'plate_z + plate_t/2'},
                '3.4 mm', 'plate_t + 2 mm', op=CUT, bodies=[plate])
    log('saddles ok')
    done()
