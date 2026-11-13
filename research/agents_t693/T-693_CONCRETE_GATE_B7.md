# T-693: CONCRETE GATE B ROUND 7 integration package, ARCH_TAKEOFF_V3.0.70 (lane I)

Worker 3, 2026-11-11. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.69 (T-687, Gate B
PASS, merge 12bf5b8c, run of record 7ea65f9b); released default V2.9 + route G untouched; nothing released. No drawing,
workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (every piece Checker-merged)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-689 R-T689-1: 2F roof slab top >= 12.937 at the B8 supports (W28 head 12.200 - 0.013 + B8 depth 0.75) | 66ffd421 | Verifier 2026-11-11 04:55 GATE A PASS (own Drive read: B8 span / 20x75 / supports / schedule AGREE) | CONC_RANGE NARROW x 1 (C2 2F 412) |
| T-689 section 2a: five blank CONFLICT columns bounded (annex trio + annex C3 on R-T678-2, 2F C5 415 on R-T689-1) | 66ffd421 | same (1.38278 .. 2.23125 m3 AGREE) | CONC_RANGE BOUND x 5 |
| T-688 R-T688-3 / F-V-P18-2: the 0.95 x 1.20 GF face with its own +0.30 is GROUND SLAB; the detector label BEAM_STRIP (BAND0042) is wrong | a62b3024 | Verifier 2026-11-11 01:56 GATE A PASS (own FR08 noding) | CONC_RANGE OWNER x 1 (record only) |
| T-678 annex plane record (R-T678-2 / R-T682-1, ONE_PLANE, s_lo 3.544) | f8515d4b | Verifier 2026-11-10T17:58Z (via T-682's pinned builder) | height datum of the 4 annex columns |

Register ruling 'column tops under B8' (ELEMENT_REGISTER, Lead 2026-11-11 04:20): the column line owns the shaft to the
joint (R-CONC-OWN-1); the window head is evidence only; the plate transfer +0.133640 stays refused (F-T689-1).

**Finding while wiring (F-T693-1):** the BOQ line L-a7ab57d8 carries no region label at all (its element id, formula
and inputs name only the face area x 0.10); the label BEAM_STRIP / BAND0042 lives in the structural slab-region
detector outputs (overlays, exception register EX-0262 / EX-0366), outside the candidate. The task text 'corrects the
BAND0042 label of L-a7ab57d8' is therefore wired as an OWNERSHIP RECORD on the line (physical element, the wrong
detector label and region, the corrected owner, the band pairing refused, the GB line whose runs stay outside the face);
the line's quantity, state and class are asserted unchanged. The detector itself (slab_engine region assignment) is not
changed here: that is a detector method version of its own (lane S / tooling), named for the Lead.

## 2. Method (R-T693-1, every villa; module `engine/source/arch_v3070.py`)

- (v) A column bound is the product of its own terms, RECOMPUTED at wiring time and asserted equal to the merged ledger
  to 1e-6 m3: section readings (one, or the two of a CONFLICT: drawn outline and schedule band, both kept) x height
  (base APPROVED / PRINTED -> slab-top joint). Bound = smaller area x lower height .. larger area x upper height; a
  blank line is never bounded on one reading (X6 / Q-61 C: one reading is never chosen).
- Lower top datum, only: BEAM_JOINT (R-T689-1: max(head - read tolerance) + the printed beam depth, for that beam's own
  support columns) or PLANE (R-T678-2 / R-T682-1, ONE_PLANE with sections checked). A window head with no printed beam
  over it bounds nothing (refused, the line stays HELD). Upper top: a printed ceiling mark with what it is.
- (w) NARROW never widens and never moves the end it does not name (ends_moved asserted).
- (x) The B8 joint bound reaches only B8's supports 412 / 415; the plate-wide transfer is refused (F-T689-1 open).
- (y) OWNER: a record only; it binds only a line whose item code is the ruled owner's (GROUND_SLAB ->
  STR.CONC.GROUND_SLAB); quantity / state / range / class unchanged (asserted in `check_concrete`).
- (z) Every restated line names its designer items in its question (section D-66 and top datum D-39 / Q-54 B).
- = R-T682-2 (a) .. (u): earlier V3.0.62 .. V3.0.67 records of a restated line move under `superseded` (L-919a5749:
  its V3.0.65 roof-column low record); only STR.CONC.*|m3 totals move, each exactly by the changes and equal to the
  inputs' `expect_totals`; released m3 never; every other line byte-identical; the V3.0.64 .. V3.0.67 concrete checks,
  the V3.0.67 lintel check, the V3.0.68 masonry check and the V3.0.69 finish check re-run on the result.

Owner manual method vs drawing-derived method, side by side: owner = section x storey height member by member, a
section conflict held with both readings and a designer request, no generic storey height; drawing = the same, the
height bounded from drawn evidence (the head under a printed beam at the joint, or the one-plane annex slab bound) and
capped by the printed finished mark. Both methods hold the same lines; the drawing method gives the bounds.

## 3. Run of record and line-by-line diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded into the private folder only: own fresh t167 `v304_run.py` (25 min) ->
`research/agents_t693/v3070_run.py` (12 min, exit 0): every earlier version re-run and asserted, **V3_0_68 d1de50cb,
V3_0_69 7ea65f9b (asserted = T-687 run of record)** -> **V3_0_70 e8e001de**, 5,123 lines; replaced 7 (5 BOUND + 1
NARROW + 1 OWNER), added 0, outside 5,116 byte-identical (asserted). Diff vs V3.0.69: CHANGED 7, SAME 5,116. vs released
V2.9 + route G: NOT_IN_RELEASED 3,531, QUANTITY_DIFFERS 1,054, SAME_QUANTITY 538, all unchanged from V3.0.69 (the six
column lines were already 'differs' as held; the slab line keeps 0.114). Census `t479_registry_census.py` (unchanged;
verdicts V3.0.44 b3b08dd7, downgrades 81732639) on V3_0_69 reproduces `research/agents_t687/out/LINE_INDEX_V3_0_69.json`
byte for byte; on V3_0_70 -> `out/LINE_INDEX_V3_0_70.json` (6c12da07), issues {}, complete map, 0 stale blocks; index
diff = exactly the six column lines' held_low / held_high. `t693_package_families.py` (chain 69 -> 70): B10-06
STR.CONC.COLUMN 6 changed; B10-05 record only. Summary `summary_t693.json`.

STR.CONC census (m3; released / bounded / blank, never summed):

| code | V3.0.69 | V3.0.70 |
|---|---|---|
| STR.CONC.COLUMN | 59 lines: 19.7765 released + 10.26435 .. 13.27025 (22 bounded) + 7 blank | 59 lines: 19.7765 released + 11.67283 .. 15.5015 (27 bounded) + 2 blank |
| STR.CONC.GROUND_SLAB | unchanged (L-a7ab57d8 0.114 released, ownership record added) | unchanged |
| every other STR.CONC.* code | - | byte-identical |

Changed lines (each by hand from the drawing terms; source drawing references: ST7757 SFRS / GFRS outlines, SBT row
1EBA, column schedule rows; architectural SW elevation heads via T-201):

| line | member | before | after | by hand | evidence status |
|---|---|---|---|---|---|
| L-919a5749 | C2 2F 412 (20x50) | 0.303 .. 0.425 | 0.3287 .. 0.425 | 0.10 x (12.937 - 9.65 = 3.287) .. 0.10 x (13.90 - 9.65) | low DRAWING-CONFIRMED, high HELD (D-39) |
| L-bc01297b | C5 2F 415 | blank | 0.3287 .. 0.51 | min(0.20x0.50, 0.60x0.20) x 3.287 .. 0.12 x 4.25 | low DRAWING-CONFIRMED, high HELD (D-66, D-39) |
| L-9f5a6470 / L-c0b3340a / L-e6c1c9a7 | C GF annex 34A / 34D / 356 | blank | 0.26352 .. 0.405 each | 0.08 x (3.544 - 0.25) .. 0.10 x (4.30 - 0.25) | low DRAWING-CONFIRMED, high HELD (D-66, Q-54 B / D-39) |
| L-694a75c8 | C3 GF annex 350 | blank | 0.26352 .. 0.50625 | 0.08 x 3.294 .. 0.125 x 4.05 | same |
| L-a7ab57d8 | GF slab face 0.95 x 1.20 | 0.114 RELEASED | 0.114 RELEASED | 1.14 x 0.10 (unchanged) | record only (R-T688-3) |

Diff against the released V2.9 + route G: none of the seven lines moves a released V2.9 quantity.

## 4. Held / missing, named; downstream

- STR.CONC.COLUMN 2 lines HELD blank: 2F tank C2 40F / C3 424 (D-44: B15 up / down stand refuses their ceiling).
- Plate-wide transfer of the B8 joint (+0.133640 m3 on C9 418, C2 41B / 41E, C1 421, PC-2F lows) REFUSED (F-T689-1:
  R-T669-2 plate lows vs the R-T678-2 'T 18 inside the plate' clause): Lead ruling needed before any plate-wide wiring.
- Register gaps F-T689-2 (PC-2F section has no designer item) / F-T689-3 (the five columns bounded here are not in
  D-66's registered list): the lines carry the section conflict in their question; the D-66 list is the Lead's.
- F-T693-1 (above): the slab-region detector label is outside the candidate; a detector fix is its own version.
- Downstream: the six columns' STR.FORMWORK lines (FW:<line>:FACES:HELD) stay HELD blank (not re-derived from the
  bounds: perimeter x height of a CONFLICT section is a formwork package of its own); column rebar for these members
  (owner 2026-11-09: rebar by ratio on HELD members) can now take the bounded m3, not wired here. Released m3, the
  BOQ export view and every non-concrete line unchanged.

## 5. Freelancer, verdicts, lesson

Freelancer: columns per type x count (T-248 / T-683); not used for any bound and not comparable line by line (no
member-level row). Verdict proposals: L-919a5749 low ENGINE (drawing) bound DRAWING-CONFIRMED, line stays HELD; the
five bounded lines UNRESOLVED (designer D-66 / D-39 / Q-54 B), bounds DRAWING-CONFIRMED at the low end; L-a7ab57d8
ENGINE_RIGHT (quantity), detector label wrong (record). No owner question: ERS 2.7 not met (designer items only).
Lesson row (ERS s.7, proposed): "a correction aimed at a 'label of a line' was a label of the detector, not of the BOQ
line: before wiring a non-quantity correction, find the field that carries it; if it lies outside the candidate, wire an
ownership record on the line and leave the detector to its own version, never an invented line field (every villa;
T-693, tests/t693_concrete_gate_b7 owner adverse)".

## 6. Validation

- L1 / L2: `tests/t693_concrete_gate_b7` (hand villa K693, not the development villa: C2 narrowed on a beam joint
  0.2392 .. 0.304, C5 conflict bound 0.2392 .. 0.38, annex A1 on a plane 0.1794 .. 0.255, an ownership record; mirror
  order; outside lines byte-identical; expect totals asserted; adverse: a head-only datum stays HELD, plate transfer to
  a non-support refused, a ledger that is not the recompute, one reading on a blank conflict, cm / mm as metres, a
  narrowing that widens or names the wrong end, a storey height as ceiling, no items, an unconfirmed head, a typical
  base, a stepped plane, VERIFIED, an owner record with a figure / a stale value / no correction / on a ground-beam
  line, a tampered owner line, stale binding, applied twice, a line twice, a released / plaster line, a stray code),
  the inputs builder on the committed ledgers (counts, hand figures, totals, joint only to its supports, tampered pin),
  master 1.71.0 (pending) builder / checks / adverse.
- L3 / L4 and the freeze / codemap checks: see the handoff (results by commit).
