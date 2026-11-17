# KiCad setup (AI PCB design)

How the VPS is set up so Claude threads can design Super bot PCBs in KiCad headless and get JLCPCB/PCBWay-ready files. Set up 2026-11-17. Proof: `hw/kicad-smoketest/`.

## Versions and paths (VPS, user `codex`)

| Thing | Version | Where |
|-------|---------|-------|
| KiCad (ppa:kicad/kicad-10.0-releases) | 10.0.8 | `/usr/bin/kicad-cli`, Python `pcbnew` in `/usr/lib/python3/dist-packages` (system python3.12) |
| Official libraries | 10.0.8 | `/usr/share/kicad/{symbols,footprints,3dmodels}` (3D models are 3.2 GB) |
| Global lib tables | - | `~/.config/kicad/10.0/{sym,fp}-lib-table` (KiCad template tables + `LCSC`) |
| KiCad MCP server | mixelpixx/KiCAD-MCP-Server 2.9.0 (stable branch) | `~/tools/kicad-mcp-server` (node `dist/index.js`, Python venv `.venv` with system site-packages) |
| Freerouting | 2.5.0 | `~/tools/freerouting/freerouting.jar`, linked at `~/.kicad-mcp/freerouting.jar` |
| Java for Freerouting | OpenJDK 25 | `/usr/lib/jvm/java-25-openjdk-amd64` (the system default `java` stays 21) |
| JLCPCB parts DB | cdfer in-stock snapshot, 522k parts | `~/.local/share/kicad-mcp/jlcpcb_parts.db` (370 MB) |
| KiBot | 1.9.1 (pipx, system site-packages) | `~/.local/bin/kibot` |
| easyeda2kicad | 1.0.1 (pipx) | `~/.local/bin/easyeda2kicad`, library at `~/kicad-libs/lcsc/` |
| kicad-jlcpcb-tools (Bouni) | git 7a46b00 | `~/tools/kicad-jlcpcb-tools`, a GUI plugin kept for reference only (headless work uses KiBot + the MCP DB) |
| rsvg-convert | 2.58 | SVG to PNG |

Mac: KiCad 10.0.8 (unified universal dmg) so Adam can open the `.kicad_pro` files. It is a viewer only; the AI does not use the Mac.

## MCP server: `kicad`

Registered user-wide in `~/.claude.json` (`claude mcp add --scope user kicad ...`), so every new Claude / T3 thread on the VPS gets about 250 `mcp__kicad__*` tools. Env: `KICAD_BACKEND=swig` (headless pcbnew, no GUI needed), `KICAD_PYTHON` = the venv, `JAVA_HOME` = Java 25.

Why this one: it is the most used and most actively maintained KiCad MCP (MIT, about 3.4k stars, release Nov 2026). It supports KiCad 10 and edits boards headless through pcbnew SWIG, unlike Konnect (AGPL, needs the KiCad GUI IPC socket for most PCB edits). It covers schematic capture, footprint placement, routing, Freerouting autoroute, DRC/ERC, every kicad-cli export, JLCPCB part search (Basic/Extended, stock, price) and library management. One server was enough; no second analysis server was needed.

Useful tools:
- Project: `create_project`, `open_project`, `open_board`, `save_board`, `snapshot_project`
- Schematic: `batch_add_and_connect` (fastest), `add_schematic_component`, `connect_to_net`, `set_schematic_component_property` (put `LCSC` on every part), `add_hierarchical_sheet`, `run_erc`, `get_schematic_view`
- Board: `sync_schematic_to_board` (F8), `add_board_outline`, `set_design_rules`, `move_component` / `batch_move_components`, `add_mounting_hole`, `add_copper_pour`, `route_pad_to_pad`, `autoroute`, `run_drc`, `get_board_2d_view`
- Parts: `search_jlcpcb_parts` (`library_type: "Basic"`), `get_jlcpcb_part`, `suggest_jlcpcb_alternatives`
- Export: `export_gerbers`, `export_drill`, `export_pos`, `export_3d_cli`, `export_sch_pdf`

To trim the tool list, set `KICAD_MCP_TOOLBOXES=core` (37 tools plus `open_toolbox`).

## Helper scripts (`~/.local/bin`, on PATH)

- `kicad-check <board.kicad_pcb>`: ERC + DRC with schematic parity and zone refill; exits non-zero on any violation. JSON reports land next to the board.
- `kicad-render <board.kicad_pcb> [outdir]`: schematic SVG/PNG/PDF, PCB front/back SVG+PNG, 3D top/bottom/iso PNG (`kicad-cli pcb render`), STEP. Default outdir is `renders/`.
- `kicad-jlc <project dir> [kibot.yaml]`: KiBot JLCPCB preset that writes the Gerber+drill zip, BOM and CPL into `out/`. Uses the project `jlcpcb.kibot.yaml` or the template at `~/tools/kicad-templates/jlcpcb.kibot.yaml`.
- `source kicad-env`: exports the `KICAD10_*` library vars (KiBot needs them) plus `JAVA25` and `FREEROUTING_JAR`.

Raw commands, if you need them:

```bash
kicad-cli sch erc --severity-all --exit-code-violations -o erc.rpt board.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones --severity-all --exit-code-violations -o drc.rpt board.kicad_pcb
kicad-cli sch export svg -o renders/ board.kicad_sch
kicad-cli pcb export svg --mode-single --fit-page-to-board --exclude-drawing-sheet --layers F.Cu,F.Silkscreen,F.Mask,Edge.Cuts -o front.svg board.kicad_pcb
rsvg-convert -w 1600 -b white front.svg -o front.png
kicad-cli pcb render --side top --quality high --width 1600 --height 1200 -o top.png board.kicad_pcb   # headless, no xvfb needed
kicad-cli pcb render --rotate "-45,0,45" --quality high -o iso.png board.kicad_pcb
kicad-cli pcb export step --force --subst-models -o board.step board.kicad_pcb
easyeda2kicad --full --lcsc_id C2286 --output ~/kicad-libs/lcsc/LCSC   # symbol, footprint, 3D into the LCSC lib
```

## JLCPCB workflow

1. Pick parts with `search_jlcpcb_parts` and prefer `Basic` (Extended costs about $3 per unique part). Check stock.
2. Put the LCSC number in an `LCSC` field on every symbol; KiBot's JLC BOM reads it.
3. Use stock KiCad footprints when they match; otherwise `easyeda2kicad --full --lcsc_id Cxxxx` and use `LCSC:<name>`.
4. Design rules: JLC 2-layer standard is 0.127 mm (5 mil) track/space and 0.3 mm drill / 0.6 mm via minimum. The smoke test uses 0.2 mm clearance and 0.3 mm tracks to be safe. For 4-layer, set the stackup to match JLC's JLC04161H-7628.
5. `kicad-check` must report 0 errors before export.
6. `kicad-jlc .` makes `out/JLCPCB/*.zip` (upload as Gerbers), `out/fab/jlcpcb/*_bom_jlc.csv` (BOM) and `*_cpl_jlc.csv` (CPL).
7. `kicad-render` and look at the PNGs before calling it done.
8. PCBWay accepts the same Gerber zip. Its BOM format differs (Designator, Qty, MPN, Package); build it from the KiBot BOM.

## Gotchas

- `kicad-cli` in KiCad 10 dropped DSN export / SES import. The MCP `autoroute` tool handles that itself through pcbnew.
- Freerouting 2.5 needs Java 25. The MCP gets it from `JAVA_HOME`. Don't switch the system `java` (21), because other tools use it.
- KiBot 1.9.1 doesn't know KiCad 10's `KICAD10_*` variables on its own. `kicad-jlc` sources `kicad-env` first. KiBot must be installed with `--no-compile` (already done).
- ERC flagged "library not in configuration" until the global `sym-lib-table` / `fp-lib-table` existed in `~/.config/kicad/10.0/`. They're there now; a fresh user needs them copied from `/usr/share/kicad/template/`.
- The first `search_symbols` call can time out (30 s) while the symbol cache warms up. Retry, or use `get_symbol_info Lib:Name` when you know the name.
- Every MCP session is a fresh process, so call `open_board` before board tools. Schematic tools work straight on the file.
- KiBot writes `*.kicad_pcb-bak`, and the MCP writes `.mcp-backups/`. Both are gitignored.
- CPL coordinates come out with negative Y (KiCad's Y axis points down). JLC accepts that. Always check part rotations in JLC's assembly preview.
- The MCP's GUI tools (`launch_kicad_ui`, `kicad_gui_*`) and the IPC backend need a running KiCad GUI. They aren't used on the VPS.
