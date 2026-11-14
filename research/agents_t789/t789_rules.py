"""R-T789-1 (every villa): parapet masonry is the complement of the parapet concrete reading, run by run.

One parapet run = one physical element from the structural slab top to its printed top. Its height above the slab
top is H = h_finish + b_edge (h_finish: printed height above the finished roof, or the company default 1.20 when no
drawing prints one; b_edge: roof build-up at the edge, company default 0.175 = screed 7.5 + insulation 5 + protection
5 cm). The run is split between two trades and never billed in both:
  ALL_RC      -> concrete H, masonry 0 (no masonry line: the element is billed in concrete)
  P1_UPSTAND  -> concrete u (printed RC upstand above the slab top), masonry max(0, H - u)
A printed section height always wins over the default (a lower printed parapet gives a lower masonry figure).
Missing data never becomes 0: a run with no length or no material reading raises.
"""
from __future__ import annotations

DEFAULT_PARAPET_H = 1.20   # company default above the finished roof (owner 2026-11-13)
DEFAULT_B_EDGE = 0.175     # company default roof build-up (owner 2026-11-13)
MATERIALS = ("ALL_RC", "P1_UPSTAND")


def run_split(length_m, t_m, material, h_printed=None, b_edge=DEFAULT_B_EDGE, upstand=None):
    """Return dict(h_label, h_finish, H, conc_m3, block_m2) for one run; raises on missing data."""
    if length_m is None or length_m <= 0:
        raise ValueError("run length missing: HELD, never 0")
    if t_m is None or t_m <= 0:
        raise ValueError("run thickness missing: HELD, never 0")
    if material not in MATERIALS:
        raise ValueError(f"material reading missing or unknown: {material!r} (HELD, never 0)")
    if h_printed is not None:
        if not (0 < h_printed < 5):
            raise ValueError(f"printed height out of range (units?): {h_printed}")
        h, label = float(h_printed), "DRAWING-READ"
    else:
        h, label = DEFAULT_PARAPET_H, "DEFAULT"
    H = h + b_edge
    if material == "ALL_RC":
        conc_h, block_h = H, 0.0
    else:
        if upstand is None or upstand <= 0:
            raise ValueError("P1 reading needs the printed upstand height")
        conc_h = min(upstand, H)
        block_h = max(0.0, H - upstand)
    assert abs(conc_h + block_h - H) < 1e-9, "one run, one height: never in both trades"
    return {"h_label": label, "h_finish": h, "H": H,
            "conc_m3": length_m * t_m * conc_h, "block_m2": length_m * block_h}
