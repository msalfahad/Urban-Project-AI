# T-380 B12-02 drainage / water-supply source census, and the freelancer's shower residual

Worker 2, 2026-10-30. Lane A, research files only (`research/agents_t380/`, `tests/t380_drainage_census/`). No engine
file, rule version, candidate line or family-master file changes. Statuses per WORKFLOW_CONTROLS s.5: every count below
is **DRAWING-CONFIRMED** (read in this run, not yet independently verified); nothing is RELEASED; no length is given.

## 1. Physical element first (ERS s.2.1)

B12-02 "Pipes / drainage / water supply" (unit lm) is three physical systems, each with discrete items and runs:

| System | Discrete items (pcs) | Runs (m.l) |
|---|---|---|
| Foul drainage | inspection chambers / manholes, clean-outs, rodding eyes, valves, soil stacks, floor traps (B12-01) | GF main to the outfall, soil branches (WC, FD, stack foot), waste branches (basin / tray to FD), suspended runs, stack verticals |
| Rain water | roof outlets RWD (B12-01 / roof drainage), rain-water pipes | RWP verticals, any below-ground storm run |
| Water supply | tanks, pumps, heaters, supply points | cold / hot supply pipework |

A length exists only where the drawings STATE it (a dimension, or printed levels at both ends). A single-line route is a
SCHEMATIC, not a measured length, and the Alsenan drainage sheets add the title-block note **"THE BUILDER TO WORK WITH
STATED DIMENSIONS NOT TO SCALE DRAWING"** (p1, p2, p3; the same note the Q-48 door census relied on): no pipe length may
be scaled from them, whatever the printed 1/100.

## 2. Sources read

| Source | Drive file | What it prints for B12-02 |
|---|---|---|
| SAN | 'Alsenan chalet project' / sanitary-7757.pdf, p1 GROUND / p2 FIRST / p3 2nd FLOOR DRAINAGE PLAN | drainage only: routes, sizes, slopes, MH, GCO, CO, SS, RWP, FD, RWD; legend (p1-p3) also lists R.E, NRV, AD, B.T.T.S., H/L, SUMP PUMP. Positions below are drawn-circle centres from the vector paths (`p<page>@x,y`, PDF points, rotation applied; the three pages share one frame) |
| ARCH | 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf ab54dd55) | nothing: layer TOI is empty; no pipe, tank, pump, heater, drain or sewer text or block in modelspace or in the 442 block definitions (only 'mecvent', T-370) |

Water tank, from merged evidence (cited, not re-derived; WORKFLOW_CONTROLS s.10.5): T-221 s.5 searched the structural and
architectural sheets sheet by sheet: the structural plan ST p.6 prints a 'WATER TANK PLACE' slab panel (T18); the
architect's elevations and sections A-A / B-B draw no tank; the sanitary sheets have no roof-plan tank. So a tank PLACE is
printed, a tank (count, capacity, type) is not.

## 3. Census (acceptance a)

### 3.1 Discrete items

| Item | pcs | Status | Evidence (sheet / position / printed text) |
|---|---|---|---|
| Inspection chamber MH | **1** | COUNTABLE | p1@141.6,243.6 'MH 100X100X100 DEEP INSPECTION CHAMBER WITH HATCH BOX AND VENT PIPE' (NW court, outfall arrow to the street). The unit of '100' is not printed (notation read, not assumed: size HELD as printed text); hatch box and vent pipe are parts of this item |
| Ground clean-out GCO | **2** | COUNTABLE | p1@317.5,455.4 (head of the south branch), p1@825.4,244.6 (east head of the court main) |
| Clean-out CO ø4" | **1** | COUNTABLE | p1@415.7,578.1 'CO ø4"' by the pantry |
| Soil stack ø4" | **4** | COUNTABLE | SS-A p3/p2/p1@591.3,263.8 (2F T/B -> 1F F/A-T/B -> GF F/A); SS-B p2/p1@644.7,263.9 (1F T/B; **GF drop drawn with no tag**); SS-C @812.5,263.9 (1F T/B at the end of the B.T.T.S. run -> GF F/A); SS-D @455.7,572.7 (1F T/B -> GF 'F/A H/L', to CO-1) |
| Rain-water pipe ø4" | **5** | COUNTABLE | one per RWD: NE @867.9,263.9 (2F T/B -> 1F F/A-T/B -> GF free discharge), SE2 @897.5,564.6 and SW2 @409.7,572.8 (2F T/B -> free discharge on the 1F +5.50 roof), TER @937.4,597.5 (**1F drop drawn with no tag** -> GF F/A free discharge), ANX @120.5,606.1 (annex +4.30 T/B -> GF F/A free discharge) |
| Floor drains / roof outlets | 19 / 5 | COUNTABLE (B12-01) | not recounted: merged T-370 register (Checker-verified), the connection ends of the branches below |
| Rodding eye, NRV, area drain, sump pump | HELD | NOT_PRINTED (legend only) | legend p1-p3; symbol on no plan |
| Water tank, water heater / booster, supply points | HELD | NOT_PRINTED | searched p1-p3 and P7757.dxf: absent; for the tank, merged T-221 s.5: ST p.6 prints a 'WATER TANK PLACE' panel only |

The stack chain is position-matched (identical frame on the three pages, tolerance 12 pt): 9 chains = 4 soil stacks + 5
RWPs, exactly the counted items. Two links are printed on one side only (finding, not a conflict): SS-B (T/B on 1F, the GF
circle untagged) and RWP-TER (F/A on GF, the 1F circle untagged).

### 3.2 Runs

| Run | Size printed | Slope printed | Status | Why no length |
|---|---|---|---|---|
| GF main to MH-1, branches to GCO-1 / GCO-2 | Pø6" (3 labels) | 1 % | SCHEMATIC_ONLY | no dimension, no invert level; sheet not to scale |
| GF soil branches (main -> each WC, FD, stack foot) | not printed | - | SCHEMATIC_ONLY | as above; branch diameter also not printed |
| Waste branches (basin / tray / walk-in -> FD), all floors | not printed | - | SCHEMATIC_ONLY | as above |
| 1F suspended run SE bath -> SS-C | Pø4" | 1 % | SCHEMATIC_ONLY | 'B.T.T.S.' (below the slab), not dimensioned |
| 1F / 2F soil branches WC / FD -> stack | not printed | - | SCHEMATIC_ONLY | as above |
| Stack verticals SS-A..D | ø4" | - | SCHEMATIC_ONLY | storey levels printed (GF +0.15 / +0.30 / +1.00, 1F +5.50, 2F +9.70) but not the stack ends (foot under the GF slab, H/L at SS-D, top / vent) |
| RWP verticals | ø4" | - | SCHEMATIC_ONLY | bottom printed ('15CM ABOVE FFL'); top = an outlet on a roof laid to 'SLOPE 1%' whose level is not printed |
| Water supply | - | - | NOT_PRINTED | no supply layout in the set read |

Level indicators, never quantities: RWP-SE2 / RWP-SW2 nominal 9.70 - (5.50 + 0.15) = 4.05 m before the unstated fall at
the outlet; RWP-NE / TER / ANX have no printed discharge-surface level at the pipe (court +0.15 and ground +-0.00 both
printed nearby). The census therefore gives B12-02 **no measurable length on Alsenan: 0 of 8 run groups MEASURABLE**;
every length is HELD (missing, never 0).

## 4. B12-02 family status proposal (acceptance b; proposal only, for the next BOQ_FAMILY_MASTER version)

- capability: stays **BLOCKED_BY_SOURCE** for the lm lines. Evidence to replace 'needs MEP plans': "sanitary-7757.pdf
  read (T-380): drainage routes drawn as schematics with sizes (6in main, 4in stacks / RWP / suspended run) and slopes
  (1 %), no dimension or invert level, sheet note 'work with stated dimensions, not to scale'; water supply not printed;
  needs a dimensioned drainage layout with invert levels and a water-supply layout".
- missing: "lengths: no stated dimension; water supply: no drawing".
- New count scope for the Lead to place (not in B12-02's lm unit): drainage accessories as pcs, DRAWING-CONFIRMED in
  research (MH 1, GCO 2, CO 1, SS 4, RWP 5; NOT_PRINTED: R.E, NRV, AD, sump pump, tank, heater). Capability for that scope:
  NOT_IMPLEMENTED (no method emits it) -> a lane I row if the Lead wants count lines.
- Designer RFI candidates (for T-381 / the Lead; not sent): (1) dimensioned drainage layout or invert levels at MH-1,
  GCO-1, GCO-2 and the stack feet; (2) unit of 'MH 100X100X100'; (3) branch diameters for WC / basin / tray connections;
  (4) water-supply layout, tank(s), heater; (5) is the GF untagged circle at SS-B the foot of the 1F 'SSø4"T/B' (T/B
  printed above), and the 1F terrace RWD pipe the top of the GF 'RWPø4F/A' (F/A printed below)?

## 5. Freelancer comparison and the shower residual (acceptance c)

The freelancer gives **no pipe length** on either workbook: B12-02 m.l is NOT COMPARABLE (his sanitary is a lump sum).
'Alsenan Chalet_by_category.xlsx', category sanitary, in workbook order:

| Freelancer row | Freelancer | Drawing reading | Verdict proposal |
|---|---|---|---|
| sanitary materials | 1 item (lump sum) | - | NOT COMPARABLE |
| 'system' item | 1 item | no heater / booster printed | NOT IN THE DRAWING (UNRESOLVED scope) |
| water tanks | 2 qty | one 'WATER TANK PLACE' panel printed (ST p.6, T-221 s.5); no tank count, capacity or type on any sheet | UNRESOLVED: NOT IN THE DRAWING as a count; HELD |
| pit pump | 1 qty | sump pump = legend only | NOT IN THE DRAWING |
| pit covers | 2 qty | 1 inspection chamber MH-1; no pit (soak-away / septic) printed | UNRESOLVED: +1 cover not explained by the drawings; MH-1 = 1 pcs DRAWING-CONFIRMED |
| plumber labour | 1 item (lump sum) | - | NOT COMPARABLE |

**Shower 11 vs 6.** The 11 is the tiling-labour row 'شاور' (11 qty x 15 KD), unit undefined. Each population the
drawings or his own workbooks print, tested in units:

| Population | pcs | = 11? |
|---|---|---|
| drawn shower positions (3 tray + 3 screened walk-in; T-369 / T-370) | 6 | no (-5) |
| + the UNKNOWN valve in GF W.C 1C8 | 7 | no (-4) |
| WC rooms on the drawings (GF 6 / 1F 5 / 2F 1) | 12 | no (+1) |
| bath rows in his own wet-room table ('الارضيات+العازل+الديكور+الرخام (1).xlsx', waterproofing sheet: GF 4 + 2, 1F 5, 2F 1; plus 3 wash, 1 kitchen, 1 laundry rows) | 12 | no (+1) |
| 4in floor drains / all floor drains (T-370) | 14 / 19 | no |
| GF + 1F WC rooms | 11 | yes, the only match: excludes the 2F W.C 12B6, which HAS a screened shower: physically inconsistent with "a shower per bathroom" |

Verdict proposal: **UNRESOLVED**. No drawn population equals 11 by a physical cause; the nearest physical reading
("a shower floor per bathroom") gives 12, and the one arithmetic match drops a room that the drawings show with a shower.
What is missing: the freelancer's definition of the 'شاور' labour item (per shower floor zone, per mixer point, per
bathroom) and his room list for it; his wet-room table carries no shower row. No quantity depends on it: B12-01 showers =
6 DRAWING-CONFIRMED (T-370 / T-369 MERGED), B8-04 shower floor extra 0.000 m2 (Q-40 A). Not an owner question (ERS s.2.7:
a freelancer count is reconciled, never adopted; nothing is blocked).

## 6. Open / HELD

- Every B12-02 length (8 run groups): HELD until a dimensioned layout / invert levels exist; water supply HELD.
- MH-1 size unit; branch diameters; SS-B / RWP-TER one-sided links (designer confirmation only if a line needs it).
- Water tanks: number / capacity / type printed nowhere (a tank place is: ST p.6); RFI candidate (4) covers it.
- Pool drainage / backwash: printed nowhere on the sanitary sheets (the pool is a freelancer lump sum).

## 7. Rule and lessons-register row (ERS s.4, s.7)

Rule proposal R-T380-1 (research scope, any villa): *a drainage item is COUNTABLE only on a printed symbol / tag /
label; a run is MEASURABLE only on a printed dimension or printed levels at both ends; a drawn route is SCHEMATIC_ONLY
and is never scaled (never at all under a 'not to scale' note); a legend entry drawn nowhere and an absent system are
NOT_PRINTED and HELD, never 0; a stack passing several floors is one item, matched by position and its F/A / T/B tags,
a one-sided link kept as a named finding.* Tests: `tests/t380_drainage_census/` (villa V by hand: 12.40 m dimensioned,
5.95 m between printed levels; adverse: schematic measured, scaled / practice / freelancer basis, NOT_PRINTED as 0,
legend counted, mm levels, inverted levels, duplicate, dangling T/B / F/A, T/B into an untagged non-drop, offset beyond
tolerance, mirror).

Lessons row proposal: "A drainage sheet at a printed scale is not a measured pipe length: Alsenan's sanitary sheets print
sizes and slopes but no dimension and say 'not to scale'; B12-02 stays BLOCKED_BY_SOURCE for lengths while its accessories
(MH, GCO, CO, stacks, RWPs) are countable. Count a stack once across floors by position + F/A / T/B."
