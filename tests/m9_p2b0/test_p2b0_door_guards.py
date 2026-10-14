"""Phase 2B-0 P1, findings F-18 / F-19 / F-20 / F-22: door release guards (ARCH_TAKEOFF_V2.2; door_model guards=True).
V2.1 (guards off) keeps its frozen classes and releases (characterization)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import p2b0_fixtures as FX                                    # noqa: E402
from engine.source import arch_measure as AM                  # noqa: E402
from engine.source import arch_rooms as AR                    # noqa: E402
from engine.source import door_model as DM                    # noqa: E402
from engine.source import robust_geometry as RG               # noqa: E402

U = 1e-3


def _model(guards):
    ents, roles = FX.door_guards()
    S = AR.spaces(ents, roles, U, region_id="R", tol="UNIT_RELATIVE", geom=RG.Geometry(U))
    FX.mark_stacked_shaft(S, (8200, 3200, 9800, 4800))
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64, documents=[])
    walls = [k for k, v in roles.items() if v == "WALL"]
    fm = DM.floor_model(S, M["rooms"], ents, U, "GF", wall_layers=walls, **({"guards": True} if guards else {}))
    texts = {t["id"]: t for t in ents["texts"]}
    ft = {f["face_id"]: [texts[i] for i in f.get("label_text_ids") or () if i in texts] for f in S["faces"]}
    return DM.building_model([("GF", fm)], {"GF": ents["texts"]}, {"GF": ft}, U, entrance_floor="GF",
                             **({"guards": True} if guards else {}))


def _by_width(model, cls=None):
    return sorted(round(e["structural_opening_width_m"], 3) for e in model["elements"]
                  if e["released"] and (cls is None or e["boq_class"] == cls))


@pytest.fixture(scope="module")
def v21():
    return _model(False)


@pytest.fixture(scope="module")
def v22():
    return _model(True)


def test_v2_1_releases_the_doubtful_doors(v21):
    """characterization: the kitchen door into the lobby is released PVC, the 0.90 / 1.00 m door is released
    aluminium, the shaft access is an ordinary passage."""
    assert _by_width(v21, DM.PVC) == [0.9, 0.9, 0.9] and _by_width(v21, DM.ALU) == [0.9]
    assert v21["lift_openings"] == [] and not v21.get("lift_candidates")


def test_a_door_with_an_open_width_review_is_held(v22):
    """F-18: the external door with a 0.90 m opening and a 1.00 m frame is not released."""
    held = [e for e in v22["elements"] if e.get("hold")]
    assert [round(e["structural_opening_width_m"], 3) for e in held] == [0.9]
    assert held[0]["released"] is False and held[0]["boq_class"] == DM.ALU
    assert _by_width(v22, DM.ALU) == []


def test_a_door_into_a_possibly_external_space_is_not_internal_pvc(v22):
    """F-20: the lobby has a 1.40 m doorless opening to the outside and no room word: the kitchen door into it is a
    class REVIEW; the two ordinary internal doors stay PVC."""
    rev = [e for e in v22["elements"] if e["class"] == DM.CLASS_REVIEW]
    assert len(rev) == 1 and "possibly external" in rev[0]["class_evidence"]
    assert _by_width(v22, DM.PVC) == [0.9, 0.9]


def test_a_stacked_shaft_opening_is_a_lift_entrance_candidate_never_confirmed(v22):
    """F-22: the 0.80 m access opening into the stacked shaft footprint is a candidate (REVIEW), not a confirmed lift
    door and not an ordinary passage."""
    cands = v22["lift_candidates"]
    assert len(cands) == 1 and cands[0]["width_m"] == pytest.approx(0.8)
    assert cands[0]["class"] == DM.LIFT_CANDIDATE and cands[0]["section"] == "REVIEW"
    assert v22["lift_openings"] == []


def test_every_withheld_door_has_a_finding(v22):
    """F-19: no door is withheld silently (held, class review, class unresolved, main candidate, provisional)."""
    assert v22["withheld_without_finding"] == []
    codes = {f["code"] for f in v22["findings"]}
    assert {"DOOR_HELD_WIDTH_REVIEW", "DOOR_CLASS_REVIEW", "LIFT_ENTRANCE_CANDIDATE"} <= codes


def test_the_main_entrance_stays_separate(v22):
    assert v22["main_entrance"]["state"] == "IDENTIFIED"
    main = [e for e in v22["elements"] if e["boq_class"] == DM.MAIN]
    assert len(main) == 1 and main[0]["structural_opening_width_m"] == pytest.approx(1.0)
    assert _by_width(v22, DM.ALU) == [] and main[0]["released"]


def test_no_height_is_invented(v22):
    for e in v22["elements"]:
        assert e["height"]["state"] == "BLOCKED" and e["area_m2"] is None


def test_the_phase_2a_door_fixture_keeps_its_truth_under_the_guards():
    """the P2A fixture (no doubtful door) gives the same released doors with and without the guards, and every
    withheld element is named by a finding."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m9_p2a"))
    import p2a_helpers as H
    ents = H.door_fixture()
    out = []
    for guards in (False, True):
        S = AR.spaces(ents, H.DOOR_ROLES, U, region_id="R", tol="UNIT_RELATIVE", geom=RG.Geometry(U))
        M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64, documents=[])
        walls = [k for k, v in H.DOOR_ROLES.items() if v == "WALL"]
        fm = DM.floor_model(S, M["rooms"], ents, U, "GF", wall_layers=walls, **({"guards": True} if guards else {}))
        texts = {t["id"]: t for t in ents["texts"]}
        ft = {f["face_id"]: [texts[i] for i in f.get("label_text_ids") or () if i in texts] for f in S["faces"]}
        out.append(DM.building_model([("GF", fm)], {"GF": ents["texts"]}, {"GF": ft}, U, entrance_floor="GF",
                                     **({"guards": True} if guards else {})))
    a, b = out
    assert [(e["element_id"], e["boq_class"], e["released"]) for e in a["elements"]] == \
        [(e["element_id"], e["boq_class"], e["released"]) for e in b["elements"]]
    assert b["withheld_without_finding"] == []


REAL = os.environ.get("URBAN_REAL_PLAN_DXF")


@pytest.mark.skipif(not (REAL and Path(REAL).exists()), reason="the reference plan is private (URBAN_REAL_PLAN_DXF)")
def test_the_reference_plan_door_holds():
    """acceptance review DR-02 / DR-03 / DR-04 / DR-06: 16 door sets stay released; the 0.9 / 1.0 m door and the
    kitchen door into the lobby are held; three stacked-shaft openings are lift-entrance candidates."""
    from tools import urban_boq_m9 as M9
    try:
        _room, arch, _E = M9.arch_compute(REAL, method="ARCH_TAKEOFF_V2.2")
    except M9.CompletenessFailed as ex:
        arch = ex.arch
    d = arch["doors"]
    rel = [e for e in d["elements"] if e["released"]]
    assert len(rel) == 16 and len(d["lift_candidates"]) == 3 and d["withheld_without_finding"] == []
