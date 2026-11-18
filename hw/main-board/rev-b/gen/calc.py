"""IPC-2221 trace width calculations for the README (python3 gen/calc.py)."""
import math

OZ = {'outer 1 oz (35 um)': (0.035, 0.048), 'inner 0.5 oz (15.2 um)': (0.0152, 0.024)}


def width_mm(current, dT=20.0, thick_mm=0.035, k=0.048):
    """IPC-2221: I = k * dT^0.44 * A^0.725, A in mil^2."""
    area_mil2 = (current / (k * dT ** 0.44)) ** (1 / 0.725)
    thick_mil = thick_mm / 0.0254
    return area_mil2 / thick_mil * 0.0254


def current_a(width, dT=20.0, thick_mm=0.035, k=0.048):
    area = (width / 0.0254) * (thick_mm / 0.0254)
    return k * dT ** 0.44 * area ** 0.725


CASES = [
    ('Battery input chain (fuse rating)', 15.0, 'F.Cu + B.Cu pours in parallel, 4.5-8 mm wide each'),
    ('Battery input chain (4 motors stalled + Pi, worst case)', 12.3, 'same pours'),
    ('VBUS shunt -> motor-cut FET', 10.0, 'F.Cu + B.Cu VBUS pour, 7.8 mm channel on both layers'),
    ('VMOT FET -> drivers (4 motors, normal driving)', 4.0, 'F.Cu + B.Cu pour at the FET, then the 14 mm In2 VMOT band'),
    ('One motor output (ITRIP 3.1 A)', 3.1, '1.0 mm F.Cu tracks (0.4 mm neck for 1.1 mm at the 0.65 mm-pitch pin)'),
    ('VBUS feed to both bucks (full load)', 3.8, '1.5 mm B.Cu feed + 0.8 mm F.Cu drop to each VIN + local VIN pour'),
    ('+5 V Pi rail', 6.0, 'In2 5 V plane (18-37 mm wide) + F.Cu pour and 4 vias at the Pi USB-C'),
    ('Servo rail', 2.0, 'In2 servo plane under the buck and the servo headers'),
]


def inner_width(current, dT=20.0):
    return width_mm(current, dT, 0.0152, 0.024)


if __name__ == '__main__':
    print('IPC-2221 external k=0.048, internal k=0.024; dT = temperature rise')
    for name, i, how in CASES:
        w10 = width_mm(i, 10)
        w20 = width_mm(i, 20)
        print('%-60s %5.1f A  outer 1 oz: %5.2f mm (dT 20 C), %5.2f mm (dT 10 C)  -> %s' % (name, i, w20, w10, how))
    print()
    for w in (0.8, 1.0, 1.2):
        print('outer 1 oz %.1f mm carries %.2f A at dT 20 C, %.2f A at dT 30 C' % (w, current_a(w, 20), current_a(w, 30)))
    print('inner 0.5 oz: 14 mm VMOT band carries %.1f A at dT 20 C, %.1f A at dT 30 C (stalls are cut by firmware in 0.5 s)'
          % (current_a(14, 20, 0.0152, 0.024), current_a(14, 30, 0.0152, 0.024)))
    print('inner 0.5 oz: 10 A would need %.0f mm at dT 20 C' % inner_width(10, 20))
    print('inner 0.5 oz: 18 mm 5 V plane carries %.1f A at dT 20 C' % current_a(18, 20, 0.0152, 0.024))
