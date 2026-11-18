"""Stage 2 of the board: zones (planes + power pours), Freerouting for the rest, zone fill.

Usage (from hw/main-board): ~/tools/kicad-mcp-server/.venv/bin/python gen/route.py [passes]
"""
import os
import re
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser('~/tools/kicad-mcp-server/python'))
from pcblib import BOARD_DIR, MM   # noqa: E402
from build_pcb import X0, Y0, W, H, NOTCH, ANT_KEEPOUT   # noqa: E402
from utils.project_netclasses import load_project_net_classes, apply_net_classes_to_board   # noqa: E402

PCB = os.path.join(BOARD_DIR, 'main-board.kicad_pcb')
PRO = os.path.join(BOARD_DIR, 'main-board.kicad_pro')
JAVA = '/usr/lib/jvm/java-25-openjdk-amd64/bin/java'
JAR = os.path.expanduser('~/.kicad-mcp/freerouting.jar')
WORK = '/tmp/sbpcb/route'


def P(x, y):
    return pcbnew.VECTOR2I(int(MM(X0 + x)), int(MM(Y0 + y)))


def board_poly():
    nx0, nx1, ny0, ny1 = NOTCH
    return [(0, 0), (nx0, 0), (nx0, ny1), (nx1, ny1), (nx1, 0), (W, 0), (W, H), (0, H)]


def add_zone(board, net, layer, pts, prio=0, clearance=0.25, full=False, minw=0.2, name=''):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if net:
        z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(clearance))
    z.SetMinThickness(MM(minw))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(int(MM(X0 + x)), int(MM(Y0 + y)))
    board.Add(z)
    return z


def add_keepout(board, rect, name):
    x0, y0, x1, y1 = rect
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(int(MM(X0 + x)), int(MM(Y0 + y)))
    board.Add(z)


def pads_of(board, net):
    out = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == net:
                pos = p.GetPosition()
                out.append((pos.x / 1e6 - X0, pos.y / 1e6 - Y0, p))
    return out


def hull_rect(board, net, margin, refs=None):
    pts = [(x, y) for x, y, p in pads_of(board, net) if refs is None or p.GetParentFootprint().GetReference() in refs]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)


def rect(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def zones(board):
    for z in list(board.Zones()):
        board.Remove(z)
    add_keepout(board, ANT_KEEPOUT, 'WROOM antenna keepout')
    bp = board_poly()
    # In1: solid GND reference plane
    add_zone(board, 'GND', pcbnew.In1_Cu, bp, prio=0, clearance=0.25, name='GND plane')
    # In2: split power plane
    add_zone(board, '+3V3', pcbnew.In2_Cu, rect((44.5, 0.5, 147.5, 34.5)), prio=1, name='3V3 plane')
    add_zone(board, 'VMOT', pcbnew.In2_Cu, rect((44.5, 39.5, 147.5, 69.5)), prio=1, name='VMOT plane')
    add_zone(board, 'VBUS', pcbnew.In2_Cu,
             [(0.5, 0.5), (43.5, 0.5), (43.5, 35.5), (147.5, 35.5), (147.5, 38.5), (43.5, 38.5), (43.5, 69.5), (0.5, 69.5)],
             prio=1, name='VBUS plane')
    add_zone(board, '+5V', pcbnew.In2_Cu,
             [(148.5, 8.5), (172.5, 8.5), (172.5, 0.5), (185.5, 0.5), (185.5, 35.0), (167.0, 35.0), (167.0, 69.5), (148.5, 69.5)],
             prio=1, name='5V plane')
    add_zone(board, 'VSERVO', pcbnew.In2_Cu, rect((167.8, 35.8, 185.5, 69.5)), prio=1, name='servo plane')
    # outer-layer power pours for the 15 A input chain, VBUS and VMOT (F.Cu and B.Cu, solid pad connection).
    # Polygons follow the placement in build_pcb.py; each pair of layers carries the current in parallel.
    def pad_box(ref, num, m):
        fp = board.FindFootprintByReference(ref)
        bbs = [p.GetBoundingBox() for p in fp.Pads() if p.GetNumber() == num]
        return (min(b.GetLeft() for b in bbs) / 1e6 - X0 - m, min(b.GetTop() for b in bbs) / 1e6 - Y0 - m,
                max(b.GetRight() for b in bbs) / 1e6 - X0 + m, max(b.GetBottom() for b in bbs) / 1e6 - Y0 + m)

    def union(*bs):
        return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    f2 = pad_box('F101', '2', 0.6)
    j2 = pad_box('J102', '2', 0.9)
    pours = {
        '/Power/VBAT_IN': [rect(union(pad_box('J101', '2', 1.2), pad_box('F101', '1', 0.8)))],
        '/Power/VBAT_F': [[(j2[0], j2[1]), (f2[2], j2[1]), (f2[2], f2[3]), (f2[0], f2[3]), (f2[0], j2[3]), (j2[0], j2[3])]],
        '/Power/VSW': [rect(union(pad_box('J102', '1', 1.2), pad_box('Q101', '2', 0.6)))],
        '/Power/VPROT': [rect(union(pad_box('Q101', '3', 0.6), pad_box('R102', '1', 0.6), pad_box('D102', '1', 0.6)))],
        'VBUS': [[(35.8, 0.8), (43.6, 0.8), (43.6, 44.6), (49.6, 44.6), (49.6, 48.6), (32.0, 48.6), (32.0, 43.4), (35.8, 43.4)]],
        'VMOT': [[(50.8, 38.0), (63.6, 38.0), (63.6, 69.4), (44.4, 69.4), (44.4, 52.0), (50.8, 52.0)]],
    }
    for net, polys in pours.items():
        for poly in polys:
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                add_zone(board, net, layer, poly, prio=6 if net.endswith('VBAT_IN') else 5, clearance=0.3, full=True,
                         name=net + ' pour')
    # buck output pours (+5V, VSERVO) and switch nodes stay on F.Cu, routed; GND fill everywhere else
    add_zone(board, 'GND', pcbnew.F_Cu, bp, prio=0, clearance=0.25, name='GND top')
    add_zone(board, 'GND', pcbnew.B_Cu, bp, prio=0, clearance=0.25, name='GND bottom')


def track(board, net, pts, width, layer=pcbnew.F_Cu):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(int(a[0]), int(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(int(b[0]), int(b[1])))
        t.SetWidth(int(MM(width)))
        t.SetLayer(layer)
        t.SetNet(net)
        t.SetLocked(True)
        board.Add(t)


def pad(board, ref, num):
    fp = board.FindFootprintByReference(ref)
    return next(p for p in fp.Pads() if p.GetNumber() == num)


def manual_tracks(board):
    """Locked high-current tracks drawn before autorouting: motor outputs and buck switch nodes."""
    for t in list(board.GetTracks()):
        board.Remove(t)
    mm = MM(1)
    for n in (6, 7, 8, 9):
        u, j = 'U%d01' % n, 'J%d01' % n
        for upin, jpin, side in (('8', '1', -1), ('10', '6', 1)):
            p0 = pad(board, u, upin)
            pj = pad(board, j, jpin)
            a = p0.GetPosition()
            b = pj.GetPosition()
            # 0.4 mm neck out of the 0.65 mm-pitch pin, 0.6 mm diagonal clear of the VM via, then 1.0 mm to the connector
            p1 = (a.x + side * 1.1 * mm, a.y)
            p2 = (p1[0] + side * 1.0 * mm, p1[1] + 1.0 * mm)
            dx = abs(b.x - p2[0])
            p3 = (b.x, p2[1] + dx)
            track(board, p0.GetNet(), [(a.x, a.y), p1], 0.4)
            track(board, p0.GetNet(), [p1, p2], 0.6)
            track(board, p0.GetNet(), [p2, p3, (b.x, b.y)], 1.0)
    for u, l in (('U102', 'L101'), ('U103', 'L102')):
        sw = pad(board, u, '6')
        lp = pad(board, l, '1')
        a, b = sw.GetPosition(), lp.GetPosition()
        # 0.3 mm neck from the SW pad straight down into the inductor pad (pad top edge ~0.6 mm below the IC)
        track(board, sw.GetNet(), [(a.x, a.y), (a.x, b.y)], 0.3)
    # driver GND pins into the exposed pad, and a VM via right of pin 11 (VMOT plane)
    for n in (6, 7, 8, 9):
        u = 'U%d01' % n
        ep = pad(board, u, '17').GetPosition()
        for num in ('7', '9', '15'):
            pp = pad(board, u, num)
            a = pp.GetPosition()
            track(board, pp.GetNet(), [(a.x, a.y), (ep.x, a.y)], 0.3)
        vm = pad(board, u, '11')
        a = vm.GetPosition()
        vx, vy = a.x + int(2.6 * mm), a.y
        track(board, vm.GetNet(), [(a.x, a.y), (vx, vy)], 0.4)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(vx, vy))
        v.SetWidth(int(MM(0.8)))
        v.SetDrill(int(MM(0.4)))
        v.SetNet(vm.GetNet())
        v.SetLocked(True)
        board.Add(v)
    # thermal vias (0.3 mm drill, JLC standard) in the driver and amp exposed pads, tied to the GND planes
    gnd = board.FindNet('GND')
    for ref in ('U601', 'U701', 'U801', 'U901', 'U501'):
        ep = pad(board, ref, '17')
        c = ep.GetPosition()
        offs = [(dx, dy) for dx in (-0.6, 0.6) for dy in (-1.2, 0.0, 1.2)] if ref != 'U501' else [(0.0, 0.0)]
        fp = board.FindFootprintByReference(ref)
        rot = fp.GetOrientationDegrees()
        for dx, dy in offs:
            if rot in (90, 270, -90):
                dx, dy = dy, dx
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(int(c.x + dx * mm), int(c.y + dy * mm)))
            v.SetWidth(int(MM(0.6)))
            v.SetDrill(int(MM(0.3)))
            v.SetNet(gnd)
            v.SetLocked(True)
            board.Add(v)


PLANE_NETS = {'GND': 'In1', '+3V3': 'In2', 'VMOT': 'In2', 'VBUS': 'In2', '+5V': 'In2', 'VSERVO': 'In2'}


def fanout(board, clearance=0.2):
    """Via + stub from every SMD pad of a plane net that sits over its own plane (Freerouting fails at this)."""
    import math
    zones_by_net = {}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        if z.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            zones_by_net.setdefault(z.GetNetname(), []).append(z.Outline())
    keep = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            keep.append(z.Outline())
    obst = []   # (x0, y0, x1, y1, net) in nm
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            obst.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom(), p.GetNetname(), p))
    for t in board.GetTracks():
        bb = t.GetBoundingBox()
        obst.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom(), t.GetNetname(), t))
    GRID = MM(2)
    grid = {}

    def gadd(o):
        for gx in range(int(o[0] // GRID), int(o[2] // GRID) + 1):
            for gy in range(int(o[1] // GRID), int(o[3] // GRID) + 1):
                grid.setdefault((gx, gy), []).append(o)
    for o in obst:
        gadd(o)

    def hits(x0, y0, x1, y1, net):
        seen = set()
        for gx in range(int(x0 // GRID), int(x1 // GRID) + 1):
            for gy in range(int(y0 // GRID), int(y1 // GRID) + 1):
                for o in grid.get((gx, gy), []):
                    if id(o) in seen:
                        continue
                    seen.add(id(o))
                    if o[4] == net:
                        continue
                    if x1 > o[0] and x0 < o[2] and y1 > o[1] and y0 < o[3]:
                        return True
        return False
    c = MM(clearance)
    nx0, nx1, ny0, ny1 = NOTCH
    placed, failed = 0, []
    for fp in board.GetFootprints():
        fc = fp.GetPosition()
        for p in fp.Pads():
            net = p.GetNetname()
            if net not in PLANE_NETS or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if p.GetNumber() == '17' and fp.GetReference()[0] == 'U' and fp.GetReference()[1] in '56789':
                continue     # exposed pads already have thermal vias
            pc = p.GetPosition()
            polys = zones_by_net.get(net, [])
            if not any(pl.Contains(pcbnew.VECTOR2I(pc.x, pc.y)) for pl in polys):
                continue
            big = net in ('VMOT', 'VBUS', '+5V', 'VSERVO')
            vd, vdr = (MM(0.8), MM(0.4)) if big else (MM(0.6), MM(0.3))
            bb = p.GetBoundingBox()
            tw = min(MM(0.5) if big else MM(0.3), min(bb.GetWidth(), bb.GetHeight()))
            half = max(bb.GetWidth(), bb.GetHeight()) / 2
            ang0 = math.atan2(pc.y - fc.y, pc.x - fc.x) if (pc.x, pc.y) != (fc.x, fc.y) else 0
            ok = None
            for dist in (half + vd / 2 + c, half + vd / 2 + c + MM(0.4), half + vd / 2 + c + MM(0.9), half + vd + MM(1.4)):
                for k in range(16):
                    a = ang0 + (k // 2) * (math.pi / 8) * (1 if k % 2 == 0 else -1)
                    vx, vy = pc.x + dist * math.cos(a), pc.y + dist * math.sin(a)
                    bx, by = vx / 1e6 - X0, vy / 1e6 - Y0
                    if bx < 0.8 or by < 0.8 or bx > W - 0.8 or by > H - 0.8:
                        continue
                    if nx0 - 0.8 < bx < nx1 + 0.8 and by < ny1 + 0.8:
                        continue
                    if any(pl.Contains(pcbnew.VECTOR2I(int(vx), int(vy))) for pl in keep):
                        continue
                    if not any(pl.Contains(pcbnew.VECTOR2I(int(vx), int(vy))) for pl in polys):
                        continue
                    r = vd / 2 + c
                    if hits(vx - r, vy - r, vx + r, vy + r, net):
                        continue
                    # stub: sample along the segment outside the pad
                    bad = False
                    for t in [i / 20.0 for i in range(2, 21)]:
                        sx, sy = pc.x + (vx - pc.x) * t, pc.y + (vy - pc.y) * t
                        rr = tw / 2 + c
                        if hits(sx - rr, sy - rr, sx + rr, sy + rr, net) or \
                                any(pl.Contains(pcbnew.VECTOR2I(int(sx), int(sy))) for pl in keep):
                            bad = True
                            break
                    if bad:
                        continue
                    ok = (vx, vy)
                    break
                if ok:
                    break
            if not ok:
                failed.append('%s.%s' % (fp.GetReference(), p.GetNumber()))
                continue
            vx, vy = ok
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(int(vx), int(vy)))
            v.SetWidth(int(vd))
            v.SetDrill(int(vdr))
            v.SetNet(p.GetNet())
            v.SetLocked(True)
            board.Add(v)
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(pc.x, pc.y))
            t.SetEnd(pcbnew.VECTOR2I(int(vx), int(vy)))
            t.SetWidth(int(tw))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(p.GetNet())
            t.SetLocked(True)
            board.Add(t)
            for o in ((vx - vd / 2, vy - vd / 2, vx + vd / 2, vy + vd / 2, net, v),
                      (min(pc.x, vx) - tw / 2, min(pc.y, vy) - tw / 2, max(pc.x, vx) + tw / 2, max(pc.y, vy) + tw / 2, net, t)):
                gadd(o)
            placed += 1
    print('fanout: %d vias, %d pads without room: %s' % (placed, len(failed), ' '.join(failed)))


def stitch(board, pitch=2.4):
    """Via grid inside each outer-layer power pour, tying F.Cu, B.Cu and the In2 plane of the same net together."""
    import math
    obst = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            obst.append((p.GetBoundingBox(), p.GetNetname()))
    for t in board.GetTracks():
        obst.append((t.GetBoundingBox(), t.GetNetname()))
    n = 0
    for z in list(board.Zones()):
        if z.GetIsRuleArea() or z.GetLayer() != pcbnew.F_Cu or not z.GetZoneName().endswith(' pour'):
            continue
        net = z.GetNetname()
        ol = z.Outline()
        bb = ol.BBox()
        x = bb.GetLeft() + MM(1.0)
        while x < bb.GetRight() - MM(1.0):
            y = bb.GetTop() + MM(1.0)
            while y < bb.GetBottom() - MM(1.0):
                pt = pcbnew.VECTOR2I(int(x), int(y))
                inside = ol.Contains(pt)
                if inside:
                    # stay 1 mm inside the outline
                    inside = all(ol.Contains(pcbnew.VECTOR2I(int(x + dx), int(y + dy)))
                                 for dx, dy in ((MM(1), 0), (-MM(1), 0), (0, MM(1)), (0, -MM(1))))
                if inside:
                    r = MM(0.4 + 0.35)
                    clash = any(o[1] != net and o[0].GetLeft() < x + r and o[0].GetRight() > x - r and
                                o[0].GetTop() < y + r and o[0].GetBottom() > y - r for o in obst)
                    same = any(o[1] == net and o[0].GetLeft() < x + MM(0.5) and o[0].GetRight() > x - MM(0.5) and
                               o[0].GetTop() < y + MM(0.5) and o[0].GetBottom() > y - MM(0.5) for o in obst)
                    if not clash and not same:
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pt)
                        v.SetWidth(int(MM(0.8)))
                        v.SetDrill(int(MM(0.4)))
                        v.SetNet(z.GetNet())
                        v.SetLocked(True)
                        board.Add(v)
                        obst.append((v.GetBoundingBox(), net))
                        n += 1
                y += MM(pitch)
            x += MM(pitch)
    print('stitching vias:', n)


def run_freerouting(board, passes):
    os.makedirs(WORK, exist_ok=True)
    dsn, ses = os.path.join(WORK, 'mb.dsn'), os.path.join(WORK, 'mb.ses')
    for f in (dsn, ses):
        if os.path.exists(f):
            os.remove(f)
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    txt = open(dsn).read()
    # inner layers are planes only: no tracks there
    txt = re.sub(r'\(layer (In[12]\.Cu)\s*\(type signal\)', r'(layer \1 (type power)', txt)
    # the outer GND pours would make every pad look connected; keep only In1 as the GND plane
    pos = 0
    while True:
        i = txt.find('(plane GND (polygon ', pos)
        if i < 0:
            break
        layer = txt[i + len('(plane GND (polygon '):].split()[0]
        depth, j = 0, i
        while True:
            if txt[j] == '(':
                depth += 1
            elif txt[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if layer in ('F.Cu', 'B.Cu'):
            txt = txt[:i] + txt[j + 1:]
        else:
            pos = j
    open(dsn, 'w').write(txt)
    cmd = [JAVA, '-jar', JAR, '-de', dsn, '-do', ses, '--gui.enabled=false', '-mp', str(passes),
           '-mt', '4', '--router.optimizer.enabled=true']
    print(' '.join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3000)
    print(r.stdout[-3000:], r.stderr[-2000:])
    if not os.path.exists(ses):
        raise SystemExit('no SES produced')
    s = open(ses).read()
    i = s.find('(placement')
    if i >= 0:
        depth, j = 0, i
        while True:
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        s = s[:i] + s[j + 1:]
    open(ses, 'w').write(s)
    ok = pcbnew.ImportSpecctraSES(board, ses)
    print('SES import', ok)


def main():
    passes = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    cont = '--continue' in sys.argv      # keep the existing routing and let Freerouting finish it
    board = pcbnew.LoadBoard(PCB)
    apply_net_classes_to_board(board, load_project_net_classes(PRO))
    if not cont:
        zones(board)
        manual_tracks(board)
        fanout(board)
        stitch(board)
    if '--no-route' in sys.argv:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(PCB)
        return
    run_freerouting(board, passes)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(PCB)
    print('saved')


if __name__ == '__main__':
    main()
