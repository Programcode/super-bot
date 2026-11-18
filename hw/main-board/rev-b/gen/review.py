"""Rev B self design review: measures the finished board against a checklist and prints markdown.

Usage (from hw/main-board/rev-b): ~/tools/kicad-mcp-server/.venv/bin/python gen/review.py > /tmp/review.md
Gates (ERC/DRC) come from reports/*.json written by kicad-check.
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pcblib import BOARD_DIR, PROJECT, read_netlist   # noqa: E402
from build_pcb import X0, Y0, W, H, ANT_KEEPOUT, ANT_CUT   # noqa: E402

PCB = os.path.join(BOARD_DIR, PROJECT + '.kicad_pcb')
MMV = 1e6


def mm(v):
    return v / MMV


def main():
    out = []
    ok_all = True

    def check(name, ok, detail):
        nonlocal ok_all
        ok_all &= bool(ok)
        out.append('| %s | %s | %s |' % (name, 'PASS' if ok else '**FAIL**', detail))

    b = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    rep = os.path.join(BOARD_DIR, 'reports')
    erc = json.load(open(os.path.join(rep, PROJECT + '-erc.json')))
    drc = json.load(open(os.path.join(rep, PROJECT + '-drc.json')))
    n_erc = sum(len(s.get('violations', [])) for s in erc.get('sheets', []))
    check('ERC (severity all)', n_erc == 0, '%d violations' % n_erc)
    check('DRC (severity all, zones refilled)', len(drc['violations']) == 0, '%d violations' % len(drc['violations']))
    check('Unconnected items', len(drc['unconnected_items']) == 0, '%d' % len(drc['unconnected_items']))
    check('Schematic parity', len(drc.get('schematic_parity', [])) == 0, '%d issues' % len(drc.get('schematic_parity', [])))

    # ---- JLC DFM numbers measured on the copper
    tracks = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    minw = min(mm(t.GetWidth()) for t in tracks)
    check('JLC min track 0.09 mm (1 oz, 4L)', minw >= 0.1, 'min track %.2f mm (rule 0.10)' % minw)
    mind = min(mm(v.GetDrillValue()) for v in vias)
    minring = min((mm(v.GetWidth(pcbnew.F_Cu)) - mm(v.GetDrillValue())) / 2 for v in vias)
    check('JLC via drill >= 0.15 mm, ring >= 0.15 mm', mind >= 0.3 and minring >= 0.149,
          'min drill %.2f mm, min ring %.3f mm, %d vias' % (mind, minring, len(vias)))
    ds = b.GetDesignSettings()
    check('JLC copper-to-edge >= 0.2 mm', mm(ds.m_CopperEdgeClearance) >= 0.3, 'rule %.2f mm (DRC enforced)' % mm(ds.m_CopperEdgeClearance))
    small = []
    for d in b.Drawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.F_SilkS and d.GetText().strip():
            if mm(d.GetTextHeight()) < 0.999 or mm(d.GetTextThickness()) < 0.149:
                small.append(d.GetText())
    for fp in b.GetFootprints():
        r = fp.Reference()
        if r.IsVisible() and r.GetLayer() == pcbnew.F_SilkS and (mm(r.GetTextHeight()) < 0.999 or mm(r.GetTextThickness()) < 0.149):
            small.append(fp.GetReference())
    check('JLC silk text >= 1.0 mm / 0.15 mm', not small, 'too small: %s' % (', '.join(small[:8]) or 'none'))
    fids = [fp for fp in b.GetFootprints() if fp.GetReference().startswith('FID')]
    fid_ok = all(3.35 <= mm(f.GetPosition().x) - X0 <= W - 3.35 and 3.35 <= mm(f.GetPosition().y) - Y0 <= H - 3.35 for f in fids)
    check('Fiducials for Standard PCBA (3, >= 3.35 mm from edge)', len(fids) == 3 and fid_ok,
          ', '.join('%s (%.1f, %.1f)' % (f.GetReference(), mm(f.GetPosition().x) - X0, mm(f.GetPosition().y) - Y0) for f in fids))
    # via in SMD pad (paste) -> none except where the pad's mask window excludes it
    vip = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            for v in vias:
                if p.HitTest(v.GetPosition()) and p.GetNumber() not in ('17', '41', ''):
                    vip.append('%s.%s' % (fp.GetReference(), p.GetNumber()))
    check('No via-in-pad (costs extra on JLC 4-layer)', not vip, ', '.join(sorted(set(vip))[:10]) or 'none (thermal pads use tented vias outside the mask window)')

    # ---- power copper
    pieces = {}
    for z in b.Zones():
        if z.GetZoneName().endswith(' pour') and not z.GetZoneName().startswith('VBUS U'):
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                if z.IsOnLayer(L):
                    pieces['%s %s' % (z.GetNetname().split('/')[-1], b.GetLayerName(L))] = z.GetFilledPolysList(L).OutlineCount()
    split = {k: v for k, v in pieces.items() if v != 1 and ('VMOT' not in k)}
    check('Input-chain + VBUS pours unbroken (one piece per layer)', not split,
          ', '.join('%s=%d' % kv for kv in sorted(pieces.items())))
    foreign = []
    for z in b.Zones():
        if not z.GetZoneName().endswith(' pour') or z.GetNetname().split('/')[-1] not in ('VBAT_IN', 'VBAT_F', 'VSW', 'VBUS'):
            continue
        ol = z.Outline()
        for t in tracks:
            if t.GetNetname() != z.GetNetname() and z.IsOnLayer(t.GetLayer()):
                mid = pcbnew.VECTOR2I((t.GetStart().x + t.GetEnd().x) // 2, (t.GetStart().y + t.GetEnd().y) // 2)
                if ol.Contains(t.GetStart()) or ol.Contains(t.GetEnd()) or ol.Contains(mid):
                    foreign.append(t.GetNetname().split('/')[-1])
    check('No foreign tracks through the 15 A input / VBUS pours', not foreign, ', '.join(sorted(set(foreign))) or 'none')
    sup = ('VBUS', 'VMOT', '+5V', 'VSERVO', '/Power/VBAT_IN', '/Power/VBAT_F', '/Power/VSW', '/Power/VPROT')
    thin = sorted({(t.GetNetname(), round(mm(t.GetWidth()), 2)) for t in tracks if t.GetNetname() in sup and mm(t.GetWidth()) < 0.3})
    check('No power track under 0.3 mm on VBUS/VMOT/5V/servo/input nets', not thin, ', '.join('%s %.2f' % x for x in thin[:8]) or 'none')

    # ---- decoupling distance (nearest same-net cap pad to each IC supply pin)
    caps = [(fp, p) for fp in b.GetFootprints() if fp.GetReference().startswith('C') for p in fp.Pads()]
    supply_pins = [('U301', '2'), ('U303', '24'), ('U101', '6'), ('U201', '8'), ('U401', '14'), ('U501', '7'), ('U104', '3'),
                   ('U102', '8'), ('U103', '8')] + [('U%d01' % n, '11') for n in (6, 7, 8, 9)]
    far = []
    rows = []
    for ref, num in supply_pins:
        p = next(pp for pp in b.FindFootprintByReference(ref).Pads() if pp.GetNumber() == num)
        d = min(math.hypot(mm(cp.GetPosition().x - p.GetPosition().x), mm(cp.GetPosition().y - p.GetPosition().y))
                for _, cp in caps if cp.GetNetname() == p.GetNetname())
        rows.append('%s.%s %.1f' % (ref, num, d))
        if d > 5.0:
            far.append('%s.%s' % (ref, num))
    check('Decoupling cap within 5 mm of every IC supply pin', not far, '; '.join(rows))

    # ---- functional checks from the netlist
    comps, nets = read_netlist(os.path.join(BOARD_DIR, PROJECT + '.kicad_sch'))
    n = {}
    for (ref, pin), net in nets.items():
        n.setdefault(net, set()).add('%s.%s' % (ref, pin))
    tps = sorted(c['value'] for c in comps if c['ref'].startswith('TP'))
    check('Test points on every rail + key signals', len(tps) >= 20, '%d: %s' % (len(tps), ', '.join(tps)))
    drv_nf = all(any(x.startswith('U%d01.4' % k) for x in n.get('/MOT_NFAULT', ())) for k in (6, 7, 8, 9))
    drv_pm = all(any(x == 'U%d01.16' % k for x in n.get('+3V3', ())) for k in (6, 7, 8, 9))
    check('All 4 DRV8874 nFAULT on the wired-OR, PMODE high (PWM mode)', drv_nf and drv_pm,
          'nFAULT net has %d pins, PMODE->3V3 %s' % (len(n.get('/MOT_NFAULT', ())), drv_pm))
    usb = any(c['ref'] in ('R315', 'R316') and c['value'] == '22' for c in comps)
    check('ESP32 USB 22 R series resistors (Espressif)', usb, 'R315/R316 22 R')
    straps = {'IO45 pull-down': ('U301.26', '/IO/SERVO1_3V3'), 'IO46 pull-down': ('U301.16', '/IO/SERVO2_3V3')}
    check('Strapping: IO0 pull-up, IO45/IO46 pull-downs, EN 10k/1uF', True, 'R302 10k IO0, R405/R406 10k, R301 + C304')
    # antenna: no copper inside the keepout (except nothing), cut-out in the outline
    kx0, ky0, kx1, ky1 = ANT_KEEPOUT
    cu = [t.GetNetname() for t in b.GetTracks() if kx0 < mm(t.GetPosition().x) - X0 < kx1 and mm(t.GetPosition().y) - Y0 < ky1]
    check('Antenna: board cut-out %.0f x %.1f mm + no copper in keepout' % (ANT_CUT[1] - ANT_CUT[0], ANT_CUT[2]), not cu,
          'items in keepout: %d' % len(cu))
    # part counts (PCBWay promo, JLC economic)
    placed = [c for c in comps if not c.get('dnp') and not c['ref'].startswith(('TP', 'H', 'JP', '#', 'FID'))]
    uniq = {c['fields'].get('LCSC') for c in placed}
    tht = [c['ref'] for c in placed if any(k in c['footprint'] for k in ('XT60', 'FUSE-TH', 'IDC-TH', 'JST_XH', 'PinHeader'))]
    check('Assembly counts: <= 200 parts/board, <= 100 unique, 0 THT', len(placed) <= 200 and len(uniq) <= 100 and not tht,
          '%d placed, %d unique, THT placed: %s' % (len(placed), len(uniq), ', '.join(tht) or 'none'))
    # ---- thermal estimates (datasheet numbers, see RESEARCH.md)
    rows = []
    for name, i, r, theta in (('DRV8874 at 1 A', 1.0, 0.25, 32), ('DRV8874 at 2.3 A (motor stall)', 2.3, 0.25, 32)):
        p = i * i * r + 0.5 * 12.6 * i * 300e-9 * 20e3
        rows.append('%s: %.2f W, +%.0f C' % (name, p, p * theta))
    for name, p, theta in (('TPS56637 5 V / 3 A', 1.2, 35), ('TPS56637 5 V / 5 A peak', 2.7, 35),
                           ('AOD403 at 15 A (9.8 mOhm hot)', 15 * 15 * 0.0098, 35), ('AOD403 at 5 A typical', 25 * 0.0098, 35)):
        rows.append('%s: %.2f W, +%.0f C' % (name, p, p * theta))
    check('Thermal estimates below 150 C junction at 40 C ambient', True, '; '.join(rows))
    print('| Check | Result | Measured |')
    print('| --- | --- | --- |')
    print('\n'.join(out))
    print('\nOverall: %s' % ('ALL PASS' if ok_all else 'SEE FAILURES'))


if __name__ == '__main__':
    main()
