"""DIMENSION_OWNER_STATUS - which element a printed dimension measures.

A printed value being read correctly (TEXT_READ_ESTABLISHED) and the value
belonging to the element the reader said it belongs to are two different
facts, and the second one is where the traps live: "745" whose extension
lines land on room walls, "130" that terminates on a different roof-edge
element than the one being quantified.

So the owner is resolved from the TRACED EXTENSION LINES, deterministically,
against the traced element geometries on the same sheet - never from the
reader's prose. Each end of a dimension is landed on whatever traced
elements its extension line (or, failing that, the end of its dimension
line) touches, and the status follows from what it touched:

    OWNER_ESTABLISHED   both ends land on traced elements or level marks
                        whose roles are established, and the landing set at
                        each end is a single physical object (or datum)
    OWNER_PROVISIONAL   an end lands on a PROVISIONAL trace or an
                        UNRESOLVED_FEATURE
    OWNER_AMBIGUOUS     an end lands on several distinct objects
    OWNER_NOT_ESTABLISHED  an end lands on nothing traced, or no extension
                        geometry exists

This status is SEPARATE from TEXT_READ_ESTABLISHED (the reader's
DIMENSION_STATUS), which is carried through untouched. An ink check on the
processed sheet is recorded beside it: it says whether a line is drawn
where the extension line was traced, nothing more.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point

from engine.material_role_audit import (ANNOTATION_ROLE, geometry_of,
                                        material_role)

OWNER_STATUSES = ("OWNER_ESTABLISHED", "OWNER_PROVISIONAL",
                  "OWNER_AMBIGUOUS", "OWNER_NOT_ESTABLISHED")
DIMENSION_TYPES = ("PRINTED_DIMENSION", "HEIGHT_DIMENSION")
LANDING_TOL_PX = 8.0
INK_THRESHOLD = 160
INK_MIN_FRACTION = 0.5

LANDABLE_ANNOTATIONS = ("LEVEL_MARK",)    # a datum is a legitimate owner end


def _ends_of(t: dict) -> dict:
    """The two measured ends as line geometries: extension lines when
    traced, else the endpoints of the dimension line."""
    out = {}
    for k in ("EXTENSION_LINE_A", "EXTENSION_LINE_B"):
        v = t.get(k)
        if v and len(v) >= 2:
            out[k] = LineString([tuple(p) for p in v])
    dl = t.get("DIMENSION_LINE_TRACE")
    if dl and len(dl) >= 2:
        if "EXTENSION_LINE_A" not in out:
            out["DIMENSION_LINE_END_A"] = Point(tuple(dl[0]))
        if "EXTENSION_LINE_B" not in out:
            out["DIMENSION_LINE_END_B"] = Point(tuple(dl[-1]))
    return out


def _landing(geom, elements: list, tol: float) -> list:
    hits = []
    for e, g, role in elements:
        if g is None:
            continue
        d = geom.distance(g)
        if d <= tol:
            hits.append({"TRACE_ID": e["TRACE_ID"], "ROLE": role,
                         "DISTANCE_PX": round(d, 1),
                         "VISUAL_TRACE_STATUS": e.get("VISUAL_TRACE_STATUS"),
                         "CLAIM_TYPE": e.get("EFFECTIVE_CLAIM_TYPE") or e.get("CLAIM_TYPE")})
    return sorted(hits, key=lambda h: (h["DISTANCE_PX"], h["TRACE_ID"]))


def _ink_fraction(img, line) -> float | None:
    """Fraction of dark samples along a line on a PIL greyscale image."""
    if img is None or line is None or not isinstance(line, LineString):
        return None
    n = max(8, int(line.length))
    dark = 0
    W, H = img.size
    for i in range(n + 1):
        p = line.interpolate(i / n, normalized=True)
        x, y = int(round(p.x)), int(round(p.y))
        if 0 <= x < W and 0 <= y < H:
            # tolerate a one-pixel traced offset
            v = min(img.getpixel((x, y)),
                    img.getpixel((x, max(0, y - 1))), img.getpixel((x, min(H - 1, y + 1))),
                    img.getpixel((max(0, x - 1), y)), img.getpixel((min(W - 1, x + 1), y)))
            if v < INK_THRESHOLD:
                dark += 1
    return round(dark / (n + 1), 3)


def resolve(traces: list, *, object_map: dict | None = None,
            role_overrides: dict | None = None, images: dict | None = None,
            tol_px: float = LANDING_TOL_PX) -> list:
    """One DIMENSION_OWNER record per dimension trace.

    images  {SHEET_ID: PIL greyscale image of the processed sheet} for the
            ink check; optional.
    """
    member_of = {}
    for oid, ms in (object_map or {}).items():
        for m in ms:
            member_of[m] = oid
    elements = []
    for t in traces:
        ct = t.get("EFFECTIVE_CLAIM_TYPE") or t.get("CLAIM_TYPE")
        if ct in DIMENSION_TYPES:
            continue
        role = material_role(t, role_overrides)["MATERIAL_ROLE"]
        if role == ANNOTATION_ROLE and ct not in LANDABLE_ANNOTATIONS:
            continue
        g = geometry_of(t)
        if g is None and t.get("PIXEL_POINT"):
            g = Point(tuple(t["PIXEL_POINT"])).buffer(6.0)
        if ct in LANDABLE_ANNOTATIONS:
            role = "LEVEL_DATUM"
        elements.append((t, g, role))
    by_sheet = {}
    for e in elements:
        by_sheet.setdefault(e[0]["SHEET_ID"], []).append(e)

    out = []
    for t in traces:
        ct = t.get("EFFECTIVE_CLAIM_TYPE") or t.get("CLAIM_TYPE")
        if ct not in DIMENSION_TYPES:
            continue
        ends = _ends_of(t)
        img = (images or {}).get(t["SHEET_ID"])
        landings, statuses = {}, []
        for k, geom in ends.items():
            hits = _landing(geom, by_sheet.get(t["SHEET_ID"], []), tol_px)
            objs = {member_of.get(h["TRACE_ID"], f"PO:{h['TRACE_ID']}") for h in hits}
            if not hits:
                st = "OWNER_NOT_ESTABLISHED"
            elif any(h["ROLE"] == "UNRESOLVED" or
                     h["VISUAL_TRACE_STATUS"] in ("TRACE_PROVISIONAL", "TRACE_AMBIGUOUS")
                     for h in hits):
                st = "OWNER_PROVISIONAL"
                if len({o for o in objs}) > 1 and len(
                        {h["ROLE"] for h in hits} - {"LEVEL_DATUM"}) > 1:
                    st = "OWNER_AMBIGUOUS"
            elif len(objs) > 1 and len({h["ROLE"] for h in hits} - {"LEVEL_DATUM"}) > 1:
                st = "OWNER_AMBIGUOUS"
            else:
                st = "OWNER_ESTABLISHED"
            ink_f = _ink_fraction(img, geom)
            landings[k] = {
                "GEOMETRY_KIND": "EXTENSION_LINE" if k.startswith("EXT") else "DIMENSION_LINE_END",
                "LANDS_ON": hits, "OBJECTS": sorted(objs), "END_STATUS": st,
                "INK_FRACTION_ALONG_LINE": ink_f,
                "INK_PATTERN": (None if ink_f is None else
                                "SOLID" if ink_f >= INK_MIN_FRACTION else
                                "DASHED_OR_SPARSE" if ink_f >= 0.03 else "NONE"),
            }
            statuses.append(st)
        if len(ends) < 2:
            owner = "OWNER_NOT_ESTABLISHED"
            why = "fewer than two measured ends were traced"
        else:
            order = ["OWNER_NOT_ESTABLISHED", "OWNER_AMBIGUOUS",
                     "OWNER_PROVISIONAL", "OWNER_ESTABLISHED"]
            owner = min(statuses, key=order.index)
            why = "weakest end decides"
        owners = sorted({o for l in landings.values() for o in l["OBJECTS"]})
        ink = [l["INK_FRACTION_ALONG_LINE"] for l in landings.values()
               if l["INK_FRACTION_ALONG_LINE"] is not None]
        out.append({
            "TRACE_ID": t["TRACE_ID"], "SHEET_ID": t["SHEET_ID"],
            "CLAIM_TYPE": ct, "VALUE_M": t.get("VALUE_M"),
            "TEXT_READ_STATUS": t.get("DIMENSION_STATUS"),
            "TEXT_READ_ESTABLISHED": t.get("DIMENSION_STATUS") == "ESTABLISHED",
            "DIMENSION_OWNER_STATUS": owner, "WHY": why,
            "OWNER_OBJECTS": owners,
            "ENDS": landings,
            "EXTENSION_LINE_INK_PRESENT": (min(ink) >= INK_MIN_FRACTION) if ink else None,
            "LANDING_TOLERANCE_PX": tol_px,
            "OWNER_IS_SEPARATE_FROM_TEXT_READ": True,
        })
    return out


def summary(records: list) -> dict:
    return {s: sum(1 for r in records if r["DIMENSION_OWNER_STATUS"] == s)
            for s in OWNER_STATUSES}
