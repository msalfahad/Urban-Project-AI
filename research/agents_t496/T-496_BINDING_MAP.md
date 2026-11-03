# T-496: materials binding map + check on candidate V3.0.47 (research, unwired)

Worker 3, 2026-11-03. `t496_binding_map.py` + `out/BINDING_MAP_T496.{json,csv}` + `tests/t496_binding_map/` (16).
No candidate, engine, rule, knowledge or registry file changed; no candidate or released (V2.9 + route G) line moves.
Rebuild: `python3 -I research/agents_t496/t496_binding_map.py` (byte-identical, tested); check: `... --check` (exit 1
on any failure).

## What it binds
Five committed, sha256-pinned material outputs (T-453 r2 blockwork, T-454 plaster V1, T-489 plaster V2, T-455 tile V4,
T-495 outdoor finish-HELD rows) onto ARCH_TAKEOFF_V3.0.47 e86a53a8 = the V3.0.46 line index (35d70129) + the T-443
change set (2 replaced + 7 added FIN.SKIRTING lines). 1,202 bindings: per row the line id, item code, unit, candidate
class, material, quantity kind, stage (theoretical / installed / procurement / no candidate line), value, bound,
estimate beside, status, purchasing group and wiring state.

## Rules R-T496-1..6 (code docstring has the full text)
1 presence + unit + read equals the candidate line (class, net, held range); 2 HELD stays HELD (no figure from a HELD
line or row; a bound only on a candidate held range; a purchasing group with an open member prints no 'to buy');
3 one producer per (line, material, kind), declared read chain T-489 <- T-454 must reproduce exactly; 4 cross-trade:
a candidate layer line (tile bed, spatter, mortar, lintel) on the same host excludes a table's same material;
5 scope: every in-scope candidate line read or named in KNOWN_GAPS; 6 owner arithmetic re-derived (276 figures:
12.5 blocks / m2, glue 3.5 / 4.5 kg/m2 and 25 kg bags, 1:4 = 8 bags + 1.1 m3 sand per m3, adhesive area / 5 .. / 3,
lintel face (w + 0.80) x D, bed x 1.05) plus subtotal proof (rows -> each table's printed total).

## Result on V3.0.47 (0 failures)
| material | wireable figure (released line) | not a figure |
|---|---|---|
| black 0.20 units | 3 lines 1,346.55 nr VERIFIED-NET | 1 RANGE 43.25 .. 47.50; 22 HELD |
| black mortar 1:4 | 3 lines 1.588929 m3, 12.711 bags, 1.748 m3 sand PROVISIONAL-NET | 1 RANGE; 0.15 m and held lines HELD |
| AAC glue | 116.703 kg VERIFIED-NET + 112.8725 kg PROVISIONAL-NET | 4 RANGE 907.2 .. 932.9 kg; PROJECT bags HELD (13 open members) |
| wall plaster dry | none | 4.726962 m3 = ESTIMATE BESIDE a HELD figure (level-4 thickness) |
| wet render | none | >= 5.104557 m3 AT_LEAST bound (12 lines) |
| bond coat, cement / sand of every coat | none | HELD (no thickness / no mix) |
| tile adhesive, boxes | none | bounds only (size not given); PROJECT group 66 members HELD |
| outdoor finish-HELD (T-495) | none | per-option bounds on the candidate held ranges |
| RC lintels (60) | none: B9-02 has no line (T-487) | 16 REQUIRED, 2 FLAGGED, 42 HELD; 27 on held hosts |

All 26 MAS.BLOCK, 83 plaster, 77 tile and 2 outdoor lines read by the tables are in V3.0.47 with the same class and
net (tables built on V3.0.45 still read V3.0.47 identically); none is among T-443's 9 changed lines.
Cross-trade identity (UPC-WETWALL-001): released render face 340.3038 m2 = wall-tile face 340.3038 m2 (12 + 12
lines): one face, two materials, never added.

## Findings for the wiring row
- KNOWN GAP: 2 MAS.BLOCK lines added at V3.0.46 (T-419 house below-ground masonry, HELD) are read by no table: their
  units / glue / mortar must be carried HELD, and they are open members of the PROJECT glue group (11 -> 13).
- T-454 labels the dry plaster mortar ESTIMATED-NET; T-489 gives the same figure s.5 HELD. The map carries it as an
  estimate beside a HELD figure (weakest input); a wiring must not release 4.726962 m3.
- F-T496-1: T-455 (and its re-run in T-495) prints 0.0 for subtotals over rows none of which carries a number
  (v4_bags_known on every code and the PROJECT group; FIN.FLOOR.FINISH_HELD bound_low / high / v3_flat_bags). Status
  beside says HELD, no released figure is wrong; a wiring must read them as None. Declared in the check; an
  undeclared one fails ZERO_SUBTOTAL.
- No table covers: FIN.FLOOR.BED.DRY / WET (88 bed lines: bed mortar material), EXT.PAVING.INTERLOCK (declared out),
  FIN.EXT.FINISH, FIN.STAIR.* (named in `not_in_any_table`).

## Verdict proposal / lesson
No engine vs freelancer change (no quantity moved; freelancer material lines not compared). Lesson (proposed): a
material is wired from its binding, not its table: the line's class and the weakest input decide the status, a
purchasing group is keyed by product across tables, and a subtotal over held rows is unknown, never 0 (T-496).
