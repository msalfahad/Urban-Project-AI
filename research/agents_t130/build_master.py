"""T-130 builder (kept outside the repository): writes rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json from
(1) the 1.0.0 file (codes, names, units, source_needed, next_slice copied unchanged),
(2) the per-family audit below (status, evidence file:line / merge commit / verifier run, readers, missing, V3.0),
(3) the development-villa run summaries made by summ.py on the runs of this task (engine values only).
Every file:line is checked to exist and to hold the symbol named right after it (r3); every commit is checked with
git. Usage:
    python3 -I build_master.py <repo> <runs_dir>          (runs of the released and the V2.13 candidate method)
    python3 -I build_master.py <repo> <previous 1.1.0>    (r3: reuse the development-villa figures of a previous
                                                           build when no released-path file changed since its runs)
"""
import json, subprocess, sys
from pathlib import Path

REPO, RUNS = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(Path(__file__).parent))
import summ  # noqa: E402

HEAD = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "--short=7", "HEAD"], text=True).strip()
OLD = json.loads((REPO / "rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json").read_text(encoding="utf-8"))

REL = "ARCH_TAKEOFF_V2.9 + route G (conventions URBAN_M8_GENERIC_CONVENTIONS_V6)"
V30 = "ARCH_TAKEOFF_V3.0 (merged b1a6d6d, verifier 2026-10-21 02:30 UTC; opt-in, not the released default; extended in place by ARCH_TAKEOFF_V3.0.1, T-133 merge 967d6d5, verifier 2026-10-21 17:40 UTC: route G scope piece + MEMBRANE_FOLD_V5 audit; every other line byte-identical to V3.0)"

# ---------------------------------------------------------------- per-family audit
# c: capability 1.1.0; ev: evidence (file:line refs and commits); rd: released reads; cand: opt-in readers;
# miss: what is missing; v3: in V3.0 yes/no; plan: task ids planned to change it in V3.0.x; codes: item codes whose
# lines the development-villa summary reports (released run, then candidate run)
A = {}


def f(code, c, ev, rd, cand, miss, v3, plan=(), codes=(), cand_codes=None, note=None):
    A[code] = dict(c=c, ev=ev, rd=rd, cand=cand, miss=miss, v3=v3, plan=list(plan), codes=list(codes),
                   cand_codes=list(cand_codes if cand_codes is not None else codes), note=note)


# r3: pieces the T-133 extension left waiting (named in its WAITING table)
W = "engine/source/arch_v301.py:88 WAITING: "
T133 = " (T-133 ARCH_TAKEOFF_V3.0.1 merged PARTIAL 967d6d5 without it, verifier 2026-10-21 17:40 UTC)"
NONE_EMITTED = "no method emits a line of this family: no item code for it in engine/source/boq_line.py:46-110 ITEMS and " \
               "none in the item codes seen in the released and candidate runs (run_evidence.item_codes_seen)"
for c in ("B1-01", "B1-03", "B1-04", "B1-05", "B1-07"):
    f(c, "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "site works are not measured by any route", "no")
f("B1-02", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/struct_n10.py:216 excavation(): a pit per footing (L + 2 ws) x (W + 2 ws) and a trench per ground "
   "beam clear length x (width + 2 ws) from the route G register; the volume only when the working space and the depth "
   "(or NGL and founding level) are stated facts, otherwise HELD (EX-D1 / EX-D2); backfill always HELD (:255 \"backfill\")",
   "tools/struct_n10.py:40 build(): standalone tool over a route G run, writes EXCAVATION.json; no method imports it "
   "(only tests/m9_n10 and the rebar firewall registry name it)",
   "commit 40f3184 (Structural N10); tests/m9_n10/test_n10_structural.py:82 test_excavation_is_held_without_levels_and_working_space() / :90 "
   "test_excavation_with_stated_depth_and_working_space() (held without levels, measured "
   "with stated depth and working space)",
   "development villa (" + "tool run on the released route G registers, head 0dec24c): 26 footing pits + 3 ground-beam "
   "trenches, footprint 139.299 m2; volume HELD: working space and excavation depth not stated (no project fact); the "
   "59 UNRESOLVED ground-beam rows of route G give no trench (the 3 trenches come from its PROVISIONAL rows)"],
  "none", "none (standalone tool tools/struct_n10.py)",
  "not in any method or BOQ line; volume needs the working space and the depth (owner / project facts); pits are not "
  "merged where they overlap (upper bound); by type and depth (soil classes) not modelled; no hand check", "no",
  note="1.0.0 and 1.0.0-derived r1 said NOT_IMPLEMENTED; raised on the verifier's T-130 r1 finding (merged, tested "
       "code measures the footprints)")
f("B1-06", "BLOCKED_BY_SOURCE", [NONE_EMITTED], "none", "none", "needs a site investigation", "no")

f("B2-01", "PARTIAL",
  ["engine/source/arch_rooms.py:984 spaces() builds the room register of every plan region in the released arch route",
   "engine/source/arch_measure.py:92 room_id(floor, face_id): stable room id on every line",
   "tools/urban_boq_m9.py:260 ARCH_ROOMS.json written by every arch run (not a BOQ line)",
   "commit 677c740 (T-099 room census guard, verifier run 37): 0 rooms lost on the development villa, 3 unlabelled "
   "rooms HELD; engine/source/room_census_guard.py:186 census() is read by no method",
   "commit 362630a (T-061 room label guard): engine/source/room_label_guard.py:171 guard() is read only by the "
   "opt-in methods (engine/source/arch_v211.py:232 room_label_guard)",
   "commit b35c944 (T-022 ROOM_VOCAB_V2): read by ARCH_TAKEOFF_V2.10 and later only"],
  "ARCH_TAKEOFF_V2.9: register file ARCH_ROOMS.json, room ids on every line; no BOQ line of its own",
  "ARCH_TAKEOFF_V2.10 .. V2.13 (room vocabulary V2, label guard from V2.11)",
  "no BOQ line (a register, not a quantity); unlabelled rooms held; the census guard is not wired", "yes",
  note="1.0.0 named TS01 / room_slice (tests); the register now runs in the released arch route")
f("B2-02", "PARTIAL",
  ["engine/source/arch_measure.py:381 FIN.FLOOR.PORCELAIN: the room's clear floor area is the net of its floor-finish line",
   "engine/source/arch_measure.py:323 ARCH.SPACE: a space without a finish kind gets ARCH.SPACE / ARCH.EXTERIOR with its area",
   "commit c1f0467 (T-113, verifier run 40): first-floor living released 44.869 m2 vs hand 38.588 m2 (+16.3 %), "
   "HAND_RIGHT: the stair void residue stays in the room face",
   "commit 5592692 (T-116 STAIR_FLOOR_RESIDUE_V1): engine/source/stair_floor_residue.py:142 face_residue(), read by "
   "no released method; wired in ARCH_TAKEOFF_V3.0 (T-131)"],
  "ARCH_TAKEOFF_V2.9: on FIN.FLOOR.PORCELAIN / FIN.FLOOR.WET_TILE / ARCH.SPACE lines",
  "ARCH_TAKEOFF_V3.0 stair-residue piece (merged b1a6d6d)",
  "a stair footprint or void inside a room face is not deducted in the released method (verifier-confirmed); the "
  "landing / arrival floor moves T-122 / T-129 wait for an outline reader (" + W + "T-122, T-129" + T133 + ")", "yes",
  codes=("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "ARCH.SPACE"),
  note="no census map entry for B2-02 (engine/source/coverage_census.py:23-40 FAMILY_ITEMS): a run always reports it NOT_RUN")
f("B2-03", "PARTIAL",
  ["engine/source/arch_floor.py:108 reconcile(): gross floor plate per floor with three balance checks",
   "engine/source/arch_floor.py:156 gross_floor_plate_m2",
   "tools/urban_boq_m9.py:266 ARCH_FLOOR_AREAS.json written by every arch run"],
  "ARCH_TAKEOFF_V2.9: ARCH_FLOOR_AREAS.json (file, not a BOQ line)", "same in every later method",
  "no BOQ line; no independent check of the plates; no census map entry", "yes",
  note="development villa released run: gross floor plate GF 284.1465, 1F 209.8017, 2F 55.08 m2, every floor's three "
       "checks BALANCED (ARCH_FLOOR_AREAS.json of the released run)")
f("B2-04", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/arch_v213.py:223 typed_zones(): an open-plan wet zone measured from its printed size typed in "
   "the project data file (owner Q-37 A, Q-17 A)",
   "commit 2264938 (T-120 ARCH_TAKEOFF_V2.13, verifier run 44): pantry 4.50 x 3.00 m = 13.50 m2, 2 rolls, re-checked",
   "commit 8c23eea (T-114, verifier run 41): pantry cutting plan by hand"],
  "none (ARCH_TAKEOFF_V2.9 holds the zone)", "ARCH_TAKEOFF_V2.13 (opt-in)",
  "a zone needs its printed size typed by a reviewer; not in the released method", "yes")
f("B2-05", "PARTIAL",
  ["engine/source/arch_floor.py:65 split_face(): voids and stair treads split out of a face in the released route",
   "engine/source/arch_measure.py:434 FIN.CEILING over a void",
   "commit c1f0467 (T-113, verifier run 40): a stair void residue left inside the first-floor living face (+6.281 m2)",
   "commit 5592692 (T-116): stair_floor_residue.py read by no released method"],
  "ARCH_TAKEOFF_V2.9 (floor-area categories VOID / STAIR_FLIGHTS in ARCH_FLOOR_AREAS.json)",
  "ARCH_TAKEOFF_V3.0 stair-residue piece (merged b1a6d6d)",
  "void residues inside room faces (verifier-confirmed defect); double heights not measured as a line", "yes")

f("B3-01", "PARTIAL",
  ["engine/source/arch_measure.py:381 FIN.FLOOR.PORCELAIN per dry room",
   "commit c1f0467 (T-113, verifier run 40): first-floor living +16.3 % HAND_RIGHT (stair void residue)",
   "commit 4ae3a68 (T-122, verifier run 45): first-floor porcelain 33.594 .. 33.711 m2 under owner Q-66 B (research)"],
  "ARCH_TAKEOFF_V2.9: FIN.FLOOR.PORCELAIN", "ARCH_TAKEOFF_V3.0 stair-residue piece (merged b1a6d6d)",
  "rooms with a stair void / landing inside them (verifier-confirmed); no printed tile size, so the tile count "
  "(engine/source/tile_count.py, commit 8de2a21) holds every room; the 1F living porcelain range under Q-66 B waits "
  "(" + W + "T-122" + T133 + ")", "yes",
  codes=("FIN.FLOOR.PORCELAIN",))
f("B3-02", "PARTIAL",
  ["engine/source/arch_measure.py:381 FIN.FLOOR.WET_TILE per wet room",
   "commit 8fcabe0 (T-010 wet / dry from the room label and fixtures, verifier run 22): read by ARCH_TAKEOFF_V2.11 "
   "and later only (engine/source/arch_v211.py:105 wet_classes())"],
  "ARCH_TAKEOFF_V2.9: FIN.FLOOR.WET_TILE (wet rooms merged into dry zones where the label is ambiguous)",
  "ARCH_TAKEOFF_V2.11 .. V2.13 (wet / dry evidence)",
  "the released method misses wet rooms that only the fixtures identify", "yes", codes=("FIN.FLOOR.WET_TILE",))
f("B3-03", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/marble_thresholds.py exists (research engine, read by no method)",
   "commit 4ae3a68 (T-122, verifier run 45): first-floor landing marble 4.875 m2 by hand (research only)"],
  "none", "none", "no marble floor line except stair landings (B7-04); the landing marble of T-122 / T-129 waits "
  "(" + W + "T-122, T-129" + T133 + ")", "no")
f("B3-04", "PARTIAL",
  ["engine/source/owner_finish_scope.py:136 FIN.MARBLE.THRESHOLD: the wet-area doorway marble threshold (owner scope, knowledge 1.0.0+)",
   "engine/source/surface_ledger.py:115 ARCH.THRESHOLD: the threshold row of a door"],
  "ARCH_TAKEOFF_V2.9: FIN.MARBLE.THRESHOLD", "same in every later method",
  "census gap: FIN.MARBLE.THRESHOLD is not mapped to B3-04 (engine/source/coverage_census.py:23-40 FAMILY_ITEMS)", "yes",
  codes=("FIN.MARBLE.THRESHOLD",))
f("B3-05", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/finish_materials_table.py:1 \"FINISH MATERIALS TABLE V1\": the cement-sand bed under tiles as a range (owner Q-45), roof / balcony "
   "screed HELD (owner Q-41, thickness not given)",
   "commit 6002856 (T-086, verifier run 30): new files only, read by no method"],
  "none", "none", "no BOQ line; screed thickness on roofs not given (Q-41)", "no")
f("B3-06", "PARTIAL",
  ["engine/source/arch_measure.py:506-557 FIN.SKIRTING per room (released, bounded or held)",
   "commit a51bdca (T-106 skirting deduction audit, verifier run 40): all released nets right; 20 of 28 lines do "
   "not list 17.035 m of deductions; engine/source/skirting_deduction_audit.py:196 audit() read by no method"],
  "ARCH_TAKEOFF_V2.9: FIN.SKIRTING", "none",
  "listed deductions do not add back on 20 lines (T-118 queued); door closures without a door id", "yes",
  codes=("FIN.SKIRTING",))
f("B3-07", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/trade_strips.py exists (research engine, read by no method)",
   "the released route emits ARCH.THRESHOLD doorway strips (engine/source/surface_ledger.py:78 ARCH.THRESHOLD) as BLOCKED_RFI "
   "(owner decision Q-S6-1 open): geometry, not a profile line"],
  "none (ARCH.THRESHOLD strips held)", "none", "no profile / transition-strip line", "no")

f("B4-01", "PARTIAL",
  ["engine/source/arch_measure.py:639-681 FIN.WALL.TILE in the wall-finish loop of every wet room",
   "commit a703655 (T-112, verifier run 40): wall heights by the owner method and from the drawing (research)"],
  "ARCH_TAKEOFF_V2.9: FIN.WALL.TILE (every line BLOCKED_RFI without an established height)", "same",
  "height not established (owner Q-48 A / Q-52): every development-villa line held", "yes", codes=("FIN.WALL.TILE",))
f("B4-02", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "kitchen / laundry tiled zones not measured", "no")
f("B4-03", "PARTIAL",
  ["engine/source/arch_measure.py:639-681 FIN.PLASTER per room face",
   "engine/source/arch_measure.py:195 _wall_finish_rs(): net from the room's own boundary",
   "commit d52b5dd (T-081-r2 room levels V2 + finish height V2, verifier run 30): engine/source/finish_height_v2.py:173 "
   "room_heights() read by no method",
   "commit a703655 (T-112, verifier run 40): owner method 234.17 m2 on 4 verified dry rooms (research)"],
  "ARCH_TAKEOFF_V2.9: FIN.PLASTER", "none",
  "most walls held without an established height; the owner manual method is not wired", "yes",
  codes=("FIN.PLASTER",))
f("B4-04", "PARTIAL",
  ["tools/urban_boq_m9.py:1274 _v29_facade(): facade outline run per floor and area (UP-FACADE-001)",
   "tools/urban_boq_m9.py:2718 FACADE.json",
   "commit 5476226 (T-014 facade gap closure, verifier run 39): engine/source/facade_gap_closure.py read only by "
   "engine/source/facade_passage_walls.py",
   "commit 4fddf74 (T-109 passage walls) + 6699bb6 (T-123, verifier run 45): ground-floor run 98.887 -> 105.887 m "
   "(hand right), wired in ARCH_TAKEOFF_V3.0"],
  "ARCH_TAKEOFF_V2.9: ARCH.FACADE_RUN (lm), ARCH.FACADE (m2), FIN.EXT.FINISH (held without a specification)",
  "ARCH_TAKEOFF_V3.0 passage piece (merged b1a6d6d)",
  "the external finish is held without a stated specification; facade m2 held", "yes",
  codes=("ARCH.FACADE_RUN", "ARCH.FACADE", "FIN.EXT.FINISH"))
f("B4-05", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "spatter dash not measured", "no")
f("B4-06", "PARTIAL",
  ["engine/source/arch_measure.py:639-681 FIN.PAINT per room face",
   "engine/source/surface_ledger.py:155 WALLS_ABOVE_TILE: in wet rooms paint only above the tile"],
  "ARCH_TAKEOFF_V2.9: FIN.PAINT", "none",
  "every development-villa paint line held (height) or not applicable (wet rooms tiled full height)", "yes",
  codes=("FIN.PAINT",))
f("B4-07", "PARTIAL",
  ["tools/urban_boq_m9.py:1274 _v29_facade(): FIN.EXT.FINISH line per floor, held without a specification"],
  "ARCH_TAKEOFF_V2.9: FIN.EXT.FINISH (held)", "ARCH_TAKEOFF_V3.0 passage piece (merged b1a6d6d, run length only)",
  "no specification read; the line is always held", "yes", codes=("FIN.EXT.FINISH",))
f("B4-08", "PARTIAL",
  ["engine/source/arch_v28.py:734 window_strip_lines(): UP-REVEAL-001 window reveals = jambs 2 x measured strip depth x "
   "the window's height inside the plaster band + head soffit depth x width where wall remains above; emitted as "
   "FIN.PLASTER element 'window reveals' PROVISIONAL (:816 'window reveals') and the internal sill surface as ARCH.WINDOW_REVEAL",
   "tools/urban_boq_m9.py:720 window_strip_lines(): the call in every method from ARCH_TAKEOFF_V2.8, so in the released V2.9 (run file "
   "WINDOW_REVEALS.json); commit 789d1a6 (Phase 2B-9, V2.8)",
   "tests/m9_p2b9/test_p2b9_openings.py:101 'window reveals' / :148 test_example1_reveals_and_sill_surface() (worked example: reveals and sill surface; a window without "
   "sill / schedule held BLOCKED_RFI, :91 ARCH.WINDOW_REVEAL)",
   "development villa released run: 27 ARCH.WINDOW_REVEAL lines, all BLOCKED_RFI "
   "(WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED: no window reaches an established sill and height), so "
   "WINDOW_REVEALS.json has 0 reveal records and no reveal plaster line is released",
   "engine/source/opening_reveals.py:46 passage_reveals() (door / passage jambs and soffit, OPENING_REVEAL_POLICY_V2) "
   "is read by no arch method"],
  REL + ": FIN.PLASTER 'window reveals' (where sill, height and plaster height are established) and ARCH.WINDOW_REVEAL "
  "(sill surface)", "same in every later method (V2.10 .. V3.0)",
  "every development-villa window held (sill / height not established), so 0 m2 released and the 27 held lines carry "
  "no range; door and passage reveals not measured by any method; returns are measured only as wall (V2.8 return "
  "stubs inside the wall faces), never as their own line; external reveals listed as geometry, not finish; census gap: "
  "no item code is mapped to B4-08", "yes", codes=("ARCH.WINDOW_REVEAL",),
  note="1.0.0 and r1 said NOT_IMPLEMENTED; r1 read ARCH.WINDOW_REVEAL as geometry only and missed the V2.8 reveal "
       "plaster path; raised on the verifier's T-130 r1 finding")
f("B4-09", "IMPLEMENTED_NOT_INTEGRATED", ["engine/source/corner_bead.py exists (research engine, read by no method)"],
  "none", "none", "not in any method", "no")
f("B4-10", "IMPLEMENTED_NOT_INTEGRATED", ["engine/finishes_rules.py exists (idle arithmetic, read by no method)"],
  "none", "none", "not in any method", "no")
f("B4-11", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "cladding not measured", "no")

f("B5-01", "PARTIAL",
  ["engine/source/arch_measure.py:418 FIN.CEILING per room (physical ceiling area, no material)",
   "engine/source/arch_measure.py:337 'stairwell ceiling'; :434 'ceiling over void'",
   "defect O-P8-02 (by design): every ceiling line is PROVISIONAL, the ceiling type is not in a plan"],
  "ARCH_TAKEOFF_V2.9: FIN.CEILING", "same",
  "ceiling material / type (BLOCKED_BY_SOURCE: RCP); ceilings over outside air (owner Q-68)", "yes",
  codes=("FIN.CEILING",), note="1.0.0 said NOT_IMPLEMENTED; the released run quantifies it")
for c, src in (("B5-02", "RCP, spec"), ("B5-03", "RCP"), ("B5-04", "RCP, sections"), ("B5-05", "RCP")):
    f(c, "BLOCKED_BY_SOURCE", [NONE_EMITTED], "none", "none", f"needs {src}", "no")

f("B6-01", "PARTIAL",
  ["engine/source/arch_measure.py:698-755 ARCH.DOOR: one pcs line per jambed opening (ARCH.DOOR / WINDOW / PASSAGE)",
   "tools/urban_boq_m9.py:2589 _v21_doors(): door counts replaced by the owner door classes",
   "engine/source/arch_v29.py:277 curved_openings(): curved wall openings read as openings",
   "commit c564481 (T-077 opening omission guard), 2dee954 (T-082 heights from vector PDF elevations): read by no "
   "released method"],
  "ARCH_TAKEOFF_V2.9: ARCH.WINDOW, ARCH.PASSAGE, DOOR.* (ARCH.DOOR replaced by the door classes)", "same",
  "opening heights and m2 (B6-02..04)", "yes",
  codes=("ARCH.DOOR", "ARCH.WINDOW", "ARCH.PASSAGE", "DOOR.INTERNAL.PVC", "DOOR.EXTERNAL.ALUMINIUM",
         "DOOR.MAIN_ENTRANCE"))
f("B6-02", "PARTIAL",
  ["engine/source/door_model.py:54 DOOR.INTERNAL.PVC class (owner door classes 2026-10-13)",
   "tools/urban_boq_m9.py:2589 _v21_doors() releases the class count",
   "commit 5f07bf0 (T-078 door / window m2 from printed dimensions): engine/source/opening_area.py:304 measure() "
   "read only by engine/source/opening_height_pdf.py, by no method"],
  "ARCH_TAKEOFF_V2.9: DOOR.INTERNAL.PVC (pcs)", "same",
  "door m2 not released (no printed height wired); census gap: DOOR.* are counted under B6-01 only", "yes",
  codes=("DOOR.INTERNAL.PVC",), note="1.0.0 said NOT_IMPLEMENTED; the released run counts the class")
f("B6-03", "PARTIAL",
  ["engine/source/door_model.py:54 DOOR.EXTERNAL.ALUMINIUM / DOOR.MAIN_ENTRANCE classes",
   "tools/urban_boq_m9.py:2589 _v21_doors()"],
  "ARCH_TAKEOFF_V2.9: DOOR.EXTERNAL.ALUMINIUM, DOOR.MAIN_ENTRANCE (pcs)", "same",
  "steel doors not a class; m2 not released; census gap as B6-02", "yes",
  codes=("DOOR.EXTERNAL.ALUMINIUM", "DOOR.MAIN_ENTRANCE"))
f("B6-04", "PARTIAL",
  ["engine/source/arch_measure.py:698 ARCH.WINDOW count",
   "engine/source/arch_v28.py:766 ARCH.WINDOW_REVEAL: window strip from the opening schedule (width, height, sill)",
   "engine/source/arch_v29.py:277 curved_openings(): curved glazing as openings",
   "commit 5f07bf0 (T-078): window m2 from printed dimensions, read by no method"],
  "ARCH_TAKEOFF_V2.9: ARCH.WINDOW (pcs)", "same",
  "window m2 not released (the freelancer's m2 line is unit-refused); census gap as B6-02", "yes",
  codes=("ARCH.WINDOW",))
f("B6-05", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "shutters not measured", "no")
f("B6-06", "EXPERIMENTAL", ["engine/elevator_marble.py exists (round 6 research, read by no method)"],
  "none", "none", "not in any method", "no")
f("B6-07", "EXPERIMENTAL", ["engine/elevator_marble.py exists (round 6 research, read by no method)"],
  "none", "none", "not in any method", "no")

f("B7-01", "PARTIAL",
  ["engine/source/arch_measure.py:876 _stair_lines() per drawn flight; :930 FIN.STAIR.FLIGHT",
   "engine/source/arch_measure.py:829 _seen_below(): a flight seen below the cut is not measured again",
   "commit 1513f1d (T-129, verifier run 46): the first -> second floor lower flight is counted again on the second-"
   "floor plan (+3.45 m2 tread marble, +11.5 lm steps)",
   "commit 05e2eab (T-135 STAIR_FLIGHT_ONCE_V1, verifier merge): engine/source/stair_flight_once_v1.py:180 "
   "flights_once() measures each flight once; read by no method"],
  "ARCH_TAKEOFF_V2.9: FIN.STAIR.FLIGHT (held) and the stair finish lines", "none",
  "a flight drawn on two plans counted twice (verifier-confirmed); flight length held; STAIR_FLIGHT_ONCE_V1 waits "
  "(" + W + "T-135" + T133 + ")", "yes",
  codes=("FIN.STAIR.FLIGHT",))
f("B7-02", "PARTIAL",
  ["engine/source/arch_measure.py:899 FIN.MARBLE.TREAD from the tread polygons",
   "commit 1513f1d (T-129, verifier run 46): +3.45 m2 counted twice on the second floor",
   "commit 05e2eab (T-135 STAIR_FLIGHT_ONCE_V1): engine/source/stair_flight_once_v1.py:180 flights_once(), read by no method"],
  "ARCH_TAKEOFF_V2.9: FIN.MARBLE.TREAD", "none",
  "double-counted flight; round stair held (owner Q-50); STAIR_FLIGHT_ONCE_V1 waits (" + W + "T-135" + T133 + ")",
  "yes", codes=("FIN.MARBLE.TREAD",), note="1.0.0 said EXPERIMENTAL; the released run quantifies it")
f("B7-03", "PARTIAL",
  ["engine/source/arch_measure.py:922 FIN.MARBLE.RISER / :950 FIN.MARBLE.RISER (UP-STAIR-003), held without the tread thickness"],
  "ARCH_TAKEOFF_V2.9: FIN.MARBLE.RISER (held)", "none", "tread marble thickness not given: every line held", "yes",
  codes=("FIN.MARBLE.RISER",))
f("B7-04", "PARTIAL",
  ["engine/source/arch_measure.py:965 _landing(): FIN.MARBLE.LANDING as a bounded range",
   "commit 4ae3a68 (T-122) and 1513f1d (T-129): landings by hand, counted once (research, verifier runs 45 / 46)"],
  "ARCH_TAKEOFF_V2.9: FIN.MARBLE.LANDING (bounded)", "none",
  "landing polygons not settled (owner Q-66 B, Q-70 A); the hand result is not wired (" + W + "T-122, T-129" + T133
  + ")", "yes",
  codes=("FIN.MARBLE.LANDING",))
f("B7-05", "EXPERIMENTAL", ["engine/stair_assembly.py exists (NOSING_LENGTH, research, read by no method)"],
  "none", "none", "not in any method", "no")
f("B7-06", "PARTIAL",
  ["engine/source/arch_measure.py:902 FIN.STAIR.STEP_LM: sum of the physical step widths (owner Q-19)",
   "commit 05e2eab (T-135 STAIR_FLIGHT_ONCE_V1): engine/source/stair_flight_once_v1.py:180 flights_once(), read by no method"],
  "ARCH_TAKEOFF_V2.9: FIN.STAIR.STEP_LM", "none",
  "same double count as B7-02 (T-129); STAIR_FLIGHT_ONCE_V1 waits (" + W + "T-135" + T133 + ")", "yes",
  codes=("FIN.STAIR.STEP_LM",))
f("B7-07", "IMPLEMENTED_NOT_INTEGRATED", ["engine/finishes_rules.py exists (zigzag skirting, idle arithmetic)"],
  "none", "none", "not in any method", "no")
f("B7-08", "IMPLEMENTED_NOT_INTEGRATED", ["engine/finishes_rules.py exists (sloped skirting, idle)"],
  "none", "none", "not in any method", "no")
f("B7-09", "PARTIAL",
  ["engine/source/arch_measure.py:938-954 FIN.RAILING per open side: sqrt(plan path^2 + rise^2) (UP-STAIR-012)"],
  "ARCH_TAKEOFF_V2.9: FIN.RAILING (held)", "none", "open sides not established: every development-villa line held",
  "yes", codes=("FIN.RAILING",), note="1.0.0 said NOT_IMPLEMENTED; the released route emits the line (held)")
f("B7-10", "NOT_IMPLEMENTED",
  ["FIN.HANDRAIL is defined (engine/source/boq_line.py:91 FIN.HANDRAIL) but no module emits it (grep of engine/ and tools/)"],
  "none", "none", "not measured", "no")
f("B7-11", "BLOCKED_BY_SOURCE", [NONE_EMITTED], "none", "none", "needs a specification", "no")
f("B7-12", "PARTIAL",
  ["engine/source/generic_route.py:1921 _stair_items(); :1995 STAIRS concrete in route G",
   "docs/agents SCOREBOARD (verifier, released run): stair + dome concrete compared line UNRESOLVED (owner Q-12)",
   "commit e74c182 (T-105 with T-056 STAIR_CONCRETE_V1, verifier merge): engine/source/stair_steps_concrete.py:399 "
   "measure_all() gives stair concrete flight by flight; read by no method; round stair HELD (owner Q-50 / Q-51)"],
  REL + ": STR.CONC.STAIR", "none",
  "flight-by-flight stair concrete merged but not wired; round stair and winders held; the T-111 stair ledger and "
  "STAIR_CONCRETE_V1 wait (" + W + "T-111, T-105" + T133 + ")", "yes",
  codes=("STR.CONC.STAIR",),
  note="1.0.0 said INTEGRATED_AND_TESTED; lowered: the stair line is UNRESOLVED on the development villa and the "
       "stair piece that replaces it is not wired")
f("B7-13", "NOT_IMPLEMENTED",
  [NONE_EMITTED + "; engine/source/stair_geometry.py INCLINED_WAIST_SURFACE_AREA is structural geometry, not a trade"],
  "none", "none", "no formwork trade", "no")
f("B7-14", "BLOCKED_BY_SOURCE", ["route G gives stair concrete without a bar model (coverage census B11-03)"],
  "none", "none", "needs bar details", "no")

f("B8-01", "PARTIAL",
  ["engine/source/arch_measure.py:560 FIN.WP.FLOOR per wet room",
   "engine/source/waterproofing_system.py:284 areas_from_floor() (ARCH_TAKEOFF_V2.4+ system)",
   "commit 8fcabe0 (T-010, verifier run 22): wet / dry evidence 72.12 m2 vs the released 62.773 m2 (wet rooms "
   "merged into dry zones in the released method)",
   "commit 9f14742 (T-093 ARCH_TAKEOFF_V2.11, verifier run 32); commit 2264938 (V2.13, verifier run 44: 85.62 m2 "
   "with the typed pantry zone)"],
  "ARCH_TAKEOFF_V2.9: FIN.WP.FLOOR", "ARCH_TAKEOFF_V2.11 .. V2.13",
  "the released method misses wet rooms identified by fixtures (verifier-confirmed)", "yes",
  codes=("FIN.WP.FLOOR",), note="1.0.0 said IMPLEMENTED_NOT_INTEGRATED; the released route emits the line")
f("B8-02", "PARTIAL",
  ["engine/source/arch_measure.py:571 FIN.WP.DOORWAY / :602 FIN.WP.DOORWAY per doorway",
   "engine/source/surface_ledger.py:134 FIN.WP.DOORWAY_TRANSITION by detail (bounded until the detail is chosen)",
   "engine/source/arch_v211.py:494 door_transition_lines(): one transition per door (opt-in)"],
  "ARCH_TAKEOFF_V2.9: FIN.WP.DOORWAY, FIN.WP.DOORWAY_TRANSITION (bounded)", "ARCH_TAKEOFF_V2.11 .. V2.13",
  "doorway detail not chosen: transitions bounded", "yes",
  codes=("FIN.WP.DOORWAY", "FIN.WP.DOORWAY_TRANSITION"),
  cand_codes=("FIN.WP.DOORWAY", "FIN.WP.DOORWAY_TRANSITION", "FIN.WP.DOORWAY_TRANSITION_NR"))
f("B8-03", "PARTIAL",
  ["engine/source/waterproofing_system.py:905-910 FIN.WP.WALL_UPTURN on eligible wall boundaries (UP-WP-002)",
   "engine/source/surface_ledger.py:142 FIN.WP.WALL_UPTURN: the V2.4+ ledger replaces FIN.WP.UPTURN by FIN.WP.WALL_UPTURN",
   "engine/source/arch_measure.py:615 FIN.WP.UPTURN (ARCH_TAKEOFF_V1 .. V2.3 path only)"],
  "ARCH_TAKEOFF_V2.9: FIN.WP.WALL_UPTURN", "ARCH_TAKEOFF_V2.11 .. V2.13",
  "census gap: B8-03 maps to FIN.WP.UPTURN only (engine/source/coverage_census.py:31 FIN.WP.UPTURN), so the released run reports "
  "it NOT_FOUND_IN_SOURCE although 14 wall-upturn lines are released", "yes",
  codes=("FIN.WP.WALL_UPTURN", "FIN.WP.UPTURN"),
  note="1.0.0 text '7 conflicting implementations (C01)': the released route uses one (waterproofing_system); the "
       "membrane fold versions V2..V5 lay strips, they do not re-measure the upturn area")
f("B8-04", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "shower extents and tanking height not read", "no")
f("B8-05", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/arch_v211.py:568 rolls_lines(): FIN.WP.MEMBRANE_ROLLS per wet area / roof (owner Q-49 A strips)",
   "engine/source/arch_v213.py:86 prove_q58_a(); :413 rolls_lines()",
   "commit 9f14742 (T-093 V2.11, verifier run 32: wet areas 19 rolls = hand); 54bd6a4 (T-096 V2.12, run 35); "
   "2264938 (T-120 V2.13, run 44: second-floor roof 17 rolls under Q-58 A, placement re-checked); f47ae01 (T-124 "
   "MEMBRANE_FOLD_V5)",
   "commit 967d6d5 (T-133 ARCH_TAKEOFF_V3.0.1, verifier 2026-10-21 17:40 UTC): engine/source/arch_v301.py:334 "
   "membrane_changes(): the MEMBRANE_FOLD_V5 audit is each roll line's evidence field (22 roll lines: 21 AGREES, 1 "
   "NOT_COMPARABLE); roll counts unchanged (wet 21, roofs 6 + 8 / 17); opt-in",
   "engine/source/membrane_layout.py:1 \"MEMBRANE LAYOUT\": exact roll plan per rectangular wet room in the released route; "
   "engine/source/coverage_census.py:108 QUANTIFIED: it is a procurement view, never a BOQ "
   "line (coverage census)"],
  "ARCH_TAKEOFF_V2.9: procurement roll view only (no BOQ line)",
  "ARCH_TAKEOFF_V2.11 .. V2.13; ARCH_TAKEOFF_V3.0.1 (V5 audit as evidence, merge 967d6d5)",
  "the owner strip method's roll lines are opt-in only; the coverage proof (T-137) is not attached yet", "yes",
  plan=("T-142",),
  codes=(), cand_codes=("FIN.WP.MEMBRANE_ROLLS",),
  note="1.0.0 said NOT_IMPLEMENTED (single factor)")
f("B8-06", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/arch_v211.py:227 roof_records(); :527 roof_lines(): FIN.WP.ROOF inside the parapet + "
   "FIN.WP.ROOF_UPTURN",
   "commit 4054509 (T-071 exterior spaces, verifier 2026-10-19); 9f14742 (V2.11, verifier run 32)"],
  "none (ARCH_TAKEOFF_V2.9 has no roof waterproofing line)", "ARCH_TAKEOFF_V2.11 .. V2.13",
  "opt-in only; the top roof is held", "yes", codes=(),
  cand_codes=("FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN"))
f("B8-07", "PARTIAL",
  ["engine/source/arch_measure.py:349 owner_scope (ARCH_TAKEOFF_V2.3 and later, so the released V2.9): a space typed "
   "EXTERIOR whose label is BALCONY / TERRACE / ROOF gets engine/source/owner_finish_scope.py:231 exterior_wp_lines(): "
   "FIN.WP.FLOOR element 'exterior wp_floor' PROVISIONAL over the drawn area (UP-WP-ROOF-001), the balcony upturn "
   "HELD by specification",
   "tests/m9_kb/test_kb_wp5.py:81 test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed() (drawn balcony: one PROVISIONAL membrane line 8.0 m2 in V2.3, none in V2.2) and "
   "tests/m9_kb/test_kb_finish_scope.py:190 test_balconies_get_provisional_waterproofing()",
   "engine/source/arch_v211.py:527 roof_lines(): FIN.WP.BALCONY (:537 FIN.WP.BALCONY) for a balcony label on its own exterior layer "
   "(EXTERIOR_SPACES_V1, commit a444907 T-071; V2.11 commit bfadb52), opt-in ARCH_TAKEOFF_V2.11 .. V3.0",
   "development villa: no balcony / terrace label, 0 lines in both runs (not proof of absence)"],
  REL + ": FIN.WP.FLOOR 'exterior wp_floor' (balcony drawn as a space)",
  "ARCH_TAKEOFF_V2.11 .. V3.0 (FIN.WP.BALCONY from exterior spaces)",
  "balcony upturn held by specification; planters not measured; census gap: the released balcony membrane carries "
  "FIN.WP.FLOOR, which engine/source/coverage_census.py:31 FIN.WP.FLOOR counts under B8-01; no hand check", "yes",
  codes=("FIN.WP.BALCONY",),
  note="1.0.0 and r1 said NOT_IMPLEMENTED ('no item code'); the verifier found FIN.WP.BALCONY (opt-in); the released "
       "owner-scope path was found in this rework")
f("B8-08", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "below-grade waterproofing not measured", "no")
f("B8-09", "BLOCKED_BY_SOURCE", [NONE_EMITTED], "none", "none", "needs details", "no")

f("B9-01", "PARTIAL",
  ["engine/source/arch_measure.py:789 _wall_lines(): ARCH.WALL_RUN by thickness (PROVISIONAL); :811 MAS.BLOCK held",
   "tools/urban_boq_m9.py:1172 _v29_masonry(): ARCH.WALL_PANEL m2 / ARCH.WALL_VOLUME m3 from height evidence",
   "commit 2dc1657 (T-027 masonry centreline, verifier run 39) and bc21314 (T-117 vs hand): "
   "engine/source/masonry_centreline.py:212 measure() read by no method",
   "commit 79bd397 (T-103 wall metres by hand, verifier run 37)"],
  "ARCH_TAKEOFF_V2.9: ARCH.WALL_RUN, ARCH.WALL_PANEL, ARCH.WALL_VOLUME, MAS.BLOCK", "none",
  "panel m2 / m3 held (owner Q-60 height not wired); block type per wall (Q-65); census gap: B9-01 maps to MAS.BLOCK "
  "only", "yes", plan=("T-125", "T-108"),
  codes=("ARCH.WALL_RUN", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME", "MAS.BLOCK"),
  note="1.0.0 said EXPERIMENTAL (qs_core.masonry research)")
f("B9-02", "PARTIAL",
  ["engine/source/generic_route.py:2030 _lintel_items(): route G lintels over the jambed openings of the architectural "
   "plans, bound to the PRINTED lintel schedule by opening width; no schedule, no lintel line",
   "tests/lintels_s8_6/test_s8_6_package.py and tests/lintels_s8_6a/test_s8_6a_package.py (frozen S8.6 packages)",
   "development villa released run: 0 STR.CONC.LINTEL lines; route G family coverage LINTELS = NO_EVIDENCE_FOUND "
   "('not proof of absence'), while the same run counts 27 windows, 17 doors and 11 passages; no hand check of "
   "lintels exists"],
  REL + ": STR.CONC.LINTEL (only with a printed lintel schedule)", "same in every later method",
  "with no printed lintel schedule (the development villa) every opening's lintel is unanswered (family "
  "NOT_FOUND_IN_SOURCE, no held line per opening); no lintel hand check on any villa", "yes",
  codes=("STR.CONC.LINTEL",),
  note="1.0.0 and r1 said INTEGRATED_AND_TESTED; lowered on the verifier's T-130 r1 finding: no released line and no "
       "independent check on the development villa")
f("B9-03", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "mesh at joints not measured", "no")
f("B9-04", "NOT_IMPLEMENTED",
  [NONE_EMITTED + "; block mortar from the mix is QUEUED (T-115); finish_materials_table.py covers tile beds only"],
  "none", "none", "block mortar / glue not measured", "no")
f("B9-05", "PARTIAL", ["M8 parapet bound (RC 0..high) in route G family coverage (PARAPETS, B10-12)"],
  "none as a block line", "none", "block parapets not measured (owner Q-65 block type)", "no")

f("B10-01", "PARTIAL",
  ["engine/source/generic_route.py:1374 _blinding_items(); :1448 PLAIN_CONCRETE in route G",
   "commit 5fe31ca (T-100 by hand, verifier run 40): blinding scope by member family differs from route G",
   "commit cd34bd0 (T-126 route G scope V1, verifier run 46): engine/source/route_g_scope_v1.py:276 "
   "blinding_scope(), read by no released method",
   "commit 967d6d5 (T-133 ARCH_TAKEOFF_V3.0.1, verifier 2026-10-21 17:40 UTC): engine/source/arch_v301.py:141 "
   "scope_changes(): blinding by member family in the opt-in candidate, footings 15.179 m3 released (verifier hand "
   "15.213, -0.2 %) + separate HELD lines F10 0.480 .. 0.590, under ground beams 5.724 .. 9.423, under straps 0.772 "
   "m3, never summed; verifier defect D3: both HELD lower bounds exceed the hand value by more than 1 % (5.724 vs "
   "5.189, 0.772 vs 0.670), the lines stay HELD"],
  REL + ": STR.CONC.BLINDING", "ARCH_TAKEOFF_V3.0.1 route G scope piece (merge 967d6d5)",
  "released configuration: one bounded line only; the member-family scope is wired only in the opt-in V3.0.1; the "
  "HELD lower bounds of D3 not explained", "yes",
  codes=("STR.CONC.BLINDING",),
  note="1.0.0 said INTEGRATED_AND_TESTED; lowered on the verifier's T-100 / T-126 findings")
f("B10-02", "PARTIAL",
  ["engine/source/generic_route.py:509 FOOTINGS concrete in route G",
   "engine/source/generic_route.py:542 FOOTING_LABEL_CONFLICT: a footing labelled with two types and no outline is "
   "released PROVISIONAL at the convention's choice (LARGER, support CONVENTION_ONLY); on the development villa the "
   "combined footing labelled F10 + F",
   "commit cd34bd0 (T-126 ROUTE_G_SCOPE_V1, verifier run 46): engine/source/route_g_scope_v1.py:321 "
   "FOOTING_HELD_OR_IN_CONFLICT: the same footing is HELD under owner Q-31 C (its blinding follows it) while the "
   "released route releases it at the larger type; read only by the opt-in ARCH_TAKEOFF_V3.0.1 (merge 967d6d5, "
   "blinding lines only), not by the released configuration: an unwired verified correction",
   "commit 9671133 (T-060 CONCRETE_LEDGER_V2, verifier merge): engine/source/concrete_ledger_v2.py:296 _band(): the "
   "footing / boundary-wall edge band (owner Q-28) stays HELD until its member type is identified with sheet evidence "
   "(:53 MEMBER_TYPES, owner Q-12); read by no method: an unwired verified correction",
   "commit 8774071 (T-058 strip guard): footing strip pieces read by no method"],
  REL + ": STR.CONC.FOOTING", "ARCH_TAKEOFF_V3.0.1 route G scope piece (blinding of the conflict footing HELD)",
  "two verified corrections are not wired into the released route: the conflict footing F10 + F HELD under owner "
  "Q-31 C (T-126, released by route G at the larger type) and the footing edge band HELD under owner Q-28 (T-060); "
  "the compared footing line stays UNRESOLVED (owner Q-12, member type of the boundary-wall footing)", "yes",
  codes=("STR.CONC.FOOTING",),
  note="1.0.0, r1 and r2 said INTEGRATED_AND_TESTED; lowered on the verifier's T-130 r2 finding (2026-10-21 16:45 UTC, "
       "run session_01F2oCdgDYGC1oK392rb5Dv7): the registry's own INTEGRATED_AND_TESTED definition excludes a path "
       "touched by an unwired verified correction (merges 9671133 and cd34bd0) or an UNRESOLVED compared line (Q-12)")
f("B10-03", "PARTIAL", ["engine/source/generic_route.py:1268 _neck_items(); :1295 FOUNDATION necks (family COLUMNS)"],
  REL + ": STR.CONC.NECK", "none", "neck height bounded from printed levels", "yes", codes=("STR.CONC.NECK",))
f("B10-04", "PARTIAL",
  ["engine/source/generic_route.py:160 _straps(); :769 GROUND_BEAMS in route G",
   "commit c874c7b (T-073 plot-edge members, verifier run 33): straps 3.390 m3 measured, ENGINE_RIGHT; wired in "
   "ARCH_TAKEOFF_V3.0 (T-131)",
   "commit 6ab7719 (T-141 GROUND_SYSTEM_SPANS_V2, verifier 2026-10-21 18:40 UTC): "
   "engine/source/ground_system_spans_v2.py:343 split_ground_beams() / :507 measure_straps(): spans re-measured "
   "(145/7CA 1.900 m, 109/7CB 4.400 + 4.400 + 2.700 m), read by no method"],
  REL + ": STR.CONC.STRAP, STR.CONC.GROUND_BEAM", "ARCH_TAKEOFF_V3.0 strap piece (merged b1a6d6d)",
  "every development-villa ground-beam line bounded; band held (owner Q-28)", "yes",
  codes=("STR.CONC.STRAP", "STR.CONC.GROUND_BEAM"),
  note="1.0.0 said INTEGRATED_AND_TESTED; lowered: the released route releases no ground-beam quantity on the "
       "development villa")
f("B10-05", "PARTIAL", ["engine/source/generic_route.py:1080 GROUND_SLAB / SLABS: the family of the slab faces (:1095-1214 CONCRETE items) in route G"],
  REL + ": STR.CONC.GROUND_SLAB", "none", "two pieces bounded", "yes", codes=("STR.CONC.GROUND_SLAB",))
f("B10-06", "PARTIAL",
  ["engine/source/generic_route.py:689 COLUMNS concrete in route G",
   "commit 5fe31ca (T-100, verifier run 40): columns at the full storey interval 34.446 m3 vs 36.711 m3 from the typed "
   "values: 5 columns no upper slab plan draws (HAND_RIGHT)",
   "commit b87f4d6 (T-075 column schedule text rows), 8ceeeb2 (T-064 project data file), cd34bd0 (T-126 "
   "engine/source/route_g_scope_v1.py:161 column_scope()): read by no released method",
   "commit 967d6d5 (T-133 ARCH_TAKEOFF_V3.0.1, verifier 2026-10-21 17:40 UTC): engine/source/arch_v301.py:141 "
   "scope_changes(): columns above the necks 36.714 -> 34.446 m3, 5 undrawn pieces NOT_APPLICABLE_WITH_EVIDENCE "
   "(2.268 m3, re-confirmed by the verifier on the structural drawing); opt-in; verifier defect D1: the committed "
   "runner omits --profile"],
  REL + ": STR.CONC.COLUMN", "ARCH_TAKEOFF_V3.0.1 route G scope piece (merge 967d6d5)",
  "every development-villa column line BLOCKED_RFI (no machine-read section); typed values not wired", "yes",
  plan=("T-119",), codes=("STR.CONC.COLUMN",),
  note="1.0.0 said INTEGRATED_AND_TESTED; lowered: no column quantity is released on the development villa and the "
       "verifier found phantom columns in the typed path")
f("B10-07", "PARTIAL",
  ["engine/source/generic_route.py:834 BEAMS family of the beam bands (:856 CONCRETE items) concrete in route G",
   "commit cb4a66f (T-085 beam binding V2, verifier run 32): about +4.30 m3 of beam concrete once wired; read by "
   "no method",
   "commit 575df66 (T-110 beam member register, verifier run 45, research); owner Q-61 C member by member",
   "commit e74c182 (T-105 with T-097 CONCRETE_LEDGER_V3, verifier merge): engine/source/concrete_ledger_v3.py:418 "
   "measure() / :501 apply() bind the held spans; read by no released method"],
  REL + ": STR.CONC.BEAM", "none",
  "24 spans bounded; beam binding V2 / concrete ledger V3 merged but not wired (" + W + "T-105, T-102" + T133 + ")",
  "yes", codes=("STR.CONC.BEAM",),
  note="1.0.0 said INTEGRATED_AND_TESTED; lowered: spans held and a verified binding correction not wired")
f("B10-08", "PARTIAL",
  ["engine/source/generic_route.py:1080 SLABS: the family of the slab faces (:1095-1214 CONCRETE items) concrete in route G",
   "development villa released run: 76 STR.CONC.SLAB lines, 75 released 61.551 m3 + 1 BOUNDED_EXPOSURE 2.740 m3 "
   "held (the dome opening and ring face, which the slab hand ledger reads as not slab, owner Q-44 A)",
   "slab panel-by-panel hand ledger (T-139) REJECTED by the verifier 2026-10-21 16:45 UTC (copied note text, wrong "
   "dome-detail page; 3 panels re-measured 0.0 / 0.05 / 0.0 %): no merged slab hand check yet",
   "commit d0b91a4 (T-145 slab-check leftovers, verifier 2026-10-21 16:45 UTC, research): CB5 span 2 is beam "
   "(0.296 m3), not slab"],
  REL + ": STR.CONC.SLAB", "none",
  "one face held on the development villa (2.740 m3, a non-slab face inside the slab family); no merged hand check "
  "(T-139 rework: 13 non-slab faces in the engine total; moving them is T-146)", "yes", plan=("T-139", "T-146"),
  codes=("STR.CONC.SLAB",),
  note="1.0.0 and r1 said INTEGRATED_AND_TESTED; lowered on the verifier's T-130 r1 finding (a held face and no merged "
       "hand check)")
f("B10-09", "PARTIAL", ["route G DOMES family (engine/source/boq_line.py:113 ROUTE_G_FAMILY)"],
  REL + ": STR.CONC.DOME", "none", "stair + dome compared concrete line UNRESOLVED on the development villa (owner Q-12)", "yes", codes=("STR.CONC.DOME",))
f("B10-10", "PARTIAL",
  ["route G POOL / WATER_TANK / LIFT families (engine/source/boq_line.py:113 ROUTE_G_FAMILY)",
   "commit 15de9c4 (T-057 pool check list), fd0d5dd (T-048 curved pool strips): read by no released method"],
  REL + ": STR.CONC.POOL, STR.CONC.TANK, STR.CONC.LIFT", "none",
  "pool compared line UNRESOLVED (owner Q-12); pool floor term FREELANCER_RIGHT (verifier 2026-10-19)", "yes",
  codes=("STR.CONC.POOL", "STR.CONC.TANK", "STR.CONC.LIFT"))
f("B10-11", "PARTIAL", ["route G BOUNDARY_WALL family (engine/source/boq_line.py:113 ROUTE_G_FAMILY)",
                        "commit c874c7b (T-073): plot-edge members separated from the band (piece)"],
  REL + ": STR.CONC.BOUNDARY_WALL", "none", "fence / boundary split not settled (owner Q-28)", "yes",
  codes=("STR.CONC.BOUNDARY_WALL",))
f("B10-12", "PARTIAL", ["route G PARAPETS family coverage: BOUNDED_NOT_MEASURED (exposure range only)"],
  REL + ": family coverage PARAPETS (bounded)", "none", "RC parapets not measured", "yes",
  codes=("STR.CONC.PARAPET",))
f("B10-13", "IMPLEMENTED_NOT_INTEGRATED",
  ["engine/source/struct_n10.py:184 formwork(): contact faces per route G register row (slab soffit MEASURED, beam "
   "soffit MEASURED, beam sides CONDITIONAL on the schedule depth basis FW-D2, column sides UPPER_BOUND, footing / "
   "ground-beam sides CONDITIONAL FORMED / EARTH_CAST FW-D1, stairs / necks / lintels HELD); alternatives never summed",
   "tools/struct_n10.py:40 build(): standalone tool, writes FORMWORK.json / FORMWORK_FACES.csv; no method imports it",
   "commit 40f3184 (Structural N10); tests/m9_n10/test_n10_structural.py:45 test_hand_truth_faces() / :58 "
   "test_alternatives_are_never_summed_and_held_is_never_zero() / :158 test_formwork_matches_the_design() (hand truth faces, held never "
   "zero, synthetic villas)",
   "development villa (" + "tool run on the released route G registers, head 0dec24c): slab soffit 379.041 m2, beam "
   "soffit 99.123 m2, beam sides 337.405 (TOTAL) or 458.025 m2 (BELOW_SLAB), footing sides 93.260 m2 if FORMED or 0 if "
   "EARTH_CAST, ground-beam sides 10.581 m2 FORMED (3 rows only); 311 faces HELD (columns 118, slabs 76 edges, ground "
   "beams 59, ground slab 25, beams 24, others 9)"],
  "none", "none (standalone tool tools/struct_n10.py)",
  "not in any method or BOQ line; owner conventions FW-D1 .. FW-D4 open; slab edges and column-beam framing not in the "
  "register; stair formwork held (B7-13); no hand check", "no",
  note="1.0.0 and r1 said NOT_IMPLEMENTED; raised on the verifier's T-130 r1 finding")

f("B11-01", "PARTIAL",
  ["route G bar models: engine/source/generic_route.py:1838 _footing_bars() footings, :1779 _gb_bars() ground beams, :2251 _beam_bars() beams, :2297 _slab_bars() slabs",
   "engine/source/boq_line.py:327 STR.REBAR for every REINFORCEMENT item",
   "commit 6d532c5 (T-136 FOOTING_REBAR_POPULATION_V1, verifier merge): "
   "engine/source/footing_rebar_population_v1.py:280 run(): footing steel by bar population, read by no method",
   "commit 8a22eec (T-148 column steel by bar population, verifier 2026-10-21 18:40 UTC, research only): hand ledger, "
   "no code"],
  REL + ": STR.REBAR (PROVISIONAL bar models)", "none",
  "bar population merged for footings only and not wired (T-136; five per-metre footings HELD on owner Q-71); "
  "columns / ground beams by hand only (T-148 / T-138 r2); 30 lines held", "yes", plan=("T-142", "T-151"),
  codes=("STR.REBAR",))
f("B11-02", "PARTIAL", ["engine/source/bbs_optimiser.py exists (route G, partial)"],
  "none as a BOQ line", "none", "no bar-mark schedule output", "no")
f("B11-03", "BLOCKED_BY_SOURCE",
  ["coverage census of the released run: MISSING_DATA, concrete lines of these families carry no bar model"],
  "none", "none", "needs bar details", "no")
f("B11-04", "IMPLEMENTED_NOT_INTEGRATED", ["URBAN-REBAR-NET-AND-PROCUREMENT@v1 (research)"],
  "none", "none", "not in any method", "no")

f("B12-01", "EXPERIMENTAL",
  ["engine/sanitary_source.py exists (research); the fixture reading feeds only the wet / dry evidence of "
   "ARCH_TAKEOFF_V2.11+ (engine/source/arch_v211.py:105 wet_classes()), never a fixture count line"],
  "none", "none", "no fixture count line", "no")
for c, src in (("B12-02", "MEP plans"), ("B12-03", "electrical plans"), ("B12-04", "HVAC plans"),
               ("B12-05", "LV plans")):
    f(c, "BLOCKED_BY_SOURCE", [NONE_EMITTED], "none", "none", f"needs {src}", "no")
f("B13-01", "NOT_IMPLEMENTED",
  [NONE_EMITTED + "; roof screed held in engine/source/finish_materials_table.py (owner Q-41, thickness not given)"],
  "none", "none", "roof build-up not measured", "no")
f("B13-02", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "paving not measured", "no")
f("B13-03", "BLOCKED_BY_SOURCE", [NONE_EMITTED], "none", "none", "needs a landscape plan", "no")
f("B13-04", "NOT_IMPLEMENTED", [NONE_EMITTED], "none", "none", "fencing not measured", "no")
for c, src in (("B13-05", "details"), ("B13-06", "interior drawings"), ("B13-07", "details")):
    f(c, "BLOCKED_BY_SOURCE", [NONE_EMITTED], "none", "none", f"needs {src}", "no")

# ---------------------------------------------------------------- item codes and names (r2: the verifier's NEW test)
# every canonical item code an engine module or the released driver writes -> the ONE family whose lines it is;
# codes that are a register or a label, not a family line, are listed apart with the reason
ITEM_OWNER = {
    "STR.CONC.BLINDING": "B10-01", "STR.CONC.FOOTING": "B10-02", "STR.CONC.NECK": "B10-03",
    "STR.CONC.STRAP": "B10-04", "STR.CONC.GROUND_BEAM": "B10-04", "STR.CONC.GROUND_SLAB": "B10-05",
    "STR.CONC.COLUMN": "B10-06", "STR.CONC.BEAM": "B10-07", "STR.CONC.SLAB": "B10-08", "STR.CONC.DOME": "B10-09",
    "STR.CONC.POOL": "B10-10", "STR.CONC.TANK": "B10-10", "STR.CONC.LIFT": "B10-10",
    "STR.CONC.BOUNDARY_WALL": "B10-11", "STR.CONC.PARAPET": "B10-12", "STR.CONC.STAIR": "B7-12",
    "STR.CONC.LINTEL": "B9-02", "STR.REBAR": "B11-01",
    "ARCH.SPACE": "B2-02", "FIN.FLOOR.PORCELAIN": "B3-01", "FIN.FLOOR.WET_TILE": "B3-02",
    "FIN.MARBLE.THRESHOLD": "B3-04", "ARCH.THRESHOLD": "B3-04", "FIN.SKIRTING": "B3-06",
    "FIN.WALL.TILE": "B4-01", "FIN.PLASTER": "B4-03", "FIN.PAINT": "B4-06",
    "ARCH.FACADE": "B4-07", "ARCH.FACADE_RUN": "B4-07", "FIN.EXT.FINISH": "B4-07", "ARCH.WINDOW_REVEAL": "B4-08",
    "FIN.CEILING": "B5-01",
    "ARCH.DOOR": "B6-01", "ARCH.PASSAGE": "B6-01", "DOOR.INTERNAL.PVC": "B6-02", "DOOR.EXTERNAL.ALUMINIUM": "B6-03",
    "DOOR.MAIN_ENTRANCE": "B6-03", "ARCH.WINDOW": "B6-04",
    "FIN.STAIR.FLIGHT": "B7-01", "FIN.MARBLE.TREAD": "B7-02", "FIN.MARBLE.RISER": "B7-03",
    "FIN.MARBLE.LANDING": "B7-04", "FIN.STAIR.STEP_LM": "B7-06", "FIN.RAILING": "B7-09", "FIN.HANDRAIL": "B7-10",
    "FIN.WP.FLOOR": "B8-01", "FIN.WP.DOORWAY": "B8-02", "FIN.WP.DOORWAY_TRANSITION": "B8-02",
    "FIN.WP.DOORWAY_TRANSITION_NR": "B8-02", "FIN.WP.THRESHOLD": "B8-02",
    "FIN.WP.UPTURN": "B8-03", "FIN.WP.WALL_UPTURN": "B8-03", "FIN.WP.TERMINATION": "B8-03",
    "FIN.WP.PENETRATION": "B8-01", "FIN.WP.MEMBRANE_ROLLS": "B8-05", "FIN.WP.DETAILING": "B8-05",
    "FIN.WP.ROOF": "B8-06", "FIN.WP.ROOF_UPTURN": "B8-06", "FIN.WP.BALCONY": "B8-07",
    "ARCH.WALL_RUN": "B9-01", "ARCH.WALL_PANEL": "B9-01", "ARCH.WALL_VOLUME": "B9-01", "MAS.BLOCK": "B9-01"}
NO_FAMILY = {
    "ARCH.EXTERIOR": "the area of an exterior space (garden, court, roof) as a register line; its waterproofing is "
                     "FIN.WP.* (B8-06 / B8-07) and it carries no finish of its own",
    "STR.CONC.OTHER": "declared in the item master (engine/source/boq_line.py) for a route G family outside the "
                      "map; no module writes it",
    "STR.CONC": "a prefix filter, not a line code: engine/source/arch_v301.py:489 'STR.CONC' (family_totals() of the "
                "V3.0.1 blinding rows, T-133 merge 967d6d5)",
    "FIN.FLOOR": "the label of an unresolved-floor record (engine/source/arch_measure.py:378 'FIN.FLOOR'), not a line code"}
# NOT_IMPLEMENTED families: words a measuring function for the family would carry in its name; the test checks that no
# function in engine/source is so named (the r1 miss was excavation() / formwork(), which emit no item code)
NAME_TERMS = {
    "B1-01": ("site_clear",), "B1-03": ("backfill", "compaction"), "B1-04": ("disposal", "surplus_soil"),
    "B1-05": ("termite", "soil_treat"), "B1-07": ("prelim",),
    "B4-02": ("kitchen_tile", "laundry_tile", "pantry_tile", "splash"), "B4-05": ("spatter", "dash_coat"),
    "B4-11": ("cladding",), "B6-05": ("shutter",), "B7-10": ("handrail",), "B7-13": ("stair_formwork",),
    "B8-04": ("shower", "tanking"), "B8-08": ("below_grade", "basement", "tanking"),
    "B9-03": ("joint_mesh", "mesh_joint", "block_mesh"), "B9-04": ("mortar", "glue"),
    "B13-01": ("roof_screed", "insulation", "screed_to_fall", "roof_build"), "B13-02": ("paving", "interlock"),
    "B13-04": ("fenc", "gates")}

# ---------------------------------------------------------------- checks of the evidence
import re  # noqa: E402

REF = re.compile(r"((?:engine|tools|tests|research|rules|knowledge)/[\w/.]+\.(?:py|json|md))(?::(\d+)(?:-(\d+))?)?")
COMMIT = re.compile(r"\b(?:commit|merged|merge)\s+([0-9a-f]{7})\b|\b([0-9a-f]{7}) \(T-")


SHORT = re.compile(r"(?<![\w/.]):(\d+)(?:-(\d+))?")          # ':123' after a path: the same file
SYM = re.compile(r"\s*(?:/\s*)?(\"[^\"]+\"|'[^']+'|[A-Za-z_][\w.]*(?:\(\))?)")


def named_symbol(text, end):
    """r3: the symbol a citation names right after it: name(), a dotted / underscored name, an UPPER name or a quoted
    string; None when the next word is prose (then the citation names nothing and is refused)"""
    m = SYM.match(text, end)
    if not m:
        return None
    t = m.group(1)
    if t[0] in "\"'":
        return t[1:-1]
    t = t.rstrip(".")
    if t.endswith("()"):
        return t[:-2]
    return t if ("_" in t or "." in t or (t.isupper() and len(t) > 1)) else None


def citations(text):
    """every line citation of a text: (path, first, last, symbol); ':N' binds to the last full path before it"""
    full = [(m.start(), m.end(), m.group(1), m.group(2), m.group(3)) for m in REF.finditer(text)]
    short = [(m.start(), m.end(), None, m.group(1), m.group(2)) for m in SHORT.finditer(text)
             if not any(a <= m.start() < b for a, b, *_ in full)]
    last = None
    for st, en, path, a, b in sorted(full + short):
        last = path or last
        if a is not None:
            yield last, int(a), int(b or a), named_symbol(text, en)


def citation_problem(path, a, b, sym):
    p = REPO / path
    if not p.exists():
        return "no such file"
    lines = p.read_text(encoding="utf-8").splitlines()
    if a < 1 or b > len(lines) or a > b:
        return "line out of range"
    if sym is None:
        return "names no symbol"
    return None if sym in "\n".join(lines[a - 1:max(b, a + 2)]) else f"{sym!r} not on the cited line or the next 2"


def check_refs(text):
    bad = []
    for m in REF.finditer(text):
        if not (REPO / m.group(1)).exists():
            bad.append(m.group(0))
    bad += [f"{p}:{a} {why}" for p, a, b, sym in citations(text) if (why := citation_problem(p, a, b, sym))]
    for m in re.finditer(r"\b([0-9a-f]{7})\b", text):
        h = m.group(1)
        if h.isdigit():
            continue
        r = subprocess.run(["git", "-C", str(REPO), "cat-file", "-t", h], capture_output=True, text=True)
        if r.returncode and h != "33f1da2" and h != "7975663":
            bad.append(h)
    return bad


def run_codes(run):
    return summ.summ(run)


RUN_COMMIT = "0dec24c"            # the engine commit of the two development-villa runs (r2)
REUSE = RUNS.suffix == ".json"
if REUSE:
    # r3: the runs are not repeated; the figures come from the previous build of this file, allowed only when no file
    # of the released path changed since the runs (git diff RUN_COMMIT..HEAD); new opt-in modules are listed apart
    PREV = json.loads(RUNS.read_text(encoding="utf-8"))
    changed = subprocess.check_output(["git", "-C", str(REPO), "diff", "--name-only", RUN_COMMIT, "HEAD", "--",
                                       "engine", "tools", "rules", "knowledge", "data"], text=True).split()
    added = set(subprocess.check_output(["git", "-C", str(REPO), "diff", "--name-only", "--diff-filter=A",
                                         RUN_COMMIT, "HEAD", "--", "engine", "tools"], text=True).split())
    OWN = {"rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json", "rules/RULES_MANIFEST.json", "tools/m9_rules_manifest.py"}
    MODIFIED = sorted(set(changed) - added - OWN)
    # the only modified engine file since the runs: tools/urban_boq_m9.py, where T-133 (967d6d5) added the opt-in
    # ARCH_TAKEOFF_V3.0.1 flag (V301 / CANDIDATE_EXTENSIONS, cmd_arch branch taken only for that method)
    assert MODIFIED == ["tools/urban_boq_m9.py"], MODIFIED
    PREV_VILLA = {x["code"]: x["development_villa"] for x in PREV["families"]}
    PREV_SEEN = PREV["run_evidence"]["item_codes_seen"]
    REUSE_NOTE = (f"r3: runs NOT repeated; figures reused from the r2 build (runs on {RUN_COMMIT}); since then "
                  f"{len(added)} engine / tools files were added ({', '.join(sorted(added))}: opt-in, read by no "
                  "released method) and one modified: tools/urban_boq_m9.py (T-133 967d6d5: the opt-in "
                  "ARCH_TAKEOFF_V3.0.1 flag; the verifier's 17:40 run found a plain V3.0 run byte-identical)")
    rel = cand = None
else:
    rel = run_codes(RUNS / "v29")
    cand = run_codes(RUNS / "facts" / "V2.13")


def snap(o, codes, run=None, fam=None):
    if o is None:                    # r3 reuse: the previous build's rows, for the same item codes only
        rows = PREV_VILLA[fam][run]
        assert {r["item_code"] for r in rows} <= set(codes), (fam, run)
        return rows
    out = []
    for k in codes:
        x = o.get(k)
        if not x:
            continue
        u = ",".join(sorted(x["unit"]))
        out.append({"item_code": k, "unit": u, "lines": x["n"], "released_lines": x["rel"],
                    "released_qty": round(x["rel_qty"], 3), "held_lines": x["held"],
                    "held_bounded_low": round(x["lo"], 3) if x["bounded"] else None,
                    "held_bounded_high": round(x["hi"], 3) if x["bounded"] else None,
                    "not_applicable_lines": x["excl"]})
    return out


fams, bad = [], {}
for old in OLD["families"]:
    a = A[old["code"]]
    b = check_refs(" ".join(a["ev"]) + " " + (a["note"] or "") + " " + a["miss"])
    if b:
        bad[old["code"]] = b
    c0, c1 = old["capability"], a["c"]
    order = OLD["capability_states"]
    rank = {s: i for i, s in enumerate(order)}
    change = "UNCHANGED" if c0 == c1 else ("RAISED" if rank[c1] < rank[c0] else "LOWERED")
    rec = {k: old[k] for k in ("code", "group", "item_en", "item_ar", "unit")}
    rec.update({
        "capability": c1, "capability_1_0_0": c0, "capability_change": change,
        "implementation": old["implementation"] if change == "UNCHANGED" and a["rd"] == "none" else a["rd"],
        "source_needed": old["source_needed"], "next_slice": old["next_slice"],
        "evidence": a["ev"], "released_method_reads": a["rd"], "opt_in_readers": a["cand"],
        "missing": a["miss"],
        "in_v3_0_candidate": a["v3"], "v3_0_planned_tasks": a["plan"],
        "development_villa": {"released_run": snap(rel, a["codes"], "released_run", old["code"]),
                              "candidate_run_v2_13": snap(cand, a["cand_codes"], "candidate_run_v2_13", old["code"])}})
    rec["item_codes"] = sorted(k for k, v in ITEM_OWNER.items() if v == old["code"])
    if a["c"] == "NOT_IMPLEMENTED":
        rec["name_terms"] = list(NAME_TERMS[old["code"]])
    if a["note"]:
        rec["note"] = a["note"]
    if change != "UNCHANGED" and not any(REF.search(e) or re.search(r"\b[0-9a-f]{7}\b", e) for e in a["ev"]):
        bad.setdefault(old["code"], []).append("status changed without a file:line or commit")
    fams.append(rec)
assert len(fams) == 99 and set(A) == {x["code"] for x in OLD["families"]}, "family set"
assert set(NAME_TERMS) == {k for k, v in A.items() if v["c"] == "NOT_IMPLEMENTED"}, "name terms per NOT_IMPLEMENTED"
assert set(ITEM_OWNER.values()) <= set(A) and not set(ITEM_OWNER) & set(NO_FAMILY), "item owner map"
if bad:
    print(json.dumps(bad, indent=1))
    sys.exit(1)

seen_rel = PREV_SEEN["released_run"] if REUSE else sorted(rel)
seen_cand = PREV_SEEN["candidate_run_v2_13"] if REUSE else sorted(cand)
doc = {
    "master": OLD["master"], "version": "1.1.0", "supersedes": "1.0.0 (kept unchanged on disk)",
    "source": f"re-derived from the code of claude/access-permissions-setup-ii24ws at {HEAD} and from runs of that "
              "code (task T-130, plan P-02); 1.0.0 was the M9A read-only audit of 8177ccf",
    "loaded_by": "nothing yet: engine/source/rule_store.py:104 _load() (rule_store.family_master()) and engine/source/coverage_census.py still read 1.0.0, so "
                 "no run, census or quantity changes with this file; adopting it is a census version of its own",
    "capability_states": OLD["capability_states"],
    "capability_definitions": {
        "INTEGRATED_AND_TESTED": "the released configuration emits BOQ lines of the family from tested code, and no "
                                 "verifier-confirmed open defect or unwired verified correction touches that path",
        "PARTIAL": "the released configuration emits lines (or a run file) of the family, but part of the scope is "
                   "missing, always held on a known input, or a verifier-confirmed defect / unwired verified "
                   "correction is open",
        "IMPLEMENTED_NOT_INTEGRATED": "merged, tested code measures the family, but only an opt-in method or a "
                                      "standalone piece reads it; the released configuration does not",
        "EXPERIMENTAL": "research code only (round / P7757 engines), read by no method",
        "BLOCKED_BY_SOURCE": "needs documents the engine does not read",
        "NOT_IMPLEMENTED": "no code measures the family"},
    "released_configuration": REL + " (the scored configuration of docs/agents/SCOREBOARD.md; ARCH_METHODS has no "
                              "default, tools/urban_boq_m9.py:67 ARCH_METHODS; the owner switches the released default)",
    "v3_0_candidate": V30 + ": ARCH_TAKEOFF_V2.13 + route G + checker-verified pieces (straps T-073, passage walls "
                      "T-109 / T-123, stair floor residue T-116); 'in_v3_0_candidate' = the family's lines are "
                      "produced by that candidate; 'v3_0_planned_tasks' = board tasks that change them next",
    "run_evidence": {
        "engine_commit": ((REUSE_NOTE + "; ") if REUSE else "") + "0dec24c (r2: both runs repeated on the working head; the released BOQ_LINES.csv is byte-identical to the r1 run on 1513f1d, the candidate again 579 lines); the N10 figures of B1-02 / B10-13 come from tools/struct_n10.py on the released run's route G registers", "python": "3.11 (project venv from requirements.txt)",
        "inputs": "the development villa's architectural and structural DXF from the private Drive folder (read-only, "
                  "never in this repository): sha256 ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4 "
                  "and 9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079 (= SOURCE_MANIFEST)",
        "released_run": "tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9 --structural <ST> --conventions "
                        "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json, no facts file: exit 0, 1455 lines, "
                        "BOQ_LINES.csv sha256 b96185d468524743e600f1992d4e4b2028193ff4a379961bc5686c9662f8c115",
        "candidate_run_v2_13": "arch_compute(method ARCH_TAKEOFF_V2.13) with the project inputs of "
                               "the T-120 runner in research/agents_t120/ (fixture reading, exterior spaces, pantry "
                               "4.50 x 3.00 m typed record): 579 lines, architectural only",
        "released_qty": "sum of measured_net over lines in MEASURED / SOURCE_DERIVED / PROVISIONAL; held lines carry "
                        "no quantity (bounded low / high summed where the line gives a range); missing is never 0",
        "item_codes_seen": {"released_run": seen_rel, "candidate_run_v2_13": seen_cand}},
    "item_code_scan": "every quoted item code in engine/source/*.py and tools/urban_boq_m9.py, except the item "
                      "master engine/source/boq_line.py and the census map engine/source/coverage_census.py, is "
                      "owned by exactly one family ('item_codes') or listed in 'item_codes_without_family'; a "
                      "NOT_IMPLEMENTED family owns no written code and no engine/source function name carries one "
                      "of its 'name_terms' (tests/t130_family_master)",
    "item_codes_without_family": NO_FAMILY,
    "census_gaps": [
        "B8-03: engine/source/coverage_census.py:31 FIN.WP.UPTURN is the only code mapped; the V2.4+ methods emit FIN.WP.WALL_UPTURN",
        "B6-02 / B6-03 / B6-04: DOOR.* and ARCH.WINDOW are counted under B6-01 only (coverage_census.py:35-36)",
        "B9-01: maps MAS.BLOCK only; ARCH.WALL_RUN / WALL_PANEL / WALL_VOLUME are not counted",
        "B3-04: FIN.MARBLE.THRESHOLD is not mapped; B2-02 / B2-03 have no entry (always NOT_RUN)",
        "B5-01, B7-02, B7-06, B8-05: the 1.0.0 capability under-states what the census itself reports QUANTIFIED",
        "B4-08: no item code is mapped; the released reveal lines are ARCH.WINDOW_REVEAL and FIN.PLASTER 'window "
        "reveals' (the latter counted under B4-03)",
        "B8-07: the released balcony membrane is FIN.WP.FLOOR 'exterior wp_floor', counted under B8-01; "
        "FIN.WP.BALCONY (V2.11+) is not mapped",
        "B1-02 / B10-13: the N10 tool writes no BOQ line, so a run always reports them NOT_IMPLEMENTED"],
    "families": fams,
}
top_bad = check_refs(" ".join(doc["census_gaps"] + [doc["loaded_by"], doc["released_configuration"]]
                               + list(doc["item_codes_without_family"].values())))
if top_bad:
    print(json.dumps({"top": top_bad}, indent=1))
    sys.exit(1)
out = REPO / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json"
out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
from collections import Counter  # noqa: E402
print(Counter(x["capability"] for x in fams), Counter(x["capability_change"] for x in fams),
      Counter(x["in_v3_0_candidate"] for x in fams))
