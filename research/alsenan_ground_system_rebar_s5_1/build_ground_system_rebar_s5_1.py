"""ALSENAN S5.1 - ground-beam + strap-beam rebar DELTA release over the frozen S5 baseline.

    python3 -I research/alsenan_ground_system_rebar_s5_1/build_ground_system_rebar_s5_1.py

S5 stays frozen (manifest hash-checked first; the S4.1 and S6.1 freezes must precede this round); no S5 file is
written. Every change is a delta record (engine.source.delta_release) with its graphic class
(engine.source.graphic_evidence); link lengths come from engine.source.link_geometry.

Released (LOWER_BOUND, envelope only):
  * GB links: the p.13 sections each draw one closed 2-leg link. Where width, depth, cover (70 mm soil, note 22),
    diameter, rate and count are all source-known, CORE_PATH = 2(b-2c-d) + 2(h-2c-d) x count. Hook extension and
    bend arc stay blocked. The <2.5 m link (no label) and the FOLLOW ARCH depth keep their spans blocked.
  * SB1 / SB3: STR2 topology (4 legs); outer-link core path only, inner link blocked.
  * Through-support runs: where two spans of the same drawn GB band meet at a column and both carry identical
    released bars, the bars run through the support as one BAR_RUN (p.13: GB bars unbroken through the column).
    The portion inside the column is released at its lower bound (the column's smaller schedule side), and
    development / hook at that internal support become NOT_APPLICABLE. End supports stay unresolved.
SB2 stays a SOURCE_CONFLICT. Blind: frozen Urban registers and the issued drawing's own readings only. Deterministic.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import graphic_evidence as GE  # noqa: E402
from engine.source import link_geometry as LG  # noqa: E402

ROUND = "S5.1"
POLICY = "GROUND_SYSTEM_REBAR_S5_1_DELTA_V1"
S5 = ROOT / "research/alsenan_ground_system_rebar_s5"
S41 = ROOT / "research/alsenan_footing_rebar_s4_1"
S61 = ROOT / "research/alsenan_superstructure_beam_rebar_s6_1"
SRD = ROOT / "research/source_recovery_delta"
S1 = ROOT / "research/alsenan_structural_census_s1"
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json"
CODE = ["engine/source/graphic_evidence.py", "engine/source/delta_release.py", "engine/source/link_geometry.py",
        "research/alsenan_ground_system_rebar_s5_1/build_ground_system_rebar_s5_1.py"]
INPUTS = ["research/alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
          "research/alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
          "research/alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json",
          "research/alsenan_structural_census_s1/COLUMN_OCCURRENCE_REGISTER.json",
          "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json",
          "research/source_recovery_delta/13_GRAPHIC_EVIDENCE.json",
          "research/source_recovery_delta/02_UNRESOLVED_MASTER_REGISTER.csv",
          "research/source_recovery_delta/08_S5_1_CANDIDATES.csv"]
OUTPUTS = ["S5_1_DELTA_COMPONENTS.csv", "S5_1_RELEASE_SUMMARY.json", "S5_1_UNRESOLVED.csv", "S5_1_PROVENANCE.jsonl",
           "S5_1_CHANGELOG.md"]
UNIT_MASS = "D2_OVER_162"
LONG_BARS = ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2")
STRAPS_STR2 = {"SB1": "1FE6", "SB3": "2B11"}
PRIMARY = ("WHOLE_COMPONENT", "CORE_PATH", "STRAIGHT_RUN")
ALL_TRUE = {c: True for c in GE.DERIVATION_CONDITIONS}
P13 = "ST7757.pdf p.13 ground-beam sections (one closed link + hook each)"


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"S5.1 check failed: {what}")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _csv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(r.get(k), sort_keys=True, ensure_ascii=False) if isinstance(r.get(k), (list, dict))
                        else ("" if r.get(k) is None else (round(r[k], 6) if isinstance(r.get(k), float) else r[k])))
                    for k in fields})
    path.write_text(buf.getvalue(), encoding="utf-8")


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode() + b"\0" + (ROOT / c).read_bytes() + b"\0")
    return h.hexdigest()


def kg_per_m(d):
    return d * d / 162.0


# ------------------------------------------------------------------ sources
def evidence():
    ge = _j(SRD / "13_GRAPHIC_EVIDENCE.json")["evidence"]
    secs = ge["E-PDF-02"]["facts"]
    check(len(secs) == 4 and all(v["links"] == 1 for v in secs.values()), "p.13: four sections, one closed link each")
    check(secs["GB_LT_2_5M (30x30)"]["label_leaders_on_link"] == 0, "the <2.5 m link carries no label")
    check(sum(1 for v in secs.values() if v["label_leaders_on_link"] == 1) == 3, "three labelled links (Ø8/15cm)")
    icons = {p["row"]: p for p in ge["E-DXF-03"]["facts"]["placements"]}
    for row, handle in STRAPS_STR2.items():
        check(icons[row]["icon"] == "STR2" and icons[row]["handle"] == handle, f"{row} carries the STR2 icon")
    check(icons["SB2"]["icon"] == "str3", "SB2 carries str3")
    check(ge["E-PDF-01"]["handles"] == ["p13:S-REIN.D"], "p.13 footing details (GB bars through the column)")
    reg = {r["ITEM_ID"]: r for r in _rows(SRD / "02_UNRESOLVED_MASTER_REGISTER.csv")}
    for i, st in (("S5-01", "SOURCE_FOUND_DERIVED"), ("S5-04", "SOURCE_FOUND_DERIVED"), ("S5-18", "SOURCE_FOUND_DERIVED"),
                  ("S5-02", "SOURCE_EXPECTED_NOT_LOCATED"), ("S5-08", "SOURCE_EXPECTED_NOT_LOCATED"),
                  ("S5-05", "SOURCE_EXPECTED_NOT_LOCATED"), ("S5-06", "SOURCE_EXPECTED_NOT_LOCATED"),
                  ("S5-11", "SOURCE_CONFLICT"), ("S5-07", "SOURCE_CONFLICT"), ("S5-16", "SOURCE_CONFLICT")):
        check(reg[i]["TERMINAL_STATE"] == st, f"SRD {i} is {st}")
    return {"sections": secs, "str2_rows": STRAPS_STR2}


def rules():
    cov = next(r for r in _j(R4)["rules"] if r["rule_id"] == "COVER_AGAINST_SOIL_70MM")
    check(cov["value"] == 70 and {"GROUND_BEAM", "STRAP_BEAM"} <= set(cov["applies_to"]), "soil cover applies")
    return {"cover_mm": 70.0, "cover_rule": f"{cov['rule_id']} ({cov['claim_id']}, {cov['source_state']})",
            "why": "70 mm is the larger note-22 cover; a 25 mm face elsewhere only enlarges the link, so the core "
                   "path stays a lower bound under either cover"}


def column_sides():
    by_handle = defaultdict(list)
    for r in _j(S1 / "COLUMN_OCCURRENCE_REGISTER.json")["rows"]:
        if r["floor"] != "FOUNDATION":
            continue
        for h in r["plan_source"]["handles"]:
            by_handle[h].append(r)
    return by_handle


def str2_icon_from_s61():
    s = _j(S61 / "S6_1_RELEASE_SUMMARY.json")["str2_icon"]
    check(s["legs"] == 4 and s["inner_levels_shared"] is False, "STR2 icon (as frozen in S6.1)")
    return s


# ------------------------------------------------------------------ support-end classification
def classify_ends(reg, bars):
    """Every GB support end: THROUGH_SUPPORT (same drawn band continues through a column and both spans carry the
    same released bars), INTERIOR_CONTINUING_UNVERIFIED, BEAM_JUNCTION_END or END_SUPPORT."""
    lines = defaultdict(list)
    for o in reg.values():
        if o["family"] == "GROUND_BEAM":
            lines[tuple(o["geometry_handles"])].append(o)
    shared = {}
    for k, os in lines.items():
        ends = defaultdict(list)
        for o in os:
            for side, idx in (("start_node", 1), ("end_node", 2)):
                nd = o[side]
                ends[(nd["kind"], tuple(nd["refs"]))].append((o["occurrence_id"], idx))
        for key, lst in ends.items():
            if len(lst) == 2 and key[0] == "COLUMN":
                shared[key] = lst
            check(len(lst) <= 2, f"band {k}: node {key} used by more than two spans")
    out = {}
    for key, lst in shared.items():
        (a, ia), (b, ib) = lst
        ok = (reg[a]["occurrence_state"] == reg[b]["occurrence_state"] == "LOWER_BOUND" and bars[a] == bars[b] and
              all(bars[a][c][0] == "LOWER_BOUND" for c in LONG_BARS) and not reg[a]["node_issues"] and
              not reg[b]["node_issues"])
        cls = "THROUGH_SUPPORT" if ok else "INTERIOR_CONTINUING_UNVERIFIED"
        why = ("same drawn band continues through the column; both spans carry identical released bars" if ok else
               "same drawn band continues through the column, but the other span is blocked or its bars differ")
        for (o, i), (other, j) in (((a, ia), (b, ib)), ((b, ib), (a, ia))):
            out[(o, i)] = {"class": cls, "node": key, "other_span": other, "other_end": j, "why": why}
    for o in reg.values():
        if o["family"] != "GROUND_BEAM":
            continue
        for side, idx in (("start_node", 1), ("end_node", 2)):
            if (o["occurrence_id"], idx) in out:
                continue
            nd = o[side]
            cls = "BEAM_JUNCTION_END" if nd["kind"] == "BEAM_JUNCTION" else "END_SUPPORT"
            out[(o["occurrence_id"], idx)] = {"class": cls, "node": (nd["kind"], tuple(nd["refs"])),
                                              "other_span": None, "other_end": None,
                                              "why": "the band does not continue through this node: development / "
                                                     "anchorage stays unresolved (S5-02)"}
    return out


# ------------------------------------------------------------------ build
def build(frozen, ev, rl, cols, icon):
    base = DR.baseline_label(frozen)
    comps = _rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv")
    part_kg = {}
    for line in (S5 / "GROUND_SYSTEM_REBAR_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines():
        p = json.loads(line)
        part_kg[p["record_id"]] = p["kg"]
    reg = {o["occurrence_id"]: o for o in _j(S5 / "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json")["occurrences"]}
    by = defaultdict(dict)
    for cm in comps:
        by[cm["occurrence_id"]][cm["component"]] = cm
    bars = {o: {c: (by[o][c]["state"], by[o][c]["bar_count"], by[o][c]["dia_mm"]) for c in LONG_BARS}
            for o, r in reg.items() if r["family"] == "GROUND_BEAM"}
    ends = classify_ends(reg, bars)
    c = rl["cover_mm"]

    def column_lb(node):
        kind, refs = node
        check(kind == "COLUMN" and len(refs) == 1 and refs[0].startswith("COL:"), f"column node {node}")
        h = refs[0].split(":", 1)[1].split("+")[0]
        rows = cols.get(h, [])
        check(len(rows) == 1, f"node {node}: one foundation column in S1")
        r = rows[0]
        return {"column_id": r["column_id"], "type": r["column_type"], "section_cm": r["schedule_section_cm"],
                "width_lb_mm": min(r["schedule_section_cm"]) * 10.0}

    recs, prov, runs = [], [], []

    def add(cm, change, portion, cls, model, state, portion_state, why, *, delta=0.0, basis=DR.BASIS_NONE,
            conditions=None, blocked=(), facets=None, evid=(), page="", handles="", source="", formula="",
            inputs=None):
        rid = f"{cm['occurrence_id']}:{cm['component']}"
        primary = portion in PRIMARY
        old = (part_kg.get(rid) or 0.0) if primary else 0.0
        if primary and cm["kg"]:
            check(abs(old - float(cm["kg"])) < 1e-5, f"{rid} provenance kg")
        r = DR.record(delta_id=f"S5.1-D{len(recs) + 1:04d}", change_kind=change, frozen_baseline=base,
                      baseline_component_id=rid, old_state=cm["state"], old_known_quantity=old,
                      new_project_source=source, source_page=page, source_handles=handles,
                      graphic_evidence_class=cls, new_component_model=model, delta_known_quantity=delta,
                      new_blocked_components=list(blocked), new_release_state=state, portion=portion,
                      portion_state=portion_state, quantity_basis=basis, derivation_conditions=conditions, why=why,
                      OCCURRENCE_ID=cm["occurrence_id"], FAMILY=cm["family"], MARK=cm["mark"],
                      COMPONENT=cm["component"], ACCURATE_COMPONENT=cm["accurate_component"],
                      QUANTITY_KIND=cm["quantity_kind"], DIA_MM=cm["dia_mm"], PRIMARY="Y" if primary else "N",
                      FACETS=facets or {}, EVIDENCE_IDS=list(evid), FORMULA=formula)
        recs.append(r)
        prov.append({"delta_id": r["DELTA_ID"], "baseline_component_id": rid, "portion": portion,
                     "frozen_baseline": {"manifest": frozen["manifest"], "sha256": frozen["manifest_sha256"],
                                         "engine_commit_stamp": frozen["engine_commit_stamp"]},
                     "frozen_row": {k: cm[k] for k in ("state", "kg", "count", "dia_mm", "bar_count",
                                                       "straight_run_m")},
                     "change_kind": change, "graphic_evidence_class": cls, "derivation_conditions": conditions,
                     "evidence_ids": list(evid), "source_page": page, "source_handles": handles,
                     "quantity_basis": basis, "formula": formula, "inputs": inputs, "delta_kg": delta,
                     "round": ROUND, "unit_mass": UNIT_MASS})
        return r

    def no_change(cm, why="unchanged from frozen S5"):
        add(cm, DR.NO_CHANGE, "WHOLE_COMPONENT", GE.NO_GRAPHIC_EVIDENCE, "unchanged", cm["state"], "", why)

    def stirrup_inputs(o):
        r = reg[o]
        sd, ss, sc = by[o]["STIRRUP_DIAMETER"], by[o]["STIRRUP_SPACING"], by[o]["STIRRUP_COUNT"]
        known = (sd["state"] == "VERIFIED" and ss["state"] == "VERIFIED" and sc["state"] == "LOWER_BOUND" and
                 r["width_state"] == "SOURCE_EXPLICIT" and r["depth_state"] == "SOURCE_EXPLICIT")
        return known, r, sd, ss, sc

    for cm in comps:
        o, comp, st, fam = cm["occurrence_id"], cm["component"], cm["state"], cm["family"]
        r = reg[o]
        lb = r["occurrence_state"] == "LOWER_BOUND"

        # ---------------- links
        if comp == "STIRRUP_CORE_PATH" and lb:
            known, rr, sd, ss, sc = stirrup_inputs(o)
            strap_icon = fam == "STRAP_BEAM" and cm["mark"] in STRAPS_STR2
            topo = (LG.topology_from_closed_links(2) if strap_icon else LG.topology_from_closed_links(1))
            topo_src = ("SBT REMARKS icon STR2 (E-DXF-03)" if strap_icon else
                        "p.13 sections: one closed link each (E-PDF-02)")
            if fam == "STRAP_BEAM" and not strap_icon:
                no_change(cm, "strap without an STR2 icon")
                continue
            if known:
                b, h, d = float(rr["width_mm"]), float(rr["depth_mm"]), float(sd["value"])
                n = int(sc["count"])
                core = LG.core_path_mm(b, h, c, d)
                kg = n * core / 1000.0 * kg_per_m(d)
                rid = f"{o}:{comp}"
                blocked = [f"{rid}:BEND_ARC"] + ([f"{rid}:INNER_LINK"] if strap_icon else [])
                formula = (f"n x [2(b-2c-d) + 2(h-2c-d)] x d^2/162 = {n} x [2({b:.0f}-{2 * c:.0f}-{d:.0f}) + "
                           f"2({h:.0f}-{2 * c:.0f}-{d:.0f})] mm x {d:.0f}^2/162 = {kg:.6f} kg")
                add(cm, DR.QUANTITY_RELEASED, "CORE_PATH", GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY,
                    (f"{topo['topology']}: outer link core path released; inner link blocked" if strap_icon else
                     f"{topo['topology']}: core path released"), DR.LOWER_BOUND, GE.DERIVED_LOWER_BOUND,
                    "width, depth, cover, diameter, rate, count and topology all source-known; corners sharp, hooks "
                    "and bends excluded", delta=kg, basis=DR.BASIS_DERIVED, conditions=ALL_TRUE, blocked=blocked,
                    facets={"TOPOLOGY": topo["topology"], "LEGS": topo["legs"], "CORE_PATH_MM": core, "COUNT": n,
                            "WIDTH_MM": b, "DEPTH_MM": h, "COVER_MM": c, "DIA_MM": d,
                            "PREMISES": list(LG.CORE_PATH_PREMISES)},
                    evid=("E-DXF-03",) if strap_icon else ("E-PDF-02",),
                    page="ST7757.pdf p.10 REMARKS" if strap_icon else "ST7757.pdf p.13",
                    handles=(f"ST7757.dxf STR2 insert {STRAPS_STR2[cm['mark']]}" if strap_icon else "p13:S-REIN.D"),
                    source=topo_src if strap_icon else P13, formula=formula,
                    inputs={"b_mm": b, "h_mm": h, "cover_mm": c, "d_mm": d, "count": n,
                            "cover_rule": rl["cover_rule"], "spacing": [ss["value"], ss["unit"]]})
                add(cm, DR.PORTION_DECOMPOSITION, "BEND_ARC", GE.NO_GRAPHIC_EVIDENCE,
                    "corner bend radius not in the set", DR.LOWER_BOUND, GE.BLOCKED_UNQUANTIFIED,
                    "corners taken sharp in the core path; bend radius not drawn or noted", blocked=blocked)
                if strap_icon:
                    add(cm, DR.TOPOLOGY_RECORDED, "INNER_LINK", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                        "STR2 inner closed link: 2 more legs found; width, location and height not dimensioned; no "
                        "equal subdivision", DR.LOWER_BOUND, GE.SHAPE_FOUND_LENGTH_BLOCKED,
                        f"the REMARKS icon draws the inner link offset {icon['inner_level_offsets']} units from the "
                        "outer one (a symbol, not a section)", blocked=blocked, evid=("E-DXF-03",),
                        page="ST7757.pdf p.10 REMARKS", handles="ST7757.dxf block STR2")
            else:
                if fam == "GROUND_BEAM" and rr["depth_state"] != "SOURCE_EXPLICIT" and "P13-GB-EXTERIOR" in \
                        rr["detail_ids"] and len(rr["detail_ids"]) == 1:
                    reason = ("FOLLOW ARCH depth unresolved (" + rr["depth_state"] + "): mass blocked (brief §16)")
                else:
                    reason = ("<2.5 m candidate: its link diameter / rate are not printed (S5-08 "
                              "SOURCE_EXPECTED_NOT_LOCATED), and the candidate details disagree")
                add(cm, DR.TOPOLOGY_RECORDED, "CORE_PATH", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                    f"{topo['topology']}: topology found; core path not quantified", st, GE.SHAPE_FOUND_LENGTH_BLOCKED,
                    reason, blocked=[f"{o}:{comp}"], facets={"TOPOLOGY": topo["topology"], "LEGS": topo["legs"],
                                                             "BLOCKED_BY": reason},
                    evid=("E-PDF-02",), page="ST7757.pdf p.13", handles="p13:S-REIN.D", source=P13)
            continue
        if comp in ("STIRRUP_HOOK_1", "STIRRUP_HOOK_2") and lb and not (fam == "STRAP_BEAM" and
                                                                      cm["mark"] not in STRAPS_STR2):
            add(cm, DR.FACET_ADDED, "WHOLE_COMPONENT", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                "link hook drawn (p.13 hook branch / icon hook ticks); angle and extension not printed",
                st, GE.SHAPE_FOUND_LENGTH_BLOCKED, "hook extension stays blocked (S5-05)",
                facets={"HOOK_SHAPE": "SOURCE_FOUND", "HOOK_EXTENSION": "BLOCKED_UNQUANTIFIED (S5-05)"},
                evid=("E-PDF-02", "E-DXF-03") if fam == "STRAP_BEAM" else ("E-PDF-02",), page="ST7757.pdf p.13")
            continue

        # ---------------- support ends (GB)
        if fam == "GROUND_BEAM" and comp in ("DEVELOPMENT_SUPPORT_1", "DEVELOPMENT_SUPPORT_2", "HOOK_1", "HOOK_2"):
            idx = int(comp[-1])
            e = ends[(o, idx)]
            facets = {"END_CLASS": e["class"], "NODE": list(e["node"][1]), "NODE_KIND": e["node"][0],
                      "CONTINUES_INTO": e["other_span"]}
            if e["class"] == "THROUGH_SUPPORT":
                what = "development" if comp.startswith("DEVELOPMENT") else "bar-end hook"
                add(cm, DR.SEMANTIC_CORRECTION, "WHOLE_COMPONENT", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                    f"THROUGH_SUPPORT: the bars run on into {e['other_span']}; no {what} at this internal support",
                    DR.NOT_APPLICABLE, "", "p.13 draws the GB bars unbroken through the column (S5-01); "
                                           "no termination at the column face", facets=facets,
                    evid=("E-PDF-01",), page="ST7757.pdf p.13", handles="p13:S-REIN.D 'Ground beam reinforcements.'")
            else:
                add(cm, DR.FACET_ADDED, "WHOLE_COMPONENT", GE.NO_GRAPHIC_EVIDENCE,
                    f"support end classified {e['class']}", st, "", e["why"], facets=facets)
            continue

        # ---------------- through-support portions on the longitudinal bars
        if fam == "GROUND_BEAM" and comp in LONG_BARS and lb and st == "LOWER_BOUND":
            through = [(i, ends[(o, i)]) for i in (1, 2) if ends[(o, i)]["class"] == "THROUGH_SUPPORT"]
            if not through:
                no_change(cm)
                continue
            n, d = int(cm["bar_count"]), int(cm["dia_mm"])
            blocked = [f"{o}:{comp}:{x}" for x in ("END_DEVELOPMENT",) if any(ends[(o, i)]["class"] !=
                                                                            "THROUGH_SUPPORT" for i in (1, 2))]
            add(cm, DR.PORTION_DECOMPOSITION, "STRAIGHT_RUN", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                "frozen face-to-face run kept; the bar continues through "
                + " and ".join(f"support {i}" for i, _ in through), DR.LOWER_BOUND, GE.KNOWN_STRAIGHT_SEGMENT,
                "the frozen run is part of one continuous BAR_RUN; nothing is subtracted", blocked=blocked,
                facets={"THROUGH_ENDS": [i for i, _ in through]}, evid=("E-PDF-01",), page="ST7757.pdf p.13")
            for i, e in through:
                col = column_lb(e["node"])
                half = col["width_lb_mm"] / 2.0
                kg = n * half / 1000.0 * kg_per_m(d)
                formula = (f"n x (column lower-bound side / 2) x d^2/162 = {n} x ({col['width_lb_mm']:.0f}/2) mm x "
                           f"{d}^2/162 = {kg:.6f} kg")
                add(cm, DR.QUANTITY_RELEASED, f"THROUGH_SUPPORT_{i}", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                    f"this span's half of the bar inside column {col['column_id']} (shared with {e['other_span']})",
                    DR.LOWER_BOUND, GE.DERIVED_LOWER_BOUND,
                    "p.13 shows the GB bars continuous through the column (topology only); the length is the "
                    "column's smaller schedule side (S1), a lower bound for any orientation, split half to each span",
                    delta=kg, basis=DR.BASIS_SCHEDULE, blocked=blocked,
                    facets={"NODE": list(e["node"][1]), "COLUMN": col, "OTHER_SPAN": e["other_span"]},
                    evid=("E-PDF-01",), page="ST7757.pdf p.13", handles="p13:S-REIN.D; S1 " + col["column_id"],
                    source="ST7757.pdf p.13 'TYP. DETAIL OF ISOLATED FOOTING' (GB bars through the column)",
                    formula=formula, inputs={"count": n, "dia_mm": d, "column": col})
            continue
        no_change(cm)

    # continuous BAR_RUN chains along each band
    chains = defaultdict(list)
    for (o, i), e in ends.items():
        if e["class"] == "THROUGH_SUPPORT" and i == 2:
            chains[tuple(reg[o]["geometry_handles"])].append((o, e["other_span"], e["node"]))
    for band, links in sorted(chains.items()):
        spans = []
        nxt = {a: b for a, b, _ in links}
        prv = {b: a for a, b, _ in links}
        start = [a for a in nxt if a not in prv]
        check(len(start) == 1, f"band {band}: one chain")
        cur = start[0]
        spans.append(cur)
        while cur in nxt:
            cur = nxt[cur]
            spans.append(cur)
        nodes = [nd for _, _, nd in sorted(links, key=lambda x: spans.index(x[0]))]
        run_lb = sum(reg[s]["bar_straight_run_lower_bound_m"] for s in spans) + \
            sum(column_lb(nd)["width_lb_mm"] / 1000.0 for nd in nodes)
        runs.append({"BAR_RUN_ID": "THROUGH:" + "+".join(band), "BAND_HANDLES": list(band), "SPANS": spans,
                     "INTERIOR_SUPPORTS": [list(nd[1]) for nd in nodes], "BARS": {c_: list(bars[spans[0]][c_][1:])
                                                                                   for c_ in LONG_BARS},
                     "CONTINUOUS_RUN_LOWER_BOUND_M": run_lb,
                     "END_SUPPORTS": "development / anchorage unresolved (S5-02)"})
    return comps, recs, prov, ends, runs


def unresolved(recs):
    frozen_unres = _rows(S5 / "GROUND_SYSTEM_REBAR_UNRESOLVED.csv")
    by_cid = defaultdict(list)
    for r in recs:
        by_cid[r["BASELINE_COMPONENT_ID"]].append(r)
    out = []
    for u in frozen_unres:
        cid = f"{u['occurrence_id']}:{u['component']}"
        rs = by_cid.get(cid, [])
        prim = next((r for r in rs if r["PRIMARY"] == "Y"), None)
        released = any(r["CHANGE_KIND"] == DR.QUANTITY_RELEASED and r["DELTA_KNOWN_QUANTITY"] > 0 for r in rs)
        if prim is None or prim["CHANGE_KIND"] == DR.NO_CHANGE:
            status, st = "OPEN (unchanged)", u["state"]
        elif prim["NEW_RELEASE_STATE"] == DR.NOT_APPLICABLE:
            status, st = "CLOSED (not applicable: through-support)", DR.NOT_APPLICABLE
        elif released:
            status, st = "NARROWED (lower bound released; named facets still open)", DR.LOWER_BOUND
        else:
            status, st = "OPEN (facet recorded)", prim["NEW_RELEASE_STATE"]
        out.append({"UNRESOLVED_ID": f"S5.1-U{len(out) + 1:04d}", "ORIGIN": "CARRIED_FROM_S5",
                    "BASELINE_COMPONENT_ID": cid, "OCCURRENCE_ID": u["occurrence_id"], "FAMILY": u["family"],
                    "MARK": u["mark"], "COMPONENT": u["component"], "PORTION": "WHOLE_COMPONENT",
                    "S5_STATE": u["state"], "S5_1_STATE": st, "S5_1_STATUS": status,
                    "WHAT_IS_MISSING": u["what_is_missing"], "QUESTION_ID": u["question_id"]})
    for r in recs:
        if r["PRIMARY"] == "N" and r["PORTION_STATE"] in (GE.SHAPE_FOUND_LENGTH_BLOCKED, GE.BLOCKED_UNQUANTIFIED):
            out.append({"UNRESOLVED_ID": f"S5.1-U{len(out) + 1:04d}", "ORIGIN": "NEW_IN_S5_1",
                        "BASELINE_COMPONENT_ID": r["BASELINE_COMPONENT_ID"], "OCCURRENCE_ID": r["OCCURRENCE_ID"],
                        "FAMILY": r["FAMILY"], "MARK": r["MARK"], "COMPONENT": r["COMPONENT"],
                        "PORTION": r["PORTION"], "S5_STATE": "", "S5_1_STATE": r["PORTION_STATE"],
                        "S5_1_STATUS": "OPEN (new named portion)", "WHAT_IS_MISSING": r["WHY"], "QUESTION_ID": ""})
    return out


CHANGELOG = """# S5.1 CHANGELOG: ground-system rebar delta release over frozen S5

**Round:** `S5.1` · **Policy:** `{policy}` · **Frozen baseline:** `{manifest}` (sha `{msha12}`, stamp `{stamp}`)
**Preceded by:** S4.1 (`{s41}`) and S6.1 (`{s61}`) freezes · **Built by** `build_ground_system_rebar_s5_1.py` (blind, byte-identical rebuild)

S5 is unchanged. Every S5 code, input and output hash was checked first, and no S5 file was written. This file is
BASELINE + DELTA.

## Headline

| | kg |
|---|---|
| Frozen S5 known | {frozen_known:.4f} |
| Longitudinal delta (through-support portions) | {d_long:.4f} |
| Stirrup core-path delta | {d_core:.4f} |
| **S5.1 known** | **{new_known:.4f}** |

Every released quantity is a LOWER_BOUND. Nothing was raised to VERIFIED.

## Links (brief §16, §18)

- Each p.13 section draws one closed link (2 legs) with a hook. Three of the links carry Ø8/15cm; the <2.5 m link
  has no label, so its diameter and rate stay SOURCE_EXPECTED_NOT_LOCATED.
- **Released:** {n_gb_core} GB stirrup sets and {n_strap_core} strap sets (SB1 / SB3).
  - These are the only sets where width, depth, cover, diameter, rate, count and topology are all source-known.
  - CORE_PATH = 2(b-2c-d) + 2(h-2c-d), with c = 70 mm. That is the larger note-22 cover, so the result is a lower
    bound under either cover.
  - Hook extension and bend arc stay blocked.
- **SB1 / SB3** use the STR2 topology (4 legs): only the outer link is released. The inner link is not inferred.
  SB2 (str3) stays a SOURCE_CONFLICT.
- **Topology only, mass blocked:** {n_topo_only} GB sets.
  - {n_follow} are spans whose depth is FOLLOW ARCH (unresolved).
  - {n_cand} are <2.5 m candidate spans (their link is not printed).

## Through-support runs (brief §17)

- Every GB support end is classified: {end_classes}.
- **THROUGH_SUPPORT** means the same drawn band continues through a column and both spans carry identical released
  bars.
  - Source: p.13 draws the GB bars unbroken through the column.
  - The two spans become one BAR_RUN. There is no termination at the column face and no development at the
    internal support: those development and hook components become NOT_APPLICABLE.
  - The bar inside the column is released at the column's smaller schedule side (S1), split half to each span.
- **Continuous runs:** {n_runs}, over {n_nodes} interior supports.
- End-support development stays unresolved (S5-02).

## Not resolved (brief §20)

SB2, the annex exterior-GB depth, and the GB band against the support face.

## Counts

- Delta rows: {n_rows}, covering all {n_frozen} frozen components.
- Unresolved: {n_unres} rows ({n_carried} carried from S5 with their S5.1 status, {n_new} new named portions).

## Files

| File | Content |
|---|---|
| `S5_1_DELTA_COMPONENTS.csv` | one row per frozen component (plus named portions), with all brief §2 fields |
| `S5_1_RELEASE_SUMMARY.json` | baseline, deltas, new totals, end classes, continuous runs, conservation, flags |
| `S5_1_UNRESOLVED.csv` | carried S5 rows with their S5.1 status, plus new blocked portions |
| `S5_1_PROVENANCE.jsonl` | per delta row: frozen row, formula, inputs, evidence ids, class, conditions |
| `S5_1_FREEZE_MANIFEST.json` | S5.1 frozen |
"""


def main():
    frozen = DR.verify_frozen(S5 / "S5_FREEZE_MANIFEST.json", ROOT)
    s41 = DR.verify_frozen(S41 / "S4_1_FREEZE_MANIFEST.json", ROOT)
    s61 = DR.verify_frozen(S61 / "S6_1_FREEZE_MANIFEST.json", ROOT)
    check(_j(S61 / "S6_1_FREEZE_MANIFEST.json")["state"] == "FROZEN_BEFORE_S5_1", "S6.1 frozen before S5.1")
    ev = evidence()
    rl = rules()
    cols = column_sides()
    icon = str2_icon_from_s61()
    s5 = _j(S5 / "GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json")
    frozen_known = s5["known_source_derived_ground_system_rebar_kg"]
    comps, recs, prov, ends, runs = build(frozen, ev, rl, cols, icon)
    new_known = sum(r["NEW_KNOWN_QUANTITY"] for r in recs)
    cons = DR.conservation(frozen_known, recs, new_known)
    check(cons["all_pass"], f"conservation {cons}")
    ids = {f"{c['occurrence_id']}:{c['component']}" for c in comps}
    check({r["BASELINE_COMPONENT_ID"] for r in recs} == ids, "every component covered")
    check(sum(1 for r in recs if r["PRIMARY"] == "Y") == len(comps), "one primary row per component")
    d_core = sum(r["DELTA_KNOWN_QUANTITY"] for r in recs if r["PORTION"] == "CORE_PATH")
    d_long = sum(r["DELTA_KNOWN_QUANTITY"] for r in recs if r["PORTION"].startswith("THROUGH_SUPPORT"))
    check(abs(d_core + d_long - cons["delta_known"]) < 1e-9, "delta split")
    core_rel = [r for r in recs if r["PORTION"] == "CORE_PATH" and r["CHANGE_KIND"] == DR.QUANTITY_RELEASED]
    core_topo = [r for r in recs if r["PORTION"] == "CORE_PATH" and r["CHANGE_KIND"] == DR.TOPOLOGY_RECORDED]
    n_follow = sum(1 for r in core_topo if "FOLLOW ARCH" in r["WHY"])
    end_classes = dict(sorted(Counter(e["class"] for e in ends.values()).items()))
    n_nodes = sum(len(r["INTERIOR_SUPPORTS"]) for r in runs)
    comp_state = {r["BASELINE_COMPONENT_ID"]: r["NEW_RELEASE_STATE"] for r in recs if r["PRIMARY"] == "Y"}
    old_state = {f"{c['occurrence_id']}:{c['component']}": c["state"] for c in comps}
    transitions = Counter(f"{old_state[k]} -> {v}" for k, v in comp_state.items() if old_state[k] != v)
    unres = unresolved(recs)
    ctx = {"ROUND": ROUND, "POLICY": POLICY, "ENGINE_COMMIT": f"{frozen['engine_commit_stamp']}+delta:"
                                                             f"{code_digest()[:16]}",
           "FROZEN_BASELINE": frozen, "PRECEDING_FREEZES": {"S4.1": s41, "S6.1": s61}, "UNIT_MASS": UNIT_MASS,
           "COVER": rl}
    summary = {
        "round": ROUND, "policy": POLICY, "context": ctx, "graphic_evidence_policy": GE.policy_record(),
        "frozen_s5": {"known_kg": frozen_known, "components_by_state": s5["components_by_state"]},
        "delta_known_kg": cons["delta_known"],
        "delta_by_kind_kg": {"longitudinal_through_support": d_long, "stirrup_core_path": d_core},
        "s5_1_known_kg": new_known, "s5_1_verified_kg": 0.0,
        "stirrup_core_path_released": {"ground_beam": sum(1 for r in core_rel if r["FAMILY"] == "GROUND_BEAM"),
                                       "strap_str2_outer_link": sum(1 for r in core_rel if r["FAMILY"] ==
                                                                    "STRAP_BEAM"),
                                       "by_occurrence": {r["OCCURRENCE_ID"]: r["DELTA_KNOWN_QUANTITY"]
                                                         for r in core_rel}},
        "stirrup_topology_only": {"total": len(core_topo), "follow_arch_depth": n_follow,
                                  "lt_2_5m_candidate": len(core_topo) - n_follow},
        "gb_link_sections": {k: {"links": v["links"], "label_leaders_on_link": v["label_leaders_on_link"]}
                             for k, v in ev["sections"].items()},
        "support_end_classes": end_classes, "continuous_bar_runs": runs,
        "through_support_interior_nodes": n_nodes,
        "sb2": "SOURCE_CONFLICT (unchanged; brief §18 / §20)",
        "components_by_state": dict(sorted(Counter(comp_state.values()).items())),
        "state_transitions": dict(sorted(transitions.items())),
        "unresolved": {"rows": len(unres), "carried_from_s5": sum(1 for u in unres if u["ORIGIN"] ==
                                                                  "CARRIED_FROM_S5"),
                       "new_portion_rows": sum(1 for u in unres if u["ORIGIN"] == "NEW_IN_S5_1"),
                       "by_status": dict(sorted(Counter(u["S5_1_STATUS"] for u in unres).items()))},
        "not_resolved_brief_20": ["SB2 (S5-11)", "annex exterior-GB depth (S5-07)", "GB band vs support face (S5-16)"],
        "delta_rows": len(recs), "frozen_components": len(comps), "conservation": cons,
        "flags": {"frozen_outputs_changed": False, "plotted_scale_used": False, "kg_from_shape_only_graphic": False,
                  "verified_created": False, "equal_inner_link_subdivision": False, "pre_s7_started": False,
                  "references_read": []},
        "headline": "S5.1 KNOWN GROUND-SYSTEM REBAR = FROZEN S5 KNOWN + LOWER-BOUND DELTA"}
    fields = ["DELTA_ID", "CHANGE_KIND", "FROZEN_BASELINE", "BASELINE_COMPONENT_ID", "OCCURRENCE_ID", "FAMILY", "MARK",
              "COMPONENT", "ACCURATE_COMPONENT", "QUANTITY_KIND", "PORTION", "PRIMARY", "OLD_STATE",
              "OLD_KNOWN_QUANTITY", "NEW_PROJECT_SOURCE", "SOURCE_PAGE", "SOURCE_HANDLES", "GRAPHIC_EVIDENCE_CLASS",
              "NEW_COMPONENT_MODEL", "PORTION_STATE", "QUANTITY_BASIS", "DELTA_KNOWN_QUANTITY", "NEW_KNOWN_QUANTITY",
              "NEW_BLOCKED_COMPONENTS", "NEW_RELEASE_STATE", "DIA_MM", "FACETS", "EVIDENCE_IDS", "FORMULA", "WHY"]
    _csv(HERE / "S5_1_DELTA_COMPONENTS.csv", recs, fields)
    _csv(HERE / "S5_1_UNRESOLVED.csv", unres, list(unres[0].keys()))
    with open(HERE / "S5_1_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for p in prov:
            f.write(json.dumps(p, sort_keys=True, ensure_ascii=False) + "\n")
    _json(HERE / "S5_1_RELEASE_SUMMARY.json", summary)
    (HERE / "S5_1_CHANGELOG.md").write_text(CHANGELOG.format(
        policy=POLICY, manifest=frozen["manifest"], msha12=frozen["manifest_sha256"][:12],
        stamp=frozen["engine_commit_stamp"], s41=s41["manifest_sha256"][:12], s61=s61["manifest_sha256"][:12],
        frozen_known=frozen_known, d_long=d_long, d_core=d_core, new_known=new_known,
        n_gb_core=summary["stirrup_core_path_released"]["ground_beam"],
        n_strap_core=summary["stirrup_core_path_released"]["strap_str2_outer_link"], n_topo_only=len(core_topo),
        n_follow=n_follow, n_cand=len(core_topo) - n_follow,
        end_classes=", ".join(f"{k} {v}" for k, v in end_classes.items()), n_runs=len(runs), n_nodes=n_nodes,
        n_rows=len(recs), n_frozen=len(comps), n_unres=len(unres), n_carried=summary["unresolved"]["carried_from_s5"],
        n_new=summary["unresolved"]["new_portion_rows"]), encoding="utf-8")
    manifest = {"round": ROUND, "state": "FROZEN", "baseline_round": "S5", "frozen_baseline": frozen,
                "preceding_freezes": {"S4.1": s41, "S6.1": s61}, "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {i: _sha(ROOT / i) for i in INPUTS}, "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "engine_commit_stamp": ctx["ENGINE_COMMIT"], "references_read_before_freeze": [],
                "rule": "S5.1 is a delta over frozen S5; a correction needs a new delta round, never an edit of S5 "
                        "or of these outputs"}
    _json(HERE / "S5_1_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({k: summary[k] for k in ("delta_known_kg", "delta_by_kind_kg", "s5_1_known_kg",
                                              "stirrup_core_path_released", "stirrup_topology_only",
                                              "support_end_classes", "through_support_interior_nodes",
                                              "components_by_state", "state_transitions", "unresolved")}, indent=1))


if __name__ == "__main__":
    main()
