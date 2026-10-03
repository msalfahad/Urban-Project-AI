"""ALSENAN / P7757 + ST7757 - PHASE A2 (SOURCE-ONLY GENERIC ENGINE IMPROVEMENT; SHADOW; frozen before any benchmark).

    python3 research/external_engine_lab/alsenan_phase_a2.py <work_dir> <register_dir> [code_commit]

PROJECT ADAPTER (facts only), on top of the Phase A adapter (alsenan_phase_a: intake by sha256, sheets, schedules,
footing association, units). Phase A2 adds, all through generic engine code (engine/source):
    CAD tables       linetype DEFINITIONS (dash patterns), layer linetypes, solid-fill extents - read from the source
    RTEXT placement  the layer and proxy-graphics extent of RTEXT entities read from the raw DXF (K2 does not realise
                     them), so the frozen unrealised accounting can place them instead of blocking every site
    role inference   entity_role_inference V1 per plan region, two passes (same-source corroboration in pass 2)
    topology         room_topology TS01 + closure policy with the inferred claims and inferred doors
    units            level_marks.cross_document_plot_evidence: plot sides printed in ONE drawing vs the plot
                     rectangle drawn in the OTHER (frame.assess decides; nothing is overridden)
    footings         structural_qto.template_outlines + complete_by_count (constraint-unique, never by distance)
    vertical         raster SECTION pages transcribed by eye into VERTICAL_EVIDENCE items (page, crop, text,
                     confidence); heights are differences of PRINTED values, never pixels
There is no layer map, handle list or coordinate list here; no Qortuba fact; no donor calculator.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import ezdxf                                                                                     # noqa: E402

from engine.source import benchmark_firewall as FW, canonical_input as CI, entity_role_inference as ERI  # noqa: E402
from engine.source import frame as FR, level_marks as LM, room_topology as RT, structural_qto as SQ    # noqa: E402
from engine.source import topology_closures as TC, topology_digest as TD, text_role as TX             # noqa: E402

import alsenan_phase_a as AP                                                                      # noqa: E402

PHASE = "ALSENAN_P7757_ST7757_PHASE_A2"
FLOORS = ("GF", "1F", "2F")
WET_WORDS = ("BATH", "W.C", "WC", "WASH", "KITCHEN", "LAUNDRY", "TOILET", "SHOWER")

# ------------------------------------------------------------------ raster vertical evidence (transcribed by eye)
# Each item: what is PRINTED on the delivered raster page, where (page, crop box in the 150 dpi upright render),
# the transcription and a confidence. Nothing here is measured from pixels.
SECTION_PDF = "P7757_Architectural_Plan_Pages_07-12.pdf"
VERTICAL_TRANSCRIPTIONS = [
    # page 10 (PDF page index 3): SECTION A-A 1:100 (drawn rotated on the sheet)
    {"id": "VE-AA-01", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "LEVEL_MARK",
     "text": "±0.00", "value_m": 0.00, "reading": "natural ground, both sides", "confidence": "HIGH"},
    {"id": "VE-AA-02", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "LEVEL_MARK",
     "text": "+0.15", "value_m": 0.15, "reading": "external paving at the stair foot", "confidence": "HIGH"},
    {"id": "VE-AA-03", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "LEVEL_MARK",
     "text": "+0.30", "value_m": 0.30, "reading": "entrance / landing", "confidence": "HIGH"},
    {"id": "VE-AA-04", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "FFL",
     "text": "+1.00", "value_m": 1.00, "floor": "GF", "reading": "ground floor finished level", "confidence": "HIGH"},
    {"id": "VE-AA-05", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "FFL",
     "text": "+5.50", "value_m": 5.50, "floor": "1F", "reading": "first floor finished level", "confidence": "HIGH"},
    {"id": "VE-AA-06", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "FFL",
     "text": "+9.70", "value_m": 9.70, "floor": "2F", "reading": "second floor finished level", "confidence": "HIGH"},
    {"id": "VE-AA-07", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "ROOF_LEVEL",
     "text": "+13.90", "value_m": 13.90, "floor": "ROOF", "reading": "upper roof level", "confidence": "HIGH"},
    {"id": "VE-AA-08", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "DIMENSION_CHAIN",
     "text": "100 / 870 / 420 / 50 = 1440 (cm)", "values_cm": [100, 870, 420, 50], "total_cm": 1440,
     "reading": "left chain: ground -> GF FFL, GF -> 2F FFL, 2F -> roof, parapet", "confidence": "HIGH"},
    {"id": "VE-AA-09", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "DIMENSION_CHAIN",
     "text": "450 (cm) between +1.00 and +5.50; 420 between +5.50 and +9.70; 420 between +9.70 and +13.90",
     "values_cm": [450, 420, 420], "reading": "floor-to-floor dimensions printed beside the rooms", "confidence": "HIGH"},
    {"id": "VE-AA-10", "page": 10, "view": "SECTION A-A", "crop_px": [680, 360, 1940, 1380], "kind": "PARAPET",
     "text": "50 (cm) above +13.90 and above +5.50 (terrace edge)", "values_cm": [50],
     "reading": "parapet height", "confidence": "MEDIUM"},
    # page 11 (PDF page index 4): SECTION B-B 1:100
    {"id": "VE-BB-01", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "LEVEL_MARK",
     "text": "±0.00", "value_m": 0.00, "reading": "natural ground", "confidence": "HIGH"},
    {"id": "VE-BB-02", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "FFL",
     "text": "+0.30", "value_m": 0.30, "floor": "ANNEX", "reading": "annex (pool side) floor", "confidence": "HIGH"},
    {"id": "VE-BB-03", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "ROOF_LEVEL",
     "text": "+4.30", "value_m": 4.30, "floor": "ANNEX", "reading": "annex roof", "confidence": "HIGH"},
    {"id": "VE-BB-04", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "LEVEL_MARK",
     "text": "+0.15", "value_m": 0.15, "reading": "court paving", "confidence": "HIGH"},
    {"id": "VE-BB-05", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "FFL",
     "text": "+1.00", "value_m": 1.00, "floor": "GF", "reading": "ground floor finished level", "confidence": "HIGH"},
    {"id": "VE-BB-06", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "FFL",
     "text": "+5.50", "value_m": 5.50, "floor": "1F", "reading": "first floor finished level", "confidence": "HIGH"},
    {"id": "VE-BB-07", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "FFL",
     "text": "+9.70", "value_m": 9.70, "floor": "2F", "reading": "second floor / roof terrace level", "confidence": "HIGH"},
    {"id": "VE-BB-08", "page": 11, "view": "SECTION B-B", "crop_px": [0, 0, 2484, 1755], "kind": "DIMENSION_CHAIN",
     "text": "480 / 400 (annex); 535; 100 / 550 / 50; 450; 420; 870; 130; 420 / 50; 1440 (cm)",
     "values_cm": [480, 400, 535, 100, 550, 50, 450, 420, 870, 130, 420, 50, 1440],
     "reading": "vertical chains; 400 = annex +0.30 -> +4.30", "confidence": "MEDIUM"},
]


# ------------------------------------------------------------------ CAD structure facts
def cad_tables(path) -> dict:
    """Linetype DEFINITIONS (group-49 dash elements), layer -> linetype, solid-fill extents, and how many entities
    override the layer linetype (recorded: the inference uses layer linetypes only)."""
    doc = ezdxf.readfile(str(path))
    lts = {lt.dxf.name: [float(t.value) for t in lt.pattern_tags.tags if t.code == 49] for lt in doc.linetypes}
    lay = {L.dxf.name: L.dxf.linetype for L in doc.layers}
    fills = []
    for h in doc.modelspace().query("HATCH"):
        if not h.dxf.solid_fill:
            continue
        pts = []
        for pth in h.paths:
            if hasattr(pth, "vertices"):
                pts += [(v[0], v[1]) for v in pth.vertices]
            else:
                for e in pth.edges:
                    for nm in ("start", "end"):
                        if hasattr(e, nm):
                            v = getattr(e, nm)
                            pts.append((v[0], v[1]))
        if pts:
            fills.append((h.dxf.layer, (min(p[0] for p in pts), min(p[1] for p in pts),
                                        max(p[0] for p in pts), max(p[1] for p in pts))))
    over = sum(1 for e in doc.modelspace() if e.dxf.hasattr("linetype") and e.dxf.linetype.upper() not in ("BYLAYER",))
    return {"linetypes": lts, "layer_linetype": lay, "fills": sorted(fills), "entity_linetype_overrides": over}


def _proxy_vertices(chunks: list) -> list:
    """Vertices of AutoCAD proxy-graphics POLYLINE (6) / POLYGON (7) records; [] if the stream is not understood."""
    try:
        data = bytes.fromhex("".join(chunks))
        total, count = struct.unpack_from("<ii", data, 0)
        off, pts = 8, []
        for _ in range(count):
            size, typ = struct.unpack_from("<ii", data, off)
            if typ in (6, 7):
                n = struct.unpack_from("<i", data, off + 8)[0]
                for k in range(n):
                    x, y, _z = struct.unpack_from("<ddd", data, off + 12 + 24 * k)
                    pts.append((x, y))
            off += size
        return pts
    except (struct.error, ValueError):
        return []


def rtext_placements(path) -> dict:
    """{decimal handle: {layer, insert, extent}} of RTEXT entities, read from the raw DXF: layer (8), insertion
    (10/20) and the proxy-graphics extent (310). Generic: any RTEXT, any drawing."""
    lines = Path(path).read_bytes().decode("utf-8", errors="replace").splitlines()
    pairs = [(lines[i].strip(), lines[i + 1]) for i in range(0, len(lines) - 1, 2)]
    out = {}
    for i, (c, v) in enumerate(pairs):
        if c != "0" or v.strip() != "RTEXT":
            continue
        g = {"310": []}
        for c2, v2 in pairs[i + 1:]:
            if c2 == "0":
                break
            if c2 == "310":
                g["310"].append(v2.strip())
            else:
                g.setdefault(c2, v2.strip())
        pts = _proxy_vertices(g["310"])
        ins = (float(g["10"]), float(g["20"])) if "10" in g and "20" in g else None
        ext = ([min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
               if pts else None)
        out[int(g["5"], 16)] = {"handle": g["5"], "layer": g.get("8"), "insert": ins, "extent": ext,
                                "extent_basis": "PROXY_GRAPHICS_VERTICES" if pts else "NONE"}
    return out


def fix_unrealised(unrealised, placements) -> tuple:
    """Unrealised entries gain the layer and placement extent read from the raw DXF where the entity is an RTEXT
    found there; everything else is passed through unchanged (and still blocks where the frozen rule says)."""
    out, rec = [], []
    for u in unrealised:
        try:
            h = int(str(u["obs_id"]).split(":")[1])
        except (IndexError, ValueError):
            h = None
        pl = placements.get(h)
        if pl is not None and u["code"] == "UNHANDLED":
            v = dict(u, layer=pl["layer"], extent=pl["extent"])
            rec.append({"obs_id": u["obs_id"], "entity": "RTEXT", "layer": pl["layer"], "extent": pl["extent"],
                        "basis": pl["extent_basis"]})
            out.append(v)
        else:
            out.append(u)
    return out, rec


# ------------------------------------------------------------------ helpers
def _rect_layers(blob, min_len, inside=None):
    by = defaultdict(list)
    for p in blob["parts"]:
        if p.kind != "SEGMENT" or p.identity.instance_handles:
            continue
        g = p.geometry
        if math.hypot(g[2] - g[0], g[3] - g[1]) < min_len:
            continue
        if inside and not (AP.in_box(g[0], g[1], inside) and AP.in_box(g[2], g[3], inside)):
            continue
        by[CI.effective_layer(p)[0]].append((p.identity.key,) + tuple(g))
    return [dict(r, layer=lay) for lay, s in sorted(by.items(), key=lambda kv: str(kv[0]))
            for r in SQ.rectangles(s, eps=AP.EPS)]


def _evidence_from_records(recs):
    return [FR.UnitEvidence(e["evidence_id"], e["question"], e["kind"], e["scope"], tuple(e["lineage"]),
                            derived_value=e.get("derived_value"), observed_value=e.get("observed_value"),
                            source_ref=e.get("source_ref"), source_sha256=e.get("source_sha256"), unit=e.get("unit"))
            for e in recs if e["kind"] not in (FR.UNIT_HEADER_DECLARATION,)]


def _english(values):
    return [v for v in values if v and v.isascii() and AP._english_space_name(v)]


# ------------------------------------------------------------------ the build
def build(work, commit=None) -> dict:
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    fw_census = AP.firewall_census()
    fw_census["scratch_disclosure"] = AP.scratch_disclosure(work)
    loaded_before = set(sys.modules)
    with FW.OpenAudit() as audit:
        ctx = _build(work)
    ctx["code_commit"] = commit
    ctx["firewall"] = {"census": fw_census, "audit": audit.opened, "modules_loaded_during_build":
                       sorted(set(sys.modules) - loaded_before), "modules_all": sorted(sys.modules)}
    return ctx


def _build(work: Path) -> dict:
    ctx = AP._build(work)                                    # Phase A facts (frozen logic, rerun from source)
    P = {k: work / v for k, v in ctx["paths"].items()}
    A = AP.k2(P["P7757.dxf"], AP.REV_ARCH, work / f"k2_{AP.FILES['P7757.dxf'][0][:16]}.pkl")
    S = AP.k2(P["ST7757.dxf"], AP.REV_STR, work / f"k2_{AP.FILES['ST7757.dxf'][0][:16]}.pkl")
    ra = AP.revision(AP.REV_ARCH, AP.FILES["P7757.dxf"][0])
    rs = AP.revision(AP.REV_STR, AP.FILES["ST7757.dxf"][0])
    a2 = {}
    # ---------------- units: Phase A evidence + cross-document plot sides (both directions)
    pa_units = ctx["units"]
    a_rects = _rect_layers(A, 5000.0)
    s_rects = _rect_layers(S, 5000.0)
    pv_s = LM.plot_side_values([(t.identity.key, t.value) for t in S["texts"]])
    pv_a = LM.plot_side_values([(t.identity.key, t.value) for t in A["texts"]])
    plot_a = LM.cross_document_plot_evidence(pv_s, a_rects, printed_sha256=rs.anchor_sha256,
                                             drawing_sha256=ra.anchor_sha256, evidence_id="PLOT_SIDES:ST7757->P7757")
    plot_s = LM.cross_document_plot_evidence(pv_a, s_rects, printed_sha256=ra.anchor_sha256,
                                             drawing_sha256=rs.anchor_sha256, evidence_id="PLOT_SIDES:P7757->ST7757")
    ua = AP.unit_context("P7757.dxf", ra.anchor_sha256, ctx["facts"]["P7757.dxf"]["insunits_declared"],
                         _evidence_from_records(pa_units["ARCHITECTURAL"]["evidence"]) + plot_a["evidence"],
                         pa_units["ARCHITECTURAL"]["views"] + [{"view": "PLOT SIDES printed in ST7757 vs plot "
                                                                         "rectangle drawn in P7757",
                                                                "state": plot_a["state"], "ratios": plot_a["ratios"]}])
    us = AP.unit_context("ST7757.dxf", rs.anchor_sha256, ctx["facts"]["ST7757.dxf"]["insunits_declared"],
                         _evidence_from_records(pa_units["STRUCTURAL"]["evidence"]) + plot_s["evidence"],
                         pa_units["STRUCTURAL"]["views"] + [{"view": "PLOT SIDES printed in P7757 vs plot rectangle "
                                                                      "drawn in ST7757",
                                                             "state": plot_s["state"], "ratios": plot_s["ratios"]}])
    a2["units"] = {"ARCHITECTURAL": ua, "STRUCTURAL": us, "plot_evidence": {
        "P7757": {k: v for k, v in plot_a.items() if k != "evidence"},
        "ST7757": {k: v for k, v in plot_s.items() if k != "evidence"}},
        "phase_a": {k: {"status": v["status"], "reason": v["reason"]} for k, v in pa_units.items()}}
    umm = ua["native_to_mm"] or 1.0
    # ---------------- CAD tables, RTEXT placements
    tab = cad_tables(P["P7757.dxf"])
    a2["cad_tables"] = {"linetypes": tab["linetypes"], "linetype_class": {k: ERI.linetype_class(v)
                                                                          for k, v in tab["linetypes"].items()},
                        "layer_linetype": tab["layer_linetype"], "solid_fills": len(tab["fills"]),
                        "entity_linetype_overrides": tab["entity_linetype_overrides"]}
    placements = rtext_placements(P["P7757.dxf"])
    unreal, fixes = fix_unrealised(A["unrealised"], placements)
    a2["unrealised"] = {"phase_a": A["unrealised"], "placed": fixes, "rtext_in_dxf": len(placements)}
    # ---------------- per plan region: inputs, pass 1
    inputs, pass1 = {}, {}
    for fl in FLOORS:
        s = ctx["sheets_by_floor"][fl]
        inp = AP.assemble(A, ra, s["bounds"], f"{s['sheet']}:{fl}", umm, "ALSENAN-PHASE-A2-UNIT:" + ua["status"])
        inputs[fl] = inp
        pass1[fl] = ERI.infer(inp, linetypes=tab["linetypes"], layer_linetype=tab["layer_linetype"], fills=tab["fills"])
    co = ERI.corroboration_from({inputs[fl].region_id: pass1[fl] for fl in FLOORS})
    floors = {}
    for fl in FLOORS:
        inp = inputs[fl]
        r = ERI.infer(inp, linetypes=tab["linetypes"], layer_linetype=tab["layer_linetype"], fills=tab["fills"],
                      corroboration=co[inp.region_id])
        res = RT.run(inp, frame_insert=None, expected_revision_id=ra.revision_id, selected_region_id=inp.region_id,
                     unrealised=unreal, closure_policy=TC.POLICY_ID, claims=r["claims"],
                     inferred_doors=r["inferred_doors"],
                     provenance={"role_inference": [ERI.POLICY_ID, ERI.policy_record()["digest"]]})
        floors[fl] = {"inp": inp, "eri": r, "res": res, "pass1_decisions": pass1[fl]["decisions"]}
    a2["floors"] = {fl: _floor_facts(fl, v["inp"], v["eri"], v["res"], v["pass1_decisions"], umm)
                    for fl, v in floors.items()}
    ctx["a2_raw"] = floors                                   # engine objects for later phases (never serialised)
    a2["region_leakage"] = _leakage(inputs)
    # ---------------- vertical evidence
    a2["vertical"] = _vertical(ctx, a2)
    # ---------------- structural completion
    a2["footings"] = _footing_completion(ctx, S, us["native_to_mm"] or 1.0)
    a2["columns"], a2["beams"] = _columns(ctx, S), _beams(ctx, S)
    ctx["a2"] = a2
    return ctx


def _leakage(inputs) -> dict:
    seen = defaultdict(list)
    for fl, inp in inputs.items():
        for p in inp.parts:
            seen[p.identity.key].append(fl)
    shared = {k: v for k, v in seen.items() if len(v) > 1}
    return {"state": "NO_LEAKAGE" if not shared else "PARTS_IN_TWO_REGIONS", "shared_parts": len(shared),
            "parts_per_region": {fl: len(inp.parts) for fl, inp in inputs.items()},
            "rule": "each plan region is its own sheet-frame interior; a part belongs to at most one region"}


def _label_values(site):
    vals = [lt.get("value") for lt in (site.get("label_texts") or [])]
    return _english(vals), [v for v in vals if v and v not in _english(vals)]


def _floor_facts(fl, inp, r, res, pass1, umm) -> dict:
    """Everything the registers need from one plan region, as plain data (no engine objects)."""
    u2 = umm * umm / 1e6
    sites = res.get("sites") or []
    parts = {p.identity.key: p for p in inp.parts}
    role_of = {k: a.role for k, a in res["roles"]["roles"].items()}
    # rooms = labelled sites
    rooms = []
    for s in sorted(sites, key=lambda z: z["site_id"]):
        if not s["labels"]:
            continue
        en, other = _label_values(s)
        rl = s.get("boundary_role_lengths", {})
        rooms.append({"floor": fl, "site": s["site_id"], "labels": list(s["labels"]), "label_en": " / ".join(en),
                      "label_other": "UNDECODED_FONT_GLYPH_TEXT" if other else None, "status": s["status"],
                      "issues": list(s["issues"]), "area_m2": round(s["area_m2"], 6),
                      "area_bound_m2": round(s["area_bound_m2"], 6), "perimeter_m": round(s["perimeter"] * umm / 1000, 6),
                      "holes": s.get("holes", 0), "kind": s.get("kind"), "crosscheck": s.get("crosscheck"),
                      "role_lengths_m": {k: round(v * umm / 1000, 6) for k, v in sorted(rl.items())},
                      "contents": dict(s.get("contents", {})), "blocked_by_layers": dict(Counter(
                          CI.effective_layer(parts[k])[0] for k in s.get("blocked_by", []) if k in parts))})
    # openings
    adj = {a["opening"]: a["sites"] for a in (res.get("opening_adjacency") or [])}
    label_of = {s["site_id"]: " / ".join(_label_values(s)[0]) for s in sites}
    doors = []
    for o, st in sorted((res.get("openings") or {}).items()):
        sig = r["inferred_doors"].get(o) or res["roles"]["doors"].get(o) or {}
        doors.append({"floor": fl, "occurrence": o, "basis": "INFERRED_DOOR_MOTIF" if o in r["inferred_doors"] else
                      "GEOMETRY_ROLE_DOOR", "block_name_corroboration": sig.get("block_name"),
                      "leaf_width_mm": round(sig["radius"] * umm, 1) if sig.get("radius") else None,
                      "closure_width_mm": round(st["width"] * umm, 1) if st.get("width") else None,
                      "state": st["state"], "why": st.get("why"),
                      "sites": adj.get(o, []), "rooms": [label_of.get(x, "") for x in adj.get(o, [])],
                      "height": "BLOCKED_HEIGHT (no door schedule; section shows no printed door head)",
                      "material": "BLOCKED_MATERIAL (no door schedule)"})
    windows = []
    gp = set(r["glazing"]["parts"])
    for i, w in enumerate(r["glazing"]["windows"]):
        host = sorted({s["site_id"] for s in sites if set(s.get("boundary_source_ids", [])) & set(w["parts"])})
        windows.append({"floor": fl, "window": f"{fl}-W{i + 1:02d}", "width_mm": w["width_mm"],
                        "wall_thickness_mm": w["thickness_mm"], "parts": len(w["parts"]), "host_sites": host,
                        "host_rooms": [label_of.get(x, "") for x in host if label_of.get(x)],
                        "existence": "GLAZING_IN_WALL_GAP (entity_role_inference)",
                        "height": "BLOCKED_HEIGHT (no sill / head printed for this opening)",
                        "material": "BLOCKED_MATERIAL (no window schedule)"})
    infill = [{"floor": fl, "id": f"{fl}-G{i + 1:02d}", "width_mm": g["width_mm"], "wall_thickness_mm": g["thickness_mm"],
               "type": g["type"], "parts": len(g["parts"])} for i, g in enumerate(r["residual"]["gap_infill"])]
    # wall bands
    bands = []
    for b in (res.get("wall_bands") or {}).get("bands", []):
        t0, t1 = b["interval"]
        ob = sum(iv["s"][1] - iv["s"][0] for iv in b["evidence"].get("intervals", []) if iv["class"] == "OBSTACLE_OVERLAP")
        bands.append({"band": b["band_id"], "state": b["state"], "thickness_mm": round(b["width"] * umm, 1),
                      "length_m": round((t1 - t0) * umm / 1000, 6),
                      "column_overlap_m": round(ob * umm / 1000, 6), "axis": [round(v, 6) for v in b["axis"]]})
    # stairs
    stairs = [{"floor": fl, "layer": x["layer"], "tread_lines": x["tread_lines"], "going_mm": x["going_mm"],
               "width_mm": x["width_mm"], "role": role_of.get(x["parts"][0]),
               "linetype_class": r["observations"].get(x["layer"], {}).get("linetype_class", ERI.LT_UNKNOWN)}
              for x in r["treads"]["runs"]]
    # role inference record (data only)
    eri = {"decisions": {str(k): v for k, v in r["decisions"].items()},
           "pass1_states": {str(k): v["state"] for k, v in pass1.items()},
           "observations": {str(k): v for k, v in r["observations"].items()},
           "glazing_share": {str(k): v for k, v in r["glazing_share"].items()},
           "claims": [ERI.claim_record(c) for c in r["claims"]],
           "frames": [{"bounds": [round(v, 3) for v in f["bounds"]], "aspect": f["aspect"],
                       "content_share": f["content_share"], "parts": len(f["parts"])} for f in r["frames"]["frames"]],
           "doors_found": len(r["inferred_doors"]), "doors_rejected": dict(Counter(x["why"] for x in r["doors"]["rejected"])),
           "glazing_parts": len(gp), "windows": len(windows), "tread_runs": len(stairs),
           "plot_boundary_parts": len(r["plot_boundary"]["parts"]),
           "occurrences": dict(Counter(v["role"] for v in r["occurrences"].values())),
           "residual": dict(Counter(r["residual"]["parts"].values())), "gap_infill": len(infill),
           "part_roles": dict(Counter(r["part_roles"].values())),
           "unresolved_parts": sum(1 for k, a in res["roles"]["roles"].items() if a.role in ("UNKNOWN_PHYSICAL",
                                                                                            "UNKNOWN_PRESENTATION"))}
    topo = {"state": res["state"], "sites": len(sites), "by_status": dict(Counter(s["status"] for s in sites)),
            "issues": dict(sorted(Counter(i for s in sites for i in s["issues"]).items())),
            "labelled_sites": sum(1 for s in sites if s["labels"]),
            "certified_labelled_sites": sum(1 for s in sites if s["labels"] and s["status"] == "CERTIFIED"),
            "wall_bands": dict(Counter(b["state"] for b in bands)),
            "openings": dict(Counter(d["state"] for d in doors)),
            "inferred_doors_admitted": dict(Counter((res["roles"].get("inferred_doors") or {}).values())),
            "unrealised": {"blocking_input": [x["disposition"] for x in res["unrealised"].get("blocking_input", [])],
                           "recorded": [x.get("disposition") for x in res["unrealised"].get("recorded", [])]},
            "result_digest": TD.digest(res)["sha256"],
            "run_input_digest": (res.get("run_manifest") or {}).get("RUN_INPUT_DIGEST")}
    labels_all = [t for t in inp.texts if t.visibility == CI.VISIBLE]
    troles = res["roles"]["text_roles"]
    est = sorted({(t.identity.instance_handles or ("E" + str(t.identity.source_handle),))[0] for t in labels_all
                  if troles[t.identity.key].role == TX.ROOM_LABEL_ESTABLISHED})
    return {"eri": eri, "topology": topo, "rooms": rooms, "doors": doors, "windows": windows, "gap_infill": infill,
            "bands": bands, "stairs": stairs, "established_label_occurrences": len(est), "unit_area": u2}


def _vertical(ctx, a2) -> dict:
    """Raster transcriptions + CAD plan / elevation level marks -> per-floor vertical evidence and floor-to-floor
    heights as DIFFERENCES OF PRINTED VALUES, cross-checked against printed dimension chains."""
    cad = {}
    for fl in FLOORS:
        vals = sorted({r["value_m"] for r in ctx["arch"][fl]["levels"]})
        cad[fl] = vals
    ffl = {}
    for v in VERTICAL_TRANSCRIPTIONS:
        if v["kind"] in ("FFL", "ROOF_LEVEL") and v.get("floor"):
            ffl.setdefault(v["floor"], set()).add(v["value_m"])
    order = [("GF", "1F"), ("1F", "2F"), ("2F", "ROOF")]
    chains = sorted({c for v in VERTICAL_TRANSCRIPTIONS if v["kind"] == "DIMENSION_CHAIN" for c in v["values_cm"]})
    f2f = []
    for lo, hi in order:
        a, b = ffl.get(lo, set()), ffl.get(hi, set())
        if len(a) != 1 or len(b) != 1:
            f2f.append({"from": lo, "to": hi, "state": "BLOCKED", "why": "level not unique on the sections"})
            continue
        d = round(next(iter(b)) - next(iter(a)), 3)
        printed = round(d * 100) in chains
        cad_ok = lo in cad and next(iter(a)) in cad[lo]
        f2f.append({"from": lo, "to": hi, "ffl_from_m": next(iter(a)), "ffl_to_m": next(iter(b)),
                    "floor_to_floor_m": d, "printed_dimension_agrees": printed,
                    "cad_plan_level_agrees": cad_ok,
                    "state": "EVIDENCE_CORROBORATED" if printed else "EVIDENCE_SINGLE_CHANNEL",
                    "use": "vertical EVIDENCE only: a clear (wall-face) height also needs the slab thickness AND the "
                           "floor build-up and any false ceiling - the build-up is not in the source"})
    return {"items": VERTICAL_TRANSCRIPTIONS, "cad_plan_levels_m": cad, "floor_to_floor": f2f,
            "pdf": SECTION_PDF, "pages": [10, 11], "method": "transcribed by eye from 150 dpi renders of the delivered "
            "raster pages; no OCR; no pixel measurement; scale never derived from pixels",
            "clear_height": "BLOCKED: FFL-to-FFL minus structural slab (16 / 18 cm, ST7757 labels) minus floor build-up "
                            "(NOT IN SOURCE) minus false ceiling (NOT IN SOURCE)"}


def _footing_completion(ctx, S, umm) -> dict:
    ss = ctx["structural_sheets"]["FOUNDATION"]["bounds"]
    inb = lambda x, y: AP.in_box(x, y, ss)
    seg = lambda layers: [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT"
                          and CI.effective_layer(p)[0] in layers and inb(p.geometry[0], p.geometry[1])
                          and inb(p.geometry[2], p.geometry[3])]
    fs = seg({"S-FOOTINGS"})
    sup = seg({"S-BOUN", "S-BW"})
    rects = SQ.rectangles(fs, eps=AP.EPS)
    tags = [{"key": t.identity.key, "value": t.value.strip(), "x": t.x, "y": t.y} for t in S["texts"]
            if t.x is not None and t.value and inb(t.x, t.y) and AP.footing_tag_types(t.value.strip())
            and t.value.strip().upper() not in ("FOUNDATION PLAN.",) and len(t.value.strip()) <= 8]
    assoc = SQ.associate(rects, tags)
    taken = [r["bounds"] for r in assoc["rectangles"] if len(r["tags"]) == 1]
    orph = defaultdict(list)
    for o in assoc["orphans"]:
        orph[AP.footing_tag_types(o["value"])].append(o)
    cs = [p for p in S["parts"] if p.kind == "SEGMENT" and CI.effective_layer(p)[0] == "S-COL.BON"
          and inb(p.geometry[0], p.geometry[1])]
    carriers = [r[3] for r in ERI._rectangles([tuple(p.geometry) for p in cs], [p.identity.key for p in cs], umm)]
    ft = ctx["footing_schedule"]
    cand = {t: (SQ.template_outlines(fs, ft[t]["L_cm"] * 10, ft[t]["W_cm"] * 10, umm, eps=AP.EPS, support=sup)
                if t in ft and ft[t]["L_cm"] and ft[t]["W_cm"] else []) for t in orph}
    res = SQ.complete_by_count(dict(orph), cand, taken=taken, carriers=carriers,
                               tags=[(t["x"], t["y"]) for t in tags])
    return {"policy": SQ.completion_policy_record(), "orphans": {k: [o["value"] for o in v] for k, v in orph.items()},
            "result": res, "carriers": len(carriers), "matched_before": len(taken)}


def _columns(ctx, S) -> dict:
    cb = ctx["structural_sheets"]["COLUMN_AXIS"]["bounds"]
    cs = [p for p in S["parts"] if p.kind == "SEGMENT" and CI.effective_layer(p)[0] == "S-COL.BON"
          and AP.in_box(p.geometry[0], p.geometry[1], cb)]
    rects = ERI._rectangles([tuple(p.geometry) for p in cs], [p.identity.key for p in cs], 1.0)
    tags = [(t.value.strip(), t.x, t.y) for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, cb)
            and t.layer == "S-TEXT" and t.value.strip() in set(AP.ctype_names(ctx["schedules"]["COLUMNS"]))]
    return {"outlines_on_column_plan": len(rects), "outline_sizes_mm": dict(Counter(
        f"{min(r[1], r[2]):.0f}x{max(r[1], r[2]):.0f}" for r in rects)), "tags": dict(Counter(t[0] for t in tags))}


def _beams(ctx, S) -> dict:
    types = [r["type"] for r in ctx["schedules"]["SIMPLE_BEAMS"]["records"]]
    out = {}
    for key in ("GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB", "GROUND_BEAMS"):
        sb = ctx["structural_sheets"].get(key)
        if not sb:
            continue
        c = Counter(t.value.strip() for t in S["texts"] if t.x is not None and t.value and
                    AP.in_box(t.x, t.y, sb["bounds"]) and t.value.strip() in set(types))
        out[key] = dict(sorted(c.items()))
    return {"schedule_types": types, "tags_per_sheet": out}


def main(work, regdir, commit=None):
    import alsenan_a2_registers as REGS
    ctx = build(work, commit)
    regs = REGS.registers(ctx)
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    fz = regs["ALSENAN_P7757_ST7757_PHASE_A2_FREEZE"]
    print(json.dumps({"firewall": regs["BENCHMARK_FIREWALL"]["audit_verdict"]["state"],
                      "freeze_schema": fz["schema_validation"]["state"], "units": fz["units"], "counts": fz["counts"],
                      "xlsx": regs["QA_RECONCILIATION"]["xlsx"]["readback"]["state"]}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
