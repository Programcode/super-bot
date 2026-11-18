# Stage 9: minimal bumpers on 4 microswitches (the main board reads 4 bumper inputs on J410, PH-6).
# Why: the lidar plane is 301 mm up (option A) or 467 mm (option B), the cliff sensors only look
# down, and the camera only looks where the head points. Low obstacles (shoes, toys, chair bases,
# the space between the wheels) and anything behind or beside the robot when it reverses or strafes
# are otherwise unseen. Front: one printed bar between the front wheels on 2 switches. Rear: two
# half bars, one each side of the battery door (the sled still slides out), each on 1 switch plus a
# guide pin. Bars sit from the 30 mm ground clearance up; pins pass through open-bottom U-slots in
# the walls (s5b) to the switch levers inside.
# Switch: Omron D2F-01L, body 12.8 x 5.8 x 6.5 mm (SRC Omron D2F datasheet), hinge lever, lying on
# the chassis plate on a printed bracket.

SW_L, SW_D, SW_H = 12.8, 5.8, 6.5


def switch(c, tag, x, sy):
    """Microswitch lying on the plate at x, lever toward the wall (sy = +1 front, -1 rear)."""
    yb = S(sy, 'shell_y - pwall - 2.9 mm - 3.2 mm - %.1f mm/2' % SW_D)     # body centre Y
    body = B(c, 'D2F-01L microswitch %s' % tag, x, yb, 'plate_top', '%.1f mm' % SW_L, '%.1f mm' % SW_D, '%.1f mm' % SW_H, 'ABS Plastic', BLACK)
    # hinge lever: 3.2 mm out of the body front, its tip face where the bumper pin touches it
    B(c, 'D2F lever %s' % tag, x, S(sy, 'shell_y - pwall - 2.9 mm - 1.6 mm'), 'bump_z0 + 9 mm', '10 mm', '3.2 mm', '0.5 mm', 'Steel', STEEL)
    br = None
    for k in (-1, 1):
        cheek = B(c, 'switch bracket (printed) %s' % tag, '(%s) + %d*(%.1f mm/2 + 1 mm)' % (x, k, SW_L), yb, 'plate_top', '2 mm', '%.1f mm' % (SW_D + 4), '5 mm',
                  'PET Plastic', BLACK)
        if br is None:
            br = cheek
    return body


def bar(c, name, x0, x1, sy, pins, switch_xs):
    """Bar outside the wall from bump_z0, with pins through the wall slots."""
    yo = S(sy, 'shell_y + 1 mm + 3 mm')                    # bar centre Y (1 mm in front of the wall)
    b = B(c, name, '((%s) + (%s))/2' % (x0, x1), yo, 'bump_z0', '(%s) - (%s)' % (x1, x0), '6 mm', '14 mm', 'PET Plastic', 'Plastic - Matte (Black)')
    fillet(c, edges_where(b, lambda e: is_axis_line(e, 'x')), '2.5 mm')
    tools = []
    for px in pins:
        # switch pins reach the lever tip; guide pins only ride in the wall slot
        depth = 'pwall + 3.9 mm' if px in switch_xs else 'pwall + 3 mm'
        tools.append(B(c, 'pin', px, S(sy, '(shell_y + 1 mm) - (%s)/2' % depth), 'bump_z0 + 7 mm', '4 mm', depth, '4 mm'))
    join(c, b, tools, name)
    return b


def main():
    param('bump_z0', 'plate_z', 'Bumper bar bottom Z (= the 30 mm ground clearance)')
    c = fresh('Bumpers (4x D2F-01L microswitch)')
    for x in ('-42 mm', '42 mm'):
        switch(c, 'front %s' % x, x, 1)
        switch(c, 'rear %s' % x, x, -1)
    bar(c, 'front bumper bar (printed)', '-75 mm', '75 mm', 1, ('-42 mm', '42 mm'), ('-42 mm', '42 mm'))
    bar(c, 'rear bumper bar left (printed)', '-92 mm', '-30 mm', -1, ('-78 mm', '-42 mm'), ('-42 mm',))
    bar(c, 'rear bumper bar right (printed)', '30 mm', '92 mm', -1, ('42 mm', '78 mm'), ('42 mm',))
    log('bumpers ok')
    done()
