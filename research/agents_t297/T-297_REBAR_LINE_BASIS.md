# T-297 Rebar line-to-member basis ledger (lane S; Alsenan; every villa)

Worker 1, 2026-10-25 13:22 .. UTC, run session_01C7yJoRPEg2NvUf2TEEdb9H, branch `agents/task-T-297`. Research ledger:
nothing wired, no candidate or released line changed, no method version, no quantity released or re-labelled in the
candidate. Integration dependency of the rebar line (lane I) and of the metric-ton export (T-298). Development villa,
not an accuracy claim. Drawings named by Drive folder and title only. ERS s.2.1 - 2.6, s.3, s.4 applied.

## 0. Run, identity, sources

Own run, Python 3.11.17, Drive copies "Alsenan chalet project" / 'ST7757 dxf.dxf' (`9f9d1179`) and P7757.dxf from
P7757_DXF_COMPRESSED.zip (`ab54dd55`): `research/agents_t167/v304_run.py` then `research/agents_t245/v3016_run.py`
(ARCH_TAKEOFF_V3.0.16, 3,699 lines; lines csv **`a4dc01dd`** = the candidate of record, reproduced). Extract:
`python3 -I research/agents_t297/t297_extract.py <run>/v3016 --out research/agents_t297` ->
`CANDIDATE_V3016_REBAR_LINES.json` (every line of item STR.REBAR / trade REINFORCEMENT: **2,505 lines**; ids, states,
quantities, ledger keys, printed readings; long texts cut at 240 characters). Ledger:
`python3 -I research/agents_t297/t297_alsenan.py --write | --check` -> `LINE_BASIS_T297.csv` (one row per line),
`LINE_BASIS_SUMMARY_T297.json`, `LINE_BASIS_CONSUMER_T297.json` (the lane I shape). Rules: `t297_ledger.py`
(LINE_BASIS_LEDGER_V1, stdlib). Tests: `tests/t297_rebar_line_basis` (villa K297 hand fixture + Alsenan rebuild).

## 1. Physical element and the question (ERS s.2.1)

A reinforcement line is a set of bars in one member (or one member group), in one bar group (main / links / laps /
ends / mesh ...), with ONE basis for its figure. The question is not "how many kg" but "on what basis does each kg
figure of the candidate stand": a printed schedule row on drawn geometry, a Checker verdict, a bound on a stated datum,
an approved owner fallback, a convention, or nothing (held). A bound stays a bound at the export boundary and is never
added to a measured figure (owner 2026-10-25 10:33 (2); lesson 2026-10-25 'a bound is only as good as its datum').

## 2. Rules (LINE_BASIS_LEDGER_V1; general, every villa; Alsenan only supplies the data)

| Rule | Content |
|---|---|
| LB-1 | a line the candidate carries as NOT_APPLICABLE_WITH_EVIDENCE is NOT_APPLICABLE (superseded / member not present) |
| LB-2 | a hand-ledger line released from a printed schedule row is DRAWING_CONFIRMED for the component it names; VERIFIED only where the line cites its own Checker re-measure (none does). A face-to-face component is a measured COMPONENT; the ends it leaves out are their own lines (flag COMPONENT_ENDS_HELD); never relabelled a bound of itself |
| LB-3 | a hand-ledger HELD_RANGE line is a BOUND; its datum is the range basis the line states; datum HELD unless a printed / verified chain is cited |
| LB-4 | HELD_LOWER_BOUND -> BOUND with an OPEN upper end; at 0 with the upper end open it carries no information -> HELD (flag LOWER_BOUND_ZERO_OPEN); HELD_DEFINED / UNQUANTIFIED -> HELD (the defined kg kept as audit `line_kg` only) |
| LB-5 | a route line (no hand ledger) with kg is a CONVENTION (route G V6 generic conventions; owner 10:33 (2): provisional subtotal, never verified, never a bound) |
| LB-6 | a lap / bar end / development figure from a default factor (DEFAULT_FACTOR) or from note 9, the starter-bar development note (NOTE_READING; owner 2026-10-24 s.6 (1): not a general lap rule) is CONVENTION, BOUND (datum HELD / CONVENTION) or HELD, never measured |
| LB-7 | one line, one row; totals only per (family, basis status); kg internally, t = kg / 1000 once (OWNER_RULE_REBAR s.1) |
| LB-8 | a research bound in no candidate line (T-280 cores) is a coverage finding, never added to a line |
| LB-9 | a footing line released on a printed count but a straight length of side - 2 x the MINIMUM cover of the general notes is a CONVENTION (a minimum printed in the notes is never a member dimension, lesson 2026-10-23 necks; bends not derived); per-metre footings BOUND, datum HELD (Q-71 footing '/m', owner 12:36 / 13:16) |

## 3. Result: every reinforcement line once (2,505 rows), residual 0.000 kg

Per family and basis status (kg internal, t once). **Statuses are never added to each other; a BOUND is never a
quantity.**

| Family | DRAWING_CONFIRMED | CONVENTION | BOUND low .. high | HELD (lines) | NOT_APPLICABLE (lines) |
|---|---|---|---|---|---|
| Columns (T-148, GF / 1F / 2F) | 32 lines **1.887128 t** | - | 113 lines 1.280992 .. 2.119349 t (links Q-71, laps note 9) | 238 (182 T-148 defined / unquantified + 56 route neck lines) | 122 (route G superseded) |
| Beams (T-149) | 230 lines **5.171031 t** (face to face) | - | 457 lines 4.637530 .. OPEN t (51 lines with an open upper end) | 76 | 366 |
| Ground beams + straps (T-138 r2) | 88 lines **1.252907 t** (face to face) | - | 62 lines 1.297139 .. 2.269557 t | 131 | 9 |
| Footings | - | 38 lines **0.874862 t** (count printed, min cover as exact) | 20 lines 2.742506 .. 2.836400 t (per-metre F8 / F12 / F13 / F14 / FF) | 27 | - |
| Slabs (T-152) | - | - | 294 lines 4.643766 .. 6.832326 t | 18 | 72 |
| Ground slab (route G) | - | 24 lines **1.064240 t** | - | - | - |
| Stairs (T-166) | - | - | 50 lines 1.039160 .. 1.443671 t | 17 | - |
| Pool / water tank | - | - | - | 20 / 1 | - |

Closure: per family, the rows' quantity sum and BOUND-low sum equal the candidate's own measured_net and
bounded_range.low sums to **0.000000 kg** (11 keys, `residuals_vs_candidate_kg`). Against each hand ledger's own named
total: T-148 released 1,887.128 vs named 1,887.131 kg (-0.003 kg, tolerance 0.017 = storage rounding of 32 rows at
3 dp + the total's own), T-149 5,171.031 vs 5,171.03 kg (+0.001, tolerance 0.120). No VERIFIED line (no candidate
reinforcement line cites its own Checker re-measure) and no ASSUMED — OWNER-APPROVED line (the owner's 40 d / 60 d lap
convention is a proposal, not an approved rule: OWNER_RULE_REBAR s.2, s.4 (3)).

What may be read as one figure: only within one (family, status) cell. The candidate's "released" reinforcement (lines
in a quantity state) is **8.311066 t DRAWING_CONFIRMED components** (columns 1.887128 + beams 5.171031 + ground beams
1.252907) **plus 1.939102 t CONVENTION** (footings 0.874862 + ground slab 1.064240), two different bases that are
reported side by side and never as one 10.250168 t total.

## 4. Hand checks (from the drawing readings the lines print, ERS s.2.3)

| Line | Printed reading | Hand | Line | Basis |
|---|---|---|---|---|
| COL-1F-35 C2 main (T-148) | p.9 C2 1F 8 ø 16; storey interval 3.70 + D_ctrl 0.50 = 4.20 m | 8 x 4.20 x 256 / 162 = 53.096 kg | 53.096 | DRAWING_CONFIRMED |
| COL-GF-18 lap at storey bottom (T-148) | note 9: 8 bars x 40 d .. 70 d, ø 16 | 8 x 0.64 x 1.580247 = 8.091 .. 8 x 1.12 x 1.580247 = 14.159 kg | 8.091 .. 14.159 | BOUND, datum HELD, NOTE_READING (zone and splice position not printed; note 9 governs starters) |
| F5 bottom long bars (footing) | schedule '20 \| 12', side 2.40 m, cover note 22 'not less than 7 cm' | 20 x (2.40 - 2 x 0.07) x 144 / 162 = 20 x 2.26 x 0.888889 = 40.178 kg | 40.177778 | CONVENTION: the count is printed, the straight length uses the MINIMUM cover as exact and no bend of the p.13 detail; the installed bar is neither bounded below nor above by this figure |

## 5. Findings (coverage and basis; nothing changed)

- **F-T297-01 column foundation storey.** The candidate's only column lines on the FOUNDATION floor are 56 route G
  neck lines (28 MAIN, 28 TIES), all BLOCKED (HELD). The T-280 core bounds (26 LOWER bounds 0.734781 t on the printed
  level chain, 10 HELD; MERGED 86fdc315) sit in NO candidate line. A later lane I row carries them as BOUND lines with
  their datum (formation limit + underlay 0.17 + H), never as measured kg; until then the column family has no
  foundation main-bar quantity of any status.
- **F-T297-02 ground-beam basis.** The candidate's 88 DRAWING_CONFIRMED ground-beam / strap lines (1.252907 t) rest on
  T-138 r2. T-265 (MERGED) restates 13 axis pairs of T-138 (T-299 READY: 0.572500 t of T-138 -> T-265 released rows,
  0.320440 t -> HELD annex / court). Until lane I re-bases those lines, their DRAWING_CONFIRMED label stands for T-138
  only; a lane I row takes T-299's REPLACES relation, never both ledgers.
- **F-T297-03 footings (basis).** All 38 released footing lines (0.874862 t, the "released 874.86 kg" footing figure)
  are CONVENTION: count printed, straight length = side - 2 x 70 mm where note 22 prints a minimum, no bends. Owner
  13:16 (F2 - F5) asks exactly this for T-299 part F; this ledger records the basis, it does not re-measure.
- **Released components are lower parts of their bars.** 265 face-to-face lines (beams, ground beams) carry
  COMPONENT_ENDS_HELD: the bar ends (note 9) are their own BOUND lines with a HELD datum. A lane I row reports the
  component as DRAWING_CONFIRMED and the ends as BOUND, never one "bar total".

## 6. The consumer shape for a later lane I rebar row (acceptance 4)

`LINE_BASIS_CONSUMER_T297.json`: one record per line: `line_id, family, members[], bar_group, basis_status,
quantity_t (null unless VERIFIED / DRAWING_CONFIRMED / ASSUMED / CONVENTION), bound_t {low, high (null = OPEN), datum,
datum_status} (BOUND only), held_reason, evidence, sources[], flags[]`; t = kg / 1000 once at 6 decimals; totals per
(family, basis_status) only (`t297_ledger.total` refuses a mix of statuses, a BOUND, a HELD row or a t row).

## 7. Tests (villa K297, not Alsenan; hand values in the test docstring)

Normal: beam B1 bottom 3 ø 16 over 4.20 m = 19.911111 kg DRAWING_CONFIRMED; column C1 core 4 ø 14 on the printed
chain 1.00 - (-1.50 + 0.17 + 0.60) = 1.73 m = 8.372346 kg BOUND (upper OPEN, datum DRAWING_CONFIRMED); B1 lap 40 d
default = 3.034074 kg CONVENTION; C1 links HELD. Adverse (all refused): a bound reported as measured; a bound without
its datum; a default-factor lap as DRAWING_CONFIRMED / VERIFIED / ASSUMED; a HELD row as 0; a t row / a string kg in a
kg total; two statuses in one total; a line tied twice / missing / extra; a residual outside storage rounding; a
measured row without evidence or member.

## 8. Verdict proposals, lesson, what is missing

- Engine vs freelancer: not measured by this task (basis ledger only; released route rebar vs freelancer -40.6 % is the
  board's T-009 figure, unchanged). Verdict proposals: footing released lines RULE_DIFFERENCE pending T-299 part F
  (minimum cover used as exact, bends absent); ground-beam lines ENGINE basis superseded by T-265 (F-T297-02).
- Lesson proposed (ERS s.7): problem: candidate reinforcement lines carried kg with no stated basis, so released
  components, bounds and conventions could be summed into one tonne figure at export; root cause: the export reads the
  line state (SOURCE_DERIVED / BOUNDED_EXPOSURE), which does not distinguish a printed-count component from a
  convention length; rule: every reinforcement line carries a basis status (LB-1 .. LB-9) and totals exist only per
  (family, status); a minimum printed in the notes (cover) used as an exact length makes the line a CONVENTION;
  test: tests/t297_rebar_line_basis (villa K297 normal + adverse); status: proposed.
- Not done / uncertain: no Checker verdict on any line (VERIFIED 0); the T-152 / T-166 per-row datums are carried as the
  ledgers state them (HELD), not re-derived; the pool / tank lines stay HELD; no unit-mass choice between exact density
  and d^2 / 162 (lines carry the candidate's own); beams / slabs were not re-derived (basis only).
