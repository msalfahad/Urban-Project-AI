"""T-130: BOQ_FAMILY_MASTER 1.1.0 (rules/coverage/) - the family registry re-derived from the code and the runs.

Checks the file only (it is read by no engine module yet: the census and rule_store keep 1.0.0, so no run changes):
the same 99 families as 1.0.0 with their names / units untouched, every status in the registry's own vocabulary,
every status change carrying a file:line that resolves or a merge commit, every file:line in the evidence resolving
to an existing line, the V3.0 field in its vocabulary, development-villa figures that never turn a held line into a
quantity, and no benchmark (freelancer) number or client name in the rule store."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json"
OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json"
REF = re.compile(r"((?:engine|tools|tests|research|rules|knowledge)/[\w/.]+\.(?:py|json|md))(?::(\d+)(?:-(\d+))?)?")
COMMIT = re.compile(r"\b[0-9a-f]{7}\b")
UNITS = {"m", "m2", "m3", "lm", "pcs", "kg", "t", "nr", "item", "-"}


@pytest.fixture(scope="module")
def new():
    return json.loads(NEW.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def old():
    return json.loads(OLD.read_text(encoding="utf-8"))


def test_same_families_names_and_units_as_1_0_0(new, old):
    assert new["master"] == old["master"] and new["version"] == "1.1.0"
    assert new["capability_states"] == old["capability_states"]
    assert [f["code"] for f in new["families"]] == [f["code"] for f in old["families"]]
    for a, b in zip(new["families"], old["families"]):
        for k in ("group", "item_en", "item_ar", "unit", "source_needed", "next_slice"):
            assert a[k] == b[k], (a["code"], k)
        assert a["capability_1_0_0"] == b["capability"], a["code"]


def test_status_vocabulary_and_change_direction(new):
    rank = {s: i for i, s in enumerate(new["capability_states"])}
    assert set(new["capability_definitions"]) == set(rank)
    for f in new["families"]:
        assert f["capability"] in rank, f["code"]
        c0, c1 = rank[f["capability_1_0_0"]], rank[f["capability"]]
        want = "UNCHANGED" if c0 == c1 else ("RAISED" if c1 < c0 else "LOWERED")
        assert f["capability_change"] == want, f["code"]


SHORT = re.compile(r"(?<![\w/.]):(\d+)(?:-(\d+))?")          # ':123' after a full path cites the same file
SYM = re.compile(r"\s*(?:/\s*)?(\"[^\"]+\"|'[^']+'|[A-Za-z_][\w.]*(?:\(\))?)")


def _named_symbol(text, end):
    """r3 (verifier 2026-10-21 16:45): the symbol a citation names right after it - name(), a dotted or underscored
    name, an UPPER name or a quoted string; None when prose follows (such a citation names nothing)"""
    m = SYM.match(text, end)
    if not m:
        return None
    t = m.group(1)
    if t[0] in "\"'":
        return t[1:-1]
    t = t.rstrip(".")
    if t.endswith("()"):
        return t[:-2]
    return t if ("_" in t or "." in t or (t.isupper() and len(t) > 1)) else None


def _citations(text):
    """every line citation in a text: (path, first, last, symbol); a ':N' binds to the last full path before it"""
    full = [(m.start(), m.end(), m.group(1), m.group(2), m.group(3)) for m in REF.finditer(text)]
    short = [(m.start(), m.end(), None, m.group(1), m.group(2)) for m in SHORT.finditer(text)
             if not any(a <= m.start() < b for a, b, *_ in full)]
    last = None
    for st, en, path, a, b in sorted(full + short):
        last = path or last
        if a is not None:
            yield last, int(a), int(b or a), _named_symbol(text, en)


def _resolves(path, a, b, sym, root=ROOT):
    """the file exists, the lines exist, and the named symbol stands on the cited line or the next 2 (in a range:
    anywhere in it); a citation that names no symbol does not resolve"""
    p = root / path
    if not p.exists():
        return False
    lines = p.read_text(encoding="utf-8").splitlines()
    if not (1 <= a <= b <= len(lines)) or sym is None:
        return False
    return sym in "\n".join(lines[a - 1:max(b, a + 2)])


def _texts(new):
    for f in new["families"]:
        for text in f["evidence"] + [f["missing"], f.get("note", "")]:
            yield f["code"], text
    for text in new["census_gaps"] + [new["loaded_by"], new["released_configuration"]] + \
            list(new["item_codes_without_family"].values()):
        yield "top", text


def test_every_file_line_in_the_evidence_resolves(new):
    bad = []
    for code, text in _texts(new):
        bad += [(code, m.group(0)) for m in REF.finditer(text) if not (ROOT / m.group(1)).exists()]
        bad += [(code, c) for c in _citations(text) if not _resolves(*c)]
    assert not bad


def test_the_resolver_refuses_the_three_r2_citations():
    """the verifier's three wrong r2 lines (blank line, a line before the def, a blank line) and a prose citation
    fail; the corrected lines pass"""
    for text in ("engine/source/generic_route.py:2027 _lintel_items(): route G lintels",
                 "tools/struct_n10.py:42 build(): standalone tool",
                 "tests/m9_kb/test_kb_wp5.py:80 (drawn balcony: one PROVISIONAL membrane line)",
                 "engine/source/arch_measure.py:381 the room's clear floor area"):
        assert [c for c in _citations(text) if not _resolves(*c)], text
    for text in ("engine/source/generic_route.py:2030 _lintel_items(): route G lintels",
                 "tools/struct_n10.py:40 build(): standalone tool",
                 "tests/m9_kb/test_kb_wp5.py:81 test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed()",
                 "engine/source/generic_route.py:1374 _blinding_items(); :1448 PLAIN_CONCRETE in route G"):
        cs = list(_citations(text))
        assert cs and all(_resolves(*c) for c in cs), text
    # a short ':N' citation binds to the file before it and is checked on its own
    (_, c2), = [(None, c) for c in _citations("engine/source/generic_route.py:1374 _blinding_items(); :1449 "
                                              "PLAIN_CONCRETE") if c[1] == 1449]
    assert not _resolves(*c2)


def test_the_corrected_r2_citations(new):
    text = json.dumps(new, ensure_ascii=False)
    assert "generic_route.py:2030 _lintel_items()" in text and "generic_route.py:2028" not in text
    assert "tools/struct_n10.py:40 build()" in text and "tools/struct_n10.py:42" not in text
    assert "tests/m9_kb/test_kb_wp5.py:81 test_a_balcony_door" in text and "test_kb_wp5.py:80" not in text


def test_no_status_changes_without_a_file_line_or_a_commit(new):
    for f in new["families"]:
        if f["capability_change"] == "UNCHANGED":
            continue
        assert any(REF.search(e) and ":" in REF.search(e).group(0) or COMMIT.search(e) for e in f["evidence"]), f["code"]


def test_v3_0_field(new):
    for f in new["families"]:
        assert f["in_v3_0_candidate"] in ("yes", "no"), f["code"]
        assert all(re.fullmatch(r"T-\d{3}", t) for t in f["v3_0_planned_tasks"]), f["code"]
        if f["capability"] in ("NOT_IMPLEMENTED", "BLOCKED_BY_SOURCE", "EXPERIMENTAL"):
            assert f["in_v3_0_candidate"] == "no", f["code"]


def test_development_villa_figures_never_turn_held_into_a_quantity(new):
    for f in new["families"]:
        for run in ("released_run", "candidate_run_v2_13"):
            for r in f["development_villa"][run]:
                assert r["unit"] in UNITS and "," not in r["unit"], (f["code"], r)   # one unit per row, never mixed
                assert r["released_lines"] + r["held_lines"] + r["not_applicable_lines"] == r["lines"], (f["code"], r)
                if r["released_lines"] == 0:
                    assert r["released_qty"] == 0, (f["code"], r)                    # held lines add nothing
                lo, hi = r["held_bounded_low"], r["held_bounded_high"]
                assert (lo is None) == (hi is None) and (lo is None or 0 <= lo <= hi), (f["code"], r)


def test_status_and_run_agree_where_the_released_run_releases(new):
    """a family with released lines in the released run is at least PARTIAL; one the released route never reads is
    at most IMPLEMENTED_NOT_INTEGRATED"""
    rank = {s: i for i, s in enumerate(new["capability_states"])}
    for f in new["families"]:
        if any(r["released_lines"] for r in f["development_villa"]["released_run"]):
            assert rank[f["capability"]] <= rank["PARTIAL"], f["code"]
        if f["released_method_reads"].startswith("none") and f["code"] not in ("B9-05", "B11-02"):
            assert rank[f["capability"]] >= rank["IMPLEMENTED_NOT_INTEGRATED"], f["code"]


def test_the_engine_still_reads_1_0_0(new):
    from engine.source import rule_store as RS
    assert RS.family_master()["version"] == "1.0.0"          # adopting 1.1.0 is a census version of its own
    assert "1.0.0" in new["loaded_by"]


def test_no_benchmark_number_or_client_name_in_the_rule_store():
    text = NEW.read_text(encoding="utf-8")
    assert not re.search(r"(?i:als[ey]?n[ya]?an)|YEARS 2013|7757-[A-Z]", text)
    for n in ("44.19", "352.436075", "77.6305", "75.09", "39.7515", "65.965875", "59.8174", "21.8328", "12.348",
              "337.812", "333.173", "22.619", "22.916"):
        assert n not in text


# ------------------------------------------------------------------ r2 (verifier 2026-10-21 02:30: gate d / P-02)
CODE = re.compile(r"\"((?:STR|FIN|ARCH|MAS|DOOR)\.[A-Z0-9_.]*[A-Z0-9_])\"")
DECLARED_ONLY = ("engine/source/boq_line.py", "engine/source/coverage_census.py")   # the item master and the census map
DEF = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def _written_codes():
    files = [p for p in sorted((ROOT / "engine/source").rglob("*.py"))
             if p.relative_to(ROOT).as_posix() not in DECLARED_ONLY] + [ROOT / "tools/urban_boq_m9.py"]
    out = {}
    for p in files:
        for c in CODE.findall(p.read_text(encoding="utf-8")):
            out.setdefault(c, p.relative_to(ROOT).as_posix())
    return out


def _owners(new):
    own = {}
    for f in new["families"]:
        for c in f["item_codes"]:
            assert c not in own, (c, own.get(c), f["code"])                     # one family per code
            own[c] = f["code"]
    return own


def _unowned_written(doc, written=None):
    """{code: file} of every written item code that doc neither assigns to a family nor lists apart"""
    own, apart = _owners(doc), doc["item_codes_without_family"]
    written = _written_codes() if written is None else written
    return {c: p for c, p in written.items() if c not in own and c not in apart}


def _not_implemented_hits(doc, written=None):
    """[(family, code or term, ...)] where a NOT_IMPLEMENTED family owns a written code or a function name term"""
    written = _written_codes() if written is None else written
    defs = {(m.group(1).lower(), p.relative_to(ROOT).as_posix())
            for p in sorted((ROOT / "engine/source").rglob("*.py")) for m in DEF.finditer(p.read_text(encoding="utf-8"))}
    bad = []
    for f in doc["families"]:
        if f["capability"] != "NOT_IMPLEMENTED":
            assert "name_terms" not in f, f["code"]
            continue
        assert f["name_terms"], f["code"]
        bad += [(f["code"], c, written[c]) for c in f["item_codes"] if c in written]
        bad += [(f["code"], t, d, p) for t in f["name_terms"] for d, p in defs if t in d]
    return bad


# ------------------------------------------------------------------ r4 (T-199 r2, Checker 2026-10-31 02:58, gate f)
# These two checks run on the LIVE code against the 1.1.0 snapshot. A later registry version that owns a new code or
# moves a family off NOT_IMPLEMENTED (with file:line evidence) is the registry of record; the 1.1.0 snapshot cannot
# learn it (an existing rule version is never edited). So the 1.1.0 era exempts ONLY what the governing registry (the
# newest BOQ_FAMILY_MASTER on the tree) owns or moved, and ONLY while that governing registry passes the same two
# guards at full strength; any code no registry owns, and any NOT_IMPLEMENTED family the governing registry did not
# move, still fails here. The exemption is empty whenever the governing registry is 1.1.0's own content.
def _semver(v):
    return tuple(int(x) for x in v.split("."))


def _governing():
    files = sorted((ROOT / "rules/coverage").glob("BOQ_FAMILY_MASTER_*.json"),
                   key=lambda p: _semver(p.stem.rsplit("_", 1)[1]))
    return json.loads(files[-1].read_text(encoding="utf-8"))


def _era_exemptions(new, gov, written=None):
    """-> (codes, families) the 1.1.0 era may exempt: codes 1.1.0 never mapped that gov owns in a family that is not
    NOT_IMPLEMENTED; 1.1.0 NOT_IMPLEMENTED families gov moved off NOT_IMPLEMENTED with a resolving file:line. Refuses
    (AssertionError) a governing registry that fails either guard itself."""
    if gov["version"] == new["version"]:
        return set(), set()
    written = _written_codes() if written is None else written
    assert _unowned_written(gov, written) == {}, ("governing registry", gov["version"], "leaves a written code unowned")
    assert _not_implemented_hits(gov, written) == [], ("governing registry", gov["version"], "NOT_IMPLEMENTED hit")
    known = set(_owners(new)) | set(new["item_codes_without_family"])
    gfam = {f["code"]: f for f in gov["families"]}
    gown = _owners(gov)
    codes = {c for c, fc in gown.items() if c not in known and gfam[fc]["capability"] != "NOT_IMPLEMENTED"}
    fams = set()
    for f in new["families"]:
        g = gfam.get(f["code"])
        if f["capability"] == "NOT_IMPLEMENTED" and g and g["capability"] != "NOT_IMPLEMENTED":
            cites = [c for e in g["evidence"] for c in _citations(e)]
            if cites and all(_resolves(*c) for c in cites):
                fams.add(f["code"])
    return codes, fams


def test_every_written_item_code_belongs_to_one_family(new):
    own, apart = _owners(new), new["item_codes_without_family"]
    written = _written_codes()
    assert not set(own) & set(apart)
    codes, _fams = _era_exemptions(new, _governing(), written)
    assert not {c: p for c, p in _unowned_written(new, written).items() if c not in codes}
    from engine.source import boq_line as BL
    assert set(own) | set(apart) <= set(written) | set(BL.ITEMS)               # no invented code in the map


def test_no_not_implemented_family_has_a_module_in_engine_source(new):
    """NOT_IMPLEMENTED = no code measures the family: no module writes one of its item codes and no function in
    engine/source carries one of its name terms (r1 missed struct_n10.excavation() / formwork(): no item code)"""
    _codes, fams = _era_exemptions(new, _governing())
    assert not [b for b in _not_implemented_hits(new) if b[0] not in fams]


def test_the_era_exemption_never_covers_an_unowned_code_or_an_unmoved_family(new):
    """adverse (r4): a code no registry owns and a family the governing registry left NOT_IMPLEMENTED are never
    exempt; a governing registry that fails the guards exempts nothing (it is refused)"""
    gov = _governing()
    written = dict(_written_codes(), **{"FIN.NO_FAMILY_X": "engine/source/synthetic.py"})
    try:
        codes, fams = _era_exemptions(new, gov, written)
    except AssertionError:
        codes, fams = None, None                                                # refused: nothing exempt
    assert codes is None or "FIN.NO_FAMILY_X" not in codes
    if gov["version"] != new["version"]:
        assert codes is None                                                    # the unowned code fails gov itself
        codes, fams = _era_exemptions(new, gov)
        gfam = {f["code"]: f for f in gov["families"]}
        assert all(gfam[c]["capability"] != "NOT_IMPLEMENTED" for c in fams)
        assert not set(codes) & (set(_owners(new)) | set(new["item_codes_without_family"]))
        import copy
        bad = copy.deepcopy(gov)
        for f in bad["families"]:
            if f["code"] in fams:
                f["capability"] = "NOT_IMPLEMENTED"                             # moved back: no exemption left
                f["name_terms"] = ["zz_never_a_def_name"]
        try:
            c2, f2 = _era_exemptions(new, bad)
        except AssertionError:
            c2, f2 = set(), set()
        assert not (f2 & fams)


def test_the_name_scan_finds_the_r1_misses():
    """the scan itself: excavation() and formwork() exist, so B1-02 / B10-13 could never pass as NOT_IMPLEMENTED"""
    text = (ROOT / "engine/source/struct_n10.py").read_text(encoding="utf-8")
    assert {"excavation", "formwork"} <= set(DEF.findall(text))
    assert "FIN.WP.BALCONY" in _written_codes()


def test_integrated_and_tested_is_backed_by_the_development_villa(new):
    """INTEGRATED_AND_TESTED needs released lines of the family on the development villa and none of them held
    (r1 kept lintels with 0 lines and slabs with a held face)"""
    for f in new["families"]:
        if f["capability"] != "INTEGRATED_AND_TESTED":
            continue
        rows = f["development_villa"]["released_run"]
        assert rows and all(r["released_lines"] for r in rows), f["code"]
        assert not any(r["held_lines"] for r in rows), f["code"]


def test_the_families_the_verifier_named(new):
    fam = {f["code"]: f for f in new["families"]}
    for c in ("B1-02", "B10-13"):
        assert fam[c]["capability"] == "IMPLEMENTED_NOT_INTEGRATED", c
        assert any("engine/source/struct_n10.py:" in e for e in fam[c]["evidence"]), c
        assert any("tests/m9_n10/" in e for e in fam[c]["evidence"]), c
        assert fam[c]["in_v3_0_candidate"] == "no", c
    assert fam["B8-07"]["capability"] in ("PARTIAL", "IMPLEMENTED_NOT_INTEGRATED")
    assert any("engine/source/arch_v211.py:" in e for e in fam["B8-07"]["evidence"])
    for c in ("B9-02", "B10-08"):
        assert fam[c]["capability"] == "PARTIAL", c
    assert fam["B4-08"]["capability"] == "PARTIAL"
    assert any("engine/source/arch_v28.py:734" in e for e in fam["B4-08"]["evidence"])
    # a held reveal line keeps no quantity: 27 held, 0 released on the development villa
    (rv,) = fam["B4-08"]["development_villa"]["released_run"]
    assert rv["released_lines"] == 0 and rv["released_qty"] == 0 and rv["held_lines"] == rv["lines"]


# ------------------------------------------------------------------ r3 (verifier 2026-10-21 16:45: gate d, B10-02)
OPEN_CLAUSE = re.compile(r"read by no (?:released )?method|not wired|unwired|UNRESOLVED|\bHELD\b|\bheld\b|"
                         r"read only by (?:the )?opt-in")


def _it_violations(f):
    """why a family fails the INTEGRATED_AND_TESTED definition: released lines on the development villa, none held,
    and no verifier-confirmed open defect or unwired verified correction on the path (evidence, missing or note
    naming one)"""
    why = []
    rows = f["development_villa"]["released_run"]
    if not rows or not all(r["released_lines"] for r in rows):
        why.append("no released lines")
    if any(r["held_lines"] for r in rows):
        why.append("held lines")
    for text in f["evidence"] + [f["missing"], f.get("note") or ""]:
        if OPEN_CLAUSE.search(text) and not text.startswith(("1.0.0", "r1", "r2")):
            why.append("open defect / unwired correction: " + OPEN_CLAUSE.search(text).group(0))
    return why


def test_integrated_and_tested_has_no_open_defect_or_unwired_correction(new):
    bad = {f["code"]: _it_violations(f) for f in new["families"]
           if f["capability"] == "INTEGRATED_AND_TESTED" and _it_violations(f)}
    assert not bad


def test_the_open_defect_clause_catches_the_r2_footing_record():
    """B10-02 as r2 wrote it (released 26 lines, none held) passed the r2 test; the clause test must refuse it"""
    r2 = {"code": "B10-02", "capability": "INTEGRATED_AND_TESTED",
          "evidence": ["engine/source/generic_route.py:509 FOOTINGS concrete in route G",
                       "commit 8774071 (T-058 strip guard) and 9671133 (T-060 ledger V2): footing band pieces read by "
                       "no method"],
          "missing": "footing edge band held (owner Q-28) in the unwired ledger; compared line UNRESOLVED (owner Q-12)",
          "development_villa": {"released_run": [{"item_code": "STR.CONC.FOOTING", "unit": "m3", "lines": 26,
                                                   "released_lines": 26, "released_qty": 66.264, "held_lines": 0,
                                                   "held_bounded_low": None, "held_bounded_high": None,
                                                   "not_applicable_lines": 0}]}}
    assert len(_it_violations(r2)) >= 2
    clean = dict(r2, evidence=r2["evidence"][:1], missing="-")
    assert _it_violations(clean) == []


def test_footings_are_partial_with_the_verifier_evidence(new):
    fam = {f["code"]: f for f in new["families"]}
    f = fam["B10-02"]
    assert f["capability"] == "PARTIAL" and f["capability_change"] == "LOWERED"
    ev = " ".join(f["evidence"])
    for needle in ("9671133", "cd34bd0", "engine/source/route_g_scope_v1.py:321 FOOTING_HELD_OR_IN_CONFLICT",
                   "engine/source/concrete_ledger_v2.py:296 _band()", "engine/source/generic_route.py:542"):
        assert needle in ev, needle
    assert "Q-12" in f["missing"] and "UNRESOLVED" in f["missing"]
    from collections import Counter
    states = Counter(x["capability"] for x in new["families"])
    assert states["INTEGRATED_AND_TESTED"] == 0 and states["PARTIAL"] == 47


def test_no_plan_names_a_merged_integration_task(new):
    """T-133 (V3.0.1) is merged: a piece it left waiting is named from its WAITING table, never planned on it"""
    for f in new["families"]:
        assert "T-133" not in f["v3_0_planned_tasks"], f["code"]


def test_the_counts_in_the_file_equal_the_families(new):
    fam = new["families"]
    assert new["capability_counts"] == {k: sum(1 for f in fam if f["capability"] == k) for k in new["capability_states"]}
    assert new["capability_change_counts"] == {k: sum(1 for f in fam if f["capability_change"] == k)
                                               for k in ("RAISED", "LOWERED", "UNCHANGED")}
    assert new["in_v3_0_candidate_counts"] == {k: sum(1 for f in fam if f["in_v3_0_candidate"] == k)
                                               for k in ("yes", "no")}
    assert sum(new["capability_counts"].values()) == 99
