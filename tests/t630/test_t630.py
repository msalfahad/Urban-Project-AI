"""T-630: 10 NOV END-TO-END BOQ DRY RUN (R-T630-1).

Synthetic villa K630 (not the training villa; hand values):
  B10 m3: slab L1 10.5 (VERIFIED_WHOLE binding) + slab L2 4.25 (no stamp) = slab BOQ line 14.75 TOTAL;
          beam L3 HELD 1.0 .. 1.4; beam L12 2.0 (VERIFIED_COMPONENT binding on 1.8, moved by a DRAWING-CONFIRMED SET:
          stale -> DRAWING-CONFIRMED) -> trade m3 released 16.75, NO TOTAL (1 HELD bounded 1.0 .. 1.4).
  B11 kg: L4 1234.5678 kg + L5 HELD blank -> released 1234.5678 kg = 1.234568 t displayed, NO TOTAL (1 HELD blank).
  B4 m2:  L6 plaster 20 + L7 EXCLUDED -> TOTAL 20 (1 line not a BOQ line).
  B9 m2:  L10 ARCH.WALL_PANEL 12 + L11 MAS.BLOCK 12 -> REGISTER_BESIDE_WORK flagged; re-add 24 is arithmetic only.
  UNCODED: L8 MAS.UNITS.BLACK 125 pcs ADDed ASSUMED - OWNER-APPROVED (no family); L9 ARCH.EXTERIOR 9 m2 NOT_A_BOQ_LINE.
  Families B9-04 (no item code) and B12-01 (no item code) MISSING.
Adverse: a code owned by two families; a group outside B1 .. B13; a line without a unit; a non s.5 op status; an
unknown binding; WORKER-PROPOSED; a tampered family sum (aggregation break); a HELD high open; a census that disagrees.
Then the training-villa build must equal the committed outputs and close by hand."""

import copy
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t630"))
import e2e_dry_run as E          # noqa: E402


def _l(lid, code, unit, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": "K630:" + lid, "class": cls,
            "measured_net": v, "held_low": lo, "held_high": hi}


def _villa():
    L = [_l("L1", "STR.CONC.SLAB", "m3", v=10.5), _l("L2", "STR.CONC.SLAB", "m3", v=4.25),
         _l("L3", "STR.CONC.BEAM", "m3", "HELD", lo=1.0, hi=1.4), _l("L4", "STR.REBAR", "kg", v=1234.5678),
         _l("L5", "STR.REBAR", "kg", "HELD"), _l("L6", "FIN.PLASTER", "m2", v=20),
         _l("L7", "FIN.PLASTER", "m2", "EXCLUDED"), _l("L8", "MAS.UNITS.BLACK", "pcs", v=125),
         _l("L9", "ARCH.EXTERIOR", "m2", v=9), _l("L10", "ARCH.WALL_PANEL", "m2", v=12),
         _l("L11", "MAS.BLOCK", "m2", v=12), _l("L12", "STR.CONC.BEAM", "m3", v=2.0)]
    after = {l["line_id"]: l for l in L}
    bound = {"L1": ({"binding": "VERIFIED_WHOLE", "verdict_id": "K-1"}, E.OV.state(after["L1"])),
             "L12": ({"binding": "VERIFIED_COMPONENT", "verdict_id": "K-2"},
                     {"class": "RELEASED", "measured_net": 1.8, "held_low": None, "held_high": None})}
    order = [("K-PKG", [
        {"op_id": "K|ADD|L8", "package": "K-PKG", "row": "r1", "kind": "ADD", "line_id": "L8",
         "item_code": "MAS.UNITS.BLACK", "evidence": {"status": "ASSUMED — OWNER-APPROVED"}},
        {"op_id": "K|SET|L12", "package": "K-PKG", "row": "r2", "kind": "SET", "line_id": "L12",
         "evidence": {"status": "DRAWING-CONFIRMED"}}])]
    fam = lambda code, grp, codes: {"code": code, "group": grp, "item_en": code, "unit": None, "item_codes": codes,
                                    "capability": "PARTIAL", "candidate": {"state": "INTEGRATED_IN_CANDIDATE_AND_TESTED"}}
    master = {"families": [fam("B10-08", "B10 Concrete", ["STR.CONC.SLAB"]), fam("B10-07", "B10 Concrete",
                                                                                  ["STR.CONC.BEAM"]),
                           fam("B11-01", "B11 Rebar", ["STR.REBAR"]), fam("B4-03", "B4 Walls", ["FIN.PLASTER"]),
                           fam("B9-01", "B9 Masonry", ["ARCH.WALL_PANEL", "MAS.BLOCK"]),
                           fam("B9-04", "B9 Masonry", []), fam("B12-01", "B12 MEP", [])],
              "not_a_boq_line_codes": {"ARCH.EXTERIOR": {}},
              "candidate_census": {"families": {"B4-03": {"units": {"m2": {
                  "lines": 2, "released_lines": 1, "released": 20.0, "held_lines": 0, "excluded_lines": 1,
                  "verified_whole_lines": 0, "verified_component_lines": 0}}}}}}
    return after, bound, order, master


@pytest.fixture
def k():
    after, bound, order, master = _villa()
    owner, item, fam, grp, unit, per_line, unc = E.aggregate(after, bound, order, master)
    return dict(after=after, bound=bound, order=order, master=master, item=item, fam=fam, grp=grp, unit=unit,
                per_line={l["line_id"]: l for l in per_line}, unc=unc)


def test_hand_values_per_trade_and_unit(k):
    b10 = E._out(k["grp"][("B10", "m3")], "m3")
    assert b10["released"] == "16.75" and b10["total"] is None and b10["held_bounded_n"] == 1
    assert (b10["held_low"], b10["held_high"]) == ("1", "1.4") and b10["total_state"].startswith("NO TOTAL")
    slab = E._out(k["item"][("B10", "B10-08", "STR.CONC.SLAB", "m3")], "m3")
    assert slab["total"] == "14.75" and slab["total_state"].startswith("TOTAL")
    b11 = E._out(k["grp"][("B11", "kg")], "kg", rebar=True)
    assert b11["released"] == "1234.5678" and b11["released_t_display"] == "1.234568" and b11["total"] is None
    assert b11["held_blank_n"] == 1 and b11["held_low"] is None          # HELD blank is never 0
    b4 = E._out(k["grp"][("B4", "m2")], "m2")
    assert b4["total"] == "20" and b4["excluded_n"] == 1 and b4["live_lines"] == 1
    assert ("B10", "kg") not in k["grp"] and ("B11", "m3") not in k["grp"]   # never mixed units


def test_evidence_order(k):
    p = k["per_line"]
    assert p["L1"]["evidence"] == "VERIFIED"
    assert p["L12"]["evidence"] == "DRAWING-CONFIRMED" and "stale" in p["L12"]["evidence_basis"]
    assert p["L2"]["evidence"] == "UNKNOWN" and p["L3"]["evidence"] == "HELD"
    assert p["L8"]["evidence"] == "ASSUMED — OWNER-APPROVED" and p["L7"]["evidence"] is None
    # a VERIFIED_COMPONENT binding on an unmoved line is PARTIALLY VERIFIED, never VERIFIED
    after, bound, order, master = _villa()
    bound["L2"] = ({"binding": "VERIFIED_COMPONENT", "verdict_id": "K-3"}, E.OV.state(after["L2"]))
    assert E.evidence_of(after["L2"], bound["L2"], None)[0] == "PARTIALLY VERIFIED"
    # a moved bound line with no op stamp is UNKNOWN, never VERIFIED
    bound["L2"] = ({"binding": "VERIFIED_WHOLE", "verdict_id": "K-4"}, {"class": "RELEASED", "measured_net": 4.0,
                                                                        "held_low": None, "held_high": None})
    assert E.evidence_of(after["L2"], bound["L2"], None)[0] == "UNKNOWN"


def test_uncoded_and_register(k):
    assert k["unc"] == {(E.UNCODED_NO_FAMILY, "MAS.UNITS.BLACK", "pcs"): 1,
                        (E.UNCODED_NOT_A_LINE, "ARCH.EXTERIOR", "m2"): 1}
    d = E.same_quantity_codes(k["item"])
    assert len(d) == 1 and d[0]["codes"] == ["ARCH.WALL_PANEL", "MAS.BLOCK"] and d[0]["kind"].startswith("REGISTER")
    assert E._out(k["grp"][("B9", "m2")], "m2")["released"] == "24"   # arithmetic re-add, flagged above
    assert "released_t_display" not in E._out(k["grp"][(E.UNCODED_NO_FAMILY, "pcs")], "pcs")


def test_proof_and_coverage(k):
    checks = E.proof(k["after"], k["item"], k["fam"], k["grp"], k["unit"])
    assert all(c["re_adds_exactly"] for c in checks)
    m3 = [c for c in checks if c["unit"] == "m3"][0]
    assert m3["released_lines_sum"] == m3["unit_grand"] == "16.75" and m3["held_n"] == 1
    cov = {c["family"]: c["overlay_state"] for c in E.family_coverage(k["master"], k["fam"])}
    assert cov["B9-04"].startswith("MISSING (the family owns no item code")
    assert cov["B12-01"].startswith("MISSING") and cov["B10-07"].startswith("PRESENT with 1 HELD")
    assert cov["B4-03"] == "PRESENT (every live line valued)"
    x = E.census_crosscheck(k["master"], k["fam"], k["order"], k["after"], k["after"], set(),
                            list(k["per_line"].values()))
    assert [r["family"] for r in x] == ["B4-03"] and x[0]["agrees"]


def test_adverse(k):
    after, bound, order, master = _villa()
    m2 = copy.deepcopy(master)
    m2["families"][1]["item_codes"].append("STR.CONC.SLAB")
    with pytest.raises(E.DryRunError, match="owned by"):
        E.aggregate(after, bound, order, m2)
    m3 = copy.deepcopy(master)
    m3["families"][0]["group"] = "B14 Other"
    with pytest.raises(E.DryRunError, match="not B1 .. B13"):
        E.aggregate(after, bound, order, m3)
    a2 = copy.deepcopy(after)
    a2["L2"]["unit"] = None
    with pytest.raises(E.DryRunError, match="without a unit"):
        E.aggregate(a2, bound, order, master)
    o2 = copy.deepcopy(order)
    o2[0][1][1]["evidence"]["status"] = "PROBABLY FINE"
    with pytest.raises(E.DryRunError, match="s.5"):
        E.aggregate(after, bound, o2, master)
    o2[0][1][1]["evidence"]["status"] = "WORKER-PROPOSED"
    assert E.evidence_of(after["L12"], bound["L12"], o2[0][1][1])[0] == "UNKNOWN"
    b2 = dict(bound, L2=({"binding": "GUESSED"}, E.OV.state(after["L2"])))
    with pytest.raises(E.DryRunError, match="unknown binding"):
        E.aggregate(after, b2, order, master)
    fam = copy.deepcopy(k["fam"])
    fam[("B10", "B10-08", "m3")]["released"] += Decimal("0.000001")
    with pytest.raises(E.DryRunError, match="AGGREGATION BREAK"):
        E.proof(k["after"], k["item"], fam, k["grp"], k["unit"])
    a3 = copy.deepcopy(after)
    a3["L3"]["held_high"] = None
    _, _, _, g3, _, _, _ = E.aggregate(a3, bound, order, master)
    o = E._out(g3[("B10", "m3")], "m3")
    assert o["held_high"] is None and "OPEN" in o["total_state"] and o["total"] is None
    m4 = copy.deepcopy(master)
    m4["candidate_census"]["families"]["B4-03"]["units"]["m2"]["released"] = 21.0
    x = E.census_crosscheck(m4, k["fam"], order, after, after, set(), list(k["per_line"].values()))
    assert not x[0]["agrees"]


@pytest.fixture(scope="module")
def built():
    return E.build()


def test_training_villa_is_the_committed_rebuild(built):
    assert E.OUT_JSON.read_text(encoding="utf-8") == E.dumps(built)
    assert E.OUT_MD.read_text(encoding="utf-8") == E.render_md(built)


def test_training_villa_closes_by_hand(built):
    ln = built["lines"]
    assert (ln["base_v3_0_58"], ln["after_v15"]) == (4999, 5141)
    assert ln["released"] + ln["held"] + ln["excluded"] == 5141
    assert sum(built["evidence_lines"].values()) == ln["released"] + ln["held"]
    assert built["evidence_lines"]["HELD"] == ln["held"]
    assert all(c["re_adds_exactly"] for c in built["aggregation_proof"])
    assert len(built["census_crosscheck_untouched_families"]) == 59
    assert all(x["agrees"] for x in built["census_crosscheck_untouched_families"])
    assert len(built["family_coverage"]) == 103
    t = {(r["trade"], r["unit"]): r["subtotal"] for r in built["trades"]}
    assert t[("B11", "kg")]["held_blank_n"] == 801 and t[("B11", "kg")]["released"] == "9375.30576"
    assert t[("B11", "kg")]["released_t_display"] == "9.375306" and t[("B11", "kg")]["total"] is None
    assert t[("B10", "m2")]["held_blank_n"] == 370
    assert all(s["total"] is None for (g, u), s in t.items() if s["held_n"])
    # released units / mortar of the 0.15 m and 0.20 m black hosts = the V15 manifest's hand figures
    unc = {(r["trade"], r["unit"]): r for r in built["trades"]}
    pcs = [i for f in unc[(E.UNCODED_NO_FAMILY, "pcs")]["families"] for i in f["boq_lines"]
           if i["item_code"] == "MAS.UNITS.BLACK"][0]
    m3 = [i for f in unc[(E.UNCODED_NO_FAMILY, "m3")]["families"] for i in f["boq_lines"]][0]
    assert pcs["released"] == "3269.9375" and m3["released"] == "3.387982"
    assert built["verified_whole_lines"] == 66 and built["released_quantities_changed"] == 0


@pytest.mark.skipif(os.environ.get("URBAN_T630_WRITE") != "1", reason="writer: URBAN_T630_WRITE=1 only")
def test_write_outputs():
    b = E.write_outputs()
    assert E.OUT_JSON.exists() and E.OUT_MD.exists() and b["lines"]["after_v15"] == 5141
