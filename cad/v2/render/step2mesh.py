"""step2mesh.py: STEP assembly -> one triangle mesh per solid body, with names and colours.

usage: ~/tools/sb-ocp/bin/python -I step2mesh.py in.step out_prefix [deflection_mm=0.03] [angle_deg=6]

Writes out_prefix.json (manifest) and out_prefix.bin (float32 xyz in mm, world coordinates, then
uint32 triangle indices, per body). Each B-rep face keeps its own vertices, so Blender's smooth
shading gives soft curved faces and hard CAD edges without an auto-smooth pass.

Manifest entry per body: path (component names from the root, Fusion's ":1" suffixes stripped),
name (the Fusion body name when the STEP carries it), colour per face group, offsets into .bin.
Runs on the VPS in the venv with cadquery-ocp 7.8 (OCP 8.0 lacks the collection bindings).
"""
import json, math, sys, time
import numpy as np
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.Quantity import Quantity_Color
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_SHELL, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.TopLoc import TopLoc_Location
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.gp import gp_Trsf
from OCP.BRepTools import BRepTools

STATS = {'retry': 0, 'failed': 0, 'failed_in': set()}
import re


def strip(n):
    return re.sub(r':\d+$', '', n or '')


def main():
    src, prefix = sys.argv[1], sys.argv[2]
    defl = float(sys.argv[3]) if len(sys.argv) > 3 else 0.03
    ang = math.radians(float(sys.argv[4]) if len(sys.argv) > 4 else 6)
    t0 = time.time()
    doc = TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True)
    r.SetNameMode(True)
    assert r.ReadFile(src) == IFSelect_RetDone, 'STEP read failed: ' + src
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    # XCAF drops the solids' own names (Fusion body names); get them from the STEP entities instead
    tr = r.ChangeReader().WS().TransferReader()

    def name(l):
        a = TDataStd_Name()
        return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else ''

    def entity_name(s):
        try:
            ent = tr.EntityFromShapeResult(s, 1)
            return ent.Name().ToCString() if ent is not None else ''
        except Exception:
            return ''

    def colour_of_shape(s):
        c = Quantity_Color()
        for t in (XCAFDoc_ColorType.XCAFDoc_ColorSurf, XCAFDoc_ColorType.XCAFDoc_ColorGen):
            if ct.GetColor(s, t, c):
                return (c.Red(), c.Green(), c.Blue())
        return None

    def colour_of_label(l):
        c = Quantity_Color()
        for t in (XCAFDoc_ColorType.XCAFDoc_ColorSurf, XCAFDoc_ColorType.XCAFDoc_ColorGen):
            if ct.GetColor_s(l, t, c):
                return (c.Red(), c.Green(), c.Blue())
        return None

    bodies, chunks = [], []
    off = [0]

    def emit(entry, verts, tris):
        v = np.asarray(verts, np.float32).reshape(-1, 3)
        t = np.asarray(tris, np.uint32).reshape(-1, 3)
        entry['v_off'], entry['v_n'] = off[0], len(v)
        chunks.append(v.tobytes())
        off[0] += v.nbytes
        entry['t_off'], entry['t_n'] = off[0], len(t)
        chunks.append(t.tobytes())
        off[0] += t.nbytes
        bodies.append(entry)

    def mesh_solid(solid, trsf, path, bname, base_col):
        BRepMesh_IncrementalMesh(solid, defl, False, ang, True)
        verts, tris, groups = [], [], []   # groups: (first tri, colour)
        exp = TopExp_Explorer(solid, TopAbs_FACE)
        cur = None
        while exp.More():
            f = TopoDS.Face_s(exp.Current())
            loc = TopLoc_Location()
            tri = BRep_Tool.Triangulation_s(f, loc)
            if tri is None or tri.NbTriangles() == 0:
                STATS['retry'] += 1
                # OCCT fails on some of Fusion's conical faces (mecanum roller tapers): mesh a NURBS copy
                from OCP.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
                for d, a in ((defl, ang), (defl * 4, ang * 2)):
                    f2 = TopoDS.Face_s(BRepBuilderAPI_NurbsConvert(f, True).Shape())
                    BRepMesh_IncrementalMesh(f2, d, False, a, False)
                    loc = TopLoc_Location()
                    tri = BRep_Tool.Triangulation_s(f2, loc)
                    if tri is not None and tri.NbTriangles():
                        f = f2
                        break
                else:
                    from OCP.BRepAdaptor import BRepAdaptor_Surface
                    STATS.setdefault('types', set()).add(str(BRepAdaptor_Surface(f).GetType()))
                    STATS['failed'] += 1
                    STATS['failed_in'].add(bname)
            if tri is not None:
                fc = colour_of_shape(f) or base_col
                if fc != cur:
                    groups.append([len(tris) // 3, fc])
                    cur = fc
                tr = trsf.Multiplied(loc.Transformation())
                base = len(verts) // 3
                for i in range(1, tri.NbNodes() + 1):
                    p = tri.Node(i).Transformed(tr)
                    verts += (p.X(), p.Y(), p.Z())
                rev = f.Orientation() == TopAbs_REVERSED
                for i in range(1, tri.NbTriangles() + 1):
                    a, b, c = tri.Triangle(i).Get()
                    if rev:
                        b, c = c, b
                    tris += (base + a - 1, base + b - 1, base + c - 1)
            exp.Next()
        if tris:
            emit({'path': path, 'name': bname, 'groups': groups}, verts, tris)

    def walk(l, trsf, path, inherited):
        lab = l
        if st.IsReference_s(l):
            ref = TDF_Label()
            st.GetReferredShape_s(l, ref)
            lab = ref
            trsf = trsf.Multiplied(st.GetLocation_s(l).Transformation())
        nm = strip(name(l)) or strip(name(lab))
        col = colour_of_label(l) or colour_of_label(lab) or inherited
        if st.IsAssembly_s(lab):
            ch = TDF_LabelSequence()
            st.GetComponents_s(lab, ch)
            for i in range(1, ch.Length() + 1):
                walk(ch.Value(i), trsf, path + [nm], col)
            return
        shape = st.GetShape_s(lab)
        exp = TopExp_Explorer(shape, TopAbs_SOLID)
        k = 0
        while exp.More():
            s = exp.Current()
            k += 1
            mesh_solid(s, trsf, path + [nm], entity_name(s) or '%s body %d' % (nm, k), colour_of_shape(s) or col)
            exp.Next()
        if k == 0:   # open shells / surface bodies (Fusion writes the face graphic this way)
            exp = TopExp_Explorer(shape, TopAbs_SHELL)
            while exp.More():
                s = exp.Current()
                k += 1
                mesh_solid(s, trsf, path + [nm], entity_name(s) or '%s surface %d' % (nm, k), colour_of_shape(s) or col)
                exp.Next()

    roots = TDF_LabelSequence()
    st.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), gp_Trsf(), [], None)
    with open(prefix + '.bin', 'wb') as fh:
        for c in chunks:
            fh.write(c)
    json.dump({'source': src, 'units': 'mm', 'deflection_mm': defl, 'bodies': bodies},
              open(prefix + '.json', 'w'), indent=0)
    ntri = sum(b['t_n'] for b in bodies)
    print('faces re-meshed %d, still failed %d in %s' % (STATS['retry'], STATS['failed'], sorted(STATS['failed_in'])[:20]))
    print('failed surface types', STATS.get('types'))
    print('bodies %d  triangles %d  %.1f MB  %.1fs' % (len(bodies), ntri, off[0] / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
