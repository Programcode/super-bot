# Decisions

Key decisions for Super bot. Newest first. Dates are Europe/Budapest. The full log with reasons is on the Grok Bot page (snapshot in [super-bot-page.md](super-bot-page.md)). Append a row whenever something is decided.

## 17-18 Nov 2026: main PCB rev A (KiCad, `hw/main-board/`)

Made overnight by a Claude thread while Adam slept; all are proposals for Adam/Pip to accept or change. Details and open questions in [hw/main-board/README.md](../hw/main-board/README.md).

| Decision | Notes |
| --- | --- |
| Scope: one main power + I/O carrier board, 186 x 70 mm, flat on the spine in the front chimney between the front motors (z 70) and the Pi (z 140) | Replaces the v2 perfboard driver board, the ESP32 cradle, the cheek PDB + INA226 module, the Pololu Pi buck, the servo buck and the MAX98357A breakout. The Pi 5 plugs in with a 40-way ribbon (GPIO) and a short USB-C cable (5 V). Outline and holes are provisional until v2 CAD is final. |
| 4 layers (JLC04161H-7628, 1.6 mm, 1 oz outer) instead of 2 | Solid GND plane under the ESP32 radio, motor drivers and both bucks, a split power plane (VMOT, VBUS, 3.3 V, 5 V, servo) for 15 A-class currents, and room to route a dense board. Costs about EUR 15-20 more than 2 layers for 5 boards. |
| On-board 5 V 6 A and 5.5 V servo bucks (2x TI TPS56637) replace the approved Pololu D36V50F5 / D36V28F6 modules | One part for both rails (one Extended fee), 6 A synchronous, 28 V input. Changes an approved placeholder: Adam to confirm. |
| ESP32-S3-WROOM-1-**N16R2** (16 MB flash, 2 MB quad PSRAM) | Quad PSRAM keeps GPIO35-37 free; all 31 free GPIOs are used. The local JLC snapshot lacks every WROOM-1 variant, so stock was checked live on LCSC (6613 pcs; N8R2 C2913204 is the drop-in backup). |
| 4x DRV8874 on board, PWM mode, current limit 3.1 A per motor (VREF 2.53 V, RIPROPI 1.8k) | IPROPI goes to ESP32 ADC1 for the stall reflex. |
| Hardware motor cut = watchdog + kill loop + CPX, not a button | Consistent with "no e-stop button on the body". A 74LVC1G123 one-shot keeps the drivers awake and the VMOT P-FET on only while the ESP32 toggles WDI (timeout about 47 ms). An open kill loop (NC connector for a future remote kill or button) or the CPX kill line cuts it too. |
| Reverse-polarity P-FET + 15 A blade fuse + XT30 loop for the DC main switch on the board | The v2 CAD also puts a 15 A fuse on the pack; keeping both is harmless. |
| Pi I/O: UART0 to ESP32 UART0 (also its ROM bootloader), Pi GPIO23/24 drive ESP32 EN/BOOT, LD19 on Pi UART2, I2S to amp + mic, Pi I2C1 on a Qwiic port | The Pi can flash the ESP32 with esptool, no USB cable needed. |
| Connectors: JST-PH (SMD) for harnesses, JST-SH (Qwiic order) for the cliff sensors and IMU, JST-XH for motors, XT60 battery, XT30 switch loop | Cliff/IMU on SH to fit the board. |
| Board 186 x 70 mm, all parts on top, 4-layer JLC04161H-7628 | Fills the front chimney from the front motors (z 70) to the Pi's bottom edge (z 140); a notch leaves room for the Pi's USB-C cable. |
| DRV8874s in PH/EN mode (PMODE = GND) instead of PWM mode | Routing: PMODE on two drivers couldn't reach 3.3 V, and GND is the next pin. IN1 = EN (PWM), IN2 = PH (direction); EN low = brake, nSLEEP low = coast. Firmware uses the PH/EN truth table. |
| Rev A: motor C/D nFAULT not wired | Their pins were boxed in during routing. The drivers still self-protect, and the ESP32 still reads their IPROPI current. Route them in rev B. |
| ESP32 XT60 polarity: pad 2 = + | From the LCSC footprint silkscreen. Reverse-polarity FET protects against a mix-up. |

## 17-18 Nov 2026: Super bot v2 layout (Fusion "Super bot - v2", `cad/v2/`)

| Decision | Notes |
| --- | --- |
| First v2 build (300 x 300 x 340 open frame with corner tie rods) scrapped | Adam, 17 Nov: "not at all what I want ... a giant empty 3D printer looking box". Rebuilt to match `docs/concepts/v2-target-photo.png`. Scripts kept in `cad/v2/scripts/old-frame-build/`. |
| Body 200 x 200 x 250 (height = 1.25 x width), rounded smoked PETG shell in 7 printed pieces | Per Adam via Pip: compact and dense, a bit taller than wide, like the photo. Overall 306 x 252 with the wheels; head top at 429 mm. |
| Wheels outside the body at the corners; motors inside | As in the photo. Wheel = 40 % of body height. |
| Battery: 3S4P as a 2 x 3 x 2 cell block on a sled that slides out the back; charge jack on the battery door (pack side of the loop key); blind-mate XT60 | Proposal (Claude). The wheels outside the sides leave no side exit. |
| Boards flat on a vertical spine behind the front wall (driver board + ESP32, Pi 5 stack, CPX, LED bar); side cheeks and a rear plate close the frame; no corner rods | Proposal (Claude), matching the photo's "boards stacked behind the front wall". Front channel is the cooling chimney. |
| LED bar: 8 WS2812B (from a 60/m strip) behind a smoked diffuser slot, driven by the CPX | Pip/Adam asked for the photo's bar. New small part. |
| Short chunky gimbal on a 64 mm square plinth, head 190 x 76 x 64 capsule | Photo match. The head is bigger than the original "much smaller than v1" ask: open for Adam (`head_w` knob). |
| Lidar LD19 in a pod at the rear left, sunk so the scan plane passes under the turret | Head clear of the plane at all pan/tilt. The 30 mm knuckle blocks about 19 deg (mask in software); a taller pod would fix it but changes the look: open for Adam. |
| **v2 accepted as the current design** | Pip, 18 Nov, after the side-by-side with the photo (`cad/v2/review/v2-vs-target-photo.png`), the renders and `cad/v2/README.md`. Result: 0 interferences at rest and across a 15-pose pan/tilt sweep, every part mounted, all 114 printed parts fit a 256 mm bed, 5.04 kg, CoG z 128 mm, head at least 6.3 mm above the lidar plane. Fusion "Super bot - v2" saved; commits 3994b36, 318a829. The module layout (driver perfboard, cradles, PDB, bucks, amp) stays until the main PCB outline is final. |

**Open, waiting on Adam** (don't change until he decides):

| Open decision | Options |
| --- | --- |
| Head width 190 mm (photo match) vs the original "much smaller than v1" brief | Keep 190 x 76 x 64, or shrink with `head_w` / `head_h` / `head_d`. |
| Lidar blind sector of about 19 deg from the gimbal knuckle | Mask it in software (current design), or a taller pod that puts the scan plane above the head (removes it, changes the look). |
| Lidar pod lower than in the photo | Follows from the scan plane having to pass under the turret; changes only together with the decision above. |
| Charge path diode | The charge jack is live with the loop key out (pack side, 5 A fuse). Add a Schottky or ideal-diode module and a recessed jack / shrouded dock contacts. |
| Bumpers | Part of the safety plan but not modelled yet (the walls could float on microswitches). |

## 17 Nov 2026: PCB tool

| Decision | Notes |
| --- | --- |
| PCB tool: KiCad, not Fusion Electronics | Per [hw/fusion-electronics-test/RESULT.md](../hw/fusion-electronics-test/RESULT.md): Fusion's electronics API is read-only, building needs undocumented commands on the active document, and the test crashed the shared Fusion session. Accepted by Pip. |

## 17 Nov 2026: review decisions (apply to v2; v1 stays frozen)

| Decision | Notes |
| --- | --- |
| v1 frozen and backed up | Fusion copy "Super bot - concept K v1 (backup)", git tag `concept-k-v1`. v2 will be a taller, narrower 30×30 cm WALL-E-style torso with stacked levels. |
| Placeholders approved: 2× MG90S pan/tilt, 6805 bearings + 25 mm collar, Pololu D36V50F5 5 V buck | The head and camera must look around independently of the body. |
| Drive: 4× JGB37-520, 12 V, **530 rpm** (19:1), with **100 mm** mecanum wheels | About 2 m/s top speed on hard floors. Speed is a benchmark/fun goal, not for chasing people; the robot mostly drives slowly. Details in `cad/concept-k-v1/review/REVIEW.md`. |
| Motor drivers: DRV8874 class instead of 4× BTS7960 | The BTS7960 heatsinks are overkill. The 530 rpm motor stalls at about 2.3 A, within the DRV8874's 4.4 A limit. |
| Safety plan without an e-stop: software speed and acceleration limits plus bumpers | Enforced as ESP32 reflexes, alongside the cliff sensors, the fuse and the DC switch below. |
| Cliff sensors on all 4 sides | 4× VL53L0X-class ToF, because mecanum drives sideways and backwards. |
| INA226 battery monitor | Voltage and current for the battery time-left model and limp mode. |
| Audio: INMP441 mic + MAX98357A amp + speaker | For wake word, speech-to-text and text-to-speech. |
| HC-SR04 level shifting (or the HC-SR04P) | The ESP32 is 3.3 V only. |
| Start with one ESP32-S3 | A second one can come later if needed. |
| 15 A main fuse after the BMS | |
| DC-rated main switch instead of the KCD1 | Placed where you can reach it. |
| Separate 5–6 V supply for the servos | Keeps servo spikes off the Pi's 5 V rail. |
| Pi 5 set to 5 A (no USB-PD), buck placed next to the Pi | `usb_max_current_enable=1` or `PSU_MAX_CURRENT=5000`. |
| Camera: Raspberry Pi Camera Module 3 replaces the C270 | About €27, 25 × 24 mm. Needs a long Pi 5 (22-pin) camera ribbon through the neck that survives pan/tilt. |
| Pending | Rear HC-SR04 removal, shell material, neck design (all part of the v2 torso work). |

## 17 Nov 2026: concept K v1 design

| Decision | Notes |
| --- | --- |
| No e-stop button on the body | Adam, 17 Nov. Removed from the design. The main rocker switch on the battery door cuts power; ESP32 reflexes and the verbal "stop" stay. |
| Battery: 3S4P 18650 pack with BMS (about 130 Wh) | Adam, 17 Nov. Replaces the unspecified 3S pack. Lies flat in one layer, centred low in the base, on a sled that slides out the rear. About 0.6 kg in total. |
| Concept K v1 layout drafted in Fusion (proposal, for review) | `cad/concept-k-v1/`. Laser-cut smoked acrylic panels plus printed smoked PETG corner fenders, two internal levels, 25 mm aluminium neck tube with pan/tilt. MG90S servos, 6805 bearings and the 5 V buck are placeholders until Adam OKs them. |

## 17 Nov 2026: body, parts, and tooling

| Decision | Notes |
| --- | --- |
| All coding and CAD run through Claude Code on the VPS via T3 Code | Fusion itself runs on Adam's Mac; the VPS reaches its official MCP server through an SSH tunnel (see CLAUDE.md). |
| Private `super-bot` repo as the T3 project, page synced into `docs/` | Pip re-syncs the page snapshot when it changes. |
| No Roomba look | Smooth pucks and toy blobs were rejected. |
| Apple-style dense enclosed shell | Seamless, no visible screws, hidden wiring, tucked wheels, integrated lidar, glowing status ring. The open 3-deck standoff layout was rejected as ugly. |
| Translucent smoked walls | Tinted see-through plastic, not glass, so the internals show. |
| Creature silhouette: head with a face on a neck | Like WALL-E or Vector. Current pick is concept K. |
| More visible "inside tech", like a Chinese EV | Dense sensors, cameras, compute, all connected, so a bigger body still feels full. |
| Built visibly from the real parts | Mecanum wheels, lidar, C270, CPX ring, e-stop, arm should read as a real machine. |
| Size about 40×40×40 cm base, height from the neck | Adam finds 40 cm small, but a bigger body would be empty with current parts. |
| Cheap DIY chassis | Cut 40×40 plywood or aluminium plate. No prebuilt chassis. |
| Drive: 4× JGB37 12 V encoder motors, 80 mm mecanum wheels, 4× BTS7960 | Replaces the earlier 2× TB6612FNG plan. |
| Compute: Adam's own Pi 5 8 GB in the robot, AI HAT+ 2 later | A Pi, not a mini PC. Separate home hardware as a VPS fallback. |
| 2× ESP32-S3 for real-time reflexes | Not owned yet. |
| Sensors: BNO085, HC-SR04 ultrasonics, VL53L0X | |
| Power: 3S 18650 pack | |
| Camera: Logitech C270 | |
| Face: 1.3" TFT | |
| Circuit Playground Express = status ring + backup safety | 10 NeoPixels as the ring, LIS3DH backup tilt, IR dock beacon, backup e-stop if an ESP32 freezes. Cannot drive motors. |
| Lidar later, cheap: LD06 or LD19 (~€30–50) | Expensive lidar rejected. Waits for mapping. |
| Arm and dock later | |
| Custom PCB is v2 | KiCad + JLCPCB, after prototyping with modules. |
| CAD tool: Autodesk Fusion driven by Claude over MCP | Industry-standard tool with live "change this" editing. |

## 16 Nov 2026: brain

| Decision | Notes |
| --- | --- |
| Mind gives behaviors and plans, not single steps | e.g. follow(person, distance), go_to(place), multi-step plans. Supervises every 1–2 s plus events. |
| Layer split: mind / controller (~30 fps) / ESP32 reflexes (~1 kHz, always win) | Under ~100 ms or safety goes to reflexes; judgment to the mind; the rest to the controller. |
| Skills are not limited to safe primitives | Safety from ESP32 reflexes, sim-twin or slow test, score cards, versioned rollback. |
| Qwen bench compared reasoning levels only | Low scored best (10/10). Other models not compared yet. |

## 14–15 Nov 2026: foundations

| Decision | Notes |
| --- | --- |
| Passion project, layered brain is the star | |
| Six-layer roadmap, starting with "Brain on a desk" | |
| Mind: Qwen3.8-27B on Cerebras via OpenRouter, at least low reasoning | |
| Memory keeper: GLM-5.3-Flash every 1–2 min, memory only | |
| Local YOLO at ~30 fps; Qwen gets photos only on events | |
| Audio: openWakeWord, Whisper, Piper, sound classifier | |
| Skip a depth camera | |
| Code firmware in PlatformIO, not the Arduino IDE | |
| Working name "Super bot" | Temporary. |
