"""R-T533-1 BLOCK_MODULE_BY_THICKNESS_V1: the installed block module is a property of ONE block product (type and
thickness), never of the wall family; a thickness with no sourced module stays HELD by name.

Physical element. A mortared black (cement) block wall of net laid area A (m2) and thickness t (m) is built of units
with an actual face w x h laid with a bed joint b and a head joint j. One unit plus its joints occupies one MODULE cell
(w + j) x (h + b). Then, for full (solid-unit) bedding:
    units installed       n  = A / ((w + j)(h + b))                                   [nr]
    panel joint mortar    Vm = A t (1 - w h / ((w + j)(h + b)))                       [m3]  (= bed + head joint strips)
    cement / sand         by the owner mix rule of the mortar (Q-78 A: 8 bags 50 kg + 1.1 m3 loose sand per m3)
Check: a course-by-course count (A = L x H with L and H whole multiples of the module) gives the same n and Vm
(L H t - n w h t).

Rule (every villa, every blockwork trade): the module is looked up by (block type, thickness) in a register whose every
entry carries a citation (drawing / block schedule / project specification / owner rule / supplier datasheet or sales
record). A thickness with no entry returns HELD naming the missing datum; the result is never 0 and never the module
of another thickness (the owner's Q-75 answer of 2026-11-02 gives the 20 cm block only: 40 x 19 x 19, 12.5 per m2
only where the installed module is confirmed 40 x 20). Units in metres; a value over 1.0 m for a thickness or a face
is refused as millimetres.
"""
from __future__ import annotations

from dataclasses import dataclass

RULE = "R-T533-1 BLOCK_MODULE_BY_THICKNESS_V1"
MISSING_015 = ("installed face module of the 0.15 m black (cement) block: unit length x height and the joint it is "
               "laid with (block schedule, project specification 04220, or the supplier's datasheet / sales record)")


class ModuleError(ValueError):
    """an input the rule refuses (never turned into a quantity)."""


@dataclass(frozen=True)
class ModuleEntry:
    block_type: str          # 'BLACK' (cement) ...
    thickness_m: float       # 0.15, 0.20 ...
    face_w_m: float          # actual unit length
    face_h_m: float          # actual unit height
    head_joint_m: float      # j
    bed_joint_m: float       # b
    citation: str            # where the module is printed / stated
    status: str              # OWNER_CONFIRMED / PROJECT_DOCUMENT / SUPPLIER_RECORD (never ESTIMATED)


SOURCED = {"OWNER_CONFIRMED", "PROJECT_DOCUMENT", "SUPPLIER_RECORD"}


def _metres(name, v):
    if v is None:
        raise ModuleError(f"{name}: missing")
    v = float(v)
    if not (0.0 < v <= 1.0):
        raise ModuleError(f"{name}={v}: must be in metres, 0 < value <= 1.0 (millimetres refused)")
    return v


def check_entry(e: ModuleEntry):
    for k in ("thickness_m", "face_w_m", "face_h_m"):
        _metres(k, getattr(e, k))
    for k in ("head_joint_m", "bed_joint_m"):
        v = getattr(e, k)
        if v is None or not (0.0 <= float(v) < 0.05):
            raise ModuleError(f"{k}={v}: a joint in metres, 0 <= j < 0.05")
    if not (e.citation or "").strip():
        raise ModuleError("module entry without a citation: refused (no unsourced module)")
    if e.status not in SOURCED:
        raise ModuleError(f"module status {e.status!r} is not a source ({sorted(SOURCED)})")
    return e


def resolve(register, block_type, thickness_m):
    """the entry of exactly this (type, thickness), or a HELD record naming the missing datum. Never another
    thickness: a register holding 0.20 only answers HELD for 0.15."""
    t = _metres("thickness_m", thickness_m)
    hits = [check_entry(e) for e in register
            if e.block_type == block_type and abs(e.thickness_m - t) < 1e-9]
    if len(hits) > 1:
        mods = {(h.face_w_m, h.face_h_m, h.head_joint_m, h.bed_joint_m) for h in hits}
        if len(mods) > 1:
            return {"status": "CONFLICT", "entry": None,
                    "held": f"{block_type} {t:.2f} m: {len(mods)} different sourced modules ("
                            + "; ".join(h.citation for h in hits) + ")"}
    if not hits:
        return {"status": "HELD", "entry": None,
                "held": MISSING_015 if (block_type == "BLACK" and abs(t - 0.15) < 1e-9) else
                f"installed face module of the {t:.2f} m {block_type} block (no sourced entry)"}
    return {"status": "RESOLVED", "entry": hits[0], "held": None}


def per_m2(e: ModuleEntry):
    W, H = e.face_w_m + e.head_joint_m, e.face_h_m + e.bed_joint_m
    kappa = e.face_w_m * e.face_h_m / (W * H)
    return {"module_m": (W, H), "units_per_m2": 1.0 / (W * H), "kappa": kappa,
            "mortar_m3_per_m2": e.thickness_m * (1.0 - kappa)}


def quantities(area_m2, register, block_type, thickness_m, cement_bags_per_m3, sand_m3_per_m3, mix_source):
    """units and panel joint mortar of one laid area; HELD (None, named) when the module or the area is missing."""
    r = resolve(register, block_type, thickness_m)
    out = {"rule": RULE, "block_type": block_type, "thickness_m": float(thickness_m), "area_m2": area_m2,
           "status": r["status"], "held": r["held"], "units_nr": None, "mortar_m3": None,
           "cement_bags": None, "sand_m3": None, "module_m": None, "citation": None}
    if area_m2 is None:
        out.update(status="HELD", held=(r["held"] + "; " if r["held"] else "") + "laid area missing")
        return out
    if float(area_m2) < 0:
        raise ModuleError(f"area {area_m2} m2 < 0")
    if r["status"] != "RESOLVED":
        return out
    if not (mix_source or "").strip() or cement_bags_per_m3 is None or sand_m3_per_m3 is None:
        raise ModuleError("mortar mix without its source: refused")
    p = per_m2(r["entry"])
    vm = float(area_m2) * p["mortar_m3_per_m2"]
    out.update(units_nr=float(area_m2) * p["units_per_m2"], mortar_m3=vm, cement_bags=vm * cement_bags_per_m3,
               sand_m3=vm * sand_m3_per_m3, module_m=p["module_m"], citation=r["entry"].citation)
    return out


def course_layout(L, H, e: ModuleEntry):
    """independent check on a wall whose length and height are whole module multiples: units by course, mortar by
    solid volume less unit volume."""
    p = per_m2(e)
    W, Hm = p["module_m"]
    per_course, courses = L / W, H / Hm
    if abs(per_course - round(per_course)) > 1e-9 or abs(courses - round(courses)) > 1e-9:
        raise ModuleError("course_layout needs L and H in whole modules")
    n = round(per_course) * round(courses)
    return {"units_nr": n, "mortar_m3": L * H * e.thickness_m - n * e.face_w_m * e.face_h_m * e.thickness_m}
