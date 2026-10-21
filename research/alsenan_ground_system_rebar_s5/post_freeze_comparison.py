"""S5 POST-FREEZE COMPARISON (comparison layer; never upstream of a quantity).

    python3 -I research/alsenan_ground_system_rebar_s5/post_freeze_comparison.py <CHRISTIANNP_FORENSIC_RERUN dir>

Refuses to run unless S5_FREEZE_MANIFEST.json still matches every frozen code / input / output file. Then compares the
frozen S5 ground-beam and strap-beam rebar, comparable scope only, with:
  * christiannp's frozen rebar evidence (13_rebar/REBAR_EVIDENCE.csv, read-only, hashed);
  * the freelancer QS lineage (FREELANCER_CATEGORY_LINEAGE.json: GB / strap concrete rows, steel lumps only);
  * the U-C4N oracle (MULTI_ENGINE_REBAR_COMPARISON.json: one incomplete project total);
  * the old Urban registers (R4 GROUND_BEAM_REBAR_V4 per span; R3 BEAM_REBAR_REGISTER_V3 straps; the multi-engine
    GROUND_BEAMS_AND_GROUND_SLAB row).
Every difference gets one class from CLASSES. The S5 outputs are never modified and nothing is tuned: a correction
found here needs a new issue, new source evidence, a new regression and a new version.
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
CLASSES = ("SCOPE_DIFFERENCE", "DEVELOPMENT_MISSING", "HOOK_MISSING", "STIRRUP_GEOMETRY_MISSING",
           "DETAIL_APPLICABILITY_DIFFERENCE", "BAR_RUN_CONVENTION", "SECTION_CONFLICT", "OCCURRENCE_DIFFERENCE",
           "ASSUMED_COMPONENT", "UNKNOWN", "SAME")
LINEAGE = ROOT / "research/alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
ORACLES = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_REBAR_COMPARISON.json"
R4_GB = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/GROUND_BEAM_REBAR_V4.json"
R3_BEAM = ROOT / "research/alsenan_rebar_truth_03/registers/BEAM_REBAR_REGISTER_V3.json"
OLD_ROLE = {"TOP": "TOP_MAIN", "LOWER_1": "BOTTOM_ROW_1", "LOWER_2": "BOTTOM_ROW_2", "STIRRUPS": "STIRRUPS",
            "SIDE_BARS": "SIDE_REBAR", "BOTTOM": "BOTTOM_MAIN"}
STRAP_MARK = {"SB1": "SOCC-1689-1B1C", "SB2": "SOCC-1B08-1B09", "SB3": "SOCC-1B26-1B27"}
FREELANCER_STRAP = {"STB1": "SB1", "STB2": "SB2", "STB3": "SB3"}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def verify_freeze():
    m = _j(HERE / "S5_FREEZE_MANIFEST.json")
    bad = [k for g, base in (("code", ROOT), ("inputs", ROOT), ("outputs", HERE)) for k, h in m[g].items()
           if _sha(base / k) != h]
    if bad or m["state"] != "FROZEN_BEFORE_REFERENCE_COMPARISON":
        raise SystemExit(f"S5 freeze broken - refusing to compare: {bad}")
    return m


def s5():
    occ = {r["occurrence_id"]: r for r in _rows(HERE / "GROUND_SYSTEM_REBAR_OCCURRENCES.csv")}
    comps = defaultdict(dict)
    for c in _rows(HERE / "GROUND_SYSTEM_REBAR_COMPONENTS.csv"):
        comps[c["occurrence_id"]][c["component"]] = c
    return occ, comps


def _f(v):
    return float(v) if v not in ("", None) else 0.0


# ------------------------------------------------------------------------------------------------ references
def chris(chris_dir):
    p = Path(chris_dir) / "13_rebar" / "REBAR_EVIDENCE.csv"
    rows = _rows(p)
    gb = [r for r in rows if r["COMPONENT"] == "GROUND_BEAM_REBAR"]
    straps = [r for r in rows if re.match(r"^S\.?T?B\d", r["MEMBER_MARK"].upper()) or "STRAP" in r["COMPONENT"]]
    return {"gb_rows": gb, "strap_rows": straps}, {"file": str(p.relative_to(Path(chris_dir).parent)),
                                                   "sha256": _sha(p)}


def freelancer():
    lin = _j(LINEAGE)
    cats = {c["category_id"]: c for c in lin["categories"]}
    gbc, fnd = cats["GROUND_BEAMS_AND_GROUND_SLAB"], cats["FOUNDATIONS_RELATED"]
    gb_rows = [s for s in gbc["subcomponents"] if s["physical_kind"] == "GROUND_BEAM"]
    straps = {FREELANCER_STRAP[s["label"]]: s for s in fnd["subcomponents"] if s["physical_kind"] == "STRAP_BEAM"}
    perim = [s for s in fnd["subcomponents"] if s["physical_kind"] == "PERIMETER_GROUND_BEAM"]
    boundary = [s for s in gbc["subcomponents"] if s["physical_kind"] == "BOUNDARY_GROUND_BEAM"]
    return {"gb_rows": gb_rows, "straps": straps, "perimeter": perim, "boundary": boundary,
            "gb_slab_steel_t": gbc["steel_value_t"], "foundations_steel_t": fnd["steel_value_t"]}, _sha(LINEAGE)


def uc4n():
    d = _j(ORACLES)
    row = next(r for r in d["rows"] if r["category"] == "GROUND_BEAMS_AND_GROUND_SLAB")
    return next(o for o in d["oracle_net_rebar"] if o["oracle"] == "UC4N"), row, _sha(ORACLES)


def _hexset(band):
    out = set()
    for t in band.replace("ARC:", "").split("+"):
        t = t.strip()
        out.add(format(int(t[1:]), "X") if t.startswith("H") and t[1:].isdigit() else t)
    return frozenset(out)


def old_urban(occ):
    """Old Urban R4 spans mapped onto S5 spans: by band handle set (old handles are decimal), then by nearest length
    inside a band. An old band that is a subset of a new one (multi-partner pairing) maps onto it."""
    g = _j(R4_GB)
    new_bands = defaultdict(list)
    for oid, o in occ.items():
        if o["family"] == "GROUND_BEAM":
            new_bands[frozenset(h.replace("ARC:", "") for h in json.loads(o["geometry_handles"]))].append(oid)
    old_bands = defaultdict(list)
    for o in g["occurrences"]:
        old_bands[_hexset(o["band"])].append(o)
    mapping, unmatched = {}, []
    for ob, olds in old_bands.items():
        nb = ob if ob in new_bands else next((k for k in new_bands if ob <= k), None)
        if nb is None:
            unmatched += [o["span"] for o in olds]
            continue
        free = list(new_bands[nb])
        for o in sorted(olds, key=lambda z: z["length_m"]):
            best = min(free, key=lambda oid: min(abs(_f(occ[oid][k]) - o["length_m"]) for k in (
                "member_clear_concrete_length_m", "support_face_to_face_run_m", "member_centerline_length_m")))
            free.remove(best)
            mapping[best] = dict(o, band_change="SAME_BAND" if nb == ob else f"OLD_BAND_SUBSET {sorted(ob)} -> "
                                                                              f"{sorted(nb)}")
    straps = {}
    for r in _j(R3_BEAM)["rows"]:
        if r["element_type"] == "STRAP_BEAM":
            straps[STRAP_MARK[r["occurrence"].split(":")[1]]] = r
    return mapping, unmatched, straps, {"R4_GB": _sha(R4_GB), "R3_BEAM": _sha(R3_BEAM)}


# ---------------------------------------------------------------------------------------------- classification
def _why_blocked(c):
    w = c["why"]
    if "bar straight run not established" in w:
        return "BAR_RUN_CONVENTION", "S5 bar run withheld (length geometry conflict); old Urban used its span length"
    if "SBT:" in w or "SBT:" in c.get("candidate_values", ""):
        return "SECTION_CONFLICT", "SB2 duplicated schedule key: S5 chooses no row"
    if "no project definition" in w:
        return "DETAIL_APPLICABILITY_DIFFERENCE", ("concentrated load not excluded: S5 keeps the 'without concentrated "
                                                   "load' detail blocked; old Urban applied it")
    if "disagree" in w or "applicability" in w:
        return "DETAIL_APPLICABILITY_DIFFERENCE", "candidate details differ: S5 chooses none; old Urban picked a primary"
    return "UNKNOWN", w[:120]


def classify_long(c, old_c, old_len, band_change=None):
    """One longitudinal component, S5 vs old Urban."""
    s_kg = _f(c["kg"])
    o_ver = old_c["verified_kg"] if old_c else 0.0
    o_pro = old_c["provisional_kg"] if old_c else 0.0
    if c["state"] == "NOT_APPLICABLE" and not (o_ver or o_pro):
        return "SAME", "not applicable on either side", None
    if c["state"] == "BLOCKED_UNQUANTIFIED":
        if not (o_ver or o_pro):
            return "SAME", "unquantified on both sides", None
        cls, why = _why_blocked(c)
        return cls, why, None
    if old_c is None or not (o_ver or o_pro):
        return "DETAIL_APPLICABILITY_DIFFERENCE", "old Urban booked no kg for this component", None
    o_kg = o_ver + o_pro
    if (int(c["bar_count"]), int(c["dia_mm"])) != (old_c["count"], old_c["dia_mm"]):
        return "DETAIL_APPLICABILITY_DIFFERENCE", (f"bars S5 {c['bar_count']}Ø{c['dia_mm']} / old "
                                                   f"{old_c['count']}Ø{old_c['dia_mm']} (old primary detail)"), None
    remeasured = int(c["bar_count"]) * old_len * _f(c["kg_per_m"])
    if abs(o_kg - s_kg) <= 0.01:
        return "SAME", ("same kg; old Urban held it PROVISIONAL (ambiguous governing detail), S5 releases it as a "
                        "LOWER_BOUND only because the bars are identical in every candidate") if o_pro and not o_ver \
            else "", remeasured
    if band_change and band_change != "SAME_BAND":
        return "OCCURRENCE_DIFFERENCE", (f"PRE-S5 network rebuild changed the member ({band_change}); old length "
                                         f"{old_len:.3f} m vs S5 {_f(c['straight_run_m']):.3f} m"), remeasured
    if abs(remeasured - o_kg) <= max(0.02, 0.0005 * o_kg):
        return "BAR_RUN_CONVENTION", (f"same bars; old length {old_len:.3f} m vs S5 BAR_STRAIGHT_RUN_LOWER_BOUND "
                                      f"{_f(c['straight_run_m']):.3f} m"), remeasured
    return "UNKNOWN", f"not explained by the length basis (re-measured {remeasured:.2f})", remeasured


def main(chris_dir):
    manifest = verify_freeze()
    OUT.mkdir(exist_ok=True)
    occ, comps = s5()
    ch, ch_src = chris(chris_dir)
    fl, fl_sha = freelancer()
    uc, uc_row, uc_sha = uc4n()
    om, om_unmatched, ostraps, ou_src = old_urban(occ)
    comp_rows, occ_rows = [], []
    for oid in sorted(occ):
        o = occ[oid]
        cs = comps[oid]
        fam = o["family"]
        if fam == "GROUND_BEAM":
            old = om.get(oid)
            old_len = old["length_m"] if old else None
            old_c = {OLD_ROLE[x["role"]]: x for x in (old["components"] if old else [])}
        else:
            old = ostraps.get(oid)
            old_c = {OLD_ROLE[x["role"]]: x for x in (old["components"] if old else []) if x["role"] in OLD_ROLE}
            old_len = next((x["verified_length_m"] for x in (old["components"] if old else [])
                            if x["role"] == "TOP"), None)
        long_c = ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2") if fam == "GROUND_BEAM" else ("TOP_MAIN", "BOTTOM_MAIN")
        for k in long_c:
            c = cs[k]
            oc = old_c.get(k if fam == "GROUND_BEAM" else ("TOP_MAIN" if k == "TOP_MAIN" else "BOTTOM_MAIN"))
            if fam == "STRAP_BEAM" and old and old["occurrence_state"] == "BLOCKED":
                oc = None
            cls, why, rem = classify_long(c, oc, old_len or 0.0, (old or {}).get("band_change"))
            comp_rows.append({"OCCURRENCE_ID": oid, "FAMILY": fam, "COMPONENT": k, "S5_STATE": c["state"],
                              "S5_KG": _f(c["kg"]), "S5_RUN_M": _f(c["straight_run_m"]),
                              "OLD_URBAN_SPAN": (old or {}).get("span", (old or {}).get("occurrence", "")),
                              "OLD_URBAN_LENGTH_M": old_len if old_len is not None else "",
                              "OLD_URBAN_VERIFIED_KG": oc["verified_kg"] if oc else 0.0,
                              "OLD_URBAN_PROVISIONAL_KG": oc["provisional_kg"] if oc else 0.0,
                              "S5_REMEASURED_AT_OLD_LENGTH_KG": "" if rem is None else rem,
                              "OLD_URBAN_CLASS": cls, "OLD_URBAN_WHY": why})
        # stirrups: S5 count only; old Urban booked link mass
        st = old_c.get("STIRRUPS")
        cnt = cs["STIRRUP_COUNT"]
        if st:
            for part, kg_, cls, why in (
                    ("STIRRUP_CORE_PATH", st["verified_kg"], "STIRRUP_GEOMETRY_MISSING",
                     "old Urban priced the link path (assumed perimeter / legs); S5 keeps the mass blocked (Q6)"),
                    ("STIRRUP_HOOK_1+2", st["provisional_kg"], "HOOK_MISSING",
                     "old Urban added a provisional hook / perimeter allowance; S5 has no hook source (Q6)")):
                comp_rows.append({"OCCURRENCE_ID": oid, "FAMILY": fam, "COMPONENT": part,
                                  "S5_STATE": cs["STIRRUP_CORE_PATH"]["state"], "S5_KG": 0.0, "S5_RUN_M": "",
                                  "OLD_URBAN_SPAN": (old or {}).get("span", (old or {}).get("occurrence", "")),
                                  "OLD_URBAN_LENGTH_M": old_len, "OLD_URBAN_VERIFIED_KG": kg_ if part ==
                                  "STIRRUP_CORE_PATH" else 0.0,
                                  "OLD_URBAN_PROVISIONAL_KG": kg_ if part != "STIRRUP_CORE_PATH" else 0.0,
                                  "S5_REMEASURED_AT_OLD_LENGTH_KG": "",
                                  "OLD_URBAN_CLASS": cls if kg_ else "SAME",
                                  "OLD_URBAN_WHY": (why + f"; counts S5 {cnt['count'] or cnt['state']} / old "
                                                    f"{st['count']}") if kg_ else "no kg on either side"})
        sb = old_c.get("SIDE_REBAR")
        if sb and (sb["verified_kg"] or sb["provisional_kg"]):
            comp_rows.append({"OCCURRENCE_ID": oid, "FAMILY": fam, "COMPONENT": "SIDE_REBAR",
                              "S5_STATE": cs.get("SIDE_REBAR", {}).get("state", "NOT_APPLICABLE"), "S5_KG": 0.0,
                              "S5_RUN_M": "", "OLD_URBAN_SPAN": old.get("span", ""), "OLD_URBAN_LENGTH_M": old_len,
                              "OLD_URBAN_VERIFIED_KG": sb["verified_kg"], "OLD_URBAN_PROVISIONAL_KG": sb["provisional_kg"],
                              "S5_REMEASURED_AT_OLD_LENGTH_KG": "", "OLD_URBAN_CLASS": "ASSUMED_COMPONENT",
                              "OLD_URBAN_WHY": "old Urban assumed a FOLLOW ARCH. depth for 2Ø12/30cm side bars; S5 "
                                               "keeps them blocked until the depth is source-established (Q2)"})
        for k in [k for k in cs if k.startswith("DEVELOPMENT_")]:
            comp_rows.append({"OCCURRENCE_ID": oid, "FAMILY": fam, "COMPONENT": k, "S5_STATE": cs[k]["state"],
                              "S5_KG": 0.0, "S5_RUN_M": "", "OLD_URBAN_SPAN": (old or {}).get("span", ""),
                              "OLD_URBAN_LENGTH_M": old_len if old_len is not None else "",
                              "OLD_URBAN_VERIFIED_KG": 0.0, "OLD_URBAN_PROVISIONAL_KG": 0.0,
                              "S5_REMEASURED_AT_OLD_LENGTH_KG": "", "OLD_URBAN_CLASS": "DEVELOPMENT_MISSING",
                              "OLD_URBAN_WHY": "development / anchorage unquantified on both sides (Q7)"})
        # occurrence row + the reference-level classes
        old_kg_v = sum(x["verified_kg"] for x in (old["components"] if old else []))
        old_kg_p = sum(x["provisional_kg"] for x in (old["components"] if old else []))
        if fam == "STRAP_BEAM":
            mk = o["mark"]
            fs = fl["straps"].get(mk)
            f_len = fs["D"] if fs else None
            f_cls = ("SAME" if f_len is not None and abs(f_len - _f(o["bar_straight_run_lower_bound_m"])) <= 0.01
                     else "BAR_RUN_CONVENTION")
            f_why = (f"freelancer {fs['label']} {fs['B']}x{fs['C']} m x {f_len} m concrete; S5 bar run "
                     f"{o['bar_straight_run_lower_bound_m']} m" + ("; freelancer used the 100 cm row (S5 chooses "
                                                                   "none: SECTION_CONFLICT)" if mk == "SB2" else ""))
            if mk == "SB2":
                f_cls = "SECTION_CONFLICT"
        else:
            f_cls, f_why = "SCOPE_DIFFERENCE", "freelancer measures ground beams as two length lumps (no span rows)"
        occ_rows.append({"OCCURRENCE_ID": oid, "FAMILY": fam, "MARK": o["mark"], "S5_STATE": o["occurrence_state"],
                         "S5_KNOWN_KG": _f(o["known_kg"]), "S5_BAR_RUN_M": o["bar_straight_run_lower_bound_m"],
                         "S5_DETAILS": o["detail_ids"], "S5_APPLICABILITY": o["detail_applicability_state"],
                         "OLD_URBAN_SPAN": (old or {}).get("span", (old or {}).get("occurrence", "")),
                         "OLD_URBAN_BAND_CHANGE": (old or {}).get("band_change", ""),
                         "OLD_URBAN_PRIMARY_DETAIL": (old or {}).get("primary_detail", ""),
                         "OLD_URBAN_RELEASE": (old or {}).get("release_state", ""),
                         "OLD_URBAN_VERIFIED_KG": old_kg_v, "OLD_URBAN_PROVISIONAL_KG": old_kg_p,
                         "OLD_URBAN_OCCURRENCE_CLASS": "SAME" if old else "OCCURRENCE_DIFFERENCE",
                         "CHRIS_CLASS": "SCOPE_DIFFERENCE",
                         "CHRIS_WHY": ("christiannp EXCLUDED GROUND_BEAM_REBAR ('no GB schedule/section anywhere'); "
                                       "S5 reads the p.13 typical sections" if fam == "GROUND_BEAM" else
                                       "christiannp has no strap-beam row"),
                         "FREELANCER_CLASS": f_cls, "FREELANCER_WHY": f_why})
    # totals and decomposition
    by_cls = defaultdict(lambda: {"rows": 0, "s5_kg": 0.0, "old_verified_kg": 0.0, "old_provisional_kg": 0.0})
    for r in comp_rows:
        if r["FAMILY"] != "GROUND_BEAM":
            continue
        b = by_cls[r["OLD_URBAN_CLASS"]]
        b["rows"] += 1
        b["s5_kg"] += r["S5_KG"]
        b["old_verified_kg"] += r["OLD_URBAN_VERIFIED_KG"]
        b["old_provisional_kg"] += r["OLD_URBAN_PROVISIONAL_KG"]
    gb_s5 = sum(r["S5_KNOWN_KG"] for r in occ_rows if r["FAMILY"] == "GROUND_BEAM")
    sb_s5 = sum(r["S5_KNOWN_KG"] for r in occ_rows if r["FAMILY"] == "STRAP_BEAM")
    gb_old_v = sum(r["OLD_URBAN_VERIFIED_KG"] for r in occ_rows if r["FAMILY"] == "GROUND_BEAM")
    gb_old_p = sum(r["OLD_URBAN_PROVISIONAL_KG"] for r in occ_rows if r["FAMILY"] == "GROUND_BEAM")
    long_old = sum(r["OLD_URBAN_VERIFIED_KG"] for r in comp_rows if r["FAMILY"] == "GROUND_BEAM"
                   and r["COMPONENT"] in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2"))
    fl_gb_len = sum(s["C"] for s in fl["gb_rows"])
    s5_cl = sum(_f(o["member_centerline_length_m"]) for o in occ.values() if o["family"] == "GROUND_BEAM")
    s5_run = sum(_f(o["bar_straight_run_lower_bound_m"]) for o in occ.values() if o["family"] == "GROUND_BEAM")
    totals = {
        "S5_GROUND_BEAM_KNOWN_KG": gb_s5, "S5_STRAP_KNOWN_KG": sb_s5, "S5_TOTAL_KNOWN_KG": gb_s5 + sb_s5,
        "OLD_URBAN_R4_GB_VERIFIED_KG": gb_old_v, "OLD_URBAN_R4_GB_PROVISIONAL_KG": gb_old_p,
        "OLD_URBAN_R4_GB_VERIFIED_LONGITUDINAL_KG": long_old,
        "OLD_URBAN_R4_GB_VERIFIED_STIRRUP_KG": gb_old_v - long_old,
        "OLD_URBAN_GB_MINUS_S5_LONGITUDINAL_KG": long_old - gb_s5,
        "OLD_URBAN_GB_DECOMPOSITION_BY_CLASS": {k: dict(v) for k, v in sorted(by_cls.items())},
        "OLD_URBAN_STRAPS": {mk: {"old_verified_kg": sum(x["verified_kg"] for x in r["components"]),
                                  "old_provisional_kg": sum(x["provisional_kg"] for x in r["components"]),
                                  "old_release": r["release_state"]} for mk, r in sorted(ostraps.items())},
        "OLD_URBAN_UNMATCHED_SPANS": om_unmatched,
        "OLD_URBAN_MULTI_ENGINE_GB_AND_SLAB_RELEASED_KG": uc_row["actual_released_kg"],
        "OLD_URBAN_MULTI_ENGINE_CLASS": "SCOPE_DIFFERENCE (ground beams + ground slab in one row)",
        "CHRIS": {"ground_beam_rows": [{k: r[k] for k in ("COMPONENT", "INCLUDED_EXCLUDED", "WHY")}
                                       for r in ch["gb_rows"]], "strap_rows": len(ch["strap_rows"]),
                  "class": "SCOPE_DIFFERENCE (christiannp quantifies no ground-beam or strap steel)"},
        "FREELANCER": {"gb_and_slab_steel_t": fl["gb_slab_steel_t"], "foundations_steel_t": fl["foundations_steel_t"],
                       "gb_concrete_length_m": fl_gb_len, "gb_section_m": sorted({(s["B"], s["D"])
                                                                                 for s in fl["gb_rows"]}),
                       "perimeter_beam_in_foundations": [{"length_m": s["D"], "B": s["B"], "C": s["C"]}
                                                         for s in fl["perimeter"]],
                       "boundary_beam_m": [s["C"] for s in fl["boundary"]],
                       "s5_gb_centreline_m": s5_cl, "s5_gb_bar_run_m": s5_run,
                       "class": "SCOPE_DIFFERENCE (steel only as lumps: GB + ground slab 9.75 t; footings + straps "
                                "+ perimeter beam 5.8 t) - no kg difference or percentage is reported"},
        "UC4N": uc, "UC4N_CLASS": "SCOPE_DIFFERENCE (project net rebar only, KNOWN_INCOMPLETE; no ground-system split)"}
    _csv(OUT / "S5_POST_FREEZE_COMPONENT_COMPARISON.csv", comp_rows)
    _csv(OUT / "S5_POST_FREEZE_OCCURRENCE_COMPARISON.csv", occ_rows)
    summary = {"freeze_manifest_verified": True, "frozen_engine_stamp": manifest["engine_commit_stamp"],
               "references": {"christiannp": ch_src, "old_urban": ou_src, "freelancer_lineage_sha256": fl_sha,
                              "oracles_sha256": uc_sha},
               "classes": list(CLASSES), "totals": totals,
               "class_counts_old_urban_components": dict(sorted(Counter(r["OLD_URBAN_CLASS"]
                                                                        for r in comp_rows).items())),
               "class_counts_freelancer_occurrences": dict(sorted(Counter(r["FREELANCER_CLASS"]
                                                                          for r in occ_rows).items())),
               "class_counts_chris_occurrences": dict(sorted(Counter(r["CHRIS_CLASS"] for r in occ_rows).items())),
               "rule": "comparison only; S5 is not tuned. A correction needs a new issue, new source evidence, a new "
                       "regression and a new version."}
    (OUT / "S5_POST_FREEZE_SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) +
                                                     "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("class_counts_old_urban_components",
                                              "class_counts_freelancer_occurrences")}, indent=1))
    print(json.dumps({k: v for k, v in totals.items() if k not in ("CHRIS", "FREELANCER", "UC4N")}, indent=1,
                     default=str))


def _csv(path, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 3) if isinstance(v, float) else json.dumps(v) if isinstance(v, (list, dict))
                        else v) for k, v in r.items()})
    path.write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
