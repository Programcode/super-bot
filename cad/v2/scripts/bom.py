# Builds cad/v2/BOM.csv and cad/v2/BOM.md from bom_items.py (one source, so the two can't drift).
# Run from anywhere: python3 cad/v2/scripts/bom.py
#
# Prices: "price" is the number shown on the seller's page for ONE purchase unit, in "cur"; "incl" is the VAT
# rate already inside that number (0.27 for Hungarian gross prices, 0.21 / 0.19 for NL / DE shelf prices,
# 0 for net prices). net = price / rate / (1 + incl). The buyer pays "vat" on top of net: 27 % Hungarian VAT
# for every seller (HU shops in the price, EU shops by OSS at checkout, AliExpress by IOSS at checkout),
# except VAT-exempt Hungarian shops ("alanyi adómentes"), marked vat=0, whose shown price is final.
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bom_items import ITEMS, SHIPPING, NOTES, RATES, RATE_DATE, VAT  # noqa: E402

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = ['id', 'section', 'item', 'part', 'qty', 'buy', 'unit', 'seller', 'url', 'price', 'cur', 'incl', 'vat',
        'unit_eur_net', 'line_eur_net', 'line_eur_gross', 'stock', 'owned', 'total', 'placeholder', 'check',
        'alt', 'notes', 'verified']


def net(price, cur, incl):
    return price / RATES[cur] / (1 + incl)


def rows():
    out = []
    for it in ITEMS:
        r = dict(it)
        r.setdefault('vat', VAT)
        r.setdefault('incl', 0)
        if r.get('price') is None:
            r['unit_eur_net'] = r['line_eur_net'] = r['line_eur_gross'] = ''
        else:
            u = net(r['price'], r['cur'], r['incl'])
            line = 0.0 if r.get('owned') else u * r.get('buy', 1)
            r['unit_eur_net'] = round(u, 2)
            r['line_eur_net'] = round(line, 2)
            r['line_eur_gross'] = round(line * (1 + r['vat']), 2)
        out.append(r)
    return out


def ship_rows():
    out = []
    for s in SHIPPING:
        s = dict(s)
        s.setdefault('vat', VAT)
        s.setdefault('incl', 0)
        n = net(s['price'], s['cur'], s['incl'])
        s['n'], s['g'] = n, n * (1 + s['vat'])
        out.append(s)
    return out


def total(rs, kind, col):
    return sum(r[col] for r in rs if r.get('total') == kind and r[col] != '')


def money(x):
    return '' if x == '' else '%.2f' % x


def main():
    rs = rows()
    ss = ship_rows()
    with open(os.path.join(OUT, 'BOM.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction='ignore')
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, '') for k in COLS})
        for s in ss:
            w.writerow({'id': 'SHIP', 'section': 'Shipping', 'item': 'Shipping: ' + s['seller'], 'part': s['basis'],
                        'qty': 1, 'buy': 1, 'seller': s['seller'], 'url': s.get('url', ''), 'price': s['price'],
                        'cur': s['cur'], 'incl': s['incl'], 'vat': s['vat'], 'unit_eur_net': round(s['n'], 2),
                        'line_eur_net': round(s['n'], 2), 'line_eur_gross': round(s['g'], 2), 'total': 'robot',
                        'verified': s.get('verified', '')})
    T = {
        'parts': total(rs, 'robot', 'line_eur_net'), 'parts_g': total(rs, 'robot', 'line_eur_gross'),
        'ship': sum(s['n'] for s in ss), 'ship_g': sum(s['g'] for s in ss),
        'board': total(rs, 'board', 'line_eur_net'), 'board_g': total(rs, 'board', 'line_eur_gross'),
        'opt': total(rs, 'optional', 'line_eur_net'), 'opt_g': total(rs, 'optional', 'line_eur_gross'),
    }
    T['without'] = T['parts'] + T['ship']
    T['without_g'] = T['parts_g'] + T['ship_g']
    T['with'] = T['without'] + T['board']
    T['with_g'] = T['without_g'] + T['board_g']
    fmt = {k: '%.0f' % v for k, v in T.items()}
    fmt.update(rate_huf=RATES['HUF'], rate_usd=RATES['USD'], rate_gbp=RATES['GBP'], rate_date=RATE_DATE)
    md = NOTES['header'].format(**fmt)
    sections = []
    for r in rs:
        if r['section'] not in sections:
            sections.append(r['section'])
    for sec in sections:
        md += '\n## %s\n\n' % sec
        if sec in NOTES:
            md += NOTES[sec].format(**fmt) + '\n\n'
        md += '| # | Item | Part / variant to pick | Qty | Buy | Seller | EUR net | EUR incl. VAT | Stock, notes |\n'
        md += '| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
        for r in rs:
            if r['section'] != sec:
                continue
            seller = '[%s](%s)' % (r['seller'], r['url']) if r.get('url') else r.get('seller', '')
            if r.get('alt'):
                seller += '<br>Alt: %s' % r['alt']
            bits = [r.get('stock', '')]
            if r.get('placeholder'):
                bits.append('**Placeholder in the model:** ' + r['placeholder'])
            if r.get('check'):
                bits.append('**Check:** ' + r['check'])
            if r.get('notes'):
                bits.append(r['notes'])
            note = '<br>'.join(b for b in bits if b)
            tag = ' (owned)' if r.get('owned') else {'optional': ' (optional)'}.get(r.get('total'), '')
            buy = '%s x %s' % (r.get('buy', 1), r['unit']) if r.get('unit') else str(r.get('buy', ''))
            md += '| %s | %s%s | %s | %s | %s | %s | %s | %s | %s |\n' % (
                r['id'], r['item'], tag, r.get('part', ''), r.get('qty', ''), buy, seller,
                money(r['line_eur_net']), money(r['line_eur_gross']), note)
    md += '\n## Shipping\n\n' + NOTES['shipping'] + '\n\n'
    md += '| Seller | Basis | EUR net | EUR incl. VAT |\n| --- | --- | --- | --- |\n'
    for s in ss:
        md += '| %s | %s | %.2f | %.2f |\n' % (s['seller'], s['basis'], s['n'], s['g'])
    md += '| **All shipping** | | **%.2f** | **%.2f** |\n' % (T['ship'], T['ship_g'])
    md += NOTES['footer'].format(**fmt)
    with open(os.path.join(OUT, 'BOM.md'), 'w') as f:
        f.write(md)
    for k in ('parts', 'ship', 'without', 'board', 'with', 'opt'):
        print('%-8s net %8.2f  incl. VAT %8.2f' % (k, T[k], T[k + '_g']))


if __name__ == '__main__':
    main()
