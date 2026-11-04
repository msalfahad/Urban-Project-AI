"""ARCH_TAKEOFF_V3.0.55 (T-488, stream S): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.54
(engine.source.arch_v30, arch_v301 .. arch_v3054), with ONE new piece, the BLOCKWORK WIRING CONDITIONS of the merged
blockwork basis (T-449 round 3, BLOCKWORK_BASIS_RULES_V1) as the T-482 verdict settled them (BLOCKWORK_CONDITIONS_V1):

  ROOF_DATUM      (R-MAS-ROOF-DATUM-1) a wall of a storey under a ROOF-ONLY plate whose structural top is not printed
                  (top = finished roof level - b_r, b_r the unprinted roof build-up) has no structural storey: the
                  wall is HELD ON ROOF DATUM with its terms U - L x b_r (U = net at b_r = 0, an UPPER bound, never a
                  quantity; L = its closable length), never the finished-chain storey (FINISHED_AS_STRUCTURAL refused).
                  A part line all of whose walls are roof-datum walls becomes BLOCKED_RFI blank by name; a part line
                  with other walls keeps them and drops only the held ones.
  WIDTH_CONFLICT  (R-MAS-WIDTH-CONFLICT-1) a wall whose two printed readings of the member over it differ (a designer
                  conflict) is never released at one end (CONFLICT_ONE_END refused): it leaves its part line and is
                  named on its parent as CONFLICT [low, high] by its designer item, outside every total.
  DROP_UPPER      a drop wall's U (U - L x d) is the MAX over the conflict readings (an upper bound is its high end);
                  the term is restated on the parent, never evaluated.
  PARAPET_RUN     (R-MAS-PARAPET-RUN-1) a parapet run's block alternative is taken on the run as drawn at the roof
                  level, never on the floor outline below; a run with no alternative booked gets its [0, hi] beside.
                  Block alternatives are BESIDE the parapet line (exclusive with the RC above the upstand): no total moves.

MAS.BLOCK / ARCH.WALL_PANEL carry the same m2; ARCH.WALL_VOLUME = m2 x the line thickness (asserted per wall).

R-T488-1 (every villa): (1) the storey of a wall is the structural top of the plate under it to the structural top of
the plate over it (Q-60 A, Q-72); a roof-only plate with no printed structural level holds every wall under it ON ROOF
DATUM (D-39-type item), never from the architectural finished chain; (2) a width conflict is a range on the parent,
never one end on a released line; (3) held stays held: blank, never 0, never a range in the BOQ; the terms and ranges
are named on the record and the RFI question; (4) the host MAS.BLOCK contract area takes no lintel face (element
register ruling 'RC LINTEL', R-T487-1 (3)): lintel lines and their records are byte-identical; a lintel whose host line
becomes held is named in the downstream list for the material side (T-498).

Refused (InputsError / ValueError, nothing written): a stale basis (a wall's carried figure is not the candidate's
piece, or not U - L x the what-if build-up the carried storey implies); a held part line that still carries a figure;
a wall twice; a conflict whose carried figure is not its low end; a range with low > high; an upper bound below the
carried U; a parapet run whose stated 'before' is not the line's; a candidate that already carries V3.0.55 records.
Every other line is byte-identical to V3.0.54 (asserted); totals move only in MAS.BLOCK, ARCH.WALL_PANEL and
ARCH.WALL_VOLUME (asserted). Files: V3_0_55_BOQ_LINES.json / .csv, V3_0_55_INTEGRATION_LEDGER.json / .csv,
V3_0_55_DIFF.csv, V3_0_55_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3026 as A3026
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3050 as A3050
from engine.source import arch_v3053 as A3053
from engine.source import arch_v3054 as A3054

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: holds / restates Checker-verified basis conditions; adds no value
METHOD = "ARCH_TAKEOFF_V3.0.55"
EXTENDS = A3054.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T488_ARCH_V3_0_55"
INPUTS_SCHEMA = "URBAN_V3055_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3055_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3054.InputsError
_r = A3050._r
_fmt = A3050._fmt
RULE_ID, RULE_VERSION = "R-T488-1", "T-488"
REC_KEY = "blockwork_v3055"
FILL_KEY = "blockwork_fill_v3026"
SUPERSEDED_KEY = "blockwork_fill_v3026_superseded_v3055"
P_WIRING = "BLOCKWORK_WIRING"
ITEMS = {"MAS.BLOCK": "m2", "ARCH.WALL_PANEL": "m2", "ARCH.WALL_VOLUME": "m3"}
VOLUME_ITEM = "ARCH.WALL_VOLUME"
PARAPET_KEY = "parapet_rc_v3023"
TOL = 1e-4
MAX_WALL_M = 100.0         # a closable wall length above this is not metres (mm / cm refused)
ROUND_TOL = 5e-4 + 1e-9     # carried figures are printed to 3 dp: U - L x what-if agrees within half a unit
EVIDENCE = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")   # WORKFLOW_CONTROLS s.5
ROOF, CONFLICT, DROP_UP = "HELD ON ROOF DATUM", "CONFLICT", "DROP_UPPER"

PIECES = {
    P_WIRING: {"module": "engine/source/arch_v3055.py (blockwork wiring conditions on the merged fill: roof-datum walls "
                         "HELD U - L x b_r, width conflicts as named ranges, drop U at its high end, parapet block "
                         "alternatives on the roof-level run)",
               "policy": "BLOCKWORK_WIRING_V1", "rule_id": "R-T488-1 (on BLOCKWORK_BASIS_RULES_V1 / "
                                                           "BLOCKWORK_CONDITIONS_V1)",
               "owner_rules": ["Q-60 A (a wall rises to the soffit of the member over it)",
                               "Q-72 (heights to the structural slab / roof underside)",
                               "Q-73 (every actual opening deducted; only masonry that exists)",
                               "Q-54 B / D-39 (roof datum and build-up HELD until printed)",
                               "Q-61 (a contradicting member is held, the range visible, never one end)",
                               "UP-QTY-STATUS-001 (held is blank or a range, never 0)",
                               "ELEMENT_REGISTER rulings RC LINTEL vs host masonry; TOP-STOREY WALL HEIGHT vs ROOF "
                               "BUILD-UP"],
               "owner_manual_method": "block wall m2 = length x clear height (structural floor to the underside of "
                                      "the beam / slab over it) less every opening; one line per storey and "
                                      "thickness; volume = m2 x thickness",
               "drawing_method": "T-449 r3 register (BLOCKWORK_BASIS_RULES_V1, 260 entries reproduced from the drawn "
                                 "pieces, printed soffit depths and declared storeys) under the T-482 conditions "
                                 "(BLOCKWORK_CONDITIONS_V1: plate tops from the structural set, the roof-only plate "
                                 "has no printed level -> U - L x b_r; D-27 width readings; the roof-level parapet "
                                 "run read straight)"},
}
WAITING = dict(A3054.WAITING)
WAITING.update({
    "T488_ROOF_BUILDUP": "the roof-storey walls stay HELD ON ROOF DATUM until the roof build-up b_r (or the structural "
                         "top of the roof-only plate) is printed (D-39); their terms U - L x b_r are on the record",
    "T488_WIDTH_CONFLICT": "a width-conflict wall stays CONFLICT [low, high] until the designer answers its item "
                           "(D-27 type)",
    "T488_DROP_LENGTH": "a drop wall's d-coefficient L stays as carried until its re-clip (T-288); only U is restated",
    "T488_LINTEL_HOSTS": "a REQUIRED lintel whose host line becomes held keeps its line; its host face leaves the "
                         "material base of a held line (T-498)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=True, hi=1e5):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'} (held is never 0)")
    if x > hi:
        raise InputsError(f"{where}: {x} is above {hi} (not a quantity in m / m2)")
    return float(x)


def _rng(r, where, hi=1e5):
    if not isinstance(r, (list, tuple)) or len(r) != 2:
        raise InputsError(f"{where}: a range is [low, high]")
    lo, hh = _num(r[0], where + " low", pos=False, hi=hi), _num(r[1], where + " high", pos=False, hi=hi)
    if lo > hh + 1e-12:
        raise InputsError(f"{where}: low {lo} > high {hh}")
    return [lo, hh]


def load_inputs(doc, project_id=None):
    """URBAN_V3055_INPUTS_V1 or None:
        {"schema", "project", "sources": {task: {file, sha256, task, merge_commit, checker_run}},
         "roof_datum": {"item", "plate", "what_if_buildup_m", "walls": [{wall_id, parent_line_id, thickness_m,
                        carried_m2, upper_m2, length_m, kind WHOLE | ESTABLISHED_PART, evidence_status, source_task}]},
         "conflicts": [{wall_id, parent_line_id, thickness_m, carried_m2, range_m2 [lo, hi], item, low_reading,
                        high_reading, source_task}],
         "drop_upper": [{wall_id, parent_line_id, thickness_m, carried_upper_m2, upper_m2, item, source_task}],
         "parapets": [{run, element_id (<parapet line element>:<run>), before_m2 [lo, hi] | null, after_m2 [lo, hi], centreline_m, height_m,
                       why, source_task}]}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    _need(doc, ("sources",), "inputs")
    S = {}
    for t, s in doc["sources"].items():
        _need(s, ("file", "sha256", "task", "merge_commit", "checker_run"), f"source {t}")
        S[t] = s
    seen = set()

    def src(x, where):
        if x.get("source_task") not in S:
            raise InputsError(f"{where}: source_task {x.get('source_task')!r} is not a declared merged source")

    def once(w, where):
        if w in seen:
            raise InputsError(f"{where}: wall {w} named twice (one wall, one condition)")
        seen.add(w)

    roof = doc.get("roof_datum") or {"walls": []}
    walls = []
    if roof.get("walls"):
        _need(roof, ("item", "plate", "what_if_buildup_m"), "roof_datum")
        bw = _num(roof["what_if_buildup_m"], "roof_datum what_if_buildup_m", pos=False, hi=1.0)
        for w in roof["walls"]:
            where = f"roof wall {w.get('wall_id')}"
            _need(w, ("wall_id", "parent_line_id", "thickness_m", "carried_m2", "upper_m2", "length_m", "kind",
                      "evidence_status"), where)
            src(w, where)
            once(w["wall_id"], where)
            t = _num(w["thickness_m"], where + " thickness", hi=1.0)
            c, u = (_num(w[k], f"{where} {k}") for k in ("carried_m2", "upper_m2"))
            L = _num(w["length_m"], f"{where} length_m", hi=MAX_WALL_M)
            if w["kind"] not in ("WHOLE", "ESTABLISHED_PART"):
                raise InputsError(f"{where}: kind {w['kind']!r}")
            if w["evidence_status"] not in EVIDENCE:
                raise InputsError(f"{where}: evidence status {w['evidence_status']!r}")
            if abs((u - L * bw) - c) > ROUND_TOL:
                raise InputsError(f"{where}: carried {c} is not U - L x {bw} = {_r(u - L * bw)} (the carried storey "
                                  f"is not the what-if the basis names: stale basis)")
            walls.append(dict(w, thickness_m=t, carried_m2=c, upper_m2=u, length_m=L))
    conf = []
    for x in doc.get("conflicts") or ():
        where = f"conflict {x.get('wall_id')}"
        _need(x, ("wall_id", "parent_line_id", "thickness_m", "carried_m2", "range_m2", "item", "low_reading",
                  "high_reading"), where)
        src(x, where)
        once(x["wall_id"], where)
        lo, hi = _rng(x["range_m2"], where)
        c = _num(x["carried_m2"], where + " carried")
        if abs(c - lo) > TOL or hi - lo <= 1e-9:
            raise InputsError(f"{where}: the carried figure {c} is the low end of [{lo}, {hi}] with a width > 0")
        conf.append(dict(x, thickness_m=_num(x["thickness_m"], where, hi=1.0), carried_m2=c, range_m2=[lo, hi]))
    drops = []
    for x in doc.get("drop_upper") or ():
        where = f"drop {x.get('wall_id')}"
        _need(x, ("wall_id", "parent_line_id", "thickness_m", "carried_upper_m2", "upper_m2", "item"), where)
        src(x, where)
        once(x["wall_id"], where)
        cu, u = _num(x["carried_upper_m2"], where), _num(x["upper_m2"], where)
        if u < cu - 1e-9:
            raise InputsError(f"{where}: U {u} below the carried {cu} (U is an upper bound: its high end)")
        drops.append(dict(x, thickness_m=_num(x["thickness_m"], where, hi=1.0), carried_upper_m2=cu, upper_m2=u))
    pars = []
    for x in doc.get("parapets") or ():
        where = f"parapet {x.get('run')}"
        _need(x, ("run", "element_id", "after_m2", "centreline_m", "height_m", "why"), where)
        if ":" not in x["element_id"] or x["element_id"].rsplit(":", 1)[1] != x["run"]:
            raise InputsError(f"{where}: element {x['element_id']!r} is not '<parapet line element>:<run>'")
        src(x, where)
        if x["run"] in seen:
            raise InputsError(f"{where}: run named twice")
        seen.add(x["run"])
        b = None if x.get("before_m2") is None else _rng(x["before_m2"], where + " before")
        a = _rng(x["after_m2"], where + " after")
        if a[0] != 0.0:
            raise InputsError(f"{where}: a block alternative is [0, hi] (exclusive with the RC above the upstand)")
        if x.get("upstand_m") is not None and abs(a[1] - x["centreline_m"] * (x["height_m"] - x["upstand_m"])) > TOL:
            raise InputsError(f"{where}: high {a[1]} is not centreline x (h - upstand)")
        pars.append(dict(x, before_m2=b, after_m2=a, centreline_m=_num(x["centreline_m"], where),
                         height_m=_num(x["height_m"], where, hi=10.0)))
    if not (walls or conf or drops or pars):
        raise InputsError("inputs name no condition")
    return dict(doc, _sources=S, _roof=dict(roof, walls=walls), _conflicts=conf, _drops=drops, _parapets=pars)


# ================================================================================================ helpers
def _inp(ln):
    return (ln.get("calculation") or {}).get("inputs") or {}


def _factor(code, t):
    return t if code == VOLUME_ITEM else 1.0


def _rec(doc, **kw):
    return dict({"policy": PIECES[P_WIRING]["policy"], "rule_id": RULE_ID, "rule_version": RULE_VERSION,
                 "sources": {k: {x: v[x] for x in ("file", "sha256", "task", "merge_commit", "checker_run")}
                             for k, v in doc["_sources"].items()}, "release_status": "NOT RELEASED"}, **kw)


def _term(u, L, sym, unit):
    return f"{_fmt(_r(u, 6))} - {_fmt(_r(L, 6))} x {sym} {unit}"


def _ver(doc):
    S = doc["_sources"]
    return {"task": "T-488", "merge_commits": [s["merge_commit"] for s in S.values()],
            "verifier_runs": [s["checker_run"] for s in S.values()],
            "ledgers": [s["file"] for s in S.values()]}


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). REPLACE changes only (part lines held or reduced, parents restated, parapet records)."""
    if not doc:
        return [], {"piece": P_WIRING, "state": "NO_PROJECT_INPUT"}
    if any(_inp(ln).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.55 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    roof = {w["wall_id"]: w for w in doc["_roof"]["walls"]}
    conf = {x["wall_id"]: x for x in doc["_conflicts"]}
    drops = {x["wall_id"]: x for x in doc["_drops"]}
    parents = {}
    for w in list(roof.values()) + list(conf.values()) + list(drops.values()):
        p = by.get(w["parent_line_id"])
        if p is None or p["item_code"] != "MAS.BLOCK":
            raise InputsError(f"wall {w['wall_id']}: parent {w['parent_line_id']} is not a MAS.BLOCK line of the "
                              f"candidate (stale basis)")
        prec = _inp(p).get(FILL_KEY) or {}
        if prec.get("action") not in ("PARENT", "RESTATE"):
            raise InputsError(f"wall {w['wall_id']}: {p['line_id']} is not a held parent of the fill")
        if abs(prec.get("thickness_m", -1) - w["thickness_m"]) > 1e-9:
            raise InputsError(f"wall {w['wall_id']}: thickness {w['thickness_m']} is not its parent's "
                              f"{prec.get('thickness_m')}")
        parents.setdefault(p["line_id"], p)
    # the same parent in every item: (floor, element id) of the MAS.BLOCK parent -> parents of the 3 items
    fam = {}
    for ln in prev:
        if ln["item_code"] in ITEMS and _inp(ln).get(FILL_KEY, {}).get("action") in ("PARENT", "RESTATE"):
            fam[(ln["item_code"], ln["location"].get("floor"), ln["location"].get("element_id"))] = ln
    changes, log = [], {"piece": P_WIRING, "state": "RUN", "sources": sorted(doc["_sources"]), "by_item": {},
                        "roof_walls": len(roof), "conflicts": len(conf), "drops": len(drops),
                        "parapets": len(doc["_parapets"]), "lines": {}}
    touched_walls = {c: set() for c in ITEMS}
    for mp in sorted(parents.values(), key=lambda x: x["line_id"]):
        for code, unit in ITEMS.items():
            par = fam.get((code, mp["location"].get("floor"), mp["location"].get("element_id")))
            if par is None:
                raise InputsError(f"{mp['line_id']}: no {code} parent twin (the three items move together)")
            t = _inp(par)[FILL_KEY]["thickness_m"]
            f = _factor(code, t)
            part_ids = dict(_inp(par)[FILL_KEY].get("parts") or {})
            new_held, held_part_ids, reduced = [], {}, {}
            for pname, pid in part_ids.items():
                pl = by.get(pid)
                if pl is None:
                    raise InputsError(f"{par['line_id']}: part {pid} not in the candidate")
                prc = _inp(pl).get(FILL_KEY) or {}
                keep, gone = [], []
                for pc in prc.get("pieces") or ():
                    w = roof.get(pc["id"]) or conf.get(pc["id"])
                    if w is None:
                        keep.append(pc)
                        continue
                    want = (w["carried_m2"]) * f
                    if abs(pc["value"] - _r(want)) > TOL * max(1.0, f * 10):
                        raise InputsError(f"{code} {pc['id']}: candidate piece {pc['value']} is not the basis "
                                          f"carried {_r(want)} (stale basis)")
                    if pc["id"] in touched_walls[code]:
                        raise InputsError(f"{code} {pc['id']}: wall in two part lines")
                    touched_walls[code].add(pc["id"])
                    gone.append((pc, w))
                if not gone:
                    continue
                after = copy.deepcopy(pl)
                before_q = A3018._before_rec(pl)
                gone_txt = []
                for pc, w in gone:
                    if w["wall_id"] in roof:
                        gone_txt.append(f"{w['wall_id']} {ROOF} {_term(w['upper_m2'] * f, w['length_m'] * f, 'b_r', unit)}"
                                        f" ({doc['_roof']['item']})")
                    else:
                        gone_txt.append(f"{w['wall_id']} {CONFLICT} [{_fmt(_r(w['range_m2'][0] * f, 6))}, "
                                        f"{_fmt(_r(w['range_m2'][1] * f, 6))}] {unit} ({w['item']})")
                rec = _rec(doc, action="PART_HELD" if not keep else "PART_REDUCED", parent_line_id=par["line_id"],
                           part=pname, before=before_q, removed=[pc["id"] for pc, _ in gone], kept=[pc["id"] for pc in keep],
                           removed_terms=gone_txt)
                if keep:
                    nprc = dict(copy.deepcopy(prc), pieces=copy.deepcopy(keep))
                    v = _r(sum(pc["value"] for pc in keep))
                    nprc["value"] = v
                    after["calculation"]["inputs"][FILL_KEY] = nprc
                    after["measured_net"] = v
                    if pl.get("gross") is not None:
                        after["gross"] = v
                    terms = " + ".join(f"{x['id']}{' (part)' if x['kind'] == 'ESTABLISHED_PART' else ''} {x['value']}"
                                       for x in keep)
                    after["calculation"]["formula"] = (f"{terms} = {_r(v, 6)} {unit} ({prc['status']}, "
                                                       f"{prc['block_type']} t {t} m) | {METHOD}: left for "
                                                       f"{'; '.join(gone_txt)}")[:700]
                    reduced[pname] = pid
                    log["lines"][pid] = {"action": "PART_REDUCED", "before": pl.get("measured_net"), "after": v}
                else:
                    after["calculation"]["inputs"][SUPERSEDED_KEY] = after["calculation"]["inputs"].pop(FILL_KEY)
                    after["evidence_state"] = "BLOCKED_RFI"
                    after["measured_net"] = None
                    after["gross"] = None
                    after["bounded_range"] = None
                    q = (f"HELD (blank, never 0; terms never evaluated): {'; '.join(gone_txt)}")[:900]
                    after["rfi"] = {"question": q, "unlocks": after["location"].get("element_id")}
                    after["calculation"]["formula"] = (f"HELD by {RULE_ID}: every wall of this part line is held "
                                                       f"({len(gone)}): {'; '.join(gone_txt)}")[:700]
                    held_part_ids[pname] = pid
                    log["lines"][pid] = {"action": "PART_HELD", "before": pl.get("measured_net"), "after": None}
                after["calculation"]["inputs"][REC_KEY] = rec
                A305._note(after, f"{METHOD}: {rec['action']} by {RULE_ID} (T-449 r3 basis, T-482 conditions)")
                after = _validate(after)
                for pc, w in gone:
                    new_held.append({"wall": w["wall_id"], "kind": "ROOF_DATUM" if w["wall_id"] in roof else
                                     "CONFLICT", "item": (doc["_roof"]["item"] if w["wall_id"] in roof else w["item"]),
                                     "terms": gone_txt[[g[0]["id"] for g in gone].index(w["wall_id"])],
                                     "from_part_line": pid,
                                     **({"upper": _r(w["upper_m2"] * f, 6), "length": _r(w["length_m"] * f, 6)}
                                        if w["wall_id"] in roof else
                                        {"range": [_r(w["range_m2"][0] * f, 6), _r(w["range_m2"][1] * f, 6)]})})
                down = [f"{code} {pname} {_fmt(pl.get('measured_net'))} -> "
                        f"{'HELD blank' if not keep else _fmt(after['measured_net'])} {unit}"]
                changes.append(A305._change(P_WIRING, "REPLACE", pl, after, step=rec["action"],
                                            drawing_reference="; ".join(s["file"] for s in doc["_sources"].values()),
                                            held=[{"what": f"{code} {pc['id']}", "why": txt[:300], "range": None,
                                                   "scenario": None} for (pc, _w), txt in zip(gone, gone_txt)],
                                            downstream=down, verification=_ver(doc),
                                            evidence_status="HELD" if not keep else prc["status"], group=code,
                                            parent_line_id=par["line_id"]))
            # roof walls / conflicts that were HELD on the parent already, and the drop U restatements
            pr_after = copy.deepcopy(par)
            prc = copy.deepcopy(_inp(par)[FILL_KEY])
            still = prc.get("still_held") or []
            drop_txt = []
            for x in drops.values():
                if x["parent_line_id"] != mp["line_id"]:
                    continue
                hit = [h for h in still if h.get("wall") == x["wall_id"] and h.get("kind") == "DROP"]
                if len(hit) != 1:
                    raise InputsError(f"drop {x['wall_id']}: not one DROP term on {par['line_id']}")
                h = hit[0]
                if abs(h["upper_at_d0"] - x["carried_upper_m2"] * f) > TOL * max(1.0, f * 10):
                    raise InputsError(f"drop {x['wall_id']}: {code} carried U {h['upper_at_d0']} is not "
                                      f"{_r(x['carried_upper_m2'] * f)} (stale basis)")
                old = h["terms"]
                h["upper_at_d0_before_v3055"] = h["upper_at_d0"]
                h["upper_at_d0"] = _r(x["upper_m2"] * f, 6)
                h["terms"] = f"{_r(h['upper_at_d0'], 4)} - {_r(h['drop_coefficient'], 4)} d"
                h["upper_source"] = f"{RULE_ID}: U = max over the {x['item']} readings"
                drop_txt.append((x["wall_id"], old, h["terms"]))
            if not (new_held or drop_txt):
                continue
            # a conflict increment named outside (V3.0.26) is now INSIDE the wall's range / its drop U: retire it once
            retired = []
            for x in list(conf.values()) + list(drops.values()):
                if x["parent_line_id"] != mp["line_id"]:
                    continue
                inc = [h for h in still if h.get("wall") == x["wall_id"] and h.get("kind") == "CONFLICT_INCREMENT_OUTSIDE"]
                if len(inc) > 1:
                    raise InputsError(f"{x['wall_id']}: two conflict increments on {par['line_id']}")
                if not inc:
                    continue
                want = (x["range_m2"][1] - x["range_m2"][0]) if x["wall_id"] in conf else \
                    (x["upper_m2"] - x["carried_upper_m2"])
                got = float(str(inc[0]["item"]).split(" ")[0])
                if abs(got - _r(want * f, 4)) > TOL * max(1.0, f * 10) and abs(got - want) > TOL:
                    raise InputsError(f"{x['wall_id']}: the named increment {got} is not the condition's "
                                      f"{_r(want, 6)} (stale basis)")
                still.remove(inc[0])
                retired.append(dict(inc[0], retired_by=f"{RULE_ID}: inside the "
                                    f"{'CONFLICT range' if x['wall_id'] in conf else 'drop U (its high end)'}"))
            still.extend(new_held)
            prc["still_held"] = still
            prc["parts"] = {k: v for k, v in part_ids.items() if k not in held_part_ids}
            prc["parts_held_v3055"] = dict(held_part_ids)
            pr_after["calculation"]["inputs"][FILL_KEY] = prc
            q = pr_after["rfi"]["question"]
            if retired:
                gone_ids = {h["wall"] for h in retired}
                key = "CONFLICT_INCREMENT_OUTSIDE: "
                if key not in q:
                    raise InputsError(f"{par['line_id']}: the parent question names no conflict increment (stale)")
                a = q.index(key) + len(key)
                b = min([i for i in (q.find(";", a), q.find(" |", a)) if i >= 0] or [len(q)])
                names = [n.strip() for n in q[a:b].split(",")]
                if not gone_ids <= set(names):
                    raise InputsError(f"{par['line_id']}: increments {sorted(gone_ids)} not in the question (stale)")
                keep = [n for n in names if n not in gone_ids]
                q = (q[:a] + ", ".join(keep) + q[b:]) if keep else (q[:a - len(key)] + q[b:].lstrip("; "))
            for wid, old, new in drop_txt:
                if f"{wid} {old}" not in q:
                    raise InputsError(f"drop {wid}: its term '{old}' is not in the parent question (stale)")
                q = q.replace(f"{wid} {old}", f"{wid} {new}")
            if new_held:
                q = q + " | " + f"{METHOD} {RULE_ID}: " + "; ".join(h["terms"] for h in new_held)
            if len(q) > 1800:
                raise ValueError(f"{METHOD}: the held list of {par['line_id']} does not fit the RFI question")
            pr_after["rfi"] = dict(pr_after["rfi"], question=q)
            carried = "; ".join(f"{k} on {v}" for k, v in prc["parts"].items())
            pr_after["calculation"]["formula"] = (
                f"HELD remainder (blank in the BOQ, never 0): {len(still)} named item(s)"
                + (f" | closable walls carried on their own lines: {carried}" if prc["parts"] else
                   " | no closable wall in this line") + (f" | part lines held by {RULE_ID}: "
                                                         f"{', '.join(held_part_ids.values())}" if held_part_ids
                                                         else ""))[:600]
            pr_after["calculation"]["inputs"][REC_KEY] = _rec(
                doc, action="PARENT_RESTATED", before=A3018._before_rec(par), added_held=new_held,
                retired_increments=retired,
                drop_upper=[{"wall": a, "before": b, "after": c} for a, b, c in drop_txt],
                parts_held=dict(held_part_ids), parts_reduced=dict(reduced))
            A305._note(pr_after, f"{METHOD}: parent restated by {RULE_ID}")
            pr_after = _validate(pr_after)
            changes.append(A305._change(P_WIRING, "REPLACE", par, pr_after, step="PARENT_RESTATED",
                                        drawing_reference="; ".join(s["file"] for s in doc["_sources"].values()),
                                        held=[{"what": f"{code} {h['wall']}", "why": h["terms"][:300], "range":
                                               h.get("range"), "scenario": None} for h in new_held]
                                        + [{"what": f"{code} {a}", "why": f"DROP U restated {b} -> {c}", "range": None,
                                            "scenario": c} for a, b, c in drop_txt],
                                        downstream=[], verification=_ver(doc), evidence_status="HELD", group=code,
                                        parent_line_id=par["line_id"]))
            log["by_item"].setdefault(code, {"held_added": 0, "drops": 0})
            log["by_item"][code]["held_added"] += len(new_held)
            log["by_item"][code]["drops"] += len(drop_txt)
    for code in ITEMS:
        want = set(roof) | set(conf)
        miss = sorted(w for w in want if w not in touched_walls[code])
        if miss:
            raise InputsError(f"{code}: wall(s) {miss} are in no part line and not held on their parent (stale basis)")
    for x in doc["_parapets"]:
        changes.append(_parapet_change(x, by, doc))
    ids = [c["after"]["line_id"] for c in changes]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{METHOD}: a line is changed twice")
    log["changed_lines"] = len(changes)
    return changes, log


def _validate(ln):
    from engine.source import boq_line as BL
    return BL.validate(ln)


def _parapet_change(x, by, doc):
    where = f"parapet {x['run']}"
    el = x["element_id"].rsplit(":", 1)[0]
    hits = [ln for ln in by.values() if (ln.get("location") or {}).get("element_id") == el and _inp(ln).get(PARAPET_KEY)]
    if len(hits) != 1:
        raise InputsError(f"{where}: {len(hits)} parapet line(s) with element {el} carry a {PARAPET_KEY} record (one)")
    ln = hits[0]
    rec = _inp(ln)[PARAPET_KEY]
    s0 = [sum((r.get("block_alternative_m2") or [0, 0])[i] for r in _runs(rec)) for i in (0, 1)]
    b0 = (rec.get("bound") or {}).get("block_alternative_m2")
    if b0 is not None and any(abs(p - q) > 1e-5 for p, q in zip(b0, s0)):
        raise InputsError(f"{where}: the line's block-alternative summary {b0} is not the sum of its runs {s0}")
    hits = [r for r in _runs(rec) if r.get("run") == x["run"]]
    if len(hits) != 1:
        raise InputsError(f"{where}: not one run {x['run']} on {x['line_id']}")
    r0 = hits[0]
    up = (rec.get("upstand") or {}).get("floor_m")
    if up is None or abs(x["after_m2"][1] - x["centreline_m"] * (x["height_m"] - up)) > TOL \
            or abs((r0.get("centreline_m") or [0])[0] - x["centreline_m"]) > TOL:
        raise InputsError(f"{where}: [0, {x['after_m2'][1]}] is not the line's run centreline {r0.get('centreline_m')} "
                          f"x (h {x['height_m']} - upstand {up})")
    b = r0.get("block_alternative_m2")
    if (b is None) != (x["before_m2"] is None) or (b is not None and any(abs(p - q) > TOL for p, q in
                                                                         zip(b, x["before_m2"]))):
        raise InputsError(f"{where}: stated before {x['before_m2']} is not the line's {b} (stale)")
    after = copy.deepcopy(ln)
    arec = _inp(after)[PARAPET_KEY]
    r1 = [r for r in _runs(arec) if r.get("run") == x["run"]][0]
    r1["block_alternative_m2_before_v3055"] = b
    r1["block_alternative_m2"] = [_r(x["after_m2"][0], 6), _r(x["after_m2"][1], 6)]
    r1["block_alternative_note"] = (f"{RULE_ID}: [0, {_fmt(x['centreline_m'])} x ({_fmt(x['height_m'])} - upstand)] on "
                                    f"the run as drawn at roof level; {x['why']}")[:300]
    _restate_parapet_summary(arec)
    after["calculation"]["inputs"][REC_KEY] = _rec(doc, action="PARAPET_BLOCK_ALT", run=x["run"], before_m2=b,
                                                   after_m2=r1["block_alternative_m2"], why=x["why"])
    A305._note(after, f"{METHOD}: block alternative of {x['run']} on the roof-level run by {RULE_ID} (beside)")
    after = _validate(after)
    if after.get("measured_net") != ln.get("measured_net") or after.get("bounded_range") != ln.get("bounded_range") \
            or after["evidence_state"] != ln["evidence_state"]:
        raise ValueError(f"{METHOD}: {where}: a block alternative moved the parapet line's quantity")
    return A305._change(P_WIRING, "REPLACE", ln, after, step="PARAPET_BLOCK_ALT",
                        drawing_reference="; ".join(s["file"] for s in doc["_sources"].values()),
                        held=[{"what": f"block alternative {x['run']}", "why": "beside, exclusive with the RC above "
                               "the upstand; never in a total", "range": r1["block_alternative_m2"], "scenario": None}],
                        downstream=[f"MAS.BLOCK beside: {x['run']} {b} -> {r1['block_alternative_m2']} m2 (no total)"],
                        verification=_ver(doc), evidence_status="UNKNOWN", group=ln["item_code"])


def _runs(rec):
    for k in ("runs", "bound_runs"):
        if isinstance(rec.get(k), list):
            return rec[k]
    b = rec.get("bound") or {}
    if isinstance(b.get("runs"), list):
        return b["runs"]
    return []


def _restate_parapet_summary(rec):
    runs = _runs(rec)
    for holder in (rec, rec.get("bound") or {}):
        if "block_alternative_m2" in holder and isinstance(holder["block_alternative_m2"], list):
            lo = sum((r.get("block_alternative_m2") or [0, 0])[0] for r in runs)
            hi = sum((r.get("block_alternative_m2") or [0, 0])[1] for r in runs)
            holder["block_alternative_m2"] = [_r(lo, 6), _r(hi, 6)]
        if "block_alternative_not_booked" in holder:
            holder["block_alternative_not_booked"] = [r["run"] for r in runs if r.get("block_alternative_m2") is None]


# ================================================================================================ checks
def check_wiring(lines):
    """R-T488-1 on the integrated lines: a PART_HELD line is BLOCKED_RFI blank and its parent names it held; a
    PART_REDUCED line's value is its kept walls; a roof / conflict wall is released on no line of its item; the three
    items carry the same walls (volume = m2 x t). -> summary."""
    out = {"part_held": 0, "part_reduced": 0, "parents": 0, "parapets": 0, "roof_walls": set(), "conflicts": set()}
    by = {ln["line_id"]: ln for ln in lines}
    held_by_item = {c: set() for c in ITEMS}
    for ln in lines:
        rec = _inp(ln).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        if a == "PART_HELD":
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None \
                    or ln.get("bounded_range") is not None or _inp(ln).get(FILL_KEY):
                raise ValueError(f"{METHOD}: held part {ln['line_id']} carries a figure or a live part record")
            par = by.get(rec["parent_line_id"])
            prc = _inp(par).get(FILL_KEY) or {} if par else {}
            if ln["line_id"] not in (prc.get("parts_held_v3055") or {}).values() \
                    or ln["line_id"] in (prc.get("parts") or {}).values():
                raise ValueError(f"{METHOD}: parent of {ln['line_id']} does not name it held")
            out["part_held"] += 1
            held_by_item[ln["item_code"]].update(rec["removed"])
        elif a == "PART_REDUCED":
            prc = _inp(ln).get(FILL_KEY) or {}
            if abs(sum(p["value"] for p in prc.get("pieces") or ()) - (ln.get("measured_net") or -1)) > 1e-6 \
                    or set(rec["removed"]) & {p["id"] for p in prc.get("pieces") or ()}:
                raise ValueError(f"{METHOD}: reduced part {ln['line_id']} is not its kept walls")
            out["part_reduced"] += 1
            held_by_item[ln["item_code"]].update(rec["removed"])
        elif a == "PARENT_RESTATED":
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None:
                raise ValueError(f"{METHOD}: parent {ln['line_id']} carries a figure")
            for h in rec.get("added_held") or ():
                (out["roof_walls"] if h["kind"] == "ROOF_DATUM" else out["conflicts"]).add(h["wall"])
            out["parents"] += 1
        elif a == "PARAPET_BLOCK_ALT":
            out["parapets"] += 1
        else:
            raise ValueError(f"{METHOD}: action {a}")
    for ln in lines:
        prc = _inp(ln).get(FILL_KEY) or {}
        if prc.get("action") != "PART" or ln["item_code"] not in ITEMS:
            continue
        bad = {p["id"] for p in prc.get("pieces") or ()} & held_by_item[ln["item_code"]]
        if bad:
            raise ValueError(f"{METHOD}: {sorted(bad)} held by {RULE_ID} and still released on {ln['line_id']}")
    sets = {c: frozenset(v) for c, v in held_by_item.items()}
    if len(set(sets.values())) > 1:
        raise ValueError(f"{METHOD}: the three items hold different walls {sets}")
    out["roof_walls"], out["conflicts"] = sorted(out["roof_walls"]), sorted(out["conflicts"])
    return out


# ================================================================================================ integrate / write
def _earlier_checks(out, for_lead=()):
    """every check the V3.0.54 integration runs, on the V3.0.55 lines (same functions, same order)."""
    from engine.source import arch_v3031 as A3031, arch_v3032 as A3032, arch_v3033 as A3033, arch_v3034 as A3034
    from engine.source import arch_v3035 as A3035, arch_v3036 as A3036, arch_v3038 as A3038, arch_v3039 as A3039
    from engine.source import arch_v3040 as A3040, arch_v3041 as A3041, arch_v3042 as A3042, arch_v3044 as A3044
    from engine.source import arch_v3045 as A3045, arch_v3047 as A3047, arch_v3051 as A3051
    older = [ln for ln in out if not _inp(ln).get(A3051.REC_KEY)]
    return {"guards": A3031._family_guards(out, for_lead),
            "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
            "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
            "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
            "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
            "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
            "earthworks": A3050.check_zone_owner(out), "skirting": A3044.check_skirting(older),
            "blinding": A3045.check_blinding(out), "tie_masonry": A3046.check_tie_masonry(out),
            "stair_rooms": A3047.check_stair_rooms(out), "remainder": A3051.check_remainder(out),
            "lintels": A3053.check_lintels(out), "rail_runs": A3054.check_runs(out)}


def integrate(prev, changes, for_lead=()):
    """-> (V3.0.55 lines, identity). Replaced lines keep their place and id; every other line is byte-identical
    (asserted). Every earlier family guard and V3.0.54 check runs on the integrated lines."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    rep = {}
    for c in changes:
        a = c["after"]
        if c["action"] != "REPLACE" or a["line_id"] not in sid or c["before"]["line_id"] != a["line_id"]:
            raise ValueError(f"{METHOD}: {c['action']} {a['line_id']} (this version only replaces candidate lines)")
        if a["line_id"] in rep:
            raise ValueError(f"{METHOD}: {a['line_id']} replaced twice")
        rep[a["line_id"]] = a
    out = [rep.get(ln["line_id"], ln) for ln in prev]
    ident = {"base_lines": len(prev), "v3_0_55_lines": len(out), "v3_0_55_rows": len(changes),
             "replaced": len(rep), "added": 0, **_earlier_checks(out, for_lead), "wiring": check_wiring(out)}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    same = [ln for ln in prev if ln["line_id"] not in rep]
    bad = [a["line_id"] for a in same if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    ident.update(outside_rows=len(same), outside_rows_identical_to_base=len(same),
                 outside_rows_sha256=hashlib.sha256("".join(A30.line_sha(x) for x in same).encode()).hexdigest())
    return out, ident


def check_totals(t0, t1):
    """totals move only in the three blockwork items (asserted)."""
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        if t0.get(k) == t1.get(k):
            continue
        if k.split("|")[0] not in ITEMS:
            raise ValueError(f"{METHOD}: totals moved outside this version's codes: {k}")
        moved[k] = {"base": t0.get(k), "v3_0_55": t1.get(k)}
    return moved


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = _inp(ref).get(REC_KEY) or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "parent_line_id": c.get("parent_line_id"), "before_released_v2_9": b29,
                     "before_base": A30._qty(c.get("before")), "after_v3_0_55": A30._qty(ref),
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "downstream": c.get("downstream"), "record": rec, "verification": c.get("verification") or {},
                     "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "floor", "element_id", "unit", "parent_line_id", "v2_9",
              "base", "v3_0_55", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_55")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']}: {x.get('why')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "parent_line_id": r.get("parent_line_id") or "",
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_55": q(r.get("after_v3_0_55")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    rows = A3046.diff_rows(prev, new, released_lines)
    return [dict({k: v for k, v in r.items() if k != "v3_0_46"}, v3_0_55=r["v3_0_46"]) for r in rows]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_55_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new))
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": {k: log.get(k) for k in ("by_item", "roof_walls", "conflicts", "drops", "parapets", "lines")},
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_55_BOQ_LINES.json": BL.dumps(new),
             "V3_0_55_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_55_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_55_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_55_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_55_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK,
            "actions": ["PART_HELD", "PART_REDUCED", "PARENT_RESTATED", "PARAPET_BLOCK_ALT"]}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "ITEMS", "load_inputs",
           "changes_for", "check_wiring", "integrate", "check_totals", "ledger_rows", "diff_rows", "write",
           "InputsError"]
