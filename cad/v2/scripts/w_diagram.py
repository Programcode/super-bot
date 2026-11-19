# w_diagram.py (offline): block diagram of the v2 harness from review/wiring.json -> SVG.
# python3 -I w_diagram.py <wiring.json> <out.svg>
# Boxes = parts/modules, lines = cables (label = schedule id). Red = power, blue = data/signal, grey = FFC/stock.
import json, sys

N = {  # name: (x, y, w, h, group)
    'pack': (40, 520, 150, 60, 'Battery sled: pack 3S4P + BMS + 15 A fuse'),
    'charge': (40, 640, 150, 50, 'Charge jack + 5 A fuse + ideal diode'),
    'bulk': (250, 520, 120, 40, 'Bulkhead XT60 (blind mate)'),
    'key': (430, 620, 120, 40, 'XT60 loop key'),
    'pdb': (430, 500, 150, 60, 'PDB + INA226 (right cheek)'),
    'drv': (650, 600, 150, 60, '4x DRV8874 perfboard'),
    'buck5': (650, 420, 130, 40, '5 V buck D36V50F5'),
    'buck6': (650, 500, 130, 40, '6 V buck D36V28F6'),
    'esp': (880, 520, 140, 60, 'ESP32-S3 (cradle)'),
    'pi': (880, 300, 140, 70, 'Pi 5 + AI HAT+ 2'),
    'motors': (650, 720, 150, 50, '4x JGB37 + encoders'),
    'bump': (880, 720, 140, 40, '4x D2F-01L bumpers'),
    'cliff': (1080, 720, 140, 40, '4x VL53L0X cliff'),
    'imu': (1080, 600, 140, 36, 'BNO085'),
    'cpx': (1080, 480, 140, 44, 'CPX (light + watchdog)'),
    'servo': (650, 300, 130, 50, 'Pan + tilt MG90S (Y harness)'),
    'amp': (1080, 360, 140, 36, 'MAX98357A'),
    'spk': (1260, 360, 110, 36, 'Speaker 40 mm'),
    'lidar': (1080, 250, 140, 36, 'LD19 lidar'),
    'head': (880, 120, 140, 70, 'Head: Camera 3, TFT, INMP441'),
}
E = {  # cable id -> (from node, to node, kind)
    'S01': ('pack', 'pack', 'p'), 'S02': ('pack', 'pack', 'p'), 'S03': ('pack', 'pack', 'p'), 'S04': ('pack', 'bulk', 'p'), 'S05': ('pack', 'bulk', 'p'),
    'S06': ('charge', 'charge', 'p'), 'S07': ('charge', 'charge', 'p'), 'S08': ('charge', 'pack', 'p'), 'S09': ('charge', 'pack', 'p'),
    'F01': ('bulk', 'key', 'p'), 'F02': ('bulk', 'pdb', 'p'), 'F03': ('key', 'pdb', 'p'),
    'O01': ('pdb', 'drv', 'p'), 'O02': ('pdb', 'buck5', 'p'), 'O03': ('pdb', 'buck6', 'p'), 'P01': ('buck5', 'pi', 'p'),
    'U01': ('pi', 'esp', 'd'), 'G01': ('pi', 'lidar', 'd'), 'G02': ('pi', 'amp', 'd'), 'G03': ('pi', 'cpx', 'p'), 'G04': ('pi', 'head', 'd'), 'G05': ('pi', 'head', 'd'),
    'K01': ('pi', 'head', 'f'), 'MA': ('motors', 'drv', 'p'), 'L01': ('esp', 'drv', 'd'),
    'B01': ('bump', 'esp', 'd'), 'C01': ('cliff', 'esp', 'd'), 'C05': ('esp', 'imu', 'd'), 'C06': ('esp', 'pdb', 'd'),
    'W01': ('esp', 'cpx', 'd'), 'W02': ('cpx', 'drv', 'd'), 'V03': ('buck6', 'servo', 'p'), 'V04': ('esp', 'servo', 'd'), 'A01': ('amp', 'spk', 'p'),
}
GROUP = {'MA': 'MA-MD (x4, encoder wires on to the ESP32)', 'B01': 'B01-B04 (x4)', 'C01': 'C01-C04 (x4)'}
COL = {'p': '#d9483b', 'd': '#3b7dd9', 'f': '#8a8f98'}


def centre(n):
    x, y, w, h, _ = N[n]
    return x + w / 2, y + h / 2


def edge_pt(n, tx, ty):
    x, y, w, h, _ = N[n]
    cx, cy = x + w / 2, y + h / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    s = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return cx + dx * s, cy + dy * s


def main():
    data = json.load(open(sys.argv[1]))
    cut = {c['id']: (c['cut_mm'] or c.get('stock_len_mm')) for c in data['cables']}
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1420 800" font-family="Helvetica, Arial, sans-serif" font-size="12">',
           '<rect width="1420" height="800" fill="#ffffff"/>',
           '<text x="40" y="50" font-size="20" font-weight="bold" fill="#111">Super bot v2 harness (module layout, 19 Nov 2026)</text>',
           '<text x="40" y="72" fill="#444">Lines = cables, label = id in WIRING.md / review/wiring.json, with cut or stock length in mm. Red power, blue signal, grey FFC.</text>']
    seen = set()
    for cid, (a, b, k) in E.items():
        if a == b:
            continue
        ax, ay = centre(a)
        bx, by = centre(b)
        p1, p2 = edge_pt(a, bx, by), edge_pt(b, ax, ay)
        off = 0
        key = tuple(sorted((a, b)))
        while (key, off) in seen:
            off += 1
        seen.add((key, off))
        dx, dy = (p2[1] - p1[1]), -(p2[0] - p1[0])
        L = max((dx * dx + dy * dy) ** 0.5, 1)
        ox, oy = dx / L * 9 * off, dy / L * 9 * off
        x1, y1, x2, y2 = p1[0] + ox, p1[1] + oy, p2[0] + ox, p2[1] + oy
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2"/>' % (x1, y1, x2, y2, COL[k]))
        lab = GROUP[cid] if cid in GROUP else '%s %s' % (cid, cut.get(cid) or '')
        t = (0.5, 0.3, 0.7, 0.4)[off % 4]
        out.append('<text x="%.1f" y="%.1f" fill="%s" text-anchor="middle" font-size="11" paint-order="stroke" stroke="#fff" stroke-width="3">%s</text>'
                   % (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t - 3, COL[k], lab))
    for n, (x, y, w, h, t) in N.items():
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="#f4f5f7" stroke="#333" stroke-width="1.2"/>' % (x, y, w, h))
        words, lines, cur = t.split(), [], ''
        for wd in words:
            if len(cur + ' ' + wd) > w / 6.6:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + ' ' + wd).strip()
        lines.append(cur)
        for i, l in enumerate(lines):
            out.append('<text x="%.1f" y="%.1f" text-anchor="middle" fill="#111">%s</text>' % (x + w / 2, y + h / 2 - 7 * (len(lines) - 1) + 14 * i + 4, l))
    inside = [c for c, (a, b, k) in E.items() if a == b]
    out.append('<text x="40" y="780" fill="#444">Inside the battery sled / charge path (not drawn): %s. Spare: PDB XT30 out 4.</text>' % ', '.join(inside))
    out.append('</svg>')
    open(sys.argv[2], 'w').write('\n'.join(out))
    print('svg ok', len(E), 'cables')


main()
