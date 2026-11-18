"""Netlist -> board helpers (pcbnew SWIG, KiCad 10)."""
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sexpr import parse, find, find1   # noqa: E402

BOARD_DIR = os.path.dirname(HERE)
PROJECT = 'main-board-rev-b'
KFP = '/usr/share/kicad/footprints'
MM = pcbnew.FromMM


def lib_path(lib):
    if lib == 'sbot':
        return os.path.join(BOARD_DIR, 'lib', 'sbot.pretty')
    return os.path.join(KFP, lib + '.pretty')


def read_netlist(sch):
    out = '/tmp/sbpcb/board.net'
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, sch],
                   check=True, capture_output=True)
    n = parse(open(out).read())
    comps = []
    for c in find(find1(n, 'components'), 'comp'):
        d = {'ref': str(find1(c, 'ref')[1]), 'value': str(find1(c, 'value')[1]),
             'footprint': str(find1(c, 'footprint')[1]) if find1(c, 'footprint') else ''}
        sp = find1(c, 'sheetpath')
        d['sheetname'] = str(find1(sp, 'names')[1])
        d['path'] = str(find1(sp, 'tstamps')[1]) + str(find1(c, 'tstamps')[1])
        d['fields'] = {}
        fl = find1(c, 'fields')
        if fl:
            for f in find(fl, 'field'):
                nm = str(find1(f, 'name')[1])
                d['fields'][nm] = str(f[2]) if len(f) > 2 else ''
        for p in find(c, 'property'):
            nm = str(find1(p, 'name')[1])
            v = find1(p, 'value')
            if nm == 'dnp':
                d['dnp'] = True
            if nm == 'exclude_from_bom':
                d['exclude_from_bom'] = True
            if v is not None and nm in ('Sheetfile',):
                d['sheetfile'] = str(v[1])
        comps.append(d)
    nets = {}
    for net in find(find1(n, 'nets'), 'net'):
        name = str(find1(net, 'name')[1])
        for nd in find(net, 'node'):
            nets[(str(find1(nd, 'ref')[1]), str(find1(nd, 'pin')[1]))] = name
    return comps, nets


def load_fp(fpid, cache={}):
    lib, name = fpid.split(':', 1)
    key = (lib, name)
    if key not in cache:
        fp = pcbnew.FootprintLoad(lib_path(lib), name)
        if fp is None:
            raise RuntimeError('footprint not found: ' + fpid)
        cache[key] = fp
    return pcbnew.FOOTPRINT(cache[key])


def courtyard_bbox(fp):
    """Courtyard bbox (front or back) in board coords; falls back to the footprint bbox."""
    for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        try:
            poly = fp.GetCourtyard(layer)
            if poly.OutlineCount():
                return poly.BBox()
        except Exception:
            pass
    return fp.GetBoundingBox(False)
