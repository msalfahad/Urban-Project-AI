"""T-581: LINTEL MASONRY-OPENING WIDTH BASIS census (research rule proposal R-T581-1; research only: nothing in engine/
or tools/ imports it; no candidate line moves; V2.9 + route G and V3.0.58 untouched).

Physical element (ERS s.2.1). A precast lintel spans the MASONRY OPENING: the gap between the two drawn wall ends (the
wall-face lines stop at the jambs); the door frame sits INSIDE that gap. Lintel = shortest stock length >= masonry
opening + 2 x 0.15 m bearing (owner lintel rule 2026-11-02, UPC-LINTEL-001; arithmetic in R-T571-1 / company_rulebook_v1).
A door block (symbol) carries three different widths and they must not be confused:
  - block OVERALL width: outer edge to outer edge of the two drawn frame jambs (the symbol's footprint);
  - FRAME-CLEAR width: inner edge to inner edge of the frame jambs (the leaf / threshold line);
  - MASONRY OPENING: the gap between the two wall-face line ends AT THE INSERT, read on each face.
The symbol is usually drawn with its outer edges on the wall ends (overall = masonry), but not always: a block shifted or
overlapping the masonry leaves the wall ends elsewhere. Only the wall ends define the opening the lintel spans.

R-T581-1 (every villa; scope: the width a lintel / masonry deduction takes at an opening drawn with a door-frame block;
provenance: owner lintel rule 2026-11-02, Q-32 A (printed over drawn), Q-04 (an owner minimum is a separate view, never a
measured width), R-T571-1, ERS s.3 (a symbol is not the element)):
  (1) basis: the masonry opening = gap between the two wall-face line ends on the same face, read on BOTH faces; one basis
      for every opening of a census. A census row whose stated basis is frame-clear, block overall or leaf radius is
      refused, and a census mixing bases is refused;
  (2) the two faces agree within 5 mm -> the width (DRAWING-CONFIRMED); they disagree, or a face has no wall end within
      reach of the insert -> UNRESOLVED by name (never the block width, never a majority, never 0);
  (3) a printed dimension spanning the jambs governs the drawn gap (Q-32 A); none is used here unless supplied;
  (4) the block overall and frame-clear widths are listed BESIDE for every insert; they never become the width.
Nothing here names a client, a sheet or a coordinate; DXF handles and block names only.
"""
from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
T571 = ROOT / "research" / "agents_t571"
if str(T571) not in sys.path:
    sys.path.insert(0, str(T571))

import t571_lintel_count as L  # noqa: E402

RULE_ID = "R-T581-1"
FACE_TOL_MM = 5.0
REACH_MM = 800.0          # a wall end is looked for at most this far outside the block footprint
ACROSS_TOL_MM = 25.0      # a wall-face line lies on the block's face line (y = 0 or y = t) within this
MASONRY = "MASONRY_WALL_ENDS"
REFUSED_BASES = ("FRAME_CLEAR", "BLOCK_OVERALL", "LEAF_RADIUS")
CONFIRMED, UNRESOLVED = "DRAWING-CONFIRMED", "UNRESOLVED"


class BasisError(ValueError):
    pass


# ------------------------------------------------------------------------------------------- block frame (symbol)
def block_frame(lines):
    """lines: [((x0, y0), (x1, y1))] of a door block in block units (mm). The frame jambs are the lines across the wall
    (x constant) spanning the full wall band [0, t]; the leaf lines start at y = t and run away from it. Returns
    {'overall_mm', 'frame_clear_mm', 't_mm', 'x0', 'x1'} or None when the block has no end frames."""
    vert = [(a, b) for a, b in lines if abs(a[0] - b[0]) < 1e-6]
    if not vert:
        return None
    ys = [min(a[1], b[1]) for a, b in vert] + [max(a[1], b[1]) for a, b in vert]
    lo = min(ys)
    span = [(a[0], min(a[1], b[1]), max(a[1], b[1])) for a, b in vert]
    t = max(hi for x, y0, hi in span if abs(y0 - lo) < 1e-6)
    xs = sorted({round(x, 6) for x, y0, hi in span if abs(y0 - lo) < 1e-6 and abs(hi - t) < 1e-6})
    if len(xs) < 4 or t <= 0:
        return None
    return {"overall_mm": xs[-1] - xs[0], "frame_clear_mm": xs[-2] - xs[1], "t_mm": t - lo, "x0": xs[0],
            "x1": xs[-1], "y0": lo}


# ------------------------------------------------------------------------------------------- wall ends at an insert
def wall_ends(local_segments, frame):
    """local_segments: [((x0, y0), (x1, y1), tag)] of the WALL-FACE layer already in the insert's block coordinates.
    For each face (y = y0 and y = y0 + t) the last wall-face line end left of the block centre and the first one right
    of it. Returns {'faces': {face: {'left', 'right', 'gap_mm', 'tags'}}, 'gap_mm', 'state', 'why'}."""
    x0, x1, y0, t = frame["x0"], frame["x1"], frame["y0"], frame["t_mm"]
    mid = (x0 + x1) / 2.0
    faces = OrderedDict()
    for name, fy in (("face_a", y0), ("face_b", y0 + t)):
        left = right = None
        for a, b, tag in local_segments:
            if abs(a[1] - b[1]) > 2.0 or abs((a[1] + b[1]) / 2.0 - fy) > ACROSS_TOL_MM:
                continue
            lo, hi = sorted((a[0], b[0]))
            if hi < x0 - REACH_MM or lo > x1 + REACH_MM:
                continue
            if hi <= mid and (left is None or hi > left[0]):
                left = (hi, tag)
            if lo >= mid and (right is None or lo < right[0]):
                right = (lo, tag)
            if lo < mid < hi:   # a wall-face line runs through the opening: no opening on this face
                left = right = ("THROUGH", tag)
                break
        if left and right and left[0] != "THROUGH":
            faces[name] = {"left": round(left[0], 1), "right": round(right[0], 1),
                           "gap_mm": round(right[0] - left[0], 1), "tags": [left[1], right[1]]}
        else:
            faces[name] = {"left": None, "right": None, "gap_mm": None,
                           "tags": [left[1]] if left and left[0] == "THROUGH" else []}
    gaps = [f["gap_mm"] for f in faces.values()]
    if any(g is None for g in gaps):
        return {"faces": faces, "gap_mm": None, "state": UNRESOLVED,
                "why": "a face has no wall end on each side within reach (or a face line runs through): never the "
                       "block width"}
    if abs(gaps[0] - gaps[1]) > FACE_TOL_MM:
        return {"faces": faces, "gap_mm": None, "state": UNRESOLVED,
                "why": f"faces disagree ({gaps[0]} vs {gaps[1]} mm): which face the lintel spans is not established"}
    return {"faces": faces, "gap_mm": round((gaps[0] + gaps[1]) / 2.0, 1), "state": CONFIRMED, "why": ""}


def classify(frame, ends):
    """where the wall ends sit relative to the symbol: AT_BLOCK_EDGES (masonry = overall), AT_FRAME_LINE (masonry =
    frame clear), SHIFTED (neither: the block overlaps the masonry), or UNRESOLVED."""
    if ends["state"] != CONFIRMED:
        return UNRESOLVED
    fa = ends["faces"]["face_a"]
    edge = abs(fa["left"] - frame["x0"]) <= FACE_TOL_MM and abs(fa["right"] - frame["x1"]) <= FACE_TOL_MM
    if edge:
        return "AT_BLOCK_EDGES"
    inner_l, inner_r = frame["x0"] + (frame["overall_mm"] - frame["frame_clear_mm"]) / 2.0, \
        frame["x1"] - (frame["overall_mm"] - frame["frame_clear_mm"]) / 2.0
    if abs(fa["left"] - inner_l) <= FACE_TOL_MM and abs(fa["right"] - inner_r) <= FACE_TOL_MM:
        return "AT_FRAME_LINE"
    return "SHIFTED"


# ------------------------------------------------------------------------------------------- DXF reader (ezdxf)
def measure_dxf(path, wall_layer, frame_line_layer=None, names=None):
    """every INSERT whose block has end frames (block_frame not None), optionally only blocks in `names`. Units: block
    and model space in mm (checked: the frame overall must lie in 500 .. 3000 mm, else refused)."""
    import ezdxf
    from ezdxf.math import Vec3
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    def lyr(e):
        try:
            return e.dxf.layer
        except Exception:  # entities without a layer attribute (RTEXT)
            return None
    segs = {wall_layer: [], frame_line_layer: []}
    for e in msp:
        lay = lyr(e)
        if lay not in segs:
            continue
        if e.dxftype() == "LINE":
            segs[lay].append((Vec3(e.dxf.start), Vec3(e.dxf.end), e.dxf.handle))
        elif e.dxftype() == "LWPOLYLINE":
            pts = [Vec3(p[0], p[1], 0) for p in e.get_points()]
            if e.closed:
                pts.append(pts[0])
            segs[lay] += [(a, b, e.dxf.handle) for a, b in zip(pts, pts[1:])]
    frames = {}
    out = []
    for ins in msp.query("INSERT"):
        n = ins.dxf.name
        if names is not None and n not in names:
            continue
        if n not in frames:
            bl = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)) for e in doc.blocks[n]
                  if e.dxftype() == "LINE"]
            frames[n] = block_frame(bl)
        fr = frames[n]
        if fr is None:
            continue
        if not 500.0 <= fr["overall_mm"] <= 3000.0:
            raise BasisError(f"{n}: frame overall {fr['overall_mm']} is not a door width in mm (units refused)")
        inv = ins.matrix44().copy()
        inv.inverse()

        def loc(lst):
            r = []
            for a, b, h in lst:
                pa, pb = inv.transform(a), inv.transform(b)
                r.append(((pa.x, pa.y), (pb.x, pb.y), h))
            return r
        ends = wall_ends(loc(segs[wall_layer]), fr)
        fl = None
        if frame_line_layer:
            mid = (fr["x0"] + fr["x1"]) / 2.0
            for a, b, h in loc(segs[frame_line_layer]):
                if abs(a[1] - b[1]) < 2.0 and abs(a[1] - fr["y0"]) < ACROSS_TOL_MM and min(a[0], b[0]) < mid < max(
                        a[0], b[0]):
                    fl = {"len_mm": round(abs(a[0] - b[0]), 1), "tag": h}
                    break
        out.append({"block": n, "handle": ins.dxf.handle, "mirrored": ins.dxf.xscale < 0,
                    "rotation_deg": round(ins.dxf.rotation, 3), "overall_mm": fr["overall_mm"],
                    "frame_clear_mm": fr["frame_clear_mm"], "wall_t_mm": fr["t_mm"], "frame_line": fl,
                    "wall_ends": ends, "ends_sit": classify(fr, ends)})
    return out


# ------------------------------------------------------------------------------------------- census basis check
def masonry_width(rec):
    """one census opening -> width in m on the masonry basis (R-T581-1 (1)-(2))."""
    basis = rec.get("basis")
    if basis in REFUSED_BASES:
        raise BasisError(f"{rec.get('id')}: basis {basis} is not the masonry opening (R-T581-1 (1)); refused")
    if basis != MASONRY:
        raise BasisError(f"{rec.get('id')}: basis {basis!r} unknown")
    if rec.get("state") != CONFIRMED or rec.get("gap_mm") is None:
        return None
    g = rec["gap_mm"]
    if not 300.0 <= g <= 6000.0:
        raise BasisError(f"{rec.get('id')}: gap {g} is not mm of a door opening (units refused)")
    return round(g / 1000.0, 3)


def check_single_basis(records):
    bases = {r.get("basis") for r in records}
    if len(bases) != 1:
        raise BasisError(f"mixed width basis in one census {sorted(map(str, bases))}: refused (R-T581-1 (1))")
    return bases.pop()


def restate(census, measured, storeys, bearing_m=None, bearing_source=None):
    """census: T-571 engine records; measured: {opening id: {'basis', 'gap_mm', 'state'}} for the frame-block openings.
    Every measured opening takes its masonry width; an UNRESOLVED one is HELD by name (width None, never 0). Returns the
    T-571 count table on that one basis, the per-opening change list and the table difference (new minus old)."""
    check_single_basis(list(measured.values()))
    new, changes = [], []
    for r in census:
        m = measured.get(r["id"])
        if m is None:
            new.append(r)
            continue
        w = masonry_width(dict(m, id=r["id"]))
        old_p = L.piece(r.get("width_m"), bearing_m, bearing_source).get("piece_m") if r.get("width_m") else None
        new_p = L.piece(w, bearing_m, bearing_source).get("piece_m") if w else None
        if w is None or r.get("width_m") is None or abs(w - r["width_m"]) > 0.005 or old_p != new_p:
            changes.append({"id": r["id"], "storey": r["storey"], "w_old": r.get("width_m"), "w_new": w,
                            "piece_old": old_p, "piece_new": new_p, "state": m["state"]})
        new.append(dict(r, width_m=w))
    a = L.count_table([dict(r, key=None) for r in census], storeys, bearing_m, bearing_source)
    b = L.count_table([dict(r, key=None) for r in new], storeys, bearing_m, bearing_source)
    diff = OrderedDict((Lg, OrderedDict((s, b["at_most"][Lg][s] - a["at_most"][Lg][s]) for s in storeys))
                       for Lg in L.STOCK)
    lm = round(sum(b["lm_beside_at_most"].values()) - sum(a["lm_beside_at_most"].values()), 6)
    return {"before": L._strip(a), "after": L._strip(b), "diff_nr": diff, "diff_lm": lm, "changes": changes}


# ------------------------------------------------------------------------------------------- training villa
# insert handle -> census opening id. Sources: research/agents_t568/t568_alsenan.py DRAWN_LEAVES (GF external, 1F);
# research/alsenan_lintels_s8_6/01_OPENING_CENSUS.csv DOOR_BLOCKS with its side rooms against the T-198 census sides
# (GF internal, 2F). D-GF-11 / D-GF-12 (two identical D315 W.C. doors off one lobby) are a pair: both inserts read 800 /
# 800, so either assignment gives the same width and piece.
INSERT_TO_OPENING = OrderedDict([
    ("15E", "D-GF-01"), ("1EF", "D-GF-02"), ("1B5", "D-GF-03"), ("19E", "D-GF-04"), ("192", "D-GF-05"),
    ("33E", "D-GF-06"), ("281", "D-GF-07"), ("2C7", "D-GF-08"), ("3FF", "D-GF-09"), ("339", "D-GF-10"),
    ("321", "D-GF-11"), ("320", "D-GF-12"), ("2F2", "D-GF-13"),
    ("C2B", "D-1F-01"), ("C31", "D-1F-02"), ("C32", "D-1F-03"), ("C2E", "D-1F-04"), ("C1A", "D-1F-05"),
    ("11B4", "D-1F-06"), ("BEE", "D-1F-07"), ("C18", "D-1F-08"), ("BEF", "D-1F-09"), ("C12", "D-1F-10"),
    ("12BA", "D-2F-01"), ("12C2", "D-2F-02"), ("12BB", "D-2F-03"),
])
# frame-block inserts with no census opening (not in the lintel population), listed by name
OUTSIDE_CENSUS = {"2D8": "boundary (compound) wall door, S8.6 OP-GF-B01 SYMBOL_ONLY / SITE_BOUNDARY: the compound wall "
                         "is drawn on the site layer, not a building masonry wall; not in the T-198 census or the "
                         "T-453 lintel ledger"}
# jamb-only blocks (no frame: overall = frame clear), wall-face ends read on both faces this run along the block's jamb
# lines; listed for completeness, no frame basis question arises
JAMB_ONLY_READS = OrderedDict([
    ("A-GF-01", {"handle": "1F8", "block": "arch120", "face_a_gap_m": 1.000, "face_b_gap_m": 1.000}),
    ("A-1F-01", {"handle": "BEC", "block": "arch120", "face_a_gap_m": 1.000, "face_b_gap_m": 1.000}),
])
WALL_LAYER, FRAME_LINE_LAYER = "1", "5"
OUT = Path(__file__).resolve().parent / "out" / "T581_WIDTH_BASIS.json"


def census_basis_rows():
    """the T-198 census r3 width basis / source text for every frame-block opening (what census r3 used)."""
    import csv
    rows = {r["ID"]: r for r in csv.DictReader(L.CENSUS.open(encoding="utf-8"))}
    return {oid: {"census_w": float(rows[oid]["WIDTH_M"]), "census_basis": rows[oid]["WIDTH_BASIS"],
                  "census_source": rows[oid]["WIDTH_SOURCE"][:90]} for oid in INSERT_TO_OPENING.values()}


def build(dxf_path=None):
    """with the DXF (git-excluded private copy) the inserts are re-measured; without it the committed measurement is
    re-used (its numbers only), so the restatement and the tests run anywhere."""
    if dxf_path and Path(dxf_path).exists():
        inserts = measure_dxf(dxf_path, WALL_LAYER, FRAME_LINE_LAYER)
    else:
        inserts = json.loads(OUT.read_text(encoding="utf-8"))["inserts"]
    by_h = {i["handle"]: i for i in inserts}
    missing = [h for h in INSERT_TO_OPENING if h not in by_h]
    if missing:
        raise BasisError(f"inserts {missing} not found in the drawing (stale map)")
    unmapped = [h for h in by_h if h not in INSERT_TO_OPENING and h not in OUTSIDE_CENSUS]
    if unmapped:
        raise BasisError(f"frame-block inserts {unmapped} carry no census id and no outside-census cause")
    cb = census_basis_rows()
    table, measured = [], {}
    for h, oid in INSERT_TO_OPENING.items():
        i = by_h[h]
        e = i["wall_ends"]
        measured[oid] = {"basis": MASONRY, "gap_mm": e["gap_mm"], "state": e["state"]}
        w = masonry_width(dict(measured[oid], id=oid))
        c = cb[oid]
        if w is None:
            used = "UNRESOLVED (masonry not read)"
        elif abs(c["census_w"] - w) <= 0.005:
            used = "MASONRY (= wall-end gap)"
        elif abs(c["census_w"] * 1000 - i["frame_clear_mm"]) <= 5:
            used = "FRAME_CLEAR"
        elif abs(c["census_w"] * 1000 - i["overall_mm"]) <= 5:
            used = "BLOCK_OVERALL"
        else:
            used = "OTHER"
        table.append(OrderedDict(id=oid, handle=h, block=i["block"], overall_m=i["overall_mm"] / 1000,
                                 frame_clear_m=i["frame_clear_mm"] / 1000,
                                 frame_line_m=(i["frame_line"] or {}).get("len_mm", 0) / 1000 or None,
                                 face_a_gap_m=(e["faces"]["face_a"]["gap_mm"] or 0) / 1000 or None,
                                 face_b_gap_m=(e["faces"]["face_b"]["gap_mm"] or 0) / 1000 or None,
                                 wall_ends_sit=i["ends_sit"], masonry_m=w, census_w_m=c["census_w"],
                                 census_basis_used=used, census_basis_text=c["census_basis"],
                                 lintel_masonry=L.piece(w)["piece_m"] if w else None,
                                 lintel_frame_clear=L.piece(i["frame_clear_mm"] / 1000)["piece_m"],
                                 lintel_overall=L.piece(i["overall_mm"] / 1000)["piece_m"]))
    census = L.engine_records()
    storeys = ["GF", "1F", "2F", L.UNSPLIT]
    res = OrderedDict(rule=RULE_ID, t571_pins=L.PINS, inserts=inserts, openings=table,
                      outside_census=OUTSIDE_CENSUS, jamb_only_reads=JAMB_ONLY_READS)
    res["restated_owner_0.15"] = restate(census, measured, storeys)
    # BESIDE (refused as a basis): the same census if the frame-clear width were taken at every frame-block opening
    fc = {oid: {"basis": MASONRY, "gap_mm": by_h[h]["frame_clear_mm"], "state": CONFIRMED}
          for h, oid in INSERT_TO_OPENING.items()}
    res["beside_frame_clear_refused"] = {k: v for k, v in restate(census, fc, storeys).items()
                                         if k in ("diff_nr", "diff_lm", "changes")}
    ov = {oid: {"basis": MASONRY, "gap_mm": by_h[h]["overall_mm"], "state": CONFIRMED}
          for h, oid in INSERT_TO_OPENING.items()}
    res["beside_block_overall_refused"] = {k: v for k, v in restate(census, ov, storeys).items()
                                           if k in ("diff_nr", "diff_lm", "changes")}
    return res


if __name__ == "__main__":
    dxf = sys.argv[1] if len(sys.argv) > 1 else None
    r = build(dxf)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(L._keyfix(r), indent=1, ensure_ascii=False) + "\n")
    print(OUT)
