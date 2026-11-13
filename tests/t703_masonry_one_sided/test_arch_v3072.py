"""T-703: ARCH_TAKEOFF_V3.0.72 (MASONRY_GATE_B_V4, R-T703-1) on the hand-calculated NON-Alsenan villa M703 (own figures,
no drawing). Rates: black units 12.5 / m2; laying mortar 0.0110625 m3/m2 at 0.15, 0.01475 at 0.20; AAC glue 3.5 / 4.5
kg/m2 at 0.15 / 0.20.
  H1  1F 0.20 black part host, roof build-up not printed: area AT_MOST 7.3333 m2 (b_r >= 0) ->
      units AT_MOST 7.3333 x 12.5 = 91.66625 pcs; mortar 7.3333 x 0.01475 = 0.108166175 -> UP 0.108167 m3
      (half-up would print 0.108166 < exact: refused).
  H2  1F 0.15 white part host: glue AT_MOST 5.25 x 3.5 = 18.375 kg.
  P1  GF 0.15 parent: components upper 0.40 + 1.13 = AT_MOST 1.53 m2; units 19.125 pcs, mortar 1.53 x 0.0110625 =
      0.016925625 -> UP 0.016926 m3, glue 1.53 x 3.5 = 5.355 kg (colour not split: each colour at most the face).
  P2  GF 0.20 parent: a BLACK conflict wall 8.1234 .. 8.1300 + a piece with no drawn end: AT_LEAST 8.1234 m2;
      units AT_LEAST 101.5425 pcs, mortar 8.1234 x 0.01475 = 0.11982015 -> DOWN 0.119820 m3; no glue minimum.
  S   below-ground host, thickness not printed (one leaf >= 0.15, CONDITIONAL): units AT_LEAST 5.0 x 12.5 = 62.5,
      mortar 5.0 x 0.0110625 = 0.0553125 -> DOWN 0.055312 m3.
  Ranges (R-T696-1): bed 0.4 .. 0.63852 m x 0.001389375 = 0.00055575 .. 0.000887143725: print 0.000556 .. 0.000887 ->
      0.000555 .. 0.000888; mortar base 55.8929 .. 56.2329 x 0.0110625 -> high 0.622076 -> 0.622077; perimeter drawn
      0.0103 .. 0.0105 + bands 0.0004 + pieces 0.0003 = 0.0103 .. 0.0112: exact at 6 dp, unchanged.
Every one-sided line stays HELD blank; only the bed / mortar held ranges move (by 1e-6); every other line is
byte-identical."""
from __future__ import annotations

import copy
import decimal
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3059 as A3059  # noqa: E402
from engine.source import arch_v3072 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "M703-SYNTHETIC", "e" * 64
H1, H2 = "1F-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK", "1F-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_WHITE"
P1, P2, S = "GF-WALLS:walls t=0.15", "GF-WALLS:walls t=0.20", "HOUSE_BELOW_NG:BASE_S"
B, UB, UW, MO, GL, PE, BE = ("MAS.BLOCK", "MAS.UNITS.BLACK", "MAS.UNITS.WHITE", "MAS.MORTAR.BLACK", "MAS.GLUE.AAC",
                             "MAS.MORTAR.BLACK.PERIMETER", "MAS.MORTAR.BLACK.LINTEL_BEARING")
UNIT = {B: "m2", UB: "pcs", UW: "pcs", MO: "m3", GL: "kg", PE: "m3", BE: "m3"}


def _ln(code, eid, state="BLOCKED_RFI", net=None, rng=None, rec=None):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=UNIT.get(code, "m2"),
                      evidence_state=state, measured_net=net, gross=net, element_id=eid, floor=eid[:2], room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC", inputs=rec,
                      rfi={"question": "host held", "unlocks": eid} if state != "MEASURED" else None, notes="synthetic",
                      item_en=f"synthetic {code}", item_ar="اصطناعي", trade="MASONRY")
    return BL.validate(ln)


def base():
    out = [
        _ln(B, H1), _ln(UB, f"MATERIAL:{H1}"), _ln(MO, f"MATERIAL:{H1}"),
        _ln(B, H2), _ln(GL, f"MATERIAL:{H2}"), _ln(UW, f"MATERIAL:{H2}"),
        _ln(B, P1), _ln(UB, f"MATERIAL:{P1}"), _ln(MO, f"MATERIAL:{P1}"), _ln(GL, f"MATERIAL:{P1}"),
        _ln(UW, f"MATERIAL:{P1}"), _ln(PE, f"MATERIAL:{P1}#PERIMETER_JOINT"),
        _ln(B, P2), _ln(UB, f"MATERIAL:{P2}"), _ln(MO, f"MATERIAL:{P2}"), _ln(GL, f"MATERIAL:{P2}"),
        _ln(B, S), _ln(UB, f"MATERIAL:{S}"), _ln(MO, f"MATERIAL:{S}"),
        _ln(BE, "MATERIAL:LINTEL_BEARING:D3", "BOUNDED_EXPOSURE", rng=(0.000556, 0.000887)),
        _ln(MO, "MATERIAL:1F-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK", "BOUNDED_EXPOSURE", rng=(0.618315, 0.622076)),
        _ln(PE, "MATERIAL:GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK#PERIMETER_JOINT", "BOUNDED_EXPOSURE",
            rng=(0.0103, 0.0112)),
        _ln(B, "GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK", "MEASURED", net=101.976),
        _ln(B, "1F-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK", "MEASURED", net=58.2529),
        _ln(MO, "MATERIAL:GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK", "PROVISIONAL", net=1.504),
        _ln("STR.CONC.LINTEL", "LINTEL:D3", "MEASURED", net=0.048,
            rec={"lintel_v3053": {"opening_id": "D3", "decision": "REQUIRED"}}),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31),
    ]
    return [_v68(ln, out) for ln in out]


def _v68(ln, lines):
    """the V3.0.68 producer record every perimeter / bed line carries (bound to its black mortar line by id)"""
    eid = ln["location"]["element_id"]
    ids = {(x["item_code"], x["location"]["element_id"]): x["line_id"] for x in lines}
    if ln["item_code"] == PE:
        rec = {"piece": "PERIMETER_JOINT", "mortar_line_id": ids[(MO, eid.split("#PERIMETER_JOINT")[0])],
               "evidence_status": "HELD"}
    elif ln["item_code"] == BE:
        rec = {"piece": "LINTEL_BED", "opening_id": "D3", "lintel_line_id": ids[("STR.CONC.LINTEL", "LINTEL:D3")],
               "mortar_line_id": ids[(MO, "MATERIAL:1F-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK")],
               "evidence_status": "ASSUMED - OWNER-APPROVED"}
    elif ln["item_code"] in (UB, UW, MO, GL):
        ln = copy.deepcopy(ln)
        ln["calculation"]["inputs"] = dict(ln["calculation"]["inputs"], **{
            A3059.REC_KEY: {"source_line_id": ids[(B, eid.split("MATERIAL:", 1)[1])]}})
        return BL.validate(ln)
    else:
        return ln
    ln = copy.deepcopy(ln)
    ln["calculation"]["inputs"] = dict(ln["calculation"]["inputs"], masonry_gate_b_v3068=rec)
    return BL.validate(ln)


LN = base()
ID = {(ln["item_code"], ln["location"]["element_id"]): ln["line_id"] for ln in LN}
SRC = [{"task": "T-A", "file": "research/m703/T-A.json", "sha256": "a" * 64, "merge_commit": "b" * 40,
        "checker_run": "checker T-A Gate A PASS"},
       {"task": "T-B", "file": "research/m703/T-B.json", "sha256": "c" * 64, "merge_commit": "d" * 40,
        "checker_run": "checker T-B Gate A PASS"}]
RATES = {"units_black_per_m2": {"value": "12.5", "source": "Q-75"},
         "mortar_black_m3_per_m2": {"by_t": {"0.15": "0.0110625", "0.20": "0.01475"}, "source": "T-670"},
         "glue_aac_kg_per_m2": {"by_t": {"0.15": "3.5", "0.20": "4.5"}, "source": "owner"}}
CAUSE = {"class": "DESIGNER ITEM", "ref": "roof build-up not printed", "deciding_datum": "b_r"}


def _m(code, host, kind, area, exact, printed, task="T-A", **kw):
    e = {"line_id": ID[(code, f"MATERIAL:{host}")], "source_tasks": [task], "item_code": code, "unit": UNIT[code],
         "kind": kind, "host": host, "host_line_id": ID[(B, host)], "area_m2": area, "exact": exact,
         "printed": printed, "cause": dict(CAUSE), "basis": "hand"}
    e.update(kw)
    return e


def _p(host, kind, comps, exact, printed):
    return {"line_id": ID[(B, host)], "source_tasks": ["T-B"], "item_code": B, "unit": "m2", "kind": kind,
            "host": host, "host_line_id": ID[(B, host)], "components": comps, "exact": exact, "printed": printed,
            "cause": {"class": "DESIGNER ITEM", "ref": "member depth", "deciding_datum": "depth"}, "basis": "hand"}


def _r(code, eid, form, inputs, exact, was, restated):
    return {"line_id": ID[(code, eid)], "source_tasks": ["T-A"], "item_code": code, "unit": UNIT[code], "form": form,
            "inputs": inputs, "exact": exact, "was": was, "restated": restated}


def doc():
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC), "rates": copy.deepcopy(RATES),
            "one_sided": [
                _m(UB, H1, "AT_MOST", "7.3333", "91.66625", 91.66625),
                _m(MO, H1, "AT_MOST", "7.3333", "0.108166175", 0.108167),
                _m(GL, H2, "AT_MOST", "5.25", "18.375", 18.375),
                _p(P1, "AT_MOST", [{"id": "a", "upper": "0.40", "lower": None},
                                   {"id": "b", "upper": "1.13", "lower": None}], "1.53", 1.53),
                _m(UB, P1, "AT_MOST", "1.53", "19.125", 19.125, task="T-B"),
                _m(MO, P1, "AT_MOST", "1.53", "0.016925625", 0.016926, task="T-B"),
                _m(GL, P1, "AT_MOST", "1.53", "5.355", 5.355, task="T-B"),
                _p(P2, "AT_LEAST", [{"id": "w22", "upper": "8.1300", "lower": "8.1234"},
                                    {"id": "annex", "upper": None, "lower": None}], "8.1234", 8.1234),
                _m(UB, P2, "AT_LEAST", "8.1234", "101.5425", 101.5425, task="T-B", min_colour="BLACK"),
                _m(MO, P2, "AT_LEAST", "8.1234", "0.11982015", 0.11982, task="T-B", min_colour="BLACK"),
                _m(UB, S, "AT_LEAST", "5.0", "62.5", 62.5, min_colour="BLACK", t_conditional="0.15",
                   condition="CONDITIONAL: one leaf of at least 0.15 m"),
                _m(MO, S, "AT_LEAST", "5.0", "0.0553125", 0.055312, min_colour="BLACK", t_conditional="0.15",
                   condition="CONDITIONAL: one leaf of at least 0.15 m")],
            "rounding": [
                _r(BE, "MATERIAL:LINTEL_BEARING:D3", "BEARING_X_F", {"bearing_m": ["0.4", "0.63852"],
                                                                       "f_m3_per_m": "0.0013893750"},
                   ["0.00055575000", "0.000887143725000"], [0.000556, 0.000887], [0.000555, 0.000888]),
                _r(MO, "MATERIAL:1F-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK", "BASE_X_RATE",
                   {"base_m2": ["55.8929", "56.2329"], "rate": "0.0110625"}, ["0.61831520625", "0.62207645625"],
                   [0.618315, 0.622076], [0.618315, 0.622077]),
                _r(PE, "MATERIAL:GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK#PERIMETER_JOINT", "DRAWN_PLUS_HELD",
                   {"drawn": ["0.0103", "0.0105"], "bands_high": "0.0004", "pieces_high": "0.0003"},
                   ["0.0103", "0.0112"], [0.0103, 0.0112], [0.0103, 0.0112])]}


def run(d=None, lines=None):
    lines = base() if lines is None else lines
    inp = A.load_inputs(d or doc(), PID)
    ch, log = A.changes_for(inp, lines)
    new, ident = A.integrate(lines, ch)
    return lines, new, ch, log, ident


def _rec(ln):
    return ln["calculation"]["inputs"].get(A.REC_KEY)


def _by(new):
    return {ln["line_id"]: ln for ln in new}


# ------------------------------------------------------------------------------------------------ normal
def test_normal_hand_figures():
    lines, new, ch, log, ident = run()
    by = _by(new)
    want = {(UB, f"MATERIAL:{H1}"): ("AT_MOST", 91.66625), (MO, f"MATERIAL:{H1}"): ("AT_MOST", 0.108167),
            (GL, f"MATERIAL:{H2}"): ("AT_MOST", 18.375), (B, P1): ("AT_MOST", 1.53),
            (UB, f"MATERIAL:{P1}"): ("AT_MOST", 19.125), (MO, f"MATERIAL:{P1}"): ("AT_MOST", 0.016926),
            (GL, f"MATERIAL:{P1}"): ("AT_MOST", 5.355), (B, P2): ("AT_LEAST", 8.1234),
            (UB, f"MATERIAL:{P2}"): ("AT_LEAST", 101.5425), (MO, f"MATERIAL:{P2}"): ("AT_LEAST", 0.11982),
            (UB, f"MATERIAL:{S}"): ("AT_LEAST", 62.5), (MO, f"MATERIAL:{S}"): ("AT_LEAST", 0.055312)}
    for k, (kind, v) in want.items():
        ln = by[ID[k]]
        r = _rec(ln)
        assert r["piece"] == A.P_OS and r["action"] == kind
        assert r["beside"]["kind"] == f"{kind}_{ln['unit'].upper()}" and r["beside"]["value"] == v
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["bounded_range"] is None
        assert A.line_class(ln) == "HELD" and ln["rfi"]["question"]
        assert ("at most" if kind == "AT_MOST" else "at least") in ln["calculation"]["formula"]
    assert by[ID[(MO, f"MATERIAL:{S}")]]["calculation"]["inputs"][A.REC_KEY]["beside"]["condition"].startswith(
        "CONDITIONAL")
    assert ident["masonry"] == {A.P_OS: 12, A.P_BR: 2}
    assert ident["replaced"] == 14 and ident["added"] == 0


def test_normal_rounding_restated_and_exact_kept():
    lines, new, ch, log, ident = run()
    by = _by(new)
    bed = by[ID[(BE, "MATERIAL:LINTEL_BEARING:D3")]]
    assert (bed["bounded_range"]["low"], bed["bounded_range"]["high"]) == (0.000555, 0.000888)
    assert bed["bounded_range"]["basis"] == "synthetic" and bed["evidence_state"] == "BOUNDED_EXPOSURE"
    mo = by[ID[(MO, "MATERIAL:1F-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK")]]
    assert (mo["bounded_range"]["low"], mo["bounded_range"]["high"]) == (0.618315, 0.622077)
    pe_id = ID[(PE, "MATERIAL:GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK#PERIMETER_JOINT")]
    assert A30.line_sha(by[pe_id]) == A30.line_sha(_by(lines)[pe_id])            # exact at 6 dp: untouched
    assert [x["line_id"] for x in log["rounding_exact_already_inside"]] == [pe_id]


def test_normal_outside_byte_identical_and_totals():
    lines, new, ch, log, ident = run()
    named = {c["after"]["line_id"] for c in ch}
    for a, b in zip(lines, new):
        if a["line_id"] not in named:
            assert A30.line_sha(a) == A30.line_sha(b)
    t0, t1 = A304.code_totals(lines), A304.code_totals(new)
    moved = A.check_totals(t0, t1, ch)
    assert sorted(moved) == [f"{BE}|m3", f"{MO}|m3"]
    assert abs(t1[f"{BE}|m3"]["held_low"] - t0[f"{BE}|m3"]["held_low"] + 0.000001) < 1e-9
    assert abs(t1[f"{MO}|m3"]["held_high"] - t0[f"{MO}|m3"]["held_high"] - 0.000001) < 1e-9
    for k in (f"{B}|m2", f"{UB}|pcs", f"{GL}|kg"):                               # a figure beside is never summed
        assert t0[k] == t1[k]


def test_census_before_after():
    lines, new, ch, log, ident = run()
    b, a = ident["b9_census_before"], ident["b9_census_after"]
    assert b[f"{UB}|pcs"] == {"released": 0, "bounded": 0, "at_most": 0, "at_least": 0, "blank": 4, "excluded": 0}
    assert a[f"{UB}|pcs"] == {"released": 0, "bounded": 0, "at_most": 2, "at_least": 2, "blank": 0, "excluded": 0}
    assert a[f"{B}|m2"] == {"released": 2, "bounded": 0, "at_most": 1, "at_least": 1, "blank": 3, "excluded": 0}
    assert a[f"{UW}|pcs"]["blank"] == 2 and a[f"{PE}|m3"] == b[f"{PE}|m3"]


def test_mirror_order_same_lines():
    d = doc()
    d["one_sided"] = list(reversed(d["one_sided"]))
    d["rounding"] = list(reversed(d["rounding"]))
    _, n1, *_ = run()
    _, n2, *_ = run(d)
    assert [A30.line_sha(x) for x in n1] == [A30.line_sha(x) for x in n2]


def test_global_decimal_context_untouched():
    p = decimal.getcontext().prec
    run()
    assert decimal.getcontext().prec == p


def test_write_files(tmp_path):
    lines = base()
    inp = A.load_inputs(doc(), PID)
    ch, log = A.changes_for(inp, lines)
    names, ident, led = A.write(tmp_path, lines, ch, log)
    assert "V3_0_72_BOQ_LINES.json" in names and led["integration_package"] is True
    assert ident["diff"]["vs_base"] == {"CHANGED": 14, "SAME": len(lines) - 14}


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, msg, lines=None):
    d = doc()
    mut(d)
    with pytest.raises((A.InputsError, ValueError), match=msg):
        run(d, lines)


def _os(d, code, host):
    return next(e for e in d["one_sided"] if e["line_id"] == ID[(code, host if code == B else f"MATERIAL:{host}")])


def test_adverse_half_up_print_refused():
    _bad(lambda d: _os(d, MO, H1).update(printed=0.108166), "not the recomputed")


def test_adverse_at_least_rounded_up_refused():
    _bad(lambda d: _os(d, MO, P2).update(printed=0.119821), "not the recomputed")


def test_adverse_exact_not_area_times_rate():
    _bad(lambda d: _os(d, UB, H1).update(exact="91.67"), "ledger exact")


def test_adverse_area_in_mm_or_zero():
    _bad(lambda d: _os(d, UB, H1).update(area_m2="7333.3", exact="91666.25", printed=91666.25), "unit slip")
    _bad(lambda d: _os(d, UB, H1).update(area_m2="0", exact="0", printed=0), "unit slip, or 0")


def test_adverse_missing_area_never_zero():
    _bad(lambda d: _os(d, UB, H1).update(area_m2=None), "never 0")


def test_adverse_parent_open_component_no_at_most():
    _bad(lambda d: _os(d, B, P1)["components"].append({"id": "c", "upper": None, "lower": None}), "no upper end")


def test_adverse_parent_at_least_without_minimum():
    def m(d):
        for c in _os(d, B, P2)["components"]:
            c["lower"] = None
    _bad(m, "no positive drawn minimum")


def test_adverse_glue_at_least_from_black_minimum():
    def m(d):
        d["one_sided"].append(_m(GL, P2, "AT_LEAST", "8.1234", "36.5553", 36.5553, task="T-B", min_colour="BLACK"))
    _bad(m, "needs a WHITE drawn minimum")


def test_adverse_white_units_and_perimeter_get_no_figure():
    def m(d):
        d["one_sided"].append(dict(_m(GL, H2, "AT_MOST", "5.25", "18.375", 18.375),
                                   line_id=ID[(UW, f"MATERIAL:{H2}")], item_code=UW, unit="pcs"))
    _bad(m, "gets no one-ended figure")

    def p(d):
        d["one_sided"].append(dict(_m(MO, P1, "AT_MOST", "1.53", "0.016925625", 0.016926),
                                   line_id=ID[(PE, f"MATERIAL:{P1}#PERIMETER_JOINT")], item_code=PE))
    _bad(p, "gets no one-ended figure")


def test_adverse_kind_range_or_point():
    _bad(lambda d: _os(d, UB, H1).update(kind="RANGE"), "never a range or a point")


def test_adverse_material_firmer_than_parent():
    _bad(lambda d: _os(d, UB, P1).update(kind="AT_LEAST", min_colour="BLACK", printed=19.125), "on a host stated")
    _bad(lambda d: _os(d, UB, P1).update(area_m2="1.60", exact="20.0", printed=20.0), "is not its host's figure")


def test_adverse_no_printed_thickness_needs_condition():
    def m(d):
        e = _os(d, UB, S)
        e.pop("condition")
    _bad(m, "needs the stated condition")


def test_adverse_printed_thickness_with_conditional():
    _bad(lambda d: _os(d, UB, H1).update(t_conditional="0.15", condition="x"), "no conditional thickness")


def test_adverse_missing_rate():
    _bad(lambda d: d["rates"]["mortar_black_m3_per_m2"]["by_t"].pop("0.20"), "a missing input is never 0")


def test_adverse_line_named_twice():
    _bad(lambda d: d["one_sided"].append(copy.deepcopy(d["one_sided"][0])), "named twice")


def test_adverse_line_not_blank():
    lines = base()
    i = next(i for i, ln in enumerate(lines) if ln["line_id"] == ID[(UB, f"MATERIAL:{H1}")])
    lines[i] = _ln(UB, f"MATERIAL:{H1}", "BOUNDED_EXPOSURE", rng=(90.0, 91.0))
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(), lines)


def test_adverse_line_already_carries_a_figure():
    lines = base()
    i = next(i for i, ln in enumerate(lines) if ln["line_id"] == ID[(UB, f"MATERIAL:{H1}")])
    lines[i] = _ln(UB, f"MATERIAL:{H1}", rec={"older_v": {"beside": {"kind": "AT_MOST_PCS", "value": 91.0}}})
    with pytest.raises(A.InputsError, match="already carries a figure"):
        run(doc(), lines)


def test_adverse_host_not_held_block():
    _bad(lambda d: _os(d, UB, H1).update(host_line_id=ID[(B, "GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK")]),
         "is not the HELD MAS.BLOCK line|is not a HELD blank")


def test_adverse_rounding_stale_print_and_wrong_restated():
    _bad(lambda d: d["rounding"][0].update(was=[0.000556, 0.000886]), "stale binding")
    _bad(lambda d: d["rounding"][0].update(restated=[0.000556, 0.000888]), "R-T696-1")
    _bad(lambda d: d["rounding"][0].update(exact=["0.000556", "0.000887"]), "ledger exact")


def test_adverse_rounding_inverted_or_bad_form():
    _bad(lambda d: d["rounding"][0]["inputs"].update(bearing_m=["0.7", "0.4"]), "inverted")
    _bad(lambda d: d["rounding"][0].update(form="ROUNDED_SUM"), "form")


def test_adverse_applied_twice():
    lines, new, *_ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), new)


def test_adverse_another_project():
    d = doc()
    d["project_id"] = "OTHER"
    with pytest.raises(A.InputsError, match="the run is"):
        A.load_inputs(d, PID)


def test_adverse_moved_total_outside_ranges():
    lines, new, ch, *_ = run()
    t0, t1 = A304.code_totals(lines), A304.code_totals(new)
    t1 = dict(t1)
    t1[f"{UB}|pcs"] = dict(t1[f"{UB}|pcs"], released=1.0)
    with pytest.raises(ValueError, match="never summed"):
        A.check_totals(t0, t1, ch)


def test_adverse_unknown_source():
    _bad(lambda d: _os(d, UB, H1).update(source_tasks=["T-Z"]), "no merged source")
