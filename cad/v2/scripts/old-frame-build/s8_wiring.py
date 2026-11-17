# Stage 8: wiring paths. The main harness runs are modelled as pipes along their routes
# (not every wire): 12 V power in 16 AWG pairs, branch leads, the camera ribbon from the
# Pi 5 up through the hollow pan shaft to the head, and the lidar cable. Fixed points,
# not parametric: rerun this stage after moving parts.

RUNS = [
    # name, diameter mm, appearance, points (mm)
    ('main 12 V 16 AWG: XT60 bulkhead to loop key', 5, 'Plastic - Matte (Red)',
     [(-117, 0, 46), (-124, 0, 60), (-112, 0, 100), (-112, 0, 125), (-112, -125, 135), (-112, -128, 270), (40, -132, 286), (52, -136, 288)]),
    ('main 12 V 16 AWG: loop key to PDB', 5, 'Plastic - Matte (Red)',
     [(68, -136, 284), (80, -126, 270), (-20, -122, 200), (-92, -112, 140), (-92, -100, 128)]),
    ('12 V branch XT30: PDB to motor driver board', 4, 'Plastic - Matte (Red)',
     [(-70, -60, 126), (-100, -20, 126), (-112, 0, 118), (-112, 4, 100), (-70, 40, 64), (-30, 45, 52)]),
    ('12 V branch XT30: PDB to Pi 5 V buck', 4, 'Plastic - Matte (Red)',
     [(-56, -60, 126), (-104, -16, 126), (-112, 6, 110), (-62, 82, 100), (-22, 118, 104), (-22, 118, 128), (-15, 104, 150)]),
    ('12 V branch XT30: PDB to servo buck', 4, 'Plastic - Matte (Red)',
     [(-42, -60, 126), (-50, 0, 180), (-60, 70, 260), (-60, 86, 276)]),
    ('servo 6 V + PWM: buck to pan and tilt servos', 3, 'Plastic - Matte (Black)',
     [(-60, 86, 296), (-20, 70, 302), (20, 50, 300), (40, 35, 300)]),
    ('camera ribbon 500 mm (Pi 5 DISP0 to Camera Module 3), path', 3, 'Plastic - Matte (White)',
     [(64.5, 107, 198), (64.5, 127, 200), (64.5, 127, 255), (10, 124, 296), (0, 100, 307), (0, 60, 307), (0, 35, 304), (0, 35, 330),
      (0, 35, 398), (0, 18, 403), (0, 10, 412), (0, 20, 428), (0, 29, 428)]),
    ('LD19 cable (UART to the Pi GPIO)', 3, 'Plastic - Matte (Black)',
     [(0, -94, 360), (0, -94, 326), (0, -60, 318), (-10, 60, 309), (-6, 100, 307), (20, 122, 270), (40, 118, 250)]),
    ('ESP32 USB-C to Pi USB-A', 3.5, 'Plastic - Matte (Black)',
     [(96, 112, 140), (110, 114, 150), (112, 114, 205), (100, 112, 219)]),
    ('motor + encoder leads to the driver board / ESP32 (front pair)', 4, 'Plastic - Matte (Black)',
     [(-42, 100, 70), (-20, 82, 64), (0, 76, 58)]),
    ('motor + encoder leads (front right)', 4, 'Plastic - Matte (Black)',
     [(42, 100, 70), (20, 82, 64), (0, 76, 58)]),
    ('logic loom: driver board + cliff + IMU to the ESP32', 4, 'Plastic - Matte (Black)',
     [(8, 42, 52), (40, 40, 80), (60, 84, 106), (60, 86, 125), (62, 98, 128)]),
]


def main():
    c = fresh('Wiring harness (paths)')
    sk = c.sketches.add(c.xYConstructionPlane)
    sk.name = 'harness routes'
    sk.isVisible = False
    n = 0
    for name, d, look, pts in RUNS:
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
        # soften the corners so the pipe sweeps cleanly
        path = adsk.fusion.Path.create(lines, adsk.fusion.ChainedCurveOptions.noChainedCurves)
        pi = c.features.pipeFeatures.createInput(path, NEWB)
        pi.sectionSize = V.createByReal(d / 10.0)
        f = c.features.pipeFeatures.add(pi)
        for b in f.bodies:
            b.name = name
            finish(b, 'Copper' if 'ribbon' not in name else 'PET Plastic', look)
        n += 1
    log('wiring runs', n)
    done()
