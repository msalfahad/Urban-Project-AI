# T-748 WIRING READINESS ROUND 6 + MILESTONE SCORECARD on ARCH_TAKEOFF_V3.0.75 (worker 3, lane I, 2026-11-12; research)

No quantity is produced, changed or wired; no candidate, hub, registry, rule / knowledge version file is touched; no
drawing opened. Candidate of record ARCH_TAKEOFF_V3.0.75 (T-729 Gate B PASS, merge 05ca1a46, lines a1eba08f,
`research/agents_t729/out/LINE_INDEX_V3_0_75.json`); released default V2.9 + route G untouched. Every input sha256-pinned.
Rule R-T748-1 1.0.0 (`t748_rules.py`, every villa) on R-T730-1 1.0.0; scorecard = R-T739-1 1.0.0 applied unchanged.

- (a) `t748_alsenan.py` -> `out/T748_READINESS.json` + `out/T748_ROWS.csv` (1,366 rows).
- (b) `t748_scorecard.py` (T-739 r2 application, changed only where the candidate moved) -> `out/T748_SCORECARD.json/.md`;
  its own cause pin `CAUSE_SOURCES_PIN.json` (110 files, run of record, L-T717-1).
- `in/T748_BOARD_DOWNGRADES.json` = byte copy of the Checker record `docs/agents/verdicts/V3.0.74/DOWNGRADES.json`
  (agents/control @ 2d28645c); ids, handles and quantities only.
- Both builders: `--check` rebuilds and compares. ERS read: s.2.1, s.2.4, s.3, s.7.

## R-T748-1 (summary; full text in the module)

(1) RESTATE on the newer index: absent host = STALE (fails); host entry equal = UNCHANGED, else HOST_CHANGED with the
package that moved it (the row is re-derived, its old before never wired). (2) MERGED HUB: rows the merged package names
(line id, or key for an ADD) are WIRED_SAME / WIRED_RESTATED / WIRED_ADDED; a live moving row it left = UNWIRED_AFTER_MERGE.
(3) BLOCKERS refreshed against the board (MERGED -> CLEARED). (4) RELEASED UNCHANGED: within a named ledger rounding
(<= 0.0005) KEEP_RELEASED, else CHANGE_RELEASED flagged. (5) DOWNGRADE record applied only if the index's downgrade input
lists it; the record file's id is the identity. (6) ONE HUB PER TARGET across the restated map and the new pieces.
(7) NO-LINE families as ADD_FAMILY rows, HELD never 0, hub or NO_PACKAGE_ROW.

## (a1) T-730 map restated on V3.0.75 (1,174 rows; stale 0)

Line moves V3.0.73 -> V3.0.75 are exactly the T-717 (36) and T-729 (396) package rows (asserted). T-717 rows: 32
WIRED_ADDED (by map_row) + 3 WIRED_SAME + 1 WIRED_RESTATED (T-701:GF-01, T-717 carried 47.949844 .. 66.249856 m2 by its
Gate B, the T-701 figure is superseded); T-729 + C10 rows: 82 WIRED_SAME, 337 WIRED_RESTATED (T-735 precedence), 4
WIRED_ADDED (strip children), 1 KEEP; **UNWIRED_AFTER_MERGE 0**. 194 blockers CLEARED (T-717, T-732, T-733, T-493, T-708
merged). **HOST_CHANGED 11 outside merged hubs**: the T-697 / T-728 bead rows on plaster hosts GF-01
L-b1529955 and GF-04 L-1ddc23d5, moved by T-717: T-736 must bind those beads to the V3.0.74 host values.

## (a2) Pieces merged since T-730, by line id (192 rows; stale 0)

| piece | rows | actions | package |
|---|---|---|---|
| T-740 paint rule (0f0e0cd0) | 105 faces | CHANGE 5, KEEP 48, KEEP_RELEASED 1 (L-7f083d3e 56.0131 vs ledger 56.01315), PENDING 30 (returns: T-746 READY, reading B lm), NONE 21 (no paint line) | T-749 (H1P) |
| T-742 parapet blocks | 25 runs + 4 families | 25 STATEMENT on the STR.CONC.PARAPET lines (RC reading stays S), 4 ADD_FAMILY B9-05 HELD 0 .. 15.092525 / 14.184950 / 57.661748 / 14.525000 m2 (D-39 / Q-65 C) | NO_PACKAGE_ROW |
| T-733 tread highs | 4 | KEEP (F1 4.094412 / F4 3.45 m2 ENGINE_RIGHT): clears the H3S PENDING_ON T-733 | T-738 |
| T-734 WP H4 + Checker record | 14 | CHANGE 9 (MEASURABLE_NOW: 5 penetrations, ledge 0.639573 m2, upturns 0.551614 / 0.500002 lm ...), ADD 4 (MISSING doorway / ...), DOWNGRADE 1 | NO_PACKAGE_ROW (H4) |
| T-735 decider | 7 | WIRED_RESTATED by T-729 | merged |
| T-737 facade / parapet readiness | 18 | CHANGE 3 (FIN.EXT.FINISH per storey, e.g. 1F 248.178057 .. 249.954348 m2), ADD 15 (face lines) | T-314 r3 |
| T-708 earthworks round 3 | 8 | scenario A: CHANGE 1 (B1-04 disposal AT_LEAST 234.333083 m3), BESIDE 1 (import 128.643547); 6 scenario B rows (after T-695 / T-700 rows land) | T-509 |
| T-743 sanitary census | 7 | ADD_FAMILY B12-01 pcs (BASIN 17, FLOOR_DRAIN 19, SHOWER_TRAY 3, SHOWER_WALKIN 3, WC 12; 2 HELD) | NO_PACKAGE_ROW (MEP last) |

## (a3) Queued Gate B packages on V3.0.75 (one hub per target: 202 targets, **double count 0**)

| package | rows | moving live | targets | open blockers | host changed |
|---|---|---|---|---|---|
| T-736 beads + ceiling (H2a / H1R) | 208 | 74 | 15 | none | 11 (GF-01 / GF-04 hosts, T-717) |
| T-738 tiles + stair finishes (H3 / H3S) | 98 | 87 | 87 | RULING ORR-007 27 | 0 |
| T-314 r3 facade + exterior beads | 112 | 61 | 22 | WAITS T-314 60 (its own stage) | 0 |
| T-509 earthworks (H5) | 49 | 18 | 17 | none (T-708 merged) | 0 |
| T-749 paint (H1P) | 105 | 5 (+30 pending T-746) | 5 | PENDING_ON T-746 30 | 0 |
| NO_PACKAGE_ROW: H4 WP / roof, B9-05, B12-01 | 124 | 66 | 56 | MEP last 7 | 0 |

Same target, same package, two pieces (listed for the package, not a fault): 11 lines, e.g. L-636fd3ff (T-691 + the
record), L-78d7c8a9 (T-700 + T-708).

## (b) Scorecard restated on V3.0.75 (T-739 method; out/T748_SCORECARD.md)

5,159 lines: RELEASED 1,569, BOUNDED 1,225, BLANK 1,522, EXCLUDED 843. Chain V3.0.74 + 396 T-729 rows = V3.0.75, 4,763
lines byte-equal; T-729's own census AGREE on all 5 codes. Against the merged T-739 r2 statement only three cells move:
B10 m2 (formwork) released 1,027.977403 -> 1,061.104461 (+33.127058), bounded 0 -> 107.200712 .. 132.785507 (32),
BLANK 370 -> 284; B10 m3 bounded high 67.784279 -> 64.258679 (-3.5256, L-fb7a6431 now BLANK + cap beside), BLANK 49 ->
54; B7 m2 (stair formwork) bounded 0 .. 21.071914 -> 2.583193 .. 24.295379. 28 other cells unchanged. HELD 2,747: 2,743
with a committed cause, 4 without (the 4 C10 strip children: T-729 ADD rows carry no cause field, same class as F-T739-4).
Freelancer keys (diagnostic, never proof): CONC.FOOTING -2.69 .. +5.18 %, CONC.SLAB +0.77 %, CONC.BEAM at least +10.52 %,
plaster like for like -16.76 .. -8.68 %, paint at least -30.97 %: every key % as on V3.0.74; only CONC.GROUND's bound
narrows 1.178378 .. 5.096771 -> 1.178378 .. 1.571171 m3 (still at least -37.97 %, upper end open, 21 BLANK).

## Findings

- **F-T748-1 (record not applied).** The Checker record issued 15:06Z (roof membrane L-636fd3ff 115.832 m2 RELEASED ->
  HELD) is in the board file only; both V3.0.74 and V3.0.75 indexes read the T-469 downgrade snapshot (8173263...), so
  the line is still RELEASED there. The record stays VALID on V3.0.75 (line entry byte-equal, unit m2, qty 115.832). The
  scorecard keeps the index state and prints the record beside: B8 m2 released 711.350096 -> 595.518096 if applied.
  Lead: the next export / hub (H4) must read the board record file.
- **F-T748-2 (id).** The board text (Verifier 15:12, Lead 16:20, LEAD_STATE, FEEDBACK) cites `DG-a429c160`; the record
  file holds one record, `DG-98cbadebaecc5ede`. No record with the cited id exists: the text should cite the file id.
- **F-T748-3 (record only).** T-729 row L-fb7a6431 before_base reads BLOCKED_RFI blank while the V3.0.74 index carried
  0 .. 3.5256 m3 (the F-T739-2 form); after = V3.0.75 index AGREE; no quantity effect.
- **F-T748-4 (no package row).** H4 (WP + roof: 53 CHANGE / TEXT incl. 9 T-734 MEASURABLE_NOW rows + the downgrade),
  B9-05 (4 HELD families) and B12-01 (7 families, MEP last) have moving rows and no board row to wire them.

## Gate A sample (10 rows; expected on an own V3.0.75 rebuild)

T-697:A-GF-01#GF-01 ADD B4-09@L-b1529955 HOST_CHANGED by T-717 (T-736) | T-715:L-5d2be30d KEEP, WAITS T-493 CLEARED
(T-738) | T-700:EW-T350:B1-02:Z1-LOWER-GB-ROW TEXT, WAITS T-708 CLEARED (T-509) | T-709:band:plaster WIRED_ADDED
(T-717) | T-701:GF-01 WIRED_RESTATED (T-717) | T-740 1F_13 L-be48ea84 CHANGE 111.0177 -> 111.0175 (ledger rounding
0.0002 on a HELD line) | DG-98cbadeb L-636fd3ff DOWNGRADE NOT_APPLIED_IN_INDEX | T-742 B9-05@1F ADD_FAMILY HELD 0 ..
57.661748 | T-737 1F-FACADE CHANGE 248.178057 .. 249.954348 (T-314 r3) | T-708 A:1 B1-04 CHANGE AT_LEAST 234.333083.

Lessons row (ERS s.7, proposed): 2026-11-12 | a Checker downgrade record was issued on the board while the candidate's
index kept reading an older downgrade snapshot, and the board text cited an id the record file does not hold | a
statement built from the index alone would show the roof membrane as released after the Checker held it | map every
issued record by line id and print it beside the index state with its validity on the newer candidate; the file's id
is the identity (R-T748-1 rule 5, every villa) | tests/t748_readiness_r6 | PROPOSED.

Tests: tests/t748_readiness_r6 (24): synthetic villa W748 by hand (ids incl. a same-prefix neighbour, host status,
blockers, released rounding with / without a named cause, records applied / not / mis-cited, one hub per target incl.
mirror order and a declared decider, held families as 0 .. 0 and inverted) + the development villa (rebuild equal,
stale 0, double count 0, merged packages wired, blockers cleared, host-changed rows, the record beside, paint rows,
scorecard delta = T-729 cells, census AGREE, held never summed, a tampered pin refused).
