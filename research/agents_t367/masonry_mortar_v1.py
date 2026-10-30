"""MASONRY_JOINT_MORTAR_V1 (T-367, B9-04): installed bed + perpend joint mortar of MORTARED block walls, wall by wall,
bound to the candidate's MAS.BLOCK line ids; the white AAC thin-bed adhesive kept apart and HELD; cement / sand only
from a mix source that names MASONRY LAYING mortar.

A research piece: NOT wired into any method version (released default ARCH_TAKEOFF_V2.9 + route G and the candidate
ARCH_TAKEOFF_V3.0.26 are unchanged). Standard library only. Every villa; the development-villa run is alsenan_t367.py.

PHYSICAL ELEMENT (ERS s.2.1). A mortared block wall is units laid in courses: each unit has an actual face w x h and
a bed (b, under every course) and a perpend / head joint (j, after every unit), both filled through the full wall
thickness t for SOLID units (full bedding). One unit + its joints occupy one MODULE (w + j) x (h + b). The installed
joint mortar is a physical volume of the built wall; it is NOT a contract BOQ area (MAS.BLOCK m2 is) and NOT the
procurement quantity (waste, dry factor, bags come after, each from a named source).

Per m2 of wall face, two independent derivations that must agree (refused otherwise):
  joints:   bed = (1 / (h + b)) x 1.0 x b x t      head = (1 / ((w + j)(h + b))) x h x j x t
  identity: t x (1 - w h / ((w + j)(h + b)))       (wall volume minus unit volume)
  black 0.39 x 0.19 + 10 / 10 mm -> 0.07375 t: t 0.15 -> 0.0110625, t 0.20 -> 0.01475 m3 / m2.

SOURCES (no default is invented here; every value enters with its source):
  - unit face 0.39 x 0.19 and 10 mm joints: Q-75 owner decision 2026-10-23 14:15 (40 x 20 module PROVISIONAL, final
    on the supplier's actual dimensions and joint) + owner session 2026-10-29 ("provisional 10 mm bed joint for
    mortared blocks, not AAC thin-bed") -> every mortar figure is ASSUMED — OWNER-APPROVED at best, whatever the
    wall's AREA status (a quantity's status is the weakest of its inputs: ERS s.7, T-333 lesson);
  - the alternative 200 mm-high unit (module 0.40 x 0.21: the owner's T-355 example) is computed BESIDE, never merged:
    which one applies is a supplier data item (Q-75), not chosen here;
  - white AAC: thin-bed adhesive, no joint and no coverage given (Q-60, T-355 / T-362, masonry_area_v1.py:27): HELD by
    name; a 10 mm mortar joint on a white wall is REFUSED (owner 2026-10-29: "not AAC thin-bed");
  - cement / sand: only from a mix whose source names MASONRY / BLOCK LAYING mortar. The finish 1:4 table
    (finish_materials_table.py, Q-45 B: the bed under / behind TILES) and the 1:3 stair bed (Q-53) govern other
    physical layers: a source naming them is REFUSED. The Q-53 C derivation constants (dry factor 1.33, cement 1,440
    kg/m3, 50 kg bag; 'not universal constants') may be passed with that source; mix None -> cement / sand HELD;
  - mortar waste: none approved (owner 2026-10-23: never a hardcoded %) -> procurement volume HELD unless given with
    a source.

Statuses: the five of WORKFLOW_CONTROLS s.5. HELD / UNKNOWN never become 0: a wall with no established area carries a
BLANK mortar cell and is named.
"""
from __future__ import annotations

METHOD = "MASONRY_JOINT_MORTAR_V1"
RULE_ID = "R-T367-1"
VER, DC, AOA, HELD, UNKNOWN = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
STATUSES = (VER, DC, AOA, HELD, UNKNOWN)
_RANK = {s: i for i, s in enumerate(STATUSES)}
_ALIASES = {"ASSUMED - OWNER-APPROVED": AOA}          # the candidate's ASCII spelling of the same status
TOL = 1e-9

Q75 = ("Q-75 owner decision 2026-10-23 14:15 (40 x 20 module PROVISIONAL; actual face 39 x 19 + 1 cm joint per the "
       "owner's 2025 sales-order record) + owner session 2026-10-29 (provisional 10 mm bed joint for mortared blocks, "
       "not AAC thin-bed)")
MODULE_BLACK = {"name": "BLACK 39x19 + 10/10 mm (module 0.40 x 0.20)", "face_m": (0.39, 0.19),
                "bed_m": 0.010, "head_m": 0.010, "status": AOA, "source": Q75}
MODULE_BLACK_ALT = {"name": "BLACK 39x20 + 10/10 mm (module 0.40 x 0.21), beside only", "face_m": (0.39, 0.20),
                    "bed_m": 0.010, "head_m": 0.010, "status": AOA,
                    "source": "owner example in the T-355 row (200 mm block -> 210 mm module); applies only if the "
                              "supplier's unit is 200 mm high (supplier data item, Q-75); computed beside, never merged"}
MORTARED = ("BLACK",)                  # conventional cement-block walls laid in mortar
THIN_BED = ("WHITE",)                  # AAC laid with thin-bed adhesive
ADHESIVE_HELD = ("white AAC thin-bed adhesive: no joint, no coverage and no product given (Q-60 A pallet data only; "
                 "T-355 / T-362; masonry_area_v1.py:27): HELD by name, never a mortar volume, never 0")
# words that mark a mix source as belonging to ANOTHER physical layer (finish beds), refused for masonry mortar
FOREIGN_LAYER_WORDS = ("finish_materials_table", "tile", "tiling", "porcelain", "marble", "bartash", "screed",
                       "q-45", "q-53", "stair", "floor bed", "wall mortar behind")
MASONRY_WORDS = ("masonry", "block laying", "blockwork mortar", "laying mortar")


def status(s):
    s = _ALIASES.get(s, s)
    if s not in _RANK:
        raise ValueError(f"status {s!r} is not one of the five section-5 statuses {STATUSES}")
    return s


def weakest(*ss):
    return max((status(s) for s in ss), key=lambda s: _RANK[s])


def _m(v, what, cap):
    v = float(v)
    if not (0 < v <= cap):
        raise ValueError(f"{what} {v} outside 0 .. {cap} m (millimetres or a sign error?)")
    return v


def per_m2(module, t_m):
    """{bed, head, total, identity} m3 per m2 of wall face for full bedding; the two derivations must agree."""
    w, h = (_m(x, "unit face", 1.0) for x in module["face_m"])
    b, j = _m(module["bed_m"], "bed joint", 0.03), _m(module["head_m"], "head joint", 0.03)
    t = _m(t_m, "wall thickness", 0.60)
    mw, mh = w + j, h + b
    bed = (1.0 / mh) * 1.0 * b * t
    head = (1.0 / (mw * mh)) * h * j * t
    ident = t * (1.0 - (w * h) / (mw * mh))
    if abs(bed + head - ident) > 1e-12:
        raise ValueError(f"joint sum {bed + head} != identity {ident}")
    return {"bed": bed, "head": head, "total": bed + head, "identity": ident, "module_m": (mw, mh),
            "units_per_m2": 1.0 / (mw * mh)}


def laid_volume(length_m, height_m, module, t_m):
    """Independent course-by-course lay-out of one rectangular wall (EVIDENCE for the identity, never the quantity):
    a bed under every course (the last course cut to fit), a head joint after every unit except the course end."""
    L, H = _m(length_m, "length", 100.0), _m(height_m, "height", 20.0)
    w, h = module["face_m"]
    b, j = module["bed_m"], module["head_m"]
    t = _m(t_m, "wall thickness", 0.60)
    v, z = 0.0, 0.0
    while z < H - TOL:
        bed = min(b, H - z)
        v += L * bed * t
        z += bed
        ch = min(h, H - z)
        if ch <= TOL:
            break
        x, units = 0.0, 0
        while x < L - TOL:
            u = min(w, L - x)
            x += u
            units += 1
            if x < L - TOL:
                jj = min(j, L - x)
                v += jj * ch * t
                x += jj
        z += ch
    return v


def mix_source_ok(source):
    s = (source or "").lower()
    if not s:
        raise ValueError("a mix needs its evidence source")
    bad = [x for x in FOREIGN_LAYER_WORDS if x in s]
    if bad:
        raise ValueError(f"mix source {source!r} names another physical layer ({', '.join(bad)}): a finish-bed / stair "
                         "mix is never borrowed for masonry laying mortar")
    if not any(x in s for x in MASONRY_WORDS):
        raise ValueError(f"mix source {source!r} does not name masonry / block laying mortar")
    return True


def cement_sand(wet_m3, mix=None, waste=None, derivation=None):
    """Q-53 C-style derivation from a NAMED masonry mix; anything missing -> HELD with its reason (never a default).
    mix = (c, s, source); waste = (fraction, source); derivation = {dry_factor, cement_kg_m3, bag_kg, source}."""
    out = {"ordered_m3": None, "dry_m3": None, "cement_kg": None, "cement_bags": None, "sand_m3": None, "why": []}
    if wet_m3 is None:
        out["why"].append("wet mortar HELD")
        return out
    if waste is None:
        out["why"].append("mortar waste: no approved source (owner 2026-10-23: never a hardcoded %)")
    else:
        f, src = waste
        if not src:
            raise ValueError("a waste fraction needs its evidence source")
        if not (0 <= float(f) <= 0.5):
            raise ValueError(f"waste {f} must be a fraction 0 .. 0.5 (5 % = 0.05)")
        out["ordered_m3"] = wet_m3 * (1 + float(f))
    if mix is None:
        out["why"].append("masonry laying-mortar mix: printed on no sheet, no owner answer names it")
        return out
    c, s, src = mix
    mix_source_ok(src)
    if not (float(c) > 0 and float(s) > 0):
        raise ValueError(f"mix {c}:{s} must be positive parts")
    if derivation is None or not derivation.get("source"):
        out["why"].append("dry factor / cement density / bag mass not given with a source")
        return out
    base = out["ordered_m3"]
    if base is None:
        return out
    dry = base * float(derivation["dry_factor"])
    ck = dry * float(c) / (float(c) + float(s)) * float(derivation["cement_kg_m3"])
    out.update(dry_m3=dry, cement_kg=ck, cement_bags=ck / float(derivation["bag_kg"]),
               sand_m3=dry * float(s) / (float(c) + float(s)))
    return out


def wall_row(w, t_m, module=MODULE_BLACK, joint_m=None):
    """One wall (or established piece) of a MAS.BLOCK line -> its mortar row.
    w = {wall_id, block_type, area_m2 (None = HELD), area_status, kind}; joint_m only to try a joint on a white wall
    (refused)."""
    bt = w.get("block_type")
    row = {"wall_id": w["wall_id"], "block_type": bt or "UNKNOWN", "t_m": t_m, "area_m2": w.get("area_m2"),
           "area_status": w.get("area_status"), "kind": w.get("kind"), "mortar_per_m2": None, "bed_m3": None,
           "head_m3": None, "mortar_m3": None, "mortar_status": HELD, "alt_mortar_m3": None, "adhesive": None,
           "why": ""}
    if bt in THIN_BED:
        if joint_m is not None:
            raise ValueError(f"{w['wall_id']}: a {joint_m} m mortar joint on a white AAC wall is refused (thin-bed "
                             "adhesive; owner 2026-10-29)")
        row.update(adhesive="HELD", why=ADHESIVE_HELD)
        return row
    if bt not in MORTARED:
        row.update(mortar_status=UNKNOWN, why="block type not established: mortared or thin-bed unknown")
        return row
    a, ast = w.get("area_m2"), status(w.get("area_status") or HELD)
    if a is None or ast in (HELD, UNKNOWN):
        if a is not None:
            raise ValueError(f"{w['wall_id']}: a HELD wall carries a figure ({a})")
        row.update(why="wall area HELD in the candidate: mortar blank by name, never 0")
        return row
    a = float(a)
    if a <= 0:
        raise ValueError(f"{w['wall_id']}: area {a} <= 0 on an established wall (a held wall is None, never 0)")
    p = per_m2(module, t_m)
    alt = per_m2(MODULE_BLACK_ALT, t_m)
    row.update(mortar_per_m2=p["total"], bed_m3=a * p["bed"], head_m3=a * p["head"], mortar_m3=a * p["total"],
               mortar_status=weakest(ast, module["status"]), alt_mortar_m3=a * alt["total"],
               why=f"area {ast} x joint geometry ({module['name']}; {module['source'][:60]}...)")
    return row


def line_rows(line):
    """line = {line_id, floor, t_m, walls[...]} -> rows; a wall named twice in one line is refused."""
    seen, out = set(), []
    for w in line["walls"]:
        if w["wall_id"] in seen:
            raise ValueError(f"{line['line_id']}: wall {w['wall_id']} twice")
        seen.add(w["wall_id"])
        r = wall_row(w, line["t_m"])
        r["line_id"] = line["line_id"]
        r["part_line_id"] = w.get("part_line_id")
        r["floor"] = line.get("floor")
        out.append(r)
    return out


def close(rows, black_area_expected, tol=0.0005):
    """sum of established BLACK areas must equal the candidate's black share; every wall once across lines."""
    ids = [r["wall_id"] for r in rows]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        raise ValueError(f"wall(s) in two lines: {dup}")
    s = sum(r["area_m2"] for r in rows if r["block_type"] == "BLACK" and r["mortar_m3"] is not None)
    if abs(s - black_area_expected) > tol:
        raise ValueError(f"black established area {s:.4f} != expected {black_area_expected:.4f}")
    return s


def policy_record():
    return {"method": METHOD, "rule_id": RULE_ID, "module": MODULE_BLACK, "module_beside": MODULE_BLACK_ALT,
            "white": ADHESIVE_HELD, "status_rule": "mortar status = weakest(area status, ASSUMED — OWNER-APPROVED)",
            "cement_sand": "only from a mix whose source names masonry laying mortar; finish / stair beds refused",
            "release": "NOT RELEASED; research only"}
