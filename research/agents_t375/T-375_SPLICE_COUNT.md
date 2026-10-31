# T-375 Splice count of a run longer than the stock bar: frozen `_with_laps` vs the proposed method

Research only: `research/agents_t375/*`, `tests/t375_splice_count/*`. No frozen file, rule, knowledge file,
integration module or candidate line changed. Code: `t375_splice_count.py` (`build`, `build --check`, `routeg`).

## 1. Physical element and the arithmetic (ERS s.2.1, s.2.5)

A continuous bar run of length L longer than the stock bar S is built from N pieces (each <= S) joined by N - 1 lap
splices of length lap. The pieces reach the run only if `N x S - (N - 1) x lap >= L`, so

    N = ceil((L - lap) / (S - lap))     (L > S);   N = 1 when L <= S;   lap >= S BLOCKED
    procurement length = L + (N - 1) x lap         (installed run + lap steel; never the net quantity)

The frozen form (`engine/source/continuous_beams.py:451-455`, FROZEN, read only) counts `N - 1 = ceil(L / S) - 1`: it
splits L by S as if a lap consumed no bar length. Proved in exact rationals and tested (`tests/t375_splice_count`):

| | Statement | Evidence |
|---|---|---|
| P1 | `ceil((L - lap) / (S - lap)) - 1 = ceil((L - S) / (S - lap))` for L > S: the row's pieces form IS the owner formula (OWNER_RULE_REBAR s.2), `bbs_optimiser.split_run` and `rebar_laps_v1.lap_count_exact` | grid test against both engine functions (519 runs 11.90 .. 48.00 m x 6 laps 0.40 .. 3.00 m) |
| P2 | the frozen count is never above the correct one (a LOWER bound: it can only miss laps) | grid + boundary table: `frozen_ever_above_proposed` false |
| P3 | they disagree exactly on `S + k (S - lap) < L <= (k + 1) S`, k = 1, 2, ... (width k x lap); equivalently frozen is right only for `lap <= S - (L - S) / n0`, n0 = ceil(L / S) - 1 (T-366 s.5) | grid test both ways |
| P4 | deficit `< (L - S) lap / (S (S - lap)) + 1`; exactly 1 lap on every window up to L = S^2 / lap (180 m at 0.80 m; algebra) | bound tested on the grid to 48 m; table max deficit 1 |
| - | wherever they disagree, the frozen pieces physically do not reach the run | table column `frozen_pieces_cover_run` = NO on all 158 disagreeing rows |

## 2. Boundary table (acceptance a): `T375_BOUNDARY_TABLE.csv`

L 11.9 .. 48.0 m step 0.1 m, plus each window edge and 1 mm above it, at lap 0.40 / 0.48 / 0.64 / 0.84 m, S = 12 m:
1,481 rows, 158 disagreements, all listed in `T375_SUMMARY.json`. Windows (m) where the frozen count is 1 lap short:

| lap | k = 1 | k = 2 | k = 3 |
|---|---|---|---|
| 0.40 | 23.60 .. 24.00 | 35.20 .. 36.00 | 46.80 .. 48.00 |
| 0.48 | 23.52 .. 24.00 | 35.04 .. 36.00 | 46.56 .. 48.00 |
| 0.64 | 23.36 .. 24.00 | 34.72 .. 36.00 | 46.08 .. 48.00 |
| 0.84 | 23.16 .. 24.00 | 34.32 .. 36.00 | 45.48 .. 48.00 |

(lower edge open, upper edge closed). Spot values (match T-366 s.5): 23.80 m at 0.48: 1 vs 2 laps, 24.28 vs 24.76 m;
35.00 m at 0.48: 2 = 2 (35 < 35.04); 35.00 m at 0.64: 2 vs 3 laps, 36.28 vs 36.92 m. **Below 2S - lap (at least 23.16 m
for every lap here) the frozen method is exact**; it is wrong only for runs over about two stock bars.

Row wording correction (finding F-T375-1, text only): the row's adverse case "35 m at 0.64 m: 3 pieces, the frozen 2
refused" mixes pieces and laps: the correct result is **4 pieces / 3 laps**; the frozen form gives 2 laps (3 pieces,
reaching 34.72 m < 35 m). The test asserts 4 / 3 and refuses the frozen 2 laps.

## 3. Callers and candidate lines (acceptance b)

Static census (AST over `engine/` and `tools/`, `T375_CALLERS.json`): `_with_laps` is called ONLY in
`continuous_beams.physical_bars` (line 373, every non-link bar group, three readings 40 / 50 / 60 d), and
`physical_bars` ONLY from `generic_route._cb_model` (line 2178): route G continuous-beam items
`P-S:<id>:CB_<role>:D<d>`. Frozen-form copies: 4, each classified: the defect itself; two before / after reproductions
in `rebar_laps_v1` (T-273); `rebar_laps_v1._coupler_row`, where `ceil(L / S) - 1` is CORRECT (a mechanical coupler
consumes no bar length, owner s.6.1). No other copy in engine/ or tools/.

Instrumented route G run, this run, on Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..), conventions
V6 + M4 profile (the candidate's rule_id `URBAN_M8_GENERIC_CONVENTIONS_V6+ST7757_M4`, completeness on, as
`urban_boq_m9 arch --structural`), working head 6b9ce820, `_with_laps` / `physical_bars` wrapped in memory
(`T375_ROUTE_G_RUN.json`): 4,752 calls, 1,584 bar groups, 11 CB marks, stock 12 m, lap 40 / 50 / 60 d; longest run
**8.483 m** (CB11 bottom ø18); runs over the stock **0**; readings that differ **0**; scenario kg moved at each lap
reading **0.000 / 0.000 / 0.000 kg**. No TOP_THROUGH group reaches `_with_laps` on this profile (role not printed).
Residual named: the main chat's 2026-10-24 instrumentation (engine head 768ff1d, V5 and V6) recorded 3,564 calls and
8.708 m; the head and convention sets differ and the cause of the 0.225 m / 1,188-call difference was not traced here.
It cannot change the result: both are below 12 m, where the two formulas return L unchanged for ANY lap.

Candidate lines (`T375_CANDIDATE_BINDING.json`): all **105** continuous-beam route G lines of the candidate (T-297
extract, V3.0.16 = V3.0.17 rebar) are `NOT_APPLICABLE_WITH_EVIDENCE` with no quantity (SUPERSEDED by the T-149 hand
ledger since V3.0.3); none of the steps V3.0.17 .. V3.0.28 (`arch_v3017.py` .. `arch_v3028.py`) names a CB /
continuous-beam token; T-373's V3.0.27 lap-bearing set holds 0 CB lines. **Effect on the candidate: 0.000 kg, every
lap reading; on released V2.9 + route G: route G CB steel PROVISIONAL, 0.000 kg moved.** Limitation: V3.0.28 itself
was not rebuilt in this run; the Checker can confirm on its own reproduction by filtering element ids `:CB_`.

## 4. Rule proposal R-T375-1 (acceptance d; every villa; provenance T-273 D-T273-01, T-366 s.5, T-375)

The number of lap splices of a continuous run is `ceil((L - S) / (S - lap))` (= pieces - 1 with pieces
`ceil((L - lap) / (S - lap))`), 0 for L <= S, BLOCKED for lap >= S, HELD (never 0) when L > S and the lap is HELD.
The form `ceil(L / S) - 1` is valid ONLY for splices that consume no bar length (mechanical couplers). The method
version already exists: `CONTINUOUS_BEAM_LAPS_V2` = `engine/source/rebar_laps_v1.with_laps_v2` (T-273, merged
42e32cf3, unwired, not in the rules manifest). **No third copy is proposed.** Wiring (lane I, when a route G CB line
is ever booked again): replace the frozen call by a new continuous-beam method version that calls `with_laps_v2`,
register `CONTINUOUS_BEAM_LAPS_V2` in the method registry, and keep `continuous_beams.py` byte-identical. Until then
the defect is latent: 0.000 kg on Alsenan, and any villa with a continuous-beam run below 2S - lap is unaffected.

## 5. Engine vs freelancer; verdict proposals

No BOQ line moves (0.000 kg candidate, 0.000 kg route G). The freelancer's reinforcement is a kg/m3 lump with no lap
row: RULE_DIFFERENCE, no %. Verdict proposals: frozen `_with_laps` ENGINE_WRONG for runs inside the P3 windows
(latent, 0 effect on Alsenan); F-T375-1 row text (pieces vs laps) for the Lead.

## 6. Lessons-register row (proposed, ERS s.7)

| Lesson | Rule | Test |
|---|---|---|
| A splice count must subtract the length each lap consumes; `ceil(L / S) - 1` counts stock joints, which equals the lap count only below 2S - lap. Name pieces and laps separately in any acceptance text. | R-T375-1 | tests/t375_splice_count (normal: 20 m / 23.52 m agree; adverse: 23.80 m at 0.48 and 35 m at 0.64 refuse the frozen count) |
