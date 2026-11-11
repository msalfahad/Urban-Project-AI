"""T-672 ARCH_TAKEOFF_V3.0.68 (MASONRY GATE B ROUND 1) on a synthetic villa-K672 candidate (hand fixture, not the
development villa): the V3.0.59 producer's material lines re-produced on a rulebook version that confirms the 0.15 m
black module, AAC lines retired on a host a printed note makes black, perimeter joint and lintel bed lines added.

Villa K672 by hand (40 x 20 module, 0.39 x 0.19 unit, 10 mm joint; kappa = 0.0741 / 0.08 = 0.92625):
  A  GF black 0.20 VERIFIED, net 20.000 m2; REQUIRED RC lintels D-A face 0.36 and D-A2 face 0.30 m2
       base 19.34 m2 -> 241.75 pcs (unchanged by the rulebook step: 0.20 was already confirmed)
  C  1F black 0.15 OWNER-APPROVED, net 8.000 m2; HELD lintel D-C face 0 .. 0.32 m2
       rulebook 1.0.0: units / mortar HELD (0.15 module not stated); rulebook 1.0.0 + 0.15 confirmed:
       base 7.68 .. 8.00 m2 -> units 96.0 .. 100.0 pcs, mortar x 0.0110625 = 0.08496 .. 0.0885 m3 (RESTATED)
  B  1F white 0.15 DRAWING-CONFIRMED, net 10.000 m2: glue 35.0 kg; units HELD (unchanged)
  S  below-ground host 'HOUSE_BELOW_NG:S1' HELD, no colour in its id: 4 blank lines; a printed note makes it black:
       its AAC glue / AAC unit lines NOT_APPLICABLE_WITH_EVIDENCE, black pair stays HELD
  perimeter: A VALUE 0.010 m3; C drawn 0.004 .. 0.006 + bands 0 .. 0.001 + pieces 0 .. 0.0005 = 0.004 .. 0.0075 m3;
       S HELD with the host's cause
  bed: f(0.20) = 0.92625 x 0.20 x 0.010 = 0.0018525 m3/m; D-A bearing 0.80 -> 0.001482 m3 (EXACT);
       D-A2 0.40 .. 0.60 m -> 0.000741 .. 0.0011115 (0.001111 / 0.001112 by float, asserted as the module rounds);
       f(0.15) = 0.001389375; D-C lintel HELD -> 0 .. 0.80 f = 0 .. 0.001111 m3 (HELD BOUNDED)
"""
import copy

import pytest

from engine.source import arch_v304 as A304
from engine.source import arch_v3059 as P
from engine.source import arch_v3068 as M
from engine.source import boq_line as BL
from engine.source import company_rulebook_v1 as CR

PID, REV = "villa-k672", "0" * 64
E_A = "GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK"
E_B = "1F-WALLS:walls t=0.15#BLOCKWORK:DRAWING_CONFIRMED_WHITE"
E_C = "1F-WALLS:walls t=0.15#BLOCKWORK:ASSUMED___OWNER_APPROVED_BLACK"
E_S = "HOUSE_BELOW_NG:S1"


def mk(eid, code, unit, state, net=None, floor="GF", inputs=None):
    return BL.make_line(inputs=inputs, project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit,
                        evidence_state=state, measured_net=net, gross=net, element_id=eid, floor=floor,
                        formula="synthetic", rule_id="R-X", rule_version="1", item_en=code, item_ar=code,
                        trade=None if code in BL.ITEMS else "MASONRY",
                        rfi={"question": "formation level not printed"} if state == "BLOCKED_RFI" else None)


def lid(eid, code="MAS.BLOCK", unit="m2"):
    return BL.line_id(PID, code, eid, "R-X", "1", unit)


def lint(op, state, net, host, decision, floor="GF"):
    rec = {"opening_id": op, "decision": decision, "host_line": lid(host)}
    return mk(f"LINTEL:{op}", "STR.CONC.LINTEL", "m3", state, net, floor=floor, inputs={"lintel_v3053": rec})


def base():
    return [mk(E_A, "MAS.BLOCK", "m2", "MEASURED", 20.0),
            mk(E_B, "MAS.BLOCK", "m2", "SOURCE_DERIVED", 10.0, floor="1F"),
            mk(E_C, "MAS.BLOCK", "m2", "PROVISIONAL", 8.0, floor="1F"),
            mk(E_S, "MAS.BLOCK", "m2", "BLOCKED_RFI"),
            lint("D-A", "PROVISIONAL", 0.072, E_A, "REQUIRED"),
            lint("D-A2", "PROVISIONAL", 0.06, E_A, "REQUIRED"),
            lint("D-C", "BLOCKED_RFI", None, E_C, "HELD", floor="1F"),
            mk("GF-R1:skirting", "FIN.SKIRTING", "lm", "MEASURED", 9.0)]


SRC59 = [{"task": "T-K", "file": "ledger.py", "sha256": "k" * 64, "merge_commit": "abcdef12", "checker_run": "run k"}]
JOINT = {"module_m": [0.40, 0.20], "unit_m": [0.39, 0.19], "joint_mm": 10, "status": "OWNER-PROVISIONAL",
         "source": "villa K672 joint"}


def rulebook(confirm_015=False):
    rb = {"method": CR.METHOD, "version": CR.VERSION, "digest": CR.digest(),
          "records": {rid: {"status": CR.record(rid).get("status"),
                            "params": {k: copy.deepcopy(v.get("value") if isinstance(v, dict) else v)
                                       for k, v in CR.record(rid)["params"].items()}}
                      for rid in (P.R_BLOCK, P.R_GLUE, P.R_MORTAR)}}
    if confirm_015:
        rb["version"], rb["digest"] = "1.1.0-k672", "f" * 64
        rb["records"][P.R_BLOCK]["params"]["confirmed_modules_m"]["0.15"] = [0.4, 0.2]
    return rb


FACES = {lid(E_A): {"required": [{"opening_id": "D-A", "face_m2": 0.36}, {"opening_id": "D-A2", "face_m2": 0.30}],
                    "held": []},
         lid(E_C): {"required": [], "held": [{"opening_id": "D-C", "face_max_m2": 0.32, "why": "head"}]}}


def candidate():
    """the V3.0.59 producer on the base (rulebook 1.0.0): the candidate this version reads."""
    b = base()
    d = P.load_inputs({"schema": P.INPUTS_SCHEMA, "project": PID, "sources": SRC59, "joint": copy.deepcopy(JOINT),
                       "rulebook": rulebook(), "faces": copy.deepcopy(FACES)}, PID)
    ch, _ = P.changes_for(d, b)
    return b + [c["after"] for c in ch]


def mid(host, code):
    return P.material_ids({"project": {"project_id": PID}, "location": {"element_id": host}})[code]


SRC = [{"task": t, "file": f"{t}.json", "sha256": t[-1] * 64, "merge_commit": "1234abcd", "checker_run": f"run {t}"}
       for t in ("T-670", "T-372", "T-675")]


def restate_rows():
    after = {(E_A, P.U_BLACK): ["VALUE", 241.75], (E_A, P.MORTAR): ["VALUE", 0.285265],
             (E_B, P.GLUE): ["VALUE", 35.0], (E_B, P.U_WHITE): ["HELD", None],
             (E_C, P.U_BLACK): ["RANGE", [96.0, 100.0]], (E_C, P.MORTAR): ["RANGE", [0.08496, 0.0885]]}
    before = dict(after)
    before[(E_C, P.U_BLACK)] = before[(E_C, P.MORTAR)] = ["HELD", None]
    rows = [{"line_id": mid(h, c), "item_code": c, "host": h, "before": before[(h, c)], "after": a,
             "changed": before[(h, c)] != a} for (h, c), a in after.items()]
    rows += [{"line_id": mid(E_S, c), "item_code": c, "host": E_S, "before": ["HELD", None], "after": ["HELD", None],
              "changed": False} for c in P.CODES]
    return rows


def doc(**over):
    d = {"schema": M.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC),
         "producer": {"faces": copy.deepcopy(FACES), "joint": copy.deepcopy(JOINT), "sources": SRC59,
                      "faces_on_held_hosts": [], "rulebook_before": rulebook(), "rulebook_after": rulebook(True)},
         "restate": restate_rows(),
         "not_applicable": [{"line_id": mid(E_S, c), "item_code": c, "host": E_S, "evidence": "general note: black "
                             "block below the ground beams", "arch_check": "silent"} for c in (P.GLUE, P.U_WHITE)],
         "perimeter": [
             {"mortar_line_id": mid(E_A, P.MORTAR), "host_line_id": lid(E_A), "host": E_A, "state": "VALUE",
              "t372": {"low": 0.010, "high": 0.010, "walls": ["GF-K1"]}, "bands": []},
             {"mortar_line_id": mid(E_C, P.MORTAR), "host_line_id": lid(E_C), "host": E_C, "state": "RANGE",
              "t372": {"low": 0.004, "high": 0.006, "walls": ["1F-K2"]},
              "bands": [{"wall_id": "1F-K2", "high": 0.001, "low": 0.0, "verdict": "HELD bounded",
                         "end_ids": "run end | D-C lintel bearing not established",
                         "cause": "D-C: FLAGGED_DEFICIT lintel end"}],
              "t675": {"low": 0.004, "high_drawn_t372": 0.006, "held_bands": 1, "held_bands_high": 0.001,
                       "held_pieces": 1, "held_pieces_high": 0.0005, "envelope": [0.004, 0.0075],
                       "walls": ["1F-K2"]}},
             {"mortar_line_id": mid(E_S, P.MORTAR), "host_line_id": lid(E_S), "host": E_S, "state": "HELD",
              "t372": {"low": None, "high": None, "held_cause": "formation level not printed"}, "bands": []}],
         "lintel_bed": [
             {"opening_id": "D-A", "lintel_line_id": lid("LINTEL:D-A", "STR.CONC.LINTEL", "m3"),
              "mortar_line_id": mid(E_A, P.MORTAR), "state": "EXACT", "low": 0.001482, "high": 0.001482,
              "bearing_m": [0.8, 0.8]},
             {"opening_id": "D-A2", "lintel_line_id": lid("LINTEL:D-A2", "STR.CONC.LINTEL", "m3"),
              "mortar_line_id": mid(E_A, P.MORTAR), "state": "RANGE", "low": 0.000741,
              "high": round(0.6 * M.joint_factor(JOINT, 0.20), 6), "bearing_m": [0.4, 0.6],
              "ends": [{"low": 0.0, "high": 0.2, "side": "START"}, {"low": 0.4, "high": 0.4, "side": "END"}]},
             {"opening_id": "D-C", "lintel_line_id": lid("LINTEL:D-C", "STR.CONC.LINTEL", "m3"),
              "mortar_line_id": mid(E_C, P.MORTAR), "state": "HELD", "low": 0.0,
              "high": round(0.8 * M.joint_factor(JOINT, 0.15), 6), "cause": "lintel itself HELD"}]}
    d.update(over)
    return d


def run(d=None, prev=None):
    prev = candidate() if prev is None else prev
    ch, log = M.changes_for(M.load_inputs(d or doc(), PID), prev)
    new, ident = M.integrate(prev, ch)
    return prev, ch, log, new, ident


def after(ch, code, host=None, piece=None):
    out = [c["after"] for c in ch if c["after"]["item_code"] == code and (piece is None or c["piece"] == piece) and
           (host is None or c["after"]["location"]["element_id"].startswith(f"MATERIAL:{host}"))]
    assert len(out) == 1, out
    return out[0]


# ------------------------------------------------------------------------------------------------ normal
def test_joint_factor_by_hand():
    assert M.joint_factor(JOINT, 0.15) == pytest.approx(0.001389375)
    assert M.joint_factor(JOINT, 0.20) == pytest.approx(0.0018525)


def test_normal_hand_figures():
    prev, ch, log, new, ident = run()
    assert log["mat"] == {"reproduced": 10, "changed": 2, "unchanged": 8}
    u = after(ch, P.U_BLACK, E_C)
    assert u["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (u["bounded_range"]["low"], u["bounded_range"]["high"]) == pytest.approx((96.0, 100.0))
    m = after(ch, P.MORTAR, E_C)
    assert (m["bounded_range"]["low"], m["bounded_range"]["high"]) == pytest.approx((0.08496, 0.0885))
    assert m["line_id"] == mid(E_C, P.MORTAR)          # same producer, same id: replaced in place
    na = [c["after"] for c in ch if c["piece"] == M.P_NA]
    assert sorted(x["item_code"] for x in na) == sorted([P.GLUE, P.U_WHITE])
    assert all(x["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and x["measured_net"] is None for x in na)
    pa = after(ch, M.PERIM, E_A)
    assert pa["evidence_state"] == "PROVISIONAL" and pa["measured_net"] == pytest.approx(0.010)
    pc = after(ch, M.PERIM, E_C)
    assert (pc["bounded_range"]["low"], pc["bounded_range"]["high"]) == pytest.approx((0.004, 0.0075))
    ps = after(ch, M.PERIM, E_S)
    assert ps["evidence_state"] == "BLOCKED_RFI" and ps["measured_net"] is None and ps["rfi"]["question"]
    beds = {c["after"]["calculation"]["inputs"][M.REC_KEY]["opening_id"]: c["after"] for c in ch
            if c["piece"] == M.P_BED}
    assert beds["D-A"]["measured_net"] == pytest.approx(0.001482)
    assert beds["D-A2"]["bounded_range"]["low"] == pytest.approx(0.000741)
    assert beds["D-C"]["bounded_range"]["low"] == 0.0 and beds["D-C"]["bounded_range"]["high"] > 0
    assert ident["replaced"] == 4 and ident["added"] == 6
    sc = log["scenarios"]
    assert sc["deficit_lintels"] == ["D-A2"] and sc["B_available_bearing_no_end_bands_m3"] == pytest.approx(
        round(0.6 * M.joint_factor(JOINT, 0.20), 6))


def test_every_other_line_byte_identical_and_totals_only_masonry_codes():
    prev, ch, log, new, ident = run()
    named = {c["after"]["line_id"] for c in ch}
    old = {x["line_id"]: x for x in prev}
    assert all(BL.dumps([x]) == BL.dumps([old[x["line_id"]]]) for x in new if x["line_id"] not in named)
    moved = M.check_totals(A304.code_totals(prev), A304.code_totals(new), ch)
    assert set(k.split("|")[0] for k in moved) <= set(M.CODES)
    assert ident["masonry"]["perimeter"] == 3 and ident["masonry"]["lintel_bed"] == 3


def test_mirror_order_same_lines():
    _, ch1, *_ = run()
    _, ch2, *_ = run(prev=list(reversed(candidate())))
    assert sorted(BL.dumps([c["after"]]) for c in ch1) == sorted(BL.dumps([c["after"]]) for c in ch2)


# ------------------------------------------------------------------------------------------------ adverse
def test_adverse_candidate_not_reproduced_is_refused():
    prev = candidate()
    i = next(k for k, x in enumerate(prev) if x["line_id"] == mid(E_A, P.U_BLACK))
    prev[i] = BL.validate(dict(copy.deepcopy(prev[i]), measured_net=999.0, gross=999.0))
    with pytest.raises(M.InputsError, match="does not reproduce"):
        run(prev=prev)


def test_adverse_expected_figure_differs_refused():
    d = doc()
    r = next(x for x in d["restate"] if x["line_id"] == mid(E_C, P.U_BLACK))
    r["after"] = ["RANGE", [96.0, 101.0]]
    with pytest.raises(M.InputsError, match="T-670 figure"):
        run(d)


def test_adverse_typed_rate_refused():
    with pytest.raises(M.InputsError, match="typed rate"):
        run(doc(blocks_per_m2=12.5))


def test_adverse_na_on_coloured_host_refused():
    d = doc()
    d["not_applicable"] = [{"line_id": mid(E_B, P.U_WHITE), "item_code": P.U_WHITE, "host": E_B, "evidence": "x"}]
    with pytest.raises(M.InputsError, match="carries its colour"):
        run(d)


def test_adverse_held_host_keeps_perimeter_blank_never_zero():
    d = doc()
    d["perimeter"][2]["state"] = "VALUE"
    d["perimeter"][2]["t372"] = {"low": 0.0, "high": 0.0}
    with pytest.raises(M.InputsError, match="blank panel"):
        run(d)


def test_adverse_missing_perimeter_entry_refused():
    d = doc()
    d["perimeter"] = d["perimeter"][:2]
    with pytest.raises(M.InputsError, match="without a perimeter entry"):
        run(d)


def test_adverse_envelope_not_the_ledger_refused():
    d = doc()
    d["perimeter"][1]["t675"]["envelope"] = [0.004, 0.0080]
    with pytest.raises(M.InputsError, match="envelope"):
        run(d)


def test_adverse_bed_under_held_lintel_measured_refused():
    d = doc()
    d["lintel_bed"][2].update(state="EXACT", bearing_m=[0.8, 0.8], low=0.001111, high=0.001111)
    with pytest.raises(M.InputsError, match="blank / held lintel"):
        run(d)


def test_adverse_bed_figure_not_recomputed_refused():
    d = doc()
    d["lintel_bed"][0]["high"] = d["lintel_bed"][0]["low"] = 0.0015
    with pytest.raises(M.InputsError, match="recomputed"):
        run(d)


def test_adverse_applied_twice_refused():
    prev, ch, log, new, ident = run()
    with pytest.raises(M.InputsError, match="already carries"):
        run(prev=new)


def test_adverse_unit_or_rotation_does_not_change_counts():
    """units: a 0.15 m host in millimetres in a face is refused by the producer (unit error, not a figure)."""
    d = doc()
    d["producer"]["faces"][lid(E_C)]["held"][0]["face_max_m2"] = 320.0
    with pytest.raises(M.InputsError):
        run(d)
