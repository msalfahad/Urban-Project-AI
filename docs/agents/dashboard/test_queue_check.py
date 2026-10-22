"""Regression test for queue_check.py; T-185 (dome scenarios, 2026-10-22) is the case. Run: python3 -I test_queue_check.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from queue_check import check  # noqa: E402

ROW = "| T-185 | 1 | lane S · domes, scenarios S0 / S1 / S2 (every villa) | owner teaching case | TODO [owner teaching case] | | |"
ROW_184 = "| T-184 | 1 | lane S · staircases | owner | MERGED (verifier 2026-10-22 15:00 UTC) | | |"
ROW_Q = "| T-170 | 2 | lane S · level chain | plan | QUEUED | | |"
ROW_CHK = "| T-180 | 0 | checker · re-measure reference lines | owner | IN PROGRESS (checker standing slot) | | |"
ROW_QB = "| T-168 | 2 | lane I · something | plan | QUEUED (after T-167 merges) | | |"
LEAD_WITH = "Lead 2026-10-22 12:20: VERIFIER QUEUE (...). LANE ORDER for the next worker runs: S (worker 1): T-184, T-183 r2, T-163 r2, T-185, T-174; A (worker 2): T-175; I (worker 3): T-167."
LEAD_WITHOUT = "Lead 2026-10-22 12:20: VERIFIER QUEUE (...). LANE ORDER for the next worker runs: S (worker 1): T-184, T-183 r2, T-163 r2, T-174; A (worker 2): T-175; I (worker 3): T-167."
OWNER_TAKES = "OWNER SESSION 2026-10-22 15:55 (main chat): WORKER 1 takes T-185 in its next run."


def runs(n):
    return ["- 2026-10-22 %02d:%02d UTC | Worker 1 | SUCCESS | T-x READY | ... | none" % (13 + i, 5) for i in range(n)]


def get(res, tid):
    return next(r for r in res if r["id"] == tid)


def test_not_queued():  # adverse: a TODO task no queue names (what the owner saw for T-185)
    r = get(check([LEAD_WITHOUT, ROW, ROW_184], [])[0], "T-185")
    assert any(f.startswith("NOT_QUEUED") for f in r["flags"]), r
    assert r["agent"] == "Worker 1"


def test_queued_in_order():  # normal: position 4, the worker has finished 2 runs since the note
    r = get(check([LEAD_WITH, ROW], runs(2))[0], "T-185")
    assert r["flags"] == [] and r["queue"] == "Worker 1 position 4", r


def test_stalled():  # adverse: the worker finished 5 runs since the note and T-185 (position 4) is still TODO
    r = get(check([LEAD_WITH, ROW], runs(5))[0], "T-185")
    assert any(f.startswith("STALLED") for f in r["flags"]), r


def test_owner_session_moves_it_first():  # a newer owner-session note puts it at position 1; runs before it do not count
    r = get(check([OWNER_TAKES, LEAD_WITH, ROW], runs(2))[0], "T-185")  # runs at 13:05, 14:05, before the 15:55 note
    assert r["queue"] == "Worker 1 position 1" and r["flags"] == [], r
    late = ["- 2026-10-22 16:30 UTC | Worker 1 | SUCCESS | T-163 READY | ... | none",
            "- 2026-10-22 18:30 UTC | Worker 1 | SUCCESS | T-174 READY | ... | none"]
    r = get(check([OWNER_TAKES, LEAD_WITH, ROW], runs(2) + late)[0], "T-185")  # two runs after the note, still TODO
    assert any(f.startswith("STALLED") for f in r["flags"]), r


def test_merged_rows_ignored_and_blockers_required():
    res = check([LEAD_WITH, ROW_184, ROW_Q, ROW_QB], [])[0]
    assert all(r["id"] != "T-184" for r in res)
    assert any(f.startswith("NO_BLOCKER") for f in get(res, "T-170")["flags"])
    assert get(res, "T-168")["flags"] == []
    assert get(check([LEAD_WITH, ROW_CHK], [])[0], "T-180")["agent"] == "Checker"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
    print("ALL QUEUE CHECK TESTS PASSED")
