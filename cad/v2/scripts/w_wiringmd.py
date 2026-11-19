# w_wiringmd.py (offline): writes cad/v2/WIRING.md from review/wiring.json (tables are generated; rerun after
# any route change: w_flex.py -> w_report.py -> w_diagram.py -> this).
# python3 -I w_wiringmd.py <wiring.json> <out.md>
import json, sys

d = json.load(open(sys.argv[1]))
C = d['cables']
L = []
w = L.append
w('# Super bot v2: wiring harness')
w('')
w('Every cable in the v2 robot, modelled in Fusion (doc "Super bot - v2"): component **Wiring harness** (fixed), plus '
  '**Wiring harness (tilt)** inside the head, which tilts with it. 19 Nov 2026, module layout (the custom main board is parked; '
  'see [docs/decisions.md](../../docs/decisions.md)). Generated from [`scripts/w_routes.py`](scripts/w_routes.py) by '
  '[`scripts/w_wiringmd.py`](scripts/w_wiringmd.py); the same data is in [`review/wiring.json`](review/wiring.json) for the BOM thread.')
w('')
w('![Harness block diagram](review/wiring-diagram.svg)')
w('')
w('| Front | Right | Left |')
w('| --- | --- | --- |')
w('| ![front](renders/wiring-front.png) | ![right](renders/wiring-right.png) | ![left](renders/wiring-left.png) |')
w('')
w('| Rear 3/4 | Head and gimbal |')
w('| --- | --- |')
w('| ![rear](renders/wiring-rear-iso.png) | ![head](renders/wiring-head.png) |')
w('')
w('## Model changes made for the wiring (19 Nov 2026)')
w('')
w('- Nov 19, 2026: optional HC-SR04P front sonar dropped to make room for the sled XT60 nose; front covered by lidar + bumpers + cliff sensors; J415 spare (on the parked main board).')
w('- Battery sled: 14 mm nose (`sled_nose`) carrying the blind-mate XT60 male; bulkhead + female moved 14 mm forward. Before, the XT60 cups sat 0.7 mm from the pack.')
w('- Raspberry Pi 5 stand-in fixed to pose B: it was a mirror image of a real Pi 5. Checked against the official Pi 5 mechanical drawing (components to the front wall, USB/Ethernet to the right wall, GPIO + AI HAT+ 2 along the bottom edge, USB-C top-left). PCIe FFC position corrected, fan header added; all Pi cables are routed for this pose.')
w('- Back to off-the-shelf modules (no main board); PDB + INA226 moved to the right cheek, amp + 6 V buck to the left, spare ESP32 cradle lowered, 5 V buck behind the Pi USB-C.')
w('- Spine: wire relief over the battery-tunnel notch (x +-10 to z 108) and two low harness slots (x +-48). Head: one 24 x 9 mm cable slot over the pan shaft through turret top, crossbar, head bottom and head-frame foot. CPX bracket bottom raised 6 mm. Placeholders trimmed so real parts fit: AI HAT+ 2 heatsink 42 x 37 (clears the GPIO housing), Active Cooler box clear of the MIPI connectors.')
w('')
w('## How it is routed')
w('')
w('- **Main feed (16 AWG silicone):** pack -> BMS -> 15 A blade fuse -> sled XT60 male (blind mate, in the sled\'s 14 mm nose) -> bulkhead '
  'XT60 female. From the bulkhead the pair runs up the front power lane 4.6 mm behind the front wall, up the right column, through the right '
  'spine slot and along the right side channel. + goes out through the rear-plate loop slot to the XT60 loop key (pin A) and back from pin B '
  'to the PDB XT60 on the right cheek; - goes straight to the PDB. Charging (jack -> 5 A fuse -> ideal diode -> pack, on the sled) bypasses the key.')
w('- **12 V outputs:** PDB XT30 1 -> DRV8874 perfboard (back through the right spine slot, right column, over the ESP32); XT30 2 -> 5 V buck '
  'on the spine back and XT30 3 -> 6 V servo buck on the left cheek, both through the right upper cheek slot and under the top deck. XT30 4 is spare.')
w('- **Pi 5 (pose B: GPIO along the bottom, USB-C top-left):** 5 V from the D36V50F5 through the spine centre slot into a right-angle USB-C '
  'plug (Pi in 5 A mode, `usb_max_current_enable=1`). ESP32 on the Pi\'s USB 3 port (bought 15 cm USB-A to right-angle USB-C). Everything else '
  'from one 2x20 Dupont housing on the AI HAT+ 2 pass-through header: lidar (UART0 RX), I2S amp + mic (BCLK/LRCLK spliced), TFT (SPI0), CPX power.')
w('- **ESP32-S3 carrier:** the DevKit sits pins-down in its printed cradle on two 1x22 female header rows; wires are soldered to the header tails. '
  'Three exits: the cradle back through the spine slot behind it (rear motor encoders, rear bumpers, side/rear cliff sensors, BNO085, servo '
  'signals), the bottom edge (front motor encoders, front bumpers, front cliff), the right end (INA226, CPX heartbeat, USB).')
w('- **Head:** camera FFC (Pi CAM/DISP0), TFT bundle and mic bundle go up the spine back, through the centre slot, into the bottom of the hollow '
  'pan shaft, up the shaft (tied just below it), past the lying tilt servo, out of the turret top through one 24 x 9 mm slot, across the tilt '
  'joint in a rolling U-loop, and up into the head. TFT and mic are soldered at the head end. The tilt servo lead runs down the same shaft.')
w('- **Bend rule:** >= 4x the conductor OD where static (silicone), >= 10x where a span flexes. Tight spots are listed per cable '
  '(min bend / x OD): mostly the first few mm at a terminal (Dupont exits 4 mm from the front wall, sled solder joints), which is normal with '
  'heatshrink strain relief.')
w('- **Cut length** = routed centreline + 12 mm (strip/crimp/solder at both ends), rounded up to 5 mm. Bought cables give the stock length; '
  'where stock is longer than the route, the slack is stowed as noted.')
w('')
w('## Cable schedule')
w('')
w('| Id | Cable | From | To | Wire | Cut / stock (mm) | End A | End B | Route | Min bend (mm, x OD) |')
w('| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
for c in C:
    awg = sorted({(cd['awg']) for cd in c['conductors'] if cd['awg']})
    wire = ('%d x %s AWG' % (len(c['conductors']), '/'.join(str(a) for a in awg))) if awg else c['kind']
    if c['kind'].startswith('flat'):
        wire = 'FFC ' + c['kind'][5:]
    length = c['cut_mm'] if c['cut_mm'] else (c['note_cut'] if c.get('note_cut') else 'stock %s (route %d)' % (c['stock_len_mm'] or '', c['route_mm']))
    mb = '' if c['min_bend_mm'] is None else '%.1f (%sx)' % (c['min_bend_mm'], c['min_bend_x_od'] if c['min_bend_x_od'] is not None else '-')
    w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (c['id'], c['name'], c['from'], c['to'], wire, length, c['end_a'], c['end_b'],
                                                               (c['route'] or '-').replace('|', '/'), mb))
w('')
w('## Conductors and pins')
w('')
w('| Cable | # | From pin | To pin | AWG | Colour | Signal | Cut (mm) |')
w('| --- | --- | --- | --- | --- | --- | --- | --- |')
for c in C:
    for cd in c['conductors']:
        if not cd['awg']:
            continue
        w('| %s | %s | %s | %s | %s | %s | %s | %s |' % (c['id'], cd['wire'], cd['from'], cd['to'], cd['awg'], cd['colour'], cd['signal'], cd.get('cut_mm') or 'stock'))
w('')
w('Shared pins: Pi pin 2 (5 V) feeds the amp and the CPX, pin 12 (BCLK) and 35 (LRCLK) feed the amp and the mic (solder splices with heatshrink '
  'next to the housing). The I2C buses meet on the ESP32 carrier (one SDA/SCL bus for the cliff sensors, BNO085 and INA226; the VL53L0X '
  'addresses are set at boot with XSHUT1-4). Pin numbers on the ESP32 side are firmware choices (GPIO); assign them in the firmware pin map.')
w('')
w('## Crimps, housings and wire (for the BOM)')
w('')
w('| Part | Qty |')
w('| --- | --- |')
for k, v in d['connector_crimp_tally'].items():
    w('| %s | %s |' % (k, v))
for b in d['bought_cables']:
    w('| %s | %s |' % (b['item'], b['qty']))
w('')
w('| Wire (silicone) | Metres incl. cut allowance |')
w('| --- | --- |')
for k, v in d['wire_totals_m'].items():
    w('| %s | %.2f |' % (k, v))
w('')
w('Add 20 % for mistakes when ordering. The sled-internal leads (S01-S09) are soldered to the pack, BMS, fuse-holder leads and diode module.')
w('')
w('## Moving cables (pan -90..90, tilt -35..45, 15 poses)')
w('')
mv = d['moving_cables']
w('| Tilt span | Rest length | Tilt | Chord | Slack | Gap at the slot | U-loop radius |')
w('| --- | --- | --- | --- | --- | --- | --- |')
for s in mv['tilt_spans']:
    for p in s['per_tilt']:
        w('| %s | %.1f | %d | %.1f | %.1f | %s | %.1f |' % (s['cable'], s['rest_length_mm'], p['tilt'], p['chord_mm'], p['slack_mm'],
                                                        p['gap_at_slot_mm'] if p['gap_at_slot_mm'] < 90 else 'open', p['u_loop_radius_mm']))
w('')
w('Both ends of a tilt span ride with the pan, so the pan angle does not change it. The U-loop radius (3-6 mm) is below the 10x rule for '
  'the 28 AWG bundles (10 mm): use high-flex silicone wire there and tie the loop ends at the slots. The only way to reach 10 mm is a taller '
  'turret-to-crossbar gap (the head about 6 mm higher), which is a looks call left to Adam.')
w('')
w('| Pan span | Twist length | Twist rate (deg/mm at 90 deg) | Offset from the axis | Helix take-up | FFC edge strain |')
w('| --- | --- | --- | --- | --- | --- |')
for s in mv['pan_spans']:
    w('| %s | %.1f | %.2f | %.1f | %.2f mm | %s |' % (s['cable'], s['twist_length_mm'], s['twist_rate_deg_per_mm'], s['offset_from_axis_mm'],
                                                 s['helix_takeup_mm'], '%.3f %%' % s['ffc_edge_strain_pct'] if s['ffc_edge_strain_pct'] is not None else '-'))
w('')
ch = d.get('checks')
w('## Checks')
w('')
if ch:
    w('- Wire bodies checked: %d, against %d solid parts (B-rep intersection, `scripts/w_check.py`).' % (ch['wires'], ch['parts_checked']))
    w('- Wire vs part: %d overlaps over 0.05 mm3, listed below with what they are. None blocks assembly: the pocket and frame ones are two small printed-part tweaks, the rest are wire ends touching the pad, terminal or cradle they end at.' % len(ch['wire_part_hits']))
    w('- Wire vs wire (different cables): %d.' % len(ch['wire_wire_hits']))
    w('- Lidar scan band (z 298-304): only the cables inside the pan shaft (%s), all inside the shaft (r <= 11.5 mm), i.e. inside the '
      'masked knuckle sector. Nothing else crosses the plane.' % ', '.join(b['wire'].split(' | ')[0] for b in ch['scan_band']))
    for h in ch['wire_part_hits']:
        why = ('print a 1.5 x 1.5 mm wire groove in the pocket from the PCB edge to the plate hole (not modelled; the wire body shows the path)'
               if 'pocket' in h['part'] else 'the FFC grazes the head-frame web next to the cable slot: trim the web 1.5 mm there when printing'
               if 'head frame' in h['part'] else 'termination contact')
        w('  - %s / %s: %.2f mm3 (%s)' % (h['wire'], h['part'], h['mm3'], why))
    sw = d.get('sweep')
    if sw is not None:
        w('- Pan/tilt sweep (15 poses, the head wiring moving with the head, vs plinth, frame, shell, lidar): %d hits.' % sw)
w('')
if len(sys.argv) > 3:
    k = json.load(open(sys.argv[3]))
    steps = [r['slide_mm'] for r in k['battery_slide_out']]
    w('- Battery removal: the sled, pack, sled connectors and the sled leads S01-S09 slid out of the back in %d steps up to %d mm: %d new contacts with '
      'any fixed part or other cable (rails and bulkhead stay). The leads pass the spine through the feed relief.' % (len(steps), max(steps), sum(len(r['new_hits']) for r in k['battery_slide_out'])))
    a = k['airflow_sections']
    w('- Airflow (front chimney, spine front face to the front wall, %d mm2): free cross-section %s. The cables in front of the AI HAT+ 2 heatsink (%s) '
      'all run vertically, along the chimney flow.' % (list(a.values())[0]['channel_mm2'], ', '.join('%s mm %.0f %%' % (z[1:], v['free_pct']) for z, v in a.items()),
                                                      ', '.join(x.split(' / ')[-1].split(' | ')[0] for x in k['wiring_in_front_of_hat_heatsink'])))
w('- Tie points: tie each bundle with a 2.5 mm cable tie at every ply slot it passes (a 3 mm hole beside the slot) and every ~60 mm on long runs; '
  'the ties modelled are the shaft-bottom ties of the head cables and the tilt lead.')
w('')
w('## Open items')
w('')
w('- Tilt U-loop radius 3-6 mm is below the 10x-OD rule for the 28 AWG bundles. Meeting it needs a taller turret-to-crossbar gap (head about 6 mm higher), a looks call for Adam.')
w('- Most visible through the smoked front: the 16 AWG 12 V pair (O01) across the top of the ESP32 and the GPIO loom from the Dupont housing. Tidy-up is cosmetic.')
w('- ESP32 GPIO numbers are left to the firmware pin map; the carrier tails are listed by function.')
open(sys.argv[2], 'w').write('\n'.join(L) + '\n')
print('WIRING.md lines', len(L))
