# checks.py: timeline health, mass + CoG, print-bed fit, interference (rest pose), and a
# pan/tilt sweep (interference of the moving head vs everything near it, head clearance to
# the lidar scan plane, what crosses the scan plane, ribbon length change). Each part uploads
# checks-<part>.json to the bridge. The sweep restores the rest pose before it returns.
import json, time

# Real masses (g) of bought parts: the leaf component's non-printed bodies share this mass by volume.
REAL = [
    ('Motor JGB37-520', 155, 'SRC vendor listings 150-158'),
    ('Wheel mecanum 100', 300, 'EST: 100 mm wheels weigh 200-400 g; Studica/Nexus 354-400'),
    ('Battery 3S4P', 602, '12 x 47 g cells + nickel/wrap 20 + BMS 10 + fuse holder 8'),
    ('Raspberry Pi 5', 71, 'Pi 5 46 g + Active Cooler ~25 g'),
    ('Raspberry Pi AI HAT', 45, 'EST'),
    ('ESP32-S3-DevKitC-1 A', 10, 'EST'),
    ('ESP32-S3-DevKitC-1 B', 0, 'empty cradle only'),
    ('BNO085', 2.5, 'SRC'),
    ('Cliff sensors', 5.2, 'SRC 4 x 1.3'),
    ('Lidar LDROBOT LD19', 47, 'SRC'),
    ('Raspberry Pi Camera Module 3', 4, 'EST'),
    ('TFT 1.3in', 7.6, 'SRC'),
    ('Servo MG90S', 13.4, 'SRC'),
    ('Pi 5 V 5.5 A buck', 7, 'SRC'),
    ('Servo 6 V buck', 3.3, 'SRC'),
    ('Power distribution board', 40, 'EST: perfboard, XT60, 4x XT30, INA226, bus bar'),
    ('Audio MAX98357A', 28.5, 'SRC amp 1.2 + speaker 27.3'),
    ('Motor driver board', 25, 'EST: perfboard, 4 carriers, headers, terminals'),
    ('Power connectors', 16, 'XT60 pair'),
    ('Charge port', 13, 'EST: jack 5 + fuse holder 8'),
    ('Circuit Playground Express', 8.9, 'SRC'),
    ('Mic INMP441', 1, 'EST'),
    ('Main power XT60 loop key', 26, 'EST: XT60 pair + 14 AWG loop'),
    ('Face graphic', 0, 'not a part'),
    ('Wiring harness', 0, 'counted separately'),
]
PRINT_FACTOR = 0.75     # printed non-shell parts: 4 perimeters + ~30 % infill vs solid
WIRING_G = 220          # harness estimate (16 AWG power runs, signal looms, ribbon), placed at z 160
BED = 256.0
SKIP = ('Face graphic',)
HARDWARE_SAME = ('Corner tie rods', 'L0 posts', 'Motor JGB37', 'Wheel mecanum', 'Battery 3S4P', 'Raspberry Pi', 'ESP32', 'BNO085',
                 'Cliff sensors', 'Lidar LDROBOT', 'Raspberry Pi Camera', 'TFT 1.3in', 'Servo MG90S', 'Pi 5 V', 'Servo 6 V', 'Power distribution',
                 'Audio', 'Motor driver board', 'Circuit Playground', 'Mic INMP441', 'Main power', 'Charge port', 'Power connectors')


def items():
    out = []
    for occ in root.allOccurrences:
        for b in occ.bRepBodies:
            if b.isSolid:
                out.append((occ, occ.component, b))
    return out


def is_printed(c, b):
    return 'printed' in (c.name + ' ' + b.name).lower() or (b.material and b.material.name == 'PET Plastic')


def is_shell(c, b):
    return c.name.startswith('Shell') or 'smoked' in b.name or 'head shell' in b.name


def masses(its):
    by = {}
    for occ, c, b in its:
        by.setdefault(occ.fullPathName, []).append((occ, c, b))
    tot, mom, rows = 0.0, [0.0, 0.0, 0.0], []
    groups = {}
    for path, lst in by.items():
        c = lst[0][1]
        real = None
        for pre, g, src in REAL:
            if c.name.startswith(pre):
                real = g
        rest = [b for _, _, b in lst if not is_printed(c, b)]
        rv = sum(b.volume for b in rest) or 1.0
        gsum, m = 0.0, [0.0, 0.0, 0.0]
        for occ, cc, b in lst:
            pp = b.physicalProperties
            if real is not None and b in rest:
                g = real * b.volume / rv
            elif is_printed(cc, b) and not is_shell(cc, b):
                g = pp.mass * 1000.0 * PRINT_FACTOR
            else:
                g = pp.mass * 1000.0
            com = pp.centerOfMass
            for i, v in enumerate((com.x, com.y, com.z)):
                m[i] += g * v * 10.0
            gsum += g
        top = path.split('+')[0]
        grp = groups.setdefault(top, [0.0, [0.0, 0.0, 0.0]])
        grp[0] += gsum
        for i in range(3):
            grp[1][i] += m[i]
            mom[i] += m[i]
        tot += gsum
    tot += WIRING_G
    mom[2] += WIRING_G * 160.0
    rows = sorted([(k, round(v[0], 1), [round(x / v[0], 1) for x in v[1]] if v[0] else None) for k, v in groups.items()], key=lambda r: -r[1])
    return tot, [x / tot for x in mom], rows


def bedfit(its):
    rows = []
    for occ, c, b in its:
        if not is_printed(c, b):
            continue
        bb = b.boundingBox
        d = sorted([(bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10, (bb.maxPoint.z - bb.minPoint.z) * 10])
        rows.append({'part': occ.fullPathName + ' / ' + b.name, 'dims': [round(v, 1) for v in d], 'fits': all(v <= BED for v in d)})
    return rows


def interference(bodies):
    col = OC.create()
    for b in bodies:
        col.add(b)
    inp = design.createInterferenceInput(col)
    inp.areCoincidentFacesIncluded = False
    res = design.analyzeInterference(inp)
    out = []
    for r in res:
        e1, e2 = r.entityOne, r.entityTwo
        o1 = e1.assemblyContext.fullPathName if e1.assemblyContext else e1.parentComponent.name
        o2 = e2.assemblyContext.fullPathName if e2.assemblyContext else e2.parentComponent.name
        if o1 == o2 and any(o1.split('+')[-1].startswith(h) or o1.startswith(h) for h in HARDWARE_SAME):
            continue
        out.append({'a': o1 + ' / ' + e1.name, 'b': o2 + ' / ' + e2.name, 'mm3': round(r.interferenceBody.volume * 1000.0, 2)})
    return sorted(out, key=lambda d: -d['mm3'])


def health():
    return [design.timeline.item(i).name for i in range(design.timeline.count)
            if design.timeline.item(i).healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]


def put_json(name, obj):
    put(name, json.dumps(obj, indent=1))


def occ_by_name(name, parent=None):
    for o in (parent.childOccurrences if parent else root.occurrences):
        if o.component.name == name:
            return o
    return None


def rot(axis, ang, px, py, pz):
    m = adsk.core.Matrix3D.create()
    v = {'x': (1, 0, 0), 'z': (0, 0, 1)}[axis]
    m.setToRotation(math.radians(ang), adsk.core.Vector3D.create(*v), P(px, py, pz))
    return m


def sweep():
    pan = occ_by_name('Head pan rotor')
    tilt = occ_by_name('Head tilt rotor', pan)
    py, tz, sz = mm('pan_y'), mm('tilt_z'), mm('scan_z')
    near_prefix = ('Head joint fixed', 'Shell', 'Lidar', 'Top deck')
    fixed_bodies = []
    for occ, c, b in items():
        top = occ.fullPathName.split('+')[0]
        if top.startswith(near_prefix):
            fixed_bodies.append(b)
    res = []
    i0 = pan.transform2
    for pa in (-90, -45, 0, 45, 90):
        for ta in (-35, 0, 45):
            pan.transform2 = rot('z', pa, 0, py, 0)
            tilt.transform2 = rot('x', ta, 0, py, tz)
            adsk.doEvents()
            mov = [b for b in pan.bRepBodies] + [b for o in pan.childOccurrences for b in o.bRepBodies] + \
                  [b for o in tilt.childOccurrences for b in o.bRepBodies] + [b for b in tilt.bRepBodies]
            mov = [b for b in mov if b.isSolid]
            # lowest point of the tilt rotor (head + fork) and of the pan rotor above the deck
            hz = min(b.boundingBox.minPoint.z for b in tilt.bRepBodies) * 10
            col = OC.create()
            for b in mov + fixed_bodies:
                col.add(b)
            inp = design.createInterferenceInput(col)
            inp.areCoincidentFacesIncluded = False
            hits = []
            movset = set(b.entityToken for b in mov)
            for r in design.analyzeInterference(inp):
                a, b = r.entityOne, r.entityTwo
                if (a.entityToken in movset) == (b.entityToken in movset):
                    continue  # only moving-vs-fixed pairs
                hits.append([a.name, b.name, round(r.interferenceBody.volume * 1000, 2)])
            res.append({'pan': pa, 'tilt': ta, 'head_min_z': round(hz, 1), 'head_above_scan': round(hz - sz, 1), 'hits': hits})
    pan.transform2 = adsk.core.Matrix3D.create()
    tilt.transform2 = adsk.core.Matrix3D.create()
    adsk.doEvents()
    return res


def scan_plane():
    """Bodies crossing the lidar beam (scan_z +- 3 mm) and the bearing sector each blocks."""
    lx, ly, sz = 0.0, mm('lidar_y'), mm('scan_z')
    out = []
    for occ, c, b in items():
        top = occ.fullPathName.split('+')[0]
        if top.startswith('Lidar'):
            continue
        bb = b.boundingBox
        if bb.minPoint.z * 10 > sz + 3 or bb.maxPoint.z * 10 < sz - 3:
            continue
        angs = []
        for x in (bb.minPoint.x, bb.maxPoint.x):
            for y in (bb.minPoint.y, bb.maxPoint.y):
                angs.append(math.degrees(math.atan2(x * 10 - lx, y * 10 - ly)))
        dist = math.hypot((bb.minPoint.x + bb.maxPoint.x) * 5 - lx, (bb.minPoint.y + bb.maxPoint.y) * 5 - ly)
        out.append({'body': top + ' / ' + b.name, 'bearing_deg_from_front': [round(min(angs), 1), round(max(angs), 1)],
                    'width_deg': round(max(angs) - min(angs), 1), 'dist_mm': round(dist, 1)})
    return out


def main(parts=('mass', 'bed', 'interf', 'sweep')):
    its = [(o, c, b) for (o, c, b) in items() if not o.fullPathName.split('+')[0].startswith(SKIP)]
    R = {'bodies': len(its), 'timeline': design.timeline.count, 'unhealthy': health(),
         'params': [{'name': p.name, 'expr': p.expression, 'mm': round(p.value * 10, 2), 'comment': p.comment} for p in design.userParameters]}
    if 'mass' in parts:
        tot, cog, rows = masses(its)
        R.update(mass_g=round(tot, 1), cog_mm=[round(v, 1) for v in cog], mass_rows=rows)
    if 'bed' in parts:
        R['bed'] = bedfit(its)
    if 'scan' in parts or 'sweep' in parts:
        R['scan_plane'] = scan_plane()
    put_json('checks-a.json', R)
    if 'sweep' in parts:
        R['sweep'] = sweep()
        put_json('checks-sweep.json', R['sweep'])
    if 'interf' in parts:
        t0 = time.time()
        R['interference'] = interference([b for o, _, b in its if not o.fullPathName.startswith('Wiring harness')])
        R['interf_s'] = round(time.time() - t0)
        put_json('checks-interf.json', R['interference'])
    log('checks done', len(its))
    done()
