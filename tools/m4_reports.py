"""M4 REPORTS - the registers an M4 generic-route run adds to the BOQ, for any project (no project data here).

    locate(D, arch)               component id -> {sheet, x_m, y_m, poly}: where each component sits on its sheet
    missing_register(D, items, reg, arch, prev_reg)
                                  one row per component without a full bar quantity: family, storey, location,
                                  geometry, concrete (or its exposure), whether the component's existence or
                                  section is itself unresolved, the evidence the engine had, the missing roles, the
                                  detail a person must supply, the provisional kg that exists, the unknowns, and the
                                  state in a previous run (prev_reg) when given
    missing_summary(rows)         counts and the concrete volume without bar data, by family / storey / role /
                                  existence (counts, never kg: a missing bar quantity is never estimated by ratio)
    unresolved_concrete(D, items, arch)
                                  every UNRESOLVED concrete item, numbered per sheet for the exception overlay, with
                                  its class, location, exposure, the alternatives the engine found and what would
                                  settle it
    cb_lines(D) / cb_bars(D)      the continuous-beam lines (span matching) and their physical bar groups
    gb_exterior(D, items, arch)   per perimeter ground beam: architectural class, wall cover, inside level, case
    lintels(arch, items)          every architectural opening and what the lintel rule made of it
    slab_faces(D, items)          per slab panel: gross area, member overlap, net area, thickness and its basis
    ocr_items(items)              the quantities built on OCR-derived (unreviewed) evidence
    conflicts(risk)               the coverage-risk rows that are source conflicts (two readings of the drawing)
Every row carries ids and engine marks only; no text from the drawing is reproduced.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

POLICY_ID = "M4_REPORTS_V1"
MISSING = ("MISSING_DATA", "PARTIAL_MISSING")
CB_UNMAPPED = ("AMBIGUOUS_SPANS", "SPAN_COUNT_CONFLICT", "SPAN_LENGTH_CONFLICT", "NO_PRINTED_SPANS")
SAFE_MARK = re.compile(r"^[A-Z]{1,4}\d{0,3}[A-Z]?$")
CONFLICT_KINDS = ("GB_EXTERIOR_SHALLOWER_THAN_CLASS", "GB_PERIMETER_NO_WALL", "SLAB_THICKNESS_SHEET_TAG_VS_PROJECT_DEFAULT",
                  "BEAM_UNLABELLED_SPAN_ACROSS_SUPPORT", "FOOTING_LABEL_TYPE_CONFLICT", "SCHEDULE_DUPLICATE_MARK",
                  "MARK_AMBIGUOUS", "BAND_MULTIPLE_MARKS", "STAIR_ZONE_PARTIAL", "STAIR_FLIGHT_EXCEEDS_ZONE",
                  "LINTEL_OPENING_ABOVE_SCHEDULE", "BLINDING_OVERLAP_NOT_ESTABLISHED", "CB_SPAN_MARK_CONFLICT")
UNRESOLVED_CLASS = {
    "UNBOUND": ("MISSING_LABEL", "a mark on the band or a schedule row for its drawn width"),
    "MULTIPLE_MARKS": ("SOURCE_AMBIGUITY", "which of the marks on the band applies"),
    "AMBIGUOUS": ("SOURCE_AMBIGUITY", "which mark applies"),
    "UNLABELLED_SPAN_ACROSS_SUPPORT": ("SOURCE_AMBIGUITY", "a label on the span, or a statement that the neighbour's "
                                                           "section continues across the support"),
    "NECK_SECTION_OR_FOOTING": ("MISSING_SOURCE", "the neck section in the column schedule, or the footing under it"),
    "TYPE_NOT_IN_SCHEDULE": ("MISSING_SOURCE", "a schedule row for the column type"),
    "SLAB_STAIR_ZONE": ("NOT_SLAB", "the stair section (waist, risers) - the cell is a stair, not slab"),
    "SLAB_CELL_FREE_COLUMNS": ("SOURCE_AMBIGUITY", "whether the cell is slab, a void or a court (free columns inside)"),
    "LINTEL_NEED_UNDER_BEAM": ("NEED_UNRESOLVED", "the head height against the beam soffit: masonry between them "
                                                  "needs a lintel"),
    "LINTEL_PARTIAL_BEAM": ("NEED_UNRESOLVED", "the beam covers part of the opening: lintel extent"),
    "STAIR_WAIST_NOT_PRINTED": ("MISSING_SOURCE", "the stair waist thickness"),
    "GB_CLASS_WIDTH_MISMATCH": ("MISSING_SOURCE", "a typical ground-beam class at the drawn width"),
    "NO_SCHEDULE_DEPTH": ("MISSING_SOURCE", "the depth of the scheduled mark"),
    "UNTAGGED_SPAN": ("MISSING_LABEL", "a label on the span"),
}
DETAIL_FOR_ROLE = {
    "CB_TOP_THROUGH": "top bars running through the continuous beam (schedule column or typical continuous-beam "
                      "detail)",
    "CB_SUPPORT_TOP": "support top bars at the named support (schedule cell is empty)",
    "CB_BOTTOM": "bottom bars of the span",
    "CB_STIRRUP": "stirrups of the span",
    "LINKS": "link notation of the typical detail for the band's class",
    "SIDE": "side bars of the typical detail",
    "ALL": "",
}


def _mark(src):
    m = re.search(r"; mark (\S+) ", src or "")
    return m.group(1) if m and SAFE_MARK.match(m.group(1)) else ""


def _centroid(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def locate(D, arch=None):
    u = D["unit_m"]
    out = {}
    for sid, rec in D["sheets"].items():
        role, st = rec["sheet"]["role"], rec["sheet"]["storey"]
        fam = "GROUND_BEAMS" if role == "GROUND_BEAM_PLAN" else "BEAMS"
        for b in rec.get("beams", []):
            out[f"{fam}:{st}:{b['band_id']}"] = {"sheet": sid, "poly": b["polygon"]}
        for b in (rec.get("straps") or {}).get("bands", []):
            if b.get("polygon"):
                out[f"GROUND_BEAMS:FOUNDATION:{b['band_id']}"] = {"sheet": sid, "poly": b["polygon"]}
        sfam = "GROUND_SLAB" if role == "GROUND_BEAM_PLAN" else "SLABS"
        for f in (rec.get("slab") or {}).get("faces", []):
            out[f"{sfam}:{st}:{f['face_id']}"] = {"sheet": sid, "poly": f["polygon"]}
            out[f"STAIRS:{st}:{f['face_id']}"] = {"sheet": sid, "poly": f["polygon"]}
        for f in rec.get("footings", []):
            if f.get("box"):
                b = f["box"]
                out[f["member_id"]] = {"sheet": sid, "poly": [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]}
    for st, L in ((arch or {}).get("lintels") or {}).items():
        reg = L.get("registration") or {}
        slab = next((s for s, r in D["sheets"].items() if r["sheet"]["role"] == "SLAB_PLAN" and
                     r["sheet"]["storey"] == st), None)
        if reg.get("state") != "REGISTERED" or slab is None:
            continue
        for op in L["openings"]:
            c = (op["centre"][0] + reg["dx"], op["centre"][1] + reg["dy"])
            out[f"LINTELS:{st}:{op['opening_id']}"] = {"sheet": slab, "poly": [c]}
    res = {}
    for cid, v in out.items():
        x, y = _centroid(v["poly"])
        res[cid] = {"sheet": v["sheet"], "x_m": round(x * u, 3), "y_m": round(y * u, 3), "poly": v["poly"]}
    return res


def _loc(cid, loc, u):
    if cid in loc:
        return loc[cid]
    m = re.search(r":(SH\d+):.*@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", cid)      # column / footing ids carry x,y
    if m:
        x, y = float(m.group(2)), float(m.group(3))
        return {"sheet": m.group(1), "x_m": round(x * u, 3), "y_m": round(y * u, 3), "poly": [(x, y)]}
    return {"sheet": "", "x_m": None, "y_m": None, "poly": []}


def _geometry(dims):
    d = dims or {}
    keys = ("width_m", "length_m", "clear_length_m", "depth_m", "net_plan_m2", "area_m2", "t_m", "section_m",
            "height_m", "opening_m", "wall_t_m", "D_m", "schedule_m")
    return "; ".join(f"{k}={d[k]}" for k in keys if d.get(k) is not None)


def missing_register(D, items, reg, arch=None, prev_reg=None):
    u = D["unit_m"]
    loc = locate(D, arch)
    conc = defaultdict(list)
    steel = defaultdict(list)
    for i in items:
        (conc if i["trade"] == "CONCRETE" else steel)[i["component_id"]].append(i)
    cb = {}
    for rec in D["sheets"].values():
        for ln in rec.get("cb_lines", []):
            for pid in ln["pieces"]:
                cb[pid] = ln
    prev = {r["COMPONENT_ID"]: r["REBAR_STATE"] for r in (prev_reg or [])}
    rows = []
    for r in reg:
        if r["REBAR_STATE"] not in MISSING:
            continue
        cid = r["COMPONENT_ID"]
        cs = conc.get(cid, [])
        c = next((i for i in cs if i["category"] in ("PROVISIONAL", "VERIFIED")), cs[0] if cs else None)
        ss = steel.get(cid, [])
        roles = sorted({i["item_id"].split(":")[-1] for i in ss if i["category"] == "UNRESOLVED"})
        roles = [re.sub(r"\d+$", "", x) if x.startswith("CB_SUPPORT_TOP") else x for x in roles]
        roles = sorted(set(roles)) or ["ALL"]
        kg = [sum(i[k] or 0.0 for i in ss if i["category"] == "PROVISIONAL") for k in ("low", "base", "high")]
        band = cid.split(":")[-1]
        line = cb.get(band) if r["FAMILY"] == "BEAMS" else None
        if c and c["category"] == "UNRESOLVED":
            existence = "NEED_UNRESOLVED" if c["blocker"].startswith("LINTEL") else "SECTION_UNRESOLVED"
        else:
            existence = "MEASURED" if c else "NO_CONCRETE_ITEM"
        ev = []
        if c and _mark(c["source"]):
            ev.append(f"mark {_mark(c['source'])}")
        if line:
            ev.append(f"continuous-beam line {line['line_id']} ({line['state']})")
        det = sorted({m.group(1) for i in ss for m in [re.search(r"typical detail (\S+)", i.get("source") or "")]
                      if m})
        if det:
            ev.append("typical detail " + ",".join(det))
        if "schedule" in (r["REASON"] or "") and not ev:
            ev.append("schedule (no row for this member)")
        need = [DETAIL_FOR_ROLE.get(x, x) for x in roles if DETAIL_FOR_ROLE.get(x, x)]
        if roles == ["ALL"]:
            need = [UNRESOLVED_CLASS.get(c["blocker"], ("", ""))[1] if c and c["category"] == "UNRESOLVED" else
                    r["REASON"]]
            if line and line["state"] in CB_UNMAPPED:
                need = [f"a span sequence for {line['mark']} that matches the drawn spans of line {line['line_id']} "
                        f"({line['state']}): bars are per span"]
        loc_ = _loc(cid, loc, u)
        rows.append({"COMPONENT_ID": cid, "FAMILY": r["FAMILY"], "STOREY": r["STOREY"], "SHEET": loc_["sheet"],
                     "X_M": loc_["x_m"], "Y_M": loc_["y_m"], "MARK": _mark(c["source"]) if c else "",
                     "GEOMETRY": _geometry(c.get("dimensions")) if c else "",
                     "CONCRETE_CATEGORY": c["category"] if c else "",
                     "CONCRETE_BASE_M3": c["base"] if c and c["category"] != "UNRESOLVED" else None,
                     "CONCRETE_EXPOSURE_LOW_M3": c.get("exposure_low") if c and c["category"] == "UNRESOLVED" else None,
                     "CONCRETE_EXPOSURE_HIGH_M3": c.get("exposure_high") if c and c["category"] == "UNRESOLVED"
                     else None,
                     "EXISTENCE": existence, "REBAR_STATE": r["REBAR_STATE"],
                     "PREVIOUS_STATE": prev.get(cid, "ABSENT" if prev_reg is not None else ""),
                     "AVAILABLE_EVIDENCE": "; ".join(ev) or "none", "MISSING_ROLES": ",".join(roles),
                     "DETAIL_REQUIRED": "; ".join(need), "PROVISIONAL_KG_LOW": kg[0], "PROVISIONAL_KG_BASE": kg[1],
                     "PROVISIONAL_KG_HIGH": kg[2],
                     "UNKNOWNS": "all bars" if roles == ["ALL"] else "the missing roles' bars (the provisional kg "
                                                                      "covers the other roles only)",
                     "REASON": r["REASON"]})
    return rows


def missing_summary(rows):
    out = []
    for dim in ("FAMILY", "STOREY", "MISSING_ROLES", "EXISTENCE", "REBAR_STATE"):
        g = defaultdict(lambda: [0, 0.0, 0.0, 0.0])
        for r in rows:
            for key in (r[dim].split(",") if dim == "MISSING_ROLES" else [r[dim]]):
                v = g[key]
                v[0] += 1
                v[1] += r["CONCRETE_BASE_M3"] or 0.0
                v[2] += r["CONCRETE_EXPOSURE_HIGH_M3"] or 0.0
                v[3] += r["PROVISIONAL_KG_BASE"] or 0.0
        for k, v in sorted(g.items()):
            out.append({"BY": dim, "VALUE": k, "COMPONENTS": v[0], "CONCRETE_WITHOUT_FULL_BARS_M3": v[1],
                        "UNRESOLVED_CONCRETE_EXPOSURE_HIGH_M3": v[2], "PROVISIONAL_KG_OF_OTHER_ROLES": v[3]})
    return out


def unresolved_concrete(D, items, arch=None):
    u = D["unit_m"]
    loc = locate(D, arch)
    rows, n = [], Counter()
    for i in sorted((i for i in items if i["trade"] == "CONCRETE" and i["category"] == "UNRESOLVED"),
                    key=lambda i: (_loc(i["component_id"], loc, u)["sheet"], i["family"], i["component_id"])):
        lc = _loc(i["component_id"], loc, u)
        n[lc["sheet"]] += 1
        cls, need = UNRESOLVED_CLASS.get(i["blocker"], ("UNCLASSIFIED", i["blocker"]))
        d = i.get("dimensions") or {}
        alt = []
        if d.get("alternative_as_neighbour_m3") is not None:
            alt.append(f"as the collinear {d.get('neighbour_mark')}: {d['alternative_as_neighbour_m3']:.3f} m3")
        if i.get("exposure_low") is not None:
            alt.append(f"exposure {i['exposure_low']:.3f} - {i['exposure_high']:.3f} m3")
        rows.append({"NO": f"{lc['sheet']}-{n[lc['sheet']]:02d}", "ITEM_ID": i["item_id"],
                     "COMPONENT_ID": i["component_id"], "FAMILY": i["family"], "STOREY": i["storey"],
                     "SHEET": lc["sheet"], "X_M": lc["x_m"], "Y_M": lc["y_m"], "MARK": _mark(i["source"]),
                     "BLOCKER": i["blocker"], "CLASS": cls, "EXPOSURE_LOW_M3": i.get("exposure_low"),
                     "EXPOSURE_HIGH_M3": i.get("exposure_high"), "ALTERNATIVES": "; ".join(alt),
                     "GEOMETRY": _geometry(d), "TO_SETTLE": need})
    return rows


def cb_lines(D):
    out = []
    for sid, rec in sorted(D["sheets"].items()):
        for ln in rec.get("cb_lines", []):
            out.append({"LINE_ID": ln["line_id"], "SHEET": sid, "MARK": ln["mark"], "STATE": ln["state"],
                        "DIRECTION": ln.get("direction") or "", "DECIDED_BY": ln.get("decided_by") or "",
                        "PRINTED_SPANS_M": " / ".join(f"{x:g}" for x in ln["printed_m"]),
                        "DRAWN_SPANS_M": " / ".join(f"{s['drawn_m']:.2f}" for s in sorted(ln["spans"], key=lambda s:
                                                                                           s["index"])),
                        "CLEAR_SPANS_M": " / ".join(f"{s['clear_m']:.2f}" for s in sorted(ln["spans"], key=lambda s:
                                                                                           s["index"])),
                        "RESIDUALS_M": " / ".join(f"{x:.2f}" for x in (ln.get("residuals") or [])),
                        "PIECES": len(ln["pieces"]), "INHERITED_PIECES": ",".join(ln.get("inherited") or []),
                        "BAR_GROUPS": len(ln.get("groups") or []),
                        "MISSING": "; ".join(f"{a}{b} {c}" for a, b, c in (ln.get("missing") or []))})
    return out


def cb_bars(D):
    out = []
    for sid, rec in sorted(D["sheets"].items()):
        for ln in rec.get("cb_lines", []):
            for g in ln.get("groups") or []:
                m = g.get("mass_kg") or (None, None, None)
                L = g.get("length_m")
                out.append({"LINE_ID": ln["line_id"], "MARK": ln["mark"], "BAR_ID": g.get("bar_id"),
                            "ROLE": g.get("role"), "COUNT": g.get("count"), "DIA_MM": g.get("dia_mm"),
                            "SPANS": ",".join(str(x) for x in sorted(g.get("share") or {})),
                            "LENGTH_M_LOW": L[0] if L else None, "LENGTH_M_BASE": L[1] if L else None,
                            "LENGTH_M_HIGH": L[2] if L else None, "BASIS": g.get("basis"),
                            "MASS_KG_LOW": m[0], "MASS_KG_BASE": m[1], "MASS_KG_HIGH": m[2]})
    return out


def gb_exterior(D, items, arch):
    bands = (arch or {}).get("bands") or {}
    conc = {i["component_id"]: i for i in items if i["trade"] == "CONCRETE" and i["family"] == "GROUND_BEAMS"}
    out = []
    for rec in D["sheets"].values():
        if rec["sheet"]["role"] != "GROUND_BEAM_PLAN":
            continue
        for b in rec.get("beams", []):
            sides = rec.get("band_sides", {}).get(b["band_id"], [])
            a = bands.get(b["band_id"], {})
            if "OUTSIDE" not in sides and a.get("class") not in ("EXTERIOR_WALL", "PERIMETER_NO_WALL"):
                continue
            i = conc.get(f"GROUND_BEAMS:{rec['sheet']['storey']}:{b['band_id']}", {})
            out.append({"BAND": b["band_id"], "LENGTH_M": round(b["length_m"], 3), "WIDTH_M": round(b["width_m"], 3),
                        "OUTSIDE_SIDE": "OUTSIDE" in sides, "ARCH_CLASS": a.get("class", "NOT_REGISTERED"),
                        "WALL_COVER": a.get("wall_cover"), "INSIDE_FLOOR_LEVEL_M": a.get("floor_level_m"),
                        "CASE": i.get("blocker", ""), "LOW_M3": i.get("low"), "BASE_M3": i.get("base"),
                        "HIGH_M3": i.get("high")})
    return out


def lintels(arch, items):
    conc = {i["component_id"]: i for i in items if i["trade"] == "CONCRETE" and i["family"] == "LINTELS"}
    kg = Counter()
    for i in items:
        if i["trade"] == "REINFORCEMENT" and i["family"] == "LINTELS" and i["category"] == "PROVISIONAL":
            kg[i["component_id"]] += i["base"]
    out = []
    for st, L in sorted(((arch or {}).get("lintels") or {}).items()):
        for op in L["openings"]:
            cid = f"LINTELS:{st}:{op['opening_id']}"
            i = conc.get(cid, {})
            out.append({"OPENING": cid, "WIDTH_M": round(op["width_m"], 3), "WALL_T_M": round(op["wall_t_m"], 3),
                        "JAMBS": f"{op['start_jamb']}/{op['end_jamb']}", "CUT_AT_COLUMN": op.get("split_at_column"),
                        "BEAM_OVER": op.get("beam_over", "NOT_REGISTERED"), "CATEGORY": i.get("category", "REPORTED"),
                        "BLOCKER": i.get("blocker", ""), "CONCRETE_BASE_M3": i.get("base"),
                        "EXPOSURE_HIGH_M3": i.get("exposure_high"), "BARS_KG_BASE": kg.get(cid) or None})
    return out


def slab_faces(D, items):
    conc = {i["component_id"]: i for i in items if i["trade"] == "CONCRETE"}
    out = []
    for sid, rec in sorted(D["sheets"].items()):
        fam = "GROUND_SLAB" if rec["sheet"]["role"] == "GROUND_BEAM_PLAN" else "SLABS"
        for f in (rec.get("slab") or {}).get("faces", []):
            if f["class"] != "PANEL":
                continue
            cid = f"{fam}:{rec['sheet']['storey']}:{f['face_id']}"
            i = conc.get(cid, {})
            out.append({"COMPONENT_ID": cid, "SHEET": sid, "AREA_GROSS_M2": f.get("area_gross_m2", f["area_m2"]),
                        "MEMBER_OVERLAP_M2": f.get("member_overlap_m2", 0.0), "AREA_NET_M2": f["area_m2"],
                        "T_M": f.get("t_m"), "T_BASIS": f.get("t_basis"),
                        "T_SHEET_UNIFORM_M": f.get("t_sheet_uniform_m"), "REGION": f.get("region") or "",
                        "CATEGORY": i.get("category", ""), "BASE_M3": i.get("base")})
    return out


def ocr_items(items):
    return [{"ITEM_ID": i["item_id"], "FAMILY": i["family"], "STOREY": i["storey"], "DIA_MM": i.get("dia_mm"),
             "LOW_KG": i["low"], "BASE_KG": i["base"], "HIGH_KG": i["high"],
             "DETAIL": (re.search(r"typical detail (\S+)", i["source"]) or [None, ""])[1]}
            for i in items if i.get("blocker") == "OCR_DERIVED_UNREVIEWED"]


def conflicts(risk):
    return [{"KIND": r["KIND"], "WHERE": r["WHERE"], "DETAIL": str(r["DETAIL"])[:300]} for r in risk
            if r["KIND"] in CONFLICT_KINDS]


def policy_record():
    return {"policy": POLICY_ID, "rule": "registers of ids and engine marks only; missing bars are counted with the "
                                         "concrete they leave without steel, never estimated by a kg/m3 ratio"}
