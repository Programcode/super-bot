# w_routes.py: every cable of the v2 harness (module layout, 19 Nov 2026), as data. Needs w_lib.py in the
# same namespace. build(P, parts) -> {'cables': [...schedule rows...], 'items': [...geometry...]}
#   P = user parameters in mm (live from Fusion, or from geom.json offline); every end point is an expression
#   of the parameters, so rerunning s8_wiring after a layout change moves the ends with the parts.
# (`parts` = the parked main board's KiCad data; only used by the H helper, kept for the board option.)

BOARD_OVERRIDE = {   # ref: (KiCad x, KiCad y, header height above the PCB front face, mated stack, long axis)
    'J101': (59.0, 103.5, 16.0, 26.0, 'z'),     # XT60PB-M vertical (rev B), option (a) spot
    'J102': (57.0, 60.0, 16.0, 26.0, 'x'),      # XT60PB-M vertical (rev B), option (a) spot
}
HDR = [('JST_XH', 9.8), ('JST_PH', 6.0), ('JST_SH', 4.25), ('IDC', 9.0), ('USB_C', 3.3), ('PinHeader', 8.5)]
PLUG_OUT = {'JST_XH': 4.0, 'JST_PH': 3.0, 'JST_SH': 2.0, 'IDC': 4.0, 'PinHeader': 6.0}   # plug housing above the header top

# wire data (EST unless noted; silicone hook-up wire)
OD = {16: 2.9, 18: 2.3, 20: 1.9, 22: 1.6, 24: 1.4, 26: 1.2, 28: 1.0}
LOOK = {'red': 'Plastic - Matte (Red)', 'black': 'Plastic - Matte (Black)', 'white': 'Plastic - Matte (White)',
        'grey': 'Plastic - Matte (Gray)', 'yellow': 'Plastic - Matte (Yellow)', 'blue': 'Plastic - Matte (Blue)',
        'ffc': 'Plastic - Glossy (White)', 'brown': 'Plastic - Matte (Black)', 'tie': 'Plastic - Matte (Black)', 'sleeve': 'Plastic - Matte (Black)'}


class H:
    """Collects geometry items and schedule rows."""

    def __init__(self, P, parts):
        self.P, self.items, self.cables = P, [], []
        self.J = {}
        top, xr, yf = P['mb_top'], P['mb_xr'], P['mb_y0'] + 1.6
        for p in parts:
            r = p['ref']
            if not r.startswith('J'):
                continue
            h = next((v for k, v in HDR if k in p['fp']), 6.0)
            fam = next((k for k, v in HDR if k in p['fp']), 'XT60')
            kx, ky = (p['x0'] + p['x1']) / 2, (p['y0'] + p['y1']) / 2
            w, ht = p['x1'] - p['x0'], p['y1'] - p['y0']
            stack = h + PLUG_OUT.get(fam, 3.0)
            ax = 'x' if w >= ht else 'z'
            if r in BOARD_OVERRIDE:
                kx, ky, h, stack, ax = BOARD_OVERRIDE[r]
                fam, w, ht = 'XT60', (16.0 if ax == 'x' else 8.2), (8.2 if ax == 'x' else 16.0)
            self.J[r] = {'x': xr - (kx - 50.0), 'z': top - (ky - 50.0), 'y_top': yf + h, 'y_out': yf + stack, 'fam': fam,
                         'w': w, 'h': ht, 'axis': ax, 'val': p['val']}

    # ---- geometry primitives
    def round(self, name, pts, d, look, group='fixed', R=None, cable=None):
        R = R if R is not None else 3.0 * d
        dense, radii = smooth(pts, R)
        self.items.append({'kind': 'round', 'name': name, 'd': d, 'pts': dense, 'look': LOOK.get(look, look), 'group': group, 'cable': cable})
        return plen(dense), radii

    def flat(self, name, wps, w, t, look, group='fixed', R=5.0, cable=None):
        dense, radii, folds = flat_path(wps, R)
        self.items.append({'kind': 'flat', 'name': name, 'w': w, 't': t, 'pts': [p for p, _ in dense], 'wv': [v for _, v in dense],
                           'look': LOOK.get(look, look), 'group': group, 'cable': cable})
        return plen([p for p, _ in dense]), radii, folds

    def box(self, name, c, u, v, size, look, group='fixed', cable=None):
        """Box centred at c; u = length axis, v = width axis (unit vectors), size = (length, width, height)."""
        self.items.append({'kind': 'box', 'name': name, 'c': c, 'u': unit(u), 'v': unit(v), 'size': size, 'look': LOOK.get(look, look),
                           'group': group, 'cable': cable})

    def housing(self, name, face, out, wdir, size, look='white', group='fixed', cable=None):
        """Connector housing: sits on `face` (point), extends along `out` by size[0]; wdir = its long axis.
        Returns the point where the wires leave it."""
        out = unit(out)
        self.box(name, add(face, mul(out, size[0] / 2)), out, wdir, size, look, group, cable)
        return add(face, mul(out, size[0]))

    def board_plug(self, ref, name, cable, look='white', out_len=None):
        """Mated cable plug on main-board connector `ref`. Returns the wire exit point (cable leaves along +Y)."""
        j = self.J[ref]
        L = (j['y_out'] - j['y_top']) if out_len is None else out_len
        wdir = (1, 0, 0) if j['axis'] == 'x' else (0, 0, 1)
        sz = (L, max(j['w'], j['h']) + (1.0 if j['fam'] != 'XT60' else 0.0), min(j['w'], j['h']) + (1.0 if j['fam'] != 'XT60' else 0.0))
        return self.housing('%s plug on %s' % (name, ref), (j['x'], j['y_top'], j['z']), (0, 1, 0), wdir, sz, look, 'fixed', cable)

    def tie(self, cable, at, d, axis, group='fixed'):
        """Cable tie (2.5 mm band) round a bundle of diameter d at point `at`, bundle along `axis`."""
        a = unit(axis)
        v = perp((0, 0, 1), a) if abs(a[2]) < 0.9 else perp((1, 0, 0), a)
        self.box('tie', at, a, v, (2.5, d + 1.4, d + 1.4), 'tie', group, cable)

    def row(self, **kw):
        self.cables.append(kw)


def pair(h, cid, name, centre, sides, sep, gauge, looks, R, group='fixed'):
    """Two single wires (e.g. +/-) side by side: centre waypoints offset by +-sep/2 along per-waypoint side vectors
    (sep: one value, or one per waypoint)."""
    L = []
    seps = sep if isinstance(sep, (list, tuple)) else [sep] * len(centre)
    for k, sgn in ((0, 1), (1, -1)):
        pts = [add(c, mul(unit(s), sgn * sp / 2)) for c, s, sp in zip(centre, sides, seps)]
        ln, radii = h.round('%s %s' % (name, looks[k]), pts, OD[gauge], looks[k], group, R, cid)
        L.append((ln, radii))
    return L




# ================================================================== module-layout harness (19 Nov 2026)
STRIP = 12.0      # cut-length allowance per cable: 2 x (strip/crimp or solder 4 mm + 2 mm slack)
BEND_STATIC, BEND_MOVING = 4.0, 10.0     # min bend radius, x conductor OD (loose tied bundles bend wire by wire) or x cable OD (jacketed):
# silicone hook-up wire 4x static (Central Wires; 5-7.5x quoted for stiffer PVC), 10x for spans that flex (NEWT)


def bundle_od(conds):
    """Outer diameter of a loose round bundle of the given conductors (EST: packing factor 1.25)."""
    a = sum((OD[c[3]] / 2.0) ** 2 for c in conds)
    return round(2.0 * math.sqrt(a) * 1.25, 1) if len(conds) > 1 else OD[conds[0][3]]


def cable(h, cid, name, a, b, conds, pts, look='black', od=None, R=None, group='fixed', stock=None, note='', moving=False,
          kind='bundle', route=''):
    """One cable = one round body along pts. conds: (wire, from pin, to pin, AWG, colour, signal)."""
    d = od or bundle_od(conds)
    base = d if od else max(OD[c[3]] for c in conds)        # jacketed cable: its OD; loose bundle: its thickest conductor
    rule = (BEND_MOVING if moving else BEND_STATIC) * base
    R = max(rule, R or 0.0)
    ln, radii = h.round(name, pts, d, look, group, R, cid)
    h.row(id=cid, name=name, from_=a, to=b, kind=kind, od=d, route_mm=round(ln, 1), cut_mm=int(math.ceil((ln + STRIP) / 5.0) * 5),
          min_bend_mm=min(radii) if radii else None, bend_rule_mm=round(rule, 1), min_bend_x_od=round(min(radii) / base, 1) if radii else None, moving=moving, stock=stock, note=note, route=route,
          conductors=[{'wire': c[0], 'from': c[1], 'to': c[2], 'awg': c[3], 'colour': c[4], 'signal': c[5]} for c in conds])
    return ln


def flatcable(h, cid, name, a, b, conds, wps, w, t, look='ffc', group='fixed', stock=None, note='', moving=False, route='', R=6.0):
    ln, radii, folds = h.flat(name, wps, w, t, look, group, R, cid)
    h.row(id=cid, name=name, from_=a, to=b, kind='flat %.1f x %.1f' % (w, t), od=None, route_mm=round(ln, 1), cut_mm=None,
          min_bend_mm=min(radii) if radii else None, bend_rule_mm=R, folds=folds, moving=moving, stock=stock, note=note, route=route,
          conductors=[{'wire': c[0], 'from': c[1], 'to': c[2], 'awg': c[3], 'colour': c[4], 'signal': c[5]} for c in conds])
    return ln


def H2(h, name, c, u, v, size, look='white', cid=None, group='fixed'):
    h.box(name, c, u, v, size, look, group, cid)


def build(P, parts, only=None):
    h = H(P, parts) if parts else H.__new__(H)
    if not parts:
        h.P, h.items, h.cables, h.J = P, [], [], {}
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    want = (lambda k: True) if only is None else (lambda k: any(k.startswith(o) for o in only))
    # ---------------------------------------------------------------- anchors from the parameters
    sp_f, sp_b = P['spine_y'], P['spine_y'] - P['ply_t']                     # spine faces 44 / 40
    top_deck = P['top_deck_z']
    pt = P['plate_top']
    # Pi 5 (pose B): u -> +X from the USB-C end, v -> -Z from the HDMI edge (top) ; component face y
    px0, pz_top, pyf = P['pi_xc'] - 42.5, P['pi_z0'] + 56.0, P['pi_y0'] + 1.4
    PI = lambda u, v, y=0.0: (px0 + u, pyf + y, pz_top - v)
    hat_hdr_top = pyf + P['hat_so'] + 1.6 + 8.5                              # 77.5
    # DRV perfboard (s4c): centre x -45, bottom drv_z, front face spine_y + 9.6
    dxc, dz0, dpy = -45.0, P['drv_z'], P['spine_y'] + 9.6
    # ESP32 cradle (s4c): x 17..83, z drv_z + 5.3 .. drv_z + 34.7, PCB front y spine_y + 10.6
    ez0, ez1 = P['drv_z'] + 20 - 14.7, P['drv_z'] + 20 + 14.7
    # PDB (s4c, right cheek): board outer face x cheek_x + ply_t + 6.6, y -45..35, z0 = plate_top + 130
    pdx, pdz0 = P['cheek_x'] + P['ply_t'] + 6.6, pt + 130.0
    # amp + servo buck (left cheek outer face)
    lcx = -(P['cheek_x'] + P['ply_t'] + 5.6)
    # loop key: XT60E-F panel socket tails
    key_y, key_z = -(P['shell_y'] - P['pwall']) + 12.0, P['body_top'] - 44.1
    # lanes
    yF = 93.0                       # front power lane, 4.6 mm behind the front wall
    yU = 66.0                       # under-board lane (in front of the driver terminals, above the motors)
    zU = 79.0
    zT = 216.0                      # top lane, above the Pi/HAT, under the CPX bracket
    xR, xL = 89.0, -89.0            # side columns / side channels
    zS = 165.0                      # left/right spine slots (centre)
    slot_c = (0.0, sp_b + 2.0, top_deck - 44.0)            # centre slot centre (x 0, z 220)
    upper_cheek = lambda sx: (sx * (P['cheek_x'] + 2.0), -40.0, top_deck - 20.0)   # z 244
    low_slot = lambda sx: (sx * 48.0, sp_b + 2.0, pt + 18.0)                        # z 54
    # upper cheek slots (y -50..-30, z 239..249): one flat row per slot, every cable at its own y (tidy, no crossings)
    ucz = top_deck - 22.2                                                             # row height z 241.8
    ucy = {'O03': -47.6, 'A01': -43.8, 'G01': -40.0, 'V01': -36.2, 'V02a': -32.6, 'O02': -38.0}
    ucs = lambda sx, cid, dx=0.0: (sx * (P['cheek_x'] + 2.0 + dx), ucy[cid], ucz)      # point in the slot (dx: + = outboard)
    lch = {'A01': -93.3, 'G01': -94.0}                                                # left channel planes outboard of the JR sockets / buck
    # centre slot (x -12..12, z 214..226): camera FFC flat at the bottom (x -2.55..8.95), P01 left, TFT + mic bundles stacked
    # on the right (they pass the FFC's riser into the shaft on its right side); same positions along the top lane
    zK = 214.6
    cs = {'P01': (-8.5, 218.5), 'G04': (10.2, 218.6), 'G05': (10.4, 222.2)}
    # =============================================================== sled (rides with the battery sled)
    if want('S'):
        ptop = pt + 2 + P['pack_z']              # pack top 95.8
        zw = ptop + 1.6
        bp = (12.0, P['pack_y1'] - 3.0, zw)      # pack B+ terminal (front top, right)
        bm = (-12.0, P['pack_y0'] + 3.0, zw)     # pack B- terminal (rear top, left)
        fz = ptop + 5.5                          # fuse holder lead height
        f_in, f_out = (0.0, P['pack_y1'] - 33.0, fz), (0.0, P['pack_y1'] - 3.0, fz)
        mcz = pt + 12.4                          # XT60 cup height
        m_y = P['sled_y1'] - 2.0                 # XT60 male cups (inside the nose)
        bms_bm, bms_pm = (-6.0, P['pack_y0'] + 15.2, ptop + 2.6), (-6.0, P['pack_y1'] - 55.2, ptop + 2.6)
        cable(h, 'S01', 'pack B- to BMS B-', 'pack B- terminal (rear top)', 'BMS B- pad', [(1, 'B-', 'B-', 16, 'black', 'pack -')],
              [bm, (bm[0], bm[1] + 6.2, zw), (bm[0], bms_bm[1], bms_bm[2] + 0.3), (bms_bm[0] - 0.4, bms_bm[1], bms_bm[2] + 0.3)], 'black', R=6.0,
              note='solder both ends; lands on the B- pad from the left (clear of the 5 A fuse holder)')
        cable(h, 'S02', 'BMS balance lead', 'BMS balance header (4)', 'cell group taps 0 / 1 / 2 / 3', [(1, 'B0', 'B-', 22, 'black', 'cell 0'), (2, 'B1', 'cell 1+', 22, 'red', 'cell 1'),
              (3, 'B2', 'cell 2+', 22, 'red', 'cell 2'), (4, 'B3', 'B+', 22, 'red', 'cell 3')],
              [(8.0, -45.0, ptop + 3.4), (14.0, -41.0, zw + 1.6), (14.0, P['pack_y0'] + 67.2, zw)], 'red', R=6.0,
              note='JST-XH 4 at the BMS; taps soldered to the nickel strips (bundle drawn to the middle strip; the rear strip is under the ideal diode)')
        cable(h, 'S03', 'B+ to 15 A fuse in', 'pack B+ terminal (front top)', '15 A fuse holder in-lead', [(1, 'B+', 'in', 16, 'red', 'pack +')],
              [bp, (bp[0], f_in[1] - 4, zw), (f_in[0], f_in[1] - 4, fz), f_in], 'red', R=6.0)
        cable(h, 'S04', '15 A fuse out to sled XT60 male +', '15 A fuse holder out-lead', 'XT60 male (sled) +', [(1, 'out', '+', 16, 'red', 'VBAT fused')],
              [f_out, (2.0, P['pack_y1'] + 1.5, fz), (3.6, P['spine_y'] + 3.0, fz - 8), (3.6, P['spine_y'] + 3.0, mcz + 8), (3.6, m_y - 3, mcz), (3.6, m_y, mcz)],
              'red', R=6.0, note='over the pack front edge, through the spine feed relief, down into the sled nose')
        cable(h, 'S05', 'BMS P- to sled XT60 male -', 'BMS P- pad', 'XT60 male (sled) -', [(1, 'P-', '-', 16, 'black', 'GND')],
              [(bms_pm[0] + 1.5, bms_pm[1], bms_pm[2] + 0.3), (bms_pm[0] + 1.5, bms_pm[1] + 6.5, bms_pm[2] + 0.3), (-13.0, bms_pm[1] + 12.5, zw), (-13.0, P['pack_y1'] - 6, zw), (-3.6, P['pack_y1'] + 1.5, fz - 2), (-3.6, P['spine_y'] + 3.0, fz - 10),
               (-3.6, P['spine_y'] + 3.0, mcz + 8), (-3.6, m_y - 3, mcz), (-3.6, m_y, mcz)], 'black', R=6.0)
        jk = (0.0, P['sled_y0'] + 19.0, P['body_z0'] + 82.0)      # charge jack tails
        cf_in, cf_out = (0.0, P['pack_y0'] + 35.0, ptop + 3.5), (0.0, P['pack_y0'] + 9.0, ptop + 3.5)
        di_in, di_out = (10.0, P['pack_y0'] + 4.0, ptop + 4.5), (18.0, P['pack_y0'] + 22.0, ptop + 4.5)
        cable(h, 'S06', 'charge jack + to 5 A fuse in', 'DC jack 5.5x2.1 centre (+)', '5 A inline fuse in', [(1, 'tip', 'in', 18, 'red', 'charge +')],
              [(1.5, jk[1], jk[2]), (1.5, cf_in[1] + 12, jk[2]), (0.5, cf_in[1] + 12, cf_in[2]), cf_in], 'red')
        cable(h, 'S07', '5 A fuse out to ideal diode IN', '5 A inline fuse out', 'ideal-diode module IN', [(1, 'out', 'IN', 18, 'red', 'charge + fused')],
              [cf_out, (cf_out[0], cf_out[1] - 3, cf_out[2]), (6.0, di_in[1] + 1, di_in[2]), di_in], 'red', R=4.0)
        cable(h, 'S08', 'ideal diode OUT to pack B+', 'ideal-diode module OUT', 'pack B+ terminal', [(1, 'OUT', 'B+', 18, 'red', 'charge into P+ (common-port BMS)')],
              [di_out, (18.0, di_out[1] + 5, di_out[2]), (17.6, di_out[1] + 12, zw), (17.6, bp[1] - 6, zw), (bp[0] + 3.2, bp[1], zw)], 'red', R=5.0)
        cable(h, 'S09', 'charge jack - to BMS P-', 'DC jack sleeve (-)', 'BMS P- pad', [(1, 'sleeve', 'P-', 18, 'black', 'charge -')],
              [(-1.5, jk[1], jk[2]), (-1.5, jk[1] + 10, jk[2]), (-8.0, jk[1] + 30, ptop + 6), (-8.0, bms_pm[1] - 6, ptop + 3.0), (bms_pm[0] - 2, bms_pm[1], ptop + 3.0)], 'black', R=5.0)
    # =============================================================== main feed: bulkhead XT60 -> loop key -> PDB
    fcz = pt + 12.4
    fy = P['sled_y1'] + 30.0                                   # bulkhead XT60 female cups (y 86.4)
    x60 = (pdx + 4.1, -31.0, pdz0 + 2.0)                       # PDB XT60 (bottom), mates from below
    x60p = (x60[0], x60[1], x60[2] - 10.0)                     # mated XT60 male plug bottom (wires leave downward)
    # right spine slot (x 78..92, z 160..170): lower row F01 / F02 / C06, upper row the O01 pair; behind the spine F01 runs
    # in the gap between the cheek and the PDB (x 80..85), F02 / F03 come up into the PDB XT60 plug from below
    rs_lo, rs_hi = 161.7, 165.6
    xF1, xF2, xC6, xO1 = 82.3, 85.6, 89.4, 83.8
    if want('F'):
        H2(h, 'heatshrink on bulkhead XT60 cup +', (3.6, fy + 2.0, fcz), Y, X, (4.0, 6.6, 7.0), 'sleeve', 'F01')
        H2(h, 'heatshrink on bulkhead XT60 cup -', (-3.6, fy + 2.0, fcz), Y, X, (4.0, 6.6, 7.0), 'sleeve', 'F02')
        H2(h, 'XT60 male plug on PDB (XT60H-M)', (x60[0], x60[1], x60[2] - 5.0), Z, Y, (10.0, 16.4, 8.2), 'yellow', 'F02')
        up = [(0, fy + 4, fcz), (0, yF, fcz + 10), (0, yF, zU + 6), (60, yF, zU + 6), (xR, yF - 4, zU + 14)]
        sideR = [(1, 0, 0)] + [(0, 1, 0)] * 4                  # side by side across the lane (+ toward the front wall)
        red = [add(p, mul(unit(s), -1.8)) for p, s in zip(up, sideR)]
        blk = [add(p, mul(unit(s), 1.8)) for p, s in zip(up, sideR)]
        red[0], blk[0] = (3.6, fy + 4, fcz), (-3.6, fy + 4, fcz)
        cable(h, 'F01', 'main feed + : bulkhead XT60 to loop key A', 'bulkhead XT60 female + (sled blind mate)', 'loop key XT60E-F socket pin A',
              [(1, '+', 'A', 16, 'red', 'VBAT fused, unswitched')],
              [(3.6, fy, fcz)] + red + [(xF1, 66.0, 140.0), (xF1, 66.0, 150.0), (xF1, 52.0, rs_lo), (xF1, 30.0, rs_lo), (xF1, 20.0, 157.0), (xF1, -46.0, 157.0),
                                         (xF1, -46.0, 224.3), (xF1, -46.0, 227.8), (xF1, P['rear_y'] - 7, 227.8), (66.0, key_y + 18.6, key_z), (53.6, key_y + 12, key_z),
                                         (53.6, key_y, key_z)],
              'red', R=8.0, route='up the front power lane, right column, right spine slot, behind the PDB (cheek gap), rear-plate loop slot')
        cable(h, 'F02', 'main feed - : bulkhead XT60 to PDB XT60 -', 'bulkhead XT60 female -', 'PDB XT60H-M plug -', [(1, '-', '-', 16, 'black', 'GND')],
              [(-3.6, fy, fcz)] + blk + [(xF2, 70.0, 140.0), (xF2, 70.0, 150.0), (xF2, 54.0, rs_lo), (xF2, 34.0, rs_lo), (xF2 + 1.0, 18.0, 150.0),
                                          (87.2, -14.0, 140.0), (87.2, x60[1], 140.0), (x60p[0], x60[1] - 3.6, 150.0), (x60p[0], x60[1] - 3.6, x60p[2])],
              'black', R=8.0, route='with F01 to the right spine slot, under the PDB, up into the PDB XT60 from below')
        cable(h, 'F03', 'loop key B to PDB XT60 +', 'loop key XT60E-F socket pin B', 'PDB XT60H-M plug +', [(1, 'B', '+', 16, 'red', 'VBAT switched')],
              [(46.4, key_y, key_z), (46.4, key_y + 12, key_z), (62.0, key_y + 24, key_z - 4), (88.6, P['rear_y'] - 8, 222.3), (88.6, -45.1, 222.3),
               (88.6, -45.1, 213.5), (94.2, -44.0, 200.0), (94.2, -44.0, 160.0), (94.2, -44.0, 140.0), (94.2, x60[1], 140.0), (x60p[0], x60[1] + 3.6, 150.0),
               (x60p[0], x60[1] + 3.6, x60p[2])],
              'red', R=8.0, route='back through the loop slot, down the side channel outboard of the PDB, into the PDB XT60 from below')
    # =============================================================== PDB outputs (XT30 on the top edge, plugs from above)
    xt30 = lambda k: (pdx + 2.75, -17.0 + 12.5 * k, pdz0 + 46.0 + 10.0)      # mated XT30 female plug top (wires leave upward)
    if want('O'):
        for k in range(4):
            c0 = xt30(k)
            H2(h, 'XT30 female plug on PDB out %d' % (k + 1), (c0[0], c0[1], c0[2] - 5.0), Z, Y, (10.0, 10.2, 5.2), 'yellow', 'O%02d' % (k + 1))
        # O1 -> DRV perfboard XT30 12 V in (front left, mates +Y)
        dxt = (dxc + 28.0, dpy + 5.5 + 12.0, dz0 + 36.0)          # mated plug front
        H2(h, 'XT30 female plug on DRV perfboard', (dxt[0], dxt[1] - 6.0, dxt[2]), Y, X, (12.0, 10.2, 5.2), 'yellow', 'O01')
        c0 = xt30(0)
        d45 = unit((1, 1, 0))                       # side vector turning from X to Y without the pair crossing over
        route = [c0, add(c0, (0, 0, 4.0)), ((c0[0] + xO1) / 2, c0[1] + 2.5, c0[2] + 6.5), (xO1, c0[1] + 6, c0[2] + 7.5), (xO1, 37.0, c0[2] + 7.5),
                 (xO1, 37.0, rs_hi), (xO1, 76.0, rs_hi), (xO1, 76.0, 142.0), (xO1, 76.0, 137.0), (xO1, 76.0, 130.0), (60.0, 76.0, 130.0), (dxt[0], 74.0, 130.0),
                 (dxt[0], dxt[1] + 4, dxt[2] + 6), (dxt[0], dxt[1], dxt[2])]
        pair(h, 'O01', 'PDB out 1 -> DRV perfboard 12 V (16 AWG)', route, [Y, Y, d45, X, X, X, X, X, d45, Y, Y, Y, Y, X],
             [5.0, 5.0, 4.2] + [3.6] * 11, 16, ('red', 'black'), 8.0)
        L = plen(route)
        h.row(id='O01', name='PDB out 1 -> DRV8874 perfboard 12 V in', from_='PDB XT30 out 1', to='DRV perfboard XT30 in', kind='pair', od=OD[16], route_mm=round(L, 1),
              cut_mm=int(math.ceil((L + STRIP) / 5) * 5), bend_rule_mm=5 * OD[16], moving=False, route='up over the PDB, forward behind it, right spine slot (upper row), right column, across above the ESP32',
              conductors=[{'wire': 1, 'from': '+', 'to': '+', 'awg': 16, 'colour': 'red', 'signal': '12 V motors'}, {'wire': 2, 'from': '-', 'to': '-', 'awg': 16, 'colour': 'black', 'signal': 'GND'}])
        # O2 -> 5 V buck VIN (spine back), O3 -> servo buck VIN (left cheek); both through the right upper cheek slot
        bk_in = (px0 + 22.0 - 8.0, sp_b - 6.0, P['pi_z0'] + 44.0 + 12.7)          # D36V50F5 VIN/GND pads (top edge)
        c0 = xt30(1)
        cable(h, 'O02', 'PDB out 2 -> Pi 5 V buck VIN', 'PDB XT30 out 2', 'D36V50F5 VIN / GND', [(1, '+', 'VIN', 18, 'red', '12 V'), (2, '-', 'GND', 18, 'black', 'GND')],
              [c0, add(c0, (0, 0, 8)), (91.0, c0[1] - 7.5, 236.0), (91.0, -28.0, ucz), (91.0, ucy['O02'], ucz), ucs(1, 'O02', -6),
               (bk_in[0], ucy['O02'], ucz), (bk_in[0], sp_b - 8, ucz), (bk_in[0], sp_b - 8, bk_in[2] + 6), bk_in],
              'red', route='right upper cheek slot, across the bay behind the bearing housing, forward beside it, down the spine back')
        sb_in = (lcx - 3.0, -40.0, pt + 150.0 + 17.8)
        c0 = xt30(2)
        cable(h, 'O03', 'PDB out 3 -> servo 6 V buck VIN', 'PDB XT30 out 3', 'D36V28F6 VIN / GND', [(1, '+', 'VIN', 20, 'red', '12 V'), (2, '-', 'GND', 20, 'black', 'GND')],
              [c0, add(c0, (0, 0, 11)), (95.0, c0[1] - 8, 238.0), (95.0, -40.0, 238.0), (88.0, ucy['O03'], ucz), ucs(-1, 'O03', 4),
               (sb_in[0], ucy['O03'], ucz - 8), (sb_in[0], sb_in[1], sb_in[2] + 12), (sb_in[0], sb_in[1], sb_in[2] + 3), sb_in],
              'red', route='right upper cheek slot, across the bay, left upper cheek slot, down the left side channel')
    # =============================================================== Pi 5 power: 5 V buck -> Pi USB-C (top-left, pose B)
    usbc = PI(11.2, 0.0)                     # Pi USB-C opening (top edge)
    if want('P'):
        plug = H2(h, 'right-angle USB-C power plug (DIY, 5 A)', (usbc[0], pyf + 3.2, usbc[2] + 5.0), Z, X, (8.0, 12.0, 7.0), 'black', 'P01')
        bk_out = (px0 + 22.0 + 6.0, sp_b - 6.0, P['pi_z0'] + 44.0 + 12.7)
        cable(h, 'P01', 'Pi 5 V: buck VOUT -> Pi USB-C', 'D36V50F5 VOUT / GND', 'Pi 5 USB-C (right-angle plug, 5 A mode)',
              [(1, 'VOUT', 'VBUS', 18, 'red', '5.1 V'), (2, 'GND', 'GND', 18, 'black', 'GND')],
              [bk_out, add(bk_out, (0, 0, 7)), (cs['P01'][0], sp_b - 4, cs['P01'][1]), (cs['P01'][0], sp_f + 4, cs['P01'][1]), (usbc[0] + 14, pyf + 6, usbc[2] + 12),
               (usbc[0] + 6, pyf + 3.2, usbc[2] + 5.0)],
              'red', route='up the spine back, centre slot, down to the plug; set usb_max_current_enable=1 on the Pi')
    # =============================================================== ESP32 <-> Pi: USB-A (Pi USB3) to right-angle USB-C (ESP32)
    if want('U'):
        ua = PI(88.1, 29.1)                       # Pi USB 3 stack opening (right edge)
        H2(h, 'USB-A plug (Pi USB 3)', (ua[0] + 14.0, ua[1] + 6.5, ua[2]), X, Y, (28.0, 12.0, 6.5), 'black', 'U01')
        ec = (83.0, P['spine_y'] + 12.2, P['drv_z'] + 20 + 4.5 - 4.45)
        H2(h, 'right-angle USB-C plug (ESP32 native USB)', (ec[0] + 4.0, ec[1] + 4.0, ec[2]), X, Z, (8.0, 12.0, 6.5), 'black', 'U01')
        cable(h, 'U01', 'USB 2.0 data + 5 V: Pi USB 3 -> ESP32-S3 USB', 'Pi 5 USB-A (USB 3 stack, lower)', 'ESP32-S3-DevKitC-1 USB-C (native USB)',
              [(1, 'VBUS', 'VBUS', 28, 'red', '5 V'), (2, 'D+', 'D+', 28, 'green', 'D+'), (3, 'D-', 'D-', 28, 'white', 'D-'), (4, 'GND', 'GND', 28, 'black', 'GND')],
              [(ua[0] + 28.0, ua[1] + 6.5, ua[2]), (73.5, 60.0, ua[2] - 5), (73.5, 63.0, 124.0), (ec[0] + 4, ec[1] + 10, ec[2] + 14), (ec[0] + 4, ec[1] + 10, ec[2])],
              'black', od=3.5, stock='bought 15 cm USB-A to right-angle USB-C cable; slack in an S in the right column', route='right column (inboard of the power column)')
    # =============================================================== Pi GPIO harness (2x20 Dupont housing on the AI HAT+ 2 pass-through header)
    gh = (px0 + 32.5, hat_hdr_top + 7.0, pz_top - 52.5)        # housing centre; wires leave at y hat_hdr_top + 14
    gy = hat_hdr_top + 14.15                                   # wires start 0.15 mm off the housing face (no wire-wire contact)
    pinx = lambda n: px0 + 8.3 + ((n + 1) // 2 - 1) * 2.54
    if want('G'):
        H2(h, '2x20 Dupont housing (21 of 40 populated) on the HAT GPIO header', gh, Y, X, (14.0, 51.0, 5.1), 'black', 'G')
        # lidar branch: LD19 (ZH1.5-4 on its base) <- pins 4 5V, 6 GND, 10 RXD ; LD19 PWM tied to GND at the plug
        ld = (P['ld_x'], P['ld_y'], P['ld_z'])
        H2(h, 'ZH1.5 4-pin plug on the LD19 base', (ld[0], ld[1], ld[2] - 3.0), Z, X, (6.0, 7.5, 3.5), 'white', 'G01')
        g1 = (pinx(6), gy, gh[2])
        cable(h, 'G01', 'lidar: Pi GPIO -> LD19 (custom ZH1.5-4 to Dupont)', 'Pi GPIO pins 4 / 6 / 10 (+ GND jumper to LD19 PWM)', 'LD19 ZH1.5 socket (1 Tx, 2 PWM, 3 GND, 4 P5V)',
              [(1, '10 RXD (GPIO15)', '1 Tx', 26, 'yellow', 'lidar data 230400 Bd'), (2, '6 GND (bridge)', '2 PWM', 26, 'blue', 'PWM held low = internal speed control'),
               (3, '6 GND', '3 GND', 26, 'black', 'GND'), (4, '4 5V', '4 P5V', 26, 'red', '5 V 180 mA')],
              [g1, add(g1, (0, 3, 0)), (g1[0], gy + 4.0, gh[2] - 5.7), (-80.0, gy + 4.0, gh[2] - 5.7), (-90.0, 82.0, 150.0), (-90.0, 52.0, 164.0), (-90.0, 36.0, 164.0),
               (lch['G01'], 28.0, 180.0), (lch['G01'], 24.0, 225.0), (lch['G01'], -34.0, 225.0), (lch['G01'], ucy['G01'], 234.0), ucs(-1, 'G01', 6), ucs(-1, 'G01', -6),
               (-64.0, ucy['G01'], ucz - 6), (-44.0, -46.0, 205.0), (-44.0, -48.5, 194.0), (-44.0, P['rear_y'] - 7, 191.0), (ld[0], P['rear_y'] - 7, 200.0),
               (ld[0], ld[1], 230.0), (ld[0], ld[1], ld[2] - 6)],
              'black', route='down the front loom, left column, left spine slot, left channel, left upper cheek slot, rear-plate speaker slot (beside A01), up behind the rear plate through the deck hole under the LD19')
        # audio branch: MAX98357A (left cheek) <- 2 5V, 14 GND, 12 BCLK, 35 LRC, 40 DIN
        amp = (lcx - 1.0, 20.0, pt + 150.0 + 19.3)
        g2 = (pinx(12), gy, gh[2])
        cable(h, 'G02', 'I2S out: Pi GPIO -> MAX98357A', 'Pi GPIO pins 2 / 14 / 12 / 35 / 40', 'MAX98357A Vin / GND / BCLK / LRC / DIN (header, soldered)',
              [(1, '2 5V', 'Vin', 24, 'red', '5 V'), (2, '14 GND', 'GND', 24, 'black', 'GND'), (3, '12 GPIO18', 'BCLK', 28, 'yellow', 'I2S BCLK (spliced to the mic)'),
               (4, '35 GPIO19', 'LRC', 28, 'green', 'I2S LRCLK (spliced to the mic)'), (5, '40 GPIO21', 'DIN', 28, 'blue', 'I2S data out')],
              [g2, add(g2, (0, 3, 0)), (g2[0], gy + 3.0, gh[2] - 9.5), (-40.0, gy + 1.5, gh[2] - 9.5), (-72.0, gy + 1.5, gh[2] - 9.5), (-85.6, 78.0, 150.0), (-85.6, 52.0, 164.0), (-85.6, 36.0, 164.0),
               (-86.6, amp[1] + 12, amp[2] + 5), (amp[0], amp[1] + 3, amp[2] + 5), (amp[0], amp[1], amp[2] + 2)],
              'black', route='front loom, left column, left spine slot, left channel')
        # CPX power: 2 5V + 30 GND -> CPX JST-PH battery input (5 V into the 3.5-6 V input)
        cj = (0.0, 87.0 - 3.0, P['cpx_z'] - 19.0)
        H2(h, 'PH 2-pin plug (CPX battery input)', cj, Y, X, (6.0, 5.8, 4.5), 'white', 'G03')
        g3 = (pinx(30), gy, gh[2])
        cable(h, 'G03', 'CPX power: Pi GPIO 5 V -> CPX battery JST', 'Pi GPIO pins 2 (spliced) / 30', 'CPX JST-PH 2 (1 +, 2 GND)',
              [(1, '2 5V (splice)', '1 +', 24, 'red', '5 V'), (2, '30 GND', '2 GND', 24, 'black', 'GND')],
              [g3, add(g3, (0, 3, 0)), (-6.5, gy + 3.0, gh[2] + 7), (-6.5, gy + 3.0, 203.0), (-6.5, cj[1] - 14, cj[2]), (cj[0], cj[1] - 14, cj[2]),
               (cj[0], cj[1] - 3, cj[2])],
              'black', route='front loom, straight up in front of the HAT (left of the camera FFC), back under the CPX')
        # head branch: TFT (8) + mic (6), both soldered at the head end; up the right of the HAT to the top lane, centre slot, pan shaft
        g4 = (pinx(19), gy, gh[2])
        tft = [(1, '17 3V3', 'Vin', 28, 'red', '3.3 V'), (2, '20 GND', 'GND', 28, 'black', 'GND'), (3, '23 SCLK', 'SCK', 28, 'yellow', 'SPI0 SCLK'),
               (4, '19 MOSI', 'SI', 28, 'blue', 'SPI0 MOSI'), (5, '24 CE0', 'TCS', 28, 'white', 'SPI0 CE0'), (6, '22 GPIO25', 'D/C', 28, 'green', 'data/command'),
               (7, '13 GPIO27', 'RST', 28, 'grey', 'reset'), (8, '15 GPIO22', 'Lite', 28, 'orange', 'backlight PWM')]
        mic = [(1, '1 3V3', 'VDD', 28, 'red', '3.3 V'), (2, '9 GND', 'GND', 28, 'black', 'GND'), (3, '12 GPIO18 (splice)', 'SCK', 28, 'yellow', 'I2S BCLK'),
               (4, '35 GPIO19 (splice)', 'WS', 28, 'green', 'I2S LRCLK'), (5, '38 GPIO20', 'SD', 28, 'blue', 'I2S data in'), (6, '9 GND (splice)', 'L/R', 28, 'black', 'left channel')]
        # shaft geometry
        sy0, shz0 = P['pan_y'], P['shaft_z0']
        ttop = P['tilt_z'] + 13.0                      # turret top 338
        cb0 = P['head_z0'] - 5.0                       # crossbar bottom 348
        hz0 = P['head_z0']
        for cid, nm, conds, sx, sy_, dest in (('G04', 'TFT', tft, 9.0, 2.0, (11.0, 43.6, hz0 + 21.0)), ('G05', 'mic', mic, 9.0, -3.5, (P['mic_x'], 45.5, hz0 + 37.0))):
            d = bundle_od(conds)
            g = (pinx(19 if cid == 'G04' else 37), gy, gh[2])
            cx_, cz_ = cs[cid]
            if cid == 'G04':      # under the GPIO housing exits, right to x 13.8, up in front of the HAT
                base = [g, add(g, (0, 3, 0)), (g[0], gy + 3.0, gh[2] - 6.5), (8.0, gy + 3.0, gh[2] - 6.5), (13.8, gy + 3.0, gh[2] + 2), (13.8, gy + 3.0, 194.0),
                        (cx_, 78.0, cz_), (cx_, sp_b, cz_), (11.3, 27.6, cz_ + 0.6), (sx, sy0 + sy_, shz0 - 6), (sx, sy0 + sy_, shz0 + 2)]
            else:
                base = [g, add(g, (0, 3, 0)), (10.0, gy + 3.0, gh[2] + 6), (10.0, gy + 3.0, 206.0), (cx_, 86.0, cz_), (cx_, sp_b, cz_), (13.5, 30.0, cz_),
                        (13.5, sy0 + sy_, cz_ - 0.8), (sx, sy0 + sy_, shz0 - 2.4), (sx, sy0 + sy_, shz0 + 2)]
            fixed_ln = cable(h, cid + 'a', '%s cable, fixed part (to the shaft bottom tie)' % nm, 'Pi GPIO (Dupont housing)', 'pan shaft bottom tie', conds, base,
                             'black', route='front loom, up in front of the HAT, top lane, centre slot (right, stacked), into the pan shaft')
            h.tie(cid, (sx, sy0 + sy_, shz0 - 1.5), d, Z)
            # head slot (x -8..16): FFC x -2.55..8.95, TFT bundle x 10.9, mic bundle x 14.3; y >= 26 at the head floor (the back
            # shell half is not slotted), so both bundles change from y 23.5 to y ~28 in the tilt loop
            xt, yh = (10.9, 28.0) if cid == 'G04' else (14.3, 27.6)
            stop = P['shaft_z0'] + 89.5                      # above the shaft top (z 315): lateral moves happen in the turret
            if cid == 'G04':
                shaft = [(sx, sy0 + sy_, shz0 + 2), (sx, sy0 + sy_, stop), (xt, sy0 + 3.5, stop + 10.5), (xt, sy0 + 3.5, ttop + 1)]
            else:                 # out to x 14.3 first, then forward: passes behind/right of the TFT bundle
                shaft = [(sx, sy0 + sy_, shz0 + 2), (sx, sy0 + sy_, stop), (xt, sy0 - 2.5, stop + 6.5), (xt, sy0 + 3.5, stop + 14.5), (xt, sy0 + 3.5, ttop + 1)]
            cable(h, cid + 'b', '%s cable in the pan shaft + turret (twist span, rest pose)' % nm, 'shaft bottom tie', 'turret top slot clamp', conds, shaft, 'black',
                  moving=True, note='pan twist +-90 deg over the shaft length')
            # rolling U-loop folded back toward the rear inside the turret-to-crossbar gap (see w_flex.py); legs kept one bundle
            # radius + 0.2 mm off the turret top (338) and the crossbar (348), U radius ~2.9 mm (> bundle radius: a valid pipe)
            r_ = d / 2.0
            zlo, zhi = ttop + r_ + 0.5, cb0 - r_ - 0.2
            loop = [(xt, sy0 + 3.5, ttop - 1.0), (xt, sy0 + 3.5, zlo), (xt, sy0 - 10.0, zlo), (xt, sy0 - 10.0, zhi), (xt, yh, zhi), (xt, yh, cb0 + 1.0)]
            cable(h, cid + 'c', '%s cable across the tilt joint (rest pose)' % nm, 'turret top slot', 'crossbar slot', conds, loop, 'black', moving=True,
                  R=3.0, note='tilt -35..45 deg: rolling U-loop in the 10 mm turret-to-crossbar gap; U radius ~3 mm (below the 10x rule: use high-flex silicone)')
            if cid == 'G04':      # up behind the head-frame plate, forward between the plate and the camera FFC band, over the band to the TFT pads
                head = [(xt, yh, cb0 - 0.5), (xt, yh, hz0 + 9), (xt, 36.8, hz0 + 11), (xt, 36.8, dest[2]), (dest[0], dest[1] - 0.2, dest[2])]
            else:                 # up behind the head-frame plate, left over the frame web, forward to the INMP441 pads
                head = [(xt, yh, cb0 - 0.5), (xt, yh, hz0 + 27), (dest[0], yh, hz0 + 27), (dest[0], 40.0, dest[2] - 4), (dest[0], dest[1] - 3, dest[2]), dest]
            cable(h, cid + 'd', '%s cable in the head' % nm, 'crossbar slot', ('TFT header pads (soldered)' if cid == 'G04' else 'INMP441 pads (soldered)'), conds, head, 'black',
                  group='tilt')
    # =============================================================== camera FFC: Pi CAM/DISP0 -> Camera Module 3 (up the shaft)
    if want('K'):
        c0 = PI(54.9, 8.4, 3.0)                       # CAM/DISP0 connector top (u 54.9 per the drawing)
        sy0, shz0 = P['pan_y'], P['shaft_z0']
        ttop, cb0, hz0 = P['tilt_z'] + 13.0, P['head_z0'] - 5.0, P['head_z0']
        yfs = sy0 + 6.6                               # FFC plane in the shaft (in front of the tilt servo)
        cmx = P['cam_x']
        kx = 3.2                                      # FFC centre x (x -2.55..8.95: clear of the tilt lead at x -4, TFT/mic bundles at x 10.9 / 14.3)
        w = [((c0[0], c0[1], c0[2]), Z), ((c0[0], 86.0, c0[2]), Z), ((kx, 86.0, c0[2]), X), ((kx, 86.0, zK), X),
             ((kx, sp_b - 6, zK), X), ((kx, yfs, zK), X), ((kx, yfs, shz0 + 2), X)]
        flatcable(h, 'K01a', 'camera FFC, fixed part', 'Pi 5 CAM/DISP0 (22-pin 0.5 mm)', 'pan shaft bottom tie', [(1, '22-pin', '15-pin', 0, 'FFC', 'MIPI CSI-2 2-lane')],
                  w, 11.5, 0.3, route='up through the HAT cut-out, 45 deg fold to vertical, top lane, centre slot, into the pan shaft',
                  stock='Raspberry Pi 5 camera cable 500 mm (22 to 15 pin); slack folded flat on the spine back')
        w2 = [((kx, yfs, shz0 + 2), X), ((kx, yfs, ttop + 1), X)]
        flatcable(h, 'K01b', 'camera FFC in the shaft + turret (twist span)', 'shaft bottom tie', 'turret top slot', [(1, '', '', 0, 'FFC', '')], w2, 11.5, 0.3, moving=True)
        w3 = [((kx, yfs, ttop + 0.5), X), ((kx, yfs, ttop + 2.5), X), ((kx, sy0 - 4.0, ttop + 2.5), X), ((kx, sy0 - 4.0, cb0 - 2.5), X),
              ((kx, sy0 + 8.0, cb0 - 2.5), X), ((kx, sy0 + 8.0, cb0 - 0.5), X)]
        flatcable(h, 'K01c', 'camera FFC across the tilt joint (rest pose)', 'turret top slot', 'crossbar slot', [(1, '', '', 0, 'FFC', '')], w3, 11.5, 0.3, moving=True)
        w4 = [((kx, sy0 + 8.0, cb0 - 1), X), ((kx, sy0 + 8.0, hz0 + 6), X), ((kx, 40.0, hz0 + 8.5), X), ((kx, 40.0, hz0 + 13), Z), ((cmx - 6, 40.0, hz0 + 13), Z),
              ((cmx, 36.0, hz0 + 13), Z), ((cmx, 36.0, hz0 + 25.4), X)]      # band at y 40: room for the TFT bundle between it and the head-frame plate
        flatcable(h, 'K01d', 'camera FFC in the head', 'crossbar slot', 'Camera Module 3 (15-pin 1 mm)', [(1, '', '', 0, 'FFC', '')], w4, 11.5, 0.3, group='tilt')
    # =============================================================== PCIe FFC: Pi 5 -> AI HAT+ 2 (stock)
    if want('Q'):
        q0 = PI(2.8, 30.0, 1.2)
        w = [((q0[0], q0[1], q0[2]), Z), ((q0[0], q0[1] + 6, q0[2]), Z), ((px0 - 3.0, q0[1] + 6, q0[2]), Z), ((px0 - 3.0, pyf + P['hat_so'] + 5, q0[2]), Z),
             ((px0 + 2.6, pyf + P['hat_so'] + 5, q0[2]), Z), ((px0 + 2.6, pyf + P['hat_so'] + 2, q0[2]), Z)]
        flatcable(h, 'Q01', 'PCIe FFC Pi 5 -> AI HAT+ 2', 'Pi 5 PCIe FFC (16-pin)', 'AI HAT+ 2 PCIe FFC', [(1, '16-pin', '16-pin', 0, 'FFC', 'PCIe Gen 2/3 x1')],
                  w, 10.7, 0.3, stock='included with the AI HAT+ 2', route='wraps round the left edge of the HAT', R=3.0)
    # =============================================================== drive: 4x JGB37 (PH2.0-6 on the encoder) -> DRV terminals + ESP32
    ecb = lambda x: (x, P['spine_y'] + 4.5, ez0 - 1.0)          # ESP32 carrier bottom edge exit
    ebk = lambda dz=0.0: (40.0, sp_b - 3.0, P['drv_z'] + 15.0 + dz)   # out of the carrier back, through the spine slot behind it
    term = lambda i: (dxc + (i - 1.5) * 16.5, dpy + 10.0, dz0 + 4.75)  # DRV screw-terminal wire entry (front face)
    enc_z = 79.5                                                    # encoder lane height (under the terminal block, above the motors)
    enc_lane = {'MC': (55.4, 23.5), 'MD': (58.6, 27.0), 'MA': (61.8, 30.5), 'MB': (65.0, 34.0)}   # (lane y, carrier exit x)
    # carrier-back slot (spine x 25..55, z 92..102): one flat row at z 97, each cable at its own x
    cbz = 97.0
    cbx = {'C04': 27.0, 'B03': 30.0, 'C03': 33.2, 'C02': 36.6, 'B04': 39.8, 'C05': 42.8, 'V04': 46.2}   # left-side cables at the left end
    cb = lambda cid: (cbx[cid], sp_b - 3.0, cbz)
    zX = 108.5                                                      # left-side cables cross over the battery pack (above the slide-out path)
    if want('M'):
        enc_x = P['gb_face'] - P['gb_len'] - P['can_len'] - P['cap_len'] - P['enc_len']     # encoder rear face |x| 31.9
        mot = [('MA', 'FL', -1, 1, 2), ('MB', 'FR', 1, 1, 3), ('MC', 'RL', -1, -1, 0), ('MD', 'RR', 1, -1, 1)]
        six = lambda tag: [(1, 'M+ (red)', 'OUT1', 24, 'red', 'motor +'), (6, 'M- (white)', 'OUT2', 24, 'white', 'motor -'),
                           (2, 'GND (black)', 'GND', 26, 'black', 'encoder GND'), (5, 'VCC (blue)', '3V3', 26, 'blue', 'encoder 3.3 V'),
                           (3, 'A (yellow)', 'ENC_%s_A' % tag, 26, 'yellow', 'Hall A'), (4, 'B (green)', 'ENC_%s_B' % tag, 26, 'green', 'Hall B')]
        for cid, tag, sx, sy, ti in mot:
            face = (sx * enc_x, sy * P['wheel_y'], P['motor_z'] + 9.0)
            ex = h.housing('PH 6-pin plug on %s encoder' % tag, face, (-sx, 0, 0), Y, (7.5, 13.9, 4.5), 'white', cable=cid)
            t = term(ti)
            if sy > 0:            # over the bulkhead top, up and across to the terminal (in front of the block)
                pts = [ex, (ex[0] - sx * 6, ex[1], ex[2] + 2.5), (ex[0] - sx * 10, 74.0, zU), (t[0], 76.0, t[2]), t]
            else:                 # up off the encoder plug (clear of the sled wall), over the motor, bay floor, low spine slot, then
                ls = low_slot(sx) # under the terminal block (MD lane y 59 z 70) and up in front of its terminal
                pts = [ex, (ex[0] - sx * 1.4, ex[1], ex[2] + 3.5), (sx * 30.0, -66.0, 76.0), (sx * 52, -45.0, 74.0), (sx * 50, 20.0, 64.0), (ls[0], sp_b - 4, ls[2]),
                       (ls[0], sp_f, ls[2])]
                if sx < 0:
                    pts += [(ls[0], 50.0, 56.0), (-60.0, 53.0, 62.0), (-64.5, 60.0, 74.0), (-66.0, 65.0, 81.5), (t[0], 69.5, t[2]), t]
                else:
                    pts += [(ls[0], 50.0, 58.0), (ls[0] - 2, 59.0, 70.0), (t[0] + 2.2, 59.0, 70.0), (t[0], 61.0, 76.0), (t[0], 68.0, 81.5), (t[0], 69.5, t[2]), t]
            ln = cable(h, cid, 'motor %s cable to the DRV terminal (6 x 24/26 AWG)' % tag, 'JGB37 %s encoder PH2.0-6' % tag, 'DRV8874 #%d screw terminal (OUT1/OUT2)' % (ti + 1),
                       six(tag), pts, 'black', route=('straight up between the front motors' if sy > 0 else 'over the rear motor, along the bay floor, low spine slot, under the terminal block'))
            # the 4 encoder wires split at the terminal and run under the terminal block in their own lane (rear-most lane = left-most
            # terminal, so no bundle crosses another), then back up to the ESP32 carrier bottom edge (right-most exit = front-most lane)
            e4 = six(tag)[2:]
            ly, ex_ = enc_lane[cid]
            e0 = (t[0], t[1] + 2.9, t[2] + 0.25)                      # split point just in front of the terminal entry
            if cid == 'MB':       # front-most lane: straight down-and-over into it
                ep = [e0, (t[0] + 4.0, ly, enc_z)]
            else:                 # drop in front of the block, then diagonally back under it into the lane
                ep = [e0, (t[0], e0[1], enc_z + 1.0), (t[0] + 8.0, ly, enc_z)]
            ep += [(ex_ - 5.0, ly, enc_z), (ex_, ly - 3.5, enc_z + 3.0), ecb(ex_)]
            cable(h, cid + 'e', 'motor %s encoder wires to the ESP32' % tag, 'split at the DRV terminal', 'ESP32 carrier (3V3, GND, ENC A/B)', e4, ep, 'black',
                  route='under-board lane (own lane under the terminal block)')
        # DRV logic: XH-10 (perfboard) <- ESP32 carrier left end
        xh = (dxc - 10.0, dpy + 7.0 + 4.0, dz0 + 36.0)
        H2(h, 'XHP-10 plug (DRV logic)', (xh[0], xh[1] - 2.0, xh[2]), Y, X, (4.0, 27.5, 5.7), 'white', 'L01')
        logic = [(k + 1, n, 'GPIO', 28, c, sig) for k, (n, c, sig) in enumerate([('EN1', 'yellow', 'PWM motor A'), ('PH1', 'green', 'DIR motor A'), ('EN2', 'yellow', 'PWM B'),
                 ('PH2', 'green', 'DIR B'), ('EN3', 'yellow', 'PWM C'), ('PH3', 'green', 'DIR C'), ('EN4', 'yellow', 'PWM D'), ('PH4', 'green', 'DIR D'),
                 ('3V3', 'red', 'logic 3.3 V'), ('GND', 'black', 'GND')])]
        cable(h, 'L01', 'DRV logic: ESP32 -> perfboard XH-10', 'ESP32 carrier left end', 'DRV perfboard JST-XH 10', logic,
              [(14.9, P['spine_y'] + 5.0, ez1 - 6), (12.0, 62.0, ez1 + 4), (-8.0, 68.0, dz0 + 46), (xh[0] + 10, 70.0, xh[2] + 6), (xh[0], xh[1] + 4, xh[2]), xh], 'black',
              route='over the DRV XT30 plug')
        # ESP32 <-> servo buck Y-harness signals, via the carrier back slot and the left cheek loom slot
    # =============================================================== bumpers: 4x D2F-01L (solder pins) -> ESP32
    if want('B'):
        sw = lambda sx, sy: (sx * 42.0, sy * (P['shell_y'] - P['pwall'] - 2.9 - 3.2 - 2.9 - 2.9), P['plate_top'] + 3.25)
        for cid, sx, sy, nm in (('B01', -1, 1, 'front left'), ('B02', 1, 1, 'front right'), ('B03', -1, -1, 'rear left'), ('B04', 1, -1, 'rear right')):
            s0 = sw(sx, sy)
            k = int(cid[-1])
            conds = [(1, 'COM', 'GND', 28, 'black', 'GND'), (2, 'NO', 'BUMP%d' % k, 28, 'white', 'bumper %d (pull-up on the ESP32)' % k)]
            if sy > 0:            # under the front motor, across in front of the sled nose at the floor, up beside the right front motor
                xr_ = 52.0 if sx < 0 else 55.5
                pts = [s0, (s0[0], s0[1] - 6, s0[2]), (s0[0], 58.4, s0[2] + 0.15)]
                if sx < 0:
                    pts += [(s0[0] + 8, 57.5, 43.0), (xr_ - 6, 57.5, 43.0), (xr_, 57.5, 49.0)]
                else:
                    pts += [(s0[0] + 8, 57.6, s0[2] + 0.55), (xr_, 57.6, 46.0)]
                pts += [(xr_, 57.5, 80.0), (xr_, 51.0, 84.0), ecb(xr_)]
            elif sx > 0:          # along the floor, up beside the right low slot, into the carrier-back row
                pts = [s0, (s0[0], s0[1] + 6, s0[2]), (54.0, -50.0, 38.2), (54.0, 18.0, 38.2), (56.0, 24.0, 46.0), (56.0, 26.0, 92.0), (cb(cid)[0], 32.0, cbz), cb(cid)]
            else:                 # along the left floor, up the left side, over the battery pack, into the carrier-back row
                pts = [s0, (s0[0], s0[1] + 6, s0[2]), (-54.0, -50.0, 38.2), (-54.0, 18.0, 38.2), (-56.0, 24.0, 46.0), (-56.0, 24.0, zX - 8), (-50.0, 24.0, zX),
                       (cb(cid)[0] - 3.6, 24.0, zX), (cb(cid)[0], 28.0, zX - 4), (cb(cid)[0], 33.0, cbz), cb(cid)]
            cable(h, cid, 'bumper %s (D2F-01L)' % nm, 'D2F-01L COM/NO pins (soldered; terminals face inward)', 'ESP32 carrier', conds, pts, 'black',
                  route=('under the front motor, along the floor in front of the sled nose, up to the carrier bottom edge' if sy > 0 else
                         ('along the plate, carrier back slot' if sx > 0 else 'along the plate, up the left side, over the battery pack, carrier back slot')))
    # =============================================================== cliff sensors 4x VL53L0X (pads soldered) + BNO085 + INA226 (I2C, ESP32)
    if want('C'):
        holes = {'front': (24.0, 72.0), 'right': (62.0, 14.0), 'rear': (40.0, -40.0), 'left': (-62.0, 14.0)}
        pos = {'front': (0.0, P['tof_r']), 'right': (P['tof_r'], 0.0), 'rear': (0.0, -P['tof_r']), 'left': (-P['tof_r'], 0.0)}
        zpad = P['plate_z'] - 1.6 - 0.6
        for k, nm in enumerate(('front', 'right', 'rear', 'left')):
            cid = 'C%02d' % (k + 1)
            hx, hy = holes[nm]
            sx, sy = pos[nm]
            pad = (sx + (8.0 if nm != 'left' else -8.0) * (1 if nm in ('front', 'rear') else 0), sy + (8.0 if nm in ('right', 'left') else 0) * 0, zpad)
            pad = (sx * 0.86 + (hx - sx) * 0.0, sy * 0.86, zpad) if nm != 'front' else (11.5, 73.0, zpad)
            conds = [(1, 'VIN', '3V3', 28, 'red', '3.3 V'), (2, 'GND', 'GND', 28, 'black', 'GND'), (3, 'SCL', 'SCL', 28, 'yellow', 'I2C SCL (bus)'),
                     (4, 'SDA', 'SDA', 28, 'blue', 'I2C SDA (bus)'), (5, 'XSHUT', 'XSHUT%d' % (k + 1), 28, 'white', 'address select at boot')]
            if nm == 'front':     # up beside the bulkhead, back over the encoder lanes to the carrier bottom edge (left-most exit)
                pts = [pad, (hx, hy, zpad), (hx, hy, P['plate_top'] + 1), (21.0, hy, P['plate_top'] + 8), (21.0, hy, 82.0), (19.5, 60.0, 85.5), ecb(19.5)]
            elif nm == 'right':
                pts = [pad, (hx, hy, zpad), (hx, hy, P['plate_top'] + 4), (hx, hy, cbz - 3), (cb(cid)[0], 30.0, cbz), cb(cid)]
            elif nm == 'rear':
                pts = [pad, (hx, hy, zpad), (hx, hy, P['plate_top'] + 4), (hx, 20.0, cbz - 5), (cb(cid)[0], 30.0, cbz), cb(cid)]
            else:                 # left: up the left side, over the battery pack (front lane), into the carrier-back row
                pts = [pad, (hx, hy, zpad), (hx, hy, P['plate_top'] + 4), (hx, 16.0, zX - 18), (hx + 2, 27.4, zX),
                       (cb(cid)[0] - 2.6, 27.4, zX), (cb(cid)[0], 31.0, zX - 5.5), (cb(cid)[0], 34.0, cbz), cb(cid)]
            cable(h, cid, 'cliff sensor %s (VL53L0X 3317)' % nm, 'VL53L0X pads VIN/GND/SCL/SDA/SHDN (soldered)', 'ESP32 carrier', conds, pts, 'black',
                  note='runs 8 mm under the plate in a groove of the printed pocket to the plate hole',
                  route='plate hole, then %s' % ('front lane' if nm == 'front' else ('over the battery pack, carrier back slot' if nm == 'left' else 'carrier back slot')))
        bno = (0.0, P['spine_y'] - P['ply_t'] - 5.0 - 1.6, P['plate_top'] + 82.0 + 2.0)
        cable(h, 'C05', 'IMU: ESP32 -> BNO085 (I2C + INT + RST)', 'ESP32 carrier back', 'BNO085 header VIN/GND/SCL/SDA/INT/RST (soldered)',
              [(1, '3V3', 'VIN', 28, 'red', '3.3 V'), (2, 'GND', 'GND', 28, 'black', 'GND'), (3, 'SCL', 'SCL', 28, 'yellow', 'I2C'), (4, 'SDA', 'SDA', 28, 'blue', 'I2C'),
               (5, 'GPIO', 'INT', 28, 'white', 'interrupt'), (6, 'GPIO', 'RST', 28, 'grey', 'reset')],
              [cb('C05'), (cb('C05')[0], sp_b - 5.0, cbz + 9), (12.0, bno[1] - 2.0, bno[2]), (bno[0], bno[1] - 1.5, bno[2])], 'black', route='carrier back slot')
        ina = (pdx + 1.0, -5.0 + 9.0 + 13.0, pdz0 + 12.0)
        cable(h, 'C06', 'power monitor: ESP32 -> INA226 (I2C)', 'ESP32 carrier right end', 'INA226 header VCC/GND/SCL/SDA (soldered)',
              [(1, '3V3', 'VCC', 28, 'red', '3.3 V'), (2, 'GND', 'GND', 28, 'black', 'GND'), (3, 'SCL', 'SCL', 28, 'yellow', 'I2C'), (4, 'SDA', 'SDA', 28, 'blue', 'I2C')],
              [(84.5, P['spine_y'] + 6, ez1 - 4), (89.4, P['spine_y'] + 6, ez1 + 3), (89.4, P['spine_y'] + 6, 148.0), (89.4, sp_f + 3, 161.7), (89.4, sp_b - 6, 161.7),
               (89.4, ina[1] + 7, 172.0), (89.4, ina[1] + 1.5, ina[2]), (ina[0] + 1.3, ina[1] - 1.0, ina[2])],
              'black', route='right column, right spine slot')
    # =============================================================== CPX watchdog link + kill line
    if want('W'):
        cz = P['cpx_z']
        a6, a1 = (21.0, 92.8, cz + 8.0), (-21.0, 92.8, cz - 8.0)
        cable(h, 'W01', 'heartbeat: ESP32 TX -> CPX A6/RX', 'ESP32 carrier right end (UART1 TX)', 'CPX pad A6 / RX (soldered)',
              [(1, 'TX', 'A6 RX', 28, 'white', 'heartbeat UART'), (2, 'GND', 'GND pad', 28, 'black', 'reference')],
              [(84.0, P['spine_y'] + 8, ez1 - 2), (84.0, P['spine_y'] + 8, ez1 + 3), (78.5, 56.0, ez1 + 10), (78.5, 56.0, 196.0), (34.0, 90.0, cz), (a6[0] + 4, 91.0, a6[2]), a6], 'black', route='right column, beside the CPX bracket')
        drv_sl = (dxc + 20.0, dpy + 2.0, dz0 + 40.0)                 # nSLEEP bus at the board top edge, left of the XT30
        cable(h, 'W02', 'kill line: CPX A1 -> DRV8874 SLEEP (all four)', 'CPX pad A1 (soldered)', 'DRV perfboard nSLEEP bus', [(1, 'A1', 'nSLEEP', 28, 'red', 'motors enabled only while the CPX watchdog is fed')],
              [a1, (a1[0] - 4, 91.0, a1[2]), (-34.0, 90.0, cz - 14), (-48.0, 90.0, 150.0), (-46.0, 84.0, 136.0), (drv_sl[0], 74.0, 133.0), (drv_sl[0], drv_sl[1] + 4, drv_sl[2] + 3), drv_sl], 'red',
              route='down the left of the HAT stack (in front of it)')
    # =============================================================== servos: pan (under the deck) + tilt (in the turret, lead up the shaft)
    if want('V'):
        jr = lambda k: (xL - 1.0, -14.0 + 11.0 * k, P['plate_top'] + 172.0)       # JR male sockets of the servo Y harness (left channel)
        for k in range(2):
            H2(h, 'JR 3-pin male socket (servo Y harness %d)' % (k + 1), jr(k), Z, Y, (14.0, 8.0, 2.6), 'black', 'V03')
        sbo = (lcx - 3.0, -20.0, P['plate_top'] + 150.0 + 2.0)                    # servo buck VOUT/GND
        cable(h, 'V03', 'servo Y harness: 6 V buck -> 2 JR sockets', 'D36V28F6 VOUT / GND', '2x JR male socket (+6 V, GND)',
              [(1, 'VOUT', '+ (both)', 22, 'red', '6 V'), (2, 'GND', '- (both)', 22, 'black', 'GND')],
              [sbo, (sbo[0], sbo[1] + 3, sbo[2]), (xL - 1, jr(0)[1], jr(0)[2] - 14), (xL - 1, jr(0)[1], jr(0)[2] - 7)], 'red', route='left side channel')
        cable(h, 'V04', 'servo signals: ESP32 -> Y harness', 'ESP32 carrier back (2 PWM GPIO)', 'JR sockets signal pins',
              [(1, 'GPIO', 'pan S', 28, 'orange', 'pan PWM 50 Hz'), (2, 'GPIO', 'tilt S', 28, 'orange', 'tilt PWM 50 Hz')],
              [cb('V04'), (cb('V04')[0], sp_b - 7, cbz + 6), (cb('V04')[0], sp_b - 12, cbz + 15), (36.0, 22.0, 116.5), (-60.0, -25.0, 116.5), (-74.0, -25.0, P['frame_z1'] + 29), (xL + 2, -25.0, P['frame_z1'] + 31),
               (xL + 1, jr(1)[1], jr(1)[2] - 10), (xL, jr(1)[1], jr(1)[2] - 7.1)], 'black', route='carrier back slot, across the bay, left cheek loom slot')
        ps = (36.0, P['pan_y'] + 6.1, P['gear_z'] - 26.0)              # pan servo lead exit
        cable(h, 'V01', 'pan servo lead (stock MG90S 250 mm)', 'MG90S pan (lead exit)', 'JR socket 1', [(1, 'brown', '-', 26, 'brown', 'GND'), (2, 'red', '+', 26, 'red', '6 V'), (3, 'orange', 'S', 26, 'orange', 'PWM')],
              [ps, (ps[0], ps[1] + 6, ps[2]), (14.0, ps[1] + 6, ps[2]), (-16.0, 0.0, 214.0), (-60.0, ucy['V01'], ucz - 5), ucs(-1, 'V01', -6), ucs(-1, 'V01', 6),
               (-90.6, ucy['V01'] + 8, ucz - 10), (-90.6, jr(0)[1], jr(0)[2] + 16), (xL - 1, jr(0)[1], jr(0)[2] + 7.1)],
              'brown', od=2.6, stock='MG90S lead 250 mm (stock)', route='over the shelf front, under the shaft-bottom cables, across the bay, left upper cheek slot, left channel')
        sy0, shz0, ttop = P['pan_y'], P['shaft_z0'], P['tilt_z'] + 13.0
        tx = (-4.0, sy0 + 6.0, P['tilt_z'] - 4.0)                       # tilt servo lead exit (front end face of the lying servo)
        tl = [(1, 'brown', '-', 26, 'brown', 'GND'), (2, 'red', '+', 26, 'red', '6 V'), (3, 'orange', 'S', 26, 'orange', 'PWM')]
        cable(h, 'V02b', 'tilt servo lead in the turret + shaft (twist span)', 'MG90S tilt (in the turret)', 'shaft bottom tie', tl,
              [tx, (tx[0], sy0 + 9.8, tx[2]), (0.0, sy0 + 9.8, tx[2] - 12), (0.0, sy0 + 9.8, shz0 + 2)], 'brown', od=2.6, group='fixed', moving=True,
              note='turret end rides with the pan; +-90 deg twist over the shaft')
        h.tie('V02', (0.0, sy0 + 9.8, shz0 - 4), 2.6, Z)
        cable(h, 'V02a', 'tilt servo lead + 150 mm extension, fixed part', 'shaft bottom tie', 'JR socket 2', tl,
              [(0.0, sy0 + 9.8, shz0 + 2), (0.0, sy0 + 9.8, shz0 - 6), (-14.0, sy0 + 9.8, shz0 - 9), (-24.0, sy0 + 0, shz0 - 9), (-60.0, ucy['V02a'], ucz - 3), ucs(-1, 'V02a', -6), ucs(-1, 'V02a', 6),
               (-87.4, ucy['V02a'] + 8, ucz - 10), (-87.4, jr(1)[1], jr(1)[2] + 16), (xL, jr(1)[1], jr(1)[2] + 7.1)], 'brown', od=2.6, stock='MG90S lead 250 mm + JR extension 150 mm (joint in the bay)')
    # =============================================================== speaker: MAX98357A terminal -> 40 mm speaker tabs
    if want('A'):
        at = (lcx - 4.0, 11.0, P['plate_top'] + 150.0 + 6.0)
        tabs = (-45.0, -(P['shell_y'] - P['pwall'] - 23.0) + 2.0, P['body_top'] - 70.0)
        cable(h, 'A01', 'speaker: MAX98357A -> 40 mm speaker', 'MAX98357A 3.5 mm terminal (+/-)', 'Adafruit 3968 solder tabs (+/-)',
              [(1, '+', '+', 22, 'red', 'speaker +'), (2, '-', '-', 22, 'black', 'speaker -')],
              [at, (at[0], at[1] - 6, at[2]), (lch['A01'], at[1] - 12, at[2] + 2), (lch['A01'], ucy['A01'], at[2] + 2), (lch['A01'], ucy['A01'], 232.0), ucs(-1, 'A01', 6),
               ucs(-1, 'A01', -6), (-64.0, ucy['A01'], ucz - 6), (-36.0, -48.5, 205.0), (-36.0, -48.5, 194.0), (-36.0, P['rear_y'] - 8, 190.5),
               (tabs[0], tabs[1] + 8, tabs[2] - 4), tabs],
              'red', route='left channel, left upper cheek slot, rear-plate speaker slot, through the bracket magnet hole')
    return {'cables': h.cables, 'items': h.items}
