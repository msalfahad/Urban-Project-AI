# T-293 part 2: slab-level formwork tied to the candidate concrete lines (slabs, beams, free edges, column joints)

Worker 3, 2026-10-25 17:01 .. UTC, run unknown, branch `agents/task-T-293` (cross-lane: lane I had no claimable TODO).
Research ledger: nothing wired, no candidate or released line changed, no method version, no quantity released.
Integration dependency of T-199 (formwork is a BOQ category the candidate lacks). Development villa, not an accuracy
claim. ERS s.2.1 - 2.6, s.3, s.4 applied. Part 1 (foundations, ground beams, columns: MERGED 294da634) is unchanged.

## 0. Run, identity, sources

Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha `9f9d1179`), decoded into `.work/private` only. Python 3.11.17.

1. T-139 faces: `python3 -I research/agents_t139/slab_faces.py <ST7757> faces.json` (GF 193 / 1F 110 / 2F 95 faces).
2. Formwork r3 reproduced: `research/agents_t163/t163_formwork.py faces.json <dir>` -> FORMWORK_LINES.csv **byte-identical**
   to the merged r3 file (T-163 MERGED 659f889f).
3. Route G band polygons: `research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g
   bands.json` (136 bands, fit 0.6 mm; committed route G data).
4. Walk per face and run: `python3 -I research/agents_t293/t293p2_walk.py faces.json
   research/agents_t293/T293P2_WALK_RECORDS.json --bands bands.json` (785 records: face ids, members, runs,
   categories, m2 only; no coordinate). It asserts the r3 slab-level rows (12 checks) and reproduces every per-floor
   r3 aggregate to 2e-9 m2 with or without the run attribution.
5. Ledger: `python3 -I research/agents_t293/t293p2_ledger.py --write` (committed outputs = a fresh build, tested).

Source rows: the **65** r4 rows of element SLAB / SLAB_EDGE / BEAM / JOINT (formwork r4 FORMWORK_LINES_R4.csv, T-264
MERGED 90203feb; part 1 listed them NAMED). Candidate: the part-1 file CANDIDATE_V3016_CONCRETE_LINES.json; the slab
and beam lines are byte-identical in V3.0.17 (T-254 changed 48 ground-beam / column lines and added the boundary line,
Gate B PASS 13:35); the 49 changed lines' V3.0.17 states are carried beside each face (`line_v3017`, from the T-254
per-line table).

## 1. Physical element and the question (ERS s.2.1)

A formed face bounds ONE member; its formwork is reported beside the candidate line that owns that member's concrete.
On a roof slab: the slab panel soffit (between beam and column faces, T-234 C1), the beam soffit and its sides below
the slab, the full-depth outer face of an edge member (r3 books it in two parts: side below the slab + the
slab-thickness band), and the column joint faces left open by the beams. Question: which candidate line owns every
piece of the 65 slab-level rows, with which status, and does every row close.

## 2. Result: every row closes, residual 0.000 m2 (65 source rows -> 928 pieces)

| r4 rows (m2) | Printed | Tied | Not tied (why) | Lines carrying it |
|---|---|---|---|---|
| Slab soffits E=G CALCULATED | 375.048 (206.684 / 123.479 / 44.885) | **375.0481** (unrounded 206.6845 / 123.4786 / 44.885) | 0 | 62 / 62 STR.CONC.SLAB (one panel each, by panel id T-298; 10 INTERCHANGEABLE pairs flagged) |
| Beam soffits + sides E CALCULATED | 425.209 | **422.6934** | 2.516 DUPLICATE_IN_SOURCE (finding 1) | 107 STR.CONC.BEAM |
| Beam soffits + sides G CALCULATED | 390.835 | **385.2504** | 5.5844 SPLIT_UNRESOLVED (beyond every band end of a split member) | 105 STR.CONC.BEAM |
| Upstands B20 / B23 E=G | 2.400 | 2.400 | 0 | 2 (BM-GF-053, BM-1F-029 lines) |
| Free-edge bands G CALCULATED | 27.747 (15.055 / 8.667 / 4.025) | **27.2059** = beams 24.1443 + columns 3.0599 + slabs 0.0017 | 0.5409 SPLIT | 82 beam / 40 column / 30 slab pieces |
| Column joints G CALCULATED | 9.639 (6.498 / 2.214828 / 0.926) | 9.6392 | 0 | 21 STR.CONC.COLUMN |
| Held rows (beam / joint / edge) | lo 50.466 .. hi 98.765 | lo 48.316 .. hi 95.327 | 0.618 NO_CANDIDATE_LINE (5 unbound band pieces), 0.091 .. 1.257 SPLIT, winder slab 1.44 .. 1.5625 NAMED (part 3) | each on its member's line, blank (never a number) |
| INFO (drawn-outline joints), OWNED_BY_OTHER_LINE (dome openings, pool-court void), sunken panels (no value) | - | - | named | - |

Closure (R-FW-LINE-6 + R-FW-P2-1, `summary_t293_p2.json` `closure`): per (status, method) residual 0.000000 m2 / low /
high. Rows printed to 3 dp (or a 3-dp r3 value + an unrounded r4 delta) carry the unrounded recomputation, asserted to
be within 0.0005 m2 of the printed value; the printed value and the residual stay on the row.

**How the G pieces are attributed to runs (R-FW-P2-5).** 17 members are split by the candidate over 2 or 3 runs (CB1
BAND0041.1 / .2, CB11 BAND0027.1 / .2 / .3, ...). The r3 walk is NOT re-cut: each exact edge piece it found (r2
method) is divided by where it lies, its overlap with each run's band cutter (the route G band's rectangle, widened
0.50 m across its axis only, so a 0.6 mm band-fit error never leaves a side sliver), mapped back from the 5 mm probe
line onto the face's own edge (an end face's probe line lies beyond the band end, the edge does not). Soffits: each
face's area inside each cutter. The parts beyond every band end (support zones, junction pieces) are REST: SPLIT, blank,
the run lines named. Overlapping cutters never divide a piece (0 overlaps on Alsenan). Without attribution 126.6 m2 of
G beam faces and 11.5 m2 of edge bands were SPLIT; with it 5.58 and 0.54.

**Element method per span (R-FW-P2-4):** a T-149 span goes to the run whose own recorded length (T-241 length_m) equals
the span's; all 28 CALCULATED spans of split members matched exactly one run (0 E pieces SPLIT).

## 3. Findings (engineering, for lane I, the Checker and the formwork owner)

1. **F-T293-P2-01 formwork r3 / r4 element method counts CB5 span 2 twice (GF).** `t163_formwork.beam_rows()` appends
   R138 (BM-GF-035.2, CB5 span 2, 0.20 x 0.40 x 3.70, T-145) although `T149_SPANS_INPUT.csv` already holds R138. The
   GF E rows therefore print soffit 55.738 (correct 54.998, +0.740 m2, +1.35 %) and sides 187.103 (correct 185.327,
   +1.776 m2, +0.96 %). The G (drawing-face) rows are not affected. Kept in the ledger as DUPLICATE_IN_SOURCE so the
   rows close; never tied. Verdict proposal: ENGINE_WRONG (formwork r4 E method), fix in the next formwork revision
   (a new r5 file, r3 / r4 untouched); hand check: 0.20 x 3.70 = 0.740; 2 x 3.70 x (0.40 - 0.16) = 1.776.
2. **F-T293-P2-02 BAND0049 has element-method faces but no drawing face.** r3 bound the ring pieces GF-035 / GF-060 to
   BM-GF-049 (hard-coded 'B7 ring band'); r4 replaced them by the T-252 ring (RING-B7 line, 0.666406 m2), and T-252
   (merged) finds BAND0049 outside the ring. The kept candidate line P-C:BEAMS:GF:BAND0049 (0.282743 m3, PROVISIONAL)
   now carries E faces only (soffit 0.377, sides 2.2243 m2): where its drawn face lies in the T-139 partition is not
   established. UNKNOWN, not 0; the G total is not short by a guessed amount. To check by the Checker / T-199 before a
   formwork line is wired for it.
3. **Free-edge bands are edge-member faces.** Of the 27.747 m2 'slab-thickness band at every free edge', 24.144 m2 sit on
   beam faces and 3.060 on column faces; 0.0017 m2 on slab panels. Physically it is the upper 0.16 m of an edge beam's
   full-depth outer face (T-234 C1, D-T163-3): T-199 must report it with the beam / column line, never as slab
   formwork (rule R-FW-P2-2).
4. **CALCULATED faces beside unmeasured concrete lines: 26 pieces, 3.2574 m2** (flag `line_flag`): edge bands on CONFLICT
   / HELD beams (CB2 BM-GF-055 1.09 m2, ...), the 3 CALCULATED 2F column joints (COL-2F-51 / 53 / 54, 0.9265 m2) whose
   column lines V3.0.17 now holds (D-39 roof datum). The face is measurable, the concrete line is not: T-199 must show
   these beside a held line, never as a measured element (R-FW-LINE-5).
5. **Lines with no slab-level face (12 live beam lines):** the D-05 / D-26 strips BM-GF-058 (2 runs), BM-1F-033 (2),
   BM-1F-034 / 035 / 036 / 037 / 038, BM-2F-019 (T-139 classes them EDGE_HELD: their neighbours carry the 'next to
   HELD_EDGE' held ranges; their own soffits / outer faces are in no r4 row) and the two dome ring lines (part 3).
   Listed, never zero: a missing formwork scope that waits on the same designer items as their concrete (D-05 / D-26).
6. **Unbound band pieces:** 5 faces (GF-095 / 151 / 152 / 161 / 167, HELD 0.618 m2 plan) have no member and no line;
   GF-112 is tied to BM-GF-062's line by the merged T-241 naming of that partition face.

## 4. Part 3 (named, not tied in this run; quantities kept)

Stairs (23 r4 rows + the two T-290 delta rows: tie to the T-290 / V3.0.18 stair lines once T-266 merges, MS2-LD drawn
2.935 and riser width 1.20), domes (18 rows: T-290 ledger, ring / drum / shell lines), the water tank (1 row, HELD
D-44), the slab under the main-stair winders (HELD 1.44 .. 1.5625), the sunken-panel faces (HELD, D-41) and the two
OWNED_BY_OTHER_LINE opening bands. F-T293-01 (SB2 cover chord) is a part-1 footing row: carried to the part-3 hand-in.

## 5. Verdict proposals

- Slab soffits: ENGINE_RIGHT on identity (62 / 62 panels, one line each, by panel id).
- Beam G attribution: ENGINE_RIGHT on plan identity for the 17 split members (positional, exact closure); REST named.
- F-T293-P2-01: ENGINE_WRONG (formwork E method double count, 0.740 + 1.776 m2).
- F-T293-P2-02: UNRESOLVED (BAND0049 drawn face).
- Freelancer: no formwork row in any workbook (r3 / r4): FREELANCER_NO_ROW, no %. Owner manual method: none on record
  for formwork; methods E (element) and G (drawing faces) stay side by side, never summed.

## 6. Rules, tests, lesson

Rules R-FW-P2-1 .. 5 (`t293p2_ledger.py` docstring, research scope, any villa; provenance T-293 part 2 on T-163 / T-264
/ T-234 / T-298 / T-241). Tests `tests/t293p2_formwork_slab_line` (24): villa V293P2 by hand (NORMAL: runs A / B sides
1.768 / 2.448, end bands 0.032 each on the BEAM, soffits 0.500 / 0.700, slab edges 1.600, attribution adds up to the
walk, mirror, span-to-run by recorded length, REST kept SPLIT, 3-dp closure; ADVERSE: 0.6 mm band shift changes
nothing, a gap between band ends stays REST, overlapping band ends never divide a piece, pieces that do not close are
refused, a held row cannot gain a quantity, two equal-length runs / no exact length -> member) and Alsenan pinned
(65 rows once, closure, 62 panels, the CB5 duplicate, split 5.5844, ring and BAND0049, untied pieces, V3.0.17 states and
flags, held blank, committed outputs = fresh build, no coordinates in the walk file).

Lessons row (proposed, ERS s.7): 2026-10-25 | A derived-trade aggregate (formwork per slab level) was walked on drawing
faces that are not the candidate's line partition (one drawn face spans two candidate runs) | Splitting by length or
order would have bound CB4's faces to the wrong run (T-264's oblique-end evidence) | Attribute a merged walk to lines by
where each measured piece lies, never re-cut or re-classify it; prove the attribution adds up to the walk exactly; the
part beyond every line's extent stays unresolved and named (PROJECT-INDEPENDENT) | tests/t293p2_formwork_slab_line |
OPEN (T-293 part 2 READY).

## 7. Checker re-measure

(a) one split member: CB1 BM-GF-042 face GF-104 -> BAND0041.1 soffit 2.5095 / sides 8.5351 m2, BAND0041.2 1.7849 /
4.3920, REST 0.0756 / 0.2495 (+ the r4 CB1 void face 2A9 piece, SPLIT): bands 7.4 / 5.1 m long x 0.35, D 0.75;
(b) the CB5 duplicate: `T149_SPANS_INPUT.csv` row R138 and `t163_formwork.beam_rows()` (its last append) -> E GF
soffit 54.998, sides 185.327; (c) one slab panel: GF-015 2.5725 m2 -> its T-298 join line; (d) one edge band: GF-011
(B24, BM-GF-046) EDGE_BAND 0.888148 on the B24 line, not on a slab line.
