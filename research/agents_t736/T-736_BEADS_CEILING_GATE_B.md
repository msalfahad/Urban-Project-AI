# T-736: BEADS + CEILING ROUND 3 integration package, ARCH_TAKEOFF_V3.0.76 (lane I, hubs H2a / H1R + one Checker record)

Worker 3, 2026-11-12. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.75 (T-729, Gate B
PASS, merge 05ca1a46, BOQ_FAMILY_MASTER 1.76.0); released default V2.9 + route G untouched; nothing released, nothing
VERIFIED. No drawing, workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (Checker-merged / Checker-issued only, stale 0)

| source | merge / record | Checker | wired as |
|---|---|---|---|
| T-728 `out/T728_BEAD_RESTATEMENT.json` R-T728-1 (73 interior arrises) | 80e27c10 | Verifier 2026-11-12T03:48Z Gate A PASS | 14 NEW FIN.PLASTER.BEAD lines (9 BOUND, 5 AT_LEAST) |
| T-727 `out/T727_VOIDS_CLOSED.json` R-T727-2 | 8ea912b5 | Verifier 2026-11-12 ~02:00Z Gate A PASS | L-35341ff2 EXCLUDED DUPLICATE_FACE of L-43bf1f86 |
| T-730 `out/T730_ROWS.csv` (map: H2a 73 live T-728 rows, H1R 1 row) | 6143f30d | Verifier 2026-11-12T07:58Z Gate A PASS | line-by-line map |
| Checker record DG-98cbadebaecc5ede (board `docs/agents/verdicts/V3.0.74/DOWNGRADES.json`, board commit 2d28645c; extract `in/DG_98cbadebaecc5ede.json` asserted equal to the board record) | T-734 pack 3d8185fe | Verifier 2026-11-12T15:06:49Z (run token 20261112T135228-451-21809) | L-636fd3ff RELEASED -> HELD at the record band |

Every input is sha-pinned in `t736_inputs.py` (`--check` rebuilds `out/T736_ENTRIES.json`). The record is read from the
board record file, never re-derived (L-T748-1: the V3.0.75 index had not applied it; the line now carries it).

## 2. Method (R-T736-1, every villa; module `engine/source/arch_v3076.py`)

- Physical element first: a corner bead is the steel angle on a convex plastered arris, exposed length only (OD-V3B-8,
  G1 to the finished ceiling). Owner manual method: every convex arris (external corners, door / window jambs and heads,
  wall ends) x exposed height, once per arris, m.l. Drawing-derived method: the merged T-697 / T-728 arris ledger by
  handle, each arris its own measured length; arches, curved openings and undrawn heads HELD blank by name.
- BEAD_ADD: one line per HELD FIN.PLASTER host (one per host, an arris once, never under two hosts). Every arris
  measured -> HELD BOUNDED sum(lows) .. sum(highs). Any arris blank -> the line is HELD blank with the measured
  arrises' lower-end sum beside as AT_LEAST (an unmeasured arris only adds, so no closed range is formed). The host's
  m2 bound is never turned into m.l (F-T728-1); a held host never yields a released bead; the host must be the line
  the map bound (item, element, unit, HELD, range to 1e-6) or the run stops. The bead line's open question is the host's
  current question as the candidate carries it, plus the blank arrises.
- New item code FIN.PLASTER.BEAD (lm, trade PLASTER, subtrade CORNER_BEAD) for family B4-09 (register ruling: corner
  beads -> plaster); `boq_line.py` is not edited (make_line takes the item names); B4-09 takes the code in 1.77.0.
- CEIL_EXCL: a HELD blank ceiling line whose face is inside a RELEASED line of the same code -> EXCLUDED_WITH_REASON,
  DUPLICATE_FACE of the named owner (asserted RELEASED, same code / unit). Never valued, never 0.
- DG_HOLD: the record must name the line, bind its content (LINE_CONTENT_V1 sha256 = the V3.0.75 line), equal its
  engine_qty, state HELD; the band is the ONE band its reason prints (two bands = refused). Released -> HELD only.
- Totals: only FIN.PLASTER.BEAD|lm, FIN.CEILING|m2 and FIN.WP.ROOF|m2 move, each exactly by the changes (asserted);
  every other line byte-identical (asserted); V3.0.64 .. V3.0.75 state checks re-run on the result.

## 3. Lines (evidence status per WORKFLOW_CONTROLS s.5: every line HELD or EXCLUDED; nothing VERIFIED)

| line | host / what | V3.0.75 | V3.0.76 | hand (arris lengths, m) |
|---|---|---|---|---|
| L-3f739ef6 | GF_15 plaster (HELD 66.52899) | - | **28.85 .. 28.85 m.l** | 7 arrises (T-728) |
| L-768a147c | GF_04 (HELD 34.33 .. 43.78, T-717) | - | **10.50 .. 10.50** | D-GF-03 5.3 + D-GF-04 5.2 |
| L-c446c784 | ST_1F | - | **7.92 .. 7.92** | 1 arris pair 7.92 |
| L-cf7c0b342 | ST_2F | - | **7.58 .. 7.78** | own held bound (pier returns 0.379 .. 0.389, F-T728-3) |
| L-23c35b30 | 2F_03 | - | **10.50 .. 10.50** | 2 arrises |
| L-d61b82b6 | 1F_04 | - | **17.30 .. 17.30** | T-728 |
| L-375cb0fc | 1F_13 | - | **44.75 .. 44.75** | T-728 |
| L-ad606e88 | 2F_01 | - | **14.05 .. 14.05** | T-728 |
| L-40fd6512 | 1F_01 | - | **24.00 .. 24.00** | T-728 |
| L-ec2092fd | 1F_10 | - | **blank, >= 5.30 beside** | arch A-1F-01 blank (T-313) |
| L-54081b38 | 1F_11 | - | **blank, >= 33.95 beside** | W17 room side blank (curved) |
| L-775120ed | GF_08 | - | **blank, >= 64.8228 beside** | W03 room side + OP-003 head blank |
| L-752cd530 | ST_GF | - | **blank, >= 19.16 beside** | OP-020 head blank |
| L-905765ed | GF_01 (HELD 47.949844 .. 66.249856, T-717) | - | **blank, >= 5.40 beside** | arch A-GF-01 blank (D-45) |
| L-35341ff2 | ceiling over the light well | HELD blank | **EXCLUDED (DUPLICATE_FACE of L-43bf1f86 51.0496 m2)** | T-727 s.3 |
| L-636fd3ff | +9.70 roof membrane | RELEASED 115.832 m2 | **HELD 115.656474 .. 115.813974 m2** | record: 146.5320 - 2 x 15.359013 = 115.813974; 146.3745 - 2 x 15.359013 = 115.656474 |

Hand reconciliation (m.l): BOUND 28.85 + 10.50 + 7.92 + 7.58 + 10.50 + 17.30 + 44.75 + 14.05 + 24.00 = 165.45 (high
+0.20 = 165.65); AT_LEAST 5.30 + 33.95 + 64.8228 + 19.16 + 5.40 = 128.6328; 165.45 + 128.6328 = **294.0828 = T-728
interior low exactly** (high 294.4828: the 0.20 on ST_2F and 0.20 on a GF_08 arris; the GF_08 one sits on an AT_LEAST
line, its high open). 73 arrises once each, 6 blank: A-1F-01, A-GF-01, W03, W17, OP-003, OP-020.
Roof band by hand: pi x 2.2110915^2 = 15.359013 per dome; 146.532000 - 30.718026 = 115.813974; 146.374500 - 30.718026 =
115.656474 (the record's band; the released 115.832 used 105-chord polygons 15.349849, under-deducting 0.018329).

## 4. Run of record, census, diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded by the wrapper into the private folder only: own fresh t167 `v304_run.py` (19m46s) ->
`v3076_run.py` (exit 0, 12m42s): every earlier version re-run and asserted by its own wrapper (V3_0_74 bea5be02, REGION
CHECK PASS), **V3_0_75 a1eba08f (asserted = the T-729 run of record by its line index) -> V3_0_76 9b35725c**, 5,173
lines; replaced 2, added 14, outside 5,157 byte-identical (asserted). Diff vs V3.0.75: CHANGED 2, ADDED 14, SAME 5,157.
vs released V2.9 + route G: NOT_IN_RELEASED 3,581 (+14), QUANTITY_DIFFERS 1,054, SAME_QUANTITY 538 (unchanged).
Census `t479_registry_census.py` (verdicts V3.0.44 b3b08dd7, downgrades 81732639): on V3_0_75 it reproduces
`research/agents_t729/out/LINE_INDEX_V3_0_75.json` byte for byte; on V3_0_76 -> `out/LINE_INDEX_V3_0_76.json`
(184e0e3c), issues {}, complete map; 1 stale block = B4-09 'in_v3_0_candidate no' vs census yes, closed by the
in-merge `--promote` (the family's first lines). `t736_package_families.py` (chain 75 -> 76): B4-09 added 14, B5-01
changed 1, B8-06 changed 1. Summary `out/T736_SUMMARY.json`.

| code | V3.0.75 | V3.0.76 |
|---|---|---|
| FIN.PLASTER.BEAD lm (B4-09) | no line | 14 lines: 9 BOUNDED **165.45 .. 165.65**, 5 blank (AT_LEAST 128.6328 beside, never summed); released 0 |
| FIN.CEILING m2 (41) | released 36 / 411.337177; blank 5 | released unchanged; blank 4, **EXCLUDED 1** (code lines 40, blocked -1) |
| FIN.WP.ROOF m2 (6) | released 4 / 209.018867; bounded 1, 0 .. 0.639573 | released 3 / **93.186867** (-115.832); bounded 2, **115.656474 .. 116.453547** |

## 5. Engine vs freelancer, findings, held / missing, downstream

- Beads: the candidate now carries B4-09 for the first time: interior 294.0828 m.l measured (165.45 bounded + 128.6328
  at least), HELD only because the plaster hosts are HELD (D-39 roof build-up, Q-54 B annex datum, shaft exposure):
  they release with their hosts, no re-measure (F-T728-2). Freelancer (T-697, unchanged): like for like 285.03 vs his
  259.60 m.l (+9.8 %; corners ENGINE_RIGHT T-405, door rings -19.70 UNRESOLVED); exterior 310.68 vs 1,297.35
  RULE_DIFFERENCE. No verdict moves with this package.
- Roof membrane: the released figure leaves the released total (-115.832 m2) and is held at the drawing band
  115.656474 .. 115.813974 (spread 0.1575 m2 = the unprinted 0.075 layer-D feature); the H4 package (T-750) carries the
  rest of the roof WP family.
- F-T736-1 (item code, for the Checker / Lead): B4-09 had no item code; this package opens FIN.PLASTER.BEAD (lm) as a
  plaster-trade code (register ruling 'corner beads -> plaster'). A naming decision, no quantity rides on it; if the
  Lead prefers another code it is a rename in the next version.
- F-T736-2 (AT_LEAST form): T-728 counted 67 rows in a 294.0828 .. 294.4828 band; five hosts also carry a blank
  arris, so their line can carry no closed range (an unmeasured arris only adds). The candidate states those five as
  AT_LEAST; the row-level band stays in the ledger rows. Consistent with R-T730-1 (4) / R-T729-1 (c).
- F-T736-3 (index stale block): the 1.77.0 pending registry still says B4-09 'not in candidate'; the census sees 14
  lines: the in-merge promotion rewrites the block (as every first-line family before).
- F-T736-4 (rounding, immaterial): the exact band high is 115.81397437; R-T696-1 (highs round up) would print
  115.813975, the record prints 115.813974. Wired as the record states (the integrator changes no Checker figure);
  residual 0.000001 m2 named for the Checker.
- Held / missing: 6 interior arrises blank by name; exterior beads (43 arrises, H2b) wait T-314 r3 / D-62: no line.
- Downstream: none outside the three codes (asserted); bead lines bind their hosts by id and are never summed into m2.

Lessons row (ERS s.7, proposed): 2026-11-12 | a derived lm line was to carry a host-level band while one of its
arrises was unmeasured | a closed range over a set with a blank member understates the high | a line with any blank
component is AT_LEAST (lower end beside), never a closed range; a hub version reads the Checker record file and asserts
its content binding before it holds a released line (R-T736-1, every villa) | tests/t736_beads_ceiling | PROPOSED.

## 6. Validation

tests/t736_beads_ceiling (24): synthetic villa W736 by hand (bound / at-least / two-trade corner once / exclusion /
downgrade; totals by hand; outside byte-identical; mirror order) and adverse (blank arris on a BOUND line, a figure on a
blank arris, an arris twice / under two hosts, a released arris state, no measured arris, stale host range, released
host, host not plaster, record band / line / stale content / engine_qty, owner held / self / other code, VERIFIED,
applied twice, downgrade of a held line, held never 0); development villa (entries rebuild equal, pins, 73 arrises once,
projection by hand, index V3.0.76 vs V3.0.75: only the 2 named lines changed, 14 added). L3: t729 / t717 / t459 / t741
/ t728 / t730 / t727 + registry folders (m9_kb, t130, t140, t203, t236, t448, t461, t463, t468, t485, t525, t615, t637,
t651, t655) pass; freeze 0; codemap stale none.
