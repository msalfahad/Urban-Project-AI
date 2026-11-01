"""T-436 rules (pure, stdlib): ground-slab parts with no owner, re-measured and classed (every villa).

R-T436-1  A STAIR ON GRADE DOES NOT REMOVE THE SLAB. A slab-on-grade panel closed by drawn ground-beam faces that
          carries the lines of a flight in a hidden linetype (the flight is above the plan's plane) is slab: the whole
          panel, at the printed thickness. It leaves the slab family only where the drawings show what replaces it: a
          drawn void / pit / opening, a stair base on the foundation plan, or a section that cuts the flight into the
          ground instead of the slab. A flight-to-slab intersection is the slab's (Q-62 A). A panel is never dropped
          whole because stair lines are drawn on it; a panel with stair lines in a CONTINUOUS linetype (cut at the
          plan, not above it) and no section is HELD, never 0 (stair_zone_panel).
R-T436-2  AN OWN PARTITION IS CLOSED ON THE DRAWN FACES BEFORE IT IS A REFERENCE. A band face that ends on another drawn
          edge (an arc included: tested on the true curve, never on its chords) is noded to it; a band face that stops
          short of the face it meets by less than the band width is closed to that face, with the square-end reading
          printed beside it as the other end of the range; a panel that still contains a drawn band pair (two parallel
          faces one band width apart) is refused as a reference (strip_merged). An own-read artefact (chords, a missed
          node) is named as such, never a physical cause and never an engine error.
R-T436-3  A BARE AREA IS A CAUSE ONLY WHEN A PRINTED CONSTRUCTION REPRODUCES IT. The other side's single area with no
          dimension is tested against constructions from printed data only (the drawn network, printed area-table
          pieces and their sums, outlines offset by a printed projection); a construction reproduces it only within
          half a unit of the precision he states; the nearest construction is listed, never taken. 'Slab beyond the
          drawn edge' is a cause only with the drawn line that bounds it (bare_area_tests, beyond_cause).
R-T436-4  A SUB-TRACE RESTATES ONE PART. Sub-parts re-add to their part within 0.000002 m3, carry a verdict from the
          T-428 list, ENGINE_WRONG names the correction owner, a HELD sub-part is never 0, and one sub-part id appears in
          one part only (check_split; the ids are disjoint from any other row's part ids by disjoint).
"""

from __future__ import annotations

import itertools

TOL_PART = 0.000002
VERDICTS = ("AGREE", "ENGINE_RIGHT", "ENGINE_WRONG", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "HELD", "UNRESOLVED",
            "UNTRACED")
CLASS = {"HELD": "HELD", "UNRESOLVED": "UNEXPLAINED", "UNTRACED": "UNEXPLAINED"}


class RefusedT436(ValueError):
    pass


def r6(x):
    return round(float(x), 6) + 0.0


def stair_zone_panel(*, area_m2, closed_by_bands, stair_linetypes, void_or_pit_drawn, stair_base_drawn,
                     section_replaces_slab, floored_above):
    """R-T436-1. Returns the panel's class: SLAB (DRAWING-CONFIRMED) / NOT_SLAB (with the drawn reason) / HELD."""
    if area_m2 is None or area_m2 <= 0:
        raise RefusedT436("stair-zone panel: area missing (never 0)")
    if not closed_by_bands:
        return {"class": "HELD", "why": "panel not closed by drawn ground-beam faces", "area_m2": r6(area_m2)}
    if void_or_pit_drawn:
        return {"class": "NOT_SLAB", "why": "a void / pit / opening is drawn in the panel", "area_m2": r6(area_m2)}
    if stair_base_drawn:
        return {"class": "NOT_SLAB", "why": "a stair base is drawn below the panel", "area_m2": r6(area_m2)}
    if section_replaces_slab:
        return {"class": "NOT_SLAB", "why": "a section shows the flight in the ground in place of the slab",
                "area_m2": r6(area_m2)}
    lts = {str(x).upper() for x in stair_linetypes}
    if not lts:
        return {"class": "SLAB", "status": "DRAWING-CONFIRMED", "why": "no stair line in the panel",
                "area_m2": r6(area_m2)}
    if lts <= {"HIDDEN", "DASHED", "HIDDEN2", "DASHED2"} and floored_above:
        return {"class": "SLAB", "status": "DRAWING-CONFIRMED",
                "why": "flight drawn hidden (above the plan), no void / pit / stair base, floored space",
                "area_m2": r6(area_m2)}
    return {"class": "HELD", "why": "stair lines cut at the plan (continuous) or the space is not floored: the drawings "
                                    "do not settle what lies under the flight", "area_m2": r6(area_m2)}


def drop_whole(panel_class):
    """The engine move this task found: a panel with stair lines dropped from the slab family as a whole."""
    if panel_class["class"] == "SLAB":
        raise RefusedT436("a slab panel dropped whole because stair lines are drawn on it (R-T436-1)")
    if panel_class["class"] == "HELD":
        raise RefusedT436("a HELD panel dropped as 0 (held is never 0)")
    return 0.0


def band_end_closure(*, gap_m, band_width_m, closed_m2, square_m2):
    """R-T436-2: a face short of the face it meets by less than the band width -> closed to the face; the square-end
    reading is the other end of the range. A gap of a band width or more is not a drafting gap: HELD."""
    if gap_m < 0 or band_width_m <= 0:
        raise RefusedT436("band end: gap / width missing")
    if square_m2 > closed_m2 + 1e-9:
        raise RefusedT436("band end: square end larger than the closed strip")
    if gap_m >= band_width_m:
        return {"state": "HELD", "range_m2": [r6(square_m2), r6(closed_m2)]}
    return {"state": "CLOSED", "reading_m2": r6(closed_m2), "range_m2": [r6(square_m2), r6(closed_m2)]}


def strip_merged(panel_pairs, band_width_m, tol_m=0.012):
    """R-T436-2: panel_pairs = [(face a, face b, perpendicular distance m)] of parallel drawn band faces inside a panel;
    a pair one band width apart means a band strip was read as panel: refused as a reference."""
    for a, b, d in panel_pairs:
        if abs(d - band_width_m) <= tol_m:
            raise RefusedT436(f"panel contains the band pair {a} / {b} ({d:.3f} m): a strip read as panel")
    return True


def subset_sums(pieces):
    out = {}
    keys = sorted(pieces)
    for n in range(1, len(keys) + 1):
        for c in itertools.combinations(keys, n):
            out[c] = r6(sum(pieces[k] for k in c))
    return out


def bare_area_tests(other_m2, constructions, *, precision_m2):
    """R-T436-3: every construction with its misfit (construction - other); reproduces only within precision / 2."""
    if other_m2 is None or other_m2 <= 0:
        raise RefusedT436("bare area missing")
    if not constructions:
        raise RefusedT436("no construction tried: a bare area is not classed by its sign")
    rows = []
    for name, v in constructions.items():
        if v is None:
            raise RefusedT436(f"{name}: construction value missing")
        mis = r6(v - other_m2)
        rows.append({"construction": name, "value_m2": r6(v), "misfit_m2": mis,
                     "reproduces": abs(mis) <= precision_m2 / 2 + 1e-9})
    return sorted(rows, key=lambda x: abs(x["misfit_m2"]))


def beyond_cause(rows, *, drawn_line=None):
    """R-T436-3: class of 'his area beyond the drawn network'. TRACED only with a reproducing construction AND the drawn
    line that bounds the extra area; the nearest construction is never taken."""
    hits = [x for x in rows if x["reproduces"]]
    if hits and not drawn_line:
        raise RefusedT436("slab beyond the drawn edge counted as a residual cause without a drawn line")
    if len(hits) > 1:
        return {"class": "UNRESOLVED", "why": "several constructions reproduce it: none chosen",
                "candidates": [x["construction"] for x in hits]}
    if hits:
        return {"class": "TRACED", "construction": hits[0]["construction"], "drawn_line": drawn_line}
    return {"class": "UNRESOLVED", "nearest": rows[0]["construction"], "nearest_misfit_m2": rows[0]["misfit_m2"],
            "why": "no construction reproduces it; the nearest is listed, not taken"}


def check_split(subparts_by_part, parts_m3):
    """R-T436-4."""
    seen = set()
    for pid, total in parts_m3.items():
        subs = subparts_by_part.get(pid)
        if not subs:
            raise RefusedT436(f"{pid}: no sub-parts")
        s = 0.0
        for sp in subs:
            if sp["id"] in seen:
                raise RefusedT436(f"{sp['id']}: sub-part in two parts")
            seen.add(sp["id"])
            if sp.get("verdict") not in VERDICTS:
                raise RefusedT436(f"{sp['id']}: unknown verdict {sp.get('verdict')!r}")
            if not str(sp.get("cause") or "").strip():
                raise RefusedT436(f"{sp['id']}: a sub-part states its physical cause")
            if sp["verdict"] == "ENGINE_WRONG" and not str(sp.get("correction_owner") or "").strip():
                raise RefusedT436(f"{sp['id']}: ENGINE_WRONG names the owner of the correction")
            if sp["verdict"] == "HELD" and abs(sp["m3"]) < 5e-7:
                raise RefusedT436(f"{sp['id']}: HELD never 0")
            s += float(sp["m3"])
        if abs(s - total) > TOL_PART:
            raise RefusedT436(f"{pid}: sub-parts re-add to {s:.7f}, not {total:.6f}")
    extra = set(subparts_by_part) - set(parts_m3)
    if extra:
        raise RefusedT436(f"sub-parts for parts not restated here: {sorted(extra)}")
    return True


def totals(subparts_by_part):
    out = {"TRACED": 0.0, "HELD": 0.0, "UNEXPLAINED": 0.0}
    for subs in subparts_by_part.values():
        for sp in subs:
            out[CLASS.get(sp["verdict"], "TRACED")] += sp["m3"]
    return {k: r6(v) for k, v in out.items()}


def disjoint(ids_a, ids_b):
    common = set(ids_a) & set(ids_b)
    if common:
        raise RefusedT436(f"part ids shared with another row: {sorted(common)}")
    return True
