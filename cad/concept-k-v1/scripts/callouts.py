# callouts.py: zoomed-in callout views, one per area. Runs ONLY in the backup copy
# (it hides occurrences and changes body opacity; the copy is closed without saving).
# Needs diag.py loaded first (guard, camera, put, P). Uploads <name>.png + <name>.json.
import json, os, tempfile

C = {
    'wheel-corner': dict(
        title='Wheel corner (front right): motor, mount, wheel and driver',
        show=['Drive FR', 'Motor driver BTS7960 FR', 'Chassis plate', 'Shell - corner fender FR'],
        fade=[('Shell - corner fender FR', None, 0.25)],
        cam=((470, 480, 240), (140, 140, 50)),
        items=[('Mecanum wheel, 80 mm, 9 rubber rollers', 'Wheel mecanum 80 FR', 'roller 1', None),
               ('Wheel hub plate', 'Wheel mecanum 80 FR', 'side plate out', None),
               ('Gearbox, 37 mm (sets speed and torque)', 'Motor JGB37-520 FR', 'gearbox', None),
               ('Motor can, 12 V DC motor', 'Motor JGB37-520 FR', 'motor can', None),
               ('Hall encoder (counts wheel turns)', 'Motor JGB37-520 FR', 'encoder', None),
               ('6 mm D-shaft + collar', 'Motor JGB37-520 FR', 'shaft collar', None),
               ('Motor mount + wheel-well liner (printed)', None, None, (159, 112, 76)),
               ('Motor saddle (printed)', 'Motor mount + well liner FR', 'motor saddle', None),
               ('BTS7960 driver (decision: swap to DRV8874)', 'Motor driver BTS7960 FR', 'heatsink', None),
               ('Chassis plate, 6 mm birch ply', None, None, (95, 95, 26)),
               ('Corner fender (printed, smoked)', None, None, (185, 165, 137))]),
    'battery-power': dict(
        title='Battery sled and power parts (seen from the back)',
        show=['Battery 3S4P', 'Battery sled', 'Power placeholders', 'Chassis plate'],
        fade=[],
        cam=((-430, -600, 380), (0, -60, 35)),
        items=[('18650 cells, 3S4P = 12 cells, about 130 Wh', 'Battery 3S4P', 'cell', None),
               ('Nickel strips (connect the cells)', 'Battery 3S4P', 'nickel strip', None),
               ('BMS: battery protection board', 'Battery 3S4P', 'BMS', None),
               ('Battery sled (printed), slides out the back', None, None, (-70, -40, 36)),
               ('Battery door with finger recess', None, None, (-30, -203, 46)),
               ('Sled rails (printed)', 'Battery sled', 'sled rail', None),
               ('Main switch, KCD1 (decision: DC-rated switch)', 'Power placeholders', 'main rocker', None),
               ('XT60 battery plug', 'Power placeholders', 'XT60', None),
               ('5 V buck (decision: move next to the Pi)', 'Power placeholders', 'buck Pololu', None),
               ('Chassis plate', None, None, (-150, 40, 26))]),
    'pi-stack': dict(
        title='Raspberry Pi 5 + Active Cooler + AI HAT+ 2 stack',
        show=['Raspberry Pi 5', 'Raspberry Pi AI HAT', 'Upper deck'],
        fade=[],
        cam=((230, -470, 300), (-55, -150, 100)),
        items=[('Raspberry Pi 5, 8 GB', 'Raspberry Pi 5', 'Pi 5 PCB', None),
               ('Active Cooler (fan + heatsink)', 'Raspberry Pi 5', 'Active Cooler', None),
               ('AI HAT+ 2 board (Hailo-10H)', 'Raspberry Pi AI HAT', 'AI HAT+ 2 PCB', None),
               ('AI HAT+ 2 heatsink', 'Raspberry Pi AI HAT', 'HAT heatsink', None),
               ('16 mm spacers between Pi and HAT', 'Raspberry Pi 5', 'M2.5 spacer 16', None),
               ('6 mm standoffs on the deck', 'Raspberry Pi 5', 'M2.5 standoff 6', None),
               ('USB-A ports (camera, lidar)', 'Raspberry Pi 5', 'USB-A stack', None),
               ('Ethernet', 'Raspberry Pi 5', 'Ethernet RJ45', None),
               ('USB-C power in (from the 5 V buck)', 'Raspberry Pi 5', 'USB-C power', None),
               ('micro-HDMI x2', 'Raspberry Pi 5', 'micro HDMI', None),
               ('GPIO header (40 pins)', 'Raspberry Pi 5', 'GPIO 2x20 header', None),
               ('Upper deck, 3 mm clear acrylic', None, None, (40, -110, 83))]),
    'esp32-imu': dict(
        title='ESP32-S3 boards and BNO085 motion sensor on the upper deck',
        show=['ESP32-S3-DevKitC-1 A', 'ESP32-S3-DevKitC-1 B', 'BNO085', 'Upper deck'],
        fade=[],
        cam=((330, -430, 330), (45, -95, 88)),
        items=[('ESP32-S3 A: motors + reflexes (decision: keep only this one)', 'ESP32-S3-DevKitC-1 A', 'DevKitC PCB', None),
               ('ESP32-S3 B (decision: drop for now)', 'ESP32-S3-DevKitC-1 B', 'DevKitC PCB', None),
               ('WROOM-1 module (the chip + antenna)', 'ESP32-S3-DevKitC-1 A', 'WROOM-1', None),
               ('USB-C ports, facing the rear I/O window', 'ESP32-S3-DevKitC-1 B', 'USB-C', None),
               ('Printed cradle (the board has no holes)', 'ESP32-S3-DevKitC-1 A', 'printed cradle', None),
               ('BNO085 IMU, near the centre of rotation', 'BNO085', 'BNO085 PCB', None),
               ('Cut-out for the pan servo', None, None, (0, 34.6, 83)),
               ('Cable slot to the lower level', None, None, (100, -75, 83)),
               ('Upper deck standoff (M3)', None, None, (80, -174, 70))]),
    'cpx-ring': dict(
        title='Front: CPX status ring, ultrasonic sensor and cliff sensor',
        show=['Circuit Playground', 'HC-SR04 front', 'VL53L0X', 'Upper deck', 'Shell - acrylic panels'],
        fade=[('Shell - acrylic panels', None, 0.15)],
        cam=((300, 560, 200), (0, 180, 80)),
        items=[('Circuit Playground Express (status ring)', 'Circuit Playground', 'CPX PCB', None),
               ('NeoPixel LEDs, 10 in a ring', 'Circuit Playground', 'NeoPixel', None),
               ('CPX buttons', 'Circuit Playground', 'button', None),
               ('CPX bracket (printed), hangs from the deck', 'Circuit Playground', 'CPX mount', None),
               ('HC-SR04 ultrasonic (decision: level-shift the echo)', 'HC-SR04 front', 'transducer', None),
               ('HC-SR04 holder (printed)', 'HC-SR04 front', 'HC-SR04 holder', None),
               ('VL53L0X cliff sensor, looks down (decision: 4 of them)', 'VL53L0X', None, None),
               ('Front panel, 3 mm smoked acrylic', None, None, (-110, 201.5, 115)),
               ('Upper deck', None, None, (-90, 150, 83))]),
    'lidar-backpack': dict(
        title='Lidar backpack on the rear of the top',
        show=['Lidar backpack', 'Lidar LDROBOT', 'Shell - acrylic panels', 'Raspberry Pi 5', 'Raspberry Pi AI HAT'],
        fade=[('Shell - acrylic panels', None, 0.3)],
        cam=((330, -480, 380), (-20, -135, 140)),
        items=[('LD19 lidar: spinning head + optical window', 'Lidar LDROBOT', 'LD19 optical window', None),
               ('LD19 base (motor + electronics)', 'Lidar LDROBOT', 'LD19 base', None),
               ('Backpack (printed, hollow)', None, None, (36, -110, 154)),
               ('Side vents (let the Pi heat out)', None, None, (36, -130, 149)),
               ('Exhaust slots in the top panel', None, None, (-91, -150, 140)),
               ('Top panel, 3 mm smoked acrylic', None, None, (110, -40, 140)),
               ('AI HAT+ 2 heatsink (below)', 'Raspberry Pi AI HAT', 'HAT heatsink', None),
               ('Raspberry Pi 5 (below)', 'Raspberry Pi 5', 'Pi 5 PCB', None)]),
    'neck-base': dict(
        title='Neck base: pan bearings, collar and pan servo (hub shown see-through)',
        show=['Neck', 'Upper deck', 'Shell - acrylic panels'],
        fade=[('Neck', 'pan bearing hub', 0.25), ('Shell - acrylic panels', None, 0.15), ('Upper deck', None, 0.5)],
        cam=((270, 330, 210), (0, 40, 112)),
        items=[('Pan bearing hub (printed)', None, None, (19.5, 40, 128)),
               ('6805 bearing, upper', 'Neck', '6805 bearing 25x37x7 1', None),
               ('6805 bearing, lower', 'Neck', '6805 bearing 25x37x7 2', None),
               ('Clamp collar: carries the neck weight', 'Neck', 'neck thrust collar', None),
               ('Retaining ring (printed)', 'Neck', 'bearing retaining ring', None),
               ('Cable exit slot', None, None, (0, 27.5, 109.5)),
               ('Pan coupler (printed)', 'Neck', 'pan coupler', None),
               ('Pan servo MG90S, hangs in the deck', 'Servo MG90S pan', 'MG90S body', None),
               ('Neck tube, 25 x 1 mm aluminium', None, None, (12.5, 40, 175)),
               ('Top panel', None, None, (70, 70, 140)),
               ('Upper deck', None, None, (70, 0, 83))]),
    'head': dict(
        title='Head and tilt joint (head shell shown see-through)',
        show=['Neck', 'Head'],
        fade=[('Head', 'head shell', 0.22)],
        cam=((300, 560, 760), (0, 45, 652)),
        items=[('Tilt servo MG90S', 'Servo MG90S tilt', 'MG90S body', None),
               ('Tilt yoke (printed)', 'Neck', 'tilt yoke', None),
               ('Head bracket (printed)', 'Neck', 'head tilt bracket', None),
               ('Head shell, front half (printed, smoked)', None, None, (-60, 73, 650)),
               ('Head shell, back half', None, None, (-60, 23, 660)),
               ('Head frame (printed)', 'Head', 'head frame', None),
               ('Logitech C270 (decision: Pi Camera Module 3)', 'Logitech C270', 'C270 body', None),
               ('Eye-ring bezel around the lens', 'Head', 'eye ring bezel', None),
               ('1.3" TFT face screen', 'TFT 1.3in', 'TFT module', None),
               ('Clear window over the screen', 'Head', 'TFT window insert', None),
               ('Foam pad (clamps the camera)', 'Head', 'C270 foam pad', None),
               ('Neck tube', None, None, (12.5, 40, 590))]),
}


def _body(prefix, body):
    for occ in root.allOccurrences:
        if occ.component.name.startswith(prefix):
            bs = [b for b in occ.bRepBodies if body is None or b.name.startswith(body)]
            if bs:
                return max(bs, key=lambda x: x.volume)
    return None


def _fade(prefix, body, op):
    n = 0
    for occ in root.allOccurrences:
        if occ.component.name.startswith(prefix):
            for b in occ.bRepBodies:
                if body is None or b.name.startswith(body):
                    b.opacity = op
                    n += 1
    return n


def shoot(name):
    spec = C[name]
    for occ in root.occurrences:
        occ.isLightBulbOn = any(occ.component.name.startswith(s) for s in spec['show'])
    for pre, body, op in spec['fade']:
        _fade(pre, body, op)
    camera(spec['cam'][0], spec['cam'][1], (0, 0, 1))
    vp = app.activeViewport
    w, h = vp.width, vp.height
    path = os.path.join(tempfile.gettempdir(), 'co-' + name + '.png')
    vp.saveAsImageFile(path, w, h)
    labels = []
    for text, pre, body, pt in spec['items']:
        if pt is not None:
            a = P(*pt)
        else:
            b = _body(pre, body)
            if b is None:
                print('missing', name, text)
                continue
            bb = b.boundingBox
            a = adsk.core.Point3D.create((bb.minPoint.x + bb.maxPoint.x) / 2, (bb.minPoint.y + bb.maxPoint.y) / 2,
                                         (bb.minPoint.z + bb.maxPoint.z) / 2)
        p2 = vp.modelToViewSpace(a)
        labels.append({'text': text, 'x': p2.x, 'y': p2.y})
    put('co-' + name + '.png', open(path, 'rb').read())
    put('co-' + name + '.json', json.dumps({'w': w, 'h': h, 'title': spec['title'], 'labels': labels}).encode())
    os.remove(path)
    for pre, body, op in spec['fade']:
        _fade(pre, body, 1.0)
    print(name, len(labels))


def run_all(names=None):
    explode({})
    for n in (names or list(C)):
        shoot(n)
    for occ in root.occurrences:
        occ.isLightBulbOn = True
