# Fusion Electronics capability test (AI agent via `fusion` MCP)

Date: 2026-11-17. Fusion 2706.1.17 (Personal license) on Adam's Mac, reached from the VPS through the `fusion` MCP server (SSH tunnel to 127.0.0.1:27182). Run by Claude Code (Opus 5.5) in the T3 thread "Fusion Electronics capability test". The "Super bot: v2 tall WALL-E torso in Fusion" thread was using the same Fusion session throughout.

## Verdict

**Fusion is viable for a full multi-board robot PCB project done by an AI: PARTLY, leaning NO.**

Recommendation: do the custom-PCB project in **KiCad**, not Fusion.

Why:

1. **There's no supported write API.** The `adsk.electron` Python API is a read-only preview. It can't add parts, nets, traces or outlines, and it can't create an electronics document. Everything an agent would need goes through undocumented text commands (`Electron.run`, `Electron.runScript`, `Electron.mfgexport`), some of them labelled dev/testing. Autodesk can change or remove them in any update.
2. **Everything depends on the active document.** You can only create an electronics document by firing a UI command. That command is async and takes focus (observed). `Electron.run` and `Electron.runScript` take no document argument (`Usage: Electron.run command`), so they almost certainly act only on the active editor. That's inferred from the usage strings, not tested. An agent therefore has to own the Fusion UI while it works.
3. **It crashed Fusion on the first real attempt.** Creating one empty Electronics design shifted focus, another agent's MCP screenshot then landed on that document, and Fusion segfaulted (details below). With one Fusion on one Mac shared by several agents and Adam, that will happen again.
4. **Every step goes through the Mac.** Fusion only runs on Adam's Mac, so each step needs the Mac awake, Fusion open, the MCP add-in enabled and the tunnel up. Over about 10 minutes of use I saw one unexplained `ECONNRESET` while Fusion was healthy, and one crash.
5. **Why not a flat NO:** the engine underneath is full EAGLE 9.7, with the whole command language (ADD, NET, AUTO, ERC, DRC, RUN ulp), a CAM job runner (`Electron.mfgexport <dir> <job.cam>`), shipped CAM jobs and ULPs. On a *dedicated* Fusion instance that no one else touches, an agent could probably script a board end to end. I could not prove that today: steps 2 to 5 never ran (see below).

By comparison, and **not tested in this run**: KiCad has a documented, file-based design format and a headless `kicad-cli` (ERC, DRC, Gerber, drill, BOM, position files, STEP export). It runs on Linux, so it could run on the VPS with no GUI and no shared session.

## Step-by-step results

### 1. What the MCP tools offer for electronics: done

- `fusion_mcp_electronics_read` is read-only, and only works on the *active* document.
- `fusion_mcp_execute` (Python) can import `adsk.electron`. Its classes (Schematic, Board, Part, Element, Signal, Net, Error, Package3d, ...) are read-only. The only writes I found were `Sheets.create`, `deleteEntities` and the begin/end/cancel design-change calls.
- `ElectronicsExportManager` only exports EAGLE 9.6.2 `.sch`, `.brd` and `.lbr` files. There's no Gerber, BOM, CPL or STEP export in the API.
- `adsk.core.DocumentTypes` only has `FusionDesignDocumentType`, so `app.documents.add()` can't create an electronics document.
- `TextCommands.List /hidden` shows the real path in:
  - `Electron.run <EAGLE command>`
  - `Electron.runScript <file.scr>`
  - `Electron.mfgexport <outputDir> <camJobFile>` (Gerber, NC drill, assembly and drawing)
  - `Electron.mfgodb`, `Electron.importSchAndBrd`, `PCB.export`, `PCB.loadbrdoutline`, `pcb3d.update`, `NuElectronCommands.PCBLinkToBrdCmd`
  - test-automation hooks such as `Electron.LeftButtonDown` and `Electron.KeyPressed`
- New documents come only from UI command definitions: `NewElectronIntegratedDesignDocumentCommand`, `NewElectronDesignDocumentCommand`, `NewElectronSchDocumentCommand`, `NewElectronPcbDocumentCommand`, run with `CommandDefinition.execute()`.
- Found on the Mac over SSH, inside the app bundle under `.../Electron/LibEagle/examples/`:
  - CAM jobs: `cam/examples/example_2_layer.cam`, plus Seeed, OSH Park, AISLER and Beta Layout jobs. There's **no JLCPCB job**.
  - ULPs: `bom.ulp`, `mount.ulp`, `mountsmd.ulp`, `centroid-screamingcircuits-smd.ulp`. The BOM and centroid ULPs normally open dialogs.
  - Design rules: `design rules/examples/default.dru`.
  - Libraries: `Resistor.lbr` (`R` / `CHIP-0603(1608-METRIC)`), `LED.lbr` (`CHIP-FLAT-R` / `_0603-0.55MM`), `Connector.lbr` (`PINHD-1X2`).
  - There's no headless EAGLE binary in the bundle (`LibEagle/bin` holds only resources), so nothing can run without the Fusion GUI.

### 2. Tiny test board: failed (Fusion crashed), then blocked

Method: `CommandDefinition.execute()` on `NewElectronIntegratedDesignDocumentCommand`, then (planned) `Electron.runScript` with [schematic.scr](schematic.scr) and [board.scr](board.scr).

What happened, all times CET:

1. 21:18:47: the create command fired. An integrated "Untitled" Electronics document appeared, with Schematic, PCB and 3D PCB products, and became the active tab.
2. 21:18:52: my next script tried to `saveAs` it as "Super bot - electronics test" in a new "Electronics test" folder, then reactivate the v2 document in a `finally`. The MCP call **timed out**.
3. 21:18:53: **Fusion crashed** (segfault, pid 34028). The CER crash log shows the main thread in `Nu::Canvas::invalidate` ← `ScreenshotFuncRegister` ← `Nu::SceneUtilities::takeScreenshot` ← MCP `readScreenshot`. The screenshot came from the v2 thread's MCP session, while my new Electronics document was active. That thread's scripts at 21:18:52 to 21:18:53 also logged `Active product is not a Design`, because they had hit my document.
4. Adam restarted Fusion at about 21:23. My document was never saved and is gone. The v2 thread had to recover and rebuild its own work.

My `saveAs` didn't crash Fusion. The trigger was a screenshot taken while the active document was an Electronics document, and that state existed only because creating the document had switched focus.

After the crash, Pip set a rule for the shared session: **never change the active document; if the API needs the electronics document to be active, stop and write that up.** Step 2 needs exactly that, both to create the document and to run any EAGLE command in it, so I stopped there.

What's prepared but not run:

- [schematic.scr](schematic.scr): R1 1 kΩ 0603, D1 red 0603 LED, JP1 2-pin header, nets VIN, LED_A and GND drawn by pin coordinates read from the shipped libraries.
- [board.scr](board.scr): a 20 × 15 mm outline on layer 20, parts moved by name, then `AUTO ;`.

### 3. ERC and DRC: not run

The plan was EAGLE's `ERC` and `DRC ;` via `Electron.run`, then reading `Schematic.errors` and `Board.errors` through `adsk.electron`. They need the active editor, so they're blocked for the same reason.

### 4. Gerber, drill, BOM and CPL export: not run

- Gerber and drill: `Electron.mfgexport <dir> example_2_layer.cam` looks headless, but it's untested. JLCPCB takes standard RS-274X/X2 Gerbers and Excellon drill files, and there's no JLC-specific job.
- BOM and CPL in JLCPCB format: Fusion has no JLCPCB exporter. The shipped ULPs open dialogs. The fallback is to build the CSVs from `Part`/`Element` (name, value, package, x, y, angle, mirror) in our own script, which means it's our code, not Fusion's.
- Whether this works without a human clicking: unknown.

### 5. 3D model into a Fusion design: not run

The integrated document already includes a "3D PCB" product, and there are `pcb3d.update` and `PCBDocumentUpdateCmd` commands. So the 3D board likely comes for free inside the electronics document, but it's unverified. Getting it into an existing design such as "Super bot - v2" would mean inserting or deriving a component across documents, which needs that design to be active.

## How much needed GUI clicks or hacks

- No human clicks were needed for what did run. But everything past step 1 depends on undocumented text commands and on running UI commands as if a user had clicked them. That counts as a hack, not an API.
- Creating a document has the same effect as a click: it's async, it steals focus, and the next MCP call from *any* agent goes to the new document.

## Reliability

Poor in this setup. In about 10 minutes of Fusion time:

- 1 × `ECONNRESET` from the MCP bridge while Fusion was healthy (a plain retry worked)
- 1 × full Fusion crash, which cost the v2 thread unsaved work. My two timeouts and the second `ECONNRESET` came after the crash and were caused by it, so they don't count separately.

## Leftovers for Adam to check

- Fusion's crash recovery may have reopened my unsaved "Untitled" Electronics document. Close it without saving. While it's open it's the same screenshot-crash hazard if anyone activates it.
- The `saveAs` script may have created an empty "Electronics test" folder in Default Project before the crash. Delete it if it's there.

## Files

- [RESULT.md](RESULT.md): this report
- [schematic.scr](schematic.scr), [board.scr](board.scr): the prepared EAGLE scripts (not executed)
- No Gerber, drill, BOM, CPL or 3D exports: those steps never ran.
