"""Source unit and coordinate contract (PA06 WS1).

Priority: 1 explicit INSUNITS; 2 authored dimension measured value vs
geometry (with a unit suffix in the dimension text or a declared display
unit); 3 declared source metadata; 4 cross-check against a second
independent authored dimension; 5 UNIT_NOT_ESTABLISHED.

A unit is never inferred because the numbers "look like millimetres".
Physical lengths may be consumed downstream only when STATUS is
SOURCE_ESTABLISHED or DECLARED_ESTABLISHED.
"""

from __future__ import annotations

import copy
import dataclasses
import math
import re

INSUNITS = {1: ("in", 25.4), 2: ("ft", 304.8), 4: ("mm", 1.0), 5: ("cm", 10.0), 6: ("m", 1000.0), 3: ("mi", 1.609344e6), 7: ("km", 1e6), 8: ("uin", 2.54e-5),
            9: ("mil", 0.0254), 10: ("yd", 914.4), 14: ("dm", 100.0)}
UNIT_SCALE = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8, "dm": 100.0}
SUFFIX = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m|in|ft)\b", re.I)
ACCEPTABLE = ("SOURCE_ESTABLISHED", "DECLARED_ESTABLISHED")
# plausibility bands in millimetres for villa-scale architecture, used only as a SECONDARY check of a candidate, never to pick a unit
DOOR_SWING_BAND_MM = (600.0, 1400.0)
WALL_THICKNESS_BAND_MM = (50.0, 600.0)


def _dimension_consistency(dims, tol=0.005):
    """Authored (non-overridden) linear dimensions whose display value equals geometry x DIMLFAC within tol.
    Returns (consistent, inconsistent, checked) counts and the two strongest witnesses."""
    ok, bad, witnesses = 0, 0, []
    for d in dims:
        if d.display_value is None or d.user_text or d.geometry_mm <= 0 or not d.dimlfac:
            continue
        expect = d.geometry_mm * d.dimlfac
        if expect <= 0:
            continue
        if abs(d.display_value - expect) / expect <= tol:
            ok += 1
            if len(witnesses) < 2:
                witnesses.append({"HANDLE": d.provenance.handle, "GEOMETRY_UNITS": round(d.geometry_mm, 3), "DISPLAY": d.display_value, "DIMLFAC": d.dimlfac})
        else:
            bad += 1
    return ok, bad, witnesses


def _display_ratio_mode(dims, tol=0.005):
    """The commonest ratio of a dimension's display value to its own geometry, and the share of dimensions at it.

    The header's DIMLFAC is only the current default; each dimension is plotted through its own style.  When the
    dimensions agree among themselves on one ratio they are internally consistent, whatever the header says.
    """
    ratios = []
    for d in dims:
        if d.display_value is None or d.user_text or d.geometry_mm <= 0:
            continue
        ratios.append(d.display_value / d.geometry_mm)
    if not ratios:
        return None, 0.0
    buckets = {}
    for r in ratios:
        key = round(r, 3)
        buckets[key] = buckets.get(key, 0) + 1
    best = max(buckets, key=buckets.get)
    share = sum(1 for r in ratios if abs(r - best) <= tol * max(best, 1.0)) / len(ratios)
    return best, share


def _suffix_scale(dims):
    """Scale-to-mm from dimension texts that carry a unit suffix ("5.87 m"); needs two agreeing witnesses."""
    found = []
    for d in dims:
        m = SUFFIX.match(d.user_text or "")
        if m and d.geometry_mm > 0:
            val = float(m.group(1).replace(",", "."))
            unit = m.group(2).lower()
            scale = val * UNIT_SCALE[unit] / d.geometry_mm            # mm per drawing unit
            found.append({"HANDLE": d.provenance.handle, "TEXT": d.user_text, "SCALE_TO_MM": scale})
    if len(found) < 2:
        return None, found
    s0 = found[0]["SCALE_TO_MM"]
    agree = all(abs(f["SCALE_TO_MM"] - s0) / s0 <= 0.01 for f in found[1:])
    return (s0 if agree else "CONFLICT"), found


def _wall_thickness_mode(primitives, wall_layers, scale):
    """The commonest face-to-face separation of paired wall lines, in millimetres under the candidate scale.

    A wall is drawn as two parallel lines that overlap along their length and sit a little apart.  That separation
    is the one length in a building whose plausible range is narrow whatever the drawing is of, which is what makes
    it a usable check on a claimed unit: no residential wall is 5 mm thick and none is 5 m thick.
    """
    walls = set(wall_layers or ())
    segs = []
    for p in primitives:
        if p.kind != "SEGMENT" or (walls and p.provenance.layer not in walls):
            continue
        dx, dy = p.x2 - p.x1, p.y2 - p.y1
        n = math.hypot(dx, dy)
        if n < 1e-9:
            continue
        # axis-aligned only: a skew wall pair needs the band engine, and this is a check, not a measurement
        if abs(dx) < 1e-9:
            segs.append(("V", p.x1, min(p.y1, p.y2), max(p.y1, p.y2)))
        elif abs(dy) < 1e-9:
            segs.append(("H", p.y1, min(p.x1, p.x2), max(p.x1, p.x2)))
    gaps = []
    for axis in ("H", "V"):
        rows = sorted((s for s in segs if s[0] == axis), key=lambda s: s[1])
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                d = b[1] - a[1]
                if d <= 0:
                    continue
                if d * scale > WALL_THICKNESS_BAND_MM[1] * 2:
                    break                                   # rows are sorted: nothing further is a pair
                overlap = min(a[3], b[3]) - max(a[2], b[2])
                if overlap > 0:
                    gaps.append(round(d * scale, 1))
    if not gaps:
        return None, 0
    mode = max(set(gaps), key=gaps.count)
    return mode, len(gaps)


def _secondary(primitives, door_layer, wall_layers, scale):
    """Under the candidate scale, do door swings and paired wall thicknesses fall in villa bands?"""
    radii = [p.radius * scale for p in primitives if p.kind == "ARC" and door_layer and p.provenance.layer == door_layer]
    swing_ok = None
    if radii:
        inside = sum(1 for r in radii if DOOR_SWING_BAND_MM[0] <= r <= DOOR_SWING_BAND_MM[1])
        swing_ok = inside >= max(1, 0.5 * len(radii))
    mode, pairs = _wall_thickness_mode(primitives, wall_layers, scale)
    wall_ok = None if mode is None else (WALL_THICKNESS_BAND_MM[0] <= mode <= WALL_THICKNESS_BAND_MM[1])
    return {"DOOR_SWING_RADII_CHECKED": len(radii), "DOOR_SWING_IN_BAND": swing_ok, "BAND_MM": DOOR_SWING_BAND_MM,
            "WALL_PAIRS_CHECKED": pairs, "WALL_THICKNESS_MODE_MM": mode, "WALL_THICKNESS_IN_BAND": wall_ok,
            "WALL_BAND_MM": WALL_THICKNESS_BAND_MM}


def resolve(normalized, *, source_id, declared_unit=None, door_layer=None, wall_layers=()):
    """SOURCE_UNIT_REGISTER row for one CAD source."""
    raw = normalized.insunits_code
    dims = list(normalized.dimensions)
    ok, bad, witnesses = _dimension_consistency(dims)
    suffix_scale, suffix_found = _suffix_scale(dims)
    evidence, conflict = [], None
    cand, scale, status, prov = None, None, "NOT_ESTABLISHED", None
    if raw in INSUNITS and raw not in (0, None):
        cand, scale = INSUNITS[raw]
        prov = "INSUNITS"
        evidence.append(f"INSUNITS = {raw} -> {cand}")
        if suffix_scale not in (None, "CONFLICT") and abs(suffix_scale - scale) / scale > 0.01:
            conflict = {"KIND": "INSUNITS_VS_DIMENSION_TEXT", "INSUNITS_SCALE": scale, "DIMENSION_TEXT_SCALE": suffix_scale}
        if cand == "mm" and normalized.dimlfac and normalized.dimlfac > 1.0 + 1e-9:
            conflict = conflict or {"KIND": "INSUNITS_MM_BUT_DIMLFAC_ABOVE_ONE", "DIMLFAC": normalized.dimlfac, "NOTE": "displayed numbers exceed the geometry: the geometry is authored in a larger unit than INSUNITS claims"}
        status = "SOURCE_ESTABLISHED" if conflict is None else "CONFLICT"
    elif suffix_scale not in (None, "CONFLICT"):
        scale = suffix_scale; prov = "DIMENSION_TEXT_UNIT_SUFFIX"
        cand = next((u for u, s in UNIT_SCALE.items() if abs(s - scale) / s <= 0.01), f"scale_{scale:.6g}")
        evidence.append(f"two or more dimension texts carry a unit suffix agreeing on {scale:.6g} mm per drawing unit")
        status = "SOURCE_ESTABLISHED"
    elif suffix_scale == "CONFLICT":
        status, prov = "CONFLICT", "DIMENSION_TEXT_UNIT_SUFFIX"
        conflict = {"KIND": "DIMENSION_TEXTS_DISAGREE", "WITNESSES": suffix_found}
    elif declared_unit in UNIT_SCALE:
        cand, scale, prov = declared_unit, UNIT_SCALE[declared_unit], "DECLARED_SOURCE_METADATA"
        evidence.append(f"declared source metadata unit {declared_unit}; INSUNITS absent or unitless ({raw})")
        status = "DECLARED_ESTABLISHED"
    else:
        evidence.append(f"INSUNITS absent or unitless ({raw}); no dimension text carries a unit; no declared metadata")
        status = "NOT_ESTABLISHED"
    # dimension consistency is evidence about the AUTHORING, and the second authored dimension is the cross-check
    if ok + bad:
        evidence.append(f"{ok} authored dimensions display geometry x DIMLFAC ({normalized.dimlfac}); {bad} do not")
    # DIMLFAC comes from the header, but each dimension carries its own style's factor: a drawing whose dimensions
    # are all plotted through a style with DIMLFAC 100 looks wholly "inconsistent" against a header that says 1.
    # So the count is recorded as evidence and the modal display-to-geometry ratio is recorded beside it, and the
    # mismatch is only a conflict when the dimensions do not agree among THEMSELVES.
    ratio, ratio_share = _display_ratio_mode(dims)
    if ratio is not None:
        evidence.append(f"{ratio_share:.0%} of authored dimensions display geometry x {ratio:g}")
    if bad > ok and status in ACCEPTABLE and not (ratio is not None and ratio_share >= 0.5):
        conflict = conflict or {"KIND": "DIMENSIONS_INCONSISTENT_WITH_DIMLFAC", "CONSISTENT": ok, "INCONSISTENT": bad}
        status = "CONFLICT"
    secondary = {"SECOND_DIMENSION_CROSS_CHECK": len(witnesses) >= 2, "WITNESSES": witnesses}

    # INSUNITS is a field a drafter can leave wrong, and a wrong one is not a reason to refuse to measure a building
    # that says plainly how big it is.  So a declared unit may overrule it, but only on physical evidence: the
    # declared unit has to put the drawing's own wall pairs inside the band that every masonry wall is inside, and
    # the INSUNITS candidate has to put them outside it.  Both readings and the overruled code stay in the register.
    override = None
    if declared_unit in UNIT_SCALE and scale and abs(UNIT_SCALE[declared_unit] - scale) / scale > 0.01:
        dec_scale = UNIT_SCALE[declared_unit]
        sec_ins = _secondary(normalized.primitives, door_layer, wall_layers, scale)
        sec_dec = _secondary(normalized.primitives, door_layer, wall_layers, dec_scale)
        if sec_ins.get("WALL_THICKNESS_IN_BAND") is False and sec_dec.get("WALL_THICKNESS_IN_BAND") is True:
            override = {"OVERRULED_PROVENANCE": prov, "OVERRULED_UNIT": cand, "OVERRULED_SCALE_TO_MM": scale,
                        "OVERRULED_WALL_THICKNESS_MODE_MM": sec_ins.get("WALL_THICKNESS_MODE_MM"),
                        "DECLARED_WALL_THICKNESS_MODE_MM": sec_dec.get("WALL_THICKNESS_MODE_MM"),
                        "WALL_BAND_MM": WALL_THICKNESS_BAND_MM,
                        "WHY": "the paired wall lines this drawing is built from are outside every plausible wall "
                               "thickness under the INSUNITS code and inside it under the declared unit"}
            evidence.append(f"INSUNITS {cand} put the modal wall pair at {sec_ins.get('WALL_THICKNESS_MODE_MM')} mm, "
                            f"outside {WALL_THICKNESS_BAND_MM}; declared {declared_unit} puts it at "
                            f"{sec_dec.get('WALL_THICKNESS_MODE_MM')} mm, inside it")
            cand, scale, prov, status = declared_unit, dec_scale, "DECLARED_OVERRIDES_IMPLAUSIBLE_INSUNITS", "DECLARED_ESTABLISHED"
            conflict = None

    if scale:
        secondary.update(_secondary(normalized.primitives, door_layer, wall_layers, scale))
        if secondary.get("DOOR_SWING_IN_BAND") is False and status in ACCEPTABLE:
            conflict = {"KIND": "DOOR_SWING_RADII_OUTSIDE_BAND_UNDER_CANDIDATE", "RADII_CHECKED": secondary["DOOR_SWING_RADII_CHECKED"]}
            status = "CONFLICT"
    return {"SOURCE_ID": source_id, "RAW_INSUNITS": raw, "RAW_DRAWING_UNIT": normalized.drawing_unit, "DIMLFAC": normalized.dimlfac, "UNIT_CANDIDATE": cand,
            "UNIT_SCALE_TO_MM": scale, "EVIDENCE": evidence, "SECONDARY_CHECK": secondary, "STATUS": status, "CONFLICT": conflict, "PROVENANCE": prov,
            "DECLARED_UNIT": declared_unit, "INSUNITS_OVERRIDE": override,
            "ACCEPTABLE_FOR_QUANTITIES": status in ACCEPTABLE and conflict is None}


def scale_drawing(normalized, scale_to_mm):
    """A copy of the drawing with every coordinate in millimetres.  Identity (handles, layers) is untouched, so
    entity ids computed from millimetre geometry are the same whatever unit the file was authored in."""
    if scale_to_mm == 1.0:
        return normalized
    s = float(scale_to_mm)
    def rep(obj, **kw):
        if dataclasses.is_dataclass(obj):
            return dataclasses.replace(obj, **kw)
        out = copy.copy(obj)
        for k, v in kw.items():
            setattr(out, k, v)
        return out
    prims = [rep(p, x1=p.x1 * s, y1=p.y1 * s, x2=p.x2 * s, y2=p.y2 * s, cx=p.cx * s, cy=p.cy * s, radius=p.radius * s) for p in normalized.primitives]
    texts = [rep(t, x=t.x * s, y=t.y * s, height=t.height * s) for t in normalized.texts]
    dims = [rep(d, geometry_mm=d.geometry_mm * s, x1=d.x1 * s, y1=d.y1 * s, x2=d.x2 * s, y2=d.y2 * s) for d in normalized.dimensions]
    return rep(normalized, primitives=prims, texts=texts, dimensions=dims)


def register(rows):
    return {"ARTIFACT": "SOURCE_UNIT_REGISTER", "ROWS": rows, "ACCEPTABLE_STATUSES": list(ACCEPTABLE),
            "RULE": "no quantity engine consumes a physical length from a source whose unit status is not acceptable"}
