"""R8.6A — DXF INTAKE: identify by hash, measure the file, separate writer / decoder / source metadata.

Research lab (SHADOW). Every fact is measured from the file bytes in one read-only streaming pass; the DXF is
never loaded through a library that could normalise it for the intake facts, and it is never rewritten.

    python3 research/external_engine_lab/r8_6a_intake.py <work_dir> <register_dir>

<work_dir> holds the hash-addressed working copies and the reconciliation outputs of r8_6a_reconcile.py.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import independent_export as IX                                     # noqa: E402

UPLOADS = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
BY_SHA256 = ROOT / "data/inputs/by_sha256"           # hash-addressed inputs: <sha256>.dxf, the same store the tests read
FILES = {
    "QORTUBA": {"dxf_sha256": "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315",
                "dwg_sha256": "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355",
                "decode": "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json", "role": "ARCHITECTURAL_SOURCE",
                "transport": "438b9176-qurtoba_villah_lossless.zip (sha256 2abccc6c...) -> 'qurtoba villah.dxf'"},
    "P7757": {"dxf_sha256": "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4",
              "dwg_sha256": "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3",
              "decode": "data/runs/cad_convert/P7757_ARCHITECTURAL.json", "role": "ARCHITECTURAL_SOURCE"},
    "ST7757": {"dxf_sha256": "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079",
               "dwg_sha256": "3f7a556c69786834c16c355504437b5abcd1f5aa3a9625b33a2c5b14213f0227",
               "decode": None, "role": "STRUCTURAL_SUPPORTING_EVIDENCE_ONLY"},
}
HEADER_VARS = ("$ACADVER", "$ACADMAINTVER", "$LASTSAVEDBY", "$INSUNITS", "$HANDSEED", "$DWGCODEPAGE",
               "$FINGERPRINTGUID", "$VERSIONGUID", "$TDCREATE", "$TDUPDATE", "$TDUCREATE", "$TDUUPDATE", "$TDINDWG",
               "$EXTMIN", "$EXTMAX", "$MEASUREMENT")


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find_by_hash(want: str, roots) -> list:
    """Every file under the given roots whose bytes hash to `want` (names are irrelevant)."""
    out = []
    for r in roots:
        for p in Path(r).glob("*"):
            if p.is_file() and p.suffix.lower() in (".dxf", ".dwg") and sha(p) == want:
                out.append(str(p))
    return out


def scan(path) -> dict:
    """One read-only pass: header vars (with the group code of $ACADMAINTVER), 999 comments, sections, classes,
    census by section/type, handle census, unresolved owner references, line endings."""
    hdr, comments, sections, classes = {}, [], [], []
    census, handles = Counter(), Counter()
    owners = Counter()
    maint_code, crlf = None, False
    with open(path, "rb") as fb:
        crlf = b"\r\n" in fb.read(4096)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        it = iter(f)
        sec, cur_var = None, None
        own_handle_taken = True
        while True:
            try:
                code = next(it).strip()
                val = next(it).rstrip("\r\n")
            except StopIteration:
                break
            if code == "999":
                comments.append(val)
                continue
            if code == "0":
                if val == "SECTION":
                    next(it)
                    sec = next(it).strip()
                    sections.append(sec)
                    continue
                own_handle_taken = False
                if sec in ("ENTITIES", "BLOCKS", "OBJECTS", "TABLES"):
                    census[f"{sec}:{val}"] += 1
                continue
            if sec == "HEADER":
                if code == "9":
                    cur_var = val if val in HEADER_VARS else None
                    continue
                if cur_var:
                    if cur_var == "$ACADMAINTVER" and maint_code is None:
                        maint_code = int(code)
                    hdr.setdefault(cur_var, []).append(val.strip())
                continue
            if sec == "CLASSES" and code == "1":
                classes.append(val)
            if code in ("5", "105") and sec in ("ENTITIES", "BLOCKS", "OBJECTS", "TABLES") and not own_handle_taken:
                # only the object's OWN handle: the first 5/105 after its 0 record (SORTENTSTABLE, for one,
                # reuses code 5 for sort keys, which are not handles)
                handles[val.upper()] += 1
                own_handle_taken = True
            elif code == "330" and sec in ("ENTITIES", "BLOCKS", "OBJECTS"):
                owners[val.upper()] += 1
    header = {k: (v[0] if len(v) == 1 else v) for k, v in hdr.items()}
    ints = [int(h, 16) for h in handles if h and all(c in "0123456789ABCDEF" for c in h)]
    unresolved = [h for h in owners if h not in handles and h != "0"]
    return {"header": header, "acadmaintver_group_code": maint_code, "comments": comments, "sections": sections,
            "classes": classes, "census": dict(census), "crlf": crlf,
            "handles": {"count": sum(handles.values()), "distinct": len(handles),
                        "collisions": sum(1 for v in handles.values() if v > 1),
                        "max": format(max(ints), "X") if ints else None,
                        "max_bytes": (max(ints).bit_length() + 7) // 8 if ints else None},
            "owner_references": {"distinct": len(owners), "unresolved": len(unresolved),
                                 "unresolved_examples": sorted(unresolved)[:10]}}


def d1_header(decode_path):
    if decode_path is None:
        return {}
    d = json.loads((ROOT / decode_path).read_text(encoding="utf-8", errors="replace"))
    h = d.get("HEADER", {})
    return {"FINGERPRINTGUID": h.get("FINGERPRINTGUID"), "VERSIONGUID": h.get("VERSIONGUID"),
            "INSUNITS": h.get("INSUNITS"), "HANDSEED": h.get("HANDSEED"), "TDINDWG": h.get("TDINDWG"),
            "TDUCREATE": h.get("TDUCREATE"), "TDUUPDATE": h.get("TDUUPDATE"),
            "version": d.get("FILEHEADER", {}).get("version"), "maint_version": d.get("FILEHEADER", {}).get("maint_version")}


def days(v):
    """[days, milliseconds] (pinned decode) or a decimal-day string (DXF) -> days."""
    if isinstance(v, list) and len(v) == 2:
        return v[0] + v[1] / 86_400_000
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def editing_time_evidence(d1h, dxf_header):
    """TDINDWG is the drawing's cumulative editing time. The DXF value minus the source DWG value is how long the
    drawing was open between the measured DWG and the DXF; TDUPDATE - TDUUPDATE is the writing machine's UTC offset.
    Both are header facts: they constrain the story, they do not name the tool."""
    src, dst = days(d1h.get("TDINDWG")), days(dxf_header.get("$TDINDWG"))
    loc, utc = days(dxf_header.get("$TDUPDATE")), days(dxf_header.get("$TDUUPDATE"))
    delta = None if src is None or dst is None else round((dst - src) * 86400, 1)
    return {"source_dwg_TDINDWG_days": src, "dxf_TDINDWG_days": dst, "added_editing_time_seconds": delta,
            "source_dwg_TDUUPDATE_julian": days(d1h.get("TDUUPDATE")), "dxf_TDUUPDATE_julian": utc,
            "dxf_writer_clock_utc_offset_hours": None if loc is None or utc is None else round((loc - utc) * 24, 2),
            "reading": (None if delta is None else
                        "open only for the save (seconds): consistent with a straight conversion" if delta < 600 else
                        "hours of additional editing: the DXF's drawing was edited after the measured DWG was saved")}


# ====================================================================== identity vs D1
def identity_vs_d1(decode_json_path, index):
    """Per D1 model-space entity: is its handle in the DXF with the same type and layer? (identity only)."""
    from engine.source.cad import libredwg_map as L
    dec = json.loads(Path(decode_json_path).read_text(encoding="utf-8", errors="replace"))
    doc = L.to_document(dec)
    byh = {e.get("5", "").upper(): e for e in index["entities"]}
    same, missing, differ, ex = [], [], [], Counter()
    for o in doc.entities:
        e = byh.get(format(int(o.source_handle.split("+")[0]), "X"))
        if e is None:
            missing.append(o.obs_id)
            continue
        type_ok = e["type"] == o.kind or o.kind in ("UNSUPPORTED",)
        if type_ok and (e.get("8") == o.layer or (o.kind == "UNSUPPORTED" and not o.layer)):
            same.append(o.obs_id)
        else:
            differ.append(o.obs_id)
            ex[f"{o.kind}/{o.layer} -> {e['type']}/{e.get('8')}"] += 1
    unsupported_read = [o.obs_id for o in doc.entities if o.kind == "UNSUPPORTED"
                        and (byh.get(format(int(o.source_handle.split('+')[0]), 'X')) or {}).get("type")]
    return {"d1_model_space_entities": len(doc.entities), "same_handle_type_layer": len(same),
            "different": len(differ), "different_examples": dict(ex), "missing_in_dxf": len(missing),
            "missing_obs": missing, "d1_unsupported_read_by_dxf_route": len(unsupported_read),
            "dxf_model_space_entities": len(index["entities"]), "d1_block_headers": sum(
                # same rule as libredwg_map: the object name is empty on 409/442 P7757 rows, so detect by type 49
                1 for o in dec["OBJECTS"] if o.get("object") == "BLOCK_HEADER" or o.get("type") == 49),
            "dxf_block_definitions": len(index["blocks"])}


# ====================================================================== Qortuba plan variants
def qortuba_variants(index, region_bounds, proof):
    """The four 'SECOND FLOOR PLAN' layouts, by drawing evidence: title text position, handle ranges, content."""
    ents = index["entities"]
    labels = sorted([e for e in ents if (e.get("1") or "").strip().upper() == "SECOND FLOOR PLAN"],
                    key=lambda e: float(e["20"]))
    ys = [float(e["20"]) for e in labels]

    def band(y):
        k = None
        for i, ly in enumerate(ys):
            if y >= ly - 300:
                k = i
        return k
    x_lo, x_hi = min(float(e["10"]) for e in labels) - 4000, max(float(e["10"]) for e in labels) + 4000
    content, handles = {i: Counter() for i in range(len(labels))}, {i: [] for i in range(len(labels))}
    outside = Counter()
    for e in ents:
        try:
            x, y = float(e["10"]), float(e["20"])
        except (KeyError, ValueError):
            outside["NO_POSITION"] += 1
            continue
        b = band(y) if x_lo < x < x_hi else None
        if b is None:
            outside[e["type"]] += 1
            continue
        content[b][f"{e['type']}/{e.get('8')}"] += 1
        handles[b].append(int(e["5"], 16))
    variants = []
    for i, lab in enumerate(labels):
        variants.append({"label_handle": lab["5"], "label_position": [float(lab["10"]), float(lab["20"])],
                         "entities": sum(content[i].values()),
                         "handle_range": [format(min(handles[i]), "X"), format(max(handles[i]), "X")] if handles[i] else None,
                         "newest_handle": format(max(handles[i]), "X") if handles[i] else None,
                         "differs_from_bottom_most_on_type_layer_keys": sum(
                             1 for k in set(content[i]) | set(content[0]) if content[i][k] != content[0][k])})
    # name by position: top-most is variant 1 ... bottom-most is variant 4
    order = sorted(range(len(variants)), key=lambda i: -variants[i]["label_position"][1])
    for rank, i in enumerate(order):
        variants[i]["variant_id"] = f"PLAN_VARIANT_{rank + 1}" + ("_SELECTED_CANDIDATE" if rank == len(order) - 1 else "")
        variants[i]["position_rank_from_top"] = rank + 1
    newest = max(variants, key=lambda v: int(v["newest_handle"], 16))
    bottom = min(variants, key=lambda v: v["label_position"][1])
    return {"variants": variants, "bottom_most_label_handle": bottom["label_handle"],
            "variant_with_newest_edit": newest["label_handle"],
            "bottom_most_is_the_most_recently_edited": newest is bottom,
            "creation_order_by_label_handle": [v["label_handle"] for v in sorted(variants, key=lambda v: int(v["label_handle"], 16))],
            "outside_the_four_plans": dict(outside),
            "tracked_dwg_region": {"region_id": "RC:MODEL_SPACE:4267:540:1649", "bounds": list(region_bounds),
                                   "contains_label_handle": "1AC"},
            "note": ("'last' is ambiguous: by creation order the top-most copy (label 3690) is the newest COPY; by edit "
                     "history the bottom-most plan carries the newest edits. Both readings are recorded; the owner "
                     "review decides")}


def revision_evidence(index, d1_identity, region_bounds, d1_handseed_hex):
    x0, y0, x1, y1 = region_bounds
    added = [e for e in index["entities"] if int(e["5"], 16) > int(d1_handseed_hex, 16)
             and x0 <= float(e.get("10", "nan") or "nan") <= x1 and y0 - 300 <= float(e.get("20", "nan") or "nan") <= y1]
    return {"source_entities_missing_from_dxf": d1_identity["missing_in_dxf"],
            "entities_added_inside_region": len(added),
            "added_by_type_layer": dict(Counter(f"{e['type']}/{e.get('8')}" for e in added)),
            "added_handle_range": [format(min(int(e["5"], 16) for e in added), "X"),
                                   format(max(int(e["5"], 16) for e in added), "X")] if added else None}


# ====================================================================== main
def main(work: Path, out: Path):
    work, out = Path(work), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    roots = [BY_SHA256, UPLOADS, work]
    proof = json.loads((ROOT / "tests/r8_6/registers/QORTUBA_ROUND1_PROOF.json").read_text())
    region = json.loads((work / "qortuba_region.json").read_text())
    intake, prov, fid, recon = {}, {}, {}, {}
    ref = {"LIBREDWG_0_13_3_DWG2DXF": {k: scan(work / f"{k}_libredwg.dxf") for k in ("P7757", "QORTUBA")}}
    for name, f in FILES.items():
        dxf_paths = find_by_hash(f["dxf_sha256"], roots)
        dwg_paths = find_by_hash(f["dwg_sha256"], [UPLOADS])
        dxf = Path(dxf_paths[0])
        s = scan(dxf)
        index = json.loads((work / f"{name.lower()}_index.json").read_text())
        writer = IX.writer_fingerprint(s["header"], s["comments"], s["sections"], s["acadmaintver_group_code"])
        decoder = IX.decoder_provenance(writer, None)
        decode_path = (ROOT / f["decode"]) if f["decode"] else work / "ST7757_D1.json"
        ident = identity_vs_d1(decode_path, index)
        dh = d1_header(f["decode"]) if f["decode"] else {}
        if not dh:
            d = json.loads(decode_path.read_text(encoding="utf-8", errors="replace"))
            dh = {"FINGERPRINTGUID": d["HEADER"].get("FINGERPRINTGUID"), "VERSIONGUID": d["HEADER"].get("VERSIONGUID"),
                  "INSUNITS": d["HEADER"].get("INSUNITS"), "HANDSEED": d["HEADER"].get("HANDSEED"),
                  "TDINDWG": d["HEADER"].get("TDINDWG"), "TDUCREATE": d["HEADER"].get("TDUCREATE"),
                  "TDUUPDATE": d["HEADER"].get("TDUUPDATE"), "version": d.get("FILEHEADER", {}).get("version")}
        handseed_hex = format(dh["HANDSEED"][-1], "X") if isinstance(dh.get("HANDSEED"), list) else None
        if name == "QORTUBA":
            rev_ev = revision_evidence(index, ident, region["bounds"], handseed_hex)
            added = rev_ev["entities_added_inside_region"]
        else:
            added = sum(1 for e in index["entities"] if handseed_hex and int(e["5"], 16) > int(handseed_hex, 16))
            rev_ev = {"source_entities_missing_from_dxf": ident["missing_in_dxf"], "dxf_entities_with_handle_above_source_handseed": added}
        revision = IX.revision_identity(dh, s["header"], ident["missing_in_dxf"], added)
        declared = {"tool": None, "operations": None, "requested_format": None,
                    "exported_from_sha256": f["dwg_sha256"], "exported_by": "converted for the owner through ChatGPT; "
                                                                             "tool and settings not recorded"}
        adm = IX.admission_v2(f["dxf_sha256"], s["header"], writer, decoder, revision, declared, f["dwg_sha256"])
        rc = json.loads((work / f"{name.lower()}_reconcile.json").read_text())
        intake[name] = {"dxf_sha256": f["dxf_sha256"], "found_as": sorted(Path(x).name for x in dxf_paths),
                        "dwg_sha256": f["dwg_sha256"], "dwg_found_as": sorted(Path(x).name for x in dwg_paths),
                        "located_by": "SHA-256 search of the session inputs; no path is frozen truth", "role": f["role"], "transport": f.get("transport"),
                        "file_size_bytes": dxf.stat().st_size, "header": s["header"],
                        "acadmaintver_group_code": s["acadmaintver_group_code"], "comments_999": s["comments"],
                        "sections": s["sections"], "crlf": s["crlf"], "class_count": len(s["classes"]),
                        "custom_classes_of_interest": sorted(c for c in s["classes"] if c in (
                            "ARC_DIMENSION", "RTEXT", "SORTENTSTABLE", "WIPEOUT", "IMAGE", "DIMASSOC", "ACAD_PROXY_ENTITY")),
                        "census": s["census"], "handles": s["handles"], "owner_references": s["owner_references"],
                        "dwg_header_from_d1": dh, "modified_by_urban": False, "normalised_by_urban": False}
        prov[name] = {"DXF_WRITER": writer, "DWG_DECODER": decoder,
                      "editing_time_evidence": editing_time_evidence(dh, s["header"]),
                      "SOURCE_METADATA_LASTSAVEDBY": s["header"].get("$LASTSAVEDBY"),
                      "converter_provenance": "CONVERTER_UNKNOWN: converted for the owner through ChatGPT; no tool name, "
                                              "version, settings or log was supplied",
                      "revision": revision, "revision_evidence": rev_ev, "admission_v2": adm}
        geometry_ok = rc["summary"]["verdict"] == "PASS"
        fidelity = ("SOURCE_FIDELITY_PASS" if revision["state"] == IX.SAME_REVISION and ident["different"] <= 3
                    and geometry_ok and ident["missing_in_dxf"] == 0 else
                    "SOURCE_FIDELITY_FAIL" if revision["state"] == IX.SAME_LINEAGE_DIFFERENT_REVISION else
                    "SOURCE_FIDELITY_PARTIAL" if geometry_ok else "SOURCE_FIDELITY_NOT_ESTABLISHED")
        fid[name] = {"result": fidelity, "against_source": f["dwg_sha256"], "identity": ident,
                     "geometry_reconciliation": rc["summary"], "visibility_rows_nonpass": rc["summary"]["non_pass_by_field"].get("VISIBILITY", 0),
                     "intake_class": ("HIGH_FIDELITY_PROVENANCE_UNVERIFIED_DXF" if fidelity == "SOURCE_FIDELITY_PASS"
                                      and adm["status"] == IX.PROVENANCE_UNVERIFIED else
                                      "DIFFERENT_SOURCE_REVISION_PROVENANCE_UNVERIFIED_DXF" if revision["state"] ==
                                      IX.SAME_LINEAGE_DIFFERENT_REVISION else adm["status"]),
                     "basis": "measured from the files; no quantity agreement is used"}
        recon[name] = {"signature_states": IX.scoped_signature_states(rc["signature_diagnostic_states"], adm),
                       "signature_detail": rc["signature_detail"], "summary": rc["summary"]}
    qv = qortuba_variants(json.loads((work / "qortuba_index.json").read_text()), region["bounds"], proof)
    prior = json.loads((ROOT / "tests/r8_5/registers/R8_INDEPENDENT_EXPORT_INTAKE.json").read_text())
    write = lambda n, o: (out / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")  # noqa: E731
    write("DXF_INTAKE_REGISTER", {"SCHEMA": "URBAN_R8_6A_DXF_INTAKE_REGISTER_V1", "files": intake,
                                  "identified_by": "SHA-256 of the bytes; file names are ignored",
                                  "reference_writer_fingerprints": {k: {p: {"comments_999": v["comments"],
                                                                            "acadmaintver_group_code": v["acadmaintver_group_code"],
                                                                            "header_acadver": v["header"].get("$ACADVER"),
                                                                            "header_acadmaintver": v["header"].get("$ACADMAINTVER"),
                                                                            "sections": v["sections"]}
                                                                        for p, v in d.items()} for k, d in ref.items()},
                                  "history_previous_rejected_conversions": [
                                      {"file": e["file"], "sha256": e.get("sha256") or e.get("admission", {}).get("file_sha256"),
                                       "status": e["admission"]["status"], "writer_in_file": e["admission"]["writer_in_file"],
                                       "register": "tests/r8_5/registers/R8_INDEPENDENT_EXPORT_INTAKE.json (unchanged)"}
                                      for e in prior["exports"]]})
    write("DXF_PROVENANCE_REGISTER", {"SCHEMA": "URBAN_R8_6A_DXF_PROVENANCE_REGISTER_V1",
                                      "decoder_states": list(IX.DECODER_STATES), "files": prov,
                                      "rule": "writer, decoder and source metadata are separate facts; only a conversion "
                                              "record with hashed evidence can prove a decoder"})
    write("SOURCE_FIDELITY_RESULTS", {"SCHEMA": "URBAN_R8_6A_SOURCE_FIDELITY_V1", "files": fid})
    write("QORTUBA_ROUND1_DXF_RESULTS", {"SCHEMA": "URBAN_R8_6A_QORTUBA_ROUND1_DXF_V1",
                                         "INDEPENDENT_QORTUBA_RECONCILIATION": "BLOCKED_EXTERNAL_PROVENANCE",
                                         "also_blocked_by": "SOURCE_REVISION_MISMATCH: the DXF is an export of a later "
                                                            "revision of the drawing, not of " + FILES["QORTUBA"]["dwg_sha256"],
                                         "round1_counts_from_committed_register": {
                                             k: json.loads((ROOT / "tests/r8_6/registers/ROUND1_CAPABILITY_SIGNATURES.json").read_text())[k]
                                             for k in ("required_count", "round1_observations", "round1_occurrences",
                                                       "occurrences_inside_block_instances", "net_reflected_occurrences")},
                                         "signatures": recon["QORTUBA"], "plan_variants": qv,
                                         "revision_evidence": prov["QORTUBA"]["revision_evidence"],
                                         "qualified": 0})
    write("P7757_DXF_RESULTS", {"SCHEMA": "URBAN_R8_6A_P7757_DXF_V1",
                                "handle_0x929": {"dxf_type": next((e["type"] for e in json.loads(
                                    (work / "p7757_index.json").read_text())["entities"] if e.get("5", "").upper() == "929"), None),
                                    "d1_type": "UNSUPPORTED (LIBREDWG:763)",
                                    "previous_rejected_ezdxf_rebuild": "LINE (R8.5 intake: custom classes missing)"},
                                "signatures": recon["P7757"], "structural_ST7757": recon["ST7757"], "qualified": 0,
                                "classification": fid["P7757"]["intake_class"]})
    print({k: (fid[k]["result"], fid[k]["intake_class"], prov[k]["admission_v2"]["status"], prov[k]["revision"]["state"])
           for k in fid})
    return intake, prov, fid, recon, qv


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
