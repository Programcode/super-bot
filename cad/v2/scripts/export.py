# export.py: STEP of the whole robot, Fusion archive, one STL per printed part, one DXF
# per cut sheet part. Files are written to the Mac temp dir and PUT to the VPS bridge.
import os, re, tempfile

OUT = os.path.join(tempfile.gettempdir(), 'sbv2_export')
BASE = 'super-bot-v2'


def _slug(s):
    s = re.sub(r'\(.*?\)', '', s)
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def _send(path, name):
    put(name, open(path, 'rb').read())
    os.remove(path)


def step():
    em = design.exportManager
    p = os.path.join(OUT, BASE + '.step')
    em.execute(em.createSTEPExportOptions(p, root))
    _send(p, BASE + '.step')


def f3d():
    em = design.exportManager
    p = os.path.join(OUT, BASE + '.f3d')
    em.execute(em.createFusionArchiveExportOptions(p, root))
    _send(p, BASE + '.f3d')


def printed(c, b):
    return 'printed' in (c.name + ' ' + b.name).lower() or (b.material and b.material.name == 'PET Plastic')


def stls():
    em = design.exportManager
    seen = {}
    n = 0
    for occ in root.allOccurrences:
        c = occ.component
        for b in occ.bRepBodies:
            if not b.isSolid or not printed(c, b):
                continue
            nm = 'stl__%s__%s' % (_slug(c.name), _slug(b.name))
            seen[nm] = seen.get(nm, 0) + 1
            if seen[nm] > 1:
                nm += '-%d' % seen[nm]
            p = os.path.join(OUT, nm + '.stl')
            o = em.createSTLExportOptions(b, p)
            o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
            em.execute(o)
            _send(p, nm + '.stl')
            n += 1
    log('stl files', n)


def dxfs():
    n = 0
    for occ in root.allOccurrences:
        c = occ.component
        for b in occ.bRepBodies:
            mat = b.material.name if b.material else ''
            if mat not in ('Birch', 'Acrylic'):
                continue
            faces = [f for f in b.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType]
            big = max(faces, key=lambda f: f.area)
            sk = c.sketches.add(big)
            sk.name = 'dxf export tmp'
            for e in big.edges:
                sk.project(e)
            nm = 'dxf__%s__%s.dxf' % (_slug(c.name), _slug(b.name))
            p = os.path.join(OUT, nm)
            sk.saveAsDXF(p)
            sk.deleteMe()
            _send(p, nm)
            n += 1
    log('dxf files', n)


def main(parts=('step', 'f3d', 'stl', 'dxf')):
    os.makedirs(OUT, exist_ok=True)
    for k, f in (('step', step), ('f3d', f3d), ('stl', stls), ('dxf', dxfs)):
        if k in parts:
            f()
    done()
