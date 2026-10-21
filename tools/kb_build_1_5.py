"""KNOWLEDGE REGISTRY 1.5.0 BUILDER (M9 Phase N10) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json is the frozen
1.4.0 registry (read byte for byte, never rebuilt) plus the delta of the Phase N10 program (2026-10-17), read only by
ARCH_TAKEOFF_V2.9 (and engine.source.struct_n10). Every new rule is the engine's reading of the owner program, so it
stays REQUIRES_CONFIRMATION until the owner confirms it: no interpretation is promoted to OWNER_APPROVED.

    new rules        UP-OPEN-CURVED-001 a jambed gap in a curved wall band is an opening closed on both wall faces;
                     the room ends at its own face; the width on a room is the arc of the face it meets
                     UP-MAS-HEIGHT-001 the masonry panel runs from the floor's T.O.S. to the soffit (or a beam bottom),
                     from the floor's own section or stated facts; never a finish height or floor-to-floor
                     UP-FACADE-001 the facade run is the exterior outline of the floor's wall network (openings on
                     their outer face included); its area F.F.L. to the next F.F.L. (or to the parapet top); a second
                     outline is never added; the finish is held without a specification
                     UP-FW-001 formwork contact faces from the concrete register by element, with the open conventions
                     as alternatives (never summed)
                     UP-EXC-001 excavation footprints; the volume only with stated depth and working space; backfill
                     held
    owner questions  OQ-06 .. OQ-13 (the conventions the new rules leave open)
    1.4.0 is unchanged and stays the registry of ARCH_TAKEOFF_V2.8.

    python3 -I tools/kb_build_1_5.py            write the 1.5.0 registry
    python3 -I tools/kb_build_1_5.py --check    exit 1 when the committed 1.5.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.4.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json"
D = "2026-10-17"
P = ("owner program 2026-10-17 (URBAN PROJECT AI - Phase N10: autonomous engineering development - curved geometry, "
     "architectural and structural completeness, independent proofs)")
T = "tests/m9_n10/"
C29 = "engine/source/arch_v29.py::"
CS = "engine/source/struct_n10.py::"
H = [{"version": "1.5.0", "date": D, "change": "first registry record (Phase N10)"}]
AUTH = {"kind": "OWNER", "received": D, "source": f"{P}: the workstream asks for the quantity; the convention below is "
                                                  "the engine's reading, pending the owner's confirmation"}


def rec(rule_id, title, *, purpose, scope, elements, logic, tests, code, trades, evidence=(), limitations=(),
        conflicts=(), examples=()):
    return {"rule_id": rule_id, "title": title, "kind": "ENGINEERING_RULE", "purpose": purpose, "scope": scope,
            "elements": list(elements), "locations": ["ALL"], "preconditions": [], "exceptions": [],
            "authority": AUTH, "status": "REQUIRES_CONFIRMATION", "effective_version": "1.5.0", "logic": logic,
            "required_evidence": list(evidence), "assumptions_permitted": "NONE", "conflicts": list(conflicts),
            "dependent_trades": list(trades), "tests": list(tests), "code": list(code), "examples": list(examples),
            "limitations": list(limitations), "history": H, "supersedes": [], "superseded_by": None}


NEW = [
    rec("UP-OPEN-CURVED-001", "A jambed gap in a curved wall band is an opening closed on its own wall faces",
        purpose="a curved window, door or passage ends the room at the room's own wall face (never at the glazing "
                "line) and takes the width of the face the room meets (D-P9-01, D-P9-02)",
        scope="ARCH_TAKEOFF_V2.9: curved wall bands (concentric wall-layer arcs 0.10 - 0.45 m apart)",
        elements=("WALL", "WINDOW", "DOOR", "PASSAGE"),
        logic={"opening": "both faces open over the same span (the outer face may stop up to 0.03 m further along "
                          "the arc), a radial or splayed jamb line on a wall layer at each end, sweep <= half a turn, "
                          "mid-band arc >= 0.40 m, no wall arc inside the gap",
               "kind": "DOOR (a free swing hinged within 0.30 m of a jamb end, its radius fitting the mid chord), "
                       "WINDOW (glazing arcs over half the gap), else PASSAGE",
               "closure": "an arc threshold on each wall face",
               "width": "the arc of the face the room meets (MIN_RADIUS_ARC; MAX_RADIUS_ARC when only the outer "
                        "face bounds a room); every basis (inner, mid-band, outer arc, chord) is published",
               "strips": "the strip between the face and the glazing is a reveal / sill strip, measured radially",
               "glazing_layer": "an OTHER layer whose concentric arcs glaze the jambed curved gaps (most of its "
                                "linework in wall gaps) is read as a WINDOW layer; a declared role is never changed",
               "never": ["the glazing line as the room boundary", "a gap without a jamb line at both ends read as "
                         "an opening", "a mean radius used for a face's width"]},
        trades=("FLOOR_FINISH", "PLASTER", "PAINT", "SKIRTING", "OPENINGS"),
        tests=(T + "test_n10_curved_openings.py::test_curved_window_room_ends_at_its_own_wall_face",
               T + "test_n10_curved_openings.py::test_gap_without_jamb_lines_is_not_an_opening",
               T + "test_n10_curved_openings.py::test_splayed_jamb_is_still_an_opening",
               T + "test_n10_indep_curved.py::test_v28_to_v29_curved_window_changes_are_independently_verified"),
        code=(C29 + "curved_gaps", C29 + "curved_openings", C29 + "curved_glazing_roles"),
        limitations=["ARCH_TAKEOFF_V2.9 only; earlier methods are unchanged"]),
    rec("UP-MAS-HEIGHT-001", "The masonry panel runs from the floor's structural slab top to the soffit above",
        purpose="masonry area and volume by wall thickness from an evidenced panel height, never a finish height",
        scope="ARCH_TAKEOFF_V2.9: ARCH.WALL_PANEL, ARCH.WALL_VOLUME and MAS.BLOCK",
        elements=("WALL",),
        logic={"panel": "U/S SLAB - T.O.S. of the floor's own section band (T.O.S. within 0.30 m below the F.F.L.); "
                        "or the stated facts masonry.{floor|*}.panel_height_m and floor_buildup_m",
               "beams": "a section B.O.B. level gives a beam depth: a range between the beam bottom and the soffit "
                        "(which walls carry a beam is not in the plan); without beam evidence the panel is held at "
                        "its upper bound",
               "area": "wall-mass plan area / t x panel + the wall above / below each opening (a door or passage "
                       "from the slab: its height + the build-up; a window: min(h, panel); unknown: a range)",
               "volume": "area x t; the junction pieces of different thicknesses are their own volume",
               "material": "MAS.BLOCK takes the panel only when the family's material is stated",
               "never": ["a finish height or floor-to-floor used as a masonry height", "a material inferred from a "
                         "thickness"]},
        evidence=("SECTION T.O.S. / U/S SLAB / B.O.B. levels, or stated project facts",),
        trades=("MASONRY",),
        tests=(T + "test_n10_masonry.py::test_panel_measured_with_beams_stated_absent",
               T + "test_n10_masonry.py::test_beams_not_established_hold_the_panel_at_its_upper_bound",
               T + "test_n10_masonry.py::test_no_masonry_height_without_its_evidence"),
        code=(C29 + "masonry_evidence", C29 + "masonry_takeoff")),
    rec("UP-FACADE-001", "The facade is the exterior outline of the floor's wall network, F.F.L. to the next F.F.L.",
        purpose="the exterior wall face of each floor: its run, its area and its finish",
        scope="ARCH_TAKEOFF_V2.9: ARCH.FACADE_RUN, ARCH.FACADE and FIN.EXT.FINISH",
        elements=("WALL", "WINDOW", "DOOR"),
        logic={"run": "the outer cycle of the plan topology, each opening closed on its outer wall face (the run "
                      "includes the openings); a network inside a room is an island, never a facade",
               "height": "the floor's section band: F.F.L. to the next floor's F.F.L.; above the top floor, to the "
                         "lowest parapet top; or the stated fact facade.{floor|*}.height_m",
               "deductions": "each opening on the outline: its width on the outline x its own band (a door from the "
                             "F.F.L., a window min(sill + h, H) - max(sill, 0)); unknown heights give a range",
               "outlines": "a second exterior outline is an RFI, never added; an outline around the building (a "
                           "boundary wall) holds the facade",
               "finish": "FIN.EXT.FINISH = the facade area only when the exterior finish is stated",
               "plinth": "below the lowest floor's F.F.L. down to the external ground level: an RFI",
               "never": ["a ceiling or finish height used as a facade height", "a second outline added",
                         "a finish measured without a specification"]},
        trades=("FACADE",),
        tests=(T + "test_n10_facade.py::test_facade_run_and_area_from_floor_to_floor",
               T + "test_n10_facade.py::test_second_outline_is_reported_never_added",
               T + "test_n10_facade.py::test_outline_around_the_building_holds_the_facade",
               T + "test_n10_facade.py::test_facade_run_is_independently_verified"),
        code=(C29 + "facade_outlines", C29 + "facade_evidence", C29 + "facade_takeoff"),
        limitations=["an undetected window recess on the outline is walked (its returns are in the run: D-N10-03)",
                     "set-back floors: the lower floor's exposed slab edge and parapet are not separate items"]),
    rec("UP-FW-001", "Formwork contact faces by element from the concrete register",
        purpose="the faces a form shapes, element by element, without choosing an open convention",
        scope="engine.source.struct_n10.formwork on the route G register (read only)",
        elements=("SLAB", "BEAM", "COLUMN", "FOOTING", "GROUND_BEAM"),
        logic={"SLABS": "soffit = the slab face area (MEASURED); free edges HELD; a ground slab has no soffit",
               "BEAMS": "soffit = the net plan (MEASURED); sides 2 x net length x (depth | depth - slab): CONDITIONAL",
               "COLUMNS": "perimeter x (storey height - slab thickness): UPPER_BOUND (framing beams not deducted)",
               "FOOTINGS / GROUND_BEAMS": "sides CONDITIONAL on FORMED / EARTH_CAST; base on blinding: no form",
               "other": "HELD with the reason (necks without a height, stairs, lintels, unresolved rows)",
               "never": ["conditional alternatives summed", "a held face counted as zero"]},
        trades=("FORMWORK",),
        tests=(T + "test_n10_structural.py::test_hand_truth_faces",
               T + "test_n10_structural.py::test_formwork_matches_the_design",
               T + "test_n10_structural.py::test_faces_conserve_the_route_g_concrete"),
        code=(CS + "element_faces", CS + "formwork")),
    rec("UP-EXC-001", "Excavation footprints; the volume only with stated depth and working space",
        purpose="excavation and backfill never invented from missing levels",
        scope="engine.source.struct_n10.excavation on the route G register (read only)",
        elements=("FOOTING", "GROUND_BEAM"),
        logic={"plan": "a pit per footing (L + 2 ws) x (W + 2 ws); a trench per ground beam clear length x (width + "
                       "2 ws)",
               "volume": "plan x depth when the depth (or NGL and founding level) and the working space are stated "
                         "facts; neighbouring pits are not merged (positions are not in the register): an upper "
                         "bound",
               "backfill": "held: it needs the buried concrete below ground level",
               "never": ["an excavation depth or working space assumed"]},
        evidence=("natural ground level, founding level / blinding, working space",),
        trades=("EARTHWORKS",),
        tests=(T + "test_n10_structural.py::test_excavation_is_held_without_levels_and_working_space",
               T + "test_n10_structural.py::test_excavation_with_stated_depth_and_working_space"),
        code=(CS + "excavation",)),
]


def q(qid, group, category, found, alternatives, recommendation, affects, rules, why):
    return {"affects": list(affects), "alternatives": list(alternatives), "category": category,
            "continue_safely": True, "found": found, "group": group, "id": qid, "recommendation": recommendation,
            "rules_checked": list(rules), "why_unresolved": why}


QUESTIONS = [
    q("OQ-06", "MASONRY_BEAMS_OVER_WALLS", "B_MISSING_DRAWING_EVIDENCE",
      "the architectural plan does not say which walls carry a beam, nor its depth",
      ["no beams over walls (a stated project fact)", "the structural plan's beam layout and depths"],
      "hold the panel at its upper bound until the structural plan or a fact says so",
      ["ARCH.WALL_PANEL", "ARCH.WALL_VOLUME", "MAS.BLOCK"], ["UP-MAS-HEIGHT-001"],
      "a beam bottom on a section applies to the walls under beams only"),
    q("OQ-07", "MASONRY_MATERIAL", "B_MISSING_DRAWING_EVIDENCE",
      "the wall material of each thickness family (block type, RC wall, partition) is not stated",
      ["a legend or specification on the drawing", "a project fact masonry.materials.{family}"],
      "MAS.BLOCK stays an RFI naming the family", ["MAS.BLOCK"], ["UP-MAS-HEIGHT-001"],
      "a thickness is never evidence of a material"),
    q("OQ-08", "FACADE_HEIGHT_CONVENTION", "D_MISSING_OWNER_POLICY",
      "the facade of a floor is measured from its F.F.L. to the next floor's F.F.L.",
      ["F.F.L. to the next F.F.L. (each floor's own band, stacked)", "structural levels (slab top to slab top)",
       "a stated height per floor"],
      "F.F.L. to F.F.L. (the bands meet without overlap); confirm", ["ARCH.FACADE"], ["UP-FACADE-001"],
      "the engine's reading of the program; no owner statement yet"),
    q("OQ-09", "FACADE_PLINTH_AND_FINISH", "B_MISSING_DRAWING_EVIDENCE",
      "the external ground level (plinth below the lowest F.F.L.) and the exterior finish system are not read",
      ["external ground level from a section / site plan", "exterior finish from elevations / specification / a "
       "project fact facade.finish"],
      "hold the plinth and the finish", ["ARCH.FACADE plinth", "FIN.EXT.FINISH"], ["UP-FACADE-001"],
      "neither is in the plan"),
    q("OQ-10", "FORMWORK_EARTH_FACES", "D_MISSING_OWNER_POLICY",
      "footing and ground-beam sides: formed, or cast against the excavation",
      ["FORMED (formwork measured)", "EARTH_CAST (no formwork)"], "keep both readings side by side",
      ["formwork FOOTINGS / GROUND_BEAMS SIDES"], ["UP-FW-001"], "a contract / method statement decision"),
    q("OQ-11", "FORMWORK_BEAM_DEPTH", "D_MISSING_OWNER_POLICY",
      "the schedule beam depth: below the slab, or total including the slab (route G BEAM_DEPTH_CONVENTION)",
      ["BELOW_SLAB", "TOTAL"], "keep both readings side by side", ["formwork BEAMS SIDES", "beam concrete"],
      ["UP-FW-001"], "the schedule does not say; route G keeps the same two readings for the concrete"),
    q("OQ-12", "FORMWORK_COLUMN_JUNCTIONS_AND_SLAB_EDGES", "B_MISSING_DRAWING_EVIDENCE",
      "which beams frame into each column, and the free edges of each slab, are not in the register",
      ["the structural plan adjacency (beam ends at columns; slab perimeter and openings)"],
      "column sides stay an upper bound; slab edges held", ["formwork COLUMNS SIDES", "formwork SLABS EDGES"],
      ["UP-FW-001"], "the register keeps elements, not their contacts"),
    q("OQ-13", "EXCAVATION_LEVELS_AND_WORKING_SPACE", "B_MISSING_DRAWING_EVIDENCE",
      "the natural ground level, the founding level and the working space are not stated",
      ["levels from the foundation section / soil report; the working space from the specification or a fact"],
      "footprints only; volume and backfill held", ["excavation", "backfill"], ["UP-EXC-001"],
      "an excavation depth is never assumed"),
]


def build():
    base_bytes = BASE.read_bytes()
    reg = copy.deepcopy(json.loads(base_bytes.decode("utf-8")))
    rules = {r["rule_id"]: r for r in reg["rules"]}
    for r in NEW:
        assert r["rule_id"] not in rules, r["rule_id"]
        rules[r["rule_id"]] = r
    have = {x["id"] for x in reg["owner_questions"]}
    assert not have & {x["id"] for x in QUESTIONS}
    reg.update(version="1.5.0", effective=D,
               base={"version": "1.4.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["ARCH_TAKEOFF_V2.9 (engine/source/knowledge.py, using('1.5.0'))",
                            "engine/source/struct_n10.py (rule ids only)"],
               not_consumed_by="ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; rules/ 1.5.0); ARCH_TAKEOFF_V2.3 reads "
                               "registry 1.0.0; ARCH_TAKEOFF_V2.4 .. V2.6 read registry 1.1.0; ARCH_TAKEOFF_V2.7 "
                               "reads registry 1.2.0; ARCH_TAKEOFF_V2.7.1 reads registry 1.3.0; ARCH_TAKEOFF_V2.8 "
                               "reads registry 1.4.0 (frozen)",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]),
               owner_questions=reg["owner_questions"] + QUESTIONS,
               delta={"builder": "tools/kb_build_1_5.py", "new": sorted(r["rule_id"] for r in NEW), "amended": [],
                      "owner_questions": [x["id"] for x in QUESTIONS],
                      "status_note": "every new rule is REQUIRES_CONFIRMATION: the engine's reading of the owner "
                                     "program, not an owner statement"})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.5.0 up to date" if same else "registry 1.5.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_5.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["owner_questions"]), "owner questions", OUT.stat().st_size, "bytes")
