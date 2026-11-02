"""T-474 part 1: formwork piece census rules R-T474-1 .. 7 (research/agents_t474/t474_rules.py) on a hand-calculated
NON-Alsenan villa (V474), normal and adverse, plus the development-villa line map pins (offline, merged ledgers only).

Villa V474, by hand:
  B1 beam 0.20 wide x 0.60 deep under a 0.15 slab, clear span 4.00 m, its NORTH side cast against an existing block
     wall: soffit 0.20 x 4.00 = 0.800; south side below the slab (0.60 - 0.15) x 4.00 = 1.800; north side against
     MASONRY: no form (no piece) -> B1 = 2.600 m2 (not 4.400 with both sides).
  S1 slab panel 4.00 x 3.00 between member faces: soffit 12.000 m2 (VERIFIED geometry: S1 concrete 12.000 x 0.15 =
     1.800 m3 in a Checker record V-S1); its free south edge 4.00 x 0.15 = 0.600 m2 (slab-thickness band).
  P1 RC parapet on that edge, outer face 1.00 m high from the slab top: 4.00 x 1.00 = 4.000 m2. Given FROM THE SLAB
     SOFFIT (1.15 m: 4.600 m2) it overlaps the slab band by 0.15 m -> netted to 4.000 (0.600 booked once, on S1).
  C1 column 0.30 x 0.30, held (height not printed): blank, never 0.
  C9 column NOT_PRESENT on this floor: a piece on it is refused.
  F1 footing side below EG: OQ-10 open -> held (FORMED / EARTH_CAST pair), never valued.
  Totals valued: B1 2.600 + S1 12.000 + 0.600 + P1 4.000 = 19.200 m2; of it VERIFIED geometry 12.000 m2.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t474"


def _load(name):
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t474_rules")

MEMBERS = {"B1": {"state": "PROVISIONAL"}, "S1": {"state": "SOURCE_DERIVED", "verified_area_m2": 12.0},
           "P1": {"state": "PROVISIONAL"}, "C1": {"state": "PROVISIONAL"}, "F1": {"state": "SOURCE_DERIVED"},
           "C9": {"state": "NOT_PRESENT"}, "G1": {"state": "BLOCKED_RFI", "reason": "depth CONFLICT"}}


def _villa(parapet_from_soffit=False):
    span = R.length((0.0, 0.0), (4.0, 0.0))
    p = [R.piece(member="B1", cls="BEAM", kind="BEAM", contact="FORM", length_m=span, height_m=0.20, ref="soffit"),
         R.piece(member="B1", cls="BEAM", kind="BEAM", contact="FORM", length_m=span, height_m=0.60 - 0.15,
                 ref="south side below slab"),
         R.piece(member="B1", cls="BEAM", kind="BEAM", contact="MASONRY", ref="north side on the block wall"),
         R.piece(member="S1", cls="SLAB", kind="SLAB", contact="FORM", m2=4.0 * 3.0, ref="soffit"),
         R.piece(member="C1", cls="COLUMN", kind="SOFFIT", contact="FORM", held="height not printed", lo=0.0,
                 hi=3.6),
         R.piece(member="F1", cls="FOOTING", kind="SIDE", contact="OQ10", held="OQ-10 FORMED / EARTH_CAST open",
                 lo=0.0, hi=1.92)]
    edge = R.piece(member="S1", cls="SLAB_EDGE", kind="SLAB_EDGE", contact="FORM", length_m=span, height_m=0.15,
                   z=(0.0, 0.15))
    par = (R.piece(member="P1", cls="PARAPET", kind="SIDE", contact="FORM", length_m=span, height_m=1.15,
                   z=(0.0, 1.15)) if parapet_from_soffit else
           R.piece(member="P1", cls="PARAPET", kind="SIDE", contact="FORM", length_m=span, height_m=1.00,
                   z=(0.15, 1.15)))
    return p + [edge, R.net_edge_overlap(edge, par)]


def test_hand_totals_and_bases():
    c = R.census(_villa(), MEMBERS, {"S1": "V-S1"})
    val = [p for p in c["pieces"] if p["m2"] is not None]
    assert round(sum(p["m2"] for p in val), 6) == 19.2
    b1 = sum(p["m2"] for p in val if p["member"] == "B1")
    assert round(b1, 6) == 2.6                                   # the masonry side is no piece
    assert c["by_class"]["SLAB"]["verified_geometry_m2"] == 12.0
    s1 = [p for p in val if p["member"] == "S1" and p["kind"] == "SLAB"][0]
    assert s1["basis"] == "VERIFIED_GEOMETRY V-S1"
    edge = [p for p in val if p["kind"] == "SLAB_EDGE"][0]
    assert edge["basis"].startswith("CALCULATED")                # the verdict covers the panel area, not the edge
    held = [p for p in c["pieces"] if p["m2"] is None]
    assert {p["member"] for p in held} == {"C1", "F1"} and all(p["basis"].startswith("HELD") for p in held)


def test_parapet_from_soffit_is_netted_once():
    a = R.census(_villa(False), MEMBERS, {"S1": "V-S1"})
    b = R.census(_villa(True), MEMBERS, {"S1": "V-S1"})
    tot = lambda c: round(sum(p["m2"] for p in c["pieces"] if p["m2"] is not None), 6)  # noqa: E731
    assert tot(a) == tot(b) == 19.2
    par = [p for p in b["pieces"] if p["member"] == "P1"][0]
    assert par["m2"] == 4.0 and par["netted"] == 0.6


def test_rotation_and_mirror_invariant():
    span_rot = R.length((1.0, 1.0), (1.0 + 4.0 * 0.6, 1.0 + 4.0 * 0.8))     # the 4.00 m span rotated
    span_mir = R.length((0.0, 0.0), (-4.0, 0.0))                              # mirrored
    for s in (span_rot, span_mir):
        p = R.piece(member="B1", cls="BEAM", kind="BEAM", contact="FORM", length_m=s, height_m=0.20)
        assert p["m2"] == 0.8


def test_masonry_or_blinding_face_with_a_figure_refused():
    with pytest.raises(R.PieceError, match="no form"):
        R.piece(member="B1", cls="BEAM", kind="BEAM", contact="MASONRY", m2=1.8)
    with pytest.raises(R.PieceError, match="no form"):
        R.piece(member="F1", cls="FOOTING", kind="SIDE", contact="BLINDING", length_m=1.2, height_m=0.4)


def test_piece_on_not_present_member_refused():
    p = R.piece(member="C9", cls="COLUMN", kind="SOFFIT", contact="FORM", m2=3.6)
    with pytest.raises(R.PieceError, match="leaves with it"):
        R.census([p], MEMBERS)


def test_held_never_zero_and_never_summed():
    with pytest.raises(R.PieceError, match="never 0"):
        R.piece(member="C1", cls="COLUMN", kind="SOFFIT", contact="FORM", held="x", m2=0.0)
    c = R.census(_villa(), MEMBERS, {"S1": "V-S1"})
    assert c["by_class"]["COLUMN"] == {"pieces": 1, "valued_m2": 0.0, "held": 1, "verified_geometry_m2": 0.0}
    assert all(p["m2"] is None for p in c["pieces"] if p["held"])


def test_valued_piece_on_held_concrete_line_goes_held():
    p = R.piece(member="G1", cls="GROUND_BEAM", kind="SIDE", contact="FORM", m2=2.0)
    c = R.census([p], MEMBERS)
    q = c["pieces"][0]
    assert q["m2"] is None and q["held_from"] == 2.0 and "BLOCKED_RFI" in q["basis"]


def test_oq10_never_valued_and_unknown_kind_refused_and_units():
    with pytest.raises(R.PieceError, match="OQ-10"):
        R.piece(member="F1", cls="FOOTING", kind="SIDE", contact="OQ10", m2=1.92)
    with pytest.raises(R.PieceError, match="not a face of class"):
        R.piece(member="S1", cls="SLAB", kind="RISER", contact="FORM", m2=1.0)
    with pytest.raises(R.PieceError, match="lengths in m only"):
        R.piece(member="B1", cls="BEAM", kind="BEAM", contact="FORM", length_m=4000, height_m=200, unit="mm")
    with pytest.raises(R.PieceError, match="no concrete member"):
        R.census([R.piece(member="X", cls="BEAM", kind="BEAM", contact="FORM", m2=1.0)], MEMBERS)


def test_verified_geometry_needs_the_same_area():
    m = dict(MEMBERS, S1={"state": "SOURCE_DERIVED", "verified_area_m2": 11.9})
    c = R.census([R.piece(member="S1", cls="SLAB", kind="SLAB", contact="FORM", m2=12.0)], m, {"S1": "V-S1"})
    assert c["pieces"][0]["basis"].startswith("CALCULATED")       # 0.1 m2 apart: not the verified geometry


def test_parapet_wholly_inside_slab_band_refused():
    edge = R.piece(member="S1", cls="SLAB_EDGE", kind="SLAB_EDGE", contact="FORM", length_m=4.0, height_m=0.15,
                   z=(0.0, 0.15))
    par = R.piece(member="P1", cls="PARAPET", kind="SIDE", contact="FORM", length_m=4.0, height_m=0.15,
                  z=(0.0, 0.15))
    with pytest.raises(R.PieceError, match="one surface twice"):
        R.net_edge_overlap(edge, par)


# ------------------------------------------------------------------ development villa (offline, merged ledgers)
def test_development_villa_line_map_pins():
    A = _load("t474_alsenan")
    rows, s = A.build()
    assert len(rows) == 643 and len({r["line_id"] for r in rows}) == 643
    fw, st = s["by_code"]["STR.FORMWORK"], s["by_code"]["STR.FORMWORK.STAIR"]
    assert (fw["lines"], fw["valued"], fw["valued_m2"]) == (612, 254, 1028.905457)      # = T-199 Gate B
    assert (st["lines"], st["valued"], st["valued_m2"]) == (31, 10, 36.927436)
    vg = s["by_basis"]["VERIFIED_GEOMETRY"]
    assert vg == {"lines": 62, "m2": 375.0481}                   # 62 slab soffits on V2-0c71eb8f0ae7dae0
    assert all(r["m2_v3030"] == "" for r in rows if r["basis"].startswith(("HELD", "NOT_APPLICABLE")))
    # every face booked once across the line map
    ids = [f for r in rows for f in r["face_ids"].split()]
    assert len(ids) == len(set(ids))


def test_committed_outputs_equal_a_fresh_build(tmp_path):
    A = _load("t474_alsenan")
    out = HERE / "out"
    if not (out / "FORMWORK_LINE_MAP_T474.csv").exists():
        pytest.skip("no committed output")
    lines = None
    live = out / "LIVE_V3_0_43_STATES.json"
    if live.exists():
        lines = json.loads(live.read_text())["lines"]
    A.main((["--lines", str(live)] if lines is not None else []) + ["--out", str(tmp_path)])
    for name in ("FORMWORK_LINE_MAP_T474.csv", "summary_t474.json"):
        assert (tmp_path / name).read_text() == (out / name).read_text(), name


def test_line_ids_are_the_engine_formula():
    A = _load("t474_alsenan")
    sys.path.insert(0, str(ROOT))
    from engine.source import boq_line as BL
    rows, _ = A.build()
    r = rows[0]
    assert r["line_id"] == BL.line_id("development-villa-t131", r["item_code"], r["element_id"], "R-T199-1", "T-199",
                                      "m2")
    # the map's classes come only from the R-T474-1 piece classes
    for r in rows:
        for c in r["classes"].split():
            cls, kind = c.split(":")[0].split("/")
            assert cls in R.PIECE_CLASSES and kind in R.PIECE_CLASSES[cls]


def test_live_v3_0_43_map_pins():
    """the committed reduced states of an own V3.0.43 reproduction (candidate of record 6f534d5e)."""
    A = _load("t474_alsenan")
    live = json.loads((HERE / "out" / "LIVE_V3_0_43_STATES.json").read_text())
    assert live["boq_lines_json_sha256"].startswith("6f534d5e")
    rows, s = A.build(live["lines"])
    fw, st = s["by_code"]["STR.FORMWORK"], s["by_code"]["STR.FORMWORK.STAIR"]
    assert (fw["valued"], fw["blank"], fw["valued_m2"]) == (244, 368, 1027.977403)      # = T-471 matrix C-B10-13
    assert (st["valued"], st["blank"], st["valued_m2"]) == (10, 21, 36.927436)          # = C-B7-13
    d = s["binding_drift"]
    assert len(d["dependent_held"]) == 10 and d["dependent_held_m2"] == 0.928054       # V3.0.33 DEPENDENT_HELD
    assert round(1028.905457 - d["dependent_held_m2"], 6) == fw["valued_m2"]
    assert len(d["valued_on_restated_concrete"]) == 4                                   # T-392 restated beams
    assert s["by_basis"]["VERIFIED_GEOMETRY"] == {"lines": 62, "m2": 375.0481}
    # no valued formwork beside a concrete line outside the valued states
    by = {ln["line_id"]: ln for ln in live["lines"]}
    for r in rows:
        if r["m2_live"] and r["concrete_line"]:
            assert by[r["concrete_line"]]["evidence_state"] in A.VALUED
