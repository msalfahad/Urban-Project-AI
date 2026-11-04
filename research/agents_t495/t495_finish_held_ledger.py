"""T-495: TILE PURCHASE LEDGER V2 = the T-455 ledger (URBAN_T455_TILE_PURCHASE_V1, kept byte-identical) + the
FINISH-HELD OUTDOOR FLOOR rows + a SCOPE GUARD, beside the candidate, NOT in it (no candidate, released or registry
quantity changes; FINISH_MATERIALS_TABLE_V4 is read, never edited).

Physical element. An outdoor floor surface whose AREA is measured (the candidate carries it as a HELD range because the
FINISH is not decided) but whose finish product is one of several the sources allow. What is bought for it depends on
the finish: porcelain / ceramic = a 1:4 cement-sand bed + 20 kg adhesive bags + tiles; marble / stone = the bed + a stone
adhesive whose coverage is not given; timber decking / interlock pavers = no owner material rule at all. So the purchase
is not one number: it is one figure PER FINISH OPTION, every option HELD until the finish is decided, with its bound.

Rules (project-independent):
  R-T495-1 SCOPE    every candidate FLOOR-SURFACE line (item code FIN.FLOOR.* other than the beds FIN.FLOOR.BED.*,
           EXT.FLOOR.*, EXT.PAVING.*) is IN the tile ledger (T-455 scope or FINISH_HELD_OPTIONS below) or DECLARED OUT
           with its reason (DECLARED_OUT). A code that is neither, or a HELD line of a declared-out code that is not
           listed, fails the guard: a held floor line can no longer fall outside the material bound unseen (F-C-T455-1).
  R-T495-2 OPTIONS  a finish-held line carries ONLY the finish options a source names (owner rule / owner words / the
           open owner question that frames the choice), each with that source; never an option added by the agent, never
           one picked. An option outside {PORCELAIN_CERAMIC, MARBLE_STONE, TIMBER_DECK, INTERLOCK} is refused.
  R-T495-3 BOUND    per option, the owner rules applied at both ends of the line's held area range:
           adhesive (UPC-ADHESIVE-001 via FINISH_MATERIALS_TABLE_V4: porcelain / ceramic area / 5 .. area / 3 bags of
           20 kg, size not given; stone coverage HELD, Q-45), bed (Q-45 B regular floor 0.03 .. 0.04 m, 1:4, 5 % waste,
           8 x 50 kg cement and 1.1 m3 loose sand per m3, PROVISIONAL, via FINISH_MATERIALS_TABLE_V1). Timber and
           interlock: no owner rule -> every material HELD with NO bound (never 0, never a typical figure). A line whose
           held range is open (no low or high) has no bound. Every figure is a BOUND, never a quantity; per option only,
           never summed across options (that would be two finishes on one floor).
  R-T495-4 AREA     the candidate's held range is copied, never re-measured; evidence UNKNOWN unless the line is bound
           VERIFIED_WHOLE (R-T455-2); the rate never upgrades the area.

Input (committed, sha256-pinned; ids, codes, units, classes and areas only, no drawing content):
  research/agents_t485/out/LINE_INDEX_V3_0_46.json. The candidate of record V3.0.47 (T-443) changed FIN.SKIRTING only
  (4865 of 4874 lines byte-identical, T-443 report), so every floor-surface line below is the V3.0.47 line.

    python3 -I research/agents_t495/t495_finish_held_ledger.py [OUT_DIR]     # writes the ledger (default: ./out)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t455"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import finish_materials_table as V1  # noqa: E402
from engine.source import finish_materials_table_v4 as V4  # noqa: E402
import t455_tile_purchase as L455  # noqa: E402

SCHEMA = "URBAN_TILE_PURCHASE_LEDGER_V2"
SUPERSEDES = L455.SCHEMA
CANDIDATE = "ARCH_TAKEOFF_V3.0.47 (floor-surface lines identical to V3.0.46, T-443 changed FIN.SKIRTING only)"
LINE_INDEX = ROOT / "research/agents_t485/out/LINE_INDEX_V3_0_46.json"
PIN = "d9e0a7e46b2e17a1cef78d8630cf2b1f6c2aa8bbe5dbe0f29037e6f1e54f2dd0"

PORCELAIN, MARBLE, TIMBER, INTERLOCK = V4.PORCELAIN_CERAMIC, V4.MARBLE_STONE, "TIMBER_DECK", "INTERLOCK"
OPTION_FINISHES = (PORCELAIN, MARBLE, TIMBER, INTERLOCK)

FLOOR_SURFACE = re.compile(r"^(FIN\.FLOOR\.(?!BED\.)|EXT\.FLOOR\.|EXT\.PAVING\.)")
DECLARED_OUT = {
    "EXT.PAVING.INTERLOCK": "finish decided (interlock, owner 2026-10-21 23:20) but no owner material rule for pavers "
                            "or their sand bed: no adhesive / box row exists to bound (named, not silently dropped)",
}
OPTIONS_SOURCE_RULE = "OWNER_RULE_OUTDOOR_FLOORS_2026-10-21"
# item code -> {element_id suffix -> (options, source, options_status)}; element ids are the candidate's own.
FINISH_HELD_OPTIONS = {
    "EXT.FLOOR.OUTDOOR": {
        "COURT#PORCH": ((TIMBER, PORCELAIN, MARBLE),
                        f"{OPTIONS_SOURCE_RULE} additions 20:45 (owner: 'it could be wood or ceramic or marble with the "
                        f"stairs') and 23:20 (porch at court level, 'measure the area and can decide later for the kind')",
                        "OWNER-STATED OPTIONS"),
        "COURT#POOL-DECK": ((INTERLOCK, PORCELAIN),
                            f"{OPTIONS_SOURCE_RULE} OD-1 (open owner question: 'interlock like the court, or ceramic "
                            f"like house side / front areas?'); owner 20:45 'pool deck not sure yet'",
                            "OPTIONS FROM THE OPEN OWNER QUESTION OD-1 (owner has not limited them; a finish named "
                            "later outside this list is a new row, never folded in)"),
    },
}


class LedgerError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def load(path=None):
    p = Path(path) if path else LINE_INDEX
    raw = p.read_bytes()
    if path is None and hashlib.sha256(raw).hexdigest() != PIN:
        raise LedgerError(f"{p.relative_to(ROOT)}: sha256 is not the pinned {PIN[:8]}")
    return json.loads(raw.decode("utf-8"))


def _options_for(item_code, element_id, options_map):
    for suffix, spec in (options_map.get(item_code) or {}).items():
        if element_id == suffix or element_id.endswith("-" + suffix) or element_id.endswith(":" + suffix):
            return spec
    return None


def _num(v):
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
        return None
    return float(v)


def _adhesive(finish, area):
    """UPC-ADHESIVE-001 through FINISH_MATERIALS_TABLE_V4 for one area, size not given -> (low, high) or HELD reason."""
    if finish not in (PORCELAIN, MARBLE):
        return None, f"NO_OWNER_ADHESIVE_RULE for {finish} (UPC-ADHESIVE-001 / Q-45 price porcelain / ceramic only)"
    r = V4.purchase_from_lines([{"id": "x", "area_m2": area, "kind": V4.DRY_FLOOR, "finish": finish}])["rows"][0]
    b = r.get("adhesive_bound_bags")
    if b is None:
        return None, r["adhesive_reason"]
    return (b["low"], b["high"]), None


def _bed(finish, area):
    """Q-45 B regular-floor bed through FINISH_MATERIALS_TABLE_V1 -> dict of (low, high) or HELD reason."""
    if finish not in (PORCELAIN, MARBLE):
        return None, f"NO_OWNER_BED_RULE for {finish} (Q-45 gives a cement-sand bed under tiles and stone only)"
    m = V1.materials(V1.DRY_FLOOR, finish, area)
    if m["mortar_m3_low"] is None:
        return None, m["mortar_reason"]
    return {"mortar_m3": (m["mortar_m3_low"], m["mortar_m3_high"]),
            "cement_bags_50kg": (m["cement_bags_low"], m["cement_bags_high"]),
            "sand_m3_loose": (m["sand_m3_low"], m["sand_m3_high"]),
            "bed_m": (m["bed_low_m"], m["bed_high_m"]), "mix": m["mix"]}, None


def option_bound(finish, area_low, area_high):
    """one finish option on a held area range [area_low, area_high]: low end from area_low at the thin / cheap rate, high
    end from area_high at the thick / dear rate. None ends -> no bound (HELD, never 0)."""
    if finish not in OPTION_FINISHES:
        raise LedgerError(f"finish option {finish!r} is not one of {OPTION_FINISHES} (R-T495-2)")
    out = {"finish": finish, "status": "HELD", "reason": "FINISH_NOT_DECIDED (the owner chooses among the options)",
           "adhesive_bags_20kg": None, "adhesive_reason": None, "bed": None, "bed_reason": None}
    lo, hi = _num(area_low), _num(area_high)
    if lo is None or hi is None or hi < lo or hi == 0:
        out["adhesive_reason"] = out["bed_reason"] = "AREA_RANGE_OPEN (no measured low / high): no bound"
        return out
    a_lo, why = _adhesive(finish, lo)
    if a_lo is None:
        out["adhesive_reason"] = why
    else:
        a_hi, _ = _adhesive(finish, hi)
        out["adhesive_bags_20kg"] = {"low": a_lo[0], "high": a_hi[1],
                                     "basis": "area_low / 5 .. area_high / 3 (tile size not given): a BOUND"}
    b_lo, why = _bed(finish, lo)
    if b_lo is None:
        out["bed_reason"] = why
    else:
        b_hi, _ = _bed(finish, hi)
        out["bed"] = {k: {"low": b_lo[k][0], "high": b_hi[k][1]} for k in ("mortar_m3", "cement_bags_50kg",
                                                                           "sand_m3_loose")}
        out["bed"].update(bed_m=b_lo["bed_m"], mix=b_lo["mix"], status="PROVISIONAL (Q-45 B)",
                          basis="Q-45 B regular floor, area_low x 0.03 .. area_high x 0.04, +5 % waste: a BOUND")
    return out


def finish_held_rows(d, options_map=FINISH_HELD_OPTIONS):
    rows = []
    for ln in d["lines"]:
        if ln["item_code"] not in options_map or ln["class"] == "EXCLUDED":
            continue
        if ln["unit"] != "m2":
            raise LedgerError(f"{ln['line_id']}: unit {ln['unit']!r} is not m2")
        if ln["class"] != "HELD" and ln.get("measured_net") is not None:
            raise LedgerError(f"{ln['line_id']}: a finish-held row must be HELD in the candidate (finish undecided), "
                              f"got {ln['class']} {ln['measured_net']}")
        spec = _options_for(ln["item_code"], ln["element_id"], options_map)
        if spec is None:
            raise LedgerError(f"{ln['line_id']} ({ln['element_id']}): no sourced finish options (R-T495-2); a held "
                              f"outdoor floor is never given options by the agent")
        opts, src, ostat = spec
        b = ln.get("binding") or {}
        rows.append({"id": ln["line_id"], "item_code": ln["item_code"], "element_id": ln["element_id"],
                     "floor": L455._floor(ln["element_id"]), "area_m2": None,
                     "area_held_low_m2": ln.get("held_low"), "area_held_high_m2": ln.get("held_high"),
                     "area_reason": "candidate line HELD: FINISH not decided (area carried as its held range)",
                     "evidence_status": "VERIFIED" if b.get("binding") == "VERIFIED_WHOLE" else "UNKNOWN",
                     "options_source": src, "options_status": ostat,
                     "options": [option_bound(f, ln.get("held_low"), ln.get("held_high")) for f in opts],
                     "status": "HELD", "tile_product": None,
                     "boxes_reason": "finish, tile size, product and packaging not established: boxes HELD"})
    return rows


def scope_guard(d, options_map=FINISH_HELD_OPTIONS, declared_out=DECLARED_OUT):
    """R-T495-1: every floor-surface line is in the ledger or declared out. Returns the census; raises on a gap."""
    in_scope = set(L455.SCOPE) | set(options_map)
    census, gaps = {}, []
    for ln in d["lines"]:
        code = ln["item_code"]
        if not FLOOR_SURFACE.match(code):
            continue
        c = census.setdefault(code, {"lines": 0, "held": 0, "where": None})
        c["lines"] += 1
        c["held"] += ln["class"] == "HELD"
        if code in in_scope:
            c["where"] = "T-455 SCOPE" if code in L455.SCOPE else "FINISH_HELD_OPTIONS"
        elif code in declared_out:
            c["where"] = "DECLARED_OUT: " + declared_out[code]
            if ln["class"] == "HELD":
                gaps.append(f"{ln['line_id']} {code}: HELD line of a declared-out code (its bound is named nowhere)")
        else:
            gaps.append(f"{ln['line_id']} {code}: floor-surface code outside the ledger scope and not declared out")
    if gaps:
        raise LedgerError("SCOPE_GAP (R-T495-1): " + "; ".join(sorted(set(gaps))))
    return census


def build(line_index=None, options_map=None):
    d = load(line_index)
    opts = FINISH_HELD_OPTIONS if options_map is None else options_map
    census = scope_guard(d, opts)
    base = L455.build(LINE_INDEX if line_index is None else line_index)
    rows = finish_held_rows(d, opts)
    per_option = {}
    for r in rows:
        for o in r["options"]:
            s = per_option.setdefault(o["finish"], {"lines": [], "adhesive_low": 0.0, "adhesive_high": 0.0,
                                                    "adhesive_unbounded_lines": [], "bed_unbounded_lines": [],
                                                    "mortar_m3_low": 0.0, "mortar_m3_high": 0.0})
            s["lines"].append(r["id"])
            if o["adhesive_bags_20kg"]:
                s["adhesive_low"] += o["adhesive_bags_20kg"]["low"]
                s["adhesive_high"] += o["adhesive_bags_20kg"]["high"]
            else:
                s["adhesive_unbounded_lines"].append(r["id"])
            if o["bed"]:
                s["mortar_m3_low"] += o["bed"]["mortar_m3"]["low"]
                s["mortar_m3_high"] += o["bed"]["mortar_m3"]["high"]
            else:
                s["bed_unbounded_lines"].append(r["id"])
    for s in per_option.values():
        for k in ("adhesive_low", "adhesive_high", "mortar_m3_low", "mortar_m3_high"):
            unb = s["adhesive_unbounded_lines" if k.startswith("adhesive") else "bed_unbounded_lines"]
            # an option with an unbounded line has NO option bound (a partial sum is never printed as the bound)
            s[k] = None if unb else _r(s[k])
        s["note"] = ("IF every listed line took this finish; a line without this option is not in 'lines'; never "
                     "summed across options")
    return {"schema": SCHEMA, "supersedes": SUPERSEDES, "candidate": CANDIDATE, "input_sha256": PIN,
            "t455_ledger_on_this_input": {"by_item_code": base["by_item_code"],
                                          "adhesive": base["purchase"]["adhesive"],
                                          "excluded_lines": base["excluded_lines"]},
            "finish_held_rows": rows, "finish_held_by_option": per_option,
            "scope_census": census, "released_quantities_changed": 0}


def write(out_dir=None):
    out = Path(out_dir) if out_dir else HERE / "out"
    out.mkdir(parents=True, exist_ok=True)
    led = build()
    (out / "TILE_PURCHASE_LEDGER_V2.json").write_text(
        json.dumps(led, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(("id", "item_code", "area_low_m2", "area_high_m2", "option", "adhesive_low", "adhesive_high",
                "adhesive_reason", "mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high",
                "sand_m3_low", "sand_m3_high", "bed_reason", "status"))
    for r in led["finish_held_rows"]:
        for o in r["options"]:
            a, b = o["adhesive_bags_20kg"] or {}, o["bed"] or {}
            g = lambda k, e: (b.get(k) or {}).get(e)  # noqa: E731
            w.writerow((r["id"], r["item_code"], r["area_held_low_m2"], r["area_held_high_m2"], o["finish"],
                        a.get("low"), a.get("high"), o["adhesive_reason"], g("mortar_m3", "low"),
                        g("mortar_m3", "high"), g("cement_bags_50kg", "low"), g("cement_bags_50kg", "high"),
                        g("sand_m3_loose", "low"), g("sand_m3_loose", "high"), o["bed_reason"], o["status"]))
    (out / "TILE_PURCHASE_LEDGER_V2.csv").write_text(buf.getvalue(), encoding="utf-8")
    return led


if __name__ == "__main__":
    led = write(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"by_option": led["finish_held_by_option"], "census": led["scope_census"]}, indent=1))
