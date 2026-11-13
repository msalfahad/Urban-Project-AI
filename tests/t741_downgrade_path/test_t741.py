"""T-741: research/agents_t741/downgrade_add.py, the Checker's downgrade-only issue path over tools/boq_export_v1.py.

Hand-made synthetic villa N741 (not the development villa), quantities by hand:
  R1 roof membrane 12.40 x 9.50 = 117.800 m2 MEASURED (the released line the Checker downgrades)
  R2 roof membrane  6.00 x 4.00 =  24.000 m2 MEASURED
  U1 membrane upturn perimeter 2 x (12.40 + 9.50) = 43.800 lm MEASURED (another unit)
  R3 roof membrane BLOCKED_RFI (screed fall not printed)
NORMAL: a HELD downgrade of R1 (engine_qty 117.8 bound, no quantity of its own) in dry run prints exactly the record the
tool itself writes and writes nothing; a real issue writes the record file byte-identical to calling the tool directly;
CONFLICT and the optional leading action word are accepted. ADVERSE: promotion states, an unknown line, path traversal,
a file that is not a downgrade record file, a symlink on the path, another action, an abbreviated or foreign option, a
non-Checker routine, two units: each refused (exit 2) with the record file byte-unchanged.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from engine.source import boq_line as BL
from tools import boq_export_v1 as X

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t741"))  # noqa: E402
import downgrade_add as D  # noqa: E402

PID, REV = "villa-n741", "7" * 64
CV = "ARCH_TAKEOFF_V9.0.1"
DOC = {"file": "A-05 roof plan.dxf", "sha256": "b" * 64}
TIME = "2026-11-12T14:00:00Z"


def ln(code, eid, unit, q=None, ev="MEASURED", **kw):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=q, element_id=eid, floor="RF", formula="L*B", rule_id="R-N741",
                        rule_version="1", documents=[DOC], inputs=kw.pop("inputs", {}), item_en="Roof waterproofing",
                        item_ar="عازل الأسطح", trade="WATERPROOFING", **kw)


def lines():
    return [ln("FIN.WP.ROOF", "R1", "m2", 117.8, inputs={"L": 12.4, "B": 9.5}),
            ln("FIN.WP.ROOF", "R2", "m2", 24.0, inputs={"L": 6.0, "B": 4.0}),
            ln("FIN.WP.ROOF", "U1", "lm", 43.8, inputs={"P": 43.8}),
            ln("FIN.WP.ROOF", "R3", "m2", ev="BLOCKED_RFI", rfi={"question": "screed fall not printed"})]


def lid(eid):
    return [x for x in lines() if x["location"]["element_id"] == eid][0]["line_id"]


@pytest.fixture
def env(tmp_path):
    lp = tmp_path / "V9_0_1_BOQ_LINES.json"
    lp.write_text(BL.dumps(lines()), encoding="utf-8")
    verdicts = tmp_path / "board" / "docs" / "agents" / "verdicts"
    verdicts.mkdir(parents=True)
    return {"tmp": tmp_path, "lines": lp, "verdicts": verdicts, "out": verdicts / "V9.0.1" / "DOWNGRADES.json"}


def args(env, *, ids=("R1",), state="HELD", out=None, routine="Checker", extra=()):
    return ["--lines", str(env["lines"]), "--candidate-version", CV, "--line-ids", ",".join(lid(i) for i in ids),
            "--state", state, "--reason", "membrane band above its own measured high end (chord deduction)",
            "--evidence", "A-05 roof plan=dome D 1.40 (two)", "--evidence", "A-05 roof plan=parapet face 12.40",
            "--run-token", "20261112T140000-1-1", "--routine", routine, "--verdict-commit", "c0ffee12",
            "--time", TIME, "--out", str(out if out is not None else env["out"]), *extra]


def call(argv):
    buf = io.StringIO()
    rc = D.run(argv, stdout=buf)
    return rc, buf.getvalue()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None


def seed(env):
    """an existing record file with one earlier record (on R2), written by the tool itself."""
    a = args(env, ids=("R2",))
    a[a.index("--time") + 1] = "2026-11-11T09:00:00Z"
    env["out"].parent.mkdir()
    with __import__("contextlib").redirect_stdout(io.StringIO()):
        assert X.main(["downgrade-add"] + a) == 0
    return sha(env["out"])


# ---- NORMAL ---------------------------------------------------------------------------------------------------------

def test_dry_run_prints_the_tools_record_and_writes_nothing(env):
    before = seed(env)
    rc, txt = call(args(env, extra=("--dry-run",)))
    assert rc == 0 and sha(env["out"]) == before
    rec = json.loads(txt.split("T741 DRY RUN")[0])
    assert rec["schema"] == X.DOWNGRADE_SCHEMA and rec["state"] == "HELD" and rec["line_ids"] == [lid("R1")]
    assert rec["engine_qty"] == 117.8 and rec["unit"] == "m2" and rec["resolved"] is False
    assert not any(k in rec for k in ("checker_qty", "qty", "measured_net", "corrected_qty"))
    assert rec["basis_label"] == "UNSUPPORTED BASIS" and not X.validate_downgrade(rec)
    # the same record, byte for byte, as the tool's own stdout on a direct call
    direct = env["tmp"] / "direct" / "docs" / "agents" / "verdicts" / "V9.0.1"
    direct.mkdir(parents=True)
    buf = io.StringIO()
    with __import__("contextlib").redirect_stdout(buf):
        assert X.main(["downgrade-add"] + args(env, out=direct / "DOWNGRADES.json")) == 0
    assert txt.split("T741 DRY RUN")[0] == buf.getvalue()


def test_dry_run_on_absent_file_creates_nothing(env):
    rc, txt = call(args(env, extra=("--dry-run",)))
    assert rc == 0 and "absent, not created" in txt
    assert not env["out"].exists() and not env["out"].parent.exists()


def test_issue_is_byte_identical_to_the_tool(env):
    seed(env)
    other = env["tmp"] / "tool" / "docs" / "agents" / "verdicts" / "V9.0.1"
    other.mkdir(parents=True)
    (other / "DOWNGRADES.json").write_bytes(env["out"].read_bytes())
    rc, txt = call(["downgrade-add"] + args(env))
    with __import__("contextlib").redirect_stdout(io.StringIO()) as tbuf:
        assert X.main(["downgrade-add"] + args(env, out=other / "DOWNGRADES.json")) == 0
    assert rc == 0 and txt == tbuf.getvalue()
    assert env["out"].read_bytes() == (other / "DOWNGRADES.json").read_bytes()
    doc = json.loads(env["out"].read_text(encoding="utf-8"))
    assert len(doc["downgrades"]) == 2 and all(not X.validate_downgrade(r) for r in doc["downgrades"])


def test_conflict_state_and_held_line_accepted(env):
    rc, _ = call(args(env, ids=("R3",), state="CONFLICT"))
    doc = json.loads(env["out"].read_text(encoding="utf-8"))
    assert rc == 0 and doc["downgrades"][0]["state"] == "CONFLICT" and doc["downgrades"][0]["engine_qty"] == 0.0


def test_runs_as_the_wrapper_runs_it(env):
    """`agent_env.sh run` = `python -I research/agents_t741/downgrade_add.py ...` from the tree root."""
    p = subprocess.run([sys.executable, "-I", "research/agents_t741/downgrade_add.py", "downgrade-add",
                        *args(env, extra=("--dry-run",))], cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert "T741 DRY RUN: nothing written" in p.stdout and not env["out"].exists()


# ---- ADVERSE --------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("state", ["VERIFIED", "RELEASED", "MEASURED", "VERIFIED ZERO", "held", ""])
def test_promotion_or_other_state_refused(env, state):
    before = seed(env)
    with pytest.raises(D.Refused, match="state|arguments"):
        call(args(env, state=state))
    assert sha(env["out"]) == before


def test_unknown_line_refused_and_nothing_left(env):
    a = args(env)
    a[a.index("--line-ids") + 1] = "L-00000000000000000000"
    with pytest.raises(D.Refused, match="unknown line id"):
        call(a)
    assert not env["out"].parent.exists()


def test_two_units_refused(env):
    with pytest.raises(D.Refused, match="more than one unit"):
        call(args(env, ids=("R1", "U1")))
    assert not env["out"].exists()


def test_non_checker_routine_refused(env):
    with pytest.raises(D.Refused, match="not the Checker"):
        call(args(env, routine="Worker 1"))
    assert not env["out"].exists()


@pytest.mark.parametrize("bad", [
    "{v}/V9.0.1/../V9.0.1/DOWNGRADES.json",           # traversal, even back to the same file
    "{v}/V9.0.1/../../../../evil/DOWNGRADES.json",
    "{v}/V9.0.1/DOWNGRADES.json.bak",                  # not the record file
    "{v}/V9.0.1/URBAN_CHECKER_VERDICT_V2_SET.json",
    "{v}/DOWNGRADES.json",                             # no version folder
    "{v}/latest/DOWNGRADES.json",                      # not a version folder
    "{t}/elsewhere/V9.0.1/DOWNGRADES.json",            # not under docs/agents/verdicts
    "{t}/missing/docs/agents/verdicts/V9.0.1/DOWNGRADES.json",   # verdicts folder absent
])
def test_out_not_a_record_file_refused(env, bad):
    before = seed(env)
    out = bad.format(v=env["verdicts"], t=env["tmp"])
    with pytest.raises(D.Refused, match="--out"):
        call(args(env, out=out))
    assert sha(env["out"]) == before
    assert not Path(os.path.abspath(out)).exists() or Path(os.path.abspath(out)) == env["out"]


def test_symlink_on_path_refused(env):
    real = env["tmp"] / "real" / "docs" / "agents" / "verdicts"
    real.mkdir(parents=True)
    link = env["tmp"] / "link"
    link.mkdir()
    (link / "docs").symlink_to(env["tmp"] / "real" / "docs")
    with pytest.raises(D.Refused, match="symlink"):
        call(args(env, out=link / "docs" / "agents" / "verdicts" / "V9.0.1" / "DOWNGRADES.json"))
    assert not (real / "V9.0.1").exists()
    env["out"].parent.mkdir()
    (env["out"].parent / "DOWNGRADES.json").symlink_to(env["tmp"] / "target.json")
    with pytest.raises(D.Refused, match="symlink"):
        call(args(env))
    assert not (env["tmp"] / "target.json").exists()


@pytest.mark.parametrize("pre,extra", [
    (["verdict-add"], ()), (["verdict-rebind"], ()), (["export"], ()),
    ([], ("--checker-qty", "115.8")),     # a downgrade carries no Checker measurement
    ([], ("--scope", "WHOLE")),
    ([], ("--ou", "x")),                  # abbreviation never widened to --out
])
def test_other_action_or_option_refused(env, pre, extra):
    before = seed(env)
    with pytest.raises(D.Refused):
        call(pre + args(env, extra=extra))
    assert sha(env["out"]) == before


def test_main_exit_code_on_refusal(env, capsys):
    assert D.main(args(env, state="VERIFIED")) == 2
    assert "T741 REFUSED: state 'VERIFIED'" in capsys.readouterr().err
    assert not env["out"].exists()


# ---- the T-734 record (L-636fd3ff on V3.0.74) through this path, on a stand-in line ---------------------------------

def test_t734_draft_dry_run_on_a_stand_in_line(env, capsys):
    """research/agents_t741/t741_v3074_dryrun.py: the committed T-734 draft fields pass the entry unchanged; the line
    is RELEASED 115.832 m2 on the V3.0.74 index; a stand-in line carrying that id and quantity (the real canonical lines
    are private) gives a HELD record binding 115.832, three evidence items, nothing written."""
    import t741_v3074_dryrun as P
    e = P.index_entry()
    assert (e["class"], e["measured_net"], e["unit"]) == ("RELEASED", 115.832, "m2")
    stand = ln("FIN.WP.ROOF", "2F-ROOF-STAND-IN", "m2", 115.832)
    stand["line_id"] = P.LINE
    lp = env["tmp"] / "stand_in_lines.json"
    lp.write_text(BL.dumps([stand] + lines()), encoding="utf-8")
    av = P.draft_args(lp, env["out"], run_token="20261112T140000-1-1", routine="Checker", verdict_commit="c0ffee12")
    assert D.main(av) == 0
    txt = capsys.readouterr().out
    rec = json.loads(txt.split("T741 DRY RUN")[0])
    assert rec["line_ids"] == [P.LINE] and rec["engine_qty"] == 115.832 and rec["state"] == "HELD"
    assert rec["candidate_version"] == "ARCH_TAKEOFF_V3.0.74" and len(rec["evidence"]) == 3
    assert not X.validate_downgrade(rec) and not env["out"].exists()
    # without lines: the Checker's command only, nothing written
    assert P.main(["--out", str(env["out"])]) == 0 and not env["out"].parent.exists()
    with pytest.raises(D.Refused, match="--out"):
        P.main(["--out", str(env["tmp"] / "x.json")])
