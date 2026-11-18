"""Project symbol library (lib/sbot.kicad_sym): parts KiCad's libraries lack or number differently."""
import copy

from sexpr import Q, find, find1
from schgen import make_symbol, write_symbol_lib, Libs

I, O, B, P, PI, PO, OC, NC = 'input', 'output', 'bidirectional', 'passive', 'power_in', 'power_out', 'open_collector', 'no_connect'


def build(path):
    syms = []
    syms.append(make_symbol(
        'DRV8874', ref='U', footprint='Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm',
        descr='TI DRV8874 37 V 6 A brushed DC H-bridge, current sense (IPROPI), HTSSOP-16',
        datasheet='https://www.ti.com/lit/ds/symlink/drv8874.pdf',
        pins_left=[('1', 'EN/IN1', I), ('2', 'PH/IN2', I), ('3', '~{SLEEP}', I), ('16', 'PMODE', I),
                   ('7', 'IMODE', I), ('5', 'VREF', I), ('4', '~{FAULT}', OC), ('6', 'IPROPI', O)],
        pins_right=[('11', 'VM', PI), ('12', 'VCP', P), ('13', 'CPH', P), ('14', 'CPL', P),
                    ('8', 'OUT1', O), ('10', 'OUT2', O), ('15', 'GND', PI), ('9', 'PGND', PI), ('17', 'PAD', P)]))
    syms.append(make_symbol(
        'TPS56637', ref='U', footprint='sbot:VQFN-HR-10_L3.0-W3.0_RPA',
        descr='TI TPS56637 4.5-28 V in, 6 A synchronous buck, D-CAP3, VQFN-HR-10',
        datasheet='https://www.ti.com/lit/ds/symlink/tps56637.pdf',
        pins_left=[('8', 'VIN', PI), ('1', 'EN', I), ('10', 'MODE', I), ('4', 'PG', OC), ('5', 'NC', NC)],
        pins_right=[('7', 'BOOT', P), ('6', 'SW', O), ('2', 'FB', I), ('3', 'AGND', PI), ('9', 'PGND', PI)]))
    # pad 2 is '+' and pad 1 is '-' on the Amass footprints (silkscreen marks in the LCSC footprint)
    for nm, fp, d in (('XT60PW-M', 'sbot:CONN-TH_XT60PW-M', 'Amass XT60PW-M male, right-angle PCB, 30 A. Pad 2 = +, pad 1 = -'),
                      ('XT30PW-M', 'sbot:CONN-TH_XT30PW-M', 'Amass XT30PW-M male, right-angle PCB, 15 A')):
        syms.append(make_symbol(nm, ref='J', footprint=fp, descr=d,
                                pins_left=[('2', '+', P), ('1', '-', P)],
                                pins_right=[('3', 'MP', P), ('4', 'MP', P)], width=10.16))
    syms.append(make_symbol('XT60PB-M', ref='J', footprint='sbot:CONN-TH_XT60PB-M',
                            descr='Amass XT60PB-M vertical PCB male, 20 A (UL1977). Pad 2 = +, pad 1 = - (check the molded marks)',
                            pins_left=[('2', '+', P), ('1', '-', P)], pins_right=[], width=10.16))
    # AOD403: P-MOSFET in DPAK, pad 1 = G, tab 2 = D, 3 = S (AO3401A graphics, renumbered)
    libs = Libs({})
    base = copy.deepcopy(libs.get('Transistor_FET:AO3401A'))
    renum = {'1': '1', '2': '3', '3': '2'}     # AO3401A: 1 G, 2 S, 3 D
    base[1] = Q('AOD403')
    for sub in find(base, 'symbol'):
        sub[1] = Q('AOD403' + sub[1][len('Transistor_FET:AO3401A'):]) if sub[1].startswith('Transistor_FET:') else Q(sub[1].replace('AO3401A', 'AOD403'))
        for p in find(sub, 'pin'):
            num = find1(p, 'number')
            num[1] = Q(renum[str(num[1])])
    for p in find(base, 'property'):
        if p[1] == 'Value':
            p[2] = Q('AOD403')
        if p[1] == 'Footprint':
            p[2] = Q('Package_TO_SOT_SMD:TO-252-2')
        if p[1] == 'Description':
            p[2] = Q('AOS AOD403 -30 V -70 A P-MOSFET, 6.7 mOhm, DPAK (1 G, 2 D tab, 3 S)')
        if p[1] == 'Datasheet':
            p[2] = Q('https://www.aosmd.com/res/datasheets/AOD403.pdf')
        if p[1] == 'ki_fp_filters':
            p[2] = Q('TO?252*')
    syms.append(base)
    # MAX98357A with the exposed pad typed passive (library has it 'unspecified', which ERC flags on GND)
    amp = copy.deepcopy(libs.get('Audio:MAX98357A'))
    amp[1] = Q('MAX98357A')
    for sub in find(amp, 'symbol'):
        for p in find(sub, 'pin'):
            if str(find1(p, 'number')[1]) == '17':
                p[1] = 'passive'
    syms.append(amp)
    write_symbol_lib(path, syms)
    return [s[1] for s in syms]


if __name__ == '__main__':
    import sys
    print(build(sys.argv[1]))
