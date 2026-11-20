"""scene.py: photoreal Cycles renders of Super bot v2 from the Fusion STEP (via step2mesh.py).

usage (VPS, headless):
  heavy blender -b -P cad/v2/render/scene.py -- --mesh /tmp/sbr/v2 --shots hero,front --out cad/v2/renders/real
      [--res 1920] [--samples 192] [--assets ~/ops/sb-render-assets] [--vendor /tmp/sbr/vendor.json]
      [--blend /tmp/x.blend] [--test]

Shots are defined in SHOTS below. Coordinates follow the CAD: mm in the manifest, metres in Blender,
Z up, +Y robot front, +X robot right, ground at Z 0. Materials come from name rules (RULES); every
body that matches no rule is printed as UNMATCHED and falls back to its Fusion colour.
"""
import bpy, json, math, os, re, sys, time
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))


def args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    o = {'mesh': '/tmp/sbr/old', 'shots': 'hero', 'out': '/tmp/sbr/out', 'res': 1920, 'samples': 128,
         'assets': os.path.expanduser('~/ops/sb-render-assets'), 'vendor': '', 'blend': '', 'test': False,
         'threads': 4}
    i = 0
    while i < len(a):
        k = a[i].lstrip('-')
        if k == 'test':
            o['test'] = True
            i += 1
            continue
        v = a[i + 1]
        o[k] = int(v) if k in ('res', 'samples', 'threads') else v
        i += 2
    return o


A = args()
LOG = []


def log(*x):
    s = ' '.join(str(v) for v in x)
    LOG.append(s)
    print(s, flush=True)


# ------------------------------------------------------------------ materials
def principled(m):
    return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def setin(node, names, val):
    for n in (names if isinstance(names, (list, tuple)) else [names]):
        if n in node.inputs:
            node.inputs[n].default_value = val
            return True
    return False


def new_mat(name, base, rough=0.5, metal=0.0, coat=0.0, spec=0.5, aniso=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = principled(m)
    setin(b, 'Base Color', tuple(base) + (1.0,))
    setin(b, 'Roughness', rough)
    setin(b, 'Metallic', metal)
    setin(b, ['Coat Weight', 'Clearcoat'], coat)
    setin(b, ['Specular IOR Level', 'Specular'], spec)
    if aniso:
        setin(b, 'Anisotropic', aniso)
    return m


def link(m, a, b):
    m.node_tree.links.new(a, b)


def add_bump(m, height_socket, strength=0.2, distance=0.0001):
    nt = m.node_tree
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = distance
    link(m, height_socket, bump.inputs['Height'])
    link(m, bump.outputs['Normal'], principled(m).inputs['Normal'])
    return bump


def tex_coord(m, kind='Object'):
    t = m.node_tree.nodes.new('ShaderNodeTexCoord')
    return t.outputs[kind]


def mat_printed(name, base, rough=0.55):
    """FDM PETG: fine 0.2 mm layer lines (world Z) as a faint bump, slight roughness noise."""
    m = new_mat(name, base, rough=rough, spec=0.45)
    nt = m.node_tree
    w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'
    w.bands_direction = 'Z'
    w.inputs['Scale'].default_value = 2 * math.pi / (10 * 0.0002)   # 0.2 mm period in metres
    w.inputs['Distortion'].default_value = 0.0
    link(m, tex_coord(m, 'Generated' if False else 'Object'), w.inputs['Vector'])
    add_bump(m, w.outputs['Fac'], strength=0.06, distance=0.00003)
    return m


def mat_smoked(name='smoked PETG', tint=(0.50, 0.48, 0.46), shadow=(0.58, 0.56, 0.54), rough=0.06):
    """Smoked translucent PETG. Camera rays see real refraction; shadow rays pass through a tinted
    transparent shader so the inside is lit like the real thing (no black box)."""
    m = new_mat(name, tint, rough=rough, spec=0.5)
    b = principled(m)
    setin(b, ['Transmission Weight', 'Transmission'], 1.0)
    setin(b, 'IOR', 1.57)
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    lp = nt.nodes.new('ShaderNodeLightPath')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = tuple(shadow) + (1,)
    mix = nt.nodes.new('ShaderNodeMixShader')
    link(m, lp.outputs['Is Shadow Ray'], mix.inputs['Fac'])
    link(m, b.outputs['BSDF'], mix.inputs[1])
    link(m, tr.outputs['BSDF'], mix.inputs[2])
    link(m, mix.outputs['Shader'], out.inputs['Surface'])
    return m


def mat_glass(name, tint=(0.95, 0.95, 0.95), rough=0.0, ior=1.5):
    m = new_mat(name, tint, rough=rough)
    b = principled(m)
    setin(b, ['Transmission Weight', 'Transmission'], 1.0)
    setin(b, 'IOR', ior)
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    lp = nt.nodes.new('ShaderNodeLightPath')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = tuple(tint) + (1,)
    mix = nt.nodes.new('ShaderNodeMixShader')
    link(m, lp.outputs['Is Shadow Ray'], mix.inputs['Fac'])
    link(m, b.outputs['BSDF'], mix.inputs[1])
    link(m, tr.outputs['BSDF'], mix.inputs[2])
    link(m, mix.outputs['Shader'], out.inputs['Surface'])
    return m


def mat_ply(name='stained birch ply'):
    """Dark-grey stained birch: stretched noise grain along the sheet, satin finish."""
    m = new_mat(name, (0.075, 0.075, 0.08), rough=0.55, spec=0.4)
    nt = m.node_tree
    tc = tex_coord(m, 'Object')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (60.0, 900.0, 60.0)
    link(m, tc, mp.inputs['Vector'])
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 1.0
    n.inputs['Detail'].default_value = 6.0
    n.inputs['Roughness'].default_value = 0.6
    link(m, mp.outputs['Vector'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.045, 0.045, 0.05, 1)
    ramp.color_ramp.elements[1].color = (0.11, 0.105, 0.105, 1)
    link(m, n.outputs['Fac'], ramp.inputs['Fac'])
    link(m, ramp.outputs['Color'], principled(m).inputs['Base Color'])
    add_bump(m, n.outputs['Fac'], strength=0.08, distance=0.0002)
    return m


def mat_emit(name, col, strength, base=(0.02, 0.02, 0.02)):
    m = new_mat(name, base, rough=0.2)
    b = principled(m)
    setin(b, ['Emission Color', 'Emission'], tuple(col) + (1,))
    setin(b, 'Emission Strength', strength)
    return m


def mat_neopixel(name='NeoPixel (on)'):
    m = new_mat(name, (0.9, 0.9, 0.88), rough=0.3)
    b = principled(m)
    setin(b, ['Emission Color', 'Emission'], (0.25, 0.85, 1.0, 1))
    setin(b, 'Emission Strength', 6.0)
    return m


def mat_pcb(name, mask, silk=(0.9, 0.9, 0.88)):
    """Soldermask over FR4 with a faint procedural trace pattern and white silk specks (generic boards;
    the main board and the vendor boards bring their own artwork)."""
    m = new_mat(name, mask, rough=0.32, coat=0.4, spec=0.5)
    nt = m.node_tree
    tc = tex_coord(m, 'Object')
    v = nt.nodes.new('ShaderNodeTexVoronoi')
    v.feature = 'DISTANCE_TO_EDGE'
    v.inputs['Scale'].default_value = 300.0
    link(m, tc, v.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].position = 0.06
    link(m, v.outputs['Distance'], ramp.inputs['Fac'])
    add_bump(m, ramp.outputs['Color'], strength=0.05, distance=0.00005)
    return m


MATS = {}


def build_mats():
    M = MATS
    M['smoked'] = mat_smoked()
    M['smoked_head'] = mat_smoked('smoked PETG head')
    M['clear_acrylic'] = mat_glass('clear acrylic', (0.97, 0.97, 0.97), 0.0, 1.49)
    M['frosted'] = mat_glass('frosted diffuser', (0.9, 0.9, 0.9), 0.5, 1.49)
    M['glass_dark'] = mat_glass('lens glass', (0.25, 0.27, 0.3), 0.0, 1.52)
    M['lidar_window'] = mat_glass('LD19 window (IR filter)', (0.18, 0.12, 0.12), 0.05, 1.55)
    M['petg_black'] = mat_printed('matte black PETG', (0.018, 0.018, 0.02), 0.55)
    M['ply'] = mat_ply()
    M['pcb_green'] = mat_pcb('PCB green soldermask', (0.02, 0.16, 0.05))
    M['pcb_black'] = mat_pcb('PCB black soldermask', (0.012, 0.012, 0.014))
    M['pcb_blue'] = mat_pcb('PCB blue soldermask', (0.01, 0.04, 0.22))
    M['pcb_purple'] = mat_pcb('PCB purple soldermask (OSH-style)', (0.12, 0.03, 0.2))
    M['gold'] = new_mat('ENIG gold', (1.0, 0.78, 0.38), rough=0.2, metal=1.0)
    M['brass'] = new_mat('brass', (0.92, 0.72, 0.36), rough=0.28, metal=1.0)
    M['steel'] = new_mat('steel', (0.75, 0.75, 0.76), rough=0.18, metal=1.0)
    M['steel_satin'] = new_mat('satin steel', (0.7, 0.7, 0.72), rough=0.35, metal=1.0, aniso=0.4)
    M['tin'] = new_mat('tinned steel (connector shells)', (0.62, 0.62, 0.64), rough=0.38, metal=1.0)
    M['nickel'] = new_mat('nickel', (0.78, 0.76, 0.72), rough=0.25, metal=1.0)
    M['alu_brushed'] = new_mat('brushed aluminium', (0.9, 0.9, 0.92), rough=0.28, metal=1.0, aniso=0.6)
    M['alu_anod_dark'] = new_mat('dark anodised aluminium', (0.12, 0.12, 0.13), rough=0.4, metal=1.0)
    M['steel_black'] = new_mat('black oxide steel', (0.06, 0.06, 0.065), rough=0.4, metal=1.0)
    M['rubber'] = new_mat('rubber (mecanum rollers)', (0.009, 0.009, 0.01), rough=0.62, spec=0.35)
    M['plastic_black'] = new_mat('black plastic', (0.02, 0.02, 0.022), rough=0.45)
    M['ic'] = new_mat('IC epoxy', (0.015, 0.015, 0.017), rough=0.5)
    M['nylon_yellow'] = new_mat('XT nylon (yellow)', (0.85, 0.55, 0.04), rough=0.45, spec=0.4)
    M['nylon_white'] = new_mat('JST/FPC nylon (off-white)', (0.85, 0.82, 0.74), rough=0.5)
    M['plastic_red'] = new_mat('red plastic', (0.6, 0.03, 0.02), rough=0.4)
    M['cell'] = new_mat('18650 PVC wrap (blue)', (0.03, 0.12, 0.45), rough=0.25, coat=0.6)
    M['wire_red'] = new_mat('red silicone wire', (0.55, 0.02, 0.015), rough=0.55, spec=0.35)
    M['wire_black'] = new_mat('black silicone wire', (0.02, 0.02, 0.022), rough=0.5, spec=0.35)
    M['ffc'] = new_mat('camera ribbon (FFC)', (0.82, 0.8, 0.72), rough=0.35)
    M['paper'] = new_mat('speaker cone (paper)', (0.12, 0.12, 0.12), rough=0.85)
    M['screen'] = new_mat('TFT glass (off area)', (0.005, 0.005, 0.006), rough=0.05, coat=1.0)
    M['face'] = mat_emit('face graphic (cyan on the TFT)', (0.2, 0.85, 1.0), 4.0)
    M['neopixel'] = mat_neopixel()
    M['floor_studio'] = new_mat('studio floor', (0.42, 0.42, 0.42), rough=0.38, spec=0.3)
    M['wall_paint'] = new_mat('wall paint', (0.78, 0.76, 0.72), rough=0.9, spec=0.2)
    M['skirting'] = new_mat('skirting board', (0.85, 0.84, 0.8), rough=0.5)


# Rules: (regex on 'top component / component :: body', material key). First match wins. Lower case.
RULES = [
    (r'face graphic', 'face'),
    (r'keep-out', None),
    (r'shell.*:: (front wall|rear wall|side wall|top half|battery door)', 'smoked'),
    (r'head shell', 'smoked_head'),
    (r'lidar pod', 'smoked'),
    (r'diffuser', 'frosted'),
    (r'tft window|clear acrylic', 'clear_acrylic'),
    (r'magnet 6x3', 'nickel'),
    (r'ld19 window', 'lidar_window'),
    (r'lens glass', 'glass_dark'),
    (r'tft glass', 'screen'),
    (r'neopixel|bar led|status led', 'neopixel'),
    (r'birch|chassis plate|ply\b', 'ply'),
    (r'roller', 'rubber'),
    (r'hub cap|pilot boss|gearbox', 'alu_brushed'),
    (r'wheel mecanum.*:: (hub|side plate)', 'alu_anod_dark'),
    (r'pan shaft .*alu|alu tube', 'alu_brushed'),
    (r'motor can', 'steel_satin'),
    (r'shaft|thrust collar|bearing|spline', 'steel'),
    (r'standoff|spacer', 'brass'),
    (r'screw|button head|m3 |m2\.5 |m2 ', 'steel_black'),
    (r'nickel strip|bus bar', 'nickel'),
    (r'\bcell\b', 'cell'),
    (r'camera ribbon|ffc|ribbon', 'ffc'),
    (r'wiring.*(12 v|5 v|6 v|vmot|battery|bat |bat_|power|xt60|xt30|charge|main )', 'wire_red'),
    (r'wiring|harness|cable|lead|loom', 'wire_black'),
    (r'xt60|xt30', 'nylon_yellow'),
    (r'loop key|fuse holder|kill', 'plastic_red'),
    (r'jst|mipi|fpc connector|cam-disp|pcie ffc', 'nylon_white'),
    (r'ethernet|usb|hdmi|rj45|wroom', 'tin'),
    (r'active cooler|heatsink', 'alu_anod_dark'),
    (r'chip|inductor|\bic\b|sensor\b|vl53l0x .*sensor|bno085 chip', 'ic'),
    (r'speaker cone', 'paper'),
    (r'speaker 40', 'steel_black'),
    (r'encoder', 'pcb_green'),
    (r'pcb|perfboard|carrier \(pololu|bms|ina226|module \(|ideal diode|devkitc', 'PCB'),
    (r'printed|cradle|pillar|bracket|bumper bar|holder|bezel|pocket|knuckle|turret|plinth|fork|hub|gear|shelf|sled|rail|clip|magnet block|mount|saddle', 'petg_black'),
    (r'motor terminals', 'nylon_white'),
    (r'ws2812b strip', 'pcb_black'),
    (r'button', 'plastic_black'),
    (r'header|rear cap|mg90s|ld19|d2f|microswitch|dc jack|lever', 'plastic_black'),
]


def pcb_for(col):
    if col is None:
        return 'pcb_green'
    r, g, b = col
    if g > 0.2 and g > r and g > b:
        return 'pcb_green'
    if b > 0.2 and b > r:
        return 'pcb_blue'
    if r > 0.1 and b > 0.1 and g < 0.1:
        return 'pcb_purple'
    return 'pcb_black'


def colour_mat(col):
    key = 'col_%.2f_%.2f_%.2f' % tuple(col)
    if key not in MATS:
        MATS[key] = new_mat(key, col, rough=0.5)
    return MATS[key]


def pick_mat(key, col):
    for rx, mk in RULES:
        if re.search(rx, key):
            if mk is None:
                return 'SKIP'
            if mk == 'PCB':
                return MATS[pcb_for(col)]
            return MATS[mk]
    log('UNMATCHED', key, col)
    return colour_mat(col or (0.5, 0.5, 0.5))


# ------------------------------------------------------------------ geometry
ROBOT = []


def load_bodies(prefix, tag='cad', colour_fn=None, top=None):
    man = json.load(open(prefix + '.json'))
    blob = np.fromfile(prefix + '.bin', dtype=np.uint8)
    coll = bpy.data.collections.new(tag)
    bpy.context.scene.collection.children.link(coll)
    n = 0
    for b in man['bodies']:
        path = [p for p in b['path'] if p and not p.startswith('=>')]
        rootless = path[1:] if len(path) > 1 else path
        comp = rootless[-1] if rootless else '?'
        top_ = top or (rootless[0] if rootless else '?')
        key = ('%s / %s :: %s' % (top_, comp, b['name'])).lower()
        col = b['groups'][0][1] if b['groups'] else None
        mat = colour_fn(col) if colour_fn else pick_mat(key, col)
        if mat == 'SKIP':
            continue
        v = np.frombuffer(blob, dtype=np.float32, count=b['v_n'] * 3, offset=b['v_off']).reshape(-1, 3) * 0.001
        t = np.frombuffer(blob, dtype=np.uint32, count=b['t_n'] * 3, offset=b['t_off']).reshape(-1, 3)
        me = bpy.data.meshes.new(b['name'][:60])
        me.from_pydata(v.tolist(), [], t.tolist())
        me.update()
        me.shade_smooth()
        if colour_fn and len(b['groups']) > 1:      # vendor parts: one material slot per colour group
            slots = {}
            idx = np.zeros(b['t_n'], dtype=np.int32)
            bounds = [g[0] for g in b['groups']] + [b['t_n']]
            for gi, g in enumerate(b['groups']):
                m = colour_fn(g[1])
                if m.name not in slots:
                    slots[m.name] = len(me.materials)
                    me.materials.append(m)
                idx[bounds[gi]:bounds[gi + 1]] = slots[m.name]
            me.polygons.foreach_set('material_index', idx)
        else:
            me.materials.append(mat)
        ob = bpy.data.objects.new(b['name'][:60], me)
        ob['top'] = top_
        ob['comp'] = comp
        ob['body'] = b['name']
        ob['key'] = key
        coll.objects.link(ob)
        ROBOT.append(ob)
        n += 1
    log('loaded', n, 'bodies from', prefix)
    return coll


def upgrade_rollers():
    """The Fusion rollers are double cones (a modelling shortcut). Replace each with a rubber barrel on
    the same axis, same length and same largest diameter, the shape real mecanum rollers have."""
    n = 0
    for o in list(ROBOT):
        if not re.search(r'wheel mecanum.*:: roller \d+', o['key']):
            continue
        v = np.array([o.matrix_world @ x.co for x in o.data.vertices])
        c = v.mean(0)
        w, U = np.linalg.eigh(np.cov((v - c).T))
        ax = U[:, np.argmax(w)]
        t = (v - c) @ ax
        rad = np.linalg.norm((v - c) - np.outer(t, ax), axis=1)
        L0, L1 = t.min(), t.max()
        c = c + ax * (L0 + L1) / 2
        L = L1 - L0
        R = rad.max()
        ends = rad[np.abs(t - (L0 + L1) / 2) > 0.45 * L]
        r_end = max(min(ends.max() if len(ends) else R * 0.55, R * 0.8), R * 0.45)
        segs, rings = 40, 24
        verts, faces = [], []
        prof = []
        for i in range(rings + 1):
            u = -1 + 2 * i / rings
            r = r_end + (R - r_end) * (1 - u * u)
            if abs(u) > 0.94:                       # small rounded edge at the ends
                r -= (abs(u) - 0.94) / 0.06 * 0.0006
            prof.append((u * L / 2, r))
        a = Vector(ax)
        b = a.orthogonal().normalized()
        cc = a.cross(b)
        for z, r in prof:
            for j in range(segs):
                ph = 2 * math.pi * j / segs
                p = Vector(c) + a * z + (b * math.cos(ph) + cc * math.sin(ph)) * r
                verts.append(p[:])
        for i in range(rings):
            for j in range(segs):
                q = i * segs
                faces.append((q + j, q + (j + 1) % segs, q + segs + (j + 1) % segs, q + segs + j))
        for end, sign in ((0, 1), (rings * segs, -1)):
            ctr = len(verts)
            verts.append((Vector(c) + a * (prof[0][0] if end == 0 else prof[-1][0]))[:])
            for j in range(segs):
                f = (end + j, end + (j + 1) % segs, ctr)
                faces.append(f if sign < 0 else f[::-1])
        me = bpy.data.meshes.new(o.name + ' barrel')
        me.from_pydata(verts, [], faces)
        me.shade_smooth()
        me.materials.append(MATS['rubber'])
        old = o.data
        o.data = me
        bpy.data.meshes.remove(old)
        n += 1
    log('rollers rebuilt as barrels', n)


def bbox_world(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


# ------------------------------------------------------------------ environment
ENV = []


def add_obj(name, me, mat):
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ENV.append(ob)
    return ob


def cyclorama(azimuth_deg, size=8.0, radius=1.2, back=2.2):
    """Floor + curved backdrop; the curve sits `back` m behind the robot, opposite the camera."""
    prof = []
    for i in range(0, 12):
        y = 4.0 - i * (4.0 + back) / 11.0
        prof.append((y, 0.0))
    for i in range(1, 13):
        a = math.radians(90 * i / 12)
        prof.append((-back - radius * math.sin(a), radius * (1 - math.cos(a))))
    prof.append((-back - radius, 4.0))
    verts, faces = [], []
    xs = (-size / 2, size / 2)
    for (y, z) in prof:
        for x in xs:
            verts.append((x, y, z))
    for i in range(len(prof) - 1):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    me = bpy.data.meshes.new('cyclorama')
    me.from_pydata(verts, [], faces)
    me.shade_smooth()
    ob = add_obj('cyclorama', me, MATS['floor_studio'])
    ob.rotation_euler = (0, 0, math.radians(azimuth_deg))
    return ob


def area(name, loc, target, size, power, color=(1, 1, 1), shape='RECTANGLE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    ld.energy = power
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    ENV.append(ob)
    return ob


def world_hdri(path, strength=1.0, rot_deg=0.0, bg=None):
    w = bpy.data.worlds.new('world')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bgn = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(path)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(rot_deg))
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bgn.inputs['Color'])
    bgn.inputs['Strength'].default_value = strength
    if bg is not None:   # camera sees a flat colour, everything else sees the HDRI
        lp = nt.nodes.new('ShaderNodeLightPath')
        b2 = nt.nodes.new('ShaderNodeBackground')
        b2.inputs['Color'].default_value = tuple(bg) + (1,)
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
        nt.links.new(bgn.outputs['Background'], mix.inputs[1])
        nt.links.new(b2.outputs['Background'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])


def clear_env():
    for o in ENV:
        bpy.data.objects.remove(o, do_unlink=True)
    ENV.clear()


def studio(az, top=True):
    """Neutral grey studio: cyclorama behind the robot (opposite the camera azimuth `az`, degrees,
    0 = camera on +Y looking at the front), big soft key, fill, rim and top light."""
    clear_env()
    cyclorama(az + 180 if False else az)
    world_hdri(os.path.join(A['assets'], 'studio_small_09_2k.hdr'), 0.35, az, bg=(0.35, 0.35, 0.35))
    r = math.radians(az)

    def rot(x, y, z):   # local frame: +y toward the camera
        return (x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r), z)
    tgt = (0, 0, 0.2)
    area('key', rot(-1.3, 1.3, 1.5), tgt, 1.4, 160, (1.0, 0.97, 0.93), size_y=1.0)
    area('fill', rot(1.6, 1.0, 0.7), tgt, 1.8, 50, (0.93, 0.96, 1.0), size_y=1.2)
    area('rim', rot(0.9, -1.6, 1.3), tgt, 1.0, 120, (1, 1, 1), size_y=0.5)
    if top:
        area('top', (0, 0, 2.3), (0, 0, 0), 1.6, 70, (1, 1, 1), 'DISK')


def apartment(az):
    """Apartment floor: oak laminate, painted wall with a skirting board, daylight HDRI + window light."""
    clear_env()
    r = math.radians(az)
    d = A['assets']
    # floor with the laminate texture
    me = bpy.data.meshes.new('floor')
    s = 6.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new()
    uv = me.uv_layers[0].data
    for i, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv[i].uv = (u * s * 2 / 1.6, v * s * 2 / 1.6)   # one texture tile = 1.6 m
    m = new_mat('oak laminate', (0.5, 0.4, 0.3), rough=0.4)
    nt = m.node_tree
    b = principled(m)
    ti = lambda f, nc: (lambda n: (setattr(n, 'image', bpy.data.images.load(os.path.join(d, f))), n)[1])(nt.nodes.new('ShaderNodeTexImage'))
    diff = ti('laminate_floor_02_diff_2k.jpg', False)
    rough = ti('laminate_floor_02_rough_2k.jpg', True)
    rough.image.colorspace_settings.name = 'Non-Color'
    nor = ti('laminate_floor_02_nor_gl_2k.jpg', True)
    nor.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap')
    link(m, diff.outputs['Color'], b.inputs['Base Color'])
    link(m, rough.outputs['Color'], b.inputs['Roughness'])
    link(m, nor.outputs['Color'], nm.inputs['Color'])
    link(m, nm.outputs['Normal'], b.inputs['Normal'])
    fl = add_obj('floor', me, m)
    fl.rotation_euler = (0, 0, r + math.radians(90))
    # back wall + skirting, opposite the camera
    wall_d = 1.5

    def rot(x, y, z):
        return (x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r), z)
    me = bpy.data.meshes.new('wall')
    me.from_pydata([rot(-5, -wall_d, 0), rot(5, -wall_d, 0), rot(5, -wall_d, 3), rot(-5, -wall_d, 3)], [], [(0, 1, 2, 3)])
    add_obj('wall', me, MATS['wall_paint'])
    me = bpy.data.meshes.new('skirting')
    y0, y1, h = -wall_d + 0.012, -wall_d, 0.08
    vs = [rot(-5, y1, 0), rot(5, y1, 0), rot(5, y0, 0), rot(-5, y0, 0), rot(-5, y1, h), rot(5, y1, h), rot(5, y0, h), rot(-5, y0, h)]
    me.from_pydata(vs, [], [(0, 1, 2, 3), (4, 5, 6, 7), (3, 2, 6, 7), (0, 3, 7, 4), (1, 2, 6, 5)])
    add_obj('skirting', me, MATS['skirting'])
    world_hdri(os.path.join(d, 'lebombo_2k.hdr'), 0.9, az + 60)
    area('window', rot(-2.2, 0.4, 1.4), (0, 0, 0.2), 2.0, 1400, (1.0, 0.96, 0.9), size_y=1.4)
    area('bounce', rot(1.5, 1.5, 1.2), (0, 0, 0.2), 1.5, 120, (1.0, 0.95, 0.88))


# ------------------------------------------------------------------ camera
def camera(eye_mm, target_mm, up='Z', fit_objs=None, margin=0.08, fstop=8.0, res=(1920, 1280), focus=None, lens=None):
    sc = bpy.context.scene
    cd = bpy.data.cameras.get('cam') or bpy.data.cameras.new('cam')
    cam = bpy.data.objects.get('cam') or bpy.data.objects.new('cam', cd)
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    sc.camera = cam
    eye = Vector(eye_mm) * 0.001
    tgt = Vector(target_mm) * 0.001
    cam.location = eye
    if up == 'Y':   # straight down, robot front at the top of the image
        cam.rotation_euler = (0, 0, 0)
    else:
        cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    cd.sensor_fit = 'HORIZONTAL'
    cd.sensor_width = 36.0
    cd.shift_x = cd.shift_y = 0.0
    cd.clip_start, cd.clip_end = 0.01, 60
    bpy.context.view_layer.update()
    aspect = res[0] / res[1]
    if fit_objs and lens is None:
        inv = cam.matrix_world.inverted()
        xs, ys = [], []
        for o in fit_objs:
            if o.hide_render:
                continue
            mw = o.matrix_world
            for c in o.bound_box:
                p = inv @ (mw @ Vector(c))
                if p.z < -1e-4:
                    xs.append(p.x / -p.z)
                    ys.append(p.y / -p.z)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        half = max((max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2 * aspect) * (1 + margin)
        cd.lens = 18.0 / half
        cd.shift_x = cx / (2 * half)
        cd.shift_y = cy / (2 * half) / 1.0
    elif lens:
        cd.lens = lens
    cd.dof.use_dof = fstop is not None
    if fstop:
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = focus if focus else (tgt - eye).length
    return cam


# ------------------------------------------------------------------ states
def base(o):
    return Matrix(o['base']) if 'base' in o else Matrix.Identity(4)


def reset():
    for o in ROBOT:
        o.hide_render = 'hidden_by_vendor' in o
        o.matrix_world = base(o)
        o.visible_shadow = True


def hide(rx):
    n = 0
    for o in ROBOT:
        if re.search(rx, o['key']):
            o.hide_render = True
            n += 1
    return n


SHELL_PANELS = r'^shell.*:: (front wall|rear wall|side wall|top half|battery door)'

GROUPS = [   # same groups as scripts/shots.py, metres
    (0.0, ('chassis', 'drive', 'battery', 'power connectors', 'cliff', 'front ultrasonic', 'bumpers')),
    (0.17, ('frame', 'raspberry pi', 'esp32', 'circuit playground', 'bno085', 'speaker', 'main power', 'wiring',
            'audio', 'charge', 'motor driver', 'pololu', 'power distribution', 'pdb', 'ina226', 'pi 5 v', 'servo 6 v',
            'buck', 'drv8874', 'perfboard', 'loop key', 'mic', 'amp')),
    (0.43, ('head joint fixed', 'lidar')),
    (0.56, ('head pan rotor',)),
]
SHELL_OUT = 0.21


def explode():
    unmatched = set()
    for o in ROBOT:
        k = o['key']
        top = o['top'].lower()
        if top.startswith('shell'):
            if not re.search(SHELL_PANELS, k):
                o.hide_render = True        # magnets, clips, blocks stay out of the exploded view
                continue
            mn, mx = bbox_world([o])
            c = (mn + mx) / 2
            dx = SHELL_OUT if c.x > 0.06 else (-SHELL_OUT if c.x < -0.06 else 0)
            dy = SHELL_OUT if c.y > 0.06 else (-SHELL_OUT if c.y < -0.06 else 0)
            dz = 0.17
            if 'top half' in k:
                dx, dy, dz = 0, (0.06 if 'front' in k else -0.06), 0.30
            if 'battery door' in k:
                dz = 0.0
                dy = -SHELL_OUT
            o.matrix_world = Matrix.Translation((dx, dy, dz)) @ base(o)
            continue
        if top.startswith('wiring'):
            o.hide_render = True            # harness runs between groups; shown in the cut-aways instead
            continue
        dz = None
        for g, pre in GROUPS:
            if top.startswith(pre):
                dz = g
        if dz is None:
            unmatched.add(o['top'])
            dz = 0.0
        o.matrix_world = Matrix.Translation((0, 0, dz)) @ base(o)
    if unmatched:
        log('EXPLODE-UNMATCHED', sorted(unmatched))


# ------------------------------------------------------------------ labels
SEE_THROUGH = ('smoked', 'glass', 'acrylic', 'diffuser', 'window')


def see_through(o):
    return any(k in (o.active_material.name if o.active_material else '').lower() for k in SEE_THROUGH)


def visible_anchor(cam, objs):
    """A point on one of `objs` that the camera actually sees: sample vertices near the projected
    centre and keep the first whose ray from the camera hits that object first."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    cands = []
    for o in objs:
        if o.hide_render:
            continue
        mw = o.matrix_world
        vs = o.data.vertices
        step = max(1, len(vs) * len(objs) // 4000)
        for i in range(0, len(vs), step):
            cands.append((o, mw @ vs[i].co))
    if not cands:
        return None
    pts = [world_to_camera_view(sc, cam, p) for _, p in cands]
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    order = sorted(range(len(cands)), key=lambda i: (pts[i].x - cx) ** 2 + (pts[i].y - cy) ** 2)
    eye = cam.matrix_world.translation
    names = set(o.name for o in objs)
    for i in order:
        o, p = cands[i]
        # nudge the target point toward the object's centre so the ray doesn't graze an edge
        d = (p - eye)
        start, dirn, left = eye.copy(), d.normalized(), d.length + 0.002
        for _ in range(8):   # step through see-through parts (smoked shell, glass, acrylic)
            hit, loc, nrm, idx, ho, mtx = sc.ray_cast(dg, start, dirn, distance=left)
            if not hit or ho.name in names or not see_through(ho):
                break
            left -= (loc - start).length + 0.0005
            start = loc + dirn * 0.0005
        if hit and ho.name in names and (loc - p).length < 0.004:
            return pts[i]
    return None


def labels_json(cam, items, title, path):
    sc = bpy.context.scene
    W, H = sc.render.resolution_x, sc.render.resolution_y
    out = []
    for text, rx in items:
        objs = [o for o in ROBOT if re.search(rx, o['key']) and not o.hide_render]
        if not objs:
            log('LABEL-MISSING', text, rx)
            continue
        p = visible_anchor(cam, objs)
        if p is None:
            log('LABEL-HIDDEN', text, rx)
            continue
        out.append({'text': text, 'x': p.x * W, 'y': (1 - p.y) * H})
    json.dump({'w': W, 'h': H, 'title': title, 'labels': out}, open(path, 'w'), indent=1)
    log('labels', len(out), '/', len(items), '->', path)


# ------------------------------------------------------------------ render settings
def setup_render(samples, res):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    c = sc.cycles
    c.device = 'CPU'
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.use_denoising = True
    try:
        c.denoiser = 'OPENIMAGEDENOISE'
    except TypeError:
        pass
    c.max_bounces = 16
    c.diffuse_bounces = 4
    c.glossy_bounces = 6
    c.transmission_bounces = 12
    c.transparent_max_bounces = 16
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.sample_clamp_indirect = 6.0
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = A['threads']
    sc.render.use_persistent_data = True
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    vs = sc.view_settings
    try:
        vs.view_transform = 'AgX'
        vs.look = 'AgX - Medium High Contrast'
    except TypeError:
        try:
            vs.look = 'Medium High Contrast'
        except TypeError:
            pass
    vs.exposure = 0.0


# ------------------------------------------------------------------ shots
# eye/target in mm (CAD frame). az = studio azimuth (degrees) of the camera around Z, 0 = front (+Y).
def az_of(eye):
    return math.degrees(math.atan2(-eye[0], eye[1]))


EXPLODED_LABELS = [
    ('Head: smoked PETG capsule, 190 x 76 x 64 mm', r'head tilt rotor.*:: head shell front'),
    ('Raspberry Pi Camera Module 3 (eye)', r'camera module 3'),
    ('1.3" 240 x 240 TFT face', r'tft 1\.3in|:: tft glass'),
    ('Tilt MG90S in the printed turret', r'head pan rotor.*:: turret'),
    ('Square plinth with the upper 6805 bearing', r':: plinth'),
    ('LDROBOT LD19 lidar', r'ldrobot'),
    ('Lidar pod (smoked PETG)', r'lidar pod'),
    ('Top halves (smoked PETG, magnets)', r'shell.*:: top half front'),
    ('Front wall (smoked PETG, 2.4 mm)', r'shell.*:: front wall'),
    ('Side wall (lifts off over the wheel shaft)', r'shell.*:: side wall right'),
    ('Top deck, 4 mm stained birch ply', r':: top deck'),
    ('Raspberry Pi 5 8 GB + AI HAT+ 2', r'raspberry pi 5|raspberry pi ai hat'),
    ('4x Pololu DRV8874 motor drivers on a perfboard', r'(motor driver|drv8874).*:: (perfboard|drv8874 carrier)'),
    ('ESP32-S3-DevKitC-1 (reflex layer)', r'esp32-s3-devkitc.*:: (devkitc pcb|wroom)'),
    ('Power distribution board + INA226', r'(power distribution|pdb).*:: (pdb|ina226|bus bar|perfboard)'),
    ('Pololu 5 V buck for the Pi', r'(pi 5 v|d36v50).*:: (d36v50|pcb)'),
    ('Circuit Playground Express (front status light)', r'circuit playground'),
    ('Spine, 4 mm stained birch ply', r':: spine'),
    ('3S4P 18650 pack + BMS on the battery sled', r'battery 3s4p.*:: cell'),
    ('JGB37-520 gear motor with Hall encoder', r'motor jgb37.*fr.*:: (gearbox|motor can)'),
    ('100 mm mecanum wheel (rubber rollers)', r'wheel mecanum 100 fr'),
    ('Chassis plate, 6 mm birch ply', r'chassis plate'),
    ('Bumper bar on D2F-01L microswitches', r'bumper'),
    ('Battery door with charge jack', r'shell.*:: battery door'),
]

SHOTS = {
    'hero': dict(eye=(1050, 1250, 560), tgt=(0, 0, 200), env='studio', fstop=5.6),
    'front': dict(eye=(0, 1800, 240), tgt=(0, 0, 215), env='studio', fstop=11),
    'side': dict(eye=(1800, 0, 240), tgt=(0, 0, 215), env='studio', fstop=11),
    'rear': dict(eye=(0, -1800, 240), tgt=(0, 0, 215), env='studio', fstop=11),
    'top': dict(eye=(0, 1, 1900), tgt=(0, 0, 0), env='studio', fstop=None, up='Y', res=(1920, 1920), az=-20, toplight=False),
    'rear34': dict(eye=(-1000, -1200, 620), tgt=(0, 0, 200), env='studio', fstop=5.6),
    'photo': dict(eye=(-920, 1320, 640), tgt=(0, 0, 220), env='studio', fstop=5.6, res=(1440, 1920)),
    'apartment': dict(eye=(-650, 1150, 230), tgt=(0, 0, 190), env='apartment', fstop=2.8, margin=0.35),
    'insides-front': dict(eye=(950, 1150, 640), tgt=(0, 0, 190), env='studio', fstop=8, hide=SHELL_PANELS + r'|^shell.*magnet 6x3 \(panel|panel clip'),
    'insides-rear': dict(eye=(-950, -1150, 640), tgt=(0, 0, 190), env='studio', fstop=8, hide=SHELL_PANELS + r'|^shell.*magnet 6x3 \(panel|panel clip'),
    'cutaway': dict(eye=(1050, 1250, 560), tgt=(0, 0, 200), env='studio', fstop=8,
                    hide=r'^shell.*:: (front wall|side wall right|top half)|^shell.*magnet 6x3 \(panel\) (front|right|top)|panel clip.*(front|right)'),
    'exploded': dict(eye=(-1500, 2000, 1250), tgt=(0, 0, 420), env='studio', fstop=11, state='explode', res=(1920, 2160), margin=0.05),
    'exploded-labels': dict(eye=(-1500, 2000, 1250), tgt=(0, 0, 420), env='studio', fstop=None, state='explode', res=(1920, 2160),
                            margin=0.05, labels=(EXPLODED_LABELS, 'Super bot v2, exploded: every part is a real, bought or printed part')),
    'close-head': dict(eye=(-330, 520, 450), tgt=(0, 20, 340), env='studio', fstop=8, fit=r'head pan rotor|head joint fixed.*plinth|servo mg90s', margin=0.12),
    'close-board': dict(eye=(-300, 680, 230), tgt=(0, 60, 160), env='studio', fstop=8, hide=r'^shell.*:: (front wall|top half front)|^shell.*\(panel\) (front|top f)',
                        fit=r'motor driver|drv8874|esp32-s3-devkitc|raspberry pi 5|raspberry pi ai|circuit playground', margin=0.15),
    'close-battery': dict(eye=(420, -560, 300), tgt=(0, -30, 70), env='studio', fstop=8,
                          hide=r'^shell.*:: (rear wall|battery door|side wall right|top half)|^shell.*\(panel\) (rear|right|top)|panel clip.*(rear|right)|^frame.*:: rear plate|^drive rr.*wheel',
                          fit=r'battery|power connectors|sled', margin=0.25),
    'close-wheel': dict(eye=(470, 460, 210), tgt=(110, 70, 60), env='studio', fstop=8, fit=r'drive fr', margin=0.18),
    'close-lidar': dict(eye=(-560, -440, 480), tgt=(-50, -50, 300), env='studio', fstop=8, fit=r'^lidar pod|ldrobot', margin=0.45),
}


def render(name, outdir):
    s = SHOTS[name]
    reset()
    if s.get('hide'):
        log('hidden', hide(s['hide']), 'for', name)
    if s.get('state') == 'explode':
        explode()
    az = s.get('az', az_of(s['eye']))
    if s['env'] == 'apartment':
        apartment(az)
    else:
        studio(az, top=s.get('toplight', True))
    res = s.get('res', (1920, 1280))
    if A['test']:
        res = (res[0] // 2, res[1] // 2)
    fit = [o for o in ROBOT if not o.hide_render and (not s.get('fit') or re.search(s['fit'], o['key']))]
    cam = camera(s['eye'], s['tgt'], s.get('up', 'Z'), fit, s.get('margin', 0.08), s.get('fstop'), res)
    setup_render(A['samples'] if not A['test'] else min(A['samples'], 32), res)
    sc = bpy.context.scene
    os.makedirs(outdir, exist_ok=True)
    sc.render.filepath = os.path.join(outdir, name + '.png')
    if s.get('labels'):
        items, title = s['labels']
        labels_json(cam, items, title, os.path.join(outdir, name + '.json'))
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    log('rendered', name, res, '%.0fs' % (time.time() - t0), '->', sc.render.filepath)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_mats()
    load_bodies(A['mesh'])
    upgrade_rollers()
    if A['vendor']:
        import importlib.util
        spec = importlib.util.spec_from_file_location('vendor', os.path.join(HERE, 'vendor.py'))
        vm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vm)
        vm.apply(A['vendor'], ROBOT, load_bodies, log, MATS, new_mat)
    mn, mx = bbox_world(ROBOT)
    log('robot bbox mm', [round(v * 1000) for v in mn], [round(v * 1000) for v in mx])
    for n in A['shots'].split(','):
        render(n, A['out'])
    if A['blend']:
        bpy.ops.wm.save_as_mainfile(filepath=A['blend'])
    open(os.path.join(A['out'], 'render-log.txt'), 'a').write('\n'.join(LOG) + '\n')


main()
