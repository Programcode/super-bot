# w_check.py: wiring checks (run through the loader, e.g. fmcp.py job shot-wchk "[('w_check.py', 'main()')]").
#   1. every wire / housing / tie body vs every solid part it could touch (B-rep intersection volume)
#   2. wire vs wire between different cables (pieces of the same cable may touch at their joints)
#   3. wiring bodies in the lidar scan band (scan_z +- 3 mm), with their distance from the pan axis
# Uploads checks-wiring.json. Bodies of one cable share the id before ' | ' (a/b/c/d/e suffixes = same cable).
import json, time, re


def _cid(name):
    return re.sub(r'[a-e]$', '', name.split(' | ')[0])


def _bb(b):
    bb = b.boundingBox
    return [v * 10 for v in bb.minPoint.asArray()], [v * 10 for v in bb.maxPoint.asArray()]


def _ov(a, b, pad=0.0):
    return all(a[0][i] - pad <= b[1][i] and a[1][i] + pad >= b[0][i] for i in range(3))


def _vol(b1, b2):
    """Intersection volume in mm3; -1 when the kernel can't measure it (then the pair is listed as 'unmeasured')."""
    try:
        t1, t2 = TB.copy(b1), TB.copy(b2)
        TB.booleanOperation(t1, t2, adsk.fusion.BooleanTypes.IntersectionBooleanType)
        return t1.volume * 1000.0 if t1.faces.count else 0.0
    except Exception:
        return -1.0


def main(tag='wiring'):
    t0 = time.time()
    wires, parts = [], []
    for occ in root.allOccurrences:
        path = occ.fullPathName
        if not occ.isVisible and 'keep-outs' not in path:
            pass
        for b in occ.bRepBodies:
            if not b.isSolid:
                continue
            if occ.component.name.startswith('Wiring harness'):
                wires.append((path, b, _bb(b)))
            elif not any(seg.startswith(('Face graphic', 'Main board keep-outs')) for seg in path.split('+')):
                parts.append((path, b, _bb(b)))
    hits, ww = [], []
    for wp, w, wb in wires:
        for pp, p, pb in parts:
            if _ov(wb, pb):
                v = _vol(w, p)
                if v > 0.05 or v < 0:
                    hits.append({'wire': w.name, 'part': pp.split('+')[0].split(':')[0] + ' / ' + p.name, 'mm3': round(v, 2)})
    for i in range(len(wires)):
        for j in range(i + 1, len(wires)):
            a, b = wires[i], wires[j]
            if _cid(a[1].name) == _cid(b[1].name) or not _ov(a[2], b[2]):
                continue
            v = _vol(a[1], b[1])
            if v > 0.05 or v < 0:
                ww.append({'a': a[1].name, 'b': b[1].name, 'mm3': round(v, 2)})
    sz, py = mm('scan_z'), mm('pan_y')
    band = []
    for wp, w, (lo, hi) in wires:
        if lo[2] <= sz + 3 and hi[2] >= sz - 3:
            cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
            band.append({'wire': w.name, 'max_r_from_pan_axis': round(max(abs(lo[0]), abs(hi[0]), abs(lo[1] - py), abs(hi[1] - py)), 1)})
    R = {'wires': len(wires), 'parts_checked': len(parts), 'wire_part_hits': sorted(hits, key=lambda d: -d['mm3']), 'wire_wire_hits': sorted(ww, key=lambda d: -d['mm3']),
         'scan_band': band, 'shaft_inner_r': (mm('shaft_od') - 2) / 2, 'seconds': round(time.time() - t0)}
    put_json('checks-%s.json' % tag, R) if 'put_json' in globals() else put('checks-%s.json' % tag, json.dumps(R, indent=1))
    log('wiring check: %d wire bodies, %d wire-part hits, %d wire-wire hits, %d in the scan band (%ds)' % (len(wires), len(hits), len(ww), len(band), R['seconds']))
    done()
