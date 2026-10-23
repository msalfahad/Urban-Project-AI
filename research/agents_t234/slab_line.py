"""T-234 slab line rules (pure, stdlib only, wired into no method): CONC.SLAB as a whole line, every panel once.

Physical element (ERS s.2.1): a suspended slab PANEL is the RC plate between the faces of the members that carry it,
on one slab sheet (storey convention: named by the slab sheet that draws it, T-213), of thickness t; openings and voids
are deducted once, inside the panel they pierce; a sunken panel is the same plate lowered by its drop (its thickness is
printed for the panel, so it is measured at the full t: T-213); a finished level never gives a structural dimension.

Ownership (one owner per intersection; R-CONC-OWN-1 / concrete_overlap_ownership.PRECEDENCE_ROUTE_G):
  C1 'panel between beam faces' (route G released lines, the beam register T-110 at full depth D, the freelancer):
     slab = panel area x t;  beam = band area x D;  the band under the plate belongs to the beam.
  C2 'plate over the beams' (URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1): slab = (panel + band) area x t;
     beam downstand = band area x (D - t).  C1 and C2 move band x t between the two lines; slab + beam is the same.
A comparison of two slab totals is valid only when both sides state the same convention (convention()).

Thickness basis per panel: TAG (a thickness tag printed in the panel), GENERAL_NOTE (the set's general note gives the
default 'unless stated'), or HELD (no printed value: never 0, never a default). SHEET_UNIFORM (a tag printed in one panel
spread to the untagged panels of its sheet) is refused when the set prints a general-note default: the note, not the
neighbour's tag, governs an untagged panel (T-234 finding on the released route G, ST 2F sheet).
"""

from __future__ import annotations

import math

SCHEMA = "T234_SLAB_LINE_V1"
TOL_M2 = 1e-4
TOL_M3 = 1e-4
UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}
THICKNESS_BASES = ("TAG", "GENERAL_NOTE", "HELD")
CONVENTIONS = ("C1_PANEL_BETWEEN_BEAM_FACES", "C2_PLATE_OVER_BEAMS")
# face classes of a slab sheet partition (T-139 PANELS.csv) -> the ONE line that owns the face (None = no concrete)
FACE_OWNER = {
    "SLAB": "CONC.SLAB",
    "BEAM_OR_COLUMN": "CONC.BEAM|CONC.COLUMN",   # band, column top or junction square: one band or the column owns it
    "BEAM": "CONC.BEAM",
    "BEAM_HELD": "CONC.BEAM (HELD)",
    "EDGE_HELD": "CONC.BEAM (HELD)",              # strips / boxes outside the outer beams: beam lane, D-05 / D-26
    "STAIR": "CONC.STAIR",
    "VOID+STAIR": "CONC.STAIR",                   # the void is no concrete; the stair inside it is the stair ledger's
    "OPENING": None,
    "OPENING+RING": "CONC.BEAM",                  # the void is no concrete; the ring band is a beam
    "DOME_OPENING+RING": "CONC.BEAM",             # opening (Q-44 A) + ring band (beam); corners are SLAB rows
    "NOT_SLAB": None,                             # drafting break mark
    "DETAIL": None,                               # a section drawn on the sheet, not plan
    "NOT_THIS_SLAB": None,                        # the lower roof outline repeated on the upper sheet
}


def poly_area(points, unit="m"):
    """Shoelace area of a simple polygon in m2 (orientation-free: mirror / rotation never change it)."""
    if unit not in UNIT_TO_M:
        raise ValueError("unknown length unit %r" % (unit,))
    k = UNIT_TO_M[unit]
    if len(points) < 3:
        raise ValueError("a panel outline needs at least 3 points")
    s = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0 * k * k


def panel_thickness(panel, general_note_t_m=None):
    """(t_m, basis) for one panel, or (None, 'HELD'). Refuses a spread tag, a finished-level thickness and mm values."""
    basis = panel.get("t_basis")
    if basis == "SHEET_UNIFORM":
        if general_note_t_m is not None:
            raise ValueError("%s: a tag printed in another panel is spread to an untagged panel while the general "
                             "note prints the default (%.2f m): the note governs" % (panel["id"], general_note_t_m))
        raise ValueError("%s: SHEET_UNIFORM is not a printed thickness for this panel: HELD, not spread"
                         % panel["id"])
    if basis == "FROM_LEVELS":
        raise ValueError("%s: a thickness from a level difference needs structural levels; finished levels are "
                         "never a structural dimension" % panel["id"])
    if basis not in THICKNESS_BASES:
        raise ValueError("%s: unknown thickness basis %r" % (panel["id"], basis))
    if basis == "HELD":
        return None, "HELD"
    if basis == "GENERAL_NOTE":
        if general_note_t_m is None:
            raise ValueError("%s: GENERAL_NOTE basis without a printed general-note thickness" % panel["id"])
        t = general_note_t_m
        if panel.get("t_m") is not None and abs(panel["t_m"] - t) > 1e-9:
            raise ValueError("%s: thickness %.3f differs from the general note %.3f" % (panel["id"], panel["t_m"], t))
    else:
        t = panel.get("t_m")
    if t is None or not (0.05 <= t <= 0.60):
        raise ValueError("%s: slab thickness %r m outside 0.05 .. 0.60 (a value in cm or mm?)" % (panel["id"], t))
    return t, basis


def panel_record(panel, general_note_t_m=None):
    """One panel -> its ledger record. Openings deducted once each; a sunken panel at its full thickness."""
    if panel.get("sunken") and panel.get("depth_basis", "FULL") != "FULL":
        raise ValueError("%s: a sunken panel is the plate lowered by its drop; its printed thickness is not reduced "
                         "(T-213)" % panel["id"])
    if panel.get("top_datum", "STRUCTURAL") != "STRUCTURAL":
        raise ValueError("%s: the slab top is a structural datum; a finished floor level is refused" % panel["id"])
    gross = panel["area_m2"] if "area_m2" in panel else poly_area(panel["outline"], panel.get("unit", "m"))
    seen, ded = set(), 0.0
    for o in panel.get("openings", []):
        if o["id"] in seen:
            raise ValueError("%s: opening %s deducted twice" % (panel["id"], o["id"]))
        seen.add(o["id"])
        a = o["area_m2"] if "area_m2" in o else poly_area(o["outline"], o.get("unit", "m"))
        ded += a
    if ded > gross + TOL_M2:
        raise ValueError("%s: openings %.4f m2 exceed the panel %.4f m2" % (panel["id"], ded, gross))
    net = gross - ded
    t, basis = panel_thickness(panel, general_note_t_m)
    rec = dict(id=panel["id"], storey=panel.get("storey"), gross_m2=gross, openings=sorted(seen), deducted_m2=ded,
               net_m2=net, t_m=t, t_basis=basis, sunken=bool(panel.get("sunken")))
    if t is None:
        rec.update(m3=None, status="HELD", held=(net * 0.05, net * 0.60), why="no printed thickness")
    else:
        rec.update(m3=net * t, status="MEASURED")
    return rec


def slab_line(panels, general_note_t_m=None, openings_census=None):
    """Whole CONC.SLAB line: every panel once, every opening once across the line, HELD never 0.

    openings_census: ids of every opening drawn on the slab sheets (an independent list, e.g. the S-OPENING marks);
    each must be deducted exactly once or be a void outside every panel (listed under 'outside_panels')."""
    ids = [p["id"] for p in panels]
    if len(set(ids)) != len(ids):
        raise ValueError("a panel is listed twice")
    recs = [panel_record(p, general_note_t_m) for p in panels]
    used = {}
    for r in recs:
        for o in r["openings"]:
            if o in used:
                raise ValueError("opening %s deducted in %s and %s" % (o, used[o], r["id"]))
            used[o] = r["id"]
    missing = []
    if openings_census is not None:
        census = dict(openings_census)        # id -> 'IN_PANEL' | 'OUTSIDE_PANELS' (a void face of its own)
        for o in used:
            if o not in census:
                raise ValueError("opening %s deducted but absent from the census" % o)
        missing = [o for o, where in sorted(census.items()) if where == "IN_PANEL" and o not in used]
    measured = sum(r["m3"] for r in recs if r["m3"] is not None)
    held = [(r["id"], r["held"]) for r in recs if r["m3"] is None]
    status = "CLOSABLE" if not held and not missing else "NOT_CLOSABLE"
    return dict(schema=SCHEMA, panels=recs, measured_m3=measured, held=held, openings_not_deducted=missing,
                status=status, by_storey=_by(recs, "storey"))


def _by(recs, key):
    out = {}
    for r in recs:
        o = out.setdefault(r[key], dict(n=0, net_m2=0.0, m3=0.0))
        o["n"] += 1
        o["net_m2"] += r["net_m2"]
        o["m3"] += r["m3"] or 0.0
    return out


def face_partition_check(faces):
    """Plan check of one slab sheet: every face of the sheet's partition has exactly one owner line.

    faces: [{'id', 'cls', 'area_m2', 'billed_by': [line keys]}]. DOUBLE = a face billed by two lines (or by a line its
    class does not give it); GAP = a concrete face (owner not None) billed by no line. HELD owners count as billed."""
    double, gap, wrong = [], [], []
    for f in faces:
        owner = FACE_OWNER.get(f["cls"], "UNKNOWN")
        if owner == "UNKNOWN":
            raise ValueError("face %s: unknown class %r" % (f["id"], f["cls"]))
        billed = list(f.get("billed_by", []))
        if len(billed) > 1:
            double.append((f["id"], billed, f["area_m2"]))
        elif owner is None and billed:
            wrong.append((f["id"], billed[0], f["area_m2"]))
        elif owner is not None and not billed:
            gap.append((f["id"], owner, f["area_m2"]))
        elif owner is not None and billed and billed[0] not in owner.split("|") and billed[0] != owner:
            wrong.append((f["id"], billed[0], f["area_m2"]))
    ok = not (double or gap or wrong)
    return dict(status="PASS" if ok else "FAIL", double=double, gap=gap, wrong_owner=wrong)


def convention(c, slab_c1_m3, band_area_by_t):
    """Express a C1 slab total in convention c. band_area_by_t: [(band plan area under the plate m2, t m)].
    Returns (slab_m3, moved_m3): C2 adds band x t to the slab; the beam line loses the same (sum invariant)."""
    if c not in CONVENTIONS:
        raise ValueError("unknown slab / beam convention %r" % (c,))
    moved = sum(a * t for a, t in band_area_by_t)
    return (slab_c1_m3, 0.0) if c == CONVENTIONS[0] else (slab_c1_m3 + moved, moved)


def compare(side_a, side_b):
    """Two slab totals are compared only with the same stated convention."""
    if side_a.get("convention") not in CONVENTIONS or side_b.get("convention") not in CONVENTIONS:
        raise ValueError("state the slab / beam convention of both sides before comparing")
    if side_a["convention"] != side_b["convention"]:
        raise ValueError("convention %s vs %s: convert one side first (convention())"
                         % (side_a["convention"], side_b["convention"]))
    d = side_a["m3"] - side_b["m3"]
    return dict(diff_m3=d, pct=(100.0 * d / side_b["m3"]) if side_b["m3"] else math.nan)


def reconcile(a_m3, b_m3, components, tol=1e-3):
    """a - b explained by named components [(cause, m3)]; the remainder is the named residual."""
    s = sum(m for _, m in components)
    residual = (a_m3 - b_m3) - s
    return dict(diff_m3=a_m3 - b_m3, explained_m3=s, residual_m3=residual, closed=abs(residual) <= tol)
