"""T-167: ARCH_TAKEOFF_V3.0.4, the SAME opt-in candidate as V3.0 .. V3.0.3 with the no-assumptions audit of the route G
profile against the owner Q-17 A project data file (engine.source.arch_v304), on synthetic data only (no client
drawing). Hand calculations (kg = count x length x d^2/162; T16 = 256/162 = 1.580247 kg/m):

VILLA M (not the development villa). Project data file: STOREY_HEIGHT_GF 3.60 m DRAWING-VERIFIED (usable),
NECK_TOP_LEVEL_M 0.90 m DRAWING-VERIFIED (usable), FOUNDING_DEPTH_M 1.40 m HELD (the note prints an excavation
minimum), CB_SUPPORT_BAR_EXTENT_FRAC 0.22 HELD (a second extent is printed). The run's profile carries all four.
  K1 column GF 0.30 x 0.40 x 3.60                              = 0.432 m3     usable value only: UNCHANGED
  N1 neck 0.30 x 0.30, top +0.90, footing 0.50 deep, F 1.40:  h = 0.90 + 1.40 - 0.50 = 1.80 -> 0.162 m3 released;
     restricted run (no F): generic F 1.20 .. 2.00 -> h 1.60 .. 2.40   -> 0.144 .. 0.216 m3: HELD over that range
  N2 neck 0.25 x 0.30 = 0.075 m2, footing 0.60 deep, held 1.40 .. 1.90 (high not printed): h 1.70 .. 2.20
     -> 0.1275 .. 0.165 m3; restricted F 1.20 .. 2.00 -> h 1.50 .. 2.30 -> 0.1125 .. 0.1725 m3: the restricted range
  N1 neck steel 4 T16 x 1.80 = 7.20 m                          = 11.377778 kg released; the restricted run has no such
     line -> BLOCKED (UNKNOWN), 11.377778 kept as information, never a quantity
  B1 support bars 2 ends x 4 T16 x 0.22 x 5.00 = 8 x 1.10 m    = 13.906173 kg released; restricted run BLOCKED ->
     BLOCKED, 13.906173 kept as information
  a beam steel line SUPERSEDED in V3.0.3 (NOT_APPLICABLE) and absent from the restricted run: never re-held
  a line only in the restricted run: listed RESTRICTED_ONLY, never added
Totals: STR.CONC.NECK released 0.162 -> 0 released lines, held 0.144 + 0.1125 = 0.2565 .. 0.216 + 0.1725 = 0.3885 m3;
STR.REBAR released 25.283951 -> 0 kg released (2 blocked lines); the column stays 0.432 m3.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "t131_arch_v30"))

from engine.source import arch_v30 as A30                     # noqa: E402
from engine.source import arch_v304 as A304                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402

A = pytest.approx
PID = "synthetic-v304-villa-m"
T16 = 256 / 162
KEYS = ("STOREY_HEIGHT_GF", "NECK_TOP_LEVEL_M", "FOUNDING_DEPTH_M", "CB_SUPPORT_BAR_EXTENT_FRAC")
NOT_USABLE = ["CB_SUPPORT_BAR_EXTENT_FRAC", "FOUNDING_DEPTH_M"]


# ------------------------------------------------------------------------------------------------ fixture
def rec(key, value, unit, status, **kw):
    r = {"key": key, "project": PID, "kind": "number", "unit": unit, "value": value, "status": status,
         "drawing_file": "villa-m-structural.dxf", "drawing_number": "VM-S", "revision": "no revision printed",
         "sheet": "S-01", "reference": f"printed note for {key}", "applies_to": {"members": ["ALL"]},
         "reviewer_or_source": "synthetic fixture", "entered_by": "TYPED"}
    if status == "HELD":
        r["hold_reason"] = f"{key}: not printed as used"
    r.update(kw)
    return r


def data_file(**over):
    rs = {"STOREY_HEIGHT_GF": rec("STOREY_HEIGHT_GF", 3.60, "m", "DRAWING-VERIFIED"),
          "NECK_TOP_LEVEL_M": rec("NECK_TOP_LEVEL_M", 0.90, "m", "DRAWING-VERIFIED"),
          "FOUNDING_DEPTH_M": rec("FOUNDING_DEPTH_M", 1.40, "m", "HELD"),
          "CB_SUPPORT_BAR_EXTENT_FRAC": rec("CB_SUPPORT_BAR_EXTENT_FRAC", 0.22, "fraction", "HELD")}
    for k, v in over.items():
        if v is None:
            rs.pop(k)
        else:
            rs[k] = v
    return {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": PID, "records": list(rs.values())}


def profile(**over):
    c = [{"id": "STOREY_HEIGHT_GF", "kind": "number", "unit": "m", "base": 3.60, "low": 3.60, "high": 3.60},
         {"id": "NECK_TOP_LEVEL_M", "kind": "number", "unit": "m", "base": 0.90, "low": 0.90, "high": 0.90},
         {"id": "FOUNDING_DEPTH_M", "kind": "number", "unit": "m", "base": 1.40, "low": 1.40, "high": 1.90},
         {"id": "CB_SUPPORT_BAR_EXTENT_FRAC", "kind": "number", "base": 0.22, "low": 0.22, "high": 0.22}]
    for x in c:
        x.update(over.get(x["id"]) or {})
    return {"profile": "VILLA_M", "conventions": c}


def ln(code, eid, floor, ev, net=None, rng=None, unit="m3", pe=None, notes=""):
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, bounded_range=None if rng is None else
                        {"low": rng[0], "high": rng[1], "basis": "route G range"},
                        element_id=eid, floor=floor, physical_element=pe, formula="route G (synthetic)",
                        inputs={"assumptions": ["synthetic"]}, geometry_source="CAD_VECTOR",
                        rule_id="ROUTE_G", rule_version="v1", material_state="SOURCE",
                        rfi={"question": "held (synthetic)", "unlocks": eid} if ev == "BLOCKED_RFI" else None,
                        notes=notes or ("superseded by a hand ledger" if ev == "NOT_APPLICABLE_WITH_EVIDENCE" else ""))


def v303_lines():
    return [ln("STR.CONC.COLUMN", "COL:GF:K1", "GF", "PROVISIONAL", 0.30 * 0.40 * 3.60),
            ln("STR.CONC.NECK", "NECK:N1", "FOUNDATION", "PROVISIONAL", 0.30 * 0.30 * 1.80),
            ln("STR.CONC.NECK", "NECK:N2", "FOUNDATION", "BOUNDED_EXPOSURE", rng=(0.075 * 1.70, 0.075 * 2.20)),
            ln("STR.REBAR", "P-S:NECK:N1:MAIN:D16", "FOUNDATION", "PROVISIONAL", 4 * 1.80 * T16, unit="kg",
               pe="COLUMNS"),
            ln("STR.REBAR", "P-S:BEAMS:GF:B1:SUPPORT:D16", "GF", "PROVISIONAL", 2 * 4 * 0.22 * 5.0 * T16, unit="kg",
               pe="BEAMS"),
            ln("STR.REBAR", "P-S:BEAMS:GF:B1:BOT:D16", "GF", "NOT_APPLICABLE_WITH_EVIDENCE", unit="kg", pe="BEAMS")]


def restricted_lines(base=None):
    """the same candidate without FOUNDING_DEPTH_M and CB_SUPPORT_BAR_EXTENT_FRAC (hand values in the docstring)."""
    b = {x["location"]["element_id"]: x for x in copy.deepcopy(base or v303_lines())}
    out = [b["COL:GF:K1"]]
    n1 = b["NECK:N1"]
    n1.update(evidence_state="BOUNDED_EXPOSURE", measured_net=None,
              bounded_range={"low": 0.09 * 1.60, "high": 0.09 * 2.40, "basis": "generic founding range"})
    n2 = b["NECK:N2"]
    n2["bounded_range"] = {"low": 0.075 * 1.50, "high": 0.075 * 2.30, "basis": "generic founding range"}
    sb = b["P-S:BEAMS:GF:B1:SUPPORT:D16"]
    sb.update(evidence_state="BLOCKED_RFI", measured_net=None, rfi={"question": "support bar extent", "unlocks": "B1"})
    extra = ln("STR.CONC.NECK", "NECK:N3-PLACEHOLDER", "FOUNDATION", "BLOCKED_RFI")
    return out + [n1, n2, sb, extra]                  # no N1 steel line, no superseded B1 bottom line


def single_fnd_lines():
    """the candidate without FOUNDING_DEPTH_M only: the necks and their steel move, the beam bar does not."""
    r = {x["location"]["element_id"]: x for x in restricted_lines()}
    b = {x["location"]["element_id"]: x for x in v303_lines()}
    return [b["COL:GF:K1"], r["NECK:N1"], r["NECK:N2"], b["P-S:BEAMS:GF:B1:SUPPORT:D16"]]


def run(rid, keys, lines):
    return {"id": rid, "removed_keys": list(keys), "profile_sha256": "p" * 64, "lines_sha256": A304.lines_sha256(lines),
            "lines": lines}


def inputs(df=None, runs=None):
    return {"schema": A304.INPUTS_SCHEMA, "project": PID,
            "data_file": {"file": "villa_m_data.json", "sha256": "d" * 64, "doc": df or data_file()},
            "audit_classes": {"FOUNDING_DEPTH_M": "PRINTED_MINIMUM", "CB_SUPPORT_BAR_EXTENT_FRAC": "DIFFERENT"},
            "runs": runs if runs is not None else [run("RESTRICTED", NOT_USABLE, restricted_lines())]}


def by_eid(changes):
    return {c["before"]["location"]["element_id"]: c for c in changes}


# ------------------------------------------------------------------------------------------------ the audit
def test_hand_values_held_never_zero_and_usable_value_lines_unchanged():
    base = v303_lines()
    ch, log = A304.audit_changes(A304.load_inputs(inputs(), PID), base, profile())
    c = by_eid(ch)
    assert set(c) == {"NECK:N1", "NECK:N2", "P-S:NECK:N1:MAIN:D16", "P-S:BEAMS:GF:B1:SUPPORT:D16"}
    n1 = c["NECK:N1"]["after"]
    assert n1["evidence_state"] == "BOUNDED_EXPOSURE" and n1["measured_net"] is None
    assert (n1["bounded_range"]["low"], n1["bounded_range"]["high"]) == (A(0.144), A(0.216))
    pa = n1["calculation"]["inputs"]["profile_audit"]
    assert pa["candidate_v3_0_3"]["value"] == A(0.162) and pa["removed_keys"] == NOT_USABLE
    n2 = c["NECK:N2"]["after"]
    assert (n2["bounded_range"]["low"], n2["bounded_range"]["high"]) == (A(0.1125), A(0.1725))
    assert n2["calculation"]["inputs"]["profile_audit"]["candidate_v3_0_3"]["high"] == A(0.165)
    st = c["P-S:NECK:N1:MAIN:D16"]
    assert st["after"]["evidence_state"] == "BLOCKED_RFI" and st["after"]["measured_net"] is None
    assert st["evidence_status"] == "UNKNOWN"
    assert st["after"]["calculation"]["inputs"]["profile_audit"]["candidate_v3_0_3"]["value"] == A(11.377778, abs=1e-6)
    sb = c["P-S:BEAMS:GF:B1:SUPPORT:D16"]
    assert sb["after"]["evidence_state"] == "BLOCKED_RFI" and sb["evidence_status"] == "HELD"
    assert sb["after"]["calculation"]["inputs"]["profile_audit"]["candidate_v3_0_3"]["value"] == \
        A(13.906173, abs=1e-6)
    for x in ch:
        a = x["after"]
        assert a["measured_net"] is None and a["gross"] is None                     # missing never becomes 0
        assert "PROFILE_VALUE_NOT_USABLE" in a["rfi"]["question"] and a["line_id"] == x["before"]["line_id"]
        BL.validate(a)
    assert [x["line_id"] for x in log["restricted_only"]] and log["restricted_only"][0]["item_code"] == "STR.CONC.NECK"
    assert [x["state"] for x in log["no_quantity_in_v3_0_3"]] == ["NOT_APPLICABLE_WITH_EVIDENCE"]
    assert log["usable_keys"] == ["NECK_TOP_LEVEL_M", "STOREY_HEIGHT_GF"]


def test_totals_by_code_hand_values():
    base = v303_lines()
    ch, log = A304.audit_changes(A304.load_inputs(inputs(), PID), base, profile())
    l304, ident = A304.integrate(base, ch)
    t3, t4 = A304.code_totals(base), A304.code_totals(l304)
    assert t3["STR.CONC.NECK|m3"]["released"] == A(0.162)
    assert t4["STR.CONC.NECK|m3"]["released"] == 0 and t4["STR.CONC.NECK|m3"]["bounded_lines"] == 2
    assert (t4["STR.CONC.NECK|m3"]["held_low"], t4["STR.CONC.NECK|m3"]["held_high"]) == (A(0.2565), A(0.3885))
    assert t3["STR.REBAR|kg"]["released"] == A(25.283951, abs=1e-6)
    assert t4["STR.REBAR|kg"]["released"] == 0 and t4["STR.REBAR|kg"]["blocked_lines"] == 2
    assert t4["STR.CONC.COLUMN|m3"] == t3["STR.CONC.COLUMN|m3"] and t4["STR.CONC.COLUMN|m3"]["released"] == A(0.432)
    assert ident["replaced"] == 4 and ident["outside_rows"] == 2 and ident["added"] == 0


def test_cause_by_single_value_runs_and_no_single_value():
    rs = [run("RESTRICTED", NOT_USABLE, restricted_lines()), run("MINUS_FND", ["FOUNDING_DEPTH_M"], single_fnd_lines())]
    ch, log = A304.audit_changes(A304.load_inputs(inputs(runs=rs), PID), v303_lines(), profile())
    c = by_eid(ch)
    assert c["NECK:N1"]["cause"] == ["FOUNDING_DEPTH_M"] and c["NECK:N2"]["cause"] == ["FOUNDING_DEPTH_M"]
    # the single run has no N1 steel line: absent != released, so it moves too
    assert c["P-S:NECK:N1:MAIN:D16"]["cause"] == ["FOUNDING_DEPTH_M"]
    # the beam bar does not move without FOUNDING_DEPTH_M alone and no other single run is given
    assert c["P-S:BEAMS:GF:B1:SUPPORT:D16"]["cause"] == [A304.NO_SINGLE_VALUE]
    assert "NO_SINGLE_VALUE" in c["P-S:BEAMS:GF:B1:SUPPORT:D16"]["after"]["rfi"]["question"]
    assert set(log["by_cause"]) == {"FOUNDING_DEPTH_M", "NO_SINGLE_VALUE"}


def test_a_category_change_keeps_the_element_and_is_paired_one_to_one():
    """route G re-files a neck from 'P-C:' (provisional) to 'U-C:' (unresolved) without the founding value: the line id
    changes, the element does not. N4 0.20 x 0.30 released 0.06 x 1.80 = 0.108 m3; restricted U-C N4 held 0.06 x 1.60
    .. 0.06 x 2.40 = 0.096 .. 0.144 m3 -> paired, HELD 0.096 .. 0.144 (not UNKNOWN). Adverse: two U-C candidates for
    one element are never guessed between: the line stays unpaired (BLOCKED, UNKNOWN)."""
    base = v303_lines() + [ln("STR.CONC.NECK", "P-C:NECK:N4", "FOUNDATION", "PROVISIONAL", 0.06 * 1.80)]
    u = ln("STR.CONC.NECK", "U-C:NECK:N4", "FOUNDATION", "BOUNDED_EXPOSURE", rng=(0.06 * 1.60, 0.06 * 2.40))
    r = restricted_lines() + [u]
    ch, log = A304.audit_changes(A304.load_inputs(inputs(runs=[run("RESTRICTED", NOT_USABLE, r)]), PID), base,
                                 profile())
    n4 = by_eid(ch)["P-C:NECK:N4"]
    assert n4["after"]["evidence_state"] == "BOUNDED_EXPOSURE" and n4["evidence_status"] == "HELD"
    assert (n4["after"]["bounded_range"]["low"], n4["after"]["bounded_range"]["high"]) == (A(0.096), A(0.144))
    assert n4["after"]["calculation"]["inputs"]["profile_audit"]["restricted_line_id"] == u["line_id"]
    assert n4["after"]["line_id"] == base[-1]["line_id"]                     # the candidate keeps its own line id
    assert log["paired_by_element"] == 1 and u["line_id"] not in [x["line_id"] for x in log["restricted_only"]]
    u2 = ln("STR.CONC.NECK", "X-C:NECK:N4", "FOUNDATION", "BOUNDED_EXPOSURE", rng=(0.0, 1.0))
    ch2, log2 = A304.audit_changes(A304.load_inputs(inputs(runs=[run("RESTRICTED", NOT_USABLE, r + [u2])]), PID),
                                   base, profile())
    n4b = by_eid(ch2)["P-C:NECK:N4"]
    assert n4b["after"]["evidence_state"] == "BLOCKED_RFI" and n4b["evidence_status"] == "UNKNOWN"
    assert log2["paired_by_element"] == 0


def test_a_profile_without_non_usable_values_changes_nothing():
    """the adverse direction: a restricted run identical to the candidate (no line rests on the removed values) holds
    nothing; every line stays byte-identical."""
    base = v303_lines()
    ch, log = A304.audit_changes(A304.load_inputs(inputs(runs=[run("RESTRICTED", NOT_USABLE, base)]), PID), base,
                                 profile())
    assert ch == [] and log["lines_held"] == 0
    l304, ident = A304.integrate(base, ch)
    assert [A30.line_sha(x) for x in l304] == [A30.line_sha(x) for x in base]


def test_units_a_data_file_in_cm_matches_a_profile_in_m():
    df = data_file(STOREY_HEIGHT_GF=rec("STOREY_HEIGHT_GF", 360, "cm", "DRAWING-VERIFIED"))
    chk = A304.check_profile(A304.load_inputs(inputs(df=df), PID), profile())
    assert "STOREY_HEIGHT_GF" in chk["usable"]


@pytest.mark.parametrize("df,prof,msg", [
    (lambda: data_file(STOREY_HEIGHT_GF=None), lambda: profile(), "no project data file record"),
    (lambda: data_file(), lambda: profile(STOREY_HEIGHT_GF={"base": 3.70, "low": 3.70, "high": 3.70}),
     "neither the project data file value"),
    (lambda: data_file(), lambda: profile(NECK_TOP_LEVEL_M={"high": 1.00}), "profile high"),
    (lambda: data_file(STOREY_HEIGHT_GF=rec("STOREY_HEIGHT_GF", 360, "mm", "DRAWING-VERIFIED")), lambda: profile(),
     "neither the project data file value"),
    (lambda: data_file(), lambda: {"conventions": []}, "--profile"),
])
def test_profile_against_data_file_refusals(df, prof, msg):
    with pytest.raises(A304.InputsError, match=msg):
        A304.audit_changes(A304.load_inputs(inputs(df=df()), PID), v303_lines(), prof())


def test_a_usable_printed_alternative_may_bound_the_profile_range():
    alt = [{"value": 1.00, "unit": "m", "status": "DRAWING-VERIFIED", "note": "printed at another position"}]
    df = data_file(NECK_TOP_LEVEL_M=rec("NECK_TOP_LEVEL_M", 0.90, "m", "DRAWING-VERIFIED", alternatives=alt))
    A304.check_profile(A304.load_inputs(inputs(df=df), PID), profile(NECK_TOP_LEVEL_M={"high": 1.00}))
    alt[0]["status"] = "NOT_PRINTED"
    df = data_file(NECK_TOP_LEVEL_M=rec("NECK_TOP_LEVEL_M", 0.90, "m", "DRAWING-VERIFIED", alternatives=alt))
    with pytest.raises(A304.InputsError, match="profile high"):
        A304.check_profile(A304.load_inputs(inputs(df=df), PID), profile(NECK_TOP_LEVEL_M={"high": 1.00}))


@pytest.mark.parametrize("mutate,msg", [
    (lambda d: d.update(schema="X"), "schema"),
    (lambda d: d["data_file"].pop("sha256"), "data_file.sha256"),
    (lambda d: d["data_file"]["doc"]["records"][0].pop("reviewer_or_source"), "data_file"),
    (lambda d: d["runs"][0].update(id="OTHER"), "RESTRICTED"),
    (lambda d: d["runs"].append(dict(d["runs"][0])), "unique id"),
    (lambda d: d["runs"][0].update(removed_keys=[]), "removed_keys"),
    (lambda d: d["runs"][0].pop("lines_sha256"), "lines_sha256"),
    (lambda d: d.update(project="another-villa"), "another-villa"),
])
def test_inputs_are_checked(mutate, msg):
    d = inputs()
    mutate(d)
    with pytest.raises(A304.InputsError, match=msg):
        A304.load_inputs(d, PID)


@pytest.mark.parametrize("keys,msg", [
    (["FOUNDING_DEPTH_M"], "must be the same set"),                     # one non-usable value left in
    (NOT_USABLE + ["STOREY_HEIGHT_GF"], "must be the same set"),         # a usable value removed too
])
def test_the_restricted_run_removes_exactly_the_non_usable_values(keys, msg):
    with pytest.raises(A304.InputsError, match=msg):
        A304.audit_changes(A304.load_inputs(inputs(runs=[run("RESTRICTED", keys, restricted_lines())]), PID),
                           v303_lines(), profile())


def test_tampered_run_lines_and_unknown_removed_keys_are_refused():
    r = run("RESTRICTED", NOT_USABLE, restricted_lines())
    r["lines"][0]["measured_net"] = 9.0
    with pytest.raises(A304.InputsError, match="lines_sha256"):
        A304.audit_changes(A304.load_inputs(inputs(runs=[r]), PID), v303_lines(), profile())
    rs = [run("RESTRICTED", NOT_USABLE, restricted_lines()), run("X", ["NOT_A_PROFILE_KEY"], v303_lines())]
    with pytest.raises(A304.InputsError, match="does not have"):
        A304.audit_changes(A304.load_inputs(inputs(runs=rs), PID), v303_lines(), profile())


def test_a_restricted_run_of_another_candidate_is_refused_not_compared():
    """adverse (found on the development villa): a profile renamed for the restricted run changes every route G
    line id; comparing by id would hold every line of the candidate. Fewer than half of the ids shared -> refused."""
    other = []
    for x in restricted_lines():
        y = copy.deepcopy(x)
        y["line_id"] = "L-other-" + x["line_id"][-8:]
        other.append(y)
    with pytest.raises(A304.InputsError, match="not the same candidate"):
        A304.audit_changes(A304.load_inputs(inputs(runs=[run("RESTRICTED", NOT_USABLE, other)]), PID), v303_lines(),
                           profile())


def test_an_approved_line_is_never_re_held_silently():
    base = v303_lines()
    base[1]["approval_state"] = "APPROVED"
    with pytest.raises(ValueError, match="approved line"):
        A304.audit_changes(A304.load_inputs(inputs(runs=[run("RESTRICTED", NOT_USABLE, restricted_lines(base))]),
                                            PID), base, profile())


def test_no_inputs_changes_nothing():
    ch, log = A304.audit_changes(None, v303_lines(), profile())
    assert ch == [] and log["state"] == "NO_PROJECT_INPUT"


# ------------------------------------------------------------------------------------------------ integrate, write
def test_integrate_refusals():
    base = v303_lines()
    ch, _log = A304.audit_changes(A304.load_inputs(inputs(), PID), base, profile())
    with pytest.raises(ValueError, match="changed twice"):
        A304.integrate(base, ch + [ch[0]])
    with pytest.raises(ValueError, match="does not have"):
        A304.integrate([base[0]] + base[2:], ch)                # the N1 neck line missing
    add = dict(ch[0], action="ADD")
    with pytest.raises(ValueError, match="only re-holds"):
        A304.integrate(base, [add])


def test_write_files_ledger_and_diff(tmp_path):
    base = v303_lines()
    inp = A304.load_inputs(inputs(), PID)
    ch, log = A304.audit_changes(inp, base, profile())
    names, ident, led = A304.write(tmp_path, base, ch, log, inp, released_lines=base)
    assert set(names) == {"V3_0_4_BOQ_LINES.json", "V3_0_4_BOQ_LINES.csv", "V3_0_4_INTEGRATION_LEDGER.json",
                          "V3_0_4_INTEGRATION_LEDGER.csv", "V3_0_4_DIFF.csv", "V3_0_4_RUN.json"}
    run_ = json.loads((tmp_path / "V3_0_4_RUN.json").read_text(encoding="utf-8"))
    assert run_["released_default"] is False and run_["extends"] == "ARCH_TAKEOFF_V3.0.3"
    assert ident["diff"]["vs_v3_0_3"] == {"CHANGED": 4, "SAME": 2}
    assert set(run_["totals_moved_by_code"]) == {"STR.CONC.NECK|m3", "STR.REBAR|kg"}
    assert led["integration_package"] is True and len(led["rows"]) == 4
    for r in led["rows"]:
        assert r["evidence_status"] in ("HELD", "UNKNOWN") and r["release_status"] == "NOT RELEASED"
        assert r["drawing_reference"] and r["owner_manual_method"] and r["drawing_method"]
    assert run_["evidence_status_counts"] == {"HELD": 3, "UNKNOWN": 1}


def test_no_project_constants_in_the_module():
    text = (ROOT / "engine/source/arch_v304.py").read_text(encoding="utf-8")
    for word in ("Alsenan", "ST7757", "P7757", "7757", "1.50", "0.22"):
        assert word not in text


def test_the_earlier_method_lists_are_untouched():
    from tools import urban_boq_m9 as M9
    assert M9.CANDIDATE_METHODS == ("ARCH_TAKEOFF_V3.0",) and M9.CANDIDATE_EXTENSIONS == ("ARCH_TAKEOFF_V3.0.1",)
    assert M9.CANDIDATE_EXTENSIONS_V302 == ("ARCH_TAKEOFF_V3.0.2",)
    assert M9.CANDIDATE_EXTENSIONS_V303 == ("ARCH_TAKEOFF_V3.0.3",)
    assert M9.CANDIDATE_EXTENSIONS_V304 == ("ARCH_TAKEOFF_V3.0.4",) and M9.V304 not in M9.ARCH_METHODS


# ------------------------------------------------------------------------------------------------ end to end
def test_end_to_end_v3_0_3_files_unchanged_and_v3_0_4_beside_them(tmp_path):
    """the synthetic villa through tools/urban_boq_m9.py: a V3.0.3 run, then V3.0.4 with that run as the restricted
    comparison (nothing rests on the removed value): the V3.0.3 files are byte-identical and V3.0.4 holds nothing; a
    restricted run whose first released line is turned into a held range holds exactly that line."""
    import test_arch_v30 as T131
    from tools import arch_synth as AS
    AS.villa(tmp_path / "villa.dxf")
    a = T131._run(tmp_path / "villa.dxf", tmp_path / "v303", "ARCH_TAKEOFF_V3.0.3")
    prof = tmp_path / "prof.json"
    prof.write_text(json.dumps(profile()), encoding="utf-8")
    df = tmp_path / "df.json"
    df.write_text(json.dumps(dict(data_file(), project=T131.PID,
                                  records=[dict(r, project=T131.PID) for r in data_file()["records"]])),
                  encoding="utf-8")
    inp = tmp_path / "inp.json"
    inp.write_text(json.dumps({"schema": "URBAN_V304_PROFILE_AUDIT_FILES_V1", "project": T131.PID,
                               "data_file": "df.json", "runs": [{"id": "RESTRICTED", "removed_keys": NOT_USABLE,
                                                                 "profile": "prof.json",
                                                                 "lines": str(a / "V3_0_3_BOQ_LINES.json")}]}),
                   encoding="utf-8")
    b = T131._run(tmp_path / "villa.dxf", tmp_path / "v304", "ARCH_TAKEOFF_V3.0.4", "--v304-inputs", str(inp),
                  "--profile", str(prof))
    for name in ("V3_0_BOQ_LINES.json", "V3_0_1_BOQ_LINES.json", "V3_0_2_BOQ_LINES.json", "V3_0_3_BOQ_LINES.json",
                 "V3_0_3_INTEGRATION_LEDGER.json", "BOQ_LINES.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    assert (b / "V3_0_4_BOQ_LINES.json").read_bytes() == (b / "V3_0_3_BOQ_LINES.json").read_bytes()
    run_ = json.loads((b / "V3_0_4_RUN.json").read_text(encoding="utf-8"))
    assert run_["identity"]["replaced"] == 0
    # adverse: the restricted run holds one released line
    l3 = T131._lines(a / "V3_0_3_BOQ_LINES.json")
    i = next(k for k, x in enumerate(l3) if x["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
             and (x["measured_net"] or 0) > 0)
    v = l3[i]["measured_net"]
    l3[i] = dict(l3[i], evidence_state="BOUNDED_EXPOSURE", measured_net=None,
                 bounded_range={"low": v * 0.9, "high": v * 1.2, "basis": "synthetic"})
    (tmp_path / "restricted.json").write_text(json.dumps(l3), encoding="utf-8")
    d = json.loads(inp.read_text(encoding="utf-8"))
    d["runs"][0]["lines"] = "restricted.json"
    inp.write_text(json.dumps(d), encoding="utf-8")
    c = T131._run(tmp_path / "villa.dxf", tmp_path / "v304b", "ARCH_TAKEOFF_V3.0.4", "--v304-inputs", str(inp),
                  "--profile", str(prof))
    l4 = T131._lines(c / "V3_0_4_BOQ_LINES.json")
    moved = [y for x, y in zip(T131._lines(a / "V3_0_3_BOQ_LINES.json"), l4) if A30.line_sha(x) != A30.line_sha(y)]
    assert len(moved) == 1 and moved[0]["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (moved[0]["bounded_range"]["low"], moved[0]["bounded_range"]["high"]) == (A(v * 0.9), A(v * 1.2))
