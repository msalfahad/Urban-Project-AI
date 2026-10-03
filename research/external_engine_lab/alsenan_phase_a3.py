"""ALSENAN / P7757 + ST7757 - PHASE A3 (SOURCE-ONLY; SCHEDULE-DRIVEN STRUCTURE + OWNER FACTS + ROOM RECOVERY;
SHADOW; the last source-only freeze before any benchmark).

    python3 research/external_engine_lab/alsenan_phase_a3.py <work_dir> <register_dir> [code_commit]

PROJECT ADAPTER (facts only) on top of the A2 adapter (which reruns the generic engines from source - role
inference now also carries the CURVED_GLAZING and COUNTER_RUN joinery motifs). A3 adds:
    structure    engine/source/structural_schedule (STRUCTURAL_SCHEDULE_QTO_V1): plan mark = type identity,
                 schedule = nominal size, plan geometry = validation; footings, strap beams, columns per storey,
                 beams by mark with sections (simple-beam schedule from the CAD table; continuous-beam schedules
                 TRANSCRIBED from ST7757.pdf pages 11-12, whose text is drawn as vector glyphs and cannot be
                 extracted), slab evidence, rebar DEFINITIONS (weights blocked)
    owner facts  three statements of the owner for THIS project, each scoped and stored with its authority
                 (OWNER_FACT / PROJECT_OWNER_DERIVED_DIMENSION); none is globalised
    architecture curved glazing length, the salon sea-view opening (width source-proved, height owner-derived),
                 the reception DOUBLE_HEIGHT_ZONE (plan VOID + section levels), certified physical sites with or
                 without a readable label
No layer map, handle list or coordinate list; no Qortuba fact; no benchmark value.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import benchmark_firewall as FW, canonical_input as CI, entity_role_inference as ERI  # noqa: E402
from engine.source import structural_qto as SQ, structural_schedule as SS                              # noqa: E402

import alsenan_phase_a as AP                                                                      # noqa: E402
import alsenan_phase_a2 as A2                                                                     # noqa: E402

PHASE = "ALSENAN_P7757_ST7757_PHASE_A3"
FLOORS = A2.FLOORS
ST_PDF = "ST7757.pdf"

# ------------------------------------------------------------------ continuous-beam schedules (transcribed)
# ST7757.pdf pages 11 (two-span, two tables) and 12 (three-span). The page text is drawn as vector glyphs (no text
# layer); each row was read from the rendered page (crop in PDF points) and is stored as a transcription with a
# confidence - B / H in cm, spans in m exactly as printed (structural analysis spans between supports).
CB_TRANSCRIPTION = [
    {"type": "CB1", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - left", "crop_pt": [150, 100, 560, 800],
     "B_cm": 35, "H_cm": 75, "spans_m": [7.5, 5.7], "confidence": "HIGH"},
    {"type": "CB2", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - left", "crop_pt": [150, 100, 560, 800],
     "B_cm": 20, "H_cm": 50, "spans_m": [4.0, 4.0], "confidence": "HIGH"},
    {"type": "CB4", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - left", "crop_pt": [150, 100, 560, 800],
     "B_cm": 20, "H_cm": 50, "spans_m": [3.3, 3.7], "confidence": "HIGH"},
    {"type": "CB5", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - left", "crop_pt": [150, 100, 560, 800],
     "B_cm": 20, "H_cm": 40, "spans_m": [2.5, 4.5], "confidence": "HIGH"},
    {"type": "CB6", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - left", "crop_pt": [150, 100, 560, 800],
     "B_cm": 20, "H_cm": 75, "spans_m": [4.4, 6.3], "confidence": "HIGH"},
    {"type": "CB7", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - right", "crop_pt": [595, 100, 1010, 560],
     "B_cm": 20, "H_cm": 75, "spans_m": [6.0, 6.1], "confidence": "HIGH"},
    {"type": "CB10", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - right", "crop_pt": [595, 100, 1010, 560],
     "B_cm": 25, "H_cm": 50, "spans_m": [3.0, 4.1], "confidence": "HIGH"},
    {"type": "CB12", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - right", "crop_pt": [595, 100, 1010, 560],
     "B_cm": 25, "H_cm": 75, "spans_m": [6.1, 5.5], "confidence": "HIGH"},
    {"type": "CB13", "page": 11, "table": "CONTINUES BEAMS (2 SPAN) - right", "crop_pt": [595, 380, 1010, 560],
     "B_cm": 30, "H_cm": 50, "spans_m": [3.7, 3.6], "confidence": "MEDIUM (read at 60 dpi overview)"},
    {"type": "CB3", "page": 12, "table": "CONTINUES BEAMS (THREE SPAN)", "crop_pt": [260, 240, 880, 690],
     "B_cm": 20, "H_cm": 75, "spans_m": [3.4, 3.3, 3.8], "confidence": "HIGH"},
    {"type": "CB8", "page": 12, "table": "CONTINUES BEAMS (THREE SPAN)", "crop_pt": [260, 240, 880, 690],
     "B_cm": 30, "H_cm": 75, "spans_m": [3.7, 6.4, 6.8], "confidence": "HIGH"},
    {"type": "CB9", "page": 12, "table": "CONTINUES BEAMS (THREE SPAN)", "crop_pt": [260, 240, 880, 690],
     "B_cm": 20, "H_cm": 50, "spans_m": [4.1, 4.0, 3.7], "confidence": "HIGH"},
    {"type": "CB11", "page": 12, "table": "CONTINUES BEAMS (THREE SPAN)", "crop_pt": [215, 200, 760, 570],
     "B_cm": 30, "H_cm": 75, "spans_m": [7.1, 3.2, 3.7], "confidence": "MEDIUM (read at 60 dpi overview)"},
]

# ------------------------------------------------------------------ owner statements (THIS project only)
OWNER_FACTS = [
    {"id": "OF-A3-SALON-MATERIAL", "authority": "OWNER_FACT", "scope": {"floor": "GF", "label": "SALOON",
     "element": "sea-view opening"}, "fact": {"material": "ALUMINIUM_GLASS"},
     "statement": "SALON sea-view opening is aluminium + glass"},
    {"id": "OF-A3-SALON-HEIGHT", "authority": "PROJECT_OWNER_DERIVED_DIMENSION",
     "scope": {"floor": "GF", "label": "SALOON", "element": "sea-view opening"},
     "fact": {"finished_aluminium_height_m": 3.65},
     "derivation": {"floor_to_floor_m": 4.50, "minus_beam_depth_approx_m": 0.60, "minus_ceiling_allowance_m": 0.15,
                    "minus_floor_build_up_allowance_m": "<= 0.10", "result_m": "approximately 3.65"},
     "not": ["a source-measured height", "a wall / ceiling / blockwork / dry-wall height",
             "a height for any other opening (master-bedroom glazing included)",
             "a beam depth (the 0.60 m inside the derivation is an allowance, not a beam fact)"],
     "precedence": "an explicit SOURCE opening height, if one is found later, outranks this value; both are kept"},
    {"id": "OF-A3-RECEPTION-DOUBLE-HEIGHT", "authority": "OWNER_FACT", "scope": {"floor": "GF", "label": "RECEPTION"},
     "fact": {"zone": "DOUBLE_HEIGHT", "with": ["stair volume", "open vertical volume (munawwar)"]},
     "statement": "RECEPTION is double height, with the stair and the open vertical volume"},
    {"id": "OF-A3-MASTER-BED-GLAZING", "authority": "OWNER_FACT",
     "scope": {"label": "MASTER BED ROOM", "side": "pool"},
     "fact": {"material": "ALUMINIUM_GLAZING", "form": "CURVED"},
     "statement": "MASTER BEDROOM has curved aluminium glass facing the pool",
     "not": ["the salon width", "the salon height"]},
]
SALON_WIDTH_TOL_MM = 10.0                     # the owner-stated width must match exactly one source opening
STRUCT_LAYERS = {"text": "S-TEXT", "footing": "S-FOOTINGS", "column": "S-COL.BON", "support": ("S-BOUN", "S-BW")}
STOREY_SHEETS = {"FOUNDATION": "COLUMN_AXIS", "GROUND FLOOR": "GF_ROOF_SLAB", "1ST FLOOR": "1F_ROOF_SLAB",
                 "2ND FLOOR & TOP": "2F_ROOF_SLAB"}


# ------------------------------------------------------------------ build
def build(work, commit=None) -> dict:
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    fw_census = AP.firewall_census()
    fw_census["scratch_disclosure"] = AP.scratch_disclosure(work)
    loaded_before = set(sys.modules)
    with FW.OpenAudit() as audit:
        ctx = A2._build(work)
        ctx["a3"] = _a3(ctx, work)
    ctx["code_commit"] = commit
    ctx["firewall"] = {"census": fw_census, "audit": audit.opened, "modules_loaded_during_build":
                       sorted(set(sys.modules) - loaded_before), "modules_all": sorted(sys.modules)}
    return ctx


def _blob(ctx, work, name):
    rev = AP.REV_STR if name == "ST7757.dxf" else AP.REV_ARCH
    return AP.k2(work / ctx["paths"][name], rev, work / f"k2_{AP.FILES[name][0][:16]}.pkl")


def _segs(S, bounds, layers, both_ends=True):
    inb = lambda x, y: AP.in_box(x, y, bounds)
    return [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT"
            and CI.effective_layer(p)[0] in layers and inb(p.geometry[0], p.geometry[1])
            and (not both_ends or inb(p.geometry[2], p.geometry[3]))]


def _marks(S, bounds, types, *, layer=None, normalise=False):
    out, rejected = [], []
    for t in sorted(S["texts"], key=lambda z: z.identity.key):
        if t.x is None or not t.value or not AP.in_box(t.x, t.y, bounds):
            continue
        if layer and t.layer != layer:
            continue
        pm = SS.parse_mark(t.value.strip(), types, normalise=normalise)
        if len(pm["types"]) == 1:
            out.append({"key": t.identity.key, "value": t.value.strip(), "x": t.x, "y": t.y, "type": pm["types"][0],
                        "normalised": pm["normalised"]})
        elif len(pm["types"]) > 1:
            rejected.append({"key": t.identity.key, "value": t.value, "why": "names several types"})
    return out, rejected


def _col_rects(S, bounds, umm):
    cs = [p for p in S["parts"] if p.kind == "SEGMENT" and CI.effective_layer(p)[0] == STRUCT_LAYERS["column"]
          and AP.in_box(p.geometry[0], p.geometry[1], bounds)]
    return ERI._rectangles([tuple(p.geometry) for p in cs], [p.identity.key for p in cs], umm)


def _a3(ctx, work) -> dict:
    S = _blob(ctx, work, "ST7757.dxf")
    us = ctx["a2"]["units"]["STRUCTURAL"]
    umm = us["native_to_mm"] or 1.0
    out = {"units": {"STRUCTURAL": us["status"], "native_to_mm": umm}}
    out["footings"] = _footings(ctx, S, umm)
    out["straps"] = _straps(ctx, S, umm, out["footings"]["candidates"], out["footings"]["rows"])
    out["columns"] = _columns(ctx, S, umm)
    out["beams"] = _beams(ctx, S, umm)
    out["slabs"] = _slabs(ctx, S)
    out["rebar"] = _rebar(ctx, out)
    out["concrete"] = _concrete(out)
    out["owner_facts"] = OWNER_FACTS
    out["architecture"] = _architecture(ctx, work)
    out["h_audit"] = _h_audit(out)
    for k in ("footings",):
        out[k].pop("candidates", None)
    return out


# ------------------------------------------------------------------ footings
def _footings(ctx, S, umm) -> dict:
    fb = ctx["structural_sheets"]["FOUNDATION"]["bounds"]
    lib = ctx["footing_schedule"]
    fs = _segs(S, fb, {STRUCT_LAYERS["footing"]})
    sup = _segs(S, fb, set(STRUCT_LAYERS["support"]))
    rings = SS.entity_rings(fs, eps=AP.EPS)
    rects = [SS.rect_candidate(r) for r in SQ.rectangles(fs, eps=AP.EPS)]
    tmpl = {t: SQ.template_outlines(fs, v["L_cm"] * 10, v["W_cm"] * 10, umm, eps=AP.EPS, support=sup)
            for t, v in lib.items() if v["L_cm"] and v["W_cm"]}
    cands = SS.merge_candidates(rings, rects, [SS.rect_candidate(c, "TEMPLATE") for v in tmpl.values() for c in v])
    carriers = [r[3] for r in _col_rects(S, fb, umm)]
    marks, rej = _marks(S, fb, list(lib))
    res = SS.footing_occurrences(marks, lib, cands, umm=umm, tol_mm=1.0, eps=AP.EPS, templates_by_type=tmpl,
                                 carriers=carriers)
    summary = SS.type_summary(res["rows"], lib)
    recon = SS.reconcile(marks, res["rows"], lib)
    # forensic record for every combined / conflicting outline (source entities, never a matcher composite)
    col_tags = [t for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, fb)
                and re.fullmatch(r"C\d*|CN", t.value.strip() or "")]
    by_outline = defaultdict(list)
    for r in res["rows"]:
        if r["geometry_state"] in SS.CONFLICT_STATES:
            by_outline[r["geometry"]["outline"]].append(r)
    forensic = []
    for oid, rs in sorted(by_outline.items()):
        c = next(x for x in cands if x["id"] == oid)
        cols = [r for r in _col_rects(S, fb, umm) if SS.contains(c, *r[3])]
        forensic.append({
            "outline": oid, "kind": c["kind"], "source_keys": c["keys"], "polygon": [list(p) for p in c["polygon"]],
            "bounds": list(c["bounds"]), "drawn_mm": rs[0]["geometry"]["drawn_mm"], "state": c["state"],
            "entering_element_keys": c.get("gap_keys", []),
            "marks_inside": [{"type": r["type"], "key": r["mark_key"], "xy": r["mark_xy"],
                              "schedule_cm": [r["schedule_row"]["L_cm"], r["schedule_row"]["W_cm"], r["schedule_row"]["H_cm"]]}
                             for r in rs],
            "columns_inside": [{"keys": list(k[0]), "w_mm": k[1], "h_mm": k[2], "centre": [round(v, 3) for v in k[3]]}
                               for k in cols],
            "column_tags_inside": sorted(t.value.strip() for t in col_tags if SS.contains(c, t.x, t.y)),
            "explicit_local_dimensions": [],
            "a2_claims_explained": ("A2 clipped this ONE outline at the entering element: the parts on either side "
                                    "of it were reported as separate candidate sizes; neither is drawn as a footing"),
            "classification": "COMBINED_OUTLINE (one source outline enclosing differently typed marks)"})
    # explicit local footing dimensions on the footing layer (the only override source)
    fdims = []
    for d in S["dims"]:
        if d.layer == STRUCT_LAYERS["footing"] and all(AP.in_box(*p, fb) for p in d.placed_points):
            (x1, y1), (x2, y2) = d.placed_points[:2]
            L = math.hypot(x2 - x1, y2 - y1) * umm
            fdims.append({"handle": d.identity.source_handle, "length_mm": round(L, 1),
                          "printed_cm": round(d.measurement, 3), "points": [[round(v, 3) for v in p] for p in d.placed_points]})
    for f in forensic:                                       # a dimension binds only when BOTH its points lie on
        b = f["bounds"]                                      # this outline's extent
        f["explicit_local_dimensions"] = [x["handle"] for x in fdims if all(
            b[0] - AP.EPS <= p[0] <= b[2] + AP.EPS and b[1] - AP.EPS <= p[1] <= b[3] + AP.EPS for p in x["points"])]
    return {"policy": SS.policy_record(), "completion_policy": SQ.completion_policy_record(),
            "library": {t: dict(v, source="SCHEDULE OF FOOTINGS (CAD table, cm)") for t, v in sorted(lib.items())},
            "marks": len(marks), "marks_rejected": rej, "rows": res["rows"], "summary": summary,
            "reconciliation": recon, "completion": res["completion"], "bindings": res["bindings"],
            "forensic": forensic, "footing_layer_dimensions": fdims,
            "candidates_count": {"entity_rings": len(rings), "rectangles": len(rects),
                                 "templates": sum(len(v) for v in tmpl.values()), "merged": len(cands)},
            "candidates": cands}


def _simple_beam_library(ctx):
    lib = {}
    for r in ctx["schedules"]["SIMPLE_BEAMS"]["records"]:
        B = next((c for c in r["cells"] if c["path"][-1:] == ["B-(Bredth)"]), None)
        D = next((c for c in r["cells"] if c["path"][-1:] == ["D-(Depth)"]), None)
        cell = lambda w: next((c["value"] for c in r["cells"] if c["path"][-1:] == [w]), None)
        lib[r["type"]] = {"B_cm": AP.num(B and B["value"]), "D_cm": AP.num(D and D["value"]),
                          "bottom": cell("B O T T O M"), "top": cell("T O P B A R S"), "stirrups": cell("STIRRUPS/m"),
                          "remarks": cell("REMARKS"), "source": "SCHEDULE OF SIMPLE BEAMS (CAD table, cm)"}
    return lib


def _straps(ctx, S, umm, cands, occurrences=()) -> dict:
    fb = ctx["structural_sheets"]["FOUNDATION"]["bounds"]
    lib = {k: v for k, v in _simple_beam_library(ctx).items() if k.startswith("SB")}
    marks, _ = _marks(S, fb, list(lib), normalise=True)
    lines = _segs(S, fb, {STRUCT_LAYERS["footing"]})
    supports = [c for c in cands if c["kind"] in ("ENTITY_RING", "RECTANGLE", "TEMPLATE")]
    rows = SS.beam_bands(marks, lib, lines, umm=umm, tol_mm=ERI.PHYSICAL_MM["authoring_tolerance"], eps=AP.EPS,
                         supports=supports)
    for r, m in zip(rows, sorted(marks, key=lambda z: z["key"])):
        r["mark_normalised"] = m["normalised"]
        r["status"] = SQ.COMPLETE if r["state"].startswith("MEASURED") else SQ.BLOCKED
        dep = sorted({o["geometry"]["outline"] for o in occurrences
                      if o["geometry_state"].startswith("SOURCE_CONFLICT") and (o.get("geometry") or {}).get("outline")
                      and o["geometry"]["outline"] in (r.get("clear") or [])})
        r["support_outline_conflicts"] = dep
        if dep:
            r["dependency"] = ("a clear end lies on a drawn face of an outline whose footing size is a SOURCE_CONFLICT; "
                               "the strap length is measured to that face as drawn and moves only if the owner answer "
                               "moves that face")
    return {"library": lib, "rows": rows,
            "rule": "strap = mark between a parallel pair of footing-layer lines at the scheduled breadth "
                    f"(+- {ERI.PHYSICAL_MM['authoring_tolerance']} mm authoring tolerance); clear length between the "
                    "footing outlines it joins; volume = clear length x B x D"}


# ------------------------------------------------------------------ columns
BAND_NAMES = (("FOUNDATION", "FOUNDATION"), ("GROUND", "GROUND FLOOR"), ("1ST", "1ST FLOOR"), ("2ND", "2ND FLOOR & TOP"))


def column_library(sched) -> dict:
    """Schedule storey bands from the header path of each cell; per band the first two numeric cells are B and D
    (cm) and the cell holding a bar mark is the reinforcement. A band without both sizes is not scheduled."""
    lib = {}
    for r in sched["records"]:
        bands = defaultdict(list)
        for c in r["cells"]:
            top = (c["path"][0] if c["path"] else "").upper()
            name = next((n for w, n in BAND_NAMES if w in top), None)
            if name:
                bands[name].append(c)
        lib[r["type"]] = {}
        for _, name in BAND_NAMES:
            cs = bands.get(name, [])
            nums = [AP.num(c["value"]) for c in cs if AP.num(c["value"]) is not None]
            reinf = next((c["value"] for c in cs if "Ø" in c["value"] and re.search(r"\d", c["value"])), None)
            lib[r["type"]][name] = ({"B_cm": nums[0], "D_cm": nums[1], "reinf": reinf} if len(nums) >= 2 else
                                    {"B_cm": None, "D_cm": None, "reinf": reinf})
    return lib


def _columns(ctx, S, umm) -> dict:
    cb = ctx["structural_sheets"]["COLUMN_AXIS"]["bounds"]
    lib = column_library(ctx["schedules"]["COLUMNS"])
    marks, _ = _marks(S, cb, list(lib), layer=STRUCT_LAYERS["text"])
    labels = [t.value.strip() for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, cb)
              and SS.SIZE_LABEL.match(t.value.strip())]
    outl = {}
    for band, sheet in STOREY_SHEETS.items():
        sb = ctx["structural_sheets"].get(sheet)
        if sb:
            outl[band] = [(r[1], r[2]) for r in _col_rects(S, sb["bounds"], umm)]
    res = SS.column_storeys(lib, marks, size_labels=labels, per_sheet_outlines=outl)
    res["library"] = lib
    res["_occ"] = [(m["key"], m["type"], m["value"]) for m in marks]
    res["schedule_state"] = ctx["schedules"]["COLUMNS"]["state"]
    res["height"] = ("BLOCKED_HEIGHT: no structural level, slab-soffit or joint level is given in the structural "
                     "source; architectural floor-to-floor is NOT a column concrete height")
    res["sheet_for_band"] = STOREY_SHEETS
    return res


# ------------------------------------------------------------------ beams
def _beams(ctx, S, umm) -> dict:
    simple = _simple_beam_library(ctx)
    cb = {r["type"]: dict(r, source=f"{ST_PDF} p.{r['page']} {r['table']} (transcribed)") for r in CB_TRANSCRIPTION}
    types = sorted(set(simple) | set(cb) | {f"CB{i}" for i in range(1, 30)}, key=SS._type_key)
    sheets = {}
    for key in ("GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB", "GROUND_BEAMS"):
        sb = ctx["structural_sheets"].get(key)
        if not sb:
            continue
        marks, _ = _marks(S, sb["bounds"], types)
        marks = [m for m in marks if not m["type"].startswith("SB")]
        lines = _segs(S, sb["bounds"], {"1"}, both_ends=False)
        H, V = SQ.edges(lines, eps=AP.EPS)
        merged = [(f"H{i}:{'+'.join(k[:3])}", a, y, c, y) for i, (y, a, c, k) in enumerate(H)] + \
                 [(f"V{i}:{'+'.join(k[:3])}", x, a, x, c) for i, (x, a, c, k) in enumerate(V)]
        cols = [SS.rect_candidate({"bounds": (r[3][0] - r[1] / 2 / umm, r[3][1] - r[2] / 2 / umm,
                                              r[3][0] + r[1] / 2 / umm, r[3][1] + r[2] / 2 / umm)})
                for r in _col_rects(S, sb["bounds"], umm)]
        slib = {t: {"B_cm": v["B_cm"], "D_cm": v["D_cm"]} for t, v in simple.items()}
        bands = SS.beam_bands([m for m in marks if m["type"] in slib], slib, merged, umm=umm,
                              tol_mm=ERI.PHYSICAL_MM["authoring_tolerance"], eps=AP.EPS, supports=cols)
        sheets[key] = {"marks": dict(sorted(Counter(m["type"] for m in marks).items(), key=lambda kv: SS._type_key(kv[0]))),
                       "simple_band_states": dict(Counter(b["state"] for b in bands)), "simple_bands": bands}
    rows = []
    for t in types:
        per = {k: v["marks"].get(t, 0) for k, v in sheets.items()}
        n = sum(per.values())
        if not n and t not in simple and t not in cb:
            continue
        if t in cb:
            c = cb[t]
            L = round(sum(c["spans_m"]), 6)
            rows.append({"type": t, "kind": "CONTINUOUS", "marks_per_sheet": per, "marks": n, "B_cm": c["B_cm"],
                         "D_cm": c["H_cm"], "section_source": c["source"], "section_confidence": c["confidence"],
                         "spans_m": c["spans_m"], "length_basis": "SCHEDULE SPANS (centre line between supports)",
                         "length_m": L, "marks_vs_spans": f"{n} mark(s) / {len(c['spans_m'])} span(s)",
                         "gross_volume_on_spans_m3_info": round(L * c["B_cm"] * c["H_cm"] / 1e4, 6),
                         "volume_m3": None, "status": SQ.BLOCKED,
                         "blocker": "BEAM_CLEAR_LENGTH_NOT_PROVED: the schedule spans run between support centres; "
                                    "the clear length (support faces) and the slab / beam overlap are not resolved"})
        elif t in simple:
            s = simple[t]
            meas = [b for v in sheets.values() for b in v["simple_bands"] if b["type"] == t
                    and b["state"].startswith("MEASURED")]
            rows.append({"type": t, "kind": "SIMPLE" if not t.startswith("SB") else "STRAP (foundation plan)",
                         "marks_per_sheet": per, "marks": n, "B_cm": s["B_cm"], "D_cm": s["D_cm"],
                         "section_source": s["source"], "length_basis": "PLAN BAND bound by containment",
                         "measured_occurrences": len(meas), "length_m": None if len(meas) < n or not n else
                         round(sum(b["length_m"] for b in meas), 6), "volume_m3": None,
                         "status": SQ.BLOCKED if not t.startswith("SB") else "SEE_STRAPS",
                         "blocker": None if t.startswith("SB") else
                         "BEAM_PLAN_EXTENT_NOT_PROVED: the mark is written beside the beam band, not inside it; "
                         "binding it by distance is refused"})
        else:
            rows.append({"type": t, "kind": "CONTINUOUS", "marks_per_sheet": per, "marks": n, "B_cm": None, "D_cm": None,
                         "section_source": None, "length_m": None, "volume_m3": None, "status": SQ.BLOCKED,
                         "blocker": "SECTION_NOT_IN_ANY_SCHEDULE"})
    return {"simple_library": simple, "continuous_library": cb, "sheets": sheets, "rows": rows,
            "transcription": {"pdf": ST_PDF, "pages": [11, 12], "why": "schedule text drawn as vector glyphs (no text "
                              "layer); values read from the rendered page, no pixel measurement"}}


# ------------------------------------------------------------------ slabs
def _slabs(ctx, S) -> dict:
    out = {}
    for key in ("GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB"):
        sb = ctx["structural_sheets"].get(key)
        if not sb:
            continue
        tx = [t for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, sb["bounds"])]
        ts = [t for t in tx if t.value.strip() == "T"]
        thick = Counter()
        for t in ts:                                                          # 'T' over the thickness inside one tag
            below = [u for u in tx if u is not t and re.fullmatch(r"\d{2}", u.value.strip())
                     and abs(u.x - t.x) < 300 and 0 < t.y - u.y < 500]
            if len(below) == 1:
                thick[int(below[0].value.strip())] += 1
        out[key] = {"thickness_marks_cm": dict(thick), "void_labels": sum(1 for t in tx if t.value.strip().upper() == "VOID"),
                    "as_per_schedule_notes": sum(1 for t in tx if "AS PER SCH" in t.value.upper()),
                    "opening_layer_segments": sum(1 for p in S["parts"] if p.kind == "SEGMENT" and
                                                  CI.effective_layer(p)[0] == "S-OPENING"
                                                  and AP.in_box(p.geometry[0], p.geometry[1], sb["bounds"])),
                    "area_m2": None, "volume_m3": None,
                    "blocker": "SLAB_OUTLINE_NOT_ESTABLISHED: no closed slab-edge outline with role authority; voids / "
                               "openings and the beam overlap are not resolved",
                    "thickness_state": "PRINTED" if thick else "NOT_PRINTED"}
    return out


# ------------------------------------------------------------------ rebar definitions
def _rebar(ctx, out) -> dict:
    rows = [{"element": "FOOTING", "type": t, "fields": {k: v[k] for k in ("short_bars", "long_bars") if v.get(k)}}
            for t, v in sorted(ctx["footing_schedule"].items(), key=lambda kv: SS._type_key(kv[0]))]
    for t, bands in sorted(out["columns"]["library"].items(), key=lambda kv: SS._type_key(kv[0])):
        rows.append({"element": "COLUMN", "type": t, "fields": {b: s["reinf"] for b, s in bands.items() if s.get("reinf")}})
    for t, s in sorted(out["beams"]["simple_library"].items(), key=lambda kv: SS._type_key(kv[0])):
        rows.append({"element": "BEAM" if not t.startswith("SB") else "STRAP", "type": t,
                     "fields": {k: s[k] for k in ("bottom", "top", "stirrups") if s.get(k)}})
    defs = SS.rebar_definitions(rows)
    for d in defs:
        if d["element"] == "FOOTING":
            d["boxed"] = ctx["footing_schedule"][d["type"]].get("short_bars_sub_rows")
    return {"definitions": defs, "continuous_beams": "bar layout is in the PDF schedule drawings; not transcribed bar by "
                                                     "bar -> definition PARTIAL, weight BLOCKED",
            "tonnage_kg": None, "never": "kg/m3"}


def _concrete(out) -> dict:
    f = [r for r in out["footings"]["rows"] if r["status"] == SQ.COMPLETE]
    s = [r for r in out["straps"]["rows"] if r["status"] == SQ.COMPLETE]
    tot = round(sum(r["qty"] for r in f) + sum(r["volume_m3"] for r in s), 6)
    return {"footings_m3": round(sum(r["qty"] for r in f), 6), "footings_computed": len(f),
            "footings_total": len(out["footings"]["rows"]),
            "straps_m3": round(sum(r["volume_m3"] for r in s), 6), "straps_measured": len(s),
            "straps_total": len(out["straps"]["rows"]), "deterministic_total_m3": tot,
            "blocked": {"columns": "HEIGHT", "beams": "CLEAR LENGTH (simple: binding; continuous: support faces)",
                        "slabs": "OUTLINE", "ground_beams": "LEVEL AND EXTENT", "stairs": "RISERS",
                        "footings": [r["mark_key"] for r in out["footings"]["rows"] if r["status"] != SQ.COMPLETE],
                        "straps": [r["mark_key"] for r in out["straps"]["rows"] if r["status"] != SQ.COMPLETE]}}


def _h_audit(out) -> dict:
    bad = [r["mark_key"] for r in out["footings"]["rows"] if r.get("dims") and r["schedule_row"]
           and abs(r["dims"]["H"]["m"] - r["schedule_row"]["H_cm"] / 100.0) > 1e-9]
    F = out["footings"]["library"].get("F", {})
    return {"state": "PASS" if not bad and F.get("H_cm") == 30 else "FAIL", "rows_with_non_schedule_H": bad,
            "F_schedule_H_cm": F.get("H_cm"), "rule": "every footing H is the schedule H of its type; no 0.60 m exists"}


# ------------------------------------------------------------------ architecture
def _architecture(ctx, work) -> dict:
    a2 = ctx["a2"]
    out = {}
    # salon sea-view opening: the owner-stated width must match EXACTLY one GF source opening and one printed dim
    A = _blob(ctx, work, "P7757.dxf")
    gb = ctx["sheets_by_floor"]["GF"]["bounds"]
    umm = a2["units"]["ARCHITECTURAL"]["native_to_mm"] or 1.0
    dims = [d for d in A["dims"] if all(AP.in_box(*p, gb) for p in d.placed_points)]
    owner_w = 6330.0
    wins = [w for w in a2["floors"]["GF"]["windows"] if abs(w["width_mm"] - owner_w) <= SALON_WIDTH_TOL_MM]
    pd = [d for d in dims if abs(math.hypot(d.placed_points[0][0] - d.placed_points[1][0],
                                            d.placed_points[0][1] - d.placed_points[1][1]) * umm - owner_w) <= SALON_WIDTH_TOL_MM]
    ok = len(wins) == 1 and len(pd) == 1
    w = wins[0] if wins else None
    h = OWNER_FACTS[1]["fact"]["finished_aluminium_height_m"]
    out["salon_glazing"] = {
        "owner_facts": ["OF-A3-SALON-MATERIAL", "OF-A3-SALON-HEIGHT"], "binding": "UNIQUE_WIDTH_MATCH" if ok else "NOT_UNIQUE",
        "window": w and w["window"], "cad_gap_width_mm": w and w["width_mm"],
        "printed_dimension": pd[0].identity.source_handle if pd else None,
        "printed_value_cm": round(pd[0].measurement, 3) if pd else None,
        "width_m": 6.33 if ok else None, "width_authority": "SOURCE (printed dimension 633 + glazing gap in CAD)",
        "height_m": h, "height_authority": "PROJECT_OWNER_DERIVED_DIMENSION (OF-A3-SALON-HEIGHT) - not source-measured",
        "material": "ALUMINIUM_GLASS (OWNER_FACT)", "area_m2": round(6.33 * h, 6) if ok else None,
        "area_formula": "6.33 x 3.65", "status": SQ.COMPLETE if ok else SQ.BLOCKED, "class": "TRADE_ASSIGNMENT",
        "source_height_found": None, "precedence": OWNER_FACTS[1]["precedence"]}
    # curved glazing per floor (entity_role_inference CURVED_GLAZING)
    raw = ctx["a2_raw"]
    cg = []
    for fl in FLOORS:
        sites = raw[fl]["res"].get("sites") or []
        for i, g in enumerate(raw[fl]["eri"]["curved_glazing"]["windows"]):
            host = sorted({s["site_id"] for s in sites if set(s.get("boundary_source_ids", [])) & set(g["parts"])
                           and s["kind"] == "LABELLED_SITE"})
            labels = sorted({" / ".join(A2._label_values(s)[0]) for s in sites if s["site_id"] in host})
            cg.append(dict(g, floor=fl, id=f"{fl}-CG{i + 1:02d}", host_sites=host, host_labels=labels,
                           height="BLOCKED_HEIGHT (no head / sill printed; the salon owner height is not transferred)",
                           area_m2=None))
    gf = [g for g in cg if g["floor"] == "GF"]
    mb = OWNER_FACTS[3]
    out["curved_glazing"] = {"items": cg, "master_bedroom": {
        "owner_fact": mb["id"], "binding": "UNIQUE_CURVED_GLAZING_ON_GF" if len(gf) == 1 else "NOT_UNIQUE",
        "item": gf[0]["id"] if len(gf) == 1 else None,
        "developed_length_m": round(gf[0]["developed_length_mm"] / 1000.0, 6) if len(gf) == 1 else None,
        "length_range_m": [round(v / 1000.0, 6) for v in gf[0]["developed_length_range_mm"]] if len(gf) == 1 else None,
        "material": "ALUMINIUM_GLAZING (OWNER_FACT)", "form": "CURVED (source: concentric arcs)",
        "height_m": None, "area_m2": None, "status_length": SQ.COMPLETE if len(gf) == 1 else SQ.BLOCKED,
        "status_area": "BLOCKED_HEIGHT"}}
    # reception double-height zone: GF RECEPTION + 1F VOID at the same plan position (sheets share one frame size)
    out["double_height"] = _double_height(ctx, A)
    out["joinery"] = {fl: raw[fl]["eri"]["counter_runs"] for fl in FLOORS}
    out["wall_end_caps"] = {fl: len(raw[fl]["eri"]["wall_end_caps"]["parts"]) for fl in FLOORS}
    out["door_frames"] = {fl: len(raw[fl]["eri"]["door_frames"]["parts"]) for fl in FLOORS}
    out["physical_sites"] = _physical_sites(ctx)
    return out


ROOM_LIKE = {"min_area_m2": 1.0, "min_effective_width_m": 0.6}


def _physical_sites(ctx) -> dict:
    """Certified sites WITHOUT a readable label are published as PHYSICAL_SITE when they are room-like (area >= 1 m2
    and effective width 2A/P >= 0.6 m); the rest (wall cavities, glazing slivers) are counted, never published."""
    u = ctx["a2"]["units"]["ARCHITECTURAL"]["native_to_mm"] or 1.0
    out = {}
    for fl in FLOORS:
        sites = ctx["a2_raw"][fl]["res"].get("sites") or []
        pub, cav = [], Counter()
        for s in sorted(sites, key=lambda z: z["site_id"]):
            if s["kind"] != "UNLABELLED_SITE" or s["status"] != "CERTIFIED":
                continue
            P = s["perimeter"] * u / 1000.0
            w = 2 * s["area_m2"] / P if P else 0.0
            if s["area_m2"] >= ROOM_LIKE["min_area_m2"] and w >= ROOM_LIKE["min_effective_width_m"]:
                pub.append({"floor": fl, "site": s["site_id"], "semantic": "UNKNOWN", "floor_area_m2": round(s["area_m2"], 6),
                            "base_ceiling_area_m2": round(s["area_m2"], 6), "perimeter_m": round(P, 6),
                            "effective_width_m": round(w, 3), "status": "COMPUTED_SHADOW_COMPLETE"})
            else:
                cav["THIN_OR_SMALL (wall cavity / glazing sliver / reveal)"] += 1
        out[fl] = {"published": pub, "not_room_like": dict(cav)}
    return {"rule": dict(ROOM_LIKE), "floors": out}


def _double_height(ctx, A) -> dict:
    gb, fb = ctx["sheets_by_floor"]["GF"]["bounds"], ctx["sheets_by_floor"]["1F"]["bounds"]
    dx, dy = fb[0] - gb[0], fb[1] - gb[1]
    rec = [t for t in A["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, gb)
           and t.value.strip().upper() == "RECEPTION"]
    voids = [t for t in A["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, fb)
             and t.value.strip().upper() == "VOID"]
    from engine.source import topology as T
    r1 = ctx["a2_raw"]["1F"]["res"]
    sites1, arr = r1.get("sites") or [], r1.get("_arr")
    by = {s["site_id"]: s for s in sites1}
    out = []
    for r in rec:
        x1, y1 = r.x + dx, r.y + dy
        hit = []
        here = T.locate(arr, sites1, (x1, y1), 1.0)[0] if arr is not None else None
        for v in voids:
            sid = T.locate(arr, sites1, (v.x, v.y), 1.0)[0] if arr is not None else None
            s = by.get(sid)
            hit.append({"void_text": v.identity.key, "site": sid, "reception_above_inside": sid is not None and sid == here,
                        "site_status": s and s["status"], "site_area_m2": s and round(s["area_m2"], 6),
                        "site_labels": s and sorted({t.get("value") for t in s.get("label_texts", []) if t.get("value")})})
        good = [h for h in hit if h["reception_above_inside"]]
        out.append({"reception_text": r.identity.key, "projected_to_1F": [round(x1, 3), round(y1, 3)], "voids": hit,
                    "state": "DOUBLE_HEIGHT_ZONE_CORROBORATED" if good else "OWNER_FACT_ONLY",
                    "owner_fact": "OF-A3-RECEPTION-DOUBLE-HEIGHT",
                    "horizontal_extent_m2": good[0]["site_area_m2"] if good and good[0]["site_status"] == "CERTIFIED" else None,
                    "vertical_extent": {"from_ffl_m": 1.00, "to_ffl_m": 9.70, "storeys": "GF + 1F",
                                        "source": "section levels VE-AA-04 / VE-AA-06 (A2 transcription)"},
                    "ceiling_condition": "NOT_IN_SOURCE", "wall_heights": "BLOCKED (no single-storey assumption)"})
    return {"zones": out, "plan_offset_native": [round(dx, 3), round(dy, 3)],
            "rule": "the GF label position carried to 1F by the sheet-frame offset must fall inside a 1F site labelled "
                    "VOID; then the owner fact is corroborated by the plan"}


def main(work, regdir, commit=None):
    import alsenan_a3_registers as REGS
    ctx = build(work, commit)
    regs = REGS.registers(ctx)
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    fz = regs[REGS.FREEZE]
    print(json.dumps({"firewall": regs["BENCHMARK_FIREWALL"]["audit_verdict"]["state"],
                      "freeze_schema": fz["schema_validation"]["state"], "counts": fz["counts"],
                      "xlsx": regs["QA_RECONCILIATION"]["xlsx"]["readback"]["state"]}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
