# T-665 CONCRETE GATE B ROUND 2: integration package ARCH_TAKEOFF_V3.0.63 (B10 columns / ground beams / straps)

Worker 3 (lane I), 2026-11-10, branch `agents/task-T-665`. **Integration package for Checker Gate B.** Opt-in
candidate only: the released default V2.9 + route G is untouched; nothing is released; no rule, owner decision or
frozen file changes. Development villa, not an accuracy claim. ERS s.2-5, WORKFLOW_CONTROLS s.1 / s.5, UP-QTY-STATUS-001.
Base: the published T-661 merge (V3.0.62, Gate B PASS, engine 7a9ccbff; working branch b89ea23f with T-667).

## 0. What was wired, from what

| Source (Checker-merged) | Merge | Checker run | Lines | Wired as |
|---|---|---|---|---|
| T-658 r2 ledger (`research/agents_t658/out/T658_LEDGER.json`, sha 6c4d9673) | 2cec1520 | Verifier 2026-11-10T02:10Z Gate A PASS (own dxf polygons, D-33 floors re-added) | 61 | 60 wired: GB 8 BOUND + 16 LOWER_ONLY + 5 CONFIRM; columns 6 UPPER_ONLY + 23 CONFIRM; straps 2 CONFIRM; 1 NOT WIRED (footing) |
| T-469 downgrade snapshot (`research/agents_t469/DOWNGRADES_SNAPSHOT.json`, sha 81732639) | (binding) | DG-a31a0d7e (Verifier 2026-10-30, 9 lines), DG-2ddc451c (Verifier 2026-11-01, 4 lines), both APPLIED on V3.0.62 | 13 | materialised whole (R-T665-1 (g)) |
| T-661 line index V3.0.62 (`research/agents_t661/out/LINE_INDEX_V3_0_62.json`, sha 858eba3b) | ea1533e4 | (binding) | 5,073 | binding asserted again on the live run |
| T-595 restatements (`research/agents_t595/out/T595_RESTATEMENTS.json`, sha 80d32d70) | 568ce15e | Verifier 2026-11-07T09:56Z Gate A PASS | 1 | stated and reconciled, NOT wired (below) |

**Two findings made while binding the ledger to the CANDIDATE (not the trial overlay; T-661 lesson):**

1. **13 ground-beam lines are RELEASED (PROVISIONAL, a value) in the candidate** and HELD only at export, by two
   Checker downgrades (D-34 titles, 'UNSUPPORTED BASIS'). The T-658 ledger and the line index read them as HELD. A
   restatement changes a line's content, which makes a LINE_CONTENT_V1 downgrade STALE for ALL its lines: restating 2 of
   DG-2ddc451c's 4 lines would have RELEASED the other 2 (0.288 + 0.279 m3) in the export by side effect. Rule R-T665-1 (g):
   a released line is restated only under an APPLIED downgrade (content sha and engine_qty asserted on the live
   candidate), only to HELD, and the downgrade is materialised WHOLE (its 2 unchanged lines restated BOUND at their own
   range). After the change no line either downgrade names is released; both records go STALE_CONTENT with nothing
   left to hold.
2. **The F10 + F footing (L-164ae9d3) is NOT wired.** The ledger states 1.960 .. 2.275 m3 ('UNCHANGED' on the trial r4
   overlay, which carries the T-595 owner scenario set); the candidate carries 2.176 .. 2.275 under the V3.0.11
   multi-tag conflict record, whose guard (asserted in the chain) is 'the range IS the readings' (ROWS_SEPARATELY 2.176,
   OUTLINE 2.275). 'F10 alone' 1.960 is a third reading that record does not carry; wiring it would break that guard or
   rewrite an earlier version's record (the first run of this package stopped exactly there). Kept at 2.176 .. 2.275,
   named WAITING `T665_FOOTING_SCENARIO`; a lane I row is proposed (how an owner-approved scenario enters a conflict
   record: a new conflict-record version with the S02 scenario set as its readings).

Not wired, named (never 0): boundary band and junction squares (T-666), pool blinding (T-667 merged, unwired), 3 court
beams + 1 neck-cut sliver (blank, CONFIRM), L-fb7a6431 boundary GB (BLOCKED_RFI carrying a 0 .. 3.5256 record range:
the census counts it bounded, the candidate code totals blank; unchanged, CONFIRM).

## 1. Owner manual method beside the drawing-derived method

| Element | Owner / freelancer manual method | Drawing-derived method (wired) |
|---|---|---|
| Short GB span (< 2.5 m) | one section (30x30 or 30x40 by reading) x span | span x 0.30 x the titles that hold, 0.30 .. 0.40 (D-34 no precedence; R-T658-1) |
| Oblique GB band | short edge x 0.30 x depth | drawn outline area (own dxf, Checker re-measured) x titles (R-T658-7) |
| GB carrying a landing / framing beam | the unloaded title section | floor only: area x least title, high NOT printed (ST p.13 'without concentrated load', D-33, R-T658-8) |
| Annex exterior GB | printed exterior section | floor only: run x 0.30 x (+0.25 .. N.G. literal), high open (D-35, R-T658-3) |
| Roof-storey column | storey height x schedule section | ceiling only: section x (printed finished mark - approved structural datum, not printed text), low open (D-39 / Q-54 B, R-T658-4) |

## 2. Evidence status (WORKFLOW_CONTROLS s.5)

- VERIFIED: none new. DRAWING-CONFIRMED bounds, HELD: 8 GB lines (6 restated + 2 materialised).
- HELD blank with the drawn measure beside: 16 GB LOWER_ONLY (AT_LEAST 5.069839 m3: D-33 2.841866 + D-35 2.227973);
  6 columns UPPER_ONLY (AT_MOST 2.80125 m3; datums: +13.90 / +4.30 PRINTED, +9.65 / +0.25 APPROVED_DATUM).
- UNCHANGED (CONFIRM, byte-identical): 5 GB, 23 columns, 2 straps. ASSUMED - OWNER-APPROVED: none. UNKNOWN: none new.

## 3. B10 before -> after (m3; candidate code totals, V3.0.62 run of record 56207c79 -> V3.0.63 09ec4c1a)

| Code | Released | Held bounded low .. high (lines) | Held blank (lines) | Beside the blank lines |
|---|---|---|---|---|
| STR.CONC.GROUND_BEAM (61) | 26.856686 -> **23.760555** (-3.096131 = the 13 downgraded lines, 1.943901 + 1.152231) | 0 (0) -> **1.173410 .. 1.571171 (8)** | 16 -> **21** | AT_LEAST 5.069839 m3 (16 lower-only lines) |
| STR.CONC.COLUMN (64) | 19.7765 (unchanged) | 9.168 .. 13.602 (18, unchanged) | 16 (unchanged; 6 now carry a ceiling) | AT_MOST 2.80125 m3 (6 upper-only lines) |
| STR.CONC.STRAP / FOOTING / every other code | unchanged | unchanged | unchanged | footing 2.176 .. 2.275 kept (NOT WIRED) |

Census view (Checker downgrades applied, the T-658 ledger's frame): GB 9 bounded 1.17341 .. 5.096771 (the 9th is
L-fb7a6431 0 .. 3.5256, a BLOCKED_RFI line with a record range) + 16 lower only 5.069839 + 4 blank = the T-658 r2
totals exactly; 11 index rows change (HELD -> HELD), none released; DG-a31a0d7e / DG-2ddc451c now STALE_CONTENT with
no line left to hold. Reconciliation (candidate, exact): GB released 26.856686 - 3.096131 = 23.760555; held low
0 + 1.17341 (8 bounds: 0.1125 + 0.216 + 0.1305 + 0.09304 + 0.20925 + 0.108 + 0.108 + 0.19612); high 0.15 + 0.288 +
0.174 + 0.130678 + 0.279 + 0.144 + 0.144 + 0.261493 = 1.571171. Asserted in the run by `check_totals` (changes alone).

## 4. Line-by-line diff vs V3.0.62 (every other line byte-identical, asserted)

| Line | Code | Action | Member | V3.0.62 | V3.0.63 | Beside / downgrade |
|---|---|---|---|---|---|---|
| L-26f6b6f2 | COLUMN | UPPER_ONLY | column C2 | blank | blank | AT_MOST_M3 0.425 |
| L-33a9b772 | COLUMN | UPPER_ONLY | column C2 | blank | blank | AT_MOST_M3 0.425 |
| L-53f223b0 | COLUMN | UPPER_ONLY | column C9 | blank | blank | AT_MOST_M3 0.595 |
| L-919a5749 | COLUMN | UPPER_ONLY | column C2 | blank | blank | AT_MOST_M3 0.425 |
| L-d79d17d1 | COLUMN | UPPER_ONLY | column C1 | blank | blank | AT_MOST_M3 0.425 |
| L-fad18af6 | COLUMN | UPPER_ONLY | column C3 | blank | blank | AT_MOST_M3 0.50625 |
| L-0c5ede7f | GROUND_BEAM | BOUND | ground BAND0034 | 0.1125 (PROVISIONAL) | 0.1125 .. 0.15 |  ; DG-a31a0d7e |
| L-0e852cca | GROUND_BEAM | BOUND | ground BAND0007 | 0.288 (PROVISIONAL) | 0.216 .. 0.288 |  ; DG-2ddc451c |
| L-81444e22 | GROUND_BEAM | BOUND | ground BAND0020 | 0.1305 (PROVISIONAL) | 0.1305 .. 0.174 |  ; DG-a31a0d7e |
| L-970bac56 | GROUND_BEAM | BOUND | ground BAND0038 | 0.071008 (PROVISIONAL) | 0.09304 .. 0.130678 |  ; DG-a31a0d7e |
| L-c0b7102a | GROUND_BEAM | BOUND | ground BAND0025.1 | 0.279 (PROVISIONAL) | 0.20925 .. 0.279 |  ; DG-2ddc451c |
| L-e2134034 | GROUND_BEAM | BOUND | ground BAND0021 | 0.108 (PROVISIONAL) | 0.108 .. 0.144 |  ; DG-a31a0d7e |
| L-f0e25ad2 | GROUND_BEAM | BOUND | ground BAND0030 | 0.108 (PROVISIONAL) | 0.108 .. 0.144 |  ; DG-a31a0d7e |
| L-f24cf117 | GROUND_BEAM | BOUND | ground BAND0039 | 0.186592 (PROVISIONAL) | 0.19612 .. 0.261493 |  ; DG-a31a0d7e |
| L-00465df9 | GROUND_BEAM | LOWER_ONLY | ground BAND0035 | blank | blank | AT_LEAST_M3 0.18 |
| L-0bb78acc | GROUND_BEAM | LOWER_ONLY | ground BAND0037.1 | 0.291231 (PROVISIONAL) | blank | AT_LEAST_M3 0.242309 ; DG-2ddc451c |
| L-1487bdda | GROUND_BEAM | LOWER_ONLY | ground BAND0019 | 0.294 (PROVISIONAL) | blank | AT_LEAST_M3 0.2205 ; DG-2ddc451c |
| L-3284f440 | GROUND_BEAM | LOWER_ONLY | ground BAND0012.2 | blank | blank | AT_LEAST_M3 0.1725 |
| L-402dbe61 | GROUND_BEAM | LOWER_ONLY | ground BAND0015 | blank | blank | AT_LEAST_M3 0.7275 |
| L-4783c6e1 | GROUND_BEAM | LOWER_ONLY | ground BAND0016 | blank | blank | AT_LEAST_M3 0.45 |
| L-5af89b9f | GROUND_BEAM | LOWER_ONLY | ground BAND0010.3 | 0.9 (PROVISIONAL) | blank | AT_LEAST_M3 0.6 ; DG-a31a0d7e |
| L-6bf14711 | GROUND_BEAM | LOWER_ONLY | ground BAND0012.1 | blank | blank | AT_LEAST_M3 0.09 |
| L-95a1f198 | GROUND_BEAM | LOWER_ONLY | ground 7DC+7DD#1 | blank | blank | AT_LEAST_M3 0.423 |
| L-a8c5c32c | GROUND_BEAM | LOWER_ONLY | ground BAND0040 | 0.189 (PROVISIONAL) | blank | AT_LEAST_M3 0.189 ; DG-a31a0d7e |
| L-b4a13a43 | GROUND_BEAM | LOWER_ONLY | ground BAND0017.2 | blank | blank | AT_LEAST_M3 0.0375 |
| L-cfb4555c | GROUND_BEAM | LOWER_ONLY | ground 7E7+7E8#2 | blank | blank | AT_LEAST_M3 0.423 |
| L-d53e5eb0 | GROUND_BEAM | LOWER_ONLY | ground BAND0008.2 | 0.1383 (PROVISIONAL) | blank | AT_LEAST_M3 0.147657 ; DG-a31a0d7e |
| L-d8b98b14 | GROUND_BEAM | LOWER_ONLY | ground BAND0013.2 | blank | blank | AT_LEAST_M3 0.435 |
| L-e16c9807 | GROUND_BEAM | LOWER_ONLY | ground BAND0042 | blank | blank | AT_LEAST_M3 0.135473 |
| L-e24946df | GROUND_BEAM | LOWER_ONLY | ground BAND0008.1 | blank | blank | AT_LEAST_M3 0.5964 |

## 5. Regression and validation

- Run of record (Drive copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) / 'ST7757 dxf.dxf' 9f9d1179, decoded
  into the private folder only): t167 `v304_run.py` (33 min) -> `research/agents_t665/v3063_run.py` (exit 0):
  **V3_0_62 56207c79 (asserted = T-661 run of record)** -> **V3_0_63 09ec4c1a**, 5,073 lines; replaced 30, added 0,
  outside rows 5,043 byte-identical (asserted); diff vs V3.0.62: CHANGED 13, CHANGED_TEXT_ONLY 17 (blank -> blank with
  the figure beside), SAME 5,043; vs released V2.9: QUANTITY_DIFFERS 1,043, SAME_QUANTITY 549, NOT_IN_RELEASED 3,481;
  every earlier version's identity check re-ran on the result (A3062.integrate chain) and passed.
- First run of this package STOPPED at the V3.0.11 conflict guard on the footing line (the T-595 bound): not wired.
- `t479_registry_census.py` (unchanged; verdict set V3.0.44 b3b08dd7, downgrade snapshot 81732639) on V3_0_62
  reproduces `research/agents_t661/out/LINE_INDEX_V3_0_62.json` byte for byte; on V3_0_63 ->
  `out/LINE_INDEX_V3_0_63.json`, 5,073 lines, issues {}, complete map, 0 stale blocks against 1.64.0.
- `t665_package_families.py` (T-483 attribute unchanged, chain 62 -> 63): B10-04 STR.CONC.GROUND_BEAM 13 changed + 11
  record; B10-06 record-only (6 ceilings); nothing added or removed.
- Tests: `tests/t665_concrete_gate_b2` (hand villa V665 + downgrade villa + adverse, inputs builder, master 1.64.0)
  PASS. L4: `tests/` on 4bb10688 (module, hub, master, maps; before the downgrade rule): 22,171 passed, 680 skipped,
  105 xfailed, 0 failed (36 min; private inputs absent: skipped by the conftest, known). Targeted re-run on the final
  head: listed in the handoff. freeze 0 differing; codemap stale none; build_master --check equal, 0 problems;
  RULES_MANIFEST check [].

## 6. Registry: BOQ_FAMILY_MASTER_1.64.0 (pending now, promoted IN the merge)

`research/agents_t665/build_master_1_64_0.py`: 1.63.0 + V3.0.63 pending + B10-04 / B10-06 text (0 problems). In the
merge the Verifier runs (ADOPTED lesson, as T-661):

    python3 -I research/agents_t665/t665_promotions_source.py --board .work/board/docs/agents --out research/agents_t665/out/PROMOTIONS_SOURCE_1_64_0.json
    python3 -I research/agents_t665/build_master_1_64_0.py --promote --write
    python3 -I research/agents_t665/write_manifest.py

## 7. Who is right (freelancer beside, never proof)

Columns: freelancer 28.5465 m3 (scorecard V11) vs engine released 19.7765 + HELD bounded 9.168 .. 13.602 + 6 ceilings
<= 2.80125 + 10 blank: the freelancer total lies inside the engine's open range: UNRESOLVED (D-39 roof datum).
Ground beams: no separate freelancer row (his footing line 77.6305 m3 lumps pads + straps + band): NOT_COMPARABLE.
D-33 runs: the freelancer's section is an unloaded title; the drawings print none for a loaded run: ENGINE_RIGHT that
only a floor is drawn (Checker T-658 r2 (h)).

## 8. Rule and lessons row (proposed)

R-T665-1 (engine/source/arch_v3063.py) = R-T661-1 + (f) an UPPER_ONLY ceiling names each datum and whether it is
printed or approved + (g) a downgraded released line is restated only to HELD and only with its whole downgrade.

Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | a ledger read 13 ground beams as HELD that the candidate carries
RELEASED under two content-bound Checker downgrades; restating part of a downgrade's lines makes the record stale and
silently releases the rest | the export view (downgrades applied) was taken for the candidate line | an integration
binds to the raw candidate line, names the downgrade that holds it, and materialises that downgrade whole (every
package; provenance T-665) | tests/t665_concrete_gate_b2 (test_downgrade_materialised_whole, test_adverse_downgrade
partial) | PROPOSED |
