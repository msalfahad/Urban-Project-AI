"""T-511: CEMENT / SAND PRODUCER CENSUS and cross-trade binding on the candidate of record ARCH_TAKEOFF_V3.0.56
(research, UNWIRED: no candidate, released, engine, rule, knowledge or registry file changes; no line moves).

Physical element (ERS s.2.1): the 50 kg bags of cement and the loose sand bought for SITE-MIXED cement : sand mortar,
layer by layer, on the candidate's lines: black-block laying mortar (T-453 r2, 1:4 Q-78), the plaster coats (bond coat,
wall plaster, wet-wall levelling render: T-454 installed / T-489 mix, PLASTER_MATERIALS_TABLE_V3 subtotals), the
floor-tile bed (T-500, Q-45 bands, 1:4) and any other cement : sand layer the candidate carries (stone beds, screeds,
fence masonry, outdoor beds). Ready-mix concrete, precast lintels, bagged adhesive and AAC glue are other products
(their own keys), never cement : sand. Kept apart per row: installed (theoretical) quantity, waste, procurement.

Rules (project-independent; scope: every villa):
  R-T511-1 CLASSIFY: every item code on the candidate is in CODE_TABLE as a HOST (one cement : sand layer per line,
           named trade), a PARTNER (measure-pair / count partner of a host: no second key), NOT_A_KEY (another
           product, with the reason) or SCOPE_OPEN (finish / fixing system not stated: named, not summed, not 0).
           An unclassified code fails (UNCLASSIFIED_CODE): a new code is never silently out of the cement total.
  R-T511-2 ONE PRODUCER per PHYSICAL key (host element, layer, material, stage). A bed line and its floor-finish
           host are ONE physical key (the bed is keyed on its host), so a finish-table row on the host is a second
           producer (TWO_PRODUCERS) unless it is a READER, which must equal the producer (READER_DIVERGENCE) at the
           same stage. BESIDE and OPTION rows are never summed. No cement : sand key on a NOT_A_KEY / PARTNER line
           (KEY_ON_NON_HOST: e.g. a wet wall's tile line; its render is the plaster line's, UPC-WETWALL-001).
  R-T511-3 FRESHNESS: a producer row carries what it read (class, net). If the candidate line no longer carries
           that figure (line now HELD / EXCLUDED / absent, or a different net) the producer figure is STALE: it
           leaves the sum, the contributor is HELD by name and the figure stays BESIDE. Never re-scaled here.
  R-T511-4 UNITS / HELD: cement in 50 kg bags, sand in loose m3; anything else fails (UNIT). A HELD row never
           carries 0 (ZERO_FOR_HELD); a range has low <= high.
  R-T511-5 SUBTOTALS: per trade, per stage and per range end, by R-T499-1 (engine FINISH_MATERIALS_TABLE_V5
           .subtotal): COMPUTED only when every contributor of the group carries a number; otherwise HELD, value
           None, the known part AT_LEAST, the held contributors listed. Whole bags only over a COMPUTED project
           subtotal; waste only where a source gives it (else HELD).
  R-T511-6 COMPLETENESS BY HOST: every HOST line ends in exactly one state per material: PRODUCED (fresh producer
           row), HELD (producer row held, stale, or NO_PRODUCER with the reason) or NOT_APPLICABLE (with evidence:
           line EXCLUDED, white AAC masonry, bed host not bedded with the producer's evidence).

    python3 -I research/agents_t511/t511_cement_sand_census.py [OUT_DIR]   # CEMENT_SAND_CENSUS_T511.json / .csv
    python3 -I research/agents_t511/t511_cement_sand_census.py --check     # exit 1 on any failure
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

from engine.source import finish_materials_table as V1  # noqa: E402
from engine.source import finish_materials_table_v5 as V5  # noqa: E402

SCHEMA = "URBAN_T511_CEMENT_SAND_CENSUS_V1"
GUARD_CLASS = "UNWIRED_READER"
CANDIDATE = "ARCH_TAKEOFF_V3.0.56"
CANDIDATE_SHA8 = "4e25c54f"
BASE = "ARCH_TAKEOFF_V3.0.55"
BASE_SHA8 = "a498fc61"

R = "research/"
INDEX = ROOT / (R + "agents_t508/out/LINE_INDEX_V3_0_55.json")
T508 = ROOT / (R + "agents_t508/summary_t508.json")
T453 = ROOT / (R + "agents_t453/out/MATERIAL_LEDGER_T453.json")
T454 = ROOT / (R + "agents_t454/out/PLASTER_MATERIALS_T454.json")
T489 = ROOT / (R + "agents_t489/out/PLASTER_MIX_T489.json")
T500 = ROOT / (R + "agents_t500/out/TILE_BED_MORTAR_T500.json")
T495 = ROOT / (R + "agents_t495/out/TILE_PURCHASE_LEDGER_V2.json")
T455 = ROOT / (R + "agents_t455/out/TILE_PURCHASE_T455.json")
PINS = {INDEX: "80b7a634f866af0ca38d5974feb9c72b8b4511f03e827e9b6738b2f9b8cc81c2",
        T508: "8e5f55876e7f49ada616ef01188055f171e1df47750fe3e104b45f58fbe7bd22",
        T453: "ad9bceee3bfdbc12218edec2a648e39104f3503bd73342c8ebb451b8394c13f9",
        T454: "dd144416850ca735e114a7c6ee3d56fbcdc3e41eacc89bea9297fb3af4a57f66",
        T489: "f04659307895198813cc378462dc14e68d98865ff58b8415def74d158fa173f7",
        T500: "e2689c7c3da11d9faf4a2133cd2946d96a74c4fe8c252471e6256ad8d2243a61",
        T495: "56aa1813c08ff738c496a4189b896af47a383a816ea55527eae2b1fd4ff5b94d",
        T455: "30f3c90eeee907b9e531d73c9e43f3ec8dae8d249a4151963046c48e0ec9bed8"}

CEMENT, SAND = "CEMENT_50KG", "SAND_LOOSE"
MATERIALS = (CEMENT, SAND)
UNIT_OF = {CEMENT: "bags", SAND: "m3"}
INSTALLED, WASTE, PROCUREMENT = "INSTALLED", "WASTE", "PROCUREMENT"
STAGES = (INSTALLED, WASTE, PROCUREMENT)
PRODUCER, READER, BESIDE, OPTION = "PRODUCER", "READER", "BESIDE", "OPTION"
PRODUCED, HELD, NA = "PRODUCED", "HELD", "NOT_APPLICABLE"
TOL = 1e-6

# trade names (one cement key, several trades)
MASONRY, PLASTER, TILE_BED, STONE_BED, SCREED, OUTDOOR_BED = (
    "MASONRY_LAYING", "PLASTER_COATS", "TILE_BED", "STONE_BED", "SCREED", "OUTDOOR_BED")

# R-T511-1. kind: HOST (trade, reason when no producer) / PARTNER / NOT_A_KEY / SCOPE_OPEN.
_NK_CONC = "ready-mix concrete: bought as concrete m3, not as bagged cement and loose sand"
_NK = "not a cement : sand layer"
CODE_TABLE = {
    "MAS.BLOCK": ("HOST", MASONRY, "black-block laying mortar 1:4 (Q-78); white AAC: glue, its own key"),
    "EXT.FENCE.BLOCK": ("HOST", MASONRY, "fence block laying mortar: no material table reads the fence masonry"),
    "EXT.FENCE.MASONRY_BELOW_NG": ("HOST", MASONRY, "fence masonry below ground: no material table reads it"),
    "EXT.FENCE.BLOCK_COUNT": ("PARTNER", None, "unit count of the EXT.FENCE.BLOCK masonry (same mortar)"),
    "FIN.PLASTER": ("HOST", PLASTER, "plaster coats: bond coat, wall plaster, wet-wall levelling render"),
    "EXT.FENCE.PLASTER": ("HOST", PLASTER, "fence plaster coats"),
    "FIN.EXT.FINISH": ("HOST", PLASTER, "exterior render / Sigma system: no mix and no material table "
                                        "(T-489 not in scope; T-314 exterior rows)"),
    "FIN.FLOOR.BED.DRY": ("HOST", TILE_BED, "1:4 bed under a dry floor tile (Q-45 3-4 cm)"),
    "FIN.FLOOR.BED.WET": ("HOST", TILE_BED, "1:4 bed (bartash) under a wet floor tile (Q-45 4-6 cm)"),
    "FIN.FLOOR.PORCELAIN": ("PARTNER", None, "floor finish: its bed is its FIN.FLOOR.BED line (keyed on this host)"),
    "FIN.FLOOR.WET_TILE": ("PARTNER", None, "floor finish: its bed is its FIN.FLOOR.BED line (keyed on this host)"),
    "FIN.FLOOR.FINISH_HELD": ("PARTNER", None, "floor finish: bed per T-500 host state (BEDDED / MISSING)"),
    "FIN.WALL.TILE": ("NOT_A_KEY", None, "wet wall: adhesive only, no fixing bed; its render is the FIN.PLASTER "
                                         "line (UPC-WETWALL-001, T-457): one face, two materials"),
    "EXT.FLOOR.OUTDOOR": ("HOST", OUTDOOR_BED, "outdoor floor, finish not decided (T-495 options, OD-1)"),
    "EXT.FLOOR.PORCELAIN": ("HOST", OUTDOOR_BED, "released outdoor porcelain: no table binds its bed (T-500 = "
                                                 "interior B3-05 beds; T-495 = finish-HELD outdoor lines only); "
                                                 "bed basis for an exterior walk not stated"),
    "EXT.PAVING.INTERLOCK": ("HOST", OUTDOOR_BED, "interlock on a sand bed: no owner rule for pavers or their bed "
                                                  "(T-495 DECLARED_OUT)"),
    "FIN.MARBLE.TREAD": ("HOST", STONE_BED, "marble on a 1:3 bed (Q-45 stairs 3 cm, Q-53 C): no bed line, "
                                            "no material table on the candidate"),
    "FIN.MARBLE.RISER": ("HOST", STONE_BED, "marble on a 1:3 bed (Q-45 / Q-53 C): no bed line, no table"),
    "FIN.MARBLE.LANDING": ("HOST", STONE_BED, "landing marble bed: no bed line, no table"),
    "FIN.MARBLE.THRESHOLD": ("HOST", STONE_BED, "threshold marble bed: thickness / mix not stated, no table"),
    "FIN.MARBLE.LIFT_SURROUND": ("HOST", STONE_BED, "lift surround marble fixing: not stated, no table"),
    "FIN.MARBLE.LIFT_THRESHOLD": ("HOST", STONE_BED, "lift threshold marble bed: not stated, no table"),
    "FIN.ROOF.SCREED": ("HOST", SCREED, "roof screed to falls: thickness HELD (Q-41), mix not stated, no table"),
    "WP.FOUNDATION.FOOTING_SCREED": ("HOST", SCREED, "printed '5 cm screed' (ST p.13): mix not printed, no table"),
    "WP.FOUNDATION.LIFT_PIT_SCREED": ("HOST", SCREED, "lift-pit base screed: mix not printed, no table"),
    "FIN.STAIR.FLIGHT": ("PARTNER", None, "flight length record: the bed belongs to the tread / riser m2 lines"),
    "FIN.STAIR.STEP_LM": ("PARTNER", None, "step-edge length record (tread / riser m2 lines carry the bed)"),
    "FIN.SKIRTING": ("SCOPE_OPEN", None, "skirting fixing material not stated (adhesive or mortar)"),
    "FIN.STAIR.SKIRTING.ZIGZAG": ("SCOPE_OPEN", None, "stair skirting fixing material not stated"),
    "FIN.STAIR.SKIRTING.SLOPED": ("SCOPE_OPEN", None, "stair skirting fixing material not stated"),
    "FIN.ROOF.PROTECTION": ("SCOPE_OPEN", None, "roof protection layer type not stated"),
    "FIN.ROOF.FINISH": ("SCOPE_OPEN", None, "roof finish and its fixing not stated"),
    "FIN.STAIR.SOFFIT": ("SCOPE_OPEN", None, "stair soffit finish system not stated (T-489 not in scope)"),
    "FIN.DOME.SOFFIT": ("SCOPE_OPEN", None, "dome intrados finish system not stated"),
    "FIN.CEILING": ("SCOPE_OPEN", None, "ceiling type not in a plan (O-P8-02): plaster or false ceiling unknown"),
    "FIN.CEILING.BULKHEAD": ("SCOPE_OPEN", None, "bulkhead construction not stated"),
    "EXT.FENCE.TOP": ("SCOPE_OPEN", None, "fence coping / top finish not stated"),
}
for _c in ("STR.CONC.BEAM", "STR.CONC.BLINDING", "STR.CONC.BOUNDARY_PAD", "STR.CONC.BOUNDARY_WALL",
           "STR.CONC.COLUMN", "STR.CONC.DOME", "STR.CONC.FOOTING", "STR.CONC.GROUND_BEAM", "STR.CONC.GROUND_SLAB",
           "STR.CONC.LIFT", "STR.CONC.NECK", "STR.CONC.PARAPET", "STR.CONC.POOL", "STR.CONC.SLAB",
           "STR.CONC.STAIR", "STR.CONC.STRAP"):
    CODE_TABLE[_c] = ("NOT_A_KEY", None, _NK_CONC)
CODE_TABLE["STR.CONC.LINTEL"] = ("NOT_A_KEY", None, "precast lintel pieces (owner rule 2026-11-02)")
for _c, _why in (("STR.REBAR", "steel"), ("STR.FORMWORK", "formwork"), ("STR.FORMWORK.STAIR", "formwork"),
                 ("STR.EARTH.BACKFILL", "earthworks"), ("STR.EARTH.DISPOSAL", "earthworks"),
                 ("STR.EARTH.EXCAVATION", "earthworks"), ("FIN.PAINT", "paint"), ("FIN.PAINT.CEILING", "paint"),
                 ("EXT.FENCE.PAINT", "paint"), ("FIN.ROOF.INSULATION", "insulation board"),
                 ("FIN.RAILING", "metal"), ("FIN.HANDRAIL", "metal"), ("MET.RAILING.GUARD", "metal"),
                 ("DOOR.EXTERNAL.ALUMINIUM", "door"), ("DOOR.INTERNAL.PVC", "door"), ("DOOR.MAIN_ENTRANCE", "door"),
                 ("EXT.FENCE.GATE", "gate"), ("EXT.POOL.WATER_FACE", "water-face record"),
                 ("EXT.FENCE.FACE", "fence face geometry record (plaster / paint lines carry the materials)"),
                 ("EXT.FENCE.WALL", "fence wall geometry record (block / plaster lines carry the materials)"),
                 ("WP.FOUNDATION.BURIED_LIQUID", "liquid membrane"), ("WP.FOUNDATION.FOOTING_MEMBRANE", "membrane"),
                 ("WP.FOUNDATION.FOOTING_SIDES", "membrane"), ("WP.FOUNDATION.LIFT_PIT_BOARD", "protection board"),
                 ("WP.FOUNDATION.LIFT_PIT_MEMBRANE", "membrane"), ("WP.FOUNDATION.PROCUREMENT", "membrane rolls"),
                 ("FIN.WP.DOORWAY", "membrane"), ("FIN.WP.DOORWAY_TRANSITION", "membrane"),
                 ("FIN.WP.DOORWAY_TRANSITION_NR", "membrane"), ("FIN.WP.FLOOR", "membrane (bartash = bed line)"),
                 ("FIN.WP.MEMBRANE_ROLLS", "membrane rolls"), ("FIN.WP.PENETRATION", "membrane"),
                 ("FIN.WP.ROOF", "membrane"), ("FIN.WP.ROOF_UPTURN", "membrane"), ("FIN.WP.TERMINATION", "membrane"),
                 ("FIN.WP.WALL_UPTURN", "membrane")):
    CODE_TABLE[_c] = ("NOT_A_KEY", None, f"{_NK}: {_why}")
for _c in ("ARCH.EXTERIOR", "ARCH.FACADE", "ARCH.FACADE_RUN", "ARCH.PASSAGE", "ARCH.SHUTTER", "ARCH.SPACE",
           "ARCH.THRESHOLD", "ARCH.WALL_PANEL", "ARCH.WALL_RUN", "ARCH.WALL_VOLUME", "ARCH.WINDOW",
           "ARCH.WINDOW_REVEAL"):
    CODE_TABLE[_c] = ("NOT_A_KEY", None, f"{_NK}: geometry record (the finish lines carry the materials)")

FAIL_KINDS = ("PIN", "STALE_CANDIDATE", "UNCLASSIFIED_CODE", "TWO_PRODUCERS", "READER_DIVERGENCE", "LONE_READER",
              "KEY_ON_NON_HOST", "UNIT", "ZERO_FOR_HELD", "RANGE_ORDER", "HOST_STATE", "ARITHMETIC")


class CensusError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p, pins=True):
    if pins and _sha(p) != PINS[p]:
        raise CensusError(f"PIN: {Path(p).name} sha256 {_sha(p)[:8]} is not the pinned {PINS[p][:8]}")
    return json.loads(Path(p).read_text(encoding="utf-8"))


def prow(table, role, line_id, host, layer, material, stage, low, high, unit=None, read=None, status=None,
         reason=None, trade=None):
    """One producer / reader / beside / option row. low == high for a point figure; None = HELD (never 0)."""
    return {"table": table, "role": role, "line_id": line_id, "host": host or line_id, "layer": layer,
            "material": material, "stage": stage, "unit": unit or UNIT_OF.get(material), "low": _r(low),
            "high": _r(high), "read": read, "status": status or (HELD if low is None else "COMPUTED"),
            "reason": reason, "trade": trade}


# ---------------------------------------------------------------- the rules (project-independent) ----------------
def _fail(fails, kind, where, why):
    fails.append({"kind": kind, "where": where, "why": why})


def _fresh(row, line):
    """R-T511-3: None if the producer's figure still stands on the candidate line, else the STALE reason."""
    if row["low"] is None:
        return None
    if line is None:
        return "STALE_ABSENT: line not on the candidate"
    rd = row.get("read") or {}
    if line["class"] != rd.get("class"):
        return f"STALE_CLASS: producer read {rd.get('class')}, candidate line is {line['class']}"
    if "net" in rd and rd["net"] is not None:
        net = line["measured_net"]
        if net is None or abs(net - rd["net"]) > TOL:
            return f"STALE_NET: producer read {rd['net']}, candidate net {net}"
    return None


def census(lines, rows, host_states=None, code_table=None):
    """lines: candidate lines; rows: prow() rows; host_states: {line_id: (state, material, reason)} for every HOST
    line not covered by a producer row (NO_PRODUCER / NOT_APPLICABLE / HELD). Returns the census dict."""
    code_table = CODE_TABLE if code_table is None else code_table
    host_states = host_states or {}
    fails, by_id = [], {ln["line_id"]: ln for ln in lines}
    # R-T511-1
    for c in sorted({ln["item_code"] for ln in lines}):
        if c not in code_table:
            _fail(fails, "UNCLASSIFIED_CODE", c, "item code in no class of CODE_TABLE")
    # R-T511-4
    for r in rows:
        w = f"{r['table']}|{r['line_id']}|{r['layer']}|{r['material']}|{r['stage']}"
        if r["unit"] != UNIT_OF.get(r["material"]):
            _fail(fails, "UNIT", w, f"{r['material']} in {r['unit']} (must be {UNIT_OF.get(r['material'])})")
        if r["status"] == HELD and (r["low"] == 0.0 or r["high"] == 0.0):
            _fail(fails, "ZERO_FOR_HELD", w, "a HELD row carries 0")
        if r["low"] is not None and (r["high"] is None or r["low"] - r["high"] > TOL):
            _fail(fails, "RANGE_ORDER", w, f"low {r['low']} high {r['high']}")
        ln = by_id.get(r["line_id"])
        kind = code_table.get(ln["item_code"], ("?",))[0] if ln else None
        if ln is not None and kind != "HOST" and r["role"] in (PRODUCER, READER):
            _fail(fails, "KEY_ON_NON_HOST", w, f"{ln['item_code']} is {kind}: no cement : sand key")
    # R-T511-2
    keys = {}
    for r in rows:
        keys.setdefault((r["host"], r["layer"], r["material"], r["stage"]), []).append(r)
    for k, rs in sorted(keys.items(), key=lambda kv: str(kv[0])):
        prods = [r for r in rs if r["role"] == PRODUCER]
        if len(prods) > 1:
            _fail(fails, "TWO_PRODUCERS", "|".join(map(str, k)), "producers: " + ", ".join(r["table"] for r in prods))
        for r in rs:
            if r["role"] != READER:
                continue
            if not prods:
                _fail(fails, "LONE_READER", "|".join(map(str, k)), f"{r['table']} reads no producer")
                continue
            p = prods[0]
            if (p["low"] is None) != (r["low"] is None) or (p["low"] is not None and (
                    abs(p["low"] - r["low"]) > 1e-5 or abs(p["high"] - r["high"]) > 1e-5)):
                _fail(fails, "READER_DIVERGENCE", "|".join(map(str, k)),
                      f"{r['table']} {r['low']}..{r['high']} vs {p['table']} {p['low']}..{p['high']}")
    # contributors per (trade, stage, material): fresh producer figures, held producer rows, held host states
    contrib, stale, states = [], [], {}
    for r in rows:
        if r["role"] != PRODUCER:
            continue
        ln = by_id.get(r["line_id"])
        why = _fresh(r, ln)
        c = dict(r)
        if why:
            stale.append({"line_id": r["line_id"], "table": r["table"], "layer": r["layer"],
                          "material": r["material"], "stage": r["stage"], "beside_low": r["low"],
                          "beside_high": r["high"], "why": why})
            c.update(low=None, high=None, status=HELD, reason=why)
        contrib.append(c)
        if r["stage"] == INSTALLED:
            st = PRODUCED if c["low"] is not None else HELD
            prev = states.get((r["line_id"], r["material"]))
            states[(r["line_id"], r["material"])] = HELD if HELD in (st, prev) else st
    for lid, (st, trade, reason) in sorted(host_states.items()):
        for m in MATERIALS:
            if (lid, m) in states:
                _fail(fails, "HOST_STATE", lid, f"host has a producer row and a declared state {st}")
                continue
            states[(lid, m)] = st
            if st == HELD:
                for stg in STAGES:
                    contrib.append(prow("NONE", PRODUCER, lid, lid, trade, m, stg, None, None, reason=reason,
                                        trade=trade))
    # R-T511-6
    for ln in lines:
        kind = code_table.get(ln["item_code"], ("?",))[0]
        if kind != "HOST":
            continue
        for m in MATERIALS:
            if (ln["line_id"], m) not in states:
                _fail(fails, "HOST_STATE", ln["line_id"], f"{ln['item_code']} {m}: no producer row and no state")
    return {"fails": fails, "contributors": contrib, "stale": stale, "states": states,
            "subtotals": subtotals(contrib)}


def _sub(items):
    return V5.subtotal(items)


def subtotals(contrib):
    """R-T511-5: per trade and project, per stage, per material, per range end (R-T499-1)."""
    out, groups = {}, {}
    for c in contrib:
        if c["role"] != PRODUCER:
            continue
        for scope in (c["trade"], "PROJECT"):
            groups.setdefault((scope, c["stage"], c["material"]), []).append(c)
    for (scope, stage, mat), cs in sorted(groups.items()):
        lo = _sub([(f"{c['line_id']}|{c['layer']}", c["low"]) for c in cs])
        hi = _sub([(f"{c['line_id']}|{c['layer']}", c["high"]) for c in cs])
        e = {"low": lo["value"], "high": hi["value"], "status": lo["status"] if lo["status"] == hi["status"] else HELD,
             "at_least_low": lo["at_least"], "at_least_high": hi["at_least"], "rows": lo["rows"],
             "held": sorted(set(lo["held_rows"]) | set(hi["held_rows"])), "unit": UNIT_OF[mat]}
        if mat == CEMENT and e["status"] == "COMPUTED":
            e["whole_bags_low"], e["whole_bags_high"] = math.ceil(e["low"] - 1e-9), math.ceil(e["high"] - 1e-9)
        out.setdefault(scope, {}).setdefault(stage, {})[mat] = e
    return out


# ---------------------------------------------------------------- the candidate of record --------------------------
def candidate(pins=True):
    """V3.0.56 = the V3.0.55 line index + the T-508 change set (FIN.SKIRTING / FIN.STAIR.SKIRTING only). Every
    cement : sand HOST / PARTNER line is identical between them (asserted)."""
    idx, s = _load(INDEX, pins), _load(T508, pins)
    if not idx["inputs"]["lines"].startswith(BASE_SHA8) or s["chain"]["V3_0_55"] != BASE_SHA8 \
            or s["chain"]["V3_0_56"] != CANDIDATE_SHA8 or s["method"] != CANDIDATE or s["extends"] != BASE:
        raise CensusError("STALE_CANDIDATE: the T-508 identity block is not V3.0.55 -> V3.0.56")
    touched = {r["item_code"] for r in s["rows"]}
    for c in touched:
        if CODE_TABLE.get(c, ("?",))[0] in ("HOST", "PARTNER", "?"):
            raise CensusError(f"STALE_CANDIDATE: T-508 changes {c}, a cement : sand host; rebuild on V3.0.56")
    lines = [dict(ln) for ln in idx["lines"]]
    for r in s["rows"]:              # the added / replaced skirting lines (SCOPE_OPEN): carried by code only
        if r["line_id"] and r["line_id"] not in {ln["line_id"] for ln in lines}:
            lines.append({"line_id": r["line_id"], "item_code": r["item_code"], "element_id": r["element_id"],
                          "class": "ADDED_T508", "measured_net": None, "held_low": None, "held_high": None,
                          "unit": r["unit"]})
    ident = {"base_lines": len(idx["lines"]), "t508_rows": len(s["rows"]), "t508_codes": sorted(touched),
             "v3_0_56_lines_t508": s["identity"]["v3_0_56_lines"]}
    return lines, ident


# ---------------------------------------------------------------- readers of the merged tables ----------------------
def _read(ln):
    return {"class": ln["class"], "net": ln["measured_net"]} if ln else None


def masonry_rows(lines, pins=True):
    """T-453 r2 (PRODUCER of black-block mortar cement / sand, R-T506-2): one installed row per material per black
    source line, with what it read on V3.0.45. Waste and procurement: not sourced -> HELD. White AAC: NOT_APPLICABLE
    (glue). Parent lines (material not established) and MAS.BLOCK lines no T-453 row reads: HELD by name."""
    d = _load(T453, pins)
    src = {s["line_id"]: s for s in d["source_lines"]}
    by_id = {ln["line_id"]: ln for ln in lines}
    rows, states = [], {}
    for b in d["block_materials"]:
        if b["item"] != "LAYING_MATERIAL":
            continue
        lid, s = b["line_id"], src[b["line_id"]]
        if s.get("material") == "WHITE":
            states[lid] = (NA, MASONRY, "white AAC masonry: laid in AAC glue (own key, T-453 R-T453-2)")
            continue
        if s.get("material") != "BLACK":
            continue
        read = {"class": s["class"], "net": s["net_m2"]}
        for m, k in ((CEMENT, "cement_bags"), (SAND, "sand_m3_loose")):
            v, rg = b.get(k), b.get(k + "_range")
            lo, hi = (v, v) if v is not None else (tuple(rg) if rg else (None, None))
            why = None if lo is not None else f"T-453 {b['label']}: {b.get('why') or b.get('base_why') or 'HELD'}"
            rows.append(prow("T-453", PRODUCER, lid, lid, MASONRY, m, INSTALLED, lo, hi, read=read, reason=why,
                             status=None if lo is None else ("RANGE" if lo != hi else "COMPUTED"), trade=MASONRY))
            for stg in (WASTE, PROCUREMENT):
                rows.append(prow("T-453", PRODUCER, lid, lid, MASONRY, m, stg, None, None, read=read, trade=MASONRY,
                                 reason="no waste / purchase factor sourced for block mortar (T-453 procurement HELD)"))
    for ln in lines:
        if ln["item_code"] != "MAS.BLOCK" or ln["line_id"] in states:
            continue
        if ln["line_id"] in {r["line_id"] for r in rows}:
            continue
        s = src.get(ln["line_id"])
        if s is None:
            states[ln["line_id"]] = (HELD, MASONRY, f"NO_PRODUCER: {ln['element_id']} is read by no material table "
                                                    "(T-496 KNOWN GAP, V3.0.46 house below-ground masonry)")
        else:
            states[ln["line_id"]] = (HELD, MASONRY, "material not established on the parent line (its held walls / "
                                                    "pieces are named in the candidate): block type HELD")
    for ln in lines:
        if ln["item_code"] in ("EXT.FENCE.BLOCK", "EXT.FENCE.MASONRY_BELOW_NG"):
            states[ln["line_id"]] = (HELD, MASONRY, "NO_PRODUCER: " + CODE_TABLE[ln["item_code"]][2])
    _ = by_id
    return rows, states


_COAT_MAT = ((CEMENT, "cement_bags"), (SAND, "sand_m3"))


def plaster_rows(lines, pins=True):
    """T-489 PRODUCER of the coats' cement / sand (V2 mix stage; R-T506-3), T-454 BESIDE (installed mortar, no mix).
    Every coat row of the 70 lines is HELD on V3.0.56 (no readable source prints a coat's mix; T-489 s.2): carried
    HELD with T-489's reason. The 13 T-454 excluded lines: NOT_APPLICABLE. FIN.EXT.FINISH: NO_PRODUCER."""
    a, b = _load(T489, pins), _load(T454, pins)
    by_id = {ln["line_id"]: ln for ln in lines}
    beside = {(r["id"], ly["layer"]): ly for r in b["table"]["rows"] for ly in r["layers"]}
    rows, states = [], {}
    for r in a["table"]["rows"]:
        ln = by_id.get(r["id"])
        read = {"class": r.get("line_class"), "net": r.get("area_m2")}
        if ln is not None and read["class"] is None:
            read["class"] = ln["class"]
        for ly in r["layers"]:
            for m, k in _COAT_MAT:
                v, al = ly.get(k), ly.get(k + "_at_least")
                rows.append(prow("T-489", PRODUCER, r["id"], r["id"], ly["layer"], m, INSTALLED, v, v, read=read,
                                 reason=None if v is not None else (ly.get("materials_reason") or ly.get("reason")),
                                 trade=PLASTER))
                bl = beside.get((r["id"], ly["layer"]), {})
                if bl.get(k) is not None or al is not None:
                    bv = bl.get(k) if bl.get(k) is not None else al
                    rows.append(prow("T-454" if bl.get(k) is not None else "T-489", BESIDE, r["id"], r["id"],
                                     ly["layer"], m, INSTALLED, bv, bv, read=read, trade=PLASTER,
                                     reason="BESIDE: not summed"))
                for stg in (WASTE, PROCUREMENT):
                    rows.append(prow("T-489", PRODUCER, r["id"], r["id"], ly["layer"], m, stg, None, None, read=read,
                                     trade=PLASTER, reason="no waste / purchase factor sourced (T-489 s.Open)"))
    for e in b["excluded"]:
        states[e["line_id"]] = (NA, PLASTER, "T-454: " + e["why"])
    for ln in lines:
        if ln["item_code"] == "FIN.EXT.FINISH":
            states[ln["line_id"]] = (HELD, PLASTER, "NO_PRODUCER: " + CODE_TABLE["FIN.EXT.FINISH"][2])
    return rows, states


def bed_rows(lines, pins=True):
    """T-500 PRODUCER of the tile-bed cement / sand, keyed on the FLOOR-FINISH HOST (one physical bed per host),
    installed + waste + procurement. FINISH_MATERIALS_TABLE V1 materials() on the host area = READER at the
    procurement stage (its mortar has the 5 % waste folded in) and must agree. The m2 partner of each measure pair:
    NOT_APPLICABLE. A MISSING bed host: HELD by name with its widest-band effect beside."""
    t = _load(T500, pins)
    by_id = {ln["line_id"]: ln for ln in lines}
    host_of = {h["element_id"]: h for h in t["hosts"]}
    rows, states, missing = [], {}, []
    for r in t["rows"]:
        h = host_of[r["element_id"][:-len(":bed")]]
        host = h["finish_line"]
        ln = by_id.get(r["id"])
        read = {"class": "HELD", "net": None}            # the bed m3 line is a HELD range: compare the range below
        if ln is not None and (abs((ln["held_low"] or -1) - r["installed_m3_low"]) > TOL
                               or abs((ln["held_high"] or -1) - r["installed_m3_high"]) > TOL):
            read = {"class": "RANGE_DIFFERS", "net": None}
        for m, k in ((CEMENT, "cement_bags"), (SAND, "sand_m3")):
            for stg, pre in ((INSTALLED, ""), (WASTE, "waste_"), (PROCUREMENT, "procurement_")):
                rows.append(prow("T-500", PRODUCER, r["id"], host, TILE_BED, m, stg, r[f"{pre}{k}_low"],
                                 r[f"{pre}{k}_high"], read=read, status="BOUND", trade=TILE_BED))
        v1 = V1.materials(r["kind"], None, r["area_m2"])
        rows.append(prow("FINISH_MATERIALS_TABLE_V1", READER, r["id"], host, TILE_BED, CEMENT, PROCUREMENT,
                         v1["cement_bags_low"], v1["cement_bags_high"], trade=TILE_BED))
        rows.append(prow("FINISH_MATERIALS_TABLE_V1", READER, r["id"], host, TILE_BED, SAND, PROCUREMENT,
                         v1["sand_m3_low"], v1["sand_m3_high"], trade=TILE_BED))
        states[r["pair_m2_line"]] = (NA, TILE_BED, f"measure-pair m2 partner of {r['id']} (R-T420-1)")
    for h in t["hosts"]:
        if h["state"] == "MISSING_BED_LINE":
            ln = by_id[h["finish_line"]]
            widest = max(V1.OWNER_VALUES["bed_m"][V1.DRY_FLOOR][1], V1.OWNER_VALUES["bed_m"][V1.WET_FLOOR][1])
            per = V1.OWNER_VALUES["per_m3_of_mortar"]["1:4"]
            hi_m3 = (ln["held_high"] or 0.0) * widest
            missing.append({"host": h["finish_line"], "element_id": h["element_id"],
                            "area_held_m2": [ln["held_low"], ln["held_high"]],
                            "widest_band_m": widest, "effect_bags_at_most": _r(hi_m3 * per["cement_bags_50kg"]),
                            "effect_sand_m3_at_most": _r(hi_m3 * per["sand_m3_loose"]), "why": h["why"]})
            states[h["finish_line"]] = (HELD, TILE_BED, "MISSING_BED_LINE: " + h["why"])
    # line-level guard: the bed lines on V3.0.56 carry exactly the ranges T-500 bound
    for ln in lines:
        if ln["item_code"] in ("FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET") and ln["unit"] == "m2" \
                and ln["line_id"] not in states:
            states[ln["line_id"]] = (HELD, TILE_BED, "bed m2 line with no T-500 pair row")
    return rows, states, missing


def other_hosts(lines, pins=True):
    """Hosts no merged table produces: NO_PRODUCER HELD (stone beds, screeds, outdoor) or NOT_APPLICABLE when the
    candidate EXCLUDES the line / it is the lm partner. T-495 outdoor options: OPTION rows (never summed). The
    released outdoor porcelain walk: HELD, with the T-495 basis figure BESIDE for the wiring row."""
    o = _load(T495, pins)
    rows, states, beside = [], {}, []
    per = V1.OWNER_VALUES["per_m3_of_mortar"]["1:4"]
    for fr in o["finish_held_rows"]:
        for op in fr["options"]:
            bed = op.get("bed")
            if not bed:
                continue
            for m, k in ((CEMENT, "cement_bags_50kg"), (SAND, "sand_m3_loose")):
                rows.append(prow("T-495", OPTION, fr["id"], fr["id"], f"OUTDOOR_BED@{op['finish']}", m, PROCUREMENT,
                                 bed[k]["low"], bed[k]["high"], trade=OUTDOOR_BED,
                                 reason="option bound (finish not decided, OD-1): never summed"))
    for ln in lines:
        kind, trade, why = CODE_TABLE.get(ln["item_code"], ("?", None, None))
        if kind != "HOST" or trade not in (STONE_BED, SCREED, OUTDOOR_BED):
            continue
        if ln["class"] == "EXCLUDED":
            states[ln["line_id"]] = (NA, trade, "line EXCLUDED in the candidate")
        elif ln["unit"] == "lm":
            states[ln["line_id"]] = (NA, trade, "lm partner of the same element's m2 line")
        elif ln["unit"] == "m2" and ln["item_code"] in ("WP.FOUNDATION.FOOTING_SCREED",
                                                         "WP.FOUNDATION.LIFT_PIT_SCREED"):
            states[ln["line_id"]] = (NA, trade, "m2 partner of the same screed's m3 line")
        else:
            reason = ("FINISH_NOT_DECIDED (T-495 options beside)" if ln["item_code"] == "EXT.FLOOR.OUTDOOR"
                      else "NO_PRODUCER: " + why)
            states[ln["line_id"]] = (HELD, trade, reason)
            if ln["item_code"] == "EXT.FLOOR.PORCELAIN" and ln["measured_net"] is not None:
                lo, hi = V1.OWNER_VALUES["bed_m"][V1.DRY_FLOOR]
                a = ln["measured_net"]
                beside.append({"line_id": ln["line_id"], "element_id": ln["element_id"], "area_m2": a,
                               "basis": "T-495 basis (Q-45 B regular floor 0.03 .. 0.04 m, 1:4 = 8 bags + 1.1 m3 "
                                        "per m3), installed, no waste: BESIDE, not a producer",
                               "m3": [_r(a * lo), _r(a * hi)],
                               "cement_bags": [_r(a * lo * per["cement_bags_50kg"]), _r(a * hi * per["cement_bags_50kg"])],
                               "sand_m3": [_r(a * lo * per["sand_m3_loose"]), _r(a * hi * per["sand_m3_loose"])]})
            if ln["item_code"] in ("WP.FOUNDATION.FOOTING_SCREED", "WP.FOUNDATION.LIFT_PIT_SCREED") \
                    and ln["class"] == "RELEASED":
                beside.append({"line_id": ln["line_id"], "element_id": ln["element_id"],
                               "installed_m3_released": ln["measured_net"],
                               "basis": "released screed m3 with no printed mix: cement / sand HELD (no 1:n invented)"})
    return rows, states, beside


def adhesive_has_no_cement_key(pins=True):
    """T-455 (tile adhesive / boxes) carries no cement or sand key: adhesive is a bagged product of its own."""
    s = json.dumps(_load(T455, pins))
    return ("cement" not in s) and ("sand_m3" not in s)


def build(pins=True):
    lines, ident = candidate(pins)
    m_rows, m_states = masonry_rows(lines, pins)
    p_rows, p_states = plaster_rows(lines, pins)
    b_rows, b_states, missing = bed_rows(lines, pins)
    o_rows, o_states, beside = other_hosts(lines, pins)
    rows = m_rows + p_rows + b_rows + o_rows
    states = {}
    for st in (m_states, p_states, b_states, o_states):
        for k, v in st.items():
            states[k] = v
    produced_lines = {r["line_id"] for r in rows if r["role"] == PRODUCER}
    for k in list(states):
        if k in produced_lines:
            del states[k]
    c = census(lines, rows, states)
    if not adhesive_has_no_cement_key(pins):
        c["fails"].append({"kind": "TWO_PRODUCERS", "where": "T-455", "why": "adhesive ledger carries a cement key"})
    # owner arithmetic re-derived on every fresh figure (R-T496-6 style): bed = m3 x 8 / x 1.1; waste 5 %
    for r in b_rows:
        if r["role"] == PRODUCER and r["stage"] == PROCUREMENT and r["low"] is not None:
            inst = next(x for x in b_rows if x["role"] == PRODUCER and x["line_id"] == r["line_id"]
                        and x["material"] == r["material"] and x["stage"] == INSTALLED)
            for e in ("low", "high"):
                if abs(inst[e] * 1.05 - r[e]) > 2e-6:
                    c["fails"].append({"kind": "ARITHMETIC", "where": r["line_id"],
                                       "why": f"{r['material']} procurement {r[e]} != installed {inst[e]} x 1.05"})
    by_code = {}
    for ln in lines:
        k = CODE_TABLE.get(ln["item_code"], ("UNCLASSIFIED",))[0]
        by_code.setdefault(k, set()).add(ln["item_code"])
    host_lines = [ln for ln in lines if CODE_TABLE.get(ln["item_code"], ("?",))[0] == "HOST"]
    tally = {}
    for (lid, m), st in c["states"].items():
        if m == CEMENT:
            tally[st] = tally.get(st, 0) + 1
    keyset = {}
    for r in rows:
        keyset.setdefault((r["host"], r["layer"], r["material"], r["stage"]), set()).add(r["table"])
    return {
        "schema": SCHEMA, "guard_class": GUARD_CLASS, "candidate": CANDIDATE, "candidate_sha8": CANDIDATE_SHA8,
        "base": BASE, "identity": ident,
        "input_sha256": {Path(p).relative_to(ROOT).as_posix(): h for p, h in PINS.items()},
        "rules": ["R-T511-%d" % i for i in range(1, 7)],
        "code_classes": {k: sorted(v) for k, v in sorted(by_code.items())},
        "host_lines": len(host_lines), "host_states_cement": dict(sorted(tally.items())),
        "keys": len(keyset), "keys_bound_by_two_tables": sum(1 for v in keyset.values() if len(v) > 1),
        "keys_with_two_producers": sum(1 for f in c["fails"] if f["kind"] == "TWO_PRODUCERS"),
        "reader_divergences": sum(1 for f in c["fails"] if f["kind"] == "READER_DIVERGENCE"),
        "stale": c["stale"], "missing_bed": missing, "beside": beside,
        "held_contributors": sorted({(x["trade"], x["line_id"], x["reason"]) for x in c["contributors"]
                                     if x["role"] == PRODUCER and x["low"] is None and x["stage"] == INSTALLED
                                     and x["material"] == CEMENT}),
        "subtotals": c["subtotals"], "fails": c["fails"],
        "rows": sorted(rows, key=lambda r: (r["trade"] or "", r["line_id"], r["layer"], r["material"], r["stage"],
                                            r["role"], r["table"])),
        "states": sorted([[lid, m, st] for (lid, m), st in c["states"].items()]),
        "released_quantities_changed": 0,
    }


CSV_COLS = ("trade", "table", "role", "line_id", "host", "layer", "material", "stage", "unit", "low", "high",
            "status", "reason")


def write(m, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "CEMENT_SAND_CENSUS_T511.json").write_text(
        json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False, default=list) + "\n", encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in m["rows"]:
        w.writerow(["" if r.get(k) is None else r.get(k) for k in CSV_COLS])
    (out_dir / "CEMENT_SAND_CENSUS_T511.csv").write_text(buf.getvalue(), encoding="utf-8")


def main(argv):
    m = build()
    if argv and argv[0] == "--check":
        for f in m["fails"]:
            print("FAIL", f["kind"], f["where"], f["why"])
        print(f"fails {len(m['fails'])}; keys {m['keys']}; two producers {m['keys_with_two_producers']}; "
              f"reader divergences {m['reader_divergences']}; stale {len(m['stale'])}")
        return 1 if m["fails"] else 0
    write(m, Path(argv[0]) if argv else HERE / "out")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
