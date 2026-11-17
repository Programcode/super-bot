# Decisions

Key decisions for Super bot. Newest first. Dates are Europe/Budapest. The full log with reasons is on the Grok Bot page (snapshot in [super-bot-page.md](super-bot-page.md)). Append a row whenever something is decided.

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
