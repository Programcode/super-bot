# Super bot

Super bot (temporary working name) is Adam's passion-project home robot: an indoor mecanum-wheel robot with a creature-style head on a neck (think WALL-E or Vector), a translucent smoked shell, and a layered AI brain that can see, map, talk, fetch, remember, and teach itself new skills.

> **Master page:** the single source of truth is the Grok Bot page **"Super bot"** in Adam's Grok Bot library:
> https://cursor.com/canvas/store-3f866d4b-6e7e-4115-b119-325492ec6c21/45200f5a-d70f-476f-988f-23a206c0bfd9
> (opens for Adam's signed-in account; canvas id `45200f5a-d70f-476f-988f-23a206c0bfd9`).
> A markdown snapshot lives in [`docs/super-bot-page.md`](docs/super-bot-page.md). Pip re-syncs it whenever the page changes.

## Current status (17 Nov 2026)

- **Roadmap layer:** 1 of 6, "Brain on a desk" (laptop + webcam, local YOLO, Qwen mind, Whisper + Piper).
- **Body design:** exploring. AI concept renders are in [`docs/concepts/`](docs/concepts/). Current pick is concept K (WALL-E-style head on a neck, smoked translucent shell).
- **CAD:** starting in Autodesk Fusion, driven by Claude Code on the VPS. See [`cad/`](cad/) and the Fusion section of [`CLAUDE.md`](CLAUDE.md).
- **Hardware:** parts plan agreed, mostly not bought yet. Adam owns a Pi 5 8 GB, an ELEGOO UNO kit, and a Circuit Playground Express. No ESP32-S3s yet.
- **Brain:** architecture drafted (mind / controller / reflexes). A full brain plan from Claude Fable is pending review.

Key decisions are in [`docs/decisions.md`](docs/decisions.md).

## The robot in one table

| Part | Plan |
| --- | --- |
| Drive | 80 mm mecanum wheels, 4× JGB37 12 V encoder gear motors, 4× BTS7960 drivers |
| Chassis | Cheap DIY 40×40 cm plate (plywood or aluminium), enclosed in a dense smoked translucent shell |
| Onboard brain | Raspberry Pi 5 8 GB, plus Raspberry Pi AI HAT+ 2 (Hailo-10H) later |
| Real-time | 2× ESP32-S3 (reflexes, motor control at ~1 kHz) |
| Sensors | BNO085 IMU, HC-SR04 ultrasonics, VL53L0X ToF, Logitech C270 webcam, mic |
| Face | 1.3" TFT face on the head |
| Status ring | Circuit Playground Express (10 NeoPixels), also backup tilt / safety |
| Power | 3S 18650 pack |
| Later | Cheap lidar (LD06 / LD19), arm, self-docking charger, custom PCB (v2, KiCad + JLCPCB) |

## Repo layout

```
.
├── CLAUDE.md              Project context for Claude Code (AGENTS.md points here)
├── docs/
│   ├── super-bot-page.md  Snapshot of the Grok Bot master page
│   ├── decisions.md       Decision log (keep current)
│   ├── sync.md            How the page snapshot is kept in sync
│   └── concepts/          AI concept renders (not real photos)
├── cad/                   Fusion designs, STEP/STL exports, Fusion API scripts
├── firmware/
│   ├── esp32/             ESP32-S3 reflex + motor firmware (PlatformIO)
│   └── cpx/               Circuit Playground Express status ring / backup safety
├── pi/                    Onboard brain (Python, later ROS 2)
├── electronics/           Wiring diagrams, future KiCad PCB
├── tests/benchmarks/      Mind benchmarks and test suites
└── scripts/               Helper scripts (ask-pip.sh, sync notes)
```

## License

MIT, see [LICENSE](LICENSE).
