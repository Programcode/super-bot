# Super bot v2: working plan and checklist

Coordinates: mm, Z up, +Y = robot front, +X = robot right, ground Z = 0.

## Layout (decided while planning)

- Torso shell 300 x 300 (`body_w`, `body_d`), top `T` = 340. Vertical corner radius 30, top edge radius 20.
- Wheels 100 mm mecanum at the corners, axle z 50, `wheel_y` = 100, outer face slightly proud of the shell. Open wheel wells; printed motor mounts double as well liners.
- Chassis plate 6 mm ply at z 30..36 (30 mm ground clearance), corner notches for the wheels.
- Battery 3S4P as a 2 (x) x 3 (y) x 2 (z) block of cells (134 x 59 x 40) on a printed sled, centred low, slides out the **right side** between the wheels; the lower right skirt panel is the battery door. BMS + 15 A blade fuse ride on the sled; XT60 to the robot.
- L0 (plate): sled, 4 motors, DRV8874 driver board (front bay), 4 VL53L0X cliff sensors at the side centres, optional front HC-SR04P holder, charge jack at the rear.
- L1 deck at z 112 over battery and motors: PDB + INA226, servo buck, BNO085 at the centre, MAX98357A, speaker.
- Spine: vertical plate at y ~ 93..96 from L1 to the top deck. Front face (the "front chimney" visible through the front panel): ESP32-S3 + spare slot, Pi 5 + Active Cooler + AI HAT+ 2 standing vertical (fins vertical), CPX ring + mic near the top. Back face: 5 V 5 A buck right behind the Pi, servo buck.
- Chimney: intake through lower skirt slots and wheel wells, up the front channel between spine and front panel, out through vents in the top deck and top panel in front of the head joint.
- Top deck (cut plate) at z ~ 326..330 carries the head joint plinth and the lidar pod. Upper frame on 4 corner tie rods.
- Shell: one rounded solid, shelled 2.4 mm, cut into pieces that fit the 256 bed: top centre (240 x 240), 4 upper walls with a rounded top lip, 4 corner posts, 4 lower skirts. Clips at the bottom edges, 6 x 3 mm magnets at the top.
- Head joint: fixed printed plinth (~Ø86) on the top deck holds 2x 6805 bearings and the 1:1 printed pan gear pair; pan MG90S sits through the top deck beside it. Exposed Ø25 hollow stem, then the rotating turret with the tilt MG90S, tilt on 2x 6800 bearings, fork up to the head. Camera ribbon runs down the hollow stem.
- Lidar: LD19 on a vented pod at the top rear; scan plane passes the exposed stem gap above the plinth and below the turret, so the head is clear at all pan and tilt angles. The stem shades a fixed ~13 deg sector (mask in software); option: taller pod puts the plane above the head.
- Head: small smoked capsule ~104 x 46 x 42 with Camera Module 3 (+X, viewer's left) and the 1.3" TFT (-X).
- Main power: XT60 loop key on the upper back. Charge jack on the rear skirt for a future dock.

## Checklist

- [ ] File bridge + v2lib (doc guard 'Super bot - v2')
- [ ] New Fusion document "Super bot - v2" saved in Default Project
- [ ] s1: parameters, plate, 4 drive corners (JGB37-520 19:1, 100 mm wheels, mounts)
- [ ] s2: battery sled + BMS + fuse, driver board, cliff sensors, ultrasonic spot, charge jack
- [ ] s3: frame (L1 deck, posts, spine, top deck)
- [ ] s4: electronics (PDB, INA226, bucks, ESP32 + spare, BNO085, Pi stack, CPX, audio, loop key)
- [ ] s5: shell pieces, clips, magnets, vents, grille, holes
- [ ] s6: head joint + head
- [ ] s7: lidar pod + LD19
- [ ] wiring paths
- [ ] checks: interference (rest + pan/tilt sweep), clearances, bed fit, mass + CoG
- [ ] shots: front, side, rear, 3/4, top, head, exploded; visual review and fixes
- [ ] callouts with leader lines
- [ ] exports: f3d, STEP, STL, DXF
- [ ] README (params, parts list, clearances, mass/CoG, power, runtime, speed, open issues)
- [ ] decisions.md row, commits + pushes, Pip message
