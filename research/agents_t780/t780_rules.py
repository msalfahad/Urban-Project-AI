"""T-780 rule (ROOF_LAYER_AREA_V1, proposed; company roof default owner 2026-11-13 + Q-24 / Q-29 answers).

Physical element: a roof surface = the slab top exposed to the sky inside the parapet inner faces (and the building
wall faces it meets). Every layer of the company build-up (falls screed 7.5 cm average, membrane, 5 cm insulation,
5 cm protection, finish) covers that SAME plan area:

    area = face inside the parapet / wall faces (beam tops included) - footprints of closed upstands standing on it
           (dome bases, skylight openings), each footprint getting an upturn = its perimeter.

Refused: a slab-panel area (panels stop at beam faces, beam tops lost: Checker flag F-V770-1), a finish hatch used as
the layer area (hatch gaps at symbols / door swings / drafting bands are not roof), a missing outline (HELD, never 0).
Any villa: nothing here is Alsenan-specific; the Alsenan figures live in fill_t780.py.
"""
from __future__ import annotations

import math

SCREED_AVG_M = 0.075   # company default roof build-up, falls screed average thickness (owner 2026-11-13)


class RoofRuleError(ValueError):
    pass


def rect_face(inner_x_m, inner_y_m):
    """plan area inside the parapet inner faces of a rectangular roof (m, m) -> m2; missing / non-positive refused"""
    for v in (inner_x_m, inner_y_m):
        if v is None or not isinstance(v, (int, float)) or v <= 0:
            raise RoofRuleError(f"roof side missing or not positive: {v!r} (HELD, never 0)")
    return inner_x_m * inner_y_m


def disc(r_m):
    if r_m is None or r_m <= 0:
        raise RoofRuleError(f"footprint radius missing: {r_m!r}")
    return math.pi * r_m * r_m, 2 * math.pi * r_m


def roof_surface(face_m2, footprints_r_m=(), parapet_inner_lm=None, basis="FACE"):
    """layer area and upturn of one roof surface.

    face_m2: the face inside the parapet / wall faces; basis must be 'FACE' ('SLAB_PANELS' and 'FINISH_HATCH' are refused).
    footprints_r_m: radii of round closed upstands (domes / skylights) standing on the face.
    parapet_inner_lm: length of parapet inner face + building wall face along the edge (upturn), or None (not read).
    """
    if basis != "FACE":
        raise RoofRuleError(f"layer area on basis {basis!r} refused: beam tops / hatch gaps are roof (F-V770-1)")
    if face_m2 is None or face_m2 <= 0:
        raise RoofRuleError("roof face missing: HELD, never 0")
    fp = [disc(r) for r in footprints_r_m]
    a_fp = sum(a for a, _ in fp)
    if a_fp >= face_m2:
        raise RoofRuleError("footprints exceed the face: outline or footprint misread")
    net = face_m2 - a_fp
    up = None if parapet_inner_lm is None else parapet_inner_lm + sum(c for _, c in fp)
    return {"face_m2": face_m2, "footprints_m2": a_fp, "layer_m2": net, "screed_m3": net * SCREED_AVG_M,
            "upturn_lm": up}


def layers_for(surface):
    """the five company layers of one roof surface: every m2 layer = the membrane area; screed m3 = area x 0.075"""
    a = surface["layer_m2"]
    return {"FIN.WP.ROOF": a, "FIN.ROOF.INSULATION": a, "FIN.ROOF.PROTECTION": a, "FIN.ROOF.FINISH": a,
            "FIN.ROOF.SCREED": a * SCREED_AVG_M}
