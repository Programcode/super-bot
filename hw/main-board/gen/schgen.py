"""Schematic generator for KiCad 10 hierarchical schematics.

Parts are placed in blocks; every used pin gets a 2.54 mm wire stub ending in a
local label, a hierarchical label (sheet port) or a power symbol. Unused pins get
a no-connect flag. Symbols are flattened from the KiCad libraries (or the project
library) and embedded in lib_symbols.
"""
import copy
import math
import os
import uuid as _uuid

from sexpr import Q, parse, dump, find, find1

KICAD_SYM = '/usr/share/kicad/symbols'
GRID = 1.27
STUB = 2.54
FONT = 1.27
CHAR_W = 1.0           # approx label character width at 1.27 mm font

NS = _uuid.UUID('5b2f6f0e-2a1c-4b7e-9a51-5b07c0ffee00')


def uid(*key):
    """Deterministic UUID so regeneration keeps stable ids (board links survive)."""
    return str(_uuid.uuid5(NS, '/'.join(str(k) for k in key)))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


# ---------------------------------------------------------------- libraries

class Libs:
    def __init__(self, project_libs):
        self.files = {}
        self.project_libs = project_libs      # {'sbot': path}
        self.cache = {}

    def _load(self, lib):
        if lib not in self.files:
            path = self.project_libs.get(lib) or os.path.join(KICAD_SYM, lib + '.kicad_sym')
            root = parse(open(path).read())
            self.files[lib] = {s[1]: s for s in find(root, 'symbol')}
        return self.files[lib]

    def get(self, lib_id):
        if lib_id in self.cache:
            return self.cache[lib_id]
        lib, name = lib_id.split(':', 1)
        syms = self._load(lib)
        s = copy.deepcopy(syms[name])
        ext = find1(s, 'extends')
        if ext:
            parent = copy.deepcopy(syms[ext[1]])
            pext = find1(parent, 'extends')
            assert not pext, 'nested extends not supported: ' + lib_id
            child_props = {p[1]: p for p in find(s, 'property')}
            out = [x for x in parent if not (isinstance(x, list) and x[0] in ('property', 'symbol'))]
            props = []
            for p in find(parent, 'property'):
                props.append(child_props.pop(p[1], p))
            props += list(child_props.values())
            subs = []
            for sub in find(parent, 'symbol'):
                sub = copy.deepcopy(sub)
                sub[1] = Q(name + sub[1][len(ext[1]):])
                subs.append(sub)
            # keep header tokens (pin_names, exclude_from_sim ...) from parent, then props, then units
            head = [x for x in out if not isinstance(x, list) or x[0] not in ('embedded_fonts',)]
            s = head + props + subs
            if find1(parent, 'embedded_fonts'):
                s.append(find1(parent, 'embedded_fonts'))
        s[1] = Q(lib_id)
        self.cache[lib_id] = s
        return s


def sym_units(sym):
    us = set()
    for sub in find(sym, 'symbol'):
        u = int(sub[1].rsplit('_', 2)[-2])
        if u:
            us.add(u)
    return sorted(us) or [1]


def sym_pins(sym, unit):
    pins = []
    for sub in find(sym, 'symbol'):
        parts = sub[1].rsplit('_', 2)
        u = int(parts[-2])
        if u not in (0, unit):
            continue
        for p in find(sub, 'pin'):
            at = find1(p, 'at')
            hidden = any(x == 'hide' or (isinstance(x, list) and x[0] == 'hide' and (len(x) == 1 or x[1] == 'yes')) for x in p)
            pins.append({
                'num': str(find1(p, 'number')[1]),
                'name': str(find1(p, 'name')[1]),
                'type': p[1],
                'x': float(at[1]), 'y': float(at[2]), 'a': int(float(at[3])) if len(at) > 3 else 0,
                'hidden': hidden,
            })
    return pins


def sym_bbox(sym, unit):
    xs, ys = [], []
    for sub in find(sym, 'symbol'):
        u = int(sub[1].rsplit('_', 2)[-2])
        if u not in (0, unit):
            continue
        for g in sub:
            if not isinstance(g, list):
                continue
            if g[0] == 'rectangle':
                for k in ('start', 'end'):
                    pt = find1(g, k)
                    xs.append(float(pt[1])); ys.append(float(pt[2]))
            elif g[0] in ('polyline', 'bezier'):
                for pt in find(find1(g, 'pts') or [], 'xy'):
                    xs.append(float(pt[1])); ys.append(float(pt[2]))
            elif g[0] == 'circle':
                c = find1(g, 'center'); r = float(find1(g, 'radius')[1])
                xs += [float(c[1]) - r, float(c[1]) + r]; ys += [float(c[2]) - r, float(c[2]) + r]
            elif g[0] == 'pin':
                at = find1(g, 'at'); ln = float(find1(g, 'length')[1]); a = math.radians(float(at[3]))
                xs += [float(at[1]), float(at[1]) + ln * math.cos(a)]
                ys += [float(at[2]), float(at[2]) + ln * math.sin(a)]
    if not xs:
        return (-1.27, -1.27, 1.27, 1.27)
    return (min(xs), min(ys), max(xs), max(ys))


def rot(px, py, r):
    """Rotate a lib-frame (Y up) point CCW by r degrees."""
    if r == 0:
        return px, py
    if r == 90:
        return -py, px
    if r == 180:
        return -px, -py
    if r == 270:
        return py, -px
    raise ValueError(r)


# ---------------------------------------------------------------- custom symbols

def make_symbol(name, pins_left, pins_right, ref='U', value=None, footprint='', descr='',
                pins_top=(), pins_bottom=(), width=None, datasheet='~', power=False):
    """Pins are (number, name, etype) tuples, or None for a gap. Returns a lib symbol node."""
    n = max(len(pins_left), len(pins_right), 1)
    pitch = 2.54
    if width is None:
        lw = max([len(p[1]) for p in pins_left if p] + [0])
        rw = max([len(p[1]) for p in pins_right if p] + [0])
        width = max(10.16, snap((lw + rw) * 1.05 + 5.08))
        width = math.ceil(width / 5.08) * 5.08
    nt = max(len(pins_top), len(pins_bottom))
    width = max(width, (nt + 1) * 5.08)
    h = (n + 1) * pitch
    top = snap(h / 2)
    top = math.ceil(top / 2.54) * 2.54
    bot = top - (n + 1) * pitch
    x0, x1 = -width / 2, width / 2
    body = [['rectangle', ['start', x0, top], ['end', x1, bot],
             ['stroke', ['width', 0.254], ['type', 'default']], ['fill', ['type', 'background']]]]
    pins = []

    def pin(p, x, y, a):
        num, nm, et = p
        pins.append(['pin', et, 'line', ['at', x, y, a], ['length', 2.54],
                     ['name', Q(nm), ['effects', ['font', ['size', 1.27, 1.27]]]],
                     ['number', Q(str(num)), ['effects', ['font', ['size', 1.27, 1.27]]]]])
    for i, p in enumerate(pins_left):
        if p:
            pin(p, x0 - 2.54, top - pitch * (i + 1), 0)
    for i, p in enumerate(pins_right):
        if p:
            pin(p, x1 + 2.54, top - pitch * (i + 1), 180)
    for i, p in enumerate(pins_top):
        if p:
            pin(p, x0 + 5.08 * (i + 1), top + 2.54, 270)
    for i, p in enumerate(pins_bottom):
        if p:
            pin(p, x0 + 5.08 * (i + 1), bot - 2.54, 90)

    def prop(k, v, x, y, hide=False):
        e = ['effects', ['font', ['size', 1.27, 1.27]]]
        if k in ('Reference',):
            e.append(['justify', 'left'])
        node = ['property', Q(k), Q(v), ['at', x, y, 0]]
        if hide:
            node.append(['hide', 'yes'])
        node.append(e)
        return node
    sym = ['symbol', Q(name), ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'],
           prop('Reference', ref, x0, top + 1.27),
           prop('Value', value or name, x0, bot - 1.27),
           prop('Footprint', footprint, 0, 0, True),
           prop('Datasheet', datasheet, 0, 0, True),
           prop('Description', descr, 0, 0, True),
           ['symbol', Q(name + '_0_1')] + body,
           ['symbol', Q(name + '_1_1')] + pins]
    return sym


def write_symbol_lib(path, symbols):
    root = ['kicad_symbol_lib', ['version', 20251024], ['generator', Q('sbot_gen')],
            ['generator_version', Q('1.0')]] + symbols
    open(path, 'w').write(dump(root) + '\n')


# ---------------------------------------------------------------- schematic model

POWER_SYMS = {'GND': 'power:GND', '+3V3': 'power:+3V3', '+5V': 'power:+5V'}
POWER_NETS = {'GND', '+3V3', '+5V', 'VBUS', 'VMOT', 'VSERVO', '+5V_USB', 'V3V3_IN'}


class Part:
    def __init__(self, lib_id, ref, value, footprint, nets, lcsc=None, mpn=None, dnp=False,
                 rot=None, fields=None, unit_nets=None, descr=None, in_bom=True):
        self.lib_id, self.ref, self.value, self.footprint = lib_id, ref, value, footprint
        self.nets = nets or {}
        self.lcsc, self.mpn, self.dnp, self.rot = lcsc, mpn, dnp, rot
        self.fields = fields or {}
        self.descr = descr
        self.in_bom = in_bom


class Block:
    def __init__(self, title, x, y, w=150, parts=None, note=None):
        self.title, self.x, self.y, self.w = title, x, y, w
        self.parts = parts or []
        self.note = note


class Sheet:
    def __init__(self, key, file, title, paper='A3'):
        self.key, self.file, self.title, self.paper = key, file, title, paper
        self.blocks = []
        self.ports = {}           # name -> shape
        self.texts = []

    def block(self, title, x, y, w=150, note=None):
        b = Block(title, x, y, w, note=note)
        self.blocks.append(b)
        return b

    def port(self, name, shape='bidirectional'):
        self.ports[name] = shape


class Design:
    def __init__(self, name, libs):
        self.name = name
        self.libs = libs
        self.sheets = []
        self.instances = []       # (sheet, inst_name, page, pin_map, refmap fn)
        self.root_texts = []

    def add_sheet(self, sheet):
        self.sheets.append(sheet)
        return sheet

    def instantiate(self, sheet, name, ref_offset, pin_map, x, y):
        """ref_offset: number added to every reference index of the sheet's parts for this instance."""
        self.instances.append(dict(sheet=sheet, name=name, off=ref_offset, pin_map=pin_map, x=x, y=y))


# ---------------------------------------------------------------- writer helpers

def eff(justify=None, hide=False, size=FONT):
    e = ['effects', ['font', ['size', size, size]]]
    if justify:
        e.append(['justify'] + justify.split())
    if hide:
        e.append(['hide', 'yes'])
    return e


def text_len(s):
    return len(s) * CHAR_W + 1.5


def out_dir(angle_lib, r):
    """Outward unit vector (schematic coords, Y down) for a pin whose lib angle is angle_lib."""
    a = math.radians((angle_lib + r + 180) % 360)
    dx, dy = round(math.cos(a)), round(math.sin(a))
    return dx, -dy


def label_angle(dx, dy):
    if dx == 1:
        return 0, 'left'
    if dx == -1:
        return 180, 'right'
    if dy == -1:
        return 90, 'left'
    return 270, 'right'


def ref_index(ref):
    i = len(ref)
    while i > 0 and ref[i - 1].isdigit():
        i -= 1
    return ref[:i], int(ref[i:]) if ref[i:] else 0


class Writer:
    def __init__(self, design, outdir, project):
        self.d = design
        self.outdir = outdir
        self.project = project
        self.root_uuid = uid('root', project)
        self.pwr_n = 0
        self.flg_n = 0
        self.lib_used = {}
        self.report = []

    # ---- symbol instance
    def symbol_node(self, lib_id, x, y, r, unit, uuid, props, instances, pins, dnp=False, in_bom=True, on_board=True):
        node = ['symbol', ['lib_id', Q(lib_id)], ['at', x, y, r], ['unit', unit],
                ['exclude_from_sim', 'no'], ['in_bom', 'yes' if in_bom else 'no'],
                ['on_board', 'yes' if on_board else 'no'], ['dnp', 'yes' if dnp else 'no'],
                ['uuid', Q(uuid)]]
        node += props
        for pn in pins:
            node.append(['pin', Q(pn), ['uuid', Q(uid(uuid, 'pin', pn))]])
        node.append(['instances', ['project', Q(self.project)] + instances])
        return node

    def prop(self, k, v, x, y, hide=False, justify=None, angle=0):
        return ['property', Q(k), Q(v), ['at', x, y, angle], ['show_name', 'no'], ['do_not_autoplace', 'no']] + \
            ([['hide', 'yes']] if hide else []) + [eff(justify)]

    def power_symbol(self, net, x, y, dx, dy, sheet_paths, items):
        lib_id = POWER_SYMS.get(net, 'power:VCC')
        sym = self.d.libs.get(lib_id)
        self.lib_used[lib_id] = sym
        down = net == 'GND'
        # default GND body points down (+y screen); +V symbols point up
        if down:
            r = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[(dx, dy)]
        else:
            r = {(0, -1): 0, (0, 1): 180, (1, 0): 270, (-1, 0): 90}[(dx, dy)]
        self.pwr_n += 1
        ref = '#PWR%04d' % self.pwr_n
        u = uid('pwr', sheet_paths[0], x, y, net)
        tx, ty = x + dx * 3.2, y + dy * 3.2
        if dx == 0:
            tx, ty = x, y + dy * (4.4 if down else 3.4)
        props = [self.prop('Reference', ref, x, y, hide=True),
                 self.prop('Value', net, tx, ty, justify=None),
                 self.prop('Footprint', '', x, y, hide=True),
                 self.prop('Datasheet', '', x, y, hide=True)]
        inst = [['path', Q(p), ['reference', Q('#PWR%04d' % (self.pwr_n + 10000 * i) if i else ref)], ['unit', 1]]
                for i, p in enumerate(sheet_paths)]
        items.append(self.symbol_node(lib_id, x, y, r, 1, u, props, inst, ['1'], in_bom=False, on_board=False))

    # ---- one sheet file
    def write_sheet(self, sheet, sheet_paths, ref_offsets, page_numbers):
        items = []
        nc_items = []
        port_nets = set(sheet.ports)
        used_ports = set()
        col_bottom = {}
        self.max_x, self.max_y = 0, 0
        for blk in sheet.blocks:
            if blk.y is None:
                if blk.w >= 300 or blk.x not in col_bottom:
                    blk.y = max(list(col_bottom.values()) + [26]) + 14
                else:
                    blk.y = col_bottom[blk.x] + 14
            items.append(['text', Q(blk.title), ['exclude_from_sim', 'no'], ['at', snap(blk.x), snap(blk.y - 5.08), 0],
                          ['effects', ['font', ['size', 2.0, 2.0], ['bold', 'yes']], ['justify', 'left', 'bottom']],
                          ['uuid', Q(uid(sheet.key, 'blk', blk.title))]])
            if blk.note:
                items.append(['text', Q(blk.note), ['exclude_from_sim', 'no'], ['at', snap(blk.x), snap(blk.y - 2.54), 0],
                              ['effects', ['font', ['size', 1.27, 1.27], ['italic', 'yes']], ['justify', 'left', 'bottom']],
                              ['uuid', Q(uid(sheet.key, 'blknote', blk.title))]])
            cx, cy, rowh = blk.x, blk.y + 2.54, 0
            for part in blk.parts:
                sym = self.d.libs.get(part.lib_id)
                self.lib_used[part.lib_id] = sym
                units = sym_units(sym)
                r = part.rot if part.rot is not None else (90 if self.is_two_pin(sym) else 0)
                for unit in units:
                    pins = sym_pins(sym, unit)
                    vis = [p for p in pins if not p['hidden']]
                    if not vis:
                        continue
                    bx0, by0, bx1, by1 = sym_bbox(sym, unit)
                    corners = [rot(px, py, r) for px, py in ((bx0, by0), (bx1, by1), (bx0, by1), (bx1, by0))]
                    sx0 = min(c[0] for c in corners); sx1 = max(c[0] for c in corners)
                    sy0 = min(-c[1] for c in corners); sy1 = max(-c[1] for c in corners)
                    # label extents
                    ext = {'l': 0, 'r': 0, 't': 0, 'b': 0}
                    for p in vis:
                        net = self.net_of(part, p)
                        dx, dy = out_dir(p['a'], r)
                        L = STUB + (text_len(net) if net and net not in POWER_NETS else (6 if net else 1.5))
                        if dx == -1: ext['l'] = max(ext['l'], L)
                        if dx == 1: ext['r'] = max(ext['r'], L)
                        if dy == -1: ext['t'] = max(ext['t'], L)
                        if dy == 1: ext['b'] = max(ext['b'], L)
                    w = (sx1 - sx0) + ext['l'] + ext['r'] + 5
                    h = (sy1 - sy0) + ext['t'] + ext['b'] + 7
                    if cx + w > blk.x + blk.w and cx > blk.x:
                        cx = blk.x
                        cy += rowh
                        rowh = 0
                    X = snap(cx + ext['l'] - sx0)
                    Y = snap(cy + ext['t'] - sy0 + 2.54)
                    cx += w
                    rowh = max(rowh, h)
                    self.place(sheet, part, sym, unit, units, r, X, Y, pins, vis, (sx0, sy0, sx1, sy1),
                               sheet_paths, ref_offsets, items, nc_items, used_ports)
                    self.max_x = max(self.max_x, cx)
            col_bottom[blk.x] = cy + rowh
            self.max_y = max(self.max_y, cy + rowh)
        # hierarchical labels are placed as part of pins; check ports used
        missing = port_nets - used_ports
        if missing:
            raise ValueError('sheet %s ports never used: %s' % (sheet.key, sorted(missing)))
        for t in sheet.texts:
            x, y, s, size = t
            items.append(['text', Q(s), ['exclude_from_sim', 'no'], ['at', snap(x), snap(y), 0],
                          ['effects', ['font', ['size', size, size]], ['justify', 'left', 'top']],
                          ['uuid', Q(uid(sheet.key, 'text', s[:40], x, y))]])
        return items + nc_items

    @staticmethod
    def is_two_pin(sym):
        pins = sym_pins(sym, 1)
        vis = [p for p in pins if not p['hidden']]
        return len(vis) == 2 and all(p['a'] in (90, 270) for p in vis)

    def net_of(self, part, p):
        n = part.nets
        if p['num'] in n:
            return n[p['num']]
        if p['name'] in n:
            return n[p['name']]
        return None

    def place(self, sheet, part, sym, unit, units, r, X, Y, pins, vis, bb, sheet_paths, ref_offsets, items, nc_items, used_ports):
        pfx, idx = ref_index(part.ref)
        u = uid(sheet.key, part.ref, unit)
        sx0, sy0, sx1, sy1 = bb
        fa = 90 if r in (90, 270) else 0
        flag = part.lib_id == 'power:PWR_FLAG'
        props = [
            self.prop('Reference', part.ref, snap(X + sx0), snap(Y + sy0 - 1.27), justify='left bottom', angle=fa, hide=flag),
            self.prop('Value', part.value, snap(X + sx0), snap(Y + sy1 + 1.27), justify='left top', angle=fa, hide=flag),
            self.prop('Footprint', part.footprint, X, Y, hide=True),
            self.prop('Datasheet', '', X, Y, hide=True),
        ]
        if part.descr:
            props.append(self.prop('Description', part.descr, X, Y, hide=True))
        if part.lcsc:
            props.append(self.prop('LCSC', part.lcsc, X, Y, hide=True))
        if part.mpn:
            props.append(self.prop('MPN', part.mpn, X, Y, hide=True))
        for k, v in part.fields.items():
            props.append(self.prop(k, v, X, Y, hide=True))
        if unit != units[0] and len(units) > 1:
            # extra units: show only the reference
            props[1] = self.prop('Value', part.value, snap(X + sx0), snap(Y + sy1 + 1.27), hide=True)
        inst = []
        for path, off in zip(sheet_paths, ref_offsets):
            ref = '%s%d' % (pfx, idx + off) if not pfx.startswith('#') else part.ref
            inst.append(['path', Q(path), ['reference', Q(ref)], ['unit', unit]])
        all_nums = [p['num'] for p in pins]
        node = self.symbol_node(part.lib_id, X, Y, r, unit, u, props, inst, all_nums,
                                dnp=part.dnp, in_bom=part.in_bom and not part.lib_id.startswith('power:'),
                                on_board=not part.lib_id.startswith('power:'))
        items.append(node)
        done_pos = set()
        for p in vis:
            px, py = rot(p['x'], p['y'], r)
            ax, ay = snap(X + px), snap(Y - py)
            if (ax, ay) in done_pos:
                continue
            done_pos.add((ax, ay))
            net = self.net_of(part, p)
            if net is None:
                nc_items.append(['no_connect', ['at', ax, ay], ['uuid', Q(uid(u, 'nc', p['num']))]])
                continue
            dx, dy = out_dir(p['a'], r)
            ex, ey = snap(ax + dx * STUB), snap(ay + dy * STUB)
            items.append(['wire', ['pts', ['xy', ax, ay], ['xy', ex, ey]],
                          ['stroke', ['width', 0], ['type', 'default']], ['uuid', Q(uid(u, 'w', p['num']))]])
            if net in POWER_NETS:
                self.power_symbol(net, ex, ey, dx, dy, sheet_paths, items)
            elif net in sheet.ports:
                used_ports.add(net)
                ang, just = label_angle(dx, dy)
                items.append(['hierarchical_label', Q(net), ['shape', sheet.ports[net]], ['at', ex, ey, ang],
                              eff(just), ['uuid', Q(uid(u, 'hl', p['num']))]])
            else:
                ang, just = label_angle(dx, dy)
                items.append(['label', Q(net), ['at', ex, ey, ang], eff(just + ' bottom'),
                              ['uuid', Q(uid(u, 'lb', p['num']))]])

    # ---- files
    def sch_file(self, file_uuid, paper, items, title):
        lib_syms = ['lib_symbols'] + [copy.deepcopy(s) for k, s in sorted(self.lib_used.items())]
        root = ['kicad_sch', ['version', 20260306], ['generator', Q('eeschema')], ['generator_version', Q('10.0')],
                ['uuid', Q(file_uuid)], ['paper', Q(paper)],
                ['title_block', ['title', Q(title)], ['date', Q('2026-11-17')], ['rev', Q('A')],
                 ['company', Q('Super bot')], ['comment', 1, Q('Main power + I/O carrier board')]],
                lib_syms] + items
        return root

    def write(self, root_title, root_paper='A3'):
        d = self.d
        # instance paths for each sheet
        sheet_insts = {}
        page = 2
        for inst in d.instances:
            inst['uuid'] = uid('sheetinst', inst['name'])
            inst['page'] = page
            page += 1
            sheet_insts.setdefault(inst['sheet'].key, []).append(inst)
        written = {}
        for sheet in d.sheets:
            insts = sheet_insts[sheet.key]
            paths = ['/%s/%s' % (self.root_uuid, i['uuid']) for i in insts]
            offs = [i['off'] for i in insts]
            self.lib_used = {}
            items = self.write_sheet(sheet, paths, offs, [i['page'] for i in insts])
            paper = 'A4' if self.max_x < 270 and self.max_y < 175 else ('A3' if self.max_x < 395 and self.max_y < 260 else 'A2')
            self.report.append((sheet.key, paper, round(self.max_x), round(self.max_y)))
            node = self.sch_file(uid('file', sheet.key), paper, items, sheet.title)
            open(os.path.join(self.outdir, sheet.file), 'w').write(dump(node) + '\n')
            written[sheet.key] = sheet
        # root
        self.lib_used = {}
        items = []
        for inst in d.instances:
            sh = inst['sheet']
            names = list(inst['pin_map'].items())
            h = max(10.16, snap(len(names) * 2.54 + 5.08))
            w = 40.64
            x, y = snap(inst['x']), snap(inst['y'])
            node = ['sheet', ['at', x, y], ['size', w, h], ['exclude_from_sim', 'no'], ['in_bom', 'yes'],
                    ['on_board', 'yes'], ['dnp', 'no'], ['fields_autoplaced', 'yes'],
                    ['stroke', ['width', 0.1524], ['type', 'solid']], ['fill', ['color', 0, 0, 0, 0.0]],
                    ['uuid', Q(inst['uuid'])],
                    ['property', Q('Sheetname'), Q(inst['name']), ['at', x, snap(y - 0.7), 0], ['show_name', 'no'],
                     ['do_not_autoplace', 'no'], eff('left bottom')],
                    ['property', Q('Sheetfile'), Q(sh.file), ['at', x, snap(y + h + 0.6), 0], ['show_name', 'no'],
                     ['do_not_autoplace', 'no'], eff('left top')]]
            for i, (port, net) in enumerate(names):
                py = snap(y + 2.54 + i * 2.54)
                shape = sh.ports[port]
                node.append(['pin', Q(port), shape, ['at', x + w, py, 0], ['uuid', Q(uid(inst['uuid'], 'pin', port))],
                             eff('right')])
                ex = snap(x + w + 2.54)
                items.append(['wire', ['pts', ['xy', x + w, py], ['xy', ex, py]], ['stroke', ['width', 0], ['type', 'default']],
                              ['uuid', Q(uid(inst['uuid'], 'rw', port))]])
                if net is None:
                    items.append(['no_connect', ['at', ex, py], ['uuid', Q(uid(inst['uuid'], 'rnc', port))]])
                else:
                    items.append(['label', Q(net), ['at', ex, py, 0], eff('left bottom'),
                                  ['uuid', Q(uid(inst['uuid'], 'rl', port))]])
            node.append(['instances', ['project', Q(self.project), ['path', Q('/' + self.root_uuid), ['page', Q(str(inst['page']))]]]])
            items.append(node)
        for (x, y, s, size) in d.root_texts:
            items.append(['text', Q(s), ['exclude_from_sim', 'no'], ['at', snap(x), snap(y), 0],
                          ['effects', ['font', ['size', size, size]], ['justify', 'left', 'top']],
                          ['uuid', Q(uid('root', 'text', s[:40], x, y))]])
        root = self.sch_file(self.root_uuid, root_paper, items, root_title)
        root.append(['sheet_instances', ['path', Q('/'), ['page', Q('1')]]])
        open(os.path.join(self.outdir, self.project + '.kicad_sch'), 'w').write(dump(root) + '\n')
