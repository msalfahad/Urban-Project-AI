"""DISPLACEMENT_LEDGER_V1 (T-320, research, unwired, stdlib only): the buried-structure DISPLACEMENT side of the
backfill line, every solid or void that occupies the excavation between the formation and the existing ground ONCE,
net of every shared volume, by pit and by trench. Backfill = excavated - displacement; disposal = excavated x bulking -
backfill re-used; both are formed here only when their inputs are values (excavated) or answered rules (bulking).

Physical element (ERS s.2.1). BACKFILL (BOQ family B1-03) is the soil returned into the excavation around the buried
structure up to the EXISTING GROUND EG (the top of the excavation; finished ground outside the building is a finish
laid on EG, e.g. court paving). Everything that sits inside the excavation and is NOT returned soil displaces it:
blinding, underlay, footings, straps, the part of a neck / beam / wall BELOW EG, the shells of pits and pools and the
VOIDS they enclose (a pool's water space is not backfilled either). The part of any component ABOVE EG is not
displacement of this element (it sits in placed fill or in the air): it is refused, never counted. The fill placed
ABOVE EG under a ground slab is a different element (zone Z2) and is not formed here.

Level model. Each component is a prism: plan area A (m2) and a vertical extent [z_b, z_t]. A level is absolute
({"abs": v}) or relative to its group's formation ({"form": k}: z = F + k). A group's formation F is a printed VALUE
({"value": v}), or only a printed LIMIT ({"limit": L}: 'not less than ... below', so F = L - d with d >= 0 HELD), or
absent (every formation-relative component of the group is HELD, value None, never 0). With a limit the below-EG volume
is reported at d = 0 (an AT_LEAST bound when it grows with d) with its coefficient dV/dd (m3 per m of formation below
the limit). A level carried with status HELD and a number is refused (HELD_LEVEL_AS_VALUE).

Sharing. Two components that occupy the same space are counted once: for rectangle plans the module finds every
plan intersection itself and nets the 3-D intersection (plan overlap x vertical overlap below EG); for other plans the
caller supplies the shared plan area (e.g. a footing inside a curved pool envelope). A shared record between groups
with different formations is a function of d; it is reported as a range and is a CONFLICT when the two solids
physically collide (two drawn structures in one volume), never silently netted. Summing components without the
netting is refused (GROSS_OVERLAP_REFUSED).
"""
from __future__ import annotations

METHOD_ID = "DISPLACEMENT_LEDGER_V1"
DRAWING_CONFIRMED, HELD, CONFLICT = "DRAWING-CONFIRMED", "HELD", "CONFLICT"
BOUND_AT_LEAST = "HELD (AT_LEAST bound at the printed limit)"
ZERO_BY_BOUND = "ZERO_BY_BOUND"
CONFIRMED = {DRAWING_CONFIRMED, "VERIFIED", "CALCULATED", ZERO_BY_BOUND}
_UNIT = {"m": 1.0, "cm": 0.01, "mm": 0.001}


class Refused(ValueError):
    def __init__(self, code, msg=""):
        super().__init__(f"{code}: {msg}" if msg else code)
        self.code = code


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def scale(unit):
    if unit not in _UNIT:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    return _UNIT[unit]


def level(fact, unit="m"):
    """A level fact -> (value_m or None, status). A HELD fact carrying a number is refused."""
    s = scale(unit)
    if fact is None:
        return None, HELD
    st = fact.get("status", DRAWING_CONFIRMED)
    v = fact.get("value")
    if st not in CONFIRMED and v is not None:
        raise Refused("HELD_LEVEL_AS_VALUE", f"{fact!r}")
    if st in CONFIRMED and v is None:
        raise Refused("CONFIRMED_LEVEL_WITHOUT_VALUE", f"{fact!r}")
    return (None if v is None else float(v) * s), st


def formation(fact, unit="m"):
    """{"value": v} printed / {"limit": L} AT_MOST bound (F = L - d) / None -> (F0, slope, status)."""
    s = scale(unit)
    if not fact:
        return None, None, HELD
    if fact.get("value") is not None:
        if fact.get("status", DRAWING_CONFIRMED) not in CONFIRMED:
            raise Refused("HELD_LEVEL_AS_VALUE", f"formation {fact!r}")
        return float(fact["value"]) * s, 0.0, fact.get("status", DRAWING_CONFIRMED)
    if fact.get("limit") is not None:
        return float(fact["limit"]) * s, 1.0, HELD
    return None, None, HELD


def _z(spec, form, s):
    """-> (c, slope): z(d) = c - slope * d, or None when the formation it hangs on is absent."""
    if "abs" in spec:
        return float(spec["abs"]) * s, 0.0
    F0, sl, _ = form
    if F0 is None:
        return None
    return F0 + float(spec["form"]) * s, sl


def _below(zb, zt, eg, d):
    b = zb[0] - zb[1] * d
    t = min(zt[0] - zt[1] * d, eg)
    return max(0.0, t - b)


def _rect(c, s):
    r = c.get("rect")
    if r is None:
        return None
    x0, y0, x1, y1 = (float(v) * s for v in r)
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def _rect_overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if (w > 1e-12 and h > 1e-12) else 0.0


def _range_over_d(fn, breaks):
    """min / max of fn(d) for d >= 0 (fn piecewise linear with the given break candidates; d -> large sampled)."""
    cands = sorted({0.0, 50.0} | {b for b in breaks if b > 0})
    vals = [fn(d) for d in cands]
    return min(vals), max(vals)


def build(spec):
    """spec: {"unit", "eg": level fact, "groups": {gid: {"formation": fact, "kind": "PIT"|"TRENCH"|...}},
    "components": [{"id", "group", "kind", "rect" | "plan", "z": [bottom, top], "status", "source", "held": [...],
    "range": [lo, hi] (HELD with a known range), "void": bool}], "shared": [{"a", "b", "plan", "status", "why"}]}"""
    unit = spec.get("unit", "m")
    s = scale(unit)
    eg, eg_st = level(spec.get("eg"), unit)
    if eg is None:
        raise Refused("EXISTING_GROUND_NOT_ESTABLISHED", "no displacement below an unknown ground")
    groups = {g: dict(v, _form=formation(v.get("formation"), unit)) for g, v in spec.get("groups", {}).items()}
    comps, by_id = [], {}
    for c in spec["components"]:
        if c.get("include_above_ground"):
            raise Refused("ABOVE_GROUND_NOT_DISPLACEMENT", c["id"])
        g = groups.get(c["group"])
        if g is None:
            raise Refused("GROUP_NOT_DECLARED", c["group"])
        rect = _rect(c, s)
        plan = (rect[2] - rect[0]) * (rect[3] - rect[1]) if rect else (
            None if c.get("plan") is None else float(c["plan"]) * s * s)
        zb = _z(c["z"][0], g["_form"], s) if c.get("z") else None
        zt = _z(c["z"][1], g["_form"], s) if c.get("z") else None
        st = c.get("status", DRAWING_CONFIRMED)
        held = list(c.get("held", []))
        rec = {"id": c["id"], "group": c["group"], "kind": c["kind"], "void": bool(c.get("void")),
               "source": c.get("source", ""), "plan_m2": _r(plan), "rect": rect, "zb": zb, "zt": zt,
               "status": st, "held": held, "value_m3": None, "coef_m3_per_m": None, "range_m3": None}
        if c.get("info"):
            rec["info"] = c["info"]
        if c.get("value") is not None:                       # a merged volume whose level is not printed
            if not c.get("below_eg_basis"):
                raise Refused("BELOW_EG_NOT_ESTABLISHED", f"{c['id']}: a volume without levels needs the reason "
                              "it lies wholly below the existing ground")
            if st not in CONFIRMED:
                raise Refused("HELD_VOLUME_AS_VALUE", c["id"])
            rec.update(value_m3=_r(float(c["value"]) * s ** 3), coef_m3_per_m=0.0,
                       below_eg_basis=c["below_eg_basis"])
        elif c.get("range") is not None:                     # HELD / CONFLICT with a known range (never a value)
            lo, hi = (float(v) * s ** 3 for v in c["range"])
            rec.update(range_m3=[_r(lo), _r(hi)], status=st if st not in CONFIRMED else HELD)
        elif plan is None or zb is None or zt is None or st not in CONFIRMED and st != BOUND_AT_LEAST:
            if plan is None:
                held.append("PLAN_NOT_ESTABLISHED")
            if zb is None or zt is None:
                held.append("LEVEL_NOT_ESTABLISHED")
            rec["status"] = st if st not in CONFIRMED else HELD
        else:
            v0 = plan * _below(zb, zt, eg, 0.0)
            v1 = plan * _below(zb, zt, eg, 1e-3)
            coef = (v1 - v0) / 1e-3
            rec["value_m3"], rec["coef_m3_per_m"] = _r(v0), _r(coef, 6)
            rec["above_ground_m3_excluded"] = _r(max(0.0, plan * (zt[0] - max(zb[0], eg))) if zt[0] > eg else 0.0)
            if abs(coef) > 1e-9:
                rec["status"] = BOUND_AT_LEAST
                rec["held"] = held + ["FORMATION_ONLY_A_LIMIT"]
            elif zb[1] and g["_form"][2] == HELD and st in CONFIRMED:
                rec["note"] = "volume independent of the unprinted formation (whole element below EG)"
        comps.append(rec)
        by_id[rec["id"]] = rec
    shared = _shared(comps, spec.get("shared", []), eg, by_id, s)
    return {"method": METHOD_ID, "unit_in": unit, "eg_m": eg, "eg_status": eg_st, "components": comps,
            "shared": shared}


def _pair_range(a, b, plan, eg):
    def fn(d):
        lo = max(a["zb"][0] - a["zb"][1] * d, b["zb"][0] - b["zb"][1] * d)
        hi = min(a["zt"][0] - a["zt"][1] * d, b["zt"][0] - b["zt"][1] * d, eg)
        return plan * max(0.0, hi - lo)
    breaks = []
    for p in (a["zb"], a["zt"]):
        for q in (b["zb"], b["zt"], (eg, 0.0)):
            if abs(p[1] - q[1]) > 1e-12:
                breaks.append((p[0] - q[0]) / (p[1] - q[1]))
    return fn(0.0), _range_over_d(fn, breaks)


def _shared(comps, explicit, eg, by_id, s):
    out, seen = [], set()
    rects = [c for c in comps if c["rect"]]
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            ov = _rect_overlap(a["rect"], b["rect"])
            if ov <= 0:
                continue
            if a["value_m3"] is None or b["value_m3"] is None:
                if a["group"] != b["group"]:                 # cannot be netted until the held one is known
                    out.append({"a": a["id"], "b": b["id"], "plan_m2": _r(ov), "value_m3": None, "range_m3": None,
                                "status": HELD, "why": "OVERLAP_WITH_HELD_COMPONENT: plan intersection with a "
                                "component whose level or value is held; netted once both are known"})
                continue
            v0, (lo, hi) = _pair_range(a, b, ov, eg)
            if hi <= 1e-12:
                continue
            same = abs(lo - hi) < 1e-9
            out.append({"a": a["id"], "b": b["id"], "plan_m2": _r(ov), "value_m3": _r(v0) if same else None,
                        "range_m3": None if same else [_r(lo), _r(hi)], "status": "NETTED" if same else HELD,
                        "why": "plan intersection of two positioned prisms, 3-D overlap below EG counted once"})
            seen.add((a["id"], b["id"]))
    for e in explicit:
        a, b = by_id[e["a"]], by_id[e["b"]]
        if a["zb"] is None or b["zb"] is None or a["zt"] is None or b["zt"] is None:
            out.append({"a": e["a"], "b": e["b"], "plan_m2": _r(float(e["plan"]) * s * s), "value_m3": None,
                        "range_m3": None, "status": e.get("status", HELD), "why": e.get("why", "")})
            continue
        plan = float(e["plan"]) * s * s
        v0, (lo, hi) = _pair_range(a, b, plan, eg)
        same = abs(lo - hi) < 1e-9
        st = e.get("status", "NETTED" if same else HELD)
        out.append({"a": e["a"], "b": e["b"], "plan_m2": _r(plan), "value_m3": _r(v0) if same and st == "NETTED"
                    else None, "range_m3": None if same and st == "NETTED" else [_r(lo), _r(hi)],
                    "at_limit_m3": _r(v0), "status": st, "why": e.get("why", "")})
    return out


def totals(ledger, net=True):
    """Sum of the established values, net of every NETTED shared volume; HELD / CONFLICT parts listed apart."""
    if not net and any(x["status"] == "NETTED" for x in ledger["shared"]):
        raise Refused("GROSS_OVERLAP_REFUSED", "components overlap; the gross sum counts shared soil twice")
    value = sum(c["value_m3"] for c in ledger["components"] if c["value_m3"] is not None)
    netted = sum(x["value_m3"] for x in ledger["shared"] if x["status"] == "NETTED")
    bound = any(c["status"] == BOUND_AT_LEAST for c in ledger["components"])
    coef = sum(c["coef_m3_per_m"] or 0.0 for c in ledger["components"])
    held = [c["id"] for c in ledger["components"] if c["value_m3"] is None]
    held_lo = sum((c["range_m3"] or [0, 0])[0] for c in ledger["components"] if c["value_m3"] is None)
    held_hi_known = all(c["range_m3"] is not None for c in ledger["components"] if c["value_m3"] is None)
    held_hi = sum((c["range_m3"] or [0, 0])[1] for c in ledger["components"] if c["value_m3"] is None)
    open_shared = [x for x in ledger["shared"] if x["status"] != "NETTED"]
    sh_lo = sum((x["range_m3"] or [0, 0])[0] for x in open_shared)
    sh_hi = sum((x["range_m3"] or [0, 0])[1] for x in open_shared)
    return {"established_m3": _r(value - netted), "netted_m3": _r(netted), "at_least": bound,
            "coef_m3_per_m": _r(coef), "held_components": held, "held_range_m3": [_r(held_lo),
            _r(held_hi) if held_hi_known else None], "open_shared": [(x["a"], x["b"], x["status"]) for x in open_shared],
            "open_shared_range_m3": [_r(sh_lo), _r(sh_hi)]}


def by_group(ledger):
    out = {}
    for c in ledger["components"]:
        g = out.setdefault(c["group"], {"value_m3": 0.0, "held": [], "statuses": set()})
        if c["value_m3"] is not None:
            g["value_m3"] += c["value_m3"]
        else:
            g["held"].append(c["id"])
        g["statuses"].add(c["status"])
    for x in ledger["shared"]:
        if x["status"] == "NETTED":
            ga = next(c["group"] for c in ledger["components"] if c["id"] == x["a"])
            out[ga]["value_m3"] -= x["value_m3"]
    for g in out.values():
        g["value_m3"] = _r(g["value_m3"])
        g["statuses"] = sorted(g["statuses"])
    return out


def backfill(excavated_m3, displacement_m3):
    """Backfill = excavated - displacement, only when both are values; HELD (None) otherwise, never 0."""
    if excavated_m3 is None or displacement_m3 is None:
        return None, HELD
    if displacement_m3 > excavated_m3 + 1e-9:
        raise Refused("DISPLACEMENT_EXCEEDS_EXCAVATION", f"{displacement_m3} > {excavated_m3}")
    return _r(excavated_m3 - displacement_m3), "CALCULATED"


def disposal(excavated_m3, backfill_m3, bulking=None, bulking_source=None):
    """Disposal = excavated x bulking - backfill re-used; a bulking factor without an answered rule is refused."""
    if bulking is not None and not bulking_source:
        raise Refused("DEFAULT_BULKING_REFUSED", f"factor {bulking} has no answered rule")
    if excavated_m3 is None or backfill_m3 is None or bulking is None:
        return None, HELD
    return _r(excavated_m3 * bulking - backfill_m3), "CALCULATED"
