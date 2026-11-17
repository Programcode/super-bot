# shots.py: deliverable viewport images, the exploded view and the zoomed callouts.
# Needs view.py loaded first (cam, save, vis). Nothing is left changed: visibility, opacity,
# occurrence transforms and custom graphics are restored before each function returns, and
# the loader does not save the document after a shot run.
import json, os, tempfile

VIEWS = {
    # name: (eye, target, fov). The robot is about 306 x 256 x 430 mm.
    'photo': ((-920, 1320, 640), (0, 0, 220), 20),     # matches the target photo's camera (~35 deg off the front)
    'front': ((0, 1500, 230), (0, 0, 215), 22),
    'side': ((1500, 0, 230), (0, 0, 215), 22),
    'rear': ((0, -1500, 230), (0, 0, 215), 22),
    'iso': ((850, 1050, 760), (0, 0, 200), 24),
    'iso-rear': ((-800, -1000, 720), (0, 0, 200), 24),
    'top': ((0, 1, 1650), (0, 0, 0), 22),
    'head': ((-330, 760, 560), (0, 20, 370), 22),
}


def all_on():
    for o in root.occurrences:
        o.isLightBulbOn = True


def views(names=None):
    all_on()
    for n in (names or list(VIEWS)):
        e, t, f = VIEWS[n]
        cam(e, t, (0, 1, 0) if n == 'top' else (0, 0, 1), fov=f)
        save_t('v2-' + n, 1600, 1200)


# ---------------------------------------------------------------- exploded
GROUPS = [
    ('base', 0, ('Chassis', 'Drive', 'Battery', 'Power connectors', 'Cliff', 'Front ultrasonic')),
    ('frame', 170, ('Frame', 'Motor driver', 'Raspberry Pi', 'Pi 5 V', 'ESP32', 'Circuit Playground', 'BNO085',
                    'Power distribution', 'Audio', 'Servo 6 V', 'Main power', 'Wiring')),
    ('top', 330, ('Head joint fixed', 'Lidar')),
    ('head', 450, ('Head pan rotor',)),
]
SHELL_OUT = 210


def _grp(name):
    for g, dz, pre in GROUPS:
        if name.startswith(pre):
            return dz
    return None


def exploded():
    all_on()
    moved = []
    for o in root.occurrences:
        dz = _grp(o.component.name)
        if dz:
            m = adsk.core.Matrix3D.create()
            m.translation = adsk.core.Vector3D.create(0, 0, dz / 10.0)
            o.transform2 = m
            moved.append(o)
    shell = [o for o in root.occurrences if o.component.name.startswith('Shell')][0]
    cg = root.customGraphicsGroups.add()
    look = design.appearances.itemByName('SB Smoked PETG')
    for b in shell.component.bRepBodies:
        if not b.isSolid or not b.isVisible or not b.name.startswith(('front wall', 'rear wall', 'side wall', 'top half', 'battery door')):
            continue
        bb = b.boundingBox
        cx, cy = (bb.minPoint.x + bb.maxPoint.x) * 5, (bb.minPoint.y + bb.maxPoint.y) * 5
        dx = SHELL_OUT if cx > 60 else (-SHELL_OUT if cx < -60 else 0)
        dy = SHELL_OUT if cy > 60 else (-SHELL_OUT if cy < -60 else 0)
        dz = 0
        if b.name.startswith('top half'):
            dx, dy, dz = 0, (70 if 'front' in b.name else -70), 520
        elif b.name.startswith(('front wall', 'rear wall', 'side wall')):
            dz = 170
        tb = TB.copy(b)
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(dx / 10.0, dy / 10.0, dz / 10.0)
        TB.transform(tb, m)
        g = cg.addBRepBody(tb)
        g.color = adsk.fusion.CustomGraphicsSolidColorEffect.create(adsk.core.Color.create(96, 101, 112, 255))
    shell.isLightBulbOn = False
    try:
        app.activeViewport.refresh()
        adsk.doEvents()
        cam((-1250, 1700, 1050), (0, 0, 420), (0, 0, 1), fov=26)
        save_t('v2-exploded', 1600, 1500)
    finally:
        cg.deleteMe()
        shell.isLightBulbOn = True
        for o in moved:
            o.transform2 = adsk.core.Matrix3D.create()
        app.activeViewport.refresh()
    log('exploded ok', len(moved))


# ---------------------------------------------------------------- callouts
def _occ_bodies(prefix):
    out = []
    for o in root.allOccurrences:
        if o.component.name.startswith(prefix):
            out += [b for b in o.bRepBodies if b.isSolid]
    return out


def _body(prefix, body):
    bs = [b for b in _occ_bodies(prefix) if body is None or b.name.startswith(body)]
    return max(bs, key=lambda x: x.volume) if bs else None


def _fade(prefix, body, op):
    for b in _occ_bodies(prefix):
        if body is None or b.name.startswith(body):
            b.opacity = op


CO = {}


def callout(name, title, show, fade, eye, target, items):
    CO[name] = dict(title=title, show=show, fade=fade, cam=(eye, target), items=items)


callout('wheel-corner', 'Wheel corner (front right): JGB37-520 19:1 inside, 100 mm mecanum outside',
        ['Drive FR', 'Chassis plate', 'Shell', 'Frame'], [('Shell', None, 0.2), ('Frame', None, 0.35)],
        (430, 420, 200), (110, 70, 60),
        [('Mecanum wheel 100 x 50 mm, 9 rollers (X layout)', 'Wheel mecanum 100 FR', 'roller 1', None),
         ('Gearbox 19:1, 530 rpm', 'Motor JGB37-520 19to1 FR', 'gearbox', None),
         ('Motor can, 12 V', 'Motor JGB37-520 19to1 FR', 'motor can', None),
         ('Hall encoder (11 PPR)', 'Motor JGB37-520 19to1 FR', 'encoder', None),
         ('Printed motor mount, 6x M3 on PCD 31', 'Motor mount FR', 'motor mount', None),
         ('Motor saddle (printed)', 'Motor mount FR', 'motor saddle', None),
         ('Side wall U-slot: lifts off over the shaft', 'Shell', 'side wall right', None),
         ('Chassis plate, 6 mm birch ply, 30 mm ground clearance', 'Chassis plate', None, None)])
callout('battery', 'Battery: 3S4P block on a sled that slides out the back',
        ['Battery', 'Power connectors', 'Chassis plate', 'Shell', 'Drive RR', 'Drive RL'], [('Shell', None, 0.2)],
        (380, -520, 260), (0, -30, 70),
        [('3S4P 18650 block, 2 x 3 x 2 cells, ~130 Wh', 'Battery 3S4P', 'cell', None),
         ('BMS 3S 20 A on top of the pack', 'Battery 3S4P', 'BMS', None),
         ('15 A mini blade fuse right after the BMS', 'Battery 3S4P', 'fuse holder 15A', None),
         ('Charge fuse 5 A', 'Battery 3S4P', 'charge fuse', None),
         ('Battery sled (printed)', 'Battery sled', 'battery sled', None),
         ('Sled rails (printed)', 'Battery sled', 'sled rail', None),
         ('Battery door = shell piece, carries the charge jack', 'Shell', 'battery door', None),
         ('Charge jack 5.5 x 2.1 (works with the loop key out)', 'Power connectors', 'DC jack', None),
         ('XT60 blind-mates in a bulkhead under the spine', 'Power connectors', 'XT60 female', None)])
callout('chimney', 'Front chimney: boards flat on the spine, seen through the front wall',
        ['Frame', 'Raspberry Pi', 'Pi 5 V', 'ESP32-S3-DevKitC-1 A', 'Motor driver', 'Circuit Playground', 'Shell', 'Wiring'],
        [('Shell', None, 0.12)],
        (-260, 640, 230), (0, 60, 170),
        [('Raspberry Pi 5 8 GB (ports face the right wall)', 'Raspberry Pi 5', 'Pi 5 PCB', None),
         ('AI HAT+ 2, heatsink fins vertical in the draft', 'Raspberry Pi AI HAT', 'HAT heatsink', None),
         ('4x DRV8874 on a perfboard (enable shared with the CPX watchdog)', 'Motor driver board', 'DRV8874 carrier', None),
         ('ESP32-S3 in a printed cradle', 'ESP32-S3-DevKitC-1 A', 'DevKitC PCB', None),
         ('CPX: status LEDs + watchdog', 'Circuit Playground', 'CPX PCB', None),
         ('LED bar: 8x WS2812B behind a smoked diffuser', 'Circuit Playground', 'LED bar carrier', None),
         ('Intake slots above the front motors', None, None, (0, 100, 98)),
         ('Exhaust vents in the top deck and the front top half', None, None, (36, 70, 278)),
         ('Spine (4 mm ply): back wall of the chimney', 'Frame', 'spine', None)])
callout('back-and-sides', 'Behind the spine: power distribution, buck converters, IMU, audio',
        ['Frame', 'Power distribution', 'Pi 5 V', 'BNO085', 'Audio', 'Servo 6 V', 'Main power', 'ESP32-S3-DevKitC-1 B', 'Battery', 'Wiring'],
        [('Frame', None, 0.35)],
        (-430, -460, 330), (-20, -10, 160),
        [('PDB: XT60 in, 4x XT30 out (left cheek)', 'Power distribution', 'PDB perfboard', None),
         ('INA226 + 2 mOhm shunt', 'Power distribution', 'INA226', None),
         ('5 V 5.5 A buck right behind the Pi', 'Pi 5 V', 'D36V50F5', None),
         ('BNO085 IMU near the centre', 'BNO085', 'BNO085 PCB', None),
         ('40 mm speaker, rear grille', 'Audio MAX98357A', 'speaker 40', None),
         ('XT60 loop key = main switch', 'Main power', 'loop key', None),
         ('Rear plate (4 mm ply)', 'Frame', 'rear plate', None),
         ('Battery block below', 'Battery 3S4P', 'cell', None)])
callout('right-cheek', 'Right cheek: spare ESP32 cradle, amp, servo buck (seen through the right wall)',
        ['Frame', 'ESP32-S3-DevKitC-1 B', 'Audio', 'Servo 6 V', 'Shell', 'Drive FR', 'Drive RR'], [('Shell', None, 0.15)],
        (560, 140, 230), (80, -5, 160),
        [('Empty cradle for a second ESP32-S3', 'ESP32-S3-DevKitC-1 B', 'printed cradle', None),
         ('MAX98357A I2S amp', 'Audio MAX98357A', 'MAX98357A', None),
         ('Servo 6 V buck (own rail, keeps servo spikes off the Pi)', 'Servo 6 V', 'D36V28F6', None),
         ('Side cheek (4 mm ply)', 'Frame', 'side cheek right', None),
         ('Cheek pillar (printed)', 'Frame', 'cheek pillar', None)])
callout('head-joint', 'Gimbal: plinth bearing, under-deck gears, knuckle, turret (plinth, turret, deck see-through)',
        ['Head joint fixed', 'Head pan rotor', 'Frame'], [('Head joint fixed', 'plinth', 0.25), ('Head pan rotor', 'turret', 0.3), ('Frame', None, 0.25),
                                                           ('Head pan rotor', 'head shell', 0.3)],
        (-300, 420, 360), (0, 20, 280),
        [('Square plinth (printed), 4 visible M3', 'Head joint fixed', 'plinth', None),
         ('6805 bearing, upper (in the plinth)', 'Head joint fixed', '6805 bearing 25x37x7 upper', None),
         ('6805 bearing, lower (under the deck)', 'Head joint fixed', '6805 bearing 25x37x7 lower', None),
         ('Thrust collar: head weight on the bearing, not the servo', 'Head pan rotor', 'thrust collar', None),
         ('Hollow 25 mm shaft: ribbon + leads inside', 'Head pan rotor', 'pan shaft', None),
         ('Pan gears 36T:36T (printed)', 'Head pan rotor', 'pan shaft gear', None),
         ('Pan MG90S on a printed shelf', 'Servo MG90S pan', 'MG90S body', None),
         ('Knuckle: the lidar scan plane passes here', 'Head pan rotor', 'knuckle sleeve', None),
         ('Tilt MG90S lying in the turret', 'Servo MG90S tilt', 'MG90S body', None),
         ('Tilt on 2x 6800 bearings', 'Head pan rotor', '6800 bearing 10x19x5 right', None)])
callout('head', 'Head: Camera Module 3 eye, 1.3" TFT face, mic ear (shell see-through)',
        ['Head pan rotor'], [('Head tilt rotor', 'head shell', 0.25)],
        (-200, 560, 470), (0, 20, 390),
        [('Raspberry Pi Camera Module 3', 'Raspberry Pi Camera Module 3', 'CM3 PCB', None),
         ('Eye-ring bezel (printed)', 'Head tilt rotor', 'eye ring bezel', None),
         ('1.3" TFT 240 x 240 (cartoon eyes)', 'TFT 1.3in', 'TFT glass module', None),
         ('INMP441 mic behind the "ear"', 'Mic INMP441', 'INMP441', None),
         ('Head frame (printed)', 'Head tilt rotor', 'head frame', None),
         ('Head shell, front half (smoked PETG)', 'Head tilt rotor', 'head shell front', None),
         ('Tilt fork (printed)', 'Head tilt rotor', 'tilt fork', None)])
callout('lidar', 'Lidar pod at the rear left: LD19 sunk in a vented pod',
        ['Lidar', 'Head joint fixed', 'Head pan rotor', 'Frame', 'Shell'], [('Shell', None, 0.3)],
        (-560, -420, 420), (-40, -40, 290),
        [('LDROBOT LD19 (scan plane 27 mm above its ears)', 'Lidar LDROBOT LD19', 'LD19 rotating head', None),
         ('Vented pod (printed), bolted to the top deck', 'Lidar pod', 'lidar pod', None),
         ('Scan plane: under the turret, over the plinth', 'Lidar LDROBOT LD19', 'LD19 window band', None),
         ('Top half rear: slides back off the pod', 'Shell', 'top half rear', None)])
callout('shell-retention', 'Shell: 7 printed pieces, drop-in tabs at the bottom, 6 x 3 mm magnets at the top',
        ['Shell', 'Frame', 'Chassis plate'], [('Shell', None, 0.45)],
        (480, 470, 300), (40, 50, 150),
        [('Front wall incl. both corner rounds (200 x 236, fits a 256 bed)', 'Shell', 'front wall', None),
         ('Side wall (flat)', 'Shell', 'side wall right', None),
         ('Top half front (slides forward off the plinth)', 'Shell', 'top half front', None),
         ('Magnet pair: wall top to a block under the deck', 'Shell', 'magnet 6x3 (panel) front', None),
         ('Drop-in tab into a printed clip on the plate edge', 'Shell', 'panel clip (printed) front', None),
         ('Top-half magnets onto the top deck', 'Shell', 'magnet 6x3 (panel) top F', None)])


def shoot(name):
    spec = CO[name]
    for o in root.occurrences:
        o.isLightBulbOn = any(o.component.name.startswith(s) for s in spec['show'])
    for pre, body, op in spec['fade']:
        _fade(pre, body, op)
    try:
        cam(spec['cam'][0], spec['cam'][1], (0, 0, 1), fov=24)
        vp = app.activeViewport
        w, h = vp.width, vp.height
        path = os.path.join(tempfile.gettempdir(), 'co-' + name + '.png')
        o = adsk.core.SaveImageFileOptions.create(path)
        o.width, o.height, o.isAntiAliased, o.isBackgroundTransparent = w, h, True, True
        vp.saveAsImageFileWithOptions(o)
        # modelToViewSpace may return physical (Retina) pixels; the camera target must land at the image centre
        tc = vp.modelToViewSpace(P(*spec['cam'][1]))
        sx, sy = (w / 2.0) / tc.x, (h / 2.0) / tc.y
        labels = []
        for text, pre, body, pt in spec['items']:
            if pt is not None:
                a = P(*pt)
            else:
                b = _body(pre, body)
                if b is None:
                    log('missing', name, text)
                    continue
                bb = b.boundingBox
                a = adsk.core.Point3D.create((bb.minPoint.x + bb.maxPoint.x) / 2, (bb.minPoint.y + bb.maxPoint.y) / 2, (bb.minPoint.z + bb.maxPoint.z) / 2)
            p2 = vp.modelToViewSpace(a)
            labels.append({'text': text, 'x': p2.x * sx, 'y': p2.y * sy})
        put('co-' + name + '.png', open(path, 'rb').read())
        put('co-' + name + '.json', json.dumps({'w': w, 'h': h, 'title': spec['title'], 'labels': labels}))
    finally:
        for pre, body, op in spec['fade']:
            _fade(pre, body, 1.0)
        all_on()


def callouts(names=None):
    for n in (names or list(CO)):
        shoot(n)
    all_on()
