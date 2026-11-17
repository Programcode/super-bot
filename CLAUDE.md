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

Verified 17 Nov 2026 by a setup thread on the VPS (read-only check):

- **Fusion is not installed on the VPS.** It runs on Adam's Mac (free personal license). There is no Wine, VM, display, or Fusion process on the VPS.
- **Claude Code reaches it over MCP anyway.** `claude mcp list` shows `fusion: http://127.0.0.1:27182/mcp (HTTP) - Connected`, defined in the user config (`~/.claude.json`), so every project can use it.
- **How:** port 27182 on the VPS is an SSH port-forward to the Mac, run by the systemd user unit `~/.config/systemd/user/fusion-mcp-tunnel.service` (`ssh -N -L 127.0.0.1:27182:127.0.0.1:27182 adam-macbook`, over Tailscale). On the Mac it lands on Fusion's official MCP server (Preferences > General > API > "Fusion MCP Server").
- **Tools exposed:** `fusion_mcp_read`, `fusion_mcp_execute`, `fusion_mcp_update`, `fusion_mcp_electronics_read`.

For it to work, all of these must be true: the Mac is awake and on Tailscale, Fusion is open on the Mac with the MCP server enabled, and the tunnel service is up (`systemctl --user status fusion-mcp-tunnel`). If a call fails, check those in that order and tell Adam (or Pip) what is down instead of retrying in a loop.

Working rules for CAD:

- Start each session with a `fusion_mcp_read` to see what is open. Do not modify or close designs you did not create without asking.
- Prefer reproducible Fusion API scripts saved in `cad/scripts/` over one-off clicks, so a design can be rebuilt.
- Export STEP/STL to `cad/exports/` and screenshots to `cad/renders/`, and commit them with the script that made them.
- Change one thing at a time and show a render after each meaningful change.

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
