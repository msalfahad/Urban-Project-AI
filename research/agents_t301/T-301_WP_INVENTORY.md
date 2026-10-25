# T-301: the waterproofing scope inventory per WP family (F-REC-02), WP.FOUNDATION first

Worker 2 (lane A), claim 2026-10-25 16:45 UTC, run session_01PaZobx5HDeZfMySZff4V7U. Owner 2026-10-25 11:51 (0); Verifier
11:28 F-REC-02 ("no waterproofing inventory, so no WP line can read WHOLE"). Read-only: no candidate line, quantity,
state or V2.9 cell moves. Drawings named by Drive folder and title only ("Alsenan chalet project": P7757.dxf from
P7757_DXF_COMPRESSED.zip `ab54dd55`, "ST7757 dxf.dxf" `9f9d1179`).

## 1. The physical question (ERS s.2.1)

Which faces does each WP family cover, and is every one either carried by a candidate line or NOT_APPLICABLE with
evidence? An inventory element is ONE face of ONE drawn element for ONE item code and unit (the membrane under a footing
and its 5 cm protection screed are two items on the same underside; screed m2 and m3 are two rows; the lift pit has four
faces per item). Elements come from the merged, Checker-verified censuses of the drawn elements, never from the engine's
lines:

| Elements | Source (merged, Checker) | Count |
|---|---|---|
| footing undersides / sides / tops | T-233 drawn outlines (2ecb5bf0, all 26 re-measured 2026-10-23 20:14); presence cross-checked with T-219 (26 = 26) | 26 outlines |
| lift pit LIFT-01 | outline 1B2B FF + ST7757.pdf p.14 lift detail (T-219 de7c1c4c, Verifier 10:40 own read) | 4 faces |
| buried ground-beam faces | T-276 r2 trace, every buried face once (4d88681b, Verifier 22:54) | 175 faces |
| necks below the beam zone | T-263 neck rows; presence cross-checked with the T-217 neck census (36 DRAWN = 36) | 36 necks |
| GB soffits, ground slab, boundary G.B., straps, pit walls | T-263 (c0ab564d, Verifier 17:59) | 59 + 1 + 2 + 1 + 1 |

Statuses: IN_LINE (line id + state; a held line holds the face BLANK), NOT_APPLICABLE (sheet + ref / handle; e.g. a face
whose soffit is at / above the natural ground, a soffit cast on the printed blinding, a face the p.14 lift system owns),
MISSING (no line: an omission, blank, never 0).

## 2. Result on the candidate of record ARCH_TAKEOFF_V3.0.17

Own run this session (Python 3.11.17, research/agents_t167/v304_run.py then research/agents_t254/v3017_run.py on the
Drive copies): V3.0.16 canonical lines 3181cf12 and V3.0.17 366be2f8 (3,700 lines) REPRODUCED (= the Verifier's record
binding). T-266 (V3.0.18) is READY, not merged: the line ids below are V3.0.17's. 19 WP.FOUNDATION lines extracted
(CANDIDATE_V3017_WP.json: ids, codes, states, quantities, component ids only).

**416 inventory elements: IN_LINE 320, NOT_APPLICABLE 96, MISSING 0; register-only line keys 0; unlinked lines 0.**

| Item (unit) | Elements | In line: qty / held | NA (evidence) | Missing | Inventory m2 (in line) | Line | Residual | Whole countable |
|---|---|---|---|---|---|---|---|---|
| FOOTING_MEMBRANE m2 | 26 | 24 / 1 (1B1B two tags) | 1 (1B2B: p.14 lift system) | 0 | 109.850 (24 T-233 areas) | 109.850 | 0.000 | no: 1B1B held |
| FOOTING_SCREED m2 | 26 | 24 / 1 | 1 | 0 | 109.850 | 109.850 | 0.000 | no |
| FOOTING_SCREED m3 | 26 | 24 / 1 | 1 | 0 | 5.4925 (area x 0.05 printed) | 5.4925 | 0.000 | no |
| FOOTING_SIDES m2 | 26 | 0 / 25 (detail Q-21 C) | 1 (pit membrane owns 1B2B sides) | 0 | blank | blank | n/a | no |
| LIFT_PIT_MEMBRANE m2 | 4 | 3 / 1 (walls, D-43) | 0 | 0 | 47.430 (20.700 + 10.920 + 15.810) | 47.430 | 0.000 | no: walls held |
| LIFT_PIT_BOARD m2 | 4 | 2 / 1 | 1 (no board under the base) | 0 | 26.730 | 26.730 | 0.000 | no |
| LIFT_PIT_SCREED m2 / m3 | 1 / 1 | 1 / 0 | 0 | 0 | 20.700 / 1.035 | 20.700 / 1.035 | 0.000 | **yes** |
| BURIED_LIQUID m2 | 301 | 32 / 178 (118 GB faces, 25 tops, 32 necks, 3 boundary / straps) | 91 (17 above N.G., 8 lift ring, 1 FF top, 4 lift necks, 59 soffits on blinding, slab soffit, pit walls) | 0 | 45.4682 (32 T-276 faces) | 45.4682 | 0.000 | no |
| PROCUREMENT item | 1 | 0 / 1 | 0 | 0 | blank | blank | n/a | no |

T-236 schema (to_t236 -> engine/source/trade_completeness_v1.check): WATERPROOFING on storey FDN
COMPLETE_AGAINST_INVENTORY, found 320, measured 111, held 209, missing 0, excluded 96.

The whole / component reading agrees with every Verifier V2 record on V3.0.17: LIFT_PIT_SCREED m2 / m3 WHOLE (the item's
only face, released); footing membrane, screed m2 / m3, pit membrane, pit board COMPONENT (the same item holds a face
blank). So the 2 WHOLE records can now count as whole verified lines once the export join reads this inventory (T-298
side, lane I); the 5 COMPONENT records stay components until their held faces are resolved (1B1B Q-31 C, pit depth D-43).

Engine vs freelancer: unchanged by this task (no quantity moves); the freelancer has no foundation waterproofing rows
(FREELANCER_WRONG on scope, Checker T-219 / T-263).

## 3. Other WP families (named; no inventory built in this run)

| Family | Candidate lines (V3.0.17) | Inventory still to build from |
|---|---|---|
| WP.WET_AREA | FIN.WP.FLOOR 18 (15 SD + 3 PROV), WALL_UPTURN 18, DOORWAY 14, DOORWAY_TRANSITION 13 (bounded), TRANSITION_NR 14, PENETRATION 17 (held), TERMINATION 7 (bounded), MEMBRANE_ROLLS 22 | the T-209 wet-room set (rooms by printed label, each floor face + upturn run + doorway) |
| WP.ROOF | FIN.WP.ROOF 4, ROOF_UPTURN 4 | roof planes per roof slab plan (Q-24 / Q-34), parapet upturn runs, dome rings |
| WP.POOL_TANK | none in the candidate | the pool / tank details (T-191 / T-193 elements): whether the drawings print a WP layer is not established here |

Until these exist no wet-area or roof WP line can count WHOLE (the family has no inventory: ERS lesson 2026-10-25).

## 4. Rule, tests, files

Rule R-T301-WP-INVENTORY-1 (PROJECT-INDEPENDENT; research rule from ERS s.2.1 / s.3 + Verifier 11:28 F-REC-02, not a
rule-file version): a waterproofing family's completeness is read against an inventory of drawn faces (one element per
item code, unit, element and face); every face is IN_LINE, NOT_APPLICABLE with sheet + ref, or MISSING (blank); a face in
two lines of one item / unit is refused; a quantity line counts WHOLE only when no face of its item is held or missing
and the inventory closes on it to 0.000.

Files: research/agents_t301/t301_wp_inventory.py (core, stdlib), t301_alsenan.py (adapter, --extract), CANDIDATE_V3017_WP.json,
WP_FOUNDATION_INVENTORY_T301.csv, WP_FOUNDATION_REPORT_T301.json; tests/t301_wp_inventory (villa V-301 by hand: normal +
adverse: face in two lines, NA without evidence, missing as 0, NA carried by a line, wrong item / unit, register-only +
residual, T-236 GAPS; development villa pinned to the committed extract and the Verifier records).

Residual risk: the 32 released buried faces have one source (T-276); their inventory m2 and the line come from the same
trace, so that residual checks transcription only (the footing m2 residual is against T-233 areas, a separate census).
The three boundary / strap elements are T-263's rows (one row for SB1 / SB2 / SB3): held, so no quantity depends on how
they are split.

Lessons-register row (proposed, ERS s.7): 2026-10-25 | 7 WP lines with V2 records could not count WHOLE | no family had a
face inventory, so 'whole' could not be told from 'component' | a family's whole line is read against a drawn-face
inventory (IN_LINE / NOT_APPLICABLE with evidence / MISSING blank); a held face of the same item makes a line a component
(PROJECT-INDEPENDENT; provenance T-236, T-298, T-301) | tests/t301_wp_inventory | OPEN until T-301 merges and the export
join reads it.
