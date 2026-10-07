"""R9.1 - christiannp post-freeze OBJECT-LEVEL comparison (research only).

Reads
  * the frozen christiannp forensic re-run (CHRISTIANNP_FORENSIC_RERUN_2026_10_07, extracted from the ZIP; path as
    argv[1]); every file read is checked against FORENSIC_FREEZE_MANIFEST.json before use;
  * frozen Urban registers at HEAD (S1 census, V3 / V3b / B2A1 registers, coverage-round QUANTITY_SCENARIOS and
    extracts) and the two R9.1 Urban-only geometry extracts (urban_extract/, scripts/extract_urban_geometry.py);
  * the three Urban bar parsers (engine.source.schedule_grammar / structural_schedule / slab_rebar_binding), called
    read-only on the christiannp token corpus.

Writes the CSV / JSON deliverables of R9_1_CHRIS_POST_FREEZE (02, 03, 05-12, 14, 15) plus CHRIS_INPUT_LEDGER.json.
The markdown deliverables are written by hand from these outputs. Nothing in engine/ is modified, no AutoCAD / MCP
call is made and no christiannp script is executed. The Urban side was frozen before this comparison (HEAD 2c00561);
no christiannp, U-C4N or freelancer value enters any Urban register.

    python research/R9_1_CHRIS_POST_FREEZE/scripts/build_r9_1.py <CHRISTIANNP_FORENSIC_RERUN_2026_10_07 dir>
"""

from __future__ import annotations

import ast
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
OUT = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import schedule_grammar as SG  # noqa: E402
from engine.source import slab_rebar_binding as SRB  # noqa: E402
from engine.source import structural_schedule as SS  # noqa: E402
from engine.source import wall_band_reconciliation as WB  # noqa: E402

ZIP_SHA256 = "fcaff77001a470bb2187e086f42b6cdbc435f8b5ea02126c9cb7aea67bce7b80"
MANIFEST_SHA256 = "af2d3441cf2d464e5fb31c8651a540abf22ff5dc55f9d34786f9506038197bf2"
URBAN_HEAD = "2c00561"
DRAWINGS = {"ST7757.dxf": "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079",
            "P7757.dxf": "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"}
STAMP = {"URBAN_ENGINE_COMMIT": URBAN_HEAD, "CHRIS_DATASET": "CHRISTIANNP_FORENSIC_RERUN_2026_10_07",
         "CHRIS_MANIFEST_SHA256": MANIFEST_SHA256, "CALCULATION_ROUND": "R9.1"}

CLASSES = ("SAME_OBJECT_SAME_RESULT", "SAME_OBJECT_DIFFERENT_SEGMENTATION", "SAME_GEOMETRY_DIFFERENT_CONVENTION",
           "URBAN_MISSED_PHYSICAL_OBJECT", "CHRIS_MISSED_PHYSICAL_OBJECT", "URBAN_BINDING_FAILURE",
           "CHRIS_BINDING_FAILURE", "URBAN_PUBLICATION_LOSS", "SOURCE_AUTHORITY_DIFFERENCE", "ASSUMPTION_DIFFERENCE",
           "DONOR_FALSE_POSITIVE", "URBAN_FALSE_POSITIVE", "DONOR_HEURISTIC", "SOURCE_CONFLICT", "NOT_COMPARABLE",
           "UNKNOWN")


# ------------------------------------------------------------------------------------------------------- io
class Chris:
    """Read-only access to the frozen dataset; every file is hash-checked against the freeze manifest."""

    def __init__(self, root):
        self.root = Path(root)
        raw = (self.root / "FORENSIC_FREEZE_MANIFEST.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
            raise SystemExit("christiannp manifest hash differs from the frozen dataset")
        self.manifest = json.loads(raw)
        self.files = {f["path"]: f for f in self.manifest["files"]}
        self.read = {}

    def bytes(self, rel):
        b = (self.root / rel).read_bytes()
        h = hashlib.sha256(b).hexdigest()
        if rel not in self.files or self.files[rel]["sha256"] != h:
            raise SystemExit(f"christiannp file {rel} is not the frozen version")
        self.read[rel] = h
        return b

    def csv(self, rel):
        return list(csv.DictReader(io.StringIO(self.bytes(rel).decode("utf-8"))))

    def json(self, rel):
        return json.loads(self.bytes(rel))


def UJ(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def r3(x):
    return None if x is None else round(float(x), 3)


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def write_csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    (OUT / name).write_text(buf.getvalue(), encoding="utf-8")
    return buf.getvalue()


def _origin(ch, region):
    for r in ch.csv("04_plan_regions/PLAN_REGION_REGISTER.csv"):
        if r["REGION_ID"] == region:
            return tuple(json.loads(r["LOCAL_ORIGIN(frame min)"]))
    raise KeyError(region)


XW = ["URBAN_OBJECT_ID", "CHRIS_OBJECT_ID", "TRADE", "FLOOR", "SOURCE_HANDLES", "X", "Y", "BBOX", "MARK", "GEOMETRY",
      "URBAN_VALUE", "CHRIS_VALUE", "UNIT", "MATCH_METHOD", "MATCH_DISTANCE", "MATCH_CONFIDENCE", "DIFFERENCE_CLASS",
      "NOTES"]


# ============================================================================================ 03 ground beams
def ground_beams(ch):
    U = UJ("research/R9_1_CHRIS_POST_FREEZE/urban_extract/URBAN_GB_GEOMETRY_EXTRACT.json")
    G = UJ("tests/alsenan/registers_v3/GROUND_STRUCTURE_REGISTER.json")["ground"]
    Q = UJ("research/coverage_recovery_round/QUANTITY_SCENARIOS.json")["ground_beams"]
    O = _origin(ch, "ST_GBP")
    strips = ch.csv("06_ground_beams/GROUND_BEAM_STRIPS.csv")
    pairs = {p["PAIR_ID"]: p for p in ch.csv("06_ground_beams/GROUND_BEAM_PAIR_CANDIDATES.csv")}
    edges = defaultdict(list)
    for e in ch.csv("06_ground_beams/GROUND_BEAM_EDGES.csv"):
        edges[e["STRIP"]].append(e)
    band_of = {}
    for b in ch.csv("06_ground_beams/GROUND_BEAM_BANDS.csv"):
        for s in b["STRIPS"].split("|"):
            band_of[s] = b["BAND_ID"]
    summ = ch.json("06_ground_beams/GROUND_BEAM_SUMMARY.json")
    # Urban spans (frozen ids) -> band, kind, depth
    span_rec = {s["span"]: s for s in Q["spans"]}
    spans_by_band = defaultdict(list)
    for s in G["spans"]:
        spans_by_band[s["band"]].append(s)
    ub = {frozenset(b["face_handles_hex"]): b for b in U["bands"]}
    rows, used = [], set()
    for s in strips:
        key = frozenset([s["FACE_A"].upper(), s["FACE_B"].upper()])
        m = ub.get(key)
        co = re.search(r"COLUMN_OVERLAP_LEN=([\d.]+)", s["COLUMN_FOOTING_CONNECTIONS"])
        col = float(co.group(1)) / 1000.0 if co else 0.0
        L = float(s["CENTERLINE_LENGTH"]) / 1000.0
        p0 = (float(s["CENTERLINE_START_X"]), float(s["CENTERLINE_START_Y"]))
        p1 = (float(s["CENTERLINE_END_X"]), float(s["CENTERLINE_END_Y"]))
        curved = bool(s["CURVE_GEOMETRY"])
        ne = len(edges[s["STRIP_ID"]])
        row = {"CHRIS_OBJECT_ID": f"{s['STRIP_ID']} ({s['PAIR_ID']}, {band_of.get(s['STRIP_ID'])}, {ne} edges)",
               "TRADE": "GROUND_BEAM", "FLOOR": "GROUND_BEAMS_PLAN",
               "SOURCE_HANDLES": f"{s['FACE_A']}|{s['FACE_B']}",
               "X": r3((p0[0] + p1[0]) / 2), "Y": r3((p0[1] + p1[1]) / 2), "MARK": "(untagged)",
               "GEOMETRY": ("ARC " + s["CURVE_GEOMETRY"]) if curved else f"LINE w={s['DRAWN_WIDTH']}",
               "CHRIS_VALUE": f"strip {L:.3f} m; in-column {col:.3f}; net {L - col:.3f}", "UNIT": "m"}
        if not m:
            pc = pairs[s["PAIR_ID"]]
            row.update(URBAN_OBJECT_ID="(none)", URBAN_VALUE="0", MATCH_METHOD="FACE_HANDLE_PAIR (no Urban band)",
                       MATCH_DISTANCE="", MATCH_CONFIDENCE="HIGH", BBOX="",
                       DIFFERENCE_CLASS="URBAN_MISSED_PHYSICAL_OBJECT",
                       NOTES=(f"face {s['FACE_A']} ({pc['FACE_A_LENGTH']} mm) has two collinear partners on the other "
                              f"side ({s['FACE_B']} {pc['FACE_B_LENGTH']} mm and 7DF); Urban _pair_bands keeps one "
                              "best partner per face and scans forward only, so this 300 mm pair is never formed. "
                              "Generic defect: fragmented-mate pairing (A: network geometry)."))
            rows.append(row)
            continue
        used.add(m["band_id"])
        kept = [p for p in m["pieces"] if p["kept_as_span"]]
        sp = sorted(spans_by_band[m["band_id"]], key=lambda z: z["id"])
        urb_len = sum(p["length_m"] for p in kept)
        kinds = Counter(span_rec[z["id"]]["kind"] for z in sp)
        depth = sorted({(span_rec[z["id"]]["depth_level"], span_rec[z["id"]]["depth_m"]) for z in sp})
        bb = m["bbox"]
        lbb = [round(bb[0] - O[0], 1), round(bb[1] - O[1], 1), round(bb[2] - O[0], 1), round(bb[3] - O[1], 1)]
        if m.get("centreline"):
            c0 = (m["centreline"][0][0] - O[0], m["centreline"][0][1] - O[1])
            c1 = (m["centreline"][1][0] - O[0], m["centreline"][1][1] - O[1])
            dist = max(_pt_line(p0, c0, c1), _pt_line(p1, c0, c1))
        else:
            dist = None
        dg = m["gross_length_m"] - L
        dn = urb_len - (L - col)
        if abs(dg) < 0.002 and abs(dn) < 0.002:
            cls, note = "SAME_OBJECT_SAME_RESULT", "same face pair, same length, same column split"
        elif curved and abs(dg) >= 0.002:
            cls = "SAME_GEOMETRY_DIFFERENT_CONVENTION"
            note = (f"same concentric arc pair; Urban _arc_bands uses ONE arc's sweep x mean radius (gross "
                    f"{m['gross_length_m']:.3f} m), christiannp uses the ANGULAR OVERLAP of both arcs ({L:.3f} m); "
                    f"Urban then removes {m['gross_length_m'] - urb_len:.3f} m inside column 17BD, christiannp does "
                    "not clip arcs at columns (E: curves)")
        elif abs(dg) < 0.002:
            cls = "SAME_GEOMETRY_DIFFERENT_CONVENTION"
            note = (f"same faces and gross length; column split differs: Urban removes {m['gross_length_m'] - urb_len:.3f} m "
                    f"(band polygon minus column rectangles, piece extent; a column that does not cover the full band "
                    f"width leaves the extent unchanged), christiannp removes {col:.3f} m (centreline clipped by every "
                    "S-COL.BON box it crosses, end boxes included) (F: support splitting)")
        else:
            cls, note = "UNKNOWN", "same faces, different gross length"
        row.update(URBAN_OBJECT_ID=f"{m['band_id']} -> {','.join(z['id'] for z in sp)}",
                   URBAN_VALUE=(f"gross {m['gross_length_m']:.3f} m; spans {urb_len:.3f} m in {len(kept)}; "
                                f"kinds {dict(kinds)}; depth {depth}"),
                   BBOX=json.dumps(lbb), MATCH_METHOD="FACE_HANDLE_PAIR_EXACT",
                   MATCH_DISTANCE="" if dist is None else f"{dist:.1f} mm centreline offset",
                   MATCH_CONFIDENCE="HIGH", DIFFERENCE_CLASS=cls, NOTES=note)
        rows.append(row)
    for b in U["bands"]:
        if b["band_id"] not in used:
            rows.append({"URBAN_OBJECT_ID": b["band_id"], "CHRIS_OBJECT_ID": "(none)", "TRADE": "GROUND_BEAM",
                         "DIFFERENCE_CLASS": "CHRIS_MISSED_PHYSICAL_OBJECT", "NOTES": "Urban band with no christiannp strip"})
    # strap beams (foundation plan): same faces, length convention
    sbu = {frozenset(format(int(h.split("|")[1][1:]), "X") for h in r["band"]): r
           for r in UJ("tests/alsenan/registers_a3/STRAP_BEAM_REGISTER.json")["rows"]}
    for sb in ch.csv("06_ground_beams/STRAP_BEAM_STRIPS.csv"):
        u = sbu.get(frozenset([sb["FACE_A"].upper(), sb["FACE_B"].upper()]))
        L = float(sb["CENTERLINE_LENGTH"]) / 1000.0
        rows.append({"URBAN_OBJECT_ID": u and f"{u['type']} ({u['state']})", "CHRIS_OBJECT_ID": f"{sb['STRIP_ID']} ({sb['NEAREST_LABEL']})",
                     "TRADE": "STRAP_BEAM", "FLOOR": "FOUNDATION_PLAN", "SOURCE_HANDLES": f"{sb['FACE_A']}|{sb['FACE_B']}",
                     "MARK": sb["NEAREST_LABEL"], "GEOMETRY": f"LINE w={sb['DRAWN_WIDTH']} (schedule row by drawn width)",
                     "URBAN_VALUE": u and f"clear {u['length_m']:.3f} m x {u['B_cm'] / 100:.2f} x {u['D_cm'] / 100:.2f} = {u['volume_m3']:.3f} m3",
                     "CHRIS_VALUE": f"strip {L:.3f} m = {sb['VOLUME_M3']} m3", "UNIT": "m / m3",
                     "MATCH_METHOD": "FACE_HANDLE_PAIR_EXACT" if u else "NONE", "MATCH_CONFIDENCE": "HIGH",
                     "DIFFERENCE_CLASS": "SAME_GEOMETRY_DIFFERENT_CONVENTION" if u else "URBAN_MISSED_PHYSICAL_OBJECT",
                     "NOTES": "same face pair and the same width-selected schedule row (SB2 W=100 from 987 mm, christiannp "
                              "MD17 / R4 = Urban MEASURED_WITH_WIDTH_DEVIATION); Urban measures the CLEAR length between "
                              "footing outlines, christiannp the full face overlap, which runs inside the footings whose "
                              "concrete is already counted (double count of the overlap)"})
    # topology / segmentation summary and the depth authority row (G)
    urb_gross = sum(b["gross_length_m"] for b in U["bands"])
    urb_spans = sum(p["length_m"] for b in U["bands"] for p in b["pieces"] if p["kept_as_span"])
    seg = {"URBAN": {"bands": len(U["bands"]), "spans": len(G["spans"]), "gross_band_length_m": round(urb_gross, 3),
                     "span_length_m": round(urb_spans, 3), "frozen_register_length_m": r3(Q["length_m"]),
                     "exterior_spans": sum(1 for s in Q["spans"] if s["kind"] == "EXTERIOR"),
                     "interior_spans": sum(1 for s in Q["spans"] if s["kind"] == "INTERIOR"),
                     "columns_on_sheet": len(U["columns"]), "layer1_lines": len(U["layer1_segments"]),
                     "layer1_arcs": len(U["layer1_arcs"])},
           "CHRIS": {k: summ[k] for k in ("strips", "bands", "edges", "support_to_support_spans", "nodes_by_kind",
                                          "MEASURED_NETWORK_LENGTH_STRIP_CENTERLINES_MM", "straight_strip_length_mm",
                                          "curved_strip_length_mm", "strip_length_inside_column_boxes_mm",
                                          "MEASURED_NETWORK_LENGTH_NET_OF_COLUMN_OVERLAP_MM",
                                          "NODE_TO_NODE_EDGE_LENGTH_MM", "raw_segments_on_face_layer_1",
                                          "pair_candidates", "accepted_pairs", "rejections_by_reason")}}
    rows.append({"URBAN_OBJECT_ID": "GB depth authority (all 59 spans)", "CHRIS_OBJECT_ID": "A03 / U01",
                 "TRADE": "GROUND_BEAM", "FLOOR": "GROUND_BEAMS_PLAN", "GEOMETRY": "section depth",
                 "URBAN_VALUE": "interior: ST7757 p.13 typical GB sections by span length (0.30 / 0.40 / 0.60 m, DETAIL "
                                "level, raster/visual lane); exterior: FOLLOW ARCH. -> BOUNDED_CANDIDATE 1.0 m",
                 "CHRIS_VALUE": "UNKNOWN after 8 DXF routes; scenarios 0.4 / 0.6 / 0.8 m only", "UNIT": "m",
                 "MATCH_METHOD": "SOURCE_ROUTE", "MATCH_CONFIDENCE": "HIGH",
                 "DIFFERENCE_CLASS": "SOURCE_AUTHORITY_DIFFERENCE",
                 "NOTES": "the p.13 section table is a drawn detail (no DXF TEXT carries it); christiannp searched DXF "
                          "text only, Urban reads it from the visual source lane (R4.1). Depth must stay separate "
                          "from network length (G: depth authority)."})
    return rows, seg


def _in_poly(pt, ring):
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _pt_line(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / L


# ============================================================================================ 05 ground slab
def ground_slab(ch):
    Q = UJ("research/coverage_recovery_round/QUANTITY_SCENARIOS.json")["ground_slab"]
    E = UJ("research/coverage_recovery_round/GROUND_SLAB_CELL_EXTRACT.json")
    O = _origin(ch, "ST_GBP")
    faces = ch.csv("09_slabs/GBP/GBP_VECTOR_FACES.csv")
    conv = ch.csv("09_slabs/GBP/GBP_SLAB_RASTER_CONVERGENCE.csv")
    vec = ch.json("09_slabs/GBP/GBP_SLAB_INPUTS_AND_VECTOR.json")
    qs = {r["ITEM"]: r for r in ch.csv("16_final/QUANTITY_SUMMARY.csv") if r["TRADE"] == "GROUND_SLAB"}
    role = {c["cell_id"]: c["role"] for c in Q["cells"]}
    rows = []
    A = Q["area"]
    fpa = sum({c["footprint_id"]: c["footprint_area_m2"] for c in E["cells"]}.values())
    U = [("URBAN OFFICIAL (VERIFIED: cells inside the two T=10cm zones)", A["VERIFIED_QUANTITY"]),
         ("URBAN LOWER_BOUND / LOW", A["LOWER_BOUND_QUANTITY"]),
         ("URBAN BEST / HIGH (+ 9 unlabelled cells between ground beams)", A["BEST_PROVISIONAL_QUANTITY"]),
         ("URBAN founded footprints (bands 1+2, arcs, columns, single lines; before cell subtraction)", fpa)]
    best = A["BEST_PROVISIONAL_QUANTITY"]
    for name, v in U:
        rows.append({"ROW_KIND": "ROUTE", "SYSTEM": "URBAN", "ROUTE": name, "AREA_M2": r3(v),
                     "DIFF_VS_URBAN_BEST_M2": r3(v - best), "AREA_AUTHORITY": "VECTOR_CELLS (ground_slab_recovery)",
                     "THICKNESS_M": Q["thickness"]["value"], "THICKNESS_AUTHORITY":
                         f"{Q['thickness']['level']} / {Q['thickness']['authority']} ('T=10cm' H5776 / H5789 = TT1 1690 / 169D)",
                     "BEAMS_EXCLUDED": "YES (300 mm bands layers 1+2)", "COLUMNS_EXCLUDED": "YES",
                     "OPENINGS_EXCLUDED": "lift pit: see CELL rows", "ROUTE_CLASS": "PRODUCTION (frozen)"})
    chris_routes = [
        ("CHRIS ROUTE1v vector planar faces (sampled apportioning)", qs["ROUTE1v vector planar faces (sampled apportioning)"]["VALUE"], "VECTOR_FACES", "PRODUCTION_CANDIDATE (concept)"),
        ("CHRIS vector point-classification", vec["vector"]["VECTOR_NET_SLAB_M2"], "VECTOR_FACES", "CHALLENGER_ONLY (mislabels mixed faces)"),
        ("CHRIS ROUTE3 footprint - beams - columns - pit", qs["ROUTE3 footprint - beams - columns - pit"]["VALUE"], "VECTOR_FACES", "same as ROUTE1v"),
        ("CHRIS ROUTE2 footprint inside GB outer faces (vector)", qs["ROUTE2 overall footprint inside GB outer faces (vector)"]["VALUE"], "VECTOR_OUTLINE", "NOT_SLAB (includes beams, columns, pit)"),
        ("CHRIS ROUTE2b site boundary S-BOUN 1658", qs["ROUTE2b site boundary polygon S-BOUN 1658 (NOT slab)"]["VALUE"], "PROPERTY_LINE", "REJECT (property line)"),
    ]
    for name, v, auth, cl in chris_routes:
        v = float(v)
        rows.append({"ROW_KIND": "ROUTE", "SYSTEM": "CHRIS", "ROUTE": name, "AREA_M2": r3(v),
                     "DIFF_VS_URBAN_BEST_M2": r3(v - best), "AREA_AUTHORITY": auth, "THICKNESS_M": 0.10,
                     "THICKNESS_AUTHORITY": "SOURCE_TEXT TT1 1690 / 169D 'T=10cm' (applied to all cells)",
                     "BEAMS_EXCLUDED": "YES (accepted 300 mm strips)" if "ROUTE2" not in name else "NO",
                     "COLUMNS_EXCLUDED": "YES" if "ROUTE2" not in name else "NO",
                     "OPENINGS_EXCLUDED": "YES (lift pit 7BE 3.24 m2)" if "ROUTE2" not in name else "NO",
                     "ROUTE_CLASS": cl})
    for c in conv:
        for col, lab in (("NET_SLAB_AREA_M2", "slab cells only"), ("NET_SLAB_PLUS_HALF_ADJ_EDGE_M2", "+ half adjacent edge")):
            v = float(c[col])
            rows.append({"ROW_KIND": "ROUTE", "SYSTEM": "CHRIS", "ROUTE": f"RASTER {c['RESOLUTION_MM']} mm {c['GRID_ORIGIN_SHIFT'].split(' ')[0]} {lab}",
                         "AREA_M2": r3(v), "DIFF_VS_URBAN_BEST_M2": r3(v - best), "AREA_AUTHORITY": "RASTER_FLOOD_FILL",
                         "THICKNESS_M": 0.10, "THICKNESS_AUTHORITY": "SOURCE_TEXT TT1",
                         "BEAMS_EXCLUDED": "YES (strip mask)", "COLUMNS_EXCLUDED": "YES (filled)",
                         "OPENINGS_EXCLUDED": f"YES ({c['OPENING_M2']} m2 marker component)",
                         "ROUTE_CLASS": "ORACLE_ONLY",
                         "NOTES": f"edge cells {c['EDGE_CELLS']}, unresolved {c['UNRESOLVED_ENCLOSED_CELLS']}, footprint {c['FOOTPRINT_NOT_OUTSIDE_M2']} m2"})
    # cell-level crosswalk by containment: every christiannp vector face's interior point is located in the Urban
    # cell polygons (urban_extract/URBAN_GROUND_CELL_GEOMETRY_EXTRACT.json); one Urban cell may hold several faces.
    UG = UJ("research/R9_1_CHRIS_POST_FREEZE/urban_extract/URBAN_GROUND_CELL_GEOMETRY_EXTRACT.json")["cells"]
    meta = defaultdict(lambda: {"labels": set(), "roles": set()})
    for c in E["cells"]:
        meta[c["parent_cell"]]["labels"].update(c["labels"])
        meta[c["parent_cell"]]["roles"].add(role.get(c["cell_id"]))
        meta[c["parent_cell"]]["eff"] = c["eff_width_mm"]
    inside = defaultdict(list)
    orphan = []
    for f in faces:
        ip = json.loads(f["INTERIOR_PT"])
        g = (ip[0] + O[0], ip[1] + O[1])
        hit = [c["cell_id"] for c in UG if _in_poly(g, c["exterior"]) and not any(_in_poly(g, h) for h in c["holes"])]
        if hit:
            inside[hit[0]].append(f)
        else:
            orphan.append(f)
    for c in UG:
        fs = inside.get(c["cell_id"], [])
        slab = sum(float(f["SAMPLED_SLAB_M2"]) for f in fs)
        other = Counter(f["CLASS"] for f in fs if f["CLASS"] != "SLAB")
        m = meta[c["cell_id"]]
        d = c["area_m2"] - slab
        if not fs:
            cls, note = ("SAME_GEOMETRY_DIFFERENT_CONVENTION" if m.get("eff", 0) < 450 else "UNKNOWN",
                         "no christiannp face interior point in this Urban cell (sliver / beam-band remnant)")
        elif other.get("OPENING"):
            cls = "URBAN_FALSE_POSITIVE"
            note = (f"the Urban cell contains a christiannp OPENING face (lift pit, S-BW 7BE, 3.24 m2): Urban's barrier "
                    f"set (layers 1+2, columns, single lines) has no S-BW layer, so the pit is counted inside a slab "
                    f"cell; the cell also spans {sum(1 for f in fs if f['CLASS'] == 'SLAB')} christiannp slab faces")
        elif len([f for f in fs if f["CLASS"] == "SLAB"]) > 1:
            cls = "SAME_OBJECT_DIFFERENT_SEGMENTATION"
            note = f"one Urban cell = {len(fs)} christiannp faces ({dict(Counter(f['CLASS'] for f in fs))})"
        elif abs(d) <= max(0.06, 0.02 * c["area_m2"]):
            cls, note = "SAME_OBJECT_SAME_RESULT", "same cell"
        else:
            cls, note = "SAME_OBJECT_DIFFERENT_SEGMENTATION", "same region, boundary set differs"
        rows.append({"ROW_KIND": "CELL", "SYSTEM": "URBAN<->CHRIS", "ROUTE": c["cell_id"], "AREA_M2": c["area_m2"],
                     "CHRIS_FACE": "|".join(f["FACE_ID"] for f in fs),
                     "CHRIS_FACE_CLASS": "|".join(sorted({f["CLASS"] for f in fs})),
                     "CHRIS_FACE_SLAB_M2": r3(slab), "DIFF_VS_URBAN_BEST_M2": r3(d),
                     "URBAN_ROLE": "|".join(sorted(x for x in m["roles"] if x)),
                     "URBAN_LABELS": "|".join(sorted(m["labels"])), "URBAN_EFF_WIDTH_MM": m.get("eff"),
                     "DIFFERENCE_CLASS": cls, "NOTES": note})
    for f in orphan:
        a = float(f["SAMPLED_SLAB_M2"])
        if a <= 0.0:
            continue
        rows.append({"ROW_KIND": "CELL", "SYSTEM": "CHRIS_ONLY", "ROUTE": f["FACE_ID"], "CHRIS_FACE": f["FACE_ID"],
                     "CHRIS_FACE_CLASS": f["CLASS"], "CHRIS_FACE_SLAB_M2": a, "AREA_M2": r3(a),
                     "X_LOCAL": json.loads(f["INTERIOR_PT"])[0], "Y_LOCAL": json.loads(f["INTERIOR_PT"])[1],
                     "DIFFERENCE_CLASS": "SAME_GEOMETRY_DIFFERENT_CONVENTION" if a < 0.5 else "UNKNOWN",
                     "NOTES": "christiannp slab area whose interior point lies in no Urban cell (inside an Urban band / "
                              "barrier or outside the Urban footprint)"})
    return rows


SLAB_FIELDS = ["ROW_KIND", "SYSTEM", "ROUTE", "AREA_M2", "DIFF_VS_URBAN_BEST_M2", "AREA_AUTHORITY", "THICKNESS_M",
               "THICKNESS_AUTHORITY", "BEAMS_EXCLUDED", "COLUMNS_EXCLUDED", "OPENINGS_EXCLUDED", "ROUTE_CLASS",
               "CHRIS_FACE", "CHRIS_FACE_CLASS", "CHRIS_FACE_SLAB_M2", "X_LOCAL", "Y_LOCAL", "URBAN_ROLE",
               "URBAN_LABELS", "URBAN_EFF_WIDTH_MM", "DIFFERENCE_CLASS", "NOTES"]


# ============================================================================================ 06 structural beams
BEAM_FIELDS = ["TAG_KEY", "PLAN", "MARK", "TAG_X_LOCAL", "TAG_Y_LOCAL", "SCHEDULE_WIDTH_MM", "SCHEDULE_DEPTH_MM",
               "CHRIS_TAG_ID", "CHRIS_STATUS", "CHRIS_STRIP", "CHRIS_STRIP_WIDTH_MM", "CHRIS_STRIP_LENGTH_MM",
               "CHRIS_CAND_N", "CHRIS_BEST_DIST_MM", "CHRIS_BEST_WIDTH_DIFF_MM", "CHRIS_BEST_ORIENT_DIFF_DEG",
               "CHRIS_BEST_WITHIN_EXTENT", "CHRIS_REASON", "CHRIS_RULES",
               "URBAN_BEAM_ID", "URBAN_BINDING", "URBAN_MEMBER", "URBAN_MEMBER_CANDIDATES", "URBAN_DRAWN_LENGTH_M",
               "URBAN_WIDTH_DRAWN_MM", "URBAN_ISSUES", "URBAN_TERMINAL", "MATCH_METHOD", "MATCH_CONFIDENCE",
               "BINDING_TECHNIQUE_URBAN", "BINDING_TECHNIQUE_CHRIS", "DIFFERENCE_CLASS", "NOTES"]


def beams(ch):
    rows_u = UJ("research/alsenan_structural_census_s1/BEAM_OCCURRENCE_REGISTER.json")["rows"]
    tags = ch.csv("08_beams/BEAM_TAGS.csv")
    bind = {b["TAG_ID"]: b for b in ch.csv("08_beams/BEAM_BINDINGS.csv")}
    strips = {s["STRIP_ID"]: s for s in ch.csv("08_beams/BEAM_STRIPS.csv")}
    cand = defaultdict(list)
    for c in ch.csv("08_beams/BEAM_BINDING_CANDIDATES.csv"):
        cand[c["TAG_ID"]].append(c)
    rules = defaultdict(list)
    for r in ch.csv("08_beams/BEAM_RULE_TESTS_R1_R5.csv"):
        for t in re.findall(r"[A-Z]+_T\d{3}", r["OBJECTS"]):
            rules[t].append(f"{r['RULE'].split(' ')[0]}:{r['SAFE']}")
    by_h = {}
    by_mark_block = defaultdict(list)
    for r in rows_u:
        if not r["source_id"].startswith("BEAMTAG"):
            continue
        h = r["source_id"].split(":")[-1]
        by_h[(r["sheet"], h)] = r
        if ">" in h:                                   # tag text inside a tag block (b4 / b7 / b20 / B24): virtual key
            by_mark_block[(r["sheet"], r["beam_type"])].append(r)
    used = set()
    out = []
    for t in tags:
        b = bind[t["TAG_ID"]]
        u = by_h.get((t["PLAN"], t["HANDLE"]))
        method = "TAG_HANDLE"
        if u is None and by_mark_block.get((t["PLAN"], t["MARK"])):
            u = by_mark_block[(t["PLAN"], t["MARK"])][0]
            method = "TAG_BLOCK_MARK (Urban keys tag-block text by block path, christiannp by INSERT handle)"
        if u:
            used.add(u["beam_id"])
        cs = sorted(cand[t["TAG_ID"]], key=lambda c: int(c["DIST_MM"]))
        chosen = next((c for c in cs if c["STRIP_ID"] == b["STRIP_ID"]), cs[0] if cs else None)
        st = strips.get(b["STRIP_ID"]) if b["STRIP_ID"] else None
        ub = u.get("binding") if u else None
        cls, note = _beam_class(b, u, chosen)
        out.append({"TAG_KEY": t["HANDLE"], "PLAN": t["PLAN"], "MARK": t["MARK"], "TAG_X_LOCAL": t["X"],
                    "TAG_Y_LOCAL": t["Y"], "SCHEDULE_WIDTH_MM": t["SCHEDULE_WIDTH_MM"],
                    "SCHEDULE_DEPTH_MM": t["SCHEDULE_DEPTH_MM"], "CHRIS_TAG_ID": t["TAG_ID"], "CHRIS_STATUS": b["STATUS"],
                    "CHRIS_STRIP": b["STRIP_ID"], "CHRIS_STRIP_WIDTH_MM": st and st["DRAWN_WIDTH_MM"],
                    "CHRIS_STRIP_LENGTH_MM": st and st["LENGTH_MM"], "CHRIS_CAND_N": len(cs),
                    "CHRIS_BEST_DIST_MM": chosen and chosen["DIST_MM"],
                    "CHRIS_BEST_WIDTH_DIFF_MM": chosen and chosen["WIDTH_DIFF_MM"],
                    "CHRIS_BEST_ORIENT_DIFF_DEG": chosen and chosen["ORIENTATION_DIFF_DEG"],
                    "CHRIS_BEST_WITHIN_EXTENT": chosen and chosen["WITHIN_STRIP_EXTENT"], "CHRIS_REASON": b["REASON"],
                    "CHRIS_RULES": "|".join(sorted(set(rules.get(t["TAG_ID"], [])))),
                    "URBAN_BEAM_ID": u and u["beam_id"], "URBAN_BINDING": ub, "URBAN_MEMBER": u and u.get("member"),
                    "URBAN_MEMBER_CANDIDATES": u and "|".join(u.get("member_candidates") or []),
                    "URBAN_DRAWN_LENGTH_M": u and u.get("drawn_length_m"),
                    "URBAN_WIDTH_DRAWN_MM": u and u.get("width_drawn_mm"),
                    "URBAN_ISSUES": u and "|".join(u.get("issues") or []), "URBAN_TERMINAL": u and u.get("terminal_state"),
                    "MATCH_METHOD": method if u else "NONE", "MATCH_CONFIDENCE": "HIGH" if method == "TAG_HANDLE" else "MEDIUM",
                    "BINDING_TECHNIQUE_URBAN": "beam_binding.bind: tag on merged member line, rotation-aware, schedule "
                                               "breadth checked as a FLAG (never nearest-text)",
                    "BINDING_TECHNIQUE_CHRIS": "nearest strip: parallel <=10 deg + within extent + <=1 m + schedule "
                                               "width = drawn width <=30 mm (R4 as a GATE)",
                    "DIFFERENCE_CLASS": cls, "NOTES": note})
    for r in rows_u:
        if r["source_id"].startswith("BEAMTAG") and r["beam_id"] not in used:
            out.append({"TAG_KEY": r["source_id"], "PLAN": r["sheet"], "MARK": r["beam_type"],
                        "URBAN_BEAM_ID": r["beam_id"], "URBAN_BINDING": r.get("binding"), "MATCH_METHOD": "NONE",
                        "DIFFERENCE_CLASS": "CHRIS_MISSED_PHYSICAL_OBJECT", "NOTES": "Urban tag with no christiannp tag"})
    # unlabelled / untagged population (count level; Urban member stations and christiannp strips use different axes)
    un_c = [s for s in strips.values() if not s["BOUND_MARKS"]]
    un_u = [r for r in rows_u if r.get("binding") == "NO_TAG"]
    for plan in ("GFRS", "FFRS", "SFRS"):
        c = [s for s in un_c if s["PLAN"] == plan]
        u = [r for r in un_u if r["sheet"] == plan]
        out.append({"TAG_KEY": f"UNLABELLED:{plan}", "PLAN": plan, "MARK": "(none)",
                    "CHRIS_STATUS": f"{len(c)} unlabelled strips, {sum(float(s['LENGTH_MM']) for s in c) / 1000:.3f} m",
                    "URBAN_BINDING": f"{len(u)} NO_TAG members, {sum((r.get('support_centreline_length_m') or 0) for r in u):.3f} m "
                                     "support-centreline",
                    "MATCH_METHOD": "POPULATION_COUNT", "MATCH_CONFIDENCE": "LOW",
                    "DIFFERENCE_CLASS": "SAME_OBJECT_DIFFERENT_SEGMENTATION",
                    "NOTES": "both keep untagged beams measured and depth-less (no R5); christiannp counts strips "
                             "(face overlaps), Urban counts members between supports"})
    return out


def _beam_class(b, u, c):
    ub = u.get("binding") if u else None
    if u is None:
        return "URBAN_MISSED_PHYSICAL_OBJECT", "christiannp tag with no Urban row"
    if b["STATUS"] == "ACCEPTED" and ub == "BOUND":
        return "SAME_OBJECT_SAME_RESULT", "both bind the tag"
    if b["STATUS"] == "ACCEPTED" and ub == "AMBIGUOUS":
        return ("URBAN_BINDING_FAILURE", "Urban leaves the tag AMBIGUOUS between members "
                f"{'|'.join(u.get('member_candidates') or [])}; christiannp resolves it with orientation + extent + "
                "width-equality (R4 as a gate). Deterministic tie-break candidate, not a donor value.")
    if b["STATUS"] == "UNRESOLVED" and ub == "BOUND":
        if "width" in b["REASON"]:
            return ("SOURCE_CONFLICT", f"drawn strip width differs from the schedule by {c and c['WIDTH_DIFF_MM']} mm: "
                    "christiannp refuses (R4 gate), Urban binds and raises DRAWN_WIDTH_DIFFERS_FROM_SCHEDULE. "
                    "Neither is wrong; the drawing and schedule disagree.")
        return ("CHRIS_BINDING_FAILURE", "christiannp finds no parallel strip within 1 m (oblique / angled member or "
                f"wide beam; nearest orientation diff {c and c['ORIENTATION_DIFF_DEG']} deg); Urban binds on the merged "
                "member line with the tag's own rotation")
    return "UNKNOWN", f"christiannp {b['STATUS']} / Urban {ub}"


# ============================================================================================ 07 walls
WALL_FIELDS = ["FLOOR", "CHRIS_PAIR_ID", "FACE_A", "FACE_B", "LAYERS", "SEPARATION_MM", "CHRIS_ACCEPTED",
               "CHRIS_REASON", "CHRIS_OVERLAP_MM", "M_TRUE_PHYSICAL_WALL", "M_OPENING_SPAN", "M_COLUMN_OVERLAP",
               "M_DUPLICATE_FACE", "M_FINISH_LINE", "M_PARAPET", "M_KERB", "M_FALSE_PAIR", "M_UNKNOWN",
               "URBAN_METHOD_B_WIDTH", "URBAN_METHOD_B_M", "URBAN_B_PAIRED_WALL_M", "URBAN_B_COLUMN_OVERLAP_M",
               "URBAN_B_OPENING_SPAN_M", "URBAN_B_DUPLICATE_M", "MATCH_METHOD", "DIFFERENCE_CLASS", "NOTES"]
CHRIS_TO_CLASS = {"PHYSICAL_WALL": "M_TRUE_PHYSICAL_WALL", "COLUMN_OVERLAP": "M_COLUMN_OVERLAP",
                  "OPENING_SPAN(window frame lines on W)": "M_OPENING_SPAN",
                  "UNKNOWN(shared face - ambiguous)": "M_UNKNOWN", "DUPLICATE_FACE(rejected)": "M_DUPLICATE_FACE",
                  "LAYER5_PARALLEL_PAIR(rejected; kerb/step/furniture candidate - not separable)": "M_KERB"}


def walls(ch):
    acc = ch.csv("10_walls/WALL_PAIRS_ACCEPTED.csv")
    rej = ch.csv("10_walls/WALL_PAIRS_REJECTED.csv")
    met = defaultdict(lambda: defaultdict(float))
    for m in ch.csv("10_walls/WALL_METRE_CLASSIFICATION.csv"):
        met[m["PAIR_ID"]][CHRIS_TO_CLASS.get(m["CLASS"], "M_UNKNOWN")] += float(m["LEN_MM"]) / 1000.0
    X = UJ("research/coverage_recovery_round/WALL_FACE_PAIR_EXTRACT.json")["floors"]
    ub = {}
    for fl, v in X.items():
        for w, ps in v["pairs"].items():
            ivs = [dict(x, p0=tuple(x["p0"]), p1=tuple(x["p1"])) for x in ps]
            cl = WB.classify(ivs, column_boxes=[tuple(c) for c in v["column_boxes"]],
                             opening_boxes=[tuple(c) for c in v["opening_boxes"]])
            for iv in cl:
                k = (fl, frozenset(format(int(h.split("|")[1][1:]), "X") for h in (iv["a"], iv["b"])))
                e = ub.setdefault(k, {"w": w, "len": 0.0, "parts": defaultdict(float)})
                e["len"] += iv["length"] / 1000.0
                for pk, pv in iv["parts"].items():
                    e["parts"][pk] += pv / 1000.0
    out, seen = [], set()

    def row(p, accepted):
        k = (p["FLOOR"], frozenset([p["FACE_A"].split("#")[0].upper(), p["FACE_B"].split("#")[0].upper()]))
        u = ub.get(k)
        if u:
            seen.add(k)
        m = met.get(p["PAIR_ID"], {})
        rr = p.get("REASON", "")
        if not accepted and not m:
            m = {"M_FALSE_PAIR": float(p["OVERLAP"]) / 1000.0}
        cls, note = _wall_class(accepted, rr, m, u, float(p["OVERLAP"]), float(p["SEPARATION"]))
        return {"FLOOR": p["FLOOR"], "CHRIS_PAIR_ID": p["PAIR_ID"], "FACE_A": p["FACE_A"], "FACE_B": p["FACE_B"],
                "LAYERS": f"{p['FACE_A_LAYER']}/{p['FACE_B_LAYER']}", "SEPARATION_MM": p["SEPARATION"],
                "CHRIS_ACCEPTED": accepted, "CHRIS_REASON": rr, "CHRIS_OVERLAP_MM": p["OVERLAP"],
                **{k2: r3(v2) for k2, v2 in m.items()},
                "URBAN_METHOD_B_WIDTH": u and u["w"], "URBAN_METHOD_B_M": u and r3(u["len"]),
                "URBAN_B_PAIRED_WALL_M": u and r3(u["parts"].get(WB.PAIRED_WALL, 0.0)),
                "URBAN_B_COLUMN_OVERLAP_M": u and r3(u["parts"].get(WB.COLUMN_OVERLAP, 0.0)),
                "URBAN_B_OPENING_SPAN_M": u and r3(u["parts"].get(WB.OPENING_SPAN, 0.0)),
                "URBAN_B_DUPLICATE_M": u and r3(u["parts"].get(WB.DUPLICATE_FACE, 0.0)),
                "MATCH_METHOD": "FACE_HANDLE_PAIR" if u else "NONE", "DIFFERENCE_CLASS": cls, "NOTES": note}
    for p in acc:
        out.append(row(p, True))
    for p in rej:                                  # rejected pairs christiannp classified per metre, or Urban kept
        k = (p["FLOOR"], frozenset([p["FACE_A"].split("#")[0].upper(), p["FACE_B"].split("#")[0].upper()]))
        if p["PAIR_ID"] in met or k in ub:
            out.append(row(p, False))
    for k, u in sorted(ub.items(), key=lambda z: (z[0][0], sorted(z[0][1]))):
        if k not in seen:
            out.append({"FLOOR": k[0], "FACE_A": sorted(k[1])[0], "FACE_B": sorted(k[1])[-1],
                        "URBAN_METHOD_B_WIDTH": u["w"], "URBAN_METHOD_B_M": r3(u["len"]),
                        "URBAN_B_PAIRED_WALL_M": r3(u["parts"].get(WB.PAIRED_WALL, 0.0)),
                        "URBAN_B_COLUMN_OVERLAP_M": r3(u["parts"].get(WB.COLUMN_OVERLAP, 0.0)),
                        "URBAN_B_OPENING_SPAN_M": r3(u["parts"].get(WB.OPENING_SPAN, 0.0)),
                        "URBAN_B_DUPLICATE_M": r3(u["parts"].get(WB.DUPLICATE_FACE, 0.0)),
                        "MATCH_METHOD": "NONE", "DIFFERENCE_CLASS": "UNKNOWN",
                        "NOTES": "Urban Method-B pair with no christiannp candidate row of the same faces"})
    return out


def _wall_class(accepted, reason, m, u, overlap, sep):
    if accepted and u:
        cw = m.get("M_TRUE_PHYSICAL_WALL", 0.0)
        uw = u["parts"].get(WB.PAIRED_WALL, 0.0)
        if abs(cw - uw) < 0.02:
            return "SAME_OBJECT_SAME_RESULT", "same faces, same per-metre split"
        if abs(u["len"] - sum(m.values())) < 0.02:
            return ("SAME_GEOMETRY_DIFFERENT_CONVENTION", "same faces and gross length; column / opening / ambiguity "
                    "split differs (christiannp: S-COL.BON overlap + W-layer frame lines + side-aware ambiguity; Urban "
                    "Method B: column boxes + door/window extents grown 25 mm)")
        return "SAME_OBJECT_DIFFERENT_SEGMENTATION", "same faces, different overlap interval"
    if accepted and not u:
        if m.get("M_OPENING_SPAN") and not m.get("M_TRUE_PHYSICAL_WALL"):
            return "SAME_GEOMETRY_DIFFERENT_CONVENTION", "W-layer window-frame pair: christiannp OPENING_SPAN; Urban Method B pairs layer 1 only"
        if not m.get("M_TRUE_PHYSICAL_WALL"):
            return ("SAME_GEOMETRY_DIFFERENT_CONVENTION", "christiannp pair with no physical-wall metres (column overlap / "
                    "ambiguous only); Urban Method B has no pair here")
        if overlap <= 200.0:
            return ("SAME_GEOMETRY_DIFFERENT_CONVENTION", f"overlap {overlap:.0f} mm: christiannp min overlap 100 mm, "
                    "Urban Method B min overlap 200 mm (short return / pier piece)")
        if min(abs(sep - 150.0), abs(sep - 200.0)) > 15.0:
            return ("URBAN_MISSED_PHYSICAL_OBJECT", f"separation {sep:.0f} mm is outside Urban's nominal widths "
                    "150 / 200 +-15 mm; christiannp accepts any 90-450 mm pair (width coverage gap)")
        return ("URBAN_MISSED_PHYSICAL_OBJECT", f"{sep:.0f} mm pair, overlap {overlap:.0f} mm, accepted by christiannp "
                "with no Urban Method-B pair: nearest-partner / fragmented-mate selection in pair_parallel_faces")
    if not accepted and u:
        return ("URBAN_FALSE_POSITIVE" if reason.startswith(("DUPLICATE", "INTERVENING")) else "UNKNOWN",
                f"christiannp rejects ({reason}); Urban Method B keeps the pair")
    return "NOT_COMPARABLE", f"christiannp rejection ({reason}) with no Urban pair: both exclude it"


# ============================================================================================ 08 footings
FOOT_FIELDS = ["CHRIS_ID", "URBAN_ID", "OUTLINE_HANDLES", "OUTLINE_SOURCE_CHRIS", "OUTLINE_GEOMETRY_URBAN",
               "TAG_HANDLES_CHRIS", "TAG_URBAN", "MARK_CHRIS", "TYPE_URBAN", "CENTER_X_LOCAL", "CENTER_Y_LOCAL",
               "DRAWN_LxW_CHRIS_MM", "DRAWN_LxW_URBAN_CM", "SCHEDULE_LxWxD_MM", "COLUMNS_INSIDE_CHRIS",
               "COLUMNS_URBAN", "CHRIS_STATUS", "CHRIS_CONFLICTS", "URBAN_TERMINAL", "URBAN_CANDIDATES",
               "CHRIS_M3_SCHEDULE", "CHRIS_M3_DRAWN_AREA", "MATCH_METHOD", "DIFFERENCE_CLASS", "NOTES"]


def footings(ch):
    occ = ch.csv("05_footings/FOOTING_OCCURRENCES.csv")
    U = UJ("research/alsenan_structural_census_s1/FOOTING_OCCURRENCE_REGISTER.json")
    norm = lambda h: "|".join(sorted(x.split(":")[0].upper() for x in re.split(r"[|+]", h)))  # noqa: E731
    by = {norm(r["outline"]["handle"]): r for r in U["rows"]}
    out, used = [], set()
    for o in occ:
        k = norm(o["OUTLINE_HANDLE(S)"])
        u = by.get(k)
        if u:
            used.add(u["footing_id"])
        cls, note = _foot_class(o, u, U)
        out.append({"CHRIS_ID": o["FOOTING_OCCURRENCE_ID"], "URBAN_ID": u and u["footing_id"], "OUTLINE_HANDLES": k,
                    "OUTLINE_SOURCE_CHRIS": o["OUTLINE_SOURCE"], "OUTLINE_GEOMETRY_URBAN": u and u["outline"]["geometry"],
                    "TAG_HANDLES_CHRIS": o["TAG_HANDLE"], "TAG_URBAN": u and u["tag"] and
                    "|".join([u["tag"]["handle"].split(":")[0]] + [c["handle"] for c in u.get("competing_tags") or []]),
                    "MARK_CHRIS": o["MARK"], "TYPE_URBAN": u and (u["type"] or "|".join(u.get("candidate_types") or [])),
                    "CENTER_X_LOCAL": o["CENTER_X_LOCAL"], "CENTER_Y_LOCAL": o["CENTER_Y_LOCAL"],
                    "DRAWN_LxW_CHRIS_MM": f"{o['DRAWN_LENGTH_MM']}x{o['DRAWN_WIDTH_MM']}",
                    "DRAWN_LxW_URBAN_CM": u and u.get("sizes") and f"{u['sizes']['drawn_L_cm']}x{u['sizes']['drawn_W_cm']}",
                    "SCHEDULE_LxWxD_MM": f"{o['SCHEDULE_LENGTH_MM']}x{o['SCHEDULE_WIDTH_MM']}x{o['DEPTH_MM']}",
                    "COLUMNS_INSIDE_CHRIS": o["COLUMN_TAGS_INSIDE"] or o["COLUMN(S)_INSIDE"],
                    "COLUMNS_URBAN": u and len(u["supported_columns"]), "CHRIS_STATUS": o["MATCH_STATUS"],
                    "CHRIS_CONFLICTS": o["CONFLICTS"], "URBAN_TERMINAL": u and u["terminal_state"],
                    "URBAN_CANDIDATES": u and "|".join(u.get("candidate_types") or []),
                    "CHRIS_M3_SCHEDULE": o["CONCRETE_M3_SCHEDULE_LxWxD"], "CHRIS_M3_DRAWN_AREA": o["CONCRETE_M3_DRAWN_AREA_x_SCHED_DEPTH"],
                    "MATCH_METHOD": "OUTLINE_HANDLE" if u else "NONE", "DIFFERENCE_CLASS": cls, "NOTES": note})
    for r in U["rows"]:
        if r["footing_id"] not in used:
            out.append({"URBAN_ID": r["footing_id"], "OUTLINE_HANDLES": norm(r["outline"]["handle"]),
                        "MATCH_METHOD": "NONE", "DIFFERENCE_CLASS": "CHRIS_MISSED_PHYSICAL_OBJECT",
                        "NOTES": "Urban outline with no christiannp occurrence"})
    rej = ch.csv("05_footings/FOOTING_REJECTED_MATCHES.csv")
    out.append({"CHRIS_ID": "REJECTED_CANDIDATES", "MATCH_METHOD": "LOG", "DIFFERENCE_CLASS": "NOT_COMPARABLE",
                "NOTES": f"{len(rej)} christiannp rejected tag-outline candidates logged; Urban keeps competing tags "
                         "on the occurrence (competing_tags) but does not log every rejected candidate"})
    return out


def _foot_class(o, u, U):
    if u is None:
        return "URBAN_MISSED_PHYSICAL_OBJECT", "christiannp outline with no Urban occurrence"
    if o["MATCH_STATUS"] == "UNRESOLVED" or u["terminal_state"] != "COUNTED_AND_DEFINED":
        return ("SOURCE_CONFLICT", "two tags (F 10A5, F10 168B) bound to one notched outline 1B1B drawn 3250x1400: "
                "both systems refuse nearest-wins. Hypothesis sets differ: Urban {2 x F = 0.432 m3 | F10 = 1.960 m3}, "
                "christiannp {F10 2.8x1.4x0.5 = 1.96 | drawn 3.25x1.4x0.5 = 2.275}")
    mm = [x for x in U["mismatches"] if x["kind"] == "FOOTING_OUTLINES_OVERLAP" and any(
        f.split(":")[1] in o["OUTLINE_HANDLE(S)"] for f in x["footings"])]
    if "IRREGULAR_OUTLINE" in o["CONFLICTS"] or mm:
        return ("SAME_OBJECT_SAME_RESULT", "same footing and size; christiannp flags IRREGULAR_OUTLINE (uses polygon area "
                f"{o['OUTLINE_AREA_M2']} m2), Urban flags FOOTING_OUTLINES_OVERLAP {mm[0]['overlap_m2'] if mm else ''} m2 "
                "with F9 180F - same physical irregularity seen two ways")
    if "columns inside" in o["CONFLICTS"]:
        return ("SAME_OBJECT_SAME_RESULT", f"combined footing: christiannp flags '{o['CONFLICTS']}' as a conflict, "
                f"Urban records {len(u['supported_columns'])} supported columns as normal")
    return "SAME_OBJECT_SAME_RESULT", "same outline, tag, mark and schedule size"


# ============================================================================================ 09 columns
COL_FIELDS = ["CHRIS_ID", "URBAN_CHAIN", "X_LOCAL", "Y_LOCAL", "TYPE_CHRIS", "TYPE_URBAN", "CHRIS_PLANS",
              "URBAN_SHEETS", "CHRIS_INTERVALS", "URBAN_FLOORS", "URBAN_PLANTED", "SECTIONS_CHRIS",
              "SECTION_URBAN_BY_FLOOR", "CHRIS_FLAGS", "MATCH_METHOD", "AGREEMENT_CLASS", "DIFFERENCE_CLASS", "NOTES"]
PLAN_TO_INTERVAL = {"FP": "NECK", "GFRS": "GF", "FFRS": "1F", "SFRS": "2F"}
FLOOR_U = {"FOUNDATION": "NECK", "GF": "GF", "1F": "1F", "2F": "2F"}


def columns(ch):
    mat = ch.csv("07_columns/COLUMN_OCCURRENCE_MATRIX.csv")
    chains = UJ("research/alsenan_structural_census_s1/COLUMN_VERTICAL_CHAIN_REGISTER.json")["rows"]
    occ = UJ("research/alsenan_structural_census_s1/COLUMN_OCCURRENCE_REGISTER.json")["rows"]
    h2c = {(sh, h): c for c in chains for sh, h in c["members_by_sheet"].items()}
    fl = defaultdict(list)
    for o in occ:
        fl[o["chain_id"]].append(o)
    out = []
    per_c, per_u = Counter(), Counter()
    for r in mat:
        sh = json.loads(r["SOURCE_HANDLES"])
        cs = {h2c[(p, h)]["chain_id"]: h2c[(p, h)] for p, hs in sh.items() for h in hs if (p, h) in h2c}
        c = next(iter(cs.values())) if len(cs) == 1 else None
        ci = sorted(PLAN_TO_INTERVAL[p] for p in sh if p in PLAN_TO_INTERVAL)
        for i in ci:
            per_c[i] += 1
        uo = sorted(fl[c["chain_id"]], key=lambda o: list(FLOOR_U).index(o["floor"])) if c else []
        uf = [FLOOR_U[o["floor"]] for o in uo]
        planted = [o["floor"] for o in uo if o.get("planted_on")]
        sec = {FLOOR_U[o["floor"]]: "x".join(str(int(v)) for v in (o.get("drawn_section_cm") or [])) for o in uo}
        if set(ci) == set(uf):
            cls, note = "SAME_OBJECT_SAME_RESULT", "same position, same storey intervals"
        elif planted and set(ci) - set(uf) and r["PLANTED?"] == "True":
            cls = "DONOR_FALSE_POSITIVE"
            note = (f"planted column (ANSI35 hatch, christiannp MD14; Urban planted_on {planted}): christiannp still counts "
                    f"the storey below ({sorted(set(ci) - set(uf))}) because its interval rule is 'outline drawn on the "
                    "storey's roof plan' - the column starts at that slab and has no interval below it")
        else:
            extra_c, extra_u = sorted(set(ci) - set(uf)), sorted(set(uf) - set(ci))
            cls = "SAME_GEOMETRY_DIFFERENT_CONVENTION"
            note = (f"interval convention: christiannp counts a storey when the outline is drawn on that storey's ROOF "
                    f"plan (GFRS = GF, FFRS = 1F, SFRS = 2F); Urban counts from the chain (starts / stops, planted_on). "
                    f"christiannp-only {extra_c}, Urban-only {extra_u}")
        out.append({"CHRIS_ID": r["COLUMN_ID"], "URBAN_CHAIN": c and c["chain_id"], "X_LOCAL": r["X"], "Y_LOCAL": r["Y"],
                    "TYPE_CHRIS": r["PLAN_TAG"], "TYPE_URBAN": c and c["column_type"], "CHRIS_PLANS": "|".join(sorted(sh)),
                    "URBAN_SHEETS": c and "|".join(sorted(c["members_by_sheet"])), "CHRIS_INTERVALS": "|".join(ci),
                    "URBAN_FLOORS": "|".join(uf), "URBAN_PLANTED": "|".join(planted),
                    "SECTIONS_CHRIS": r["OUTLINE_DIMS_BY_PLAN"], "SECTION_URBAN_BY_FLOOR": json.dumps(sec, sort_keys=True),
                    "CHRIS_FLAGS": "|".join(x for x in (r["PLANTED?"] == "True" and "PLANTED", r["STOPPED?"] == "True" and "STOPPED",
                                                         r["TURNED?"] == "True" and "TURNED", r["NOTES"]) if x),
                    "MATCH_METHOD": "PER_PLAN_OUTLINE_HANDLE" if c else "NONE",
                    "AGREEMENT_CLASS": "INDEPENDENT_EXTRACTION (same S-COL.BON outlines + CGT schedule, different code)",
                    "DIFFERENCE_CLASS": cls if c else "UNKNOWN", "NOTES": note})
    for o in occ:
        per_u[FLOOR_U[o["floor"]]] += 1
    shared = Counter(r["URBAN_CHAIN"] for r in out)
    for r in out:
        if shared[r["URBAN_CHAIN"]] > 1:
            r["NOTES"] += f"; christiannp splits Urban chain {r['URBAN_CHAIN']} into {shared[r['URBAN_CHAIN']]} positions (offset > 120 mm continuity tolerance)"
            if r["DIFFERENCE_CLASS"] != "DONOR_FALSE_POSITIVE":
                r["DIFFERENCE_CLASS"] = "SAME_OBJECT_DIFFERENT_SEGMENTATION"
    out.append({"CHRIS_ID": "POPULATION", "URBAN_CHAIN": f"{len(chains)} chains / {len(occ)} occurrences",
                "CHRIS_INTERVALS": json.dumps(dict(per_c), sort_keys=True), "URBAN_FLOORS": json.dumps(dict(per_u), sort_keys=True),
                "MATCH_METHOD": "POPULATION", "AGREEMENT_CLASS": "INDEPENDENT_EXTRACTION",
                "DIFFERENCE_CLASS": "SAME_GEOMETRY_DIFFERENT_CONVENTION",
                "NOTES": "normalise the storey convention first: christiannp = drawn on the storey's roof plan; Urban = "
                         "vertical chain with planted / stopped events. Heights: christiannp GF 4.50 / 1F 4.20 from FFL "
                         "(A01), neck and 2F UNRESOLVED; Urban neck LOWER_BOUND from founding level <= -1.50 m"})
    return out


# ============================================================================================ 10 slab openings
OPEN_FIELDS = ["OPENING_ID", "FLOOR_URBAN", "PLAN_CHRIS", "URBAN_FACE", "URBAN_ROLE", "URBAN_EVIDENCE",
               "URBAN_AREA_M2", "URBAN_BBOX_LOCAL", "URBAN_TAGS_CM_IN_FACE", "CHRIS_ID", "CHRIS_TYPE", "CHRIS_EVIDENCE",
               "CHRIS_AREA_M2", "CHRIS_BBOX_LOCAL", "CHRIS_CLASSIFICATION", "MATCH_METHOD", "MATCH_IOU",
               "DIFFERENCE_CLASS", "NOTES"]
PLAN_OF = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0.0


def slab_openings(ch):
    U = UJ("research/R9_1_CHRIS_POST_FREEZE/urban_extract/URBAN_SLAB_OPENING_GEOMETRY_EXTRACT.json")["floors"]
    reg = ch.csv("11_openings/SLAB_OPENING_REGISTER.csv")
    faces = {pl: {f["FACE_ID"]: f for f in ch.csv(f"09_slabs/{pl}/{pl}_VECTOR_FACES.csv")} for pl in ("GFRS", "FFRS", "SFRS")}
    co = []
    for r in reg:
        if r["PLAN"] == "GBP":
            continue
        m = re.search(r"bbox \['\[([^\]]+)\]'\]", r["GEOMETRY"])
        bb = [float(v) for v in m.group(1).split(",")] if m else None
        if r["TYPE"] == "STAIR_ZONE_UNMARKED":
            bb = [float(v) for v in json.loads(faces["GFRS"]["F046"]["BBOX"])]
        co.append(dict(r, _bb=bb))
    out, used = [], set()
    for fl, v in U.items():
        pl = PLAN_OF[fl]
        for o in v["openings"]:
            bb = o["bbox_local"]
            cand = [(c, _iou(bb, c["_bb"])) for c in co if c["PLAN"] == pl and c["_bb"]]
            best = max(cand, key=lambda t: t[1]) if cand else (None, 0.0)
            c, iou = best if best[1] > 0.3 else (None, 0.0)
            if c is None and o["role"] == "OPENING_STAIR":     # christiannp kept this stair zone as a slab face
                f = next((f for f in faces[pl].values() if _iou(bb, [float(x) for x in json.loads(f["BBOX"])]) > 0.8), None)
                c = {"OPENING_ID": f"(slab face {f['FACE_ID']})" if f else "(none)", "TYPE": "SLAB FACE",
                     "EVIDENCE": "no S-OPENING marker; stair treads not used", "AREA_M2": f and f["NET_AREA_M2"],
                     "CLASSIFICATION": "SLAB (counted)", "_bb": f and json.loads(f["BBOX"])} if f else None
                iou = _iou(bb, c["_bb"]) if c and c["_bb"] else 0.0
            if c and c.get("OPENING_ID") in [x["OPENING_ID"] for x in co]:
                used.add(c["OPENING_ID"])
            cls, note = _open_class(fl, o, c)
            out.append({"OPENING_ID": f"{fl}:{o['face']}", "FLOOR_URBAN": fl, "PLAN_CHRIS": pl, "URBAN_FACE": o["face"],
                        "URBAN_ROLE": o["role"], "URBAN_EVIDENCE": o["why"], "URBAN_AREA_M2": o["area_m2"],
                        "URBAN_BBOX_LOCAL": json.dumps(bb), "URBAN_TAGS_CM_IN_FACE": "|".join(map(str, o["tags_cm"])),
                        "CHRIS_ID": c and c["OPENING_ID"], "CHRIS_TYPE": c and c["TYPE"], "CHRIS_EVIDENCE": c and c["EVIDENCE"],
                        "CHRIS_AREA_M2": c and c["AREA_M2"], "CHRIS_BBOX_LOCAL": c and json.dumps(c["_bb"]),
                        "CHRIS_CLASSIFICATION": c and c["CLASSIFICATION"], "MATCH_METHOD": "BBOX_IOU (frame-local)",
                        "MATCH_IOU": round(iou, 3), "DIFFERENCE_CLASS": cls, "NOTES": note})
    for c in co:
        if c["OPENING_ID"] not in used:
            out.append({"OPENING_ID": c["OPENING_ID"], "PLAN_CHRIS": c["PLAN"], "CHRIS_ID": c["OPENING_ID"],
                        "CHRIS_TYPE": c["TYPE"], "CHRIS_EVIDENCE": c["EVIDENCE"], "CHRIS_AREA_M2": c["AREA_M2"],
                        "CHRIS_CLASSIFICATION": c["CLASSIFICATION"], "MATCH_METHOD": "NONE",
                        "DIFFERENCE_CLASS": "SAME_OBJECT_DIFFERENT_SEGMENTATION" if "SAME VECTOR FACE" in c["CLASSIFICATION"] else "UNKNOWN",
                        "NOTES": "second X marker inside the same christiannp face as 2D1/2D2 (U21): one void counted once by "
                                 "both systems" if "SAME VECTOR FACE" in c["CLASSIFICATION"] else ""})
    # thickness authority per sheet (separate from area)
    for fl, v in U.items():
        out.append({"OPENING_ID": f"{fl}:THICKNESS", "FLOOR_URBAN": fl, "PLAN_CHRIS": PLAN_OF[fl],
                    "URBAN_EVIDENCE": "stacked TEXT 'T' over 'nn' on S-TEXT-SLAB: " + "; ".join(
                        f"{t['t_cm']} cm @ {t['xy_local']}" for t in v["thickness_tags"]),
                    "URBAN_TAGS_CM_IN_FACE": "|".join(map(str, v["sheet_thickness_tags_cm"])),
                    "CHRIS_EVIDENCE": "A04 / U05: 'no suspended slab thickness in source' (searched 'T=' and 'cm')",
                    "MATCH_METHOD": "SOURCE_ROUTE", "DIFFERENCE_CLASS": "SOURCE_AUTHORITY_DIFFERENCE",
                    "NOTES": "the stacked T / 16 (T / 18 on 2F) TEXT pairs are in christiannp's own entity dump "
                             "(ST7757_entities.jsonl, e.g. 768/769, 7B3/7B4); its search pattern 'T=' misses the "
                             "two-entity grammar, so all suspended-slab volumes stay UNRESOLVED there"})
    return out


def _open_class(fl, o, c):
    if c is None:
        return "CHRIS_MISSED_PHYSICAL_OBJECT", "no christiannp opening or face at this location"
    if o["role"] == "OPENING_STAIR":
        return ("ASSUMPTION_DIFFERENCE", f"stair well: Urban deducts on stair line work (>= MIN_TREAD_LINES tread lines "
                f"inside the face{', with a T' + str(o['tags_cm'][0]) + ' tag inside it - not flagged' if o['tags_cm'] else ''}); "
                f"christiannp keeps it as slab ({c['OPENING_ID']}{', U07' if fl == 'GF' else ', not registered at all'})")
    if "FAN" in c["TYPE"]:
        return ("ASSUMPTION_DIFFERENCE", f"radial fan (dome): Urban deducts as OPENING_VOID because the fan lines exceed "
                f"1.5 x the face diagonal (opening-layer cross rule); christiannp keeps it AMBIGUOUS_VOID (dome?), not "
                f"deducted. Areas {o['area_m2']} vs {c['AREA_M2']} m2 differ by the face construction (arc chords)")
    if o["role"] == "OPENING_VOID" and o["tags_cm"]:
        return ("SAME_OBJECT_DIFFERENT_SEGMENTATION", f"Urban face {o['area_m2']} m2 = christiannp void F013 "
                f"{c['AREA_M2']} m2 + christiannp slab face F031 6.979 m2: christiannp uses S-OPENING lines as barriers, "
                "so the void is separated from the labelled slab; Urban uses S-OPENING only as a role marker, merges "
                "both, sees the T16 tag in the same face and publishes OPENING_CONFLICT (the conflict is a segmentation "
                "artefact, not a source conflict)")
    if abs(float(o["area_m2"]) - float(c["AREA_M2"])) < 0.05:
        return "SAME_OBJECT_SAME_RESULT", f"same void ({o['why']} / {c['EVIDENCE']})"
    return "SAME_OBJECT_DIFFERENT_SEGMENTATION", "same void, different face boundary"


# ============================================================================================ 11 rebar token corpus
REBAR_FIELDS = ["PATTERN_ID", "RAW_TOKEN", "N_OCCURRENCES", "ELEMENTS", "SOURCE_TYPES", "EXAMPLE_HANDLES",
                "EXPECTED_NORMALISED", "EXPECTED_CLASS", "SG_PARSE_BAR", "SG_BAR_FROM_CELLS", "SS_BAR_SPEC",
                "SRB_PARSE", "URBAN_ACCEPTING_PARSERS", "URBAN_REJECTING_PARSERS", "URBAN_DISAGREEMENT",
                "CHRIS_INTERPRETATION", "CHRIS_TARGET_COMPONENTS", "CHRIS_TERMINAL_STATES", "NOTES"]


def _expected(tok):
    """Research oracle for the meaning of one token (independent of the three Urban parsers)."""
    t = tok.replace("%%c", "Ø").replace("%%C", "Ø").strip()
    if not t:
        return "", "EMPTY"
    if re.fullmatch(r"\d+\+\d+", t):
        return t, "BOXED_PAIR (semantics not printed)"
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)(/m)?", t)
    if m:
        return f"{m[1]} x Ø{m[2]}" + (" per m" if m[3] else ""), "COUNT_DIA_SPLIT_CELLS" + ("_PER_M" if m[3] else "")
    m = re.search(r"(\d+)\s*Ø\s*(\d+)\s*/\s*m", t)
    if m:
        return f"{m[1]} x Ø{m[2]} per m" + (" each way" if "E.W" in t.upper() else ""), "COUNT_DIA_PER_M"
    m = re.fullmatch(r"(\d+)\s*Ø\s*(\d+)\s*/\s*(Top|Bot\w*)", t, re.I)
    if m:
        return f"{m[1]} x Ø{m[2]} {m[3].upper()}", "COUNT_DIA_POSITION"
    m = re.fullmatch(r"(\d+)?\s*Ø\s*(\d+)\s*(MM)?\s*/\s*(\d+)\s*cm", t, re.I)
    if m:
        return (f"{m[1]} x " if m[1] else "") + f"Ø{m[2]} @ {m[4]} cm", "DIA_AT_SPACING" if not m[1] else "COUNT_DIA_AT_SPACING"
    m = re.fullmatch(r"(\d+)\s*Ø\s*(\d+)", t)
    if m:
        return f"{m[1]} x Ø{m[2]}", "COUNT_DIA"
    return t, "NOT_A_BAR_TOKEN"


def _p_sg(t):
    r = SG.parse_bar(t)
    return "REJECT" if r["grammar"] == "UNPARSED" else f"{r['grammar']}:{r['count']}xØ{r['dia_mm']}" + (
        "/m" if r["per_m"] else "") + (f"@{r['spacing_cm']}" if r["spacing_cm"] else "") + (f" {r['position']}" if r["position"] else "") + (" EW" if r["each_way"] else "")


def _p_cells(t):
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+\s*(/\s*m)?)\s*", t)
    if not m:
        return "N/A"
    r = SG.bar_from_cells(m[1], m[2])
    return "REJECT" if r.get("grammar") in ("UNPARSED", "EMPTY") or r.get("count") is None else f"{r['grammar']}:{r['count']}xØ{r['dia_mm']}" + ("/m" if r["per_m"] else "")


def _p_ss(t):
    r = SS.bar_spec(t)
    return "REJECT" if not r else ";".join(f"{x['count']}xØ{x['dia_mm']}" + ("/m" if x["per_m"] else "") for x in r)


def _p_srb(t):
    r = SRB.parse(t)
    return "REJECT" if r is None else f"{r['kind']}:{r['n']}xØ{r['dia_mm']}" + ("/m" if r["kind"] == "PER_M" else "") + (
        " TOP" if r["top"] else "") + (" EW" if r["both_ways"] else "")


def _norm(v):
    m = re.search(r"(\d+)xØ(\d+)(/m)?", v or "")
    return (int(m[1]), int(m[2]), bool(m[3])) if m else None


def rebar_corpus(ch):
    ev = ch.csv("13_rebar/REBAR_EVIDENCE.csv")
    groups = defaultdict(list)
    for r in ev:
        groups[r["RAW_TEXT"]].append(r)
    out = []
    for i, (tok, rs) in enumerate(sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])), 1):
        exp, ecls = _expected(tok)
        cells = ecls.startswith("COUNT_DIA_SPLIT_CELLS")
        res = {"SG_PARSE_BAR": "N/A (cell pair)" if cells else _p_sg(tok),
               "SG_BAR_FROM_CELLS": _p_cells(tok) if cells else "N/A",
               "SS_BAR_SPEC": "N/A (cell pair)" if cells else _p_ss(tok),
               "SRB_PARSE": "N/A (cell pair)" if cells else _p_srb(tok)}
        acc = [k for k, v in res.items() if not v.startswith(("REJECT", "N/A"))]
        rej = [k for k, v in res.items() if v == "REJECT"]
        vals = {_norm(res[k]) for k in acc}
        exp_n = _norm(exp.replace(" x ", "x").replace(" per m", "/m"))
        if ecls in ("EMPTY", "NOT_A_BAR_TOKEN", "BOXED_PAIR (semantics not printed)"):
            dis = "NONE (not a bar token)" if not acc else f"ACCEPTED_NON_BAR by {acc}"
        elif not acc:
            dis = "ALL_REJECT a readable bar token"
        elif rej:
            dis = f"SPLIT: accept {acc} / reject {rej}"
        else:
            dis = "NONE"
        if len(vals) > 1:
            dis += f"; VALUES_DIFFER {sorted(map(str, vals))}"
        if exp_n and vals and exp_n not in vals:
            dis += "; NO_PARSER_GIVES_EXPECTED"
        if "@" in exp and any(k == "SS_BAR_SPEC" for k in acc):
            dis += "; SS_BAR_SPEC_DROPS_SPACING"
        hs = []
        for r in rs:
            hs += [h for h in r["SOURCE_HANDLE"].split(",") if h]
        out.append({"PATTERN_ID": f"TOK{i:03d}", "RAW_TOKEN": tok, "N_OCCURRENCES": len(rs),
                    "ELEMENTS": "|".join(sorted({r["ELEMENT"] for r in rs})),
                    "SOURCE_TYPES": "|".join(sorted({r["SOURCE_TYPE"] or "(none)" for r in rs})),
                    "EXAMPLE_HANDLES": "|".join(sorted(set(hs))[:6]), "EXPECTED_NORMALISED": exp, "EXPECTED_CLASS": ecls,
                    **res, "URBAN_ACCEPTING_PARSERS": "|".join(acc), "URBAN_REJECTING_PARSERS": "|".join(rej),
                    "URBAN_DISAGREEMENT": dis,
                    "CHRIS_INTERPRETATION": "|".join(sorted({r["PARSED_VALUE"] for r in rs}))[:160],
                    "CHRIS_TARGET_COMPONENTS": "|".join(sorted({r["COMPONENT"] for r in rs})),
                    "CHRIS_TERMINAL_STATES": "|".join(sorted({r["INCLUDED_EXCLUDED"] for r in rs})),
                    "NOTES": ""})
    return out


# ============================================================================================ 12 manual decisions
MD_FIELDS = ["DECISION_ID", "OBJECTS", "CHRIS_DECISION", "CHRIS_COULD_BE_DETERMINISTIC", "DOES_URBAN_ALREADY_HANDLE_DETERMINISTICALLY",
             "URBAN_EVIDENCE", "IF_NOT_EVIDENCE_NEEDED", "IF_NOT_ALGORITHM", "FALSE_POSITIVE_RISK", "GAP_CLASS", "NOTES"]
MD_GAP = {
    "MD01": ("PARTIAL", "alsenan_v3_structure.ground / extract_geometry use a configured layer '1' + 300 mm (project config, "
             "not derived)", "accepted-pair width histogram per layer vs schedule width set", "rank layers by the share of "
             "pairs whose width falls in the schedule width set; accept the layer only above a threshold, log the rest",
             "stair treads on layer 2 at 300 mm (christiannp: 134 LAYER_NOT_ALLOWED rejects)", "AUTOMATABLE_NOW"),
    "MD02": ("PARTIAL", "S1 FOOTING_DEFINITION_REGISTER maps FT W/H/DEPHT to L/W/D (W=90 -> L 90 cm) by a fixed block "
             "mapping in rules_s1, not by header geometry", "ATTDEF x-position and the header TEXT above it",
             "bind each ATTDEF to the nearest header TEXT above its x (christiannp schedules.py); keep the tag name as a "
             "second opinion and raise a conflict when they disagree", "a header over two columns", "AUTOMATABLE_NOW"),
    "MD03": ("YES", "S1 COLUMN census: CN section from loose texts ('FOU (loose texts, not a CGT block row)')",
             "", "", "", "AUTOMATABLE_NOW"),
    "MD04": ("YES", "S1 FOOTING_OCCURRENCE_REGISTER outline geometry BLOCK_F_INSERT (12 occurrences)", "", "", "", "AUTOMATABLE_NOW"),
    "MD05": ("YES", "S1 footing outlines 1B07 / 1B19 / 1B1B read as POLYLINE occurrences", "", "", "", "AUTOMATABLE_NOW"),
    "MD06": ("PARTIAL", "ground-slab barrier set (layers 1+2, columns, single lines) has no S-BW layer: the lift pit sits inside "
             "Urban cell FP1-C99368_44772 (05 CELL rows)", "layer role of S-BW (pit / pool walls) from the layer table plus "
             "closed-box geometry under a footing", "add closed S-BW boxes to the slab barrier set and to the opening "
             "markers (inner box = void)", "boundary walls on S-BW outside the network", "AUTOMATABLE_NOW"),
    "MD07": ("NO", "Urban GB spans are split at columns only; no junction topology is built (not needed for length)",
             "face-line intersections at oblique / curved arrivals", "intersect the arriving strip's two face lines with "
             "the target's faces instead of centreline distance + tolerance", "near-miss crossings", "NEEDS_NEW_GEOMETRY_ROUTE"),
    "MD08": ("PARTIAL", "STRAP_BEAM_REGISTER binds straps by their S.B tags and clears them at footing outlines; no explicit "
             "footing-to-footing-gap rejection rule", "both faces being footing edges", "reject a pair whose two faces belong "
             "to two different footing outlines", "a real strap drawn on footing edges", "AUTOMATABLE_NOW"),
    "MD09": ("YES", "GB bands use the fixed 300 +- 12 mm width (stricter than a 150-800 cap)", "", "", "", "AUTOMATABLE_NOW"),
    "MD10": ("YES", "slab_region.regions keeps only arrangement components containing a bound beam band point "
             "(band_points); detail clusters are dropped without the 'touches no column' heuristic that removed a real "
             "plan segment in christiannp (U21)", "", "", "", "AUTOMATABLE_NOW"),
    "MD11": ("YES", "slab_region: opening-layer cross length >= 1.5 x face diagonal -> OPENING_VOID", "", "", "", "AUTOMATABLE_NOW"),
    "MD12": ("NO", "Urban deducts both 1F radial fans as OPENING_VOID (fan lines satisfy the cross rule); the dome shells "
             "are measured separately (C-DOME-SHELL-*)", "DETAIL OF DOME relation to the fan regions", "classify radial "
             "fans (>= 6 lines from one centre) as AMBIGUOUS_VOID; deduct only when a dome / void source binds",
             "a real circular void", "NEEDS_SOURCE_AUTHORITY"),
    "MD13": ("NO", "Urban deducts the stair face on tread line work (OPENING_STAIR), even with a T16 tag inside the face",
             "stair-well opening marker or section", "stair face = STAIR_ZONE_CANDIDATE; deduct only with a void marker, "
             "else keep a scenario pair (slab / void)", "landing slabs", "NEEDS_SOURCE_AUTHORITY"),
    "MD14": ("PARTIAL", "S1 chains carry planted_on from vertical continuity (outline above, none below); no hatch-pattern "
             "evidence", "hatch pattern per outline (SOLID vs ANSI35) and a legend", "record the hatch pattern on each "
             "outline as corroborating evidence for planted / stopped; never as the only evidence", "hatch used for another "
             "meaning", "PROJECT_SPECIFIC"),
    "MD15": ("YES", "WALL_LAYER '1', DOOR_LAYERS ('D', 'W') in the wall extracts (configured)", "", "", "", "PROJECT_SPECIFIC"),
    "MD16": ("YES", "door-transition / portal closures in the room topology (R8.x door_transition, topology_closures)",
             "", "", "", "AUTOMATABLE_NOW"),
    "MD17": ("YES", "STRAP_BEAM_REGISTER SB2 state MEASURED_WITH_WIDTH_DEVIATION (drawn 987.1 -> B 100)", "", "", "", "AUTOMATABLE_NOW"),
    "MD18": ("YES", "Urban does not use MCP screenshots as evidence; its renders come from the decoded geometry", "", "",
             "", "INHERENT_REVIEW"),
}


def manual_decisions(ch):
    out = []
    for r in ch.csv("14_assumptions/MANUAL_DECISIONS.csv"):
        g = MD_GAP[r["DECISION_ID"]]
        out.append({"DECISION_ID": r["DECISION_ID"], "OBJECTS": r["OBJECTS"], "CHRIS_DECISION": r["DECISION"],
                    "CHRIS_COULD_BE_DETERMINISTIC": r["COULD_BE_DETERMINISTIC"],
                    "DOES_URBAN_ALREADY_HANDLE_DETERMINISTICALLY": g[0], "URBAN_EVIDENCE": g[1],
                    "IF_NOT_EVIDENCE_NEEDED": g[2], "IF_NOT_ALGORITHM": g[3] or r["SUGGESTED_GENERIC_ALGORITHM"] if g[0] != "YES" else "",
                    "FALSE_POSITIVE_RISK": g[4], "GAP_CLASS": g[5], "NOTES": f"christiannp confidence {r['CONFIDENCE']}"})
    return out


# ============================================================================================ 14 technique matrix
TM_FIELDS = ["TECHNIQUE", "URBAN_CURRENT", "CHRIS_FORENSIC", "WHICH_IS_STRONGER", "WHY", "EVIDENCE", "KNOWN_DEFECT", "DECISION"]
TECHNIQUES = [
    ("Face pairing population (GB)", "_pair_bands: layer 1, 300 +-12 mm, ONE best partner per face, forward scan, 80 % area de-dup",
     "pairing.py: all parallel pairs <= 1 deg / <= 1000 mm logged, accept 150-800 mm + overlap >= 150 + no intervening face",
     "CHRIS", "same 43 pairs, plus the fragmented-mate pair Urban cannot form", "03 S008 (1.000 m)", "Urban: fragmented mates dropped",
     "ADOPT_CONCEPT"),
    ("Full candidate log with reject reasons", "accepted bands only", "every candidate with measurements + reason", "CHRIS",
     "regression evidence for every rejection (stair treads, duplicates)", "GROUND_BEAM_PAIR_CANDIDATES 179 rows", "", "ADOPT_CONCEPT"),
    ("Intervening-face test", "absent in GB / Method B (nearest partner implicit)", "reject a pair with another allowed face between "
     "over >= 50 % of the overlap", "CHRIS", "stops double-skin / duplicate faces pairing across a third line",
     "WALL_PAIRS_REJECTED INTERVENING_FACE 31", "", "ADAPT"),
    ("Curved band length", "_arc_bands: one arc's sweep x mean radius", "angular overlap of both arcs x mean radius", "CHRIS",
     "length where both faces exist", "03 S044 (7.005 vs 6.287 m gross)", "Urban: +0.718 m on the curved GB", "ADOPT_CONCEPT"),
    ("Column split of beam length", "polygon difference + piece extent (partial-width columns not deducted)",
     "centreline clip by every column box (end boxes included)", "NEITHER (convention)", "both deterministic; QS rule decides",
     "03: 9.051 vs 16.256 m inside columns", "Urban under-deducts partial-width columns; christiannp over-deducts end boxes",
     "CHALLENGER_ONLY"),
    ("Network topology (nodes / T / L / free ends)", "spans between columns only", "strip ends snapped to column / T / arc / pit / "
     "corner / free end; edges", "CHRIS", "connectivity and free-end QA", "GROUND_BEAM_NODES 80, 4 free ends",
     "tolerance-based snapping (w/2+60, w+60 for curves)", "CHALLENGER_ONLY"),
    ("GB depth", "p.13 typical sections (visual lane) + bounded exterior", "not assumed; 0.4/0.6/0.8 scenarios", "URBAN",
     "a drawn section table exists; christiannp searched DXF text only", "03 depth row", "", "KEEP_URBAN"),
    ("Strap beam length", "clear between footing outlines", "full face overlap (inside footings)", "URBAN",
     "footing concrete already holds the overlap", "03 STRAP rows: 3.392 vs 6.036 m3", "christiannp double count", "KEEP_URBAN"),
    ("Schedule row choice by drawn width (R4)", "width deviation recorded on the occurrence", "row chosen by drawn width; gate on "
     "beam binding", "BOTH", "both resolve SB2 W80 / W100", "03 SB_S2; 06", "", "KEEP_URBAN"),
    ("Beam tag binding", "merged member line + tag rotation; breadth mismatch = FLAG", "parallel <= 10 deg + extent + 1 m + width "
     "<= 30 mm = GATE", "SPLIT", "christiannp resolves 6 Urban AMBIGUOUS tags; Urban binds 8 oblique / wide tags christiannp misses",
     "06: 98 same, 6 URBAN_BINDING_FAILURE, 8 CHRIS_BINDING_FAILURE, 7 SOURCE_CONFLICT", "christiannp: horizontal-text parallel "
     "test fails on oblique members", "ADAPT"),
    ("R1 CB occurrence once per band", "CB occurrence register (span count / length conflicts)", "CONDITIONAL 25", "URBAN",
     "Urban already raises SPAN_LENGTH_CONFLICT / SPAN_COUNT_CONFLICT", "BEAM_RULE_TESTS_R1_R5", "", "KEEP_URBAN"),
    ("R2 collinear inheritance", "not applied (NO_TAG kept)", "4 SAFE / 2 UNSAFE", "NEITHER", "unsafe in 2 of 6", "BEAM_RULE_TESTS",
     "", "CHALLENGER_ONLY"),
    ("R3 same-mark de-dup on one band", "duplicates_removed in coverage residue", "34 SAFE (same band only)", "BOTH", "",
     "BEAM_RULE_TESTS", "", "KEEP_URBAN"),
    ("R5 equal sharing", "never", "never applied (3 UNSAFE)", "BOTH", "", "BEAM_RULE_TESTS", "", "REJECT"),
    ("Ground-slab area (vector)", "ground_slab_recovery cells (bands 1+2, columns, single lines)", "planar faces with hole "
     "subtraction + sampled apportioning", "BOTH", "217.012 vs 217.683 m2 (0.3 %); 28 / 31 cells identical", "05 CELL rows",
     "Urban: lift pit S-BW not a barrier (inside one cell); christiannp: point classification mislabels mixed faces", "KEEP_URBAN"),
    ("Raster flood fill", "absent", "4/8-connected flood, strip mask, 4 resolutions x 2 origins", "CHRIS (as oracle)",
     "converges to vector within 0.11 % (half-edge, 10 mm); origin shift <= 0.04 m2", "05 RASTER rows", "under-reads by the edge "
     "band; slow; resolution-dependent", "ORACLE_ONLY"),
    ("Area vs thickness authority", "separate (thickness ladder per cell)", "separate", "BOTH", "", "05", "", "KEEP_URBAN"),
    ("Suspended-slab thickness", "stacked 'T' / 'nn' TEXT pair (S-TEXT-SLAB)", "searched 'T=' / 'cm' only -> UNRESOLVED", "URBAN",
     "the tags are in christiannp's own dump", "10 THICKNESS rows", "christiannp miss", "KEEP_URBAN"),
    ("S-OPENING lines as face barriers", "S-OPENING = role marker only", "S-OPENING segments are barriers", "CHRIS",
     "separates the GF void (20.15 m2) from the labelled slab cell (6.98 m2) that Urban merges into one conflict face",
     "10 GF:SITE-4e71d36d91b40e50", "Urban OPENING_CONFLICT is a segmentation artefact", "ADOPT_CONCEPT"),
    ("Detail-cluster exclusion", "components holding a bound beam band", "clusters touching no column", "URBAN",
     "christiannp's rule removed a real plan segment (U21)", "UNRESOLVED_REGISTER U21", "", "KEEP_URBAN"),
    ("Radial fan / stair deduction", "deduct (cross rule / tread lines)", "AMBIGUOUS / kept as slab", "NEITHER",
     "both are assumptions; source authority needed", "10 ASSUMPTION_DIFFERENCE rows", "", "CHALLENGER_ONLY"),
    ("Footing outline routes", "BLOCK_F_INSERT / POLYLINE / FOUR_LINES (+ open notched)", "A1-A4 same four routes",
     "BOTH", "26 / 26 outlines identical by handle", "08", "", "KEEP_URBAN"),
    ("Footing tag binding", "tag + competing_tags kept on the occurrence", "inside + dims match, then nearest dims, then nearest; "
     "61 candidates logged", "BOTH", "identical 25 + the same F/F10 conflict", "08", "", "KEEP_URBAN"),
    ("Column continuity", "chains across 6 sheets, planted / stopped events", "coordinate continuity 120 mm, no propagation", "URBAN",
     "christiannp splits 2 turned columns and counts planted columns in the storey below", "09: 3 DONOR_FALSE_POSITIVE, 2 split chains",
     "christiannp interval rule", "KEEP_URBAN"),
    ("Column hatch semantics", "not read", "ANSI35 = planted", "CHRIS (as corroboration)", "independent evidence for planted_on",
     "MD14", "legend not printed", "CHALLENGER_ONLY"),
    ("Wall face pairing", "Method B: layer 1, 150 / 200 +-15 mm, overlap > 200", "layers 1+W, 90-450 mm, overlap >= 100, "
     "intervening + side-aware ambiguity", "CHRIS (population)", "finds the 385 / 400 mm walls and the fragmented mate Urban "
     "misses", "07: 2 URBAN_MISSED pairs (GF_WP0638 400 mm, GF_WP0965 fragmented mate; 2.485 m physical)", "", "ADAPT"),
    ("Wall per-metre classification", "WB.classify: column / opening box / duplicate", "column / W-frame opening / ambiguity / "
     "duplicate / layer-5 kerb", "SPLIT", "christiannp opening metres only from W frames (9.94 m) vs Urban door+window boxes "
     "(53.96 m): different OPENING definition", "07 per-metre totals", "", "ADAPT"),
    ("Side-aware shared-face ambiguity", "WALL_BAND_AMBIGUOUS bands", "a face with partners on opposite sides = UNKNOWN", "BOTH",
     "27.5 m christiannp UNKNOWN vs 45.23 m Urban WALL_BAND_AMBIGUOUS", "07", "", "KEEP_URBAN"),
    ("Rebar token parsing", "three parsers (schedule_grammar / structural_schedule / slab_rebar_binding)", "one evidence table, "
     "507 rows with handle + component + terminal state", "SPLIT", "the three Urban parsers agree on 74 of 80 bar patterns; 6 "
     "note patterns (53 rows) split", "11", "Urban: parser disagreement on notes; christiannp: lengths = member dimension (A05)",
     "ADOPT_CONCEPT"),
    ("Rebar evidence table with terminal state", "S1 / S3 evidence registers per element", "one REBAR_EVIDENCE with INCLUDED / "
     "EXCLUDED + why", "CHRIS", "census and conservation in one place", "13_rebar/REBAR_EVIDENCE.csv", "", "ADOPT_CONCEPT"),
    ("Disk-vs-memory reconciliation + DBMOD", "K2 decode of the hashed DXF (no live CAD)", "entget dump vs disk, handle for handle",
     "BOTH", "Urban never reads live CAD state", "02_raw_entities", "", "KEEP_URBAN"),
    ("Frame-local coordinates", "S1 registers already frame-local", "frame-local", "BOTH", "made this crosswalk possible", "03-10",
     "", "KEEP_URBAN"),
]


def technique_matrix():
    return [dict(zip(TM_FIELDS, t)) for t in TECHNIQUES]


# ============================================================================================ 15 reconciliation
REC_FIELDS = ["ITEM", "UNIT", "URBAN_OFFICIAL", "URBAN_LOWER_BOUND", "URBAN_BEST", "URBAN_LOW", "URBAN_HIGH", "CHRIS_FROZEN",
              "CHRIS_BASIS", "UC4N", "FREELANCER_QS_REFERENCE", "NORMALISED_URBAN", "NORMALISED_CHRIS", "NORMALISED_BASIS",
              "SAME_BASIS", "POPULATION_DIFF", "GEOMETRY_DIFF", "RULE_DIFF", "ASSUMPTION_DIFF", "ROOT_CAUSE_CLASS",
              "TECHNIQUE_TO_TEST", "SOURCE_VERSION"]


def _donor_dicts():
    """U-C4N and freelancer reference values, read from the frozen coverage-round comparison by AST (never imported)."""
    tree = ast.parse((ROOT / "research/coverage_recovery_round/post_freeze_comparison.py").read_text(encoding="utf-8"))
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("UC4N", "FREELANCER"):
            out[n.targets[0].id] = ast.literal_eval(n.value)
    return out


def _L(q):
    return {"URBAN_OFFICIAL": q["VERIFIED_QUANTITY"], "URBAN_LOWER_BOUND": q["LOWER_BOUND_QUANTITY"],
            "URBAN_BEST": q["BEST_PROVISIONAL_QUANTITY"], "URBAN_LOW": q["LOW_SCENARIO"], "URBAN_HIGH": q["HIGH_SCENARIO"]}


def reconciliation(ch, gb_seg, walls_rows):
    D = _donor_dicts()
    U, F = D["UC4N"], D["FREELANCER"]
    Q = UJ("research/coverage_recovery_round/QUANTITY_SCENARIOS.json")
    cq = {(r["TRADE"], r["ITEM"]): r["VALUE"] for r in ch.csv("16_final/QUANTITY_SUMMARY.csv")}
    num = lambda v: float(v) if re.fullmatch(r"-?\d+(\.\d+)?", str(v)) else None  # noqa: E731
    sv = (f"URBAN {URBAN_HEAD} (coverage round 680264d registers) | CHRIS {MANIFEST_SHA256[:12]} | UC4N / FREELANCER "
          "from post_freeze_comparison.py | drawings ST 9f9d1179 / P ab54dd55")
    rows = []

    def add(item, unit, urban, chris, basis, **kw):
        r = {"ITEM": item, "UNIT": unit, **urban, "CHRIS_FROZEN": chris, "CHRIS_BASIS": basis, "SOURCE_VERSION": sv}
        r.update(kw)
        rows.append(r)

    gb = Q["ground_beams"]
    s = gb_seg
    add("Ground-beam network length", "m", {"URBAN_OFFICIAL": s["URBAN"]["span_length_m"], "URBAN_BEST": s["URBAN"]["span_length_m"]},
        r3(s["CHRIS"]["MEASURED_NETWORK_LENGTH_STRIP_CENTERLINES_MM"] / 1000), "strip centrelines (face overlaps), gross of columns",
        NORMALISED_URBAN=s["URBAN"]["gross_band_length_m"], NORMALISED_CHRIS=r3(s["CHRIS"]["MEASURED_NETWORK_LENGTH_STRIP_CENTERLINES_MM"] / 1000),
        NORMALISED_BASIS="gross band / strip length (same 89 layer-1 faces)", SAME_BASIS="YES after normalisation",
        POPULATION_DIFF="-1.000 m: strip S008 (114 + 115) not formed by Urban", GEOMETRY_DIFF="+0.718 m: Urban arc 157/158 sweep",
        RULE_DIFF="net basis: Urban removes 9.051 m in columns (piece extent), christiannp 16.256 m (centreline clip)",
        ASSUMPTION_DIFF="none", ROOT_CAUSE_CLASS="URBAN_MISSED_PHYSICAL_OBJECT + SAME_GEOMETRY_DIFFERENT_CONVENTION",
        TECHNIQUE_TO_TEST="multi-partner pairing; arc angular overlap; declared column-split convention")
    add("Ground-beam concrete", "m3", _L(gb["volume"]), "24.976 / 37.463 / 49.951 (0.4 / 0.6 / 0.8 m scenarios)",
        "depth not assumed", UC4N=U.get("GROUND_BEAMS_m3"), FREELANCER_QS_REFERENCE=F.get("GROUND_BEAMS_m3"),
        SAME_BASIS="NO", POPULATION_DIFF="same network", GEOMETRY_DIFF="length basis as above",
        RULE_DIFF="Urban: p.13 section table by span length (interior), exterior FOLLOW ARCH bounded 1.0 m",
        ASSUMPTION_DIFF="christiannp: no depth; U-C4N / freelancer: own depths",
        ROOT_CAUSE_CLASS="SOURCE_AUTHORITY_DIFFERENCE", TECHNIQUE_TO_TEST="depth evidence ladder unchanged; keep length separate")
    add("Strap beams concrete", "m3", {"URBAN_OFFICIAL": 3.392, "URBAN_BEST": 3.392},
        num(cq[("STRAP_BEAMS", "concrete (schedule W x H, row chosen by drawn width)")]), "full face overlap x schedule W x H",
        UC4N=U.get("STRAPS_m3"), FREELANCER_QS_REFERENCE=F.get("STRAPS_m3"), SAME_BASIS="NO (length convention)",
        POPULATION_DIFF="same 3 straps", GEOMETRY_DIFF="same faces", RULE_DIFF="Urban clear length between footings; "
        "christiannp full length incl. the part inside footings", ASSUMPTION_DIFF="none",
        ROOT_CAUSE_CLASS="SAME_GEOMETRY_DIFFERENT_CONVENTION", TECHNIQUE_TO_TEST="none (Urban convention avoids a double count)")
    gs = Q["ground_slab"]
    add("Ground slab area", "m2", _L(gs["area"]), num(cq[("GROUND_SLAB", "ROUTE1v vector planar faces (sampled apportioning)")]),
        "vector faces, net of beams / columns / lift pit", NORMALISED_URBAN=gs["area"]["BEST_PROVISIONAL_QUANTITY"],
        NORMALISED_CHRIS=num(cq[("GROUND_SLAB", "ROUTE1v vector planar faces (sampled apportioning)")]),
        NORMALISED_BASIS="all cells between ground beams", SAME_BASIS="YES (BEST vs ROUTE1v)",
        POPULATION_DIFF="Urban official keeps only the 2 labelled zones (115.275); BEST adds 9 unlabelled cells",
        GEOMETRY_DIFF="lift pit 3.24 m2 inside one Urban cell; Urban single lines buffered 1 mm; 8 slivers excluded",
        RULE_DIFF="thickness ladder per cell (Urban) vs one note for all (christiannp)", ASSUMPTION_DIFF="label scope",
        ROOT_CAUSE_CLASS="URBAN_FALSE_POSITIVE (pit) + SAME_OBJECT_DIFFERENT_SEGMENTATION",
        TECHNIQUE_TO_TEST="S-BW boxes as barriers / void markers")
    add("Ground slab concrete", "m3", _L(gs["volume"]), num(cq[("GROUND_SLAB", "concrete (ROUTE1v x 0.10)")]), "ROUTE1v x 0.10",
        UC4N=U.get("GROUND_SLAB_m3"), FREELANCER_QS_REFERENCE=F.get("GROUND_SLAB_m3"), SAME_BASIS="YES (BEST)",
        ROOT_CAUSE_CLASS="as area", TECHNIQUE_TO_TEST="")
    add("Footings concrete (matched occurrences)", "m3", {"URBAN_OFFICIAL": 64.346, "URBAN_BEST": 64.346},
        num(cq[("FOOTINGS", "concrete, matched occurrences (schedule LxWxD)")]), "schedule L x W x D x 25 matched",
        UC4N=U.get("FOOTINGS_m3"), FREELANCER_QS_REFERENCE=F.get("FOOTINGS_m3"), SAME_BASIS="YES",
        POPULATION_DIFF="none (26 outlines, same handles)", ROOT_CAUSE_CLASS="SAME_OBJECT_SAME_RESULT",
        TECHNIQUE_TO_TEST="drawn polygon area x depth as a check (christiannp 64.304)")
    add("Footing F / F10 conflict (1B1B)", "m3", {"URBAN_OFFICIAL": None, "URBAN_LOW": 0.432, "URBAN_HIGH": 1.96, "URBAN_BEST": 1.96},
        "2.0 .. 2.275", "F10 schedule .. drawn 3.25 x 1.4 x 0.5", SAME_BASIS="NO (hypothesis sets)",
        RULE_DIFF="Urban {2 x F, F10}; christiannp {F10, drawn outline}", ROOT_CAUSE_CLASS="SOURCE_CONFLICT",
        TECHNIQUE_TO_TEST="add the drawn-outline hypothesis to the conflict record")
    pf = Q["columns"]["per_floor"]
    for fl, ck, uk, fk in (("FOUNDATION", "NECK(FOUNDATION->GF) concrete", "COL_FOU_m3", "COL_NECK_m3"), ("GF", "GF concrete", "COL_GF_m3", "COL_GF_m3"),
                           ("1F", "1F concrete", "COL_1F_m3", "COL_1F_m3"), ("2F", "2F concrete", "COL_2F_m3", "COL_2F_m3")):
        add(f"Columns {fl}", "m3", _L(pf[fl]["column_plus_joint"]), cq.get(("COLUMNS", ck)), "section x FFL interval (A01); neck / 2F unresolved",
            UC4N=U.get(uk), FREELANCER_QS_REFERENCE=F.get(fk), SAME_BASIS="NO",
            POPULATION_DIFF={"FOUNDATION": "36 vs 36", "GF": "christiannp 33 vs Urban 30 (planted / turned columns counted below)",
                             "1F": "christiannp 21 vs Urban 20 (planted on FFRS counted in 1F)", "2F": "9 vs 9"}[fl],
            RULE_DIFF="Urban column + joint, net of slab; christiannp full FFL-to-FFL height", ASSUMPTION_DIFF="A01 FFL as structural level",
            ROOT_CAUSE_CLASS="SAME_GEOMETRY_DIFFERENT_CONVENTION" + (" + DONOR_FALSE_POSITIVE" if fl in ("GF", "1F") else ""),
            TECHNIQUE_TO_TEST="storey-convention declaration on every column record")
    add("Beams concrete", "m3", _L(Q["beams"]["volume"]), num(cq[("BEAMS", "labelled strips concrete, full depth (overlaps slab)")]),
        "labelled strips x schedule B x D, full depth through the slab", UC4N=U.get("BEAMS_m3"), FREELANCER_QS_REFERENCE=F.get("BEAMS_GROSS_m3"),
        SAME_BASIS="NO", POPULATION_DIFF="christiannp 80 labelled strips; Urban residue 24 objects (8 unquantified) on top of V3b lines",
        RULE_DIFF="Urban B x (D - t) below slab; christiannp full D", ROOT_CAUSE_CLASS="SAME_GEOMETRY_DIFFERENT_CONVENTION",
        TECHNIQUE_TO_TEST="publish both full-depth and below-slab on one record")
    sl = Q["slabs"]["sheets"]
    vec = {pl: ch.json(f"09_slabs/{pl}/{pl}_SLAB_INPUTS_AND_VECTOR.json")["vector"] for pl in ("GFRS", "FFRS", "SFRS")}
    for fl, pl in PLAN_OF.items():
        cg, co = vec[pl]["VECTOR_GROSS_ENCLOSED_M2"], vec[pl]["VECTOR_OPENINGS_M2"]
        add(f"Suspended slab {fl} (= {pl}) area", "m2", _L(sl[fl]["net_area"]),
            f"gross {cg} / net {cq.get(('SLABS', f'{pl} net slab (excl. beams/columns/unambiguous openings; ambiguous voids NOT deducted)'))}",
            "christiannp net excludes beam strips and columns",
            NORMALISED_URBAN=sl[fl]["plate_m2"], NORMALISED_CHRIS=r3(cg - co), NORMALISED_BASIS="gross outline - openings (beams kept in the plate)",
            SAME_BASIS="YES after normalisation", POPULATION_DIFF="stair wells (Urban deducts 10.725 on GF and 1F), radial fans "
            "(Urban deducts), GF void face merge (Urban +6.98 m2 void)" if fl != "2F" else "none",
            GEOMETRY_DIFF=f"gross {sl[fl]['gross_m2']} vs {cg}", RULE_DIFF="opening classification", ASSUMPTION_DIFF="stair / dome",
            ROOT_CAUSE_CLASS="ASSUMPTION_DIFFERENCE + SAME_OBJECT_DIFFERENT_SEGMENTATION" if fl != "2F" else "SAME_OBJECT_SAME_RESULT",
            TECHNIQUE_TO_TEST="S-OPENING as barrier; fan / stair scenario pairs")
    add("Suspended slabs concrete", "m3", _L(Q["slabs"]["volume"]), "UNRESOLVED (no thickness)", "thickness not found",
        UC4N=U.get("SLABS_m3"), FREELANCER_QS_REFERENCE=F.get("SLABS_NET_m3"), SAME_BASIS="NO",
        ROOT_CAUSE_CLASS="SOURCE_AUTHORITY_DIFFERENCE (christiannp missed the stacked T / nn tags)", TECHNIQUE_TO_TEST="")
    acc_w = [r for r in walls_rows if r.get("CHRIS_ACCEPTED") is True]
    for w in (150, 200):
        cw = sum(float(r.get("M_TRUE_PHYSICAL_WALL") or 0) for r in acc_w if abs(float(r["SEPARATION_MM"]) - w) <= 15)
        add(f"Blockwork {w} mm length", "m", _L(Q["walls"]["length_by_thickness"][str(w)]), r3(cw),
            "PHYSICAL_WALL metres of accepted pairs at this separation", UC4N=U.get(f"BLOCK_{w}_m"), SAME_BASIS="NO",
            RULE_DIFF="christiannp PHYSICAL_WALL keeps door / window spans whose faces continue; Urban Method A bands are net of "
            "openings and stop at columns", ROOT_CAUSE_CLASS="SAME_GEOMETRY_DIFFERENT_CONVENTION",
            TECHNIQUE_TO_TEST="per-metre classes on Method A bands")
    oth = sum(float(r.get("M_TRUE_PHYSICAL_WALL") or 0) for r in acc_w
              if min(abs(float(r["SEPARATION_MM"]) - 150), abs(float(r["SEPARATION_MM"]) - 200)) > 15)
    add("Wall pairs at other separations", "m", {"URBAN_OFFICIAL": 0.0}, r3(oth), "PHYSICAL_WALL at separations outside 150 / 200",
        SAME_BASIS="NO", POPULATION_DIFF="Urban measures 150 / 200 only", ROOT_CAUSE_CLASS="URBAN_MISSED_PHYSICAL_OBJECT (partly)",
        TECHNIQUE_TO_TEST="width-agnostic pair census")
    add("Wall faces (physical, both sides)", "m2", _L(Q["walls"]["physical_faces"]["physical_area"]),
        f"GF {cq.get(('WALLS', 'GF physical wall face gross area (both sides, before openings)'))} + 1F "
        f"{cq.get(('WALLS', '1F physical wall face gross area (both sides, before openings)'))}; 2F unresolved",
        "floor-to-floor, before openings (A01 / A02)", SAME_BASIS="NO", RULE_DIFF="Urban interval - terminating member, net of openings",
        ROOT_CAUSE_CLASS="ASSUMPTION_DIFFERENCE", TECHNIQUE_TO_TEST="")
    kg = sum(num(v) or 0 for (t, i), v in cq.items() if t == "REBAR")
    add("Rebar (component evidence)", "kg", {}, r3(kg), "INCLUDED components only; bar length = member dimension (A05); 16 "
        "components UNRESOLVED", UC4N=U.get("NET_REBAR_t") and U["NET_REBAR_t"] * 1000, SAME_BASIS="NO",
        ROOT_CAUSE_CLASS="NOT_COMPARABLE", TECHNIQUE_TO_TEST="token census + conservation only (11)")
    return rows


# ============================================================================================ 02 gap register
GAP_FIELDS = ["GAP_ID", "TRADE", "OBJECT", "DIFFERENCE_CLASS", "QUANTITY_EFFECT", "WHO_IS_RIGHT", "TECHNIQUE", "ACTION",
              "WHEN", "EVIDENCE_FILE"]


def gap_register(parts):
    out = []
    n = 0
    for trade, fname, rows, key, eff in parts:
        for r in rows:
            c = r.get("DIFFERENCE_CLASS")
            if c in (None, "SAME_OBJECT_SAME_RESULT", "NOT_COMPARABLE"):
                continue
            n += 1
            out.append({"GAP_ID": f"G{n:03d}", "TRADE": trade, "OBJECT": r.get(key) or "", "DIFFERENCE_CLASS": c,
                        "QUANTITY_EFFECT": eff(r), "WHO_IS_RIGHT": _who(c), "TECHNIQUE": (r.get("NOTES") or "")[:220],
                        "ACTION": _action(c), "WHEN": _when(trade, c), "EVIDENCE_FILE": fname})
    return out


def _who(c):
    return {"URBAN_MISSED_PHYSICAL_OBJECT": "CHRIS", "URBAN_BINDING_FAILURE": "CHRIS", "URBAN_FALSE_POSITIVE": "CHRIS",
            "CHRIS_MISSED_PHYSICAL_OBJECT": "URBAN", "CHRIS_BINDING_FAILURE": "URBAN", "DONOR_FALSE_POSITIVE": "URBAN",
            "SOURCE_AUTHORITY_DIFFERENCE": "SEE_ROW", "SOURCE_CONFLICT": "NEITHER (source)",
            "ASSUMPTION_DIFFERENCE": "NEITHER (assumption)", "SAME_GEOMETRY_DIFFERENT_CONVENTION": "BOTH (convention)",
            "SAME_OBJECT_DIFFERENT_SEGMENTATION": "BOTH (segmentation)"}.get(c, "UNKNOWN")


def _action(c):
    return {"URBAN_MISSED_PHYSICAL_OBJECT": "fix Urban population route (generic)", "URBAN_BINDING_FAILURE": "deterministic tie-break",
            "URBAN_FALSE_POSITIVE": "fix Urban barrier / classification", "CHRIS_MISSED_PHYSICAL_OBJECT": "none (Urban stronger)",
            "CHRIS_BINDING_FAILURE": "none (Urban stronger)", "DONOR_FALSE_POSITIVE": "none (record)",
            "SOURCE_AUTHORITY_DIFFERENCE": "keep Urban source route", "SOURCE_CONFLICT": "owner / consultant question",
            "ASSUMPTION_DIFFERENCE": "scenario pair + source search", "SAME_GEOMETRY_DIFFERENT_CONVENTION": "declare convention id",
            "SAME_OBJECT_DIFFERENT_SEGMENTATION": "compare on invariant (length / area), not counts"}.get(c, "investigate")


def _when(trade, c):
    if trade in ("FOOTING", "REBAR") and c not in ("CHRIS_MISSED_PHYSICAL_OBJECT", "CHRIS_BINDING_FAILURE", "DONOR_FALSE_POSITIVE"):
        return "BEFORE_S4 (test only)"
    return "AFTER_S4"


# ============================================================================================ main
def main(chris_dir):
    ch = Chris(chris_dir)
    gb, seg = ground_beams(ch)
    gs = ground_slab(ch)
    bm = beams(ch)
    wl = walls(ch)
    ft = footings(ch)
    co = columns(ch)
    op = slab_openings(ch)
    rb = rebar_corpus(ch)
    md = manual_decisions(ch)
    tm = technique_matrix()
    rc = reconciliation(ch, seg, wl)
    gap = gap_register([
        ("GROUND_BEAM", "03_GB_OBJECT_CROSSWALK.csv", gb, "CHRIS_OBJECT_ID", lambda r: r.get("CHRIS_VALUE") or ""),
        ("GROUND_SLAB", "05_GROUND_SLAB_ROUTE_COMPARISON.csv", [r for r in gs if r["ROW_KIND"] == "CELL"], "ROUTE",
         lambda r: f"{r.get('DIFF_VS_URBAN_BEST_M2')} m2"),
        ("BEAM", "06_BEAM_BINDING_CROSSWALK.csv", bm, "TAG_KEY", lambda r: f"{r.get('URBAN_DRAWN_LENGTH_M') or ''} m"),
        ("WALL", "07_WALL_PAIR_CROSSWALK.csv", [r for r in wl if r["DIFFERENCE_CLASS"] != "SAME_GEOMETRY_DIFFERENT_CONVENTION"],
         "CHRIS_PAIR_ID", lambda r: f"{r.get('M_TRUE_PHYSICAL_WALL') or 0} m physical"),
        ("FOOTING", "08_FOOTING_OCCURRENCE_CROSSWALK.csv", ft, "CHRIS_ID", lambda r: r.get("CHRIS_M3_SCHEDULE") or ""),
        ("COLUMN", "09_COLUMN_CROSSWALK.csv", co, "CHRIS_ID", lambda r: r.get("CHRIS_INTERVALS") or ""),
        ("SLAB_OPENING", "10_SLAB_OPENING_CROSSWALK.csv", op, "OPENING_ID",
         lambda r: f"Urban {r.get('URBAN_AREA_M2')} / christiannp {r.get('CHRIS_AREA_M2')} m2"),
    ])
    files = {
        "02_OBJECT_GAP_REGISTER.csv": write_csv("02_OBJECT_GAP_REGISTER.csv", gap, GAP_FIELDS),
        "03_GB_OBJECT_CROSSWALK.csv": write_csv("03_GB_OBJECT_CROSSWALK.csv", gb, XW),
        "05_GROUND_SLAB_ROUTE_COMPARISON.csv": write_csv("05_GROUND_SLAB_ROUTE_COMPARISON.csv", gs, SLAB_FIELDS),
        "06_BEAM_BINDING_CROSSWALK.csv": write_csv("06_BEAM_BINDING_CROSSWALK.csv", bm, BEAM_FIELDS),
        "07_WALL_PAIR_CROSSWALK.csv": write_csv("07_WALL_PAIR_CROSSWALK.csv", wl, WALL_FIELDS),
        "08_FOOTING_OCCURRENCE_CROSSWALK.csv": write_csv("08_FOOTING_OCCURRENCE_CROSSWALK.csv", ft, FOOT_FIELDS),
        "09_COLUMN_CROSSWALK.csv": write_csv("09_COLUMN_CROSSWALK.csv", co, COL_FIELDS),
        "10_SLAB_OPENING_CROSSWALK.csv": write_csv("10_SLAB_OPENING_CROSSWALK.csv", op, OPEN_FIELDS),
        "11_REBAR_TOKEN_CORPUS.csv": write_csv("11_REBAR_TOKEN_CORPUS.csv", rb, REBAR_FIELDS),
        "12_CHRIS_MANUAL_DECISION_GAP.csv": write_csv("12_CHRIS_MANUAL_DECISION_GAP.csv", md, MD_FIELDS),
        "14_DONOR_TECHNIQUE_MATRIX_UPDATED.csv": write_csv("14_DONOR_TECHNIQUE_MATRIX_UPDATED.csv", tm, TM_FIELDS),
        "15_QUANTITY_RECONCILIATION_UPDATED.csv": write_csv("15_QUANTITY_RECONCILIATION_UPDATED.csv", rc, REC_FIELDS),
    }
    summary = {"stamp": STAMP, "gb_segmentation": seg,
               "class_counts": {k: dict(Counter(r.get("DIFFERENCE_CLASS") for r in v)) for k, v in
                                (("GB", gb), ("GROUND_SLAB_CELLS", [r for r in gs if r["ROW_KIND"] == "CELL"]), ("BEAMS", bm),
                                 ("WALLS", wl), ("FOOTINGS", ft), ("COLUMNS", co), ("SLAB_OPENINGS", op), ("GAPS", gap))},
               "rebar": {"patterns": len(rb), "occurrences": sum(r["N_OCCURRENCES"] for r in rb),
                         "disagreement": dict(Counter(r["URBAN_DISAGREEMENT"].split(":")[0] for r in rb))},
               "manual_decisions": dict(Counter(r["DOES_URBAN_ALREADY_HANDLE_DETERMINISTICALLY"] for r in md)),
               "manual_decision_classes": dict(Counter(r["GAP_CLASS"] for r in md))}
    files["15_QUANTITY_RECONCILIATION_UPDATED.json"] = dumps({"stamp": STAMP, "rows": rc})
    (OUT / "15_QUANTITY_RECONCILIATION_UPDATED.json").write_text(files["15_QUANTITY_RECONCILIATION_UPDATED.json"], encoding="utf-8")
    files["R9_1_SUMMARY.json"] = dumps(summary)
    (OUT / "R9_1_SUMMARY.json").write_text(files["R9_1_SUMMARY.json"], encoding="utf-8")
    ledger = {"zip_sha256": ZIP_SHA256, "manifest_sha256": MANIFEST_SHA256, "dataset": ch.manifest["dataset"],
              "frozen_at_utc": ch.manifest["frozen_at_utc"], "source_integrity": ch.manifest["source_integrity"],
              "files_read": dict(sorted(ch.read.items())), "drawings_match_urban": {
                  k: any(f["sha256_after"] == v for f in ch.manifest["source_integrity"]["files"]) for k, v in DRAWINGS.items()}}
    files["CHRIS_INPUT_LEDGER.json"] = dumps(ledger)
    (OUT / "CHRIS_INPUT_LEDGER.json").write_text(files["CHRIS_INPUT_LEDGER.json"], encoding="utf-8")
    for k, v in sorted(files.items()):
        print(f"{k:45s} {hashlib.sha256(v.encode()).hexdigest()[:16]}")
    write_index()
    return summary


def write_index():
    """sha256 of every file of the package (markdown written by hand included), INDEX.json excluded."""
    idx = {}
    for f in sorted(OUT.rglob("*")):
        if f.is_file() and f.name != "INDEX.json" and "__pycache__" not in f.parts:
            idx[str(f.relative_to(OUT)).replace("\\", "/")] = hashlib.sha256(f.read_bytes()).hexdigest()
    (OUT / "INDEX.json").write_text(dumps({"stamp": STAMP, "files": idx}), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1:] == ["--index-only"]:
        write_index()
    else:
        print(json.dumps(main(sys.argv[1])["class_counts"], indent=1))
