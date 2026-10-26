"""T-307 suspended-slab BAR-END CLASSIFICATION (research ledger, lane S; every villa; stdlib only).

Physical element: the END of one bottom bar of a suspended slab panel, where the bar meets the support at the panel
edge. What the bar does there is read from the typical detail of the set (Alsenan: ST p.15 TYP. SLAB ON BEAMS DETAIL),
end by end, BEFORE any length is applied (ERS s.2.1, s.3: notation before arithmetic). A general note's length (p.8
note 9, 40 d / 70 d, the starter-bar note) is never a slab bar-end basis.

What p.15 draws (re-read this run at 600 dpi, line by line; T-306 F-01 and the Checker's T-306 verdict):
  * CONTINUOUS support (a slab on both sides of the beam): 50 % of the bottom bars stop 0.125 L short of the face, the
    balance runs on across the beam (booked as the crossing half of the bottom line). No development, no lap is drawn:
    the end carries 0 m (NOT_APPLICABLE_WITH_EVIDENCE).
  * NON-CONTINUOUS support (an edge beam): BOTH bottom bars run past the beam's inner face to '40 CL.' of its outer face
    (the straight continuing bar ends there; the curtailed bar reaches the same point and turns UP to the top of the
    slab: an up-turn leg drawn, not dimensioned). Straight part = support width along the bar - 0.040 m (DRAWN basis;
    the width is the drawn band); the up-turn leg is a designer item (HELD, never valued). The top anchor bar (0.25 L1)
    hooks down into the edge beam (leg not dimensioned) and the detail prints "EXTEND 50% OF TOP REINF. INTO ADJACENT
    SLAB WHERE POSSIBLE" (dashed): a printed conditional extension of the TOP bars, length not printed.
  * The detail draws a slab on beams at ONE level. No detail draws a bar end at a level step (sunken panel), at an
    opening edge with no beam, against a column / junction piece or across an irregular (oblique / composite) support.

Rules R307-1 .. R307-8 (research rules; no rule-file version; provenance T-152, T-213, T-306, Checker T-306 verdict):
  R307-1  every bar end carries one support class (SUPPORT_CLASSES); an end with no class is refused.
  R307-2  CONTINUOUS / CONTINUOUS_WIDE_BEAM: no development; a length booked there is refused.
  R307-3  EDGE_BEAM (one band crossed square, slab not beyond it): straight part = w - 0.040 m, w the drawn band width
          along the bar; DRAWING_DERIVED length, count still the A / B BOUND of T-306 R306-1. The up-turn leg is HELD;
          a value offered for it is refused. A '(T&B)' top-layer end is HELD (the detail shows no top mesh end).
  R307-4  STEP_EDGE (one side sunken, or two sunken panels whose drops are not printed), OPENING_EDGE (no beam face),
          IRREGULAR_SUPPORT (column / junction piece / oblique or composite band / conflicting mark width): HELD,
          never 0, never a default length.
  R307-5  note 9 (40 d / 70 d) and the owner's 40 d / 60 d lap proposal are refused as a slab bar-end basis.
  R307-6  closure: the candidate development line (2 ends per bar line x 40 d at count A .. 70 d at count B) is
          re-booked end by end on the candidate's own per-end figure; class kg + unbooked opening-segment ends -
          booked = 0 to storage rounding (0.0015 kg per 3 dp figure).
  R307-7  a corrected bound contains every defensible reading of its own line (T-306 R306-6), else refused.
  R307-8  kg internal, t = kg / 1000 once at the export boundary (OWNER_RULE_REBAR_2026-10-24 s.4); summed per class,
          never across statuses.
"""

import math

COVER_END_M = 0.040          # p.15 '40 CL.' (printed)
DEV_K = (40, 70)             # the candidate's note-9 figures (re-booked for closure only, never a basis)
ROUND_TOL = 0.0015

SUPPORT_CLASSES = {
    "CONTINUOUS": ("NOT_APPLICABLE_WITH_EVIDENCE", "p.15: slab on both sides; 50 % stop 0.125 L short, 50 % run on "
                   "(crossing half of the bottom line); no development drawn"),
    "CONTINUOUS_WIDE_BEAM": ("NOT_APPLICABLE_WITH_EVIDENCE", "slab beyond a beam band wider than the T-152 probe "
                             "(0.80 m): p.15 continuous case; T-152 booked it as non-continuous (finding)"),
    "EDGE_BEAM": ("DRAWING_DERIVED", "p.15 non-continuous: straight to 40 mm clear of the far face (w - 0.040); "
                  "curtailed bar turns up (leg not dimensioned, HELD)"),
    "STEP_EDGE": ("HELD", "continuous on plan but at a sunken-panel level step (drop not printed, D-41); no detail "
                  "draws a bar end at a step"),
    "OPENING_EDGE": ("HELD", "no beam face beyond the slab edge (opening / free edge); no detail draws this end"),
    "IRREGULAR_SUPPORT": ("HELD", "column / junction piece / oblique or composite band / band width in conflict with "
                          "the schedule: p.15 draws a slab on one square beam only"),
}


def kgm(d_mm):
    """unit mass d^2 / 162 kg/m (the project method, as the candidate lines)."""
    return d_mm * d_mm / 162.0


def end_basis(support, d_mm, w_m=None, length_m=None, upturn_leg_m=None, basis=None, layer="BOTTOM"):
    """R307-1 .. R307-5 -> dict(status, straight_m, upturn) for one bar end.
    basis: None (read from the detail) | 'NOTE9' | 'LAP_40D_60D' | 'DEV' (any development length offered)."""
    if support not in SUPPORT_CLASSES:
        raise ValueError(f"SUPPORT_CLASS_REFUSED: bar end with support class {support!r} (R307-1)")
    if basis == "LAP_40D_60D":
        raise ValueError("LAP_PROPOSAL_REFUSED: the owner 40 d / 60 d lap method is a proposal (OWNER_RULE_REBAR "
                         "s.2), not a slab bar-end basis (R307-5)")
    if basis == "NOTE9":
        raise ValueError("NOTE9_BASIS_REFUSED: note 9 (40 d / 70 d) names starter bars; the slab bar end is read "
                         "from the typical detail (R307-5)")
    if upturn_leg_m is not None:
        raise ValueError("UPTURN_LEG_VALUE_REFUSED: the up-turn leg is drawn but not dimensioned (designer item, "
                         "R307-3)")
    status, why = SUPPORT_CLASSES[support]
    if support in ("CONTINUOUS", "CONTINUOUS_WIDE_BEAM"):
        if basis is not None or length_m not in (None, 0, 0.0):
            raise ValueError("CONTINUOUS_END_LENGTH_REFUSED: the typical detail draws no development at a continuous "
                             "support (R307-2)")
        return dict(support=support, status=status, straight_m=0.0, upturn="NONE", why=why)
    if length_m is not None or basis is not None:
        raise ValueError("UNDRAWN_LENGTH_REFUSED: a bar-end length offered with no drawn source (R307-3 / R307-4)")
    if support == "EDGE_BEAM":
        if layer == "TOP_OF_TB":
            return dict(support=support, status="HELD", straight_m=None, upturn="NONE",
                        why="(T&B) top-layer end: p.15 draws no top-mesh end at an edge beam")
        if w_m is None:
            raise ValueError("EDGE_BEAM end without its drawn support width")
        if w_m > 5.0:
            raise ValueError(f"UNIT_REFUSED: support width {w_m} reads as mm, not m")
        if w_m <= COVER_END_M:
            raise ValueError(f"support width {w_m} m not wider than the 40 mm end cover")
        return dict(support=support, status=status, straight_m=w_m - COVER_END_M, upturn="HELD", why=why)
    return dict(support=support, status=status, straight_m=None, upturn="NONE", why=why)


def candidate_end_kg(d_mm, layers):
    """the candidate's own per-end figures (low at 40 d, high at 70 d), for closure only (R307-6)."""
    u = kgm(d_mm) * layers
    return DEV_K[0] * d_mm / 1000.0 * u, DEV_K[1] * d_mm / 1000.0 * u


def close_line(line_id, cand_low, cand_high, ends_A, ends_B, bars_A, bars_B, d_mm, layers):
    """R307-6. ends_X: dict class -> number of ends at reading X (all segment ends). The candidate books 2 ends per
    bar line; ends beyond that (bar lines cut by an opening) are unbooked. Returns per-class kg + the unbooked kg; the
    residual against the candidate figures must be storage rounding only."""
    lo_e, hi_e = candidate_end_kg(d_mm, layers)
    nA, nB = sum(ends_A.values()), sum(ends_B.values())
    if nA < 2 * bars_A or nB < 2 * bars_B:
        raise ValueError(f"{line_id}: fewer ends than 2 per bar line")
    cls_lo = {k: v * lo_e for k, v in ends_A.items()}
    cls_hi = {k: v * hi_e for k, v in ends_B.items()}
    unb_lo, unb_hi = (nA - 2 * bars_A) * lo_e, (nB - 2 * bars_B) * hi_e
    r_lo = sum(cls_lo.values()) - unb_lo - cand_low
    r_hi = sum(cls_hi.values()) - unb_hi - cand_high
    if abs(r_lo) > 2 * ROUND_TOL or abs(r_hi) > 2 * ROUND_TOL:
        raise ValueError(f"{line_id}: end census does not close the candidate line ({r_lo:+.6f} / {r_hi:+.6f} kg)")
    return dict(class_low=cls_lo, class_high=cls_hi, unbooked_low=unb_lo, unbooked_high=unb_hi,
                rounding_low=r_lo, rounding_high=r_hi)


def contains(line_id, low, high, readings, tol=ROUND_TOL):
    """R307-7: every reading inside [low, high]; a bound that excludes one is refused."""
    bad = {k: v for k, v in readings.items() if v < low - tol or v > high + tol}
    if bad:
        raise ValueError(f"BOUND_EXCLUDES_READING_REFUSED: {line_id} [{low}, {high}] excludes {bad}")
    return True


def straight_bound(ext_A, ext_B, d_mm, layers_valued=1):
    """R307-3: the valued straight part of a line from the summed straight lengths (m) of its EDGE_BEAM ends at
    readings A and B (bottom layer only). Low / high = min / max over the two count readings (a skewed panel can have
    B below A, T-306 F-03). -> (low_kg, high_kg)."""
    u = kgm(d_mm) * layers_valued
    a, b = ext_A * u, ext_B * u
    return min(a, b), max(a, b)


def proposed_status(classes_present):
    """lane I consumer shape: the proposed status of a re-based development line from the support classes of its ends."""
    cl = set(classes_present)
    if not cl:
        raise ValueError("line with no ends")
    if cl <= {"CONTINUOUS", "CONTINUOUS_WIDE_BEAM"}:
        return "NOT_APPLICABLE_WITH_EVIDENCE"
    if "EDGE_BEAM" in cl:
        return "BOUND_PART_WITH_HELD"      # the straight part is valued; the up-turn leg (and any held end) is HELD
    return "HELD"


def per_bar_extremes(bar_exts):
    """per-bar straight length (sum of its valued ends) -> (min, max); used for the bare-label '5 in all' reading."""
    if not bar_exts:
        return None
    return min(bar_exts), max(bar_exts)


def tonnes(kg):
    """R307-8: once, at the export boundary."""
    return kg / 1000.0


def isclose(a, b, tol=1e-6):
    return math.isclose(a, b, abs_tol=tol)
