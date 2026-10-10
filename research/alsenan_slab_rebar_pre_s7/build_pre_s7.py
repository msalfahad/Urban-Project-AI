"""PRE-S7 elevated slab rebar readiness / source exhaustion (no kg).

    python3 -I research/alsenan_slab_rebar_pre_s7/build_pre_s7.py

Reads the Urban project source ST7757.dxf (sha256-checked) through the S1 lab source model
(research/external_engine_lab/alsenan_structural_s1.py: sheets, entities, detail zones), the frozen S1 slab / beam /
rule registers (checked against the S1 INDEX), the R4 temperature / slab-detail registers (prior claims, reconciled),
the D1.2 cover basis, and the committed visual reading of ST7757.pdf pp.4-6 and p.15. The nine frozen stage
manifests (S4 ... D1.2) are hash-checked first. Nothing else is opened: no reference quantity, no donor, no old
estimate. Every decision is made by engine/source/slab_rebar_readiness.py; this builder measures and records.

No bar length total and no kg is computed. A rule extent appears only where the rule's gate passes, and only as a
candidate value beside its conflict.
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
LAB = ROOT / "research" / "external_engine_lab"
for p in (ROOT, LAB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import alsenan_structural_s1 as S  # noqa: E402
from engine.source import cover_authority as CA  # noqa: E402
from engine.source import delta_release as DR  # noqa: E402
from engine.source import graphic_evidence as GE  # noqa: E402
from engine.source import legacy_text as LT  # noqa: E402
from engine.source import slab_rebar_readiness as SR  # noqa: E402
from engine.source import structural_census as SC  # noqa: E402

ROUND = "PRE-S7"
POLICY = "ELEVATED_SLAB_REBAR_READINESS_V1"
BASELINE_HEAD = "44f693e"
DRAWING_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
DXF = ROOT / "data" / "inputs" / "by_sha256" / f"{DRAWING_SHA}.dxf"
PDF = ROOT / "data" / "inputs" / "by_sha256" / f"{PDF_SHA}.pdf"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
R4 = R / "alsenan_rebar_source_exhaustion_04" / "registers"
D12 = R / "d1_2_footing_cover_audit"
VIS = HERE / "source_search_inputs" / "PRE_S7_VISUAL_READING.json"
MANIFESTS = {"S4": R / "alsenan_footing_rebar_s4" / "S4_FREEZE_MANIFEST.json",
             "S4.1": R / "alsenan_footing_rebar_s4_1" / "S4_1_FREEZE_MANIFEST.json",
             "S5": R / "alsenan_ground_system_rebar_s5" / "S5_FREEZE_MANIFEST.json",
             "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
             "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1" / "S6_1_FREEZE_MANIFEST.json",
             "S5.1": R / "alsenan_ground_system_rebar_s5_1" / "S5_1_FREEZE_MANIFEST.json",
             "AD1": R / "ad1_authority_decisions" / "AD1_FREEZE_MANIFEST.json",
             "D1.1": R / "d1_1_stirrup_authority_audit" / "D1_1_FREEZE_MANIFEST.json",
             "D1.2": D12 / "D1_2_FREEZE_MANIFEST.json"}
S1_FROZEN = ["SLAB_PANEL_REGISTER", "SLAB_REBAR_SOURCE_REGISTER", "SLAB_RULE_APPLICATION_MAP",
             "STRUCTURAL_PROJECT_RULE_REGISTER", "BEAM_OCCURRENCE_REGISTER"]
CODE = ["engine/source/slab_rebar_readiness.py", "engine/source/cover_authority.py",
        "engine/source/graphic_evidence.py", "engine/source/structural_census.py", "engine/source/legacy_text.py",
        "engine/source/delta_release.py", "engine/source/planar_shadow_topology.py",
        "research/external_engine_lab/alsenan_structural_s1.py",
        "research/alsenan_slab_rebar_pre_s7/build_pre_s7.py"]
INPUTS = [str(p.relative_to(ROOT)) for p in MANIFESTS.values()] + [
    "research/alsenan_structural_census_s1/INDEX.json"] + [
    f"research/alsenan_structural_census_s1/{n}.json" for n in S1_FROZEN] + [
    "research/alsenan_rebar_source_exhaustion_04/registers/TEMPERATURE_REBAR_RULE_REGISTER.json",
    "research/alsenan_rebar_source_exhaustion_04/registers/SLAB_DETAIL_RULE_REGISTER.json",
    "research/d1_2_footing_cover_audit/02_COVER_BASIS.json",
    "research/alsenan_slab_rebar_pre_s7/source_search_inputs/PRE_S7_VISUAL_READING.json"]
OUTPUTS = ["00_README.md", "01_SLAB_PANEL_CENSUS.csv", "02_THICKNESS_REGISTER.csv", "03_SLAB_REBAR_TOKENS.csv",
           "04_COMPONENT_READINESS.csv", "05_SUPPORT_REGISTER.csv", "06_SUPPORT_RULES.csv",
           "07_BAR_RUN_REGISTER.csv", "08_OPENING_REGISTER.csv", "09_TEMPERATURE_REBAR_REGISTER.csv",
           "10_COUNT_RULE_REGISTER.csv", "11_SOURCE_CONFLICTS.csv", "12_SOURCE_EXPECTED_NOT_LOCATED.csv",
           "13_PROVENANCE.jsonl", "14_S7_RELEASE_CANDIDATES.csv", "15_ENGINEER_QUESTIONS.csv", "PRE_S7_SUMMARY.json"]
SHEETS = ("GFRS", "FFRS", "SFRS")
FLOOR = {"GFRS": "GF_ROOF_SLAB", "FFRS": "1F_ROOF_SLAB", "SFRS": "2F_ROOF_SLAB"}
REBAR = re.compile(r"\d+\s*(%%[cC]|[Øø])\s*\d+|(%%[cC]|[Øø])\s*\d+\s*(@|/)|\b[YT]\d{1,2}\s*@\s*\d+|\(T&B\)|"
                   r"\bE\.?W\.?\b|AS\s+PER\s+SCH", re.I)
WIDE_HATCH_SCALE = 2000.0    # the legend's sunken-slab hatch (wide spacing)
DENSE_HATCH_SCALE = 800.0    # the legend's cantilever-portion / bearing-wall hatch (dense spacing)
RECT_MIN = 0.95              # S1's rectangularity floor for a single-valued span
SIDE_TOL_MM = 60.0           # an edge lies on a panel side when its endpoints are this close to the side
ALIGN_TOL_MM = 60.0          # two panels are aligned across a support when their cross extents agree this closely
DUP_TOL_MM = 50.0            # same text this close = the same graphic twice
ZONE_MARGIN_MM = 600.0       # a label this close to a section / detail drawing belongs to it
MIN_COVER_MM = 25.0
BRIEF_RULES = {"P15-SLAB-ON-BEAMS", "P15-TEMP-TABLE", "P15-TEMP-NOTES", "P4-6-NOTE-2", "P8-N18", "P1-NOTE-A",
               "P8-N22", "P8-N04", "P3-LEGEND"}


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"PRE-S7 check failed: {what}")


# ------------------------------------------------------------------ io
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6g}" if abs(v) < 1e15 else str(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _r(v, n=1):
    return None if v is None else round(float(v), n)


# ------------------------------------------------------------------ inputs
def verify_inputs():
    check(_sha(DXF) == DRAWING_SHA, "ST7757.dxf sha256")
    check(Path(S.DXF).resolve() == DXF.resolve() or _sha(S.DXF) == DRAWING_SHA, "the S1 lab reads ST7757.dxf")
    check(_sha(PDF) == PDF_SHA, "ST7757.pdf sha256")
    idx = _j(S1 / "INDEX.json")["registers"]
    for n in S1_FROZEN:
        check(_sha(S1 / f"{n}.json") == idx[n]["sha256"], f"frozen S1 register {n}")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    vis = _j(VIS)
    check(vis["pdf_sha256"] == PDF_SHA, "visual reading is of ST7757.pdf")
    return frozen, vis


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ geometry
def bbox(ring):
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def in_face(pt, row):
    return SC.point_in_ring(pt, row["polygon_mm"]) and not any(SC.point_in_ring(pt, h) for h in row["holes_mm"] or [])


def edge_geom(row, i):
    ring = row["polygon_mm"]
    a, b = ring[i], ring[(i + 1) % len(ring)]
    return a, b, ("V" if abs(b[0] - a[0]) < abs(b[1] - a[1]) else "H")


def side_of_edge(row, a, b, ori):
    x0, y0, x1, y1 = bbox(row["polygon_mm"])
    if ori == "V":
        x = (a[0] + b[0]) / 2
        if abs(x - x0) <= SIDE_TOL_MM:
            return "W"
        if abs(x - x1) <= SIDE_TOL_MM:
            return "E"
    else:
        y = (a[1] + b[1]) / 2
        if abs(y - y0) <= SIDE_TOL_MM:
            return "S"
        if abs(y - y1) <= SIDE_TOL_MM:
            return "N"
    return "INTERIOR"


def axis_aligned(row):
    ori = row.get("orientation_deg")
    return ori is not None and min(abs(ori % 90), 90 - abs(ori % 90)) < 1.0


def sweep_texts(src):
    """Every TEXT / MTEXT / ATTRIB (model space, block contents to depth 4, attributes) and DIMENSION override on
    the slab sheets."""
    doc, msp = src.doc, src.msp
    styles = {s.dxf.name.upper(): (s.dxf.font or "") for s in doc.styles}
    out = []

    def add(e, ident):
        t = e.dxftype()
        try:
            layer = e.dxf.layer
        except Exception:
            return
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            p = e.dxf.insert
            raw = (e.dxf.text if t != "MTEXT" else e.plain_text()) or ""
            rot = float(e.dxf.get("rotation", 0.0) or 0.0) % 360.0
        elif t == "DIMENSION":
            raw = e.dxf.get("text", "") or ""
            if not raw.strip() or raw.strip() == "<>":
                return
            p = e.dxf.get("text_midpoint") or e.dxf.defpoint
            rot = 0.0
        else:
            return
        sh = src.sheet_of(p.x, p.y)
        if sh not in SHEETS:
            return
        fam = LT.font_family(styles.get(str(e.dxf.get("style", "STANDARD")).upper(), "")) if t != "DIMENSION" else None
        out.append({"id": ident, "sheet": sh, "type": t, "layer": layer, "raw": raw.strip(),
                    "decoded": LT.decode(raw, fam)["text"] if fam else None, "p": src.local(sh, p.x, p.y),
                    "rotation": round(rot, 3)})

    def walk(e, prefix, depth):
        ident = f"{prefix}{e.dxf.handle}" if e.dxf.handle else None
        if e.dxftype() == "INSERT":
            for k, a in enumerate(e.attribs):
                add(a, f"{prefix}{e.dxf.handle}@{k}")
            if depth < 4:
                for k, v in enumerate(e.virtual_entities()):
                    walk_virtual(v, f"{prefix}{e.dxf.handle}:{e.dxf.name}>{k}", depth + 1)
            return
        add(e, ident)

    def walk_virtual(v, ident, depth):
        if v.dxftype() == "INSERT":
            for k, a in enumerate(v.attribs):
                add(a, f"{ident}@{k}")
            if depth < 4:
                for k, w in enumerate(v.virtual_entities()):
                    walk_virtual(w, f"{ident}>{k}", depth + 1)
            return
        add(v, ident)

    for e in msp:
        walk(e, "", 0)
    return out


def hatches(src):
    out = []
    for e in src.msp.query("HATCH"):
        if e.dxf.layer != "S-HAT.BAT":
            continue
        pts = []
        for path in e.paths:
            if hasattr(path, "vertices"):
                pts += [(v[0], v[1]) for v in path.vertices]
            else:
                pts += [(ed.start[0], ed.start[1]) for ed in path.edges if hasattr(ed, "start")]
        if not pts:
            continue
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        sh = src.sheet_of(cx, cy)
        if sh not in SHEETS:
            continue
        lp = [src.local(sh, *p) for p in pts]
        out.append({"handle": e.dxf.handle, "sheet": sh, "pattern": e.dxf.pattern_name,
                    "scale": round(float(e.dxf.pattern_scale), 3), "bbox": [round(v, 1) for v in bbox(lp)],
                    "centre": src.local(sh, cx, cy)})
    return out


# ------------------------------------------------------------------ build
def build():
    frozen, vis = verify_inputs()
    src = S.Source(DXF)
    E = src.entities()
    s1p = _j(S1 / "SLAB_PANEL_REGISTER.json")["rows"]
    s1t = _j(S1 / "SLAB_REBAR_SOURCE_REGISTER.json")["rows"]
    s1rules = {r["rule_id"]: r for r in _j(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"]}
    check(BRIEF_RULES <= set(s1rules), "the slab rules are in the frozen S1 rule register")
    beams = _j(S1 / "BEAM_OCCURRENCE_REGISTER.json")["rows"]
    r4t = _j(R4 / "TEMPERATURE_REBAR_RULE_REGISTER.json")
    r4d = _j(R4 / "SLAB_DETAIL_RULE_REGISTER.json")
    d12 = _j(D12 / "02_COVER_BASIS.json")
    for t in s1t:                       # S1 spells a printed count ABSOLUTE_COUNT
        if t.get("count_mode") == "ABSOLUTE_COUNT":
            t["count_mode"] = SR.COUNT_EXPLICIT
    panels = [r for r in s1p if r["sheet"] in SHEETS]
    pidx = {r["panel_id"]: r for r in panels}
    tokens_s1 = [t for t in s1t if t["sheet"] in SHEETS]
    zones = {sh: S.detail_zones(src, sh) for sh in SHEETS}

    # ---------------------------------------------------- the p.15 rules and the note box, re-read
    temp_table = {int(k): v for k, v in s1rules["P15-TEMP-TABLE"]["values"]["rows"].items()}
    check(set(temp_table) == {int(k) for k in vis["p15_temperature"]["rows"]}, "temperature table rows agree")
    check(all(v.replace(" ", "") == vis["p15_temperature"]["rows"][str(k)].replace(" ", "")
              for k, v in temp_table.items()), "temperature table values agree")
    check(vis["p15_slab_on_beams_detail"]["span_basis"]["L1"].startswith("CLEAR_SPAN"), "L1 read as clear span")
    texts = sweep_texts(src)
    note2 = {}
    for sh in SHEETS:
        box = [t for t in texts if t["sheet"] == sh and t["layer"] == "S-TITLE TEXT"]
        ar = " ".join(t["decoded"] for t in sorted(box, key=lambda t: -t["p"][1]) if t["decoded"])
        rate = [t for t in box if REBAR.search(t["raw"])]
        check("فوق" in ar and "ثلث البحر" in ar and "الاتجاهين" in ar, f"{sh}: plan note 2 decoded")
        check(len(rate) == 1 and rate[0]["raw"].upper() == "5%%C10/M", f"{sh}: plan note 2 bar size")
        note2[sh] = {"arabic": ar, "bar": "5Ø10/m", "token_id": rate[0]["id"],
                     "handles": sorted(t["id"] for t in box)}
    note2_en = ("top steel 5Ø10/m for the slabs over the beams, length one third of the span, in both directions")
    cover = SR.cover_basis(s1rules["P8-N22"]["raw_text"], MIN_COVER_MM)
    check(cover["basis"] == CA.MINIMUM_PROJECT_COVER and cover["label"] == "MINIMUM_PROJECT_COVER_25",
          "slab cover 25 mm is a minimum")
    check(d12["basis"]["basis"] == CA.MINIMUM_PROJECT_COVER, "D1.2 binding: note 22 is a minimum")

    # ---------------------------------------------------- non-panel geometry evidence
    H = hatches(src)
    wide = [h for h in H if abs(h["scale"] - WIDE_HATCH_SCALE) < 1]
    dense = [h for h in H if abs(h["scale"] - DENSE_HATCH_SCALE) < 1]
    check(len(wide) + len(dense) == len(H), "every S-HAT.BAT hatch is one of the two legend scales")
    sunken = {}
    for h in wide:
        hit = [r["panel_id"] for r in panels if r["sheet"] == h["sheet"] and in_face(h["centre"], r)]
        check(len(hit) == 1, f"wide hatch {h['handle']} lies in one panel")
        pb = bbox(pidx[hit[0]]["polygon_mm"])
        check(all(abs(a - b) <= 60 for a, b in zip(h["bbox"], pb)), f"wide hatch {h['handle']} fills its panel")
        sunken[hit[0]] = h["handle"]
    dense_rows = []
    for h in dense:
        hit = [r["panel_id"] for r in panels if r["sheet"] == h["sheet"] and r["class"] == "SLAB_PANEL"
               and in_face(h["centre"], r)]
        check(not hit, f"dense hatch {h['handle']} lies outside every slab panel")
        dense_rows.append(h)
    tank_texts = [t for t in texts if "WATER TANK" in t["raw"].upper()]
    check(len(tank_texts) == 1, "one WATER TANK PLACE text")
    tank = tank_texts[0]
    clouds = []
    for e in E[tank["sheet"]]:
        if e["type"] == "LWPOLYLINE" and e.get("has_bulge") and len(e["pts"]) > 12:
            clouds.append(e)
    near = [c for c in clouds if min(math.dist(tank["p"], q) for q in c["pts"]) < 2500]
    check(len(near) == 1, "one revision cloud beside the WATER TANK PLACE text")

    def centre(r):
        b = bbox(r["polygon_mm"])
        return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    tank_panels = sorted(r["panel_id"] for r in panels if r["sheet"] == tank["sheet"] and r["class"] == "SLAB_PANEL"
                         and SC.point_in_ring(centre(r), near[0]["pts"]))
    tank_cloud = near[0]["handle"]
    check(len(tank_panels) == 2, f"the water-tank cloud holds two panels: {tank_panels}")
    void_inserts = [e for sh in SHEETS for e in E[sh] if e["type"] == "INSERT" and e.get("name") == "void"]
    opening_lines = {sh: [e for e in E[sh] if e["layer"] == "S-OPENING" and e["type"] == "LINE"] for sh in SHEETS}
    rein = {sh: [e for e in E[sh] if e["layer"] in ("S-REIN-SLAB", "S-REIN-CORNER") and
                 e["type"] in ("LINE", "LWPOLYLINE")] for sh in SHEETS}
    roof_marks = {sh: [t for t in texts if t["sheet"] == sh and (t["raw"].upper().startswith("ROOF") or
                                                                 re.fullmatch(r"\+\d+\.\d\d", t["raw"]))]
                  for sh in SHEETS}

    # ---------------------------------------------------- tokens per panel (S1 bindings) and thickness marks
    tok_by_panel = defaultdict(list)
    for t in tokens_s1:
        if t["owner"] == "SLAB" and t.get("panel"):
            tok_by_panel[t["panel"]].append(t)
    gf_void_conflict = None

    # ---------------------------------------------------- 01 census + scope
    census = []
    scope_of = {}
    for r in panels:
        pid, cls = r["panel_id"], r["class"]
        toks = tok_by_panel.get(pid, [])
        tmarks = r["local_thickness_notes"] or []
        void = bool(r["void_evidence"]["x_lines"] or r["void_evidence"]["void_texts"])
        special = []
        if cls in ("STAIR_FLIGHT_ZONE", "STAIR_IN_VOID_ZONE") or (r.get("stair_treads") or 0) >= 4:
            special.append("STAIR")
        if cls == "DOME_ZONE":
            special.append("DOME")
        designated = ["WATER_TANK"] if pid in tank_panels else []
        outside = cls == "OUTSIDE_BUILDING_OR_COURT"
        slab_ev = bool(toks or tmarks)
        if cls == "DOME_ZONE":
            void = False          # dome radials sit on S-OPENING: they are the dome's lines, not an open-to-below X
        sd = SR.scope_decision(slab_face=cls == "SLAB_PANEL" or cls in ("STAIR_FLIGHT_ZONE", "DOME_ZONE"),
                               outside=outside, void=void, special=special if not void else special,
                               designated_special=designated, slab_evidence=slab_ev)
        if cls == "STAIR_IN_VOID_ZONE":
            gf_void_conflict = SR.void_conflict(
                void_marks=r["void_evidence"]["x_lines"] + r["void_evidence"]["void_texts"],
                slab_marks=[f"T {m['value_cm']} ({m['handle']})" for m in tmarks] +
                           [f"{t['raw']} ({t['text_handle']})" for t in toks] + [f"{r['stair_treads']} stair treads"])
        x0, y0, x1, y1 = bbox(r["polygon_mm"])
        rect_ok = r["rectangularity"] is not None and r["rectangularity"] >= RECT_MIN and axis_aligned(r)
        panel_class = ("SUNKEN_SLAB" if pid in sunken else "NORMAL_SLAB") if cls == "SLAB_PANEL" else cls
        if pid in tank_panels:
            panel_class = "WATER_TANK_PLACE_SLAB"
        notes = []
        if outside and roof_marks[r["sheet"]] and any(in_face(t["p"], r) for t in roof_marks[r["sheet"]]):
            notes.append("ROOF / level marks inside: the roof of the floor below seen on this sheet; its slab is on "
                         "that floor's sheet")
        if pid in sunken:
            notes.append(f"wide legend hatch {sunken[pid]} (Sunken slab) fills the panel")
        census.append({"SLAB_PANEL_ID": pid, "FLOOR": FLOOR[r["sheet"]], "SOURCE_SHEET": r["sheet"],
                       "S1_CLASS": cls, "PANEL_CLASS": panel_class, "SCOPE": sd["scope"],
                       "SCOPE_REASON": sd["why"], "SPECIAL": sd.get("special"), "CONFLICT": sd.get("conflict"),
                       "BOUNDARY_HANDLES": r["boundary_handles"], "_edges": r["edges"] or [],
                       "GEOMETRIC_AREA_M2": r["area_m2"], "RECTANGULARITY": r["rectangularity"],
                       "BBOX_MM": [round(v) for v in (x0, y0, x1, y1)],
                       "CLEAR_SPAN_X_MM": _r(x1 - x0) if rect_ok else None,
                       "CLEAR_SPAN_Y_MM": _r(y1 - y0) if rect_ok else None,
                       "SPAN_STATE": "SINGLE_VALUED_FACE_TO_FACE" if rect_ok else "NOT_SINGLE_VALUED",
                       "THICKNESS_MARKS": [{"value_mm": m["value_cm"] * 10, "handle": m["handle"]} for m in tmarks],
                       "TOKENS": sorted(t["text_handle"] for t in toks), "VOID_EVIDENCE": r["void_evidence"],
                       "STAIR_TREADS": r["stair_treads"], "NOTES": notes})
        scope_of[pid] = sd["scope"]
    for h in dense_rows:
        hid = f"HZ-{h['sheet']}-{h['handle']}"
        sd = SR.scope_decision(slab_face=False)
        census.append({"SLAB_PANEL_ID": hid, "FLOOR": FLOOR[h["sheet"]], "SOURCE_SHEET": h["sheet"],
                       "S1_CLASS": "NOT_A_FACE", "PANEL_CLASS": "DENSE_HATCH_CANTILEVER_OR_BEARING_WALL",
                       "SCOPE": sd["scope"], "SCOPE_REASON": "the legend draws the cantilever portion and the bearing "
                                                             "wall with the same dense hatch",
                       "SPECIAL": None, "CONFLICT": None, "BOUNDARY_HANDLES": [h["handle"]], "_edges": [],
                       "GEOMETRIC_AREA_M2": _r((h["bbox"][2] - h["bbox"][0]) * (h["bbox"][3] - h["bbox"][1]) / 1e6, 3),
                       "RECTANGULARITY": None, "BBOX_MM": [round(v) for v in h["bbox"]], "CLEAR_SPAN_X_MM": None,
                       "CLEAR_SPAN_Y_MM": None, "SPAN_STATE": "NOT_A_PANEL", "THICKNESS_MARKS": [], "TOKENS": [],
                       "VOID_EVIDENCE": None, "STAIR_TREADS": None,
                       "NOTES": [f"dense legend hatch {h['handle']} (scale {h['scale']:g}), outside every slab face"]})
        scope_of[hid] = sd["scope"]
    check(gf_void_conflict and gf_void_conflict["state"] == SR.SOURCE_CONFLICT, "the void + stair face is a conflict")

    # ---------------------------------------------------- beam widths, supports
    bw = defaultdict(set)
    for b in beams:
        if b.get("sheet") in SHEETS and b.get("member") and b.get("width_drawn_mm"):
            bw[(b["sheet"], b["member"])].add(round(float(b["width_drawn_mm"])))
    pid_scope = {c["SLAB_PANEL_ID"]: c for c in census}

    def support_type(e, me):
        nb = e["neighbour_panel"]
        if e["support"] != "BEAM":
            return SR.CONTINUITY_UNRESOLVED, f"edge support is {e['support']} (the typical detail is slab on beams)"
        if nb is None:
            return SR.NON_CONTINUOUS, "no slab beyond the support"
        nc = pid_scope[nb]
        if nc["SCOPE"] in (SR.NOT_SLAB, SR.VOID_OR_OPENING):
            return SR.NON_CONTINUOUS, f"beyond the support: {nc['S1_CLASS']}"
        if nc["SCOPE"] == SR.IN_SCOPE:
            if (me in sunken) != (nb in sunken):
                return SR.CONTINUITY_UNRESOLVED, "a sunken slab on one side: level step not detailed"
            return SR.CONTINUOUS, "slab panel on both sides"
        return SR.CONTINUITY_UNRESOLVED, f"beyond the support: {nc['PANEL_CLASS']} ({nc['SCOPE']})"

    edge_views = []
    for c in census:
        pid = c["SLAB_PANEL_ID"]
        if pid not in pidx or c["SCOPE"] not in (SR.IN_SCOPE, SR.CLASSIFICATION_BLOCKED):
            continue
        r = pidx[pid]
        for e in c["_edges"]:
            a, b, ori = edge_geom(r, e["edge_index"])
            st, why = support_type(e, pid)
            edge_views.append({"panel": pid, "neighbour": e["neighbour_panel"], "support_ref": e["support_ref"],
                               "edge_index": e["edge_index"], "length_mm": e["length_m"] * 1000, "continuity":
                               e["continuity"], "_ori": ori, "_side": side_of_edge(r, a, b, ori), "_type": st,
                               "_why": why, "_sheet": r["sheet"], "_support": e["support"]})
    sups = SR.supports_from_edges(edge_views)
    producing = {v["panel"] for v in edge_views}
    view_of = {(v["panel"], v["edge_index"]): v for v in edge_views}
    supports = []
    for k, s in enumerate(sups):
        views = [view_of[x] for x in s["views"]]
        v0 = max(views, key=lambda v: (v["length_mm"], v["panel"], v["edge_index"]))
        sheet = v0["_sheet"]
        types = sorted({v["_type"] for v in views})
        stype = types[0] if len(types) == 1 else SR.CONTINUITY_UNRESOLVED
        slab_sides = [p for p in s["sides"] if not str(p).startswith(SR.EXTERIOR)]
        ori = v0["_ori"]
        lo_hi = []
        for p in slab_sides:
            pb = bbox(pidx[p]["polygon_mm"]) if p in pidx else None
            lo_hi.append((p, ((pb[0] + pb[2]) / 2) if ori == "V" else ((pb[1] + pb[3]) / 2)))
        lo_hi.sort(key=lambda t: t[1])
        left = lo_hi[0][0] if lo_hi else None
        right = lo_hi[1][0] if len(lo_hi) > 1 else None
        if len(lo_hi) == 1:
            side = v0["_side"]
            left, right = ((None, lo_hi[0][0]) if side in ("W", "S") else (lo_hi[0][0], None))
        widths = sorted(bw.get((sheet, s["support_ref"]), set()))
        supports.append({"SUPPORT_ID": f"SUP-{FLOOR[sheet]}-{k + 1:03d}", "SHEET": sheet, "FLOOR": FLOOR[sheet],
                         "SUPPORT_REF": s["support_ref"], "SUPPORT_KIND": v0["_support"], "ORIENTATION": ori,
                         "LEFT_PANEL": left, "RIGHT_PANEL": right, "SIDES": list(s["sides"]),
                         "SEEN_FROM": s["seen_from"], "VIEWS": [f"{p}#{i}" for p, i in s["views"]],
                         "VIEWS_SYMMETRIC": {p for p in s["sides"] if p in producing} <= set(s["seen_from"]),
                         "SUPPORT_TYPE": stype,
                         "MIXED_ORIENTATION": len({v["_ori"] for v in views}) > 1,
                         "SUPPORT_TYPE_WHY": "; ".join(sorted({v["_why"] for v in views})),
                         "LENGTH_MM": _r(max(s["lengths_mm"])), "SUPPORT_WIDTH_MM": widths[0] if len(widths) == 1
                         else None, "_views": views,
                         "BARS_CROSSING": "X" if ori == "V" else "Y",
                         "COUNT_DIRECTION": "ALONG_SUPPORT (" + ("Y" if ori == "V" else "X") + ")"})
    sup_by_view = {}
    for s in supports:
        for v in s["_views"]:
            sup_by_view[(v["panel"], v["edge_index"])] = s

    # ---------------------------------------------------- centreline spans
    def side_width(pid, side):
        ws = set()
        for e in pidx[pid]["edges"] or []:
            s = sup_by_view.get((pid, e["edge_index"]))
            a, b, ori = edge_geom(pidx[pid], e["edge_index"])
            if side_of_edge(pidx[pid], a, b, ori) == side:
                ws.add(s["SUPPORT_WIDTH_MM"] if s else None)
        return ws.pop() if len(ws) == 1 else None
    for c in census:
        pid = c["SLAB_PANEL_ID"]
        c["SUPPORT_CENTERLINE_SPAN_X_MM"] = c["SUPPORT_CENTERLINE_SPAN_Y_MM"] = None
        if pid in pidx and c["CLEAR_SPAN_X_MM"] and c["SCOPE"] in (SR.IN_SCOPE, SR.CLASSIFICATION_BLOCKED):
            c["SUPPORT_CENTERLINE_SPAN_X_MM"] = SR.spans(c["CLEAR_SPAN_X_MM"], side_width(pid, "W"),
                                                         side_width(pid, "E"))["centreline_mm"]
            c["SUPPORT_CENTERLINE_SPAN_Y_MM"] = SR.spans(c["CLEAR_SPAN_Y_MM"], side_width(pid, "S"),
                                                         side_width(pid, "N"))["centreline_mm"]
        c["SUPPORT_EDGES"] = [f"{e['edge_index']}:{e['support']}:{e['support_ref']}:{e['continuity']}"
                              for e in c["_edges"]]
        c["ADJACENT_PANEL_IDS"] = sorted({e["neighbour_panel"] for e in c["_edges"] if e["neighbour_panel"]})

    # ---------------------------------------------------- 02 thickness
    default_vals = [s1rules["P8-N18"]["values"]["t_mm"], s1rules["P1-NOTE-A"]["values"]["t_mm"]]
    thick_rows = []
    thickness_of = {}
    r4_2f = [f for f in r4t["floors"] if f["floor"] == "2F"][0]
    for c in census:
        pid = c["SLAB_PANEL_ID"]
        if c["SCOPE"] in (SR.NOT_SLAB, SR.VOID_OR_OPENING) or pid not in pidx:
            continue
        marks = [m["value_mm"] for m in c["THICKNESS_MARKS"]]
        if c["SCOPE"] == SR.IN_SCOPE or pid in tank_panels:
            d = SR.thickness_decision(local=marks, floor=[], default=default_vals)
        else:                    # stairs, domes, the void / stair conflict face: not decided in this round
            d = {"value_mm": None, "authority": c["SCOPE"], "level": None, "values_mm": marks, "overridden": [],
                 "confirms": []}
        thickness_of[pid] = d
        c["THICKNESS_MM"] = d["value_mm"]
        c["THICKNESS_AUTHORITY"] = d["authority"]
        prior = None
        if c["FLOOR"] == "2F_ROOF_SLAB":
            prior = (f"R4 TEMPERATURE register gave the whole 2F floor {r4_2f['thickness_mm']} mm "
                     f"({r4_2f['thickness_source']}); the source has two T 18 marks only, inside two panels")
        thick_rows.append({"SLAB_PANEL_ID": pid, "FLOOR": c["FLOOR"], "SCOPE": c["SCOPE"],
                           "PANEL_CLASS": c["PANEL_CLASS"], "LOCAL_PANEL_MARKS": c["THICKNESS_MARKS"],
                           "FLOOR_RULE": "NONE_FOUND", "PROJECT_DEFAULT_MM": 160,
                           "PROJECT_DEFAULT_SOURCES": "P8-N18 (p.8 note 18) + P1-NOTE-A (p.1 note)",
                           "EFFECTIVE_THICKNESS_MM": d["value_mm"], "AUTHORITY": d["authority"],
                           "OVERRIDDEN": d["overridden"], "CONFIRMS": d.get("confirms"),
                           "SUNKEN": pid in sunken, "DROP_DEPTH": "SOURCE_EXPECTED_NOT_LOCATED" if pid in sunken
                           else None, "PRIOR_REGISTER_NOTE": prior,
                           "STATE": "SOURCE_CONFLICT" if d["authority"] == SR.SOURCE_CONFLICT else "RESOLVED" if
                           d["value_mm"] else "NOT_DECIDED_OUT_OF_SCOPE"})
    for c in census:
        c.setdefault("THICKNESS_MM", None)
        c.setdefault("THICKNESS_AUTHORITY", None)

    # ---------------------------------------------------- '/Top' callouts: do their bars cross a support?
    def graphic_near(sh, pt):
        g = None
        for e in rein[sh]:
            pts = e.get("pts") or [e["a"], e["b"]]
            d0 = min(math.dist(q, pt) for q in pts)
            if g is None or d0 < g[0]:
                g = (d0, e)
        return g[1] if g and g[0] < 1500 else None
    top_verdict = {}
    for t in tokens_s1:
        if not (t["owner"] == "SLAB_SUPPORT_TOP_BAR" or (t["owner"] == "SLAB" and t["layer"] == "TOP")):
            continue
        sh = t["sheet"]
        gs = graphic_near(sh, t["position_mm"])
        gpts = (gs.get("pts") or [gs["a"], gs["b"]]) if gs else []
        touched = sorted({r["panel_id"] for r in panels if r["sheet"] == sh and r["class"] == "SLAB_PANEL"
                          for q in gpts if in_face(q, r)})
        cand = [s_ for s_ in supports if s_["SHEET"] == sh and len(touched) == 2 and
                {s_["LEFT_PANEL"], s_["RIGHT_PANEL"]} == set(touched)]
        if len(cand) == 1:
            top_verdict[t["text_handle"]] = {"state": SR.BOUND_TO_SUPPORT, "support": cand[0]["SUPPORT_ID"],
                                             "graphic": gs["handle"], "touched": touched,
                                             "why": "the drawn bar crosses the support between the two panels"}
        else:
            top_verdict[t["text_handle"]] = {
                "state": SR.SOURCE_CONFLICT, "support": None, "graphic": gs["handle"] if gs else None,
                "touched": touched, "why": "the drawn '/Top' bar runs beside a beam line outside every slab panel "
                                           "(parallel to the support, not across it): beam top bars drawn beside the "
                                           "beam, edge / cantilever bars, or slab support bars"}
    for v in top_verdict.values():
        if v["support"]:
            [s_ for s_ in supports if s_["SUPPORT_ID"] == v["support"]][0].setdefault("_explicit_top", [])

    # ---------------------------------------------------- 03 tokens
    s1_by_pos = {}
    for t in tokens_s1:
        s1_by_pos[(t["sheet"], round(t["position_mm"][0]), round(t["position_mm"][1]), t["raw"])] = t
    swept = [t for t in texts if REBAR.search(t["raw"])]
    seen_pos = {}
    tok_rows, tok_recs = [], []
    family_token = {}
    s1_matched = set()
    qualifiers_claimed = {t["tb_text_handle"] for t in tokens_s1 if t.get("tb_text_handle")}
    fam_of_panel_dir = defaultdict(list)
    for t in tokens_s1:
        if t["owner"] == "SLAB" and t.get("panel") and t["direction"] in ("X", "Y") and t["layer"] != "TOP":
            fam_of_panel_dir[(t["panel"], t["direction"])].append(t["text_handle"])
    for t in sorted(swept, key=lambda t: (t["sheet"], t["id"])):
        key = (t["sheet"], round(t["p"][0]), round(t["p"][1]), t["raw"])
        s1 = s1_by_pos.get(key)
        dup = [o for o in seen_pos.get((t["sheet"], t["raw"]), []) if math.dist(o["p"], t["p"]) <= DUP_TOL_MM]
        seen_pos.setdefault((t["sheet"], t["raw"]), []).append(t)
        families, bound_to, kind = [], None, "BAR_CALLOUT"
        if dup:
            state, why = SR.DUPLICATE_GRAPHIC, f"same text within {DUP_TOL_MM:g} mm of {dup[0]['id']}"
        elif t["raw"].upper().replace(" ", "") == "(T&B)":
            kind = "QUALIFIER"
            claimers = [x for x in tokens_s1 if x.get("tb_text_handle") == t["id"]]
            if claimers:
                state, bound_to = SR.BOUND_TO_PANEL, claimers[0]["panel"]
                why = f"(T&B) qualifier of {', '.join(sorted(x['text_handle'] for x in claimers))}"
            else:
                state, why = SR.UNBOUND, "qualifier claimed by no callout"
        elif s1 is None:
            if any(z[0] - ZONE_MARGIN_MM <= t["p"][0] <= z[2] + ZONE_MARGIN_MM and
                   z[1] - ZONE_MARGIN_MM <= t["p"][1] <= z[3] + ZONE_MARGIN_MM for z in zones[t["sheet"]]):
                state, why, kind = SR.REFERENCE_ONLY, "in or beside a section / detail drawing on the plan sheet", \
                    "SECTION_LABEL"
            else:
                state, why = SR.UNBOUND, "rebar-like text not registered by S1"
        else:
            s1_matched.add(s1["source_row_id"])
            own = s1["owner"]
            if own == "PLAN_NOTE":
                state, why, kind = SR.DESIGN_NOTE, "plan note 2 (P4-6-NOTE-2): top steel over beams, floor rule", \
                    "RULE_NOTE"
            elif own == "SECTION_DETAIL":
                state, why, kind = SR.REFERENCE_ONLY, "section detail on the plan sheet (beam section)", \
                    "SECTION_LABEL"
            elif own == "PLANTED_COLUMN_LABEL":
                state, why, kind = SR.REFERENCE_ONLY, "planted-column reinforcement label (column scope)", \
                    "COLUMN_LABEL"
            elif own == "SLAB_SUPPORT_TOP_BAR" or (own == "SLAB" and s1["layer"] == "TOP"):
                v = top_verdict[s1["text_handle"]]
                state, kind, why = v["state"], "SUPPORT_TOP_BAR", v["why"]
                bound_to = v["support"]
                if state == SR.BOUND_TO_SUPPORT:
                    families = [f"TOPSUP:{v['support']}:{s1['text_handle']}"]
            elif own == "SLAB":
                p = s1["panel"]
                sc = scope_of.get(p)
                fams = fam_of_panel_dir.get((p, s1["direction"]), [])
                if sc == SR.EXCLUDED_SPECIAL:
                    state, why = SR.EXCLUDED_SPECIAL_TOKEN, f"bound to {p} ({pid_scope[p]['PANEL_CLASS']})"
                elif pid_scope[p]["CONFLICT"] == SR.SOURCE_CONFLICT:
                    state, why = SR.SOURCE_CONFLICT, f"bound to {p}: void and stair / slab evidence in one face"
                elif s1["direction"] not in ("X", "Y"):
                    state, kind = SR.BOUND_TO_PANEL, "CORNER_BAR" if s1.get("corner_reinforcement") else "DIAGONAL"
                    bound_to, families = p, [f"{p}:{s1['direction']}:{s1['text_handle']}"]
                    why = "corner reinforcement callout (S-TEXT-CORNER), diagonal"
                elif len(fams) > 1:
                    state, bound_to = SR.SOURCE_CONFLICT, p
                    why = f"{len(fams)} callouts for one panel and direction ({', '.join(sorted(fams))})"
                else:
                    state, bound_to = SR.BOUND_TO_PANEL, p
                    families = [f"{p}:{s1['direction']}"]
                    why = f"inside {p}; {s1.get('note') or ''}".strip()
                if families:
                    family_token[families[0]] = s1
            else:
                state, why = SR.UNBOUND, f"S1 owner {own}"
        rec = SR.terminate_token(t["id"], state, bar_families=families, bound_to=bound_to, reason=why)
        tok_recs.append(rec)
        parsed = SC.parse_slab_rebar(t["raw"].replace("Ø", "%%c")) or {}
        tok_rows.append({"TOKEN_ID": t["id"], "SHEET": t["sheet"], "FLOOR": FLOOR[t["sheet"]], "ENTITY": t["type"],
                         "LAYER": t["layer"], "RAW": t["raw"], "POSITION_MM": [round(v, 1) for v in t["p"]],
                         "ROTATION_DEG": t["rotation"], "KIND": kind, "S1_SOURCE_ROW": s1["source_row_id"] if s1
                         else None, "DIA_MM": parsed.get("dia_mm"), "COUNT_OR_RATE": parsed.get("count"),
                         "COUNT_MODE": parsed.get("count_mode"), "LAYER_QUALIFIER": (s1 or {}).get("layer"),
                         "DIRECTION": (s1 or {}).get("direction"), "TERMINAL_STATE": state, "BOUND_TO": bound_to,
                         "BAR_FAMILIES": families, "REASON": why})
    unmatched_s1 = [t["source_row_id"] for t in tokens_s1 if t["source_row_id"] not in s1_matched]
    check(not unmatched_s1, f"every S1 slab-sheet token found again by the sweep: {unmatched_s1}")
    tcons = SR.token_conservation([t["id"] for t in swept], tok_recs)
    check(tcons["all_pass"], f"token conservation {tcons}")

    # ---------------------------------------------------- bottom families, runs
    fam_rows = []
    for fid, t in sorted(family_token.items()):
        p = t["panel"]
        c = pid_scope[p]
        if t["direction"] not in ("X", "Y") or t["layer"] == "TOP":
            continue
        fam_rows.append({"family_id": fid, "panel": p, "direction": t["direction"], "dia_mm": t["dia_mm"],
                         "rate": t["count"] if t["count_mode"] == "BARS_PER_METRE" else None,
                         "count_mode": t["count_mode"], "count": t["count"], "token": t["text_handle"],
                         "layer": t["layer"], "scope": c["SCOPE"]})
    run_families = [f for f in fam_rows if f["scope"] == SR.IN_SCOPE]
    links = [{"support_id": s["SUPPORT_ID"], "panels": tuple(s["SIDES"]), "direction": s["BARS_CROSSING"],
              "support_type": s["SUPPORT_TYPE"]} for s in supports if s["LEFT_PANEL"] and s["RIGHT_PANEL"]]
    runs = SR.bar_runs(run_families, links)
    sup_idx = {s["SUPPORT_ID"]: s for s in supports}
    fam_idx = {f["family_id"]: f for f in fam_rows}
    run_of_family = {}
    run_rows = []
    for k, rn in enumerate(runs["runs"]):
        rid = f"RUN-B-{k + 1:03d}"
        for f in rn["families"]:
            run_of_family[f] = rid
        d = rn["direction"]
        crossed = [sup_idx[s] for s in rn["supports_crossed"]]
        aligned = True
        for s in crossed:
            a, b = pidx[s["LEFT_PANEL"]], pidx[s["RIGHT_PANEL"]]
            ba, bb = bbox(a["polygon_mm"]), bbox(b["polygon_mm"])
            lo = (1, 3) if d == "X" else (0, 2)
            if abs(ba[lo[0]] - bb[lo[0]]) > ALIGN_TOL_MM or abs(ba[lo[1]] - bb[lo[1]]) > ALIGN_TOL_MM:
                aligned = False
        deg = Counter(p for s in crossed for p in (s["LEFT_PANEL"], s["RIGHT_PANEL"]))
        chain = all(v <= 2 for v in deg.values())
        ends = []
        for f in rn["families"]:
            p = fam_idx[f]["panel"]
            for e in pidx[p]["edges"] or []:
                s = sup_by_view.get((p, e["edge_index"]))
                if s and s["BARS_CROSSING"] == d and s["SUPPORT_ID"] not in rn["supports_crossed"]:
                    ends.append(f"{s['SUPPORT_ID']}:{s['SUPPORT_TYPE']}")
        known = None
        if rn["multi_panel"] and aligned and chain and all(pid_scope[fam_idx[f]["panel"]]["CLEAR_SPAN_X_MM"]
                                                           for f in rn["families"]):
            bbs = [bbox(pidx[fam_idx[f]["panel"]]["polygon_mm"]) for f in rn["families"]]
            known = _r(max(b[2] for b in bbs) - min(b[0] for b in bbs)) if d == "X" else \
                _r(max(b[3] for b in bbs) - min(b[1] for b in bbs))
        tok = sorted({fam_idx[f]["token"] for f in rn["families"]})
        blocked = ["end anchorage into the end supports (shape only)", "lap / splice positions (not located)"]
        if any("CONTINUITY_UNRESOLVED" in e for e in ends):
            blocked.append("behaviour at a support whose continuity is unresolved")
        run_rows.append({"BAR_RUN_ID": rid, "KIND": "BOTTOM_BALANCE_CONTINUOUS" if rn["multi_panel"] else
                         "BOTTOM_SINGLE_PANEL", "BAR_MARK_TOKEN": tok, "DIAMETER_MM": rn["dia_mm"],
                         "SPACING_MM": _r(rn["spacing_mm"]) if rn["spacing_mm"] else None, "DIRECTION": d,
                         "PANELS_CROSSED": rn["panels"], "SUPPORTS_CROSSED": rn["supports_crossed"],
                         "START_CONDITION": sorted(ends)[0] if ends else None,
                         "END_CONDITION": sorted(ends)[-1] if len(ends) > 1 else None, "END_SUPPORTS": sorted(ends),
                         "ALIGNMENT": ("FULL_CHAIN" if aligned and chain else "PARTIAL") if rn["multi_panel"] else
                         "SINGLE_PANEL", "KNOWN_STRAIGHT_EXTENT_MM": known,
                         "KNOWN_EXTENT_BASIS": "face to face of the run's end supports (project-source panel faces) "
                                               "under the p.15 'balance continuous' rule" if known else None,
                         "BLOCKED_EXTENT": blocked, "COUNTED_ONCE": True})
    for m in runs["mismatches"]:
        pass
    top_runs = []
    for s in supports:
        if s["SUPPORT_KIND"] != "BEAM":
            continue
        rid = f"RUN-T-{s['SUPPORT_ID'][4:]}"
        s["BAR_RUN_ID"] = rid
        top_runs.append({"BAR_RUN_ID": rid, "KIND": "TOP_SUPPORT_BARS", "BAR_MARK_TOKEN": None,
                         "DIAMETER_MM": None, "SPACING_MM": None, "DIRECTION": s["BARS_CROSSING"],
                         "PANELS_CROSSED": [p for p in (s["LEFT_PANEL"], s["RIGHT_PANEL"]) if p],
                         "SUPPORTS_CROSSED": [s["SUPPORT_ID"]], "START_CONDITION": s["SUPPORT_TYPE"],
                         "END_CONDITION": s["SUPPORT_TYPE"], "END_SUPPORTS": [], "ALIGNMENT": "ONE_SUPPORT",
                         "KNOWN_STRAIGHT_EXTENT_MM": None, "KNOWN_EXTENT_BASIS": None,
                         "BLOCKED_EXTENT": ["extent: plan note 2 (1/3 span) vs p.15 (0.25 L1 / 0.30 max L)"],
                         "COUNTED_ONCE": True})

    sup_by_id = {s_["SUPPORT_ID"]: s_ for s_ in supports}
    for t in tok_rows:
        if t["TERMINAL_STATE"] == SR.BOUND_TO_SUPPORT:
            sup_by_id[t["BOUND_TO"]]["_explicit_top"].append(t)
    topsup = [{"token": h, **v} for h, v in sorted(top_verdict.items())]

    # ---------------------------------------------------- 06 support rules
    det = vis["p15_slab_on_beams_detail"]
    rules = [
        {"RULE_ID": "P15-TOP-NONCONT-0.25L1", "SOURCE_PAGE": 15, "SOURCE": "TYP.SLAB ON BEAMS DETAIL",
         "WORDING": ".25\"L1\"; TOP ANCHOR BARS. FOR SIZE & SPACING SEE SCHEDULE OR PLAN",
         "BAR_ROLE": "TOP_ANCHOR", "RULE_KIND": SR.TOP_NONCONT, "SPAN_DEFINITION": SR.CLEAR_SPAN,
         "MEASUREMENT_ORIGIN": SR.FACE_OF_SUPPORT, "APPLICABILITY": "slab on beams, non-continuous support",
         "CONTINUITY": SR.NON_CONTINUOUS, "DIRECTION": "perpendicular to the support",
         "WHICH_50_PERCENT": None, "ENDPOINT": "end of the top anchor bar inside the span; the other end turns "
                                                 "down into the support (leg drawn, not dimensioned)",
         "NTS_STATUS": det["nts_status"], "EVIDENCE": det["dimension_attachment"]["TOP_ANCHOR_NON_CONTINUOUS"]},
        {"RULE_ID": "P15-TOP-CONT-0.30Lmax", "SOURCE_PAGE": 15, "SOURCE": "TYP.SLAB ON BEAMS DETAIL",
         "WORDING": ".30\"L1\" OR .30\"L2\" WHICHEVER LARGER", "BAR_ROLE": "TOP_OVER_SUPPORT",
         "RULE_KIND": SR.TOP_CONT, "SPAN_DEFINITION": SR.CLEAR_SPAN, "MEASUREMENT_ORIGIN": SR.FACE_OF_SUPPORT,
         "APPLICABILITY": "slab on beams, continuous support", "CONTINUITY": SR.CONTINUOUS,
         "DIRECTION": "perpendicular to the support", "WHICH_50_PERCENT": None,
         "ENDPOINT": "dimensioned on the L1 side only; the L2-side extent is drawn, not dimensioned",
         "NTS_STATUS": det["nts_status"], "EVIDENCE": det["dimension_attachment"]["TOP_CONTINUOUS_WHICHEVER_LARGER"]},
        {"RULE_ID": "P15-BOT-STOP-0.125L", "SOURCE_PAGE": 15, "SOURCE": "TYP.SLAB ON BEAMS DETAIL",
         "WORDING": "STOP 50% OF BOT. REINF. BALANCE CONTINUOUS; .125\"L1\" / .125\"L2\"",
         "BAR_ROLE": "BOTTOM", "RULE_KIND": SR.BOTTOM_STOP, "SPAN_DEFINITION": SR.CLEAR_SPAN,
         "MEASUREMENT_ORIGIN": SR.FACE_OF_SUPPORT, "APPLICABILITY": "bottom bars at a continuous support",
         "CONTINUITY": SR.CONTINUOUS, "DIRECTION": "the bar direction (each span its own L)",
         "WHICH_50_PERCENT": "NOT_STATED", "ENDPOINT": "stopped bars end 0.125 L short of each continuous-support "
                                                       "face; the balance runs through the support",
         "NTS_STATUS": det["nts_status"], "EVIDENCE": det["dimension_attachment"]["BOTTOM_50PCT_STOP"]},
        {"RULE_ID": "P15-TOP-EXTEND-50PCT", "SOURCE_PAGE": 15, "SOURCE": "TYP.SLAB ON BEAMS DETAIL",
         "WORDING": "EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE POSSIBLE", "BAR_ROLE": "TOP_ANCHOR",
         "RULE_KIND": None, "SPAN_DEFINITION": SR.L_UNDEFINED, "MEASUREMENT_ORIGIN": None,
         "APPLICABILITY": "'where possible' is not defined", "CONTINUITY": SR.NON_CONTINUOUS,
         "DIRECTION": "perpendicular to the support", "WHICH_50_PERCENT": "NOT_STATED", "ENDPOINT": "not dimensioned",
         "NTS_STATUS": det["nts_status"], "EVIDENCE": "dashed bar beyond the non-continuous support"},
        {"RULE_ID": "P4-6-NOTE-2-TOP-OVER-BEAMS", "SOURCE_PAGE": "4-6",
         "SOURCE": "plan note box on each slab sheet (Arabic note 2 + 5Ø10/m)",
         "WORDING": f"{note2['GFRS']['arabic']} [5Ø10/m] - {note2_en}", "BAR_ROLE": "TOP_OVER_SUPPORT",
         "RULE_KIND": None, "SPAN_DEFINITION": SR.L_UNDEFINED, "MEASUREMENT_ORIGIN": None,
         "APPLICABILITY": "all slabs over beams, both directions (floor rule on each slab sheet)",
         "CONTINUITY": "NOT_STATED", "DIRECTION": "both directions",
         "WHICH_50_PERCENT": None, "ENDPOINT": "'length one third of the span': total bar length or extension each "
                                                "side is not stated; 'span' is not defined",
         "NTS_STATUS": "PLAN_NOTE", "EVIDENCE": "decoded legacy Arabic text (S-TITLE TEXT) + the 5%%C10/m text"},
        {"RULE_ID": "P15-TEMP-NOTE-2-STRIP", "SOURCE_PAGE": 15, "SOURCE": "TEMPERATURE notes",
         "WORDING": vis["p15_temperature"]["notes"][1], "BAR_ROLE": "TEMPERATURE_TOP",
         "RULE_KIND": None, "SPAN_DEFINITION": "NOT_A_SPAN_RULE (2000 mm strip, 1000 at spandrel)",
         "MEASUREMENT_ORIGIN": "NOT_STATED", "APPLICABILITY": "where beams are parallel to the MAIN slab "
                                                             "reinforcement: main direction undefined for two-way panels",
         "CONTINUITY": None, "DIRECTION": "at right angles to the beams", "WHICH_50_PERCENT": None,
         "ENDPOINT": "strip 2000 (1000 at spandrel); centring not stated", "NTS_STATUS": "TABLE_NOTE",
         "EVIDENCE": "p.15 temperature note 2"},
        {"RULE_ID": "P15-TEMP-NOTE-3-LARGER", "SOURCE_PAGE": 15, "SOURCE": "TEMPERATURE notes",
         "WORDING": vis["p15_temperature"]["notes"][2], "BAR_ROLE": "TOP_OVER_SUPPORT", "RULE_KIND": None,
         "SPAN_DEFINITION": None, "MEASUREMENT_ORIGIN": None,
         "APPLICABILITY": "a support between spans with different top reinforcement",
         "CONTINUITY": SR.CONTINUOUS, "DIRECTION": None, "WHICH_50_PERCENT": None,
         "ENDPOINT": None, "NTS_STATUS": "TABLE_NOTE", "EVIDENCE": "p.15 temperature note 3"},
        {"RULE_ID": "P15-TEMP-NOTE-1-LAP-40D", "SOURCE_PAGE": 15, "SOURCE": "TEMPERATURE notes",
         "WORDING": vis["p15_temperature"]["notes"][0], "BAR_ROLE": "TEMPERATURE", "RULE_KIND": None,
         "SPAN_DEFINITION": None, "MEASUREMENT_ORIGIN": None, "APPLICABILITY": "temperature bars only",
         "CONTINUITY": None, "DIRECTION": None, "WHICH_50_PERCENT": None, "ENDPOINT": "lap 40 x diameter",
         "NTS_STATUS": "TABLE_NOTE", "EVIDENCE": "p.15 temperature note 1"},
        {"RULE_ID": "P15-COVER-25CL", "SOURCE_PAGE": 15, "SOURCE": "TYP.SLAB ON BEAMS DETAIL",
         "WORDING": "25 CL (soffit to bottom bars); note 22: not less than 2.5 cm in slabs", "BAR_ROLE": "COVER",
         "RULE_KIND": None, "SPAN_DEFINITION": None, "MEASUREMENT_ORIGIN": None,
         "APPLICABILITY": "vertical cover (does not set a plan length)", "CONTINUITY": None, "DIRECTION": None,
         "WHICH_50_PERCENT": None, "ENDPOINT": None, "NTS_STATUS": det["nts_status"],
         "EVIDENCE": f"cover basis {cover['label']} (note 22 minimum, D1.2)"},
        {"RULE_ID": "P15-END-40CL", "SOURCE_PAGE": 15, "SOURCE": "TYP.SLAB ON BEAMS DETAIL",
         "WORDING": "40 CL. at the outer face of the non-continuous support", "BAR_ROLE": "END_COVER",
         "RULE_KIND": None, "SPAN_DEFINITION": None, "MEASUREMENT_ORIGIN": "outer face of the support",
         "APPLICABILITY": "which bar it dimensions is not legible", "CONTINUITY": SR.NON_CONTINUOUS,
         "DIRECTION": None, "WHICH_50_PERCENT": None, "ENDPOINT": "bar end", "NTS_STATUS": det["nts_status"],
         "EVIDENCE": det["covers"]["40 CL."]}]
    for ru in rules:
        if ru["RULE_KIND"]:
            g = SR.rule_gate(ru["RULE_KIND"], L_basis=ru["SPAN_DEFINITION"], direction="X",
                             support_type=ru["CONTINUITY"], origin=ru["MEASUREMENT_ORIGIN"])
            ru["GATE"] = g["state"]
            ru["GATE_BLOCKERS"] = g["blockers"]
        else:
            ru["GATE"] = SR.RULE_BLOCKED
            ru["GATE_BLOCKERS"] = ["NOT_A_NUMERIC_SPAN_RULE" if ru["SPAN_DEFINITION"] is None else "L_BASIS_UNKNOWN"
                                   if ru["SPAN_DEFINITION"] == SR.L_UNDEFINED else "NOT_A_NUMERIC_SPAN_RULE"]
        ru["STATE"] = ("PROVEN_PROJECT_RULE" if ru["GATE"] == SR.RELEASABLE else "RECORDED_NOT_RELEASABLE")
    rule_conflict = ("P4-6-NOTE-2 gives top bars over beams 'one third of the span' (both directions); p.15 gives "
                     "0.25 L1 (non-continuous) / 0.30 max(L1, L2) (continuous) from the support face")

    # ---------------------------------------------------- 05 support register rows (+ candidate p.15 extents)
    def clear_perp(pid, ori):
        c = pid_scope[pid]
        return c["CLEAR_SPAN_X_MM"] if ori == "V" else c["CLEAR_SPAN_Y_MM"]
    for s in supports:
        ori = s["ORIENTATION"]
        lp, rp = s["LEFT_PANEL"], s["RIGHT_PANEL"]
        expl = s.get("_explicit_top", [])
        if expl:
            t = expl[0]
            s["BAR_SOURCE"] = f"explicit '/Top' callout {t['TOKEN_ID']} ({t['RAW']})"
            s["BAR_DIAMETER_MM"], s["SPACING"] = t["DIA_MM"], f"{t['COUNT_OR_RATE']} bars (printed count)"
        elif s["SUPPORT_KIND"] == "BEAM":
            s["BAR_SOURCE"] = "plan note 2 (P4-6-NOTE-2), floor rule"
            s["BAR_DIAMETER_MM"], s["SPACING"] = 10, "5 bars per metre (200 mm)"
        else:
            s["BAR_SOURCE"] = "NONE (not a beam support)"
            s["BAR_DIAMETER_MM"], s["SPACING"] = None, None
        ext_l = ext_r = None
        if s["SUPPORT_KIND"] == "BEAM" and s["SUPPORT_TYPE"] in (SR.CONTINUOUS, SR.NON_CONTINUOUS):
            kind = SR.TOP_CONT if s["SUPPORT_TYPE"] == SR.CONTINUOUS else SR.TOP_NONCONT
            g = SR.rule_gate(kind, L_basis=SR.CLEAR_SPAN, direction="X" if ori == "V" else "Y",
                             support_type=s["SUPPORT_TYPE"], origin=SR.FACE_OF_SUPPORT)
            slab = [p for p in (lp, rp) if p and pid_scope.get(p, {}).get("SCOPE") in (SR.IN_SCOPE,
                                                                                    SR.CLASSIFICATION_BLOCKED)]
            Ls = [clear_perp(p, ori) for p in slab]
            if g["state"] == SR.RELEASABLE and Ls and all(Ls) and len(Ls) == (2 if kind == SR.TOP_CONT else 1):
                if kind == SR.TOP_CONT:
                    v = SR.rule_extent(kind, gate=g, L1_mm=Ls[0], L2_mm=Ls[1])
                    ext_l = ext_r = _r(v)
                else:
                    v = _r(SR.rule_extent(kind, gate=g, L1_mm=Ls[0]))
                    ext_l, ext_r = (v, None) if slab[0] == lp else (None, v)
        s["EXTENT_LEFT_MM"], s["EXTENT_RIGHT_MM"] = ext_l, ext_r
        s["EXTENT_STATE"] = ("CANDIDATE_ONLY_SOURCE_CONFLICT" if ext_l or ext_r else "NOT_COMPUTED")
        s["RULE_SOURCE"] = ("P15-TOP-CONT-0.30Lmax" if s["SUPPORT_TYPE"] == SR.CONTINUOUS else
                            "P15-TOP-NONCONT-0.25L1" if s["SUPPORT_TYPE"] == SR.NON_CONTINUOUS else None)
        s["RULE_CONFLICT"] = rule_conflict if s["SUPPORT_KIND"] == "BEAM" else None
        s["OWNERSHIP"] = "SUPPORT (counted once, not once per adjacent panel)"

    # ---------------------------------------------------- 04 components
    comps = []
    decision_blockers = {"COUNT_BASIS_UNRESOLVED": "Q-COUNT", "EDGE_BAR_UNRESOLVED": "Q-COUNT",
                         "TOP_EXTENT_SOURCE_CONFLICT": "Q-TOPEXT", "TOP_OVERRIDE_RULE_UNRESOLVED": "Q-TOPOVR",
                         "WHICH_50_PERCENT_UNRESOLVED": "Q-50PCT", "CONTINUOUS_BAR_SPEC_MISMATCH": "Q-MISMATCH",
                         "TABLE_NO_EXACT_ROW": "Q-TEMP", "TEMPERATURE_REGION_DEPENDS_ON_TOP_EXTENT": "Q-TOPEXT",
                         "COUNT_NOTATION_AMBIGUOUS_NO_PER_METRE": "Q-ABSCOUNT"}
    fam_by_pd = defaultdict(list)
    for f in fam_rows:
        fam_by_pd[(f["panel"], f["direction"])].append(f)

    def edges_dir(pid, d):
        out = []
        for e in pidx[pid]["edges"] or []:
            s = sup_by_view.get((pid, e["edge_index"]))
            if s and s["BARS_CROSSING"] == d:
                out.append(s)
        return out
    for c in census:
        pid = c["SLAB_PANEL_ID"]
        if c["SCOPE"] not in (SR.IN_SCOPE, SR.CLASSIFICATION_BLOCKED) or pid not in pidx:
            continue
        base_block = []
        if c["SCOPE"] == SR.CLASSIFICATION_BLOCKED:
            base_block.append("CLASSIFICATION_BLOCKED")
        if c["SPAN_STATE"] != "SINGLE_VALUED_FACE_TO_FACE":
            base_block.append("SPAN_NOT_SINGLE_VALUED")
        for d in ("X", "Y"):
            fams = fam_by_pd.get((pid, d), [])
            toks_all = [t for t in tok_by_panel.get(pid, []) if t["direction"] == d and t["layer"] != "TOP"]
            if not toks_all:
                continue
            sd = edges_dir(pid, d)
            blk = list(base_block)
            if len(toks_all) > 1:
                blk.append("SOURCE_CONFLICT_TWO_CALLOUTS_ONE_DIRECTION")
            if any(s["SUPPORT_TYPE"] == SR.CONTINUITY_UNRESOLVED for s in sd):
                blk.append("SUPPORT_CONTINUITY_UNRESOLVED")
            if any(s["SUPPORT_KIND"] != "BEAM" for s in sd):
                blk.append("SUPPORT_NOT_A_BEAM")
            t = toks_all[0]
            mode = t["count_mode"]
            if mode == "BARS_PER_METRE":
                blk += ["COUNT_BASIS_UNRESOLVED", "EDGE_BAR_UNRESOLVED"]
            else:
                blk.append("COUNT_NOTATION_AMBIGUOUS_NO_PER_METRE")
            layer = "TOP_AND_BOTTOM" if t["layer"] == "T&B" else "BOTTOM"
            layer_auth = ("PROJECT_SOURCE ((T&B) qualifier)" if t["layer"] == "T&B" else
                          "ENGINEERING_DERIVED (unqualified plan callout; '/Top' and '(T&B)' are marked, plan note 2 "
                          "gives the top steel over beams; p.15: bottom bars 'see schedule or plan')")
            cont = [s for s in sd if s["SUPPORT_TYPE"] == SR.CONTINUOUS]
            fid = f"{pid}:{d}"
            run_id = run_of_family.get(fid)
            run = [r for r in run_rows if r["BAR_RUN_ID"] == run_id]
            if run and run[0]["ALIGNMENT"] == "PARTIAL":
                blk.append("RUN_ALIGNMENT_PARTIAL")
            if any(fid in m["families"] for m in runs["mismatches"]):
                blk.append("CONTINUOUS_BAR_SPEC_MISMATCH")
            span = c["CLEAR_SPAN_X_MM"] if d == "X" else c["CLEAR_SPAN_Y_MM"]
            dist = c["CLEAR_SPAN_Y_MM"] if d == "X" else c["CLEAR_SPAN_X_MM"]
            common = dict(panel=pid, floor=c["FLOOR"], direction=d, token=t["text_handle"], dia_mm=t["dia_mm"],
                          rate_or_count=t["count"], count_mode=mode, layer=layer, layer_authority=layer_auth,
                          clear_span_mm=span, distribution_mm=dist, l_basis=SR.CLEAR_SPAN,
                          cover_basis=cover["label"], scope=c["SCOPE"])
            ends_nc = [s["SUPPORT_ID"] for s in sd if s["SUPPORT_TYPE"] == SR.NON_CONTINUOUS]
            portions_blocked = ["end anchorage into non-continuous supports " + ",".join(ends_nc) +
                                " (shape only; cover >= 25 mm minimum, '40 CL.' binding unclear)"] if ends_nc else []
            if cont and t["layer"] != "T&B":
                comps.append(SR.component("CURTAILMENT_SEGMENT", owner=pid, project_support="P15-BOT-STOP-0.125L + "
                                          f"plan callout {t['text_handle']}", blockers=blk +
                                          ["WHICH_50_PERCENT_UNRESOLVED"],
                                          bar_role=f"BOTTOM_{d}", share="50% STOPPED",
                                          length_state=SR.PROJECT_BASIS_NUMERIC,
                                          length_rule="clear span minus 0.125 L at each continuous end "
                                                      f"({len(cont)}), plus the end portion at non-continuous ends",
                                          blocked_portions=portions_blocked, bar_run=None, **common))
                comps.append(SR.component("CONTINUOUS_BAR_RUN", owner=run_id, project_support="P15-BOT-STOP-0.125L "
                                          "'balance continuous' + plan callout " + t["text_handle"],
                                          blockers=blk + ["WHICH_50_PERCENT_UNRESOLVED"], bar_role=f"BOTTOM_{d}",
                                          share="50% CONTINUOUS (counted once per run)",
                                          length_state=SR.PROJECT_BASIS_NUMERIC,
                                          length_rule="run extent face to face of the run's end supports, "
                                                      "plus the end portions", blocked_portions=portions_blocked +
                                          ["laps / splices (not located)"], bar_run=run_id, **common))
            else:
                ctype = f"BOTTOM_{d}"
                comps.append(SR.component(ctype, owner=pid, project_support=f"plan callout {t['text_handle']}",
                                          blockers=blk, bar_role=ctype, share="100%",
                                          length_state=SR.PROJECT_BASIS_NUMERIC,
                                          length_rule="clear span plus the end portions into the supports",
                                          blocked_portions=portions_blocked, bar_run=run_id, **common))
                if t["layer"] == "T&B":
                    comps.append(SR.component(f"TOP_{d}", owner=pid, project_support=f"plan callout {t['text_handle']}"
                                              " (T&B)", blockers=blk, bar_role=f"TOP_{d}", share="100%",
                                              length_state=SR.PROJECT_BASIS_NUMERIC,
                                              length_rule="clear span plus the end portions into the supports",
                                              blocked_portions=portions_blocked, bar_run=None, **common))
        # temperature (p.15 detail draws TEMP. REINFORCING in the top layer)
        tr = SR.temperature_row(thickness_of.get(pid, {}).get("value_mm"), temp_table)
        for d in (("X", "Y") if thickness_of.get(pid, {}).get("value_mm") else ()):
            comps.append(SR.component(f"TEMPERATURE_{d}", owner=pid, project_support="P15 detail 'TEMP. REINFORCING' "
                                      "+ P15-TEMP-TABLE", blockers=base_block +
                                      (["TABLE_NO_EXACT_ROW"] if tr["state"] != SR.TABLE_EXACT_ROW else []) +
                                      ["TEMPERATURE_REGION_DEPENDS_ON_TOP_EXTENT", "COUNT_BASIS_UNRESOLVED"],
                                      bar_role=f"TEMPERATURE_{d}", panel=pid, floor=c["FLOOR"], direction=d,
                                      thickness_mm=thickness_of.get(pid, {}).get("value_mm"),
                                      table_state=tr["state"], length_state=SR.BLOCKED_UNQUANTIFIED,
                                      scope=c["SCOPE"], lap="P15-TEMP-NOTE-1-LAP-40D"))
        for t in tok_by_panel.get(pid, []):
            if t["direction"] not in ("X", "Y") and t.get("corner_reinforcement"):
                comps.append(SR.component("CORNER_BAR", owner=pid, project_support=f"corner callout {t['text_handle']}"
                                          " (S-TEXT-CORNER / S-REIN-CORNER)", blockers=base_block +
                                          ["CORNER_BAR_LENGTH_NOT_DIMENSIONED", "CORNER_BAR_LAYER_NOT_STATED"],
                                          bar_role="CORNER_BAR", panel=pid, floor=c["FLOOR"],
                                          direction=t["direction"], token=t["text_handle"], dia_mm=t["dia_mm"],
                                          rate_or_count=t["count"], count_mode=t["count_mode"],
                                          length_state=SR.BLOCKED_UNQUANTIFIED, scope=c["SCOPE"]))
    for s in supports:
        if s["SUPPORT_KIND"] != "BEAM":
            continue
        sides = [p for p in (s["LEFT_PANEL"], s["RIGHT_PANEL"]) if p]
        sc = {pid_scope[p]["SCOPE"] for p in sides}
        blk = ["TOP_EXTENT_SOURCE_CONFLICT"]
        if SR.CLASSIFICATION_BLOCKED in sc:
            blk.append("CLASSIFICATION_BLOCKED")
        if s["SUPPORT_TYPE"] == SR.CONTINUITY_UNRESOLVED:
            blk.append("SUPPORT_CONTINUITY_UNRESOLVED")
        if s.get("_explicit_top"):
            blk.append("TOP_OVERRIDE_RULE_UNRESOLVED")
            blk.append("EXPLICIT_TOP_GRAPHIC_SHAPE_ONLY")
        else:
            blk += ["COUNT_BASIS_UNRESOLVED", "EDGE_BAR_UNRESOLVED"]
        nc_bend = ["top anchor leg turned down into the support (shape only)"] if \
            s["SUPPORT_TYPE"] == SR.NON_CONTINUOUS else []
        comps.append(SR.component(f"TOP_SUPPORT_{s['BARS_CROSSING']}", owner=s["SUPPORT_ID"],
                                  project_support=s["BAR_SOURCE"], blockers=blk, bar_role="TOP_SUPPORT",
                                  floor=s["FLOOR"], direction=s["BARS_CROSSING"], dia_mm=s["BAR_DIAMETER_MM"],
                                  rate_or_count=s["SPACING"], support_type=s["SUPPORT_TYPE"],
                                  sides=sides, length_state=SR.BLOCKED_UNQUANTIFIED, bar_run=s.get("BAR_RUN_ID"),
                                  blocked_portions=nc_bend, scope=",".join(sorted(sc))))
    for k, c in enumerate(comps):
        c["COMPONENT_ID"] = f"CMP-{k + 1:04d}"
        hard = [b for b in c["blockers"] if b not in decision_blockers]
        c["DECISION_ONLY"] = bool(c["blockers"]) and not hard
        c["DECISIONS_NEEDED"] = sorted({decision_blockers[b] for b in c["blockers"] if b in decision_blockers})
    check(all(c["kg"] is None for c in comps), "no component carries kg")

    # ---------------------------------------------------- 08 openings
    openings = []
    for c in census:
        pid = c["SLAB_PANEL_ID"]
        if pid not in pidx:
            continue
        r = pidx[pid]
        if c["SCOPE"] == SR.VOID_OR_OPENING or c["CONFLICT"] == SR.SOURCE_CONFLICT:
            openings.append({"OPENING_ID": f"OP-{pid}", "FLOOR": c["FLOOR"], "GEOMETRY": "FACE " + pid,
                             "BBOX_MM": c["BBOX_MM"], "AREA_M2": c["GEOMETRIC_AREA_M2"],
                             "TYPE": "OPEN_TO_BELOW_FACE" if c["SCOPE"] == SR.VOID_OR_OPENING else
                             "VOID_WITH_STAIR_AND_SLAB_EVIDENCE",
                             "SOURCE": c["VOID_EVIDENCE"], "PANEL_OWNER": "itself (a face bounded by supports)",
                             "REBAR_DEDUCTION_RULE": "NONE_REQUIRED: no slab bar of a neighbouring panel crosses it "
                                                     "(the bars stop at the bounding supports)",
                             "TRIM_BAR_RULE": "NONE_DRAWN (SOURCE_EXPECTED_NOT_LOCATED)",
                             "DIAGONAL_BAR_RULE": "NONE_DRAWN (SOURCE_EXPECTED_NOT_LOCATED)",
                             "STATE": c["CONFLICT"] or "VOID",
                             "BAR_EFFECT": SR.opening_effect(tuple(c["BBOX_MM"]), {"X": None, "Y": None})})
    for sh in SHEETS:
        lines = opening_lines[sh]
        face_lines = {h: c["SLAB_PANEL_ID"] for c in census if c["SOURCE_SHEET"] == sh and c["VOID_EVIDENCE"]
                      for h in c["VOID_EVIDENCE"]["x_lines"]}
        parent = {e["handle"]: e["handle"] for e in lines}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        ends = defaultdict(list)
        for e in lines:
            for q in (e["a"], e["b"]):
                ends[(round(q[0] / 5), round(q[1] / 5))].append(e["handle"])
        for hs in ends.values():
            for h in hs[1:]:
                ra, rb = find(hs[0]), find(h)
                if ra != rb:
                    parent[rb] = ra
        comps_ = defaultdict(list)
        for e in lines:
            comps_[find(e["handle"])].append(e)
        for root, es in sorted(comps_.items(), key=lambda kv: min(e["handle"] for e in kv[1])):
            hs = sorted(e["handle"] for e in es)
            pts = [q for e in es for q in (e["a"], e["b"])]
            bb = [round(v) for v in bbox(pts)]
            mid = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
            hub = max(Counter((round(q[0] / 5), round(q[1] / 5)) for q in pts).values())
            faces = sorted({face_lines[h] for h in hs if h in face_lines})
            inz = any(z[0] - ZONE_MARGIN_MM <= mid[0] <= z[2] + ZONE_MARGIN_MM and
                      z[1] - ZONE_MARGIN_MM <= mid[1] <= z[3] + ZONE_MARGIN_MM for z in zones[sh])
            hit = [r["panel_id"] for r in panels if r["sheet"] == sh and in_face(mid, r)]
            if not hit:          # a slot between faces: the smallest face whose box holds it
                box = [r for r in panels if r["sheet"] == sh and r["class"] != "OUTSIDE_BUILDING_OR_COURT"
                       and bbox(r["polygon_mm"])[0] - 1 <= bb[0] and bbox(r["polygon_mm"])[1] - 1 <= bb[1]
                       and bb[2] <= bbox(r["polygon_mm"])[2] + 1 and bb[3] <= bbox(r["polygon_mm"])[3] + 1]
                hit = [min(box, key=lambda r: r["area_m2"])["panel_id"]] if box else []
            if faces and all(pid_scope[f]["S1_CLASS"] == "DOME_ZONE" for f in faces) or hub >= 6:
                kind, owner, state = "DOME_RADIALS", None, "EXCLUDED_WITH_DOME"
            elif faces:
                kind, owner = "VOID_OUTLINE", faces[0]
                state = f"EVIDENCE_OF_OP-{faces[0]}"
            elif inz:
                kind, owner, state = "LINES_IN_A_SECTION_DETAIL", None, "REFERENCE_ONLY"
            else:
                owner = hit[0] if hit else None
                kind = "OPENING_STRIP"
                state = ("EXCLUDED_WITH_" + pid_scope[owner]["PANEL_CLASS"] if owner and
                         pid_scope[owner]["SCOPE"] != SR.IN_SCOPE else "UNRESOLVED")
            openings.append({"OPENING_ID": f"OP-{sh}-{kind}-{hs[0]}", "FLOOR": FLOOR[sh],
                             "GEOMETRY": f"{len(es)} S-OPENING lines " + ",".join(hs), "BBOX_MM": bb,
                             "AREA_M2": _r((bb[2] - bb[0]) * (bb[3] - bb[1]) / 1e6, 3), "TYPE": kind,
                             "SOURCE": "S-OPENING layer", "PANEL_OWNER": owner,
                             "REBAR_DEDUCTION_RULE": "PER_BAR_DIRECTION (opening_effect) if it lies in a released "
                                                     "panel" if kind == "OPENING_STRIP" and state == "UNRESOLVED"
                             else "NOT_APPLICABLE", "TRIM_BAR_RULE": "NONE_DRAWN" if kind == "OPENING_STRIP" else None,
                             "DIAGONAL_BAR_RULE": "NONE_DRAWN" if kind == "OPENING_STRIP" else None,
                             "STATE": state, "BAR_EFFECT": None})
    merged, keep = {}, []
    for o in openings:
        key = (o["FLOOR"], o["TYPE"], o["PANEL_OWNER"]) if o["TYPE"] in ("VOID_OUTLINE",
                                                                          "LINES_IN_A_SECTION_DETAIL") else None
        if key is None:
            keep.append(o)
        elif key in merged:
            m = merged[key]
            m["GEOMETRY"] = m["GEOMETRY"] + "; " + o["GEOMETRY"]
            m["BBOX_MM"] = [min(m["BBOX_MM"][0], o["BBOX_MM"][0]), min(m["BBOX_MM"][1], o["BBOX_MM"][1]),
                            max(m["BBOX_MM"][2], o["BBOX_MM"][2]), max(m["BBOX_MM"][3], o["BBOX_MM"][3])]
            m["AREA_M2"] = None
        else:
            merged[key] = dict(o, AREA_M2=None)
            keep.append(merged[key])
    openings = keep
    for e in void_inserts:
        sh = e["sheet"]
        c0 = ((e["bbox"][0] + e["bbox"][2]) / 2, (e["bbox"][1] + e["bbox"][3]) / 2)
        hit = [r["panel_id"] for r in panels if r["sheet"] == sh and in_face(c0, r)]
        openings.append({"OPENING_ID": f"OP-{sh}-VOIDTAG-{e['handle']}", "FLOOR": FLOOR[sh],
                         "GEOMETRY": f"'void' block insert {e['handle']} (VOID + Arabic)",
                         "BBOX_MM": [round(v) for v in e["bbox"]], "AREA_M2": None, "TYPE": "VOID_LABEL",
                         "SOURCE": "block 'void'", "PANEL_OWNER": hit[0] if hit else None,
                         "REBAR_DEDUCTION_RULE": "LABEL_ONLY (the void is the face it labels)",
                         "TRIM_BAR_RULE": None, "DIAGONAL_BAR_RULE": None, "STATE": "LABELS_" + (hit[0] if hit else
                                                                                               "NOTHING"),
                         "BAR_EFFECT": None})

    # ---------------------------------------------------- 09 temperature, 10 counts
    temp_rows = []
    for c in census:
        pid = c["SLAB_PANEL_ID"]
        if c["SCOPE"] not in (SR.IN_SCOPE, SR.CLASSIFICATION_BLOCKED) or pid not in pidx:
            continue
        t = thickness_of[pid]["value_mm"]
        if t is None:
            continue
        tr = SR.temperature_row(t, temp_table)
        temp_rows.append({"SLAB_PANEL_ID": pid, "FLOOR": c["FLOOR"], "SCOPE": c["SCOPE"], "THICKNESS_MM": t,
                          "THICKNESS_AUTHORITY": thickness_of[pid]["authority"], "TABLE_STATE": tr["state"],
                          "TABLE_VALUE": tr["value"], "BRACKET_CONTEXT_ONLY": tr.get("bracket_context_only"),
                          "INTERPOLATED": False,
                          "REGION_RULE": "p.15 detail: top layer between the top anchor bars; note 2: 2000 mm "
                                         "(1000 at spandrel) where beams are parallel to the main reinforcement",
                          "LAP_RULE": "40 x diameter (note 1)",
                          "STATE": "SOURCE_EXPECTED_NOT_LOCATED (TABLE_NO_EXACT_ROW)" if tr["state"] ==
                          SR.TABLE_NO_EXACT_ROW else tr["state"]})
    count_rows = []
    for c in comps:
        if c["component"] in ("BOTTOM_X", "BOTTOM_Y", "TOP_X", "TOP_Y", "CURTAILMENT_SEGMENT", "CONTINUOUS_BAR_RUN"):
            cd = SR.count_decision(c["count_mode"], c["rate_or_count"], distribution_mm=c.get("distribution_mm"))
            count_rows.append({"COMPONENT_ID": c["COMPONENT_ID"], "COMPONENT": c["component"], "OWNER": c["owner"],
                               "TOKEN": c.get("token"), "COUNT_MODE": c["count_mode"],
                               "RATE_PER_M": cd.get("rate"), "SPACING_MM": cd.get("spacing_mm"),
                               "DISTRIBUTION_WIDTH_MM": c.get("distribution_mm"),
                               "DISTRIBUTION_BASIS": "clear span perpendicular to the bars (face to face); first-bar "
                                                     "offset from the face not stated",
                               "COUNT_RULE": cd["rule"] or "UNRESOLVED", "CANDIDATES": cd.get("candidates"),
                               "PRINTED_COUNT": cd["count"] if cd["state"] == SR.COUNT_EXPLICIT else None,
                               "EDGE_BAR": cd.get("edge_bar"), "STATE": cd["state"],
                               "NOTE": "50% share of the family" if c["component"] in ("CURTAILMENT_SEGMENT",
                                                                                         "CONTINUOUS_BAR_RUN") else ""})
    for s in supports:
        if s["SUPPORT_KIND"] != "BEAM":
            continue
        if s.get("_explicit_top"):
            t = s["_explicit_top"][0]
            cd = SR.count_decision("EXPLICIT_COUNT", t["COUNT_OR_RATE"])
        else:
            cd = SR.count_decision("BARS_PER_METRE", 5, distribution_mm=s["LENGTH_MM"])
        count_rows.append({"COMPONENT_ID": next(c["COMPONENT_ID"] for c in comps if c["owner"] == s["SUPPORT_ID"]),
                           "COMPONENT": f"TOP_SUPPORT_{s['BARS_CROSSING']}", "OWNER": s["SUPPORT_ID"],
                           "TOKEN": s["BAR_SOURCE"], "COUNT_MODE": cd["state"] if cd["state"] == SR.COUNT_EXPLICIT
                           else "BARS_PER_METRE", "RATE_PER_M": cd.get("rate"), "SPACING_MM": cd.get("spacing_mm"),
                           "DISTRIBUTION_WIDTH_MM": s["LENGTH_MM"], "DISTRIBUTION_BASIS": "support edge length",
                           "COUNT_RULE": cd["rule"] or "UNRESOLVED", "CANDIDATES": cd.get("candidates"),
                           "PRINTED_COUNT": cd["count"] if cd["state"] == SR.COUNT_EXPLICIT else None,
                           "EDGE_BAR": cd.get("edge_bar"), "STATE": cd["state"], "NOTE": ""})

    # ---------------------------------------------------- 11 conflicts, 12 SENL, 15 questions
    conflicts = [
        {"CONFLICT_ID": "C-01", "KIND": "PANEL_VOID_CONFLICT", "WHERE": "SP-GF_ROOF_SLAB-21 (B29 light well)",
         "EVIDENCE": gf_void_conflict, "STATE": SR.SOURCE_CONFLICT,
         "CANDIDATES": gf_void_conflict["candidates"], "RESOLUTION": "NONE (not voted; excluded from S7)"},
        {"CONFLICT_ID": "C-02", "KIND": "UNSUPPORTED_SUPPORT_RULE_APPLICABILITY", "WHERE": "every beam support",
         "EVIDENCE": rule_conflict, "STATE": SR.SOURCE_CONFLICT,
         "CANDIDATES": ["P4-6-NOTE-2 1/3 span", "P15 0.25 L1 / 0.30 max(L1, L2)"], "RESOLUTION": "NONE"}]
    two_calls = sorted({c["panel"] for c in comps if "SOURCE_CONFLICT_TWO_CALLOUTS_ONE_DIRECTION" in c["blockers"]})
    for p in two_calls:
        ts = [t for t in tok_by_panel[p] if (p, t["direction"]) in fam_of_panel_dir and
              len(fam_of_panel_dir[(p, t["direction"])]) > 1]
        conflicts.append({"CONFLICT_ID": f"C-{len(conflicts) + 1:02d}", "KIND": "MULTIPLE_CANDIDATE_BINDINGS",
                          "WHERE": p, "EVIDENCE": [f"{t['raw']} {t['direction']} ({t['text_handle']})" for t in ts],
                          "STATE": SR.SOURCE_CONFLICT, "CANDIDATES": ["one is a different layer / a local extra",
                                                                       "one belongs to the neighbouring stair"],
                          "RESOLUTION": "NONE"})
    abs_tokens = sorted({c["token"] for c in comps if "COUNT_NOTATION_AMBIGUOUS_NO_PER_METRE" in c["blockers"]})
    conflicts.append({"CONFLICT_ID": f"C-{len(conflicts) + 1:02d}", "KIND": "COUNT_NOTATION_CONFLICT",
                      "WHERE": abs_tokens, "EVIDENCE": "printed 'NØD' without '/m' where every other slab callout is "
                                                       "a rate per metre", "STATE": SR.SOURCE_CONFLICT,
                      "CANDIDATES": ["absolute count", "rate per metre with '/m' omitted"], "RESOLUTION": "NONE"})
    conflicts += [
        {"CONFLICT_ID": f"C-{len(conflicts) + 1:02d}", "KIND": "THICKNESS_PRIOR_REGISTER_CONFLICT",
         "WHERE": "2F_ROOF_SLAB", "EVIDENCE": "R4 TEMPERATURE register: whole 2F floor 180 mm; source: two T 18 marks "
                                              "inside the two water-tank panels, no floor note",
         "STATE": "RESOLVED_BY_SOURCE (LOCAL_PANEL 180 for two panels; PROJECT_DEFAULT 160 elsewhere)",
         "CANDIDATES": None, "RESOLUTION": "source precedence (no vote)"},
        {"CONFLICT_ID": f"C-{len(conflicts) + 2:02d}", "KIND": "COVER_DIMENSION_BINDING",
         "WHERE": "p.15 non-continuous support", "EVIDENCE": "'40 CL.' at the outer face; note 22 minimum 25 mm; the "
                                                             "bar it dimensions is not legible",
         "STATE": SR.SOURCE_CONFLICT, "CANDIDATES": ["end cover of the top anchor leg", "end cover of the bottom bar",
                                                     "cover to the inner bar"], "RESOLUTION": "NONE"},
        {"CONFLICT_ID": f"C-{len(conflicts) + 3:02d}", "KIND": "CLASSIFICATION",
         "WHERE": tank_panels, "EVIDENCE": "WATER TANK PLACE cloud; T 18 marks; (T&B) callouts",
         "STATE": SR.CLASSIFICATION_BLOCKED, "CANDIDATES": ["normal roof slab (S7)", "water-tank structure (S8)"],
         "RESOLUTION": "NONE"},
        {"CONFLICT_ID": f"C-{len(conflicts) + 4:02d}", "KIND": "CLASSIFICATION",
         "WHERE": [f"HZ-{h['sheet']}-{h['handle']}" for h in dense_rows],
         "EVIDENCE": "the legend draws Cantilever portion and Bearing wall with the same dense hatch",
         "STATE": SR.CLASSIFICATION_BLOCKED, "CANDIDATES": ["cantilever slab portion", "bearing wall"],
         "RESOLUTION": "NONE"}]
    par = sorted(h for h, v in top_verdict.items() if v["state"] == SR.SOURCE_CONFLICT)
    if par:
        conflicts.append({"CONFLICT_ID": f"C-{len(conflicts) + 1:02d}", "KIND": "TOP_BAR_BINDING",
                          "WHERE": par, "EVIDENCE": [f"{h}: graphic {top_verdict[h]['graphic']}" for h in par],
                          "STATE": SR.SOURCE_CONFLICT,
                          "CANDIDATES": ["beam top bars drawn beside the beam (beam scope)",
                                         "edge / cantilever bars of the dense-hatch strip",
                                         "slab top bars over the support"], "RESOLUTION": "NONE"})
    asym = [s["SUPPORT_ID"] for s in supports if not s["VIEWS_SYMMETRIC"]]
    if asym:
        conflicts.append({"CONFLICT_ID": f"C-{len(conflicts) + 1:02d}", "KIND": "ASYMMETRIC_SUPPORT_VIEW",
                          "WHERE": asym, "EVIDENCE": "the S1 edge probe saw the neighbour from one side only",
                          "STATE": "RECORDED", "CANDIDATES": None, "RESOLUTION": "support kept once"})
    mism = runs["mismatches"]
    if mism:
        conflicts.append({"CONFLICT_ID": f"C-{len(conflicts) + 1:02d}", "KIND": "CONTINUOUS_BAR_SPEC_MISMATCH",
                          "WHERE": sorted({m["support_id"] for m in mism}),
                          "EVIDENCE": f"{len(mism)} continuous supports where the bottom callouts differ in diameter "
                                      "or spacing ('balance continuous')", "STATE": SR.SOURCE_CONFLICT,
                          "CANDIDATES": ["each span keeps its own bar (lap at the support)",
                                         "the larger continues"], "RESOLUTION": "NONE"})
    senl = [
        ("SENL-01", "TEMPERATURE_ROW_160_180", "temperature reinforcement for 160 mm / 180 mm (p.15 table rows: 100, "
                                               "125, 150, 175, 200, 250, 300)", "P15-TEMP-TABLE"),
        ("SENL-02", "SLAB_SCHEDULE", "a slab reinforcement schedule ('FOR SIZE & SPACING SEE SCHEDULE OR PLAN'): no "
                                     "slab schedule in the issued set", "P15-SLAB-ON-BEAMS"),
        ("SENL-03", "COUNT_RULE", "how a rate callout becomes a bar count (first bar from the face, edge bars)",
         "plans pp.4-6"),
        ("SENL-04", "LAYER_WORD", "a TOP / BOTTOM word on the unqualified plan callouts", "legend 'Normal Slab "
                                                                                          "Reinforcement'"),
        ("SENL-05", "MAIN_BAR_LAP", "lap length / location for main slab bars (only temperature bars: 40 D)",
         "P15-TEMP-NOTES"),
        ("SENL-06", "END_ANCHORAGE", "top anchor leg and bottom bar end lengths at non-continuous supports",
         "P15-SLAB-ON-BEAMS"),
        ("SENL-07", "SUNKEN_SLAB", "sunken slab drop depth and step detail (bar continuity at the step)",
         "legend 'Sunken slab'"),
        ("SENL-08", "OPENING_TRIM", "opening trim / diagonal bars at slab openings", "P8-N04"),
        ("SENL-09", "WHICH_50_PERCENT", "which half of the bottom bars stops", "P15-SLAB-ON-BEAMS"),
        ("SENL-10", "T1_T4_DETAILS", "'See main details for T1, T2, T3 & T4' (p.6 legend)", "p.6 legend"),
        ("SENL-11", "CORNER_BAR_LENGTH", "corner reinforcement bar length / layer", "legend 'Corner Reinforcement'"),
        ("SENL-12", "CANTILEVER_DETAIL", "cantilever-portion reinforcement (dense-hatch strips)", "legend")]
    senl_rows = [{"SENL_ID": a, "TOPIC": b, "EXPECTED": c, "REFERENCED_BY": d, "STATE": "SOURCE_EXPECTED_NOT_LOCATED",
                  "SEARCHED": "ST7757.dxf texts / attributes / block contents (all slab sheets), pp.4-6 and p.15 "
                              "(visual reading)"} for a, b, c, d in senl]
    questions = [
        ("Q-COUNT", "How is a slab rate callout (e.g. 5Ø10/m) turned into a bar count across a panel: first bar at "
                    "cover or at half a spacing from the face, and is there a bar at both edges?", "SENL-03"),
        ("Q-LAYER", "Are the plan callouts without '/Top' or '(T&B)' the bottom bars?", "SENL-04"),
        ("Q-TOPEXT", "Top bars over beams: does plan note 2 ('5Ø10/m ... length one third of the span, both "
                     "directions') replace the p.15 extents (0.25 L1 / 0.30 max(L1, L2))? Is 'one third of the span' "
                     "the total bar length or the extension each side, and of which span?", "C-02"),
        ("Q-TOPOVR", "Where a '/Top' callout is drawn at a support, does it replace plan note 2's 5Ø10/m there or add "
                     "to it?", "P4-6-NOTE-2"),
        ("Q-TEMP", "Which temperature reinforcement applies to the 160 mm and 180 mm slabs? The p.15 table has no "
                   "160 or 180 row.", "SENL-01"),
        ("Q-TEMPREG", "Temperature note 2 ('where beams are parallel to the main slab reinforcement'): which direction "
                      "is 'main' in a two-way panel?", "P15-TEMP-NOTE-2-STRIP"),
        ("Q-GFVOID", "B29 light well (GF roof slab): the open-to-below X spans the stair flights, a T 16 mark and "
                     "8Ø16/m bars. Which part is void, which is stair slab?", "C-01"),
        ("Q-TANK", "WATER TANK PLACE (2F roof): are the two T 18 panels normal roof slab (S7) or part of a "
                   "water-tank structure (S8)?", "C-tank"),
        ("Q-SUNKEN", "Sunken slabs: drop depth and the step detail; do the bottom bars continue across the step?",
         "SENL-07"),
        ("Q-HATCH", "The dense-hatch strips: cantilever portions or bearing walls?", "C-hatch"),
        ("Q-ENDCOVER", "p.15 '40 CL.' at the non-continuous support: which bar does it dimension?", "C-cover"),
        ("Q-ANCHOR", "Length of the top anchor leg and of the bottom bar end at a non-continuous support?",
         "SENL-06"),
        ("Q-50PCT", "Which half of the bottom bars stops at 0.125 L (alternate bars?), and how is an odd count "
                    "split?", "SENL-09"),
        ("Q-ABSCOUNT", "Callouts printed without '/m' (e.g. 5Ø10): absolute counts or rates?", "C-count"),
        ("Q-TWOCALL", "Panels with two callouts in one direction: which governs?", "C-two"),
        ("Q-MISMATCH", "At a continuous support between panels with different bottom callouts, which bars run "
                       "through ('balance continuous'): each span's own bars lapped at the support, or the larger?",
         "C-mismatch"),
        ("Q-LAP", "Lap length and lap positions for main slab bars?", "SENL-05"),
        ("Q-T1T4", "Where are the 'main details for T1, T2, T3 & T4' (p.6 legend)?", "SENL-10"),
        ("Q-OPENING", "Trim / diagonal bars at slab openings and shafts?", "SENL-08"),
        ("Q-CORNER", "Corner reinforcement (3Ø14): bar length and layer?", "SENL-11"),
        ("Q-TOPBESIDE", "The '/Top' bars drawn beside beam lines outside the 2F panels (4Ø16/Top, 5Ø18/Top): beam "
                        "top bars, edge / cantilever bars, or slab top bars?", "C-topbar")]
    def n_comp(pred):
        return len([c for c in comps if pred(c)])
    sunken_ids = set(sunken)
    affects = {
        "Q-LAYER": f"{n_comp(lambda c: str(c.get('layer_authority', '')).startswith('ENGINEERING_DERIVED'))} "
                   "bottom components (non-blocking: layer recorded as ENGINEERING_DERIVED)",
        "Q-TEMPREG": f"{n_comp(lambda c: c['component'].startswith('TEMPERATURE'))} temperature components",
        "Q-GFVOID": "1 face (SP-GF_ROOF_SLAB-21) and its tokens",
        "Q-TANK": f"{len(tank_panels)} panels, {n_comp(lambda c: c.get('panel') in tank_panels)} components",
        "Q-SUNKEN": f"{len(sunken_ids)} panels; "
                    f"{len([s_ for s_ in supports if sunken_ids & set(s_['SIDES']) and s_['SUPPORT_TYPE'] == SR.CONTINUITY_UNRESOLVED])} supports",
        "Q-HATCH": f"{len(dense_rows)} dense-hatch strips",
        "Q-ENDCOVER": f"{n_comp(lambda c: any('non-continuous' in x for x in c.get('blocked_portions') or []))} "
                      "components with end portions at non-continuous supports",
        "Q-ANCHOR": f"{n_comp(lambda c: any('non-continuous' in x or 'turned down' in x for x in c.get('blocked_portions') or []))} "
                    "components with end portions",
        "Q-TWOCALL": f"{n_comp(lambda c: 'SOURCE_CONFLICT_TWO_CALLOUTS_ONE_DIRECTION' in c['blockers'])} components",
        "Q-LAP": f"{n_comp(lambda c: c['component'] == 'CONTINUOUS_BAR_RUN')} continuous-run components",
        "Q-T1T4": "not linked to a component (legend reference only)",
        "Q-OPENING": f"{len([o for o in openings if o['TYPE'] in ('OPEN_TO_BELOW_FACE', 'OPENING_STRIP')])} openings",
        "Q-CORNER": f"{n_comp(lambda c: c['component'] == 'CORNER_BAR')} corner components",
        "Q-TOPBESIDE": f"{len(par)} tokens"}
    q_rows = []
    for q, t, l in questions:
        n = n_comp(lambda c, q=q: q in c["DECISIONS_NEEDED"])
        q_rows.append({"QUESTION_ID": q, "QUESTION": t, "LINKED_TO": l, "ASKED_OF": "PROJECT_ENGINEER",
                       "COMPONENTS_AFFECTED": n, "AFFECTS": affects.get(q, f"{n} components (blocker)"),
                       "STATE": "OPEN"})

    # ---------------------------------------------------- 14 candidates
    cands = []
    for c in comps:
        if c["readiness"] == SR.S7_RELEASE_CANDIDATE:
            st = "S7_RELEASE_CANDIDATE"
        elif c["DECISION_ONLY"]:
            st = "CONDITIONAL_ON_OWNER_DECISIONS"
        else:
            continue
        cands.append({"COMPONENT_ID": c["COMPONENT_ID"], "COMPONENT": c["component"], "OWNER": c["owner"],
                      "FLOOR": c.get("floor"), "DIRECTION": c.get("direction"), "TOKEN": c.get("token"),
                      "DIA_MM": c.get("dia_mm"), "RATE_OR_COUNT": c.get("rate_or_count"),
                      "LENGTH_STATE": c.get("length_state"), "LENGTH_RULE": c.get("length_rule"),
                      "BLOCKED_PORTIONS": c.get("blocked_portions"), "STATE": st,
                      "DECISIONS_NEEDED": c["DECISIONS_NEEDED"], "LAYER_AUTHORITY": c.get("layer_authority"),
                      "KG": None})

    # ---------------------------------------------------- conservation gates
    geo_ids = [r["panel_id"] for r in panels] + [f"HZ-{h['sheet']}-{h['handle']}" for h in dense_rows]
    pcons = SR.population_conservation(geo_ids, [{"id": c["SLAB_PANEL_ID"], "scope": c["SCOPE"],
                                                  "special": c["SPECIAL"] if c["SCOPE"] == SR.IN_SCOPE else None}
                                                 for c in census])
    check(pcons["all_pass"], f"population conservation {pcons}")
    view_once = Counter(v for s in supports for v in s["VIEWS"])
    check(all(n == 1 for n in view_once.values()), "every panel edge view belongs to one support")
    sup_once = len({s["SUPPORT_ID"] for s in supports}) == len(supports) and \
        sum(view_once.values()) == len(edge_views)
    run_once = Counter(f for r in runs["runs"] for f in r["families"])
    check(all(n == 1 for n in run_once.values()), "every bottom family is in one run")
    owner_of_top = Counter(c["owner"] for c in comps if c["component"].startswith("TOP_SUPPORT"))
    check(all(n == 1 for n in owner_of_top.values()), "one top-support component per support")
    special_leak = [c["COMPONENT_ID"] for c in comps if c.get("scope") == SR.EXCLUDED_SPECIAL]
    check(not special_leak, "no special structure leaks into S7 components")
    gates = {"all_slab_geometries_terminate": pcons["checks"]["every_geometry_terminates_once"],
             "all_panel_labels_terminate": all(c["SCOPE"] in SR.SCOPES for c in census),
             "all_reinforcement_tokens_terminate": tcons["checks"]["every_token_terminates_once"],
             "all_supports_terminate": sup_once and all(s["SUPPORT_TYPE"] in SR.SUPPORT_TYPES for s in supports),
             "all_openings_terminate": all(o["STATE"] for o in openings),
             "all_bar_runs_terminate": all(n == 1 for n in run_once.values()),
             "no_token_produces_two_physical_bars": tcons["checks"]["no_bar_family_from_two_tokens"],
             "no_support_bar_counted_from_both_panels": all(n == 1 for n in owner_of_top.values()),
             "no_special_structure_in_s7": not special_leak,
             "no_blocked_component_carries_kg": all(c["kg"] is None for c in comps),
             "no_kg_in_pre_s7": True}
    check(all(gates.values()), f"conservation gates {gates}")
    return locals()


# ------------------------------------------------------------------ write
def write(B):
    census, supports, comps = B["census"], B["supports"], B["comps"]
    _csv("01_SLAB_PANEL_CENSUS.csv", census, [
        "SLAB_PANEL_ID", "FLOOR", "SOURCE_SHEET", "S1_CLASS", "PANEL_CLASS", "SCOPE", "SCOPE_REASON", "SPECIAL",
        "CONFLICT", "BOUNDARY_HANDLES", "SUPPORT_EDGES", "ADJACENT_PANEL_IDS", "GEOMETRIC_AREA_M2", "RECTANGULARITY",
        "BBOX_MM", "SPAN_STATE", "CLEAR_SPAN_X_MM", "CLEAR_SPAN_Y_MM", "SUPPORT_CENTERLINE_SPAN_X_MM",
        "SUPPORT_CENTERLINE_SPAN_Y_MM", "THICKNESS_MM", "THICKNESS_AUTHORITY", "THICKNESS_MARKS", "TOKENS",
        "VOID_EVIDENCE", "STAIR_TREADS", "NOTES"])
    _csv("02_THICKNESS_REGISTER.csv", B["thick_rows"], [
        "SLAB_PANEL_ID", "FLOOR", "SCOPE", "PANEL_CLASS", "LOCAL_PANEL_MARKS", "FLOOR_RULE", "PROJECT_DEFAULT_MM",
        "PROJECT_DEFAULT_SOURCES", "EFFECTIVE_THICKNESS_MM", "AUTHORITY", "OVERRIDDEN", "CONFIRMS", "SUNKEN",
        "DROP_DEPTH", "PRIOR_REGISTER_NOTE", "STATE"])
    _csv("03_SLAB_REBAR_TOKENS.csv", B["tok_rows"], [
        "TOKEN_ID", "SHEET", "FLOOR", "ENTITY", "LAYER", "RAW", "POSITION_MM", "ROTATION_DEG", "KIND", "S1_SOURCE_ROW",
        "DIA_MM", "COUNT_OR_RATE", "COUNT_MODE", "LAYER_QUALIFIER", "DIRECTION", "TERMINAL_STATE", "BOUND_TO",
        "BAR_FAMILIES", "REASON"])
    crow = []
    for c in comps:
        crow.append({"COMPONENT_ID": c["COMPONENT_ID"], "COMPONENT": c["component"], "OWNER": c["owner"],
                     "FLOOR": c.get("floor"), "BAR_ROLE": c.get("bar_role"), "SHARE": c.get("share"),
                     "DIRECTION": c.get("direction"), "TOKEN": c.get("token"), "DIA_MM": c.get("dia_mm"),
                     "RATE_OR_COUNT": c.get("rate_or_count"), "COUNT_MODE": c.get("count_mode"),
                     "LAYER": c.get("layer"), "LAYER_AUTHORITY": c.get("layer_authority"),
                     "CLEAR_SPAN_MM": c.get("clear_span_mm"), "DISTRIBUTION_MM": c.get("distribution_mm"),
                     "L_BASIS": c.get("l_basis"), "COVER_BASIS": c.get("cover_basis"),
                     "LENGTH_STATE": c.get("length_state"), "LENGTH_RULE": c.get("length_rule"),
                     "BLOCKED_PORTIONS": c.get("blocked_portions"), "BAR_RUN_ID": c.get("bar_run"),
                     "PROJECT_SUPPORT": c["project_support"], "BLOCKERS": c["blockers"],
                     "READINESS": c["readiness"], "DECISION_ONLY": c["DECISION_ONLY"],
                     "DECISIONS_NEEDED": c["DECISIONS_NEEDED"], "SCOPE": c.get("scope"), "KG": None})
    _csv("04_COMPONENT_READINESS.csv", crow, list(crow[0]))
    _csv("05_SUPPORT_REGISTER.csv", supports, [
        "SUPPORT_ID", "FLOOR", "SHEET", "SUPPORT_REF", "SUPPORT_KIND", "ORIENTATION", "LEFT_PANEL", "RIGHT_PANEL",
        "SEEN_FROM", "VIEWS", "VIEWS_SYMMETRIC", "MIXED_ORIENTATION", "SUPPORT_TYPE", "SUPPORT_TYPE_WHY", "LENGTH_MM", "SUPPORT_WIDTH_MM",
        "BARS_CROSSING", "BAR_SOURCE", "BAR_DIAMETER_MM", "SPACING", "COUNT_DIRECTION", "EXTENT_LEFT_MM",
        "EXTENT_RIGHT_MM", "EXTENT_STATE", "RULE_SOURCE", "RULE_CONFLICT", "BAR_RUN_ID", "OWNERSHIP"])
    _csv("06_SUPPORT_RULES.csv", B["rules"], [
        "RULE_ID", "SOURCE_PAGE", "SOURCE", "WORDING", "BAR_ROLE", "RULE_KIND", "SPAN_DEFINITION",
        "MEASUREMENT_ORIGIN", "APPLICABILITY", "CONTINUITY", "DIRECTION", "WHICH_50_PERCENT", "ENDPOINT",
        "NTS_STATUS", "EVIDENCE", "GATE", "GATE_BLOCKERS", "STATE"])
    rr = B["run_rows"] + B["top_runs"]
    _csv("07_BAR_RUN_REGISTER.csv", rr, list(rr[0]))
    _csv("08_OPENING_REGISTER.csv", B["openings"], [
        "OPENING_ID", "FLOOR", "GEOMETRY", "BBOX_MM", "AREA_M2", "TYPE", "SOURCE", "PANEL_OWNER",
        "REBAR_DEDUCTION_RULE", "TRIM_BAR_RULE", "DIAGONAL_BAR_RULE", "STATE", "BAR_EFFECT"])
    _csv("09_TEMPERATURE_REBAR_REGISTER.csv", B["temp_rows"], list(B["temp_rows"][0]))
    _csv("10_COUNT_RULE_REGISTER.csv", B["count_rows"], list(B["count_rows"][0]))
    _csv("11_SOURCE_CONFLICTS.csv", B["conflicts"], ["CONFLICT_ID", "KIND", "WHERE", "EVIDENCE", "STATE",
                                                    "CANDIDATES", "RESOLUTION"])
    _csv("12_SOURCE_EXPECTED_NOT_LOCATED.csv", B["senl_rows"], list(B["senl_rows"][0]))
    _csv("14_S7_RELEASE_CANDIDATES.csv", B["cands"], [
        "COMPONENT_ID", "COMPONENT", "OWNER", "FLOOR", "DIRECTION", "TOKEN", "DIA_MM", "RATE_OR_COUNT",
        "LENGTH_STATE", "LENGTH_RULE", "BLOCKED_PORTIONS", "STATE", "DECISIONS_NEEDED", "LAYER_AUTHORITY", "KG"])
    _csv("15_ENGINEER_QUESTIONS.csv", B["q_rows"], ["QUESTION_ID", "QUESTION", "LINKED_TO", "ASKED_OF",
                                                    "COMPONENTS_AFFECTED", "AFFECTS", "STATE"])
    with open(HERE / "13_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for kind, rows, key in (("PANEL", census, "SLAB_PANEL_ID"), ("TOKEN", B["tok_rows"], "TOKEN_ID"),
                                ("SUPPORT", supports, "SUPPORT_ID"), ("COMPONENT", crow, "COMPONENT_ID"),
                                ("BAR_RUN", rr, "BAR_RUN_ID"), ("OPENING", B["openings"], "OPENING_ID"),
                                ("CONFLICT", B["conflicts"], "CONFLICT_ID")):
            for r in rows:
                f.write(json.dumps({"kind": kind, "id": r[key], "source": "ST7757.dxf " + DRAWING_SHA[:12] +
                                    " + frozen S1 registers", "round": ROUND, "record": {
                                        k: v for k, v in r.items() if not k.startswith("_")}},
                                   sort_keys=True, ensure_ascii=False, default=str) + "\n")
    summary = summarise(B)
    _json("PRE_S7_SUMMARY.json", summary)
    (HERE / "00_README.md").write_text(readme(B, summary), encoding="utf-8")
    return summary


def summarise(B):
    census, comps, supports = B["census"], B["comps"], B["supports"]
    ins = [c for c in census if c["SCOPE"] == SR.IN_SCOPE]
    area = defaultdict(float)
    for c in ins:
        area[c["FLOOR"]] += c["GEOMETRIC_AREA_M2"]
    thick = Counter(f"{c['THICKNESS_MM']:g} mm ({c['THICKNESS_AUTHORITY']})" for c in census
                    if c["SCOPE"] == SR.IN_SCOPE)
    thick_blocked = Counter(f"{c['THICKNESS_MM']:g} mm ({c['THICKNESS_AUTHORITY']})" for c in census
                            if c["SCOPE"] == SR.CLASSIFICATION_BLOCKED and c["THICKNESS_MM"])
    local = [t["SLAB_PANEL_ID"] for t in B["thick_rows"] if t["AUTHORITY"] == SR.LOCAL_PANEL]
    overrides = [t["SLAB_PANEL_ID"] for t in B["thick_rows"] if t["AUTHORITY"] == SR.LOCAL_PANEL and t["OVERRIDDEN"]]
    bfam = {(c["panel"], c["direction"], c["scope"]) for c in comps if c.get("bar_role", "").startswith("BOTTOM")}
    tok = Counter(t["TERMINAL_STATE"] for t in B["tok_rows"])
    comp_k = Counter(c["component"] for c in comps)
    ready = Counter(c["readiness"] for c in comps)
    cand_k = Counter(c["STATE"] for c in B["cands"])
    temp_unres = [t for t in B["temp_rows"] if t["TABLE_STATE"] == SR.TABLE_NO_EXACT_ROW]
    families = [c for c in comps if c["component"] in ("BOTTOM_X", "BOTTOM_Y", "CURTAILMENT_SEGMENT",
                                                         "CONTINUOUS_BAR_RUN")]
    return {
        "round": ROUND, "policy": POLICY, "baseline_head": BASELINE_HEAD, "no_kg": True,
        "frozen": {k: {kk: v[kk] for kk in ("manifest", "manifest_sha256", "round", "files_checked")}
                   for k, v in B["frozen"].items()},
        "floors_included": sorted({c["FLOOR"] for c in ins}),
        "geometries": len(census), "geometries_by_scope": dict(Counter(c["SCOPE"] for c in census)),
        "panels_in_scope": len(ins), "panels_in_scope_by_floor": dict(Counter(c["FLOOR"] for c in ins)),
        "panels_in_scope_by_class": dict(Counter(c["PANEL_CLASS"] for c in ins)),
        "slab_area_in_scope_m2_by_floor": {k: round(v, 3) for k, v in sorted(area.items())},
        "slab_area_in_scope_m2": round(sum(area.values()), 3),
        "classification_blocked": [c["SLAB_PANEL_ID"] for c in census if c["SCOPE"] == SR.CLASSIFICATION_BLOCKED],
        "excluded_special": [c["SLAB_PANEL_ID"] for c in census if c["SCOPE"] == SR.EXCLUDED_SPECIAL],
        "thickness_distribution": dict(thick), "thickness_classification_blocked": dict(thick_blocked),
        "local_thickness_panels": local, "local_thickness_overrides": overrides,
        "local_marks_confirming_default": [p for p in local if p not in overrides],
        "bottom_families": dict(Counter(sc for _, _, sc in bfam)),
        "tokens_found": len(B["tok_rows"]), "tokens_by_state": dict(tok),
        "tokens_bound": sum(v for k, v in tok.items() if k in SR.BAR_PRODUCING),
        "token_conservation": B["tcons"]["checks"],
        "components_by_type": dict(comp_k), "components_by_readiness": dict(ready),
        "bottom_populations": len([c for c in comps if c.get("bar_role", "").startswith("BOTTOM")]),
        "top_populations": len([c for c in comps if c["component"] in ("TOP_X", "TOP_Y")]),
        "support_populations": len([c for c in comps if c["component"].startswith("TOP_SUPPORT")]),
        "temperature_populations": len([c for c in comps if c["component"].startswith("TEMPERATURE")]),
        "temperature_160_180_unresolved": len(temp_unres),
        "temperature_unresolved_by_thickness": dict(Counter(f"{t['THICKNESS_MM']:g}:{t['SCOPE']}" for t in temp_unres)),
        "supports": len(supports), "supports_by_type": dict(Counter(s["SUPPORT_TYPE"] for s in supports)),
        "support_rules": {r["RULE_ID"]: r["STATE"] for r in B["rules"]},
        "bar_runs": {"bottom": len(B["run_rows"]), "bottom_multi_panel": len([r for r in B["run_rows"]
                                                                              if r["KIND"].endswith("CONTINUOUS")]),
                     "top_support": len(B["top_runs"])},
        "openings": len(B["openings"]), "openings_by_type": dict(Counter(o["TYPE"] for o in B["openings"])),
        "source_conflicts": len(B["conflicts"]), "senl": len(B["senl_rows"]), "questions": len(B["q_rows"]),
        "s7_candidates": dict(cand_k), "s7_release_candidates": cand_k.get("S7_RELEASE_CANDIDATE", 0),
        "conditional_candidates": cand_k.get("CONDITIONAL_ON_OWNER_DECISIONS", 0),
        "blocked_from_s7": ready.get(SR.BLOCKED_FROM_S7, 0) - cand_k.get("CONDITIONAL_ON_OWNER_DECISIONS", 0),
        "gates": B["gates"], "cover_basis": B["cover"],
        "note2_decoded": {k: v["arabic"] for k, v in B["note2"].items()},
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "flags": {"kg_calculated": False, "s7_started": False, "interpolated_temperature": False,
                  "nts_measured": False, "donor_or_code_used": False, "references_read": []},
        "component_type_instantiation": instantiation(B)}


def instantiation(B):
    have = Counter(c["component"] for c in B["comps"])
    why = {"MID_STRIP_TOP": "beam-supported slabs: no strip definition in the source",
           "COLUMN_STRIP_TOP": "beam-supported slabs: no strip definition in the source",
           "OPENING_EXTRA_TOP": "no extra / trim callout at any opening (SENL-08)",
           "OPENING_EXTRA_BOTTOM": "no extra / trim callout at any opening (SENL-08)",
           "OPENING_TRIM": "no trim callout (SENL-08)", "EDGE_BAR": "no edge-bar callout or note",
           "DIAGONAL_BAR": "only the corner reinforcement is diagonal (CORNER_BAR)",
           "LAP": "temperature lap 40 D is carried on the TEMPERATURE rows; main-bar lap not located (SENL-05)",
           "DEVELOPMENT": "not located", "HOOK": "no hook drawn on the slab detail",
           "BEND": "carried as a blocked portion of TOP_SUPPORT at non-continuous supports (leg shape only)",
           "TOP_X": "only (T&B) callouts give top panel bars", "TOP_Y": "only (T&B) callouts give top panel bars"}
    return {t: ({"state": "INSTANTIATED", "rows": have[t]} if have.get(t) else
                {"state": "NOT_INSTANTIATED", "why": why.get(t, "no project source")}) for t in SR.COMPONENT_TYPES}


def readme(B, s):
    fl = ", ".join(s["floors_included"])
    lines = [
        "# PRE-S7: elevated slab rebar readiness / source exhaustion", "",
        f"**Round:** `{ROUND}` · **Policy:** `{POLICY}` · **Baseline:** HEAD `{BASELINE_HEAD}` · **Built by** "
        "`build_pre_s7.py` (blind, byte-identical rebuild) · **No kg is calculated.**", "",
        "S4 to D1.2 are unchanged: all nine freeze manifests were hash-checked before anything was read. S7 was not "
        "started.", "",
        "## Scope", "",
        f"- Floors in scope: {fl}.",
        f"- Geometries: {s['geometries']} ({', '.join(f'{k} {v}' for k, v in sorted(s['geometries_by_scope'].items()))}).",
        f"- In-scope slab panels: {s['panels_in_scope']} "
        f"({', '.join(f'{k} {v}' for k, v in sorted(s['panels_in_scope_by_floor'].items()))}); "
        f"area {s['slab_area_in_scope_m2']} m².",
        f"- Excluded to the special-structures round (stairs, domes): {len(s['excluded_special'])}. "
        f"Classification blocked: {', '.join(s['classification_blocked'])}.", "",
        "## What the source settles", "",
        "- **L is the clear span.** The p.15 slab-on-beams detail labels L1 and L2 CLEAR SPAN, face to face.",
        "- **The rules are measured from the support face:** 0.25 L1 (non-continuous), 0.30 max(L1, L2) (continuous), "
        "50% of the bottom bars stop 0.125 L short of a continuous support, the balance runs through.",
        "- **Thickness:** 160 mm default (p.8 note 18 + p.1 note); local T marks override (T 18 on two panels; T 16 "
        "marks confirm the default). No floor rule. No conflict.",
        "- **Cover:** 25 mm is a minimum (note 22, D1.2): straight runs at 25 mm are maxima, never exact.",
        "- **Temperature table:** no 160 / 180 row. Nothing is interpolated.", "",
        "## What blocks S7", "",
        f"- {s['source_conflicts']} source conflicts (11_SOURCE_CONFLICTS.csv), {s['senl']} items expected and not "
        f"located (12), {s['questions']} engineer questions (15).",
        "- Every rate callout needs a count rule (first bar, edge bars): none is stated.",
        "- Top bars over beams: plan note 2 says 5Ø10/m, 'one third of the span', both directions; p.15 says "
        "0.25 L1 / 0.30 max(L1, L2). They disagree and the note does not define its span.",
        f"- Components: {sum(s['components_by_readiness'].values())}; S7 release candidates "
        f"{s['s7_release_candidates']}; conditional on owner decisions {s['conditional_candidates']}; "
        f"blocked {s['blocked_from_s7']}.", "",
        "## Files", "",
        "| File | Content |", "|---|---|",
        "| 01_SLAB_PANEL_CENSUS.csv | every slab-plan face and dense-hatch strip, one scope each |",
        "| 02_THICKNESS_REGISTER.csv | local / floor / default ladder per slab face |",
        "| 03_SLAB_REBAR_TOKENS.csv | every rebar notation on the slab sheets, one terminal state each |",
        "| 04_COMPONENT_READINESS.csv | instantiated components, blockers, readiness (no kg) |",
        "| 05_SUPPORT_REGISTER.csv | one row per support (shared edges counted once) |",
        "| 06_SUPPORT_RULES.csv | the p.15 and plan-note rules with their gates |",
        "| 07_BAR_RUN_REGISTER.csv | bottom runs (balance continuous) and top-support runs |",
        "| 08_OPENING_REGISTER.csv | voids, shafts, opening strips, void labels |",
        "| 09_TEMPERATURE_REBAR_REGISTER.csv | thickness vs the p.15 table (exact rows only) |",
        "| 10_COUNT_RULE_REGISTER.csv | rate, distribution width and count rule kept apart |",
        "| 11 / 12 / 15 | conflicts, expected-not-located, engineer questions |",
        "| 13_PROVENANCE.jsonl | one line per record |",
        "| 14_S7_RELEASE_CANDIDATES.csv | candidates and the decisions they wait for |",
        "| PRE_S7_SUMMARY.json | counts, gates, flags |",
        "| source_search_inputs/PRE_S7_VISUAL_READING.json | p.15 / pp.4-6 visual reading (render hashes only) |", ""]
    return "\n".join(lines)


def main():
    B = build()
    summary = write(B)
    man = {"round": ROUND, "state": "FROZEN", "references_read_before_freeze": [],
           "rule": "a readiness register: no kg; frozen stages are never edited",
           "engine_commit_stamp": summary["engine_commit"],
           "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
           "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
           "drawing_sha256": {"ST7757.dxf": DRAWING_SHA, "ST7757.pdf": PDF_SHA},
           "frozen_baselines": {k: v["manifest_sha256"] for k, v in B["frozen"].items()}}
    _json("PRE_S7_FREEZE_MANIFEST.json", man)
    print(json.dumps({k: summary[k] for k in ("panels_in_scope", "slab_area_in_scope_m2", "tokens_found",
                                              "tokens_by_state", "components_by_readiness", "s7_candidates",
                                              "source_conflicts", "gates")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
