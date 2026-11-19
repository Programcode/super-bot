# Rev B: handoff (paused 18 Nov 2026, ~12:40 UTC)

Paused on Adam's request. Rev A (`hw/main-board/`, tag `main-board-rev-a`) is untouched.

## Where it stands
- **Schematic:** done, ERC 0. Regenerate with `~/tools/kicad-mcp-server/.venv/bin/python gen/build_sch.py`. It has:
  - DRV8874 PWM mode and nFAULT on all four drivers
  - JSM 74LVC1G123, SRV05-4 USB ESD, 22 Ω USB series resistors
  - servo rail at 5.0 V (same parts as the 5 V buck), shared EN divider, PG unused
  - bumper resistor arrays, 21 test points, vertical XT60PB-M ×2 (Pip's fit fix)
  - all THT parts DNP (hand-solder kit)
  - 196 placed parts, 58 unique
- **Placement:** done, with no courtyard overlaps. The ESP32 antenna sits over an 18 × 6.4 mm board cut-out. `gen/build_pcb.py` handles placement.
- **Routing:** `main-board-rev-b.kicad_pcb` is the current routed board. After Freerouting, repair cleanup and one `gen/fixup.py --inner` pass, DRC (errors only) shows:
  - 6 unconnected: 4 GND, 1 M1_ENC_A, 1 VMOT
  - 2 copper-edge errors on H103 at 0.2987 mm. Its anchor is now (182.3, 66.3) in `build_pcb.py`, and the routed board was moved by hand to match.
  - 1 courtyard overlap, not yet looked at
- **Snapshots:** `/tmp/sbpcb/rb_routed.kicad_pcb` (raw Freerouting) and `/tmp/sbpcb/rb_fixup1.kicad_pcb` (current). /tmp may be wiped.

## 19 Nov: power plugs pass (power-plugs thread)
- **J101/J102:** the vertical Amass XT60PB-M (LCSC C19268037, 19,502 in stock at JLC) is kept for both, as Pip confirmed. The footprint and the F101 holder were checked against their datasheets (see RESEARCH.md).
- **J101 polarity fixed:** + is now pad 1, the square-corner end. The footprint is rotated 180° with its nets swapped, so the copper did not move. The changes are in `gen/symbols.py`, `gen/design.py`, `gen/build_pcb.py` and `gen/finish.py`, and the schematic was regenerated.
- **J101 GND pad:** thermal spokes are 1.5 mm (they were 0.5 mm), because that pad carries the whole battery return.
- **Gate (`kicad-check`, zones refilled), from `reports/`:**
  - ERC: 0.
  - Schematic parity: 0.
  - DRC errors: 3. There are 2 copper-to-edge errors on H103 (0.2987 mm), at the bottom-right corner. The third is a courtyard overlap between H103 and J414.
  - Unconnected: 6. That is 4 GND (U303 pad 21 and C606 pad 2 to the GND pours), 1 M1_ENC_A (C606 pad 1) and 1 VMOT.
  - Warnings: 312 silkscreen warnings, because `finish.py` hasn't run yet.
  - None of these is in the power input area; all were there before this pass.
- **Outputs:** `out/` (KiBot; DRC preflight skipped, ERC on) and `renders/` are regenerated. **Not orderable** until the steps below are done.
- **Duplicate footprint UUIDs:** 25 groups of footprints share UUIDs (for example J601/J701/J801/J901), which makes every pcbnew save reorder them in the file. It does no harm in KiCad, but the generator should give each one its own UUID.

## Next steps (in order)
1. Find the courtyard overlap. Check the KiCad DRC JSON `items`.
2. Clear the last connections:
   `T=$(~/tools/kicad-mcp-server/.venv/bin/python gen/ripup.py main-board-rev-b.kicad_pcb 0.8 | grep TRAPPED= | cut -d= -f2)`, then `gen/fixup.py main-board-rev-b.kicad_pcb --inner --first=$T`.
   Don't use `--cut-pours`, so the 15 A pours stay intact.
3. Run `gen/clean_loop.sh main-board-rev-b.kicad_pcb --repair`, then `gen/finish.py` (labels, polarity marks, fiducials), then `gen/clean_loop.sh` again.
4. Run `kicad-check main-board-rev-b.kicad_pcb`, move the reports into `reports/`, then `~/tools/kicad-mcp-server/.venv/bin/python gen/review.py` for the checklist. Write it to `REVIEW.md`.
5. Run `kicad-jlc .` and `kicad-render main-board-rev-b.kicad_pcb`, then `python3 gen/pcbway.py` (PCBWay BOM and centroid) and `python3 gen/cost.py 2` / `5`.
6. Write `README.md` for rev B: the changes vs rev A, the 15 A input proof (the review shows the pours unbroken), the XT60PB fit fix, and open questions. Fill rev B into `../QUOTES.md` if the numbers moved.
7. Commit, push (fast-forward; the v2 thread keeps uncommitted files in this checkout, so don't stash them), then `scripts/ask-pip.sh done "..."`. Mention the XT60PB vertical fix and the edge-facing parts listed in RESEARCH.md.

## Gotchas
- pcbnew SWIG breaks after `BOARD.Remove()`. Remove items by UUID at the text level, or one round per process (`cleanup.py`).
- `route.py` refuses a board that already has zones, so rerun `build_pcb.py` first.
- DRC JSON sometimes pairs a stale second item. Trust the first item, or check connectivity with `fixup.clusters()`.
- Freerouting runs take about 25 min. Use `heavy` and run them in the background.
