"""S6 POST-FREEZE COMPARISON (comparison layer; never upstream of a quantity).

    python3 -I research/alsenan_superstructure_beam_rebar_s6/post_freeze_comparison.py <CHRISTIANNP_FORENSIC_RERUN dir>

Refuses to run unless S6_FREEZE_MANIFEST.json still matches every frozen code / input / output file. Then compares the
frozen S6 simple-beam and continuous-beam rebar, comparable scope only, with:
  * the old Urban registers (R3 BEAM_REBAR_REGISTER_V3 simple beams per tag; R3 CONTINUOUS_BEAM_BAR_GEOMETRY_REGISTER
    per CB mark; the multi-engine BEAMS row);
  * christiannp's frozen rebar evidence (13_rebar/REBAR_EVIDENCE.csv, read-only, hashed);
  * the freelancer QS lineage (FREELANCER_CATEGORY_LINEAGE.json: BEAMS concrete rows, one steel lump);
  * the U-C4N oracle (MULTI_ENGINE_REBAR_COMPARISON.json: one incomplete project total).
Every difference gets one class from CLASSES. The S6 outputs are never modified and nothing is tuned: a correction
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
CLASSES = ("SCOPE_DIFFERENCE", "OCCURRENCE_DIFFERENCE", "BINDING_DIFFERENCE", "WIDTH_SOURCE_CONFLICT",
           "BAR_RUN_CONVENTION", "DETAIL_APPLICABILITY", "MID_EXTENT", "HANGER_MISSING", "ANCHORAGE_MISSING",
           "HOOK_MISSING", "STIRRUP_GEOMETRY_MISSING", "SIDE_REBAR_SEMANTICS", "ASSUMED_COMPONENT", "UNKNOWN", "SAME")
LINEAGE = ROOT / "research/alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
ORACLES = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_REBAR_COMPARISON.json"
R3_BEAM = ROOT / "research/alsenan_rebar_truth_03/registers/BEAM_REBAR_REGISTER_V3.json"
R3_CB = ROOT / "research/alsenan_rebar_truth_03/registers/CONTINUOUS_BEAM_BAR_GEOMETRY_REGISTER.json"
SHEET_OF_FLOOR = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _f(v):
    return float(v) if v not in ("", None) else 0.0


def kgm(d):
    return d * d / 162.0


def verify_freeze():
    m = _j(HERE / "S6_FREEZE_MANIFEST.json")
    bad = [k for g, base in (("code", ROOT), ("inputs", ROOT), ("outputs", HERE)) for k, h in m[g].items()
           if _sha(base / k) != h]
    if bad or m["state"] != "FROZEN_BEFORE_REFERENCE_COMPARISON":
        raise SystemExit(f"S6 freeze broken - refusing to compare: {bad}")
    return m


def s6():
    occ = {r["occurrence_id"]: r for r in _rows(HERE / "SUPERSTRUCTURE_BEAM_OCCURRENCES.csv")}
    comps = defaultdict(list)
    for c in _rows(HERE / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv"):
        comps[c["occurrence_id"]].append(c)
    runs = defaultdict(list)
    for r in _rows(HERE / "SUPERSTRUCTURE_BEAM_BAR_RUNS.csv"):
        runs[r["occurrence_id"]].append(r)
    return occ, comps, runs


def _one(comps, oid, comp):
    return next(c for c in comps[oid] if c["component"] == comp)


def _blocked_class(o, c):
    """Why S6 holds a component that a reference quantified (from the frozen blocking reason)."""
    why = (c.get("why") or "") + " " + (o.get("occurrence_blocking_reason") or "")
    if "width" in why:
        return "WIDTH_SOURCE_CONFLICT", "drawn band width conflicts with the schedule B: S6 keeps geometry, blocks rebar"
    if "candidate" in why and "binding" in why:
        return "BINDING_DIFFERENCE", "tag binding is a PRE-S6 candidate: S6 releases no steel on it"
    if "two marks" in why:
        return "BINDING_DIFFERENCE", "two marks claim the same span (B3 / CB3): S6 chooses none"
    if "WITH STAIR" in why or "planted column" in why or "undefined candidate" in why:
        return "DETAIL_APPLICABILITY", "an unread candidate detail (p.15 / p.16) may change the SBT bars"
    if "curved" in why or "UNRESOLVED" in why or "straight run" in why:
        return "BAR_RUN_CONVENTION", "S6 withholds the bar run (curved member / free end): the reference used a length"
    if ("span" in why and ("conflict" in why.lower() or "schedule spans" in why)) or "vs schedule" in why:
        return "OCCURRENCE_DIFFERENCE", "CB span sequence conflicts with the schedule: S6 forms no bar run"
    if "reading" in why:
        return "DETAIL_APPLICABILITY", "both CB reading directions match and the bars differ: S6 chooses none"
    return "UNKNOWN", why.strip()[:140]


# --------------------------------------------------------------------------------------------- old Urban (R3)
def old_simple(occ):
    rows = [r for r in _j(R3_BEAM)["rows"] if r["element_type"] == "BEAM"]
    by_tag = {}
    for oid, o in occ.items():
        if o["subfamily"] == "SIMPLE_BEAM":
            by_tag[(o["mark"], oid.rsplit("-", 1)[-1].split(":")[0].upper())] = oid
    mapping, unmatched = {}, []
    for r in rows:
        _, fl, mark, h = r["occurrence"].split(":")
        hexh = format(int(h[1:]), "X") if h.startswith("H") and h[1:].isdigit() else h
        oid = by_tag.get((mark, hexh))
        if oid is None:
            unmatched.append(r["occurrence"])
        else:
            mapping[oid] = r
    return mapping, unmatched


def old_cb():
    return {o["occurrence"].split(":")[2]: o for o in _j(R3_CB)["occurrences"]}


def compare_old_simple(occ, comps, mapping, unmatched):
    out = []
    for oid in sorted(o for o in occ if occ[o]["subfamily"] == "SIMPLE_BEAM"):
        o, old = occ[oid], mapping.get(oid)
        if old is None:
            out.append(dict(_base(oid, o, "ALL"), REF_ID="", REF_VERIFIED_KG=0.0, REF_PROVISIONAL_KG=0.0,
                            CLASS="OCCURRENCE_DIFFERENCE", WHY="occurrence not in the old Urban R3 register (PRE-S6 "
                            "binding / census recovered it)"))
            continue
        oc = {c["role"]: c for c in old["components"]}
        for role, comp in (("BOTTOM", "BOTTOM_MAIN"), ("TOP", "TOP_MAIN")):
            c, x = _one(comps, oid, comp), oc.get(role)
            row = dict(_base(oid, o, comp, c), REF_ID=old["occurrence"],
                       REF_VERIFIED_KG=x["verified_kg"] if x else 0.0, REF_PROVISIONAL_KG=x["provisional_kg"]
                       if x else 0.0, REF_BARS=f"{x['count']}Ø{x['dia_mm']}" if x and x["count"] else "",
                       REF_LENGTH_M=x["verified_length_m"] if x else "")
            if x is None or not x["verified_kg"]:
                cls, why = ("SAME", "unquantified on both sides") if c["state"] != "LOWER_BOUND" else (
                    "OCCURRENCE_DIFFERENCE", "old Urban booked no kg for this occurrence")
            elif c["state"] != "LOWER_BOUND":
                cls, why = _blocked_class(o, c)
            elif (int(c["bar_count"]), int(c["dia_mm"])) != (x["count"], x["dia_mm"]):
                cls, why = "DETAIL_APPLICABILITY", f"bars S6 {c['bar_count']}Ø{c['dia_mm']} vs old {row['REF_BARS']}"
            elif abs(_f(c["kg"]) - x["verified_kg"]) <= 0.01:
                cls, why = "SAME", "same bars and same face-to-face length"
            else:
                rem = int(c["bar_count"]) * x["verified_length_m"] * kgm(int(c["dia_mm"]))
                cls = "BAR_RUN_CONVENTION" if abs(rem - x["verified_kg"]) <= 0.02 else "UNKNOWN"
                why = (f"same bars; old length {x['verified_length_m']:.3f} m vs S6 face to face "
                       f"{_f(c['straight_run_m']):.3f} m")
            out.append(dict(row, CLASS=cls, WHY=why))
            if x and x["provisional_kg"]:
                out.append(dict(_base(oid, o, f"{comp}:END_ALLOWANCE", None), REF_ID=old["occurrence"],
                                REF_VERIFIED_KG=0.0, REF_PROVISIONAL_KG=x["provisional_kg"], REF_BARS=row["REF_BARS"],
                                REF_LENGTH_M=x["provisional_length_m"], CLASS="ANCHORAGE_MISSING",
                                WHY=f"old Urban added a provisional {x['provisional_length_m']} m end allowance; S6 "
                                    "keeps DEVELOPMENT_1/2 blocked (Q1, no 40D / 70D / code default)"))
        st = oc.get("STIRRUPS")
        if st:
            cnt = _one(comps, oid, "STIRRUP_COUNT")
            for part, kg_, cls, why in (
                    ("STIRRUP_CORE_PATH", st["verified_kg"], "STIRRUP_GEOMETRY_MISSING",
                     "old Urban priced an assumed link path; S6 keeps stirrup mass blocked (legs / path / hooks, Q7)"),
                    ("STIRRUP_HOOKS", st["provisional_kg"], "HOOK_MISSING",
                     "old Urban added a provisional hook allowance; S6 has no hook source (Q7)")):
                out.append(dict(_base(oid, o, part, None), REF_ID=old["occurrence"],
                                REF_VERIFIED_KG=kg_ if part == "STIRRUP_CORE_PATH" else 0.0,
                                REF_PROVISIONAL_KG=kg_ if part != "STIRRUP_CORE_PATH" else 0.0,
                                REF_BARS=f"{st['count']} (conv {st['count_convention']}) Ø{st['dia_mm']}",
                                REF_LENGTH_M=st["verified_length_m"], CLASS=cls if kg_ else "SAME",
                                WHY=(why + f"; counts S6 {cnt['count'] or cnt['state']} / old {st['count']}")
                                if kg_ else "no kg on either side"))
        sb = oc.get("SIDE_BARS")
        if sb:
            out.append(dict(_base(oid, o, "SIDE_REBAR", _one(comps, oid, "SIDE_REBAR")), REF_ID=old["occurrence"],
                            REF_VERIFIED_KG=sb["verified_kg"], REF_PROVISIONAL_KG=sb["provisional_kg"], REF_BARS="",
                            REF_LENGTH_M="", CLASS="SIDE_REBAR_SEMANTICS" if (sb["verified_kg"] or sb["provisional_kg"]
                                                                              or sb["state"] == "BLOCKED") else "SAME",
                            WHY=f"old Urban: {sb['state']} ({sb.get('why') or ''}); S6 keeps the text, kg blocked (Q6)"))
    for u in unmatched:
        out.append({"OCCURRENCE_ID": "", "SUBFAMILY": "SIMPLE_BEAM", "MARK": u.split(":")[2], "COMPONENT": "ALL",
                    "S6_STATE": "", "S6_KG": 0.0, "S6_RUN_M": "", "REF_ID": u, "REF_VERIFIED_KG": 0.0,
                    "REF_PROVISIONAL_KG": 0.0, "REF_BARS": "", "REF_LENGTH_M": "", "CLASS": "OCCURRENCE_DIFFERENCE",
                    "WHY": "old Urban row has no S6 occurrence with the same tag"})
    return out


def compare_old_cb(occ, comps, runs, ocb):
    out = []
    for oid in sorted(o for o in occ if occ[o]["subfamily"] == "CONTINUOUS_BEAM"):
        o = occ[oid]
        old = ocb.get(o["mark"])
        if old is None:
            out.append(dict(_base(oid, o, "ALL"), REF_ID="", REF_VERIFIED_KG=0.0, REF_PROVISIONAL_KG=0.0,
                            REF_BARS="", REF_LENGTH_M="", CLASS="OCCURRENCE_DIFFERENCE",
                            WHY="CB occurrence not in the old Urban R3 CB register"))
            continue
        rr = runs[oid]
        used = set()
        for m in old.get("component_matrix") or []:
            name, kind = m["component"], m["component"].split(" ")[0]
            s6c, cls, why = None, "UNKNOWN", ""
            if kind in ("BOTTOM", "SUPPORT_TOP", "CONTINUOUS_TOP", "SPAN_TOP"):
                role = {"BOTTOM": "BOTTOM_MAIN", "SUPPORT_TOP": "MID_TOP"}.get(kind, "TOP_MAIN")
                cand = [r for r in rr if r["BAR_ROLE"] == role and r["BAR_RUN_ID"] not in used and
                        (r["count"], r["dia_mm"]) == (str(m["count"]), str(m["dia_mm"]))]
                s6c = cand[0] if cand else None
                if s6c:
                    used.add(s6c["BAR_RUN_ID"])
                s6kg = _f(s6c["kg"]) if s6c else 0.0
                if s6c is None:
                    cls, why = "OCCURRENCE_DIFFERENCE", f"no S6 {role} run with {m['count']}Ø{m['dia_mm']}"
                elif s6c["state"] != "LOWER_BOUND":
                    if role == "TOP_MAIN":
                        cls, why = "ASSUMED_COMPONENT", ("old Urban priced the frame top bar with an assumed extent "
                                                         "(provisional); S6 keeps CB top bars blocked (Q2 / Q3)")
                    else:
                        cls, why = _blocked_class(o, s6c)
                elif role == "MID_TOP":
                    cls, why = "MID_EXTENT", (f"old Urban held the MID bar PROVISIONAL ({m['provisional_kg']:.2f} kg); "
                                              f"S6 releases 0.22 x Ln (axis to axis) + support = "
                                              f"{_f(s6c['STRAIGHT_LENGTH_M']):.3f} m, {s6kg:.2f} kg")
                elif abs(s6kg - m["verified_kg"]) <= 0.01:
                    cls, why = "SAME", "same bars and length"
                else:
                    cls, why = "BAR_RUN_CONVENTION", (f"old core {m.get('core_m')} m (+ template "
                                                      f"{m.get('template_m')}) vs S6 run "
                                                      f"{_f(s6c['STRAIGHT_LENGTH_M']):.3f} m (clear + support + "
                                                      "bound 7.5 cm)")
                out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": o["mark"],
                            "COMPONENT": f"{role}:{s6c['BAR_RUN_ID'] if s6c else name}",
                            "S6_STATE": s6c["state"] if s6c else "", "S6_KG": s6kg,
                            "S6_RUN_M": _f(s6c["STRAIGHT_LENGTH_M"]) if s6c else "", "REF_ID": f"{old['occurrence']}"
                            f"|{name}", "REF_VERIFIED_KG": m["verified_kg"], "REF_PROVISIONAL_KG": m["provisional_kg"],
                            "REF_BARS": f"{m['count']}Ø{m['dia_mm']}", "REF_LENGTH_M": m.get("core_m"),
                            "CLASS": cls, "WHY": why})
                if m["provisional_kg"] and role == "BOTTOM_MAIN":
                    out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": o["mark"],
                                "COMPONENT": f"{role}:END_ALLOWANCE", "S6_STATE": "BLOCKED_UNQUANTIFIED",
                                "S6_KG": 0.0, "S6_RUN_M": "", "REF_ID": f"{old['occurrence']}|{name}",
                                "REF_VERIFIED_KG": 0.0, "REF_PROVISIONAL_KG": m["provisional_kg"],
                                "REF_BARS": f"{m['count']}Ø{m['dia_mm']}", "REF_LENGTH_M": m.get("template_m"),
                                "CLASS": "ANCHORAGE_MISSING", "WHY": "old Urban template allowance at the end "
                                "support; S6 keeps development / anchorage blocked (Q1)"})
            elif kind == "STIRRUPS":
                k = int(name.split(" ")[1]) if " " in name else 1
                cnt = next((c for c in comps[oid] if c["component"] == "STIRRUP_COUNT" and c["span_index"] == str(k)),
                           None)
                out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": o["mark"],
                            "COMPONENT": f"STIRRUP_CORE_PATH:SPAN{k}", "S6_STATE": "BLOCKED_UNQUANTIFIED",
                            "S6_KG": 0.0, "S6_RUN_M": "", "REF_ID": f"{old['occurrence']}|{name}",
                            "REF_VERIFIED_KG": m["verified_kg"], "REF_PROVISIONAL_KG": m["provisional_kg"],
                            "REF_BARS": f"{m['count']} Ø{m['dia_mm']}", "REF_LENGTH_M": m.get("core_m"),
                            "CLASS": "STIRRUP_GEOMETRY_MISSING" if m["verified_kg"] else "HOOK_MISSING",
                            "WHY": f"old Urban priced an assumed link path / hooks; S6 count "
                                   f"{(cnt or {}).get('count') or (cnt or {}).get('state')} vs old {m['count']}, mass "
                                   "blocked (Q7)"})
            elif kind == "SIDE_BARS":
                out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": o["mark"],
                            "COMPONENT": "SIDE_REBAR", "S6_STATE": _one(comps, oid, "SIDE_REBAR")["state"],
                            "S6_KG": 0.0, "S6_RUN_M": "", "REF_ID": f"{old['occurrence']}|{name}",
                            "REF_VERIFIED_KG": m["verified_kg"], "REF_PROVISIONAL_KG": m["provisional_kg"],
                            "REF_BARS": "", "REF_LENGTH_M": "", "CLASS": "SIDE_REBAR_SEMANTICS",
                            "WHY": "side bars blocked on both sides ('/30cm' semantics, Q6)"})
        out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": o["mark"], "COMPONENT": "HANGER",
                    "S6_STATE": _one(comps, oid, "HANGER")["state"], "S6_KG": 0.0, "S6_RUN_M": "",
                    "REF_ID": old["occurrence"], "REF_VERIFIED_KG": 0.0, "REF_PROVISIONAL_KG": 0.0, "REF_BARS": "",
                    "REF_LENGTH_M": "", "CLASS": "HANGER_MISSING",
                    "WHY": "the typical's unlabelled second top row is quantified on neither side (Q2)"})
        for r in rr:
            if r["BAR_RUN_ID"] not in used and r["state"] == "LOWER_BOUND":
                out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": o["mark"],
                            "COMPONENT": f"{r['BAR_ROLE']}:{r['BAR_RUN_ID']}", "S6_STATE": r["state"],
                            "S6_KG": _f(r["kg"]), "S6_RUN_M": _f(r["STRAIGHT_LENGTH_M"]), "REF_ID": old["occurrence"],
                            "REF_VERIFIED_KG": 0.0, "REF_PROVISIONAL_KG": 0.0, "REF_BARS": "", "REF_LENGTH_M": "",
                            "CLASS": "OCCURRENCE_DIFFERENCE", "WHY": "S6 bar run with no old Urban counterpart"})
    return out


def _base(oid, o, comp, c=None):
    return {"OCCURRENCE_ID": oid, "SUBFAMILY": o["subfamily"], "MARK": o["mark"], "COMPONENT": comp,
            "S6_STATE": c["state"] if c else o["occurrence_state"], "S6_KG": _f(c["kg"]) if c else 0.0,
            "S6_RUN_M": _f(c["straight_run_m"]) if c and c.get("straight_run_m") else "",
            "REF_BARS": "", "REF_LENGTH_M": ""}


# -------------------------------------------------------------------------------------------------- christiannp
def chris(chris_dir):
    p = Path(chris_dir) / "13_rebar" / "REBAR_EVIDENCE.csv"
    rows = [r for r in _rows(p) if r["ELEMENT"] == "BEAM"]
    return rows, {"file": str(p.relative_to(Path(chris_dir).parent)), "sha256": _sha(p)}


def compare_chris(occ, comps, rows):
    """christiannp simple beams mapped onto S6 by mark + sheet, then nearest clear length (assignment without
    replacement). CB rows: christiannp excluded every continuous beam."""
    by_member = defaultdict(dict)
    for r in rows:
        if "@" in r["MEMBER_MARK"]:
            by_member[r["MEMBER_MARK"]][r["COMPONENT"]] = r
    free = defaultdict(list)
    for oid, o in occ.items():
        if o["subfamily"] == "SIMPLE_BEAM":
            free[(o["mark"], o["sheet"])].append(oid)
    out, matched = [], set()
    for mm in sorted(by_member, key=lambda m: (m.split("@")[0], m)):
        rr = by_member[mm]
        mark, sheet = mm.split("@")[0], mm.split("@")[1].split("_")[0]
        L = _f(re.match(r"([\d.]+)", rr["BEAM_BOTTOM"]["GEOMETRY_LENGTH"]).group(1)) if "BEAM_BOTTOM" in rr else 0.0
        cand = free[(mark, sheet)]
        if not cand:
            out.append({"OCCURRENCE_ID": "", "SUBFAMILY": "SIMPLE_BEAM", "MARK": mark, "COMPONENT": "ALL",
                        "S6_STATE": "", "S6_KG": 0.0, "S6_RUN_M": "", "REF_ID": mm,
                        "REF_KG": sum(_f(x["KG"]) for x in rr.values()), "REF_LENGTH_M": L,
                        "CLASS": "OCCURRENCE_DIFFERENCE", "WHY": "no S6 occurrence of this mark left on the sheet"})
            continue

        def geo(oid):
            g = json.loads(occ[oid]["geometry"] or "{}")
            return g.get("clear_face_to_face_m") or 0.0
        oid = min(cand, key=lambda z: abs(geo(z) - L))
        cand.remove(oid)
        matched.add(oid)
        o = occ[oid]
        for comp, ccomp in (("BOTTOM_MAIN", "BEAM_BOTTOM"), ("TOP_MAIN", "BEAM_TOP")):
            c, x = _one(comps, oid, comp), rr.get(ccomp)
            ref = _f(x["KG"]) if x else 0.0
            if c["state"] != "LOWER_BOUND":
                cls, why = _blocked_class(o, c)
            elif x and x["PARSED_VALUE"] != f"{c['bar_count']}Ø{c['dia_mm']}":
                cls, why = "DETAIL_APPLICABILITY", f"bars S6 {c['bar_count']}Ø{c['dia_mm']} vs {x['PARSED_VALUE']}"
            elif abs(_f(c["kg"]) - ref) <= 0.011:
                cls, why = "SAME", "same bars, same clear strip length (christiannp also excludes anchorage)"
            elif L > (json.loads(o["geometry"] or "{}").get("length_cc_m") or 0.0) + 0.05:
                cls, why = "OCCURRENCE_DIFFERENCE", (f"christiannp strip {L:.3f} m is longer than this S6 span's "
                                                     "centreline: the strip covers more than one S6 span (different "
                                                     "member segmentation); S6 runs support face to support face "
                                                     f"{_f(c['straight_run_m']):.3f} m")
            else:
                cls, why = "BAR_RUN_CONVENTION", (f"christiannp strip {L:.3f} m vs S6 support face to face "
                                                  f"{_f(c['straight_run_m']):.3f} m")
            out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "SIMPLE_BEAM", "MARK": mark, "COMPONENT": comp,
                        "S6_STATE": c["state"], "S6_KG": _f(c["kg"]), "S6_RUN_M": _f(c["straight_run_m"]),
                        "REF_ID": mm, "REF_KG": ref, "REF_LENGTH_M": L, "CLASS": cls, "WHY": why})
        st = rr.get("BEAM_STIRRUPS")
        if st:
            cnt = _one(comps, oid, "STIRRUP_COUNT")
            out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "SIMPLE_BEAM", "MARK": mark,
                        "COMPONENT": "STIRRUP_CORE_PATH", "S6_STATE": "BLOCKED_UNQUANTIFIED", "S6_KG": 0.0,
                        "S6_RUN_M": "", "REF_ID": mm, "REF_KG": _f(st["KG"]), "REF_LENGTH_M": st["GEOMETRY_LENGTH"],
                        "CLASS": "STIRRUP_GEOMETRY_MISSING",
                        "WHY": f"christiannp assumed the gross perimeter ({st['ASSUMPTION']}); S6 count "
                               f"{cnt['count'] or cnt['state']}, mass blocked (Q7)"})
    for oid, o in sorted(occ.items()):
        if o["subfamily"] == "SIMPLE_BEAM" and oid not in matched:
            out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "SIMPLE_BEAM", "MARK": o["mark"], "COMPONENT": "ALL",
                        "S6_STATE": o["occurrence_state"], "S6_KG": _f(o["known_kg"]), "S6_RUN_M": "",
                        "REF_ID": "", "REF_KG": 0.0, "REF_LENGTH_M": "", "CLASS": "OCCURRENCE_DIFFERENCE",
                        "WHY": "christiannp bound no strip to this S6 occurrence"})
        if o["subfamily"] == "CONTINUOUS_BEAM":
            out.append({"OCCURRENCE_ID": oid, "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": o["mark"], "COMPONENT": "ALL",
                        "S6_STATE": o["occurrence_state"], "S6_KG": _f(o["known_kg"]), "S6_RUN_M": "", "REF_ID":
                        "(continuous beams CB*, all)", "REF_KG": 0.0, "REF_LENGTH_M": "", "CLASS": "SCOPE_DIFFERENCE",
                        "WHY": "christiannp EXCLUDED every CB component ('T/M-n semantics unprinted; CB instances per "
                               "plan not countable'); S6 excludes T/M as a design load and releases bound CB runs"})
    return out


# ----------------------------------------------------------------------------------------- freelancer / U-C4N
def freelancer(occ):
    lin = _j(LINEAGE)
    cat = next(c for c in lin["categories"] if c["category_id"] == "BEAMS")
    by_label, alias = Counter(), {}
    for s in cat["subcomponents"]:
        if s.get("kind") == "LEAF_ROW":
            m = re.match(r"^[BG]CB(\d+)$", s["label"])
            lab = f"CB{m.group(1)}" if m else s["label"]          # BCBn / GCBn read as CBn (comparison only)
            if m:
                alias[lab] = s["label"]
            by_label[lab] += int(s.get("count") or 1)
    s6_marks = Counter(o["mark"] for o in occ.values() if o["subfamily"] in ("SIMPLE_BEAM", "CONTINUOUS_BEAM"))
    rows = []
    for mark in sorted(set(by_label) | set(s6_marks), key=lambda m: (m[:2], len(m), m)):
        n_f, n_s = by_label.get(mark, 0), s6_marks.get(mark, 0)
        rows.append({"MARK": mark, "FREELANCER_LABEL": alias.get(mark, mark if n_f else ""),
                     "FREELANCER_CONCRETE_PIECES": n_f, "S6_OCCURRENCES": n_s,
                     "CLASS": "SAME" if n_f == n_s else "OCCURRENCE_DIFFERENCE",
                     "WHY": ("concrete pieces per label (row count x count) vs S6 occurrences per mark; freelancer "
                             "steel is one lump" + (f"; label {alias[mark]} read as {mark}" if mark in alias else ""))})
    return rows, {"beams_steel_t": cat.get("steel_value_t"), "beams_concrete_m3": cat.get("quantity"),
                  "class": "SCOPE_DIFFERENCE (BEAMS steel is one lump; no bar, span or component rows - no kg "
                           "difference or percentage is reported)"}, _sha(LINEAGE)


def uc4n():
    d = _j(ORACLES)
    row = next(r for r in d["rows"] if r["category"] == "BEAMS")
    return next(o for o in d["oracle_net_rebar"] if o["oracle"] == "UC4N"), row, _sha(ORACLES)


# ------------------------------------------------------------------------------------------------------- main
def _csv(path, rows):
    buf = io.StringIO()
    fields = list(dict.fromkeys(k for r in rows for k in r))
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 3) if isinstance(v, float) else json.dumps(v) if isinstance(v, (list, dict))
                        else v) for k, v in r.items()})
    path.write_text(buf.getvalue(), encoding="utf-8")


def _decomp(rows, ref_keys):
    by = defaultdict(lambda: {"rows": 0, "s6_kg": 0.0, "ref_verified_kg": 0.0, "ref_provisional_kg": 0.0})
    for r in rows:
        b = by[r["CLASS"]]
        b["rows"] += 1
        b["s6_kg"] += r["S6_KG"]
        b["ref_verified_kg"] += r.get(ref_keys[0], 0.0) or 0.0
        b["ref_provisional_kg"] += (r.get(ref_keys[1], 0.0) or 0.0) if ref_keys[1] else 0.0
    return {k: dict(v) for k, v in sorted(by.items())}


def main(chris_dir):
    manifest = verify_freeze()
    OUT.mkdir(exist_ok=True)
    occ, comps, runs = s6()
    s_map, s_unmatched = old_simple(occ)
    ocb = old_cb()
    old_rows = compare_old_simple(occ, comps, s_map, s_unmatched) + compare_old_cb(occ, comps, runs, ocb)
    ch_rows_src, ch_src = chris(chris_dir)
    ch_rows = compare_chris(occ, comps, ch_rows_src)
    fl_rows, fl, fl_sha = freelancer(occ)
    uc, uc_row, uc_sha = uc4n()
    s6sum = _j(HERE / "SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json")
    old_simple_v = sum(c["verified_kg"] for r in s_map.values() for c in r["components"])
    old_simple_p = sum(c["provisional_kg"] for r in s_map.values() for c in r["components"])
    old_long_v = sum(c["verified_kg"] for r in s_map.values() for c in r["components"] if c["role"] in ("BOTTOM",
                                                                                                         "TOP"))
    old_cb_v = sum(m["verified_kg"] for o in ocb.values() for m in o.get("component_matrix") or [])
    old_cb_p = sum(m["provisional_kg"] for o in ocb.values() for m in o.get("component_matrix") or [])
    old_cb_long_v = sum(m["verified_kg"] for o in ocb.values() for m in o.get("component_matrix") or []
                        if m["component"].split(" ")[0] in ("BOTTOM", "SUPPORT_TOP", "CONTINUOUS_TOP", "SPAN_TOP"))
    ch_long = sum(_f(r["KG"]) for r in ch_rows_src if r["COMPONENT"] in ("BEAM_BOTTOM", "BEAM_TOP"))
    ch_st = sum(_f(r["KG"]) for r in ch_rows_src if r["COMPONENT"] == "BEAM_STIRRUPS")
    matched_long = [r for r in ch_rows if r["COMPONENT"] in ("BOTTOM_MAIN", "TOP_MAIN")]
    totals = {
        "S6_SIMPLE_KNOWN_KG": s6sum["SIMPLE_BEAM_LOWER_BOUND_KNOWN_KG"],
        "S6_CB_KNOWN_KG": s6sum["CONTINUOUS_BEAM_LOWER_BOUND_KNOWN_KG"], "S6_MID_KNOWN_KG": s6sum["MID_KNOWN_KG"],
        "S6_TOTAL_KNOWN_KG": s6sum["known_source_derived_superstructure_beam_rebar_kg"],
        "OLD_URBAN_SIMPLE_MATCHED_ROWS": len(s_map), "OLD_URBAN_SIMPLE_UNMATCHED_ROWS": s_unmatched,
        "OLD_URBAN_SIMPLE_VERIFIED_KG": old_simple_v, "OLD_URBAN_SIMPLE_PROVISIONAL_KG": old_simple_p,
        "OLD_URBAN_SIMPLE_VERIFIED_LONGITUDINAL_KG": old_long_v,
        "OLD_URBAN_SIMPLE_VERIFIED_STIRRUP_KG": old_simple_v - old_long_v,
        "OLD_URBAN_CB_OCCURRENCES": sorted(ocb), "OLD_URBAN_CB_VERIFIED_KG": old_cb_v,
        "OLD_URBAN_CB_PROVISIONAL_KG": old_cb_p, "OLD_URBAN_CB_VERIFIED_LONGITUDINAL_KG": old_cb_long_v,
        "OLD_URBAN_MULTI_ENGINE_BEAMS_RELEASED_KG": uc_row["actual_released_kg"],
        "OLD_URBAN_DECOMPOSITION_BY_CLASS": _decomp(old_rows, ("REF_VERIFIED_KG", "REF_PROVISIONAL_KG")),
        "CHRIS": {"beam_longitudinal_kg": ch_long, "beam_stirrup_kg": ch_st,
                  "simple_members": len({r["MEMBER_MARK"] for r in ch_rows_src if "@" in r["MEMBER_MARK"]}),
                  "cb": "EXCLUDED (UNRESOLVED_COMPONENT)",
                  "matched_longitudinal_s6_kg": sum(r["S6_KG"] for r in matched_long),
                  "matched_longitudinal_chris_kg": sum(r["REF_KG"] for r in matched_long),
                  "decomposition_by_class": _decomp([dict(r, REF_VERIFIED_KG=r["REF_KG"]) for r in ch_rows],
                                                    ("REF_VERIFIED_KG", None))},
        "FREELANCER": fl, "UC4N": uc, "UC4N_CLASS": "SCOPE_DIFFERENCE (project net rebar only, KNOWN_INCOMPLETE; "
                                                    "no beam split)",
        "ROUGH_150_KG_M3": {"value_kg": uc_row["rough_reference_kg_released"],
                            "class": "SCOPE_DIFFERENCE (estimating sanity only; never an accurate input)"}}
    _csv(OUT / "S6_POST_FREEZE_OLD_URBAN_COMPARISON.csv", old_rows)
    _csv(OUT / "S6_POST_FREEZE_CHRIS_COMPARISON.csv", ch_rows)
    _csv(OUT / "S6_POST_FREEZE_FREELANCER_OCCURRENCES.csv", fl_rows)
    summary = {"freeze_manifest_verified": True, "frozen_engine_stamp": manifest["engine_commit_stamp"],
               "references": {"christiannp": ch_src, "old_urban": {"R3_BEAM": _sha(R3_BEAM), "R3_CB": _sha(R3_CB)},
                              "freelancer_lineage_sha256": fl_sha, "oracles_sha256": uc_sha},
               "classes": list(CLASSES), "totals": totals,
               "class_counts_old_urban": dict(sorted(Counter(r["CLASS"] for r in old_rows).items())),
               "class_counts_christiannp": dict(sorted(Counter(r["CLASS"] for r in ch_rows).items())),
               "class_counts_freelancer_occurrences": dict(sorted(Counter(r["CLASS"] for r in fl_rows).items())),
               "unknown_rows": [r for r in old_rows + ch_rows if r["CLASS"] == "UNKNOWN"],
               "rule": "comparison only; S6 is not tuned. A correction needs a new issue, new source evidence, a new "
                       "regression and a new version."}
    (OUT / "S6_POST_FREEZE_SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) +
                                                     "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("class_counts_old_urban", "class_counts_christiannp",
                                              "class_counts_freelancer_occurrences")}, indent=1))
    print(json.dumps({k: v for k, v in totals.items() if k not in ("FREELANCER", "UC4N", "OLD_URBAN_DECOMPOSITION_BY_"
                                                                   "CLASS")}, indent=1, default=str)[:4000])


if __name__ == "__main__":
    main(sys.argv[1])
