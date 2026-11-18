# Super bot v2: working plan and checklist

Coordinates: mm, Z up, +Y = robot front, +X = robot right, ground Z = 0.

## Revised layout (17 Nov, after Adam's feedback on the target photo)

Target: `docs/concepts/v2-target-photo.png`. A compact, dense, rounded smoked box a bit taller than wide,
boards stacked flat behind the front wall, big wheels outside the corners, a short chunky gimbal on a
square plinth forward of centre, a rounded lidar pod at the top rear, an LED bar near the top front.

The first build (300 x 300 x 340 open frame with corner tie rods) is scrapped and rebuilt in the same
Fusion document.

### Body
- Body box (shell outside) **200 W x 200 D x 250 H** (`body_h = 1.25 * body_w`), bottom z 28, top `T` = 278.
  Vertical corner radius 16, top edge radius 12, 2.4 mm smoked PETG.
- Shell pieces (all fit the 256 bed): front wall and rear wall (each includes the two vertical corner
  rounds, 200 x 236), two flat side walls (168 x 236, U-slots for the wheel shafts so they lift off),
  two top halves split at x = 0 (100 x 200 x 14, notched round the plinth and the pod), and the battery
  door (bottom centre of the rear wall, carried by the sled). Seam gap 0.4 mm. Magnets at the top edges,
  hooks under the plate edge at the bottom.
- LED bar: 140 x 12 slot near the top of the front wall with a printed black bezel and frosted diffuser,
  8 WS2812B LEDs (133 mm cut from a 60 LED/m strip) driven by the CPX.

### Drive
- 4x JGB37-520 19:1 inside the body at the corners, gearbox faces against printed mounts at x = +/-92.
  Shafts pass through the side walls. 100 mm x 50 mm mecanum wheels **outside** the body:
  inner face 3 mm off the side wall, centres x +/-128, y +/-78. Overall about 306 x 256.
  Wheel = 40 % of the body height, as in the photo.
- Chassis plate 6 mm ply, 194 x 194, z 30..36 (30 mm ground clearance), rectangular.

### Inside, front to back
- Front channel (between the spine at y 52..56 and the front wall at 97.6), seen through the front:
  front motors at the bottom corners; motor-driver board (4x DRV8874) and ESP32-S3 at z 80..125;
  Pi 5 + Active Cooler + AI HAT+ 2 flat against the spine at z 150..206 (ports face +X with ~40 mm
  plug room); CPX on the spine above the Pi; LED bar strip right behind the front wall.
  This channel is the chimney: intake slots low in the front wall, exhaust slots in the top halves.
- Spine (4 mm ply, vertical, full width) from the plate to the top deck. Back face: 5 V buck right behind
  the Pi, BNO085 low near the centre.
- Centre bay: battery block 2 (x) x 3 (z) x 2 (y) cells = 38 x 56 x 134, on a sled, centre x 0, y -28,
  z 38..94, slides out the **back** between the rear motors (encoder gap +/-32). The battery door
  carries the charge jack, so charging works with the loop key out. Blind-mate XT60 at a bulkhead
  in front of the pack. Pan gears, pan servo and the lower pan bearing hang under the top deck here.
- Rear plate (4 mm ply, vertical at y -51..-55, notched for the battery tunnel). Back face: PDB + INA226,
  servo buck, MAX98357A, 40 mm speaker firing through a rear grille. Front face: empty cradle for a
  second ESP32. XT60 loop key on the upper back.
- Top deck 4 mm ply at z 264..268, held by printed brackets on the spine and rear plate. No corner rods.
- 4x VL53L0X cliff sensors under the plate (front, rear, left, right). Optional HC-SR04P holder at the
  front between the front motors, knock-outs in the front wall.

### Top
- Square plinth 64 x 64 x 12 (fixed, black, 4 visible screws) at x 0, y +28, upper 6805 bearing inside;
  lower 6805 in a housing under the top deck; 36T:36T printed pan gears and the pan MG90S under the deck.
- Knuckle (rotating, Ø30, T+12..T+48) on the hollow 25 mm shaft, turret 60 x 50 x 26 (T+48..T+74) with
  the tilt MG90S lying inside, tilt on 2x 6800 bearings, axis T+61, fork arms outside the turret.
- Head: wide capsule 170 x 70 x 62, bottom at T+89. Camera Module 3 at the +X end, TFT face beside it,
  INMP441 mic in the -X end behind a small bezel (the "ear" in the photo).
- Lidar pod: rounded 66 x 60 x 35 at x 0, y -62. The LD19 sits on a shelf inside, ears at T+13, so its
  head pokes out of the pod top like the photo's cap. Scan plane T+40: clear of the head at every pan
  and tilt; only the Ø30 knuckle crosses it (fixed sector, measure and mask in software).

## Checklist

- [x] File bridge + v2lib (doc guard 'Super bot - v2'), auto-save after every stage
- [x] First build (300 frame) done and reviewed by Adam: rejected, scrapped
- [x] Wipe the old components in the v2 document
- [x] s1 drive with outside wheels, s2 battery (rear slide), s3 frame, s4 electronics, s5 shell, s6 gimbal + head, s7 pod, s8 wiring
- [x] Fusion hang (r4) recovered: Fusion force-quit over ssh (approved), reopened, version 10 kept r4's work
- [x] Photo-matched look (side-by-side in review/), dark frame, LED bar, centred Pi
- [x] Checks: 0 interferences (8 groups), 0 hits in the 15-pose pan/tilt sweep, all printed parts fit the bed, mass/CoG, tip-over
- [x] Renders, exploded view, 9 callouts, exports (f3d, STEP, 87 STL, 7 DXF), stale parameters removed
- [x] README, decisions.md
- [ ] Adam's calls: head size vs the original brief, the lidar blind sector / pod height, bumpers


## 18 Nov: Adam's answers (one stage per Fusion job, save + checks after each)

Prepared while the Mac was offline. Job order when Fusion is back (each saves on success, then its quick check):

1. `s4_electronics main()`: remove the module parts the main board replaces (perfboard drivers, ESP32 DevKit, PDB/INA226, Pololu bucks, MAX98357A breakout) and the LED bar; Pi 5 stack above the board; CPX front status light (50.6 mm, 10 NeoPixels, behind the front wall); spare ESP32 cradle; BNO085, speaker, XT30 loop key. Check `front`, `back`.
2. `s4b_mainboard main()`: main board rev A block from its KiCad data (outline + notch, 4x M3 standoffs, connectors at real positions) + hidden keep-outs. Check `front` + `keepouts()`.
3. `s1_drive main()`: plate cable holes for the cliff sensors. Check `drive`.
4. `s2_battery main(('battery',))`: ideal-diode module in the charge path. Check `battery`.
5. `s3_frame main()`: harness slots (spine sides, cheeks, rear plate). Check `frame`.
6. `s5b_shell_edits main()`: remove the LED bar slot, cut the bumper pin U-slots. Check `shell`.
7. `s9_bumpers main()`: front bar + 2 rear half bars, 4x D2F-01L. Check `bumpers`.
8. `s7_lidar set_option(166)`: option B (mast), shot `photo` -> `v2-photo-optB`, sweep + scan plane. Then `set_option(0)`: option A, shot -> `v2-photo-optA`, sweep + scan plane. Check `lidar`.
9. `s8_wiring main()`: harness from every main-board connector to its part.
10. Full checks: `all_quick()`, `floating()`, `keepouts()`, `main(('mass', 'bed', 'sweep'))`.
11. Shots (views, exploded, callouts), exports (f3d, STEP, STL, DXF), side-by-side, README, decisions, commit, pull --rebase, push, Pip.

- [ ] jobs 1-11
