"""validate.py: check a step2mesh export is the design state the renders must show.

usage: ~/tools/sb-ocp/bin/python -I cad/v2/render/validate.py /tmp/sbr/v2
Checks: lidar option A (LD19 scan band near z 301, not 467), the wiring harness is there, the
off-the-shelf modules are there and the custom main board is not, no keep-out bodies leak into the render, and lists
the top-level components so new ones can be mapped to materials and exploded groups.
"""
import json, re, sys
import numpy as np

pre = sys.argv[1]
man = json.load(open(pre + '.json'))
blob = np.fromfile(pre + '.bin', dtype=np.uint8)
ok = True


def bb(b):
    v = np.frombuffer(blob, dtype=np.float32, count=b['v_n'] * 3, offset=b['v_off']).reshape(-1, 3)
    return v.min(0), v.max(0)


def find(rx):
    out = []
    for b in man['bodies']:
        key = ' / '.join(p for p in b['path'] if not p.startswith('=>')) + ' :: ' + b['name']
        if re.search(rx, key, re.I):
            out.append((key, b))
    return out


def check(name, cond, detail):
    global ok
    ok &= bool(cond)
    print('%-4s %s: %s' % ('OK' if cond else 'FAIL', name, detail))


tops = sorted(set(next((p for p in b['path'][1:] if not p.startswith('=>')), '?') for b in man['bodies']))
print('top-level components (%d):' % len(tops))
for t in tops:
    print('   ', t)
band = find(r'LD19 window band')
if band:
    mn, mx = bb(band[0][1])
    zc = (mn[2] + mx[2]) / 2
    check('lidar option A', abs(zc - 301) < 15, 'LD19 window band centre z %.1f mm (A ~301, B ~467)' % zc)
else:
    check('lidar option A', False, 'no LD19 window band body')
wires = find(r'wiring|harness')
check('wiring harness', len(wires) >= 15, '%d harness bodies' % len(wires))
# Adam, 19 Nov: v2 uses off-the-shelf modules, not the custom main board
board = find(r'^[^:]*main board')
check('no custom main board', not board, '%d main-board bodies' % len(board))
for what, rx in (('DRV8874 drivers', r'drv8874'), ('ESP32-S3 dev board', r'esp32-s3-devkitc|devkitc'),
                 ('power distribution / INA226', r'power distribution|ina226|pdb'), ('Pololu bucks', r'd36v|buck')):
    hits = find(rx)
    check(what, len(hits) > 0, '%d bodies' % len(hits))
ko = find(r'keep-out')
check('no keep-outs', not ko, '%d keep-out bodies (scene.py skips them by name)' % len(ko))
print('bodies', len(man['bodies']), 'triangles', sum(b['t_n'] for b in man['bodies']))
print('VALID' if ok else 'NOT VALID')
sys.exit(0 if ok else 1)
