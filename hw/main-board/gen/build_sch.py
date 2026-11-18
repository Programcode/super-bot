"""Regenerate lib/sbot.kicad_sym, the hierarchical schematic and main-board.kicad_pro.

Usage: ~/tools/kicad-mcp-server/.venv/bin/python gen/build_sch.py   (from hw/main-board)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BOARD = os.path.dirname(HERE)

import symbols                      # noqa: E402
from schgen import Libs, Writer     # noqa: E402
from design import build_design     # noqa: E402

PROJECT = 'main-board'


def project_file():
    tmpl = os.path.join(BOARD, '..', 'kicad-smoketest', 'kicad-smoketest.kicad_pro')
    d = json.load(open(tmpl))
    d['meta']['filename'] = PROJECT + '.kicad_pro'
    rules = d['board']['design_settings']['rules']
    # JLCPCB 4-layer standard capability, with margin
    rules.update({'min_clearance': 0.15, 'min_track_width': 0.1, 'min_via_diameter': 0.45,
                  'min_through_hole_diameter': 0.3, 'min_via_annular_width': 0.1, 'min_hole_clearance': 0.25,
                  'min_hole_to_hole': 0.25, 'min_copper_edge_clearance': 0.25, 'min_text_height': 0.8,
                  'min_silk_clearance': 0.0, 'min_resolved_spokes': 1})
    base = dict(d['net_settings']['classes'][0])
    base.update({'clearance': 0.15, 'track_width': 0.2, 'via_diameter': 0.6, 'via_drill': 0.3})
    classes = [base]

    def nc(name, width, clr, via=0.8, drill=0.4, prio=0):
        c = dict(base)
        c.update({'name': name, 'track_width': width, 'clearance': clr, 'via_diameter': via, 'via_drill': drill,
                  'priority': prio})
        return c
    classes += [nc('HighCurrent', 1.2, 0.15, 0.8, 0.4, 0), nc('Motor', 1.0, 0.15, 0.8, 0.4, 1),
                nc('Supply', 0.4, 0.15, 0.6, 0.3, 2)]
    d['net_settings']['classes'] = classes
    pats = []
    # IPC-2221 widths: see README "Trace widths". Zones carry the 15 A input path; these are the routed minimums.
    for pat, cls in (('/Power/VBAT_IN', 'HighCurrent'), ('/Power/VBAT_F', 'HighCurrent'), ('/Power/VSW', 'HighCurrent'),
                     ('/Power/VPROT', 'HighCurrent'), ('VBUS', 'HighCurrent'), ('VMOT', 'HighCurrent'),
                     ('+5V', 'HighCurrent'), ('VSERVO', 'HighCurrent'), ('/Power/BUCK*_SW', 'Supply'),
                     ('/Motor*/OUT1', 'Motor'), ('/Motor*/OUT2', 'Motor'), ('/Power/LED_*', 'Default'),
                     ('GND', 'Supply'), ('+3V3', 'Supply'), ('V3V3_IN', 'Supply'), ('+5V_USB', 'Supply'),
                     ('/IO/SPK_*', 'Supply'), ('/Audio/SPK_*', 'Supply')):
        pats.append({'netclass': cls, 'pattern': pat})
    d['net_settings']['netclass_patterns'] = pats
    d['net_settings']['netclass_assignments'] = None
    d['sheets'] = []
    d['boards'] = []
    json.dump(d, open(os.path.join(BOARD, PROJECT + '.kicad_pro'), 'w'), indent=2)


def main():
    symbols.build(os.path.join(BOARD, 'lib', 'sbot.kicad_sym'))
    libs = Libs({'sbot': os.path.join(BOARD, 'lib', 'sbot.kicad_sym')})
    design = build_design(libs)
    w = Writer(design, BOARD, PROJECT)
    design.root_texts.append((30, 215, 'Super bot main board rev A: 4-layer, 1.6 mm, JLC04161H-7628.\n'
                              'Sheets: power input and rails, hardware motor cut, MCU, connectors, audio, 4x motor channel.\n'
                              'See hw/main-board/README.md for the block diagram, current calculations and open questions.', 2.0))
    w.write('Super bot main board: hierarchy')
    project_file()
    print('ok')


if __name__ == '__main__':
    main()
