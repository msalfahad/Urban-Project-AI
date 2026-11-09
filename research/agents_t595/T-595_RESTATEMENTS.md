# T-595 Structural restatement versions (dome-ring side bars; F10 + F footing bound)

Worker 1 (lane S), 2026-11-07, branch `agents/task-T-595`. Research only: no engine module, candidate line, released
line, rule file or method version file changed; T-583 and T-572 rows and files untouched; nothing valued or released.
Development villa, not an accuracy claim. ERS s.2 - 4, s.7; Q-71, OWNER_RULE_REBAR_2026-10-24, R-T583-1 .. 6,
R-T572-1 .. 4, owner 2026-11-02 RFI re-review (4) and its acceptance of the S02 range.

## 0. Sources (own read this run)

Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523..., same file as T-575 / T-583), p.7 DETAIL OF DOME,
both ring cuts rendered at 600 dpi into `.work/private` only. Each cut draws: 3 top dots (label 3 d16), 3 bottom dots
(3 d18), a closed link (8 d8 / m) and **two dots on the left vertical face and two on the right face at two levels**;
the leader '2 d14 / 20cm' runs through the lower level (both of its dots); ring depth 'AS PER ARCH' (not printed).
This independently confirms the Checker's T-589 read (F-C-T583-1). Footing dimensions: T-233 / T-572 committed basis
texts and the owner S02 text.

## 1. Physical elements

(1) The d14 side bars of the dome ring: longitudinal bars on both vertical faces of the ring section, two levels, over
the in-bay length. (2) Footing F10 / F at 10A5: one drawn plan element with three owner-accepted readings.

## 2. Restated rows (new versions)

| Row | Before (version) | After (version) | Hand check |
|---|---|---|---|
| East dome ring low (DETAIL) | 0.122518 t (T-583 V1) | **0.144290 t** (V2, R-T595-1) | side bars 2 -> 4 x d14 x 8.99725 m in-bay x 1.209877 kg/m = 21.771 -> 43.543 kg (+21.771) |
| West dome ring low | 0.063897 t (B4 reading) | 0.063897 t (unchanged) | DETAIL reading low rises 102.94 -> 121.29 kg, still above the B4 reading 63.90 kg: row low = smaller reading (R-T575-5) |
| Bounded rebar rows low | 0.767783 t | **0.789555 t** | sum of the four rounded row lows (T-583 convention); board text 0.789554 = 0.767783 + 0.021771 rounded parts, 1 g rounding |
| Highs | HELD | HELD | ring depth (further side-bar rows, link path), hooks, laps, anchorage by name; bounded part 1.164174 t unchanged |
| F10 + F concrete (L-164ae9d3) | 2.176 .. 2.275 m3 (T-572 V1, reading A low) | **1.960 .. 2.275 m3** (V2, R-T595-2) | 2.80 x 1.40 x 0.50 = 1.960; + 0.90 x 0.80 x 0.30 = 0.216 -> 2.176; 3.25 x 1.40 x 0.50 = 2.275 |
| B10 footing line bounded part | 7.8445 .. 13.9613 m3 | **7.6285 .. 13.9613 m3** | -0.216 on the low; family total still not stateable (boundary pad count, Q-28 A) |

Status: S02 range ESTIMATED, owner PROVISIONAL, never VERIFIED; the T-572 reading-A low was not strict (an accepted
scenario, F10 alone, lies below it).

Scenario consistency (owner 2026-11-02): concrete low = S02-1 F10 alone, high = S02-3 drawn outline; the excavation
low (4.350 m2 x 1.50 = 6.525) and blinding low (4.350 x 0.10 = 0.435) already use the S02-1 in-plot plan; blinding high
0.590 rests on the T-233 readings (per-scenario split not measured: SCENARIO_SPLIT_OPEN); SB1 in footing 0 .. 0.385 and
the PIT-F10F backfill (UNBOUNDED) unchanged; F10 reinforcement / formwork per scenario: open (T-560 / T-474 owners).

## 3. Freelancer, verdicts

Rebar: TYPED_LUMP 44.19 t (T-560): NOT_COMPARABLE, no %. Dome rings: ENGINE_OMISSION -> bounded HELD (low corrected).
F10 + F: his 1.960 m3 moves from BELOW_DRAWN_LOWER to WITHIN (it equals the S02-1 F10-alone reading): proposal
RULE_DIFFERENCE / interpretation (he takes F10 alone), not ENGINE_RIGHT; no % on a held line.

## 4. Rules, tests, lessons

R-T595-1 / R-T595-2 in `t595_rules.py` (every villa). `tests/t595` (19): K595 ring 6.48 m d12 side bars 1 face 11.52 kg
/ 2 faces 23.04 kg, three levels; footing pad 1.728 / + second pad 2.008 / outline 2.088 m3; adverse: single-face
reading where two are drawn refused, dropped level refused, label conflict HELD, mm refused, non-strict low / high
refused, missing scenario never 0, mixed scenario view refused; development rebuild = committed, V1 rows byte-equal,
T-572 file untouched. Run `.work/venv/bin/python -I research/agents_t595/t595_alsenan.py --check`.

Lessons row (ERS s.7, the T-589 row adopted on merge plus): | 2026-11-07 | a held bound kept the low of one reading
after the owner accepted a wider scenario set | a bound was not re-derived when the accepted interpretations changed |
low / high = min / max over every accepted scenario; a stated low above any accepted scenario is refused; one scenario
across all families of an element | R-T595-2 (every villa) | tests/t595 | PROPOSED |
