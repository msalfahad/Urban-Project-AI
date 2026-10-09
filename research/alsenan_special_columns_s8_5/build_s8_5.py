"""S8.5 - special columns: turned (twisted), dead and planted columns. Source-controlled and blind (frozen before any
comparison).

    python3 -I research/alsenan_special_columns_s8_5/build_s8_5.py

Reads the registered structural DXF (ST7757: the GFRS / FFRS / SFRS plans, every sheet searched for special-column
labels) and frozen Urban stages:
- S1 registers, S2 flags and components, S3.1 column components;
- S4 / S4.1 footings, S5 ground beams, S6 / S6.1 beams;
- the PRE-S8 census, through a column whitelist (its quantity column is never bound).
p.15 of the plotted set exists only as a plot. Its two twisted-column details and the planted-column detail enter as
visual records read in session; their renders are client drawing and stay out of git.

Each of the six special-column labels is bound to one real column occurrence. Every physical bar role of the turn,
the termination and the planted support is matched against the stage that already owns it. A role is added only when
the source requires it, fixes its quantity and no stage holds it. Everything else stays blocked, with its kg as
sensitivity. No frozen quantity moves. No earlier Urban total, contractor figure or third-party figure is read.
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
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import special_column_components as SC  # noqa: E402

ROUND = "S8_5"
DATE = "2026-10-09"
BASELINE_HEAD = "9a82950"
POLICY = "S8_5_SPECIAL_COLUMNS_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
MANIFESTS = {"S4": R / "alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
             "S4.1": R / "alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
             "S5": R / "alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
             "S5.1": R / "alsenan_ground_system_rebar_s5_1/S5_1_FREEZE_MANIFEST.json",
             "S6": R / "alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
             "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json",
             "AD1": R / "ad1_authority_decisions/AD1_FREEZE_MANIFEST.json",
             "D1.1": R / "d1_1_stirrup_authority_audit/D1_1_FREEZE_MANIFEST.json",
             "D1.2": R / "d1_2_footing_cover_audit/D1_2_FREEZE_MANIFEST.json",
             "PRE-S7": R / "alsenan_slab_rebar_pre_s7/PRE_S7_FREEZE_MANIFEST.json",
             "PRE-S7.1": R / "alsenan_slab_rebar_pre_s7_1/PRE_S7_1_FREEZE_MANIFEST.json",
             "S7": R / "alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json",
             "S7A": R / "alsenan_slab_rebar_s7a_qa/11_S7A_FREEZE_MANIFEST.json",
             "PRE-S8": R / "pre_s8_structural_completeness/13_PRE_S8_FREEZE_MANIFEST.json",
             "S8.1": R / "alsenan_ground_slab_s8_1/11_S8_1_FREEZE_MANIFEST.json",
             "S8.1A": R / "alsenan_ground_slab_s8_1a/14_S8_1A_FREEZE_MANIFEST.json",
             "S8.2": R / "alsenan_swimming_pool_s8_2/18_S8_2_FREEZE_MANIFEST.json",
             "S8.2A": R / "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json",
             "S8.3": R / "alsenan_dome_ring_s8_3/16_S8_3_FREEZE_MANIFEST.json",
             "S8.3A": R / "alsenan_dome_mesh_s8_3a/09_S8_3A_FREEZE_MANIFEST.json",
             "S8.4": R / "alsenan_water_tank_s8_4/15_S8_4_FREEZE_MANIFEST.json"}
S83_ERRATA = R / "alsenan_dome_ring_s8_3/errata"
S1D = R / "alsenan_structural_census_s1"
S2D = R / "alsenan_structural_s2"
S31D = R / "alsenan_column_rebar_s3_1"
INDEXES = {"S1": (S1D / "INDEX.json", "registers"), "S2": (S2D / "INDEX.json", "outputs"),
           "S3": (R / "alsenan_column_rebar_s3/INDEX.json", "outputs"), "S3.1": (S31D / "INDEX.json", "outputs")}
READ = {"S1_SPECIAL": S1D / "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json",
        "S1_COLUMNS": S1D / "COLUMN_OCCURRENCE_REGISTER.json",
        "S1_CHAINS": S1D / "COLUMN_VERTICAL_CHAIN_REGISTER.json",
        "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
        "S1_LEVELS": S1D / "STRUCTURAL_LEVEL_REGISTER.json",
        "S1_BEAM_DEFS": S1D / "BEAM_DEFINITION_REGISTER.json",
        "S2_FLAGS": S2D / "ALSENAN_ENGINEERING_FLAGS.json",
        "S2_COMPONENTS": S2D / "ALSENAN_COMPONENT_RELEASE.json",
        "S31_RELEASE": S31D / "COLUMN_RELEASE_REGISTER.json",
        "S31_SUMMARY": S31D / "COLUMN_REBAR_S3_1_SUMMARY.json",
        "S4_COMPONENTS": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_COMPONENTS.csv",
        "S4_OCC": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_OCCURRENCES.csv",
        "S41_DELTA": R / "alsenan_footing_rebar_s4_1/S4_1_DELTA_COMPONENTS.csv",
        "S5_OCC": R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_REBAR_OCCURRENCES.csv",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S61_DELTA": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_DELTA_COMPONENTS.csv",
        "S61_SUMMARY": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_RELEASE_SUMMARY.json",
        "PRE_S8_CENSUS": R / "pre_s8_structural_completeness/02_STRUCTURAL_ELEMENT_CENSUS.csv",
        "SOURCE_MANIFEST": ROOT / "tests/alsenan/registers/SOURCE_MANIFEST.json"}
# PRE-S8 is read for its ownership claims only. Its quantity column is never bound to a name.
PRE_S8_COLUMNS = ("ELEMENT_ID", "PARENT_ELEMENT", "ELEMENT_FAMILY", "FLOOR", "EXISTING_STAGE_OWNER", "NEW_S8_OWNER",
                  "MISSING_INFORMATION")
PRE_S8_FIREWALLED = ("CONCRETE_QUANTITY_STATE",)
CODE = ["engine/source/special_column_components.py", "engine/source/rebar_unit_mass.py",
        "engine/source/delta_release.py", "research/alsenan_special_columns_s8_5/build_s8_5.py",
        "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_SOURCE_AND_ANNOTATION_REGISTER.csv", "02_SIX_OCCURRENCE_POPULATION.csv",
           "03_COLUMN_PARENT_CROSSWALK.csv", "04_TWISTED_COLUMN_REINFORCEMENT.csv",
           "05_PLANTED_COLUMN_REINFORCEMENT.csv", "06_DEAD_COLUMN_TERMINATION_AUDIT.csv", "07_CONCRETE_QTO.csv",
           "08_INCREMENTAL_REBAR_QTO.csv", "09_INTERFACE_RECONCILIATION.csv", "10_BLOCKED_COMPONENTS.csv",
           "11_SOURCE_CONFLICTS_AND_QUESTIONS.csv", "12_OWNERSHIP_DELTAS.csv", "13_SENSITIVITY_CASES.csv",
           "14_CONSERVATION_CHECKS.csv", "15_PROVENANCE.jsonl", "16_S8_5_SUMMARY.json"]
MANIFEST_NAME = "17_S8_5_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO = "SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"
BLOCKED, CONFLICT, SENS = "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "SENSITIVITY_ONLY"
NOT_IN_SOURCE, NOT_ADDED = "NOT_IN_SOURCE", "NOT_ADDED"
RELEASED_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO)
LANE_OF = {SC.ALREADY_OWNED: NOT_ADDED, SC.INCREMENTAL: PROJECT_BASIS_QTO, SC.BLOCKED: BLOCKED,
           SC.NOT_REQUIRED: NOT_IN_SOURCE}

# ------------------------------------------------------------------ the brief's starting population
START_POPULATION = ("SPC-TURN_COLUMN-GFRS-31F", "SPC-TURN_COLUMN-GFRS-324", "SPC-DEAD_COLUMN-GFRS-38A",
                    "SPC-PLANTED_COLUMN-GFRS-544", "SPC-PLANTED_COLUMN-GFRS-548", "SPC-PLANTED_COLUMN-FFRS-77C")
KIND_FAMILY = {"TURN_COLUMN": SC.TURN, "DEAD_COLUMN": SC.DEAD, "PLANTED_COLUMN": SC.PLANTED}
SHORT = {s: s.rsplit("-", 1)[1] for s in START_POPULATION}
LABEL_LAYER, COLUMN_LAYER = "S-TEXT-SLAB", "S-COL.BON"
STOREYS = ("FOUNDATION", "GF", "1F", "2F")
LEADER_REACH_MM = 300.0           # a leader starts within 1.5 text heights of its label
CIRCLE_REACH_MM = 600.0           # a T.C / D.C label sits within 3 text heights of its circle
ON_CIRCLE_MM = 5.0
BAR_TEXT_REACH_MM = 600.0
SPECIAL_WORDS = re.compile(r"TWIST|PLANT|DEAD\s*COL|TURN(?:ED)?\s*COL|SPIRAL", re.I)
OTHER_LEGEND_CODES = re.compile(r"^\s*(F\.C|C\.S|C\.A)\b")
# ------------------------------------------------------------------ what the p.15 details state (rule P15-*)
TURN_EXTRA = {"count": 4, "dia_mm": 16, "below_mm": 1000.0, "above_mm": 1000.0}
SPIRAL = {"dia_mm": 8, "per_m": 6, "zone_mm": 2000.0}
PLANTED_EXTRA = {"count": 4, "dia_mm": 16}
STARTER_PROJECTION_MM = 1000.0     # the '100' (cm) dimension: beam top to the starter crank
UNDER_COLUMN_STIRRUP_RATE = 10     # '10 10': links at 10 cm under the column
LAP_40D_MM = 640.0                 # S3.1 lap / anchorage basis for Ø16 (P8-N09, 40D)
# ------------------------------------------------------------------ visual records (read in session; renders not kept)
VISUAL = [
    {"ID": "VR-S8.5-01", "FILE": "ST7757.pdf", "PAGE": 15, "DPI": 300, "BOX_PX": [290, 130, 965, 790],
     "READ": "TYP. DETAIL OF TWISTED COLUMN, cross variant, plan: 'COLUMN IN GROUND' and 'COLUMN IN FIRST' "
             "superimposed. Eight bars inside an elliptical spiral at their overlap; a '4Ø16 EXTRA' leader touches "
             "two of them; 'Spiral Stirrups 6Ø8/m'. Both columns' rectangular ties are drawn continuous through the "
             "overlap. '25' dimensions the column in ground. The spiral is not dimensioned"},
    {"ID": "VR-S8.5-02", "FILE": "ST7757.pdf", "PAGE": 15, "DPI": 300, "BOX_PX": [1020, 130, 1930, 790],
     "READ": "TYP. DETAIL OF TWISTED COLUMN, T variant, plan: the same eight bars, spiral, '4Ø16 EXTRA' leader and "
             "'Spiral Stirrups 6Ø8/m' at the end of the column in ground"},
    {"ID": "VR-S8.5-03", "FILE": "ST7757.pdf", "PAGE": 15, "DPI": 600,
     "BOX_PX": [[400, 1700, 1500, 4600], [2300, 1700, 3400, 4600]],
     "READ": "both twisted elevations, measured on the 600 dpi render:\n"
             "- '1M' above and '1M' below the top of the column in ground; the ticks are 1181 px apart (1:20).\n"
             "- Two inner bars run tick to tick (2.0 m straight), with a short inward crank at the top and a plain "
             "bottom end.\n"
             "- The column in first's bars in the overlap start at the lower tick and continue up.\n"
             "- The column in ground's outer bars end at its top in a horizontal bend.\n"
             "- 25 horizontal lines cross the 2 m zone at about 80 mm (about 12.5 per m): consistent with 6/m ties "
             "plus 6/m spiral drawn together, not with the spiral alone. They are unlabelled except 'Spiral "
             "Stirrups 6Ø8/m'.\n"
             "- No closing turns and no hooks are drawn on the spiral. The same arrangement appears in both "
             "variants"},
    {"ID": "VR-S8.5-04", "FILE": "ST7757.pdf", "PAGE": 15, "DPI": 300, "BOX_PX": [3210, 1895, 4175, 3215],
     "READ": "BEAM CARRYING PLANTED COL. DETAIL:\n"
             "- The column bars are drawn as a U whose legs rise '100' above the beam top to an inward crank. The "
             "dimension runs from the beam top up to the crank, so it is a projection, not an embedment. A foot "
             "lies near the beam bottom.\n"
             "- '4Ø16' sits in the beam with hooked ends, 'DEPTH' past each column face.\n"
             "- An unlabelled X sits in the beam under the column. A 'STIRRUPS' leader. '10 10' spaces three "
             "links under the column.\n"
             "- The beam spans between two columns. No other bar is labelled"},
    {"ID": "VR-S8.5-05", "FILE": "ST7757.pdf", "PAGE": "13-15", "DPI": 60, "BOX_PX": None,
     "READ": "typical details: footings with column starters (p.13), lintels, ground beams, lift, boundary wall, "
             "parapets (p.14), twisted columns, beams in casement, the planted column, slab on beams and the "
             "temperature table (p.15). No dead-column or column-top termination detail, no other special-column "
             "detail"},
    {"ID": "VR-S8.5-06", "FILE": "ST7757.pdf", "PAGE": 3, "DPI": None, "BOX_PX": None,
     "READ": "plan legend (S1 P3-LEGEND): T.C turn column, D.C dead column, P.C planted column. The legend names the "
             "event, not the reinforcement"}]


class Stop(Exception):
    pass


def check(cond, msg):
    if not cond:
        raise Stop(msg)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _full(v, nd=9):
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return _full(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows, fields=None):
    fields = fields or list(rows[0])
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


def kg(length_mm, dia_mm):
    return SC.straight_kg(length_mm, dia_mm, UNIT_MASS)


# ------------------------------------------------------------------ inputs
def verify_inputs():
    dxf = BY_SHA / f"{STRUCT_SHA}.dxf"
    check(dxf.exists(), "private input ST7757.dxf not in data/inputs/by_sha256 (never committed)")
    check(_sha(dxf) == STRUCT_SHA, "drawing unchanged")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    errata = _j(R / "alsenan_dome_mesh_s8_3a/07_FROZEN_VERIFICATION.json")["s8_3_errata_sha256"]
    for name, h in errata.items():
        check(_sha(S83_ERRATA / name) == h, f"S8.3 errata {name} unchanged")
    index = {}
    for k, (p, key) in INDEXES.items():
        n = 0
        for name, v in _j(p)[key].items():
            h = v["sha256"] if isinstance(v, dict) else v
            f = p.parent / (v["file"] if isinstance(v, dict) else name)
            check(_sha(f) == h, f"{k} register {name} unchanged")
            n += 1
        index[k] = {"index_sha256": _sha(p), "registers_verified": n}
    return frozen, errata, index


def pre_s8_claims():
    """The PRE-S8 census rows of the six records, whitelisted columns only."""
    with open(READ["PRE_S8_CENSUS"], encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        head = next(rd)
        check(not set(PRE_S8_COLUMNS) & set(PRE_S8_FIREWALLED), "PRE-S8 whitelist excludes the firewalled columns")
        idx = {c: head.index(c) for c in PRE_S8_COLUMNS}
        out = {}
        for row in rd:
            eid = row[idx["ELEMENT_ID"]]
            if eid in START_POPULATION:
                out[eid] = {c: row[i] for c, i in idx.items()}
    return out


# ------------------------------------------------------------------ drawing
def _bounds_inside_circle(pts, c, r, tol=1.0):
    return all(math.dist(p, c) <= r + tol for p in pts)


def _rect_disc_distance(rect, c):
    dx = max(rect[0] - c[0], 0.0, c[0] - rect[2])
    dy = max(rect[1] - c[1], 0.0, c[1] - rect[3])
    return math.hypot(dx, dy)


def _pip_rect(pt, rect, tol=1.0):
    return rect[0] - tol <= pt[0] <= rect[2] + tol and rect[1] - tol <= pt[1] <= rect[3] + tol


def structural(src):
    E = src.entities()
    labels, words, other_codes = [], [], []
    for sh, ents in E.items():
        for e in ents:
            if e["type"] not in ("TEXT", "MTEXT"):
                continue
            t = e.get("text") or ""
            lab = SC.parse_special_label(t)
            if lab:
                labels.append({"sheet": sh, "handle": e["handle"], "text": t, "p": tuple(e["p"]),
                               "height": e.get("height"), "layer": e["layer"], **lab})
            if SPECIAL_WORDS.search(t):
                words.append((sh, e["handle"], t))
            if OTHER_LEGEND_CODES.match(t):
                other_codes.append((sh, e["handle"], t))
    circles = {sh: [e for e in ents if e["type"] == "CIRCLE" and e["layer"] == LABEL_LAYER] for sh, ents in E.items()}
    outlines = {sh: [e for e in ents if e["type"] == "LWPOLYLINE" and e["layer"] == COLUMN_LAYER and e.get("closed")]
                for sh, ents in E.items()}
    leaders = {sh: [e for e in ents if e["type"] == "LWPOLYLINE" and e["layer"] == LABEL_LAYER and not e.get("closed")]
               for sh, ents in E.items()}
    bar_texts = {sh: [e for e in ents if e["type"] == "TEXT" and SC.parse_bar_count(e.get("text"))]
                 for sh, ents in E.items()}
    out = {}
    for lab in labels:
        sh, p = lab["sheet"], lab["p"]
        rec = {"label": lab, "sheet_page": src.sheets[sh]["pdf_page"]}
        if lab["family"] == SC.PLANTED:
            hits = []
            for ld in leaders[sh]:
                pts = [tuple(q) for q in ld["pts"]]
                for near, far in ((pts[-1], pts[0]), (pts[0], pts[-1])):
                    if math.dist(near, p) > LEADER_REACH_MM:
                        continue
                    for c in circles[sh]:
                        if abs(math.dist(far, c["c"]) - c["r"]) <= ON_CIRCLE_MM:
                            hits.append((ld, c, math.dist(near, p)))
            check(len(hits) == 1, f"{lab['handle']}: one leader from the label to one circle ({len(hits)})")
            ld, circ, d = hits[0]
            rec["leader"] = {"handle": ld["handle"], "pts": [list(q) for q in ld["pts"]], "label_gap_mm": d}
            texts = sorted(((math.dist(tuple(t["p"]), p), t) for t in bar_texts[sh]
                            if math.dist(tuple(t["p"]), p) <= BAR_TEXT_REACH_MM), key=lambda x: x[0])
            check(len(texts) == 1, f"{lab['handle']}: one bar text beside the label ({len(texts)})")
            rec["bar_text"] = {"handle": texts[0][1]["handle"], "text": texts[0][1]["text"],
                               "gap_mm": texts[0][0], **SC.parse_bar_count(texts[0][1]["text"])}
        else:
            ranked = sorted(((abs(math.dist(p, c["c"]) - c["r"]), c) for c in circles[sh]), key=lambda x: x[0])
            check(ranked and ranked[0][0] <= CIRCLE_REACH_MM and (len(ranked) == 1 or ranked[1][0] >= 2 * ranked[0][0]),
                  f"{lab['handle']}: one circle beside the label")
            circ, d = ranked[0][1], ranked[0][0]
            rec["circle_gap_mm"] = d
            rec["second_circle_gap_mm"] = ranked[1][0] if len(ranked) > 1 else None
        rec["circle"] = {"handle": circ["handle"], "c": list(circ["c"]), "r": circ["r"]}
        met = [o for o in outlines[sh] if _rect_disc_distance(SC.axis_rect(o["pts"]), circ["c"]) <= circ["r"]]
        check(met, f"{lab['handle']}: the circle meets a column outline")
        rec["outlines"] = {o["handle"]: SC.axis_rect(o["pts"]) for o in sorted(met, key=lambda o: o["handle"])}
        rec["enclosed"] = sorted(o["handle"] for o in met
                                 if _bounds_inside_circle([tuple(q) for q in o["pts"]], circ["c"], circ["r"]))
        out[f"{sh}:{lab['handle']}"] = rec
    rects = {sh: {o["handle"]: SC.axis_rect(o["pts"]) for o in outlines[sh]} for sh in outlines}
    return {"labels": labels, "records": out, "words": words, "other_codes": other_codes, "rects": rects,
            "sheets": {k: v["pdf_page"] for k, v in src.sheets.items()}}


SPAN_RE = re.compile(r"^SPAN:([A-Z]+):(BL\d+):(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)$")


def beam_model(src, s6occ, sheets):
    import alsenan_structural_s1 as S1
    lines, spans = {}, defaultdict(list)
    for sh in sheets:
        segs, _arcs, _ = S1.beam_linework(src, sh)
        lines[sh] = {l["line_id"]: l for l in S1.beam_lines(S1.straight_bands(segs))}
    for o in s6occ:
        for g in json.loads(o["geometry_objects"] or "[]"):
            m = SPAN_RE.match(g)
            if m and m.group(1) in lines:
                spans[(m.group(1), m.group(2))].append((o["occurrence_id"], float(m.group(3)), float(m.group(4))))
    return lines, spans


def _angle(line):
    return math.degrees(math.atan2(line["dir"][1], line["dir"][0]))


def host_relations(sheet, centre, pts, lines, spans):
    rel = []
    for lid, l in sorted(lines[sheet].items()):
        (dx, dy), (nx, ny) = l["dir"], l["normal"]
        t, off = centre[0] * dx + centre[1] * dy, centre[0] * nx + centre[1] * ny
        if abs(off - l["offset"]) > l["width_mm"] / 2 + ON_CIRCLE_MM or not l["t0"] - 300 <= t <= l["t1"] + 300:
            continue
        ang = _angle(l)
        half = SC.extent_along(pts, ang) / 2
        for occ, a, b in sorted(spans[(sheet, lid)]):
            r = SC.span_relation(t, a, b, half, tol=1.0)
            if r != SC.OUTSIDE:
                rel.append({"occurrence_id": occ, "line_id": lid, "relation": r, "t": t, "span": [a, b],
                            "angle_deg": ang, "along_mm": 2 * half, "line_width_mm": l["width_mm"]})
    return rel


def framing_at(sheet, rect, lines, spans):
    """S6 spans with an end inside a column outline (the beams the column supports or meets)."""
    out = []
    for (sh, lid), lst in sorted(spans.items()):
        if sh != sheet:
            continue
        l = lines[sh][lid]
        (dx, dy), (nx, ny) = l["dir"], l["normal"]
        for occ, a, b in lst:
            for end, t in (("START", a), ("END", b)):
                p = (t * dx + l["offset"] * nx, t * dy + l["offset"] * ny)
                if _pip_rect(p, rect):
                    out.append({"occurrence_id": occ, "line_id": lid, "end": end, "point": [p[0], p[1]]})
    return sorted(out, key=lambda x: (x["occurrence_id"], x["end"]))


# ------------------------------------------------------------------ build
def build():
    frozen, errata, index = verify_inputs()
    import alsenan_structural_s1 as S1
    src = S1.Source()
    special = {r["special_id"]: r for r in _j(READ["S1_SPECIAL"])["rows"] if r["kind"] in KIND_FAMILY}
    check(sorted(special) == sorted(START_POPULATION), f"S1 special columns = the brief's six ({sorted(special)})")
    cols = {r["column_id"]: r for r in _j(READ["S1_COLUMNS"])["rows"]}
    chains = {r["chain_id"]: r for r in _j(READ["S1_CHAINS"])["rows"]}
    by_chain = defaultdict(dict)
    for c in cols.values():
        by_chain[c["chain_id"]][c["floor"]] = c
    rules = {r["rule_id"]: r for r in _j(READ["S1_RULES"])["rows"]}
    lv = _j(READ["S1_LEVELS"])
    iv = {i["storey"]: i for i in lv["intervals"]}
    closing = {s: iv[s].get("closing_slab_sheet") for s in STOREYS if s in iv}
    bdef = {r["source_row"]["insert_handle"]: r for r in _j(READ["S1_BEAM_DEFS"])["rows"] if r.get("source_row")}
    s2flags = {f["flag_id"]: f for f in _j(READ["S2_FLAGS"])["flags"]}
    s2comp = defaultdict(dict)
    for c in _j(READ["S2_COMPONENTS"])["components"]:
        s2comp[c["element_id"]][c["component"]] = c
    s31 = _j(READ["S31_RELEASE"])
    s31rows = defaultdict(dict)
    for r in s31["rows"]:
        s31rows[r["occurrence_id"]][r["part_id"].split("|", 1)[1]] = r
    s31_headline = _j(READ["S31_SUMMARY"])["headline"]
    s4c = _rows(READ["S4_COMPONENTS"])
    s4o = _rows(READ["S4_OCC"])
    s41 = _rows(READ["S41_DELTA"])
    s5o = _rows(READ["S5_OCC"])
    s6o = {r["occurrence_id"]: r for r in _rows(READ["S6_OCC"])}
    s61 = _rows(READ["S61_DELTA"])
    s61sum = _j(READ["S61_SUMMARY"])
    pre = pre_s8_claims()
    check(sorted(pre) == sorted(START_POPULATION), "PRE-S8 census names the same six records")
    st = structural(src)
    lines, spans = beam_model(src, list(s6o.values()), ("GFRS", "FFRS"))

    # ------------------------------------------------------------ population: label -> circle / leader -> outline
    check(len(st["labels"]) == 6 and not st["words"], f"six special-column labels on all sheets, no other special "
                                                      f"word ({len(st['labels'])}, {st['words']})")
    pop, xwalk, members = [], [], {}
    for sid in START_POPULATION:
        sp = special[sid]
        sh, h = sp["source_id"].split(":")[1:]
        rec = st["records"].get(f"{sh}:{h}")
        check(rec is not None, f"{sid}: label {sh}:{h} found")
        fam = KIND_FAMILY[sp["kind"]]
        check(rec["label"]["family"] == fam and rec["label"]["text"] == sp["label"], f"{sid}: label text and family")
        ch = chains[sp["bound_chain"]]
        check(ch["members_by_sheet"].get(sh) in rec["enclosed"], f"{sid}: the circle encloses the chain's {sh} outline")
        segs = {fl: by_chain[ch["chain_id"]][fl] for fl in STOREYS if fl in by_chain[ch["chain_id"]]}
        centre = tuple(rec["circle"]["c"])
        m = {"special_id": sid, "family": fam, "sheet": sh, "page": rec["sheet_page"], "chain": ch, "segs": segs,
             "rec": rec, "centre": centre}
        if fam == SC.TURN:
            lower = segs["GF"]
            upper = segs["1F"]
            check(ch["turn"] and ch["turn"]["sheet"] == sh, f"{sid}: S1 records the turn on {sh}")
            lo_h, up_h = ch["turn"]["lower_outline"].split(":")[1], ch["turn"]["upper_outline"].split(":")[1]
            check(set(rec["outlines"]) == {lo_h, up_h} and lo_h in rec["enclosed"],
                  f"{sid}: the circle encloses the lower outline and meets the turned upper one, nothing else "
                  f"({rec['outlines']}, enclosed {rec['enclosed']})")
            up_sheet_h = upper["plan_source"]["handles"][0]
            check(st["rects"]["FFRS"][up_sheet_h] == rec["outlines"][up_h], f"{sid}: the turned outline on {sh} is the "
                                                                             f"1F column on FFRS")
            ov = SC.rect_intersection(rec["outlines"][lo_h], rec["outlines"][up_h])
            check(ov is not None, f"{sid}: the two sections overlap")
            m.update(event="TURN_ORIENTATION_CHANGE", event_sheet=sh, event_ffl=iv["GF"]["upper_ffl_m"],
                     owners=[lower["column_id"], upper["column_id"]], storeys=["GF", "1F"],
                     overlap_mm=(ov[2] - ov[0], ov[3] - ov[1]), lower=lower, upper=upper,
                     outline_handles=[lo_h, up_h, up_sheet_h])
        elif fam == SC.DEAD:
            top = segs["GF"]
            check(not top["continues_above"] and ch["terminates_at"] == "GF", f"{sid}: the chain ends at GF")
            above = [k for k, r in st["rects"]["FFRS"].items() if _pip_rect(centre, r, tol=0.0)]
            check(not above, f"{sid}: no column outline above on FFRS ({above})")
            m.update(event="TERMINATION", event_sheet=sh, event_ffl=iv["GF"]["upper_ffl_m"], owners=[top["column_id"]],
                     storeys=["GF"], top=top, outline_handles=[ch["members_by_sheet"][sh]], above_on_ffrs=above)
        else:
            pc = list(segs.values())
            check(len(pc) == 1, f"{sid}: one planted occurrence")
            pc = pc[0]
            storey = SC.planted_storey(sh, STOREYS, closing)
            check(storey == pc["floor"], f"{sid}: planted on {sh} -> storey {storey} = S1 {pc['floor']}")
            lab_sec = rec["label"]["section_cm"]
            slab_h = ch["members_by_sheet"][sh]
            up_sheet = pc["plan_source"]["sheets"][0]
            up_h = pc["plan_source"]["handles"][0]
            check(st["rects"][up_sheet][up_h] == rec["outlines"][slab_h], f"{sid}: the outline on {sh} is the column "
                                                                          f"on {up_sheet}")
            r_ = rec["outlines"][slab_h]
            drawn = sorted((round((r_[2] - r_[0]) / 10, 1), round((r_[3] - r_[1]) / 10, 1)))
            pts = [(r_[0], r_[1]), (r_[2], r_[1]), (r_[2], r_[3]), (r_[0], r_[3])]
            rel = host_relations(sh, centre, pts, lines, spans)
            host = SC.resolve_host([(x["occurrence_id"], x["relation"]) for x in rel])
            bt = rec["bar_text"]
            check((bt["count"], bt["dia_mm"]) == (pc["longitudinal_bars"]["count"], pc["longitudinal_bars"]["dia_mm"])
                  and bt["handle"] == pc["longitudinal_bars"]["text_handle"], f"{sid}: bar text = S1 bars")
            m.update(event="PLANTED_START", event_sheet=sh, event_ffl=iv[storey]["lower_ffl_m"],
                     top_ffl=iv[storey]["upper_ffl_m"], owners=[pc["column_id"]], storeys=[storey], pc=pc,
                     label_section_cm=list(lab_sec), drawn_section_cm=drawn, pts=pts, rel=rel, host=host,
                     outline_handles=[slab_h, up_h], up_sheet=up_sheet)
        members[sid] = m

    # ------------------------------------------------------------ helpers over frozen stages
    def s31_of(occ):
        check(occ in s31rows, f"S3.1 owns {occ}")
        return s31rows[occ]

    def ids(occ, parts):
        return [f"S3.1:{occ}|{p}" for p in parts]

    def s31_kg(occ, parts, released_only=True):
        rows_ = s31_of(occ)
        return math.fsum(rows_[p]["kg"] or 0.0 for p in parts
                         if not released_only or rows_[p]["release_state"] in SC.OWNED_STATES)

    def s31_state(occ, parts):
        st_ = sorted({s31_of(occ)[p]["release_state"] for p in parts})
        return st_[0] if len(st_) == 1 else "+".join(st_)

    def tie_parts(occ):
        return sorted(p for p in s31_of(occ) if p.startswith("TIE_") or p.startswith("HOOK_"))

    def beam_def(occ):
        o = s6o[occ]
        d = bdef.get(o["schedule_row"])
        base = {"mark": o["mark"] or "UNTAGGED", "s6_state": o["occurrence_state"],
                "s6_known_kg": float(o["known_kg"] or 0.0), "width_match": o["width_match_state"] or "NO_SCHEDULE",
                "subfamily": o["subfamily"]}
        if d is None:                       # an untagged S6 span: no schedule row, so no depth and no link rate
            return {**base, "B_mm": None, "H_mm": None, "stirrups_per_m": None, "stirrup_dia_mm": None}
        sti = d["fields"]["stirrups_per_m"]
        return {**base, "B_mm": d["B_cm"] * 10, "H_mm": d["H_cm"] * 10, "stirrups_per_m": sti["count"],
                "stirrup_dia_mm": sti["dia_mm"]}

    def tagged(occ):
        return beam_def(occ)["H_mm"] is not None

    s61_by_occ = defaultdict(list)
    for r in s61:
        s61_by_occ[r["OCCURRENCE_ID"]].append(r)
    cited = defaultdict(list)            # frozen component id -> S8.5 rows citing it
    comps, blocked, sens = [], [], []

    def C(table, cid, sid, col, role, kind, dia, count, stated, drawn, existing, ex_state, ex_kg, authority,
          required, established, new_owner, s85_kg=None, check_=None, question="", sens_ids=(), why="", key=None):
        decision = SC.decide(required, ex_state if existing else None, established)
        row = {"TABLE": table, "COMPONENT_ID": cid, "SPECIAL_ID": sid, "COLUMN_ID": col, "PHYSICAL_BAR_ROLE": role,
               "KIND": kind, "DIA_MM": dia, "COUNT": count, "STATED": stated, "DRAWN": drawn,
               "EXISTING_OWNER": existing or [], "EXISTING_STATE": ex_state or "", "EXISTING_KG": _r(ex_kg),
               "NEW_EXTRA_OWNER": new_owner, "SOURCE_AUTHORITY": authority, "DECISION": decision,
               "QUANTITY_STATE": LANE_OF[decision], "S8_5_KG": _r(s85_kg) if decision == SC.INCREMENTAL else
               (0.0 if decision in (SC.ALREADY_OWNED, SC.NOT_REQUIRED) else None),
               "CHECK": check_ or "", "BLOCKED_ID": f"BL-{cid}" if decision == SC.BLOCKED else "",
               "QUESTION": question, "SENSITIVITY_IDS": list(sens_ids), "WHY": why,
               "PHYSICAL_ROLE_KEY": key or f"{col}|{role}"}
        comps.append(row)
        for e in existing or []:
            cited[e].append(cid)
        if decision == SC.BLOCKED:
            blocked.append({"BLOCKED_ID": row["BLOCKED_ID"], "COMPONENT_ID": cid, "SPECIAL_ID": sid, "COLUMN_ID": col,
                            "PHYSICAL_BAR_ROLE": role, "DIA_MM": dia, "STATE": BLOCKED, "WHY": why,
                            "EXISTING_OWNER": existing or [], "EXISTING_STATE": ex_state or "",
                            "CUSTODY": new_owner, "QUESTION": question, "SENSITIVITY_IDS": list(sens_ids)})
        return row

    def S(case, sid, role, case_text, kg_, basis, kind="kg", lo=None, hi=None):
        sens.append({"CASE_ID": case, "SPECIAL_ID": sid, "ROLE": role, "LANE": SENS, "CASE": case_text,
                     "KG": _r(kg_) if kind == "kg" else None, "KG_LOW": _r(lo), "KG_HIGH": _r(hi),
                     "COUNT_DELTA": _r(kg_) if kind == "count" else None, "BASIS": basis, "RELEASED": False})

    kg16 = UM.kg_per_m(16, UNIT_MASS)
    cover = rules["P8-N22"]["values"]["member_mm"]
    # ------------------------------------------------------------ twisted (turned) columns
    for sid in START_POPULATION[:2]:
        m = members[sid]
        k = SHORT[sid]
        lo, up = m["lower"]["column_id"], m["upper"]["column_id"]
        r_lo, r_up = s31_of(lo), s31_of(up)
        nb_lo, nb_up = m["lower"]["longitudinal_bars"]["count"], m["upper"]["longitudinal_bars"]["count"]
        T = "04"
        auth = ["P15-TWISTED", "VR-S8.5-01", "VR-S8.5-02", "VR-S8.5-03"]
        C(T, f"TC-{k}-01", sid, lo, "ORDINARY_LONGITUDINAL_BELOW_TURN", "ORDINARY", 16, nb_lo,
          f"{nb_lo}Ø16 (S1 schedule)", "column in ground bars", ids(lo, ["MAIN_CORE"]),
          s31_state(lo, ["MAIN_CORE"]), s31_kg(lo, ["MAIN_CORE"]), ["S1 schedule", "S3.1"], True, True, "S3.1",
          why="the ordinary GF bars over the storey; the turn label adds no second column")
        C(T, f"TC-{k}-02", sid, up, "ORDINARY_LONGITUDINAL_ABOVE_TURN", "ORDINARY", 16, nb_up,
          f"{nb_up}Ø16 (S1 schedule)", "column in first bars", ids(up, ["MAIN_CORE"]),
          s31_state(up, ["MAIN_CORE"]), s31_kg(up, ["MAIN_CORE"]), ["S1 schedule", "S3.1"], True, True, "S3.1",
          why="the ordinary 1F bars over the storey")
        cont = [p for p in ("LAP_TOP", "ANCHORAGE_TOP_STOPPED") if p in r_lo]
        C(T, f"TC-{k}-03", sid, lo, "CONTINUITY_AT_TURN", "ORDINARY", 16, nb_lo,
          "P8-N09 40D lap (S3.1 basis)", "upper bars start 1M below; lower bars end in a top bend (VR-S8.5-03)",
          ids(lo, cont), s31_state(lo, cont), s31_kg(lo, cont), ["P8-N09", "S3.1", "VR-S8.5-03"], True, True, "S3.1",
          sens_ids=[f"SA-{k}-CONT"], question="Q-03",
          why="S3.1 owns the bar continuity at the GF roof (40D lap"
              + (", plus the stopped bars' anchorage" if "ANCHORAGE_TOP_STOPPED" in cont else "")
              + "). The twisted detail draws the upper bars starting 1 m below instead; that reading is sensitivity")
        C(T, f"TC-{k}-04", sid, lo, "SECTION_TRANSITION_BENDS", "SPECIAL", 16, None,
          "not dimensioned", "lower bars' top bend; upper bars' lower ends", ids(lo, ["SECTION_TRANSITION"]),
          s31_state(lo, ["SECTION_TRANSITION"]), None, ["S3.1 STR-COL-024", "VR-S8.5-03"], True, False,
          "S3.1 (ordinary continuity)",
          question="Q-03", why="the bends are drawn, never dimensioned; S3.1 holds the transition blocked")
        straight = TURN_EXTRA["count"] * (TURN_EXTRA["below_mm"] + TURN_EXTRA["above_mm"])
        ex = r_lo["EXTRA:TURN_EXTRA_BARS"]
        mine = kg(straight, TURN_EXTRA["dia_mm"])
        C(T, f"TC-{k}-05", sid, lo, "EXTRA_LONGITUDINAL_STRAIGHT", "SPECIAL", 16, TURN_EXTRA["count"],
          "4Ø16 EXTRA; 1M above / 1M below", "two inner bars tick to tick in elevation; a leader to two of the eight "
                                             "bars in plan", ids(lo, ["EXTRA:TURN_EXTRA_BARS"]), ex["release_state"],
          ex["kg"], auth, True, True, "S3.1",
          check_=f"4 x (1000 + 1000) mm x 16^2/162 = {_full(mine, 6)} kg; S3.1 {ex['kg']} kg "
                 f"({'equal' if abs(mine - ex['kg']) < 5e-4 else 'DIFFERENT'})",
          question="Q-02", why="the extra bars are already S3.1's; S8.5 verifies the basis and adds nothing")
        C(T, f"TC-{k}-06", sid, lo, "EXTRA_BAR_TOP_CRANK", "SPECIAL", 16, TURN_EXTRA["count"], "not stated",
          "a short inward crank at the top of each extra bar", [], None, None, ["VR-S8.5-03"], True, False, "S8.5",
          question="Q-02", why="drawn, not dimensioned; no hook, turn or development length is invented")
        C(T, f"TC-{k}-07", sid, lo, "EXTRA_BAR_BOTTOM_END", "SPECIAL", 16, TURN_EXTRA["count"], "not stated",
          "plain straight end at the lower tick", [], None, None, ["VR-S8.5-03"], False, False, "none",
          why="no hook or bend is drawn at the bottom end")
        C(T, f"TC-{k}-08", sid, lo, "ORDINARY_TIES_BELOW_TURN", "ORDINARY", 8, None, "P9 ST. OF COLUMN- 6Ø8/m",
          "column in ground ties drawn through the overlap", ids(lo, tie_parts(lo)), s31_state(lo, tie_parts(lo)),
          s31_kg(lo, tie_parts(lo)), ["P9-COL-TIES", "S3.1", "VR-S8.5-01"], True, True, "S3.1",
          why="S3.1 counts the GF ties over the whole storey, the 1 m zone below the turn included")
        C(T, f"TC-{k}-09", sid, up, "ORDINARY_TIES_ABOVE_TURN", "ORDINARY", 8, None, "P9 ST. OF COLUMN- 6Ø8/m",
          "column in first ties drawn through the overlap", ids(up, tie_parts(up)), s31_state(up, tie_parts(up)),
          s31_kg(up, tie_parts(up)), ["P9-COL-TIES", "S3.1", "VR-S8.5-01"], True, True, "S3.1",
          why="S3.1 counts the 1F ties over the whole storey, the 1 m zone above the turn included")
        sp_ = r_lo["EXTRA:TURN_SPIRAL"]
        ov = m["overlap_mm"]
        C(T, f"TC-{k}-10", sid, lo, "SPIRAL", "SPECIAL", SPIRAL["dia_mm"], None,
          "Spiral Stirrups 6Ø8/m over 1M above + 1M below", f"an ellipse inside the {ov[0]:g} x {ov[1]:g} mm overlap; "
                                                           "no diameter, no closing turns",
          ids(lo, ["EXTRA:TURN_SPIRAL"]), sp_["release_state"], None, auth, True, False, "S8.5 (custody)",
          question="Q-01", sens_ids=[f"SA-{k}-SPI-C", f"SA-{k}-SPI-E"],
          why="the rate and zone are stated but the spiral's diameter is not, so its helix length is unknown; its "
              "role against the ordinary ties is drawn (both shown), not stated")
        C(T, f"TC-{k}-11", sid, up, "UPPER_TOP_ANCHORAGE", "ORDINARY", 16, nb_up, "P8-N09 40D (S3.1 basis)",
          "", ids(up, ["ANCHORAGE_TOP"]), s31_state(up, ["ANCHORAGE_TOP"]), s31_kg(up, ["ANCHORAGE_TOP"]),
          ["S3.1"], True, True, "S3.1", why="the 1F column's own top end at the 1F roof; not part of the turn")
        # sensitivity
        turns = SC.turns_over(SPIRAL["zone_mm"], SPIRAL["per_m"])
        pitch = SC.pitch_from_rate(SPIRAL["per_m"])
        w, h = SC.inscribed_centreline(ov[0], ov[1], cover, SPIRAL["dia_mm"])
        circ = SC.helix_length(math.pi * min(w, h), pitch, turns)
        ell = SC.helix_length(SC.ellipse_perimeter(w / 2, h / 2), pitch, turns)
        S(f"SA-{k}-SPI-C", sid, "SPIRAL", f"circular spiral of the largest centreline diameter that fits the "
                                          f"{ov[0]:g} mm side ({min(w, h):g} mm), {turns:g} turns at {_full(pitch, 3)} mm",
          kg(circ, SPIRAL["dia_mm"]), f"{turns:g} x sqrt((pi x {min(w, h):g})^2 + {_full(pitch, 3)}^2) = "
                                      f"{_full(circ, 3)} mm x 8^2/162; an UPPER bound, cover {cover} mm (P8-N22)")
        S(f"SA-{k}-SPI-E", sid, "SPIRAL", f"elliptical spiral of the largest centreline that fits the overlap "
                                          f"({w:g} x {h:g} mm), {turns:g} turns", kg(ell, SPIRAL["dia_mm"]),
          f"{turns:g} x sqrt(P^2 + p^2), P = Ramanujan({w / 2:g}, {h / 2:g}) = "
          f"{_full(SC.ellipse_perimeter(w / 2, h / 2), 3)} mm; an UPPER bound")
        d = STARTER_PROJECTION_MM - LAP_40D_MM
        inside = 8 - TURN_EXTRA["count"]
        S(f"SA-{k}-CONT", sid, "CONTINUITY_AT_TURN", f"the upper bars embedded the full 1 m below the turn instead of a "
                                                     f"40D lap: + {d:g} mm per bar, {inside} bars (those drawn inside "
                                                     f"the spiral) to {nb_up} bars (every upper bar)",
          None, f"{d:g} mm x 16^2/162 = {_full(kg(d, 16), 6)} kg per bar", lo=kg(d * inside, 16), hi=kg(d * nb_up, 16))

    # ------------------------------------------------------------ dead column
    sid = START_POPULATION[2]
    m = members[sid]
    top = m["top"]["column_id"]
    T = "06"
    nb = m["top"]["longitudinal_bars"]["count"]
    C(T, "DC-01", sid, top, "ORDINARY_LONGITUDINAL", "ORDINARY", 16, nb, f"{nb}Ø16 (S1 schedule)", "",
      ids(top, ["MAIN_CORE"]), s31_state(top, ["MAIN_CORE"]), s31_kg(top, ["MAIN_CORE"]), ["S1 schedule", "S3.1"],
      True, True, "S3.1", why="the ordinary GF bars; the column stops at the GF roof")
    C(T, "DC-02", sid, top, "TOP_TERMINATION_STRAIGHT", "ORDINARY", 16, nb, "P8-N09 40D (S3.1 basis)",
      "no termination drawn", ids(top, ["ANCHORAGE_TOP"]), s31_state(top, ["ANCHORAGE_TOP"]),
      s31_kg(top, ["ANCHORAGE_TOP"]), ["P8-N09", "S3.1"], True, True, "S3.1",
      why="S3.1 owns a straight 40D anchorage of every bar into the roof members above")
    C(T, "DC-03", sid, top, "TOP_TERMINATION_BENDS_AND_HOOKS", "SPECIAL", 16, nb, "not stated",
      "no termination detail on any sheet (VR-S8.5-05)", [], None, None, ["P3-LEGEND", "VR-S8.5-05"], True, False,
      "S8.5 (custody)", question="Q-07", why="a dead column's bars must end in the members above, but no bend, hook "
                                              "or length is drawn; none is manufactured")
    C(T, "DC-04", sid, top, "SPECIAL_END_REINFORCEMENT", "SPECIAL", None, None, "not stated",
      "nothing drawn or scheduled", [], None, None, ["P3-LEGEND", "VR-S8.5-05"], None, False, "S8.5 (custody)",
      question="Q-07", why="no cap, extra bar or link is drawn at the end of the dead column; it is not established "
                           "whether one is required")
    tp = tie_parts(top)
    C(T, "DC-05", sid, top, "ORDINARY_TIES", "ORDINARY", 8, None, "P9 ST. OF COLUMN- 6Ø8/m", "", ids(top, tp),
      s31_state(top, tp), s31_kg(top, tp), ["P9-COL-TIES", "S3.1"], True, True, "S3.1",
      why="S3.1 counts the ties over the GF storey")
    C(T, "DC-06", sid, top, "CONTINUATION_ABOVE", "ORDINARY", 16, None, "D.C (legend)",
      "no column outline above on FFRS", [], None, None, ["P3-LEGEND", "S1 chain"], False, False, "none",
      why="the chain ends at GF and no 1F outline sits over it")

    # ------------------------------------------------------------ planted columns
    T = "05"
    for sid in START_POPULATION[3:]:
        m = members[sid]
        k = SHORT[sid]
        pc = m["pc"]["column_id"]
        nb = m["pc"]["longitudinal_bars"]["count"]
        host = m["host"]
        auth = ["P15-PLANTED", "VR-S8.5-04", "S2 STR-PLA-001"]
        C(T, f"PC-{k}-01", sid, pc, "COLUMN_LONGITUDINAL", "ORDINARY", 16, nb,
          f"{m['rec']['bar_text']['text']} (plan text {m['rec']['bar_text']['handle']})", "", ids(pc, ["MAIN_CORE"]),
          s31_state(pc, ["MAIN_CORE"]), s31_kg(pc, ["MAIN_CORE"]), ["S1", "S3.1"], True, True, "S3.1",
          why=f"the planted column's own bars over its storey ({m['storeys'][0]}); the label, the supporting-beam "
              "detail and the plan show the same bars once")
        C(T, f"PC-{k}-02", sid, pc, "COLUMN_BASE_ANCHORAGE", "ORDINARY", 16, nb, "P8-N09 40D (S3.1 basis)",
          "bars drawn into the beam with a foot", ids(pc, ["ANCHORAGE_BASE"]), s31_state(pc, ["ANCHORAGE_BASE"]),
          s31_kg(pc, ["ANCHORAGE_BASE"]), ["P8-N09", "S3.1 STR-PLA-001"], True, True, "S3.1",
          why="S3.1 owns a straight 40D anchorage of each bar into the supporting member")
        C(T, f"PC-{k}-03", sid, pc, "COLUMN_TOP_ANCHORAGE", "ORDINARY", 16, nb, "P8-N09 40D (S3.1 basis)", "",
          ids(pc, ["ANCHORAGE_TOP"]), s31_state(pc, ["ANCHORAGE_TOP"]), s31_kg(pc, ["ANCHORAGE_TOP"]), ["S3.1"], True,
          True, "S3.1", why="the column's top end at its roof slab")
        tp = tie_parts(pc)
        C(T, f"PC-{k}-04", sid, pc, "COLUMN_TIES", "ORDINARY", 8, None, "P9 ST. OF COLUMN- 6Ø8/m", "", ids(pc, tp),
          s31_state(pc, tp), s31_kg(pc, tp), ["P9-COL-TIES", "S3.1"], True, True, "S3.1",
          why="S3.1 counts the ties over the column's storey")
        C(T, f"PC-{k}-05", sid, pc, "STARTER_PROJECTION_ABOVE_BEAM", "SPECIAL", 16, None, "'100' above the beam top",
          "a U-bar, legs to an inward crank 1.00 m above the beam", [], None, None, auth, None, False, "S8.5 (custody)",
          question="Q-06", sens_ids=[f"SA-{k}-STARTER"],
          why="it is not stated whether the drawn bars are separate starters lapping the column bars or the column "
              "bars themselves, nor how many there are")
        C(T, f"PC-{k}-06", sid, pc, "STARTER_LEG_AND_FOOT_IN_BEAM", "SPECIAL", 16, None, "not dimensioned",
          "legs down to a foot near the beam bottom", [], None, None, auth, None, False, "S8.5 (custody)",
          question="Q-06", why="the in-beam leg and the foot are drawn, not dimensioned; S3.1's 40D base anchorage "
                               "already stands for the bars' embedment")
        C(T, f"PC-{k}-07", sid, pc, "STARTER_TOP_CRANK", "SPECIAL", 16, None, "not dimensioned",
          "inward crank at the top of each leg", [], None, None, auth, None, False, "S8.5 (custody)", question="Q-06",
          why="drawn, not dimensioned")
        if host["state"] == SC.RESOLVED:
            hb = beam_def(host["host"])
            hrel = next(x for x in m["rel"] if x["occurrence_id"] == host["host"])
            d1324 = [r for r in s61_by_occ[host["host"]] if r["COMPONENT"] == "OTHER_EXPLICIT_EXTRA" and
                     r["PORTION"] == "STRAIGHT_PROJECTION"]
            check(len(d1324) == 1, f"{sid}: S6.1 holds the planted-column extra on {host['host']}")
            d = d1324[0]
            facets = json.loads(d["FACETS"])
            check(abs(facets["DEPTH_MM"] - hb["H_mm"]) < 1e-9, f"{sid}: S6.1 DEPTH = {hb['mark']} schedule depth")
            proj = SC.beam_extra_projection_mm(PLANTED_EXTRA["count"], facets["DEPTH_MM"],
                                               facets["COLUMN_WIDTH_LB_MM"])
            mine = kg(proj, PLANTED_EXTRA["dia_mm"])
            exact = SC.beam_extra_projection_mm(PLANTED_EXTRA["count"], hb["H_mm"], hrel["along_mm"])
            C(T, f"PC-{k}-08", sid, host["host"], "BEAM_EXTRA_4D16_PROJECTION", "SPECIAL", 16, PLANTED_EXTRA["count"],
              "4Ø16, DEPTH past each column face", "in the beam under the column, hooked ends",
              [f"S6.1:{d['DELTA_ID']}"], d["NEW_RELEASE_STATE"], float(d["NEW_KNOWN_QUANTITY"]), auth, True, True,
              "S6.1", check_=f"S6.1 basis 4 x (2 x {facets['DEPTH_MM']:g} + {facets['COLUMN_WIDTH_LB_MM']:g}) mm x "
                             f"16^2/162 = {_full(mine, 6)} kg; S6.1 {d['NEW_KNOWN_QUANTITY']} kg "
                             f"({'equal' if abs(mine - float(d['NEW_KNOWN_QUANTITY'])) < 1e-6 else 'DIFFERENT'}); the "
                             f"drawn footprint spans {_full(hrel['along_mm'], 1)} mm along {hb['mark']} "
                             f"({_full(hrel['angle_deg'], 2)} deg): SA-{k}-EXTRA-{SHORT_MARK(hb['mark'])}",
              sens_ids=[f"SA-{k}-EXTRA-{SHORT_MARK(hb['mark'])}"], key=f"{host['host']}|BEAM_EXTRA_4D16_PROJECTION",
              why=f"the column sits inside {hb['mark']}'s clear span; S6.1 already released the projection")
            S(f"SA-{k}-EXTRA-{SHORT_MARK(hb['mark'])}", sid, "BEAM_EXTRA_4D16_PROJECTION",
              f"the drawn footprint's length along {hb['mark']} ({_full(hrel['along_mm'], 1)} mm at "
              f"{_full(hrel['angle_deg'], 2)} deg) instead of S6.1's 200 mm column width (its stated lower bound); "
              "the role stays S6.1's", kg(exact, 16),
              f"4 x (2 x {hb['H_mm']:g} + {_full(hrel['along_mm'], 1)}) = {_full(exact, 1)} mm x 16^2/162; "
              f"+{_full(kg(exact, 16) - mine, 6)} kg over S6.1")
            por = [r for r in s61_by_occ[host["host"]] if r["COMPONENT"] == "OTHER_EXPLICIT_EXTRA" and
                   r["PORTION"] in ("CRANK_DIAGONAL_EXCESS", "END_HOOK_1", "END_HOOK_2")]
            C(T, f"PC-{k}-09", sid, host["host"], "BEAM_EXTRA_CRANK_HOOKS_AND_X", "SPECIAL", 16,
              PLANTED_EXTRA["count"], "not dimensioned", "hooked ends; an unlabelled X under the column",
              [f"S6.1:{r['DELTA_ID']}" for r in por], "BLOCKED", None, auth + ["S6.1"], True, False, "S6.1",
              question="Q-08", key=f"{host['host']}|BEAM_EXTRA_CRANK_HOOKS_AND_X",
              why="S6.1 holds the crank excess and both hooks blocked (it reads the X as the cranked bars' "
                  "diagonals)")
            stir = [r for r in s61_by_occ[host["host"]] if r["COMPONENT"] in ("STIRRUP_COUNT", "STIRRUP_CORE_PATH")]
            C(T, f"PC-{k}-10", sid, host["host"], "BEAM_STIRRUPS_UNDER_COLUMN", "SPECIAL", hb["stirrup_dia_mm"], None,
              "'10 10' (links at 10 cm under the column)", f"{hb['mark']} schedule {hb['stirrups_per_m']}/m",
              [], None, None, auth + ["S1 schedule"], hb["stirrups_per_m"] < UNDER_COLUMN_STIRRUP_RATE, True, "none",
              key=f"{host['host']}|BEAM_STIRRUPS_UNDER_COLUMN",
              why=f"{hb['mark']}'s own links are already {hb['stirrups_per_m']}/m (10 cm), counted by S6.1 "
                  f"({', '.join(r['DELTA_ID'] for r in stir)}): no extra link")
            sched = [r for r in s61_by_occ[host["host"]] if r["COMPONENT"] in ("TOP_MAIN", "BOTTOM_MAIN") and
                     r["PORTION"] == "STRAIGHT_RUN"]
            C(T, f"PC-{k}-11", sid, host["host"], "SUPPORTING_BEAM_SCHEDULE_BARS", "ORDINARY", None, None,
              f"{hb['mark']} schedule", "", [f"S6.1:{r['DELTA_ID']}" for r in sched],
              s31_state_join([r["NEW_RELEASE_STATE"] for r in sched]),
              math.fsum(float(r["NEW_KNOWN_QUANTITY"]) for r in sched), ["S6 / S6.1"], True, True, "S6.1",
              key=f"{host['host']}|SUPPORTING_BEAM_SCHEDULE_BARS",
              why="the carrying beam's own bars; the planted-column detail changes none of them")
        else:
            cands = sorted({x["occurrence_id"] for x in m["rel"]})
            hk = f"{sid}|HOST_UNRESOLVED"
            na = {occ: [r for r in s61_by_occ[occ] if r["COMPONENT"] == "OTHER_EXPLICIT_EXTRA"] for occ in cands}
            na_state = sorted({r["NEW_RELEASE_STATE"] for v in na.values() for r in v})
            C(T, f"PC-{k}-08", sid, hk, "BEAM_EXTRA_4D16_PROJECTION", "SPECIAL", 16, PLANTED_EXTRA["count"],
              "4Ø16, DEPTH past each column face", "the column sits on a beam-on-beam node",
              [], None, None, auth + ["S6.1 " + "/".join(na_state)], True, False, "S8.5 (custody)",
              question="Q-04" if k == "544" else "Q-05", sens_ids=[f"SA-{k}-EXTRA-{SHORT_MARK(s6o[c]['mark'])}"
                                                                    for c in cands if tagged(c)],
              key=f"{hk}|BEAM_EXTRA_4D16_PROJECTION",
              why=f"no beam carries the column inside its clear span: {', '.join(cands)} all end or start under it "
                  f"(host {host['state']}). S6.1 marks the planted-column extra {'/'.join(na_state)} on each, so no "
                  "stage owns it, and DEPTH and direction depend on the beam")
            C(T, f"PC-{k}-09", sid, hk, "BEAM_EXTRA_CRANK_HOOKS_AND_X", "SPECIAL", 16, PLANTED_EXTRA["count"],
              "not dimensioned", "hooked ends; an unlabelled X under the column", [], None, None, auth, True, False,
              "S8.5 (custody)", question="Q-08", key=f"{hk}|BEAM_EXTRA_CRANK_HOOKS_AND_X",
              why="the host is unresolved and the bends are not dimensioned")
            C(T, f"PC-{k}-10", sid, hk, "BEAM_STIRRUPS_UNDER_COLUMN", "SPECIAL", 8, None,
              "'10 10' (links at 10 cm under the column)",
              ", ".join(f"{beam_def(c)['mark']} {beam_def(c)['stirrups_per_m']}/m" if tagged(c) else
                        f"{c} (untagged, no schedule)" for c in cands), [], None, None,
              auth + ["S1 schedule"], None, False, "S8.5 (custody)", question="Q-04" if k == "544" else "Q-05",
              sens_ids=[f"SA-{k}-LINKS"], key=f"{hk}|BEAM_STIRRUPS_UNDER_COLUMN",
              why="extra links exist only if the host's own rate is below 10/m, and the host is unresolved")
            C(T, f"PC-{k}-11", sid, hk, "SUPPORTING_BEAM_SCHEDULE_BARS", "ORDINARY", None, None,
              "candidate host schedules", "", [f"S6:{c}" for c in cands],
              s31_state_join([beam_def(c)["s6_state"] for c in cands]),
              math.fsum(beam_def(c)["s6_known_kg"] for c in cands), ["S6"], True, True, "S6",
              key=f"{hk}|SUPPORTING_BEAM_SCHEDULE_BARS",
              why="each candidate beam keeps its own S6 bars; nothing moves")
            for c in [c for c in cands if tagged(c)]:
                hb = beam_def(c)
                x = next(x for x in m["rel"] if x["occurrence_id"] == c)
                proj = SC.beam_extra_projection_mm(PLANTED_EXTRA["count"], hb["H_mm"], x["along_mm"])
                sched = m["label_section_cm"]
                rr = m["pts"]
                cx, cy = m["centre"]
                long_y = (rr[2][1] - rr[0][1]) > (rr[1][0] - rr[0][0])
                bx, by = (sched[0] * 10, sched[1] * 10) if long_y else (sched[1] * 10, sched[0] * 10)
                spts = [(cx - bx / 2, cy - by / 2), (cx + bx / 2, cy - by / 2), (cx + bx / 2, cy + by / 2),
                        (cx - bx / 2, cy + by / 2)]
                along_s = SC.extent_along(spts, x["angle_deg"])
                proj_s = SC.beam_extra_projection_mm(PLANTED_EXTRA["count"], hb["H_mm"], along_s)
                S(f"SA-{k}-EXTRA-{SHORT_MARK(hb['mark'])}", sid, "BEAM_EXTRA_4D16_PROJECTION",
                  f"host {hb['mark']} ({c}): DEPTH {hb['H_mm']:g} mm, column {_full(x['along_mm'], 1)} mm along the "
                  f"beam (drawn)" + ("" if abs(along_s - x["along_mm"]) < 0.05 else
                                     f"; {_full(along_s, 1)} mm with the labelled {sched[0]:g}x{sched[1]:g}"),
                  kg(proj, 16), f"4 x (2 x {hb['H_mm']:g} + {_full(x['along_mm'], 1)}) = {_full(proj, 1)} mm x "
                                f"16^2/162 (S6.1 convention, horizontal projection)", lo=min(kg(proj, 16), kg(proj_s, 16)),
                  hi=max(kg(proj, 16), kg(proj_s, 16)))
            deltas = [(beam_def(c)["mark"], max(0, UNDER_COLUMN_STIRRUP_RATE - beam_def(c)["stirrups_per_m"]) *
                       next(x for x in m["rel"] if x["occurrence_id"] == c)["along_mm"] / 1000.0)
                      for c in cands if tagged(c)]
            S(f"SA-{k}-LINKS", sid, "BEAM_STIRRUPS_UNDER_COLUMN",
              "extra links under the column by host: " + ", ".join(f"{mk} {_full(v, 3)}" for mk, v in deltas),
              max(v for _, v in deltas), "(10 - host rate)/m x column length along the host (count, rate "
                                         "equivalent; no kg)", kind="count",
              lo=None, hi=None)
        S(f"SA-{k}-STARTER", sid, "STARTER_PROJECTION_ABOVE_BEAM",
          f"separate starters, one per column bar ({nb}), projection only", kg(nb * STARTER_PROJECTION_MM, 16),
          f"{nb} x {STARTER_PROJECTION_MM:g} mm x 16^2/162; legs, feet and cranks excluded")

    # ------------------------------------------------------------ coverage of the frozen S3.1 rows
    special_segs = sorted({oc for m in members.values() for oc in m["owners"]})
    for oc in special_segs:
        for part in s31_of(oc):
            cid = f"S3.1:{oc}|{part}"
            check(len(cited[cid]) == 1, f"{cid} cited by exactly one S8.5 row ({cited[cid]})")
    dup = SC.duplicate_roles(comps)
    check(not dup, f"no physical role is held twice: {dup}")
    dup_ex = sorted(e for e, v in cited.items() if len(v) > 1)
    check(not dup_ex, f"no frozen component is cited twice: {dup_ex}")
    released = [c for c in comps if c["DECISION"] == SC.INCREMENTAL]
    released_kg = math.fsum(c["S8_5_KG"] for c in released)

    # ------------------------------------------------------------ concrete
    conc = []
    for sid in START_POPULATION:
        m = members[sid]
        for oc in m["owners"]:
            cc = s2comp[oc]["CONCRETE"]
            conc.append({"ITEM_ID": f"CON-{SHORT[sid]}-{cols[oc]['floor']}", "SPECIAL_ID": sid, "COLUMN_ID": oc,
                         "EXISTING_OWNER": f"S2:{oc}:CONCRETE", "EXISTING_STATE": cc["release_state"],
                         "EXISTING_QUANTITY": f"{cc['quantity']} {cc['unit']}", "FLAGS": cc["flags"],
                         "S8_5_M3": 0.0, "LANE": NOT_ADDED,
                         "WHY": "the column occurrence owns its concrete; S8.5 never measures a whole column again"})
    for sid, what, why in (
            (START_POPULATION[0], "TURN_OVERLAP_ZONE", "the 1 m zones lie inside the GF and 1F occurrences, whose "
                                                       "storey intervals meet at +5.50 without overlap"),
            (START_POPULATION[1], "TURN_OVERLAP_ZONE", "as for 31F"),
            (START_POPULATION[2], "DEAD_COLUMN_HEAD", "no capital, head or thickening is drawn; the members above "
                                                      "own their concrete"),
            (START_POPULATION[3], "PLANTED_BASE", "the column bears on the beam; no plinth or thickening is drawn"),
            (START_POPULATION[4], "PLANTED_BASE", "as for 544"),
            (START_POPULATION[5], "PLANTED_BASE", "as for 544")):
        conc.append({"ITEM_ID": f"CON-{SHORT[sid]}-{what}", "SPECIAL_ID": sid, "COLUMN_ID": "", "EXISTING_OWNER": "",
                     "EXISTING_STATE": "", "EXISTING_QUANTITY": "", "FLAGS": [], "S8_5_M3": None,
                     "LANE": NOT_IN_SOURCE, "WHY": why})

    # ------------------------------------------------------------ population and crosswalk rows
    for sid in START_POPULATION:
        m = members[sid]
        rec = m["rec"]
        fam = m["family"]
        if fam == SC.PLANTED:
            pc = m["pc"]
            host = m["host"]
            support = host["host"] if host["state"] == SC.RESOLVED else f"UNRESOLVED ({host['state']}: " \
                f"{', '.join(sorted({x['occurrence_id'] for x in m['rel']}))})"
            sec = {"schedule_cm": pc["schedule_section_cm"], "label_cm": m["label_section_cm"],
                   "drawn_cm": m["drawn_section_cm"], "state": pc["drawn_vs_schedule"]}
            extent = f"{m['storeys'][0]}: FFL {m['event_ffl']:+.2f} -> {m['top_ffl']:+.2f} m"
            below = f"supporting beam {support}"
            binding = f"label {rec['label']['handle']} -> leader {rec['leader']['handle']} -> circle " \
                      f"{rec['circle']['handle']} -> outline {m['outline_handles'][0]}; bars {rec['bar_text']['text']} " \
                      f"({rec['bar_text']['handle']})"
        elif fam == SC.TURN:
            sec = {"lower_cm": m["lower"]["schedule_section_cm"], "upper_schedule_cm": m["upper"]["schedule_section_cm"],
                   "upper_drawn_cm": m["upper"]["drawn_section_cm"], "upper_state": m["upper"]["drawn_vs_schedule"],
                   "overlap_mm": list(m["overlap_mm"])}
            extent = f"GF FFL {iv['GF']['lower_ffl_m']:+.2f} -> {iv['GF']['upper_ffl_m']:+.2f} m, 1F -> " \
                     f"{iv['1F']['upper_ffl_m']:+.2f} m; zone 1 m below / 1 m above {m['event_ffl']:+.2f} m"
            below = "its own chain (foundation segment, footing)"
            met_only = [h for h in rec["outlines"] if h not in rec["enclosed"]]
            binding = f"label {rec['label']['handle']} -> circle {rec['circle']['handle']} (gap " \
                      f"{_full(rec['circle_gap_mm'], 1)} mm) enclosing {', '.join(rec['enclosed'])}" + \
                      (f", meeting {', '.join(met_only)}" if met_only else "")
            support = below
        else:
            sec = {"schedule_cm": m["top"]["schedule_section_cm"], "drawn_cm": m["top"]["drawn_section_cm"]}
            extent = f"GF FFL {iv['GF']['lower_ffl_m']:+.2f} -> {iv['GF']['upper_ffl_m']:+.2f} m (stops)"
            below = "its own chain (foundation segment, footing)"
            binding = f"label {rec['label']['handle']} -> circle {rec['circle']['handle']} (gap " \
                      f"{_full(rec['circle_gap_mm'], 1)} mm) enclosing {', '.join(rec['outlines'])}"
            support = below
        rows_ = [c for c in comps if c["SPECIAL_ID"] == sid]
        missing = sorted({c["PHYSICAL_BAR_ROLE"] for c in rows_ if c["DECISION"] == SC.BLOCKED})
        pop.append({"SPECIAL_ID": sid, "FAMILY": fam, "LABEL": rec["label"]["text"], "LABEL_HANDLE": rec["label"]["handle"],
                    "SHEET": m["sheet"], "PDF_PAGE": m["page"], "BINDING": binding, "CHAIN_ID": m["chain"]["chain_id"],
                    "COLUMN_OWNERS": m["owners"], "STOREYS": m["storeys"], "EVENT": m["event"],
                    "EVENT_LEVEL": f"{m['event_sheet']} (FFL {m['event_ffl']:+.2f} m)", "SUPPORT_OR_PARENT": support,
                    "SECTION": sec, "VERTICAL_EXTENT": extent, "OUTLINE_HANDLES": m["outline_handles"],
                    "CONCRETE_OWNER": [f"S2:{o}:CONCRETE" for o in m["owners"]],
                    "LONGITUDINAL_OWNER": sorted({e for c in rows_ if c["KIND"] == "ORDINARY" and "LONGITUDINAL" in
                                                  c["PHYSICAL_BAR_ROLE"] for e in c["EXISTING_OWNER"]}),
                    "TIE_OWNER": sorted({e for c in rows_ if "TIES" in c["PHYSICAL_BAR_ROLE"] for e in c["EXISTING_OWNER"]}),
                    "SPECIAL_ROLES_AUDITED": sorted({c["PHYSICAL_BAR_ROLE"] for c in rows_ if c["KIND"] == "SPECIAL"}),
                    "SPECIAL_ALREADY_OWNED": sorted({c["PHYSICAL_BAR_ROLE"] for c in rows_ if c["KIND"] == "SPECIAL"
                                                     and c["DECISION"] == SC.ALREADY_OWNED}),
                    "MISSING": missing, "TERMINAL": "RESOLVED_TO_COLUMN_OCCURRENCE" +
                    ("" if fam != SC.PLANTED or m["host"]["state"] == SC.RESOLVED else "; SUPPORT_UNRESOLVED"),
                    "PRE_S8_EXISTING_OWNER_CLAIM": pre[sid]["EXISTING_STAGE_OWNER"],
                    "PRE_S8_NEW_OWNER_CLAIM": pre[sid]["NEW_S8_OWNER"]})
        for fl, seg in m["segs"].items():
            oc = seg["column_id"]
            role = ("TURN_LOWER" if fl == "GF" else "TURN_UPPER" if fl == "1F" else "CHAIN_BELOW") if fam == SC.TURN \
                else ("DEAD_TERMINATING" if fl == "GF" else "CHAIN_BELOW") if fam == SC.DEAD else "PLANTED"
            s3 = s31_of(oc)
            xwalk.append({"CROSSWALK_ID": f"X-{SHORT[sid]}-{fl}", "SPECIAL_ID": sid, "MEMBER": oc, "MEMBER_KIND":
                          "COLUMN_OCCURRENCE", "ROLE": role, "FLOOR": fl, "SHEETS": seg["plan_source"]["sheets"],
                          "HANDLES": seg["plan_source"]["handles"], "ORIENTATION": seg["orientation"],
                          "SECTION_SCHEDULE_CM": seg["schedule_section_cm"], "SECTION_DRAWN_CM": seg["drawn_section_cm"],
                          "DRAWN_VS_SCHEDULE": seg["drawn_vs_schedule"],
                          "BARS": f"{seg['longitudinal_bars']['count']}Ø{seg['longitudinal_bars']['dia_mm']}",
                          "S3_1_PARTS": sorted(s3), "S3_1_RELEASED_KG": _r(math.fsum(
                              r["kg"] or 0.0 for r in s3.values() if r["release_state"] in SC.OWNED_STATES)),
                          "S3_1_BLOCKED_PARTS": sorted(p for p, r in s3.items() if r["release_state"] == "BLOCKED"),
                          "S2_CONCRETE": s2comp[oc]["CONCRETE"]["release_state"],
                          "S8_5_TOUCHES": oc in m["owners"]})
        if fam == SC.PLANTED:
            for x in m["rel"]:
                hb = beam_def(x["occurrence_id"])
                xwalk.append({"CROSSWALK_ID": f"X-{SHORT[sid]}-{SHORT_MARK(hb['mark'])}-{x['line_id']}",
                              "SPECIAL_ID": sid,
                              "MEMBER": x["occurrence_id"], "MEMBER_KIND": "BEAM_OCCURRENCE",
                              "ROLE": "SUPPORT_HOST" if m["host"]["host"] == x["occurrence_id"] else
                              "SUPPORT_CANDIDATE", "FLOOR": s6o[x["occurrence_id"]]["floor"],
                              "SHEETS": [m["sheet"]], "HANDLES": [x["line_id"]], "ORIENTATION": _full(x["angle_deg"], 6),
                              "SECTION_SCHEDULE_CM": [hb["B_mm"] / 10, hb["H_mm"] / 10] if hb["H_mm"] else None,
                              "SECTION_DRAWN_CM": "",
                              "DRAWN_VS_SCHEDULE": hb["width_match"], "BARS": "",
                              "S3_1_PARTS": [], "S3_1_RELEASED_KG": None, "S3_1_BLOCKED_PARTS": [],
                              "S2_CONCRETE": "", "S8_5_TOUCHES": False,
                              "SPAN_RELATION": f"{x['relation']} (t {_full(x['t'], 1)} on span "
                                               f"{x['span'][0]:.0f}..{x['span'][1]:.0f}, column "
                                               f"{_full(x['along_mm'], 1)} mm along)"})
        else:
            rect = rec["outlines"][m["chain"]["members_by_sheet"][m["sheet"]]]
            for f_ in framing_at(m["sheet"], rect, lines, spans):
                hb = beam_def(f_["occurrence_id"])
                xwalk.append({"CROSSWALK_ID": f"X-{SHORT[sid]}-{SHORT_MARK(hb['mark'])}-{f_['line_id']}",
                              "SPECIAL_ID": sid, "MEMBER": f_["occurrence_id"], "MEMBER_KIND": "BEAM_OCCURRENCE",
                              "ROLE": "FRAMING_AT_TERMINATION" if fam == SC.DEAD else "FRAMING_AT_TURN",
                              "FLOOR": s6o[f_["occurrence_id"]]["floor"], "SHEETS": [m["sheet"]],
                              "HANDLES": [f_["line_id"]], "ORIENTATION": "", "SECTION_SCHEDULE_CM":
                              [hb["B_mm"] / 10, hb["H_mm"] / 10] if hb["H_mm"] else None, "SECTION_DRAWN_CM": "",
                              "DRAWN_VS_SCHEDULE": hb["width_match"], "BARS": "", "S3_1_PARTS": [],
                              "S3_1_RELEASED_KG": None, "S3_1_BLOCKED_PARTS": [], "S2_CONCRETE": "",
                              "S8_5_TOUCHES": False, "SPAN_RELATION": f"span {f_['end']} inside the column outline"})
    framing = {sid: [x["MEMBER"] for x in xwalk if x["SPECIAL_ID"] == sid and x["ROLE"].startswith("FRAMING")]
               for sid in START_POPULATION}

    # ------------------------------------------------------------ interfaces
    inter = []

    def I(iid, sid, interface, role, existing, new_owner, authority, state, check_, ok):
        inter.append({"INTERFACE_ID": iid, "SPECIAL_ID": sid, "INTERFACE": interface, "PHYSICAL_BAR_ROLE": role,
                      "EXISTING_OWNER": existing, "NEW_EXTRA_OWNER": new_owner, "SOURCE_AUTHORITY": authority,
                      "QUANTITY_STATE": state, "DOUBLE_COUNT_CHECK": check_, "RESULT": "PASS" if ok else "FAIL"})
    for sid in START_POPULATION[:3]:
        m = members[sid]
        f_occ = m["segs"]["FOUNDATION"]["column_id"]
        fo = [o for o in s4o if m["chain"]["chain_id"] in json.loads(o["columns"])]
        check(len(fo) == 1, f"{sid}: one S4 footing under the chain")
        fo = fo[0]
        sd = [c for c in s4c if c["occurrence_id"] == fo["occurrence_id"] and c["component"] == "STARTER_DOWEL_REFERENCE"]
        sd41 = [r for r in s41 if r["OCCURRENCE_ID"] == fo["occurrence_id"] and r["COMPONENT"] == "STARTER_DOWEL_REFERENCE"]
        st_ = s31_of(f_occ)["STARTER"]
        I(f"I-{SHORT[sid]}-01", sid, f"footing {fo['mark']} ({fo['occurrence_id']}) -> starter -> column",
          "STARTER", [f"S3.1:{f_occ}|STARTER ({st_['release_state']} {st_['kg']} kg)"],
          "none", "S4 STARTER_DOWEL_REFERENCE: " + "; ".join(c["why"] for c in sd), "NOT_ADDED",
          f"S4 {sd[0]['state']} / S4.1 {sd41[0]['NEW_RELEASE_STATE'] if sd41 else 'n/a'}: the footing assigns no "
          f"starter steel; S3.1 owns it once; the special event is at the GF roof, not at the footing",
          len(sd) == 1 and sd[0]["state"] == "NOT_APPLICABLE")
        gbp = m["chain"]["members_by_sheet"]["GBP"]
        gb = sorted(o["occurrence_id"] for o in s5o if f"COL:{gbp}+" in o["start_node"] + o["end_node"])
        I(f"I-{SHORT[sid]}-02", sid, f"ground beams -> column (GBP outline {gbp})", "GROUND_BEAM_BARS_AT_COLUMN",
          [f"S5:{g}" for g in gb], "none", "S5 occurrences (node COL:" + gbp + ")", "NOT_ADDED",
          "the ground-beam bars end in the column under S5; the column bars pass under S3.1; no special-column "
          "steel at this level", bool(gb))
    for sid in START_POPULATION[:2]:
        k = SHORT[sid]
        I(f"I-{k}-03", sid, "column -> slab / beams at the turn (GFRS)", "BEAMS_FRAMING_AT_THE_TURN",
          [f"S6:{o}" for o in framing[sid]], "none", "S6 occurrences whose span ends inside the GF outline",
          "NOT_ADDED", "the beams keep their S6 bars; the 2 m extra-bar and spiral zone passes through their depth "
                       "without adding beam steel", bool(framing[sid]))
        I(f"I-{k}-04", sid, "confinement zone (spiral) vs ordinary ties", "SPIRAL / ORDINARY_TIES",
          sorted(c for c in cited if c.startswith(f"S3.1:{members[sid]['lower']['column_id']}|TIE_")) +
          [f"S3.1:{members[sid]['lower']['column_id']}|EXTRA:TURN_SPIRAL (BLOCKED)"], "S8.5 (custody, BLOCKED)",
          "P15-TWISTED, P9-COL-TIES, VR-S8.5-01, VR-S8.5-03", BLOCKED,
          "the ties stay S3.1; the spiral adds nothing until its diameter and role are answered (Q-01); were it to "
          "replace the ties in the 2 m zone, S3.1's ties there would be the overstatement, not S8.5's",
          True)
    sid = START_POPULATION[2]
    I("I-38A-03", sid, "dead column -> members above (GFRS)", "TOP_TERMINATION",
      [f"S3.1:{members[sid]['top']['column_id']}|ANCHORAGE_TOP"] + [f"S6:{o}" for o in framing[sid]],
      "S8.5 (custody, BLOCKED)", "P3-LEGEND, P8-N09, VR-S8.5-05", BLOCKED,
      "the bars anchor 40D straight under S3.1 into the beams it supports (S6 owns their bars); bends / hooks not "
      "drawn", bool(framing[sid]))
    for sid in START_POPULATION[3:]:
        k = SHORT[sid]
        m = members[sid]
        host = m["host"]
        cands = sorted({x["occurrence_id"] for x in m["rel"]})
        I(f"I-{k}-01", sid, "planted column -> supporting beam", "BEAM_EXTRA_4D16 / COLUMN_BASE_ANCHORAGE",
          ([c["EXISTING_OWNER"][0] for c in comps if c["COMPONENT_ID"] == f"PC-{k}-08" and
            c["EXISTING_OWNER"]] or ["none (no stage)"]) + [f"S3.1:{m['pc']['column_id']}|ANCHORAGE_BASE"],
          "S6.1" if host["state"] == SC.RESOLVED else "S8.5 (custody, BLOCKED)", "P15-PLANTED, VR-S8.5-04",
          NOT_ADDED if host["state"] == SC.RESOLVED else BLOCKED,
          f"host {host['state']} ({', '.join(cands)}); the column bars stay S3.1, the extra stays with its one "
          "owner or blocked; nothing counted twice", True)
        I(f"I-{k}-02", sid, "planted column -> top slab", "COLUMN_TOP_ANCHORAGE",
          [f"S3.1:{m['pc']['column_id']}|ANCHORAGE_TOP"], "none", "S3.1", NOT_ADDED,
          f"the column's top end at {closing[m['storeys'][0]]}", True)

    # ------------------------------------------------------------ conflicts and questions
    cq = []

    def Q(i, kind, state, text, affects):
        cq.append({"ID": i, "KIND": kind, "STATE": state, "TEXT": text, "AFFECTS": affects})
    tc_kg = {SHORT[s]: s31_of(members[s]["lower"]["column_id"])["EXTRA:TURN_EXTRA_BARS"]["kg"]
             for s in START_POPULATION[:2]}
    Q("C-01", "SOURCE_CONFLICT", "RESOLVED_BY_FROZEN_OWNER",
      f"PRE-S8 records the twisted extras as 'none (no S3-S7 stage)' and assigns '4Ø16 + spiral' to S8. S3.1 already "
      f"holds 4Ø16 x 2 m on each GF segment ({', '.join(f'{k} {v} kg' for k, v in tc_kg.items())}, LOWER_BOUND), with "
      f"the spiral blocked. S8.5 adds no 4Ø16.", list(START_POPULATION[:2]))
    Q("C-02", "SOURCE_CONFLICT", "RESOLVED_BY_FROZEN_OWNER",
      "PRE-S8 records the planted columns as 'column not in S3.1' and assigns 'column + 4Ø16 support bars' to S8. "
      "S3.1 holds each planted column's bars, anchorages and ties, and S6.1 holds 548's beam extra. S8.5 re-adds "
      "neither.", list(START_POPULATION[3:]))
    Q("C-03", "SOURCE_CONFLICT", "RESOLVED_BY_FROZEN_OWNER",
      "PRE-S8 records the dead column as 'none (no S3-S7 stage)'. S3.1 holds its bars and a 40D top anchorage "
      "(PROVISIONAL). Only the undrawn termination form stays open.", [START_POPULATION[2]])
    Q("C-04", "SOURCE_CONFLICT", "OPEN",
      f"S1 reads P15-PLANTED as 'column bars anchored 100 into the beam' ({rules['P15-PLANTED']['english_interpretation']}). "
      "On the plot the '100' runs from the beam top up to the bars' crank: a 1.00 m projection ABOVE the beam (VR-S8.5-04).",
      list(START_POPULATION[3:]))
    m77 = members[START_POPULATION[5]]
    Q("C-05", "SOURCE_CONFLICT", "OPEN",
      f"77C: drawn {m77['drawn_section_cm'][0]:g}x{m77['drawn_section_cm'][1]:g} (FFRS 77B / SFRS 778) vs labelled and "
      f"scheduled {m77['label_section_cm'][0]:g}x{m77['label_section_cm'][1]:g}. S3.1 STR-COL-022 uses the schedule; "
      f"S2 holds its concrete PROVISIONAL.", [START_POPULATION[5]])
    c9 = members[START_POPULATION[1]]["upper"]
    Q("C-06", "SOURCE_CONFLICT", "OPEN",
      f"C9 1F (turn 324): drawn {c9['drawn_section_cm'][0]:g}x{c9['drawn_section_cm'][1]:g} vs scheduled "
      f"{c9['schedule_section_cm'][0]:g}x{c9['schedule_section_cm'][1]:g} (S3.1 STR-COL-020). The 200 x 250 overlap "
      "is the same under both.", [START_POPULATION[1]])
    Q("C-07", "SOURCE_CONFLICT", "OPEN",
      "The twisted elevation draws 25 horizontal lines over the 2 m zone (about 12.5 per m). The stated spiral is "
      "6Ø8/m. The drawing is consistent with 6/m ties plus 6/m spiral drawn together; the label states only the "
      "spiral. The stated rate is the only quantity statement.", list(START_POPULATION[:2]))
    Q("C-08", "SOURCE_CONFLICT", "OPEN",
      "Eight bars are drawn inside the spiral and '4Ø16 EXTRA' points at two of them. Which four are extra is not "
      "drawn. The straight quantity (4 x 2 m) does not depend on it.", list(START_POPULATION[:2]))
    for sid, q in ((START_POPULATION[3], "C-09"), (START_POPULATION[5], "C-10")):
        m = members[sid]
        cands = sorted({x["occurrence_id"] for x in m["rel"]})
        node = ", ".join(x["occurrence_id"] + " (" + x["relation"] + ")" for x in m["rel"])
        Q(q, "SOURCE_CONFLICT", "OPEN",
          f"{SHORT[sid]}: the planted-column detail shows a column on a beam spanning between two columns. The "
          f"column here sits on a beam-on-beam node: {node}. S6.1 marks the planted-column extra NOT_APPLICABLE on "
          "each, and PRE-S6 found no carrying span.", [sid] + cands)
    b6 = [c for c in sorted({x["occurrence_id"] for x in m77["rel"]}) if beam_def(c)["width_match"] == "SOURCE_CONFLICT"]
    Q("C-11", "SOURCE_CONFLICT", "OPEN",
      "77C candidate host " + ", ".join(f"{c} (drawn {s6o[c]['drawn_width_mm']} vs schedule "
                                         f"{s6o[c]['schedule_width_mm']} mm)" for c in b6) +
      ": the drawn width conflicts with the schedule (S6 BLOCKED). The sensitivity uses the schedule depth.",
      [START_POPULATION[5]] + b6)
    Q("Q-01", "QUESTION", "OPEN", "Twisted columns: the spiral's diameter (or its centreline dimensions in the 200 x "
                                  "250 overlap), cover, closing turns. Does it supplement the ordinary ties in the "
                                  "2 m zone or replace them?", list(START_POPULATION[:2]))
    Q("Q-02", "QUESTION", "OPEN", "Twisted columns: which four of the eight bars are the 4Ø16 extras, and the length "
                                  "of their top crank? Is the bottom end plain?", list(START_POPULATION[:2]))
    Q("Q-03", "QUESTION", "OPEN", "Twisted columns: do the upper column's bars start 1 m below the turn (as drawn) "
                                  "instead of a 40D lap, and what are the lower bars' top bends?",
      list(START_POPULATION[:2]))
    Q("Q-04", "QUESTION", "OPEN", "P.C 544: which beam carries it? B27 ends, B5 ends and B4 starts under it, and "
                                  "BL002 continues past it as an untagged span. Does the 4Ø16 / 10 cm-link detail "
                                  "apply, and along which beam?", [START_POPULATION[3]])
    Q("Q-05", "QUESTION", "OPEN", "P.C 77C: which beam carries it? B1 ends, B6 starts and B19 ends under it, and "
                                  "BL029 continues past it as an untagged span. Is the section 20x40 (drawn) or 20x50 "
                                  "(label)? Does the detail apply?", [START_POPULATION[5]])
    Q("Q-06", "QUESTION", "OPEN", "Planted columns: are the bars rising '100' above the beam separate starters "
                                  "lapping the column bars, or the column bars themselves? How many, and how long are "
                                  "the leg, the foot and the crank?", list(START_POPULATION[3:]))
    Q("Q-07", "QUESTION", "OPEN", "Dead column C11 at X06-Y04: how do its bars terminate in B27 / B1 / the GF roof "
                                  "(bend, hook, length)? Is any special end reinforcement required?",
      [START_POPULATION[2]])
    Q("Q-08", "QUESTION", "OPEN", "Planted-column detail: what is the unlabelled X in the beam under the column "
                                  "(the cranked 4Ø16, or separate diagonal bars)?", list(START_POPULATION[3:]))
    q_ids = {r["ID"] for r in cq if r["KIND"] == "QUESTION"}

    # ------------------------------------------------------------ ownership deltas
    od = []

    def D(did, stage, comp, old_owner, old_state, old_kg, new_owner, new_state, why, s85=""):
        od.append({"DELTA_ID": did, "DATE": DATE, "FROZEN_STAGE": stage, "COMPONENT_ID": comp,
                   "S8_5_COMPONENT": s85, "OLD_OWNER": old_owner,
                   "OLD_STATE": old_state, "OLD_KG": _r(old_kg), "NEW_OWNER": new_owner, "NEW_STATE": new_state,
                   "KG_MOVED": 0.0, "WHY": why})
    n = 0
    for c in comps:
        if c["DECISION"] == SC.ALREADY_OWNED and c["KIND"] == "SPECIAL":
            n += 1
            D(f"OD-{n:02d}", c["EXISTING_OWNER"][0].split(":")[0], c["EXISTING_OWNER"], c["NEW_EXTRA_OWNER"],
              c["EXISTING_STATE"], c["EXISTING_KG"], c["NEW_EXTRA_OWNER"], c["EXISTING_STATE"],
              f"CONFIRMED where it is: {c['CHECK']}", s85=c["COMPONENT_ID"])
    for c in comps:
        if c["DECISION"] == SC.BLOCKED:
            n += 1
            old = c["EXISTING_OWNER"] or ["none"]
            D(f"OD-{n:02d}", old[0].split(":")[0] if c["EXISTING_OWNER"] else "none", c["EXISTING_OWNER"] or "none",
              old[0].split(":")[0] if c["EXISTING_OWNER"] else "none", c["EXISTING_STATE"] or "UNOWNED", None,
              c["NEW_EXTRA_OWNER"], BLOCKED,
              "custody of a blocked role: the single owner of a future release" if "custody" in c["NEW_EXTRA_OWNER"]
              else "stays blocked with its frozen owner", s85=c["COMPONENT_ID"])
    for sid in START_POPULATION:
        n += 1
        D(f"OD-{n:02d}", "PRE-S8", f"PRE-S8 02 census {sid}", "PRE-S8 claim: " + pre[sid]["EXISTING_STAGE_OWNER"],
          "CENSUS", None, "S8.5 rows " + ", ".join(c["COMPONENT_ID"] for c in comps if c["SPECIAL_ID"] == sid
                                                   and c["KIND"] == "SPECIAL"), "SUPERSEDED_CLAIM",
          "PRE-S8 stays frozen; its ownership claim is replaced by the S8.5 role-by-role audit, no quantity")

    # ------------------------------------------------------------ conservation
    cons = []

    def A(cid, text, ok, detail=""):
        cons.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    A("K-01", "every frozen stage (21 manifests), the S8.3 errata and the S1 / S2 / S3 / S3.1 registers verify before "
              "and after", len(frozen) == len(MANIFESTS) == 21 and len(errata) == 3 and len(index) == 4,
      f"{len(frozen)} manifests, {len(errata)} errata, " + ", ".join(f"{k} {v['registers_verified']}"
                                                                   for k, v in index.items()))
    A("K-02", "six records, six real column occurrences; every planted support resolved or explicitly unresolved",
      len(pop) == 6 and all(p["TERMINAL"].startswith("RESOLVED_TO_COLUMN_OCCURRENCE") for p in pop),
      "; ".join(f"{SHORT[p['SPECIAL_ID']]} -> {', '.join(p['COLUMN_OWNERS'])} ({p['SUPPORT_OR_PARENT']})" for p in pop))
    A("K-03", "every special-column annotation is accounted: six DXF labels on seven sheets, each bound once; p.15 "
              "details and the legend as visual records",
      len(st["labels"]) == 6 and len({(l["sheet"], l["handle"]) for l in st["labels"]}) == 6 and not st["words"],
      "labels " + ", ".join(sorted(l["sheet"] + ":" + l["handle"] for l in st["labels"])) +
      f"; other legend codes {st['other_codes']}")
    A("K-04", "no duplicate column: S8.5 creates no column occurrence; each owner appears once per record",
      all(len(p["COLUMN_OWNERS"]) == len(set(p["COLUMN_OWNERS"])) for p in pop) and
      s31["occurrence_states"] == {"REBAR_LOWER_BOUND": 95}, "S3.1 occurrences 95")
    A("K-05", "no duplicate bars or ties: every S3.1 row of the eight special segments is cited by exactly one S8.5 "
              "row, no frozen component twice, no role twice", not dup and not dup_ex,
      f"{sum(len(s31_of(o)) for o in special_segs)} S3.1 rows over {len(special_segs)} segments")
    A("K-06", "S3.1 and S6.1 totals unchanged", abs(s31["totals_kg"]["total"] - s31_headline["MODELLED_SUM_NOT_FINAL_KG"])
      < 5e-4 and abs(s61sum["delta_by_kind_kg"]["planted_column_extra"] - float(
          next(c for c in comps if c["COMPONENT_ID"] == "PC-548-08")["EXISTING_KG"])) < 1e-6,
      f"S3.1 {s31['totals_kg']['total']} kg; S6.1 known {s61sum['s6_1_known_kg']} kg")
    A("K-07", "S8.5 releases only INCREMENTAL roles", released_kg == math.fsum(c["S8_5_KG"] or 0.0 for c in comps) and
      all(c["QUANTITY_STATE"] in RELEASED_LANES for c in released), f"{len(released)} rows, {_full(released_kg)} kg")
    A("K-08", "the twisted 4Ø16 straight basis recomputes to S3.1's figure on both columns",
      all("(equal)" in c["CHECK"] for c in comps if c["PHYSICAL_BAR_ROLE"] == "EXTRA_LONGITUDINAL_STRAIGHT"), "")
    A("K-09", "548's beam extra recomputes to S6.1's figure",
      "(equal)" in next(c for c in comps if c["COMPONENT_ID"] == "PC-548-08")["CHECK"], "")
    A("K-10", "every blocked role is registered with its question; every question is used",
      all(b["QUESTION"] in q_ids for b in blocked) and q_ids <= {c["QUESTION"] for c in comps},
      f"{len(blocked)} blocked")
    A("K-11", "sensitivity is never released", all(not s_["RELEASED"] and s_["LANE"] == SENS for s_ in sens),
      f"{len(sens)} cases")
    A("K-12", "planted storeys: 544 / 548 -> 1F, 77C -> 2F, as S1 and S3.1",
      [members[s]["storeys"][0] for s in START_POPULATION[3:]] == ["1F", "1F", "2F"], "")
    A("K-13", "turned outlines on GFRS are the 1F columns; the dead column has nothing above",
      all(members[s]["outline_handles"][1] in members[s]["rec"]["outlines"] for s in START_POPULATION[:2]) and
      members[START_POPULATION[2]]["above_on_ffrs"] == [], "")
    A("K-14", "no new concrete: every column keeps its S2 owner",
      all(c["S8_5_M3"] in (0.0, None) for c in conc), f"{sum(1 for c in conc if c['LANE'] == NOT_ADDED)} owned rows")
    A("K-15", "PRE-S8 read through its whitelist only", set(PRE_S8_COLUMNS).isdisjoint(PRE_S8_FIREWALLED),
      f"{list(PRE_S8_COLUMNS)}")
    A("K-16", "no client drawing, render or crop in the package",
      not [p for p in HERE.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")], "")
    check(all(c["RESULT"] == "PASS" for c in cons), "; ".join(f"{c['CHECK_ID']} {c['DETAIL']}" for c in cons
                                                             if c["RESULT"] != "PASS"))

    # ------------------------------------------------------------ source register
    srcreg = source_register(st, members, rules)

    # ------------------------------------------------------------ write
    for o in OUTPUTS + [MANIFEST_NAME]:
        if (HERE / o).exists():
            (HERE / o).unlink()
    COMP_FIELDS = ["COMPONENT_ID", "SPECIAL_ID", "COLUMN_ID", "PHYSICAL_BAR_ROLE", "KIND", "DIA_MM", "COUNT", "STATED",
                   "DRAWN", "EXISTING_OWNER", "EXISTING_STATE", "EXISTING_KG", "NEW_EXTRA_OWNER", "SOURCE_AUTHORITY",
                   "DECISION", "QUANTITY_STATE", "S8_5_KG", "CHECK", "BLOCKED_ID", "QUESTION", "SENSITIVITY_IDS", "WHY"]
    XW = ["CROSSWALK_ID", "SPECIAL_ID", "MEMBER", "MEMBER_KIND", "ROLE", "FLOOR", "SHEETS", "HANDLES", "ORIENTATION",
          "SECTION_SCHEDULE_CM", "SECTION_DRAWN_CM", "DRAWN_VS_SCHEDULE", "BARS", "S3_1_PARTS", "S3_1_RELEASED_KG",
          "S3_1_BLOCKED_PARTS", "S2_CONCRETE", "S8_5_TOUCHES", "SPAN_RELATION"]
    _csv(OUTPUTS[1], srcreg)
    _csv(OUTPUTS[2], pop)
    _csv(OUTPUTS[3], xwalk, XW)
    _csv(OUTPUTS[4], [c for c in comps if c["TABLE"] == "04"], COMP_FIELDS)
    _csv(OUTPUTS[5], [c for c in comps if c["TABLE"] == "05"], COMP_FIELDS)
    _csv(OUTPUTS[6], [c for c in comps if c["TABLE"] == "06"], COMP_FIELDS)
    _csv(OUTPUTS[7], conc)
    qto = [{"ITEM_ID": c["COMPONENT_ID"], "SPECIAL_ID": c["SPECIAL_ID"], "ROLE": c["PHYSICAL_BAR_ROLE"],
            "KIND": c["KIND"], "DIA_MM": c["DIA_MM"], "DECISION": c["DECISION"], "LANE": c["QUANTITY_STATE"],
            "EXISTING_OWNER": c["EXISTING_OWNER"], "EXISTING_KG": c["EXISTING_KG"], "INCREMENTAL_KG": c["S8_5_KG"],
            "BLOCKED_ID": c["BLOCKED_ID"], "SENSITIVITY_IDS": c["SENSITIVITY_IDS"]} for c in comps]
    _csv(OUTPUTS[8], qto)
    _csv(OUTPUTS[9], inter)
    _csv(OUTPUTS[10], blocked)
    _csv(OUTPUTS[11], cq, ["ID", "KIND", "STATE", "TEXT", "AFFECTS"])
    _csv(OUTPUTS[12], od)
    _csv(OUTPUTS[13], sens, ["CASE_ID", "SPECIAL_ID", "ROLE", "LANE", "CASE", "KG", "KG_LOW", "KG_HIGH", "COUNT_DELTA",
                             "BASIS", "RELEASED"])
    _csv(OUTPUTS[14], cons)
    prov = [{"record": r["SOURCE_ID"], "output": OUTPUTS[1], "handles": r["HANDLES"], "file": r["FILE"],
             "page": r["PAGE"]} for r in srcreg]
    prov += [{"record": p["SPECIAL_ID"], "output": OUTPUTS[2], "handles": [p["LABEL_HANDLE"], *p["OUTLINE_HANDLES"]],
              "sheet": p["SHEET"], "drawing_sha256": STRUCT_SHA} for p in pop]
    prov += [{"record": c["COMPONENT_ID"], "output": OUTPUTS[{"04": 4, "05": 5, "06": 6}[c["TABLE"]]],
              "existing_owner": c["EXISTING_OWNER"], "authority": c["SOURCE_AUTHORITY"]} for c in comps]
    prov += [{"record": v["ID"], "output": OUTPUTS[1], "file": v["FILE"], "page": v["PAGE"], "dpi": v["DPI"],
              "box_px": v["BOX_PX"], "kept_in_git": False} for v in VISUAL]
    (HERE / OUTPUTS[15]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in prov),
                                    encoding="utf-8")
    by_dia = defaultdict(float)
    for c in released:
        by_dia[str(c["DIA_MM"])] += c["S8_5_KG"]
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "starting_population": list(START_POPULATION),
        "verified_special_columns": {p["SPECIAL_ID"]: {"family": p["FAMILY"], "owners": p["COLUMN_OWNERS"],
                                                       "storeys": p["STOREYS"], "event": p["EVENT"],
                                                       "event_level": p["EVENT_LEVEL"],
                                                       "support_or_parent": p["SUPPORT_OR_PARENT"]} for p in pop},
        "released": {"concrete_m3": 0.0, "reinforcement_kg": _r(released_kg),
                     "reinforcement_items": [c["COMPONENT_ID"] for c in released]},
        "incremental_by_diameter_kg": {"8": _r(by_dia.get("8", 0.0)), "16": _r(by_dia.get("16", 0.0))},
        "already_owned": {
            "s3_1_special_extras_kg": {c["COMPONENT_ID"]: c["EXISTING_KG"] for c in comps
                                       if c["DECISION"] == SC.ALREADY_OWNED and c["KIND"] == "SPECIAL" and
                                       c["EXISTING_OWNER"][0].startswith("S3.1")},
            "s6_1_special_extras_kg": {c["COMPONENT_ID"]: c["EXISTING_KG"] for c in comps
                                       if c["DECISION"] == SC.ALREADY_OWNED and c["KIND"] == "SPECIAL" and
                                       c["EXISTING_OWNER"][0].startswith("S6.1")},
            "s3_1_ordinary_kg_by_special": {sid: _r(math.fsum(c["EXISTING_KG"] or 0.0 for c in comps
                                                              if c["SPECIAL_ID"] == sid and c["KIND"] == "ORDINARY" and
                                                              c["EXISTING_OWNER"] and
                                                              c["EXISTING_OWNER"][0].startswith("S3.1")))
                                            for sid in START_POPULATION}},
        "spiral": {"state": BLOCKED, "stated": "6Ø8/m over 1 m above + 1 m below", "turns": SC.turns_over(
            SPIRAL["zone_mm"], SPIRAL["per_m"]), "pitch_mm": _r(SC.pitch_from_rate(SPIRAL["per_m"])),
            "overlap_mm": {SHORT[s]: list(members[s]["overlap_mm"]) for s in START_POPULATION[:2]},
            "upper_bound_kg_per_column": {r["CASE_ID"]: r["KG"] for r in sens if r["ROLE"] == "SPIRAL"}},
        "planted_hosts": {SHORT[s]: {"state": members[s]["host"]["state"], "host": members[s]["host"]["host"],
                                     "candidates": sorted({x["occurrence_id"] for x in members[s]["rel"]})}
                          for s in START_POPULATION[3:]},
        "lanes": {"components": dict(sorted(Counter(c["DECISION"] for c in comps).items())),
                  "blocked": len(blocked), "concrete": dict(sorted(Counter(c["LANE"] for c in conc).items()))},
        "conflicts": [r["ID"] for r in cq if r["KIND"] == "SOURCE_CONFLICT"],
        "questions": [r["ID"] for r in cq if r["KIND"] == "QUESTION"],
        "sensitivity": {r["CASE_ID"]: r["KG"] if r["KG"] is not None else
                        ([r["KG_LOW"], r["KG_HIGH"]] if r["KG_LOW"] is not None else r["COUNT_DELTA"]) for r in sens},
        "s3_1": {"total_kg": s31["totals_kg"]["total"], "state": "UNCHANGED"},
        "s6_1": {"known_kg": s61sum["s6_1_known_kg"], "planted_column_extra_kg":
                 s61sum["delta_by_kind_kg"]["planted_column_extra"], "state": "UNCHANGED"},
        "conservation": {c["CHECK_ID"]: c["RESULT"] for c in cons},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
        "register_indexes": index, "s8_3_errata_sha256": errata,
        "unit_mass": UM.describe(UNIT_MASS), "references_read": []}
    _json(OUTPUTS[16], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, comps, blocked, cq, sens, pop), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in READ.values()},
                "drawing_sha256": {"ST7757.dxf": STRUCT_SHA, "ST7757.pdf": STRUCT_PDF_SHA},
                "pre_s8_columns_read": list(PRE_S8_COLUMNS),
                "frozen_baselines": summary["frozen_baselines"], "register_indexes": index,
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "released": summary["released"],
                "rule": "frozen before any earlier Urban, contractor or third-party figure is read; the comparison "
                        "after it explains differences and never changes a frozen quantity"}
    _json(MANIFEST_NAME, manifest)
    for k, m_ in MANIFESTS.items():
        DR.verify_frozen(m_, ROOT)
    return summary


def SHORT_MARK(mark):
    return re.sub(r"[^A-Za-z0-9]", "", mark)


def s31_state_join(states):
    s = sorted(set(states))
    return s[0] if len(s) == 1 else "+".join(s)


def source_register(st, members, rules):
    man = {o["sha256"]: o for o in _j(READ["SOURCE_MANIFEST"])["files"] if isinstance(o, dict) and o.get("sha256")}
    rows = []

    def add(sid, kind, file, page, handles, layer, raw, role, evidence):
        rows.append({"SOURCE_ID": sid, "KIND": kind, "FILE": file, "PAGE": page, "HANDLES": handles, "LAYER": layer,
                     "RAW": raw, "ROLE": role, "EVIDENCE": evidence})
    add("SRC-01", "FILE", "ST7757.dxf", "1-7", [], "", STRUCT_SHA, "STRUCTURAL_AUTHORITY",
        f"registered {STRUCT_SHA in man}; every text of the seven sheets searched; GFRS / FFRS / SFRS plans read")
    add("SRC-02", "FILE", "ST7757.pdf", "1-15", [], "", STRUCT_PDF_SHA, "PLOT_OF_SRC-01 + PAGES_8-15",
        f"registered {STRUCT_PDF_SHA in man}; visual records only (p.15 exists only as a plot)")
    for sid, m in members.items():
        rec = m["rec"]
        lab = rec["label"]
        hs = [lab["handle"], rec["circle"]["handle"], *rec["outlines"]]
        ev = f"bound to {m['chain']['chain_id']}"
        if "leader" in rec:
            hs.insert(1, rec["leader"]["handle"])
            hs.append(rec["bar_text"]["handle"])
            ev += f"; leader gap {_full(rec['leader']['label_gap_mm'], 1)} mm; bar text {rec['bar_text']['text']}"
        else:
            ev += f"; circle gap {_full(rec['circle_gap_mm'], 1)} mm (next {_full(rec['second_circle_gap_mm'], 1)} mm)"
        add(f"A-{SHORT[sid]}", "ANNOTATION", f"ST7757 p.{m['page']} {m['sheet']}", m["page"], hs, lab["layer"],
            lab["text"], f"{m['family']}_COLUMN_LABEL", ev)
    for i, (sh, h, t) in enumerate(st["other_codes"], 1):
        add(f"A-OTHER-{i:02d}", "ANNOTATION", f"ST7757 {sh}", st["sheets"][sh], [h], "", t, "OTHER_LEGEND_CODE",
            "outside the special-column families of S8.5")
    for rid in ("P15-TWISTED", "P15-PLANTED", "P3-LEGEND", "P9-COL-TIES", "P8-N09", "P8-N22"):
        r = rules[rid]
        add(f"RULE-{rid}", "PROJECT_RULE", f"ST7757 p.{r['page']}", r["page"], r.get("dxf_handles") or [], "",
            "Arabic general note (raw text in S1)" if r.get("arabic_wording") else r["raw_text"], r["topic"],
            f"S1 {r['status']}: {r['english_interpretation']}")
    for v in VISUAL:
        add(v["ID"], "VISUAL_RECORD", v["FILE"], v["PAGE"], [], "",
            f"{v['DPI']} dpi box {v['BOX_PX']}" if v["DPI"] else "S1 register (plot legend)",
            "VISUAL_EVIDENCE (render not kept)", v["READ"])
    for k, p in READ.items():
        add(f"REG-{k}", "FROZEN_REGISTER", str(p.relative_to(ROOT)), "", [], "", _sha(p), "URBAN_REGISTER_READ",
            "whitelisted columns only: " + ", ".join(PRE_S8_COLUMNS) if k == "PRE_S8_CENSUS" else "read, never written")
    return rows


def readme(s, comps, blocked, cq, sens, pop):
    L = ["# S8.5: special columns (turned, dead and planted)", "",
         f"Baseline `{s['baseline']}`. Frozen before any comparison: `{MANIFEST_NAME}`, `references_read: []`.", "",
         "## The six records", "",
         "| record | family | column owner(s) | event | support / parent |", "|---|---|---|---|---|"]
    L += [f"| {p['SPECIAL_ID']} | {p['FAMILY']} | {', '.join(p['COLUMN_OWNERS'])} | {p['EVENT']} at {p['EVENT_LEVEL']} "
          f"| {p['SUPPORT_OR_PARENT']} |" for p in pop]
    L += ["", "Each label binds by drawing geometry. A T.C circle encloses the GF outline and meets or encloses the "
              "turned 1F outline; the D.C circle encloses the dead column. A P.C label reaches, through its leader, a circle "
              "centred on the outline, with its bar text beside it. Each label is an event on an ordinary S1 / S3.1 "
              "column, never a second column.", "",
          "## Released", "",
          f"- Concrete: **{_full(s['released']['concrete_m3'])} m3**. Every column keeps its S2 concrete owner. No "
          "head, plinth or thickening is drawn.",
          f"- Incremental reinforcement: **{_full(s['released']['reinforcement_kg'])} kg** (Ø16 "
          f"{_full(s['incremental_by_diameter_kg']['16'])}, Ø8 {_full(s['incremental_by_diameter_kg']['8'])}). No "
          "special role is both required by the source with a fixed quantity and unowned by an earlier stage.", "",
          "## Already counted (not added again)", ""]
    for k, v in sorted(s["already_owned"]["s3_1_special_extras_kg"].items()):
        L.append(f"- {k}: S3.1 {_full(v)} kg")
    for k, v in sorted(s["already_owned"]["s6_1_special_extras_kg"].items()):
        L.append(f"- {k}: S6.1 {_full(v)} kg")
    L += ["- The ordinary bars, anchorages and ties of all eight segments stay S3.1's: " +
          ", ".join(f"{SHORT[k]} {_full(v, 3)} kg" for k, v in s["already_owned"]["s3_1_ordinary_kg_by_special"].items())
          + ".", "", "## Blocked (10_BLOCKED_COMPONENTS.csv)", ""]
    for b in blocked:
        L.append(f"- {b['BLOCKED_ID']}: {b['PHYSICAL_BAR_ROLE']} ({b['QUESTION']})")
    L += ["", "## Sensitivity (not released)", ""]
    for x in sens:
        val = _full(x["KG"], 6) + " kg" if x["KG"] is not None else (
            f"{_full(x['KG_LOW'], 6)} - {_full(x['KG_HIGH'], 6)} kg" if x["KG_LOW"] is not None else
            f"{_full(x['COUNT_DELTA'], 3)} links")
        L.append(f"- {x['CASE_ID']}: {x['CASE']} -> {val}")
    L += ["", "## Conflicts and questions", ""]
    L += [f"- **{x['ID']}** ({x['STATE']}): {x['TEXT']}" for x in cq]
    L += ["", "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`", "",
          "Rebuild: `python3 -I research/alsenan_special_columns_s8_5/build_s8_5.py` (byte-identical). Renders and "
          "crops of the drawings stay outside git."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    try:
        s = build()
    except Stop as e:
        print(f"STOP: {e}")
        sys.exit(1)
    print(json.dumps({k: s[k] for k in ("released", "incremental_by_diameter_kg", "already_owned", "spiral",
                                        "planted_hosts", "lanes", "conservation")}, indent=1, ensure_ascii=False))
