"""T-654 WIRING MANIFEST V20 + overlay dry run on ARCH_TAKEOFF_V3.0.61 (R-T654-1; lane I, non-candidate, research only).

V20 moves the overlay base from ARCH_TAKEOFF_V3.0.59 (V19, T-652 merged 2e80c03f) to the merged candidate of record
ARCH_TAKEOFF_V3.0.61 and carries the one Lead fix row accepted since V19 (claim 2026-11-09T17:00Z):
  - V3.0.60 (T-423 r3, Gate B MERGED 62e18eed): 22 CHANGED_TEXT_ONLY lines (5 FIN.CEILING dome lists, the D-1F-04 face
    move on the 1F-02 tile / backing pair, 14 FIN.MARBLE.THRESHOLD material state + measure pair, the D-1F-03 dry strip
    measure pair); no quantity field moves (class, net, held low / high): asserted line by line against the T-423
    inputs' own 'expect' (the state the merged module binds to). The line index is the V3.0.59 one on those lines.
  - V3.0.61 (T-563, Gate B MERGED e04d99d9): PLASTER_HEIGHT_V1_WIRING restates 11 FIN.PLASTER lines (4 released 217.2081
    m2 -> HELD; 7 held ranges moved), each HELD BOUNDED_EXPOSURE with the roof build-up RFI D-39 / DCR-6; paint pairs
    byte-identical (summary_t563.json, the numbers-only package summary of record).
  - The overlay carried both merges before they merged: package 'T-423 r2' (17 TEXT_ONLY rows on V3.0.60 lines and its
    2 named set-asides) and package 'T-563' (11 PLASTER_HEIGHT_V1 SET + 11 PAINT_UNCHANGED TEXT_ONLY, then FR-T617-1
    chained on 3 lines). Each PLASTER_HEIGHT_V1 / PAINT_UNCHANGED row leaves the overlay only by equality with
    the merged line; FR-T617-1 (T-617 Checker AGREE, not part of the merged module) stays chained after them.
  - F-T652-1 (Lead fix row accepted in the T-652 verdict, Verifier 2026-11-09 11:29): T-615 deducted the D-1F-07 RC
    lintel face from the 1F 0.15 m ASSUMED host as (0.80 + 2 x 0.40) x 0.20 = 0.32 m2; the Checker's 07:06 re-measure
    bounds that lintel at 0.036 .. 0.04377 m3 = length 1.20 .. 1.459 m (START available 0.259 < printed MIN 0.40), so the
    face is 0.240 .. 0.2918 m2. The units and panel-mortar lines of that host move RELEASED -> HELD on the bound their
    own formula gives over the re-measured face (never a point, never 0); the host MAS.BLOCK contract net is untouched.

R-T654-1 (every villa on the engine's line-index scheme; adds to R-T652-1, which stands whole):
  (a) A MERGED TEXT-ONLY VERSION MOVES NO INDEX LINE: each line it names keeps class, net and held bound equal to the
      state its inputs bind to; a quantity field that differs is refused.
  (b) A MERGED RESTATEMENT BECOMES THE BASE ONLY BY EQUALITY: each restated line's merged 'before' must be the base line;
      an overlay SET that carried it pre-merge leaves the overlay only when its before and after equal the merged
      before / after (TEXT_ONLY rows of the same package only when the merged package keeps that line byte-identical);
      every row chained after them stays and must still apply (never STALE); the rebased overlay must give every line
      byte-equal to the previous manifest.
  (c) A CROSS-TRADE RE-MEASURE IS PROPAGATED AS A BOUND: when the Checker bounds an element whose face another trade's
      line deducts at a point, the dependent lines move to HELD low .. high computed by their own formula at both ends of
      the bound (both ends from the re-measure, the line's other terms unchanged); the old released point is not kept
      when it lies outside that bound; never 0, never a value.
  (d) A FREELANCER FIGURE IS NEVER A SOURCE (R-T652-1 (e), restated).
Rebuild: `URBAN_T654_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-654
tests/t654_manifest_v20/test_t654.py::test_write_outputs`; check: `... pytest --tree task-T-654 tests/t654_manifest_v20`.
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT / "research/agents_t652", ROOT / "research/agents_t423", ROOT / "research/agents_t563"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import manifest_v19 as M19                                            # noqa: E402  (R-T652-1, read only)
import t423_inputs as I423                                            # noqa: E402  (T-423 r3 inputs, read only)
import t563_inputs as I563                                            # noqa: E402  (T-563 inputs, read only)

M18, M15, M9, OV = M19.M18, M19.M15, M19.M9, M19.OV
D, S, q6 = M19.D, M19.S, M19.q6

SCHEMA = "URBAN_T654_WIRING_MANIFEST_V20"
RULE = "R-T654-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V20.json"
CANDIDATE = ("ARCH_TAKEOFF_V3.0.61 (T-563 Gate B MERGED e04d99d9 on V3.0.60, T-423 r3 Gate B MERGED 62e18eed on "
             "V3.0.59; 5,073 lines: V3_0_59 75331a76 -> V3_0_60 8c8a9642 (22 text-only) -> V3_0_61 2bc99980 (11 "
             "FIN.PLASTER restated))")
IN = {
    "INDEX59": ROOT / "research/agents_t651/out/LINE_INDEX_V3_0_59.json",
    "T563": ROOT / "research/agents_t563/summary_t563.json",
    "T498": ROOT / "research/agents_t498/summary_t498.json",
    "T650": ROOT / "research/agents_t650/out/T650_PAYABLE_FORM.json",
    "V19": ROOT / "research/agents_t652/out/WIRING_MANIFEST_V19.json",
    "V19_CODE": ROOT / "research/agents_t652/manifest_v19.py",
    "T423_INPUTS": ROOT / "research/agents_t423/t423_inputs.py",
    "T563_INPUTS": ROOT / "research/agents_t563/t563_inputs.py",
}
# pinned on the merged tree at claim (2026-11-09T17:00Z, engine e04d99d9); an edited input stops the build
PINS = {
    "INDEX59": "2cd0ebd8e39db84510ba7a4a4f257cd3b2c1176f650ca7094ed71741fb698ab0",
    "T563": "7e34828ce9c72534c5c6776a13ae4fe9b89b0f632bd41326005e85132e83978c",
    "T498": "47737dc2b80b3b656cb57b306b84c695bae3abaab2097c744993798ef9a46765",
    "T650": "cd72b44596cc1b2840282ab56f1f6653a7b53b5601db2bb9f3f7bcb7eb0a1fb2",
    "V19": "39e1b1c157900f288196babd593ec15b4466e6e077bb75191bba126d42fbd07d",
    "V19_CODE": "365b9281481bda086bdf62d30882354a6daddff1c1d5f0edbf402a078da424ba",
    "T423_INPUTS": "a0d446e5d30e708a2ffacf9962859836c7d7f57f300b6f292ab9111c98d77fcb",
    "T563_INPUTS": "b16ef3ffdbfbb348ab6096150615c9c7ef794e557a094c1e35a04073071491ce",
}

MERGED = {
    "T-423": {"merge": "62e18eed",
              "verdict": "BOARD T-423 r3 VERIFIER 2026-11-09 (Gate B step 3 MERGED 62e18eed): ARCH_TAKEOFF_V3.0.60, own "
                         "Drive chain V3_0_59 75331a76 -> V3_0_60 8c8a9642, 22 CHANGED_TEXT_ONLY, totals moved {} "
                         "(no quantity field moves); master 1.60.0"},
    "T-563": {"merge": "e04d99d9",
              "verdict": "BOARD T-563 VERIFIER 2026-11-09 (Gate B step 4 MERGED e04d99d9): ARCH_TAKEOFF_V3.0.61 "
                         "PLASTER_HEIGHT_V1_WIRING, V3_0_60 8c8a9642 -> V3_0_61 2bc99980, 5,062 SAME + 11 CHANGED; "
                         "FIN.PLASTER released 580.5819 -> 363.3738 m2, 4 lines 217.2081 -> HELD 262.01799 .. "
                         "262.05199, every line HELD with D-39 / DCR-6 (F-C-T563-2: the next manifest carries the 11 "
                         "lines); paint byte-identical; master 1.61.0"},
    "T-652": {"merge": "2e80c03f",
              "verdict": "BOARD T-652 VERIFIER 2026-11-09 11:29 (MERGED 2e80c03f): F-T652-1 (D-1F-07 face 0.24 .. "
                         "0.2918 vs 0.32 deducted) accepted as a Lead fix row; T-650 CHECKER RE-MEASURE 07:06: D-1F-07 "
                         "0.15 x 0.20 x (0.80 + 0.40) = 0.036 .. 0.15 x 0.20 x (0.80 + 0.40 + 0.259) = 0.04377 m3, START "
                         "available 0.259 < printed MIN 0.40, HELD BY NAME (designer item)"},
}
P563 = "T-563"
P423 = "T-423 r2"
P498 = M19.P498
STAGE_ROW = "PLASTER_HEIGHT_V1"
PAINT_ROW = "PAINT_UNCHANGED"
F_T652_1 = {"opening": "D-1F-07", "host": "L-a56a8add7812d1b52cb7", "units": "L-1e61a4aaeb00aa711dcd",
            "mortar": "L-866a6602ffa70d03f210"}
TEXT_ONLY_60 = 22


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pins(pinmap=None):
    for k, pin in (pinmap or PINS).items():
        if pin and sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def require_merged(task, merged=None):
    m = MERGED if merged is None else merged
    if task not in m or not m[task].get("merge") or not m[task].get("verdict"):
        raise ManifestError(f"{task} is not MERGED with a Checker verdict: its rows cannot enter a manifest")
    return m[task]


def _qstate(l):
    return {k: l.get(k) for k in OV.QFIELDS}


# ---- (a) V3.0.59 -> V3.0.60: text only ------------------------------------------------------------------------------

def text_only_60(base, entries=None):
    """R-T654-1 (a): the T-423 r3 lines keep every quantity field; returns the sorted line ids (22)."""
    ents = I423.build()["entries"] if entries is None else entries
    seen = {}
    for e in ents:
        lid, x = e["line_id"], e["expect"]
        l = base.get(lid)
        if l is None:
            raise ManifestError(f"{lid}: a V3.0.60 line not in the V3.0.59 base")
        if (l["item_code"], l["unit"], l["element_id"]) != (x["item_code"], x["unit"], x["element_id"]):
            raise ManifestError(f"{lid}: V3.0.60 binds {x['item_code']} {x['element_id']}, the base is "
                                f"{l['item_code']} {l['element_id']}")
        if "measured_net" in x and (l["class"] != "RELEASED" or D(l["measured_net"]) != D(x["measured_net"])):
            raise ManifestError(f"{lid}: V3.0.60 binds net {x['measured_net']}, the base is {OV.state(l)} "
                                "(a text-only version moves no quantity: R-T654-1 (a))")
        seen.setdefault(lid, []).append(e["action"])
    return {k: sorted(v) for k, v in sorted(seen.items())}


def rebase_423(order, base, text60, set_aside, pkg=P423):
    """(a)/(b): the pre-merge 'T-423 r2' TEXT_ONLY rows leave the overlay when the merged V3.0.60 names their line (a
    text-only line or a named set-aside) and their before is the base line; the emptied package leaves the order."""
    named = set(text60) | set(set_aside)
    out, removed = [], []
    for name, ops in order:
        if name != pkg:
            out.append((name, ops))
            continue
        for op in ops:
            lid = op["line_id"]
            if op["kind"] != "TEXT_ONLY" or lid not in named or not OV.same_state(op["before"], base[lid]):
                raise ManifestError(f"{op['op_id']}: a pre-merge T-423 row the merged V3.0.60 does not carry "
                                    "as it stands: refused (R-T654-1 (b))")
            removed.append(op["op_id"])
    if not removed:
        raise ManifestError(f"{pkg}: no pre-merge rows found (the V19 order changed)")
    return out, removed


# ---- (b) V3.0.60 -> V3.0.61: the T-563 restatement ------------------------------------------------------------------

def _merged_state(s):
    st = s["state"]
    if st == "BOUNDED_EXPOSURE":
        if s["low"] is None or s["high"] is None:
            raise ManifestError("a bounded merged line without its bound")
        return M9.held(s["low"], s["high"])
    if st in ("BLOCKED_RFI",):
        if s["value"] is not None or s["low"] is not None:
            raise ManifestError("a blocked merged line carries a figure (HELD is never a value)")
        return M9.held()
    if st in ("PROVISIONAL", "SOURCE_DERIVED", "MEASURED"):
        if s["value"] is None:
            raise ManifestError("a released merged line without a value")
        return M9.released(s["value"])
    raise ManifestError(f"merged state {st} has no index class")


def stage_61(base, t563):
    """the 11 restated lines: {line_id: (before_state, after_state, paint_line_id, room)}; before = the base line."""
    out = {}
    for r in t563["rows"]:
        lid = r["line_id"]
        b, a = _merged_state(r["before"]), _merged_state(r["after"])
        if lid not in base or base[lid]["item_code"] != "FIN.PLASTER" or not OV.same_state(b, base[lid]):
            raise ManifestError(f"{lid}: the merged before {OV.state(b)} is not the base line "
                                f"{OV.state(base.get(lid, {}))} (R-T654-1 (b))")
        if a["class"] != "HELD" or a["measured_net"] is not None:
            raise ManifestError(f"{lid}: T-563 restates to HELD only (never a value, never 0)")
        if r.get("manifest_after") != [a["held_low"], a["held_high"]] or not r.get("paint_byte_identical"):
            raise ManifestError(f"{lid}: the merged after is not the T-558 manifest's / paint moved")
        out[lid] = {"before": b, "after": a, "paint": r["paint_line_id"], "room": r["room"]}
    if len(out) != 11:
        raise ManifestError(f"T-563: {len(out)} restated lines (the merged summary names 11)")
    return out


def base_v3061(base59, stage):
    base = {k: dict(v) for k, v in base59.items()}
    for lid, s in stage.items():
        base[lid].update(_qstate(s["after"]))
    return base


def rebase_563(order, stage, pkg=P563):
    """(b): drop the pre-merge T-563 rows equal to the merged lines; returns (order, removed ids)."""
    paints = {s["paint"] for s in stage.values()}
    out, removed, seen_set, seen_paint = [], [], set(), set()
    for name, ops in order:
        keep = []
        for op in ops:
            lid = op["line_id"]
            if name == pkg and op["row"] == STAGE_ROW:
                s = stage.get(lid)
                if s is None or op["kind"] != "SET" or not OV.same_state(op["before"], s["before"]) or \
                        not OV.same_state(op["after"], s["after"]):
                    raise ManifestError(f"{op['op_id']}: the pre-merge row {OV.state(op['before'])} -> "
                                        f"{OV.state(op.get('after') or {})} is not the merged line: refused "
                                        "(R-T654-1 (b))")
                removed.append(op["op_id"])
                seen_set.add(lid)
                continue
            if name == pkg and op["row"] == PAINT_ROW:
                if op["kind"] != "TEXT_ONLY" or lid not in paints:
                    raise ManifestError(f"{op['op_id']}: a paint row on a line the merged package does not keep")
                removed.append(op["op_id"])
                seen_paint.add(lid)
                continue
            if lid in stage and op["kind"] in ("ADD", "SET", "RECODE") and lid not in seen_set:
                raise ManifestError(f"{op['op_id']}: writes a restated line before its merged row (order)")
            keep.append(op)
        out.append((name, keep))
    if seen_set != set(stage) or seen_paint != paints:
        raise ManifestError(f"pre-merge rows missing: {sorted(set(stage) - seen_set)[:3]} "
                            f"{sorted(paints - seen_paint)[:3]} (the base move is not an identity)")
    return out, removed


# ---- (c) F-T652-1: the D-1F-07 face in the 1F 0.15 m ASSUMED host ---------------------------------------------------

def f_t652_1_rows(t498, t650, idx, order, merged=None):
    src = require_merged("T-652", merged)
    oid = F_T652_1["opening"]
    po = t650["per_opening"][oid]
    vlo, vhi = D(po["low_m3"]), D(po["high_m3"])
    if (vlo, vhi) != (Decimal("0.036"), Decimal("0.04377")):
        raise ManifestError(f"{oid}: census bound {S(vlo)} .. {S(vhi)} is not the Checker's 0.036 .. 0.04377")
    recs = {}
    for r in t498["rows"]:
        if r["source_line_id"] == F_T652_1["host"] and r["item_code"] in ("MAS.UNITS.BLACK", "MAS.MORTAR.BLACK"):
            recs[r["item_code"]] = r
    u, m = recs["MAS.UNITS.BLACK"], recs["MAS.MORTAR.BLACK"]
    if (u["line_id"], m["line_id"]) != (F_T652_1["units"], F_T652_1["mortar"]):
        raise ManifestError("F-T652-1: the host's material lines are not the named ones")
    t = D(u["element_id"].split("t=", 1)[1].split("#", 1)[0])
    faces = {f["opening_id"]: f for f in u["lintels"]}
    f7 = faces[oid]
    if f7["kind"] != "REQUIRED" or D(f7["face_m2"]) != Decimal("0.32"):
        raise ManifestError(f"{oid}: T-615 face {f7} is not the REQUIRED 0.32 m2 the finding names")
    other_req = sum((D(f["face_m2"]) for k, f in faces.items() if f["kind"] == "REQUIRED" and k != oid), Decimal(0))
    held = sum((D(f["face_max_m2"]) for f in faces.values() if f["kind"] != "REQUIRED"), Decimal(0))
    flo, fhi = vlo / t, vhi / t                     # the face of a t-deep lintel: m3 / t (0.15 x 0.20 x L -> 0.20 x L)
    c = D(idx[F_T652_1["host"]]["measured_net"])
    if c != D(u["contract_net_m2"]):
        raise ManifestError("F-T652-1: host contract net is not the record's")
    # line convention (R-T629-1 (d), T-615): the line carries the LOW end of the HELD faces (D-1F-09 at its max)
    b_lo, b_hi = c - other_req - fhi - held, c - other_req - flo - held
    ul, uh = q6(b_lo * M19.UNITS_PER_M2), q6(b_hi * M19.UNITS_PER_M2)
    ml, mh = q6(b_lo * M19.PANEL_015), q6(b_hi * M19.PANEL_015)
    out, calc = [], {}
    for lid, lo, hi, what, rate in ((u["line_id"], ul, uh, "units", "12.5 / m2 (Q-80 A)"),
                                    (m["line_id"], ml, mh, "panel mortar", "0.0110625 m3 / m2 (T-615)")):
        line = idx[lid]
        if line["class"] != "RELEASED":
            raise ManifestError(f"{lid}: not the RELEASED line T-615 valued")
        old = D(line["measured_net"])
        if lo <= old <= hi:
            raise ManifestError(f"{lid}: the released {S(old)} lies inside the new bound: not this rule's case")
        pkg = M18.writer_of(order, lid)
        if pkg != P498:
            raise ManifestError(f"{lid}: written by {pkg}, expected the T-498 chain (R1)")
        out.append(M19.row(pkg, f"F-T652-1/{what.split()[0]}", "SET", lid, OV.state(line),
                           M9.held(float(lo), float(hi)), "HELD", src["verdict"],
                           beside={"opening": oid, "host": F_T652_1["host"],
                                   "cause": f"F-T652-1: the {oid} RC lintel face deducted from this host is 0.240 .. "
                                            "0.2918 m2 (Checker re-measure 07:06: START available 0.259 < printed MIN "
                                            "0.40, designer item D-1F-07 bearing), not the 0.32 m2 T-615 deducted; HELD "
                                            "on the bound until the designer fixes the bearing",
                                   "hand": f"base = {S(c)} - {S(other_req)} (other REQUIRED faces) - face - {S(held)} "
                                           f"(D-1F-09 HELD face, line at its low end); face = {S(vlo)} .. {S(vhi)} m3 "
                                           f"/ {S(t)} = {S(flo)} .. {S(fhi)} m2 -> base {S(b_lo)} .. {S(b_hi)} m2 x "
                                           f"{rate} = {S(lo)} .. {S(hi)}",
                                   "was": f"RELEASED {S(old)} (T-615, face 0.32 m2)",
                                   "envelope_with_D_1F_09": f"{S(lo)} .. "
                                                            f"{S(q6((b_hi + held) * (M19.UNITS_PER_M2 if what == 'units' else M19.PANEL_015)))}",
                                   "rule": "R-T654-1 (c)"}))
        calc[what] = {"line_id": lid, "was": S(old), "bound": [S(lo), S(hi)], "delta": [S(lo - old), S(hi - old)]}
    calc["face_m2"] = [S(flo), S(fhi)]
    calc["base_m2"] = [S(b_lo), S(b_hi)]
    return out, calc


# ---- conflicts: origin labels moved by the base move ----------------------------------------------------------------

def rulings_v20(conflicts, conflicts19, stage):
    """R-T654-1 (b): a group that now mixes CANDIDATE (merged restated lines) with the T-563 package (the FR-T617-1 rows
    chained after them) was one writer in V19 (the T-563 package wrote every restated line): explained."""
    was = {(c["family"], c["host"], c["unit"]): c for c in conflicts19}
    out = []
    for c in conflicts:
        if c["status"] != "UNEXPLAINED":
            continue
        k = (c["family"], c["host"], c["unit"])
        then = {P563 if x == "CANDIDATE" else x for x in c["sources"]}
        prev = was.get(k)
        same_then = (prev is None and len(then) == 1) or (prev is not None and prev["status"] == "EXPLAINED"
                                                          and set(prev["sources"]) == then)
        cand = [l for l in c["lines"] if l in stage]
        if "CANDIDATE" in c["sources"] and same_then and cand and set(c["sources"]) <= {"CANDIDATE", P563}:
            out.append({"layer": c["family"], "host_re": "^" + __import__("re").escape(c["host"]) + "$",
                        "sources": c["sources"],
                        "ruling": f"R-T654-1 (b): {len(cand)} merged V3.0.61 line(s) and the FR-T617-1 rows T-563 "
                                  "chains after them on this host: "
                                  + ("one source in V19" if prev is None else f"explained in V19 ({prev['ruling']})")
                                  + "; the restatement is now the candidate's own; no line counted twice",
                        "fix_row": "R-T654-1 (b)"})
    return out


# ---- overlay --------------------------------------------------------------------------------------------------------

def overlay_v20():
    """(base61, order20, rul20, after20, rep20, after19, rep19, rows, outs, src)."""
    pins()
    src = {k: _json(IN[k]) for k in ("INDEX59", "T563", "T498", "T650")}
    base59, order19, rul19, after19, rep19, after18, rep18, rows19, outs19, src19 = M19.overlay_v19()
    idx59 = {l["line_id"]: l for l in src["INDEX59"]["lines"]}
    if set(idx59) != set(base59) or any(
            any(idx59[k].get(f) != base59[k].get(f) for f in ("item_code", "unit", "element_id", *OV.QFIELDS))
            for k in base59):
        raise ManifestError("the V19 base is not the merged T-651 V3.0.59 line index")
    text60 = text_only_60(base59)
    if len(text60) != TEXT_ONLY_60:
        raise ManifestError(f"V3.0.60: {len(text60)} lines (the merged chain names {TEXT_ONLY_60} text-only)")
    stage = stage_61(base59, src["T563"])
    base = base_v3061(base59, stage)
    t59, t61 = OV.totals(base59), OV.totals(base)
    dt_base = OV.diff_totals(t59, t61)
    want = src["T563"]["totals_moved_by_code"]["FIN.PLASTER|m2"]["v3_0_61"]
    if sorted(dt_base) != ["FIN.PLASTER|m2"] or D(t61["FIN.PLASTER|m2"]["released"]) != D(str(want["released"])) or \
            D(t61["FIN.PLASTER|m2"]["held_low"]) != D(str(want["held_low"])) or \
            D(t61["FIN.PLASTER|m2"]["held_high"]) != D(str(want["held_high"])):
        raise ManifestError(f"the V3.0.61 base totals {dt_base} are not the merged summary's")
    set_aside = [x["line_id"] for x in I423.build()["set_aside"]]
    order_a, removed423 = rebase_423(order19, base59, text60, set_aside)
    order_r, removed = rebase_563(order_a, stage)
    removed = removed423 + removed
    after_r, rep_r = OV.apply(base, order_r, rul19)
    if set(after_r) != set(after19) or any(after_r[k] != after19[k] for k in after19):
        raise ManifestError("the V19 overlay on the V3.0.61 base is not byte-equal to V19 (R-T654-1 (b))")
    if any(r["status"] == "STALE" for r in rep_r["rows"]):
        raise ManifestError("a chained row went STALE on the V3.0.61 base")
    frows, fcalc = f_t652_1_rows(src["T498"], src["T650"], after19, order_r)
    M9.validate_rows(frows)
    order20 = M15.chain_into(order_r, P498, frows)
    _, rep0 = OV.apply(base, order20, rul19)
    rul20 = list(rul19) + rulings_v20(rep0["conflicts"], rep19["conflicts"], stage)
    after20, rep20 = OV.apply(base, order20, rul20)
    outs = {"stage": stage, "removed": removed, "text60": text60, "set_aside_60": set_aside, "rep_rebased": rep_r, "f_t652_1": fcalc,
            "rulings_v20": rul20[len(rul19):], "base_totals_moved": dt_base, "base59": base59}
    return base, order20, rul20, after20, rep20, after19, rep19, {"f_t652_1": frows}, outs, dict(src19, **src)


def build():
    base, order20, rul, after20, rep, after19, rep19, rows, outs, src = overlay_v20()
    allrows = [r for v in rows.values() for r in v]
    v20_lines = {r["line_id"] for r in allrows}
    others = sorted(k for k in set(after19) | set(after20) if k not in v20_lines and after19.get(k) != after20.get(k))
    if others:
        raise ManifestError(f"lines V20 does not write changed: {others[:5]}")
    t19, t20 = OV.totals(after19), OV.totals(after20)
    dt = OV.diff_totals(t19, t20)
    writes = sorted({f"{after19[l]['item_code']}|{after19[l].get('unit')}" for l in v20_lines})
    if sorted(dt) != writes:
        raise ManifestError(f"totals moved on {sorted(dt)}, V20 writes {writes}")
    if any(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]):
        raise ManifestError(f"unexplained conflicts after V20: "
                            f"{[c for c in rep['conflicts'] if c['status'] == 'UNEXPLAINED'][:2]}")
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    if any(r["op_id"] in {x["op_id"] for x in allrows} for r in flagged):
        raise ManifestError("a V20 row is not APPLIED")
    if len(flagged) != len([r for r in rep19["rows"] if r["status"] != "APPLIED"]):
        raise ManifestError("the flagged rows of V19 changed")
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    stage = outs["stage"]
    restated = []
    for lid, s in sorted(stage.items(), key=lambda kv: kv[1]["room"]):
        restated.append({"room": s["room"], "line_id": lid, "v3_0_60": _qstate(s["before"]),
                         "v3_0_61": _qstate(s["after"]), "after_v19_overlay": _qstate(after19[lid]),
                         "after_v20_overlay": _qstate(after20[lid]),
                         "overlay_row_after_merge": next((op["op_id"] for _, ops in order20 for op in ops
                                                          if op["line_id"] == lid and op["kind"] == "SET"), None)})
    table = []
    for r in allrows:
        table.append({"row": r["row"], "package": r["package"], "kind": r["kind"], "line_id": r["line_id"],
                      "item": after19[r["line_id"]]["item_code"],
                      "before": {k: r["before"][k] for k in OV.QFIELDS},
                      "after": {k: r["after"][k] for k in OV.QFIELDS}, "evidence": r["evidence"]["status"]})
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-654", "candidate": CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "base_move": {
            "from": "ARCH_TAKEOFF_V3.0.59 (V19 base = the T-651 line index, asserted on every line)", "to": CANDIDATE,
            "v3_0_60_text_only": {"lines": len(outs["text60"]), "by_line": outs["text60"],
                                  "rule": "R-T654-1 (a): no class / net / held bound moves (asserted against the "
                                          "T-423 inputs' expect)"},
            "v3_0_60_set_aside_named": outs["set_aside_60"],
            "v3_0_61_restated": restated, "base_totals_moved": outs["base_totals_moved"],
            "overlay_rows_removed": outs["removed"], "overlay_rows_removed_n": len(outs["removed"]),
            "rule": "R-T654-1 (b): each removed row equal to its merged line; the V19 overlay re-applied on the V3.0.61 "
                    "base is byte-equal to V19 on every line; FR-T617-1 stays chained (not in the merged module)",
            "lines_after_rebased_v19": len(after19),
            "rebased_flagged_rows": sum(1 for r in outs["rep_rebased"]["rows"] if r["status"] != "APPLIED")},
        "f_t652_1": outs["f_t652_1"],
        "line_table": table,
        "rows": [dict(r) for r in allrows],
        "rulings_v20": outs["rulings_v20"],
        "totals": {k: {"v19": t19.get(k), "v20": t20.get(k)} for k in dt},
        "overlay": {
            "lines": {"base_v3_0_61": len(base), "after_v19": len(after19), "after_v20": len(after20)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order20],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "other_lines_changed_vs_v19_overlay": others,
            "v20_vs_v19_totals": dt,
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    return b
