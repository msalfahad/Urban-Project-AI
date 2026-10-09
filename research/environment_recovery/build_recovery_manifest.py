"""Environment recovery manifest: every test prerequisite missing from this checkout, with its expected identity.

    python3 -I research/environment_recovery/build_recovery_manifest.py [<junit.xml of a full-suite run>]

Sources of the list:
  * the full-suite run's JUnit XML: every FileNotFoundError path and every skip reason that names a path;
  * a static scan of tests/*.py for data/ path literals (paths a failing test never reached);
  * tracked identity records that pin a sha256 to a path: tests/r8_6|r8_7/FIXTURE_MANIFEST.json,
    runs/golden/23010_MANIFEST.json, tests/alsenan/registers/SOURCE_MANIFEST.json (content-addressed inputs).
Writes RECOVERY_MANIFEST.json and INPUTS.lock.proposed.json. Records paths, hashes and producers only: no file
content, no client drawing, no credential. Paths that tests build on purpose as non-existent are excluded.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATE = "2026-10-09"
RUN_COMMIT = "52fa35f"
FAKE = re.compile(r"(^data/inputs/\*$|/any\.xlsx$|/a\.dxf$|/abc\.dxf$|/x\.json$|does_not_exist|/run1$|^data/(golden|runs)$)")
BENCHMARK = re.compile(r"(BENCHMARK|SEAL|CONTRACTOR|KIYAL|HISTORICAL|sealed/|site_benchmark|EXTERNAL_RECONCILIATION|"
                       r"EXTERNAL_VALIDATION|AGGREGATE_CONTRACTOR|freelancer)", re.I)
FIXTURE_MANIFESTS = ["tests/r8_6/FIXTURE_MANIFEST.json", "tests/r8_7/FIXTURE_MANIFEST.json"]
GOLDEN = {"runs/golden/23010_MANIFEST.json": "data/golden/23010/"}
SOURCE_MANIFEST = "tests/alsenan/registers/SOURCE_MANIFEST.json"
# owner decision 2026-10-09: keep the two earlier architectural PDFs, which were rebuilt byte for byte from the uploaded
# 12-sheet set; mark them as reconstructions, with the uploaded set as the independent parent evidence
RECONSTRUCTED = "BYTE_IDENTICAL_RECONSTRUCTION_FROM_VERIFIED_UPLOAD"
SET_KEY = "P7757_ARCH_PDF_SET_01-12"
RECONSTRUCTIONS = {
    "80b6a80428990db4dfa86aa343ed2c7cb429709459d564f0dac92362480a9b00":
        {"parent_part": "ARCH_PART_1_PAGES_01-06", "set_sheets": "01-06",
         "parent_sha256": "cd3b8669d55998cb638bd8e2b572da4992ed64babcecacd73753d6a2f0c68b97"},
    "281a0c3f8c1cdd8f2a78528513b66d14ba4793e981e2d8059423faf6e6162f99":
        {"parent_part": "ARCH_PART_2_PAGES_07-12", "set_sheets": "07-12",
         "parent_sha256": "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"}}
RECON_METHOD = ("the 134 bytes of /Title and /Subject added to the uploaded part were removed and the cross-reference "
                "offsets restored (engine/source/source_identity.py); the result's SHA-256 equals the registered one")


def acquisition(sha):
    """How a registered input on disk was obtained. A reconstruction is never a separately obtained original."""
    r = RECONSTRUCTIONS.get(sha)
    if not r:
        return None
    return {"acquisition": RECONSTRUCTED, "parent_evidence": f"{SET_KEY} {r['parent_part']} (sheets {r['set_sheets']})",
            "parent_sha256": r["parent_sha256"], "method": RECON_METHOD,
            "owner_decision": "2026-10-09: keep in private, git-ignored storage",
            "not": "a separately obtained original"}


def _git_files():
    return subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()


def runtime_missing(xml):
    import xml.etree.ElementTree as ET
    miss, skips = defaultdict(set), defaultdict(int)
    if not xml or not Path(xml).exists():
        return miss, skips
    for tc in ET.parse(xml).getroot().iter("testcase"):
        mod = tc.get("classname", "").split(".")[-1]
        for x in tc:
            msg = (x.get("message") or "") + " " + (x.text or "")
            if x.tag in ("failure", "error"):
                for m in re.finditer(r"No such file or directory: '([^']+)'", msg):
                    miss[m.group(1).replace(str(ROOT) + "/", "")].add(mod)
            elif x.tag == "skipped":
                skips[re.sub(r"\s+", " ", x.get("message") or "")[:200]] += 1
    return miss, skips


def static_paths(files):
    out = defaultdict(set)
    for f in files:
        if f.startswith("tests/") and f.endswith(".py"):
            for m in re.finditer(r"""["'](data/[^"'\s{}]+)["']""", (ROOT / f).read_text(encoding="utf-8", errors="ignore")):
                out[m.group(1)].add(Path(f).stem)
    return out


def pinned_identities():
    pins = {}
    for f in FIXTURE_MANIFESTS:
        p = ROOT / f
        if p.exists():
            for k, v in json.loads(p.read_text(encoding="utf-8")).get("fixtures", {}).items():
                pins[k] = {"sha256": v, "pinned_by": f}
    for f, base in GOLDEN.items():
        p = ROOT / f
        if p.exists():
            for k, v in json.loads(p.read_text(encoding="utf-8")).get("input_sha256", {}).items():
                pins[base + k] = {"sha256": v, "pinned_by": f}
    return pins


def source_inputs():
    d = json.loads((ROOT / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    rows = []
    for o in d.get("files", []):
        if isinstance(o, dict) and o.get("sha256"):
            ext = Path(o["file"]).suffix.lower()
            rows.append({"name": o["file"], "sha256": o["sha256"], "bytes": o.get("bytes"),
                         "path": f"data/inputs/by_sha256/{o['sha256']}{ext}", "role": o.get("declared_role"),
                         "discipline": o.get("discipline")})
    return rows


def producers(files, basenames):
    """Tracked research scripts that name a file (its likely producer or reader), excluding tests."""
    out = defaultdict(list)
    code = [f for f in files if f.endswith(".py") and f.startswith(("research/", "engine/", "tools/"))]
    texts = {f: (ROOT / f).read_text(encoding="utf-8", errors="ignore") for f in code}
    for b in basenames:
        out[b] = sorted(f for f, t in texts.items() if b in t)[:4]
    return out


def category(p):
    if p.startswith("/root/.claude/uploads/"):
        return "SESSION_UPLOAD"
    if BENCHMARK.search(p):
        return "BENCHMARK_TRUTH"
    if p.startswith("data/inputs/") or p.startswith("data/golden/") and "/inputs/" in p:
        return "SOURCE_DRAWING"
    if p.startswith("data/golden/"):
        return "GOLDEN_FIXTURE"
    if p.startswith("data/experiments/"):
        return "DERIVED_EXPERIMENT"
    if p.startswith("data/runs/"):
        return "DERIVED_RUN"
    if p.startswith("data/reports/"):
        return "DELIVERED_PACKAGE"
    return "OTHER"


def route(cat, prod):
    return {"SOURCE_DRAWING": "RESTORE_FROM_PRIVATE_STORE (verify sha256)",
            "BENCHMARK_TRUTH": "RESTORE_FROM_SEALED_STORE (separate key; never into a blind run)",
            "SESSION_UPLOAD": "NOT_A_FIXTURE (a test reads a session upload: should skip, not fail)",
            "GOLDEN_FIXTURE": "RESTORE_FROM_PRIVATE_STORE (verify sha256)",
            "DELIVERED_PACKAGE": "RESTORE_FROM_PRIVATE_STORE"}.get(
        cat, "REGENERATE_FROM_SOURCES" + (f" ({prod[0]})" if prod else " (producer not identified)")
        + " or RESTORE_FROM_PRIVATE_STORE")


def main(xml=None):
    files = _git_files()
    miss, skips = runtime_missing(xml)
    stat = static_paths(files)
    pins = pinned_identities()
    req = defaultdict(lambda: {"needed_by": set(), "evidence": set()})
    for p, mods in miss.items():
        req[p]["needed_by"] |= mods
        req[p]["evidence"].add("RUNTIME_FILE_NOT_FOUND")
    for p, mods in stat.items():
        if not FAKE.search(p) and not (ROOT / p).exists():
            req[p]["needed_by"] |= mods
            req[p]["evidence"].add("STATIC_TEST_REFERENCE")
    for reason in skips:
        for m in re.finditer(r"(data/[\w./-]+[\w])", reason):
            if not (ROOT / m.group(1)).exists():
                req[m.group(1)]["evidence"].add("SKIP_REASON")
    for p in pins:
        if not (ROOT / p).exists():
            req[p]["evidence"].add("PINNED_FIXTURE")
    prod = producers(files, {Path(p).name for p in req})
    entries = []
    for p in sorted(req):
        cat = category(p)
        pr = prod.get(Path(p).name, [])
        named = re.search(r"by_sha256/([0-9a-f]{64})\.", p)
        entries.append({"path": p, "kind": "DIRECTORY" if not Path(p).suffix else "FILE", "category": cat,
                        "present": (ROOT / p).exists() if not p.startswith("/") else Path(p).exists(),
                        "expected_sha256": pins.get(p, {}).get("sha256") or (named.group(1) if named else None),
                        "identity_source": pins.get(p, {}).get("pinned_by") or ("content-addressed name"
                                                                                if "by_sha256/" in p else None),
                        "needed_by": sorted(req[p]["needed_by"]), "evidence": sorted(req[p]["evidence"]),
                        "named_in_tracked_code": pr, "restore_route": route(cat, pr)})
    src = source_inputs()
    for s in src:
        s["present"] = (ROOT / s["path"]).exists()
        if acquisition(s["sha256"]):
            s["acquisition"] = acquisition(s["sha256"])
    by_cat = defaultdict(int)
    for e in entries:
        by_cat[e["category"]] += 1
    manifest = {"schema": "URBAN_ENVIRONMENT_RECOVERY_MANIFEST_V1", "date": DATE,
                "derived_from": {"full_suite_run": f"JUnit XML of the run at {RUN_COMMIT} (6659 passed, 344 failed, "
                                                  "32 errors, 138 skipped)" if xml else None,
                                 "static_scan": "tests/**/*.py data/ path literals",
                                 "identity_records": FIXTURE_MANIFESTS + list(GOLDEN) + [SOURCE_MANIFEST]},
                "rule": "paths, hashes and producers only; no file content, no client drawing, no credential",
                "missing_prerequisites": entries, "missing_by_category": dict(sorted(by_cat.items())),
                "skip_reasons": dict(sorted(skips.items(), key=lambda kv: -kv[1])),
                "registered_source_inputs": src,
                "registered_source_inputs_present": sum(1 for s in src if s["present"]),
                "registered_source_inputs_total": len(src)}
    (HERE / "RECOVERY_MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
                                                 encoding="utf-8")
    lock = {"schema": "URBAN_INPUTS_LOCK_V1 (PROPOSED)", "date": DATE,
            "rule": "metadata and sha256 only. A missing entry SKIPS the tests that need it, with this file's reason; "
                    "a present file whose sha256 differs FAILS. No content, no credential, no client name.",
            "stores": {"SOURCE": "private source store (client drawings, content-addressed)",
                       "DERIVED": "regenerable outputs (experiments, runs); restore or regenerate, then verify",
                       "BENCHMARK": "sealed store, separate key; never mounted for a blind run"},
            "entries": [{"path": s["path"], "sha256": s["sha256"], "bytes": s["bytes"], "store": "SOURCE",
                         "role": s["role"], "discipline": s["discipline"]}
                        | ({"note": f"{RECONSTRUCTED} from {acquisition(s['sha256'])['parent_evidence']} "
                                    f"({acquisition(s['sha256'])['parent_sha256']}); not a separately obtained "
                                    "original"} if acquisition(s["sha256"]) else {}) for s in src]
                       + [{"path": p, "sha256": v["sha256"], "bytes": None,
                           "store": "BENCHMARK" if BENCHMARK.search(p) else
                           ("SOURCE" if "/inputs/" in p else "DERIVED"), "pinned_by": v["pinned_by"]}
                          for p, v in sorted(pins.items())]
                       + [{"path": e["path"], "sha256": None, "bytes": None,
                           "store": {"BENCHMARK_TRUTH": "BENCHMARK", "SOURCE_DRAWING": "SOURCE"}.get(e["category"], "DERIVED"),
                           "note": "identity not recorded in git: record its sha256 on the next restore"}
                          for e in entries if not e["expected_sha256"] and e["category"] != "SESSION_UPLOAD"
                          and "by_sha256/" not in e["path"]]}
    (HERE / "INPUTS.lock.proposed.json").write_text(json.dumps(lock, indent=1, ensure_ascii=False) + "\n",
                                                    encoding="utf-8")
    print(json.dumps({"missing": len(entries), "by_category": manifest["missing_by_category"],
                      "sources_present": f"{manifest['registered_source_inputs_present']}/{len(src)}"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
