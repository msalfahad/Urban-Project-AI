"""T-409 development-villa run: the B3-07 boundary table (floor transition profiles) and the US-08 hidden profile,
built ONLY from committed, Checker-merged ledgers (no private input, no candidate re-run):

  research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv   every census door / arch: width, wall t, wet / dry / external,
                                                         threshold material, line id (T-325 MERGED, Gate A)
  research/agents_t325/LINES_T325.csv                   the non-census strips (lift landings, OP-020) and their lines
  research/agents_t312/FACE_LEDGER_T312.csv             the drawn open edges (pantry 4.490, wash lobby 1.245)
  research/agents_t303/WP_WET_ROOF_POOL_INVENTORY_T303.csv  the three basin-space floors (Q-06 a: 9.35 m2)
  research/agents_t296/summary.json                     the skirting payable path ledger bound (V3.0.17)

    python3 -I research/agents_t409/t409_alsenan.py            # writes BOUNDARY_TABLE_T409.csv + summary.json
    python3 -I research/agents_t409/t409_alsenan.py --check    # re-derives and compares with the committed files
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import transition_profiles as TP  # noqa: E402

R = ROOT / "research"
INPUTS = {
    "t325_ledger": R / "agents_t325" / "SILL_THRESHOLD_LEDGER_T325.csv",
    "t325_lines": R / "agents_t325" / "LINES_T325.csv",
    "t312_faces": R / "agents_t312" / "FACE_LEDGER_T312.csv",
    "t303_inventory": R / "agents_t303" / "WP_WET_ROOF_POOL_INVENTORY_T303.csv",
    "t296_summary": R / "agents_t296" / "summary.json",
}
Q06 = "owner Q-06 (a) 2026-10-18: basin-only hand-wash spaces GF-02 / GF-11 / GF-14 take a marble threshold"
BASIN = ("GF-02", "GF-11", "GF-14")
FIELDS = ["id", "kind", "floor", "width_m", "finish_a", "finish_b", "threshold", "threshold_line", "class", "status",
          "qty_ml", "bound_lo_ml", "bound_hi_ml", "source", "why"]


def _csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha8(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]


def boundaries():
    led = _csv(INPUTS["t325_ledger"])
    out = []
    for r in led:
        if r["component"] != "THRESHOLD" or r["kind"] not in ("DOOR", "ARCH"):
            continue
        w = float(r["width_m"]) if r["width_m"] else None
        b = {"id": r["opening"], "kind": "GATE" if r["opening"] == "D-GF-15" else r["kind"], "floor": r["floor"],
             "width": w, "src": "T-325 ledger (width T-237, wall t T-150)"}
        mat = r["material"]
        if r["opening"] == "D-GF-15":
            b["unresolved"] = "site gate: width / wall HELD (T-325 UNRESOLVED, T-150 GATE)"
        elif r["external"] == "True":
            b.update(external=True, sides=["PORCELAIN (interior)", None],
                     threshold={"material": "HELD", "line_id": r["line_id"]})
        elif mat == "MARBLE":
            b.update(sides=["PORCELAIN (wet)", "PORCELAIN (dry)"], wet=[True, False],
                     threshold={"material": "MARBLE", "line_id": r["line_id"],
                                "source": "UP-THR-001 + URBAN-WET-SERVICE-MARBLE-THRESHOLD v1"})
        elif mat == "FLOOR PORCELAIN":
            b.update(sides=["PORCELAIN (dry)", "PORCELAIN (dry)"], threshold=None)
        elif r["opening"] == "A-GF-01":
            # arch120 OP-027 between the basin space GF-02 (WP floor 3.1325 m2, T-303) and the dewaneya GF-01
            b.update(sides=["PORCELAIN (wet)", "PORCELAIN (dry)"], wet=[True, False],
                     threshold={"material": "MARBLE", "line_id": r["line_id"], "source": Q06},
                     src="T-325 ledger + T-303 basin floor GF-02 + Q-06 (a)")
        elif r["opening"] == "A-1F-01":
            # arch120 OP-011 between the 3.80 x 4.30 room and the dressing 1F-RFFE7AF (material HELD, T-223)
            b.update(sides=["PORCELAIN (dry)", None], threshold=None,
                     src="T-325 ledger + T-223 dressing (DRY, area VERIFIED, floor material HELD)")
        else:
            raise TP.CensusError(f"unclassified T-325 row {r['opening']}")
        b["line_id"] = r["line_id"]
        out.append(b)

    lines = {x["line_id"]: x for x in _csv(INPUTS["t325_lines"])}
    # P-GF-01 = engine GF OP-020: doorless 0.90 opening, GF stair hall <-> basin space GF-11 (T-198 / T-128 r3)
    op20 = lines["L-9bcc79e76f84667b244a"]
    out.append({"id": "P-GF-01", "kind": "PASSAGE", "floor": "GF", "width": float(op20["length_m"]),
                "sides": ["PORCELAIN (wet)", "PORCELAIN (dry)"], "wet": [True, False],
                "threshold": {"material": "MARBLE", "line_id": op20["line_id"], "source": Q06},
                "src": "T-325 LINES (OP-020 strip 0.90 x 0.20) + T-198 (faces 0.890 / 0.891) + Q-06 (a)"})
    faces = {x["face_id"]: x for x in _csv(INPUTS["t312_faces"])}
    for key, other, wet_side, src in (
            ("GF-14|OPEN", "stair hall (dry)", True, Q06),
            ("GF-07|OPEN", "dining (dry)", True, None)):
        f = faces[key]
        assert f["scope"] == "OPEN_EDGE", key
        w = float(f["length_m"])
        b = {"id": f"OPEN-{key.split('|')[0]}", "kind": "OPEN_EDGE", "floor": "GF", "width": w,
             "sides": ["PORCELAIN (wet)", "PORCELAIN (dry)"], "wet": [True, False],
             "src": f"T-312 face ledger {key} (open side, no wall drawn) -> {other}"}
        if src:
            b["threshold"] = {"material": "MARBLE", "line_id": None, "source": src + " (no wall: depth not drawn)"}
        else:
            b["threshold"] = None   # pantry: the marble rule names it not_applicable; Q-37 A is a WP answer
            b["src"] += "; marble rule not_applicable to pantry; Q-37 A = WP termination only"
        out.append(b)
    for lid, oid, fl in (("L-6f5806adbacba9118497", "LIFT-GF-OP-011", "GF"),
                         ("L-084df97d3d41525a65c2", "LIFT-1F-OP-007", "1F"),
                         ("L-3c5a3be22e861d9d4cfb", "LIFT-2F-OP-002", "2F")):
        out.append({"id": oid, "kind": "LIFT_LANDING", "floor": fl, "width": 1.0, "lift": True,
                    "threshold": {"material": "HELD", "line_id": lid},
                    "src": "T-325 LINES (ARCH.THRESHOLD LIFT_LANDING, T-240) / T-223"})
    for r in led:
        if r["kind"] == "FLOOR_GLAZING" and r["component"] == "THRESHOLD_OUT":
            if r["outside"].startswith("TERRACE"):
                out.append({"id": r["opening"], "kind": "FLOOR_GLAZING", "floor": r["floor"],
                            "width": float(r["width_m"]), "frame": True,
                            "src": f"T-325 ledger (flush frame; outside strip = {r['outside']} finish)"})
            elif r["opening"] == "W03":
                out.append({"id": "W03", "kind": "FLOOR_GLAZING", "floor": "GF", "width": None,
                            "unresolved": "curved floor glazing: both sides UNRESOLVED (T-302 / T-325)",
                            "src": "T-325 ledger"})
            # W25 / W27 stand over outside air: no floor beyond, not a floor boundary
    out.append({"id": "GF-OP-007", "kind": "PASSAGE", "floor": "GF", "width": 1.2,
                "unresolved": "side passage mouth (FLOOR.OUTDOOR side walk, porcelain by the owner sides rule): the "
                              "floor beyond the mouth is not traced in any merged ledger",
                "src": "T-223 STRIPS (GF OP-007 1.20 x 0.20, part of FLOOR.OUTDOOR 5.640)"})
    return out


def build():
    bs = boundaries()
    rows = TP.census(bs)
    src = {b["id"]: b["src"] for b in bs}
    for r in rows:
        r["source"] = src[r["id"]]
    TP.check(rows)
    # marble threshold rows never also strips: the threshold line is the marble's, no strip line exists
    assert not any(r["class"] == TP.RULE_IF and r.get("strip_line") for r in rows)
    t296 = json.loads(INPUTS["t296_summary"].read_text())["ledger"]
    hp = TP.hidden_profile([t296["ledger_lo_lm"], t296["ledger_hi_lm"]], None)
    hp.update(candidate_skirting_net_lm=json.loads(INPUTS["t296_summary"].read_text())["ledger"]["cand_net_lm"],
              skirting_basis="T-296 ledger on V3.0.17 (MERGED); re-read on the candidate of record by lane I",
              freelancer_rows=0)
    return rows, hp


def table_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        b = r.get("bound_ml") or [None, None]
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in FIELDS if k not in ("bound_lo_ml", "bound_hi_ml")}
                   | {"bound_lo_ml": "" if b[0] is None else f"{b[0]:.6f}",
                      "bound_hi_ml": "" if b[1] is None else f"{b[1]:.6f}",
                      "width_m": "" if r["width_m"] is None else f"{r['width_m']:.6f}",
                      "qty_ml": "" if r["qty_ml"] is None else f"{r['qty_ml']:.6f}"})
    return buf.getvalue()


def summary(rows, hp):
    held_hi = round(sum(r["bound_ml"][1] for r in rows if r["status"] == TP.HELD), 6)
    return {"policy": TP.POLICY_ID, "inputs": {k: sha8(p) for k, p in INPUTS.items()},
            "boundaries": len(rows), "by_class": TP.totals(rows),
            "transition_profile": {"released_ml": 0.0, "held_rows": sum(r["status"] == TP.HELD for r in rows),
                                   "held_bound_ml": [0.0, held_hi],
                                   "unknown_rows": sum(r["status"] == TP.UNKNOWN for r in rows)},
            "marble_edges_geometry_ml": round(2 * sum(r["width_m"] for r in rows
                                                      if r["class"] == TP.RULE_IF and r["width_m"]), 6),
            "hidden_profile_us08": hp, "freelancer_profile_rows": 0}


def main(argv):
    rows, hp = build()
    t = table_csv(rows)
    s = json.dumps(summary(rows, hp), indent=1, sort_keys=True) + "\n"
    if "--check" in argv:
        ok = (HERE / "BOUNDARY_TABLE_T409.csv").read_text() == t and (HERE / "summary.json").read_text() == s
        print("T-409 check:", "REPRODUCED" if ok else "DIFFERS")
        return 0 if ok else 1
    (HERE / "BOUNDARY_TABLE_T409.csv").write_text(t)
    (HERE / "summary.json").write_text(s)
    print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
