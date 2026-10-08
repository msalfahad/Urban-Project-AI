"""URBAN PROJECTS D1.1 - stirrup / link core-path lower-bound audit (authority correction, no redesign).

    python3 -I research/d1_1_stirrup_authority_audit/build_d1_1_stirrup_audit.py

D1 released link mass from a sharp-corner rectangular centreline path, 2(b-2c-d) + 2(h-2c-d), on the premise that
the closing hooks add back what the rounded bends take away. This audit:
  1. exhausts the issued set for bend radius, bend diameter, hook angle / length / extension, closure / lap and any
     link-fabrication note:
       - every DXF text, attribute, dimension and block, legacy Arabic decoded;
       - the p.8 general notes (S1 transcription) and the project rule register;
       - the PDF detail sheets pp.9-16 (vector text layers, OCR search aid);
       - the drawn link geometry itself;
  2. classifies the sharp path: a bent closed loop is shorter than its sharp polygon by (8 - 2 pi) R, so without a
     project-source R (or an upper bound on R) and an exact envelope it is a MODELLED_POLYGONAL_EQUIVALENT, not a
     lower bound;
  3. writes explicit CORRECTION_ERRATA records (engine.source.delta_correction) over S6.1 and S5.1. S6.1 / S5.1
     stay frozen and are never edited. Every non-link release is kept and its independence from bend geometry stated;
  4. keeps link topology, count and diameter separate from the (blocked) cut length.
Blind: issued drawing + frozen Urban registers only. No design code, external example, donor or other engine is
read. Deterministic.
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
for p in (ROOT, ROOT / "research/source_recovery_delta"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import ezdxf  # noqa: E402

import vector_pdf as V  # noqa: E402
from engine.source import delta_correction as DC  # noqa: E402
from engine.source import delta_release as DR  # noqa: E402
from engine.source import legacy_text as LT  # noqa: E402

ROUND = "D1.1"
POLICY = "STIRRUP_AUTHORITY_AUDIT_V1"
R = ROOT / "research"
S4, S5, S6 = R / "alsenan_footing_rebar_s4", R / "alsenan_ground_system_rebar_s5", R / "alsenan_superstructure_beam_rebar_s6"
S41, S51, S61 = (R / "alsenan_footing_rebar_s4_1", R / "alsenan_ground_system_rebar_s5_1",
                 R / "alsenan_superstructure_beam_rebar_s6_1")
SRD = R / "source_recovery_delta"
S1 = R / "alsenan_structural_census_s1"
R4 = R / "alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json"
OCR = HERE / "source_search_inputs/PDF_TEXT_OCR_PP9_16.json"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
DXF = ROOT / "data/inputs/by_sha256" / f"{DXF_SHA}.dxf"
PDF = ROOT / "data/inputs/by_sha256" / f"{PDF_SHA}.pdf"
MANIFESTS = {"S4": S4 / "S4_FREEZE_MANIFEST.json", "S5": S5 / "S5_FREEZE_MANIFEST.json",
             "S6": S6 / "S6_FREEZE_MANIFEST.json", "S4.1": S41 / "S4_1_FREEZE_MANIFEST.json",
             "S6.1": S61 / "S6_1_FREEZE_MANIFEST.json", "S5.1": S51 / "S5_1_FREEZE_MANIFEST.json"}
CODE = ["engine/source/delta_correction.py", "engine/source/delta_release.py", "engine/source/legacy_text.py",
        "research/source_recovery_delta/vector_pdf.py",
        "research/d1_1_stirrup_authority_audit/build_d1_1_stirrup_audit.py"]
INPUTS = [str(p.relative_to(ROOT)) for p in MANIFESTS.values()] + [
    "research/alsenan_structural_census_s1/STRUCTURAL_PROJECT_RULE_REGISTER.json",
    "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json",
    "research/source_recovery_delta/13_GRAPHIC_EVIDENCE.json",
    "research/d1_1_stirrup_authority_audit/source_search_inputs/PDF_TEXT_OCR_PP9_16.json"]
OUTPUTS = ["00_README.md", "01_SOURCE_SEARCH.md", "02_STIRRUP_PATH_AUDIT.csv", "03_S6_1A_CORRECTIONS.csv",
           "04_S5_1A_CORRECTIONS.csv", "05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv", "06_CORRECTED_RELEASE_SUMMARY.json",
           "07_PROVENANCE.jsonl"]
EN_TERMS = ("BEND", "BENT", "RADIUS", "RAD.", "MANDREL", "FORMER", "HOOK", "135", "LAP", "SPLICE", "OVERLAP",
            "CLOSURE", "ANCHOR", "DEVELOP", "EXTENSION", "CRANK", "SHAPE", "CUT", "LINK", "TIE", "STIRR", "XD", "XDIA",
            "X DIA", "R=")
AR_TERMS = ("ثني", "تثني", "خطاف", "كانة", "كانات", "رباط", "وصلة", "وصلات", "تراكب", "نصف قطر", "تكسيح")
LINK_PORTIONS = ("CORE_PATH",)


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"D1.1 check failed: {what}")


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


# ------------------------------------------------------------------ 1. source search
def dxf_sweep():
    check(_sha(DXF) == DXF_SHA, "ST7757.dxf sha256")
    doc = ezdxf.readfile(str(DXF))
    styles = {s.dxf.name.upper(): (s.dxf.font or "") for s in doc.styles}
    texts, dimtypes = [], Counter()

    def take(e, where):
        t = e.dxftype()
        if t == "DIMENSION":
            dimtypes[e.dimtype & 0x0F] += 1
            s = e.dxf.get("text", "") or ""
        elif t in ("TEXT", "ATTRIB", "ATTDEF"):
            s = e.dxf.text
        elif t == "MTEXT":
            s = e.plain_text()
        else:
            return
        fam = None
        if t != "DIMENSION":
            fam = LT.font_family(styles.get(str(e.dxf.get("style", "STANDARD")).upper(), ""))
        dec = LT.decode(s, fam)["text"] if fam else None
        texts.append({"handle": e.dxf.handle, "type": t, "where": where, "raw": s or "", "decoded": dec})

    for lay in doc.layouts:
        for e in lay:
            take(e, "layout:" + lay.name)
            if e.dxftype() == "INSERT":
                for a in e.attribs:
                    take(a, "insert:" + e.dxf.name)
    for b in doc.blocks:
        if b.name.startswith(("*Model", "*Paper")):
            continue
        for e in b:
            take(e, "block:" + b.name)
    hits = defaultdict(set)
    for t in texts:
        up = t["raw"].upper()
        for k in EN_TERMS:
            if k in up:
                hits[k].add(t["raw"].strip())
        if t["decoded"]:
            for k in AR_TERMS:
                if k in t["decoded"]:
                    hits["AR:" + k].add(t["decoded"].strip())
    # drawn reinforcement arcs (undimensioned; reported for QA only - P8-N03 forbids scaling)
    radii = Counter()
    for e in doc.modelspace().query('LWPOLYLINE[layer=="S-REIN.D"]'):
        pts = e.get_points("xyb")
        n = len(pts)
        for i in range(n if e.closed else n - 1):
            x0, y0, b = pts[i]
            x1, y1, _ = pts[(i + 1) % n]
            if abs(b) > 1e-9:
                chord = math.hypot(x1 - x0, y1 - y0)
                radii[round(float(chord / (2.0 * math.sin(2.0 * math.atan(abs(b))))), 1)] += 1
    for e in doc.modelspace().query('ARC[layer=="S-REIN.D"]'):
        radii[round(float(e.dxf.radius), 1)] += 1
    return {"texts_scanned": len(texts), "legacy_arabic_decoded": sum(1 for t in texts if t["decoded"]),
            "by_type": dict(sorted(Counter(t["type"] for t in texts).items())),
            "dimension_types": {str(k): v for k, v in sorted(dimtypes.items())},
            "radial_or_diameter_dimensions": dimtypes.get(3, 0) + dimtypes.get(4, 0),
            "term_hits": {k: sorted(v) for k, v in sorted(hits.items())},
            "drawn_rebar_arc_radii_units": {str(k): v for k, v in sorted(radii.items())}}


def drawn_link_corners():
    """Chord structure of the issued link sections (p.15 beam section, p.13 GB sections)."""
    check(_sha(PDF) == PDF_SHA, "ST7757.pdf sha256")
    ge = _j(SRD / "13_GRAPHIC_EVIDENCE.json")["evidence"]
    boxes = {"p15 TYP. SLAB ON BEAMS beam section": (15, ge["E-PDF-05"]["facts"]["bbox_pt"])}
    for name, v in ge["E-PDF-02"]["facts"].items():
        boxes["p13 " + name] = (13, v["bbox_pt"])
    cache, out = {}, {}
    for name, (pg, bb) in sorted(boxes.items()):
        if pg not in cache:
            cache[pg] = V.paths(str(PDF), pg)
        box = (bb[0] - 1, bb[1] - 1, bb[2] + 1, bb[3] + 1)
        comps = V.components(V.segments(cache[pg], box, {"S-REIN.D"}))
        link = max(comps, key=V.length)
        lengths = sorted(math.dist(s[2], s[3]) for s in link)
        long_sides = [x for x in lengths if x > 8.0]
        short = [x for x in lengths if x < 3.0]
        out[name] = {"page": pg, "segments": len(link), "straight_sides": len(long_sides),
                     "short_corner_chords": len(short), "chords_per_corner": len(short) / 4.0,
                     "corner_shape": "ROUNDED (chorded arcs)" if len(short) >= 8 else "SHARP_OR_UNCLEAR",
                     "radius_dimensioned": False}
    return out


def notes_and_rules():
    notes = _j(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"]
    words = ("hook", "bend", "bent", "radius", "mandrel", "lap", "splice", "closure", "stirrup", "link", "tie",
             "anchor", "develop")
    relevant = []
    for n in notes:
        txt = " ".join(str(n.get(k) or "") for k in ("english_interpretation", "normalized_rule")).lower()
        relevant.append({"rule_id": n["rule_id"], "page": n["page"], "hits": [w for w in words if w in txt],
                         "english": n["english_interpretation"]})
    p8 = [n for n in relevant if n["page"] == 8]
    r4 = {r["rule_id"]: r for r in _j(R4)["rules"]}
    hb = r4["HOOKS_AND_BENDS"]
    check(hb["source_state"] == "NO_PROJECT_SOURCE", "R4 hooks / bends have no project source")
    n03 = next(n for n in notes if n["rule_id"] == "P8-N03")
    n22 = next(n for n in notes if n["rule_id"] == "P8-N22")
    return {"p8_notes": len(p8), "p8_with_any_term": [n for n in p8 if n["hits"]],
            "all_notes_with_any_term": [n for n in relevant if n["hits"]],
            "do_not_scale": {"rule_id": n03["rule_id"], "english": n03["english_interpretation"]},
            "cover": {"rule_id": n22["rule_id"], "english": n22["english_interpretation"],
                      "r4_scope": [r4["COVER_GENERAL_25MM"]["scope"], r4["COVER_AGAINST_SOIL_70MM"]["scope"]]},
            "hooks_and_bends_rule": {"rule_id": "HOOKS_AND_BENDS", "source_state": hb["source_state"],
                                     "use": "never used for official kg"}}


def source_search():
    dx = dxf_sweep()
    corners = drawn_link_corners()
    nr = notes_and_rules()
    ocr = _j(OCR)
    check(ocr["pdf_sha256"] == PDF_SHA, "OCR record is from the issued PDF")
    ocr_terms = sorted({k for p in ocr["pages"].values() for k in p["hits"]})
    for bad in ("BEND", "BENT", "RADIU", "HOOK", "SPLIC", "MANDREL", "135", "OVERLAP"):
        check(bad not in ocr_terms, f"OCR: no '{bad}' anywhere on pp.9-16")
    for k in ("BEND", "BENT", "RADIUS", "MANDREL", "HOOK", "SPLICE", "135", "CLOSURE"):
        check(k not in dx["term_hits"], f"DXF: no '{k}' in any text")
    check(dx["radial_or_diameter_dimensions"] == 0, "no radial / diameter dimension in the DXF")
    check(all(v["corner_shape"].startswith("ROUNDED") for v in corners.values()), "issued links drawn with bends")
    findings = {
        "BEND_RADIUS": "SOURCE_EXPECTED_NOT_LOCATED - the issued sections draw the corners bent (chorded arcs) but no "
                       "radius, diameter or mandrel is printed; no radial dimension exists; P8-N03 forbids scaling",
        "BEND_DIAMETER": "SOURCE_EXPECTED_NOT_LOCATED - no text, note or dimension",
        "CENTRELINE_BEND_GEOMETRY": "SOURCE_EXPECTED_NOT_LOCATED - drawn, not dimensioned",
        "HOOK_ANGLE": "SOURCE_EXPECTED_NOT_LOCATED - hook ticks / corner hook drawn; no angle printed",
        "HOOK_LENGTH_EXTENSION": "SOURCE_EXPECTED_NOT_LOCATED - no text or dimension; project rule register "
                                 "HOOKS_AND_BENDS = NO_PROJECT_SOURCE",
        "CLOSURE_LAP": "SOURCE_EXPECTED_NOT_LOCATED - the only lap note in the set is p.15 'LAP LENGTH FOR ALL "
                       "TEMPERATURE BARS SHALL BE 40xDIA' (slab temperature bars); note 9 70D / 40D is for starters",
        "LINK_FABRICATION_NOTE": "SOURCE_EXPECTED_NOT_LOCATED - no standard-link, bending-schedule or bending note",
        "GENERAL_BENDING_NOTE": "SOURCE_EXPECTED_NOT_LOCATED - p.8 notes 1-24 carry none",
        "COVER_SEMANTICS": "p.8 note 22 prints a MINIMUM cover (>= 2.5 / >= 7 cm): the cover-reduced link envelope "
                           "is an UPPER envelope, not an exact or minimum size"}
    return {"dxf": dx, "pdf_link_corners": corners, "notes": nr, "ocr": {"method": ocr["method"],
                                                                         "terms_found": ocr_terms,
                                                                         "pages": ocr["pages"],
                                                                         "reviewed": ocr["reviewed"]},
            "findings": findings}


# ------------------------------------------------------------------ 2-3. audit + corrections
def stage_rows(pkg, prefix):
    rows = _rows(pkg / f"{prefix}_DELTA_COMPONENTS.csv")
    prov = {}
    for line in (pkg / f"{prefix}_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines():
        p = json.loads(line)
        prov[p["delta_id"]] = p
    return rows, prov


def link_row(stage, r, p, cid):
    inp = p["inputs"]
    b, h, c, d, n = inp["b_mm"], inp["h_mm"], inp["cover_mm"], inp["d_mm"], inp["count"]
    W, T = b - 2 * c - d, h - 2 * c - d
    sharp = DC.sharp_loop_mm(W, T)
    f = json.loads(r["FACETS"])
    check(abs(sharp - f["CORE_PATH_MM"]) < 1e-6, f"{r['DELTA_ID']} sharp path reproduces")
    kg = p["delta_kg"]
    check(abs(kg - float(r["DELTA_KNOWN_QUANTITY"])) < 1e-5, f"{r['DELTA_ID']} kg")
    cls = DC.classify_link_path(bend_radius_mm=None, bend_radius_max_mm=None, hook_length_known=False,
                                closure_known=False, envelope_exact=False)
    check(cls == DC.MODELLED_POLYGONAL_EQUIVALENT, "classification")
    return {"AUDIT_ID": cid, "STAGE": stage, "ORIGINAL_DELTA_ID": r["DELTA_ID"],
            "ORIGINAL_DELTA_COMPONENT_ID": f"{r['BASELINE_COMPONENT_ID']}:{r['PORTION']}",
            "OCCURRENCE_ID": r["OCCURRENCE_ID"], "MARK": r["MARK"], "SPAN_INDEX": r.get("SPAN_INDEX") or "",
            "COMPONENT": r["COMPONENT"],
            "PORTION": r["PORTION"], "OBJECT_KIND": "LINK_CORE_PATH", "TOPOLOGY": f["TOPOLOGY"],
            "B_MM": b, "H_MM": h, "COVER_MM": c, "COVER_STATE": "MINIMUM (P8-N22): envelope is an upper bound",
            "LINK_DIA_MM": d, "COUNT": n, "CENTRELINE_W_MM": W, "CENTRELINE_T_MM": T, "SHARP_PATH_MM": sharp,
            "ROUNDED_LOOP_MM": "2W + 2T - (8 - 2 pi) R = %.0f - 1.7168 R" % sharp, "BEND_RADIUS_R": "NOT_IN_SOURCE",
            "HOOK_LENGTH": "NOT_IN_SOURCE (drawn only)", "CLOSURE": "NOT_IN_SOURCE",
            "CLASSIFICATION": cls, "MASS_USE": "QA_ONLY (modelled value, never known steel)",
            "ORIGINAL_KG": kg, "SOURCE_SAFE_KG": 0.0, "MODELLED_ONLY_KG": kg, "BLOCKED_KG": kg,
            "AUDIT_RESULT": "RETRACTED_TO_MODELLED",
            "WHY": "a bent closed loop is shorter than its sharp polygon by (8 - 2 pi) R; R is not in the issued set "
                   "and not bounded, the hooks / closure are not dimensioned (and may not be used to cover the "
                   "deficit), and the cover is a minimum - no project-source constraint keeps the fabricated bar "
                   "above the sharp path"}


def retained_row(stage, r, p, cid):
    portion, comp = r["PORTION"], r["COMPONENT"]
    kg = p["delta_kg"]
    if portion.startswith("THROUGH_SUPPORT"):
        kind, why = ("THROUGH_SUPPORT_PORTION", "a straight bar inside the column; its length (smaller column side) "
                                                "does not depend on any bend, hook or cover")
    elif portion == "STRAIGHT_PROJECTION":
        kind, why = ("PLANTED_COLUMN_EXTRA_PROJECTION", "a cranked bar is never shorter than its horizontal projection "
                                                        "(2 x DEPTH + column side): rounded bends at the crank and the "
                                                        "hooks do not move its end points; hooks and crank excess stay "
                                                        "excluded")
    elif portion == "STRAIGHT_RUN":
        kind, why = ("LONGITUDINAL_BASE_BAR", "a straight schedule bar over the clear run (B26), or a cranked bar over "
                                              "its plan run (B3 WITH STAIR) - the arc length of a bar is never below "
                                              "its projection, whatever the bend radius; no cover is deducted")
    elif comp == "STIRRUP_COUNT":
        kind, why = ("STIRRUP_COUNT", "a count: ceil(rate x clear run) carries no length and no bend geometry")
    else:
        raise Stop(f"unclassified released row {r['DELTA_ID']}")
    return {"AUDIT_ID": cid, "STAGE": stage, "ORIGINAL_DELTA_ID": r["DELTA_ID"],
            "ORIGINAL_DELTA_COMPONENT_ID": f"{r['BASELINE_COMPONENT_ID']}:{portion}",
            "OCCURRENCE_ID": r["OCCURRENCE_ID"], "MARK": r["MARK"], "SPAN_INDEX": r.get("SPAN_INDEX") or "",
            "COMPONENT": comp, "PORTION": portion, "OBJECT_KIND": kind, "CLASSIFICATION": "INDEPENDENT_OF_BEND_GEOMETRY", "MASS_USE": "KNOWN_STEEL_KEPT",
            "ORIGINAL_KG": kg, "SOURCE_SAFE_KG": kg, "MODELLED_ONLY_KG": 0.0, "BLOCKED_KG": 0.0,
            "AUDIT_RESULT": "RETAINED", "DELTA_COUNT": r.get("DELTA_COUNT") or "", "WHY": why}


def audit(stage, pkg, prefix, corr_prefix, evidence):
    rows, prov = stage_rows(pkg, prefix)
    released = [r for r in rows if r["CHANGE_KIND"] == DR.QUANTITY_RELEASED]
    out, corr = [], []
    for r in released:
        p = prov[r["DELTA_ID"]]
        cid = f"{corr_prefix}-A{len(out) + 1:03d}"
        if r["PORTION"] in LINK_PORTIONS:
            a = link_row(stage, r, p, cid)
            out.append(a)
            corr.append(DC.correction(
                correction_id=f"{corr_prefix}-C{len(corr) + 1:03d}", original_delta_component_id=
                a["ORIGINAL_DELTA_COMPONENT_ID"], original_kg=a["ORIGINAL_KG"], correction_kg=-a["ORIGINAL_KG"],
                correction_reason="sharp-corner path is not a proven lower bound: a bent loop is (8 - 2 pi) R shorter; "
                                  "bend radius, hook length and closure are not in the issued set; cover is a minimum",
                source_evidence=evidence, new_authority_state=DC.MODELLED_POLYGONAL_EQUIVALENT,
                new_release_state=DC.BLOCKED_UNQUANTIFIED, ORIGINAL_DELTA_ID=r["DELTA_ID"], STAGE=stage,
                OCCURRENCE_ID=r["OCCURRENCE_ID"], MARK=r["MARK"], TOPOLOGY=a["TOPOLOGY"], COUNT=a["COUNT"],
                LINK_DIA_MM=a["LINK_DIA_MM"], MODELLED_SHARP_PATH_MM=a["SHARP_PATH_MM"],
                MODELLED_KG_QA_ONLY=a["ORIGINAL_KG"], TOPOLOGY_KEPT="YES", COUNT_KEPT="YES", DIAMETER_KEPT="YES"))
        else:
            out.append(retained_row(stage, r, p, cid))
    return out, corr


# ------------------------------------------------------------------ 4. topology / count / diameter register
def tcd_register():
    out = []
    s6counts = {(r["occurrence_id"], r["span_index"]): r for r in _rows(S6 / "SUPERSTRUCTURE_BEAM_STIRRUP_COUNTS.csv")}
    s61 = {r["STIRRUP_SET_ID"]: r for r in _rows(S61 / "S6_1_STIRRUP_TOPOLOGY.csv")}
    s61_counts = {(r["OCCURRENCE_ID"], r["SPAN_INDEX"]): int(r["DELTA_COUNT"])
                  for r in _rows(S61 / "S6_1_DELTA_COMPONENTS.csv")
                  if r["COMPONENT"] == "STIRRUP_COUNT" and r["CHANGE_KIND"] == DR.QUANTITY_RELEASED}
    for sid, t in sorted(s61.items()):
        key = (t["OCCURRENCE_ID"], t["SPAN_INDEX"])
        sc = s6counts[key]
        if sc["state"] == "LOWER_BOUND":
            count, cstate = int(sc["count_lower_bound"]), "SOURCE_DERIVED_LOWER_BOUND (S6)"
        elif key in s61_counts:
            count, cstate = s61_counts[key], "SOURCE_DERIVED_LOWER_BOUND (S6.1)"
        else:
            count, cstate = None, "BLOCKED_UNQUANTIFIED"
        dia = sc["DIAMETER_MM"]
        out.append({"STIRRUP_SET_ID": sid, "STAGE": "S6.1", "OCCURRENCE_ID": t["OCCURRENCE_ID"], "MARK": t["MARK"],
                    "SPAN_INDEX": t["SPAN_INDEX"], "A_LINK_TOPOLOGY": t["TOPOLOGY"], "LINKS": int(t["LINKS"]),
                    "LEGS": int(t["LEGS"]), "TOPOLOGY_STATE": t["TOPOLOGY_STATE"],
                    "TOPOLOGY_SOURCE": t["TOPOLOGY_SOURCE"], "B_LINK_COUNT": count, "COUNT_STATE": cstate,
                    "C_LINK_DIAMETER_MM": int(dia) if dia else None,
                    "DIAMETER_STATE": ("SOURCE_EXPLICIT (schedule)" if dia and cstate != "BLOCKED_UNQUANTIFIED" else
                                       ("SCHEDULE_VALUE (set blocked)" if dia else "NOT_LOCATED")),
                    "D_LINK_CUT_LENGTH": "BLOCKED_UNQUANTIFIED",
                    "MODELLED_SHARP_PATH_MM_QA_ONLY": float(t["OUTER_LINK_CORE_PATH_MM"]) if t.get(
                        "OUTER_LINK_CORE_PATH_MM") else None,
                    "LINK_MASS": "BLOCKED_UNQUANTIFIED", "INNER_LINK": t.get("INNER_LINK") or ""})
    s5c = defaultdict(dict)
    for r in _rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv"):
        s5c[r["occurrence_id"]][r["component"]] = r
    reg = {o["occurrence_id"]: o for o in _j(S5 / "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json")["occurrences"]}
    icons = {p["row"]: p["icon"] for p in _j(SRD / "13_GRAPHIC_EVIDENCE.json")["evidence"]["E-DXF-03"]["facts"][
        "placements"]}
    s51 = {r["OCCURRENCE_ID"]: r for r in _rows(S51 / "S5_1_DELTA_COMPONENTS.csv") if r["PORTION"] == "CORE_PATH"}
    for o in sorted(reg):
        rr, cm = reg[o], s5c[o]
        if rr["family"] == "STRAP_BEAM":
            icon = icons.get(rr["mark"])
            topo = {"STR2": "STR2_OUTER_PLUS_ONE_INNER_4_LEG", "str3": "STR3_OUTER_PLUS_TWO_INNER_6_LEG"}[icon]
            links = {"STR2": 2, "str3": 3}[icon]
            tsrc = f"SBT REMARKS icon {icon} (E-DXF-03)"
        else:
            topo, links, tsrc = "SINGLE_CLOSED_LINK_2_LEG", 1, "p.13 sections: one closed link each (E-PDF-02)"
        sc, sd = cm["STIRRUP_COUNT"], cm["STIRRUP_DIAMETER"]
        conflict = rr["mark"] == "SB2"
        f = json.loads(s51[o]["FACETS"]) if o in s51 and s51[o]["CHANGE_KIND"] == DR.QUANTITY_RELEASED else {}
        out.append({"STIRRUP_SET_ID": f"{o}:LINKS", "STAGE": "S5.1", "OCCURRENCE_ID": o, "MARK": rr["mark"],
                    "SPAN_INDEX": "1", "A_LINK_TOPOLOGY": topo, "LINKS": links, "LEGS": 2 * links,
                    "TOPOLOGY_STATE": "SOURCE_FOUND_DERIVED" + (" (occurrence SOURCE_CONFLICT)" if conflict else ""),
                    "TOPOLOGY_SOURCE": tsrc,
                    "B_LINK_COUNT": int(sc["count"]) if sc["state"] == "LOWER_BOUND" else None,
                    "COUNT_STATE": ("SOURCE_DERIVED_LOWER_BOUND (S5)" if sc["state"] == "LOWER_BOUND" else
                                    "BLOCKED_UNQUANTIFIED") + (" - SB2 row conflict" if conflict else ""),
                    "C_LINK_DIAMETER_MM": int(sd["value"]) if sd["state"] == "VERIFIED" else None,
                    "DIAMETER_STATE": ("SOURCE_EXPLICIT (S5 VERIFIED)" if sd["state"] == "VERIFIED" else
                                       "SOURCE_EXPECTED_NOT_LOCATED"),
                    "D_LINK_CUT_LENGTH": "BLOCKED_UNQUANTIFIED",
                    "MODELLED_SHARP_PATH_MM_QA_ONLY": f.get("CORE_PATH_MM"), "LINK_MASS": "BLOCKED_UNQUANTIFIED",
                    "INNER_LINK": ("BLOCKED_UNQUANTIFIED" if links > 1 else "NONE")})
    return out


# ------------------------------------------------------------------ docs
README = """# D1.1 stirrup / link core-path authority audit

**Round:** `D1.1` · **Policy:** `{policy}` · **Baseline:** HEAD `59f2083` · **Built by** `build_d1_1_stirrup_audit.py` (blind, byte-identical rebuild)

S4, S5, S6, S4.1, S6.1 and S5.1 are unchanged. All six freeze manifests were hash-checked before anything was read.
Every change below is an explicit CORRECTION_ERRATA record. No frozen file was edited, and PRE-S7 was not started.

## Conclusion

**The sharp-corner link path is a `MODELLED_POLYGONAL_EQUIVALENT`. It is not a lower bound.** All the link mass
released in D1 is retracted to BLOCKED_UNQUANTIFIED:

| Stage | Link kg released in D1 | Retained | Corrected (moved to modelled / QA) |
|---|---|---|---|
| S6.1 | {s6_link:.2f} | 0.00 | {s6_corr:.2f} |
| S5.1 | {s5_link:.2f} | 0.00 | {s5_corr:.2f} |

Every other D1 release is kept, because none of them depends on bend geometry:
- S6.1: B3 WITH STAIR and B26 longitudinal bars {s6_long:.2f} kg, the B26 planted-column extra {s6_extra:.2f} kg, and
  {n_counts} new stirrup counts.
- S5.1: through-support portions {s5_through:.2f} kg.

| | D1 known | Corrected known |
|---|---|---|
| S4.1 | {s41:.2f} | {s41:.2f} |
| S6.1 | {s61:.2f} | {s61c:.2f} |
| S5.1 | {s51:.2f} | {s51c:.2f} |
| **Combined** | **{tot:.2f}** | **{totc:.2f}** |

## The mathematics

Take a closed link whose centreline envelope is W x T, with four 90-degree bends of centreline radius R:

    L_rounded = 2W + 2T - (8 - 2 pi) R = L_sharp - 1.7168 R

Per corner, the sharp path counts 2R and the arc is (pi / 2) R. So L_rounded < L_sharp for every R > 0. Equality
holds only at R = 0, and no bar can be bent to R = 0.

Proving any lower bound would need all three of these:
1. R, or an upper bound on R, from a project source;
2. an envelope that is exact or a minimum;
3. the deficit deducted.

The hooks and the closing overlap could make up the difference, but their lengths are not in the issued set. Using
them is exactly the unsupported premise of D1.

The cover is a second, independent reason:
- p.8 note 22 prints a minimum cover (>= 2.5 cm, >= 7 cm against soil).
- So b - 2c and h - 2c are the largest the link can be, not the smallest.

## Source search ({n_texts} DXF texts / attributes / dimensions, {n_dec} legacy-Arabic notes decoded, the 24 p.8 notes, OCR of pp.9-16, the drawn link geometry)

- **Bend radius / diameter / centreline bend geometry: not located.**
  - The issued p.13 and p.15 link sections draw every corner bent: 4 straight sides plus 16 short chords, i.e. 4
    chords per corner. So the drawing itself shows rounded links.
  - No radius is printed. The DXF has {n_rad} radius or diameter dimensions.
  - P8-N03 says "do not scale the drawings", so the drawn radii cannot be measured.
- **Hook angle / length / extension: not located.** The hook is drawn; the project rule register records
  HOOKS_AND_BENDS = NO_PROJECT_SOURCE.
- **Closure / lap of links: not located.** The only lap rule in the set is for slab temperature bars (p.15: 40 x DIA).
  Note 9 (70D / 40D) applies to starter bars.
- **Link fabrication or bending note: none.**

See `01_SOURCE_SEARCH.md`.

## What stays valid (`05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv`)

For every stirrup set, A topology, B count and C diameter keep their own states, and only D cut length is blocked:
- **Topology:** {n_sets} sets in total: {n_single} single closed links, {n_str2} STR2 (4 legs) and {n_str3} STR3
  (6 legs, SB2, still a source conflict).
- **Counts:** {n_cnt} sets carry a released count.
- **Diameters:** {n_dia} sets carry a source diameter.

## Files

| File | Content |
|---|---|
| `01_SOURCE_SEARCH.md` | what was searched and what each search returned |
| `02_STIRRUP_PATH_AUDIT.csv` | every D1 released row (S6.1 and S5.1): link paths retracted to modelled, other releases kept, with the reason |
| `03_S6_1A_CORRECTIONS.csv` | S6_1A_STIRRUP_AUTHORITY_CORRECTION errata ({n6} rows) |
| `04_S5_1A_CORRECTIONS.csv` | S5_1A_STIRRUP_AUTHORITY_CORRECTION errata ({n5} rows) |
| `05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv` | per stirrup set: topology, count and diameter kept; cut length and mass blocked |
| `06_CORRECTED_RELEASE_SUMMARY.json` | original, correction and corrected totals; conservation; flags |
| `07_PROVENANCE.jsonl` | one line per audited row and per correction |
| `D1_1_FREEZE_MANIFEST.json` | hashes of the code, inputs and outputs |
| `TEST_RUN.md` | the targeted and full-suite runs (written after the freeze) |

## For the owner

The issued set will not support link mass until it states a bend radius (or a maximum), the hook extension and
closure, and the cover as built rather than as a minimum. If an engineer supplies those facts as a versioned claim,
a later round can release a proven lower bound.

The same minimum-cover reading also affects the cover-reduced footing lengths in frozen S4 (span - 2 x 70 mm). That
is outside this audit's scope and was not changed; it is raised as a question.
"""


def source_md(ss):
    dx, nr, ocr, cor = ss["dxf"], ss["notes"], ss["ocr"], ss["pdf_link_corners"]
    lines = ["# 01 SOURCE SEARCH: bend radius, hooks, closure, link fabrication", "",
             "Every channel of the issued set was searched again for the facts a fabricated link length needs. "
             "No design code, external example, donor or other engine was opened.", "",
             "## Findings", "", "| Fact | Result |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in ss["findings"].items()]
    lines += ["", "## A. DXF (ST7757.dxf, all layouts and block definitions)", "",
              f"- Texts scanned: {dx['texts_scanned']} ({', '.join(f'{k} {v}' for k, v in dx['by_type'].items())}).",
              f"- Legacy-Arabic texts decoded: {dx['legacy_arabic_decoded']}.",
              f"- Dimension types: {dx['dimension_types']} (0 linear, 1 aligned).",
              f"- Radius or diameter dimensions: **{dx['radial_or_diameter_dimensions']}**.",
              "- Term hits (every hit is listed below; an absent term had none):"]
    for k, v in dx["term_hits"].items():
        lines.append(f"  - `{k}`: " + "; ".join(f"'{x}'" for x in v))
    lines += [f"- Searched English terms: {', '.join(EN_TERMS)}.",
              f"- Searched Arabic terms: {', '.join(AR_TERMS)}.",
              "- Drawn reinforcement arcs in model space (S-REIN.D), by undimensioned drawn radius in drawing units:",
              "  " + ", ".join(f"{k}: {v}" for k, v in dx["drawn_rebar_arc_radii_units"].items()) + ".",
              "  These several drawn radii show bends are drawn but not defined. They are QA only: P8-N03 forbids "
              "scaling.", "",
              "## B. Issued link sections (PDF vector strokes, S-REIN.D)", "",
              "| Section | Segments | Straight sides | Short corner chords | Corners | Radius dimensioned |",
              "|---|---|---|---|---|---|"]
    for k, v in cor.items():
        lines.append(f"| {k} | {v['segments']} | {v['straight_sides']} | {v['short_corner_chords']} | "
                     f"{v['corner_shape']} | {v['radius_dimensioned']} |")
    lines += ["", "## C. General notes and project rules", "",
              f"- p.8 notes transcribed (S1): {nr['p8_notes']}. Notes containing any bend / hook / lap / link term: "
              f"{', '.join(n['rule_id'] for n in nr['p8_with_any_term']) or 'none'}.",
              "- Notes or typicals anywhere in the S1 rule register containing such a term:"]
    for n in nr["all_notes_with_any_term"]:
        lines.append(f"  - {n['rule_id']} (p.{n['page']}, {', '.join(n['hits'])}): {n['english']}")
    lines += [f"- {nr['do_not_scale']['rule_id']}: {nr['do_not_scale']['english']}",
              f"- {nr['cover']['rule_id']}: {nr['cover']['english']} (rule register scope: "
              f"{', '.join(nr['cover']['r4_scope'])}).",
              f"- Project rule register HOOKS_AND_BENDS: {nr['hooks_and_bends_rule']['source_state']} (never used "
              "for official kg).", "",
              "## D. PDF detail and schedule sheets pp.9-16 (OCR search aid)", "", f"Method: {ocr['method']}.", "",
              f"Terms found: {', '.join(ocr['terms_found'])}. Every hit was re-read:"]
    for k, v in ocr["reviewed"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "No BEND, BENT, RADIUS, HOOK, SPLICE, MANDREL, 135 or OVERLAP text appears on pp.9-16.", ""]
    return "\n".join(lines)


def main():
    frozen = {k: DR.verify_frozen(p, ROOT) for k, p in MANIFESTS.items()}
    ss = source_search()
    evidence = ("01_SOURCE_SEARCH.md: no bend radius, hook length or closure in the issued set; p.13 / p.15 links "
                "drawn bent; P8-N03 do not scale; P8-N22 minimum cover; HOOKS_AND_BENDS NO_PROJECT_SOURCE")
    a6, c6 = audit("S6.1", S61, "S6_1", "S6.1A", evidence)
    a5, c5 = audit("S5.1", S51, "S5_1", "S5.1A", evidence)
    s61 = _j(S61 / "S6_1_RELEASE_SUMMARY.json")
    s51 = _j(S51 / "S5_1_RELEASE_SUMMARY.json")
    s41 = _j(S41 / "S4_1_RELEASE_SUMMARY.json")
    s6_link = sum(c["ORIGINAL_KG"] for c in c6)
    s5_link = sum(c["ORIGINAL_KG"] for c in c5)
    check(abs(s6_link - s61["delta_by_kind_kg"]["stirrup_core_path"]) < 1e-6, "S6.1 link kg = released core paths")
    check(abs(s5_link - s51["delta_by_kind_kg"]["stirrup_core_path"]) < 1e-6, "S5.1 link kg = released core paths")
    s61c = s61["s6_1_known_kg"] + sum(c["CORRECTION_KG"] for c in c6)
    s51c = s51["s5_1_known_kg"] + sum(c["CORRECTION_KG"] for c in c5)
    cons6 = DC.conservation(s61["s6_1_known_kg"], c6, s61c)
    cons5 = DC.conservation(s51["s5_1_known_kg"], c5, s51c)
    check(cons6["all_pass"] and cons5["all_pass"], "correction conservation")
    kept6 = [a for a in a6 if a["AUDIT_RESULT"] == "RETAINED"]
    kept5 = [a for a in a5 if a["AUDIT_RESULT"] == "RETAINED"]
    s6_long = sum(a["SOURCE_SAFE_KG"] for a in kept6 if a["OBJECT_KIND"] == "LONGITUDINAL_BASE_BAR")
    s6_extra = sum(a["SOURCE_SAFE_KG"] for a in kept6 if a["OBJECT_KIND"] == "PLANTED_COLUMN_EXTRA_PROJECTION")
    s5_through = sum(a["SOURCE_SAFE_KG"] for a in kept5 if a["OBJECT_KIND"] == "THROUGH_SUPPORT_PORTION")
    check(abs(s6_long - s61["delta_by_kind_kg"]["longitudinal_base_bars"]) < 1e-6, "S6.1 longitudinal kept whole")
    check(abs(s6_extra - s61["delta_by_kind_kg"]["planted_column_extra"]) < 1e-6, "planted extra kept whole")
    check(abs(s5_through - s51["delta_by_kind_kg"]["longitudinal_through_support"]) < 1e-6, "through-support kept")
    check(abs(s61c - (s61["frozen_s6"]["known_kg"] + s6_long + s6_extra)) < 1e-6, "S6.1A = S6 + kept deltas")
    check(abs(s51c - (s51["frozen_s5"]["known_kg"] + s5_through)) < 1e-6, "S5.1A = S5 + kept deltas")
    counts_kept = [a for a in kept6 if a["OBJECT_KIND"] == "STIRRUP_COUNT"]
    reg = tcd_register()
    tot = s41["s4_1_known_kg"] + s61["s6_1_known_kg"] + s51["s5_1_known_kg"]
    totc = s41["s4_1_known_kg"] + s61c + s51c
    topo_counts = Counter(r["A_LINK_TOPOLOGY"] for r in reg)
    summary = {
        "round": ROUND, "policy": POLICY, "baseline_head": "59f2083",
        "engine_commit": f"{frozen['S6.1']['engine_commit_stamp']}+audit:{code_digest()[:16]}",
        "frozen": frozen, "correction_policy": DC.policy_record(),
        "mathematics": {"sharp_loop": "2W + 2T", "rounded_loop": "2W + 2T - (8 - 2 pi) R",
                        "deficit_per_link": "(8 - 2 pi) R = %.4f R" % (8 - 2 * math.pi),
                        "conclusion": "L_rounded < L_sharp for every R > 0; the sharp path is a "
                                      "MODELLED_POLYGONAL_EQUIVALENT, not a lower bound",
                        "lower_bound_would_need": ["project-source R or R_max", "exact (or minimum) envelope",
                                                   "the deficit deducted; hooks / closure taken as zero"],
                        "second_reason": "P8-N22 cover is a minimum: the cover-reduced envelope is an upper bound"},
        "source_search": {"findings": ss["findings"], "bend_radius_in_source": False,
                          "hook_length_in_source": False, "closure_in_source": False,
                          "dxf_texts_scanned": ss["dxf"]["texts_scanned"],
                          "radial_dimensions": ss["dxf"]["radial_or_diameter_dimensions"],
                          "drawn_link_corners": {k: v["corner_shape"] for k, v in ss["pdf_link_corners"].items()}},
        "s6_1": {"d1_known_kg": s61["s6_1_known_kg"], "link_core_path_kg_released": s6_link,
                 "link_kg_retained": 0.0, "link_kg_retracted": s6_link, "corrections": len(c6),
                 "other_retained_kg": {"longitudinal_base_bars": s6_long, "planted_column_extra": s6_extra},
                 "stirrup_counts_retained": {f'{a["OCCURRENCE_ID"]}#{a.get("SPAN_INDEX") or "1"}': int(a["DELTA_COUNT"])
                                             for a in counts_kept},
                 "corrected_known_kg": s61c, "frozen_s6_known_kg": s61["frozen_s6"]["known_kg"],
                 "conservation": cons6},
        "s5_1": {"d1_known_kg": s51["s5_1_known_kg"], "link_core_path_kg_released": s5_link,
                 "link_kg_retained": 0.0, "link_kg_retracted": s5_link, "corrections": len(c5),
                 "other_retained_kg": {"through_support": s5_through},
                 "corrected_known_kg": s51c, "frozen_s5_known_kg": s51["frozen_s5"]["known_kg"],
                 "conservation": cons5},
        "s4_1": {"known_kg": s41["s4_1_known_kg"], "link_paths": 0},
        "combined": {"frozen_s4_s5_s6_kg": s41["frozen_s4"]["known_kg"] + s61["frozen_s6"]["known_kg"] +
                     s51["frozen_s5"]["known_kg"], "d1_kg": tot, "corrected_kg": totc,
                     "scope": "footings (S4.1) + superstructure beams (S6.1A) + ground system (S5.1A)"},
        "topology_count_diameter": {"stirrup_sets": len(reg), "by_topology": dict(sorted(topo_counts.items())),
                                    "with_count": sum(1 for r in reg if r["B_LINK_COUNT"] is not None),
                                    "with_diameter": sum(1 for r in reg if r["C_LINK_DIAMETER_MM"] is not None),
                                    "cut_length_blocked": sum(1 for r in reg if r["D_LINK_CUT_LENGTH"] ==
                                                              "BLOCKED_UNQUANTIFIED")},
        "flags": {"frozen_outputs_changed": False, "normal_delta_rule_changed": False,
                  "hook_length_used_as_proof": False, "external_code_used": False, "plotted_scale_used": False,
                  "pre_s7_started": False, "references_read": []},
        "owner_question": "the issued set gives no bend radius / hook / closure and prints a minimum cover; link "
                          "mass needs these as a versioned project claim. The same minimum-cover reading bears on the "
                          "cover-reduced footing lengths of frozen S4 (not changed here)."}
    audit_fields = ["AUDIT_ID", "STAGE", "ORIGINAL_DELTA_ID", "ORIGINAL_DELTA_COMPONENT_ID", "OCCURRENCE_ID", "MARK",
                    "SPAN_INDEX", "COMPONENT", "PORTION", "OBJECT_KIND", "TOPOLOGY", "B_MM", "H_MM", "COVER_MM", "COVER_STATE",
                    "LINK_DIA_MM", "COUNT", "CENTRELINE_W_MM", "CENTRELINE_T_MM", "SHARP_PATH_MM", "ROUNDED_LOOP_MM",
                    "BEND_RADIUS_R", "HOOK_LENGTH", "CLOSURE", "CLASSIFICATION", "MASS_USE", "ORIGINAL_KG",
                    "SOURCE_SAFE_KG", "MODELLED_ONLY_KG", "BLOCKED_KG", "AUDIT_RESULT", "DELTA_COUNT", "WHY"]
    _csv(HERE / "02_STIRRUP_PATH_AUDIT.csv", a6 + a5, audit_fields)
    corr_fields = ["CORRECTION_ID", "RECORD_TYPE", "STAGE", "ORIGINAL_DELTA_ID", "ORIGINAL_DELTA_COMPONENT_ID",
                   "OCCURRENCE_ID", "MARK", "ORIGINAL_KG", "CORRECTION_REASON", "SOURCE_EVIDENCE",
                   "NEW_AUTHORITY_STATE", "NEW_RELEASE_STATE", "CORRECTION_KG", "RETAINED_KG", "MODELLED_KG_QA_ONLY",
                   "MODELLED_SHARP_PATH_MM", "TOPOLOGY", "COUNT", "LINK_DIA_MM", "TOPOLOGY_KEPT", "COUNT_KEPT",
                   "DIAMETER_KEPT"]
    _csv(HERE / "03_S6_1A_CORRECTIONS.csv", c6, corr_fields)
    _csv(HERE / "04_S5_1A_CORRECTIONS.csv", c5, corr_fields)
    reg_fields = ["STIRRUP_SET_ID", "STAGE", "OCCURRENCE_ID", "MARK", "SPAN_INDEX", "A_LINK_TOPOLOGY", "LINKS", "LEGS",
                  "TOPOLOGY_STATE", "TOPOLOGY_SOURCE", "B_LINK_COUNT", "COUNT_STATE", "C_LINK_DIAMETER_MM",
                  "DIAMETER_STATE", "D_LINK_CUT_LENGTH", "MODELLED_SHARP_PATH_MM_QA_ONLY", "LINK_MASS", "INNER_LINK"]
    _csv(HERE / "05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv", reg, reg_fields)
    _json(HERE / "06_CORRECTED_RELEASE_SUMMARY.json", summary)
    with open(HERE / "07_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for a in a6 + a5:
            f.write(json.dumps({"kind": "AUDIT", "audit_id": a["AUDIT_ID"], "stage": a["STAGE"],
                                "original_delta_id": a["ORIGINAL_DELTA_ID"],
                                "original_component": a["ORIGINAL_DELTA_COMPONENT_ID"], "result": a["AUDIT_RESULT"],
                                "classification": a["CLASSIFICATION"], "original_kg": a["ORIGINAL_KG"],
                                "source_safe_kg": a["SOURCE_SAFE_KG"], "why": a["WHY"],
                                "frozen_stage_manifest": frozen[a["STAGE"]]["manifest_sha256"]},
                               sort_keys=True, ensure_ascii=False) + "\n")
        for c in c6 + c5:
            f.write(json.dumps({"kind": DC.RECORD_TYPE, **c}, sort_keys=True, ensure_ascii=False) + "\n")
    (HERE / "01_SOURCE_SEARCH.md").write_text(source_md(ss), encoding="utf-8")
    (HERE / "00_README.md").write_text(README.format(
        policy=POLICY, s6_link=s6_link, s6_corr=-s6_link, s5_link=s5_link, s5_corr=-s5_link, s6_long=s6_long,
        s6_extra=s6_extra, n_counts=len(counts_kept), s5_through=s5_through, s41=s41["s4_1_known_kg"],
        s61=s61["s6_1_known_kg"], s61c=s61c, s51=s51["s5_1_known_kg"], s51c=s51c, tot=tot, totc=totc,
        n_texts=ss["dxf"]["texts_scanned"], n_dec=ss["dxf"]["legacy_arabic_decoded"],
        n_rad=ss["dxf"]["radial_or_diameter_dimensions"], n_sets=len(reg),
        n_single=topo_counts.get("SINGLE_CLOSED_LINK_2_LEG", 0), n_str2=topo_counts.get(
            "STR2_OUTER_PLUS_ONE_INNER_4_LEG", 0), n_str3=topo_counts.get("STR3_OUTER_PLUS_TWO_INNER_6_LEG", 0),
        n_cnt=summary["topology_count_diameter"]["with_count"],
        n_dia=summary["topology_count_diameter"]["with_diameter"], n6=len(c6), n5=len(c5)), encoding="utf-8")
    manifest = {"round": ROUND, "state": "FROZEN", "frozen_baselines": frozen,
                "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
                "drawing_sha256": {"ST7757.dxf": DXF_SHA, "ST7757.pdf": PDF_SHA},
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "references_read_before_freeze": [],
                "rule": "an errata layer over frozen S6.1 / S5.1; S4, S5, S6, S4.1, S6.1 and S5.1 are never edited"}
    _json(HERE / "D1_1_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({k: summary[k] for k in ("s6_1", "s5_1", "combined", "topology_count_diameter")}, indent=1,
                     default=str)[:3000])


if __name__ == "__main__":
    main()
