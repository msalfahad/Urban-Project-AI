# T-314: EXTERIOR PLASTER / SIGMA face rows into the FIN.EXT.FINISH lines (integration package ARCH_TAKEOFF_V3.0.60 on V3.0.59; method every villa)

Worker 2, claim 2026-11-09 06:43 UTC (run session_01E6cPnezLwZiiw89C3J26fj). Gate B integration package, fifth in the
owner's Gate B order (the version number is allotted at merge: T-423 r2 / T-563 merging first renumber this package).
Opt-in candidate only; the released default V2.9 + route G is untouched; nothing released. No drawing, workbook, client
name or coordinate in this folder.

## 1. Physical element and the two methods (ERS s.2.1, s.2.2)

The outer render / Sigma face of the built envelope, band by band: storey bands (F.F.L. -> next level), parapet outer
bands (roof -> parapet top), parapet inner faces above the membrane upturn and parapet tops, the plinth (ground ->
lowest house F.F.L.) and slab edges over open air, each face once; every opening deducted once, in full, on the face
that holds it. Reveals (ARCH.WINDOW_REVEAL), soffits (FIN.CEILING), the upturn zone face (waterproofing), corners /
copings / drips (m.l) and cladding are other items.

| | owner manual method | drawing-derived method (this package) |
|---|---|---|
| area | Sigma = exterior plaster area (OWNER_NOTES_SIGMA 2026-10-21); Q-07 B bands from the floor | drawn face band length x band height by element and levels (T-305 / T-311 / T-324 / T-337 / T-348 r2 / T-567) |
| openings | every actual opening in full where masonry exists (Q-73 A) | same holes, by schedule size, once, on the face band that holds them |
| plinth | outside the Q-07 B bands (RFI) | its own line, HELD (pool-court bottom, finish not printed) |
| corners | own m.l line (owner 2026-10-22) | named MISSING here (no registry item code yet), never m2 |

The owner Q-07 B figure is recorded BESIDE every storey / parapet line (`owner_q07_beside_m2`), never as its quantity.

## 2. Rule R-T314-1 (engine/source/arch_v3060.py)

(1) one element per line: a parapet / plinth / slab-edge band in a STOREY line is refused; (2) a levelled face lies
inside one level part of its line, a band crossing a part is refused until split (an unprinted level is HELD and only
its printed end is checked); (3) every face once, every opening once, on a face of the same line, sill / head inside
the band, never larger than the face; a HELD hole has a cap above 0; (4) HELD never 0: a held face or hole makes the line
a bounded range with no point value, a blank face makes it blank; a DRAWING-CONFIRMED face carries one value; a
bounded / blank line carries no numeric gross (the V3.0.24 two-states guard caught it on the fixture); (5) existing lines
CHANGED in place (id, element, rule kept), new lines ADDED; every other line byte-identical, totals move only in
FIN.EXT.FINISH; every V3.0.10 .. V3.0.59 family check re-run on the result; (6) owner method beside; (7) every line
recomputed from its rows and asserted equal to the merged ledgers' expected figure.

## 3. Inputs (research/agents_t314/t314_inputs.py; merged files only, sha256 pinned in the inputs)

T-337 binding (109 bands with levels and owner line), openings (38 holes + 1 NOT_AN_OPENING), items (parapet inner /
top) and FILL tables (ce3aaf8f); T-348 r2 FILL_T314 + FACES (623885fd): NW-2 parapet re-measured 3.977236 DC (was HELD
4.223108 .. 4.585300), 9 new faces for T-314, the NW-1 / NW-3 slab edges removed (no physical face); T-567 (8aba0d81)
R-T567-6 SW pier returns (storey 2.2533924 DC, parapet 0.0536522 .. 0.6974786 HELD). **The 118 render faces equal the
T-567 face set of record key by key, value by value and status by status (asserted in tests).**

## 4. Per BOQ line, before (V3.0.59) -> after (V3.0.60), m2

| line (key) | element | before | faces | gross | holes fixed (assumed) | held holes | after (net) | state / status | owner Q-07 B beside |
|---|---|---|---|---|---|---|---|---|---|
| NEW FIN.EXT.PARAPET-INNER 1F +9.70 | PARAPET_INNER | no line | 1 (0 blank) | 41.82353 .. 56.608545 | 0.0 (0.0) | - | **41.82353 .. 56.608545** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70 | PARAPET_OUTER | no line | 14 (0 blank) | 54.00748 .. 60.029307 | 0.0 (0.0) | - | **54.00748 .. 60.029307** | BOUNDED_EXPOSURE / HELD | 48.106656 |
| NEW FIN.EXT.PARAPET-TOP 1F +9.70 | PARAPET_TOP | no line | 1 (0 blank) | 9.83151 .. 9.84653 | 0.0 (0.0) | - | **9.83151 .. 9.84653** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.FINISH SLAB-EDGE 1F | SLAB_EDGE | no line | 7 (6 blank) | - | 0.0 (0.0) | - | **blank** | BLOCKED_RFI / HELD blank | - |
| L-8bb83e16cc7b104ab88b | STOREY | HELD blank | 18 (0 blank) | 278.961829 .. 280.73812 | 30.783772 (0.0) | - | **248.178057 .. 249.954348** | BOUNDED_EXPOSURE / HELD | 278.961829 |
| NEW FIN.EXT.PARAPET-INNER 2F +13.90 | PARAPET_INNER | no line | 1 (0 blank) | 8.49 .. 14.15 | 0.0 (0.0) | - | **8.49 .. 14.15** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.FINISH PARAPET-OUTER 2F +13.90 | PARAPET_OUTER | no line | 4 (0 blank) | 14.9 | 0.0 (0.0) | - | **14.9** | MEASURED / DRAWING-CONFIRMED | 14.9 |
| NEW FIN.EXT.PARAPET-TOP 2F +13.90 | PARAPET_TOP | no line | 1 (0 blank) | 5.415 | 0.0 (0.0) | - | **5.415** | MEASURED / DRAWING-CONFIRMED | - |
| L-d52c4f763b19aedf8b8b | STOREY | HELD blank | 4 (0 blank) | 125.16 | 7.855 (2.2) | - | **117.305** | PROVISIONAL / ASSUMED — OWNER-APPROVED part | 125.16 |
| NEW FIN.EXT.PARAPET-INNER ANNEX +4.30 | PARAPET_INNER | no line | 1 (0 blank) | 8.88843 .. 14.91405 | 0.0 (0.0) | - | **8.88843 .. 14.91405** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.PARAPET-INNER GF +5.50 | PARAPET_INNER | no line | 1 (0 blank) | 8.209433 .. 13.88495 | 0.0 (0.0) | - | **8.209433 .. 13.88495** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.FINISH PARAPET-OUTER ANNEX +4.30 | PARAPET_OUTER | no line | 7 (0 blank) | 14.671022 .. 15.271022 | 0.0 (0.0) | - | **14.671022 .. 15.271022** | BOUNDED_EXPOSURE / HELD | 14.671022 |
| NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50 | PARAPET_OUTER | no line | 3 (0 blank) | 14.385 | 0.0 (0.0) | - | **14.385** | MEASURED / DRAWING-CONFIRMED | 14.385 |
| NEW FIN.EXT.PARAPET-TOP ANNEX +4.30 | PARAPET_TOP | no line | 1 (0 blank) | 5.99701 .. 6.03701 | 0.0 (0.0) | - | **5.99701 .. 6.03701** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.PARAPET-TOP GF +5.50 | PARAPET_TOP | no line | 1 (0 blank) | 5.592956 .. 5.67398 | 0.0 (0.0) | - | **5.592956 .. 5.67398** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.FINISH PLINTH GF | PLINTH | no line | 29 (0 blank) | 71.68859 .. 72.749795 | 0.0 (0.0) | - | **71.68859 .. 72.749795** | BOUNDED_EXPOSURE / HELD | - |
| NEW FIN.EXT.FINISH SLAB-EDGE GF | SLAB_EDGE | no line | 2 (0 blank) | 1.85426 .. 4.30924 | 0.0 (0.0) | - | **1.85426 .. 4.30924** | BOUNDED_EXPOSURE / HELD | - |
| L-b05f70c92405dbcfbe62 | STOREY | HELD blank | 30 (0 blank) | 469.329178 | 59.150029 (10.56) | 0.0 .. 33.485 | **376.694149 .. 410.179149** | BOUNDED_EXPOSURE / HELD | 469.329178 |

Before = V3.0.59: the three storey lines BLOCKED_RFI blank (never 0); the 15 other lines do not exist. V2.9 + route G:
no FIN.EXT.FINISH face line (NOT_IN_RELEASED). Totals FIN.EXT.FINISH m2 (18 lines): point **152.005** (2F storey
117.305 PROVISIONAL, GF / 2F parapet outer 14.385 / 14.900, 2F parapet top 5.415) + 13 bounded lines; all lines
**1,007.931427 .. 1,085.612926 m2 net** + 1F slab edge blank by name. Hand re-adds: GF 469.329178 - 59.150029 =
410.179149, - 33.485 (W02 28.485 + D-GF-07 5.000) = 376.694149; 1F 265.309300 + 4.715710 x 2 + 0.715029 + 1.252688 +
2.2533924 = 278.961829 (+ moulding steps 0 .. 1.776291) - 30.783772 = 248.178057 .. 249.954348; 2F 125.160 - 7.855 =
117.305 (D-2F-01 2.20 m door, Q-55 C); 1F parapet 53.550644 - 4.223108 + 3.977236 + 0.221319 + 0.427737 + 0.0536522 =
54.00748 .. 59.290836 - 4.585300 + 3.977236 + 0.649056 + 0.6974786 = 60.029307.

## 4b. Run of record (this session, inside the wrapper)

Drive copies decoded by `agent_env.sh decode` into the private folder only (P7757.dxf sha256 ab54dd55, "ST7757 dxf"
9f9d1179). `run research/agents_t167/v304_run.py` -> `run research/agents_t498/v3059_run.py`: V3_0_47 e86a53a8 .. 56
4e25c54f, 57 25a8b406, 58 c9570e6c, **59 75331a76 (candidate of record, T-498 Gate B, reproduced)**. Then `run
research/agents_t314/v3060_apply.py` on that V3_0_59: **V3_0_60 c57a0a42, 5,088 lines = 5,070 byte-identical
(outside_rows_sha256 6e49b30b) + 3 CHANGED (the three storey lines, ids kept) + 15 ADDED + 0 removed**; every V3.0.10 ..
V3.0.59 family check re-run on the result (A3059.integrate) passes; totals move only in FIN.EXT.FINISH|m2:
'HELD (3 blank lines)' -> 'AT_LEAST 152.005 + HELD (14 lines: 13 bounded, 1 blank)'; 126 face rows, 38 holes, each once
(check_faces). Per-line summary: out/summary_t314.json (ids, keys, states, quantities only).

## 4a. Against the freelancer (T-567 bridge, merged; no new reading)

His net 1,469.9675 m2 (invoice row 25 = J93 1,502.84 - half of 65.745) vs these 18 lines 1,007.931 .. 1,085.613 m2:
-31.4 % .. -26.1 %. The difference is the T-567 exact bridge (residual 0): RULE_DIFFERENCE (domes 181.806, owner item
3; pool soffit is FIN.CEILING 12.834; plinth below his +1.00 planes; half vs full holes, Q-73 A), HELD scope of his
(frames 28.8675, boundary 107.24 Q-65 C, drip 50.876 UNKNOWN), UNRESOLVED (his unprinted rows 77 / 78 / 83 / 84) and
ENGINE_RIGHT (row 65 double count 9.000, row 74 no exterior face 52.770, drawn faces in no row of his 162.744). Like
for like (his comparable gross 1,114.8965 vs our faces 1,166.452 .. 1,185.408 incl. the upturn zone): ENGINE_RIGHT
proposal per T-567; the 26.7116 m2 upturn-zone part is the waterproofing item (named MISSING), never in these lines.


## 5. Missing / held (never 0)

W02 (D-53) and D-GF-07 (D-45) holes 0 .. 28.485 / 0 .. 5.000; 1F parapet heights NE-1 / SW-1 / SW-2; NW-2 moulding
steps 0 .. 1.776291; SW pier parapet top; the annex C5 face owner (Q-65 C); plinth bottom at the pool court and plinth
finish; 6 slab-edge faces (depth not printed, Q-68 C), void ring depth, court-front owner (Q-65 C); parapet split height
(D-39). Named MISSING items of this stage (no registry item code yet; a NEW BOQ_FAMILY_MASTER version must own them
before they become lines): FIN.EXT.CORNERS m.l (T-337 710.171878 .. 821.858800 m.l + blank slab-edge arris), coping,
drip, beads, frames, divider, FIN.WP upturn-zone face (4 roofs, with the inner face one face 94.123 .. 99.558 m2).

## 6. Stage status, what is NOT in this stage (r1 hand-back)

- Registry: the head carries engine/source/arch_v3060.py, so the registry tests that check the as_of head
  (t199 test_family_master_1_25_0 x2, t507 test_checks_clean_with_git, and every newer master test of the same kind)
  are red on this branch until a BOQ_FAMILY_MASTER version names ARCH_TAKEOFF_V3.0.60 as pending; 1.58.0 still holds
  T-498 pending, so that version must first PROMOTE T-498 (R-T485-1; the T-525 precedent) - which T-423 r2 / T-563
  (ahead in the Gate B order) will do and renumber. Not built here: it would be thrown away at the renumber.
- L4 to the end, the hub path run (v3060_run.py), the scoreboard exterior plaster row restated: after the rebase.
- New item codes (corners m.l, copings, drips, frames, upturn zone) need a registry family first: named MISSING.

## 7. Lessons-register row (proposal, ERS s.7)

2026-11-09 | a FILL table handed to an integration row was taken from its first ledger (T-337) while two later merged
tasks (T-348 r2, T-567) had re-measured one face, added 11 and removed 2 | the integration input was read from the
row's named ledger, not from the newest merged face set | before wiring, compare the input face set key by key with
the newest merged face set of record and carry every later verified change by name (every villa) |
tests/t314_facade_faces/test_alsenan_inputs.py | proposed.
