"""R8.7 addendum — is the supplied DWG the exact source of the new-revision DXF?

The candidate DWG is decoded with the PINNED LibreDWG dwgread (binary hash checked). Every comparison the decode
allows is recorded; the verdict follows fixed rules and is never forced:

    SAME_EXACT_SOURCE_REVISION       lineage + version GUID + handle seed equal, < 600 s editing added, and every
                                     compared record (entities, blocks, inserts, four plans, selected plan) equal
    SAME_LINEAGE_DIFFERENT_REVISION  same lineage, content or handle seed differs
    NOT_THE_CORRESPONDING_DWG        a different drawing lineage
    NOT_ESTABLISHED                  a required comparison could not be made (e.g. the decoder cannot read the
                                     header / objects sections)

Matching establishes SOURCE REVISION IDENTITY only; it never establishes the DXF converter or parser independence.

    python3 research/external_engine_lab/r8_7_dwg_anchor.py <dwg> <dxf> <work_dir> <out_json>
"""

from __future__ import annotations

import binascii
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_6a_intake as INTAKE                                                  # noqa: E402
from engine.source import decoder_pins as PINS                                 # noqa: E402

DWGREAD = Path("/tmp/ldwg/programs/dwgread")
REQUIRED = ("HEADER: FINGERPRINTGUID / VERSIONGUID / HANDSEED / INSUNITS", "CLASSES", "OBJECTS: entity handles, census, "
            "block records, INSERT lineage, four plans, title 0x1AC, selected plan geometry, wall edits")


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def days(pair):
    return None if not pair else pair[0] + pair[1] / 86_400_000


def run_decoder(dwg, work):
    """The pinned decoder, JSON output plus its verbose log (the log is the only record when the decode fails)."""
    pin = PINS.PINS["LIBREDWG_DWGREAD"][0]
    binary_ok = DWGREAD.exists() and sha(DWGREAD) == pin["sha256"]
    out_json, log = Path(work) / "NEW_DWG_D1.json", Path(work) / "NEW_DWG_D1.v3.log"
    if not binary_ok:
        return {"binary_matches_pin": False}, None, ""
    p = subprocess.run([str(DWGREAD), "-v3", "-O", "JSON", "-o", str(out_json), str(dwg)], capture_output=True,
                       text=True, errors="replace", timeout=3600)
    log.write_text(p.stdout + p.stderr)
    text = log.read_text(errors="replace")
    return ({"binary_matches_pin": True, "binary_sha256": pin["sha256"], "version": pin["version"],
             "command": ["dwgread", "-v3", "-O", "JSON", "-o", "<out>", "<dwg>"], "exit_code": p.returncode,
             "json_written": out_json.exists() and out_json.stat().st_size > 0},
            out_json if out_json.exists() and out_json.stat().st_size > 0 else None, text)


def read_log(text):
    """What the decoder reported, from its own verbose log: sections read / failed, SummaryInfo, AppInfoHistory."""
    errors = sorted(set(re.findall(r"ERROR: (.+)", text)))
    flags = re.findall(r"Critical: (.+)", text)
    summ = {}
    for key in ("LASTSAVEDBY", "TDINDWG", "TDCREATE", "TDUPDATE"):
        m = re.search(rf"^{key}: (.+?) \[", text, re.M)
        if m:
            summ[key] = m.group(1)
    def pair(s):
        m = re.match(r"\[(\d+), (\d+)\]", s or "")
        return [int(m.group(1)), int(m.group(2))] if m else None
    app = {}
    m = re.search(r"^AppInfoHistory \(\d+\)\n-+\n([0-9A-F]+)$", text, re.M)
    if m:
        raw = binascii.unhexlify(m.group(1)).decode("utf-16-le", errors="ignore")
        for tag, pat in (("saved_at", r"<datetime>([^<]+)</datetime>"), ("saved_by", r'prop id="8"><string>([^<]+)<'),
                         ("product", r'prop id="258"><string>([^<]+)<'), ("build", r'prop id="259"><string>([^<]+)<'),
                         ("registry_version", r'registry_version=\\"([^\\"]+)'),
                         ("trusted_dwg", r"(This file is a Trusted DWG[^.]*\.)")):
            mm = re.search(pat, raw)
            app[tag] = mm.group(1) if mm else None
    sections_failed = sorted({s for s in re.findall(r"Failed to read (?:un)?compressed (\w+) section", text)})
    return {"errors": errors, "critical_flags": flags, "sections_failed": sections_failed,
            "summary_info": {"LASTSAVEDBY": (summ.get("LASTSAVEDBY") or "").strip('"') or None,
                             "TDINDWG": pair(summ.get("TDINDWG")), "TDCREATE": pair(summ.get("TDCREATE")),
                             "TDUPDATE": pair(summ.get("TDUPDATE"))},
            "app_info_history": app,
            "file_version": (re.search(r"version code is: (\w+)", text) or [None, None])[1]}


def main(dwg, dxf, work, out):
    dwg, dxf = Path(dwg), Path(dxf)
    dec, d1_json, text = run_decoder(dwg, work)
    log = read_log(text) if text else {}
    dh = INTAKE.scan(dxf)["header"]
    si = log.get("summary_info", {})
    td_dwg, td_dxf = days(si.get("TDINDWG")), INTAKE.days(dh.get("$TDINDWG"))
    partial = {
        "file_version": {"dwg": log.get("file_version"), "dxf": dh.get("$ACADVER"),
                         "equal": log.get("file_version") == dh.get("$ACADVER")},
        "LASTSAVEDBY": {"dwg_summary_info": si.get("LASTSAVEDBY"), "dxf": dh.get("$LASTSAVEDBY"),
                        "equal": si.get("LASTSAVEDBY") == dh.get("$LASTSAVEDBY")},
        "TDCREATE": {"dwg_summary_info_julian": days(si.get("TDCREATE")), "dxf_TDUCREATE": INTAKE.days(dh.get("$TDUCREATE")),
                     "equal": days(si.get("TDCREATE")) is not None and
                     abs(days(si.get("TDCREATE")) - INTAKE.days(dh.get("$TDUCREATE"))) < 1e-6},
        "TDINDWG": {"dwg_summary_info_days": td_dwg, "dxf_days": td_dxf,
                    "dxf_minus_dwg_seconds": None if td_dwg is None or td_dxf is None else round((td_dxf - td_dwg) * 86400, 1)},
        "TDUPDATE": {"dwg_summary_info_julian_local": days(si.get("TDUPDATE")), "dxf_local": INTAKE.days(dh.get("$TDUPDATE"))},
        "last_saved_by_application": log.get("app_info_history"),
    }
    readable = bool(d1_json) and not ({"Header", "Classes", "AcDbObjects"} & set(log.get("sections_failed", [])))
    if not readable:
        verdict = "NOT_ESTABLISHED"
        why = ("the pinned decoder could not read the DWG's Header, Classes and AcDbObjects sections "
               f"({'; '.join(log.get('errors', [])[:4])}); FINGERPRINTGUID, VERSIONGUID, HANDSEED, INSUNITS, entity "
               "handles, census, block records, INSERT lineage, the four plans, title 0x1AC and the selected plan "
               "geometry cannot be compared")
    else:                                                     # never reached with this decoder build; kept explicit
        verdict, why = "NOT_ESTABLISHED", "full comparison not implemented for a readable decode in this round"
    res = {"SCHEMA": "URBAN_R8_7_NEW_DWG_SOURCE_IDENTITY_V1",
           "candidate_dwg": {"sha256": sha(dwg), "bytes": dwg.stat().st_size, "store": f"data/inputs/by_sha256/{sha(dwg)}.dwg",
                             "transport": "1fd0405d-qurtoba_villah.zip (sha256 45532010...); one entry, 35,110,771 bytes",
                             "identified_by": "SHA-256 of the extracted bytes (file names ignored)"},
           "compared_with_dxf": sha(dxf),
           "decoder": dec, "decoder_report": {k: log.get(k) for k in ("errors", "critical_flags", "sections_failed")},
           "required_comparisons": list(REQUIRED), "required_comparisons_possible": readable,
           "partial_evidence_read": partial,
           "partial_evidence_reading": ("consistent with the DWG being the DXF's source (same lineage creation time, same "
                                        "user, the DXF's editing time = the DWG's + ~2 min, the DXF written after the DWG's "
                                        "last AutoCAD 2023 save), but these fields cannot exclude an edit made during "
                                        "that session: they do not decide identity"),
           "verdict": verdict, "why": why,
           "consequences": {"source_anchor": "UNCHANGED: QORTUBA_REV_NEW stays anchored to DXF df0e1d69 (pending)",
                            "owner_claims": "NOT re-anchored (v1 claims stay ACTIVE, pending-anchor, SHADOW only)",
                            "SUPPLY_QORTUBA_NEW_REVISION_DWG": "FILE_RECEIVED (the owner's part is done); "
                                                               "identity not established",
                            "parser_independence": "unaffected: CONVERTER_UNKNOWN, nothing qualified"},
           "to_establish": ["a DWG decoder that reads AutoCAD 2018-format (AC1032) object sections, pinned and recorded "
                            "(a newer LibreDWG build or the ODA File Converter); the environment currently denies "
                            "github.com and ftp.gnu.org, so none can be installed here",
                            "then run the full comparison and re-anchor only on SAME_EXACT_SOURCE_REVISION"],
           "decision_rules": __doc__.split("\n\n")[1]}
    Path(out).write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(verdict, "|", why[:200])
    print(json.dumps(partial, default=str)[:1500])
    return res


if __name__ == "__main__":
    main(*sys.argv[1:5])
