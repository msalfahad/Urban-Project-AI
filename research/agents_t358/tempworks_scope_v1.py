"""TEMPWORKS_SCOPE_V1 (T-358): is B1-06 dewatering / excavation support / temporary works in scope, and under what
condition. Pure rules, stdlib only. Research rule (scope every villa, provenance T-358), not a rule-library version.

Physical elements (ERS s.2.1):
  DEWATERING  = lowering the groundwater below the formation of an excavation for the duration of the works. It is
                needed only where a formation (bottom of the excavation, under the blinding) reaches the water level.
  SUPPORT     = shoring / protection of an excavation face so that the soil beyond it (a neighbour plot, a street, an
                existing structure) does not move. A face is EXPOSED to a plot side when its horizontal distance to
                that side is not more than its own depth below the existing ground (the 1 : 1 influence line named in
                the T-358 acceptance); a face ON or BEYOND the plot line is exposed at any depth.
  TEMPORARY   = other site temporary works (formwork props are the formwork item's, never B1-06).

Rules:
  R-TW-1  A status comes only from a printed source (sheet + note number). Without a printed water level the
          dewatering status is UNKNOWN, never NOT_TRIGGERED; a convention, a reference book or another project is not
          a source.
  R-TW-2  Levels are on the existing-ground datum (EG). A water depth is converted with the datum its source states
          (or the datum of the notes it is printed with, recorded as INTERPRETED); a FINISHED level offered as EG is
          refused.
  R-TW-3  Formation kinds: PRINTED (one value), AT_MOST (the source gives only an upper limit: "not less than x below
          EG", open below) and PARAMETRIC (level = a - d, d not printed, e.g. a pit depth 'as per manufacturer').
          PRINTED above water -> NOT_TRIGGERED with its clearance; PRINTED at / below -> TRIGGERED; AT_MOST limit
          above water -> CONDITIONAL (trigger: formation lowered by limit - water); PARAMETRIC -> CONDITIONAL with the
          threshold value of d. The project status is the worst of its elements (TRIGGERED > CONDITIONAL >
          NOT_TRIGGERED) and a note that is itself conditional never lifts a measured TRIGGERED.
  R-TW-4  Exposure of an excavation face to a plot side by distance d (m, negative = beyond the line) and depth:
          d <= 0 -> ON_OR_BEYOND_LINE; PRINTED depth: d <= depth -> WITHIN else OUTSIDE; AT_LEAST depth (the
          limit, open below): d <= limit -> WITHIN else CONDITIONAL (trigger depth >= d); depth HELD -> CONDITIONAL
          (trigger depth >= d). A distance is a geometric fact, not a quantity.
  R-TW-5  B1-06 is an ITEM: a quantity (m, m2, m3, days, pumps) exists only with a drawn or specified extent; a
          quantity written without an extent is refused; an unresolved one is HELD (None), never 0.
"""
from __future__ import annotations

RULE_ID = "TEMPWORKS_SCOPE_V1"
UNITS = ("m",)
FORMATION_KINDS = ("PRINTED", "AT_MOST", "PARAMETRIC")
DEPTH_KINDS = ("PRINTED", "AT_LEAST", "HELD")
RANK = {"NOT_TRIGGERED": 0, "CONDITIONAL": 1, "TRIGGERED": 2}
EPS = 1e-9


class Refused(ValueError):
    """A rule of TEMPWORKS_SCOPE_V1 refuses the input."""


def _unit(u):
    if u not in UNITS:
        raise Refused(f"unit {u!r} not declared as metres (R-TW-2)")


def _source(src):
    if not src or not isinstance(src, dict) or not src.get("sheet") or not src.get("note"):
        raise Refused("a status needs a printed source: sheet + note number (R-TW-1)")
    if src.get("kind") in ("CONVENTION", "REFERENCE_BOOK", "OTHER_PROJECT", "FREELANCER", "USUAL_PRACTICE"):
        raise Refused(f"{src.get('kind')} is not a source (R-TW-1)")


def water_level(water):
    """Water level on the EG datum (m, EG = 0, up positive) from a printed water record, or None (R-TW-1 / R-TW-2).

    water = {"depth": 4.5, "unit": "m", "datum": "EG" | "FINISHED" | ..., "datum_level": 0.0, "source": {...}}"""
    if water is None:
        return None
    _source(water.get("source"))
    _unit(water.get("unit"))
    if water.get("datum") != "EG":
        raise Refused(f"water depth measured from a {water.get('datum')} level is not on the EG datum (R-TW-2)")
    if water.get("datum_level") is None:
        raise Refused("EG datum level not stated (R-TW-2)")
    d = float(water["depth"])
    if d <= 0:
        raise Refused("a water depth must be positive below its datum")
    return float(water["datum_level"]) - d


def formation_status(f, wl):
    """One element's dewatering status against the water level wl (EG datum)."""
    _unit(f.get("unit"))
    kind = f.get("kind")
    if kind not in FORMATION_KINDS:
        raise Refused(f"formation kind {kind!r} (R-TW-3)")
    if f.get("level_basis") == "FINISHED":
        raise Refused("a finished level is not a formation / EG level (R-TW-2)")
    out = {"element": f["element"], "kind": kind}
    if wl is None:
        out.update(status="UNKNOWN", trigger=None, clearance_m=None)
        return out
    if kind == "PRINTED":
        lv = float(f["level"])
        c = round(lv - wl, 6)
        out.update(status="TRIGGERED" if c <= EPS else "NOT_TRIGGERED", clearance_m=c,
                   trigger=f"formation {lv:+.3f} vs water {wl:+.3f}")
    elif kind == "AT_MOST":
        lim = float(f["limit"])
        c = round(lim - wl, 6)
        if c <= EPS:
            out.update(status="TRIGGERED", clearance_m=c, trigger=f"limit {lim:+.3f} already at / below water")
        else:
            out.update(status="CONDITIONAL", clearance_m=c,
                       trigger=f"only if the formation is lowered {c:.3f} m or more below its printed limit "
                               f"{lim:+.3f} (to {wl:+.3f} or deeper)")
    else:  # PARAMETRIC: level = a + b * p  (b < 0: deeper as p grows); trigger p >= (wl - a) / b
        a, b = float(f["a"]), float(f["b"])
        if b >= 0:
            raise Refused("a parametric formation must go down as its parameter grows (b < 0)")
        p = round((wl - a) / b, 6)
        lim = f.get("limit")  # the element may also carry an AT_MOST limit (e.g. the general excavation note)
        out.update(status="CONDITIONAL", clearance_m=None, threshold=p,
                   trigger=f"only if {f['param']} >= {p:.3f} m" + (f" (and never above {float(lim):+.3f})" if lim is not None else ""))
    return out


def dewatering(formations, water, note_conditional=True):
    """Project dewatering status: per element (R-TW-3) and the worst. note_conditional: the printed note itself says
    'if groundwater is found'; it keeps a CONDITIONAL / NOT_TRIGGERED result open on site, never lifts TRIGGERED."""
    if not formations:
        raise Refused("no formation listed: the deepest excavation must be named")
    names = [f["element"] for f in formations]
    if len(set(names)) != len(names):
        raise Refused("an element listed twice")
    wl = water_level(water)
    rows = [formation_status(f, wl) for f in formations]
    if wl is None:
        return {"status": "UNKNOWN", "water_level": None, "rows": rows, "quantity": None}
    worst = max(rows, key=lambda r: RANK[r["status"]])["status"]
    printed = [r["clearance_m"] for r in rows if r["kind"] in ("PRINTED", "AT_MOST")]
    return {"status": worst, "water_level": wl, "rows": rows,
            "min_clearance_m": min(printed) if printed else None,
            "site_condition": bool(note_conditional), "quantity": None}


def face_distances(rect, plot, projection=0.0):
    """Distances (m) from the four faces of an excavation rectangle to the four sides of an axis-parallel plot.

    rect = (x0, y0, dx, dy) in m from the plot corner; plot = (Lx, Ly); projection = how far the excavation face stands
    beyond the element outline (e.g. a blinding projection). Negative = the face is beyond that plot line."""
    x0, y0, dx, dy = (float(v) for v in rect)
    lx, ly = (float(v) for v in plot)
    if dx <= 0 or dy <= 0 or lx <= 0 or ly <= 0:
        raise Refused("rectangle / plot sizes must be positive")
    p = float(projection)
    return {"S0": round(y0 - p, 6), "S1": round(ly - (y0 + dy) - p, 6),
            "S2": round(x0 - p, 6), "S3": round(lx - (x0 + dx) - p, 6)}


def exposure(d, depth):
    """R-TW-4. depth = {"kind": PRINTED|AT_LEAST|HELD, "value"/"limit": m}."""
    kind = depth.get("kind")
    if kind not in DEPTH_KINDS:
        raise Refused(f"depth kind {kind!r} (R-TW-4)")
    if depth.get("basis") == "FINISHED":
        raise Refused("an excavation depth measured from a finished level is not a depth below EG (R-TW-2)")
    if d <= EPS:
        return {"class": "ON_OR_BEYOND_LINE", "trigger_depth_m": 0.0}
    if kind == "PRINTED":
        v = float(depth["value"])
        return {"class": "WITHIN" if d <= v + EPS else "OUTSIDE", "trigger_depth_m": round(d, 6)}
    if kind == "AT_LEAST":
        lim = float(depth["limit"])
        return {"class": "WITHIN" if d <= lim + EPS else "CONDITIONAL", "trigger_depth_m": round(d, 6)}
    return {"class": "CONDITIONAL", "trigger_depth_m": round(d, 6)}


SIDE_STATUS = {"ON_OR_BEYOND_LINE": "TRIGGERED", "WITHIN": "TRIGGERED", "CONDITIONAL": "CONDITIONAL",
               "OUTSIDE": "NOT_TRIGGERED"}


def support_by_side(excavations, plot, side_names):
    """Per plot side: every excavation face's distance and exposure, and the side's support status (the worst).

    excavations: [{"id", "rect", "projection", "depth": {...}, "projection_status"}]."""
    ids = [e["id"] for e in excavations]
    if len(set(ids)) != len(ids):
        raise Refused("an excavation listed twice")
    if set(side_names) != {"S0", "S1", "S2", "S3"}:
        raise Refused("four plot sides S0..S3 must be named")
    rows = []
    for e in excavations:
        ds = face_distances(e["rect"], plot, e.get("projection", 0.0))
        for s, d in ds.items():
            x = exposure(d, e["depth"])
            rows.append({"id": e["id"], "side": s, "side_name": side_names[s], "distance_m": d, **x,
                         "depth_kind": e["depth"]["kind"]})
    sides = {}
    for s in ("S0", "S1", "S2", "S3"):
        rs = [r for r in rows if r["side"] == s]
        st = max((SIDE_STATUS[r["class"]] for r in rs), key=lambda k: RANK[k])
        on = sorted(r["id"] for r in rs if r["class"] == "ON_OR_BEYOND_LINE")
        within = sorted(r["id"] for r in rs if r["class"] == "WITHIN")
        cond = [r for r in rs if r["class"] == "CONDITIONAL"]
        sides[s] = {"name": side_names[s], "status": st, "on_or_beyond_line": on, "within": within,
                    "nearest_m": min(r["distance_m"] for r in rs),
                    "conditional_min_trigger_m": min((r["trigger_depth_m"] for r in cond), default=None),
                    "quantity": None}
    return {"rows": rows, "sides": sides}


def item_quantity(status, extent):
    """R-TW-5: an item quantity needs a drawn / specified extent; otherwise HELD (None), never 0."""
    if status not in ("TRIGGERED", "CONDITIONAL", "NOT_TRIGGERED", "UNKNOWN"):
        raise Refused(f"status {status!r}")
    if extent is None:
        return None
    if not isinstance(extent, dict) or not extent.get("source") or extent.get("value") is None or not extent.get("unit"):
        raise Refused("an extent needs a value, a unit and a printed source (R-TW-5)")
    _source(extent["source"])
    if status == "NOT_TRIGGERED":
        raise Refused("a quantity under NOT_TRIGGERED (R-TW-5)")
    return {"value": float(extent["value"]), "unit": extent["unit"]}


def write_quantity(item):
    """Refuse a quantity written for an item without its extent (adverse case of acceptance d)."""
    if item.get("quantity") not in (None,) and not item.get("extent"):
        raise Refused(f"{item.get('item')}: quantity {item['quantity']!r} without a drawn / specified extent (R-TW-5)")
    if item.get("quantity") == 0 and item.get("status") != "NOT_TRIGGERED":
        raise Refused("held written as 0 (R-TW-5)")
    return item
