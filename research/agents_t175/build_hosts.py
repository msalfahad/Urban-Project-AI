"""T-175 step 1 (read-only, scratch inputs): bind every opening of the T-150 census (and every engine opening the census
does not list) to its host wall run of the T-143 block table, and say whether it lies INSIDE that run's measured gross.

Usage (Python 3.11; drawings and scratch files stay outside the clone):
    python3 -I research/agents_t175/build_hosts.py <T-150 OPENINGS_T150.csv> <scratch>/v2.json <scratch>/arch.pkl \
        --out research/agents_t175/T175_OPENING_HOSTS.csv
<scratch>/v2.json comes from research/agents_t125/alsenan_v2_dump.py + alsenan_v2_run.py on P7757.dxf (sha256 ab54dd55..);
<scratch>/arch.pkl is the same ARCH_TAKEOFF_V2.12 run's arch dict (door elements with centres).
Binding: engine opening id (T-150 ENGINE_REF) -> the MASONRY_CENTRELINE_V2 run whose openings_in_run carries it -> the
T-143 row whose v2_runs lists that run. Doors with no band opening (closures) -> the free-end doorway record of V2
(DOORWAY_AT_FREE_END, the run it ends) by nearest wall end (distance printed); the rest are bound by hand below, each
with its evidence. IN_GROSS: the T-143 row's L1 - L2b (hand plan-cut gaps inside the run) is > 0 for an opening inside
its run; = 0 means the hand run stops at the opening (the gap is not in the gross)."""
from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
T143 = HERE.parent / "agents_t143" / "T143_BLOCK_BY_WALL_RUN.csv"

# hand bindings (no band opening id): opening -> (T-143 row, in_gross, evidence)
HAND = {
    "D-GF-02": ("GF-W27", True, "V2 DOORWAY_AT_FREE_END at end 0 of WB-FL0010-FL0011 (gap 0.80 after T-169); door "
                                "element 0.41 m from that wall end; T-143 L1 1.65 - L2b 0.85 = 0.80"),
    "D-GF-10": ("GF-W29", True, "V2 DOORWAY_AT_FREE_END at end 0 of WB-FL0038-FL0039 (gap 0.797); door element 0.41 m "
                                "from that end; T-143 L1 1.224 - L2b 0.424 = 0.80"),
    "D-1F-03": ("1F-W12", True, "V2 DOORWAY_AT_FREE_END of WB-FL0011-FL0012 (1.00); door element 0.51 m from that end; "
                                "T-143 L1 3.80 - L2b 2.80 = 1.00"),
    "D-1F-04": ("1F-W23", True, "V2 DOORWAY_AT_FREE_END of WB-FL0074-FL0075 (0.80); door element 0.41 m from that end; "
                                "T-143 L1 6.50 - L2b 4.70 = 1.80 = this 0.80 + OP-020 1.00"),
    "D-GF-14": ("GF-W30", True, "no V2 band (T-125 MISSING, GF-W30); the hand run GF-W30 (T-103) is the only hand row with "
                                "an unexplained 0.797 gap at the master bath; door element 0.51 m from the end of "
                                "WB-FL0059-FL0060; binding by the hand table, the row itself is HELD (no band, no height)"),
    "W03": ("GF-W37", False, "curved glazing printed 657 (Q-38 A) = the glazed line GF-W37 (T-103: 4.95 glazing of 5.05; "
                             "V2 GLAZED_LINE 6.726 m); its span is already out of the Q-69 B physical run (L2a 0.10)"),
    "W02": ("GF-W11", False, "saloon glazing 6.332 = the glazing span T-143 takes out of GF-W11 (L1 7.00 -> L2a 0.668)"),
    "W17": ("1F-W25", False, "concave glazed bay (COP-001, outer arc 3.29); its glazing 3.579 is out of 1F-W25 (L2a 0.537)"),
    "W18": ("1F-W00", True, "V2 GLAZED_STRETCH 0.50 in WB-FL0041-FL0042#1 (T-040 G7; engine has no opening id); T-103 "
                            "gap list of 1F-W00: 1.552 + 1.552 + 0.500"),
    "SX-01": (None, False, "east wall of the pool court: its piers (0.632 and 0.247 m, T-154) are carried by no T-143 row "
                           "(no wall band): the opening is in no measured gross; the piers are a block scope gap"),
    "SX-03": (None, False, "north wall of the pool court beside the 0.30 pier: no T-143 row carries this line"),
    "D-GF-15": (None, False, "gate in the sea-side fence (T-103 F-GF, 7.00 m with a 1.00 gate): fence, not in the house "
                             "block gross (fence material / height HELD, Q-65 C)"),
    "U-01": (None, False, "identity not established (T-150): no engine opening, no window mark: bound to no wall"),
}
# sill ABOVE THE FINISHED FLOOR where the T-150 SILL_M column carries a chain value or a level instead (found by the
# T-175 head-above-soffit guard): printed levels, floor levels GF +1.00 / 1F +5.50 / 2F +9.70 (T-143 / T-112)
SILL_FFL = {
    "W01": ("1.00", "SE p.6 chain from +0.15: 185 -> sill +2.00, 200 -> head +4.00; GF FFL +1.00: sill 1.00, head 3.00 "
                    "above the floor (T-150 SILL_M 1.85 is the chain part from +0.15, not a height above the floor)"),
    "W03": ("0.00", "NW p.8: +1.00 to +5.30; +1.00 is the GF FFL: sill 0.00 (T-150 SILL_M 1.00 is the level)"),
}
# engine openings the T-150 census does not list (found here): id -> (kind, width, floor, note)
EXTRA = {
    ("GF", "OP-020"): ("P-GF-01", "PASSAGE", "doorless 0.90 opening with head lines (HEAD_LINE evidence) in the GF stair "
                                             "hall wall WB-FL0076-FL0077; T-103 gap 1.10 on the face where a 0.20 cross "
                                             "wall ends (0.90 jamb to jamb on the other face)"),
    ("1F", "OP-009"): ("P-1F-01", "PASSAGE", "doorless 1.30 opening with head lines in WB-FL0022-FL0023; the hand runs "
                                             "1F-W14 / 1F-W15 stop at it (L1 = L2b): not in the gross"),
    ("GF", "OP-001"): ("P-GF-02", "PASSAGE", "1.40 open side (masonry / column jambs) between the two annex runs "
                                             "WB-FL0001-FL0002 #1 / #2: in no run (split out)"),
    ("GF", "OP-002"): ("P-GF-03", "PASSAGE", "1.00 open side of WB-FL0007-FL0008: in no run (split out)"),
    ("GF", "OP-003"): ("P-GF-04", "PASSAGE", "11.22 m open side along WB-FL0007-FL0008 (the side passage, Q-67): in no "
                                             "run, not a building opening"),
    ("GF", "OP-007"): ("P-GF-05", "PASSAGE", "1.20 open side of WB-FL0017-FL0018: in no run (split out)"),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("census")
    ap.add_argument("v2")
    ap.add_argument("arch")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    t143 = {r["row_id"]: r for r in csv.DictReader(open(T143, encoding="utf-8"))}
    run2row = {}
    for rid, r in t143.items():
        for v in (r["v2_runs"] or "").split():
            run2row.setdefault((r["floor"], v.split("|")[-1]), []).append(rid)
    v2 = json.load(open(a.v2))
    op2run = {}
    for fl, F in v2["floors"].items():
        for run in F["v2"]["runs"]:
            for o in run["openings_in_run"]:
                if o.get("opening_id"):
                    op2run[(fl, o["opening_id"])] = run["run_id"]
    arch = pickle.load(open(a.arch, "rb"))
    allops = {(o["floor"], o["opening_id"]): o for o in arch.get("openings") or () if o.get("opening_id")}
    rows, used = [], set()

    def gap(rid):
        r = t143[rid]
        return round(float(r["L1_arch_run_m"]) - float(r["L2b_plan_cut_solid_m"]), 3)

    for c in csv.DictReader(open(a.census, encoding="utf-8")):
        oid, fl = c["ID"], c["FLOOR"]
        refs = re.findall(r"\bC?OP-\d+", c["ENGINE_REF"])
        for r in refs:
            used.add((fl, r))
        if oid in HAND:
            row, ing, ev = HAND[oid]
            run = ""
        elif refs and (fl, refs[0]) in op2run:
            run = op2run[(fl, refs[0])]
            cand = run2row.get((fl, run), [])
            if len(cand) != 1:
                raise SystemExit(f"{oid}: V2 run {run} binds to T-143 rows {cand}: bind by hand")
            row = cand[0]
            ing = gap(row) > 0
            ev = f"engine {refs[0]} in V2 run {run} (T-143 v2_runs); T-143 L1 - L2b = {gap(row)}"
        else:
            raise SystemExit(f"{oid}: no binding")
        rows.append({"ID": oid, "FLOOR": fl, "KIND_T150": c["KIND"], "ENGINE_OPENING": ";".join(refs),
                     "WIDTH_M": c["WIDTH_M"], "HOST_ROW": row or "", "V2_RUN": run, "IN_GROSS": "YES" if ing else "NO",
                     "BINDING_EVIDENCE": ev, "SOURCE": "T-150 census (READY d4a22b0)",
                     "WIDTH_LO_M": c["WIDTH_LO_M"], "HEIGHT_M": c["HEIGHT_M"], "SILL_M": c["SILL_M"],
                     "HEIGHT_STATUS_T150": c["HEIGHT_STATUS"], "WALL_T_M": c["WALL_T_M"], "SIDE_A": c["SIDE_A"],
                     "SIDE_B": c["SIDE_B"], "HOLD_CAUSE": c["HOLD_CAUSE"], "FREELANCER_W": c["FREELANCER_W"],
                     "FREELANCER_H": c["FREELANCER_H"],
                     "SILL_ABOVE_FFL_M": SILL_FFL.get(oid, (c["SILL_M"], ""))[0],
                     "SILL_NOTE": SILL_FFL.get(oid, ("", ""))[1]})
    for (fl, opid), (nid, kind, note) in EXTRA.items():
        o = allops[(fl, opid)]
        run = op2run.get((fl, opid), "")
        cand = run2row.get((fl, run), []) if run else []
        row = cand[0] if len(cand) == 1 else ""
        ing = bool(row) and gap(row) > 0 and nid == "P-GF-01"
        rows.append({"ID": nid, "FLOOR": fl, "KIND_T150": "NOT IN THE T-150 CENSUS", "ENGINE_OPENING": opid,
                     "WIDTH_M": f"{float(o['width_m']):.2f}", "HOST_ROW": row if nid == "P-GF-01" else "",
                     "V2_RUN": run, "IN_GROSS": "YES" if ing else "NO",
                     "BINDING_EVIDENCE": note + (f"; T-143 L1 - L2b = {gap(row)}" if row else ""),
                     "SOURCE": "engine ARCH_TAKEOFF_V2.12 opening census (found by T-175)",
                     "WIDTH_LO_M": "", "HEIGHT_M": "", "SILL_M": "", "HEIGHT_STATUS_T150": "HELD",
                     "WALL_T_M": f"{float(o['wall_t_m']):.2f}", "SIDE_A": "", "SIDE_B": "", "HOLD_CAUSE": "",
                     "FREELANCER_W": "", "FREELANCER_H": "", "SILL_ABOVE_FFL_M": "", "SILL_NOTE": ""})
    # every engine opening is accounted for once
    missing = sorted(set(allops) - used - set(EXTRA))
    if missing:
        raise SystemExit(f"engine openings not accounted for: {missing}")
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "openings bound;", sum(r["IN_GROSS"] == "YES" for r in rows), "inside a measured gross run")


if __name__ == "__main__":
    main()
