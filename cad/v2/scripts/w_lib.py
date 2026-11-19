# w_lib.py: geometry helpers for the v2 wiring harness. Pure stdlib (no Fusion), so the same code runs
# offline on the VPS (lengths, schedule, docs) and inside Fusion (bodies). All lengths in mm, robot frame:
# +X right, +Y front, +Z up.
#
# A cable is described by waypoints. Round cables (single wires, bundles) get every corner replaced by an
# arc of at least its minimum bend radius (smaller only where the waypoints leave no room; the arc radius
# actually used is reported). Flat cables (FFC, ribbon) carry a width vector per waypoint: a corner whose
# bend axis is the width vector becomes an arc (the easy bend); any other corner is a crease fold.
# Twists between waypoints are spread along the segment.
import math


def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a): return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 0.0, 0.0)


def perp(v, t):
    """v made perpendicular to unit t, normalised."""
    return unit(sub(v, mul(t, dot(v, t))))


def rot(v, axis, ang):
    """Rodrigues rotation of v about unit axis by ang (rad)."""
    c, s = math.cos(ang), math.sin(ang)
    return add(add(mul(v, c), mul(cross(axis, v), s)), mul(axis, dot(axis, v) * (1 - c)))


def plen(pts):
    return sum(norm(sub(pts[i + 1], pts[i])) for i in range(len(pts) - 1))


def smooth(pts, R, step=6.0):
    """Polyline -> dense polyline with an arc at every corner. Returns (points, radii used)."""
    pts = [tuple(map(float, p)) for p in pts]
    clean = [pts[0]]
    for p in pts[1:]:
        if norm(sub(p, clean[-1])) > 1e-6:
            clean.append(p)
    pts = clean
    if len(pts) < 3:
        return pts, []
    out, radii = [pts[0]], []
    used = 0.0                                   # part of the incoming leg already taken by the previous corner's arc
    for i in range(1, len(pts) - 1):
        a, p, b = pts[i - 1], pts[i], pts[i + 1]
        din, dout = unit(sub(p, a)), unit(sub(b, p))
        th = math.acos(max(-1.0, min(1.0, dot(din, dout))))
        if th < 1e-3:
            out.append(p)
            used = 0.0
            continue
        lin, lout = norm(sub(p, a)), norm(sub(b, p))
        nxt_corner = i + 1 < len(pts) - 1
        t = min(R * math.tan(th / 2), max(lin - used, 0.0) * 0.999, lout * (0.5 if nxt_corner else 0.999))
        used = t
        r = t / math.tan(th / 2)
        radii.append(round(r, 2))
        A = sub(p, mul(din, t))
        n = perp(dout, din)
        C = add(A, mul(n, r))
        m = max(2, int(math.ceil(math.degrees(th) / step)))
        for k in range(m + 1):
            ph = th * k / m
            out.append(add(C, add(mul(n, -r * math.cos(ph)), mul(din, r * math.sin(ph)))))
    out.append(pts[-1])
    return out, radii


def transport(pts, side0):
    """Parallel-transport a side vector along a dense polyline (one per point)."""
    sides = []
    s = side0
    for i in range(len(pts)):
        if i < len(pts) - 1:
            t = unit(sub(pts[i + 1], pts[i]))
        else:
            t = unit(sub(pts[i], pts[i - 1]))
        if i > 0:
            t = unit(add(t, unit(sub(pts[i], pts[i - 1])))) if i < len(pts) - 1 else t
        s = perp(s, t)
        sides.append(s)
    return sides


def offset(pts, side0, d):
    sides = transport(pts, side0)
    return [add(p, mul(s, d)) for p, s in zip(pts, sides)]


def flat_path(wps, R, step=8.0, twist_step=6.0):
    """wps: list of (point, width_vector). Returns dense list of (point, width_vector), radii, folds."""
    out, radii, folds = [], [], 0
    n = len(wps)
    P = [tuple(map(float, w[0])) for w in wps]
    W = [unit(w[1]) for w in wps]
    # decide corner type
    corner = [None] * n
    for i in range(1, n - 1):
        din, dout = unit(sub(P[i], P[i - 1])), unit(sub(P[i + 1], P[i]))
        ax = cross(din, dout)
        if norm(ax) < 1e-4:
            corner[i] = 'straight'
        elif abs(dot(unit(ax), perp(W[i], din))) > 0.97:
            corner[i] = 'bend'
        else:
            corner[i] = 'fold'
            folds += 1
    # arc trims
    trim_in, trim_out, arcs = [0.0] * n, [0.0] * n, {}
    for i in range(1, n - 1):
        if corner[i] != 'bend':
            continue
        din, dout = unit(sub(P[i], P[i - 1])), unit(sub(P[i + 1], P[i]))
        th = math.acos(max(-1.0, min(1.0, dot(din, dout))))
        t = min(R * math.tan(th / 2), 0.45 * norm(sub(P[i], P[i - 1])), 0.45 * norm(sub(P[i + 1], P[i])))
        r = t / math.tan(th / 2)
        radii.append(round(r, 2))
        trim_in[i], trim_out[i] = t, t
        arcs[i] = (din, dout, th, t, r)
    for i in range(n - 1):
        a, b = P[i], P[i + 1]
        d = unit(sub(b, a))
        s = add(a, mul(d, trim_out[i]))
        e = sub(b, mul(d, trim_in[i + 1]))
        w0 = perp(W[i], d)
        w1 = perp(W[i + 1] if corner[i + 1] != 'fold' else W[i + 1], d) if i + 1 < n else w0
        if corner[i + 1] == 'fold' if i + 1 < n - 1 else False:
            w1 = w0           # a fold changes direction at the corner, not along the segment
        if corner[i] == 'fold':
            w0 = perp(W[i], d)
        ang = math.atan2(dot(cross(w0, w1), d), dot(w0, w1))
        L = norm(sub(e, s))
        m = max(1, int(math.ceil(abs(math.degrees(ang)) / twist_step))) if abs(ang) > 1e-3 else 1
        for k in range(m + 1):
            if k == 0 and out:
                continue
            f = k / m
            out.append((add(s, mul(d, L * f)), rot(w0, d, ang * f)))
        if i + 1 in arcs:
            din, dout, th, t, r = arcs[i + 1]
            A = e
            nn = perp(dout, din)
            C = add(A, mul(nn, r))
            mm = max(2, int(math.ceil(math.degrees(th) / step)))
            wv = perp(W[i + 1], din)
            for k in range(1, mm + 1):
                ph = th * k / mm
                out.append((add(C, add(mul(nn, -r * math.cos(ph)), mul(din, r * math.sin(ph)))), wv))
    return out, radii, folds


def resample(pts, step=2.0):
    """Uniform resampling of a polyline (keeps both ends)."""
    out = [pts[0]]
    acc = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = norm(sub(b, a))
        if L < 1e-9:
            continue
        d = unit(sub(b, a))
        pos = step - acc
        while pos < L - 1e-6:
            out.append(add(a, mul(d, pos)))
            pos += step
        acc = L - (pos - step)
    if norm(sub(out[-1], pts[-1])) < step * 0.4 and len(out) > 1:
        out[-1] = pts[-1]
    else:
        out.append(pts[-1])
    return out
