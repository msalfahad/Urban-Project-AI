# T-262: opening-to-room assignment by geometry, not by name (any villa; Alsenan as the sample)

Worker 2, 2026-10-24 08:47 UTC onward. Lane A, gate 1. Research + tests only (`research/agents_t262/*`,
`tests/t262_opening_rooms/*`): no engine module, method, rule / knowledge version, registry, merged ledger or released /
candidate quantity changed; nothing applied. Development villa, not an accuracy claim. ERS read: s.2 steps 1-4 (physical
element first, evidence hierarchy, reconstruction from the drawing, reconciliation in units), s.3, s.4, s.7. Drawing:
Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55); every reference is an entity
handle on it; no coordinate, image, client name or personal data is committed.

## 1. Result in engineering terms

| Check (59 openings: 29 windows, 27 doors, 1 gate, 2 arches; T-249 inventory, joined by their handles) | Result |
|---|---|
| Sides settled by geometry | 118 / 118 (116 one room or no room, 2 serve two rooms: W03, D-1F-02); 0 SPLIT; every door / gate / arch has two sides |
| Census side labels (T-198 SIDE_A / SIDE_B, carried from T-144 / T-150 / T-175) | 51 AGREE, 2 AGREE_OPEN_ZONE, 1 LABEL_INCOMPLETE, **5 LABEL_WRONG** |
| T-128 r3 per-room opening table (feeds V3.0.9 plaster / paint and T-209 wet tiles) | **32 / 32 rooms AGREE** (doors, arches, windows by count per room) |
| T-237 crosswalk (room -> census id, by name / width) | 76 AGREE, **4 JOIN_WRONG** (the two west baths swapped), 3 not in the inventory (lift doors) |
| T-209 wet-tile input (window id per room) | 11 AGREE, **2 ids in the wrong room** (W19 / W20 swapped) |
| Room regions over wall strips | GF-16 only: 3 strips 0.522 m2 + its door reveal 0.120 m2 |

**No trade total and no per-room m2 moves today**: every per-room line of the candidate reads the T-128 walk, which is
geometric and agrees on 32 / 32 rooms; the wrong labels sit in the census text and in two research joins, and every
swapped pair carries equal values (stated below from the values, never assumed). Engine vs freelancer: unchanged on
every trade (0.000 m2, 0.0 %); this task moves identity, not quantity. What it prevents: the plaster / paint whole line
(T-244) and any per-room trade that joins openings by the census names would put W19 / W20 / D-1F-01 / D-1F-04 in the
wrong west bath and W06 in the wrong W.C. wedge, and would lose GF-08's share of W03.

## 2. Physical element and method (ERS s.2 steps 1-3)

An opening is a gap through ONE wall. Its jambs cut the wall's two faces; the room on each face at the opening (or no
room: outdoors, a court, a roof, an unwalked space) is the opening's side A / side B. A door therefore has two sides; a
window in an outer wall has one room and no room. A room region is the area bounded by wall faces; it never lies
inside a wall strip.

`opening_rooms.py` (stdlib, any villa) walks square to the opening line from one station every 5 cm, on both sides,
in 0.01 m steps up to 0.70 m, and takes the first room region entered. The opening line comes from the drawing by
the inventory's handles, never from a name or an engine id (`capture_t262.py`):

- door / gate: hinge (swing-arc centre) to the closed-leaf point (the arc end the drawn open leaf does not touch);
  side A = the swing side;
- window: the longest glazing entity of the symbol, probed square to itself (a curved band along its own arc);
- leafless arch: the long axis of the arch block's outline.

Room regions: the merged T-128 r3 walk (walk_r2.py, a6ac2c66) executed unchanged, re-checked against walk_r3.json on
32 / 32 rooms before use. A side is ESTABLISHED (one room or none on every station), MULTI_ROOM (every station finds a
room, more than one) or SPLIT (refused). A region covering the opening's own reveal is named and the side is the room
beyond it. Two regions overlapping at a probe point are refused. Labels are read once into the room set each label
claims (by the T-128 room names) and compared as an unordered pair; open-zone parts that only a clip box divides
(GF-07 / GF-08 / GF-14; 1F-13 / ST-1F; 2F-01 / ST-2F) agree only as AGREE_OPEN_ZONE.

## 3. Results (`OPENING_ROOMS_T262.csv`, handles per row)

**(a) LABEL_WRONG (5)**

| Opening (handles) | Census label | Geometry | Consequence |
|---|---|---|---|
| W06 (glazing 3E3 .. 3ED) | W.C. core wedge A | GF-13 (wedge B, 245 x 167); GF-12 is 1.24 m away | T-128 / T-209 / T-237 already put W06 in GF-13: 0 m2 |
| W19 (CFB .. D05) | bath west upper | 1F-03 (T-128 "lower") | T-237 and T-209 put it in 1F-02 |
| W20 (CEE .. CF8) | bath west lower | 1F-02 (T-128 "upper") | T-237 and T-209 put it in 1F-03 |
| D-1F-01 (D315 insert C2B) | bed west 425 x 450 / bath west upper | 1F-01 / 1F-03 | T-237 puts it in 1F-02 |
| D-1F-04 (D315 insert C2E) | bed 500 x 365 / bath west lower | 1F-04 / 1F-02 | T-237 puts it in 1F-03 |

Cause: the two 1F west baths stand SIDE BY SIDE (west and east of each other, both 2.05 x 2.45 by their walked
regions), not upper / lower. "Upper" / "lower" names a north / south split the plan does not draw, so T-144 and T-128
attached the two words to opposite rooms and every name join inherited one or the other. Geometry: the west bath
(T-128 1F-03) has W19 and the door to the west bed room 1F-01 (D-1F-01, on their shared wall); the east bath (T-128
1F-02) has W20 and the door to the 500 x 365 bed room 1F-04 (D-1F-04). Values: W19 and W20 are both 0.60 wide, sill
1.70, head 2.50 (T-201, DRAWING-CONFIRMED); both doors D315 0.80, head 2.20 (Q-55 C, ASSUMED — OWNER-APPROVED).
So the swap moves 0.000 m2 in T-209 (1F-02 / 1F-03 tile nets 27.91 each, both unchanged) and in T-237's room faces,
and no door class moves (each door still has a bath on one side, UP-DOOR-CLS-003; each window is still in an outer
wall).

**(b) LABEL_INCOMPLETE (1): W03.** The curved pool glazing serves TWO rooms: the master bed room GF-15 and the open
room GF-08 (the GF-15 / GF-08 partition stops on the glass); the census names GF-15 only. T-128 already splits it by
the walk (GF-15 5.106 m, GF-08 1.625 m; T-250: room-side line 6.726 .. 6.738). Station shares here are an identity
check, not a length (stations on the inner glass line 280).

**(c) AGREE_OPEN_ZONE (2):** D-1F-02 (bed west door, its outer side in both the landing 1F-13 and the shaft box ST-1F:
T-128 splits its 1.00 m into 0.425 + 0.580) and D-1F-03 (bed 500 x 365: census "stair landing (shaft side)", geometry
1F-13). Both are one space divided only by the shaft clip box; no quantity question.

**(d) Unwalked interior space:** the dressing passage of the 380 x 430 bed room is not a walked room region; A-1F-01
(arch) and D-1F-07 (bath by the laundry) have NO_ROOM on that side, matching the census label (T-180 already named the
dressing-scope finding +2.970 m2 floor area).

## 4. GF-16 region inside wall strips (`REGION_OVERLAP_T262.csv`)

| Wall material inside the walked GF-16 region | m2 |
|---|---|
| strip between 2DD / 2DE (0.15, GF-W19, 2.000 m) | 0.300 |
| strip between 324 / 325 (0.15, diagonal GF-W31) | 0.1805 |
| strip between 2E5 / 2E7 (0.15, the south wall stub beside the door, overlap 0.279 m) | 0.0418 |
| D-GF-14 doorway reveal (0.80 x 0.15) | 0.120 |
| walked region / region without the wall material / printed (T-074, T-147) | 4.4203 / 3.776 / 3.717 |

Mechanism (physical cause): D-GF-14 is the only door drawn as a LOOSE swing arc (layer D), not a door block; the
region builder (rooms.py) closes door BLOCKS only, so the bath's near face is open at the doorway, the region flows
into the reveal and along the hollow double-line walls around the bath, and stops at their FAR faces (2DE = GF-15's
face; 325 = GF-14's side; the gap closure on the far face of the doorway). So 2DE is walked by GF-16 and GF-15 and the
bath's own face 2DD by nobody. Residual 0.059 m2 (3.776 vs printed 3.717) is not explained here (named).

Per-trade effect today (each read from the ledger that carries the trade): wall tile GF-16 = T-128 / T-209 use the
T-074 verified hand outline 7.625 m, not the walk: **0.000 m2**; floor / ceiling GF-16 = T-147 printed 3.717 m2:
**0.000**; plaster / paint GF-15 = its own region, on its own face 2DE: **0.000**; T-209 sunken-panel share (48.6 % of
the 4.5958 m2 raw region): status text only, GF-16 stays HELD on T-206 either way: **0.000**; walk contour 8.314 m vs
7.625 m: used by no candidate line. The walk's GF-16 is wrong (+0.703 m2, +0.689 m contour) but nothing that is carried
reads it; any future reader must use the T-074 outline or a region with the loose-arc door closed.

## 5. Where the name join lives (step 1 of the row)

No engine module writes a room into the opening census: `engine/source/opening_census.py` carries no room field, and
the candidate's per-room deductions come from the T-128 r3 walk (V3.0.9 `t211_inputs.py` reads OPENINGS_T128_R3.csv
by ROOM_ROW; T-209 hosts per the T-128 walk). The room words are hand text in the research census
(T-144 -> T-150 -> T-175 -> T-198, SIDE_A / SIDE_B) and two research joins read them: T-237's crosswalk
(`alsenan_t237.py`, name / width match) and T-209's window ids per room. So no frozen or engine file needs a new
version; the check lives beside the census as research (`opening_rooms.py`), any villa.

The V3.0.10 window lines key each window to the ENGINE's own room of its ARCH_OPENING (t232_inputs.py
WINDOW_ROOM): crosswalked to the T-128 rooms in part 2 (section 10, 2026-10-24 second run): every engine room agrees
with the geometric join. The freelancer's per-room wet-tile metres for the two west baths (T-209 FL_LM 9.0 / 8.9) are
joined by name too; his workbook has no geometry, so which bath each of his rows is cannot be established from it.

## 6. Lane I proposal (nothing applied; room level only, trade totals unchanged)

1. T-244 (plaster / paint whole line) and any per-room join use `OPENING_ROOMS_T262.csv` (ROOMS_GEO) for room <->
   opening identity, never the census names or T-237's name join.
2. 1F-02 carries W20 and D-1F-04; 1F-03 carries W19 and D-1F-01 (T-237 rows and T-209 input ids swap; 0.000 m2).
3. W03 is a window of GF-15 AND GF-08 (finish deduction already split by T-128).
4. Census text correction (next census version, not an edit of T-198): W06 side "W.C. core wedge B"; W19 / D-1F-01 the
   west bath; W20 / D-1F-04 the east bath; W03 adds the open room.

## 7. Statuses and verdict proposals

Opening -> room identity for the 59 openings: DRAWING-CONFIRMED (geometry, handles), Checker to re-check. No
quantity is changed, VERIFIED or released. Verdicts: W06 ENGINE_RIGHT (T-128 / T-209 right, census label wrong);
W19 / W20 / D-1F-01 / D-1F-04: T-128 RIGHT, census label and T-237 / T-209 name joins wrong, 0 m2 (equal values);
W03: T-128 RIGHT (two rooms), census incomplete; GF-16: walk region wrong (+0.703 m2), no carried line reads it.
No owner question (ERS 2.7 not met: the drawing settles every case).

## 8. For the Checker (re-check from the jambs; handles on P7757.dxf)

1. W06: glazing 3E3 .. 3ED in the wall of the wedge whose door is D-GF-12 (GF-13 / "wedge B"), not D-GF-11's wedge.
2. W19: glazing CFB .. D05 in the WEST bath, the one whose other door D-1F-01 (D315 insert C2B) opens to the west bed
   room 1F-01; W20 (CEE .. CF8) in the east bath whose door D-1F-04 (insert C2E) opens to 1F-04.
3. One west-bath door: D-1F-01's hinge / closed-leaf line on the wall between 1F-01 and the west bath.
4. GF-16: D-GF-14 is a loose arc (layer D), the strip 2DD / 2DE is inside the walked region.
Reproduce: `capture_t262.py <P7757.dxf> --out <scratch>/t262_capture.pkl`, then `alsenan_t262.py <capture> --check`;
tests `tests/t262_opening_rooms` (with URBAN_P7757_DXF set, the rebuild test runs).

## 9. Rules and lessons

- R-T262-1 (proposed, any villa): the room of an opening is the room region entered square to the opening line on
  each side of its wall (a door: two sides, a window in an outer wall: one room and none); a label or name never
  decides it; a side whose stations disagree (some room, some none) is not established and refused as a value.
- R-T262-2: an opening may serve several rooms on one side (a band with a partition stopping on it): every room is
  listed; a label naming one of them is incomplete, not right.
- R-T262-3: a room region must not cover a wall strip or an opening reveal; a door drawn as a loose swing arc closes
  the region like a door block, or the region is refused for per-room use.
- Lessons row proposed (ERS s.7): "Two side-by-side baths named 'upper' / 'lower' (a north / south split the plan
  does not draw) were attached to opposite rooms by two ledgers; every later join by name inherited the swap
  (W19 / W20, D-1F-01 / D-1F-04, T-237, T-209) | a room name is a label, not a location | join openings to rooms by
  the drawn opening line and the room regions on both faces; a name may only be checked against that (any villa) |
  tests/t262_opening_rooms (wrong-room label refused, door with one side refused, region over a strip found)".

## 10. Part 2: the engine's own room of each opening (2026-10-24, second worker-2 run)

Question: the candidate's window lines (V3.0.10 .. V3.0.12, t232_inputs.py WINDOW_ROOM) and the engine's door
classes (UP-DOOR-CLS-003, a wet room on one side) read the ENGINE's room of an opening, not the census label. Is that
room the one the drawing puts the opening in?

Method (`engine_rooms_t262.py`, any villa): the released ARCH_TAKEOFF_V2.9 arch run on P7757.dxf (tools/urban_boq_m9.py
arch, conventions V6, route G profile M4, facts as research/agents_t131; scratch only) gives every engine room's
polygon and the door / window / passage ids it names; each engine room is crosswalked by AREA to the T-128 r3 regions
of part 1 (overlap at least 50 % of the reference room or of the engine room; R-T262-4 proposed); the engine's room of
an opening = every engine room naming the census ENGINE_REF id on that floor; compared with ROOMS_GEO of part 1.

Result (59 openings; ENGINE_ROOMS_T262.csv, ENGINE_ROOM_XWALK_T262.csv, CANDIDATE_WINDOW_ROOM_T262.csv):

| Verdict | Openings |
|---|---|
| AGREE (one engine room per geometric room) | 29 |
| AGREE_COARSER (an engine open-plan face spans two T-128 rooms: GF-07 + GF-08, 1F-13 + ST-1F, 2F-01 + ST-2F) | 17 |
| AGREE_PLUS_UNREFERENCED (the engine also names a small UNLABELLED space where part 1 found no room: 1.56, 2.97, 3.60 m2) | 4 + 1 coarser |
| ENGINE_WRONG_ROOM / ENGINE_SIDE_MISSING | **0** |
| NO_ENGINE_OPENING (the 5 doors held in the engine's door schedule only, D-GF-15, W03, W18 missed by V2.9) | 8 |

- The five census labels part 1 found wrong are RIGHT in the engine: W06 -> GF-13 (wedge B); W19 -> 1F-03 (west bath),
  W20 -> 1F-02 (east bath); D-1F-01 -> 1F-01 + 1F-03. D-1F-04 is not in the engine's room model (door schedule only),
  so its room is the geometric one of part 1.
- All 27 candidate WINDOW_ROOM ids are this run's rooms naming that opening (27 / 27 SAME: room id = hash of the face
  id, the same face model in V2.9 and the candidate).
- Effect: 0.000 m2 / 0 pcs on every trade; the window lines and door classes of the candidate already sit in the
  geometric rooms; only the research census labels (and the T-237 / T-209 name joins of part 1) carry the swap.
- The UNLABELLED spaces (side-passage pocket by D-GF-05 / W10, a pocket outside W09, the dressing-passage pocket by
  D-1F-07 / A-1F-01) are not T-128 rooms; they are listed with class and area, never counted as a room match.
- Statuses: identity DRAWING-CONFIRMED (engine geometry vs part-1 geometry, two independent region builders); no
  quantity changed, VERIFIED or released. Verdict proposal: ENGINE_RIGHT for the engine's room of W06, W19, W20,
  D-1F-01 (census labels wrong).
- Reproduce: `capture_t262.py <P7757.dxf> --out <s>/cap.pkl`; the V2.9 arch run to `<s>/v29`; then
  `engine_rooms_t262.py <s>/cap.pkl <s>/v29/ARCH_ROOMS.json --out <s>/eng` (CSV byte-identical to the committed ones).
  Tests: tests/t262_opening_rooms/test_t262_engine_rooms.py (non-villa fixture with mirror and 37 / -90 deg rotation,
  open-plan coarser, outdoors pocket, wrong room / missing side / pocket-only / sliver refused).
- Lesson (ERS s.7, proposed): two independent region builders agreeing on an opening's room is the check a name join
  can never give; a name in a census is checked against the engine's face model, not the other way round.
