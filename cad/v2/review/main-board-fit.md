# Main board rev A in the v2 bay: fit report

The board geometry comes straight from `hw/main-board/main-board.kicad_pcb` (pcbnew): the outline, the 4 M3 holes and every connector's footprint. `scripts/main_board_parts.json` holds it, and `scripts/s4b_mainboard.py` builds the board block in Fusion from it. Rev B (`hw/main-board/rev-b`, work in progress) has the same outline, holes and power connectors, so this report applies to it too.

## Where it sits

- **Placement:** flat on 4 M3 brass standoffs (6 mm) on the spine's front face, components toward the front wall. KiCad x runs to robot -X, so the battery/power end (KiCad x 50) is on the robot's right, as the board README says. KiCad y runs down.
- **Board extent:** x -93..+93, z 78..148 (bottom edge 42 mm above the plate), back face at y 50, front face at y 51.6.
- **Pi 5 + AI HAT+ 2:** above the board, bottom edge at z 156 (8 mm gap for a right-angle USB-C plug). Its USB-C (x -67) sits over the board's 24 x 8 mm notch (x -55..-79).

## Clearances

| Pair | Clearance | OK? |
| --- | --- | --- |
| Board edge to each side wall | 4.6 mm | yes |
| Board bottom edge to the front motors (top z 75.5) | 2.5 mm | yes |
| Board front face to the motor-mount walls (start y 52) | 0.4 mm (they sit beside the board, not in front of it) | tight, clear |
| Tallest part (F101 fuse holder, 14 mm) to the front wall | 32 mm | yes |
| JST-XH motor plugs + cable bend (22 mm keep-out) to the front wall | 14 mm | yes |
| 40-way IDC + ribbon (18 mm keep-out) to the front wall | 19 mm | yes |
| Board top edge to the Pi's bottom edge | 8 mm | yes (right-angle USB-C) |
| ESP32 antenna (board top edge, x 30..49) | nothing metal above it; the Pi stack is at x <= 7 | yes |
| J103 PI 5V OUT plug (top edge, x -86) to the Pi | clear (Pi starts at x -78) | yes |
| **J101 BAT IN (XT60PW-M) and J102 MAIN SWITCH LOOP (XT30PW-M) plugs** | **4.6 mm to the right side wall; a mated plug plus a 16 AWG bend needs about 35 mm** | **no** |

## The one problem: the two right-angle power connectors

J101 and J102 are right-angle through-hole parts whose plugs mate across the board's KiCad x = 50 edge, which is the robot's right side wall in v2. The bay can't give them 35 mm without making the body about 60 mm wider, which breaks the photo's proportions.

**Board change needed (same outline, same holes):**
- **(a) Recommended:** swap J101 and J102 for the vertical (top-entry) PCB-mount XT60 and XT30 at the same positions, so the plugs mate toward the front wall. There's 46 mm of room; a mated XT60 is about 26 mm plus about 15 mm for the 16 AWG bend, so it fits with about 5 mm to spare (the XT30 is smaller). Only the footprints change; the input-chain copper stays.
- **(b) Alternative:** rotate both connectors to mate across the board's top edge at the right end (robot x 68..93, which is free above the board). This needs the input chain re-laid out.

Until then the CAD shows the right-angle parts as they are on the board, and the connector keep-out check (`checks.keepouts()`) reports the clash.

**Option (a) is modelled too** (Pip passed it to the PCB thread as the preferred fix). These go in the hidden keep-out component, at the board positions below, mating toward the front wall:

| Proposed part (rev B) | KiCad position (mm) | Connector body (EST) | Mated plug | Cable bend (16 AWG, bending up) | Front of the volume |
| --- | --- | --- | --- | --- | --- |
| J101 vertical XT60 | (59, 103.5), long side along KiCad y | 8.2 x 16, 16 mm tall | to 26 mm off the board | +15 mm | y 92.6 (front wall inner face 97.6) |
| J102 vertical XT30 | (57, 60), long side along KiCad x | 10.2 x 5.2, 11.6 mm tall | to 19 mm | +12 mm | y 82.6 |

- **On the board itself (checked from the KiCad footprints):** the vertical XT60 at (59, 103.5) clears the fuse holder F101 by 5.9 mm and the H101 mounting-hole pad by 1.5 mm. At the old origin (63.7, 104.5) it would hit F101. The vertical XT30 clears everything (1.9 mm from the board edge).
- **In the bay:** `checks.keepouts()` reports option (a) separately from rev A (`option_a_hits`). Results are under Check results below.

## Connector use in v2

| Connector | Goes to | Route |
| --- | --- | --- |
| J101 BAT IN (XT60) | battery sled XT60 bulkhead | under the spine notch (board change above) |
| J102 MAIN SWITCH LOOP (XT30) | XT30 loop key on the upper back | right spine slot, right channel, rear plate slot |
| J103 PI 5V OUT (USB-C) | Pi 5 USB-C | short right-angle USB-C cable over the notch |
| J401 PI GPIO (40-way IDC) | AI HAT+ 2 pass-through header | ribbon straight up in front of the stack; a second IDC socket crimped on it taps SPI0 + 3 GPIOs for the head TFT |
| J403 LIDAR | LD19 | left spine slot, left channel, upper cheek slot, deck hole |
| J404 CPX | Circuit Playground Express | up the left side of the bay: +5V/GND to the CPX's JST-PH battery input, RX to A6, KILL from A1 |
| J405-J408 CLIFF 1-4 | 4x VL53L0X | down the front channel, through 8 mm holes in the plate |
| J410 BUMPERS | 4x D2F-01L microswitches | down the front channel; the rear pair through the spine notch along the battery tunnel |
| J411 IMU | BNO085 behind the spine | spine slot |
| J413/J414 PAN/TILT | MG90S servos | spine centre slot; the tilt lead runs up the hollow pan shaft |
| J501 SPEAKER | 40 mm speaker on the rear plate | left slot, left channel, rear plate slot |
| J502 MIC | INMP441 in the head | spine centre slot, up the pan shaft |
| J601-J901 MOTOR A-D | JGB37-520 + encoders | front motors straight up; rear motors under the cheeks and through the spine notch |
| J201 KILL LOOP | shorting plug (motors stay off without it) | on the board |
| J301 ESP32 USB | service only (the Pi flashes the ESP32 over UART0) | free above the board |
| J412 LED BAR | **not used** (no LED bar on v2) | rev B can drop it and its 74HCT125 channel |
| J402/J409 QWIIC PI/ESP, J415 SONAR | spare / optional HC-SR04P | - |

## Check results

RESULTS_PENDING
