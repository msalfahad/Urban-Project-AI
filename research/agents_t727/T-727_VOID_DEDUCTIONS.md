# T-727 V-01 light-well floor / ceiling deductions: the two T-719 findings closed (lane A, research, unwired)

Worker 2, 2026-11-12. Candidate of record ARCH_TAKEOFF_V3.0.72 (T-703 line index). No engine, rule / knowledge version,
registry or candidate file touched; no line moved; V2.9 + route G unchanged. Drawing read this run: Drive "Alsenan
chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf sha ab54dd55, decoded by the wrapper into `.work/private` only)
and a V2.9 run on it kept there. Files: `t727_extract.py` (own read by handle -> `T727_DRAWN.json`, handles / lengths /
areas only), `t727_rules.py` (R-T727-1 .. -4, every villa), `t727_alsenan.py` (builder, 5 inputs sha256-pinned,
`--check`), `out/T727_VOIDS_CLOSED.{json,md}`, `tests/t727_void_union` (16 tests).

## Physical element (ERS 2.1)

Inside the 1F slab opening of the ST-02 light well (outline 26.240 m2, 26.1725 inside the 1F living face) nothing is
floor: the void window, the GF flights seen through it and the cells between them are labels on ONE area, built once.
Above the double-height volume one ceiling closes it at the 1F roof.

## 1. F1 / F4 overlap re-measured by handle

On the 1F plan F4's first riser **B43** (layer 5, 1.150 m) and F1's last line **B4E** (layer 2, 1.150 m) are parallel,
**0.050 m** apart: strip 1.150 x 0.050 = **0.0575 m2**. The engine footprints F1 x F4 overlap 0.057438 m2
(0.05 x 1.15); handle - engine -0.000062 m2 (F1 is radial: its last riser is drawn 1.1498 wide). The GF plan draws the
same pair (22F layer 5 / 234 layer 2), so it is the designer's junction, not a 1F drafting slip. The strip lies inside
the well (0.057438), outside the X-marked void window (0.000).

## 2. Floor: L-b06400d4 1F living porcelain 33.411036 m2 -> **33.411036 (unchanged), ENGINE_RIGHT**

- The net was set by STAIR_FLOOR_RESIDUE_V1 (T-116 piece, wired in V3.0): its record (T-345 TRACE_ROWS, 22 rows) minus
  the T-421 threshold 0.300 re-adds to the net exactly (RECORD_OF_NET, residual 0.000000).
- In that record the flights seen through the well are F1 1.981743 + F4 **3.352442** + F6 1.380 = 6.714185 = their
  UNION (own geometry 6.714230; F4 = 3.410 - 0.0575 overlap): the overlap is deducted once, on F1.
- In-well rows of the record: void 16.005 + flights 6.714185 + VOID_RESIDUE R01 / R02 2.034669 + STAIR_FOOTPRINT R04 /
  R05 / R07..R13 1.418214 = 26.172068 vs face 26.1725: **DEDUCTED_ONCE**, residual +0.000432 m2 (the piece's 0.1 mm
  snap grid, below TOL 0.005). Own geometry (void + union increments + remainder 3.45327): residual 0.000000.
- T-719 compared the face with the BASE list (V2.x split_face: STAIR_BELOW_SEEN 6.771668 = F1 + F4 + F6 summed) plus the
  T-116 residue: DEDUCTED_TWICE -0.057168. That list is stale on this line (T-345 ENGINE_LIST_STALE); it never set the
  net. **T-719 finding (1) withdrawn**; its if-corrected 33.468204 (+0.17 %) is NOT applied: it would put the 0.0575 m2
  stair strip inside the opening back into porcelain floor. Bed line L-ebce765b 33.411036 follows unchanged.
- Freelancer: his 1F living row 38.96 m2 (incl. the landing) is not affected; T-553 / T-240 verdicts unchanged.

## 3. Ceiling over V-01: owner **L-43bf1f86** (decor group 51.0496); L-35341ff2 stays blank, EXCLUDED

- 2F plan (= 1F roof slab) over the well, by type / layer: one INSERT block 'ROOF' (12AA, layer 4), the east dome circle
  2F33 (layer 5) and one column line: **no opening outline**. The roof is closed over the light well, so the ceiling
  over the double-height volume is at the 1F roof soffit, inside the 1F living ceiling face (T-271 / T-283 R2: 'the
  double-height ceiling over the light-well footprint at the 1F roof').
- Decor face split (T-283 ledger): 51.0496 + ST-01 stair zone 10.725 + east dome HELD 14.0359 + ST-01 first going under
  B23 0.1725 = 75.983000 vs face 75.983002. ST-01's own flights F2 / F3 / F5 are 3.687 m from the well (0.000 inside).
  So the decor line carries the well top **26.064062 m2** = 26.1725 - 0.108438 under the east dome (HELD in the dome row).
- L-35341ff2 '1F-R78C367:ceiling over void' (V2.9 base line, blank) names 16.005 = only the X-rect, already inside the
  decor face: **EXCLUDED, cause DUPLICATE_FACE of L-43bf1f86** (R-T727-2); never valued, never 0 by omission.
- GF ceiling L-eb3be58f 101.137092: no ceiling inside the projected well (T-719: ONCE); unchanged.

## 4. V-07 third dome: HELD (VOID_EXTENT_UNRESOLVED)

2F layer-2 circle 1300 r 2.205 drawn 'above'; no opening line on any plan, no structural drawing; S0 / S1 (Q-29 /
T-185) undecided. Nothing deducted from the 2F maid 11.066 / bath 1.624 / shaft 1.619 ceilings; m2 None, never 0.

## 5. Downstream (named, not this task's line)

FIN.MARBLE.TREAD 1F-R78C367 flight 1 (L-6cf11c2d, HELD 0 .. 4.094413) and flight 4 (L-ea55ed31, HELD 0 .. 3.45): highs
7.544413 vs union 7.486974: the same strip, **0.0574 m2 DOUBLE_COUNT_RISK** in the held highs; the stair ledger
(T-725 family) must state F4 as its union increment before any value.

## Rules (t727_rules.py, every villa) and lessons row (ERS s.7, proposed)

R-T727-1 union, not sum (pieces as union increments); R-T727-2 one face, one line (DUPLICATE_FACE exclusion);
R-T727-3 a deduction check reads the record that set the net, never a superseded base list; R-T727-4 no outline stays
HELD. Tests: normal (K727 hand villa: 24.00 opening deducted once, floor 36.00) + adverse (summed overlap -0.05 =
DEDUCTED_TWICE; stale list NOT_THE_NET_RECORD; ceiling face in two valued lines; two owners; no owner; missing outline)
+ mirror / rotation / mm + the development-villa rebuild.

Lessons row: "1F living porcelain flagged DEDUCTED_TWICE 0.057 m2 (T-719) | the check summed the base list's flight
footprints (F1 + F4 overlap 0.0575 on B43 / B4E) while the net came from the piece's union record | deduct the UNION of
void pieces, and audit a line only against the record that set its net (provenance first, then arithmetic) (any villa)
| tests/t727_void_union adverse summed overlap + stale list | closed, no quantity moved".
