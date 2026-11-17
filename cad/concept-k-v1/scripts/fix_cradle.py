# One-off repair for designs built before the s1 cradle fix: delete the failed
# 'can cradle' cuts and re-cut the cradle into the joined mount body.
def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def main():
    tl = design.timeline
    for i in range(tl.count - 1, -1, -1):
        it = tl.item(i)
        if it.name.startswith('can cradle') and it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            it.entity.deleteMe()
    for sx, sy, tag in ((1, 1, 'FR'), (-1, 1, 'FL'), (1, -1, 'RR'), (-1, -1, 'RL')):
        mo = find_occ('Motor mount + well liner %s' % tag, find_occ('Drive %s' % tag).component)
        c = mo.component
        b = c.bRepBodies.itemByName('motor saddle (printed)')
        cyl(c, 'can cradle', 'x', {'x': S(sx, 'gb_face - gb_len - can_len/2'), 'y': S(sy, 'wheel_y'), 'z': 'motor_z'}, 'can_d + 0.4 mm', '16 mm', op=CUT, bodies=[b])
        log(tag, 'cradle ok', c.bRepBodies.count)
    done()
