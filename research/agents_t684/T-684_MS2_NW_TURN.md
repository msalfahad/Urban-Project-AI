# T-684 Stair ST-01, MS2 1F north-west corner square: winders or a flat half-landing (Checker F-V680-1)

Worker 1 (lane S), 2026-11-10. Research + an unwired rule module + tests; no engine, rule-version, knowledge or method
file is changed; candidate V3.0.66 and the released V2.9 + route G are untouched. ERS s.1-4 and s.7 applied. Drive
"Alsenan chalet project" read this run (read-only, private copies in `.work/private`, never committed):
P7757_DXF_COMPRESSED.zip (P7757.dxf), ST7757 dxf.dxf, p7757_arch_sheet10.pdf (section A-A, rendered at 600 dpi),
p7757_arch_sheet04.pdf (1F plan). Rules: owner stair rule S-9 (2026-10-24: winders never generated, only drawn
ones), Q-46 A (section counts govern), Q-51 A cond, Q-62 A cond, R-STAIR-CONT-1 (T-184), UP-QTY-STATUS-001.

## 1. Result in engineering terms

**The NW square of the 1F -> 2F stair is a FLAT landing**: the west part of the split-level half landing MS2-LD at
+7.516 (scaled), reached by the 12th riser of MS2-L, with ONE closing riser MS2-TR on the drawn line 0.10 m east of the
square's inner corner up to the east part at +7.684. **The three radiating lines on the 1F plan are the GF winders
(MS1-T) seen below through the open shaft**, not 1F -> 2F winders. The T-184 / T-173 / T-493 / T-680 model stands:
F-V680-1 is closed with **no quantity change** (released concrete 0.000 m3, every dependent line byte-identical).

| Line (V3.0.66) | Before | After | Change |
|---|---|---|---|
| STR.CONC.STAIR MS2-L L-67e4b048 | 1.033445 m3 RELEASED | 1.033445 m3 | none |
| STR.CONC.STAIR MS2-LD L-2416e65f (incl. the NW square) | 0.4696 m3 RELEASED | 0.4696 m3 | none |
| STR.CONC.STAIR MS2-TR L-659243ed | HELD blank | HELD blank (levels scaled, step soffit not drawn) | none |
| STR.CONC.STAIR MS2-U L-bb0e57b1 | 1.001373 m3 RELEASED | 1.001373 m3 | none |
| STR.FORMWORK.STAIR MS2-LD faces / side | 2.935 m2 RELEASED / HELD | same | none |
| B7 treads / step lm 1F flight 2 (MS2-L) | 3.795 m2 / 12.65 lm RELEASED | same (11 treads + landing; no winder tread) | none |
| 1F flight 5 tread / step lm / riser L-b4660de0 / L-e085c168 / L-820baecf | HELD blank (MS1-T SEEN_THROUGH, T-429) | same: the GF winders, counted once on the GF element, HELD S-9 / Q-51 | none |
| Skirting MS2-LD landing L-b442a00b | 3.70 lm RELEASED | same (flat +7.516 / +7.684) | none |
| Skirting MS2-LD.W25 / .W13 / MS2-TR.N sloped + zigzag | HELD / NOT_APPLICABLE / HELD | same | none |
| Railing RL-07 at MS2-LD L-1c899e8c | HELD | same | none |
| T-680 shaft 1F band plaster / paint L-0eac839f / L-2ab93d50 (research) | 45.317 .. 46.564 m2 each | same: N face contact u 0 .. 1.25 stays flat; the 0.1 .. 0.2 m2 per finish of F-V680-1 does not arise | none |
| **B7-05 nosing MS2-TR** (T-412 census: HELD 'position not drawn') | blank | **1.150 lm DRAWING-CONFIRMED, PROPOSED** for the B7-05 package (T-424) | +1.150 lm (proposal, unwired) |

Tread and riser counts by flight (1F -> 2F, 4.20 m printed): MS2-L 12 risers / 11 treads + landing; MS2-TR 1 riser;
MS2-U 12 risers / 11 treads + floor; 25 x 0.168 = 4.200 m. No winder on this storey.

## 2. Element definition (ERS s.1) and evidence, owner manual method and drawing-derived method side by side

Physical element: the north 1.25 x 1.20 m (1.15 x 1.15 clear inside the finishes) of the west lane of the 2.50 m shaft
on the 1F -> 2F storey, between MS2-L's last riser and the north wall, west of the closing-riser line.

1. **Riser budget (mathematical, decisive).** Storey height 4.20 m printed on A-A ('420'); risers 0.168 m measured on
   A-A (about 40 px at 237 px/m, 600 dpi; the Checker's T-111 re-measure 0.0 %); MS2-L 12 risers (plan 12 lines,
   A-A seen beyond), MS2-U 12 (A-A cut flight). (4.200 - 24 x 0.168) / 0.168 = **1.000 riser** for the whole turn:
   room for the closing riser only. Winders like the GF turn (4 wedges, 5 risers) would need 28 .. 29 risers =
   4.70 .. 4.87 m > 4.20 printed. On GF the same budget gives (4.50 - 22 x 0.16667) / 0.16667 = **5.000**, exactly
   the GF winder turn.
2. **Section A-A (drawn, decisive).** In the GF storey the north 1.20 m zone below the cut half landing MS1-LD draws
   **4 dashed + 1 solid riser** between +2.667 and +3.50 (0.833 m = 5 x 0.1667): the winders. In the 1F storey the
   same zone below the cut landing draws **no riser line**: only the west quarter's slab edge seen one riser below
   the cut east landing (the closing riser), and MS2-L's last steps arriving at it.
3. **2F plan (looks down on the MS2 north strip).** No radiating line in the NW square; only the 1.15 m closing-riser
   line 0.10 m east of the corner (layer '5', CONTINUOUS) and its 0.05 riser-face twin (layer '2', HIDDEN).
4. **Structural DXF.** ST p.5 (1F roof slab, carries MS2): no radiating line in the NW square (the probe finds only a
   45 deg pair in the NE half and the column outlines). ST p.4 (GF roof slab, carries MS1; the sheet that also draws
   the round stair): the three radiating lines at the same corner.
5. **The 1F lines are the GF lines.** Relative to the square's inner corner the 1F plan's lines end at (-0.511,
   1.150), (-1.150, 1.150), (-1.150, 0.512) m (lengths 1.259 / 1.626 / 1.259, angles 114 / 135 / 156 deg), with
   0.05 companions; the GF plan's MS1-T lines are identical line for line (within 1 mm). The GF plan draws them on the
   HIDDEN layer (its own turn above the GF cut); the 1F plan on the VISIBLE layer (below the 1F cut): the plan
   convention for an object seen below. The 1F plan draws no floor or landing in the NW square (its arrival landing
   1.95 x 2.50 is at the south end), so the square is open down to the GF turn.
6. Prior work agreeing (not used as proof): T-425 / T-429 bound the engine's 1F 'flight 5' (4-tread RADIAL, width
   1.247) to MS1-T with role SEEN_THROUGH; T-493 placed the closing riser at x 1.25 / 1.30 on 1F and 2F.

Owner manual method (STAIR_CONCRETE_V1 / Q-19 / Q-47 A) and drawing-derived method give the same element: a landing
plate L x W x T 16 and one closing riser; the winder alternative is refuted by facts 1-4, not chosen by size. The
freelancer has no separate line for this square ('2 landings' 6.20 m2, T-493 UNRESOLVED); not used.

Cross-trade owner (ELEMENT_REGISTER): structure (lane S) owns the element and STR.CONC.STAIR MS2-LD / MS2-TR; finishes
take it as STAIR_LANDING (B7-04, T-493 2.9325 m2) and never re-decide it.

## 3. Rules proposed (general, labelled; a rule change is a new rule version when adopted) — `t684_rules.py`

- **R-T684-1 (turn element):** radiating lines in a turn square are not by themselves winders of that storey. WINDERS
  only when the storey's riser budget leaves >= 2 risers for the turn AND the section draws that number AND the lines
  are the storey's own; LANDING (0) / LANDING_SPLIT (1) when the budget leaves no room and the section draws no more;
  lines coinciding line for line with the lower storey's turn through an open zone are SEEN_BELOW (counted once,
  below); anything else UNDETERMINED (HELD, never 0, never a default landing).
- **R-T684-2 (layers):** an annotation-layer line is never a winder; a hidden-layer line proves nothing alone (it is
  how a plan draws its own turn above the cut).
- **R-T684-3 (dependent lines):** concrete, tread / riser / nosing, skirting and shaft bands move as one package on the
  element decision; a finish line never re-decides the element.

## 4. Tests (`tests/t684_ms2_turn`, all pass; t184_stairs, t680_shaft_round2, m9_s6, stairs_s8_7* pass)

Synthetic villa V684 (3.60 m storeys, riser 0.18, hand-calculated budgets 4 / 1 / 0): lower winders DRAWN; upper lines
SEEN_BELOW on a split landing; genuine upper winders; annotation-layer lines ignored; hidden lines without a section
HELD; coinciding lines with a floor between = CONFLICT; coinciding lines while the budget asks 4 = HELD; a line 15 mm
off = not seen below; missing height / riser / count HELD (never 0); non-whole budget and section disagreement HELD;
mirror and three rotations; mm / cm / refused unit and role. Development villa pinned to `out/T684_MS2_TURN.json`.

## 5. Verdict proposals (for the Checker)

- MS2 NW square: **ENGINE_RIGHT** (the T-184 flat-landing model) on facts 1-4; F-V680-1 CLOSED, no quantity change.
- MS2-TR nosing: the census's "position not drawn" is **wrong on the drawing**; proposed 1.150 lm DRAWING-CONFIRMED
  (re-measure: 1F and 2F plans, x +0.10 from the NW inner corner, y 0 .. 1.15).
- Checker re-measure suggested: (a) A-A north zone, 1F storey: count riser lines (expected 0 beyond the closing step);
  (b) one dependent line: STR.CONC.STAIR MS2-LD 0.4696 m3 stays.

## 6. Missing / held

MS2-TR concrete and the two landing levels (+7.516 / +7.684 scaled, not printed; designer); the GF MS1-T winder
treads / soffit (S-9, Q-51, C-ST-3) unchanged. No owner question: nothing here meets ERS s.2.7.

## 7. Lessons-register row proposed (ERS s.7)

| 2026-11-10 | MS2 1F NW square: three radiating lines on the 1F plan read as possible 1F -> 2F winders (F-V680-1) | a plan shows what lies BELOW its cut: in an open dog-leg shaft the lower storey's winders appear on the upper plan, on the visible layer, line for line | a turn square is classified per storey from the riser budget + the section + coincidence with the lower turn (R-T684-1); lines alone never make winders (any villa) | tests/t684_ms2_turn (adverse: annotation layer, hidden without section, floor between, 15 mm off, budget asking winders while lines coincide) | rule proposed; no quantity change |
