"""ARCH_TAKEOFF_V3.0.23 (T-319): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.22 (engine.source.arch_v30,
arch_v301 .. arch_v3022), extended with ONE piece, PARAPET_RC: the reinforced-concrete part of every roof / terrace
parapet run, a structural category that no candidate line carried, as its own concrete line family (STR.CONC.PARAPET,
one line per roof chain), HELD with its bound. Not a new method family and not the released default (owner management
decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): a parapet is a wall standing on the edge of a roof slab, above the
supporting edge beam. The beam lines take the beam to its scheduled depth, which ends at the structural slab top, so
nothing above the slab top is inside a beam line (R-T311-2). Above the slab top every printed alternative of the set
carries reinforced concrete: a typical detail with an RC upstand of a printed minimum height under a block wall, or
details that are RC throughout. Which detail governs which run is not keyed (a designer item), so the MATERIAL above
the upstand is HELD, and so is the build-up depth b_edge at the roof edge (the parapet height is printed above the
FINISHED roof). What every alternative shares is booked as the bound, never as the quantity:

  lower bound   top x max(u, b_edge + margin): the upstand rises at least u (printed) above the slab top and at least
                the roof finishing depth plus a margin (the typical detail's note); while b_edge is HELD only the floor
                top x u is established, an AT_LEAST figure valid for every b_edge, never 'the' lower bound;
  upper bound   top x (h + b_edge): the whole parapet in RC, h the printed height above the finished roof; open while
                b_edge is HELD (its increment, top m3 per m of b_edge, is stated);
  top           the parapet's plan footprint per run (drawn centreline x drawn thickness, as the merged component
                ledger measures it), so a solid volume = top x a height.

So each line is BLOCKED (HELD, BLANK: no figure, no range, never 0, never a midpoint) and carries its bound beside it
(calculation.inputs.parapet_rc_v3023, notes, rfi). The block alternative above the upstand belongs to the blockwork
family (MAS.BLOCK) and is EXCLUSIVE with the RC above the upstand: a run is RC OR block there, never both, and the two
are never added. Formwork faces belong to the formwork family, reinforcement to the rebar family, the faces / top /
arrises to the finish families, the membrane upturn to the roof waterproofing line: none of them is in this line.

  ADD     one STR.CONC.PARAPET line per roof chain (element '<chain>#PARAPET_RC'), BLOCKED_RFI, with its runs.

Refused (InputsError / ValueError, nothing written): a run named twice or in two chains; a chain named twice; a height
outside H_MIN .. H_MAX (mm or a typo) or without its source (a defaulted height); a height range that is not HELD; a
thickness outside T_MIN .. T_MAX; a top that is not centreline x thickness; a missing top (HELD is never 0); an upstand
floor without its printed source, or a floor status DRAWING-CONFIRMED without the checker run; a run whose material is
set to RC while its block alternative carries area (RC OR block, never both), or to anything but HELD / RC / BLOCK; a
run already carried by a concrete line of the run (a concrete line whose basis names a parapet: the beam stops at the
slab top) or a STR.CONC.PARAPET line already in the run; a declared total that is not the records' sum; a parapet line
with a figure or a range (a held line summed into a total). Every V3.0.22 line is byte-identical (asserted); the
merged default guard runs again over the result (arch_v307.guard_changes) with the added lines.

Files: V3_0_23_BOQ_LINES.json / .csv, V3_0_23_INTEGRATION_LEDGER.json / .csv (per line: before (absent), after,
released V2.9, runs, bound, owner manual method beside the drawing-derived method, exclusive / downstream items, status,
source tasks / merges / checker runs), V3_0_23_RUNS.csv (every parapet run once), V3_0_23_DIFF.csv (every line against
V3.0.22 and the released V2.9), V3_0_23_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate:
every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3021 as A3021
from engine.source import arch_v3022 as A3022

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: it adds lines; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.23"
EXTENDS = A3022.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T319_ARCH_V3_0_23"
INPUTS_SCHEMA = "URBAN_V3023_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3023_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
VER, DC, OA = A3018.VER, A3018.DC, A3018.OA
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
TOL = 1e-6
TOP_TOL_M2 = 1e-5                       # top vs centreline x thickness (6-decimal ledgers)
SUM_TOL = 1e-4                          # declared totals vs the records' sums
H_MIN, H_MAX = 0.10, 3.00               # a parapet height above the finished roof, m (mm or a typo is refused)
T_MIN, T_MAX = 0.05, 0.60               # a parapet thickness, m
PARAPET = "STR.CONC.PARAPET"
MATERIALS = ("HELD", "RC", "BLOCK")
FLOOR_STATUS = (VER, DC, "HELD")
HELD_STATUS = ("HELD", "UNKNOWN")
STATE = "BLOCKED_RFI"
RULE = ("R-PARAPET-RC-1", "T-319")
PARAPET_WORDS = ("parapet",)

PIECES = {
    "PARAPET_RC": {
        "module": "engine/source/arch_v3023.py (the RC part of every roof / terrace parapet run as its own concrete "
                  "line family, one HELD line per roof chain with its bound, from checker-merged run ledgers)",
        "policy": "PARAPET_RC_V1", "rule_id": RULE[0], "rule_version": RULE[1],
        "owner_rules": ["Q-65 C (parapet material: request material and construction details from the designer; "
                        "provisional alternatives may be shown; classification HELD)",
                        "D-39 (roof structural tops / build-up depth at the edge HELD)",
                        "UP-QTY-STATUS-001 (held never 0)", "UP-WALL-GEOM-001",
                        "owner BLOCKWORK rule (block above the RC upstand is masonry, MAS.BLOCK)",
                        "ERS 2026-10-22 s.2 - s.4, s.7 (R-T311-1 .. 4; Checker addition: an upstand tied to the roof "
                        "build-up carries its lower bound as max(printed, build-up), never the printed value alone)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5"],
        "owner_manual_method": "no answered owner rule measures parapet concrete (Q-65 C holds the material for the "
                               "designer); the manual take-off of the set carries every parapet as blockwork at "
                               "1.00 / 1.80 / 1.00 m and has no parapet row in its concrete: shown beside, never used",
        "drawing_method": "per run: top = drawn centreline x drawn thickness (plan footprint); RC above the slab top "
                          "at least the printed upstand in every alternative: lower bound top x max(upstand, b_edge "
                          "+ margin), floor top x upstand; upper bound all RC top x (printed height above the "
                          "finished roof + b_edge); b_edge and the material per run HELD"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3022.WAITING)
WAITING.update({
    "PARAPET_RC_MATERIAL": "which parapet detail governs which run (RC upstand under block, or RC throughout): a "
                           "designer item under owner Q-65 C; until then every STR.CONC.PARAPET line stays BLANK with "
                           "its bound",
    "PARAPET_RC_B_EDGE": "the roof build-up depth at each parapet (D-39): it sets the upstand lower bound max(u, b_edge "
                         "+ margin) and the open part of the upper bound",
    "PARAPET_BLOCK_ALTERNATIVE": "the block above the upstand (MAS.BLOCK, exclusive with the RC above the upstand, "
                                 "never added to it): the blockwork binding carries it",
    "PARAPET_FORMWORK": "the formed faces of the RC reading: the formwork family carries them",
    "PARAPET_REBAR": "reinforcement of the upstand / RC parapet: type unkeyed, no rebar change before an approved stage",
})


# ================================================================================================ inputs
def _check_run(u, where):
    """one parapet run. -> (top_lo, top_hi, h_lo, h_hi)"""
    for x in ("run", "kind", "geometry_status", "h_source", "material", "source_task"):
        if not u.get(x):
            raise InputsError(f"{where}: {x} required")
    t = u.get("t_m")
    if not (_num(t) and T_MIN <= t <= T_MAX):
        raise InputsError(f"{where}: thickness {t} m outside {T_MIN} .. {T_MAX} (mm, a typo or missing)")
    hl, hh = u.get("h_lo_m"), u.get("h_hi_m")
    if not (_num(hl) and _num(hh)):
        raise InputsError(f"{where}: the height above the finished roof is printed or HELD as a range, never a "
                          "default (h_lo_m / h_hi_m)")
    if not (H_MIN <= hl <= hh <= H_MAX):
        raise InputsError(f"{where}: height {hl} .. {hh} m outside {H_MIN} .. {H_MAX} m or reversed (mm, a typo)")
    if hh > hl + TOL and u.get("h_status") not in HELD_STATUS:
        raise InputsError(f"{where}: a height range is HELD with its reason (h_status), never a chosen value")
    cl, ch = u.get("centreline_lo_m"), u.get("centreline_hi_m")
    tl, th = u.get("top_lo_m2"), u.get("top_hi_m2")
    if not (_num(cl) and _num(ch) and _num(tl) and _num(th)) or not (0 < cl <= ch and 0 < tl <= th):
        raise InputsError(f"{where}: centreline and top > 0 with low <= high (a missing one is HELD, never 0)")
    if abs(tl - cl * t) > TOP_TOL_M2 or abs(th - ch * t) > TOP_TOL_M2:
        raise InputsError(f"{where}: top {tl} .. {th} != centreline {cl} .. {ch} x t {t} (the plan footprint)")
    if th > tl + TOL and not str(u["geometry_status"]).startswith("HELD"):
        raise InputsError(f"{where}: a top range is HELD (geometry_status), never a chosen length")
    m = u["material"]
    if m not in MATERIALS:
        raise InputsError(f"{where}: material {m!r} not one of {MATERIALS}")
    blk = u.get("block_alt_m2")
    if blk is None:
        if not u.get("block_alt_note"):
            raise InputsError(f"{where}: a run with no block-alternative figure names why (block_alt_note), never 0")
        blk = [0.0, 0.0]
    elif not (isinstance(blk, (list, tuple)) and len(blk) == 2 and all(_num(x) for x in blk) and
              0 <= blk[0] <= blk[1]):
        raise InputsError(f"{where}: block_alt_m2 [low, high] (the block alternative above the upstand)")
    if m == "RC" and (blk[1] > TOL or u.get("block_alt_m2") is None):
        raise InputsError(f"{where}: the run is RC above the upstand and carries block {blk}: RC OR block, never both")
    if m == "BLOCK":
        raise InputsError(f"{where}: a run read as block above the upstand still carries its RC upstand: the "
                          "material is HELD (or RC) here, the block part belongs to MAS.BLOCK only")
    return tl, th, hl, hh


def load_inputs(doc, project_id=None):
    """URBAN_V3023_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "upstand": {"floor_m", "source", "status" VERIFIED | DRAWING-CONFIRMED | HELD, "checker_run",
                     "lower_bound_rule"},
         "chains": [{chain, floor, roof_level, element_id, roof_wp_line_id, task, material_status, material_item,
                     b_edge_item, runs: [{run, kind, t_m, centreline_lo_m, centreline_hi_m, top_lo_m2, top_hi_m2,
                     h_lo_m, h_hi_m, h_source, h_status, geometry_status, material, block_alt_m2 [lo, hi],
                     source_task, corrections}], exclusive, downstream}],
         "excluded": [{what, evidence, owner, status}],
         "declared": {"lines", "top_lo_m2", "top_hi_m2", "floor_m3", "all_rc_printed_lo_m3", "all_rc_printed_hi_m3"},
         "guard": as URBAN_V307_INPUTS_V1 "guard" (optional)}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the merged ledgers the runs come from")
    tasks = set()
    for s in srcs:
        A3018._source(s, "sources")
        tasks.add(s["task"])
    up = doc.get("upstand") or {}
    u0 = up.get("floor_m")
    if not (_num(u0) and 0 < u0 <= H_MAX) or not up.get("source") or not up.get("lower_bound_rule"):
        raise InputsError("upstand: floor_m > 0 with its printed source and the lower-bound rule (never a default)")
    if up.get("status") not in FLOOR_STATUS:
        raise InputsError(f"upstand: status one of {FLOOR_STATUS}")
    if up["status"] in (VER, DC) and not up.get("checker_run"):
        raise InputsError("upstand: a confirmed floor names the checker run that confirmed it")
    chains = doc.get("chains") or []
    if not chains:
        raise InputsError("no chains")
    seen_c, seen_r, seen_e = set(), set(), set()
    tot = {"lines": 0, "top_lo_m2": 0.0, "top_hi_m2": 0.0, "floor_m3": 0.0, "all_rc_printed_lo_m3": 0.0,
           "all_rc_printed_hi_m3": 0.0}
    for c in chains:
        where = f"chain {c.get('chain')}"
        for x in ("chain", "floor", "roof_level", "element_id", "task", "material_status", "material_item",
                  "b_edge_item"):
            if not c.get(x):
                raise InputsError(f"{where}: {x} required")
        if c["task"] not in tasks:
            raise InputsError(f"{where}: task {c['task']!r} is not one of the sources {sorted(tasks)}")
        if c["chain"] in seen_c or c["element_id"] in seen_e:
            raise InputsError(f"{where}: a chain (or its element) named twice: one line per roof chain")
        seen_c.add(c["chain"])
        seen_e.add(c["element_id"])
        if c["material_status"] not in HELD_STATUS:
            raise InputsError(f"{where}: the parapet material is HELD until a detail is keyed to the run (Q-65 C)")
        runs = c.get("runs") or []
        if not runs:
            raise InputsError(f"{where}: a chain lists its runs (each once)")
        for u in runs:
            rid = f"{c['chain']}/{u.get('run')}"
            if rid in seen_r:
                raise InputsError(f"run {rid}: named twice (each parapet run in exactly one line)")
            seen_r.add(rid)
            if u.get("source_task") not in tasks:
                raise InputsError(f"run {rid}: source_task {u.get('source_task')!r} is not a source")
            tl, th, hl, hh = _check_run(u, f"run {rid}")
            tot["top_lo_m2"] += tl
            tot["top_hi_m2"] += th
            tot["floor_m3"] += tl * u0
            tot["all_rc_printed_lo_m3"] += tl * hl
            tot["all_rc_printed_hi_m3"] += th * hh
        tot["lines"] += 1
    for i, e in enumerate(doc.get("excluded") or ()):
        if not (e.get("what") and e.get("evidence") and e.get("owner") and e.get("status")):
            raise InputsError(f"excluded {i}: {{what, evidence, owner, status}} (an item kept out of this line by "
                              "evidence, never dropped)")
    dec = doc.get("declared") or {}
    for k, v in tot.items():
        d = dec.get(k)
        if not _num(d) or abs(d - v) > SUM_TOL:
            raise InputsError(f"declared {k} {d} != the records' {round(v, 6)}")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ bound
def run_bound(u, u0):
    """-> the bound of one run: floor (AT_LEAST, any b_edge), all-RC printed part at b_edge 0 (lo .. hi), the open
    increment per m of b_edge."""
    return {"run": u["run"], "kind": u["kind"], "t_m": _r(u["t_m"]),
            "centreline_m": [_r(u["centreline_lo_m"]), _r(u["centreline_hi_m"])],
            "top_m2": [_r(u["top_lo_m2"]), _r(u["top_hi_m2"])],
            "h_above_finish_m": [_r(u["h_lo_m"]), _r(u["h_hi_m"])], "h_source": u["h_source"][:200],
            "h_status": u.get("h_status") or "PRINTED", "geometry_status": u["geometry_status"],
            "material": u["material"], "floor_at_least_m3": _r(u["top_lo_m2"] * u0),
            "all_rc_printed_part_m3": [_r(u["top_lo_m2"] * u["h_lo_m"]), _r(u["top_hi_m2"] * u["h_hi_m"])],
            "held_increment_m3_per_m_b_edge": _r(u["top_hi_m2"]),
            "block_alternative_m2": [_r(u["block_alt_m2"][0]), _r(u["block_alt_m2"][1])]
            if u.get("block_alt_m2") is not None else None,
            "block_alternative_note": u.get("block_alt_note"),
            "source_task": u["source_task"], "corrections": list(u.get("corrections") or ())}


def chain_bound(c, u0):
    runs = [run_bound(u, u0) for u in c["runs"]]

    def s(k, i=None):
        return _r(sum(r[k] if i is None else r[k][i] for r in runs if r[k] is not None))
    return runs, {"runs": len(runs), "top_m2": [s("top_m2", 0), s("top_m2", 1)], "floor_at_least_m3": s(
        "floor_at_least_m3"), "all_rc_printed_part_m3": [s("all_rc_printed_part_m3", 0), s("all_rc_printed_part_m3", 1)],
        "held_increment_m3_per_m_b_edge": s("held_increment_m3_per_m_b_edge"),
        "block_alternative_m2": [s("block_alternative_m2", 0), s("block_alternative_m2", 1)],
        "block_alternative_not_booked": [r["run"] for r in runs if r["block_alternative_m2"] is None]}


def _bound_text(b, u0):
    return (f"lower bound top x max({u0}, b_edge + margin) (at least {b['floor_at_least_m3']} m3 for any b_edge); "
            f"upper bound all RC top x (h + b_edge): {b['all_rc_printed_part_m3'][0]} .. "
            f"{b['all_rc_printed_part_m3'][1]} m3 at b_edge 0 plus {b['held_increment_m3_per_m_b_edge']} m3 per m of "
            f"b_edge (open)")


# ================================================================================================ lines
def _template(lines):
    """the shape of the family's lines: a structural concrete line of the run (trade, documents, source)."""
    for ln in lines:
        if ln["item_code"] == "STR.CONC.BEAM":
            return ln
    for ln in lines:
        if str(ln["item_code"]).startswith("STR.CONC."):
            return ln
    raise InputsError("the run carries no structural concrete line to shape the parapet family from")


def added_line(template, c, doc, src):
    """ONE STR.CONC.PARAPET line of a roof chain: BLOCKED_RFI, blank, its bound beside it."""
    from engine.source import boq_line as BL
    up = doc["upstand"]
    u0 = up["floor_m"]
    runs, b = chain_bound(c, u0)
    pid, rev = template["project"]["project_id"], template["project"]["revision_set_sha256"]
    rec = {"policy": PIECES["PARAPET_RC"]["policy"], "chain": c["chain"], "roof_level": c["roof_level"],
           "record_state": "ADD", "evidence_status": "HELD", "task": src["task"], "ledger": src["file"],
           "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
           "upstand": {"floor_m": u0, "source": up["source"][:300], "status": up["status"],
                       "checker_run": up.get("checker_run"), "lower_bound_rule": up["lower_bound_rule"][:300]},
           "bound": dict(b, floor_status=up["status"], lower_bound="top x max(upstand, b_edge + margin): HELD on "
                                                                   "b_edge (D-39) and the margin (not printed)",
                         upper_bound="top x (h + b_edge): open while b_edge is HELD", release_status="NOT RELEASED"),
           "runs": runs, "material_status": c["material_status"], "material_item": c["material_item"],
           "b_edge_item": c["b_edge_item"], "roof_wp_line_id": c.get("roof_wp_line_id"),
           "exclusive": list(c.get("exclusive") or ()), "downstream": list(c.get("downstream") or ()),
           "rule_id": RULE[0], "rule_version": RULE[1]}
    inputs = {"chain": c["chain"], "record_state": "ADD", "evidence_status": "HELD",
              "owner_manual_method": PIECES["PARAPET_RC"]["owner_manual_method"],
              "drawing_derived_method": PIECES["PARAPET_RC"]["drawing_method"], "parapet_rc_v3023": rec}
    q = (f"Parapet RC, {c['chain']} roof {c['roof_level']}: HELD bound at least {b['floor_at_least_m3']} m3 (top "
         f"{b['top_m2'][0]} m2 x {u0}, any b_edge), all RC {b['all_rc_printed_part_m3'][0]} .. "
         f"{b['all_rc_printed_part_m3'][1]} m3 at b_edge 0 + {b['held_increment_m3_per_m_b_edge']} m3 per m of b_edge; "
         f"unlocks: which detail governs each run ({c['material_item']}) and the roof build-up depth at the edge "
         f"({c['b_edge_item']})")
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=PARAPET, unit="m3", evidence_state=STATE,
                      measured_net=None, element_id=c["element_id"], floor=c["floor"],
                      physical_element="parapet_rc", gross=None, bounded_range=None,
                      formula=(f"held: {METHOD}: parapet RC of {len(runs)} runs, each top (centreline x t) x a height "
                               f"above the slab top; {_bound_text(b, u0)}; material per run {c['material_item']}, "
                               f"b_edge {c['b_edge_item']}: BLANK, never 0")[:600],
                      inputs=inputs, documents=(template.get("source") or {}).get("documents") or [],
                      geometry_source=(template.get("source") or {}).get("geometry_source") or "CAD_VECTOR",
                      geometry_confidence="TOLERANCE_CERTIFIED", rule_id=RULE[0], rule_version=RULE[1],
                      material_state=template.get("material_state") or "BY_SPEC",
                      rfi={"question": q[:700], "items": [c["material_item"], c["b_edge_item"]],
                           "blocks": "the parapet RC volume of this chain"},
                      notes=(f"{METHOD}: a MISSING structural category (no candidate concrete line carried the parapet; "
                             f"the beam lines stop at the slab top) added HELD from the merged run ledgers "
                             f"({', '.join(sorted({u['source_task'] for u in c['runs']}))}): {_bound_text(b, u0)}; "
                             f"floor {up['status']} ({(up.get('checker_run') or '')[:80]}); block above the upstand is "
                             f"the exclusive alternative in MAS.BLOCK (never added); formwork, rebar, faces and upturn "
                             f"in their own families"),
                      subtrade=template.get("subtrade"), trade=template.get("trade"))
    return BL.validate(ln)


def _names_parapet(ln):
    t = " ".join(str(x) for x in (ln.get("notes"), (ln.get("calculation") or {}).get("formula"),
                                  (ln.get("location") or {}).get("element_id"), ln.get("physical_element"))).lower()
    return any(w in t for w in PARAPET_WORDS)


def _assert_not_carried(l3022):
    """no parapet carrier already in the run: no STR.CONC.PARAPET line and no concrete line whose basis names a
    parapet (the beam lines stop at the slab top, R-T311-2)."""
    for ln in l3022:
        code = str(ln["item_code"])
        if code == PARAPET:
            raise InputsError(f"the run already carries {PARAPET} line {ln['line_id']}: a second carrier is refused")
        if code.startswith("STR.CONC.") and _names_parapet(ln):
            raise InputsError(f"concrete line {ln['line_id']} ({code}) names a parapet: the run would be carried twice "
                              "(a beam line ends at the slab top; the parapet is its own line)")


def family_changes(doc, l3022):
    """-> (changes, log, run rows)."""
    _assert_not_carried(l3022)
    tpl = _template(l3022)
    have = {ln["line_id"] for ln in l3022}
    u0 = doc["upstand"]["floor_m"]
    changes, rows = [], []
    log = {"piece": "PARAPET_RC", "state": "RUN", "sources": doc["sources"], "lines": 0, "runs": 0,
           "floor_at_least_m3": 0.0, "all_rc_printed_part_m3": [0.0, 0.0], "held_increment_m3_per_m_b_edge": 0.0,
           "excluded": list(doc.get("excluded") or ())}
    for c in doc["chains"]:
        src = A3018._src_of(doc, c["task"])
        after = added_line(tpl, c, doc, src)
        if after["line_id"] in have:
            raise ValueError(f"{METHOD}: the added line repeats a candidate line id")
        runs, b = chain_bound(c, u0)
        log["lines"] += 1
        log["runs"] += len(runs)
        log["floor_at_least_m3"] = _r(log["floor_at_least_m3"] + b["floor_at_least_m3"])
        log["all_rc_printed_part_m3"] = [_r(log["all_rc_printed_part_m3"][i] + b["all_rc_printed_part_m3"][i])
                                         for i in (0, 1)]
        log["held_increment_m3_per_m_b_edge"] = _r(log["held_increment_m3_per_m_b_edge"] +
                                                   b["held_increment_m3_per_m_b_edge"])
        ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
               "ledger": src["file"], "ledger_sha256": src["sha256"],
               "upstand_checker_run": doc["upstand"].get("checker_run")}
        changes.append(A305._change("PARAPET_RC", "ADD", None, after, drawing_reference=src["file"],
                                    held=[{"what": f"{PARAPET} {c['chain']}",
                                           "why": f"{c['material_item']}; {c['b_edge_item']}: "
                                                  f"{_bound_text(b, u0)}"[:900]}],
                                    downstream=[d if isinstance(d, dict) else {"item": d}
                                                for d in c.get("downstream") or ()],
                                    verification=ver, evidence_status="HELD", codes=["PARAPET_RC", "ADD"],
                                    group=c["chain"], record=c,
                                    guard_element={"element_id": after["location"]["element_id"], "part": "WHOLE"}))
        for r in runs:
            rows.append(dict(r, chain=c["chain"], roof_level=c["roof_level"], line_id=after["line_id"],
                             material_item=c["material_item"], b_edge_item=c["b_edge_item"]))
    return changes, log, rows


def changes_for(doc, l3022):
    """-> (changes, logs, run rows). The guard re-check runs over the result (arch_v307) with the added lines."""
    if not doc:
        return [], [{"piece": "PARAPET_RC", "state": "NO_PROJECT_INPUT"}], []
    ch, log, rows = family_changes(doc, l3022)
    ch_g, log_g = A307.guard_changes(doc, l3022, ch, set())
    added = {c["after"]["line_id"] for c in ch}
    for c in ch_g:
        lid = c["before"]["line_id"]
        if lid in added:
            raise ValueError(f"{METHOD}: the guard flags a line this version adds ({lid})")
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, [log, log_g], rows


# ================================================================================================ integrate / write
def check_parapet_family(lines):
    """every STR.CONC.PARAPET line is BLANK (no figure, no range) with its bound record; -> summary. A figure or a
    range on one of them (a held line summed into a total) is refused."""
    out = {"lines": 0, "blank": 0, "floor_at_least_m3": 0.0, "runs": 0}
    seen_runs = set()
    for ln in lines:
        if ln["item_code"] != PARAPET:
            continue
        out["lines"] += 1
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get("parapet_rc_v3023")
        if ln["evidence_state"] != STATE or ln.get("measured_net") is not None or ln.get("bounded_range") is not None \
                or ln.get("gross") is not None:
            raise ValueError(f"{METHOD}: parapet line {ln['line_id']} carries a figure or a range: a HELD line is "
                             "never summed into a total")
        if not rec or not rec.get("bound"):
            raise ValueError(f"{METHOD}: parapet line {ln['line_id']} carries no bound record")
        for r in rec["runs"]:
            k = (rec["chain"], r["run"])
            if k in seen_runs:
                raise ValueError(f"{METHOD}: run {k} in two parapet lines")
            seen_runs.add(k)
        out["blank"] += 1
        out["runs"] += len(rec["runs"])
        out["floor_at_least_m3"] = _r(out["floor_at_least_m3"] + rec["bound"]["floor_at_least_m3"])
    return out


def integrate(l3022, changes):
    """-> (V3.0.23 lines, identity). Every V3.0.22 line is byte-identical; only the parapet lines are added."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3022}
    adds, rep = [], {}
    for c in changes:
        if c["action"] == "ADD":
            if c["piece"] != "PARAPET_RC" or c["after"]["item_code"] != PARAPET:
                raise ValueError(f"{METHOD}: only the parapet piece adds, and only {PARAPET} lines")
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.22 line id")
            adds.append(c["after"])
        elif c["action"] == "REPLACE" and c["piece"] == "DEFAULT_GUARD":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid:
                raise ValueError(f"{METHOD}: guard line {lid} changed twice or not in V3.0.22")
            rep[lid] = c["after"]
        else:
            raise ValueError(f"{METHOD}: action {c['action']} of {c['piece']} (this version only adds parapet lines)")
    if rep:
        raise ValueError(f"{METHOD}: the guard re-check changed {len(rep)} V3.0.22 line(s): every V3.0.22 line stays "
                         "byte-identical in this version")
    out = list(l3022) + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    A3018.check_splits(out)
    tile = A3021.check_tile_family(out)
    fam = check_parapet_family(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by22 = {ln["line_id"]: ln for ln in l3022}
    outside = out[:len(l3022)]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by22[ln["line_id"]]) != A30.line_sha(ln)]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.22 line(s) differ")
    ident = {"v3_0_22_lines": len(l3022), "v3_0_23_lines": len(out), "v3_0_23_rows": len(changes),
             "replaced": 0, "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_22": len(outside), "parapet_family": fam, "wall_tile_family": tile,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, doc, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        inp = ref["calculation"]["inputs"]
        pr = inp.get("parapet_rc_v3023") or {}
        loc = ref.get("location") or {}
        pp = PIECES.get(c["piece"]) or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "chain": pr.get("chain"),
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "before_released_v2_9": b29,
                     "before_v3_0_22": dict(A30._qty(None), state="NOT_IN_V3_0_22") if c["before"] is None else
                     A30._qty(c["before"]), "after_v3_0_23": A30._qty(ref), "bound": pr.get("bound"),
                     "runs": pr.get("runs") or [], "upstand": pr.get("upstand"),
                     "material_item": pr.get("material_item"), "b_edge_item": pr.get("b_edge_item"),
                     "evidence_status": c.get("evidence_status"), "release_status": "NOT RELEASED",
                     "owner_manual_method": inp.get("owner_manual_method"),
                     "drawing_derived_method": inp.get("drawing_derived_method"),
                     "exclusive": pr.get("exclusive") or [], "roof_wp_line_id": pr.get("roof_wp_line_id"),
                     "codes": c.get("codes") or [], "owner_rules": pp.get("owner_rules"),
                     "verification": dict(c.get("verification") or {}, module=pp.get("module"),
                                          policy=pp.get("policy")),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "chain", "line_id", "item_code", "floor", "unit", "v2_9", "v3_0_22", "v3_0_23", "runs",
              "top_m2", "floor_at_least_m3", "floor_status", "all_rc_printed_part_m3", "held_increment_m3_per_m_b_edge",
              "block_alternative_m2", "material_item", "b_edge_item", "evidence_status", "release_status", "held",
              "verification")
RUNS_CSV = ("chain", "run", "kind", "roof_level", "line_id", "t_m", "centreline_m", "top_m2", "h_above_finish_m",
            "h_source", "h_status", "geometry_status", "material", "floor_at_least_m3", "all_rc_printed_part_m3",
            "held_increment_m3_per_m_b_edge", "block_alternative_m2", "block_alternative_note", "source_task",
            "corrections")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_22", "vs_released_v2_9", "v2_9",
            "v3_0_22", "v3_0_23")


def _rng(x):
    return f"{x[0]} .. {x[1]}" if x else ""


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "chain": r["chain"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "unit": r["unit"],
                       "v2_9": A302._q(r["before_released_v2_9"]) if r["before_released_v2_9"] else "",
                       "v3_0_22": A302._q(r["before_v3_0_22"]), "v3_0_23": A302._q(r["after_v3_0_23"]),
                       "runs": len(r["runs"]), "top_m2": _rng((r["bound"] or {}).get("top_m2")),
                       "floor_at_least_m3": (r["bound"] or {}).get("floor_at_least_m3", ""),
                       "floor_status": (r["bound"] or {}).get("floor_status", ""),
                       "all_rc_printed_part_m3": _rng((r["bound"] or {}).get("all_rc_printed_part_m3")),
                       "held_increment_m3_per_m_b_edge": (r["bound"] or {}).get("held_increment_m3_per_m_b_edge", ""),
                       "block_alternative_m2": _rng((r["bound"] or {}).get("block_alternative_m2")),
                       "material_item": r["material_item"] or "", "b_edge_item": r["b_edge_item"] or "",
                       "evidence_status": r["evidence_status"] or "", "release_status": r["release_status"],
                       "held": "; ".join(h["why"] for h in r["held"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''} "
                                       f"{r['verification'].get('verifier_run') or ''}".strip()[:300]}
                      for r in rows if r["piece"] == "PARAPET_RC"], LEDGER_CSV)


def runs_csv(rows):
    return A305._csv([dict(r, centreline_m=_rng(r["centreline_m"]), top_m2=_rng(r["top_m2"]),
                           h_above_finish_m=_rng(r["h_above_finish_m"]),
                           all_rc_printed_part_m3=_rng(r["all_rc_printed_part_m3"]),
                           block_alternative_m2=_rng(r["block_alternative_m2"]) if r["block_alternative_m2"] is not None
                           else "not booked", block_alternative_note=r.get("block_alternative_note") or "",
                           corrections="; ".join(r["corrections"])) for r in rows], RUNS_CSV)


def diff_rows(l3022, l3023, released_lines=None):
    b22 = {ln["line_id"]: ln for ln in l3022}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3023:
        o = b22.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_22": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_22": A302._q(A30._qty(o)) if o else "", "v3_0_23": A302._q(A30._qty(ln))})
    return out


def write(out, l3022, changes, logs, rows_runs, doc, released_lines=None):
    """the V3_0_23_* files beside the V3_0_22_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3023, ident = integrate(l3022, changes)
    rows = ledger_rows(changes, doc, released_lines)
    diff = diff_rows(l3022, l3023, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_22", {}).setdefault(d["vs_v3_0_22"], 0)
        dsum["vs_v3_0_22"][d["vs_v3_0_22"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, runs=len(rows_runs))
    t22, t23 = A304.code_totals(l3022), A304.code_totals(l3023)
    moved = {k: {"v3_0_22": t22.get(k), "v3_0_23": t23.get(k)} for k in sorted(set(t22) | set(t23))
             if t22.get(k) != t23.get(k)}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "runs": rows_runs, "upstand": doc.get("upstand"), "excluded": doc.get("excluded") or [],
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] or "NONE" for r in rows)}
    files = {"V3_0_23_BOQ_LINES.json": BL.dumps(l3023),
             "V3_0_23_BOQ_LINES.csv": A30._lines_csv(l3023),
             "V3_0_23_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_23_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_23_RUNS.csv": runs_csv(rows_runs),
             "V3_0_23_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_23_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "run_bound",
           "chain_bound", "added_line", "family_changes", "changes_for", "check_parapet_family", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError"]
