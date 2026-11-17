# final_shots.py: the README / repo images (explicit perspective cameras).

SHOTS = [
    ('k-v1-front', 'front_k', 1100, 1400, 15),
    ('k-v1-side', 'side_k', 1100, 1400, 15),
    ('k-v1-top', 'top_k', 1200, 1200, 9),
    ('k-v1-iso', 'iso_k', 1200, 1500, 25),
    ('k-v1-rear', 'rear_k', 1400, 1100, 24),
    ('k-v1-head', 'head_k', 1400, 1000, 18),
    ('k-v1-body', 'body_k', 1500, 1000, 26),
]


def main(alt=True):
    tune_looks()
    for name, view, w, h, fov in SHOTS:
        shot(name, view, w=w, h=h, fov=fov)
    if alt:
        p = design.userParameters.itemByName('neck_len')
        old = p.expression
        p.expression = '220 mm'
        shot('k-v1-alt-short-neck', None, w=1200, h=1300, fov=24, eye=(1250, 1600, 750), target=(0, 0, 210), up=(0, 0, 1))
        p.expression = old
    done()
