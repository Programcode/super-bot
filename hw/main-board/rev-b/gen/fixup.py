"""Stage 2b: route the few connections Freerouting leaves open, with a small grid A* router (F.Cu/B.Cu + vias).

Usage (from hw/main-board): ~/tools/kicad-mcp-server/.venv/bin/python gen/fixup.py
Items it adds are ordinary tracks/vias; run kicad-check afterwards.
"""
import heapq
import math
import os
import sys

import numpy as np
import pcbnew
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pcblib import BOARD_DIR, MM, PROJECT   # noqa: E402
from build_pcb import X0, Y0, W, H, NOTCH, ANT_KEEPOUT   # noqa: E402

PCB = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.path.join(BOARD_DIR, PROJECT + '.kicad_pcb')
RES = 0.05                      # mm per cell
NX, NY = int(W / RES) + 1, int(H / RES) + 1
CLR = 0.18                      # clearance used by this router (board rule 0.15 + raster margin)
INNER = '--inner' in sys.argv
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu) if INNER else (pcbnew.F_Cu, pcbnew.B_Cu)
WIDE = {'+5V': 0.3, 'VSERVO': 0.3, 'VBUS': 0.3, 'VMOT': 0.3, '+3V3': 0.15, 'GND': 0.15, 'V3V3_IN': 0.2, '+5V_USB': 0.2}


def to_cell(x_nm, y_nm):
    return int(round((x_nm / 1e6 - X0) / RES)), int(round((y_nm / 1e6 - Y0) / RES))


def to_nm(cx, cy):
    return int(MM(X0 + cx * RES)), int(MM(Y0 + cy * RES))


class Grid:
    def __init__(self, board, width):
        self.board = board
        self.width = width
        self.owner = [np.zeros((NY, NX), np.int32) for _ in LAYERS]
        self.nl = len(LAYERS)
        self.pour_marks = []     # (layer index, mask, net) of F/B power pours, so vias can ignore them   # 0 free, >0 net code, -1 blocked
        self.infl = (CLR + width / 2)
        self._build()

    def mark(self, layer_i, m, net):
        """m = (x0, y0, bool array) window in cells."""
        x0, y0, sub = m
        if sub is None:
            return
        h, w = sub.shape
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(NX, x0 + w), min(NY, y0 + h)
        if xb <= xa or yb <= ya:
            return
        sub = sub[ya - y0:yb - y0, xa - x0:xb - x0]
        o = self.owner[layer_i][ya:yb, xa:xb]
        cur = o[sub]
        o[sub] = np.where((cur == 0) | (cur == net), net, -1)

    def _window(self, xs, ys, grow):
        x0 = int(math.floor(((min(xs) - grow) - X0) / RES)) - 1
        y0 = int(math.floor(((min(ys) - grow) - Y0) / RES)) - 1
        x1 = int(math.ceil(((max(xs) + grow) - X0) / RES)) + 2
        y1 = int(math.ceil(((max(ys) + grow) - Y0) / RES)) + 2
        return x0, y0, max(1, x1 - x0), max(1, y1 - y0)

    def poly_mask(self, pts_mm, grow):
        if len(pts_mm) < 3:
            return (0, 0, None)
        xs, ys = [p[0] for p in pts_mm], [p[1] for p in pts_mm]
        x0, y0, w, h = self._window(xs, ys, grow)
        img = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(img)
        d.polygon([((x - X0) / RES - x0, (y - Y0) / RES - y0) for x, y in pts_mm], fill=1)
        r = grow / RES
        # grow: draw thick outline as well (approximates a Minkowski sum with a disk)
        pts = [((x - X0) / RES - x0, (y - Y0) / RES - y0) for x, y in pts_mm]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            d.line([a, b], fill=1, width=max(1, int(round(2 * r))))
            d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=1)
        return (x0, y0, np.array(img, bool))

    def seg_mask(self, a, b, half):
        x0, y0, w, h = self._window([a[0], b[0]], [a[1], b[1]], half)
        img = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(img)
        r = half / RES
        ax, ay = (a[0] - X0) / RES - x0, (a[1] - Y0) / RES - y0
        bx, by = (b[0] - X0) / RES - x0, (b[1] - Y0) / RES - y0
        d.line([(ax, ay), (bx, by)], fill=1, width=max(1, int(round(2 * r))))
        d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=1)
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=1)
        return (x0, y0, np.array(img, bool))

    def _build(self):
        b = self.board
        g = self.infl
        # board edge, notch, antenna keepout: blocked everywhere
        for i in range(len(LAYERS)):
            o = self.owner[i]
            m = int(math.ceil((0.3 + self.width / 2) / RES))
            o[:m, :] = -1
            o[-m:, :] = -1
            o[:, :m] = -1
            o[:, -m:] = -1
            nx0, nx1, ny0, ny1 = NOTCH
            o[:int((ny1 + 0.3 + self.width / 2) / RES) + 1, int((nx0 - 0.3 - self.width / 2) / RES):int((nx1 + 0.3 + self.width / 2) / RES) + 1] = -1
            kx0, ky0, kx1, ky1 = ANT_KEEPOUT
            o[int(ky0 / RES):int(ky1 / RES) + 1, int(kx0 / RES):int(kx1 / RES) + 1] = -1
        for fp in b.GetFootprints():
            for p in fp.Pads():
                net = p.GetNetCode() or -1
                poly = p.GetEffectivePolygon(pcbnew.F_Cu, pcbnew.ERROR_INSIDE)
                pts = [(poly.CVertex(k).x / 1e6, poly.CVertex(k).y / 1e6) for k in range(poly.FullPointCount())]
                mask = self.poly_mask(pts, g)
                for i, L in enumerate(LAYERS):
                    if p.IsOnLayer(L):
                        self.mark(i, mask, net)
                if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    for i in range(len(LAYERS)):
                        self.mark(i, mask, net)
        for t in b.GetTracks():
            net = t.GetNetCode() or -1
            if t.Type() == pcbnew.PCB_VIA_T:
                c = t.GetPosition()
                r = t.GetWidth(pcbnew.F_Cu) / 2e6 + g
                mask = self.seg_mask((c.x / 1e6, c.y / 1e6), (c.x / 1e6, c.y / 1e6), r)
                for i in range(len(LAYERS)):
                    self.mark(i, mask, net)
            else:
                if t.GetLayer() not in LAYERS:
                    continue
                i = LAYERS.index(t.GetLayer())
                s, e = t.GetStart(), t.GetEnd()
                mask = self.seg_mask((s.x / 1e6, s.y / 1e6), (e.x / 1e6, e.y / 1e6), t.GetWidth() / 2e6 + g)
                self.mark(i, mask, net)
        for z in b.Zones():
            if z.GetIsRuleArea():
                continue
            for i, L in enumerate(LAYERS):
                # GND fill and In2 planes refill around new copper. F.Cu power pours too: each has a stitched twin on
                # B.Cu, so a signal track may cut the F.Cu copy (current continues on B.Cu); B.Cu pours stay obstacles.
                if L == pcbnew.In2_Cu or not z.IsOnLayer(L) or z.GetNetname() == 'GND' or \
                        (L == pcbnew.F_Cu and z.GetZoneName().endswith(' pour') and '--cut-pours' in sys.argv):
                    continue     # GND pours refill around new copper
                fp = z.GetFilledPolysList(L)
                for k in range(fp.OutlineCount()):
                    ol = fp.Outline(k)
                    pts = [(ol.CPoint(j).x / 1e6, ol.CPoint(j).y / 1e6) for j in range(ol.PointCount())]
                    m_ = self.poly_mask(pts, g)
                    self.pour_marks.append((i, m_, z.GetNetCode()))

    def free(self, i, net, pours=True):
        if pours and self.pour_marks and not hasattr(self, '_withpours'):
            # build the with-pours owner arrays once (pour_marks applied on a copy)
            self._nopour = [o.copy() for o in self.owner]
            for li, m_, nc in self.pour_marks:
                self.mark(li, m_, nc)
            self._withpours = True
        if not pours:
            o = self._nopour[i] if hasattr(self, '_nopour') else self.owner[i]
        else:
            o = self.owner[i]
        return (o == 0) | (o == net)


def dilate(m, r):
    if r <= 0:
        return m
    out = m.copy()
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return m
    y0, y1 = max(0, ys.min() - r), min(NY, ys.max() + r + 1)
    x0, x1 = max(0, xs.min() - r), min(NX, xs.max() + r + 1)
    sub = m[y0:y1, x0:x1]
    acc = sub.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r:
                continue
            acc |= np.roll(np.roll(sub, dy, 0), dx, 1)
    out[y0:y1, x0:x1] = acc
    return out


def astar(grid, net, starts, goals, via_r):
    free = [grid.free(i, net) for i in range(len(LAYERS))]
    vfree = [grid.free(i, net, pours=False) for i in range(2)]
    vr = int(math.ceil(via_r / RES))
    goal_l = {(c[2], c[0], c[1]) for c in goals}
    tx = sum(c[0] for c in goals) / len(goals)
    ty = sum(c[1] for c in goals) / len(goals)
    openh = []
    best = {}
    for (x, y, l) in starts:
        if free[l][y, x]:
            heapq.heappush(openh, (0, 0, l, x, y))
            best[(l, x, y)] = 0
    prev = {}
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    lcost = [1.0, 1.15, 3.0]
    n = 0
    while openh:
        f, gcost, l, x, y = heapq.heappop(openh)
        if (l, x, y) in goal_l:
            path = [(l, x, y)]
            k = (l, x, y)
            while k in prev:
                k = prev[k]
                path.append(k)
            return path[::-1]
        n += 1
        if n > 6000000:
            return None
        if best.get((l, x, y), 1e18) < gcost:
            continue
        for dx, dy, c in moves:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < NX and 0 <= ny < NY) or not free[l][ny, nx]:
                continue
            ng = gcost + c * lcost[l]
            k = (l, nx, ny)
            if ng < best.get(k, 1e18):
                best[k] = ng
                prev[k] = (l, x, y)
                heapq.heappush(openh, (ng, ng, l, nx, ny))
        # through via: must be free on every copper layer it crosses (In1 is GND plane: antipad, fine)
        ok = True
        for dy in range(-vr, vr + 1, max(1, vr)):
            for dx in range(-vr, vr + 1, max(1, vr)):
                yy, xx = y + dy, x + dx
                if not (0 <= xx < NX and 0 <= yy < NY) or not all(fr[yy, xx] for fr in vfree):
                    ok = False
        if ok:
            for ol in range(len(LAYERS)):
                if ol == l or not (free[ol][y, x] or (ol < 2 and vfree[ol][y, x])):
                    continue
                ng = gcost + 25
                k = (ol, x, y)
                if ng < best.get(k, 1e18):
                    best[k] = ng
                    prev[k] = (l, x, y)
                    heapq.heappush(openh, (ng, ng, ol, x, y))
    return None


def pad_cells(p):
    bb = p.GetBoundingBox()
    x0, y0 = to_cell(bb.GetLeft(), bb.GetTop())
    x1, y1 = to_cell(bb.GetRight(), bb.GetBottom())
    cx, cy = to_cell(p.GetPosition().x, p.GetPosition().y)
    cells = []
    for i, L in enumerate(LAYERS):
        if (p.IsOnLayer(L) and L != pcbnew.In2_Cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            for x in range(max(x0, cx - 2), min(x1, cx + 2) + 1):
                for y in range(max(y0, cy - 2), min(y1, cy + 2) + 1):
                    cells.append((x, y, i))
    return cells


def item_cells(it):
    if isinstance(it, pcbnew.PAD):
        return pad_cells(it)
    if it.Type() == pcbnew.PCB_VIA_T:
        x, y = to_cell(it.GetPosition().x, it.GetPosition().y)
        return [(x, y, i) for i in range(len(LAYERS))]
    if it.Type() == pcbnew.PCB_TRACE_T and it.GetLayer() in LAYERS:
        i = LAYERS.index(it.GetLayer())
        s, e = it.GetStart(), it.GetEnd()
        a, b = to_cell(s.x, s.y), to_cell(e.x, e.y)
        n = max(abs(a[0] - b[0]), abs(a[1] - b[1]), 1)
        return [(round(a[0] + (b[0] - a[0]) * k / n), round(a[1] + (b[1] - a[1]) * k / n), i) for k in range(n + 1)]
    return []


def clusters(board, c, net):
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    groups = []
    seen = set()
    for p in pads:
        key = (p.GetParentFootprint().GetReference(), p.GetNumber(), p.GetPosition().x, p.GetPosition().y)
        if key in seen:
            continue
        items = [p] + [i for i in c.GetConnectedItems(p) if isinstance(i, (pcbnew.PAD, pcbnew.PCB_TRACK, pcbnew.PCB_VIA))]
        g = []
        for it in items:
            if isinstance(it, pcbnew.PAD):
                k = (it.GetParentFootprint().GetReference(), it.GetNumber(), it.GetPosition().x, it.GetPosition().y)
                seen.add(k)
            g.append(it)
        groups.append(g)
    return groups


def add_path(board, net, path, width):
    ni = board.FindNet(net)
    # collapse into straight runs
    pts = [path[0]]
    for k in range(1, len(path) - 1):
        a, b, c = pts[-1], path[k], path[k + 1]
        if a[0] == b[0] == c[0] and (b[1] - a[1]) * (c[2] - b[2]) == (b[2] - a[2]) * (c[1] - b[1]):
            continue
        pts.append(b)
    pts.append(path[-1])
    for a, b in zip(pts, pts[1:]):
        if a[0] != b[0]:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(*to_nm(a[1], a[2])))
            v.SetWidth(int(MM(0.6)))
            v.SetDrill(int(MM(0.3)))
            v.SetNet(ni)
            board.Add(v)
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(*to_nm(a[1], a[2])))
        t.SetEnd(pcbnew.VECTOR2I(*to_nm(b[1], b[2])))
        t.SetWidth(int(MM(width)))
        t.SetLayer(LAYERS[a[0]])
        t.SetNet(ni)
        board.Add(t)


def main():
    board = pcbnew.LoadBoard(PCB)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    c = board.GetConnectivity()
    todo = []
    for net in sorted({p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}):
        if not net or net.startswith('unconnected') or net.startswith('Net-'):
            continue
        g = clusters(board, c, net)
        if len(g) > 1:
            todo.append((net, len(g)))
    first = []
    for a in sys.argv:
        if a.startswith('--first='):
            first = a.split('=', 1)[1].split(',')
    todo.sort(key=lambda t: (0 if t[0] in first else 1, t[0]))
    print('nets with open connections:', todo)
    done, failed = [], []
    for net, _ in todo:
        width = WIDE.get(net, 0.15)
        skip = set()
        for attempt in range(12):
            board.BuildConnectivity()
            c = board.GetConnectivity()
            g = clusters(board, c, net)
            if len(g) < 2:
                break
            grid = Grid(board, width)
            code = board.FindNet(net).GetNetCode()
            g.sort(key=len)
            # connect the smallest cluster not yet known to be trapped to the rest
            def ckey(gg):
                return tuple(sorted('%s.%s' % (i.GetParentFootprint().GetReference(), i.GetNumber())
                                    for i in gg if isinstance(i, pcbnew.PAD))) or ('track', len(gg))
            cand = [k for k in range(len(g) - 1) if ckey(g[k]) not in skip]
            if not cand:
                failed.append(net)
                break
            k = cand[0]
            src = [cell for it in g[k] for cell in item_cells(it)]
            dst = [cell for j, gg in enumerate(g) if j != k for it in gg for cell in item_cells(it)]
            if INNER:
                # the net's own filled In2 plane is a target too (reach it through a via)
                for z in board.Zones():
                    if z.GetIsRuleArea() or z.GetNetname() != net or not z.IsOnLayer(pcbnew.In2_Cu):
                        continue
                    fpl = z.GetFilledPolysList(pcbnew.In2_Cu)
                    bbx = fpl.BBox()
                    x0c, y0c = to_cell(bbx.GetLeft(), bbx.GetTop())
                    x1c, y1c = to_cell(bbx.GetRight(), bbx.GetBottom())
                    for cy_ in range(max(0, y0c), min(NY, y1c), 3):
                        for cx_ in range(max(0, x0c), min(NX, x1c), 3):
                            X, Y = to_nm(cx_, cy_)
                            if fpl.Contains(pcbnew.VECTOR2I(X, Y)):
                                dst.append((cx_, cy_, 2))
            path = astar(grid, code, src, dst, 0.3 + CLR + 0.05)
            if not path:
                skip.add(ckey(g[k]))
                continue
            add_path(board, net, path, width)
            done.append(net)
        filler.Fill(board.Zones())
    board.Save(PCB)
    print('routed:', done)
    print('failed:', failed)


if __name__ == '__main__':
    main()
