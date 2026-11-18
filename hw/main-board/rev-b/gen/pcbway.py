"""PCBWay turnkey assembly files: BOM (xlsx-friendly CSV) + centroid, into out/fab/pcbway/.

Usage (from a board dir): python3 gen/pcbway.py
BOM columns follow PCBWay's template: Item, Designator, Qty, Manufacturer, Manufacturer Part Number, Description,
Value, Package, Type (SMD/THT), LCSC Part #, Digi-Key search, Note. DNP parts are listed separately at the end.
Centroid comes from kicad-cli (KiCad-native rotation, mm, origin = board lower-left via --use-drill-file-origin? no:
PCBWay accepts KiCad .pos/CSV with absolute coordinates).
"""
import csv
import json
import os
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sexpr import parse, find, find1   # noqa: E402

BOARD_DIR = os.path.dirname(HERE)

DB = os.path.expanduser('~/.local/share/kicad-mcp/jlcpcb_parts.db')
THT_HINTS = ('XT60', 'XT30', 'FUSE-TH', 'IDC-TH', 'JST_XH', 'PinHeader', 'MountingHole')


def project_name():
    for f in os.listdir(BOARD_DIR):
        if f.endswith('.kicad_pro'):
            return f[:-len('.kicad_pro')]
    raise SystemExit('no project')


def comps(sch):
    out = '/tmp/sbpcb/pcbway.net'
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, sch], check=True,
                   capture_output=True)
    n = parse(open(out).read())
    res = []
    for c in find(find1(n, 'components'), 'comp'):
        f = {}
        fl = find1(c, 'fields')
        if fl:
            for x in find(fl, 'field'):
                f[str(find1(x, 'name')[1])] = str(x[2]) if len(x) > 2 else ''
        props = {str(find1(p, 'name')[1]) for p in find(c, 'property')}
        res.append({'ref': str(find1(c, 'ref')[1]), 'value': str(find1(c, 'value')[1]),
                    'fp': str(find1(c, 'footprint')[1]) if find1(c, 'footprint') else '',
                    'lcsc': f.get('LCSC', ''), 'mpn': f.get('MPN', ''), 'dnp': 'dnp' in props,
                    'nobom': 'exclude_from_bom' in props, 'descr': str(find1(c, 'description')[1]) if find1(c, 'description') else ''})
    return res


def live(lcsc):
    raw = subprocess.run(['curl', '-s', '-m', '15', 'https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=' + lcsc],
                         capture_output=True, text=True).stdout
    try:
        d = json.loads(raw)['result']
        return d['productModel'], d['brandNameEn'], d.get('encapStandard', '')
    except Exception:
        return None


def main():
    proj = project_name()
    outdir = os.path.join(BOARD_DIR, 'out', 'fab', 'pcbway')
    os.makedirs(outdir, exist_ok=True)
    db = sqlite3.connect(DB)
    lines = {}
    dnp = []
    for c in comps(os.path.join(BOARD_DIR, proj + '.kicad_sch')):
        if c['nobom'] or c['ref'].startswith('#') or c['ref'].startswith('H'):
            continue
        if c['dnp']:
            dnp.append(c)
            continue
        lines.setdefault((c['lcsc'], c['value'] if not c['lcsc'] else '', c['fp']), []).append(c)
    rows = []
    for i, ((lcsc, value, fp), cs) in enumerate(sorted(lines.items(), key=lambda kv: kv[1][0]['ref']), 1):
        r = db.execute('select mfr_part, manufacturer, package, description from components where lcsc=?', (lcsc,)).fetchone()
        if r:
            mpn, mfr, pkg, desc = r
        else:
            lv = live(lcsc) if lcsc else None
            mpn, mfr, pkg = lv if lv else (cs[0]['mpn'], '', '')
            desc = cs[0]['descr']
        tht = any(h in fp for h in THT_HINTS)
        value = ' / '.join(sorted({c['value'] for c in cs}))
        rows.append([i, ','.join(c['ref'] for c in cs), len(cs), mfr, mpn, (desc or '')[:80], value, pkg or fp.split(':')[-1],
                     'THT' if tht else 'SMD', lcsc, 'https://www.digikey.com/en/products/result?keywords=' + (mpn or value).replace(' ', '+'),
                     ''])
    for c in dnp:
        rows.append(['DNP', c['ref'], 1, '', c['mpn'], 'Do not populate (hand-solder later)', c['value'], c['fp'].split(':')[-1],
                     'THT' if any(h in c['fp'] for h in THT_HINTS) else 'SMD', c['lcsc'], '', 'DNP'])
    with open(os.path.join(outdir, proj + '_bom_pcbway.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Item #', 'Designator', 'Qty', 'Manufacturer', 'Mfg Part #', 'Description', 'Value', 'Package/Footprint',
                    'Type', 'LCSC Part #', 'Digi-Key (search)', 'Note'])
        w.writerows(rows)
    # centroid: KiCad native, mm, front only, SMD + THT (PCBWay places THT too when quoted)
    pos = os.path.join(outdir, proj + '_centroid_pcbway.csv')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'front',
                    '--exclude-dnp', '-o', pos, os.path.join(BOARD_DIR, proj + '.kicad_pcb')], check=True, capture_output=True)
    rd = list(csv.reader(open(pos)))
    with open(pos, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Value', 'Package', 'Mid X (mm)', 'Mid Y (mm)', 'Rotation', 'Layer'])
        for r in rd[1:]:
            if r[0].startswith('H'):
                continue
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], 'Top' if r[6].lower().startswith('top') else 'Bottom'])
    n_smd = sum(r[2] for r in rows if r[0] != 'DNP' and r[8] == 'SMD')
    n_tht = sum(r[2] for r in rows if r[0] != 'DNP' and r[8] == 'THT')
    print('PCBWay BOM lines %d (placed SMD %d, THT %d, DNP %d) -> %s' % (len([r for r in rows if r[0] != 'DNP']), n_smd, n_tht,
                                                                     len(dnp), outdir))


if __name__ == '__main__':
    main()
