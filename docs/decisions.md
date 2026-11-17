# Decisions

Key decisions for Super bot. Newest first. Dates are Europe/Budapest. The full log with reasons is on the Grok Bot page (snapshot in [super-bot-page.md](super-bot-page.md)). Append a row whenever something is decided.

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
