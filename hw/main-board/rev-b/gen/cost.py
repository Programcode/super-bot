"""BOM stock check + cost estimate for N assembled boards (python3 gen/cost.py [boards]).

Prices and stock come from the local JLC catalog snapshot (~/.local/share/kicad-mcp/jlcpcb_parts.db) and, for parts
the snapshot lacks, the live LCSC product API. Assumptions for the PCB and assembly fees are listed in ASSUME.
"""
import json
import os
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sexpr import parse, find, find1   # noqa: E402

BOARD_DIR = os.path.dirname(HERE)
PROJECT = 'main-board-rev-b'
DB = os.path.expanduser('~/.local/share/kicad-mcp/jlcpcb_parts.db')
USD_EUR = 0.92
ASSUME = {
    'pcb_usd': 32.0,          # 5x 186x70 mm 4-layer 1.6 mm, HASL lead-free, JLC04161H-7628 (JLC quote estimate, check online)
    'setup_usd': 25.0,        # standard PCBA setup ($25 incl. stencil) for one side
    'smt_joint_usd': 0.0017,
    'tht_joint_usd': 0.0173,  # hand-soldered through-hole joints
    'ext_fee_usd': 3.0,       # per unique Extended part (Basic and Preferred are free)
    'shipping_usd': 20.0,     # DHL/consolidated estimate to Hungary, excl. VAT/customs
}


def components():
    out = '/tmp/sbpcb/cost.net'
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out,
                    os.path.join(BOARD_DIR, PROJECT + '.kicad_sch')], check=True, capture_output=True)
    n = parse(open(out).read())
    comps = []
    for c in find(find1(n, 'components'), 'comp'):
        fields = {}
        fl = find1(c, 'fields')
        if fl:
            for f in find(fl, 'field'):
                fields[str(find1(f, 'name')[1])] = str(f[2]) if len(f) > 2 else ''
        props = {str(find1(p, 'name')[1]) for p in find(c, 'property')}
        comps.append({'ref': str(find1(c, 'ref')[1]), 'value': str(find1(c, 'value')[1]),
                      'fp': str(find1(c, 'footprint')[1]) if find1(c, 'footprint') else '',
                      'lcsc': fields.get('LCSC', ''), 'dnp': 'dnp' in props, 'nobom': 'exclude_from_bom' in props})
    return comps


def live(lcsc):
    try:
        raw = subprocess.run(['curl', '-s', '-m', '15', 'https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=' + lcsc],
                             capture_output=True, text=True).stdout
        d = json.loads(raw)['result']
        ladder = [{'qty': p['ladder'], 'price': float(p['productPrice'])} for p in d['productPriceList']]
        return {'mfr': d['productModel'], 'stock': d['stockNumber'], 'type': 'Extended (live LCSC)', 'price': ladder,
                'joints': None}
    except Exception as e:
        return None


def price_at(ladder, q):
    best = ladder[0]['price']
    for step in ladder:
        if q >= step['qty']:
            best = step['price']
    return best


def main():
    boards = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    db = sqlite3.connect(DB)
    lines = {}
    kit = {}
    for c in components():
        if c['nobom'] or not c['lcsc']:
            continue
        if c['dnp']:
            if not c['ref'].startswith('R'):        # optional sonar divider stays unpopulated
                kit.setdefault(c['lcsc'], []).append(c)
            continue
        lines.setdefault(c['lcsc'], []).append(c)
    rows, parts_usd, ext, smt_j, tht_j, problems = [], 0.0, 0, 0, 0, []
    for lcsc, cs in sorted(lines.items(), key=lambda kv: kv[1][0]['ref']):
        r = db.execute('select mfr_part, stock, library_type, price_json, solder_joints from components where lcsc=?', (lcsc,)).fetchone()
        if r:
            info = {'mfr': r[0], 'stock': r[1], 'type': r[2], 'price': json.loads(r[3]), 'joints': r[4]}
        else:
            info = live(lcsc)
            if info is None:
                problems.append('%s not found anywhere' % lcsc)
                continue
        qty = len(cs) * boards
        unit = price_at(info['price'], qty)
        cost = unit * qty
        parts_usd += cost
        if info['type'].startswith('Extended'):
            ext += 1
        tht = any(k in cs[0]['fp'] for k in ('XT60', 'XT30', 'FUSE-TH', 'IDC-TH', 'JST_XH', 'PinHeader'))
        joints = info['joints'] or 2
        if tht:
            tht_j += joints * len(cs)
        else:
            smt_j += joints * len(cs)
        if info['stock'] < qty * 2:
            problems.append('%s %s stock %d < 2x need %d' % (lcsc, info['mfr'], info['stock'], qty))
        rows.append((lcsc, info['mfr'], info['type'], info['stock'], len(cs), unit, cost, ' '.join(c['ref'] for c in cs)))
    a = ASSUME
    asm = a['setup_usd'] + boards * (smt_j * a['smt_joint_usd'] + tht_j * a['tht_joint_usd'])
    fees = ext * a['ext_fee_usd']
    total = a['pcb_usd'] + parts_usd + asm + fees + a['shipping_usd']
    print('%-10s %-26s %-22s %8s %4s %8s %8s  %s' % ('LCSC', 'MPN', 'JLC type', 'stock', 'qty', 'unit$', 'total$', 'refs'))
    for row in rows:
        print('%-10s %-26s %-22s %8d %4d %8.4f %8.2f  %s' % (row[0], row[1][:26], row[2][:22], row[3], row[4], row[5], row[6], row[7][:60]))
    print()
    print('unique BOM lines %d, Extended %d, SMT joints/board %d, THT joints/board %d' % (len(rows), ext, smt_j, tht_j))
    summary = [('PCB (5x, 4-layer)', a['pcb_usd']), ('Parts', parts_usd), ('Assembly (setup + joints)', asm),
               ('Extended part fees', fees), ('Shipping (estimate)', a['shipping_usd'])]
    for k, v in summary:
        print('%-28s $%8.2f  EUR %8.2f' % (k, v, v * USD_EUR))
    print('%-28s $%8.2f  EUR %8.2f  (per board EUR %.2f, excl. VAT/customs)' % ('TOTAL for %d boards' % boards, total, total * USD_EUR, total * USD_EUR / boards))
    kit_usd = 0.0
    for lcsc, cs in kit.items():
        r = db.execute('select price_json, stock, mfr_part from components where lcsc=?', (lcsc,)).fetchone()
        unit = price_at(json.loads(r[0]), len(cs) * boards) if r else 0
        kit_usd += unit * len(cs) * boards
        print('  hand-solder kit: %-10s %-24s x%d  $%.3f  stock %s' % (lcsc, r[2][:24] if r else '?', len(cs) * boards, unit, r[1] if r else '?'))
    print('hand-solder kit parts (not assembled) for %d boards: $%.2f' % (boards, kit_usd))
    print('problems:', problems or 'none')
    json.dump({'rows': rows, 'summary': summary, 'total_usd': total, 'ext': ext, 'smt_joints': smt_j, 'tht_joints': tht_j,
               'problems': problems, 'boards': boards, 'usd_eur': USD_EUR, 'assume': a, 'kit_usd': kit_usd,
               'parts_usd': parts_usd, 'lines': len(rows)},
              open('/tmp/sbpcb/cost_%s_%d.json' % (PROJECT, boards), 'w'), indent=1)


if __name__ == '__main__':
    main()
