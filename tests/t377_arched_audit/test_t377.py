"""T-377: R-T377-1 / R-T377-2 (every villa). Non-Alsenan villa T377-M with hand calculations (semicircular window
W-A 1.20 x springing 1.50 + rise 0.60, segmental passage P-B chord 1.00 rise 0.30, rectangular window W-R 1.00 x 1.20),
normal and adverse cases (rectangle refused on an arched opening, band crown refused, held as 0 refused, a figure on a
held outline refused, missing depth, millimetres as metres, impossible arch, mirror), then the development-villa audit
pins (committed inputs only, --check reproduction).

Hand truth, W-A (r = 0.60, semicircle):
  segment = pi r^2 / 2 = 0.565487 m2; arch = pi r = 1.884956 m; hole = 1.20 x 1.50 + 0.565487 = 2.365487 m2
  reveal d 0.10: 0.10 x (2 x 1.50 + 1.884956) = 0.488496 m2   (rectangle to the crown 2.10: 0.10 x (2 x 2.10 + 1.20) = 0.540)
  edge jambs + head 4.884956 m; with sill 6.084956 m           (rectangle 5.400 / 6.600)
  chord 0.10 below the crown (z = 2.00): 2 x sqrt(2 x 0.60 x 0.10 - 0.01) = 0.663325 m; at z <= 1.50: 1.20
P-B (chord 1.00, rise 0.30): r = (0.25 + 0.09) / 0.60 = 0.566667; segment 0.213736 m2; arc 1.224951 m (T-238 hand values).
"""

import importlib.util
import json
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t377")


def _load(name):
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t377_arch_audit")
AL = _load("t377_alsenan")

WA = R.Outline("W-A", 1.20, 1.50, 0.60, math.pi * 0.36 / 2, math.pi * 0.60, band=0.10)
WR = R.Outline("W-R", 1.00, 1.20, 0.0, 0.0, 1.00)


# ---------------------------------------------------------------- hand values (normal cases)
def test_semicircle_outline_by_hand():
    assert WA.hole_m2() == pytest.approx(2.365487, abs=1e-6)
    assert WA.reveal_jambs_head(0.10) == pytest.approx(0.488496, abs=1e-6)
    assert WA.edge_jambs_head() == pytest.approx(4.884956, abs=1e-6)
    assert WA.hole_width_at(2.00) == pytest.approx(0.663325, abs=1e-6)
    assert WA.hole_width_at(1.50) == pytest.approx(1.20)
    assert WA.hole_width_at(0.30) == pytest.approx(1.20)
    assert WA.hole_width_at(2.20) == 0.0


def test_segmental_arch_by_hand():
    a, L = R.circular_segment(1.00, 0.30)
    assert a == pytest.approx(0.213736, abs=1e-6)
    assert L == pytest.approx(1.224951, abs=1e-6)
    # independent strip integration of the same segment
    r = R.circle_radius(1.00, 0.30)
    n, s = 20000, 0.0
    for i in range(n):
        x = -0.5 + (i + 0.5) / n
        s += (math.sqrt(r * r - x * x) - (r - 0.30)) / n
    assert s == pytest.approx(a, abs=1e-6)


def test_outline_values_accepted():
    assert R.check_value(WA, "REVEAL_JAMBS_HEAD", 0.4885, depth=0.10) == "OUTLINE"
    assert R.check_value(WA, "EDGE_WITH_SILL", 6.0850) == "OUTLINE"
    assert R.check_value(WA, "HOLE_AREA", 2.3655) == "OUTLINE"
    assert R.check_value(WA, "HOLE_WIDTH_AT", 0.6633, z=2.00) == "OUTLINE"


def test_rectangular_opening_keeps_its_rectangle():
    # normal case of the rule: a rectangular window's perimeter IS its rectangle
    assert R.check_value(WR, "REVEAL_JAMBS_HEAD", 0.10 * (2 * 1.20 + 1.00), depth=0.10) == "OUTLINE"
    assert R.check_value(WR, "EDGE_JAMBS_HEAD", 3.40) == "OUTLINE"
    assert R.check_value(WR, "HOLE_AREA", 1.20) == "OUTLINE"


def test_width_only_and_window_rule_are_not_rectangle_errors():
    assert R.check_value(WA, "WIDTH_ONLY", 0.12, depth=0.10) == "WIDTH_ONLY"
    assert R.check_value(WA, "WINDOW_UNIT_Q32A", 1.20 * 2.10) == "RULE RECTANGLE (Q-32 A)"


# ---------------------------------------------------------------- adverse cases
def test_arched_reveal_on_the_rectangle_is_refused():
    with pytest.raises(R.AuditError, match="RECTANGLE"):
        R.check_value(WA, "REVEAL_JAMBS_HEAD", 0.540, depth=0.10)


def test_band_crown_as_head_is_refused():
    band = 0.10 * (2 * 2.20 + 1.20)
    assert R.classify(WA, "REVEAL_JAMBS_HEAD", band, depth=0.10) == "RECTANGLE (band crown)"
    with pytest.raises(R.AuditError):
        R.check_value(WA, "REVEAL_JAMBS_HEAD", band, depth=0.10)


def test_arched_perimeter_and_hole_from_rectangle_refused():
    with pytest.raises(R.AuditError):
        R.check_value(WA, "EDGE_JAMBS_HEAD", 5.40)
    with pytest.raises(R.AuditError):
        R.check_value(WA, "HOLE_AREA", 1.20 * 2.10)
    with pytest.raises(R.AuditError):
        R.check_value(WA, "HOLE_WIDTH_AT", 1.20, z=2.00)       # mesh cut at full width inside the arch


def test_unmatched_value_refused():
    with pytest.raises(R.AuditError, match="matches no basis"):
        R.check_value(WA, "EDGE_JAMBS_HEAD", 4.0)


def test_missing_depth_is_held_never_zero():
    with pytest.raises(R.AuditError, match="HELD"):
        R.check_value(WA, "REVEAL_JAMBS_HEAD", 0.4885, depth=None)
    with pytest.raises(R.AuditError):
        R.check_value(WA, "REVEAL_JAMBS_HEAD", 0.0, depth=0.0)


def test_held_outline_stays_held():
    assert R.check_held("W-H", "HELD", None) == "HELD"
    assert R.check_held("W-H", "HELD", 9.86) == "HELD BOUND"
    assert R.check_held("W-H", "DRAWING-CONFIRMED", 8.14, "a merged developed-hole ledger").startswith("DEVELOPED")
    with pytest.raises(R.AuditError, match="0"):
        R.check_held("W-H", "HELD", 0)
    with pytest.raises(R.AuditError, match="HELD outline"):
        R.check_held("W-H", "PRINTED", 10.29)               # the T-162 W17 pattern
    with pytest.raises(R.AuditError, match="blank"):
        R.check_held("W-H", "DRAWING-CONFIRMED", None)


def test_millimetres_and_impossible_arches_refused():
    with pytest.raises(R.AuditError, match="millimetres"):
        R.Outline("W-mm", 1200, 1500, 600, 565487, 1885)
    with pytest.raises(R.AuditError, match="impossible"):
        R.Outline("W-x", 1.20, 1.50, 0.60, 0.50, 1.10)       # arch shorter than its chord
    with pytest.raises(R.AuditError, match="segment"):
        R.Outline("W-y", 1.20, 1.50, 0.60, 0.80, 1.80)       # segment above width x rise
    with pytest.raises(R.AuditError, match="rectangular"):
        R.Outline("W-z", 1.00, 1.20, 0.0, 0.10, 1.00)


def test_mirrored_profile_gives_the_same_chord():
    pts = [(0.6 - 0.6 * math.cos(t * math.pi / 40), 0.6 * math.sin(t * math.pi / 40)) for t in range(41)]
    p1 = R.Outline("W-P", 1.20, 1.50, 0.60, math.pi * 0.36 / 2, math.pi * 0.60, profile=tuple(pts))
    mirror = tuple((1.20 - x, z) for x, z in reversed(pts))
    p2 = R.Outline("W-Pm", 1.20, 1.50, 0.60, math.pi * 0.36 / 2, math.pi * 0.60, profile=mirror)
    for z in (1.60, 1.90, 2.05):
        assert p1.hole_width_at(z) == pytest.approx(p2.hole_width_at(z), abs=1e-9)
        assert p1.hole_width_at(z) == pytest.approx(WA.hole_width_at(z), abs=0.01)   # polyline vs circle


# ---------------------------------------------------------------- development villa (committed inputs only)
def test_alsenan_reproduces_committed_files():
    assert AL.main(["--check"]) == 0


def test_alsenan_d_t326_1_values_and_findings():
    rows = AL.build()
    rev = {r["opening"]: r for r in rows if r["trade"] == "reveal (outside jambs + head)"}
    assert float(rev["W15"]["value_on_outline"]) == pytest.approx(0.5477, abs=1e-4)
    assert float(rev["W26"]["value_on_outline"]) == pytest.approx(0.4071, abs=1e-4)
    assert all(r["basis_used"].startswith("RECTANGLE") for r in rev.values())
    ar = {r["opening"]: r for r in rows if r["trade"].startswith("opening arrises")}
    assert ar["W15"]["basis_used"] == "RECTANGLE (band crown)" and float(ar["W15"]["difference"]) == pytest.approx(0.9039, abs=1e-4)
    assert ar["W26"]["basis_used"] == "RECTANGLE (crown)" and float(ar["W26"]["difference"]) == pytest.approx(0.5291, abs=1e-4)
    # every RECTANGLE row names a lane I carrier; T-326 owns only the reveal lines
    for r in rows:
        if r["basis_used"].startswith("RECTANGLE"):
            assert r["correction_carrier"] not in ("", "none")
    # the outline rows (masonry, interior and exterior holes) agree with the outline within 0.0005 m2
    for r in rows:
        if r["basis_used"] == "OUTLINE" and r["unit"] == "m2":
            assert abs(float(r["difference"])) <= 0.0005


def test_alsenan_held_set_cross_check():
    held = AL.held_check()
    assert {h["opening"] for h in held} == {"W17", "A-GF-01", "A-1F-01"}
    findings = [h for h in held if h["verdict"] != "PASS"]
    assert [(h["opening"], h["ledger"]) for h in findings] == [("W17", "T-162 CORNERS opening arris")]
    s = json.loads(open(os.path.join(HERE, "summary.json"), encoding="utf-8").read())
    assert s["outline_own_reread"]["W15"]["hole_m2"] == pytest.approx(4.3629, abs=1e-4)


def test_candidate_of_record_carries_no_rectangle():
    rows = AL.rd("agents_t377/CANDIDATE_T377.csv")
    assert len(rows) == 33
    assert not [r for r in rows if r["basis"].startswith("RECTANGLE") or r["basis"] == "UNCLASSIFIED"]
    blank = [r for r in rows if r["basis"].startswith("BLANK")]
    assert all(r["quantity"] == "" and r["low"] == "" for r in blank)      # pending carriers blank, never 0
    assert {r["carrier"] for r in blank} == {"T-326 / T-327 reveal and threshold fill", "T-314 exterior plaster / Sigma"}
