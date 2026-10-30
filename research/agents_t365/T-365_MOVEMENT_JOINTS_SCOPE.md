# T-365 Movement / expansion joints and sealants (B13-05): what the drawings print (development villa; every villa)

Worker 1 (lane S), 2026-10-30, run session_01E6cPnav3d5R3ry3qkULcez. Research piece, not wired: no engine module, method
version, route G, rule / knowledge file, candidate line or released quantity changed. Development villa, not an accuracy
claim. Drawings named by Drive folder "Alsenan chalet project" and title; entities by DXF handle or PDF page; note numbers
only (no note text copied, no client data). ERS s.2 - s.4, s.7.

Files: `joints_scope_v1.py` (JOINT_SCOPE_V1, pure rules, stdlib), `ALSENAN_JOINTS_INPUT.json` (read this run),
`t365_alsenan_check.py` -> `SHEET_SEARCH_T365.csv` (31 sheets), `JOINTS_T365.csv` (11 physical joints), `HATCHES_T365.csv`
(62 hatches), `FREELANCER_T365.csv`, `summary.json`; tests `tests/t365_joints/` (28 pass: 22 hand fixture villa K365
incl. adverse cases + 6 development-villa pins incl. output reproduction).

## 1. The physical elements (ERS s.2.1)

Eleven separate items, each m.l, each with one owner trade: J1 structural movement joint through the frame; J2 slab-on-grade
contraction / isolation joint; J3 construction joint / water stop (pool, footings); J4 roof screed / roof-tile field joint;
J5 outside tiled-floor field joint; J6 tile perimeter joint; J7 paving joint; J8 boundary-wall-to-building / ground-slab
separation; J9 joint along the boundary wall; J10 parapet / coping joint; J11 opening perimeter sealant. Sealant (m.l) is
counted only on a measured joint, per printed sealed face. The grout joint between tiles (Q-42: 1 mm inside, 2 mm roofs /
outside) is part of the tile layout, not B13-05.

## 2. Evidence search (acceptance a) — `SHEET_SEARCH_T365.csv`

| Source | How read | Joint printed |
|---|---|---|
| ST p.1 - p.6 (plans) | p.1 / p.4 at 110 dpi, others 30 dpi + DXF | none: ONE continuous frame 31.37 x 15.00, the annex tied to the house by continuous beams (CB6, CB7); no double column / beam line |
| ST p.7 pool, dome | 200 dpi quadrants | none: no construction joint, no water stop (5 cm screed / 5 cm membrane / 10 cm plain concrete only) |
| ST p.8 notes 1 - 24 | 170 dpi, every note | none names a joint |
| ST p.9 - p.12 schedules | 30 dpi + DXF | none |
| ST p.13 footings, lintels, ground beams | 200 dpi | none |
| ST p.14 lift pit, boundary wall, parapets | 200 dpi | none: 'Slab on grade.' meets the pit wall with no joint; 15 cm plain concrete drawn against the boundary wall ends in a break line; parapets continuous |
| ST p.15 - p.16 columns, slab-on-beams, stairs | 110 - 200 dpi | none (p.15 note 1 is the 40 d lap of temperature bars, a bar lap, not a joint) |
| ARCH p.10 SECTION A-A, p.11 SECTION B-B, p.12 FENCE | this run, 60 / 200 dpi | none; street fence runs 580 / 250 / 81 / 195 / 115 / 195 / 83 cm without a joint mark |
| ARCH p.1 - p.9 | T-091 (merged: every page read, 'expansion joint' 0) + this run's DXF census | none |
| SAN p.1 - p.3 | 70 dpi this run (+ T-091 150 dpi) | none; legend has no joint symbol; roofs: slope arrows only |

DXF census (English + Arabic keywords, SHX decoded with `engine/source/cad/shx_arabic`): ST 2 253 text records -> 0 hits;
P7757 276 -> 10 hits, all FALSE_POSITIVE (title-block 'plot number', handles 1578 .. 1601). Layers ST 49 / ARCH 19, blocks
420 / 442, linetypes (CONTINUOUS, HIDDEN, CENTER, CENTER2): none named or styled as a joint. 62 non-solid hatches (ST 33,
ARCH 29: NET, LINE, ANGLE, AR-PARQ1, MUDST, ANSI3x, AR-CONC, ...) classed HATCH_NOT_JOINT (a pattern pitch is not a
joint). Twin-column test (a structural joint shows as two columns side by side): 171 column shapes, 0 pairs 1 - 100 mm
apart (3 touching pairs = two outline pieces of one cruciform / L column).

## 3. Result per joint (acceptance b, c) — `JOINTS_T365.csv`

| Joint | Status | m.l | Owner trade | V3.0.26 line | Basis |
|---|---|---|---|---|---|
| J1 structural movement | NOT_IN_DRAWN_SCOPE | None | structural | NO LINE | continuous frame, 0 twin columns, monolithic sections |
| J2 slab on grade | NOT_IN_DRAWN_SCOPE | None | structural | NO LINE (STR.CONC.GROUND_SLAB is m3) | ST p.3, p.14 |
| J3 construction joint / water stop | NOT_IN_DRAWN_SCOPE | None | structural | NO LINE | ST p.7, p.13, p.8 |
| J4 roof field | **HELD** | None | roofing (B13-01) | NO LINE (FIN.WP.ROOF m2 untouched) | Q-42: expansion joint 3 mm wide in roof / outside tiling; spacing and own line not answered; no roof joint printed |
| J5 outside tile field | **HELD** | None | finishes (outside floors) | NO LINE | Q-42 width + OWNER_RULE_OUTDOOR_FLOORS (side walk, side passage porcelain / ceramic) |
| J6 tile perimeter | NOT_IN_DRAWN_SCOPE | None | finishes | NO LINE | no drawing, no owner rule |
| J7 paving (court interlock) | NOT_IN_DRAWN_SCOPE | None | external works (B13-02) | NO LINE | owner rule names interlock only; nothing drawn |
| J8 boundary wall / building | NOT_IN_DRAWN_SCOPE | None | structural | NO LINE | ST p.14 |
| J9 along the boundary wall | NOT_IN_DRAWN_SCOPE | None | structural | NO LINE | ST p.14 'SEE ARCH PLAN', ARCH p.12 |
| J10 parapet | NOT_IN_DRAWN_SCOPE | None | structural | NO LINE | ST p.14, p.4 note 1 |
| J11 opening sealant | NOT_IN_DRAWN_SCOPE | None | openings | NO LINE | no opening detail issued |

Measured: 0 m; HELD: 2 (never 0); double count with B13-02 paving and B13-01 roof build-up: 0 (neither has a line in
V3.0.26; no joint quantity is added to or taken from FIN.WP.ROOF m2). RFI candidates (acceptance f): none, because no
joint is drawn (R-JT-7: an absence is NOT_IN_DRAWN_SCOPE, not a designer question).

## 4. Methods side by side and reconciliation (ERS s.2.4; acceptance d)

| | J1 - J3, J6 - J11 | J4 roof field, J5 outside tile field |
|---|---|---|
| Owner manual method | no rule | Q-42: width 3 mm; the picture's 5 - 6 m spacing / 12 mm profile are NOT Urban rules; spacing and own BOQ line HELD |
| Drawing-derived (this task) | nothing printed: NOT_IN_DRAWN_SCOPE | no position, no printed spacing: HELD |
| Engine V3.0.26 | no line (B13-05 NOT_IN_CANDIDATE) | no line |
| Freelancer | no row | no row |

Freelancer: 885 register rows + the concrete and by-category workbooks searched. ONE row uses the word 'joints': PLS
invoice row 26 (= by-category A51), external plaster labour 'corners, grooves and rounded arrises', 1 297.35 m.l physical,
priced as 648.675 m at '2 m = 1 m'. Verdict proposal **RULE_DIFFERENCE (scope)**: a plaster-accessory item of the external
plaster trade, not a movement joint; B13-05 double count 0; it is 1 297.35 m of physical length at a half rate (the ERS
s.3 example), never 648.675 m of joint. Project verdict proposal: **NO_QUANTITY_BOTH** — engine 0 lines vs freelancer 0
lines on B13-05, both correct on quantity because the set prints no joint; residual in units: none.

Limit: the floors / insulation workbook (23.6 MB) is over the connector's download limit; its 197 register rows were
searched, not every cell.

## 5. General rules (JOINT_SCOPE_V1, every villa, provenance T-365; research rule, not a rule-library version)

R-JT-1 position only from a drawn line or a printed spacing on a drawn extent; textbook, picture, typical, freelancer,
engine default and hatch refused. R-JT-2 an owner width / type is not a position: HELD. R-JT-3 spacing notation first:
MAX -> ceil(L / s) - 1; EXACT -> L / s - 1 only when whole within 1 mm, else HELD; UNSTATED -> HELD. R-JT-4 MEASURED /
HELD / NOT_IN_DRAWN_SCOPE; a quantity only when MEASURED, never 0. R-JT-5 sealant = joint x printed sealed faces. R-JT-6
one segment, one line (DOUBLE_COUNT refused). R-JT-7 RFI only for a drawn joint without its type.

Tests (villa K365, hand calculations in the docstrings): drawn joint 12 000 mm = 12.000 m, sealant both faces 24.000 m;
roof 14.0 x 9.0 at max 4.5 m = 3 x 9.0 + 1 x 14.0 = 41.0 m; court 12.0 x 7.5 at 3.0 m c/c -> 7.5 / 3.0 = 2.5 HELD (and
12.0 x 9.0 -> 51.0 m); adverse: six borrowed spacing / position sources, the Q-42 picture spacing, a hatch, the same
segment on the paving and the screed line, a held 0, missing sources, mm / cm / m and an unknown unit, mirror and two
rotations, a drawn joint without a type (RFI, sealant HELD).

## 6. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-30 | B13-05 sat BLOCKED_BY_SOURCE 'needs details' with no record of what the set prints; the Q-42 picture carried a 5 - 6 m spacing that could be read as a rule | absence of a joint was never recorded as a finding, and an owner width was not separated from a position / spacing | a joint is MEASURED only from a drawn line or a printed spacing on a drawn extent (notation read first); an owner width alone is HELD; nothing printed is NOT_IN_DRAWN_SCOPE; a borrowed spacing or a hatch is refused (every villa) | tests/t365_joints (picture spacing refused; hatch refused; EXACT spacing that does not fit HELD; held 0 refused; double count refused) | PROPOSED |

## 7. For the Checker (re-read)

1. ST7757.pdf p.8 notes 1 - 24; p.14 lift pit 'Slab on grade.', TYPICAL BOUNDARY WALL plan + A-A, parapet details; p.7
   pool section; p.13 footing details; p.15 notes 1 - 3; p.4 notes 1 - 2.
2. ST DXF: text census 2 253 records 0 hits; column shapes on *COL* layers, no pair 1 - 100 mm apart.
3. P7757.dxf: 276 records, 10 false positives 1578 .. 1601 (title block); hatches in HATCHES_T365.csv.
4. Architectural p7757_arch_sheet10 (A-A), Pages_11-12 (B-B, fence): no joint mark.

## 8. Not done / uncertain

- No quantity: nothing printed. J4 / J5 wait on the Q-42 residual (spacing and own BOQ line), which the Lead asks when
  the roof tile count is built (already registered; no new owner question: ERS 2.7 is not newly met).
- The roof finish itself is not printed (T-091); J4 exists only through the owner's Q-42 wording.
- Construction joints are not drawn; whether a contract carries them as an item (pool) is a specification matter not
  issued for this villa.
- Process note for the Lead: the Drive connector now saves downloads as raw bytes, while `agent_env.sh decode` expects
  base64; this run re-encoded each file to base64 in the scratchpad and decoded it with the wrapper into .work/private.
