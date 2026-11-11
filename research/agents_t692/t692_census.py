"""T-692 MISSING BOQ FAMILIES CENSUS (research only; no quantity produced or wired).

Selection (from the board row): every family of the coverage master whose capability is NOT_IMPLEMENTED or whose
candidate state is NOT_IN_CANDIDATE (the PRIMARY set: the candidate emits no line of it). The owner's '38 missing
families' (owner order 2026-11-09 18:30) is reconciled by id: PRIMARY (NOT_IN_CANDIDATE, which contains every
NOT_IMPLEMENTED family) + the IN_CANDIDATE_BASE_LINES band (lines exist but only as the base run gives them, no verified
piece integrated) = every family that is neither INTEGRATED_IN_CANDIDATE_AND_TESTED nor HELD_IN_CANDIDATE.

Every selected family needs exactly one CLASS (MEASURABLE FROM DRAWINGS / NEEDS OWNER RULE / DESIGNER ITEM / OUT OF
SCOPE) with its evidence; build() fails when a selected family has no class, a class names a family that is not
selected, an id is doubled, or a class value is not one of the four. The class is about THIS villa unless the row says
'every villa'; the method scope is always every villa.

Order (owner order 2026-11-09 18:30): concrete -> rebar -> masonry -> plaster / paint -> tiles -> waterproofing ->
earthworks -> missing families, MEP last. Inside the missing families: band (BUILDING, then EARTHWORKS_SITE kept
separate, then MEP last), then class (measurable first), then the owner trade step, then the established scale (an
order-of-magnitude bucket of a quantity already measured in a merged piece, never a rate or a price).
"""
from __future__ import annotations

import json
from pathlib import Path

CLASSES = ("MEASURABLE FROM DRAWINGS", "NEEDS OWNER RULE", "DESIGNER ITEM", "OUT OF SCOPE")
BANDS = ("BUILDING", "EARTHWORKS_SITE", "MEP")
SELECT_PRIMARY = "NOT_IN_CANDIDATE"
SELECT_BAND = "IN_CANDIDATE_BASE_LINES"

# owner trade step (owner order 2026-11-09 18:30): 1 concrete, 2 rebar, 3 masonry, 4 plaster / paint (incl. ceilings
# and wall profiles), 5 tiles / floors / stairs / openings, 6 waterproofing, 7 earthworks / site, 8 other, 9 MEP
STEP = {"concrete": 1, "rebar": 2, "masonry": 3, "plaster_paint": 4, "tiles": 5, "waterproofing": 6,
        "earthworks": 7, "other": 8, "mep": 9, "register": 10}
# established scale bucket from merged pieces: 3 = hundreds of units or more, 2 = tens, 1 = a few, 0 = none / unknown
CLASS_ORDER = {c: i for i, c in enumerate(CLASSES)}
BAND_ORDER = {b: i for i, b in enumerate(BANDS)}

ST = "Drive 'Alsenan chalet project' / ST7757.pdf + 'ST7757 dxf.dxf'"
AR = "Drive 'Alsenan chalet project' / architectural PDF (p7757_arch_sheet03 / 04 / 09 / 10, Pages_01-02 .. 11-12) + P7757_DXF_COMPRESSED.zip"
SAN = "Drive 'Alsenan chalet project' / sanitary-7757.pdf p.1-3"
NONE_SET = "none of the 31 sheets of the Drive set (ST p.1-16, ARCH p.1-12, SAN p.1-3; research/agents_t357/SHEET_SEARCH_T357.csv)"

# family -> classification. 'dxf' names the keyword group of t692_dxf_census.KEYWORDS read for that family.
FAMILY_CLASS: dict[str, dict] = {
    "B1-01": dict(cls="OUT OF SCOPE", band="EARTHWORKS_SITE", step="earthworks", scale=0, dxf="clearance",
                  source=f"{NONE_SET}: no site plan, no clearance note",
                  evidence="T-357 MERGED 90135e91 sheet search; T-471 C-B1-01 NOT_APPLICABLE (Lead ruling 2026-10-30 R-CLR-1)",
                  rule="every villa: m2 only from a printed site plan / scope; a contract provisional item is commercial",
                  host="engine/source/struct_n10.py (route excavation); no site module yet"),
    "B1-05": dict(cls="OUT OF SCOPE", band="EARTHWORKS_SITE", step="earthworks", scale=0, dxf="termite",
                  source=f"{ST} p.8 notes 1-24, p.9 notes 1-4: none requires soil treatment",
                  evidence="T-354 MERGED e157c2d1 (R-ST-1..4); T-471 C-B1-05 NOT_APPLICABLE",
                  rule="every villa: m2 per specification wording only",
                  host="engine/source/struct_n10.py (route excavation)"),
    "B1-06": dict(cls="DESIGNER ITEM", band="EARTHWORKS_SITE", step="earthworks", scale=0, dxf="dewater",
                  source=f"{ST} p.8 recommendations 14 (groundwater dewatering) and 15 (excavation support), p.9 note 4 (groundwater depth): required in words, no extent or design printed",
                  evidence="T-357 SHEET_SEARCH (ST p.8 / p.9 read in full); T-471 C-B1-06 APPLICABLE_UNMEASURED",
                  rule="temporary works are the contractor's / geotechnical design: item HELD by name, never 0",
                  host="engine/source/struct_n10.py (route excavation)"),
    "B1-07": dict(cls="NEEDS OWNER RULE", band="EARTHWORKS_SITE", step="earthworks", scale=0, dxf=None,
                  source=f"{NONE_SET}: preliminaries are contract items, no drawing prints them",
                  evidence="T-471 C-B1-07 POSSIBLY_APPLICABLE ('needs the contract documents')",
                  rule="GAP: whether an Urban BOQ carries a preliminaries section and how (itemised / lump sum); no Urban rule in OWNER_QUESTIONS_ANSWERED",
                  host="tools/urban_boq_m9.py (BOQ sections); no module"),
    "B2-01": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="register", scale=0, dxf="rooms",
                  source=f"{AR}: GF / 1F / 2F plans (sheet03, sheet04, Pages_05-06 p.5)",
                  evidence="engine/source/arch_rooms.py:984 spaces(); ARCH_ROOMS.json per run; T-099 census 0 rooms lost, 3 unlabelled HELD",
                  rule="register, not a priced line (UP-QTY-STATUS-001); what is missing: the census guard is not wired",
                  host="engine/source/arch_rooms.py"),
    "B2-03": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="register", scale=0, dxf=None,
                  source=f"{AR}: area plans Pages_01-02 (p.1 GF + 1F, p.2 2F + total) print the floor areas: an independent check of the plates",
                  evidence="engine/source/arch_floor.py:108 reconcile() (GF 284.1465 / 1F 209.8017 / 2F 55.08 m2, three checks BALANCED)",
                  rule="register, not a priced line; missing: the plate vs printed-area check",
                  host="engine/source/arch_floor.py"),
    "B2-04": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="register", scale=0, dxf="kitchen",
                  source=f"{AR}: GF plan (sheet03) prints the pantry size",
                  evidence="engine/source/arch_v213.py:223 typed_zones() (4.50 x 3.00 = 13.50 m2, T-120 verifier run 44)",
                  rule="UP-PANTRY-001..004, Q-37 A, Q-17 A; zone feeds B3 / B4 lines, no own priced line",
                  host="engine/source/arch_v213.py"),
    "B2-05": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="register", scale=0, dxf=None,
                  source=f"{AR}: printed VOID on the plans, sections A-A (sheet10) and B-B (Pages_11-12)",
                  evidence="T-573 MERGED 587e47f9: light well -14.943 m2, 1F double height +12.090 m2 in the ceiling reconciliation",
                  rule="register (drives B5 / B4 heights); missing: double heights as a line",
                  host="engine/source/arch_floor.py:65 split_face()"),
    "B3-03": dict(cls="DESIGNER ITEM", band="BUILDING", step="tiles", scale=1, dxf="marble",
                  source=f"{AR}: no finish schedule or floor-material legend; entrance / stair-hall floor material unprinted",
                  evidence="T-471 C-B3-03 POSSIBLY_APPLICABLE (owner gate 'entrance and stair-hall finishes', RFI-B-A12); T-692 DXF census: 0 marble texts",
                  rule="URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 covers dry floors; a marble floor needs the finish schedule; landing marble is B7-04 (Q-66 B, Q-70 A)",
                  host="engine/source/marble_thresholds.py (research, read by no method)"),
    "B3-07": dict(cls="NEEDS OWNER RULE", band="BUILDING", step="tiles", scale=2, dxf="profile",
                  source=f"{AR}: doorway material changes are on the plans (24 ARCH.THRESHOLD strip lines in V3.0.67); no profile detail printed",
                  evidence="engine/source/trade_strips.py (research); registry Q-S6-1 open; T-471 'skirting system not specified' (T-460)",
                  rule="GAP: whether every floor-material change takes a profile and which (OD-V3-4 makes profiles separate items only 'wherever source geometry supports'); lm = doorway width per transition once ruled",
                  host="engine/source/trade_strips.py"),
    "B4-02": dict(cls="OUT OF SCOPE", band="BUILDING", step="tiles", scale=0, dxf="kitchen",
                  source=f"{AR}: kitchen / pantry counter outlines (P7757.dxf layer 5, 20 handles re-read)",
                  evidence="T-351 MERGED f0bd9f3c: 24 faces, 0 new B4-02 faces, overlap 0.0000 m2: every face already on a B4-01 FIN.WALL.TILE line (laundry 52.5290, pantry 32.3422 m2; kitchen HELD Q-54 B)",
                  rule="covered by B4-01 on this villa (no double count); every villa: a printed splash band or a kitchen open to a dry plan is a real B4-02 line (R-T351-1 / -3)",
                  host="engine/source/arch_v3034.py:243 zone_check"),
    "B4-04": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="plaster_paint", scale=3, dxf="facade",
                  source=f"{AR}: elevations Pages_05-06 p.6, Pages_07-08 p.7 / p.8, sheet09 + plans",
                  evidence="T-305 face ledger MERGED 9d71ef09; T-317 exterior faces GF 96.30 + 1F 134.45 m2 (+ held); candidate carries base lines only (ARCH.FACADE 4, FIN.EXT.FINISH 3)",
                  rule="UP-FACADE-001; Q-79 external render 1:4; wiring is QUEUED as T-314 r3",
                  host="tools/urban_boq_m9.py:1274 _v29_facade(); engine/source/facade_passage_walls.py"),
    "B4-05": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="plaster_paint", scale=3, dxf="spatter",
                  source=f"{AR}: every finished wall face (plans + heights); no sheet prints spatter (T-317 text census 0 of 675 + 2,339 texts; T-692 DXF census 0)",
                  evidence="T-317 MERGED 328a7095: determinate 913.7202 m2 + held 1,016.75 .. 1,112.66 m2 on 60 hosts (18 carried by another host, 10 held blank)",
                  rule="owner OD-V3B-4..7 + OD-V3-4 (separate item); wet-area walls spatter + levelling render (owner 2026-11-02); Q-79 spatter 1:2; wiring QUEUED as T-364",
                  host="engine/source/owner_finish_scope.py; research/agents_t317/t317_spatter_mesh.py"),
    "B4-09": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="plaster_paint", scale=2, dxf="bead",
                  source=f"{AR}: external arrises of plastered faces from the plans (wall ends, piers, column corners) x the plaster height; opening edges from the opening census",
                  evidence="engine/source/corner_bead.py (research, read by no method); no merged ledger yet",
                  rule="URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1 (OD-V3-4): corner beads lm a separate item wherever geometry supports; to investigate before any question: whether opening reveal edges count (not named in OD-V3-4)",
                  host="engine/source/corner_bead.py; engine/source/wall_height.py (plaster height, Q-72)"),
    "B4-10": dict(cls="NEEDS OWNER RULE", band="BUILDING", step="tiles", scale=2, dxf="edge",
                  source=f"{AR}: exposed tile edges at wet-room openings and band tops follow from the B4-01 tile lines; no edge detail printed",
                  evidence="engine/finishes_rules.py edge_finish (idle); T-471 C-B4-10 APPLICABLE_UNMEASURED",
                  rule="GAP: Urban default edge treatment (45-degree mitre vs steel / PVC profile) and which edges; geometry follows once ruled",
                  host="engine/finishes_rules.py"),
    "B4-11": dict(cls="OUT OF SCOPE", band="BUILDING", step="plaster_paint", scale=0, dxf="cladding",
                  source=f"{AR}: no material legend; elevations show plaster + Sigma faces",
                  evidence="T-360 MERGED (R-T360-1..5): 0 of 675 DXF texts name a cladding; T-692 DXF census 0; porch arch surround HELD by name (RFI-B-A12 / A13)",
                  rule="every villa: m2 from an elevation legend / specification only",
                  host="engine/source/owner_finish_scope.py"),
    "B5-02": dict(cls="DESIGNER ITEM", band="BUILDING", step="plaster_paint", scale=3, dxf="ceiling",
                  source=f"{AR}: no reflected ceiling plan, no ceiling-finish note (sections give levels only)",
                  evidence="T-573 MERGED 587e47f9: board ceiling 366.891 m2 on B5-01 lines (HELD -36.520); the area is published on B5-01 FIN.CEILING (41 lines)",
                  rule="URBAN ceiling method: no ceiling is assumed gypsum unless a source / project fact authorises it (MATERIAL = BY_SPEC); Q-57 A modified: gypsum, moisture-resistant board where specified, bulkheads and coves measured apart; board type is the designer's",
                  host="engine/source/arch_measure.py (FIN.CEILING); research/agents_t573"),
    "B5-03": dict(cls="DESIGNER ITEM", band="BUILDING", step="plaster_paint", scale=3, dxf="cornice",
                  source=f"{AR}: no cove / cornice detail on any sheet",
                  evidence="T-573: cove HELD (T-283 ledger 288.640 m HELD, 6 faces blank); T-692 DXF census 0",
                  rule="Q-57 A modified: cove needs geometry or an approved detail; OD-V3-4 separate item",
                  host="engine/source/arch_measure.py; research/agents_t573"),
    "B5-05": dict(cls="DESIGNER ITEM", band="BUILDING", step="plaster_paint", scale=1, dxf="access",
                  source=f"{NONE_SET}: no RCP or MEP layout locates an access panel",
                  evidence="T-471 C-B5-05 POSSIBLY_APPLICABLE ('MEP-driven; no source')",
                  rule="every villa: pcs from the RCP / MEP coordination drawing",
                  host="engine/source/arch_measure.py"),
    "B6-08": dict(cls="DESIGNER ITEM", band="BUILDING", step="tiles", scale=1, dxf="lift",
                  source=f"{AR}: 3 lift landings (GF / 1F / 2F) drawn; landing door size and head height printed nowhere",
                  evidence="research/agents_t619/manifest_v14.py:118 DOOR.LIFT_LANDING 3 HELD blank lines (non-candidate overlay); ELEMENT_REGISTER 'LIFT LANDING HEAD'",
                  rule="count 3 pcs is drawn; supply HELD on the lift supplier schedule (FR-T608-2); the wall opening deduction stays on the wall lines",
                  host="engine/source/door_model.py (route doors)"),
    "B7-01": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="tiles", scale=2, dxf=None,
                  source=f"{AR} plans + {ST} p.16 stair details",
                  evidence="candidate: 14 FIN.STAIR.FLIGHT lines HELD UNKNOWN (base run); T-135 MERGED 05e2eab STAIR_FLIGHT_ONCE_V1 read by no method (flight on two plans counted once)",
                  rule="OWNER_RULE_STAIRS 2026-10-21 / 2026-10-24; Q-50 A (reconstructed stair)",
                  host="engine/source/stair_flight_once_v1.py:180 flights_once(); engine/source/stair_measure.py"),
    "B7-05": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="tiles", scale=2, dxf="nosing",
                  source=f"{AR} plans (tread edges) + {ST} p.16",
                  evidence="T-412 census MERGED: 69 DRAWING-CONFIRMED nosing edges 87.350 lm (incl. 7.400 landing / floor edges), 20 HELD blank by name; T-690 MS2-TR 1.150 lm AGREE",
                  rule="OWNER_RULE_STAIRS_2026-10-24 (nosing in the stair BOQ); wiring QUEUED as T-424",
                  host="engine/stair_assembly.py NOSING_LENGTH; engine/source/stair_measure.py"),
    "B7-11": dict(cls="DESIGNER ITEM", band="BUILDING", step="tiles", scale=1, dxf="glass",
                  source=f"{AR}: railing lines drawn (FIN.RAILING 22, MET.RAILING.GUARD 6 in V3.0.67); post spacing and glass panels unprinted",
                  evidence="T-471 C-B7-11 POSSIBLY_APPLICABLE (specification RFI-B-A12); T-692 DXF census 0 glass / post texts",
                  rule="every villa: pcs / m2 from the railing specification",
                  host="engine/source/stair_measure.py (route stairs)"),
    "B8-04": dict(cls="OUT OF SCOPE", band="BUILDING", step="waterproofing", scale=0, dxf="shower",
                  source=f"{SAN}: 6 showers (3 trays, 3 walk-in zones), extents not dimensioned",
                  evidence="T-369 MERGED 6b9ce820; T-471 C-B8-04: 'inside the wet-room membrane (no separate tanking)'",
                  rule="owner Q-40 A (2026-10-19 20:45): no extra shower tanking, 0.20 m upturn on all walls, full-height tile; the membrane is on B8-01 / B8-03 lines; every villa: an own line only where a project detail prints a tanking height",
                  host="engine/source/waterproofing_system.py"),
    "B8-07": dict(cls="OUT OF SCOPE", band="BUILDING", step="waterproofing", scale=0, dxf="balcony",
                  source=f"{AR}: no balcony, terrace or planter label; 2F roof terrace drawn",
                  evidence="T-486 MERGED e8ee22f0: B8-07 adds 0 m2 (2F terrace 115.832 m2 already in FIN.WP.ROOF; ROOF-430 / strip CARRIED); the pool-court slab omission 4.907 m2 is B8-06 (T-494)",
                  rule="UP-WP-ROOF-001; every villa: FIN.WP.BALCONY over a drawn balcony / terrace / planter (engine/source/arch_v211.py:527)",
                  host="engine/source/arch_v211.py:527 roof_lines(); research/agents_t486"),
    "B9-03": dict(cls="MEASURABLE FROM DRAWINGS", band="BUILDING", step="masonry", scale=3, dxf="mesh",
                  source=f"{AR}: block walls (plans) + {ST} column / beam outlines (junctions); no sheet prints mesh",
                  evidence="T-355 MERGED 21f7b58a: mesh strip net 543.4739 m (GF 214.2846, 1F 278.6896, 2F 50.4997) + 164.4613 m HELD by cause; 117 wall-column junctions (sharmat); T-317 joint ledger",
                  rule="owner Q-77 (2026-10-29 21:22): mesh strip every third course along every block wall (lm) + sharmat per third course per wall-column junction (pcs), OPTIONAL items apart from the block m2; wiring QUEUED as T-363",
                  host="research/agents_t355/t355_masonry_accessories.py; engine/source/arch_walls.py"),
    "B9-05": dict(cls="DESIGNER ITEM", band="BUILDING", step="masonry", scale=2, dxf="parapet",
                  source=f"{ST} p.14 TYPICAL DETAIL OF PARAPET SECTION ('Brick Wall' on a 0.30 m upstand), p.4-6 parapet boxes ('check architectural detail'); {AR} sheet04 / Pages_05-06 roof plans",
                  evidence="Q-65 geometry 104.25 lm (subject to verification); B10-12 V3.0.55 keeps block alternatives exclusive with the RC parapet above",
                  rule="owner Q-65 C: block type and parapet construction HELD on the designer, never chosen for lightness; the run length is measurable",
                  host="engine/source/arch_walls.py (route walls)"),
    "B11-02": dict(cls="OUT OF SCOPE", band="BUILDING", step="rebar", scale=0, dxf=None,
                   source=f"{ST} p.10-12 schedules print sizes and spacings, no bar marks or shape codes",
                   evidence="engine/source/bbs_optimiser.py (route G, partial); kg are B11-01 lines (STR.REBAR 2,644 in V3.0.67)",
                   rule="a bar-mark / shape schedule is a fabrication deliverable, not a BOQ quantity; members on the owner rebar ratio (2026-11-09) cannot have one",
                   host="engine/source/bbs_optimiser.py"),
    "B11-04": dict(cls="NEEDS OWNER RULE", band="BUILDING", step="rebar", scale=3, dxf=None,
                   source=f"{ST}: no lap length, splice or stock-length note found (owner B 2026-10-29: unprinted bar ends are not calculated)",
                   evidence="URBAN-REBAR-NET-AND-PROCUREMENT@v1 (research); T-375 CONTINUOUS_BEAM_LAPS_V2 merged; wiring of splice count QUEUED as T-382",
                   rule="GAP: the procurement allowance for DETAILED members (the owner 3-5 % covers RATIO members only, 2026-11-09) and the stock bar length; net kg stay on B11-01",
                   host="engine/source/accurate_boq_rebar.py; engine/source/rebar_unit_mass.py"),
    "B12-01": dict(cls="MEASURABLE FROM DRAWINGS", band="MEP", step="mep", scale=2, dxf="sanitary",
                   source=f"{SAN}: fixtures and floor drains per floor (GF / 1F / 2F drainage plans); the legend prints FD floor drain, GCO / CO clean-outs, MH, area drain, sump pump (GF sheet read 2026-11-11 by T-692)",
                   evidence="engine/sanitary_source.py reads fixtures for wet / dry only; T-471 C-B12-01 APPLICABLE_UNMEASURED, outside the 2026-11-02 scope freeze (stated, not dropped)",
                   rule="Q-06 / UP-WET (sanitary plan locates fixtures); pcs per fixture type",
                   host="engine/sanitary_source.py"),
    "B12-02": dict(cls="MEASURABLE FROM DRAWINGS", band="MEP", step="mep", scale=2, dxf="sanitary",
                   source=f"{SAN}: drainage runs drawn with diameter and 1 % slope to an inspection chamber, rain-water pipes (RWP) marked; water supply NOT drawn (supply part = DESIGNER ITEM)",
                   evidence="T-471 C-B12-02 APPLICABLE_UNMEASURED (scope freeze 2026-11-02); T-010 wet-room evidence ('B.T.T.S.' branches)",
                   rule="lm drainage by diameter from the plan; supply HELD on the designer",
                   host="engine/sanitary_source.py"),
    "B12-03": dict(cls="DESIGNER ITEM", band="MEP", step="mep", scale=0, dxf="electrical",
                   source=f"{NONE_SET}: no electrical plan in the Drive set",
                   evidence="T-471 C-B12-03 BLOCKED_BY_SOURCE; T-692 DXF census 0 electrical texts",
                   rule="every villa: pcs / lm from electrical plans", host="none (no codemap topic)"),
    "B12-04": dict(cls="DESIGNER ITEM", band="MEP", step="mep", scale=0, dxf="hvac",
                   source=f"{NONE_SET}: no HVAC plan",
                   evidence="T-471 C-B12-04 BLOCKED_BY_SOURCE; cooling module is a load calculation, not a takeoff",
                   rule="every villa: from HVAC plans", host="none (cooling E9 is not QTO)"),
    "B12-05": dict(cls="DESIGNER ITEM", band="MEP", step="mep", scale=0, dxf="lv",
                   source=f"{NONE_SET}: no low-voltage plan",
                   evidence="T-471 C-B12-05 BLOCKED_BY_SOURCE", rule="every villa: from LV plans", host="none"),
    "B13-03": dict(cls="DESIGNER ITEM", band="BUILDING", step="other", scale=2, dxf="garden",
                   source=f"{AR}: GF plan (sheet03) labels a garden; no landscape plan",
                   evidence="OQ-04 A (outdoor finishes in the BOQ by OWNER_RULE_OUTDOOR_FLOORS_2026-10-21); garden band 13.986 m2 classification with the designer (D-48)",
                   rule="every villa: m2 / lm from a landscape plan; garden band HELD on D-48", host="tools/urban_boq_m9.py (EXT.* lines)"),
    "B13-05": dict(cls="NEEDS OWNER RULE", band="BUILDING", step="other", scale=1, dxf="expansion",
                   source=f"{NONE_SET}: no movement-joint detail or layout",
                   evidence="owner tile-joint answer (2026-10-19 22:55): expansion joint 3 mm wide; the picture's 5-6 m spacing is NOT an Urban rule; T-471 'spacing and own line not answered'",
                   rule="GAP: joint spacing / layout on roofs and outdoor paving (width given, count not); structural movement joints would be the designer's",
                   host="none (no codemap topic); nearest engine/source/membrane_layout.py"),
    "B13-06": dict(cls="DESIGNER ITEM", band="BUILDING", step="other", scale=1, dxf="joinery",
                   source=f"{AR}: kitchen / pantry counter outlines drawn (layer 5); no interior / joinery drawings, no wardrobe layout",
                   evidence="T-471 C-B13-06 BLOCKED_BY_SOURCE; T-351 counter outlines re-read",
                   rule="counter run (lm) is measurable from the outline; units and wardrobes need interior drawings",
                   host="none (floor-before-cabinetry method only)"),
    "B13-07": dict(cls="DESIGNER ITEM", band="BUILDING", step="other", scale=0, dxf="metalwork",
                   source=f"{AR}: no canopy / pergola label found; NE elevation (p7757_arch_sheet09.pdf) read by T-692: none drawn; SE / SW / NW elevations not re-read",
                   evidence="T-471 C-B13-07 BLOCKED_BY_SOURCE; T-692 DXF census 0 texts (absence of a label is not proof of absence)",
                   rule="every villa: kg / m2 from details", host="none"),
}

# first five by order: what each needs next (a QUEUED row is released, never duplicated)
DRAFTS = {
    "B9-03": "RELEASE QUEUED T-363 (lane I): wire T-355 mesh strip lm (net 543.4739, held 164.4613 by cause) + sharmat pcs (117 junctions x courses) as OPTIONAL MAS lines apart from MAS.BLOCK; Checker Gate B; no block m2 changes.",
    "B9-05": "DRAFT (lane A, every villa): parapet construction census: per roof parapet run (104.25 lm, Q-65) the ST p.14 / p.4-6 evidence RC vs block, exclusive with B10-12 STR.CONC.PARAPET; run length DRAWING-CONFIRMED, block type HELD (D-nn), never both RC and block on one run.",
    "B4-05": "RELEASE QUEUED T-364 (lane I): wire T-317 spatter m2 face by face on the T-349 backing lines (913.7202 determinate + held bounded), Q-79 1:2 material binding; HELD stays HELD.",
    "B4-04": "RELEASE QUEUED T-314 r3 (lane I): exterior plaster / Sigma faces from the T-305 ledger into FIN.EXT.FINISH lines; base lines replaced, every other line byte-identical.",
    "B7-01": "DRAFT (lane I, every villa): wire the merged STAIR_FLIGHT_ONCE_V1 (T-135 05e2eab, flights_once) into the SAME candidate so each flight drawn on two plans is measured once; the 14 FIN.STAIR.FLIGHT lm lines leave base-run state only where a flight length is DRAWING-CONFIRMED, else stay HELD by name; tread / riser / nosing lines byte-identical.",
    "B4-09": "DRAFT (lane A, every villa): CORNER BEAD LEDGER: every external arris of a plastered face (plan corner x Q-72 plaster height) once, tied to its FIN.PLASTER line; opening edges separate and named; non-Alsenan fixture (mirror, rotation, mm units); OD-V3-4.",
}


def load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def select(master: dict) -> tuple[list[dict], list[dict]]:
    """PRIMARY: NOT_IN_CANDIDATE or NOT_IMPLEMENTED; BAND: IN_CANDIDATE_BASE_LINES (not already primary)."""
    prim, band = [], []
    for f in master["families"]:
        st = f["candidate"]["state"]
        if st == SELECT_PRIMARY or f["capability"] == "NOT_IMPLEMENTED":
            prim.append(f)
        elif st == SELECT_BAND:
            band.append(f)
    return prim, band


def validate(selected_ids: list[str], classes: dict) -> list[str]:
    """Every selected family exactly once and classed; no class for an unselected family; class values legal."""
    errors = []
    seen = set()
    for i in selected_ids:
        if i in seen:
            errors.append(f"DOUBLED {i}")
        seen.add(i)
        if i not in classes:
            errors.append(f"NO CLASS {i}")
    for i, c in classes.items():
        if i not in seen:
            errors.append(f"CLASS FOR UNSELECTED {i}")
        if c.get("cls") not in CLASSES:
            errors.append(f"BAD CLASS {i}: {c.get('cls')}")
        if c.get("band") not in BANDS:
            errors.append(f"BAD BAND {i}: {c.get('band')}")
        if c.get("step") not in STEP:
            errors.append(f"BAD STEP {i}: {c.get('step')}")
        for k in ("source", "evidence", "rule", "host"):
            if not str(c.get(k, "")).strip():
                errors.append(f"NO {k.upper()} {i}")
    return errors


def order_key(code: str, c: dict) -> tuple:
    return (BAND_ORDER[c["band"]], CLASS_ORDER[c["cls"]], STEP[c["step"]], -int(c["scale"]), code)


def line_presence(index_lines: list[dict], families: list[dict]) -> dict:
    """item codes of each family present in the candidate line index (a NOT_IN_CANDIDATE family must show none)."""
    codes = {}
    for l in index_lines:
        codes[l["item_code"]] = codes.get(l["item_code"], 0) + 1
    return {f["code"]: {ic: codes.get(ic, 0) for ic in f.get("item_codes", [])} for f in families}


def build(master: dict, index_lines: list[dict], classes: dict | None = None, dxf_hits: dict | None = None) -> dict:
    classes = FAMILY_CLASS if classes is None else classes
    prim, band = select(master)
    sel = prim + band
    ids = [f["code"] for f in sel]
    errors = validate(ids, classes)
    pres = line_presence(index_lines, sel)
    for f in prim:
        if f["candidate"]["state"] == SELECT_PRIMARY and any(pres[f["code"]].values()):
            errors.append(f"LINE PRESENT FOR NOT_IN_CANDIDATE {f['code']}: {pres[f['code']]}")
    if errors:
        raise ValueError("; ".join(errors))
    rows = []
    for f in sel:
        c = classes[f["code"]]
        rows.append({
            "code": f["code"], "group": f["group"], "item": f["item_en"], "unit": f["unit"],
            "capability": f["capability"], "candidate_state": f["candidate"]["state"],
            "set": "PRIMARY" if f in prim else "BASE_LINES_BAND",
            "item_codes": f.get("item_codes", []), "candidate_lines_by_code": pres[f["code"]],
            "class": c["cls"], "band": c["band"], "trade_step": c["step"], "scale_bucket": c["scale"],
            "drawing_source": c["source"], "evidence": c["evidence"], "rule_or_gap": c["rule"], "host_module": c["host"],
            "dxf_keyword_group": c.get("dxf"),
            "dxf_text_hits": (dxf_hits or {}).get(c.get("dxf")) if c.get("dxf") else None,
        })
    rows.sort(key=lambda r: order_key(r["code"], classes[r["code"]]))
    for n, r in enumerate(rows, 1):
        r["order"] = n
    counts = {k: sum(1 for r in rows if r["class"] == k) for k in CLASSES}
    return {
        "master_version": master["version"], "candidate": master["candidate_census"]["method_version"],
        "families_in_master": len(master["families"]), "primary": len(prim), "base_lines_band": len(band),
        "selected": len(rows), "class_counts": counts,
        "band_counts": {b: sum(1 for r in rows if r["band"] == b) for b in BANDS},
        "rows": rows,
        "first_five": [{"code": r["code"], "draft": DRAFTS.get(r["code"], "")} for r in rows[:5]],
    }
