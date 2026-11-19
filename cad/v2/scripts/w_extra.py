# w_extra.py: keep-out and airflow checks for the module layout + harness (read-only; run through the loader with a
# 'shot-' tag so nothing is saved). Uploads checks-keepout-airflow.json.
#  1. battery removal: the sled, pack, sled-side connectors and the sled leads (S01-S09) slide out of the back in
#     steps; any new intersection with a fixed body (parts or other wiring) vs the rest pose is reported
#  2. airflow: free cross-section of the front channel (spine front face to the front wall) at the intake band and
#     at the Pi/HAT heatsink band, and any wiring in front of the AI HAT+ 2 heatsink face
import json, time


def _bb(b):
    bb = b.boundingBox
    return [v * 10 for v in bb.minPoint.asArray()], [v * 10 for v in bb.maxPoint.asArray()]


def _ov(a, b):
    return all(a[0][i] <= b[1][i] and a[1][i] >= b[0][i] for i in range(3))


def _ivol(t1, b2):
    try:
        a, c = TB.copy(t1), TB.copy(b2)
        TB.booleanOperation(a, c, adsk.fusion.BooleanTypes.IntersectionBooleanType)
        return a.volume * 1000.0 if a.faces.count else 0.0
    except Exception:
        return -1.0


def _moving(occ, b):
    top = occ.fullPathName.split('+')[0]
    if 'rail' in b.name or 'bulkhead' in b.name.lower():
        return False                     # guide rails and the XT60 bulkhead stay on the plate
    if top.startswith(('Battery sled', 'Battery 3S4P')):
        return True
    if top.startswith('Power connectors') and ('male on sled' in b.name or 'DC jack' in b.name):
        return True
    if occ.component.name == 'Wiring harness' and b.name.startswith('S0'):
        return True
    return 'door' in b.name.lower()


def main():
    t0 = time.time()
    mov, fix = [], []
    for occ in root.allOccurrences:
        if any(seg.startswith(('Face graphic', 'Main board keep-outs')) for seg in occ.fullPathName.split('+')):
            continue
        for b in occ.bRepBodies:
            if b.isSolid:
                (mov if _moving(occ, b) else fix).append((occ.fullPathName.split('+')[0].split(':')[0] + ' / ' + b.name, b, _bb(b)))
    steps = [0, 10, 25, 40, 55, 70, 85, 100, 115, 130, 145, 160]
    base, res = None, []
    for s in steps:
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, -s / 10.0, 0)
        hits = {}
        for mn, mb, (lo, hi) in mov:
            t = TB.copy(mb)
            TB.transform(t, m)
            blo, bhi = [lo[0], lo[1] - s, lo[2]], [hi[0], hi[1] - s, hi[2]]
            for fn, fb, fbb in fix:
                if not _ov((blo, bhi), fbb):
                    continue
                v = _ivol(t, fb)
                if v > 0.5 or v < 0:
                    hits[(mn, fn)] = round(v, 1)
        if base is None:
            base = set(hits)
        new = [{'moving': k[0], 'fixed': k[1], 'mm3': v} for k, v in hits.items() if k not in base]
        res.append({'slide_mm': s, 'new_hits': new})
    # airflow
    sections = {}
    x0, x1, y0, y1 = -(mm('shell_x') - mm('pwall')), mm('shell_x') - mm('pwall'), mm('spine_y'), mm('shell_y') - mm('pwall')
    for z in (90.0, 100.0, 160.0, 175.0, 230.0):
        obb = adsk.core.OrientedBoundingBox3D.create(P((x0 + x1) / 2, (y0 + y1) / 2, z), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
                                                     (x1 - x0) / 10.0, (y1 - y0) / 10.0, 0.1)
        slab = TB.createBox(obb)
        occ_area, who = 0.0, []
        for fn, fb, fbb in fix + mov:
            if fn.startswith('Shell'):
                continue
            if not _ov(fbb, ([x0, y0, z - 0.5], [x1, y1, z + 0.5])):
                continue
            v = _ivol(slab, fb)
            if v > 0.05:
                occ_area += v
                who.append(fn)
        tot = (x1 - x0) * (y1 - y0)
        sections['z%d' % z] = {'channel_mm2': round(tot), 'blocked_mm2': round(occ_area), 'free_pct': round(100 * (1 - occ_area / tot), 1), 'bodies': len(who)}
    hs = [b for n, b, _ in fix if 'HAT heatsink' in n]
    face = []
    if hs:
        lo, hi = _bb(hs[0])
        box = ([lo[0], hi[1], lo[2]], [hi[0], y1, hi[2]])
        for fn, fb, fbb in fix:
            if fn.startswith('Wiring harness') and _ov(fbb, box):
                face.append(fn)
    R = {'battery_slide_out': res, 'airflow_sections': sections, 'wiring_in_front_of_hat_heatsink': face, 'seconds': round(time.time() - t0)}
    put('checks-keepout-airflow.json', json.dumps(R, indent=1))
    log('keep-out/airflow: new sled hits at any step %d; wiring in front of the heatsink %d (%ds)'
        % (sum(len(r['new_hits']) for r in res), len(face), R['seconds']))
    done()
