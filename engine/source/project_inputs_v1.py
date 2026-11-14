"""PROJECT INPUTS SHEET V1 (T-782; owner ACCURACY_PLAN_2026-11-14 change A): the first object of every project.

One sheet per villa holds the storey table (FFL, next FFL, slab thickness, beam-depth default, ceiling drop, wet-room
ceiling and tile heights, plinth), grades, wastage % and scope switches. Every value carries its SOURCE:
  PRINTED        read from a drawing (ref = sheet / section)
  OWNER-DEFAULT  an owner rule or company default (ref = rule id / date)
  DESIGNER       the designer's answer (replaces a default)
  HELD           optional items only: no value yet, kept by name, never 0
A required value that is missing, HELD, non-numeric or without a source is REFUSED (MissingInputError); nothing is
defaulted to 0. Derived heights (plaster, paint, blockwork) come from ONE function each, with their formula, their
components' sources and a BOQ label (DRAWING-READ when every component is PRINTED / DESIGNER, else DEFAULT).
A storey whose level band overlaps another storey's band is flagged SPLIT_LEVEL (its heights are still derived); a
SLOPED storey (two FFLs) is flagged and its heights are HELD (state HELD, value None), never averaged.

Project-agnostic; stdlib only. Reads nothing from any candidate; changes no BOQ line.
"""

from __future__ import annotations

import json
import math

SCHEMA = "PROJECT_INPUTS_V1"
SOURCES = ("PRINTED", "OWNER-DEFAULT", "DESIGNER")
HELD = "HELD"
EPS = 1e-9

# required per storey; optional per storey (may be HELD)
STOREY_REQUIRED = ("ffl", "next_ffl", "slab_thickness")
STOREY_OPTIONAL = ("beam_depth_default", "ceiling_drop", "wet_ceiling_height", "wet_tile_height", "plinth_height")
SCOPE_SWITCHES = ("foundation_wp", "fence")


class InputsError(ValueError):
    """The sheet is malformed (schema, ids, sources)."""


class MissingInputError(InputsError):
    """A required value is missing / HELD / invalid: the sheet is refused, never defaulted to 0."""


# ----------------------------------------------------------------------------------------------- values
def _val(field: str, rec, *, required: bool, positive: bool = True, allow_bool: bool = False):
    """Validate one {value, source, ref} record; returns it normalised or raises."""
    if rec is None:
        if required:
            raise MissingInputError(f"{field}: missing (required; never defaulted)")
        return {"value": None, "source": HELD, "ref": "absent"}
    if not isinstance(rec, dict) or "source" not in rec:
        raise InputsError(f"{field}: every value is a record with 'value' and 'source'")
    src = rec.get("source")
    v = rec.get("value")
    if src == HELD or v is None:
        if required:
            raise MissingInputError(f"{field}: HELD / no value (required; never defaulted)")
        return {"value": None, "source": HELD, "ref": rec.get("ref") or rec.get("why") or ""}
    if src not in SOURCES:
        raise InputsError(f"{field}: source {src!r} not in {SOURCES + (HELD,)}")
    if not rec.get("ref"):
        raise InputsError(f"{field}: a {src} value needs its ref (sheet / rule / answer)")
    if allow_bool:
        if not isinstance(v, bool):
            raise InputsError(f"{field}: a scope switch is true / false")
        return {"value": v, "source": src, "ref": rec["ref"]}
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise InputsError(f"{field}: value {v!r} is not a finite number")
    if positive and v <= 0:
        raise MissingInputError(f"{field}: value {v} must be > 0 (0 is never a stand-in for missing)")
    return {"value": float(v), "source": src, "ref": rec["ref"]}


def _merge(defaults: dict, storey: dict, name: str):
    """A storey value overrides the sheet-wide default of the same name."""
    return storey[name] if name in storey else defaults.get(name)


# ----------------------------------------------------------------------------------------------- load
def load(sheet) -> dict:
    """Validate a sheet (dict, JSON text or path) and return the normalised sheet. Raises on any missing storey value."""
    if isinstance(sheet, str):
        if sheet.lstrip().startswith("{"):
            sheet = json.loads(sheet)
        else:
            with open(sheet, encoding="utf-8") as fh:
                sheet = json.load(fh)
    if not isinstance(sheet, dict) or sheet.get("schema") != SCHEMA:
        raise InputsError(f"not a {SCHEMA} sheet")
    if not sheet.get("project_id"):
        raise InputsError("project_id missing")
    storeys = sheet.get("storeys")
    if not storeys:
        raise MissingInputError("storeys: the storey table is empty (a project needs at least one storey)")
    defaults = sheet.get("storey_defaults") or {}
    out_st, seen = [], set()
    for i, st in enumerate(storeys):
        sid = st.get("id")
        if not sid:
            raise MissingInputError(f"storeys[{i}]: storey id missing")
        if sid in seen:
            raise InputsError(f"storeys: duplicate id {sid}")
        seen.add(sid)
        n = {"id": sid, "name": st.get("name", sid), "parent": st.get("parent")}
        sloped = st.get("sloped", False)
        for f in STOREY_REQUIRED:
            rec = _merge(defaults, st, f)
            if f in ("ffl", "next_ffl"):
                if sloped and f == "ffl":
                    lo = _val(f"{sid}.ffl_low", st.get("ffl_low"), required=True, positive=False)
                    hi = _val(f"{sid}.ffl_high", st.get("ffl_high"), required=True, positive=False)
                    n["ffl_low"], n["ffl_high"] = lo, hi
                    n["ffl"] = {"value": None, "source": HELD, "ref": "sloped storey: two FFLs"}
                    continue
                n[f] = _val(f"{sid}.{f}", rec, required=True, positive=False)
            else:
                n[f] = _val(f"{sid}.{f}", rec, required=True)
        for f in STOREY_OPTIONAL:
            n[f] = _val(f"{sid}.{f}", _merge(defaults, st, f), required=False)
        n["flags"] = []
        if sloped:
            n["flags"].append("SLOPED")
        else:
            h = n["next_ffl"]["value"] - n["ffl"]["value"]
            if h <= EPS:
                raise MissingInputError(f"{sid}: next_ffl {n['next_ffl']['value']} not above ffl {n['ffl']['value']}")
            if n["slab_thickness"]["value"] >= h - EPS:
                raise InputsError(f"{sid}: slab thickness {n['slab_thickness']['value']} >= storey height {h}")
        out_st.append(n)
    _flag_split_levels(out_st)
    scope = {}
    for s in SCOPE_SWITCHES:
        scope[s] = _val(f"scope.{s}", (sheet.get("scope") or {}).get(s), required=False, allow_bool=True)
    grades = {k: _val(f"grades.{k}", v, required=False) for k, v in (sheet.get("grades") or {}).items()}
    wastage = {k: _val(f"wastage_pct.{k}", v, required=False) for k, v in (sheet.get("wastage_pct") or {}).items()}
    return {"schema": SCHEMA, "project_id": sheet["project_id"], "units": "m", "storeys": out_st,
            "scope": scope, "grades": grades, "wastage_pct": wastage, "notes": sheet.get("notes", [])}


def _band(st):
    if "SLOPED" in st["flags"]:
        return (min(st["ffl_low"]["value"], st["ffl_high"]["value"]), st["next_ffl"]["value"])
    return (st["ffl"]["value"], st["next_ffl"]["value"])


def _flag_split_levels(storeys):
    """Two storeys whose level bands overlap without sharing the same FFL are a split level: both are flagged."""
    for a in storeys:
        for b in storeys:
            if a is b:
                continue
            (a0, a1), (b0, b1) = _band(a), _band(b)
            if a0 < b1 - EPS and b0 < a1 - EPS and abs(a0 - b0) > EPS:
                tag = "SPLIT_LEVEL:" + b["id"]
                if tag not in a["flags"]:
                    a["flags"].append(tag)


def storey(sheet: dict, sid: str) -> dict:
    for st in sheet["storeys"]:
        if st["id"] == sid:
            return st
    raise MissingInputError(f"storey {sid!r} not in the sheet (never defaulted)")


# ----------------------------------------------------------------------------------------------- derive
def _label(comps):
    return "DRAWING-READ" if all(c["source"] in ("PRINTED", "DESIGNER") for c in comps) else "DEFAULT"


def _result(value, formula, comps, st, **extra):
    return dict({"storey": st["id"], "state": "DERIVED", "value_m": round(value, 6), "formula": formula,
                 "components": comps, "label": _label(comps), "flags": list(st["flags"])}, **extra)


def _held(st, what, why):
    return {"storey": st["id"], "state": HELD, "value_m": None, "what": what, "why": why, "flags": list(st["flags"])}


def _comp(name, rec):
    return {"name": name, "value": rec["value"], "source": rec["source"], "ref": rec["ref"]}


def storey_height(sheet: dict, sid: str) -> dict:
    st = storey(sheet, sid)
    if "SLOPED" in st["flags"]:
        return _held(st, "storey height", "sloped storey: two FFLs, height varies (never averaged)")
    h = st["next_ffl"]["value"] - st["ffl"]["value"]
    return _result(h, "next_ffl - ffl", [_comp("ffl", st["ffl"]), _comp("next_ffl", st["next_ffl"])], st)


def plaster_height(sheet: dict, sid: str) -> dict:
    """Interior plaster height H = storey (FFL to next FFL) - slab thickness (R-T763-1 / Q-72)."""
    st = storey(sheet, sid)
    sh = storey_height(sheet, sid)
    if sh["state"] == HELD:
        return _held(st, "plaster height", sh["why"])
    v = sh["value_m"] - st["slab_thickness"]["value"]
    return _result(v, "(next_ffl - ffl) - slab_thickness",
                   sh["components"] + [_comp("slab_thickness", st["slab_thickness"])], st)


def ceiling_height(sheet: dict, sid: str, wet: bool = False) -> dict:
    """False-ceiling height: dry = H - ceiling_drop; wet rooms / kitchen = wet_ceiling_height (company defaults)."""
    st = storey(sheet, sid)
    ph = plaster_height(sheet, sid)
    if ph["state"] == HELD:
        return _held(st, "ceiling height", ph["why"])
    if wet:
        rec = st["wet_ceiling_height"]
        if rec["value"] is None:
            return _held(st, "wet ceiling height", "wet_ceiling_height HELD")
        v = min(rec["value"], ph["value_m"])
        return _result(v, "wet_ceiling_height (capped at H)", ph["components"] + [_comp("wet_ceiling_height", rec)], st)
    rec = st["ceiling_drop"]
    if rec["value"] is None:
        return _held(st, "ceiling height", "ceiling_drop HELD")
    return _result(ph["value_m"] - rec["value"], "H - ceiling_drop",
                   ph["components"] + [_comp("ceiling_drop", rec)], st)


def paint_height(sheet: dict, sid: str, wet: bool = False) -> dict:
    """Wall paint height: to the false ceiling; in a wet room the tiles (wet_tile_height) cover the wall below the
    ceiling, so paint = max(0, ceiling - tile top) (no paint on tiled faces, owner 2026-11-02)."""
    st = storey(sheet, sid)
    ch = ceiling_height(sheet, sid, wet=wet)
    if ch["state"] == HELD:
        return _held(st, "paint height", ch["why"])
    if not wet:
        return _result(ch["value_m"], "ceiling height (dry)", ch["components"], st)
    tile = st["wet_tile_height"]
    if tile["value"] is None:
        return _held(st, "wet paint height", "wet_tile_height HELD")
    v = max(0.0, ch["value_m"] - tile["value"])
    return _result(v, "max(0, wet ceiling - wet_tile_height)", ch["components"] + [_comp("wet_tile_height", tile)], st,
                   note="0 here is a measured result (tiles reach above the ceiling), not a missing value")


def blockwork_height(sheet: dict, sid: str, under_beam: bool = False, beam_depth_m: float | None = None,
                     beam_ref: str | None = None) -> dict:
    """Blockwork wall height: H = storey - slab; under a beam, minus the beam depth (a printed depth when given, else
    the sheet's beam_depth_default; a missing depth is HELD, never 0)."""
    st = storey(sheet, sid)
    ph = plaster_height(sheet, sid)
    if ph["state"] == HELD:
        return _held(st, "blockwork height", ph["why"])
    if not under_beam:
        return _result(ph["value_m"], "H (no beam on the wall)", ph["components"], st)
    if beam_depth_m is not None:
        if beam_depth_m <= 0 or not beam_ref:
            raise InputsError("a printed beam depth needs a value > 0 and its ref")
        rec = {"value": float(beam_depth_m), "source": "PRINTED", "ref": beam_ref}
    else:
        rec = st["beam_depth_default"]
        if rec["value"] is None:
            return _held(st, "blockwork height under a beam", "no printed beam depth and beam_depth_default HELD")
    v = ph["value_m"] - rec["value"]
    if v <= EPS:
        raise InputsError(f"{sid}: beam depth {rec['value']} leaves no wall under H {ph['value_m']}")
    return _result(v, "H - beam depth", ph["components"] + [_comp("beam_depth", rec)], st)


def summary(sheet: dict) -> list:
    """One row per storey: the derived heights (for the workbook inputs sheet / a reviewer)."""
    rows = []
    for st in sheet["storeys"]:
        sid = st["id"]
        r = {"storey": sid, "flags": st["flags"]}
        for k, fn in (("storey", storey_height), ("plaster", plaster_height), ("blockwork", blockwork_height)):
            d = fn(sheet, sid)
            r[k] = d["value_m"]
        for k, wet in (("ceiling_dry", False), ("ceiling_wet", True)):
            r[k] = ceiling_height(sheet, sid, wet=wet)["value_m"]
        for k, wet in (("paint_dry", False), ("paint_wet", True)):
            r[k] = paint_height(sheet, sid, wet=wet)["value_m"]
        rows.append(r)
    return rows
