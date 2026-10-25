"""T-290 Alsenan stairs and domes basis ledger (research, read-only).

    python3 -I research/agents_t290/t290_alsenan.py [--write]

Inputs (committed, no private data): the candidate digest CANDIDATE_V3015_STAIR_DOME_LINES.json (t290_extract.py on an
own V3.0.15 run, csv a4dc01dd = T-270 r2 Gate B), the engine-free piece inventory research/agents_t258/LEDGER_T258.csv
(MERGED b1b72a50, Checker Gate A r2), the soffit ledger research/agents_t281/LEDGER_T281.csv (MERGED 40518c58) and the
formwork r4 lines research/agents_t264/FORMWORK_LINES_R4.csv (MERGED 90203feb). The ST-03 line's basis row is the T-289
row (BASIS_LEDGER_T289.csv, READY): CITED here, never re-booked. Writes BASIS_LEDGER_T290.csv and summary.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import stair_dome_basis as B  # noqa: E402

T258 = ROOT / "research" / "agents_t258" / "LEDGER_T258.csv"
T281 = ROOT / "research" / "agents_t281" / "LEDGER_T281.csv"
T264 = ROOT / "research" / "agents_t264" / "FORMWORK_LINES_R4.csv"
CAND = HERE / "CANDIDATE_V3015_STAIR_DOME_LINES.json"

EVIDENCE = {"VERIFIED": B.VERIFIED, "DRAWING-CONFIRMED": B.DC, "ASSUMED — OWNER-APPROVED": B.AOA}

# Checker records behind the VERIFIED pieces and the owner rule behind the owner-approved ones (T-258 s.2, merged)
CHECKER = {
    "ST01-MS1-LD": "Checker 2026-10-22 17:18 (T-180 slot); T-258 Gate A r2 b1b72a50",
    "ST01-MS1-U": "Checker own 0.9976, D-CHK-T180-1 (rev2); T-258 Gate A r2 b1b72a50",
    "ST01-MS2-L": "Checker 2026-10-23 01:57 (T-192), T-187 Gate B 8a6d604a",
    "ST01-MS2-U": "T-187 Gate B 8a6d604a (Checker own)",
    "DOME-A-SHELL": "Checker 2026-10-22 18:15; V3.0.7 Gate B (T-193 e866328a)",
    "DOME-B-SHELL": "Checker 2026-10-22 18:15; V3.0.7 Gate B (T-193 e866328a)",
}
OWNER_RULE = "Q-50 A cond (round-stair riser 4.50 / 28); waist 'T 16' printed (T-287 G2-w); geometry Checker own 13:10"
DIMS = {
    B.VERIFIED: {"riser": "CHECKER", "going": "CHECKER", "width": "CHECKER", "waist": "PRINTED"},
    B.DC: {"riser": "PRINTED", "going": "PRINTED", "width": "PRINTED"},
    B.AOA: {"riser": "OWNER_RULE", "going": "PRINTED", "width": "PRINTED", "waist": "PRINTED"},
}
SHELL_DIMS = {"chord": "PRINTED", "rise": "PRINTED", "thickness": "PRINTED"}
CURVED = {"ST01-MS1-T": "WINDER", "ST01-MS1-T-SLAB": "WINDER", "ST02-RS-C": "CURVED", "ST02-RS-C-SOFFIT": "CURVED"}
ITEM_FIX = {"ST01-MS1-L": "C-ST-4 (designer; owner 2026-10-22 18:00 (4))", "ST01-MS1-T": "C-ST-3 / G2-a",
            "ST01-MS1-T-SLAB": "C-ST-3 / G2-a", "ST01-MS2-TR": "C-ST-3 / G2-c", "ST01b-D1-WAIST": "G2-w (D1)",
            "ST03-E1-WAIST": "G2-w (E1); S-9", "ST02-RS-C": "Q-50 / Q-51; G2-w (RS-C)",
            "ST02-RS-C-SOFFIT": "Q-51 step 5, C-ST-3", "ST02-CA": "CA level not stated (T-184)",
            "ST02-2CC": "layer-5 pair 2CC / 2CD, no mark (designer)", "DOME-A-DRUM": "G3-b (drum material / thickness)",
            "DOME-B-DRUM": "G3-b (drum material / thickness)", "DOME-3-SHELL": "G3-a / D-21 (tower dome)"}

# one owner per soffit / formwork row: T-281 ids and T-264 r4 'item' texts, given to the concrete piece they face
SOFFIT = {"ST01-MS1-L": ["ST01-MS1-L"], "ST01-MS1-T-SLAB": ["ST01-MS1-T"], "ST01-MS1-LD": ["ST01-MS1-LD"],
          "ST01-MS1-U": ["ST01-MS1-U"], "ST01-MS2-L": ["ST01-MS2-L", "ST01-MS2-L/head kink"],
          "ST01-MS2-LD-W": ["ST01-MS2-LD-W"], "ST01-MS2-LD-E": ["ST01-MS2-LD-E"], "ST01-MS2-TR": ["ST01-MS2-TR"],
          "ST01-MS2-U": ["ST01-MS2-U"], "ST02-RS-S": ["ST02-RS-S", "ST02-RS-S/head kink"],
          "ST02-RS-LD": ["ST02-RS-LD"], "ST02-RS-A": ["ST02-RS-A", "ST02-RS-A/head kink"],
          "ST02-RS-C-SOFFIT": ["ST02-RS-C"]}
FORM = {"ST01-MS1-L": ["MS1-L riser forms (10 x 1.20 x 0.1667)", "MS1-L waist soffit"],
        "ST01-MS1-T": ["MS1-T (turn (winders)) faces"],
        "ST01-MS1-T-SLAB": ["slab under the main-stair winders (warped soffit)"],
        "ST01-MS1-LD": ["MS1-LD landing soffit"],
        "ST01-MS1-U": ["MS1-U riser forms (12 x 1.20 x 0.1667)", "MS1-U waist soffit"],
        "ST01-MS2-L": ["MS2-L riser forms (12 x 1.20 x 0.1680)", "MS2-L waist soffit"],
        "ST01-MS2-LD-W": ["MS2-LD landing soffit"],
        "ST01-MS2-TR": ["MS2-TR (closing riser quarter -> NE la) faces"],
        "ST01-MS2-U": ["MS2-U riser forms (12 x 1.20 x 0.1680)", "MS2-U waist soffit"],
        "ST01b-D1-STEPS": ["D1 riser forms (4 x 1.20 x 0.175)"], "ST01b-D1-WAIST": ["D1 waist soffit"],
        "ST03-E1-STEPS": ["E1 riser forms (5 x 2.80 x 0.170)"], "ST03-E1-WAIST": ["E1 waist soffit"],
        "ST02-RS-C": ["RS-C (curved (12 tapered treads)) faces"],
        "ST02-RS-S": ["RS-S riser forms (11 x 1.20 x 0.1607)", "RS-S waist soffit"],
        "ST02-RS-LD": ["RS-LD landing soffit"],
        "ST02-RS-A": ["RS-A riser forms (5 x 1.25 x 0.1607)", "RS-A waist soffit"],
        "DOME-A-SHELL": ["DOME-A S0 approved design: shell soffit form (intrados 2 pi R_i h_i)",
                         "DOME-A S0 approved design: shell top (extrados) form"],
        "DOME-A-DRUM": ["DOME-A S0 approved design: drum faces (1.30 m)"],
        "DOME-B-SHELL": ["DOME-B S0 approved design: shell soffit form (intrados 2 pi R_i h_i)",
                         "DOME-B S0 approved design: shell top (extrados) form"],
        "DOME-B-DRUM": ["DOME-B S0 approved design: drum faces (1.30 m)"],
        "DOME-3-SHELL": ["DOME-TOWER S0 approved design: shell soffit form",
                         "DOME-TOWER S0 approved design: shell top (extrados) form",
                         "DOME-TOWER S0 approved design: support faces"]}

# the candidate's 14 lines -> the pieces each measures (engine ids from the digest; the binding is by guard element,
# element id and formula, never by row order)
BIND = {
    "L-7863355dfcb68a681d2d": ("ST-01 GF -> 1F flights, winder turn and half landing",
                               ["ST01-MS1-L", "ST01-MS1-T", "ST01-MS1-T-SLAB", "ST01-MS1-LD", "ST01-MS1-U"]),
    "L-67e4b0485135f84acc46": ("ST-01 MS2-L flight 1F -> half landing", ["ST01-MS2-L"]),
    "L-2416e65f053a14199cfc": ("ST-01 MS2-LD half landing, two plates +7.516 / +7.684", ["ST01-MS2-LD-W", "ST01-MS2-LD-E"]),
    "L-659243ed9fc2831c3ae8": ("ST-01 MS2-TR turn riser between the plates", ["ST01-MS2-TR"]),
    "L-bb0e57b1948175a3d5b8": ("ST-01 MS2-U flight half landing -> 2F", ["ST01-MS2-U"]),
    "L-821032bc04a0b0d02133": ("ST-01b lobby flight D1 +0.30 -> +1.00", ["ST01b-D1-STEPS", "ST01b-D1-WAIST"]),
    "L-b6b0354b7842f0ed6e41": ("ST-02 round reception stair GF +1.00 -> 1F +5.50",
                               ["ST02-RS-C", "ST02-RS-C-SOFFIT", "ST02-RS-S", "ST02-RS-LD", "ST02-RS-A", "ST02-CA",
                                "ST02-2CC"]),
    "L-061e18cf35a4b6b33d68": ("ST-03 entrance flight +0.15 -> +1.00", ["ST03-E1-STEPS", "ST03-E1-WAIST"]),
    "L-8ea34765d16b54898140": ("DOME-A terrace dome shell (S0)", ["DOME-A-SHELL"]),
    "L-fffa895ed96b9d6a682c": ("DOME-B terrace dome shell (S0)", ["DOME-B-SHELL"]),
    "L-d5401fa8986900c66c37": ("DOME-3 tower dome over the +13.90 roof", ["DOME-3-SHELL"]),
    "L-14f885e95132fa0cedec": ("retired: the 18 'tread' lines on SH04 are the ribs of a 4.42 m dome (T-193)", []),
    "L-33769fb181e11dca13cc": ("superseded: convention dome DOME-1, replaced by the verified shell line (T-185 / T-193)", []),
    "L-004e8e9fd032cb0aeb72": ("superseded: convention dome DOME-2, replaced by the verified shell line (T-185 / T-193)", []),
}
CITED = {"L-061e18cf35a4b6b33d68": ("T-289 BASIS_LEDGER_T289.csv (row ST03)", "S-9: ST-03 waist not printed (steps "
                                    "0.355017 m3 DRAWING-CONFIRMED component)")}
NAMED = {"STAIR": 2.983085, "DOME": 5.081362}     # released in the candidate (T-258 s.5, merged): line-id sums below
T266_LABEL_2915 = 2.915089                        # T-266 row text: the T-258 r1 sum of the same pieces


def _csv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def inventory():
    comps = []
    for r in _csv(T258):
        if r["cls"] == "BESIDE":                  # owner-method knees reported beside, never a piece of the line
            continue
        cid = r["id"]
        c = {"id": cid, "element": r["element"], "piece": r["part"], "kind": CURVED.get(cid, "PIECE"),
             "source_row": "LEDGER_T258 " + cid, "sheet": r["source"],
             "soffit_rows": SOFFIT.get(cid, []), "formwork_rows": FORM.get(cid, [])}
        if r["cls"] == "OWNED_ELSEWHERE":
            c.update(status=B.OWNED_ELSEWHERE, owner_line=r["owner_line"], value_m3=r["value_m3"] or None)
        elif r["cls"] == "CLOSABLE":
            st = EVIDENCE[r["evidence"]]
            c.update(status=st, value_m3=float(r["value_m3"]))
            if "SHELL" in cid:
                c.update(kind="SHELL", dims=SHELL_DIMS)
            else:
                c.update(dims=DIMS[st])
            if st == B.VERIFIED:
                c["checker"] = CHECKER[cid]
            if st == B.AOA:
                c["owner_rule"] = OWNER_RULE
        elif r["cls"] == "CONFLICT":
            c.update(status=B.CONFLICT, low_m3=float(r["low_m3"]), high_m3=float(r["high_m3"]),
                     held_item=ITEM_FIX.get(cid) or r["blocker"][:80])
        elif r["cls"] in ("HELD", "UNKNOWN"):
            c.update(status=B.HELD if r["cls"] == "HELD" else B.UNKNOWN, held_item=ITEM_FIX.get(cid) or r["blocker"][:80],
                     low_m3=r["low_m3"] or None, high_m3=r["high_m3"] or None)
        else:
            raise B.BasisError(f"{cid}: class {r['cls']} not mapped")
        comps.append(c)
    return comps


def check_owner_rows(comps):
    """every soffit / formwork row named exists in its merged ledger (no invented row)"""
    sof = {r["id"] for r in _csv(T281)}
    fw = {r["item"] for r in _csv(T264) if r["element"] in ("STAIR", "DOME", "SLAB")}
    for c in comps:
        for s in c["soffit_rows"]:
            if s not in sof:
                raise B.BasisError(f"{c['id']}: soffit row '{s}' not in LEDGER_T281")
        for s in c["formwork_rows"]:
            if s not in fw:
                raise B.BasisError(f"{c['id']}: formwork row '{s}' not in FORMWORK_LINES_R4")


def lines(cand):
    out = []
    for l in cand["lines"]:
        pe, ids = BIND[l["line_id"]]
        q = l["measured_net"]
        rec = {"group": "STAIR" if l["item_code"] == "STR.CONC.STAIR" else "DOME", "line_id": l["line_id"],
               "item_code": l["item_code"], "element_id": l["element_id"], "physical_element": pe,
               "engine_qty_m3": None if q is None else float(q), "engine_state": l["evidence_state"],
               "engine_basis": (l["formula"] or "")[:220], "components": ids,
               "evidence": "LEDGER_T258 (b1b72a50) pieces " + (" + ".join(ids) if ids else "none"),
               "printed_support": "see the pieces' sources (LEDGER_T258 'source')",
               "sheets_searched": "ST p.3 / p.4 / p.5 / p.7, arch GF / 1F / 2F, sections A-A / B-B (T-184, T-258, T-287)"}
        if not ids:
            rec["reason"] = pe
        if l["line_id"] in CITED:
            rec["cited"], rec["cited_item"] = CITED[l["line_id"]]
            rec["cited_status"] = B.HELD
        out.append(rec)
    return out


def build():
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    comps = inventory()
    check_owner_rows(comps)
    ctx = {"project_id": cand["project"]["project_id"], "revision_set_sha256": cand["project"]["revision_set_sha256"],
           "candidate": cand["candidate"]}
    ls = lines(cand)
    rows = B.ledger(ls, comps, ctx, NAMED)
    return cand, comps, rows


def summary(cand, comps, rows):
    byid = {c["id"]: c for c in comps}
    vo = [("ST01-MS1-LD", "L-7863355dfcb68a681d2d"), ("ST01-MS1-U", "L-7863355dfcb68a681d2d"),
          ("ST02-RS-S", "L-b6b0354b7842f0ed6e41"), ("ST02-RS-LD", "L-b6b0354b7842f0ed6e41"),
          ("ST02-RS-A", "L-b6b0354b7842f0ed6e41"), ("ST01b-D1-STEPS", "L-821032bc04a0b0d02133")]
    held_parts = [{"piece": i, "line_id": ln, "status": byid[i]["status"], "m3": byid[i]["value_m3"],
                   "evidence": byid[i].get("checker") or byid[i].get("owner_rule") or "drawing (T-258 r2 own read)"}
                  for i, ln in vo]
    s2864 = round(math.fsum(p["m3"] for p in held_parts), 6)
    st = {}
    for r in rows:
        st.setdefault(r["status"], []).append(r["line_id"])
    released_now = round(math.fsum(r["engine_qty_m3"] or 0 for r in rows), 6)
    ledger_q = round(math.fsum(r["drawing_qty_m3"] or 0 for r in rows), 6)
    return {
        "schema": "T290_SUMMARY", "rule": B.SCHEMA, "candidate": cand["candidate"],
        "candidate_lines_csv_sha256": cand["candidate_lines_csv_sha256"], "project": cand["project"],
        "lines": len(rows), "pieces_in_inventory": len(comps),
        "residual_m3": {g: round(math.fsum(r["engine_qty_m3"] or 0 for r in rows if r["group"] == g) - t, 6)
                        for g, t in NAMED.items()},
        "lines_by_status": {k: sorted(v) for k, v in sorted(st.items())},
        "engine_released_m3": released_now,
        "ledger_quantity_m3_on_closable_lines": ledger_q,
        "held_closable_parts": held_parts,
        "held_closable_parts_m3": s2864,
        "t266_label_m3": T266_LABEL_2915,
        "t266_label_minus_ledger_m3": round(T266_LABEL_2915 - s2864, 6),
        "unbound_pieces": B.unbound(rows, comps),
        "rows": [{k: r[k] for k in ("line_id", "status", "engine_qty_m3", "drawing_qty_m3", "drawing_low_m3",
                                    "drawing_high_m3", "closable_component_m3", "ledger_owner")} for r in rows],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    cand, comps, rows = build()
    s = summary(cand, comps, rows)
    if a.write:
        B.write_csv(HERE / "BASIS_LEDGER_T290.csv", rows)
        (HERE / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: s[k] for k in ("residual_m3", "lines_by_status", "engine_released_m3",
                                        "ledger_quantity_m3_on_closable_lines", "held_closable_parts_m3",
                                        "t266_label_minus_ledger_m3", "unbound_pieces")}, indent=1))
    for r in s["rows"]:
        print(r)


if __name__ == "__main__":
    main()
