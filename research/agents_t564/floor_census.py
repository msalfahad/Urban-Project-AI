"""R-T564-1 FLOOR-FINISH COMPLETENESS CENSUS on a candidate LINE_INDEX (any villa; no drawing read, no quantity typed).

Physical element: the finished floor of every ENCLOSED SPACE (register ruling ENCLOSED SPACE FLOOR, Lead 2026-11-06
12:18): a space that is finished overhead (ceiling) or along its walls (skirting) has a finished floor, and that floor
is one floor-finish line (B3 tile / FINISH_HELD, or the B7 stair marble that owns it), carried once, on the bed its
own wet / dry scope requires.

The census finds defects BY RULE from the line records only. It never takes a list of room ids, never names the hits
it expects and never gives a missing floor a 0:

  C1 MISSING_FLOOR      a space key with a live (RELEASED / HELD) ceiling or skirting line and no live floor-finish line
  C2 WET_BED_DRY_FINISH a live dry finish (FIN.FLOOR.PORCELAIN) whose own bed pair is FIN.FLOOR.BED.WET (or the reverse:
                        FIN.FLOOR.WET_TILE on a BED.DRY pair); the finish class is wrong, the area is right
  C3 WP_FLOOR_COVER     per storey, every FIN.WP.FLOOR m2 is covered by wet finishes (WET_TILE) of its space plus the
                        wet finishes of the same storey that no WP line of their own covers; residual named
  C4 BED_PAIR           every RELEASED floor-finish line has a bed m2 line of the same area and a HELD m3 line

Space keys (generic for the engine's id scheme): '<storey>-R<6 hex>' anywhere in an element id (also inside scope ids
such as 'GF-PANTRY-R<hex>-PART'), and the named stair-room sub-spaces '<storey>-ST-<NAME>' (T-443). Ceiling / skirting
lines with no space key must match a declared OUT_OF_SCOPE prefix (exterior slab soffits, B7 stair skirting), else the
census refuses (UNSCOPED): a new villa cannot drop a line silently.

Each hit is classed afterwards (classify): ENGINE_WRONG (expected after with its value, or HELD by name), ENGINE_RIGHT
(only with a cited owner line that exists and is a floor-owning family on the same storey), or HELD (no area known).
"""

from __future__ import annotations

import re
from decimal import Decimal

STOREY = r"(?:B1|GF|1F|2F|3F|RF)"
R_KEY = re.compile(rf"\b({STOREY})-(?:[A-Z]+-)*R([0-9A-F]{{6}})\b")
ST_KEY = re.compile(rf"\b({STOREY}-ST-[A-Z]+[0-9]*)\b")

LIVE = ("RELEASED", "HELD")
FLOOR_FINISH = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD")
FLOOR_OWNER_B7 = ("FIN.MARBLE.LANDING", "FIN.MARBLE.TREAD")         # stair marble owns the floor it covers (B7)
OVERHEAD = ("FIN.CEILING", "FIN.PAINT.CEILING")
WALL_BASE = ("FIN.SKIRTING",)
BED = {"FIN.FLOOR.BED.DRY": "DRY", "FIN.FLOOR.BED.WET": "WET"}
FINISH_SCOPE = {"FIN.FLOOR.PORCELAIN": "DRY", "FIN.FLOOR.WET_TILE": "WET"}
OUT_OF_SCOPE = {
    "SOFFIT:": "exterior slab soffit (no enclosed space below; T-435 reverse join: no floor finish by nature)",
    "STAIR-SKIRT:": "B7 stair skirting (its floor is the B7 landing / tread marble, owned by the stair lines)",
}
TOL = Decimal("0.001")          # m2: the candidate prints areas to 1e-6; a cover residual under 1e-3 is rounding


class CensusError(ValueError):
    pass


def _d(x):
    return None if x is None else Decimal(str(x))


def keys(element_id):
    """the space keys an element id carries: R keys as '<storey>-R<hex>', stair sub-space tokens as printed."""
    out = {f"{m.group(1)}-R{m.group(2)}" for m in R_KEY.finditer(element_id)}
    out |= {m.group(1) for m in ST_KEY.finditer(element_id)}
    return out


def storey(key_or_element):
    m = re.match(STOREY, key_or_element)
    if m:
        return m.group(0)
    m = re.search(rf"\b({STOREY})\b", key_or_element)
    return m.group(1) if m else None


def _check_lines(lines):
    if isinstance(lines, dict):
        lines = list(lines.values())
    for l in lines:
        if not isinstance(l, dict) or "line_id" not in l or "item_code" not in l or "element_id" not in l:
            raise CensusError("KEYED_INPUT: the census reads line records (line_id, item_code, element_id, class, "
                              "unit, measured_net), never a list of room ids")
    return lines


def _live(l):
    return l["class"] in LIVE


def _m2(l):
    return l.get("unit") == "m2"


def census(lines, **kw):
    """C1 .. C4 on the line records. Any keyword (an id list, an expected hit list) is refused: hits come from the rule."""
    if kw:
        raise CensusError(f"KEYED_INPUT: census takes line records only; refused {sorted(kw)} (hits are found by the "
                          "rule, never by room id)")
    lines = _check_lines(lines)
    by_key, unscoped, scoped_out = {}, [], {}
    for l in lines:
        ks = keys(l["element_id"])
        for k in ks:
            by_key.setdefault(k, []).append(l)
        if not ks and l["item_code"] in OVERHEAD + WALL_BASE:
            pre = next((p for p in OUT_OF_SCOPE if l["element_id"].startswith(p)), None)
            if pre is None:
                unscoped.append(l["line_id"])
            else:
                scoped_out.setdefault(pre, []).append(l["line_id"])
    if unscoped:
        raise CensusError(f"UNSCOPED: ceiling / skirting lines with no space key and no declared scope: {unscoped[:5]}")
    return {"rule": "R-T564-1",
            "spaces": len(by_key),
            "out_of_scope": {p: {"reason": OUT_OF_SCOPE[p], "lines": sorted(v)} for p, v in sorted(scoped_out.items())},
            "C1_missing_floor": _c1(by_key),
            "C2_wet_bed_dry_finish": _c2(lines),
            "C3_wp_floor_cover": _c3(lines),
            "C4_bed_pair": _c4(lines)}


def _c1(by_key):
    hits = []
    for k in sorted(by_key):
        ls = by_key[k]
        top = [l for l in ls if l["item_code"] in OVERHEAD + WALL_BASE and _live(l)]
        flo = [l for l in ls if l["item_code"] in FLOOR_FINISH + FLOOR_OWNER_B7 and _live(l)]
        if top and not flo:
            space = [l for l in ls if l["item_code"] == "ARCH.SPACE" and l["class"] == "RELEASED" and _m2(l)]
            wet = [l for l in ls if _live(l) and (l["item_code"] == "FIN.WP.FLOOR" or l["item_code"] ==
                                                  "FIN.FLOOR.BED.WET")]
            hits.append({"key": k, "storey": storey(k),
                         "evidence_lines": sorted((l["line_id"], l["item_code"], l["class"]) for l in top),
                         "space_lines": sorted((l["line_id"], float(_d(l["measured_net"]))) for l in space),
                         "ceiling_m2": sorted(float(_d(l["measured_net"])) for l in top
                                              if l["item_code"] == "FIN.CEILING" and l["class"] == "RELEASED"),
                         "wet_scope": bool(wet)})
    return hits


def _pairs(lines):
    """finish line -> its bed lines (element id + ':bed', the engine's own pairing)."""
    bed = {}
    for l in lines:
        if l["item_code"] in BED:
            bed.setdefault(l["element_id"], []).append(l)
    return {l["line_id"]: bed.get(l["element_id"] + ":bed", []) for l in lines if l["item_code"] in FLOOR_FINISH}


def _c2(lines):
    pairs, hits = _pairs(lines), []
    for l in sorted(lines, key=lambda x: x["line_id"]):
        if l["item_code"] not in FINISH_SCOPE or not _live(l):
            continue
        bs = [b for b in pairs[l["line_id"]] if _live(b)]
        scopes = {BED[b["item_code"]] for b in bs}
        if len(scopes) > 1:
            raise CensusError(f"{l['line_id']}: its bed pair carries both a DRY and a WET bed")
        if scopes and scopes != {FINISH_SCOPE[l["item_code"]]}:
            bed_scope = scopes.pop()
            hits.append({"line_id": l["line_id"], "element_id": l["element_id"], "item_code": l["item_code"],
                         "class": l["class"], "m2": None if l["measured_net"] is None else float(_d(l["measured_net"])),
                         "finish_scope": FINISH_SCOPE[l["item_code"]], "bed_scope": bed_scope,
                         "bed_lines": sorted(b["line_id"] for b in bs),
                         "expected_item_code": "FIN.FLOOR.WET_TILE" if bed_scope == "WET" else "FIN.FLOOR.PORCELAIN"})
    return hits


def _c3(lines):
    """per storey: WP floor m2 per space vs the wet finish m2 of that space; shortfalls covered by the storey's wet
    finishes that sit under no WP line of their own. Residual per storey named (never absorbed)."""
    wp, wet = {}, {}
    for l in lines:
        if l["class"] != "RELEASED" or not _m2(l):
            continue
        if l["item_code"] == "FIN.WP.FLOOR":
            for k in keys(l["element_id"]) or {"(no key)"}:
                wp.setdefault(k, []).append(l)
        if l["item_code"] == "FIN.FLOOR.WET_TILE":
            ks = sorted(k for k in keys(l["element_id"]) if "-R" in k)
            wet.setdefault(ks[0] if ks else "(no key)|" + (storey(l["element_id"]) or "?"), []).append(l)
    out = {}
    storeys = sorted({storey(k) for k in wp if storey(k)} | {storey(k.split("|")[-1]) for k in wet if storey(k.split("|")[-1])})
    for st in storeys:
        rows, short, free = [], Decimal(0), []
        for k in sorted(k for k in wp if storey(k) == st):
            a = sum((_d(l["measured_net"]) for l in wp[k]), Decimal(0))
            f = sum((_d(l["measured_net"]) for l in wet.get(k, [])), Decimal(0))
            rows.append({"key": k, "wp_m2": float(a), "wet_finish_m2": float(f), "shortfall_m2": float(a - f),
                         "wp_lines": sorted(l["line_id"] for l in wp[k])})
            short += max(a - f, Decimal(0))
        for k, ls in sorted(wet.items()):
            kst = storey(k.split("|")[-1]) if k.startswith("(no key)") else storey(k)
            if kst == st and k not in wp:
                free += [(l["line_id"], l["element_id"], _d(l["measured_net"])) for l in ls]
        fsum = sum((x[2] for x in free), Decimal(0))
        out[st] = {"spaces": rows, "shortfall_m2": float(short),
                   "uncovered_wet_finish": [[a, b, float(c)] for a, b, c in free], "uncovered_wet_m2": float(fsum),
                   "residual_m2": float(short - fsum),
                   "state": "COVERED" if abs(short - fsum) <= TOL else "RESIDUAL"}
    return out


def _c4(lines):
    pairs, misses = _pairs(lines), []
    for l in sorted(lines, key=lambda x: x["line_id"]):
        if l["item_code"] not in FLOOR_FINISH or l["class"] != "RELEASED":
            continue
        bs = pairs[l["line_id"]]
        m2 = [b for b in bs if b["unit"] == "m2" and b["class"] == "RELEASED"]
        m3 = [b for b in bs if b["unit"] == "m3" and b["class"] == "HELD"]
        ok = len(m2) == 1 and _d(m2[0]["measured_net"]) == _d(l["measured_net"]) and len(m3) == 1
        if not ok:
            misses.append({"line_id": l["line_id"], "element_id": l["element_id"],
                           "bed_m2": [b["line_id"] for b in m2], "bed_m3": [b["line_id"] for b in m3]})
    return misses


def bed_thickness(lines):
    """the bed depth range the candidate itself applies per scope (held m3 / released m2 of each pair): one range per
    scope or refused. Read, never typed."""
    pairs, seen = _pairs(lines), {}
    for l in lines:
        if l["item_code"] not in FLOOR_FINISH or l["class"] != "RELEASED":
            continue
        bs = pairs[l["line_id"]]
        m2 = [b for b in bs if b["unit"] == "m2" and b["class"] == "RELEASED"]
        m3 = [b for b in bs if b["unit"] == "m3" and b["class"] == "HELD"]
        if len(m2) != 1 or len(m3) != 1:
            continue
        a = _d(m2[0]["measured_net"])
        lo, hi = _d(m3[0]["held_low"]) / a, _d(m3[0]["held_high"]) / a
        seen.setdefault(BED[m2[0]["item_code"]], set()).add((lo.quantize(Decimal("0.0001")),
                                                             hi.quantize(Decimal("0.0001"))))
    out = {}
    for s, v in seen.items():
        if len(v) != 1:
            raise CensusError(f"bed depth for {s} is not one range in the candidate: {sorted(v)[:4]}")
        lo, hi = v.pop()
        out[s] = [lo.normalize(), hi.normalize()]
    return out


def classify(c, lines, owners=()):
    """each C1 hit -> ENGINE_WRONG with an expected after (area from the space's own released ARCH.SPACE line, the
    finish class FINISH_HELD by name, the bed pair at the candidate's own depth) / ENGINE_RIGHT (a cited owner line
    that exists, owns floors and sits on the same storey) / HELD (no released space area). C2 hits are ENGINE_WRONG on
    class only (0 m2). A missing floor is never written as 0."""
    lines = _check_lines(lines)
    by_id = {l["line_id"]: l for l in lines}
    own = {}
    for o in owners:
        ol = by_id.get(o["owner_line"])
        if ol is None or ol["item_code"] not in FLOOR_OWNER_B7 + FLOOR_FINISH:
            raise CensusError(f"OWNER: {o['owner_line']} is not a floor-owning line of the candidate")
        if storey(ol["element_id"]) != storey(o["key"]):
            raise CensusError(f"OWNER: {o['owner_line']} is not on the storey of {o['key']}")
        own[o["key"]] = o
    depth = bed_thickness(lines)
    out = []
    for h in c["C1_missing_floor"]:
        if h["key"] in own:
            o = own[h["key"]]
            out.append(dict(h, verdict="ENGINE_RIGHT", owner_line=o["owner_line"], why=o["source"],
                            expected_after="no new line: the floor is carried by the owner line"))
            continue
        if len(h["space_lines"]) == 1:
            a = Decimal(str(h["space_lines"][0][1]))
            if a <= 0:
                raise CensusError(f"{h['key']}: space area {a} is not positive")
            if h["ceiling_m2"] and any(Decimal(str(x)) != a for x in h["ceiling_m2"]):
                raise CensusError(f"{h['key']}: ceiling {h['ceiling_m2']} is not the space area {a}")
            scope = "WET" if h["wet_scope"] else "DRY"
            lo, hi = depth[scope]
            out.append(dict(h, verdict="ENGINE_WRONG", expected_after={
                "add": [{"item_code": "FIN.FLOOR.FINISH_HELD", "element_id": f"{h['key']}:floor", "class": "RELEASED",
                         "unit": "m2", "value": float(a), "material": "HELD by name (no finish class in the line index "
                                                                         "for this space)"},
                        {"item_code": f"FIN.FLOOR.BED.{scope}", "element_id": f"{h['key']}:floor:bed",
                         "class": "RELEASED", "unit": "m2", "value": float(a)},
                        {"item_code": f"FIN.FLOOR.BED.{scope}", "element_id": f"{h['key']}:floor:bed", "class": "HELD",
                         "unit": "m3", "value": None, "held_low": float(a * lo), "held_high": float(a * hi)}],
                "floor_change_m2": float(a)}))
        else:
            out.append(dict(h, verdict="HELD", expected_after={"add": [{"item_code": "FIN.FLOOR.FINISH_HELD",
                                                                          "element_id": f"{h['key']}:floor",
                                                                          "class": "HELD", "value": None}],
                                                                 "floor_change_m2": None},
                            why="no released space area: the floor is named HELD, never 0"))
    c2 = [dict(h, verdict="ENGINE_WRONG", expected_after={"recode": [h["line_id"], h["item_code"],
                                                                     h["expected_item_code"]], "m2_change": 0.0})
          for h in c["C2_wet_bed_dry_finish"]]
    for r in out:
        check_after(r)
    return {"C1": out, "C2": c2, "bed_depth_m": {k: [float(x) for x in v] for k, v in depth.items()}}


def check_after(row):
    """refuse a missing floor wired as 0 (or a RELEASED add with no value)."""
    ea = row.get("expected_after")
    if not isinstance(ea, dict):
        return
    for a in ea.get("add", []):
        if a.get("value") == 0 or a.get("value") == 0.0:
            raise CensusError(f"ZERO: {row['key']} {a['item_code']} wired as 0 (a missing floor is HELD or valued)")
        if a.get("class") == "RELEASED" and a.get("value") is None:
            raise CensusError(f"ZERO: {row['key']} {a['item_code']} RELEASED with no value")
    if ea.get("floor_change_m2") == 0:
        raise CensusError(f"ZERO: {row['key']} floor change 0 for a missing floor")
