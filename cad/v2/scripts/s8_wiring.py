# Stage 8: wiring paths. The main harness runs are modelled as pipes along their routes, not
# every wire: 12 V power (red), branch leads, the Pi's 5 V lead, motor and servo leads, the camera
# ribbon from the Pi 5 up through the hollow pan shaft to the head, the lidar cable and USB links.
# Fixed points (mm), not parametric: rerun this stage after moving parts.

RED, BLK, WHT = 'Plastic - Matte (Red)', 'Plastic - Matte (Black)', 'Plastic - Matte (White)'
RUNS = [
    ('main 12 V 16 AWG: battery XT60 to the loop key', 5, RED,
     [(0, 64, 48), (0, 58, 66), (10, 36, 76), (40, 28, 118), (55, -30, 180), (-40, -53, 191), (20, -78, 222), (50, -90, 234)]),
    ('main 12 V 16 AWG: loop key to the PDB', 5, RED,
     [(56, -90, 230), (10, -75, 205), (-40, -53, 191), (-66, -30, 180), (-72, -12, 111), (-86, -20, 140), (-90, -31, 160)]),
    ('12 V XT30: PDB to the motor-driver board', 4, RED,
     [(-89, -5, 132), (-72, -8, 111), (-20, 20, 112), (30, 28, 112), (40, 42, 97), (10, 58, 110), (-17, 57, 118)]),
    ('12 V XT30: PDB to the Pi 5 V buck', 4, RED,
     [(-89, 7, 132), (-72, 2, 111), (-40, 20, 140), (-26, 34, 150)]),
    ('5 V 5 A: buck to the Pi USB-C (through the spine)', 4, RED,
     [(-20, 34, 160), (-30, 38, 161), (-30, 46, 161), (-34, 56, 142), (-36.3, 55, 137)]),
    ('12 V XT30: PDB to the servo buck', 4, RED,
     [(-89, 20, 132), (-72, 6, 111), (40, -10, 120), (72, -10, 111), (86, -22, 150), (85, -30, 190)]),
    ('6 V + PWM: servo buck to the pan servo (tilt lead runs up the shaft)', 3, BLK,
     [(85, -30, 205), (86, -10, 112), (70, -10, 112), (45, 8, 190), (51, 20, 204)]),
    ('camera ribbon 500 mm (Pi 5 DISP0 to Camera Module 3), path', 3, WHT,
     [(7.5, 55, 148), (7.5, 72, 152), (7.5, 73, 200), (2, 73, 220), (0, 46, 220), (0, 28, 222), (0, 20, 226), (0, 20, 312),
      (14, 22, 316), (14, 40, 322), (14, 32, 345), (14, 30, 354)]),
    ('LD19 cable (UART to the Pi GPIO)', 3, BLK,
     [(-50, -58, 272), (-50, -58, 262), (-30, 0, 240), (0, 42, 220), (-15, 66, 208), (-15, 60, 197)]),
    ('ESP32 USB-C to Pi USB-A', 3.5, BLK,
     [(82, 58, 102), (90, 62, 130), (70, 66, 170), (42, 60, 172)]),
    ('logic loom: driver board to the ESP32', 3, BLK,
     [(-10, 58, 118), (5, 60, 112), (18, 58, 108)]),
    ('motor + encoder leads, front', 4, BLK,
     [(-32, 76, 57), (-40, 64, 80), (-45, 60, 84)]),
    ('motor + encoder leads, front right', 4, BLK,
     [(32, 76, 57), (10, 64, 76), (-30, 60, 84)]),
    ('motor + encoder leads, rear (under the cheeks, through the spine notch)', 4, BLK,
     [(-32, -76, 57), (-28, -40, 44), (-26, 30, 44), (-25, 46, 60), (-40, 58, 82)]),
    ('motor + encoder leads, rear right', 4, BLK,
     [(32, -76, 57), (28, -40, 44), (25, 30, 44), (24, 46, 60), (-20, 58, 82)]),
]


def main():
    c = fresh('Wiring harness (paths)')
    n = 0
    for name, d, look, pts in RUNS:
        sk = c.sketches.add(c.xYConstructionPlane)
        sk.name = 'route: ' + name[:40]
        sk.isVisible = False
        lines = OC.create()
        prev = None
        for (x, y, z) in pts:
            p = P(x, y, z)
            if prev is not None:
                ln = sk.sketchCurves.sketchLines.addByTwoPoints(prev, p)
                lines.add(ln)
                prev = ln.endSketchPoint
            else:
                prev = p
        path = c.features.createPath(lines.item(0), True)   # the connected chain of this run's lines
        pi = c.features.pipeFeatures.createInput(path, NEWB)
        pi.sectionSize = V.createByReal(d / 10.0)
        f = c.features.pipeFeatures.add(pi)
        for b in f.bodies:
            b.name = name
            finish(b, 'Copper', look)
        n += 1
    log('wiring runs', n)
    done()
