# T-696: MASONRY ROUND 3 on ARCH_TAKEOFF_V3.0.68: the blank B9 lines by host and cause + R-T696-1 directed rounding

Worker 2, 2026-11-11. Lane A research piece, non-candidate: `research/agents_t696/*`, `tests/t696_bound_rounding/*` only.
No engine, rule / rulebook / knowledge version, registry or candidate file changed; nothing wired or released. No drawing,
workbook, client name or coordinate here. Read this run (Drive 'Alsenan chalet project', read-only, private copies only):
'P7757_DXF_COMPRESSED.zip' -> P7757.dxf (ab54dd55) and 'ST7757 dxf.dxf' (9f9d1179), for the candidate re-run (s.4).

## 1. Physical element (ERS s.2.1)

Each B9 material line is the units / joint mortar / perimeter joint / AAC glue of ONE host masonry line (MAS.BLOCK):
its quantity exists only as far as the host's block area exists. A host with no drawn end gives no material end. A
host whose area has ONE drawn end gives a one-ended material figure that stays BESIDE the HELD blank line (a range needs
two ends; a point is never picked; never 0). Installed quantities only; waste / procurement and bag rounding stay HELD.

## 2. (a) Census of the blank lines (V3.0.68: UNITS.BLACK 12, MORTAR.BLACK 12, PERIMETER 12, GLUE.AAC 10, UNITS.WHITE 15)

`t696_b9_census.py` -> `out/T696_B9_CENSUS.json` (61 rows, one per blank line: host, cause class, host bound, beside).

| Host group (lines) | Cause class | Why HELD | Drawn host bound | Material beside (R-T696-1) |
|---|---|---|---|---|
| 2F part hosts: 3 black (L-e1e06ec1 OA 0.15 W08, L-a6eedf5e DC 0.20 W05 part, L-76a4d8e5 V 0.20 W01+W06), 3 white (L-9056ebed OA 0.15 W03 part, L-bbb82de2 DC 0.20 W02+W07 parts, L-e90c9dd5 V 0.20 W04) | DESIGNER ITEM (D-39) | roof structural level / build-up b_r not printed; wall = U - L b_r (T-482 / T-488) | AT_MOST U at b_r = 0 (b_r >= 0: the structural top cannot sit above the finished +13.90); lower end open (P1 'b_r < 0.30' not keyed to this roof) | black: units AT_MOST 118.375 / 48.125 / 274.3125 pcs; mortar AT_MOST 0.104762 / 0.056788 / 0.323689 m3; white glue AT_MOST 90.6325 / 73.0125 / 98.04375 kg; perimeter and white units none |
| 7 parents (GF 0.15 / 0.20 / 0.40, 1F 0.15 / 0.20, 2F 0.15 / 0.20) x 3 black + glue + white | OPEN BOUND | BLOCK_WALL_NOT_ESTABLISHED: held walls / pieces no part line carries, colour not split | none: every parent holds >= 1 wall with no drawn end (annex storey not declared, no drawn piece, unsized lift tie beam ST p.8 n.19, opening width not drawn, dome-opening top not drawn, unlabelled members D-04); drop walls only AT_MOST | none |
| MAIN_S (black x 3) | OPEN BOUND | ST p.1 note 2 black block below the neighbour-side beams; h >= 0.70 m only, leaf not printed | AT_LEAST 11.389 m2 net (T-407 / T-675) | units AT_LEAST 142.3625 pcs; mortar AT_LEAST 0.125990 m3 (one 0.15 leaf, CONDITIONAL; T-675 printed 0.125991, half-way ABOVE the exact 0.12599081: -0.000001) |
| ANNEX_S (black x 3) | DESIGNER ITEM (D-35) | annex beam soffit CONFLICT | none | none |
| 5 valued white hosts (UNITS.WHITE only) | RULE NOT GIVEN | AAC face not selected (Q-60 two supplier faces, no count rule) | area VALUED | none (producer's 6.4 / 8.33 per m2 alternatives stay beside) |

Hand checks (any reviewer): W08 (9.79 - 0.32 D-2F-03 face) x 12.5 = 118.375; x 0.0110625 = 0.104761875 -> UP 0.104762;
W05 3.85 x 12.5 = 48.125, x 0.01475 = 0.0567875 -> 0.056788; W01 + W06 (6.93 + 15.015) x 12.5 = 274.3125, x 0.01475 =
0.32368875 -> 0.323689; W03 (26.255 - 0.36 D-2F-01 face) x 3.5 = 90.6325 kg; W02 + W07 (9.865 + 6.36) x 4.5 = 73.0125;
W04 21.7875 x 4.5 = 98.04375. A HELD lintel face (D-2F-02, W26 .. W29) deducts 0 so the end stays an upper end; the
REQUIRED faces hold for b_r < 0.99 m (T-488) and beyond that U - 0.99 L is below U - face, so the end holds for any b_r.
The 2F perimeter joint stays HELD (its vertical bands depend on b_r: T-520 figure only).

Why the parents give no bound (register T-449 r3, re-checked on the V3.0.68 run, s.4): e.g. GF 0.15 holds GF-W23 .. W27
(slab / beam pieces with STOREY_HEIGHT.GF.ANNEX not declared), GF-W30 (no drawn piece) beside the drop walls W20 / W31 /
W32 / W34 (U - L d) and W22 CONFLICT [12.9311, 12.9439] m2 (D-27); 1F 0.15 holds 1F-W11 (dome ring face), W13 / W17 /
W24 dome-opening pieces (top not drawn, T-227), W14 + W15 / W16 (opening width not drawn). A sum with one open term
is open.

## 3. (b) F-V672-1: R-T696-1 BOUND_ROUNDING_V1 (new research rule version; the frozen producers are not edited)

`bound_rounding_v1.py`: a bound's LOW rounds toward minus infinity and its HIGH toward plus infinity at the reporting
precision (6 dp); a point keeps half-up; the ends are the exact decimal products / sums of the line's own inputs (a
half-way-rounded intermediate is refused as an end); a measured length recorded at 4 dp enters as its +/- 0.00005 m
interval; local decimal context only (F-T648-2). `t696_b9_bounds.py` restates all 15 bounded B9 lines of V3.0.68 from
the merged ledgers (T-670 bases, T-675 bearings / bands / pieces, T-520 wall lengths), each recomputed end asserted to
reproduce its ledger figure.

| line | code | V3.0.68 | R-T696-1 | delta (low / high) | exact ends |
|---|---|---|---|---|---|
| L-686a15f1 D-1F-09 | LINTEL_BEARING m3 | 0 .. 0.001111 | 0 .. **0.001112** | 0 / +0.000001 | 0 .. 0.0011115 |
| L-5b828080 D-1F-03 | LINTEL_BEARING | 0.000556 .. 0.000887 | **0.000555 .. 0.000888** | -1e-6 / +1e-6 | 0.00055575 .. 0.0008871437 |
| L-e5cefb37 D-1F-04 | LINTEL_BEARING | 0.000556 .. 0.000667 | 0.000555 .. 0.000667 | -1e-6 / 0 | .. 0.0006666221 |
| L-ae1d4bef / L-ba28032b D-1F-07 / -10 | LINTEL_BEARING | 0.000556 .. 0.000916 | 0.000555 .. 0.000917 | -1e-6 / +1e-6 | .. 0.0009160149 |
| L-dc668eb5 D-GF-10 | LINTEL_BEARING | 0.000556 .. 0.000907 | 0.000555 .. 0.000908 | -1e-6 / +1e-6 | .. 0.0009072619 |
| L-866a6602 1F 0.15 OA | MORTAR.BLACK m3 | 0.618315 .. 0.622076 | 0.618315 .. **0.622077** | 0 / +1e-6 | 0.6183152 .. 0.6220765 |
| L-c5969291 1F 0.15 OA | PERIMETER m3 | 0.028344 .. 0.049793 | **0.028342 .. 0.049797** | -2e-6 / +4e-6 | 0.0283429 .. 0.0497965 |
| L-3b5eff6c 1F 0.15 V | PERIMETER | 0.018729 .. 0.019896 | 0.018728 .. 0.019897 | -1e-6 / +1e-6 | 0.0187285 .. 0.0198963 |
| L-dfe9524c GF 0.15 OA | PERIMETER | 0.010361 .. 0.011195 | 0.010360 .. 0.011195 | -1e-6 / 0 | 0.0103604 .. 0.0111947 |
| 5 others (UNITS L-1e61a4aa, 3 GLUE, PERIMETER L-43e616ee) | | unchanged | unchanged | 0 | exact at <= 6 dp |

By code (bounded lines, never summed across codes): LINTEL_BEARING 0.002780 .. 0.005404 -> 0.002775 .. 0.005409 m3;
PERIMETER bounded 0.072178 .. 0.108325 -> 0.072174 .. 0.108330 m3; MORTAR.BLACK bounded high 0.622076 -> 0.622077 m3;
UNITS / GLUE unchanged. 10 of 15 lines move, all by <= 4 x 10^-6 m3; in 10 of 15 the V3.0.68 print did NOT contain the
exact interval (the five deficit-bed lows 0.000556 sat ABOVE the exact 0.00055575; the D-1F-09 / -03 / -07 / -10, D-GF-10, mortar
and two perimeter highs sat below their exact highs). Cause: half-way rounding of each end, and for the perimeter the sum of three half-way-rounded components
(T-372 drawn high + bands + pieces: 0.032121 + 0.012199 + 0.005473 = 0.049793 vs exact 0.0497965).

## 4. Candidate re-run (private, read-only) and checks

Own fresh run this task (private folder, read-only): `research/agents_t167/v304_run.py` (32 min) then
`research/agents_t672/v3068_run.py` (19 min, exit 0): every version re-asserted, V3_0_67 a29a11a9 -> **V3_0_68 d1de50cb**,
5,105 lines = the T-672 run of record (the committed LINE_INDEX_V3_0_68 inputs.lines). `t696_b9_census.py --candidate`:
all 61 census rows AGREE (blank, BLOCKED_RFI, host named in the rfi), disagree []. The 7 parent questions on V3.0.68
list exactly the register walls of s.2 (plus T-488: GF-W34 U 10.4121, GF-W22 CONFLICT [12.9311, 12.9439] on GF 0.15,
the 2F roof-datum walls named on the 2F parents with the U - L b_r forms used in s.2: W08 9.79 - 3 b_r, W03 26.255 -
7.4 b_r, W01 6.93 - 1.8 b_r, W06 15.015 - 3.9 b_r, W04 21.7875 - 6.225 b_r, W05 3.85 - b_r, W02 9.865 - 3.47 b_r, W07
6.36 - 2.7 b_r). Nothing from the run is committed but these ids and figures.

## 5. Verdicts, freelancer, lesson

Freelancer: blockwork in m2 only; no unit / mortar / glue / perimeter / bed rows: RULE_DIFFERENCE, no %. Proposals:
(a) census ENGINE_RIGHT on the hold (every blank line has a named host cause; no host bound is invented); the 2F
AT_MOST and MAIN_S AT_LEAST figures ENGINE_RIGHT as one-ended bounds, UNRESOLVED as quantities (D-39 / leaf build);
(b) the restated bounds ENGINE_RIGHT (exact ends inside), the V3.0.68 prints ENGINE_WRONG by <= 4e-6 m3 (rounding
direction, not geometry). Lesson row (ERS s.7, proposed): "a printed bound must still contain the exact quantity: round
a low down and a high up from the exact inputs, never from rounded components (every villa; T-696)".

## 6. Held / missing / for the wiring row

- Wiring (Gate B, not here): apply R-T696-1 at the bound producers (bed, perimeter envelope, material base ranges) in a
  new method version; the 2F AT_MOST / MAIN_S AT_LEAST figures go beside their HELD blank lines.
- HELD: D-39 (b_r), D-35 (annex soffit), the parents' open walls, AAC face (no count rule), waste / procurement.

## 7. Validation

`tests/t696_bound_rounding` (23): hand villa M (held-lintel bed 0.0011115 -> 0.001112, never 0.001111; deficit bed;
mortar range; exact-at-precision not widened; point half-up; one-ended AT_MOST after a REQUIRED face, AT_LEAST, glue;
adverse: None / NaN / bool, inverted bound, rounded end refused, bad precision, mm length, mirror order, missing glue
rate, faces above the area, global decimal context untouched) + the development-villa regression from merged files
(counts 12 / 12 / 12 / 10 / 15, 11 beside figures, 15 bounded lines, 10 moved, every exact end inside, tampered index
refused). Freeze 0; codemap rebuilt by the tool.
