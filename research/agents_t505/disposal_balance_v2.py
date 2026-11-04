"""DISPOSAL_BALANCE_V2 (T-505, lane S, research, unwired, stdlib only): DISPOSAL_BALANCE_V1 (T-503, rule R-T503-1,
research/agents_t503/disposal_balance_v1.py, UNTOUCHED and called here) with the LOSS terms as their own accounts.
Rule R-T505-1 (every villa). From Checker F-C-T503-1: V1 had no loss term, so a reuse end (s > 0) could be valued
without one (owner 2026-11-02 18:00 (3): reused material, imported material and losses are separate accounts).

PHYSICAL ELEMENT (ERS s.2.1): the dry mass of soil leaving the site (disposal) and arriving (import) for one villa:
excavation E in situ, fill demand D compacted at its PLACEMENT TARGET density, suitable share s, and two losses:

    loss_reuse  lr   share of the excavated soil TAKEN for reuse that is never placed (handling, stockpiling, double
                     handling, contamination); its own account, in in-situ m3; never silently inside disposal or reuse
    loss_import li   share of the PROCURED import that is never placed (delivery, spreading); its own account, in t

    k              = rho_target / rho_insitu                     in-situ m3 per compacted m3 (dry-mass conservation)
    taken_insitu   = min(s x E, k x D / (1 - lr))                excavated soil taken for reuse
    placed_insitu  = taken_insitu x (1 - lr)                     reused soil that ends in the fill
    loss_reuse_m3  = taken_insitu x lr                           separate account (destination: contract / site fact)
    disposal       = E - taken_insitu                            surplus never taken for reuse (payable basis in situ)
    import_compact = D - placed_insitu / k                       net compacted import
    import_net_t   = import_compact x rho_target                 net dry mass placed
    import_procured_t = import_net_t / (1 - li)                  procurement; loss_import_t = procured - net
    conservation   E = disposal + placed + loss_reuse            D x rho_target = placed x rho_insitu + import_net_t

Equivalently the reuse end of V1 with an effective yield k_eff = k / (1 - lr): V1's own end logic (qualifiers, open
sums, AT_MOST low ends, every-fill-HELD) is reused unchanged by passing that yield; the loss account is then derived.

GATES (hold only the affected quantity, ERS s.2.7 / no-assumptions rule):
  * the s = 0 end needs no density and no loss: it is V1's figure byte for byte (pure geometry, asserted);
  * an end with s > 0 is HELD unless lr is SOURCED (MEASURED on site, printed in the project specification /
    contract, or a documented reference figure read in full: ESTIMATED level 4); an unsourced lr names its missing
    source; a zero loss is a figure like any other and needs its source (never a default 0);
  * li gates the import PROCUREMENT mass and loose volume only (never the in-situ disposal or the net import);
  * a HELD candidate line enters the sums BLANK (open) even when it carries a bound; its bound is named beside, never
    summed (a HELD line's figure is not released into another quantity).
Nothing names a project.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t503"))
import disposal_balance_v1 as V1  # noqa: E402

METHOD_ID = "DISPOSAL_BALANCE_V2"
EXTENDS = V1.METHOD_ID
RULE_ID, RULE_VERSION = "R-T505-1", "1.0.0"
Refused = V1.Refused
DC, MEAS, CALC, EST, SPEC, PV, HELD, GEOTECH = V1.DC, V1.MEAS, V1.CALC, V1.EST, V1.SPEC, V1.PV, V1.HELD, V1.GEOTECH
EXC, FILL, EXACT, AT_LEAST, AT_MOST, IN_SITU, LOOSE = V1.EXC, V1.FILL, V1.EXACT, V1.AT_LEAST, V1.AT_MOST, V1.IN_SITU, \
    V1.LOOSE
term, density, suitability, bulking, worst, describe_end = V1.term, V1.density, V1.suitability, V1.bulking, V1.worst, \
    V1.describe_end
TOL = V1.TOL
_r = V1._r

REUSE, IMPORT = "REUSE_HANDLING", "IMPORT_PROCUREMENT"
LOSS_LEVEL = {MEAS: "site measurement (level 1)", DC: "project specification / contract (level 2)",
              EST: "documented reference figure read in full (level 4)"}
_LOSS_UNIT = {"fraction": 1.0, "%": 0.01}
LOSS_MAX = 0.5                      # a unit guard (a percent passed as a fraction), not a value
MISSING_LR = ("handling loss of the re-used excavated soil (loss_reuse): no measured, specified or documented figure "
              "(Kuwait MPW General Specifications 1990 s.02220 / s.02223 and the reference folders state none)")
MISSING_LI = ("procurement loss of the imported fill (loss_import): no measured, specified or documented figure")


def loss(kind, value=None, status=HELD, source=None, unit="fraction", read_in_full=False):
    """One loss fact. HELD (value None) names its missing source. A value needs a status in LOSS_LEVEL and a source;
    an ESTIMATED figure only from a documented reference read in full (read_in_full=True)."""
    if kind not in (REUSE, IMPORT):
        raise Refused("UNKNOWN_LOSS", repr(kind))
    if unit not in _LOSS_UNIT:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    if value is None or status == HELD:
        if value is not None:
            raise Refused("HELD_AS_VALUE", f"{kind} {value!r}")
        return {"kind": kind, "value": None, "status": HELD, "source": source,
                "missing": MISSING_LR if kind == REUSE else MISSING_LI}
    if status not in LOSS_LEVEL:
        raise Refused("LOSS_LEVEL", f"{kind}: {status} is not a measured, specified or documented figure")
    if not source:
        raise Refused("LOSS_WITHOUT_SOURCE", f"{kind} {value}")
    if status == EST and not read_in_full:
        raise Refused("LOSS_SOURCE_NOT_READ", f"{kind}: a documented figure only with its source read in full")
    v = float(value) * _LOSS_UNIT[unit]
    if not 0.0 <= v < LOSS_MAX:
        raise Refused("LOSS_UNIT", f"{kind} {v} outside 0 .. {LOSS_MAX}: a percent given as a fraction?")
    return {"kind": kind, "value": v, "status": status, "source": source, "level": LOSS_LEVEL[status],
            "missing": None}


def _held(missing, scenario):
    return {"value": None, "qualifier": "HELD", "status": HELD, "missing": missing, "scenario": scenario}


def balance(terms, rho_insitu, rho_target, suit, loss_reuse=None, loss_import=None, rho_loose_import=None, bulk=None,
            contract_basis=None, truck_capacity_m3=None, rho_acceptance=None):
    """The B1-04 balance with the loss accounts. Same returns as V1 (disposal / import ranges, loose, payable,
    truckloads) plus loss_reuse_insitu_m3, excavated_not_placed_m3, import_procurement and the V2 conservation."""
    lr = loss_reuse or loss(REUSE)
    li = loss_import or loss(IMPORT)
    if lr["kind"] != REUSE or li["kind"] != IMPORT:
        raise Refused("LOSS_SWAPPED", "loss_reuse and loss_import are different facts")
    for t in terms:
        if V1._base(t["status"]) == HELD and t["low"] is not None:
            raise Refused("HELD_BOUND_IN_SUM", f"{t['line_id']}: a HELD line enters blank, its bound beside")
    ri, rt = (rho_insitu or {}).get("value"), (rho_target or {}).get("value")
    # V1 on the effective yield k / (1 - lr): the in-situ density carrier is scaled (its status kept), so V1's own
    # end logic runs unchanged; the s = 0 ends do not depend on it (asserted below against a plain V1 run)
    eff_insitu = rho_insitu
    if ri is not None and lr["value"] is not None:
        eff_insitu = dict(rho_insitu, value=ri * (1.0 - lr["value"]))
    out = V1.balance(terms, eff_insitu, rho_target, suit, rho_loose_import, bulk, contract_basis, truck_capacity_m3,
                     rho_acceptance)
    plain = V1.balance(terms, rho_insitu, rho_target, suit, rho_loose_import, bulk, contract_basis, truck_capacity_m3,
                       rho_acceptance)
    k = None if ri is None or rt is None else rt / ri
    out["method"], out["extends"], out["rule"] = METHOD_ID, EXTENDS, f"{RULE_ID} {RULE_VERSION}"
    out["k_insitu_per_compacted"] = _r(k)
    out["k_effective_with_reuse_loss"] = None if k is None or lr["value"] is None else _r(k / (1.0 - lr["value"]))
    out["losses"] = {"reuse": copy.deepcopy(lr), "import": copy.deepcopy(li)}
    Es = out["excavation"]
    s_of = {("disposal_insitu_m3", "low"): suit["high"], ("disposal_insitu_m3", "high"): suit["low"],
            ("import_compacted_m3", "low"): suit["high"], ("import_compacted_m3", "high"): suit["low"]}
    E_of = {("disposal_insitu_m3", "low"): Es["low"], ("disposal_insitu_m3", "high"): Es["high"],
            ("import_compacted_m3", "low"): Es["high"], ("import_compacted_m3", "high"): Es["low"]}
    for (q, side), s in s_of.items():
        e = out[q][side]
        if s == 0.0:                                            # pure geometry: V1's end byte for byte
            if e != plain[q][side]:
                raise AssertionError(f"{q} {side}: the s = 0 end moved under V2")
            continue
        if lr["value"] is None:
            out[q][side] = _held(list(dict.fromkeys((e.get("missing") or []) + [MISSING_LR])), e["scenario"])
        elif e["value"] is not None:
            e["status"] = worst(e["status"], lr["status"])
    dl, im = out["disposal_insitu_m3"], out["import_compacted_m3"]
    out["state"] = ("VALUED" if all(e["qualifier"] == EXACT for e in (dl["low"], dl["high"])) and
                    dl["low"]["value"] == dl["high"]["value"] else
                    "BOUNDED" if all(e["value"] is not None for e in (dl["low"], dl["high"])) else "HELD_RANGE")
    out["single_number"] = out["state"] == "VALUED"
    # loose / payable / truckloads re-derived from the V2 ends (V1 built them from its own, loss-free ends)
    bf = (bulk or {}).get("value")
    loose = {s: (None if dl[s]["value"] is None or bf is None else _r(dl[s]["value"] * bf)) for s in ("low", "high")}
    out["disposal_loose_m3"].update(low=loose["low"], high=loose["high"])
    basis = out["payable"]["basis"]
    out["payable"].update(low=dl["low"]["value"] if basis == IN_SITU else loose["low"],
                          high=dl["high"]["value"] if basis == IN_SITU else loose["high"])
    if "truckloads_logistics_only" in out:
        out["truckloads_logistics_only"] = {s: (None if loose[s] is None else
                                                V1.math.ceil(loose[s] / float(truck_capacity_m3) - 1e-9))
                                            for s in ("low", "high")}
    # the reuse-loss account and the not-placed total, at every EXACT disposal end
    acc, notp = {}, {}
    for side in ("low", "high"):
        e, E, s = dl[side], E_of[("disposal_insitu_m3", side)], s_of[("disposal_insitu_m3", side)]
        if s == 0.0 and e["value"] is not None:
            acc[side] = {"value": 0.0, "calculated_zero": True, "basis": "no soil taken for reuse (s = 0)"}
        elif e["value"] is None:
            acc[side] = {"value": None, "missing": list(e.get("missing") or [MISSING_LR])}
        elif lr["value"] is None:
            acc[side] = {"value": None, "missing": [MISSING_LR]}
        elif e["qualifier"] != EXACT:
            acc[side] = {"value": None, "missing": ["an open sum: the soil taken for reuse is not bounded"]}
        else:
            taken = E - e["value"]
            acc[side] = {"value": _r(taken * lr["value"]), "taken_insitu_m3": _r(taken),
                         "placed_insitu_m3": _r(taken * (1.0 - lr["value"])), "status": worst(e["status"], lr["status"])}
        notp[side] = (None if acc[side]["value"] is None or e["value"] is None else
                      {"value": _r(e["value"] + acc[side]["value"]), "qualifier": e["qualifier"]})
    out["loss_reuse_insitu_m3"] = acc
    out["excavated_not_placed_m3"] = notp
    out["payable"]["loss_reuse"] = ("not in payable disposal: its destination (carted with the spoil or spread on "
                                    "site) is a contract / site fact; reported as its own account")
    # import procurement: net mass (V1) / (1 - li), loss beside
    proc = {}
    rl = (rho_loose_import or {}).get("value")
    for side in ("low", "high"):
        e = im[side]
        if e["value"] is None or rt is None:
            proc[side] = {"net_dry_t": None, "procured_dry_t": None, "loss_import_t": None,
                          "missing": (e.get("missing") or []) + ([] if rt else
                                                                 ["placement target dry density of the fill"])}
            continue
        net = e["value"] * rt
        if li["value"] is None:
            proc[side] = {"net_dry_t": _r(net), "procured_dry_t": None, "loss_import_t": None,
                          "qualifier": e["qualifier"], "missing": [MISSING_LI]}
            continue
        pr = net / (1.0 - li["value"])
        proc[side] = {"net_dry_t": _r(net), "procured_dry_t": _r(pr), "loss_import_t": _r(pr - net),
                      "procured_loose_m3": _r(pr / rl) if rl else None, "qualifier": e["qualifier"],
                      "status": worst(e["status"], li["status"]),
                      "missing": [] if rl else ["loose delivered dry density of the import (its own fact)"]}
    out["import_procurement"] = proc
    # V1's import_material is the NET mass on the V2 import ends
    for side in ("low", "high"):
        e = im[side]
        if e["value"] is None:
            out["import_material"][side] = {"dry_t": None, "loose_m3": None, "missing": e["missing"]}
    # V2 conservation at every closed end (true densities, loss account included)
    out["conservation"] = []
    if k is not None and lr["value"] is not None:
        for side in ("low", "high"):
            e, s = dl[side], s_of[("disposal_insitu_m3", side)]
            E = E_of[("disposal_insitu_m3", side)]
            D = out["fill_demand"]["high" if side == "low" else "low"]
            if e["value"] is None or e["qualifier"] != EXACT or out["fill_demand"]["open"]:
                continue
            taken = E - e["value"]
            placed = taken * (1.0 - lr["value"])
            imp_c = D - placed / k
            if abs(E - (e["value"] + placed + taken * lr["value"])) > TOL or \
                    abs(D * rt - (placed * ri + imp_c * rt)) > TOL or imp_c < -TOL:
                raise AssertionError("dry-mass conservation broken (V2)")
            out["conservation"].append({"side": side, "E": _r(E), "D": _r(D), "s": s, "taken_insitu_m3": _r(taken),
                                        "placed_insitu_m3": _r(placed), "loss_reuse_insitu_m3": _r(taken - placed),
                                        "import_compacted_m3": _r(max(imp_c, 0.0)), "closes": True})
    return out
