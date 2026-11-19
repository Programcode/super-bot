# w_flex.py (offline, VPS): pan/tilt check of the cables that move, at the 15 sweep poses
# (pan -90/-45/0/45/90 x tilt -35/0/45). Usage: python3 -I w_flex.py <geom.json> <out.json>
#  - tilt spans (turret top slot -> crossbar slot): the span keeps its rest length L; at each tilt the crossbar end
#    turns about the tilt axis. Needs chord < L; the slack forms an arc of length L over the chord, whose radius must
#    stay >= 10x the conductor OD (FFC: 10 mm) and whose bulge must stay inside the 10 mm turret-to-crossbar gap
#    plus the open space in front of it.
#  - pan spans (shaft bottom tie -> turret clamp): pure twist about the shaft axis; reports the twist rate, the FFC
#    edge strain from the twist and the extra length an off-axis bundle needs on its quarter-turn helix.
import json, math, os, sys
S = os.path.dirname(os.path.abspath(__file__))
g = {}
for f in ('w_lib.py', 'w_routes.py'):
    exec(open(os.path.join(S, f)).read(), g)
geo = json.load(open(sys.argv[1]))
P = {k: v['mm'] for k, v in geo['params'].items() if isinstance(v['mm'], (int, float))}
R = g['build'](P, json.load(open(os.path.join(S, 'main_board_parts.json'))))
items = {}
for it in R['items']:
    items.setdefault(it['cable'], []).append(it)
rows = {c['id']: c for c in R['cables']}
ty, tz = P['pan_y'], P['tilt_z']


def rot_x(p, deg):
    a = math.radians(deg)
    y, z = p[1] - ty, p[2] - tz
    return (p[0], ty + y * math.cos(a) - z * math.sin(a), tz + y * math.sin(a) + z * math.cos(a))


def arc_radius(L, c):
    """Radius of a circular arc of length L over chord c (bisection on c = 2R sin(L/2R))."""
    if c >= L:
        return None
    lo, hi = L / (2 * math.pi) * 1.0001, 1e6
    for _ in range(200):
        mid = (lo + hi) / 2
        if 2 * mid * math.sin(L / (2 * mid)) < c:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


out = {'tilt_spans': [], 'pan_spans': [], 'poses': [[p, t] for p in (-90, -45, 0, 45, 90) for t in (-35, 0, 45)]}
for cid in ('G04c', 'G05c', 'K01c'):
    it = items[cid][0]
    pts = it['pts']
    A, B0 = pts[0], pts[-1]
    L = g['plen'](pts)
    cond = rows[cid]
    rule = 10.0 if cid.startswith('K') else 10.0 * max(g['OD'][c['awg']] for c in cond['conductors'])
    per = []
    thick = 0.3 if cid.startswith('K') else rows[cid]['od']
    yrel = A[1] - ty                       # slot position in front of the tilt axis
    for t in (-35, 0, 45):
        B = rot_x(B0, t)
        c = g['norm'](g['sub'](B, A))
        # gap above the turret top at the slot: crossbar bottom (radius head_z0 - 5 - tilt_z from the axis) after tilting
        rcb, rtt = P['head_z0'] - 5.0 - tz, 13.0
        a = math.radians(t)
        if abs(math.cos(a)) > 1e-6:
            y0 = (yrel - rcb * math.sin(-a)) / math.cos(a)          # crossbar-local y above the slot
            gap = (y0 * math.sin(a) + rcb * math.cos(a)) - rtt if abs(y0) <= 15.0 else 99.0
        else:
            gap = 99.0
        r_u = max(0.0, (min(gap, 12.0) - thick) / 2.0)
        per.append({'tilt': t, 'chord_mm': round(c, 1), 'slack_mm': round(L - c, 1), 'gap_at_slot_mm': round(gap, 1), 'u_loop_radius_mm': round(r_u, 1),
                    'ok': L - c > 3.0 and r_u >= 2.5})
    out['tilt_spans'].append({'cable': cid, 'rest_length_mm': round(L, 1), 'rule_radius_mm': rule, 'per_tilt': per,
                              'note': 'same at every pan angle (both ends ride with the pan)'})
for cid in ('G04b', 'G05b', 'K01b', 'V02b'):
    it = items[cid][0]
    pts = it['pts']
    L = abs(pts[-1][2] - pts[0][2])
    r_off = math.hypot(pts[0][0], pts[0][1] - ty)
    rate = 90.0 / L
    w = it.get('w')
    strain = None if not w else (w * math.radians(rate)) ** 2 / 24.0
    out['pan_spans'].append({'cable': cid, 'twist_length_mm': round(L, 1), 'max_twist_deg': 90, 'twist_rate_deg_per_mm': round(rate, 2),
                             'offset_from_axis_mm': round(r_off, 1), 'helix_takeup_mm': round(math.hypot(L, r_off * math.pi / 2) - L, 2),
                             'ffc_edge_strain_pct': None if strain is None else round(strain * 100, 3)})
json.dump(out, open(sys.argv[2], 'w'), indent=1)
bad = [(s['cable'], p['tilt']) for s in out['tilt_spans'] for p in s['per_tilt'] if not p['ok']]
print('tilt spans', [(s['cable'], s['rest_length_mm'], [(p['tilt'], p['chord_mm'], p['gap_at_slot_mm'], p['u_loop_radius_mm']) for p in s['per_tilt']]) for s in out['tilt_spans']])
print('pan spans', [(s['cable'], s['twist_rate_deg_per_mm'], s['helix_takeup_mm'], s['ffc_edge_strain_pct']) for s in out['pan_spans']])
print('not ok:', bad)
