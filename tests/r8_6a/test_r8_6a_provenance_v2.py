"""R8.6A provenance V2 on synthetic inputs: writer, decoder and source metadata stay three separate facts;
a file's existence, its format family or its $LASTSAVEDBY never proves the decoder; nothing qualifies unless
the route is admitted."""

from __future__ import annotations

from engine.source import independent_export as IX

ACAD_HDR = {"$ACADVER": "AC1032", "$LASTSAVEDBY": "Msalf", "$FINGERPRINTGUID": "{F}", "$VERSIONGUID": "{V}"}
SRC_HDR = {"FINGERPRINTGUID": "{F}", "VERSIONGUID": "{V}"}
DECLARED_UNKNOWN = {"tool": None, "operations": None, "requested_format": None}


def _acad_writer():
    return IX.writer_fingerprint(ACAD_HDR, (), ("HEADER", "CLASSES", "ACDSDATA"), 90)


def test_writer_classes_come_from_the_file_bytes():
    assert IX.writer_fingerprint({"$LASTSAVEDBY": "ezdxf"})["class"] == IX.WRITER_EZDXF
    assert IX.writer_fingerprint({}, ["LibreDWG 0.13.3"], ("HEADER",), 70)["class"] == IX.WRITER_LIBREDWG
    w = _acad_writer()
    assert w["class"] == IX.WRITER_AUTOCAD_ODA_FORMAT and "ACDSDATA section present" in w["evidence"]
    # the family needs BOTH traits; either one alone is not enough
    assert IX.writer_fingerprint(ACAD_HDR, (), ("ACDSDATA",), 70)["class"] == IX.WRITER_UNKNOWN
    assert IX.writer_fingerprint(ACAD_HDR, (), ("HEADER",), 90)["class"] == IX.WRITER_UNKNOWN


def test_lastsavedby_is_source_metadata_not_a_tool():
    w = _acad_writer()
    assert w["source_metadata_lastsavedby"] == "Msalf"
    d = IX.decoder_provenance(w, None)
    assert d["state"] == "CONVERTER_UNKNOWN" and d["independent"] is False


def test_only_a_record_with_hashed_evidence_proves_a_decoder():
    w = _acad_writer()
    assert IX.decoder_provenance(w, {"tool": "AUTOCAD"})["state"] == "CONVERTER_UNKNOWN"
    assert IX.decoder_provenance(w, {"tool": "AUTOCAD", "evidence_sha256": "e" * 64})["state"] == "AUTOCAD_PROVEN"
    assert IX.decoder_provenance(w, {"tool": "ODA_FILE_CONVERTER", "evidence_sha256": "e" * 64})["independent"]
    assert IX.decoder_provenance(w, {"tool": "X", "evidence_sha256": "e" * 64})["state"] == "CONVERTER_UNKNOWN"
    assert IX.decoder_provenance(w, {"shares_libredwg": True})["state"] == "SHARED_OR_DEPENDENT_LINEAGE"
    lib = IX.writer_fingerprint({}, ["LibreDWG 0.13.3"])
    # a LibreDWG stamp proves lineage, and no record can turn it into an independent decoder
    assert IX.decoder_provenance(lib, {"tool": "AUTOCAD", "evidence_sha256": "e" * 64})["state"] == "LIBREDWG_LINEAGE_PROVEN"


def test_revision_identity_needs_every_source_entity_and_nothing_added():
    assert IX.revision_identity(SRC_HDR, ACAD_HDR, 0, 0)["state"] == IX.SAME_REVISION
    assert IX.revision_identity(SRC_HDR, ACAD_HDR, 21, 19)["state"] == IX.SAME_LINEAGE_DIFFERENT_REVISION
    assert IX.revision_identity(SRC_HDR, ACAD_HDR, 0, 1)["state"] == IX.SAME_LINEAGE_DIFFERENT_REVISION
    assert IX.revision_identity(SRC_HDR, dict(ACAD_HDR, **{"$FINGERPRINTGUID": "{G}"}), 0, 0)["state"] == IX.UNRELATED_SOURCE
    assert IX.revision_identity({}, ACAD_HDR, 0, 0)["state"] == IX.REVISION_NOT_ESTABLISHED
    # a renewed VERSIONGUID alone does not make a different revision (recorded as supporting evidence only)
    r = IX.revision_identity(SRC_HDR, dict(ACAD_HDR, **{"$VERSIONGUID": "{W}"}), 0, 0)
    assert r["state"] == IX.SAME_REVISION and r["versionguid_equal"] is False


def test_admission_v2_orders_revision_writer_decoder_operations():
    w, unk = _acad_writer(), IX.decoder_provenance(_acad_writer(), None)
    same, other = IX.revision_identity(SRC_HDR, ACAD_HDR, 0, 0), IX.revision_identity(SRC_HDR, ACAD_HDR, 21, 19)
    a = IX.admission_v2("f" * 64, ACAD_HDR, w, unk, same, DECLARED_UNKNOWN, "s" * 64)
    assert a["status"] == IX.PROVENANCE_UNVERIFIED and a["qualifies_anything"] is False
    assert (a["DXF_WRITER"], a["DWG_DECODER"], a["SOURCE_METADATA_LASTSAVEDBY"]) == (
        IX.WRITER_AUTOCAD_ODA_FORMAT, "CONVERTER_UNKNOWN", "Msalf")
    assert IX.admission_v2("f" * 64, ACAD_HDR, w, unk, other, DECLARED_UNKNOWN, "s" * 64)["status"] == IX.REJECTED
    ez = IX.writer_fingerprint({"$LASTSAVEDBY": "ezdxf"})
    oda = IX.decoder_provenance(ez, {"tool": "ODA_FILE_CONVERTER", "evidence_sha256": "e" * 64})
    assert IX.admission_v2("f" * 64, ACAD_HDR, ez, oda, same, {"operations": []}, "s" * 64)["status"] == \
        IX.DIAGNOSTIC_NONQUALIFYING_CONVERSION
    proven = IX.decoder_provenance(w, {"tool": "AUTOCAD", "evidence_sha256": "e" * 64})
    ok = IX.admission_v2("f" * 64, ACAD_HDR, w, proven, same, {"operations": [], "requested_format": None}, "s" * 64)
    assert ok["status"] == IX.ADMITTED_FOR_VERIFICATION and ok["qualifies_anything"] is False
    bad = IX.admission_v2("f" * 64, ACAD_HDR, w, proven, same, {"operations": ["EXPLODE"]}, "s" * 64)
    assert bad["status"] == IX.REJECTED


def test_unadmitted_route_never_yields_a_qualification_state():
    diag = {"SIG_A": "EXERCISED_AND_PASS", "SIG_B": "NOT_EXERCISED"}
    w = _acad_writer()
    a = IX.admission_v2("f" * 64, ACAD_HDR, w, IX.decoder_provenance(w), IX.revision_identity(SRC_HDR, ACAD_HDR, 0, 0),
                        DECLARED_UNKNOWN, "s" * 64)
    s = IX.scoped_signature_states(diag, a)
    assert {v["state"] for v in s.values()} == {IX.PROVENANCE_NOT_INDEPENDENT}
    assert s["SIG_A"]["diagnostic"] == "EXERCISED_AND_PASS"
    adm = dict(a, status=IX.ADMITTED_FOR_VERIFICATION)
    assert IX.scoped_signature_states(diag, adm)["SIG_A"]["state"] == "EXERCISED_AND_PASS"
