# diag.py: labelled / exploded review images. Runs ONLY in the backup copy
# "Super bot - concept K v1 (backup)" (it moves and hides occurrences; the copy is
# closed without saving). Uploads PNGs plus label anchors (JSON) to the VPS.
import adsk.core, adsk.fusion, json, math, os, tempfile, urllib.request

app = adsk.core.Application.get()
BACKUP = 'Super bot - concept K v1 (backup)'
if app.activeDocument.name != BACKUP:
    raise Exception('diag.py only runs in the backup copy, active is %r' % app.activeDocument.name)
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

# number, component prefix, body name prefix (None = biggest body)
PARTS = [
    (1, 'Chassis plate', 'Chassis plate'), (2, 'Motor JGB37-520 FR', 'gearbox'), (3, 'Wheel mecanum 80 FR', 'hub'),
    (4, 'Motor mount + well liner FR', 'motor mount'), (5, 'Motor mount + well liner FR', 'motor saddle'),
    (6, 'Motor driver BTS7960 FR', 'heatsink'), (7, 'Battery 3S4P', 'cell'), (8, 'Battery 3S4P', 'BMS'),
    (9, 'Battery sled', 'battery sled'), (10, 'Battery sled', 'sled rail'), (11, 'Power placeholders', 'main rocker'),
    (12, 'Power placeholders', 'XT60'), (13, 'Power placeholders', 'buck Pololu'), (14, 'VL53L0X', None),
    (15, 'HC-SR04 front', 'HC-SR04 PCB'), (16, 'HC-SR04 rear', 'HC-SR04 PCB'), (17, 'Upper deck', 'upper deck'),
    (18, 'Upper deck', 'M3 standoff'), (19, 'Raspberry Pi 5', 'Pi 5 PCB'), (20, 'Raspberry Pi 5', 'Active Cooler'),
    (21, 'Raspberry Pi AI HAT+ 2', 'HAT heatsink'), (22, 'ESP32-S3-DevKitC-1 A', 'DevKitC PCB'),
    (23, 'ESP32-S3-DevKitC-1 B', 'DevKitC PCB'), (24, 'BNO085', 'BNO085 PCB'), (25, 'Circuit Playground', 'CPX PCB'),
    (26, 'Circuit Playground', 'CPX mount'), (27, 'Shell - acrylic panels', 'front panel'), (28, 'Shell - acrylic panels', 'side panel'),
    (29, 'Shell - acrylic panels', 'top panel'), (30, 'Shell - corner fender FR', None), (31, 'Shell - panel clips', 'clip'),
    (32, 'Lidar backpack', None), (33, 'Lidar LDROBOT LD19', 'LD19 base'), (34, 'Neck', 'pan bearing hub'),
    (35, 'Servo MG90S pan', 'MG90S body'), (36, 'Neck', 'pan coupler'), (37, 'Neck', 'neck tube'), (38, 'Neck', 'tilt yoke'),
    (39, 'Servo MG90S tilt', 'MG90S body'), (40, 'Neck', 'head tilt bracket'), (41, 'Head', 'head shell front'),
    (42, 'Head', 'head frame'), (43, 'Logitech C270', 'C270 body'), (44, 'Head', 'eye ring bezel'), (45, 'TFT 1.3in', 'TFT module'),
    (46, 'Neck', '6805 bearing'), (47, 'Neck', 'neck thrust collar'), (48, 'Head', 'C270 foam pad'),
]

L1 = ('Upper deck', 'Raspberry Pi 5', 'Raspberry Pi AI HAT', 'ESP32-S3', 'BNO085', 'Circuit Playground', 'HC-SR04 rear')
L2 = ('Shell - acrylic', 'Shell - corner', 'Lidar backpack', 'Lidar LDROBOT')


def level(name):
    if name.startswith('Head'):
        return 'H'
    if name.startswith('Neck'):
        return 'N'
    if name.startswith(L1):
        return 'L1'
    if name.startswith(L2):
        return 'L2'
    return 'L0'


def P(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def anchor(prefix, body):
    for occ in root.allOccurrences:
        if occ.component.name.startswith(prefix):
            bs = [b for b in occ.bRepBodies if body is None or b.name.startswith(body)]
            if bs:
                b = max(bs, key=lambda x: x.volume)
                bb = b.boundingBox
                return adsk.core.Point3D.create((bb.minPoint.x + bb.maxPoint.x) / 2, (bb.minPoint.y + bb.maxPoint.y) / 2,
                                                (bb.minPoint.z + bb.maxPoint.z) / 2)
    return None


def show(levels):
    for occ in root.occurrences:
        occ.isLightBulbOn = level(occ.component.name) in levels


def explode(dz):
    for occ in root.occurrences:
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(0, 0, dz.get(level(occ.component.name), 0) / 10.0)
        occ.transform2 = m


def camera(eye, target, up, fov=26):
    vp = app.activeViewport
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    cam.perspectiveAngle = math.radians(fov)
    vp.camera = cam
    adsk.doEvents()
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.eye = P(*eye)
    cam.target = P(*target)
    cam.upVector = adsk.core.Vector3D.create(*up)
    vp.camera = cam
    vp.refresh()
    adsk.doEvents()


def put(name, data):
    urllib.request.urlopen(urllib.request.Request('http://100.115.45.111:8765/' + name, data=data, method='PUT'), timeout=120).read()


def snap(name, nums):
    vp = app.activeViewport
    w, h = vp.width, vp.height
    path = os.path.join(tempfile.gettempdir(), name + '.png')
    vp.saveAsImageFile(path, w, h)
    labels = []
    for n, pre, body in PARTS:
        if n not in nums:
            continue
        a = anchor(pre, body)
        if a is None:
            continue
        p2 = vp.modelToViewSpace(a)
        labels.append({'n': n, 'x': p2.x, 'y': p2.y})
    put(name + '.png', open(path, 'rb').read())
    put(name + '.json', json.dumps({'w': w, 'h': h, 'labels': labels}).encode())
    os.remove(path)
    print(name, w, h, len(labels))


def main():
    explode({})
    show({'L0'})
    camera((0, 1, 1250), (0, 0, 0), (0, 1, 0))
    snap('diag-level0-top', range(1, 17))
    show({'L1'})
    camera((0, 1, 1250), (0, 0, 60), (0, 1, 0))
    snap('diag-level1-top', range(17, 27))
    show({'N', 'H'})
    camera((330, 560, 260), (0, 40, 120), (0, 0, 1))
    snap('diag-neck-base', [34, 35, 36, 37, 46, 47])
    camera((300, 520, 760), (0, 48, 640), (0, 0, 1))
    snap('diag-head', [38, 39, 40, 41, 43, 44, 45, 48])
    show({'L0', 'L1', 'L2', 'N', 'H'})
    explode({'L1': 170, 'L2': 360, 'N': 360, 'H': 460})
    camera((2100, 2700, 1900), (0, 0, 560), (0, 0, 1))
    snap('diag-exploded', [1, 2, 3, 6, 7, 9, 17, 19, 25, 27, 28, 29, 30, 32, 33, 34, 37, 41])
    explode({})
    show({'L0', 'L1', 'L2', 'N', 'H'})
    camera((0, 2400, 380), (0, 0, 360), (0, 0, 1), fov=20)
    snap('diag-front', [3, 15, 25, 27, 29, 30, 33, 37, 41, 43, 45])
