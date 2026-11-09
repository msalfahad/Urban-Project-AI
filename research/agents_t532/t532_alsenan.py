"""T-532 training-villa builder (research only): COLUMN_END_CENSUS_V3 (R-T532-1) run on the merged T-274 run pieces with
their own kinds (BEAM / FACE / NONE / COLUMN), checked against the merged ledgers.

Inputs (committed, numbers and ids only): research/agents_t274/T274_RUN_PIECES.csv (piece kinds per run),
research/agents_t526/out/END_CENSUS_V2_T526.csv (end classes from the drawings, R-T526-1) and MISSED_ENDS_T526.csv
(per-end effects), research/agents_t355/SHARMAT_T355.csv (R-T355-3 junctions) and research/agents_t317/JOINTS_T317.csv
(V joints). No drawing is read here.

Checks: (1) V2 on the raw kinds raises / skips (the F-C-T526-1 before state); (2) V3 lists the same end junctions as
T-526 (12 COLUMN + 1 PARTIAL HELD) without raising, so the T-526 per-end deltas stand unchanged; (3) every interior
masonry / column junction V3 lists on a run of the T-317 / T-355 ledgers is found there (no new or lost tie / mesh
junction), and every one V2 skips on raw kinds is named with its class.
Writes research/agents_t532/out/{KIND_MAP_T532.csv, JUNCTIONS_V3_T532.csv, SUMMARY_T532.json}.

    python3 -I research/agents_t532/t532_alsenan.py [--check]
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
RES = HERE.parent
sys.path.insert(0, str(HERE))
import end_census_v3 as V3  # noqa: E402

OUT = HERE / "out"
PIECES = RES / "agents_t274/T274_RUN_PIECES.csv"
CENSUS = RES / "agents_t526/out/END_CENSUS_V2_T526.csv"
MISSED = RES / "agents_t526/out/MISSED_ENDS_T526.csv"
SHARMAT = RES / "agents_t355/SHARMAT_T355.csv"
JOINTS = RES / "agents_t317/JOINTS_T317.csv"


def _csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def run_pieces():
    by = defaultdict(list)
    for x in _csv(PIECES):
        by[x["run_key"]].append(x)
    for k in by:
        by[k].sort(key=lambda x: int(x["seq"]))
    return by


def end_results():
    """(run -> [EndResult end 0, EndResult end 1]) rebuilt from the committed T-526 census (drawing-derived)."""
    out = defaultdict(dict)
    meta = {}
    for r in _csv(CENSUS):
        if r["end"] == "":
            continue
        gap = float(r["gap_mm"]) / 1000 if r["gap_mm"] else None
        cov = float(r["cover"]) if r["cover"] else 0.0
        j = {"YES": True, "NO": False}.get(r["junction_v2"])
        out[r["run"]][int(r["end"])] = V3.EndResult(r["class_v2"], gap, cov, None, None, j, r["held"])
        meta[(r["run"], int(r["end"]))] = r
    return {k: [v[0], v[1]] for k, v in out.items()}, meta


def column_key(rk, piece):
    """the column id the merged T-317 / T-355 builders give a COLUMN piece (t317_alsenan.run_pieces)."""
    return f"{rk}@{float(piece['from_m']):.3f}"


def build():
    P = run_pieces()
    ER, meta = end_results()
    sharmat = {(x["column_at"], x["face"]) for x in _csv(SHARMAT)}
    sharmat_runs = {x["column_at"].split("@")[0] for x in _csv(SHARMAT)}
    vj = Counter(x["at"] for x in _csv(JOINTS) if x["dir"] == "V")
    t317_runs = {x["run"] for x in _csv(JOINTS)}
    rows, v2_state = [], Counter()
    for rk in sorted(ER):
        if rk not in P:
            raise V3.EndCensusError(f"{rk}: census run without T-274 pieces")
        ps = P[rk]
        kinds = [x["kind"] for x in ps]
        v2, err = V3.v2_on_kinds(rk, kinds, ER[rk])
        v2_interior = 0 if v2 is None else sum(1 for j in v2 if j["source"] == "V1")
        v2_state["RAISES" if v2 is None else "RUNS"] += 1
        for j in V3.end_junctions_v3(rk, kinds, ER[rk]):
            rec = {"run": rk, "wall_id": meta[(rk, 0)]["wall_id"], "source": j["source"], "at": j["at"],
                   "class": j["class"], "state": j["state"], "held": j.get("held", ""),
                   "v2_on_raw_kinds": "RAISES" if v2 is None else ("LISTED" if v2_interior or j["source"] == "V3_END"
                                                                   else "SKIPPED"),
                   "column_at": "", "face": "", "in_t355": "", "in_t317_v": ""}
            if j["source"] == "V3_INTERIOR" and j["state"] == "LISTED":
                col = ps[j["column_piece"]]
                key = column_key(rk, col)
                rec.update(column_at=key, face=j["face"])
                rec["in_t355"] = ("YES" if (key, j["face"]) in sharmat else "NO") if rk in sharmat_runs else "RUN NOT IN LEDGER"
                rec["in_t317_v"] = ("YES" if vj[key] else "NO") if rk in t317_runs else "RUN NOT IN LEDGER"
                # V2 on raw kinds lists no interior junction: BLOCK is never a T-274 kind
                rec["v2_on_raw_kinds"] = "RAISES" if v2 is None else "SKIPPED"
            if j["source"] == "V3_END":
                m = meta[(rk, int(j["at"].split()[1]))]
                rec.update(column_at=m["t119_id"], face="end", in_t355=m["listed_t355"], in_t317_v=m["listed_t317"])
                rec["v2_on_raw_kinds"] = "RAISES" if v2 is None else rec["v2_on_raw_kinds"]
            rows.append(rec)
    v3keys = {(r["column_at"], r["face"]) for r in rows if r["source"] == "V3_INTERIOR" and r["state"] == "LISTED"}
    v2_state["t355_rows_not_in_v3"] = len(sharmat - v3keys)
    v2_state["t317_v_columns_not_in_v3"] = len(set(vj) - {k for k, _f in v3keys})
    return rows, v2_state, ER, P


def reconcile(rows):
    """V3 end junctions vs the T-526 per-end ledger: the same 12 + 1 ends, so its deltas stand unchanged."""
    missed = _csv(MISSED)
    want_listed = {(m["run"], m["end"]) for m in missed if m["state"] == "COMPUTED"}
    want_held = {(m["run"], m["end"]) for m in missed if m["state"] == "HELD"}
    got_listed = {(r["run"], r["at"].split()[1]) for r in rows if r["source"] == "V3_END" and r["state"] == "LISTED"}
    got_held = {(r["run"], r["at"].split()[1]) for r in rows if r["source"] == "V3_END" and r["state"] == "HELD"}
    num = lambda k: round(sum(float(m[k]) for m in missed if m.get(k) not in ("", None)), 6)
    w09 = next(m for m in missed if m["wall_id"] == "1F-W09")
    return {"listed_equal": got_listed == want_listed, "held_equal": got_held == want_held,
            "listed_n": len(got_listed), "held_n": len(got_held),
            "only_v3": sorted(map(list, got_listed - want_listed)), "only_t526": sorted(map(list, want_listed - got_listed)),
            "carried_deltas": {"d_length_m": num("d_length_m"), "d_blockwork_m2": num("d_blockwork_m2"),
                               "d_blocks_nr": num("d_blocks_nr"), "d_mesh_owner_ml": num("d_mesh_owner_ml"),
                               "d_mesh_drawing_ml": num("d_mesh_drawing_ml"), "d_ties_nr": num("d_ties_nr"),
                               "d_perimeter_m3_1F-W09": float(w09["d_perimeter_m3"])}}


def summarise(rows, v2_state, ER, P):
    inner_end = Counter(r["class"] for r in rows if r["source"] == "V3_END")
    inter = [r for r in rows if r["source"] == "V3_INTERIOR"]
    kinds_seen = Counter(x["kind"] for rk in ER for x in P[rk])
    s = {"rule": "R-T532-1 COLUMN_END_CENSUS_V3: junctions read on the ledger's own piece kinds by plan role "
                 "(BEAM / FACE / NONE / BLOCK = masonry, COLUMN / ST_COLUMN = concrete, any other kind HELD by name); "
                 "end classes from R-T526-1 unchanged",
         "runs": len(ER), "piece_kinds_on_census_runs": dict(sorted(kinds_seen.items())),
         "v2_on_raw_kinds": dict(v2_state),
         "end_junctions_by_class": dict(sorted(inner_end.items())),
         "interior_listed_by_class": dict(sorted(Counter(r["class"] for r in inter if r["state"] == "LISTED").items())),
         "interior_held": [f"{r['run']} {r['at']} {r['class']}: {r['held']}" for r in inter if r["state"] == "HELD"],
         "interior_vs_t355": dict(sorted(Counter(r["in_t355"] for r in inter if r["state"] == "LISTED").items())),
         "interior_vs_t317_v": dict(sorted(Counter(r["in_t317_v"] for r in inter if r["state"] == "LISTED").items())),
         "interior_not_in_ledger_named": [f"{r['run']} {r['at']} {r['class']} {r['column_at']} {r['face']} "
                                          f"(t355 {r['in_t355']}, t317 {r['in_t317_v']})" for r in inter
                                          if r["state"] == "LISTED" and "NO" in (r["in_t355"], r["in_t317_v"])],
         "reconcile_t526": reconcile(rows),
         "sha256_inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (PIECES, CENSUS, MISSED, SHARMAT, JOINTS)}}
    return s


def kind_map_csv():
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(["kind", "plan_role", "masonry_head", "source"])
    for k, (r, h, src) in V3.KIND_MAP.items():
        w.writerow([k, r, h, src])
    w.writerow(["<any other>", V3.UNKNOWN, "-", "not mapped: every boundary it takes part in is HELD by name"])
    return b.getvalue()


def texts():
    rows, v2_state, ER, P = build()
    keys = list(rows[0].keys())
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return {"KIND_MAP_T532.csv": kind_map_csv(), "JUNCTIONS_V3_T532.csv": b.getvalue(),
            "SUMMARY_T532.json": json.dumps(summarise(rows, v2_state, ER, P), indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    T = texts()
    if "--check" in argv:
        bad = [k for k, v in T.items() if not (OUT / k).exists() or (OUT / k).read_text(encoding="utf-8") != v]
        print("reproduce:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for k, v in T.items():
        (OUT / k).write_text(v, encoding="utf-8")
    print(T["SUMMARY_T532.json"][:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
