# KiCad smoke test

A tiny 20 x 15 mm board that proves the headless KiCad pipeline on the VPS works end to end, before the real Super bot PCBs.

Circuit: 2-pin header (VIN, GND) -> 1k resistor -> red LED -> GND.

| Ref | Part | Footprint | LCSC | JLC type |
|-----|------|-----------|------|----------|
| R1 | 1k 1% 0603 (UNI-ROYAL 0603WAF1001T5E) | Resistor_SMD:R_0603_1608Metric | C21190 | Basic |
| D1 | Red LED 0603 (KENTO KT-0603R) | LED_SMD:LED_0603_1608Metric | C2286 | Basic |
| J1 | 1x02 2.54 mm pin header (BOOMELE B-2100S02P-A110) | PinHeader_1x02_P2.54mm_Vertical | C124375 | Extended, through-hole |

J1 is through-hole and there is no Basic 1x2 header, so for a real order leave it out of assembly and hand-solder it, or pay for THT assembly.

## How it was made

Everything went through the `kicad` MCP server (mixelpixx/KiCAD-MCP-Server v2.9.0), driven by an MCP client on the VPS:

1. `create_project`, `batch_add_and_connect` (3 parts + nets), `set_schematic_component_property` (LCSC fields), `run_erc`
2. `open_board`, `sync_schematic_to_board`, `add_board_outline` (rounded 20x15), `set_design_rules`, `move_component` x3, `save_board`
3. `autoroute` (Freerouting 2.5.0 on Java 25, 4.6 s, 5 tracks, 0 vias), `run_drc`
4. MCP export tools (`export_gerbers`, `export_drill`, `export_pos`, `export_3d_cli`, `get_board_2d_view`) were checked too

Then the helper scripts (see docs/kicad-setup.md) made the committed outputs:

- `kicad-check kicad-smoketest.kicad_pcb`: ERC 0, DRC 0 violations, 0 unconnected, 0 schematic-parity issues (reports in `reports/`)
- `kicad-jlc .`: KiBot 1.9.1 with its built-in JLCPCB preset (`jlcpcb.kibot.yaml`)
- `kicad-render kicad-smoketest.kicad_pcb`: the PNG/SVG/PDF/STEP files in `renders/`

## Files

- `out/JLCPCB/kicad-smoketest-_JLCPCB_compress.zip`: Gerbers + drill files, ready to upload to JLCPCB
- `out/fab/jlcpcb/kicad-smoketest_bom_jlc.csv`: BOM (Comment, Designator, Footprint, LCSC Part #)
- `out/fab/jlcpcb/kicad-smoketest_cpl_jlc.csv`: CPL / pick-and-place (Designator, Mid X, Mid Y, Rotation, Layer)
- `out/3d/kicad-smoketest-3D.step` and `renders/kicad-smoketest.step`: 3D model
- `out/docs/kicad-smoketest-schematic.pdf`, `out/*-erc.html`, `out/*-drc.html`
- `renders/pcb-3d-top.png`, `pcb-3d-bottom.png`, `pcb-3d-iso.png`: ray-traced 3D renders
- `renders/pcb-front.png`, `pcb-back.png`: 2D copper/silk/mask plots
- `renders/kicad-smoketest.png`: schematic

Nothing was ordered. Check JLCPCB rotation offsets in their preview before a real order, since KiCad and JLC footprints sometimes disagree.
