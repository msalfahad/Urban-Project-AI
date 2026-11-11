"""T-706 development-villa statement: the CONC.SLAB key residual (reference - engine released -0.462755 m3, -0.77 %)
closed storey by storey to its causes, and the CONC.BEAM reference slip (-0.128 m3) tied to its drawn member.

Reads committed files only:
  - research/agents_t693/out/LINE_INDEX_V3_0_70.json (candidate of record V3.0.70, master 1.71.0): every STR.CONC.SLAB
    line, released m3 per storey;
  - out/T706_OWN_PANELS.json (t706_measure.py, own re-measure of GF / 1F / 2F from the private ST DXF, numbers only);
  - research/agents_t688/out/T688_STATEMENT.json (1F cause split, merged a62b3024; re-checked here: the 1F own area of
    this run equals T-688's to the digit);
  - out/T706_REFERENCE_1F_BEAM.json (t706_reference.py, own read of the beam sheet block, numbers only) and
    research/agents_t545/out/T545_BEAM_RECONCILE.json (1F B1 split: the engine bills both B1 runs);
  - research/agents_t525/out/LINE_INDEX_V3_0_58.json (to show the 1F released beam lines did not change since T-545).
The reference slab values are the typed constants of his slab sheet as quoted by T-683 (GF 207, 1F 120, roof 31.84 x
0.16 + 13.35 x 0.18); no derivation exists behind them. The reference is never a quantity and agreement never proof.

    python3 -I research/agents_t706/t706_alsenan.py [--write] [--check]

Development villa: no accuracy claim; nothing released; no quantity changed.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t706_rules as R  # noqa: E402

INDEX = "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
INDEX_58 = "research/agents_t525/out/LINE_INDEX_V3_0_58.json"
OWN = "research/agents_t706/out/T706_OWN_PANELS.json"
T688 = "research/agents_t688/out/T688_STATEMENT.json"
T545 = "research/agents_t545/out/T545_BEAM_RECONCILE.json"
REFB = "research/agents_t706/out/T706_REFERENCE_1F_BEAM.json"
OUT_JSON, OUT_MD = HERE / "out" / "T706_STATEMENT.json", HERE / "out" / "T706_STATEMENT.md"

REF_SLAB = {"GF": {"0.16": "207"}, "1F": {"0.16": "120"}, "2F": {"0.16": "31.84", "0.18": "13.35"}}
KEY_REF_M3 = Decimal("59.8174")              # his slab cover total (T-694 key CONC.SLAB)
# drawn beam widths (m) of this villa, from the merged T-229 beam-support input (widths rounded to 0.01 m)
MEMBER_SECTIONS = ("0.20", "0.25", "0.30", "0.35", "0.40", "0.45", "0.50", "0.55", "0.65", "0.90")


def J(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def q6(x):
    return f"{Decimal(x).quantize(Decimal('0.000001')):f}"


def slab_lines():
    return [x for x in J(INDEX)["lines"] if x["item_code"] == "STR.CONC.SLAB"]


def storey_statement(st, own_st):
    rows = own_st["lines"]
    loc = R.check_location([{"line_id": r["line_id"], "class": r["class"], "own_face": r["own_face"],
                             "engine_m2": r["engine_face_m2"], "own_m2": r["own_m2"] or 0} for r in rows])
    rel = [r for r in rows if r["class"] == "RELEASED"]
    # engine panel area = released net m3 / its thickness (net of the member overlaps the engine deducts)
    eng = [{"id": r["line_id"], "m2": Decimal(str(r["engine_m3"])) / Decimal(str(r["t_m"])),
            "marks": ([Decimal("0.18")] if r.get("thickness_marks_inside") == ["18", "T"] else
                      [Decimal("0.16")] if r.get("thickness_marks_inside") == ["16", "T"] else [])} for r in rel]
    own = {r["line_id"]: Decimal(str(r["own_m2"])) for r in rel}
    zr = R.zone_reconcile(eng, own, REF_SLAB[st], sheet_default_t="0.16")
    engine_m3 = sum(Decimal(str(r["engine_m3"])) for r in rel)
    if engine_m3 != zr["engine_m3"].quantize(Decimal("0.000001")):
        raise SystemExit(f"T-706 {st}: zone engine m3 {zr['engine_m3']} != released {engine_m3}")
    # physical class of every EXCLUDED line and every own face no line owns
    classes, excl, census = {}, [], []
    for r in rows:
        if r["class"] != "EXCLUDED":
            continue
        c = R.classify_face({"mean_width_m": r["own_inscribed_width_m"], "opening_lines": r["opening_lines"],
                             "inner_lines": r["inner_lines"], "member_label": r["member_label_inside"],
                             "thickness_mark": bool(r["thickness_marks_inside"])}, member_sections_m=MEMBER_SECTIONS)
        classes["line " + r["line_id"]] = c
        excl.append({"line_id": r["line_id"], "engine_face_m2": r["engine_face_m2"], "own_face_m2": r["own_m2"],
                     "inscribed_width_m": r["own_inscribed_width_m"], "class": c})
    for c_ in own_st["census"]:
        c = R.classify_face({"mean_width_m": c_["own_inscribed_width_m"], "opening_lines": c_["opening_lines"],
                             "inner_lines": c_["inner_lines"], "member_label": c_["member_label_inside"],
                             "radial_ring_segment": c_["radial_ring_segment"],
                             "thickness_mark": bool(c_["thickness_marks_inside"])}, member_sections_m=MEMBER_SECTIONS)
        classes[f"face {c_['own_face']}"] = c
        census.append(c)
    closure = R.storey_closure(classes)
    by = {}
    for c in census:
        by[c] = by.get(c, 0) + 1
    checked = [x for x in loc["lines"] if x["check"] == "CHECKED" and x["class"] == "RELEASED"]
    noise = sum((x["own_minus_engine_m2"] for x in checked), Decimal(0))
    return {"released_lines": len(rel), "released_m3": q6(engine_m3),
            "released_engine_face_m2": own_st["released_engine_face_m2"], "released_own_m2": own_st["released_own_m2"],
            "checked": len(checked), "geometry_claim_allowed": loc["geometry_claim_allowed"],
            "own_minus_engine_face_m2": q6(noise),
            "max_abs_panel_diff_m2": q6(max(abs(x["own_minus_engine_m2"]) for x in checked)),
            "zones": [{k: (q6(v) if isinstance(v, Decimal) and k not in ("t_m", "resolution_m2") else
                           (f"{v:f}" if isinstance(v, Decimal) else v)) for k, v in z.items()} for z in zr["zones"]],
            "zone_terms_sum_m3": q6(zr["terms_sum_m3"]), "reference_m3": q6(zr["reference_m3"]),
            "difference_m3": q6(zr["difference_m3"]), "transfers": len(zr["transfers"]), "status": zr["status"],
            "excluded": excl, "unowned_faces_by_class": dict(sorted(by.items())),
            "radial_rings": own_st.get("radial_rings", []), "closure": closure}


def beam_slip():
    ref = J(REFB)
    vals = {int(k): v for k, v in ref["rows_m3"].items()}
    c, t = ref["carry"], ref["total"]
    slip = R.omitted_rows(vals, range(c["range"][0], c["range"][1] + 1), range(t["range"][0], t["range"][1] + 1),
                          c["value"], t["value"])
    t545 = J(T545)
    b1 = [m for m in t545["marks"] if m.get("floor") == "1F" and m.get("mark") == "B1"]
    owned = bool(b1) and set(b1[0]) - {"floor", "mark"} == {"THROUGH_SUPPORT"}
    # the 1F released beam lines are byte-equal V3.0.58 (T-545) -> V3.0.70
    def rel1f(p):
        return {x["line_id"]: x["measured_net"] for x in J(p)["lines"] if x["item_code"] == "STR.CONC.BEAM"
                and ":1F:" in x["element_id"] and x["class"] == "RELEASED"}
    same = rel1f(INDEX_58) == rel1f(INDEX)
    members = {r: {**ref["omitted_row_members"][str(r)], "engine": "OWNED" if (owned and same) else None}
               for r in slip["omitted"]}
    ex = R.explain_slip(slip, members)
    return {"omitted_rows": slip["omitted"], "doubled_rows": slip["extra"], "gap_m3": q6(slip["gap_m3"]),
            "carry": c, "total": t, "members": members, "engine_b1_1f_t545_terms": b1[0] if b1 else None,
            "released_1f_beam_lines_unchanged_since_v3_0_58": same, "explanation": [
                {k: (q6(v) if isinstance(v, Decimal) else v) for k, v in o.items()} for o in ex["rows"]],
            "explained": ex["explained"], "engine_quantity_moved_m3": "0.000000"}


def build():
    own = J(OWN)["storeys"]
    t688 = J(T688)["slab_1f"]
    if Decimal(t688["own_m2"]) != Decimal(str(own["1F"]["released_own_m2"])):
        raise SystemExit("T-706: the 1F own re-measure differs from T-688's")
    st = {s: storey_statement(s, own[s]) for s in ("GF", "1F", "2F")}
    released = sum(Decimal(str(x["measured_net"])) for x in slab_lines() if x["class"] == "RELEASED")
    key = KEY_REF_M3 - released
    terms = sum(Decimal(st[s]["difference_m3"]) for s in st)
    if terms != key:
        raise SystemExit(f"T-706: storey terms {terms} != key residual {key}")
    causes = {
        "GF": {"term_m3": st["GF"]["difference_m3"], "cause": "REFERENCE ROUNDING: his typed 207 m2 is read at +-0.5 m2"
               " (+-0.080 m3); engine net 206.684513 m2 lies 0.315488 m2 below it, inside the band; own re-measure"
               " 33 / 33 panels CHECKED", "status": "CLOSED_WITHIN_REFERENCE_RESOLUTION", "verdict": "ENGINE_RIGHT"},
        "1F": {"term_m3": st["1F"]["difference_m3"], "cause": "T-688 (merged): rounding -0.080 .. +0.080 + scope "
               + "-0.636333 .. -0.476333 (2.977 .. 3.977 m2 of drawn panels not in his 120; 62 subsets fit, none named)",
               "status": "UNRESOLVED_AMBIGUOUS (reference composition)", "verdict": "ENGINE_RIGHT on geometry"},
        "2F": {"term_m3": st["2F"]["difference_m3"], "cause": "THICKNESS ZONES: 0.16 zone +0.59 m2 x 0.16 = +0.094400;"
               " 0.18 zone -0.285 m2 x 0.18 = -0.051300; 'T 18' printed inside exactly the two 0.18 panels; no whole-"
               "panel subset or zone transfer fits either typed figure", "status": "NOT_WHOLE_PANELS (reference "
               "dimensions; residual named)", "verdict": "ENGINE_RIGHT on geometry and zones"}}
    return {"schema": "URBAN_T706_STATEMENT_V1", "rules": [R.R1, R.R2, R.R3], "candidate": "ARCH_TAKEOFF_V3.0.70",
            "key": "CONC.SLAB", "reference_m3": q6(KEY_REF_M3), "engine_released_m3": q6(released),
            "key_residual_m3": q6(key), "key_residual_pct": f"{(key / KEY_REF_M3 * 100).quantize(Decimal('0.01'))}",
            "storey_terms_sum_m3": q6(terms), "storeys": st, "causes": causes, "beam_slip": beam_slip(),
            "member_sections_m": list(MEMBER_SECTIONS)}


def md(s):
    L = ["# T-706 statement (generated by t706_alsenan.py; numbers only)", "",
         f"Candidate {s['candidate']}; key {s['key']}: reference {s['reference_m3']} - engine released "
         f"{s['engine_released_m3']} = **{s['key_residual_m3']} m3 ({s['key_residual_pct']} %)**; storey terms re-add to "
         f"{s['storey_terms_sum_m3']}.", "",
         "| Storey | Released lines | Engine m3 | Own vs engine (m2, sum / max panel) | Zone terms m3 (t: ref - engine m2) "
         "| Term m3 | Status | Excluded | Unowned own faces |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in s["storeys"].items():
        z = "; ".join(f"{x['t_m']}: {x['ref_minus_engine_m2']} m2 -> {x['term_m3']} ({x['status']})" for x in v["zones"])
        ex = ", ".join(f"{e['class']} {e['own_face_m2']}" for e in v["excluded"])
        L.append(f"| {k} | {v['released_lines']} ({v['checked']} CHECKED) | {v['released_m3']} | "
                 f"{v['own_minus_engine_face_m2']} / {v['max_abs_panel_diff_m2']} | {z} | {v['difference_m3']} | "
                 f"{v['status']} | {ex} | {v['unowned_faces_by_class']} closed={v['closure']['closed']} |")
    L += ["", "Causes:"]
    for k, v in s["causes"].items():
        L.append(f"- {k} {v['term_m3']}: {v['cause']}; {v['status']}; {v['verdict']}.")
    b = s["beam_slip"]
    L += ["", f"Beam slip (R-T706-3): carry row {b['carry']['row']} sums rows {b['carry']['range']} = "
          f"{b['carry']['value']}, total row {b['total']['row']} sums rows {b['total']['range']} = {b['total']['value']}; "
          f"omitted rows {b['omitted_rows']} = {b['gap_m3']} m3; members {b['members']}; explained {b['explained']}; "
          f"engine quantity moved {b['engine_quantity_moved_m3']}."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    s = build()
    txt = json.dumps(s, indent=1, ensure_ascii=False, default=str) + "\n"
    if a.write:
        OUT_JSON.write_text(txt, encoding="utf-8")
        OUT_MD.write_text(md(s), encoding="utf-8")
    if a.check:
        if OUT_JSON.read_text(encoding="utf-8") != txt or OUT_MD.read_text(encoding="utf-8") != md(s):
            raise SystemExit("T-706: committed statement differs from a rebuild")
        print("T-706 statement: rebuild identical")
    print(md(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
