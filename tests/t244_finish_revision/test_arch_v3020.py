"""T-244: ARCH_TAKEOFF_V3.0.20 (room-face finish deductions brought to merged opening outlines) on a hand-calculated
NON-Alsenan villa (K244), normal and adverse.

Villa K244, owner manual method (face x owner height, less every opening by its own area; one figure for plaster and
paint), hand calculation:
  R1 (1F, H 3.20): face 18.000 m -> gross 57.600; door D1 0.90 x 2.20 = 1.980; arched window AW1 carried as its band
     rectangle 1.40 x 2.80 = 3.920 -> RELEASED 51.700. The merged ledger: AW1 room-side outline 3.300 .. 3.450 (head
     soffit through the curved wall not drawn) -> BOUNDED 57.600 - 1.980 - 3.450 = 52.170 .. 52.320 (the released 51.700
     is LOW by 0.470 .. 0.620 m2: it leaves the released total).
  R2 (1F, H 3.20): face 25.000 -> 80.000; doors 2 x 1.980; arched window AW2 HELD 3.70969 .. 3.920; lift door HELD
     0 .. 2.420 -> BOUNDED 69.700 .. 72.33031. The merged ledger: AW2 semicircular head, width 1.40, springing 2.10:
     1.40 x 2.10 + pi x 0.70^2 / 2 = 2.940 + 0.769690 = 3.709690 -> BOUNDED 69.910310 .. 72.330310 (lift door still held).
  R3 (GF, H 3.65): face 12.000 -> 43.800; door D3 carried 0.85 x 2.20 = 1.870 (rebate side), window W5 1.20 x 1.50 =
     1.800 -> RELEASED 40.130. The merged census: D3 0.90 x 2.20 = 1.980 (frame rule) -> RELEASED 40.020 (-0.110).
  R4 (annex): held without a figure (roof datum): the D4 width delta is NOT_APPLIED (carrier: the annex height).
  W5 in R3: CARRIED (1.800 already, named once on both lines).
Totals FIN.PLASTER (and FIN.PAINT): released 91.830 -> 40.020; bounded [69.700, 72.33031] -> R1 + R2
[122.08031, 124.65031].
"""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3020 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k244", "f" * 64
AW2 = round(1.40 * 2.10 + math.pi * 0.70 ** 2 / 2, 6)        # 3.70969


def _om(face, h, deds):
    return {"height_m": h, "face_m": face, "gross": round(face * h, 6),
            "deductions": [dict({"opening": o}, **({"m2": v} if not isinstance(v, list) else {"range": v}),
                                basis="k244") for o, v in deds]}


def _ln(code, room, ev, net=None, br=None, om=None, floor="1F"):
    fin = code.split(".")[-1]
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m2", evidence_state=ev,
                      measured_net=net, element_id=f"HL:WALL_FINISH:{room}:{fin}", floor=floor, room_id=f"{room}-R",
                      physical_element=f"wall face {fin.lower()}", formula="face x owner height less openings",
                      bounded_range=br, rfi=None if ev in BL.QUANTITY_STATES else {"question": "held", "unlocks": room},
                      documents=[{"file": "k244.dxf"}], rule_id="Q-43", rule_version="owner", notes="k244",
                      inputs={"room": room, "owner_manual_method": copy.deepcopy(om), "drawing_derived_method": {"note": "beside"},
                              "record_state": "x"})
    return ln


def lines():
    r1 = _om(18.0, 3.20, [("D1 door", 1.98), ("AW1 arched", 3.92)])
    r2 = _om(25.0, 3.20, [("D2a door", 1.98), ("D2b door", 1.98), ("AW2 arched", [AW2, 3.92]),
                          ("LIFT door", [0.0, 2.42])])
    r3 = _om(12.0, 3.65, [("D3 door", 1.87), ("W5 window", 1.80)])
    out = []
    for code in A.CODES:
        out += [_ln(code, "R1", "PROVISIONAL", 51.70, om=r1),
                _ln(code, "R2", "BOUNDED_EXPOSURE", br={"low": 69.70, "high": 72.33031, "basis": "held"}, om=r2),
                _ln(code, "R3", "PROVISIONAL", 40.13, om=r3, floor="GF"),
                _ln(code, "R4", "BLOCKED_RFI", om={"height_m": 3.15, "status": "PROVISIONAL"}, floor="GF")]
    out.append(BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="ARCH.WINDOW", unit="m2",
                            evidence_state="SOURCE_DERIVED", measured_net=1.8, element_id="K:WIN", floor="GF",
                            formula="W5 1.20 x 1.50", rule_id="R", rule_version="1", documents=[{"file": "k244.dxf"}]))
    return out


def ids(ls):
    return {(ln["calculation"]["inputs"].get("room"), ln["item_code"]): ln["line_id"] for ln in ls
            if ln["item_code"] in A.CODES}


SOURCES = [{"file": "k244_hole.csv", "sha256": "a" * 64, "task": "T-K1", "merge_commit": "m1", "checker_run": "c1"},
           {"file": "k244_census.csv", "sha256": "b" * 64, "task": "T-K2", "merge_commit": "m2", "checker_run": "c2"}]


def records(i, codes=A.CODES):
    out = []
    for c in codes:
        out += [
            {"line_id": i[("R1", c)], "item_code": c, "room": "R1", "task": "T-K1",
             "before": {"evidence_state": "PROVISIONAL", "measured_net": 51.70}, "state": "BOUNDED",
             "range": [52.17, 52.32], "evidence_status": "HELD", "reasons": ["AW1 head soffit not drawn"],
             "revisions": [{"opening": "AW1", "before": {"m2": 3.92}, "after": {"range": [3.30, 3.45]},
                            "source_task": "T-K1", "why": "band rectangle -> room-side outline"}]},
            {"line_id": i[("R2", c)], "item_code": c, "room": "R2", "task": "T-K1",
             "before": {"evidence_state": "BOUNDED_EXPOSURE", "bounded_range": [69.70, 72.33031]}, "state": "BOUNDED",
             "range": [69.91031, 72.33031], "evidence_status": "HELD", "reasons": ["LIFT door head not printed"],
             "revisions": [{"opening": "AW2", "before": {"range": [AW2, 3.92]}, "after": {"m2": AW2},
                            "source_task": "T-K1", "why": "semicircular outline"}]},
            {"line_id": i[("R3", c)], "item_code": c, "room": "R3", "task": "T-K2",
             "before": {"evidence_state": "PROVISIONAL", "measured_net": 40.13}, "state": "RELEASED", "value": 40.02,
             "evidence_status": "ASSUMED - OWNER-APPROVED", "assumption": "owner height G1, door head 2.20 Q-55 C",
             "revisions": [{"opening": "D3", "before": {"m2": 1.87}, "after": {"m2": 1.98},
                            "source_task": "T-K2", "why": "frame rule 0.85 + 0.05 -> 0.90"}]}]
    return out


def deltas(i):
    return [{"opening": "W5", "room": "R3", "kind": "CARRIED", "task": "T-K2", "why": "census agrees",
             "line_ids": [i[("R3", c)] for c in A.CODES], "m2": 1.80},
            {"opening": "D4", "room": "R4", "kind": "NOT_APPLIED", "task": "T-K2", "why": "annex line has no figure",
             "line_ids": [i[("R4", c)] for c in A.CODES], "carrier": "annex height G2", "value_delta": -0.11}]


def doc(i, **kw):
    d = {"schema": A.INPUTS_SCHEMA, "project": PID, "sources": copy.deepcopy(SOURCES), "records": records(i),
         "deltas": deltas(i)}
    d.update(kw)
    return d


def run(ls, d):
    A.load_inputs(d, PID)
    ch, log, dl = A.changes_for(d, ls)
    return A.integrate(ls, ch), ch, log, dl


# ------------------------------------------------------------------------------------------------ normal
def test_hand_values_and_states():
    ls = lines()
    i = ids(ls)
    (out, ident), ch, log, dl = run(ls, doc(i))
    by = {ln["line_id"]: ln for ln in out}
    for c in A.CODES:
        r1, r2, r3 = by[i[("R1", c)]], by[i[("R2", c)]], by[i[("R3", c)]]
        assert r1["evidence_state"] == "BOUNDED_EXPOSURE" and r1["measured_net"] is None
        assert (r1["bounded_range"]["low"], r1["bounded_range"]["high"]) == (52.17, 52.32)
        assert r1["rfi"]["question"] and r1["source"]["geometry_confidence"] == "INFERRED_CANDIDATE"
        assert r2["bounded_range"]["low"] == pytest.approx(80 - 3.96 - AW2 - 2.42, abs=1e-6)
        assert r2["bounded_range"]["high"] == pytest.approx(80 - 3.96 - AW2, abs=1e-6)
        assert r3["evidence_state"] == "PROVISIONAL" and r3["measured_net"] == 40.02
        om = r3["calculation"]["inputs"]["owner_manual_method"]
        d3 = [d for d in om["deductions"] if d["opening"] == "D3 door"][0]
        assert d3["m2"] == 1.98 and d3["revised_by"]["before"]["m2"] == 1.87
        assert r3["calculation"]["inputs"]["owner_net_recomputed"] == [40.02, 40.02]
    assert ident["replaced"] == 6 and ident["outside_rows"] == len(ls) - 6 and ident["added"] == 0
    kinds = log["delta_kinds"]
    assert kinds == {"CARRIED": 1, "NOT_APPLIED": 1, "REVISED": 6}
    assert AW2 == pytest.approx(3.709690, abs=1e-6)


def test_totals_move_only_on_the_two_codes():
    from engine.source import arch_v304 as A304
    ls = lines()
    i = ids(ls)
    (out, _), *_ = run(ls, doc(i))
    t0, t1 = A304.code_totals(ls), A304.code_totals(out)
    assert {k.split("|")[0] for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)} == set(A.CODES)
    rel0 = sum(ln["measured_net"] for ln in ls if ln["item_code"] == "FIN.PLASTER" and ln["measured_net"])
    rel1 = sum(ln["measured_net"] for ln in out if ln["item_code"] == "FIN.PLASTER" and ln["measured_net"])
    assert rel0 == pytest.approx(91.83) and rel1 == pytest.approx(40.02)
    lo = sum(ln["bounded_range"]["low"] for ln in out if ln["item_code"] == "FIN.PLASTER" and ln["bounded_range"])
    hi = sum(ln["bounded_range"]["high"] for ln in out if ln["item_code"] == "FIN.PLASTER" and ln["bounded_range"])
    assert (lo, hi) == (pytest.approx(122.08031), pytest.approx(124.65031))


def test_held_stays_held_never_zero_and_outside_lines_identical():
    from engine.source import arch_v30 as A30
    ls = lines()
    i = ids(ls)
    (out, _), *_ = run(ls, doc(i))
    by0 = {ln["line_id"]: ln for ln in ls}
    for ln in out:
        if ln["line_id"] not in {r["line_id"] for r in records(i)}:
            assert A30.line_sha(ln) == A30.line_sha(by0[ln["line_id"]])
        assert ln["measured_net"] != 0
    for c in A.CODES:
        r4 = [ln for ln in out if ln["line_id"] == i[("R4", c)]][0]
        assert r4["evidence_state"] == "BLOCKED_RFI" and r4["measured_net"] is None


def test_deduction_order_does_not_change_the_net():
    """the 'rotation / mirror' case of a list method: the same deductions in another order give the same figure."""
    ls = lines()
    for ln in ls:
        om = ln["calculation"]["inputs"].get("owner_manual_method") or {}
        if om.get("deductions"):
            om["deductions"] = list(reversed(om["deductions"]))
    i = ids(ls)
    (out, _), *_ = run(ls, doc(i))
    r2 = [ln for ln in out if ln["line_id"] == i[("R2", "FIN.PAINT")]][0]
    assert r2["bounded_range"]["low"] == pytest.approx(69.91031, abs=1e-6)


def test_write_files(tmp_path):
    ls = lines()
    i = ids(ls)
    d = doc(i)
    A.load_inputs(d, PID)
    ch, log, dl = A.changes_for(d, ls)
    names, ident, led = A.write(tmp_path, ls, ch, log, dl, d, released_lines=ls[:2])
    assert "V3_0_20_OPENING_DELTAS.csv" in names and led["integration_package"] is True
    assert ident["diff"]["vs_v3_0_19"] == {"CHANGED": 6, "SAME": len(ls) - 6}
    txt = (tmp_path / "V3_0_20_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")
    assert "AW1 arched 3.92 -> [3.3, 3.45] (T-K1)" in txt


# ------------------------------------------------------------------------------------------------ adverse
def _refused(mut, match):
    ls = lines()
    i = ids(ls)
    d = doc(i)
    mut(d, i, ls)
    with pytest.raises(A.InputsError, match=match):
        run(ls, d)


def test_adverse_stale_before_value():
    _refused(lambda d, i, ls: d["records"][2].update(before={"evidence_state": "PROVISIONAL", "measured_net": 40.0}),
             "stale ledger")


def test_adverse_stale_before_range():
    _refused(lambda d, i, ls: d["records"][1].update(before={"evidence_state": "BOUNDED_EXPOSURE",
                                                             "bounded_range": [69.0, 72.33031]}), "stale ledger")


def test_adverse_deduction_before_not_the_lines():
    def m(d, i, ls):
        d["records"][2]["revisions"][0]["before"] = {"m2": 1.80}
    _refused(m, "stale ledger")


def test_adverse_opening_not_on_the_line():
    def m(d, i, ls):
        d["records"][2]["revisions"][0]["opening"] = "D9"
    _refused(m, "0 times")


def test_adverse_opening_named_twice_on_the_line():
    def m(d, i, ls):
        for ln in ls:
            om = ln["calculation"]["inputs"].get("owner_manual_method") or {}
            if ln["calculation"]["inputs"].get("room") == "R3":
                om["deductions"].append({"opening": "D3 door (again)", "m2": 1.87})
    _refused(m, "2 times")


def test_adverse_recomputed_net_disagrees():
    _refused(lambda d, i, ls: d["records"][2].update(value=40.13), "net recomputed")


def test_adverse_mm_units_refused():
    def m(d, i, ls):   # a hole given in mm2 / mm units cannot close the net
        d["records"][2]["revisions"][0]["after"] = {"m2": 1980.0}
    _refused(m, "net recomputed")


def test_adverse_released_with_a_held_deduction():
    def m(d, i, ls):
        d["records"][0].update(state="RELEASED", value=52.17, evidence_status="DRAWING-CONFIRMED", assumption="h")
    _refused(m, "every deduction known")


def test_adverse_bounded_with_every_deduction_known():
    def m(d, i, ls):
        d["records"][2].update(state="BOUNDED", range=[40.02, 40.02], evidence_status="HELD", reasons=["x"])
    _refused(m, "every deduction known")


def test_adverse_zero_deduction():
    def m(d, i, ls):
        d["records"][2]["revisions"][0]["after"] = {"m2": 0}
    _refused(m, "never 0")


def test_adverse_verified_without_checker_run():
    _refused(lambda d, i, ls: d["records"][2].update(evidence_status="VERIFIED"), "checker run")


def test_adverse_stale_twin_one_code_only():
    def m(d, i, ls):
        d["records"] = records(i, codes=("FIN.PLASTER",))
    _refused(m, "stale twin")


def test_adverse_not_applied_on_a_line_with_a_figure():
    def m(d, i, ls):
        d["deltas"][1] = {"opening": "D3", "room": "R3", "kind": "NOT_APPLIED", "task": "T-K2", "why": "x",
                          "line_ids": [], "carrier": "y"}
        d["records"] = [r for r in d["records"] if r["room"] != "R3"]
    _refused(m, "REVISION record is due")


def test_adverse_carried_value_differs():
    def m(d, i, ls):
        d["deltas"][0]["m2"] = 1.65
    _refused(m, "the delta 1.65")


def test_adverse_unknown_line_and_wrong_room():
    _refused(lambda d, i, ls: d["records"][0].update(line_id="L-nothing"), "carries no line")
    ls = lines()
    i = ids(ls)
    d = doc(i)
    d["records"][0]["room"] = "R9"
    with pytest.raises(A.InputsError, match="the record"):
        run(ls, d)


def test_adverse_load_inputs():
    ls = lines()
    i = ids(ls)
    for mut, match in [(lambda d: d.update(schema="x"), "schema"),
                       (lambda d: d.update(sources=[]), "sources"),
                       (lambda d: d["records"].append(copy.deepcopy(d["records"][0])), "named twice"),
                       (lambda d: d["records"][0].update(task="T-X"), "not one of the sources"),
                       (lambda d: d["records"][0].update(item_code="FIN.WALL.TILE"), "not one of"),
                       (lambda d: d["records"][0]["revisions"][0].pop("why"), "why"),
                       (lambda d: d["records"][0].update(reasons=[]), "names why"),
                       (lambda d: d["deltas"][1].pop("carrier"), "carrier"),
                       (lambda d: d["records"][0]["revisions"][0].update(after={"range": [3.5, 3.3]}), "range")]:
        d = doc(i)
        mut(d)
        with pytest.raises(A.InputsError, match=match):
            A.load_inputs(d, PID)


def test_adverse_change_outside_quantity_is_refused():
    ls = lines()
    i = ids(ls)
    d = doc(i)
    A.load_inputs(d, PID)
    ch, *_ = A.changes_for(d, ls)
    ch[0]["after"]["location"]["floor"] = "2F"
    with pytest.raises(ValueError, match="outside quantity"):
        A.integrate(ls, ch)
