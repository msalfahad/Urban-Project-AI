"""T-314 r3: ARCH_TAKEOFF_V3.0.79 (EXT_RENDER_GATE_B_V1 + EXT_PAINT_GATE_B_V1 + EXT_EDGE_DELTA_V1, R-T314-3) on the
hand-calculated NON-Alsenan villa W314 (own figures, no drawing; every figure below by hand):
  GF storey line (HELD blank before): face GF/N 10.00 x 3.50 = 35.00 less window 1.20 x 1.50 = 1.80 -> 33.20 (point);
      face GF/E 8.00 x 3.50 = 28.00 less a held door hole 0 .. 2.20 -> 25.80 .. 28.00; line 59.00 .. 61.20 m2 HELD.
      This is a TWO-F.F.L. ground floor measured BY FACE (GF/N from +0.30, GF/E from +0.00, both to +3.80): run x one
      storey height (18.00 x 3.80 = 68.40, less 1.80) would be wrong by +7.40 .. +9.60 m2.
  1F storey line (HELD blank): face 1F/N 10.00 x 3.20 = 32.00 -> 32.00 (point, DRAWING-CONFIRMED, held not released).
  1F parapet outer (ADDED, its own line, never folded into the storey): 1F/N 10.00 x 1.00 = 10.00 + 1F/E 8.00 x 0.80 ..
      1.00 = 6.40 .. 8.00 -> 16.40 .. 18.00 m2.
  1F slab edge (ADDED): 1F/N 10.00 x 0.25 = 2.50, 1F/E not printed (blank) -> line HELD BLANK, valued part 2.50 beside.
  Paint (UP-FIN-PAINT-002) = render face by face: 4 FIN.EXT.PAINT lines with the same figures / states.
  Edge verdict: 1F corners 6.00 -> 4.00 lm (two straight joints are no corner, -2.00).
Totals by hand: FIN.EXT.FINISH lines 2 -> 4, blocked 2 -> 1, bounded 0 -> 3, 107.40 .. 111.20 m2 (59.00 + 32.00 + 16.40
.. 61.20 + 32.00 + 18.00); FIN.EXT.PAINT 0 -> 4 lines, the same; FIN.EXT.PAINT.EDGE 6.00 -> 4.00 lm; the released
concrete 2.00 m3 and the released wall plaster 40.00 m2 byte-identical.
Adverse: a parapet face folded into a storey line, a face on two lines, a held face carried as 0, a face sum that is not
the ledger figure, a blank face with a line figure, VERIFIED, a stale (already valued) storey line, an added id not the
reserved one, applied twice, a mm2 slip, paint not equal to render; mirror order gives the same lines."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3077 as A3077  # noqa: E402
from engine.source import arch_v3079 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "W314-SYNTHETIC", "e" * 64
R = "FIN.EXT.FINISH"


def _ln(code, eid, state, net=None, unit="m2", rng=None, floor="GF", inputs=None):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", inputs=inputs or {}, rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      rfi={"question": f"not printed: {eid}", "unlocks": eid} if state in (
                          "BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic",
                      **({} if code in BL.ITEMS else {"item_en": code, "item_ar": code, "trade": "PAINT"}))
    return BL.validate(ln)


def base():
    gf = _ln(R, "GF-FACADE:facade", "BLOCKED_RFI")
    f1 = _ln(R, "1F-FACADE:facade", "BLOCKED_RFI", floor="1F")
    rec = {"piece": A3077.P_EXT, "action": "CORNER", "host_line_id": f1["line_id"], "corner_group": "W314-C1",
           "release_status": "NOT RELEASED"}
    edge = _ln("FIN.EXT.PAINT.EDGE", "1F-FACADE:CORNER_EDGE:1F", "BOUNDED_EXPOSURE", unit="lm", rng=(6.0, 6.0),
               floor="1F", inputs={A3077.REC_KEY: rec})
    return [gf, f1, edge, _ln("STR.CONC.COLUMN", "COL:R1", "MEASURED", net=2.0, unit="m3"),
            _ln("FIN.PLASTER", "HL:WALL_FINISH:R9:PLASTER", "MEASURED", net=40.0)]


LN = base()
GF, F1, EDGE = LN[0]["line_id"], LN[1]["line_id"], LN[2]["line_id"]
SRC = [{"task": "T-FACE", "file": "research/w314/faces.csv", "sha256": "a" * 64, "merge_commit": "c" * 40,
        "checker_run": "checker T-FACE"}]


def nid(eid):
    return BL.line_id(PID, R, eid, *A.ADD_RULE, "m2")


def face(fid, el, r, holes=""):
    return {"face_id": fid, "element": el, "render": r, "holes": holes, "state": "BLANK" if r is None else "POINT"}


def doc():
    common = {"source_tasks": ["T-FACE"], "rule": "R-SYN-FACE", "why": "synthetic face rows"}
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC), "render": [
        dict(common, line_id=GF, action="CHANGE", element_id="GF-FACADE:facade", status="HELD",
             expect={"item_code": R, "element_id": "GF-FACADE:facade", "unit": "m2", "class": "HELD"},
             faces=[face("GF/N", "STOREY", [33.2, 33.2], "W1"), face("GF/E", "STOREY", [25.8, 28.0], "D1")],
             expect_after=[59.0, 61.2]),
        dict(common, line_id=F1, action="CHANGE", element_id="1F-FACADE:facade", status="DRAWING-CONFIRMED",
             expect={"item_code": R, "element_id": "1F-FACADE:facade", "unit": "m2", "class": "HELD"},
             faces=[face("1F/N", "STOREY", [32.0, 32.0])], expect_after=[32.0, 32.0]),
        dict(common, line_id=nid("1F-FACADE:PARAPET_OUTER:1F_ROOF"), action="ADD",
             element_id="1F-FACADE:PARAPET_OUTER:1F_ROOF", host_line_id=F1, status="HELD",
             faces=[face("1F/N/parapet", "PARAPET_OUTER", [10.0, 10.0]),
                    face("1F/E/parapet", "PARAPET_OUTER", [6.4, 8.0])], expect_after=[16.4, 18.0]),
        dict(common, line_id=nid("1F-FACADE:SLAB_EDGE"), action="ADD", element_id="1F-FACADE:SLAB_EDGE",
             host_line_id=F1, status="HELD", faces=[face("1F/N/edge", "SLAB_EDGE", [2.5, 2.5]),
                                                    face("1F/E/edge", "SLAB_EDGE", None)],
             expect_after=None, valued_part=[2.5, 2.5])],
        "edges": [{"line_id": EDGE, "source_tasks": ["T-FACE"], "status": "HELD", "rule": "R-SYN-EDGE",
                   "why": "two straight joints are no corner",
                   "expect": {"item_code": "FIN.EXT.PAINT.EDGE", "element_id": "1F-FACADE:CORNER_EDGE:1F", "unit": "lm",
                              "class": "HELD", "low": 6.0, "high": 6.0}, "low": 4.0, "high": 4.0}]}


def run(d=None, prev=None):
    prev = copy.deepcopy(LN) if prev is None else prev
    inp = A.load_inputs(d or doc(), PID)
    ch, log = A.changes_for(inp, prev)
    out, ident = A.integrate(prev, ch)
    return prev, ch, out, ident


def by(lines):
    return {(x["item_code"], x["location"]["element_id"]): x for x in lines}


def rng(x):
    b = x.get("bounded_range")
    return None if b is None else (b["low"], b["high"])


def test_line_figures_by_hand():
    _, ch, out, ident = run()
    b = by(out)
    assert rng(b[(R, "GF-FACADE:facade")]) == (59.0, 61.2)
    assert rng(b[(R, "1F-FACADE:facade")]) == (32.0, 32.0)
    assert rng(b[(R, "1F-FACADE:PARAPET_OUTER:1F_ROOF")]) == (16.4, 18.0)
    se = b[(R, "1F-FACADE:SLAB_EDGE")]
    assert se["evidence_state"] == "BLOCKED_RFI" and rng(se) is None and se.get("measured_net") is None
    bs = se["calculation"]["inputs"][A.REC_KEY]["beside"]
    assert bs["kind"] == "VALUED_PART" and (bs["low"], bs["high"]) == (2.5, 2.5) and bs["blank_faces"] == ["1F/E/edge"]
    assert rng(b[("FIN.EXT.PAINT.EDGE", "1F-FACADE:CORNER_EDGE:1F")]) == (4.0, 4.0)
    assert ident["ext_render_paint"] == {"RENDER_FACES:CHANGE": 2, "RENDER_FACES:ADD": 2, "PAINT_FACES:ADD": 4,
                                         "EDGE_DELTA:CHANGE": 1}
    assert ident["replaced"] == 3 and ident["added"] == 6


def test_two_ffl_ground_floor_by_face_not_run_times_height():
    _, _, out, _ = run()
    lo, hi = rng(by(out)[(R, "GF-FACADE:facade")])
    run_x_height = (10.0 + 8.0) * 3.80 - 1.80          # the storey-height shortcut: 66.60
    assert round(run_x_height - lo, 6) == 7.6 and round(run_x_height - hi, 6) == 5.4
    assert (lo, hi) == (59.0, 61.2)


def test_paint_equals_render_face_by_face():
    _, _, out, _ = run()
    b = by(out)
    paints = [x for x in out if x["item_code"] == A.PAINT]
    assert len(paints) == 4
    for p in paints:
        r = b[(R, p["location"]["element_id"])]
        assert p["calculation"]["inputs"][A.REC_KEY]["render_line_id"] == r["line_id"]
        assert rng(p) == rng(r) and p["evidence_state"] == r["evidence_state"] and p.get("measured_net") is None
        assert p["line_id"] != r["line_id"]


def test_totals_by_hand():
    prev, ch, out, _ = run()
    t0, t1 = A304.code_totals(prev), A304.code_totals(out)
    assert t0[f"{R}|m2"] == {"lines": 2, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0,
                             "blocked_lines": 2}
    assert t1[f"{R}|m2"] == {"lines": 4, "released": 0.0, "held_low": 107.4, "held_high": 111.2, "bounded_lines": 3,
                             "blocked_lines": 1}
    assert t1[f"{A.PAINT}|m2"] == t1[f"{R}|m2"]
    assert t1["FIN.EXT.PAINT.EDGE|lm"]["held_low"] == 4.0
    for k in ("STR.CONC.COLUMN|m3", "FIN.PLASTER|m2"):
        assert t0[k] == t1[k]
    moved = A.check_totals(t0, t1, ch)
    assert set(moved) == {f"{R}|m2", f"{A.PAINT}|m2", "FIN.EXT.PAINT.EDGE|lm"}


def test_other_lines_byte_identical_and_ids_reserved():
    prev, _, out, ident = run()
    o = {x["line_id"]: x for x in out}
    for x in prev[3:]:
        assert BL.dumps([x]) == BL.dumps([o[x["line_id"]]])
    assert ident["outside_rows"] == 2
    assert nid("1F-FACADE:PARAPET_OUTER:1F_ROOF") in o and nid("1F-FACADE:SLAB_EDGE") in o


def test_mirror_order_same_lines():
    d = doc()
    d["render"] = list(reversed(d["render"]))
    for e in d["render"]:
        e["faces"] = list(reversed(e["faces"]))
    _, _, out2, _ = run(d)
    _, _, out1, _ = run()
    a = {x["line_id"]: rng(x) for x in out1}
    b = {x["line_id"]: rng(x) for x in out2}
    assert a == b


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, msg):
    d = doc()
    mut(d)
    with pytest.raises(A.InputsError, match=msg):
        run(d)


def test_parapet_face_folded_into_storey_refused():
    _bad(lambda d: d["render"][1]["faces"].append(face("1F/N/parapet-x", "PARAPET_OUTER", [1.0, 1.0])),
         "the element owns the band")


def test_face_on_two_lines_refused():
    _bad(lambda d: d["render"][2]["faces"].append(face("1F/N", "PARAPET_OUTER", [1.0, 1.0])), "booked on two lines")


def test_held_face_as_zero_refused():
    _bad(lambda d: d["render"][0]["faces"].__setitem__(1, face("GF/E", "STOREY", [0.0, 0.0])), "never 0")


def test_face_sum_not_ledger_figure_refused():
    _bad(lambda d: d["render"][0].__setitem__("expect_after", [59.0, 61.0]), "is not the ledger's line figure")


def test_blank_face_with_line_figure_refused():
    _bad(lambda d: d["render"][3].__setitem__("expect_after", [2.5, 2.5]), "a blank face makes the line blank")


def test_verified_refused():
    _bad(lambda d: d["render"][0].__setitem__("status", "VERIFIED"), "never VERIFIED")


def test_mm2_slip_refused():
    _bad(lambda d: d["render"][1]["faces"].__setitem__(0, face("1F/N", "STOREY", [32000.0, 32000.0])), "unit slip")


def test_reserved_id_mismatch_refused():
    _bad(lambda d: d["render"][2].__setitem__("element_id", "1F-FACADE:PARAPET_OUTER:OTHER"), "reserved id")


def test_stale_storey_line_refused():
    prev = copy.deepcopy(LN)
    prev[0] = _ln(R, "GF-FACADE:facade", "BOUNDED_EXPOSURE", rng=(50.0, 60.0))
    d = doc()
    d["render"][0]["line_id"] = prev[0]["line_id"]
    with pytest.raises(A.InputsError, match="stale binding"):
        run(d, prev)


def test_applied_twice_refused():
    _, _, out, _ = run()
    inp = A.load_inputs(doc(), PID)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(inp, out)


def test_paint_not_render_refused_by_check():
    _, _, out, _ = run()
    out = copy.deepcopy(out)
    p = next(x for x in out if x["item_code"] == A.PAINT and rng(x) == (32.0, 32.0))
    p["bounded_range"] = dict(p["bounded_range"], low=31.0)
    with pytest.raises(ValueError, match="not in its state"):
        A.check_lines(out)


def test_released_line_never_restated():
    prev = copy.deepcopy(LN)
    prev[1] = _ln(R, "1F-FACADE:facade", "MEASURED", net=30.0, floor="1F")
    d = doc()
    d["render"][1]["line_id"] = prev[1]["line_id"]
    with pytest.raises(A.InputsError, match="stale binding"):
        run(d, prev)
