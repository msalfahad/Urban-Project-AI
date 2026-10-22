"""T-185 dome scenarios: approved design (S0) vs client-requested change (S1) vs consultant revision (S2).

Pure, stdlib-only research module (not wired into any method; nothing released). Two parts:

1. Geometry and bar population of a spherical-cap dome shell from PRINTED values only (chord at the springing plane,
   rise from the springing plane to the outer apex, shell thickness normal to the surface). Exact solid between two
   concentric spheres above the springing plane; surface areas of the extrados, intrados and mid-surface; shell bars
   counted by population (hoops along the meridian, meridians round the springing circle), never a kg/m2 rate.
   A value the drawings do not print is None and every quantity that needs it is HELD (never a default, never 0).

2. Scenario ledger (owner rule 2026-10-22, ENGINEERING_REASONING_STANDARD lessons row "Dome lines removed from the BOQ
   after a client request"): a change requested by the client but NOT issued by the consultant never edits the
   approved-design baseline S0. S1 (client-requested) is built beside S0 and is never released; S2 (consultant
   revision) exists only when a revised drawing reference is supplied, otherwise it is UNKNOWN.

Units: every length in the input carries `unit` ("m" or "mm"); outputs are m, m2, m3, kg.
Unit mass: engine/source/rebar_unit_mass.py method D2_OVER_162 (the project method of the merged slab / stair / pool
ledgers), imported by path so this file stays importable from tests without the engine package on sys.path.

CLI: python -I t185_dome_scenarios.py <ALSENAN_DOME_INPUT.json> [--json OUT.json]
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("rebar_unit_mass", _ROOT / "engine" / "source" / "rebar_unit_mass.py")
_rum = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rum)
UNIT_MASS = {"method": _rum.D2_OVER_162, "authority": "project method of the merged ledgers (T-152 / T-166 / T-183)"}

SCENARIOS = ("S0_APPROVED_DESIGN", "S1_CLIENT_REQUESTED", "S2_CONSULTANT_REVISED")
HELD, UNKNOWN, CALC, CONFIRMED, OMITTED = "HELD", "UNKNOWN", "CALCULATED", "DRAWING-CONFIRMED", "OMITTED_BY_SCENARIO"


class DomeInputError(ValueError):
    pass


def _m(value, unit):
    if value is None:
        return None
    if unit == "m":
        return float(value)
    if unit == "mm":
        return float(value) / 1000.0
    raise DomeInputError(f"unit must be 'm' or 'mm', got {unit!r}")


def kg_per_m(d_mm):
    return _rum.kg_per_m(d_mm, UNIT_MASS)


# ---------------------------------------------------------------- 1. shell geometry from printed values

def cap_volume(R, h):
    """volume of a spherical cap of sphere radius R and height h (h may exceed R: more than a hemisphere)."""
    return math.pi * h * h * (3.0 * R - h) / 3.0


def shell_geometry(chord, rise, t):
    """chord = OUTER chord at the springing plane, rise = springing plane to the OUTER apex, t = shell thickness
    normal to the surface (concentric spheres). Returns None for every value when one input is None."""
    if chord is None or rise is None:
        return None
    if chord <= 0 or rise <= 0:
        raise DomeInputError("chord and rise must be positive")
    a = chord / 2.0
    R_o = (a * a + rise * rise) / (2.0 * rise)
    d = R_o - rise                       # signed distance of the sphere centre BELOW the springing plane
    g = {"R_outer_m": R_o, "centre_below_springing_m": d, "outer_area_m2": 2.0 * math.pi * R_o * rise,
         "springing_outer_radius_m": a}
    if t is None:
        g.update({"R_inner_m": None, "inner_area_m2": None, "mid_area_m2": None, "volume_m3": None})
        return g
    if not 0 < t < rise:
        raise DomeInputError("shell thickness must be positive and smaller than the rise")
    R_i = R_o - t
    h_i = R_i - d                        # inner apex above the springing plane
    if h_i <= 0:
        raise DomeInputError("inner surface does not reach above the springing plane")
    R_mid = R_o - t / 2.0
    g.update({"R_inner_m": R_i, "inner_rise_m": h_i, "inner_area_m2": 2.0 * math.pi * R_i * h_i,
              "mid_area_m2": 2.0 * math.pi * R_mid * (R_mid - d),
              "volume_m3": cap_volume(R_o, rise) - cap_volume(R_i, h_i),
              "springing_inner_radius_m": math.sqrt(R_i * R_i - d * d)})
    return g


def shell_bars(chord, rise, R_bar, spacing, d_mm, stock_m=None):
    """One mesh on the sphere of radius R_bar (concentric with the shell). HOOPS: equal spacing <= `spacing` along the
    meridian from the springing circle up (the apex point has no length): N = ceil(s / spacing) hoops at u_k = k s / N,
    k = 0 .. N-1. MERIDIANS: M = ceil(springing circumference / spacing), each from the springing circle to the apex
    (a bar drawn crown to crown = two of them). Laps, anchorage legs and crown curtailment are NOT included (none is
    dimensioned); `stock_m` only COUNTS the hoops longer than one stock bar, which then need a lap that stays HELD."""
    a = chord / 2.0
    R_o = (a * a + rise * rise) / (2.0 * rise)
    d = R_o - rise
    if not d < R_bar:
        raise DomeInputError("bar sphere lies below the springing plane")
    phi_s = math.acos(d / R_bar)          # polar angle of the springing circle from the apex
    s = R_bar * phi_s                    # meridian arc, springing -> apex
    N = math.ceil(s / spacing - 1e-9)
    hoops = [2.0 * math.pi * R_bar * math.sin(phi_s * (1.0 - k / N)) for k in range(N)]
    r_spr = math.sqrt(R_bar * R_bar - d * d)
    M = math.ceil(2.0 * math.pi * r_spr / spacing - 1e-9)
    w = kg_per_m(d_mm)
    out = {"R_bar_m": R_bar, "meridian_arc_m": s, "hoop_count": N, "hoop_length_m": sum(hoops),
           "hoop_kg": sum(hoops) * w, "meridian_count": M, "meridian_length_m": M * s, "meridian_kg": M * s * w,
           "springing_bar_radius_m": r_spr, "kg_per_m": w}
    # lower bound if the meridians were curtailed continuously so that no gap exceeds `spacing` anywhere:
    # bar length per unit area of the bar sphere = 1 / spacing (crown curtailment is not detailed: HELD range)
    lb = 2.0 * math.pi * R_bar * (R_bar - d) / spacing
    out.update({"meridian_length_curtailed_lb_m": lb, "meridian_kg_curtailed_lb": lb * w})
    out["total_kg"] = out["hoop_kg"] + out["meridian_kg"]
    out["total_kg_curtailed_lb"] = out["hoop_kg"] + out["meridian_kg_curtailed_lb"]
    if stock_m is not None:
        out["hoops_longer_than_stock"] = sum(1 for L in hoops if L > stock_m)
    return out


# ---------------------------------------------------------------- 2. scenario ledger

def _line(scn, dome, item, unit, qty, status, basis, released=False):
    if qty is None and status not in (HELD, UNKNOWN):
        raise DomeInputError(f"{dome}/{item}: a missing quantity must be HELD or UNKNOWN, never {status}")
    if status == OMITTED and qty != 0:
        raise DomeInputError("an omitted-by-scenario line carries 0 by design")
    return {"scenario": scn, "dome": dome, "item": item, "unit": unit, "qty": qty, "status": status,
            "basis": basis, "released": bool(released)}


def _s0_lines(dome):
    did, u = dome["id"], dome.get("unit", "m")
    p = dome.get("printed", {})
    chord, rise, t = _m(p.get("chord"), u), _m(p.get("rise"), u), _m(p.get("thickness"), u)
    lines = []
    g = shell_geometry(chord, rise, t) if dome.get("structural_detail") else None
    if g and g["volume_m3"] is not None:
        lines.append(_line("S0_APPROVED_DESIGN", did, "shell concrete", "m3", g["volume_m3"], CONFIRMED,
                           "exact solid between concentric spheres from the printed chord / rise / thickness"))
        lines.append(_line("S0_APPROVED_DESIGN", did, "shell intrados (soffit form / internal finish)", "m2",
                           g["inner_area_m2"], CALC, "2 pi R_i h_i"))
        lines.append(_line("S0_APPROVED_DESIGN", did, "shell extrados (external finish / waterproofing)", "m2",
                           g["outer_area_m2"], CALC, "2 pi R_o h"))
    else:
        why = "no structural detail" if not dome.get("structural_detail") else "a printed size is missing"
        lines.append(_line("S0_APPROVED_DESIGN", did, "shell concrete", "m3", None, HELD,
                           f"{why}: thickness / support not printed; never a default (owner Q-18)"))
        if chord is not None and rise is not None:
            lines.append(_line("S0_APPROVED_DESIGN", did, "shell extrados (architectural outline)", "m2",
                               shell_geometry(chord, rise, None)["outer_area_m2"], CALC,
                               "2 pi R_o h from the architectural chord / rise"))
    bars = dome.get("shell_bars")
    if g and g["volume_m3"] is not None and bars:
        lo = shell_bars(chord, rise, g["R_inner_m"], _m(bars["spacing"], u), bars["d_mm"], bars.get("stock_m"))
        hi = shell_bars(chord, rise, g["R_outer_m"], _m(bars["spacing"], u), bars["d_mm"], bars.get("stock_m"))
        lines.append(_line("S0_APPROVED_DESIGN", did, "shell bars (hoops + meridians, no laps / anchorage)",
                           "kg", [lo["total_kg_curtailed_lb"], hi["total_kg"]], HELD,
                           "bar population; range = mesh at the intrados with meridians curtailed at the maximum "
                           "spacing .. mesh at the extrados with every meridian to the crown (bar position and "
                           "crown curtailment not dimensioned)"))
    for comp in dome.get("held_components", []):
        lines.append(_line("S0_APPROVED_DESIGN", did, comp["item"], comp["unit"], comp.get("candidate"), HELD,
                           comp["reason"]))
    return lines


def scenario_ledger(project):
    """project = {"domes": [...], "changes": [...], "revised_drawings": [...]}.
    A change record: {"dome": id, "requested_by": "client" | "consultant", "kind": "REMOVE_SHELL", "issued_drawing":
    ref or None, "s1_items": [...]}. Only a change with an issued drawing from the consultant may build S2."""
    lines = []
    for dome in project["domes"]:
        lines += _s0_lines(dome)                       # S0 is never edited by any change record
    revised = project.get("revised_drawings") or []
    for ch in project.get("changes", []):
        did = ch["dome"]
        issued = ch.get("requested_by") == "consultant" and ch.get("issued_drawing")
        for s0 in [x for x in lines if x["scenario"] == "S0_APPROVED_DESIGN" and x["dome"] == did]:
            if ch.get("kind") == "REMOVE_SHELL" and (s0["item"].startswith("shell") or s0["item"] in ch.get("also_removes", [])):
                lines.append(_line("S1_CLIENT_REQUESTED", did, s0["item"], s0["unit"], 0,
                                   OMITTED, f"client-requested removal ({ch.get('reference', 'no reference')})"))
        for it in ch.get("s1_items", []):
            st = it.get("status", UNKNOWN if it.get("qty") is None else CALC)
            lines.append(_line("S1_CLIENT_REQUESTED", did, it["item"], it["unit"], it.get("qty"), st, it["basis"]))
        if issued and ch["issued_drawing"] in revised:
            lines.append(_line("S2_CONSULTANT_REVISED", did, "per revised drawing", "", None, HELD,
                               f"measure from {ch['issued_drawing']}"))
        else:
            lines.append(_line("S2_CONSULTANT_REVISED", did, "all items", "", None, UNKNOWN,
                               "no consultant-issued revised drawing"))
    for x in lines:                                    # release guard: only S0 lines may ever be released
        if x["scenario"] != "S0_APPROVED_DESIGN":
            x["released"] = False
    return lines


def totals(lines, scenario, item_prefix, unit):
    """measured sum and the count of HELD / UNKNOWN lines left out of it (never summed as 0)."""
    sel = [x for x in lines if x["scenario"] == scenario and x["item"].startswith(item_prefix) and x["unit"] == unit]
    meas = sum(x["qty"] for x in sel if isinstance(x["qty"], (int, float)) and x["status"] in (CONFIRMED, CALC, OMITTED))
    open_ = [x["dome"] for x in sel if x["status"] in (HELD, UNKNOWN)]
    return {"measured": meas, "open": open_}


def main(argv):
    src = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    led = scenario_ledger(src)
    out = {"lines": led, "unit_mass": UNIT_MASS["method"],
           "S0_shell_m3": totals(led, "S0_APPROVED_DESIGN", "shell concrete", "m3"),
           "S1_shell_m3": totals(led, "S1_CLIENT_REQUESTED", "shell concrete", "m3")}
    text = json.dumps(out, indent=1, ensure_ascii=False)
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
