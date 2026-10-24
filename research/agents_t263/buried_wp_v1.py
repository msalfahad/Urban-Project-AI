"""T-263: liquid waterproofing of buried concrete as a BOQ scope (research piece, not wired; BURIED_WP_V1).

Pure functions, stdlib only, no I/O, any villa. Inputs are VALUES (lengths, depths, printed levels, footing outline
areas, neck sections) in metres; nothing here reads a drawing. The development-villa runner `t263_alsenan_check.py`
builds the inputs from merged ledgers and states every source.

Physical element (ERS s.2.1). A typical isolated-footing detail (ST p.13 of a set like Alsenan) prints, in BOTH of its
variants, 'Two layers liquid water proofing to be applied to all surface in contact with earth'. A liquid coat is
brushed / sprayed on a concrete face AFTER the formwork is struck and BEFORE backfill. So a face is coated when, and
only over the height where, the concrete face is (a) a formed face and (b) has earth (natural ground or compacted fill)
against it in the finished work. Per member and face:

- FOOTING TOP outside the neck(s): formed / exposed, backfilled -> coated, area = outline area - the neck footprints
  standing on it (a neck footprint is concrete, not earth). The two-ground-beam variant of the detail puts a lower ground
  beam on part of the top, whose plan is not drawn when that variant is not the drawn system: the top line follows the
  same detail selection as the footing sides (HELD while the selecting level is unprinted; reading SINGLE given).
- FOOTING SIDES: owned by the footing-underlay line (T-219, WP.FOOTING_SIDES): never counted here (each face once).
- FOOTING SOFFIT: membrane + screed underlay (T-219): never a liquid coat (a soffit cast on the underlay cannot be
  coated; the underlay face is refused here).
- NECK SIDES (column below the ground beam): perimeter x the neck height; the height rests on the formation / ground-beam
  levels: HELD while those are unprinted (rate m2 per metre given), never 0.
- GROUND-BEAM SIDES: a face has earth against it only below the ground slab that bears on fill (slab on grade on the
  panel side: buried height = D - slab thickness, the beam billed full depth from the slab top) or below the natural
  ground on an outside face (buried height = max(0, natural ground - beam soffit)). A face whose side is a held panel
  (open or floored not printed), a split-level panel, or an outside face whose datum / depth is held is HELD.
  A coat above the printed ground (or above the slab underside) is REFUSED: that face is a plinth / finish face.
- GROUND-BEAM SOFFIT: cast on the blinding the ground-beam sections print (10 cm plain concrete): not in contact with
  earth and not coatable: a named exclusion, never a quantity.
- GROUND-BEAM TOP: under the floor build-up, not earth: excluded.
- Members drawn in OTHER typical details that print no coating (boundary-wall beam, lift-pit walls with their own sheet
  membrane): the note of one detail is not carried to another element (ERS s.3): HELD (note applicability) with the
  geometry, or owned by the other detail's line.

Installed quantity = coated face area, one system ('two layers' is the system, not twice the area). Procurement (litres,
kg, coats, coverage) only when the product and its coverage are printed: otherwise HELD (UP-WP-MAT-001 BY_SPEC).

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED, HELD (never 0, never in a measured total), UNKNOWN, EXCLUDED
(a named face that is physically not in the scope, with its reason).
"""

from __future__ import annotations

from dataclasses import dataclass, field

METHOD = "BURIED_WP_V1"
TOL = 1e-9
DC = "DRAWING-CONFIRMED"
HELD = "HELD"
EXCLUDED = "EXCLUDED"
MAX_MEMBER_DEPTH_M = 3.0      # a ground beam / neck dimension above this is a unit slip (mm or cm given as m)
FACE_SIDES = ("PANEL", "OUTSIDE")
PANEL_STATES = ("FILL", "HELD", "SPLIT_LEVEL")


class RefusedError(ValueError):
    """An input that would put a wrong or invented quantity into the buried-concrete waterproofing line."""


def r6(x):
    return None if x is None else round(x + 0.0, 6)


def _metres(v, what):
    if v is None:
        return None
    v = float(v)
    if v < -TOL:
        raise RefusedError(f"{what} {v} is negative")
    if v > MAX_MEMBER_DEPTH_M:
        raise RefusedError(f"{what} {v} m exceeds {MAX_MEMBER_DEPTH_M} m: a unit slip (mm / cm as m) is refused")
    return v


@dataclass
class Row:
    element: str
    member: str
    face: str
    unit: str
    qty: float | None
    status: str
    basis: str
    readings: dict = field(default_factory=dict)
    held_why: str = ""

    def as_dict(self):
        return {"element": self.element, "member": self.member, "face": self.face, "unit": self.unit,
                "qty": r6(self.qty), "status": self.status, "basis": self.basis,
                "readings": {k: r6(v) for k, v in self.readings.items()}, "held_why": self.held_why}


# ------------------------------------------------------------------------------------------------ ground-beam faces
def gb_face_height(side, *, top, depth, slab_t=None, natural_ground=None, panel_state=None):
    """Buried height (m) of one ground-beam side face, or (None, why) when it is held.

    side PANEL: the face looks into a slab-on-grade panel. Fill reaches the slab underside: h = depth - slab_t.
    side OUTSIDE: the face looks outside the building. Earth reaches the natural ground: h = max(0, ng - soffit).
    Returns (h, why): h None means HELD with why.
    """
    if side not in FACE_SIDES:
        raise RefusedError(f"face side {side!r} not declared ({FACE_SIDES})")
    depth = _metres(depth, "ground-beam depth")
    if side == "PANEL":
        if panel_state not in PANEL_STATES:
            raise RefusedError(f"panel state {panel_state!r} not declared ({PANEL_STATES})")
        if panel_state == "HELD":
            return None, "PANEL_HELD: the panel on this side is not established as a slab on fill (open or floored not printed)"
        if panel_state == "SPLIT_LEVEL":
            return None, "PANEL_SPLIT_LEVEL: the panel carries two slab levels; the slab underside beside this face is not traced"
        if depth is None:
            return None, "DEPTH_HELD: the beam depth is not established (designer item)"
        slab_t = _metres(slab_t, "slab thickness")
        if slab_t is None:
            return None, "SLAB_T_NOT_PRINTED"
        if slab_t > depth + TOL:
            raise RefusedError("a slab thicker than the beam it bears on is refused")
        return depth - slab_t, ""
    # OUTSIDE
    if natural_ground is None:
        return None, "DATUM_HELD: the natural ground beside this face is not printed / typed"
    if depth is None or top is None:
        return None, "DEPTH_HELD: the beam depth (soffit) is not established"
    soffit = float(top) - depth
    return max(0.0, float(natural_ground) - soffit), ""


def gb_run_rows(run):
    """One ground-beam run -> rows for its two side faces + the named soffit / top exclusions.

    run: {id, L, b, top, depth (or None), slab_t, natural_ground, faces: [{side, panel_state}] x 2}
    """
    L = float(run["L"])
    if L <= TOL:
        raise RefusedError(f"{run['id']}: a run without a length is refused")
    faces = run["faces"]
    if len(faces) != 2:
        raise RefusedError(f"{run['id']}: a beam has exactly two side faces ({len(faces)} given)")
    rows = []
    for i, f in enumerate(faces):
        name = f"side {'AB'[i]} ({f['side']}{'' if f['side'] == 'OUTSIDE' else ': ' + str(f.get('panel_state'))})"
        h, why = gb_face_height(f["side"], top=run.get("top"), depth=run.get("depth"), slab_t=run.get("slab_t"),
                                natural_ground=run.get("natural_ground"), panel_state=f.get("panel_state"))
        if h is None:
            rd = {}
            if f["side"] == "PANEL" and run.get("depth_range") and f.get("panel_state") == "FILL":
                lo, hi = run["depth_range"]
                rd = {"candidate_low": L * (lo - run["slab_t"]), "candidate_high": L * (hi - run["slab_t"])}
            rows.append(Row(run["id"], "GROUND_BEAM", name, "m2", None, HELD,
                            f"L {L:.4f} m x buried height (held)", rd, why))
        elif h <= TOL:
            rows.append(Row(run["id"], "GROUND_BEAM", name, "m2", None, EXCLUDED,
                            f"soffit {run['top'] - run['depth']:+.2f} at or above the natural ground "
                            f"{run['natural_ground']:+.2f}: no earth against this face (a plinth / finish face)",
                            {"face_m2": L * float(run["depth"])}))
        else:
            basis = (f"L {L:.4f} x (D {run['depth']:.2f} - slab {run['slab_t']:.2f}) = {L * h:.4f}"
                     if f["side"] == "PANEL" else
                     f"L {L:.4f} x max(0, NG {run['natural_ground']:+.2f} - soffit {run['top'] - run['depth']:+.2f})"
                     f" = {L * h:.4f}")
            rows.append(Row(run["id"], "GROUND_BEAM", name, "m2", L * h, DC, basis))
    rows.append(Row(run["id"], "GROUND_BEAM", "soffit", "m2", None, EXCLUDED,
                    f"b {run['b']:.2f} x L {L:.4f} cast on the printed blinding: not in contact with earth, not coatable",
                    {"face_m2": float(run["b"]) * L}))
    return rows


def refuse_coat_height(requested_h, run, face):
    """Refuse a coat height above the buried height (a coat above the printed ground / slab underside)."""
    h, why = gb_face_height(face["side"], top=run.get("top"), depth=run.get("depth"), slab_t=run.get("slab_t"),
                            natural_ground=run.get("natural_ground"), panel_state=face.get("panel_state"))
    if h is None:
        raise RefusedError(f"coat height on a held face is refused ({why})")
    if requested_h > h + 1e-6:
        raise RefusedError(f"coat height {requested_h:.3f} m above the buried height {h:.3f} m is refused: the face above "
                           "the printed ground / slab underside is not in contact with earth")
    return requested_h


# ------------------------------------------------------------------------------------------------ footings and necks
def footing_top_row(outline_id, ftype, outline_area, necks, *, detail_selected, held_outline=None):
    """Footing top outside the necks. necks: [{id, section_m2, range (lo, hi) or None}].

    detail_selected: 'SINGLE' (one ground beam, the top fully backfilled), 'DOUBLE' (a lower ground beam on part of the
    top, plan not drawn) or None (selecting level not printed: HELD with reading SINGLE).
    """
    if held_outline:
        return Row(outline_id, "FOOTING", "top outside the necks", "m2", None, HELD, f"{ftype}: {held_outline}", {},
                   "OUTLINE_HELD")
    a = float(outline_area)
    if a <= TOL:
        raise RefusedError(f"{outline_id}: footing outline without area")
    lo = hi = 0.0
    parts = []
    for n in necks:
        rng = n.get("range") or (n["section_m2"], n["section_m2"])
        lo += rng[0]
        hi += rng[1]
        parts.append(f"{n['id']} {n['section_m2']:.4f}" + ("" if rng[0] == rng[1] else f" ({rng[0]:.4f}..{rng[1]:.4f})"))
    if hi > a + TOL:
        raise RefusedError(f"{outline_id}: neck footprints {hi:.4f} exceed the footing outline {a:.4f}")
    single_hi, single_lo = a - lo, a - hi
    basis = f"{ftype} outline {a:.4f} - necks [{'; '.join(parts) or 'none'}]"
    readings = {"SINGLE": single_lo} if single_lo == single_hi else {"SINGLE_low": single_lo, "SINGLE_high": single_hi}
    if detail_selected == "SINGLE":
        if single_lo != single_hi:
            return Row(outline_id, "FOOTING", "top outside the necks", "m2", None, HELD, basis, readings,
                       "NECK_SECTION_CONFLICT")
        return Row(outline_id, "FOOTING", "top outside the necks", "m2", single_lo, DC, basis)
    why = ("DETAIL_NOT_SELECTED: the selecting level (formation vs ground-beam top, 2.5 m) is not printed; reading SINGLE "
           "shown, reading DOUBLE has no value (the lower ground beam on the top is not drawn)")
    if detail_selected == "DOUBLE":
        why = "DOUBLE detail: the lower ground beam covering part of the top is not drawn on plan"
    return Row(outline_id, "FOOTING", "top outside the necks", "m2", None, HELD, basis, readings, why)


def neck_row(neck_id, ntype, W, D, height=None, height_why="NECK_HEIGHT_HELD"):
    """Neck side faces = perimeter x height; HELD with the m2-per-metre rate while the height is held."""
    W = _metres(W, "neck width")
    D = _metres(D, "neck depth")
    p = 2.0 * (W + D)
    if height is None:
        return Row(neck_id, "NECK", "4 sides", "m2", None, HELD, f"{ntype} perimeter 2 x ({W:.2f} + {D:.2f}) = {p:.2f} m "
                   "x neck height", {"m2_per_m_height": p}, height_why)
    height = _metres(height, "neck height")
    return Row(neck_id, "NECK", "4 sides", "m2", p * height, DC, f"perimeter {p:.2f} x height {height:.3f}")


def underlay_face_refused(face):
    """The footing soffit / underlay belongs to the membrane + screed line (T-219), never to the liquid coat."""
    if face in ("FOOTING_SOFFIT", "FOOTING_UNDERLAY", "FOOTING_SIDES"):
        raise RefusedError(f"{face} is owned by the footing-underlay line (WP.FOOTING_MEMBRANE / WP.FOOTING_SIDES): "
                           "counting it again as a liquid coat is refused (each face once)")
    return face


def procurement_row(element, product=None, coverage=None):
    if product and coverage:
        return Row(element, "PROCUREMENT", "liquid coating material", "printed coverage", None, HELD,
                   f"product {product}, coverage {coverage}: rule not yet in the owner rule library", {},
                   "NO_OWNER_RULE")
    return Row(element, "PROCUREMENT", "liquid coating material", "litres / kg", None, HELD,
               "UP-WP-MAT-001 BY_SPEC", {}, "PRODUCT_NOT_PRINTED: product, coats and coverage not printed")


def totals(rows):
    """Per member and status: DRAWING-CONFIRMED rows carry their m2 sum; HELD / EXCLUDED rows carry a COUNT only
    (a held quantity is never shown as 0 or summed)."""
    out = {}
    for r in rows:
        k = f"{r.member}|{r.status}"
        if r.status == DC:
            out[k] = r6(out.get(k, 0.0) + r.qty)
        else:
            out[k] = {"rows": out.get(k, {"rows": 0})["rows"] + 1}
    return dict(sorted(out.items()))


def measured_total(rows):
    """Sum of DRAWING-CONFIRMED rows only: a HELD or EXCLUDED row never enters it (never as 0)."""
    return r6(sum(r.qty for r in rows if r.status == DC))
