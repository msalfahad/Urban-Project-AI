# T-370 Sanitary fixtures and floor drains as a count (B12-01), two sources reconciled

Worker 3, 2026-10-30. Lane A investigation, research files only (`research/agents_t370/`, `tests/t370_*`). No engine
file, rule version or candidate line changes. Statuses per WORKFLOW_CONTROLS s.5: every count below is
**DRAWING-CONFIRMED** (read from the drawings in this run, not yet independently verified); nothing is RELEASED.

## 1. Physical element and evidence (ERS s.2.1)

A fixture is a physical item fixed in a room: WC, basin, shower (tray or screened walk-in zone), bath tub, sink,
bidet, shattaf. A floor drain is a grated outlet in a floor; a roof rain-water outlet (RWD) is a different element
(roof drainage) and is kept as its own population. Each source is read on its own first, then matched:

| Source | Drive file | What it PRINTS |
|---|---|---|
| ARCH | 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, modelspace) | room-tag blocks (WC 'W.C' x7, bath 'BATH' x4 + text 2ED 'BATH', WASH 'Wash' x2, kit, PAN, laun) and **only 5 fixtures**: the WASH2 basin block (handles 33B, 2C0, 2C1, 1CF, 1EE, layer 1). WCs, showers and baths are NOT drawn (tag + floor-tile hatch only). |
| SAN | 'Alsenan chalet project' / sanitary-7757.pdf, p1 GROUND / p2 FIRST / p3 2nd FLOOR DRAINAGE PLAN 1:100 | vector only (no text layer), read at 600 dpi. Blue = fixtures the sanitary sheet adds; black = architectural underlay; legend: FD floor drain, RWD rain water drain, GCO, CO, R.E, RWP, SS, MH. |

Adverse evidence found and NOT counted: the three circles in GF W.C rooms (DXF A79, A81 r 192 mm; A84 r 94 mm, layer 5)
each carry a `mecvent` leader (A7A, A82, A85) whose x-arab text 'ji,dm wkhudm' is 'تهوية صناعية' (mechanical
ventilation): they are exhaust-fan marks, not floor drains. A yellow valve symbol on p1 in the W.C by the kitchen
(p1@360.0,600.0) is the symbol the 1F / 2F sheets draw as the shower valve inside a screened zone; here there is no
screen and no tray and the legend does not define it: **UNKNOWN**, not counted, never typed as shattaf or shower.

## 2. Register (room by room; refs: DXF handle, or `p<page>@x,y` in PDF points of the displayed page)

| Floor | Room (arch tag handle) | WC | Basin | Shower | FD | Status per item |
|---|---|---|---|---|---|---|
| GF | W.C 2DA (core, left) | 1 | 1 | - | 1 (4") | SAN_ONLY (arch: tag only) |
| GF | annex of W.C 2DA (untagged) | - | 1 | - | 1 (3") | basin AGREE (arch 33B = black underlay basin p1@615.6,331.2 with waste drawn); FD SAN_ONLY |
| GF | W.C 322 (upper of the two split by the diagonal wall) | 1 | 1 | - | 1 (4") | SAN_ONLY; the two basins sit back to back on the diagonal wall, both wasting to this FD |
| GF | W.C 323 (lower) | 1 | 1 | - | 1 (4") | SAN_ONLY |
| GF | BATH 2ED (by the master bedroom) | 1 | 1 | tray 1 | 1 (4") | SAN_ONLY |
| GF | Wash 2C5 (core lobby) | - | 2 | - | 1 (3") | basins AGREE (2C0, 2C1); FD SAN_ONLY |
| GF | Wash 1F0 (by the dewaneya) | - | 2 | - | 1 (3") | basins AGREE (1CF, 1EE); FD SAN_ONLY |
| GF | W.C 1F7 (west) | 1 | 1 | - | 1 (4") | SAN_ONLY |
| GF | W.C 1C8 (by the kitchen) | 1 | 1 | - | 1 (4") | SAN_ONLY; + 1 UNKNOWN valve symbol |
| GF | KITCHEN 276 | - | - | - | 1 (4") | SAN_ONLY; **no sink drawn on either sheet** |
| GF | PANTRY 178 | - | - | - | 1 (3") | SAN_ONLY; no sink drawn |
| 1F | LAUNDRY BDD | - | - | - | 1 (4") | SAN_ONLY; no washer / sink drawn |
| 1F | W.C C19 | 1 | 1 | - | 1 (4") | SAN_ONLY |
| 1F | BATH C01 (top) | 1 | 1 | tray 1 | 1 (4") | SAN_ONLY |
| 1F | BATH C11 (right) | 1 | 1 | tray 1 | 1 (4") | SAN_ONLY |
| 1F | BATH C2F (bottom left) | 1 | 1 | walk-in 1 | 1 (4") | SAN_ONLY; zone closed by a screen line + shower valve, FD outside the zone |
| 1F | BATH C2C (bottom right) | 1 | 1 | walk-in 1 | 2 (3" in the zone, 4" by the WC) | SAN_ONLY |
| 2F | W.C 12B6 | 1 | 1 | walk-in 1 | 1 (4") | SAN_ONLY; screened zone + valve |
| 1F | annex roof +4.30 / terrace roof +5.50 | | | | RWD 1 + 1 | roof outlets, separate population |
| 2F | roof +9.70 | | | | RWD 3 | roof outlets, separate population |

Machine-readable: `t370_alsenan.py` (every item with its ref and basis); run it to print the tables below.

## 3. Counts (pcs; each physical item once; CONFLICT / UNKNOWN never added)

| Kind | GF | 1F | 2F | Total | of which AGREE / ARCH_ONLY / SAN_ONLY |
|---|---|---|---|---|---|
| WC | 6 | 5 | 1 | **12** | 0 / 0 / 12 |
| Basin | 11 | 5 | 1 | **17** | 5 / 0 / 12 |
| Shower tray | 1 | 2 | 0 | **3** | 0 / 0 / 3 |
| Shower, screened walk-in (no tray drawn) | 0 | 2 | 1 | **3** | 0 / 0 / 3 |
| Bath tub, sink, bidet, shattaf | 0 | 0 | 0 | **0 printed** (not inferred; see s.5) | |
| Floor drain (FD) | 11 | 7 | 1 | **19** (3" x 5, 4" x 14) | 0 / 0 / 19 |
| Roof rain-water outlet (RWD) | 0 | 2 | 3 | **5** | separate population |
| CONFLICT | 0 | 0 | 0 | 0 | |
| UNKNOWN | 1 | 0 | 0 | 1 (valve symbol, GF W.C 1C8) | |

Why SAN_ONLY dominates: the architectural DXF draws basins only; every other fixture exists on the sanitary sheet
alone. That is not a conflict: each W.C / BATH room tag on the architectural plan has its WC on the sanitary sheet
(arch tags: GF 5 W.C + 1 BATH = 6 rooms, 6 WCs; 1F 1 + 4 = 5, 5 WCs; 2F 1, 1 WC).

## 4. Cross-check with the wet-room classes (acceptance c)

- Every W.C / BATH / Wash space (15, incl. the untagged annex) holds at least one fixture: wet room without fixture 0.
- Fixture in a dry room: 0.
- Drain-only spaces: GF KITCHEN 276 (classed wet under Q-30 = A; FD drawn, **no sink on either sheet**), GF PANTRY 178
  (candidate HELD zone, T-010) and 1F LAUNDRY BDD (FD only). A kitchen sink is a fixture the BOQ will need, but no
  drawing prints it: it stays UNKNOWN (missing, not 0).
- Against the earlier unverified kind list (T-010 `sanitary_reading.json`, worker 1, 110 / 250 dpi, kinds only):
  same WC (12) and FD (19) totals; this run finds **1 more basin** (the back-to-back basin on the lower face of the
  diagonal wall of the GF core W.C pair, p1@639.6,294.0) and **2 more showers** (the screened walk-in zones of 1F
  BATH C2F / C2C, p2@427.2,559.2 and p2@484.8,514.8). The wet / dry class of no space changes (each already WET).

## 5. Freelancer comparison and verdict proposals (acceptance d)

The only freelancer file with sanitary content is 'Alsenan Chalet_by_category.xlsx' (a cost record by category, not a
measured BOQ). Sanitary: 'sanitary materials' 1 item and the plumber's labour 1 item, both lump sums: **no fixture
count to compare** (not comparable; no verdict). Two counted items sit in the tiling labour:

| Freelancer row | Freelancer | Engine reading | Difference | Verdict proposal |
|---|---|---|---|---|
| floor gratings fixed ('تركيب صفايات') | 24 qty | FD 19 + RWD 5 = 24 pcs | 0 (0.0 %) on the combined count; FD alone 19 vs 24 = -5 (-20.8 %) | RULE_DIFFERENCE: the freelancer counts every grating the tiler sets, floor drains and roof outlets together; B12-01 floor drains = 19 pcs, the 5 roof outlets belong to the roof-drainage line (B13 family), not to the wet-room drains. Both numbers are drawing-printed. |
| shower ('شاور') | 11 qty | 6 shower positions (3 tray + 3 walk-in) | -5 (-45 %) | UNRESOLVED: a tiling labour item of undefined unit; 11 matches no physical population read here (it equals the WC-room count of GF + 1F, 6 + 5, which is a coincidence until shown otherwise). No quantity is changed on it. |

## 6. What is missing / HELD

- Kitchen and pantry sinks, a laundry washer point: printed on no sheet -> UNKNOWN (never 0, never inferred).
- The GF valve symbol: UNKNOWN until the designer states it (a shattaf / hand-shower point is typical in Kuwait but
  practice is not evidence).
- Fixture specification, brand, mounting, WC type (floor / wall-hung): printed nowhere; not inferred.
- Engine binding: none. B12-01 stays EXPERIMENTAL in the family master; a fixture-count line needs a lane I package
  that wires this register's method (and a reader that types fixtures on a sanitary sheet automatically: this run was
  a visual reading).

## 7. General rule proposed and lessons-register row (ERS s.7)

Rule proposal (research scope, not a rule version): *a fixture is counted once per physical item; each source is
read for what it prints (symbol, legend tag, label); a type with no printed basis is UNKNOWN; a drain needs a printed
drain symbol (a fall is not a drain); roof outlets and floor drains are separate populations; a source that does not
draw a fixture is silent, not in conflict.* Tests: `tests/t370_sanitary_fixture_count/` (normal villa by hand,
adverse: double count, guessed type, drain from a fall, cross-room link, unknown / conflict never counted).

Lessons row proposal: "A circle with a leader in a W.C is not a floor drain: on P7757 the three such circles are
mechanical-ventilation marks (x-arab 'ji,dm wkhudm'). Read the leader before typing a symbol. Also: the freelancer's
grating count (24) = floor drains (19) + roof outlets (5): compare populations, not totals."
