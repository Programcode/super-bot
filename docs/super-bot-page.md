# Super bot: page snapshot

> **Synced from the Grok Bot page "Super bot" on 18 Nov 2026, 12:45 AM (Europe/Budapest)** (canvas id `45200f5a-d70f-476f-988f-23a206c0bfd9`, [open the live page](https://cursor.com/canvas/store-3f866d4b-6e7e-4115-b119-325492ec6c21/45200f5a-d70f-476f-988f-23a206c0bfd9), Adam's account).
> The page itself says "Last updated: 18 Nov 2026, 12:45 AM (Europe/Budapest)".
> Do not hand-edit. Pip regenerates this file whenever the page changes (see [`sync.md`](sync.md)).

Living master page for Super bot, Adam's mecanum-wheel home robot and layered brain. This is a passion project. The page is the single source of truth: every decision goes there and into the decision log.

## Vision

A mecanum-wheel robot with a layered brain that can see, map, talk, fetch, remember, and teach itself new skills. The brain is the interesting part; the body is built in layers around it.

| Metric | Value |
| --- | --- |
| Mind | Qwen3.8-27B, Cerebras via OpenRouter, at least low thinking, text + image |
| Drive | Mecanum, four motors, one per wheel, encoders |
| Pilot decisions | 4 / 4, high and medium, all under 1.1 s |
| Target API cost | Under $1/h (event-driven); ~$4–5/h if it thinks every 2 s (estimates) |

Current layer: 1 (starting). The brain runs on a laptop. A first breadboard has a stepper, a servo, an ultrasonic sensor, an IR receiver and a power module, ready for layer 2.

## Roadmap (build in layers)

Approved 15 Nov 2026. Each layer works and is fun on its own.

| Layer | Name | What you get | Status |
| --- | --- | --- | --- |
| 1 | Brain on a desk | A talking, seeing head on the desk | Current, starting |
| 2 | Brain moves the body | Skills layer is born: look_at, panning camera, reflexes | Next |
| 3 | Wheels | Mecanum go_to by dead-reckoning, plus the slip model | Later |
| 4 | Memory + learning | GLM memory keeper, learn_skill, house-object YOLO | Later |
| 5 | Cut the cord | Brain on a Pi on the robot, batteries, clean wiring | Later |
| 6 | Dream layer | LiDAR and mapping, face, arm, dock | Later, any order |

1. **Brain on a desk ($0):** laptop plus a webcam (a phone as webcam is fine). Local YOLO with live boxes. Qwen gets a still photo only on events or when spoken to. Whisper STT and Piper TTS.
2. **Brain moves the body (UNO + kit):** serial protocol laptop to Arduino. The mind calls a long-running look_at behavior; a servo pans the webcam. Ultrasonic reflex and the 200 ms no-command stop.
3. **Wheels:** mecanum chassis, motors and encoders on an ESP32-S3, driven from the laptop over USB serial / UART. go_to by dead-reckoning at ~30 fps. First ML on driving data: the mecanum slip model. Safety on the S3: e-stop, bump and cliff, speed limits, 200 ms watchdog, measured stopping distance.
4. **Memory + learning:** GLM-5.3-Flash memory keeper every 1–2 minutes. Skill library: learn_skill, demos, retry-and-patch, ML from logs, with sim-twin or slow test, score cards and rollback. House-object YOLO fine-tune in Colab.
5. **Cut the cord:** brain onto a Pi 5 8 GB + AI HAT+ 2 with the Active Cooler, on the robot, on batteries, WiFi to the cloud models. Clean wiring.
6. **Dream layer:** LiDAR and mapping, a face, an arm, a self-docking charger. The CPX can stand in early as status ring, head-pat, bump/pickup and IR dock beacon. Depth camera stays skipped.

## Concept renders

The page lists three early renders from 15 Nov (core bot, with arm, docked). The newer 17 Nov concept renders are in [`concepts/`](concepts/).

## CAD / concept K

v2 finished and accepted 18 Nov 2026, 12:45 AM (Europe/Budapest). v1 stays frozen as a backup.

**Repo, Fusion, and how Claude talks to Pip.** The project lives in the private repo [github.com/Programcode/super-bot](https://github.com/Programcode/super-bot), set up as a T3 project on the VPS. Autodesk Fusion runs on Adam's Mac. The VPS reaches the official Fusion MCP at `127.0.0.1:27182` through the SSH tunnel `fusion-mcp-tunnel.service`. Claude Code can message Pip through a webhook routine, using `scripts/ask-pip.sh`.

**v2 is done and accepted.** The Fusion design is named "Super bot - v2". Pip accepted it at 12:45 AM on 18 Nov 2026 (Europe/Budapest), after the side-by-side with the target photo (`docs/concepts/v2-target-photo.png`), the renders, and [`cad/v2/README.md`](../cad/v2/README.md). Every part is at real datasheet size. Result: 0 interferences at rest and across a 15-pose pan/tilt sweep, every part mounted, all 114 printed parts fit a 256 mm bed. Files are in [`cad/v2/`](../cad/v2/): STEP, f3d, STL, DXF, renders, review checks, and a README. Git commits `3994b36` and `318a829`. The first v2 build, a 300×300×340 mm open frame with corner tie rods, was scrapped on 17 Nov as a giant empty 3D-printer-looking box; those scripts are in `cad/v2/scripts/old-frame-build/`. v1 stays frozen as the `concept-k-v1` backup.

The live page shows two images: the finished model next to the target photo (same viewpoint), and an isometric render. In the repo those are [`cad/v2/review/v2-vs-target-photo.png`](../cad/v2/review/v2-vs-target-photo.png) and [`cad/v2/renders/v2-iso.png`](../cad/v2/renders/v2-iso.png). The smoked PETG renders darker than the real material and the photo.

| Metric | Value |
| --- | --- |
| Body box | 200×200×250 mm, 1.25× taller than wide, rounded smoked PETG |
| Footprint | 306×252 mm (wheels outside the body at the corners) |
| Head top | 429 mm |
| Mass | 5.04 kg, CoG z 128 mm; tips at 31° forward/back, 45° sideways |
| Fit | 0 interferences at rest and at 15 pan/tilt poses; all 114 printed parts fit a 256 mm bed |

### v2 layout

As built in [`cad/v2/`](../cad/v2/). Coordinates in mm, Z up, +Y is the front, ground at Z 0. Built from user parameters at real datasheet size. Full write-up: [`cad/v2/README.md`](../cad/v2/README.md).

| Part | As built |
| --- | --- |
| Body | 200×200×250 mm rounded smoked PETG box (14 mm vertical corners, 12 mm top edges). Height is 1.25× the width, as in the photo. |
| Wheels | 100 mm mecanum wheels (40% of body height) sticking out at the corners, X configuration. Track 256 mm, wheelbase 152 mm. Four JGB37-520 12 V 530 rpm motors sit inside on printed mounts. Chassis plate: 6 mm birch ply, 194×194 mm, 30 mm ground clearance. |
| Battery | 3S4P 18650 pack, about 130 Wh, as a 2×3×2 cell block on a printed sled, low and central. It slides out the back between the rear motors. The battery door is a shell piece screwed to the sled and carries the charge jack (5.5×2.1 mm, 5 A, pack side of the loop key). Blind-mate XT60 at the front of the sled, under the spine. |
| Front chimney | Boards stacked flat behind the front wall on a vertical 4 mm ply spine, bottom to top: the motor-driver board (4× Pololu DRV8874) and the ESP32-S3; the Pi 5 8 GB + Active Cooler + AI HAT+ 2, standing flat with 14.6 mm of air to the front wall; the Circuit Playground Express; and the LED bar. Air comes in through slots above the front motors and leaves through vents in the top deck and the front top half. |
| Behind the spine | The 5 V 5.5 A Pi buck (Pololu D36V50F5) sits right behind the Pi (Pi set to 5 A mode). The BNO085 sits low near the centre. Two ply side cheeks and a rear plate close the frame (no corner rods). Left cheek: power distribution board with the INA226. Right cheek: a spare ESP32-S3 cradle, the MAX98357A amp, and the servo 6 V buck (Pololu D36V28F6). Rear plate: 40 mm speaker and the XT60 loop key (the main DC switch) on the upper back. |
| Shell | 2.4 mm smoked translucent PETG in 7 pieces: front and rear walls, two side walls, two top halves, and the battery door. 0.4 mm seams. Each wall has two drop-in tabs at the bottom and two 6×3 mm magnet pairs at the top. All printed parts fit a 256 mm bed; the biggest are the front and rear walls, 200×236×14 mm. |
| Head | A short chunky gimbal on a 64 mm square plinth, with a hollow 25 mm aluminium shaft, 6805 and 6800 bearings, and MG90S pan/tilt servos. Wide capsule head, 190×76×64 mm: Camera Module 3 behind an eye-ring bezel, a 1.3" TFT face, and the INMP441 mic. The 500 mm Pi 5 camera ribbon runs up the hollow shaft. |
| Lidar | LD19 in a vented pod at the rear left. The scan plane (z 301 mm) passes under the turret; the head stays at least 6.3 mm above it at every pan and tilt pose. The 30 mm gimbal knuckle blocks about 19° of the scan (see open decisions). |
| LED bar | 8 WS2812B LEDs in a 140 mm slot near the top of the front, behind a smoked diffuser, driven by the CPX. Added to match the photo. |

### Runtime and speed

From [`cad/v2/README.md`](../cad/v2/README.md). Pack is 12 Ah × 10.8 V = 130 Wh nominal, about 110 Wh usable. Speed is still a benchmark and fun goal; normal indoor driving stays slow, with ESP32 limits of 0.5 m/s and 1 m/s².

| Load | Estimate |
| --- | --- |
| Standing, awake | About 13.5 W, about 8 h |
| Driving indoors (0.5 m/s) | About 29 W, about 3.8 h continuous |
| Typical mix (20% driving) | About 16.5 W, about 6.5 h |
| Forward, hard floor | About 2.0–2.2 m/s (2.8 m/s no-load); sideways about 1.4–1.7 m/s |
| 0–2 m/s / tip-over | About 1.4 s at 5.0 kg. Static tip 31° forward/back, 45° sideways. On a flat floor it tips only above about 5.9 m/s² of braking; the motors can push about 3.9 m/s², so it cannot tip itself on the flat. Keep the indoor accel limit, because the head sways long before that. |

### Open v2 decisions, waiting on Adam

Logged 18 Nov 2026, 12:45 AM (Europe/Budapest). Do not change these until Adam decides.

| Open item | Detail |
| --- | --- |
| Head width | The head is 190 mm wide (190×76×64 mm), which matches the target photo but is bigger than the earlier "much smaller than v1" brief (that one was 136×56×50 mm). Keep 190 mm, or shrink it with the `head_w` / `head_h` / `head_d` knobs? |
| Lidar blind sector | The gimbal knuckle blocks about 19° of the lidar, centred about 33° to the right of forward. Mask that sector in software (current design), or use a taller pod that puts the scan plane above the head (removes the blind sector, but changes the look)? |
| Lidar pod height | That is why the pod sits lower and smaller than in the photo: the scan plane has to pass under the turret, so the pod rim stays under the LD19 window. This only changes together with the blind-sector decision above. |
| Charge-path diode (recommended) | The charge jack is always live, even with the loop key out, because it sits on the pack side of the switch, behind a 5 A fuse but no diode. The jack and any future dock contacts would carry 12.6 V with the robot off. Add a reverse-blocking Schottky or an ideal-diode module, and use a recessed jack or shrouded dock contacts. |
| Bumpers | Part of the safety plan, but not modelled yet. The walls could float on microswitches. |

Other notes, not waiting on a decision: the head's centre of mass is about 66 mm above the tilt axis, so it will nod when the servos are unpowered and sway when braking (a friction washer, or keeping the tilt servo powered, would help); the camera ribbon needs a test-fit of the real 500 mm cable before the turret is printed; a few clearances are tight (front gearbox to the corner round about 1.3 mm, pan gear to the spine about 1 mm); and an optional HC-SR04P holder and knock-outs are in the model but not fitted.

Close-up callout diagrams for v2 are in [`cad/v2/review/callouts/`](https://github.com/Programcode/super-bot/tree/main/cad/v2/review/callouts): wheel corner, battery, front chimney, back and sides, right cheek, gimbal, head, lidar pod, and shell retention. Review checks live in [`cad/v2/review/`](../cad/v2/review/) (`checks-quick.json`, `checks-sweep.json`, `checks-floating.json`, `checks-a.json`).

- [v2 README and files](https://github.com/Programcode/super-bot/tree/main/cad/v2)
- [v2 callout diagrams](https://github.com/Programcode/super-bot/tree/main/cad/v2/review/callouts)

### Concept K v1 (frozen)

Frozen 17 Nov 2026. Kept as a backup.

**Concept K v1 is done and frozen.** The Fusion design is named "Super bot - concept K blockout v1". It is backed up as the Fusion copy "Super bot - concept K v1 (backup)" and as the git tag `concept-k-v1`. Files are in [`cad/concept-k-v1/`](../cad/concept-k-v1/): STEP, f3d, STL, DXF, images, and a README.

| Metric | Value |
| --- | --- |
| Footprint | 406×406 mm |
| Head top | 699 mm (`neck_len` 480) |
| Mass | About 5.5 kg, centre of gravity 99 mm |
| Fit | No part collisions; all printed parts fit a 256 mm bed |

**Decisions, 17 Nov 2026:**

| Decision | Notes |
| --- | --- |
| No e-stop button | Not on the body. ESP32 reflexes and the verbal "stop" stay. |
| 3S4P 18650 battery, about 130 Wh, on a slide-out sled | Replaces earlier rough 4 h driving / 10 h idle figures. The concept K v1 README estimates about 3 h of continuous driving, about 8 h idle, and about 6 h on a typical mix. |
| MG90S pan/tilt servos are OK | Adam wants the head to look around on its own, independently of the body. |
| Drive: 4× JGB37-520, 12 V, 530 rpm, with 100 mm mecanum wheels | Decided 17 Nov. Speed is a benchmark and fun goal; normal driving is slow, with software speed limits and bumpers for safety. |
| 4× Pololu DRV8874 drivers, replacing 4× BTS7960 | Accepted 17 Nov. The speed check (REVIEW.md section 5, commit `9b6bc6e`) confirms DRV8874 is OK: stall is about 2.3 A per motor. |
| 15 A main fuse | On the main power path. Accepted 17 Nov. |
| DC-rated main switch | Replaces the AC-rated KCD1 switch. Accepted 17 Nov. |
| Separate servo supply | The servos get their own 5–6 V buck. Accepted 17 Nov. |
| Cliff sensors on all 4 sides | Accepted 17 Nov. |
| INA226 battery monitor | Accepted 17 Nov. |
| Mic and speaker | INMP441 + MAX98357A + speaker. Accepted 17 Nov. |
| HC-SR04 level shifting | Accepted 17 Nov. |
| Start with one ESP32-S3 | Instead of two from the start. Later boards can still be added for an arm or a face. Accepted 17 Nov. |
| Pi Camera Module 3, instead of the C270 | Accepted 17 Nov. |
| Pi 5 set to 5 A, buck next to the Pi | `usb_max_current_enable` / 5 A mode, no USB-PD. Logged in [`docs/decisions.md`](decisions.md). |

#### Speed check

From [`cad/concept-k-v1/review/REVIEW.md`](../cad/concept-k-v1/review/REVIEW.md) section 5, commit `9b6bc6e`. Estimates for the 530 rpm motors and 100 mm wheels at about 5.5 kg.

| Figure | Estimate |
| --- | --- |
| Forward, hard floor | About 2.0–2.2 m/s (2.8 m/s no-load) |
| Sideways | About 1.4–1.7 m/s |
| 0–2 m/s | About 1.4 s at 5.5 kg |
| Climb | About 14° |
| Current | Stall about 2.3 A per motor (DRV8874 OK); normal draw 0.3–1 A |
| Stall cutoff | After about 0.5 s, via DRV8874 current sense |

Eight labelled callout diagrams are in [`cad/concept-k-v1/review/callouts/`](https://github.com/Programcode/super-bot/tree/main/cad/concept-k-v1/review/callouts): wheel corner, battery/power, Pi stack, ESP32/IMU, CPX/front sensors, lidar backpack, neck base, and head.

The v1 review items that were still open (shell material, neck length, and the rear HC-SR04) are settled or absorbed in v2: the shell is smoked PETG, the long neck is gone, and an optional HC-SR04P holder is in the v2 model but not fitted.

## PCB / electronics design

Decided 17 Nov 2026. The custom PCB tool is KiCad, not Fusion Electronics. Set up and smoke-tested on the VPS the same evening.

**Fusion Electronics test: PARTLY, leaning NO.** A Claude Opus 5.5 T3 thread tried to build a tiny LED board in Fusion Electronics through the Fusion MCP. Fusion's electronics API (`adsk.electron`) is read-only: it can't add parts, nets, traces or outlines, or create an electronics document. The only way to write is through hidden, undocumented text commands (`Electron.run`, `Electron.runScript`, `Electron.mfgexport`). Those act only on the active document, so an agent would have to take over the Fusion UI. On the first real attempt, creating an empty electronics document switched focus, and Fusion crashed when the v2 thread's screenshot hit it. It also has no JLCPCB CAM job and no headless mode, and every step depends on Adam's Mac.

- [Fusion Electronics test: RESULT.md](https://github.com/Programcode/super-bot/blob/main/hw/fusion-electronics-test/RESULT.md)
- [KiCad setup: docs/kicad-setup.md](kicad-setup.md)
- [KiCad smoke test: hw/kicad-smoketest](../hw/kicad-smoketest/)

**KiCad runs headless on the VPS.** It runs right next to Claude, with no GUI, no shared Fusion session and no need for the Mac to be awake, and it can't crash the Mac. It still renders the schematic, both board sides and 3D views as images, so the AI can check its work. KiCad 10.0.8 is also on Adam's Mac for opening and looking at the files.

| Part of the setup | Details |
| --- | --- |
| KiCad 10.0.8 | From the kicad-10.0 PPA, with the official symbol, footprint and 3D libraries. `kicad-cli` and pcbnew Python both work headless. |
| KiCad MCP server | mixelpixx/KiCAD-MCP-Server 2.9.0 (MIT, the most used and most active KiCad MCP). Registered user-wide for Claude Code on the VPS as `kicad`, so every new T3 thread gets about 250 tools: schematic, placement, routing, autoroute, ERC/DRC, exports and part search. It edits boards headless through pcbnew, unlike Konnect, which needs the KiCad GUI. |
| Autorouter | Freerouting 2.5.0 on Java 25, called by the MCP's `autoroute` tool. |
| JLC parts catalog | A local copy of the in-stock JLCPCB catalog (522k parts) with Basic vs. Extended, stock and price, searchable through the MCP. easyeda2kicad pulls a symbol, footprint and 3D model by LCSC number into a global `LCSC` library. |
| Fab and assembly outputs | KiBot 1.9.1 with its JLCPCB preset: a Gerber + drill zip, a BOM with LCSC numbers, and a CPL. PCBWay takes the same Gerbers. |
| Helpers on the VPS | `kicad-check` (ERC + DRC with schematic parity), `kicad-render` (schematic, front/back and 3D PNGs, STEP), `kicad-jlc` (JLCPCB files). |

### Smoke test

[`hw/kicad-smoketest/`](../hw/kicad-smoketest/), commit `c96ce9b`. Built entirely through the KiCad MCP.

| Metric | Value |
| --- | --- |
| Board | 20×15 mm, header → 1k → red LED |
| ERC errors | 0 |
| DRC violations | 0 (0 unconnected, 0 schematic mismatches) |
| Autoroute | 4.6 s, 5 tracks, 0 vias |

- Parts: R1 1k 0603 (C21190, Basic), D1 red 0603 LED (C2286, Basic), J1 1×2 2.54 mm header (C124375, Extended and through-hole, so hand-solder it).
- Exported: JLCPCB Gerber + drill zip, BOM, CPL, STEP, a schematic PDF, ERC/DRC reports, and 3D top/bottom/iso plus front/back PNG renders.
- Nothing was ordered.

**In progress: the main carrier board.** A T3 thread is designing the custom main carrier board in KiCad (ESP32-S3, 4× DRV8874, INA226, power, e-stop, connectors). Output goes to [`hw/main-board/`](../hw/main-board/). The board outline is provisional until it is fitted to the v2 electronics bay. It's an experiment. Ready-to-order JLCPCB / PCBWay outputs and full ERC/DRC checks are still to come. The thread must message Pip through the webhook when it's done.

## Brain architecture

**Mind gives behaviors and plans, not single steps** (decided 16 Nov). No stop-and-wait control. Qwen calls long-running behaviors with parameters (follow(person, distance), go_to(place), look_for(object)) and can send a multi-step plan in one call. A local executor runs the active behavior every frame. Reflexes always win.

**Layer split (16 Nov):** under ~100 ms or safety goes to reflexes; judgment goes to the mind; everything in between goes to the controller.

| Layer | Rate | Does |
| --- | --- | --- |
| Mind | Check-ins every 1–2 s while a behavior runs, plus events | Understand commands, pick and chain behaviors, multi-step plans, scene judgment, surprises, talking, clarifying or refusing, deciding what to remember and when to write a skill |
| Controller | ~30 fps, laptop now, Pi later | Run behaviors, YOLO tracking, obstacle steering, mecanum mixing, smooth accel, later mapping and path planning. No cloud round-trip. |
| Reflexes (ESP32) | ~1 kHz, always win | 200 ms no-command stop, too-close braking, cliff, pickup/tilt motor cut, e-stop + "stop" wake word, stall/overcurrent, speed and accel limits, low-battery limp mode, encoder speed control |

Other parts of the brain:

- **Perception and classic ML:** local YOLO with tracking every frame, wake word, speech in/out, classic models.
- **Cheap classifier:** Luna Decisions or Jev for fast "what is this / which skill" calls.
- **Behaviors, plans, skill library:** follow, go_to, look_for, look_at, stop, ask_help, plus self-written skills.
- **Mind:** Qwen3.8-27B on Cerebras via OpenRouter, text and image, at least low reasoning, never in the inner loop.
- **Memory keeper:** GLM-5.3-Flash every ~1–2 min. Writes memory only; never sends motor commands.
- **Learning:** learn_skill, Adam's demos, retry and patch, ML from logged data.
- **Offline fallback:** a small local Qwen when WiFi dies.

Kept from the old 14 Nov plan: the skills layer, message timestamps with time-to-live, the 200 ms no-command stop, reflexes always winning, switching layers off to measure their value. Dropped: gpt-oss, Waveshare UGV Rover, Jetson Orin Nano, and the "skills may only call safe primitives" rule.

**Thinking schedule:** the inner loop never waits on the mind. Check-in every 1–2 s during a behavior plus events (target lost, obstacle or door, new voice command, behavior done or failed); every 30–60 s or sleep when idle. Thinking every 2 s nonstop is ~1,800 calls/h, roughly $4–5/h.

## Skills and learning

Skills are not limited to safe primitives: they can be complex code with direct motor, servo and sensor control, their own ML models, calls to the mind, and nested skills. Safety comes from three rails:

1. ESP32 reflexes, always on, no skill can override them.
2. Sim-twin or slow test mode before a new or patched skill is trusted.
3. Score card and version history, with rollback.

Four ways it learns: self-writing (learn_skill), demos from Adam, retry and patch, ML from logged data.

## Brain refinement plan

Current lean (not locked): a thin custom loop for the real-time mind, and a coding-agent harness (Pi, Oh My Pi / omp, fx/libfx) for skill-writing and memory agents.

1. Write the layer contracts first (message formats, rates, override rules).
2. Design the event list (what wakes the mind, what never should).
3. Grow the benchmark into a test suite.
4. Sim-twin testing.
5. Red-teaming.
6. Log everything.
7. Compare mind setups head to head.

## Fable brain-plan prompt

The page holds a verbatim prompt Adam pasted into Claude Fable 5.2 for a full brain plan (source file on the Grok Bot box: `/home/box/pip/fable-brain-prompt.md`). It asks Fable to question first, critique the architecture, define interfaces, the event system, skill library, memory design, learning, harness choice, model choices, testing strategy, and a build order starting at $0. Fable's answer is pending review by Pip.

## Perception and ML

- **Vision (decided):** YOLO v8 or v11 locally at ~30 fps; the controller uses tracks every frame; the mind gets a still photo only on events or check-ins. House-object fine-tune in layer 4. Optional later: YOLO-World / Grounding DINO, face recognition, Depth Anything.
- **Audio (planned):** openWakeWord (also the verbal "stop" e-stop), Whisper STT, Piper TTS, sound-event classifier.
- **Classic ML (all planned):** mecanum slip / motion model, floor-type classifier, RL for docking and doorways, sound-event classifier, motor anomaly detection, habit prediction, battery time-left model, arm grasping policy (later).

## Models

| Model | Role | Where | Status |
| --- | --- | --- | --- |
| Qwen3.8-27B | Mind, text + image | Cerebras via OpenRouter (~800 tok/s, 0.26 s TTFT, $0.99 / $1.49 per M) | Current pick |
| GLM-5.3-Flash | Memory keeper and skill writer | Host not pinned | Current pick |
| Luna Decisions / Jev | Cheap classifier | OpenRouter | Planned, not chosen |
| Small local Qwen | Offline mind | Laptop, later Pi | Planned fallback |
| DeepSeek V4.1 Flash | Rare hard planning, maybe | — | Thinking off only |
| gpt-oss-20b / 120b | Old candidate | Groq / Cerebras | Dropped |

Use at least low reasoning (agentic score 22.4 none vs 38.9 low). Set reasoning effort explicitly on Cerebras.

## Qwen benchmark

Reasoning-effort test of one model (qwen/qwen3.8-27b on Cerebras), not a bake-off. 10 mission-style scenarios, 15 Nov 2026.

| Effort | Pass | Right move after a failure | Median time | Cost per decision |
| --- | --- | --- | --- | --- |
| none | 7 / 10 | 4 / 6 | 0.53 s | ~$0.002 |
| low | **10 / 10** | **6 / 6** | 0.55 s | ~$0.002 |
| medium | 8 / 10 | 4 / 6 | 0.49 s | ~$0.002 |
| high | 9 / 10 | 6 / 6 | 0.54 s | ~$0.002 |

Low is the current default. Total spend ~$0.19. Bench files were in `/workspace/qwen-bench/` on the Grok Bot box.

## Hardware

Kit and early to-buy list as of 15 Nov 2026. Body, battery, and CAD updates from 17–18 Nov, including the accepted v2, are in [CAD / concept K](#cad--concept-k). The current pack is a 3S4P 18650, about 130 Wh, on a slide-out sled that comes out the back of the v2 body. Drive is 4× JGB37-520, 12 V, 530 rpm, with 100 mm mecanum wheels and 4× Pololu DRV8874 drivers (the v2 speed figures in CAD / concept K, and the earlier speed check in REVIEW.md section 5, commit `9b6bc6e`, confirm the drivers are OK). Speed is a benchmark and fun goal; normal driving is slow, with software speed limits and bumpers for safety. The robot camera is a Pi Camera Module 3, not the C270. Start with one ESP32-S3. The finished v2 model is a 200×200×250 mm rounded smoked PETG body; details are in [CAD / concept K](#cad--concept-k).

**Owned now:** laptop (brain now), an existing Pi that is busy with other work, ELEGOO UNO R3 Advanced Starter Kit (servo, 28BYJ-48 stepper + ULN2003, HC-SR04, IR receiver, power module, GY-521 IMU, MAX7219, LCD1602, PIR, RC522, and more), Circuit Playground Express. Code in PlatformIO.

**To buy (updated 17 Nov):** Pi Camera Module 3 (instead of the C270; layer 1 on the desk can still use a phone or a cheap USB cam), MG90S servos + pan-tilt, PCA9685, a separate 5–6 V servo supply, INMP441 + MAX98357A + speaker, one ESP32-S3 DevKitC-1 N16R8 to start, mecanum chassis with 4× JGB37-520 12 V 530 rpm encoder motors, 100 mm wheels, and 4× Pololu DRV8874, 3S4P 18650 pack with BMS (about 130 Wh; README runtime about 3 h continuous driving, about 8 h idle, about 6 h on a typical mix), 15 A main fuse, DC-rated main switch, cliff sensors, INA226, XIAO ESP32S3 Sense later. Euro prices incomplete. Older ballpark for cells was about $30 for 3 cells and a charger.

**Dream upgrades:** lidar, robot arm, face display, self-docking charger, VL53L0X ToF, BNO085 IMU. Depth camera skipped.

**Circuit Playground Express:** LIS3DH, 10 NeoPixels, light, temperature, mic, speaker, IR TX/RX, 7 touch pads, 2 buttons, switch. Uses: status LED ring, head-pat, bump/pickup, IR dock beacon. Too slow for motor control.

## Onboard compute

The Pi rides on the robot as the onboard brain (not a relay): vision, speech, mapping, controller, deciding, WiFi to cloud models. ESP32-S3s keep the reflexes. UNO is for prototyping. CPX is an optional add-on.

| Option | All-in price | Power | Verdict |
| --- | --- | --- | --- |
| Laptop, now | Owned | Wall | Do this now |
| Pi 5 8 GB + AI HAT+ 2 (Hailo-10H) | ~€450–480 in Hungary | 4–15 W | Recommended later |
| Jetson Orin Nano Super | ~€519 in the EU | 7–25 W | Alternative |
| RK3588, mini PCs, Coral | — | — | Skip |

The Active Cooler is compatible with the AI HAT+ 2 (HAT stacks on top). Train YOLO on free Google Colab.

## Wiring

Now: short pre-cut jumpers, UNO next to the breadboard, red 5 V / black ground. Target: I2C / Qwiic daisy chain, modular ESP32-S3s over USB serial / UART, breadboard to perfboard to a custom PCB designed in KiCad (see [PCB / electronics design](#pcb--electronics-design)), real connectors, one shared power bus (motor current never from the MCU 5 V pin).

## Decision log

Condensed from the page. The shorter running log is also in [`decisions.md`](decisions.md).

**18 Nov 2026**

| Decision | Why |
| --- | --- |
| v2 CAD is done and accepted as the current design | Pip, 18 Nov 2026, 12:45 AM (Europe/Budapest), after the side-by-side with the target photo, the renders, and [`cad/v2/README.md`](../cad/v2/README.md). Body 200×200×250 mm rounded smoked PETG, footprint 306×252 mm, head top 429 mm, 5.04 kg, CoG z 128 mm, tips at 31°. 0 interferences at rest and across a 15-pose pan/tilt sweep; all 114 printed parts fit a 256 mm bed. 7-piece shell with tabs and 6×3 mm magnets. 3S4P pack slides out the back. LED bar at the front, lidar pod at the rear, wide capsule head on a short chunky gimbal, mecanum wheels out at the corners. Fusion document "Super bot - v2"; files in [`cad/v2/`](../cad/v2/); commits `3994b36` and `318a829`. The first 300×300 open-frame build was scrapped. Five open decisions wait on Adam (head width, lidar blind sector / pod height, charge-path diode, bumpers). |

**17 Nov 2026**

| Decision | Why |
| --- | --- |
| Private super-bot repo, T3 project, Fusion MCP tunnel, and a Claude-to-Pip webhook | github.com/Programcode/super-bot is the T3 project on the VPS. Fusion runs on Adam's Mac; the VPS reaches the official Fusion MCP at 127.0.0.1:27182 through `fusion-mcp-tunnel.service`. Claude Code messages Pip through a webhook routine, using `scripts/ask-pip.sh`. |
| No e-stop button on the body | The physical button is out of the design. ESP32 reflexes and the verbal "stop" stay. |
| Battery is a 3S4P 18650 pack, about 130 Wh, on a slide-out sled | Adam doubled the earlier 3S idea, then agreed 3S4P is enough rather than going larger. The pack sits flat and slides out the back. README runtime: about 3 h continuous driving, about 8 h idle, about 6 h on a typical mix (replaces earlier rough 4 h / 10 h figures). |
| MG90S pan/tilt servos are OK | Adam wants the head to look around on its own, independently of the body. |
| Concept K v1 is done, frozen, and backed up | Fusion design "Super bot - concept K blockout v1": 406×406 mm footprint, head top 699 mm (`neck_len` 480), about 5.5 kg, centre of gravity 99 mm, no collisions, all printed parts fit a 256 mm bed. Backup: Fusion copy "Super bot - concept K v1 (backup)" and git tag `concept-k-v1`. Files in `cad/concept-k-v1/`. |
| v2 direction is a taller, narrower WALL-E torso, but the redesign has not started | About 30×30 cm stacked torso, 100 mm wheels, chunky short neck. The redesign, including neck length, waits on Adam. Still open: the rear HC-SR04 and the shell material. Logged in [`docs/decisions.md`](decisions.md). |
| Accepted v1 review items: cliffs, INA226, mic and speaker, HC-SR04 level shifting, one ESP32-S3 to start, 15 A fuse, DC-rated main switch, separate servo supply, a Pi Camera Module 3 instead of the C270, and the Pi 5 set to 5 A with the buck next to the Pi | Adam, 17 Nov, from the review in `cad/concept-k-v1/review/REVIEW.md`, and logged in [`docs/decisions.md`](decisions.md) (commit `9b6bc6e`). |
| v2 CAD started | 8:42 PM. The T3 thread "Super bot: v2 tall WALL-E torso in Fusion" builds a ~300×300 mm stacked torso with 100 mm wheels and a short exposed stem instead of a long neck. Output goes to `cad/v2/`, with the plan in [`cad/v2/TASKS.md`](../cad/v2/TASKS.md). Fusion crashed at about 9:19 PM because of the electronics test; the recovered "Super bot - v2" kept stages 1–4, and the thread now saves after every stage. |
| Custom PCBs are designed in KiCad, not Fusion Electronics | The Fusion Electronics test came back PARTLY, leaning NO: its electronics API is read-only, the hidden write commands only act on the active document, and the test crashed Fusion. See [`hw/fusion-electronics-test/RESULT.md`](../hw/fusion-electronics-test/RESULT.md). KiCad 10.0.8 was set up headless on the VPS with the `kicad` MCP, Freerouting, the JLC parts catalog and KiBot JLCPCB outputs. The smoke test passed with ERC 0 and DRC 0 (commit `c96ce9b`, [`docs/kicad-setup.md`](kicad-setup.md)). KiCad is also on the Mac for viewing. |
| Drive is 4× JGB37-520, 12 V, 530 rpm, with 100 mm mecanum wheels and 4× Pololu DRV8874 drivers | Decided 17 Nov. Speed is a benchmark and fun goal; normal driving is slow, with software speed limits and bumpers for safety. The speed check (REVIEW.md section 5, commit `9b6bc6e`) estimates about 2.0–2.2 m/s forward on a hard floor (2.8 m/s no-load), about 1.4–1.7 m/s sideways, 0–2 m/s in about 1.4 s at 5.5 kg, a climb of about 14°, stall about 2.3 A per motor (DRV8874 OK), normal draw 0.3–1 A, and a stall cutoff after about 0.5 s via DRV8874 current sense. |

**16 Nov 2026:** mind gives behaviors and plans, not single steps; layer split mind / controller (~30 fps) / ESP32 reflexes (~1 kHz, always win); skills are not limited to safe primitives; the in-house Qwen bench compared reasoning levels only (low 10/10), not models.

**14–15 Nov 2026:** passion project; six-layer roadmap; mind Qwen3.8-27B on Cerebras via OpenRouter, at least low reasoning; memory keeper GLM-5.3-Flash; local YOLO; audio stack; skip a depth camera; PlatformIO; working name Super bot. See [`decisions.md`](decisions.md) for the full condensed log of earlier days, including the 17 Nov body and parts picks (4× JGB37, 4× BTS7960, Pi 5, cheap LD06/LD19 lidar, and the rest).

## Open questions and next steps

- Open v2 decisions, waiting on Adam (logged 18 Nov 2026, 12:45 AM, Europe/Budapest): 1) The head is 190 mm wide, which matches the target photo but is bigger than the earlier "much smaller than v1" brief — keep it, or shrink it with the `head_w` / `head_h` / `head_d` knobs? 2) The gimbal knuckle blocks about 19° of the lidar. Mask that sector in software (current design), or use a taller pod that puts the scan plane above the head (removes the blind sector, but changes the look)? 3) That is why the lidar pod sits lower and smaller than in the photo; it only changes together with (2). 4) The charge jack is always live, even with the loop key out. Adding a reverse-blocking Schottky or an ideal-diode module, plus a recessed jack or shrouded dock contacts, is recommended. 5) Bumpers are part of the safety plan but are not modelled yet.
- Finish the custom main PCB in KiCad, and fit it to the v2 bay (in progress, 18 Nov), in the T3 thread "Super bot: custom PCB in KiCad (JLCPCB-ready)" (output: [`hw/main-board/`](../hw/main-board/)). Main carrier board: ESP32-S3, 4× DRV8874, INA226, power, e-stop, connectors. The board outline is provisional until it is fitted to the v2 electronics bay. When it messages Pip: read the renders, ERC/DRC, the JLCPCB zip and the README, and send it back if it needs fixes.
- Which harness for the skill-writing and memory agents (thin custom loop for the mind; libfx, Pi agent core, or omp for agents)?
- Wait for Fable's questions and plan; then write layer contracts and the event list.
- A minimal keep-target / hold-distance fallback on the ESP32?
- Run batch 3 of the Qwen bench?
- When to buy the AI HAT+ 2 and Active Cooler.
- Order for the remaining classic ML models.
- Optional vision extras (YOLO-World, face recognition, Depth Anything).
- Pick Luna or Jev for the classifier.
- Check Cerebras prompt caching; cap reasoning tokens.
- Recheck live prices before later-layer purchases.
- Finish layer 1: a talking, seeing head on the desk.
- A final official name, if "Super bot" should not stick.

## Sources

Facts on the page come from Adam's decisions on 14–18 Nov 2026, the Qwen runs in `/workspace/qwen-bench/`, hardware notes, model figures checked on 15 Nov 2026, onboard-compute research that day, the concept K v1 Fusion design and review in this repo (`cad/concept-k-v1/`, including `review/REVIEW.md` and the speed check in section 5 at commit `9b6bc6e`, with the condensed log in [`docs/decisions.md`](decisions.md)), the accepted v2 design in [`cad/v2/`](../cad/v2/) (README, renders, and review checks; commits `3994b36` and `318a829`), the Fusion Electronics test ([`hw/fusion-electronics-test/RESULT.md`](../hw/fusion-electronics-test/RESULT.md)) and the KiCad setup and smoke test ([`docs/kicad-setup.md`](kicad-setup.md), `hw/kicad-smoketest/`, commit `c96ce9b`).
