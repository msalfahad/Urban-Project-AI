"""Phase 2B-1 WP-3: the owner door-opening correction (UP-DOOR-OPEN-002), door heights (UP-DOOR-HGT-001), the
AS_DRAWN / OWNER_REQUIRED scenarios and the elevator schedule (ARCH_TAKEOFF_V2.3; engine.source.door_standards).

Hand truth: the owner table (internal PVC 1.00 -> wall 1.10, bathroom PVC 0.90 -> 1.00, external aluminium 1.00 ->
1.10; wall = nominal + 0.10 m, never a second 0.10 m) and the coordinates of the door-guard floor (tests/m9_p2b0)."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kb_fixtures as KF                                      # noqa: E402
from engine.source import door_model as DM                    # noqa: E402
from engine.source import door_standards as DSTD              # noqa: E402
from engine.source import knowledge as K                      # noqa: E402

I, B, E = DSTD.INTERNAL, DSTD.BATH, DSTD.EXTERNAL


@pytest.fixture(scope="module")
def floor():
    return KF.door_floor()


@pytest.mark.parametrize("cat,cad,wall,enl", [
    (I, 0.90, 1.10, 0.20), (B, 0.90, 1.00, 0.10), (E, 1.00, 1.10, 0.10), (I, 1.20, 1.20, 0.00),
    (B, 0.80, 1.00, 0.20), (E, 0.90, 1.10, 0.20), (I, 1.10, 1.10, 0.00), (B, 1.05, 1.05, 0.00),
    (I, 1.00, 1.10, 0.10), (B, 1.00, 1.00, 0.00), (E, 1.20, 1.20, 0.00), (E, 1.10, 1.10, 0.00)],
    ids=["internal-0.90", "bath-0.90", "external-1.00", "internal-1.20", "bath-0.80", "external-0.90",
         "internal-1.10", "bath-1.05", "internal-1.00", "bath-1.00", "external-1.20", "external-1.10"])
def test_the_owner_correction_table(cat, cad, wall, enl):
    """the owner's examples: internal 0.90 -> 1.10 (+0.20), bathroom 0.90 -> 1.00 (+0.10), external 1.00 -> 1.10
    (+0.10), internal 1.20 -> no enlargement; the CAD value is kept beside the requirement."""
    r = DSTD.required_opening(cat, cad)
    assert r["state"] == "ESTABLISHED" and r["cad_wall_opening_m"] == cad
    assert r["owner_required_wall_opening_m"] == pytest.approx(wall, abs=1e-9)
    assert r["enlargement_m"] == pytest.approx(enl, abs=1e-9)
    assert ("OPENING_BELOW_OWNER_STANDARD" in r["flags"]) == (enl > 0)
    assert r["architectural_wall_opening_m"] == pytest.approx(r["required_nominal_door_m"] + 0.10)


def test_no_second_allowance_is_added():
    """the required wall opening already holds the 0.10 m: re-applying the rule to it changes nothing."""
    for cat in (I, B, E):
        s = K.door_standard(cat)
        once = DSTD.required_opening(cat, 0.70)["owner_required_wall_opening_m"]
        twice = DSTD.required_opening(cat, once)
        assert once == pytest.approx(s["required_nominal_door_m"] + 0.10)
        assert twice["owner_required_wall_opening_m"] == pytest.approx(once) and twice["enlargement_m"] == 0.0
        assert twice["nominal_door_for_opening_m"] == pytest.approx(s["required_nominal_door_m"])
    # a wider drawn opening keeps its width; its nominal door is derived (CAD - 0.10), never widened again
    w = DSTD.required_opening(I, 1.20)
    assert w["owner_required_wall_opening_m"] == 1.20 and w["nominal_door_for_opening_m"] == pytest.approx(1.10)
    assert w["nominal_basis"].startswith("RULE_DERIVED")


def test_the_drawn_width_is_never_overwritten(floor):
    """every scenario row carries the door model's CAD opening unchanged, and the door model is not modified."""
    model = copy.deepcopy(floor["model"])
    out = DSTD.door_scenarios(model, None, openings=floor["M"]["openings"], rooms=floor["M"]["rooms"])
    assert model == floor["model"]
    for el, r in zip(model["elements"], out["rows"]):
        assert r["as_drawn"]["cad_wall_opening_m"] == el.get("structural_opening_width_m")
        assert r["owner_required"]["owner_required_wall_opening_m"] is None or el.get("structural_opening_width_m") \
            is None or _num(r["owner_required"]["owner_required_wall_opening_m"]) >= el["structural_opening_width_m"]


def _num(v):
    return v["high"] if isinstance(v, dict) else v


def test_the_main_entrance_keeps_its_drawn_width(floor):
    """UP-DOOR-CLS-004: the main entrance is measured from its drawing; the ordinary standard is never applied."""
    r = DSTD.required_opening(DSTD.MAIN, 1.6)
    assert r["state"] == "AS_DRAWN_ONLY" and r["owner_required_wall_opening_m"] == 1.6 and r["enlargement_m"] == 0.0
    assert r["required_nominal_door_m"] is None
    main = [x for x in floor["scenarios"]["rows"] if x["category"] == DSTD.MAIN]
    assert len(main) == 1 and main[0]["as_drawn"]["cad_wall_opening_m"] == pytest.approx(1.0)
    assert main[0]["owner_required"]["enlargement_m"] == 0.0 and main[0]["review_status"] == "NO_MODIFICATION"
    assert "MAIN_ENTRANCE_FALLBACK_SUBJECT_TO_PROJECT_CONTEXT" in main[0]["flags"]


def test_no_elevator_entrance_reaches_the_door_quantities(floor):
    """UP-DOOR-CLS-005: a lift door is EXCLUDED from both door views; a lift candidate is not a door element."""
    assert DSTD.required_opening(DSTD.ELEVATOR, 1.0)["state"] == "EXCLUDED"
    lift = KF.door("LIFT-1", "A", "B", cls=DM.LIFT)
    lift["released"] = False
    model = {"elements": [lift], "lift_candidates": [], "lift_openings": []}
    out = DSTD.door_scenarios(model, None, openings=[], rooms=[])
    assert out["views"]["EXCLUDED"] == {DSTD.ELEVATOR: 1}
    assert out["views"]["AS_DRAWN"] == {} and out["views"]["OWNER_REQUIRED"] == {}
    cand = {c["opening_id"] for c in floor["model"]["lift_candidates"]}
    assert cand and not cand & {r["opening_id"] for r in floor["scenarios"]["rows"]}


def test_scenario_areas_are_kept_apart(floor):
    """AS_DRAWN and OWNER_REQUIRED are separate views of the same doors (never summed); an area on an assumed height
    is never in a confirmed total."""
    v = floor["scenarios"]["views"]
    released = [r for r in floor["scenarios"]["rows"] if r["view"] == "AS_DRAWN"]
    assert sum(x["count"] for x in v["AS_DRAWN"].values()) == len(released)
    assert sum(x["count"] for x in v["OWNER_REQUIRED"].values()) == len(released)
    assert all(x["area_confirmed_m2"] == 0.0 for x in v["AS_DRAWN"].values())        # every height is assumed here
    pvc = v["OWNER_REQUIRED"][I]
    assert pvc["count"] == 2 and pvc["enlargement_m"] == pytest.approx(0.40) and pvc["wall_opening_m"] == \
        pytest.approx(2.20)
    assert pvc["wall_opening_area_assumed_m2"] == pytest.approx(2 * 1.10 * 2.20)
    assert v["AS_DRAWN"]["DOOR.INTERNAL.PVC"]["area_assumed_m2"] == pytest.approx(2 * 0.90 * 2.20)
    assert floor["scenarios"]["conservation"]["ok"]


def test_an_owner_fallback_height_is_assumed_never_confirmed():
    for cat in (I, B, E):
        h = DSTD.door_height(cat, None)
        assert h["value_m"] == 2.20 and h["state"] == "ASSUMED" and "HEIGHT_ASSUMED" in h["flags"]
    m = DSTD.door_height(DSTD.MAIN, None)
    assert m["value_m"] == 2.50 and "MAIN_ENTRANCE_FALLBACK_SUBJECT_TO_PROJECT_CONTEXT" in m["flags"]
    assert DSTD.door_height(DSTD.ELEVATOR, None)["state"] == "NOT_APPLICABLE"


def test_a_schedule_height_wins_over_the_owner_fallback(floor):
    sched = {"schema": "URBAN_ARCH_FACTS_V1", "project_id": "SYNTHETIC KB",
             "opening_heights": {"DOOR": {"value_m": 2.10, "authority": "SOURCE: door schedule"}}}
    h = DSTD.door_height(I, sched)
    assert (h["value_m"], h["state"], h["precedence"]) == (2.10, "SOURCE", "APPROVED_DRAWING")
    fb = DSTD.door_height(I, {"opening_heights": {"DOOR_ASSUMED": {"value_m": 2.4, "authority": "project"}}})
    assert (fb["value_m"], fb["state"]) == (2.4, "ASSUMED")
    # the door model reads a source height before the owner fallback it is handed
    f = DSTD.door_model_facts(sched)
    assert f["opening_heights"]["DOOR"]["value_m"] == 2.10 and set(sched["opening_heights"]) == {"DOOR"}
    run = KF.door_floor(facts=sched)
    rows = [r for r in run["scenarios"]["rows"] if r["view"] == "AS_DRAWN"]
    assert rows and all(r["as_drawn"]["height"]["value_m"] == 2.10 for r in rows)
    assert all(r["as_drawn"]["wall_opening_area"]["state"] == "CONFIRMED" for r in rows)


def test_an_enlargement_lists_its_dependent_trades_and_releases_nothing(floor):
    d = DSTD.dependency_impacts(0.20, {"value_m": 2.2, "state": "ASSUMED"}, 0.20, ["COLUMN:C1", "WALL"],
                                ["WET", "DRY"])
    trades = {x["trade"] for x in d["impacts"]}
    assert {"OPENINGS", "MASONRY", "WALL_FINISH", "PLASTER", "MARBLE", "WATERPROOFING", "CONCRETE",
            "FLOOR_FINISH"} <= trades
    assert d["release"] == "REVIEW_REQUIRED" and d["structural"].startswith("STRUCTURAL_INTERFACE_REVIEW")
    assert DSTD.dependency_impacts(0.2, None, 0.2, ["COLUMN:a", "COLUMN:b"], [])["structural"].startswith(
        "STRUCTURAL_INTERFACE_BLOCKS_ENLARGEMENT")
    rows = [r for r in floor["scenarios"]["rows"] if r["review_status"] == "MODIFICATION_PROPOSED_NOT_APPROVED"]
    assert rows and all(r["dependency_impacts"]["release"] == "REVIEW_REQUIRED" for r in rows)
    # no BOQ line comes from a scenario: the measured lines name no door-standard rule
    assert not [ln for ln in floor["M"]["lines"] if (ln.get("rule") or {}).get("rule_id", "").startswith("UP-DOOR")]


def test_categories_follow_the_space_model(floor):
    """the dimension category comes from the typed sides (the space model), not from a layer or a label alone."""
    assert DSTD.door_category(KF.door("a", "X", "Y"))[0] == I
    bath = KF.door("b", "X", "Y")
    bath["sides"][0]["codes"] = ["BATHROOM"]
    assert DSTD.door_category(bath)[0] == B
    assert DSTD.door_category(KF.door("c", "X", "FACADE", cls=DM.ALU))[0] == E
    rev = DSTD.required_opening(DSTD.REVIEW, 0.90)
    assert rev["state"] == "ESTABLISHED" and "CLASS_NOT_SETTLED_SAME_STANDARD" in rev["flags"]
    assert rev["owner_required_wall_opening_m"] == pytest.approx(1.10)
    k = next(e for e in floor["model"]["elements"] if e["class"] == DM.CLASS_REVIEW)        # kitchen | lobby
    assert KF.row_of(floor, k)["category"] == DSTD.REVIEW and KF.row_of(floor, k)["view"] == "UNRESOLVED"


def test_a_kitchen_door_to_outdoors_is_aluminium():
    """the lobby the kitchen door opens into is bound EXTERIOR by a project decision: the door is external
    aluminium (1.00 nominal, 1.10 wall), released; the decision binds the lobby only."""
    run = KF.door_floor(decisions=KF.decisions(("PD-1", KF.LOBBY_POINT_M, "EXTERIOR")))
    assert len(run["decided"]) == 1
    k = next(e for e in run["model"]["elements"] if any("KITCHEN" in (s.get("codes") or ()) for s in e["sides"])
             and e.get("opening_id"))
    assert k["boq_class"] == DM.ALU and k["released"]
    assert any("project decision PD-1" in (s.get("evidence") or "") for s in k["sides"])
    r = KF.row_of(run, k)
    assert r["category"] == E and r["owner_required"]["owner_required_wall_opening_m"] == pytest.approx(1.10)


def test_a_pantry_door_to_an_indoor_corridor_stays_pvc():
    """a pantry is a wet area (UP-WET-001) but not a bathroom: its door to a labelled corridor is internal PVC with
    the internal standard (1.00 / 1.10), even though the corridor has a doorless opening to the outside; an INTERIOR
    project decision on the unlabelled lobby gives the same class."""
    words = tuple((("PANTRY" if w == "KITCHEN" else w), p) for w, p in KF.FX.DOOR_WORDS) + (("CORRIDOR", (5100, 1600)),)
    run = KF.door_floor(words=words)
    p = next(e for e in run["model"]["elements"] if any("PANTRY" in (s.get("codes") or ()) for s in e["sides"]))
    assert p["boq_class"] == DM.PVC and p["released"]
    r = KF.row_of(run, p)
    assert r["category"] == I and r["owner_required"]["owner_required_wall_opening_m"] == pytest.approx(1.10)
    inside = KF.door_floor(decisions=KF.decisions(("PD-2", KF.LOBBY_POINT_M, "INTERIOR")))
    k = next(e for e in inside["model"]["elements"] if any("KITCHEN" in (s.get("codes") or ()) for s in e["sides"])
             and e.get("opening_id"))
    assert k["boq_class"] == DM.PVC and all(s["kind"] == "SPACE" for s in k["sides"])


def test_the_elevator_schedule_uses_cad_geometry(floor):
    """UP-ELEV-SCHED-001: the shaft size is the drawn footprint (1.6 x 1.6 m), compared with - never replaced by -
    the 1.8 x 1.8 m reference; the landing is the 0.80 m opening; a stacked footprint is a CANDIDATE."""
    (sh,) = floor["elevators"]["shafts"]
    assert sh["shaft_dimensions_m"] == [[1.6, 1.6]] and sh["shaft_area_m2"] == [pytest.approx(2.56)]
    assert sh["reference_comparison"][0]["differs_m"] == [pytest.approx(-0.2), pytest.approx(-0.2)]
    assert sh["status"] == "CANDIDATE" and sh["number_of_landings"] == 1
    assert sh["landings"][0]["width_m"] == pytest.approx(0.80) and sh["in_door_boq"] is False
    assert "a lift label or lift schedule confirming the shaft is a lift" in sh["missing"]


def test_the_superseded_part_c_reading_is_not_applied():
    """Part C section 7 read the minimums 1.00 / 0.90 / 1.00 as wall openings (UP-DOOR-MIN-001, DEPRECATED): they are
    nominal doors; the wall opening is 0.10 m wider."""
    old = K.rule("UP-DOOR-MIN-001")
    assert old["status"] == "DEPRECATED" and old["superseded_by"] == "UP-DOOR-OPEN-002"
    for cat, nominal in ((I, 1.00), (B, 0.90), (E, 1.00)):
        r = DSTD.required_opening(cat, nominal)
        assert r["owner_required_wall_opening_m"] == pytest.approx(nominal + 0.10)       # not max(CAD, minimum)
        assert r["enlargement_m"] == pytest.approx(0.10)


# --- knowledge registry 1.6.0 (board task T-011, owner answer Q-04 / OQ-05): DSTD.opening_record_kb16 ---------------
# Hand truth (not from the engine): the minimum is the nominal door; wall opening = nominal + 0.10 m (internal PVC
# 1.00 -> 1.10, bathroom PVC 0.90 -> 1.00, external aluminium 1.00 -> 1.10); a wider drawn opening keeps its size; the
# main door as drawn. Enlargement = required wall opening - drawn opening, proposed only.

def _el(w, source="BAND_GAP"):
    return {"structural_opening_width_m": w, "structural_opening_source": source}


@pytest.mark.parametrize("cat,cad,wall,enl,nominal,compliance", [
    (I, 0.90, 1.10, 0.20, 1.00, "ENLARGEMENT_REQUIRED"), (I, 1.00, 1.10, 0.10, 1.00, "ENLARGEMENT_REQUIRED"),
    (I, 1.20, 1.20, 0.00, 1.10, "MEETS_STANDARD"), (I, 1.10, 1.10, 0.00, 1.00, "MEETS_STANDARD"),
    (B, 0.90, 1.00, 0.10, 0.90, "ENLARGEMENT_REQUIRED"), (B, 1.00, 1.00, 0.00, 0.90, "MEETS_STANDARD"),
    (B, 1.20, 1.20, 0.00, 1.10, "MEETS_STANDARD"), (B, 0.80, 1.00, 0.20, 0.90, "ENLARGEMENT_REQUIRED"),
    (E, 0.90, 1.10, 0.20, 1.00, "ENLARGEMENT_REQUIRED"), (E, 1.00, 1.10, 0.10, 1.00, "ENLARGEMENT_REQUIRED"),
    (E, 1.20, 1.20, 0.00, 1.10, "MEETS_STANDARD")],
    ids=["int-0.90", "int-1.00", "int-1.20", "int-1.10", "bath-0.90", "bath-1.00", "bath-1.20", "bath-0.80",
         "ext-0.90", "ext-1.00", "ext-1.20"])
def test_kb16_hand_table(cat, cad, wall, enl, nominal, compliance):
    r = DSTD.opening_record_kb16(_el(cad), cat)
    assert r["state"] == "ESTABLISHED" and r["knowledge"] == "1.6.0"
    assert r["rule"]["rule_id"] == "UP-DOOR-OPEN-002" and r["rule"]["status"] == "OWNER_APPROVED"
    assert r["as_drawn_wall_opening_m"] == cad                                  # the drawn width is kept
    assert r["owner_required_wall_opening_m"] == pytest.approx(wall, abs=1e-9)
    assert r["enlargement_m"] == pytest.approx(enl, abs=1e-9)
    assert r["nominal_door_for_opening_m"] == pytest.approx(nominal, abs=1e-9)
    assert r["compliance"] == compliance
    assert ("OPENING_BELOW_OWNER_STANDARD" in r["flags"]) == (enl > 0)
    # the 0.10 m is applied once: the required opening re-read meets the standard with no further enlargement
    again = DSTD.opening_record_kb16(_el(r["owner_required_wall_opening_m"]), cat)
    assert again["enlargement_m"] == 0.0 and again["compliance"] == "MEETS_STANDARD"


@pytest.mark.parametrize("mm_units,angle,mirror", [(1e-3, 0.0, False), (1e-3, 30.0, True), (1.0, 123.0, False),
                                                   (1.0, 210.0, True)],
                         ids=["mm", "mm-rot30-mirror", "m-rot123", "m-rot210-mirror"])
def test_kb16_width_from_rotated_mirrored_jambs_in_mm_and_m(mm_units, angle, mirror):
    """a 0.90 m bathroom door drawn in mm or m, rotated and mirrored: the jamb-to-jamb width is 0.90 m by hand, so the
    wall opening required is 1.00 m (+0.10 m) whatever the drawing frame."""
    import math
    half = 0.45 / mm_units
    a = math.radians(angle)
    pts = [(-half, 0.0), (half, 0.0)]
    if mirror:
        pts = [(-x, y) for x, y in pts]
    pts = [(x * math.cos(a) - y * math.sin(a) + 1234.5, x * math.sin(a) + y * math.cos(a) - 98.7) for x, y in pts]
    w = math.dist(*pts) * mm_units
    r = DSTD.opening_record_kb16(_el(w), B)
    assert r["owner_required_wall_opening_m"] == pytest.approx(1.00, abs=1e-6)
    assert r["enlargement_m"] == pytest.approx(0.10, abs=1e-6)


def test_kb16_main_door_elevator_and_unsettled_class():
    main = DSTD.opening_record_kb16(_el(0.80), DSTD.MAIN)            # narrower than any minimum: still as drawn
    assert main["state"] == "AS_DRAWN_ONLY" and main["owner_required_wall_opening_m"] == 0.80
    assert main["enlargement_m"] == 0.0 and main["required_nominal_door_m"] is None
    lift = DSTD.opening_record_kb16(_el(0.90), DSTD.ELEVATOR)
    assert lift["state"] == "EXCLUDED" and lift["owner_required_wall_opening_m"] is None
    rev = DSTD.opening_record_kb16(_el(0.90), DSTD.REVIEW)           # bathroom 1.00 .. internal / external 1.10
    assert rev["state"] == "RANGE" and rev["owner_required_wall_opening_m"] == {"low": 1.0, "high": 1.1}
    assert rev["enlargement_m"] == {"low": pytest.approx(0.10), "high": pytest.approx(0.20)}
    assert rev["compliance"] == "NOT_ESTABLISHED" and "CLASS_NOT_SETTLED" in rev["flags"]
    cand = DSTD.opening_record_kb16(_el(0.90), DSTD.MAIN_CAND)       # as drawn (main) .. external 1.10
    assert cand["state"] == "RANGE" and cand["owner_required_wall_opening_m"] == {"low": 0.9, "high": 1.1}
    wide = DSTD.opening_record_kb16(_el(1.30), DSTD.UNRESOLVED)      # wider than every minimum: one value
    assert wide["state"] == "ESTABLISHED_FOR_EVERY_CANDIDATE" and wide["owner_required_wall_opening_m"] == 1.30


@pytest.mark.parametrize("cat", [I, B, E, DSTD.MAIN, DSTD.MAIN_CAND, DSTD.REVIEW, DSTD.UNRESOLVED])
def test_kb16_missing_width_is_never_zero(cat):
    r = DSTD.opening_record_kb16(_el(None), cat)
    assert r["state"] == "NOT_ESTABLISHED" and r["compliance"] == "NOT_ESTABLISHED"
    assert r["owner_required_wall_opening_m"] is None and r["enlargement_m"] is None
    assert "NO_DRAWN_WIDTH" in r["flags"]


def test_kb16_on_the_door_floor(floor):
    """the synthetic door-guard floor (hand truth in kb_fixtures): main D1 1.00 as drawn; the living room's 0.90 m
    door to the outside is external aluminium -> 1.10; the 0.90 m internal doors -> 1.10; the kitchen | lobby 0.90 m
    door of unsettled class -> 1.00 .. 1.10. The model is not changed and the active registry stays the default."""
    model = copy.deepcopy(floor["model"])
    before = K.version()
    got = {}
    for el in model["elements"]:
        cat, _ = DSTD.door_category(el)
        got.setdefault(cat, []).append(DSTD.opening_record_kb16(el, cat))
    assert model == floor["model"] and K.version() == before == "1.0.0"
    (m,) = got[DSTD.MAIN]
    assert m["state"] == "AS_DRAWN_ONLY" and m["owner_required_wall_opening_m"] == pytest.approx(1.00)
    (e,) = got[E]
    assert e["owner_required_wall_opening_m"] == pytest.approx(1.10) and e["enlargement_m"] == pytest.approx(0.20)
    assert len(got[I]) == 2 and all(r["owner_required_wall_opening_m"] == pytest.approx(1.10) for r in got[I])
    (rv,) = got[DSTD.REVIEW]
    assert rv["owner_required_wall_opening_m"] == {"low": 1.0, "high": 1.1}
