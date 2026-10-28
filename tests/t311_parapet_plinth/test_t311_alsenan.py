"""T-311 on the development villa: the committed ledgers rebuild byte for byte from merged ledgers (T-172, T-305) and
the committed candidate extract (own V3.0.19 run); no drawing needed. Pins the closures and the ownership."""
import csv
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t311"
sys.path.insert(0, str(HERE))
import t311_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def files():
    return A.outputs()


@pytest.fixture(scope="module")
def summ(files):
    return json.loads(files["summary.json"])


def rows(files, name):
    return list(csv.DictReader(files[name].splitlines()))


def test_rebuild_byte_identical(files):
    for n, t in files.items():
        assert (HERE / n).read_text(encoding="utf-8") == t, n


def test_every_run_and_segment_once(summ, files):
    pr = rows(files, "PARAPET_RUN_LEDGER_T311.csv")
    assert len({(r["chain"], r["side"]) for r in pr}) == len(pr) == summ["parapet_runs"] == 24
    pl = rows(files, "PLINTH_SEGMENT_LEDGER_T311.csv")
    assert len(pl) == summ["plinth_segments"] == 29


def test_closures_named(files, summ):
    for c in rows(files, "CLOSURE_T311.csv"):
        if c["check"].startswith("upturn line"):
            assert float(c["this_ledger_lo"]) <= float(c["reference_lo"]) + 1e-6, c["check"]
        else:
            assert abs(float(c["residual_lo"])) < 1e-3 and abs(float(c["residual_hi"])) < 1e-3, c["check"]
            if abs(float(c["residual_lo"])) > 1e-6:
                assert c["cause"] != "none", c["check"]
    assert summ["closure_max_abs_residual"] < 1e-3


def test_one_owner_per_component_no_double(files, summ):
    cs = rows(files, "COMPONENT_OWNER_T311.csv")
    assert len({c["component"] for c in cs}) == len(cs)
    assert summ["double"] == 0
    assert {c["ledger_state"] for c in cs} <= {"IN_LINE", "NO_LINE", "OTHER_LINE"}


def test_material_held_never_zero_and_bounded(files, summ):
    lo, hi = summ["parapet_concrete_m3"]
    assert 0 < lo < hi
    for c in rows(files, "COMPONENT_OWNER_T311.csv"):
        if c["status"] == "HELD" and c["qty_lo"] != "":
            assert float(c["qty_hi"]) > 0, c["component"]
        if "reinforcement" in c["component"] or "substrate split" in c["component"]:
            assert c["qty_lo"] == "" and c["status"] == "HELD"


def test_parapet_concrete_lower_bound_is_the_upstand(files):
    for r in rows(files, "PARAPET_RUN_LEDGER_T311.csv"):
        cl, t = float(r["centreline_m"]), float(r["t_m"])
        assert abs(float(r["concrete_m3_lo"]) - 0.30 * t * cl) < 1e-5, r["side"]


def test_plinth_house_ground_beam_top(files):
    for r in rows(files, "PLINTH_SEGMENT_LEDGER_T311.csv"):
        if r["zone"] == "house":
            assert r["gb_top_m"] == "0.950000" and r["ffl_m"] == "1.000000"
            assert abs(float(r["wall_course_m2"]) - 0.05 * float(r["length_m"])) < 1e-6
        if r["zone"] == "passage":
            assert r["gb_top_m"] == "" and r["concrete_face_m2_lo"] == ""


def test_candidate_identity_is_the_record(summ):
    c = summ["candidate"]
    assert (c["lines_file"], c["lines_json_sha256_8"], c["lines_csv_sha256_8"], c["lines_total"]) == (
        "V3_0_19_BOQ_LINES.json", "b35475bf", "ef63b73b", 3705)


def test_upstand_mentions_are_not_parapets(summ):
    assert len(summ["concrete_lines_naming_an_upstand_not_parapet"]) == 2
    assert all(x["item_code"] == "STR.CONC.COLUMN" for x in summ["concrete_lines_naming_an_upstand_not_parapet"])
