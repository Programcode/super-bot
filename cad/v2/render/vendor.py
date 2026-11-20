"""vendor.py: swap the Fusion stand-ins for vendor 3D models (Raspberry Pi, Adafruit, LDROBOT) and the
KiCad export of the main board. Loaded by scene.py when --vendor <json> is given.

vendor json: {"items": [ {
    "name": "Raspberry Pi 5",
    "mesh": "/tmp/sbr/vm/pi5"            step2mesh.py output prefix   (or "glb": path for KiCad GLB)
    "hide": "regex on body keys",         Fusion stand-in bodies to hide
    "target": "regex",                    Fusion stand-in PCB body to align to (optional with "matrix")
    "rot": [[...],[...],[...]],           vendor axes -> robot axes (rows), applied before alignment
    "matrix": [[4x4]],                    or an explicit vendor->robot matrix in metres
    "scale": 0.001 } ] }
Alignment: after `rot`, the vendor PCB (the largest body about 1-2 mm thick) is moved so its bbox
centre sits on the target body's bbox centre. Models are not committed (size, licences); see
fetch_vendor.sh for the sources.
"""
import json, re
import numpy as np
import bpy
from mathutils import Matrix, Vector


def _bbox(objs):
    pts = np.array([o.matrix_world @ Vector(c) for o in objs for c in o.bound_box])
    return pts.min(0), pts.max(0)


def _pcb(objs):
    best, area = None, 0
    for o in objs:
        mn, mx = _bbox([o])
        d = sorted(mx - mn)
        if 0.0007 < d[0] < 0.0022 and d[1] * d[2] > area:
            best, area = o, d[1] * d[2]
    return best


def _glb(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = []
    for o in new:
        if o.type == 'MESH':
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            meshes.append(o)
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        bpy.ops.object.select_all(action='DESELECT')
        o['top'] = tag
        o['comp'] = tag
        o['body'] = o.name
        o['key'] = (tag + ' / ' + tag + ' :: ' + o.name).lower()
    return meshes


def smart_colour(col, MATS, new_mat):
    """Material from a CAD colour for vendor parts, which carry colours but not names."""
    r, g, b = col[:3]
    mx, mn = max(r, g, b), min(r, g, b)
    if r > 0.55 and g > 0.4 and b < 0.35 and r - b > 0.3:
        return MATS['gold']
    if mn > 0.5 and mx - mn < 0.12 and mx < 0.9:
        return MATS['tin']
    if mx < 0.06:
        return MATS['plastic_black']
    if g > r + 0.05 and g > b and mx < 0.5:
        return MATS['pcb_green']
    if mn > 0.85:
        return MATS['nylon_white']
    key = 'vendor %.2f %.2f %.2f' % (r, g, b)
    if key not in MATS:
        MATS[key] = new_mat(key, (r, g, b), rough=0.45)
    return MATS[key]


def apply(path, ROBOT, load_bodies, log, MATS=None, new_mat=None):
    cfg = json.load(open(path))
    for it in cfg['items']:
        tag = 'vendor ' + it['name']
        if it.get('glb'):
            objs = _glb(it['glb'], tag)
            if it.get('glb_materials') == 'kicad':
                for o in objs:
                    for i, m in enumerate(o.data.materials):
                        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m else None
                        if b is None:
                            continue
                        c = tuple(b.inputs['Base Color'].default_value)[:3]
                        r, g, bb = c
                        if r > 0.55 and g > 0.4 and bb < 0.4 and r - bb > 0.25:      # pads, pins: gold
                            o.data.materials[i] = MATS['gold']
                        elif g > r and g > bb and g < 0.5 and max(c) < 0.5:         # soldermask
                            o.data.materials[i] = MATS['pcb_green']
                        else:
                            b.inputs['Roughness'].default_value = 0.4
        else:
            n0 = len(ROBOT)
            load_bodies(it['mesh'], tag, colour_fn=lambda col: smart_colour(col or (0.5, 0.5, 0.5), MATS, new_mat), top=tag)
            objs = ROBOT[n0:]
        if it.get('glb'):
            ROBOT.extend(objs)
        for rx, mk in it.get('mat_by_name', {}).items():     # vendor files name parts, not materials
            for o in objs:
                if re.search(rx, o['body'], re.I):
                    for i in range(len(o.data.materials)):
                        o.data.materials[i] = MATS[mk]
        s = it.get('scale', 1.0)
        R = Matrix(it.get('rot', [[1, 0, 0], [0, 1, 0], [0, 0, 1]])).to_4x4()
        if it.get('matrix'):
            M = Matrix(it['matrix'])
        else:
            M = R @ Matrix.Scale(s, 4)
        for o in objs:
            o.matrix_world = M @ o.matrix_world
        if it.get('target'):
            tgt = [o for o in ROBOT if re.search(it['target'], o['key']) and not o['top'].startswith('vendor')]
            a = it.get('anchor')
            pcb = _pcb(objs) if not a else (objs if a == 'ALL' else [o for o in objs if re.search(a, o['body'], re.I)])
            if tgt and pcb:
                tmn, tmx = _bbox(tgt)
                pmn, pmx = _bbox(pcb if isinstance(pcb, list) else [pcb])
                d = Vector((tmn + tmx) / 2 - (pmn + pmx) / 2)
                if it.get('align') == 'bottom':
                    d.z = tmn[2] - pmn[2]
                d += Vector(it.get('nudge', (0, 0, 0)))
                for o in objs:
                    o.matrix_world = Matrix.Translation(d) @ o.matrix_world
                log('vendor', it['name'], 'pcb', [round(v * 1000, 1) for v in (pmx - pmn)], 'target',
                    [round(v * 1000, 1) for v in (tmx - tmn)], 'moved mm', [round(v * 1000, 1) for v in d])
            else:
                log('vendor', it['name'], 'ALIGN FAILED: target', bool(tgt), 'pcb', bool(pcb))
        if it.get('neopixels'):     # the CPX is the status light: its 10 NeoPixels glow
            pmn, pmx = _bbox(objs)
            c = (pmn + pmx) / 2
            k = 0
            for o in objs:
                mn, mx = _bbox([o])
                dd = sorted(mx - mn)
                r = np.linalg.norm(((mn + mx) / 2 - c)) * 1000
                if dd[0] < 0.0022 and 0.004 < dd[1] < 0.0058 and 0.004 < dd[2] < 0.0058 and 12 < r < 22:
                    for i in range(len(o.data.materials)):
                        o.data.materials[i] = MATS['neopixel']
                    k += 1
            log('vendor', it['name'], 'NeoPixels lit', k)
        # base matrices for exploded views
        for o in objs:
            o['base'] = [list(r) for r in o.matrix_world]
            o['top'] = it.get('group', tag)
        if it.get('hide'):
            k = 0
            for o in ROBOT:
                if not o['top'].startswith('vendor') and o.get('vendor_of') is None and re.search(it['hide'], o['key']):
                    o['hidden_by_vendor'] = it['name']
                    k += 1
            log('vendor', it['name'], 'replaces', k, 'stand-in bodies;', len(objs), 'vendor bodies')
        mn, mx = _bbox(objs)
        log('vendor', it['name'], 'bbox mm', [round(v * 1000) for v in mn], [round(v * 1000) for v in mx])
