# Stage 8: the wiring harness, every real cable. Routes, wire sizes, housings and ties are data in
# w_routes.py (with w_lib.py), evaluated here against the live parameters and the board's KiCad data,
# so a board or layout change only needs this stage rerun. Bodies are built as temporary B-rep
# primitives (cylinders for round wires, thin boxes for FFC/ribbon, boxes for housings and ties),
# unioned to one body per wire, and stored in base features:
#   'Wiring harness'                              fixed wiring (top level, mass counted as WIRING_G)
#   'Head pan rotor' / 'Wiring harness (pan)'     rides with the pan
#   'Head tilt rotor' / 'Wiring harness (tilt)'   rides with the tilt
# Flex spans (inside the pan shaft, across the tilt joint) are built at the rest pose in the fixed part.
import json, time

GROUPS = {'fixed': None, 'pan': ('Head pan rotor',), 'tilt': ('Head pan rotor', 'Head tilt rotor')}


def live_params():
    return {p.name: p.value * 10.0 for p in design.userParameters if p.unit in ('mm', 'cm')}


def routes(only=None):
    g = globals()
    for f in ('w_lib.py', 'w_routes.py'):
        exec(urllib.request.urlopen(BRIDGE + f, timeout=30).read().decode(), g)
    parts = json.loads(urllib.request.urlopen(BRIDGE + 'main_board_parts.json', timeout=30).read().decode())
    return g['build'](live_params(), parts, only)


def _cyl(a, b, r, ext):
    d = unit(sub(b, a))
    a2, b2 = sub(a, mul(d, ext)), add(b, mul(d, ext))
    return TB.createCylinderOrCone(P(*a2), r / 10.0, P(*b2), r / 10.0)


def _box(c, u, v, size):
    w = cross(u, v)
    obb = adsk.core.OrientedBoundingBox3D.create(P(*c), adsk.core.Vector3D.create(*u), adsk.core.Vector3D.create(*v),
                                                 size[0] / 10.0, size[1] / 10.0, size[2] / 10.0)
    return TB.createBox(obb)


def body_of(it):
    U = adsk.fusion.BooleanTypes.UnionBooleanType
    parts = []
    if it['kind'] == 'round':
        r = it['d'] / 2.0
        pts = it['pts']
        for i in range(len(pts) - 1):
            if norm(sub(pts[i + 1], pts[i])) < 0.05:
                continue
            parts.append(_cyl(pts[i], pts[i + 1], r, 0.0))
        for i in range(1, len(pts) - 1):      # joint spheres (same radius) close the polyline joints smoothly
            parts.append(TB.createSphere(P(*pts[i]), r / 10.0))
    elif it['kind'] == 'flat':
        pts, wv = it['pts'], it['wv']
        vlast = None
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            L = norm(sub(b, a))
            if L < 0.05:
                continue
            u = unit(sub(b, a))
            v = perp(wv[i], u)
            if norm(v) < 0.5:
                v = vlast if vlast is not None and abs(dot(vlast, u)) < 0.9 else perp((0, 0, 1) if abs(u[2]) < 0.9 else (1, 0, 0), u)
            v = perp(v, u)
            vlast = v
            ext = 0.0 if i in (0, len(pts) - 2) else 0.25
            parts.append(_box(mul(add(a, b), 0.5), u, v, (L + 2 * ext, it['w'], it['t'])))
    else:
        parts.append(_box(it['c'], it['u'], perp(it['v'], it['u']), it['size']))
    body = parts[0]
    for t in parts[1:]:
        TB.booleanOperation(body, t, U)
    return body


def target_comp(group):
    if group == 'fixed':
        return fresh('Wiring harness')
    occ = None
    for name in GROUPS[group]:
        occ = find_occ(name, occ.component if occ else None)
    return fresh('Wiring harness (%s)' % group, occ.component)


def pipe(c, it):
    """Round wire: one pipe along a fitted spline through the resampled centreline (one smooth face)."""
    pts = resample(it['pts'], 2.0)
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.isComputeDeferred = True
    sk.name = ('%s | %s' % (it['cable'], it['name']))[:60]
    col = OC.create()
    for p in pts:
        col.add(P(*p))
    spl = sk.sketchCurves.sketchFittedSplines.add(col)
    sk.isComputeDeferred = False
    sk.isVisible = False
    pi = c.features.pipeFeatures.createInput(c.features.createPath(spl, False), NEWB)
    pi.sectionSize = V.createByReal(it['d'] / 10.0)
    f = c.features.pipeFeatures.add(pi)
    b = f.bodies.item(0)
    b.name = ('%s | %s' % (it['cable'], it['name']))[:120]
    finish(b, 'ABS Plastic', it['look'])
    return b


def main(only=None, tag='wiring'):
    t0 = time.time()
    for old in ('Wiring harness (paths)',):
        o = find_occ(old)
        if o:
            o.deleteMe()
    R = routes(only)
    by = {}
    for it in R['items']:
        by.setdefault(it['group'], []).append(it)
    stats = {'items': len(R['items']), 'failed': [], 'bodies': 0}
    for group in ('fixed', 'pan', 'tilt'):
        its = by.get(group, [])
        c = target_comp(group)
        if not its:
            continue
        tb, names, looks = [], [], []
        for it in its:
            if it['kind'] == 'round':
                try:
                    pipe(c, it)
                    stats['bodies'] += 1
                    continue
                except Exception as e:      # tight spline bend: fall back to cylinders + joint spheres (same centreline)
                    stats.setdefault('primitive_fallback', []).append([it['cable'], it['name'], str(e)[:60]])
            try:
                tb.append(body_of(it))
                names.append(('%s | %s' % (it['cable'], it['name']))[:120])
                looks.append(it['look'])
            except Exception as e:
                stats['failed'].append([it['cable'], it['name'], str(e)[:80]])
        if not tb:
            continue
        bf = c.features.baseFeatures.add()
        bf.name = 'wiring %s' % group
        bf.startEdit()
        for b, n in zip(tb, names):
            c.bRepBodies.add(b, bf).name = n
        bf.finishEdit()
        for b, lk in zip(list(bf.bodies), looks):
            finish(b, 'ABS Plastic', lk)
        stats['bodies'] += bf.bodies.count
    stats['seconds'] = round(time.time() - t0, 1)
    put('build-%s.json' % tag, json.dumps({'stats': stats, 'cables': R['cables']}, default=str))
    log('wiring', stats['bodies'], 'bodies', len(stats['failed']), 'failed', stats['seconds'], 's')
    done()
