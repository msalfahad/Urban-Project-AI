"""T-542: every stair marble surface classed to its governing bed rule, once against the floor-bed family, and turned
into mortar / cement / sand per component (research/agents_t542).

Fixture villa P542 (not the training villa), by hand; tread marble 0.030, bed 0.03 m 1:3 (Q-45 B), UP-STAIR-017 rate
9.576 bags + 0.9975 m3 loose sand per m3 installed, Q-45 5 % loss on its own account:
  straight flight F1: 10 risers of 0.165 (the 10th lands on the half landing, so 9 treads), going 0.30, width 1.10
    treads   9 x 0.30 x 1.10              = 2.9700 m2
    risers  10 x 1.10 x (0.165 - 0.030)   = 1.4850 m2   (visible riser, UP-STAIR-003)
  half landing LD (STAIR_LANDING) 1.10 x 1.20 = 1.3200 m2
  arrival AR (STAIR_ARRIVAL, owner answer named) 1.10 x 1.50 = 1.6500 m2, deducted from the floor host by 1.65
  stair bed                                = 7.4250 m2 -> 0.22275 m3 installed
      cement 0.22275 x 9.576 = 2.133054 bags, sand 0.22275 x 0.9975 = 0.22219313 m3
      loss 0.0111375 m3; procurement 0.2338875 m3 -> 2.2397067 bags, 0.2333028 m3
  by class: treads 0.0891 m3 / risers 0.04455 m3 / landings 0.0891 m3 (0.0396 + 0.0495)
Adverse: the foot-of-flight lobby LB (FLOOR_OR_LANDING, 1.10 x 1.10 = 1.21) is already bedded by a floor-bed line ->
FLOOR_BED_FAMILY, beside, never in the stair sum; a STAIR_LANDING on a floor-bedded element is a DOUBLE_COUNT; a
landing inside a floor host with no or a partial deduction is refused; no riser / landing / arrival source -> HELD,
never 0 and never the floor 1:4 bed; a held part stays HELD; twice / unknown surface / bad class / bad area refused;
mm, mirror and rotation of a landing polygon give the same bed.
"""

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t542"))
sys.path.insert(0, str(ROOT / "research" / "agents_t534"))

import stair_bed_classes as C  # noqa: E402
import stair_bed_reconcile as M  # noqa: E402

A = lambda x: pytest.approx(x, abs=1e-6)  # noqa: E731
SRC = {"riser": "owner record naming risers in the stair bed", "landing": "owner record naming landings"}
FLOOR_BEDS = {"P542:LOBBY": "L-floorbed-lobby"}


def villa(**over):
    f = M.flight_parts(dict(id="F1", treads=9, risers=10, going=0.30, width=1.10, rise=0.165), 0.03)
    ld = M.landing_part(dict(id="LD", length=1.20, width=1.10))
    ar = M.landing_part(dict(id="AR", length=1.50, width=1.10))
    parts = [dict(p) for p in f]
    parts.append(dict(ld, landing_class=C.STAIR_LANDING,
                      floor_host={"host": "lower floor", "void": True, "source": "plan: over the stair void"}))
    parts.append(dict(ar, landing_class=C.STAIR_ARRIVAL, arrival_source="owner answer X",
                      floor_host={"host": "upper floor tiles", "deducted_m2": 1.65, "source": "floor net of AR"}))
    parts.append({"key": "LB", "surface": C.LANDING, "m2": None, "status": M.HELD, "beside": 1.21,
                  "reason": "MATERIAL_HELD", "element_id": "P542:LOBBY", "landing_class": C.FLOOR_OR_LANDING})
    for p in parts:
        p.update(over.get(p["key"] + ":" + p["surface"], {}))
    return parts


def run(parts=None, src=SRC, beds=FLOOR_BEDS):
    return C.materials(C.classify_all(parts if parts is not None else villa(), src, beds))


def test_fixture_by_hand_per_component():
    rows = run()
    s = C.summarise(rows)
    assert s["area_m2"] == A(7.425) and s["state"] == "COMPLETE"
    assert s["mortar_m3_low"] == A(0.22275)
    assert s["cement_bags_low"] == pytest.approx(0.22275 * 9.576, abs=5e-6)        # V7 rounds per row (6 dp)
    assert 0.22275 * 9.576 == A(2.133054)
    assert s["sand_m3_low"] == pytest.approx(0.22275 * 0.9975, abs=2e-6)
    assert s["bed_loss_m3_low"] == pytest.approx(0.0111375, abs=2e-6)
    assert s["bed_procurement_m3_low"] == pytest.approx(0.2338875, abs=2e-6)
    assert s["cement_bags_procurement_low"] == pytest.approx(0.2338875 * 9.576, abs=1e-5)
    assert s["sand_m3_procurement_low"] == pytest.approx(0.2338875 * 0.9975, abs=1e-5)
    by = {(r["key"], r["surface"]): r for r in rows}
    assert by[("F1", "TREAD")]["mortar_m3_low"] == A(0.0891) and by[("F1", "TREAD")]["kind"] == "STAIR_FLIGHT"
    assert by[("F1", "RISER")]["mortar_m3_low"] == A(0.04455)
    assert by[("LD", "LANDING")]["mortar_m3_low"] == A(0.0396) and by[("LD", "LANDING")]["kind"] == "STAIR_LANDING"
    assert by[("AR", "LANDING")]["mortar_m3_low"] == A(0.0495)
    for r in rows:
        if r["bed_class"] == C.STAIR_BED:
            assert r["bed_m"] == 0.03 and r["mix"] == "1:3" and r["rule"]
            # installed and the 5 % own account apart: procurement = installed + loss, never merged
            assert r["bed_procurement_m3_low"] == pytest.approx(r["mortar_m3_low"] + r["bed_loss_m3_low"], abs=2e-6)
            assert r["allowance_cement_bags"] == pytest.approx(10 * r["mortar_m3_low"], abs=1e-6)


def test_landing_already_in_floor_bed_family_not_counted_twice():
    rows = run()
    lb = next(r for r in rows if r["key"] == "LB")
    assert lb["bed_class"] == C.FLOOR_BED_FAMILY and lb["floor_bed_line"] == "L-floorbed-lobby"
    assert lb["bed_m2"] is None and "mortar_m3_low" not in lb
    s = C.summarise(rows)
    assert s["area_m2"] == A(7.425)                      # 1.21 is NOT added
    assert s["floor_bed_family_beside"] == [{"key": "LB", "surface": "LANDING", "floor_bed_line": "L-floorbed-lobby",
                                             "beside_m2": 1.21}]
    assert "floor-bed family" in s["print"]
    # even with a measured area and no floor-bed line it is never a stair bed (the floor host decides)
    rows2 = run(villa(**{"LB:LANDING": {"m2": 1.21, "status": "MEASURED", "element_id": None}}))
    assert next(r for r in rows2 if r["key"] == "LB")["bed_class"] == C.FLOOR_BED_FAMILY
    assert C.summarise(rows2)["area_m2"] == A(7.425)


def test_stair_landing_on_a_floor_bedded_element_is_a_double_count():
    with pytest.raises(C.BedClassError, match="DOUBLE_COUNT"):
        run(villa(**{"LD:LANDING": {"element_id": "P542:LOBBY"}}))
    with pytest.raises(C.BedClassError, match="DOUBLE_COUNT"):
        run(villa(**{"F1:TREAD": {"element_id": "P542:LOBBY"}}))


def test_floor_host_must_deduct_the_landing():
    with pytest.raises(C.BedClassError, match="DOUBLE_COUNT"):
        run(villa(**{"AR:LANDING": {"floor_host": {"host": "upper floor tiles", "source": "plan"}}}))
    with pytest.raises(C.BedClassError, match="partial deduction"):
        run(villa(**{"AR:LANDING": {"floor_host": {"host": "upper floor tiles", "deducted_m2": 1.20,
                                                   "source": "plan"}}}))
    with pytest.raises(C.BedClassError, match="without its source"):
        run(villa(**{"AR:LANDING": {"floor_host": {"host": "upper floor tiles", "deducted_m2": 1.65}}}))
    s = C.summarise(run(villa(**{"AR:LANDING": {"floor_host": {"host": "x", "outside": True, "source": "plan"}}})))
    assert s["area_m2"] == A(7.425)


def test_riser_without_source_held_never_zero():
    rows = run(src={"riser": None, "landing": SRC["landing"]})
    s = C.summarise(rows)
    assert s["area_m2"] == A(5.94) and s["state"] == "PARTIAL"
    (h,) = s["held"]
    assert h["surface"] == "RISER" and h["beside_m2"] == A(1.485) and "RISER_BED_SOURCE_NOT_GIVEN" in h["reason"]
    assert s["print"].startswith("AT_LEAST 5.9400 m2 + HELD (1 parts)")


def test_landing_without_source_held_floor_bed_never_borrowed():
    rows = run(src={"riser": SRC["riser"], "landing": None})
    s = C.summarise(rows)
    assert s["area_m2"] == A(4.455) and {(h["key"], h["beside_m2"]) for h in s["held"]} == {("LD", 1.32),
                                                                                           ("AR", 1.65)}
    for r in rows:
        if r["bed_class"] == C.HELD:
            assert "LANDING_BED_SOURCE_NOT_GIVEN" in r["reason"] and "mortar_m3_low" not in r
            assert r.get("mix") is None                     # no 1:4 floor mix on a held landing


def test_arrival_without_owner_answer_held():
    rows = run(villa(**{"AR:LANDING": {"arrival_source": None}}))
    ar = next(r for r in rows if r["key"] == "AR")
    assert ar["bed_class"] == C.HELD and "ARRIVAL_MATERIAL_NOT_GIVEN" in ar["reason"] and ar["beside_m2"] == A(1.65)
    assert C.summarise(rows)["area_m2"] == A(5.775)


def test_held_marble_part_stays_held():
    parts = villa(**{"F1:TREAD": {"m2": None, "status": M.HELD, "reason": "WINDERS_NOT_ESTABLISHED", "beside": 3.0}})
    s = C.summarise(run(parts))
    assert s["area_m2"] == A(4.455) and s["held"][0]["beside_m2"] == 3.0
    assert s["held"][0]["reason"] == "WINDERS_NOT_ESTABLISHED"


def test_refusals():
    p = villa()
    with pytest.raises(C.BedClassError, match="twice"):
        run(p + [dict(p[0])])
    with pytest.raises(C.BedClassError, match="unknown surface"):
        run([{"key": "X", "surface": "NOSING", "m2": 1.0, "status": "MEASURED"}])
    with pytest.raises(C.BedClassError, match="landing class"):
        run([{"key": "X", "surface": C.LANDING, "m2": 1.0, "status": "MEASURED"}])
    with pytest.raises(C.BedClassError, match="no landing class"):
        run([{"key": "X", "surface": C.TREAD, "m2": 1.0, "status": "MEASURED", "landing_class": C.STAIR_LANDING}])
    for bad in (0, -1.0, True, float("nan"), "1.0"):
        with pytest.raises(C.BedClassError):
            run([{"key": "X", "surface": C.TREAD, "m2": bad, "status": "MEASURED"}])


def test_units_mirror_rotation_same_bed():
    base = M.landing_part(dict(id="LD", length=1.20, width=1.10))["m2"]
    pts = [(0, 0), (1100, 0), (1100, 1200), (0, 1200)]
    for deg in (0, 37, 90, 211):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        for mirror in (1, -1):
            q = [(mirror * (x * c - y * s), x * s + y * c) for x, y in pts]
            ld = M.landing_part(dict(id="LD", polygon=q, unit_m=0.001))
            rows = run([dict(ld, landing_class=C.STAIR_LANDING)])
            assert rows[0]["bed_m2"] == A(base) == A(1.32)
            assert rows[0]["mortar_m3_low"] == A(0.0396)


def test_module_holds_no_villa_constant():
    src = (ROOT / "research/agents_t542/stair_bed_classes.py").read_text(encoding="utf-8")
    for token in ("Alsenan", "L-", "GF-", "1F-", "2F-", "MS1", "MS2", "RS-", "E1"):
        assert token not in src, token


# ------------------------------------------------------------------ training villa pins (merged research only) ----
def alsenan():
    import t542_alsenan as AL
    return AL, AL.build()


def test_alsenan_whole_stair_bed_per_class():
    AL, o = alsenan()
    s = o["summary"]
    assert s["whole_stair_bed"]["area_m2"] == A(56.35861) and len(s["whole_stair_bed"]["held"]) == 6
    assert s["tread"]["area_m2"] == A(23.37) and s["riser"]["area_m2"] == A(12.29861)
    assert s["landing"]["area_m2"] == A(20.69) and s["landing"]["state"] == "COMPLETE"
    assert s["whole_stair_bed"]["mortar_m3_low"] == pytest.approx(56.35861 * 0.03, abs=1e-5)
    assert s["whole_stair_bed"]["cement_bags_low"] == pytest.approx(56.35861 * 0.03 * 9.576, abs=1e-4)
    assert s["whole_stair_bed"]["bed_procurement_m3_low"] == pytest.approx(56.35861 * 0.03 * 1.05, abs=1e-5)
    held = {(h["key"], h["surface"]) for h in s["whole_stair_bed"]["held"]}
    assert held == {("MS1-T", "TREAD"), ("MS1-T", "RISER"), ("MS2-TR#held-risers", "RISER"),
                    ("MS2-U#held-treads", "TREAD"), ("RS-C", "TREAD"), ("RS-C", "RISER")}


def test_alsenan_beyond_the_treads_and_v7_wire():
    AL, o = alsenan()
    s = o["summary"]
    assert s["beyond_v7_wire"]["area_m2"] == A(20.92611)        # risers 10.33861 + landings 10.5875
    beyond = [r for r in o["rows"] if r["bed_class"] == C.STAIR_BED and not r["in_v7_wire"]]
    assert sum(r["bed_m2"] for r in beyond if r["surface"] == "RISER") == A(10.33861)
    assert sum(r["bed_m2"] for r in beyond if r["surface"] == "LANDING") == A(10.5875)
    assert {r["key"] for r in beyond if r["surface"] == "LANDING"} == {"MS1-LD", "MS2-LD", "2F-ARR", "RS-LD"}
    assert s["beyond_v7_wire"]["mortar_m3_low"] == pytest.approx(20.92611 * 0.03, abs=1e-5)
    w = o["v7_wire_candidate_net"]
    assert w["area_m2"] == A(35.4313) and w["lines"] == 11 and w["polygon_residual_m2"] == A(0.0012)
    assert s["in_v7_wire"]["area_m2"] == A(35.4325)


def test_alsenan_floor_bed_family_once():
    AL, o = alsenan()
    fam = {r["key"]: r["floor_bed_line"] for r in o["rows"] if r["bed_class"] == C.FLOOR_BED_FAMILY}
    assert fam == {"GF-HALL": "L-3e451bfc3e11473a2cec", "GF-LOBBY": "L-faa974d23d90547f0b5b"}
    stair_elements = {r["element_id"] for r in o["rows"] if r["bed_class"] == C.STAIR_BED and r["element_id"]}
    d, by_id, floor_bed, census = AL.load()
    assert not stair_elements & set(floor_bed)
    # the arrival deducted from its host; the intermediate landings over the void or outside every host
    rows = {r["key"]: r for r in o["rows"]}
    assert rows["1F-ARR"]["floor_host"]["deducted_m2"] == A(4.9225)
    assert rows["RS-LD"]["floor_host"]["deducted_m2"] == A(1.352454)
    assert rows["MS1-LD"]["floor_host"]["void"] and rows["2F-ARR"]["floor_host"]["outside"]
    a = o["adverse_no_sources"]
    assert a["area_m2"] == A(23.37) and len(a["held"]) == 20


def test_alsenan_committed_out_reproduces():
    AL, o = alsenan()
    old = json.loads((AL.OUT / "T542_STAIR_BED_CLASSES.json").read_text(encoding="utf-8"))
    assert old == json.loads(json.dumps(o, sort_keys=True))
