# T-728 BEAD LEDGER RESTATEMENT on ARCH_TAKEOFF_V3.0.72 (worker 3, lane I, 2026-11-12; research only)

No quantity is measured, changed or wired; no candidate, hub, registry, rule / knowledge version file is touched; no
drawing opened. Released default V2.9 + route G untouched. Rule R-T728-1 1.0.0 (`t728_rules.py`, every villa);
application `t728_alsenan.py` (`--check` rebuilds and compares); outputs `out/T728_BEAD_RESTATEMENT.json` and
`out/T728_BEAD_ROWS.csv` (one row per arris). Inputs (sha256-pinned, merged only): T-697 bead ledger, T-723 rows,
line indexes V3.0.64 / .69 / .71 / .72, T-676 hold census, T-687 shaft restatement.

## Physical element and the ruling (ERS s.2.1, s.3)

A corner bead is the steel angle on a convex plastered arris, exposed length only (OD-V3B-8; owner method G1 to the
finished ceiling, F-T697-1 CONFIRMED by the Checker on T-697). Lead ruling 2026-11-11 16:25 (F-T705-1): the bead takes
its host face's height state; on a HELD host it is HELD, never released at a chosen height, never 0; released together
with its host. The host bounds on V3.0.72 are AREA bounds (m2: openings without an established head, beam ends, shaft
build-up b); the host height itself is a scenario value with no printed bound (D-39 roof build-up). So the bead keeps
its OWN ledger length (no new measure), takes the host's HELD state and cause, and the host's m2 bound is quoted beside.

R-T728-1 state table: host RELEASED + measured -> RELEASED; host BOUNDED + measured -> HELD point (low = high = ledger
m); own held bound -> kept, both causes; host BLANK -> HELD blank with the host's cause, the ledger figure kept as
reference text only; a HELD-blank bead stays blank everywhere. G1 .. soffit stays text in `drawing_band`, never the bound.

## Result (116 / 116 by arris id, stale 0)

All 18 hosts are HELD on V3.0.72 (14 BOUNDED, 4 BLANK) and equal to their V3.0.71 entries (T-723 map not stale; also
equal on the READY T-722 index V3.0.73, read by hand, not pinned). Released beads: 0.

| scope | rows | HELD bounded (m.l) | HELD blank | why |
|---|---|---|---|---|
| Interior (H2a, 14 room / shaft plaster hosts) | 73 | 67 rows 294.0828 .. 294.4828 | 6 | hosts HELD on D-39 roof build-up (rooms) / BOUNDED_EXPOSURE (shaft, T-687) |
| Exterior (H2b, 3 FIN.EXT.FINISH + plinth ARCH.FACADE) | 43 | 0 | 43 | hosts blank: face rows queued in T-314 r3; plinth D-62 |

Hand reconciliation with T-697: interior owner 285.03 - D-1F-02 far ring 5.40 (BINDING_OPEN, not a ruling row) +
held 14.4528 .. 14.8528 (GF-08 V60 / V61 2 x 3.4364 .. 3.5364; ST-2F 7.58 .. 7.78) = 294.0828 .. 294.4828 m.l (exact).
Exterior ledger figures on blank hosts: 183.5 (GF) + 88.5122 (1F) + 38.6709 (2F) = 310.6831 m.l = T-697 exterior owner
m.l, carried as text, not a quantity. 6 interior blanks keep their own cause (arches A-1F-01 / A-GF-01, W03 / W17 room
side, OP-020 / OP-003 heads). Per-host table in the JSON `summary.hosts`.

Pending: 42 exterior rows wait on T-314 r3 (it REPLACES the 3 blank facade hosts by face rows: the beads must be
re-bound by face id then); 4 rows on GF_01 / GF_04 wait on the H1 plaster package (T-717). T-726 (READY, shaft residual,
research) may restate the ST hosts: the 3 shaft bead rows follow.

## Engine vs freelancer (unchanged from T-697; nothing wired)

Interior like for like 285.03 vs his 259.60 m.l (+9.8 %): corners ENGINE_RIGHT (T-405), door rings -19.70 UNRESOLVED;
exterior 310.6831 vs 1,297.35 RULE_DIFFERENCE. This task moves no figure, only the state: B4-09 enters the candidate
HELD (interior point / bounded, exterior blank) until its hosts release.

## Findings

- F-T728-1 (Lead, wording): the ruling's 'host's bound' cannot be transferred as an m2 bound to an m.l bead; read as
  'host's HELD state and cause' + the bead's own length. If the Lead means a length band from the host's height band,
  no host prints one (D-39 'no lower bound printed'): the result would be the same HELD point.
- F-T728-2 (consequence): 294.08 m.l of interior bead measured at G1 is HELD only because the plaster host is held on
  the roof build-up (D-39); it releases the moment D-39 is answered, with no re-measure.
- F-T728-3 (2F shaft): the bead uses the PAINT pier returns 0.379 .. 0.389 (exposed, R-T697-6) while the plaster host
  uses 0.394 .. 0.404 (to soffit): consistent with F-T697-1, named so Gate B does not 'correct' one to the other.

Lessons row (ERS s.7, proposed): 2026-11-12 | a derived element (bead lm) was given its host's state | an m2 bound
cannot become an m.l bound; carry the host's HELD state and cause, keep the element's own measured length, never invent
a band | R-T728-1 | tests/t728_bead_restatement | PROPOSED.

Tests: tests/t728_bead_restatement (39): synthetic villa W728 by hand (released / bounded / point / blank hosts; adverse:
absent / EXCLUDED / malformed host, 0 / negative / inverted ledger, blank host never numbered, arris twice / under two
hosts, released on a held host, owner missing, mirror order) and the development villa (rebuild equal, pins, 116 once,
stale 0, none released / 0, reconciliation by hand, specific rows, pending hosts, adverse on real rows).
