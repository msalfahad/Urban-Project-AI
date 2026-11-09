"""T-540: SAND LOAD SIZE and BULK DENSITY for the sand procurement of T-535 (loose m3). Research reader, not wired: no
candidate, engine, rule, knowledge, registry or producer file changes; T-535 is read, never edited; no candidate or
released (V2.9 + route G) line moves.

Physical element (ERS s.2.1). Washed building sand as the supplier delivers it: a LOOSE, MOIST, UNCOMPACTED heap in a
lorry body. Its mass per loose m3 depends on two states that change BOTH mass and volume: the moisture content (water
adds mass and, at low moisture, bulks the loose volume) and the compaction (a rodded / compacted volume holds more
grains than a loose one). The owner rates (Q-45 B / Q-53 C / Q-78 A) give 'm3 of LOOSE sand per m3 of mortar' for
purchasing (Q-45 request: 'how many cement and sand I need'), i.e. the volume as bought. So the volume that a density
multiplies is LOOSE_AS_BOUGHT; a density measured in another state (oven-dry, rodded / compacted, particle density,
loose-dry) is a different physical quantity and is never applied to it (no hidden bulking correction).

Evidence searched (s.2.2, resolution order of AGENT_BRIEF; full census in SOURCE_CENSUS; nothing borrowed):
  owner rules          OWNER_QUESTIONS_ANSWERED (Q-45 / Q-53 / Q-78), AGENT_BRIEF table: unit loose m3; no load size,
                       no tonne, no density.
  supplier             CLARIFICATIONS_SUPPLIER_2026-10-23 rows 2-3: sand only as HELD.
  skill                quantity-takeoff-rules (supplier data): blocks, AAC pallets, lintels, glue, cement 1440 kg/m3;
                       a block 'delivery' line per trip; NO sand load size, NO sand density.
  Drive references     MPW general specification 1990 (01, text read covers divisions 1-2 only, earthworks / paving:
                       soil compaction densities, no building-sand density); KSE 'bait al-omr' 2023 (01): no sand
                       data; 'supervisor's eye' (02, readable part): no sand quantity data; SBC summary 2021 (04):
                       Table 3-D-1 unit weights list concrete, RC, solid brick, sand-lime brick and wet clay, NOT
                       building sand; IBC / IPC / ACI files (03): no sand bulk density table; 'finishes' and
                       'mistakes' books (02): scanned, over the download limit, unreadable; QCS 2014 (04): over the
                       download limit, not text-searchable for this.
  => LOAD SIZE HELD 'SAND_LOAD_SIZE_NOT_SOURCED'; BULK DENSITY HELD 'SAND_BULK_DENSITY_NOT_SOURCED'. No invented, typical
     or borrowed value; tonnes and loads stay HELD, the m3 stays printed (never replaced, never 0). A book value, if
     one is found later, is ESTIMATED with its citation (REFERENCE_SOURCES: a book is evidence, not an Urban rule).

Rules (every villa; PROPOSED for the Lead / Checker):
  R-T540-1 STATE     a tonne figure = loose m3 x a SOURCED bulk density measured in the SAME state as the m3
           (LOOSE_AS_BOUGHT); any other state (LOOSE_DRY, COMPACTED_DRY, OVEN_DRY_PARTICLE, ...) is refused, never
           converted by an unsourced bulking factor. A density range gives a tonne range end to end (low x low,
           high x high).
  R-T540-2 LOAD UNIT a load size is used in its own unit: m3 loads only from a load stated in the same loose state;
           a load stated in tonnes needs R-T540-1 first (no density -> loads HELD even with a sourced load).
  R-T540-3 GROUP     loads are one ceiling per COMPLETE villa group (R-T535-1 / R-T535-3); an AT_LEAST group gives
           tonnes AT_LEAST and loads HELD; no m3 -> everything HELD, never 0.
  R-T540-4 BESIDE    tonnes and loads are printed beside the loose m3, which stays the owner unit (R-T535-1).

Rebuild: `python3 -I research/agents_t540/t540_sand_load_density.py` writes out/SAND_LOAD_DENSITY_T540.json;
`--check` exits 1 when the rebuild differs from the committed file or any failure is found.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "SAND_LOAD_DENSITY_T540.json"
T535_JSON = ROOT / "research/agents_t535/out/SAND_PROCUREMENT_T535.json"
PINNED = (T535_JSON,)

SCHEMA = "URBAN_T540_SAND_LOAD_DENSITY_V1"
HELD, COMPUTED, AT_LEAST = "HELD", "COMPUTED", "AT_LEAST"
LOAD_HELD = "SAND_LOAD_SIZE_NOT_SOURCED"
DENSITY_HELD = "SAND_BULK_DENSITY_NOT_SOURCED"

# The state of the owner m3 (Q-45 request: a purchasing quantity; Q-45 B / Q-53 C / Q-78 A: 'loose sand').
OWNER_STATE = "LOOSE_AS_BOUGHT"
STATES = ("LOOSE_AS_BOUGHT", "LOOSE_DRY", "COMPACTED_DRY", "COMPACTED_MOIST", "OVEN_DRY_PARTICLE")

# One record per datum; value None where no source was found (T-540 census 2026-11-05).
DENSITY_RECORD = {"value_t_per_m3": None, "state": None, "source": None, "status": f"HELD: {DENSITY_HELD}"}
LOAD_RECORD = {"size": None, "unit": None, "state": None, "source": None, "status": f"HELD: {LOAD_HELD}"}

SOURCE_CENSUS = [
    {"source": "OWNER_QUESTIONS_ANSWERED Q-45 / Q-53 / Q-78; AGENT_BRIEF OWNER CONFIRMED table",
     "load_size": "none", "bulk_density": "none", "note": "unit = m3 of loose sand (purchasing quantity)"},
    {"source": "CLARIFICATIONS_SUPPLIER_2026-10-23 rows 2-3", "load_size": "none", "bulk_density": "none",
     "note": "sand listed only as HELD"},
    {"source": "skill quantity-takeoff-rules (supplier price / pallet data, 2025)", "load_size": "none",
     "bulk_density": "none", "note": "cement 1440 kg/m3 and block delivery per trip only; nothing for sand"},
    {"source": "Drive 'Engineering Sources' / 01 Kuwait References / MPW general specification 1990",
     "load_size": "none", "bulk_density": "none in the readable part",
     "note": "text read stops in division 2 (earthworks, paving: soil compaction to maximum dry density); the "
             "masonry / plaster divisions are past the readable range and the file is over the download limit"},
    {"source": "Drive 01 Kuwait References / KSE 'bait al-omr' 2023", "load_size": "none", "bulk_density": "none",
     "note": "owner guide and contract templates; sand only as a pool filter"},
    {"source": "Drive 02 Construction Books / 'supervisor's eye'", "load_size": "none", "bulk_density": "none",
     "note": "readable text part has no sand quantity data"},
    {"source": "Drive 02 Construction Books / 'finishes' and 'mistakes in construction'", "load_size": "unreadable",
     "bulk_density": "unreadable", "note": "scanned, over the download limit (REFERENCE_SOURCES)"},
    {"source": "Drive 04 Regional Codes / Saudi code summary 2021 (SBC 1101 Table 3-D-1)", "load_size": "none",
     "bulk_density": "none for sand",
     "note": "unit weights for plain / reinforced concrete, solid brick, sand-lime brick, wet clay only"},
    {"source": "Drive 04 Regional Codes / QCS 2014", "load_size": "not searched in text",
     "bulk_density": "not searched in text", "note": "86 MB, over the download limit; no text hit for the terms"},
    {"source": "Drive 03 International Codes (IBC 2009 / 2018 / 2021, IPC 2006, ACI 318)", "load_size": "none",
     "bulk_density": "none", "note": "full-text search hits are front matter only; no material weight table"},
    {"source": "engine FINISH V6:91 / T-523 GROUPS / T-535 SAND_RECORD", "load_size": "HELD", "bulk_density": "HELD",
     "note": "agree with the census"},
]

RULES = {
    "R-T540-1": "tonnes = loose m3 x a SOURCED bulk density in the SAME state as the m3 (LOOSE_AS_BOUGHT); another "
                "state is refused (no unsourced bulking factor); a range converts end to end.",
    "R-T540-2": "a load size is used in its own unit: m3 loads only from a load in the same loose state; a tonne "
                "load needs R-T540-1 first.",
    "R-T540-3": "loads = one ceiling per COMPLETE villa group; AT_LEAST group -> tonnes AT_LEAST, loads HELD; no m3 "
                "-> HELD, never 0.",
    "R-T540-4": "tonnes and loads beside the loose m3; the m3 stays the owner unit (R-T535-1).",
}


class DensityError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _ceil(x):
    return int(math.ceil(round(x, 9)))


def _num(v):
    return (not isinstance(v, bool)) and isinstance(v, (int, float)) and math.isfinite(v)


def _range(v, what):
    """A positive value or (low, high) range; returns (low, high)."""
    if _num(v):
        v = (v, v)
    if not isinstance(v, (tuple, list)) or len(v) != 2 or not all(_num(x) and x > 0 for x in v) or v[0] > v[1]:
        raise DensityError(f"BAD_VALUE: {what} {v!r} (a positive value or an ordered positive range)")
    return (float(v[0]), float(v[1]))


def check_density(rec):
    """Returns (low, high) t/m3 or None (HELD). A figure needs a source and a state equal to the m3 state."""
    v = rec.get("value_t_per_m3")
    if v is None:
        return None
    d = _range(v, "density")
    if not rec.get("source"):
        raise DensityError(f"DENSITY_UNSOURCED: {v!r} (a bulk density needs its citation)")
    st = rec.get("state")
    if st not in STATES:
        raise DensityError(f"DENSITY_STATE_UNKNOWN: {st!r} (moisture / compaction state must be named)")
    if st != OWNER_STATE:
        raise DensityError(f"DENSITY_STATE_MISMATCH: {st} density on {OWNER_STATE} m3 (R-T540-1: never mixed, no "
                           "unsourced bulking factor)")
    return d


def check_load(rec):
    """Returns (size, unit) or None (HELD)."""
    v = rec.get("size")
    if v is None:
        return None
    if not _num(v) or v <= 0:
        raise DensityError(f"BAD_VALUE: load {v!r}")
    if not rec.get("source"):
        raise DensityError(f"LOAD_UNSOURCED: {v!r} (a load size needs its citation)")
    u = rec.get("unit")
    if u not in ("m3", "t"):
        raise DensityError(f"LOAD_UNIT_UNKNOWN: {u!r} (m3 or t)")
    if u == "m3" and rec.get("state") != OWNER_STATE:
        raise DensityError(f"LOAD_STATE_MISMATCH: {rec.get('state')} m3 load on {OWNER_STATE} m3 (R-T540-2)")
    return (float(v), u)


def convert(group_id, villa, m3, status, density=DENSITY_RECORD, load=LOAD_RECORD, purchasing_group=True):
    """R-T540-1..4 on one villa group. m3 = (low, high) loose m3 or None; status COMPUTED (complete group) or
    AT_LEAST (known part of an open group). purchasing_group False = a trade subtotal: tonnes only, never its own
    load ceiling (R-T535-3 / R-T540-3)."""
    if status not in (COMPUTED, AT_LEAST):
        raise DensityError(f"BAD_STATUS: {status!r}")
    d, ld = check_density(density), check_load(load)
    base = None if m3 is None else _range(m3, "m3")
    out = {"group": group_id, "villa": villa, "unit": "m3 loose (owner unit, R-T540-4)",
           "m3": None if base is None else [_r(base[0]), _r(base[1])], "m3_status": status if base else HELD}
    if base is None:
        out.update(t=None, t_status="HELD: no m3 (never 0)", loads=None, loads_status="HELD: no m3 (never 0)")
        return out
    if d is None:
        t = None
        out.update(t=None, t_status=f"HELD: {DENSITY_HELD}")
    else:
        t = (base[0] * d[0], base[1] * d[1])
        out.update(t=[_r(t[0]), _r(t[1])], t_status=status,
                   t_arithmetic=f"{_r(base[0])} x {d[0]:g} .. {_r(base[1])} x {d[1]:g} t/m3 ({density['source']})")
    if not purchasing_group:
        out.update(loads=None, loads_status="NOT A PURCHASING GROUP: loads only on the villa group (R-T540-3)")
    elif ld is None:
        out.update(loads=None, loads_status=f"HELD: {LOAD_HELD}")
    elif status != COMPUTED:
        out.update(loads=None, loads_status="HELD: group AT_LEAST (open members; one ceiling per complete group)")
    elif ld[1] == "m3":
        n = [_ceil(base[0] / ld[0]), _ceil(base[1] / ld[0])]
        out.update(loads=n, loads_status=f"COMPUTED: ceil(m3 / {ld[0]:g} m3), one ceiling per villa group",
                   delivered_m3=[_r(n[0] * ld[0]), _r(n[1] * ld[0])])
    elif t is None:
        out.update(loads=None, loads_status=f"HELD: tonne load needs a density ({DENSITY_HELD})")
    else:
        n = [_ceil(t[0] / ld[0]), _ceil(t[1] / ld[0])]
        out.update(loads=n, loads_status=f"COMPUTED: ceil(t / {ld[0]:g} t), one ceiling per villa group",
                   delivered_t=[_r(n[0] * ld[0]), _r(n[1] * ld[0])])
    return out


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run():
    s = json.loads(T535_JSON.read_text())
    fails = []
    g = s["group"]

    def _base(x):
        if x.get("procurement_m3"):
            return x["procurement_m3"], COMPUTED
        return x.get("procurement_at_least_m3"), AT_LEAST

    m3, st = _base(g)
    group = convert(g["group"], g["villa"], m3, st)
    trades = {k: convert(k, v["villa"], *_base(v), purchasing_group=False) for k, v in sorted(s["trades"].items())}
    # the m3 is restated unchanged (R-T540-4): a drift from T-535 is a failure, never hidden
    for k, v in [("SAND_LOOSE", group)] + sorted(trades.items()):
        src = g if k == "SAND_LOOSE" else s["trades"][k]
        exp, _ = _base(src)
        if (exp or None) != (v["m3"] or None):
            fails.append({"kind": "M3_DRIFT", "where": k, "why": f"{v['m3']} vs T-535 {exp}"})
    return {
        "schema": SCHEMA, "density_record": DENSITY_RECORD, "load_record": LOAD_RECORD, "owner_state": OWNER_STATE,
        "source_census": SOURCE_CENSUS, "rules": RULES,
        "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in PINNED},
        "group": group, "trades": trades, "failures": fails, "released_quantities_changed": 0,
    }


def _dump(m):
    return json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    m = run()
    for f in m["failures"]:
        print(f"FAIL {f['kind']}: {f['where']}: {f['why']}")
    text = _dump(m)
    if "--check" in argv:
        same = OUT.exists() and OUT.read_text() == text
        print("check:", "identical" if same else "DIFFERS")
        return 0 if same and not m["failures"] else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    g = m["group"]
    print(json.dumps({k: g[k] for k in ("m3", "m3_status", "t_status", "loads_status")}, indent=1))
    return 1 if m["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
