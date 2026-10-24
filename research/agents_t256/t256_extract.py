"""T-256 extractor: per-column evidence for the 15 CONFLICT columns and the 5 NOT_DRAWN upper lines (values only).

Reads the private copies (never committed) of Drive "Alsenan chalet project":
    'ST7757 dxf.dxf'                 sha256 9f9d1179...  structural set (slab plans, CAP, schedule)
    'P7757_DXF_COMPRESSED.zip'       -> P7757.dxf, sha256 ab54dd55...  architectural set
    'ST7757.pdf'                     sha256 74da1523...  the issued structural plot (16 pages, vector, 1:100 on A3)
and the committed T-217 / T-248 research inputs. Writes ALSENAN_T256_EVIDENCE.json: DXF handles, sizes in mm, page
numbers, counts and booleans. No coordinates, no text of the drawings beyond size marks, no client data.

    python3 -I research/agents_t256/t256_extract.py <ST dxf> <P7757 dxf> <ST pdf> [--write]

The PDF part needs PyMuPDF (`pip install pymupdf`); without it the PDF block is written as NOT_RUN (never as a match).
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SHA = {"st": "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079",
       "arch": "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4",
       "pdf": "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"}
PITCH = 38724.406108773          # T-217: the six plan frames are one drawing at this pitch (mm)
FP_CENTRE_X = 135500.0
FRAME = {"GF": ("GFRS", 2, 4), "1F": ("FFRS", 3, 5), "2F": ("SFRS", 4, 6)}   # sheet, frame index, PDF page
BAND = {"GF": "GR", "1F": "1ST", "2F": "2ND"}
PT_MM = 1000 / 28.3465           # 1:100 plot: 1 pt on paper = 35.28 mm in the building
FACE_TOL = 30.0                  # mm: a dimension point lies on a column face
ARCH_WINDOWS = {"GF": (-162, -127, -807, -789), "1F": (-196, -173, -806, -790), "2F": (-237, -224, -799, -790)}
ST_WINDOWS = {"GF": (40.5, 74.5, 35.5, 51.0), "1F": (11.5, 36.0, 35.5, 51.0), "2F": (-27.0, -2.0, 35.5, 51.0)}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _ledger():
    rows = list(csv.DictReader(open(ROOT / "research/agents_t248/LEDGER_T248.csv", encoding="utf-8")))
    conflict = [r for r in rows if r["status"] == "CONFLICT" and r["kind"] in ("COLUMN", "TURNED")]
    unknown = [r for r in rows if r["status"] == "UNKNOWN"]
    return conflict, unknown


def _bb(e):
    from ezdxf import bbox
    b = bbox.extents([e])
    return b if b.has_data else None


def _col_outlines(msp, storey_frame=None):
    out = []
    for e in msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        b = _bb(e)
        if b is None or max(b.size.x, b.size.y) > 1500:
            continue
        fr = round((FP_CENTRE_X - b.center.x) / PITCH)
        if storey_frame is None or fr == storey_frame:
            out.append((e.dxf.handle, b.center.x, b.center.y, b.size.x, b.size.y))
    return out


def _arch_translation(st_msp, ar_msp):
    """T-147 column fit, re-run: per storey the one translation that puts the architectural S-COL.BON outlines on the
    structural slab-plan outlines (returns translation in mm, matched count, spread)."""
    res = {}
    for s in ("GF", "1F", "2F"):
        def cents(m, w):
            pts = []
            for e in m.query('LWPOLYLINE[layer=="S-COL.BON"]'):
                b = _bb(e)
                if b is None:
                    continue
                cx, cy = b.center.x / 1000, b.center.y / 1000
                if w[0] < cx < w[1] and w[2] < cy < w[3] and max(b.size.x, b.size.y) < 1500:
                    if all(math.hypot(cx - u[0], cy - u[1]) > 0.05 for u in pts):
                        pts.append((cx, cy, b.size.x, b.size.y, e.dxf.handle))
            return pts
        a, t = cents(ar_msp, ARCH_WINDOWS[s]), cents(st_msp, ST_WINDOWS[s])
        votes = collections.Counter((round(q[0] - p[0], 2), round(q[1] - p[1], 2)) for p in a for q in t)
        (tx, ty), _ = votes.most_common(1)[0]
        pairs = [(p, q) for p in a for q in t if math.hypot(q[0] - p[0] - tx, q[1] - p[1] - ty) < 0.03]
        dx = [q[0] - p[0] for p, q in pairs]
        dy = [q[1] - p[1] for p, q in pairs]
        mx, my = sum(dx) / len(dx), sum(dy) / len(dy)
        spread = max(max(abs(v - mx) for v in dx), max(abs(v - my) for v in dy))
        same_size = sum(1 for p, q in pairs if abs(p[2] - q[2]) < 1 and abs(p[3] - q[3]) < 1)
        res[s] = {"t_mm": (mx * 1000, my * 1000), "arch_outlines": len(a), "st_outlines": len(t), "matched": len(pairs),
                  "same_size": same_size, "spread_mm": round(spread * 1000, 3)}
    return res


def _arch_member(ar_msp, ar_dims, ar_walls, st_e, t_mm):
    b = _bb(st_e)
    cx, cy = b.center.x - t_mm[0], b.center.y - t_mm[1]
    w, d = b.size.x, b.size.y
    copies = []
    for e in ar_msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        ab = _bb(e)
        if ab and abs(ab.center.x - cx) < 80 and abs(ab.center.y - cy) < 80 and max(ab.size.x, ab.size.y) < 1600:
            copies.append({"handle": e.dxf.handle, "layer": "S-COL.BON", "W_mm": round(ab.size.x), "D_mm": round(ab.size.y),
                           "same_size": abs(ab.size.x - w) < 1 and abs(ab.size.y - d) < 1})
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2

    def on_face(p):
        inside = x0 - FACE_TOL <= p[0] <= x1 + FACE_TOL and y0 - FACE_TOL <= p[1] <= y1 + FACE_TOL
        face = min(abs(p[0] - x0), abs(p[0] - x1)) <= FACE_TOL or min(abs(p[1] - y0), abs(p[1] - y1)) <= FACE_TOL
        return inside and face

    both, one = [], 0
    for h, m, a, c in ar_dims:
        fa, fc = on_face(a), on_face(c)
        if fa and fc:
            horiz = abs(a[1] - c[1]) < 1
            spans_width = horiz and min(abs(a[0] - x0), abs(a[0] - x1)) <= FACE_TOL and min(abs(c[0] - x0), abs(c[0] - x1)) <= FACE_TOL
            vert = abs(a[0] - c[0]) < 1
            spans_depth = vert and min(abs(a[1] - y0), abs(a[1] - y1)) <= FACE_TOL and min(abs(c[1] - y0), abs(c[1] - y1)) <= FACE_TOL
            both.append({"handle": h, "value_mm": round(m), "face_to_face": bool(spans_width or spans_depth)})
        elif fa or fc:
            one += 1
    # architectural wall lines (layer '1') that run THROUGH the column parallel to a side: the wall faces at the member
    walls = set()
    for (p, q) in ar_walls:
        if abs(p[0] - q[0]) < 1 and x0 - 1 < p[0] < x1 + 1 and min(p[1], q[1]) < y1 and max(p[1], q[1]) > y0:
            walls.add(("x", round(p[0] - x0)))
        if abs(p[1] - q[1]) < 1 and y0 - 1 < p[1] < y1 + 1 and min(p[0], q[0]) < x1 and max(p[0], q[0]) > x0:
            walls.add(("y", round(p[1] - y0)))
    return copies, both, one, sorted(walls)


def _pdf(pdf_path, st_msp):
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        return {"status": "NOT_RUN", "why": "PyMuPDF not installed"}
    import pymupdf
    doc = pymupdf.open(str(pdf_path))
    out = {"status": "RUN", "pages": len(doc), "scale": "1:100 (1 pt = 35.28 mm)", "storeys": {}}
    for s, (sheet, n, pg) in FRAME.items():
        cols = _col_outlines(st_msp, n)
        fills = []
        for d in doc[pg - 1].get_drawings():
            r = d["rect"]
            if d.get("fill") is None or not (3 < r.width < 40 and 3 < r.height < 40):
                continue
            X, Y = (r.x0 + r.width / 2) * PT_MM, -(r.y0 + r.height / 2) * PT_MM
            X, Y = -Y, X                                   # page rotation 270 -> drawing axes
            fills.append((X, Y, r.height * PT_MM, r.width * PT_MM))
        votes = collections.Counter((round((c[1] - X) / 20), round((c[2] - Y) / 20)) for X, Y, _, _ in fills for c in cols)
        (tx, ty), k = votes.most_common(1)[0]
        tx, ty = tx * 20, ty * 20
        rows = {}
        for h, cx, cy, w, dd in cols:
            near = sorted((abs(X + tx - cx) + abs(Y + ty - cy), fw, fh) for X, Y, fw, fh in fills
                          if abs(X + tx - cx) < 150 and abs(Y + ty - cy) < 150)
            rows[h] = None if not near else {"W_mm": round(near[0][1]), "D_mm": round(near[0][2]),
                                              "agrees_with_dxf_within_10mm": abs(near[0][1] - w) <= 10 and abs(near[0][2] - dd) <= 10}
        unmatched = [(round(fw), round(fh)) for X, Y, fw, fh in fills
                     if min(abs(X + tx - c[1]) + abs(Y + ty - c[2]) for c in cols) > 300]
        out["storeys"][s] = {"page": pg, "fills": len(fills), "registration_votes": k, "dxf_outlines": len(cols),
                             "rows": rows, "fills_not_on_a_dxf_column": sorted(unmatched),
                             "_t": (tx, ty), "_fills": fills}
    return out


def extract(st_path: Path, ar_path: Path, pdf_path: Path) -> dict:
    import ezdxf
    for k, p in (("st", st_path), ("arch", ar_path), ("pdf", pdf_path)):
        if _sha(p) != SHA[k]:
            raise SystemExit(f"{p.name}: sha256 differs from the manifest copy")
    st = ezdxf.readfile(str(st_path)).modelspace()
    ar = ezdxf.readfile(str(ar_path)).modelspace()
    t217 = json.load(open(ROOT / "research/agents_t217/ALSENAN_SECTION_INPUT.json", encoding="utf-8"))
    sched = dict(t217["schedule"])
    inst = {i["fp_outline"]: i for i in t217["instances"]}
    conflict, unknown = _ledger()
    tr = _arch_translation(st, ar)
    ar_dims = []
    for d in ar.query("DIMENSION"):
        a, c = d.dxf.get("defpoint2"), d.dxf.get("defpoint3")
        if a is None or c is None:
            continue
        try:
            m = d.get_measurement()
        except Exception:
            continue
        ar_dims.append((d.dxf.handle, m, (a.x, a.y), (c.x, c.y)))
    ar_walls = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)) for e in ar.query('LINE[layer=="1"]')]
    pdf = _pdf(pdf_path, st)
    members = []
    for r in conflict:
        sheet, h = r["member"].split(":")
        storey = r["storey"]
        e = st.entitydb[h]
        b = _bb(e)
        neck = inst[r["fp_neck"]]
        sc = sched[r["mark"]]["bands"]
        fou = neck["storeys"]["FOUNDATION"]
        copies, dims_both, dims_one, walls = _arch_member(ar, ar_dims, ar_walls, e, tr[storey]["t_mm"])
        prow = pdf["storeys"][storey]["rows"].get(h) if pdf["status"] == "RUN" else None
        members.append({
            "member": r["member"], "storey": storey, "mark": r["mark"], "kind": r["kind"], "neck": r["fp_neck"],
            "drawn_mm": [round(b.size.x), round(b.size.y)],
            "schedule_band": BAND[storey], "schedule_cm": [sc[BAND[storey]]["W"], sc[BAND[storey]]["D"]],
            "schedule_handle": sched[r["mark"]]["handle"],
            "gr_band_cm": [sc["GR"]["W"], sc["GR"]["D"]] if sc.get("GR") else None,
            "foundation_cap_text_cm": [[t["W_cm"], t["D_cm"], t["handle"]] for t in fou["texts"]],
            "foundation_cap_dims_mm": [[d_["W_mm"], d_["D_mm"]] + d_["handles"] for d_ in fou["dims"]],
            "slab_plan_text_or_dim_at_member": len(neck["storeys"][storey]["texts"]) + len(neck["storeys"][storey]["dims"]),
            "pdf_plot_mm": None if prow is None else [prow["W_mm"], prow["D_mm"]],
            "pdf_agrees_with_dxf": None if prow is None else prow["agrees_with_dxf_within_10mm"],
            "arch_outline_copies": copies,
            "arch_dims_both_points_on_faces": dims_both, "arch_dims_one_point_on_a_face": dims_one,
            "arch_wall_lines_through_member_mm_from_face": walls,
        })
    # the five NOT_DRAWN upper lines: every sheet that could draw them, searched at the stack position
    absent = []
    for r in unknown:
        neck_h, storey = r["fp_neck"], r["storey"]
        sheet, n, pg = FRAME[storey]
        nb = _bb(st.entitydb[neck_h])
        x, y = nb.center.x - n * PITCH, nb.center.y
        res = {"line": r["member"], "mark": r["mark"], "storey": storey, "neck": neck_h,
               "route_g_m3": float(r["route_g_m3"]), "searched": {}}
        def st_near(frame_n, rad):
            xx = nb.center.x - frame_n * PITCH
            hits = []
            for e in st:
                if e.dxftype() not in ("LWPOLYLINE", "HATCH", "TEXT", "MTEXT", "INSERT", "LINE"):
                    continue
                if not (e.dxf.layer.startswith("S-COL") or e.dxftype() in ("TEXT", "MTEXT")):
                    continue
                bb = _bb(e)
                if bb and max(bb.size.x, bb.size.y) < 3000 and abs(bb.center.x - xx) < rad and abs(bb.center.y - y) < rad:
                    hits.append({"type": e.dxftype(), "layer": e.dxf.layer, "handle": e.dxf.handle,
                                 "pattern": e.dxf.pattern_name if e.dxftype() == "HATCH" else None})
            return hits
        own = st_near(n, 600)
        res["searched"]["ST dxf " + sheet + " (column layers + texts, 0.6 m)"] = "FOUND" if any(
            h["layer"].startswith("S-COL") for h in own) else "ABSENT"
        below = FRAME.get({"1F": "GF", "2F": "1F"}[storey])
        bl = [e for e in _col_outlines(st, below[1]) if abs(e[1] - (nb.center.x - below[1] * PITCH)) < 600 and abs(e[2] - y) < 600]
        res["column_below_on_" + below[0]] = [e[0] for e in bl]
        res["start_symbol_on_" + below[0]] = any(
            hh["type"] == "HATCH" and hh["layer"] == "S-COL.HAT" and hh["pattern"] != "SOLID" for hh in st_near(below[1], 600))
        res["texts_within_0.6m_on_" + sheet] = sum(1 for hh in own if hh["type"] in ("TEXT", "MTEXT"))
        t = tr[storey]["t_mm"]
        ac = [e for e in ar.query('LWPOLYLINE[layer=="S-COL.BON"]')
              if (lambda bb: bb and abs(bb.center.x - (x - t[0])) < 600 and abs(bb.center.y - (y - t[1])) < 600)(_bb(e))]
        res["searched"]["architectural dxf " + storey + " plan (S-COL.BON, 0.6 m)"] = "FOUND" if ac else "ABSENT"
        if pdf["status"] == "RUN":
            ps = pdf["storeys"][storey]
            tx, ty = ps["_t"]
            near = [f for f in ps["_fills"] if abs(f[0] + tx - x) < 600 and abs(f[1] + ty - y) < 600]
            res["searched"][f"ST pdf p.{pg} (filled outlines, 0.6 m)"] = "FOUND" if near else "ABSENT"
        else:
            res["searched"][f"ST pdf p.{pg}"] = "NOT_RUN"
        absent.append(res)
    # the schedule's upper bands are a type table: per type, how many members each storey plan draws
    drawn_by_type = collections.defaultdict(lambda: collections.Counter())
    for i in t217["instances"]:
        for s in ("GF", "1F", "2F"):
            if i["storeys"][s]["drawn"]:
                drawn_by_type[i["mark"]][s] += 1
    type_table = {m: {"band_2ND_printed": sched[m]["bands"].get("2ND") is not None,
                      "band_1ST_printed": sched[m]["bands"].get("1ST") is not None,
                      "drawn_1F": drawn_by_type[m]["1F"], "drawn_2F": drawn_by_type[m]["2F"]}
                  for m in sorted(sched) if m != "CN"}
    if pdf["status"] == "RUN":
        for s in pdf["storeys"].values():
            s.pop("_t"), s.pop("_fills")
            s["dxf_outlines_with_an_agreeing_plot_fill"] = sum(1 for v in s["rows"].values() if v and v["agrees_with_dxf_within_10mm"])
            s["dxf_outlines_without_a_plot_fill"] = sorted(h for h, v in s["rows"].items() if v is None)
    return {
        "schema": "T256_COLUMN_EVIDENCE_INPUT_V1",
        "sources": {"ST7757 dxf.dxf": SHA["st"], "P7757_DXF_COMPRESSED.zip -> P7757.dxf": SHA["arch"],
                    "ST7757.pdf": SHA["pdf"]},
        "arch_vs_structural_column_layer": {s: {k: v for k, v in d.items() if k != "t_mm"} for s, d in tr.items()},
        "arch_column_layers": sorted({e.dxf.layer for e in ar.query("LWPOLYLINE HATCH") if "COL" in e.dxf.layer.upper()}),
        "arch_column_outlines_total": len(list(ar.query('LWPOLYLINE[layer=="S-COL.BON"]'))),
        "pdf": pdf, "members": members, "not_drawn_lines": absent, "schedule_type_table": type_table,
    }


def main(argv):
    if len(argv) < 4:
        raise SystemExit(__doc__)
    out = extract(Path(argv[1]), Path(argv[2]), Path(argv[3]))
    txt = json.dumps(out, indent=1, sort_keys=True, default=list)
    if "--write" in argv:
        (HERE / "ALSENAN_T256_EVIDENCE.json").write_text(txt + "\n", encoding="utf-8")
    else:
        print(txt)


if __name__ == "__main__":
    main(sys.argv)
