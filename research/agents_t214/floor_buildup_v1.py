"""T-214 FLOOR_BUILDUP_V1: the floor build-up between a finished floor level and the structural top, per floor and zone,
with the drawing-derived method and the owner manual method kept side by side (any villa; unwired research module).

Physical element: the layers between the FFL (a FINISHED datum) and the top of the structural slab under it (a
STRUCTURAL datum): finish, adhesive, mortar bed / screed / fill, membrane where present. Its thickness b fixes every
structural level that the drawings give only as a finished level (slab top = FFL - b), e.g. ground-beam tops, neck tops,
beam tops at stair heads.

Drawing-derived method (evidence order, ERS s.2.2):
  1. a printed structural top of the zone (kind must be STRUCTURAL; a FINISHED level offered as the structural top is
     refused: FINISHED_AS_STRUCTURAL) or a printed build-up thickness  -> DRAWING-CONFIRMED;
  2. a drawn, unprinted layer between the level line and the hatched structure of a cut section: accepted only when the
     vector measurement and a current-issue measurement agree (TOL_DRAWN), and only for a zone of the same type as the
     cut zone (a dry-floor layer is never carried to a wet or sunken zone) -> DRAWING-CONFIRMED (drawn, unprinted);
     vector only -> HELD (REVISION_NOT_CHECKED); the two disagree -> CONFLICT;
  3. a CONSTANT drawn layer on a ROOF zone (falls always: printed, or the owner's falls rule where none is printed)
     or on an OUTDOOR zone whose sheets print falls is not that zone's build-up: a fall makes the build-up vary, so it
     is HELD (CONSTANT_LAYER_VS_FALLS) until a build-up at a named point is printed;
  4. a SUNKEN zone needs its printed drop; without it the zone is HELD (SUNKEN_DROP_NOT_PRINTED);
  5. two established sources that disagree -> CONFLICT; nothing -> HELD. b is never 0 by default.

Owner manual method: the answered owner items that give a thickness, each with its SCOPE. Only an item whose scope is
LEVEL_DATUM may fix a structural level; an allowance inside a height formula (e.g. a 'floor finishing' deduction in a
wall-height rule) or a mortar-bed range is shown beside with its residual against the drawing-derived value, and is
refused as a datum (ALLOWANCE_AS_DATUM): a value's meaning is not extended to another element type (ERS s.3).

Conditions: 'the quantity holds while min <= b <= max' (a downstream ledger's stated margin) is evaluated per basis:
PROVEN / VIOLATED / NOT PROVEN, never by picking the basis that passes.
"""
from __future__ import annotations

METHOD = "FLOOR_BUILDUP_V1"
ZONE_TYPES = ("DRY", "WET", "SUNKEN", "OUTDOOR", "ROOF")
SOURCES = ("PRINTED_TOP", "PRINTED_THICKNESS", "DRAWN_VECTOR", "DRAWN_CURRENT_ISSUE")
STRUCTURAL_KINDS = ("SLAB_TOP", "GB_TOP", "BEAM_TOP")
FINISHED_KINDS = ("FFL", "FINISHED_ROOF", "FINISHED_GROUND")
SCOPES = ("LEVEL_DATUM", "WALL_HEIGHT_ALLOWANCE", "MORTAR_BED", "SCREED")
TOL = 0.005          # m: printed levels and thicknesses agree to 5 mm
TOL_DRAWN = 0.010    # m: vector vs current-issue scan of a drawn layer (a 400 dpi scan at 1:100 resolves ~6 mm)
SCALE = {"m": 1.0, "mm": 0.001}


def _k(units):
    if units not in SCALE:
        raise ValueError(f"unknown units {units!r}")
    return SCALE[units]


def _num(v, k, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{what}: a number is required, got {v!r}")
    return float(v) * k


def _ref(r, what):
    if not isinstance(r, str) or not r.strip():
        raise ValueError(f"{what}: a source reference is required")
    return r


def _drawing(zone, ffl, k):
    zid, ztype = zone["zone_id"], zone["type"]
    notes, est = [], []                     # est: (b, label, ref)
    vec, cur = [], []
    for i, e in enumerate(zone.get("evidence", [])):
        what = f"zone {zid} evidence {i}"
        src = e.get("source")
        if src not in SOURCES:
            raise ValueError(f"{what}: unknown source {src!r}")
        ref = _ref(e.get("ref"), what)
        if src == "PRINTED_TOP":
            kind = e.get("kind")
            if kind in FINISHED_KINDS:
                raise ValueError(f"{what}: FINISHED_AS_STRUCTURAL: {kind} offered as the structural top")
            if kind not in STRUCTURAL_KINDS:
                raise ValueError(f"{what}: unknown structural kind {kind!r}")
            est.append((ffl - _num(e.get("value"), k, what), "PRINTED structural top", ref))
            continue
        t = _num(e.get("thickness"), k, what)
        if t < 0:
            raise ValueError(f"{what}: negative thickness")
        if src == "PRINTED_THICKNESS":
            est.append((t, "PRINTED build-up", ref))
            continue
        cut_type = e.get("cut_zone_type")
        if cut_type not in ZONE_TYPES:
            raise ValueError(f"{what}: cut_zone_type is required for a drawn layer")
        if cut_type != ztype:
            notes.append(f"drawn layer of a cut {cut_type} zone not carried to this {ztype} zone ({ref})")
            continue
        falls = ztype == "ROOF" or zone.get("printed_falls")
        if falls and e.get("constant_layer", True):
            notes.append(f"CONSTANT_LAYER_VS_FALLS: a constant drawn layer {t:.3f} m cannot carry the falls of a "
                         f"{ztype} zone (printed, or the owner's falls rule where none is printed) ({ref})")
            continue
        (vec if src == "DRAWN_VECTOR" else cur).append((t, ref))
    if vec and cur:
        vs, cs = [t for t, _ in vec], [t for t, _ in cur]
        if max(vs + cs) - min(vs + cs) > TOL_DRAWN:
            return {"b": None, "status": "CONFLICT", "basis": "DRAWN layer: vector vs current issue disagree",
                    "values": sorted({round(x, 4) for x in vs + cs}), "notes": notes}
        est.append((vs[0], "DRAWN (unprinted) layer, vector + current issue agree", vec[0][1] + " | " + cur[0][1]))
    elif vec:
        notes.append("REVISION_NOT_CHECKED: a drawn layer read on one source only is not established")
    elif cur:
        notes.append("a scan reading alone is not a measurement (no vector source): not established")
    if ztype == "SUNKEN" and zone.get("sunken_drop") is None:
        return {"b": None, "status": "HELD", "basis": "SUNKEN_DROP_NOT_PRINTED", "notes": notes,
                "missing": ["the drop of the sunken panel"]}
    if not est:
        return {"b": None, "status": "HELD", "basis": "NOT_PRINTED_NOT_DRAWN", "notes": notes,
                "missing": ["a printed structural top, a printed build-up or a drawn layer checked on the current issue"]}
    bs = [b for b, _, _ in est]
    if max(bs) - min(bs) > TOL:
        return {"b": None, "status": "CONFLICT", "basis": " vs ".join(f"{b:.3f} ({lab})" for b, lab, _ in est),
                "values": sorted({round(b, 4) for b in bs}), "notes": notes}
    b, lab, ref = est[0]
    if ztype == "SUNKEN":
        b = b + _num(zone["sunken_drop"], k, f"zone {zid} sunken_drop")
        lab += " + printed sunken drop"
    if b < -TOL:
        raise ValueError(f"zone {zid}: structural top above the FFL by {-b:.3f} m: check the datums")
    return {"b": round(b, 4), "status": "DRAWING-CONFIRMED", "basis": lab, "ref": ref, "notes": notes}


def _owner(zone, k, drawn_b):
    rows = []
    for i, o in enumerate(zone.get("owner_items", [])):
        what = f"zone {zone['zone_id']} owner item {i}"
        if o.get("scope") not in SCOPES:
            raise ValueError(f"{what}: unknown scope {o.get('scope')!r}")
        lo = _num(o.get("lo"), k, what)
        hi = _num(o.get("hi", o.get("lo")), k, what)
        if hi < lo:
            raise ValueError(f"{what}: hi < lo")
        missing = list(o.get("parts_missing", []))
        row = {"rule": _ref(o.get("rule"), what), "scope": o["scope"], "lo": round(lo, 4), "hi": round(hi, 4),
               "parts_missing": missing, "partial": bool(missing),
               "usable_as_datum": o["scope"] == "LEVEL_DATUM" and not missing,
               "status": "ASSUMED — OWNER-APPROVED (own scope only)"}
        if drawn_b is not None:
            row["residual_drawn_minus_owner"] = [round(drawn_b - hi, 4), round(drawn_b - lo, 4)]
            row["residual_named"] = ("the missing parts " + ", ".join(missing)) if missing and drawn_b > hi + TOL \
                else ("none" if lo - TOL <= drawn_b <= hi + TOL else "different scope / basis (see the rule's scope)")
        rows.append(row)
    return rows


def structural_top(floor_result, zone_id, basis="DRAWING"):
    """Slab top of one zone under one basis; refuses an owner allowance used as a datum and a HELD / CONFLICT b."""
    z = floor_result["zones"][zone_id]
    if basis == "DRAWING":
        if z["drawing"]["b"] is None:
            raise ValueError(f"{zone_id}: build-up {z['drawing']['status']}: no structural top (never the FFL)")
        return round(floor_result["ffl"] - z["drawing"]["b"], 4)
    if basis == "OWNER_MANUAL":
        ok = [o for o in z["owner_manual"] if o["usable_as_datum"]]
        if not ok:
            raise ValueError(f"{zone_id}: ALLOWANCE_AS_DATUM: no owner item with scope LEVEL_DATUM")
        o = ok[0]
        return [round(floor_result["ffl"] - o["hi"], 4), round(floor_result["ffl"] - o["lo"], 4)]
    raise ValueError(f"unknown basis {basis!r}")


def evaluate(project):
    k = _k(project.get("units", "m"))
    floors = {}
    for f in project.get("floors", []):
        fid = f["floor_id"]
        ffl = f.get("ffl") or {}
        if ffl.get("kind") not in FINISHED_KINDS:
            raise ValueError(f"floor {fid}: the floor datum must be a FINISHED level, got {ffl.get('kind')!r}")
        _ref(ffl.get("ref"), f"floor {fid} ffl")
        v = _num(ffl.get("value"), k, f"floor {fid} ffl")
        zones = {}
        for z in f.get("zones", []):
            if z.get("type") not in ZONE_TYPES:
                raise ValueError(f"zone {z.get('zone_id')}: unknown type {z.get('type')!r}")
            d = _drawing(z, v, k)
            zones[z["zone_id"]] = {"type": z["type"], "drawing": d, "owner_manual": _owner(z, k, d["b"])}
            if d["b"] is not None:
                zones[z["zone_id"]]["slab_top_drawing"] = round(v - d["b"], 4)
        floors[fid] = {"ffl": round(v, 4), "ffl_ref": ffl["ref"], "zones": zones}
    conds = []
    for c in project.get("conditions", []):
        cid = c["condition_id"]
        fr = floors[c["floor_id"]]
        z = fr["zones"][c["zone_id"]]
        mx = _num(c["max_build_up"], k, f"condition {cid}")
        mn = _num(c["min_build_up"], k, f"condition {cid}") if "min_build_up" in c else float("-inf")
        row = {"condition_id": cid, "ref": _ref(c.get("ref"), f"condition {cid}"),
               "range": [None if mn == float("-inf") else round(mn, 4), round(mx, 4)]}
        b = z["drawing"]["b"]
        if b is None:
            row["DRAWING"] = f"NOT PROVEN (build-up {z['drawing']['status']})"
        else:
            row["DRAWING"] = ("PROVEN" if mn - TOL <= b <= mx + TOL else "VIOLATED") + \
                f" (b = {b:.3f} m, {z['drawing']['status']})"
        dat = [o for o in z["owner_manual"] if o["usable_as_datum"]]
        if dat:
            o = dat[0]
            ok = mn - TOL <= o["lo"] and o["hi"] <= mx + TOL
            row["OWNER_MANUAL"] = ("PROVEN" if ok else "NOT PROVEN") + " (ASSUMED — OWNER-APPROVED)"
        elif z["owner_manual"]:
            row["OWNER_MANUAL"] = "NOT PROVEN (ALLOWANCE_AS_DATUM: " + ", ".join(
                f"{o['rule']} is {o['scope']}" for o in z["owner_manual"]) + ")"
        else:
            row["OWNER_MANUAL"] = "NOT PROVEN (no owner item)"
        conds.append(row)
    return {"method": METHOD, "floors": floors, "conditions": conds}
