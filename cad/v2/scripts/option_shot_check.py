# option_shot_check.py: photo-angle render + lidar quick check, scan plane and pan/tilt sweep for the current lidar option.
# Set TAG ('optA' / 'optB') to match lidar_rise, then: python3 cad/v2/scripts/fmcp.py exec cad/v2/scripts/option_shot_check.py
import adsk.core, urllib.request, traceback, json
U = 'http://100.115.45.111:8766/'
TAG = 'optB'

def run(_context: str):
    g = {'__name__': 'sbv2'}
    try:
        for f in ('v2lib.py', 'view.py', 'shots.py'):
            exec(urllib.request.urlopen(U + f, timeout=30).read().decode(), g)
        exec("views(['photo'], suffix='-%s')" % TAG, g)
        g2 = {'__name__': 'sbv2'}
        for f in ('v2lib.py', 'checks.py'):
            exec(urllib.request.urlopen(U + f, timeout=30).read().decode(), g2)
        g2['quick'](('Lidar',), 'lidar-' + TAG)
        sp = g2['scan_plane']()
        sw = g2['sweep']()
        g2['put_json']('checks-lidar-%s.json' % TAG, {'scan_plane': sp, 'sweep': sw, 'scan_z': g2['mm']('scan_z')})
        msg = 'OK\n' + '\n'.join(g['LOG'] + g2['LOG'])
    except Exception:
        msg = 'FAIL\n' + traceback.format_exc()
    print(msg)
