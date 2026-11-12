# T-731 ST-01 MS1-L coherent reading (F-T725-1) and ST-01 flights / landings re-measured (research, unwired)

Worker 1, lane S, 2026-11-12, branch `agents/task-T-731`. Files: `t731_rules.py` (R-T731-1 / R-T731-2, every villa),
`t731_alsenan.py` (builder; committed inputs sha256-pinned in `PINS.json`; drawing facts as constants),
`out/T731_LEDGER.json`, `out/T731_REMEASURE.md`, `tests/t731_stair_coherent` (19 tests). No engine, candidate, rule /
knowledge version, registry or frozen file changed; nothing wired, released or VERIFIED. Candidate of record V3.0.73
(line index of T-722): the 4 lines below are still HELD blank there.

Own drawing read this run (decoded by the wrapper into `.work/private` only): Drive "Alsenan chalet project" /
"ST7757 dxf.dxf" (sha256 9f9d1179 = manifest; `t352_extract.py` re-run, every T-352 length reproduced; riser lines by
handle) and "p7757_arch_sheet10.pdf" (section A-A, rendered: level marks +0.30 / +1.00 / +5.50 / +9.70, dimension 450
and the dimension **320 from the +0.30 mark to the top (finish) line of the GF half landing**).

## 1. Physical element and readings (ERS s.2.1 / 2.2; R-T731-1)

ST-01 GF -> 1F: MS1-L straight flight, MS1-T winder turn, half landing MS1-LD, MS1-U flight. Printed levels: GF +1.00,
half landing **+3.50 = 0.30 + 3.20** (section A-A), 1F +5.50. The ST plans print no level at ST-01 (no level text within
5 m of 45A on p.4 or 646 on p.5), so every reading's rise rests on the section's levels; counts come from one source.

| Reading | Count source | Segments (n x r = printed rise) | State |
|---|---|---|---|
| A | section A-A (owner Q-46 A) | +1.00 -> +3.50: 15 x 0.166667 = 2.50; +3.50 -> +5.50: 12 x 0.166667 = 2.00 | COHERENT |
| B | ST p.4: 12 lines 45A .. 25E + 2F6 / 2F4 / 2F5 + 2F3 + 12 lines 25B .. 459 | 16 x **0.15625** = 2.50; 12 x 0.166667 = 2.00 | COHERENT |
| B28-uniform (T-725 "coherent B") | ST p.4 count 28 at 4.50 / 28 | lands at +3.571429 against the printed +3.50 (miss +0.071 m); carries the VERIFIED MS1-U at 0.160714 instead of 2.00 / 12 | REFUSED |
| B27-as-recorded (T-258 / T-281 / T-352 / T-711) | count 28, rise 4.50 / 27 | 28 x 0.166667 = 4.667 m in a 4.50 m storey | REFUSED (R-T725-1) |
| P (architectural GF plan 10 + 4 + 11) | arch plan | 11 MS1-U risers against 12 drawn on ST p.4 and cut in section A-A | REFUSED (R-T731-1 (d); Q-46 A: a check) |

## 2. Restated on V3.0.73 (R-T731-2: a low is never raised; highs named old -> new)

| Line | Piece | Before | After |
|---|---|---|---|
| L-7863355d STR.CONC.STAIR m3 | MS1-L + winders + turn | AT_LEAST 1.213429; B sum 1.400927 (T-725: 1.383119) | AT_LEAST **1.213428** (directed floor of the exact 1.2134283; T-711 printed half-up, -0.000001 rounding only); B sum 1.366662 |
| MS1-L concrete high (beside) | side O x 1.20 | 1.054813 (B27) / 1.037005 (B28u) | **1.023763** m3 |
| L-9c3643da STR.FORMWORK.STAIR m2 | MS1-L well side | BOUNDED 0.679193 .. 0.854426 | BOUNDED 0.679193 .. **0.843465** |
| L-d9790e45 | west wall + well-end junction | BLANK, cap 0.873917 | BLANK (SEQ), cap **0.862807** |
| L-ffd491ad | risers + soffit + winder turn | AT_LEAST 7.678894 (B readings 8.662885 / 9.124142) | AT_LEAST 7.678894 (B readings 8.540233 / 9.008873) |
| MS1-L soffit highs (lane A input, beside) | true O / D | 4.464083 / 4.002826 | 4.436732 / 3.968092 |

No floor rises, no released line moves (released stair formwork 36.927436 m2 unchanged). Componentwise minimum 1.209143 -> 1.205928 mixes readings: information only, never a bound.

## 3. Re-measure for the Checker (own read by handle; residual vs ledger)

| Piece | Own | Ledger | Residual | Ledger state |
|---|---|---|---|---|
| MS2-LD-W +7.516 | p.5 5E3 -> 5E2 1.300 x 632 -> 5C0 1.150 x 0.16 = 0.239200 | 0.239200 | 0 | DRAWING-CONFIRMED |
| MS2-LD-E +7.684 | p.5 5E2 -> 5D4 1.200 x 62F -> 5C0 1.200 x 0.16 = 0.230400 | 0.230400 | 0 | DRAWING-CONFIRMED |
| MS1-LD +3.50 | p.4 25A -> 296 1.200 x 25B -> 279 1.200 x 0.16 = 0.230400 | 0.230400 | 0 | VERIFIED |
| D1 steps +0.30 -> +1.00 | p.3 1C7 / 1C6 / 1C5 / 1C4 at 0.300, lane 1C3 -> 15F 1.200, r 0.175: 0.126000 - wedge 0.025714 = 0.100286 | 0.100286 | 0 | DRAWING-CONFIRMED |
| MS1-U / MS2-L / MS2-U | 12 / 12 / 11 drawn lines at 0.300 by handle (ledger), heads 0.200 / 0.150 / 3.100 to the beam faces | T-258 basis | geometry AGREE | VERIFIED |
| MS1-L / MS1-T | 12 lines 45A .. 25E (A from 26C, 10 lines), turn region 1.300 x 1.150, winders 1.2587 / 1.6263 / 1.2587 / 1.1500 | HELD | geometry AGREE | HELD |

MS2 1F levels: section 13 + 12 = 25 over 4.20 with no printed intermediate level: uniform 0.168 is coherent (R-T731-1).
"T 16" is taken from owner Q-47 A; its text pair was not found next to the ST-01 panels in this read (only 768 / 769 on
p.5, outside the stair): stated, not re-proved here.

## 4. Findings, verdicts, lesson

- **F-T731-1** (R-T731-1): T-725's "coherent B" (4.50 / 28 uniform) misses the printed half landing by 0.071 m and
  re-rises the VERIFIED MS1-U; the coherent structural reading is 16 x 0.15625 then 12 x 0.166667. Highs only move.
- **F-T731-2**: the arch-plan reading is refused twice (Q-46 A; MS1-U count against two drawings).
- **F-T731-3**: the ST plans print no stair level: reading B's levels are architectural (levels are physical facts).
- **F-T731-4**: T-711 printed the L-7863355d floor half-up (1.213429 > exact 1.2134283); R-T696-1 floors it to 1.213428.
- Who is right: freelancer has no MS1-L-specific row (stairs as one lump, T-184): NOT_COMPARABLE, no %. MS1-L stays HELD
  (C-ST-4, owner 2026-10-22 18:00 (4)); no owner question (ERS 2.7 not met: the drawings bound both readings).
- Lessons row (ERS s.7, proposed): 2026-11-12 | a "coherent" uniform rise still missed a printed half landing | the
  rise was taken over the storey, not between printed levels | rise per segment between printed levels, counts from one
  source (R-T731-1, PROJECT-INDEPENDENT) | tests/t731_stair_coherent test_adverse_uniform_rise_missing_a_printed_landing_refused | PROPOSED.
