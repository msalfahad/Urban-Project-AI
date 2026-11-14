# T-789 masonry open items: parapet block, 1F 'projections', below-ground basis (worker 2, lane A, 2026-11-14)

Fix rows only (`t789_fill.py --check`, out/FIX_ROWS.json); rule R-T789-1 in `t789_rules.py` (every villa); tests
`tests/t789_parapet_masonry` (synthetic villa, normal + adverse). No engine, method, rule / knowledge version, registry
or candidate file changed. Base: ARCH_TAKEOFF_V3.0.84 line index.

## 1. Parapet block (F-T789-1..4): 0 m2 DRAWING-READ, the whole run is already billed in concrete

Physical element: each parapet run from the structural slab top to its printed top, H = printed height above the
finish (0.50 annex / GF / 2F; 1F 0.448 .. 1.30 per run; 1F NE-1 / SW-1 / SW-2 unprinted -> company default 1.20)
+ roof build-up 0.175 (company default). Evidence: this villa's sections A-A / B-B cut every parapet in the slab / edge
beam hatch with the block walls unhatched (T-311 s.2); ST slab plans 'check architectural detail of parapet before
casting'; ST p.14 P2 / P3 are all RC; only the unkeyed 'typical' P1 shows block on a 0.30 RC upstand. The candidate
already bills every run all-RC: STR.CONC.PARAPET 24.37 m3 (T-761, wired). `t789_fill.py` rebuilds that figure run by
run from the T-742 run ledger (asserted per chain: annex 4.048, GF 3.7752, 1F 12.8892, 2F 3.6551 m3), so a block line
on top would bill the same body twice. R-T789-1: masonry = complement of the concrete reading, never both. The four
T-742 draft lines (HELD 0 .. 101.46, never wired) close as NO_LINE, 0 HELD parapet masonry lines remain.

Centreline 136.157 m = T-742 run low ends (drawn on the roof plan, T-742 s.3); the row's 136.84 m is the high ends
(SW-3 +0.20, SW-9 +0.405, SW-2 +0.075).

Ready alternative (if the designer keys P1, item 5 / Q-65 C): block 82.32 m2 (annex 11.24, GF 10.49, 1F 49.70, 2F 10.89)
and concrete 24.37 -> 8.05 m3 (-16.32), both swapped together. The row's literal reading (1.20 less 0.30 from the
finish, b_edge 0) gives 58.50 m2: it puts the upstand top 0.175 below its printed position, so it is not used.

Against the freelancer: his three parapet rows 172.93 m2 of block vs ours 0 m2 block + 24.37 m3 concrete:
RULE_DIFFERENCE on material (designer item 5); of his 172.93, 68.42 is the 0.50 m below the finish (edge member
concrete, ENGINE_RIGHT, T-550) and 7.63 his flat 1.80 vs printed 1F heights (ENGINE_RIGHT). Under P1: ours 82.32 vs
his 172.93 (-90.61 = 68.42 + 7.63 + length / datum 14.56 named in T-550).

## 2. 1F 'projections' 41.25 m2 (his BLK row 78, 7.50 x 5.50): candidate element named, no new line

Read this run: Drive 'Alsenan chalet project' / Alsenan_Architectural_P7757_Pages_07-08 (SW and NW elevations), with
T-550 (four elevations, two sections, GF plan) and sheet 09 (T-779). Description: the SW elevation draws a narrow
projecting band at the left end of the 1F facade running from the GF roof up to the 1F parapet top; by the printed
levels that is +5.50 -> +9.70 + 1.30 = +11.00, i.e. 5.50 m, the only 5.50 m vertical span found on the two elevations read. Its
plan length is not printed on these sheets (no 7.50 dimension on either elevation; nothing scaled from the image).
Map: DIFFERS in kind, not missing: that face is the 1F external wall (MAS.BLOCK 1F, clear height under the members)
plus the 1F parapet (STR.CONC.PARAPET); both are already billed. The NW arch frame is about 4.4 m wide by its printed
dims (43 + 15 + 269 + 5 + 75 + 30 cm) and does not match. Status UNRESOLVED (named): his row most likely re-bills the
1F wall + parapet face of the projecting 1F bay that his storey rows also contain, or covers a wall his 1F list lacks;
which, needs his per-wall rows. No line is added (it would double count). BOQ lines affected: none.

## 3. Below-ground basis (F-T789-5, supersedes F-T779-1 text)

MAIN_S 16.27 x 0.70 = 11.389 m2 ESTIMATE unchanged; 0.70 = slab -0.10 down to the governing ground-beam band top -0.80
(T-407 lower bound), not the footing top -0.85 (Checker F-V779-2).

## 4. Numbers

Masonry lines without figure (parapet family): 4 HELD drafts -> 0. Blockwork vs freelancer: ours 981.35 vs 1,260.69 m2
(-22.2 %); parapets 172.93 RULE_DIFFERENCE (material) / ENGINE_RIGHT (datum); projections 41.25 UNRESOLVED (named,
3.3 %); like-for-like storey walls -0.94 % (T-779).

Lesson row (proposed): a missing masonry family for an element already billed whole in another trade is closed as the
complement of that trade's reading, not filled by a default (R-T789-1; tests/t789_parapet_masonry).
