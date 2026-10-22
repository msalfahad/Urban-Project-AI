"""T-142: ARCH_TAKEOFF_V3.0.2, the SAME opt-in candidate as V3.0 / V3.0.1 extended (engine.source.arch_v302), on
synthetic data only (no client drawing). Hand calculations:

FOOTING STEEL (FOOTING_REBAR_POPULATION_V1, cover 70 mm MINIMUM, d^2/162 kg/m: d12 0.888889, d14 1.209877 kg/m):
  FA 2.00 x 2.00, bottom '8 T 12' both ways: bar 2.00 - 0.14 = 1.86 m; 8 x 1.86 x 0.888889 = 13.226667 kg per
     direction -> 2 lines SOURCE_DERIVED, 26.453333 kg; its BOXED cell '3+4' -> 1 line BLOCKED (unquantified)
  FB 2.40 x 2.00, bottom '9 T 14 /m' both ways (per metre: owner Q-71 open):
     SHORT bars 2.00 - 0.14 = 1.86 m spread over 2.40 - 0.14 = 2.26 m at 0.1111 m: A ceil(20.34) = 21, B 22
        21 x 1.86 x 1.209877 = 47.257778 .. 22 x ... = 49.508148 kg
     LONG bars 2.40 - 0.14 = 2.26 m spread over 1.86 m: A ceil(16.74) = 17, B 18
        17 x 2.26 x 1.209877 = 46.483457 .. 18 x ... = 49.217778 kg
     -> 2 lines BOUNDED_EXPOSURE, held 93.741235 .. 98.725926 kg (never one value, never 0)
  FX/FY one footing with two labels (Q-31 C; no single mark) -> 1 line BLOCKED (component ALL)
  route G lines: FA 1 (D12 30.0 kg), FB 2 (D14 60.0 + 40.0), FX 1 (D14 20.0) = 150.0 kg PROVISIONAL ->
  FA 1 REPLACE + 2 ADD, FB 2 REPLACE, FX 1 REPLACE; released 26.453333 kg + held 93.741235 .. 98.725926 kg.
  The same in cm and m schedule units; a missing cover holds every length.

BLINDING D3 (the T-126 villa SV-SCOPE, t 0.075, p 0.15) with the FX/FY labels placed: FX at local (5000, 6500), FY at
  (5000, 6600). FX's window: 1.6 x 1.5 (its larger candidate) = 2.40 m + p 0.15 -> y 3950 .. 9050, x 2450 .. 7550;
  FY's: 1.6 x 0.9 = 1.44 + 0.15 -> y 5010 .. ; beam 2's strip (x 4700 .. 5300 with p, y 0 .. 4000: the strip runs the
  beam's length, as in the T-126 hand table 0.6 x 4.0) enters FX's window over y 3950 .. 4000: 0.05 x 0.60 = 0.03 m2.
  Merged lower bound 3.60 - 0.03 = 3.57 m2 x 0.075 = 0.26775 m3 (V1 0.270);
  own layer 0.324 unchanged; strap unchanged 0.07875; released footing blinding 1.10625 unchanged. No label at all on
  an outline-less footing -> merged lower bound NOT_ESTABLISHED (0).

SOFFITS: two typed places 19.181 + 12.834 = 32.015 m2 (finish HELD Q-68 C, option A shown apart); SX listed apart.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "t126_route_g_scope"))
sys.path.insert(0, str(ROOT / "tests" / "t133_arch_v301"))
sys.path.insert(0, str(ROOT / "tests" / "t131_arch_v30"))

from engine.source import arch_v30 as A30                     # noqa: E402
from engine.source import arch_v301 as A301                   # noqa: E402
from engine.source import arch_v302 as A302                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import footing_rebar_population_v1 as P    # noqa: E402
from engine.source import provisional_estimate as PE          # noqa: E402
from engine.source import route_g_scope_v1 as SC              # noqa: E402
import test_route_g_scope as T126                             # noqa: E402

A = pytest.approx
PID = "synthetic-v302-villa"
KG12, KG14 = 144 / 162, 196 / 162
COVER = {"value_mm": 70.0, "wording": "MINIMUM", "source": "SV general note 7"}
ENDS = {"BOTTOM": {"state": "STRAIGHT", "source": "SV typical footing detail"}, "TOP": None}


def to_line(it):
    return BL.from_route_g(it, project_id=PID, revision_set_sha256="0" * 64, conventions_set="SV",
                           conventions_digest="d" * 16)


# ------------------------------------------------------------------------------------------------ footing steel
def footing_route(scale=1.0):
    """route G items: three footing occurrences and their steel lines (kg from the route's own convention)."""
    items = []
    occ = {"FA": "FTG:FND:FA@1000,1000:aa", "FB": "FTG:FND:FB@6800,1000:bb", "FX": "FTG:FND:T1:X1"}
    for mark, cid in occ.items():
        items.append(PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family="FOOTINGS",
                             storey="FOUNDATION", category="PROVISIONAL", low=1.0, base=1.0, high=1.0,
                             formula="L x W x D", assumptions=["X"], support="CONVENTION_ONLY", confidence="MEDIUM",
                             blocker="SOURCE_CONFLICT" if mark == "FX" else "NOT_REVIEWED", source="SV",
                             dimensions={"drawn_m": None if mark == "FX" else [2.0, 2.0]}))
    for cid, dia, kg in ((occ["FA"], 12, 30.0), (occ["FB"], 14, 60.0), (occ["FB"], 16, 40.0), (occ["FX"], 14, 20.0)):
        items.append(PE.item(item_id=f"P-S:{cid}:D{dia}", component_id=cid, trade="REINFORCEMENT", family="FOOTINGS",
                             storey="FOUNDATION", category="PROVISIONAL", low=kg, base=kg, high=kg, dia_mm=dia,
                             formula="count x (side - 2 cover) x d^2/162", assumptions=["REBAR_COVER_FOOTING_M"],
                             support="CONVENTION_ONLY", confidence="MEDIUM", blocker="NOT_REVIEWED", source="SV"))
    return {"items": items}


def schedule(unit="cm"):
    f = {"mm": 10.0, "cm": 1.0, "m": 0.01}[unit]
    fa = P.schedule_row("FA", (200 * f, 200 * f, 50 * f), unit, {"BOTTOM_SHORT": "8 T 12", "BOTTOM_LONG": "8 T 12"},
                        source="INSERT 1 block SV-FTG")
    fa["boxed_raw"] = "3+4"
    fb = P.schedule_row("FB", (240 * f, 200 * f, 60 * f), unit, {"BOTTOM_SHORT": "9 T 14 /m",
                                                                 "BOTTOM_LONG": "9 T 14 /m"},
                        source="INSERT 2 block SV-FTG")
    fb["boxed_raw"] = None
    return [fa, fb]


def inputs(cover=COVER, soffits=None):
    d = {"schema": A302.INPUTS_SCHEMA, "project": PID,
         "footing_rebar": {"size_unit": {"value": "cm", "source": "SV schedule header"}, "cover": cover,
                           "end_treatment": ENDS}}
    if soffits is not None:
        d["soffits"] = soffits
    return A302.load_inputs(d, PID)


def steel_case(unit="cm", cover=COVER):
    R = footing_route()
    base = [to_line(it) for it in R["items"]]
    ch, log = A302.footing_rebar_changes(R, schedule(unit), base, inputs(cover))
    return R, base, ch, log


@pytest.mark.parametrize("unit", ["cm", "mm", "m"])
def test_footing_steel_by_hand(unit):
    R, base, ch, log = steel_case(unit)
    after = [c["after"] for c in ch if c["after"]["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE"]
    by = {(a["calculation"]["inputs"]["mark"], a["calculation"]["inputs"]["component"]): a for a in after}
    fa = 8 * 1.86 * KG12
    assert by[("FA", "BOTTOM_SHORT")]["measured_net"] == A(fa) == A(13.226667, abs=1e-6)
    assert by[("FA", "BOTTOM_LONG")]["evidence_state"] == "SOURCE_DERIVED"
    assert by[("FA", "BOXED")]["evidence_state"] == "BLOCKED_RFI" and by[("FA", "BOXED")]["measured_net"] is None
    s, lg = by[("FB", "BOTTOM_SHORT")], by[("FB", "BOTTOM_LONG")]
    assert s["evidence_state"] == lg["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (s["bounded_range"]["low"], s["bounded_range"]["high"]) == (A(21 * 1.86 * KG14), A(22 * 1.86 * KG14))
    assert (lg["bounded_range"]["low"], lg["bounded_range"]["high"]) == (A(17 * 2.26 * KG14), A(18 * 2.26 * KG14))
    assert "Q-71" in s["rfi"]["question"]
    assert by[(None, "ALL")]["evidence_state"] == "BLOCKED_RFI"        # two labels: no single mark
    t = log["totals"]
    assert t["released_kg"] == A(26.453333, abs=1e-6)
    assert (t["held_low_kg"], t["held_high_kg"]) == (A(93.741235, abs=1e-6), A(98.725926, abs=1e-6))
    assert t["route_kg"] == A(150.0) and t["held_unquantified_lines"] == 2
    acts = sorted((c["piece"], c["action"]) for c in ch)
    assert acts.count(("FOOTING_REBAR", "REPLACE")) == 4 and acts.count(("FOOTING_REBAR", "ADD")) == 2
    assert all(c["after"]["measured_net"] != 0 for c in ch)
    assert all(c["held"] for c in ch if c["after"]["evidence_state"] in ("BOUNDED_EXPOSURE", "BLOCKED_RFI"))


def test_footing_steel_without_a_printed_cover_holds_every_length():
    R, base, ch, log = steel_case(cover=None)
    assert log["totals"]["released_kg"] == 0.0
    assert all(c["after"]["measured_net"] is None for c in ch)
    assert any("COVER_NOT_PRINTED" in (c["after"].get("rfi") or {}).get("question", "") for c in ch)


def test_footing_steel_without_project_inputs_changes_nothing():
    R = footing_route()
    base = [to_line(it) for it in R["items"]]
    ch, log = A302.footing_rebar_changes(R, schedule(), base, None)
    assert ch == [] and log["state"] == "NO_PROJECT_INPUT"
    assert A302.footing_rebar_changes(None, [], base, inputs())[1]["state"] == "NO_ROUTE_G_RESULT"


def test_inputs_are_checked():
    with pytest.raises(A302.InputsError):
        A302.load_inputs({"schema": "OTHER"})
    with pytest.raises(A302.InputsError):
        A302.load_inputs({"schema": A302.INPUTS_SCHEMA, "footing_rebar": {"size_unit": {"value": "inch",
                                                                                       "source": "x"}}})
    with pytest.raises(A302.InputsError):
        A302.load_inputs({"schema": A302.INPUTS_SCHEMA, "soffits": {"places": [
            {"place": "P", "floor": "GF", "m2": 3.0, "status": "TYPED", "drawing_reference": "x",
             "verification": "y", "evidence_status": "VERIFIED"}]}})
    with pytest.raises(A302.InputsError):
        A302.load_inputs({"schema": A302.INPUTS_SCHEMA, "project": "other"}, PID)


# ------------------------------------------------------------------------------------------------ D3 blinding
def villa_with_labels(frame, fy_label=True):
    fr = T126.FRAMES[frame]
    R, K = T126.villa(fr)
    for f in R["generic"]["D"]["sheets"]["FND"]["footings"]:
        if f["mark"] == "FX":
            f["mark_at"] = fr.at("FND", 5000, 6500)
        if f["mark"] == "FY" and fy_label:
            f["mark_at"] = fr.at("FND", 5000, 6600)
    return R, K


@pytest.mark.parametrize("frame", sorted(T126.FRAMES))
def test_reach_footprint_lower_bounds_by_hand(frame):
    R, K = villa_with_labels(frame)
    v1 = SC.blinding_scope(R)
    rc = SC.blinding_scope(R, footprint="REACH")
    g1 = next(r for r in v1["records"] if r["family"] == "GROUND_BEAM")
    g2 = next(r for r in rc["records"] if r["family"] == "GROUND_BEAM")
    assert g1["exposure_m3"] == [A(0.270), A(0.324)]               # V1 unchanged (default)
    assert g2["exposure_m3"] == [A(0.26775), A(0.324)]
    s2 = next(r for r in rc["records"] if r["family"] == "STRAP")
    assert s2["exposure_m3"] == [A(0.07875), A(0.07875)]
    assert rc["released_m3"] == A(1.10625) == v1["released_m3"]
    assert rc["merged_low_bound"] == "ESTABLISHED" and len(rc["no_outline_windows"]) == 2
    assert "footprint" not in v1                                    # V1's record is byte-for-byte as before


def test_reach_without_a_label_leaves_the_lower_bound_open():
    R, K = villa_with_labels("mm", fy_label=False)
    rc = SC.blinding_scope(R, footprint="REACH")
    g = next(r for r in rc["records"] if r["family"] == "GROUND_BEAM")
    assert rc["merged_low_bound"] == "NOT_ESTABLISHED" and g["exposure_m3"][0] == 0.0
    assert g["exposure_m3"][1] == A(0.324) and g["status"] == "HELD"
    with pytest.raises(SC.ScopeError):
        SC.blinding_scope(R, footprint="ANY")


def test_reach_never_releases_a_merged_value_it_cannot_establish():
    R, K = villa_with_labels("mm")
    rc = SC.blinding_scope(R, footprint="REACH", beam_detail="MERGED_WITH_FOOTING", strap_blinding_printed=True)
    for fam in ("GROUND_BEAM", "STRAP"):
        r = next(x for x in rc["records"] if x["family"] == fam)
        assert r["status"] == "HELD" and r["blocker"] == "FOOTING_OUTLINE_NOT_FOUND"
    v1 = SC.blinding_scope(R, beam_detail="MERGED_WITH_FOOTING")
    assert next(x for x in v1["records"] if x["family"] == "GROUND_BEAM")["m3"] == A(0.270)


def v301_case(frame="mm"):
    R, K = villa_with_labels(frame)
    base = [to_line(it) for it in R["items"]]
    ch301, log301 = A301.scope_changes(R, base, to_line)
    l301 = A302.integrate(base, [], ch301, [])[0]
    return R, base, ch301, log301, l301


def test_scope_fix_replaces_the_held_ground_beam_line_only():
    R, base, ch301, log301, l301 = v301_case()
    ch, log = A302.scope_fix_changes(R, l301, to_line)
    assert len(ch) == 1 and ch[0]["action"] == "REPLACE"
    b, a = ch[0]["before"], ch[0]["after"]
    assert b["location"]["element_id"] == a["location"]["element_id"] == \
        "U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_GROUND_BEAM"
    assert (b["bounded_range"]["low"], a["bounded_range"]["low"]) == (A(0.270), A(0.26775))
    assert a["bounded_range"]["high"] == A(0.324) and a["evidence_state"] == "BOUNDED_EXPOSURE"
    st = {x["family"]: x["change"] for x in log["blinding"]}
    assert st == {"GROUND_BEAM": "CHANGED", "STRAP": "NONE (same range)"}
    _l, l302, ident = A302.integrate(base, [], ch301, ch)
    assert ident["replaced"] == 1 and ident["outside_rows"] == len(l302) - 1


def test_a_line_v3_0_1_replaced_is_never_replaced_again():
    R, base, ch301, log301, l301 = v301_case()
    victim = next(c["after"] for c in ch301 if c["action"] == "REPLACE")
    bad = [A302._change("SCOPE_FIX", "REPLACE", victim, dict(copy.deepcopy(victim), notes="again"))]
    with pytest.raises(ValueError):
        A302.integrate(base, [], ch301, bad)
    first = next(ln for ln in l301 if ln["line_id"] not in {c["after"]["line_id"] for c in ch301})
    two = [A302._change("SCOPE_FIX", "REPLACE", first, dict(copy.deepcopy(first), notes="a")),
           A302._change("SOFFITS", "REPLACE", first, dict(copy.deepcopy(first), notes="b"))]
    with pytest.raises(ValueError):
        A302.integrate(base, [], ch301, two)


# ------------------------------------------------------------------------------------------------ D2 storey summary
def test_columns_by_storey_equals_the_lines_and_lists_what_the_scope_piece_does_not_see():
    R, base, ch301, log301, l301 = v301_case()
    cbs = A302.columns_by_storey(l301, log301["columns_by_storey"])
    lines = sum(A30._qty(ln)["value"] or 0.0 for ln in l301 if ln["item_code"].startswith("STR.CONC.COLUMN"))
    assert sum(v["released_m3"] for v in cbs.values()) == A(lines)
    assert cbs["GF"]["released_m3"] == A(1.500)                    # T-126 hand: GF released 1.500
    # 1F: K1 0.210 from the scope piece + the planted column 0.200 the scope piece does not evaluate
    assert cbs["1F"]["released_m3"] == A(0.410) and cbs["1F"]["outside_scope_piece_released_m3"] == A(0.200)
    assert cbs["1F"]["not_present_lines"] == 1 and cbs["1F"]["held_high_m3"] == A(0.350)


# ------------------------------------------------------------------------------------------------ soffits
SOFF = {"finish_question": "Q-68", "places": [
    {"place": "PL-A", "floor": "GF", "m2": 19.181, "status": "DRAWING-VERIFIED", "evidence_status": "DRAWING-CONFIRMED",
     "drawing_reference": "SV GF plan porch 4.60 x 4.096 + ...", "verification": "SV checker"},
    {"place": "PL-B", "floor": "GF", "m2": 12.834, "status": "DRAWING-VERIFIED", "evidence_status": "VERIFIED",
     "void_excluded_m2": 3.690, "drawing_reference": "SV court", "verification": "SV checker re-measured"}],
    "listed_apart": [{"id": "SX-1", "m2": 0.904, "what": "opening head"}]}


def test_soffits_published_finish_held_option_a_apart():
    base = [to_line(it) for it in footing_route()["items"]]
    ch, log = A302.soffit_changes(inputs(soffits=SOFF), base)
    assert [c["action"] for c in ch] == ["ADD", "ADD"]
    a = {c["after"]["room_id"] if "room_id" in c["after"] else c["after"]["location"]["room_id"]: c for c in ch}
    pa = a["PL-A"]["after"]
    assert pa["measured_net"] == A(19.181) and pa["evidence_state"] == "SOURCE_DERIVED" and pa["unit"] == "m2"
    assert pa["material_state"] == "BY_SPEC" and pa["physical_element"] == A302.SOFFIT_ELEMENT
    fin = pa["calculation"]["inputs"]["finish"]
    assert fin["status"] == "HELD" and fin["provisional_option_a"]["exterior_paint_m2"] == A(19.181)
    assert log["total_m2"] == A(32.015) and log["listed_apart"][0]["added"] is False
    assert a["PL-B"]["evidence_status"] == "VERIFIED" and a["PL-A"]["evidence_status"] == "DRAWING-CONFIRMED"
    assert not any("PLASTER" in c["after"]["item_code"] or "PAINT" in c["after"]["item_code"] for c in ch)
    assert A302.soffit_changes(None, base)[1]["state"] == "NO_PROJECT_INPUT"


# ------------------------------------------------------------------------------------------------ membrane proof
import test_arch_v301 as T133                                 # noqa: E402


def test_membrane_proof_attached_counts_unchanged():
    lines = [T133.roll_line("2F", "R1", value=5), T133.roll_line("1F", "NOPE", value=3)]
    areas = [T133.area("2F", "R1", T133.ROOF_R)]
    ch, log = A302.membrane_proof_changes(areas, lines)
    by = {c["before"]["location"]["room_id"]: c for c in ch}
    pr = by["R1"]["after"]["calculation"]["inputs"]["v3_0_2_membrane_proof"]
    assert pr["state"] == "PROVED" and pr["undeclared_residue"] == [] and pr["layouts_proved"] > 4
    assert pr["verdict_all_layouts"] in ("PROVEN", "PROVEN_EXCEPT_DETAIL")
    assert by["NOPE"]["after"]["calculation"]["inputs"]["v3_0_2_membrane_proof"]["state"] == "NOT_PROVEN"
    assert by["NOPE"]["held"] and not by["R1"]["held"]
    for c in ch:
        assert (c["after"]["measured_net"], c["after"]["bounded_range"], c["after"]["evidence_state"]) == (
            c["before"]["measured_net"], c["before"]["bounded_range"], c["before"]["evidence_state"])
        assert c["action"] == "EVIDENCE_ATTACHED"


def test_undeclared_residue_fails_the_build():
    lines = [T133.roll_line("2F", "R1", value=5)]
    areas = [T133.area("2F", "R1", T133.ROOF_R)]

    def bad(area):
        return {"state": "PROVED", "verdict_all_layouts": "FAILED", "undeclared_residue": ["UNDECLARED_RESIDUE: 0.2"]}
    with pytest.raises(A302.MembraneProofError):
        A302.membrane_proof_changes(areas, lines, prove=bad)


def test_evidence_may_be_attached_on_top_of_the_v3_0_1_audit():
    lines = [T133.roll_line("2F", "R1", value=5)]
    areas = [T133.area("2F", "R1", T133.ROOF_R)]
    ch301, _ = A301.membrane_changes(areas, lines)
    l301 = A302.integrate(lines, [], ch301, [])[0]
    ch, _ = A302.membrane_proof_changes(areas, l301)
    _l, l302, ident = A302.integrate(lines, [], ch301, ch)
    inp = l302[0]["calculation"]["inputs"]
    assert "v3_0_1_membrane_audit" in inp and "v3_0_2_membrane_proof" in inp
    assert ident["evidence_attached"] == 1 and l302[0]["measured_net"] == 5


# ------------------------------------------------------------------------------------------------ ledger, write
def test_write_ledger_diff_and_identity(tmp_path):
    R, base, ch301, log301, l301 = v301_case()
    R2 = footing_route()
    sb = [to_line(it) for it in R2["items"]]
    base2 = base + sb
    l301b = A302.integrate(base2, [], ch301, [])[0]
    ch_r, log_r = A302.footing_rebar_changes(R2, schedule(), l301b, inputs())
    ch_s, log_s = A302.soffit_changes(inputs(soffits=SOFF), l301b)
    ch_x, log_x = A302.scope_fix_changes(R, l301b, to_line)
    names, ident, led = A302.write(tmp_path, base2, [], ch301, ch_r + ch_s + ch_x, [log_r, log_s, log_x],
                                   {"plan": "synthetic"}, released_lines=base2,
                                   scope_summary=log301["columns_by_storey"])
    assert set(names) == {"V3_0_2_BOQ_LINES.json", "V3_0_2_BOQ_LINES.csv", "V3_0_2_INTEGRATION_LEDGER.json",
                          "V3_0_2_INTEGRATION_LEDGER.csv", "V3_0_2_DIFF.csv", "V3_0_2_DOWNSTREAM.json",
                          "V3_0_2_RUN.json"}
    run = json.loads((tmp_path / "V3_0_2_RUN.json").read_text(encoding="utf-8"))
    assert run["released_default"] is False and run["extends"] == "ARCH_TAKEOFF_V3.0.1"
    t = run["totals"]
    assert t["footing_steel_kg"]["released"] == A(26.453333, abs=2e-6)          # two lines of 13.226667
    assert (t["footing_steel_kg"]["held_low"], t["footing_steel_kg"]["held_high"]) == (A(93.741235, abs=1e-6),
                                                                                       A(98.725926, abs=1e-6))
    assert t["soffits_m2"] == A(32.015)
    d = ident["diff"]["vs_v3_0_1"]
    # new line ids: 4 replacing route steel lines + 2 added steel lines + 2 soffits; the ground-beam blinding keeps
    # its id (same element) and is CHANGED; the 4 route steel lines are REPLACED
    assert d["ADDED"] == 4 + 2 + 2 and d["CHANGED"] == 1 and d["REPLACED"] == 4
    assert d["SAME"] == len(l301b) - 5
    assert led["integration_package"] is True
    for r in led["rows"]:
        assert r["evidence_status"] in A302.EVIDENCE_STATUS and r["release_status"] == "NOT RELEASED"
        assert r["verification"]["task"] and r["drawing_reference"]
    csv_text = (tmp_path / "V3_0_2_DIFF.csv").read_text(encoding="utf-8")
    assert csv_text.splitlines()[0].startswith("line_id,item_code")


def test_no_project_constants_in_the_module():
    src = (ROOT / "engine/source/arch_v302.py").read_text(encoding="utf-8")
    for word in ("Alsenan", "ST7757", "P7757", "S-FOOTINGS", "FO-TY\" ==", "19.181", "12.834"):
        assert word not in src


def test_the_earlier_method_lists_are_untouched():
    from tools import urban_boq_m9 as M9
    assert M9.CANDIDATE_METHODS == ("ARCH_TAKEOFF_V3.0",) and M9.CANDIDATE_EXTENSIONS == ("ARCH_TAKEOFF_V3.0.1",)
    assert M9.CANDIDATE_EXTENSIONS_V302 == ("ARCH_TAKEOFF_V3.0.2",) and M9.V302 not in M9.ARCH_METHODS


# ------------------------------------------------------------------------------------------------ D1 runners
@pytest.mark.parametrize("script", ["research/agents_t131/alsenan_v30_run.py", "research/agents_t133/v301_run.py",
                                    "research/agents_t142/v302_run.py"])
def test_runners_refuse_to_run_without_the_route_g_profile(script, tmp_path):
    r = subprocess.run([sys.executable, "-I", str(ROOT / script), "plan.dxf", "st.dxf", "--out", str(tmp_path / "o")],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 2 and "--profile" in r.stderr
    assert not (tmp_path / "o").exists()                           # refused before any work


def test_runner_common_args_forward_the_profile(tmp_path):
    sys.path.insert(0, str(ROOT / "research" / "agents_t131"))
    import argparse
    import alsenan_v30_run as R131
    ns = argparse.Namespace(plan="p.dxf", structural="s.dxf", profile="prof.json")
    args = R131.common_args(ns, tmp_path)
    assert args[args.index("--profile") + 1] == "prof.json"
    with pytest.raises(SystemExit):
        R131.common_args(argparse.Namespace(plan="p", structural="s", profile=None), tmp_path)


# ------------------------------------------------------------------------------------------------ end to end
def test_end_to_end_v3_0_1_files_unchanged_and_v3_0_2_beside_them(tmp_path):
    import test_arch_v30 as T131
    from tools import arch_synth as AS
    AS.villa(tmp_path / "villa.dxf")
    a = T131._run(tmp_path / "villa.dxf", tmp_path / "v301", "ARCH_TAKEOFF_V3.0.1")
    inp = tmp_path / "inp.json"
    inp.write_text(json.dumps({"schema": A302.INPUTS_SCHEMA, "soffits": SOFF}), encoding="utf-8")
    b = T131._run(tmp_path / "villa.dxf", tmp_path / "v302", "ARCH_TAKEOFF_V3.0.2", "--v302-inputs", str(inp))
    for name in ("V3_0_BOQ_LINES.json", "V3_0_1_BOQ_LINES.json", "V3_0_1_INTEGRATION_LEDGER.json", "BOQ_LINES.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    l301 = T131._lines(b / "V3_0_1_BOQ_LINES.json")
    l302 = T131._lines(b / "V3_0_2_BOQ_LINES.json")
    run = json.loads((b / "V3_0_2_RUN.json").read_text(encoding="utf-8"))
    logs = {lg["piece"]: lg for lg in run["piece_logs"]}
    assert logs["FOOTING_REBAR"]["state"] == "NO_ROUTE_G_RESULT" and logs["SCOPE_FIX"]["state"] == "NO_ROUTE_G_RESULT"
    assert len(l302) == len(l301) + 2 and run["totals"]["soffits_m2"] == A(32.015)
    by = {x["line_id"]: x for x in l301}
    proved = 0
    for y in l302:
        x = by.get(y["line_id"])
        if x is None:
            assert y["physical_element"] == A302.SOFFIT_ELEMENT
            continue
        if y["item_code"] in A30.MEMBRANE_ITEMS:
            assert (x["measured_net"], x["bounded_range"]) == (y["measured_net"], y["bounded_range"])
            pr = y["calculation"]["inputs"]["v3_0_2_membrane_proof"]
            proved += pr["state"] == "PROVED"
            assert not pr.get("undeclared_residue")
        else:
            assert A30.line_sha(x) == A30.line_sha(y)
    assert proved >= 1
