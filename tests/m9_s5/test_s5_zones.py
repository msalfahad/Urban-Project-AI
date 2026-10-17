"""M9 S5 - zones of an open space from DRAWN lines (arch_rooms.zone_partition), on hand-built plan entities
(tools/arch_synth.s5_zones; every expected value is derived by hand from its rectangles, never from the engine).

    the open space whose words need different finishes (MERGED) is split only along lines drawn inside it
    symbols never split it: an X-marked rectangle (the slab opening above), stair flights, a table, a section cut
    a word-less part touching two finish families stays unallocated (no nearest-label choice)
    the zones partition the face exactly; measurement and the floor reconciliation follow them
    metamorphic: translation, rotation, reflection, entity order, collinear subdivision, irrelevant furniture
"""

from __future__ import annotations

import math
import random

import pytest

from engine.source import arch_floor as AF
from engine.source import arch_measure as AM
from engine.source import arch_rooms as AR
from tools import arch_synth as AS

U = 0.001
TOL = 1e-6


def _run(ents, roles):
    return AR.spaces(ents, roles, U, region_id="T")


def _zones(S):
    rec = next(r for r in S["zones"] if r["state"] == "SPLIT")
    return rec, sorted((z["class"], tuple(z["codes"]), round(z["area_m2"], 6)) for z in rec["zones"])


@pytest.fixture(scope="module")
def hall():
    ents, roles, truth = AS.s5_zones()
    return _run(ents, roles), truth


def test_open_space_split_only_along_drawn_lines(hall):
    S, T = hall
    rec, zones = _zones(S)
    assert rec["area_m2"] == pytest.approx(T["face_m2"], abs=TOL)
    got = {c: (cl, a) for cl, c, a in zones}
    assert got[("GARDEN",)] == ("ROOM", pytest.approx(T["GARDEN"], abs=TOL))
    assert got[("BATHROOM",)] == ("ROOM", pytest.approx(T["WASH_CORNER"], abs=TOL))       # named from the basin
    assert got[("DINING", "LIVING")] == ("MIXED", pytest.approx(T["OPEN_PLAN"], abs=TOL))
    assert got[("DINING", "GARDEN", "LIVING")] == ("MERGED", pytest.approx(T["POCKET"], abs=TOL))
    assert sum(a for _, _, a in zones) == pytest.approx(T["face_m2"], abs=1e-4)           # an exact partition


def test_symbols_and_through_lines_never_bound_a_zone(hall):
    S, _ = hall
    rec, _ = _zones(S)
    assert rec["x_rects"] == 1 and rec["symbol_lines"] == 6            # the X-marked rectangle: 4 sides + 2 diagonals
    assert rec["through_lines"] == 1                                    # the section cut runs through the walls
    used = {x for z in rec["zones"] for x in z["lines"]}
    ents, _, _ = AS.s5_zones()
    lay = {s["id"]: s["layer"] for s in ents["segments"]}
    assert {lay[x] for x in used} == {"A-FLOR"}                         # no furniture, no section line
    wash = next(f for f in S["spaces"] if f["codes"] == ["BATHROOM"])
    assert wash["label_source"] == "FIXTURES" and "ZONE_FROM_DRAWN_LINES" in wash["issue"]
    pocket = next(f for f in S["spaces"] if f["class"] == "MERGED")
    assert pocket["label_source"] == "ZONE_SHARED" and pocket["zone"]["shared_between"] == ["DINING", "GARDEN",
                                                                                            "LIVING"]


def test_measurement_follows_the_zones(hall):
    S, T = hall
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64)
    by = {}
    for ln in M["lines"]:
        by.setdefault(ln["item_code"], []).append(ln)
    por = [x for x in by["FIN.FLOOR.PORCELAIN"]]
    assert len(por) == 1 and por[0]["measured_net"] == pytest.approx(T["OPEN_PLAN"], abs=TOL)
    assert por[0]["evidence_state"] == "PROVISIONAL"                    # a zone is an inference
    assert by["FIN.FLOOR.WET_TILE"][0]["measured_net"] == pytest.approx(T["WASH_CORNER"], abs=TOL)
    assert by["FIN.WP.FLOOR"][0]["measured_net"] == pytest.approx(T["WASH_CORNER"], abs=TOL)
    assert by["FIN.WP.UPTURN"][0]["measured_net"] == pytest.approx(4 * 2.0 * 0.20, abs=TOL)   # full perimeter
    assert [x["measured_net"] for x in by["ARCH.EXTERIOR"]] == [pytest.approx(T["GARDEN"], abs=TOL)]
    wash = next(r for r in M["rooms"] if r["codes"] == ["BATHROOM"])
    assert wash["runs_lm"]["wall"] == pytest.approx(4.0, abs=TOL)       # two wall sides; two drawn-line sides
    reasons = [u["reason"] for u in M["unresolved"]]
    assert sum(r.startswith("ZONE_FROM_DRAWN_LINES") for r in reasons) == 3     # open plan, garden, wash corner
    assert any(r.startswith("MERGED_SPACE") for r in reasons)                   # the pocket: a review decision
    assert AM.flag({"reason": next(r for r in reasons if r.startswith("ZONE_FROM"))}, drawing="d")["cause"] == "REVIEW"


def test_floor_reconciliation_follows_the_zones(hall):
    S, T = hall
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64)
    fa = AF.reconcile(S, M["rooms"], M["lines"], floor="GF")
    c = fa["categories_m2"]
    assert c["EXTERNAL"] == pytest.approx(T["GARDEN"], abs=1e-4)
    assert c["ROOM_FLOOR"] == pytest.approx(T["WASH_CORNER"], abs=1e-4)
    assert c["OPEN_PLAN_FLOOR"] == pytest.approx(T["OPEN_PLAN"], abs=1e-4)
    assert c["UNALLOCATED_MERGED"] == pytest.approx(T["POCKET"], abs=1e-4)
    assert all(ch["state"] == "BALANCED" for ch in fa["checks"])


def test_no_drawn_lines_no_split():
    ents, roles, T = AS.s5_zones()
    ents["segments"] = [s for s in ents["segments"] if s["layer"] != "A-FLOR"]
    S = _run(ents, roles)
    assert [r["state"] for r in S["zones"]] == ["DRAWN_LINES_DO_NOT_SEPARATE_THE_LABELS"]   # only the table is left
    m = [f for f in S["spaces"] if f["class"] == "MERGED"]
    assert len(m) == 1 and m[0]["area_m2"] == pytest.approx(T["face_m2"], abs=TOL)       # never an invented wall


def test_a_line_short_of_the_wall_does_not_close_a_zone():
    # no permissive snapping: the garden's right line stops 3 mm above the wall face, so it bounds nothing; the strip
    # opens onto the pocket and the drawn lines round both close ONE garden zone (the drawing does not separate them)
    ents, roles, T = AS.s5_zones()
    for s in ents["segments"]:
        if s["layer"] == "A-FLOR" and s["a"] == (9000.0, 200.0):
            s["a"] = (9000.0, 203.0)
    S = _run(ents, roles)
    rec, zones = _zones(S)
    garden = [z for z in zones if "GARDEN" in z[1]]
    assert garden == [("ROOM", ("GARDEN",), pytest.approx(T["GARDEN"] + T["POCKET"], abs=1e-4))]


def test_a_mixed_open_plan_is_left_alone():
    ents, roles, _ = AS.s5_zones()
    ents["texts"] = [t for t in ents["texts"] if t["value"] != "GARDEN"]
    ents["inserts"] = []
    S = _run(ents, roles)
    assert S["zones"] == [] and not any(f.get("zone") for f in S["faces"])


# ---- metamorphic: the same drawing under transformations measures the same zones
def _rot(deg, c=(6100.0, 4100.0)):
    a = math.radians(deg)

    def f(p):
        x, y = p[0] - c[0], p[1] - c[1]
        return (c[0] + x * math.cos(a) - y * math.sin(a) + 1.0e6, c[1] + x * math.sin(a) + y * math.cos(a) - 2.0e6)
    return f


@pytest.mark.parametrize("name,transform", [
    ("translate", lambda p: (p[0] + 3.5e6, p[1] - 1.25e6)),
    ("rotate_37", _rot(37.0)),
    ("rotate_90", _rot(90.0)),
    ("mirror", lambda p: (-p[0], p[1])),
])
def test_zones_invariant_under_rigid_motions(hall, name, transform):
    S0, _ = hall
    _, z0 = _zones(S0)
    ents, roles, _ = AS.s5_zones(transform)
    _, z1 = _zones(_run(ents, roles))
    assert [(c, k) for c, k, _ in z1] == [(c, k) for c, k, _ in z0]
    for (_, _, a1), (_, _, a0) in zip(z1, z0):
        assert a1 == pytest.approx(a0, abs=1e-5)                       # float round-off of the transform only


def test_zones_invariant_under_entity_order_and_subdivision_and_furniture(hall):
    S0, _ = hall
    _, z0 = _zones(S0)
    ents, roles, _ = AS.s5_zones()
    split = []
    for s in ents["segments"]:                                         # each floor line drawn as two collinear pieces
        if s["layer"] == "A-FLOR":
            m = (s["a"][0] + 0.37 * (s["b"][0] - s["a"][0]), s["a"][1] + 0.37 * (s["b"][1] - s["a"][1]))
            split += [dict(s, id=s["id"] + "a", b=m), dict(s, id=s["id"] + "b", a=m)]
        else:
            split.append(s)
    k = len(split)
    for a, b in (((1000, 6000), (1800, 6000)), ((1800, 6000), (1800, 6800)), ((1800, 6800), (1000, 6800)),
                 ((1000, 6800), (1000, 6000))):                         # an armchair: furniture, not a boundary
        k += 1
        split.append({"id": f"F{k}", "layer": "A-FURN", "a": (float(a[0]), float(a[1])), "b": (float(b[0]), float(b[1]))})
    random.Random(7).shuffle(split)
    ents["segments"] = split
    _, z1 = _zones(_run(ents, roles))
    assert z1 == z0


def test_s5_files_carry_no_client_identity():
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    pat = re.compile("YEARS" + r" 2013|7757-[A-Z]|[\u0600-\u06ff]{3,}|(?i:als[ey]?n[ya]?an)")
    for rel in ("tests/m9_s5/test_s5_zones.py", "tests/m9_s5/test_s5_ceilings_wp.py",
                "tests/m9_s5/test_s5_metamorphic_cad.py", "tests/m9_s5/test_s5_real_regression.py",
                "tools/arch_overlay.py", "tools/urban_boq_m9.py", "tools/arch_intake.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert not pat.search(text), rel
