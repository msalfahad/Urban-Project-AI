"""Phase A2 generic pieces besides role inference, on synthetic known answers: constraint-unique footing completion
(template outlines, strap-beam entries, clipping, containment, count uniqueness, refusals), cross-document plot-side
unit evidence through the frozen frame rule, and the RTEXT proxy-graphics placement reader."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from engine.source import frame as FR, level_marks as LM, structural_qto as SQ

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/external_engine_lab"))


def box(k, x0, y0, x1, y1, gap=None):
    """Four sides of an outline; `gap` = (side, a, b) leaves an entry gap on that side between a and b."""
    out = []
    sides = {"S": (x0, y0, x1, y0), "E": (x1, y0, x1, y1), "N": (x1, y1, x0, y1), "W": (x0, y1, x0, y0)}
    for name, (ax, ay, bx, by) in sides.items():
        if gap and gap[0] == name:
            a, b = gap[1], gap[2]
            if name in "SN":
                lo, hi = min(ax, bx), max(ax, bx)
                out += [(f"{k}{name}1", lo, ay, a, ay), (f"{k}{name}2", b, ay, hi, ay)]
            else:
                lo, hi = min(ay, by), max(ay, by)
                out += [(f"{k}{name}1", ax, lo, ax, a), (f"{k}{name}2", ax, b, ax, hi)]
        else:
            out.append((f"{k}{name}", ax, ay, bx, by))
    return out


# ------------------------------------------------------------------ template outlines
def test_template_finds_only_the_scheduled_size_either_orientation():
    segs = box("A", 0, 0, 900, 800) + box("B", 2000, 0, 2800, 900) + box("C", 4000, 0, 5000, 1000)
    got = SQ.template_outlines(segs, 900, 800, 1.0, eps=1.0)
    assert sorted(o["bounds"][:2] for o in got) == [(0.0, 0.0), (2000.0, 0.0)]
    assert all(o["state"] == SQ.FULL for o in got)


def test_strap_entry_gap_is_explained_only_by_an_entering_element():
    gap = ("N", 600, 1400)                                                # 40 % of the side open
    strap = [("S1", 600, 1000, 600, 3000), ("S2", 1400, 1000, 1400, 3000)]
    got = SQ.template_outlines(box("A", 0, 0, 2000, 1000, gap=gap) + strap, 2000, 1000, 1.0, eps=1.0)
    assert len(got) == 1 and got[0]["sides"]["N"] == "ENTRY_GAPS_EXPLAINED"
    # an inclined strap whose side lines pass THROUGH the gap ends into the footing also explains it
    through = [("T1", 400, 1600, 1000, -200), ("T2", 1200, 1600, 1800, -200)]
    xa = 600.0                                                             # T1 crosses y = 1000 at x = 600
    xb = 1400.0                                                            # T2 crosses y = 1000 at x = 1400
    got2 = SQ.template_outlines(box("A", 0, 0, 2000, 1000, gap=("N", xa, xb)) + through, 2000, 1000, 1.0, eps=1.0)
    assert len(got2) == 1 and got2[0]["sides"]["N"] == "ENTRY_GAPS_EXPLAINED"
    # the same gap with nothing entering: the side pieces end there, but that explains nothing
    assert SQ.template_outlines(box("A", 0, 0, 2000, 1000, gap=gap), 2000, 1000, 1.0, eps=1.0) == []
    # a side missing altogether is never an outline
    open_side = [s_ for s_ in box("A", 0, 0, 2000, 1000) if s_[0] != "AN"]
    assert SQ.template_outlines(open_side, 2000, 1000, 1.0, eps=1.0) == []


def test_one_side_clipped_by_a_support_line():
    segs = [s for s in box("A", 0, 0, 900, 800) if s[0] != "AS"]
    sup = [("B1", -5000, 0, 5000, 0)]
    got = SQ.template_outlines(segs, 900, 800, 1.0, eps=1.0, support=sup)
    assert len(got) == 1 and got[0]["state"] == SQ.CLIPPED
    assert SQ.template_outlines(segs, 900, 800, 1.0, eps=1.0) == []


def test_count_unique_completion_and_refusals():
    cand = SQ.template_outlines(box("A", 0, 0, 900, 800) + box("B", 3000, 0, 3900, 800), 900, 800, 1.0, eps=1.0)
    carriers = [(450, 400), (3450, 400)]
    orph = {"F": [{"key": "t1", "x": 1000, "y": 900}, {"key": "t2", "x": 3950, "y": 900}]}
    r = SQ.complete_by_count(orph, {"F": cand}, carriers=carriers, tags=[(1000, 900), (3950, 900)])
    assert r["F"]["state"] == SQ.COUNT_UNIQUE and r["F"]["free_candidates"] == 2
    # three tags, two outlines -> mismatch, nothing completed
    orph3 = {"F": orph["F"] + [{"key": "t3", "x": 6000, "y": 0}]}
    assert SQ.complete_by_count(orph3, {"F": cand}, carriers=carriers)["F"]["state"] == SQ.COUNT_MISMATCH
    # an outline overlapping an already matched outline is not admissible
    r2 = SQ.complete_by_count(orph, {"F": cand}, taken=[(100, 100, 500, 500)], carriers=carriers)
    assert r2["F"]["state"] == SQ.COUNT_MISMATCH
    # no column inside -> not a footing candidate
    assert SQ.complete_by_count(orph, {"F": cand}, carriers=[(9999, 9999)])["F"]["state"] == SQ.NO_CANDIDATE


def test_contained_orphan_matched_before_counting():
    cand = SQ.template_outlines(box("A", 0, 0, 900, 800), 900, 800, 1.0, eps=1.0)
    orph = {"F": [{"key": "t1", "x": 450, "y": 600}]}
    r = SQ.complete_by_count(orph, {"F": cand}, carriers=[(450, 400)], tags=[(450, 600)])
    assert r["F"]["state"] == SQ.COUNT_UNIQUE and r["F"]["contained"][0]["matched_tag"] == "t1"
    # an outline holding ANOTHER type's tag is never this type's
    r2 = SQ.complete_by_count({"F": [{"key": "t1", "x": 2000, "y": 2000}]}, {"F": cand}, carriers=[(450, 400)],
                              tags=[(450, 600), (2000, 2000)])
    assert r2["F"]["state"] != SQ.COUNT_UNIQUE
    assert len(SQ.completion_policy_record()["digest"]) == 64


# ------------------------------------------------------------------ cross-document plot sides
def test_plot_side_values_read_two_decimal_numbers_only():
    vals = LM.plot_side_values([("a", "31.37"), ("b", "15.00"), ("c", "+5.50"), ("d", "3700"), ("e", "NEIGHBOUR")])
    assert vals == [(15.0, "b"), (31.37, "a")]


def test_cross_document_evidence_agrees_and_reaches_verified_with_a_second_class():
    printed = [(31.37, "p1"), (15.0, "p2")]
    rects = [{"width": 31370.0, "height": 15000.0, "edge_keys": ["r1"]}]
    r = LM.cross_document_plot_evidence(printed, rects, printed_sha256="a" * 64, drawing_sha256="b" * 64,
                                        evidence_id="PLOT")
    assert r["state"] == "AGREE" and abs(r["ratios"][0] - 1.0) < 1e-12 and r["evidence"][0].kind == FR.OTHER_SOURCE_DOCUMENT
    lev = FR.UnitEvidence("LEV", FR.NATIVE_UNIT, FR.SECTION_ELEVATION_DIMENSION, "MODEL_SPACE",
                          (FR.family_lineage(FR.SECTION_ELEVATION_DIMENSION, "b" * 64),), derived_value=1.0)
    decl, _ = FR.declaration_evidence(4, "MODEL_SPACE", "b" * 64, parser="EZDXF")
    a = FR.assess(FR.NATIVE_UNIT, list(decl) + [lev] + r["evidence"], "b" * 64, scope="MODEL_SPACE")
    assert a.status == FR.VERIFIED
    alone = FR.assess(FR.NATIVE_UNIT, list(decl) + [lev], "b" * 64, scope="MODEL_SPACE")
    assert alone.status == FR.PROVISIONAL


def test_cross_document_refusals():
    printed = [(31.37, "p1"), (15.0, "p2")]
    square = [{"width": 200.0, "height": 200.0}]
    assert LM.cross_document_plot_evidence(printed, square, printed_sha256="a" * 64, drawing_sha256="b" * 64,
                                           evidence_id="X")["state"] == "NO_MATCH"
    # the plot drawn full size AND as a small-scale key plan in the same model space: two ratios -> contradiction
    two_scales = [{"width": 31370.0, "height": 15000.0}, {"width": 672.3, "height": 1406.0}]
    r = LM.cross_document_plot_evidence(printed, two_scales, printed_sha256="a" * 64, drawing_sha256="b" * 64,
                                        evidence_id="X")
    assert r["state"] == "RATIOS_DISAGREE" and r["evidence"] == []


# ------------------------------------------------------------------ RTEXT placement from proxy graphics
def test_rtext_proxy_vertices_and_fix_unrealised():
    import alsenan_phase_a2 as A2
    pts = [(10.0, 20.0), (110.0, 20.0), (110.0, 40.0), (10.0, 40.0), (10.0, 20.0)]
    rec = struct.pack("<iii", 12 + 24 * 5, 6, 5) + b"".join(struct.pack("<ddd", x, y, 0.0) for x, y in pts)
    blob = struct.pack("<ii", 8 + len(rec), 1) + rec
    assert A2._proxy_vertices([blob.hex().upper()]) == pts
    assert A2._proxy_vertices(["ZZ"]) == []
    out, fixed = A2.fix_unrealised([{"code": "UNHANDLED", "obs_id": "D2:5483", "layer": None, "path": []},
                                    {"code": "DEGENERATE_GEOMETRY", "obs_id": "D2:7", "layer": None, "path": []}],
                                   {5483: {"layer": "stamp", "extent": [10.0, 20.0, 110.0, 40.0],
                                           "extent_basis": "PROXY_GRAPHICS_VERTICES"}})
    assert out[0]["layer"] == "stamp" and out[0]["extent"] == [10.0, 20.0, 110.0, 40.0]
    assert out[1]["layer"] is None and len(fixed) == 1
