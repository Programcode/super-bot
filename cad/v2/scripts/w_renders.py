# w_renders.py: deliverable wiring renders (shell hidden), 1600x1200, to the bridge as <name>.png.
# (made from w_look.py) Edit SHOTS (or let a wrapper substitute it), then
# python3 cad/v2/scripts/fmcp.py exec cad/v2/scripts/w_look.py
# Each shot: (name, eye, target, hide-prefixes). Visibility is restored afterwards.
import adsk.core, urllib.request, traceback
U = 'http://100.115.45.111:8766/'
SHOTS = [('wiring-front', (30, 560, 175), (0, 40, 160), ('Shell', 'Bumpers')),
         ('wiring-right', (560, 10, 175), (0, 0, 160), ('Shell', 'Drive FR', 'Drive RR')),
         ('wiring-left', (-560, 10, 175), (0, 0, 160), ('Shell', 'Drive FL', 'Drive RL')),
         ('wiring-rear-iso', (-330, -420, 380), (0, 0, 160), ('Shell', 'Lidar pod')),
         ('wiring-head', (170, 330, 420), (0, 20, 345), ('Shell',))]


def run(_context: str):
    g = {'__name__': 'sbv2'}
    try:
        for f in ('v2lib.py', 'view.py'):
            exec(urllib.request.urlopen(U + f, timeout=30).read().decode(), g)
        root = g['root']
        before = {o.component.name: o.isLightBulbOn for o in root.occurrences}
        try:
            for name, eye, tgt, hide in SHOTS:
                for o in root.occurrences:
                    o.isLightBulbOn = before[o.component.name] and not any(o.component.name.startswith(p) for p in hide)
                g['cam'](eye, tgt, fov=24)
                g['save'](name)
        finally:
            for o in root.occurrences:
                o.isLightBulbOn = before[o.component.name]
        print('OK ' + ' '.join(s[0] for s in SHOTS))
    except Exception:
        print('FAIL\n' + traceback.format_exc())
