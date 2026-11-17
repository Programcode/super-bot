# export.py: STEP of the whole robot, Fusion archive, STL per printed / shell part,
# DXF outline per laser-cut sheet. Files are written to the Mac temp dir and PUT to the VPS.
import os, re, tempfile, urllib.request

OUT = os.path.join(tempfile.gettempdir(), 'sb_export')


def _put(path, name):
    data = open(path, 'rb').read()
    urllib.request.urlopen(urllib.request.Request('http://100.115.45.111:8765/' + name, data=data, method='PUT'), timeout=300).read()
    log('put', name, len(data))


def _slug(s):
    s = re.sub(r'\(.*?\)', '', s)
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def step():
    em = design.exportManager
    p = os.path.join(OUT, 'super-bot-concept-k-v1.step')
    em.execute(em.createSTEPExportOptions(p, root))
    _put(p, 'super-bot-concept-k-v1.step')


def f3d():
    em = design.exportManager
    p = os.path.join(OUT, 'super-bot-concept-k-v1.f3d')
    em.execute(em.createFusionArchiveExportOptions(p, root))
    _put(p, 'super-bot-concept-k-v1.f3d')


def stls():
    em = design.exportManager
    n = 0
    for occ in root.allOccurrences:
        c = occ.component
        for b in occ.bRepBodies:
            nm = (c.name + ' ' + b.name).lower()
            mat = b.material.name if b.material else ''
            printed = ('printed' in nm or mat == 'PET Plastic')
            shell = c.name.startswith('Shell') or c.name.startswith('Lidar backpack') or 'head shell' in b.name
            if not (printed or shell):
                continue
            name = 'stl__%s__%s.stl' % (_slug(c.name), _slug(b.name))
            p = os.path.join(OUT, name)
            o = em.createSTLExportOptions(b, p)
            o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
            em.execute(o)
            _put(p, name)
            n += 1
    log('stl files', n)


def dxfs():
    """Outline of each flat sheet part (plate, deck, acrylic panels) as DXF."""
    n = 0
    for occ in root.allOccurrences:
        c = occ.component
        for b in c.bRepBodies:
            mat = b.material.name if b.material else ''
            if mat not in ('Acrylic', 'Birch') or 'insert' in b.name:
                continue
            faces = [f for f in b.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType]
            big = max(faces, key=lambda f: f.area)
            sk = c.sketches.add(big)
            sk.name = 'dxf export tmp'
            for e in big.edges:
                sk.project(e)
            name = 'dxf__%s__%s.dxf' % (_slug(c.name), _slug(b.name))
            p = os.path.join(OUT, name)
            sk.saveAsDXF(p)
            sk.deleteMe()
            _put(p, name)
            n += 1
    log('dxf files', n)


def main(parts=('step', 'f3d', 'stl', 'dxf')):
    os.makedirs(OUT, exist_ok=True)
    if 'step' in parts:
        step()
    if 'f3d' in parts:
        f3d()
    if 'stl' in parts:
        stls()
    if 'dxf' in parts:
        dxfs()
    done()
