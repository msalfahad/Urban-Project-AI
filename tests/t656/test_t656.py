"""T-656 (F-T653-1): research/agents_t627 computes in its OWN local 40-digit Decimal context.

Before T-656, t627_alsenan / t627_rules never set a context: they ran at 40 digits only through t568's old import side
effect (removed by T-653), so after T-653 they ran at the caller's precision: byte-identical at the default 28, an
InvalidOperation at an adverse prec 6. These tests pin: (1) the committed outputs rebuild sha256-identical to the
pre-T-656 build (the T-653 pin) at prec 28 AND at prec 6 set before the import; (2) importing the modules never changes
the caller's precision; (3) every own function runs at 40 inside and restores the caller; (4) the old pattern (the
unwrapped function at prec 6) really fails, so the wrapper is what makes the difference; (5) t627_extract.q3 (its only
Decimal arithmetic) gives the same text as before at the default context and no longer depends on the caller; (6) one
session, t568 then t627 and t627 then t568, same outputs.
"""
from __future__ import annotations

import decimal
import importlib
import inspect
import json
import subprocess
import sys
import types
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
T627 = ROOT / "research" / "agents_t627"
sys.path.insert(0, str(ROOT / "research" / "agents_t653"))
import t653_rebuild as RB  # noqa: E402

# sha256 of the t627 outputs on the base tree e04d99d9 (before T-656) at the default context = the T-653 pin (2e80c03f)
PIN = {"T627_ROW_EVIDENCE.json": "491f2f7fbfbf2208d4a5793224364b21e2ffb072b335886411a6b638bddf81bf",
       "T627_ROW_EVIDENCE.md": "7cb60e0581255964e0bb77c6ab6b18e539cbfab231710de998c016d534270ebd"}


def _child(code: str, pre: str = "") -> str:
    r = subprocess.run([sys.executable, "-I", "-B", "-c", pre + code], capture_output=True, text=True, cwd=ROOT,
                       timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout.strip().splitlines()[-1]


@pytest.mark.parametrize("mode,prec", [("default", 28), ("prec6", 6)])
def test_outputs_sha256_identical_before_after_at_28_and_at_adverse_6(mode, prec):
    r = RB.run_one(ROOT, "t627", mode)
    assert r["error"] is None, r["error"]
    assert r["prec_before"] == prec and r["prec_after_import"] == prec and r["prec_after_build"] == prec
    got = {o["output"]: o for o in r["outputs"]}
    assert set(got) == set(PIN)
    for name, sha in PIN.items():
        assert got[name]["rebuilt_sha256"] == sha, (mode, name)
        assert got[name]["committed_sha256"] == sha and got[name]["equal_committed"] is True, (mode, name)


ORDER = (
    "import sys, decimal, importlib, json, hashlib\n"
    "root = %r\n"
    "for f in ('agents_t568', 'agents_t627'):\n"
    "    sys.path.insert(0, root + '/research/' + f)\n"
    "seen = []\n"
    "for m in %r:\n"
    "    importlib.import_module(m)\n"
    "    seen.append(decimal.getcontext().prec)\n"
    "B = importlib.import_module('t627_alsenan')\n"
    "b = B.build()\n"
    "print(json.dumps({'prec': seen + [decimal.getcontext().prec],\n"
    "                  'json': hashlib.sha256(B.dumps(b).encode()).hexdigest(),\n"
    "                  'md': hashlib.sha256(B.render_md(b).encode()).hexdigest()}))\n"
)


@pytest.mark.parametrize("pre,prec", [("", 28), ("import decimal; decimal.getcontext().prec = 6\n", 6)])
@pytest.mark.parametrize("order", [["t568_rules", "t568_alsenan", "t627_rules", "t627_alsenan"],
                                   ["t627_rules", "t627_alsenan", "t568_rules", "t568_alsenan"]])
def test_one_session_both_import_orders_same_outputs(order, pre, prec):
    out = json.loads(_child(ORDER % (str(ROOT), order), pre=pre))
    assert out["prec"] == [prec] * 5
    assert out["json"] == PIN["T627_ROW_EVIDENCE.json"] and out["md"] == PIN["T627_ROW_EVIDENCE.md"]


def _mods():
    sys.path.insert(0, str(ROOT / "research" / "agents_t568"))
    sys.path.insert(0, str(T627))
    return importlib.import_module("t627_rules"), importlib.import_module("t627_alsenan")


def test_import_keeps_this_sessions_precision():
    before = decimal.getcontext().prec
    _mods()
    importlib.import_module("t627_extract")
    assert decimal.getcontext().prec == before


def test_every_own_function_runs_at_40_digits_and_restores_the_caller():
    R, B = _mods()
    assert R.PREC == 40
    for M in (R, B):
        own = {n: f for n, f in vars(M).items() if isinstance(f, types.FunctionType)
               and getattr(f, "__wrapped__", f).__module__ == M.__name__ and n not in ("ctx40", "in_prec40", "_wrap40")}
        assert len(own) >= 7, M.__name__
        for n, f in own.items():
            assert not inspect.isgeneratorfunction(getattr(f, "__wrapped__", f))
            assert getattr(f, "_t653_prec40", False), f"{M.__name__}.{n} is not in the local 40-digit context"
    with decimal.localcontext(decimal.Context(prec=6)):
        assert R.opening_area("1.40", "1.50") == Decimal("2.100000")
        assert decimal.getcontext().prec == 6


def test_adverse_the_unwrapped_function_fails_at_prec_6_the_wrapped_one_does_not():
    """the old behaviour, reproduced on purpose: the same rule function without its local context, called by a prec-6
    caller, cannot quantize an 8-digit area (12.3456 x 1.234 = 15.2344704 m2 -> 15.234470, 8 significant digits at Q6)."""
    R, _ = _mods()
    raw = R.opening_area.__wrapped__
    with decimal.localcontext(decimal.Context(prec=6)):
        with pytest.raises(decimal.InvalidOperation):
            raw("12.3456", "1.234")
        assert R.opening_area("12.3456", "1.234") == Decimal("15.234470")      # hand: 12.3456 x 1.234 = 15.2344704
        t = R.split_terms("1.40", "2.20", "1.40", "2.40")                         # hand: 0 and 1.40 x 0.20 = 0.28
        assert [x["qty"] for x in t] == [Decimal("0.000000"), Decimal("0.280000")]
    # a missing value is still refused, never 0, also inside the local context
    with pytest.raises(R.RuleError):
        R.opening_area("0", "2.20")


@pytest.mark.parametrize("x,want", [(1.2345, "1.234"), (2.2, "2.200"), (-0.0005, "-0.000"), (162.3456789, "162.346"),
                                    (162345.6789, "162345.679"), (6.332, "6.332")])
def test_extract_q3_same_text_as_before_and_independent_of_the_caller(x, want):
    sys.path.insert(0, str(T627))
    X = importlib.import_module("t627_extract")
    # before T-656 (the default context, prec 28): the reference text
    with decimal.localcontext(decimal.Context(prec=28)):
        ref = str(Decimal(repr(float(x))).quantize(Decimal("0.001")))
        assert X.q3(x) == ref == want
    with decimal.localcontext(decimal.Context(prec=6)):
        assert X.q3(x) == want                            # adverse caller: same text
        assert decimal.getcontext().prec == 6
        if len(want.replace("-", "").replace(".", "").lstrip("0")) > 6:
            with pytest.raises(decimal.InvalidOperation):   # the old line at prec 6 fails on a 9-digit value
                Decimal(repr(float(x))).quantize(Decimal("0.001"))
