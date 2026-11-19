# Rev B research notes

The rules behind rev B's changes, with their sources. Figures marked *calc* are worked out from datasheet equations; *plot* means read off a datasheet graph. Compiled 18 Nov 2026.

## DRV8874 (TI, HTSSOP-16 PowerPAD)

Source: [DRV8874 datasheet SLVSF66A](https://www.ti.com/lit/ds/symlink/drv8874.pdf) §10.1 (layout), §8.2.1.2 (thermal), §7.3.3 (current sense), package drawing PWP0016J.

- **Capacitors:** the 0.1 µF VM cap, the bulk cap, the CPH–CPL 22 nF and the VCP–VM 100 nF go as close to the pins as possible. VM, OUTx and PGND need wide copper.
- **Thermal pad:** tie it to the top GND pour and the inner GND plane through vias. TI's thermal model uses a 1.2 mm via grid. Vias under paste should be tented or plugged.
- **RθJA:** about 36 °C/W JEDEC, and about 31–32 °C/W on 4 layers with 2–4 cm² of top copper (*plot*, Fig. 21). Thermal shutdown is at 175 °C.
- **Loss model:** P = I²·(R_HS + R_LS) + 0.5·VM·I·(tr + tf)·f_PWM. R_DS(on) is about 100 mΩ per FET, ×1.25 at 85 °C, and tr/tf are about 150 ns.
- **Our worst case (*calc*, 12.6 V, 20 kHz):**
  - 1 A: 0.33 W, +11 °C.
  - 2.3 A (a full stall of the JGB37-520 530 rpm): about 1.45 W, +46 °C. Fine even continuously.
  - The 3.1 A ITRIP is above the motor's own stall current, so the driver only chops on a short or a jam. The firmware stall cut (0.5 s) is the second layer.
- **PMODE:** a tri-level input. It reads logic high above 1.5 V and is latched when nSLEEP rises (§7.3.2). Rev B ties it to +3.3 V (PWM mode) through a dedicated B.Cu bus.
- **IPROPI:** gain 455 µA/A. A 10 nF filter next to the pin is recommended if transients trip the regulation (§7.3.3.2). Rev B keeps it.

## TPS56637 (TI, VQFN-HR-10)

Sources: [TPS56637 datasheet SLVSEG1A](https://www.ti.com/lit/ds/symlink/tps56637.pdf) §10.1 and table 4; [EVM user's guide SLVUBE3B](https://www.ti.com/lit/pdf/slvube3) §5.1.

- **Input caps:** CIN (≥10 µF) and 0.1 µF go right at VIN/PGND, with at least two vias each for VIN and GND near the pins.
- **SW and BOOT:** keep the SW node short and wide, and 0.1 µF from BOOT to SW.
- **Feedback:** the divider sits next to FB, its top leg taps VOUT separately, and FB stays away from SW.
- **AGND:** joins PGND at one point.
- **5 V values:** L = 3.3 µH, COUT 20–100 µF effective, plus the optional 100–220 pF / 20 kΩ feed-forward. Rev B uses the same values for both rails, since the servo rail is now 5.0 V too: one inductor line, one FB pair.
- **Loss (*plot*/*calc*):** about 92 % efficient at 12 V → 5 V/3 A (about 1.2 W), about 90 % at 5 A (about 2.7 W). RθJA is 49 °C/W JEDEC, so 5 A continuous needs the board to do better than that.
- **What we expect:** the Pi 5 + AI HAT+ 2 typically draw 2–3 A, which is comfortable. 5 A is a peak. The IC sits on the In1 GND plane, with GND vias at PGND and a VIN pour.

## ESP32-S3-WROOM-1 (Espressif)

Sources: [ESP32-S3 hardware design guidelines, PCB layout](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html); [schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html); [WROOM-1 datasheet v1.8](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) §11 and fig. 11-1.

- **Antenna:**
  - Put it outside the board edge, or cut the board away under and beside it. No copper on any layer in the antenna area.
  - Add dense GND vias near the antenna.
  - Keep USB, UART, motor and switching traces away from it.
  - **Rev B:** the antenna hangs over an 18 × 6.4 mm cut-out in the top edge, and a copper keepout around it covers all layers.
- **Strapping pins:** GPIO0 needs a pull-up (high = normal boot). GPIO45 must stay low at reset on modules with 3.3 V flash. GPIO46 has a weak pull-down. Rev B keeps rev A's 10 kΩ pull-downs on IO45/IO46 and the 10 kΩ pull-up on IO0. GPIO3 only matters if the JTAG-select eFuse is burned (it isn't).
- **EN:** 10 kΩ + 1 µF (kept).
- **USB:** reserve 22–33 Ω series resistors close to the chip, use 90 Ω differential over solid GND, and put return vias at layer changes. **Rev B adds 2 × 22 Ω.**
- **Power:** 3.0–3.6 V, at least 0.5 A, at least 10 µF at the 3V3 entry, and 0.1 µF per pin (kept: 22 µF + 2 × 100 nF).

## 4-layer stackup and copper

Sources: [Altium on 4-layer power planes](https://resources.altium.com/p/right-way-use-power-planes-4-layer-pcb-stackup); TI [SLLA414](https://www.ti.com/lit/pdf/slla414), [SNVA021C / AN-1149](https://www.ti.com/lit/an/snva021c/snva021c.pdf), [SLMA002H](https://www.ti.com/lit/an/slma002h/slma002h.pdf) §2.4.

- SIG/GND/GND/SIG gives both outer layers a solid reference. SIG/GND/PWR/SIG routes more easily, but the B.Cu signals then reference a split power plane.
  - **Rev B keeps SIG/GND/PWR/SIG,** because the board needs the In2 power plane for VMOT, VBUS, 5 V and 3.3 V.
  - The fast signals sit on F.Cu over the solid In1 GND: USB 12 Mbit/s, I2S BCLK about 3 MHz, WS2812 800 kHz, the buck SW nodes.
  - B.Cu carries slow and DC signals, the buses and power feeds.
- Put stitching vias near every layer change of a signal.
- **Thermal vias:** about 0.3 mm drill on a 1.0–1.2 mm grid, tented or plugged under paste. Rev B puts 6 per DRV8874 pad, outside its 2.46 × 2.31 mm mask window, so they're tented.
- **Current capacity:** IPC-2221 for 15 A on 1 oz outer copper needs 8.3 mm at +20 °C, or 12.6 mm at +10 °C. Rev B runs the input chain on F.Cu and B.Cu in parallel, each at least 4.9 mm wide (≈9.8 mm total).
  - **New in rev B:** no foreign track may cross these pours. That's enforced as Freerouting keepouts, and the last-mile router may not cut them.
  - IPC-2152 (which an adjacent plane improves) is less conservative than 2221.

## JLCPCB DFM and assembly

Sources: [JLCPCB PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities); [PCBA capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities); [edge rails and fiducials](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order); [via filling](https://jlcpcb.com/blog/via-filling-guide).

- **Copper and drill:**
  - Multilayer 1 oz trace/space is 0.09/0.09 mm. Rev B rules: 0.15 mm clearance, 0.10 mm minimum track.
  - Minimum via is 0.15 mm hole / 0.25 mm diameter. Annular ring is 0.15 mm minimum, 0.20 recommended. Rev B uses 0.3/0.6 signal vias (0.15 ring) and 0.4/0.8 power vias (0.2 ring).
  - Hole to hole is 0.2 mm for vias and 0.45 mm for pads.
  - Copper to routed edge is at least 0.2 mm. Rev B rule: 0.3 mm.
- **Silkscreen:** line ≥ 0.15 mm, text ≥ 1.0 mm high, 0.15 mm from pads. Rev B rules: min text height 1.0, thickness 0.15.
- **Via-in-pad:** costs extra on 4-layer, and rev B uses none. Thermal vias sit outside the mask window, not in paste.
- **Fiducials and rails:** "Necessary" for Standard PCBA (1 mm copper, 2 mm mask opening, ≥ 3.35 mm from the edge). **Rev B has 3 board fiducials.** Edge rails can be added by JLC at order time.
- **Not published:** part-to-part and part-to-edge spacing. Rev B keeps courtyards apart and at least 0.4 mm from the edge.

## Connector fit in the v2 bay (Pip / v2 CAD, 18 Nov)

- **Problem:** in v2 the board's left edge (KiCad x = 0, the battery end) faces the robot's right side wall only 4.6 mm away. Rev A's right-angle XT60PW (battery) and XT30PW (switch loop) mate across that edge, and a mated XT60 with a 16 AWG bend needs about 35 mm. They can't be plugged in.
- **Rev B fix (option a):** both become an **Amass XT60PB-M.G.Y vertical PCB male** ([LCSC C19268037](https://www.lcsc.com/product-detail/C19268037.html)), mating toward the front wall, which has about 46 mm free (about 44 mm needed).
  - **Stock:** 17,051 at LCSC (live, 18 Nov). It's in the local JLC catalog as Extended (19,502).
  - **Rating (Amass datasheet):** 20 A per UL1977, under 60 °C rise at 20 A for 4 h, 500 V DC, pull-out 1.8–4.5 kg.
  - **Footprint:** the LCSC/EasyEDA footprint (two Ø4.5 mm plated holes on 7.2 mm pitch), via easyeda2kicad. Checked against the Amass drawing on 19 Nov: 7.20 mm pitch, 8.1 × 15.5/16 mm body, 16 mm tall, 3.0 mm solder tails. The drawing contradicts itself on the hole (Ø4.30 pins, but a Ø4.00 hole in the "mounting hole diagram"). The Ø4.5 drill is kept because it fits a 4.3 mm pin.
  - **3D model:** the EasyEDA STEP had its origin far off the pads, so the body rendered beside its holes. The footprint now uses KiCad's stock `AMASS_XT60-M_1x02_P7.2mm_Vertical.step` (offset x −3.6 mm, chamfer at pad 2). That stock footprint also uses a Ø4.5 drill.
  - **Fuse holder F101 (XF-506P, C492610), checked the same day:** four 0.50 × 1.90 mm slots, 3.70 mm within a pair, 4.30 mm between pairs, matching the footprint. The 0.3 mm terminals are rated 15 A per contact.
- **Why XT60 for the switch loop too:** the vertical XT30 (XT30UPB-M, C428721) is only rated 15 A, exactly the fuse value, while the XT60PB has margin. One part for both saves a BOM line and matches the v2 XT60 loop key.
- **Copper:** the input-chain pours and positions are unchanged. The 15 A target is now enforced with keepouts.
  - **Measured 19 Nov:** the VBAT_IN, VBAT_F and VSW pours join J101, J102 and F101 with a solid ring on F.Cu and B.Cu (zone connection full, about 18 mm of ring per XT60 pad per layer).
  - **The weak spot was J101's GND pad:** that pad carries the whole battery return, and it met the GND planes (F.Cu, B.Cu, In1) through four 0.5 mm thermal spokes per layer, only about 2 mm of neck per layer.
  - **Fix:** its spokes are now 1.5 mm (a pad override, also set in `gen/build_pcb.py`). That gives about 6 mm per layer and 18 mm in total, like the + side, and the pad stays hand-solderable.
- **Polarity (fixed 19 Nov):** the Amass drawing doesn't say which contact is +, but the XT-series convention (and the molded marks) put **+ on the square-corner end and − on the chamfered end**. Red goes to the flat side ([FlyMod connector FAQ](https://flymod.net/en/txt/power_connector_faq)).
  - **What was wrong:** the LCSC footprint draws the chamfer at pad 2, but rev B had pad 2 as + (copied from rev A's right-angle XT60PW, whose footprint has its own +/− silk). A standard battery lead would have put + on GND. The reverse-polarity FET would have blocked it, and the robot would never power up.
  - **Now:** the XT60PB-M symbol has pad 1 = + and pad 2 = −. J101 is rotated 180° with its nets swapped, so the copper stays exactly where it was and only the chamfer moves to the GND end. `gen/finish.py` places the +/− silk by net.
  - **J102:** a series loop, so its polarity doesn't matter.
  - **Before soldering:** still check the molded marks on the real part.
- **Other edge-facing parts to check against the v2 fit report:**
  - **J301 ESP32 USB-C:** right-angle, mates across the top edge at x ≈ 74, toward the Pi's bottom edge about 10 mm above. Fine for a short programming session with a straight plug; tight with the Pi installed.
  - **J103 PI 5V OUT USB-C:** right-angle at the top-right notch, toward the Pi's USB-C by design.
  - Everything else (JST-PH/SH/XH, servo headers, box header) is vertical and mates toward the front wall.
