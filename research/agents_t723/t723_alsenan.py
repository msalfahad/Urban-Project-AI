"""T-723 WIRING READINESS ROUND 4 on ARCH_TAKEOFF_V3.0.71 (development villa; method R-T723-1 in t723_rules.py, on top
of R-T705-1 1.0.0 and R-T698-1 1.1.0, every villa). Research only: no candidate, released, rule / knowledge version or
registry file is touched; no quantity is produced, changed or wired; no drawing is opened.

(1) The T-705 map (R-T705-1, 274 rows on V3.0.70) restated on V3.0.71 line ids: every host re-classified (index entry
and beside record compared between the two candidates; hosts the READY T-703 package changes marked PENDING on it),
every action re-tested on the V3.0.71 line. (2) The pieces merged since T-705 that no candidate line reads yet, mapped
by line id with their after-states, HELD carried, owner trade named and the hub package that wires each: T-707 (column
tail), T-709 (plaster / paint residuals), T-710 (WP round 3), T-711 (concrete blank tail), T-712 (ground beams), T-713
(masonry rest), T-715 + T-718 (stair finishes), T-721 (beams blank). T-706 (slab statement) and T-716 (designer census)
carry no line target (stated, 0 rows). (3) Hub packages in the owner order with their changed / text-only / added
line counts.

Inputs: merged repository files only (sha256-pinned in PINS) + the pinned extract of the READY T-703 package
(in/T703_PENDING.json, built by t723_extract_t703.py from its commit). The beside register (one-sided figures already
carried beside V3.0.70 / V3.0.71 lines) is REBUILT here from the merged concrete Gate B input builders of rounds 1 .. 8
(research/agents_t661 .. t704 `*_inputs.build()`, each sha-pinned by its own builder).

Rebuild:  bash scripts/agent_env.sh run --tree task-T-723 research/agents_t723/t723_alsenan.py --write
Check:    bash scripts/agent_env.sh run --tree task-T-723 research/agents_t723/t723_alsenan.py --check
"""
from __future__ import annotations

import csv
import hashlib
import importlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t723_rules as R  # noqa: E402

R705, R698 = R.R705, R.R698
SCHEMA = "URBAN_T723_WIRING_READINESS_R4_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.71"
IDX71 = "research/agents_t704/out/LINE_INDEX_V3_0_71.json"
IDX70 = "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
T705 = "research/agents_t705/out/T705_READINESS.json"
T703 = "research/agents_t723/in/T703_PENDING.json"
T707 = "research/agents_t707/out/T707_COLUMN_TAIL.json"
T709 = "research/agents_t709/out/T709_RESIDUALS.json"
T710 = "research/agents_t710/out/T710_WP_ROUND3.json"
T711 = "research/agents_t711/out/T711_LEDGER.json"
T712 = "research/agents_t712/out/T712_LEDGER.json"
T713 = "research/agents_t713/out/T713_MASONRY_REST.json"
T715 = "research/agents_t715/out/T715_LEDGER.json"
T718 = "research/agents_t718/out/T718_LEDGER.json"
T721 = "research/agents_t721/out/T721_LEDGER.json"
T706 = "research/agents_t706/out/T706_STATEMENT.json"
T716 = "research/agents_t716/out/T716_CENSUS.json"
PINS = [IDX71, IDX70, T705, T703, T707, T709, T710, T711, T712, T713, T715, T718, T721, T706, T716]
# board MERGED cells (Verifier, Gate A PASS), in merge order (rule 4); the T-705 pieces merged before all of these
MERGES = {
    "T-697": "MERGED 6ed575ad (T-705 piece)", "T-695": "MERGED bbda7212 (T-705 piece)",
    "T-700": "MERGED 8210b549 (T-705 piece)", "T-701": "MERGED 65083ee7 (T-705 piece)",
    "T-702": "MERGED b90d85af (T-705 piece)", "T-691": "MERGED 5e4fdc33 (T-705 piece)",
    "T-706": "MERGED 11489726 (Verifier 2026-11-11T13:57Z, Gate A PASS)",
    "T-709": "MERGED fe461c6e (Verifier 2026-11-11T13:59Z, Gate A PASS)",
    "T-707": "MERGED f34a5baa (Verifier 2026-11-11T15:58Z, Gate A PASS)",
    "T-710": "MERGED 4a34ced0 (Verifier 2026-11-11T16:00Z, Gate A PASS)",
    "T-711": "MERGED 1e06f656 (Verifier 2026-11-11T17:58Z, Gate A PASS)",
    "T-713": "MERGED aa4d8979 (Verifier 2026-11-11T17:58Z, Gate A PASS)",
    "T-715": "MERGED a4e4277a (Verifier 2026-11-11T20:02Z, Gate A PASS)",
    "T-712": "MERGED dfeb0240 (Verifier 2026-11-11T20:55Z, Gate A PASS)",
    "T-716": "MERGED 17aaab4b (Verifier 2026-11-11T21:47Z, Gate A PASS)",
    "T-721": "MERGED 9e1ed6c5 (Verifier 2026-11-11T22:05Z, Gate A PASS)",
    "T-718": "MERGED 8052ca51 (Verifier 2026-11-11T22:12Z, Gate A PASS)",
}
ORDER = list(MERGES)
GATE_B_ROUNDS = [("661", "V3.0.62"), ("665", "V3.0.63"), ("668", "V3.0.64"), ("671", "V3.0.65"), ("677", "V3.0.66"),
                 ("682", "V3.0.67"), ("693", "V3.0.70"), ("704", "V3.0.71")]
CLEARS = {"BOUND", "VALUE", "REVALUE", "NARROW", "NOT_APPLICABLE", "OWNER"}
SIDE = {"LOWER_ONLY": "AT_LEAST", "UPPER_ONLY": "AT_MOST", "AT_MOST": "AT_MOST"}
CONC = {"STR.CONC.COLUMN", "STR.CONC.NECK", "STR.CONC.LIFT", "STR.CONC.PARAPET", "STR.CONC.STAIR",
        "STR.CONC.GROUND_BEAM", "STR.CONC.BEAM"}
STAIR = {"FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.STAIR.FLIGHT", "FIN.MARBLE.RISER",
         "FIN.MARBLE.TREAD", "FIN.STAIR.STEP_LM", "FIN.MARBLE.LANDING", "FIN.STAIR.SOFFIT"}
MAS = {"MAS.BLOCK", "MAS.UNITS.BLACK", "MAS.UNITS.WHITE", "MAS.MORTAR.BLACK", "MAS.MORTAR.BLACK.PERIMETER",
       "MAS.MORTAR.BLACK.LINTEL_BEARING", "MAS.GLUE.AAC"}
WP_PREFIXES = ("FIN.WP.", "WP.")                 # roof / wet-room (FIN.WP.*) and foundation (WP.FOUNDATION.*)
PRIOR_BESIDE = {"STR.CONC.PARAPET": "ARCH_TAKEOFF_V3.0.23 (PARAPET_RC, AT_LEAST beside)",
                "STR.CONC.LIFT": "ARCH_TAKEOFF_V3.0.46 (lift tie beam / below-ground, AT_LEAST plane beside)"}
# register rulings (ELEMENT_REGISTER.md, Lead 2026-11-11): owner trade per family
OWNER = {
    "B10": "concrete STR.CONC.* (S; R-CONC-OWN-1; stairs: concrete body only, ruling 16:25)",
    "B10-13": "formwork STR.FORMWORK (S; follows its member's bound, T-714)",
    "B9": "masonry MAS.* (A; parapet / lift block vs concrete, ruling 16:25)",
    "B5": "plaster FIN.PLASTER m2 (Q-72 heights; void bands R-T709-1 + ruling 20:25 VOIDS B2-05)",
    "B5-paint": "paint FIN.PAINT m2 (Q-72: to the finished ceiling; returns R-T709-4)",
    "B7-04": "stair finish faces FIN.STAIR.* / FIN.MARBLE.* (A; ruling 16:25; MS2-L ruling 20:25)",
    "B8": "waterproofing FIN.WP.*",
}
HUB = {"T-722": "T-722 CONCRETE GATE B ROUND 9 (QUEUED, reserves V3.0.73)",
       "T-714": "T-714 FORMWORK restated (TODO, lane S)",
       "T-717": "T-717 PLASTER / PAINT GATE B, hub H1 (QUEUED after T-722, reserves V3.0.74)",
       "T-703": "T-703 MASONRY GATE B ROUND 4 (READY, V3.0.72, Gate B pending)",
       "H3S": "H3s STAIR FINISHES (no row yet)", "H4": "H4 WATERPROOFING + ROOF BUILD-UP (no row yet)"}
OUT_JSON = HERE / "out" / "T723_READINESS.json"
OUT_CSV = HERE / "out" / "T723_ROWS.csv"


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def index(rel):
    return {ln["line_id"]: ln for ln in jload(rel)["lines"]}


def num(s):
    return None if s in (None, "", "None", "null") else float(s)


# ============================================================================== beside register (rebuilt, rule 1/6)
IDX_CACHE = {}


def beside_registers():
    """-> ({line: beside} on V3.0.70, {line: beside} on V3.0.71, provenance). Replays the merged concrete Gate B input
    builders in round order: LOWER_ONLY / UPPER_ONLY / AT_MOST set the figure beside; a later BOUND / VALUE / ... on the
    same line clears it (the line now carries a range or a value); CONFIRM / DATUM_NAMED / HELD_BLANK leave it."""
    reg, snap, prov = {}, {}, []
    for t, ver in GATE_B_ROUNDS:
        d = ROOT / "research" / f"agents_t{t}"
        for p in (d, ROOT / "research" / "agents_t699"):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        doc = importlib.import_module(f"t{t}_inputs").build()
        n = 0
        for e in doc["entries"]:
            a, lid = e.get("action"), e.get("line_id")
            if lid is None:      # an ADDed line: resolved by its element id on the V3.0.71 index (unique)
                ad = e["add"]
                hits = [k for k, ln in IDX_CACHE.items() if ln["element_id"] == ad["element_id"]
                        and ln["item_code"] == ad["item_code"]]
                if len(hits) != 1:
                    raise R.ReadinessError(f"T-{t} {a} {e['key']}: {len(hits)} lines carry its element id")
                lid = hits[0]
                if a == "ADD_LOWER_ONLY":
                    a = "LOWER_ONLY"
            if a in SIDE:
                v = e["at_most_m3"] if a == "AT_MOST" else e["beside"]["value"]
                reg[lid] = {"side": SIDE[a], "value": R.r6(v), "unit": "m3", "carried_by": ver}
                n += 1
            elif a in CLEARS:
                reg.pop(lid, None)
        prov.append({"round": f"T-{t}", "version": ver, "one_sided_set": n})
        if ver == "V3.0.70":
            snap = dict(reg)
    return snap, dict(reg), prov


# ======================================================================================== row builder
def mk(piece, family, ledger, key, cls, host, reason, *, element, after=None, action=R.NONE, action_reason="",
       new_line_key=None, unit="", hub=None, flags=(), ledger_state="", qty=None, lo=None, hi=None, **kw):
    held = ledger_state == "HELD" or (after is not None and after["kind"] in (R705.BOUND, R705.BLANK, R.ONE_SIDED))
    return dict({"piece": piece, "family": family, "owner_family": family, "owner": OWNER.get(family, family),
                 "ledger": ledger, "row": f"{piece}:{key}", "class": cls, "host_line_id": host, "reason": reason,
                 "element": element, "after": after, "action": action, "action_reason": action_reason,
                 "new_line_key": new_line_key, "unit": unit, "hub": hub, "flags": list(flags),
                 "ledger_state": ledger_state or ("HELD" if held else ""), "qty": R.r6(qty), "lo": R.r6(lo),
                 "hi": R.r6(hi), "held": bool(held)}, **kw)


def on_line(piece, family, ledger, key, lid, a, codes, ctx, *, hub, unit=None, flags=(), **kw):
    tgt, bes, pend = ctx["tgt"], ctx["beside"], ctx["pending"]
    cls, host, reason = R698.classify(lid, allowed_codes=codes, target=tgt, reference=ctx["ref"],
                                      pending_changed=pend, pending_name="the READY package T-703 (V3.0.72)")
    if cls in (R698.STALE, R698.WRONG, R698.AMBIGUOUS, R698.NO_HOST) or host is None:
        ac, ar = R.NONE, f"class {cls}: not wireable as stated"
    else:
        ac, ar = R.wire_action(a, tgt[host], bes.get(host))
    ln = tgt.get(lid) or {}
    return mk(piece, family, ledger, key, cls, host, reason, element=ln.get("element_id", key), after=a, action=ac,
              action_reason=ar, unit=unit or ln.get("unit", ""), hub=hub, flags=flags,
              qty=a["value"] if a and a["kind"] == R705.VALUE else None,
              lo=a["low"] if a and a["kind"] == R705.BOUND else None,
              hi=a["high"] if a and a["kind"] == R705.BOUND else None, **kw)


def conc_after(x):
    if x["bound"] == "AT_LEAST":
        return R.after(R.ONE_SIDED, side="AT_LEAST", value=num(x["at_least_m3"]), note=x.get("item", "")[:100])
    if x["bound"] == "AT_MOST":
        return R.after(R.ONE_SIDED, side="AT_MOST", value=num(x["at_most_m3"]), note=x.get("item", "")[:100])
    if x["bound"] == "BLANK_NAMED":
        return R.after(R705.BLANK, note=("named: " + (x.get("item") or ""))[:120])
    raise R.ReadinessError(f"unknown concrete bound {x['bound']}")


# ============================================================================================ concrete (hub T-722)
def p707(ctx):
    d = jload(T707)
    out = []
    for x in d["lines"]:
        lo, hi = num(x["after"][0]), num(x["after"][1])
        if x["kind"] == "PLATE":
            a = R.after(R705.BOUND, lo=lo, hi=hi, note=f"{x['item']}: low +{x['delta_low_m3']} (plate transfer)")
        else:
            if hi is not None:
                raise R.ReadinessError(f"{x['line_id']}: TANK row with a high end")
            a = R.after(R.ONE_SIDED, side="AT_LEAST", value=lo, note=f"LOWER_ONLY: {x['item'][:90]}")
        out.append(on_line("T-707", "B10", "T-707 column tail", x["line_id"], x["line_id"], a, CONC, ctx, hub="T-722",
                           member=x["member"]))
    for x in d["formwork"]:
        a = R.after(R705.BOUND, lo=num(x["low_m2"]), hi=num(x["high_m2"]),
                    note=f"{x['state']} ({x['member']}): perimeter x h bounds of T-707")
        out.append(on_line("T-707", "B10-13", "T-707 formwork beside its column", x["fw_line"], x["fw_line"], a,
                           {"STR.FORMWORK"}, ctx, hub="T-714", column_line=x["column_line"],
                           flags=("FOLLOWS_MEMBER: wired with T-714 after its column line moves in T-722",)))
    return out


def p_conc(path, piece, key, ctx):
    d = jload(path)
    out = []
    for x in d[key]:
        a = conc_after(x)
        flags = []
        if x.get("guard"):
            flags.append(f"GUARD: {x['guard']}")
        code = ctx["tgt"].get(x["line_id"], {}).get("item_code")
        if code in PRIOR_BESIDE:
            flags.append(f"CONFIRM_ON_LIVE: {PRIOR_BESIDE[code]} may already carry a figure beside this code, outside "
                         "the rebuilt concrete register: the package reads the live record before BESIDE vs RESTATE")
        out.append(on_line(piece, "B10", f"{piece} ledger", x["line_id"], x["line_id"], a, CONC, ctx, hub="T-722",
                           flags=flags, member=x.get("member", "")))
    return out


# ==================================================================================== T-709 plaster / paint (T-717)
BAND_HOSTS = {"plaster": ("L-8cecb1d010d5aafbf25d", "FIN.PLASTER", "B5"),
              "paint": ("L-c0ac22c964a42e7d71b1", "FIN.PAINT", "B5-paint")}


def p709(ctx):
    d = jload(T709)
    tgt = ctx["tgt"]
    out = []
    a_dh = d["a_double_height"]
    for kind, (host, code, fam) in BAND_HOSTS.items():
        b = a_dh[f"{kind}_band"]
        lo, hi = (num(v) for v in b["m2"])
        a = R.after(R705.BOUND, lo=lo, hi=hi, note=f"R-T709-1 band +{b['levels'][0]} .. +{b['levels'][1]}: {b['status'][:60]}")
        cls, h, reason = R698.classify(host, allowed_codes={code}, target=tgt, reference=ctx["ref"])
        if tgt[host]["element_id"] != f"HL:WALL_FINISH:GF_08:{kind.upper()}":
            raise R.ReadinessError(f"band host {host} is not the GF-08 {kind} line")
        out.append(mk("T-709", fam, "T-709 (a) double-height band", f"band:{kind}", cls, h, reason,
                      element=f"GF-08 face 336 +{b['levels'][0]} .. +{b['levels'][1]} (stairwell, no slab between)",
                      after=a, action=R.ADD, action_reason="new HELD band line bound to the GF-08 face line (host "
                      "decided by lane I: the band continues the GF wall face 336 over its solid 3.997 m; 1F-13 starts "
                      "at its own floor +5.50)", new_line_key=f"{kind.upper()}-BAND@{host}", unit="m2", hub="T-717",
                      lo=lo, hi=hi,
                      flags=("PREREQUISITE: T-719 VOIDS B2-05 names the stairwell void (ruling 20:25)",
                             "PREREQUISITE: the T-147 region of GF-08 carries face 336 (T-709 named uncertainty)")))
    for f in a_dh["held_beam_faces"]:
        out.append(mk("T-709", "B5", "T-709 (a) beam faces", f"beam:{f['face'][:40]}", R698.NO_HOST, None,
                      f"HELD by name: {f['datum'][:90]}", element=f["face"], after=R.after(R705.BLANK, note=f["datum"][:90]),
                      action=R.NONE, action_reason="named HELD item, no line (datum not read)", unit="m2",
                      ledger_state="HELD"))
    for x in d["c_return_paint"]["rows"]:
        pr = x["paint_row"]
        host = x["plaster_line"]
        if pr["bound_beside_m2"]:
            lo, hi = (num(v) for v in pr["bound_beside_m2"])
            a = R.after(R705.BOUND, lo=lo, hi=hi, note=f"R-T709-4: {pr['flag']}")
        else:
            a = R.after(R705.BLANK, note=f"R-T709-4: {pr['flag']}")
        cls, h, reason = R698.classify(host, allowed_codes={"FIN.PLASTER"}, target=tgt, reference=ctx["ref"])
        flags = ["NOT_ESTABLISHED: one finish per face (R-T701-3); Gate B states which face is painted"] \
            if pr["flag"].startswith("NOT_ESTABLISHED") else []
        out.append(mk("T-709", "B5-paint", "T-709 (c) return paint", x["face_id"], cls, h, reason,
                      element=pr["element_id"], after=a, action=R.ADD,
                      action_reason=f"new HELD FIN.PAINT return line keyed by the plaster face {host}",
                      new_line_key=pr["element_id"], unit="m2", hub="T-717", flags=flags,
                      lo=a["low"], hi=a["high"]))
    return out


# =============================================================================================== T-710 WP (H4)
MISSING_710 = {"FIN.WP.TERMINATION": "MISSING FIN.WP.TERMINATION GF-07 open side",
               "FIN.WP.DOORWAY": "MISSING FIN.WP.DOORWAY D-GF-07",
               "FIN.WP.DOORWAY_TRANSITION_NR": "MISSING FIN.WP.DOORWAY_TRANSITION_NR D-GF-07",
               "FIN.WP.PENETRATION": "MISSING FIN.WP.PENETRATION GF-07"}


def _wp_after(r):
    a = r["after"]
    if a is None:
        return R.after(R705.NOPROP, note=f"{r['cause']}: state only")
    if isinstance(a, str):
        txt = a.split("(")[0].replace("pcs", "").strip()
        if ".." in txt:
            lo, hi = (float(v) for v in txt.split(".."))
            return R.after(R705.VALUE, value=lo, note=a) if lo == hi else R.after(R705.BOUND, lo=lo, hi=hi, note=a)
        return R.after(R705.VALUE, value=float(txt), note=a)
    if a.get("status") == "MEASURED":
        return R.after(R705.VALUE, value=num(a["value"]), note=a.get("source", "")[:100])
    if a.get("status") == "OPEN_BOUND":
        return R.after(R705.BOUND, lo=num(a["low"]), hi=num(a["high"]), note="OPEN_BOUND (W09 / W10 sills, D-45)")
    raise R.ReadinessError(f"{r['key']}: unknown WP after {a}")


def p710(ctx, prior):
    d = jload(T710)
    tgt = ctx["tgt"]
    added = {r["new_line_key"]: r for r in prior if r["piece"] == "T-691" and r["action"] == R.ADD}
    out = []
    for r in d["census"]["rows"]:
        a = _wp_after(r)
        flags = [] if r["cause"] != "NO_PHYSICAL_ELEMENT" else \
            ["NO_PHYSICAL_ELEMENT: T-710 states no element under this held line; the package states its removal "
             "cause, never 0 (Gate B)"]
        if r["key"].startswith("L-"):
            out.append(on_line("T-710", "B8", f"T-710 census ({r['cause']})", r["key"], r["key"], a, ctx["wp"], ctx,
                               hub="H4", unit=r["unit"], flags=flags))
            continue
        if r["after"] is None:       # a MISSING element held by the designer: a HELD blank line, never dropped
            out.append(mk("T-710", "B8", "T-710 census (MISSING, HELD)", r["key"], R698.NO_HOST, None,
                          f"MISSING and HELD ({r['cause']}): no candidate line, none added by T-691",
                          element=r["element"], after=R.after(R705.BLANK, note=r["drawing"][:100]), action=R.ADD,
                          action_reason="new HELD blank line (missing is never dropped)", new_line_key=r["key"],
                          unit=r["unit"], hub="H4", ledger_state="HELD",
                          flags=("NEW_HELD_LINE: T-691 left it out; the package adds it HELD blank or states why not",)))
            continue
        k = MISSING_710[r["code"]]
        if k not in added:
            raise R.ReadinessError(f"T-710 MISSING {r['code']}: no T-691 ADD of the same item and room")
        out.append(mk("T-710", "B8", "T-710 census (MISSING)", r["key"], R698.NO_HOST, None,
                      f"MISSING line = the T-691 ADD '{k}' (same item code, same pantry room GF-07)",
                      element=r["element"], after=a, action=R.ADD, action_reason="new line (restated)",
                      new_line_key=k, unit=r["unit"], hub="H4", qty=a["value"]))
    if len([r for r in out if r["piece"] == "T-710"]) != len(d["census"]["rows"]):
        raise R.ReadinessError("T-710 rows lost")
    return out


# ===================================================================================== T-713 masonry (T-703)
def p713(ctx):
    d = jload(T713)
    out = []
    for x in d["census"]:
        a = R.after(R705.NOPROP, note=f"{x['state']}: {x['cause'][:80]}")
        r = on_line("T-713", "B9", "T-713 census", x["line_id"], x["line_id"], a, MAS, ctx, hub="T-703")
        if r["class"] == R698.PENDING_CHANGE:
            r["action"], r["action_reason"] = R.NONE, "wired by the READY package T-703 (V3.0.72): Gate B pending"
        out.append(r)
    return out


# ============================================================================= T-715 + T-718 stair finishes (H3s)
def stair_after(x):
    a = x["after"]
    c = a["class"]
    note = (a.get("item") or a.get("cause") or "")[:100]
    if c == "MEASURED":
        return R.after(R705.VALUE, value=num(a["value"]), note=a["status"][:100])
    if c == "RANGE":
        return R.after(R705.BOUND, lo=num(a["low"]), hi=num(a["high"]), note=note)
    if c == "AT_LEAST":
        return R.after(R.ONE_SIDED, side="AT_LEAST", value=num(a["low"]), note=note)
    if c == "AT_MOST":
        return R.after(R.ONE_SIDED, side="AT_MOST", value=num(a["high"]), note=note)
    if c == "CONDITIONAL_ON_FORM":
        return R.after(R.ONE_SIDED, side="CONDITIONAL", value=num(a["value"]), note=note or "ORR-007 payable form")
    if c == "NOT_APPLICABLE":
        return R.after(R.EXCLUDED, note=(a.get("cause") or "")[:100])
    if c == "BLANK_NAMED":
        return R.after(R705.BLANK, note=note)
    if c == "WIRING_GAP":
        return R.after(R705.NOPROP, note=(a.get("cause") or "")[:100])
    raise R.ReadinessError(f"{x['line_id']}: stair class {c}")


def p_stairs(ctx):
    out = []
    for path, piece in ((T715, "T-715"), (T718, "T-718")):
        d = jload(path)
        for x in d["lines"]:
            flags = ["WIRING_GAP: closes when the T-493 B7-04 landing lines are wired"] \
                if x["after"]["class"] == "WIRING_GAP" else []
            out.append(on_line(piece, "B7-04", f"{piece} ledger", x["line_id"], x["line_id"], stair_after(x), STAIR,
                               ctx, hub="H3S", flags=flags, element_note=x.get("element_id")))
    for n in jload(T715)["new_lines_proposed"]:
        v = num(n["value_m2"])
        out.append(mk("T-715", "B7-04", "T-715 new line", n["proposed"][:60], R698.NO_HOST, None,
                      "MISSING line (no candidate line): the package adds it", element=n["proposed"],
                      after=R.after(R705.VALUE, value=v, note=n["status"]), action=R.ADD, action_reason="new line",
                      new_line_key=n["proposed"], unit="m2", hub="H3S", qty=v))
    return out


# ================================================================================== T-705 rows restated (rule 6)
def restate705(ctx, i70, b70):
    t = jload(T705)
    if t["candidate"] != "ARCH_TAKEOFF_V3.0.70" or t["line_index_sha256"] != sha(IDX70):
        raise R.ReadinessError("T-705 map is not the V3.0.70 map of record")
    tgt, b71 = ctx["tgt"], ctx["beside"]
    pend705 = {}       # host -> (the pending package's name, the pieces it is made of): still unwired on V3.0.71
    for r in t["rows"]:
        if r["class"] == R698.PENDING_CHANGE:
            name = r["reason"].split(" changes the host")[0]
            pend705[r["host_line_id"]] = (name, {p for p in ("T-701", "T-702", "T-314") if p in name})
    out = []
    for r in t["rows"]:
        r = json.loads(json.dumps(r))
        r["t705_class"], r["t705_action"] = r["class"], r["action"]
        r.setdefault("flags", [])
        r["hub"] = None
        host = r.get("host_line_id")
        if host:
            pend = {h: n for h, (n, ps) in pend705.items() if r["piece"] not in ps}   # never pending on itself
            pend.update(ctx["pending"])
            cls, why = R.restate_class(host, i70, tgt, b70, b71, pend)
            if cls == R698.MAPPED and r["t705_class"] == R698.HOST_CHANGED:   # since the LEDGER, not since T-705
                cls, why = R698.HOST_CHANGED, f"{why}; host moved since its ledger (T-705: {r['reason'][:120]})"
            if cls == R698.STALE:
                raise R.ReadinessError(f"{r['row']}: {why}")
            if r["class"] in (R698.WRONG, R698.AMBIGUOUS):
                cls = r["class"]
            r["class"], r["reason"] = cls, f"V3.0.71: {why}"
            if r["action"] not in (R.ADD, R.NONE) and r.get("after"):
                r["action"], r["action_reason"] = R.wire_action(r["after"], tgt[host], b71.get(host))
        if r["piece"] == "T-697" and r["action"] == R.ADD:
            r["flags"].append("RULING_RESTATE: Lead 2026-11-11 16:25 CORNER BEAD HEIGHT STATE: on a HELD host the "
                              "bead is HELD with its host's bound (T-697 measured G1 lm cannot be wired as stated)")
        if r["piece"] == "T-701" and str(r["row"]).endswith("GF-01"):
            r["flags"].append("RESTATE_FIRST F-T709-1: W12 deduction 4.290 -> 4.300824 m2 (T-709 MERGED fe461c6e), "
                              "both ends -0.010824 m2 (47.949844 .. 66.249856), quoted, not applied")
        r["hub"] = {"T-701": "T-717", "T-702": None, "T-691": "H4", "T-700": "H5", "T-695": "H5"}.get(r["piece"])
        if r["piece"] == "T-702":
            r["hub"] = {"B5-band": "T-717", "B2": "H3", "B13": "H4"}.get(r["family"])
        if r["piece"] == "T-697":
            r["hub"] = "H2a" if r.get("scope") == "INTERIOR" else "H2b"
        r["piece_round"] = "T-705"
        out.append(r)
    return out, t


def conc_census(tgt, beside, live_rows):
    """STR.CONC census per touched code on V3.0.71 and as T-722 would leave it (projection of the map, not a run):
    released / bounded / blank lines, the bounded low / high sums, and the beside figures per side (counted and summed
    as a run-record figure only, never into released or a range). Read from the line INDEX (class / value / held range); an EXCLUDED line is
    counted apart (the code totals skip it)."""
    after = {r["host_line_id"]: r for r in live_rows if r["host_line_id"]}
    codes = sorted({tgt[h]["item_code"] for h in after})
    out = {}
    for code in codes:
        ids = [k for k, ln in tgt.items() if ln["item_code"] == code]
        st = {}
        for when in ("v3_0_71", "after_t722"):
            c = Counter()
            lo = hi = rel = 0.0
            side = Counter()
            side_sum = Counter()
            for k in ids:
                ln = dict(tgt[k])
                b = beside.get(k)
                r = after.get(k) if when == "after_t722" else None
                if r is not None:
                    a = r["after"]
                    if a["kind"] == R705.BOUND:
                        ln["held_low"], ln["held_high"] = a["low"], a["high"]
                    if a["kind"] == R.ONE_SIDED:
                        b = {"side": a["side"], "value": a["value"]}
                v, l_, h_ = ln["measured_net"], ln["held_low"], ln["held_high"]
                if ln["class"] == "EXCLUDED" and v is None and l_ is None and h_ is None and r is None:
                    c["excluded"] += 1                  # no element of the family (evidence named): never blank
                elif v is not None:
                    c["released"] += 1
                    rel += v
                elif l_ is not None and h_ is not None:
                    c["bounded"] += 1
                    lo, hi = lo + l_, hi + h_
                else:
                    c["blank"] += 1
                    if b:
                        side[b["side"]] += 1
                        side_sum[b["side"]] += b["value"]
            st[when] = {"lines": len(ids),
                        **{k: c.get(k, 0) for k in ("released", "bounded", "blank", "excluded")},
                        "released_m3": round(rel, 6), "bounded_low_m3": round(lo, 6), "bounded_high_m3": round(hi, 6),
                        "blank_with_beside": dict(sorted(side.items())),
                        "beside_sum_m3_run_record_only": {k: round(v, 6) for k, v in sorted(side_sum.items())}}
        out[code] = st
    return out


# =================================================================================================== build
def build():
    tgt, i70 = index(IDX71), index(IDX70)
    if any(R698.state_key(i70.get(k)) != R698.state_key(v) for k, v in tgt.items()) or set(i70) != set(tgt):
        raise R.ReadinessError("V3.0.71 index lines differ from V3.0.70: restate the census note")
    IDX_CACHE.clear()
    IDX_CACHE.update(tgt)
    b70, b71, prov = beside_registers()
    for lid, b in b71.items():
        ln = tgt.get(lid)
        if ln is None or ln["measured_net"] is not None or (ln["held_low"] is not None and ln["held_high"] is not None):
            raise R.ReadinessError(f"beside register {lid}: not a HELD line without value / range on V3.0.71")
    p703 = jload(T703)
    pending = {k: f"T-703 {'ONE_SIDED' if k in p703['one_sided'] else 'BOUND_ROUNDING'} (V3.0.72, READY)"
               for k in p703["one_sided"] + p703["bound_rounding"]}
    ctx = {"tgt": tgt, "ref": i70, "beside": b71, "pending": pending,
           "wp": {ln["item_code"] for ln in tgt.values() if ln["item_code"].startswith(WP_PREFIXES)}}
    rows705, t705 = restate705(ctx, i70, b70)
    new = (p707(ctx) + p_conc(T711, "T-711", "lines", ctx) + p_conc(T712, "T-712", "lines", ctx)
           + p_conc(T721, "T-721", "rows", ctx) + p709(ctx) + p710(ctx, rows705) + p713(ctx) + p_stairs(ctx))
    rows = rows705 + new
    supersede = {("T-718", "T-715"): {x["line_id"] for x in jload(T718)["lines"]}}
    if "79 of 85" not in jload(T718)["unchanged"]:
        raise R.ReadinessError("T-718 no longer declares the 6 lines it restates")
    R.resolve_live([r for r in rows if r["piece"] not in ("T-697",)], ORDER, supersede)
    for r in rows:
        r.setdefault("live", None)
    R.check_one_line_per_row(rows)
    R.check_after(new)
    R698.check_hosts_present(rows, tgt)
    R698.check_no_zero_for_held(rows)
    R705.check_owner_named(rows)
    for r in rows:
        if r["class"] == R698.STALE:
            raise R.ReadinessError(f"stale host {r['row']}")
        if r["held"] and r["qty"] is not None and r["piece_round" if "piece_round" in r else "piece"] != "T-705":
            raise R.ReadinessError(f"{r['row']}: HELD row with a quantity")
    expect = {"T-707": 7 + 13, "T-711": 15, "T-712": 20, "T-721": 12, "T-709": 2 + 2 + 30, "T-710": 58, "T-713": 95,
              "T-715": 85 + 1, "T-718": 6}
    pieces = {}
    for p, n in expect.items():
        sel = [r for r in new if r["piece"] == p]
        classes = R698.reconcile(sel, n, p)
        pieces[p] = {"rows": n, "merge": MERGES[p], "classes": {k: v for k, v in classes.items() if v},
                     "actions": dict(sorted(Counter(r["action"] for r in sel).items())),
                     "live": dict(sorted(Counter(str(r["live"]) for r in sel).items()))}
    restated = {"rows": len(rows705), "t705_rows": len(t705["rows"]),
                "classes_before": dict(sorted(Counter(r["t705_class"] for r in rows705).items())),
                "classes_after": dict(sorted(Counter(r["class"] for r in rows705).items())),
                "actions_before": dict(sorted(Counter(r["t705_action"] for r in rows705).items())),
                "actions_after": dict(sorted(Counter(r["action"] for r in rows705).items())),
                "host_changed": sorted({r["host_line_id"] for r in rows705 if r["class"] == R698.HOST_CHANGED
                                        and r["t705_class"] != R698.HOST_CHANGED}),
                "ruling_restate_rows": sum(1 for r in rows705 if any(f.startswith("RULING_RESTATE") for f in r["flags"]))}
    if restated["rows"] != restated["t705_rows"]:
        raise R.ReadinessError("T-705 rows lost in the restatement")

    def hub_rows(h):
        return [r for r in rows if r.get("hub") == h]
    hubs = []
    for order, h, name, note in [
        (1, "T-703", HUB["T-703"], "carries the T-713 parent / B9 figures (18 ONE_SIDED + 10 rounding); no row here moves"),
        (2, "T-722", HUB["T-722"], "T-707 columns + T-711 + T-712 + T-721; T-721 (MERGED 22:05) is not in the row's list: "
                                   "the Lead adds it or opens a round 10"),
        (3, "T-714", HUB["T-714"], "the 13 T-707 formwork rows follow their column lines (after T-722)"),
        (4, "T-717", HUB["T-717"], "T-705 H1 (4) + T-709 bands (2 ADD) + 30 return-paint ADD; F-T709-1 restated first"),
        (5, "H2a", "H2a B4-09 INTERIOR beads", "BLOCKED: RULING_RESTATE (Lead 16:25): the bead ledger must be restated"),
        (6, "H2b", "H2b B4-09 EXTERIOR beads", "BLOCKED: RULING_RESTATE + T-314 r3"),
        (7, "H3", "H3 TILES (T-702 GF-10 / GF-11)", ""),
        (8, "H3S", HUB["H3S"], "T-715 with T-718 governing its 6 lines; 26 skirting form pairs CONDITIONAL (ORR-007)"),
        (9, "H4", HUB["H4"], "T-705 H4 rows + T-710 (restates T-691: duplicates counted once)"),
        (10, "H5", "H5 EARTHWORKS (T-700 form)", "unchanged from T-705; T-708 round 3 TODO"),
    ]:
        sel = hub_rows(h)
        s = R.package_size(sel)
        hubs.append({"order": order, "hub": h, "package": name, "note": note, "rows": len(sel),
                     "changed": s["changed"], "text_only": s["text_only"], "added": s["added"],
                     "changed_ids": s["changed_ids"], "text_ids": s["text_ids"], "added_keys": s["added_keys"],
                     "form_conflicts": sorted({r["host_line_id"] for r in sel if r["action"] == R.FORM_CONFLICT}),
                     "pending": sorted({r["host_line_id"] for r in sel if r["class"] == R698.PENDING_CHANGE}),
                     "blocked_rows": sum(1 for r in sel if any(f.startswith(("RULING_RESTATE", "PREREQUISITE"))
                                                               for f in r["flags"]))})
    return {
        "conc_census_t722": conc_census(tgt, b71, [r for r in rows if r.get("hub") == "T-722" and r.get("live") == R.LIVE]),
        "schema": SCHEMA, "task": "T-723", "rule": [R.RULE_ID, R.RULE_VERSION], "base_rules": [list(b) for b in R.BASE_RULES],
        "candidate": CANDIDATE, "line_index_sha256": sha(IDX71), "inputs_sha256": {p: sha(p) for p in PINS},
        "index_note": "V3.0.71 index lines equal V3.0.70 (T-704 moved beside records only); asserted",
        "beside_register": {"rounds": prov, "v3_0_70": len(b70), "v3_0_71": len(b71),
                            "changed_70_71": sorted(k for k in set(b70) | set(b71) if b70.get(k) != b71.get(k)),
                            "scope": "concrete Gate B rounds 1 .. 8 rebuilt; non-concrete beside records (V3.0.23 "
                                     "parapet, V3.0.46 lift, V3.0.58 WP, V3.0.68 masonry) are confirmed by each "
                                     "package on its live run"},
        "t703_pending": {"commit": p703["commit"], "lines": len(pending)},
        "restated_t705": restated, "pieces": pieces,
        "no_line_target": {"T-706": "slab statement: engine quantity settled by the drawing, no line change (R-T706-*)",
                           "T-716": "designer-list census of HELD lines: assignment only, no quantity"},
        "hub_order": hubs, "stale": 0, "rows": rows,
    }


CSV_COLS = ["piece", "family", "ledger", "row", "class", "host_line_id", "action", "live", "after", "unit", "hub",
            "owner_family", "element", "new_line_key", "flags", "reason", "action_reason"]


def to_csv(d):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in d["rows"]:
        out = []
        for c in CSV_COLS:
            v = r.get(c)
            out.append(R.after_text(v) if c == "after" else " | ".join(v) if c == "flags" else "" if v is None else v)
        w.writerow(out)
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
        print("T-723 check:", "EQUAL" if ok else "DIFFERS")
        return 0 if ok else 1
    print(json.dumps({"pieces": d["pieces"], "restated": {k: v for k, v in d["restated_t705"].items()
                                                         if k != "host_changed"},
                      "beside": {k: v for k, v in d["beside_register"].items() if k != "changed_70_71"},
                      "hub": [(h["order"], h["hub"], h["rows"], h["changed"], h["text_only"], h["added"],
                               len(h["form_conflicts"]), len(h["pending"]), h["blocked_rows"]) for h in d["hub_order"]]},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
