"""Independent-export admission and measured verification (R8.5 follow-up).

An export is ADMITTED only from an independent tool, from the exact source DWG, with no operations and the
requested version's $ACADVER; admission qualifies nothing; handle identity etc. are verified from the file."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import independent_export as IX

SRC = "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3"
REG = Path(__file__).parent / "registers" / "R8_INDEPENDENT_EXPORT_INTAKE.json"


def declared(tool="AUTOCAD", fmt="AUTOCAD_2018_DXF", src=SRC, ops=()):
    return {"tool": tool, "tool_version": "2018", "requested_format": fmt, "exported_from_sha256": src,
            "operations": list(ops) if ops is not None else None, "exported_by": "owner"}


def hdr(ver="AC1032", saved="AutoCAD"):
    return {"$ACADVER": ver, "$LASTSAVEDBY": saved}


def test_autocad_2018_export_is_admitted_for_verification_only():
    a = IX.admission("f" * 64, hdr(), None, declared(), SRC)
    assert a["status"] == IX.ADMITTED_FOR_VERIFICATION and a["parser_independence"] == "INDEPENDENT_PARSER"
    assert a["qualifies_anything"] is False


def test_autocad_2018_requires_ac1032():
    a = IX.admission("f" * 64, hdr("AC1027"), None, declared(), SRC)
    assert a["status"] == IX.REJECTED and any("AC1032" in r for r in a["reasons"])


def test_ezdxf_or_libredwg_writer_is_a_nonqualifying_conversion():
    for saved, comment in (("ezdxf", None), ("", "LibreDWG 0.13.3")):
        a = IX.admission("f" * 64, hdr(saved=saved), comment, declared(), SRC)
        assert a["status"] == IX.DIAGNOSTIC_NONQUALIFYING_CONVERSION


def test_undeclared_tool_or_undocumented_operations_are_not_admitted():
    assert IX.admission("f" * 64, hdr(), None, declared(tool="AI_CONVERSION"), SRC)["status"] == \
        IX.DIAGNOSTIC_NONQUALIFYING_CONVERSION
    assert IX.admission("f" * 64, hdr(), None, declared(ops=None), SRC)["status"] == IX.DIAGNOSTIC_NONQUALIFYING_CONVERSION


def test_forbidden_operations_or_wrong_source_reject():
    for op in ("AUDIT", "EXPLODE", "PURGE", "RESCALE"):
        assert IX.admission("f" * 64, hdr(), None, declared(ops=[op]), SRC)["status"] == IX.REJECTED
    assert IX.admission("f" * 64, hdr(), None, declared(src="0" * 64), SRC)["status"] == IX.REJECTED


def _e(h, t="LINE", layer="W"):
    return {"handle": h, "type": t, "layer": layer, "space": "MODEL"}


def test_oda_handles_are_verified_not_assumed():
    oda = IX.admission("f" * 64, hdr(saved="ODA File Converter"), None, declared(tool="ODA_FILE_CONVERTER"), SRC)
    assert oda["status"] == IX.ADMITTED_FOR_VERIFICATION
    d1 = [_e("929", "ARC_DIMENSION", "4"), _e("A1"), _e("A2")]
    same = IX.verify(d1, d1, {"B": 2}, {"B": 2}, ["ARC_DIMENSION"], ["ARC_DIMENSION"])
    assert all(same[d]["verdict"] == IX.VERIFIED for d in ("HANDLE_IDENTITY", "ENTITY_CENSUS", "BLOCK_LINEAGE",
                                                           "CUSTOM_CLASSES"))
    assert same["handle_keyed_comparison_possible"] and same["GEOMETRY"]["verdict"] == IX.NOT_RUN
    renum = [_e("929"), _e("B1"), _e("B2", "ARC_DIMENSION", "4")]           # same content, renumbered handles
    v = IX.verify(d1, renum, {"B": 2}, {"B": 2}, ["ARC_DIMENSION"], [])
    assert v["HANDLE_IDENTITY"]["verdict"] == IX.NOT_VERIFIED and not v["handle_keyed_comparison_possible"]
    assert v["CUSTOM_CLASSES"]["missing"] == ["ARC_DIMENSION"]


def test_received_conversions_are_recorded_as_diagnostic_and_reconciliation_stays_blocked():
    reg = json.loads(REG.read_text())
    assert reg["INDEPENDENT_REAL_RECONCILIATION"] == "BLOCKED_EXTERNAL_INPUT"
    assert reg["requirements_for_the_real_route"]["autocad_2018_dxf_requires"] == "AC1032"
    assert {e["classification"] for e in reg["exports"]} == {IX.DIAGNOSTIC_NONQUALIFYING_CONVERSION}
    assert all(not (e["modified"] or e["repaired"] or e["normalised"]) for e in reg["exports"])
    arch = next(e for e in reg["exports"] if e["role"] == "ARCHITECTURAL")
    assert arch["diagnostic_verification_against_D1"]["HANDLE_IDENTITY"]["verdict"] == IX.NOT_VERIFIED
    src = {s["role"]: s for s in reg["sources"]}
    assert src["ARCHITECTURAL_SOURCE"]["sha256"] == SRC and src["ARCHITECTURAL_SOURCE"]["matches_expected_sha256"]
