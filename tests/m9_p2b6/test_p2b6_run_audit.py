"""Phase 2B-6 tools/arch_run_audit.py: each finding on the synthetic case that shows it, its absence where the run is
right, and the tool's own safety (it never writes into the run folder and changes no byte of it).

The hand truth of each case is in test_p2b6_found_defects.py / p2b6_fixtures.py; here the audit must name the
defect, the layer and the action."""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "m9_p2b5_bench"))

ezdxf = pytest.importorskip("ezdxf")

import p2b6_fixtures as F                                     # noqa: E402
import p2b6_run as R                                          # noqa: E402


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b6_audit")


def _codes(rep):
    return sorted(f["code"] for f in rep["findings"])


def _one(rep, code):
    xs = [f for f in rep["findings"] if f["code"] == code]
    assert len(xs) == 1, rep["findings"]
    return xs[0]


def test_a01_door_layer_typed_window(work):
    dxf = F.door_plan(work / "PLAIN.dxf", "PLAIN")
    rc, rep, _ = R.audit(R.run(dxf, work / "o_plain_inf"))
    f = _one(rep, "A01")
    assert rc == 0 and f["level"] == "HIGH" and f["evidence"]["layer"] == "A-DOOR"
    assert "A-DOOR=DOOR" in rep["suggested_layer_roles"]
    assert "A11" in _codes(rep)                                  # the one glazing line: its window is a passage
    rc, rep, _ = R.audit(R.run(dxf, work / "o_plain_dec", roles=F.ROLES))
    assert rep["summary"]["HIGH"] == 0 and "A01" not in _codes(rep)


def test_a02_a03_single_door_and_single_column(work):
    """benchmark B04: one door, one column, roles inferred (D-D1)."""
    import bench_cases as BC
    import bench_drawings as BD
    dxf = Path(BD.dxf(BC.BY_ID["B04"], work / "B04.dxf"))
    rc, rep, _ = R.audit(R.run(dxf, work / "o_b04"))
    assert _one(rep, "A02")["evidence"]["layer"] == "A-DOOR" and _one(rep, "A03")["evidence"]["layer"] == "A-COL"
    # with roles declared, nothing to say about roles
    rc, rep, _ = R.audit(R.run(dxf, work / "o_b04_d", roles=F.ROLES))
    assert not {"A02", "A03"} & set(_codes(rep))


def test_a04_inferred_column_layer_and_drains(work):
    out = R.run(F.lookalike(work / "DRAINS.dxf", "THREE_DRAINS"), work / "o_drains", roles=F.ROLES)
    f = _one(R.audit(out)[1], "A04")
    assert f["level"] == "REVIEW" and f["evidence"]["layer"] == "P-DRAIN"


def test_a05_nested_plan(work):
    from tools import arch_synth as AS
    base = work / "villa.dxf"
    AS.villa(base)
    rep = R.audit(R.run(F.variant(base, work / "villa_nest.dxf", "nest"), work / "o_nest"))[1]
    f = _one(rep, "A05")
    assert f["level"] == "HIGH" and len(f["evidence"]["doors"]) == 5
    assert all(d["frame_m"] > 2 * d["opening_m"] + 1.0 for d in f["evidence"]["doors"])
    assert "A05" not in _codes(R.audit(R.run(base, work / "o_villa"))[1])


def test_a06_turned_and_exploded_columns(work):
    from tools import arch_synth as AS
    base = work / "villa_t.dxf"
    AS.villa(base)
    turned = F.variant(base, work / "villa_rot30.dxf", "rot30")
    f = _one(R.audit(R.run(turned, work / "o_rot30"), turned)[1], "A06")
    rects = f["evidence"]["rectangles"]
    assert f["level"] == "HIGH" and len(rects) == 3
    assert all(abs(r["w_m"] - 0.4) < 1e-6 and abs(r["h_m"] - 0.4) < 1e-6 and abs(r["angle_deg"] - 30.0) < 1e-6
               for r in rects)
    # a true column drawn as four LINEs (axis-aligned): invisible to the inference, found by the audit
    dxf = F.lookalike(work / "COLUMN.dxf", "COLUMN")
    f = _one(R.audit(R.run(dxf, work / "o_col", roles=F.ROLES), dxf)[1], "A06")
    assert f["evidence"]["layer"] == "S-COL" and f["evidence"]["rectangles"][0]["drawn_as"] == "LINES"
    # the unturned villa: its columns are typed, nothing to find
    assert "A06" not in _codes(R.audit(R.run(base, work / "o_villa_t"), base)[1])


def test_a07_curved_band_b10(work):
    """B10's east wall: inner arc r 2.50 m, outer r 2.70 m, common sweep 2 asin(0.6) (the inner arc's). Hand truth:
    mean-radius run 2.60 x 1.287002 = 3.346206 m; band 1.287002 x (2.70^2 - 2.50^2) / 2 = 0.669241 m2."""
    import bench_cases as BC
    import bench_drawings as BD
    dxf = Path(BD.dxf(BC.BY_ID["B10"], work / "B10.dxf"))
    f = _one(R.audit(R.run(dxf, work / "o_b10", roles=F.ROLES), dxf)[1], "A07")
    b = f["evidence"]["bands"][0]
    th = 2 * math.asin(0.6)
    assert abs(b["MID_BAND_ARC_lm"] - 2.6 * th) < 1e-6 and abs(b["MIN_RADIUS_ARC_lm"] - 2.5 * th) < 1e-6
    assert abs(b["strip_m2"] - th * (2.7 ** 2 - 2.5 ** 2) / 2) < 1e-6 and b["t_m"] == 0.2


def test_a08_a09_a10(work):
    rep = R.audit(R.run(F.door_plan(work / "CROSSING.dxf", "CROSSING"), work / "o_cross", roles=F.ROLES))[1]
    assert _one(rep, "A08")["evidence"]["width_m"] == pytest.approx(1.027)
    rep = R.audit(R.run(F.basin_plan(work / "BASIN.dxf"), work / "o_basin", roles=F.ROLES))[1]
    assert _one(rep, "A09")["evidence"]["blocks"] == ["WASH"]
    dxf = F.variant(F.door_plan(work / "P2.dxf", "PLAIN"), work / "P2_r37m.dxf", "rot37_metres")
    rep = R.audit(R.run(dxf, work / "o_r37m", roles=F.ROLES))[1]
    assert len(_one(rep, "A10")["evidence"]["line_ids"]) == 1


def test_clean_runs_raise_nothing_high(work):
    """the declared CROSSING / BASIN and the synthetic villa (inferred) carry no HIGH finding."""
    for name, dxf, roles in (("o_cross_c", F.door_plan(work / "C2.dxf", "CROSSING"), F.ROLES),
                             ("o_basin_c", F.basin_plan(work / "B2.dxf"), F.ROLES)):
        assert R.audit(R.run(dxf, work / name, roles=roles), dxf)[1]["summary"]["HIGH"] == 0


def test_read_only_and_refusals(work):
    out = R.run(F.door_plan(work / "PLAIN3.dxf", "PLAIN"), work / "o_ro")
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    rc, rep, _ = R.audit(out, work / "PLAIN3.dxf")
    assert rc == 0 and rep["schema"] == "URBAN_ARCH_RUN_AUDIT_V1"
    rc, _, err = R.audit(out, None, "--out", str(out / "RUN_AUDIT.json"))
    assert rc == 2 and "never written into the run folder" in err
    rc, _, _ = R.audit(out, None, "--strict")
    assert rc == 1                                               # A01 is HIGH
    rc, _, _ = R.audit(work / "no_such_run")
    assert rc == 2
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    assert before == after
