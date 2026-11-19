# w_dump.py: read-only geometry dump for offline wire routing. Uploads geom.json to the bridge:
# every solid body (top component path, body name, bounding box in mm) and every user parameter.
# python3 cad/v2/scripts/fmcp.py exec cad/v2/scripts/w_dump.py ro
import adsk.core, adsk.fusion, json, urllib.request, traceback
U = 'http://100.115.45.111:8766/'


def run(_context: str):
    try:
        app = adsk.core.Application.get()
        doc = app.activeDocument
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        bodies = []
        for occ in root.allOccurrences:
            for b in occ.bRepBodies:
                bb = b.boundingBox
                bodies.append({'occ': occ.fullPathName, 'name': b.name, 'solid': b.isSolid, 'vis': occ.isVisible and b.isVisible,
                               'lo': [round(v * 10, 2) for v in bb.minPoint.asArray()],
                               'hi': [round(v * 10, 2) for v in bb.maxPoint.asArray()]})
        params = {p.name: {'expr': p.expression, 'mm': round(p.value * 10, 3) if p.unit in ('mm', 'cm') else p.value, 'unit': p.unit, 'comment': p.comment}
                  for p in design.userParameters}
        top = [{'name': o.component.name, 'light': o.isLightBulbOn} for o in root.occurrences]
        out = {'doc': doc.name, 'version': doc.dataFile.versionNumber if doc.dataFile else None, 'timeline': design.timeline.count,
               'top': top, 'params': params, 'bodies': bodies}
        data = json.dumps(out).encode()
        urllib.request.urlopen(urllib.request.Request(U + 'geom.json', data=data, method='PUT'), timeout=120).read()
        print('OK doc=%s v=%s bodies=%d params=%d' % (out['doc'], out['version'], len(bodies), len(params)))
    except Exception:
        print('FAIL\n' + traceback.format_exc())
