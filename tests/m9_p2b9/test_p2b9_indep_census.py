"""Phase 2B-9 independent verification: the reader's own wall-stub censuses (tools/indep_reader: ezdxf + shapely +
arithmetic, no engine module) and the change verifier's two new checks (tools/arch_change_verify):

    INDEPENDENT_STUB_CENSUS   ARCH.WALL_RUN under WALL_STUB: the change equals the floor's short curved pairs (inner
                              face 0.05 - 0.30 m) plus its straight returns, read again inside the floor's plan region
    INDEPENDENT_TAKEOFF       FIN.SKIRTING under WINDOW_SKIRTING (no window's sill established): P + hole perimeters
                              - every gap closed on the face (a door, a passage and a window alike are not certainly
                              skirted)

Truth: p2b9_truth (hand arithmetic), never an engine output."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))

pytest.importorskip("ezdxf")
pytest.importorskip("shapely")

import indep_reader as IR                                     # noqa: E402
import p2b9_fixtures as F                                     # noqa: E402
import p2b9_run as R                                          # noqa: E402
import p2b9_truth as T                                        # noqa: E402

TOOL = ROOT / "tools" / "arch_change_verify.py"
ROLES = {"A-WALL": "WALL", "A-COL": "COLUMN", "A-GLAZ": "WINDOW", "A-DOOR": "DOOR"}
A = 1e-5


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b9_census")


def _verify(before, after, dxf, out):
    argv = [sys.executable, "-I", str(TOOL), "--before", str(before), "--after", str(after), "--dxf", str(dxf),
            "--out", str(out)]
    r = subprocess.run(argv, capture_output=True, text=True)
    assert r.returncode in (0, 1), r.stdout[-1500:] + r.stderr[-1500:]
    return json.loads(Path(out).read_text(encoding="utf-8"))


def test_return_census_finds_the_short_return_only(work):
    c = IR.Drawing(str(F.example3_returns(work / "e3r.dxf")), roles=ROLES).return_census()
    assert [(r["t_m"], r["length_m"]) for r in c["returns"]] == [(T.T, T.E3R_RETURNS["short_return"])]
    # the collinear stubs of example 3 belong to their wall line's band (0.70 m in total): no return
    assert IR.Drawing(str(F.example3(work / "e3.dxf")), roles=ROLES).return_census()["returns"] == []
    # read only inside a plan region: a box away from the plan sees no wall line at all
    far = IR.Drawing(str(work / "e3r.dxf"), roles=ROLES).return_census(regions=[(100.0, 100.0, 101.0, 101.0)])
    assert far["returns"] == [] and far["bands"] == 0


def test_arc_census_lists_the_curved_stubs(work):
    c = IR.Drawing(str(F.example4_curved_stub(work / "e4s.dxf")), roles=ROLES).arc_census()
    assert c["bands"] == [] and len(c["short_stubs"]) == 2
    for s in c["short_stubs"]:
        assert (s["inner_lm"], s["mid_lm"]) == (pytest.approx(T.E4S_STUB_INNER, abs=A),
                                                pytest.approx(T.E4S_STUB_MID, abs=A))
    assert c["short_stubs_mid_lm"] == pytest.approx(T.E4S_WALL_RUN_CURVED_STUBS, abs=A)


@pytest.mark.parametrize("name,build,delta", [
    ("e3r", F.example3_returns, T.E3R_RETURNS["short_return"]),
    ("e4s", F.example4_curved_stub, T.E4S_WALL_RUN_CURVED_STUBS),
])
def test_a_stub_change_is_verified_by_the_stub_census(work, name, build, delta):
    src = build(work / f"v_{name}.dxf")
    b = R.run(src, work / f"o_{name}_271", method=R.V271)
    a = R.run(src, work / f"o_{name}_28", method=R.V28)
    rep = _verify(b, a, src, work / f"v_{name}.json")
    run = [d for d in rep["differences"] if d["item_code"] == "ARCH.WALL_RUN"]
    assert len(run) == 1 and run[0]["kinds"] == ["WALL_STUB"]
    assert run[0]["delta"] == pytest.approx(delta, abs=A)
    assert run[0]["status"] == "VERIFIED"
    assert run[0]["verification"]["method"] == "INDEPENDENT_STUB_CENSUS"
    assert run[0]["verification"]["independent_delta"] == pytest.approx(delta, abs=A)


def test_unknown_sill_skirting_is_verified_by_an_independent_takeoff(work):
    """example 1 without its schedule: V2.7.1 skirts the window threshold (13.00 m), V2.8 releases only what holds
    under every reading (14.00 - 1.00 door - 1.50 window = 11.50 m) - the reader's face gives the same."""
    src = F.example1(work / "e1_nosched.dxf", evidence={"TAGS", "SECTION"})
    b = R.run(src, work / "o_e1n_271", method=R.V271)
    a = R.run(src, work / "o_e1n_28", method=R.V28)
    rep = _verify(b, a, src, work / "v_e1n.json")
    sk = [d for d in rep["differences"] if d["item_code"] == "FIN.SKIRTING"]
    assert len(sk) == 1 and sk[0]["kinds"] == ["WINDOW_SKIRTING"]
    assert (sk[0]["before"], sk[0]["after"]) == (pytest.approx(T.E1_SKIRTING, abs=A),
                                                 pytest.approx(T.E1_UNKNOWN_SILL_SKIRTING, abs=A))
    assert sk[0]["status"] == "VERIFIED"
    assert sk[0]["verification"]["independent"] == pytest.approx(T.E1_UNKNOWN_SILL_SKIRTING, abs=1e-4)
