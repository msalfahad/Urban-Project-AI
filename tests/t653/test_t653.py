"""T-653 (F-T648-2): no research module changes the process-global Decimal context.

Before T-653, 18 merged research modules set getcontext().prec = 40 at import and one S6 review script set 50; whichever
was imported last changed every later Decimal result in the same process (t647 / t649 failed in a full session).
These tests pin: (1) importing every module leaves the caller's precision as it was (the t158 pattern); (2) the
modules still compute at 40 digits inside their own functions, also when the caller's context is prec 6 (adverse);
(3) every output they rebuild is byte-identical to the rebuild before T-653 (sha256 pinned from the base tree
2e80c03f) and to the committed file; (4) a source guard: no module under research/, engine/ or tools/ assigns the
global context again.
"""
from __future__ import annotations

import decimal
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t653"))
import t653_rebuild as RB  # noqa: E402

RULES = {  # folder -> the module that used to set the global precision at import
    "t543": "t543_reconcile", "t550": "t550_parapet_split", "t559": "t559_rules", "t568": "t568_rules",
    "t573": "t573_rules", "t574": "t574_rules", "t577": "t577_rules", "t578": "t578_rules", "t584": "t584_rules",
    "t585": "t585_rules", "t592": "t592_rules", "t598": "edge_classes", "t602": "t602_rules", "t607": "t607_rules",
    "t618": "t618_rules", "t645": "t645_rules", "t646": "t646_rules",
}
BUILDERS = {k: f"{k}_alsenan" for k in RULES if k != "t598"}   # t598_alsenan has no Decimal arithmetic of its own

# sha256 of every rebuilt output on the base tree 2e80c03f (before T-653), research/agents_t653/t653_rebuild.py
BEFORE = {
    ("eval_fixtures", "A_FIXTURE_RESULTS.json"): "b1f4a14346d7bef2649fc6b78e6868c2d7c9acea65c38e6f38b4aa9fb47303ed",
    ("t543", "T543_BLOCKWORK_RECONCILE.json"): "a4cfcdeb01aab26e38b543fa73c89c2999b54cbad85916d9fe6023aa0af4f721",
    ("t550", "T550_UNRESOLVED_RESTATED.json"): "499544802db1bab767099c07dc6a48d6ee2c3f950659656616e45b8e17412a12",
    ("t559", "T559_LEFTOVER.json"): "09ad09899c03d3fa3cfae4b88a54eece349d3a3e6625a08b2c6c1638d0eb4f10",
    ("t568", "T568_TYPE_TABLE.json"): "5f94998d667ff552116a46b394bc36e8f25739afbe2b3fa1af4152bb00e39a6c",
    ("t573", "T573_CEILING_RECONCILE.json"): "447804a48e21142e5d0eeffda8517300ab595791a11b599a7b1af74dbf3dcdbf",
    ("t574", "T574_SKIRTING_RECONCILE.json"): "7b1e01bf83c20702bad3ed58689915c57bac5e3a179bf33195816c67435abab8",
    ("t577", "T577_MARBLE_RECONCILE.json"): "b1b684a3478982b7c80d6f25a6acf0c8dea4dfaa80449f0866e373cee2ddb320",
    ("t578", "T578_RAIL_NOSING_RECONCILE.json"): "75172951bf95cfdd8a857a42c43521daa088a6a210cf95483d18c3fca3432158",
    ("t584", "T584_STEPS.json"): "242b8e0d3fdbf271b08b0f2bf1569ce21193f9b560603ee48ccdc8bf018a68b9",
    ("t585", "T585_SKIRTING_FOLLOWUPS.json"): "207d4c6a35172786a54caaa1732351cac23947ed3e69228fb815a8538361bb7e",
    ("t592", "T592_DOOR_STEPS.json"): "c32be0ed6d17ff05e3a116fafb3c0bb241a90d9cdfaf602877e16977e256f689",
    ("t598", "ALSENAN_EDGES_T598.json#result"): "775785dcfd595c63b197f96108034ab58d0c47ee0026fda27579ae6800d22686",
    ("t598", "ALSENAN_EDGES_T598.json#result==committed"): "3cbc87c7681f34db4617feaa2c8801931bc5e42d8d0f560e756dd4cd92885f18",
    ("t602", "T602_DOOR_STEPS.json"): "c7cb2f106e7b2039482582c7b95688fd003368928b38b04d325b79f1cc92db40",
    ("t607", "T607_SHARED_RESIDUAL.json"): "7a8867153e6d885b3d258e4347ac9851022cdc7d87f60f4e63e829efbee129a2",
    ("t618", "T618_RESIDUALS.json"): "3ca6790cf6378e2221d57fabbb7b775566fd27a0fea80b0b18190dcc8a0ef49f",
    ("t627", "T627_ROW_EVIDENCE.json"): "491f2f7fbfbf2208d4a5793224364b21e2ffb072b335886411a6b638bddf81bf",
    ("t627", "T627_ROW_EVIDENCE.md"): "7cb60e0581255964e0bb77c6ab6b18e539cbfab231710de998c016d534270ebd",
    ("t645", "STAIR_HOLD_CENSUS_T645.json"): "3e1384ee4e84bf9ed74a976e3a27170aad0fe4b049d76708cfe7dc3f60fe9629",
    ("t645", "STAIR_HOLD_CENSUS_T645.md"): "2181c92dd8ed82ffb0e0aa25f14fc2feaa9bf0f20dbaaa9fac8fb7c41de9f664",
    ("t646", "ROOF_FENCE_HOLD_CENSUS_T646.json"): "fd4988c7f2f9cf0d187a1eebaf57897c640ea3a0114d98314cc4f6fe9c4197cf",
    ("t646", "ROOF_FENCE_HOLD_CENSUS_T646.md"): "03f1c267408eff460969b5ca5dc020e532f496ed061020a54e89827405579d79",
}
# t559 / t568 rebuild their freelancer tables only from private inputs (.work/private); the pinned sha is the rebuild
# WITHOUT them (the committed file holds the private-input build, so it is not compared there)
PRIVATE = {"t559": ROOT.parent / "private" / "t559" / "his_openings.json",
           "t568": ROOT.parent / "private" / "alum.xlsx"}


def _child(code: str, pre: str = "") -> str:
    r = subprocess.run([sys.executable, "-I", "-B", "-c", pre + code], capture_output=True, text=True, cwd=ROOT,
                       timeout=300)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout.strip().splitlines()[-1]


IMPORT_ALL = (
    "import sys, decimal, importlib, json\n"
    "root = %r\n"
    "seen = []\n"
    "for k, m in %r:\n"
    "    sys.path.insert(0, root + '/research/agents_' + k)\n"
    "    importlib.import_module(m)\n"
    "    seen.append([m, decimal.getcontext().prec])\n"
    "print(json.dumps(seen))\n"
)


def _pairs():
    return [[k, m] for k, m in RULES.items()] + [[k, m] for k, m in BUILDERS.items()]


def test_normal_importing_every_module_keeps_the_callers_precision():
    seen = json.loads(_child(IMPORT_ALL % (str(ROOT), _pairs())))
    assert len(seen) == len(RULES) + len(BUILDERS) == 33
    assert all(p == 28 for _, p in seen), [s for s in seen if s[1] != 28]


def test_adverse_caller_at_prec_6_keeps_prec_6_after_every_import():
    seen = json.loads(_child(IMPORT_ALL % (str(ROOT), _pairs()), pre="import decimal; decimal.getcontext().prec = 6\n"))
    assert all(p == 6 for _, p in seen), [s for s in seen if s[1] != 6]


def test_in_process_import_does_not_touch_this_sessions_context():
    """the t158 pattern, in the pytest process itself"""
    before = decimal.getcontext().prec
    for k, m in _pairs():
        sys.path.insert(0, str(ROOT / "research" / f"agents_{k}"))
        importlib.import_module(m)
    assert decimal.getcontext().prec == before


@pytest.mark.parametrize("key", sorted(RULES))
def test_every_function_runs_at_40_digits_and_restores_the_caller(key):
    sys.path.insert(0, str(ROOT / "research" / f"agents_{key}"))
    mods = [importlib.import_module(RULES[key])] + ([importlib.import_module(BUILDERS[key])] if key in BUILDERS else [])
    R = mods[0]
    assert R.PREC == 40
    import inspect
    import types
    for M in mods:
        own = {n: f for n, f in vars(M).items() if isinstance(f, types.FunctionType) and
               getattr(f, "__wrapped__", f).__module__ == M.__name__ and n not in ("ctx40", "in_prec40", "_wrap40")}
        assert own, M.__name__
        for n, f in own.items():
            if inspect.isgeneratorfunction(getattr(f, "__wrapped__", f)):
                continue
            assert getattr(f, "_t653_prec40", False), f"{M.__name__}.{n} does not run in the local 40-digit context"
    # the mechanism, on a synthetic module namespace: a caller at prec 6 sees 40 inside, 6 again after
    ns = {"__name__": "t653_probe"}
    exec("import decimal\ndef probe():\n    return decimal.getcontext().prec, decimal.Decimal(1) / decimal.Decimal(7)\n"
         "def gen():\n    yield decimal.getcontext().prec\n", ns)
    for f in ("probe", "gen"):
        ns[f].__module__ = "t653_probe"
    R.in_prec40(ns)
    with decimal.localcontext(decimal.Context(prec=6)):
        prec, q = ns["probe"]()
        assert prec == 40 and len(q.as_tuple().digits) == 40
        assert decimal.getcontext().prec == 6
        assert next(ns["gen"]()) == 6          # generators are left alone (a wrapper would exit before they run)
    assert not getattr(ns["gen"], "_t653_prec40", False)


@pytest.fixture(scope="module")
def ledger():
    return RB.ledger(ROOT)


@pytest.mark.parametrize("mode,prec", [("default", 28), ("prec6", 6)])
def test_every_rebuilt_output_is_byte_identical_to_before(ledger, mode, prec):
    seen = set()
    for key, modes in ledger.items():
        r = modes[mode]
        assert r["error"] is None, (key, mode, r["error"])
        assert r["prec_after_build"] == prec, (key, mode, r["prec_after_build"])
        for o in r["outputs"]:
            seen.add((key, o["output"]))
            if key in PRIVATE and PRIVATE[key].exists():
                continue
            assert o["rebuilt_sha256"] == BEFORE[(key, o["output"])], (key, mode, o["output"])
            if key not in PRIVATE and o["committed_sha256"] is not None:
                assert o["equal_committed"], (key, mode, o["output"])
            if o["output"].endswith("==committed"):
                assert o["text"] == "True"
    assert seen == set(BEFORE)   # T-656: t627 is compared at prec 6 too (it skipped prec 6 before F-T653-1 was fixed)


def test_t627_consumer_note(ledger):
    """t627_alsenan imports t568_alsenan and never set a context of its own: before T-653 it computed at 40 only through
    t568's import side effect, and after T-653 at the caller's precision (an adverse prec 6 failed: finding F-T653-1).
    T-656 gave it its own local 40-digit context (tests/t656): both modes now rebuild the pinned bytes."""
    for mode, prec in (("default", 28), ("prec6", 6)):
        r = ledger["t627"][mode]
        assert r["error"] is None, (mode, r["error"])
        assert r["prec_after_build"] == prec
        assert all(o["rebuilt_sha256"] == BEFORE[("t627", o["output"])] and o["equal_committed"] for o in r["outputs"])


# the rebuild ledger sets prec 6 only inside the CHILD processes it spawns (the adverse caller), never in its own
GUARD_EXEMPT = {"research/agents_t653/t653_rebuild.py"}
GLOBAL_SET = re.compile(r"getcontext\(\)\s*\.\s*\w+\s*=(?!=)|\bsetcontext\s*\(|DefaultContext\s*\.\s*\w+\s*=(?!=)")


def _code_lines(path: Path):
    in_doc = False
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        s = line.strip()
        if s.count('"""') == 1 or s.count("'''") == 1:
            in_doc = not in_doc
            continue
        if in_doc or s.startswith("#"):
            continue
        yield i, line.split("#", 1)[0]


def test_source_guard_no_module_assigns_the_global_decimal_context():
    hits = []
    for top in ("research", "engine", "tools"):
        for p in sorted((ROOT / top).rglob("*.py")):
            if "__pycache__" in p.parts or p.relative_to(ROOT).as_posix() in GUARD_EXEMPT:
                continue
            for i, code in _code_lines(p):
                if GLOBAL_SET.search(code):
                    hits.append(f"{p.relative_to(ROOT)}:{i}")
    assert hits == [], hits


def test_source_guard_catches_the_old_pattern(tmp_path):
    """adverse: the guard really fires on the pre-T-653 line and on its variants"""
    for bad in ("getcontext().prec = 40", "decimal.getcontext().prec=50", "setcontext(Context(prec=40))",
                "decimal.getcontext().rounding = ROUND_DOWN", "    getcontext().prec = 40  # inside a function"):
        f = tmp_path / "m.py"
        f.write_text("from decimal import *\n" + bad + "\n")
        assert any(GLOBAL_SET.search(c) for _, c in _code_lines(f)), bad
    for ok in ("with localcontext(Context(prec=40)):", "before = decimal.getcontext().prec",
               "assert decimal.getcontext().prec == before", "# getcontext().prec = 40 (old)"):
        f = tmp_path / "m.py"
        f.write_text(ok + "\n")
        assert not any(GLOBAL_SET.search(c) for _, c in _code_lines(f)), ok
