"""T-500: TILE BED MORTAR material table on the candidate floor-bed lines (research, UNWIRED: read by no released
method and by no candidate V3.0.x; no candidate or released quantity changes).

PHYSICAL ELEMENT. The cement-sand bed laid on the structural slab (or on the membrane in a wet room) under a floor tile:
one layer per tiled floor, its own candidate item B3-05 since R-T420-1 (T-420), carried as a MEASURE PAIR of two lines
of one physical item: FIN.FLOOR.BED.<DRY|WET> in m2 (= the bound floor-finish net) and in m3 (owner thickness band,
BOUNDED: low = area x thin end, high = area x thick end; never one chosen thickness). This table turns the m3 line into
the material it consumes: cement (50 kg bags) and loose sand (m3), installed (theoretical) and, separately, the owner's
mortar waste and the procurement figure. The adhesive on top of the bed (T-455) and the tile are other layers.

NOT this table (one producer per material, R-T496-3): the wet-wall LEVELLING RENDER and the spatter dash (plaster
trade, PLASTER_MATERIALS_TABLE_V1 / V2 = T-454 / T-489); a tiled wet wall carries no fixing bed at all (UPC-WETWALL-001,
owner 2026-11-02: spatter dash + levelling render + adhesive and porcelain, no second fixing bed; T-457). Stair beds
(1:3, B7), roof / balcony screeds (Q-41) and outdoor floors (T-495) are owned elsewhere and refused here.

Owner values, READ from engine/source/finish_materials_table_v5.OWNER_VALUES (= the V1 record of Q-45), not retyped:
    bed band     DRY floors 0.03 .. 0.04 m, WET floors (bartash) 0.04 .. 0.06 m          OWNER CONFIRMED (Q-45, 2 Nov)
    mix          1:4 for floors and bartash                                               Q-45 B; Q-78 A (2026-11-02)
    per m3       8.0 bags of 50 kg cement and 1.1 m3 of loose sand per m3 of 1:4 mortar   Q-45 B practice value accepted
                 by the owner (PROVISIONAL), re-used by the owner for Q-78 A ('priced with the Q-45 figures')
    waste        5 % on mortar, its own field, never inside the installed figure          Q-45 B (PROVISIONAL; the
                 2026-10-20 audit line that called it 'not owner-approved' was WITHDRAWN by the owner)
First-principles check of the per-m3 figure (not a source, a sanity bound only): 1 m3 of wet 1:4 mortar needs about 1.25
.. 1.33 m3 of dry loose material; cement 1/5 of it at about 1,440 kg/m3 = 360 .. 383 kg = 7.2 .. 7.7 bags, sand 4/5 =
1.00 .. 1.07 m3. The owner's 8 bags / 1.1 m3 lie at the rich end of that band: plausible, used as given, never adjusted.

Rules of this table (R-T500-1 .. 5; project-independent):
  R-T500-1 BIND THE VOLUME LINE. Materials come from the m3 line of the pair only, from its candidate held range; the
           m2 partner is NOT_APPLICABLE_WITH_EVIDENCE (measure pair, price one basis, R-T420-1). The pair must be one
           m2 + one m3 on one element; a lone or doubled line fails.
  R-T500-2 REPRODUCE BEFORE DERIVING. The m3 range must equal (area x band low, area x band high) of its m2 partner at
           6 decimals; a drifted range fails (BAND_MISMATCH) and yields no figure.
  R-T500-3 RANGES, NOT MID VALUES. Cement = m3 x 8, sand = m3 x 1.1 at each end; waste = 5 % of each end, separate;
           procurement = installed + waste. No mid value, no rounding inside a row; whole bags only at project level.
  R-T500-4 HELD STAYS HELD (R-T499-1). A row with no range (bed thickness HELD, area HELD, mix with no per-m3 figure)
           prints None with its reason, never 0; any subtotal over it is HELD with the known part AT_LEAST.
  R-T500-5 COMPLETENESS BY HOST. Every floor-finish line has its bed pair, or is NOT_APPLICABLE_WITH_EVIDENCE (finish
           line EXCLUDED: no tile laid), or is named MISSING_BED_LINE (HELD, never 0). Every wall-tile line is
           NOT_APPLICABLE (no fixing bed on a wall, UPC-WETWALL-001) and may carry no bed line.

Inputs (sha256-pinned, never edited): research/agents_t487/out/LINE_INDEX_V3_0_51.json (BOQ_LINES c0b6d664) and
research/agents_t487/summary_t487.json, whose identity block proves the candidate of record ARCH_TAKEOFF_V3.0.53
(36863f6c) = V3.0.51 + 60 added STR.CONC.LINTEL lines, 4,876 outside rows identical: the bed and finish lines of V3.0.53
are those of V3.0.51 (checked: none of the 60 added lines is a FIN.* line).

    python3 -I research/agents_t500/t500_tile_bed_mortar.py [OUT_DIR]   # writes TILE_BED_MORTAR_T500.json / .csv
    python3 -I research/agents_t500/t500_tile_bed_mortar.py --check     # exit 1 on any failure
Project-agnostic: no project, layer, room name or count appears in the rules or the functions; the pinned inputs are
the only project data.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table_v5 as V5  # noqa: E402

SCHEMA = "URBAN_T500_TILE_BED_MORTAR_V1"
METHOD_ID = "TILE_BED_MORTAR_TABLE_V1"
GUARD_CLASS = "UNWIRED_PRODUCER"
CANDIDATE = "ARCH_TAKEOFF_V3.0.53"
CANDIDATE_SHA8 = "36863f6c"
BASE = "ARCH_TAKEOFF_V3.0.51"
BASE_LINES_SHA = "c0b6d664aeff58809641e1cb09cfe32834fb7a66a55565fa04cc74fb32da37b1"

INDEX = ROOT / "research/agents_t487/out/LINE_INDEX_V3_0_51.json"
T487 = ROOT / "research/agents_t487/summary_t487.json"
PINS = {INDEX: "a48b8f78c2a582b0c4c1544b24ec2366e6933c0a658f8f758cc92107bdbbcdb8",
        T487: "feb71118a22d1158581e43e752e873a85cd514a4ba2394b35c0157b2ed8f6693"}

RULES = ("R-T500-1@1.0.0 bind the volume line of the measure pair",
         "R-T500-2@1.0.0 reproduce the m3 range from area x owner band before deriving",
         "R-T500-3@1.0.0 cement / sand as ranges, waste separate, whole bags at project level only",
         "R-T500-4@1.0.0 held stays held (R-T499-1 subtotals)",
         "R-T500-5@1.0.0 completeness by host: every floor finish bedded, NOT_APPLICABLE or MISSING; no bed on walls")
SOURCES = {"band": "owner Q-45 (2026-10-19 21:40; OWNER CONFIRMED 2026-11-02, AGENT_BRIEF 'Tile bed')",
           "mix": "owner Q-45 B (floors and bartash 1:4); Q-78 A 2026-11-02 (1:4 priced with the Q-45 figures)",
           "per_m3": "owner Q-45 B practice value accepted (PROVISIONAL): 8 bags of 50 kg + 1.1 m3 loose sand per m3",
           "waste": "owner Q-45 B: 5 % on mortar (PROVISIONAL), separate field",
           "no_wall_bed": "UPC-WETWALL-001 owner 2026-11-02 (no second fixing bed on a wet wall), T-457"}
EVIDENCE_STATUS = "ASSUMED — OWNER-APPROVED"        # WORKFLOW s.5: the band, mix and per-m3 figures are owner values

DRY, WET = V5.DRY_FLOOR, V5.WET_FLOOR
BED_CODES = {"FIN.FLOOR.BED.DRY": DRY, "FIN.FLOOR.BED.WET": WET}
FINISH_CODES = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD")
WALL_TILE_CODES = ("FIN.WALL.TILE",)
OWNED_ELSEWHERE = {"FIN.STAIR": "stair bed 1:3 (B7, Q-53)", "FIN.ROOF": "roof screed (Q-41)",
                   "EXT.FLOOR": "outdoor floor bed (T-495)", "FIN.WALL": "wall: no fixing bed (UPC-WETWALL-001)",
                   "FIN.PLASTER": "render / spatter dash: plaster trade (T-454 / T-489)"}
BED_SUFFIX = ":bed"
TOL = 1e-6

FAIL_KINDS = ("PIN", "STALE_CANDIDATE", "UNIT", "LONE_LINE", "DOUBLE_LINE", "BAND_MISMATCH", "ORPHAN_BED",
              "WALL_BED", "OWNED_ELSEWHERE", "ARITHMETIC", "ZERO_FOR_HELD")


class BedError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p, pins=True):
    if pins and _sha(p) != PINS[p]:
        raise BedError(f"PIN: {Path(p).name} sha256 {_sha(p)[:8]} is not the pinned {PINS[p][:8]}")
    return json.loads(Path(p).read_text(encoding="utf-8"))


def host_of(element_id):
    return element_id[:-len(BED_SUFFIX)] if element_id.endswith(BED_SUFFIX) else None


def _fail(fails, kind, where, why):
    assert kind in FAIL_KINDS, kind
    fails.append({"kind": kind, "where": where, "why": why})


def owner_values(values=None):
    """The owner figures this table needs, read from the V5 (= V1 Q-45) record. Missing figures stay None."""
    v = V5.OWNER_VALUES if values is None else values
    out = {}
    for kind in (DRY, WET):
        mix = v["mix"].get(kind)
        per = v["per_m3_of_mortar"].get(mix) if mix else None
        out[kind] = {"band_m": v["bed_m"].get(kind), "mix": mix,
                     "cement_bags_per_m3": per["cement_bags_50kg"] if per else None,
                     "sand_m3_per_m3": per["sand_m3_loose"] if per else None}
    out["waste"] = v.get("mortar_waste")
    out["status"] = v.get("status")
    return out


# ------------------------------------------------------------------ one bed (R-T500-1 .. 4)

def bed_row(m2, m3, values=None, fails=None):
    """One physical bed from its measure pair -> the m3 row with cement / sand ranges (or HELD with the reason)."""
    fails = [] if fails is None else fails
    ov = owner_values(values)
    kind = BED_CODES[m3["item_code"]]
    k = ov[kind]
    row = {"id": m3["line_id"], "pair_m2_line": m2["line_id"] if m2 else None, "item_code": m3["item_code"],
           "element_id": m3["element_id"], "kind": kind, "binding": "BOUND_VOLUME_LINE",
           "area_m2": None, "band_m": list(k["band_m"]) if k["band_m"] else None, "mix": k["mix"],
           "installed_m3_low": None, "installed_m3_high": None,
           "cement_bags_low": None, "cement_bags_high": None, "sand_m3_low": None, "sand_m3_high": None,
           "waste_fraction": ov["waste"], "waste_cement_bags_low": None, "waste_cement_bags_high": None,
           "waste_sand_m3_low": None, "waste_sand_m3_high": None,
           "procurement_cement_bags_low": None, "procurement_cement_bags_high": None,
           "procurement_sand_m3_low": None, "procurement_sand_m3_high": None,
           "status": V5.HELD, "reason": None, "evidence_status": None}
    if m3.get("unit") != "m3" or (m2 is not None and m2.get("unit") != "m2"):
        _fail(fails, "UNIT", m3["line_id"], f"bed pair units {m2 and m2.get('unit')!r} / {m3.get('unit')!r}, not m2 / m3")
        row["reason"] = "UNIT"
        return row
    area = m2.get("measured_net") if m2 and m2.get("class") == "RELEASED" else None
    row["area_m2"] = area
    lo, hi = m3.get("held_low"), m3.get("held_high")
    if lo is None or hi is None:
        row["reason"] = "BED_RANGE_HELD (the m3 line carries no range: thickness or area HELD)"
        return row
    if k["band_m"] is None:
        row["reason"] = "BAND_NOT_GIVEN"
        return row
    if area is not None:
        exp = (_r(area * k["band_m"][0]), _r(area * k["band_m"][1]))
        if abs(exp[0] - lo) > TOL or abs(exp[1] - hi) > TOL:
            _fail(fails, "BAND_MISMATCH", m3["line_id"], f"m3 {lo} .. {hi} != area {area} x band {k['band_m']} = {exp}")
            row["reason"] = "BAND_MISMATCH"
            return row
    row.update(installed_m3_low=_r(lo), installed_m3_high=_r(hi))
    if k["cement_bags_per_m3"] is None or k["sand_m3_per_m3"] is None:
        row["reason"] = f"MIX_{k['mix']}_PER_M3_NOT_GIVEN"
        return row
    c, s = k["cement_bags_per_m3"], k["sand_m3_per_m3"]
    row.update(cement_bags_low=_r(lo * c), cement_bags_high=_r(hi * c), sand_m3_low=_r(lo * s), sand_m3_high=_r(hi * s))
    w = ov["waste"]
    if w is None:
        row.update(status="BOUND", reason="WASTE_NOT_GIVEN (procurement HELD)", evidence_status=EVIDENCE_STATUS)
        return row
    row.update(waste_cement_bags_low=_r(lo * c * w), waste_cement_bags_high=_r(hi * c * w),
               waste_sand_m3_low=_r(lo * s * w), waste_sand_m3_high=_r(hi * s * w),
               procurement_cement_bags_low=_r(lo * c * (1 + w)), procurement_cement_bags_high=_r(hi * c * (1 + w)),
               procurement_sand_m3_low=_r(lo * s * (1 + w)), procurement_sand_m3_high=_r(hi * s * (1 + w)),
               status="BOUND", reason="owner thickness band (range, never a mid value)",
               evidence_status=EVIDENCE_STATUS)
    return row


def wet_wall_bed(element):
    """A tiled wet wall: the bed keys are NOT_APPLICABLE (UPC-WETWALL-001). Asking for a bed on it is refused."""
    asked = [k for k in ("fixing_bed_m", "bed_m", "bed_low_m", "bed_high_m") if element.get(k) is not None]
    if asked:
        raise BedError(f"{element.get('id')!r}: a mortar fixing bed asked on a wet wall ({', '.join(asked)}): "
                       "the method is spatter dash + levelling render + adhesive, no second fixing bed (UPC-WETWALL-001)")
    return {"id": element.get("id"), "binding": "NOT_APPLICABLE_WITH_EVIDENCE",
            "reason": "NO_FIXING_BED_ON_WALL (UPC-WETWALL-001); render cement / sand: plaster trade T-454 / T-489"}


# ------------------------------------------------------------------ the table on a line set

def table(lines, values=None):
    """lines: candidate line dicts (line_id, item_code, element_id, class, unit, measured_net, held_low, held_high).
    -> {'rows', 'pair_rows', 'hosts', 'walls', 'subtotals', 'fails'}"""
    fails = []
    beds, finishes, walls = {}, {}, []
    for ln in lines:
        code = ln["item_code"]
        if code in BED_CODES:
            h = host_of(ln["element_id"])
            if h is None:
                _fail(fails, "ORPHAN_BED", ln["line_id"], f"bed element {ln['element_id']!r} has no ':bed' host")
                continue
            beds.setdefault(ln["element_id"], []).append(ln)
        elif code.startswith("FIN.FLOOR.BED.") or ".BED" in code:
            _fail(fails, "OWNED_ELSEWHERE", ln["line_id"], f"{code}: a bed code this table does not own")
        elif code in FINISH_CODES:
            finishes.setdefault(ln["element_id"], []).append(ln)
        elif code in WALL_TILE_CODES:
            walls.append(ln)
    rows, pair_rows = [], []
    for eid in sorted(beds):
        ls = beds[eid]
        m2s = [x for x in ls if x.get("unit") == "m2"]
        m3s = [x for x in ls if x.get("unit") == "m3"]
        other = [x for x in ls if x.get("unit") not in ("m2", "m3")]
        for x in other:
            _fail(fails, "UNIT", x["line_id"], f"bed line unit {x.get('unit')!r}")
        if len(m2s) > 1 or len(m3s) > 1:
            _fail(fails, "DOUBLE_LINE", eid, f"{len(m2s)} m2 + {len(m3s)} m3 bed lines on one element")
            continue
        if not m3s:
            if m2s:
                _fail(fails, "LONE_LINE", m2s[0]["line_id"], "m2 bed line with no m3 partner: no volume to bind")
            continue
        m2 = m2s[0] if m2s else None
        if m2 is None:
            _fail(fails, "LONE_LINE", m3s[0]["line_id"], "m3 bed line with no m2 partner")
        if m2s and m2["item_code"] != m3s[0]["item_code"]:
            _fail(fails, "DOUBLE_LINE", eid, "pair lines carry different bed codes")
            continue
        rows.append(bed_row(m2, m3s[0], values, fails))
        if m2 is not None:
            pair_rows.append({"id": m2["line_id"], "item_code": m2["item_code"], "element_id": eid,
                              "binding": "NOT_APPLICABLE_WITH_EVIDENCE",
                              "reason": f"measure pair partner (R-T420-1, price one basis): materials on {m3s[0]['line_id']}",
                              "area_m2": m2.get("measured_net"), "class": m2.get("class")})
    bed_hosts = {host_of(e) for e in beds}
    hosts = []
    for eid in sorted(finishes):
        for f in sorted(finishes[eid], key=lambda x: x["line_id"]):
            if eid in bed_hosts:
                state, why = "BEDDED", "bed pair on " + eid + BED_SUFFIX
            elif f.get("class") == "EXCLUDED":
                state, why = "NOT_APPLICABLE_WITH_EVIDENCE", "finish line EXCLUDED in the candidate: no tile laid, no bed"
            else:
                state, why = "MISSING_BED_LINE", (f"finish line {f.get('class')} with no bed pair: bed HELD, never 0 "
                                                  f"(area {f.get('measured_net')} / {f.get('held_low')} .. {f.get('held_high')})")
            hosts.append({"finish_line": f["line_id"], "item_code": f["item_code"], "element_id": eid,
                          "class": f.get("class"), "state": state, "why": why})
    for h in bed_hosts:
        if h not in finishes:
            _fail(fails, "ORPHAN_BED", h, "bed pair whose host has no floor-finish line")
    wall_rows = []
    for w in sorted(walls, key=lambda x: x["line_id"]):
        if (w["element_id"] + BED_SUFFIX) in beds:
            _fail(fails, "WALL_BED", w["line_id"], "a bed line on a wall-tile host (UPC-WETWALL-001: no fixing bed)")
        wall_rows.append({"id": w["line_id"], "element_id": w["element_id"], "binding": "NOT_APPLICABLE_WITH_EVIDENCE",
                          "reason": "NO_FIXING_BED_ON_WALL (UPC-WETWALL-001); render: plaster trade T-454 / T-489"})
    subs = subtotals(rows)
    _check_arithmetic(rows, values, fails)
    _check_zero(rows, subs, fails)
    return {"rows": rows, "pair_rows": pair_rows, "hosts": hosts, "walls": wall_rows, "subtotals": subs, "fails": fails}


KEYS = ("area_m2", "installed_m3_low", "installed_m3_high", "cement_bags_low", "cement_bags_high", "sand_m3_low",
        "sand_m3_high", "waste_cement_bags_low", "waste_cement_bags_high", "waste_sand_m3_low", "waste_sand_m3_high",
        "procurement_cement_bags_low", "procurement_cement_bags_high", "procurement_sand_m3_low",
        "procurement_sand_m3_high")


def _group_sub(rows):
    out = {"rows": len(rows)}
    for k in KEYS:
        out[k] = V5.subtotal([(r["id"], r[k]) for r in rows])
    for end in ("low", "high"):
        s = out[f"procurement_cement_bags_{end}"]
        out[f"cement_bags_to_buy_{end}"] = (math.ceil(round(s["value"], 6)) if s["status"] == V5.OK
                                            else None)      # R-T499-1: no whole bags from a HELD subtotal
    return out


def subtotals(rows):
    by = {}
    for r in rows:
        by.setdefault(r["item_code"], []).append(r)
    out = {code: _group_sub(rs) for code, rs in sorted(by.items())}
    out["PROJECT"] = _group_sub(rows)
    return out


def _check_arithmetic(rows, values, fails):
    ov = owner_values(values)
    for r in rows:
        if r["status"] != "BOUND":
            continue
        k = ov[r["kind"]]
        for end in ("low", "high"):
            v = r[f"installed_m3_{end}"]
            if abs(v * k["cement_bags_per_m3"] - r[f"cement_bags_{end}"]) > 1e-5 or \
               abs(v * k["sand_m3_per_m3"] - r[f"sand_m3_{end}"]) > 1e-5:
                _fail(fails, "ARITHMETIC", r["id"], f"{end} cement / sand not m3 x owner figure")
            p = r[f"procurement_cement_bags_{end}"]
            if p is not None and abs(p - r[f"cement_bags_{end}"] - r[f"waste_cement_bags_{end}"]) > 1e-5:
                _fail(fails, "ARITHMETIC", r["id"], f"{end} procurement != installed + waste")
        if r["installed_m3_low"] > r["installed_m3_high"] + TOL:
            _fail(fails, "ARITHMETIC", r["id"], "low end above high end")


def _check_zero(rows, subs, fails):
    for r in rows:
        if r["status"] != "BOUND" and any(r[k] == 0 for k in KEYS if k != "area_m2"):
            _fail(fails, "ZERO_FOR_HELD", r["id"], "a HELD row prints 0")
    for code, s in subs.items():
        for k in KEYS:
            if s[k]["status"] == V5.HELD and s[k]["value"] is not None:
                _fail(fails, "ZERO_FOR_HELD", code, f"{k}: HELD subtotal prints a value")


# ------------------------------------------------------------------ the candidate

def candidate_lines(pins=True):
    """The V3.0.53 floor-bed / floor-finish / wall-tile lines: the V3.0.51 index, proven unchanged by the T-487 identity."""
    idx, s = _load(INDEX, pins), _load(T487, pins)
    if idx["inputs"]["lines"] != BASE_LINES_SHA or idx["candidate_version"] != BASE:
        raise BedError("STALE_CANDIDATE: the line index is not V3.0.51 c0b6d664")
    if s["method"] != CANDIDATE or s["extends"] != BASE or not s["chain"]["V3_0_53"].startswith(CANDIDATE_SHA8):
        raise BedError("STALE_CANDIDATE: T-487 summary does not state V3.0.53 = 36863f6c extending V3.0.51")
    ident = s["identity"]
    if ident["replaced"] != 0 or ident["base_lines"] != len(idx["lines"]) \
            or ident["outside_rows_identical_to_base"] != ident["base_lines"]:
        raise BedError("STALE_CANDIDATE: V3.0.53 does not keep every V3.0.51 row")
    if set(s["totals_moved_by_code"]) != {"STR.CONC.LINTEL|m3"}:
        raise BedError("STALE_CANDIDATE: V3.0.53 moves a code other than STR.CONC.LINTEL")
    return idx["lines"]


def run(lines=None, values=None, pins=True):
    lines = candidate_lines(pins) if lines is None else lines
    t = table(lines, values)
    rows = t["rows"]
    n_bed = sum(1 for ln in lines if ln["item_code"] in BED_CODES)
    accounted = len(rows) + len(t["pair_rows"])
    return {"schema": SCHEMA, "method": METHOD_ID, "guard_class": GUARD_CLASS, "candidate": CANDIDATE,
            "candidate_sha8": CANDIDATE_SHA8, "base": BASE, "base_lines_sha256": BASE_LINES_SHA,
            "input_sha256": {Path(p).relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
            "rules": list(RULES), "sources": SOURCES, "owner_values": {k: v for k, v in owner_values(values).items()},
            "census": {"bed_lines": n_bed, "bound_m3_rows": len(rows), "pair_m2_not_applicable": len(t["pair_rows"]),
                       "accounted": accounted,
                       "bound": sum(1 for r in rows if r["status"] == "BOUND"),
                       "held": sum(1 for r in rows if r["status"] != "BOUND"),
                       "floor_finish_lines": len(t["hosts"]),
                       "hosts_by_state": _count(h["state"] for h in t["hosts"]),
                       "wall_tile_lines_not_applicable": len(t["walls"])},
            "rows": rows, "pair_rows": t["pair_rows"], "hosts": t["hosts"], "walls": t["walls"],
            "subtotals": t["subtotals"], "fails": t["fails"]}


def _count(it):
    out = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


CSV_COLS = ("id", "pair_m2_line", "item_code", "element_id", "kind", "area_m2", "mix", "installed_m3_low",
            "installed_m3_high", "cement_bags_low", "cement_bags_high", "sand_m3_low", "sand_m3_high",
            "waste_fraction", "procurement_cement_bags_low", "procurement_cement_bags_high",
            "procurement_sand_m3_low", "procurement_sand_m3_high", "status", "evidence_status", "reason")


def write(m, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "TILE_BED_MORTAR_T500.json").write_text(json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False)
                                                      + "\n", encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in m["rows"]:
        w.writerow(["" if r.get(c) is None else r.get(c) for c in CSV_COLS])
    (out_dir / "TILE_BED_MORTAR_T500.csv").write_text(buf.getvalue(), encoding="utf-8")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    m = run()
    if "--check" in argv:
        for f in m["fails"]:
            print(f"FAIL {f['kind']} {f['where']}: {f['why']}")
        print(f"T-500 check: {len(m['fails'])} failures; census {json.dumps(m['census'], sort_keys=True)}")
        return 1 if m["fails"] else 0
    out = Path(argv[0]) if argv else HERE / "out"
    write(m, out)
    p = m["subtotals"]["PROJECT"]
    print(f"T-500: {m['census']['accounted']} / {m['census']['bed_lines']} bed lines accounted; fails {len(m['fails'])}; "
          f"installed {p['installed_m3_low']['value']} .. {p['installed_m3_high']['value']} m3; cement "
          f"{p['cement_bags_low']['value']} .. {p['cement_bags_high']['value']} bags; to buy "
          f"{p['cement_bags_to_buy_low']} .. {p['cement_bags_to_buy_high']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
