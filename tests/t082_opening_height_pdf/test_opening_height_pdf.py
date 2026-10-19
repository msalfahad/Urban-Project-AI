"""T-082: printed opening heights from VECTOR PDF elevations and sections (engine/source/opening_height_pdf.py, on top
of opening_area.py), against hand truth. Hand villa SV-T082 (not a client drawing), two storeys GF (0.00) and
1F (+4.00), plan in metres:

    South facade (wall along the plan x axis, y = 0):
        GF W1 centre x 3.00, 1.50 wide    GF D1 centre x 7.00, 1.20 wide (outdoor door, aluminium class)
        1F W2 centre x 3.00, 1.50 wide (over W1)    1F W3 centre x 9.00, 2.10 wide, arched head
    North facade (y = 10): GF W4 centre x 4.00, 0.80 wide; 1F W5 centre x 9.50, 1.00 wide
    Inside, wall y = 5: GF D2 centre x 5.00, 0.90 wide; GF D3 centre x 8.00, 1.00 wide (a space on both sides)

SOUTH ELEVATION sheet (vector PDF, SCALE 1:100 printed, centimetre prints): seen from the south, x_pt = 60 + K x,
y_pt = 100 + K z, K = 1 / (0.0254 / 72 x 100) = 28.3465 pt per metre; ticks 45 deg at every dimension end.
    W1 jambs z 0.90 - 2.40, printed "150" inside it (sill to head), "90" (floor to sill); width "150" over it
    W2 jambs z 5.00 - 6.20, printed "120" inside it
    D1 jambs z 0.00 - 2.40, printed "240" OUTSIDE it (extension lines from its right jamb); width "120" over it
    W3 jambs z 4.80 - 6.60 (springing), semicircular arch r 1.05 to the crown z 7.65 (drawn as Bezier curves),
       printed "180" (sill to springing) and "105" (springing to crown); width "210" over it
NORTH ELEVATION sheet: a SCAN (raster only) in the main case; in the mm variant a vector sheet at SCALE 1:50 printed in
    MILLIMETRES, seen from the north (MIRRORED): W4 jambs z 1.00 - 2.20 "1200", W5 jambs z 5.20 - 5.80 "600"
SECTION A-A sheet (vector, 1:100, cm), cut on y = 5 looking north: D2 jambs z 0 - 2.10 "210", width "90";
    D3 jambs z 0 - 2.20 "220", width "100"

Hand areas (width x printed height, m2):
    W1 1.50 x 1.50 = 2.250   W2 1.50 x 1.20 = 1.800   W3 2.10 x (1.80 + 1.05) = 2.10 x 2.85 = 5.985 (owner Q-32 = A)
    windows 2.250 + 1.800 + 5.985 = 10.035 (aluminium, owner Q-33 = A)
    D1 1.20 x 2.40 = 2.880 (AS_DRAWN, outdoor door)
    D2 0.90 x 2.10 = 1.890, D3 1.00 x 2.20 = 2.200 (from the section only; interior doors)
    W4, W5 HELD (their face only on a scan) - mm variant: W4 0.80 x 1.20 = 0.960, W5 1.00 x 0.60 = 0.600
Adversarial: no scale printed (nothing used), scale from the sheet title, two scales, a stale print, a lone number
(units not proven), a number between two equal lines (ambiguous), a chain drawn as one line, an arch crossing a
dimension line (never a tick), plan rotated 30 deg and mirrored, section vs elevation agree / conflict, an outside
window on the same range as a section door (stack not bound), a missing width, a missing height print, and a real
PDF round trip through page_primitives (pymupdf).
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import opening_area as OA  # noqa: E402
from engine.source import opening_height_pdf as P  # noqa: E402

FLOORS = ["GF", "1F"]
K100 = 1.0 / (P.PT_M * 100)      # pt per metre at 1:100
K50 = 1.0 / (P.PT_M * 50)
BOX = (0, 0, 2000, 2000)


# ------------------------------------------------------------------------------------------------- the builder
class Sheet:
    """drawing ops in PDF points, y UP; renders to page primitives (dict) or to a real PDF page."""

    def __init__(self):
        self.lines, self.curves, self.texts = [], [], []

    def line(self, x1, y1, x2, y2):
        self.lines.append((x1, y1, x2, y2))

    def text(self, value, cx, cy, vertical=False, size=6.0):
        self.texts.append((value, cx, cy, vertical, size))

    def tick(self, x, y):
        self.line(x - 0.9, y - 0.9, x + 0.9, y + 0.9)

    def vdim(self, x, ya, yb, value, *, ext_from=None, side=1):
        self.line(x, ya, x, yb)
        self.tick(x, ya)
        self.tick(x, yb)
        if ext_from is not None:
            for y in (ya, yb):
                self.line(ext_from, y, x + 1.5 * (1 if x > ext_from else -1), y)
        self.text(value, x + side * 4.0, (ya + yb) / 2.0, vertical=True)

    def hdim(self, y, xa, xb, value, *, ext_from=None):
        self.line(xa, y, xb, y)
        self.tick(xa, y)
        self.tick(xb, y)
        if ext_from is not None:
            for x in (xa, xb):
                self.line(x, ext_from, x, y + 1.5)
        self.text(value, (xa + xb) / 2.0, y + 4.0)

    def jambs(self, x0, x1, foot, top, head=True):
        self.line(x0, foot, x0, top)
        self.line(x1, foot, x1, top)
        self.line(x0, foot, x1, foot)
        if head:
            self.line(x0, top, x1, top)

    def arch(self, cx, cy, r):
        k = 0.5523 * r
        self.curves.append(((cx - r, cy), (cx - r, cy + k), (cx - k, cy + r), (cx, cy + r)))
        self.curves.append(((cx, cy + r), (cx + k, cy + r), (cx + r, cy + k), (cx + r, cy)))

    def prims(self):
        segs = [(a, b, c, d, f"s{i}") for i, (a, b, c, d) in enumerate(self.lines)]
        for j, (p0, c1, c2, p3) in enumerate(self.curves):
            pts = []
            for k in range(9):
                t = k / 8.0
                a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                pts.append((a * p0[0] + b * c1[0] + c * c2[0] + e * p3[0],
                            a * p0[1] + b * c1[1] + c * c2[1] + e * p3[1]))
            segs += [(p[0], p[1], q[0], q[1], f"c{j}.{i}") for i, (p, q) in enumerate(zip(pts, pts[1:]))]
        words = []
        for v, cx, cy, vert, f in self.texts:
            w, h = 0.5 * f * len(v), 1.2 * f
            if vert:
                words.append({"value": v, "x0": cx - h / 2, "x1": cx + h / 2, "y0": cy - w / 2, "y1": cy + w / 2,
                              "dir": (0.0, 1.0)})
            else:
                words.append({"value": v, "x0": cx - w / 2, "x1": cx + w / 2, "y0": cy - h / 2, "y1": cy + h / 2,
                              "dir": (1.0, 0.0)})
        return {"state": "VECTOR", "words": words, "segments": segs}

    def pdf(self, path, H=1190.0, W=1684.0):
        import pymupdf
        doc = pymupdf.open()
        pg = doc.new_page(width=W, height=H)
        sh = pg.new_shape()
        for x1, y1, x2, y2 in self.lines:
            sh.draw_line((x1, H - y1), (x2, H - y2))
        for p0, c1, c2, p3 in self.curves:
            sh.draw_bezier((p0[0], H - p0[1]), (c1[0], H - c1[1]), (c2[0], H - c2[1]), (p3[0], H - p3[1]))
        sh.finish(width=0.3, color=(0, 0, 0))
        sh.commit()
        for v, cx, cy, vert, f in self.texts:
            w = pymupdf.get_text_length(v, fontsize=f)
            if vert:      # reads bottom to top
                pg.insert_text((cx + 0.35 * f, H - (cy - w / 2)), v, fontsize=f, rotate=90)
            else:
                pg.insert_text((cx - w / 2, H - (cy - 0.35 * f)), v, fontsize=f)
        doc.save(str(path))


def south_sheet(*, w1_text="150", d1_text="240", scale="1:100", extra_scale=None, k=K100):
    X = lambda x: 60 + k * x            # noqa: E731
    Y = lambda z: 100 + k * z           # noqa: E731
    s = Sheet()
    s.line(X(-0.5), Y(0), X(11), Y(0))                       # ground line
    s.line(X(0), Y(0), X(0), Y(8.4))
    s.line(X(10.5), Y(0), X(10.5), Y(8.4))
    s.line(X(0), Y(4.0), X(10.5), Y(4.0))                    # 1F floor line
    s.line(X(0), Y(8.4), X(10.5), Y(8.4))
    # W1
    s.jambs(X(2.25), X(3.75), Y(0.9), Y(2.4))
    s.vdim(X(2.25 + 0.4), Y(0.9), Y(2.4), w1_text)
    s.vdim(X(2.25 + 0.9), Y(0.0), Y(0.9), "90")
    s.hdim(Y(2.75), X(2.25), X(3.75), "150", ext_from=Y(2.4))
    # W2
    s.jambs(X(2.25), X(3.75), Y(5.0), Y(6.2))
    s.vdim(X(2.25 + 0.4), Y(5.0), Y(6.2), "120")
    # D1 (dimension outside, extension lines from the right jamb)
    s.jambs(X(6.4), X(7.6), Y(0.0), Y(2.4))
    if d1_text:
        s.vdim(X(8.0), Y(0.0), Y(2.4), d1_text, ext_from=X(7.6))
    s.hdim(Y(2.75), X(6.4), X(7.6), "120", ext_from=Y(2.4))
    # W3 arched
    s.jambs(X(7.95), X(10.05), Y(4.8), Y(6.6))
    s.arch(X(9.0), Y(6.6), 1.05 * k)
    s.vdim(X(7.95 + 0.4), Y(4.8), Y(6.6), "180")
    s.line(X(9.0), Y(7.65), X(9.0 + 0.4) + 1.5, Y(7.65))      # extension line at the crown
    s.vdim(X(9.3), Y(6.6), Y(7.65), "105")                   # the arch crosses this line: not a tick
    s.hdim(Y(8.0), X(7.95), X(10.05), "210", ext_from=Y(7.65))
    if scale:
        s.text(f"SCALE {scale}", X(5), Y(-1.5))
    if extra_scale:
        s.text(extra_scale, X(5), Y(-2.5))
    return s


def north_sheet_mm():
    """mirrored (seen from the north), 1:50, millimetre prints: x_pt = 60 + K50 (12 - x)."""
    X = lambda x: 60 + K50 * (12 - x)   # noqa: E731
    Y = lambda z: 100 + K50 * z         # noqa: E731
    s = Sheet()
    s.line(X(12.5), Y(0), X(-0.5), Y(0))
    s.line(X(10.5), Y(4.0), X(0), Y(4.0))
    s.jambs(X(4.4), X(3.6), Y(1.0), Y(2.2))
    s.vdim(X(4.4) + 8, Y(1.0), Y(2.2), "1200", ext_from=X(4.4))
    s.hdim(Y(2.6), X(4.4), X(3.6), "800", ext_from=Y(2.2))
    s.jambs(X(10.0), X(9.0), Y(5.2), Y(5.8))
    s.vdim(X(10.0) + 8, Y(5.2), Y(5.8), "600", ext_from=X(10.0))
    s.hdim(Y(6.2), X(10.0), X(9.0), "1000", ext_from=Y(5.8))
    s.text("1:50", X(6), Y(-1.5))
    return s


def section_sheet(*, with_d3=True):
    X = lambda x: 60 + K100 * x         # noqa: E731
    Y = lambda z: 100 + K100 * z        # noqa: E731
    s = Sheet()
    s.line(X(-0.5), Y(0), X(11), Y(0))
    s.line(X(0), Y(4.0), X(10.5), Y(4.0))
    s.jambs(X(4.55), X(5.45), Y(0), Y(2.1))
    s.vdim(X(4.55 + 0.3), Y(0), Y(2.1), "210")
    s.hdim(Y(2.5), X(4.55), X(5.45), "90", ext_from=Y(2.1))
    if with_d3:
        s.jambs(X(7.5), X(8.5), Y(0), Y(2.2))
        s.vdim(X(7.5 + 0.3), Y(0), Y(2.2), "220")
        s.hdim(Y(2.6), X(7.5), X(8.5), "100", ext_from=Y(2.2))
    s.text("SECTION A-A 1:100", X(5), Y(-1.5))
    return s


def plan(rot_deg=0.0, mirror=False):
    def T(x, y):
        if mirror:
            x = -x
        a = math.radians(rot_deg)
        return [x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)]

    ax = T(1.0, 0.0)
    o = lambda i, f, k, x, y, w, **kw: {"id": i, "floor": f, "kind": k, "xy": T(x, y), "axis": ax, "width_m": w,  # noqa
                                        **kw}
    return [o("W1", "GF", "WINDOW", 3.0, 0.0, 1.50), o("D1", "GF", "DOOR", 7.0, 0.0, 1.20,
                                                         door_class="ALUMINIUM_EXTERNAL", faces_outside=True),
            o("W2", "1F", "WINDOW", 3.0, 0.0, 1.50), o("W3", "1F", "WINDOW", 9.0, 0.0, 2.10),
            o("W4", "GF", "WINDOW", 4.0, 10.0, 0.80), o("W5", "1F", "WINDOW", 9.5, 10.0, 1.00),
            o("D2", "GF", "DOOR", 5.0, 5.0, 0.90, door_class="WOOD_INTERNAL", faces_outside=False),
            o("D3", "GF", "DOOR", 8.0, 5.0, 1.00, door_class="WOOD_INTERNAL", faces_outside=False)]


def by_id(res):
    return {r["id"]: r for r in res["records"]}


def run(*, south=None, north=None, section=None, raster=("NORTH ELEVATION (scan)",), plan_ops=None, basis=None):
    elev = [P.view_from_page((south or south_sheet()).prims(), BOX, "SOUTH")]
    if north is not None:
        elev.append(P.view_from_page(north.prims(), BOX, "NORTH"))
    secs = [P.view_from_page((section or section_sheet()).prims(), BOX, "A-A", kind="SECTION")]
    return P.measure_pdf(plan_ops or plan(), floors=FLOORS, elevation_views=elev, section_views=secs,
                         raster_sheets=list(raster), curved_width_basis=basis)


HAND = {"W1": (1.50, 1.50, 2.250), "W2": (1.50, 1.20, 1.800), "W3": (2.10, 2.85, 5.985), "D1": (1.20, 2.40, 2.880),
        "D2": (0.90, 2.10, 1.890), "D3": (1.00, 2.20, 2.200)}


def _check_hand(res, ids=HAND):
    r = by_id(res)
    for k in ids:
        w, h, a = HAND[k]
        assert r[k]["status"] == OA.MEASURED, (k, r[k]["reason"], r[k]["evidence"])
        assert r[k]["height_m"] == pytest.approx(h, abs=1e-4), k
        assert r[k]["area_m2"] == pytest.approx(a, abs=1e-3), k


# ------------------------------------------------------------------------------------------------- main case
def test_main_case_hand_areas():
    res = run()
    _check_hand(res)
    r = by_id(res)
    assert r["W3"]["evidence"]["shape"] == "ARCHED" and r["W3"]["evidence"]["parts_m"] == [1.8, 1.05]
    assert r["D2"]["height_source"] == "SECTION" and r["D3"]["height_source"] == "SECTION"
    assert r["D2"]["evidence"]["elevation_hold"]["reason"] == "INTERIOR_OPENING"
    assert res["summary"]["measured_m2"]["WINDOW:ALUMINIUM"] == pytest.approx(10.035, abs=1e-3)
    assert r["D1"]["material"] == "ALUMINIUM"


def test_scan_face_held_with_route_never_zero():
    r = by_id(run())
    for k in ("W4", "W5"):
        assert r[k]["status"] == OA.HELD and r[k]["area_m2"] is None
        # the south elevation sees the same plan axis but draws no jamb pair there (opening_area's own reason)
        assert r[k]["reason"] == "NOT_DRAWN_ON_THIS_ELEVATION"
        assert r[k]["evidence"]["raster_sheets_not_read"] == ["NORTH ELEVATION (scan)"]
        assert "Q-17" in r[k]["evidence"]["route"]
    assert all(x["area_m2"] != 0 for x in run()["records"])


def test_view_diagnostics_scale_unit():
    v = P.view_from_page(south_sheet().prims(), BOX, "SOUTH")
    d = v["pdf"]
    assert d["scale"] == 100 and d["scale_source"] == "PRINTED" and d["print_unit"] == "cm"
    assert v["unit_m"] == pytest.approx(0.0254 / 72 * 100)
    assert d["bound"] == 9 and not d["ambiguous"]


def test_arch_crossing_line_is_no_tick():
    v = P.view_from_page(south_sheet().prims(), BOX, "SOUTH")
    kept = {s[4] for s in v["segments"]}
    assert sum(1 for i in kept if i.startswith("c")) == 16          # every arch chord stays in the view
    assert any(d["shown_text"] == "105" for d in v["dims"])


# ------------------------------------------------------------------------------------------------- variants
def test_mm_mirrored_north_at_1_50():
    res = run(north=north_sheet_mm(), raster=())
    r = by_id(res)
    assert r["W4"]["status"] == OA.MEASURED and r["W4"]["area_m2"] == pytest.approx(0.960, abs=1e-3)
    assert r["W5"]["status"] == OA.MEASURED and r["W5"]["area_m2"] == pytest.approx(0.600, abs=1e-3)
    m = next(v for v in res["views"] if v["view_id"] == "NORTH")["mapping"]
    assert m["state"] == "MAPPED" and m["mirrored"] is True
    assert P.view_from_page(north_sheet_mm().prims(), BOX, "N")["pdf"]["print_unit"] == "mm"
    _check_hand(res)


@pytest.mark.parametrize("rot,mirror", [(30.0, False), (0.0, True), (-123.0, True)])
def test_plan_rotated_and_mirrored(rot, mirror):
    _check_hand(run(plan_ops=plan(rot, mirror)))


def test_no_scale_printed_nothing_used():
    res = run(south=south_sheet(scale=None))
    r = by_id(res)
    for k in ("W1", "W2", "W3", "D1"):
        assert r[k]["status"] == OA.HELD and r[k]["area_m2"] is None
    v = P.view_from_page(south_sheet(scale=None).prims(), BOX, "S")
    assert v["dims"] == [] and v["pdf"]["why"].startswith("SCALE_NOT_PRINTED")


def test_scale_from_sheet_title_by_caller():
    v = P.view_from_page(south_sheet(scale=None).prims(), BOX, "SOUTH", scale_den=100)
    assert v["pdf"]["scale_source"].startswith("CALLER")
    res = P.measure_pdf(plan(), floors=FLOORS, elevation_views=[v], section_views=[
        P.view_from_page(section_sheet().prims(), BOX, "A-A", kind="SECTION")])
    _check_hand(res)


def test_two_scales_conflict_and_caller_conflict():
    v = P.view_from_page(south_sheet(extra_scale="1:50").prims(), BOX, "S")
    assert v["pdf"]["why"] == "SCALE_CONFLICT" and v["dims"] == []
    v = P.view_from_page(south_sheet().prims(), BOX, "S", scale_den=50)
    assert v["pdf"]["why"] == "SCALE_CONFLICT"


def test_stale_print_not_used():
    r = by_id(run(south=south_sheet(w1_text="160")))
    assert r["W1"]["status"] == OA.HELD and r["W1"]["area_m2"] is None
    assert r["W2"]["status"] == OA.MEASURED                         # the rest of the view still reads


def test_missing_height_print_held():
    r = by_id(run(south=south_sheet(d1_text=None)))
    assert r["D1"]["status"] == OA.HELD and r["D1"]["reason"] == "NO_PRINTED_HEIGHT"


def test_missing_width_held():
    ops = plan()
    ops[0]["width_m"] = None
    r = by_id(run(plan_ops=ops))
    assert r["W1"]["status"] == OA.HELD and r["W1"]["reason"] == "WIDTH_MISSING"


def test_units_not_proven_with_one_number():
    s = Sheet()
    s.line(100, 100, 100, 100 + 1.5 * K100)
    s.tick(100, 100)
    s.tick(100, 100 + 1.5 * K100)
    s.text("150", 104, 100 + 0.75 * K100, vertical=True)
    s.text("1:100", 300, 50)
    v = P.view_from_page(s.prims(), BOX, "X")
    assert v["pdf"]["why"].startswith("UNITS_NOT_PROVEN") and v["dims"] == []


def test_number_between_two_lines_is_ambiguous():
    s = Sheet()
    for x, h in ((100, 1.5), (108, 1.6)):
        s.line(x, 100, x, 100 + h * K100)
        s.tick(x, 100)
        s.tick(x, 100 + h * K100)
    s.text("150", 104, 100 + 0.75 * K100, vertical=True)
    s.text("1:100", 300, 50)
    v = P.view_from_page(s.prims(), BOX, "X")
    assert v["pdf"]["ambiguous"] == ["150"]


def test_chain_drawn_as_one_line_is_split():
    s = Sheet()
    y0 = 100
    s.line(100, y0, 100, y0 + 3.0 * K100)
    for z in (0.0, 0.9, 3.0):
        s.tick(100, y0 + z * K100)
    s.text("90", 104, y0 + 0.45 * K100, vertical=True)
    s.text("210", 104, y0 + 1.95 * K100, vertical=True)
    s.text("1:100", 300, 50)
    v = P.view_from_page(s.prims(), BOX, "X")
    got = sorted((d["shown_text"], round(abs(d["p3"][1] - d["p2"][1]) / K100, 3)) for d in v["dims"])
    assert got == [("210", 2.1), ("90", 0.9)]


def test_corner_is_not_a_dimension():
    """a number beside a window jamb (a plain corner, no tick) is not bound to the jamb."""
    s = Sheet()
    s.jambs(100, 100 + 1.2 * K100, 100, 100 + 1.5 * K100)
    s.text("150", 96, 100 + 0.75 * K100, vertical=True)
    s.text("1:100", 300, 50)
    v = P.view_from_page(s.prims(), BOX, "X")
    assert v["dims"] == [] and ("150", "NO_DIMENSION_LINE") in v["pdf"]["unbound"]


def _inside_view(w1_print):
    """an inside section looking south (mirrored) that also prints W1."""
    X = lambda x: 60 + K100 * (11 - x)  # noqa: E731
    Y = lambda z: 100 + K100 * z        # noqa: E731
    s = Sheet()
    s.jambs(X(3.75), X(2.25), Y(0.9), Y(0.9 + float(w1_print) / 100))
    s.vdim(X(3.75) + 10, Y(0.9), Y(0.9 + float(w1_print) / 100), w1_print, ext_from=X(3.75))
    s.jambs(X(3.75), X(2.25), Y(5.0), Y(6.2))                  # W2 above it (unprinted here)
    s.hdim(Y(3.0), X(3.75), X(2.25), "150", ext_from=Y(0.9 + float(w1_print) / 100))
    s.jambs(X(7.6), X(6.4), Y(0.0), Y(2.4))
    s.hdim(Y(3.0), X(7.6), X(6.4), "120", ext_from=Y(2.4))
    s.text("1:100", X(5), Y(-1.5))
    return P.view_from_page(s.prims(), BOX, "B-B", kind="SECTION")


def test_section_agrees_with_elevation():
    elev = [P.view_from_page(south_sheet().prims(), BOX, "SOUTH")]
    r = by_id(P.measure_pdf(plan(), floors=FLOORS, elevation_views=elev, section_views=[_inside_view("150")]))
    assert r["W1"]["status"] == OA.MEASURED and "section_agrees" in r["W1"]["evidence"]


def test_section_conflicts_with_elevation_held():
    elev = [P.view_from_page(south_sheet().prims(), BOX, "SOUTH")]
    r = by_id(P.measure_pdf(plan(), floors=FLOORS, elevation_views=elev, section_views=[_inside_view("155")]))
    assert r["W1"]["status"] == OA.HELD and r["W1"]["reason"] == "HEIGHT_CONFLICT"
    assert r["W1"]["evidence"]["values_m"] == [1.5, 1.55] and r["W1"]["area_m2"] is None


def test_outside_window_on_section_door_range_holds_door():
    ops = plan()
    ops.append({"id": "W6", "floor": "1F", "kind": "WINDOW", "xy": [8.0, 10.0], "axis": [1.0, 0.0], "width_m": 1.00})
    r = by_id(run(plan_ops=ops))
    assert r["D3"]["status"] == OA.HELD and r["D3"]["area_m2"] is None
    assert r["D2"]["status"] == OA.MEASURED


def test_raster_page_reads_nothing():
    v = P.view_from_page({"state": "RASTER_ONLY", "words": [], "segments": []}, BOX, "SCAN")
    assert v["dims"] == [] and v["pdf"]["why"].startswith("RASTER_ONLY")


def test_inputs_not_mutated():
    ops = plan()
    before = copy.deepcopy(ops)
    run(plan_ops=ops)
    assert ops == before


# ------------------------------------------------------------------------------------------------- real PDF
def test_real_pdf_round_trip(tmp_path):
    pytest.importorskip("pymupdf")
    files = {}
    for name, sheet in (("south", south_sheet()), ("north", north_sheet_mm()), ("sect", section_sheet())):
        files[name] = tmp_path / f"{name}.pdf"
        sheet.pdf(files[name])
    pr = {k: P.page_primitives(f, 1) for k, f in files.items()}
    assert all(p["state"] == "VECTOR" for p in pr.values())
    assert any(abs(w["dir"][1]) > 0.99 for w in pr["south"]["words"])        # rotated prints are read as vertical
    elev = [P.view_from_page(pr["south"], BOX, "SOUTH"), P.view_from_page(pr["north"], BOX, "NORTH")]
    sec = [P.view_from_page(pr["sect"], BOX, "A-A", kind="SECTION")]
    res = P.measure_pdf(plan(), floors=FLOORS, elevation_views=elev, section_views=sec)
    _check_hand(res)
    r = by_id(res)
    assert r["W4"]["area_m2"] == pytest.approx(0.960, abs=1e-3)
    assert r["W5"]["area_m2"] == pytest.approx(0.600, abs=1e-3)


def test_scanned_pdf_is_raster_only(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    from PIL import Image
    img = tmp_path / "scan.png"
    Image.new("L", (200, 140), 255).save(img)
    doc = pymupdf.open()
    pg = doc.new_page(width=842, height=595)
    pg.insert_image(pg.rect, filename=str(img))
    doc.save(str(tmp_path / "scan.pdf"))
    p = P.page_primitives(tmp_path / "scan.pdf", 1)
    assert p["state"] == "RASTER_ONLY" and p["words"] == [] and p["segments"] == []
