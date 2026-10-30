"""T-279: ARCH_TAKEOFF_V3.0.26 (the held storey / thickness blockwork lines carry the walls of a checker-merged
wall-by-wall fill: closable walls on their own lines by status and block type, held walls / drop terms / held pieces
BLANK by name on the parent) on a hand-calculated NON-Alsenan villa (P279), normal and adverse.

Villa P279, by hand (structural floor to the soffit of the member over each wall; openings once by id):
  GF t 0.20:
    W1 VERIFIED   BLACK  5.000 x 3.000 - door D1 1.000 x 2.100 (printed)        = 12.900 m2 -> 2.580 m3
    W2 DRAW.-CONF. WHITE 4.000 x 3.000 - window N1 1.200 x 1.000               = 10.800 m2 -> 2.160 m3
    W3 OWNER-APPR. WHITE 3.000 x 3.000 - door D2 0.800 x 2.200 (Q-55 C height) =  7.240 m2 -> 1.448 m3
    W4 PART + HELD WHITE 6.000 long: 4.000 x 3.000 established (DRAW.-CONF.)   = 12.000 m2 -> 2.400 m3;
                         2.000 m under an unlabelled beam, depth not printed: HELD piece (blank)
    W5 HELD              no member drawn over it (blank)
    W6 HELD ON DROP      3.000 m under a sunken panel: 3.000 x (3.000 - d) = 9.000 - 3.000 d (never evaluated)
  1F t 0.15:
    W7 VERIFIED   BLACK  4.000 x 2.800 = 11.200 m2 -> 1.680 m3
  MAS.BLOCK parts: GF 0.20 VERIFIED BLACK 12.900 | DRAWING-CONFIRMED WHITE 10.800 + 12.000 = 22.800 | OWNER-APPROVED
  WHITE 7.240; 1F 0.15 VERIFIED BLACK 11.200; released 54.140 m2 (VERIFIED 24.100, DC 22.800, OA 7.240); held on the
  GF 0.20 parent: W4 piece, W5, W6 (9.000 - 3.000 d). ARCH.WALL_PANEL the same m2; ARCH.WALL_VOLUME m2 x t.
"""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3026 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-p279", "e" * 64
DOCS = [{"file": "p279_arch.dxf", "sha256": "d" * 64}]
OA = A.OA
Q55 = "Q-55 C (door height 2.20 m where no sheet prints one): D2 1.7600"


NAMES = {"ARCH.WALL_PANEL": ("Wall panel", "لوح جدار"), "ARCH.WALL_VOLUME": ("Wall volume", "حجم جدار"),
         "MAS.BLOCK": ("Blockwork", "طابوق"), "ARCH.WALL_RUN": ("Wall run", "طول جدار")}


def _ln(code, eid, ev, net=None, floor="GF", unit="m2", formula="p279 candidate"):
    en, ar = NAMES.get(code, (None, None))
    kw = {"item_en": en, "item_ar": ar, "trade": "MASONRY"} if en else {}
    return BL.make_line(**kw, project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, physical_element="walls", formula=formula,
                        documents=DOCS, rule_id="R", rule_version="1",
                        rfi={"question": "MASONRY_NOT_MEASURED"} if ev == "BLOCKED_RFI" else None, notes="p279")


def lines_3025():
    out = [_ln("FIN.FLOOR.PORCELAIN", "GF-HALL", "SOURCE_DERIVED", 30.0, formula="6 x 5 = 30.0 m2"),
           _ln("ARCH.WALL_RUN", "GF-WALLS:walls t=0.20", "PROVISIONAL", 26.0, unit="lm", formula="runs = 26.0 lm")]
    for fl, t in (("GF", "0.20"), ("1F", "0.15")):
        for code, unit in (("ARCH.WALL_PANEL", "m2"), ("ARCH.WALL_VOLUME", "m3"), ("MAS.BLOCK", "m2")):
            out.append(_ln(code, f"{fl}-WALLS:walls t={t}", "BLOCKED_RFI", floor=fl, unit=unit,
                           formula="wall-mass plan area / t x masonry height - openings"))
    return out


def _id(lines, code, fl):
    return next(ln["line_id"] for ln in lines if ln["item_code"] == code and ln["location"]["floor"] == fl
                and ln["location"]["element_id"].startswith(f"{fl}-WALLS"))


GF = [  # wall, type, status, carried m2, part_status, extra
    ("W1", "BLACK", "VERIFIED", 12.9, None, {"verified_by": "checker run 1 (own re-measure)", "openings": "D1 2.1"}),
    ("W2", "WHITE", A.DC, 10.8, None, {"openings": "N1 1.2"}),
    ("W3", "WHITE", OA, 7.24, None, {"owner_source": Q55, "openings": "D2 1.76"}),
    ("W4", "WHITE", A.PART, 12.0, A.DC, {"held_item": "2.000 m under an unlabelled beam, depth not printed"}),
    ("W5", None, A.HELD, None, None, {"held_item": "no member drawn over the wall"}),
    ("W6", None, A.DROP, None, None, {"held_item": "sunken panel drop d", "upper_at_d0": 9.0,
                                      "drop_coefficient": 3.0}),
]
F1 = [("W7", "BLACK", "VERIFIED", 11.2, None, {"verified_by": "checker run 2"})]


def _walls(spec, k):
    out = []
    for wid, bt, st, c, ps, ex in spec:
        w = {"wall_id": wid, "block_type": bt, "status": st, "carried": None if c is None else round(c * k, 6),
             "part_status": ps, "verified_by": None, "owner_source": None, "held_item": None, "upper_at_d0": None,
             "drop_coefficient": None, "conflict_increment_outside": None, "openings": None}
        w.update(copy.deepcopy(ex))
        if k != 1.0 and w.get("upper_at_d0") is not None:
            w["upper_at_d0"] = round(w["upper_at_d0"] * k, 6)
            w["drop_coefficient"] = round(w["drop_coefficient"] * k, 6)
        out.append(w)
    return out


def _decl(walls):
    d = {"verified": 0.0, "drawing_confirmed": 0.0, "owner_approved": 0.0, "established_parts": 0.0,
         "drop_upper_at_d0": 0.0, "drop_coefficient": 0.0}
    m = {"VERIFIED": "verified", A.DC: "drawing_confirmed", OA: "owner_approved"}
    for w in walls:
        if w["status"] in m:
            d[m[w["status"]]] += w["carried"]
        elif w["status"] == A.PART:
            d["established_parts"] += w["carried"]
        elif w["status"] == A.DROP:
            d["drop_upper_at_d0"] += w["upper_at_d0"]
            d["drop_coefficient"] += w["drop_coefficient"]
    return {k: round(v, 6) for k, v in d.items()}


def doc(base=None):
    base = base or lines_3025()
    lines = []
    for fl, t, spec in (("GF", 0.20, GF), ("1F", 0.15, F1)):
        for code, unit, k in (("ARCH.WALL_PANEL", "m2", 1.0), ("ARCH.WALL_VOLUME", "m3", t), ("MAS.BLOCK", "m2", 1.0)):
            ws = _walls(spec, k)
            lines.append({"line_id": _id(base, code, fl), "item_code": code, "unit": unit, "floor": fl, "family": t,
                          "element_id": f"{fl}-WALLS:walls t={t:.2f}",
                          "before": {"evidence_state": "BLOCKED_RFI", "measured_net": None},
                          "walls": ws, "declared": _decl(ws)})
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "fill_task": "T-F1",
            "sources": [{"file": "fill.csv", "sha256": "a" * 64, "task": "T-F1", "merge_commit": "b" * 40,
                         "checker_run": "checker gate A"}], "lines": lines}


def run(d=None, base=None):
    base = base or lines_3025()
    d = A.load_inputs(d or doc(base), PID)
    ch, log = A.changes_for(d, base)
    out, ident = A.integrate(base, ch)
    return out, ident, ch, log, base


def _by(out, code, fl):
    return [ln for ln in out if ln["item_code"] == code and ln["location"]["floor"] == fl]


# ================================================================================================ normal
def test_hand_values_per_part():
    out, ident, ch, log, base = run()
    parts = {ln["location"]["element_id"].split("#BLOCKWORK:")[1]: ln for ln in _by(out, "MAS.BLOCK", "GF")
             if "#BLOCKWORK:" in ln["location"]["element_id"]}
    assert {k: v["measured_net"] for k, v in parts.items()} == {
        "VERIFIED_BLACK": 12.9, "DRAWING_CONFIRMED_WHITE": 22.8, "ASSUMED___OWNER_APPROVED_WHITE": 7.24}
    assert parts["VERIFIED_BLACK"]["evidence_state"] == "SOURCE_DERIVED"
    assert parts["DRAWING_CONFIRMED_WHITE"]["evidence_state"] == "SOURCE_DERIVED"
    assert parts["ASSUMED___OWNER_APPROVED_WHITE"]["evidence_state"] == "PROVISIONAL"
    rec = parts["DRAWING_CONFIRMED_WHITE"]["calculation"]["inputs"]["blockwork_fill_v3026"]
    assert [(p["id"], p["kind"]) for p in rec["pieces"]] == [("W2", "WHOLE"), ("W4", "ESTABLISHED_PART")]
    assert ident["blockwork"]["released"] == {
        "ARCH.WALL_PANEL m2 ASSUMED - OWNER-APPROVED": 7.24, "ARCH.WALL_PANEL m2 DRAWING-CONFIRMED": 22.8,
        "ARCH.WALL_PANEL m2 VERIFIED": 24.1, "ARCH.WALL_VOLUME m3 ASSUMED - OWNER-APPROVED": 1.448,
        "ARCH.WALL_VOLUME m3 DRAWING-CONFIRMED": 4.56, "ARCH.WALL_VOLUME m3 VERIFIED": 4.26,
        "MAS.BLOCK m2 ASSUMED - OWNER-APPROVED": 7.24, "MAS.BLOCK m2 DRAWING-CONFIRMED": 22.8,
        "MAS.BLOCK m2 VERIFIED": 24.1}
    blk = sum(ln["measured_net"] for ln in out if ln["item_code"] == "MAS.BLOCK" and ln["measured_net"])
    assert round(blk, 6) == 54.14


def test_parent_blank_with_every_held_item_named():
    out, *_ = run()
    par = next(ln for ln in _by(out, "MAS.BLOCK", "GF") if "#" not in ln["location"]["element_id"])
    assert par["evidence_state"] == "BLOCKED_RFI" and par["measured_net"] is None and par["bounded_range"] is None
    q = par["rfi"]["question"]
    assert "W4 HELD_PIECE" in q and "W5 HELD_WALL" in q and "W6 DROP 9.0 - 3.0 d" in q
    rec = par["calculation"]["inputs"]["blockwork_fill_v3026"]
    assert rec["action"] == "PARENT" and len(rec["parts"]) == 3
    one = next(ln for ln in _by(out, "MAS.BLOCK", "1F") if "#" not in ln["location"]["element_id"])
    assert one["calculation"]["inputs"]["blockwork_fill_v3026"]["still_held"] == []


def test_volume_is_area_times_thickness_and_panel_equals_block():
    out, *_ = run()
    for fl, t in (("GF", 0.2), ("1F", 0.15)):
        blk = {ln["location"]["element_id"].split("#")[-1]: ln["measured_net"] for ln in _by(out, "MAS.BLOCK", fl)
               if "#" in ln["location"]["element_id"]}
        pan = {ln["location"]["element_id"].split("#")[-1]: ln["measured_net"]
               for ln in _by(out, "ARCH.WALL_PANEL", fl) if "#" in ln["location"]["element_id"]}
        vol = {ln["location"]["element_id"].split("#")[-1]: ln["measured_net"]
               for ln in _by(out, "ARCH.WALL_VOLUME", fl) if "#" in ln["location"]["element_id"]}
        assert blk == pan
        assert {k: round(v * t, 6) for k, v in blk.items()} == vol


def test_outside_lines_byte_identical_and_counts():
    out, ident, ch, log, base = run()
    assert ident["replaced"] == 6 and ident["added"] == 3 * 3 + 3 * 1
    by = {ln["line_id"]: ln for ln in base}
    for lid in (base[0]["line_id"], base[1]["line_id"]):
        assert A30.line_sha(by[lid]) == A30.line_sha(next(x for x in out if x["line_id"] == lid))


def test_order_invariance():
    base = lines_3025()
    d1 = doc(base)
    d2 = copy.deepcopy(d1)
    rnd = random.Random(279)
    for ln in d2["lines"]:
        rnd.shuffle(ln["walls"])
    rnd.shuffle(d2["lines"])
    o1 = run(d1, base)[0]
    o2 = run(d2, lines_3025())[0]
    q = lambda o: sorted((x["line_id"], x["evidence_state"], x["measured_net"]) for x in o)  # noqa: E731
    assert q(o1) == q(o2)


def test_write_files_and_totals_moved(tmp_path):
    base = lines_3025()
    d = A.load_inputs(doc(base), PID)
    ch, log = A.changes_for(d, base)
    names, ident, led = A.write(tmp_path, base, ch, log, d, released_lines=[base[0]])
    assert names == sorted(["V3_0_26_BOQ_LINES.json", "V3_0_26_BOQ_LINES.csv", "V3_0_26_INTEGRATION_LEDGER.json",
                            "V3_0_26_INTEGRATION_LEDGER.csv", "V3_0_26_WALLS.csv", "V3_0_26_DIFF.csv",
                            "V3_0_26_RUN.json"])
    run_rec = json.loads((tmp_path / "V3_0_26_RUN.json").read_text(encoding="utf-8"))
    assert set(run_rec["totals_moved_by_code"]) and all(
        any(k.startswith(c) for c in A.FAMILY) for k in run_rec["totals_moved_by_code"])
    assert run_rec["released_default"] is False and led["integration_package"] is True
    assert ident["diff"]["vs_v3_0_25"] == {"SAME": 2, "CHANGED_TEXT_ONLY": 6, "ADDED": 12}
    walls = (tmp_path / "V3_0_26_WALLS.csv").read_text(encoding="utf-8")
    assert "W6" in walls and "9.0 - 3.0 d" in walls


# ================================================================================================ adverse
def _refused(mut, match):
    base = lines_3025()
    d = doc(base)
    mut(d, base)
    with pytest.raises((A.InputsError, ValueError), match=match):
        run(d, base)


def _wall(d, code, fl, wid):
    ln = next(x for x in d["lines"] if x["item_code"] == code and x["floor"] == fl)
    return ln, next(w for w in ln["walls"] if w["wall_id"] == wid)


def test_held_wall_as_zero_refused():
    def m(d, b):
        _wall(d, "MAS.BLOCK", "GF", "W5")[1]["carried"] = 0.0
    _refused(m, "BLANK in the BOQ, never 0")


def test_drop_term_evaluated_refused():
    def m(d, b):
        _wall(d, "MAS.BLOCK", "GF", "W6")[1]["carried"] = 6.0
    _refused(m, "never evaluated")


def test_wall_twice_under_two_lines_refused():
    def m(d, b):
        ln = next(x for x in d["lines"] if x["item_code"] == "MAS.BLOCK" and x["floor"] == "1F")
        ln["walls"].append(copy.deepcopy(_wall(d, "MAS.BLOCK", "GF", "W2")[1]))
    _refused(m, "one line per wall per item")


def test_verified_without_checker_run_refused():
    def m(d, b):
        _wall(d, "MAS.BLOCK", "GF", "W1")[1]["verified_by"] = None
    _refused(m, "VERIFIED names the checker run")


def test_owner_approved_without_source_refused():
    def m(d, b):
        _wall(d, "MAS.BLOCK", "GF", "W3")[1]["owner_source"] = None
    _refused(m, "answered owner decision")


def test_released_wall_zero_refused():
    def m(d, b):
        _wall(d, "MAS.BLOCK", "GF", "W2")[1]["carried"] = 0.0
    _refused(m, "never 0")


def test_volume_at_wrong_thickness_refused():
    def m(d, b):
        ln, w = _wall(d, "ARCH.WALL_VOLUME", "GF", "W2")
        w["carried"] = 10.8 * 0.15
        ln["declared"] = _decl(ln["walls"])
    _refused(m, "x t 0.2")


def test_panel_not_block_refused():
    def m(d, b):
        ln, w = _wall(d, "ARCH.WALL_PANEL", "GF", "W2")
        w["carried"] = 10.9
        ln["declared"] = _decl(ln["walls"])
    _refused(m, "is not the MAS.BLOCK")


def test_declared_figure_not_reproduced_refused():
    def m(d, b):
        next(x for x in d["lines"] if x["item_code"] == "MAS.BLOCK" and x["floor"] == "GF")["declared"]["verified"] = 13.0
    _refused(m, "declared verified")


def test_millimetres_refused():
    def m(d, b):
        for x in d["lines"]:
            if x["floor"] == "GF":
                x["family"] = 200
    _refused(m, "thickness")


def test_unknown_status_refused():
    def m(d, b):
        _wall(d, "MAS.BLOCK", "GF", "W2")[1]["status"] = "CONVENTION"
    _refused(m, "status 'CONVENTION'")


def test_parent_with_a_figure_refused():
    base = lines_3025()
    d = doc(base)
    lid = _id(base, "MAS.BLOCK", "GF")
    i = next(i for i, x in enumerate(base) if x["line_id"] == lid)
    base[i] = _ln("MAS.BLOCK", "GF-WALLS:walls t=0.20", "SOURCE_DERIVED", 50.0, formula="engine figure = 50.0 m2")
    with pytest.raises(A.InputsError, match="stale fill"):
        run(d, base)


def test_line_not_in_the_candidate_refused():
    base = lines_3025()
    d = doc(base)
    d["lines"][0]["line_id"] = "L-00000000000000000000"
    with pytest.raises(A.InputsError, match="does not carry"):
        run(d, base)


def test_applied_twice_refused():
    out, *_ = run()
    with pytest.raises(A.InputsError, match="already filled|stale fill"):
        run(doc(out), out)


def test_part_released_inside_a_parent_with_a_figure_refused():
    out, *_ = run()
    par = next(i for i, ln in enumerate(out) if ln["item_code"] == "MAS.BLOCK" and ln["location"]["floor"] == "GF"
               and "#" not in ln["location"]["element_id"])
    bad = copy.deepcopy(out)
    bad[par]["evidence_state"] = "SOURCE_DERIVED"
    bad[par]["measured_net"] = 42.94
    with pytest.raises(ValueError, match="carries a figure"):
        A.check_blockwork(bad)


def test_wall_released_twice_refused():
    out, *_ = run()
    bad = copy.deepcopy(out)
    p = [ln for ln in bad if ln["item_code"] == "MAS.BLOCK" and "#BLOCKWORK:" in ln["location"]["element_id"]]
    p[1]["calculation"]["inputs"]["blockwork_fill_v3026"]["pieces"].append(
        dict(p[0]["calculation"]["inputs"]["blockwork_fill_v3026"]["pieces"][0],
             status=p[1]["calculation"]["inputs"]["blockwork_fill_v3026"]["status"],
             block_type=p[1]["calculation"]["inputs"]["blockwork_fill_v3026"]["block_type"]))
    with pytest.raises(ValueError, match="released twice|!= its walls"):
        A.check_blockwork(bad)
