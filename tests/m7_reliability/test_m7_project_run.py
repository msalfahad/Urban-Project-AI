"""M7 project manifest runner (tools/urban_project_run): the blind protocol is enforced by the tool - the drawing
revision is checked, the run is frozen before the reference BOQ is opened, a rebuild is byte-identical, a changed
output or a different reference refuses the comparison, and the comparison never rewrites the run. The reference BOQ
here is the synthetic generator's own design truth (never an engine output)."""

from __future__ import annotations

import json

import pytest

ezdxf = pytest.importorskip("ezdxf")

from tools import m7_evaluate as EV                         # noqa: E402
from tools import synthetic_villa as SV                     # noqa: E402
from tools import urban_project_run as PR                   # noqa: E402


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    w = tmp_path_factory.mktemp("m7_project")
    dxf = SV.generate(w, 3)
    T = json.loads((w / "villa_3.truth.json").read_text(encoding="utf-8"))
    T["m6"] = {"elements": [], "variant": {}}
    truth, _ = EV.design_truth(3, T, "TOTAL_DEPTH")
    rows = ["FAMILY,STOREY,QUANTITY,UNIT,ITEM_REF"] + [f"{f},{s},{v:.4f},m3,R{k}"
                                                       for k, ((f, s), v) in enumerate(sorted(truth.items()))]
    (w / "ref.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    PR.init(w / "manifest.json", project="SYN-3", structural=[dxf], profile=w / "villa_3.profile.json",
            reference=w / "ref.csv", rate=26.5)
    rec = PR.run(w / "manifest.json", w / "out")
    return w, rec


def test_run_is_frozen_blind_and_reproducible(project):
    w, rec = project
    assert rec["reference_opened_before_freeze"] is False and rec["CANDIDATE_GEOMETRY_HASH"]
    assert set(rec["outputs_sha256"]) == {"ITEMS.csv", "RELEASE_REGISTER.csv", "INDEPENDENT_CHECKS.csv",
                                          "COMPLETENESS_FINDINGS.csv", "SUMMARY.json"}
    S = json.loads((w / "out" / "SUMMARY.json").read_text(encoding="utf-8"))
    assert S["conventions_set"] == "URBAN_M7_GENERIC_CONVENTIONS_V5" and S["reference_opened"] is False
    assert S["release_totals"]["CONCRETE"]["released"]["n"] == 0          # nothing is released without an engineer
    assert all(PR.check(w / "manifest.json", w / "out").values())
    with pytest.raises(PR.ProtocolError):                                  # a frozen folder is never overwritten
        PR.run(w / "manifest.json", w / "out")


def test_compare_after_the_freeze_only_and_never_edits_the_run(project, tmp_path):
    w, rec = project
    before = {n: (w / "out" / n).read_text(encoding="utf-8") for n in rec["outputs_sha256"]}
    res = PR.compare(w / "manifest.json", w / "out")
    st = {(r["FAMILY"], r["STOREY"]): r["STATE"] for r in res["rows"]}
    assert st[("FOOTINGS", "FOUNDATION")] == st[("COLUMNS", "GF")] == st[("SLABS", "1F")] == "MATCH"
    assert st[("BEAMS", "1F")] in ("MATCH", "EXPLAINED_BY_UNRESOLVED")
    assert "ENGINE_OVER" not in st.values() and "ENGINE_SHORT" not in st.values()
    assert {n: (w / "out" / n).read_text(encoding="utf-8") for n in rec["outputs_sha256"]} == before
    assert json.loads((w / "out" / "COMPARE_RECORD.json").read_text())["run_freeze_hash"] == \
        rec["CANDIDATE_GEOMETRY_HASH"]


def test_the_protocol_refuses(project, tmp_path):
    w, rec = project
    m = json.loads((w / "manifest.json").read_text(encoding="utf-8"))
    bad = dict(m, drawings=[dict(m["drawings"][0], sha256="0" * 64)])      # another revision of the drawing
    (tmp_path / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(PR.ProtocolError, match="revision"):
        PR.run(tmp_path / "bad.json", tmp_path / "o1")
    with pytest.raises(PR.ProtocolError, match="frozen"):                 # no freeze, no reconciliation
        PR.compare(w / "manifest.json", tmp_path / "nothing")
    import shutil
    shutil.copytree(w / "out", tmp_path / "edited")
    p = tmp_path / "edited" / "ITEMS.csv"
    p.write_text(p.read_text(encoding="utf-8").replace("PROVISIONAL", "VERIFIED", 1), encoding="utf-8")
    with pytest.raises(PR.ProtocolError, match="changed after the freeze"):
        PR.compare(w / "manifest.json", tmp_path / "edited")
    other = dict(m, reference_boq=dict(m["reference_boq"], sha256="f" * 64))
    (tmp_path / "other.json").write_text(json.dumps(other), encoding="utf-8")
    shutil.copytree(w / "out", tmp_path / "copy")
    with pytest.raises(PR.ProtocolError, match="reference"):
        PR.compare(tmp_path / "other.json", tmp_path / "copy")
