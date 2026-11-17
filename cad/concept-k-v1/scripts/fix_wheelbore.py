# One-off: shaft bore through existing wheel hubs (s1 now does this on rebuild).
def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def main():
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        w = find_occ('Wheel mecanum 80 %s' % tag, find_occ('Drive %s' % tag).component).component
        bs = [w.bRepBodies.itemByName(n) for n in ('hub', 'side plate in', 'side plate out')]
        cyl(w, 'shaft bore', 'x', {'x': S(sx, 'wheel_xc'), 'y': S(sy, 'wheel_y'), 'z': 'axle_z'}, '6 mm', 'wheel_w + 2 mm', op=CUT, bodies=bs)
    log('bores ok')
    done()
