"""ALSENAN S6.1 - superstructure beam rebar DELTA release over the frozen S6 baseline.

    python3 -I research/alsenan_superstructure_beam_rebar_s6_1/build_superstructure_beam_rebar_s6_1.py

S6 stays frozen: its manifest (and the S4.1 freeze that must precede this round) is hash-checked first, and no
S6 file is written. Every change is a delta record (engine.source.delta_release); every graphic reading carries its
class (engine.source.graphic_evidence); link lengths come from engine.source.link_geometry.

Released (LOWER_BOUND, envelope only):
  * single closed link (p.15 / p.13): CORE_PATH = 2(b-2c-d) + 2(h-2c-d), c = 25 mm (note 22), x released count;
    hook extension blocked;
  * STR2 rows: outer link core path only; the inner link (width, location, height) stays blocked;
  * CB7: the two stirrup counts every surviving reading direction agrees on;
  * B3 WITH STAIR: the B3 schedule bars over the plan clear run (cranked excess, end bends blocked);
  * B26: base schedule bars + count + outer-link core path; planted-column extra 4 Ø16 over its horizontal
    projection 2 x DEPTH + column width (crank excess and hooks blocked).
Recorded, not released: CB end-support top-bar legs (which bar carries the leg is in conflict, Q2).
Blind: reads only frozen Urban registers and the issued drawing's own block geometry. Deterministic.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ezdxf  # noqa: E402

from engine.source import delta_release as DR  # noqa: E402
from engine.source import graphic_evidence as GE  # noqa: E402
from engine.source import link_geometry as LG  # noqa: E402

ROUND = "S6.1"
POLICY = "SUPERSTRUCTURE_BEAM_REBAR_S6_1_DELTA_V1"
S6 = ROOT / "research/alsenan_superstructure_beam_rebar_s6"
S41 = ROOT / "research/alsenan_footing_rebar_s4_1"
SRD = ROOT / "research/source_recovery_delta"
S1 = ROOT / "research/alsenan_structural_census_s1"
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
DXF = ROOT / "data/inputs/by_sha256" / f"{DXF_SHA}.dxf"
CODE = ["engine/source/graphic_evidence.py", "engine/source/delta_release.py", "engine/source/link_geometry.py",
        "research/alsenan_superstructure_beam_rebar_s6_1/build_superstructure_beam_rebar_s6_1.py"]
INPUTS = ["research/alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
          "research/alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
          "research/alsenan_structural_census_s1/BEAM_DEFINITION_REGISTER.json",
          "research/alsenan_structural_census_s1/COLUMN_OCCURRENCE_REGISTER.json",
          "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json",
          "research/source_recovery_delta/13_GRAPHIC_EVIDENCE.json",
          "research/source_recovery_delta/02_UNRESOLVED_MASTER_REGISTER.csv",
          "research/source_recovery_delta/09_S6_1_CANDIDATES.csv"]
OUTPUTS = ["S6_1_DELTA_COMPONENTS.csv", "S6_1_STIRRUP_TOPOLOGY.csv", "S6_1_RELEASE_SUMMARY.json",
           "S6_1_UNRESOLVED.csv", "S6_1_PROVENANCE.jsonl", "S6_1_CHANGELOG.md"]
UNIT_MASS = "D2_OVER_162"
B3_WITH_STAIR = ("BM-1F_ROOF-B3-BL023-6B9", "BM-GF_ROOF-B3-BL033-6B7")
B26 = "BM-GF_ROOF-B26-BL014-4CC"
CB7 = "CBO-GFRS-CB7-BL003"
PLANTED_COLUMN = "COLPOS-X15-Y02-31508-8912"
PRIMARY = ("WHOLE_COMPONENT", "CORE_PATH", "STRAIGHT_RUN", "STRAIGHT_PROJECTION")
ALL_TRUE = {c: True for c in GE.DERIVATION_CONDITIONS}
P15 = "ST7757.pdf p.15 'TYP. SLAB ON BEAMS DETAIL' beam section (one closed link)"
P13 = "ST7757.pdf p.13 labelled ground-beam sections (one closed link + hook)"


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"S6.1 check failed: {what}")


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
def link_icons():
    """STR2 / str3 block geometry from the issued DXF: closed links, legs, and whether the inner links share the
    outer link's top and bottom levels (they do not: the icon is a symbol, not a section)."""
    check(_sha(DXF) == DXF_SHA, "ST7757.dxf sha256")
    doc = ezdxf.readfile(str(DXF))
    out = {}
    for name in ("STR2", "str3"):
        rects = []
        for e in doc.blocks.get(name):
            if e.dxftype() == "LWPOLYLINE" and e.closed:
                ys = [float(p[1]) for p in e.get_points()]
                xs = [float(p[0]) for p in e.get_points()]
                rects.append({"x": [round(min(xs), 1), round(max(xs), 1)], "y": [round(min(ys), 1), round(max(ys), 1)]})
        rects.sort(key=lambda r: -(r["x"][1] - r["x"][0]))
        outer, inner = rects[0], rects[1:]
        topo = LG.topology_from_closed_links(len(rects))
        offsets = [round(i["y"][0] - outer["y"][0], 1) for i in inner]
        out[name] = dict(topo, outer=outer, inner=inner, inner_level_offsets=offsets,
                         inner_levels_shared=all(abs(o) < 1.0 for o in offsets))
    check(out["STR2"]["legs"] == 4 and out["str3"]["legs"] == 6, "STR2 = 4 legs, str3 = 6 legs")
    check(not out["STR2"]["inner_levels_shared"], "STR2 inner link is drawn offset (symbol, not section)")
    return out


def evidence():
    ge = _j(SRD / "13_GRAPHIC_EVIDENCE.json")["evidence"]
    icons = ge["E-DXF-03"]["facts"]
    str2_rows = sorted({p["row"] for p in icons["placements"] if p["icon"] == "STR2"})
    check(ge["E-PDF-05"]["facts"]["closed_links"] == 1, "p.15 beam section = one closed link")
    check(all(v["links"] == 1 for v in ge["E-PDF-02"]["facts"].values()), "p.13 sections = one closed link each")
    check(len(ge["E-PDF-04"]["facts"]["end_support_top_bar_legs"]) == 6, "six CB end legs drawn")
    stair = ge["E-PDF-06"]["facts"]["p16_TYPICAL_DETAIL_OF_STAIR_BEAM"]["callouts"]
    check(any("2" in c and "12" in c for c in stair) and any("4" in c and "16" in c for c in stair), "p.16 callouts")
    b3 = ge["E-DXF-07"]["facts"]["B3_row"]
    check((b3["W"], b3["H"]) == (20, 40), "B3 = 20 x 40")
    planted = ge["E-PDF-06"]["facts"]["p15_BEAM_CARRYING_PLANTED_COL"]
    check("DEPTH" in planted["callouts"] and any("16" in c for c in planted["callouts"]), "p.15 planted callouts")
    return {"str2_rows": str2_rows, "E-DXF-03": icons, "E-PDF-04": ge["E-PDF-04"]["facts"],
            "E-PDF-06": ge["E-PDF-06"]["facts"], "E-DXF-07": ge["E-DXF-07"]["facts"]}


def rules():
    cov = next(r for r in _j(R4)["rules"] if r["rule_id"] == "COVER_GENERAL_25MM")
    check(cov["value"] == 25 and {"BEAM", "CONTINUOUS_BEAM"} <= set(cov["applies_to"]), "note 22 cover applies")
    return {"cover_mm": 25.0, "cover_rule": f"{cov['rule_id']} ({cov['claim_id']}, {cov['source_state']})"}


def definitions():
    return {r["definition_id"]: r for r in _j(S1 / "BEAM_DEFINITION_REGISTER.json")["rows"]}


def planted_column():
    rows = [r for r in _j(S1 / "COLUMN_OCCURRENCE_REGISTER.json")["rows"] if r["chain_id"] == PLANTED_COLUMN]
    check(len(rows) == 1 and rows[0]["planted_on"], "one planted column occurrence")
    r = rows[0]
    check(r["drawn_vs_schedule"] == "MATCH", "planted column drawn = schedule")
    return {"column_id": r["column_id"], "type": r["column_type"], "section_cm": r["schedule_section_cm"],
            "width_along_beam_lower_bound_mm": min(r["schedule_section_cm"]) * 10.0,
            "why": "the smaller column side is used: a lower bound whichever way the column is oriented on the beam"}


# ------------------------------------------------------------------ build
def build(frozen, ev, icons, rl, defs, col):
    base = DR.baseline_label(frozen)
    comps = _rows(S6 / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv")
    part_kg = {}
    for line in (S6 / "SUPERSTRUCTURE_BEAM_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines():
        p = json.loads(line)
        part_kg[p["record_id"]] = p["kg"]
    occ_csv = {r["occurrence_id"]: r for r in _rows(S6 / "SUPERSTRUCTURE_BEAM_OCCURRENCES.csv")}
    reg = {o["occurrence_id"]: o for o in _j(S6 / "SUPERSTRUCTURE_BEAM_OCCURRENCE_REGISTER.json")["occurrences"]}
    counts = {(r["occurrence_id"], r["span_index"]): r for r in _rows(S6 / "SUPERSTRUCTURE_BEAM_STIRRUP_COUNTS.csv")}
    cands = _rows(S6 / "S6_1_RELEASE_CANDIDATES.csv")
    c = rl["cover_mm"]

    # occurrence-level releases decided by this round
    released_occ = set(B3_WITH_STAIR) | {B26}
    for o in released_occ:
        idn = reg[o]["identity"]
        check(occ_csv[o]["occurrence_state"] == "BLOCKED" and idn["BINDING_STATE"] == "BOUND_VERIFIED" and
              idn["WIDTH_MATCH_STATE"] == "MATCH", f"{o} binding is otherwise source-safe")
    lb_occ = {k for k, v in occ_csv.items() if v["occurrence_state"] == "LOWER_BOUND"} | released_occ

    # S6 convention check: simple-beam runs and stirrup distributions are the clear face-to-face span
    for o, r in reg.items():
        if r["subfamily"] == "SIMPLE_BEAM" and occ_csv[o]["occurrence_state"] == "LOWER_BOUND":
            g = r["geometry"]["clear_face_to_face_m"]
            check(all(abs(b["register_run_m"] - g) < 1e-9 for b in r["bar_runs"]), f"{o} run = clear span")
            check(all(abs(s["distribution_m"] - g) < 1e-9 for s in r["stirrups"]), f"{o} distribution = clear span")

    def section(o):
        r = reg[o]
        did = f"BDEF-{r['mark']}-{r['identity']['SCHEDULE_ROW']}"
        d = defs[did]
        b, h = d["B_cm"] * 10.0, d["H_cm"] * 10.0
        check(abs(b - float(r["identity"]["SCHEDULE_WIDTH_MM"])) < 1e-6, f"{o} S1 width = schedule width")
        wm = r["identity"]["WIDTH_MATCH_STATE"]
        check(all(x == "MATCH" for x in (wm if isinstance(wm, list) else [wm])), f"{o} drawn width = schedule width")
        return b, h, did

    # stirrup counts released here
    count_release = {}
    for cand in cands:
        its = json.loads(cand["interpretations"])
        inv = LG.invariant(its, ("count", "dia_mm", "run_rule"))
        check(inv is not None and inv["count"] == int(cand["would_release_count"]), "CB7 interpretations agree")
        count_release[(cand["occurrence_id"], cand["span_index"])] = {
            "count": inv["count"], "dia_mm": inv["dia_mm"], "basis": "every surviving reading direction "
            f"({', '.join(i['name'] for i in its)}) gives {inv['count']} x Ø{inv['dia_mm']} at "
            f"{inv['run_rule'][1]}/m over the same span", "readings": [i["name"] for i in its]}
    for o in released_occ:
        r = reg[o]
        run = r["geometry"]["clear_face_to_face_m"]
        for s in r["stirrups"]:
            check(s["mode"] == "BARS_PER_METRE", f"{o} stirrup rate per metre")
            count_release[(o, str(s["SPAN_INDEX"]))] = {
                "count": LG.count_lower_bound(s["value"], run), "dia_mm": s["dia_mm"],
                "basis": f"ceil({s['value']}/m x clear run {run} m), the S6 convention (no +1)",
                "readings": ["SCHEDULE"]}
    # the generic invariance test also covers every other ambiguous-direction CB with unreleased counts
    invariance_tested = []
    for o, r in reg.items():
        if r["subfamily"] != "CONTINUOUS_BEAM" or occ_csv[o]["occurrence_state"] != "LOWER_BOUND":
            continue
        if occ_csv[o]["reading_direction_state"] != "AMBIGUOUS":
            continue
        spans = sorted(r["stirrups"], key=lambda s: s["SPAN_INDEX"])
        fwd = [(s["value"], s["dia_mm"]) for s in spans]
        rev = fwd[::-1]
        for i, s in enumerate(spans):
            ok = fwd[i] == rev[i]
            invariance_tested.append({"occurrence_id": o, "span_index": s["SPAN_INDEX"], "forward": fwd[i],
                                      "reversed": rev[i], "invariant": ok})
            key = (o, str(s["SPAN_INDEX"]))
            if counts[key]["state"] != "LOWER_BOUND":
                check(ok == (key in count_release), f"{key}: count released only when the readings agree")

    stirrup_count_state = {}
    for k, v in counts.items():
        if v["state"] == "LOWER_BOUND":
            stirrup_count_state[k] = {"count": int(v["count_lower_bound"]), "dia_mm": int(v["DIAMETER_MM"]),
                                      "origin": "S6"}
    for k, v in count_release.items():
        check(k not in stirrup_count_state, f"{k} released once")
        stirrup_count_state[k] = {"count": v["count"], "dia_mm": v["dia_mm"], "origin": "S6.1", "basis": v["basis"]}

    recs, prov, topo = [], [], []

    def add(cm, change, portion, cls, model, state, portion_state, why, *, delta=0.0, basis=DR.BASIS_NONE,
            conditions=None, blocked=(), facets=None, evid=(), page="", handles="", source="", formula="",
            inputs=None, delta_count=None):
        primary = portion in PRIMARY
        old = (part_kg.get(cm["record_id"]) or 0.0) if primary else 0.0
        if primary and cm["kg"]:
            check(abs(old - float(cm["kg"])) < 1e-5, f"{cm['record_id']} provenance kg")
        r = DR.record(delta_id=f"S6.1-D{len(recs) + 1:04d}", change_kind=change, frozen_baseline=base,
                      baseline_component_id=cm["record_id"], old_state=cm["state"], old_known_quantity=old,
                      new_project_source=source, source_page=page, source_handles=handles,
                      graphic_evidence_class=cls, new_component_model=model, delta_known_quantity=delta,
                      new_blocked_components=list(blocked), new_release_state=state, portion=portion,
                      portion_state=portion_state, quantity_basis=basis, derivation_conditions=conditions,
                      why=why, OCCURRENCE_ID=cm["occurrence_id"], SUBFAMILY=cm["subfamily"], MARK=cm["mark"],
                      COMPONENT=cm["component"], ACCURATE_COMPONENT=cm["accurate_component"],
                      QUANTITY_KIND=cm["quantity_kind"], SPAN_INDEX=cm["span_index"], DIA_MM=cm["dia_mm"],
                      PRIMARY="Y" if primary else "N", DELTA_COUNT=delta_count, FACETS=facets or {},
                      EVIDENCE_IDS=list(evid), FORMULA=formula)
        recs.append(r)
        prov.append({"delta_id": r["DELTA_ID"], "baseline_component_id": cm["record_id"], "portion": portion,
                     "frozen_baseline": {"manifest": frozen["manifest"], "sha256": frozen["manifest_sha256"],
                                         "engine_commit_stamp": frozen["engine_commit_stamp"]},
                     "frozen_row": {k: cm[k] for k in ("state", "kg", "count", "dia_mm", "bar_count")},
                     "change_kind": change, "graphic_evidence_class": cls, "derivation_conditions": conditions,
                     "evidence_ids": list(evid), "source_page": page, "source_handles": handles,
                     "quantity_basis": basis, "formula": formula, "inputs": inputs, "delta_kg": delta,
                     "delta_count": delta_count, "round": ROUND, "unit_mass": UNIT_MASS})
        return r

    def no_change(cm, why="unchanged from frozen S6"):
        add(cm, DR.NO_CHANGE, "WHOLE_COMPONENT", GE.NO_GRAPHIC_EVIDENCE, "unchanged", cm["state"], "", why)

    order = {}
    for i, cm in enumerate(comps):
        order.setdefault(cm["occurrence_id"], i)
    for cm in comps:
        o, comp, st = cm["occurrence_id"], cm["component"], cm["state"]
        r = reg[o]
        sub = cm["subfamily"]
        in_lb = o in lb_occ
        key = (o, cm["span_index"])
        icon = r["mark"] in ev["str2_rows"]

        # ---------------- stirrup core path (single link / STR2 outer link)
        if comp == "STIRRUP_CORE_PATH" and in_lb:
            check(st == "BLOCKED_UNQUANTIFIED", f"{cm['record_id']} frozen blocked")
            b, h, did = section(o)
            d = float(cm["dia_mm"])
            core = LG.core_path_mm(b, h, c, d)
            tp = "STR2" if icon else "SINGLE"
            t = icons["STR2"] if icon else LG.topology_from_closed_links(1)
            cnt = stirrup_count_state.get(key)
            sid = f"{o}:SPAN{cm['span_index']}"
            blocked = [f"{cm['record_id']}:HOOK_EXTENSION"] + ([f"{cm['record_id']}:INNER_LINK"] if icon else [])
            topo_row = {"STIRRUP_SET_ID": sid, "OCCURRENCE_ID": o, "SUBFAMILY": sub, "MARK": cm["mark"],
                        "SPAN_INDEX": cm["span_index"], "TOPOLOGY": t["topology"], "LINKS": t["links"],
                        "LEGS": t["legs"], "TOPOLOGY_STATE": "SOURCE_FOUND_DERIVED",
                        "TOPOLOGY_SOURCE": ("SBT REMARKS icon STR2 (E-DXF-03)" if icon else
                                            "p.15 typical beam section + p.13 labelled sections (E-PDF-05, E-PDF-02)"),
                        "SECTION_B_MM": b, "SECTION_H_MM": h, "SECTION_SOURCE": did, "COVER_MM": c, "LINK_DIA_MM": d,
                        "OUTER_LINK_CORE_PATH_MM": core, "INNER_LINK": ("BLOCKED_UNQUANTIFIED (width, location and "
                                                                       "height not dimensioned; icon inner link drawn "
                                                                       "offset)" if icon else "NONE"),
                        "HOOKS": "SHAPE_FOUND_LENGTH_BLOCKED", "BEND_RADIUS": "NOT_IN_SOURCE (corners sharp)"}
            if cnt is None:
                add(cm, DR.TOPOLOGY_RECORDED, "CORE_PATH", GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY,
                    f"{t['topology']}: core path {core:.0f} mm per link derivable; count blocked", st,
                    GE.BLOCKED_UNQUANTIFIED, "the span's stirrup count is not released (reading-direction "
                    "ambiguity changes the diameter), so the mass stays blocked", blocked=blocked,
                    facets={"TOPOLOGY": t["topology"], "CORE_PATH_MM": core, "COUNT": "BLOCKED"},
                    evid=("E-PDF-05", "E-PDF-02", "E-DXF-03"), page="ST7757.pdf p.15 / p.13", source=P15)
                topo_row.update(COUNT="", COUNT_STATE="BLOCKED_UNQUANTIFIED", CORE_PATH_KG="",
                                STIRRUP_MASS_STATE="BLOCKED_UNQUANTIFIED")
            else:
                check(cnt["dia_mm"] == int(d), f"{key} count diameter = link diameter")
                kg = cnt["count"] * core / 1000.0 * kg_per_m(d)
                formula = (f"n x [2(b-2c-d) + 2(h-2c-d)] x d^2/162 = {cnt['count']} x [2({b:.0f}-{2 * c:.0f}-{d:.0f}) "
                           f"+ 2({h:.0f}-{2 * c:.0f}-{d:.0f})] mm x {d:.0f}^2/162 = {kg:.6f} kg")
                add(cm, DR.QUANTITY_RELEASED, "CORE_PATH", GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY,
                    (f"{t['topology']}: outer link core path released; inner link blocked" if icon else
                     f"{t['topology']}: core path released; hook extension blocked"), DR.LOWER_BOUND,
                    GE.DERIVED_LOWER_BOUND, "closed link bound to the section cover lines (b, h schedule; c note "
                    "22; d schedule); count released; corners sharp, hooks excluded", delta=kg,
                    basis=DR.BASIS_DERIVED, conditions=ALL_TRUE, blocked=blocked,
                    facets={"TOPOLOGY": t["topology"], "CORE_PATH_MM": core, "COUNT": cnt["count"],
                            "COUNT_ORIGIN": cnt["origin"], "PREMISES": list(LG.CORE_PATH_PREMISES)},
                    evid=("E-PDF-05", "E-PDF-02") + (("E-DXF-03",) if icon else ()),
                    page="ST7757.pdf p.15 / p.13" + (" / p.10 REMARKS" if icon else ""),
                    handles=("p15:S-REIN.D closed link; p13:S-REIN.D" + ("; ST7757.dxf STR2 block" if icon else "")),
                    source=P15, formula=formula,
                    inputs={"b_mm": b, "h_mm": h, "cover_mm": c, "d_mm": d, "count": cnt["count"],
                            "section_source": did, "cover_rule": rl["cover_rule"]})
                topo_row.update(COUNT=cnt["count"], COUNT_STATE="LOWER_BOUND (" + cnt["origin"] + ")",
                                CORE_PATH_KG=kg, STIRRUP_MASS_STATE="LOWER_BOUND (core path only)")
            add(cm, DR.PORTION_DECOMPOSITION, "HOOK_EXTENSION", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                "link hooks drawn (tick pair / corner hook); extension not printed (S6-07)",
                recs[-1]["NEW_RELEASE_STATE"], GE.SHAPE_FOUND_LENGTH_BLOCKED,
                "hook drawn, extension and angle not dimensioned", blocked=blocked, evid=("E-PDF-02", "E-PDF-05"))
            if icon:
                add(cm, DR.TOPOLOGY_RECORDED, "INNER_LINK", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                    "STR2 inner closed link: topology found (2 more legs); width, location and height not "
                    "dimensioned; no equal subdivision", recs[-1]["NEW_RELEASE_STATE"], GE.SHAPE_FOUND_LENGTH_BLOCKED,
                    "the icon is a REMARKS symbol: its inner rectangle is drawn offset "
                    f"{icons['STR2']['inner_level_offsets']} units from the outer link, so not even its legs are "
                    "bound to the cover lines (S6-06)", blocked=blocked, evid=("E-DXF-03",),
                    page="ST7757.pdf p.10 REMARKS", handles="ST7757.dxf block STR2")
            topo.append(topo_row)
            continue
        if comp == "STIRRUP_CORE_PATH":
            b = h = None
            topo.append({"STIRRUP_SET_ID": f"{o}:SPAN{cm['span_index']}", "OCCURRENCE_ID": o, "SUBFAMILY": sub,
                         "MARK": cm["mark"], "SPAN_INDEX": cm["span_index"],
                         "TOPOLOGY": (icons["STR2"]["topology"] if icon else LG.SINGLE_CLOSED_LINK),
                         "LINKS": 2 if icon else 1, "LEGS": 4 if icon else 2, "TOPOLOGY_STATE": "SOURCE_FOUND_DERIVED",
                         "TOPOLOGY_SOURCE": "occurrence blocked in S6 (unchanged)", "COUNT_STATE":
                         "BLOCKED_UNQUANTIFIED", "STIRRUP_MASS_STATE": "BLOCKED_UNQUANTIFIED (occurrence blocked)",
                         "INNER_LINK": "BLOCKED_UNQUANTIFIED" if icon else "NONE",
                         "HOOKS": "SHAPE_FOUND_LENGTH_BLOCKED"})
            no_change(cm, "occurrence still blocked in S6.1 (" + (occ_csv[o]["occurrence_blocking_reason"][:120] or
                                                                  "blocked type") + ")")
            continue

        # ---------------- stirrup counts released here
        if comp == "STIRRUP_COUNT" and key in count_release:
            check(st == "BLOCKED_UNQUANTIFIED", f"{cm['record_id']} frozen blocked")
            cr = count_release[key]
            add(cm, DR.QUANTITY_RELEASED, "WHOLE_COMPONENT", GE.NO_GRAPHIC_EVIDENCE,
                f"stirrup count {cr['count']} (lower bound, no +1)", DR.LOWER_BOUND, "",
                cr["basis"], basis=DR.BASIS_SCHEDULE, delta_count=cr["count"],
                facets={"COUNT": cr["count"], "DIA_MM": cr["dia_mm"], "READINGS": cr["readings"],
                        "FIRST_LAST_RULE": "NOT_STATED (no +1)"},
                evid=("E-DXF-07", "E-PDF-06") if o in B3_WITH_STAIR else (("E-PDF-06",) if o == B26 else ()),
                formula=cr["basis"])
            continue

        # ---------------- B3 WITH STAIR / B26 base longitudinal bars
        if o in released_occ and comp in ("TOP_MAIN", "BOTTOM_MAIN"):
            check(st == "BLOCKED_UNQUANTIFIED", f"{cm['record_id']} frozen blocked")
            n, d = int(cm["bar_count"]), int(cm["dia_mm"])
            did = section(o)[2]
            fld = defs[did]["fields"]["top" if comp == "TOP_MAIN" else "bottom"]
            check((fld["count"], fld["dia_mm"]) == (n, d), f"{cm['record_id']} = S1 schedule row")
            run = r["geometry"]["clear_face_to_face_m"]
            kg = n * run * kg_per_m(d)
            stair = o in B3_WITH_STAIR
            formula = f"n x clear run x d^2/162 = {n} x {run} m x {d}^2/162 = {kg:.6f} kg"
            add(cm, DR.QUANTITY_RELEASED, "STRAIGHT_RUN",
                GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                ("B3 schedule bar over the plan clear run (the p.16 stair-beam detail = B3 row, cranked)" if stair else
                 "B26 schedule bar over the clear run (the p.15 detail adds extras only)"),
                DR.LOWER_BOUND, GE.KNOWN_STRAIGHT_SEGMENT if not stair else GE.DERIVED_LOWER_BOUND,
                ("p.16 callouts 2Ø12 / 4Ø16 / 6Ø8/m equal the B3 row; the graphic gives identity and the cranked "
                 "shape only, the length is the schedule bar over the plan run" if stair else
                 "the planted-column detail does not change the schedule bars; length = schedule bar over the "
                 "clear run (S6 convention)"), delta=kg, basis=DR.BASIS_SCHEDULE,
                blocked=[f"{cm['record_id']}:{p}" for p in (("CRANK_EXCESS", "END_BENDS") if stair else ())],
                facets={"BINDING": "BOUND_VERIFIED, width MATCH", "COUNT": n, "DIA_MM": d, "RUN_M": run},
                evid=("E-PDF-06", "E-DXF-07") if stair else ("E-PDF-06",),
                page="ST7757.pdf p.16" if stair else "ST7757.pdf p.15",
                handles="ST7757.dxf 6B6-6B9, SBT B3 1E83" if stair else "ST7757.dxf SBT B26 1F80",
                source=("ST7757.pdf p.16 'TYPICAL DETAIL OF STAIR BEAM'" if stair else
                        "ST7757.pdf p.15 'BEAM CARRYING PLANTED COL. DETAIL'"), formula=formula,
                inputs={"count": n, "dia_mm": d, "clear_run_m": run, "schedule_row": did})
            if stair:
                add(cm, DR.PORTION_DECOMPOSITION, "CRANK_EXCESS", GE.GRAPHIC_NTS_OR_UNDIMENSIONED,
                    "inclined length beyond the plan run (beam follows the flight)", DR.LOWER_BOUND,
                    GE.BLOCKED_UNQUANTIFIED, "p.16 is N.T.S.; the flight rise / going over this beam is not "
                    "dimensioned for it", evid=("E-PDF-06",), page="ST7757.pdf p.16")
                add(cm, DR.PORTION_DECOMPOSITION, "END_BENDS", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                    "top bar turned down into the column at one end, bottom bar turned up with a hook at the other",
                    DR.LOWER_BOUND, GE.SHAPE_FOUND_LENGTH_BLOCKED, "end anchorage drawn, not dimensioned",
                    evid=("E-PDF-06",), page="ST7757.pdf p.16")
            continue

        # ---------------- B3 stair extra / B26 planted-column extra
        if o in B3_WITH_STAIR and comp == "OTHER_EXPLICIT_EXTRA":
            add(cm, DR.SEMANTIC_CORRECTION, "WHOLE_COMPONENT", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                "no stair-beam extra: the p.16 detail adds no bars", DR.NOT_APPLICABLE, "",
                "every p.16 callout equals the B3 schedule row (S6-14); no extra stair-beam steel (brief §12)",
                evid=("E-PDF-06", "E-DXF-07"), page="ST7757.pdf p.16")
            continue
        if o == B26 and comp == "OTHER_EXPLICIT_EXTRA":
            D = defs[section(o)[2]]["H_cm"] * 10.0
            w = col["width_along_beam_lower_bound_mm"]
            proj = 2 * D + w
            n, d = 4, 16
            kg = n * proj / 1000.0 * kg_per_m(d)
            formula = (f"COUNT_TOTAL x (2 x DEPTH + column width) x d^2/162 = {n} x (2 x {D:.0f} + {w:.0f}) mm x "
                       f"{d}^2/162 = {kg:.6f} kg")
            cond = dict(ALL_TRUE)
            blocked = [f"{cm['record_id']}:{p}" for p in ("CRANK_DIAGONAL_EXCESS", "END_HOOK_1", "END_HOOK_2")]
            add(cm, DR.QUANTITY_RELEASED, "STRAIGHT_PROJECTION", GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY,
                "PLANTED_COLUMN_EXTRA: 4 Ø16 (total), each a cranked bar running DEPTH past each column face; "
                "released over its horizontal projection only", DR.LOWER_BOUND, GE.DERIVED_LOWER_BOUND,
                "ends bound to the 'DEPTH' dimension (= schedule depth) past each column face; the two drawn bars "
                "carry one mark, so both ends repeat; a cranked bar is never shorter than its horizontal "
                "projection; row allocation does not change the projection", delta=kg, basis=DR.BASIS_DERIVED,
                conditions=cond, blocked=blocked,
                facets={"COUNT_TOTAL": n, "DIA_MM": d, "DEPTH_MM": D, "COLUMN_WIDTH_LB_MM": w,
                        "ROW_ALLOCATION": "NOT_ESTABLISHED (one '4Ø16' leader touches both bars; not 2 + 2 by "
                                          "inference) - does not change the projection",
                        "EXTRA_STIRRUPS": "10 cm under the column = B26's own 10/m: no extra count"},
                evid=("E-PDF-06",), page="ST7757.pdf p.15",
                handles="p15 'BEAM CARRYING PLANTED COL. DETAIL' strokes; S1 column " + col["column_id"],
                source="ST7757.pdf p.15 'BEAM CARRYING PLANTED COL. DETAIL'", formula=formula,
                inputs={"count_total": n, "dia_mm": d, "depth_mm": D, "column": col})
            add(cm, DR.PORTION_DECOMPOSITION, "CRANK_DIAGONAL_EXCESS", GE.GRAPHIC_NTS_OR_UNDIMENSIONED,
                "diagonal under the column longer than its projection", DR.LOWER_BOUND, GE.BLOCKED_UNQUANTIFIED,
                "crank drop and angle not dimensioned", evid=("E-PDF-06",), page="ST7757.pdf p.15")
            for p in ("END_HOOK_1", "END_HOOK_2"):
                add(cm, DR.PORTION_DECOMPOSITION, p, GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, "hooked bar end drawn",
                    DR.LOWER_BOUND, GE.SHAPE_FOUND_LENGTH_BLOCKED, "hook drawn, not dimensioned",
                    evid=("E-PDF-06",), page="ST7757.pdf p.15")
            continue

        # ---------------- CB end-support top-bar legs: recorded, not released
        if sub == "CONTINUOUS_BEAM" and comp in ("HOOK_1", "HOOK_2") and occ_csv[o]["occurrence_state"] == \
                "LOWER_BOUND":
            b, h, did = section(o)
            cond = dict(ALL_TRUE, **{GE.NO_CONTRADICTING_PROJECT_SOURCE: False})
            ok, why_not = GE.may_quantify(GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, cond)
            check(not ok, "CB end leg must not release while the bar role is in conflict")
            add(cm, DR.TOPOLOGY_RECORDED, "WHOLE_COMPONENT", GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY,
                "end-support top bar turns down in a 90° leg to the bottom-bar level (3 typicals); leg geometry "
                f"derivable = h - 2c - 2 d_link - (d_top + d_bottom)/2 with h = {h:.0f} mm, c = {c:.0f} mm",
                st, GE.SHAPE_FOUND_LENGTH_BLOCKED,
                "bar role in conflict (Q2): the frames put the leg on the per-span top bar, the typical on a "
                "separate unlabelled end-support bar; count and diameter of the leg bar are not candidate-"
                f"invariant -> {why_not}; bend radius, end termination and development stay blocked",
                conditions=cond, blocked=[f"{cm['record_id']}:LEG_MASS"],
                facets={"LEG_SHAPE": "SOURCE_FOUND_DERIVED (E-PDF-04)", "BAR_ROLE": "CONFLICT (Q2)",
                        "COUNT_DIAMETER_INVARIANT": False, "LEG_MASS": "BLOCKED_UNQUANTIFIED",
                        "SECTION_H_MM": h, "COVER_MM": c},
                evid=("E-PDF-04", "E-DXF-06"), page="ST7757.pdf pp.11-12", handles="p11/p12:S-REIN.D end legs")
            continue
        no_change(cm)
    return comps, recs, prov, topo, count_release, invariance_tested, lb_occ


def unresolved(recs):
    frozen_unres = _rows(S6 / "SUPERSTRUCTURE_BEAM_UNRESOLVED.csv")
    by_cid = defaultdict(list)
    for r in recs:
        by_cid[r["BASELINE_COMPONENT_ID"]].append(r)
    out = []
    for u in frozen_unres:
        rs = by_cid.get(u["record_id"], [])
        prim = next((r for r in rs if r["PRIMARY"] == "Y"), None)
        if prim is None or prim["CHANGE_KIND"] == DR.NO_CHANGE:
            status, st = "OPEN (unchanged)", u["state"]
        elif prim["NEW_RELEASE_STATE"] == DR.NOT_APPLICABLE:
            status, st = "CLOSED (not applicable)", DR.NOT_APPLICABLE
        elif prim["CHANGE_KIND"] == DR.QUANTITY_RELEASED:
            status, st = "NARROWED (lower bound released; named facets still open)", DR.LOWER_BOUND
        else:
            status, st = "OPEN (facet recorded)", prim["NEW_RELEASE_STATE"]
        out.append({"UNRESOLVED_ID": f"S6.1-U{len(out) + 1:04d}", "ORIGIN": "CARRIED_FROM_S6",
                    "BASELINE_COMPONENT_ID": u["record_id"], "OCCURRENCE_ID": u["occurrence_id"], "MARK": u["mark"],
                    "COMPONENT": u["component"], "PORTION": "WHOLE_COMPONENT", "S6_STATE": u["state"],
                    "S6_1_STATE": st, "S6_1_STATUS": status, "WHAT_IS_MISSING": u["what_is_missing"],
                    "QUESTION_ID": u["question_id"]})
    for r in recs:
        if r["PRIMARY"] == "N" and r["PORTION_STATE"] in (GE.SHAPE_FOUND_LENGTH_BLOCKED, GE.BLOCKED_UNQUANTIFIED):
            out.append({"UNRESOLVED_ID": f"S6.1-U{len(out) + 1:04d}", "ORIGIN": "NEW_IN_S6_1",
                        "BASELINE_COMPONENT_ID": r["BASELINE_COMPONENT_ID"], "OCCURRENCE_ID": r["OCCURRENCE_ID"],
                        "MARK": r["MARK"], "COMPONENT": r["COMPONENT"], "PORTION": r["PORTION"], "S6_STATE": "",
                        "S6_1_STATE": r["PORTION_STATE"], "S6_1_STATUS": "OPEN (new named portion)",
                        "WHAT_IS_MISSING": r["WHY"], "QUESTION_ID": ""})
    return out


CHANGELOG = """# S6.1 CHANGELOG: superstructure beam rebar delta release over frozen S6

**Round:** `S6.1` · **Policy:** `{policy}` · **Frozen baseline:** `{manifest}` (sha `{msha12}`, stamp `{stamp}`)
**Preceded by:** S4.1 freeze (`{s41}`) · **Built by** `build_superstructure_beam_rebar_s6_1.py` (blind, byte-identical rebuild)

S6 is unchanged. Every S6 code, input and output hash was checked first, and no S6 file was written. This file is
BASELINE + DELTA.

## Headline

| | kg |
|---|---|
| Frozen S6 known | {frozen_known:.4f} |
| Longitudinal delta: B3 WITH STAIR + B26 base bars | {d_long:.4f} |
| Planted-column extra (B26, horizontal projection) | {d_extra:.4f} |
| Stirrup core-path delta | {d_core:.4f} |
| **S6.1 known** | **{new_known:.4f}** |

Every released quantity is a LOWER_BOUND. Nothing was raised to VERIFIED.

## What was released

1. **Single closed link: {n_single} stirrup sets.**
   - Source: the p.15 typical beam section and the p.13 labelled sections draw one closed link.
   - CORE_PATH = 2(b-2c-d) + 2(h-2c-d), with c = 25 mm (note 22), b and h from the schedule row, and d the
     scheduled link. It is multiplied by the released count.
   - Class `GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY`, all four rule-B conditions true.
   - Hook extension stays `SHAPE_FOUND_LENGTH_BLOCKED`.
2. **STR2: {n_str2} stirrup sets.**
   - Topology SOURCE_FOUND: 2 links, 4 legs. Only the outer link's core path is released.
   - The inner link stays blocked: width, location and height. The REMARKS icon draws the inner rectangle offset
     {offset} units from the outer one, so it is a symbol, not a section, and no leg of it is bound to the cover
     lines. No equal subdivision was used.
3. **New stirrup counts: {new_counts}.**
   - CB7: both surviving reading directions give the same diameter, rate, span and count.
   - B3 / B26: ceil(rate x clear run), no +1.
   - CB13 was tested the same way and fails: reversing the reading direction swaps Ø8 / Ø10, so its counts stay
     blocked.
4. **B3 WITH STAIR ({b3_occ}).**
   - The p.16 callouts equal the B3 row, so the base components release: 2Ø12 top and 4Ø16 bottom over the plan
     clear run, 6Ø8/m count and core path.
   - The plan run is a lower bound of the cranked bar. CRANK_EXCESS and END_BENDS stay blocked.
   - The stair extra becomes NOT_APPLICABLE: the detail adds no bars.
5. **B26 ({b26}).**
   - BASE_B26: 6Ø14 top and 19Ø18 bottom over the clear run, 10Ø10/m count {b26_count}, and the STR2 outer-link
     core path.
   - PLANTED_COLUMN_EXTRA: COUNT_TOTAL 4, Ø16. Each bar runs DEPTH ({depth:.0f} mm) past each column face, so
     the released lower bound is the horizontal projection 2 x DEPTH + {colw:.0f} mm (the smaller planted-column
     side), = {extra_kg:.4f} kg.
   - Row allocation is not inferred (not 2 + 2). It does not change the projection.
   - Crank excess and hooks stay blocked.
   - Side bars stay blocked (S6-11).

## What was recorded but not released

- **CB end-support top-bar legs ({n_legs} components).**
  - The 90° leg to the bottom-bar level is SOURCE_FOUND, and its geometry is derivable.
  - But the bar that carries it is in conflict (Q2): the frames put the leg on the per-span top bar, the typical
    on a separate, unlabelled end-support bar.
  - Its count and diameter are therefore not candidate-invariant, so rule B fails (NO_CONTRADICTING_PROJECT_SOURCE)
    and the leg carries no kg.
- **Not resolved:** CB3 against B3 WITH STAIR, the five width conflicts, the CB4 / CB5 / CB8 spans, the B1
  candidate bindings, the curved and CA beams (brief §20).

## Counts

- Delta rows: {n_rows}, covering all {n_frozen} frozen components.
- Stirrup topology rows: {n_topo}.
- Unresolved: {n_unres} rows ({n_carried} carried from S6 with their S6.1 status, {n_new} new named portions).
- Blocked hook / path portions remaining: {blocked_portions}.

## Files

| File | Content |
|---|---|
| `S6_1_DELTA_COMPONENTS.csv` | one row per frozen component (plus named portions), with all brief §2 fields |
| `S6_1_STIRRUP_TOPOLOGY.csv` | one row per stirrup set: topology, legs, section, core path, count, mass state |
| `S6_1_RELEASE_SUMMARY.json` | baseline, deltas, new totals, counts, conservation, flags |
| `S6_1_UNRESOLVED.csv` | carried S6 rows with their S6.1 status, plus new blocked portions |
| `S6_1_PROVENANCE.jsonl` | per delta row: frozen row, formula, inputs, evidence ids, class, conditions |
| `S6_1_FREEZE_MANIFEST.json` | S6.1 frozen before S5.1 |
"""


def main():
    frozen = DR.verify_frozen(S6 / "S6_FREEZE_MANIFEST.json", ROOT)
    s41 = DR.verify_frozen(S41 / "S4_1_FREEZE_MANIFEST.json", ROOT)
    check(_j(S41 / "S4_1_FREEZE_MANIFEST.json")["state"] == "FROZEN_BEFORE_S6_1", "S4.1 frozen before S6.1")
    ev = evidence()
    icons = link_icons()
    rl = rules()
    defs = definitions()
    col = planted_column()
    reg_items = {r["ITEM_ID"]: r["TERMINAL_STATE"] for r in _rows(SRD / "02_UNRESOLVED_MASTER_REGISTER.csv")}
    for i in ("S6-04", "S6-05", "S6-14", "S6-15", "S6-02"):
        check(reg_items[i] == "SOURCE_FOUND_DERIVED", f"SRD {i} found")
    for i in ("S6-06", "S6-07", "S6-01"):
        check(reg_items[i] == "SOURCE_EXPECTED_NOT_LOCATED", f"SRD {i} not located")
    check(reg_items["S6-19"] == "SOURCE_CONFLICT", "CB3 vs B3 stays a conflict")
    s6 = _j(S6 / "SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json")
    frozen_known = s6["known_source_derived_superstructure_beam_rebar_kg"]
    comps, recs, prov, topo, count_release, inv_tested, lb_occ = build(frozen, ev, icons, rl, defs, col)
    new_known = sum(r["NEW_KNOWN_QUANTITY"] for r in recs)
    cons = DR.conservation(frozen_known, recs, new_known)
    check(cons["all_pass"], f"conservation {cons}")
    check({r["BASELINE_COMPONENT_ID"] for r in recs} == {c["record_id"] for c in comps}, "every component covered")
    check(sum(1 for r in recs if r["PRIMARY"] == "Y") == len(comps), "one primary row per component")

    def dsum(pred):
        return sum(r["DELTA_KNOWN_QUANTITY"] for r in recs if pred(r))
    d_core = dsum(lambda r: r["PORTION"] == "CORE_PATH")
    d_long = dsum(lambda r: r["PORTION"] == "STRAIGHT_RUN")
    d_extra = dsum(lambda r: r["PORTION"] == "STRAIGHT_PROJECTION")
    check(abs(d_core + d_long + d_extra - cons["delta_known"]) < 1e-9, "delta split")
    rel_core = [r for r in recs if r["PORTION"] == "CORE_PATH" and r["CHANGE_KIND"] == DR.QUANTITY_RELEASED]
    n_str2 = sum(1 for r in rel_core if r["FACETS"]["TOPOLOGY"] == LG.STR2)
    n_single = len(rel_core) - n_str2
    comp_state = {r["BASELINE_COMPONENT_ID"]: r["NEW_RELEASE_STATE"] for r in recs if r["PRIMARY"] == "Y"}
    old_state = {c["record_id"]: c["state"] for c in comps}
    transitions = Counter(f"{old_state[k]} -> {v}" for k, v in comp_state.items() if old_state[k] != v)
    occ_new = {}
    for o in sorted({c["occurrence_id"] for c in comps}):
        occ_new[o] = "LOWER_BOUND" if o in lb_occ else "BLOCKED"
    b3 = {o: {r["COMPONENT"] + (":" + r["PORTION"] if r["PRIMARY"] == "N" else ""): r["NEW_KNOWN_QUANTITY"]
              for r in recs if r["OCCURRENCE_ID"] == o and r["CHANGE_KIND"] != DR.NO_CHANGE}
          for o in B3_WITH_STAIR}
    b26_rows = [r for r in recs if r["OCCURRENCE_ID"] == B26 and r["CHANGE_KIND"] != DR.NO_CHANGE]
    b26_base = sum(r["DELTA_KNOWN_QUANTITY"] for r in b26_rows if r["COMPONENT"] != "OTHER_EXPLICIT_EXTRA")
    b26_extra = sum(r["DELTA_KNOWN_QUANTITY"] for r in b26_rows if r["COMPONENT"] == "OTHER_EXPLICIT_EXTRA")
    extra_row = next(r for r in b26_rows if r["PORTION"] == "STRAIGHT_PROJECTION")
    legs = [r for r in recs if r["COMPONENT"] in ("HOOK_1", "HOOK_2") and r["CHANGE_KIND"] == DR.TOPOLOGY_RECORDED]
    blocked_portions = dict(sorted(Counter(r["PORTION"] for r in recs if r["PRIMARY"] == "N" and r["PORTION_STATE"]
                                           in (GE.SHAPE_FOUND_LENGTH_BLOCKED, GE.BLOCKED_UNQUANTIFIED)).items()))
    blocked_portions["CB_END_LEG_MASS"] = len(legs)
    new_counts = {f"{k[0]}:SPAN{k[1]}": v["count"] for k, v in sorted(count_release.items())}
    unres = unresolved(recs)
    ctx = {"ROUND": ROUND, "POLICY": POLICY, "ENGINE_COMMIT": f"{frozen['engine_commit_stamp']}+delta:"
                                                             f"{code_digest()[:16]}",
           "FROZEN_BASELINE": frozen, "PRECEDING_FREEZE_S4_1": s41, "DRAWING_SHA": DXF_SHA, "UNIT_MASS": UNIT_MASS,
           "COVER": rl}
    summary = {
        "round": ROUND, "policy": POLICY, "context": ctx, "graphic_evidence_policy": GE.policy_record(),
        "frozen_s6": {"known_kg": frozen_known, "simple_lower_bound_kg": s6["SIMPLE_BEAM_LOWER_BOUND_KNOWN_KG"],
                      "cb_lower_bound_kg": s6["CONTINUOUS_BEAM_LOWER_BOUND_KNOWN_KG"],
                      "stirrup_count_known": s6["STIRRUP_COUNT_KNOWN"], "stirrup_mass_known": s6["STIRRUP_MASS_KNOWN"]},
        "delta_known_kg": cons["delta_known"],
        "delta_by_kind_kg": {"longitudinal_base_bars": d_long, "planted_column_extra": d_extra,
                             "stirrup_core_path": d_core},
        "s6_1_known_kg": new_known,
        "s6_1_verified_kg": 0.0,
        "stirrup_core_path_sets_released": {"single_link": n_single, "str2_outer_link": n_str2,
                                            "total": len(rel_core)},
        "stirrup_core_path_sets_topology_only": sum(1 for r in recs if r["PORTION"] == "CORE_PATH" and
                                                    r["CHANGE_KIND"] == DR.TOPOLOGY_RECORDED),
        "new_stirrup_counts": new_counts, "new_stirrup_count_total": sum(new_counts.values()),
        "cb_invariance_tested": inv_tested,
        "b3_with_stair": {"occurrences": list(B3_WITH_STAIR), "released_kg_by_component": b3,
                          "stair_extra": "NOT_APPLICABLE (detail adds no bars)",
                          "blocked": ["CRANK_EXCESS", "END_BENDS", "HOOK_1/2", "DEVELOPMENT_1/2"]},
        "b26": {"occurrence": B26, "base_kg": b26_base, "planted_column_extra_kg": b26_extra,
                "planted_column_extra": extra_row["FACETS"], "planted_column": col,
                "blocked": ["CRANK_DIAGONAL_EXCESS", "END_HOOK_1/2", "INNER_LINK", "SIDE_REBAR", "HOOK / DEV"]},
        "cb_end_legs": {"recorded": len(legs), "released": 0,
                        "why": "bar role conflict Q2: count / diameter of the leg bar not candidate-invariant"},
        "str2_icon": icons["STR2"], "str3_icon": icons["str3"],
        "occurrences_by_state": dict(sorted(Counter(occ_new.values()).items())),
        "occurrences_released_in_s6_1": sorted(set(B3_WITH_STAIR) | {B26}),
        "components_by_state": dict(sorted(Counter(comp_state.values()).items())),
        "state_transitions": dict(sorted(transitions.items())),
        "remaining_blocked_portions": blocked_portions,
        "unresolved": {"rows": len(unres), "carried_from_s6": sum(1 for u in unres if u["ORIGIN"] ==
                                                                  "CARRIED_FROM_S6"),
                       "new_portion_rows": sum(1 for u in unres if u["ORIGIN"] == "NEW_IN_S6_1"),
                       "by_status": dict(sorted(Counter(u["S6_1_STATUS"] for u in unres).items()))},
        "not_resolved_brief_20": ["CB3 vs B3 WITH STAIR (S6-19)", "B6 / B21 / B29 / CB2 / CB10 widths (S6-17)",
                                  "CB4 / CB5 / CB8 spans (S6-18)"],
        "delta_rows": len(recs), "frozen_components": len(comps), "conservation": cons,
        "flags": {"frozen_outputs_changed": False, "plotted_scale_used": False, "kg_from_shape_only_graphic": False,
                  "verified_created": False, "equal_inner_link_subdivision": False, "pre_s7_started": False,
                  "references_read": []},
        "headline": "S6.1 KNOWN SUPERSTRUCTURE BEAM REBAR = FROZEN S6 KNOWN + LOWER-BOUND DELTA"}

    fields = ["DELTA_ID", "CHANGE_KIND", "FROZEN_BASELINE", "BASELINE_COMPONENT_ID", "OCCURRENCE_ID", "SUBFAMILY",
              "MARK", "COMPONENT", "ACCURATE_COMPONENT", "QUANTITY_KIND", "SPAN_INDEX", "PORTION", "PRIMARY",
              "OLD_STATE", "OLD_KNOWN_QUANTITY", "NEW_PROJECT_SOURCE", "SOURCE_PAGE", "SOURCE_HANDLES",
              "GRAPHIC_EVIDENCE_CLASS", "NEW_COMPONENT_MODEL", "PORTION_STATE", "QUANTITY_BASIS",
              "DELTA_KNOWN_QUANTITY", "NEW_KNOWN_QUANTITY", "DELTA_COUNT", "NEW_BLOCKED_COMPONENTS",
              "NEW_RELEASE_STATE", "DIA_MM", "FACETS", "EVIDENCE_IDS", "FORMULA", "WHY"]
    _csv(HERE / "S6_1_DELTA_COMPONENTS.csv", recs, fields)
    topo_fields = ["STIRRUP_SET_ID", "OCCURRENCE_ID", "SUBFAMILY", "MARK", "SPAN_INDEX", "TOPOLOGY", "LINKS", "LEGS",
                   "TOPOLOGY_STATE", "TOPOLOGY_SOURCE", "SECTION_B_MM", "SECTION_H_MM", "SECTION_SOURCE", "COVER_MM",
                   "LINK_DIA_MM", "OUTER_LINK_CORE_PATH_MM", "INNER_LINK", "HOOKS", "BEND_RADIUS", "COUNT",
                   "COUNT_STATE", "CORE_PATH_KG", "STIRRUP_MASS_STATE"]
    _csv(HERE / "S6_1_STIRRUP_TOPOLOGY.csv", topo, topo_fields)
    _csv(HERE / "S6_1_UNRESOLVED.csv", unres, list(unres[0].keys()))
    with open(HERE / "S6_1_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for p in prov:
            f.write(json.dumps(p, sort_keys=True, ensure_ascii=False) + "\n")
    _json(HERE / "S6_1_RELEASE_SUMMARY.json", summary)
    (HERE / "S6_1_CHANGELOG.md").write_text(CHANGELOG.format(
        policy=POLICY, manifest=frozen["manifest"], msha12=frozen["manifest_sha256"][:12],
        stamp=frozen["engine_commit_stamp"], s41=s41["manifest_sha256"][:12], frozen_known=frozen_known,
        d_long=d_long, d_extra=d_extra, d_core=d_core, new_known=new_known, n_single=n_single, n_str2=n_str2,
        offset=icons["STR2"]["inner_level_offsets"],
        new_counts=", ".join(f"{k} = {v}" for k, v in new_counts.items()),
        b3_occ=" / ".join(B3_WITH_STAIR), b26=B26, b26_count=new_counts.get(f"{B26}:SPAN1"),
        depth=extra_row["FACETS"]["DEPTH_MM"], colw=extra_row["FACETS"]["COLUMN_WIDTH_LB_MM"], extra_kg=d_extra,
        n_legs=len(legs), n_rows=len(recs), n_frozen=len(comps), n_topo=len(topo), n_unres=len(unres),
        n_carried=summary["unresolved"]["carried_from_s6"], n_new=summary["unresolved"]["new_portion_rows"],
        blocked_portions=", ".join(f"{k} {v}" for k, v in blocked_portions.items())), encoding="utf-8")
    manifest = {"round": ROUND, "state": "FROZEN_BEFORE_S5_1", "baseline_round": "S6", "frozen_baseline": frozen,
                "preceding_freeze": s41, "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {i: _sha(ROOT / i) for i in INPUTS}, "drawing_sha256": DXF_SHA,
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "engine_commit_stamp": ctx["ENGINE_COMMIT"],
                "references_read_before_freeze": [],
                "rule": "S6.1 is a delta over frozen S6; a correction needs a new delta round, never an edit of S6 "
                        "or of these outputs"}
    _json(HERE / "S6_1_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({k: summary[k] for k in ("delta_known_kg", "delta_by_kind_kg", "s6_1_known_kg",
                                              "stirrup_core_path_sets_released", "stirrup_core_path_sets_topology_only",
                                              "new_stirrup_counts", "cb_end_legs", "occurrences_by_state",
                                              "components_by_state", "remaining_blocked_portions")}, indent=1))
    print(json.dumps({"b3": summary["b3_with_stair"]["released_kg_by_component"], "b26_base": b26_base,
                      "b26_extra": b26_extra}, indent=1))


if __name__ == "__main__":
    main()
