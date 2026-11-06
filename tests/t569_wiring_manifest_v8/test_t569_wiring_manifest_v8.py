"""T-569: WIRING MANIFEST V8 (research/agents_t569/WIRING_MANIFEST_V8.json) is recomputed from the candidate line index
and the merged pieces (T-564, T-565, T-567, T-560, T-570, T-568) and must equal the committed file. R-T569-1 (one face,
two layers): every plastered return face gets one HELD paint row on the same face id, bound beside 0 .. its plaster m2,
never 0 (fixture not Alsenan: 2 rooms, one return 0.30 x 2.80 = 0.840 m2); ESTIMATED is never shown as VERIFIED; a
range edge left out of the manifest is refused (R-T549-1 on a synthetic repository)."""

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t569"))
import manifest_v8 as M          # noqa: E402

A = pytest.approx


@pytest.fixture(scope="module")
def man():
    return M.build()


@pytest.fixture(scope="module")
def idx():
    return M.M1.line_index()


def _l(lid, code, el, cls="RELEASED", net=None, unit="m2", lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "element_id": el, "class": cls, "measured_net": net, "unit": unit,
            "held_low": lo, "held_high": hi, "binding": None, "unbound_records": []}


def _paint(face, cls="HELD", net=None):
    return _l("NEW:" + face, "FIN.PAINT", face + ":RETURN_PAINT", cls=cls, net=net)


# ---- the committed manifest and coverage ----------------------------------------------------------------------------
def test_committed_manifest_is_the_rebuild(man):
    assert M.dumps(man) == M.OUT_JSON.read_text(encoding="utf-8")


def test_every_merge_since_v7_is_covered(man):
    M.M2.check_sources(M.PIECES)
    assert man["coverage"] == {"range": ["33a5833f", "540bc99c"], "first_parent_merges": 6,
                               "covered": ["T-560", "T-564", "T-565", "T-567", "T-568", "T-570"]}
    assert set(M.NO_WIRING) | set(M.WIRING_SOURCES) == set(M.NEW_PIECES)
    assert man["candidate_lines_moved_v7_to_v8"] == 0 and man["candidate_files_touched"] == 0


def test_edited_v7_refused(monkeypatch):
    monkeypatch.setattr(M, "V7_PIN", "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.v7_manifest()


def test_adverse_wiring_source_declared_no_wiring_refused(monkeypatch):
    monkeypatch.setattr(M, "NO_WIRING", dict(M.NO_WIRING, **{"T-568": "moves nothing"}))
    with pytest.raises(M.ManifestError, match="disjoint"):
        M.build()


def _git(repo, *a):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env).stdout.decode().strip()


def _piece(repo, task, msg):
    _git(repo, "checkout", "-q", "-b", f"agents/task-{task}")
    (repo / task).write_text(task + "\n")
    _git(repo, "add", task)
    _git(repo, "commit", "-q", "-m", f"{task} work")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-ff", "-m", msg, f"agents/task-{task}")
    return _git(repo, "rev-parse", "HEAD")


def test_synthetic_range_edge_left_out_refused(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "work")
    (repo / "a").write_text("0\n")
    _git(repo, "add", "a")
    _git(repo, "commit", "-q", "-m", "base")
    base = _piece(repo, "T-940", "Merge agents/task-T-940: previous manifest (verified)")
    m = {"T-941": _piece(repo, "T-941", "Merge agents/task-T-941: first edge (verified)"),
         "T-942": _piece(repo, "T-942", "Merge agents/task-T-942: last edge (verified)")}
    p = {t: {"merge": s[:8]} for t, s in m.items()}
    assert M.M4.check_coverage(p, base, m["T-942"], repo)["covered"] == ["T-941", "T-942"]
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-942"):
        M.M4.check_coverage({"T-941": p["T-941"]}, base, m["T-942"], repo)
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-941"):
        M.M4.check_coverage({"T-942": p["T-942"]}, base, m["T-942"], repo)


# ---- R-T569-1 fixture (not Alsenan): 2 rooms, one plastered return ------------------------------------------------
def _fixture():
    return [
        _l("L-p1", "FIN.PLASTER", "GF-ROOM01:WALLS", net=30.0),
        _l("L-p2", "FIN.PAINT", "GF-ROOM01:WALLS", net=30.0),
        # one door return 0.30 deep x 2.80 developed (jambs + head) = 0.840 m2, plastered, no paint line
        _l("L-r1", "FIN.PLASTER", "GF-OPENING-D-901:door jambs and head", net=0.84),
        _l("L-p3", "FIN.PLASTER", "GF-ROOM02:WALLS", net=22.5),
        _l("L-p4", "FIN.PAINT", "GF-ROOM02:WALLS", net=22.5),
    ]


def test_fixture_one_return_one_held_paint_row():
    rf = M.return_faces(_fixture(), 1, M.Decimal("0.84"))
    assert rf["valued_faces"] == 1 and rf["held"] == []
    r = rf["valued"][0]
    assert r["face_id"] == "GF-OPENING-D-901:door jambs and head"
    assert r["plaster_m2"] == A(0.30 * 2.80) == A(0.840)
    p = r["paint_row"]
    assert p["item_code"] == "FIN.PAINT" and p["class"] == "HELD" and p["value"] is None
    assert p["bound_beside_m2"] == [0.0, A(0.840)]
    after = _fixture() + [_paint(r["face_id"])]
    assert M.check_pairs(after)


def test_adverse_return_with_plaster_and_no_paint_refused():
    with pytest.raises(M.ManifestError, match="UNPAIRED"):
        M.check_pairs(_fixture())
    face = "GF-OPENING-D-901:door jambs and head"
    with pytest.raises(M.ManifestError, match="UNPAIRED"):
        M.check_pairs(_fixture() + [_paint(face), _paint(face)])


def test_adverse_valued_return_paint_refused():
    face = "GF-OPENING-D-901:door jambs and head"
    with pytest.raises(M.ManifestError, match="valued before"):
        M.check_pairs(_fixture() + [_paint(face, cls="RELEASED", net=0.84)])
    with pytest.raises(M.ManifestError, match="valued before"):
        M.check_pairs(_fixture() + [_paint(face, net=0.0)])


def test_adverse_count_sum_and_existing_paint_return_refused():
    with pytest.raises(M.ManifestError, match="COUNT"):
        M.return_faces(_fixture(), 2)
    with pytest.raises(M.ManifestError, match="SUM"):
        M.return_faces(_fixture(), 1, M.Decimal("0.85"))
    with pytest.raises(M.ManifestError, match="exists"):
        M.return_faces(_fixture() + [_paint("GF-OPENING-D-901:door jambs and head")])
    with pytest.raises(M.ManifestError, match="not positive"):
        M.return_faces([dict(l, measured_net=0.0) if l["line_id"] == "L-r1" else l for l in _fixture()])


def test_held_plaster_return_stays_held_by_name_never_zero():
    lines = [dict(l, **{"class": "HELD", "measured_net": None}) if l["line_id"] == "L-r1" else l for l in _fixture()]
    rf = M.return_faces(lines)
    assert rf["valued"] == [] and len(rf["held"]) == 1
    assert rf["held"][0]["paint_row"]["bound_beside_m2"] is None and rf["held"][0]["paint_row"]["value"] is None


def test_adverse_estimated_shown_as_verified_refused(man):
    row = copy.deepcopy(man["dressing_class"])
    M.check_status(row)
    row["evidence_status"] = "VERIFIED"
    with pytest.raises(M.ManifestError, match="STATUS"):
        M.check_status(row)
    with pytest.raises(M.ManifestError, match="STATUS"):
        M.check_status({"id": "x", "basis": "ASSUMED - OWNER-APPROVED", "evidence_status": "VERIFIED by re-measure"})


def test_adverse_a08_neighbour_held_or_other_bed_scope_refused(idx, man):
    v7row = next(r for r in M.v7_manifest()["fix_rows"]["rows"] if r["closes"] == "F-T553-1")
    nb = man["dressing_class"]["expected_after"]["neighbour_floor_line"]
    held = dict(idx, **{nb: dict(idx[nb], item_code="FIN.FLOOR.FINISH_HELD")})
    with pytest.raises(M.ManifestError, match="HELD"):
        M.estimated_class(held, M.A08, v7row)
    wet = copy.deepcopy(v7row)
    for a in wet["expected_after"]["add"][1:]:
        a["item_code"] = "FIN.FLOOR.BED.WET"
    with pytest.raises(M.ManifestError, match="scope"):
        M.estimated_class(idx, M.A08, wet)


# ---- the candidate (Alsenan) ---------------------------------------------------------------------------------------
def test_candidate_26_return_faces_sum_23_070(man, idx):
    rp = man["return_paint"]
    assert rp["valued_faces"] == 26 and len(rp["held"]) == 4
    assert sum(r["plaster_m2"] for r in rp["valued"]) == A(23.07)
    assert sum(r["paint_row"]["bound_beside_m2"][1] for r in rp["valued"]) == A(23.07)
    for r in rp["valued"]:
        assert idx[r["plaster_line"]]["element_id"] == r["face_id"]
        assert r["paint_row"]["element_id"] == r["face_id"] + ":RETURN_PAINT" and r["paint_row"]["value"] is None
    assert len({r["face_id"] for r in rp["valued"] + rp["held"]}) == 30
    assert rp["fin_paint_released_before_m2"] == rp["fin_paint_released_after_m2"] == A(217.2081)


def test_dressing_label_estimated_quantity_unchanged(man):
    d = man["dressing_class"]
    e = d["expected_after"]
    assert e["m2"] == A(1.65 * 1.80) and e["m2_change"] == 0.0
    assert e["finish_class"] == "FIN.FLOOR.PORCELAIN (A08 ESTIMATED)" and "A08" in e["material_label_source"]
    assert e["item_code"] == "FIN.FLOOR.FINISH_HELD" and "NOT VERIFIED" in d["evidence_status"]
    assert d["label_independent_of_neighbour"] is True


def test_pier_returns_by_hand(man):
    p = man["pier_returns"]
    assert p["drawing_confirmed_m2"] == A(0.536522 * 4.20)
    assert p["held_bound_m2"] == [A(0.536522 * 0.10), A(0.536522 * 1.30)]
    assert p["internal_lines_taking_them"] == 0 and "HELD blank" in p["owner_line_state"]


def test_w17_by_hand(man):
    w = man["w17"]
    assert w["before"]["held_m2"] == [A(3.29 * 3.00), A(3.29 * 3.50)]
    assert w["expected_after"]["m2_change"] == A(9.870) and w["expected_after"]["settled_m2"] == A(23.285 + 9.870)
    assert w["cross_trade"]["moved_by_this_row"] == 0


def test_rebar_rows_held_blank_never_zero(man):
    rb = man["rebar_omission"]
    assert rb["lines"] == 6 and rb["kg_change_valued"] == 0.0
    assert all(r["expected_after"]["class"] == "HELD" and r["expected_after"]["value"] is None for r in rb["rows"])
    assert {r["concrete_item"] for r in rb["rows"]} == {"STR.CONC.DOME", "STR.CONC.BEAM", "STR.CONC.LIFT"}


def test_adverse_existing_rebar_line_refused(idx):
    k = next(iter(idx))
    bad = dict(idx, **{"X": dict(idx[k], line_id="X", item_code="STR.REBAR", element_id="LIFT_PIT:WALLS:BARS")})
    with pytest.raises(M.ManifestError, match="exists"):
        M.rebar_omission(bad)
