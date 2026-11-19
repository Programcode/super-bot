# w_report.py (offline, VPS): cable schedule + crimp/parts tally for the BOM thread.
# python3 -I w_report.py <geom.json> <flex.json> <checks-wiring.json or -> <out wiring.json>
# Cut length per conductor = routed length (smoothed centreline) + 12 mm (strip/crimp/solder both ends), rounded
# up to 5 mm. Spans split into pieces (a/b/c/d/e) are one cable: their lengths add up.
import json, math, os, re, sys
S = os.path.dirname(os.path.abspath(__file__))
g = {}
for f in ('w_lib.py', 'w_routes.py'):
    exec(open(os.path.join(S, f)).read(), g)
geo = json.load(open(sys.argv[1]))
P = {k: v['mm'] for k, v in geo['params'].items() if isinstance(v['mm'], (int, float))}
R = g['build'](P, json.load(open(os.path.join(S, 'main_board_parts.json'))))
flex = json.load(open(sys.argv[2]))
chk = json.load(open(sys.argv[3])) if sys.argv[3] != '-' else None
sweep = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else None

# end hardware per cable: (end A parts, end B parts). Crimp counts are per conductor at that end.
D = 'Dupont 2.54 female crimp in the 2x20 housing'
ENDS = {
    'S01': ('solder (pack B- tab)', 'solder (BMS B- pad)'), 'S02': ('JST-XH 4 housing + 4 XH crimps (BMS balance)', 'solder to nickel taps'),
    'S03': ('solder (pack B+ tab)', 'solder/butt splice to fuse-holder lead'), 'S04': ('butt splice to fuse-holder lead', 'XT60 male (sled), solder'),
    'S05': ('solder (BMS P-)', 'XT60 male (sled), solder'), 'S06': ('solder (DC jack tip)', 'butt splice to inline 5 A fuse lead'),
    'S07': ('butt splice to fuse lead', 'solder (ideal-diode IN)'), 'S08': ('solder (ideal-diode OUT)', 'solder (pack B+ tab)'),
    'S09': ('solder (DC jack sleeve)', 'solder (BMS P-)'),
    'F01': ('XT60 female (bulkhead), solder', 'XT60E-F panel socket, solder'), 'F02': ('XT60 female (bulkhead), solder', 'XT60H male plug (PDB), solder'),
    'F03': ('XT60E-F panel socket, solder', 'XT60H male plug (PDB), solder'),
    'O01': ('XT30 female plug (PDB out 1), solder', 'XT30 female plug (DRV perfboard), solder'), 'O02': ('XT30 female plug (PDB out 2), solder', 'solder (D36V50F5 VIN/GND)'),
    'O03': ('XT30 female plug (PDB out 3), solder', 'solder (D36V28F6 VIN/GND)'), 'P01': ('solder (D36V50F5 VOUT/GND)', 'DIY right-angle USB-C plug, 5 A, solder type'),
    'U01': ('bought cable: USB-A plug', 'bought cable: right-angle USB-C plug'),
    'G01': (D + ' x3 (+ GND bridge)', 'JST ZH1.5 4 housing + 4 ZH crimps'), 'G02': (D + ' x5', 'solder (MAX98357A header pads)'),
    'G03': (D + ' x2', 'JST-PH 2 housing + 2 PH crimps'), 'G04': (D + ' x8', 'solder (TFT header pads)'), 'G05': (D + ' x6 (2 spliced with G02)', 'solder (INMP441 pads)'),
    'K01': ('bought FFC 22-pin end', 'bought FFC 15-pin end'), 'Q01': ('bought FFC (with the AI HAT+ 2)', ''),
    'MA': ('JST-PH 6 housing + 6 PH crimps (encoder)', 'M+/M-: 2 bootlace ferrules 0.25 mm2 (DRV terminal); encoder 4: solder (ESP32 carrier)'),
    'MB': ('JST-PH 6 housing + 6 PH crimps (encoder)', 'M+/M-: 2 bootlace ferrules 0.25 mm2 (DRV terminal); encoder 4: solder (ESP32 carrier)'),
    'MC': ('JST-PH 6 housing + 6 PH crimps (encoder)', 'M+/M-: 2 bootlace ferrules 0.25 mm2 (DRV terminal); encoder 4: solder (ESP32 carrier)'),
    'MD': ('JST-PH 6 housing + 6 PH crimps (encoder)', 'M+/M-: 2 bootlace ferrules 0.25 mm2 (DRV terminal); encoder 4: solder (ESP32 carrier)'),
    'L01': ('solder (ESP32 carrier tails)', 'JST-XH 10 housing + 10 XH crimps'),
    'B01': ('solder (D2F pins)', 'solder (ESP32 carrier)'), 'B02': ('solder (D2F pins)', 'solder (ESP32 carrier)'),
    'B03': ('solder (D2F pins)', 'solder (ESP32 carrier)'), 'B04': ('solder (D2F pins)', 'solder (ESP32 carrier)'),
    'C01': ('solder (VL53L0X pads)', 'solder (ESP32 carrier)'), 'C02': ('solder (VL53L0X pads)', 'solder (ESP32 carrier)'),
    'C03': ('solder (VL53L0X pads)', 'solder (ESP32 carrier)'), 'C04': ('solder (VL53L0X pads)', 'solder (ESP32 carrier)'),
    'C05': ('solder (ESP32 carrier)', 'solder (BNO085 header pads)'), 'C06': ('solder (ESP32 carrier)', 'solder (INA226 header pads)'),
    'W01': ('solder (ESP32 carrier)', 'solder (CPX pad A6 + GND)'), 'W02': ('solder (CPX pad A1)', 'solder (perfboard nSLEEP bus)'),
    'V01': ('stock MG90S lead', 'stock JR female plug into Y-harness socket 1'),
    'V02': ('stock MG90S lead', 'stock JR female plug -> bought JR extension 150 mm -> Y-harness socket 2'),
    'V03': ('solder (D36V28F6 VOUT/GND)', '2x JR 3-pin male housing; 4 male crimps (+/- x2)'), 'V04': ('solder (ESP32 carrier)', '2 male crimps (S pins of the JR sockets)'),
    'A01': ('2 bootlace ferrules 0.5 mm2 (MAX98357A screw terminal)', 'solder (speaker tabs)'),
}
STOCK_LEN = {'K01': 500, 'U01': 150, 'V01': 250, 'V02': 400, 'Q01': None}


def base(cid):
    return re.sub(r'[a-d]$', '', cid)


cab = {}
for r in R['cables']:
    if r['id'] in ('G',):
        continue
    b = base(r['id']) if r['id'][-1] in 'abcd' and r['id'][:-1] in ('G04', 'G05', 'K01', 'V02') else r['id']
    c = cab.setdefault(b, {'id': b, 'pieces': [], 'route_mm': 0.0, 'conductors': r['conductors'], 'name': r['name'].split(',')[0].split(' (')[0]})
    c['pieces'].append({k: r.get(k) for k in ('id', 'name', 'from_', 'to', 'kind', 'od', 'route_mm', 'min_bend_mm', 'min_bend_x_od', 'bend_rule_mm', 'moving', 'stock', 'note', 'route')})
    c['route_mm'] += r['route_mm'] or 0.0
# one six-core motor cable each: MA (motor -> DRV terminal) + MAe (encoder wires on to the ESP32) = one cable
CUT = lambda L: int(math.ceil((L + 12.0) / 5.0) * 5)
for m in ('MA', 'MB', 'MC', 'MD'):
    if m in cab and m + 'e' in cab:
        e = cab.pop(m + 'e')
        c = cab[m]
        c['pieces'] += e['pieces']
        c['split_route_mm'] = (round(c['route_mm'], 1), round(e['route_mm'], 1))
        c['conductors'] = [dict(cd, cut_mm=CUT(c['route_mm'] if cd['to'].startswith('OUT') else c['route_mm'] + e['route_mm']),
                                to=(cd['to'] + ' (DRV terminal)' if cd['to'].startswith('OUT') else cd['to'] + ' (ESP32 carrier)')) for cd in c['conductors']]
        c['route_mm'] += e['route_mm']
out_c, wire_m, crimps = [], {}, {}
for b, c in cab.items():
    p0, p1 = c['pieces'][0], c['pieces'][-1]
    stock = next((p['stock'] for p in c['pieces'] if p.get('stock')), None)
    cut = int(math.ceil((c['route_mm'] + 12.0) / 5.0) * 5)
    ea, eb = ENDS.get(b, ('', ''))
    row = {'id': b, 'name': c['name'], 'from': p0['from_'], 'to': p1['to'], 'route_mm': round(c['route_mm'], 1),
           'cut_mm': None if stock else cut, 'stock': stock, 'stock_len_mm': STOCK_LEN.get(b), 'end_a': ea, 'end_b': eb,
           'kind': p0['kind'], 'od_mm': p0['od'], 'min_bend_mm': min([p['min_bend_mm'] for p in c['pieces'] if p['min_bend_mm'] is not None], default=None),
           'min_bend_x_od': min([p['min_bend_x_od'] for p in c['pieces'] if p.get('min_bend_x_od') is not None], default=None),
           'moving': any(p['moving'] for p in c['pieces']), 'route': '; '.join(p['route'] for p in c['pieces'] if p.get('route')),
           'notes': '; '.join(p['note'] for p in c['pieces'] if p.get('note')), 'conductors': c['conductors'], 'pieces': [p['id'] for p in c['pieces']]}
    out_c.append(row)
    if b in ('MA', 'MB', 'MC', 'MD'):
        row['cut_mm'] = None
        row['note_cut'] = 'per conductor: M+/M- %d mm to the DRV terminal, encoder wires %d mm to the ESP32 carrier (split after %d mm)' % (
            c['conductors'][0]['cut_mm'], c['conductors'][2]['cut_mm'], c['split_route_mm'][0])
    else:
        for cd in row['conductors']:
            cd.setdefault('cut_mm', None if (stock or row['kind'].startswith('flat')) else cut)
    if not stock and not row['kind'].startswith('flat'):
        for cd in c['conductors']:
            k = '%d AWG %s' % (cd['awg'], cd['colour'])
            wire_m[k] = round(wire_m.get(k, 0.0) + (cd.get('cut_mm') or cut) / 1000.0, 3)
    for e in (ea, eb):
        for pat, key in ((r'JST-XH (\d+) housing', 'JST-XH housing %s-pin (XHP-%s)'), (r'JST-PH (\d+) housing', 'JST-PH housing %s-pin (PHR-%s)'),
                         (r'JST ZH1.5 (\d+) housing', 'JST-ZH housing %s-pin (ZHR-%s)')):
            m = re.search(pat, e)
            if m:
                crimps[key % (m.group(1), m.group(1))] = crimps.get(key % (m.group(1), m.group(1)), 0) + 1
                fam = key.split()[0]
                crimps['%s crimp contact' % fam] = crimps.get('%s crimp contact' % fam, 0) + int(m.group(1))
        m = re.search(r'Dupont 2.54 female crimp.* x(\d+)', e)
        if m:
            crimps['Dupont 2.54 female crimp'] = crimps.get('Dupont 2.54 female crimp', 0) + int(m.group(1))
        for pat, key, n in (('XT60H male plug', 'XT60H male plug (cable)', 1), ('XT60 female (bulkhead)', 'XT60 female (bulkhead, cable side)', 1),
                            ('XT30 female plug', 'XT30 female plug (cable)', 1), ('bootlace ferrules 0.25', 'bootlace ferrule 0.25 mm2', 2),
                            ('bootlace ferrules 0.5', 'bootlace ferrule 0.5 mm2', 2), ('JR 3-pin male housing', 'JR/Futaba 3-pin male housing', 2),
                            ('USB-C plug, 5 A', 'DIY right-angle USB-C plug 5 A (solder)', 1)):
            if pat in e:
                crimps[key] = crimps.get(key, 0) + n
crimps['XT60 female (bulkhead, cable side)'] = 1
crimps['Dupont 2x20 housing (2.54)'] = 1
crimps['JR male crimp contact'] = 6
crimps['heatshrink 3 mm / 5 mm / 8 mm (m)'] = '0.5 / 0.5 / 0.3 (EST)'
crimps['cable ties 2.5 mm (pcs)'] = sum(1 for it in R['items'] if it['name'] == 'tie') + 20
bought = [{'item': 'Raspberry Pi 5 camera cable 22-to-15 pin, 500 mm', 'qty': 1}, {'item': 'USB-A to right-angle USB-C cable, 15 cm (USB 2.0 data)', 'qty': 1},
          {'item': 'JR servo extension male-female 150 mm', 'qty': 1}]
R2 = {'generated_from': 'cad/v2/scripts/w_routes.py (+ w_lib.py), doc "Super bot - v2" v%s' % geo.get('version'), 'units': 'mm',
      'cut_length_rule': 'routed centreline + 12 mm, rounded up to 5 mm; stock cables give the stock length instead',
      'bend_rule': '>= 4x conductor OD static (silicone), >= 10x where the cable flexes; tilt U-loop and terminations noted per cable',
      'cables': out_c, 'wire_totals_m': dict(sorted(wire_m.items())), 'connector_crimp_tally': crimps, 'bought_cables': bought,
      'moving_cables': flex, 'sweep': None if sweep is None else sum(len(p['hits']) for p in sweep), 'checks': chk and {k: chk[k] for k in ('wires', 'parts_checked', 'wire_part_hits', 'wire_wire_hits', 'scan_band', 'seconds') if k in chk}}
json.dump(R2, open(sys.argv[4], 'w'), indent=1)
print('cables', len(out_c), 'wire m', round(sum(wire_m.values()), 2), 'tally', len(crimps))
