"""T-576 development-villa run (research, unwired): the B10 GF / 1F column measured-set differences of T-572 restated as
signed causes per mark and per CONFLICT reading, and the GF B7 beam UNTRACED of T-566 tested against a complete
support allowance (R-T576-1 .. 4).

    .work/venv/bin/python -I research/agents_t576/t576_alsenan.py --freelancer .work/private/concrete_rebar.xlsx [--write]

Engine: candidate of record ARCH_TAKEOFF_V3.0.58 (NOT RELEASED); column lines = research/agents_t507/out/
LINE_INDEX_V3_0_57.json through the merged T-551 reader (member data from the merged T-394 per-line record). Positions /
marks / CONFLICTs: the merged T-566 register (POSITION_INPUT_T566.json + out/T566_REGISTRATION.json, an own read of
ST7757 dxf). Settled framing depths (D_low) of the open members: the merged T-119 ledger. Storey datums: T-214
(DRAWING-CONFIRMED slab tops +0.95 / +5.45 / +9.65). Beam GF B7: the merged T-545 mark terms, T-252 ledger pieces /
widths, T-229 support ends, T-392 ring closure.
Freelancer: Drive "Alsenan chalet project", the concrete + rebar workbook (sha256 ae608411..., read in memory through the
merged t551_alsenan.his_rows). Tracked output: engine figures and terms in m3 only (no row, dimension or count of his).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t576_rules as R  # noqa: E402

OUT = HERE / "out" / "T576_COLUMN_CAUSES.json"
WB_SHA = "ae608411"
D = Decimal
STOREY_INTERVAL = {"GF": D("4.50"), "1F": D("4.20")}      # T-214: +0.95 -> +5.45 -> +9.65 (slab tops)
STOREY_BASE = {"GF": D("0.95"), "1F": D("5.45")}
# R-T566-1 CONFLICT positions whose lines are VALUED or HELD members on GF / 1F (T-566 s.2): position -> line per storey
CONFLICT_LINES = {
    "10E0": {"cands": ("C7", "C8"), "lines": {"GF": "L-4c4496579e5bfa20ae9f", "1F": "L-1dc713c83bf62e525ff2"}},
    "10AE": {"cands": ("C", "C3"), "lines": {"GF": "L-694a75c84dd6e4bb4491"}},
}


def _a551():
    sys.path.insert(0, str(RES / "agents_t551"))
    return importlib.import_module("t551_alsenan"), importlib.import_module("t551_rules")


def _t566():
    pin = json.loads((RES / "agents_t566" / "POSITION_INPUT_T566.json").read_text(encoding="utf-8"))
    reg = json.loads((RES / "agents_t566" / "out" / "T566_REGISTRATION.json").read_text(encoding="utf-8"))
    return pin, reg


def _t119():
    rows = csv.DictReader((RES / "agents_t119" / "COLUMNS_TO_CONTROLLING_MEMBER.csv").open(encoding="utf-8"))
    return {r["id"]: r for r in rows}


def _t394():
    d = json.loads((RES / "agents_t394" / "summary_t394.json").read_text(encoding="utf-8"))
    return {r["line_id"]: r for r in d["per_line_engine"]}


# ------------------------------------------------------------------------------------------------- positions
def registered_members(pin, reg, reading):
    """storey -> mark -> number of drawn own members (SOLID outline over a position) under the reading; plus the marks
    a CONFLICT position can carry on each storey."""
    by_pos = {p["position"]: p for p in pin["positions"]}
    out = {"GF": defaultdict(int), "1F": defaultdict(int)}
    conflict_marks = {"GF": set(), "1F": set()}
    for p in reg["positions"]:
        members = by_pos[p["position"]]["members"]
        for sheet_st in ("GF", "1F"):
            if sheet_st not in members:
                continue
            if p["class"] == "REGISTERED":
                out[sheet_st][p["mark"]] += 1
            else:
                out[sheet_st][reading[p["position"]]] += 1
                conflict_marks[sheet_st] |= set(p["candidates"])
    # planted 1F columns: SOLID outlines on FFRS not over a position (T-566 'slab_outlines_not_on_a_position')
    planted = [r for r in pin["slab_outlines_not_on_a_position"] if r["sheet"] == "FFRS" and r["hatch"] == "SOLID"]
    return out, conflict_marks, planted


# ------------------------------------------------------------------------------------------------- columns
def column_split(freelancer, reading):
    A, R551 = _a551()
    pin, reg = _t566()
    t119, t394 = _t119(), _t394()
    remap = {}
    for pos, c in CONFLICT_LINES.items():
        for st, lid in c["lines"].items():
            remap[lid] = reading[pos]
    cols = A.column_lines()
    for c in cols:
        if c["line_id"] in remap:
            c["mark"] = remap[c["line_id"]]
    his, _ = A.his_rows(freelancer)
    his_neck = defaultdict(int)
    for r in his["NECK"]:
        his_neck[r["label"]] += r["n"]
    regm, conflict_marks, planted = registered_members(pin, reg, reading)
    out = {}
    for st in ("GF", "1F"):
        hm = defaultdict(list)
        for r in his[st]:
            lab = r["label"]
            if lab.startswith("PC"):
                lab = "P.C %dx%d" % (round(float(r["b"]) * 100), round(float(r["c"]) * 100))
            hm[lab].append(r)
        # STOREY term: his h + his head depth = drawn interval on every row of the storey (R-T576-1)
        his_depths = {R.d6(STOREY_INTERVAL[st] - R.d6(r["h"])) for r in his[st]}
        assert len(his_depths) == 1, (st, his_depths)
        d_his = his_depths.pop()
        storey_terms = {str(R.storey_term(STOREY_INTERVAL[st], r["h"], d_his)) for r in his[st]}
        assert storey_terms == {"0.000000"}
        lines = [c for c in cols if c["storey"] == st and c["class"] != "EXCLUDED"]
        marks = sorted({c["mark"] for c in lines} | set(hm))
        rows = []
        for mk in marks:
            hr = hm.get(mk, [])
            n_h = sum(r["n"] for r in hr)
            valued = [c for c in lines if c["mark"] == mk and c["class"] == "RELEASED"]
            held = [c for c in lines if c["mark"] == mk and c["class"] == "HELD"]
            v = [{"A": c["A"], "h": c["h"], "base": c["base"], "d_ctrl": c["d_ctrl"], "m3": c["m3"]} for c in valued]
            k, e, f = R551.column_mark_split(his_n=n_h, his_b=hr[0]["b"] if hr else None,
                                             his_c=hr[0]["c"] if hr else None, his_h=hr[0]["h"] if hr else None,
                                             valued=v, held_n=len(held), storey_base=STOREY_BASE[st])
            in_set = not held and e > 0 and f > 0
            row = {"mark": mk, "engine_m3": str(e), "in_measured_set": in_set}
            terms = []
            # HEIGHT_OPEN refined per open member at the settled framing depth (R-T576-1)
            if k.get("HEIGHT_OPEN"):
                ho = D(0)
                for c in valued:
                    if c["d_ctrl"] is not None:
                        continue
                    t1 = t119[t394[c["line_id"]]["t119_id"]]
                    assert t1["hold_cause"] == "FRAMING_MEMBER_HELD_D_OPEN", c["line_id"]
                    sp = R.member_height_split(A=c["A"], h_e=c["h"], base_drop=STOREY_BASE[st] - D(str(c["base"])),
                                               his_h=hr[0]["h"], d_low=t1["D_ctrl"])
                    ho += sp["JOINT_HEAD"] + sp["BASE"] + sp["GLOBAL_DEPTH"]
                    terms.append({"term": "JOINT_HEAD", "class": "RULE_DIFFERENCE", "m3": sp["JOINT_HEAD"],
                                  "note": f"at D_low {t1['D_ctrl']} ({t1['controlling']}, printed); D_ctrl open on "
                                          f"{t1['notes'] or t1['reason']}: lower end", "member": c["member"]})
                    if sp["BASE"]:
                        terms.append({"term": "BASE", "class": "ENGINE_RIGHT", "m3": sp["BASE"], "member": c["member"]})
                    terms.append({"term": "GLOBAL_DEPTH", "class": "ENGINE_RIGHT", "m3": sp["GLOBAL_DEPTH"],
                                  "note": "upper end; lower open (<= this) by the unprinted framing depth",
                                  "member": c["member"], "open_below": True})
                assert ho == k["HEIGHT_OPEN"], (st, mk, ho, k["HEIGHT_OPEN"])
            for t in ("COUNT", "HELD", "SECTION", "JOINT_HEAD", "BASE", "GLOBAL_DEPTH"):
                x = k.get(t, D(0))
                if not x:
                    continue
                cc = None
                if t == "COUNT":
                    drawn_n = len(valued) + len(held)
                    cc = R.count_verdict(drawn_n=drawn_n, registered_n=regm[st].get(mk, 0) if not mk.startswith("P.C")
                                         else drawn_n, conflict_positions=mk in conflict_marks[st])
                terms.append({"term": t, "class": R.classify(t, count_class=cc), "m3": x})
            if k.get("COUNT"):
                row["count_evidence"] = {
                    "drawn_own_members": len(valued) + len(held), "registered_members": regm[st].get(mk, 0),
                    "his_storey_rows_exceed_his_neck_rows_of_mark": n_h > his_neck.get(mk, 0),
                    "his_storey_rows_below_drawn": n_h < len(valued) + len(held)}
            assert sum((R.d6(x["m3"]) for x in terms), D(0)) == e - f, (st, mk)
            row["terms"] = [dict(x, m3=str(R.d6(x["m3"]))) for x in terms]
            row["_his"] = f
            rows.append(row)
        ms = [r for r in rows if r["in_measured_set"]]
        E = sum((D(r["engine_m3"]) for r in ms), D(0))
        H = sum((r["_his"] for r in ms), D(0))
        cls = R.class_table([t for r in ms for t in r["terms"]])
        assert sum(cls.values(), D(0)) == E - H
        net_rd = E - H - cls.get("RULE_DIFFERENCE", D(0))
        open_terms = [t for r in ms for t in r["terms"] if t.get("open_below")]
        out[st] = {"marks_all": [{k_: v_ for k_, v_ in r.items() if k_ != "_his"} for r in rows],
                   "measured_set": {"marks": [r["mark"] for r in ms], "engine_m3": str(R.d6(E)),
                                    "his_m3": str(R.d6(H)), "diff_m3": str(R.d6(E - H)), "pct": str(R.pct(E - H, H)),
                                    "by_class_m3": {k_: str(v_) for k_, v_ in cls.items()},
                                    "net_of_rule_difference_m3": str(R.d6(net_rd)),
                                    "net_of_rule_difference_pct": str(R.pct(net_rd, H)),
                                    "open_counter_terms": [{"member": t["member"], "m3_upper": t["m3"]}
                                                           for t in open_terms]},
                   "his_head_depth_m": str(d_his), "storey_term_m3": "0.000000",
                   "storey_interval_m": str(STOREY_INTERVAL[st])}
    out["planted_1F_outlines_not_on_a_position"] = len(planted)
    return out


# ------------------------------------------------------------------------------------------------- beam GF B7
# Every end of every GF B7 piece (R-T576-3). Widths: T-252 ledger b_drawn of the carrier; columns: T-229 outline extent
# along the run. Ring ends: T-252 r2 ring outline (arcs 2EE / 2EF / 312 / 313 closed by faces 46D B8, 42D B17, 2A9 CB1,
# 437 B7) and T-392 s.1: every outer arc meets its closing face obliquely; the void arcs 2F0 / 318 / 317 touch B8 / B17 /
# 437 at single points (pinches), which split the ring into four arc pieces.
B7_PIECES = [
    {"piece": "GF:BAND0025.1 (straight)", "L_m": "1.2", "source": "T-229 ends 33E / 341 (COLUMN_BELOW)",
     "ends": [{"kind": "COLUMN", "member": "33E", "width_m": "0.5"}, {"kind": "COLUMN", "member": "341", "width_m": "0.5"}]},
    {"piece": "GF:BAND0006 (straight, face 437)", "L_m": "1.7", "source": "T-229 ends BAND0003 / BAND0041.2 (BEAM)",
     "ends": [{"kind": "CARRIER", "member": "B8 BAND0003", "width_m": "0.2"},
              {"kind": "CARRIER", "member": "CB1 BAND0041.2", "width_m": "0.35"}]},
    {"piece": "GF:BAND0049 (quarter arc R 1.10 / 1.30)", "L_m": "1.884953", "source": "no T-229 end record (curved); "
     "drawn: end 0 deg closed by line 484 against the HELD unlabelled piece GF-112 (BM-GF-062, 0.20 x 0.50, D-04) "
     "in line with B4 up to column 353; end 90 deg collinear with B2 BAND0027 (same faces, mark boundary)",
     "ends": [{"kind": "COLLINEAR_OTHER_MARK", "member": "B2 BAND0027", "width_m": "0"},
              {"kind": "COLLINEAR_OTHER_MARK", "member": "GF-112 (held, unlabelled; beside, never in the allowance)",
               "width_m": "0"}],
     "beside": [{"member": "GF-112", "length_m": "0.5", "status": "HELD D-04"},
                {"member": "outer-face arc 29F", "length_m": "0.157080", "status": "CURVE_FACE reading (R 1.30 vs 1.20)"}]},
    {"piece": "RING-B7 NW arc (2EE)", "L_m": None, "source": "T-252 r2 ring outline; T-392 s.1",
     "ends": [{"kind": "SAME_MARK", "member": "B7 face 437", "width_m": "0"},
              {"kind": "CARRIER", "member": "B8 face 46D (BAND0003)", "width_m": "0.2"}]},
    {"piece": "RING-B7 SW arc (2EF)", "L_m": None, "source": "T-252 r2 ring outline; T-392 s.1",
     "ends": [{"kind": "CARRIER", "member": "B8 face 46D (BAND0003)", "width_m": "0.2"},
              {"kind": "CARRIER", "member": "B17 face 42D (BAND0044.1)", "width_m": "0.45"}]},
    {"piece": "RING-B7 SE arc (312)", "L_m": None, "source": "T-252 r2 ring outline; T-392 s.1",
     "ends": [{"kind": "CARRIER", "member": "B17 face 42D (BAND0044.1)", "width_m": "0.45"},
              {"kind": "CARRIER", "member": "CB1 face 2A9 (BAND0041.2)", "width_m": "0.35"}]},
    {"piece": "RING-B7 NE arc (313)", "L_m": None, "source": "T-252 r2 ring outline; T-392 s.1",
     "ends": [{"kind": "CARRIER", "member": "CB1 face 2A9 (BAND0041.2)", "width_m": "0.35"},
              {"kind": "SAME_MARK", "member": "B7 face 437", "width_m": "0"}]},
]
RING_PLAN_M2 = D("0.666406")        # T-252 r2 exact arcs; line RING-B7 0.499805 m3 = 0.666406 x 0.75
B7_B, B7_D = D("0.2"), D("0.75")


def beam_b7():
    t545 = json.loads((RES / "agents_t545" / "out" / "T545_BEAM_RECONCILE.json").read_text(encoding="utf-8"))
    m = [x for x in t545["marks"] if x["floor"] == "GF" and x["mark"] == "B7"]
    assert len(m) == 1
    m = m[0]
    resid = R.d6(m["THROUGH_SUPPORT"]) + R.d6(m["UNTRACED"])
    assert set(m) == {"floor", "mark", "THROUGH_SUPPORT", "UNTRACED"}          # COUNT / SECTION / HELD 0 on this mark
    old_allow, _ = R.allowance(B7_PIECES[:2])
    new_allow, missing = R.allowance(B7_PIECES)
    old_cls = R.untraced_test(his_minus_engine_m3=resid, b=B7_B, D=B7_D, allowance_m=old_allow, missing=[])
    cls = R.untraced_test(his_minus_engine_m3=resid, b=B7_B, D=B7_D, allowance_m=new_allow, missing=missing)
    excess = R.d6(-resid / (B7_B * B7_D))
    sens = {}
    for name, keep in (("CB1 ends only", ("CB1",)), ("CB1 + B8 ends", ("CB1", "B8")), ("CB1 + B17 ends", ("CB1", "B17"))):
        ring = [dict(p, ends=[e for e in p["ends"] if e["kind"] != "CARRIER" or any(k in e["member"] for k in keep)])
                for p in B7_PIECES[3:]]
        a, _ = R.allowance(B7_PIECES[:3] + ring)
        c = R.untraced_test(his_minus_engine_m3=resid, b=B7_B, D=B7_D, allowance_m=a, missing=[])
        sens[name] = {"allowance_m": str(a), "class": c[0], "untraced_m3": str(R.d6(c[2]))}
    return {
        "mark": "GF B7", "mark_residual_m3": str(resid),
        "t545_split_m3": {"THROUGH_SUPPORT": m["THROUGH_SUPPORT"], "UNTRACED": m["UNTRACED"]},
        "his_longer_by_m": str(excess),
        "allowance_t545_m": str(old_allow), "t545_reclass_check": old_cls[0],
        "allowance_complete_m": str(new_allow), "missing_end_records": missing,
        "result": {"class": cls[0], "THROUGH_SUPPORT_m3": str(R.d6(cls[1])), "UNTRACED_m3": str(R.d6(cls[2])),
                   "verdict": "RULE_DIFFERENCE (THROUGH_SUPPORT: his B7 lengths run into the carriers that close the "
                              "curved pieces; the engine bills each crossing once, the carrier owns it)"},
        "ring_equivalent_length_m": str(R.d6(RING_PLAN_M2 / B7_B)),
        "sensitivity_ring_carriers": sens,
        "not_apportioned": "his two B7 rows carry no location: the excess is inside the drawn allowance, not bound to a "
                           "crossing; GF-112 (held) and the outer-face arc reading are listed beside",
        "pieces": B7_PIECES}


# ------------------------------------------------------------------------------------------------- build
def build(freelancer):
    sha = hashlib.sha256(Path(freelancer).read_bytes()).hexdigest()
    if not sha.startswith(WB_SHA):
        raise SystemExit("not the B1-manifest workbook")
    _, reg = _t566()
    conflicts = {p["position"]: list(p["candidates"]) for p in reg["positions"] if p["class"] == "CONFLICT"}
    assert set(conflicts) == set(CONFLICT_LINES)
    res = []
    for rd in R.readings(conflicts):
        res.append({"reading": rd, "columns": column_split(freelancer, rd)})
    # the merged T-572 measured set = the merged reading (10AE C3, 10E0 C8)
    t572 = json.loads((RES / "agents_t572" / "out" / "T572_HELD_BOUNDS.json").read_text(encoding="utf-8"))["measured_set"]
    merged = [r for r in res if r["reading"] == {"10AE": "C3", "10E0": "C8"}][0]["columns"]
    for st in ("GF", "1F"):
        assert merged[st]["measured_set"]["diff_m3"] == t572[f"columns_{st}"]["diff"], st
        assert merged[st]["measured_set"]["engine_m3"] == t572[f"columns_{st}"]["engine"], st
    return {"schema": "T576_COLUMN_CAUSES_V1",
            "candidate": "ARCH_TAKEOFF_V3.0.58 (structural lines = V3.0.57 LINE_INDEX); NOT RELEASED",
            "note": "engine figures and terms in m3; his storey totals on the measured set only; no row, dimension or "
                    "count of his",
            "readings": res, "beam_gf_b7": beam_b7()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = build(a.freelancer)
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in doc["readings"]:
        print(json.dumps(r["reading"]), {st: r["columns"][st]["measured_set"] for st in ("GF", "1F")})
    print(json.dumps({k: v for k, v in doc["beam_gf_b7"].items() if k != "pieces"}, indent=1))


if __name__ == "__main__":
    main()
