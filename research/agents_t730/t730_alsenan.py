"""T-730 WIRING READINESS ROUND 5 on ARCH_TAKEOFF_V3.0.73 (development villa; method R-T730-1 in t730_rules.py, on top of
R-T723-1 1.0.0, R-T705-1 1.0.0 and R-T698-1 1.1.0, every villa). Research only: no candidate, released, rule / knowledge
version or registry file is touched; no quantity is produced, changed or wired; no drawing is opened.

(1) The T-723 map (633 rows on V3.0.71) restated on V3.0.73 line ids: every host re-classified (index entry and beside
record compared between V3.0.71 and V3.0.73; hosts the READY T-717 package changes marked PENDING on it), every action
re-tested; rows the merged packages T-703 (V3.0.72) and T-722 (V3.0.73) wired are WIRED (R-T730-1 rule 1). (2) The
pieces merged since T-723 that no candidate line reads yet, mapped by line id: T-714 (formwork bounds, 370), T-724
(Checker findings: 4 soffit lines, the L-fb7a6431 cap, 4 strip children), T-725 (stair formwork, 20), T-726 (shaft
residual: statements), T-727 (V-01: one EXCLUDED duplicate face, statements), T-728 (bead restatement, 116 arrises,
superseding T-697), T-731 (MS1-L coherent reading, 4). T-719 (void register) and T-720 (gross area B2-03) carry no line
target (stated). (3) Hub packages in the owner order with changed / text-only / added counts and their blockers.

Inputs: merged repository files only (sha256-pinned in PINS) + the pinned extract of the READY T-717 package
(in/T717_PENDING.json, built by t730_extract_t717.py from its commit). The beside register on V3.0.73 is REBUILT: the
concrete rounds 1 .. 8 replayed by t723_alsenan.beside_registers(), round 9 from the merged t722_inputs.build() and the
masonry one-ended figures from the merged t703_inputs.build().

Rebuild:  python3 -I research/agents_t730/t730_alsenan.py --write
Check:    python3 -I research/agents_t730/t730_alsenan.py --check
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t723", ROOT / "research" / "agents_t722", ROOT / "research" / "agents_t703",
          ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t730_rules as R  # noqa: E402
import t723_alsenan as A723  # noqa: E402

R723, R705, R698 = R.R723, R.R705, R.R698
SCHEMA = "URBAN_T730_WIRING_READINESS_R5_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.73"
IDX73 = "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
IDX72 = "research/agents_t703/out/LINE_INDEX_V3_0_72.json"
IDX71 = "research/agents_t704/out/LINE_INDEX_V3_0_71.json"
IDX70 = "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
T723 = "research/agents_t723/out/T723_READINESS.json"
T717 = "research/agents_t730/in/T717_PENDING.json"
T707 = "research/agents_t707/out/T707_COLUMN_TAIL.json"
T714 = "research/agents_t714/out/T714_FORMWORK_BOUNDS.json"
T724 = "research/agents_t724/out/T724_FINDINGS.json"
T725 = "research/agents_t725/out/T725_LEDGER.json"
T726 = "research/agents_t726/out/T726_SHAFT_RESIDUAL.json"
T727 = "research/agents_t727/out/T727_VOIDS_CLOSED.json"
T728 = "research/agents_t728/out/T728_BEAD_RESTATEMENT.json"
T731 = "research/agents_t731/out/T731_LEDGER.json"
T719 = "research/agents_t719/out/T719_VOIDS.json"
T720 = "research/agents_t720/out/T720_GROSS.json"
PINS = [IDX73, IDX72, IDX71, IDX70, T723, T717, T707, T714, T724, T725, T726, T727, T728, T731, T719, T720]
# board MERGED cells (Verifier, Gate A PASS / Gate B PASS), in merge order (R-T723-1 rule 4); git first-parent order
MERGES_NEW = {
    "T-703": "MERGED da1a8906 (Gate B PASS, ARCH_TAKEOFF_V3.0.72)",
    "T-714": "MERGED e6ebe28a (Gate A PASS)",
    "T-723": "MERGED 5d00f738 (Gate A PASS)",
    "T-719": "MERGED 302e002d (Gate A PASS)",
    "T-724": "MERGED cfca9394 (Gate A PASS)",
    "T-727": "MERGED 8ea912b5 (Gate A PASS)",
    "T-722": "MERGED 931dc8d9 (Gate B PASS, ARCH_TAKEOFF_V3.0.73)",
    "T-725": "MERGED b20fe25c (Gate A PASS)",
    "T-726": "MERGED 63720169 (Gate A PASS)",
    "T-728": "MERGED 80e27c10 (Gate A PASS)",
    "T-731": "MERGED e9878f39 (Verifier 2026-11-12T05:59Z, Gate A PASS)",
    "T-720": "MERGED 067b0035 (Gate A PASS)",
}
ORDER = list(A723.ORDER) + [p for p in MERGES_NEW if p not in A723.ORDER]
FW = {"STR.FORMWORK"}
FWS = {"STR.FORMWORK.STAIR"}
CONC = A723.CONC
FORM_RULES = {"L-fb7a6431fede62e93fd5": "R-T724-3 (T-724, a 0 low is no floor: capped blank)"}
# rule 2: declared conflict register (line -> decider). The 13 T-707 column formwork lines: T-707 (merged before) states
# perimeter x h bounds; T-714 (merged after, built on V3.0.70) states 'no positive floor' (BLANK) and declares no
# restatement of T-707. T-732 (TODO) re-derives every moved member's formwork face by face: it decides.
DECIDER_707 = "T-732 (TODO, lane S: formwork of members whose concrete moved; else the Lead)"
HUB = {
    "T-722": "T-722 CONCRETE GATE B ROUND 9 (MERGED, V3.0.73): wired",
    "T-703": "T-703 MASONRY GATE B ROUND 4 (MERGED, V3.0.72): wired",
    "T-717": "T-717 PLASTER / PAINT GATE B ROUND 2, hub H1 (READY, V3.0.74, Gate B pending)",
    "C10": "CONCRETE GATE B ROUND 10 (no row yet; next free version after T-717)",
    "T-729": "T-729 FORMWORK HUB H5f (QUEUED after T-717 and T-732, V3.0.75)",
    "H1R": "H1R CEILING / PLASTER-PAINT ROUND 3 (no row yet)",
    "H2a": "H2a B4-09 INTERIOR beads (no row yet)", "H2b": "H2b B4-09 EXTERIOR beads (no row yet)",
    "H3": "H3 TILES (no row yet)", "H3S": "H3s STAIR FINISHES (no row yet)",
    "H4": "H4 WATERPROOFING + ROOF BUILD-UP (no row yet; T-734 TODO first)",
    "H5": "H5 EARTHWORKS (no row yet; T-708 TODO first)",
}
HUB_ORDER = ["T-717", "C10", "T-729", "H1R", "H2a", "H2b", "H3", "H3S", "H4", "H5"]
HUB_WAITS = {"H4": "WAITS T-734 (Checker downgrade record for the released roof membrane)",
             "H5": "WAITS T-708 (earthworks round 3: zone reconciliation + balance)"}
OUT_JSON = HERE / "out" / "T730_READINESS.json"
OUT_CSV = HERE / "out" / "T730_ROWS.csv"


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def index(rel):
    return {ln["line_id"]: ln for ln in jload(rel)["lines"]}


num = A723.num


# ========================================================================================= beside register (V3.0.73)
def beside_registers(i71):
    """-> (b71, b73, named, provenance). b71 = concrete rounds 1 .. 8 (T-723); b73 = + round 9 (T-722 AT_LEAST set,
    NARROW clears) + masonry one-ended figures of T-703 (V3.0.72). named = lines a merged package recorded a cause on."""
    A723.IDX_CACHE.clear()
    A723.IDX_CACHE.update(i71)
    _, b71, prov = A723.beside_registers()
    import t722_inputs as T722
    import t703_inputs as T703
    reg = dict(b71)
    d722 = T722.build()
    n9 = 0
    named = set()
    for e in d722["entries"]:
        if e["action"] == "AT_LEAST":
            reg[e["line_id"]] = {"side": "AT_LEAST", "value": R.r6(e["beside"]["value"]), "unit": "m3",
                                 "carried_by": "V3.0.73"}
            n9 += 1
        elif e["action"] == "NARROW":
            reg.pop(e["line_id"], None)
        elif e["action"] == "NAMED":
            named.add(e["line_id"])
    for c in d722["confirm"]:
        b = reg.get(c["line_id"])
        if b is None and c.get("record"):           # a V3.0.23 parapet figure T-722 confirmed on its live run
            reg[c["line_id"]] = b = {"side": "AT_LEAST", "value": R.r6(c["value"]), "unit": "m3",
                                     "carried_by": str(c["record"])[:60]}
        if not b or b["value"] != R.r6(c["value"]):
            raise R.ReadinessError(f"T-722 confirm {c['line_id']} {c['value']}: beside register has {b}")
    prov = list(prov) + [{"round": "T-722", "version": "V3.0.73", "one_sided_set": n9}]
    m = 0
    for e in T703.build()["one_sided"]:
        reg[e["line_id"]] = {"side": e["kind"], "value": R.r6(e["printed"]), "unit": e["unit"], "carried_by": "V3.0.72"}
        m += 1
    prov.append({"round": "T-703 (masonry)", "version": "V3.0.72", "one_sided_set": m})
    return b71, reg, named, prov


# ================================================================================================ row helpers
def mk(piece, family, ledger, key, cls, host, reason, *, element, a=None, action=R.NONE, action_reason="",
       new_line_key=None, unit="", hub=None, flags=(), blockers=(), **kw):
    held = a is not None and a["kind"] in (R705.BOUND, R705.BLANK, R723.ONE_SIDED)
    return dict({"piece": piece, "family": family, "owner_family": family,
                 "owner": A723.OWNER.get(family, family), "ledger": ledger, "row": f"{piece}:{key}", "class": cls,
                 "host_line_id": host, "reason": reason, "element": element, "after": a, "action": action,
                 "action_reason": action_reason, "new_line_key": new_line_key, "unit": unit, "hub": hub,
                 "flags": list(flags), "blockers": list(blockers), "held": held,
                 "ledger_state": "HELD" if held else "",
                 "qty": a["value"] if a and a["kind"] == R705.VALUE else None,
                 "lo": a["low"] if a and a["kind"] == R705.BOUND else None,
                 "hi": a["high"] if a and a["kind"] == R705.BOUND else None, "piece_round": "T-730"}, **kw)


def on_line(piece, family, ledger, cited, a, codes, ctx, *, ref, hub, unit=None, **kw):
    lid = R.resolve(cited, ctx["tgt"])
    cls, host, reason = R698.classify(lid, allowed_codes=codes, target=ctx["tgt"], reference=ref,
                                      pending_changed=ctx["pending"], pending_name="the READY package T-717 (V3.0.74)")
    if cls in (R698.STALE, R698.WRONG, R698.AMBIGUOUS, R698.NO_HOST) or host is None:
        raise R.ReadinessError(f"{piece} {lid}: class {cls} ({reason})")
    ac, ar = R.wire_action(a, ctx["tgt"][host], ctx["beside"].get(host), named=host in ctx["named"],
                           form_rule=FORM_RULES.get(host))
    bl = list(kw.pop("blockers", ()))
    if cls == R698.PENDING_CHANGE:
        bl.append("PENDING_ON T-717")
    ln = ctx["tgt"][host]
    return mk(piece, family, ledger, lid, cls, host, reason, element=kw.pop("element", ln["element_id"]), a=a,
              action=ac, action_reason=ar, unit=unit or ln["unit"], hub=hub, blockers=bl, **kw)


# ==================================================================================== (1) T-723 rows restated
def restate723(ctx, i71, b71):
    t = jload(T723)
    if t["candidate"] != "ARCH_TAKEOFF_V3.0.71" or t["line_index_sha256"] != sha(IDX71):
        raise R.ReadinessError("T-723 map is not the V3.0.71 map of record")
    tgt, b73, pend = ctx["tgt"], ctx["beside"], ctx["pending"]
    added717 = {v["element_id"]: k for k, v in ctx["t717"]["added"].items()}
    out = []
    for r in t["rows"]:
        r = json.loads(json.dumps(r))
        r["t723_class"], r["t723_action"], r["t723_live"], r["t723_hub"] = r["class"], r["action"], r["live"], r["hub"]
        r["blockers"] = []
        host = r.get("host_line_id")
        if host:
            cls, why = R723.restate_class(host, i71, tgt, b71, b73, pend)
            if cls == R698.STALE:
                raise R.ReadinessError(f"{r['row']}: {why}")
            if r["class"] in (R698.WRONG, R698.AMBIGUOUS):
                cls = r["class"]
            elif cls == R698.MAPPED and r["t723_class"] == R698.HOST_CHANGED:
                cls, why = R698.HOST_CHANGED, f"{why}; host moved since its ledger (T-723: {r['reason'][:100]})"
            r["class"], r["reason"] = cls, f"V3.0.73: {why}"
            if r["action"] not in (R.ADD,) and r.get("after") and r["class"] not in (R698.WRONG, R698.AMBIGUOUS):
                if r["t723_action"] == R.NONE and "READY package T-703" not in r.get("action_reason", ""):
                    pass                                    # a row that yielded no line still yields none
                else:
                    r["action"], r["action_reason"] = R.wire_action(r["after"], tgt[host], b73.get(host),
                                                                    named=host in ctx["named"],
                                                                    was=r["t723_action"],
                                                                    form_rule=FORM_RULES.get(host))
                    if r["t723_action"] == R.NONE:          # T-713 statements once pending on T-703, now merged
                        r["action_reason"] = "T-703 (V3.0.72) merged: " + r["action_reason"]
            if cls == R698.PENDING_CHANGE:
                r["blockers"].append("PENDING_ON T-717")
        if r["action"] == R.ADD and r.get("new_line_key") in added717:
            r["blockers"].append("PENDING_ON T-717")
            r["pending_line_id"] = added717[r["new_line_key"]]
        hub = r["t723_hub"]
        r["hub"] = {"T-714": "T-729"}.get(hub, hub)
        if r["hub"] in HUB_WAITS and r["action"] not in (R.NONE, R.KEEP, R.WIRED):
            r["blockers"].append(HUB_WAITS[r["hub"]])
        for f in r.get("flags", []):
            if f.startswith("CONDITIONAL") or "ORR-007" in f:
                r["blockers"].append("RULING ORR-007 (payable form)")
            if f.startswith("WIRING_GAP"):
                r["blockers"].append("WAITS T-493 (B7-04 landing lines)")
        if r.get("after") and r["after"]["kind"] == R723.ONE_SIDED and r["after"]["side"] == "CONDITIONAL" \
                and r["action"] in R.MOVING:
            r["blockers"].append("RULING ORR-007 (payable form)")
        r["piece_round"] = r.get("piece_round") or "T-723"
        out.append(r)
    return out, t


# ======================================================================================= (2) new pieces
def p714(ctx, i70):
    d = jload(T714)
    wf = {w["line_id"]: w for w in d["wiring_form"]}
    out = []
    for x in d["lines"]:
        c = x["class_after"]
        if c == "BOUNDED":
            a = R.after(R705.BOUND, lo=num(x["low"]), hi=num(x["high"]), note=x.get("why", "")[:100])
        elif c == "AT_LEAST":
            a = R.after(R723.ONE_SIDED, side="AT_LEAST", value=num(x["low"]), note=x.get("why", "")[:100])
        elif c == "BLANK_NAMED":
            a = R.cap_after(num(x["cap_beside"]), note=x.get("why", "")[:100])
        elif c == "FIX_ROW":
            w = wf[x["line_id"]]
            a = R.after(R705.VALUE, value=num(w["after_m2"]), note=f"{w['fix']} {w['kind']}: {w['basis'][:80]}")
        else:
            raise R.ReadinessError(f"T-714 {x['line_id']}: class {c}")
        members = [m["line_id"] for m in (x.get("member") or {}).get("lines", [])]
        moved = sorted(m for m in members if m in ctx["moved_members"])
        bl = [f"WAITS T-732 (member concrete moved since V3.0.70: {', '.join(moved)})"] if moved else []
        fl = []
        if c == "BLANK_NAMED" and x["cap_beside"] is not None and num(x["cap_beside"]) == 0:
            fl.append("CAP_ZERO: T-714 caps this blank at 0.000000 (its one face 0 .. 0): not carried as a cap "
                      "(R-T730-1 rule 4); T-729 states ZERO_BY_GEOMETRY with evidence or re-measures")
        out.append(on_line("T-714", "B10-13", "T-714 formwork bounds", x["line_id"], a, FW, ctx, ref=i70, hub="T-729",
                           blockers=bl, members=members, flags=fl))
    return out


def p724(ctx, i72):
    d = jload(T724)
    out = []
    f = {x["finding"]: x for x in d["findings"]}
    ring = f["F-V721-1"]
    v = num(ring["after"].split()[1])
    out.append(on_line("T-724", "B10", "T-724 F-V721-1 ring floor", ring["line_id"],
                       R.after(R723.ONE_SIDED, side="AT_LEAST", value=v, note="F-V721-1 floor KEPT (D-28)"), CONC, ctx,
                       ref=i72, hub="C10"))
    for x in f["F-V714-1"]["restated"]:
        lo, hi = (num(s) for s in x["after"].split(".."))
        out.append(on_line("T-724", "B10-13", "T-724 F-V714-1 scaled soffits", x["line_id"],
                           R.after(R705.BOUND, lo=lo, hi=hi, note=f"R-T724-2 edge {x['edge_width_m']} (was {x['before']})"),
                           FW, ctx, ref=i72, hub="T-729"))
    gb = f["F-T723-3"]
    out.append(on_line("T-724", "B10", "T-724 F-T723-3 capped blank", gb["line_id"],
                       R.cap_after(3.5256, note="R-T724-3 gross 44.07 x 0.20 x 0.40; columns not printed (M4 / Q-28)"),
                       CONC, ctx, ref=i72, hub="C10"))
    for x in f["T-721 strip pieces"]["pieces"]:
        a = R.after(R705.BLANK, note=f"NAMED_BLANK_CHILD {x['m3_per_m_depth']} m3 per m depth: {x['item'][:60]}")
        out.append(mk("T-724", "B10", "T-724 strip pieces (R-T724-4)", x["piece"], R698.NO_HOST, None,
                      "a drawn roof-edge piece in no line: the package adds a HELD blank child (never 0)",
                      element=x["member"], a=a, action=R.ADD, action_reason="new HELD blank child line (named)",
                      new_line_key=f"STR.CONC.STRIP:{x['piece']}", unit="m3", hub="C10",
                      held_on=["D-05 / D-26 (projection depth not printed): the line is added HELD blank"]))
    return out


def p725(ctx, i72):
    out = []
    for x in jload(T725)["lines"]:
        c = x["class_after"]
        if c == "BOUNDED":
            a = R.after(R705.BOUND, lo=num(x["low"]), hi=num(x["high"]), note=(x["cause"] or x.get("note") or "")[:100])
        elif c == "AT_LEAST":
            a = R.after(R723.ONE_SIDED, side="AT_LEAST", value=num(x["low"]), note=(x["cause"] or x.get("note") or "")[:100])
        elif c == "BLANK_NAMED":
            a = R.cap_after(num(x["cap"]), note=f"{'/'.join(x['cited'])}: {x['cause'][:80]}")
        else:
            raise R.ReadinessError(f"T-725 {x['line_id']}: class {c}")
        out.append(on_line("T-725", "B10-13", "T-725 stair formwork", x["line_id"], a, FWS, ctx, ref=i72, hub="T-729",
                           held_on=x["cited"]))
    return out


def p731(ctx, i73):
    out = []
    for x in jload(T731)["restated"]:
        lid, item = x["line_id"], x["item"]
        if item == "STR.CONC.STAIR":
            a = R.after(R723.ONE_SIDED, side="AT_LEAST", value=num(x["low_new"]), note="R-T731-2 / R-T696-1 floor")
            fam, codes, hub = "B10", CONC, "C10"
        elif x.get("cap_new"):
            a = R.cap_after(num(x["cap_new"]), note=f"SEQ, coherent B (was {x['cap_old']})")
            fam, codes, hub = "B10-13", FWS, "T-729"
        elif x.get("high_new"):
            a = R.after(R705.BOUND, lo=num(x["low_new"]), hi=num(x["high_new"]), note="R-T731-1 coherent readings")
            fam, codes, hub = "B10-13", FWS, "T-729"
        else:
            a = R.after(R723.ONE_SIDED, side="AT_LEAST", value=num(x["low_new"]), note="R-T731-1 floor unchanged")
            fam, codes, hub = "B10-13", FWS, "T-729"
        out.append(on_line("T-731", fam, "T-731 coherent reading", lid, a, codes, ctx, ref=i73, hub=hub))
    return out


def p726(ctx, i72):
    d = jload(T726)
    out = []
    for x in d["candidate_lines"]:
        a = R.after(R705.NOPROP, note=f"T-726 R-T726-3: carried ONCE ({x['class']})")
        out.append(on_line("T-726", "B5" if x["code"] == "FIN.PLASTER" else "B5-paint", "T-726 shaft residual",
                           x["line"], a, {x["code"]}, ctx, ref=i72, hub=None))
    out.append(mk("T-726", "B5", "T-726 shaft residual", "his-row-13.50", R698.NO_HOST, None,
                  "the freelancer's continued stair-house row (R-T726-1): NO_FACE (R-T726-2), named residual on his side",
                  element="freelancer plaster row 24 / paint row 25 (2.50 x 5.40)",
                  a=R.after(R705.NOPROP, note="engine change 0 m2: never added, never 0 on the engine side"),
                  action=R.NONE, action_reason="no drawn face: no line", unit="m2"))
    return out


def p727(ctx, i72):
    d = jload(T727)
    ct = d["ceiling_top"]
    out = []
    own = ct["ownership"]
    for lid, cause in own["excluded"]:
        out.append(on_line("T-727", "B5-ceiling", "T-727 V-01 ceiling (R-T727-2)", lid,
                           R.after(R723.EXCLUDED, note=f"{cause} (R-T727-2)"), {"FIN.CEILING"}, ctx, ref=i72, hub="H1R"))
    out.append(on_line("T-727", "B5-ceiling", "T-727 V-01 ceiling owner", own["owner"],
                       R.after(R705.NOPROP, note="owner of the V-01 top (decor group), ONCE"), {"FIN.CEILING"}, ctx,
                       ref=i72, hub=None))
    fl = d["floor_1F"]
    out.append(on_line("T-727", "B6", "T-727 1F floor (R-T727-3)", fl["line"],
                       R.after(R705.NOPROP, note="ENGINE_RIGHT: overlap deducted once (T-719 finding 1 withdrawn)"),
                       {"FIN.FLOOR.PORCELAIN"}, ctx, ref=i72, hub=None))
    bed = R.resolve(fl["bed_line_same_area"]["line"], ctx["tgt"])
    out.append(on_line("T-727", "B6", "T-727 1F floor bed", bed,
                       R.after(R705.NOPROP, note="bed follows the floor unchanged"),
                       {ctx["tgt"][bed]["item_code"]}, ctx, ref=i72, hub=None))
    for lid in d["V-07"]["lines"]:
        out.append(on_line("T-727", "B5-ceiling", "T-727 V-07 (R-T727-4)", lid,
                           R.after(R705.NOPROP, note="V-07 VOID_EXTENT_UNRESOLVED: nothing deducted, HELD (S0 / S1)"),
                           {"FIN.CEILING"}, ctx, ref=i72, hub=None))
    return out


def p728(ctx, i72):
    d = jload(T728)
    if d["stale"] != 0 or d["rows_restated"] != len(d["rows"]):
        raise R.ReadinessError("T-728 ledger not stale-0 / complete")
    out = []
    for x in d["rows"]:
        host = R.resolve(x["host_line"], ctx["tgt"])
        cls, h, reason = R698.classify(host, allowed_codes={x["host_code"]}, target=ctx["tgt"], reference=i72,
                                       pending_changed=ctx["pending"], pending_name="the READY package T-717 (V3.0.74)")
        if cls not in (R698.MAPPED, R698.PENDING_CHANGE):
            raise R.ReadinessError(f"T-728 {x['edge_id']}: host {cls}")
        if x["bead_state"] == "HELD_BOUND":
            a = R.after(R705.BOUND, lo=x["low"], hi=x["high"], note=f"R-T728-1 bead HELD with its host ({x['host_state']})")
        elif x["bead_state"] == "HELD_BLANK":
            a = R.after(R705.BLANK, note=f"R-T728-1 host blank: {x['ledger_ref'][:60]}")
        else:
            raise R.ReadinessError(f"T-728 {x['edge_id']}: state {x['bead_state']}")
        bl = []
        if cls == R698.PENDING_CHANGE:
            bl.append("PENDING_ON T-717")
        if x["pending"].startswith("T-314"):
            bl.append("WAITS T-314 r3 (face rows replace the blank facade host)")
        held_on = ["D-62 (plinth host blank): the bead is added HELD blank"] \
            if x["scope"] == "EXTERIOR" and not x["pending"] else []
        out.append(mk("T-728", "B4-09", "T-728 bead restatement", x["edge_id"], cls, host, reason, element=x["edge_id"],
                      a=a, action=R.ADD, action_reason="bead line on its host (R-T728-1), one per host",
                      new_line_key=f"B4-09@{host}", unit="lm", hub=x["hub"], blockers=bl, scope=x["scope"], held_on=held_on,
                      host_state=x["host_state"]))
    return out


# =================================================================================================== census
def census(tgt, beside, rows, codes, *, label_after):
    """per code: released / bounded / one-sided (per side) / blank / excluded lines and sums per state on V3.0.73 and as
    the live rows would leave it (a projection of the map, not a run). Sums are per state only, never across states."""
    live = {r["host_line_id"]: r for r in rows if r.get("host_line_id") and r.get("live") == R.LIVE
            and r.get("action") in R.MOVING}
    out = {}
    for code in sorted(codes):
        ids = [k for k, ln in tgt.items() if ln["item_code"] == code]
        st = {}
        for when in ("v3_0_73", label_after):
            c, s = Counter(), Counter()
            for k in ids:
                ln, b = dict(tgt[k]), beside.get(k)
                r = live.get(k) if when != "v3_0_73" else None
                if r is not None:
                    a = r["after"]
                    if a["kind"] == R705.BOUND:
                        ln.update(measured_net=None, held_low=a["low"], held_high=a["high"])
                        b = None
                    elif a["kind"] == R705.VALUE:
                        ln.update(measured_net=a["value"], held_low=None, held_high=None)
                        b = None
                    elif a["kind"] == R723.ONE_SIDED:
                        ln.update(measured_net=None, held_low=None, held_high=None)
                        b = {"side": a["side"], "value": a["value"]}
                    elif a["kind"] == R723.EXCLUDED:
                        ln.update(measured_net=None, held_low=None, held_high=None, **{"class": "EXCLUDED"})
                        b = None
                v, lo, hi = ln["measured_net"], ln["held_low"], ln["held_high"]
                if ln["class"] == "EXCLUDED" and v is None and lo is None and hi is None:
                    c["excluded"] += 1
                elif v is not None:
                    c["released"] += 1
                    s["released"] += v
                elif lo is not None and hi is not None:
                    c["bounded"] += 1
                    s["bounded_low"] += lo
                    s["bounded_high"] += hi
                elif b:
                    c[f"blank_{b['side'].lower()}"] += 1
                    s[f"{b['side'].lower()}_beside"] += b["value"]
                else:
                    c["blank"] += 1
            st[when] = {"lines": len(ids), "counts": dict(sorted(c.items())),
                        "sums_by_state": {k: round(v, 6) for k, v in sorted(s.items())}}
        out[code] = st
    return out


# =================================================================================================== build
def build():
    i73, i72, i71, i70 = index(IDX73), index(IDX72), index(IDX71), index(IDX70)
    if set(i73) != set(i71) or set(i72) != set(i71):
        raise R.ReadinessError("V3.0.71 / .72 / .73 line ids differ: restate the id note")
    b71, b73, named, prov = beside_registers(i71)
    for lid, b in b73.items():
        ln = i73.get(lid)
        if ln is None or ln["measured_net"] is not None or (ln["held_low"] is not None and ln["held_high"] is not None):
            raise R.ReadinessError(f"beside register {lid}: not a HELD line without value / range on V3.0.73")
    t717 = jload(T717)
    if t717["base"] != CANDIDATE:
        raise R.ReadinessError("T-717 extract is not on V3.0.73")
    pending = {k: f"T-717 {v} (V3.0.74, READY)" for k, v in t717["changed"].items()}
    b70 = {}
    A723.IDX_CACHE.clear()
    A723.IDX_CACHE.update(i71)
    b70, _, _ = A723.beside_registers()
    moved = {k for k in i73 if i73[k]["item_code"].startswith("STR.CONC.")
             and (R698.state_key(i70.get(k)) != R698.state_key(i73[k]) or b70.get(k) != b73.get(k))}
    ctx = {"tgt": i73, "beside": b73, "named": named, "pending": pending, "t717": t717, "moved_members": moved}
    rows723, t723 = restate723(ctx, i71, b71)
    new = (p714(ctx, i70) + p724(ctx, i72) + p725(ctx, i72) + p726(ctx, i72) + p727(ctx, i72) + p728(ctx, i72)
           + p731(ctx, i73))
    rows = rows723 + new
    # rule 5: T-728 restates the T-697 bead ADD rows arris by arris
    e697 = [r for r in rows723 if r["piece"] == "T-697" and r["t723_action"] == R.ADD]
    l728 = [r for r in new if r["piece"] == "T-728"]
    sup = R.arris_supersede(e697, l728)
    by_row = {r["row"]: r for r in rows}
    for old, nw in sup.items():
        by_row[old]["live"], by_row[old]["live_of"] = R.SUPERSEDED, nw
        by_row[old]["flags"] = [f for f in by_row[old]["flags"] if not f.startswith("RULING_RESTATE")] + \
            ["RULING_RESTATE closed: restated by T-728 (R-T728-1) arris by arris"]
        by_row[nw]["live"] = R.LIVE
    beads = {r["row"] for r in rows if r["piece"] in ("T-697", "T-728")}
    for r in rows:
        if r["row"] not in beads:
            r["live"] = None
    supersede = {("T-718", "T-715"): {x["line_id"] for x in jload("research/agents_t718/out/T718_LEDGER.json")["lines"]},
                 ("T-724", "T-714"): {r["host_line_id"] for r in new if r["piece"] == "T-724" and r["family"] == "B10-13"},
                 ("T-731", "T-725"): {r["host_line_id"] for r in new if r["piece"] == "T-731" and r["family"] == "B10-13"},
                 ("T-731", "T-711"): {r["host_line_id"] for r in new if r["piece"] == "T-731" and r["family"] == "B10"}}
    conflicts = {x["fw_line"]: DECIDER_707 for x in jload(T707)["formwork"]}
    R.resolve_live([r for r in rows if r["row"] not in beads], ORDER, supersede, conflicts)
    for r in rows:
        r.setdefault("live", None)
    R723.check_one_line_per_row([r for r in rows if r["row"] not in beads])
    R723.check_after(new)
    R698.check_hosts_present(rows, i73)
    R698.check_no_zero_for_held(rows)
    R705.check_owner_named(rows)
    R.check_blockers(rows)
    for r in rows:
        if r["class"] == R698.STALE:
            raise R.ReadinessError(f"stale host {r['row']}")
        if r["held"] and r["qty"] is not None:
            raise R.ReadinessError(f"{r['row']}: HELD row with a quantity")
    # T-727 downstream: the tread double-count risk sits on the T-715 rows of the same lines
    for x in jload(T727)["downstream"]:
        for lid in x["lines"]:
            for r in rows:
                if r["host_line_id"] == lid and r["piece"] in ("T-715", "T-718"):
                    r["flags"].append(f"T-727 {x['result']}: highs {x['highs_sum_m2']} vs union {x['union_m2']} "
                                      "(excess 0.057439 m2); T-715 proposes EXCLUDED, which removes the highs")
                    r["blockers"].append("PENDING_ON T-733 (tread overlap closed by handle, READY)")
    for r in rows:
        r["blockers"] = sorted(set(r["blockers"]))
    expect = {"T-714": 370, "T-724": 1 + 4 + 1 + 4, "T-725": 20, "T-726": 15, "T-727": 6, "T-728": 116, "T-731": 4}
    pieces = {}
    for p, n in expect.items():
        sel = [r for r in new if r["piece"] == p]
        classes = R698.reconcile(sel, n, p)
        pieces[p] = {"rows": n, "merge": MERGES_NEW[p], "classes": {k: v for k, v in classes.items() if v},
                     "actions": dict(sorted(Counter(r["action"] for r in sel).items())),
                     "live": dict(sorted(Counter(str(r["live"]) for r in sel).items()))}
    restated = {"rows": len(rows723), "t723_rows": len(t723["rows"]),
                "classes_before": dict(sorted(Counter(r["t723_class"] for r in rows723).items())),
                "classes_after": dict(sorted(Counter(r["class"] for r in rows723).items())),
                "actions_before": dict(sorted(Counter(r["t723_action"] for r in rows723).items())),
                "actions_after": dict(sorted(Counter(r["action"] for r in rows723).items())),
                "wired_by_hub": dict(sorted(Counter(r["t723_hub"] for r in rows723 if r["action"] == R.WIRED).items())),
                "stale": 0}
    if restated["rows"] != restated["t723_rows"]:
        raise R.ReadinessError("T-723 rows lost in the restatement")
    hubs = []
    done = []
    for n, h in enumerate(HUB_ORDER, 1):
        sel = [r for r in rows if r.get("hub") == h]
        s = R.package_size(sel)
        ok, open_ = R.buildable(sel, earlier_hubs=done + [h])
        hubs.append({"order": n, "hub": h, "package": HUB[h], "rows": len(sel),
                     "live_rows": sum(1 for r in sel if r.get("live") in (R.LIVE, None) and r["action"] != R.NONE),
                     "changed": s["changed"], "text_only": s["text_only"], "added": s["added"],
                     "changed_ids": s["changed_ids"], "text_ids": s["text_ids"], "added_keys": s["added_keys"],
                     "wired": sum(1 for r in sel if r["action"] == R.WIRED),
                     "conflict_lines": sorted({r["host_line_id"] for r in sel if r.get("live") == R.CONFLICT}),
                     "form_conflicts": sorted({r["host_line_id"] for r in sel if r["action"] == R.FORM_CONFLICT}),
                     "buildable_after_earlier_hubs": ok, "open_blockers": open_,
                     "blocked_rows": sum(1 for r in sel if r["blockers"] and r["action"] not in (R.NONE, R.KEEP, R.WIRED)
                                         and r.get("live") in (R.LIVE, None, R.CONFLICT))})
        done.append(h)
    merged_hubs = {h: {"package": HUB[h], "rows": sum(1 for r in rows723 if r["t723_hub"] == h),
                       "wired": sum(1 for r in rows723 if r["t723_hub"] == h and r["action"] == R.WIRED),
                       "still_moving": sorted({r["host_line_id"] for r in rows723 if r["t723_hub"] == h
                                               and r["action"] in R.MOVING + (R.ADD,) and r.get("live") == R.LIVE})}
                   for h in ("T-722", "T-703")}
    fw_rows = [r for r in rows if r.get("hub") == "T-729"]
    conc_rows = [r for r in rows if r.get("hub") == "C10"]
    return {
        "schema": SCHEMA, "task": "T-730", "rule": [R.RULE_ID, R.RULE_VERSION],
        "base_rules": [list(b) for b in R.BASE_RULES], "candidate": CANDIDATE, "line_index_sha256": sha(IDX73),
        "inputs_sha256": {p: sha(p) for p in PINS},
        "index_note": "V3.0.71 / .72 / .73 carry the same 5,123 line ids; V3.0.72 moved 10 masonry ranges (T-703), "
                      "V3.0.73 5 column lows (T-722 NARROW); asserted by the restate classes",
        "beside_register": {"rounds": prov, "v3_0_71": len(b71), "v3_0_73": len(b73),
                            "changed_71_73": sorted(k for k in set(b71) | set(b73) if b71.get(k) != b73.get(k)),
                            "named_by_t722": len(named),
                            "scope": "concrete rounds 1 .. 9 + masonry one-ended (T-703); V3.0.23 parapet / V3.0.46 "
                                     "lift / V3.0.58 WP beside records are confirmed by each package on its live run"},
        "t717_pending": {"commit": t717["commit"], "changed": len(t717["changed"]), "added": len(t717["added"])},
        "moved_concrete_members_since_v3_0_70": sorted(moved),
        "restated_t723": restated, "merged_hubs": merged_hubs, "pieces": pieces,
        "no_line_target": {
            "T-719": "void register B2-05 (7 voids): band prerequisite consumed by T-717; findings closed by T-727",
            "T-720": "gross / covered floor area B2-03 (GF 278.266291, 1F 209.839104, 2F 55.08 m2): a coverage "
                     "registry denominator (lane I, BOQ_FAMILY_MASTER), no candidate line; Lead decides any B2-03 line"},
        "conflict_register": conflicts,
        "census_formwork_t729": census(i73, b73, fw_rows, FW | FWS, label_after="after_t729_projection"),
        "census_concrete_c10": census(i73, b73, conc_rows, {i73[r["host_line_id"]]["item_code"] for r in conc_rows
                                                            if r.get("host_line_id")}, label_after="after_c10_projection"),
        "hub_order": hubs, "stale": 0, "rows": rows,
    }


CSV_COLS = ["piece", "family", "ledger", "row", "class", "host_line_id", "action", "live", "after", "unit", "hub",
            "owner_family", "element", "new_line_key", "blockers", "flags", "reason", "action_reason"]


def to_csv(d):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in d["rows"]:
        out = []
        for c in CSV_COLS:
            v = r.get(c)
            out.append(R.after_text(v) if c == "after" else " | ".join(v) if c in ("flags", "blockers")
                       else "" if v is None else v)
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
        print("T-730 check:", "EQUAL" if ok else "DIFFERS")
        return 0 if ok else 1
    print(json.dumps({"pieces": d["pieces"], "restated": d["restated_t723"], "merged_hubs": d["merged_hubs"],
                      "beside": {k: v for k, v in d["beside_register"].items() if k != "changed_71_73"},
                      "hub": [(h["order"], h["hub"], h["rows"], h["changed"], h["text_only"], h["added"], h["wired"],
                               len(h["conflict_lines"]), h["blocked_rows"], h["buildable_after_earlier_hubs"],
                               h["open_blockers"]) for h in d["hub_order"]]}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
