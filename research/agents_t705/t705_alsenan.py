"""T-705 WIRING READINESS ROUND 3 on ARCH_TAKEOFF_V3.0.70 (development villa; method R-T705-1 in t705_rules.py and
R-T698-1 1.1.0 are every villa). Research only: no candidate, released, rule / knowledge version or registry file is
touched; no quantity is produced, changed or wired; no drawing is opened.

The pieces merged since T-698 that no V3.0.70 line reads yet: T-697 (B4-09 corner beads), T-700 (earthworks round 2,
its 21-row wiring form; it restates T-695's 20-line census and the strap trench), T-701 R-T701-2 (annex GF-01 / GF-04
plaster ENGINE_WRONG), T-702 (tiles round 3: beam-crossing plaster bands, GF-10 / GF-11 wall tile, roof layers, stair
core), T-691 (roof WP 115.814, upturn, pantry pieces, 18 penetration lines) and T-695 (earthworks census, strap trench).
Every ledger row is mapped by line id to V3.0.70 (stale 0 required), carries its HELD fields and marker, names its owner
trade per the element register, gets a wire action (KEEP / CHANGE / ADD / NONE) and the ordered hub packages are stated
with their changed-line counts.

Inputs: merged repository files only (sha256-pinned in PINS). T-314 r2 stage: the T-698 pinned extract (blob 040ed5f9).

Rebuild:  bash scripts/agent_env.sh run --tree task-T-705 research/agents_t705/t705_alsenan.py --write
Check:    bash scripts/agent_env.sh run --tree task-T-705 research/agents_t705/t705_alsenan.py --check
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t705_rules as R  # noqa: E402

R698 = R.R698
SCHEMA = "URBAN_T705_WIRING_READINESS_R3_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.70"
IDX70 = "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
IDX69 = "research/agents_t687/out/LINE_INDEX_V3_0_69.json"
IDX68 = "research/agents_t672/out/LINE_INDEX_V3_0_68.json"
IDX67 = "research/agents_t682/out/LINE_INDEX_V3_0_67.json"
T697 = "research/agents_t697/out/T697_BEAD_LEDGER.csv"
T697S = "research/agents_t697/out/T697_SUMMARY.json"
T700 = "research/agents_t700/WIRING_T700.csv"
T695 = "research/agents_t695/CENSUS_T695.csv"
T701 = "research/agents_t701/out/T701_RECONCILE.json"
T702 = "research/agents_t702/out/T702_TILES_ROUND3.json"
T691 = "research/agents_t691/out/T691_WP_ROUND2.json"
PEND = "research/agents_t698/in/PENDING_STAGES_T698.json"
PINS = [IDX70, IDX69, IDX68, IDX67, T697, T697S, T700, T695, T701, T702, T691, PEND]
MERGES = {   # board MERGED cells (Verifier, Gate A PASS); the Checker verdicts named there are the evidence status
    "T-697": "MERGED 6ed575ad (published bbda7212), Gate A PASS; F-T697-1 G1 and F-T697-3 arris once CONFIRMED",
    "T-695": "MERGED bbda7212, Gate A PASS (strap trench re-measured)",
    "T-700": "MERGED 8210b549, Gate A PASS (Z2 re-measured)",
    "T-701": "MERGED 65083ee7, Gate A PASS (GF-04 / 1F-04 re-measured; R-T701-2 CONFIRMED)",
    "T-702": "MERGED b90d85af, Gate A PASS (GF-14 B11 re-measured; F-V702-1 residual named)",
    "T-691": "MERGED 5e4fdc33, Gate A PASS (dome chords re-measured)",
}
OUT_JSON = HERE / "out" / "T705_READINESS.json"
OUT_CSV = HERE / "out" / "T705_ROWS.csv"
BEAD_HOST_CODES = {"FIN.PLASTER", "FIN.EXT.FINISH", "ARCH.FACADE"}
EARTH_CODES = {"STR.EARTH.EXCAVATION", "STR.EARTH.BACKFILL", "STR.EARTH.DISPOSAL"}
ROOF_CODES = {"FIN.ROOF.SCREED", "FIN.ROOF.FINISH", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION"}
WP_CODES = {"FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN", "FIN.WP.MEMBRANE_ROLLS", "FIN.WP.WALL_UPTURN", "FIN.WP.PENETRATION",
            "FIN.WP.TERMINATION", "FIN.WP.DOORWAY", "FIN.WP.DOORWAY_TRANSITION_NR"}
FLOOR_CODES = {"FIN.FLOOR.FINISH_HELD", "FIN.FLOOR.PORCELAIN", "FIN.MARBLE.LANDING"}
# register rulings (ELEMENT_REGISTER.md, Lead 2026-11-11): owner trade by family
OWNER = {
    "B4-09": "plaster B4-09 corner beads lm (ruling 04:20; arris once 08:25)",
    "B6-06": "B6-06 entrance / lift surround (ruling 04:20: lift-shaft arrises)",
    "B5": "plaster FIN.PLASTER m2 (heights rule Q-72)",
    "B5-band": "plaster FIN.PLASTER m2 (ruling 00:20: wet-room wall band above the finished ceiling)",
    "B2": "wall tile FIN.WALL.TILE m2",
    "B13": "roof build-up FIN.ROOF.* (falls carried once by FIN.ROOF.SCREED, R-T702-3)",
    "B3/B7-04": "floor / stair landing finishes (one owner per surface, R-T702-4 / R-T702-5)",
    "B8": "waterproofing FIN.WP.*",
    "B1": "earthworks STR.EARTH.* (lane S)",
}


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def cload(rel):
    with open(_p(rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def index(rel):
    return {ln["line_id"]: ln for ln in jload(rel)["lines"]}


def num(s):
    return None if s in (None, "", "None") else float(s)


def row(piece, family, ledger, key, cls, host, reason, *, owner, element, after=None, action=R.NONE,
        action_reason="", new_line_key=None, ledger_state="", qty=None, lo=None, hi=None, unit="", **kw):
    held = qty is None and ledger_state not in ("", "NOT A BEAD", "NOT_APPLICABLE", "KEEP")
    return dict({"piece": piece, "family": family, "ledger": ledger, "row": key, "class": cls, "host_line_id": host,
                 "reason": reason, "owner_family": family if family != "B5-band" else "B5-band", "owner": owner,
                 "element": element, "ledger_state": ledger_state, "qty": R.r6(qty), "lo": R.r6(lo), "hi": R.r6(hi),
                 "held": held, "unit": unit, "after": after, "action": action, "action_reason": action_reason,
                 "new_line_key": new_line_key}, **kw)


def mapped(host, allowed, tgt, ref, pend, pend_name):
    return R698.classify(host, allowed_codes=allowed, target=tgt, reference=ref, pending_changed=pend,
                         pending_name=pend_name)


def act(a, tgt, host, cls):
    if cls in (R698.STALE, R698.WRONG, R698.AMBIGUOUS, R698.NO_HOST) or host is None:
        return R.NONE, f"class {cls}: not wireable as stated"
    return R.wire_action(a, tgt.get(host))


# ===================================================================================== T-701 R-T701-2 (plaster, B5)
def p701(tgt, i69):
    d = jload(T701)["annex_plaster_coverage"]
    out = []
    for room in sorted(d):
        e = d[room]
        full, cls0, why = R.resolve_id(e["line"], tgt)
        lo, hi = (float(x) for x in e["datum_bound"])
        a = R.after(R.BOUND, lo=lo, hi=hi, note=f"R-T701-2 ENGINE_WRONG: S 3.79 point inside the datum bound; status "
                                                f"{e['status']}")
        if cls0:
            out.append(row("T-701", "B5", "T-701 R-T701-2", room, cls0, None, why, owner=OWNER["B5"], element=room,
                           after=a, ledger_state="HELD", lo=lo, hi=hi, unit="m2"))
            continue
        cls, host, reason = mapped(full, {"FIN.PLASTER"}, tgt, i69, {}, "")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-701", "B5", "T-701 R-T701-2", room, cls, host, f"{why}; {reason}", owner=OWNER["B5"],
                       element=tgt[full]["element_id"], after=a, action=ac, action_reason=ar, ledger_state="HELD",
                       lo=lo, hi=hi, unit="m2"))
    return out


# ========================================================================================= T-702 tiles round 3
def p702(tgt, i69):
    d = jload(T702)
    out = []
    for r in d["c_beam_crossings"]["rooms"]:        # plaster bands above the ceiling (ruling 00:20: owner plaster)
        lo, hi = (float(x) for x in r["after"]["band"])
        a = R.after(R.BOUND, lo=lo, hi=hi, note=r["after"]["status"])
        cls, host, reason = mapped(r["line_id"], {"FIN.PLASTER"}, tgt, i69, {}, "")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-702", "B5-band", "T-702 (c) beam crossings", r["room"], cls, host, reason,
                       owner=OWNER["B5-band"], element=tgt[r["line_id"]]["element_id"], after=a, action=ac,
                       action_reason=ar, ledger_state="HELD", lo=lo, hi=hi, unit="m2"))
    for r in d["b_stair_core"]["wall_tile"]:
        lo, hi = float(r["after"]["held_low"]), float(r["after"]["held_high"])
        a = R.after(R.BOUND, lo=lo, hi=hi, note=r["status"])
        cls, host, reason = mapped(r["line_id"], {"FIN.WALL.TILE"}, tgt, i69, {}, "")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-702", "B2", "T-702 (b) wall tile", r["room"], cls, host, reason, owner=OWNER["B2"],
                       element=tgt[r["line_id"]]["element_id"], after=a, action=ac, action_reason=ar,
                       ledger_state="HELD", lo=lo, hi=hi, unit="m2", backing=r["backing"]))
    for r in d["a_roof_layers"]["rows"]:
        t = r["t702"]
        if t.get("quantity") is not None:
            a, st, q, lo, hi = R.after(R.VALUE, value=float(t["quantity"]), note=t["state"]), "MEASURED", \
                float(t["quantity"]), None, None
        elif t.get("low") is not None:
            lo, hi = num(t["low"]), num(t.get("high"))
            a, st, q = R.after(R.BOUND, lo=lo, hi=hi, note=t["state"]), "HELD", None
        else:
            a, st, q, lo, hi = R.after(R.BLANK, note=f"{t['state']}: {t['why'][:80]}"), "HELD", None, None, None
        cls, host, reason = mapped(r["line_id"], ROOF_CODES, tgt, i69, {}, "")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-702", "B13", "T-702 (a) roof layers", f"{r['zone']}:{r['layer']}", cls, host, reason,
                       owner=OWNER["B13"], element=tgt[r["line_id"]]["element_id"], after=a, action=ac,
                       action_reason=ar, ledger_state=st, qty=q, lo=lo, hi=hi, unit=r["v3069"]["unit"]))
    for s in d["b_stair_core"]["surfaces"]:
        fam = "B3/B7-04"
        q = num(s["area_m2"])
        if s["v3069"] is None:
            out.append(row("T-702", fam, "T-702 (b) stair core", s["surface"], R698.NO_HOST, None,
                           f"no line of its own: {s['t493_line_state']} (owner trade {s['owner_trade']})",
                           owner=OWNER[fam], element=s["surface"], ledger_state="MEASURED" if q else "HELD", qty=q,
                           unit="m2"))
            continue
        lid = s["v3069"]["line_id"]
        cls, host, reason = mapped(lid, FLOOR_CODES, tgt, i69, {}, "")
        a = R.after(R.NOPROP, note="statement of the existing line (one owner per surface)")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-702", fam, "T-702 (b) stair core", s["surface"], cls, host, reason, owner=OWNER[fam],
                       element=tgt[lid]["element_id"], after=a, action=ac, action_reason=ar, ledger_state="KEEP",
                       qty=q, unit="m2"))
    for lid, b in sorted(d["b_stair_core"]["bounds_v3069"].items()):
        cls, host, reason = mapped(lid, FLOOR_CODES, tgt, i69, {}, "")
        a = R.after(R.NOPROP, note="held bound stated, not changed by T-702")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-702", "B3/B7-04", "T-702 (b) held bounds", lid, cls, host, reason, owner=OWNER["B3/B7-04"],
                       element=tgt[lid]["element_id"], after=a, action=ac, action_reason=ar, ledger_state="HELD",
                       lo=b["held"][0], hi=b["held"][1], unit="m2"))
    return out


# ============================================================================================ T-691 WP round 2
def p691(tgt, i67):
    d = jload(T691)
    out = []
    by_elem = {(l["item_code"], l["element_id"]): k for k, l in tgt.items()}
    roof = by_elem[("FIN.WP.ROOF", "2F-ROOF-AT379:wp_membrane")]
    up = by_elem[("FIN.WP.ROOF_UPTURN", "2F-ROOF-AT379:wp_upturn")]
    rolls = by_elem[("FIN.WP.MEMBRANE_ROLLS", "2F-ROOF-AT379:wp_rolls_to_buy")]
    c = d["roof_F_V685_1"]["corrected"]
    lo, hi = c["band_m2"]
    items = [("roof membrane 2F", roof, R.after(R.BOUND, lo=lo, hi=hi, note=c["status"][:120]), "HELD", None, lo, hi,
              "m2"),
             ("roof upturn 2F", up, R.after(R.VALUE, value=d["roof_F_V685_1"]["upturn"]["corrected_lm"],
                                             note="dome rings as circumferences"), "MEASURED",
              d["roof_F_V685_1"]["upturn"]["corrected_lm"], None, None, "lm"),
             ("roof rolls 2F", rolls, R.after(R.NOPROP, note=d["roof_F_V685_1"]["rolls"][:100]), "KEEP", None, None,
              None, "pcs")]
    for key, lid, a, st, q, lo_, hi_, unit in items:
        cls, host, reason = mapped(lid, WP_CODES, tgt, i67, {}, "")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-691", "B8", "T-691 roof F-V685-1", key, cls, host, reason, owner=OWNER["B8"],
                       element=tgt[lid]["element_id"], after=a, action=ac, action_reason=ar, ledger_state=st, qty=q,
                       lo=lo_, hi=hi_, unit=unit))
    for r in d["measurable_now"]:
        if r["line"].startswith("L-"):
            lo, hi = (float(x) for x in r["after"].split(".."))
            a = R.after(R.BOUND, lo=lo, hi=hi, note=r["status"])
            cls, host, reason = mapped(r["line"], WP_CODES, tgt, i67, {}, "")
            ac, ar = act(a, tgt, host, cls)
            out.append(row("T-691", "B8", "T-691 measurable now", r["item"], cls, host, reason, owner=OWNER["B8"],
                           element=tgt[r["line"]]["element_id"], after=a, action=ac, action_reason=ar,
                           ledger_state="HELD", lo=lo, hi=hi, unit=r["unit"]))
        else:
            v = float(r["after"])
            a = R.after(R.VALUE, value=v, note=r["status"])
            out.append(row("T-691", "B8", "T-691 measurable now", r["line"], R698.NO_HOST, None,
                           "MISSING line (no candidate line at any version): the package adds it", owner=OWNER["B8"],
                           element=r["line"], after=a, action=R.ADD, action_reason="new line",
                           new_line_key=r["line"], ledger_state="MEASURED", qty=v, unit=r["unit"]))
    for r in d["penetrations"]["rows"]:
        lo, hi = r["after_low"], r["after_high"]
        a = R.after(R.VALUE, value=lo, note=r["status"]) if lo == hi else \
            R.after(R.BOUND, lo=lo, hi=hi, note=f"{r['status']}: {r['open_term']}")
        q = lo if lo == hi else None
        if not r["line"].startswith("L-"):
            out.append(row("T-691", "B8", "T-691 penetrations", r["room"], R698.NO_HOST, None,
                           "MISSING line: the package adds it", owner=OWNER["B8"], element=r["line"], after=a,
                           action=R.ADD, action_reason="new line", new_line_key=r["line"],
                           ledger_state="MEASURED" if q else "HELD", qty=q, lo=None if q else lo,
                           hi=None if q else hi, unit="pcs"))
            continue
        cls, host, reason = mapped(r["line"], WP_CODES, tgt, i67, {}, "")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-691", "B8", "T-691 penetrations", r["room"], cls, host, reason, owner=OWNER["B8"],
                       element=tgt[r["line"]]["element_id"], after=a, action=ac, action_reason=ar,
                       ledger_state="MEASURED" if q else "HELD", qty=q, lo=None if q else lo, hi=None if q else hi,
                       unit="pcs"))
    return out


# ========================================================================================= T-700 / T-695 earthworks
def ew_after(r):
    b = r["bound"]
    if b == "BLANK":
        return R.after(R.BLANK, note=(r.get("basis") or r.get("proposal") or "")[:100]), "HELD", None, None, None
    if b == "RANGE":
        lo, hi = num(r["low_m3"]), num(r["high_m3"])
        return R.after(R.BOUND, lo=lo, hi=hi, note=(r.get("basis") or r.get("proposal") or "")[:100]), "HELD", None, lo, hi
    if b == "AT_LEAST":
        lo = num(r["low_m3"])
        return R.after(R.BOUND, lo=lo, hi=None, note="AT_LEAST: " + (r.get("basis") or r.get("proposal") or "")[:90]), "HELD", None, lo, None
    if b == "ZERO_BY_GEOMETRY":
        return R.after(R.ZERO, note=(r.get("basis") or r.get("proposal") or "")[:100]), "CALCULATED_ZERO", 0.0, None, None
    if b == "VALUE":
        v = num(r["value_m3"])
        return R.after(R.VALUE, value=v, note=(r.get("basis") or r.get("proposal") or "")[:100]), "MEASURED", v, None, None
    raise R.ReadinessError(f"unknown bound {b}")


def p700(tgt, i69):
    out = []
    for r in cload(T700):
        a, st, q, lo, hi = ew_after(r)
        if r["line_id"].startswith("NEW"):
            out.append(row("T-700", "B1", "T-700 wiring form", r["element_id"], R698.NO_HOST, None,
                           f"{r['line_id']}: a new line the package adds", owner=OWNER["B1"], element=r["element_id"],
                           after=a, action=R.ADD, action_reason="split line", new_line_key=r["element_id"],
                           ledger_state=st, qty=q, lo=lo, hi=hi, unit="m3", missing=r["missing_input"]))
            continue
        cls, host, reason = mapped(r["line_id"], EARTH_CODES, tgt, i69, {}, "")
        ac, ar = act(a, tgt, host, cls)
        out.append(row("T-700", "B1", "T-700 wiring form", r["element_id"], cls, host, reason, owner=OWNER["B1"],
                       element=r["element_id"], after=a, action=ac, action_reason=ar, ledger_state=st, qty=q,
                       lo=lo, hi=hi, unit="m3", missing=r["missing_input"]))
    return out


def p695(tgt, i68, form_rows):
    """T-695's census is restated row by row in the T-700 form (one count): mapped, action NONE (wired through T-700)."""
    form = {r["host_line_id"]: r for r in form_rows if r["host_line_id"]}
    out = []
    for r in cload(T695):
        a, st, q, lo, hi = ew_after(r)
        cls, host, reason = mapped(r["line_id"], EARTH_CODES, tgt, i68, {}, "")
        f = form.get(r["line_id"])
        if f is None:
            raise R.ReadinessError(f"T-695 line {r['line_id']} is not restated in the T-700 form")
        same = R.after_text(a) == R.after_text(f["after"])
        out.append(row("T-695", "B1", "T-695 census", r["element_id"], cls, host, reason, owner=OWNER["B1"],
                       element=r["element_id"], after=a, action=R.NONE,
                       action_reason=("restated in the T-700 form unchanged" if same else
                                      f"superseded in the T-700 form: {R.after_text(a)} -> {R.after_text(f['after'])}"),
                       ledger_state=st, qty=q, lo=lo, hi=hi, unit="m3", superseded_by_t700=not same))
    return out


# ======================================================================================== T-697 B4-09 corner beads
def p697(tgt, i68, pend, pend_name):
    out = []
    for r in cload(T697):
        st = r["status"]
        hosts = R.split_hosts(r["host_line"])
        qty = num(r["owner_m"]) if st in ("ASSUMED — OWNER-APPROVED", "DRAWING-CONFIRMED") else None
        lo, hi = num(r["held_low"]), num(r["held_high"])
        extra = {"dwg_low": num(r["dwg_low"]), "dwg_high": num(r["dwg_high"]), "binding": r["binding"],
                 "scope": r["scope"], "evidence": st}
        kw = dict(owner=OWNER["B4-09"], element=r["edge_id"], ledger_state=st if st != "HELD" else "HELD", qty=qty,
                  lo=lo, hi=hi, unit="lm")
        if r["binding"] == "OWNED_BY_B6-06":
            ok = r["owning_line"] in tgt
            if not ok:
                raise R.ReadinessError(f"{r['edge_id']}: owning B6-06 line {r['owning_line']} absent from V3.0.70")
            out.append(row("T-697", "B6-06", "T-697 bead ledger", r["edge_id"], R698.NO_HOST, None,
                           f"owned by B6-06 line {r['owning_line']} (present in V3.0.70): no B4-09 bead",
                           **dict(kw, owner=OWNER["B6-06"]), action=R.NONE, action_reason="other trade owns the arris",
                           **extra))
            continue
        if not hosts:
            out.append(row("T-697", "B4-09", "T-697 bead ledger", r["edge_id"], R698.NO_HOST, None,
                           f"no host line: HELD by name ({r['cause'][:90]})", **kw, action=R.NONE,
                           action_reason="named HELD item, no line", **extra))
            continue
        if len(hosts) > 1:
            out.append(row("T-697", "B4-09", "T-697 bead ledger", r["edge_id"], R698.AMBIGUOUS, None,
                           f"{len(hosts)} carriers {hosts}: split by carrier before wiring (R-T698-1 6b)", **kw,
                           action=R.NONE, action_reason="split first", carriers=hosts, **extra))
            continue
        cls, host, reason = mapped(hosts[0], BEAD_HOST_CODES, tgt, i68, pend, pend_name.get(hosts[0], ""))
        bead = st not in ("NOT A BEAD", "NOT_APPLICABLE")
        ac, ar = (R.ADD, f"one B4-09 lm line bound to host {host}") if bead and host else \
            (R.NONE, "not a bead (plaster stops / tiled / other owner): no B4-09 quantity")
        out.append(row("T-697", "B4-09", "T-697 bead ledger", r["edge_id"], cls, host, reason, **kw, action=ac,
                       action_reason=ar, new_line_key=f"B4-09@{host}" if ac == R.ADD else None,
                       host_class=tgt[host]["class"] if host in tgt else None, **extra))
    return out


# =================================================================================================== build
def bead_census(rows):
    c = defaultdict(lambda: {"rows": 0, "measured_m": 0.0, "held_rows": 0, "held_low": 0.0, "held_high": 0.0,
                             "held_blank": 0})
    for r in rows:
        if r["piece"] != "T-697" or r["family"] != "B4-09" or r["evidence"] in ("NOT A BEAD",):
            continue
        k = c[r["scope"]]
        k["rows"] += 1
        if r["qty"] is not None:
            k["measured_m"] += r["qty"]
        else:
            k["held_rows"] += 1
            if r["lo"] is None:
                k["held_blank"] += 1
            else:
                k["held_low"] += r["lo"]
                k["held_high"] += r["hi"]
    return {s: {kk: (round(v, 6) if isinstance(v, float) else v) for kk, v in k.items()} for s, k in sorted(c.items())}


def changes(rows):
    return [{"piece": r["piece"], "line_id": r["host_line_id"] or r["new_line_key"], "action": r["action"],
             "before": R698.state_text(None) if r["action"] == R.ADD else r["action_reason"].split(" -> ")[0],
             "after": R.after_text(r["after"]), "unit": r["unit"], "owner_family": r["owner_family"]}
            for r in rows if r["action"] in (R.CHANGE, R.ADD) and r["piece"] != "T-697"]


def build():
    tgt, i69, i68, i67 = index(IDX70), index(IDX69), index(IDX68), index(IDX67)
    P = jload(PEND)
    s314 = P["T-314"]
    R.check_arris_once(s314["rows"])
    chg314 = {r["line_id"]: f"T-314 r3 {r['before']['state']} -> {r['after']['state']} {r['net']}"
              for r in s314["rows"] if r["action"] == "CHANGE"}
    rows701, rows702 = p701(tgt, i69), p702(tgt, i69)
    # rule 4: lines the plaster package changes this round, under the B4-09 rows that rest on them
    plaster_chg = {r["host_line_id"]: f"{r['piece']} {r['action_reason']}" for r in rows701 + rows702
                   if r["action"] == R.CHANGE and r["host_line_id"]}
    pend = dict(chg314, **plaster_chg)
    pend_name = {k: "T-314 r3 (QUEUED)" for k in chg314}
    pend_name.update({k: "the plaster package H1 (T-701 / T-702)" for k in plaster_chg})
    rows697 = p697(tgt, i68, pend, pend_name)
    rows691 = p691(tgt, i67)
    rows700 = p700(tgt, i69)
    rows695 = p695(tgt, i68, rows700)
    rows = rows697 + rows701 + rows702 + rows691 + rows700 + rows695
    expect = {"T-697": len(cload(T697)), "T-701": 2, "T-702": 2 + 2 + 16 + 11 + 3, "T-691": 3 + 4 + 18,
              "T-700": len(cload(T700)), "T-695": len(cload(T695))}
    pieces = {}
    for p, n in expect.items():
        sel = [r for r in rows if r["piece"] == p]
        for r in sel:
            r["row"] = f"{p}:{r['row']}"
        classes = R698.reconcile(sel, n, p)
        pieces[p] = {"rows": n, "classes": {k: v for k, v in classes.items() if v},
                     "actions": dict(sorted(Counter(r["action"] for r in sel).items())), "merge": MERGES[p]}
    R698.check_hosts_present(rows, tgt)
    R.check_no_zero(rows)
    R698.check_no_zero_for_held(rows)
    R.check_owner_named(rows)
    R.check_one_owner([r for r in rows if r["piece"] == "T-697"])
    stale = [r["row"] for r in rows if r["class"] == R698.STALE]
    if stale:
        raise R.ReadinessError(f"stale hosts {stale}")
    for r in rows:   # lesson 08:25: derived maps carry HELD
        if r["held"] and r["qty"] is not None:
            raise R.ReadinessError(f"{r['row']}: HELD row with a quantity")

    def size(sel):
        return R.package_size(sel)
    bead_rows = [r for r in rows697 if r["action"] == R.ADD]
    bead_int = [r for r in bead_rows if r["scope"] == "INTERIOR"]
    bead_ext = [r for r in bead_rows if r["scope"] == "EXTERIOR"]
    hub = [
        {"order": 1, "package": "T-704 concrete Gate B round 8 (READY, in Checker queue)", "changed_lines": None,
         "note": "not this task; hub files busy until its Gate B"},
        {"order": 2, "package": "T-703 masonry Gate B round 4 (QUEUED after T-704)", "changed_lines": None,
         "note": "not this task"},
        {"order": 3, "package": "H1 PLASTER: T-701 R-T701-2 (GF-01 / GF-04) + T-702 (c) wet-room bands GF-07 / GF-14",
         **size(rows701 + [r for r in rows702 if r["family"] == "B5-band"]),
         "restate_first": ["F-T709-1 (T-709 MERGED fe461c6e): GF-01 W12 deduction 4.290 -> 4.300824 m2, both ends of "
                           "the R-T701-2 bound 0.010824 m2 lower (47.949844 .. 66.249856), quoted, not applied here",
                           "F-V702-1 (Checker, T-702 verdict): GF-14 B11 oblique footprint 0.282868 hard-coded vs "
                           "0.20 x sqrt 2 = 0.282843 m (immaterial); restate the GF-14 band before wiring"]},
        {"order": 4, "package": "H2a B4-09 INTERIOR corner beads (new lm lines bound by host id), after H1",
         **size(bead_int),
         "depends_on": sorted({r["host_line_id"] for r in bead_int if r["class"] == R698.PENDING_CHANGE})},
        {"order": 5, "package": "T-314 r3 exterior plaster faces (QUEUED; m2 only, arris once)", "changed_lines": 18,
         "note": "3 CHANGE + 15 ADD from the pinned r2 stage; its MISSING 'FIN.EXT.CORNERS' lm item is B4-09's "
                 "(ruling 08:25) and is never wired by T-314"},
        {"order": 6, "package": "H2b B4-09 EXTERIOR corner beads, after T-314 r3", **size(bead_ext),
         "depends_on": sorted({r["host_line_id"] for r in bead_ext if r["class"] == R698.PENDING_CHANGE})},
        {"order": 7, "package": "H3 TILES: T-702 (b) GF-10 / GF-11 wall tile blank -> bounded",
         **size([r for r in rows702 if r["family"] == "B2"])},
        {"order": 8, "package": "H4 WATERPROOFING + ROOF BUILD-UP: T-691 roof membrane / upturn, pantry pieces, "
                                "penetrations + T-702 (a) falls-screed AT_LEAST lows",
         **size(rows691 + [r for r in rows702 if r["family"] == "B13"]),
         "gate_b_note": "T-702 (a) AT_LEAST lows (ROOF-430 3.324832, ROOF-970 4.791492, TERRACE-550 2.512672 m3) "
                        "were merged without a Checker re-measure (the T-702 verdict re-measured GF-14 only): Gate B "
                        "hand-checks them"},
        {"order": 9, "package": "H5 EARTHWORKS: T-700 wiring form (restates T-695; strap trench split)",
         **size(rows700)},
    ]
    for h in hub:
        if "changed" in h:
            h["changed_lines"] = h["changed"] + h["added"]
    keep = {p: sum(1 for r in rows if r["piece"] == p and r["action"] == R.KEEP) for p in expect}
    return {
        "schema": SCHEMA, "task": "T-705", "rule": [R.RULE_ID, R.RULE_VERSION], "base_rule": list(R.BASE_RULE),
        "candidate": CANDIDATE, "line_index_sha256": sha(IDX70), "inputs_sha256": {p: sha(p) for p in PINS},
        "t314_stage": {"blob": s314["blob"], "stage": s314["stage_short"], "arris_once": "PASS: 18 stage rows, "
                       "face m2 only; MISSING 'FIN.EXT.CORNERS (all floors)' 710.171878 .. 821.8588 lm is the same "
                       "arrises as B4-09 exterior (F-T697-3 CONFIRMED): never wired by T-314"},
        "pieces": pieces, "keep_rows": keep, "hub_order": hub, "bead_census_m": bead_census(rows697),
        "line_changes": changes(rows),
        "bead_host_classes": dict(sorted(Counter(r["host_class"] for r in rows697 if r["action"] == R.ADD).items())),
        "stale": 0, "rows": rows,
    }


CSV_COLS = ["piece", "family", "ledger", "row", "class", "host_line_id", "action", "after", "ledger_state", "qty", "lo",
            "hi", "held", "unit", "owner_family", "element", "new_line_key", "reason", "action_reason"]


def to_csv(d):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in d["rows"]:
        w.writerow([R.after_text(r[c]) if c == "after" else ("" if r.get(c) is None else r.get(c)) for c in CSV_COLS])
    return s.getvalue()


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv):
    d = build()
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(dumps(d), encoding="utf-8")
        OUT_CSV.write_text(to_csv(d), encoding="utf-8")
    elif "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == dumps(d) and OUT_CSV.read_text(encoding="utf-8") == to_csv(d)
        print("T-705 check:", "EQUAL" if ok else "DIFFERS")
        return 0 if ok else 1
    print(json.dumps({"pieces": d["pieces"], "hub": [(h["order"], h["package"][:60], h.get("changed_lines"))
                                                     for h in d["hub_order"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
