"""MATERIAL SPECIFICATION (M9 S1) - what a material IS, kept apart from how much of it a room needs (generic; stdlib only).

Two kinds today:

    MEMBRANE_SHEET   roll_width_m, roll_length_m, min_side_lap_m, min_end_lap_m (+ corner / penetration detailing)
    TILE             length_m, width_m (+ thickness, pieces_per_box, box_area_m2, pattern, grain_direction)

    membrane(spec_id="MEM-URBAN-DEFAULT-1x10", **overrides) -> validated spec (owner default 1.00 x 10.00 m, lap >= 0.10 m)
    tile(spec_id) / custom_tile(length_m, width_m, **kw)     -> validated tile spec (registry: 120x60, 60x60, 160x80 cm)
    apply_data_sheet(spec, tds)                               -> the spec with the STRICTER lap of owner minimum and data sheet,
                                                                 and the source of every lap value recorded
    compatibility(spec, required_system)                      -> [] or ["ENGINEERING_REVIEW: ..."]

A value the registry does not hold (box size, thickness, corner detail) stays None: it is never filled with a guess,
and every calculator downstream reports what it could not establish because of it.
"""

from __future__ import annotations

import copy

from engine.source import rule_store as RS

MEMBRANE, TILE = "MEMBRANE_SHEET", "TILE"
DEFAULT_MEMBRANE = "MEM-URBAN-DEFAULT-1x10"
OWNER_TILE_SIZES = ("TILE-120x60", "TILE-60x60", "TILE-160x80")
EPS = 1e-9


class SpecError(ValueError):
    pass


def _positive(v, what):
    if v is None or not isinstance(v, (int, float)) or v <= 0:
        raise SpecError(f"{what} must be a positive number (got {v!r})")


def validate(spec):
    k = spec.get("kind")
    if k == MEMBRANE:
        for f in ("roll_width_m", "roll_length_m", "min_side_lap_m", "min_end_lap_m"):
            _positive(spec.get(f), f)
        if spec["min_side_lap_m"] >= spec["roll_width_m"]:
            raise SpecError("the side lap must be smaller than the roll width")
        if spec["min_end_lap_m"] >= spec["roll_length_m"]:
            raise SpecError("the end lap must be smaller than the roll length")
        ra = spec.get("roll_area_m2")
        if ra is not None and abs(ra - spec["roll_width_m"] * spec["roll_length_m"]) > 1e-6:
            raise SpecError("roll_area_m2 disagrees with width x length")
    elif k == TILE:
        _positive(spec.get("length_m"), "length_m")
        _positive(spec.get("width_m"), "width_m")
        for f in ("pieces_per_box", "box_area_m2", "thickness_m"):
            if spec.get(f) is not None:
                _positive(spec[f], f)
        if spec.get("pieces_per_box") and spec.get("box_area_m2"):
            implied = spec["pieces_per_box"] * spec["length_m"] * spec["width_m"]
            if abs(implied - spec["box_area_m2"]) > 0.02 * spec["box_area_m2"]:
                raise SpecError("box_area_m2 disagrees with pieces_per_box x tile area by more than 2 %")
    else:
        raise SpecError(f"unknown material kind {k!r}")
    return spec


def membrane(spec_id=DEFAULT_MEMBRANE, **overrides):
    """the registry membrane, with owner / project overrides recorded (never silently)."""
    s = RS.material_spec(spec_id)
    if s["kind"] != MEMBRANE:
        raise SpecError(f"{spec_id} is not a membrane")
    s["lap_source"] = {"side": f"{s['authority']} ({spec_id})", "end": f"{s['authority']} ({spec_id})"}
    if overrides:
        s["overrides"] = dict(overrides)
        for k, v in overrides.items():
            if k not in s:
                raise SpecError(f"unknown membrane field {k}")
            s[k] = v
        if "roll_width_m" in overrides or "roll_length_m" in overrides:
            s["roll_area_m2"] = s["roll_width_m"] * s["roll_length_m"]
        if "min_side_lap_m" in overrides:
            s["lap_source"]["side"] = "OVERRIDE"
        if "min_end_lap_m" in overrides:
            s["lap_source"]["end"] = "OVERRIDE"
    return validate(s)


def tile(spec_id):
    s = RS.material_spec(spec_id)
    if s["kind"] != TILE:
        raise SpecError(f"{spec_id} is not a tile")
    return validate(s)


def custom_tile(length_m, width_m, *, pieces_per_box=None, box_area_m2=None, thickness_m=None, pattern="STRAIGHT",
                grain_direction=None, name_en=None, name_ar=None):
    s = {"spec_id": f"TILE-CUSTOM-{round(length_m * 100)}x{round(width_m * 100)}", "kind": TILE,
         "name_en": name_en or f"Tile {length_m * 100:g} x {width_m * 100:g} cm", "name_ar": name_ar,
         "length_m": length_m, "width_m": width_m, "thickness_m": thickness_m, "pieces_per_box": pieces_per_box,
         "box_area_m2": box_area_m2, "pattern": pattern, "grain_direction": grain_direction,
         "authority": "CUSTOM_USER_INPUT"}
    return validate(s)


def with_packaging(spec, *, pieces_per_box, source):
    """a tile spec with its box size (from a supplier or product sheet), source recorded."""
    s = copy.deepcopy(spec)
    s["pieces_per_box"] = pieces_per_box
    s["box_area_m2"] = pieces_per_box * s["length_m"] * s["width_m"]
    s["packaging_source"] = source
    return validate(s)


def apply_data_sheet(spec, tds):
    """tds: {"side_lap_m", "end_lap_m", "roll_width_m", "roll_length_m", "source"} (any subset; source required).
    Dimensions come from the data sheet when it gives them; laps take the STRICTER (larger) of the owner minimum and the
    data sheet, and each lap records which one governs."""
    if not tds.get("source"):
        raise SpecError("a data-sheet value needs its source")
    s = copy.deepcopy(spec)
    for f in ("roll_width_m", "roll_length_m"):
        if tds.get(f) is not None:
            s[f] = tds[f]
    s["roll_area_m2"] = s["roll_width_m"] * s["roll_length_m"]
    for side, f in (("side", "min_side_lap_m"), ("end", "min_end_lap_m")):
        key = f"{side}_lap_m"
        if tds.get(key) is None:
            continue
        if tds[key] > s[f] + EPS:
            s[f] = tds[key]
            s.setdefault("lap_source", {})[side] = f"DATA_SHEET ({tds['source']})"
        else:
            s.setdefault("lap_source", {})[side] = (f"OWNER_MINIMUM_GOVERNS (data sheet {tds['source']} gives "
                                                    f"{tds[key]:g} m)")
    s["data_sheet"] = tds["source"]
    return validate(s)


def compatibility(spec, required_system=None):
    """an installation method the selected product cannot do is flagged, never adjusted around."""
    if not required_system:
        return []
    have = (spec.get("system") or "").upper()
    if required_system.upper().split("_")[0] not in have:
        return [f"ENGINEERING_REVIEW: the detail requires {required_system}; the selected product is {spec.get('system')}"]
    return []
