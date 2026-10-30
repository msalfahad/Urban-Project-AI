"""T-360 development-villa run: facade cladding / stone (B4-11), sheet by sheet and face by face.

Usage (repository root, Python 3.11):
  python3 -I research/agents_t360/t360_alsenan.py --write      write the ledgers below from the committed inputs
  python3 -I research/agents_t360/t360_alsenan.py --check      rebuild in memory, compare byte for byte
  python3 -I research/agents_t360/t360_alsenan.py --geometry <P7757.dxf>
        re-read the private DXF (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, sha256 ab54dd55...):
        the material-keyword text census, the hatch census of the two elevation frames (by handle) and the visible
        face of the porch-mouth arch surround (layer 1, bounded by the cited handles); prints areas, counts and
        handles only and asserts them against the committed values.

Inputs: this task's own sheet reading (SHEETS below: what each architectural page shows, no coordinate, no image, no
client text), the merged face keys research/agents_t337/BINDING_T337.csv (T-337 MERGED) and the freelancer's parsed
rows tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (keyword census only; no cell text is copied out).
Outputs: SHEET_CENSUS_T360.csv, FACE_STATE_T360.csv, CANDIDATES_T360.csv, HATCHES_T360.csv, summary.json.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t360_cladding_rules as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
T337 = os.path.join(ROOT, "research", "agents_t337", "BINDING_T337.csv")
FREE = os.path.join(ROOT, "tests", "alsenan", "registers_b1", "FREELANCER_RAW_ROWS.json")

DRV = "Drive 'Alsenan chalet project'"
# (sheet, view, how read, legend / schedule, hatch on an exterior face, text naming a material, graphic form, verdict, note)
SHEETS = [
    ("Pages_01-02 p.1", "GF + 1F AREA PLAN 1:200", "T-091 (whole page + area tables)", "none", "none", "none", "none",
     "absent", "plan: no exterior face drawn in elevation"),
    ("Pages_01-02 p.2", "2F AREA PLAN 1:200", "T-091", "none", "none", "none", "none", "absent", "plan"),
    ("p7757_arch_sheet03.pdf", "GROUND FLOOR PLAN 1:100", "T-091 (whole page + quarters)", "none", "none", "none",
     "none", "absent", "plan: 0 finish notes (T-091 PRINTED_NOTES.csv)"),
    ("p7757_arch_sheet04.pdf", "1st.FLOOR PLAN 1:100", "T-091", "none", "none", "none", "none", "absent", "plan"),
    ("Pages_05-06 p.5", "2nd.FLOOR PLAN 1:100", "T-091", "none", "none", "none", "none", "absent", "plan"),
    ("Pages_05-06 p.6", "SOUTH EAST ELEVATION 1:100", "own: 120 dpi whole page + 300 dpi crops; DXF SE frame",
     "none", "ground (AR-PARQ1) and section-cut bands (LINE) only", "none (levels and dimensions only)",
     "PORCH-MOUTH ARCH SURROUND: voussoir / quoin block outlines, layer 1",
     "marks a FORM (unit outlines), no material",
     "the only drawn unit pattern on any exterior face of the set; no legend, hatch or text names it (R-T360-2)"),
    ("Pages_07-08 p.7", "SOUTH WEST ELEVATION 1:100", "own: 120 dpi whole page + 300 dpi crop", "none",
     "ground only", "none", "a field of 6 vertical lines at the annex junction, spacing 10 / 23 / 32 / 39 / 46 px "
     "(300 dpi) = curved-face shading (R-T360-3)", "absent", "plain faces, openings, railings X-pattern"),
    ("Pages_07-08 p.8", "NORTH WEST ELEVATION 1:100", "own: 120 dpi whole page; DXF NW frame", "none",
     "ground and section-cut bands only", "none", "W17 curved-glazing lines (a window, T-238); arch frame band "
     "20 / 30 (archivolt, T-238 / T-324)", "absent", "plain faces"),
    ("p7757_arch_sheet09.pdf", "NORTH EAST ELEVATION 1:100", "own: 120 dpi whole page", "none",
     "ground and section-cut bands only", "none", "curved-face shading fields beside the annex and the GF hall",
     "absent", "drawn as a cut through the annex and the GF hall (T-082)"),
    ("p7757_arch_sheet10.pdf", "SECTION A-A 1:100", "own: 120 dpi whole page", "none", "section-cut bands only",
     "none", "none", "absent", "stair section"),
    ("Pages_11-12 p.11", "SECTION B-B 1:100", "own: 120 dpi whole page", "none", "section-cut bands only", "none",
     "dome rib lines (domes: owner, no domes in scope)", "absent", ""),
    ("Pages_11-12 p.12", "FENCE PLAN / ELEVATION / SECTION 1:100", "own: 120 dpi whole page", "none",
     "ground; the section's cross-hatch is the cut base", "'3700' house number only", "none", "absent",
     "boundary element faces: blockwork / plaster owners (Q-63 C, Q-65)"),
    ("sanitary-7757.pdf p.1-3", "GF / 1F / 2F DRAINAGE PLAN", "T-091", "none", "none", "none (manhole note)", "none",
     "absent", "drainage only"),
    ("P7757.dxf (P7757_DXF_COMPRESSED.zip)", "model space: plans + SE and NW elevation frames",
     "own: every TEXT / MTEXT / ATTRIB in model space and blocks; every HATCH", "none",
     "elevation frames: 8 hatches, all ground or section cut (HATCHES_T360.csv)",
     "0 of 675 texts match a material keyword (Latin); Arabic SHX decoded by T-091: 0 material notes",
     "the porch-mouth arch surround (SE frame)", "SE frame marks a FORM only; NW frame absent", ""),
]

# Elevation-frame hatches (own census of P7757.dxf; handle, frame, pattern, layer, width x height m, role).
HATCHES = [
    ("1C01", "SE", "LINE", "3", 6.700, 1.050, "section_cut", "section-cut band at the annex roof level"),
    ("23DE", "SE", "LINE", "3", 15.000, 0.300, "section_cut", "section-cut band along the base"),
    ("23E3", "SE", "LINE", "3", 0.200, 0.200, "section_cut", "cut element end at the annex section edge"),
    ("23E7", "SE", "AR-PARQ1", "3", 18.898, 0.650, "ground", "earth below the ground line"),
    ("27AF", "NW", "LINE", "3", 1.438, 2.850, "section_cut", "section-cut band in the pool-court cut (below +0.15)"),
    ("27D1", "NW", "LINE", "3", 9.538, 1.050, "section_cut", "slab cut band"),
    ("27D2", "NW", "LINE", "3", 15.000, 2.000, "section_cut", "section-cut band along the base"),
    ("27D4", "NW", "AR-PARQ1", "3", 19.416, 2.350, "ground", "earth below the ground line"),
]

# Porch-mouth arch surround, own vector reading of the SE frame (layer 1). Bounding handles: 23A8 (left edge line of the
# porch-mouth pier, 4.550 m), 23FE (band foot), 2416 (annex section cut line), 1CC8 (inner top line of the crown block;
# the frame reaches 50 mm above it, so the crown's outer top line 2230, 10 mm higher, is inside).
# r2 (Gate A rejection D-T360-1 re-examined): every one of the 10 blocks is drawn as a DOUBLE outline; each block's
# face is decided per block by R.block_face (R-T360-6), and all 10 have their second ring drawn 10 mm outside, with the
# joint and band lines ending on that outer ring. Inner outline -> outer ring, by handle (outer handles found on the
# offset ring by an own census):
BLOCK_RINGS = (
    ("quoin 1", "23FC/23FD/2401/2402", "23F9/23FA/23FB/23FF/2400"),
    ("quoin 2", "1CC9/1CCA/23AE/23AF", "1CC0/1CC1/1CE6 + band lines"),
    ("quoin 3", "1CCB/1CCC/23B0/23B1", "1CBD/1CBE/1CBF/1CE5"),
    ("springer", "1CCD/1CCE/23B2/23B3", "1CA6/1CBB/1CBC/1CE3"),
    ("voussoir 2", "1CCF/1CD1/23B4/23B5", "1CA7/1CB8/1CBA/1CE1"),
    ("voussoir 3", "1CD2/1CD4/23B6/23B7", "1CA8/1CB5/1CB7/1CDF"),
    ("voussoir 4 (large)", "23B8/23B9/23BA/23BB", "23A9/1CDD/23A7/1CB4 (joint lines 1CED / 1CEE end on it)"),
    ("voussoir 5", "1CD6/1CD8/23BC/23BD", "1CA9/1CB0/1CB2/1CDB"),
    ("voussoir 6", "1CC4/1CC5/23AA/23AB", "1CAA/1CAD/1CAF/1CDA"),
    ("crown", "1CC6/1CC7/1CC8/23AC/23AD", "1CC3/2230/222F/1CAB/1CC2 (right side cut by 2416)"),
)
SURROUND = dict(
    handles_bound="23A8 / 23FE / 2416 / 1CC8",
    visible_face_m2=1.5149, pieces=21, large_blocks=10, band_pieces=11, height_m=4.383, width_m=2.251,
    double_outline_blocks=10,
    jamb_hand_m2=0.535,
    jamb_hand="3 quoins 0.35 x 0.30 = 0.315 + band 0.20 x (0.20 + 3 x 0.30) = 0.220 (jamb 2.000 m to the springing)",
    arch_m2=round(1.5149 - 0.535, 4),
    arch_hand="7 block faces (outer rings) 0.0897 + 0.0931 + 0.0930 + 0.1054 + 0.0932 + 0.0933 + 0.1349 = 0.7026 + "
              "7 band pieces 0.0476 + 0.0511 + 0.0513 + 0.0448 + 0.0514 + 0.0257 + 0.0046 = 0.2765 -> 0.9791 "
              "(function 0.9799: +0.0008 = the closed 10 mm pen joints)",
    crown_side_sliver="IN: band piece right of the crown, drawn by 222F / 2231 / 2233 and truncated by the section line "
                      "2416, visible strip 0.0046 m2 (R-T360-6: a drawn piece cut by a section line is visible face)",
    block_quads="23FC/23FD/2401/2402 (quoin 1, outer 23FB/23FA); 1CC9/1CCA/23AE/23AF; 1CCB/1CCC/23B0/23B1; "
                "1CCD/1CCE/23B2/23B3; 1CCF/1CD1/23B4/23B5; 1CD2/1CD4/23B6/23B7; 23B8..23BB; 1CD6/1CD8/23BC/23BD; "
                "1CC4/1CC5/23AA/23AB; crown block 1CC8/23AC/23AD",
)


def _csv(rows, header):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(["" if v is None else v for v in r])
    return buf.getvalue()


SIDE_SHEET = {"SE": "Pages_05-06 p.6", "SW": "Pages_07-08 p.7", "NW": "Pages_07-08 p.8",
              "NE": "p7757_arch_sheet09.pdf"}


def face_rows():
    rows = []
    for b in csv.DictReader(open(T337, encoding="utf-8")):
        side = b["side"].split("-")[0]
        sheet = SIDE_SHEET.get(side, "no elevation (side-passage face; plans only)")
        face = R.Face(b["key"], float(b["length_m"]), float(b["bottom"] or 0), float(b["top"] or 0),
                      marks=(), plaster_line=b["line"])
        st = R.face_state(face)
        rows.append((b["key"], b["kind"], b["line"], b["status"], sheet, st["state"], st["status"], None, None,
                     "0.000000", "no cladding: the face's finish owner stays " + b["line"]
                     + ("; finish not printed (T-337 / T-317): stays HELD in its own line, never a stone default"
                        if b["kind"] == "plinth" else "")))
    return rows


def freelancer_census():
    d = json.load(open(FREE, encoding="utf-8"))
    kw = re.compile(r"حجر|كلاد|تكسي|كسوة|جرانيت|GRC|stone|clad|granite", re.I)
    hits = 0
    for r in d["rows"]:
        for c in r["cells"].values():
            if isinstance(c.get("v"), str) and kw.search(c["v"]):
                hits += 1
    pls_facade = sum(1 for r in d["rows"] if r["file"] == "PLS"
                     and any(isinstance(c.get("v"), str) and "واجه" in c["v"] for c in r["cells"].values()))
    return dict(rows=len(d["rows"]), per_file=d["per_file"], cladding_keyword_cells=hits,
                pls_facade_rows=pls_facade)


def candidate_rows():
    s = SURROUND
    return [
        ("C-1", "porch-mouth arch surround (voussoir / quoin blocks, SE)", "Pages_05-06 p.6; P7757.dxf SE frame layer 1 ("
         + s["handles_bound"] + ")", "MARKED_FORM_MATERIAL_HELD",
         f"visible part {s['visible_face_m2']} m2 ({s['pieces']} pieces: {s['large_blocks']} blocks + "
         f"{s['band_pieces']} band pieces; jamb {s['jamb_hand_m2']} by hand + arch {s['arch_m2']}; all "
         f"{s['double_outline_blocks']} blocks double-outlined, face = outer ring, R-T360-6); the other half lies "
         "behind the annex section line 2416: UNKNOWN", None, R.HELD,
         "none of the 109 T-337 face keys (porch mouth = open side; T-238 F-PORCH-ARCH UNKNOWN)",
         "if stone: replaces plaster / Sigma on the porch-mouth wall piece (no line today: T-238); if plaster-formed "
         "blocks: it is plaster / Sigma + arrises, not B4-11", "renders: two sets disagree (white stepped blocks vs "
         "grey cut stone, T-161 F11): design intent only, never the material"),
        ("C-2", "plinth band, ground -> lowest F.F.L. (29 faces)", "elevations draw the band, print no finish",
         "NOT_MARKED", "71.689 .. 72.750 m2 in NEW FIN.EXT.FINISH PLINTH GF (T-337, HELD)", None,
         "NOT IN DRAWN SCOPE (B4-11)", "29 T-337 plinth keys", "none: stays in its own line; finish HELD",
         "OWNER_RULE_OUTDOOR_FLOORS covers floors, not the plinth face"),
        ("C-3", "court crazy-paving stone (renders)", "renders only (OWNER_NOTES_SIGMA item 3 follow-up)", "REFUSED",
         "outdoor floor, not a facade face (T-343 / owner interlock rule)", None, "NOT B4-11", "-", "-",
         "a render is never a source (R-T360-1)"),
    ]


def build():
    sheets = _csv(SHEETS, ["sheet", "view", "read", "legend_schedule", "hatch_on_exterior_face",
                           "text_naming_material", "graphic_form", "verdict", "note"])
    hat = _csv([h[:4] + (f"{h[4]:.3f}", f"{h[5]:.3f}", h[6], R.hatch_kind(h[2], h[6]), h[7]) for h in HATCHES],
               ["handle", "frame", "pattern", "layer", "width_m", "height_m", "role", "b4_11_kind", "what"])
    fr = face_rows()
    faces = _csv(fr, ["key", "kind", "t337_line", "t337_status", "elevation_sheet", "b4_11_state", "b4_11_status",
                      "cladding_m2", "material", "double_count_m2", "finish_owner"])
    cands = _csv(candidate_rows(), ["id", "element", "evidence", "state", "geometry", "cladding_m2", "b4_11_status",
                                    "face_key", "replaces_named_not_applied", "note"])
    states = {}
    for r in fr:
        states[r[5]] = states.get(r[5], 0) + 1
    summary = dict(
        task="T-360", family="B4-11 FACADE CLADDING / STONE",
        sheets_searched=len(SHEETS), sheets_marking_material=0, sheets_marking_form_only=1,
        dxf_texts=675, dxf_material_keyword_hits=0, elevation_frame_hatches=len(HATCHES),
        elevation_frame_hatches_finish=0,
        face_keys=len(fr), face_states=states, cladding_m2_established=0.0, double_count_m2=0.0,
        candidate_porch_arch=dict(state="MARKED_FORM_MATERIAL_HELD", visible_face_m2=SURROUND["visible_face_m2"],
                                  pieces=SURROUND["pieces"], double_outline_blocks=SURROUND["double_outline_blocks"],
                                  status="HELD (blank; hidden half UNKNOWN)"),
        freelancer=freelancer_census(),
        curved_shading_sw_p7=R.is_curved_face_shading([86, 96, 119, 151, 190, 236]),
    )
    js = json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    return {"SHEET_CENSUS_T360.csv": sheets, "HATCHES_T360.csv": hat, "FACE_STATE_T360.csv": faces,
            "CANDIDATES_T360.csv": cands, "summary.json": js}


def geometry(path):
    import ezdxf
    from shapely.geometry import LineString, box
    from shapely.ops import unary_union

    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    kw = re.compile(r"STONE|CLAD|GRANIT|MARBL|TILE|BRICK|GRC|TRAVERT|CERAM|PORCEL|FINISH|MATERIAL|PLASTER|PAINT|"
                    r"LEGEND|NOTE", re.I)
    texts = []
    for lay in [msp] + [b for b in doc.blocks if not b.name.startswith("*Paper")]:
        for e in lay.query("TEXT MTEXT ATTRIB ATTDEF"):
            texts.append(e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text)
    hits = sum(1 for t in texts if kw.search(t))
    print("texts", len(texts), "material keyword hits", hits)
    assert len(texts) == 675 and hits == 0
    for h in HATCHES:
        e = doc.entitydb[h[0]]
        assert e.dxftype() == "HATCH" and e.dxf.pattern_name == h[2] and e.dxf.layer == h[3], h
        from ezdxf import bbox
        b = bbox.extents([e])
        w, hh = (b.extmax.x - b.extmin.x) / 1000, (b.extmax.y - b.extmin.y) / 1000
        assert abs(w - h[4]) < 0.002 and abs(hh - h[5]) < 0.002, (h, w, hh)
        print("hatch", h[0], h[2], f"{w:.3f} x {hh:.3f}", h[6])
    H = doc.entitydb
    x0 = H["23A8"].dxf.start.x - 100
    x1 = H["2416"].dxf.start.x
    y0 = min(H["23FE"].dxf.start.y, H["23FE"].dxf.end.y)
    y1 = H["1CC8"].dxf.start.y + 50
    B = box(x0, y0, x1, y1)
    segs = [B.boundary]
    lines = []  # the drawn layer-1 lines only (no frame box): evidence for each block's own outline(s)
    for e in msp.query("LINE ARC LWPOLYLINE"):
        if e.dxf.layer != "1":
            continue
        if e.dxftype() == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif e.dxftype() == "ARC":
            pts = [(p.x, p.y) for p in e.flattening(2)]
        else:
            pts = [(p[0], p[1]) for p in e.get_points()]
        g = LineString(pts).intersection(B)
        if not g.is_empty:
            segs.append(g)
            lines.append(g)

    def thin(r):
        c = list(r.minimum_rotated_rectangle.exterior.coords)
        return min(math.dist(c[0], c[1]), math.dist(c[1], c[2])) < 20

    # pen lines are 10 mm double outlines: regions between lines, then restored by the half pen width and closed.
    # r2: a thin region is kept when it touches the annex section-cut line 2416 (x1): it is a drawn piece truncated by
    # the cut (the band piece right of the crown, lines 222F / 2231 / 2233 / 2416), visible face up to the cut (R-T360-6)
    cut = LineString([(x1, y0), (x1, y1)])
    regs = [r for r in B.difference(unary_union(segs).buffer(6, cap_style=2)).geoms if r.area > 1000]
    sel = [r for r in regs if r.area < 0.2e6 and (not thin(r) or r.distance(cut) < 7)]
    U = unary_union([r.buffer(6, join_style=2) for r in sel]).buffer(8, join_style=2).buffer(-8, join_style=2)
    # each block's own outline, polygonized exactly at 1 mm; its face is decided per block from the linework (r2,
    # R-T360-6, block_face): the OUTER ring where a second ring is drawn 10 mm outside, else the single line itself
    import shapely
    from shapely.ops import polygonize
    inner = [f for f in polygonize(shapely.set_precision(unary_union(segs), 1.0))
             if 0.07e6 < f.area < 0.13e6 and len(f.exterior.coords) <= 6 and f.within(U.buffer(15, join_style=2))]
    print("inner block outlines", len(inner))
    assert len(inner) == SURROUND["large_blocks"]
    faces = [R.block_face(f, lines, pen=10.0, tol=3.0, clip=B) for f in inner]
    kinds = [k for _, k in faces]
    print("block outlines DOUBLE", kinds.count("DOUBLE"), "SINGLE", kinds.count("SINGLE"))
    for f, (g, k) in sorted(zip(inner, faces), key=lambda p: (p[0].centroid.y, p[0].centroid.x)):
        print(f"  block outline {f.area / 1e6:.4f} -> {k} face {g.intersection(B).area / 1e6:.4f}")
    assert kinds.count("DOUBLE") == SURROUND["double_outline_blocks"]
    U = unary_union([U] + [g for g, _ in faces]).buffer(1, join_style=2).buffer(-1, join_style=2)
    U = U.intersection(B)  # nothing beyond the annex section line 2416
    jamb = U.intersection(box(x0, y0, x1, min(H["1CBC"].dxf.start.y, H["1CBC"].dxf.end.y)))
    area = round(U.area / 1e6, 4)
    print("surround pieces", len(sel), "visible face m2", area, "jamb m2", round(jamb.area / 1e6, 4),
          "height m", round((U.bounds[3] - y0) / 1000, 3), "width m", round((U.bounds[2] - U.bounds[0]) / 1000, 3),
          "geom", U.geom_type)
    assert len(sel) == SURROUND["pieces"] and abs(area - SURROUND["visible_face_m2"]) < 0.0005
    assert abs(jamb.area / 1e6 - SURROUND["jamb_hand_m2"]) < 0.002
    print("GEOMETRY OK")


def main(argv):
    out = build()
    if "--write" in argv:
        for k, v in out.items():
            open(os.path.join(HERE, k), "w", encoding="utf-8", newline="").write(v)
        print("written", ", ".join(out))
    elif "--check" in argv:
        bad = [k for k, v in out.items() if open(os.path.join(HERE, k), encoding="utf-8", newline="").read() != v]
        print("check", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    elif "--geometry" in argv:
        geometry(argv[argv.index("--geometry") + 1])
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
