"""T-575 DOME SHELL / DOME RING / LIFT-PIT WALL reinforcement by bar population (DOME_LIFT_REBAR_V1; R-T575-1 .. 6;
every villa; research, unwired; stdlib + engine/source/rebar_unit_mass, read only).

Physical elements (ERS s.2.1):
  * DOME SHELL: a spherical cap (radius R_out, rise h, thickness t, springing chord c) with one orthogonal mesh as
    printed: MERIDIONAL bars (along the meridians, springing to crown) and HOOP bars (horizontal circles) at a printed
    spacing s. The bar surface is a sphere of radius rho concentric with the shell, R_in + d/2 <= rho <= R_out - d/2
    (cover not printed -> the bound, never a default cover).
  * RING BEAM: a closed annulus under / beside the dome edge carrying printed longitudinal bars (count per layer),
    links (per metre) and side bars (per spacing over the depth).
  * LIFT-PIT WALL: RC walls of thickness w between the lift columns, two faces, horizontal bars per metre of height and
    vertical bars per metre of wall length, verticals embedded in the raft.

R-T575-1  SURFACE LENGTH. A dome bar is measured on the bar sphere: meridian arc S = rho * acos(a / rho) (a = distance
          of the sphere centre below the springing plane), hoop length 2 pi rho sin(theta). A plan (flat) length is
          refused: it is not the bar.
R-T575-2  HOOP COUNT by spacing (Q-71): positions along the meridian from the springing, n = 1 + floor(S / s) for a
          first hoop at the springing; the other first-bar offset (s / 2) is the second reading; both are reported
          and the range is min .. max over rho bounds x offsets (no first-bar offset printed).
R-T575-3  MERIDIONAL BARS whose crown curtailment is not printed: LOWER = area / s (at every height the printed
          maximum spacing needs at least circumference / s bars, integrated over the arc: the continuous lower bound),
          UPPER = N0 x S with N0 = ceil(2 pi b / s) bars at the springing all running to the crown. A single value is
          refused while the curtailment is not printed.
R-T575-4  RING LONGITUDINAL BARS: count per layer as printed; length on the ring CENTRELINE (the mean radius of a layer
          spread symmetrically across the width); LOWER = the ring's own in-bay length (own concrete area / width),
          UPPER = the closed circle; every printed ring-position reading is evaluated and the range spans them.
          Laps of a run longer than stock, anchorage into framing members, link and side-bar mass where cover, hooks
          or depth are not printed: HELD BLANK by name (never a typical-detail value, never 0).
R-T575-5  CONFLICTING BAR SOURCES (a member tag + schedule vs a specific detail) are both evaluated as readings and the
          range spans them until the designer settles it; neither is chosen because it is larger or smaller.
R-T575-6  A wall whose height is not printed has NO value: its bars are reported as kg(h) = A x h + B with [A, B]
          bounds from the drawn plan; units kg inside, t = kg / 1000 once (OWNER_RULE_REBAR_2026-10-24 s.1).
"""
from __future__ import annotations

import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "source"))
import rebar_unit_mass as UM  # noqa: E402

UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "OWNER_RULE_REBAR_2026-10-24 / T-575 row (d^2/162)"}
Q6 = Decimal("0.000001")


class T575Error(ValueError):
    pass


def kgm(d_mm: int) -> float:
    return UM.kg_per_m(d_mm, UNIT_MASS)


def d6(x) -> Decimal:
    if x is None:
        raise T575Error("missing value: a held or absent quantity is never 0")
    return Decimal(repr(float(x))).quantize(Q6, rounding=ROUND_HALF_UP)


def to_t(kg, unit: str = "kg") -> Decimal:
    """Reporting boundary, once. Only kg comes in; a value already called t is refused (no double conversion)."""
    if unit != "kg":
        raise T575Error(f"to_t takes kg only (got {unit!r}): kg relabelled or converted twice is refused")
    return d6(float(kg) / 1000.0)


def require_printed(value, what: str):
    """A bar parameter that the drawing does not print stays HELD: giving it a value is refused."""
    if isinstance(value, dict):
        if value.get("printed") is not True:
            raise T575Error(f"{what}: not printed on the drawings; HELD by name, never a typical value")
        return value["value"]
    if value is None:
        raise T575Error(f"{what}: not printed; HELD by name")
    return value


# ---- dome shell ---------------------------------------------------------------------------------------------------
def sphere_from_chord_rise(chord: float, rise: float) -> dict:
    """R = (c^2/4 + h^2) / 2h; a = R - h (centre below the springing plane)."""
    if chord <= 0 or rise <= 0:
        raise T575Error("chord and rise must be positive")
    R = (chord * chord / 4.0 + rise * rise) / (2.0 * rise)
    return {"R_out": R, "a": R - rise}


def bar_sphere(rho: float, a: float) -> dict:
    if rho <= a:
        raise T575Error("bar sphere does not reach the springing plane")
    th = math.acos(a / rho)
    return {"rho": rho, "theta_max": th, "S": rho * th, "b": math.sqrt(rho * rho - a * a),
            "area": 2.0 * math.pi * rho * (rho - a)}


def hoop_lengths(rho: float, a: float, s: float, offset: float = 0.0) -> list:
    g = bar_sphere(rho, a)
    if not (0.0 <= offset < s):
        raise T575Error("first-hoop offset must be in [0, s)")
    n = 1 + math.floor((g["S"] - offset) / s + 1e-12)
    out = []
    for i in range(n):
        si = offset + i * s
        out.append(2.0 * math.pi * rho * math.sin(g["theta_max"] - si / rho))
    return out


def meridional_bounds(rho: float, a: float, s: float) -> dict:
    g = bar_sphere(rho, a)
    n0 = math.ceil(2.0 * math.pi * g["b"] / s - 1e-12)
    return {"n_springing": n0, "S": g["S"], "lower_m": g["area"] / s, "upper_m": n0 * g["S"]}


def plan_length_refused(kind: str):
    if kind != "SURFACE":
        raise T575Error("a dome bar measured on a flat plan length is refused (R-T575-1): measure on the bar sphere")
    return True


def dome_shell(chord, rise, thickness, d_mm, s, length_basis="SURFACE") -> dict:
    plan_length_refused(length_basis)
    sp = sphere_from_chord_rise(chord, rise)
    R_out, a = sp["R_out"], sp["a"]
    R_in = R_out - thickness
    half = d_mm / 2000.0
    rhos = (R_in + half, R_out - half)
    m = kgm(d_mm)
    hoop_m = []
    for rho in rhos:
        for off in (0.0, s / 2.0):
            L = hoop_lengths(rho, a, s, off)
            hoop_m.append({"rho": rho, "offset": off, "n": len(L), "m": sum(L), "max_hoop_m": max(L)})
    mer = [dict(meridional_bounds(rho, a, s), rho=rho) for rho in rhos]
    h_lo, h_hi = min(x["m"] for x in hoop_m), max(x["m"] for x in hoop_m)
    m_lo, m_hi = min(x["lower_m"] for x in mer), max(x["upper_m"] for x in mer)
    return {"R_out": R_out, "a": a, "R_in": R_in, "rho_bounds": rhos, "kg_per_m": m,
            "hoop_readings": hoop_m, "meridional_readings": mer,
            "groups": {
                "SHELL_HOOP": {"status": "HELD_RANGE", "m": [h_lo, h_hi], "kg": [h_lo * m, h_hi * m],
                               "why": "bar radius within the shell (cover not printed) x first-hoop offset"},
                "SHELL_MERIDIONAL": {"status": "HELD_RANGE", "m": [m_lo, m_hi], "kg": [m_lo * m, m_hi * m],
                                     "why": "crown curtailment not printed: area / s .. all bars to the crown"},
            },
            "longest_hoop_m": max(x["max_hoop_m"] for x in hoop_m)}


# ---- ring beam ----------------------------------------------------------------------------------------------------
def ring_mains(layers: list, readings: list) -> dict:
    """layers: [{"role", "n", "d_mm"}] as printed; readings: [{"id", "r_c", "inbay_area", "width"}]."""
    kg_per_m = sum(require_printed(l.get("n"), f"{l['role']} count") * kgm(l["d_mm"]) for l in layers)
    rows = []
    for r in readings:
        full = 2.0 * math.pi * r["r_c"]
        inbay = r["inbay_area"] / r["width"]
        if inbay > full + 1e-9:
            raise T575Error(f"{r['id']}: in-bay length exceeds the closed circle")
        rows.append({"id": r["id"], "inbay_m": inbay, "circle_m": full,
                     "kg": [inbay * kg_per_m, full * kg_per_m]})
    return {"kg_per_m": kg_per_m, "readings": rows,
            "kg": [min(x["kg"][0] for x in rows), max(x["kg"][1] for x in rows)]}


def ring_link_count(per_m: float, length_m: float) -> int:
    """Closed ring: links at 1 / per_m along the centreline, N = ceil(L x rate) (no +1 on a closed loop)."""
    return math.ceil(per_m * length_m - 1e-9)


def link_mass(count: int, path_m, d_mm: int) -> float:
    """Link mass only from a printed path (core perimeter + hooks); otherwise HELD."""
    p = require_printed(path_m, "link path (cover / hooks)")
    return count * p * kgm(d_mm)


# ---- lift-pit walls -----------------------------------------------------------------------------------------------
def count_by_spacing(L: float, s: float) -> int:
    """Q-71 counting with no first-bar offset printed: first and last bar at the segment ends, 1 + floor(L / s)."""
    return 1 + math.floor(L / s + 1e-9)


def pit_walls(segments: list, horiz: dict, vert: dict, top: dict, embed_max: float, return_max: float,
              face_runs_hi: list, top_run_hi: float) -> dict:
    """kg(h) = A h + B with bounds. segments: net wall lengths between columns (same on both faces);
    horiz {'d_mm', 'per_m'} each face; vert {'d_mm', 'per_m'} each face; top {'n', 'd_mm'} along the wall top;
    face_runs_hi: closed bar-line upper bounds per face (outer face line, wall centreline)."""
    net = sum(segments)
    mh, mv, mt = kgm(horiz["d_mm"]), kgm(vert["d_mm"]), kgm(top["d_mm"])
    run_lo, run_hi = 2.0 * net, sum(face_runs_hi)
    n_vert = 2 * sum(count_by_spacing(L, 1.0 / vert["per_m"]) for L in segments)
    A_lo = horiz["per_m"] * run_lo * mh + n_vert * mv
    A_hi = horiz["per_m"] * run_hi * mh + n_vert * mv
    B_lo = top["n"] * net * mt
    B_hi = top["n"] * top_run_hi * mt + n_vert * (embed_max + return_max) * mv + run_hi * mh  # +1 row (n = 1 + floor)
    return {"net_wall_m": net, "n_vertical": n_vert, "A_kg_per_m_height": [A_lo, A_hi], "B_kg": [B_lo, B_hi],
            "horizontal_run_per_row_m": [run_lo, run_hi]}


def pit_walls_value(h):
    """The wall height is the only key: absent -> HELD, never 0."""
    if h is None:
        raise T575Error("pit wall height not printed: HELD (kg(h) formula only), never 0")
    return h
