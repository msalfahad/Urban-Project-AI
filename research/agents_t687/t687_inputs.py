"""T-687: URBAN_V3069_INPUTS_V1 from the Checker-merged plaster / paint ledgers (sha256-pinned; nothing typed by hand
except the five source records and the two owner-status labels the ledgers state in words):

  T-676 out/T676_PLASTER_PAINT_CENSUS.json  OP-009 reveal fix row (1.08 m2, Q-55 C) and the A-1F-01 cause correction
  T-680 out/T680_SHAFT_ROUND2.json          the six stair-shaft storey-band lines
  T-686 out/T686_ROUND3.json                the eight annex / stair-core lines
  T-690 out/T690_TILES_ROUND2.json          c_wet_band: the 18 wet-room bands above the ceiling (R-T690-1)

and the expected FIN.PLASTER / FIN.PAINT code totals, computed from the committed V3.0.68 line index (T-672) and the
entries, cross-checked against the T-686 'after_round3' code totals (which already hold T-680 and the T-676 OP-009 fix).

    python3 -I research/agents_t687/t687_inputs.py [--out <file>]       # prints counts and totals
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

R = "research"
FILES = {
    "T-676": (f"{R}/agents_t676/out/T676_PLASTER_PAINT_CENSUS.json",
              "400b024835a159ccd378c832ffa05d32555f73565c796fa1ceba17dd2cd5e808",
              "cffefa0c079915550e201cd598eb30bd476b64c6", "session_01E6cPneC95WJNrb9QgLWXnA"),
    "T-680": (f"{R}/agents_t680/out/T680_SHAFT_ROUND2.json",
              "3a5bfc11b9d4dac53dc59e68dd752ceda1b33f27cbcdd9ba8cc5f56c217d47ea",
              "707c624ea902767b9db4bdfc48b3646e76464201", "session_01E6cPne2m28nR3xpe7rBSKd"),
    "T-686": (f"{R}/agents_t686/out/T686_ROUND3.json",
              "f755ea4f6154e008c1a7f45ae58ad62abb5ca4171602e66c41f802f359e43a8d",
              "8a0fc1e18aaa89919320e1d483bd6c9b73418fea", "session_01E6cPnaTNm32Ep1YYmyxM8c"),
    "T-690": (f"{R}/agents_t690/out/T690_TILES_ROUND2.json",
              "764caabc39caada112e6ba570a5b36aa396a4f1548a6fe58a690162ab4ffb000",
              "adef31c5797ef74429c8dda08459f6a4c9ce22a0", "session_01E6cPnbu8b82qwGYJBemCMC"),
}
INDEX = (f"{R}/agents_t672/out/LINE_INDEX_V3_0_68.json", None)     # the committed V3.0.68 census (sha printed)
OP009, A1F01 = "L-f4175f9915208dc5f9f7", "L-64cb94b4b8dc2cb17608"
CODES = ("FIN.PLASTER", "FIN.PAINT")


def _load(task):
    rel, sha, _m, _c = FILES[task]
    raw = (ROOT / rel).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != sha:
        raise SystemExit(f"{rel}: sha256 {got[:8]} is not the merged {sha[:8]} (tampered or moved)")
    return json.loads(raw.decode("utf-8"))


def _f(x):
    return None if x is None else float(x)


def sources():
    return [{"task": t, "file": FILES[t][0], "sha256": FILES[t][1], "merge_commit": FILES[t][2],
             "checker_run": FILES[t][3]} for t in sorted(FILES)]


def restate_entries():
    t676, t680, t686 = _load("T-676"), _load("T-680"), _load("T-686")
    out = []
    for x in t680["lines"]:
        c = x["candidate"]
        out.append({"line_id": x["line_id"], "item_code": x["item_code"], "action": "BOUND",
                    "expect": {"class": "HELD", "low": _f(c[0]), "high": _f(c[1])},
                    "after": {"low": float(x["held_low"]), "high": float(x["held_high"])},
                    "basis": (f"stair shaft ST-01 {x['band']} band {x['finish']} (T-680 R-T680-1 W25 / W27 heads "
                              f"T-201, R-T680-2 pier returns {x['returns_lo_hi'][0]} .. {x['returns_lo_hi'][1]} m2 in "
                              f"this band; Q-72 full exposed height)"),
                    "status": {"status": "HELD", "basis": x["status"]},
                    "still_open": list(x["still_open"]), "source_tasks": ["T-680"]})
    for x in t686["lines"]:
        ops = ", ".join(o["id"] for o in x["openings"])
        out.append({"line_id": x["line_id"], "item_code": x["item_code"], "action": "BOUND",
                    "expect": {"class": "HELD", "low": None, "high": None},
                    "after": {"low": float(x["held_low"]), "high": float(x["held_high"])},
                    "basis": (f"{x['room']} face {x['length_m']} m x height {x['height_m'][0]} .. {x['height_m'][1]} "
                              f"m ({x['height_rule']}) - openings {ops}: gross {x['calc']['gross'][0]} .. "
                              f"{x['calc']['gross'][1]} - {x['calc']['deducted_at_low']} / "
                              f"{x['calc']['deducted_at_high']} (T-686)"),
                    "status": {"status": "HELD", "basis": x["status"]},
                    "still_open": [x["still_open"]], "source_tasks": ["T-686"],
                    "freelancer_beside": ({"gross_m2": x["freelancer_gross_m2"],
                                           "engine_gross_vs_freelancer_pct": x["engine_gross_vs_freelancer_pct"],
                                           "verdict": "RULE_DIFFERENCE (flat 3.60 m vs owner G1)"}
                                          if x.get("freelancer_gross_m2") else None)})
    ent = {e["line_id"]: e for e in t676["entries"]}
    o = ent[OP009]
    fx = o["fix"]
    out.append({"line_id": OP009, "item_code": o["item_code"], "action": "VALUE",
                "expect": {"class": "HELD", "low": float(o["held_low"]), "high": float(o["held_high"])},
                "after": {"value": float(fx["value"])},
                "basis": f"OP-009 door reveal: {fx['note']} (T-676 own DXF read, Checker own re-measure AGREE)",
                "status": {"status": fx["status"], "source": fx["owner_ref"],
                           "basis": "; ".join(f"{k} {v[0]} ({v[1]})" for k, v in sorted(fx["terms"].items()))},
                "source_tasks": ["T-676"]})
    a = ent[A1F01]
    out.append({"line_id": A1F01, "item_code": a["item_code"], "action": "CAUSE",
                "expect": {"class": "HELD", "low": None, "high": None}, "after": {},
                "basis": "arch A-1F-01 reveal (T-676 cause correction, Checker own read of the 1F arch block AGREE)",
                "status": {"status": "HELD", "basis": f"DESIGNER ITEM {a['designer_ref']}: spring / rise not printed"},
                "corrected_cause": a["also"], "source_tasks": ["T-676"]})
    return out


def band_entries():
    c = _load("T-690")["c_wet_band"]
    out = []
    for r in c["rooms"]:
        lo, hi = float(r["band_low_m2"]), float(r["band_high_m2"])
        st = r["status"]
        if st.startswith("ASSUMED - OWNER-APPROVED"):
            if lo != hi:
                raise SystemExit(f"{r['engine_room']}: an owner-approved band is a point")
            status = {"status": "ASSUMED - OWNER-APPROVED", "source": "Q-48 A (tile top H = finished ceiling)",
                      "basis": st}
        else:
            status = {"status": "HELD", "basis": st}
        e = {"engine_room": r["engine_room"], "room": r["room"], "face_length_m": float(r["face_length_m"]),
             "low": lo, "high": hi, "status": status, "openings_in_band": list(r["openings_in_band"]),
             "source_tasks": ["T-690"],
             "still_open": None if status["status"] != "HELD" else st}
        if "S_floor_m" in r:
            e.update(backing_line_id=r["in_no_line_now"]["backing_plaster"], H_m=float(r["H_m"]),
                     S_floor_m=float(r["S_floor_m"]), S_roof_m=[float(x) for x in r["S_roof_m"]] if r["S_roof_m"]
                     else None, under_roof_share=float(r["under_roof_share"]),
                     deducted_m2=[float(x) for x in r["deducted_m2"]])
        else:
            e.update(backing_line_id=r["t686_line_below_H"]["line_id"], H_m=[float(x) for x in r["H_m"]],
                     S_m=[float(x) for x in r["S_m"]], gross_m2=[float(x) for x in r["gross_m2"]],
                     joint_total_m2=[float(x) for x in r["joint_total_plaster_to_S_m2"]])
        out.append(e)
    tot = (round(sum(e["low"] for e in out), 6), round(sum(e["high"] for e in out), 6))
    if abs(tot[0] - float(c["total_low_m2"])) > 1e-6 or abs(tot[1] - float(c["total_high_m2"])) > 1e-6:
        raise SystemExit(f"band totals {tot} are not the T-690 totals {c['total_low_m2']} .. {c['total_high_m2']}")
    return out


def expect_totals(restate, bands):
    """the code totals the run must give: the V3.0.68 index totals + the entries (index classes: RELEASED value,
    HELD bounded / blank; EXCLUDED outside), cross-checked with T-686 after_round3."""
    idx = json.loads((ROOT / INDEX[0]).read_text(encoding="utf-8"))["lines"]
    rs = {e["line_id"]: e for e in restate}
    tot = {}
    for x in idx:
        if x["item_code"] not in CODES or x["class"] == "EXCLUDED":
            continue
        z = tot.setdefault(f"{x['item_code']}|m2", {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0,
                                                     "bounded_lines": 0, "blocked_lines": 0})
        z["lines"] += 1
        e = rs.get(x["line_id"])
        lo, hi, val = x["held_low"], x["held_high"], x["measured_net"] if x["class"] == "RELEASED" else None
        if e:
            if e["action"] == "BOUND":
                lo, hi, val = e["after"]["low"], e["after"]["high"], None
            elif e["action"] == "VALUE":
                lo, hi, val = None, None, e["after"]["value"]
        if val is not None:
            z["released"] += val
        elif lo is not None:
            z["held_low"] += lo
            z["held_high"] += hi
            z["bounded_lines"] += 1
        else:
            z["blocked_lines"] += 1
    p = tot["FIN.PLASTER|m2"]
    for b in bands:
        p["lines"] += 1
        if b["status"]["status"] != "HELD":
            p["released"] += b["low"]
        else:
            p["held_low"] += b["low"]
            p["held_high"] += b["high"]
            p["bounded_lines"] += 1
    out = {k: {f: round(v, 6) if isinstance(v, float) else v for f, v in z.items()} for k, z in tot.items()}
    r3 = _load("T-686")["code_totals_m2"]
    for code in CODES:
        a = r3[code]["after_round3"]
        z = out[f"{code}|m2"]
        nb = [b for b in bands if b["status"]["status"] == "HELD"] if code == "FIN.PLASTER" else []
        opv = rs[OP009]["after"]["value"] if code == "FIN.PLASTER" else 0.0
        oph = opv                    # T-686 after_round3 already holds OP-009 at its fixed 1.08 at both ends
        want_lo = float(a["low"]) - opv + sum(b["low"] for b in nb)
        want_hi = float(a["high"]) - oph + sum(b["high"] for b in nb)
        if abs(z["held_low"] - want_lo) > 1e-5 or abs(z["held_high"] - want_hi) > 1e-5 or \
                z["blocked_lines"] != a["blank"]:
            raise SystemExit(f"{code}: expected totals {z} disagree with T-686 after_round3 {a} + bands / OP-009")
    return out


def build():
    restate, bands = restate_entries(), band_entries()
    return {"schema": "URBAN_V3069_INPUTS_V1", "project_id": None, "sources": sources(), "restate": restate,
            "bands": bands, "expect_totals": expect_totals(restate, bands),
            "index_sha256": hashlib.sha256((ROOT / INDEX[0]).read_bytes()).hexdigest()}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    doc = build()
    if "--out" in argv:
        Path(argv[argv.index("--out") + 1]).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    acts = {}
    for e in doc["restate"]:
        acts[e["action"]] = acts.get(e["action"], 0) + 1
    print("restate", acts, "bands", len(doc["bands"]), "owner-approved points",
          sum(1 for b in doc["bands"] if b["status"]["status"] != "HELD"), "held",
          sum(1 for b in doc["bands"] if b["status"]["status"] == "HELD"))
    print(json.dumps(doc["expect_totals"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
