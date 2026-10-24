# T-219 Foundation and lift-pit waterproofing as BOQ lines (development villa; rule for every villa)

Worker 2 (lane A), 2026-10-24, run session_01U7tq7Qh7EqUy5oAXQndZX6. Research ledger + unwired rules module
(FOUNDATION_WP_V1, stdlib), NOT wired into any method version: released ARCH_TAKEOFF_V2.9 + route G and the V3.0.x
candidate are unchanged; nothing released. Drawings named by Drive folder and title; entities by DXF handle; values only.
ERS applied: s.2 steps 1-4 (element first, evidence hierarchy, first principles, reconciliation in units), s.3
(installed vs procurement; build before deduct; geometric scope before numbers), s.4 (rule + test), s.7 (lesson row).

Files: `foundation_wp_v1.py` (rules), `t219_alsenan_check.py` (runner), `ALSENAN_T219_INPUT.json` (values),
`LEDGER_T219.csv` (one row per outline and component), `summary.json`; tests `tests/t219_foundation_wp` (25).
Repeat: `python3 -I research/agents_t219/t219_alsenan_check.py [--write]`.

## 0. Gap re-checked on the current candidate (lesson 2026-10-24, T-255)

Working head dadf8446 (candidate ARCH_TAKEOFF_V3.0.11 merged): no item code for a footing / foundation membrane, a
footing screed, a liquid coating of buried concrete or a lift-pit membrane / board / screed exists in engine/source
(the only WP codes are FIN.WP.FLOOR / DOORWAY / UPTURN / WALL_UPTURN / DOORWAY_TRANSITION(_NR) / TERMINATION /
PENETRATION / MEMBRANE_ROLLS / ROOF / ROOF_UPTURN / BALCONY / THRESHOLD / DETAILING: wet areas, roofs, balconies).
BOQ family B8-08 'Foundations / basement / below-grade' is NOT_IMPLEMENTED in BOQ_FAMILY_MASTER_1.6.0; B3-05 screed has
no line. The gap stands: a drawn scope with no BOQ line in any state.

## 1. Sources read this run (private copies in .work/private only, never committed)

| Source (Drive "Alsenan chalet project") | Read for |
|---|---|
| ST7757.pdf (2,219,156 bytes) p.13 at 110 / 300 dpi | both 'TYP. DETAIL OF ISOLATED FOOTING' details: the underlay chain, the extent of membrane and screed, the side treatment, the 'two layers liquid water proofing' note |
| ST7757.pdf p.14 at 110 / 300 dpi | 'DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)': membrane, protection board, screed, pit depth note |
| ST7757 dxf.dxf (sha 9f9d1179, = T-233 manifest) | FF 1B2B, pit ring 10EB / 10EA, lift columns 1090 (C9) / 1099 / 1093 / 1096 |
| research/agents_t233/ALSENAN_FOOTING_INPUT.json | the 26 footing outlines (T-233 MERGED 2ecb5bf0; Checker 20:14 re-measured all 26: reused with that citation) |
| T-206 (MERGED d5df7d1f), T-204 (MERGED 4fbf7627), T-174, T-230 (MERGED 17ed6f92) | chain 5 / 2 / 10 VERIFIED; lift components; strap sections and angles; strap level not printed |
| tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json | every freelancer row (6 workbooks) |

## 2. The physical elements (ERS s.2.1)

Printed on p.13 under every isolated footing, in BOTH typical details (the detail is chosen by 'the level difference
between upper ground beam and footing' more / less than 2.5 m), from the footing down: **5 cm screed / waterproofing
membrane (dimensioned 2, i.e. 2 cm) / 10 cm plain concrete**. Read again this run at 300 dpi (right detail): the
screed and the membrane end exactly at the footing faces; only the blinding projects ('10 | L x W | 10'). So:

| Component | Plan / height | Unit | Owner trade | Both details agree? |
|---|---|---|---|---|
| Membrane under the footing | the drawn footing outline (L x W) | m2 installed, one layer | WATERPROOFING | yes |
| Protection screed over it (5 cm) | the drawn outline x 0.05 | m2 and m3 | WATERPROOFING (protection) | yes |
| Blinding 10 cm | outline + 0.10 each side | m3 | STRUCTURE (existing CONC.BLINDING 14.990 + held): never here | - |
| Footing side faces | perimeter x height | m2 | WATERPROOFING | NO: right detail (< 2.5 m) = 'Two layers liquid water proofing ... all surface in contact with earth' on perimeter x H; left detail (> 2.5 m) = the 'Insulation membrane' wrapped down the sides to the blinding, perimeter x (H + 0.05 + 0.02) |
| Upturn 0.20 (owner UP-WP-003) | - | - | - | NOT APPLICABLE: UP-WP-003 is scoped to wet areas, balconies, terraces, roofs; the footing sides are covered only by the printed detail readings above |
| Procurement (rolls, laps; liquid coats / kg) | - | rolls / kg | - | product / system NOT PRINTED -> HELD (UP-WP-MAT-001; rolls only by UP-WP-001 / -002 / -005 / UP-WP-LAY-001 for a printed sheet product) |

OWNER MANUAL METHOD vs DRAWING-DERIVED METHOD (ERS s.2.2): the owner's membrane method (1 x 10 m roll, 0.10 lap, 0.20
upturn, Q-49 A per area alone) is written for wet areas and roofs; no owner method covers foundations (family B8-08).
Here only the drawing-derived method applies; it is NOT extended to footings by assumption (procurement HELD).

Lift pit (p.14, FF base): membrane under the 5 cm screed (base area), up the base and screed sides, across the base
top outside the pit walls, up the OUTER faces of the pit walls; protection board on the sides, the top outside the walls
and the walls (none under the base); screed under the base. Pit depth 'As Per Lift Manufactures recommendations':
every wall part HELD. The p.13 '2 cm' is not carried to p.14 (ERS s.3): it changes no area, only the level chain.

## 3. Ledger (LEDGER_T219.csv; each outline once)

| Type | n | Outline each (m2) | Membrane m2 | Screed m2 / m3 | Side single (liquid, P x H) | Side double (sheet, P x (H + 0.07)) |
|---|---|---|---|---|---|---|
| F | 4 | 0.72 | 2.88 | 2.88 / 0.144 | 4.08 | 5.032 |
| F2 | 2 | 3.23 | 6.46 | 6.46 / 0.323 | 5.04 | 6.048 |
| F3 | 2 | 2.24 | 4.48 | 4.48 / 0.224 | 3.6 - 0.160 (SB3, level HELD) | 4.44 - 0.198 |
| F4 | 2 | 4.40 | 8.80 | 8.80 / 0.440 | 6.72 | 7.896 |
| F5 | 2 | 5.04 | 10.08 | 10.08 / 0.504 | 7.20 | 8.46 |
| F6 | 1 | 5.72 | 5.72 | 5.72 / 0.286 | 4.80 - 0.510 (SB2) | 5.472 - 0.510 |
| F8 | 1 | 14.40 | 14.40 | 14.40 / 0.720 | 7.60 - 0.350 (SB1) | 8.664 - 0.350 |
| F9 | 1 | 9.18 | 9.18 | 9.18 / 0.459 | 6.71 - 0.225 (FN clip) | 7.564 - 0.225 |
| F11 | 1 | 5.25 | 5.25 | 5.25 / 0.2625 | 5.00 - 0.510 (SB2) | 5.70 - 0.510 |
| F12 | 1 | 14.08 | 14.08 | 14.08 / 0.704 | 10.64 | 11.704 |
| F13 | 1 | 10.32 | 10.32 | 10.32 / 0.516 | 6.70 | 7.638 |
| F14 | 1 | 12.54 | 12.54 | 12.54 / 0.627 | 7.10 | 8.094 |
| F15 | 1 | 1.80 | 1.80 | 1.80 / 0.090 | 2.24 - 0.214 (SB3) | 2.632 - 0.214 |
| FN | 4 | 3 x 1.00 + 0.86 (180C clipped where F9 lies) | 3.86 | 3.86 / 0.193 | 4.80 - 0.225 (clip) | 5.92 - 0.225 |
| **measured, 24 outlines** | | | **109.85 DRAWING-CONFIRMED** | **109.85 / 5.4925 DRAWING-CONFIRMED** | **80.037 (gross 82.23)** | **93.034 (gross 95.264)** |
| F10 + F (1B1B, one outline, two tags) | 1 | outline 3.25 x 1.40 = 4.55; rows 3.92 + 0.72 = 4.64 | HELD 4.55 .. 4.64 | HELD 4.55 .. 4.64 / 0.2275 .. 0.232 | HELD (no depth: Q-31 C) | HELD |
| FF lift base (1B2B) | 1 | 20.70 | see the lift table | 20.70 / 1.035 | (lift table) | |

Side faces: the whole line is **HELD** (detail selection waits on the formation level, owner Q-21 C; T-206: the
single-beam detail holds unless the formation lies below about -1.67), shown as both readings, never one picked, never
0. Deductions (faces against concrete, not earth): FN 180C / F9 180F clip 0.75 m x 0.30 on each (DRAWING-CONFIRMED,
one bottom stack); strap ends at e = 0 (strap level NOT printed, T-230): SB1 0.70 x 0.50; SB2 1.00 / cos 11.08 deg =
1.019 m x 0.50 at F11 and F6 (width D-38: 0.80 under the off-sheet row); SB3 0.50 / cos 20.57 deg = 0.534 m x 0.40 at
F15 and x 0.30 at F3 (level range HELD). Strap underlay: none printed under straps (D-15): HELD, not measured.

Lift pit LIFT-01 (own DXF read: FF 4.600 x 4.500; ring 2.200 x 2.200; C9 0.250 x 1.000 proud of the ring by 0.050 over
1.000 m -> pit envelope 4.890 m2, perimeter 8.900 m):

| Component | Hand calculation | Result | Status |
|---|---|---|---|
| Membrane, fixed | soffit 20.700 + sides 18.20 x (0.55 + 0.05) = 10.920 + top outside the envelope 20.700 - 4.890 = 15.810 | **47.430 m2** | DRAWING-CONFIRMED (= T-204, re-derived from the drawing this run: 0.000) |
| Membrane, pit walls | 8.900 m x pit height | HELD (8.900 m2 per m) | HELD: pit depth to the lift maker (D-43) |
| Protection board, fixed | 10.920 + 15.810 | **26.730 m2** | DRAWING-CONFIRMED |
| Protection board, walls | 8.900 m x pit height | HELD | HELD |
| Screed under the base | 20.700 m2 x 0.05 | **20.700 m2 / 1.035 m3** | DRAWING-CONFIRMED |

Cross-check against the Checker-verified blinding (T-233): the 25 measured outlines grown 0.10 =
sum(A) 109.85 + 20.70 + 0.10 x sum(P) (186.2 + 18.2) + 25 x 0.04 = **151.990 m2**, exactly T-233's blinding plan sum: the
membrane plans are the same verified outlines, with the projection on the blinding side only.

## 4. Engine vs freelancer (units first)

| Item | Drawing (this task) | Released A (V2.9 + G) | Candidate V3.0.11 | Freelancer | Difference and cause |
|---|---|---|---|---|---|
| Footing membrane | 109.85 m2 + HELD 4.55 .. 4.64 | no line | no line | no row | engine and freelancer both silent on a drawn scope: -109.85 m2 each (missing category) |
| Footing protection screed | 109.85 m2 / 5.4925 m3 + HELD 0.2275 .. 0.232 m3 | no line | no line | no row | same: -5.4925 m3 |
| Footing side waterproofing | HELD: 80.04 (liquid) .. 93.03 (sheet) m2 + 1B1B | no line | no line | no row | same, held by detail selection |
| Lift-pit membrane / board / screed | 47.43 m2 / 26.73 m2 / 1.035 m3 + walls HELD | no line | no line | no row | same |
| Blinding (STRUCTURE, for scope only) | 14.990 m3 + HELD (T-233) | BOUNDED | 15.179 PROVISIONAL | 47.055 m3 plate | not this line: never double counted with the underlay |

His waterproofing is wet areas 72.01 m2 + 144.61 lm and roofs 285 m2 + 194 lm only; he prices none of the foundation
underlay. Verdict proposals: membrane, screed, lift fixed parts: **DRAWING scope missing in BOTH; freelancer omission
(FREELANCER_WRONG on scope)**, engine silent omission to be integrated (lane I); side faces UNRESOLVED (detail selection,
Q-21 C); procurement UNRESOLVED (product not printed: designer item).

## 5. Found scope NOT measured here (follow-up)

The right p.13 detail prints 'Two layers liquid water proofing to be applied to ALL surface in contact with earth' and
draws it on the footing top and the neck as well. Beyond the footing sides (above), this covers the footing tops outside
the necks, the necks, the strap sides, the ground-beam sides / soffits on fill, and the boundary band: no line in any
state, freelancer no row. Most of it depends on the formation / ground-beam levels (HELD) and the neck sections (T-205,
4 with SECTION_CONFLICT). Proposed Lead row: 'Liquid waterproofing of buried concrete (p.13 note): footing tops less
neck sections, necks, straps, ground beams, band; per member face, heights from the level chain, HELD where unprinted'.

Designer / consultant items proposed (no owner question: ERS 2.7 not met, the drawings leave these to the designer):
(1) membrane product under footings and pit (sheet / liquid / thickness 2 cm what?) and laps; (2) the liquid coating
system and coats; (3) existing: formation level (Q-21 C) decides the side detail; pit depth (D-43); straps underlay (D-15).

## 6. Rule, test, lessons row

Rule proposed (every villa; provenance T-219 from ST p.13 / p.14 of this set; a new rule version when adopted,
R-WP-FOUND-1): the underlay printed under a footing is measured on the drawn footing outline (installed = outline,
one layer; screed m2 and m3), never on the blinding's projection; a two-tag outline is HELD with both readings; side
faces follow the governing detail (liquid on P x H vs sheet on P x (H + underlay)); while the level that selects the
detail is unprinted both readings are shown and the line is HELD; faces against other concrete are deducted; no 0.20
upturn on footings (UP-WP-003 scope); procurement only for a printed sheet product by the owner's layout rules, else
HELD; a lift pit's membrane / board / screed by component, wall parts HELD without the pit depth.
Tests: tests/t219_foundation_wp (villa U by hand: 3 types incl. a one-owner clip, lift pit with and without a printed
height; adverse: blinding counted as membrane refused, a wider extent refused, upturn refused, two tags HELD, nothing
printed HELD, pit walls without depth HELD never 0, envelope outside base refused, rotation 30 deg / mirror / shift /
mm identical, undeclared unit and mm-as-m refused; Alsenan ledger pinned, consistent with the verified blinding plan).

Lessons row proposed: 2026-10-24 | Foundation underlay (membrane 109.85 m2, screed 5.49 m3) and lift-pit membrane /
board / screed drawn on ST p.13 / p.14 had no BOQ line in any state and no freelancer row | The printed underlay chain
was read only as a level (T-206) and the lift detail as concrete (T-204); no trade owned the layers between blinding and
footing | A layer drawn between two structural elements is an element of its own trade with its own line; register it
when the chain is read, measure it on the element's outline (not the blinding's), and keep detail-dependent faces HELD
with both readings (any villa) | tests/t219_foundation_wp (adverse: blinding area as membrane, invented upturn, pit wall
without depth) | PROPOSED.

## 7. Not done / uncertain

- Not integrated (lane I package: new item codes WP.FOOTING_MEMBRANE, SCREED.FOOTING_PROTECTION, WP.FOOTING_SIDES,
  WP.LIFT_PIT_*; family B8-08 / B3-05 states in the next family master).
- The freelancer's original waterproofing workbook (23.6 MB) was not re-opened; the committed parsed rows were searched.
- Checker re-measure list: FF 1B2B 4.600 x 4.500 and ring 10EB 2.200 x 2.200 + C9 1090 (envelope 4.890 / 8.900);
  F12 1ABF 4.40 x 3.20 = 14.08 and F9 180F 3.40 x 2.70 = 9.18 (+ FN 180C notch 0.40 x 0.35); p.13 right detail:
  screed / membrane ending at the footing faces; p.13 left detail: membrane down the sides.
