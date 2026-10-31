"""T-385 development-villa checks. The input carries the freelancer's row values (private workbook content), so it lives
only in .work/private: the closure checks run where that private input exists and skip elsewhere; the guards always run."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t385"
sys.path.insert(0, str(HERE))
import t385_alsenan as A  # noqa: E402
import t385_rules as R  # noqa: E402

PRIVATE = A.INPUT


def test_no_private_table_in_the_repository():
    # the builder's input and outputs print freelancer values: none of them may sit in the research folder
    for name in ("ALSENAN_T385_INPUT.json", "RECON_T385.csv", "FAMILIES_T385.csv", "summary_t385.json"):
        assert not (HERE / name).exists(), name


def test_out_inside_the_repository_refused(tmp_path):
    if not PRIVATE.exists():
        pytest.skip("private input absent (Drive copies not prepared in this checkout)")
    with pytest.raises(SystemExit):
        A.main(["--out", str(HERE / "x")])


def test_pool_walls_split_rule_synthetic():
    # synthetic (not the development villa): engine 2.400 m3 = mean 10.00 m x 0.20 x 1.20; his row 10.50 x 1.60 x 0.20
    sp = A.pool_walls_split(2.4, [{"dims": [10.5, 1.6, 0.2]}])
    assert [x["m3"] for x in sp] == [pytest.approx(-0.8), pytest.approx(-0.16)]
    for c in sp:
        R.check_cause_text(c["cause"])
    with pytest.raises(SystemExit):                       # older input without his dimensions
        A.pool_walls_split(2.4, [{"m3": 3.36}])
    with pytest.raises(SystemExit):                       # his thickness is not the drawn wall: split does not apply
        A.pool_walls_split(2.4, [{"dims": [10.5, 1.6, 0.25]}])


def test_every_component_has_a_physical_cause_and_a_known_verdict():
    for c in A.COMPONENTS:
        R.check_cause_text(c[6])
        assert c[5] in R.CAUSE_CLASSES and c[7] in R.VERDICTS, c[0]


@pytest.fixture(scope="module")
def built():
    if not PRIVATE.exists():
        pytest.skip("private input absent (Drive copies not prepared in this checkout)")
    return A.build(A.load())


def test_candidate_of_record(built):
    _, _, doc = built
    assert doc["candidate"] == "ARCH_TAKEOFF_V3.0.29"
    assert doc["candidate_lines_json_sha256"].startswith("6b5dc44f")


def test_every_family_closes_and_every_line_bound_once(built):
    rows, fams, doc = built
    assert all(f["bookkeeping_closes"] for f in fams) and len(fams) == 9
    assert sum(r["engine_lines"] for r in rows) == len(doc["concrete_lines"]) == 525


def test_held_is_never_agreement(built):
    rows, _, _ = built
    for r in rows:
        if r["held_lines"]:
            assert r["verdict"] in ("HELD", "UNRESOLVED"), r["id"]
        if r["verdict"] == "AGREE":
            assert abs(r["contribution_m3"]) <= R.TOL


def test_engine_side_figures(built):
    # engine-side figures only (the freelancer side stays in the private table)
    rows, fams, _ = built
    f = {x["family"]: x for x in fams}
    assert f["CONC.FOOTING"]["engine_valued_m3"] == pytest.approx(67.6945)       # boundary band downgraded out
    assert f["CONC.BLINDING"]["engine_valued_m3"] == 0.0                         # footing layer downgraded out
    assert f["CONC.SLAB"]["engine_valued_m3"] == pytest.approx(60.280158)
    assert f["CONC.BEAM"]["engine_valued_m3"] == pytest.approx(66.317879)
    r = {x["id"]: x for x in rows}
    assert r["FT-F3"]["engine_valued_m3"] == pytest.approx(1.344) and r["FT-F3"]["engine_lines"] == 2
    assert r["PL-WALLS"]["engine_valued_m3"] == pytest.approx(2.828071)
    assert r["BW-BAND"]["held_high_m3"] is None and r["BW-BAND"]["held_audit_engine_m3"] == pytest.approx(7.2204)


def test_r2_cause_closure(built):
    rows, fams, _ = built
    r = {x["id"]: x for x in rows}
    for x in rows:
        assert x["traced_m3"] + x["held_named_m3"] + x["unexplained_m3"] == pytest.approx(x["contribution_m3"], abs=1e-6)
        if x["verdict"] == "UNRESOLVED":
            assert x["traced_m3"] == 0.0 and x["unexplained_m3"] == x["contribution_m3"], x["id"]
        if x["verdict"] == "HELD":
            assert x["traced_m3"] == 0.0 and x["unexplained_m3"] == 0.0, x["id"]
    w = r["PL-WALLS"]
    assert "DEPTH -0.942690" in w["cause_split"]                 # 2.356726 m2 band x 0.40 base (engine side)
    assert w["unexplained_m3"] < -R.TOL                          # part of his height no drawn level traces
    for f in fams:
        assert f["unexplained_m3"] == pytest.approx(f["unresolved_m3"] + f["untraced_remainder_m3"]
                                                    + f["bookkeeping_remainder_m3"], abs=1e-6)
    n_unres = sum(1 for x in rows if x["verdict"] == "UNRESOLVED")
    assert n_unres == 11
    assert sum(1 for f in fams if f["cause_closes"]) < len(fams)   # never 'unexplained 0.000' by construction
