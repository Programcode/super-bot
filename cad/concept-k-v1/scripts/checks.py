# checks.py: interference, clearance, centre of gravity, print-bed fit. Uploads checks.json.
import json, time, urllib.request

# Real masses (g) for bought parts; the whole leaf component carries this mass,
# spread over its bodies by volume. Everything else uses Fusion material density.
REAL = [
    ('Motor JGB37-520', 158, 'SRC manuals.plus (M)'),
    ('Wheel mecanum 80', 105, 'SRC 95-120 g (M)'),
    ('Battery 3S4P', 605, '12 x 47 g cells + nickel/wrap + BMS (EST)'),
    ('Motor driver BTS7960', 66, 'SRC handsontec (M)'),
    ('Raspberry Pi 5', 71, 'Pi 5 46 g (M) + Active Cooler ~25 g (EST)'),
    ('Raspberry Pi AI HAT+ 2', 45, 'EST'),
    ('BNO085', 3, 'SRC 2.5 g'),
    ('HC-SR04', 9, 'SRC'),
    ('VL53L0X', 1.3, 'SRC'),
    ('Lidar LDROBOT LD19', 47, 'SRC'),
    ('Logitech C270', 75, 'SRC (with cable)'),
    ('TFT 1.3in', 7.6, 'SRC'),
    ('Servo MG90S', 13.4, 'SRC'),
    ('Power placeholders', 25, 'EST: buck ~10 g, switch 5 g, XT60 8 g'),
    ('Face graphic', 0, 'not a part'),
]
MIXED = [  # (component prefix, printed body names using Fusion mass, real mass of the rest)
    ('ESP32-S3-DevKitC-1', ('printed cradle',), 10),
    ('Circuit Playground Express', ('CPX mount (printed)',), 8.9),
]
WIRING_G = 150  # harness estimate, placed at z = 60 mm on the centre line
BED = 256.0
SKIP_INTERF = ('Face graphic',)
BOUGHT = ('Motor JGB37', 'Wheel mecanum', 'Battery 3S4P', 'Motor driver', 'Raspberry Pi', 'ESP32', 'BNO085', 'HC-SR04',
          'VL53L0X', 'Lidar LDROBOT', 'Logitech C270', 'TFT 1.3in', 'Servo MG90S', 'Power placeholders', 'Circuit Playground')


def leaf_bodies():
    out = []
    for occ in root.allOccurrences:
        c = occ.component
        if occ.childOccurrences.count and c.bRepBodies.count == 0:
            continue
        for b in occ.bRepBodies:
            if b.isVisible or True:
                out.append((occ, c, b))
    return out


def top_name(occ):
    o = occ
    while o.assemblyContext:
        o = o.assemblyContext
    return o.component.name


def masses(items):
    rows = []
    by_comp = {}
    for occ, c, b in items:
        by_comp.setdefault(occ.fullPathName, []).append((occ, c, b))
    tot = 0.0
    m = [0.0, 0.0, 0.0]
    comp_rows = []
    for path, lst in by_comp.items():
        c = lst[0][1]
        real = None
        for pre, g, src in REAL:
            if c.name.startswith(pre):
                real = g
        mixed = None
        for pre, printed, g in MIXED:
            if c.name.startswith(pre):
                mixed = (printed, g)
        vols = [b.volume for _, _, b in lst]
        cm_sum = [0.0, 0.0, 0.0]
        cm_mass = 0.0
        rest = [(b, b.volume) for _, _, b in lst if not (mixed and b.name in mixed[0])]
        rest_vol = sum(v for _, v in rest) or 1.0
        for occ, cc, b in lst:
            pp = b.physicalProperties
            com = pp.centerOfMass
            if real is not None:
                g = real * b.volume / (sum(vols) or 1.0)
            elif mixed and b.name not in mixed[0]:
                g = mixed[1] * b.volume / rest_vol
            else:
                g = pp.mass * 1000.0
            cm_mass += g
            for i, v in enumerate((com.x, com.y, com.z)):
                cm_sum[i] += g * v * 10.0
        if cm_mass > 0:
            comp_rows.append((path, round(cm_mass, 1), [round(v / cm_mass, 1) for v in cm_sum]))
        tot += cm_mass
        for i in range(3):
            m[i] += cm_sum[i]
    tot += WIRING_G
    m[2] += WIRING_G * 60.0
    cog = [v / tot for v in m]
    return tot, cog, sorted(comp_rows, key=lambda r: -r[1])


def bbgap(a, b):
    g = 0.0
    for i in range(3):
        lo = max(a.minPoint.asArray()[i], b.minPoint.asArray()[i])
        hi = min(a.maxPoint.asArray()[i], b.maxPoint.asArray()[i])
        if lo > hi:
            g = max(g, lo - hi)
    return g * 10.0


def interference(items):
    col = OC.create()
    for occ, c, b in items:
        if any(c.name.startswith(s) for s in SKIP_INTERF):
            continue
        col.add(b)
    inp = design.createInterferenceInput(col)
    inp.areCoincidentFacesIncluded = False
    res = design.analyzeInterference(inp)
    out = []
    for r in res:
        e1, e2 = r.entityOne, r.entityTwo
        o1 = e1.parentComponent.name
        o2 = e2.parentComponent.name
        if o1 == o2 and o1.startswith(BOUGHT):
            continue  # internal modelling of one bought part (rollers vs hub, chip on PCB)
        v = r.interferenceBody.volume * 1000.0  # mm3
        out.append({'a': o1 + ' / ' + e1.name, 'b': o2 + ' / ' + e2.name, 'mm3': round(v, 2)})
    return sorted(out, key=lambda d: -d['mm3'])


def clearances(items, limit=6.0):
    mm_ = app.measureManager
    comps = {}
    for occ, c, b in items:
        if any(c.name.startswith(s) for s in SKIP_INTERF):
            continue
        comps.setdefault(occ.fullPathName, []).append(b)
    keys = sorted(comps)
    bbs = {k: [(b, b.boundingBox) for b in comps[k]] for k in keys}
    out = {}
    t0 = time.time()
    for i, ka in enumerate(keys):
        for kb in keys[i + 1:]:
            if ka.split('+')[0] == kb.split('+')[0] and '+' in ka:
                pass
            best = None
            for ba, bba in bbs[ka]:
                for bb_, bbb in bbs[kb]:
                    if bbgap(bba, bbb) > limit:
                        continue
                    d = mm_.measureMinimumDistance(ba, bb_).value * 10.0
                    if best is None or d < best[0]:
                        best = (d, ba.name, bb_.name)
            if best is not None:
                out[ka + ' <> ' + kb] = [round(best[0], 2), best[1], best[2]]
        if time.time() - t0 > 900:
            out['_truncated'] = True
            break
    return out


def bedfit(items):
    rows = []
    for occ, c, b in items:
        nm = (c.name + ' ' + b.name).lower()
        mat = b.material.name if b.material else ''
        kind = None
        if 'printed' in nm or mat == 'PET Plastic':
            kind = 'print'
        elif mat in ('Acrylic', 'Birch'):
            kind = 'sheet'
        if not kind:
            continue
        bb = b.boundingBox
        d = sorted([(bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10, (bb.maxPoint.z - bb.minPoint.z) * 10])
        ok = all(v <= BED for v in d) if kind == 'print' else None
        rows.append({'part': occ.fullPathName + ' / ' + b.name, 'kind': kind, 'mat': mat, 'dims': [round(v, 1) for v in d], 'fits_256': ok})
    return rows


def params():
    return [{'name': p.name, 'expr': p.expression, 'mm': round(p.value * 10, 2), 'comment': p.comment} for p in design.userParameters]


def put(name, obj):
    data = json.dumps(obj, indent=1).encode()
    urllib.request.urlopen(urllib.request.Request('http://100.115.45.111:8765/' + name, data=data, method='PUT'), timeout=60).read()


def main(parts=('mass', 'bed', 'interf', 'clear')):
    items = leaf_bodies()
    R = {'bodies': len(items), 'timeline': design.timeline.count, 'params': params()}
    unhealthy = []
    for i in range(design.timeline.count):
        it = design.timeline.item(i)
        if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            unhealthy.append(it.name)
    R['unhealthy'] = unhealthy
    if 'mass' in parts:
        tot, cog, rows = masses(items)
        R['mass_g'] = round(tot, 1)
        R['cog_mm'] = [round(v, 1) for v in cog]
        R['mass_rows'] = rows
    if 'bed' in parts:
        R['bed'] = bedfit(items)
    put('checks_a.json', R)
    if 'interf' in parts:
        R['interference'] = interference(items)
        put('checks_b.json', R)
    if 'clear' in parts:
        R['clearance'] = clearances(items)
        put('checks_c.json', R)
    log('checks done', len(items))
    done()
