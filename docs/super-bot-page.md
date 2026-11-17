# Super bot: page snapshot

> **Synced from the Grok Bot page "Super bot" on 17 Nov 2026** (canvas id `45200f5a-d70f-476f-988f-23a206c0bfd9`, [open the live page](https://cursor.com/canvas/store-3f866d4b-6e7e-4115-b119-325492ec6c21/45200f5a-d70f-476f-988f-23a206c0bfd9), Adam's account).
> The page itself says "Last updated: 16 Nov 2026, 5:39 PM (Europe/Budapest)". Body, parts, and CAD decisions from 17 Nov are in [`decisions.md`](decisions.md) and supersede the older hardware rows below (for example BTS7960 drivers instead of TB6612FNG, a cheap LD06/LD19 lidar instead of RPLIDAR C1).
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

## Hardware (as on the page, 15–16 Nov)

**Owned now:** laptop (brain now), an existing Pi that is busy with other work, ELEGOO UNO R3 Advanced Starter Kit (servo, 28BYJ-48 stepper + ULN2003, HC-SR04, IR receiver, power module, GY-521 IMU, MAX7219, LCD1602, PIR, RC522, and more), Circuit Playground Express. Code in PlatformIO.

**To buy (page version, partly superseded 17 Nov):** USB webcam, MG90S servos + pan-tilt, PCA9685, 5 V 3 A supply, INMP441 + MAX98357A + speaker, ESP32-S3 DevKitC-1 N16R8, mecanum chassis with 4 encoder motors and drivers, 18650 cells and charger, XIAO ESP32S3 Sense later. Euro prices incomplete.

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

Now: short pre-cut jumpers, UNO next to the breadboard, red 5 V / black ground. Target: I2C / Qwiic daisy chain, modular ESP32-S3s over USB serial / UART, breadboard to perfboard to custom PCB, real connectors, one shared power bus (motor current never from the MCU 5 V pin).

## Decision log

See [`decisions.md`](decisions.md) for the condensed log, including the 17 Nov body and parts decisions that the page did not yet have at sync time.

## Open questions and next steps

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
