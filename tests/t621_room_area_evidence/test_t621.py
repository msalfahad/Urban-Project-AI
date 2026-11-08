"""T-621 / R-T621-1: own drawn area per residual row (research rule, unwired).

Villa K621 (synthetic, not Alsenan), hand calculation (m):
  L-shaped bed room: outline (0,0) (6,0) (6,2.5) (4,2.5) (4,4) (0,4): A = 6 x 2.5 + 4 x 1.5 = 21.000
  column 0.30 x 0.30 centred on the south face at x 3.05: notch 0.30 x 0.15 = 0.045 -> room 20.955
  door in the south wall: inner face drawn as S1 (x 0 .. 1.00) and S2 (x 1.90 .. 6.00), outer face at y -0.20 drawn as
  O1 / O2 with the same gap: the chain uses S1 only, so the gap is closed on its own face (area unchanged);
  door strip = gap 0.90 x depth 0.20 = 0.180
Read at 0 / 37 / 90 / 211 deg, mirrored, in mm. Adverse: a room outline whose source is the engine polygon is refused;
a chain that walks into the door gap (S1 then the jamb) is a different reading, not the room.
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t621"))
sys.path.insert(0, str(ROOT / "research" / "agents_t606"))
import t606_rules as R6  # noqa: E402
import t606_extract as X6  # noqa: E402
import t621_rules as R  # noqa: E402
import t621_alsenan as B  # noqa: E402

SEGS = {  # metres; converted to mm below
    "S1": ((0, 0), (1.0, 0)), "S2": ((1.9, 0), (6, 0)), "E1": ((6, 0), (6, 2.5)), "N1": ((6, 2.5), (4, 2.5)),
    "E2": ((4, 2.5), (4, 4)), "N2": ((4, 4), (0, 4)), "W1": ((0, 4), (0, 0)),
    "O1": ((-0.2, -0.2), (1.0, -0.2)), "O2": ((1.9, -0.2), (6.2, -0.2)), "J1": ((1.0, 0), (1.0, -0.2)),
}
COL = [(2.9, -0.15), (3.2, -0.15), (3.2, 0.15), (2.9, 0.15)]
CHAIN = ["S1", "E1", "N1", "E2", "N2", "W1"]


def _xf(p, ang, mirror):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return ((x * c - y * s) * 1000 + 12345.0, (x * s + y * c) * 1000 - 6789.0)


def _geom(ang=0, mirror=False):
    return {h: ("LINE", (_xf(a, ang, mirror), _xf(b, ang, mirror))) for h, (a, b) in SEGS.items()}


@pytest.mark.parametrize("ang,mirror", [(0, False), (37, False), (90, False), (211, False), (0, True), (37, True)])
def test_l_room_hand_calc(ang, mirror):
    g = _geom(ang, mirror)
    chain = CHAIN[::-1] if mirror else CHAIN   # a mirror reverses the walking sense; the area must not care
    res = R6.outline(g, [(h, "WALL") for h in chain], [[_xf(p, ang, mirror) for p in COL]])
    assert abs(float(res["area"]) - 20.955) < 1e-6
    assert abs(float(res["notch_m2"]) + 0.045) < 1e-6
    no_col = R6.outline(g, [(h, "WALL") for h in chain])
    assert abs(float(no_col["area"]) - 21.0) < 1e-6


@pytest.mark.parametrize("ang,mirror", [(0, False), (90, False), (211, True)])
def test_door_strip_gap_times_depth(ang, mirror):
    g = _geom(ang, mirror)
    w, d = X6._gap(g, "S1", "S2") / 1000, X6._depth(g, "S1", "O1") / 1000
    assert abs(w - 0.9) < 1e-9 and abs(d - 0.2) < 1e-9
    assert abs(R6.q6(w * d) - D("0.18")) < D("0.000001")


def test_threshold_gap_closed_on_its_face_not_walked():
    """adverse: walking into the door gap (S1, jamb J1, outer face O2 ...) is not the room; it differs from 21.000."""
    g = _geom()
    walked = R6.outline(g, [(h, "WALL") for h in ["S1", "J1", "O2", "E1", "N1", "E2", "N2", "W1"]])
    assert abs(float(walked["area"]) - 22.0) < 1e-6        # 21.000 + the wall band 5.00 x 0.20 east of the jamb
    room = R6.outline(g, [(h, "WALL") for h in CHAIN])
    st, diff = R.judge("ROOM", D("0"), own=walked["area"], engine=room["area"])
    assert st == "DIFFERS" and diff == D("1.0")


def _meas(area="20.955", src="DRAWING", handles=("S1", "E1"), kind="OUTLINE"):
    return {"source": src, "handles": list(handles), "kind": kind, "area": area}


def test_engine_polygon_refused_as_evidence():
    for src in ("ENGINE", "REFERENCE", "REPORT"):
        with pytest.raises(R.RuleError):
            R.evidence(_meas(src=src))
    with pytest.raises(R.RuleError):
        R.evidence(_meas(handles=()))
    with pytest.raises(R.RuleError):
        R.evidence(_meas(area="0"))
    with pytest.raises(R.RuleError):
        R.evidence(_meas(kind="POLYGON"))
    assert R.evidence(_meas()) == D("20.955")


def test_judge_room_piece_reading():
    assert R.judge("ROOM", D("-0.05"), own=D("20.955"), engine=D("20.9555"))[0] == "DRAWING_CONFIRMED"
    st, diff = R.judge("ROOM", D("-0.05"), own=D("20.955"), engine=D("21.000"))
    assert st == "DIFFERS" and diff == D("-0.045")
    assert R.judge("PIECE", D("-0.18"), own=D("0.18"))[0] == "DRAWING_CONFIRMED"
    assert R.judge("PIECE", D("0.18"), own=D("0.20"))[0] == "DIFFERS"
    assert R.judge("READING", D("0.045"), expected=D("0.045"))[0] == "DRAWING_CONFIRMED"
    assert R.judge("NOT_ESTABLISHED", D("1")) == ("NOT_REMEASURED", None)
    with pytest.raises(R.RuleError):
        R.judge("ROOM", D("1"), own=D("1"))
    with pytest.raises(R.RuleError):
        R.judge("GUESS", D("1"))


def test_class_sanity():
    R.check_class("TOLERANCE", D("-0.005"), "ROOM", D("-0.005"))
    with pytest.raises(R.RuleError):
        R.check_class("TOLERANCE", D("0.02"), "ROOM")
    with pytest.raises(R.RuleError):
        R.check_class("ENGINE_RIGHT", D("0.004"), "ROOM", D("0.004"))
    with pytest.raises(R.RuleError):
        R.check_class("VERIFIED", D("1"), "ROOM")


def test_rule_depth_named():
    assert R.rule_piece(D("1.0"), D("0.300"), "UP-ELEV-005") == D("0.300000")
    with pytest.raises(R.RuleError):
        R.rule_piece(D("1.0"), D("0.300"), "")


def test_split_exact_and_refusals():
    rows = [{"delta": "0.18", "class": "RULE_DIFFERENCE", "evidence_status": "DRAWING_CONFIRMED"},
            {"delta": "-0.045", "class": "ENGINE_RIGHT", "evidence_status": "NOT_REMEASURED"}]
    sp = R.split(rows, D("0.135"))
    assert sp["by_evidence"] == {"DRAWING_CONFIRMED": "0.18", "NOT_REMEASURED": "-0.045"}
    with pytest.raises(R.RuleError):
        R.split(rows, D("0.136"))
    with pytest.raises(R.RuleError):
        R.split([{"delta": "0", "class": "HELD", "evidence_status": "NOT_REMEASURED"}], D("0"))
    with pytest.raises(R.RuleError):
        R.split([{"delta": "1", "class": "TOLERANCE", "evidence_status": "VERIFIED"}], D("1"))


# ---- development villa (committed drawing read; no coordinate, no client name) --------------------------------------
def test_alsenan_rebuild_identical_and_split():
    d = B.build()
    assert json.dumps(d, indent=1, sort_keys=True) + "\n" == B.OUT_JSON.read_text(encoding="utf-8")
    assert B.markdown(d) == B.OUT_MD.read_text(encoding="utf-8")
    assert len(d["rows"]) == 41
    assert d["split"]["total"] == "22.485950" == str(D(d["difference"]).quantize(D("0.000001")))
    assert d["split"]["count_by_evidence"] == {"DRAWING_CONFIRMED": 37, "NOT_REMEASURED": 4}
    assert d["split"]["by_class"] == {"ENGINE_RIGHT": "0.797732", "ENGINE_WRONG": "2.97", "RULE_DIFFERENCE": "15.941912",
                                      "TOLERANCE": "-0.028416", "UNRESOLVED": "2.804722"}
    for r in d["rows"]:
        if r["evidence_status"] == "DRAWING_CONFIRMED":
            assert r["measures"] and all(m["handles"] for m in r["measures"])
            assert D(r["difference_to_row"]).copy_abs() <= R.AREA_TOL
        else:
            assert r["kind"] == "NOT_ESTABLISHED" and r["note"]
    assert [r["row"] for r in d["rows"] if r["evidence_status"] == "NOT_REMEASURED"] == [0, 9, 11, 13]
    assert len(d["checker_top5"]) == 5


def test_alsenan_drawn_json_has_no_coordinates():
    d = json.loads(B.DRAWN.read_text(encoding="utf-8"))
    for k, m in d["measures"].items():
        assert set(m) <= {"storey", "kind", "source", "handles", "area", "perimeter", "notch_m2", "note", "roles",
                          "width", "depth", "values"}, k
        assert m["source"] == "DRAWING"
        for f in ("area", "perimeter", "width", "depth"):
            if f in m:
                assert D(m[f]) < 1000          # metres / m2, never drawing coordinates


def test_alsenan_pieces_add_to_his_rows():
    d = json.loads(B.DRAWN.read_text(encoding="utf-8"))["measures"]
    a = {k: D(v["area"]) for k, v in d.items()}
    assert a["1F-380x430"] + a["1F-DRESSING"] + a["1F-OP-011"] == D("19.46")      # his 'bed room 2' exactly
    assert a["GF-SOLID-COL-2FD2"] + a["GF-SOLID-COL-2FC6"] + a["GF-SOLID-WALL"] == D("0.88")
    assert a["1F-OP-005"] + a["1F-OP-006"] + a["1F-OP-020"] + a["1F-D-1F-03"] == D("0.57")


DXF = Path(os.environ.get("T621_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_alsenan_dxf_reread_identical():
    pytest.importorskip("ezdxf")
    import t621_extract as XT
    d = XT.read(str(DXF))
    assert json.dumps(d, indent=1, sort_keys=True) + "\n" == XT.OUT.read_text(encoding="utf-8")
