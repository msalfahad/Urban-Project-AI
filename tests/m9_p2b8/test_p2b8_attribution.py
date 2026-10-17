"""Phase 2B-8 acceptance: BOQ change attribution with independent verification (tools/arch_change_verify.py).

A correction record explaining why a quantity changed is not proof that the new quantity is right. Every difference
between two runs of one drawing is classified:
    VERIFIED              a correction record covers it AND an independent reading of the drawing (tools/indep_reader:
                          ezdxf + shapely + arithmetic, no engine module) gives the new value
    EXPLAINED_UNVERIFIED  a record covers it; no independent check exists for that item yet
    CONTRADICTED          a record covers it but the independent value disagrees
    UNEXPLAINED           no record covers it
and a floor-wide record (layer roles, column shapes) covers only the locations whose drawn entities it touches.

Truth: the hand derivations of tests/m9_p2b7 and p2b8_fixtures (CROSSING bath 26.382 m2 plaster etc.)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

ezdxf = pytest.importorskip("ezdxf")
pytest.importorskip("shapely")

import p2b8_fixtures as F                                     # noqa: E402
import p2b8_run as R                                          # noqa: E402

TOOL = ROOT / "tools" / "arch_change_verify.py"


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b8_attr")


def _verify(before, after, dxf, out, facts=True):
    argv = [sys.executable, "-I", str(TOOL), "--before", str(before), "--after", str(after), "--dxf", str(dxf),
            "--out", str(out)]
    if facts:
        argv += ["--facts", str(Path(after).parent / "facts.json")]
    r = subprocess.run(argv, capture_output=True, text=True)
    assert r.returncode in (0, 1), r.stdout[-1500:] + r.stderr[-1500:]
    return json.loads(Path(out).read_text(encoding="utf-8")), r.returncode


_cache = {}


def _pair(work, name, make, m_before=R.V26, m_after=R.V271):
    if name not in _cache:
        src = make(work / f"{name}.dxf")
        b = R.run(src, work / f"o_{name}_before", roles=F.ROLES, facts=True, method=m_before)
        a = R.run(src, work / f"o_{name}_after", roles=F.ROLES, facts=True, method=m_after)
        _cache[name] = (src, b, a)
    return _cache[name]


def _by(rep):
    return {(d["item_code"], d["location"]): d for d in rep["differences"]}


def test_door_narrowing_is_verified_by_an_independent_takeoff(work):
    """CROSSING, V2.6 -> V2.7.1: every difference is the door's opening (DOOR_OPENING) and an independent reading of
    the drawing reproduces the new values: the bath's plaster 9.354 x 3.00 - 0.80 x 2.10 = 26.382 m2, wall tile
    9.354 x 2.40 - 1.68 = 20.7696 m2, skirting 9.354 - 0.80 = 8.554 m (the door 0.80 m read from its own jamb lines)."""
    src, b, a = _pair(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    rep, code = _verify(b, a, src, work / "v_crossing.json")
    assert code == 0 and rep["summary"]["UNEXPLAINED"] == 0 and rep["summary"]["CONTRADICTED"] == 0
    by = _by(rep)
    for item, want in (("FIN.PLASTER", 26.382), ("FIN.WALL.TILE", 20.7696), ("FIN.SKIRTING", 8.554)):
        d = by[(item, "Bathroom / W.C.")]
        assert d["status"] == "VERIFIED" and "DOOR_OPENING" in d["kinds"], d
        assert abs(d["verification"]["independent"] - want) < 1e-3 and abs(d["after"] - want) < 1e-3
    assert rep["summary"]["VERIFIED"] >= 3


def test_curved_band_is_verified_by_the_arc_census(work):
    """B10, V2.6 -> V2.7.1: the wall run grows by the curved band, 2.6 x 1.287002 = 3.346206 m on the mid radius,
    which the independent arc census of the raw ARC / bulge entities reproduces."""
    src, b, a = _pair(work, "B10", F.F7.arc_room)
    rep, _ = _verify(b, a, src, work / "v_b10.json")
    run = [d for d in rep["differences"] if d["item_code"] == "ARCH.WALL_RUN"]
    assert len(run) == 1 and run[0]["status"] == "VERIFIED"
    assert abs(run[0]["delta"] - 3.346206) < 1e-5
    assert abs(run[0]["verification"]["independent_delta"] - 3.346206) < 1e-4


def test_review_release_is_verified_by_an_independent_face(work):
    """the basin lobby, V2.7 -> V2.7.1: the one difference is the released ceiling 10.20 m2, and the independent face
    of the raw wall lines around the space is 3.40 x 3.00 = 10.20 m2."""
    src, b, a = _pair(work, "WC_BASIN", lambda p: F.wc_plan(p, "BASIN"), m_before=R.V27)
    rep, code = _verify(b, a, src, work / "v_wc.json")
    assert code == 0 and len(rep["differences"]) == 1
    d = rep["differences"][0]
    assert d["item_code"] == "FIN.CEILING" and d["kinds"] == ["REVIEW_INVARIANT_RELEASE"]
    assert d["status"] == "VERIFIED" and abs(d["verification"]["independent"] - 10.2) < 1e-3


def test_wet_evidence_is_verified_by_an_independent_fixture_census(work):
    """the basin lobby, V2.6 -> V2.7.1: V2.6's wet finishes of the lobby go (WET_EVIDENCE); the independent census of
    the raw inserts and sanitary-layer lines inside the space finds one basin block and nothing else - the evidence
    the decision states."""
    src = F.wc_plan(work / "WC_B2.dxf", "BASIN")
    b = R.run(src, work / "o_wc_b2_26", roles=F.ROLES, facts=True, method=R.V26)
    a = R.run(src, work / "o_wc_b2_271", roles=F.ROLES, facts=True, method=R.V271)
    rep, _ = _verify(b, a, src, work / "v_wc2.json")
    wet = [d for d in rep["differences"] if "WET_EVIDENCE" in d["kinds"]]
    assert wet and all(d["status"] == "VERIFIED" for d in wet), [d for d in wet if d["status"] != "VERIFIED"]
    ev = wet[0]["verification"]
    assert ev["method"] == "INDEPENDENT_FIXTURE_CENSUS" and ev["independent"] == {"basins": 1, "water_closets": 0,
                                                                                   "showers_baths": 0,
                                                                                   "sanitary_layer_lines": 0}


def test_a_perturbed_quantity_is_contradicted(work):
    """the CROSSING V2.7.1 run with the bath's plaster raised by 0.50 m2 by hand: the record still explains a change
    there, but the independent value (26.382) disagrees - CONTRADICTED, exit 1."""
    src, b, a = _pair(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    bad = work / "o_crossing_bad"
    shutil.copytree(a, bad)
    p = bad / "BOQ_LINES.json"
    L = json.loads(p.read_text(encoding="utf-8"))
    for ln in L:
        if ln["item_code"] == "FIN.PLASTER" and ln["location"]["room_name_en"].startswith("Bathroom"):
            ln["measured_net"] = round(ln["measured_net"] + 0.5, 6)
    p.write_text(json.dumps(L), encoding="utf-8")
    rep, code = _verify(b, bad, src, work / "v_bad.json")
    d = _by(rep)[("FIN.PLASTER", "Bathroom / W.C.")]
    assert d["status"] == "CONTRADICTED" and code == 1


def test_an_emptied_log_is_unexplained(work):
    """the same V2.7.1 output with its correction log emptied: every difference UNEXPLAINED, exit 1."""
    src, b, a = _pair(work, "CROSSING", lambda p: F.door_plan(p, "CROSSING"))
    bare = work / "o_crossing_bare"
    shutil.copytree(a, bare)
    p = bare / "CORRECTIONS_V2_7.json"
    j = json.loads(p.read_text(encoding="utf-8"))
    j["corrections"] = []
    p.write_text(json.dumps(j), encoding="utf-8")
    rep, code = _verify(b, bare, src, work / "v_bare.json")
    assert code == 1 and rep["summary"]["UNEXPLAINED"] == len(rep["differences"]) > 0


def test_a_layer_role_record_covers_only_its_own_entities(work):
    """PLAIN with every role inferred (V2.6 reads the exploded door's layer as OTHER, V2.7.1 as DOOR: a LAYER_ROLE
    record) and an unrelated quantity - the wall run - raised by hand in the after run: the layer record explains the
    locations its door entities bound, never the walls - the wall run stays UNEXPLAINED."""
    src = F.door_plan(work / "PLAIN_X.dxf", "PLAIN")              # no roles given: the door layer is inferred
    b = R.run(src, work / "o_px_26", facts=True, method=R.V26)
    a = R.run(src, work / "o_px_271", facts=True, method=R.V271)
    hacked = work / "o_px_hacked"
    shutil.copytree(a, hacked)
    p = hacked / "BOQ_LINES.json"
    L = json.loads(p.read_text(encoding="utf-8"))
    walls = [ln for ln in L if ln["item_code"] == "ARCH.WALL_RUN"]
    assert walls
    walls[0]["measured_net"] = round(walls[0]["measured_net"] + 1.0, 6)
    p.write_text(json.dumps(L), encoding="utf-8")
    rep, code = _verify(b, hacked, src, work / "v_px.json")
    w = [d for d in rep["differences"] if d["item_code"] == "ARCH.WALL_RUN"]
    assert len(w) == 1 and w[0]["status"] == "UNEXPLAINED" and code == 1
