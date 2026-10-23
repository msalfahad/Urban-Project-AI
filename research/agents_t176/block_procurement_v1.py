"""BLOCK_PROCUREMENT_V1 (T-176): block units, cutting / breakage allowance, laying mortar, cement and sand as a
PROCUREMENT output, kept apart from the NET installed blockwork m2 (ENGINEERING_REASONING_STANDARD.md s.3).

A research piece: NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged). Standard
library only. Every villa; the Alsenan run is alsenan_t176.py.

Physical element: a block wall laid in courses; each unit has an ACTUAL face (w x h) and the joints (bed b, head j) fill
the rest of the wall face. One unit + its joint occupies one MODULE (w + j) x (h + b).

Rules and sources (docs/agents/OWNER_QUESTIONS*.md):
  - Net installed m2 comes from MASONRY_AREA_V1 r2 (T-108 r2, MERGED 01eeafd0): never re-derived here, never the T-143
    hand gross (it carries the T-stem double count). Openings (Q-73) are already deducted there and not reopened.
  - Black (cement, solid) units: Q-75 owner decision 2026-10-23 14:15: the 40 x 20 module (12.5 / m2) is a PROVISIONAL
    owner rule for standard 40 x 20 face modules (ASSUMED — OWNER-APPROVED, provisional); final only on the supplier's
    actual dimensions and joint thickness. Actual face 0.39 x 0.19 + 10 mm joints = the 0.40 x 0.20 module (owner's
    stored takeoff notes cited in Q-75).
  - White (AAC) units: Q-60 supplier pallet data: face 0.625 x 0.25 (6.4 / m2) and 0.60 x 0.20 (8.333 / m2); laid with
    a thin-bed adhesive whose joint is NOT given: the units are computed at joint 0 (the joint-free upper bound) unless a
    joint is supplied, and the bound is labelled.
  - Waste: never hardcoded (owner 2026-10-23: "Do not hardcode 5% waste"). Cutting and breakage are separate named
    parameters, each with its evidence source; a parameter left None makes the procurement count HELD (the installed
    count is still reported). A geometric course-grid count (whole units, no offcut reuse) is offered as EVIDENCE for
    the cutting parameter, never as the procurement quantity.
  - Mortar volume from the ACTUAL joint geometry: per m2 of wall = t x (1 - face area / module area) for full (solid)
    bedding, which equals the bed + head joint sum (courses x 1 m x b x t + units x h x j x t). Face-shell bedding
    (hollow units) needs the shell width, else HELD. A wall's edge courses shift at most one joint strip per edge:
    the bound (L + H) x joint x t is reported as a named tolerance, never added.
  - Dry volume factor, cement density, bag mass and the MIX are named parameters. The Q-53 C owner method (dry 1.33,
    cement 1440 kg/m3, 50 kg bag; "not universal constants") is the derivation; the block LAYING mortar mix is printed
    on no Alsenan sheet and given in no owner answer (Q-45 B's 1:4 is the mortar behind wall tiles, another element):
    mix None -> cement and sand HELD, never borrowed.
  - Mortar stays below VERIFIED until the Checker re-derives it from the joint geometry (owner 2026-10-23).

Statuses: the five of WORKFLOW_CONTROLS s.5; a result is the weakest of its inputs. HELD / UNKNOWN never become 0.
Guards (ValueError): a status outside the five; millimetre inputs (a face or module dimension > 2 m, a joint > 0.05 m,
a thickness > 0.60 m); a face larger than its module; a negative or > 0.50 waste fraction; an unknown bedding.
"""
from __future__ import annotations

import math

METHOD = "BLOCK_PROCUREMENT_V1"
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
VER, DC, AOA, HELD, UNKNOWN = STATUSES
_RANK = {s: i for i, s in enumerate(STATUSES)}
BEDDINGS = ("FULL", "FACE_SHELL")
TOL = 1e-9

# product records: (actual face w, h), joints (bed, head) or None, thicknesses made, bedding, status, source
PRODUCTS = {
    "BLACK_40x20": {"face_m": (0.39, 0.19), "joint_m": (0.010, 0.010), "t_m": (0.15, 0.20), "bedding": "FULL",
                    "kind": "BLACK", "status": AOA,
                    "source": "Q-75 owner decision 2026-10-23 14:15: 40 x 20 module PROVISIONAL owner rule (actual face "
                              "39 x 19 + 10 mm joints per the owner's stored 2025 sales-order notes); final on the "
                              "supplier's actual dimensions and joint"},
    "WHITE_62.5x25": {"face_m": (0.625, 0.25), "joint_m": None, "t_m": (0.10, 0.15, 0.20, 0.25, 0.30),
                      "bedding": "THIN_BED", "kind": "WHITE", "status": AOA,
                      "pallet": {0.10: 128, 0.15: 88, 0.20: 64, 0.25: 56, 0.30: 40},
                      "source": "Q-60 A supplier pallet list (owner 2026-10-20 10:45): pallet volumes give a 0.625 x 0.25 "
                                "face; thin-bed adhesive joint not given (joint-free upper bound)"},
    "WHITE_60x20": {"face_m": (0.60, 0.20), "joint_m": None, "t_m": (0.15, 0.20), "bedding": "THIN_BED",
                    "kind": "WHITE", "status": AOA, "pallet": {0.15: 100, 0.20: 80},
                    "source": "Q-60 A supplier pallet list (owner 2026-10-20 10:45): 15-20-60 / 20-20-60; thin-bed "
                              "adhesive joint not given (joint-free upper bound)"},
}

# procurement parameters: every value carries its source; None = not established -> the dependent line is HELD
DEFAULT_PARAMS = {
    "cutting_waste": {"value": None, "source": "no approved source (owner 2026-10-23: configurable, evidence-based)"},
    "breakage": {"value": None, "source": "no approved source"},
    "mortar_waste": {"value": None, "source": "no approved source for block laying mortar"},
    "dry_factor": {"value": 1.33, "source": "Q-53 C owner method 2026-10-20 12:02 (dry factor 1.33; not universal)"},
    "cement_kg_m3": {"value": 1440.0, "source": "Q-53 C owner method (cement 1440 kg/m3)"},
    "bag_kg": {"value": 50.0, "source": "Q-45 B / Q-53 C (50 kg bag)"},
    "mix": {"value": None, "source": "block laying mortar mix: printed on no Alsenan sheet (T-091 census), no owner "
                                     "answer; Q-45 B 1:4 is the mortar behind wall tiles (another element)"},
    "white_joint_m": {"value": None, "source": "thin-bed joint not given (Q-60: adhesive coverage HELD)"},
    "shell_width_m": {"value": None, "source": "face-shell width not given (hollow units only)"},
}


def check_status(s):
    if s not in _RANK:
        raise ValueError(f"status {s!r} is not one of the five section-5 statuses {STATUSES}")
    return s


def weakest(*statuses):
    for s in statuses:
        check_status(s)
    return max(statuses, key=lambda s: _RANK[s])


def _dim(v, what, cap):
    v = float(v)
    if v < 0 or v > cap:
        raise ValueError(f"{what} {v} outside 0 .. {cap} m (millimetres or a sign error?)")
    return v


def _frac(v, what):
    if v is None:
        return None
    v = float(v)
    if v < 0 or v > 0.50:
        raise ValueError(f"{what} {v} must be a fraction 0 .. 0.50 (5 % = 0.05, not 5)")
    return v


def params(**over):
    """DEFAULT_PARAMS with overrides given as name=(value, source); a value without a source is refused."""
    p = {k: dict(v) for k, v in DEFAULT_PARAMS.items()}
    for k, vs in over.items():
        if k not in p:
            raise ValueError(f"unknown parameter {k!r}")
        if not (isinstance(vs, tuple) and len(vs) == 2 and vs[1]):
            raise ValueError(f"parameter {k!r} needs (value, evidence source)")
        p[k] = {"value": vs[0], "source": vs[1]}
    _frac(p["cutting_waste"]["value"], "cutting_waste")
    _frac(p["breakage"]["value"], "breakage")
    _frac(p["mortar_waste"]["value"], "mortar_waste")
    return p


def module(product, joint_m=None):
    """(face w, face h, module w, module h, joint source) of a product; a thin-bed product without a joint -> joint 0."""
    pr = PRODUCTS[product]
    fw, fh = (_dim(x, "face", 2.0) for x in pr["face_m"])
    j = pr["joint_m"]
    if j is None:
        jj = 0.0 if joint_m is None else _dim(joint_m, "joint", 0.05)
        bed = head = jj
        jsrc = "JOINT_FREE_UPPER_BOUND" if joint_m is None else "GIVEN"
    else:
        bed, head = (_dim(x, "joint", 0.05) for x in j)
        jsrc = "PRODUCT"
    return fw, fh, fw + head, fh + bed, bed, head, jsrc


def units_per_m2(product, joint_m=None):
    fw, fh, mw, mh, *_ = module(product, joint_m)
    return 1.0 / (mw * mh)


def installed_units(net_m2, product, t_m, net_status, joint_m=None):
    """Installed units = net m2 / module area (no waste). Status = weakest(net, product rule)."""
    check_status(net_status)
    pr = PRODUCTS[product]
    t = _dim(t_m, "thickness", 0.60)
    if not any(abs(t - x) < TOL for x in pr["t_m"]):
        return {"units": None, "status": HELD, "why": f"{product} not made in t {t} m"}
    st = weakest(net_status, pr["status"])
    if net_m2 is None or st in (HELD, UNKNOWN):
        return {"units": None, "status": HELD if st != UNKNOWN else UNKNOWN, "why": "net area HELD"}
    per = units_per_m2(product, joint_m)
    jsrc = module(product, joint_m)[6]
    return {"units": net_m2 * per, "per_m2": per, "status": st, "joint": jsrc}


def procurement_units(installed, p):
    """Ordered units = ceil(installed x (1 + cutting + breakage)); HELD while any allowance is not established."""
    if installed["units"] is None:
        return {"units": None, "status": installed["status"], "why": "installed HELD"}
    cw, br = p["cutting_waste"]["value"], p["breakage"]["value"]
    if cw is None or br is None:
        miss = [n for n, v in (("cutting_waste", cw), ("breakage", br)) if v is None]
        return {"units": None, "status": HELD, "why": "allowance not established: " + ", ".join(miss)}
    return {"units": math.ceil(installed["units"] * (1.0 + cw + br) - TOL), "status": installed["status"],
            "factor": 1.0 + cw + br,
            "sources": {"cutting_waste": p["cutting_waste"]["source"], "breakage": p["breakage"]["source"]}}


def pallets(units, product, t_m):
    """Whole pallets for an ordered white-unit count (Q-60 pallet sizes); spare units reported."""
    if units is None:
        return {"pallets": None, "spare": None}
    per = PRODUCTS[product].get("pallet", {})
    n = next((v for k, v in per.items() if abs(k - t_m) < TOL), None)
    if n is None:
        return {"pallets": None, "spare": None, "why": "no pallet size for this product / thickness"}
    pl = math.ceil(units / n - TOL)
    return {"pallets": pl, "spare": pl * n - units, "per_pallet": n}


def mortar_per_m2(product, t_m, bedding=None, shell_width_m=None):
    """Wet laying-mortar m3 per m2 of wall from the joint geometry; also the bed + head split (same total for FULL)."""
    pr = PRODUCTS[product]
    if pr["bedding"] == "THIN_BED":
        return {"m3_per_m2": None, "status": HELD, "why": "thin-bed adhesive: coverage per bag, not a joint volume (Q-60 HELD)"}
    bedding = bedding or pr["bedding"]
    if bedding not in BEDDINGS:
        raise ValueError(f"bedding {bedding!r} not in {BEDDINGS}")
    t = _dim(t_m, "thickness", 0.60)
    fw, fh, mw, mh, bed, head, _ = module(product)
    courses = 1.0 / mh                      # courses per metre of height
    units = 1.0 / (mw * mh)
    if bedding == "FULL":
        width = t
    else:
        if shell_width_m is None:
            return {"m3_per_m2": None, "status": HELD, "why": "face-shell bedding: shell width not given"}
        width = min(t, 2 * _dim(shell_width_m, "shell width", 0.30))
    bed_v = courses * 1.0 * bed * width
    head_v = units * fh * head * width
    out = {"bed_m3": bed_v, "head_m3": head_v, "m3_per_m2": bed_v + head_v, "status": pr["status"], "bedding": bedding}
    if bedding == "FULL":
        out["identity_m3"] = t * (1.0 - (fw * fh) / (mw * mh))   # wall volume - unit volume, per m2
    return out


def edge_tolerance_m3(length_m, height_m, product, t_m):
    """Named tolerance (not added): edge courses shift by at most one joint strip per wall edge."""
    fw, fh, mw, mh, bed, head, _ = module(product)
    return (length_m * bed + height_m * head) * _dim(t_m, "thickness", 0.60)


def mortar(net_m2, net_status, product, t_m, p, bedding=None):
    """Wet mortar, mortar ordered (waste), dry volume, cement kg / bags, sand m3: each its own value and status."""
    check_status(net_status)
    per = mortar_per_m2(product, t_m, bedding, p["shell_width_m"]["value"])
    out = {"wet_m3": None, "wet_status": HELD, "ordered_m3": None, "ordered_status": HELD, "dry_m3": None,
           "cement_kg": None, "cement_bags": None, "sand_m3": None, "cement_sand_status": HELD, "why": []}
    if per["m3_per_m2"] is None:
        out["why"].append(per["why"])
        return out
    st = weakest(net_status, per["status"])
    if net_m2 is None or st in (HELD, UNKNOWN):
        out["why"].append("net area HELD")
        return out
    wet = net_m2 * per["m3_per_m2"]
    out.update(wet_m3=wet, wet_status=st)
    mw = p["mortar_waste"]["value"]
    if mw is None:
        out["why"].append("mortar waste not established")
        base = None
    else:
        base = wet * (1.0 + mw)
        out.update(ordered_m3=base, ordered_status=st)
    mix = p["mix"]["value"]
    if mix is None:
        out["why"].append("mix not established: " + p["mix"]["source"])
        return out
    c, s = (float(x) for x in mix)
    if c <= 0 or s <= 0:
        raise ValueError(f"mix {mix} must be positive parts cement : sand")
    if base is None:
        return out
    dry = base * float(p["dry_factor"]["value"])
    ck = dry * c / (c + s) * float(p["cement_kg_m3"]["value"])
    out.update(dry_m3=dry, cement_kg=ck, cement_bags=ck / float(p["bag_kg"]["value"]), sand_m3=dry * s / (c + s),
               cement_sand_status=st)
    return out


def grid_units(length_m, height_m, product, openings=(), joint_m=None):
    """Course-grid count: every partial unit at a wall end or the top course counted whole (no offcut reuse), less the
    whole modules inside each opening (w, h). EVIDENCE for the cutting parameter (an upper bound), not an order."""
    fw, fh, mw, mh, *_ = module(product, joint_m)
    L = _dim(length_m, "length", 60.0)
    H = _dim(height_m, "height", 12.0)
    n = math.ceil(L / mw - TOL) * math.ceil(H / mh - TOL)
    for w, h in openings:
        n -= math.floor(_dim(w, "opening width", 20.0) / mw + TOL) * math.floor(_dim(h, "opening height", 12.0) / mh + TOL)
    return n


def policy_record():
    return {"method": METHOD, "statuses": list(STATUSES), "wired": False, "products": sorted(PRODUCTS),
            "parameters": sorted(DEFAULT_PARAMS),
            "scope": "every villa: procurement (units, allowances, mortar, cement, sand) after the NET installed m2"}
