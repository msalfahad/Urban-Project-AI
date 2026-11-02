"""T-431: ARCH_TAKEOFF_V3.0.41 (a piece cut off by a zone edge prolonged past its own drawn end becomes room floor; the
zone lines give the parts up by id; bed pair, skirting and ceiling follow in the same step) on a hand-calculated
NON-Alsenan villa (K431).

Villa K431, by hand (own figures; nothing from the development villa). Open living room R1, floor line 60.000 m2
(PROVISIONAL, finish owner-approved). A planter zone P drawn 4.00 .. 10.00 m along the facade, 1.45 m deep (curb 0.25),
its west end line drawn at 4.00. The engine prolonged the zone edge west to the room's west wall (x 1.00), so:
  Z1  zone face west of the end line: 3.00 x 1.20 - column notch 0.80 x 0.05 = 3.560 m2   (ARCH.SPACE line, held)
  ST  strip line 1.250 m2 = west strip 3.00 x 0.25 = 0.750 + curb strip 2.00 x 0.25 = 0.500 (ARCH.SPACE, held)
Nothing is drawn between Z1 / the west strip and R1 (R-T427-1): piece = 3.560 + 0.750 = 4.310 m2 of room floor.
  Z1 RETIRED (no quantity, owned by the new line); ST 1.250 -> 0.500 (curb kept, held).
  Bed (GF dry b 0.06; owner 0.03 .. 0.04): m2 4.310, m3 0.1293 .. 0.1724.
  Skirting of R1: gross 30.000 - opening 2.000 = 28.000 lm; + wall 3.00 - 0.80 = 2.200 + column 0.05 + 0.80 + 0.05 =
  0.900 -> 31.100 lm.
  Ceiling: decor 3.560 (ledger face), paint 3.560 (bulkhead HELD), bulkhead HELD blank (edge 4.20 m), the west strip's
  ceiling HELD blank (0.750 beside). 3.560 + 0.750 = 4.310 (one plan area).
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3037 as A3037  # noqa: E402
from engine.source import arch_v3041 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k431", "f" * 64
DOCS = [{"file": "k431_plan.dxf", "sha256": "d" * 64}]
OWNER = "ASSUMED — OWNER-APPROVED"


def _src(t):
    return {"task": t, "file": f"research/k431/{t}.json", "sha256": t[-1] * 64, "merge_commit": "a" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _ln(code, unit, eid, ev="PROVISIONAL", net=None, room=None, **kw):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor="GF", room_id=room, formula=f"{code} {eid}",
                        documents=DOCS, rule_id="K", rule_version="1", notes="k", **kw)


def lines_3040():
    floor = _ln("FIN.FLOOR.PORCELAIN", "m2", "R1:floor", net=60.0, room="R1", gross=60.0,
                inputs={"evidence_status": OWNER})
    z1 = _ln("ARCH.SPACE", "m2", "Z1:space", net=3.56, room="Z1", gross=3.56)
    st = _ln("ARCH.SPACE", "m2", "ST:space", net=1.25, room="ST", gross=1.25)
    sk = _ln("FIN.SKIRTING", "lm", "R1:skirting", ev="SOURCE_DERIVED", net=28.0, room="R1", gross=30.0,
             deductions=[{"id": "OP-1", "unit": "lm", "qty": 2.0, "what": "door"}])
    ce = _ln("FIN.CEILING", "m2", "R1:ceiling", net=55.0, room="R1", gross=55.0)
    other = _ln("FIN.FLOOR.PORCELAIN", "m2", "R2:floor", ev="SOURCE_DERIVED", net=12.0, room="R2", gross=12.0)
    return [floor, z1, st, sk, ce, other]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def inputs(lines, **over):
    z1, st = _id(lines, "Z1:space"), _id(lines, "ST:space")
    piece = {"piece": "P-WEST", "room": "Z1", "floor": "GF", "joins_room": "R1", "area_status": "DRAWING-CONFIRMED",
             "finish": "porcelain (owner default, as R1)", "finish_status": OWNER, "zone": "GF-DRY", "b": 0.06,
             "b_upper": None, "template_line": _id(lines, "R1:floor"),
             "parts": [{"id": "Z1:west-face", "area": 3.56, "from_line": z1},
                       {"id": "Z1:west-strip", "area": 0.75, "from_line": st}],
             "zone_lines": [{"line_id": z1, "action": "RETIRE", "value_before": 3.56, "parts": ["Z1:west-face"]},
                            {"line_id": st, "action": "SHRINK", "value_before": 1.25, "parts": ["Z1:west-strip"],
                             "keeps": [{"id": "curb", "area": 0.5, "why": "planter curb (designer)"}]}],
             "skirting": {"line_id": _id(lines, "R1:skirting"), "net_before": 28.0,
                          "rows": [{"id": "Z1:wall", "kind": "wall", "qty": 2.2, "what": "wall face"},
                                   {"id": "Z1:column", "kind": "column", "qty": 0.9, "what": "column faces"}]},
             "ceiling": {"face": "Z1", "decor_m2": 3.56, "decor_status": "DRAWING-CONFIRMED",
                         "template_line": _id(lines, "R1:ceiling"), "class_of": "R1", "bulkhead_edge_m": 4.2,
                         "bulkhead_why": "depth not decided",
                         "unread": [{"id": "Z1:west-strip", "area": 0.75, "why": "no ceiling reading"}]},
             "source_tasks": ["T-427", "T-440", "T-283", "T-414"]}
    for k, v in over.pop("piece", {}).items():
        piece[k] = v
    doc = {"schema": A.INPUTS_SCHEMA, "project_id": PID,
           "sources": [_src("T-427"), _src("T-440"), _src("T-283"), _src("T-414")],
           "owner_bed": {"DRY": {"lo": 0.03, "hi": 0.04, "rule": "owner bed range"}}, "pieces": [piece]}
    doc.update(over)
    return doc


def run(lines=None, doc=None):
    lines = lines or lines_3040()
    d = A.load_inputs(doc if doc is not None else inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, log


def _e(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


def _dry(lines):
    return round(sum(x["measured_net"] for x in lines if x["item_code"] == "FIN.FLOOR.PORCELAIN"
                     and x["evidence_state"] in A.VALUED), 6)


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures_k431():
    lines, out, ident, ch, log = run()
    fl = _e(out, "Z1:P-WEST")
    assert fl["item_code"] == "FIN.FLOOR.PORCELAIN" and fl["measured_net"] == pytest.approx(4.31, abs=1e-9)
    assert fl["evidence_state"] == "SOURCE_DERIVED"
    assert fl["calculation"]["inputs"]["evidence_status"] == OWNER
    assert _dry(lines) == pytest.approx(72.0) and _dry(out) == pytest.approx(76.31)
    z1 = _e(out, "Z1:space")
    assert z1["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and z1["measured_net"] is None
    assert z1["calculation"]["inputs"][A.REC_KEY]["owned_by"] == fl["line_id"]
    st = _e(out, "ST:space")
    assert st["measured_net"] == pytest.approx(0.5, abs=1e-9) and st["evidence_state"] == "PROVISIONAL"
    sk = _e(out, "R1:skirting")
    assert sk["measured_net"] == pytest.approx(31.1, abs=1e-9)
    assert [a["id"] for a in sk["additions"]] == ["Z1:wall", "Z1:column"]
    assert sk["gross"] - sum(d["qty"] for d in sk["deductions"]) + sum(a["qty"] for a in sk["additions"]) == \
        pytest.approx(31.1)
    bed2 = next(x for x in out if x["item_code"] == A3037.BED_DRY and x["unit"] == "m2")
    bed3 = next(x for x in out if x["item_code"] == A3037.BED_DRY and x["unit"] == "m3")
    assert bed2["measured_net"] == pytest.approx(4.31)
    assert bed3["bounded_range"]["low"] == pytest.approx(0.1293) and bed3["bounded_range"]["high"] == pytest.approx(0.1724)
    dec, pai = _e(out, "Z1:decor"), _e(out, "Z1:paint")
    assert dec["item_code"] == "FIN.CEILING" and dec["measured_net"] == pytest.approx(3.56)
    assert pai["item_code"] == "FIN.PAINT.CEILING" and pai["measured_net"] == pytest.approx(3.56)
    blk, un = _e(out, "Z1:bulkhead"), _e(out, "Z1:west-strip:ceiling")
    for h in (blk, un):
        assert h["evidence_state"] == "BLOCKED_RFI" and h["measured_net"] is None and h["rfi"]["question"]
    assert un["calculation"]["inputs"][A.REC_KEY]["area_beside"] == pytest.approx(0.75)
    p = ident["pieces"]
    assert p["pieces"] == 1 and p["floor_m2"] == pytest.approx(4.31) and p["zone_given_m2"] == pytest.approx(4.31)
    assert p["overlap_m2"] == 0 and p["retired"] == 1 and p["shrunk"] == 1 and p["skirting_added_lm"] == pytest.approx(3.1)
    assert p["ceiling_decor_m2"] == pytest.approx(3.56) and p["ceiling_held_lines"] == 2
    assert ident["added"] == 7 and ident["replaced"] == 3 and ident["v3_0_41_lines"] == len(lines) + 7
    assert log["by_action"] == {"ADD_BED": 2, "ADD_BULKHEAD_HELD": 1, "ADD_CEILING": 1, "ADD_CEILING_HELD": 1,
                                "ADD_FLOOR": 1, "ADD_PAINT": 1, "ADD_SKIRTING": 1, "RETIRE_ZONE": 1, "SHRINK_ZONE": 1}


def test_every_other_line_byte_identical():
    lines, out, ident, ch, log = run()
    by = {x["line_id"]: x for x in out}
    for k in ("R1:floor", "R1:ceiling", "R2:floor"):
        o = next(x for x in lines if x["location"]["element_id"] == k)
        assert A30.line_sha(o) == A30.line_sha(by[o["line_id"]])
    assert ident["outside_rows_identical_to_v3_0_40"] == len(lines) - 3


def test_overlap_none_band_curb_wall():
    """own overlap test: the floor piece, the kept curb and the room floor never share an m2: zone area before =
    floor piece + kept curb; the room line is untouched."""
    lines, out, ident, ch, log = run()
    before = sum(x["measured_net"] for x in lines if x["item_code"] == "ARCH.SPACE")
    after = sum(x["measured_net"] or 0 for x in out if x["item_code"] == "ARCH.SPACE")
    assert before == pytest.approx(_e(out, "Z1:P-WEST")["measured_net"] + after)
    assert _e(out, "R1:floor")["measured_net"] == 60.0


def test_input_order_and_mirror_free():
    """the module takes areas and ids, no coordinate: a mirrored / rotated villa gives the same inputs; the order of
    parts and zone lines does not change the result."""
    lines = lines_3040()
    doc = inputs(lines)
    d2 = copy.deepcopy(doc)
    random.Random(431).shuffle(d2["pieces"][0]["parts"])
    d2["pieces"][0]["zone_lines"].reverse()
    a = run(lines, doc)[1]
    b = run(lines, d2)[1]
    assert sorted(A30.line_sha(x) for x in a) == sorted(A30.line_sha(x) for x in b)


def test_totals_move_only_own_codes():
    lines, out, *_ = run()
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k.split("|")[0] for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert moved <= set(A.OWN_CODES)


def test_no_project_input():
    ch, log = A.changes_for(None, lines_3040())
    assert ch == [] and log["state"] == "NO_PROJECT_INPUT"


# ------------------------------------------------------------------------------------------------ adverse
def test_adverse_zone_prolonged_past_its_drawn_end_keeps_the_part():
    """'a zone prolonged past its own drawn end': the strip line still keeps the west strip (it gives up nothing):
    the part would be held twice -> refused."""
    lines = lines_3040()
    doc = inputs(lines)
    z = doc["pieces"][0]["zone_lines"][1]
    z["parts"] = []
    z["keeps"] = [{"id": "curb", "area": 0.5, "why": "c"}, {"id": "west", "area": 0.75, "why": "prolonged edge"}]
    with pytest.raises(A.InputsError):
        A.load_inputs(doc, PID)


def test_adverse_part_held_by_no_line():
    lines = lines_3040()
    doc = inputs(lines)
    doc["pieces"][0]["zone_lines"] = doc["pieces"][0]["zone_lines"][:1]
    with pytest.raises(A.InputsError, match="given up by no zone line"):
        A.load_inputs(doc, PID)


def test_adverse_area_not_closed():
    lines = lines_3040()
    doc = inputs(lines)
    doc["pieces"][0]["zone_lines"][1]["keeps"][0]["area"] = 0.45
    with pytest.raises(A.InputsError, match="no area lost"):
        A.load_inputs(doc, PID)


def test_adverse_held_as_zero_and_mm():
    lines = lines_3040()
    doc = inputs(lines)
    doc["pieces"][0]["parts"][1]["area"] = 0
    with pytest.raises(A.InputsError, match="HELD_AS_ZERO"):
        A.load_inputs(doc, PID)
    doc = inputs(lines)
    doc["pieces"][0]["parts"][0]["area"] = 3560000.0
    with pytest.raises(A.InputsError, match="mm2 refused"):
        A.load_inputs(doc, PID)
    doc = inputs(lines)
    doc["pieces"][0]["skirting"]["rows"][0]["qty"] = 2200.0
    with pytest.raises(A.InputsError, match="mm refused"):
        A.load_inputs(doc, PID)


def test_adverse_missing_data():
    lines = lines_3040()
    doc = inputs(lines)
    doc["owner_bed"] = {}
    with pytest.raises(A.InputsError, match="DEFAULTED_THICKNESS"):
        A.load_inputs(doc, PID)
    doc = inputs(lines)
    doc["pieces"][0]["b"] = None
    with pytest.raises(A.InputsError):
        A.load_inputs(doc, PID)
    doc = inputs(lines)
    doc["pieces"][0]["area_status"] = "UNKNOWN"
    with pytest.raises(A.InputsError, match="area status"):
        A.load_inputs(doc, PID)


def test_adverse_stale_bindings():
    lines = lines_3040()
    doc = inputs(lines)
    doc["pieces"][0]["skirting"]["net_before"] = 27.9
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(doc, PID), lines)
    doc = inputs(lines)
    doc["pieces"][0]["zone_lines"][0]["value_before"] = 3.6
    doc["pieces"][0]["parts"][0]["area"] = 3.6
    with pytest.raises(A.InputsError):
        d = A.load_inputs(doc, PID)
        A.changes_for(d, lines)
    doc = inputs(lines)
    doc["pieces"][0]["template_line"] = _id(lines, "R1:skirting")
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_adverse_applied_twice_and_face_with_a_ceiling():
    lines, out, *_ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(lines), PID), out)
    lines = lines_3040() + [_ln("FIN.CEILING", "m2", "Z1:ceiling", net=3.56, room="Z1", gross=3.56)]
    with pytest.raises(A.InputsError, match="already carries a ceiling"):
        A.changes_for(A.load_inputs(inputs(lines), PID), lines)


def test_adverse_ceiling_not_one_plan_area():
    lines = lines_3040()
    doc = inputs(lines)
    doc["pieces"][0]["ceiling"]["unread"] = []
    with pytest.raises(A.InputsError, match="one plan area"):
        A.load_inputs(doc, PID)


def test_adverse_retire_keeps_or_shrink_keeps_nothing():
    lines = lines_3040()
    doc = inputs(lines)
    doc["pieces"][0]["zone_lines"][1]["action"] = "RETIRE"
    with pytest.raises(A.InputsError, match="retired line keeps nothing"):
        A.load_inputs(doc, PID)


def test_check_pieces_catches_tampering():
    lines, out, *_ = run()
    bad = copy.deepcopy(out)
    st = _e(bad, "ST:space")
    st["measured_net"] = 1.25          # the strip line still carries the moved part: double count
    with pytest.raises(ValueError):
        A.check_pieces(bad)
    bad = copy.deepcopy(out)
    _e(bad, "Z1:bulkhead")["measured_net"] = 0.0       # held as 0
    with pytest.raises(ValueError):
        A.check_pieces(bad)
    bad = copy.deepcopy(out)
    _e(bad, "Z1:paint")["measured_net"] = 4.31         # paint not decor
    with pytest.raises(ValueError):
        A.check_pieces(bad)


def test_policy_record():
    r = A.policy_record()
    assert r["released_default"] is False and r["method"] == "ARCH_TAKEOFF_V3.0.41"
    assert A.EXTENDS == "ARCH_TAKEOFF_V3.0.40"
