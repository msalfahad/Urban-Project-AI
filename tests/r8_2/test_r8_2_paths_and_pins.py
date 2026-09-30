"""R8.2 — active path map verified against the code (§3, §24), decoder pins and route lineage (§9, §17),
and the shadow-only rule (§18, §26)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from engine.source import decoder_pins as PINS
from engine.source.cad import kernel_ezdxf as K2, libredwg_map as L
from research.external_engine_lab import r8_2_path_and_independence as MAP
from tests.r8_0 import libredwg_builder as B
from tests.r8_0.test_r8_0_import_boundaries import _files, imports_of_text

ROOT = Path(__file__).resolve().parents[2]


def test_active_path_map_matches_the_code():
    assert MAP.verify() == []


def test_alrashed_published_path_does_not_use_cad_adapter():
    row = next(p for p in MAP.PATHS if p["project"] == "ALRASHED")
    assert row["status"] == "CURRENT_ACTIVE" and row["uses_cad_adapter"] is False


def test_every_failure_domain_names_its_independence():
    for d in MAP.FAILURE_DOMAINS:
        assert d[0] and d[1] and d[2]
    names = [d[0] for d in MAP.FAILURE_DOMAINS]
    assert "DWG byte parsing" in names and "Block placement / composition" in names


def test_no_production_module_consumes_the_source_engine_yet():
    """R8.2 ends in SHADOW: production keeps its path."""
    users = []
    for f in _files(ROOT / "engine"):
        if (ROOT / "engine" / "source") in f.parents:
            continue
        if any(n == "engine.source" or n.startswith("engine.source.") for n in imports_of_text(f.read_text(), f)):
            users.append(str(f))
    assert users == []


def test_engine_never_imports_the_lab_or_the_shadow_bridge():
    for f in _files(ROOT / "engine"):
        assert not any(n.startswith("research") for n in imports_of_text(f.read_text(), f, members=False)
                       if "a21_trace_sufficiency_01" not in n), f        # B-7 frozen debt excepted


def test_d1_anchor_records_parser_lineage_and_an_honest_pin():
    doc = L.to_document(B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]}))
    a = doc.anchor
    assert a.parser_lineage == "LIBREDWG" and a.conversion_chain == ("DWG", "LIBREDWG dwgread -O JSON")
    assert a.decoder_binary_sha256 is None and a.pin_status == PINS.NOT_ESTABLISHED


def test_pin_status_distinguishes_registered_unregistered_and_unknown():
    reg = PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"]
    assert PINS.status("LIBREDWG_DWGREAD", reg) == PINS.REGISTERED
    assert PINS.status("LIBREDWG_DWGREAD", "0" * 64) == PINS.UNREGISTERED_BUILD
    assert PINS.status("LIBREDWG_DWGREAD", None) == PINS.NOT_ESTABLISHED


def test_registered_binary_pin_is_the_binary_present_when_it_exists():
    p = Path("/tmp/ldwg/programs/dwgread")
    if p.exists():
        assert hashlib.sha256(p.read_bytes()).hexdigest() == PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"]


def test_k2_anchor_names_its_own_lineage():
    a = K2.anchor(conversion_chain=("DWG", "LibreDWG dwg2dxf", "ezdxf.readfile"), parser_lineage="LIBREDWG")
    assert a.route == "D2_DXF_EZDXF" and a.parser_lineage == "LIBREDWG" and a.pin_status == PINS.REGISTERED
