"""Stage 3 of the board: silkscreen labels, reference visibility, stackup. Run after route.py.

Usage (from hw/main-board): ~/tools/kicad-mcp-server/.venv/bin/python gen/finish.py
"""
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pcblib import BOARD_DIR, MM, PROJECT   # noqa: E402
from build_pcb import X0, Y0, W, H, NOTCH   # noqa: E402

PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BOARD_DIR, PROJECT + '.kicad_pcb')

# connector label overrides (default: the symbol's Silk field); side: 'above' or 'below' the courtyard
LABELS = {
    'J601': ('MOTOR A FL', 'above'), 'J701': ('MOTOR B FR', 'above'),
    'J801': ('MOTOR C RL', 'above'), 'J901': ('MOTOR D RR', 'above'),
    'J101': ('BATTERY 12V', 'above'), 'J102': ('MAIN SW LOOP', 'below'), 'J103': ('PI 5V OUT', 'below'),
    'J301': ('ESP32 USB', 'below'), 'J401': ('PI 5 GPIO', 'below'),
    'J405': ('CLIFF F', 'below'), 'J406': ('CLIFF R', 'below'), 'J407': ('CLIFF B', 'below'), 'J408': ('CLIFF L', 'below'),
    'J409': ('QWIIC ESP', 'below'), 'J402': ('QWIIC PI', 'below'), 'J411': ('IMU', 'below'),
    'J410': ('BUMPERS', 'below'), 'J412': ('LED BAR', 'below'), 'J201': ('KILL LOOP', 'below'),
    'J403': ('LIDAR', 'below'), 'J404': ('CPX', 'below'), 'J501': ('SPEAKER', 'below'), 'J502': ('MIC', 'below'),
    'J413': ('PAN', 'below'), 'J414': ('TILT', 'below'), 'J415': ('SONAR', 'below'),
    'F101': ('FUSE 15A', 'below'), 'SW301': ('RST', 'below'), 'SW302': ('BOOT', 'below'),
}
SMALL = ('Resistor_SMD', 'Capacitor_SMD', 'Capacitor_Tantalum_SMD', 'Diode_SMD', 'LED_SMD', 'Jumper')

STACKUP = '''(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "In1.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
			(layer "In2.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen"))
			(copper_finish "HAL lead free")
			(dielectric_constraints no)
		)
		'''


def text(board, s, x, y, size=1.0, layer=pcbnew.F_SilkS, bold=True, just=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetLayer(layer)
    t.SetPosition(pcbnew.VECTOR2I(int(MM(X0 + x)), int(MM(Y0 + y))))
    t.SetTextSize(pcbnew.VECTOR2I(int(MM(size)), int(MM(size))))
    t.SetTextThickness(int(MM(max(0.15, size * 0.16))))
    t.SetBold(bold)
    t.SetHorizJustify(just)
    return t


def main():
    board = pcbnew.LoadBoard(PCB)
    for d in list(board.Drawings()):
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.F_SilkS:
            d.SetText('')      # cleared labels from an earlier run (avoids Remove(); empty texts are dropped below)
    # nudge H103 clear of the tilt-servo header courtyard (mounting hole: only plane copper)
    h = board.FindFootprintByReference('H103')
    h.SetPosition(pcbnew.VECTOR2I(int(MM(X0 + 182.5)), int(MM(Y0 + 66.45))))
    labels = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        lib = str(fp.GetFPID().GetLibNickname())
        r = fp.Reference()
        if lib in SMALL or ref.startswith('H') or ref.startswith('JP'):
            r.SetVisible(False)
        else:
            r.SetTextSize(pcbnew.VECTOR2I(int(MM(1.0)), int(MM(1.0))))
            r.SetTextThickness(int(MM(0.15)))
        silk = LABELS.get(ref)
        if silk is None and fp.HasField('Silk'):
            silk = (fp.GetFieldText('Silk'), 'below')
        if silk:
            labels.append((fp, silk))
    # obstacles: every pad, every other courtyard, board edge
    obst = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            obst.append((p.GetBoundingBox(), None))
        if str(fp.GetFPID().GetLibNickname()) not in SMALL:
            for g in fp.GraphicalItems():
                if g.GetLayer() == pcbnew.F_SilkS and g.Type() != pcbnew.PCB_FIELD_T:
                    obst.append((g.GetBoundingBox(), fp.GetReference()))
        if fp.Reference().IsVisible():
            obst.append((fp.Reference().GetBoundingBox(), None))
    placed_boxes = []

    def free(bb, own):
        m = MM(0.25)
        if bb.GetLeft() < MM(X0 + 0.5) or bb.GetTop() < MM(Y0 + 0.5) or bb.GetRight() > MM(X0 + W - 0.5) or bb.GetBottom() > MM(Y0 + H - 0.5):
            return False
        nx0, nx1, ny0, ny1 = NOTCH
        if bb.GetRight() > MM(X0 + nx0 - 0.5) and bb.GetLeft() < MM(X0 + nx1 + 0.5) and bb.GetTop() < MM(Y0 + ny1 + 0.5):
            return False
        for o, ref in obst + placed_boxes:
            if ref is not None and ref == own:
                continue
            if bb.GetLeft() < o.GetRight() + m and bb.GetRight() > o.GetLeft() - m and bb.GetTop() < o.GetBottom() + m and bb.GetBottom() > o.GetTop() - m:
                return False
        return True
    unplaced = []
    MANUAL = {'J501': (176.75, 22.5, 90)}    # 2 mm gap between the speaker and CPX connectors
    for fp, (txt, side) in labels:
        if fp.GetReference() in MANUAL:
            x, y, ang = MANUAL[fp.GetReference()]
            t = text(board, txt, x, y, size=1.0)
            t.SetTextAngleDegrees(ang)
            board.Add(t)
            placed_boxes.append((t.GetBoundingBox(), None))
            continue
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
        cx = bb.Centre().x / 1e6 - X0
        top, bot = bb.GetTop() / 1e6 - Y0, bb.GetBottom() / 1e6 - Y0
        left, right = bb.GetLeft() / 1e6 - X0, bb.GetRight() / 1e6 - X0
        cyy = bb.Centre().y / 1e6 - Y0
        done = False
        for size in (1.0, 1.0):
            ys = [bot + 0.9, top - 0.9] if side == 'below' else [top - 0.9, bot + 0.9]
            ys2 = ys + [ys[0] + (1.2 if side == 'below' else -1.2), ys[1] + (-1.2 if side == 'below' else 1.2), ys[0] + (2.4 if side == 'below' else -2.4), ys[1] + (-2.4 if side == 'below' else 2.4)]
            cands = [(cx + dx, y, 0, 0) for y in ys2 for dx in (0, -2, 2, -4, 4, -6, 6, -9, 9, -12, 12)]
            cands += [(right + 1.0, cyy, 1, 0), (left - 1.0, cyy, 2, 0)]
            cands += [(right + 0.8, cyy, 0, 90), (left - 0.8, cyy, 0, 90), (right + 1.6, cyy, 0, 90), (left - 1.6, cyy, 0, 90)]

            for x, y, just, ang in cands:
                t = text(board, txt, x, y, size=size, just={0: 0, 1: -1, 2: 1}[just])
                if ang:
                    t.SetTextAngleDegrees(ang)
                tb = t.GetBoundingBox()
                if free(tb, fp.GetReference()):
                    board.Add(t)
                    placed_boxes.append((tb, None))
                    done = True
                    break
            if done:
                break
        if not done:
            # last resort: on the part's own body (courtyard), clear of every pad
            for dy in (-0.25, 0.25, -0.4, 0.4, 0.0):
                y = cyy + dy * (bot - top)
                t = text(board, txt, cx, y, size=1.0)
                tb = t.GetBoundingBox()
                if free(tb, fp.GetReference()) or not any(
                        tb.GetLeft() < o.GetRight() + MM(0.2) and tb.GetRight() > o.GetLeft() - MM(0.2) and
                        tb.GetTop() < o.GetBottom() + MM(0.2) and tb.GetBottom() > o.GetTop() - MM(0.2)
                        for o in [p.GetBoundingBox() for f2 in board.GetFootprints() for p in f2.Pads()] + [b for b, _ in placed_boxes]):
                    board.Add(t)
                    placed_boxes.append((tb, None))
                    done = True
                    break
        if not done:
            unplaced.append(fp.GetReference())
    print('labels not placed (no free spot):', unplaced)
    # fiducials (board-only, JLC Standard PCBA): 1 mm copper, 2 mm mask; placed where no copper or part is within 1.6 mm
    from build_pcb import FIDUCIALS
    from pcblib import load_fp
    import math
    if not any(fp.GetReference().startswith('FID') for fp in board.GetFootprints()):
        cu = [t.GetBoundingBox() for t in board.GetTracks()]
        cu += [p.GetBoundingBox() for f in board.GetFootprints() for p in f.Pads()]
        cu += [f.GetCourtyard(pcbnew.F_CrtYd).BBox() for f in board.GetFootprints() if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount()]
        cu += [b_ for b_, _ in placed_boxes]
        for i, (fx, fy) in enumerate(FIDUCIALS, 1):
            spot = None
            for rad in [k * 0.5 for k in range(0, 60)]:
                for k in range(max(1, int(2 * math.pi * rad / 0.5))):
                    px = fx + rad * math.cos(2 * math.pi * k / max(1, int(2 * math.pi * rad / 0.5)))
                    py = fy + rad * math.sin(2 * math.pi * k / max(1, int(2 * math.pi * rad / 0.5)))
                    if not (3.4 <= px <= W - 3.4 and 3.4 <= py <= H - 3.4):
                        continue
                    X, Y, r = MM(X0 + px), MM(Y0 + py), MM(1.6)
                    if not any(bb.GetLeft() < X + r and bb.GetRight() > X - r and bb.GetTop() < Y + r and bb.GetBottom() > Y - r
                               for bb in cu):
                        spot = (X, Y)
                        break
                if spot:
                    break
            if not spot:
                print('WARNING: no free spot for FID%d' % i)
                continue
            fp = load_fp('Fiducial:Fiducial_1mm_Mask2mm')
            fp.SetReference('FID%d' % i)
            fp.SetValue('Fiducial')
            fp.SetFPID(pcbnew.LIB_ID('Fiducial', 'Fiducial_1mm_Mask2mm'))
            fp.SetBoardOnly(True)
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
            fp.Reference().SetVisible(False)
            fp.SetPosition(pcbnew.VECTOR2I(int(spot[0]), int(spot[1])))
            board.Add(fp)
            cu.append(fp.GetBoundingBox())
            print('FID%d at (%.1f, %.1f)' % (i, spot[0] / 1e6 - X0, spot[1] / 1e6 - Y0))
    # battery polarity marks next to the vertical XT60 pads (pad 2 = +), left of the connector body
    j = board.FindFootprintByReference('J101')
    jb = j.GetCourtyard(pcbnew.F_CrtYd).BBox()
    for p in j.Pads():
        if p.GetNumber() in ('1', '2'):
            y = p.GetPosition().y / 1e6 - Y0
            t = text(board, '+' if p.GetNumber() == '2' else '-', jb.GetLeft() / 1e6 - X0 - 1.6, y, size=1.8)
            board.Add(t)
            placed_boxes.append((t.GetBoundingBox(), None))
    # ---- geometric silkscreen trim: outline segments that touch copper, labels, other silk or the edge go to F.Fab;
    #      reference texts that clash are hidden (they stay on F.Fab for the assembly drawing)
    pads = [(p.GetBoundingBox(), p.GetParentFootprint().GetReference() if False else None) for f in board.GetFootprints() for p in f.Pads()]
    lbl = [b for b, _ in placed_boxes]
    m = MM(0.15)

    def hit(bb, boxes):
        return any(bb.GetLeft() < o.GetRight() + m and bb.GetRight() > o.GetLeft() - m and
                   bb.GetTop() < o.GetBottom() + m and bb.GetBottom() > o.GetTop() - m for o in boxes)

    def outside(bb):
        nx0, nx1, ny0, ny1 = NOTCH
        if bb.GetLeft() < MM(X0 + 0.15) or bb.GetTop() < MM(Y0 + 0.15) or bb.GetRight() > MM(X0 + W - 0.15) or bb.GetBottom() > MM(Y0 + H - 0.15):
            return True
        return bb.GetRight() > MM(X0 + nx0 - 0.15) and bb.GetLeft() < MM(X0 + nx1 + 0.15) and bb.GetTop() < MM(Y0 + ny1 + 0.15)
    trimmed = hidden = 0
    silk = []
    for fp in board.GetFootprints():
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and g.Type() != pcbnew.PCB_FIELD_T:
                silk.append((fp.GetReference(), g))
    pad_boxes = [p.GetBoundingBox() for f in board.GetFootprints() for p in f.Pads()]
    keep_boxes = {}
    for ref, g in silk:
        bb = g.GetBoundingBox()
        # a straight outline segment is thin; use its real box (bbox of a diagonal is conservative)
        if hit(bb, pad_boxes) or hit(bb, lbl) or outside(bb):
            g.SetLayer(pcbnew.F_Fab)
            trimmed += 1
        else:
            keep_boxes.setdefault(ref, []).append(bb)
    # silk of different footprints overlapping: trim the passive one
    refs = list(keep_boxes)
    for i, ra in enumerate(refs):
        for rb in refs[i + 1:]:
            for ba in list(keep_boxes[ra]):
                if hit(ba, keep_boxes[rb]):
                    fa = board.FindFootprintByReference(ra)
                    victim = ra if str(fa.GetFPID().GetLibNickname()) in SMALL else rb
                    for rr, g in silk:
                        if rr == victim and g.GetLayer() == pcbnew.F_SilkS and hit(g.GetBoundingBox(), keep_boxes[ra if victim == rb else rb]):
                            g.SetLayer(pcbnew.F_Fab)
                            trimmed += 1
    silk_now = [g.GetBoundingBox() for fp in board.GetFootprints() for g in fp.GraphicalItems()
                if g.GetLayer() == pcbnew.F_SilkS and g.Type() != pcbnew.PCB_FIELD_T]
    for fp in board.GetFootprints():
        r = fp.Reference()
        if r.IsVisible():
            bb = r.GetBoundingBox()
            if hit(bb, pad_boxes) or hit(bb, lbl) or hit(bb, silk_now) or outside(bb):
                r.SetVisible(False)
                hidden += 1
    print('silk trimmed to fab: %d segments, references hidden: %d' % (trimmed, hidden))
    for (txt, size, bold), (x, y) in (((('SUPER BOT  MAIN BOARD  rev B', 1.3, True)), (100.0, 35.0)),
                                       ((('rev B  2026-11  JLC04161H-7628', 1.0, False)), (100.0, 37.2))):
        for dx in (0, -10, 10, -20, 20, -30, 30):
            t = text(board, txt, x + dx, y, size=size, bold=bold)
            if free(t.GetBoundingBox(), None):
                board.Add(t)
                placed_boxes.append((t.GetBoundingBox(), None))
                break
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    # stackup + plane layer types
    s = open(PCB).read()
    s = re.sub(r'\(4 "In1.Cu" signal\)', '(4 "In1.Cu" power)', s)
    s = re.sub(r'\(6 "In2.Cu" signal\)', '(6 "In2.Cu" mixed)', s)
    if '(stackup' not in s:
        s = s.replace('(setup\n\t\t', '(setup\n\t\t' + STACKUP, 1)
    open(PCB, 'w').write(s)
    print('finished')


if __name__ == '__main__':
    main()
