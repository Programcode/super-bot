# CLAUDE.md: Super bot

Project context for Claude Code (and any other coding agent) working in this repo on Adam's VPS through T3 Code.

## What this is

Super bot (temporary name) is Adam's passion-project home robot: an indoor mecanum-wheel robot with a creature-style head on a neck (like WALL-E or Vector), a translucent smoked shell, and a layered AI brain. It is not schoolwork. Adam is 15, codes mostly with AI agents, and is comfortable with Python and web stuff.

- **Source of truth for the plan:** the Grok Bot page "Super bot", owned by Pip. Snapshot: [`docs/super-bot-page.md`](docs/super-bot-page.md). Decisions: [`docs/decisions.md`](docs/decisions.md).
- **Current roadmap layer:** 1 of 6, "Brain on a desk". Body design and CAD are being explored in parallel.

## Goals

1. A robot that looks genuinely great: Apple-level industrial design, densely packed, no wasted space.
2. A layered brain: cloud mind (Qwen3.8-27B on Cerebras via OpenRouter) gives behaviors and plans, a local controller runs them at ~30 fps, and ESP32-S3 reflexes at ~1 kHz always win.
3. Build in layers. Each layer works and is fun on its own.

## Design rules (do not break these without Adam's OK)

- **No Roomba look.** No smooth puck, no toy-like blob.
- **Creature silhouette:** a head with a face (1.3" TFT eyes) on a neck, on a mecanum base. Height comes from the neck; the base stays dense.
- **Apple-style dense enclosed shell:** seamless, no visible screws, hidden wiring, tucked wheels, integrated lidar, glowing status ring.
- **Translucent smoked walls:** tinted see-through plastic (not glass) so the real internals show, like "Chinese EV" inside tech: lots of visible, tidy, connected hardware.
- **Built from the real parts** below, at real dimensions. No invented components.
- **Cheap DIY chassis:** a 40×40 cm plate (plywood or aluminium), not a prebuilt kit.

## Parts (as planned; most not bought yet)

- Drive: 4× JGB37 12 V encoder gear motors, 80 mm mecanum wheels, 4× BTS7960 motor drivers.
- Compute: Raspberry Pi 5 8 GB (owned), Raspberry Pi AI HAT+ 2 later, 2× ESP32-S3 (not owned yet).
- Sensors: BNO085 IMU, HC-SR04 ultrasonics, VL53L0X ToF, Logitech C270 webcam.
- Face: 1.3" TFT. Status ring and backup safety: Circuit Playground Express (owned).
- Power: 3S 18650 pack.
- Later: cheap lidar (LD06 / LD19), arm, self-docking charger. Custom PCB is v2 (KiCad + JLCPCB) after module prototyping.

## Repo layout

| Path | What goes there |
| --- | --- |
| `cad/` | Fusion designs, exported STEP/STL, Fusion API scripts |
| `firmware/esp32/` | ESP32-S3 reflex and motor firmware (PlatformIO) |
| `firmware/cpx/` | Circuit Playground Express status ring and backup safety |
| `pi/` | Onboard brain (Python, later ROS 2) |
| `electronics/` | Wiring diagrams, future KiCad PCB |
| `tests/benchmarks/` | Mind benchmarks and test suites |
| `docs/` | Page snapshot, decisions, concept renders |
| `scripts/` | Helpers, including `ask-pip.sh` |

## How to work

- Small, iterative steps. Show results (renders, screenshots, test output) before moving on.
- Keep [`docs/decisions.md`](docs/decisions.md) current: append a dated row whenever a decision is made.
- Do not edit `docs/super-bot-page.md` by hand. Pip regenerates it from the Grok Bot page.
- Never commit secrets (`.env*`, keys, tokens). `.env.pip` is gitignored on purpose.
- Never buy anything or sign up for paid services.
- Safety logic (reflexes, e-stop, watchdog) lives on the ESP32 and no skill or higher layer may override it.

## Fusion (CAD)

_Being verified on the VPS. This section is updated with what is actually installed and how Claude Code connects to it._

## Talking to Pip

Pip is Adam's Grok Bot build partner. Pip owns the plan and the Super bot page, so anything that changes the plan goes through Pip.

To reach Pip, POST JSON to the Pip webhook (a Grok Bot routine, "Super bot: messages from Claude Code") with these fields:

- `thread`: the T3 thread id or title you are working in
- `kind`: one of `question`, `decision-needed`, `status`, `done`, `blocker`
- `message`: plain text

The easy way:

```bash
scripts/ask-pip.sh decision-needed "Neck: fixed 30 cm or telescoping? Renders in cad/renders/neck-options.png" "<thread id or title>"
```

The script reads `PIP_WEBHOOK_URL`, `PIP_WEBHOOK_KEY` and `PIP_WEBHOOK_AUTH_HEADER` from the environment or from `.env.pip` in the repo root (gitignored; template in `.env.pip.example`). If they are not set, tell Adam in the thread instead.

Rules:

- Use it for real questions, decisions you need, finished results, and blockers. Not for every step.
- Pip replies directly in your T3 thread (Pip can read and post to T3 threads), so keep working or wait there.
- Never put secrets, keys, or tokens in a message.
