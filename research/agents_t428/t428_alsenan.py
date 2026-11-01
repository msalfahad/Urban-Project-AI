"""T-428 Alsenan: CONCRETE RECONCILIATION ROLL-UP r4. The merged T-406 r3 roll-up (T-385 r2 on V3.0.29, + V3.0.33
moves; 47 components, 10 families) restated part by part with the Checker-MERGED traces of T-415 (ST-02), T-417 (ST-01
flight length and landing area), T-416 (GB-MAIN length term) and T-426 (GB-MAIN section term), with the engine-side
register of T-426 / T-416 and the QUEUED lane I correction T-430 printed only as a scenario (research only: no
quantity, line, state or released cell changes).

Inputs (all committed; no private file is needed: every restated component's parts are in the merged r3 summary):
  research/agents_t406/summary_t406.json       BASE (T-406 r3, MERGED 35c9212e)
  research/agents_t415/summary_t415.json       ST-02 residual terms                      (T-415 MERGED 8c8372a4)
  research/agents_t417/summary_t417.json       ST-01 length / landing terms              (T-417 MERGED 6b6ff9bd)
  research/agents_t416/summary_t416.json       GB-MAIN length term, band findings        (T-416 MERGED b7bb914a)
  research/agents_t391/summary_t391.json       GB-MAIN section groups                    (T-391 MERGED c3fe8ec8)
  research/agents_t426/CENSUS_T426.json        GB section census on V3.0.36              (T-426 MERGED 1f298735)
  research/agents_t400 / t246 / t420 summaries  V3.0.35 / .36 / .37 Gate B diffs (no valued concrete moved: asserted)
Every package figure is asserted against the Checker's OWN figure as written in its board verdict (CHECKER below),
within 1e-6 m3, before it is used; the class of every TRACED / HELD sub-part names that verdict (R-T428-4).

    python3 -I research/agents_t428/t428_alsenan.py [--write]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t428_rules as R  # noqa: E402

RES = HERE.parent

MERGED = {
    "T-391": "c3fe8ec8", "T-400": "0c5d526c", "T-406": "35c9212e", "T-415": "8c8372a4", "T-416": "b7bb914a",
    "T-417": "6b6ff9bd", "T-420": "4c01fe06", "T-246": "61b78fe8", "T-426": "1f298735",
}
QUEUED = {"T-430": "QUEUED", "T-432": "TODO", "T-433": "QUEUED"}

# The Checker's own figures, as written in the merged board verdicts (the reference; never the worker's number).
CHECKER = {
    "T-415": {"ref": "T-415 MERGED 8c8372a4, Verifier 2026-11-01T05:54Z, own read of ST7757 dxf.dxf by handle "
                     "(treads 4.443096 m2, lane 1.250) and own arithmetic (h)",
              "RS-LD": -0.162300, "RS-S": -0.065268, "RS-A": -0.026107, "RS-C": -1.244067, "BEYOND": -2.476433},
    "T-417": {"ref": "T-417 MERGED 6b6ff9bd, Verifier 2026-11-01T11:10Z, own re-measure by handle (runs 3.300, lane "
                     "1.200, landings) and own arithmetic: WHO IS RIGHT ENGINE_RIGHT",
              "RISE": -2.026752, "ONE_LENGTH": 0.010752, "OWNERSHIP": -0.0768, "COUNT": 0.2392},
    "T-416": {"ref": "T-416 MERGED b7bb914a, Verifier 2026-11-01T07:54Z, own read by handle (7DC+7DD / 7E7+7E8 7.350 "
                     "less neck 0.300 exactly, F-C-T416-1): (h) through-neck ENGINE_WRONG exact 0.108000; -3.525 "
                     "BOUNDED_THROUGH_SUPPORTS accepted as a bound; (f) HELD annex lines stay HELD",
              "THROUGH_NECK_EXACT": 0.108000, "BOUNDED": -3.525102},
    "T-426": {"ref": "T-426 MERGED 1f298735, Verifier 2026-11-01 11:59 UTC, own read of ST p.13 titles and of 7DC+7DD, "
                     "7E7+7E8, 177+7CD#1: unloaded halves ENGINE_WRONG 0.423 (2 x 0.2115, VERIFIED, freelancer also "
                     "at 0.60), loaded halves HELD D-33, D-34 lines and 177+7CD#1 HELD ranges, L-be6708e0 blank named",
              "UNLOADED": 0.423, "D34": (0.864171, 1.152231), "R177": (0.5964, 0.9036), "R177_STAKE": 0.3012, "SLIVER_VALUE": 0.009},
}
SECTION_M2 = 0.18          # the other side's one section 0.30 x 0.60 (T-391, T-416 s.5): m3 per m of length term
NECK_LINES = ("L-fe78ae283abfb6256358", "L-0e30aadba2eebc6c3ede")


def _j(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def P(cause, m3, verdict, **kw):
    return {"cause": cause, "m3": round(float(m3), 6), "verdict": verdict, **kw}


def close(a, b, what, tol=0.0000005):
    if abs(float(a) - float(b)) > tol:
        raise R.Refused(f"{what}: package {a} != Checker {b}")


def base():
    s = _j("agents_t406/summary_t406.json")
    rows = []
    for r in s["retraced_components"]:
        rows.append({"id": r["id"], "family": r["family_after"], "current": r["current"],
                     "parts": list(r["parts"]) + list(r["move_parts"])})
    for r in s["unchanged_components"]:
        rows.append({"id": r["id"], "family": r["family"], "current": None, "parts": []})
    return s, rows


def subtraces(rows):
    by = {r["id"]: r for r in rows}

    def find(cid, startswith, verdict):
        hit = [p for p in by[cid]["parts"] if p["cause"].startswith(startswith) and p["verdict"] == verdict]
        if len(hit) != 1:
            raise R.Refused(f"{cid}: {startswith!r} found {len(hit)} times")
        return hit[0]

    out = []
    # ---- ST-02 (T-415)
    c = CHECKER["T-415"]
    rec = _j("agents_t415/summary_t415.json")["derived"]["reconciliation"]
    t = {x["id"].split(" ")[0]: x for x in rec["terms"]}
    for k, kk in (("ST02-RS-LD", "RS-LD"), ("ST02-RS-S", "RS-S"), ("ST02-RS-A", "RS-A"), ("ST02-RS-C", "RS-C")):
        close(t[k]["m3"], c[kk], f"T-415 {k}")
    close(t["his"]["m3"], c["BEYOND"], "T-415 area beyond")
    p = find("SD-STAIR", "SD-ST02:", "UNRESOLVED")
    close(p["m3"], rec["residual"], "T-415 residual = r3 ST-02 part")
    out.append({"component": "SD-STAIR", "source": "T-415", "part_cause": p["cause"], "part_m3": p["m3"], "subparts": [
        P("ST-02 RS-LD flat landing plate T 16 vs his 'slab + steps' 0.28 (1.3525 m2 x -0.12)", t["ST02-RS-LD"]["m3"],
          "ENGINE_RIGHT", id="ST02-RS-LD-THK", verdict_ref=c["ref"]),
        P("ST-02 RS-S drawn 0.26187 m3 per m2 (T 16 waist x sec + R/2) vs his 0.28", t["ST02-RS-S"]["m3"],
          "ENGINE_RIGHT", id="ST02-RS-S-THK", verdict_ref=c["ref"]),
        P("ST-02 RS-A drawn 0.26187 m3 per m2 vs his 0.28", t["ST02-RS-A"]["m3"], "ENGINE_RIGHT",
          id="ST02-RS-A-THK", verdict_ref=c["ref"]),
        P("ST-02 RS-C curved flight at his 0.28 over the drawn plan 4.443096 m2: engine HELD (waist t not printed, "
          "RFI-S27; AT_LEAST 0.357035)", t["ST02-RS-C"]["m3"], "HELD", id="ST02-RS-C-HELD", verdict_ref=c["ref"]),
        P("ST-02 his 8.844404 m2 beyond the drawn 10.835596 m2 (his 16.4 m traces to no drawn length)",
          t["his"]["m3"], "UNRESOLVED", id="ST02-BEYOND", owner="T-432")]})
    # ---- ST-01 (T-417)
    c = CHECKER["T-417"]
    d = _j("agents_t417/summary_t417.json")["derived"]
    close(d["rise_in_length_m3"], c["RISE"], "T-417 rise")
    close(d["one_length_m3"], c["ONE_LENGTH"], "T-417 one length")
    p = find("SD-STAIR", "SD-ST01-FLIGHTS:", "UNTRACED")
    close(p["m3"], d["length_term_m3"], "T-417 length term = r3 part")
    out.append({"component": "SD-STAIR", "source": "T-417", "part_cause": p["cause"], "part_m3": p["m3"], "subparts": [
        P("ST-01 his flight length 5.300 = developed profile run 3.300 + rise: the rise laid as plan length under a "
          "'slab + steps' 0.28 (MS1-U 2.000, MS2-L / MS2-U 2.016 each)", d["rise_in_length_m3"], "ENGINE_RIGHT",
          id="ST01-RISE-IN-LENGTH", verdict_ref=c["ref"]),
        P("ST-01 his one length 5.300 on MS2-L / MS2-U whose own profile is 5.316", d["one_length_m3"], "ENGINE_RIGHT",
          id="ST01-ONE-LENGTH", verdict_ref=c["ref"])]})
    lt = d["landing_terms"]
    own = sum(x["m3"] for x in lt if x["term"] == "OWNERSHIP")
    cnt = sum(x["m3"] for x in lt if x["term"] == "COUNT")
    close(own, c["OWNERSHIP"], "T-417 landing ownership")
    close(cnt, c["COUNT"], "T-417 landing count")
    p = find("SD-STAIR", "SD-ST01-LANDINGS:", "UNTRACED")
    close(p["m3"], d["landing_area_term_m3"], "T-417 landing area = r3 part")
    out.append({"component": "SD-STAIR", "source": "T-417", "part_cause": p["cause"], "part_m3": p["m3"], "subparts": [
        P("ST-01 landings: his depth 1.400 = plate 1.200 + B3 'With Stair' band 0.200 owned by the beam line (2 x 1.2 "
          "x 0.2 x 0.16)", own, "ENGINE_RIGHT", id="ST01-LD-OWNERSHIP", verdict_ref=c["ref"]),
        P("ST-01 landing MS2-LD-W drawn plate 1.15 x 1.30 x 0.16 with no unit of his", cnt, "ENGINE_RIGHT",
          id="ST01-LD-COUNT", verdict_ref=c["ref"])]})
    # ---- GB-MAIN section term (T-391 groups, classes from T-426)
    c = CHECKER["T-426"]
    g = _j("agents_t391/summary_t391.json")["beams"]["groups"]
    ext = g["exterior main house, D printed by two levels (top +0.95 to N.G. +-0.00)"]["section_m3"]
    d40 = g["interior p.13 class D 0.40"]["section_m3"]
    d30 = g["interior p.13 class D 0.30"]["section_m3"]
    d60 = g["interior p.13 class D 0.60"]["section_m3"] + 0.0
    p = find("GB-MAIN", "section on the valued runs", "ENGINE_RIGHT")
    cen = _j("agents_t426/CENSUS_T426.json")
    close(cen["totals_by_verdict"]["NO_PRINTED_SECTION"]["value_m3"], c["SLIVER_VALUE"], "T-426 sliver value")
    close(cen["totals_by_verdict"]["DIFFERS"]["lo_m3"], 2 * c["UNLOADED"], "T-426 DIFFERS stake")
    out.append({"component": "GB-MAIN", "source": "T-426", "part_cause": p["cause"], "part_m3": p["m3"], "subparts": [
        P("GB exterior main runs: printed D 0.95 (two levels) vs his 0.60 (16 runs, 56.5168 m)", ext, "ENGINE_RIGHT",
          id="GB-SEC-EXT", verdict_ref=c["ref"] + "; T-391 c3fe8ec8"),
        P("GB interior runs printed class 30 x 40 vs his 0.60 (17 runs, 57.3969 m; 4 short runs at the 0.40 end of "
          "the unanswered D-34 pair, engine-side register E-3)", d40, "ENGINE_RIGHT", id="GB-SEC-40",
          verdict_ref=c["ref"] + "; T-391 c3fe8ec8"),
        P("GB annex-arc sliver L-be6708e0 (0.10 m) valued at 0.30: no printed section (T-426 NO_PRINTED_SECTION)",
          d30, "UNRESOLVED", id="GB-SEC-SLIVER", owner="T-430"),
        P("GB interior runs at 0.60 where engine and other side agree (4 runs, 26.44 m): 0.000 in the comparison, "
          "but two runs are wrong on both sides (engine-side register E-1 / E-2 / E-4)", d60, "AGREE",
          id="GB-SEC-60", verdict_ref=c["ref"])]})
    # ---- GB-MAIN length term (T-416)
    c = CHECKER["T-416"]
    s = _j("agents_t416/summary_t416.json")
    lt = s["length_term"]
    close(lt["terms_m3"]["other_bounded_through_supports_m3"], c["BOUNDED"], "T-416 bounded")
    f = {x["band"]: x["engine_length_minus_net_m"] for x in s["engine_findings"]}
    neck_m = f["7DC+7DD"] + f["7E7+7E8"]
    held_m = f["F8+7D4"] + f["137+138"] + f["136+7D5"]
    field_m = f["FD+7E0"] + f["107+7CE"] + f["ARC:157+158"]
    sliver_m = f["ARC:139+13A"]
    small_m = f["13D+7D2"] + f["17E+17F"]
    beyond = lt["terms_m3"]["engine_beyond_net_m3"]
    named = SECTION_M2 * (neck_m + held_m + field_m + sliver_m + small_m)
    buffer_m3 = beyond - named - (c["THROUGH_NECK_EXACT"] - SECTION_M2 * neck_m)
    p = find("GB-MAIN", "length basis:", "UNTRACED")
    close(p["m3"], lt["length_term_m3"], "T-416 length term = r3 part")
    out.append({"component": "GB-MAIN", "source": "T-416", "part_cause": p["cause"], "part_m3": p["m3"], "subparts": [
        P("GB his lumps run through the necks / crossing squares the engine bills in the neck lines (19.584 m beyond "
          "the drawn net, inside the 34.526 m drawn allowance)", lt["terms_m3"]["other_bounded_through_supports_m3"],
          "BOUNDED_THROUGH_SUPPORTS", id="GB-LEN-BOUNDED", verdict_ref=c["ref"],
          allowance_m=lt["through_support_allowance_m"], used_m=lt["other_beyond_net_m"]),
        P("GB valued lines L-fe78ae28 / L-0e30aadb run through the founded necks 7F5 / 7ED (2 x 0.300 m x 0.30 x "
          "0.60, exact cut)", c["THROUGH_NECK_EXACT"], "ENGINE_WRONG", id="GB-LEN-NECK", verdict_ref=c["ref"],
          correction_owner="T-430"),
        P("GB HELD annex lines F8+7D4 / 137+138 / 136+7D5: length fields run through their necks (1.533 m at his "
          "section; the held part is that much smaller)", SECTION_M2 * held_m, "HELD", id="GB-LEN-HELDFIELD",
          verdict_ref=c["ref"]),
        P("GB valued lines FD+7E0 / 107+7CE / ring L-7076482d: length field beyond the net while the value is the "
          "net or inside the frame range (0.760 m; the length term is on length fields)", SECTION_M2 * field_m,
          "UNRESOLVED", id="GB-LEN-FIELD", owner="T-430"),
        P("GB annex-arc sliver L-be6708e0 0.10 m beside neck 211, no drawn band", SECTION_M2 * sliver_m, "UNRESOLVED",
          id="GB-LEN-SLIVER", owner="T-430"),
        P("GB junction kept in the other band (13D+7D2) and oblique end (17E+17F)", SECTION_M2 * small_m,
          "UNRESOLVED", id="GB-LEN-SMALL", owner="T-430"),
        P("GB support cuts read 1 mm long by the T-416 extractor buffer (F-C-T416-1) and rounding: the split between "
          "the engine-beyond-net and the bounded term, sum unchanged", buffer_m3, "UNRESOLVED", id="GB-LEN-BUFFER",
          owner="T-430")]})
    return out


def engine_side():
    c = CHECKER["T-426"]
    cen = _j("agents_t426/CENSUS_T426.json")
    ir = cen["totals_by_verdict"]["INSIDE_RANGE"]
    close(ir["value_m3"], c["D34"][1] + c["R177"][1], "T-426 INSIDE_RANGE value")
    # stake = how far above the drawn alternative the engine value sits: D-34 0.288057 (0.40 -> 0.30 on 9.6019 m;
    # the range ends 0.864171 .. 1.152231 differ by 0.288060 through their own rounding) + 177+7CD#1 0.3012 (0.06 x
    # 5.02; its range low 0.5964 is 4.97 x 0.30 x 0.40 at the column 1EC face, Checker 'AGREE')
    close(ir["hi_m3"], 0.288057 + c["R177_STAKE"], "T-426 INSIDE_RANGE stake")
    close(c["D34"][1] - c["D34"][0], 0.288057, "T-426 D-34 range width", tol=0.000005)
    return [
        {"id": "E-1", "kind": "VERIFIED_WRONG", "m3": c["UNLOADED"], "line_ids": list(NECK_LINES),
         "what": "unloaded 3.525 m halves at 0.60 where p.13 prints 30 x 40 (2 x 0.2115); the other side is at 0.60 "
                 "too, so the comparison shows 0.000 AGREE", "residual_effect_m3": 0.0, "verdict_ref": c["ref"],
         "correction_owner": "T-430"},
        {"id": "E-2", "kind": "HELD_RANGE", "range_m3": [0.846, 1.269], "line_ids": list(NECK_LINES),
         "what": "loaded halves (a beam lands on them; D-33 concentrated load): 30 x 40 .. 30 x 60 over 2 x 3.525 m, "
                 "valued today at the 0.60 end", "residual_effect_m3": 0.0, "verdict_ref": c["ref"],
         "correction_owner": "T-430"},
        {"id": "E-3", "kind": "HELD_RANGE", "range_m3": list(c["D34"]), "line_ids": ["4 short-run lines (T-426 census)"],
         "what": "runs under 2.5 m valued at the 0.40 end of the unanswered D-34 pair (F-T426-1: downgrade-only "
                 "extension of DG-a31a0d7e); the comparison term on them sits in GB-SEC-40 and would grow by up to "
                 "-0.288057 if D-34 gives 30 x 30", "residual_effect_m3": 0.0, "verdict_ref": c["ref"],
         "correction_owner": "T-430"},
        {"id": "E-4", "kind": "HELD_RANGE", "range_m3": list(c["R177"]), "line_ids": ["177+7CD#1 line (T-426 census)"],
         "what": "span 5.020 (band end) or 4.970 (column 1EC face): 30 x 60 .. 30 x 40, valued at the 0.60 end; in "
                 "GB-SEC-60 (0.000 AGREE)", "residual_effect_m3": 0.0, "verdict_ref": c["ref"],
         "correction_owner": "T-430"},
    ]


def candidate_notes():
    """V3.0.34 -> V3.0.37: read and asserted from the merged Gate B summaries; no valued concrete line moved."""
    s400 = _j("agents_t400/summary_t400.json")
    d = s400["identity"]["diff"]["vs_v3_0_34"]
    conc_added = [a for a in s400["added"] if a["item_code"].startswith("STR.CONC.")]
    conc_restated = [a for a in s400["restated"] if a["item_code"].startswith("STR.CONC.")]
    if d["CHANGED"] != 1 or len(conc_restated) != 1 or conc_restated[0]["quantity"] is not None:
        raise R.Refused("V3.0.35 changed a valued concrete line: a candidate move must be stated")
    if any(a["quantity"] not in (None, 0) and a["state"] not in ("BLOCKED_RFI",) for a in conc_added):
        raise R.Refused("V3.0.35 added a valued concrete line")
    s246 = _j("agents_t246/summary_t246.json")
    if s246["quantity_moved"] != 0:
        raise R.Refused("V3.0.36 moved a quantity")
    s420 = _j("agents_t420/summary_t420.json")
    if s420["diff"]["vs_v3_0_36"].get("CHANGED", 0) or any(
            k.startswith("STR.CONC.") for k in s420["totals_moved_by_code"]):
        raise R.Refused("V3.0.37 moved a concrete line")
    return {
        "V3.0.34 -> V3.0.35 (T-400, 0c5d526c)":
            f"CHANGED {d['CHANGED']} = {conc_restated[0]['line_id']} upper boundary G.B blank -> blank with range "
            f"{conc_restated[0]['range']} m3 (already HELD in GB-BOUNDARY, no residual move); ADDED "
            f"{len(conc_added)} concrete line {conc_added[0]['item_code']} BLANK (pad count not printed, 0.312 m3 per "
            "pad beside): new HELD scope on the engine side, no residual move (whether the other side bills pads "
            "is not readable from public data)",
        "V3.0.35 -> V3.0.36 (T-246, 61b78fe8)": "quantity_moved 0",
        "V3.0.36 -> V3.0.37 (T-420, 4c01fe06)":
            f"ADDED {s420['diff']['vs_v3_0_36']['ADDED']} FIN.FLOOR.BED lines, SAME {s420['diff']['vs_v3_0_36']['SAME']}"
            ", no concrete code moved: the r4 table holds on V3.0.37 (= V3.0.34 for valued concrete)"}


def scenarios(newparts):
    gb = newparts["GB-MAIN"]
    neck = [p for p in gb if p.get("id") == "GB-LEN-NECK"][0]
    a_moves = [
        {"removes": neck["cause"], "m3": -neck["m3"]},
        {"cause": "unloaded halves revalued 0.30 x 0.40 x 3.525 (2 x 0.2115 less) against his 0.60",
         "m3": -CHECKER["T-426"]["UNLOADED"], "verdict": "ENGINE_RIGHT"},
        {"cause": "loaded halves 2 x 0.30 x 0.60 x 3.525 withdrawn from valued into the D-33 held range",
         "m3": -1.269, "verdict": "HELD"}]
    b_moves = a_moves + [
        {"cause": "177+7CD#1 withdrawn into its held range 0.5964 .. 0.9036", "m3": -CHECKER["T-426"]["R177"][1],
         "verdict": "HELD"},
        {"cause": "L-be6708e0 withdrawn to a blank line (no printed section)", "m3": -CHECKER["T-426"]["SLIVER_VALUE"],
         "verdict": "HELD"},
        {"cause": "4 short-run D-34 lines withdrawn into the held range 0.864171 .. 1.152231 (downgrade-only "
                  "extension, Checker validation)", "m3": -CHECKER["T-426"]["D34"][1], "verdict": "HELD"}]
    a = R.scenario(gb, a_moves, "T-430", MERGED, QUEUED["T-430"])
    b = R.scenario(gb, b_moves, "T-430", MERGED, QUEUED["T-430"])
    for x in (a, b):
        x.pop("parts_after")
    a["scope"] = "T-426 s.6 (1) as T-426 states it (two neck lines split; -1.800 m3 on the valued side)"
    b["scope"] = ("the whole T-430 row (s.6 (1) + 177+7CD#1 range + L-be6708e0 blank + F-T426-1 downgrade); the "
                  "classes of the terms already on the withdrawn lines (GB-SEC-40 share of the 4 D-34 runs, "
                  "GB-SEC-60 share of 177+7CD#1, GB-SEC-SLIVER, GB-LEN-SLIVER) are not re-bound here (the other "
                  "side's per-run section is not separable from his two lumps)")
    a["t391_basis_held_term_after"] = round(-9.690354 - 1.269, 6)
    return {"A": a, "B": b}


def observation_length_fields():
    """O-T428-1 (a proposal for the Checker; no figure of the table moves): the GB-LEN-FIELD part is mostly a
    decomposition pair. T-391's section term is (valued m3) - his 0.18 x the LENGTH FIELDS of the valued lines, its
    length term 0.18 x (all length fields - his length); on three valued exterior lines the value rests on a shorter
    VALUE length (value / (b x D)), so those metres appear +0.18 x m in the length term and -0.18 x m in the section
    term: no physical difference. The rest is the value length beyond the GB-plan net."""
    cen = {}
    for l in _j("agents_t426/CENSUS_T426.json")["lines"]:
        if l["state"] == "VALUED" and l["drawn_band"] in ("FD+7E0", "107+7CE", "ARC:157+158"):
            if l["drawn_band"] in cen:
                raise R.Refused(f"O-T428-1: band {l['drawn_band']} carries two valued lines")
            cen[l["drawn_band"]] = l
    bands = {b["band"]: b for b in _j("agents_t416/summary_t416.json")["bands"]}
    rows = []
    for b in ("FD+7E0", "107+7CE", "ARC:157+158"):
        l = cen[b]
        vlen = l["candidate_value_m3"] / (l["candidate_b_m"] * l["candidate_D_m"])
        net = bands[b]["net_by_frame_m"]
        rows.append({"band": b, "line_id": l["line_id"], "length_field_m": l["candidate_L_m"],
                     "value_length_m": round(vlen, 6), "net_gbp_m": net["GBP"],
                     "net_frame_range_m": [min(net[k] for k in ("GBP", "FP", "CAP")),
                                           max(net[k] for k in ("GBP", "FP", "CAP"))],
                     "field_minus_value_m": round(l["candidate_L_m"] - vlen, 6),
                     "value_minus_net_m": round(vlen - net["GBP"], 6)})
    # the identity the pair rests on, asserted on merged figures: exterior section + plan (T-391 group) = the valued
    # exterior m3 - 0.18 x their length fields (T-426 census V3.0.36)
    ext = [l for l in _j("agents_t426/CENSUS_T426.json")["lines"] if l["state"] == "VALUED" and l["candidate_D_m"] == 0.95]
    grp = _j("agents_t391/summary_t391.json")["beams"]["groups"][
        "exterior main house, D printed by two levels (top +0.95 to N.G. +-0.00)"]
    close(sum(l["candidate_value_m3"] for l in ext) - SECTION_M2 * sum(l["candidate_L_m"] for l in ext),
          grp["section_m3"] + grp["plan_m3"], "O-T428-1 exterior identity", tol=0.000002)
    close(sum(l["candidate_L_m"] for l in ext), grp["L_m"], "O-T428-1 exterior length fields", tol=0.00005)
    pair = round(SECTION_M2 * sum(r["field_minus_value_m"] for r in rows), 6)
    rest = round(SECTION_M2 * sum(r["value_minus_net_m"] for r in rows), 6)
    return {"id": "O-T428-1", "rows": rows, "pair_m3": pair, "value_beyond_gbp_net_m3": rest,
            "re_adds_to_GB_LEN_FIELD": round(pair + rest, 6),
            "proposal": f"Checker to rule: +{pair} m3 of GB-LEN-FIELD and -{pair} m3 inside GB-SEC-EXT are one "
                        "bookkeeping pair (AGREE, net 0: his section counted on length-field metres the engine value "
                        f"does not carry); the remaining +{rest} m3 is the value length beyond the GB-plan net, the "
                        "ring's share a point inside its frame range (R-T407: a range, never a chosen frame). If "
                        f"ruled, GB-MAIN unexplained +0.124182 -> {round(0.124182 - pair, 6)} and traced -1.064382 "
                        f"-> {round(-1.064382 + pair, 6)} (ENGINE_RIGHT exterior section +5.796522 -> "
                        f"{round(5.796522 + pair, 6)}); no residual moves"}


def build():
    s, rows = base()
    st = subtraces(rows)
    newparts, fams, tot = R.rollup(rows, s["families_current_v3_0_33"], st, MERGED, engine_side())
    comps = {cid: {"family": next(r["family"] for r in rows if r["id"] == cid), "parts": parts,
                   "split": R.subtotals(parts)} for cid, parts in newparts.items()}
    sc = scenarios(newparts)
    return s, comps, fams, tot, sc


def unexplained_list(s, comps):
    """Every unexplained part left, by element, with its owner task (none = a finding for the Lead)."""
    by_cause = {"stair-zone panel": "none: designer item F2 (whether a slab runs under the curved flight foot; RFI draft)",
                "his area beyond the whole drawn network": "none: a bare number with no drawn element",
                "engine vs own on the valued faces": "none"}
    owners = {"PL-WALLS": "none",
              "BM-GF": "none", "BM-1F": "none", "BM-2F": "none", "GB-BOUNDARY": "none", "BW-BAND": "none",
              "CL-1F": "designer item (C9 schedule vs drawn section)"}
    out = []
    for r in s["retraced_components"]:
        parts = comps[r["id"]]["parts"] if r["id"] in comps else list(r["parts"]) + list(r["move_parts"])
        for p in parts:
            if R.CLASS_OF[p["verdict"]] == "UNEXPLAINED":
                out.append({"component": r["id"], "family": r["family_after"], "cause": p["cause"],
                            "m3": round(p["m3"], 6), "owner": p.get("owner") or next(
                                (v for k, v in by_cause.items() if p["cause"].startswith(k)), owners.get(r["id"], "none"))})
    retr = {r["id"] for r in s["retraced_components"]}
    fam_unexp = {f: v["UNEXPLAINED"] for f, v in s["families_current_v3_0_33"].items()}
    for r in s["retraced_components"]:
        fam_unexp[r["family_after"]] -= r["current"]["UNEXPLAINED"]
    rest = {f: round(v, 6) for f, v in fam_unexp.items() if abs(v) > 0.0000005}
    if set(rest) != {"CONC.POOL"} or abs(rest["CONC.POOL"] + 0.471346) > 0.0000005:
        raise R.Refused(f"unchanged components carry unexplained other than PL-WALLS: {rest}")
    assert "PL-WALLS" not in retr
    out.append({"component": "PL-WALLS", "family": "CONC.POOL", "cause": "0.20 m of his wall height above the "
                "drawn rim + base, traced to no drawn level (T-385 r2, unchanged)", "m3": -0.471346, "owner": "none"})
    return sorted(out, key=lambda x: x["m3"])


def public_summary():
    s, comps, fams, tot, sc = build()
    r3 = s["totals"]["current"]
    ul = unexplained_list(s, comps)
    if abs(sum(u["m3"] for u in ul) - tot["UNEXPLAINED"]) > 0.000005:
        raise R.Refused("the unexplained list does not re-add to the table's unexplained total")
    return {"schema": "T428_SUMMARY_V1",
            "basis": "T-406 r3 (MERGED 35c9212e; T-385 r2 on V3.0.29 + V3.0.33 moves) restated part by part with the "
                     "merged T-415 / T-416 / T-417 / T-426 traces; holds on V3.0.37 (no valued concrete moved since "
                     "V3.0.34)",
            "merged_register": MERGED, "queued": QUEUED, "checker_figures": CHECKER,
            "totals_r3_current": {k: r3[k] for k in ("residual_m3", "TRACED", "HELD", "UNEXPLAINED")},
            "totals_r4_current": tot, "families_r4_current": fams, "restated_components": comps,
            "engine_side_register": engine_side(), "scenarios_gb_main_t430": sc,
            "observations": [observation_length_fields()],
            "candidate_notes": candidate_notes(), "unexplained_left": ul,
            "unexplained_by_sign": {"negative_m3": round(sum(u["m3"] for u in ul if u["m3"] < 0), 6),
                                    "positive_m3": round(sum(u["m3"] for u in ul if u["m3"] > 0), 6),
                                    "parts": len(ul)},
            "note": "engine-side figures, residual splits in m3 and Checker figures only; no freelancer row, cell or "
                    "dimension beyond the W x L x T quantities already in the merged records"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    pub = public_summary()
    if a.write:
        (HERE / "summary_t428.json").write_text(json.dumps(pub, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    return pub


if __name__ == "__main__":
    p = main()
    print(json.dumps(p["totals_r3_current"]), "\n", json.dumps(p["totals_r4_current"]))
    for f, v in p["families_r4_current"].items():
        print(f"  {f:24s} res {v['residual_m3']:+11.6f} traced {v['TRACED']:+11.6f} held {v['HELD']:+11.6f} "
              f"unexpl {v['UNEXPLAINED']:+11.6f} closes {v['cause_closes']}")
    for cid, c in p["restated_components"].items():
        print(cid, c["split"])
        for q in c["parts"]:
            print(f"    {q['m3']:+10.6f} {q['verdict']:24s} {q['cause'][:90]}")
    for k, v in p["scenarios_gb_main_t430"].items():
        print("scenario", k, v["as_is"]["residual_m3"], "->", v["after"])
    for u in p["unexplained_left"]:
        print(f"  UNEXPL {u['m3']:+10.6f} {u['component']:10s} {u['owner'][:30]:30s} {u['cause'][:70]}")
