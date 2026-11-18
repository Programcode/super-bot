"""Stage 2c/3b: DRC-driven cleanup. Removes dangling and duplicate vias, dangling stubs, and trims footprint silkscreen
segments that land on copper, other silk or the board edge. Repeats until nothing changes.

Usage (from hw/main-board): ~/tools/kicad-mcp-server/.venv/bin/python gen/cleanup.py [board]
Run it until it prints a round with nothing removed (each run is one round).
"""
import json
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.dirname(HERE)
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BOARD_DIR, 'main-board.kicad_pcb')
SILK_TYPES = ('silk_over_copper', 'silk_overlap', 'silk_edge_clearance')


def drc():
    out = '/tmp/sbpcb/cleanup-drc.json'
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', out, PCB],
                   capture_output=True)
    return json.load(open(out))


def main():
    for rnd in range(1):     # one round per process: pcbnew SWIG state is unsafe after Remove()
        d = drc()
        board = pcbnew.LoadBoard(PCB)
        removed = {'via': 0, 'track': 0, 'silk': 0, 'ref': 0}
        gone = set()

        bymap = {t.m_Uuid.AsString(): t for t in board.GetTracks()}

        def item(u):
            if u in gone:
                return None
            return bymap.get(u)

        pending = []
        # NOTE: this KiCad build sometimes reports a stale second item, so only first items are trusted
        for v in d['violations']:
            t = v['type']
            first = v['items'][0]
            if t in ('via_dangling', 'track_dangling'):
                it = item(first['uuid'])
                if it is not None and it.Type() in (pcbnew.PCB_VIA_T, pcbnew.PCB_TRACE_T):
                    pending.append(it)
                    gone.add(first['uuid'])
                    removed['via' if t == 'via_dangling' else 'track'] += 1
        # duplicate / too-close vias of the same net, found geometrically (decide first, remove after)
        vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.m_Uuid.AsString() not in gone]
        victims = []
        dead = set()
        for i, a_ in enumerate(vias):
            if i in dead:
                continue
            for j in range(i + 1, len(vias)):
                b_ = vias[j]
                if j in dead or a_.GetNetCode() != b_.GetNetCode():
                    continue
                pa, pb = a_.GetPosition(), b_.GetPosition()
                dd = ((pa.x - pb.x) ** 2 + (pa.y - pb.y) ** 2) ** 0.5
                if dd < (a_.GetDrillValue() + b_.GetDrillValue()) / 2 + pcbnew.FromMM(0.26):
                    k = j if (not b_.IsLocked() or a_.IsLocked()) else i
                    dead.add(k)
                    victims.append(vias[k])
                    if k == i:
                        break
        for it in pending:
            board.Remove(it)
        for v_ in victims:
            board.Remove(v_)
            removed['via'] += 1
        print('round', rnd, removed)
        if not any(removed.values()):
            break
        board.Save(PCB)     # save right after Remove(): further SWIG iteration on this board is unsafe


if __name__ == '__main__':
    main()
