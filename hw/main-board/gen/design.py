"""Super bot main board: the circuit, sheet by sheet.

Run gen/build_sch.py to regenerate the KiCad schematic from this file.
Every part carries its LCSC number. Passives are JLC Basic parts unless noted.
"""
from schgen import Part, Sheet, Design

# ------------------------------------------------------------------ part catalog
R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
C1206 = 'Capacitor_SMD:C_1206_3216Metric'

RES = {  # value: LCSC (0603, 1 %, Basic)
    '0': 'C21189', '33': 'C23140', '100': 'C22775', '330': 'C23138', '1k': 'C21190', '1.8k': 'C4177',
    '2.2k': 'C4190', '3k': 'C4211', '4.7k': 'C23162', '5.1k': 'C23186', '9.1k': 'C23260', '10k': 'C25804',
    '20k': 'C4184', '22k': 'C31850', '33k': 'C4216', '47k': 'C25819', '75k': 'C23242', '100k': 'C25803',
    '470k': 'C23178', '1M': 'C22935',
}
CAP = {  # key: (value text, footprint, LCSC)
    '100n': ('100nF 50V X7R', C0603, 'C14663'),
    '10n': ('10nF 50V X7R', C0603, 'C57112'),
    '22n': ('22nF 50V X7R', C0603, 'C21122'),
    '1n': ('1nF 50V X7R', C0603, 'C1588'),
    '100p': ('100pF 50V C0G', C0603, 'C14858'),
    '1u': ('1uF 50V X5R', C0603, 'C15849'),
    '10u25': ('10uF 25V X5R', C0603, 'C96446'),
    '22u6': ('22uF 6.3V X5R', C0603, 'C59461'),
    '4u7': ('4.7uF 25V X5R', C0805, 'C1779'),
    '10u50': ('10uF 50V X5R', C1206, 'C13585'),
    '22u25': ('22uF 25V X5R', C1206, 'C12891'),
    '470u': ('470uF 35V 8x10.5', 'Capacitor_SMD:CP_Elec_8x10.5', 'C48935389'),
    'tant10u': ('10uF 16V tantalum', 'Capacitor_Tantalum_SMD:CP_EIA-3216-18_Kemet-A', 'C7171'),
}


class Ctx:
    """Per-sheet reference counters."""

    def __init__(self):
        self.n = {}

    def ref(self, p):
        self.n[p] = self.n.get(p, 0) + 1
        return '%s%d' % (p, self.n[p])


def R(cx, val, a, b, dnp=False, fp=R0603):
    return Part('Device:R', cx.ref('R'), val, fp, {'1': a, '2': b}, lcsc=RES[val], dnp=dnp)


def C(cx, key, a, b='GND'):
    v, fp, l = CAP[key]
    lib = 'Device:C_Polarized' if key in ('470u', 'tant10u') else 'Device:C'
    return Part(lib, cx.ref('C'), v, fp, {'1': a, '2': b}, lcsc=l)


def LED(cx, color, a, k):
    if color == 'green':
        return Part('Device:LED', cx.ref('D'), 'Green', 'LED_SMD:LED_0805_2012Metric', {'2': a, '1': k}, lcsc='C2297')
    return Part('Device:LED', cx.ref('D'), 'Red', 'LED_SMD:LED_0603_1608Metric', {'2': a, '1': k}, lcsc='C2286')


def NMOS(cx, g, d, s='GND'):
    return Part('Transistor_FET:2N7002', cx.ref('Q'), '2N7002', 'Package_TO_SOT_SMD:SOT-23', {'G': g, 'D': d, 'S': s}, lcsc='C8545')


def PH(cx, n, nets, label):
    lc = {2: 'C160352', 4: 'C160354', 5: 'C265085', 6: 'C471518'}[n]
    fp = 'Connector_JST:JST_PH_B%dB-PH-SM4-TB_1x%02d-1MP_P2.00mm_Vertical' % (n, n)
    return Part('Connector_Generic:Conn_01x%02d' % n, cx.ref('J'), label, fp,
                {str(i + 1): v for i, v in enumerate(nets)}, lcsc=lc, mpn='B%dB-PH-SM4-TB' % n,
                fields={'Silk': label})


def SH(cx, n, nets, label):
    lc = {4: 'C160390', 5: 'C160391', 6: 'C160392'}[n]
    fp = 'Connector_JST:JST_SH_BM%02dB-SRSS-TB_1x%02d-1MP_P1.00mm_Vertical' % (n, n)
    return Part('Connector_Generic:Conn_01x%02d' % n, cx.ref('J'), label, fp,
                {str(i + 1): v for i, v in enumerate(nets)}, lcsc=lc, mpn='BM%02dB-SRSS-TB' % n,
                fields={'Silk': label})


def PWRFLAG(cx, net):
    return Part('power:PWR_FLAG', cx.ref('#FLG'), 'PWR_FLAG', '', {'1': net}, in_bom=False)


def BUCK(cx, vin, vout, en, pg, fb_top, fb_bot, l_val, l_lcsc, tag):
    """TPS56637 D-CAP3 buck per datasheet table 4 (R7 scaled to Basic values)."""
    sw, boot, fb, ff = tag + '_SW', tag + '_BOOT', tag + '_FB', tag + '_FF'
    parts = [
        Part('sbot:TPS56637', cx.ref('U'), 'TPS56637RPAR', 'sbot:VQFN-HR-10_L3.0-W3.0_RPA',
             {'VIN': vin, 'EN': en, 'MODE': 'GND', 'PG': pg, 'BOOT': boot, 'SW': sw, 'FB': fb,
              'AGND': 'GND', 'PGND': 'GND'}, lcsc='C841386'),
        C(cx, '10u50', vin), C(cx, '10u50', vin), C(cx, '100n', vin),
        R(cx, '100k', vin, en), R(cx, '20k', en, 'GND'),
        C(cx, '100n', boot, sw),
        Part('Device:L', cx.ref('L'), l_val, 'sbot:IND-SMD_L7.0-W6.6_FXL0630', {'1': sw, '2': vout}, lcsc=l_lcsc),
        C(cx, '22u25', vout), C(cx, '22u25', vout), C(cx, '22u25', vout), C(cx, '100n', vout),
        R(cx, fb_top, vout, fb), R(cx, fb_bot, fb, 'GND'),
        R(cx, '20k', vout, ff), C(cx, '100p', ff, fb),
        R(cx, '100k', vout, pg),
    ]
    return parts


# ------------------------------------------------------------------ sheets

def power_sheet():
    s = Sheet('power', 'power.kicad_sch', 'Power: battery input, protection, monitor, 5 V / servo / 3.3 V rails')
    for p in ('I2C0_SDA', 'I2C0_SCL'):
        s.port(p, 'bidirectional')
    s.port('INA_ALERT', 'output')
    cx = Ctx()
    b = s.block('Battery input: XT60 -> 15 A fuse -> main switch loop -> reverse-polarity P-FET -> shunt -> VBUS', 25, 40, 360,
                note='3S 18650 pack via BMS, 10.5-12.6 V. Main path copper sized for 15 A (see README).')
    b.parts += [
        Part('sbot:XT60PW-M', cx.ref('J'), 'BAT IN XT60PW-M', 'sbot:CONN-TH_XT60PW-M', {'2': 'VBAT_IN', '1': 'GND'},
             lcsc='C98732', fields={'Silk': 'BATTERY'}),
        Part('Device:Fuse', cx.ref('F'), '15A blade (XF-506P holder)', 'sbot:FUSE-TH_XF-506P', {'1': 'VBAT_IN', '2': 'VBAT_F'},
             lcsc='C492610', mpn='XF-506P', fields={'Silk': '15A'}),
        Part('sbot:XT30PW-M', cx.ref('J'), 'MAIN SWITCH XT30PW-M', 'sbot:CONN-TH_XT30PW-M', {'2': 'VBAT_F', '1': 'VSW'},
             lcsc='C431092', descr='Series loop for the DC main switch or XT60/XT30 loop key; polarity does not matter', fields={'Silk': 'MAIN SW'}),
        Part('sbot:AOD403', cx.ref('Q'), 'AOD403', 'Package_TO_SOT_SMD:TO-252-2', {'2': 'VSW', '3': 'VPROT', '1': 'RP_G'},
             lcsc='C28969', descr='Reverse-polarity protection: body diode conducts first, then gate pulled to GND'),
        R(cx, '10k', 'RP_G', 'GND'),
        Part('Device:D_Zener', cx.ref('D'), 'BZT52C15', 'Diode_SMD:D_SOD-123', {'1': 'VPROT', '2': 'RP_G'}, lcsc='C19077412'),
        Part('Device:D_TVS', cx.ref('D'), 'SMBJ15A', 'Diode_SMD:D_SMB', {'1': 'VPROT', '2': 'GND'}, lcsc='C19077569',
             descr='Unidirectional TVS: pin/pad 1 = cathode (band) on the positive rail'),
        PWRFLAG(cx, 'VBAT_IN'), PWRFLAG(cx, 'VSW'), PWRFLAG(cx, 'VPROT'),
    ]
    b = s.block('Battery monitor INA226 (I2C 0x40), 2 mOhm shunt, 16 A full scale', 25, None, 360,
                note='VBUS = protected 12 V bus feeding the motor cut switch and both bucks.')
    b.parts += [
        Part('Device:R', cx.ref('R'), '2m 1% 3W 2512', 'Resistor_SMD:R_2512_6332Metric', {'1': 'VPROT', '2': 'VBUS'},
             lcsc='C459679', mpn='RLP25FEGR002'),
        Part('Sensor_Energy:INA226', cx.ref('U'), 'INA226AIDGSR', 'Package_SO:MSOP-10_3x3mm_P0.5mm',
             {'Vin+': 'VPROT', 'Vin-': 'VBUS', 'Vbus': 'VBUS', 'VS': '+3V3', 'GND': 'GND', 'SDA': 'I2C0_SDA',
              'SCL': 'I2C0_SCL', '~{Alert}': 'INA_ALERT', 'A0': 'GND', 'A1': 'GND'}, lcsc='C49851'),
        C(cx, '100n', '+3V3'),
        R(cx, '10k', '+3V3', 'INA_ALERT'),
        C(cx, '470u', 'VBUS'), C(cx, '100n', 'VBUS'),
        R(cx, '4.7k', 'VBUS', 'LED_VBUS'), LED(cx, 'green', 'LED_VBUS', 'GND'),
        PWRFLAG(cx, 'VBUS'), PWRFLAG(cx, 'GND'),
    ]
    b = s.block('5.0 V / 6 A rail for the Pi 5 and 5 V loads (TPS56637, 3.3 uH)', 25, None, 180,
                note='Vout = 0.6 V x (1 + 22k/3k) = 5.0 V. EN divider: on above ~7 V.')
    b.parts += BUCK(cx, 'VBUS', '+5V', 'BUCK5_EN', 'BUCK5_PG', '22k', '3k', '3.3uH', 'C167219', 'BUCK5')
    b.parts += [R(cx, '1k', '+5V', 'LED_5V'), LED(cx, 'green', 'LED_5V', 'GND'), PWRFLAG(cx, '+5V')]
    b = s.block('Servo rail 5.5 V / 6 A (TPS56637, 5.6 uH), separate from the Pi rail', 215, None, 180,
                note='Vout = 0.6 V x (1 + 75k/9.1k) = 5.54 V for 2x MG90S.')
    b.parts += BUCK(cx, 'VBUS', 'VSERVO', 'BUCKS_EN', 'BUCKS_PG', '75k', '9.1k', '5.6uH', 'C475914', 'BUCKS')
    b.parts += [C(cx, '22u25', 'VSERVO'), PWRFLAG(cx, 'VSERVO')]   # D-CAP3: keep Cout under ~100 uF (TI table 4)
    b = s.block('Pi 5 power out (USB-C source, 5 V, Rp = 10k -> 3 A advert; set usb_max_current_enable=1)', 25, None, 180)
    b.parts += [
        Part('Connector:USB_C_Receptacle_USB2.0_16P', cx.ref('J'), 'PI 5V OUT', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
             {'VBUS': '+5V', 'GND': 'GND', 'SHIELD': 'GND', 'CC1': 'PIPWR_CC1', 'CC2': 'PIPWR_CC2'}, lcsc='C165948',
             mpn='TYPE-C-31-M-12', fields={'Silk': 'PI 5V OUT'}),
        R(cx, '10k', '+5V', 'PIPWR_CC1'), R(cx, '10k', '+5V', 'PIPWR_CC2'),
        C(cx, '22u25', '+5V'),
    ]
    b = s.block('3.3 V logic rail (AMS1117-3.3), fed from +5 V or the ESP32 USB port', 215, None, 180)
    b.parts += [
        Part('Device:D_Schottky', cx.ref('D'), 'B5819W', 'Diode_SMD:D_SOD-123', {'2': '+5V', '1': 'V3V3_IN'}, lcsc='C8598'),
        Part('Device:D_Schottky', cx.ref('D'), 'B5819W', 'Diode_SMD:D_SOD-123', {'2': '+5V_USB', '1': 'V3V3_IN'}, lcsc='C8598'),
        Part('Regulator_Linear:AMS1117-3.3', cx.ref('U'), 'AMS1117-3.3', 'Package_TO_SOT_SMD:SOT-223-3_TabPin2',
             {'VI': 'V3V3_IN', 'VO': '+3V3', 'GND': 'GND'}, lcsc='C6186'),
        C(cx, '10u25', 'V3V3_IN'), C(cx, '22u6', '+3V3'), C(cx, 'tant10u', '+3V3'), C(cx, '100n', '+3V3'),
        R(cx, '1k', '+3V3', 'LED_3V3'), LED(cx, 'red', 'LED_3V3', 'GND'),
        PWRFLAG(cx, 'V3V3_IN'), PWRFLAG(cx, '+5V_USB'),
    ]
    b = s.block('Mounting: 4x M3, plated and tied to GND (provisional positions, see README)', 25, None, 180)
    b.parts += [Part('Mechanical:MountingHole_Pad', 'H%d' % i, 'M3', 'MountingHole:MountingHole_3.2mm_M3_Pad_Via',
                     {'1': 'GND'}, in_bom=False) for i in range(1, 5)]
    return s


def safety_sheet():
    s = Sheet('safety', 'safety.kicad_sch', 'Hardware motor cut: watchdog + kill loop + CPX, motor power switch')
    for p, sh in (('WDI', 'input'), ('MOT_EN', 'output'), ('CUT_OK', 'output'), ('MOT_NFAULT', 'bidirectional'),
                  ('CPX_KILL', 'input'), ('VREF', 'output')):
        s.port(p, sh)
    cx = Ctx()
    b = s.block('Motor-enable watchdog (74LVC1G123 retriggerable one-shot, ~47 ms)', 25, 40, 190,
                note='ESP32 must toggle WDI at >25 Hz from its control loop. Q low = drivers asleep and VMOT off.')
    b.parts += [
        Part('74xGxx:74LVC1G123', cx.ref('U'), 'SN74LVC1G123DCUR', 'Package_SO:VSSOP-8_2.3x2mm_P0.5mm',
             {'~{A}': 'GND', 'B': 'WDI', '~{CLR}': 'CUT_OK', 'Q': 'MOT_EN', 'Cext': 'WD_CX', 'RCext': 'WD_RC',
              'VCC': '+3V3', 'GND': 'GND'}, lcsc='C352969'),
        R(cx, '47k', '+3V3', 'WD_RC'), C(cx, '1u', 'WD_RC', 'WD_CX'), C(cx, '100n', '+3V3'),
        R(cx, '100k', 'WDI', 'GND'),
        R(cx, '100k', 'MOT_EN', 'GND'),
    ]
    b = s.block('Kill loop (normally closed: open = motors cut) and CPX backup kill', 25, None, 190,
                note='Fit a shorting plug, a remote-kill relay contact or a NC button in J KILL. JP1 bypasses it on the bench.')
    b.parts += [
        PH(cx, 2, ['KILL_SRC', 'CUT_OK'], 'KILL LOOP'),
        R(cx, '1k', '+3V3', 'KILL_SRC'),
        R(cx, '100k', 'CUT_OK', 'GND'),
        Part('Jumper:SolderJumper_2_Open', 'JP1', 'KILL BYPASS', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
             {'1': 'KILL_SRC', '2': 'CUT_OK'}, in_bom=False),
        NMOS(cx, 'CPX_KILL', 'CUT_OK'),
        R(cx, '100k', 'CPX_KILL', 'GND'),
    ]
    b = s.block('Motor power switch (AOD403 high side) - VMOT only live while MOT_EN is high', 225, 40, 180,
                note='Vgs = -VBUS x 10k/14.7k (about -8.6 V at 12.6 V). Zener clamps Vgs. 1 uF Cgs slows turn-on (inrush ~4 A); nSLEEP gives the fast cut.')
    b.parts += [
        Part('sbot:AOD403', cx.ref('Q'), 'AOD403', 'Package_TO_SOT_SMD:TO-252-2', {'3': 'VBUS', '2': 'VMOT', '1': 'MC_G'},
             lcsc='C28969'),
        R(cx, '10k', 'VBUS', 'MC_G'),
        Part('Device:D_Zener', cx.ref('D'), 'BZT52C15', 'Diode_SMD:D_SOD-123', {'1': 'VBUS', '2': 'MC_G'}, lcsc='C19077412'),
        R(cx, '4.7k', 'MC_G', 'MC_D'),
        NMOS(cx, 'MC_EN', 'MC_D'),
        R(cx, '100', 'MOT_EN', 'MC_EN'),
        C(cx, '470u', 'VMOT'), C(cx, '470u', 'VMOT'), C(cx, '100n', 'VMOT'),
        Part('Device:D_TVS', cx.ref('D'), 'SMBJ15A', 'Diode_SMD:D_SMB', {'1': 'VMOT', '2': 'GND'}, lcsc='C19077569',
             descr='Unidirectional TVS: pin/pad 1 = cathode (band) on the positive rail'),
        R(cx, '4.7k', 'VMOT', 'LED_VMOT'), LED(cx, 'red', 'LED_VMOT', 'GND'),
        PWRFLAG(cx, 'VMOT'),
        C(cx, '1u', 'VBUS', 'MC_G'),      # soft turn-on: tau ~3 ms limits VMOT bulk inrush to ~4 A
    ]
    b = s.block('Shared driver signals: current-limit reference and fault wired-OR', 225, None, 180,
                note='VREF = 3.3 V x 33k/43k = 2.53 V -> ITRIP = VREF / (1.8k x 455 uA/A) = 3.1 A per motor.')
    b.parts += [
        R(cx, '10k', '+3V3', 'VREF'), R(cx, '33k', 'VREF', 'GND'), C(cx, '100n', 'VREF'),
        R(cx, '10k', '+3V3', 'MOT_NFAULT'),
    ]
    return s


def motor_sheet():
    s = Sheet('motor', 'motor.kicad_sch', 'Motor channel: DRV8874 H-bridge, current sense, encoder input', paper='A4')
    for p, sh in (('IN1', 'input'), ('IN2', 'input'), ('NSLEEP', 'input'), ('VREF', 'input'), ('NFAULT', 'output'),
                  ('IPROPI', 'output'), ('ENC_A', 'output'), ('ENC_B', 'output')):
        s.port(p, sh)
    cx = Ctx()
    b = s.block('DRV8874 in PWM (IN/IN) mode, IMODE = GND (fixed off-time, auto retry)', 20, 35, 250,
                note='IPROPI: 455 uA/A into 1.8k -> 0.82 V/A to the ESP32 ADC; also the ITRIP comparator input.')
    b.parts += [
        Part('sbot:DRV8874', cx.ref('U'), 'DRV8874PWPR', 'Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm',
             {'EN/IN1': 'IN1', 'PH/IN2': 'IN2', '~{SLEEP}': 'NSLEEP', 'PMODE': '+3V3', 'IMODE': 'GND', 'VREF': 'VREF',
              '~{FAULT}': 'NFAULT', 'IPROPI': 'IPROPI', 'VM': 'VMOT', 'VCP': 'VCP', 'CPH': 'CPH', 'CPL': 'CPL',
              'OUT1': 'OUT1', 'OUT2': 'OUT2', 'GND': 'GND', 'PGND': 'GND', 'PAD': 'GND'}, lcsc='C1855818'),
        R(cx, '1.8k', 'IPROPI', 'GND'), C(cx, '10n', 'IPROPI'),
        C(cx, '22n', 'CPH', 'CPL'), C(cx, '100n', 'VCP', 'VMOT'),
        C(cx, '100n', 'VMOT'), C(cx, '10u50', 'VMOT'),
    ]
    b = s.block('Motor + encoder connector (JGB37-520 6-wire: M+, GND, A, B, VCC, M-)', 20, None, 250,
                note='Encoder powered at 3.3 V. 10k pull-ups for open-collector Hall outputs, 1k/1nF filter (fc 160 kHz).')
    b.parts += [
        Part('Connector_Generic:Conn_01x06', cx.ref('J'), 'MOTOR', 'Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical',
             {'1': 'OUT1', '2': 'GND', '3': 'ENC_A_RAW', '4': 'ENC_B_RAW', '5': '+3V3', '6': 'OUT2'},
             lcsc='C144397', mpn='B6B-XH-A', fields={'Silk': 'MOTOR'}),
        R(cx, '10k', '+3V3', 'ENC_A_RAW'), R(cx, '10k', '+3V3', 'ENC_B_RAW'),
        R(cx, '1k', 'ENC_A_RAW', 'ENC_A'), R(cx, '1k', 'ENC_B_RAW', 'ENC_B'),
        C(cx, '1n', 'ENC_A'), C(cx, '1n', 'ENC_B'),
    ]
    return s


ESP_PINS = {
    'GND': 'GND', '3V3': '+3V3', 'EN': 'ESP_EN', 'IO0': 'ESP_IO0', 'USB_D-': 'USB_DN', 'USB_D+': 'USB_DP',
    'RXD0': 'ESP_RXD0', 'TXD0': 'ESP_TXD0',
    'IO4': 'M1_IPROPI', 'IO5': 'M2_IPROPI', 'IO6': 'M3_IPROPI', 'IO7': 'M4_IPROPI',
    'IO15': 'M1_IN1', 'IO16': 'M1_IN2', 'IO17': 'M2_IN1', 'IO18': 'M2_IN2',
    'IO9': 'M3_IN1', 'IO10': 'M3_IN2', 'IO11': 'M4_IN1', 'IO12': 'M4_IN2',
    'IO13': 'M1_ENC_A', 'IO14': 'M1_ENC_B', 'IO21': 'M2_ENC_A', 'IO47': 'M2_ENC_B',
    'IO48': 'M3_ENC_A', 'IO35': 'M3_ENC_B', 'IO36': 'M4_ENC_A', 'IO37': 'M4_ENC_B',
    'IO1': 'I2C0_SDA', 'IO2': 'I2C0_SCL', 'IO38': 'I2C1_SDA', 'IO39': 'I2C1_SCL',
    'IO40': 'WDI', 'IO41': 'EXP_INT', 'IO42': 'LED_DATA_3V3', 'IO45': 'SERVO1_3V3', 'IO46': 'SERVO2_3V3',
    'IO8': 'HC_ECHO_3V3', 'IO3': 'CPX_TX',
}
EXP_PINS = {
    'P00': 'CLIFF1_XSHUT', 'P01': 'CLIFF2_XSHUT', 'P02': 'CLIFF3_XSHUT', 'P03': 'CLIFF4_XSHUT',
    'P04': 'IMU_RST', 'P05': 'IMU_INT', 'P06': 'HC_TRIG_3V3', 'P07': 'MOT_EN',
    'P10': 'BUMP1', 'P11': 'BUMP2', 'P12': 'BUMP3', 'P13': 'BUMP4',
    'P14': 'MOT_NFAULT', 'P15': 'INA_ALERT', 'P16': 'LED_STATUS', 'P17': 'CUT_OK',
}


def mcu_sheet():
    s = Sheet('mcu', 'mcu.kicad_sch', 'ESP32-S3 motor/sensor MCU, USB-C programming, I/O expander')
    internal = {'ESP_EN', 'ESP_IO0', 'USB_DN', 'USB_DP', 'ESP_RXD0', 'ESP_TXD0', 'EXP_INT', 'LED_STATUS', 'GND', '+3V3'}
    for n in list(ESP_PINS.values()) + list(EXP_PINS.values()) + ['PI_TXD', 'PI_RXD', 'PI_ESP_EN', 'PI_ESP_BOOT']:
        if n not in internal and n not in s.ports:
            s.port(n, 'bidirectional')
    cx = Ctx()
    b = s.block('ESP32-S3-WROOM-1-N16R2 (quad PSRAM keeps GPIO35-37 free)', 25, 40, 200,
                note='All 31 free GPIOs used. Slow I/O goes through the TCA9555. ADC1 (IO4-7) reads the four IPROPI currents.')
    b.parts += [
        Part('RF_Module:ESP32-S3-WROOM-1', cx.ref('U'), 'ESP32-S3-WROOM-1-N16R2', 'sbot:WIRELM-SMD_ESP32-S3-WROOM-1',
             dict(ESP_PINS), lcsc='C2913205', mpn='ESP32-S3-WROOM-1-N16R2'),
        C(cx, '22u6', '+3V3'), C(cx, '100n', '+3V3'), C(cx, '100n', '+3V3'),
        R(cx, '10k', '+3V3', 'ESP_EN'), C(cx, '1u', 'ESP_EN'),
        R(cx, '10k', '+3V3', 'ESP_IO0'),
        Part('Switch:SW_Push', cx.ref('SW'), 'RESET', 'sbot:SW-SMD_L3.9-W3.0-P4.45', {'1': 'ESP_EN', '2': 'GND'}, lcsc='C720477',
             fields={'Silk': 'RST'}),
        Part('Switch:SW_Push', cx.ref('SW'), 'BOOT', 'sbot:SW-SMD_L3.9-W3.0-P4.45', {'1': 'ESP_IO0', '2': 'GND'}, lcsc='C720477',
             fields={'Silk': 'BOOT'}),
    ]
    b = s.block('Pi link: UART0 (also the ROM bootloader port) + Pi-controlled reset/boot for esptool', 25, None, 200,
                note='1k series resistors stop back-powering when only one side is on.')
    b.parts += [
        R(cx, '1k', 'ESP_TXD0', 'PI_RXD'), R(cx, '1k', 'PI_TXD', 'ESP_RXD0'),
        NMOS(cx, 'PI_ESP_EN', 'ESP_EN'), R(cx, '100k', 'PI_ESP_EN', 'GND'),
        NMOS(cx, 'PI_ESP_BOOT', 'ESP_IO0'), R(cx, '100k', 'PI_ESP_BOOT', 'GND'),
    ]
    b = s.block('USB-C programming / debug port (native USB-Serial-JTAG)', 240, 40, 160,
                note='Sink only: 5.1k Rd on CC1/CC2. VBUS feeds the 3.3 V LDO through a Schottky, so the ESP32 flashes with the battery off.')
    b.parts += [
        Part('Connector:USB_C_Receptacle_USB2.0_16P', cx.ref('J'), 'ESP32 USB', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
             {'VBUS': '+5V_USB', 'GND': 'GND', 'SHIELD': 'GND', 'CC1': 'USB_CC1', 'CC2': 'USB_CC2', 'D+': 'USB_DP', 'D-': 'USB_DN'},
             lcsc='C165948', mpn='TYPE-C-31-M-12', fields={'Silk': 'ESP32 USB'}),
        R(cx, '5.1k', 'USB_CC1', 'GND'), R(cx, '5.1k', 'USB_CC2', 'GND'),
        Part('Power_Protection:USBLC6-2SC6', cx.ref('U'), 'USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6',
             {'I/O1': 'USB_DP', 'I/O2': 'USB_DN', 'GND': 'GND', 'VBUS': '+5V_USB'}, lcsc='C7519'),
        C(cx, '4u7', '+5V_USB'),
    ]
    b = s.block('TCA9555 16-bit I/O expander (I2C0 0x20): cliffs XSHUT, bumpers, IMU, status', 240, None, 160,
                note='INT is open-drain to IO41. Bumpers are read on the INT edge (<1 ms).')
    b.parts += [
        Part('Interface_Expansion:TCA9555PWR', cx.ref('U'), 'TCA9555PWR', 'Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm',
             dict(EXP_PINS, **{'VCC': '+3V3', 'GND': 'GND', 'SDA': 'I2C0_SDA', 'SCL': 'I2C0_SCL', 'A0': 'GND', 'A1': 'GND',
                               'A2': 'GND', '~{INT}': 'EXP_INT'}), lcsc='C465732'),
        C(cx, '100n', '+3V3'), R(cx, '10k', '+3V3', 'EXP_INT'),
        R(cx, '4.7k', '+3V3', 'I2C0_SDA'), R(cx, '4.7k', '+3V3', 'I2C0_SCL'),
        R(cx, '2.2k', '+3V3', 'I2C1_SDA'), R(cx, '2.2k', '+3V3', 'I2C1_SCL'),
        R(cx, '1k', '+3V3', 'LED_STATUS_A'), LED(cx, 'green', 'LED_STATUS_A', 'LED_STATUS'),
    ]
    return s


PI_HEADER = {  # Raspberry Pi 40-pin header pin -> net (None = not connected)
    3: 'PI_SDA', 5: 'PI_SCL', 8: 'PI_TXD', 10: 'PI_RXD', 12: 'I2S_BCLK', 16: 'PI_ESP_EN', 18: 'PI_ESP_BOOT',
    22: 'AMP_SD', 29: 'PI_LIDAR_RX', 33: 'PI_LIDAR_PWM', 35: 'I2S_LRCLK', 38: 'I2S_DIN', 40: 'I2S_DOUT',
    6: 'GND', 9: 'GND', 14: 'GND', 20: 'GND', 25: 'GND', 30: 'GND', 34: 'GND', 39: 'GND',
}


def io_sheet():
    s = Sheet('io', 'io.kicad_sch', 'Connectors: Pi link, cliffs, bumpers, IMU, LED bar, servos, lidar, CPX, ultrasonic')
    for n in ('PI_TXD', 'PI_RXD', 'PI_ESP_EN', 'PI_ESP_BOOT', 'I2S_BCLK', 'I2S_LRCLK', 'I2S_DIN', 'I2S_DOUT', 'AMP_SD',
              'I2C0_SDA', 'I2C0_SCL', 'I2C1_SDA', 'I2C1_SCL', 'IMU_INT', 'IMU_RST', 'LED_DATA_3V3', 'SERVO1_3V3',
              'SERVO2_3V3', 'HC_TRIG_3V3', 'HC_ECHO_3V3', 'CPX_TX', 'CPX_KILL',
              'CLIFF1_XSHUT', 'CLIFF2_XSHUT', 'CLIFF3_XSHUT', 'CLIFF4_XSHUT', 'BUMP1', 'BUMP2', 'BUMP3', 'BUMP4'):
        s.port(n, 'bidirectional')
    cx = Ctx()
    b = s.block('Raspberry Pi 5 GPIO link (40-way IDC ribbon from the AI HAT+ 2 pass-through header)', 25, 40, 150,
                note='5 V/3.3 V header pins are NOT connected: the Pi is powered from the USB-C PI 5V OUT port.')
    nets = {str(i): PI_HEADER.get(i) for i in range(1, 41) if PI_HEADER.get(i)}
    b.parts += [
        Part('Connector_Generic:Conn_02x20_Odd_Even', cx.ref('J'), 'PI GPIO', 'sbot:IDC-TH_40P-P2.54_C9138', nets,
             lcsc='C9138', mpn='2.54mm 2x20 box header', fields={'Silk': 'PI GPIO'}),
        Part('Connector_Generic:Conn_01x04', cx.ref('J'), 'QWIIC PI', 'Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical',
             {'1': 'GND', '2': '+3V3', '3': 'PI_SDA', '4': 'PI_SCL'}, lcsc='C160390', mpn='BM04B-SRSS-TB', fields={'Silk': 'QWIIC PI'}),
    ]
    b = s.block('Lidar LD19 (UART to the Pi, 230400 Bd) and CPX status ring / backup watchdog', 25, None, 150)
    b.parts += [
        PH(cx, 4, ['+5V', 'GND', 'LIDAR_TX', 'LIDAR_PWM'], 'LIDAR'),
        R(cx, '1k', 'LIDAR_TX', 'PI_LIDAR_RX'), R(cx, '1k', 'PI_LIDAR_PWM', 'LIDAR_PWM'), R(cx, '10k', 'LIDAR_PWM', 'GND'),
        PH(cx, 4, ['+5V', 'GND', 'CPX_RX', 'CPX_KILL'], 'CPX'),
        R(cx, '1k', 'CPX_TX', 'CPX_RX'),
    ]
    b = s.block('Cliff sensors 4x VL53L0X on I2C1 (front, right, rear, left), JST-SH in Qwiic pin order + XSHUT', 185, 40, 220)
    for i in range(1, 5):
        b.parts.append(SH(cx, 5, ['GND', '+3V3', 'I2C1_SDA', 'I2C1_SCL', 'CLIFF%d_XSHUT' % i], 'CLIFF %d' % i))
    b.parts.append(Part('Connector_Generic:Conn_01x04', cx.ref('J'), 'QWIIC ESP', 'Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical',
                        {'1': 'GND', '2': '+3V3', '3': 'I2C1_SDA', '4': 'I2C1_SCL'}, lcsc='C160390', mpn='BM04B-SRSS-TB',
                        fields={'Silk': 'QWIIC ESP'}))
    b = s.block('Bumpers 4x (switch to GND, one 6-pin harness: F, R, B, L, GND, GND), 10k pull-up, 1k + 100 nF debounce', 185, None, 220)
    b.parts.append(PH(cx, 6, ['BUMP1_RAW', 'BUMP2_RAW', 'BUMP3_RAW', 'BUMP4_RAW', 'GND', 'GND'], 'BUMPERS'))
    for i in range(1, 5):
        b.parts += [R(cx, '10k', '+3V3', 'BUMP%d_RAW' % i),
                    R(cx, '1k', 'BUMP%d_RAW' % i, 'BUMP%d' % i), C(cx, '100n', 'BUMP%d' % i)]
    b = s.block('IMU BNO085 breakout (I2C0 0x4A)', 185, None, 220)
    b.parts += [SH(cx, 6, ['GND', '+3V3', 'I2C0_SDA', 'I2C0_SCL', 'IMU_INT', 'IMU_RST'], 'IMU')]
    b = s.block('5 V level shifting (74HCT125, VIH 2.0 V): LED bar data, servo signals, ultrasonic trigger', 25, None, 380,
                note='IO45/IO46 are strapping pins: the 10k pull-downs keep them low at reset.')
    b.parts += [
        Part('74xx:74AHCT125', cx.ref('U'), '74HCT125D', 'Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',
             {'1': 'GND', '2': 'LED_DATA_3V3', '3': 'LED_DATA_B', '4': 'GND', '5': 'SERVO1_3V3', '6': 'SERVO1_B',
              '10': 'GND', '9': 'SERVO2_3V3', '8': 'SERVO2_B', '13': 'GND', '12': 'HC_TRIG_3V3', '11': 'HC_TRIG',
              '7': 'GND', '14': '+5V'}, lcsc='C5962', mpn='74HCT125D,653'),
        C(cx, '100n', '+5V'),
        R(cx, '10k', 'SERVO1_3V3', 'GND'), R(cx, '10k', 'SERVO2_3V3', 'GND'), R(cx, '10k', 'HC_TRIG_3V3', 'GND'),
        R(cx, '330', 'LED_DATA_B', 'LED_DATA'), R(cx, '330', 'SERVO1_B', 'SERVO1_SIG'), R(cx, '330', 'SERVO2_B', 'SERVO2_SIG'),
        PH(cx, 4, ['+5V', 'LED_DATA', 'GND', 'GND'], 'LED BAR'),
        Part('Connector_Generic:Conn_01x03', cx.ref('J'), 'PAN SERVO', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
             {'1': 'GND', '2': 'VSERVO', '3': 'SERVO1_SIG'}, lcsc='C49257', fields={'Silk': 'PAN'}),
        Part('Connector_Generic:Conn_01x03', cx.ref('J'), 'TILT SERVO', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
             {'1': 'GND', '2': 'VSERVO', '3': 'SERVO2_SIG'}, lcsc='C49257', fields={'Silk': 'TILT'}),
        Part('Connector_Generic:Conn_01x04', cx.ref('J'), 'HC-SR04 (optional)', 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
             {'1': '+5V', '2': 'HC_TRIG', '3': 'HC_ECHO', '4': 'GND'}, dnp=True, in_bom=False, fields={'Silk': 'SONAR'}),
        R(cx, '10k', 'HC_ECHO', 'HC_ECHO_3V3'), R(cx, '20k', 'HC_ECHO_3V3', 'GND'),
    ]
    return s


def audio_sheet():
    s = Sheet('audio', 'audio.kicad_sch', 'Audio: MAX98357A I2S class-D amp and INMP441 mic connector (Pi I2S/PCM)', paper='A4')
    for n in ('I2S_BCLK', 'I2S_LRCLK', 'I2S_DIN', 'I2S_DOUT', 'AMP_SD'):
        s.port(n, 'bidirectional')
    cx = Ctx()
    b = s.block('MAX98357A 3.2 W into 4 Ohm, gain 9 dB (GAIN_SLOT open), mono (L+R)/2', 20, 35, 250,
                note='SD_MODE: Pi GPIO25 high -> 3.3 V x 100k/(470k+100k) = 0.58 V = (L+R)/2; low = shutdown.')
    b.parts += [
        Part('sbot:MAX98357A', cx.ref('U'), 'MAX98357AETE+T', 'Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm',
             {'DIN': 'I2S_DOUT', 'BCLK': 'I2S_BCLK', 'LRCLK': 'I2S_LRCLK', '~{SD_MODE}': 'AMP_SDM', 'VDD': '+5V', 'GND': 'GND',
              'PAD': 'GND', 'OUTP': 'SPK_P', 'OUTN': 'SPK_N'}, lcsc='C910544'),
        R(cx, '470k', 'AMP_SD', 'AMP_SDM'),
        C(cx, '10u25', '+5V'), C(cx, '100n', '+5V'),
        PH(cx, 2, ['SPK_P', 'SPK_N'], 'SPEAKER'),
    ]
    b = s.block('INMP441 microphone (head ear) on a 6-wire cable, left channel', 20, None, 250,
                note='33 Ohm source terminations on the clocks for the ~40 cm neck cable.')
    b.parts += [
        PH(cx, 6, ['+3V3', 'GND', 'MIC_SCK', 'MIC_WS', 'I2S_DIN', 'GND'], 'MIC'),
        R(cx, '33', 'I2S_BCLK', 'MIC_SCK'), R(cx, '33', 'I2S_LRCLK', 'MIC_WS'),
    ]
    return s


def build_design(libs):
    d = Design('main-board', libs)
    pw, sf, mo, mc, io, au = power_sheet(), safety_sheet(), motor_sheet(), mcu_sheet(), io_sheet(), audio_sheet()
    for sh in (pw, sf, mo, mc, io, au):
        d.add_sheet(sh)
    ident = lambda sh: {p: p for p in sh.ports}
    d.instantiate(pw, 'Power', 100, ident(pw), 30, 40)
    d.instantiate(sf, 'Motor cut', 200, ident(sf), 30, 110)
    d.instantiate(mc, 'MCU', 300, ident(mc), 120, 40)
    d.instantiate(io, 'IO', 400, ident(io), 210, 40)
    d.instantiate(au, 'Audio', 500, ident(au), 30, 170)
    for i, (letter, pos) in enumerate((('A', 'front left'), ('B', 'front right'), ('C', 'rear left'), ('D', 'rear right'))):
        m = 'M%d_' % (i + 1)
        pm = {'IN1': m + 'IN1', 'IN2': m + 'IN2', 'NSLEEP': 'MOT_EN', 'VREF': 'VREF', 'NFAULT': 'MOT_NFAULT',
              'IPROPI': m + 'IPROPI', 'ENC_A': m + 'ENC_A', 'ENC_B': m + 'ENC_B'}
        d.instantiate(mo, 'Motor %s (%s)' % (letter, pos), 600 + 100 * i, pm, 300, 40 + 40 * i)
    return d
