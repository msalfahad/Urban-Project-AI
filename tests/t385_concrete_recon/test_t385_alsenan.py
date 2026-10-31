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
    assert all(f["closes"] for f in fams) and len(fams) == 9
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
