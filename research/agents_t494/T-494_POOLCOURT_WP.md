# T-494 B8-06 pool-court slab waterproofing: component rows and the new applicability rule version

Worker 2 (lane A), 2026-11-04, run session_01E6cPnbKEPTLtGUwris2dpV. Research piece (backlog-permitted): no candidate
file, method, existing rule / knowledge version or frozen file changed. New files: `engine/source/wp_applicability_rules_v1.py`
(the NEW rule version F-C-T486-1 asked for, unwired, stdlib only), `research/agents_t494/*`, `tests/t494_poolcourt_wp/*`.
Drawing by Drive title and handle only ("Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256
ab54dd55..., downloaded and decoded this run; sanitary-7757.pdf sheet 2 as read in T-486). No coordinate is stored.

## 1. Physical element (ERS s.2 step 1)

The top of the RC slab that the GF roof-slab sheet casts over the pool court, at printed +5.50 (LEVEL 1251), round the
oval void (label BBF). East of the 1F wall line it is open to the sky (the 2F plan draws nothing there); west of it a
0.20 m ledge between the bay's outer face and the void edge lies under the 2F roof slab 4.20 m above, open on the void
side. No door reaches it (bay glazed, bath window only): ROOF function, family B8-06. Below it: the exterior court.
It is a physical membrane location whatever the label: an exposed slab top that abuts the habitable house (bath window
wall, glazed bay) and has no falls or outlet printed.

## 2. Rule version (F-C-T486-1): WP_APPLICABILITY_RULES_V1

UP-WP-ROOF-001 (owner 2026-10-14, effective 1.1.0) states the purpose "exterior horizontal surfaces exposed to water"
but its scope is "balconies, terraces and roofs drawn as spaces". The new version (new file, nothing edited) adds:
R-WP-APPL-EXPOSED-1 (exposure decides, label never; covered = NOT_APPLICABLE; covered with an open side / unknown =
HELD with the bound shown), -FUNCTION-1 (door -> B8-07, none -> B8-06), -ONCE-1 (a surface a roof line already carries is
CARRIED, never added), -UPTURN-1 (0.20 m on wall / parapet / solid faces; under a window only with the sill at least
0.20 m above the slab, unknown sill = HELD, low sill = transition), -EDGE-1 (slab / void edges are terminations, length
measured, treatment HELD by detail), -DRAIN-1 (no outlet / falls printed = RFI, never blocks). The scope extension is
agent-derived (provenance T-486, Checker-endorsed), not an owner decision: every row carries that basis.

## 3. Component rows (B8-06, POOLCOURT-550)

| Zone | Component | Run (handles) | Qty | Unit | Status | Basis |
|---|---|---|---|---|---|---|
| open sky | flat membrane | outline C7D / B30 / C7F-B32 / BDC / wall B62-B60, less piers and void | **4.906867** | m2 | MEASURED (DRAWING-CONFIRMED, Checker 4.9069) | R-WP-APPL-EXPOSED-1 |
| open sky | upturn | N pier CAA..CA4 1.838068 lm | 0.367614 | m2 | MEASURED | -UPTURN-1 / UP-WP-003 |
| open sky | upturn | S pier CB2..CA2 1.374508 lm | 0.274902 | m2 | MEASURED | idem |
| open sky | upturn | SW pier CA1 / CA3 / C9E 0.654611 lm | 0.130922 | m2 | MEASURED | idem |
| open sky | upturn | parapet face BDC 0.894779 lm | 0.178956 | m2 | MEASURED | idem |
| open sky | upturn | parapet end C7F / B32 0.431578 lm | 0.086316 | m2 | MEASURED | idem |
| open sky | upturn | under the bath window C35 0.500002 lm | (0.100000) | m2 | HELD: sill height above the slab not read | -UPTURN-1 |
| open sky | slab-edge termination | C7D 1.500 + B30 5.368 | (6.869158) | lm | HELD: treatment by detail | -EDGE-1 / UP-WP-004 |
| open sky | void-edge termination | BCF / 2F1C / C7A / 2F1B east part | (4.321407) | lm | HELD: treatment by detail | idem |
| open sky | drainage / falls | sanitary sheet 2: none printed | - | nr | RFI (never blocks) | -DRAIN-1 |
| ledge | flat membrane | bulge 1.6009 - void 0.9613 | (0.639573) | m2 | HELD: covered 4.20 m above, open at the void side | -EXPOSED-1 |
| ledge | upturn | bay face BCD / BCE / BD0 3.528277 lm | (0.705655) | m2 | HELD (zone held; glazing BD2..BD5 in the bay) | -UPTURN-1 |
| ledge | void-edge termination | BCF west part | (2.817214) | lm | HELD | -EDGE-1 |

Doorway transitions (UP-WP-DOOR-001): 0 by evidence (no door insert on the boundary; T-486 Checker). Penetrations
(UP-WP-004): none drawn. Values in brackets are HELD bounds, shown and never summed. Valued: flat 4.906867 m2, upturn
5.193544 lm = 1.038709 m2 (state PART_AT_LEAST: the window run and the ledge are held).

Reconciliation: the boundary is partitioned run by run on the snapped geometry (each piece to one run, unassigned
0.000000): 0.894779 + 0.431578 + 0.500002 + 6.869158 + 4.321407 + 0.562437 continuation + 1.838068 + 1.374508 +
0.654611 = 17.446548 vs perimeter 17.446513 (end-point bands 0.000035). Against T-486 upturn 5.694267 = valued 5.193544
+ window 0.500002 + 0.000721: the open edge reads 6.869158 here vs 6.868422 in T-486 (a pier's rounded corner tangent
to the north edge, within 1.1 um of it, goes to the edge here): 0.7 mm, named, not material.

## 4. Overlap with FIN.WP.ROOF: 0 m2

| Roof line | Zone | Level | Overlap | Evidence |
|---|---|---|---|---|
| L-d57d2dc2 | ROOF-430 1F west | +4.30 | 0 | label B8D 25.7 m west of the wall line, 1.20 m lower: another slab |
| L-2f7502be | TERRACE-550 SE strip | +5.50 | 0 | label B81 4.70 m south of BDC; parapet BDC / BDB between; strip to BDB, this zone to BDC |
| L-636fd3ff | ROOF-970 2F terrace | +9.70 | 0 | its east edge at the wall line: in plan over the ledge only (the HELD row), not the open sky part |
| L-3e8fe55d | ROOF-1390 (HELD) | 2F block | 0 | the 2F block's own roof, not over the court |

## 5. Engine vs freelancer; verdict proposal

Candidate roof WP 204.112 m2 (flat) -> 209.019 m2 (+4.907, +2.40 %) and roof upturn +1.039 m2 if wired; freelancer roof
285.00 m2 (-28.4 % -> -26.7 %; his cells not read, workbook over the connector limit). Verdict: ENGINE_WRONG (omission)
on the physics, quantities DRAWING-CONFIRMED; freelancer UNRESOLVED.

## 6. Lessons row (proposed) and what is missing

| 2026-11-04 | an exposed, unlabelled slab top had no WP line; a window run would have been booked as a full upturn by default | applicability and upturn eligibility were keyed to labels and wall lines, not to exposure and sill height | WP_APPLICABILITY_RULES_V1 (every villa): exposure decides; an upturn under a window needs the sill >= 0.20 m above the slab, else HELD / transition | tests/t494_poolcourt_wp (villa R normal; covered ledge held, covered N/A, sill unknown / low, door -> B8-07, carried not re-added, held never 0, rotation / mirror / mm; dev villa) | proposed |

Missing / uncertain: the bath window sill height (elevation / section not read: keeps 0.100 m2 HELD); termination
details at the slab and void edges (designer); drainage and falls (RFI); screed / falls build-up (B13-01) not in this
piece; the piers assumed solid on the slab (if cladding, +0.584 m2 membrane and their upturns change: T-486 s.6).
Wiring into the candidate: a later V3.0.x under Gate B (T-310 holds the candidate WP wiring).
