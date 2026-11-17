# shots.py: deliverable viewport images, the exploded view and the zoomed callouts.
# Needs view.py loaded first (cam, save, vis). Nothing is left changed: visibility, opacity,
# occurrence transforms and custom graphics are restored before each function returns, and
# the loader does not save the document after a shot run.
import json, os, tempfile

VIEWS = {
    'front': ((0, 2600, 270), (0, 0, 250), 20),
    'side': ((2600, 0, 270), (0, 0, 250), 20),
    'rear': ((0, -2600, 270), (0, 0, 250), 20),
    'iso': ((1450, 1850, 1150), (0, 0, 230), 22),
    'iso-rear': ((-1350, -1700, 1050), (0, 0, 230), 22),
    'top': ((0, 1, 2800), (0, 0, 0), 20),
    'head': ((330, 700, 600), (0, 35, 470), 20),
}


def all_on():
    for o in root.occurrences:
        o.isLightBulbOn = True


def views(names=None):
    all_on()
    for n in (names or list(VIEWS)):
        e, t, f = VIEWS[n]
        cam(e, t, (0, 1, 0) if n == 'top' else (0, 0, 1), fov=f)
        save('v2-' + n, 1600, 1200)


# ---------------------------------------------------------------- exploded
GROUPS = [
    ('base', 0, ('Chassis', 'Drive', 'Battery', 'Power connectors', 'Motor driver', 'Cliff', 'Charge', 'Front ultrasonic', 'L0 posts')),
    ('L1', 150, ('L1 deck', 'Power distribution', 'BNO085', 'Audio')),
    ('spine', 300, ('Spine', 'Raspberry Pi', 'Pi 5 V', 'ESP32', 'Circuit Playground', 'Mic', 'Servo 6 V', 'Corner tie rods')),
    ('top', 470, ('Top deck', 'Main power', 'Head joint fixed', 'Lidar')),
    ('head', 610, ('Head pan rotor',)),
]
SHELL_OUT = 230


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
    shell.isLightBulbOn = False
    cg = root.customGraphicsGroups.add()
    look = design.appearances.itemByName('SB Smoked PETG')
    for b in shell.component.bRepBodies:
        if not b.isSolid or not b.isVisible:
            continue
        bb = b.boundingBox
        cx, cy = (bb.minPoint.x + bb.maxPoint.x) * 5, (bb.minPoint.y + bb.maxPoint.y) * 5
        dx = SHELL_OUT if cx > 100 else (-SHELL_OUT if cx < -100 else 0)
        dy = SHELL_OUT if cy > 100 else (-SHELL_OUT if cy < -100 else 0)
        dz = 0
        if b.name.startswith('top half'):
            dx, dy, dz = (90 if 'right' in b.name else -90), 0, 820
        elif b.name.startswith(('upper wall', 'corner post')):
            dz = 330
        tb = TB.copy(b)
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(dx / 10.0, dy / 10.0, dz / 10.0)
        TB.transform(tb, m)
        g = cg.addBRepBody(tb)
        if look:
            g.color = adsk.fusion.CustomGraphicsAppearanceColorEffect.create(look)
    try:
        cam((2600, 3300, 2200), (0, 0, 560), (0, 0, 1), fov=22)
        save('v2-exploded', 1600, 1500)
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


callout('wheel-corner', 'Wheel corner (front right): JGB37-520 19:1, 100 mm mecanum, printed mount',
        ['Drive FR', 'Chassis plate', 'Motor driver board', 'L1 deck', 'Shell'], [('Shell', None, 0.18), ('L1 deck', None, 0.35)],
        (520, 470, 230), (110, 95, 60),
        [('Mecanum wheel 100 mm, 9 rollers (X layout)', 'Wheel mecanum 100 FR', 'roller 1', None),
         ('Gearbox 19:1, 530 rpm', 'Motor JGB37-520 19to1 FR', 'gearbox', None),
         ('Motor can, 12 V', 'Motor JGB37-520 19to1 FR', 'motor can', None),
         ('Hall encoder (11 PPR)', 'Motor JGB37-520 19to1 FR', 'encoder', None),
         ('Motor mount + wheel-well liner (printed), 6x M3', 'Motor mount + well liner FR', 'motor mount', None),
         ('Motor saddle (printed)', 'Motor mount + well liner FR', 'motor saddle', None),
         ('Corner post = fender, 12 mm above the tyre', 'Shell', 'corner post FR', None),
         ('Chassis plate, 6 mm birch ply, 30 mm ground clearance', 'Chassis plate', None, None),
         ('Motor driver board, 4x DRV8874', 'Motor driver board', 'perfboard', None)])
callout('battery', 'Battery sled: slides out the right side, blind-mates an XT60',
        ['Battery', 'Power connectors', 'Chassis plate', 'Cliff', 'Shell', 'L0 posts'], [('Shell', None, 0.2)],
        (560, -380, 330), (20, 0, 50),
        [('3S4P 18650 block, 2x3x2 cells, ~130 Wh', 'Battery 3S4P', 'cell', None),
         ('BMS 3S 20 A', 'Battery 3S4P', 'BMS', None),
         ('15 A mini blade fuse, right after the BMS', 'Battery 3S4P', 'fuse holder', None),
         ('Battery sled (printed)', 'Battery sled', 'battery sled', None),
         ('Sled rails (printed)', 'Battery sled', 'sled rail', None),
         ('XT60 bulkhead: the sled plugs in as it slides home', 'Battery sled', 'XT60 bulkhead', None),
         ('XT60 male on the sled', 'Power connectors', 'XT60 male', None),
         ('Right lower skirt = battery door (2x M3 to the sled)', 'Shell', 'lower skirt right', None),
         ('Right cliff sensor sits under the plate, clear of the sled', 'Cliff sensors', 'VL53L0X right PCB', None)])
callout('level0', 'Level 0 from above: drivers, cliff sensors, charge port, ultrasonic spot',
        ['Chassis plate', 'Drive', 'Battery', 'Power connectors', 'Motor driver', 'Cliff', 'Charge', 'Front ultrasonic', 'L0 posts'], [],
        (0, 120, 900), (0, 10, 40),
        [('4x Pololu DRV8874 on a perfboard, enable line shared with the CPX watchdog', 'Motor driver board', 'DRV8874 carrier', None),
         ('Motor screw terminals', 'Motor driver board', 'motor terminals', None),
         ('Optional HC-SR04P holder (knock-outs in the skirt)', 'Front ultrasonic', 'HC-SR04P holder', None),
         ('Charge jack 5.5x2.1, rear, pack side of the loop key', 'Charge port', 'DC jack', None),
         ('Charge fuse 5 A', 'Charge port', 'charge fuse', None),
         ('L0 post: M4 rod in 8 mm alu tube', 'L0 posts', 'L0 post tube', None),
         ('Battery block (sled)', 'Battery 3S4P', 'cell', None),
         ('XT60 bulkhead', 'Battery sled', 'XT60 bulkhead', None)])
callout('level1', 'Level 1 deck: power distribution, IMU, audio',
        ['L1 deck', 'Power distribution', 'BNO085', 'Audio', 'Spine', 'Corner tie rods'], [('Spine', None, 0.3)],
        (-420, -520, 470), (-40, -20, 120),
        [('Power distribution board: XT60 in, 4x XT30 out', 'Power distribution', 'PDB perfboard', None),
         ('INA226 + 2 mOhm shunt: battery volts and amps', 'Power distribution', 'INA226', None),
         ('12 V bus bar', 'Power distribution', 'bus bar', None),
         ('BNO085 IMU at the centre of rotation', 'BNO085', 'BNO085 PCB', None),
         ('MAX98357A I2S amp', 'Audio MAX98357A', 'MAX98357A', None),
         ('40 mm speaker behind the left grille', 'Audio MAX98357A', 'speaker 40', None),
         ('Speaker bracket (printed)', 'Audio MAX98357A', 'speaker bracket', None),
         ('L1 deck, 4 mm birch ply', 'L1 deck', None, None),
         ('Corner tie rod: M5 in 10 mm alu tube', 'Corner tie rods', 'tie tube', None)])
callout('chimney', 'Front chimney: Pi 5 stack standing on the spine, ESP32, CPX ring',
        ['Spine', 'Raspberry Pi', 'Pi 5 V', 'ESP32', 'Circuit Playground', 'Mic', 'L1 deck', 'Top deck', 'Shell'],
        [('Shell', None, 0.12), ('Top deck', None, 0.4)],
        (420, 760, 300), (20, 100, 230),
        [('Raspberry Pi 5 8 GB, standing (ports face the right panel)', 'Raspberry Pi 5', 'Pi 5 PCB', None),
         ('AI HAT+ 2 heatsink, fins vertical in the draft', 'Raspberry Pi AI HAT', 'HAT heatsink', None),
         ('5 V 5.5 A buck right next to the Pi USB-C', 'Pi 5 V', 'D36V50F5', None),
         ('ESP32-S3 in a printed cradle', 'ESP32-S3-DevKitC-1 A', 'DevKitC PCB', None),
         ('Empty cradle for a second ESP32-S3', 'ESP32-S3-DevKitC-1 B', 'printed cradle', None),
         ('CPX status ring (10 NeoPixels) + watchdog', 'Circuit Playground', 'CPX PCB', None),
         ('INMP441 mic behind a pinhole', 'Mic INMP441', 'INMP441', None),
         ('Spine, 4 mm ply: back wall of the chimney', 'Spine', 'spine', None),
         ('Intake slots in the L1 deck', None, None, (0, 120, 116)),
         ('Exhaust vents in the top deck and shell', None, None, (66, 112, 340))])
callout('head-joint', 'Head joint: plinth bearings, under-deck pan gears, turret (plinth and turret see-through)',
        ['Head joint fixed', 'Head pan rotor', 'Top deck', 'Lidar'], [('Head joint fixed', 'plinth', 0.25), ('Head pan rotor', 'turret', 0.3), ('Top deck', None, 0.35)],
        (300, 420, 470), (10, 35, 360),
        [('Plinth (printed), bolted to the top deck', 'Head joint fixed', 'plinth', None),
         ('6805 bearing, upper', 'Head joint fixed', '6805 bearing 25x37x7 upper', None),
         ('6805 bearing, lower', 'Head joint fixed', '6805 bearing 25x37x7 lower', None),
         ('Thrust collar: head weight on the bearing, not the servo', 'Head pan rotor', 'thrust collar', None),
         ('Hollow 25 mm shaft: camera ribbon runs inside', 'Head pan rotor', 'pan shaft', None),
         ('Pan gears 36T:36T (printed), under the deck', 'Head pan rotor', 'pan shaft gear', None),
         ('Pan MG90S in a printed cradle', 'Servo MG90S pan', 'MG90S body', None),
         ('Exposed stem: the lidar scan plane passes here', None, None, (12.5, 35, 390)),
         ('Turret (printed, smoked)', 'Head pan rotor', 'turret', None),
         ('Tilt MG90S inside the turret', 'Servo MG90S tilt', 'MG90S body', None),
         ('6800 bearings carry the tilt hubs', 'Head pan rotor', '6800 bearing 10x19x5 right', None)])
callout('head', 'Head: Camera Module 3 eye + 1.3" TFT face (shell see-through)',
        ['Head pan rotor'], [('Head tilt rotor', 'head shell', 0.25)],
        (230, 560, 560), (0, 35, 470),
        [('Raspberry Pi Camera Module 3', 'Raspberry Pi Camera Module 3', 'CM3 PCB', None),
         ('Eye-ring bezel (printed)', 'Head tilt rotor', 'eye ring bezel', None),
         ('1.3" TFT 240x240, shows the cartoon eyes', 'TFT 1.3in', 'TFT glass module', None),
         ('TFT window, 1 mm clear acrylic', 'Head tilt rotor', 'TFT window', None),
         ('Head frame (printed)', 'Head tilt rotor', 'head frame', None),
         ('Head shell front half (smoked PETG)', 'Head tilt rotor', 'head shell front', None),
         ('Head shell back half', 'Head tilt rotor', 'head shell back', None),
         ('Tilt fork (printed)', 'Head tilt rotor', 'tilt fork', None),
         ('Tilt hub on a 6800 bearing', 'Head tilt rotor', 'tilt hub right', None)])
callout('lidar', 'Lidar backpack pod: LD19 scan plane between plinth and turret',
        ['Lidar', 'Head joint fixed', 'Head pan rotor', 'Top deck', 'Shell', 'Main power'], [('Shell', None, 0.35)],
        (520, -560, 470), (0, -40, 370),
        [('LDROBOT LD19 (scan plane 27 mm above its ears)', 'Lidar LDROBOT LD19', 'LD19 rotating head', None),
         ('Vented pod (printed), bolted to the top deck', 'Lidar backpack pod', 'lidar pod', None),
         ('Scan plane passes under the turret', 'Lidar LDROBOT LD19', 'LD19 window band', None),
         ('Plinth top stays below the beam', 'Head joint fixed', 'plinth', None),
         ('Top half (printed): lifts off after the magnets let go', 'Shell', 'top half right', None),
         ('XT60 loop key = main switch (pull to power off)', 'Main power', 'loop key', None)])
callout('shell-retention', 'Shell retention: drop-in tabs at the bottom, 6x3 magnets at the top',
        ['Shell', 'L1 deck', 'Top deck', 'Corner tie rods'], [('Shell', None, 0.45)],
        (520, 470, 330), (90, 110, 230),
        [('Upper wall (printed smoked PETG, fits a 256 bed)', 'Shell', 'upper wall front', None),
         ('Corner post', 'Shell', 'corner post FR', None),
         ('Magnet pair on the wall lip, block on the top deck', 'Shell', 'magnet 6x3 (panel) wall front', None),
         ('Drop-in tab into a printed clip on the L1 deck', 'Shell', 'panel clip (printed) wall front', None),
         ('Corner magnet onto a block on the tie rod', 'Shell', 'magnet 6x3 (panel) corner FR', None),
         ('Lower skirt: hooks under the plate, magnets at the top', 'Shell', 'lower skirt front', None),
         ('Top half: 3 magnets onto the top deck', 'Shell', 'top half right', None)])


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
        vp.saveAsImageFile(path, w, h)
        sx = sy = 1.0
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
