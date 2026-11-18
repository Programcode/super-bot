"""Stage 2a: targeted copper fixes on the routed board (run after route.py, before fixup.py).

- In2: +3V3 bridge at the right end of the VMOT band joins the encoder 3.3 V band to the main 3.3 V plane
  (the VBUS strip and its feed via move 3 mm left to make room).
- F.Cu VBUS pours tie each TPS56637 VIN to its nearest input capacitor and the VBUS feed via.
- F.Cu +5V pour at the Pi USB-C VBUS pins with four vias into the In2 5 V plane (the Pi's 5 A path).
- Hand ties for GND pins the fanout cannot reach (TPS56637 AGND to PGND, INA226 pin 7 to pin 1).
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pcblib import BOARD_DIR, MM, PROJECT   # noqa: E402
from build_pcb import X0, Y0   # noqa: E402


def add_zone(board, net, layer, pts, prio=0, clearance=0.25, full=False, name=''):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(int(MM(clearance)))
    z.SetMinThickness(int(MM(0.2)))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(int(MM(0.3)))
    z.SetThermalReliefSpokeWidth(int(MM(0.5)))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(int(MM(X0 + x)), int(MM(Y0 + y)))
    board.Add(z)


def rect(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


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
    return next(p for p in board.FindFootprintByReference(ref).Pads() if p.GetNumber() == num)

PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BOARD_DIR, PROJECT + '.kicad_pcb')


def P(x, y):
    return (int(MM(X0 + x)), int(MM(Y0 + y)))


def via(board, net, x, y, d=0.8, dr=0.4):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(*P(x, y)))
    v.SetWidth(int(MM(d)))
    v.SetDrill(int(MM(dr)))
    v.SetNet(board.FindNet(net))
    v.SetLocked(True)
    board.Add(v)


def bx(p):
    return p.GetPosition().x / 1e6 - X0, p.GetPosition().y / 1e6 - Y0


def main():
    board = pcbnew.LoadBoard(PCB)
    # ---- In2 rework: VBUS strip to x 143.5, VMOT band to x 144.0, +3V3 bridge x 144.5..147.5
    def reshape(name, pts):
        z = next(z for z in board.Zones() if z.GetZoneName() == name)
        ol = z.Outline()
        ol.RemoveAllContours()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(int(MM(X0 + x)), int(MM(Y0 + y)))
    reshape('VBUS plane', [(0.5, 0.5), (43.5, 0.5), (43.5, 35.5), (143.5, 35.5), (143.5, 38.5), (43.5, 38.5), (43.5, 69.5), (0.5, 69.5)])
    reshape('VMOT plane', [(44.5, 39.5), (144.0, 39.5), (144.0, 53.5), (64.5, 53.5), (64.5, 69.5), (44.5, 69.5)])
    add_zone(board, '+3V3', pcbnew.In2_Cu, rect((144.5, 34.0, 147.5, 55.0)), prio=2, name='3V3 bridge')
    # move the VBUS feed via from x 146.8 to 143.0 and extend the B.Cu feed
    vbus = board.FindNet('VBUS')
    for t in board.GetTracks():
        if t.GetNetname() == 'VBUS' and t.Type() == pcbnew.PCB_VIA_T:
            x, y = bx(t)
            if abs(x - 146.8) < 0.05 and abs(y - 37.0) < 0.05:
                t.SetPosition(pcbnew.VECTOR2I(*P(143.0, 37.0)))
    track(board, vbus, [P(143.0, 37.0), P(147.2, 37.0)], 1.5, pcbnew.B_Cu)
    # ---- buck VIN pours: VIN pad + feed via + the input capacitor on the VIN side
    for u, cap in (('U102', 'C104'), ('U103', 'C113')):
        vin = [p for p in board.FindFootprintByReference(u).Pads() if p.GetNumber() == '8']
        xs = [bx(p)[0] for p in vin]
        cp = [p for p in board.FindFootprintByReference(cap).Pads() if p.GetNetname() == 'VBUS'][0]
        cx, cy = bx(cp)
        x0, x1 = min(xs) - 0.25, max(cx + 0.9, max(xs) + 0.6)
        add_zone(board, 'VBUS', pcbnew.F_Cu, rect((x0, 36.3, x1, max(cy + 0.9, 43.6))), prio=7, clearance=0.2, full=True,
                 name='VBUS %s pour' % u)
    # ---- Pi USB-C +5V: pour over the VBUS pins + 4 vias to the In2 5 V plane
    j = board.FindFootprintByReference('J103')
    vp = [bx(p) for p in j.Pads() if p.GetNetname() == '+5V']
    xa, xb = min(p[0] for p in vp), max(p[0] for p in vp)
    ya = max(p[1] for p in vp)
    add_zone(board, '+5V', pcbnew.F_Cu, rect((xa - 0.6, ya - 0.6, xb + 0.6, ya + 3.2)), prio=7, clearance=0.2, full=True,
             name='5V USB-C pour')
    obst = [(p.GetBoundingBox(), p.GetNetname()) for f in board.GetFootprints() for p in f.Pads()]
    obst += [(t.GetBoundingBox(), t.GetNetname()) for t in board.GetTracks()]

    def clear(x, y, r):
        X, Y = MM(X0 + x), MM(Y0 + y)
        return not any(n != '+5V' and b.GetLeft() < X + r and b.GetRight() > X - r and b.GetTop() < Y + r and b.GetBottom() > Y - r
                       for b, n in obst)
    placed = 0
    for yy in (ya + 2.4, ya + 1.8, ya + 3.0):
        for k in range(13):
            x = xa - 0.3 + (xb - xa + 0.6) * k / 12.0
            if placed < 4 and clear(x, yy, MM(0.3 + 0.25)):
                via(board, '+5V', x, yy, 0.6, 0.3)
                obst.append((pcbnew.BOX2I(pcbnew.VECTOR2I(int(MM(X0 + x - 0.3)), int(MM(Y0 + yy - 0.3))), pcbnew.VECTOR2L(int(MM(0.6)), int(MM(0.6)))), '+5V'))
                placed += 1
    print('USB-C +5V vias:', placed)
    # ---- GND ties
    gnd = board.FindNet('GND')
    for u in ('U102', 'U103'):
        p3 = pad(board, u, '3').GetPosition()
        p9 = pad(board, u, '9').GetPosition()
        track(board, gnd, [(p3.x, p3.y), (p9.x, p3.y)], 0.25)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print('patched')


if __name__ == '__main__':
    main()
