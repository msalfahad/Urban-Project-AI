"""T-195: the development villa's committed register reproduces from repository files, and its invariants hold:
every Drive drawing page is a register row; no revision is invented (no sheet prints one: all FILE_PIN); the
structural set's two title-block dates are reported; the pinned merged ledgers cite only sheets that exist."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t195"))
sys.path.insert(0, str(ROOT))

import alsenan_t195 as A                                        # noqa: E402

HERE = ROOT / "research" / "agents_t195"


def _rows(name):
    return list(csv.DictReader(open(HERE / name, encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_every_page_is_a_row_and_no_revision_invented():
    rows = _rows("REGISTER_T195.csv")
    keys = [r["sheet_key"] for r in rows]
    assert keys == [f"ARCH-{p:02d}" for p in range(1, 13)] + [f"ST-{p:02d}" for p in range(1, 17)] + \
        [f"SAN-{p:02d}" for p in range(1, 4)]
    assert {r["revision_printed"] for r in rows} == {"NONE_PRINTED"}
    assert {r["revision_basis"] for r in rows} == {"FILE_PIN"}
    # the single-sheet files and the split parts are carriers of the same pages, not other issues
    arch03 = next(r for r in rows if r["sheet_key"] == "ARCH-03")["carriers"]
    assert "p7757_arch_sheet03.pdf p.1" in arch03 and "Pages_03-04.pdf p.1" in arch03


def test_structural_date_conflict_reported():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    (d,) = s["date_conflicts"]
    assert d["set"] == "ST" and set(d["dates"]) == {"May 06, 2025", "May 06, 2026"}
    assert d["dates"]["May 06, 2025"] == [f"ST-0{p}" for p in range(1, 8)]


def test_pinned_ledgers_cite_only_registered_sheets():
    rows = _rows("CITATIONS_T195.csv")
    assert rows, "no citation found"
    bad = [r for r in rows if r["verdict"] in ("NOT_IN_REGISTER", "PART_MISMATCH", "MULTI_REVISION")]
    assert bad == []
    mixed = [r for r in rows if r["verdict"] == "PART_FILE_PAGE"]
    assert len(mixed) == 5 and {r["resolves_to"] for r in mixed} == {"ARCH-05", "ARCH-06", "ARCH-07"}


def test_every_drawing_file_on_drive_is_listed():
    titles = {r["drive_title"] for r in _rows("DRIVE_FILES_T195.csv")}
    for t in ("P7757.dwg", "P7757 dxf.dxf", "P7757_DXF_COMPRESSED.zip", "ST7757 dxf.dxf", "ST7757.dwg", "ST7757.pdf",
              "sanitary-7757.pdf", "TEST_PAGE_01.pdf", "p7757_arch_sheet03.pdf", "p7757_arch_sheet10.pdf",
              "Alsenan_Architectural_P7757_Pages_11-12.pdf"):
        assert t in titles


# ---- T-243: the committed snapshot names its inputs (INPUTS_T195.csv) and reproduces when later merges change them --
import dataclasses                                               # noqa: E402
import shutil                                                    # noqa: E402

import pytest                                                    # noqa: E402

DRIFTED = "research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json"  # appended by the T-233 / T-234 merges after the pin


def _committed():
    return {n: (HERE / n).read_text(encoding="utf-8") for n in
            ("REGISTER_T195.csv", "DRIVE_FILES_T195.csv", "CITATIONS_T195.csv", "MISSING_T195.csv", "summary.json")}


def _copy_inputs(tmp_path):
    """A temporary repository root holding the pinned input paths as they are NOW in the working tree."""
    for r in _rows(A.INPUTS):
        src = ROOT / r["path"]
        if src.is_file():
            dst = tmp_path / r["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    return tmp_path


def test_inputs_manifest_is_written_by_the_tool_from_the_pin():
    assert A.write_inputs() == (HERE / A.INPUTS).read_text(encoding="utf-8")
    rows = _rows(A.INPUTS)
    assert len(rows) == 203 and len({r["path"] for r in rows}) == 203
    assert all(r["path"].split("/")[1] in A.PINNED_FOLDERS for r in rows)


def test_a_later_merge_editing_a_pinned_file_does_not_change_the_snapshot():
    # the real case of 2026-10-23: the ledger changed after the pin; the check reads its pinned blob, not the new text
    origins = {p: o for p, _, o in A.pinned_inputs()}
    assert origins[DRIFTED] == "GIT_BLOB"
    assert (ROOT / DRIFTED).is_file()
    out, _ = A.build()
    assert out == _committed()


def test_normal_unrelated_research_file_added_check_passes(tmp_path):
    root = _copy_inputs(tmp_path)
    # a new file inside a pinned folder and a new folder, both citing a sheet the register does not have
    (root / "research/agents_t100/LATER_NOTE.md").write_text("later merge: ST p.99 and sheet 13\n", encoding="utf-8")
    (root / "research/agents_t199").mkdir(parents=True)
    (root / "research/agents_t199/LEDGER.csv").write_text("ref\nST p.99\n", encoding="utf-8")
    # the new text WOULD be an error verdict in a live scan (so ignoring it is a choice, not blindness) ...
    live = A._scan_texts([("x", "ST p.99")], A.build_register())
    assert [r["verdict"] for r in live] == ["NOT_IN_REGISTER"]
    # ... but it is not an input of the pinned snapshot
    out, _ = A.build(root=root)
    assert out == _committed()


def test_normal_pinned_file_edited_later_is_read_from_its_blob(tmp_path):
    root = _copy_inputs(tmp_path)
    f = root / "research/agents_t100" / Path(_rows(A.INPUTS)[0]["path"]).name
    f.write_text(f.read_text(encoding="utf-8") + "\nST p.99\n", encoding="utf-8")
    origins = {p: o for p, _, o in A.pinned_inputs(root)}
    assert origins[f.relative_to(root).as_posix()] == "GIT_BLOB"
    out, _ = A.build(root=root)
    assert out == _committed()


def test_adverse_cited_sheet_revision_changed_check_fails(monkeypatch):
    real = A.build_register

    def revised():
        reg = real()
        reg.sheets = [dataclasses.replace(s, revision_printed="B", revision_basis="PRINTED") if s.key == "ST-08"
                      else s for s in reg.sheets]
        return reg

    monkeypatch.setattr(A, "build_register", revised)
    out, _ = A.build()
    committed = _committed()
    assert out["REGISTER_T195.csv"] != committed["REGISTER_T195.csv"]
    assert out["CITATIONS_T195.csv"] != committed["CITATIONS_T195.csv"]   # ST p.8 citations now resolve to REV B
    assert A.main(["--check"]) == 1


def test_adverse_pinned_input_unreadable_is_refused_never_rescanned(tmp_path):
    root = _copy_inputs(tmp_path)
    rows = _rows(A.INPUTS)
    target = root / rows[0]["path"]
    target.write_text("edited after the pin\n", encoding="utf-8")
    # (a) the pinned blob is gone
    bad = [dict(r, git_blob="0" * 40) if i == 0 else r for i, r in enumerate(rows)]
    m = tmp_path / "INPUTS_bad.csv"
    m.write_text(A._csv(bad, A.INPUT_COLS), encoding="utf-8")
    with pytest.raises(A.InputUnavailable, match="not readable"):
        A.pinned_inputs(root, manifest=m)
    # (b) the blob exists but is not the pinned content (wrong blob id in the manifest)
    bad = [dict(r, git_blob=rows[1]["git_blob"]) if i == 0 else r for i, r in enumerate(rows)]
    m.write_text(A._csv(bad, A.INPUT_COLS), encoding="utf-8")
    with pytest.raises(A.InputUnavailable, match="does not match"):
        A.pinned_inputs(root, manifest=m)
    # (c) a pinned file deleted after the pin is read from its blob, not dropped
    target.unlink()
    origins = {p: o for p, _, o in A.pinned_inputs(root)}
    assert origins[rows[0]["path"]] == "GIT_BLOB"
