"""T-102: BEAM_SECTION_CUT_BINDING_V1 (engine/source/beam_section_cut_binding.py) against a hand fixture.

Hand plan (NOT a client drawing): two slab-plan sheets drawn in millimetres at 1:100 (model units = real mm), every
beam section drawn beside the plan at 1:25 (4 x real size), its dimensions printed in cm (DIMLFAC 0.025 = 1/4 x mm->cm).
Beam bands come from the frozen MEMBER_DETECTION_V1 (beam_bands + split_at_supports) on the face lines below.

Sheet S1 (box -2000..36000 x -3000..30000):
  B1, 0.30 wide, faces y 0 / 300, x 0 .. 6300, column 300 x 400 at x 3000..3300 -> two clear spans 3.000 m each.
     Mark B1 printed on the east span; the west span only takes B1 along its line (INHERITED_ALONG_LINE).
     Strip 0.20 wide (faces y 1000 / 1200, x 0 .. 3000), no mark.
     Cut A-A at x 1500 crosses the B1 west span and the strip. Section A-A prints 30 / 60 (cm), drawn 1200 x 2400.
     -> RELEASED: 0.30 x 3.000 x 0.60 = 0.540 m3 (= schedule row B1 30 x 60); the strip is listed, not bound.
  C1 / C2, both 0.30 wide (y 3000..3300 and 3800..4100, x 0 .. 5000); cut B-B at x 2500 crosses both; B-B prints 30 / 60
     -> HELD CUT_CROSSES_SEVERAL_SPANS (two spans at the printed width, never a pick).
  B5, 0.30 wide (y 6000..6300, x 0 .. 4000), mark B5 = schedule 30 x 60; cut C-C at x 2000; C-C prints 30 / 70
     -> HELD CONFLICT_SECTION_VS_SCHEDULE: section 0.30 x 4.000 x 0.70 = 0.840 m3, row 0.30 x 4.000 x 0.60 = 0.720 m3.
  N1, 0.25 wide (y 9000..9250, x 0 .. 4000), NO mark; cut D-D at x 2000; D-D prints 25 / 50
     -> RELEASED SECTION_ONLY: 0.25 x 4.000 x 0.50 = 0.500 m3.
  H1, 0.30 wide (y 12000..12300, x 0 .. 4000), mark B1; cut E-E at x 2000; E-E prints only its width (no depth)
     -> HELD SECTION_HELD (depth not printed); never 0.
  K1, 0.30 wide (y 15000..15300, x 0 .. 4000), mark B1; cut F-F at x 2000; no section F-F on S1 (it is on S2)
     -> HELD SECTION_NOT_ON_SHEET (a section on another sheet is never borrowed).
  G: two cut lines lettered G (x 1000 and x 3000 across K2: y 18000..18300, x 0 .. 4000) + title G-G -> CUT_AMBIGUOUS.
Sheet S2 (box 40000..76000 x -3000..30000), letters restart: B2, 0.40 wide (y 0..400, x 40000 .. 44000), mark B2 =
  schedule 40 x 70; cut A-A at x 42000; S2's own A-A prints 40 / 70 + an upstand 20 / 20 flush right
  -> RELEASED 0.40 x 4.000 x 0.70 = 1.120 m3; upstand listed 0.20 x 0.20 x 4.000 = 0.160 m3 (not added to the span).
  Title F-F on S2 with no F cut on S2 -> HELD CUT_NOT_FOUND.
Variants: the same drawing mirrored (x -> -x), turned 90 deg (texts turned with it), in metres (unit 1.0), and with
the sections printed in mm (DIMLFAC 0.25): every state and volume identical.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import beam_section_cut_binding as SC  # noqa: E402
from engine.source import member_detection as MD  # noqa: E402

SCHEDULE = {"B1": (0.30, 0.60), "B2": (0.40, 0.70), "B5": (0.30, 0.60)}
S1 = (-2000.0, -3000.0, 36000.0, 30000.0)
S2 = (40000.0, -3000.0, 76000.0, 30000.0)


# ------------------------------------------------------------------------------------------------ fixture builder
class Plan:
    def __init__(self):
        self.segs, self.texts, self.dims, self.outlines, self.cols = [], [], [], [], []
        self.n = 0

    def _id(self, p):
        self.n += 1
        return f"{p}{self.n}"

    def seg(self, a, b, layer):
        self.segs.append({"id": self._id("S"), "layer": layer, "a": a, "b": b})

    def beam(self, x0, x1, y0, y1):
        self.seg((x0, y0), (x1, y0), "BEAM")
        self.seg((x0, y1), (x1, y1), "BEAM")

    def text(self, value, x, y, rot=0.0):
        self.texts.append({"id": self._id("T"), "value": value, "x": x, "y": y, "rotation": rot, "height": 250.0})

    def cut(self, letter, x, y0, y1, letters=True):
        self.seg((x, y0), (x, y1), "CUT")
        for y in (y0 + 250.0, y1 - 250.0):
            self.seg((x - 300.0, y), (x + 500.0, y), "CUT")
            if letters:
                self.text(letter, x + 100.0, y + (150.0 if y > (y0 + y1) / 2 else -150.0))

    def section(self, letter, x, y, w_cm, d_cm, *, up=None, depth_dim=True, lfac_mm=False):
        """title at (x, y); outline drawn 4x real (mm), bottom 500 above the title; printed numbers in cm (or mm)"""
        self.text(f"%%USECTION {letter}-{letter}", x, y)
        k = 10.0 if lfac_mm else 1.0                    # printed value: cm, or mm
        W, D = w_cm * 40.0, d_cm * 40.0                  # drawn mm: 1 cm real = 10 mm x 4
        x0, y0 = x, y + 500.0
        if up:
            uw, uh = up[0] * 40.0, up[1] * 40.0
            pts = [(x0, y0), (x0 + W, y0), (x0 + W, y0 + D + uh), (x0 + W - uw, y0 + D + uh), (x0 + W - uw, y0 + D),
                   (x0, y0 + D)]
        else:
            pts = [(x0, y0), (x0 + W, y0), (x0 + W, y0 + D), (x0, y0 + D)]
        self.outlines.append({"id": self._id("O"), "layer": "SEC", "pts": pts + [pts[0]]})
        self.dims.append({"id": self._id("D"), "axis": "x", "p1": (x0, y0), "p2": (x0 + W, y0), "shown": w_cm * k})
        if depth_dim:
            self.dims.append({"id": self._id("D"), "axis": "y", "p1": (x0, y0), "p2": (x0, y0 + D),
                              "shown": d_cm * k})
        if up:
            self.dims.append({"id": self._id("D"), "axis": "x", "p1": (x0 + W - uw, y0 + D + uh),
                              "p2": (x0 + W, y0 + D + uh), "shown": up[0] * k})
            self.dims.append({"id": self._id("D"), "axis": "y", "p1": (x0 + W - uw, y0 + D),
                              "p2": (x0 + W - uw, y0 + D + uh), "shown": up[1] * k})


def hand_plan(lfac_mm=False):
    P = Plan()
    # ---- S1
    P.beam(0, 6300, 0, 300)
    P.cols.append((3000.0, -50.0, 3300.0, 350.0))
    P.beam(0, 3000, 1000, 1200)
    P.text("B1", 4800.0, 150.0)
    P.cut("A", 1500.0, -800.0, 1500.0)
    P.section("A", 20000.0, 0.0, 30, 60, lfac_mm=lfac_mm)
    P.beam(0, 5000, 3000, 3300)
    P.beam(0, 5000, 3800, 4100)
    P.cut("B", 2500.0, 2300.0, 4600.0)
    P.section("B", 24000.0, 0.0, 30, 60, lfac_mm=lfac_mm)
    P.beam(0, 4000, 6000, 6300)
    P.cut("C", 2000.0, 5300.0, 7000.0)
    P.section("C", 28000.0, 0.0, 30, 70, lfac_mm=lfac_mm)
    P.beam(0, 4000, 9000, 9250)
    P.cut("D", 2000.0, 8300.0, 9950.0)
    P.section("D", 20000.0, 10000.0, 25, 50, lfac_mm=lfac_mm)
    P.beam(0, 4000, 12000, 12300)
    P.cut("E", 2000.0, 11300.0, 13000.0)
    P.section("E", 24000.0, 10000.0, 30, 60, depth_dim=False, lfac_mm=lfac_mm)
    P.beam(0, 4000, 15000, 15300)
    P.cut("F", 2000.0, 14300.0, 16000.0)
    P.beam(0, 4000, 18000, 18300)
    P.cut("G", 1000.0, 17300.0, 19000.0)
    P.cut("G", 3000.0, 17300.0, 19000.0)
    P.section("G", 28000.0, 10000.0, 30, 60, lfac_mm=lfac_mm)
    # ---- S2
    P.beam(40000, 44000, 0, 400)
    P.cut("A", 42000.0, -700.0, 1100.0)
    P.section("A", 60000.0, 0.0, 40, 70, up=(20, 20), lfac_mm=lfac_mm)
    P.section("F", 66000.0, 0.0, 30, 60, lfac_mm=lfac_mm)
    return P


def bindings_for(bands, tp):
    """the route's marks, written by hand for the fixture: band at (y range, x range) -> mark / state"""
    def at(xm, ym):
        for b in bands:
            if b["kind"] != "STRAIGHT":
                continue
            ts = xm * b["u"][0] + ym * b["u"][1]
            ns = xm * b["n"][0] + ym * b["n"][1]
            lo, hi = sorted((b["lo_off"], b["hi_off"]))
            if b["t0"] <= ts <= b["t1"] and lo <= ns <= hi:
                return b["band_id"]
        raise AssertionError(f"no band at {xm}, {ym}")
    m = []
    for mk, st, x, y in [("B1", "BOUND", 4800, 150), ("B1", "INHERITED_ALONG_LINE", 1500, 150),
                         ("B5", "BOUND", 2000, 6150), ("B1", "BOUND", 2000, 12150), ("B1", "BOUND", 2000, 15150),
                         ("B2", "BOUND", 42000, 200)]:
        m.append({"mark": mk, "state": st, "bands": [at(*tp((x, y)))]})
    return m


def run(P, T=lambda p: p, rot=0.0, scale=1.0, lfac_mm=False):
    """apply a drawing transform (mirror / turn) and a unit change (scale: native = mm x scale), then bind"""
    u = 0.001 / scale
    tp = lambda p: tuple(v * scale for v in T(p))         # noqa: E731
    segs = [dict(s, a=tp(s["a"]), b=tp(s["b"])) for s in P.segs]
    texts = []
    for t in P.texts:
        x, y = tp((t["x"], t["y"]))
        texts.append(dict(t, x=x, y=y, rotation=(t["rotation"] + rot) % 360.0, height=t["height"] * scale))
    dims = []
    for d in P.dims:
        p1, p2 = tp(d["p1"]), tp(d["p2"])
        axis = d["axis"] if rot in (0.0, 180.0) else {"x": "y", "y": "x"}[d["axis"]]
        k = 0 if axis == "x" else 1
        dims.append(dict(d, axis=axis, p1=p1, p2=p2, lo=min(p1[k], p2[k]), hi=max(p1[k], p2[k])))
    outl = [dict(o, pts=[tp(p) for p in o["pts"]]) for o in P.outlines]

    def tbox(b):
        c = [tp((b[0], b[1])), tp((b[2], b[3])), tp((b[0], b[3])), tp((b[2], b[1]))]
        return (min(x for x, _ in c), min(y for _, y in c), max(x for x, _ in c), max(y for _, y in c))
    cols = [tbox(c) for c in P.cols]
    tol = 0.012 / u
    ents = {"segments": [s for s in segs if s["layer"] == "BEAM"], "arcs": []}
    widths = sorted({0.20 / u, 0.25 / u, 0.30 / u, 0.40 / u})
    bands, _ = MD.beam_bands(ents, ["BEAM"], widths, tol, 0.3 / u)
    bands = MD.split_at_supports(bands, cols, 0.05 / u)
    titles = SC.section_titles(texts)
    dimmed = SC.dimensioned_outlines(outl, dims, tol)
    bnd = bindings_for(bands, tp)
    out = {}
    for sid, box in (("S1", S1), ("S2", S2)):
        bx = tbox(box)
        inside = lambda p: bx[0] <= p[0] <= bx[2] and bx[1] <= p[1] <= bx[3]  # noqa: E731
        res = SC.bind_sections(sheet_id=sid, sheet_box=bx, texts=[t for t in texts if inside((t["x"], t["y"]))],
                               segments=[s for s in segs if inside(s["a"]) and inside(s["b"])], bands=bands,
                               unit_m=u, titles_all=titles, dimmed=dimmed, bindings=bnd, schedule=SCHEDULE,
                               edge_layers={"BEAM"}, tol_native=tol)
        for r in res:
            out[(sid, r["letter"])] = r
    return out


def summary(out):
    return {k: (r["state"], r.get("reason"), r.get("volume_m3"), r.get("width_m"), r.get("depth_m"),
                r.get("length_m"), tuple(sorted((r.get("candidates_m3") or {}).items())),
                (r.get("upstand") or {}).get("volume_m3")) for k, r in out.items()}


@pytest.fixture(scope="module")
def base():
    return run(hand_plan())


# ------------------------------------------------------------------------------------------------ hand truth
def test_a_a_released_on_the_one_span_at_the_printed_width(base):
    r = base[("S1", "A")]
    assert r["state"] == "RELEASED" and r["status"] == "DRAWING-VERIFIED"
    assert (r["width_m"], r["depth_m"]) == (0.30, 0.60) and r["unit_m"] == 0.01 and r["scale"] == pytest.approx(0.025)
    assert r["length_m"] == pytest.approx(3.000)
    assert r["volume_m3"] == pytest.approx(0.30 * 3.000 * 0.60)       # 0.540
    assert r["check"].startswith("= schedule row B1")
    assert [x["width_m"] for x in r["not_bound"]] == [0.20]           # the strip: listed, never bound
    assert r["upstand"]["state"] == "NOT_PRESENT"


def test_two_spans_at_the_printed_width_are_held(base):
    r = base[("S1", "B")]
    assert r["state"] == "HELD" and r["reason"] == "CUT_CROSSES_SEVERAL_SPANS" and len(r["candidates"]) == 2
    assert r.get("volume_m3") is None


def test_section_disagreeing_with_its_schedule_row_is_a_conflict_with_both_volumes(base):
    r = base[("S1", "C")]
    assert r["state"] == "HELD" and r["reason"] == "CONFLICT_SECTION_VS_SCHEDULE"
    assert r["candidates_m3"]["section"] == pytest.approx(0.30 * 4.0 * 0.70)       # 0.840
    assert r["candidates_m3"]["schedule_row"] == pytest.approx(0.30 * 4.0 * 0.60)  # 0.720
    assert r.get("volume_m3") is None


def test_unmarked_span_settled_by_its_own_printed_section(base):
    r = base[("S1", "D")]
    assert r["state"] == "RELEASED" and r["check"].startswith("SECTION_ONLY")
    assert r["volume_m3"] == pytest.approx(0.25 * 4.0 * 0.50)          # 0.500


def test_missing_depth_is_held_never_zero(base):
    r = base[("S1", "E")]
    assert r["state"] == "HELD" and r["reason"] == "SECTION_HELD" and "depth" in r["why"]
    assert r.get("volume_m3") is None


def test_section_on_another_sheet_is_never_borrowed(base):
    assert base[("S1", "F")]["reason"] == "SECTION_NOT_ON_SHEET"
    assert base[("S2", "F")]["reason"] == "CUT_NOT_FOUND"


def test_one_letter_on_two_cut_lines_is_ambiguous(base):
    r = base[("S1", "G")]
    assert r["state"] == "HELD" and r["reason"] == "CUT_AMBIGUOUS" and len(r["cut_lines"]) == 2
    assert all(len(c["crossed"]) == 1 for c in r["cut_lines"])


def test_letters_restart_per_sheet_and_the_upstand_is_listed_apart(base):
    r = base[("S2", "A")]
    assert r["state"] == "RELEASED" and (r["width_m"], r["depth_m"]) == (0.40, 0.70)
    assert r["volume_m3"] == pytest.approx(0.40 * 4.0 * 0.70)          # 1.120, upstand not inside
    assert r["upstand"]["state"] == "MEASURED" and r["upstand"]["volume_m3"] == pytest.approx(0.20 * 0.20 * 4.0)


def test_no_letter_is_silent(base):
    assert sorted(base) == sorted([("S1", L) for L in "ABCDEFG"] + [("S2", "A"), ("S2", "F")])
    assert sum(r["volume_m3"] for r in base.values() if r["state"] == "RELEASED") == pytest.approx(0.54 + 0.5 + 1.12)


# ------------------------------------------------------------------------------------------------ adversarial
@pytest.mark.parametrize("name,T,rot,scale", [
    ("mirrored", lambda p: (-p[0], p[1]), 0.0, 1.0),
    ("turned_90", lambda p: (-p[1], p[0]), 90.0, 1.0),
    ("metres", lambda p: p, 0.0, 0.001),
    ("turned_90_mirrored_metres", lambda p: (-p[1], -p[0]), 90.0, 0.001),
])
def test_variants_give_the_same_states_and_volumes(base, name, T, rot, scale):
    got = summary(run(hand_plan(), T=T, rot=rot, scale=scale))
    want = summary(base)
    assert set(got) == set(want)
    for k in want:
        a, b = got[k], want[k]
        assert a[:2] == b[:2], (name, k)
        for x, y in zip(a[2:], b[2:]):
            if isinstance(y, float):
                assert x == pytest.approx(y, abs=1e-6), (name, k)
            else:
                assert x == y or (isinstance(x, tuple) and all(p[0] == q[0] and p[1] == pytest.approx(q[1])
                                                               for p, q in zip(x, y))), (name, k)


def test_section_printed_in_mm(base):
    got = summary(run(hand_plan(lfac_mm=True)))
    assert got[("S1", "A")][:3] == ("RELEASED", None, pytest.approx(0.54))
    r = run(hand_plan(lfac_mm=True))[("S1", "A")]
    assert r["unit_m"] == 0.001 and (r["width_m"], r["depth_m"]) == (0.30, 0.60)


def test_printed_unit_must_match_the_drawn_span():
    """a section printing 35 on a 0.30 span: no unit makes it the drawn width -> NO_SPAN_AT_PRINTED_WIDTH"""
    P = Plan()
    P.beam(0, 4000, 0, 300)
    P.cut("A", 2000.0, -700.0, 1000.0)
    P.section("A", 20000.0, 0.0, 35, 60)
    u, tol = 0.001, 12.0
    bands, _ = MD.beam_bands({"segments": P.segs, "arcs": []}, ["BEAM"], [300.0], tol, 300.0)
    res = SC.bind_sections(sheet_id="X", sheet_box=None, texts=P.texts, segments=P.segs, bands=bands, unit_m=u,
                           titles_all=SC.section_titles(P.texts),
                           dimmed=SC.dimensioned_outlines(P.outlines, P.dims, tol),
                           edge_layers={"BEAM"}, tol_native=tol)
    assert [(r["state"], r["reason"]) for r in res] == [("HELD", "NO_SPAN_AT_PRINTED_WIDTH")]


def test_two_titles_of_one_letter_on_one_sheet_are_held():
    t = SC.section_titles([{"id": "a", "value": "SECTION A-A", "x": 0, "y": 0},
                           {"id": "b", "value": "%%USECTION A-A", "x": 9000, "y": 0}])
    d = SC.pair_section_drawings(t, [], None)
    assert d["A"]["state"] == "HELD" and "2 times" in d["A"]["why"]


def test_title_text_normalised():
    assert SC.norm_text("%%USECTION  b-b") == "SECTION B-B"
    assert [t["letter"] for t in SC.section_titles([{"value": "{\\fArial;SECTION C-C}", "x": 0, "y": 0}])] == ["C"]


def test_policy_is_not_wired():
    rec = SC.policy_record()
    assert rec["wired"] is False and rec["policy"] == "BEAM_SECTION_CUT_BINDING_V1"
    src = (ROOT / "engine" / "source" / "beam_section_cut_binding.py").read_text(encoding="utf-8")
    assert "Alsenan" not in src and "B23" not in src and "B20" not in src     # no project constant


def test_a_ring_of_the_printed_width_crossed_by_the_cut_counts_as_a_second_span():
    """a 0.30 ring (radii 2.000 / 2.300 m about the origin, 0 .. 90 deg) and a straight 0.30 beam (y 3.000 .. 3.300)
    both crossed by cut A at x 1.000: two spans at the printed width -> HELD, the ring is never ignored"""
    P = Plan()
    P.beam(0, 3000, 3000, 3300)
    P.cut("A", 1000.0, 1300.0, 3800.0)
    P.section("A", 20000.0, 0.0, 30, 60)
    arcs = [{"id": f"A{r}", "layer": "BEAM", "c": (0.0, 0.0), "r": float(r), "s": (float(r), 0.0), "e": (0.0, float(r)),
             "dir": "CCW"} for r in (2000, 2300)]
    tol = 12.0
    bands, _ = MD.beam_bands({"segments": P.segs, "arcs": arcs}, ["BEAM"], [300.0], tol, 300.0)
    assert sorted(b["kind"] for b in bands) == ["ARC", "STRAIGHT"]
    res = SC.bind_sections(sheet_id="X", sheet_box=None, texts=P.texts, segments=P.segs, bands=bands, unit_m=0.001,
                           titles_all=SC.section_titles(P.texts),
                           dimmed=SC.dimensioned_outlines(P.outlines, P.dims, tol), edge_layers={"BEAM"},
                           tol_native=tol)
    assert [(r["state"], r["reason"]) for r in res] == [("HELD", "CUT_CROSSES_SEVERAL_SPANS")]
    assert sorted(c["kind"] for c in res[0]["crossed"]) == ["ARC", "STRAIGHT"]
