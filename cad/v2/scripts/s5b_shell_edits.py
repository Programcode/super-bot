# Stage 5b: small edits to the existing shell (rebuilding s5 is slow): remove the LED bar slot (no
# generic LED bar on v2; the CPX is the front status light and shows through the smoked wall), and
# cut open-bottom U-slots for the bumper pins in the front and rear walls, so the walls still lift
# straight off.

BUMP_PINS_FRONT = ('-42 mm', '42 mm')
BUMP_PINS_REAR = ('-78 mm', '-42 mm', '42 mm', '78 mm')


def remove_led_slot():
    c = find_occ('Shell (printed smoked PETG)').component
    gone = 0
    for f in list(c.features.extrudeFeatures):
        if f.name.startswith('LED bar slot'):
            sk = f.profile.parentSketch if hasattr(f.profile, 'parentSketch') else None
            f.deleteMe()
            if sk:
                try:
                    sk.deleteMe()
                except Exception:
                    pass
            gone += 1
    log('LED bar slot features removed', gone)


def remove_sonar_knockouts():
    """19 Nov 2026: the optional HC-SR04P spot is dropped, so its two front-wall knock-outs go too."""
    c = find_occ('Shell (printed smoked PETG)').component
    gone = 0
    for f in list(c.features.extrudeFeatures):
        if f.name.startswith('HC-SR04P knock-out'):
            f.deleteMe()
            gone += 1
    log('HC-SR04P knock-outs removed', gone)


def bumper_slots():
    c = find_occ('Shell (printed smoked PETG)').component
    body = {b.name: b for b in c.bRepBodies}
    for x in BUMP_PINS_FRONT:
        B(c, 'bumper pin U-slot', x, 'shell_y - pwall/2', 'body_z0 - 1 mm', '6 mm', 'pwall + 2 mm', 'bump_z0 + 13 mm - body_z0', op=CUT, bodies=[body['front wall']])
    for x in BUMP_PINS_REAR:
        B(c, 'bumper pin U-slot', x, '-(shell_y - pwall/2)', 'body_z0 - 1 mm', '6 mm', 'pwall + 2 mm', 'bump_z0 + 13 mm - body_z0', op=CUT, bodies=[body['rear wall']])
    log('bumper slots cut', len(BUMP_PINS_FRONT) + len(BUMP_PINS_REAR))


def main(parts=('led', 'slots', 'sonar')):
    param('bump_z0', 'plate_z', 'Bumper bar bottom Z (= the 30 mm ground clearance)')
    if 'led' in parts:
        remove_led_slot()
    if 'slots' in parts:
        bumper_slots()
    if 'sonar' in parts:
        remove_sonar_knockouts()
    done()
