"""R8.3 §3/§4/§27 — pinned LibreDWG re-decode of every original DWG present, compared with
the historical decode. Research lab only; nothing in engine/ imports this.

For each project:
    hash the DWG; run the REGISTERED dwgread; write a NEW artifact under
    data/runs/pinned_redecode/ (the historical JSON is never touched); hash it; compare the
    historical and pinned representations (bytes, UTF-8 normalisation, SRD, row / type
    census, handle representation, ownership / layer / block references, visibility,
    units header). Every delta is classified SAME / EXPLAINED_DELTA / UNEXPLAINED_DELTA.
    No quantity is compared: a source delta is judged on source terms only.

    python3 research/external_engine_lab/r8_3_pinned_redecode.py > out.json
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import decoder_pins as PINS                  # noqa: E402
from engine.source.cad import libredwg_map as L                 # noqa: E402

DWGREAD = Path("/tmp/ldwg/programs/dwgread")
CONFIG_LOG = Path("/tmp/ldwg/config.log")
UPLOADS = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
OUT = ROOT / "data/runs/pinned_redecode"
PROJECTS = {
    "ALRASHED": {"dwg": [UPLOADS / "a0f821ff-16-11-2025.dwg", UPLOADS / "34d0ab9e-16-11-2025.dwg"],
                 "historical": ROOT / "data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json"},
    "P7757": {"dwg": [ROOT / "data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg", UPLOADS / "79500133-P7757.dwg"],
              "historical": ROOT / "data/runs/cad_convert/P7757_ARCHITECTURAL.json"},
    "QORTUBA": {"dwg": [UPLOADS / "b634a91b-qurtoba1.dwg", UPLOADS / "dab4c836-qurtoba.dwg"],
                "historical": ROOT / "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json"},
}


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_provenance() -> dict:
    """What is recorded about how the pinned binary was built (never guessed)."""
    rec = {"configure_invocation": None, "CC": None, "CFLAGS": None, "host": None,
           "status": "BUILD_CONFIGURATION_NOT_FULLY_RECORDED"}
    if CONFIG_LOG.exists():
        for ln in CONFIG_LOG.read_text(errors="replace").splitlines():
            s = ln.strip()
            if s.startswith("$ ./configure") and rec["configure_invocation"] is None:
                rec["configure_invocation"] = s[2:]
            for k in ("CC", "CFLAGS", "host"):
                if s.startswith(k + "=") and rec[k] is None:
                    rec[k] = s.split("=", 1)[1].strip("'")
        rec["config_log_sha256"] = sha(CONFIG_LOG)
        rec["note"] = ("configure line, compiler and CFLAGS recovered from the build tree's config.log; the "
                       "compiler version, libc and source tarball hash are not recorded, so the build is not "
                       "fully reproducible from records alone. The executable hash still pins THIS binary.")
    return rec


def decode(dwg: Path, dst: Path) -> dict:
    cmd = [str(DWGREAD), "-O", "JSON", "-o", str(dst), str(dwg)]
    t0 = dt.datetime.now(dt.timezone.utc)
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=1800)
    t1 = dt.datetime.now(dt.timezone.utc)
    err = p.stderr.splitlines()
    return {"command": cmd, "exit_code": p.returncode, "started": t0.isoformat(), "finished": t1.isoformat(),
            "stderr_lines": len(err), "stderr_error_lines": sum(1 for x in err if x.startswith("ERROR")),
            "stderr_warning_lines": sum(1 for x in err if x.startswith("Warning")),
            "stderr_head": err[:5]}


def census(d: dict) -> dict:
    objs = d.get("OBJECTS", [])
    kinds = Counter(o.get("entity") or o.get("object") or "?" for o in objs)
    three_byte = [o for o in objs if isinstance(o.get("handle"), list) and len(o["handle"]) >= 3
                  and o["handle"][1] == 3]
    truncated = [o for o in three_byte if o["handle"][-1] <= 0xFFFF]
    vals = Counter(o["handle"][-1] for o in objs if isinstance(o.get("handle"), list))
    return {
        "rows": len(objs), "by_type": dict(sorted(kinds.items())),
        "handles_3_byte": len(three_byte), "handles_3_byte_printed_16_bit": len(truncated),
        "colliding_handle_values": sum(1 for v, n in vals.items() if n > 1),
        "ownerhandle_refs": sum(1 for o in objs if "ownerhandle" in o),
        "layer_refs": sum(1 for o in objs if "layer" in o),
        "block_header_refs": sum(1 for o in objs if "block_header" in o),
        "invisible": sum(1 for o in objs if o.get("invisible")),
        "header_units": {k: d.get("HEADER", {}).get(k) for k in
                         ("INSUNITS", "MEASUREMENT", "LUNITS", "LUPREC", "DIMLFAC", "DIMSCALE", "DIMLUNIT",
                          "DIMPOST", "DIMDEC", "DIMSTYLE")},
        "srd": L.source_representation_digest(d),
    }


def _json(path: Path):
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8")), 0
    except UnicodeDecodeError:
        txt = raw.decode("utf-8", errors="replace")
        return json.loads(txt), txt.count("�")


def compare(hist: Path, pinned: Path) -> dict:
    hb, pb = hist.read_bytes(), pinned.read_bytes()
    out = {"historical_sha256": hashlib.sha256(hb).hexdigest(), "pinned_sha256": hashlib.sha256(pb).hexdigest(),
           "historical_bytes": len(hb), "pinned_bytes": len(pb), "byte_identical": hb == pb}
    pinned_valid_utf8 = True
    try:
        pb.decode("utf-8")
    except UnicodeDecodeError:
        pinned_valid_utf8 = False
    out["pinned_valid_utf8"] = pinned_valid_utf8
    normalised = pb.decode("utf-8", errors="replace").encode("utf-8")
    out["identical_after_utf8_replacement_normalisation"] = normalised == hb
    out["utf8_replacement_characters_introduced"] = normalised.decode("utf-8").count("�") - \
        pb.decode("utf-8", errors="ignore").count("�")
    hd, _ = _json(hist)
    pd, _ = _json(pinned)
    ch, cp = census(hd), census(pd)
    out["census_historical"], out["census_pinned"] = ch, cp
    fields = {}
    for k in ch:
        fields[k] = "SAME" if ch[k] == cp[k] else "DIFFERENT"
    out["field_comparison"] = fields
    # row-by-row structural comparison (only when the byte comparison did not already decide)
    if not out["byte_identical"] and not out["identical_after_utf8_replacement_normalisation"]:
        diffs = Counter()
        for a, b in zip(hd.get("OBJECTS", []), pd.get("OBJECTS", [])):
            if a != b:
                for k in set(a) | set(b):
                    if a.get(k) != b.get(k):
                        diffs[k] += 1
        out["row_field_differences"] = dict(diffs.most_common(40))
    if out["byte_identical"]:
        out["classification"], out["explanation"] = "SAME", "byte-identical"
    elif out["identical_after_utf8_replacement_normalisation"]:
        out["classification"] = "EXPLAINED_DELTA"
        out["explanation"] = ("the historical file is the pinned output with invalid UTF-8 bytes replaced by U+FFFD "
                              "(the documented Arabic-font normalisation); no other byte differs")
    else:
        out["classification"] = "UNEXPLAINED_DELTA"
        out["explanation"] = "see row_field_differences"
    return out


RELATIVE = {6, 8, 10, 12}
CONSUMERS = {
    "ACTIVE": "none: Al Rashed R7 labels are read from the issued PDF (pa09/alrashed/labels.py) and the project "
              "reader (pa09/alrashed/geometry.py) reads LINE / LWPOLYLINE only; cad_adapter is not on that path",
    "FUTURE": "room-area label parsing (the m² markers sit next to area values), label / opening identity from "
              "DWG text (the two legacy-font Arabic strings)",
}


def text_delta_review(pinned: Path, hist: Path) -> dict:
    """Every U+FFFD the historical normalisation introduced: exact entity, raw pinned bytes,
    historical string, candidate code-page readings, consumers and impact (review §2)."""
    pb = pinned.read_bytes()
    bad, i = [], 0
    while True:
        try:
            pb[i:].decode("utf-8")
            break
        except UnicodeDecodeError as e:
            st = i + e.start
            bad.append((st, pb[st:i + e.end]))
            i = i + e.end
    hd, _ = _json(hist)
    layers = {o["handle"][-1]: o.get("name") for o in hd["OBJECTS"] if o.get("object") == "LAYER"}
    rows = []
    for o in hd["OBJECTS"]:
        for k, v in o.items():
            if isinstance(v, str) and "\ufffd" in v:
                rows.append({"handle": o.get("handle"), "type_code": o.get("type"),
                             "entity": o.get("entity") or o.get("object"), "field": k,
                             "layer": layers.get((o.get("layer") or [None])[-1]), "entmode": o.get("entmode"),
                             "historical_string": v})
    for r, (off, raw) in zip(rows, bad):          # both lists are in file order
        r["pinned_raw_bytes_hex"] = raw.hex()
        r["pinned_byte_offset"] = off
        ctx = pb[max(0, off - 40):off + 8]
        r["pinned_context"] = ctx.decode("utf-8", errors="backslashreplace")[-60:]
        r["readings"] = {cp: raw.decode(cp, errors="replace") for cp in ("cp1252", "cp1256")}
        r["reason"] = ("the DWG stores this text in a single-byte code page; dwgread 0.13.3 copies the byte into "
                       "its JSON verbatim, which is not valid UTF-8; the historical normalisation replaced it with U+FFFD")
    return {"invalid_sequences_in_pinned": len(bad), "rows": rows,
            "rows_by_reading": {k: sum(1 for r in rows if r.get("readings", {}).get("cp1252") == k)
                                for k in sorted({r.get("readings", {}).get("cp1252") for r in rows} - {None})},
            "consumers": CONSUMERS,
            "impact": [{"domain": "DOCUMENT_CONTENT", "severity": "REVIEW"},
                       {"domain": "IDENTITY", "severity": "BLOCKING"}],
            "finding": "TEXT_UNDECODABLE (raised by the capability census on exactly these rows; "
                       "identity_source_allowed = false)",
            "geometry_effect": "none: every changed byte is inside a text string",
            "classification": "EXPLAINED_DELTA (text-decoding delta, not geometry-identical-therefore-harmless)"}


def affected_references(d: dict) -> dict:
    """References whose target value collides (the truncation's blast radius)."""
    objs = d.get("OBJECTS", [])
    vals = Counter(o["handle"][-1] for o in objs if isinstance(o.get("handle"), list))
    coll = {v for v, n in vals.items() if n > 1}
    out = Counter()

    def walk(x, key):
        if isinstance(x, list) and len(x) == 4 and all(isinstance(v, int) for v in x) and key != "handle":
            if x[3] in coll:
                out["relative_untrusted" if x[0] in RELATIVE else "absolute_resolved_by_size"] += 1
            return
        if isinstance(x, list):
            for v in x:
                walk(v, key)
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, k)
    for o in objs:
        for k, v in o.items():
            if k != "handle":
                walk(v, k)
    return {"colliding_values": len(coll), **dict(out)}


def attribution(cmp: dict) -> str:
    """PINNED_REPRODUCED only when the pinned output itself shows the truncation."""
    cp, ch = cmp["census_pinned"], cmp["census_historical"]
    if ch["handles_3_byte_printed_16_bit"] == 0:
        return "NOT_APPLICABLE_NO_TRUNCATION_IN_HISTORICAL"
    if cmp["classification"] == "UNEXPLAINED_DELTA":
        return "UNEXPLAINED_DELTA"
    if cp["handles_3_byte_printed_16_bit"] == ch["handles_3_byte_printed_16_bit"]:
        return "PINNED_REPRODUCED"
    return "PINNED_NOT_REPRODUCED"


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    exe = {"path": str(DWGREAD), "present": DWGREAD.exists()}
    if DWGREAD.exists():
        exe["sha256"] = sha(DWGREAD)
        exe["reported_version"] = subprocess.run([str(DWGREAD), "--version"], capture_output=True,
                                                 text=True).stdout.strip()
        exe["pin_status"] = PINS.status("LIBREDWG_DWGREAD", exe["sha256"])
    res = {"SCHEMA": "URBAN_R8_3_PINNED_REDECODE_V1", "decoder": exe, "build_provenance": build_provenance(),
           "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(),
                        "python": platform.python_version()},
           "projects": {}}
    for proj, s in PROJECTS.items():
        dwgs = [p for p in s["dwg"] if p.exists()]
        rec = {"dwg_candidates": [{"path": str(p), "present": p.exists(), "sha256": sha(p) if p.exists() else None}
                                  for p in s["dwg"]],
               "historical_decode": str(s["historical"].relative_to(ROOT)),
               "historical_sha256": sha(s["historical"]) if s["historical"].exists() else None}
        if not dwgs or not DWGREAD.exists():
            rec["status"] = "NOT_EXECUTED_SOURCE_MISSING" if not dwgs else "NOT_EXECUTED_DECODER_MISSING"
            res["projects"][proj] = rec
            continue
        hashes = {sha(p) for p in dwgs}
        rec["distinct_dwg_hashes"] = sorted(hashes)
        dwg = dwgs[0]
        dst = OUT / f"{proj}_PINNED_REDECODE.json"
        rec["run"] = decode(dwg, dst)
        rec["source_dwg"], rec["source_sha256"] = str(dwg), sha(dwg)
        if not dst.exists():
            rec["status"] = "PINNED_DECODE_FAILED"
            res["projects"][proj] = rec
            continue
        rec["output"] = {"path": str(dst.relative_to(ROOT)), "sha256": sha(dst), "bytes": dst.stat().st_size}
        rec["comparison"] = compare(s["historical"], dst)
        rec["handle_truncation_attribution"] = attribution(rec["comparison"])
        hd, _ = _json(s["historical"])
        rec["affected_references"] = affected_references(hd)
        if rec["comparison"]["utf8_replacement_characters_introduced"]:
            rec["text_delta_review"] = text_delta_review(dst, s["historical"])
        rec["status"] = rec["comparison"]["classification"]
        res["projects"][proj] = rec
    rep = [p for p, r in res["projects"].items() if r.get("handle_truncation_attribution") == "PINNED_REPRODUCED"]
    res["defect"] = {
        "id": "PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT",
        "previous_name": "OBSERVED_HANDLE_TRUNCATION_IN_EXISTING_LIBREDWG_JSON",
        "route": "LibreDWG dwgread 0.13.3 -O JSON (pinned binary)",
        "binary_sha256": exe.get("sha256"),
        "reproduction_count": len(rep), "reproduced_on": rep,
        "per_project": {p: {"source_sha256": res["projects"][p]["source_sha256"],
                            "command": res["projects"][p]["run"]["command"],
                            "output_sha256": res["projects"][p]["output"]["sha256"],
                            "handles_3_byte_printed_16_bit":
                                res["projects"][p]["comparison"]["census_pinned"]["handles_3_byte_printed_16_bit"],
                            "colliding_handle_values":
                                res["projects"][p]["comparison"]["census_pinned"]["colliding_handle_values"],
                            "affected_references": res["projects"][p]["affected_references"]} for p in rep},
        "localisation": "NOT_LOCALISED: parser, internal representation or JSON writer. dwg2dxf output of P7757 "
                        "ends at handle 0x31DD, before any 3-byte handle, so the DXF route cannot localise it",
    }
    (OUT / "PINNED_REDECODE_RESULTS.json").write_text(json.dumps(res, indent=1, default=str))
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=str))
