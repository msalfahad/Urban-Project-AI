"""T-708 on the development villa (values only; no drawing content): (a) the Z2 owner plan x depth reconciled term
by term, (b) the R-T505-1 disposal / import balance restated on the T-695 / T-700 geometry beside the candidate of
record, (c) the dry-mass inputs per zone and the wiring form for T-509.

Inputs, each pinned by sha256 (an edited file stops the run); every figure and status is READ, none typed here
except the source statuses of the four ranges T-695 / T-700 newly bounded (named in NEW_STATUS with their source):
  research/agents_t700/ZONES_T700.json       merged T-700: Z2 panel / beam terms, lift pit, annex
  research/agents_t700/WIRING_T700.csv       merged T-700: the wiring form (21 rows)
  research/agents_t722/out/LINE_INDEX_V3_0_73.json   newest candidate line index (earthworks + ground-slab lines
                                             asserted equal to V3.0.69, T-700's record)
  research/agents_t687/out/LINE_INDEX_V3_0_69.json
  research/agents_t717/out/LINE_INDEX_V3_0_74.json   newest at hand-in (T-717): the same lines, asserted
  research/agents_t505/summary_t505.json     merged T-505 result on the candidate of record (scenario A check)

    python3 -I research/agents_t708/t708_alsenan.py   -> RECON_Z2_T708.csv, BALANCE_T708.json, WIRING_T708.csv,
                                                          summary_t708.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
for p in (HERE, RES / "agents_t505", RES / "agents_t503"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import balance_restate as R  # noqa: E402
import disposal_balance_v2 as B  # noqa: E402
import t505_alsenan as A505  # noqa: E402

PINS = {}                                  # rel path -> sha256, read from PINNED and checked
PINNED = HERE / "PINS_T708.json"          # the sha256 of each input at the merged state, written once and checked
OWNER_DEPTH = 0.85                         # T-700 s.1 owner manual method: main GF +1.00 - 0.05 - 0.10, EG +-0.00
DISPOSAL_LINE = "L-78d7c8a989ab34527a1c"
ROLE = {"STR.EARTH.EXCAVATION": B.EXC, "STR.EARTH.BACKFILL": B.FILL}
EXPOSURE = "L-438a4abd3adc0475d0bd"       # HELD BOUNDED_EXPOSURE (T-497, R-T497-1): its bound stays beside (as T-505)
# the source status of each range T-695 / T-700 newly bounded (the worst of the facts it rests on):
NEW_STATUS = {
    "EW-T350:B1-02:Z1-TRENCH-STRAPS": (B.EST, "T-695: D-15 x S02 scenarios on the S01 founding level (ESTIMATED)"),
    "EW-T350:B1-02:Z1-TRENCH-ANNEX": (B.EST, "T-700: high end on the R3 formation datum under S01 (ESTIMATED)"),
    "EW-T350:B1-03:Z2": (B.PV + " (T-700 Gate A; GS-08 / 12 / 16 and beam readings enveloped)",
                         "T-700: printed GF levels; unprinted extents and sections as admissible envelopes"),
}
CAUSE = {
    "PANEL_MAIN_100": "slab panel at the main GF +1.00 (LEVEL marks 1BE / 1C0 / 1C2 / 1CD): underside +0.85 = the "
                      "owner depth",
    "PANEL_ANNEX_030": "slab panel at +0.30 (annex marks 1B0 / 1B2 / 1B4, or GS-28 printed +0.30): underside +0.15, "
                       "0.70 shallower than the owner depth",
    "PANEL_HELD_LEVEL": "slab panel whose level is not printed for its whole extent (GS-08 lobby +0.30 / +1.00; "
                        "GS-12 / GS-16 floored +1.00 or court on N.G.): each end at its admissible reading",
    "BEAM_MAIN_INT": "fill under a main interior ground beam (printed D 0.40, top +0.95): column EG .. blinding "
                     "bottom +0.45 x b 0.30 less its two 0.10 x 0.10 blinding projections in panel fill",
    "BEAM_MAIN_INT_D34": "the same under a D-34 run (D 0.30 / 0.40)",
    "BEAM_MAIN_INT_D33": "the same under a D-33 run (D >= printed title, open above; at D 0.85 the blinding sits on "
                         "EG and only its projections remain: negative)",
    "BEAM_MAIN_EXT_D35": "fill under / beside a main exterior beam (D-35 0.80 .. 0.95, outer projection)",
    "BEAM_ANNEX_EXT_D35": "annex exterior beam (D-35 literal 0.10 / 0.25 against printed 0.30+, source conflict)",
    "BEAM_ANNEX_INT_D33": "annex interior beam (top +0.25, D >= 0.30): below EG, no fill",
    "BEAM_ANNEX_INT_D34": "annex interior beam (top +0.25, D 0.30 / 0.40): below EG, no fill",
    "BEAM_COURT": "court beam (section and top not printed: +0.10 .. +0.95)",
}


def sha(rel):
    return hashlib.sha256((RES / rel).read_bytes()).hexdigest()


def _check_pins():
    want = json.loads(PINNED.read_text())
    for rel in want:
        got = sha(rel)
        if got != want[rel]:
            raise SystemExit(f"{rel}: sha256 differs from the pinned merged file (edited input)")
        PINS[rel] = got


def _csv(rel):
    with open(RES / rel, newline="") as f:
        return list(csv.DictReader(f))


def _idx(rel):
    return json.loads((RES / rel).read_text())


def lines_equal():
    a = _idx("agents_t687/out/LINE_INDEX_V3_0_69.json")
    k = lambda i, c: sorted((x["element_id"], x["line_id"], x["class"], x["measured_net"], x["held_low"],  # noqa
                             x["held_high"]) for x in i["lines"] if x["item_code"].startswith(c))
    for rel in ("agents_t722/out/LINE_INDEX_V3_0_73.json", "agents_t717/out/LINE_INDEX_V3_0_74.json"):
        b = _idx(rel)
        for c in ("STR.EARTH.", "STR.CONC.GROUND_SLAB"):
            assert k(a, c) == k(b, c), f"{c} lines moved between V3.0.69 and {b['candidate_version']}"
    return b                                       # the newest candidate (V3.0.74)


# -------------------------------------------------------------------------------------------- (a) Z2 recon ----

def z2_recon(idx):
    Z = json.loads((RES / "agents_t700/ZONES_T700.json").read_text())["z2"]
    gs = {x["element_id"].split(":")[-1]: x["line_id"] for x in idx["lines"]
          if x["item_code"] == "STR.CONC.GROUND_SLAB"}
    terms = []
    for p in Z["panels"]:
        cell = p["cell"].split("/")[0]
        w = Z["panel_basis"][p["cell"]]
        cls = ("PANEL_HELD_LEVEL" if p["depth_m"][0] != p["depth_m"][1] else
               "PANEL_ANNEX_030" if "+0.30" in w else "PANEL_MAIN_100")
        terms.append({"id": f"{gs[cell]} {p['cell']}", "kind": "PANEL", "area_m2": p["area_m2"],
                      "fill_m3": p["fill_m3"], "class": cls, "cause": f"{CAUSE[cls]} [{w}]",
                      "depth_m": p["depth_m"]})
    for b in Z["beams"]:
        cls = "BEAM_" + b["class"]
        terms.append({"id": f"GB run {b['run']}", "kind": "OUTSIDE_PLAN", "fill_m3": b["fill_m3"], "class": cls,
                      "cause": f"{CAUSE[cls]} [L {b['L_m']} m, readings {b['readings']}]"})
    assert len({t["id"].split()[0] for t in terms if t["kind"] == "PANEL"}) == 26
    rec = R.reconcile_plan_x_depth(terms, OWNER_DEPTH, owner_plan_m2=216.40885,
                                   zone_ends=Z["EG"]["zone"]["fill_m3"])
    for r, t in zip(rec["terms"], terms):
        r["depth_m"] = t.get("depth_m")
    return rec, Z


# ------------------------------------------------------------------------------------------ (b) the balance ----

def scenario_a():
    """the candidate of record: T-505's terms (V3.0.50) checked figure by figure against V3.0.73"""
    return A505.terms()


def scenario_b(idx, a_terms):
    form = _csv("agents_t700/WIRING_T700.csv")
    ew = {x["line_id"]: x for x in idx["lines"] if x["item_code"].startswith("STR.EARTH.")}
    cand = {k: v["element_id"] for k, v in ew.items() if v["item_code"] != "STR.EARTH.DISPOSAL"}
    roles = {k: ROLE[v["item_code"]] for k, v in ew.items() if k in cand}
    st = {t["line_id"]: t["status"] for t in a_terms if t["low"] is not None}
    rows, exposure = [], None
    num = lambda s: None if s in ("", None) else float(s)  # noqa: E731
    for r in form:
        r = dict(r, value_m3=num(r["value_m3"]), low_m3=num(r["low_m3"]), high_m3=num(r["high_m3"]))
        if r["line_id"] == EXPOSURE:
            exposure = {"line_id": EXPOSURE, "low_m3": r["low_m3"], "high_m3": r["high_m3"],
                        "why": "HELD BOUNDED_EXPOSURE (T-497, R-T497-1): in plot .. with beyond-plot; its bound "
                               "stays beside, never summed (as T-505)"}
            r = dict(r, bound="BLANK", low_m3=None, high_m3=None,
                     missing_input=r["missing_input"] or "BOUNDED_EXPOSURE")
        if r["element_id"] in NEW_STATUS and r["line_id"].startswith("L-"):
            st[r["line_id"]] = NEW_STATUS[r["element_id"]][0]
        rows.append(r)
    terms, beside = R.restate_terms(rows, cand, roles, st)
    beside["exposure"] = exposure
    return terms, beside, form


def run_balance(T):
    return B.balance(T, rho_insitu=B.density(None, B.HELD, kind="INSITU"),
                     rho_target=B.density(None, B.HELD, kind="PLACEMENT_TARGET"),
                     suit=B.suitability(), loss_reuse=B.loss(B.REUSE), loss_import=B.loss(B.IMPORT),
                     bulk=B.bulking(), contract_basis=None)


def closure(res, T):
    """the s = 0 ends against the closed lines, residual (T-509 acceptance: residual 0)"""
    e_hi = sum(t["high"] for t in T if t["role"] == B.EXC and t["low"] is not None)
    d_hi = sum(t["high"] for t in T if t["role"] == B.FILL and t["low"] is not None)
    d = res["disposal_insitu_m3"]["high"]["value"]
    i = res["import_compacted_m3"]["high"]["value"]
    return {"disposal_s0_m3": d, "sum_closed_excavation_high_m3": round(e_hi, 6),
            "residual_disposal_m3": round(d - e_hi, 6), "import_s0_m3": i,
            "sum_closed_fill_high_m3": round(d_hi, 6), "residual_import_m3": round(i - d_hi, 6)}


def end_text(e):
    return B.describe_end(e)


# ------------------------------------------------------------------------------------------- (c) wiring ----

def wiring_t509(resA, resB, cA, cB, beside_b):
    f = lambda e: "" if e["value"] is None else f"{e['value']:.6f}"  # noqa: E731
    q = lambda e: e["qualifier"]  # noqa: E731
    rows = []
    for tag, res, c, pre in (("A", resA, cA, "candidate of record (V3.0.50 .. V3.0.74 earthworks lines unchanged): "
                                              "T-509 as queued"),
                             ("B", resB, cB, "AFTER the T-695 / T-700 wiring rows land in the candidate (straps, "
                                             "annex, Z2 ranges, three calculated zeros); never before")):
        dl, im = res["disposal_insitu_m3"], res["import_compacted_m3"]
        rows.append({"scenario": tag, "precondition": pre, "family": "B1-04", "line_id": DISPOSAL_LINE,
                     "element_id": "EW-T350:B1-04:ALL", "quantity": "disposal in situ (payable basis: contract "
                     "silent -> in situ)", "low_end": "HELD", "high_end_m3": f(dl["high"]),
                     "high_qualifier": q(dl["high"]), "state": res["state"],
                     "residual_m3": c["residual_disposal_m3"],
                     "held": "; ".join(dl["low"]["missing"])})
        rows.append({"scenario": tag, "precondition": pre, "family": "B1-04 (beside)", "line_id": "",
                     "element_id": "import (no candidate line)", "quantity": "import compacted, s = 0 end",
                     "low_end": "HELD", "high_end_m3": f(im["high"]), "high_qualifier": q(im["high"]),
                     "state": "BESIDE", "residual_m3": c["residual_import_m3"],
                     "held": "; ".join(im["low"]["missing"])})
    for a in beside_b["at_least"]:
        rows.append({"scenario": "B", "precondition": "beside, never summed", "family": "B1-02/03", "line_id":
                     a["line_id"], "element_id": a["zone"], "quantity": f"{a['role']} AT_LEAST (beside)",
                     "low_end": f"{a['at_least_m3']:.6f}", "high_end_m3": "", "high_qualifier": "", "state":
                     "BESIDE", "residual_m3": "", "held": a["missing"]})
    for a in beside_b["not_entered"] + [beside_b["exposure"]]:
        rows.append({"scenario": "B", "precondition": "beside, never summed", "family": "", "line_id":
                     a["line_id"], "element_id": a.get("element_id", ""), "quantity": "bounded line not entered",
                     "low_end": f"{a['low_m3']:.6f}", "high_end_m3": f"{a['high_m3']:.6f}", "high_qualifier": "",
                     "state": "BESIDE", "residual_m3": "", "held": a["why"]})
    return rows


def run(write=True):
    _check_pins()
    idx = lines_equal()
    rec, Z = z2_recon(idx)
    A = scenario_a()
    ew = {x["line_id"]: x for x in idx["lines"] if x["item_code"].startswith("STR.EARTH.")}
    for t in A:                                    # T-505's terms are the V3.0.73 lines (figures)
        x = ew[t["line_id"]]
        if t["low"] is not None:
            got = (x["measured_net"], x["measured_net"]) if x["measured_net"] is not None else \
                (x["held_low"], x["held_high"])
            assert (t["low"], t["high"]) == got, (t["line_id"], t["low"], t["high"], got)
    s505 = json.loads((RES / "agents_t505/summary_t505.json").read_text())
    Bt, beside, form = scenario_b(idx, A)
    resA, resB = run_balance(A), run_balance(Bt)
    for k in ("disposal_insitu_m3", "import_compacted_m3"):
        assert resA[k]["high"]["value"] == s505[k]["high"]["value"], k
    cA, cB = closure(resA, A), closure(resB, Bt)
    diff = R.term_diff(A, Bt)
    zones = [{"zone": t["zone"], "line_id": t["line_id"], "role": t["role"], "low_m3": t["low"],
              "high_m3": t["high"], "bound": "BLANK" if t["low"] is None else
              "ZERO_BY_GEOMETRY" if t["high"] == 0.0 else "VALUE" if t["low"] == t["high"] else "RANGE"} for t in Bt]
    for a in beside["at_least"]:
        z = next(x for x in zones if x["line_id"] == a["line_id"])
        z.update(low_m3=a["at_least_m3"], high_m3=None, bound="AT_LEAST")
    dm = R.dry_mass_inputs(zones)
    t700 = {"Z1-PIT-FF", "Z1-TRENCH-ANNEX", "Z2"}
    for r in dm:
        r["t700_zone"] = r["zone"] in t700
    wire = wiring_t509(resA, resB, cA, cB, beside)
    be = {k: R.break_even_yield(r) for k, r in (("A", resA), ("B", resB))}
    keep = lambda r: {k: r[k] for k in ("excavation", "fill_demand", "disposal_insitu_m3",  # noqa: E731
                                        "import_compacted_m3", "state", "loss_reuse_insitu_m3",
                                        "import_procurement", "payable")}
    summary = {
        "task": "T-708", "rules": R.RULES, "candidate": idx["candidate_version"], "inputs_sha256": dict(PINS),
        "z2_reconciliation": {"owner_m3": rec["owner_m3"], "owner_plan_m2": rec["owner_plan_m2"],
                              "owner_depth_m": rec["owner_depth_m"], "ends": rec["ends"],
                              "terms": len(rec["terms"])},
        "balance": {"A_candidate_of_record": {"closure": cA, "disposal": [end_text(e) for e in
                                                                          resA["disposal_insitu_m3"].values()],
                                              "import": [end_text(e) for e in resA["import_compacted_m3"].values()],
                                              "E": [resA["excavation"]["low"], resA["excavation"]["high"],
                                                    len(resA["excavation"]["held_lines"])],
                                              "D": [resA["fill_demand"]["low"], resA["fill_demand"]["high"],
                                                    len(resA["fill_demand"]["held_lines"])]},
                    "B_t695_t700_geometry": {"closure": cB, "disposal": [end_text(e) for e in
                                                                         resB["disposal_insitu_m3"].values()],
                                             "import": [end_text(e) for e in resB["import_compacted_m3"].values()],
                                             "E": [resB["excavation"]["low"], resB["excavation"]["high"],
                                                   len(resB["excavation"]["held_lines"])],
                                             "D": [resB["fill_demand"]["low"], resB["fill_demand"]["high"],
                                                   len(resB["fill_demand"]["held_lines"])],
                                             "beside": beside},
                    "line_changes_A_to_B": diff,
                    "s0_change_m3": {"disposal": round(cB["disposal_s0_m3"] - cA["disposal_s0_m3"], 6),
                                     "import": round(cB["import_s0_m3"] - cA["import_s0_m3"], 6)}},
        "break_even_yield_closed_parts": be, "dry_mass_inputs": dm, "wiring_rows": len(wire)}
    if write:
        with open(HERE / "RECON_Z2_T708.csv", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["term", "kind", "class", "area_m2", "depth_m", "owner_m3", "engine_low_m3",
                        "engine_high_m3", "delta_low_m3", "delta_high_m3", "cause"])
            for r in rec["terms"]:
                w.writerow([r["id"], r["kind"], r["class"], "" if r["area_m2"] is None else r["area_m2"],
                            "" if not r["depth_m"] else " .. ".join(f"{x:g}" for x in sorted(set(r["depth_m"]))),
                            f"{r['owner_m3']:.6f}", f"{r['engine_m3'][0]:.6f}", f"{r['engine_m3'][1]:.6f}",
                            f"{r['delta_m3'][0]:.6f}", f"{r['delta_m3'][1]:.6f}", r["cause"]])
        with open(HERE / "WIRING_T708.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(wire[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(wire)
        (HERE / "BALANCE_T708.json").write_text(json.dumps({"A": keep(resA), "B": keep(resB)}, indent=1,
                                                           sort_keys=True) + "\n")
        (HERE / "summary_t708.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return summary, rec, resA, resB


if __name__ == "__main__":
    s, *_ = run()
    print(json.dumps({k: s[k] for k in ("z2_reconciliation", "balance")}, indent=1)[:6000])
