"""Stage 2b helper: free trapped pads by ripping up nearby unlocked (autorouted) copper of other nets.

Usage: ~/tools/kicad-mcp-server/.venv/bin/python gen/ripup.py [board] [radius_mm]
Prints the trapped nets (route these first with gen/fixup.py --first ...). Removal is done on the file text by UUID,
because pcbnew's Python API is unreliable after BOARD.Remove().
"""
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv += [] if len(sys.argv) > 1 else []
import fixup   # noqa: E402

PROJECT = 'main-board-rev-b'
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), PROJECT + '.kicad_pcb')
R = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5


def main():
    b = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    c = b.GetConnectivity()
    nets = sorted({p.GetNetname() for f in b.GetFootprints() for p in f.Pads()})
    trapped, rip = [], set()
    r = pcbnew.FromMM(R)
    tracks = list(b.GetTracks())
    for net in nets:
        if not net or net.startswith('unconnected') or net.startswith('Net-'):
            continue
        cl = fixup.clusters(b, c, net)
        if len(cl) < 2:
            continue
        trapped.append(net)
        for g in sorted(cl, key=len)[:-1]:
            for it in g:
                if not isinstance(it, pcbnew.PAD):
                    continue
                bb = it.GetBoundingBox()
                for t in tracks:
                    if t.GetNetname() == net or t.IsLocked():
                        continue
                    tb = t.GetBoundingBox()
                    if tb.GetLeft() < bb.GetRight() + r and tb.GetRight() > bb.GetLeft() - r and \
                            tb.GetTop() < bb.GetBottom() + r and tb.GetBottom() > bb.GetTop() - r:
                        rip.add(t.m_Uuid.AsString())
    txt = open(PCB).read()
    n = 0
    for u in rip:
        # (segment ... (uuid "u") ...) or (via ... (uuid "u") ...) blocks: find the enclosing block
        i = txt.find('"%s"' % u)
        if i < 0:
            continue
        start = max(txt.rfind('\n\t(segment', 0, i), txt.rfind('\n\t(via', 0, i), txt.rfind('\n\t(arc', 0, i))
        depth, j = 0, start + 1
        while True:
            if txt[j] == '(':
                depth += 1
            elif txt[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        txt = txt[:start] + txt[j + 1:]
        n += 1
    open(PCB, 'w').write(txt)
    print('ripped %d items around trapped pads' % n)
    print('TRAPPED=' + ','.join(trapped))


if __name__ == '__main__':
    main()
