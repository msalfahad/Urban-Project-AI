# Output format reference: the "جلال" QS samples (owner upload 2026-11-13; no client names here)

Two sample takeoff documents from a Kuwait QS office that works from a Revit model (BASE design): sample A "private villa,
4 floors, 17-09-2026" (15 pages) and sample B "project 014, 22-10-2026" (17 pages + materials summary + 3D views).
They are NOT Alsenan and are reference only; nothing in them is a measured quantity of our villa. What our system takes:

## 1. Document shape (adopt as the target shape of the Urban BOQ workbook)
1. Project inputs sheet: floors, storey heights slab to slab per floor (4.70 / 4.20 / 4.20 / 4.00 in A; 5.55 / 4.00 / 4.00 in B),
   basement yes/no, F.F.L., excavation depth, concrete grades per element (K300 footings / slabs / beams, K350 columns),
   cement content, wastage % (concrete 5, steel 10, blocks 5, tiles 10), cover (footings 5 cm, others 2.5 cm), soil
   bearing, unit rates (KD/m3 per grade, KD/t steel, KD per block, KD per cement bag).
2. Key quantities page: concrete m3 (and + wastage), rebar t (+ wastage), blockwork m2 and block count (+ wastage),
   ceramics m2 (floors + walls + skirting, + wastage), skirting lm, plaster m2 (internal + external + fence), corners lm,
   waterproofing m2, paint m2 (estimate), sanitary sets count.
3. One sheet per trade: structural summary by element and floor (m3, grade, steel kg main / links, t); blockwork per
   floor per type (external, fence, internal 15, internal 20: m2, lm, m3, block count); ceramics per room with a finish
   code (F1 lobby / living, F2 wet rooms with wall tiles, F3 service, F4 laundry, F5 external, F6 bedrooms): floor m2,
   wall tiles m2, skirting lm; stair marble (treads lm, risers lm, landings nr, nosings lm, "المساح" m2); sanitary sets
   per floor (WC, pantry, laundry, kitchen, wash basin, boiler); waterproofing per zone; plaster per floor: internal
   (both faces of internal walls + inner face of external), external outer face, parapet faces, parapet tops, fence;
   corners lm per floor: window edges (jambs + head + sill), door edges (jambs + head), external building corners x
   storey height, wall ends and column projections x storey height, parapet / wall-top edges (2 per metre).
4. Steel by diameter per element per floor (lengths from the model; weight = length x d^2 / 162; laps 60 d columns,
   40 d beams / slabs; 12 m bars with 1 m overlap), totals by diameter in t, + wastage, cost.
5. Every page: issue number and date, "needs confirmation" cells in red, notes on what was assumed.

## 2. Rules seen (owner decides which become Urban rules)
- Block count by volume: a 20 cm block = 0.40 x 0.20 x 0.20 = 0.016 m3, a 15 cm block 0.009 m3; count = wall m3 /
  block m3, i.e. 12.5 blocks per m2 for both (the same as the owner's Q-75 / Q-80 rule), + 5 % wastage shown apart.
- Wall tiles in wet rooms at 3.00 m height (sample A). Owner rule stays: tile to the decor-ceiling underside (Q-48 A).
- Paint = plaster faces - tile backing; ceilings = internal floor area (same as the freelancer); both "estimate".
- Plaster faces: both faces of internal walls + the inner face of external walls, excluding column faces and beam
  soffits; external = outer face net of openings; parapets 2 faces + tops; corners as lm (not as area).
- Wastage apart: concrete 5 %, steel 10 %, blocks 5 %, tiles 10 %.

## 3. Plausibility ratios (per m2 of internal floor finish area; per m3 of concrete for steel)
| Quantity | Sample A (4 floors) | Sample B (3 floors + roof room) | Freelancer Alsenan | Use |
|---|---|---|---|---|
| Internal floor finish m2 | 780.0 | - | 409.6 (dry + wet) | the base |
| Concrete m3 / floor m2 | 432 / 780 = 0.55 | 458 (no base given) | 352.4 / 409.6 = 0.86 | 0.5 .. 0.9 |
| Steel kg per m3 concrete | 54.9 t / 432 = 127 | 62.2 t / 458 = 136 (model, by diameter) | 44.19 t / 352.4 = 125 | 120 .. 140 kg/m3 for a Kuwait villa (3 sources) |
| Blockwork m2 / floor m2 | 2,171 / 780 = 2.8 | 1,859 net (materials page) | 1,261 / 409.6 = 3.1 | 2.5 .. 3.2 |
| Plaster m2 (int + ext + fence) / floor m2 | 4,311 / 780 = 5.5 | - | 2,712 / 409.6 = 6.6 | 5 .. 7 |
| Paint m2 / floor m2 | 2,636 / 780 = 3.4 | - | 1,643 / 409.6 = 4.0 | 3 .. 4 |
| Corners lm / floor m2 | 2,031 / 780 = 2.6 | - | 1,034 / 409.6 = 2.5 | about 2.5 |
| Waterproofing m2 / floor m2 | 466 / 780 = 0.6 | - | 357 / 409.6 = 0.9 | 0.6 .. 0.9 |
| Ceramics (floors + walls + ext) m2 / floor m2 | 1,704 / 780 = 2.2 | - | about 1,037 / 409.6 = 2.5 | 2 .. 2.5 |
| Skirting lm / floor m2 | 583 / 780 = 0.75 | - | 394 / 409.6 = 0.96 | 0.75 .. 1.0 |
A trade of ours outside its band is a flag to look at, never a quantity. The steel ratio is the owner's end-of-project
"approximate tons" basis: three independent Kuwait villa sources agree on 120-140 kg per m3 of structural concrete.
