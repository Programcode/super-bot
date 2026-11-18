"""Stage 3 of the board: silkscreen labels, reference visibility, stackup. Run after route.py.

Usage (from hw/main-board): ~/tools/kicad-mcp-server/.venv/bin/python gen/finish.py
"""
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pcblib import BOARD_DIR, MM   # noqa: E402
from build_pcb import X0, Y0, W, H   # noqa: E402

PCB = os.path.join(BOARD_DIR, 'main-board.kicad_pcb')

# connector label overrides (default: the symbol's Silk field); side: 'above' or 'below' the courtyard
LABELS = {
    'J601': ('MOTOR A  front-left', 'above'), 'J701': ('MOTOR B  front-right', 'above'),
    'J801': ('MOTOR C  rear-left', 'above'), 'J901': ('MOTOR D  rear-right', 'above'),
    'J101': ('BATTERY 12V', 'above'), 'J102': ('MAIN SWITCH LOOP', 'below'), 'J103': ('PI 5V OUT', 'below'),
    'J301': ('ESP32 USB', 'below'), 'J401': ('PI 5 GPIO (40-way ribbon)', 'below'),
    'J405': ('CLIFF F', 'below'), 'J406': ('CLIFF R', 'below'), 'J407': ('CLIFF B', 'below'), 'J408': ('CLIFF L', 'below'),
    'J409': ('QWIIC ESP', 'below'), 'J402': ('QWIIC PI', 'below'), 'J411': ('IMU', 'below'),
    'J410': ('BUMPERS F R B L', 'below'), 'J412': ('LED BAR', 'below'), 'J201': ('KILL LOOP', 'below'),
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
    t.SetTextThickness(int(MM(size * 0.16)))
    t.SetBold(bold)
    t.SetHorizJustify(just)
    board.Add(t)
    return t


def main():
    board = pcbnew.LoadBoard(PCB)
    for d in list(board.Drawings()):
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            board.Remove(d)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        lib = fp.GetFPID().GetLibNickname().wx_str() if hasattr(fp.GetFPID().GetLibNickname(), 'wx_str') else str(fp.GetFPID().GetLibNickname())
        r = fp.Reference()
        if lib in SMALL or ref.startswith('H') or ref.startswith('JP'):
            r.SetVisible(False)
        else:
            r.SetTextSize(pcbnew.VECTOR2I(int(MM(0.8)), int(MM(0.8))))
            r.SetTextThickness(int(MM(0.13)))
        silk = LABELS.get(ref)
        if silk is None and fp.HasField('Silk'):
            silk = (fp.GetFieldText('Silk'), 'below')
        if silk:
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False)
            cx = bb.Centre().x / 1e6 - X0
            y = (bb.GetTop() / 1e6 - Y0 - 0.9) if silk[1] == 'above' else (bb.GetBottom() / 1e6 - Y0 + 0.9)
            text(board, silk[0], cx, y, size=0.9)
    text(board, 'SUPER BOT  MAIN BOARD  rev A', 92.0, 35.5, size=1.3)
    text(board, '2026-11  KiCad 10  JLC04161H-7628', 92.0, 37.6, size=0.9, bold=False)
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
