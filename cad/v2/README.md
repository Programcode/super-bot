# Super bot v2

The buildable v2 robot, designed in Autodesk Fusion as **"Super bot - v2"** (Adam's *Default Project*). `super-bot-v2.f3d` is an archive copy, `super-bot-v2.step` the whole robot as an assembly. Every part is built by the scripts in `scripts/`, from user parameters, at real datasheet size.

It follows Adam's target photo (`docs/concepts/v2-target-photo.png`): a compact rounded smoked box a bit taller than wide, boards stacked flat behind the front wall, big mecanum wheels sticking out at the corners, a short chunky gimbal with a wide capsule head and a low lidar pod at the top rear. The front status light is the Circuit Playground Express glowing through the smoked front wall (the photo's LED bar was dropped on 18 Nov).

**State on 19 Nov 2026:** v2 uses off-the-shelf modules, not the custom main board (Adam, 19 Nov). The board design is parked in `hw/main-board/` as a future option. The Fusion model has the module layout, lidar option A, the bumpers, the ideal diode in the charge path and the full wiring harness. Full checks, renders and exports for this state are still to be re-run, so the numbers below marked "17 Nov checks" come from the earlier layout.

![Current model, option A (low lidar pod), 19 Nov](renders/v2-photo-optA.png)

![Target photo next to the model, same viewpoint (17 Nov)](review/v2-vs-target-photo.png)

The views below are the 17 Nov renders. They still show the LED bar, the sonar knock-outs and the earlier module positions, and will be replaced when the render pass runs.

| 3/4 | Front | Side | Rear |
| --- | --- | --- | --- |
| ![iso](renders/v2-iso.png) | ![front](renders/v2-front.png) | ![side](renders/v2-side.png) | ![rear](renders/v2-rear.png) |

| Top | Head close-up | Exploded | Rear 3/4 |
| --- | --- | --- | --- |
| ![top](renders/v2-top.png) | ![head](renders/v2-head.png) | ![exploded](renders/v2-exploded.png) | ![rear 3/4](renders/v2-iso-rear.png) |

Close-up callouts with leader lines, one per area, are in [`review/callouts/`](review/callouts) (17 Nov): wheel corner, battery, front chimney, back and sides, right cheek, gimbal, head, lidar pod, shell retention.

## Headline numbers

Size numbers are set by parameters and haven't changed. Mass, balance and check counts are **from the 17 Nov checks, re-run pending**: since then the LED bar and the sonar spot were removed, the main-board block was tried and taken out again, the bumpers, the ideal diode and the full harness were added, and the PDB and audio modules swapped cheeks.

- **Body box:** 200 W x 200 D x 250 H mm (height = 1.25 x width, as in the photo). Rounded: 14 mm vertical corners, 12 mm top edges.
- **Overall:** 306 x 252 mm on the ground (wheels outside the body), **429 mm** to the top of the head.
- **Wheels:** 100 mm, 40 % of the body height. Track 256 mm, wheelbase 152 mm.
- **Mass (17 Nov checks, re-run pending):** about **5.0 kg** (5038 g). Bought parts use real masses, printed parts Fusion's PETG density (non-shell printed parts at 75 % for infill), ply its density, plus 220 g of wiring (an estimate; the harness is now modelled wire by wire).
- **Centre of gravity (17 Nov checks, re-run pending):** x -1.3, y -1.5, **z 128 mm**.
- **Tip-over (17 Nov checks, re-run pending):** static tip angle **31 deg** forward/back, **45 deg** sideways. On a flat floor it tips forward only above about **5.9 m/s^2 (0.6 g)** of braking; the motors can push about 3.9 m/s^2, so it can't tip itself on the flat, but keep the ESP32 limits (1 m/s^2 indoors) because the head sways long before that.
- **Mounting (17 Nov checks, re-run pending):** every body touched the part that holds it (0 of 369 bodies more than 0.3 mm from everything; the mecanum rollers are bought-wheel internals and not counted). `review/checks-floating.json`.
- **Interference (17 Nov checks, re-run pending):** **0** between parts at rest (8 grouped checks covering all 387 bodies), and **0** between the moving head and everything else at 15 pan/tilt poses (pan -90/-45/0/45/90 x tilt -35/0/45). `review/checks-quick.json`, `review/checks-sweep.json`. The per-stage quick checks after each 18-19 Nov job were all 0 hits (`review/checks-18nov/`, `review/checks-19nov/`), and the option A sweep on 19 Nov was 0 hits.
- **Print bed:** all printed parts fit a 256 x 256 x 256 mm bed (17 Nov, and every printed part added since passed the per-stage bed check). The biggest are the front and rear walls, 200 x 236 x 14 mm.
- **Timeline:** healthy. 101 user parameters on 17 Nov; a few have been added since.

## Layout

Coordinates: mm, Z up, +Y front, +X right, ground at Z 0.

**Drive (corners).** Four JGB37-520 12 V 530 rpm (19:1) motors sit inside the body on printed mounts, gearbox faces 7 mm inside the side walls. The shafts pass through U-slots in the side walls to 100 x 50 mm mecanum wheels outside the body, X configuration (seen from above, the top rollers point at the centre, so it can spin and strafe). Chassis plate: 6 mm birch ply, 194 x 194, 30 mm ground clearance, with a cable hole for each cliff sensor.

**Battery (low, central, removable).** 3S4P 18650 (12 cells, about 130 Wh) packed as a 2 (wide) x 3 (high) x 2 (long) block, 38 x 58 x 134 mm, on a printed sled at the bottom centre. It slides **out of the back** between the rear motors (the wheels outside the sides leave no side gap). The BMS (3S 20 A), the **15 A blade fuse**, the 5 A charge fuse and an ideal-diode module ride on top of the pack. The sled has a 14 mm nose in front of the pack (`sled_nose`) that holds the blind-mate **XT60 male** and gives its 16 AWG leads room to bend; it mates with an XT60 female in a printed bulkhead under the spine. The battery door is a shell piece screwed to the sled and carries the **charge jack** (5.5 x 2.1, 5 A).

**Front chimney (spine front, what you see through the front wall).** A vertical 4 mm ply spine 44 mm behind the front wall carries, bottom to top:

- Low left: a 70 x 40 perfboard with 4x Pololu DRV8874 carriers in female headers, motor terminals along the bottom, an XT30 12 V input and a 10-pin JST-XH logic header (x -80..-10, z 82..122).
- Low right: the ESP32-S3-DevKitC-1 in a printed cradle, USB-C ports toward the right wall (x 17..83).
- Above them: the Raspberry Pi 5 8 GB + Active Cooler + AI HAT+ 2 (`pi_xc` -5, PCB z 140..196), standing flat on the spine with the heatsink fins vertical. The Pi is in **pose B**, checked against the official Pi 5 mechanical drawing: components face the front wall, USB/Ethernet toward the right wall, the GPIO header and the AI HAT+ 2 along the bottom edge, USB-C at the top left. (The stand-in before 19 Nov was a mirror image of a real Pi 5.)
- Top: the Circuit Playground Express on a printed bracket hung from the top deck, its 10 NeoPixels 2.5 mm behind the top of the front wall (centre z 238). It is the front status light and the motor watchdog: its A1 pad drives the DRV8874 nSLEEP lines, so the CPX can cut the motors on its own.

Air comes in through slots above the front motors and leaves through vents in the top deck and the front top half.

**Behind the spine.** The Pololu D36V50F5 5 V 5.5 A buck sits right behind the Pi's USB-C (Pi set to 5 A mode); its lead passes through a spine slot. The BNO085 sits low near the centre. Two ply side cheeks and a rear plate close the frame into a box (no corner rods).

- **Right cheek** (outer face, next to the loop key): the power distribution perfboard (80 x 50, XT60 in at the bottom, 4x XT30 out on top, 12 V bus bar) and the INA226 20 A module. Under it, an empty printed cradle for a second ESP32-S3, lowered to z 90..119 so the PDB plugs have room.
- **Left cheek** (next to the speaker): the MAX98357A amp and the Pololu D36V28F6 6 V servo buck.
- **Rear plate:** 40 mm speaker firing through a rear grille, and the **XT60 loop key** (XT60E-F panel socket in a printed bracket + a male XT60 with a wire loop, the main DC switch) on the upper back.

**Frame cable passages.** Besides the 17 Nov loom slots, the spine has a 20 mm wire relief above the battery-tunnel notch (x +-10, up to z 108), so the sled's fuse-to-XT60 leads pass when the sled slides out, and two 18 x 12 mm low harness slots at x +-48 (z 48..60) for the rear motors, rear bumpers and the left/right/rear cliff sensors.

**Top.** Gimbal forward of centre: a 64 mm square printed plinth (4 visible M3) holding the upper 6805 bearing; the lower 6805, the 1:1 36T printed gear pair and the pan MG90S hang under the top deck. A hollow 25 x 1 mm aluminium shaft carries the knuckle and the turret; the head's weight sits on a thrust collar on the upper bearing, so the servo only turns it. The turret holds the tilt MG90S lying down, with the tilt on two 6800 bearings. The head is a 190 x 76 x 64 smoked capsule: Camera Module 3 behind an eye-ring bezel at one end, the 1.3" TFT face beside it, the INMP441 mic behind an "ear" bezel at the other end. Head cables (camera FFC, TFT and mic bundles) come up the hollow shaft and cross the tilt joint through one 24 x 9 mm slot straight above the pan shaft, cut through the turret top, the fork crossbar, the head bottom and the head-frame foot, with a rolling U-loop in the 10 mm gap between the turret and the crossbar. This replaced the 14 mm ribbon slots at x 14, which the 16 mm camera FFC could not pass.

**Lidar (option A).** LD19 in a rounded vented pod at the rear left, bolted to the top deck. The LD19 sits inside on a shelf so only its cap shows. Its scan plane (z 301) passes between the plinth top (z 290) and the turret bottom (z 312): the head and fork stay at least **6.3 mm** above it at every pan and tilt pose (19 Nov sweep). Option B (a mast that lifted the LD19 above the head, scan plane 467 mm) was modelled on 18 Nov for comparison and has been removed from the model; its render is `renders/v2-photo-optB.png`. `lidar_rise` switches between them (0 = A).

**Bumpers.** A printed front bar between the front wheels on 2 microswitches and two rear half bars, one each side of the battery door, on 1 switch each: 4x Omron D2F-01L lying on the plate. The bar pins pass through open-bottom U-slots in the front and rear walls, so the walls still lift off. They cover what the lidar (301 mm up), the cliff sensors (looking down) and the camera miss: shoes, toys, chair bases, and anything behind when reversing.

**Shell.** 2.4 mm smoked translucent PETG, 7 pieces: front and rear walls (each with both corner rounds), two flat side walls, two top halves (split front/back) and the battery door. 0.4 mm seams. Each wall has two drop-in tabs at the bottom (into printed clips on the plate edge) and two 6 x 3 mm magnet pairs at the top (blocks under the top deck). Each top half has magnets onto the top deck. The front wall has no LED bar slot and no sonar knock-outs any more. **To open:** slide the front top half forward off the plinth and the rear one back off the pod, then lift any wall straight up (the side walls clear the wheel shafts through their U-slots). Pull the loop key before taking off the rear wall.

**Wiring.** The full harness is modelled: component `Wiring harness` (fixed wiring) plus `Wiring harness (tilt)` inside the head. The schedule (every wire, gauge, connector and route) is in [`WIRING.md`](WIRING.md) and [`review/wiring.json`](review/wiring.json). Main points:

- The ESP32 talks to the Pi over USB (a Pi USB 3 port to the ESP32-S3's native USB-C), which also powers and flashes it. That leaves Pi UART0 free for the LD19.
- The Pi GPIO is wired through one 2x20 Dupont housing on the AI HAT+ 2 pass-through header: lidar on UART0, I2S to the amp and mic, the TFT on SPI0, and power for the CPX. The TFT and mic are soldered at the head end (no room for housings behind them).

## Power

Main path (+):

pack -> BMS -> 15 A blade fuse -> sled XT60 male (blind mate) -> bulkhead XT60 female -> loop key socket A -> loop key -> loop key socket B -> PDB XT60 in (+) -> 12 V bus bar. The INA226 module on the PDB measures the main current.

The negative lead runs straight from the bulkhead to the PDB; only + goes through the loop key. The PDB's four XT30 outputs:

1. DRV8874 perfboard (12 V motor supply)
2. Pi 5 V buck (Pololu D36V50F5)
3. Servo 6 V buck (Pololu D36V28F6)
4. Spare

**Charging:** charge jack (battery door) -> 5 A fuse -> ideal-diode module -> pack (the BMS is common-port). The charge path skips the loop key, so the robot charges while switched off, and the ideal diode keeps 12.6 V off the jack and stops back-feeding. Its drop is about 20 mV, so a 12.6 V CC/CV charger still fills the pack (a Schottky's ~0.5 V would stop near 12.1 V). Use a 3S Li-ion 12.6 V 2 A charger. (The 18 Nov draft had jack -> diode -> fuse; the order above is the current one.)

Connector families: XT60 main, XT30 branches, JST-XH (driver logic, balance lead), JST-PH (motor encoders, CPX), JST-ZH (LD19), Dupont 2x20 on the Pi, JR for the servos. The I2C sensors (VL53L0X, BNO085, INA226) are soldered to their header pads: there is no room for STEMMA QT plugs under the plate or behind the spine. Full schedule: [WIRING.md](WIRING.md).

| Load | Standing, awake | Driving indoors (0.5 m/s) |
| --- | --- | --- |
| Pi 5 (vision + controller) | 6 W | 6 W |
| AI HAT+ 2 running YOLO | 3 W | 3 W |
| LD19 lidar | 0.9 W | 0.9 W |
| Camera Module 3 | 0.4 W | 0.4 W |
| ESP32-S3 | 0.4 W | 0.4 W |
| TFT, CPX front light (low brightness), BNO085, 4x VL53L0X, mic, amp idle | 1.2 W | 1.2 W |
| 5 V subtotal / 0.9 buck efficiency | **13.2 W** | **13.2 W** |
| Pan/tilt servos (own 6 V buck) | 0.3 W | 1 W |
| 4x JGB37-520 (about 5 W no-load in total, plus rolling, turns, strafing) | none | about 15 W |
| **From the pack** | **about 13.5 W** | **about 29 W** |

The 1.2 W row is the 17 Nov estimate, which still included the 8-LED bar; without it the real figure is a little lower.

Pack: 12 Ah x 10.8 V = 130 Wh nominal, about 110 Wh usable.

- Standing awake: **about 8 h**.
- Driving continuously at indoor speed: **about 3.8 h**.
- Typical mix (20 % driving): about 16.5 W, **about 6.5 h**.
- Benchmark sprints near 2 m/s draw about 45-55 W while they last.

Peak: four stalled motors (4 x 2.4 A) + Pi at full load (about 2.3 A at 12 V) + both servos stalled (about 0.4 A) = about 12.3 A, under the 15 A fuse and the 20 A BMS.

## Speed

4x JGB37-520 12 V 530 rpm (19:1), 100 mm wheels (314 mm per turn), about 5.0 kg (17 Nov mass, re-run pending).

- No-load catalogue: 2.8 m/s. **Real top speed on a hard floor: about 2.0-2.2 m/s**; strafing about 1.4-1.7 m/s.
- Pushing force at a standstill about 22 N, so about **3.9 m/s^2** starting acceleration, 0 to 2 m/s in about 1.4 s.
- ESP32 limits (reflex layer): 0.5 m/s and 1 m/s^2 indoors; "benchmark mode" only on purpose, in a cleared space.

## Clearances (measured or set by parameters)

Measured on 17 Nov unless noted; the lidar rows were re-measured on 19 Nov with option A. The rest are set by parameters that haven't changed, but re-run the full checks before trusting the tight ones.

| Pair | Clearance |
| --- | --- |
| Head + fork to the lidar scan plane, worst pose (pan any, tilt 45) | 6.3 mm (19 Nov) |
| Plinth top / turret bottom to the scan plane | 11 mm / 11 mm |
| Head bottom to the turret, any tilt | 2.5 mm minimum (head 28 mm above the tilt axis, turret reach 25.5 mm) |
| AI HAT+ 2 heatsink to the front wall | 14.6 mm (fan and chimney air) |
| Pi USB/Ethernet edge to the right wall | about 58 mm (plug room) |
| Battery sled to the rear motors' encoders, each side | 9.9 mm |
| Front gearbox to the shell corner round | about 1.3 mm (tight; set by `wheel_y` and `corner_r`) |
| Wheel inner face to the side wall | 3 mm |
| Pan shaft gear tips to the spine | about 1 mm (tight) |
| Ground clearance: plate / cliff-sensor pockets | 30 mm / 27 mm |
| Shell seams | 0.4 mm |

## Lidar coverage

With option A the scan plane clears the head at every pan and tilt angle. The only things in the plane are the pan shaft and the 30 mm knuckle between the plinth and the turret: from the lidar they block a fixed sector about **19 deg** wide, centred about 33 deg to the right of the robot's forward direction. The bounding-box check reports a conservative 25 deg, and every cable inside the shaft stays within the same shadow (`review/checks-19nov/checks-lidar-optA.json`). Mask it in software. Option B (mast) removed the sector but changed the look; see `review/lidar-occlusion.png` and the two option renders.

## Parts list

**Bought:** see **[`BOM.md`](BOM.md)** (and [`BOM.csv`](BOM.csv)): every item to buy, with quantity, the exact part, a seller that ships to Hungary, a link, and EUR prices with and without 27 % VAT. v2 uses off-the-shelf modules (Adam, 19 Nov): 4x Pololu DRV8874 carriers on perfboard, an ESP32-S3 dev board, a PDB (XT60 in, XT30 outs) with a 20 A INA226 module, Pololu D36V50F5 and D36V28F6 bucks, a MAX98357 amp. The custom main board (`hw/main-board`, rev B) is parked. Other 18 Nov changes are in too: no LED bar (the CPX is the front light), XT60 loop key, 4x Omron D2F-01L bumpers, an ideal-diode module in the charge path, no sonar. Owned: Raspberry Pi 5 8 GB, Circuit Playground Express.

Dropped: the LED bar strip (18 Nov) and the optional HC-SR04P front sonar (19 Nov).

**Printed (PETG, `stl/`):** shell walls x4, top halves x2, battery door (smoked); head shell front/back, plinth, turret, pod (smoked or black); motor mounts + saddles x4, battery sled (with the XT60 nose) + 2 rails, XT60 bulkhead, cliff-sensor pockets x4, ESP32 cradles x2, CPX bracket, speaker bracket, loop-key bracket, bumper front bar + 2 rear half bars + switch brackets, frame brackets x14, cheek pillars x2, pan servo shelf, lower bearing housing, 36T gears x2, knuckle sleeve, tilt hubs x2, tilt fork, head frame, eye-ring/TFT/mic bezels, panel clips x8, magnet blocks x14. Identical parts share a name with a `-2`, `-3` suffix. The `stl/` folder is the 17 Nov export (86 files, still with the LED bar parts and the sonar holder); re-export pending.

**Cut (`dxf/`):** chassis plate (6 mm birch ply), spine, rear plate, 2 side cheeks, top deck (4 mm birch ply, stained dark grey in the renders), TFT window (1 mm clear acrylic). The plate and top deck are about 194 mm, so any hobby laser fits them. The DXFs are from 17 Nov; the plate cable holes and the new spine slots need a re-export.

**Placeholders / estimates (measure on arrival):** JGB37 encoder length, BMS size (the chosen 3S board is 62 x 41 mm, not the modelled 64 x 20), the ideal-diode module (modelled 22 x 16 x 5, chosen one 17 x 11.7 x 10.2), INMP441 hole positions, fuse holder bodies, AI HAT+ 2 heatsink size, the LD19 scan-plane height (27 mm, read off a datasheet figure), wheel mass (300 g used; the Nexus wheel is 400 g). INA226 module 18 x 19.4 mm. Details in `BOM.md`.

## Mass by component

From the 17 Nov checks, re-run pending. Since then the PDB + INA226 moved to the right cheek and the MAX98357A + servo buck to the left (their x signs flip), the spare ESP32 cradle moved down, the CPX bracket bottom was raised 6 mm, the sonar spot was removed, and the bumpers, the ideal diode and the modelled harness were added.

| Component | Mass (g) | Centre of mass x, y, z (mm) |
| --- | --- | --- |
| Shell (printed smoked PETG) | 829 | 1, -0, 170 |
| Battery 3S4P 18650  | 602 | 0, -27, 67 |
| Drive FR | 470 | 106, 76, 52 |
| Drive FL | 470 | -106, 76, 52 |
| Drive RR | 470 | 106, -76, 52 |
| Drive RL | 470 | -106, -76, 52 |
| Head pan rotor | 332 | 1, 22, 365 |
| Frame (4 mm ply) | 326 | 0, -2, 183 |
| Head joint fixed (plinth, pan servo, gears) | 205 | 8, 20, 261 |
| Chassis plate | 116 | 0, 0, 33 |
| Raspberry Pi 5 8GB  | 71 | -4, 57, 168 |
| Battery sled (printed) | 68 | -0, -19, 51 |
| Lidar pod (printed) | 53 | -50, -58, 277 |
| Lidar LDROBOT LD19 | 47 | -50, -58, 290 |
| Raspberry Pi AI HAT | 45 | -21, 73, 172 |
| Audio MAX98357A  | 42 | -43, -80, 206 |
| Power distribution board  | 40 | -87, -6, 150 |
| Main power XT60 loop key | 33 | 50, -100, 240 |
| Circuit Playground Express  | 27 | -1, 83, 238 |
| Motor driver board 4x DRV8874 | 25 | -45, 57, 100 |
| ESP32-S3-DevKitC-1 A | 18 | 49, 50, 102 |
| Power connectors | 16 | 0, 12, 67 |
| Cliff sensors 4x VL53L0X | 15 | 0, 0, 29 |
| ESP32-S3-DevKitC-1 B spare | 8 | 83, -8, 143 |
| Pi 5 V 5.5 A buck (Pololu D36V50F5) | 7 | -26, 33, 154 |
| Front ultrasonic spot (optional HC-SR04P), removed 19 Nov | 7 | -0, 87, 49 |

## Parameters

Change them in Fusion under Modify -> Change Parameters, or edit the stage scripts. Lengths in mm.

This is the 17 Nov dump (`review/params.json`) with the rows changed or added since then edited by hand from the stage scripts. Regenerate it after the next full check run.

| Name | Expression | Value | Meaning |
| --- | --- | --- | --- |
| `body_w` | `200 mm` | 200.00 | Body box width X (shell outside) |
| `body_d` | `200 mm` | 200.00 | Body box depth Y |
| `body_top` | `body_z0 + body_h` | 278.00 | Body box top Z (T) |
| `pwall` | `2.4 mm` | 2.40 | Printed shell wall (6 perimeters at 0.4) |
| `corner_r` | `14 mm` | 14.00 | Vertical corner radius of the body |
| `top_r` | `12 mm` | 12.00 | Radius of the rounded top edges |
| `shell_x` | `body_w / 2` | 100.00 | Body outer half-width |
| `shell_y` | `body_d / 2` | 100.00 | Body outer half-depth |
| `plate_z` | `30 mm` | 30.00 | Ground clearance under the chassis plate |
| `plate_t` | `6 mm` | 6.00 | Chassis plate thickness (6 mm birch ply) |
| `plate_top` | `plate_z + plate_t` | 36.00 | Top of the chassis plate |
| `plate_w` | `body_w - 2 * pwall - 1 mm` | 194.20 | Chassis plate X |
| `plate_d` | `body_d - 2 * pwall - 1 mm` | 194.20 | Chassis plate Y |
| `wheel_d` | `100 mm` | 100.00 | Mecanum wheel OD (SRC) |
| `wheel_w` | `50 mm` | 50.00 | Mecanum wheel width (SRC Studica/Nexus 100 mm) |
| `wheel_y` | `shell_y - pwall - gb_d / 2 - 3 mm` | 76.10 | Wheel centre /Y/ (half wheelbase); motors just inside the front/rear walls |
| `wheel_xc` | `shell_x + wheel_gap + wheel_w / 2` | 128.00 | Wheel centre /X/ (half track) |
| `mount_wall` | `5 mm` | 5.00 | Printed motor mount wall |
| `gb_face` | `shell_x - pwall - 0.5 mm - mount_wall` | 92.10 | Gearbox face /X/ |
| `axle_z` | `wheel_d / 2` | 50.00 | Wheel axle height |
| `shaft_off` | `7 mm` | 7.00 | Output shaft offset from the motor axis (SRC drawing) |
| `motor_z` | `axle_z + shaft_off` | 57.00 | Motor axis height (shaft below the axis) |
| `gb_d` | `37 mm` | 37.00 | JGB37 gearbox diameter (SRC) |
| `gb_len` | `22 mm` | 22.00 | JGB37 gearbox length, 19:1 (SRC) |
| `can_d` | `33 mm` | 33.00 | JGB37 motor can diameter (SRC) |
| `can_len` | `22.7 mm` | 22.70 | JGB37 motor can length (SRC) |
| `cap_len` | `3.5 mm` | 3.50 | JGB37 rear cap (SRC) |
| `enc_len` | `12 mm` | 12.00 | Hall encoder length (EST, measure) |
| `collar_len` | `6 mm` | 6.00 | Gearbox pilot boss (SRC 12 x 6) |
| `shaft_len` | `15.5 mm` | 15.50 | 6 mm D-shaft length (SRC) |
| `cell_d` | `18.6 mm` | 18.60 | 18650 cell diameter |
| `cell_l` | `65.2 mm` | 65.20 | 18650 cell length (flat top, unprotected) |
| `pack_x` | `2 * cell_d + 1 mm` | 38.20 | Pack width X (2 cells) |
| `pack_y` | `2 * cell_l + 4 mm` | 134.40 | Pack length Y (2 cells end to end + nickel) |
| `sled_wall` | `2.4 mm` | 2.40 | Battery sled wall |
| `tof_r` | `80 mm` | 80.00 | Cliff sensor distance from the centre (under the plate) |
| `top_deck_z` | `body_top - 14 mm` | 264.00 | Top deck underside |
| `top_deck_top` | `top_deck_z + ply_t` | 268.00 | Top deck top |
| `spine_y` | `44 mm` | 44.00 | Spine front face Y |
| `pan_y` | `20 mm` | 20.00 | Head pan axis Y (forward of centre; the pan gear clears the spine) |
| `lidar_y` | `-58 mm` | -58.00 | Lidar centre Y (rear) |
| `pan_servo_x` | `36 mm` | 36.00 | Pan servo shaft X (1:1 gear pair, 36 mm centre distance) |
| `pi_xc` | `-5 mm` | -5.00 | Pi 5 PCB centre X (module layout: USB/Ethernet edge faces +X) |
| `pi_z0` | `plate_top + 104 mm` | 140.00 | Pi 5 PCB bottom (GPIO) edge Z, above the driver board and ESP32 (pose B) |
| `pi_so` | `6 mm` | 6.00 | Pi standoffs off the spine |
| `pi_y0` | `spine_y + pi_so` | 50.00 | Pi PCB back face Y |
| `hat_so` | `16 mm` | 16.00 | AI HAT+ 2 spacer height (SRC) |
| `cpx_z` | `top_deck_z - 26 mm` | 238.00 | CPX centre Z (front status light) |
| `cpx_yf` | `shell_y - pwall - 2.5 mm` | 95.10 | CPX NeoPixel tops, 2.5 mm behind the front wall |
| `shaft_od` | `25 mm` | 25.00 | Pan shaft: 25 x 1 mm aluminium tube (fits 6805 bearings) |
| `seam_gap` | `0.4 mm` | 0.40 | Gap between shell pieces |
| `pod_w` | `70 mm` | 70.00 | Lidar pod width X |
| `pod_d` | `64 mm` | 64.00 | Lidar pod depth Y |
| `mag_d` | `6 mm` | 6.00 | Magnet diameter (6 x 3 mm N52 disc) |
| `mag_t` | `3 mm` | 3.00 | Magnet thickness |
| `scan_h` | `27 mm` | 27.00 | LD19 scan plane above its mounting ears (EST from the datasheet figure) |
| `plinth_h` | `12 mm` | 12.00 | Plinth height above the body top |
| `scan_z` | `body_top + plinth_h + knuckle_h / 2 + lidar_rise` | 301.00 | Lidar scan plane Z (option A 301, B 467) |
| `lidar_rise` | `0 mm` | 0.00 | Lidar option: 0 = A (low pod, ~19 deg masked), 166 mm = B (mast) |
| `turret_z` | `body_top + plinth_h + knuckle_h` | 312.00 | Turret bottom Z |
| `tilt_z` | `turret_z + 13 mm` | 325.00 | Tilt axis Z |
| `turret_hw` | `30 mm` | 30.00 | Turret half-width X |
| `turret_hd` | `25 mm` | 25.00 | Turret half-depth Y |
| `head_w` | `190 mm` | 190.00 | Head width (photo match; the original brief asked for smaller) |
| `head_h` | `76 mm` | 76.00 | Head height |
| `head_d` | `64 mm` | 64.00 | Head depth |
| `head_z0` | `tilt_z + 28 mm` | 353.00 | Head bottom Z (clears the turret at any tilt) |
| `head_zc` | `head_z0 + head_h / 2` | 391.00 | Head centre Z |
| `gear_z` | `top_deck_z - 32 mm` | 232.00 | Pan gear pair bottom Z (under the top deck) |
| `shaft_z0` | `gear_z - 4 mm` | 228.00 | Pan shaft bottom Z |
| `cam_x` | `60 mm` | 60.00 | Camera Module 3 centre X |
| `tft_x` | `10 mm` | 10.00 | TFT centre X |
| `body_h` | `1.25 * body_w` | 250.00 | Body box height (1.25 x width, as in the target photo) |
| `body_z0` | `28 mm` | 28.00 | Body box bottom Z |
| `wheel_gap` | `3 mm` | 3.00 | Body side to wheel inner face |
| `pack_z` | `3 * cell_d + 2 mm` | 57.80 | Pack height Z (3 cells) |
| `sled_y0` | `-( shell_y - pwall )` | -97.60 | Sled rear face (the door screws on here) |
| `pack_y0` | `sled_y0 + sled_wall + 0.5 mm` | -94.70 | Pack rear end Y |
| `pack_y1` | `pack_y0 + pack_y` | 39.70 | Pack front end Y |
| `sled_nose` | `14 mm` | 14.00 | Sled nose in front of the pack: room for the XT60 male leads (19 Nov) |
| `sled_y1` | `pack_y1 + sled_wall + 0.3 mm + sled_nose` | 56.40 | Sled front face Y (XT60 male sticks out here) |
| `sled_hw` | `pack_x / 2 + sled_wall + 0.5 mm` | 22.00 | Sled half-width |
| `tun_hw` | `sled_hw + 4.5 mm` | 26.50 | Battery tunnel half-width (notches in the spine and rear plate) |
| `ply_t` | `4 mm` | 4.00 | Frame ply thickness (4 mm birch ply) |
| `rear_y` | `-51 mm` | -51.00 | Rear plate front face Y |
| `cheek_x` | `76 mm` | 76.00 | Side cheek inner face /X/ |
| `in_x` | `shell_x - pwall - 1 mm` | 96.60 | Frame half-width (inside the shell) |
| `notch_z` | `plate_top + 44 mm` | 80.00 | Spine notch top (XT60 + sled front pass under) |
| `rnotch_z` | `body_z0 + 96 mm` | 124.00 | Rear plate notch top (pack + BMS + fuse pass under) |
| `wall_top` | `body_top - top_r - 2 mm` | 264.00 | Seam between the walls and the top halves |
| `wall_seam_y` | `shell_y - corner_r` | 86.00 | Seam between the front/rear walls and the side walls |
| `door_hw` | `tun_hw - 2 mm` | 24.50 | Battery door half-width |
| `door_top` | `body_z0 + 100 mm` | 128.00 | Battery door top |
| `plinth_s` | `64 mm` | 64.00 | Head plinth size (square) |
| `bar_z` | `body_top - 40 mm` | 238.00 | LED bar centre Z (bar dropped 18 Nov; still read by `s5_shell`, whose slot `s5b_shell_edits` removes) |
| `bar_w` | `140 mm` | 140.00 | LED bar slot length (bar dropped 18 Nov; same as `bar_z`) |
| `drv_z` | `plate_top + 46 mm` | 82.00 | Driver perfboard bottom Z (above the front motors) |
| `knuckle_h` | `22 mm` | 22.00 | Knuckle between plinth and turret (the lidar plane passes here) |
| `mic_x` | `-68 mm` | -68.00 | Mic ear centre X |
| `ld_z` | `scan_z - scan_h` | 274.00 | LD19 ear underside Z |
| `pod_top` | `pod_ld_z + scan_h - 8 mm` | 293.00 | Pod rim Z (5 mm under the LD19 window band in option A) |
| `lidar_x` | `-50 mm` | -50.00 | Lidar centre X (rear left, as in the target photo) |
| `top_seam_y` | `( pan_y - plinth_s / 2 + lidar_y + pod_d / 2 ) / 2` | -19.00 | Seam between the front and rear top halves |
| `frame_z1` | `plate_top + 46 mm` | 82.00 | Bottom of the cheeks and rear plate (clear of the motor mounts) |


## Open issues (honest)

1. **Full checks, renders and exports are stale.** Mass, CoG, floating, interference, bed, the views, STL/DXF and the side-by-side are from 17 Nov. Re-run them on the 19 Nov model (see `TASKS.md`).
2. **Custom main board parked.** v2 is built from modules (Adam, 19 Nov). The rev A/B board in `hw/main-board/` and its CAD stage `scripts/s4b_mainboard.py` are kept as a future option and are not part of this model.
3. **Lidar blind sector** of about 19 deg from the pan shaft and knuckle (option A, see above). Masking works; option B removed it but changed the look.
4. **Pod height.** The photo's pod is taller. Here the pod rim must stay under the LD19's window, which must stay under the turret, so the pod is about 15 mm tall plus the LD19 cap.
5. **Footprint.** The body is 200 x 200, but with the wheels outside, the robot needs 306 x 252 on the floor, bigger than the original "about 30 x 30" body idea.
6. **Head flop.** The head's centre of mass is about 66 mm above the tilt axis, so it will nod when the servos are unpowered and sway when braking. A friction washer on the tilt hub, or keeping the tilt servo powered, solves it.
7. **Head cables.** The camera FFC twists inside the hollow shaft for pan (about 80 mm of free twist length for +/-90 deg) and crosses the tilt joint as a U-loop through the 24 x 9 mm slot. It is checked at all 15 pan/tilt poses in the model; test-fit the real 500 mm cable before printing the turret.
8. **Blind-mate XT60.** It needs a firm push (roughly 30-40 N) and good alignment from the sled rails. The 14 mm sled nose now leaves room for the leads. If the mate fights, swap to a short pigtail with slack.
9. **Cliff sensors.** The VL53L0X pockets sit 27 mm above the floor, close to the sensor's minimum range. If readings are noisy, sink them 5 mm more into the plate.
10. **Tight spots:** front gearbox to the corner round about 1.3 mm, pan gear to the spine about 1 mm, servo tab to the turret wall under 1 mm. All are clear in the model; check them on the printed parts.
11. **Gears** are modelled as simplified trapezoid teeth. Print real involute 36T m1 gears from a gear generator.
12. **Thermals** are designed (a vertical chimney, vertical fins, a 14.6 mm gap), not simulated. Log temperatures on the first long run.
13. **Frame stiffness.** The cheeks and rear plate start above the motor mounts and stand on two printed pillars; the spine stands on the plate. Check for wobble with the head on top; add a printed gusset if needed.
14. **Front sensing without the sonar.** The HC-SR04P was dropped for the sled nose. The front is covered by the lidar, the front bumper and the cliff sensors; low, soft obstacles are found by touch.
15. **Renders** are Fusion viewport captures; the smoked PETG renders darker than the real material and the photo.

Settled since 17 Nov: the head stays 190 mm wide (Adam, 18 Nov); the LED bar is gone and the CPX is the front light; bumpers are modelled; the always-live charge jack is fixed by the ideal diode; the wiring is modelled wire by wire instead of as a few paths.

## Files

- `super-bot-v2.f3d`, `super-bot-v2.step`: the design (17 Nov export; re-export pending).
- `stl/`: printed parts. `dxf/`: cut parts (both 17 Nov).
- [`WIRING.md`](WIRING.md): the harness schedule. [`review/wiring.json`](review/wiring.json): the same as data, plus the moving-cable checks.
- `renders/`: viewport images. `v2-photo-optA.png` is the current option A view, `v2-photo-optB.png` the mast option; `v2-photo*.png` are the photo-matching views. `review/`: side-by-side with the photo, callouts, `lidar-occlusion.png`, check results (`checks-a.json` mass/bed/scan plane, `checks-quick.json` interference, `checks-sweep.json` pan/tilt sweep, `checks-floating.json`, `params.json`, all 17 Nov; per-job checks in `checks-18nov/` and `checks-19nov/`). `main-board-fit.md` is the fit report for the parked board.
- `scripts/`: the Fusion API scripts, run through the Fusion MCP. `loader.py` fetches `v2lib.py` plus one stage from the VPS file bridge, runs it, uploads the log and saves the document. Stages: `s1_drive`, `s2_battery`, `s3_frame`, `s4_electronics` (Pi stack, CPX, spare cradle, IMU, speaker), `s4c_modules` (driver perfboard, ESP32, bucks, PDB + INA226, amp, loop key), `s5_shell` + `s5b_shell_edits`, `s6_head`, `s7_lidar` (`set_option`), `s8_wiring` (harness data in `w_routes.py` and `w_lib.py`; `w_dump.py`, `w_check.py`, `w_flex.py` and `w_report.py` dump the geometry, check the wires and moving cables, and write the schedule; `w_look.py` takes quick-look images), `s9_bumpers`; then `looks.py`, `checks.py` (`quick()` per stage, `main()` for mass/bed/sweep), `shots.py`, `export.py`. `s4b_mainboard.py` is parked (main board block; not run for the module layout). `sidebyside.py`, `compose_bg.py` and `callout_annotate.py` run on the VPS.
- **File bridge:** the Fusion scripts fetch `v2lib.py` and the stage files from, and upload logs, images and exports to, a tiny HTTP bridge on the VPS: `python3 -I cad/v2/scripts/bridge_recv.py <upload dir> cad/v2/scripts` (listens on the VPS Tailscale IP, port 8766). `mkrun.py <tag> "<jobs>"` prints a loader body for one job; `fmcp.py job` runs one when the session's Fusion MCP tool is down. `old-frame-build/` holds the scrapped first layout.
