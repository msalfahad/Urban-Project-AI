# T-729: FORMWORK GATE B + CONCRETE ROUND 10 integration package, ARCH_TAKEOFF_V3.0.75 (lane I, hubs H5f + C10)

Worker 3, 2026-11-12. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.74 (T-717 r2, Gate B
PASS, merge e6481b43, BOQ_FAMILY_MASTER 1.75.0, line index `research/agents_t717/out/LINE_INDEX_V3_0_74.json`);
released default V2.9 + route G untouched; nothing VERIFIED. No drawing opened for a figure: every figure is a
Checker-merged ledger's, restated by line id. No drawing, workbook, client name or coordinate here.

## 1. What is wired (Checker-merged only; T-730 map hubs T-729 + C10: 417 rows, stale 0 on V3.0.74)

| source (merge) | Checker Gate A | rows wired as |
|---|---|---|
| T-714 `out/T714_FORMWORK_BOUNDS.json` R-T714-1/-2 (e6ebe28a) | Verifier 2026-11-11T23:49Z | 370 B10-13 lines: 54 fix rows RELEASE, BOUND / AT_LEAST / CAP / NAMED |
| T-724 `out/T724_FINDINGS.json` F-V714-1, R-T724-3/-4 (cfca9394) | Verifier 2026-11-12 ~02:00Z | 4 soffit lows restated; C10 GB cap; 4 named children ADDED |
| T-732 `out/T732_FORMWORK_MOVED.json` R-T732-1/-2 (35c0c09e) | Verifier 2026-11-12T07:56Z | 7 columns whose concrete moved (4 BOUND, 3 AT_LEAST) |
| T-735 `out/T735_DECIDER.json` R-T735-1/-2 (870f15f5) | Verifier 2026-11-12T09:55Z | 6 conflict columns (1 BOUND, 5 AT_LEAST) + L-867e155d (point 0.102019) |
| T-725 `out/T725_LEDGER.json` R-T725-1..3 (b20fe25c) | Verifier 2026-11-12T03:48Z | 20 B7-13 stair formwork lines |
| T-731 `out/T731_LEDGER.json` R-T731-1 (e9878f39) | Verifier 2026-11-12T05:59Z | L-9c3643da high, L-d9790e45 cap, C10 L-7863355d AT_LEAST restated |
| T-730 `out/T730_ROWS.csv` R-T730-1 (6143f30d) | Verifier 2026-11-12T07:58Z | the line-by-line map (coverage asserted) |

Every input is sha256-pinned in `t729_inputs.py`; `--check` rebuilds `out/T729_ENTRIES.json` and compares. One live
statement per line, by DECLARED restatement only (R-T730-1 (2)): T-735 > T-732 > T-724 > T-714 on STR.FORMWORK, T-731
> T-725 on stair formwork; the superseded forms ride on the record (`supersedes`), never summed, never picked by size.
The built formwork family equals the merged T-735 family exactly (asserted): by class AT_LEAST 40 / BLANK_NAMED 244 /
BOUNDED 32 / FIX_ROW 54; bounded 107.200712 .. 132.785507 m2; AT_LEAST 122.484697 m2. The 6 T-707 / T-714 CONFLICT
lines and the cap-0 line L-867e155d carry the T-735 one-live-form figures (412 BOUNDED 4.183916 .. 5.532116; 415
AT_LEAST 2.8938; 34A / 34D / 356 / 350 AT_LEAST 3.0528; L-867e155d 0.102019), never BLANK 'decider T-735' and never a
T-707 / T-714 form. T-724 L-ab37afa1 (ring AT_LEAST 0.115155) is KEEP / DUPLICATE: already on the candidate, not
restated.

## 2. Method (R-T729-1, every villa; module `engine/source/arch_v3075.py`)

Physical element first (ERS s.2.1): formwork = the contact area of every cast face not cast against earth, blinding,
masonry or an earlier pour (R-CONC-OWN-1); a member held on one dimension passes it face by face (R-T714-1).

- FW_WIRE RELEASE: a T-638 fix row of the merged wiring form, on its unchanged HELD blank line, valued at the merged
  CALCULATED figure (candidate only; the released default never moves); RELEASE_LOW_END keeps the column's joint faces
  HELD beside (companion), never summed.
- BOUND: 0 < low <= high, the sums of face lows / highs. AT_LEAST: lower end beside a blank line. CAP: AT_MOST beside a
  blank line (every face 0 .. x): never a quantity, never in a code total; a 0 cap is refused. NAMED: cause on the
  line, no figure.
- CONC_C10: the GB 0 .. 3.5256 range record (a 0 low is no floor, R-T724-3) becomes HELD blank with AT_MOST 3.5256
  beside; MS1-L AT_LEAST 1.213429 -> 1.213428 restated (exact reading A sum 1.213428296 floored, R-T696-1); the 4
  roof-edge pieces no line carries (R-T724-4) become NEW HELD blank STR.CONC.BEAM child lines, named, plan m2 per m of
  depth as information (never a bound).
- Totals: only STR.FORMWORK|m2, STR.FORMWORK.STAIR|m2 and STR.CONC.*|m3 move, each exactly by the changes (asserted);
  released concrete never moves; every other line byte-identical (asserted); V3.0.64 .. V3.0.74 state checks re-run.

Owner manual method vs drawing-derived method: owner = contact area per face (column perimeter x clear height, beam
sides L x (D - t) + soffit b x L, slab edges, stair soffits / risers / strings), held dimensions with the designer list;
drawing = the merged face ledgers (formwork r4 / r5 walk T-264 / T-308 / T-332) with the member's held dimension passed
face by face; moved columns floored at P_min x (least panel top - base - D_max) (R-T732-1 / R-T735-1).

## 3. Hand checks of material lines (Checker picks; m2 unless stated)

| line | V3.0.74 | V3.0.75 | hand |
|---|---|---|---|
| L-6f83fc39 COL-2F-51 (412) | blank | **4.183916 .. 5.532116** | shaft 3.5518 .. 4.90 + joint 0.5961 + edge band 0.036016 |
| L-fa037ca1 (T-732) | blank | **3.720600 .. 7.218122** | shaft 3.7206 .. 6.93 + caps 0 .. 0.0479 + 0 .. 0.240222 |
| L-867e155d BM-1F-031 side | blank (T-714 cap 0) | **0.102019 point** | 0.300055503 x (0.50 - 0.16) = 0.102018871 (see F-T729-1) |
| L-3280c42c CB2 BM-GF-055 | blank | **3.559782 .. 3.733233** | T-724 F-V714-1 soffit at the true edge width |
| FR-T638-13 L-436a0800 | blank | **5.626 released** | COL-GF-03 1.50 x (4.50 - 0.75) = 5.625 (method 5.626), joint companion 0.357774 beside |
| L-0bbf0124 parapet 1F-NW-2 | blank | **>= 2.166420 beside** | 2 x 0.30 x 3.6107 m (P1 upstand floor; all-RC high open) |
| L-fb7a6431 GB boundary (m3) | 0 .. 3.5256 bounded | **blank, <= 3.5256 beside** | 44.07 m (8.814 / 0.20) x 0.20 x 0.40 = 3.5256 gross |
| L-7863355d MS1-L (m3) | blank, >= 1.213429 | **blank, >= 1.213428** | reading A exact 1.213428296 floored |

## 4. Run of record, census, diff

RUN_SECTION

## 5. Findings, held / missing, downstream, verdicts

- **F-T729-1 (rounding, immaterial).** T-735 states L-867e155d at 0.102019 both ends; the exact figure is
  0.10201887102, so R-T696-1 (lows floor) gives 0.102018 .. 0.102019. Wired as merged (no figure is changed by the
  integrator); residual 0.000001 m2 named for the Checker.
- **F-T729-2 (fix-row method rounding).** 4 column-shaft fix rows carry the method figure (5.626 vs hand 5.625, 0.001
  m2 each, T-638 'method' column): wired as merged, residual named.
- Held: 186 + 4 named formwork lines (126 OQ-10 formed / earth-cast; member blank; drawn items), 58 + 12 caps beside,
  40 + 2 AT_LEAST beside, 4 companions HELD beside, GB boundary-column count n (M4 / Q-28), D-05 / D-26 projection
  children. Nothing VERIFIED; blank is never 0.
- Downstream: no finish, masonry, WP or earthworks line moves; formwork materials (ply / props) not in scope; rebar
  PARKED (owner 2026-11-11). SCOREBOARD v2 restated by the Lead on merge.
- Freelancer: no formwork row exists (FREELANCER_NO_ROW): NOT_COMPARABLE, no %. Verdict proposals: 54 fix rows
  ENGINE_RIGHT (calculated faces, T-638 / T-714 Gate A), 34 bounds ENGINE_RIGHT as bounds, AT_LEAST / caps HELD,
  named HELD; C10 GB cap ENGINE_RIGHT as cap (R-T724-3), MS1-L restatement rounding only.

Lesson row (ERS s.7, proposed): | 2026-11-12 | four merged pieces stated overlapping subsets of 390 formwork lines | a
wiring that reads pieces one by one can wire a superseded form or sum two forms of one line | build ONE live statement
per line by declared precedence, carry the superseded forms on the record, and assert the built family equal to the
latest merged family census before wiring (R-T729-1, every villa) | tests/t729_formwork_gate_b
(test_picking_t714_over_declared_restatement_breaks_family) | PROPOSED.

Tests (`tests/t729_formwork_gate_b`, 25): villa F729 by hand, non-Alsenan (release 4.000 / 5.625 + companion 0.300,
bound 3.200 .. 3.400, AT_LEAST 6.000, cap 0.250, named, stair 1.904 .. 2.380 / cap 0.800, GB cap 1.600 m3, stair
AT_LEAST restated 1.000001 -> 1.000000, a named child; totals by hand; beside figures never in totals; outside lines
byte-identical; mirror order; written files) and adverse (cap 0, VERIFIED, stale element / range, low > high, unit slip,
applied twice, restatement mismatch, same figure, release without companion / fix, line twice, child with a figure, cap
not the range's high, formwork action on a concrete line, held never 0); development villa (rebuild equal, family =
T-735, precedence on named lines, stale 0, coverage, inputs load; adverse stale pin, cap 0 re-entered, dropped entry,
a T-714 form picked over a declared restatement).
