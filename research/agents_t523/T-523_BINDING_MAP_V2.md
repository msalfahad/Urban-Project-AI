# T-523 Material binding map V2 (stage, freshness, one ceiling per purchasing group)

Lane I, worker 3, 2026-11-05. Research only, unwired: `t523_binding_map_v2.py` + `tests/t523_binding_map_v2` (19
tests). The merged T-496 map, every producer table and every producer module are read, never edited; no candidate,
released (V2.9 + route G), rule, knowledge or registry quantity changes. Inputs sha256-pinned (T-496 module, T-518
module, V3.0.57 line index, T-511 census, T-514 producers). Rebuild: the tests run `run()` and assert every figure
below; no committed output file (research scripts run through the package tests only).

## 1. Physical element

Per installed element: INSTALLED (area x thickness x per-m3, area / coverage, area x rate; never a loss), each LOSS as
its own key with its source (unsourced: HELD, figure beside, never stacked), PROCUREMENT = installed + sourced losses
before rounding; pack rounding ONCE per purchasing group (one product, one pack, one villa).

## 2. Rules (every villa)

- R-T523-1 PURCHASING GROUP (proposed, provenance owner Q-45 / Q-78 / 2026-11-02 pack rules, UPC-ADHESIVE-001
  'ceil per purchasing group', owner B3 project-level rounding, T-518 R-T518-2; no new factor): 50 kg cement = every
  site-mixed cement : sand layer of every trade; 20 kg adhesive = T-455 + T-495 rows; 25 kg AAC glue = T-453 white
  rows; loose sand has no pack record (fractional m3, no ceiling). To-buy = ceil(sum / pack) once, only when every
  member is known; otherwise HELD with an AT_LEAST known part (+ one ceiling of it, informative). A member with a
  known installed and a HELD loss contributes its installed (a loss is never negative), never a loss figure. A
  pre-rounded part is refused. Sub-group ceilings are never summed.
- R-T523-2 STAGE FROM THE PRODUCER: re-derive installed from the producer's stated inputs; ratio 1 -> INSTALLED;
  1 + f with f a sourced in-scope factor -> MIS_STAGED, split into installed / loss / procurement; other ratio ->
  UNRESOLVED_STAGE (fail). Not derivable -> the producer code record (STAGE_CODE, file:line).
- R-T523-3 FRESH ON THE CANDIDATE: every bound line re-read on V3.0.57 (V3.0.58 adds 5 roof WP lines, no host).
- R-T523-4 ONE PRODUCER PER KEY (line, material, kind, stage); READ chain T-489 <- T-454 must agree; options never summed.
- R-T523-5 HELD NEVER 0.

## 3. Result (0 failures)

1,202 V1 bindings read, 0 unread -> 1,208 V2 bindings: SAME 318, RELABEL 821 (V1 'THEORETICAL' = INSTALLED by the
producer's code, value unchanged; T-455 layout tile count = PROCUREMENT net of boxes / spare, cuts inside by UP-CER-010),
NO_LINE 60 (lintels, B9-02), MIS_STAGED 3 rows -> 9 bindings.

**Mis-staged keys (D-T518-2), T-495 outdoor bed options (HELD, bounds only, per option):**

| line / option | V1 bound 'INSTALLED' m3 | V2 INSTALLED | LOSS 5 % (Q-45 B, ASSUMED - OWNER-APPROVED) | PROCUREMENT |
|---|---|---|---|---|
| pool deck 6.548912 m2, porcelain | 0.206291 .. 0.275054 | 0.196467 .. 0.261956 | 0.009823 .. 0.013098 | 0.206291 .. 0.275054 |
| porch 10.6785 m2, porcelain | 0.336373 .. 0.448497 | 0.320355 .. 0.427140 | 0.016018 .. 0.021357 | 0.336373 .. 0.448497 |
| porch 10.6785 m2, marble | same as porcelain (one bed, alternative finish) | | | |

No other key is mis-staged: T-453 / T-454 / T-489 / T-455 / T-495 adhesive re-derive to ratio 1.

**Stale on V3.0.57 (21 bindings, 7 T-453 lines; figures BESIDE):** L-76a4 (2F 0.20 black, HELD), L-a6ee (2F-W05,
HELD), L-9056 (0.15 white 25.525 m2, HELD), L-e90c (0.20 white 21.476 m2, HELD), L-bbb8 (0.20 white range, HELD),
L-e1e0 (HELD), L-adb3 (re-netted 21.5261 -> 8.595 m2). T-511 caught the 2 cement lines; the glue and block figures
were still live in V1.

**Before / after per key (blockwork, the T-498 slice):** black blocks VERIFIED-NET -270.75 nr (L-76a4); black mortar
PROVISIONAL 1.588929 -> 1.269444 m3, cement 12.711432 -> 10.155552 bags (= T-511 / T-498 stage); AAC glue VERIFIED
116.703 -> 20.061 kg, PROVISIONAL 112.8725 -> 23.535 kg (229.5755 -> 43.596 kg known figures); glue group HELD, AT_LEAST
35.42625 .. 36.19665 bags (figures 1.74384 + fresh range lows / highs 33.68241 .. 34.45281), >= 36 .. 37 bags.

**Project cement (50 kg, villa group):** installed known part >= 125.126280 .. 164.620992 bags (unchanged; reproduced
row by row from T-511 + T-514 and equal to the T-514 print). Procurement known part V1 >= 120.661015 .. 162.130462 is
BELOW the installed known part because the 10.155552 masonry bags (loss HELD) were dropped; V2 >= 130.816567 ..
172.286014 bags (+10.155552). Whole bags: ONE ceiling >= 131 .. 173; summing trade ceilings (tile bed 105 / 145, stair
11, walk 6 / 8, masonry 11) would print 133 .. 175 (+2 bags). Status HELD (plaster, screeds, 20 stair lines, 2
masonry lines open): no to-buy figure. Tile adhesive group: HELD, no known figure (every T-455 row HELD).

## 4. Findings

- F-T523-1 (D-T518-2 corrected): 3 T-495 bed rows split; the installed share is 4.76 % below V1 (1 / 1.05).
- F-T523-2 STALE MATERIAL FIGURES beyond cement: 185.98 kg of AAC glue (81 % of the V1 known glue) and 270.75 black blocks
  sit on lines HELD since V3.0.55 (T-488); a wiring reading T-453 r2 / T-496 V1 releases them.
- F-T523-3 PROCUREMENT KNOWN PART BELOW INSTALLED (T-511 / T-514 project print): a loss-HELD member must contribute its
  installed to AT_LEAST; the corrected floor is 130.816567 .. 172.286014 bags.
- F-T523-4 (F-T518-3 closed by rule): one ceiling per villa group; trade ceilings summed overstate by 2 bags today.

## 5. For the T-498 resume

Read blockwork materials from the V2 fresh figures only: blocks, black mortar 1.269444 m3 / 10.155552 bags (fractional,
joins the villa cement group, no masonry-only bag ceiling), glue 43.596 kg known + 33.68 .. 34.45 bags range lows; L-9056
/ L-e90c / L-bbb8 / L-76a4 / L-a6ee HELD in the material lines, never 0.

## 6. Freelancer / verdict

Freelancer workbooks carry no cement / sand / glue rows: RULE_DIFFERENCE (scope), no numeric verdict.

## 7. Lessons row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-05 | a map bound a folded 5 % as installed, kept glue / block figures of lines HELD two versions later, and a procurement floor fell below the installed floor | stage taken from labels, freshness checked per trade, loss-HELD members dropped from procurement | R-T523-1..5 (every villa): stage from the producer's arithmetic, fresh on the candidate of record, one ceiling per villa group, loss-HELD contributes installed | tests/t523_binding_map_v2 (K523 by hand; adverse: unsourced loss, held installed, pre-rounded, two producers, chain divergence, 7 % ratio, stale class / net) | proposed |
