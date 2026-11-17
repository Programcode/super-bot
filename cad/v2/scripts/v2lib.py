# v2lib.py: shared helpers for the Super bot v2 Fusion build scripts (based on v1's sblib.py).
# The loader execs this file, then a stage file, then calls main(). All geometry is built in root
# coordinates (mm, Z up, +Y = robot front, +X = robot right, ground at Z=0) with
# sketch dimensions and feature distances driven by user-parameter expressions.
import adsk.core, adsk.fusion, math, re, urllib.request

app = adsk.core.Application.get()
DOCNAME = 'Super bot - v2'
if app.activeDocument.name != DOCNAME and re.sub(r' v\d+$', '', app.activeDocument.name) != DOCNAME:
    raise Exception('Refusing to run: active document is %r, not %r' % (app.activeDocument.name, DOCNAME))
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
um = design.unitsManager
V = adsk.core.ValueInput
OC = adsk.core.ObjectCollection
NEWB = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
INTER = adsk.fusion.FeatureOperations.IntersectFeatureOperation
LOG = []


def log(*a):
    LOG.append(' '.join(str(x) for x in a))


def mm(expr):
    """Evaluate a length expression to mm."""
    return um.evaluateExpression(str(expr), 'mm') * 10.0


def deg(expr):
    return math.degrees(um.evaluateExpression(str(expr), 'deg'))


def param(name, expr, comment='', unit='mm'):
    p = design.userParameters.itemByName(name)
    if p:
        p.expression = expr
        p.comment = comment
        return p
    return design.userParameters.add(name, V.createByString(expr), unit, comment)


# ---------------------------------------------------------------- components
def find_occ(name, parent=None):
    parent = parent or root
    for o in parent.occurrences:
        if o.component.name == name:
            return o
    return None


def fresh(name, parent=None):
    """Delete the component if it exists and create it new (idempotent stages)."""
    parent = parent or root
    o = find_occ(name, parent)
    if o:
        o.deleteMe()
    occ = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def sub(c, name):
    occ = c.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


# ---------------------------------------------------------------- sketches
_BASE = {'z': 'xYConstructionPlane', 'y': 'xZConstructionPlane', 'x': 'yZConstructionPlane'}


def _axis_of(v):
    comps = [v.x, v.y, v.z]
    i = max(range(3), key=lambda k: abs(comps[k]))
    return 'xyz'[i], (1 if comps[i] > 0 else -1)


def sketch(c, normal, name=None):
    """Sketch on the component's base plane whose normal is the given model axis."""
    sk = c.sketches.add(getattr(c, _BASE[normal]))
    sk.isComputeDeferred = True
    if name:
        sk.name = name
    sk.isVisible = False
    return sk


def _sk_info(sk):
    ax, sx = _axis_of(sk.xDirection)
    ay, sy = _axis_of(sk.yDirection)
    n = sk.xDirection.crossProduct(sk.yDirection)
    an, sn = _axis_of(n)
    return ax, ay, an, sn


def _pt(sk, coords):
    """coords: dict model-axis -> mm; returns sketch-space Point3D."""
    p = adsk.core.Point3D.create(coords.get('x', 0) / 10.0, coords.get('y', 0) / 10.0, coords.get('z', 0) / 10.0)
    return sk.modelToSketchSpace(p)


def _neg(expr):
    return '-(%s)' % expr


def _pos_dim(sk, pt, axis_role, expr, val):
    """Dimension a sketch point from the sketch origin along sketch x ('h') or y ('v')."""
    D = adsk.fusion.DimensionOrientations
    o = sk.originPoint
    if abs(val) < 1e-6:
        try:
            if axis_role == 'h':
                sk.geometricConstraints.addVerticalPoints(pt, o)
            else:
                sk.geometricConstraints.addHorizontalPoints(pt, o)
        except Exception:
            pass
        return
    tp = adsk.core.Point3D.create(pt.geometry.x + 0.3, pt.geometry.y + 0.3, 0)
    ori = D.HorizontalDimensionOrientation if axis_role == 'h' else D.VerticalDimensionOrientation
    try:
        d = sk.sketchDimensions.addDistanceDimension(o, pt, ori, tp)
    except RuntimeError as e:
        if 'OVER_CONSTRAINTS' in str(e):
            return  # already fixed by an inferred constraint (e.g. aligned with an earlier centre)
        raise
    d.parameter.expression = 'abs(%s)' % expr


def rect(sk, ctr, size, dims=True):
    """Axis-aligned rectangle. ctr/size: dict model-axis -> expression (the two in-plane axes)."""
    ax, ay, an, sn = _sk_info(sk)
    c = {k: mm(v) for k, v in ctr.items()}
    s = {k: mm(v) for k, v in size.items()}
    lo = {ax: c[ax] - s[ax] / 2, ay: c[ay] - s[ay] / 2}
    hi = {ax: c[ax] + s[ax] / 2, ay: c[ay] + s[ay] / 2}
    p0, p1 = _pt(sk, lo), _pt(sk, hi)
    lines = sk.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
    if not dims:
        return lines
    pts = [l.startSketchPoint for l in lines]
    # corner nearest to the model 'lo' corner
    corner = min(pts, key=lambda q: q.geometry.distanceTo(p0))
    D = adsk.fusion.DimensionOrientations
    # width along sketch x, height along sketch y
    hl = [l for l in lines if abs(l.startSketchPoint.geometry.y - l.endSketchPoint.geometry.y) < 1e-9][0]
    vl = [l for l in lines if abs(l.startSketchPoint.geometry.x - l.endSketchPoint.geometry.x) < 1e-9][0]
    d = sk.sketchDimensions.addDistanceDimension(hl.startSketchPoint, hl.endSketchPoint, D.HorizontalDimensionOrientation,
                                                 adsk.core.Point3D.create(hl.startSketchPoint.geometry.x, hl.startSketchPoint.geometry.y - 0.5, 0))
    d.parameter.expression = size[ax]
    d = sk.sketchDimensions.addDistanceDimension(vl.startSketchPoint, vl.endSketchPoint, D.VerticalDimensionOrientation,
                                                 adsk.core.Point3D.create(vl.startSketchPoint.geometry.x - 0.5, vl.startSketchPoint.geometry.y, 0))
    d.parameter.expression = size[ay]
    _pos_dim(sk, corner, 'h', '(%s) - (%s)/2' % (ctr[ax], size[ax]), lo[ax])
    _pos_dim(sk, corner, 'v', '(%s) - (%s)/2' % (ctr[ay], size[ay]), lo[ay])
    return lines


def circle(sk, ctr, dia, dims=True):
    ax, ay, an, sn = _sk_info(sk)
    c = {k: mm(v) for k, v in ctr.items()}
    cp = _pt(sk, c)
    ci = sk.sketchCurves.sketchCircles.addByCenterRadius(cp, mm(dia) / 20.0)
    if not dims:
        return ci
    d = sk.sketchDimensions.addDiameterDimension(ci, adsk.core.Point3D.create(cp.x + mm(dia) / 20.0, cp.y + 0.2, 0))
    d.parameter.expression = dia
    _pos_dim(sk, ci.centerSketchPoint, 'h', ctr[ax], c[ax])
    _pos_dim(sk, ci.centerSketchPoint, 'v', ctr[ay], c[ay])
    return ci


def poly(sk, pts3, closed=True):
    """Polyline through model-space points (list of dicts). Not dimensioned."""
    sp = [_pt(sk, p) for p in pts3]
    L = sk.sketchCurves.sketchLines
    out = []
    for i in range(len(sp) - (0 if closed else 1)):
        a = out[-1].endSketchPoint if out else sp[i]
        b = sp[(i + 1) % len(sp)]
        if closed and i == len(sp) - 1:
            b = out[0].startSketchPoint
        out.append(L.addByTwoPoints(a, b))
    return out


# ---------------------------------------------------------------- features
def profiles(sk, which='all'):
    sk.isComputeDeferred = False
    col = OC.create()
    profs = list(sk.profiles)
    if which == 'largest':
        profs = [max(profs, key=lambda p: p.areaProperties().area)]
    elif which == 'outer':
        # profiles that are not fully enclosed by another (i.e. drop hole discs)
        profs = [p for p in profs if p.profileLoops.count > 1] or [max(profs, key=lambda p: p.areaProperties().area)]
    elif callable(which):
        profs = [p for p in profs if which(p)]
    for p in profs:
        col.add(p)
    return col


def extrude(c, sk, start, dist, op=NEWB, which='all', name=None, bodies=None):
    """Extrude profiles from `start` to `start+dist` along the +model axis normal to the sketch."""
    ax, ay, an, sn = _sk_info(sk)
    s, d = (start, dist) if sn > 0 else (_neg(start), _neg(dist))
    prof = profiles(sk, which)
    if prof.count == 0:
        raise Exception('no profiles in ' + sk.name)
    inp = c.features.extrudeFeatures.createInput(prof, op)
    if mm(start) != 0:
        inp.startExtent = adsk.fusion.OffsetStartDefinition.create(V.createByString(s))
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V.createByString(d)),
                         adsk.fusion.ExtentDirections.PositiveExtentDirection)
    if bodies is not None:
        inp.participantBodies = bodies
    f = c.features.extrudeFeatures.add(inp)
    if name and op == NEWB:
        for i, b in enumerate(f.bodies):
            b.name = name if f.bodies.count == 1 else '%s %d' % (name, i + 1)
    if name:
        f.name = name
    return f


def box(c, name, ctr, size, op=NEWB, bodies=None):
    """ctr/size: dicts with x,y,z expressions. Returns the body (or feature for non-new ops)."""
    sk = sketch(c, 'z', name)
    rect(sk, {'x': ctr['x'], 'y': ctr['y']}, {'x': size['x'], 'y': size['y']})
    f = extrude(c, sk, '(%s) - (%s)/2' % (ctr['z'], size['z']), size['z'], op, name=name, bodies=bodies)
    return f.bodies.item(0) if op == NEWB else f


def cyl(c, name, axis, ctr, dia, length, op=NEWB, bodies=None):
    """Cylinder along model axis; ctr is its centre point (dict x,y,z)."""
    sk = sketch(c, axis, name)
    inplane = {k: v for k, v in ctr.items() if k != axis}
    circle(sk, inplane, dia)
    f = extrude(c, sk, '(%s) - (%s)/2' % (ctr[axis], length), length, op, which='all', name=name, bodies=bodies)
    return f.bodies.item(0) if op == NEWB else f


def tube(c, name, axis, ctr, od, idia, length):
    sk = sketch(c, axis, name)
    inplane = {k: v for k, v in ctr.items() if k != axis}
    c1 = circle(sk, inplane, od)
    c2 = sk.sketchCurves.sketchCircles.addByCenterRadius(c1.centerSketchPoint, mm(idia) / 20.0)
    d = sk.sketchDimensions.addDiameterDimension(c2, adsk.core.Point3D.create(c1.centerSketchPoint.geometry.x + 0.1, c1.centerSketchPoint.geometry.y + 0.1, 0))
    d.parameter.expression = idia
    f = extrude(c, sk, '(%s) - (%s)/2' % (ctr[axis], length), length, NEWB, which='outer', name=name)
    return f.bodies.item(0)


def edges_where(body, pred):
    col = OC.create()
    for e in body.edges:
        if pred(e):
            col.add(e)
    return col


def is_axis_line(e, axis):
    g = e.geometry
    if g.curveType != adsk.core.Curve3DTypes.Line3DCurveType:
        return False
    a = e.startVertex.geometry
    b = e.endVertex.geometry
    d = [abs(b.x - a.x), abs(b.y - a.y), abs(b.z - a.z)]
    i = 'xyz'.index(axis)
    return d[i] > 1e-6 and all(d[k] < 1e-6 for k in range(3) if k != i)


def fillet(c, edges, r, name=None):
    if edges.count == 0:
        return None
    fi = c.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(edges, V.createByString(r), True)
    f = c.features.filletFeatures.add(fi)
    if name:
        f.name = name
    return f


def chamfer(c, edges, d, name=None):
    if edges.count == 0:
        return None
    ci = c.features.chamferFeatures.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V.createByString(d), True)
    f = c.features.chamferFeatures.add(ci)
    if name:
        f.name = name
    return f


def combine(c, target, tools, op=CUT, keep=False):
    col = OC.create()
    for t in tools:
        col.add(t)
    ci = c.features.combineFeatures.createInput(target, col)
    ci.operation = op
    ci.isKeepToolBodies = keep
    return c.features.combineFeatures.add(ci)


def zfaces(body, top=True):
    fs = [f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType]
    fs = [f for f in fs if abs(abs(f.geometry.normal.z) - 1) < 1e-6]
    return max(fs, key=lambda f: f.pointOnFace.z) if top else min(fs, key=lambda f: f.pointOnFace.z)


# ---------------------------------------------------------------- base-feature solids (non-parametric detail)
TB = adsk.fusion.TemporaryBRepManager.get()


def P(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def base_bodies(c, name, tbodies, names=None):
    bf = c.features.baseFeatures.add()
    bf.name = name
    bf.startEdit()
    out = []
    for i, tb in enumerate(tbodies):
        b = c.bRepBodies.add(tb, bf)
        b.name = names[i] if names else '%s %d' % (name, i + 1)
        out.append(b)
    bf.finishEdit()
    return [c.bRepBodies.itemByName(b.name) for b in out] if names else list(bf.bodies)


# ---------------------------------------------------------------- appearance / material
_LIB = None


def _applib():
    global _LIB
    if _LIB is None:
        _LIB = [l for l in app.materialLibraries if l.name == 'Fusion Appearance Library'][0]
    return _LIB


def appearance(name, base=None, color=None, opacity=None):
    """Get or create a design appearance. base = library appearance to copy; color = (r,g,b)."""
    a = design.appearances.itemByName(name)
    if a:
        return a
    src = _applib().appearances.itemByName(base or name)
    if src is None:
        raise Exception('no library appearance ' + str(base or name))
    a = design.appearances.addByCopy(src, name)
    if color:
        for prop in a.appearanceProperties:
            if prop.objectType == adsk.core.ColorProperty.classType() and prop.id in (
                    'opaque_albedo', 'transparent_color', 'generic_diffuse', 'glazing_transmittance_map', 'metal_f0',
                    'layered_diffuse', 'opaque_luminance_modifier'):
                try:
                    prop.value = adsk.core.Color.create(color[0], color[1], color[2], 255)
                except Exception:
                    pass
    return a


_MAT = None


def material(name):
    global _MAT
    if _MAT is None:
        _MAT = [l for l in app.materialLibraries if l.name == 'Fusion Material Library'][0]
    m = design.materials.itemByName(name)
    if m:
        return m
    src = _MAT.materials.itemByName(name)
    if src is None:
        raise Exception('no material ' + name)
    return design.materials.addByCopy(src, name)


def finish(body, mat=None, look=None):
    if mat:
        body.material = material(mat)
    if look:
        body.appearance = look if isinstance(look, adsk.core.Appearance) else appearance(look)


def done():
    print('\n'.join(LOG[-60:]))


# ---------------------------------------------------------------- v2 additions
BRIDGE = 'http://100.115.45.111:8766/'


def put(name, data, timeout=300):
    if isinstance(data, str):
        data = data.encode()
    urllib.request.urlopen(urllib.request.Request(BRIDGE + name, data=data, method='PUT'), timeout=timeout).read()
    log('put', name, len(data))


def S(sign, expr):
    return ('(%s)' % expr) if sign > 0 else ('-(%s)' % expr)


def B(c, name, x, y, z, w, d, h, mat=None, look=None, op=NEWB, bodies=None):
    """Box by centre x,y and BOTTOM z (expressions)."""
    b = box(c, name, {'x': x, 'y': y, 'z': '(%s) + (%s)/2' % (z, h)}, {'x': w, 'y': d, 'z': h}, op=op, bodies=bodies)
    if op == NEWB:
        finish(b, mat, look)
    return b


def C(c, name, axis, x, y, z, dia, ln, mat=None, look=None, op=NEWB, bodies=None):
    """Cylinder along a model axis, centred on x,y,z."""
    b = cyl(c, name, axis, {'x': x, 'y': y, 'z': z}, dia, ln, op=op, bodies=bodies)
    if op == NEWB:
        finish(b, mat, look)
    return b


def RB(c, name, x, y, z, w, d, h, r, mat=None, look=None):
    """Box with rounded vertical edges."""
    b = B(c, name, x, y, z, w, d, h, mat, look)
    fillet(c, edges_where(b, lambda e: is_axis_line(e, 'z')), r)
    return b


def join(c, target, tools, name=None):
    combine(c, target, tools, JOIN)
    if name:
        target.name = name
    return target


def ring(c, name, axis, x, y, z, od, idia, ln, mat=None, look=None):
    b = tube(c, name, axis, {'x': x, 'y': y, 'z': z}, od, idia, ln)
    finish(b, mat, look)
    return b


GREEN = 'Plastic - Matte (Green)'
BLACK = 'Plastic - Matte (Black)'
GLOSSB = 'Plastic - Glossy (Black)'
ALU = 'Aluminum - Satin'
GREY = 'Plastic - Matte (Gray)'
BRASS = 'Brass - Polished'
STEEL = 'Steel - Satin'
