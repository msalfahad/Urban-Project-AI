# T-214 Floor build-up FFL -> structural top, per floor and zone: drawing-derived beside the owner manual method

Worker 1 (lane S), 2026-10-23, run session_01LKVtscw1NmPLZ6M27VrNc4. Development villa, not an accuracy claim. ERS read;
s.2 steps 1-4, s.3 (a value's meaning before its arithmetic; finished vs structural datum), s.4, s.7 applied. Files:
research/agents_t214/* and tests/t214_floor_buildup/* only (no engine module, method, rule / knowledge version, registry,
candidate or released quantity changed). Drawings cited by Drive title / view / level only; no coordinate, image or
client data committed.

## 1. Result in engineering terms

**The issued set does draw the floor build-up: an unhatched 0.05 m layer between the FFL marker line and the hatched
slab on every floor band cut by SECTION A-A and SECTION B-B.** T-200 / T-206 called it "printed nowhere" after reading
the sections as 200 dpi rasters, where 0.05 m at 1:100 is 0.5 mm (4 px) beside a hatched band. It is not dimensioned
(no text), so it is a DRAWN, unprinted value, established the way T-201 established window heads: vector geometry,
datum of the same view, and checked on the current issue.

| Floor / zone | FFL | Drawing-derived b (FFL -> slab top) | Slab top | Owner manual method beside (own scope only) | Residual drawn - owner |
|---|---|---|---|---|---|
| GF main, dry | +1.00 | **0.05 DRAWING-CONFIRMED** (drawn, unprinted) | **+0.95** | Q-43 0.10 (wall-height allowance); Q-45 bed 0.030 .. 0.043 + tile | -0.05 (different scope); +0.007 .. +0.020 = the tile, unprinted |
| Annex, dry | +0.30 | **0.05 DRAWING-CONFIRMED** | **+0.25** | as GF | as GF |
| 1F, dry | +5.50 | **0.05 DRAWING-CONFIRMED** (0.049 .. 0.051 between sources) | **+5.45** | as GF | as GF |
| 2F, dry | +9.70 | **0.05 DRAWING-CONFIRMED** | **+9.65** | as GF | as GF |
| GF wet rooms | +1.00 | HELD (no section cuts one; the dry layer is not carried to a wet zone) | HELD | Q-45 wet bed 0.040 .. 0.063 + tile + membrane + 1 % fall; Q-41: bathrooms bed only, no separate screed | - |
| 1F sunken wet panels x5 (HATCH 275 / 276 / 280 / 287 / 298) | +5.50 | HELD: the drop is printed nowhere (D-41) | HELD | as GF wet | - |
| 2F sunken wet panel (HATCH 5BF) | +9.70 | HELD (D-41) | HELD | as GF wet | - |
| GF-roof terraces +5.50, 1F-roof terrace +9.70, annex roof +4.30 | finished roof | HELD: the drawn layer is the same constant 0.05, which cannot carry the printed SLOPE 1 % (sanitary-7757) | HELD (D-39) | Q-41 screed over the membrane (thickness not given); Q-45 falls | - |
| Main roof +13.90 | finished roof | HELD: constant 0.05 drawn; no slope printed, so the owner's Q-45 falls (0.5 % per m) apply | HELD (D-39) | as above | - |

Measured (metres below the level line; `section_bands.py` on the architectural .dwf; the level line is the apex of the
level marker under each level text, and one translation reproduces all six markers of each view to 1.8 mm):

| View, level | Line below the level line | Hatch (concrete) span | Current issue (400 dpi band profile, 6.35 mm / px) |
|---|---|---|---|
| A-A +1.00 | 0.050, 0.200 | 0.049 .. 0.200 (119 strokes) | p7757_arch_sheet10: 23.0 / 7.5 px = 0.146 / 0.048 |
| A-A +5.50 | 0.049 (over 8.60 m of the cut), 0.200 | 0.049 .. 0.199 (90) | sheet10: 23.5 / 8.0 px = 0.149 / 0.051 (six positions along the band, all 8.0 +- 0.5 px) |
| A-A +9.70 | 0.050 (over 7.10 m), 0.200 | 0.050 .. 0.200 (73) | sheet10: 23.0 / 8.0 px = 0.146 / 0.051 |
| A-A +13.90 (roof) | 0.050, 0.201 | 0.050 .. 0.200 (70) | - (roof: refused, see s.3) |
| B-B +0.30 (annex) | 0.050, 0.150, 0.201 | 0.050 .. 0.200 (43) | Pages_11-12 p.11: 23.5 / 7.5 px = 0.149 / 0.048 |
| B-B +1.00 | 0.050, 0.200 | 0.049 .. 0.199 (191) | p.11: 23.5 / 7.5 px = 0.149 / 0.048 |
| B-B +4.30 (annex roof) | 0.050, 0.200 | 0.049 .. 0.199 (41) | - (roof) |
| B-B +5.50 | 0.049, 0.200 | 0.049 .. 0.199 (223) | p.11: 23.5 / 8.0 px = 0.149 / 0.051 |
| B-B +9.70 | 0.050, 0.200 | 0.049 .. 0.200 (204) | p.11: 24.0 / 8.0 px = 0.152 / 0.051 |

The DWF logical unit is about 2.1 mm of drawing, so 0.049 / 0.050 are one value; the scan readings agree within 3 mm
(TOL_DRAWN 10 mm). Reading b = 0.05 m.

## 2. The physical element and the meaning of each number (ERS s.2 step 1, s.3)

b is the thickness of everything between the finished floor (FFL, a FINISHED datum printed on the plans and sections)
and the top of the structural slab under it (a STRUCTURAL datum the structural set never prints, T-200 / T-206): tile,
adhesive, mortar bed / screed / fill, membrane where present. It is a level relation, so it is a DATUM question.

- **The drawn layer (drawing-derived method).** The architect's cut draws each floor as two layers: a hatched 0.15
  (concrete in these sections, T-201 s.7) and an unhatched 0.05 above it, with the FFL marker on the top line. The
  0.05 is therefore the architect's floor build-up between the FFL and the structure line. The same architect's cut gives
  the pool its 0.05 build-up (-0.85 finished floor over the -0.90 structure line, VERIFIED, T-183 r2), read the same way.
- **The hatched 0.15 is not the slab thickness.** The structural set prints 0.16 for suspended slabs and 0.10 for the
  ground slab (T-200). Following the T-183 r2 ruling (structural detail governs the RC thickness, the architectural cut
  the levels), the 0.15 is not used; the soffit comes from the structural thickness (1F soffit +5.29, 2F +9.49, GF
  ground-slab underside +0.85). Named residual: if the architect's drawn underside (FFL - 0.20) were the fixed surface
  instead of the build-up line, b would be 0.04 on the suspended floors and 0.10 on the ground slab; the drawing fixes the
  build-up line (its own two drawn lines), not the underside, so 0.05 is the drawing-derived value and 0.04 / 0.10 are
  recorded as the residual alternative, not chosen.
- **Q-43's 0.10 is a finish allowance in a wall-height formula, not a level datum.** The owner's words (Q-43, 2026-10-19
  21:40): "4.5 m floor height - 0.6 m beam - 0.15 to 0.20 m decor ceiling - 0.10 m floor finishing = 3.65 m, the height
  that plastering and paint count". It is given inside the plaster / paint height rule and nowhere as a level; with the
  marks read as FFL it acts as the upper floor's build-up in that formula (H - b - beam - ceiling), with the marks read
  as slab levels it acts as the lower floor's finish: the same height either way, so the formula does not say where the
  structure is. Its scope stays WALL_HEIGHT_ALLOWANCE (ASSUMED — OWNER-APPROVED for plaster / paint heights only); it is
  refused as a structural datum (ALLOWANCE_AS_DATUM).
- **Q-45 / Q-41 (owner manual method for the layers):** regular floors 3-4 cm cement mix + adhesive (product text: layer
  up to 3 mm) + tile; bathrooms 4-6 cm with 1 % falls; roofs screed over the membrane (thickness not given). These are
  layer rules for mortar quantities (MORTAR_BED scope), partial (tile thickness not given), shown beside.

## 3. Reconciliation (ERS s.2 step 4), dry floors, in metres

drawn b 0.050 = Q-45 bed 0.030 .. 0.040 + adhesive 0 .. 0.003 + tile (not given, not printed) -> residual +0.007 ..
+0.020 m, which is exactly the tile slot (a 60 x 60 porcelain is in that range, but no tile thickness is printed or
answered, so the residual is NAMED, not closed). Q-43 0.10 vs drawn 0.05: -0.05 m, a different quantity (a height
allowance), not a disagreement on the same datum. Roofs: a constant layer contradicts any fall (1 % over the 2-4 m to
a rain-water pipe is 0.02 .. 0.04 m of variation alone), so the drawn 0.05 is a drafting convention there and stays
beside, refused (CONSTANT_LAYER_VS_FALLS). Wet / sunken zones: the sections cut none of them (T-213: A-A / B-B cut no
panel); the sunken drop exists because the wet build-up is thicker; nothing is carried.

## 4. The T-189 condition and the consequences (data for lane I; no BOQ line moved)

| Item | Before (R2) | After (R3 = R2 + the dry-floor layers; `summary.json`) |
|---|---|---|
| T-189 B20 / B23 stair-head ownership (needs b <= 0.289, beam top not more than 0.167 above the FFL) | NOT PROVEN | **PROVEN on the drawing basis** (b 0.049 / 0.050, DRAWING-CONFIRMED; the 0.04 alternative also inside); NOT PROVEN on the owner basis (Q-43 / Q-45 are not datums). The T-189 rev2 ledger (0.1147 m3 owned by the beams) stands without change |
| GF structural slab top / exterior ground-beam top ("Ground Floor slab level", p.13) | HELD | **+0.95** DRAWING-CONFIRMED |
| 1F / 2F slab tops, soffits, B20 / B23 bottoms | HELD | +5.45 / +5.29 / +4.70; +9.65 / +9.49 / +8.90 DRAWING-CONFIRMED |
| Necks (T-205: h = 2.33 - H - b + d) | b and d HELD | **h = 2.28 - H + d**: b settled; still HELD on d (formation, Q-21 C). Sensitivity at T-205's own rate: b = 0.05 removes 0.267 m3 from the 28 necks with a printed section (5.34 m2 x 0.05) against any b = 0 what-if. Released V2.9 10.855 m3 PROVISIONAL vs freelancer 8.805 m3 (-2.050, -18.9 %): still UNRESOLVED, now on d alone |
| Neck top used at the FFL +1.00 (route G profile) | FINISHED_AS_STRUCTURAL, gap unknown | FINISHED_AS_STRUCTURAL, gap +0.05 m |
| Column heights FFL -> FFL (GF 4.50, 1F 4.20) | equal only if b is equal on both floors (T-200: not proven) | b equal on GF / 1F / 2F (0.05 / 0.05 / 0.05): structural heights 4.50 / 4.20 unchanged within 1 mm; the 2F -> roof column top stays HELD with the roof build-up |
| Exterior ground-beam depth (D-35, "FOLLOW ARCH." from GF slab level to outer ground) | top HELD | top +0.95; depth 0.95 (to +-0.00) or 0.80 (to the court +0.15): the bottom stays HELD on which ground |
| Plaster / paint heights (owner Q-43 method) | 3.65 GF, 3.35 1F / 2F (with 0.15 ceiling) | unchanged (owner method governs); drawing-derived counterpart with b 0.05 would be 0.05 m higher per storey: RULE_DIFFERENCE shown beside, not applied |
| Sunken-panel ceilings (T-213, D-41) | HELD | HELD (drop unprinted) |

D-40 narrowed: the floor build-up of the DRY zones is drawn (0.05); the designer item keeps the wet zones, the sunken
drops (D-41) and the decor-ceiling levels. D-39 narrowed: the roof build-up is not given by the constant drawn layer;
the item keeps the roof slab tops and build-up at the drains / high points.

## 5. Verdict proposals

- Floor build-up dry zones: no engine line and no freelancer line (not compared); DRAWING-CONFIRMED 0.05 m (Checker to
  re-measure).
- T-189 B20 / B23: ENGINE_RIGHT on the drawing basis (the ownership ledger stands).
- Necks: UNRESOLVED (formation d only; designer item T-042 B4).
- Roof / terrace / wet / sunken build-up: UNRESOLVED (D-39 / D-40 / D-41); no owner question (ERS 2.7 not met: unprinted
  design values, not an owner decision).

## 6. Rule and lessons row (proposed)

Rule (any villa, provenance T-214): the FFL -> structural top build-up of a zone comes from (1) a printed structural top
or build-up, else (2) a drawn layer between the level line and the hatched structure of a cut section, read on vector
geometry with the level marker as datum and confirmed on the current issue, carried only to zones of the same type as
the cut zone; a constant drawn layer is never a roof / terrace build-up (falls); an owner value is used at its own
scope only (a finish allowance in a height formula is never a level datum); unresolved -> HELD, never 0.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | The floor build-up was carried as 'printed nowhere' by three runs (T-200, T-206, T-205), holding every slab top, neck top and the T-189 condition, while both architectural sections draw it on every floor (0.05 m unhatched layer under the FFL line) | The sections were read as 200 dpi rasters, where a 0.05 m layer at 1:100 is 0.5 mm beside a hatched band; drawn-but-unprinted layers were not searched on the vector plot | Before calling a layer 'not drawn', read the band on vector geometry (or >= 400 dpi, a layer >= 5 px) with the level marker as datum; a drawn layer is DRAWING-CONFIRMED only when vector and current issue agree, only for zones of its own type, never for a roof with falls; an owner allowance stays in its own scope (any villa) | tests/t214_floor_buildup (villa T214-K normal: printed, drawn + current issue, sunken with drop, roof with printed top; adverse: finished level as structural top, allowance as datum, dry layer to a wet zone, constant layer on a roof, vector only, vector vs scan, printed vs drawn, sunken without drop, mm / m) | proposed |

## 7. For the Checker (re-measure from the drawings, not from this file)

1. The architectural .dwf (Drive "Alsenan chalet project"), SECTION A-A and B-B: `python3 -I
   research/agents_t214/section_bands.py <private copy>`; then by hand at one band: the marker triangle's apex on the top
   line, the build-up line 0.05 below it, hatch strokes only between 0.05 and 0.20.
2. p7757_arch_sheet10.pdf (A-A, 1F band) and Alsenan_Architectural_P7757_Pages_11-12.pdf p.11 (B-B, annex +0.30 band):
   the thin unhatched strip on the upper side of the hatched band, about 8 px at 400 dpi.
3. sanitary-7757.pdf: SLOPE 1 % on the +9.70 terrace, +4.30 annex roof and +5.50 terrace strips (why the roof layer is
   refused); ST7757.pdf p.13 exterior ground-beam top "Ground Floor slab level".
4. The T-189 rev2 margins (research/agents_t189 s.2) against b 0.049 / 0.050.

## 8. Not done / uncertain

- Whether a GF wet room is cut by a section was not searched room by room (the zone stays HELD either way).
- The court +0.15 is also drawn as a 0.05 / 0.15 band; whether the court is a structural slab is not established here.
- Wiring (FLOOR_BUILD_UP 0.05 DRAWING-CONFIRMED on the dry chains, the neck top datum +0.95) is lane I work; the
  released default, V3.0.x candidates and every BOQ line are unchanged.
