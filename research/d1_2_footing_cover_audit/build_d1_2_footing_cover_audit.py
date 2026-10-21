"""URBAN PROJECTS D1.2 - S4 footing cover / bar-length authority audit (narrow; authority, not redesign).

    python3 -I research/d1_2_footing_cover_audit/build_d1_2_footing_cover_audit.py

Frozen S4 / S4.1 footing bars use BAR_LENGTH = FOOTING_DIMENSION - 2 x 70 mm, and the rate counts of two-layer
footings use ceil(rate x (DIMENSION - 2 x 70 mm)). This audit:
  1. searches the issued set for the cover rule's exact wording and for any exact bar-to-face dimension in the
     footing details:
       - the p.8 note, from the S1 transcription and the raster re-read;
       - the R4 rule register;
       - every DXF text, attribute and dimension, legacy Arabic decoded;
       - the p.13 footing-detail vector strokes;
       - the visual / OCR reading of the details;
  2. classifies the cover basis (EXACT / MINIMUM / DERIVED_EXACT / BOUNDED / UNRESOLVED);
  3. audits every mass-bearing S4 / S4.1 footing part, keeping apart:
       - the straight segment caused by the cover;
       - the rate count inside the cover, and its edge-bar convention;
       - the unquantified legs / hooks / bends / end treatment;
  4. writes S4_1A_COVER_AUTHORITY_CORRECTION records (engine.source.cover_authority) without editing S4 or S4.1.
Blind: issued drawing + frozen Urban registers only. No cover is invented and no actual cover is assumed. Deterministic.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
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
from engine.source import cover_authority as CA  # noqa: E402
from engine.source import delta_release as DR  # noqa: E402
from engine.source import legacy_text as LT  # noqa: E402

ROUND = "D1.2"
POLICY = "FOOTING_COVER_AUTHORITY_AUDIT_V1"
BASELINE_HEAD = "1384bf3"
R = ROOT / "research"
S4, S41 = R / "alsenan_footing_rebar_s4", R / "alsenan_footing_rebar_s4_1"
S5, S6 = R / "alsenan_ground_system_rebar_s5", R / "alsenan_superstructure_beam_rebar_s6"
S51, S61 = R / "alsenan_ground_system_rebar_s5_1", R / "alsenan_superstructure_beam_rebar_s6_1"
AD1, D11 = R / "ad1_authority_decisions", R / "d1_1_stirrup_authority_audit"
S1 = R / "alsenan_structural_census_s1"
R4 = R / "alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json"
VIS = HERE / "source_search_inputs/D1_2_VISUAL_SEARCH.json"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
DXF = ROOT / "data/inputs/by_sha256" / f"{DXF_SHA}.dxf"
PDF = ROOT / "data/inputs/by_sha256" / f"{PDF_SHA}.pdf"
MANIFESTS = {"S4": S4 / "S4_FREEZE_MANIFEST.json", "S4.1": S41 / "S4_1_FREEZE_MANIFEST.json",
             "S5": S5 / "S5_FREEZE_MANIFEST.json", "S6": S6 / "S6_FREEZE_MANIFEST.json",
             "S6.1": S61 / "S6_1_FREEZE_MANIFEST.json", "S5.1": S51 / "S5_1_FREEZE_MANIFEST.json",
             "AD1": AD1 / "AD1_FREEZE_MANIFEST.json", "D1.1": D11 / "D1_1_FREEZE_MANIFEST.json"}
CODE = ["engine/source/cover_authority.py", "engine/source/delta_release.py", "engine/source/legacy_text.py",
        "research/source_recovery_delta/vector_pdf.py",
        "research/d1_2_footing_cover_audit/build_d1_2_footing_cover_audit.py"]
INPUTS = [str(p.relative_to(ROOT)) for p in MANIFESTS.values()] + [
    "research/alsenan_structural_census_s1/STRUCTURAL_PROJECT_RULE_REGISTER.json",
    "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json",
    "research/d1_2_footing_cover_audit/source_search_inputs/D1_2_VISUAL_SEARCH.json"]
OUTPUTS = ["00_README.md", "01_SOURCE_SEARCH.md", "02_COVER_BASIS.json", "03_FOOTING_COVER_AUDIT.csv",
           "04_S4_1A_COVER_AUTHORITY_CORRECTION.csv", "05_CORRECTED_RELEASE_SUMMARY.json", "06_PROVENANCE.jsonl"]
COVER_TERMS = re.compile(r"COVER|\bCOV\b|CLEAR\s*COVER|CONCRETE\s+COVER|\b7\s*cm\b|\b70\s*mm\b|\b7\.0\s*cm\b",
                         re.I)
AR_COVER = ("غطاء", "الغطاء", "سمك الغطاء")
DETAIL_BOXES = {"SHALLOW": (380, 181, 820, 671), "DEEP": (380, 671, 820, 1161)}
MIN_COVER_MM = 70.0


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"D1.2 check failed: {what}")


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
def rule_sources():
    n22 = next(r for r in _j(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"] if r["rule_id"] == "P8-N22")
    r4 = next(r for r in _j(R4)["rules"] if r["rule_id"] == "COVER_AGAINST_SOIL_70MM")
    vis = _j(VIS)
    check(vis["pdf_sha256"] == PDF_SHA, "visual search refers to the issued PDF")
    kinds = {"s1_transcription": CA.wording_kind(n22["raw_text"]),
             "p8_raster_reread": CA.wording_kind(vis["p8_note_22"]["visual_reading"]),
             "r4_register_scope": CA.wording_kind(r4["scope"])}
    check(set(kinds.values()) == {CA.MINIMUM}, f"every reading of the cover rule is a minimum: {kinds}")
    check(n22["values"]["soil_mm"] == 70 and r4["value"] == 70 and "FOOTING" in r4["applies_to"], "70 mm / footings")
    s4_auth = None
    for line in open(S4 / "FOOTING_REBAR_PROVENANCE.jsonl", encoding="utf-8"):
        d = json.loads(line)
        if d.get("kg"):
            s4_auth = d["provenance"]["CONVENTION_ID"]
            break
    s4_rule = (S4 / "build_footing_rebar_s4.py").read_text(encoding="utf-8")
    check('"authority": "SOURCE_EXPLICIT"' in s4_rule, "S4 recorded the cover as SOURCE_EXPLICIT")
    return {"note": {"rule_id": n22["rule_id"], "page": n22["page"], "source_file": n22["source_file"],
                     "channels": n22["channels"], "raw_text": n22["raw_text"],
                     "english": vis["p8_note_22"]["translation"],
                     "s1_english_interpretation": n22["english_interpretation"], "values": n22["values"]},
            "r4": {"rule_id": r4["rule_id"], "value": r4["value"], "scope": r4["scope"], "claim_id": r4["claim_id"],
                   "applies_to": r4["applies_to"]},
            "wording_kind": kinds,
            "s4_use": {"rule": "COVER_AGAINST_SOIL_70MM taken as the cover value with authority SOURCE_EXPLICIT; "
                               "net straight = span - 70 - 70; rate count = ceil(rate x (dimension - 2 x 70))",
                       "convention_id_example": s4_auth}}


def dxf_sweep():
    check(_sha(DXF) == DXF_SHA, "ST7757.dxf sha256")
    doc = ezdxf.readfile(str(DXF))
    styles = {s.dxf.name.upper(): (s.dxf.font or "") for s in doc.styles}
    texts = []

    def take(e, where):
        t = e.dxftype()
        if t == "DIMENSION":
            s, dec = e.dxf.get("text", "") or "", None
        elif t in ("TEXT", "ATTRIB", "ATTDEF"):
            s = e.dxf.text
        elif t == "MTEXT":
            s = e.plain_text()
        else:
            return
        if t != "DIMENSION":
            fam = LT.font_family(styles.get(str(e.dxf.get("style", "STANDARD")).upper(), ""))
            dec = LT.decode(s, fam)["text"] if fam else None
        texts.append({"handle": e.dxf.handle, "type": t, "where": where, "layer": e.dxf.layer, "raw": s or "",
                      "decoded": dec})

    for lay in doc.layouts:
        for e in lay:
            take(e, "layout:" + lay.name)
            if e.dxftype() == "INSERT":
                for a in e.attribs:
                    take(a, "insert:" + e.dxf.name)
    for b in doc.blocks:
        if b.name.startswith(("*Model", "*Paper", "*MODEL", "*PAPER")):
            continue
        for e in b:
            take(e, "block:" + b.name)
    cover_en = [t for t in texts if COVER_TERMS.search(t["raw"])]
    cover_ar = [t for t in texts if t["decoded"] and any(a in t["decoded"] for a in AR_COVER)]
    seven5 = [t for t in texts if "7.5cm" in t["raw"].replace(" ", "")]
    check(not cover_en and not cover_ar, "no DXF text states a cover")
    check(seven5 and {t["layer"] for t in seven5} == {"S-DIM.SCH"}, "the only 7.5cm dimensions sit on S-DIM.SCH")
    return {"texts_scanned": len(texts), "cover_text_hits": 0, "arabic_cover_hits": 0,
            "seven_point_five_cm": {"count": len(seven5), "layers": sorted({t["layer"] for t in seven5}),
                                    "handles": sorted({t["handle"] for t in seven5}),
                                    "reading": "continuous-beam typical figures (pp.11-12): the 7.5 cm dimension that "
                                               "binds the CB bottom bar; not a footing cover"},
            "note_22_in_dxf": False}


def pdf_details():
    check(_sha(PDF) == PDF_SHA, "ST7757.pdf sha256")
    g = _j(R / "source_recovery_delta/13_GRAPHIC_EVIDENCE.json")["evidence"]["E-PDF-01"]["facts"]
    p13 = V.paths(PDF, 13)
    out = {}
    for name, box in DETAIL_BOXES.items():
        u = g[name]["long_bar_U"]
        bot = u["base"][0][0]
        ylo, yhi = sorted((u["base"][0][1], u["base"][1][1]))
        legs_y = [leg[0][1] for leg in u["legs"]]
        dims = V.segments(p13, box, {"S-DIM.D"})
        ticks = [s for s in dims if math.dist(s[2], s[3]) < 7 and
                 abs(abs(s[2][0] - s[3][0]) - abs(s[2][1] - s[3][1])) < 0.8]
        mids = [((s[2][0] + s[3][0]) / 2, (s[2][1] + s[3][1]) / 2) for s in ticks]
        on_bottom = [m for m in mids if abs(m[0] - bot) < 1.2 and ylo - 2 <= m[1] <= yhi + 2]
        on_legs = [m for m in mids if any(abs(m[1] - y) < 1.2 for y in legs_y) and bot - 2 <= m[0] <= bot + 70]
        check(not on_bottom and not on_legs, f"p.13 {name}: no dimension tick on a footing bar line")
        out[name] = {"dimension_segments": len(dims), "dimension_ticks": len(ticks),
                     "ticks_on_bottom_bar_line": 0, "ticks_on_bar_leg_lines": 0,
                     "bottom_bar_level_pt": bot, "reading": "no dimension is bound to a footing bar line: the bar "
                                                            "position inside the footing is drawn, not dimensioned"}
    return out


def source_search():
    rs, dx, pdf = rule_sources(), dxf_sweep(), pdf_details()
    vis = _j(VIS)
    for name in DETAIL_BOXES:
        d = vis["p13_footing_details"][name]
        check(d["bar_to_concrete_face_dimension"] == "NONE" and d["cover_annotation"] == "NONE",
              f"{name}: no cover dimension read on the detail")
    check(vis["ocr_pp9_16"]["footing_cover_hits"] == 0, "no footing cover in the pp.9-16 OCR")
    basis = CA.classify_cover_basis(rule_kind=CA.MINIMUM, value_mm=MIN_COVER_MM, detail_exact_mm=None,
                                    derived_exact_mm=None, bounds_mm=None)
    check(basis["label"] == "MINIMUM_PROJECT_COVER_70", "cover basis")
    return {"rules": rs, "dxf": dx, "pdf_vector": pdf, "visual": vis, "basis": basis}


# ------------------------------------------------------------------ 2. per-component audit
def component_audit(basis):
    prov = {}
    for line in open(S4 / "FOOTING_REBAR_PROVENANCE.jsonl", encoding="utf-8"):
        d = json.loads(line)
        if d.get("kg"):
            prov[d["part_id"]] = d
    s4c = {f"{r['occurrence_id']}:{r['component']}": r for r in _rows(S4 / "FOOTING_REBAR_COMPONENTS.csv")}
    s41 = defaultdict(list)
    for r in _rows(S41 / "S4_1_DELTA_COMPONENTS.csv"):
        s41[r["BASELINE_COMPONENT_ID"]].append(r)
    occ = {o["occurrence_id"]: o for o in _j(S4 / "FOOTING_REBAR_OCCURRENCE_REGISTER.json")["occurrences"]}
    rows, corr = [], []
    for cid in sorted(prov):
        p, c = prov[cid], s4c[cid]
        inp = p["provenance"]["INPUTS"]
        main = [r for r in s41[cid] if float(r["NEW_KNOWN_QUANTITY"] or 0) > 0]
        check(len(main) == 1, f"{cid}: one S4.1 mass row")
        m = main[0]
        blocked = [r for r in s41[cid] if r is not m and r["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED"]
        two_layer = occ[c["occurrence_id"]]["schedule_row"]["layers"] == "TWO_LAYER"
        span, dist = float(inp["raw_span_mm"]), float(inp["distribution_mm"])
        check(float(inp["cover_1_mm"]) == float(inp["cover_2_mm"]) == MIN_COVER_MM, f"{cid}: 70 / 70")
        run = CA.straight_run_claim(span, basis)
        check(abs(run["value_mm"] - float(inp["net_straight_mm"])) < 1e-6, f"{cid}: frozen net = span - 140")
        mode = inp["count_mode"]
        if mode == "BARS_PER_METRE":
            n70 = CA.count_at_cover(inp["count_value"], dist, MIN_COVER_MM)
            check(n70 == int(inp["count_used"]), f"{cid}: frozen rate count = ceil(rate x (W - 140))")
            count_dir = CA.count_direction(mode, basis, edge_bar_established=False)
            conv = re.search(r"convention n = .*?= (\d+)", inp["count_formula"])
            n_edge = int(conv.group(1)) if conv else None
            count_note = (f"rate {inp['count_value']}/m over W - 2c = {dist:g} - 140 mm: ceil = {n70}; with a bar "
                          f"at both edges {n_edge}. A larger actual cover can only lower the formula count, the "
                          "edge-bar convention can raise it: no bound")
        else:
            check(mode == "EXPLICIT_COUNT", f"{cid}: count mode")
            count_dir, n_edge = CA.count_direction(mode, basis), None
            count_note = f"printed count {inp['count_value']} (cover-independent)"
        end_state = ("U-bar legs / 45° hooks / bends SHAPE_FOUND_LENGTH_BLOCKED" if blocked else
                     "END_TREATMENT_NOT_ESTABLISHED")
        n_add = len(blocked) if blocked else 1
        mass_dir = CA.combine(run["direction"], count_dir)
        mass_dir = CA.with_unquantified_additions(mass_dir, n_add)
        mstate = CA.mass_state(mass_dir)
        check(mstate == CA.PROJECT_BASIS_NUMERIC, f"{cid}: no bound survives")
        kg = float(p["kg"])
        dia = int(inp["dia_mm"])
        check(abs(kg - int(inp["count_used"]) * run["value_mm"] / 1000.0 * dia * dia / 162.0) < 1e-6,
              f"{cid}: kg = n x (span - 140) x d^2/162")
        row = {"AUDIT_ID": f"D1.2-A{len(rows) + 1:03d}", "OCCURRENCE_ID": c["occurrence_id"], "MARK": c["mark"],
               "LAYERING": "TWO_LAYER" if two_layer else "SINGLE_LAYER", "COMPONENT": c["component"],
               "S4_1_DELTA_ID": m["DELTA_ID"], "FOOTING_DIMENSION_MM": span, "DISTRIBUTION_DIMENSION_MM": dist,
               "RUN_DIRECTION": inp["run_dir"], "DIAMETER_MM": dia, "COUNT_MODE": mode,
               "COUNT_OR_RATE": inp["count_value"], "COUNT_USED": int(inp["count_used"]),
               "COUNT_WITH_EDGE_BARS": n_edge, "CURRENT_COVER": "70 / 70 mm", "CURRENT_LENGTH_MM": run["value_mm"],
               "SOURCE_FOR_COVER": "ST7757.pdf p.8 note 22 (raster): 'shall not be less than ... 7 cm in concrete in "
                                   "contact with the soil'; R4 COVER_AGAINST_SOIL_70MM scope 'minimum cover'",
               "COVER_AUTHORITY": basis["label"], "ORIGINAL_STATE": m["NEW_RELEASE_STATE"],
               "A_STRAIGHT_SEGMENT_STATE": run["state"], "A_STRAIGHT_SEGMENT_DIRECTION": run["direction"],
               "B_COUNT_DIRECTION": count_dir, "B_COUNT_NOTE": count_note,
               "C_END_PORTIONS_STATE": "BLOCKED_UNQUANTIFIED", "C_END_PORTIONS": end_state,
               "NEW_LENGTH_STATE": run["state"], "MASS_DIRECTION": mass_dir, "MASS_STATE": mstate,
               "KG_AT_MIN_COVER": kg, "AS_BUILT_KG_STATE": "NOT_ESTABLISHED",
               "NOTES": ("straight run at the 70 mm minimum is the maximum the source allows (actual <= value); "
                         + ("count is printed; " if mode == "EXPLICIT_COUNT" else "rate count moves with the cover "
                            "and the edge-bar convention; ") +
                         "the legs / hooks / end treatment can only add length and stay unquantified, so the kg is a "
                         "project-drawing number at minimum cover, not a lower or an upper bound of the as-built "
                         "bar")}
        rows.append(row)
        corr.append(CA.cover_correction(
            correction_id=f"S4.1A-C{len(corr) + 1:03d}", component_id=cid, original_state=m["NEW_RELEASE_STATE"],
            original_kg=kg, cover_basis=basis["basis"], new_length_state=run["state"],
            new_count_direction=count_dir, new_mass_state=mstate,
            correction_reason="70 mm is a minimum cover (note 22 'shall not be less than'); the straight run at 70 mm "
                              "is a maximum, not a lower bound; the end portions are unquantified additions",
            source_evidence="01_SOURCE_SEARCH.md: P8-N22 minimum wording; no bar-to-face dimension in either p.13 "
                            "footing detail; no cover text in the DXF; R4 scope 'minimum cover'",
            correction_kg=0.0, STAGE="S4.1", ORIGINAL_DELTA_ID=m["DELTA_ID"], OCCURRENCE_ID=c["occurrence_id"],
            MARK=c["mark"], COMPONENT=c["component"], LAYERING=row["LAYERING"],
            KG_AT_MIN_COVER=kg, AS_BUILT_KG_STATE="NOT_ESTABLISHED",
            STRAIGHT_SEGMENT_DIRECTION=run["direction"], END_PORTIONS_STATE="BLOCKED_UNQUANTIFIED"))
    return rows, corr


README = """# D1.2: S4 footing cover / bar-length authority audit

**Round:** `{round}` · **Policy:** `{policy}` · **Baseline:** HEAD `{head}` · **Built by** `build_d1_2_footing_cover_audit.py` (blind, byte-identical rebuild)

S4 and S4.1 are unchanged; so are S5, S6, S5.1, S6.1, AD1 and D1.1. All eight freeze manifests were hash-checked
before anything was read. No cover was invented and no actual cover was assumed. PRE-S7 was not started.

## The cover rule

ST7757.pdf p.8, note 22 (raster page, read again for this audit):

> 22. يجب أن لا يقل سمك الغطاء الخرساني عن 2.5 سم في الأعمدة والبلاطات والجسور وعن 7سم في الخرسانة الملاصقة للتربة.
>
> "The concrete cover thickness shall **not be less than** 2.5 cm in columns, slabs and beams, and 7 cm in concrete
> in contact with the soil."

**Cover basis: `{basis}`.**
- The wording is a minimum ("لا يقل ... عن").
- The R4 rule register already scoped the rule as "minimum cover".
- Neither p.13 footing detail fixes the bar position:
  - no dimension is bound to a bar line (0 dimension ticks on any footing bar line);
  - the only dimensions in the footing body are the column-bar foot (Min. 30 cm, Max. 10 cm), the screed (5) and
    the plain concrete (10).
- No DXF text states a cover ({n_texts} texts, attributes and dimensions scanned, legacy Arabic decoded).
- S4 had taken the value as an exact SOURCE_EXPLICIT cover.

## What it means for the bars

So the actual cover is >= 70 mm, and therefore:
- **Straight segment:** at most dimension - 2 x 70. The frozen straight length is the *maximum* the source allows
  (SOURCE_MAXIMUM_STRAIGHT_RUN). It is not a lower bound.
- **Rate counts (two-layer footings):** ceil(rate x (dimension - 2 x 70)). A larger actual cover can only lower the
  count; a bar at the far edge (+1, not established) can raise it. The count has no bound either way.
- **Legs / hooks / bends / end treatment:** these can only add length, and they stay BLOCKED_UNQUANTIFIED.

The three pull in opposite directions, so no bound survives on any of the {n} parts. The kg is a project-drawing
number at minimum cover (PROJECT_BASIS_NUMERIC). It is not the as-built mass.

| | Parts | kg at minimum cover |
|---|---|---|
| single-layer BOTTOM_LONG / BOTTOM_SHORT (printed counts) | {n_single} | {kg_single:.2f} |
| two-layer TOP / BOTTOM LONG / SHORT (rate counts) | {n_two} | {kg_two:.2f} |
| **Total** | **{n}** | **{kg:.2f}** |

**Quantity change:** 0.00 kg. **Authority change:** {n} parts, LOWER_BOUND -> PROJECT_BASIS_NUMERIC
(`04_S4_1A_COVER_AUTHORITY_CORRECTION.csv`).

## Two figures, kept apart

| | Project-drawing basis | As-built lower bound known |
|---|---|---|
| S4.1 footings | {kg:.2f} (at the 70 mm minimum) | not established |
| S5.1 ground system (after D1.1 / AD1) | {s51:.2f} | {s51:.2f} |
| S6.1 superstructure beams (after D1.1) | {s61:.2f} | {s61:.2f} |
| **Combined** | **{comb:.2f}** | **{asb:.2f}** |

S5 / S6 kg does not use a cover:
- {n_s5} released S5 and {n_s6} released S6 components were checked; none uses a cover term.
- Their lengths are support-face or clear runs, column sides and printed projections.

## Files

| File | Content |
|---|---|
| `01_SOURCE_SEARCH.md` | the rule wording, the footing-detail and DXF searches, the classification |
| `02_COVER_BASIS.json` | the cover basis with its evidence |
| `03_FOOTING_COVER_AUDIT.csv` | every mass-bearing S4 / S4.1 footing part: dimension, diameter, count / rate, cover, length, cover authority, the three separate uncertainties, new states |
| `04_S4_1A_COVER_AUTHORITY_CORRECTION.csv` | the state corrections (0 kg each) |
| `05_CORRECTED_RELEASE_SUMMARY.json` | the two figures, conservation, flags |
| `06_PROVENANCE.jsonl` | one line per audited part and per correction |
| `source_search_inputs/D1_2_VISUAL_SEARCH.json` | the p.8 re-read and the p.13 detail reading (render hashes only) |
| `D1_2_FREEZE_MANIFEST.json` | hashes of the code, inputs and outputs |
| `TEST_RUN.md` | the targeted and full-suite runs |

## For the owner

A footing-specific cover (for example a dimensioned bar-to-face offset), or an engineer's statement of the cover as
detailed, would make the straight lengths exact. A lower bound of the as-built footing steel would also need the leg,
hook and edge-bar facts. Until then the footing kg stays a project-basis figure.
"""


def source_md(ss):
    rs, dx, pdf, vis = ss["rules"], ss["dxf"], ss["pdf_vector"], ss["visual"]
    lines = ["# 01 SOURCE SEARCH: footing cover", "",
             f"**Classification: `{ss['basis']['label']}`** (exactly one of EXACT_PROJECT_COVER_70 / "
             "MINIMUM_PROJECT_COVER_70 / DERIVED_EXACT_COVER / BOUNDED_COVER / UNRESOLVED).", "",
             "## A. General minimum-cover note", "",
             f"- {rs['note']['rule_id']} ({rs['note']['source_file']} p.{rs['note']['page']}, channels "
             f"{', '.join(rs['note']['channels'])}):",
             f"  - Arabic: {rs['note']['raw_text']}", f"  - English: {rs['note']['english']}",
             f"- Wording read as: {rs['wording_kind']} (every reading: MINIMUM).",
             f"- R4 register: {rs['r4']['rule_id']} = {rs['r4']['value']} mm, scope '{rs['r4']['scope']}', applies to "
             f"{', '.join(rs['r4']['applies_to'])}.",
             f"- S4 used it as: {rs['s4_use']['rule']}.", "",
             "## B. Exact bar centreline / face offset in the footing details", "",
             "Both p.13 details 'TYP. DETAIL OF ISOLATED FOOTING' were checked in two ways:",
             "- the vector strokes (S-DIM.D dimension ticks against the S-REIN.D bar lines);",
             "- a visual reading of every printed label and dimension in the footing body.", ""]
    for name, d in pdf.items():
        lines.append(f"- {name}: {d['dimension_segments']} dimension segments, {d['dimension_ticks']} ticks; "
                     f"{d['ticks_on_bottom_bar_line']} on the bottom-bar line, {d['ticks_on_bar_leg_lines']} on the "
                     "bar legs.")
        for k, v in vis["p13_footing_details"][name]["printed_labels_and_dimensions"].items():
            lines.append(f"  - '{k}': {v}")
        lines.append("  - bar-to-concrete-face dimension: NONE; cover annotation: NONE")
    lines += ["", "## C. DXF", "",
              f"- {dx['texts_scanned']} texts, attributes and dimension overrides scanned, legacy Arabic decoded.",
              "- Cover wording found: 0 (English); 0 (Arabic 'غطاء').",
              f"- Note 22 is not in the DXF; it exists only on the p.8 raster.",
              f"- The only '7.5cm' values: {dx['seven_point_five_cm']['count']} on "
              f"{dx['seven_point_five_cm']['layers']} = {dx['seven_point_five_cm']['reading']}.", "",
              "## D. OCR of pp.9-16", "", f"- {vis['ocr_pp9_16']['source']}.",
              f"- Hits: {vis['ocr_pp9_16']['hits']}; footing cover hits: {vis['ocr_pp9_16']['footing_cover_hits']}.",
              "", "## Method", "", vis["method"], ""]
    return "\n".join(lines)


def main():
    frozen = {k: DR.verify_frozen(p, ROOT) for k, p in MANIFESTS.items()}
    ss = source_search()
    basis = ss["basis"]
    rows, corr = component_audit(basis)
    s41 = _j(S41 / "S4_1_RELEASE_SUMMARY.json")
    d11 = _j(D11 / "06_CORRECTED_RELEASE_SUMMARY.json")
    kg = sum(r["KG_AT_MIN_COVER"] for r in rows)
    check(abs(kg - s41["s4_1_known_kg"]) < 1e-6, "every S4.1 known kg is audited")
    check(len(rows) == 60, "60 mass-bearing footing parts")
    cons = CA.conservation(s41["s4_1_known_kg"], corr, s41["s4_1_known_kg"])
    check(cons["all_pass"], "conservation")
    single = [r for r in rows if r["LAYERING"] == "SINGLE_LAYER"]
    two = [r for r in rows if r["LAYERING"] == "TWO_LAYER"]
    s5c = sum(1 for line in open(S5 / "GROUND_SYSTEM_REBAR_PROVENANCE.jsonl", encoding="utf-8")
              if json.loads(line).get("kg"))
    s6c = sum(1 for line in open(S6 / "SUPERSTRUCTURE_BEAM_PROVENANCE.jsonl", encoding="utf-8")
              if json.loads(line).get("kg"))
    for p in (S5 / "GROUND_SYSTEM_REBAR_PROVENANCE.jsonl", S6 / "SUPERSTRUCTURE_BEAM_PROVENANCE.jsonl"):
        for line in open(p, encoding="utf-8"):
            d = json.loads(line)
            if d.get("kg"):
                f = d["provenance"].get("FORMULA", "") + json.dumps(d["provenance"].get("INPUTS", {}))
                check(not re.search(r"cover|c1|c2|- 70|- 25|2 x 70|2 x 25", f, re.I), f"{p.name}: no cover term")
    s51c, s61c = d11["s5_1"]["corrected_known_kg"], d11["s6_1"]["corrected_known_kg"]
    comb = kg + s51c + s61c
    check(abs(comb - d11["combined"]["corrected_kg"]) < 1e-6, "combined project-basis figure = D1.1 corrected")
    summary = {
        "round": ROUND, "policy": POLICY, "baseline_head": BASELINE_HEAD,
        "engine_commit": f"{frozen['S4.1']['engine_commit_stamp']}+cover:{code_digest()[:16]}", "frozen": frozen,
        "cover_policy": CA.policy_record(), "cover_basis": basis,
        "rule": {"wording": ss["rules"]["note"]["raw_text"], "english": ss["rules"]["note"]["english"],
                 "kind": "MINIMUM", "exact_in_any_footing_detail": False},
        "s4_1": {"parts_audited": len(rows), "parts_affected": len(corr),
                 "by_layering": {"SINGLE_LAYER": {"parts": len(single),
                                                  "kg": sum(r["KG_AT_MIN_COVER"] for r in single)},
                                 "TWO_LAYER": {"parts": len(two), "kg": sum(r["KG_AT_MIN_COVER"] for r in two)}},
                 "by_component": dict(sorted(Counter(f"{r['LAYERING']}:{r['COMPONENT']}" for r in rows).items())),
                 "kg_affected": kg, "quantity_change_kg": 0.0,
                 "state_change": {"from": "LOWER_BOUND", "to": CA.PROJECT_BASIS_NUMERIC, "parts": len(corr)},
                 "known_numerical_kg_at_min_cover": kg, "known_actual_as_built_kg": None,
                 "as_built_state": "NOT_ESTABLISHED (no source lower bound: the cover may exceed 70 mm; no upper "
                                   "bound: legs / hooks / end treatment and the edge bar are unquantified)",
                 "straight_segment_state": CA.SOURCE_MAXIMUM_STRAIGHT_RUN, "conservation": cons},
        "combined": {"project_drawing_basis_kg": comb, "as_built_lower_bound_known_kg": s51c + s61c,
                     "parts": {"S4.1": {"project_basis_kg": kg, "as_built_lower_bound_kg": None},
                               "S5.1": {"project_basis_kg": s51c, "as_built_lower_bound_kg": s51c},
                               "S6.1": {"project_basis_kg": s61c, "as_built_lower_bound_kg": s61c}},
                     "s5_s6_cover_independent": {"s5_components_checked": s5c, "s6_components_checked": s6c}},
        "source_search": {"dxf_texts_scanned": ss["dxf"]["texts_scanned"], "dxf_cover_hits": 0,
                          "p13_ticks_on_bar_lines": 0, "ocr_footing_cover_hits": 0},
        "flags": {"frozen_outputs_changed": False, "cover_invented": False, "actual_cover_assumed": False,
                  "plotted_scale_used": False, "silent_lower_bound": False, "pre_s7_started": False,
                  "references_read": []}}
    audit_fields = ["AUDIT_ID", "OCCURRENCE_ID", "MARK", "LAYERING", "COMPONENT", "S4_1_DELTA_ID",
                    "FOOTING_DIMENSION_MM", "DISTRIBUTION_DIMENSION_MM", "RUN_DIRECTION", "DIAMETER_MM", "COUNT_MODE",
                    "COUNT_OR_RATE", "COUNT_USED", "COUNT_WITH_EDGE_BARS", "CURRENT_COVER", "CURRENT_LENGTH_MM",
                    "SOURCE_FOR_COVER", "COVER_AUTHORITY", "ORIGINAL_STATE", "A_STRAIGHT_SEGMENT_STATE",
                    "A_STRAIGHT_SEGMENT_DIRECTION", "B_COUNT_DIRECTION", "B_COUNT_NOTE", "C_END_PORTIONS_STATE",
                    "C_END_PORTIONS", "NEW_LENGTH_STATE", "MASS_DIRECTION", "MASS_STATE", "KG_AT_MIN_COVER",
                    "AS_BUILT_KG_STATE", "NOTES"]
    _csv(HERE / "03_FOOTING_COVER_AUDIT.csv", rows, audit_fields)
    _csv(HERE / "04_S4_1A_COVER_AUTHORITY_CORRECTION.csv", corr,
         ["CORRECTION_ID", "RECORD_TYPE", "STAGE", "ORIGINAL_DELTA_ID", "COMPONENT_ID", "OCCURRENCE_ID", "MARK",
          "LAYERING", "COMPONENT", "ORIGINAL_STATE", "ORIGINAL_KG", "COVER_BASIS", "NEW_LENGTH_STATE",
          "STRAIGHT_SEGMENT_DIRECTION", "NEW_COUNT_DIRECTION", "END_PORTIONS_STATE", "NEW_MASS_STATE",
          "CORRECTION_KG", "RETAINED_NUMERIC_KG", "KG_AT_MIN_COVER", "AS_BUILT_KG_STATE", "CORRECTION_REASON",
          "SOURCE_EVIDENCE"])
    _json(HERE / "02_COVER_BASIS.json", {"round": ROUND, "basis": basis, "rules": ss["rules"],
                                         "footing_details": ss["pdf_vector"], "dxf": ss["dxf"],
                                         "outcomes_considered": ["EXACT_PROJECT_COVER_70", "MINIMUM_PROJECT_COVER_70",
                                                                 "DERIVED_EXACT_COVER", "BOUNDED_COVER", "UNRESOLVED"],
                                         "why": "the only cover rule is worded as a minimum; no footing detail binds "
                                                "a bar line to a dimensioned face; no upper bound is printed"})
    _json(HERE / "05_CORRECTED_RELEASE_SUMMARY.json", summary)
    with open(HERE / "06_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"kind": "AUDIT", **{k: r[k] for k in ("AUDIT_ID", "OCCURRENCE_ID", "COMPONENT",
                                                                        "COVER_AUTHORITY", "MASS_STATE",
                                                                        "KG_AT_MIN_COVER")},
                                "frozen_s4_1_manifest": frozen["S4.1"]["manifest_sha256"]},
                               sort_keys=True, ensure_ascii=False) + "\n")
        for c in corr:
            f.write(json.dumps({"kind": CA.RECORD_TYPE, **c, "frozen_s4_1_manifest": frozen["S4.1"]["manifest_sha256"]},
                               sort_keys=True, ensure_ascii=False) + "\n")
    (HERE / "01_SOURCE_SEARCH.md").write_text(source_md(ss), encoding="utf-8")
    (HERE / "00_README.md").write_text(README.format(
        round=ROUND, policy=POLICY, head=BASELINE_HEAD, basis=basis["label"], n_texts=ss["dxf"]["texts_scanned"],
        n=len(rows), n_single=len(single), kg_single=sum(r["KG_AT_MIN_COVER"] for r in single), n_two=len(two),
        kg_two=sum(r["KG_AT_MIN_COVER"] for r in two), kg=kg, s51=s51c, s61=s61c, comb=comb, asb=s51c + s61c,
        n_s5=s5c, n_s6=s6c), encoding="utf-8")
    manifest = {"round": ROUND, "state": "FROZEN", "frozen_baselines": frozen,
                "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
                "drawing_sha256": {"ST7757.dxf": DXF_SHA, "ST7757.pdf": PDF_SHA},
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "references_read_before_freeze": [],
                "rule": "a state-correction layer over frozen S4.1; S4 and S4.1 are never edited"}
    _json(HERE / "D1_2_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({k: summary[k] for k in ("cover_basis", "s4_1", "combined")}, indent=1, default=str)[:3500])


if __name__ == "__main__":
    main()
