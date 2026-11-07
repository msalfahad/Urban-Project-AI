"""T-596 WIRING MANIFEST V11 + OVERLAY DRY RUN (R-T596-1; lane I, non-candidate, research only).

V11 carries the Checker-merged structural restatements of T-595 (R-T595-1 dome-ring side bars on both faces, R-T595-2
F10 + F scenario-set bound) and the T-598 nosing edge closures (Lead amendment 2026-11-07 12:16) onto the candidate of
record ARCH_TAKEOFF_V3.0.58, and overlays them on a COPY of its line index AFTER V2 .. V10 (the T-593 order; R-T580-1 /
R-T588-1 / R-T593-1 code reused read only). Nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge
or registry file is written. No drawing is read: every figure comes from a committed, Checker-merged output.

R-T596-1 (every villa on the engine's line-index scheme):
  (a) SUPERSEDE BY NAME, SAME IDS: a restatement package replaces an earlier package only by its name, on exactly the
      same line ids, and only when the source task is MERGED with a Checker verdict (a row from an unmerged task is
      refused); the rows it does not restate are carried byte-equal in their after state.
  (b) HIGHS NEVER MOVE BY A LOW RESTATEMENT: a restated low may move only within [old low .. old high]; an open high
      stays open; a stated high stays the same number. A restated bound wider than the old one on the LOW side is
      allowed only when the source names the accepted scenario set (R-T595-2: low = min over every accepted scenario).
  (c) A LINE NO EARLIER MANIFEST WROTE (the T-572 footing bound is the candidate's own state) is set by one row whose
      before is the overlay state at its step, never by editing an earlier package.
  (d) NOSING LEDGER BY EDGE ID: with no B7-05 line in the candidate (T-424 adds them), the nosing family is a ledger
      keyed by the T-412 census edge id; a later reading supersedes an edge's status by id (T-412 -> T-434 -> T-598 ->
      Checker status correction), each edge is VALUED (lm + evidence status) or HELD with its bound by name, never 0;
      the developed curtail part of a front edge is its own sub-row owned by the nosing line (UP-STAIR-008: the
      commercial step lm holds the in-lane width only); the T-412 edge census stays 0 doubles / 0 orphans.
Rebuild: `python3 -I research/agents_t596/manifest_v11.py` (`--check`).
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T593_DIR = ROOT / "research/agents_t593"
for _p in (ROOT / "research/agents_t580", ROOT / "research/agents_t588", T593_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import manifest_v10 as M10                                            # noqa: E402  (R-T593-1, read only)

M9 = M10.M9
OV = M10.OV

SCHEMA = "URBAN_T596_WIRING_MANIFEST_V11"
RULE = "R-T596-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V11.json"
IN = {
    "T595": ROOT / "research/agents_t595/out/T595_RESTATEMENTS.json",
    "T598": ROOT / "research/agents_t598/ALSENAN_EDGES_T598.json",
    "T412": ROOT / "research/agents_t412/NOSING_TABLE_T412.csv",
    "T572": ROOT / "research/agents_t572/out/T572_HELD_BOUNDS.json",
    "V9": ROOT / "research/agents_t588/out/WIRING_MANIFEST_V9.json",
    "V10": T593_DIR / "out/WIRING_MANIFEST_V10.json",
    "V10_CODE": T593_DIR / "manifest_v10.py",
}
PINS = {
    "T595": "80d32d7051ee9926201b252d761d20ca1c4609465eb992a67583cbbeb1567964",
    "T598": "2ee67610d6abe69a6ca5dea4ef4a554f9cc2fc9ac9bfc6ad847b22c7e57149b6",
    "T412": "9da81b33ec1b5f4093ccd191223acede3e85ac58b599337b94a28604d83ea34c",
    "T572": "a39e7b4b838e3590d6b456327823618e66b023617cb49be39821ad93ccb264f5",
    "V9": "42463dfe7a94b47166e04cfbf4167ce68dda2bf5b7239a498b81c0f92c95b711",
    "V10": "c05827ef4c27e365e05f565ed89c46493c95ccaf826a490342a96f83e1dcd3fe",
}

# R-T596-1 (a): a source enters V11 only MERGED with a Checker verdict (board text, Verifier)
MERGED = {
    "T-595": {"merge": "568ce15e",
              "verdict": "BOARD T-595 VERIFIER 2026-11-07T09:56Z (e): ST7757.dxf DETAIL OF DOME ring cut draws side-bar "
                         "circles on BOTH vertical faces at TWO levels -> 4 x d14 CONFIRMED; 4 x 8.99725 x 1.209877 = "
                         "43.5426 kg, east ring low 0.122518 -> 0.144289 t (worker 0.144290, rounding, AGREE); F10 "
                         "alone 1.960 / F10 + F 2.176 / outline 2.275 m3 AGREE, S02 low = min over accepted scenarios; "
                         "(f) rows stay HELD bounds, S02 ESTIMATED owner PROVISIONAL, nothing VERIFIED as a line"},
    "T-598": {"merge": "78196c45",
              "verdict": "BOARD T-598 VERIFIER 2026-11-07T12:02Z (e): own read both DXFs; RS-C radials 1.150, curtail "
                         "arcs 0.949440 + 0.672000 = 1.621440 AGREE; MS1-U floor edge 1.150 DRAWING-CONFIRMED; MS2-TR "
                         "1.150 AGREE; 88.500 + 3.450 + 15.421440 = 107.371440 lm, causes residual 0 AGREE; (f) F-C-T598-1 "
                         "MS2-U floor edge on no plan -> ASSUMED - OWNER-APPROVED (Q-46 A), 1.150 unchanged; RS-C 12 "
                         "ASSUMED - OWNER-APPROVED (Q-50 A cond); N01 .. N04 HELD 4.600 .. 6.943, band 0 .. 0.050 HELD"},
    "T-434": {"merge": "a6b325b3",
              "verdict": "BOARD T-434 MERGED a6b325b3 (ST-01 GF winder turn governed by section A-A; landing nosing "
                         "N05 confirmed 1.150, T-598 s.0)"},
}

V9_REBAR = "REBAR_COMPONENTS (T-583; supersedes V8 REBAR_OMISSION by name)"
P_REBAR = "REBAR_COMPONENTS_V2 (T-595 R-T595-1; supersedes V9 REBAR_COMPONENTS by name)"
P_FOOT = "FOOTING_S02_BOUND (T-595 R-T595-2)"
FOOT_LINE = "L-164ae9d338976be9e582"
EAST_RING = "HL:DOME_RING:DOME-1F-E:RING:RING_BEAM_IN_BAY:REBAR"
NOSING_OWNER = "B7-05 nosing line (T-424 adds it; no line in V3.0.58)"
STEP_OWNER = "B7-06 step-lm line of its flight (V9 census)"
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def D(x):
    return None if x is None or x == "" else Decimal(str(x))


def S(x):
    if x is None:
        return None
    x = Decimal(x)
    return "0" if x == 0 else format(x.normalize(), "f")


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def require_merged(task, merged=None):
    """R-T596-1 (a): a row from a task that is not MERGED with a verdict is refused."""
    m = MERGED if merged is None else merged
    if task not in m or not m[task].get("merge") or not m[task].get("verdict"):
        raise ManifestError(f"{task} is not MERGED with a Checker verdict: its rows cannot enter a manifest")
    return m[task]


# ---- R-T596-1 (a)/(b): supersede by name, same ids, highs unchanged --------------------------------------------

def check_restated(old, new, scenario_set=False):
    """old / new: index states. The high never moves; the low moves within [old low .. old high] unless the source
    names the accepted scenario set (then it may go lower, never above the old high)."""
    if new["class"] != old["class"]:
        raise ManifestError(f"class {old['class']} -> {new['class']}: a restatement keeps the class")
    if D(new.get("measured_net")) is not None:
        raise ManifestError("a restated HELD row carries no value")
    oh, nh = D(old.get("held_high")), D(new.get("held_high"))
    if (oh is None) != (nh is None) or (oh is not None and oh != nh):
        raise ManifestError(f"high {oh} -> {nh}: a low restatement never moves the high")
    ol, nl = D(old.get("held_low")), D(new.get("held_low"))
    if (ol is None) != (nl is None):
        raise ManifestError(f"low {ol} -> {nl}: a blank stays blank, a bound stays a bound")
    if nl is None:
        return "UNCHANGED"
    if nl < 0 or (nh is not None and nl > nh):
        raise ManifestError(f"low {nl} outside 0 .. high {nh}")
    if nl < ol and not scenario_set:
        raise ManifestError(f"low {ol} -> {nl} lowered without a named accepted scenario set (R-T595-2)")
    if nh is not None and nl == 0 and nh == 0:
        raise ManifestError("HELD 0 .. 0")
    return "UNCHANGED" if nl == ol else ("RAISED" if nl > ol else "LOWERED")


def supersede(order, old_name, new_pkg):
    """replace old_name BY NAME with new_pkg (same line ids); refuse a missing target or a different id set."""
    new_name, new_rows = new_pkg
    out, found = [], None
    for n, ops in order:
        if n == old_name:
            found = ops
            out.append(new_pkg)
        else:
            out.append((n, ops))
    if found is None:
        raise ManifestError(f"{old_name} not in the overlay order: nothing to supersede")
    if sorted(o["line_id"] for o in found) != sorted(r["line_id"] for r in new_rows):
        raise ManifestError(f"{new_name} does not restate exactly the line ids of {old_name}")
    return out, found


def pkg_rebar_v2(t595, v9_ops, source="T-595", merged=None):
    """T-595 rows -> the 6 V9 REBAR_COMPONENTS lines, same ids, same unit (kg); highs unchanged."""
    src = require_merged(source, merged)
    by_el = {r["row_id"]: r for r in t595["rebar"]["rows"]}
    rows, moved = [], {}
    for op in v9_ops:
        el = op["element_id"]
        t = by_el.get(el)
        if t is None:
            raise ManifestError(f"{el}: no T-595 row")
        if t["unit"] != "t" or op["unit"] != "kg":
            raise ManifestError(f"{el}: unit pair {t['unit']} / {op['unit']} (t -> kg expected)")
        if t["concrete_line"] != op["beside"]["concrete_line"]:
            raise ManifestError(f"{el}: concrete line differs")
        if t["status"] == "HELD_BLANK":
            after = M9.held()
        elif t["status"] == "HELD_RANGE_HIGH_OPEN":
            after = M9.held(M9.kg(t["t_low"]), None)
            if M9.kg(t["t_high_bounded_part"]) != op["beside"]["bounded_part_high_kg"]:
                raise ManifestError(f"{el}: bounded part high moved")
        else:
            raise ManifestError(f"T-595 status {t['status']}")
        how = check_restated(op["after"], after)
        beside = json.loads(json.dumps(op["beside"]))
        beside["version"] = t["version"]
        if how != "UNCHANGED":
            moved[el] = {"kg_before": op["after"]["held_low"], "kg_after": after["held_low"], "how": how}
        if el == EAST_RING:
            beside["F-C-T583-1"] = ("CLOSED by T-595 R-T595-1: the ring cut draws 2 d14 on BOTH vertical faces at two "
                                    "levels (4 bars): +21.771 kg on the low")
        r = M9.row(P_REBAR, "T-595", "ADD", op["line_id"], None, after, op["evidence"]["status"],
                   src["verdict"] if how != "UNCHANGED" else op["evidence"]["verdict_line"],
                   op["item_code"], "kg", el, beside=beside,
                   note=None if how == "UNCHANGED" else "R-T595-1 restated low; high open by name, unchanged")
        rows.append(r)
    return (P_REBAR, rows), moved


def pkg_footing(t595, index, line=FOOT_LINE, source="T-595", merged=None):
    """R-T595-2 on the one footing line no earlier manifest wrote (R-T596-1 (c))."""
    src = require_merged(source, merged)
    c = t595["footing"]["component"]
    if c["line_id"] != line or index[line]["element_id"] != c["element_id"] or index[line]["unit"] != c["unit"]:
        raise ManifestError(f"{line}: not the T-595 component {c['element_id']} {c['unit']}")
    before = OV.state(index[line])
    if D(before["held_low"]) != D(c["t572_low"]) or D(before["held_high"]) != D(c["t572_high"]):
        raise ManifestError(f"{line}: overlay before {before} is not the T-572 V1 bound {c['t572_low']} .. "
                            f"{c['t572_high']}")
    after = M9.held(float(D(c["low"])), float(D(c["high"])))
    how = check_restated(before, after, scenario_set=bool(c.get("scenarios")))
    r = M9.row(P_FOOT, "T-595 R-T595-2", "SET", line, before, after, "HELD", src["verdict"],
               beside={"element": c["element_id"], "low_basis": c["low_basis"], "high_basis": c["high_basis"],
                       "status_label": c["status_label"], "version": t595["footing"]["version"],
                       "his_m3": t595["footing"]["beside_his"]["his_m3"],
                       "his_class": f"{t595['footing']['beside_his']['t572_class']} -> "
                                    f"{t595['footing']['beside_his']['class']}",
                       "who_is_right": "RULE_DIFFERENCE (interpretation: he takes F10 alone), no % on a held line",
                       "same_element_other_families": "unchanged (blinding high split SCENARIO_SPLIT_OPEN; SB1 in "
                                                      "footing 0 .. 0.385; PIT-F10F backfill UNBOUNDED)"},
               note=f"R-T595-2 scenario-set bound: low {how}, high unchanged")
    return (P_FOOT, [r]), how


def family_bounded(t572, index, restated=(), family="B10 FOOTING LINE"):
    """the family's bounded part on the T-572 basis: each BOUNDED component's T-572 bound, except the lines a manifest
    restates (taken from the overlay index). A component whose candidate line holds a different state (T-572 flags it,
    e.g. a Q-28 A point reading) is listed beside, never silently swapped."""
    lo = hi = Decimal(0)
    n, differ = 0, []
    for c in t572["components"]:
        if c["family"] != family or c["kind"] != "BOUNDED":
            continue
        st = index[c["line_id"]]
        if c["line_id"] in restated:
            l, h = D(st["held_low"]), D(st["held_high"])
        else:
            l, h = D(c["low"]), D(c["high"])
            if D(st["held_low"]) != l or D(st["held_high"]) != h:
                differ.append({"line": c["line_id"], "t572": [c["low"], c["high"]],
                               "candidate": [S(D(st["held_low"])), S(D(st["held_high"]))],
                               "t572_flags": c.get("flags", [])})
        lo += l
        hi += h
        n += 1
    return {"components": n, "low": format(lo.quantize(Decimal("0.0001")), "f"),
            "high": format(hi.quantize(Decimal("0.0001")), "f"), "candidate_state_differs": differ}


# ---- R-T596-1 (d): nosing ledger by edge id ----------------------------------------------------------------------

def load_t412(path=None):
    return list(csv.DictReader(Path(path or IN["T412"]).open(encoding="utf-8")))


def t598_eid(t598_id, t412):
    """T-598 edge id -> T-412 census eid (the T-598 RS-C ids carry the front-edge handle)."""
    fixed = {"ST01-MS1U-FLOOR": "ST01-MS1U-N12", "ST01-MS2U-FLOOR": "ST01-MS2U-N12", "ST01-MS2TR": "ST01-MS2TR-N01"}
    if t598_id in fixed:
        return fixed[t598_id]
    if t598_id.startswith("ST02-RSC-"):
        h = t598_id[len("ST02-RSC-"):]
        hits = [r["eid"] for r in t412 if r["flight"] == "RS-C" and r["handles"].split(" ")[:1] == [h]]
        if len(hits) != 1:
            raise ManifestError(f"{t598_id}: {len(hits)} T-412 edges carry front handle {h}")
        return hits[0]
    if any(r["eid"] == t598_id for r in t412):
        return t598_id
    raise ManifestError(f"{t598_id}: no T-412 edge")


# F-C-T598-1 (Checker status correction, binding on T-424): the MS2-U floor edge is drawn on no plan
STATUS_CORRECTIONS = {"ST01-MS2U-N12": ("ASSUMED - OWNER-APPROVED",
                                         "F-C-T598-1: drawn on no plan; existence by the section A-A count (Q-46 A), "
                                         "length by lane 1358")}
T434_CLOSED = {"ST01-MS1T-N05": ("1.150", "DRAWING-CONFIRMED", "T-434")}


def ledger_row(e, status, lm, bound, source, owner, note=None):
    if status not in STATUSES:
        raise ManifestError(f"{e['eid']}: status {status!r} is not a WORKFLOW_CONTROLS s.5 status")
    if status == "HELD":
        if lm is not None:
            raise ManifestError(f"{e['eid']}: a HELD edge carries no value")
        if bound is None or D(bound[1]) is None or D(bound[1]) <= 0:
            raise ManifestError(f"{e['eid']}: HELD edge needs its bound by name (never 0 .. 0, never blank)")
    else:
        if lm is None or D(lm) <= 0:
            raise ManifestError(f"{e['eid']}: a valued edge needs lm > 0 (missing is HELD, never 0)")
    return {"eid": e["eid"], "stair": e["stair"], "flight": e["flight"], "kind": e["kind"],
            "in_step_basis": e["in_step_basis"] == "yes", "t412_status": e["status"], "status": status,
            "lm": S(D(lm)) if lm is not None else None, "held_bound_lm": [S(D(b)) for b in bound] if bound else None,
            "source": source, "owner": owner, **({"note": note} if note else {})}


def nosing_ledger(t412, t598, merged=None):
    require_merged("T-598", merged)
    require_merged("T-434", merged)
    res = t598["result"]
    by = {}
    subs = []
    for x in res["edges"]:
        if x["id"].endswith("-BAND"):
            continue
        by[t598_eid(x["id"], t412)] = x
    rows = []
    for e in t412:
        owner = STEP_OWNER if e["in_step_basis"] == "yes" else NOSING_OWNER
        if e["status"] == "DRAWING-CONFIRMED":
            rows.append(ledger_row(e, "DRAWING-CONFIRMED", e["qty_lm"], None, "T-412", owner))
        elif e["eid"] in T434_CLOSED:
            lm, st, src = T434_CLOSED[e["eid"]]
            if D(e["beside_lm"]) != D(lm):
                raise ManifestError(f"{e['eid']}: T-412 beside {e['beside_lm']} != T-434 {lm}")
            rows.append(ledger_row(e, st, lm, None, src, owner))
        elif e["eid"] in by:
            x = by.pop(e["eid"])
            st, note = x["status"], None
            if e["eid"] in STATUS_CORRECTIONS:
                st, note = STATUS_CORRECTIONS[e["eid"]]
            if st == "HELD":
                rows.append(ledger_row(e, "HELD", None, x["bound"], "T-598", owner, note=x["cause"]))
            else:
                curt = D(x.get("curtail_m")) or Decimal(0)
                lane = D(x["lm"]) - curt
                rows.append(ledger_row(e, st, lane, None, "T-598", owner, note=note))
                if curt > 0:
                    if D(x["in_lane_m"]) != lane:
                        raise ManifestError(f"{e['eid']}: in-lane {x['in_lane_m']} != lm - curtail {lane}")
                    subs.append({**ledger_row(e, st, curt, None, "T-598 R-T598-2", NOSING_OWNER,
                                              note="developed curtail arc of the front edge; the commercial step lm "
                                                   "holds the in-lane width only (UP-STAIR-008, T-598 s.6)"),
                                 "eid": f"{e['eid']}#CURTAIL", "part_of": e["eid"]})
        else:
            raise ManifestError(f"{e['eid']}: T-412 HELD edge with no later reading (stays HELD by name: add it)")
    if by:
        raise ManifestError(f"T-598 edges with no T-412 edge: {sorted(by)}")
    for x in res["edges"]:
        if x["id"].endswith("-BAND"):
            part = t598_eid(x["id"][:-len("-BAND")], t412)
            e = next(r for r in t412 if r["eid"] == part)
            subs.append({**ledger_row(e, "HELD", None, x["bound"], "T-598", NOSING_OWNER, note=x["cause"]),
                         "eid": f"{part}#BAND", "part_of": part})
    return rows, subs


def ledger_totals(rows, subs):
    allr = rows + subs
    v = [r for r in allr if r["status"] != "HELD"]
    h = [r for r in allr if r["status"] == "HELD"]
    by_status, by_owner = {}, {}
    for r in v:
        by_status[r["status"]] = by_status.get(r["status"], Decimal(0)) + D(r["lm"])
        by_owner[r["owner"]] = by_owner.get(r["owner"], Decimal(0)) + D(r["lm"])
    return {"edges": len(rows), "edges_valued": sum(r["status"] != "HELD" for r in rows),
            "edges_held": sum(r["status"] == "HELD" for r in rows), "sub_rows": len(subs),
            "valued_lm": S(sum((D(r["lm"]) for r in v), Decimal(0))),
            "valued_lm_by_status": {k: S(x) for k, x in sorted(by_status.items())},
            "valued_lm_by_owner": {k: S(x) for k, x in sorted(by_owner.items())},
            "held_by_name": [{"eid": r["eid"], "bound_lm": r["held_bound_lm"]} for r in h],
            "held_bound_lm": [S(sum((D(r["held_bound_lm"][0]) for r in h), Decimal(0))),
                              S(sum((D(r["held_bound_lm"][1]) for r in h), Decimal(0)))]}


def census_edges(t412, rows):
    """the T-412 census with each edge's status superseded by id (in_step_basis unchanged)."""
    st = {r["eid"]: r["status"] for r in rows}
    out = []
    for e in M9.load_edges():
        e = dict(e, status=st[e["eid"]])
        out.append(e)
    if len(out) != len(t412):
        raise ManifestError("census and T-412 differ in edge count")
    return out


# ---- overlay ----------------------------------------------------------------------------------------------------

def v10_state():
    """the T-593 build up to its overlay (read only), so V11 steps from the exact V10 state."""
    idx, order9, rul9, after9, rep9, t584 = M10.v9_state()
    t592, t585 = M10._json(M10.IN["T592"]), M10._json(M10.IN["T585"])
    Pd, door_rows, _, _ = M10.pkg_door_steps(t592, after9, M10.GATE_LINE)
    Ps, sk_rows, _ = M10.pkg_stair_skirting(M10.load_pieces(), t585, after9)
    order, _ = M10.absorb(order9, M10.ABSORB[0], M10.ABSORB[1], OV.state(after9[M10.ABSORB[1]]))
    order10 = order + [(Pd, door_rows), (Ps, sk_rows)]
    rul10 = rul9 + M10.RULINGS_V10
    after10, rep10 = OV.apply(idx, order10, rul10)
    return idx, order10, rul10, after10, rep10, t584


def build():
    pins()
    t595, t598, t572, v10j = _json(IN["T595"]), _json(IN["T598"]), _json(IN["T572"]), _json(IN["V10"])
    t412 = load_t412()
    idx, order10, rul10, after10, rep10, t584 = v10_state()
    if len(after10) != v10j["overlay"]["lines"]["after_v10"]:
        raise ManifestError("V10 state rebuild differs from the committed V10 line count")
    v9_ops = next(ops for n, ops in order10 if n == V9_REBAR)
    rebar_pkg, moved = pkg_rebar_v2(t595, v9_ops)
    foot_pkg, foot_how = pkg_footing(t595, after10)
    for _, rows in (rebar_pkg, foot_pkg):
        M9.validate_rows(rows)
    order11, old = supersede(order10, V9_REBAR, rebar_pkg)
    order11 = order11 + [foot_pkg]
    after11, rep = OV.apply(idx, order11, rul10)
    v11_lines = {r["line_id"] for _, rows in (rebar_pkg, foot_pkg) for r in rows}
    others = sorted(k for k in set(after10) | set(after11) if k not in v11_lines and after10.get(k) != after11.get(k))
    if others:
        raise ManifestError(f"lines V11 does not write changed: {others[:5]}")
    # rows V11 restates without a change are byte-equal in their after state (R-T596-1 (a))
    carried = [o["line_id"] for o in old if o["element_id"] not in moved]
    for o in old:
        new = after11[o["line_id"]]
        if o["element_id"] not in moved and not OV.same_state(OV.state(new), o["after"]):
            raise ManifestError(f"{o['line_id']}: carried row changed")
    fam10, fam11 = family_bounded(t572, after10, {FOOT_LINE}), family_bounded(t572, after11, {FOOT_LINE})
    fv2 = t595["footing"]["family_v2"]
    if D(fam11["low"]) != D(fv2["bounded_part_low"]) or D(fam11["high"]) != D(fv2["bounded_part_high"]):
        raise ManifestError(f"footing family bounded part {fam11} != T-595 {fv2['bounded_part_low']} .. "
                            f"{fv2['bounded_part_high']}")
    lows = lambda ops, st: sum((D(st[o["line_id"]]["held_low"]) for o in ops            # noqa: E731
                                if D(st[o["line_id"]]["held_low"]) is not None), Decimal(0))
    kg10, kg11 = lows(old, after10), lows(old, after11)
    if (kg11 / 1000).quantize(Decimal("0.000001")) != D(t595["rebar"]["totals"]["t_low"]):
        raise ManifestError(f"bounded rebar low {kg11} kg != T-595 {t595['rebar']['totals']['t_low']} t")
    # nosing ledger
    rows, subs = nosing_ledger(t412, t598)
    tot = ledger_totals(rows, subs)
    na = t598["result"]["nosing_after"]
    if D(tot["valued_lm"]) != D(na["valued_lm"]) or tot["edges_valued"] != na["edges_valued"] \
            or tot["edges_held"] != na["edges_held"]:
        raise ManifestError(f"nosing ledger {tot['valued_lm']} / {tot['edges_valued']} != T-598 {na}")
    if [D(x) for x in tot["held_bound_lm"]] != [D(x) for x in t598["result"]["held_bound_lm"]]:
        raise ManifestError("held bound differs from T-598")
    edges11 = census_edges(t412, rows)
    cen = M9.census_on(after11, edges11, t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError(f"nosing census doubles {cen['doubles']} orphans {cen['orphans']}")
    sub_owners = {s["eid"]: s["owner"] for s in subs}
    rec = t598["result"]["reconciliation"]
    causes = sum((D(c["lm"]) for s in rec.values() for c in s["causes"]), Decimal(0))
    his = D(t598["result"]["his_total"])
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    t10, t11 = OV.totals(after10), OV.totals(after11)
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-596", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "supersedes": {
            V9_REBAR: {"by": P_REBAR, "same_line_ids": sorted(o["line_id"] for o in old),
                       "op_ids": {o["op_id"]: f"{P_REBAR}|T-595|{o['line_id']}" for o in old}},
            f"candidate T-572 V1 bound on {FOOT_LINE}": {"by": P_FOOT, "why": "no earlier manifest wrote the line "
                                                                            "(R-T596-1 (c))"},
            "T-412 census edge statuses (read by the V9 / V10 census)": {
                "by": "NOSING_LEDGER_V11 (T-434 + T-598 + F-C-T598-1), by edge id",
                "edges": sorted(r["eid"] for r in rows if r["t412_status"] == "HELD")},
        },
        "rebar": {"moved": moved, "carried_byte_equal": carried,
                  "bounded_low_kg": {"v10": S(kg10), "v11": S(kg11), "delta": S(kg11 - kg10)},
                  "board_low_t": "0.789554 (Checker: 0.767783 + 0.021771; T-595 sums the rounded row lows "
                                 "0.789555: 1 g rounding, the row value 144.29 kg is T-595's)",
                  "highs": "open by name on every row, unchanged (ring depth, links, hooks, laps, anchorage)"},
        "footing": {"line": FOOT_LINE, "before": OV.state(after10[FOOT_LINE]), "after": OV.state(after11[FOOT_LINE]),
                    "low": foot_how, "family_bounded_part_m3": {"v10": fam10, "v11": fam11},
                    "family_total": "not stateable (boundary pad count, Q-28 A): unchanged"},
        "nosing": {"ledger": rows, "sub_rows": subs, "totals": tot,
                   "census_after_v11": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"]), "by_stair": cen["by_stair"]},
                   "sub_row_owners": sub_owners,
                   "his": {"lm": S(his), "his_minus_ours": S(his - D(tot["valued_lm"])), "causes_sum": S(causes),
                           "residual": S(his - D(tot["valued_lm"]) - causes), "by_stair": rec,
                           "note": "signed his - ours, no %"},
                   "candidate_lines": "none (B7-05 has no line in V3.0.58; T-424 wires the ledger)"},
        "rows": [dict(r, package=n) for n, rs in (rebar_pkg, foot_pkg) for r in rs],
        "overlay": {
            "lines": {"base": len(idx), "after_v10": len(after10), "after_v11": len(after11)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order11],
            "flagged_rows": [r for r in rep["rows"] if r["status"] != "APPLIED"],
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                    # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "other_lines_changed_vs_v10_overlay": others,
            "v11_vs_v10_totals": OV.diff_totals(t10, t11),
        },
        "findings": {
            "F-T596-1": "the curtail parts (ST02-RSC-N01 0.949440, -N02 0.672000 lm) are owned by the B7-05 nosing "
                        "line, not the step line (UP-STAIR-008, T-598 s.6): T-424 must carry them as sub-rows of the "
                        "edge, or they are orphaned",
            "F-T596-2": "ST02-RSC-N01: T-412 beside 1.200 = in-lane 1.150 (valued) + band 0 .. 0.050 (HELD sub-row); "
                        "the 0.050 is never valued with the edge",
            "F-T596-3": "board / T-595 low 0.789554 vs 0.789555 t is rounding of parts (1 g); the manifest carries "
                        "T-595's row values (144.29 kg east ring)",
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-596 manifest V11: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
