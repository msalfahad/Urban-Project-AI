"""Phase 2B-8: the sealed second-villa benchmark protocol URBAN_BLIND_V2 and its scorer
(research/urban_m9_p2b8/benchmark/blind_score_v2.py), on synthetic plans with hand-made references (the values below
are the hand truths of p2b8_fixtures / tests/m9_p2b7, rounded as a QS writes them - never read from an engine run).

    the protocol is sealed and covers every requested category, each metric SUPPORTED / PARTIAL / UNSUPPORTED
    an UNSUPPORTED metric is reported with its reference total, never scored and never zero
    a room the engine does not find is a SILENT omission (coverage < 1), never a zero error
    a review space's conditional quantity is FLAGGED (not an answer); its released ceiling is RELEASED
    a reference that consulted the engine, names an engine id, or repeats the engine's digits is refused
    a changed reference, a wrong salt, a run of another method or another drawing is refused
    acceptance is PROPOSED until the owner approves the criteria"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BENCH = ROOT / "research" / "urban_m9_p2b8" / "benchmark"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(BENCH))

ezdxf = pytest.importorskip("ezdxf")

import blind_score_v2 as B                                    # noqa: E402
import p2b8_fixtures as F                                     # noqa: E402
import p2b8_run as R                                          # noqa: E402

SALT = "synthetic-test-salt"
CATEGORIES = {"ROOM_FLOOR_AREAS", "WET_ROOMS", "CEILINGS", "DOORS", "WINDOWS_GLAZING", "PLASTER_PAINT", "SKIRTING",
              "WATERPROOFING", "WALL_RUNS_OPENINGS", "STAIRS"}


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b8_bench")


_cache = {}


def _run(work, name, make, method=R.V271):
    key = (name, method)
    if key not in _cache:
        src = make(work / f"{name}.dxf")
        _cache[key] = (src, R.run(src, work / f"o_{name}_{method[-5:].replace('.', '')}", roles=F.ROLES, facts=True,
                                  method=method))
    return _cache[key]


def _sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _reference(src, **over):
    """the CROSSING plan by hand: bath 1.677 x 3.00 = 5.031 m2, bedroom 2.173 x 3.00 = 6.519 m2, bath plaster
    9.354 x 3.00 - 0.80 x 2.10 = 26.382 m2, the 0.80 m external door (leaf 0.70), the 0.60 m window; a third room the
    plan does not have (to be a silent omission); door height, window height and glazing area (UNSUPPORTED)."""
    ref = {"schema": "URBAN_BLIND_V2_REFERENCE", "protocol": "URBAN_BLIND_V2", "protocol_sha256": B.protocol_sha(),
           "drawing_set": [{"file": Path(src).name, "sha256": _sha(src)}],
           "prepared": {"role": "INDEPENDENT_QS", "method": "QS_HAND_TAKEOFF", "engine_outputs_consulted": False,
                        "date": "2026-10-17", "note": "synthetic test reference, from the fixture coordinates"},
           "conventions": {"door_width": "structural opening as drawn"},
           "rooms": [{"ref_id": "R1", "floor": "GF", "name": "bath", "category": "BATHROOM", "ref_xy_m": [1.0, 1.7],
                      "quantities": {"FLOOR_AREA": 5.03, "CEILING_AREA": 5.03, "PLASTER_AREA": 26.38,
                                     "WET_FLOOR_AREA": 5.03, "WP_FLOOR_AREA": 5.03}},
                     {"ref_id": "R2", "floor": "GF", "name": "bedroom", "category": "DRY", "ref_xy_m": [3.0, 1.7],
                      "quantities": {"FLOOR_AREA": 6.52, "CEILING_AREA": 6.52}},
                     {"ref_id": "R3", "floor": "GF", "name": "store not in the plan", "category": "OTHER",
                      "ref_xy_m": [12.0, 12.0], "quantities": {"FLOOR_AREA": 4.0}}],
           "floors": [{"floor": "GF", "quantities": {"OPENING_COUNT": 2, "WINDOW_COUNT": 1, "DOOR_COUNT": {"ALU": 1}}}],
           "doors": [{"ref_id": "D1", "floor": "GF", "ref_xy_m": [1.4, 0.1],
                      "quantities": {"DOOR_OPENING_WIDTH": 0.80, "DOOR_CLASS": "ALU", "DOOR_LEAF_WIDTH": 0.70,
                                     "DOOR_HEIGHT": 2.10}}],
           "windows": [{"ref_id": "W1", "floor": "GF", "ref_xy_m": [4.3, 1.3],
                        "quantities": {"WINDOW_WIDTH": 0.60, "WINDOW_HEIGHT": 1.50, "GLAZING_AREA": 0.90}}],
           "stairs": []}
    ref.update(over)
    return ref


def _write(work, name, ref):
    p = work / f"{name}.json"
    p.write_text(json.dumps(ref, indent=1), encoding="utf-8")
    c = work / f"{name}.commit.json"
    c.write_text(json.dumps(B.commitment(p, SALT)), encoding="utf-8")
    return p, c


def _metric(rep, name):
    return next(m for c in rep["categories"] for m in c["metrics"] if m["metric"] == name)


def _score(work, name, ref, out):
    p, c = _write(work, name, ref)
    return B.run_score(p, c, SALT, out)


# --------------------------------------------------------------------------- the protocol

def test_the_protocol_is_sealed_and_complete():
    assert B.verify_seal() == []
    seal = json.loads((BENCH / "SEAL.json").read_text(encoding="utf-8"))
    assert set(seal["files"]) == set(B.SEALED)
    P = B.load_protocol()
    assert {c["category"] for c in P["categories"]} == CATEGORIES
    assert all(m["support"] in ("SUPPORTED", "PARTIAL", "UNSUPPORTED") for c in P["categories"] for m in c["metrics"])
    assert P["acceptance"]["status"] == "PROPOSED_PENDING_OWNER_APPROVAL"
    assert P["methods_frozen"] == ["ARCH_TAKEOFF_V2.7.1", "ARCH_TAKEOFF_V2.7"]


def test_a_changed_protocol_is_refused(work):
    d = work / "tampered"
    shutil.copytree(BENCH, d, ignore=shutil.ignore_patterns("__pycache__"))
    p = d / "URBAN_BLIND_V2_PROTOCOL.json"
    P = json.loads(p.read_text(encoding="utf-8"))
    P["tolerances"]["m2"]["rel"] = 0.10
    p.write_text(json.dumps(P), encoding="utf-8")
    assert [x["code"] for x in B.verify_seal(d)] == ["PROTOCOL_NOT_SEALED"]


# --------------------------------------------------------------------------- scoring

def test_scoring_a_hand_reference(work):
    src, out = _run(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    rep = _score(work, "ref_ok", _reference(src), out)
    assert "refused" not in rep, rep.get("refused")
    fa = _metric(rep, "FLOOR_AREA")
    rows = {r["ref_id"]: r for r in fa["rows"]}
    assert rows["R1"]["outcome"] == "RELEASED" and rows["R1"]["within_tolerance"]
    assert rows["R2"]["outcome"] == "RELEASED" and rows["R2"]["within_tolerance"]
    pl = _metric(rep, "PLASTER_AREA")["rows"][0]
    assert pl["outcome"] == "RELEASED" and abs(pl["engine"] - 26.382) < 1e-6 and pl["within_tolerance"]
    dw = _metric(rep, "DOOR_OPENING_WIDTH")["rows"][0]
    assert dw["outcome"] == "RELEASED" and abs(dw["engine"] - 0.80) < 1e-6
    assert _metric(rep, "DOOR_CLASS")["rows"][0]["engine"] == "ALU"
    assert abs(_metric(rep, "DOOR_LEAF_WIDTH")["rows"][0]["engine"] - 0.70) < 1e-6
    assert abs(_metric(rep, "WINDOW_WIDTH")["rows"][0]["engine"] - 0.60) < 1e-6
    assert _metric(rep, "OPENING_COUNT")["rows"][0]["engine"] == 2
    assert _metric(rep, "DOOR_COUNT")["rows"][0]["engine"] == 1


def test_unsupported_is_reported_never_zero(work):
    src, out = _run(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    rep = _score(work, "ref_ok", _reference(src), out)
    for name, total in (("DOOR_HEIGHT", 2.10), ("WINDOW_HEIGHT", 1.50), ("GLAZING_AREA", 0.90)):
        m = _metric(rep, name)
        assert m["status"] == "UNSUPPORTED" and m["reference_items"] == 1 and abs(m["reference_total"] - total) < 1e-9
        assert not {"rows", "coverage_qty", "wape_released", "total_error_pct", "within_tolerance"} & set(m)
    st = _metric(rep, "HANDRAIL_LM")
    assert st["status"] == "UNSUPPORTED" and st["reference_items"] == 0 and st["reference_total"] is None


def test_a_room_the_engine_misses_is_silent_not_zero(work):
    src, out = _run(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    fa = _metric(_score(work, "ref_ok", _reference(src), out), "FLOOR_AREA")
    r3 = next(r for r in fa["rows"] if r["ref_id"] == "R3")
    assert r3["outcome"] == "SILENT" and r3["engine"] is None and "error" not in r3
    assert fa["outcomes"]["SILENT"] == 1 and fa["coverage_qty"] < 1
    assert abs(fa["coverage_qty"] - (5.03 + 6.52) / (5.03 + 6.52 + 4.0)) < 1e-6


def test_acceptance_is_proposed_only(work):
    src, out = _run(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    rep = _score(work, "ref_ok", _reference(src), out)
    assert rep["acceptance_status"] == "PROPOSED_PENDING_OWNER_APPROVAL"
    accs = {m["acceptance"] for c in rep["categories"] for m in c["metrics"] if "acceptance" in m}
    assert accs and all(a.startswith("PROPOSED_") for a in accs)
    assert _metric(rep, "FLOOR_AREA")["acceptance"] == "PROPOSED_FAIL"          # the silent store


def test_a_review_space_answers_conditionally(work):
    """the basin lobby (10.20 m2): its ceiling is released (classification-invariant), its wet floor is a conditional
    scenario quantity - FLAGGED, not an answer and not a silent omission."""
    src, out = _run(work, "WC_BASIN", lambda p: F.wc_plan(p, "BASIN"))
    ref = _reference(src, rooms=[{"ref_id": "L1", "floor": "GF", "name": "lobby", "category": "BATHROOM",
                                  "ref_xy_m": [4.0, 1.5],
                                  "quantities": {"CEILING_AREA": 10.20, "WET_FLOOR_AREA": 10.20}}],
                     doors=[], windows=[], floors=[])
    rep = _score(work, "ref_lobby", ref, out)
    assert "refused" not in rep, rep.get("refused")
    ce = _metric(rep, "CEILING_AREA")["rows"][0]
    assert ce["outcome"] == "PROVISIONAL" and ce["provisional_within_tolerance"]   # every ceiling: type not in a plan
    wf = _metric(rep, "WET_FLOOR_AREA")["rows"][0]
    assert wf["outcome"] == "FLAGGED" and wf["engine"] is None


# --------------------------------------------------------------------------- refusals

@pytest.mark.parametrize("mutate,code", [
    (lambda r: r["prepared"].update(engine_outputs_consulted=True), "REFERENCE_ENGINE_DERIVED"),
    (lambda r: r["prepared"].update(method="ENGINE_EXPORT"), "REFERENCE_METHOD_NOT_ALLOWED"),
    (lambda r: r["rooms"][0].update(name="bath B1-RA1B2C3"), "REFERENCE_LEAKAGE_MARKER"),   # an engine room id form
    (lambda r: r["prepared"].update(note="copied from ARCH_TAKEOFF_V2.7.1 BOQ_LINES"), "REFERENCE_LEAKAGE_MARKER"),
    (lambda r: r.update(protocol_sha256="0" * 64), "REFERENCE_PROTOCOL_MISMATCH"),
])
def test_a_reference_that_is_not_independent_is_refused(work, mutate, code):
    src, out = _run(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    ref = _reference(src)
    mutate(ref)
    rep = _score(work, f"ref_bad_{code}", ref, out)
    assert code in [x["code"] for x in rep["refused"]]


def test_a_reference_repeating_the_engine_digits_is_refused(work):
    """the B10 bathroom's quantities copied with the engine's six decimals (area 13.021882 ...): refused."""
    src, out = _run(work, "B10", F.F7.arc_room)
    lines = R.lines(out)
    room = next(r for r in R.rooms(out) if r["name_en"].startswith("Bath"))
    q = {"FLOOR_AREA": room["area_m2"]}
    for metric, item in (("CEILING_AREA", "FIN.CEILING"), ("WET_FLOOR_AREA", "FIN.FLOOR.WET_TILE"),
                         ("WP_FLOOR_AREA", "FIN.WP.FLOOR"), ("WP_UPTURN_AREA", "FIN.WP.WALL_UPTURN"),
                         ("PLASTER_AREA", "FIN.PLASTER"), ("WALL_CERAMIC_AREA", "FIN.WALL.TILE")):
        v = sum(ln["measured_net"] or 0 for ln in lines if ln["item_code"] == item and
                ln["location"]["room_id"] == room["room_id"])
        if v:
            q[metric] = v
    ref = _reference(src, rooms=[{"ref_id": "R1", "floor": "GF", "name": "bath", "category": "BATHROOM",
                                  "ref_xy_m": [2.0, 1.7], "quantities": q}], doors=[], windows=[], floors=[])
    rep = _score(work, "ref_digits", ref, out)
    assert [x["code"] for x in rep["refused"]] == ["REFERENCE_MATCHES_ENGINE_DIGITS"]


def test_commitment_and_run_checks(work):
    src, out = _run(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    p, c = _write(work, "ref_commit", _reference(src))
    assert "refused" not in B.run_score(p, c, SALT, out)
    assert [x["code"] for x in B.run_score(p, c, "another salt", out)["refused"]] == ["COMMITMENT_MISMATCH"]
    ref = json.loads(p.read_text(encoding="utf-8"))
    ref["rooms"][0]["quantities"]["FLOOR_AREA"] = 5.50                            # changed after the commitment
    p.write_text(json.dumps(ref, indent=1), encoding="utf-8")
    assert [x["code"] for x in B.run_score(p, c, SALT, out)["refused"]] == ["COMMITMENT_MISMATCH"]
    _src, out26 = _run(work, "CROSSING", lambda q: F.door_plan(q, "CROSSING"), method=R.V26)
    p2, c2 = _write(work, "ref_commit2", _reference(src))
    assert [x["code"] for x in B.run_score(p2, c2, SALT, out26)["refused"]] == ["RUN_METHOD_NOT_FROZEN"]
    _s, other = _run(work, "PLAIN", lambda q: F.door_plan(q, "PLAIN"))
    assert [x["code"] for x in B.run_score(p2, c2, SALT, other)["refused"]] == ["RUN_DRAWING_NOT_IN_SET"]
