"""M6 completeness engine: the generic rules on hand-made inputs - layer and label vocabulary, shapes (loops, strips,
treads, radial ribs, an opening's X), drafting symbols, grouping, composite column outlines, finding ids and the
no-ratio rule."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.source import concrete_completeness as CC     # noqa: E402


def _line(a, b, layer="9"):
    return {"eid": f"L{a}{b}", "type": "LINE", "layer": layer, "a": a, "b": b, "len": math.dist(a, b),
            "pts": [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in (0, .25, .5, .75, 1)],
            "box": CC._bbox([a, b])}


def _rect(x0, y0, x1, y1, layer="9"):
    p = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [_line(p[i], p[(i + 1) % 4], layer) for i in range(4)]


def test_annotation_layers_and_layer_families():
    for lay in ("S-DIM", "S-TEXT", "S-AXIS", "LEVEL", "S-SEC.LINE", "N-ARROW", "REIN", "S-REIN-SLAB", "DEFPOINTS"):
        assert CC.annotation_layer(lay), lay
    for lay in ("1", "S-BOUN", "S-POOL", "ST", "S-LIFT", "S-BEAM"):
        assert not CC.annotation_layer(lay), lay
    assert CC.layer_family("S-BOUN") == "BOUNDARY_WALL" and CC.layer_family("SWIMMING POOL") == "POOL"
    assert CC.layer_family("ST") == "STAIRS" and CC.layer_family("S-TEXT") is None      # 'ST' only as a whole token
    assert CC.layer_family("WATER-TANK") == "WATER_TANK" and CC.layer_family("7") is None
    assert CC.layer_family("ELEV-PIT") is None                                          # ambiguous: never guessed


def test_section_labels_and_thickness():
    assert CC.section_label("P.C 20x70")[:3] == ("PLANTED_COLUMN", 20, 70)
    assert CC.section_label("PLANTED COL. 25 x 50")[0] == "PLANTED_COLUMN"
    assert CC.section_label("PC (20x60)")[0] == "PLANTED_COLUMN"
    assert CC.section_label("GB 30X60")[0] == "GROUND_BEAMS"
    assert CC.section_label("B.W 20x60")[0] == "BOUNDARY_WALL"
    assert CC.section_label("ROOM 4x5") is None and CC.section_label("+3.50") is None
    assert CC.thickness_m("T=20") == 0.20 and CC.thickness_m("200 THK") == 0.2 and CC.thickness_m("B12") is None


def test_note_families_are_whole_words():
    words, _ = CC._note_words()
    assert CC.note_families("SWIMMING POOL", words) == ["POOL"]
    assert "BOUNDARY_WALL" in CC.note_families("BOUNDARY WALL", words)
    assert "WALLS" not in CC.note_families("BOUNDARY WALL", words)
    assert CC.note_families("STAIRCASE", words) == [] or "STAIRS" in CC.note_families("STAIRCASE", words)
    assert CC.note_families("SPOOL", words) == []                                     # not a word of POOL


def test_loops_strips_treads():
    ring = CC._loops(_rect(0, 0, 4, 3), 1e-6)
    assert len(ring) == 1 and abs(abs(CC._signed_area(ring[0])) - 12.0) < 1e-9
    pairs = CC._parallel_pairs([_line((0, 0), (5, 0)), _line((0, 0.25), (5, 0.25))], 0.08, 0.8, 0.5)
    assert pairs and abs(pairs[0][0] - 0.25) < 1e-9 and abs(pairs[0][1] - 5.0) < 1e-9
    treads = [_line((0, 0.29 * k), (1.1, 0.29 * k)) for k in range(10)]
    tr = CC._treads(treads, 0.22, 0.36)
    assert tr and tr["n_treads"] == 10 and abs(tr["going_m"] - 0.29) < 1e-9
    assert CC._treads([_line((0, 0), (1, 0)), _line((0, 3), (1, 3))], 0.22, 0.36) is None


def test_radial_ribs_and_opening_cross():
    c = {"type": "CIRCLE", "c": (5.0, 5.0), "r": 1.5, "layer": "6"}
    ribs = [_line((5.0, 5.0), (5 + 1.3 * math.cos(2 * math.pi * k / 12), 5 + 1.3 * math.sin(2 * math.pi * k / 12)))
            for k in range(12)]
    assert CC._radial(ribs, [c])["spokes"] == 12
    winder = [_line((0, 0), (2, 0.3 * k)) for k in range(6)]                           # fans from a corner
    assert (CC._radial(winder, [c]) or {"spokes": 0})["spokes"] < 6
    x = [_line((0, 0), (3, 2)), _line((0, 2), (3, 0))]
    assert CC._x_cross(x, (0, 0, 3, 2))
    assert not CC._x_cross([_line((0, 0), (3, 0)), _line((0, 1), (3, 1))], (0, 0, 3, 1))


def test_drafting_symbols():
    near = [{"norm": "Ø10@200", "x": 0, "y": 0}]
    assert CC._drafting_symbol([_line((0, 0), (3, 0)), _line((0, 0), (0, 0.15))], [], near, 1.0, {}) == "REBAR_SYMBOL"
    bub = [{"type": "CIRCLE", "c": (-0.4, 0.0), "r": 0.35}]
    assert CC._drafting_symbol([_line((0, 0), (8, 0))], bub, [{"norm": "A", "x": -0.4, "y": 0}], 1.0, {}) == \
        "SECTION_MARK"
    assert CC._drafting_symbol([_line((0, 0), (8, 0))], [], [{"norm": "POOL", "x": 0, "y": 0}], 1.0, {}) is None


def test_clusters_split_by_layer_and_gap():
    ents = _rect(0, 0, 2, 1, "9") + _rect(2.3, 0, 4, 1, "9") + _rect(10, 0, 11, 1, "9") + _rect(0, 0, 2, 1, "8")
    groups = CC._clusters(ents, 0.6)
    sizes = sorted((g[0]["layer"], len(g)) for g in groups)
    assert sizes == [("8", 4), ("9", 4), ("9", 8)]


def test_composite_column_outlines():
    boxes = [((0, 0, 0.2, 0.6), "a"), ((0.2, 0.4, 0.6, 0.6), "b"), ((3, 3, 3.3, 3.3), "c")]
    comps = CC._composites(boxes, 0.05)
    assert sorted(len(m) for _, m in comps) == [1, 2]
    assert any(b == (0, 0, 0.6, 0.6) for b, _ in comps)


def test_finding_ids_are_stable_and_severity_checked():
    a = CC._finding("DRAWN_NOT_MEASURED", "SH01", {"storey": "GF"}, (1, 1, 2, 2), "HIGH", family="POOL")
    b = CC._finding("DRAWN_NOT_MEASURED", "SH01", {"storey": "GF"}, (1, 1, 2, 2), "HIGH", family="POOL")
    assert a["FINDING_ID"] == b["FINDING_ID"] and a["FINDING_ID"].startswith("CC-")
    assert a["VOLUME_HIGH_M3"] is None and a["ACTION"]
    with pytest.raises(CC.CompletenessError):
        CC._finding("DRAWN_NOT_MEASURED", "SH01", None, None, "SEVERE")


def test_suspect_column_outline():
    row = {"by_storey": {"GF": {"dims_m": {"W": 0.2, "H": 0.4}}}, "dims_m": {}}
    assert CC._column_outline_suspect({"row": row, "drawn_m": [1.8, 1.8]})
    assert not CC._column_outline_suspect({"row": row, "drawn_m": [0.2, 0.4]})
    assert not CC._column_outline_suspect({"row": None, "drawn_m": [1.8, 1.8]})       # no section: no claim


def test_policy_names_every_kind_and_no_ratio():
    rec = CC.policy_record()
    assert rec["policy"] == "CONCRETE_COMPLETENESS_V1" and "NO_EVIDENCE_CONFIRM_ABSENT" in rec["rule"]
    src = (ROOT / "engine/source/concrete_completeness.py").read_text(encoding="utf-8")
    assert "kg/m3" not in src.replace("never a kg/m3", "") and "KG_PER_M3" not in src
