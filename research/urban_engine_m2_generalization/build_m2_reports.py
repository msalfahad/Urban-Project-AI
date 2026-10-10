"""M2 REPORTS - the Alsenan generic-route run compared with the frozen replay, the reinforcement completeness of M1's
89 bar-less components, the ground-slab gap audit, and the accuracy / coverage metrics of the synthetic evaluation.

    python3 -I research/urban_engine_m2_generalization/build_m2_reports.py [--drawing ST.dxf]

Nothing here changes a frozen stage or the generic engine: the generic route runs as committed (route G, the
generic convention set plus profile_st7757.json, printed storey heights and the p.13 ground-beam classes only),
then its output is set beside the frozen M1 replay (research/alsenan_m1_usable_boq/boq) and the S8.1 face register.
Outputs carry ids, classes and quantities only; no source text from the drawing is written.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import generic_route as GR            # noqa: E402
from engine.source import member_detection as MD         # noqa: E402
from tools import urban_intake as UI                     # noqa: E402

DRAWING = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
M1 = ROOT / "research/alsenan_m1_usable_boq/boq"
S9_BARS = ROOT / "research/alsenan_structural_s9/03_REINFORCEMENT_BOQ_RECONCILIATION.csv"
OCC = ROOT / "research/pre_s6_superstructure_beam_readiness/01_BEAM_OCCURRENCE_CONSERVATION.csv"
S81 = ROOT / "research/alsenan_ground_slab_s8_1/01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv"
GENERIC = ROOT / "engine/profiles/URBAN_M2_GENERIC_CONVENTIONS_V1.json"
PROFILE = PKG / "profile_st7757.json"
EVAL = PKG / "evaluation"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
SHEET_OF = {"GF_ROOF": "SH06", "GFRS": "SH06", "1F_ROOF": "SH04", "FFRS": "SH04", "2F_ROOF": "SH02", "SFRS": "SH02",
            "GBP": "SH08"}
GENERIC_SCOPE = ("FOOTINGS", "COLUMNS", "BEAMS", "GROUND_BEAMS", "SLABS", "GROUND_SLAB")


def _rows(p):
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _csv(rows, fields=None):
    fields = fields or (list(rows[0].keys()) if rows else [])
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (round(r[k], 6) if isinstance(r[k], float) else r[k]))
                    for k in fields})
    return b.getvalue()


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def run_generic(drawing):
    I = UI.read(drawing)
    D = GR.detect(I)
    conv = GR.merge_conventions(json.loads(GENERIC.read_text()), json.loads(PROFILE.read_text()))
    items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv))
    return I, D, conv, items, reg, risk


# ------------------------------------------------------------------ 1 family comparison
def family_rows(items):
    from engine.source import provisional_estimate as PE
    return {(r["trade"], r["family"]): r for r in PE.rollup(items, ("trade", "family"))}


def classify(fam, trade, a, g, D, risk):
    """discrepancy class from the evidence (never from the size of the difference)."""
    rk = Counter(r["KIND"] for r in risk)
    if fam not in GENERIC_SCOPE:
        return "NOT_IN_GENERIC_SCOPE", "the generic engine has no detector for this family yet"
    if trade == "REINFORCEMENT" and fam == "GROUND_BEAMS":
        return "GENERIC_MISSING_DATA", "typical ground-beam bars are in the PDF detail only (vector glyphs, no OCR)"
    if fam == "FOOTINGS":
        return "DETECTION_GAP", f"{rk.get('FOOTING_NO_OUTLINE', 0)} footing marks without an outline carry no " \
                                f"quantity (no exposure from the schedule size yet)"
    if fam == "COLUMNS" and trade == "CONCRETE":
        return "DETECTION_GAP", "column occurrences without a schedule type stay unresolved; necks need a founding " \
                                "level the drawing does not print"
    if fam == "GROUND_BEAMS":
        return "CONVENTION_DIFFERENCE", "generic route applies the p.13 class depths to every band; the frozen " \
                                        "replay separates exterior depths and straps"
    if fam == "GROUND_SLAB":
        return "SCOPE_DIFFERENCE", "see 06_GROUND_SLAB_GAP_AUDIT.csv: same 19 faces, plus generic-only faces"
    if trade == "REINFORCEMENT":
        return "BAR_MODEL_DIFFERENCE", "generic bar models (schedule bars, ACI hooks, anchorage / lap conventions) " \
                                       "versus the frozen stage BBS"
    d = (_f(g.get("PLANNING_BASE")) - _f(a.get("PLANNING_BASE")))
    base = _f(a.get("PLANNING_BASE"))
    if base and abs(d) / base <= 0.05:
        return "SAME_OBJECTS_CLOSE_RESULT", "within 5 % of the frozen replay"
    return "CONVENTION_DIFFERENCE", "same members, different section / thickness readings"


def comparison(items, D, risk):
    A = {(r["trade"], r["family"]): r for r in _rows(M1 / "FAMILY_SUMMARY.csv")}
    G = family_rows(items)
    out = []
    for k in sorted(set(A) | set(G)):
        a, g = A.get(k, {}), G.get(k, {})
        cls, why = classify(k[1], k[0], a, g, D, risk)
        pa, pg = _f(a.get("PLANNING_BASE")), _f(g.get("PLANNING_BASE"))
        out.append({"TRADE": k[0], "FAMILY": k[1], "UNIT": "m3" if k[0] == "CONCRETE" else "kg",
                    "FROZEN_REPLAY_VERIFIED": _f(a.get("VERIFIED")), "FROZEN_REPLAY_PLANNING_BASE": pa,
                    "FROZEN_REPLAY_N_UNRESOLVED": a.get("N_UNRESOLVED", ""),
                    "GENERIC_PROVISIONAL_LOW": _f(g.get("PROVISIONAL_LOW")),
                    "GENERIC_PROVISIONAL_BASE": pg, "GENERIC_PROVISIONAL_HIGH": _f(g.get("PROVISIONAL_HIGH")),
                    "GENERIC_N_UNRESOLVED": g.get("N_UNRESOLVED", ""),
                    "GENERIC_MINUS_FROZEN": pg - pa, "RATIO_GENERIC_TO_FROZEN": (pg / pa) if pa else None,
                    "DISCREPANCY_CLASS": cls, "WHY": why})
    return out


# ------------------------------------------------------------------ 2 reinforcement completeness (89)
def m1_barless():
    bars = {b["COMPONENT_ID"] for b in _rows(S9_BARS)}
    pref = {re.split(r"[#:]", b)[0] for b in bars}
    out = []
    for cat in ("PROVISIONAL", "UNRESOLVED"):
        for r in _rows(M1 / f"{cat}_REGISTER.csv"):
            if r["TRADE"] != "CONCRETE" or r["FAMILY"] not in ("BEAMS", "GROUND_BEAMS", "LIFT"):
                continue
            cid = r["COMPONENT_ID"]
            if cid in bars or re.split(r"[#:]", cid)[0] in pref or cid.startswith("BEAM-CORNER"):
                continue
            out.append(dict(r, M1_CATEGORY=cat))
    return out


def reinforcement_completeness(D, reg):
    occ = _rows(OCC)
    tag_of_span = {}
    for o in occ:
        if o["OBJECT_KIND"] == "MEMBER_SPAN":
            tag_of_span[o["OBJECT_ID"]] = (json.loads(o["BOUND_TAGS"] or "[]"), _f(o["CLEAR_M"]))
    cb_tags = defaultdict(list)                                  # (sheet, mark, line) -> tag handles
    for o in occ:
        if o["OBJECT_KIND"] == "TAG" and o["BOUND_GEOMETRY"].startswith("SPAN:"):
            _, sh, line, _ = o["BOUND_GEOMETRY"].split(":", 3)
            cb_tags[(sh, o["MARK"], line)].append(o["OBJECT_ID"].split(":")[-1])
    state_of = {r["COMPONENT_ID"]: r for r in reg}
    marks_by_hex = {}
    for sid, rec in D["sheets"].items():
        for m in rec.get("marks", []):
            hx = str(m.get("text_id", "")).split(":")[-1].upper()
            marks_by_hex[(sid, hx)] = m
    bands = {(sid, b["band_id"]): b for sid, rec in D["sheets"].items() for b in rec.get("beams", [])}
    inherited = defaultdict(list)
    for sid, rec in D["sheets"].items():
        for x in rec.get("inherited", []):
            inherited[(sid, x.get("from_band"))].append(x["band"])

    def g_state(sid, band_id, fam, storey):
        cid = f"{fam}:{storey}:{band_id}"
        r = state_of.get(cid)
        return (cid, r["REBAR_STATE"], r["REASON"], r["PROVISIONAL_KG_BASE"]) if r else (cid, "NOT_IN_REGISTER", "",
                                                                                          None)
    out = []
    for r in m1_barless():
        cid, fam = r["COMPONENT_ID"], r["FAMILY"]
        rec = {"M1_COMPONENT_ID": cid, "FAMILY": fam, "STOREY": r["STOREY"], "M1_CATEGORY": r["M1_CATEGORY"],
               "M1_CONCRETE_M3_BASE": _f(r["BASE"]), "M1_BAR_ROW": "NONE (PF-M1-03)"}
        method, gid, state, reason, kg = "NOT_MATCHED", "", "", "", None
        m = re.match(r"BM-([0-9A-Z_]+)-[A-Z]+\d*[A-Z]?-B[LA]\d+-([0-9A-F]+)", cid)
        if fam == "LIFT":
            method, state, reason = "NOT_IN_GENERIC_SCOPE", "OUTSIDE_SCOPE", "no generic lift detector"
        elif m and SHEET_OF.get(m.group(1)):
            sid = SHEET_OF[m.group(1)]
            mk = marks_by_hex.get((sid, m.group(2)))
            if mk and mk.get("band"):
                bid = mk["band"]
                method = "TAG_HANDLE"
                gid, state, reason, kg = g_state(sid, bid, "BEAMS", r["STOREY"])
            else:
                method, state = "TAG_HANDLE", "TAG_NOT_BOUND_BY_GENERIC" if mk else "TAG_NOT_FOUND"
        elif cid.startswith("CBO-"):
            mm = re.match(r"CBO-([A-Z]+)-([A-Z]+\d+)-(BL\d+)#SPAN(\d+)", cid)
            if mm:
                sid = SHEET_OF.get(mm.group(1))
                hx = cb_tags.get((mm.group(1), mm.group(2), mm.group(3)), [])
                mk = next((marks_by_hex.get((sid, h.upper())) for h in hx if marks_by_hex.get((sid, h.upper()))),
                          None)
                method = "CB_TAG_ON_LINE"
                if mk and mk.get("band"):
                    gid, state, reason, kg = g_state(sid, mk["band"], "BEAMS", r["STOREY"])
                else:
                    state = "TAG_NOT_BOUND_BY_GENERIC" if mk else "TAG_NOT_FOUND"
        elif cid.startswith("SPAN:"):
            _, sh, line, rng = cid.split(":", 3)
            sid = SHEET_OF.get(sh)
            clear = tag_of_span.get(cid, ([], 0.0))[1]
            neigh = [o for o in tag_of_span if o.startswith(f"SPAN:{sh}:{line}:") and tag_of_span[o][0]]
            method = "LINE_NEIGHBOUR_LENGTH"
            cands = []
            for o in neigh:
                for h in tag_of_span[o][0]:
                    mk = marks_by_hex.get((sid, h.upper()))
                    if mk and mk.get("band"):
                        for b2 in inherited.get((sid, mk["band"]), []):
                            b = bands.get((sid, b2))
                            if b and abs(b.get("length_m", 0) - clear) <= 0.05:
                                cands.append(b2)
            if len(set(cands)) == 1:
                gid, state, reason, kg = g_state(sid, cands[0], "BEAMS", r["STOREY"])
            else:
                # fallback: the span's stations (sheet-local mm along the line) against every generic band on the
                # sheet whose extent along x or y spans the same interval and whose length is the clear span
                a0, a1 = (float(v) for v in rng.split("-"))
                ox, oy = D["sheets"][sid]["sheet"]["origin"]
                hits = []
                for (s2, bid), b in bands.items():
                    if s2 != sid or b.get("kind") != "STRAIGHT":
                        continue
                    xs = [p[0] - ox for p in b["polygon"]]
                    ys = [p[1] - oy for p in b["polygon"]]
                    for lo, hi in ((min(xs), max(xs)), (min(ys), max(ys))):
                        if lo >= a0 - 400 and hi <= a1 + 400 and abs(b.get("length_m", 0) - clear) <= 0.10:
                            hits.append(bid)
                if len(set(hits)) == 1:
                    method = "LINE_STATIONS_LENGTH"
                    gid, state, reason, kg = g_state(sid, hits[0], "BEAMS", r["STOREY"])
                else:
                    state = ("NO_UNIQUE_GENERIC_BAND" if (cands or hits) else "NO_GENERIC_BAND_AT_STATIONS")
        elif fam == "GROUND_BEAMS":
            hx = re.findall(r"(?<=-)([0-9A-F]{3,4})(?=-|$)", cid)
            decs = {f"D2:{int(h, 16)}" for h in hx}
            hit = [b for (sid, _), b in bands.items() if sid == "SH08" and
                   decs & {m_.group(0) for h in b["handles"] for m_ in [re.match(r"D2:\d+", str(h))] if m_}]
            method = "FACE_HANDLES"
            if hit:
                b = hit[0]
                gid, state, reason, kg = g_state("SH08", b["band_id"], "GROUND_BEAMS", "GROUND")
            else:
                state = "NO_GENERIC_BAND" if hx else "NO_GEOMETRY_IN_ID"
        rec.update(MATCH_METHOD=method, GENERIC_COMPONENT_ID=gid, GENERIC_REBAR_STATE=state,
                   GENERIC_REASON=reason, GENERIC_PROVISIONAL_KG=kg)
        out.append(rec)
    return out


# ------------------------------------------------------------------ 3 ground-slab gap audit
def ground_slab_audit(D):
    rec = next(r for r in D["sheets"].values() if r["sheet"]["role"] == "GROUND_BEAM_PLAN")
    faces = rec["slab"]["faces"]
    ox, oy = rec["sheet"]["origin"]
    rows, used = [], set()
    for s in _rows(S81):
        if not s["POLYGON_MM"]:
            continue
        poly = [(x + ox, y + oy) for x, y in json.loads(s["POLYGON_MM"])]
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        c = (sum(xs) / len(xs), sum(ys) / len(ys))
        if not MD.point_in_poly(c[0], c[1], poly):
            c = next(((x, y) for x in [min(xs) + (max(xs) - min(xs)) * t / 24 for t in range(1, 24)]
                      for y in [min(ys) + (max(ys) - min(ys)) * t / 24 for t in range(1, 24)]
                      if MD.point_in_poly(x, y, poly)), c)
        hit = [k for k, f in enumerate(faces) if MD.point_in_poly(c[0], c[1], f["polygon"])]
        used.update(hit)
        f = faces[hit[0]] if hit else None
        s1 = s["S1_CLASS"]
        m1_slab = s["ROW_KIND"] == "FACE"
        if f is None:
            near = [x for x in rec["slab"]["unenclosed_sides"] if abs(x["side_mid"][0] - c[0]) < 3000 and
                    abs(x["side_mid"][1] - c[1]) < 3000]
            cls = ("GENERIC_NO_FACE_REPORTED" if near else "GENERIC_NO_FACE_SILENT") if m1_slab else \
                "BOTH_NOT_SLAB"
        elif f["class"] == "PANEL":
            cls = "MATCHED_SLAB" if m1_slab else "GENERIC_COUNTS_EXCLUDED_ZONE"
        else:
            cls = f"GENERIC_CLASS_{f['class']}" if m1_slab else "BOTH_NOT_SLAB"
        rows.append({"S8_1_ROW": s["ROW_ID"], "S8_1_KIND": s["ROW_KIND"], "S8_1_CLASS": s1,
                     "S8_1_AREA_M2": _f(s["AREA_M2_EXACT"] or s["AREA_M2_S1"]),
                     "M1_COUNTS_AS_GROUND_SLAB": m1_slab,
                     "GENERIC_FACE": f["face_id"] if f else "", "GENERIC_CLASS": f["class"] if f else "NONE",
                     "GENERIC_AREA_M2": f["area_m2"] if f else None,
                     "AREA_DIFF_M2": (f["area_m2"] - _f(s["AREA_M2_EXACT"] or s["AREA_M2_S1"])) if f else None,
                     "AUDIT_CLASS": cls})
    for k, f in enumerate(faces):
        if k in used or f["class"] not in ("PANEL", "OPEN_BOUNDARY"):
            continue
        inner = [c for c in rec.get("column_boxes", []) if MD.point_in_poly((c[0] + c[2]) / 2, (c[1] + c[3]) / 2,
                                                                             f["polygon"])]
        rows.append({"S8_1_ROW": "", "S8_1_KIND": "NO_S8_1_FACE", "S8_1_CLASS": "", "S8_1_AREA_M2": None,
                     "M1_COUNTS_AS_GROUND_SLAB": False, "GENERIC_FACE": f["face_id"], "GENERIC_CLASS": f["class"],
                     "GENERIC_AREA_M2": f["area_m2"], "AREA_DIFF_M2": f["area_m2"],
                     "AUDIT_CLASS": "GENERIC_ONLY_FACE" + ("_WITH_COLUMNS_INSIDE" if inner else ""),
                     "COLUMNS_INSIDE": len(inner)})
    return rows


# ------------------------------------------------------------------ 4 metrics
def metrics():
    out = {}
    for p in sorted(EVAL.glob("*.json")):
        d = json.loads(p.read_text())
        s = d["summary"]
        out[p.stem] = {"drawings": s["drawings"], "end_to_end_success": s["end_to_end_success"],
                       "max_abs_error": s["max_abs_error"], "mean_abs_error": s["mean_abs_error"],
                       "within_5pct": s["within_5pct"],
                       "detect": {k: s[k] for k in ("detect_footings", "detect_beams", "detect_panels")},
                       "slab_area": s.get("slab_area"),
                       "slab_loss_unreported_drawings": s.get("slab_loss_unreported_drawings"),
                       "mean_seconds": s["mean_seconds"], "defects": d.get("defects", False)}
    return out


def main(argv):
    drawing = Path(argv[argv.index("--drawing") + 1]) if "--drawing" in argv else DRAWING
    I, D, conv, items, reg, risk = run_generic(drawing)
    comp = comparison(items, D, risk)
    rc = reinforcement_completeness(D, reg)
    gs = ground_slab_audit(D)
    rc_sum = {"components": len(rc),
              "by_generic_state": dict(Counter(r["GENERIC_REBAR_STATE"] for r in rc)),
              "by_family_and_state": {f"{k[0]}|{k[1]}": v for k, v in
                                      sorted(Counter((r["FAMILY"], r["GENERIC_REBAR_STATE"]) for r in rc).items())},
              "generic_bar_model_kg": round(sum(_f(r["GENERIC_PROVISIONAL_KG"]) for r in rc), 3)}
    gs_sum = {"rows": len(gs), "by_class": dict(Counter(r["AUDIT_CLASS"] for r in gs)),
              "m1_ground_slab_area_m2": round(sum(r["S8_1_AREA_M2"] or 0 for r in gs if r["M1_COUNTS_AS_GROUND_SLAB"]),
                                              3),
              "generic_panel_area_m2": round(sum(r["GENERIC_AREA_M2"] or 0 for r in gs if r["GENERIC_CLASS"] ==
                                                 "PANEL"), 3)}
    files = {
        "04_ALSENAN_GENERIC_VS_FROZEN.csv": _csv(comp),
        "05_REINFORCEMENT_COMPLETENESS_89.csv": _csv(rc),
        "06_GROUND_SLAB_GAP_AUDIT.csv": _csv(gs, ["S8_1_ROW", "S8_1_KIND", "S8_1_CLASS", "S8_1_AREA_M2",
                                                  "M1_COUNTS_AS_GROUND_SLAB", "GENERIC_FACE", "GENERIC_CLASS",
                                                  "GENERIC_AREA_M2", "AREA_DIFF_M2", "AUDIT_CLASS",
                                                  "COLUMNS_INSIDE"]),
        "07_ALSENAN_COVERAGE_RISK.csv": _csv([{"KIND": r["KIND"], "WHERE": r["WHERE"]} for r in risk]),
        "08_ACCURACY_COVERAGE_METRICS.json": json.dumps({
            "synthetic_evaluation": metrics(),
            "alsenan_generic": {"items": len(items), "coverage_risk_by_kind": dict(Counter(r["KIND"] for r in risk)),
                                "rebar_register_by_state": dict(Counter(r["REBAR_STATE"] for r in reg)),
                                "sheets": [{k: s[k] for k in ("sheet_id", "role", "storey")} for s in
                                           D["model"]["sheets"]],
                                "reinforcement_completeness_89": rc_sum, "ground_slab_audit": gs_sum}},
            indent=1, ensure_ascii=True, default=str),
    }
    for name, text in files.items():
        bad = HYGIENE.findall(text)
        if bad:
            raise SystemExit(f"hygiene: {name} carries forbidden text ({len(bad)} matches)")
        (PKG / name).write_text(text, encoding="utf-8")
    print(json.dumps({"written": sorted(files), "reinforcement_89": rc_sum, "ground_slab": gs_sum}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
