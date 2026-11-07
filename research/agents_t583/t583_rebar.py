"""T-583 DOME / RING / LIFT-WALL reinforcement: the components T-575 left HELD (laps / joints, ring links, ring side
bars, anchorage) bounded from the drawings, and the lift-wall bar counts restated so the low is strict
(DOME_LIFT_REBAR_COMPONENTS_V1; R-T583-1 .. 6; every villa; research, unwired; stdlib + T-575 module, read only).

Physical elements (ERS s.2.1):
  * a BAR POPULATION printed as n per metre (maximum spacing s = 1 / n) across a free length L between two supports;
  * a ROW population over an unprinted height h (lift-pit horizontals);
  * a LINK: one closed bar round the mains of a ring section, centreline path, its closing hooks a separate item;
  * a SIDE BAR: a longitudinal bar on a ring face between the top and bottom layers;
  * an ANCHORAGE LEG: the drawn part of a bar inside the supporting member (shell meridional down into the ring,
    lift vertical down into the raft, the U over the lift-wall top);
  * a JOINT: the place where two pieces of one bar line meet (lap, coupler or weld); a LAP is a joint with an overlap
    length, measured as its own account (owner 2026-10-24 s.4 / s.6 (1)).

R-T583-1  SPACING READINGS (Q-71: first / last bar positions not printed). Over a free length L the admissible counts
          are ceil(L/s) - 1 (both end positions served by the supports), ceil(L/s) (one end), ceil(L/s) + 1 (both
          ends): strict LOW = max(ceil(L/s) - 1, 0), HIGH = ceil(L/s) + 1; 1 + floor(L/s) and floor(L/s) both lie
          inside. A closed loop of length C has exactly ceil(C/s). Counting with one reading only is refused.
R-T583-2  ROWS OVER AN UNPRINTED HEIGHT: rows(h) in [ceil(n h) - 1, ceil(n h) + 1], so kg(h) = A h + B with the
          continuous bounds n h - 1 <= rows <= n h + 2: B_low takes one row OFF, B_high adds two rows.
R-T583-3  PRINTED MINIMUM COVER (ST p.8 note 22, for the member classes it names) is ONE-SIDED: it caps a bar-path
          HIGH (shortest admissible cover -> longest path) and never fixes a value. A member class the note does not
          name, or a face whose class is unclear, takes cover >= 0 for the high. A LOW needs a maximum cover, which is
          never printed: the low is the GEOMETRIC FLOOR (bars in contact inside the link, legs reaching the drawn
          layer), never a typical cover.
R-T583-4  JOINTS AND LAPS. Joint count only where physically certain: a closed loop has >= max(1, ceil(C / S))
          joints, an open run longer than stock S has >= ceil(L / S) - 1 joints (S = 12 m, OD-V3-3 ASSUMED -
          OWNER-APPROVED; with any lap l > 0 the pieces ceil((L - l) / (S - l)) only grow). Lap LENGTH only from a
          PRINTED note that governs that bar group or an ADOPTED owner rule; the owner 40 d / 60 d text of
          OWNER_RULE_REBAR_2026-10-24 s.2 is a PROPOSAL and appears only as a labelled SCENARIO, never in a bound. With
          no length the lap mass LOW is 0 (a coupler or an unknown overlap are both admissible) and the HIGH is HELD
          by name. A reading in which no joint is certain (in-bay segments shorter than stock) has 0 joints.
R-T583-5  ANCHORAGE drawn but not dimensioned: the leg runs inside the drawn member; HIGH = member dimension less the
          R-T583-3 high cover, LOW = geometric floor; a member depth that is not printed gives a HELD high (kg(D)).
R-T583-6  ROW TOTALS: a row's LOW is the sum of every component low (each strict); its HIGH is finite only when every
          component high is bounded, else the row reports high_excluding [the named HELD components]. Nothing is
          valued; t = kg / 1000 once.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t575"))
import t575_rebar as R575  # noqa: E402  (read only: unit mass, sphere geometry, t conversion)

STOCK_M = 12.0
EPS = 1e-9


class T583Error(ValueError):
    pass


def kgm(d_mm: int) -> float:
    return R575.kgm(d_mm)


def to_t(kg, unit: str = "kg") -> float:
    try:
        return float(R575.to_t(kg, unit))
    except R575.T575Error as e:
        raise T583Error(str(e)) from e


# ---- R-T583-1 / -2 ---------------------------------------------------------------------------------------------------
def spacing_readings(L: float, s: float) -> dict:
    if L < 0 or s <= 0:
        raise T583Error("length must be >= 0 and spacing > 0")
    c = math.ceil(L / s - EPS)
    return {"both_supports": max(c - 1, 0), "one_end": c, "both_ends": c + 1,
            "low": max(c - 1, 0), "high": c + 1}


def count_low(L: float, s: float) -> int:
    return spacing_readings(L, s)["low"]


def count_high(L: float, s: float) -> int:
    return spacing_readings(L, s)["high"]


def assert_strict_low(stated_low: float, readings: list):
    """A stated low above any admissible reading is refused (F-C-T575-1)."""
    if any(stated_low > r + EPS for r in readings):
        raise T583Error(f"stated low {stated_low} exceeds an admissible reading {min(readings)}: not a strict low")
    return True


def loop_count(C: float, s: float) -> int:
    return math.ceil(C / s - EPS)


def rows_bounds_continuous(n_per_m: float, h: float) -> tuple:
    """Integer rows ceil(n h) - 1 .. ceil(n h) + 1 lie inside [n h - 1, n h + 2]."""
    return n_per_m * h - 1.0, n_per_m * h + 2.0


# ---- R-T583-3 / -5 ---------------------------------------------------------------------------------------------------
def link_path_high(b: float, D: float, d_link_mm: int, cover_min: float) -> float:
    """Centreline path of a closed link with the printed minimum cover (longest admissible), hooks excluded."""
    dl = d_link_mm / 1000.0
    w, h = b - 2 * cover_min - dl, D - 2 * cover_min - dl
    if w <= 0 or h <= 0:
        raise T583Error("section too small for the cover")
    return 2.0 * (w + h)


def link_path_floor(layers: list, d_link_mm: int) -> float:
    """Geometric floor: the link encloses the widest layer with bars in contact and the top + bottom bars stacked."""
    dl = d_link_mm / 1000.0
    inner_w = max(l["n"] * l["d_mm"] for l in layers) / 1000.0
    inner_h = sum(max(l["d_mm"] for l in layers if l["role"] == role) for role in ("RING_TOP", "RING_BOTTOM")) / 1000.0
    return 2.0 * (inner_w + dl) + 2.0 * (inner_h + dl)


def depth_floor(layers: list, d_link_mm: int, cover_min: float) -> float:
    """Smallest ring depth that holds the drawn top and bottom layers inside links with the printed minimum cover."""
    dl = d_link_mm / 1000.0
    dt = max(l["d_mm"] for l in layers if l["role"] == "RING_TOP") / 1000.0
    db = max(l["d_mm"] for l in layers if l["role"] == "RING_BOTTOM") / 1000.0
    return 2 * cover_min + 2 * dl + dt + db


# ---- R-T583-4 --------------------------------------------------------------------------------------------------------
def joints_closed_loop(C: float, S: float = STOCK_M) -> int:
    return max(1, math.ceil(C / S - EPS))


def joints_open_run(L: float, S: float = STOCK_M) -> int:
    return max(0, math.ceil(L / S - EPS) - 1)


LAP_AUTHORITIES = ("PRINTED", "OWNER_RULE_ADOPTED")


def lap_mass(joints: int, d_mm: int, lap: dict) -> float:
    """lap = {'class': PRINTED | OWNER_RULE_ADOPTED | OWNER_PROPOSAL, 'd_multiple' or 'm', 'source'}."""
    if not isinstance(lap, dict) or lap.get("class") not in LAP_AUTHORITIES:
        raise T583Error("lap length without a printed note or an adopted owner rule: HELD by name (an owner "
                        "proposal is a scenario only, R-T583-4)")
    length = lap["m"] if "m" in lap else lap["d_multiple"] * d_mm / 1000.0
    return joints * length * kgm(d_mm)


def lap_scenario(joints: int, d_mm: int, d_multiple: int, source: str) -> dict:
    """Labelled scenario (never in a bound, never valued)."""
    length = d_multiple * d_mm / 1000.0
    return {"label": "OWNER_PROPOSAL_SCENARIO", "source": source, "d_multiple": d_multiple, "lap_m": length,
            "joints": joints, "kg": joints * length * kgm(d_mm), "in_bound": False}


def lap_group(name: str, joints_low: int, d_mm: int, why: str, scenario_multiple: int | None = None,
              scenario_src: str = "") -> dict:
    g = {"group": name, "status": "HELD_HIGH", "d_mm": d_mm, "joints_at_least": joints_low, "kg_low": 0.0,
         "kg_high": None, "t": [0.0, None], "why": why}
    if scenario_multiple and joints_low:
        g["scenario"] = lap_scenario(joints_low, d_mm, scenario_multiple, scenario_src)
    return g


# ---- R-T583-6 --------------------------------------------------------------------------------------------------------
def row_total(groups: list) -> dict:
    lo = 0.0
    hi = 0.0
    excl = []
    for g in groups:
        if g.get("kg_low") is None:
            raise T583Error(f"{g['group']}: a component without a low is never 0; give its floor or HELD formula")
        lo += g["kg_low"]
        if g.get("kg_high") is None:
            excl.append(g["group"])
        else:
            hi += g["kg_high"]
    return {"kg_low": lo, "kg_high_bounded_part": hi, "high_excluding": excl,
            "high_status": "BOUNDED" if not excl else "HELD_HIGH"}
