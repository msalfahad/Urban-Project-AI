"""A refused input cannot be placed, and a stray file fails the launch.

The breach: a file the contract refused was supplied to a cold agent
anyway, because the sandbox was assembled with a copy command and the
contract was consulted afterwards.
"""

from __future__ import annotations

import pytest

from engine import agent_sandbox as sbx
from engine import blind_input_contract as bic


def _image(tmp_path, name="page-01.jpeg"):
    p = tmp_path / "src" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\xff\xd8\xff\xe0 bytes to hash")
    return p


def _sandbox(tmp_path, **kw):
    run = bic.BlindRun(run_id="R1", subject="a blind pass")
    return sbx.Sandbox(root=tmp_path / "sandbox", run=run, **kw)


def test_an_admitted_input_is_placed_and_hashed(tmp_path):
    box = _sandbox(tmp_path)
    d = box.place(bic.Input(input_id="IMG-01",
                            kind=bic.SOURCE_DRAWING_IMAGE,
                            path=str(_image(tmp_path))),
                  at="images/page-01.jpeg")
    assert d.admitted
    assert (box.root / "images/page-01.jpeg").exists()
    assert box.verify()["status"] == sbx.EQUAL


def test_a_refused_input_raises_and_writes_nothing(tmp_path):
    box = _sandbox(tmp_path)
    with pytest.raises(sbx.RefusedInput):
        box.place(bic.Input(input_id="X", kind=bic.SHEET_METADATA,
                            path="data/runs/7757/reconciliation/x.json"),
                  at="notes.json")
    assert not (box.root / "notes.json").exists()
    assert box.placed == {}
    assert box.refused[0]["refused_by"] == bic.PATH_GATE


def test_content_that_carries_the_answer_cannot_be_placed(tmp_path):
    box = _sandbox(tmp_path)
    with pytest.raises(sbx.RefusedInput):
        box.place(bic.Input(input_id="META", kind=bic.SHEET_METADATA,
                            content={"pages": 3, "expected_area_m2": 137.5}),
                  at="meta.json")
    assert not (box.root / "meta.json").exists()


def test_ordinary_prose_can_be_placed(tmp_path):
    # the other half of the same rule: a scanner that refuses English is a
    # scanner somebody works around
    box = _sandbox(tmp_path)
    d = box.place(bic.Input(
        input_id="META", kind=bic.SHEET_METADATA,
        content={"note": "a break is expected because a stair is its own "
                         "finish", "rule": "a known dimension is never "
                         "replaced by a default"}), at="meta.json")
    assert d.admitted
    assert box.verify()["status"] == sbx.EQUAL


def test_a_file_copied_in_behind_the_contract_fails_the_launch(tmp_path):
    box = _sandbox(tmp_path)
    box.place(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))),
              at="images/page-01.jpeg")
    assert box.assert_ready()["status"] == sbx.EQUAL
    # somebody runs cp
    (box.root / "smuggled.json").write_text('{"expected_area_m2": 137.5}')
    report = box.verify()
    assert report["status"] == sbx.MISMATCH
    assert report["problems"][0]["problem"] == sbx.UNADMITTED_PRESENT
    with pytest.raises(sbx.SandboxMismatch):
        box.assert_ready()
    with pytest.raises(sbx.SandboxMismatch):
        box.launch_token()


def test_an_admitted_file_edited_on_disk_fails_the_launch(tmp_path):
    box = _sandbox(tmp_path)
    box.place(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))),
              at="images/page-01.jpeg")
    (box.root / "images/page-01.jpeg").write_bytes(b"different bytes")
    report = box.verify()
    assert report["status"] == sbx.MISMATCH
    assert report["problems"][0]["problem"] == sbx.BYTES_DIFFER


def test_a_deleted_input_fails_the_launch(tmp_path):
    box = _sandbox(tmp_path)
    box.place(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))),
              at="images/page-01.jpeg")
    (box.root / "images/page-01.jpeg").unlink()
    assert box.verify()["problems"][0]["problem"] == sbx.ADMITTED_MISSING


def test_a_declared_working_dir_must_be_empty_before_launch(tmp_path):
    box = _sandbox(tmp_path, working_dirs=("crops",))
    box.place(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))),
              at="images/page-01.jpeg")
    assert box.assert_ready()["status"] == sbx.EQUAL
    (box.root / "crops" / "already-here.png").write_bytes(b"x")
    report = box.verify()
    assert report["status"] == sbx.MISMATCH
    assert report["problems"][0]["problem"] == sbx.WORKING_DIR_NOT_EMPTY


def test_a_token_is_issued_by_verification_not_asked_for(tmp_path):
    box = _sandbox(tmp_path)
    with pytest.raises(sbx.SandboxMismatch):
        box.launch_token()
    box.place(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))),
              at="images/page-01.jpeg")
    with pytest.raises(sbx.SandboxMismatch):
        box.launch_token()          # changed since the last check
    box.assert_ready()
    assert len(box.launch_token()) == 64


def test_placing_twice_at_one_path_is_refused(tmp_path):
    box = _sandbox(tmp_path)
    item = bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                     path=str(_image(tmp_path)))
    box.place(item, at="images/page-01.jpeg")
    with pytest.raises(sbx.SandboxMismatch):
        box.place(item, at="images/page-01.jpeg")


def test_the_manifest_carries_the_equality_result(tmp_path):
    box = _sandbox(tmp_path)
    box.place(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))),
              at="images/page-01.jpeg")
    man = box.manifest()
    assert man["SANDBOX_EQUALS_ADMITTED_INPUTS"] is True
    assert man["sandbox"]["invariant"] == (
        "SANDBOX_CONTENTS == ADMITTED_INPUT_MANIFEST")
    assert man["sandbox"]["SANDBOX_HASH"]
