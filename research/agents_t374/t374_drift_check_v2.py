"""T-473 DOWNGRADE_DRIFT_CHECK_V2 for the T-374 straight-bar schedule (every villa; every machine; stdlib only).

Supersedes, for the public test run, the T-411 check (t374_straight_bbs.snapshot_drift / check_snapshot, kept unchanged):

  R-T473-1  no test reads live board state. The committed copy T374_BOUND_DOWNGRADES_V2.json (built by
            t374_straight_bbs.snapshot_downgrades, the T-411 reader) is the only board data the public run uses; it carries
            each source file's sha256, record counts, the agents/control commit it was copied from and the sha256 of the
            copy it supersedes. A live comparison runs only when the caller names a verdicts folder (env
            T374_BOARD_VERDICTS or an argument); nothing resolves ../board by default.
  R-T473-2  a drifting record (on the board and not in the copy, in the copy and not on the board, or differing) that
            binds a line id of the schedule (any row of T374_STRAIGHT_BBS.csv, whatever its status) FAILS, naming the
            record and the bound line ids. A drifting record that binds none is REPORTED (one line each), never failed; a
            verdict-set sha change is reported, and fails only when that set carries a binding drift.
  R-T473-3  promotion stays refused: a record whose state is not HELD / CONFLICT, on either side, stops the check by id.
  R-T473-4  binding by id is necessary, not sufficient: section_invariance() states for the ground-beam spans of a
            record whether the straight longitudinal bars the schedule carries are the SAME under every p.13 section
            candidate the record leaves open (then no BBS row rests on the record's basis) or differ (then the rows on
            that span must be held by the Checker; the check names them).

    python -I research/agents_t374/t374_drift_check_v2.py --snapshot-from <verdicts dir> --board-commit <sha>
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
from decimal import Decimal
from pathlib import Path

POLICY = "DOWNGRADE_DRIFT_CHECK_V2"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SNAPSHOT_V2 = HERE / "T374_BOUND_DOWNGRADES_V2.json"
SNAPSHOT_V1 = HERE / "T374_BOUND_DOWNGRADES.json"
BBS_CSV = HERE / "T374_STRAIGHT_BBS.csv"
CENSUS_T426 = ROOT / "research/agents_t426/CENSUS_T426.csv"
T138 = ROOT / "research/agents_t138/t138_hand_ledger.py"
ENV_BOARD = "T374_BOARD_VERDICTS"
SCHEDULED = ("SCHEDULED", "SCHEDULED_BOUNDED", "RUN_PART")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = _load("t374_v1_for_t473", HERE / "t374_straight_bbs.py")
ScheduleRefused = B.ScheduleRefused


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- R-T473-1: the committed copy and the opt-in board

def board_verdicts_dir(env=None):
    """the live verdicts folder ONLY when the caller names it (env T374_BOARD_VERDICTS); None otherwise."""
    v = (os.environ if env is None else env).get(ENV_BOARD, "").strip()
    return Path(v) if v else None


def load_snapshot_v2(path=SNAPSHOT_V2) -> dict:
    snap = B.load_snapshot(path)                       # T-411 promotion refusal reused
    if snap.get("record_count") != len(snap["records"]):
        raise ScheduleRefused(f"{Path(path).name}: record_count {snap.get('record_count')} != "
                              f"{len(snap['records'])} records")
    if sum(snap.get("source_record_count", {}).values()) < len(snap["records"]):
        raise ScheduleRefused(f"{Path(path).name}: fewer source records than distinct records")
    return snap


def make_snapshot_v2(verdicts_dir, board_commit: str, supersedes=SNAPSHOT_V1) -> dict:
    snap = B.snapshot_downgrades(verdicts_dir)
    snap.update(schema="T374_BOUND_DOWNGRADES_V2", policy=POLICY, board_commit=board_commit,
                supersedes={"file": Path(supersedes).name, "sha256": sha256(supersedes)})
    return snap


# ---------------------------------------------------------------- R-T473-2 / -3: classify the drift

def bbs_line_ids(path=BBS_CSV) -> dict:
    """line id -> row_status of every row of the committed schedule."""
    return {r["line_id"]: r["row_status"] for r in csv.DictReader(open(path, encoding="utf-8"))}


def _refuse_promotion(records, side):
    bad = [r["downgrade_id"] for r in records if r.get("state") not in B.DOWNGRADE_STATES]
    if bad:
        raise ScheduleRefused(f"{side} records {bad}: state is not a downgrade (HELD / CONFLICT): a record may never "
                              "promote a line")


def classify_drift(live: dict, committed: dict, bbs_ids) -> dict:
    """{'binding': [(text, record id, bound ids)], 'reported': [text]} for every difference (T-411 naming kept)."""
    _refuse_promotion(live["records"], "board")
    _refuse_promotion(committed["records"], "snapshot")
    ids = set(bbs_ids)
    lv = {r["downgrade_id"]: r for r in live["records"]}
    cm = {r["downgrade_id"]: r for r in committed["records"]}
    binding, reported, bad_sets = [], [], set()

    def put(text, rec_ids, k, sets):
        bound = sorted(set(rec_ids) & ids)
        if bound:
            binding.append((text, k, bound))
            bad_sets.update(sets)
        else:
            reported.append(text + ": binds no schedule line (reported, not failed)")

    for k in sorted(set(lv) - set(cm)):
        put(f"record {k} on the board, missing from the snapshot", lv[k]["line_ids"], k, lv[k]["verdict_sets"])
    for k in sorted(set(cm) - set(lv)):
        put(f"record {k} in the snapshot, not on the board", cm[k]["line_ids"], k, cm[k]["verdict_sets"])
    for k in sorted(set(lv) & set(cm)):
        if lv[k] != cm[k]:
            f = ", ".join(x for x in sorted(set(lv[k]) | set(cm[k])) if lv[k].get(x) != cm[k].get(x))
            put(f"record {k} differs ({f})", set(lv[k]["line_ids"]) | set(cm[k]["line_ids"]), k,
                set(lv[k]["verdict_sets"]) | set(cm[k]["verdict_sets"]))
    ls, cs = live.get("source_sha256", {}), committed.get("source_sha256", {})
    for v in sorted(set(ls) | set(cs)):
        if ls.get(v) != cs.get(v):
            t = f"verdict set {v}: DOWNGRADES.json sha256 {str(cs.get(v))[:12]} in the snapshot, {str(ls.get(v))[:12]} on the board"
            if v in bad_sets:
                binding.append((t, None, []))
            else:
                reported.append(t + " (no binding record in it: reported)")
    if committed.get("record_count") not in (None, len(cm)):
        binding.append((f"snapshot record_count {committed['record_count']} != its {len(cm)} records", None, []))
    return {"binding": binding, "reported": reported}


def check_v2(live: dict, committed: dict, bbs_ids) -> list:
    """FAIL on a binding drift (record id and bound line ids named); return the report lines otherwise."""
    d = classify_drift(live, committed, bbs_ids)
    if d["binding"]:
        raise ScheduleRefused("downgrade drift binds schedule lines: " + "; ".join(
            t + (f" -> binds {', '.join(b)}" if b else "") for t, _, b in d["binding"]))
    return d["reported"]


# ---------------------------------------------------------------- R-T473-4: basis census for ground-beam records

def _run_to_band(run: str) -> str:
    """CENSUS_T426 run '142+7D8#1' -> the T-138 span id 'GSO-142-7D8-1'."""
    m = re.fullmatch(r"([0-9A-F+]+)#(\d+)", run)
    if not m:
        raise ScheduleRefused(f"run id {run!r} not in the <handle+handle>#<n> form")
    return "GSO-" + m.group(1).replace("+", "-") + "-" + m.group(2)


def section_invariance(record: dict, census=CENSUS_T426, bbs=BBS_CSV, t138=T138) -> list:
    """per line of a ground-beam record found in the T-426 census: its span, the p.13 candidate titles, whether the
    longitudinal bar sets (name, count, d) of those candidates are identical, and the schedule rows on that span with
    their status and net kg. A line not in the census is returned with span None (not assumed)."""
    details = _load("t138_for_t473", t138).DETAILS
    cen = {r["line_id"]: r for r in csv.DictReader(open(census, encoding="utf-8"))}
    rows = list(csv.DictReader(open(bbs, encoding="utf-8")))
    titles_map = {"LT2_5M": "LT2_5M", "LT5M": "LT5M", "GT5M": "GT5M", "EXT": "EXT"}
    out = []
    for lid in record["line_ids"]:
        c = cen.get(lid)
        if c is None:
            out.append({"line_id": lid, "span": None, "invariant": None, "rows": []})
            continue
        span = _run_to_band(c["run"])
        cands = [titles_map[t] for t in c["titles"].split("+") if t in titles_map]
        sets = [tuple(details[t]["bars"]) if details.get(t) else None for t in cands]
        invariant = bool(sets) and None not in sets and len(set(sets)) == 1
        mine = [r for r in rows if f":{span}:" in r["element_id"]]
        out.append({"line_id": lid, "span": span, "candidates": cands, "invariant": invariant,
                    "bars": [list(b) for b in sets[0]] if invariant else None,
                    "rows": [{"line_id": r["line_id"], "component": r["component"], "row_status": r["row_status"],
                              "net_kg": r["net_kg_low"]} for r in mine]})
    return out


def must_hold(census_rows) -> list:
    """schedule rows on a span whose candidate bar sets DIFFER and that are still scheduled: they rest on the record."""
    return [(c["span"], r["line_id"]) for c in census_rows if c["invariant"] is False
            for r in c["rows"] if r["row_status"] in SCHEDULED]


def scheduled_kg(census_rows) -> Decimal:
    return sum((Decimal(r["net_kg"]) for c in census_rows for r in c["rows"]
                if r["row_status"] in SCHEDULED and r["net_kg"]), Decimal(0))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-from", required=True, help="verdicts dir of agents/control")
    ap.add_argument("--board-commit", required=True)
    a = ap.parse_args(argv)
    snap = make_snapshot_v2(a.snapshot_from, a.board_commit)
    json.dump(snap, open(SNAPSHOT_V2, "w", encoding="utf-8"), indent=1)
    print(json.dumps({"records": snap["record_count"], "report": check_v2(snap, B.load_snapshot(), [])}, indent=1))


if __name__ == "__main__":
    main()
