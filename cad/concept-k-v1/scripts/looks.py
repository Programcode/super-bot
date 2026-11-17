# looks.py: tune the custom appearances and (re)apply them by body name.

def _set(a, pid, val):
    p = a.appearanceProperties.itemById(pid)
    if p is None:
        return
    if isinstance(val, tuple):
        p.value = adsk.core.Color.create(val[0], val[1], val[2], 255)
    else:
        p.value = val


def tune_looks():
    a = appearance('SB Smoked acrylic', 'Glass (Grey)')
    _set(a, 'transparent_color', (158, 161, 168))
    _set(a, 'transparent_distance', 10.0)
    p = appearance('SB Smoked PETG v2', 'Glass (Grey)')
    _set(p, 'transparent_color', (140, 143, 150))
    _set(p, 'transparent_distance', 6.0)
    _set(p, 'surface_roughness', 0.18)
    g = appearance('SB Eye glow cyan', 'LED - SMD 5050 - 20lm (White)')
    _set(g, 'opaque_albedo', (120, 235, 255))
    _set(g, 'opaque_luminance_modifier', (120, 235, 255))
    w = appearance('SB Face glow white', 'LED - SMD 5050 - 20lm (White)')
    return a, p, g, w


def apply_by_name(pattern_to_look):
    """pattern_to_look: list of (substring of body or component name, appearance)."""
    n = 0
    for occ in [None] + list(root.allOccurrences):
        comp = root if occ is None else occ.component
        for b in comp.bRepBodies:
            for pat, look in pattern_to_look:
                if pat in b.name or pat in comp.name:
                    b.appearance = look
                    n += 1
                    break
    log('applied looks to', n, 'bodies')
