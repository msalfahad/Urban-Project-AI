"""M7 on ST7757 - the M6 engine state (conventions V4) against the M7 engine (conventions V5) on the same inputs, and
each V5 convention's own effect (V5 with that one convention removed). POST-DISCOVERY: the V5 rules were written
from the metamorphic harness and synthetic villas, and some from ST7757 runs under transformation; this is not blind
evidence (the held-out synthetic set is). No external record (freelancer BOQ, MCP report) is read here.

    python3 -I research/urban_engine_m7_reliability/st7757_run.py [--cache DIR] [--no-ablation]

Writes st7757/: BY_FAMILY.csv (V4 / V5 per trade, family, storey: measured base, unresolved exposure, item counts),
ABLATION.csv (per V5 convention: the change it alone makes), RELEASE_TOTALS.json (V5 release register totals,
independent checks), SUMMARY.json (completeness findings, options, hashes). The drawings are private inputs
(data/inputs/by_sha256/); without them the script stops.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import benchmark_protection as bp            # noqa: E402
from engine.source import quantity_release as QR          # noqa: E402
from tools import m7_independent as IC                    # noqa: E402
from tools import urban_boq_m2 as CLI                     # noqa: E402

DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
INPUTS = {"profile": "research/urban_engine_m4_correctness/profile_st7757_m4.json",
          "evidence": "research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json",
          "evidence_review": "research/urban_engine_m4_correctness/evidence/OCR_INDEPENDENT_READINGS.json"}
V4 = "engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json"
V5 = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
OUT = PKG / "st7757"


def run(conv, cache):
    return CLI.compute([str(DXF)], route="G", arch=[str(ARCH)], cache_dir=cache, completeness=True,
                       conventions=str(conv), **{k: str(ROOT / v) for k, v in INPUTS.items()})


def by_family(items):
    q = defaultdict(lambda: {"measured": 0.0, "n_measured": 0, "unresolved_low": 0.0, "unresolved_high": 0.0,
                             "n_unresolved": 0})
    for i in items:
        r = q[(i["trade"], i["family"], i.get("storey") or "")]
        if i["category"] in ("PROVISIONAL", "VERIFIED"):
            r["measured"] += i.get("base") or 0.0
            r["n_measured"] += 1
        elif i["category"] == "UNRESOLVED":
            r["unresolved_low"] += i.get("exposure_low") or 0.0
            r["unresolved_high"] += i.get("exposure_high") or 0.0
            r["n_unresolved"] += 1
    return q


def _csv(rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    return buf.getvalue()


def main(argv):
    if not (DXF.exists() and ARCH.exists()):
        print("ST7757 drawings are not present (private inputs): nothing run")
        return 2
    cache = argv[argv.index("--cache") + 1] if "--cache" in argv else None
    for rel in INPUTS.values():
        bp.assert_blind(json.loads((ROOT / rel).read_text(encoding="utf-8")))
    R4, R5 = run(ROOT / V4, cache), run(ROOT / V5, cache)
    f4, f5 = by_family(R4["items"]), by_family(R5["items"])
    rows = []
    for k in sorted(set(f4) | set(f5)):
        a, b = f4.get(k, by_family([])[k]), f5.get(k, by_family([])[k])
        rows.append({"TRADE": k[0], "FAMILY": k[1], "STOREY": k[2], "UNIT": "m3" if k[0] == "CONCRETE" else "kg",
                     "V4_MEASURED": a["measured"], "V5_MEASURED": b["measured"],
                     "DELTA_MEASURED": b["measured"] - a["measured"],
                     "V4_UNRESOLVED_HIGH": a["unresolved_high"], "V5_UNRESOLVED_HIGH": b["unresolved_high"],
                     "DELTA_UNRESOLVED_HIGH": b["unresolved_high"] - a["unresolved_high"],
                     "V4_N_MEASURED": a["n_measured"], "V5_N_MEASURED": b["n_measured"],
                     "V4_N_UNRESOLVED": a["n_unresolved"], "V5_N_UNRESOLVED": b["n_unresolved"]})
    v4ids = {c["id"] for c in json.loads((ROOT / V4).read_text(encoding="utf-8"))["conventions"]}
    v5doc = json.loads((ROOT / V5).read_text(encoding="utf-8"))
    new = [c["id"] for c in v5doc["conventions"] if c["id"] not in v4ids]
    abl = []
    if "--no-ablation" not in argv:
        for cid in new:
            alt = dict(v5doc, set=v5doc["set"] + "_WITHOUT_" + cid,
                       conventions=[c for c in v5doc["conventions"] if c["id"] != cid])
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
                json.dump(alt, tf)
            fa = by_family(run(tf.name, cache)["items"])
            Path(tf.name).unlink()
            for k in sorted(set(fa) | set(f5)):
                a, b = fa.get(k), f5.get(k)
                dm = (b["measured"] if b else 0.0) - (a["measured"] if a else 0.0)
                du = (b["unresolved_high"] if b else 0.0) - (a["unresolved_high"] if a else 0.0)
                if abs(dm) > 1e-6 or abs(du) > 1e-6:
                    abl.append({"CONVENTION": cid, "TRADE": k[0], "FAMILY": k[1], "STOREY": k[2],
                                "DELTA_MEASURED_DUE_TO_IT": dm, "DELTA_UNRESOLVED_HIGH_DUE_TO_IT": du})
            if not any(r["CONVENTION"] == cid for r in abl):
                abl.append({"CONVENTION": cid, "TRADE": "", "FAMILY": "(no quantity change on ST7757)", "STOREY": "",
                            "DELTA_MEASURED_DUE_TO_IT": 0.0, "DELTA_UNRESOLVED_HIGH_DUE_TO_IT": 0.0})
    checks = IC.item_checks(R5["generic"]["D"], R5["items"])
    sources = {DXF.name: hashlib.sha256(DXF.read_bytes()).hexdigest()}
    reg = QR.register(R5["items"], sources=sources, checks=checks)
    c4, c5 = R4["generic"]["completeness"], R5["generic"]["completeness"]
    sev = lambda CR: {s: sum(1 for f in CR["findings"] if f["SEVERITY"] == s) for s in ("HIGH", "MEDIUM", "LOW")}  # noqa
    summary = {"phase": "POST_DISCOVERY", "drawings_sha256": [DXF.name.split(".")[0], ARCH.name.split(".")[0]],
               "inputs": INPUTS, "conventions": {"before": V4, "after": V5}, "v5_new_conventions": new,
               "detect_options_v5": R5["generic"]["D"].get("options"),
               "local_origin_v5": (R5["generic"].get("intake") or {}).get("local_origin"),
               "items": {"V4": len(R4["items"]), "V5": len(R5["items"])},
               "completeness_findings": {"V4": len(c4["findings"]), "V5": len(c5["findings"]),
                                         "V4_by_severity": sev(c4), "V5_by_severity": sev(c5)},
               "independent_checks_v5": IC.summary(checks),
               "rule": "post-discovery: not blind evidence; no external record read"}
    files = {"BY_FAMILY.csv": _csv(rows, list(rows[0])),
             "ABLATION.csv": _csv(abl, ["CONVENTION", "TRADE", "FAMILY", "STOREY", "DELTA_MEASURED_DUE_TO_IT",
                                        "DELTA_UNRESOLVED_HIGH_DUE_TO_IT"]),
             "RELEASE_TOTALS.json": json.dumps({"totals": reg["totals"], "independent_checks": IC.summary(checks),
                                                "rows_by_state": {s: sum(1 for r in reg["rows"] if r["STATE"] == s)
                                                                  for s in QR.STATES}}, indent=1,
                                               sort_keys=True) + "\n",
             "RELEASE_REGISTER.csv": _csv(reg["rows"], list(reg["rows"][0])),
             "SUMMARY.json": json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n"}
    for name, text in files.items():
        bp.assert_blind({"file": name, "text_sha256": hashlib.sha256(text.encode()).hexdigest()})
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8")
    (OUT / "RUN_RECORD.json").write_text(json.dumps(
        {"files_sha256": {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in sorted(files.items())},
         "phase": "POST_DISCOVERY"}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "ablation_rows": len(abl), "items": summary["items"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
