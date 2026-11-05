"""T-523: MATERIAL BINDING MAP V2. Research reader, not wired: no candidate, engine, rule, knowledge, registry or
producer file changes; the merged T-496 map, its tables and every producer are read, never edited; no candidate or
released (V2.9 + route G) line moves.

Physical element. A material binding is the material of ONE installed element read from ONE producer. Three
quantities are kept apart for it (owner MISSION 'three layers'; T-518 R-T518-1):
  INSTALLED    what is built into the element: area x thickness x per-m3, or area / coverage, or area x rate. It never
               carries a loss.
  LOSS         each named loss (mixing / spillage waste, cutting, spare) as its OWN key with its source; a loss with
               no source stays HELD with the figure BESIDE, never inside a procurement figure (never stacked).
  PROCUREMENT  installed + the sourced losses, before pack rounding; pack rounding happens ONCE per purchasing group.

What V2 changes against T-496 V1 (t496_binding_map.py, merged, untouched):
  (1) STAGE: every one of the 1,202 V1 bindings is re-staged from its producer's own arithmetic (R-T523-2): where the
      bound figure can be re-derived from the producer's stated inputs, the ratio figure / installed decides: 1 ->
      INSTALLED; 1 + f for a SOURCED factor f -> MIS_STAGED (the loss was folded in: split into INSTALLED + LOSS +
      PROCUREMENT); any other ratio -> UNRESOLVED_STAGE (a failure). Where nothing can be re-derived (HELD, no
      number), the stage comes from the producer's code record (STAGE_CODE, file and line). V1's 'THEORETICAL' is the
      same physical quantity as INSTALLED (no factor in the producer): a RELABEL, value unchanged.
      D-T518-2: the T-495 outdoor bed options (V1 FINISH_MATERIALS_TABLE materials(), finish_materials_table.py:213,
      w = 1 + mortar_waste) were bound INSTALLED with the Q-45 B 5 % inside: MIS_STAGED.
  (2) FRESHNESS on the current candidate (R-T523-3): V1 read V3.0.46 / V3.0.47; every bound line is re-read in the
      line index of ARCH_TAKEOFF_V3.0.57 (25a8b406; V3.0.58 = V3.0.57 + 5 FIN.WP.ROOF / ROOF_UPTURN lines, no
      material host, T-514 identity). A figure whose line is now HELD, re-netted or absent leaves the sum and stays
      BESIDE (R-T511-3 applied to every material, not only cement / sand).
  (3) PURCHASING GROUP (R-T523-1, proposed): one ceiling per (product, pack, villa); never a sum of sub-group ceilings.

Rules (R-T523-n, every villa; provenance in RULES below):
  R-T523-1 PURCHASING GROUP  a purchasing group is one product in one pack size bought once for the villa: 50 kg
           cement (every site-mixed cement : sand layer of every trade), 20 kg tile adhesive (T-455 and T-495 rows),
           25 kg AAC glue (T-453 white rows). Loose sand has no pack record: no ceiling, fractional m3 only. The
           to-buy figure is ceil(sum of member procurement / pack) ONCE, and only when every member is known; with an
           open member the group is HELD, its known part is AT_LEAST (fractional, plus one ceiling of it, informative
           only). A member whose installed is known but whose loss is HELD contributes its INSTALLED to AT_LEAST (a
           loss is never negative), never a loss figure. A part that arrives already rounded is refused.
  R-T523-2 STAGE FROM THE PRODUCER  as (1) above; a MIS_STAGED binding becomes three bindings on the same line and
           material (installed, loss_<factor>, procurement) and the V1 figure survives only as the procurement.
  R-T523-3 FRESH ON THE CANDIDATE  as (2) above.
  R-T523-4 ONE PRODUCER PER KEY  a key (line, material, quantity kind, stage) has exactly one producer table; a
           declared READ chain (T-489 reads T-454) must agree; finish options ('@') of one table are alternatives,
           never summed. A second producer is refused (DOUBLE_PRODUCER).
  R-T523-5 HELD NEVER 0  a HELD installed yields no figure and no loss; a group with a HELD member prints no to-buy
           figure; a known part with nothing known is None, never 0.

    python3 -I research/agents_t523/t523_binding_map_v2.py --check     # prints the summary, exit 1 on any failure
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

SCHEMA = "URBAN_T523_MATERIAL_BINDING_MAP_V2"
SUPERSEDES = "URBAN_T496_MATERIAL_BINDING_MAP_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.58 (= V3.0.57 25a8b406 line index + 5 FIN.WP.ROOF / ROOF_UPTURN lines, no material host)"

T496_PY = ROOT / "research/agents_t496/t496_binding_map.py"
T518_PY = ROOT / "research/agents_t518/t518_factor_census.py"
INDEX57 = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
T511 = ROOT / "research/agents_t511/out/CEMENT_SAND_CENSUS_T511.json"
T514 = ROOT / "research/agents_t514/out/SCREED_BED_PRODUCERS_T514.json"
PINS = {T496_PY: "88cbb382366ac743706562a2a0e4bba39e47d0c9a553b1f48d73de909f5ecaa0",
        T518_PY: "3ae7332f1f77b6bf6f79f382004a5ad537803bb137d968bfa840eb2dfc75fafe",
        INDEX57: "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738",
        T511: "a2716399281fbf9dde2e5e762b57562dabe8edccb53af9781da82bc58678aea5",
        T514: "dcd3e0aaa6f426595dea88f6077d4628e2e9da351ae67cb5d10b662bed2eb9de"}

INSTALLED, LOSS, PROCUREMENT = "INSTALLED", "LOSS", "PROCUREMENT"
TOL_REL = 2e-6          # the producers print 6 decimals
TOL_Q = 5e-5            # m2 on the candidate line

# Sourced loss factors a producer may have folded in (T-518 register; only these can explain a ratio above 1).
SOURCED_FACTORS = {
    "Q45B_MORTAR_WASTE": {"value": 0.05, "status": "ASSUMED - OWNER-APPROVED",
                          "source": "Q-45 answer B (owner 2026-10-19 21:40, waste 5 % on mortar) + owner correction "
                                    "2026-10-20 12:15 (X3 withdrawn); T-518 FX-01 / FX-12",
                          "scope": ("TILE_BED_MORTAR",)},
}

# The producer code record of each V1 (table, kind): which stage the producer computes, where (file:line).
STAGE_CODE = {
    ("T-453", "units_nr"): (INSTALLED, "t453_material_ledger.py:329-340 theoretical_count = base x 12.5, breakage HELD"),
    ("T-453", "units_procurement_nr"): (PROCUREMENT, "t453_material_ledger.py:334/340 procurement_count (None today)"),
    ("T-453", "mortar_m3"): (INSTALLED, "t453_material_ledger.py:274-301 mortar_installed_m3 = base x mortar per m2"),
    ("T-453", "cement_bags"): (INSTALLED, "t453_material_ledger.py:270/294 installed m3 x 8 bags (Q-78), no waste"),
    ("T-453", "sand_m3"): (INSTALLED, "t453_material_ledger.py:270/294 installed m3 x 1.1 m3 (Q-78), no waste"),
    ("T-453", "glue_kg"): (INSTALLED, "t453_material_ledger.py:356-363 consumption = base x 3.5 / 4.5 kg/m2"),
    ("T-453", "glue_bags_25kg_net"): (INSTALLED, "t453_material_ledger.py:358/363 consumption / 25 (net, fractional)"),
    ("T-453", "laying_material"): (INSTALLED, "t453_material_ledger.py HELD row (material type not established)"),
    ("T-453", "concrete_m3"): (INSTALLED, "t453_material_ledger.py lintel (w + 2 x 0.40) x section, no factor"),
    ("T-454", "mortar_m3"): (INSTALLED, "plaster_materials_table_v1.py:150-158 m3 = area x thickness"),
    ("T-454", "cement_bags"): (INSTALLED, "plaster_materials_table_v1.py:125-126 m3 x mix figure"),
    ("T-454", "sand_m3"): (INSTALLED, "plaster_materials_table_v1.py:125-126 m3 x mix figure"),
    ("T-489", "mortar_m3"): (INSTALLED, "plaster_materials_table_v2 reads V1 m3 (READ chain)"),
    ("T-489", "cement_bags"): (INSTALLED, "plaster_materials_table_v2 Q-53 C conversion of the installed m3"),
    ("T-489", "sand_m3"): (INSTALLED, "plaster_materials_table_v2 Q-53 C conversion of the installed m3"),
    ("T-455", "adhesive_bags_20kg"): (INSTALLED, "finish_materials_table_v4.py:139-160 area / coverage, fractional; "
                                                 "ceil only per purchasing group (:222-245)"),
    ("T-455", "tiles_nr"): (PROCUREMENT, "finish_materials_table_v4.py:124-135 layout count: whole tiles incl. the "
                                         "cuts by method (UP-CER-010), before boxes / spare; the installed quantity "
                                         "is the m2 line"),
    ("T-495", "adhesive_bags_20kg"): (INSTALLED, "t495_finish_held_ledger.py:155-158 area_low / 5 .. area_high / 3"),
    ("T-495", "bed_mortar_m3"): (INSTALLED, "t495_finish_held_ledger.py:128-138 via finish_materials_table.py:213 "
                                            "(w = 1 + mortar_waste folded in): re-derived below"),
}
RELABEL_FROM = {"THEORETICAL": INSTALLED, "INSTALLED": INSTALLED, "PROCUREMENT": PROCUREMENT}

# R-T523-1 purchasing groups (product, pack, scope, source).
GROUPS = {
    "CEMENT_50KG": {"pack": 1.0, "unit": "bags", "scope": "villa: every site-mixed cement : sand layer of every trade",
                    "source": "Q-45 B / Q-78 (50 kg bags); T-511 R-T511-5; T-518 F-T518-3"},
    "TILE_ADHESIVE_20KG": {"pack": 1.0, "unit": "bags", "scope": "villa: T-455 + T-495 adhesive rows",
                           "source": "UPC-ADHESIVE-001 (Q-45, owner 2026-11-02: ceil per purchasing group)"},
    "AAC_GLUE_25KG": {"pack": 1.0, "unit": "bags (25 kg)", "scope": "villa: T-453 white rows",
                      "source": "UPC-AAC-GLUE-001 (owner 2026-11-02 #4: 25 kg bag)"},
    "SAND_LOOSE": {"pack": None, "unit": "m3", "scope": "villa: every cement : sand layer",
                   "source": "no pack / truck record: no ceiling (fractional m3, never a rounded load)"},
}
RULES = {
    "R-T523-1": "purchasing group = one product, one pack, one villa; one ceiling; HELD member -> no to-buy, AT_LEAST "
                "known part; loss-HELD member contributes its installed. Provenance: owner Q-45 / Q-78 / 2026-11-02 "
                "rules (packs), UPC-ADHESIVE-001 'ceil per purchasing group', T-455 owner directive B3 (project-level "
                "rounding), T-518 R-T518-2. No new factor. PROPOSED (Lead / Checker).",
    "R-T523-2": "stage from the producer's own arithmetic; folded sourced loss -> split; unknown ratio fails",
    "R-T523-3": "every bound line fresh on the candidate of record, else BESIDE",
    "R-T523-4": "one producer per (line, material, kind, stage); declared READ chains agree",
    "R-T523-5": "HELD never 0",
}


class MapV2Error(ValueError):
    pass


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _check_pin(p):
    if p in PINS and _sha(p) != PINS[p]:
        raise MapV2Error(f"PIN: {Path(p).name} sha256 {_sha(p)[:8]} is not the pinned {PINS[p][:8]}")


def _load_json(p):
    _check_pin(p)
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _module(name, p):
    _check_pin(p)
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rel(a, b, tol=TOL_REL):
    return abs(a - b) <= max(tol * max(abs(a), abs(b)), 1e-6)


def _r(x, n=6):
    return None if x is None else round(x, n)


def _ceil(x):
    return int(math.ceil(round(x, 9) - 1e-9)) if x > 0 else 0


# --------------------------------------------------------------------------------------------- R-T523-2 stage
def stage_from_ratio(figure, installed, material):
    """figure / installed -> (stage, factor id or None). 1 -> INSTALLED; 1 + f (sourced, in scope) -> folded f."""
    if figure is None or installed is None or installed == 0:
        return None, None
    r = figure / installed
    if abs(r - 1.0) <= TOL_REL * 10:
        return INSTALLED, None
    for fid, f in SOURCED_FACTORS.items():
        if material in f["scope"] and abs(r - (1.0 + f["value"])) <= TOL_REL * 10:
            return "FOLDED", fid
    return "UNRESOLVED_STAGE", r


def _rederive(b, tables):
    """The installed (low, high) the producer's stated inputs give for this binding, or None when not derivable."""
    t, k = b["table"], b["kind"].split("@")[0]
    rd = b["read"]
    if t == "T-495":
        lo, hi = (rd.get("held_read") or [None, None])
        if lo is None or hi is None:
            return None
        if k == "bed_mortar_m3":
            row = next(r for r in tables["T-495"]["finish_held_rows"] if r["id"] == b["line_id"])
            opt = next(o for o in row["options"] if o["finish"] == b["kind"].split("@")[1])
            band = (opt.get("bed") or {}).get("bed_m")
            return None if not band else (lo * band[0], hi * band[1])
        if k == "adhesive_bags_20kg":
            return (lo / 5.0, hi / 3.0)
    if t == "T-455" and k == "adhesive_bags_20kg" and rd.get("net_read") is not None:
        return (rd["net_read"] / 5.0, rd["net_read"] / 3.0)
    if t in ("T-454", "T-489") and k == "mortar_m3":
        rid, layer = b["row"].split("|")
        row = next(r for r in tables[t]["table"]["rows"] if r["id"] == rid)
        L = next(x for x in row["layers"] if x["layer"] == layer)
        if L.get("thickness_m") is None or L.get("area_m2") is None:
            return None
        v = L["area_m2"] * L["thickness_m"]
        return (v, v)
    return None                       # T-453 figures are re-derived by T-496 R-T496-6 (owner arithmetic, 0 fails)


def restage(b, tables):
    """One V1 binding -> list of V2 bindings with stage / change / evidence (R-T523-2)."""
    t, kb = b["table"], b["kind"].split("@")[0]
    code = STAGE_CODE.get((t, kb))
    if code is None:
        raise MapV2Error(f"UNREAD_KIND: no producer code record for {t} {kb}")
    v1 = b["stage"]
    v2 = code[0] if v1 == "NO_CANDIDATE_LINE" else RELABEL_FROM.get(v1)
    if v2 is None:
        raise MapV2Error(f"UNKNOWN_V1_STAGE: {v1} on {t} {b['row']}")
    if v1 not in ("NO_CANDIDATE_LINE",) and v2 != code[0]:
        v2 = code[0]
    base = dict(b, stage_v1=v1, stage=v2, code=code[1], loss_of=None, factor=None,
                change="SAME" if v1 == v2 else ("NO_LINE" if v1 == "NO_CANDIDATE_LINE" else "RELABEL"))
    inst = _rederive(b, tables)
    if inst is None:
        return [base]
    figs = [b["value"], b["value"]] if b["value"] is not None else (list(b["bound"]) if b["bound"] else None)
    if figs is None or figs[0] is None:
        return [base]
    st = [stage_from_ratio(figs[i], inst[i], b["material"]) for i in (0, 1)
          if figs[i] is not None and inst[i] is not None]
    st = [s for s in st if s[0] is not None]
    if not st:
        return [base]
    if any(s[0] == "UNRESOLVED_STAGE" for s in st) or len({(s[0], s[1]) for s in st}) != 1:
        raise MapV2Error(f"UNRESOLVED_STAGE: {t} {b['row']} {b['kind']} figure {figs} vs installed {inst} "
                         f"(ratios {[s[1] for s in st]})")
    if st[0][0] == INSTALLED:
        if code[0] != INSTALLED:
            raise MapV2Error(f"STAGE_CONFLICT: {t} {b['row']} re-derives INSTALLED, code says {code[0]}")
        return [base]
    fid = st[0][1]
    f = SOURCED_FACTORS[fid]
    pair = lambda xs: None if xs is None else [_r(xs[0]), _r(xs[1])]
    as_value = b["value"] is not None
    inst_r, loss_r = pair(inst), pair((inst[0] * f["value"], inst[1] * f["value"]))
    proc_r = pair(figs)
    out = []
    for stage, kind, fig, extra in ((INSTALLED, b["kind"], inst_r, {}),
                                    (LOSS, f"{kb}_loss" + ("@" + b["kind"].split("@")[1] if "@" in b["kind"] else ""),
                                     loss_r, {"loss_of": b["kind"], "factor": dict(f, id=fid)}),
                                    (PROCUREMENT, f"{kb}_procurement" + ("@" + b["kind"].split("@")[1]
                                                                         if "@" in b["kind"] else ""), proc_r, {})):
        out.append(dict(base, kind=kind, stage=stage, change="MIS_STAGED", value=fig[0] if as_value else None,
                        bound=None if as_value else fig, **extra,
                        v1_figure=figs if stage == PROCUREMENT else None))
    return out


# --------------------------------------------------------------------------------------------- R-T523-3 freshness
def freshness(bs, index):
    lines = {ln["line_id"]: ln for ln in index["lines"]}
    for b in bs:
        lid = b["line_id"]
        if b["stage_v1"] == "NO_CANDIDATE_LINE" or lid is None:
            b["fresh"] = "NO_CANDIDATE_LINE"
            continue
        ln = lines.get(lid)
        rd = b["read"]
        if ln is None:
            why = "ABSENT"
        elif (rd["class_read"] == "HELD") != (ln["class"] == "HELD"):
            why = f"STALE_CLASS: read {rd['class_read']}, candidate {ln['class']}"
        elif ln["class"] == "RELEASED" and rd.get("net_read") is not None and abs(rd["net_read"] - ln["measured_net"]) > TOL_Q:
            why = f"STALE_NET: read {rd['net_read']}, candidate {ln['measured_net']}"
        else:
            why = None
        b["fresh"] = "FRESH" if why is None else why
        if why and (b["value"] is not None or b["bound"] is not None):
            b["beside"] = {"value": b["value"], "bound": b["bound"], "why": why}
            b["value"], b["bound"] = None, None
    return bs


# --------------------------------------------------------------------------------------------- R-T523-4 one producer
READS = {("T-454", "T-489"): ("mortar_m3",)}


def check_one_producer(bs):
    seen, fails = {}, []
    for b in bs:
        if b["line_id"] is None or b["stage_v1"] == "NO_CANDIDATE_LINE":
            continue
        if b["value"] is None and b["bound"] is None and b.get("estimate_beside") is None:
            continue              # carries nothing: produces nothing
        seen.setdefault((b["line_id"], b["material"], b["kind"].split("@")[0], b["stage"]), []).append(b)
    for key, lst in seen.items():
        tabs = sorted({b["table"] for b in lst})
        if len(lst) == 1:
            continue
        if len(tabs) == 1 and all("@" in b["kind"] for b in lst) and len({b["kind"] for b in lst}) == len(lst):
            continue              # finish options of one table: alternatives, never summed
        if len(tabs) == len(lst) and tuple(tabs) in READS and key[2] in READS[tuple(tabs)]:
            vals = {json.dumps([b["value"], b["bound"], b.get("estimate_beside")]) for b in lst}
            if len(vals) == 1:
                continue
            fails.append({"kind": "CHAIN_DIVERGES", "where": "|".join(key), "why": sorted(vals)})
            continue
        fails.append({"kind": "DOUBLE_PRODUCER", "where": "|".join(key), "why": f"{len(lst)} producers {tabs}"})
    return fails


# --------------------------------------------------------------------------------------------- R-T523-1 groups
def member(mid, installed=None, loss=None, loss_state="NONE", procurement=None):
    """installed / loss / procurement: (low, high) or None. loss_state: NONE (the producer applies no loss and none is
    sourced), SOURCED (loss given), HELD (a loss exists but has no source / value: beside, never stacked)."""
    return {"id": mid, "installed": installed, "loss": loss, "loss_state": loss_state, "procurement": procurement}


def group_purchase(group, members, pack):
    """R-T523-1: one ceiling per group. Returns status, fractional procurement (low, high) or AT_LEAST, to_buy."""
    open_, at_least, complete = [], [0.0, 0.0], True
    for m in members:
        if m.get("rounded"):
            raise MapV2Error(f"{group}: member {m['id']} arrives already rounded (round once per purchasing group)")
        if m["installed"] is None:
            open_.append(m["id"])
            complete = False
            continue
        if m["procurement"] is not None:
            p = m["procurement"]
        elif m["loss_state"] == "SOURCED" and m["loss"] is not None:
            p = (m["installed"][0] + m["loss"][0], m["installed"][1] + m["loss"][1])
        elif m["loss_state"] == "NONE":
            p = m["installed"]
        else:                                            # loss HELD: installed is a lower bound, the loss is beside
            p = m["installed"]
            complete = False
            open_.append(m["id"] + " (loss HELD)")
        at_least[0] += p[0]
        at_least[1] += p[1]
    known = any(m["installed"] is not None for m in members)
    rec = {"group": group, "members": len(members), "open": open_}
    if complete and members:
        frac = [_r(at_least[0]), _r(at_least[1])]
        rec.update(status="COMPUTED", procurement=frac, at_least=None,
                   to_buy=None if pack is None else [_ceil(frac[0] / pack), _ceil(frac[1] / pack)])
    else:
        al = [_r(at_least[0]), _r(at_least[1])] if known else None
        rec.update(status="HELD", procurement=None, at_least=al, to_buy=None,
                   to_buy_at_least=None if (al is None or pack is None) else [_ceil(al[0] / pack), _ceil(al[1] / pack)])
    return rec


def sum_of_subgroup_ceils(parts, pack=1.0):
    """The figure R-T523-1 forbids buying: one ceiling per sub-group, summed (comparison only)."""
    return [sum(_ceil(p[0] / pack) for p in parts), sum(_ceil(p[1] / pack) for p in parts)]


def cement_members(t511, t514, material="CEMENT_50KG"):
    """Cement / sand members of the villa group from the merged census rows (T-511 + T-514), keyed by
    (table, line, layer); readers and finish options are not producers; T-511 stale rows are beside."""
    stale = {(s["line_id"], s["material"], s["stage"]) for s in t511["stale"]}
    keys = {}
    for r in t511["rows"] + t514["rows"]:
        if r["material"] != material or r["role"] != "PRODUCER":
            continue
        if (r["line_id"], r["material"], r["stage"]) in stale:
            continue
        k = (r["table"], r["line_id"], r["layer"])
        d = keys.setdefault(k, {})
        if r["stage"] in d:
            raise MapV2Error(f"DOUBLE_PRODUCER: {k} {r['stage']} twice")
        d[r["stage"]] = None if r["status"] == "HELD" or r["low"] is None else (r["low"], r["high"])
        d.setdefault("trade", r["trade"])
    out = {}
    for k, d in sorted(keys.items()):
        inst, waste, proc = d.get("INSTALLED"), d.get("WASTE"), d.get("PROCUREMENT")
        if proc is not None:
            m = member("|".join(k), installed=inst, loss=waste, loss_state="SOURCED" if waste else "NONE",
                       procurement=proc)
        else:
            m = member("|".join(k), installed=inst, loss_state="HELD" if inst is not None else "NONE")
        out.setdefault(d["trade"], []).append(m)
    return out


def _sum_stage(members, key):
    v = [m[key] for m in members if m[key] is not None]
    return None if not v else [_r(sum(x[0] for x in v)), _r(sum(x[1] for x in v))]


def cement_restatement(t511, t514):
    """Project cement / sand: V1 known parts (T-514 print) and V2 (R-T523-1), plus the ceiling comparison."""
    res = {}
    for mat, gkey in (("CEMENT_50KG", "CEMENT_50KG"), ("SAND_LOOSE", "SAND_LOOSE")):
        by_trade = cement_members(t511, t514, mat)
        allm = [m for v in by_trade.values() for m in v]
        g = group_purchase(gkey, allm, GROUPS[gkey]["pack"])
        trades = {}
        for tr, ms in sorted(by_trade.items()):
            tg = group_purchase(tr, ms, GROUPS[gkey]["pack"])
            trades[tr] = {"installed_known": _sum_stage(ms, "installed"),
                          "procurement_known_v1": _sum_stage(ms, "procurement"),
                          "procurement_at_least_v2": tg.get("at_least") or tg.get("procurement"),
                          "loss_held_members": len([m for m in ms if m["loss_state"] == "HELD" and m["installed"]]),
                          "open_members": len(tg["open"])}
        p = t514["subtotals"]["PROJECT"]
        res[mat] = {"group": g, "trades": trades,
                    "installed_known_part": _sum_stage(allm, "installed"),
                    "procurement_known_part_v1": _sum_stage(allm, "procurement"),
                    "t514_prints": {"installed_at_least": [p["INSTALLED"][mat]["at_least_low"],
                                                           p["INSTALLED"][mat]["at_least_high"]],
                                    "procurement_at_least": [p["PROCUREMENT"][mat]["at_least_low"],
                                                             p["PROCUREMENT"][mat]["at_least_high"]]}}
        if mat == "CEMENT_50KG":
            parts = [t["procurement_at_least_v2"] for t in trades.values() if t["procurement_at_least_v2"]]
            res[mat]["ceilings"] = {"one_ceiling_at_least": g.get("to_buy_at_least") or g.get("to_buy"),
                                    "sum_of_trade_ceilings": sum_of_subgroup_ceils(parts),
                                    "trade_parts": parts}
    return res


def glue_and_adhesive(bs):
    """AAC glue and tile adhesive groups from the V2 bindings (fresh figures only; ranges give AT_LEAST lows)."""
    out = {}
    glue = [b for b in bs if b["table"] == "T-453" and b["kind"] == "glue_bags_25kg_net"]
    ms = []
    for b in glue:
        if b["value"] is not None:
            ms.append(member(b["line_id"], installed=(b["value"], b["value"]), loss_state="HELD"))
        elif b["bound"] is not None:
            ms.append(member(b["line_id"] + " (range)", installed=(b["bound"][0], b["bound"][1]), loss_state="HELD"))
        else:
            ms.append(member(b["line_id"]))
    for lid in ("L-7503af7cc1eea4e6735d", "L-ee857398614d817e6917"):     # T-496 KNOWN_GAPS (type not read): open
        ms.append(member(lid))
    out["AAC_GLUE_25KG"] = group_purchase("AAC_GLUE_25KG", ms, GROUPS["AAC_GLUE_25KG"]["pack"])
    out["AAC_GLUE_25KG"]["stale_beside"] = [{"line": b["line_id"], **b["beside"]} for b in glue if b.get("beside")]
    adh = [b for b in bs if b["material"] == "TILE_ADHESIVE" and "@" not in b["kind"]]
    ms = [member(b["line_id"]) if b["value"] is None else member(b["line_id"], installed=(b["value"], b["value"]))
          for b in adh]
    g = group_purchase("TILE_ADHESIVE_20KG", ms, GROUPS["TILE_ADHESIVE_20KG"]["pack"])
    bl = [b["bound"] for b in adh if b["bound"]]
    g["bound_of_rows"] = None if not bl else [_r(sum(x[0] for x in bl)), _r(sum(x[1] for x in bl))]
    g["bound_to_buy_one_ceiling"] = None if len(bl) < len(adh) else [_ceil(g["bound_of_rows"][0]), _ceil(g["bound_of_rows"][1])]
    g["options_beside"] = sorted({b["line_id"] for b in bs if b["material"] == "TILE_ADHESIVE" and "@" in b["kind"]})
    out["TILE_ADHESIVE_20KG"] = g
    return out


# --------------------------------------------------------------------------------------------- build
def _t498_slice(v2, v1):
    """Blockwork (T-453) bindings whose V2 differs from V1: what the T-498 resume must read."""
    rows, sums = [], {}
    for b in v2:
        if b["table"] != "T-453" or b["stage_v1"] == "NO_CANDIDATE_LINE":
            continue
        moved = b.get("beside") is not None
        if moved or b["change"] != "SAME":
            rows.append({"line_id": b["line_id"], "kind": b["kind"], "status": b["status"], "v1_stage": b["stage_v1"],
                         "v2_stage": b["stage"], "change": "STALE_BESIDE" if moved else b["change"],
                         "v1_value": (b.get("beside") or {}).get("value", b["value"]),
                         "v1_bound": (b.get("beside") or {}).get("bound", b["bound"]),
                         "v2_value": b["value"], "v2_bound": b["bound"], "fresh": b["fresh"]})
    for label in ("VERIFIED-NET", "PROVISIONAL-NET"):
        for kind in ("units_nr", "glue_kg", "mortar_m3", "cement_bags"):
            a = sum(b["value"] for b in v1 if b["table"] == "T-453" and b["kind"] == kind and b["status"] == label
                    and b["value"] is not None)
            c = sum(b["value"] for b in v2 if b["table"] == "T-453" and b["kind"] == kind and b["status"] == label
                    and b["value"] is not None)
            if a or c:
                sums[f"{kind}|{label}"] = {"v1": _r(a), "v2": _r(c), "delta": _r(c - a)}
    return {"rows": rows, "known_part_by_label": sums}


def run():
    m496 = _module("t496_binding_map", T496_PY)
    v1map = m496.run()                                  # pins its own inputs; must still pass its own check
    tables = {"T-453": m496._load(m496.T453), "T-454": m496._load(m496.T454), "T-489": m496._load(m496.T489),
              "T-455": m496._load(m496.T455), "T-495": m496._load(m496.T495)}
    v1 = v1map["bindings"]
    fails = [dict(f, kind="V1_" + f["kind"]) for f in v1map["failures"]]
    v2, n_read = [], 0
    for b in v1:
        try:
            v2.extend(restage(b, tables))
            n_read += 1
        except MapV2Error as e:
            fails.append({"kind": str(e).split(":")[0], "where": f"{b['table']} {b['row']}", "why": str(e)})
    freshness(v2, _load_json(INDEX57))
    fails += check_one_producer(v2)
    for b in v2:          # R-T523-5: a HELD row (or HELD candidate line) carries no figure
        if (b["status"] or "").upper() == "HELD" and b["value"] is not None:
            fails.append({"kind": "HELD_YIELDS_FIGURE", "where": f"{b['table']} {b['row']}", "why": b["kind"]})
        b["wiring_state"] = ("NO_CANDIDATE_LINE" if b["stage_v1"] == "NO_CANDIDATE_LINE" else
                             "WIREABLE_FIGURE" if b["value"] is not None else
                             "ESTIMATE_BESIDE_HELD" if b.get("estimate_beside") is not None else
                             "BOUND_ONLY" if b["bound"] is not None else
                             "STALE_BESIDE" if b.get("beside") else "HELD")
    t511, t514 = _load_json(T511), _load_json(T514)
    from collections import Counter
    changes = Counter(b["change"] for b in v2)
    mis = [b for b in v2 if b["change"] == "MIS_STAGED"]
    return {
        "schema": SCHEMA, "supersedes": SUPERSEDES, "candidate": CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
        "v1_bindings": len(v1), "v1_read": n_read, "v2_bindings": len(v2),
        "changes": dict(sorted(changes.items())),
        "stages": dict(sorted(Counter(b["stage"] for b in v2).items())),
        "fresh": dict(sorted(Counter(b["fresh"].split(":")[0] for b in v2).items())),
        "mis_staged": [{"line_id": b["line_id"], "kind": b["kind"], "stage": b["stage"], "bound": b["bound"],
                        "value": b["value"], "v1_figure": b.get("v1_figure"),
                        "factor": (b.get("factor") or {}).get("id")} for b in mis],
        "groups": dict(glue_and_adhesive(v2), **{"CEMENT_SAND": cement_restatement(t511, t514)}),
        "t498_slice": _t498_slice(v2, v1),
        "bindings": v2, "rules": RULES, "group_records": GROUPS, "failures": fails,
        "released_quantities_changed": 0,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    m = run()
    for f in m["failures"]:
        print(f"FAIL {f['kind']}: {f['where']}: {f['why']}")
    c = m["groups"]["CEMENT_SAND"]["CEMENT_50KG"]
    print(json.dumps({"v1": m["v1_bindings"], "v2": m["v2_bindings"], "changes": m["changes"], "fresh": m["fresh"],
                      "cement_group": c["group"], "ceilings": c["ceilings"]}, indent=1))
    return 1 if m["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
