"""T-414 FLOOR_BED_V1: B3-05 floor screed / cement bed per room, the layer between the structural top and the floor finish
(any villa; research module, read by no method).

Physical element (ERS s.2 step 1): the cement-sand layer laid on the structural slab (or on the membrane of a wet room)
under the floor finish of one room. It is one layer of the floor build-up b = FFL - structural top (T-214
FLOOR_BUILDUP_V1); the other layers of b are the finish (tile / stone) and its adhesive. So, physically,

    t_layer = b - t_finish - t_adhesive          (metres, per room)

and the layer's INSTALLED volume is area x t_layer. Procurement (cement bags, sand, waste) is a separate, later view
(engine/source/finish_materials_table.py, T-086) and is never mixed into the installed quantity.

What the layer IS by space (owner Q-41, 2026-10-19 20:45, his words "if it is roof or balconies it is screed;
bathrooms, cement is enough"), the CONTRACT form kept apart from the physical layer:

    DRY room        MORTAR_BED  cement-sand bed under the tiles (Q-45: 0.03 .. 0.04 m)          family B3-05
    WET room        MORTAR_BED  cement bed only ('bartash', Q-45: 0.04 .. 0.06 m, falls 1 %);    family B3-05
                                no separate falls / protection screed line (Q-41)
    BALCONY         SCREED      its own line over the membrane (Q-41), thickness not given      family B3-05
    ROOF / TERRACE  owned by B13-01 roof build-up (T-321 / T-328)                               NOT this family
    STAIR           owned by the stair marble bed (B7, Q-45 stairs 3 cm 1:3)                    NOT this family
    POOL            owned by the pool build-up (T-309)                                          NOT this family
    FOUNDATION      owned by the foundation screed / blinding (T-219 / T-353)                   NOT this family
    OUTDOOR_GROUND  paving on ground (court interlock, side walk): bedding of B13-02             NOT this family

Thickness, two methods side by side (ERS s.2 step 2), never merged into one number:

  DRAWING-DERIVED: t_layer = b - t_finish - t_adhesive with b from FLOOR_BUILDUP_V1 for this room's OWN zone type and
     level (a sunken wet room has its own level: b_dry is never carried to it), t_finish only as printed or ruled.
     b known and t_finish printed -> DRAWING-CONFIRMED value; b known, t_finish not printed -> HELD with the bound
     0 < t_layer <= b - t_adhesive_min (the drawn levels bound it, a value is never chosen inside the bound);
     b HELD -> HELD, no bound (UNKNOWN thickness, never 0).
  OWNER MANUAL: the owner's bed range for the space kind (Q-45), ASSUMED — OWNER-APPROVED at its own scope
     (MORTAR_BED), shown as m3 low .. high; checked against the drawn b: owner_hi + adhesive_min <= b -> CONSISTENT
     (the residual is the finish slot); owner_lo + adhesive_min > b -> CONFLICT (the owner bed cannot fit the drawn
     build-up); otherwise PARTLY_CONSISTENT. A balcony screed has no owner thickness: HELD (Q-41).

Refusals (raise ValueError): a thickness without a source (DEFAULTED_THICKNESS); a room of a roof / stair / pool /
foundation / outdoor-ground kind offered as a B3-05 row (OWNED_ELSEWHERE: one layer, one item); the same element in two
rows; an area of 0 offered for a HELD area (HELD_AS_ZERO); a sunken room given the dry floor's b (STEPPED_SLAB_NOT_OWN_LEVEL);
units other than m / mm.
"""
from __future__ import annotations

METHOD = "FLOOR_BED_V1"
FAMILY = "B3-05"
KINDS_IN = ("DRY", "WET", "BALCONY")
KINDS_OWNED_ELSEWHERE = {"ROOF": "B13-01 roof build-up (T-321 / T-328)", "TERRACE": "B13-01 roof build-up (T-321 / T-328)",
                         "STAIR": "B7 stair marble bed (Q-45 stairs)", "POOL": "pool build-up (T-309)",
                         "FOUNDATION": "foundation screed / blinding (T-219 / T-353)",
                         "OUTDOOR_GROUND": "B13-02 external paving bedding"}
LAYER = {"DRY": "MORTAR_BED", "WET": "MORTAR_BED", "BALCONY": "SCREED"}
OWNER_BED = {  # owner Q-45 answer B (2026-10-19 21:40), his own ranges; Q-41 for the balcony screed
    "DRY": {"lo": 0.03, "hi": 0.04, "rule": "Q-45 (owner 2026-10-19 21:40): regular floors 3-4 cm cement mix"},
    "WET": {"lo": 0.04, "hi": 0.06, "rule": "Q-45 (owner 2026-10-19 21:40): bathrooms 4-6 cm, falls 1 %"},
}
OWNER_HELD = {"BALCONY": "SCREED_THICKNESS_NOT_GIVEN (owner Q-41: screed on balconies, thickness not given)"}
ADHESIVE = {"lo": 0.0, "hi": 0.003, "rule": "Q-45 (owner photo of the adhesive bag): layer up to 3 mm"}
STATUS_OWNER = "ASSUMED — OWNER-APPROVED"
TOL = 0.0005
SCALE = {"m": 1.0, "mm": 0.001}


def _r(v, n=6):
    return None if v is None else round(v + 0.0, n)


def _num(v, what, k=1.0):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{what}: a number is required, got {v!r}")
    return float(v) * k


def _ref(r, what):
    if not isinstance(r, str) or not r.strip():
        raise ValueError(f"{what}: DEFAULTED_THICKNESS: a value without a source reference is refused")
    return r


def _area(room, what):
    """Released area of the room's floor-finish line, or None when the line is HELD (never 0 for HELD)."""
    st = room.get("area_status")
    a = room.get("area_m2")
    if st in ("HELD", "UNKNOWN", "BLOCKED_RFI", "BOUNDED"):
        if a is not None and abs(float(a)) < TOL:
            raise ValueError(f"{what}: HELD_AS_ZERO: a held area is not 0 (state {st})")
        return None
    if st not in ("VERIFIED", "DRAWING-CONFIRMED", STATUS_OWNER, "PROVISIONAL", "RELEASED"):
        raise ValueError(f"{what}: unknown area status {st!r}")
    a = _num(a, f"{what} area_m2")
    if a <= 0:
        raise ValueError(f"{what}: a released area must be positive, got {a}")
    return a


def _drawing(room, k, what):
    """Drawing-derived layer thickness: value, bound or HELD; b must be the room's own zone."""
    bu = room.get("build_up") or {}
    if room.get("sunken") and bu.get("zone_type") not in ("SUNKEN", None):
        raise ValueError(f"{what}: STEPPED_SLAB_NOT_OWN_LEVEL: a sunken room takes its own build-up, "
                         f"not the {bu.get('zone_type')} zone's")
    if room["kind"] == "WET" and bu.get("zone_type") == "DRY":
        raise ValueError(f"{what}: STEPPED_SLAB_NOT_OWN_LEVEL: a dry-zone build-up is never carried to a wet room")
    b = bu.get("b")
    if b is None:
        return {"status": "HELD", "t_value": None, "t_bound": None, "b": None,
                "missing": [bu.get("missing") or "the build-up b of this room's own zone (FFL - structural top)"]}
    b = _num(b, f"{what} build_up.b", k)
    _ref(bu.get("ref"), f"{what} build_up")
    if bu.get("status") not in ("VERIFIED", "DRAWING-CONFIRMED"):
        raise ValueError(f"{what}: build-up status {bu.get('status')!r} cannot bound a layer")
    fin = room.get("finish_thickness")
    if fin is None:
        hi = b - ADHESIVE["lo"]
        return {"status": "HELD", "t_value": None, "t_bound": [0.0, _r(hi, 4)], "b": _r(b, 4),
                "missing": ["the finish (tile / stone) thickness: printed nowhere, no owner rule"]}
    t_fin = _num(fin.get("value"), f"{what} finish_thickness", k)
    _ref(fin.get("ref"), f"{what} finish_thickness")
    lo, hi = b - t_fin - ADHESIVE["hi"], b - t_fin - ADHESIVE["lo"]
    if hi <= TOL:
        return {"status": "CONFLICT", "t_value": None, "t_bound": None, "b": _r(b, 4),
                "missing": [f"finish {t_fin:.3f} m fills the whole build-up {b:.3f} m: no room for a bed"]}
    return {"status": bu["status"], "t_value": None, "t_bound": [_r(max(lo, 0.0), 4), _r(hi, 4)], "b": _r(b, 4),
            "missing": [] if hi - lo <= TOL else ["the adhesive thickness inside 0 .. 3 mm (Q-45)"]}


def _owner(room, b):
    kind = room["kind"]
    if kind in OWNER_HELD:
        return {"status": "HELD", "lo": None, "hi": None, "rule": OWNER_HELD[kind], "check": "NOT_APPLICABLE"}
    o = OWNER_BED[kind]
    row = {"status": STATUS_OWNER, "lo": o["lo"], "hi": o["hi"], "rule": o["rule"], "scope": "MORTAR_BED"}
    if b is None:
        row["check"] = "NOT_CHECKED (drawn build-up HELD)"
    elif o["hi"] + ADHESIVE["lo"] <= b + TOL:
        row["check"] = "CONSISTENT"
        row["finish_slot_m"] = [_r(b - o["hi"] - ADHESIVE["hi"], 4), _r(b - o["lo"] - ADHESIVE["lo"], 4)]
    elif o["lo"] + ADHESIVE["lo"] > b + TOL:
        row["check"] = "CONFLICT"
    else:
        row["check"] = "PARTLY_CONSISTENT"
    return row


def evaluate(project):
    """One row per room; families owned elsewhere are refused as B3-05 rows (listed in 'excluded' only)."""
    k = SCALE.get(project.get("units", "m"))
    if k is None:
        raise ValueError(f"unknown units {project.get('units')!r}")
    rows, seen, excluded = [], set(), []
    for room in project["rooms"]:
        rid = room.get("element_id")
        what = f"room {rid}"
        if not rid:
            raise ValueError("a room needs an element id")
        if rid in seen:
            raise ValueError(f"{what}: counted twice (one layer, one item)")
        seen.add(rid)
        kind = room.get("kind")
        if kind in KINDS_OWNED_ELSEWHERE:
            if room.get("as_b3_05"):
                raise ValueError(f"{what}: OWNED_ELSEWHERE: a {kind} layer belongs to {KINDS_OWNED_ELSEWHERE[kind]}")
            excluded.append({"element_id": rid, "kind": kind, "owner_family": KINDS_OWNED_ELSEWHERE[kind]})
            continue
        if kind not in KINDS_IN:
            raise ValueError(f"{what}: unknown kind {kind!r}")
        if room.get("area_status") == "NOT_APPLICABLE":
            # the finish line itself states, with evidence, that no floor finish exists there: no bed either
            rows.append({"element_id": rid, "floor": room.get("floor"), "kind": kind, "layer": LAYER[kind],
                         "finish_line": room.get("finish_line"), "finish_code": room.get("finish_code"),
                         "area_m2": None, "area_status": "NOT_APPLICABLE", "m2_status": "NOT_APPLICABLE",
                         "ffl": room.get("ffl"), "drawing": {"status": "NOT_APPLICABLE", "b": None},
                         "owner_manual": {"status": "NOT_APPLICABLE", "check": "NOT_APPLICABLE"},
                         "m3_drawing": {"status": "NOT_APPLICABLE"}, "m3_owner": {"status": "NOT_APPLICABLE"}})
            continue
        area = _area(room, what)
        d = _drawing(room, k, what)
        o = _owner(room, d.get("b"))
        row = {"element_id": rid, "floor": room.get("floor"), "kind": kind, "layer": LAYER[kind],
               "finish_line": room.get("finish_line"), "finish_code": room.get("finish_code"),
               "area_m2": _r(area, 4), "area_status": room.get("area_status") if area is not None else "HELD",
               "ffl": room.get("ffl"), "drawing": d, "owner_manual": o}
        if area is None:
            row["m3_drawing"] = {"status": "HELD", "missing": ["the room's floor-finish area"]}
            row["m3_owner"] = {"status": "HELD", "missing": ["the room's floor-finish area"]}
        else:
            if d.get("t_bound") and d["status"] in ("VERIFIED", "DRAWING-CONFIRMED"):
                # finish printed: the layer is the build-up less a printed finish, a range only by the adhesive
                row["m3_drawing"] = {"status": d["status"], "range": [_r(area * d["t_bound"][0], 4),
                                                                       _r(area * d["t_bound"][1], 4)],
                                     "residual": d["missing"]}
            elif d.get("t_bound"):
                row["m3_drawing"] = {"status": "HELD", "bound": [_r(area * d["t_bound"][0], 4),
                                                                  _r(area * d["t_bound"][1], 4)],
                                     "missing": d["missing"]}
            else:
                row["m3_drawing"] = {"status": "HELD", "bound": None, "missing": d["missing"]}
            if o["lo"] is None:
                row["m3_owner"] = {"status": "HELD", "missing": [o["rule"]]}
            else:
                row["m3_owner"] = {"status": STATUS_OWNER, "low": _r(area * o["lo"], 4), "high": _r(area * o["hi"], 4)}
        row["m2_status"] = row["area_status"]
        rows.append(row)
    return {"method": METHOD, "family": FAMILY, "rows": rows, "excluded": excluded, "totals": totals(rows)}


def totals(rows):
    """Sums of the valued rows only; HELD rows are counted and listed, never added as 0."""
    out = {}
    for kind in KINDS_IN:
        na = [r["element_id"] for r in rows if r["kind"] == kind and r["area_status"] == "NOT_APPLICABLE"]
        rs = [r for r in rows if r["kind"] == kind and r["area_status"] != "NOT_APPLICABLE"]
        if not rs and not na:
            continue
        val = [r for r in rs if r["area_m2"] is not None]
        own = [r for r in val if r["m3_owner"]["status"] == STATUS_OWNER]
        bnd = [r for r in val if r["m3_drawing"].get("bound")]
        out[kind] = {
            "rooms": len(rs), "rows_not_applicable": na, "rooms_area_valued": len(val), "rooms_area_held": [r["element_id"] for r in rs
                                                                                 if r["area_m2"] is None],
            "m2": _r(sum(r["area_m2"] for r in val), 4),
            "m3_owner_low": _r(sum(r["m3_owner"]["low"] for r in own), 4) if own else None,
            "m3_owner_high": _r(sum(r["m3_owner"]["high"] for r in own), 4) if own else None,
            "m3_owner_rooms": len(own),
            "m3_drawing_bound_high": _r(sum(r["m3_drawing"]["bound"][1] for r in bnd), 4) if bnd else None,
            "m3_drawing_bound_rooms": len(bnd),
            "m3_drawing_range_rooms": sum(1 for r in val if r["m3_drawing"].get("range") is not None),
        }
    return out


def overlap_check(rows, other_lines):
    """other_lines: [{'element_id', 'family', 'layer'}] from the roof / pool / foundation / wet-room membrane ledgers.
    A B3-05 row whose element also carries a screed / bed layer in another family is a double count; a membrane line
    (B8-01 .. B8-03) on the same room is a DIFFERENT layer and is reported, not counted."""
    mine = {r["element_id"]: r for r in rows}
    double, beside = [], []
    for o in other_lines:
        if o["element_id"] not in mine:
            continue
        if o.get("layer") in ("SCREED", "MORTAR_BED", "FALLS_SCREED", "PROTECTION_SCREED"):
            double.append({"element_id": o["element_id"], "family": o["family"], "layer": o["layer"]})
        else:
            beside.append({"element_id": o["element_id"], "family": o["family"], "layer": o.get("layer")})
    return {"double_counted": double, "different_layer_same_room": beside}
