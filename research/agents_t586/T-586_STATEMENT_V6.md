# T-586 reconciled-quantities statement V6 (research, unwired; for the 12-13 Nov milestone)

Worker 3 (lane I, non-candidate, integration dependency, backlog-permitted), 2026-11-07. Files: `t586_adapters.py`
(R-T586-1), `t586_build.py` -> `out/RECONCILED_STATEMENT_T586.json` / `.md` (`--check` rebuilds identical),
`tests/t586_statement_v6/` (25). The T-579 builder is imported read only; the build first rebuilds statement V5 and
refuses to run unless it equals its committed JSON and markdown, then checks every V5 key / section is carried
unchanged except the pads label. Sources sha256-pinned (T-571, T-574, T-575, T-577 outputs, V8, V5). No drawing,
workbook or client data; no candidate, rule, knowledge or registry file; no quantity moves; nothing released. Sign:
reference - engine (the sources print ours - his: negated once). T-576 (TODO) and T-578 (READY) not merged: pending.

## New sections (every one re-adds from its source JSON, residual 0; no % anywhere)

| Section | Unit | Reference | Engine valued | Net | Classes (Checker) |
|---|---|---|---|---|---|
| T-571 lintel count | nr | 54 IMPLIED (his 54 openings through the owner rule; he has no lintel row) | 60 AT_MOST (16 established) | -6 | per length 1.20 -3, 1.50 -3, 2.50 -1, 4.00 +1; ENGINE_ONLY 7 + W17 UNRESOLVED; width reads D-GF-03 / D-GF-09 RD, P-GF-01 UNRESOLVED (0 net, per length +-1); lm beside 84.9 vs 91.5; lintel figure NOT_COMPARABLE (NO_ROW) |
| T-574 rooms | lm | 282.85 | 197.278592 | +85.571408 | RD 43.62, ER 32.082629, UNRES 9.693234, TOL 0.175545; outline terms 282.85 vs 276.159097 = +6.690903 (2.37 %) beside deduction terms 78.880505; PARTIALLY VERIFIED 1 / 11 outlines; net 30.25 % NOT a verdict |
| T-574 stairs | lm | 29.87 | 12.15 | +17.72 | HELD 17.009049 (flight lower bounds, highs open), UNRES 0.710951; rooms + stairs = candidate 209.428592 |
| T-574 pieces | nr | 96 | 0 | +96 | RD (unit: pieces never converted to lm) |
| T-574 outdoor | lm | 81.32 | 0 (no line) | +81.32 | UNRESOLVED scope (Lead completeness item) |
| T-577 m2 | m2 | 5.10 (area cells only) | 18.0382 | -12.9382 | ER -11.6888, RD -1.250, TOL +0.0006; his 21.70 count x length cells in the area column = NOT_COMPARABLE UNIT block |
| T-577 lm | lm | 21.70 (his count x length cells) | 56.83 | -35.13 | ER -49.13, RD -4.90, UNRES +18.90 (ext door steps 7.70; E1 step-lm 11.20 ENGINE_OMISSION PLAUSIBLE -> UNRESOLVED, F-T586-1) |
| T-577 nr | nr | 11 | 67 | -56 | ER -47, RD -9 (ext doors 6 / 6 AGREE beside) |

T-575 (beside, t): six V8 REBAR_OMISSION rows, 4 HELD_RANGE 0.733792 .. 1.161932 t + 2 HELD_BLANK (DOME-3 no
structural drawing; lift walls h not printed, kg(h) beside), valued 0; manifest rows, not candidate lines, so no V5
column moves. EXPECTED after those rows exist: T-560 G5 held 1.772952 .. 2.605603 t, residual vs his TYPED_LUMP 3.90 t
1.294397 .. 2.127048 t (no %; the B4 ring's G5 / G3 attribution UNRESOLVED).

Pads (F-C-T579-1): V5 T-572/measured-footing_pads_and_straps (67.0665 vs 67.6945 m3, -0.628) now carries
`cause_split: not split` (its split stays in V4 T-551/footing-line); nothing else in V5 changed (asserted).

## R-T586-1 (proposed, every villa; module docstring)

(a) no row, no %: NO_ROW is NOT_COMPARABLE, an implied figure is FREELANCER_IMPLIED, nr only, no %; (b) a count x
length cell in an area column never enters an m2 reference, it closes his total as a UNIT block and is compared in lm;
(c) HELD_RANGE is low .. high valued 0, never a point, and a manifest-row range stays beside; (d) t at the boundary,
kg refused inside a t block; nr / lm / m2 apart; (e) AGREE terms must cancel inside their group and sit beside;
ENGINE_OMISSION held PLAUSIBLE maps to UNRESOLVED by name; an unmapped verdict is refused; (f) gross vs gross beside
the deduction terms for a reference that deducts nothing.

## Findings

- F-T586-1: the T-577 E1 step-lm ENGINE_OMISSION (11.20 lm) is printed UNRESOLVED until the Checker confirms it
  from the drawing (his verdict: PLAUSIBLE).
- F-T586-2: T-575's report puts the B4-tagged west ring in G5 / G3; T-560's omission row sits in G5 only: the
  expected-after view adds it to G5 and labels the attribution UNRESOLVED (no split of his lump).
- Bulkhead paint -27.9345 m2 (F-T579-3) stays UNRESOLVED as in V5 (no Checker hand measure yet).

Lesson row proposal (ERS s.7): | 2026-11-07 | his marble 'm2' total held 21.70 of step / door-step lengths and his
lintel figure did not exist | a statement section is built from the reference's own cell classes: area cells only in
m2, count x length in lm, an absent row as NOT_COMPARABLE and an implied figure labelled, never a % | R-T586-1 (a) / (b)
(every villa) | tests/t586_statement_v6 | PROPOSED |
