"""T-287 Alsenan run: the sheet search behind the three RFI gaps G1 (CB5 column / neck boundary), G2 (ST-01 winder turn
MS1-T and the flight waists) and G3 (tower dome, rings, drums). Research only; nothing released, no quantity changed.

Reads the private copies (Drive "Alsenan chalet project": 'ST7757 dxf.dxf' sha256 9f9d1179..., 'P7757_DXF_COMPRESSED.zip'
-> P7757.dxf sha256 ab54dd55...) and writes ALSENAN_SEARCH_T287.json: per question and sheet the number of entities
searched, the printed evidence (handle, kind, printed value), the verdict FOUND / MISSING; no coordinates, no drawing
text other than the pattern-matched values. The PDF-only pages (ST p.8 raster notes, p.13 - p.16 details: no paper space in
the DXF, T-195) are recorded as a hand reading in MANUAL_PAGES (this run, ST7757.pdf sha256 74da1523...).

    python3 -I research/agents_t287/t287_alsenan.py <ST7757 dxf> <P7757 dxf> [--write]
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("t287_search", HERE / "t287_search.py")
S = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t287_search", S)
_s.loader.exec_module(S)

ST_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
PITCH = 38724.406108773          # ST frame pitch (mm), T-217 (merged): frame index = round((FP_CENTRE_X - x) / PITCH)
FP_CENTRE_X = 135500.0
FRAME_PAGE = {-1: 1, 0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7}     # T-195 register: CAP p.1, FP p.2, GBP p.3, GFRS p.4, ...
PLAN = 2                         # the common plan frame = ST p.4 (GFRS), as T-119 / T-248
ST_SHEETS = tuple(f"ST p.{p}" for p in FRAME_PAGE.values())
ARCH_PLANS = ("ARCH GF plan", "ARCH 1F plan", "ARCH 2F plan")
EXTENT_MARGIN = 8000.0           # mm around the p.4 column field: an architectural entity inside it belongs to that plan

# Facts this search uses, each merged and Checker-verified (cited, not re-derived):
EXTERIOR_LEVELS = (0.15,)        # court finished ground +0.15 (T-200 MERGED, DRAWING-CONFIRMED, P7757 x6 + ST SH08 x6)
BUILD_UP = 0.05                  # FFL - ground-slab top (T-214 MERGED b29060c2; T-248 datums +0.25 / +0.95)
NEAR_THICK = 3.0                 # m: context radius for the nearest thickness print beside a flight that prints none
BEAM_EDGE_LAYER = "1"            # ST p.3 ground-beam edge lines (T-242 / T-248 read the bands from this layer)
PROBE = 0.60                     # m beyond the column outline: a point inside each space that touches the column
SPACE_RADIUS = 5.0               # m: a same-space mark farther than this is not read
ADJ_RADIUS = 3.5                 # m: a level mark beyond this is not read as the bay beside the column

FLIGHTS = {   # element -> (sheet, anchor handles): the drawn riser / edge lines that bound it (T-184 / T-258 handles)
    "MS1-L": ("ST p.4", ("45A", "25E")),
    "MS1-T": ("ST p.4", ("2F6", "2F4", "2F5", "2F3", "25E")),
    "MS1-LD": ("ST p.4", ("25B", "2F3")),
    "MS1-U": ("ST p.4", ("25B", "459")),
    "MS2-L": ("ST p.5", ("646", "632")),
    "MS2-TR": ("ST p.5", ("5E2", "633")),
    "MS2-LD": ("ST p.5", ("632", "62F", "5E2")),
    "MS2-U": ("ST p.5", ("62F", "644")),
    "D1": ("ST p.3", ("1C4", "1C7")),
    "E1": ("ST p.3", ("18A", "179")),
    "RS-C": ("ST p.4", ("2E0", "2EA", "2DD", "2DE")),
    "RS-S": ("ST p.4", ("2BA", "2C4")),
    "RS-LD": ("ST p.4", ("2C4", "2C8")),
    "RS-A": ("ST p.4", ("2C8", "315")),
}
WAIST_MARGIN = 0.15              # m: a thickness tag printed on the flight or touching its edge
DOME3 = ("ARCH 2F plan", ("1300",))          # the hidden dome circle over the 2F maid room (T-185), r 2.205
TERRACE_DOMES = ("ST p.5", ("5FE", "5FF", "649"))   # DOME-A ring arcs, DOME-B circle (T-185 / T-258)

# Hand reading of the pages the DXF does not carry (ST7757.pdf, rendered and read this run; vector text, not extractable).
MANUAL_PAGES = {
    "ST p.8 (RECOMMENDATIONS, raster)": {
        "G1": "no level, neck or ground-slab note; note 12: the contractor confirms the founding level from the "
              "architectural and structural drawings with the supervising engineer",
        "G2": "note 18: ordinary roof slabs 16 cm unless stated otherwise (a slab rule; no stair, waist or winder note)",
        "G3": "note 4: every opening on the architectural drawings must exist on the structural drawings, refer to the "
              "structural engineer for any detail; no dome, ring or drum note"},
    "ST p.13 (DETAILS: isolated footing, lintel, ground beams)": {
        "G1": "exterior ground beam: top = 'Ground Floor slab level', outside 'Outer normal ground level', depth "
              "'FOLLOW ARCH'; no detail of a column between two different floor levels; no neck-end level",
        "G2": "nothing on stairs", "G3": "nothing on domes"},
    "ST p.14 (DETAILS: lift pit, boundary wall, parapets)": {
        "G1": "nothing on the CB5 line or a two-level ground slab", "G2": "nothing on stairs",
        "G3": "nothing on domes"},
    "ST p.15 (DETAILS: twisted column, slab on beams, planted column)": {
        "G1": "nothing on a neck end", "G2": "nothing on stairs", "G3": "nothing on domes"},
    "ST p.16 (DETAILS: stair beam, typical stair steel layout, opening in beam, ribs)": {
        "G1": "nothing",
        "G2": "TYPICAL STEEL LAYOUT - STAIR SECTION (N.I.S): two straight flights and a landing (S.S.L +2.00), waist "
              "marked 'THICK.' with no value; no winder, no turn, no curved flight; typical, not tied to ST-01 / ST-02 "
              "(T-184: no printed level fits any Alsenan stair)",
        "G3": "nothing on domes"},
    "ST p.7 (DETAIL OF DOME, N.I.S)": {
        "G3": "one generic detail: chord 442, rise 190, shell 10, d12 / 15 cm both faces, ring 20 wide, ring depth 'AS "
              "PER ARCH', no title naming the dome it serves, no drum"},
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_st(path: Path):
    import ezdxf
    msp = ezdxf.readfile(str(path)).modelspace()

    def sheet_of(box):
        k = round((FP_CENTRE_X - (box[0] + box[2]) / 2) / PITCH)
        if k not in FRAME_PAGE:
            return None
        return f"ST p.{FRAME_PAGE[k]}", ((k - PLAN) * PITCH, 0.0)
    return S._flatten(msp, sheet_of, 1000.0), msp


def level_marks(ents, sheet, layer=None):
    return [(e.text.strip(), (e.box[0] + e.box[2]) / 2 * 1000, (e.box[1] + e.box[3]) / 2 * 1000) for e in ents
            if e.sheet == sheet and e.kind == "TEXT" and S.LEVEL_RE.match(e.text.strip())
            and (layer is None or e.layer == layer)]


def read_arch(path: Path, st_ents):
    """Register the architectural plans to the plan frame by level marks (runtime): GF on ST p.3, 2F on ST p.6; the 1F
    plan at the equal pitch between them, accepted only if the 1F '+5.50' marks then fall inside the building extent."""
    import ezdxf
    msp = ezdxf.readfile(str(path)).modelspace()
    raw = S._flatten(msp, lambda b: ("ARCH raw", (0.0, 0.0)), 1000.0)
    am = level_marks(raw, "ARCH raw")
    gf, n_gf, _ = S.register_by_marks(level_marks(st_ents, "ST p.3", "LEVEL"), am, min_votes=10)
    f2, n_2f, _ = S.register_by_marks(level_marks(st_ents, "ST p.6", "LEVEL"), am, min_votes=2)
    if gf[1] != f2[1]:
        raise ValueError("GF and 2F registrations disagree in y: the plans are not on one row")
    cols = [e for e in st_ents if e.sheet == "ST p.4" and e.layer == "S-COL.BON"]
    ext = (min(e.box[0] for e in cols) * 1000 - EXTENT_MARGIN, min(e.box[1] for e in cols) * 1000 - EXTENT_MARGIN,
           max(e.box[2] for e in cols) * 1000 + EXTENT_MARGIN, max(e.box[3] for e in cols) * 1000 + EXTENT_MARGIN)
    mid = ((ext[0] + ext[2]) / 2, (ext[1] + ext[3]) / 2)
    # plan coordinate = arch + offset (the ST marks are already in the plan frame, read_st)
    off = {"ARCH GF plan": gf, "ARCH 2F plan": f2}
    off["ARCH 1F plan"] = ((off["ARCH GF plan"][0] + off["ARCH 2F plan"][0]) / 2, gf[1])

    def sheet_of(box):
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        inside = [(abs(cx + off[n][0] - mid[0]), n) for n in ARCH_PLANS
                  if ext[0] <= cx + off[n][0] <= ext[2] and ext[1] <= cy + off[n][1] <= ext[3]]
        if not inside:
            return "ARCH other", (0.0, 0.0)
        name = min(inside)[1]          # extents of neighbouring plans overlap by the margin: the nearer field wins
        return name, off[name]
    ents = S._flatten(msp, sheet_of, 1000.0)
    check_1f = sum(1 for t, x, y in level_marks(ents, "ARCH 1F plan") if t == "+5.50")
    if check_1f == 0:
        raise ValueError("1F plan registration not confirmed: no '+5.50' mark inside the building extent")
    reg = {"GF": {"votes": n_gf, "basis": "level marks ST p.3 = arch GF"},
           "2F": {"votes": n_2f, "basis": "level marks ST p.6 = arch 2F, same row as GF"},
           "1F": {"plus_5_50_marks_inside": check_1f, "basis": "equal pitch between GF and 2F, checked"}}
    return ents, reg


def questions():
    Q = S.Question
    out = [
        Q("G1-a", "a structural level, neck end or section cut printed at the two CB5-line GF columns",
          (("ST p.4", "35F"), ("ST p.4", "365")), 1.5, (S.STRUCT_LEVEL_RE,),
          sheets=ST_SHEETS[:6] + ("ARCH GF plan",), context=(S.LEVEL_RE,)),
        Q("G2-a", "the ST-01 winder turn MS1-T: an outline, level, dimension or soffit of the turn",
          tuple(("ST p.4", h) for h in FLIGHTS["MS1-T"][1]), 0.10, (S.STAIR_SHAPE_RE, S.LEVEL_RE),
          sheets=("ST p.3", "ST p.4", "ST p.5", "ARCH GF plan", "ARCH 1F plan"), dims_settle=True,
          context=(S.THICK_RE,)),
        Q("G2-c", "the ST-01 1F turn riser MS2-TR between the two half landings: a level or dimension",
          tuple(("ST p.5", h) for h in FLIGHTS["MS2-TR"][1]), 0.10, (S.STAIR_SHAPE_RE, S.LEVEL_RE),
          sheets=("ST p.4", "ST p.5", "ST p.6", "ARCH 1F plan", "ARCH 2F plan"), dims_settle=True,
          context=(S.THICK_RE,)),
        Q("G3-a", "a structural opening, ring, drum or dome at the tower dome over the 2F maid room",
          tuple((DOME3[0], h) for h in DOME3[1]), 0.30, (S.DOME_RE, S.THICK_RE), sheets=("ST p.5", "ST p.6", "ARCH 2F plan"),
          shapes_settle=("CIRCLE", "ARC"), context=(S.LEVEL_RE,)),
        Q("G3-b", "drum material / thickness at the two terrace domes (+9.70 -> +11.00)",
          tuple(("ST p.5", h) for h in TERRACE_DOMES[1]), 0.50, (S.THICK_RE, re.compile(r"DRUM", re.I)),
          sheets=("ST p.5", "ST p.6", "ARCH 1F plan", "ARCH 2F plan"), context=(S.DOME_RE,)),
    ]
    for el, (sheet, hs) in FLIGHTS.items():
        out.append(Q(f"G2-w:{el}", f"waist / slab thickness printed on {el}", tuple((sheet, h) for h in hs),
                     WAIST_MARGIN, (S.THICK_RE,), sheets=(sheet,), context=(S.STAIR_SHAPE_RE,)))
    return out


def box_gap(a, b):
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def _marks(ents, sheet):
    return [(e.handle, float(e.text.strip().replace("%%p", "").replace("%%P", "").replace("±", "").replace(" ", "")),
             ((e.box[0] + e.box[2]) / 2, (e.box[1] + e.box[3]) / 2)) for e in ents
            if e.sheet == sheet and e.kind == "TEXT" and S.LEVEL_RE.match(e.text.strip())]


def _probes(c, d=PROBE):
    """Eight probe points 0.60 m beyond the column outline: the four faces and the four corners."""
    x0, y0, x1, y1 = c.box
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    return [("W", (x0 - d, ym)), ("E", (x1 + d, ym)), ("S", (xm, y0 - d)), ("N", (xm, y1 + d)),
            ("SW", (x0 - d, y0 - d)), ("SE", (x1 + d, y0 - d)), ("NW", (x0 - d, y1 + d)), ("NE", (x1 + d, y1 + d))]


def g1_adjoining(ents):
    """The finished levels beside each CB5-line column, read two ways:
    (1) bay reading on ST p.3: marks reached from the column centre across its own ground-beam band edge only;
    (2) space reading on the architectural GF plan: marks in the same floor space as a probe beside the column (no
        drawn line between them). Settlement uses the space reading; the bay reading is the cross-check."""
    cols = {e.handle: e for e in ents if e.sheet == "ST p.4" and e.handle in ("35F", "365")}
    edges = [tuple(e.pts) for e in ents if e.sheet == "ST p.3" and e.kind == "LINE" and e.layer == BEAM_EDGE_LAYER]
    drawn = S.segments(ents, "ARCH GF plan")
    out = {}
    for h, c in sorted(cols.items()):
        centre = ((c.box[0] + c.box[2]) / 2, (c.box[1] + c.box[3]) / 2)
        bay = S.adjoining_levels(centre, _marks(ents, "ST p.3"), edges, ADJ_RADIUS)
        space = S.same_space_levels(_probes(c), _marks(ents, "ARCH GF plan"), drawn, SPACE_RADIUS)
        space_adj = sorted({(m, v) for m, v, _ in space})
        out[h] = {"bay_reading_ST_p3": {"adjoining": bay,
                                        "settled": S.settle_column_base(bay, EXTERIOR_LEVELS, BUILD_UP)},
                  "space_reading_ARCH_GF": {"by_probe": sorted(space, key=lambda r: (r[2], r[0])),
                                            "settled": S.settle_column_base([(m, v, 0, 0) for m, v in space_adj],
                                                                            EXTERIOR_LEVELS, BUILD_UP)}}
    return out


def build(st_path: Path, arch_path: Path) -> dict:
    assert _sha(st_path) == ST_SHA, "not the Drive 'ST7757 dxf.dxf' of the manifest"
    assert _sha(arch_path) == ARCH_SHA, "not the Drive P7757.dxf of the manifest"
    st, _ = read_st(st_path)
    ar, reg = read_arch(arch_path, st)
    ents = st + ar
    plan_sheets = ST_SHEETS + ARCH_PLANS
    res = {"schema": S.SCHEMA, "inputs": {"ST7757 dxf.dxf": f"sha256 {ST_SHA[:16]}...",
                                         "P7757.dxf": f"sha256 {ARCH_SHA[:16]}..."},
           "entities_read": {s: sum(1 for e in ents if e.sheet == s) for s in plan_sheets + ("ARCH other",)},
           "arch_registration": reg, "questions": {}}
    for q in questions():
        fs = S.search(ents, q, plan_sheets)
        v = S.verdict(fs)
        v["asks"] = q.asks
        v["context"] = [(f.sheet,) + c for f in fs for c in f.context]
        res["questions"][q.qid] = v
    by_h = {(e.sheet, e.handle): e for e in ents}
    for el, (sheet, hs) in FLIGHTS.items():
        v = res["questions"][f"G2-w:{el}"]
        if v["verdict"] == "MISSING":     # context only: the nearest thickness print on the same sheet (never applied)
            box = S.region(by_h, tuple((sheet, h) for h in hs))
            near = sorted((round(box_gap(box, e.box), 3), e.handle, e.text) for e in ents
                          if e.sheet == sheet and S._matches(e, (S.THICK_RE,)) and box_gap(box, e.box) <= NEAR_THICK)
            v["nearest_thickness_print_within_3m"] = near
    res["g1_adjoining"] = g1_adjoining(ents)
    allsheets = plan_sheets + ("ARCH other",)
    res["global"] = {
        "structural_level_or_neck_words": S.global_hits(ents, (S.STRUCT_LEVEL_RE,), allsheets),
        "thickness_or_waist": S.global_hits(ents, (S.THICK_RE, S.THICK_WORD_RE), allsheets),
        "winder_turn_landing_words": S.global_hits(ents, (re.compile(r"WINDER|TURN|SOFFIT", re.I),), allsheets),
        "dome_ring_drum_words": S.global_hits(ents, (re.compile(r"DOME|\bRING\b|DRUM|قب[ةه]", re.I),), allsheets),
    }
    res["manual_pages"] = MANUAL_PAGES
    return res


def main(argv):
    st, ar = Path(argv[1]), Path(argv[2])
    out = build(st, ar)
    js = json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if "--write" in argv:
        (HERE / "ALSENAN_SEARCH_T287.json").write_text(js, encoding="utf-8")
    print(js[:4000])


if __name__ == "__main__":
    main(sys.argv)
