# T-530 WIRING MANIFEST of the merged, unwired pieces T-516 .. T-528 on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-05, claim 15:03 UTC, run session_01E6cPneRhfF3rG8S4BCdXWy,
engine base 1c0ac911. Files: `WIRING_MANIFEST_T530.json` (this folder) and `tests/t530_wiring_manifest/` (builder
`manifest_t530.py` + 19 tests). No candidate, released (V2.9 + route G), rule, knowledge, registry or producer file is
touched; nothing is wired. Every figure in the JSON is recomputed by the builder from the merged piece outputs (their
committed out/ files and their own functions) and the V3.0.57 line index; the test asserts the committed JSON byte for
byte against the rebuild (no hand-typed number). Drawings by Drive title only: "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55), decoded this run into the private folder for the two pieces
that read it at run time (T-517 hatch, T-522 sill / bay); without it the stream F rows stay HELD and the full test skips.

Candidate of record: V3.0.58 = the V3.0.57 index (25a8b406, 4,994 lines) + the 5 T-507 lines (from T-507's run table).

## 1. Stream S, lintels: 16 STR.CONC.LINTEL lines (B9-02), every one RELEASED today

| lintels | before (m3, released) | after | source / rule |
|---|---|---|---|
| D-1F-02, D-1F-08, D-2F-01, D-GF-13, W14, W15 (BEARING_OK) | 0.502 | BOUNDED_MIN_BEARING: low = B D (w + 0.80) = today's value; high = B D (w + a_s + a_e): 0.13197 / 0.14208 / HELD (D-2F-01, pier >= 3.0 m, no ceiling) / 0.11292 / 0.246 / 0.11348 | T-516 R-T516-1, T-519 R-T519-1 (PROJECT_RC, 1 piece each, cast to length) |
| D-1F-03, -04, -07, -10, D-2F-03, D-GF-06, -10, W18 (deficit) | 0.418 | HELD BY NAME, bound beside: e.g. D-GF-06 0.056 .. 0.0616, W18 0.034692 | T-516 + T-524 R-T524-1 |
| D-GF-11 + D-GF-12 (shared 0.238 m pier) | 0.096 | both HELD BY NAME; the PAIR bound 0.060 .. 0.07914 carried ONCE (on D-GF-11), split = designer | T-524 |

Code view: 1.016 m3 released -> HELD (6 bounded, 10 held by name), AT_LEAST 0.874692 m3 (0.502 + 0.372692); upper
known part 1.183992 + D-2F-01 HELD. Removed from B9-02 0.076458 m3 = inside columns 0.037838 (STR.CONC.COLUMN lines
already hold it, untouched) + lintel on lintel 0.016860 + not built 0.021760 (conserved, asserted). Owner: register
'RC LINTEL vs host masonry' + 'LINTEL END VOLUME'.

## 2. Stream S, host material lines (on the T-498 stage) and perimeter mortar

Of the 12 T-453 host rows that deduct one of the 16 faces, 10 stay blank (host HELD on V3.0.58; L-9056 is T-523
STALE_CLASS). Two valued AAC glue lines move (face = D x [L_lo, L_hi] of the lintel line):

| host (T-498 stage line) | before kg | after kg (range by name) |
|---|---|---|
| L-2fdc0f97 1F 0.20 VERIFIED white (L-4b9a29d4): W14 / W15 bounded, W18 held | 444.4695 .. 451.2195 | 443.27313 .. 451.60893 |
| L-a3f88ecd GF 0.20 OA white (L-d14c6c9b): D-GF-06 held | 23.535 | 23.769 .. 23.895 (T-453 over-deducted 0.052 .. 0.080 m2) |

AAC glue group (R-T523-1, T-523's own function): AT_LEAST 35.42625 .. 36.19665 -> 35.387755 .. 36.226627 bags, to buy
>= 36 .. 37 unchanged, HELD.

Perimeter joint mortar (T-520, own key, never in the panel key): 2 NEW MAS.MORTAR.BLACK lines on the valued 0.20 black
hosts: GF L-1c53fadb (GF-W01) 0.058854 m3; 1F L-10dd62f6 (1F-W02 / W03 / W09) 0.039291 m3; total 0.098145 m3 = +7.73 %
on the 1.269444 m3 panel mortar; cement 0.785160 bags, sand 0.107959 m3 beside (Q-78 A). T-526 confirms 1F-W09
0.010355 (C-S3, one write). 0.15 m walls / 2F D-39 / GF-W22 D-27: figures beside, HELD. Villa cement group: AT_LEAST
130.816567 .. 172.286014 -> 131.601727 .. 173.071174 bags (one ceiling >= 132 .. 174), HELD.

## 3. Stream F, pool court (V3.0.58 lines of T-507)

| line | before | after | piece |
|---|---|---|---|
| L-1954878b window_face ROOF_UPTURN lm | HELD 0 .. 0.500002 | 0.500002 MEASURED (sill '84' printed) | T-522 R-T522-1 |
| L-d7d1bf8c ledge ROOF_UPTURN lm | HELD 0 .. 3.528277 | HELD 0 .. 0.551615 (wall ends); glazing piece leaves the line | T-522 R-T522-2 |
| NEW FIN.WP.DOORWAY_TRANSITION m2 | - | HELD blank, 2.976663 lm beside (code is m2: F-T530-4) | T-522 |
| L-2361d6ec ledge ROOF m2 | HELD 0 .. 0.639573 | unchanged (exposure decision, rule V2 needed) | T-522 R-T522-4 |
| NEW FIN.ROOF.FINISH m2 open sky | - | 4.519172 MEASURED (hatch 1250 + 1253) | T-517 |
| NEW 7 lines: screed x2 (m3), insulation x2, protection x2, ledge finish | - | HELD blank by name | T-517 |

Totals: FIN.WP.ROOF_UPTURN 186.782544 -> 187.282546 lm (+0.27 %); FIN.ROOF.FINISH 202.219760 -> 206.738932 m2
(+2.23 %); FIN.ROOF.SCREED / INSULATION / PROTECTION / DOORWAY_TRANSITION: no valued line, printed HELD, never 0.0.

## 4. FINISH V6 / V7: 0 candidate lines

V1..V7 are read by no candidate method. V6: on all 88 T-511 reader rows (44 keys) V6 procurement = T-500 PROCUREMENT and
V6 installed (V5 / 1.05) = T-500 INSTALLED (max diff 8e-6, 6-decimal rounding): V6 stays a READER, no binding stale.
V7 stair: on the 11 computed STAIR_BED_V1 keys installed agrees (1.062939 m3 = 10.178704 bags at 9.576 / m3) but
procurement differs: 10.62939 (allowance) vs 10.687639 (Q-45 5 %): C-V7, HELD until F-T518-2 is ruled.

## 5. Stale bindings

Carried: 21 T-523 bindings stale on V3.0.57 (7 T-453 lines), resolved by the T-498 resume reading V2 fresh figures.
Go stale by this wiring: 16 lintel concrete bindings + 4 glue bindings (2 hosts). F-T530-1: T-523 marks all 60
lintel bindings NO_CANDIDATE_LINE, but the candidate has 60 STR.CONC.LINTEL lines (T-487): 60 / 60 map 1 : 1 by
element id; the S package binds them first.

## 6. Conflicts and order

C-S1 lintel deficit lines: T-516 then T-524 (one write). C-S2 host glue: T-498 creates the lines, then the ranged face
(RG-1: R-T498-1 has no case for a bounded / ranged face: a rule version is needed, F-T530-2). C-S3 1F-W09 perimeter:
T-520 = T-526. C-S4 W18 / curved bays: T-527 (TODO) touches no value here; re-check W18 when it merges. C-F1 T-517's
upstand length 5.193544 lm predates the T-522 window run: T-522 first, upstand 5.693546 lm (height HELD). C-V7 above.
F-T530-3: register 'POOL-COURT SLAB' says FIN.WP.ROOF never takes the slab, T-507 (Gate B) books it there: wording.

## 7. Proposed packages

- S (on T-498 r3, after T-525): 16 lintel lines moved + 2 staged glue lines moved + 2 perimeter lines added; order
  T-525 -> T-498 -> lintel binding ids -> lintel lines -> host faces (RG-1) -> perimeter -> groups.
- F (independent of S, on V3.0.58): 2 lines moved, 1 named unchanged, 9 added; FINISH V6 as reader only; V7 after
  F-T518-2. The first package merged takes V3.0.59 (T-498 holds that stage); the second renumbers.
- Both blocked by the wrapper allow-list for their Drive-chain runs (Lead item), not by this preparation.

## 8. Verdicts, lessons

Engine vs freelancer: no freelancer lintel, mortar, glue or screed row; roof WP 285.00 m2 single line (cells not read):
UNRESOLVED / RULE_DIFFERENCE, unchanged by this manifest. Lessons row (proposed, ERS s.7): | 2026-11-05 | 9 verified
pieces each printed its own 'effect if wired' on its own base; two read the same line (T-516 / T-524, T-517 / T-522),
one assumed no line existed (T-523 lintels), one rule has no case for the new state (R-T498-1) | effects were never
recomputed together on the candidate of record | before a Gate B package, one test-checked manifest recomputes every
piece's after-value on the candidate's line ids, names every line two pieces move with the order, and every binding /
rule the move makes stale (every villa) | tests/t530_wiring_manifest | proposed |
