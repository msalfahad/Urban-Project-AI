"""Phase 2B-7: tools/arch_run_audit.py on ARCH_TAKEOFF_V2.7 runs. Each Phase 2B-6 finding, raised by V2.6 on the
synthetic drawing that shows it, is gone under V2.7 because the method now measures what the finding warned about
(the curved band, the door layer, the wet-room evidence, the door frame); a V2.7 refusal turns the matching finding
into a REVIEW that names the refusal."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "m9_p2b6"))
sys.path.insert(0, str(HERE.parent / "m9_p2b5_bench"))

ezdxf = pytest.importorskip("ezdxf")

import p2b6_run as R6                                         # noqa: E402
import p2b7_fixtures as F                                     # noqa: E402
import p2b7_run as R                                          # noqa: E402


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b7_audit")


def _codes(rep):
    return sorted(f["code"] for f in rep["findings"])


def _bench(work, case):
    import bench_cases as BC
    import bench_drawings as BD
    dxf = work / f"{case}.dxf"
    BD.dxf(BC.BY_ID[case], dxf)
    return dxf


@pytest.mark.parametrize("case,code,make,roles,with_dxf", [
    ("B10", "A07", lambda w: _bench(w, "B10"), None, True),                   # curved band now in the wall run
    ("PLAIN", "A01", lambda w: F.door_plan(w / "PLAIN.dxf", "PLAIN"), None, False),     # door layer typed WINDOW
    ("WC_BASIN", "A09", lambda w: F.wc_plan(w / "WC_BASIN.dxf", "BASIN"), F.ROLES, False),  # wet from a basin
    ("FR_NEST", "A05", lambda w: F.framed_door_plan(w / "FR_NEST.dxf", "NEST"), F.ROLES, False),  # frame pooled
])
def test_v26_finding_gone_under_v27(work, case, code, make, roles, with_dxf):
    dxf = make(work)
    a = R.run(dxf, work / f"o_{case}_26", roles=roles, facts=True, method=R.V26)
    b = R.run(dxf, work / f"o_{case}_27", roles=roles, facts=True)
    _, rep_a, _ = R6.audit(a, dxf if with_dxf else None)
    _, rep_b, err = R6.audit(b, dxf if with_dxf else None)
    assert code in _codes(rep_a), rep_a["findings"]
    assert code not in _codes(rep_b), (rep_b["findings"], err)


def test_refused_column_layer_is_a_review(work):
    """benchmark B04 (one free-standing hatched column, roles inferred): V2.6 audit A03 MEDIUM (one square, not
    typed COLUMN); V2.7 refuses the layer's role itself (FREE_STANDING) and the audit names that refusal - REVIEW."""
    dxf = _bench(work, "B04")
    _, rep_a, _ = R6.audit(R.run(dxf, work / "o_b04_26", method=R.V26))
    _, rep_b, _ = R6.audit(R.run(dxf, work / "o_b04_27"))
    a3 = [f for f in rep_a["findings"] if f["code"] == "A03"]
    b3 = [f for f in rep_b["findings"] if f["code"] == "A03"]
    assert a3 and a3[0]["level"] == "MEDIUM"
    assert b3 and b3[0]["level"] == "REVIEW" and b3[0]["evidence"].get("refusal", "").startswith("C27-")
