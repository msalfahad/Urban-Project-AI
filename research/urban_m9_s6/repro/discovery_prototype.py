"""S6 drawing-discovery PROTOTYPE (research only; read-only; not production code).

usage: python3 -I discovery_prototype.py REPO DRAWING.dxf OUT.json

Builds a URBAN_DRAWING_DISCOVERY_V1 report (S6_02_DRAWING_DISCOVERY_SCHEMA.json) for ONE DXF, BEFORE any quantity, by
reusing what the repository already has:
    tools.urban_intake.read            K2 geometry + its findings (XREF_NOT_RESOLVED, UNVERIFIED_FOR_QTO_USE, ...)
    engine.source.drawing_model        sheet frames, declared vs inferred units (infer_units)
    engine.source.arch_plan            floor-plan titles and plan regions (plan_regions)
    engine.source.capability           what each entity kind can support
    engine.source.level_marks          level texts
plus a direct ezdxf census of model space, every paper-space layout and every block (what K2 never looks at).
Each stage ends NOT_RUN | PASSED | PROVISIONAL | BLOCKED | FAILED with findings at FATAL / BLOCKED_ITEM /
REVIEW_REQUIRED / WARNING. Nothing is inferred into a quantity here.
"""
import hashlib, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

REPO, DWG, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3])
sys.path.insert(0, str(REPO))
import ezdxf                                                              # noqa: E402
from tools import urban_intake as UI                                     # noqa: E402
from engine.source import arch_plan as AP, drawing_model as DM, level_marks as LMK, capability as CAP  # noqa: E402

SCHEMA = "URBAN_DRAWING_DISCOVERY_V1"
GEOM = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE", "HATCH", "SOLID", "INSERT", "MLINE"}
# what the architectural route turns into measurable geometry today (S6 audit; see S6_03_SOURCE_ENTITY_CENSUS.md)
ARCH_READS = {"LINE": "READ", "LWPOLYLINE": "READ", "ARC": "READ", "CIRCLE": "READ", "ELLIPSE": "READ_AS_CHORDS",
              "SPLINE": "READ_AS_CHORDS", "POLYLINE": "READ_2D_ONLY", "MLINE": "READ", "INSERT": "READ_NESTED",
              "HATCH": "READ_ONE_BLOCK_LEVEL", "TEXT": "READ", "MTEXT": "READ", "ATTRIB": "READ",
              "SOLID": "CARRIED_NOT_GEOMETRY", "DIMENSION": "NOT_READ", "LEADER": "NOT_READ", "MLEADER": "NOT_READ",
              "VIEWPORT": "NOT_READ", "POINT": "NOT_READ", "RTEXT": "NOT_READ", "WIPEOUT": "NOT_READ",
              "IMAGE": "NOT_READ", "OLE2FRAME": "NOT_READ", "ACAD_PROXY_ENTITY": "NOT_READ", "3DFACE": "NOT_READ",
              "TRACE": "NOT_READ", "ACAD_TABLE": "NOT_READ", "REGION": "NOT_READ", "3DSOLID": "NOT_READ"}


def f(level, code, msg, **ev):
    return {"level": level, "code": code, "message": msg, "evidence": ev}


def stage(state, findings, **data):
    return {"state": state, "findings": findings, **data}


def worst(findings, default="PASSED"):
    lv = {x["level"] for x in findings}
    if "FATAL" in lv:
        return "FAILED"
    if "BLOCKED_ITEM" in lv:
        return "BLOCKED"
    if "REVIEW_REQUIRED" in lv or "WARNING" in lv:
        return "PROVISIONAL"
    return default


def census(doc):
    """entities per layout (model space + each paper layout) and per block, nesting depth, MINSERTs, XREFs."""
    out = {"layouts": [], "blocks": {}, "xrefs": [], "minserts": 0, "max_insert_depth": 0}
    for lay in doc.layouts:
        types = Counter(e.dxftype() for e in lay)
        vps = [e for e in lay if e.dxftype() == "VIEWPORT"]
        out["layouts"].append({"name": lay.name, "kind": "MODEL" if lay.name == "Model" else "PAPER",
                               "entities_by_type": dict(sorted(types.items())),
                               "viewports": max(len(vps) - 1, 0) if lay.name != "Model" else 0})
    for b in doc.blocks:
        if b.name.startswith("*"):
            continue
        out["blocks"][b.name] = dict(Counter(e.dxftype() for e in b))
        if b.block_record.is_xref:
            out["xrefs"].append({"block": b.name, "path": b.block.dxf.get("xref_path", ""),
                                 "resolved": False})

    def depth(name, seen=()):
        blk = doc.blocks.get(name)
        if blk is None or name in seen:
            return 0
        return 1 + max([depth(e.dxf.name, seen + (name,)) for e in blk if e.dxftype() == "INSERT"] or [0])
    for e in doc.modelspace():
        if e.dxftype() == "INSERT":
            out["max_insert_depth"] = max(out["max_insert_depth"], depth(e.dxf.name))
    for lay in [doc.modelspace()] + [b for b in doc.blocks]:
        out["minserts"] += sum(1 for e in lay if e.dxftype() == "INSERT" and
                               (e.dxf.get("row_count", 1) > 1 or e.dxf.get("column_count", 1) > 1))
    return out


def main():
    data = DWG.read_bytes()
    rep = {"schema": SCHEMA, "prototype": True, "documents": [], "stages": {}, "gates": {}}
    doc_rec = {"file": DWG.name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "format": "DXF"}
    rep["documents"].append(doc_rec)
    # ---------------------------------------------------------------- 0 intake
    try:
        doc = ezdxf.readfile(str(DWG))
    except Exception as ex:                                          # noqa: BLE001
        rep["stages"]["0_intake"] = stage("FAILED", [f("FATAL", "UNREADABLE", str(ex)[:200])])
        json.dump(rep, open(OUT, "w"), indent=1)
        return
    hdr = {"dxf_version": doc.dxfversion, "INSUNITS": doc.header.get("$INSUNITS"),
           "DIMLFAC": doc.header.get("$DIMLFAC"), "MEASUREMENT": doc.header.get("$MEASUREMENT")}
    doc_rec.update(header=hdr)
    rep["stages"]["0_intake"] = stage("PASSED", [])
    # ---------------------------------------------------------------- 1 inventory (every layout, every block)
    C = census(doc)
    fi = []
    model = next(x for x in C["layouts"] if x["kind"] == "MODEL")
    n_geo = sum(v for k, v in model["entities_by_type"].items() if k in GEOM)
    if n_geo == 0:
        fi.append(f("FATAL", "EMPTY_MODEL_SPACE", "model space holds no geometry"))
    for p in (x for x in C["layouts"] if x["kind"] == "PAPER"):
        n = sum(p["entities_by_type"].values()) - p["entities_by_type"].get("VIEWPORT", 0)
        if n:
            fi.append(f("REVIEW_REQUIRED", "PAPER_SPACE_CONTENT", f"layout '{p['name']}' holds {n} entities "
                        "(frames / titles / notes there are invisible to the plan reader)", layout=p["name"],
                        entities=p["entities_by_type"]))
    for x in C["xrefs"]:
        fi.append(f("BLOCKED_ITEM", "XREF_NOT_SUPPLIED", f"external reference {x['block']} -> {x['path']} is not "
                    "supplied: what it draws is missing from every region it covers", **x))
    if C["minserts"]:
        fi.append(f("WARNING", "MINSERT_PRESENT", f"{C['minserts']} MINSERT(s): the hatch / insert readers of the "
                    "architectural route read the first cell only", count=C["minserts"]))
    if C["max_insert_depth"] > 1:
        fi.append(f("WARNING", "NESTED_BLOCKS", f"blocks nested {C['max_insert_depth']} deep: hatches deeper than "
                    "one level are not read by the architectural route", depth=C["max_insert_depth"]))
    types_all = Counter()
    for lay in C["layouts"]:
        types_all.update(lay["entities_by_type"])
    for b in C["blocks"].values():
        types_all.update(b)
    support = {t: ARCH_READS.get(t, "UNKNOWN_KIND") for t in sorted(types_all)}
    for t, s in support.items():
        if s in ("NOT_READ", "CARRIED_NOT_GEOMETRY", "UNKNOWN_KIND") and t not in ("VIEWPORT", "ATTDEF", "POINT"):
            fi.append(f("WARNING", "ENTITY_KIND_NOT_MEASURED", f"{types_all[t]} {t}: {s}", kind=t, count=types_all[t]))
    off = []
    for L in doc.layers:
        if L.is_off() or L.is_frozen():
            n = sum(1 for e in doc.modelspace() if e.dxf.layer == L.dxf.name)
            if n:
                off.append({"layer": L.dxf.name, "off": L.is_off(), "frozen": L.is_frozen(), "entities": n})
    for o in off:
        fi.append(f("REVIEW_REQUIRED", "HIDDEN_LAYER_CONTENT", f"layer {o['layer']} is "
                    f"{'frozen' if o['frozen'] else 'off'} and holds {o['entities']} entities that the readers use",
                    **o))
    rep["stages"]["1_inventory"] = stage(worst(fi), fi, census=C, entity_support=support, hidden_layers=off)
    # ---------------------------------------------------------------- K2 intake (for units, frames, regions)
    try:
        E = UI.read(str(DWG))
    except Exception as ex:                                          # noqa: BLE001
        rep["stages"]["4_units"] = stage("FAILED", [f("FATAL", "INTAKE_FAILED", str(ex)[:200])])
        json.dump(rep, open(OUT, "w"), indent=1)
        return
    k2 = E.get("intake_findings") or {}
    # ---------------------------------------------------------------- 4 units (before regions: tolerances need them)
    fu = []
    rects = DM.closed_rectangles(E["segments"])
    U = DM.infer_units(E, rects)
    declared = E.get("unit_m")
    if declared is None:
        fu.append(f("BLOCKED_ITEM", "UNITS_NOT_DECLARED", f"$INSUNITS {hdr['INSUNITS']}: no declared unit; geometry "
                    f"suggests {U['unit_m']} m per unit - a reviewer must confirm before any measurement",
                    member_fit=U["member_fit"]))
    elif U.get("warning"):
        fu.append(f("BLOCKED_ITEM", "UNITS_CONTRADICTED", U["warning"], member_fit=U["member_fit"]))
    if hdr["DIMLFAC"] not in (None, 1, 1.0):
        fu.append(f("REVIEW_REQUIRED", "DIMLFAC_NOT_ONE", f"$DIMLFAC {hdr['DIMLFAC']}: printed dimensions are scaled"))
    unit_m = declared or U["unit_m"]
    rep["stages"]["4_units"] = stage(worst(fu), fu, declared_unit_m=declared, inferred_unit_m=U["unit_m"],
                                     member_fit=U["member_fit"], unit_m_used_for_discovery=unit_m)
    # ---------------------------------------------------------------- 2 sheets (frames + titles) and 5 plan regions
    fs = []
    E2 = dict(E, unit_m=unit_m)
    model_frames = DM.build(E2)["sheets"]
    line_frames = DM.build(E2, options={"frames_from_lines": True})["sheets"]
    titles = []
    for t in E["texts"]:
        fl, order = AP.floor_of_title(t["value"])
        if fl:
            titles.append({"floor": fl, "x": t["x"], "y": t["y"], "text_id": t["id"]})
    if len(line_frames) > len(model_frames):
        fs.append(f("BLOCKED_ITEM", "FRAME_DRAWN_AS_LINES", f"{len(line_frames) - len(model_frames)} sheet frame(s) "
                    "drawn as separate lines are not frames to the plan reader", polyline_frames=len(model_frames),
                    line_frames=len(line_frames)))
    inside = [t for t in titles if any(s["box"][0] <= t["x"] <= s["box"][2] and s["box"][1] <= t["y"] <= s["box"][3]
                                       for s in model_frames)]
    if titles and not inside:
        fs.append(f("BLOCKED_ITEM", "PLAN_TITLES_OUTSIDE_ANY_FRAME", f"{len(titles)} floor-plan title(s) found, none "
                    "inside a model-space frame: no plan region can be formed", titles=[t["floor"] for t in titles]))
    if not titles:
        fs.append(f("BLOCKED_ITEM", "NO_FLOOR_PLAN_TITLE", "no text matches a floor-plan title"))
    P = AP.plan_regions(E2)
    by_frame = defaultdict(list)
    for r in P["regions"]:
        by_frame[r["sheet_id"]].append(r)
    for sid, regs in by_frame.items():
        if len(regs) < 2:
            continue
        cuts = sorted({r["box"][0] for r in regs} - {min(r["box"][0] for r in regs)})
        for c in cuts:
            crossing = [s for s in E["segments"] if min(s["a"][0], s["b"][0]) < c < max(s["a"][0], s["b"][0])
                        and s["layer"] not in ("A-FRAME",)]
            if crossing:
                fs.append(f("BLOCKED_ITEM", "REGION_CUT_CROSSES_GEOMETRY", f"frame {sid} is split at x={c:.1f} between "
                            f"its titles, and {len(crossing)} drawn segment(s) cross the cut: a plan would be divided",
                            frame=sid, cut_x=round(c, 3), crossing=len(crossing)))
    dup = Counter(r["floor"] for r in P["regions"])
    for fl, n in dup.items():
        if n > 1:
            fs.append(f("REVIEW_REQUIRED", "FLOOR_TITLE_REPEATED", f"{n} plans titled {fl}"))
    for o in P["other_frames"]:
        fs.append(f("WARNING", "FRAME_NOT_A_FLOOR_PLAN", f"frame {o['sheet_id']}: {o['why']}", **o))
    rep["stages"]["2_sheets"] = stage(worst(fs), [x for x in fs if x["code"] in ("FRAME_DRAWN_AS_LINES",
                                                                                "FRAME_NOT_A_FLOOR_PLAN")],
                                      frames=[{"sheet_id": s["sheet_id"], "role": s["role"], "storey": s["storey"],
                                               "frame_source": s["frame_source"]} for s in model_frames])
    f5 = [x for x in fs if x["code"] not in ("FRAME_DRAWN_AS_LINES", "FRAME_NOT_A_FLOOR_PLAN")]
    if not P["regions"]:
        f5.append(f("FATAL", "NO_PLAN_REGION", "no floor plan region: the architectural BOQ must not run"))
    floors = []
    for r in P["regions"]:
        ents = AP.region_entities(E2, r["box"])
        lv = sorted({v for t in ents["texts"] for v in [LMK.parse_level(t["value"])] if v is not None})
        floors.append({"floor_id": r["floor"], "region_id": r["region_id"], "sheet_id": r["sheet_id"],
                       "title_text_id": r["title_text_id"], "level_texts_m": lv,
                       "entities": {k: len(v) for k, v in ents.items()}})
    rep["stages"]["5_floors"] = stage(worst(f5), f5, floors=floors)
    # ---------------------------------------------------------------- 6 geometry readiness (reader limits, K2 findings)
    fg = []
    for code, n in sorted(k2.items()):
        lvl = "BLOCKED_ITEM" if code in ("XREF_NOT_RESOLVED",) else "WARNING"
        fg.append(f(lvl, "K2_" + code, f"{n} x {code} (K2 kernel finding)", count=n))
    rep["stages"]["6_geometry_readiness"] = stage(worst(fg), fg)
    # ---------------------------------------------------------------- 7 heights: never from plans alone
    rep["stages"]["7_vertical_model"] = stage("BLOCKED", [f("BLOCKED_ITEM", "NO_SECTION_SOURCE", "heights need a "
                                              "section / schedule / facts file; level texts are candidates only")],
                                              level_candidates={x["floor_id"]: x["level_texts_m"] for x in floors})
    for s in ("3_identity", "8_features", "9_finish_zones", "10_boq_readiness"):
        rep["stages"][s] = stage("NOT_RUN", [])
    allf = [x for st in rep["stages"].values() for x in st["findings"]]
    rep["gates"] = {"fatal": sum(1 for x in allf if x["level"] == "FATAL"),
                    "blocked_items": sum(1 for x in allf if x["level"] == "BLOCKED_ITEM"),
                    "review_required": sum(1 for x in allf if x["level"] == "REVIEW_REQUIRED"),
                    "warnings": sum(1 for x in allf if x["level"] == "WARNING"),
                    "architectural_boq_may_run": not any(x["level"] in ("FATAL", "BLOCKED_ITEM") for x in allf
                                                         if x["code"] not in ("NO_SECTION_SOURCE", "XREF_NOT_SUPPLIED",
                                                                              "K2_XREF_NOT_RESOLVED")),
                    "rule": "FATAL anywhere, or a BLOCKED_ITEM in stages 0-5, stops the BOQ (exit != 0); a "
                            "BLOCKED_ITEM in later stages blocks the affected items only"}
    json.dump(rep, open(OUT, "w"), indent=1, ensure_ascii=True)
    print(json.dumps({"file": DWG.parent.name, "stages": {k: v["state"] for k, v in rep["stages"].items()},
                      "gates": {k: v for k, v in rep["gates"].items() if k != "rule"},
                      "codes": sorted({x["code"] for x in allf})}))


if __name__ == "__main__":
    main()
