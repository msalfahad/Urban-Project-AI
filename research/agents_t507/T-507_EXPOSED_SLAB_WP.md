# T-507 B8-06 pool-court slab waterproofing: integration package ARCH_TAKEOFF_V3.0.58 (stream F; method every villa)

Worker 2, 2026-11-05 (claim 00:40 UTC, run session_01E6cPncJeSSYTU1xowPUsGb). Gate B integration package on the
candidate of record ARCH_TAKEOFF_V3.0.57 (T-310 r7, merge 87ef8718; V3_0_57_BOQ_LINES 25a8b406). Opt-in candidate
only; the released default V2.9 + route G is untouched; nothing released. Number V3.0.58 / master 1.55.0 provisional:
T-498 and T-423 build V3.0.58 in parallel; the package merged second renumbers (Lead 2026-11-05 00:15). No drawing,
workbook, client name or coordinate in this folder; the drawing is named by its Drive folder and title only.

## 1. Physical element (ERS s.2.1)

The top of the RC slab round the pool-court void at the 1F roof-slab level (+5.50): east of the 1F wall line it is open
to the sky (POOLCOURT-550), west of it a 0.20 m ledge lies under the 2F roof slab 4.20 m above and is open on the void
side (POOLCOURT-550-LEDGE). No door reaches it: ROOF function, family B8-06 (WP_APPLICABILITY_RULES_V1
R-WP-APPL-FUNCTION-1). Installed membrane and upturn only: the build-up (falls screed, insulation, protection, B13-01)
and the membrane rolls (procurement) are NOT in this package (WAITING T507_BUILDUP).

| | owner manual method | drawing-derived method (this package) |
|---|---|---|
| flat membrane | exposed slab top inside its edges less what stands on it and the void (UP-WP-ROOF-001 purpose) | T-494 rows: 8.3537 gross - piers 0.5837 - void 2.8632 = **4.906867 m2** (Checker re-measure 4.9069 AGREE) |
| upturn | 0.20 m on every wall / parapet / solid face (UP-WP-003) | piers 1.838068 + 1.374508 + 0.654611, parapet face 0.894779, parapet end 0.431578 = **5.193544 lm x 0.20 = 1.038709 m2** |
| under the bath window | wall below the sill only if the sill is 0.20 m above the slab | sill not read: own line HELD 0 .. 0.500002 lm |
| ledge | covered above, open at the void side | own lines HELD 0 .. 0.639573 m2 and its bay face 0 .. 3.528277 lm |
| edges | terminations by the detail (UP-WP-004) | named beside: slab edge 6.869158, void edge 4.321407, ledge void edge 2.817214 lm |
| drainage | outlets / falls by the designer | none printed on the 1F drainage sheet: RFI beside, never blocks |

## 2. Rule R-T507-1 (engine/source/arch_v3058.py)

(a) the component rows are recomputed in the engine by `wp_applicability_rules_v1.component_rows` from the zone the
inputs state and must equal the merged T-494 rows, row by row; (b) only a B8-06 (no door) zone is booked; a door
(B8-07) or access unknown is refused; (c) ONCE: every FIN.WP.ROOF line of the candidate is named in the overlap census
(here 4 lines, 0.000 m2 each, T-494 s.4); a non-zero overlap or an unnamed roof line refuses the run; (d) a HELD part is
its own line, BOUNDED_EXPOSURE 0 .. bound or BLOCKED_RFI blank ('length not measured' / 'area not measured'), never in
a quantity, never 0; terminations, drainage RFI and window transitions are named beside the zone's membrane line; an
edge the zone states but did not measure gives a HELD 'length not measured' item, never no item (F-C-T494-1); every
edge must be stated (a length, null, or 0 with evidence); (e) only FIN.WP.ROOF / FIN.WP.ROOF_UPTURN move; every V3.0.57
line is byte-identical (asserted). Upturn unit: lm, the unit of every candidate FIN.WP.ROOF_UPTURN line (a m2 line on
the same code would split the code total by unit); the m2 at 0.20 m is in the line's record and formula.

Default guard: the stage wires wp_applicability_rules_v1 (class UNWIRED_PRODUCER -> GUARDED_VIA_V3.0.6, as T-310 did
for the WP policies) and is a GUARD_HOST: the merged V3.0.6 guard re-runs over the V3.0.57 lines + the added lines with
the V3.0.7 guard inputs unchanged (t193). The t494 test's 'wired into no method' assertion now asserts the one reader
exactly (arch_v3058.py) and the new class.

Code totals view (F-C-T508-1 / T-512, acceptance ii): V3_0_58_RUN.json carries `code_totals_view` for every code of
the result by the T-512 view rule and `codes_held_no_valued_line`; a code with no valued line never prints a number
(asserted in the engine). arch_v304.code_totals (frozen chain) is unchanged; `totals_moved_by_code` keeps the raw
records beside their views.

## 3. Inputs (research/agents_t507/t507_inputs.py)

From T494_COMPONENT_ROWS.json only (sha256 b87f8325..., merge cddfdf7f, Verifier 2026-11-04 08:54 Gate A PASS): each
zone dict restated from the rows (areas / lengths, no coordinate), plus one statement the merged dict lacked: the
ledge's slab edge is 0 BY EVIDENCE (T-494 s.3 partition: bay face, void edge and the wall-line continuation shared with
the open-sky zone). Template line L-2f7502be6f501baf49b1 (1F TERRACE-550, same storey and level). Guard: the V3.0.7
guard inputs unchanged (as T-310).

## 4. Before / after (development villa): see section 6 for the run

| code | V3.0.57 | V3.0.58 | change |
|---|---|---|---|
| FIN.WP.ROOF m2 | 204.112 (3 valued) + 1 blank | **209.018867** (4 valued) + 1 bounded 0 .. 0.639573 + 1 blank | +4.906867 (+2.40 %) |
| FIN.WP.ROOF_UPTURN lm | 181.589 (3 valued) + 1 blank | **186.782544** (4 valued) + 2 bounded 0 .. 4.028279 + 1 blank | +5.193544 lm (= +1.038709 m2) |

Freelancer roof waterproofing 285.00 m2 (his cells not read: workbook over the connector limit, T-494): engine
-28.4 % -> -26.7 %. Verdict proposal: ENGINE_WRONG (omission) on the physics, fixed here, quantities
DRAWING-CONFIRMED; freelancer UNRESOLVED (a freelancer figure is never proof).

## 5. Tests

tests/t507_exposed_slab_wp: villa R507 by hand (court 4 x 4 - void 2 x 1.5 - pier 1 x 1 = 12.000 m2; upturn 4 + 4 + 2 =
10.000 lm = 2.000 m2; window 0 .. 1.000 lm; ledge 0 .. 1.500 m2 / 0 .. 3.000 lm; edges 4.000 / 7.000 / 3.000 beside);
totals 50 -> 62 m2 and 30 -> 40 lm; adverse: unmeasured edge (HELD item), edge not stated / 0 without evidence, area
not measured (blank line), door / access unknown refused, overlap and census refused, stale rows, VERIFIED input, mm,
applied twice, a total outside the codes, a line on another code, run order / mirror invariance, the totals view
(all-blank HELD, bounded-only range, measured 0.0 kept); the guard (RUN with no finding, drawn part not carried,
hold on a candidate line, classes on the live tree, unwired label refused); the development-villa inputs (rows equal,
sha, edited row).

## 6. Development-villa run and registry

Drive run (this session, own decode of P7757_DXF_COMPRESSED.zip + 'ST7757 dxf.dxf' from "Alsenan chalet project", own
T-167 run, chained to the end through research/agents_t507/v3058_run.py, 8 min 29 s): V3_0_56 4e25c54f and V3_0_57
**25a8b406** (the candidate of record, asserted) -> V3_0_58_BOQ_LINES.json **c9570e6c**, 4,994 -> 4,999 lines: 5 ADDED,
4,994 SAME (byte-identical, asserted); replaced 0. Default guard RUN over 4,999 lines: held_live_new [], silent
omissions [] (findings recorded only, by code, as at V3.0.57: CONVENTION_WHERE_PRINTED 87, PARTIAL_FOOTPRINT 2,
PRINTED_VALUES_DISAGREE 75, SEARCH_INCOMPLETE 1,039).

| line | code | element | V3.0.58 |
|---|---|---|---|
| L-eff54f96bfcfcf175d58 | FIN.WP.ROOF m2 | 1F-POOLCOURT-550:wp_membrane | 4.906867 SOURCE_DERIVED; beside HELD: slab edge 0 .. 6.869158 lm, void edge 0 .. 4.321407 lm, drainage RFI |
| L-cf8d5ed40b0d546427d6 | FIN.WP.ROOF_UPTURN lm | 1F-POOLCOURT-550:wp_upturn | 5.193544 (= 1.038709 m2) SOURCE_DERIVED |
| L-1954878bb02c91139e1b | FIN.WP.ROOF_UPTURN lm | 1F-POOLCOURT-550:wp_upturn window_face | HELD 0 .. 0.500002 (sill not read) |
| L-2361d6ec13c952bd2ae3 | FIN.WP.ROOF m2 | 1F-POOLCOURT-550-LEDGE:wp_membrane | HELD 0 .. 0.639573 (covered, open side); beside: void edge 0 .. 2.817214 lm |
| L-d7d1bf8c5991ccf69ea2 | FIN.WP.ROOF_UPTURN lm | 1F-POOLCOURT-550-LEDGE:wp_upturn | HELD 0 .. 3.528277 (zone held) |

Totals moved (only these two): FIN.WP.ROOF m2 released 204.112 -> 209.018867, view 'AT_LEAST 209.018867 + HELD (2
lines: 1 bounded, 1 blank)'; FIN.WP.ROOF_UPTURN lm 181.589 -> 186.782544, view 'AT_LEAST 186.782544 + HELD (3 lines: 2
bounded, 1 blank)'. code_totals_view: 36 codes with no valued line, every one printed HELD (n blank) or a HELD range,
none 0.0. T-512 listed 37 at V3.0.56 from the T-479 index class; the 37th, STR.CONC.BOUNDARY_WALL m3, is one
SOURCE_DERIVED line 7.2204 with a point range 7.2204 .. 7.2204 (valued at line level; HELD only through the T-479
downgrade class), so the line-level view prints its number: named, not a 0.0.

Registry: rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json by research/agents_t507/build_master_1_55_0.py (the T-423
builder with this package's constants): 1.54.0 + T-310 promoted by R-T485-1 (merge 87ef8718, Verifier 2026-11-04
22:45 Gate B; out/PROMOTIONS_SOURCE_1_55_0.json), families B8-01 / B8-02 / B8-03 / B8-09 re-derived from the line diff
V3.0.56 -> V3.0.57 (out/T507_PACKAGE_FAMILIES.json) and the census at V3.0.57 (out/LINE_INDEX_V3_0_57.json, issues {};
the same tool on V3_0_56 reproduces T-310's LINE_INDEX_V3_0_56.json byte for byte; both outputs are byte-identical to
T-423's), + pending ARCH_TAKEOFF_V3.0.58 (T-507) with the B8-06 text. RULES_MANIFEST by its tool; T-459 binding by its
tool; T-463 git facts by build_t463_facts.

## 7. Lessons row (proposed)

| 2026-11-05 | the rule function drops an edge whose length is unknown (no row), and an all-blank code printed 0.0 in the run summary | `if lm:` treats None like 0; code_totals reports released 0.0 with no valued line | integration states every edge (length / null / 0 by evidence) and emits a HELD 'length not measured' item; the run carries the T-512 view of every code (every villa) | tests/t507_exposed_slab_wp (unmeasured edge, edge not stated, 0 without evidence, view) | proposed |
