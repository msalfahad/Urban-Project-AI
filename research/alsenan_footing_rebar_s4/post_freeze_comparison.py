"""S4 POST-FREEZE COMPARISON (comparison layer; never upstream of a quantity).

    python3 -I research/alsenan_footing_rebar_s4/post_freeze_comparison.py <CHRISTIANNP_FORENSIC_RERUN dir>

Refuses to run unless S4_FREEZE_MANIFEST.json still matches every frozen code / input / output file. Then compares
the frozen S4 footing rebar, by footing mark and component, with:
  * christiannp's frozen footing evidence (13_rebar/REBAR_EVIDENCE.csv, read-only, hashed);
  * the freelancer QS reference (FREELANCER_CATEGORY_LINEAGE.json: per-type footing counts + one steel lump);
  * the U-C4N oracle (MULTI_ENGINE_REBAR_COMPARISON.json: one incomplete project total);
  * the old Urban footing registers (R3 FOOTING_REBAR_REGISTER_V3, R4 REBAR_POPULATION_REGISTER_V4).
Every difference gets one class. The S4 outputs are never modified; a correction found here needs a new issue,
new evidence, a new regression and a new version.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "post_freeze"
CLASSES = ("SCOPE_DIFFERENCE", "MISSING_COMPONENT", "ASSUMED_COMPONENT", "BAR_LENGTH_CONVENTION", "COVER_CONVENTION",
           "OCCURRENCE_DIFFERENCE", "SOURCE_CONFLICT", "INCOMPLETE_REFERENCE", "UNKNOWN", "SAME")
COVER_M = 0.07
LINEAGE = ROOT / "research/alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
ORACLES = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_REBAR_COMPARISON.json"
R3 = ROOT / "research/alsenan_rebar_truth_03/registers/FOOTING_REBAR_REGISTER_V3.json"
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/REBAR_POPULATION_REGISTER_V4.json"
COMP = {"FOOTING_BOTTOM_SHORT": "BOTTOM_SHORT", "FOOTING_BOTTOM_LONG": "BOTTOM_LONG",
        "FOOTING_TOP_SHORT": "TOP_SHORT", "FOOTING_TOP_LONG": "TOP_LONG", "FOOTING_BOXED": "BOXED"}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_freeze():
    m = json.loads((HERE / "S4_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
    bad = [k for g, base in (("code", ROOT), ("inputs", ROOT), ("outputs", HERE)) for k, h in m[g].items()
           if _sha(base / k) != h]
    if bad or m["state"] != "FROZEN_BEFORE_ANY_REFERENCE_COMPARISON":
        raise SystemExit(f"S4 freeze broken - refusing to compare: {bad}")
    return m


def s4_by_mark():
    comps = list(csv.DictReader(open(HERE / "FOOTING_REBAR_COMPONENTS.csv", encoding="utf-8")))
    agg = defaultdict(lambda: {"kg": 0.0, "occ": set(), "states": set(), "rows": []})
    for c in comps:
        if c["component"] not in ("BOTTOM_SHORT", "BOTTOM_LONG", "TOP_SHORT", "TOP_LONG", "BOXED",
                                  "OTHER_EXPLICIT_EXTRA"):
            continue
        a = agg[(c["mark"], c["component"])]
        a["occ"].add(c["occurrence_id"])
        a["states"].add(c["state"])
        a["rows"].append(c)
        if c["kg"]:
            a["kg"] += float(c["kg"])
    return agg, comps


def s4_inputs():
    """Per-part calculation inputs from the frozen S4 provenance log (count_value = printed count or bars/m)."""
    out = {}
    for line in (HERE / "FOOTING_REBAR_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["provenance"].get("INPUTS"):
            out[r["part_id"]] = r["provenance"]["INPUTS"]
    return out


def chris(chris_dir):
    p = Path(chris_dir) / "13_rebar" / "REBAR_EVIDENCE.csv"
    rows = [r for r in csv.DictReader(open(p, encoding="utf-8")) if r["ELEMENT"].startswith("FOOT")]
    out = {}
    for r in rows:
        comp = COMP.get(r["COMPONENT"])
        if comp is None:
            continue
        m = re.search(r"x\s*(\d+)\s*occ", r["GEOMETRY_LENGTH"])
        out[(r["MEMBER_MARK"], comp)] = {"kg": float(r["KG"]) if r["KG"] else None, "occ": int(m[1]) if m else None,
                                         "rate": r["COUNT_RATE_SPACING"], "assumption": r["ASSUMPTION"],
                                         "included": r["INCLUDED_EXCLUDED"], "length": r["GEOMETRY_LENGTH"]}
    return out, {"file": str(p.relative_to(Path(chris_dir).parent)), "sha256": _sha(p)}


OLD_ROLE = {"PIT_WALL_BASE_BARS_2D16": "OTHER_EXPLICIT_EXTRA"}


def old_urban():
    r3 = json.loads(R3.read_text(encoding="utf-8"))
    agg = defaultdict(lambda: {"verified": 0.0, "provisional": 0.0, "occ": 0, "states": set()})
    occ = defaultdict(lambda: {"established": 0, "blocked": 0})
    for row in r3["rows"]:
        occ[row["type"]]["established" if row["occurrence_state"] == "ESTABLISHED" else "blocked"] += 1
        if row["occurrence_state"] != "ESTABLISHED":
            continue
        for c in row["components"]:
            role = "BOXED" if c["role"].startswith("BOXED") else OLD_ROLE.get(c["role"], c["role"])
            a = agg[(row["type"], role)]
            a["verified"] += c["verified_kg"]
            a["provisional"] += c["provisional_kg"]
            a["occ"] += 1
            a["states"].add(c["state"])
    r4 = json.loads(R4.read_text(encoding="utf-8"))
    pops = [p for p in r4["populations"] if p["element_type"].startswith("FOOTING")]
    r4tot = {k: sum(p[k] for p in pops) for k in ("verified_complete_kg", "lower_bound_kg", "provisional_kg",
                                                    "audit_kg")}
    return agg, occ, r4tot, {"R3": _sha(R3), "R4": _sha(R4)}


def freelancer():
    lin = json.loads(LINEAGE.read_text(encoding="utf-8"))
    c = next(x for x in lin["categories"] if x["category_id"] == "FOUNDATIONS_RELATED")
    counts = {s["label"].replace(".", ""): s["count"] for s in c["subcomponents"] if s["physical_kind"] == "FOOTING"}
    other = [{"label": s["label"], "kind": s["physical_kind"]} for s in c["subcomponents"]
             if s["physical_kind"] != "FOOTING"]
    return counts, c["steel_value_t"], other, _sha(LINEAGE)


def uc4n():
    d = json.loads(ORACLES.read_text(encoding="utf-8"))
    return next(o for o in d["oracle_net_rebar"] if o["oracle"] == "UC4N"), _sha(ORACLES)


NONE_STATES = {"NOT_APPLICABLE", "NO_OCCURRENCE"}
CONFLICT_MARK = "F|F10"


def classify_chris(mark, comp, state, s4_kg, s4_occ, c_, full_len, rate_full):
    c_kg = None if c_ is None else c_["kg"]
    if mark == CONFLICT_MARK:
        if state in NONE_STATES:
            return "SAME", "neither candidate (F, F10) has this component"
        if comp == "BOXED":
            return "MISSING_COMPONENT", "BOXED unquantified in both; the outline itself is in source conflict"
        return "SOURCE_CONFLICT", ("S4 blocks the F / F10 outline; christiannp books F x 4 and F10 x 0, so this "
                                   "outline carries no steel there either (0 kg on both sides)")
    if state in NONE_STATES and not c_kg:
        if c_ is not None and c_["occ"] == 0:
            return "SAME", "no occurrence on either side"
        if comp == "BOXED" and c_ is not None:
            return "SAME", "no occurrence on either side"
        return "SAME", "not applicable on either side"
    if comp == "BOXED":
        return "MISSING_COMPONENT", "BOXED unquantified in both (S4 BLOCKED Q-R3-6; christiannp EXCLUDED)"
    if c_ is None:
        if comp == "OTHER_EXPLICIT_EXTRA":
            return "MISSING_COMPONENT", "printed 2\u00d816 label: S4 BLOCKED (S4-Q1); christiannp has no row"
        return "INCOMPLETE_REFERENCE", "no christiannp row"
    if abs(c_kg - s4_kg) <= 0.01:
        return "SAME", ""
    if c_["occ"] is not None and c_["occ"] != s4_occ:
        return "OCCURRENCE_DIFFERENCE", f"occurrences christiannp {c_['occ']} / S4 {s4_occ}"
    if abs(c_kg - full_len) <= max(0.02, 0.0005 * c_kg):
        return "COVER_CONVENTION", "christiannp bar length = full footing dimension (no 2 x 70 mm cover)"
    if abs(c_kg - rate_full) <= max(0.05, 0.0005 * c_kg):
        return "COVER_CONVENTION", (f"cover: {full_len - s4_kg:+.2f} kg (full dimension); count convention: "
                                    f"{rate_full - full_len:+.2f} kg (christiannp count = rate x full perpendicular "
                                    "dimension, fractional bars; S4 = ceil(rate x dimension inside cover))")
    return "UNKNOWN", f"not explained by cover / count convention (S4 re-measured {rate_full:.2f})"


OLD_ONLY = {
    "PERIMETER_CLOSURE_LEGS": ("ASSUMED_COMPONENT", "old Urban R3 booked closure legs (54-56 x 2 x 0.41 m) as "
                               "PROVISIONAL; S4 has no source for them and does not create the component"),
    "LIFT_PIT_WALLS": ("SCOPE_DIFFERENCE", "old Urban kept the pit walls as a blocked FF component; S4 footing "
                       "scope excludes walls (both 0 kg)"),
    "TOP_LAYER_END_DETAIL": ("SAME", "both unquantified: old Urban BLOCKED component; S4 TOP parts LOWER_BOUND "
                             "with END_TREATMENT named missing")}


def classify_old(mark, comp, state, s4_kg, o_):
    if mark == CONFLICT_MARK:
        if state in NONE_STATES:
            return "SAME", "neither candidate (F, F10) has this component"
        return "SOURCE_CONFLICT", ("old Urban kept two BLOCKED tag rows (F#1 = tag 0x10A5, F10#19 = tag 0x168B) "
                                   "for the one outline 1B1B that S4 blocks as a single SOURCE_CONFLICT occurrence "
                                   "(0 kg on both sides)")
    if comp in OLD_ONLY:
        return OLD_ONLY[comp]
    if o_ is None:
        if state in NONE_STATES:
            return "SAME", "not applicable / no occurrence on either side"
        return "INCOMPLETE_REFERENCE", "no old Urban row"
    if comp == "BOXED":
        if mark == "FN":
            return "ASSUMED_COMPONENT", ("old Urban R3 read FN's empty BOXED cell as not required (FN released "
                                         "VERIFIED_COMPLETE); S4 keeps it BLOCKED_UNQUANTIFIED (pre-S4 decision)")
        return "MISSING_COMPONENT", "BOXED unquantified in both (Q-R3-6)"
    if comp == "OTHER_EXPLICIT_EXTRA":
        return "SAME", "2\u00d816 label blocked in both (old: length follows the pit walls; S4: S4-Q1)"
    if abs(o_["verified"] - s4_kg) <= 0.01:
        if o_["provisional"]:
            return "SAME", (f"S4 known = old verified; old provisional +{o_['provisional']:.2f} kg is the +1 edge "
                            "bar, which S4 keeps out of LOW (in BEST only)")
        return "SAME", ""
    return "UNKNOWN", f"old verified {o_['verified']:.2f}"


def _csv(path, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    path.write_text(buf.getvalue(), encoding="utf-8")


def main(chris_dir):
    manifest = verify_freeze()
    OUT.mkdir(exist_ok=True)
    s4, comps = s4_by_mark()
    inputs = s4_inputs()
    ch, ch_src = chris(chris_dir)
    ou, ou_occ, r4tot, ou_src = old_urban()
    fl_counts, fl_steel_t, fl_other, fl_sha = freelancer()
    uc, uc_sha = uc4n()
    rows = []
    keys = sorted(set(s4) | set(ch) | set(ou))
    for mark, comp in keys:
        a = s4.get((mark, comp), {"kg": 0.0, "occ": set(), "states": set(), "rows": []})
        s4_kg = a["kg"]
        state = "|".join(sorted(a["states"])) or "NO_OCCURRENCE"
        # S4 re-measured with christiannp's conventions (diagnostic): full length; count = rate x full perpendicular
        full_len = rate_full = 0.0
        for c in a["rows"]:
            if c["state"] not in ("VERIFIED", "LOWER_BOUND"):
                continue
            inp = inputs[f"{c['occurrence_id']}:{c['component']}"]
            span = inp["raw_span_mm"] / 1000.0
            kgm = inp["kg_per_m"]
            full_len += inp["count_used"] * span * kgm
            if inp["count_mode"] == "BARS_PER_METRE":
                rate_full += inp["count_value"] * inp["distribution_mm"] / 1000.0 * span * kgm
            else:
                rate_full += inp["count_used"] * span * kgm
        c_ = ch.get((mark, comp))
        c_kg = None if c_ is None else c_["kg"]
        o_ = ou.get((mark, comp))
        cls_c, why_c = classify_chris(mark, comp, state, s4_kg, len(a["occ"]), c_, full_len, rate_full)
        cls_o, why_o = classify_old(mark, comp, state, s4_kg, o_)
        rows.append({"MARK": mark, "COMPONENT": comp, "S4_STATE": state, "S4_OCCURRENCES": len(a["occ"]),
                     "S4_KNOWN_KG": s4_kg, "S4_FULL_DIMENSION_KG": full_len,
                     "S4_REMEASURED_REFERENCE_CONVENTION_KG": rate_full,
                     "CHRIS_OCCURRENCES": "" if c_ is None else c_["occ"], "CHRIS_KG": "" if c_kg is None else c_kg,
                     "CHRIS_DIFF_KG": "" if c_kg is None else c_kg - s4_kg, "CHRIS_CLASS": cls_c, "CHRIS_WHY": why_c,
                     "OLD_URBAN_R3_VERIFIED_KG": "" if o_ is None else o_["verified"],
                     "OLD_URBAN_R3_PROVISIONAL_KG": "" if o_ is None else o_["provisional"],
                     "OLD_URBAN_CLASS": cls_o, "OLD_URBAN_WHY": why_o,
                     "FREELANCER_OCCURRENCES": fl_counts.get(mark, "") if comp == "BOTTOM_SHORT" else ""})
    # occurrence-level comparison with the freelancer counts
    s4_occ = defaultdict(int)
    for c in comps:
        if c["component"] == "STARTER_DOWEL_REFERENCE":
            s4_occ[c["mark"]] += 1
    ch_occ = {m: v["occ"] for (m, comp), v in ch.items() if comp == "BOTTOM_SHORT"}
    occ_rows = []
    for m in sorted(set(s4_occ) | set(fl_counts) | set(ch_occ) | set(ou_occ)):
        s_, f = s4_occ.get(m, 0), fl_counts.get(m, 0)
        o = ou_occ.get(m, {"established": 0, "blocked": 0})
        cls = "SAME" if s_ == f else ("SOURCE_CONFLICT" if m in ("F10", CONFLICT_MARK) else "OCCURRENCE_DIFFERENCE")
        why = {"F3": "plan: two outlines, two C3/F3 tags (S4 SOURCE_VERIFIED); the reference counts one (OQ-11)",
               "F10": "the reference resolves the F / F10 outline as F10; S4 keeps the source conflict",
               CONFLICT_MARK: "S4 occurrence in source conflict; the reference books it as F10"}.get(m, "")
        occ_rows.append({"MARK": m, "S4_OCCURRENCES": s_, "FREELANCER_OCCURRENCES": f, "FREELANCER_CLASS": cls,
                         "FREELANCER_WHY": why, "CHRIS_OCCURRENCES": ch_occ.get(m, ""),
                         "OLD_URBAN_ESTABLISHED": o["established"], "OLD_URBAN_BLOCKED": o["blocked"]})
    s4_known = sum(r["S4_KNOWN_KG"] for r in rows)
    prov = [json.loads(line) for line in (HERE / "FOOTING_REBAR_PROVENANCE.jsonl").read_text(encoding="utf-8")
            .splitlines()]
    s4_best = sum(r["provenance"].get("BEST", r["kg"]) or 0.0 for r in prov)
    chris_tot = sum(r["CHRIS_KG"] for r in rows if r["CHRIS_KG"] != "")
    totals = {
        "S4_KNOWN_KG": s4_known,
        "CHRIS_FOOTING_KG": chris_tot,
        "CHRIS_MINUS_S4": chris_tot - s4_known,
        "S4_REMEASURED_WITH_CHRIS_CONVENTIONS_KG": sum(r["S4_REMEASURED_REFERENCE_CONVENTION_KG"] for r in rows
                                                       if r["CHRIS_KG"] != ""),
        "CHRIS_DECOMPOSITION_KG": {
            "cover_convention": sum(r["S4_FULL_DIMENSION_KG"] - r["S4_KNOWN_KG"] for r in rows if r["CHRIS_KG"] != ""),
            "count_convention": sum(r["S4_REMEASURED_REFERENCE_CONVENTION_KG"] - r["S4_FULL_DIMENSION_KG"]
                                    for r in rows if r["CHRIS_KG"] != ""),
            "residual_rounding": chris_tot - sum(r["S4_REMEASURED_REFERENCE_CONVENTION_KG"] for r in rows
                                                 if r["CHRIS_KG"] != "")},
        "OLD_URBAN_R3_VERIFIED_KG": sum(v["verified"] for v in ou.values()),
        "OLD_URBAN_R3_PROVISIONAL_SPLIT_KG": {
            "edge_bar_convention": sum(v["provisional"] for (m, c), v in ou.items() if c != "PERIMETER_CLOSURE_LEGS"),
            "perimeter_closure_legs": sum(v["provisional"] for (m, c), v in ou.items()
                                          if c == "PERIMETER_CLOSURE_LEGS")},
        "S4_BEST_MINUS_KNOWN_KG": s4_best - s4_known,
        "OLD_URBAN_R3_PROVISIONAL_KG": sum(v["provisional"] for v in ou.values()),
        "OLD_URBAN_R4_FOOTING_POPULATIONS": r4tot,
        "FREELANCER_FOUNDATIONS_STEEL_T": fl_steel_t,
        "FREELANCER_SCOPE": ["all footings (per-type counts)"] + [f"{o['kind']} {o['label']}" for o in fl_other],
        "FREELANCER_CLASS": "SCOPE_DIFFERENCE + INCOMPLETE_REFERENCE (one hard-typed lump for footings + straps + "
                            "perimeter beam; no component or diameter split) - no difference or percentage reported",
        "UC4N": uc, "UC4N_CLASS": "INCOMPLETE_REFERENCE (project net rebar only, KNOWN_INCOMPLETE; no footing split)"}
    _csv(OUT / "S4_POST_FREEZE_COMPONENT_COMPARISON.csv", rows)
    _csv(OUT / "S4_POST_FREEZE_OCCURRENCE_COMPARISON.csv", occ_rows)
    summary = {"freeze_manifest_verified": True, "frozen_engine_stamp": manifest["engine_commit_stamp"],
               "references": {"christiannp": ch_src, "old_urban": ou_src, "freelancer_lineage_sha256": fl_sha,
                              "oracles_sha256": uc_sha},
               "totals": totals,
               "class_counts_chris": dict(sorted(Counter(r["CHRIS_CLASS"]
                                                                                   for r in rows).items())),
               "class_counts_old_urban": dict(sorted(Counter(r["OLD_URBAN_CLASS"]
                                                                                        for r in rows).items())),
               "rule": "comparison only; S4 is not tuned. A correction needs a new issue, new source evidence, a new "
                       "regression and a new version."}
    (OUT / "S4_POST_FREEZE_SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n",
                                                     encoding="utf-8")
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1])
