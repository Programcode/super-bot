"""Stage 1 of the board: footprints from the netlist, placement, outline, holes, zones, silk labels.

Usage (from hw/main-board): ~/tools/kicad-mcp-server/.venv/bin/python gen/build_pcb.py
Writes main-board.kicad_pcb (unrouted). gen/route.py does the routing.
"""
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser('~/tools/kicad-mcp-server/python'))
from pcblib import read_netlist, load_fp, courtyard_bbox, BOARD_DIR, MM   # noqa: E402
from utils.project_netclasses import load_project_net_classes, apply_net_classes_to_board   # noqa: E402

PCB = os.path.join(BOARD_DIR, 'main-board.kicad_pcb')
X0, Y0 = 50.0, 50.0          # board origin on the KiCad page
W, H = 186.0, 70.0
NOTCH = (148.0, 172.0, 0.0, 8.0)   # x0, x1, y0, y1: room for the Pi 5's USB-C plug above the board
POWER = {'GND', '+3V3', '+5V', 'VMOT', 'VBUS', 'VSERVO', '+5V_USB', 'V3V3_IN', '/MOT_EN', '/MOT_NFAULT', '/VREF'}

# ---------------------------------------------------------------- regions (x0, y0, x1, y1), board coords
REG = {
    'PWR': (0, 0, 44, 70),
    'MCUT': (44, 37, 64, 70),
    'CH0': (64, 37, 85, 70), 'CH1': (85, 37, 106, 70), 'CH2': (106, 37, 127, 70), 'CH3': (127, 37, 148, 70),
    'B5': (148, 37, 167, 70), 'BS': (167, 37, 186, 70),
    'TM': (44, 0, 148, 37),
    'RT': (148, 8, 186, 37),
}
CHX = [74.5, 95.5, 116.5, 137.5]

# anchor: ref -> (x, y, rot_or_dir, region). rot: number = degrees; 'L','R','U','D' = mating side direction
ANCHORS = {
    # power input chain, left region: XT60 -> fuse (vertical) -> VBAT_F strip -> XT30 switch loop -> FET -> shunt -> VBUS channel
    'J101': (9.6, 54.5, 'L', 'PWR'),     # XT60 battery, plugs in from the left; pad 2 (+) is the upper pin
    'F101': (21.5, 48.5, 90, 'PWR'),
    'J102': (7.5, 10.0, 'L', 'PWR'),     # XT30 main switch loop, plugs in from the left
    'Q101': (24.0, 5.5, 180, 'PWR'),
    'R102': (34.5, 3.0, 0, 'PWR'),
    'U101': (31.0, 19.5, 0, 'PWR'),
    'D102': (32.8, 12.5, 270, 'PWR'),
    'C102': (30.8, 46.0, 180, 'PWR'),
    'U104': (30.0, 31.0, 0, 'PWR'),      # AMS1117 3.3 V
    'H101': (3.5, 66.5, 0, None), 'H102': (3.5, 23.0, 0, None), 'H103': (182.3, 66.3, 0, None), 'H104': (144.0, 3.8, 0, None),
    # motor cut
    'Q202': (52.0, 44.0, 0, 'MCUT'),
    'C203': (49.0, 62.5, 90, 'MCUT'),
    'C204': (58.6, 62.5, 90, 'MCUT'),
    'D202': (54.0, 53.0, 0, 'MCUT'),
    # bucks
    # TPS56637: SW leaves at the bottom, so the inductor sits right under it (TI EVM style); VIN caps on the right
    'U102': (155.0, 42.0, 0, 'B5'), 'L101': (155.4, 48.6, 90, 'B5'),
    'U103': (174.0, 42.0, 0, 'BS'), 'L102': (174.4, 48.6, 90, 'BS'),
    # top middle
    'U301': (54.0, 12.8, 0, 'TM'),
    'J301': (71.0, 4.4, 'U', 'TM'),
    'J401': (111.3, 4.5, 0, 'TM'),
    'U303': (74.0, 24.0, 0, 'TM'),
    'J405': (86.0, 14.5, 0, 'TM'), 'J406': (96.0, 14.5, 0, 'TM'), 'J407': (106.0, 14.5, 0, 'TM'), 'J408': (116.0, 14.5, 0, 'TM'),
    'J411': (126.0, 14.5, 0, 'TM'), 'J409': (135.0, 14.5, 0, 'TM'), 'J402': (143.0, 14.5, 0, 'TM'),
    'J410': (96.0, 30.5, 0, 'TM'),        # bumpers PH6
    'U201': (114.0, 25.0, 0, 'TM'), 'J201': (123.0, 31.0, 0, 'TM'),
    'J412': (138.0, 31.0, 0, 'TM'),       # LED bar PH4
    # right top
    'J103': (179.0, 4.4, 'U', 'RT'),
    'U401': (156.5, 15.5, 0, 'RT'),
    'J413': (150.3, 14.0, 0, 'RT'), 'J414': (150.3, 23.0, 0, 'RT'),
    'J502': (158.5, 31.7, 0, 'RT'), 'J403': (176.5, 31.7, 0, 'RT'), 'J404': (181.5, 19.0, 90, 'RT'),
    'U501': (165.5, 14.5, 0, 'RT'), 'J501': (171.0, 22.5, 0, 'RT'),
    'J415': (141.5, 24.5, 90, 'TM'),      # optional HC-SR04 header (DNP)
}
for k, xc in enumerate(CHX):
    n = 6 + k
    ANCHORS['J%d01' % n] = (xc, 66.0, 0, 'CH%d' % k)
    ANCHORS['U%d01' % n] = (xc, 48.0, 0, 'CH%d' % k)   # OUT1 bottom-left, OUT2 bottom-right

# satellites forced to a specific anchor (ref -> anchor ref)
NEAR = {
    'C104': 'U102',
    'C105': 'U102',
    'C106': 'U102',
    'R105': 'U102',
    'R106': 'U102',
    'C107': 'U102',
    'C108': 'U102',
    'C109': 'U102',
    'C110': 'U102',
    'C111': 'U102',
    'R107': 'U102',
    'R108': 'U102',
    'R109': 'U102',
    'C112': 'U102',
    'R110': 'U102',
    'R111': 'U102',
    'D104': 'U102',
    'C113': 'U103',
    'C114': 'U103',
    'C115': 'U103',
    'R112': 'U103',
    'R113': 'U103',
    'C116': 'U103',
    'C117': 'U103',
    'C118': 'U103',
    'C119': 'U103',
    'C120': 'U103',
    'R114': 'U103',
    'R115': 'U103',
    'R116': 'U103',
    'C121': 'U103',
    'R117': 'U103',
    'D103': 'C102',
    'R104': 'C102',
    'C101': 'U101', 'R103': 'U101', 'C103': 'C102',
    'C124': 'U104', 'C125': 'U104', 'C126': 'U104', 'C127': 'U104', 'R120': 'U104', 'D107': 'U104', 'D105': 'U104', 'D106': 'U104',
    'C301': 'U301', 'C302': 'U301', 'C303': 'U301', 'R301': 'U301', 'C304': 'U301', 'R302': 'U301', 'SW301': 'U301', 'SW302': 'U301',
    'R303': 'U301', 'R304': 'U301', 'Q301': 'U301', 'Q302': 'U301', 'R305': 'U301', 'R306': 'U301',
    'R307': 'J301', 'R308': 'J301', 'U302': 'J301', 'C305': 'J301',
    'C306': 'U303', 'R309': 'U303', 'R310': 'U303', 'R311': 'U303', 'R312': 'J405', 'R313': 'J405', 'R314': 'U303', 'D301': 'U303',
    'C202': 'U201', 'R202': 'U201', 'R203': 'U201', 'R204': 'J201', 'R205': 'J201', 'JP201': 'J201', 'Q201': 'J201', 'R206': 'J201',
    'R211': 'U201', 'R212': 'U201', 'C207': 'U201', 'C206': 'Q202', 'R213': 'U201',
    'C205': 'Q202', 'D203': 'Q202', 'R210': 'Q202', 'R207': 'Q202', 'D201': 'Q202', 'R208': 'Q202', 'Q203': 'Q202', 'R209': 'Q202',
    'C401': 'U401', 'R414': 'U401', 'R415': 'U401', 'R419': 'J415', 'R420': 'J415',
    'C501': 'U501', 'C502': 'U501', 'R501': 'U501', 'R502': 'J502', 'R503': 'J502',
    'R118': 'J103', 'R119': 'J103', 'C123': 'J103',
    'R401': 'J403', 'R402': 'J403', 'R403': 'J403', 'R404': 'J404',
}


def bbox_rel(fp):
    bb = courtyard_bbox(fp)
    p = fp.GetPosition()
    return (bb.GetLeft() - p.x, bb.GetTop() - p.y, bb.GetRight() - p.x, bb.GetBottom() - p.y)


def place_center(fp, x, y):
    """Move fp so its courtyard centre lands on board coords (x, y)."""
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    l, t, r, b = bbox_rel(fp)
    cx, cy = (l + r) / 2, (t + b) / 2
    fp.SetPosition(pcbnew.VECTOR2I(int(MM(X0 + x) - cx), int(MM(Y0 + y) - cy)))


def orient_dir(fp, d):
    """Rotate so the body (courtyard centre relative to the pads) points in direction d."""
    want = {'L': (-1, 0), 'R': (1, 0), 'U': (0, -1), 'D': (0, 1)}[d]
    best = None
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        bb = courtyard_bbox(fp)
        pads = [p.GetPosition() for p in fp.Pads() if p.GetNumber() not in ('', 'MP', 'SH')]
        px = sum(p.x for p in pads) / len(pads)
        py = sum(p.y for p in pads) / len(pads)
        vx, vy = bb.Centre().x - px, bb.Centre().y - py
        n = math.hypot(vx, vy) or 1
        score = (vx * want[0] + vy * want[1]) / n
        if best is None or score > best[0]:
            best = (score, rot)
    fp.SetOrientationDegrees(best[1])


class Occ:
    def __init__(self):
        self.rects = []

    def free(self, r, region, keep=()):
        x0, y0, x1, y1 = r
        if region:
            rx0, ry0, rx1, ry1 = region
            if x0 < rx0 + 0.3 or y0 < ry0 + 0.3 or x1 > rx1 - 0.3 or y1 > ry1 - 0.3:
                return False
        if x0 < 0.4 or y0 < 0.4 or x1 > W - 0.4 or y1 > H - 0.4:
            return False
        nx0, nx1, ny0, ny1 = NOTCH
        if x1 > nx0 - 0.3 and x0 < nx1 + 0.3 and y0 < ny1 + 0.3:
            return False
        for k in keep:
            if x1 > k[0] and x0 < k[2] and y1 > k[1] and y0 < k[3]:
                return False
        for q in self.rects:
            if x1 > q[0] and x0 < q[2] and y1 > q[1] and y0 < q[3]:
                return False
        return True

    def add(self, r):
        self.rects.append(r)


def fp_rect(fp, margin=0.2):
    bb = courtyard_bbox(fp)
    return (bb.GetLeft() / 1e6 - X0 - margin, bb.GetTop() / 1e6 - Y0 - margin,
            bb.GetRight() / 1e6 - X0 + margin, bb.GetBottom() / 1e6 - Y0 + margin)


ANT_KEEPOUT = (45.0, 0.0, 63.0, 6.8)     # under the WROOM antenna
CORRIDORS = [(19.0, 10.5, 24.3, 48.0),   # VBAT_F strip
             (11.0, 10.5, 24.3, 15.5),   # VBAT_F to the switch loop
             (36.0, 0.5, 43.6, 50.0),    # VBUS channel
             (36.0, 42.5, 49.0, 50.0)]   # VBUS to the motor-cut FET
for _xc in CHX:   # motor output tracks: driver corner pins down to connector pins 1 and 6
    CORRIDORS += [(_xc - 7.6, 49.6, _xc - 3.3, 63.2), (_xc + 3.3, 49.0, _xc + 7.6, 63.2)]
for _ux in (155.0, 174.0):   # buck SW node and inductor
    CORRIDORS += [(_ux - 0.6, 43.0, _ux + 1.0, 45.5)]


def main():
    comps, netmap = read_netlist(os.path.join(BOARD_DIR, 'main-board.kicad_sch'))
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    netinfo = {}
    for name in sorted(set(netmap.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    fps = {}
    for c in comps:
        fp = load_fp(c['footprint'])
        fp.SetReference(c['ref'])
        fp.SetValue(c['value'])
        lib, name = c['footprint'].split(':', 1)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetPath(pcbnew.KIID_PATH(c['path']))
        if hasattr(fp, 'SetSheetname'):
            fp.SetSheetname(c['sheetname'])
            fp.SetSheetfile(c.get('sheetfile', ''))
        for k, v in c['fields'].items():
            if k in ('LCSC', 'MPN', 'Silk', 'Description'):
                fp.SetField(k, v)
                f = next((x for x in fp.GetFields() if x.GetName() == k), None)
                if f:
                    f.SetVisible(False)
                    f.SetLayer(pcbnew.F_Fab)
        if c.get('dnp'):
            fp.SetDNP(True)
        if c.get('exclude_from_bom'):
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
        for pad in fp.Pads():
            key = (c['ref'], pad.GetNumber())
            if key in netmap:
                pad.SetNet(netinfo[netmap[key]])
        board.Add(fp)
        fps[c['ref']] = fp

    occ = Occ()
    region_of = {}
    # ---- anchors
    for ref, (x, y, r, reg) in ANCHORS.items():
        fp = fps[ref]
        if isinstance(r, str):
            orient_dir(fp, r)
        else:
            fp.SetOrientationDegrees(r)
        place_center(fp, x, y)
        region_of[ref] = reg
        occ.add(fp_rect(fp, 0.25))
    occ.add(ANT_KEEPOUT)
    for c in CORRIDORS:
        occ.add(c)
    missing = [c['ref'] for c in comps if c['ref'] not in ANCHORS]
    # ---- choose an anchor for every satellite
    nets_of = {}
    for (ref, pin), n in netmap.items():
        nets_of.setdefault(ref, set()).add(n)
    sheet_of = {c['ref']: c['sheetname'] for c in comps}

    def pick_anchor(ref):
        if ref in NEAR:
            return NEAR[ref]
        mine = nets_of.get(ref, set())
        cands = []
        for a in ANCHORS:
            if a.startswith('H'):
                continue
            shared = mine & nets_of.get(a, set())
            sig = shared - POWER
            if sig:
                cands.append((0 if sheet_of[a] == sheet_of[ref] else 1, 0, a, sig))
            elif shared:
                cands.append((0 if sheet_of[a] == sheet_of[ref] else 1, 1, a, shared))
        if not cands:
            raise SystemExit('no anchor for ' + ref)
        cands.sort(key=lambda c: (c[1], c[0]))
        return cands[0][2]

    order = sorted(missing, key=lambda r: -(fp_rect(fps[r])[2] - fp_rect(fps[r])[0]) * (fp_rect(fps[r])[3] - fp_rect(fps[r])[1]))
    failed = []
    for ref in order:
        a = pick_anchor(ref)
        fp = fps[ref]
        afp = fps[a]
        shared = (nets_of.get(ref, set()) & nets_of.get(a, set()))
        sig = shared - POWER or shared
        tpads = [p for p in afp.Pads() if p.GetNetname() in sig] or list(afp.Pads())
        tp = tpads[0].GetPosition()
        tx, ty = tp.x / 1e6 - X0, tp.y / 1e6 - Y0
        reg = REG[region_of[a]]
        done = False
        for rad in [i * 0.5 for i in range(0, 60)]:
            steps = max(1, int(2 * math.pi * rad / 0.5))
            pts = [(tx + rad * math.cos(2 * math.pi * k / steps), ty + rad * math.sin(2 * math.pi * k / steps)) for k in range(steps)]
            for (px, py) in pts:
                for rot in (0, 90):
                    fp.SetOrientationDegrees(rot)
                    place_center(fp, round(px * 4) / 4, round(py * 4) / 4)
                    r = fp_rect(fp, 0.35)
                    if occ.free(r, reg):
                        occ.add(r)
                        region_of[ref] = region_of[a]
                        done = True
                        break
                if done:
                    break
            if done:
                break
        if not done:
            failed.append((ref, a))
            place_center(fp, W + 10, H + 10 + len(failed) * 4)
    print('satellites placed: %d, failed: %d %s' % (len(order) - len(failed), len(failed), failed))

    # ---- outline with the Pi notch, 1 mm corner chamfer-free rectangle
    pts = [(0, 0), (NOTCH[0], 0), (NOTCH[0], NOTCH[3]), (NOTCH[1], NOTCH[3]), (NOTCH[1], 0), (W, 0), (W, H), (0, H)]
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(int(MM(X0 + a[0])), int(MM(Y0 + a[1]))))
        seg.SetEnd(pcbnew.VECTOR2I(int(MM(X0 + b[0])), int(MM(Y0 + b[1]))))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.1))
        board.Add(seg)

    board.Save(PCB)
    print('saved', PCB, 'failed', len(failed))
    return failed


if __name__ == '__main__':
    main()
