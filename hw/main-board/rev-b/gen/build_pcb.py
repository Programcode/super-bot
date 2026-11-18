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
from pcblib import read_netlist, load_fp, courtyard_bbox, BOARD_DIR, MM, PROJECT   # noqa: E402
from utils.project_netclasses import load_project_net_classes, apply_net_classes_to_board   # noqa: E402

PCB = os.path.join(BOARD_DIR, PROJECT + '.kicad_pcb')
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
    'J101': (11.3, 55.5, 270, 'PWR'),    # vertical XT60 battery (mates toward the front wall); pad 2 (+) upper, next to the fuse
    'F101': (21.5, 48.5, 90, 'PWR'),
    'J102': (11.0, 11.5, 90, 'PWR'),     # vertical XT60 main switch loop: pad 1 (VSW) up to Q101, pad 2 (VBAT_F) down to the strip
    'Q101': (24.0, 5.5, 180, 'PWR'),
    'R102': (34.5, 3.0, 0, 'PWR'),
    'U101': (31.0, 19.5, 0, 'PWR'),
    'D102': (32.8, 12.5, 270, 'PWR'),
    'C102': (30.8, 46.0, 180, 'PWR'),
    'H101': (3.5, 66.5, 0, None), 'H102': (3.5, 23.0, 0, None), 'H103': (182.3, 66.3, 0, None), 'H104': (144.0, 3.8, 0, None),
    # motor cut: Q202 with its gate network in a fixed row (R207 / C206 / D201 bridge VBUS pour -> gate bar)
    'Q202': (56.5, 45.5, 0, 'MCUT'),
    'R207': (44.8, 44.2, 90, 'MCUT'), 'C206': (46.3, 44.2, 90, 'MCUT'), 'D201': (48.3, 44.2, 90, 'MCUT'),
    'C203': (49.0, 62.5, 90, 'MCUT'),
    'C204': (58.6, 62.5, 90, 'MCUT'),
    'D202': (54.0, 53.6, 0, 'MCUT'),
    # bucks (identical cells): SW leaves at the bottom, inductor right under it (TI EVM style), VIN caps on the right
    'U102': (155.0, 42.0, 0, 'B5'), 'L101': (155.4, 48.6, 90, 'B5'),
    'U103': (174.0, 42.0, 0, 'BS'), 'L102': (174.4, 48.6, 90, 'BS'),
    # top middle (logic); the WROOM antenna hangs over a board cut-out at x 45-63
    'U301': (54.0, 12.8, 0, 'TM'),
    'J301': (74.0, 4.4, 'U', 'TM'),
    'J401': (111.3, 4.5, 0, 'TM'),
    'U303': (76.0, 24.0, 0, 'TM'),
    'J405': (82.3, 14.5, 0, 'TM'), 'J406': (92.1, 14.5, 0, 'TM'), 'J407': (101.9, 14.5, 0, 'TM'), 'J408': (111.7, 14.5, 0, 'TM'),
    'J411': (121.5, 14.5, 0, 'TM'), 'J409': (130.5, 14.5, 0, 'TM'), 'J402': (138.3, 14.5, 0, 'TM'),
    'J410': (96.0, 30.5, 0, 'TM'),        # bumpers PH6
    'U201': (110.0, 24.5, 0, 'TM'), 'J201': (114.0, 31.5, 0, 'TM'),
    'J412': (131.0, 31.0, 0, 'TM'),       # LED bar PH4
    'U104': (143.3, 31.6, 0, 'TM'),       # AMS1117 next to the 5 V plane, output straight into the In2 3.3 V plane
    'J415': (136.0, 23.8, 90, 'TM'),       # optional HC-SR04 header (DNP)
    # right top
    'J103': (179.0, 4.4, 'U', 'RT'),
    'U401': (156.5, 15.5, 0, 'RT'),
    'J413': (169.5, 66.6, 90, 'BS'), 'J414': (176.4, 61.5, 90, 'BS'),   # on the VSERVO plane
    'J502': (158.5, 31.7, 0, 'RT'), 'J403': (176.5, 31.7, 0, 'RT'), 'J404': (181.5, 19.0, 90, 'RT'),
    'U501': (165.5, 14.5, 0, 'RT'), 'J501': (171.0, 22.5, 0, 'RT'),
}
for k, xc in enumerate(CHX):
    n = 6 + k
    ANCHORS['J%d01' % n] = (xc, 66.0, 0, 'CH%d' % k)
    ANCHORS['U%d01' % n] = (xc, 48.0, 0, 'CH%d' % k)   # OUT1 bottom-left, OUT2 bottom-right

FIDUCIALS = [(40.0, 66.0), (150.0, 66.5), (100.0, 22.0)]   # preferred spots; moved to the nearest free place   # board-only, >= 3.35 mm from the edge (JLC Standard PCBA)


def _near():
    m = {}
    for r in ('C101', 'R103', 'TP105'):
        m[r] = 'U101'
    for r in ('C103', 'TP101'):
        m[r] = 'C102'
    for r in ('C104', 'C105', 'C106', 'R104', 'R105', 'C107', 'C108', 'C109', 'C110', 'C111', 'C112', 'R106', 'R107', 'R108',
              'TP102'):
        m[r] = 'U102'
    for r in ('C113', 'C114', 'C115', 'C116', 'C117', 'C118', 'C119', 'C120', 'C121', 'R109', 'R110', 'R111', 'TP106'):
        m[r] = 'U103'
    m['C122'] = 'L102'
    m['TP103'] = 'L102'
    for r in ('R112', 'R113', 'C123'):
        m[r] = 'J103'
    for r in ('C124', 'C125', 'C126', 'C127', 'D103', 'D104', 'R114', 'D105', 'TP104'):
        m[r] = 'U104'
    for r in ('C201', 'C202', 'R201', 'R202', 'R203', 'R211', 'R212', 'C207', 'R213', 'TP202', 'TP203', 'TP205', 'TP206'):
        m[r] = 'U201'
    for r in ('R204', 'R205', 'JP201', 'Q201', 'R206', 'TP204'):
        m[r] = 'J201'
    for r in ('C205', 'D203', 'R210', 'R208', 'Q203', 'R209'):
        m[r] = 'Q202'
    m['TP201'] = 'C203'
    m['TP207'] = 'C204'
    for r in ('C301', 'C302', 'C303', 'R301', 'C304', 'R302', 'SW301', 'SW302', 'R303', 'R304', 'Q301', 'Q302', 'R305', 'R306',
              'R315', 'R316', 'TP301', 'TP302', 'TP303', 'TP304'):
        m[r] = 'U301'
    for r in ('R307', 'R308', 'U302', 'C305'):
        m[r] = 'J301'
    for r in ('C306', 'R309', 'R310', 'R311', 'R314', 'D301', 'TP305', 'TP306'):
        m[r] = 'U303'
    for r in ('R312', 'R313', 'TP307', 'TP308'):
        m[r] = 'J405'
    for r in ('C401', 'R405', 'R406', 'R407', 'R408', 'R409', 'R410'):
        m[r] = 'U401'
    for r in ('R411', 'R412'):
        m[r] = 'J415'
    for r in ('R401', 'R402', 'R403'):
        m[r] = 'J403'
    m['R404'] = 'J404'
    for r in ('RN401', 'RN402'):
        m[r] = 'J410'
    for r in ('C501', 'C502', 'R501'):
        m[r] = 'U501'
    for r in ('R502', 'R503'):
        m[r] = 'J502'
    for n in (6, 7, 8, 9):
        for r in ('C%d01', 'R%d01', 'C%d02', 'C%d03', 'C%d04', 'C%d05'):
            m[r % n] = 'U%d01' % n
        for r in ('R%d02', 'R%d03', 'R%d04', 'R%d05', 'C%d06', 'C%d07'):
            m[r % n] = 'J%d01' % n
    return m


NEAR = _near()


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


ANT_KEEPOUT = (44.0, 0.0, 64.0, 6.6)     # around the WROOM antenna cut-out (no parts, no copper)
ANT_CUT = (45.0, 63.0, 6.4)             # board cut-out under the antenna: x0, x1, depth
CORRIDORS = [(19.0, 11.9, 24.3, 48.0),   # VBAT_F strip
             (13.5, 11.9, 24.3, 18.6),   # VBAT_F to the switch loop
             (36.0, 0.5, 43.6, 50.0),    # VBUS channel
             (36.0, 42.5, 49.0, 50.0)]   # VBUS to the motor-cut FET
for _xc in CHX:   # motor output tracks + rev B fanout vias (MOT_EN/NFAULT/VREF left, PMODE/VM right)
    CORRIDORS += [(_xc - 7.6, 49.6, _xc - 3.3, 63.2), (_xc + 3.3, 48.4, _xc + 7.6, 63.2),
                  (_xc - 5.5, 46.4, _xc - 3.5, 48.8), (_xc + 3.6, 44.3, _xc + 4.9, 45.7)]
CORRIDORS += [(44.5, 42.6, 53.4, 43.9)]          # Q202 gate bar (R207 / C206 / D201 -> gate)
for _ux in (155.0, 174.0):   # buck SW node and inductor; VBUS feed via above VIN
    CORRIDORS += [(_ux - 0.6, 43.0, _ux + 1.0, 45.5), (_ux + 0.2, 36.0, _ux + 1.9, 41.0)]
CORRIDORS += [(145.8, 36.0, 147.8, 38.0)]   # VBUS feed via at the In2 strip end


def main():
    comps, netmap = read_netlist(os.path.join(BOARD_DIR, PROJECT + '.kicad_sch'))
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

    def is_decap(r):
        return r.startswith('C') and 'GND' in nets_of.get(r, set()) and len(nets_of.get(r, set())) == 2
    order = sorted(missing, key=lambda r: (0 if is_decap(r) else 1,
                                           -(fp_rect(fps[r])[2] - fp_rect(fps[r])[0]) * (fp_rect(fps[r])[3] - fp_rect(fps[r])[1])))
    failed = []
    for ref in order:
        a = pick_anchor(ref)
        fp = fps[ref]
        afp = fps[a]
        shared = (nets_of.get(ref, set()) & nets_of.get(a, set()))
        sig = shared - POWER or shared
        tpads = [p for p in afp.Pads() if p.GetNetname() in sig and p.GetNetname() != 'GND'] or \
            [p for p in afp.Pads() if p.GetNetname() in sig] or list(afp.Pads())
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
    ax0, ax1, ad = ANT_CUT
    pts = [(0, 0), (ax0, 0), (ax0, ad), (ax1, ad), (ax1, 0), (NOTCH[0], 0), (NOTCH[0], NOTCH[3]), (NOTCH[1], NOTCH[3]),
           (NOTCH[1], 0), (W, 0), (W, H), (0, H)]
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(int(MM(X0 + a[0])), int(MM(Y0 + a[1]))))
        seg.SetEnd(pcbnew.VECTOR2I(int(MM(X0 + b[0])), int(MM(Y0 + b[1]))))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.1))
        board.Add(seg)

    for i, (fx, fy) in enumerate(FIDUCIALS if '--fiducials' in sys.argv else [], 1):
        fp = load_fp('Fiducial:Fiducial_1mm_Mask2mm')
        fp.SetReference('FID%d' % i)
        fp.SetValue('Fiducial')
        fp.SetFPID(pcbnew.LIB_ID('Fiducial', 'Fiducial_1mm_Mask2mm'))
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        board.Add(fp)
        for rad in [i * 0.5 for i in range(0, 30)]:
            steps = max(1, int(2 * math.pi * rad / 0.5))
            hitpos = None
            for k in range(steps):
                px, py = fx + rad * math.cos(2 * math.pi * k / steps), fy + rad * math.sin(2 * math.pi * k / steps)
                if not (3.4 <= px <= W - 3.4 and 3.4 <= py <= H - 3.4):
                    continue
                place_center(fp, px, py)
                r = fp_rect(fp, 0.5)
                if occ.free(r, None):
                    occ.add(r)
                    hitpos = (px, py)
                    break
            if hitpos:
                break
        if not hitpos:
            print('WARNING: no free spot for FID%d' % i)
    board.Save(PCB)
    print('saved', PCB, 'failed', len(failed))
    return failed


if __name__ == '__main__':
    main()
