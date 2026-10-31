"""T-370: sanitary fixtures and floor drains as a count (B12-01), two sources reconciled fixture by fixture.

Normal case: a two-storey villa that is not Alsenan, counted by hand. Adverse: a fixture counted from both sources
twice, a symbol type guessed from the room name, a drain inferred from a fall, a link across rooms, a conflict or an
unknown added to the drawn count, order / mirror independence. Then the committed Alsenan register (no private file).
"""

import importlib.util
import json
import os
import sys
import unicodedata

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t370")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t370_fixture_rules")
A = _load("t370_alsenan")
S, L = R.BASIS_SYMBOL, R.BASIS_LEGEND

# --- a villa that is not Alsenan -------------------------------------------------------------------------------
# GF guest WC   : arch WC block 'A1' + san WC 'S1' at the same place (one WC), san FD 'S2'
# GF bathroom   : arch draws a TUB 'A2'; the sanitary sheet draws a shower TRAY 'S3' at the same position -> CONFLICT;
#                 arch basin 'A3' (not on the sanitary sheet) -> ARCH_ONLY; san FD 'S4'
# GF kitchen    : arch sink 'A4' + san sink 'S5' (one sink); no drain
# 1F bathroom   : san WC 'S6', san basin 'S7', san FD 'S8'; arch draws nothing (tag only)
# 1F roof       : two rain-water outlets 'S9', 'S10' (separate population)
# Hand count: WC 2 (1 AGREE + 1 SAN_ONLY); BASIN 2 (1 ARCH_ONLY + 1 SAN_ONLY); SINK 1 (AGREE); FLOOR_DRAIN 3;
#             ROOF_DRAIN 2; CONFLICT 1 (tub vs tray, neither counted); drawn fixtures 5, never 6.


def _villa():
    arch = [
        R.Item(R.ARCH, "A1", "GF", "guest wc", R.WC, S),
        R.Item(R.ARCH, "A2", "GF", "bath", R.BATH_TUB, S),
        R.Item(R.ARCH, "A3", "GF", "bath", R.BASIN, S),
        R.Item(R.ARCH, "A4", "GF", "kitchen", R.SINK, S),
    ]
    san = [
        R.Item(R.SAN, "S1", "GF", "guest wc", R.WC, S),
        R.Item(R.SAN, "S2", "GF", "guest wc", R.FLOOR_DRAIN, L),
        R.Item(R.SAN, "S3", "GF", "bath", R.SHOWER_TRAY, S),
        R.Item(R.SAN, "S4", "GF", "bath", R.FLOOR_DRAIN, L),
        R.Item(R.SAN, "S5", "GF", "kitchen", R.SINK, S),
        R.Item(R.SAN, "S6", "1F", "bath 2", R.WC, S),
        R.Item(R.SAN, "S7", "1F", "bath 2", R.BASIN, S),
        R.Item(R.SAN, "S8", "1F", "bath 2", R.FLOOR_DRAIN, L),
        R.Item(R.SAN, "S9", "1F", "roof", R.ROOF_DRAIN, L),
        R.Item(R.SAN, "S10", "1F", "roof", R.ROOF_DRAIN, L),
    ]
    links = [("A1", "S1"), ("A2", "S3"), ("A4", "S5")]
    return arch, san, links


def test_villa_hand_count():
    arch, san, links = _villa()
    t = R.totals(R.reconcile(arch, san, links))
    assert t[R.WC] == {"drawn": 2, "AGREE": 1, "ARCH_ONLY": 0, "SAN_ONLY": 1}
    assert t[R.BASIN] == {"drawn": 2, "AGREE": 0, "ARCH_ONLY": 1, "SAN_ONLY": 1}
    assert t[R.SINK] == {"drawn": 1, "AGREE": 1, "ARCH_ONLY": 0, "SAN_ONLY": 0}
    assert t[R.FLOOR_DRAIN]["drawn"] == 3
    assert t[R.ROOF_DRAIN]["drawn"] == 2
    assert t[R.CONFLICT] == 1
    assert R.BATH_TUB not in t and R.SHOWER_TRAY not in t           # the conflict is in neither kind
    drawn_fixtures = sum(v["drawn"] for k, v in t.items() if k in R.FIXTURE_KINDS)
    assert drawn_fixtures == 5


def test_villa_per_floor():
    arch, san, links = _villa()
    c = R.counts(R.reconcile(arch, san, links))
    assert c[R.WC]["GF"]["drawn"] == 1 and c[R.WC]["1F"]["drawn"] == 1
    assert c[R.FLOOR_DRAIN]["GF"]["drawn"] == 2 and c[R.FLOOR_DRAIN]["1F"]["drawn"] == 1
    assert c[R.CONFLICT]["GF"] == {"held": 1}


def test_conflict_keeps_both_types_named():
    arch, san, links = _villa()
    conf = [e for e in R.reconcile(arch, san, links) if e.status == R.CONFLICT]
    assert len(conf) == 1 and conf[0].kind == "BATH_TUB|SHOWER_TRAY"
    assert conf[0].arch.ref == "A2" and conf[0].san.ref == "S3"


def test_order_and_mirror_independent():
    # a mirrored / rotated sheet changes positions, not the reading; the register order must not change a count
    arch, san, links = _villa()
    t1 = R.totals(R.reconcile(arch, san, links))
    t2 = R.totals(R.reconcile(list(reversed(arch)), list(reversed(san)), list(reversed(links))))
    assert dict(t1) == dict(t2)


# --- adverse ---------------------------------------------------------------------------------------------------

def test_fixture_from_both_sources_unlinked_is_two_not_silently_one_and_relink_refused():
    arch, san, _ = _villa()
    # without the link the same WC is ARCH_ONLY + SAN_ONLY: the register shows it twice, so the reader must link it
    t = R.totals(R.reconcile(arch, san, []))
    assert t[R.WC]["ARCH_ONLY"] == 1 and t[R.WC]["SAN_ONLY"] == 2
    # one sanitary WC linked to two architectural items: refused (one fixture counted twice)
    arch2 = arch + [R.Item(R.ARCH, "A9", "GF", "guest wc", R.WC, S)]
    with pytest.raises(R.FixtureRefused):
        R.reconcile(arch2, san, [("A1", "S1"), ("A9", "S1")])


def test_same_item_listed_twice_refused():
    arch, san, links = _villa()
    with pytest.raises(R.FixtureRefused):
        R.reconcile(arch, san + [san[0]], links)


def test_symbol_type_guessed_refused():
    with pytest.raises(R.FixtureRefused):
        R.Item(R.SAN, "X1", "GF", "bath", R.BATH_TUB, "ROOM_NAME")      # 'it is called BATH, so a tub'
    with pytest.raises(R.FixtureRefused):
        R.Item(R.SAN, "X2", "GF", "wc", R.SHATTAF, "PRACTICE")           # 'every Kuwaiti WC has one'


def test_drain_inferred_from_fall_refused():
    with pytest.raises(R.FixtureRefused):
        R.Item(R.SAN, "X3", "GF", "terrace", R.FLOOR_DRAIN, "FALL_ARROW")


def test_link_across_rooms_refused():
    arch, san, _ = _villa()
    with pytest.raises(R.FixtureRefused):
        R.reconcile(arch, san, [("A3", "S7")])                             # GF bath basin vs 1F bath basin


def test_unknown_never_counted():
    arch, san, links = _villa()
    san = san + [R.Item(R.SAN, "U1", "GF", "guest wc", R.UNKNOWN, S, "valve symbol not in the legend")]
    t = R.totals(R.reconcile(arch, san, links))
    assert t[R.UNKNOWN] == 1
    assert sum(v["drawn"] for k, v in t.items() if k in R.FIXTURE_KINDS) == 5


def test_wet_room_check():
    arch, san, links = _villa()
    e = R.reconcile(arch, san, links)
    cls = {("GF", "guest wc"): "WET", ("GF", "kitchen"): "WET", ("1F", "bath 2"): "WET",
           ("1F", "store"): "WET", ("GF", "lobby"): "DRY", ("1F", "roof"): "DRY"}
    no_fix, drain_only, in_dry = R.wet_room_check(e, cls)
    assert no_fix == [("1F", "store")]
    assert drain_only == []
    assert in_dry == []                                                   # a roof drain is not a fixture
    e2 = R.reconcile(arch + [R.Item(R.ARCH, "A7", "GF", "lobby", R.BASIN, S)], san, links)
    assert R.wet_room_check(e2, cls)[2] == [("GF", "lobby")]


# --- Alsenan register (committed reading; no private file) ------------------------------------------------------

def test_alsenan_totals():
    entries, t, _ = A.run()
    assert t[R.WC] == {"drawn": 12, "AGREE": 0, "ARCH_ONLY": 0, "SAN_ONLY": 12}
    assert t[R.BASIN] == {"drawn": 17, "AGREE": 5, "ARCH_ONLY": 0, "SAN_ONLY": 12}
    assert t[R.SHOWER_TRAY]["drawn"] == 3 and t[R.SHOWER_WALKIN]["drawn"] == 3
    assert t[R.FLOOR_DRAIN]["drawn"] == 19 and t[R.ROOF_DRAIN]["drawn"] == 5
    assert t[R.UNKNOWN] == 1 and R.CONFLICT not in t
    for k in (R.BATH_TUB, R.SINK, R.BIDET, R.SHATTAF):
        assert k not in t                                                  # printed nowhere: never inferred


def _guard():
    spec = importlib.util.spec_from_file_location(
        "provenance_guard", os.path.join(ROOT, "research", "agents_t386", "provenance_guard.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["provenance_guard"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_alsenan_benchmarks_are_the_cost_record_not_the_freelancer():
    # T-389 (R-T386-1, ERS s.2.4): the four benchmark rows are Urban's own cost record, keyed by register id; none has
    # a freelancer source cell; the counted ones are UNRESOLVED scope, never a residual of the drawn count.
    G = _guard()
    rows = G.register_rows()
    assert not hasattr(A, "FREELANCER")
    assert A.COST_RECORD_SOURCE["source_class"] == "URBAN_COST_RECORD"
    with open(os.path.join(ROOT, G.MANIFEST), encoding="utf-8") as fh:
        kinds = {f["key"]: f["kind"] for f in json.load(fh)["files"]}
    assert G.source_class(kinds[A.COST_RECORD_SOURCE["manifest_key"]]) == "URBAN_COST_RECORD"
    assert set(A.COST_RECORD) == {"WEB-018", "WEB-019", "WEB-055", "WEB-060"}
    for rid, rec in A.COST_RECORD.items():
        r = rows[rid]
        assert r["source_freelancer_items"] == [] and r["freelancer_qty"] is None
        assert rec["kind"] == r["mapping_class"] and rec["qty"] == r["qty"] and rec["unit"] == r["unit"]
        assert set(rec) == {"what", "kind", "qty", "unit", "comparison"}            # quantities only: no rate
        with pytest.raises(ValueError):
            G.comparison_class("FREELANCER", r, basis_known=True)                   # offered as his: refused
    for rid in ("WEB-018", "WEB-019"):
        assert G.comparison_class("URBAN_COST_RECORD", rows[rid], basis_known=False) == "UNRESOLVED_SCOPE"
        assert A.COST_RECORD[rid]["comparison"].startswith("UNRESOLVED_SCOPE")
    assert A.B12_01_FREELANCER.startswith("NOT_COMPARABLE")
    # the freelancer's own rows hold no fixture / drain count (B12-01 NOT COMPARABLE)
    with open(os.path.join(ROOT, "tests", "alsenan", "registers_b1", "FREELANCER_RAW_ROWS.json"), encoding="utf-8") as fh:
        raw = unicodedata.normalize("NFKC", fh.read())
    for word in ("صفاي", "شاور", "drain", "shower", "sanitary"):
        assert word not in raw.lower()


def test_alsenan_drawn_counts_do_not_rest_on_the_cost_record():
    # normal: the drawn counts are what the drawings print, whatever the cost record says
    _, t, _ = A.run()
    assert t[R.FLOOR_DRAIN]["drawn"] == 19 and t[R.ROOF_DRAIN]["drawn"] == 5
    assert t[R.SHOWER_TRAY]["drawn"] + t[R.SHOWER_WALKIN]["drawn"] == 6
    # adverse: a cost-record figure is never adopted as a drawn count (24 is not the B12-01 floor-drain count)
    assert t[R.FLOOR_DRAIN]["drawn"] != A.COST_RECORD["WEB-019"]["qty"]


def test_t370_files_carry_no_provenance_hit_and_the_old_label_is_refused():
    G = _guard()
    for rel in ("research/agents_t370/T-370_SANITARY_FIXTURE_REGISTER.md", "research/agents_t370/t370_alsenan.py",
                "research/agents_t370/t370_fixture_rules.py"):
        assert G.scan_file(os.path.join(ROOT, rel)) == []
    assert G.load_baseline()["files"] == {}
    # adverse: re-adding the old labels (assembled here so this file does not match itself) is found and refused
    fl, bycat, grat = "free" + "lancer", "Chalet_by" + "_category.xlsx", "تركيب " + "صفايات"
    old = "\n".join(["The only " + fl + " file with sanitary content is '" + bycat + "'",
                     "| floor gratings fixed ('" + grat + "') | 24 qty | the " + fl + " counts every grating |"])
    assert [k for _, k in G.scan_text(old)] == ["COST_RECORD_FILE_AS_FREELANCER", "COST_RECORD_ROW_AS_FREELANCER"]
    found = {"research/agents_t370/T-370_SANITARY_FIXTURE_REGISTER.md": G.scan_text(old)}
    assert G.unlisted(found, G.load_baseline()) == ["research/agents_t370/T-370_SANITARY_FIXTURE_REGISTER.md"]


def test_alsenan_wet_rooms():
    entries, _, _ = A.run()
    no_fix, drain_only, in_dry = R.wet_room_check(entries, A.ROOM_CLASS)
    assert no_fix == [] and in_dry == []
    assert drain_only == [("GF", A.GF_KITCHEN)]
