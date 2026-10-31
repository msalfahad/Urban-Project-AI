"""T-384: no freelancer rate in the PUBLIC repository; every currency figure is classified.

Normal: quantity lines (m2, m.l, pcs, kg), identifiers such as kd3, an f-string "{rate} KWD/m3" and the column name KWD
are not figures. Adverse: a figure before / after an English or Arabic dinar / fils token and a figure on a currency-named
key are found; a NEW research / tests / docs file carrying one is refused because the classified baseline does not list
it. Then the repository itself: no unlisted file, no FREELANCER class, the two T-380 lines are clean. The adverse
strings are assembled at run time so this file does not itself carry a currency figure.
"""

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t384")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("currency_guard")
KD, KWD, FILS = "K" + "D", "K" + "WD", "fi" + "ls"
AR_ABBR, AR_DINAR = "د" + ".ك", "دي" + "نار"


def test_normal_quantity_lines_are_not_figures():
    text = "\n".join([
        "FREELANCER_SHOWER = 11      # tiling labour, qty",
        "internal plaster 1,151.14 m2 net; corners 385.375 m.l; 44.19 t; 6 pcs",
        "k1, kd = S.kink_rows(F1, l1); k3, kd3 = S.kink_rows(f3, l3, 1.20, 2.30)",
        'f"Concrete is priced at {rate} ' + KWD + '/m3"',
        "STEP_GROUP,STEP_ID,STEP,M3," + KWD + ",CLASS",
        "/tmp/urban_rebuild_tmizlhkd/task-T-202",
    ])
    assert G.scan_text(text) == []


def test_adverse_currency_figures_are_found_on_their_lines():
    lines = [
        "tiling labour 11 qty x 15 " + KD,
        "rate 2.50 " + KWD + "/m2",
        KWD + " 2,042.50 total",
        "4,200.000 " + AR_ABBR,
        "250 " + FILS + " per piece",
        "30 " + AR_DINAR,
        '"rate_' + KWD.lower() + '": 3.0,',
        "amount_" + KWD.lower() + " = 117.5",
        "1,300 m.l x 1.25 " + "K." + "D. each",
    ]
    hits = G.scan_text("\n".join(lines))
    assert [n for n, _ in hits] == list(range(1, len(lines) + 1))
    assert {k for _, k in hits} == {"NUMBER_THEN_TOKEN", "TOKEN_THEN_NUMBER", "CURRENCY_KEY_VALUE"}


def test_new_file_with_a_rate_is_refused_and_a_quantity_file_passes(tmp_path):
    (tmp_path / "research" / "agents_t999").mkdir(parents=True)
    (tmp_path / "tests" / "t999_x").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "research" / "agents_t999" / "report.md").write_text("shower 11 qty at 15 " + KD + " each\n", "utf-8")
    (tmp_path / "tests" / "t999_x" / "test_q.py").write_text("QTY_M2 = 72.01  # wet floors\n", "utf-8")
    (tmp_path / "docs" / "note.md").write_text("no figures here\n", "utf-8")
    found = G.scan_tree(str(tmp_path))
    assert list(found) == ["research/agents_t999/report.md"]
    assert G.unlisted(found, {"files": {}}) == ["research/agents_t999/report.md"]
    # listing it in a baseline is the only way through, and a listing must carry a class
    assert G.unlisted(found, {"files": {"research/agents_t999/report.md": {"class": "PUBLIC"}}}) == []


def test_binary_and_non_text_files_are_ignored(tmp_path):
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "x.xlsx").write_bytes(("15 " + KD).encode())
    (tmp_path / "research" / "y.md").write_bytes(b"\xff\xfe\x00broken")
    assert G.scan_tree(str(tmp_path)) == {}


def test_repository_has_no_unlisted_currency_figure_and_no_freelancer_class():
    base = G.load_baseline()
    found = G.scan_tree(ROOT)
    assert G.unlisted(found, base) == [], "currency figure in an unclassified file: remove it or classify it (T-384)"
    assert all(v["class"] in ("OWNER", "PUBLIC") for v in base["files"].values())
    assert set(base["classes"]) == {"FREELANCER", "OWNER", "PUBLIC"}


def test_the_t380_rate_is_gone():
    for rel, line in (("research/agents_t380/T-380_DRAINAGE_SOURCE_CENSUS.md", 100),
                      ("research/agents_t380/t380_alsenan.py", 143)):
        path = os.path.join(ROOT, rel)
        assert G.scan_file(path) == []
        with open(path, encoding="utf-8") as fh:
            assert "11" in fh.read().splitlines()[line - 1]   # the quantity stays
