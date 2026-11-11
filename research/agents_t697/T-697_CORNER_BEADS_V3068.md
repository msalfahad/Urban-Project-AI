# T-697: B4-09 CORNER BEADS, census bound to candidate ARCH_TAKEOFF_V3.0.68 (development villa; every villa by R-T697-1 .. 6)

Worker 2, claim 2026-11-11 06:40 UTC. Research only: no engine module, method, rule / knowledge version, registry file,
candidate line or released line changed; nothing wired, released or VERIFIED. Files: `t697_rules.py` (rules),
`t697_alsenan.py` (`--write` / `--check`), `out/T697_BEAD_LEDGER.csv` (185 rows), `out/T697_SUMMARY.json`,
`tests/t697_corner_beads` (16 tests: villa E697 by hand, normal + adverse, then the development villa pinned).

## 0. Starting point (correction to T-692)

T-692 classed B4-09 "MEASURABLE, no ledger". A merged, Checker-verified arris ledger exists: T-405 (MERGED cd1aadaf,
Gate A PASS, 186 rows, interior 275.95 / exterior 310.6831 m.l). It was written on the V2.9 room polygons and never bound
to a candidate. This task does not re-derive its verified arrises; it restates them on V3.0.68 (line index T-672,
lines sha d1de50cb), applies the owner rules and register rulings issued since, and closes what can now be closed.

## 1. Physical element and height (ERS s.2.1)

A galvanised steel angle on a CONVEX arris of a plastered surface, over the length where both sides are plastered AND
the edge is exposed. Owner OD-V3B-8 (2026-10-04): beads "at exposed plaster edges ... never on a hidden edge". Owner
heights rule (2026-11-02): plaster runs to the structural soffit, paint to the finished ceiling (G1 GF 3.65, 1F / 2F 3.35).
So the plaster band between the finished ceiling and the soffit exists but its arris is hidden above the ceiling: no
bead (R-T697-1). **F-T697-1 (for the Lead):** the row text "vertical = plaster height by the heights rule" would put
beads on hidden edges, against OD-V3B-8; the owner method uses G1, the drawing-derived method shows G1 .. structural
soffit (GF 4.29, 1F 3.99 DRAWING-CONFIRMED; 2F 3.99 roof scenario D-39) because no plan prints the ceiling type
(O-P8-02). Difference on the 37 vertical corners at G1: +23.68 m.l if no room had a decor ceiling.

## 2. What changed against T-405 (m.l)

| Item | T-405 | T-697 | Cause |
|---|---|---|---|
| Stair-hall column arrises GF (2) | HELD (Q-72 open) | **8.46 DRAWING-CONFIRMED** | Q-72 answered (full exposed height); R-T697-6 on the T-680 shaft net face: paint-band pier returns 0.423 m2 / 0.05 |
| Stair-hall column arrises 1F (2) | HELD | **7.92 DRAWING-CONFIRMED** | 0.396 / 0.05 |
| Stair-hall column arrises 2F (2) | HELD | **HELD 7.58 .. 7.78** | 0.379 .. 0.389 / 0.05 (top under the roof: D-39, build-up b) |
| GF-08 #V60, #V61 (column 2FC6 north corners) | 3.65 + 3.65 ASSUMED | **HELD 3.4364 .. 3.5364 each** | own read P7757.dxf ab54dd55: both corners lie under stair C's quarter landing drawn HIDDEN (layer '2', HIDDEN linetype: 4AF east edge x = column east face, 4B6, 141); C-L1 finished +4.696429 (SOURCE_VERIFIED) - b 0 .. 0.10 - 0.16 (zone tag T16) - floor +1.00 = 3.436 .. 3.536 < G1 (R-T697-2) |
| GF-08 #V61 identity | UNRESOLVED (Checker: 4AF wall face or not) | **an arris** | 4AF is a hidden overhead line (the landing edge), not a wall face; it starts on the wall face line 336 and runs north 2.40 m with the landing's treads 144 / 145 / 146 / 4B5 at 0.30 pitch |
| Lift entrances GF / 1F / 2F | HELD (head not established) | **NOT_APPLICABLE, B6-06** | register LIFT ENTRANCE + corner-bead ruling: the surround owns the arrises; bound to FIN.MARBLE.LIFT_SURROUND per floor |
| Exterior corner held parts (notes only in T-405) | not rows | **3 HELD rows 2.10 .. 15.65** | plinth 2.10 .. 2.55 (ARCH.FACADE plinth line), 1F parapet ends 0 .. 11.90, mouth stop-ends 0 .. 1.20 (T-172) |
| Everything else | as T-405 | unchanged | door rings, windows, exterior verticals and mouths (T-172 VERIFIED), all exclusions |

## 3. Result

| Scope | Owner method measured | Drawing-derived | HELD bounded | HELD blank (by name) |
|---|---|---|---|---|
| Interior | **285.03** (ASSUMED - OWNER-APPROVED 261.65, DRAWING-CONFIRMED 23.38) | 285.03 .. 308.71 | 14.4528 .. 14.8528 (3 rows) | 11 |
| Exterior | **310.6831** (DRAWING-CONFIRMED 278.4831, ASSUMED 32.20) | 310.6831 | 2.10 .. 15.65 (3 rows) | 11 |
| **All** | **595.7131** | 595.7131 .. 619.3931 | 16.5528 .. 30.5028 | 22 |

Interior check by hand: 275.95 - 7.30 + 8.46 + 7.92 = 285.03. Exterior check: 124.70 + 43.10 + 103.6831 + 39.20 =
310.6831.

## 4. Binding (R-T697-3)

185 rows: 168 BOUND, 1 BINDING_OPEN, 3 OWNED_BY_B6-06, 13 NO_HOST (all HELD class rows that are room-wide or have no
face line: stop-ends, ceiling / void / stair edges, parapet tops, slab edge, drip, arch frames, fence, sills, the
D-1F-07 far face, the GF-15 gate). Every counted arris names a FIN.PLASTER or FIN.EXT.FINISH line present in V3.0.68;
none sits on a wall-tile room. Per host (owner m.l) in `T697_SUMMARY.json` 'hosts'. Exterior rows bind to the three
FIN.EXT.FINISH floor lines (HELD blank in V3.0.68 only because T-314 is not wired; the faces are measured in the merged
T-305 ledger, so the arrises are not HELD for that reason).

- **F-T697-2 BINDING_OPEN:** D-1F-02 far ring 5.40 m.l lies on wall face 1F-W23, split by the engine zone boundary
  between 1F-13 (1.28 m) and ST-1F (0.74 m) (T-292 FACE_TO_LINE): which jamb falls in which zone is not read; kept
  measured, both lines named.
- **F-T697-3 CROSS-TRADE (Lead ruling needed, no owner question):** T-314 (QUEUED r3) plans "corners m.l ... as their own
  lines" on the facade, from the register row of 2026-10-22 (457.095 m.l = T-162 r1, superseded by T-162 r2 / T-172:
  verticals 167.80 incl. mouths). Those are the same physical exterior arrises as the B4-09 exterior rows (310.6831).
  One arris, one quantity: B4-09 holds the physical m.l (register 2026-11-11); the Sigma "2 m.l = 1 m2" is a payable
  convention on the same m.l (OWNER_NOTES_SIGMA correction 07:10), a contract column, never a second quantity line.

## 5. Freelancer (restated from T-405 on the new figures)

Interior like for like (room corners + door rings): his 100.00 + 159.60 = 259.60 vs 145.13 + 139.90 = 285.03 m.l
(+25.43, +9.8 %). Corners +45.13: count ENGINE_RIGHT on the re-measured columns (T-405 Checker), and the shaft
arrises 16.38 that his room rows do not carry (UNRESOLVED whether his stair rows 29.20 'stringers' include them);
door rings -19.70 UNRESOLVED (his 14 doors x 2 x 5.70). Stop-ends (his 282.85) RULE_DIFFERENCE, HELD by name.
Exterior unchanged: 310.6831 vs his 1,297.35 (scope: parapet tops, drip, boundary; RULE_DIFFERENCE, T-405 / T-172).

## 6. Proposed lesson row (ERS s.7)

2026-11-11 | an arris passing under a drawn overhead element was given the room ceiling height, and a HIDDEN-linetype
line was read as a possible wall face (T-405 V61) | an arris stops at the lowest of the finished ceiling and any element
drawn over it; a layer / linetype HIDDEN line is overhead, never a wall face | R-T697-1 / -2 (every villa) |
tests/t697 (normal: column to G1; adverse: landing below G1 -> HELD from its levels, G1 refused).

## 7. Not done / uncertain

The 22 HELD blank classes (stop-ends 289.281, parapet tops 271.963, sills 29.53, arches, W02 / W03 / W17, D-1F-07 far
face, gate, stair / void / ceiling edges, slab edge, drip, fence) keep their T-405 causes. The 2F stair-hall column and
the landing-soffit bounds wait on D-39 / DCR-6 (build-up b). No wiring, no B4-09 candidate line: proposal for lane I = one
B4-09 line per host in `hosts`, HELD rows blank with cause, exterior after the F-T697-3 ruling.
