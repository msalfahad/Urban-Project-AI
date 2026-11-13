"""T-673 census of the 49 HELD blank STR.CONC lines outside B10 in ARCH_TAKEOFF_V3.0.64 (44 STR.CONC.LINTEL, B9-02;
5 STR.CONC.STAIR, B7-12), one row each by cause, and the drawn quantity of every MEASURABLE NOW line (development villa).
Research only: nothing wired, nothing released (wiring is lane I).

Committed inputs only (no drawing is opened here; the own DXF read of this run is in READS below):
  candidate lines   research/agents_t668/out/LINE_INDEX_V3_0_64.json (V3.0.64, engine 0ed807c3)
  lintel ledger     research/agents_t453 (R-T453-4 through its own functions: merged fill states, T-449 pieces)
  drawn heads       research/agents_t201/HEADS_T201.csv (DRAWING-CONFIRMED, vector DWF / P7757.dxf), T-207 W11 / W12,
                    research/agents_t238 (W16 arched head: opening crown 3.000, band crown 3.101)
  payable form      research/agents_t650/out/T650_PAYABLE_FORM.json (R-T650-1: 60 / 60 RC cast, B, D, schedule row)
  jamb evidence     research/agents_t644/out/JAMB_EVIDENCE_T644.csv, research/agents_t544/out/EXTENDED_SEARCH_T544.csv
  stairs            research/agents_t258/LEDGER_T258.csv (pieces), research/agents_t266 (V3.0.18 split, remainders)

    python3 -I research/agents_t673/t673_alsenan.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t453"))
import t673_rules as R  # noqa: E402

RES = ROOT / "research"
INDEX = RES / "agents_t668" / "out" / "LINE_INDEX_V3_0_64.json"
HEADS = RES / "agents_t201" / "HEADS_T201.csv"
T650 = RES / "agents_t650" / "out" / "T650_PAYABLE_FORM.json"
JAMBS = RES / "agents_t644" / "out" / "JAMB_EVIDENCE_T644.csv"
EXT = RES / "agents_t544" / "out" / "EXTENDED_SEARCH_T544.csv"
STAIRS = RES / "agents_t258" / "LEDGER_T258.csv"
OUT = HERE / "out" / "T673_LEDGER.json"
OUT_MD = HERE / "out" / "T673_CENSUS.md"
BED = "0.06"     # R-T453-4 floor bed stand-in (owner Q-45 tile-bed maximum), unchanged

# Own reads this run (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha ab54dd55, decoded into
# .work/private only; local frame, m): NW ELEVATION, W16 jambs 2566 / 256A 1.5523 apart, +5.50 .. +7.661 (springing
# 2.161); highest layer-1 point over the opening 3.101 above +5.50 (band crown; T-238 opening crown 3.000); the next
# horizontal lines over W16 are layer-1 9.60 / 9.80 (facade band) and layer-5 10.16 / 10.595: plain facade between the
# crown and +9.60 (no member drawn on the elevation, the soffit is the T-449 piece 3.45).
READS = {"W16": {"head_lo": "3.000", "head_hi": "3.101", "tol": "0.001",
                 "basis": "own P7757.dxf NW frame read this run (band crown 3.101) + T-238 opening crown 3.000"}}
# W05: the drawn head is +3.50 absolute (T-201); the W.C. floor (+0.30 / +1.00) is not drawn, but the host run GF-W10
# pieces are on the GF main datum +1.00 (T-143), so head and soffit share one datum: 3.50 - 1.00 = 2.50. Sensitivity
# (datum +0.30, worst for the soffit) is asserted below to give the same decision.
W05_DATUM = {"head_level": "3.500", "host_datum": "1.00", "worst_datum": "0.30"}

DESIGNER = {
    "P-GF-01": ("DESIGNER ITEM", "D-45", "head drawn on no sheet (T-207 re-check); host GF-W14 HELD in the fill"),
    "L-GF-01": ("DESIGNER ITEM", "D-45 / register LIFT LANDING DOOR LINTEL",
                "lift landing door head not printed (shaft wall vs masonry, head vs soffit); host fill HELD"),
    "L-1F-01": ("DESIGNER ITEM", "D-45 / register LIFT LANDING DOOR LINTEL", "as L-GF-01"),
    "L-2F-01": ("DESIGNER ITEM", "D-45 / register LIFT LANDING DOOR LINTEL", "as L-GF-01"),
    "D-GF-09": ("DESIGNER ITEM", "D-GF-09 (T-581 DRAWING CONFLICT: D120 1.00 frame in a 0.90 gap)",
                "opening width conflict + IN_HELD_PIECE in the fill"),
    "W26": ("DESIGNER ITEM", "D-39 (2F roof datum / build-up)",
            "printed head 2.80 under the single 3.00 piece: margin 0.20 = D exactly, fails only with the 0.06 bed; "
            "the stair-roof structural top and build-up are D-39"),
}


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _csv(p):
    return list(csv.DictReader(Path(p).open(encoding="utf-8", newline="")))


def _f(v):
    return None if v is None else format(Decimal(str(v)).quantize(R.Q6), "f")


def held_lines():
    ix = _load(INDEX)
    assert ix["candidate_version"].endswith("3.0.64"), ix["candidate_version"]
    out = {"LINTEL": {}, "STAIR": {}, "released_lintels": {}}
    for ln in ix["lines"]:
        code = ln["item_code"]
        if code == "STR.CONC.LINTEL":
            oid = ln["element_id"].split(":", 1)[1]
            if ln["class"] == "HELD" and ln["measured_net"] is None and ln["held_low"] is None:
                out["LINTEL"][oid] = ln["line_id"]
            elif ln["class"] == "RELEASED":
                out["released_lintels"][oid] = ln["measured_net"]
        elif code == "STR.CONC.STAIR" and ln["class"] == "HELD" and ln["measured_net"] is None:
            out["STAIR"][ln["element_id"]] = ln["line_id"]
    return out


def t453_context():
    import t453_material_ledger as T
    import t279_inputs as L26
    walls = T.fill_walls(L26.build())
    reg = json.loads(T.REGISTER.read_text(encoding="utf-8"))
    rows, bearing = T.schedule_rows(_csv(T.SCHEDULE))
    ops = {o["opening_id"]: o for o in T.wall_openings(walls)}
    pieces = {}
    for e in reg["entries"]:
        if e.get("item_code") == "MAS.BLOCK":
            p = T.pieces((e.get("rule_result") or {}).get("formula"))
            if p:
                pieces[(e["floor"], e["element_id"])] = sorted({x[1] for x in p})
    census = {r["ID"]: r for r in _csv(T.OPENINGS)}
    return ops, pieces, census, rows, bearing


def drawn_head(oid, heads, census):
    """(head_lo, head_hi, tol, status, basis) above the host datum; printed census head governs a drawn one."""
    c = census.get(oid, {})
    if c.get("HEIGHT_STATUS") == "PRINTED" and c.get("HEIGHT_M") and c.get("SILL_M"):
        h = Decimal(c["HEIGHT_M"]) + Decimal(c["SILL_M"])
        return h, h, Decimal(0), "PRINTED", "census r3 printed head"
    if oid in READS:
        r = READS[oid]
        return Decimal(r["head_lo"]), Decimal(r["head_hi"]), Decimal(r["tol"]), "DRAWING-CONFIRMED", r["basis"]
    h = heads.get(oid)
    if not h or h["STATUS"] != "DRAWING-CONFIRMED":
        return None, None, None, None, "no printed or drawn head"
    import re
    m = re.search(r"max edge offset ([0-9.]+) m", h["ISSUE_CHECK"] or "")
    tol = Decimal(m.group(1)) if m else None
    if h["HEAD_ABOVE_FFL_M"]:
        hd = Decimal(h["HEAD_ABOVE_FFL_M"])
        return hd, hd, tol, "DRAWING-CONFIRMED", f"T-201 {h['VIEW']} drawn head (tol {tol})"
    if oid == "W05" and h["HEAD_LEVEL_M"] == W05_DATUM["head_level"]:
        hd = Decimal(h["HEAD_LEVEL_M"]) - Decimal(W05_DATUM["host_datum"])
        return hd, hd, tol, "DRAWING-CONFIRMED", "T-201 absolute head +3.50 on the host run datum +1.00 (T-143)"
    return None, None, None, None, "drawn head without a datum"


def lintels():
    held = held_lines()
    ops, pieces, census, rows, bearing = t453_context()
    assert abs(bearing - 0.40) < 1e-9
    heads = {r["ID"]: r for r in _csv(HEADS)}
    t650 = _load(T650)["per_opening"]
    jam = {}
    for r in _csv(JAMBS):
        jam.setdefault(r["opening_id"], []).append(r)
    ext = {(r["opening_id"], r["side"]): r for r in _csv(EXT)}
    exist = {}
    for oid in sorted(held["LINTEL"]):
        p = t650[oid]
        if p["state"] == "BOUNDED":         # T-650 bound, Checker-partial, unwired (A-1F-01, P-1F-01)
            exist[oid] = ("T650_BOUNDED", None, "R-T650-1 BOUNDED (both ends >= 0.40), unwired since T-650")
            continue
        o = ops[oid]
        lo, hi, tol, st, basis = drawn_head(oid, heads, census)
        cl = pieces.get((o["floor"], o["host"]))
        if o["fill_state"] != "DEDUCTED":
            c = census.get(oid, {})
            hb = (f"head {c.get('HEIGHT_M')} {c.get('HEIGHT_STATUS')}" if c.get("HEIGHT_M") else basis)
            exist[oid] = (R.HELD, None, f"host {o['host']} ({o['wall_status']}): opening {o['fill_state']} in the "
                                        f"merged fill, masonry above the head not established; {hb}")
            continue
        if lo is None:
            exist[oid] = (R.HELD, None, basis + "; " + (f"fill {o['fill_state']}" if o["fill_state"] != "DEDUCTED"
                                                         else "host pieces drawn"))
            continue
        if tol is None:
            tol = Decimal("0")
        state, spare, why = R.existence(head_lo=lo, head_hi=hi, tol=tol, fill_state=o["fill_state"],
                                        clear_heights=cl, d=p["D_m"], bed=BED, head_status=st)
        if oid == "W05" and state == R.REQUIRED:   # datum sensitivity: worst datum gives the same decision
            off = Decimal(W05_DATUM["host_datum"]) - Decimal(W05_DATUM["worst_datum"])
            s2, _, _ = R.existence(head_lo=lo, head_hi=hi, tol=tol, fill_state="DEDUCTED",
                                   clear_heights=[Decimal(str(c)) - off for c in cl], d=p["D_m"], bed=BED,
                                   head_status=st)
            assert s2 == R.REQUIRED, s2
        exist[oid] = (state, spare, f"{why}; head {lo}..{hi} ({basis}); pieces {cl}")
    # quantities for the REQUIRED ones (two passes for the pier conventions)
    req = [k for k, v in exist.items() if v[0] == R.REQUIRED]

    def mk(oid):
        p = t650[oid]
        ends = []
        for r in jam[oid]:
            e = {"side": r["side"], "a": r["v3_available_6dp_m"], "stopper": r["stopper"], "stopper_id": r["stopper_id"]}
            if r["stopper"] == "SEARCH_LIMIT" and (oid, r["side"]) in ext:
                x = ext[(oid, r["side"])]
                e.update(extended=x["available_6dp_m"], extended_stopper=x["stopper"])
            ends.append(e)
        return {"id": oid, "width_m": p["width_m"], "B": p["B_m"], "D": p["D_m"], "form": "STRAIGHT", "ends": ends}

    def nb_map(conv):
        m = {k: "RELEASED" for k in held["released_lintels"]}
        for k in held["LINTEL"]:
            m.setdefault(k, "HELD")
        m.update(conv)
        return m

    conv = {}
    for _ in range(3):
        res = {k: R.lintel_m3(mk(k), nb_map(conv)) for k in req}
        new = {k: v["convention"] for k, v in res.items()}
        if new == conv:
            break
        conv = new
    assert {k: v["convention"] for k, v in res.items()} == conv, "pier conventions not stable"
    piers = []
    done = set()
    for k, v in sorted(res.items()):
        for other in v["pier_shared_ceiling_with"]:
            key = tuple(sorted((k, other)))
            if key in done:
                continue
            done.add(key)
            pr = [r for r in jam[k] if r["stopper_id"] == other][0]
            piers.append({"pair": list(key), "pier_m": pr["v3_available_6dp_m"],
                          "lo_m3": "0.000000",
                          "hi_m3": _f(R.pier_remainder(pr["v3_available_6dp_m"], t650[k]["B_m"], t650[k]["D_m"])),
                          "why": "R-T673-3 / R-T544-1 (4): pier remainder p - 2 x 0.40, once in the family high"})
    return held, exist, res, piers, t650


def stairs(held):
    led = {r["id"]: r for r in _csv(STAIRS)}
    g = lambda i, k: led[i][k] or None  # noqa: E731
    rows = []
    spec = [
        ("P-C:SCOPE:STAIRS:GF:CC-7390ea1139:FLIGHTS", "ST-01 GF -> 1F remainder (MS1-L + MS1-T + turn slab)",
         ["ST01-MS1-L", "ST01-MS1-T", "ST01-MS1-T-SLAB"], "DESIGNER ITEM",
         "C-ST-4 / RFI-A04 (MS1-L: arch 10 fronts vs ST p.4 12; owner 2026-10-22 'MS1-L HELD'), D-67 / C-ST-3 (winder, "
         "turn soffit not drawn)", "designer answer on the MS1-L riser count and a winder / turn-slab detail"),
        ("HL:STAIR_CONCRETE:ST-01:MS2_TR", "ST-01 MS2 turn riser between the two half landings", ["ST01-MS2-TR"],
         "DESIGNER ITEM", "C-ST-3 (junction section of the two plates 0.168 apart not drawn)",
         "a section through the MS2 half-landing junction"),
        ("P-C:STAIRS:GROUND:SITE-4df8fcd99d130701", "ST-02 round stair remainder (12 curved treads, helicoid soffit, "
         "CA junction, 2CC)", ["ST02-RS-C", "ST02-RS-C-SOFFIT", "ST02-CA", "ST02-2CC"], "DESIGNER ITEM",
         "D-08 / owner Q-50 / Q-51 (curved parts HELD), C-ST-3; CA level not stated (0 .. 0.09)",
         "a section / detail of the curved flight"),
        ("DG5:ST-01:LOBBY", "ST-01b lobby D1 waist / support", ["ST01b-D1-WAIST"], "DESIGNER ITEM",
         "S-9 (waist thickness / support not printed)", "the D1 waist / support detail"),
    ]
    for eid, member, parts, cause, ref, fix in spec:
        lo = hi = Decimal(0)
        lo_open = hi_open = False
        for pid in parts:
            l, h = g(pid, "low_m3"), g(pid, "high_m3")
            if l is None:
                lo_open = True
            else:
                lo += Decimal(l)
            if h is None:
                hi_open = True
            else:
                hi += Decimal(h)
        lo_v = None if lo_open else lo
        hi_v = None if (hi_open or lo_open) else hi
        rows.append(dict(R.census_row(member=member, line_id=held["STAIR"][eid], cause=cause, cause_ref=ref, fix=fix,
                                      lo=lo_v, hi=hi_v), element_id=eid, parts=parts,
                         note=("bounded but not releasable: a CONFLICT / HELD component (owner: never label the "
                               "staircase system VERIFIED)") if lo_v is not None else "blank, never 0"))
    st3 = led["ST03-E1-STEPS"]
    assert st3["evidence"] == "DRAWING-CONFIRMED" and st3["value_m3"] == "0.355017"
    rows.append(dict(R.census_row(
        member="ST-03 entrance flight E1 (steps part measurable; waist HELD)",
        line_id=held["STAIR"]["P-C:SCOPE:STAIRS:GROUND:CC-5ab1872c70:FLIGHTS"], cause="MEASURABLE NOW",
        cause_ref="steps: T-258 ST03-E1-STEPS DRAWING-CONFIRMED (5 riser lines ST p.3 / arch GF / B-B); waist S-9; "
                  "riser 0.170 confirmation D-56 (beside)",
        fix="split like ST-01b (V3.0.18 D1 steps): a part line 0.355017 m3 DRAWING-CONFIRMED + the waist remainder blank",
        lo="0.355017", hi=None), element_id="P-C:SCOPE:STAIRS:GROUND:CC-5ab1872c70:FLIGHTS",
        parts=["ST03-E1-STEPS (0.355017)", "ST03-E1-WAIST (HELD)"],
        hand="5 x 1/2 x 0.30 x 0.17 x 2.80 = 0.357000 - arrival wedge in the ground-slab face 0.001983 (T-192) = 0.355017",
        note="the line stays HELD for the waist; the steps part is the new closable line (lane I)"))
    return rows


def build():
    held, exist, res, piers, t650 = lintels()
    rows = []
    for oid in sorted(held["LINTEL"]):
        lid = held["LINTEL"][oid]
        p = t650[oid]
        st, spare, why = exist[oid]
        member = f"lintel {oid} ({p['storey']}, {p['block_type']}, w {p['width_m']}, {p['schedule_rows'][0]} " \
                 f"{p['B_m']} x {p['D_m']})"
        if st == "T650_BOUNDED":
            rows.append(dict(R.census_row(member=member, line_id=lid, cause="MEASURABLE NOW",
                                          cause_ref="R-T650-1 BOUNDED (T-650 MERGED 2a2e28ca; Checker 07:06 arithmetic "
                                                    "AGREE, A-1F-01 width engine-read only)",
                                          fix="wire the T-650 bound (lane I, T-671 / V19)", lo=p["low_m3"],
                                          hi=p["high_m3"]), opening=oid, existence="REQUIRED (T-616)",
                             status="HELD bounded (lo = MIN-BEARING lower bound), never VERIFIED here"))
        elif st == R.REQUIRED:
            q = res[oid]
            rows.append(dict(R.census_row(member=member, line_id=lid, cause="MEASURABLE NOW",
                                          cause_ref="R-T673-1 existence on the merged drawn head (T-201 / T-238) + "
                                                    "R-T673-3 range on the T-644 jamb evidence",
                                          fix="wire (lane I) after the Checker's Gate A", lo=q["lo_m3"],
                                          hi=q["hi_m3"]), opening=oid, existence=f"REQUIRED (spare {spare} m)",
                             why=why, convention=q["convention"], ends=[
                                 {k: (str(v) if isinstance(v, Decimal) else v) for k, v in e.items()} for e in q["ends"]],
                             length_m=[_f(q["length_lo_m"]), _f(q["length_hi_m"])],
                             status="HELD bounded (existence DRAWING-CONFIRMED from a drawn head; quantity a range)"))
        else:
            o_why = why
            if oid in DESIGNER:
                cause, ref, fix = DESIGNER[oid]
                rows.append(dict(R.census_row(member=member, line_id=lid, cause=cause, cause_ref=ref, fix=fix),
                                 opening=oid, existence=st, why=o_why, status="HELD blank, never 0"))
            else:
                fill = "host masonry over the head not established in the merged fill"
                fixes = {
                    "W13": ("which 1F roof beam piece is over W13 (pieces 3.45 / 3.80 on 1F-W04): read it on the ST 1F "
                            "roof slab plan, then R-T673-1", "printed head 3.30: HELD_BY_NAME under the lower piece"),
                    "W11": ("sill datum (T-207: height 2.20 DRAWING-CONFIRMED, sill / head level HELD) and host GF-W18 "
                            "fill", "head level not established"),
                    "W12": ("as W11", "head level not established"),
                    "A-GF-01": ("host GF-W26 fill HELD; arch drawn not dimensioned (T-238 SOURCE-SUPPORTED pending "
                                "check)", "arched opening head"),
                }
                fx, extra = fixes.get(oid, (f"close the host wall in the fill (lane A blockwork closure); then "
                                            f"R-T673-1 on its head", fill))
                rows.append(dict(R.census_row(member=member, line_id=lid, cause="OPEN BOUND",
                                              cause_ref=extra, fix=fx), opening=oid, existence=st, why=o_why,
                                 status="HELD blank, never 0"))
    srows = stairs(held)
    meas = [r for r in rows if r["cause"] == "MEASURABLE NOW"]
    lo, hi = R.family_total([{"lo_m3": r["low_m3"], "hi_m3": r["high_m3"]} for r in meas] +
                            [{"lo_m3": "0", "hi_m3": p["hi_m3"]} for p in piers])
    by = {}
    for r in rows + srows:
        by[r["cause"]] = by.get(r["cause"], 0) + 1
    return {
        "task": "T-673", "candidate": "ARCH_TAKEOFF_V3.0.64", "rules": ["R-T673-1 1.0.0", "R-T673-2 1.0.0",
                                                                        "R-T673-3 1.0.0"],
        "count": {"lintel": len(rows), "stair": len(srows), "total": len(rows) + len(srows)},
        "by_cause": dict(sorted(by.items())),
        "lintels": rows, "pier_remainders": piers, "stairs": srows,
        "totals_m3": {
            "lintel_measurable_now": {"lines": len(meas), "low": _f(lo), "high": _f(hi),
                                      "of_which_new_by_R_T673_1": len(meas) - 2},
            "lintel_held_blank": {"lines": len(rows) - len(meas), "value": None,
                                  "note": "blank, never 0; at most 1 lintel each"},
            "stair_measurable_now_part": {"lines": 1, "low": "0.355017", "high": None},
            "stair_bounded_held": {"line": srows[0]["line_id"], "low": srows[0]["low_m3"], "high": srows[0]["high_m3"]},
            "stair_held_blank": {"lines": 3, "value": None},
        },
        "own_reads": READS, "w05_datum": W05_DATUM,
    }


def write_md(led):
    L = ["# T-673 census: the 49 HELD blank STR.CONC lines outside B10 (V3.0.64)", "",
         f"count: {led['count']} ; by cause: {led['by_cause']}", "",
         "| # | line | member | cause | low m3 | high m3 | reference / fix |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(led["lintels"] + led["stairs"], 1):
        L.append(f"| {i} | {r['line_id']} | {r['member']} | {r['cause']} | {r['low_m3'] or '-'} | "
                 f"{r['high_m3'] or ('OPEN' if r['low_m3'] else '-')} | {r['cause_ref']}; fix: {r['fix']} |")
    L += ["", "pier remainders (once in the family high): " + json.dumps(led["pier_remainders"]), "",
          "totals: " + json.dumps(led["totals_m3"]), ""]
    return "\n".join(L)


def main(argv):
    led = build()
    if "--write" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(led, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        OUT_MD.write_text(write_md(led), encoding="utf-8")
    print(json.dumps({"count": led["count"], "by_cause": led["by_cause"], "totals": led["totals_m3"]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
