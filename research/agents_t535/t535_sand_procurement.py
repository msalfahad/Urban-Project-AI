"""T-535: SAND PURCHASE UNIT for the merged mortar producers. Research reader, not wired: no candidate, engine, rule,
knowledge, registry or producer file changes; every producer is read, never edited; no candidate or released (V2.9 +
route G) line moves.

Physical element (ERS s.2.1). The sand delivered to site for site-mixed cement : sand layers (block laying mortar, the
block perimeter joint, plaster coats, tile / stone / outdoor beds, screeds), as the supplier sells it. Kept apart:
INSTALLED (theoretical loose sand of the built layer: mortar m3 x the owner rate), LOSS (each named loss, own account),
PROCUREMENT (installed + sourced losses, before any pack rounding), TO-BUY (procurement in the supplier's pack, one
ceiling per villa group) and any CONVERSION (m3 -> tonne needs a bulk density with a source).

Evidence read (s.2.2, levels in order; nothing borrowed):
  owner        Q-45 request (owner's words: 'with sand (m3) and cement bags needed'); Q-45 answer B (accepted: 'about
               8 bags and 1.1 m3 loose sand per m3 of 1:4 mortar'); Q-53 answer C ('sand about 1.00 m3 ... for
               preliminary purchasing'); Q-78 A (1:4, 1.1 m3 loose sand per m3); MISSION 'Cement-based materials'
               ('cement bags, sand m3'). -> the UNIT is the LOOSE CUBIC METRE (OWNER-CONFIRMED unit; the rates stay
               PROVISIONAL / CALCULATED PROVISIONAL with their own labels).
  supplier     CLARIFICATIONS_SUPPLIER_2026-10-23.md rows 2-3 name sand only as HELD; no load, bag, tonne or density.
  references   REFERENCE_SOURCES.md: no sand entry; Drive reference folders (read-only search 2026-11-05): codes and
               the MPW 1990 general specification, no supply unit / load size / bulk density found in the search.
  engine       finish_materials_table_v6.py:91 SAND_PACK 'SAND_PACK_NOT_ESTABLISHED'; T-523 GROUPS['SAND_LOOSE'] pack
               None. Both agree with the evidence above.
  => PACK (load size, minimum order, increment) HELD 'SAND_LOAD_SIZE_NOT_SOURCED'; TONNE conversion HELD
     'SAND_BULK_DENSITY_NOT_SOURCED'; MOISTURE BULKING not applied ('SAND_BULKING_NOT_SOURCED': the owner rates are
     already loose volumes; a bulking factor would be a second, unsourced allowance). No invented value; never 0.

Rules (every villa; PROPOSED for the Lead / Checker; provenance in RULES):
  R-T535-1 SAND UNIT    sand procurement is stated in loose m3 (the unit the owner rates produce), fractional, never
           rounded while the pack is HELD; the to-buy in loads is printed only from a SOURCED pack, one ceiling per
           villa group (R-T523-1), and a tonne figure only from a SOURCED bulk density.
  R-T535-2 STAGE        a producer's 'preliminary purchasing allowance' that is a rounded RATE (Q-53 C: 0.9975 ->
           'about 1.00 m3 per m3') is a separate labelled layer, not a loss and not procurement (FINISH V7 R-T528-1,
           ALLOWANCE_LABEL). Procurement = installed + the sourced losses (V7: the Q-45 5 % named loss).
           Finding F-T535-1: the T-511 / T-523 stair members bind the allowance (1.062939 m3) as PROCUREMENT; on
           V7 it is 1.06028 x 1.05 = 1.113294 m3 (+0.050355 m3); the allowance stays beside.
  R-T535-3 ONE VILLA    members of two villas never share one group or one ceiling (refused).
  R-T535-4 NO SOURCE    a member whose loss exists but has no source contributes its installed to an AT_LEAST known
           part and the group procurement stays HELD (installed kept); a member with no installed is open (never 0).

Rebuild: `python3 -I research/agents_t535/t535_sand_procurement.py` writes out/SAND_PROCUREMENT_T535.json;
`--check` exits 1 when the rebuild differs from the committed file or any failure is found.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "SAND_PROCUREMENT_T535.json"

SCHEMA = "URBAN_T535_SAND_PROCUREMENT_V1"
T523_PY = ROOT / "research/agents_t523/t523_binding_map_v2.py"
T520_SUMMARY = ROOT / "research/agents_t520/out/SUMMARY_T520.json"
V7_PY = ROOT / "engine/source/finish_materials_table_v7.py"
V6_PY = ROOT / "engine/source/finish_materials_table_v6.py"
PINNED = (T523_PY, T520_SUMMARY, V7_PY, V6_PY)

HELD, COMPUTED = "HELD", "COMPUTED"
PACK_HELD = "SAND_LOAD_SIZE_NOT_SOURCED"
DENSITY_HELD = "SAND_BULK_DENSITY_NOT_SOURCED"
BULKING_HELD = "SAND_BULKING_NOT_SOURCED"

# The one sand purchase record (key x unit x pack x conversion x source x status). Values are None where no source.
SAND_RECORD = {
    "key": "SAND_LOOSE",
    "unit": "m3 loose (the volume the owner per-m3 rates give)",
    "unit_status": "OWNER-CONFIRMED unit (rates keep their own labels: Q-45 B / Q-78 PROVISIONAL, Q-53 C CALCULATED "
                   "PROVISIONAL)",
    "unit_source": ["Q-45 request (owner: 'with sand (m3) and cement bags needed') and answer B (1.1 m3 loose sand "
                    "per m3 of 1:4)", "Q-53 C (sand about 1.00 m3 per m3 of 1:3, preliminary purchasing)",
                    "Q-78 A (1:4, 1.1 m3 loose sand per m3)", "MISSION 'Cement-based materials' (cement bags, sand m3)"],
    "pack_m3": None, "pack_status": f"HELD: {PACK_HELD} (no load size, minimum order or increment in the owner rules, "
                                    "supplier clarifications, REFERENCE_SOURCES or the Drive reference folders)",
    "pack_source": None,
    "bulk_density_t_per_m3": None, "density_status": f"HELD: {DENSITY_HELD}", "density_source": None,
    "bulking": f"NOT APPLIED: {BULKING_HELD} (owner rates are loose volumes already)",
    "scope": "every villa: every site-mixed cement : sand layer of every trade (R-T523-1 group SAND_LOOSE)",
}

RULES = {
    "R-T535-1": "sand unit = loose m3 (owner Q-45 / Q-53 / Q-78 / MISSION); fractional while the pack is HELD; loads "
                "only from a sourced pack, one ceiling per villa group; tonnes only from a sourced bulk density.",
    "R-T535-2": "a rounded-rate 'preliminary purchasing allowance' is a separate layer, never procurement "
                "(FINISH V7 R-T528-1); procurement = installed + sourced losses.",
    "R-T535-3": "two villas never share one group or one ceiling.",
    "R-T535-4": "loss without a source -> installed into AT_LEAST, procurement HELD; no installed -> open, never 0.",
}


class SandError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _ceil(x):
    return int(math.ceil(round(x, 9)))


def _num(v):
    return (not isinstance(v, bool)) and isinstance(v, (int, float)) and math.isfinite(v)


def _pair(p, what):
    if p is None:
        return None
    if len(p) != 2 or not all(_num(x) and x >= 0 for x in p) or p[0] > p[1] + 1e-12:
        raise SandError(f"BAD_RANGE: {what} {p!r}")
    return (float(p[0]), float(p[1]))


def member(mid, villa, installed=None, loss=None, loss_state="NONE", loss_source=None):
    """One sand key: installed (low, high) m3 loose; loss (low, high) with loss_state SOURCED (needs loss_source),
    NONE (the producer applies none and none is ruled) or HELD (a loss exists, no source)."""
    if loss_state not in ("NONE", "SOURCED", "HELD"):
        raise SandError(f"BAD_LOSS_STATE: {mid} {loss_state!r}")
    if loss_state == "SOURCED" and (loss is None or not loss_source):
        raise SandError(f"LOSS_WITHOUT_SOURCE: {mid} (a loss figure needs its named source, R-T535-4)")
    return {"id": mid, "villa": villa, "installed": _pair(installed, mid), "loss": _pair(loss, mid),
            "loss_state": loss_state, "loss_source": loss_source}


def check_record(rec):
    """A pack or density figure is only accepted with its source; returns the (pack, density) to use (None = HELD)."""
    pack, dens = rec.get("pack_m3"), rec.get("bulk_density_t_per_m3")
    if pack is not None and (not _num(pack) or pack <= 0 or not rec.get("pack_source")):
        raise SandError(f"PACK_UNSOURCED: {pack!r} (a load size needs a positive value and a named source)")
    if dens is not None and (not _num(dens) or dens <= 0 or not rec.get("density_source")):
        raise SandError(f"DENSITY_UNSOURCED: {dens!r} (a bulk density needs a positive value and a named source)")
    return pack, dens


def procure(group, members, rec=SAND_RECORD):
    """R-T535-1..4 over one villa group: fractional procurement m3 (or AT_LEAST), loads and tonnes when sourced."""
    pack, dens = check_record(rec)
    villas = sorted({m["villa"] for m in members})
    if len(villas) > 1:
        raise SandError(f"TWO_VILLAS_ONE_GROUP: {group} {villas} (one ceiling per villa, R-T535-3)")
    inst, proc, open_, complete = [0.0, 0.0], [0.0, 0.0], [], True
    for m in members:
        if m["installed"] is None:
            open_.append(m["id"])
            complete = False
            continue
        i = m["installed"]
        inst = [inst[0] + i[0], inst[1] + i[1]]
        if m["loss_state"] == "SOURCED":
            p = (i[0] + m["loss"][0], i[1] + m["loss"][1])
        else:
            p = i
            if m["loss_state"] == "HELD":
                complete = False
                open_.append(m["id"] + " (loss HELD)")
        proc = [proc[0] + p[0], proc[1] + p[1]]
    known = any(m["installed"] is not None for m in members)
    out = {"group": group, "villa": villas[0] if villas else None, "unit": rec["unit"], "members": len(members),
           "open": open_, "installed_known": [_r(inst[0]), _r(inst[1])] if known else None}
    if complete and members:
        frac = [_r(proc[0]), _r(proc[1])]
        out.update(status=COMPUTED, procurement_m3=frac, procurement_at_least_m3=None)
    else:
        frac = None
        out.update(status=HELD, procurement_m3=None,
                   procurement_at_least_m3=[_r(proc[0]), _r(proc[1])] if known else None)
    if pack is None:
        out.update(to_buy_loads=None, to_buy_status=f"HELD: {PACK_HELD}")
    elif frac is None:
        out.update(to_buy_loads=None, to_buy_status="HELD: group procurement HELD (open members)")
    else:
        loads = [_ceil(frac[0] / pack), _ceil(frac[1] / pack)]
        out.update(to_buy_loads=loads, to_buy_status=f"COMPUTED: one ceiling of {pack} m3 per load (villa group)",
                   delivered_m3=[_r(loads[0] * pack), _r(loads[1] * pack)])
    base = frac or out["procurement_at_least_m3"]
    if dens is None or base is None:
        out.update(procurement_t=None, tonne_status=f"HELD: {DENSITY_HELD}" if dens is None else "HELD: no m3")
    else:
        out.update(procurement_t=[_r(base[0] * dens), _r(base[1] * dens)],
                   tonne_status="COMPUTED" if frac else "AT_LEAST")
    return out


def sum_of_ceilings(parts, pack):
    """The figure R-T535-3 / R-T523-1 forbids buying (comparison only)."""
    return [sum(_ceil(p[0] / pack) for p in parts), sum(_ceil(p[1] / pack) for p in parts)]


# ------------------------------------------------------------------------------------- merged keys (training villa)
def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


VILLA = "TRAINING_VILLA"


def merged_members():
    """Every merged sand key as a member of the one villa group, restaged by R-T535-2, plus the T-520 perimeter."""
    sys.path.insert(0, str(ROOT))
    from engine.source import finish_materials_table_v7 as V7
    m523 = _module("t523_binding_map_v2", T523_PY)
    t511, t514 = m523._load_json(m523.T511), m523._load_json(m523.T514)
    by_trade = m523.cement_members(t511, t514, "SAND_LOOSE")
    loss = V7.LOSS_Q45["value"]
    rate, why = V7.stair_rate()
    if rate is None:
        raise SandError(f"V7_STAIR_RATE_REFUSED: {why}")
    out, beside, fails = {}, [], []
    for trade, ms in sorted(by_trade.items()):
        for x in ms:
            inst, lst = x["installed"], x["loss_state"]
            if inst is None:
                out.setdefault(trade, []).append(member(x["id"], VILLA))
                continue
            if trade == "STONE_BED":
                # V7 R-T528-1: procurement = installed sand x (1 + Q-45 loss); the T-511 figure is the allowance
                allow = x["procurement"]
                exp_allow = (inst[0] / rate["sand_m3_per_m3"] * rate["purchasing_allowance"]["sand_m3_per_m3"],
                             inst[1] / rate["sand_m3_per_m3"] * rate["purchasing_allowance"]["sand_m3_per_m3"])
                if allow is None or abs(allow[0] - exp_allow[0]) > 2e-6 or abs(allow[1] - exp_allow[1]) > 2e-6:
                    fails.append({"kind": "STAIR_ALLOWANCE_MISMATCH", "where": x["id"], "why": f"{allow} {exp_allow}"})
                beside.append({"id": x["id"], "t523_procurement_m3": list(allow) if allow else None,
                               "layer": V7.ALLOWANCE_LABEL})
                out.setdefault(trade, []).append(member(
                    x["id"], VILLA, installed=inst, loss=(inst[0] * loss, inst[1] * loss), loss_state="SOURCED",
                    loss_source=V7.LOSS_Q45["source"]))
                continue
            if x["procurement"] is not None:
                lo = (x["procurement"][0] - inst[0], x["procurement"][1] - inst[1])
                # the producers print 6 decimals: the stage test is absolute (one print unit per end)
                if any(abs(x["procurement"][i] - inst[i] * (1 + loss)) > 2e-6 for i in (0, 1)):
                    fails.append({"kind": "UNRESOLVED_STAGE", "where": x["id"],
                                  "why": f"procurement {x['procurement']} vs installed {inst} x {1 + loss}"})
                out.setdefault(trade, []).append(member(x["id"], VILLA, installed=inst, loss=lo, loss_state="SOURCED",
                                                        loss_source=V7.LOSS_Q45["source"]))
            else:
                out.setdefault(trade, []).append(member(x["id"], VILLA, installed=inst,
                                                        loss_state="HELD" if lst == "HELD" else "NONE"))
    s520 = json.loads(T520_SUMMARY.read_text())
    sand = s520["materials_perimeter_020"]["sand_m3"]
    out["PERIMETER_JOINT"] = [
        member("T-520|0.20 black walls " + "+".join(s520["computed_020"]["walls"]), VILLA, installed=(sand, sand),
               loss_state="HELD"),                       # block mortar loss unsourced (Q-78 prints none), as T-453
        member(f"T-520|0.15 black walls ({s520['beside_015_held_module']['walls']}) module HELD", VILLA),
        *[member("T-520|" + h.split(":")[0] + " D-39 HELD", VILLA) for h in s520["held_2f_d39"]],
        member("T-520|GF-W22 D-27 HELD", VILLA),
    ]
    return out, beside, fails, m523


def run():
    by_trade, beside, fails, m523 = merged_members()
    allm = [m for v in by_trade.values() for m in v]
    group = procure("SAND_LOOSE", allm)
    trades = {t: procure(t, ms) for t, ms in sorted(by_trade.items())}
    # comparison with the T-523 print (V1 staging of the stair allowance)
    t523_at_least = None
    try:
        t511, t514 = m523._load_json(m523.T511), m523._load_json(m523.T514)
        ms = [x for v in m523.cement_members(t511, t514, "SAND_LOOSE").values() for x in v]
        t523_at_least = m523.group_purchase("SAND_LOOSE", ms, None)["at_least"]
    except Exception as e:                                 # pragma: no cover - reported, never hidden
        fails.append({"kind": "T523_REBUILD", "where": "t523", "why": str(e)})
    delta = None if t523_at_least is None else [_r(group["procurement_at_least_m3"][i] - t523_at_least[i])
                                                for i in (0, 1)]
    st = trades["STONE_BED"]["procurement_at_least_m3"] or trades["STONE_BED"]["procurement_m3"]
    return {
        "schema": SCHEMA, "record": SAND_RECORD, "rules": RULES,
        "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in PINNED},
        "group": group, "trades": trades,
        "stair_allowance_beside": {"members": len(beside),
                                   "t523_bound_procurement_m3": [_r(sum(b["t523_procurement_m3"][i] for b in beside))
                                                                 for i in (0, 1)],
                                   "v7_procurement_m3": st, "layer": beside[0]["layer"] if beside else None},
        "t523_group_at_least_m3": t523_at_least, "delta_vs_t523_m3": delta,
        "members_by_trade": {t: [m["id"] for m in ms] for t, ms in sorted(by_trade.items())},
        "failures": fails, "released_quantities_changed": 0,
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
    print(json.dumps({k: g[k] for k in ("status", "installed_known", "procurement_at_least_m3", "to_buy_status")},
                     indent=1))
    return 1 if m["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
