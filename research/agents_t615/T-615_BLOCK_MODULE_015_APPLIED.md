# T-615: Q-80 applied, the 0.15 m black-block module 40 x 20 (12.5 / m2), and the held 0.15 m quantities restated

Worker 1, lane S, 2026-11-08. Non-candidate: no candidate line, no released line, the default rulebook reader
(`engine/source/company_rulebook_v1.py`, 1.0.0) unchanged. Files: `rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json`
(new version), `tools/m9_rules_manifest.py` (AUTHORED entry) + `rules/RULES_MANIFEST.json` (by its tool),
`research/agents_t615/*`, `tests/t615_block_module_015/*`, maps by the tool.

## 1. Physical element and rule

The 0.15 m solid black (cement) block as laid: 39 x 19 face + 10 mm bed and head joint = 40 x 20 installed module
(owner Q-80 2026-11-07: "40x20 face, 12.5 blocks/m2"; joint owner 2026-10-29), in the 15 carried 0.15 m walls of
T-520 / T-506 / T-533 (GF-W22 D-27 and 2F-W08 D-39 stay HELD on their own area causes). Rule version:
**UPC-BLACK-BLOCK-001 1.1.0** in rulebook 1.1.0 (supersedes 1.0.0; the other nine records are byte-equal, tested):
`confirmed_modules_m` = {0.15: 40 x 20, 0.20: 40 x 20}; any other thickness is not stated (HELD, never borrowed);
a printed different 15 cm face is reported to the owner, never an override (the owner's Q-80 condition).

## 2. Drawing search (Q-80 condition: "tell me if the drawings show otherwise")

Searched this run: ST7757 dxf.dxf (2,553 strings incl. the Arabic notes in the keyboard-mapped xarb font, decoded;
49 layers; every hatch; 39 block names), the architectural DXF of P7757_DXF_COMPRESSED.zip (675 strings, 19 layers,
hatches, 47 block names), and the text layers of ST7757.pdf / sanitary-7757.pdf (none beyond sheet dates).

| Drawing | Handle | What it is | Verdict |
|---|---|---|---|
| ST7757 | B8 (S-NOTE) | note: black block walls built from foundation level at the neighbour-side perimeter; no size | NO FACE |
| ST7757 | 7FD / 7FB / 80F (S-HAT.BAT) | AR-B816C / AR-B816 hatches on 200 mm strips (U-shape 31.37 x 8.30 m; 0.2 x 1.15; 1.2 x 0.2) on the ground-level column plan: 0.20 m walls in plan; the library pattern cell 240 x 120 mm at scale 15 is graphic | 0.20 m WALL, NO FACE |
| ST7757 | 7D (S-NOTE) | slab 16 cm unless stated | NOT A BLOCK |
| ST7757 | block '816' (insert 537) | a slab bar label, not a masonry unit | NOT A BLOCK |
| P7757 arch DXF | all | no block product / size / joint text, no masonry hatch | SILENT |

Result: **no drawing prints a 15 cm (or any) block face; nothing differs from 40 x 20; nothing to report to the
owner.** Not re-read this run: the architectural PDF sheets (prints of the DXF searched).

## 3. Restated quantities (15 walls; before: HELD by name in T-533)

| Item | Unit | Now (low .. figure / high) | Hand check |
|---|---|---|---|
| Units, theoretical | nr | 2,194.14 .. 2,198.39 | 175.871 x 12.5 = 2,198.3875; low takes the HELD D-1F-09 lintel face 0.34 m2 out |
| Units, procurement | nr | HELD | ceil(theoretical x (1 + waste)); waste not sourced |
| Panel joint mortar | m3 | 1.941812 .. 1.945573 | 175.871 x 0.15 x (1 - 0.39 x 0.19 / 0.08) = 175.871 x 0.0110625 |
| Panel, contract area | m3 | 1.975442 | = T-367 pinned 1.975440 (per-wall rounding) |
| Perimeter joint mortar | m3 | 0.078582 .. 0.079138 / 0.089890 | R-T520-1 re-run on the register module (= T-520 on 40 x 20) |
| Cement (panel + perimeter) | bags 50 kg | 16.16 .. 16.20 / 16.28 | x 8 (UPC-BLACK-MORTAR-001); rounded up only at the purchasing group |
| Sand, loose | m3 | 2.222 .. 2.227 / 2.239 | x 1.1 |

Board text reconciled: "2,198" is the truncated 175.9 x 12.5 = 2,198.75; on the unrounded base it is 2,198.3875
(-0.3625 nr, area rounding only). "1.946 m3" = 1.945573. "16.3 bags" = the high end 16.28 to one decimal.
The perimeter range is R-T520-1's own: a block-to-block junction may be butt-jointed or bonded (no junction detail
printed) and dome-opening pieces of 1F-W13 / 1F-W17 / 1F-W24 stay HELD by name inside T-520.

## 4. Accessories (T-539 ledger V2 re-run on the 1.1.0 register; T-539 asserts every count = T-355 PRIMARY)

- Sharmat ties: **+12 end** (1F-W23 e0 6, 2F-W08 e0 6; 2F-W08 D-39 top 3.75 .. 3.85 m gives 6 .. 6) **+ 49 interior**
  (8 junctions: GF-W26, GF-W28 x2, GF-W32, 1F-W14+15, 1F-W20, 1F-W23 x2) -> ledger 151 -> **212 pcs measured**;
  94 junctions stay HELD on other causes (white AAC 69, lift tie beam 11, top unknown 9, annex 4, partial column 1).
- Bed-joint strip: **+367.9895 m.l on 25 0.15 m walls** -> ledger 175.4844 -> **543.4739 m.l**.

## 5. Fix rows for the manifest (FR-T615-n), statuses

FR-T615-1 units, -2 panel mortar, -3 perimeter mortar, -4 cement / sand, -5 ties, -6 strip (all
ASSUMED - OWNER-APPROVED: owner company rule, not printed), -7 drawing check (no face printed). Every wall row keeps its
area status beside (VERIFIED / DRAWING-CONFIRMED / ASSUMED - OWNER-APPROVED). Freelancer: blockwork in m2 only (T-176),
no units / mortar / ties to compare -> verdict UNRESOLVED (no comparison possible).

## 6. Tests and lesson

`tests/t615_block_module_015`: fixture (6.00 x 3.00 wall less a 1.20 x 1.00 window = 210 units, 0.18585 m3; course
layout 4.00 x 2.40 = 120 units; rotation invariance; ties 6 .. 6 on 3.75 .. 3.85) + adverse (1.0.0 register never lends
0.20 to 0.15; 0.25 unstated HELD; a printed 39 x 24 face with the owner entry = CONFLICT, no override; HELD record with 0
refused; mm refused; module guard) + Alsenan pins (reproduce, T-533 untouched, S-A equality, accessories).
Proposed lessons-register row: "A module answered for one thickness was applied by restating every quantity held on it
through the merged builders, not by scaling the what-if | a held datum resolved by the owner | the answer becomes one
rule version; the held builders re-run on it and assert equality with the earlier what-if (every villa) |
tests/t615_block_module_015 | PROPOSED".
