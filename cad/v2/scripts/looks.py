# looks.py: tune the custom appearances (smoked PETG see-through enough to show the internals).


def _set(a, pid, val):
    p = a.appearanceProperties.itemById(pid)
    if p is None:
        return False
    if isinstance(val, tuple):
        p.value = adsk.core.Color.create(val[0], val[1], val[2], 255)
    else:
        p.value = val
    return True


def tune(dist=30.0, col=(150, 155, 165)):
    a = design.appearances.itemByName('SB Smoked PETG')
    ok = [_set(a, 'transparent_color', col), _set(a, 'transparent_distance', dist), _set(a, 'surface_roughness', 0.08)]
    g = appearance('SB Eye glow cyan', 'LED - SMD 5050 - 20lm (White)')
    _set(g, 'opaque_albedo', (120, 235, 255))
    _set(g, 'opaque_luminance_modifier', (120, 235, 255))
    log('looks', ok, [p.id for p in a.appearanceProperties][:30])


def dark_frame():
    """Black-stained birch ply for the frame, decks and chassis plate (the photo's interior is dark),
    cyan glow for the LED bar dots."""
    ply = appearance('SB Dark grey ply', 'Plastic - Matte (Gray)', color=(70, 72, 78))
    g = appearance('SB NeoPixel glow', 'LED - SMD 5050 - 20lm (White)')
    n = 0
    for o in root.allOccurrences:
        for b in o.bRepBodies:
            if b.material and b.material.name == 'Birch':
                b.appearance = ply
                n += 1
            elif o.component.name.startswith('Circuit Playground') and b.name.startswith(('bar LED', 'CPX NeoPixel')):
                b.appearance = g
                n += 1
    log('dark frame + cyan LEDs', n)
