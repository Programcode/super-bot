# Main board quotes: rev A vs rev B

Fab + assembly + parts + shipping to Hungary, for 2 and 5 assembled boards. Collected 18 Nov 2026 (07:00–07:40 UTC). **Nothing was ordered,** and no account was logged in or created. Adam's purchasing bot does the buying.

## Recommendation

**Order rev B from JLCPCB with Economic assembly.**
- **Qty 2:** about **€179 excl. VAT / €227 incl. 27 % VAT**.
- **Qty 5:** about **€261 / €332**, about €66 per board including VAT.
- **Why 5:** the fixed costs (PCB setup, stencil, part fees, shipping) are about €110 whatever the quantity. Qty 5 costs only about €80 more than qty 2 and gives three spare boards (useful for a second robot or a mistake while hand-soldering).
- **Why not PCBWay:** for this board it is 3–4 × more. Its live assembly calculator charges about $490–$605 for the assembly alone, mostly a fixed cost. The "$29 PCBA" headline only appears with blank part counts, and with the real counts the calculator gave the figures below. That held even for rev B at qty 2, which meets the conditions Adam cited (≤ 200 parts per board, ≤ 600 total, ≤ 100 unique, no THT): 196 parts, 392 total, 58 unique, 0 THT.
- **Rev B vs rev A:** rev B is cheaper. It has 9 fewer Extended part fees ($3.07 each on Economic), no through-hole assembly (you hand-solder 11 connectors, a €3–8 kit), and cheaper parts. It's also the better board (see `rev-b/README.md`).

## Table (EUR, USD × 0.92)

| Option | Qty | Fab | Parts | Assembly | Part fees | Shipping | **Total excl. VAT** | **Total incl. 27 % VAT** | Per board incl. VAT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rev B, JLC Economic | 2 | 35 | 57 | 11 | 51 | 25 | **179** | **227** | 114 |
| Rev B, JLC Economic | 5 | 35 | 136 | 14 | 51 | 25 | **261** | **332** | 66 |
| Rev A, JLC Economic | 2 | 35 | 60 | 17 | 76 | 25 | **213** | **271** | 136 |
| Rev A, JLC Economic | 5 | 35 | 145 | 23 | 76 | 25 | **304** | **386** | 77 |
| Rev B, JLC Standard | 2 | 36 | 57 | 33 | 82 | 25 | **233** | **296** | 148 |
| Rev B, JLC Standard | 5 | 36 | 136 | 36 | 82 | 25 | **316** | **401** | 80 |
| Rev A, JLC Standard | 2 | 36 | 60 | 39 | 91 | 25 | **252** | **320** | 160 |
| Rev A, JLC Standard | 5 | 36 | 145 | 46 | 91 | 25 | **343** | **436** | 87 |
| Rev B, PCBWay turnkey | 2 | 81 | 57 | 452 | 0 | 3 | **592** | **752** | 376 |
| Rev B, PCBWay turnkey | 5 | 81 | 136 | 471 | 0 | 3 | **691** | **878** | 176 |
| Rev A, PCBWay turnkey | 2 | 81 | 60 | 513 | 0 | 3 | **657** | **834** | 417 |
| Rev A, PCBWay turnkey | 5 | 81 | 145 | 557 | 0 | 3 | **785** | **997** | 199 |

The VAT column is 27 % on the whole order. JLC's DDP checkout also prepays about €5 of EU handling/duty fees (€3 per HS code + €2), which isn't in the table. PCBs and PCBAs usually carry 0 % customs duty. Check the final number at checkout.

## Where each number comes from

| Item | Source | Type |
| --- | --- | --- |
| JLC PCB, 5 pcs, 186 × 70 mm, 4-layer 1.6 mm, LF-HASL, 1/0.5 oz: **$38.40** ($25 engineering + $8.10 board + $5.30 finish) | [cart.jlcpcb.com/quote](https://cart.jlcpcb.com/quote), Gerber uploaded without login | **Live quote** |
| JLC PCB with Standard-assembly edge rails (186 × 80): $39.60 | same page | **Live quote** |
| JLC shipping to HU, PCB-only weight: DHL $23.52 (2–5 days), EuroPacket $13.34, Global Standard $8.28 | same page | **Live quote.** The table uses **$27**, an estimate for the heavier assembled boards |
| JLC assembly fees, Economic: setup $8.18, stencil $1.53, $0.0016/SMT joint, $0.0164/THT joint + $3.58 hand-solder labor, **$3.07 per unique Extended part** (Basic and Preferred free) | [jlcpcb.com/help/article/pcb-assembly-price](https://jlcpcb.com/help/article/pcb-assembly-price) (updated 22 Oct 2026) | Published fee table. The assembly quote itself needs a login |
| JLC Standard: setup $25.56, stencil $8.21, $1.53 per unique part (all), +$0.50 packing | same page | Published fee table |
| Parts at LCSC/JLC prices for 2 and 5 sets | local JLC catalog snapshot + live LCSC API for the ESP32 module, `gen/cost.py` (rev A) and `rev-b/gen/cost.py` | Computed per BOM line |
| PCBWay PCB, 5 pcs, same spec (1 oz inner; no 0.5 oz option): **$87.71** | [pcbway.com/orderonline.aspx](https://www.pcbway.com/orderonline.aspx) | **Live quote** |
| PCBWay assembly: rev A $557.61 (qty 2) / $605.28 (qty 5); rev B $491.17 / $511.97 | [pcbway.com/quotesmt.aspx](https://www.pcbway.com/quotesmt.aspx) | **Live calculator.** The final price is "subject to review" after upload, which needs a login |
| PCBWay shipping to HU (assembled): DHL $33.16 minus the $30 freight deduction | live checkout estimate | **Live quote** |

Screenshots of every page above are kept on the VPS at `/tmp/quotes/` (not committed).

## Assumptions and risks

- **Login-gated:** JLC's real assembly total, including its part-availability check, needs a login. The Economic numbers are the published fees applied to our BOM: rev A has 675 SMT + 82 THT joints per board and 27 Extended parts; rev B has 655 SMT joints, 0 THT and 18 Extended parts.
- **Unexplained fee:** JLC's fee page also lists "pre-reflow soldering $0.016/joint", and it's unclear when that applies. If it applied to every SMT joint it would add about $21 (qty 2) or $52 (qty 5).
- **Part prices:** LCSC unit prices at the order quantity. JLC may add a few spares (attrition) on small passives, worth cents.
- **Vias:** JLC's quote page set "Plugged" vias automatically for this 4-layer board ("Tented" was greyed out). That's fine for this design.
- **Rev B hand-solder kit:** the XT60 ×2, fuse holder, 2 × 20 box header, 4 × JST-XH and 2 servo headers cost $3.19 (2 sets) or $7.98 (5 sets) at LCSC. That's included in the parts column. Ordered separately from LCSC, they add LCSC's own shipping (about €10–20), unless you add them to the JLC order as loose parts or buy them locally.
- **PCBWay parts:** PCBWay sources its own parts. The table uses the LCSC price as a stand-in, and the real figure is probably higher.

## How to reproduce

- `python3 gen/cost.py 5` (rev A) and `python3 rev-b/gen/cost.py 5` (rev B) print the BOM pricing.
- The fee arithmetic is in the table above.
