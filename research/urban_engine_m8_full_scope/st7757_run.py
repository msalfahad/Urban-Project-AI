"""M8 on ST7757 - the M7 engine state (conventions V5) against the M8 engine (V6) on the same inputs, every M8
convention's own effect, and - after the freeze - the positions of the project-stage records and the external
estimates by family. POST-DISCOVERY: ST7757 was seen while the M8 rules were written (the developer also saw the M5
bridge figures in earlier milestones); this is not blind evidence (the held-out synthetic set is).

    python3 -I research/urban_engine_m8_full_scope/st7757_run.py [--cache DIR] [--no-ablation]

Writes st7757/:
  BY_FAMILY.csv      V5 / V6 per trade, family, storey: measured base, unresolved exposure, item counts
  SCOPE_ITEMS.csv    every M8 item (family, storey, low / base / high, assumptions, basis)
  SCOPE_BOUNDS.csv   every completeness finding: what the scope pass did with it and its range
  ABLATION.csv       per M8 convention: a choice switched to its alternative, a switch removed, a number at its
                     low and at its high - the change in the measured RC base and the bounded RC range
  POSITIONS.csv      per family (M5 family names): the V6 measured base and bounded range, and for each position
                     recorded in M5 (02C_FAMILY_TOTALS.csv: the project-stage reconciliation, the freelance QS and the
                     two MCP runs) the difference of the V6 base from it and whether it lies inside the V6 bounded
                     range. The external figures are read from that record at run time and never written here
  SUMMARY.json       totals, family coverage states, finding states, hashes
The drawings are private inputs (data/inputs/by_sha256/); without them the script stops.
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
from tools import urban_boq_m2 as CLI                     # noqa: E402

DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
INPUTS = {"profile": "research/urban_engine_m4_correctness/profile_st7757_m4.json",
          "evidence": "research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json",
          "evidence_review": "research/urban_engine_m4_correctness/evidence/OCR_INDEPENDENT_READINGS.json"}
V5 = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
V6 = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
M5_FAMILIES = ROOT / "research/urban_engine_m5_concrete_reconciliation/02C_FAMILY_TOTALS.csv"
POSITIONS = (("STAGE_RECONCILIATION", "URBAN_M5_MEASURED_BASE_M3"), ("FREELANCE_QS", "FREELANCER_M3"),
             ("MCP_RUN_1", "UC4N_M3"), ("MCP_RUN_2", "CHRISTIANNP_M3"))
OUT = PKG / "st7757"


def run(conv, cache, overrides=None):
    return CLI.compute([str(DXF)], route="G", arch=[str(ARCH)], cache_dir=cache, completeness=True,
                       conventions=str(conv), overrides=overrides or {},
                       **{k: str(ROOT / v) for k, v in INPUTS.items()})


def _csv(rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    return buf.getvalue()


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


def _rc(R):
    T = (R["generic"].get("scope") or {}).get("totals")
    if T:
        return T["RC"]["measured_base"], T["RC"]["bounded_low"], T["RC"]["bounded_high"]
    rc = [i for i in R["items"] if i["trade"] == "CONCRETE" and i["family"] != "PLAIN_CONCRETE"]
    return sum(i["base"] for i in rc if i["category"] != "UNRESOLVED"), None, None


def ablation(cache, base_rc):
    """each M8 convention alone: a choice to its alternative, a single-option switch removed, a number at low / high."""
    v5 = {c["id"] for c in json.loads((ROOT / V5).read_text(encoding="utf-8"))["conventions"]}
    v6 = json.loads((ROOT / V6).read_text(encoding="utf-8"))
    rows = []
    for c in v6["conventions"]:
        if c["id"] in v5:
            continue
        cases = []
        if c["kind"] == "choice" and len(c["options"]) > 1:
            cases = [(f"{c['id']}={o}", {c["id"]: o}, None) for o in c["options"] if o != c["base"]]
        elif c["kind"] == "choice":
            cases = [(f"without {c['id']}", None, c["id"])]
        else:
            cases = [(f"{c['id']}=low {c['low']:g}", {c["id"]: c["low"]}, None),
                     (f"{c['id']}=high {c['high']:g}", {c["id"]: c["high"]}, None)]
        for name, ov, drop in cases:
            rec = {"CONVENTION": c["id"], "CASE": name}
            try:
                if drop:
                    alt = dict(v6, set=v6["set"] + "_WITHOUT_" + drop,
                               conventions=[x for x in v6["conventions"] if x["id"] != drop])
                    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
                        json.dump(alt, tf)
                    R = run(tf.name, cache)
                    Path(tf.name).unlink()
                else:
                    R = run(ROOT / V6, cache, overrides=ov)
                m, lo, hi = _rc(R)
                rec.update(RC_MEASURED_BASE_DELTA=m - base_rc[0],
                           RC_BOUNDED_LOW_DELTA=None if lo is None else lo - base_rc[1],
                           RC_BOUNDED_HIGH_DELTA=None if hi is None else hi - base_rc[2],
                           FINDINGS_WITHOUT_RANGE=((R["generic"].get("scope") or {}).get("totals") or {}).get(
                               "findings_without_range"), STATE="RAN")
            except Exception as e:                                # noqa: BLE001 - recorded, never hidden
                rec.update(STATE=f"NOT_SEPARABLE: {type(e).__name__}: {str(e)[:120]}")
            rows.append(rec)
    return rows


# the M5 family names and the V6 items / bounds that hold each
FAMILY_MAP = {
    "FOOTINGS": (("FOOTINGS", None),), "STRAPS": (("GROUND_BEAMS", "FOUNDATION"),),
    "NECKS": (("COLUMNS", "FOUNDATION"),), "GROUND_BEAMS": (("GROUND_BEAMS", "GROUND"),),
    "GROUND_SLAB": (("GROUND_SLAB", None),), "COLUMNS": (("COLUMNS", "GF"), ("COLUMNS", "1F"), ("COLUMNS", "2F"),
                                                          ("COLUMNS", "UNKNOWN")),
    "BEAMS": (("BEAMS", None),), "SLABS": (("SLABS", None),), "LINTELS": (("LINTELS", None),),
    "STAIRS": (("STAIRS", None),), "DOMES": (("DOMES", None),), "POOL": (("POOL", None),), "LIFT": (("LIFT", None),),
    "WATER_TANK": (("WATER_TANK", None),), "BOUNDARY_WALL": (("BOUNDARY_WALL", None),),
    "PARAPETS": (("PARAPETS", None),), "BLINDING": (("PLAIN_CONCRETE", None),)}


def _hit(fam, storey, keys):
    return any(fam == f and (s is None or storey == s) for f, s in keys)


def positions(R):
    """per M5 family: V6 measured / bounded, and each recorded position as a difference and an in-range flag. A bound
    whose family is not settled ('could be LIFT or WALLS or WATER_TANK') is credited, high end only, to each candidate
    family (V6_CANDIDATE_HIGH_M3); plain-concrete bounds go to blinding; a last row totals the RC families."""
    from engine.source import scope_quantities as SQ
    items, bounds = R["items"], (R["generic"].get("scope") or {}).get("bounds") or []
    cands = {f["FINDING_ID"]: SQ._candidates(f) for f in (R["generic"].get("scope") or {}).get("findings") or []}
    rows = list(csv.DictReader(M5_FAMILIES.open(encoding="utf-8")))
    out = []
    tot = {"mb": 0.0, "lo": 0.0, "hi": 0.0, "pos": defaultdict(float), "miss": set()}
    for r in rows:
        keys = FAMILY_MAP.get(r["FAMILY"])
        if not keys:
            continue
        its = [i for i in items if i["trade"] == "CONCRETE" and _hit(i["family"], i.get("storey"), keys)]
        mb = sum(i["base"] for i in its if i["category"] != "UNRESOLVED")
        ml = sum(i["low"] for i in its if i["category"] == "PROVISIONAL") + \
            sum(i["base"] for i in its if i["category"] == "VERIFIED")
        mh = sum(i["high"] for i in its if i["category"] == "PROVISIONAL") + \
            sum(i["base"] for i in its if i["category"] == "VERIFIED")
        el = sum(i.get("exposure_low") or 0.0 for i in its if i["category"] == "UNRESOLVED")
        eh = sum(i.get("exposure_high") or 0.0 for i in its if i["category"] == "UNRESOLVED")
        fam = keys[0][0]
        plain = fam == "PLAIN_CONCRETE"
        bs = [b for b in bounds if b["SCOPE_STATE"] == "BOUNDED" and (
            (plain and b["CLASS"] == "PLAIN") or (not plain and b["CLASS"] == "RC" and b["FAMILY"] == fam and
                                                  (keys[0][1] is None or b["STOREY"] in [k[1] for k in keys])))]
        cand = [b for b in bounds if b["SCOPE_STATE"] == "BOUNDED" and b["FAMILY"] == "UNKNOWN" and
                fam in cands.get(b["FINDING_ID"], [])]
        lo, hi = ml + el + sum(b["LOW_M3"] for b in bs), mh + eh + sum(b["HIGH_M3"] for b in bs)
        ch = sum(b["HIGH_M3"] for b in cand)
        rec = {"FAMILY": r["FAMILY"], "TITLE": r["TITLE"], "V6_MEASURED_BASE_M3": round(mb, 3),
               "V6_BOUNDED_LOW_M3": round(lo, 3), "V6_BOUNDED_HIGH_M3": round(hi, 3),
               "V6_CANDIDATE_HIGH_M3": round(ch, 3), "N_V6_ITEMS": len(its)}
        if not plain:
            tot["mb"] += mb
            tot["lo"] += lo
            tot["hi"] += hi
        for tag, col in POSITIONS:
            v = r.get(col)
            try:
                x = float(v)
            except (TypeError, ValueError):
                rec[f"{tag}_V6_DIFF_PCT"], rec[f"{tag}_IN_V6_RANGE"] = "NOT_IN_SOURCE", ""
                if not plain:
                    tot["miss"].add(tag)
                continue
            if not plain:
                tot["pos"][tag] += x
            rec[f"{tag}_V6_DIFF_PCT"] = "POSITION_ZERO" if not x else round(100.0 * (mb - x) / x, 1)
            rec[f"{tag}_IN_V6_RANGE"] = "YES" if lo - 1e-6 <= x <= hi + ch + 1e-6 else "NO"
        out.append(rec)
    rec = {"FAMILY": "TOTAL_RC", "TITLE": "Reinforced concrete, the families above (positions: their own families "
                                          "only; NOT_IN_SOURCE families count as 0)",
           "V6_MEASURED_BASE_M3": round(tot["mb"], 3), "V6_BOUNDED_LOW_M3": round(tot["lo"], 3),
           "V6_BOUNDED_HIGH_M3": round(tot["hi"], 3), "V6_CANDIDATE_HIGH_M3": "", "N_V6_ITEMS": ""}
    for tag, _ in POSITIONS:
        x = tot["pos"][tag]
        rec[f"{tag}_V6_DIFF_PCT"] = round(100.0 * (tot["mb"] - x) / x, 1) if x else "POSITION_ZERO"
        rec[f"{tag}_IN_V6_RANGE"] = "YES" if tot["lo"] - 1e-6 <= x <= tot["hi"] + 1e-6 else "NO"
    out.append(rec)
    return out


def compute(cache=None, ablate=True):
    for rel in INPUTS.values():
        bp.assert_blind(json.loads((ROOT / rel).read_text(encoding="utf-8")))
    R5, R6 = run(ROOT / V5, cache), run(ROOT / V6, cache)
    f5, f6 = by_family(R5["items"]), by_family(R6["items"])
    rows = []
    for k in sorted(set(f5) | set(f6)):
        a, b = f5.get(k, by_family([])[k]), f6.get(k, by_family([])[k])
        rows.append({"TRADE": k[0], "FAMILY": k[1], "STOREY": k[2], "UNIT": "m3" if k[0] == "CONCRETE" else "kg",
                     "V5_MEASURED": a["measured"], "V6_MEASURED": b["measured"],
                     "DELTA_MEASURED": b["measured"] - a["measured"],
                     "V5_UNRESOLVED_HIGH": a["unresolved_high"], "V6_UNRESOLVED_HIGH": b["unresolved_high"],
                     "V5_N_MEASURED": a["n_measured"], "V6_N_MEASURED": b["n_measured"],
                     "V5_N_UNRESOLVED": a["n_unresolved"], "V6_N_UNRESOLVED": b["n_unresolved"]})
    sc = R6["generic"]["scope"]
    sitems = [{"ITEM_ID": i["item_id"], "FAMILY": i["family"], "STOREY": i["storey"], "LOW_M3": i["low"],
               "BASE_M3": i["base"], "HIGH_M3": i["high"], "SUPPORT": i["support"],
               "ASSUMPTIONS": ";".join(i["assumptions"]), "FORMULA": i["formula"],
               "DIMENSIONS": json.dumps(i["dimensions"], sort_keys=True, default=str)[:400]}
              for i in R6["items"] if i["trade"] == "CONCRETE" and (i["component_id"].startswith("SCOPE:") or
                                                                    i["family"] == "STAIRS")]
    base_rc = _rc(R6)
    abl = ablation(cache, base_rc) if ablate else []
    pos = positions(R6)
    cov5 = {c["FAMILY"]: c["STATE"] for c in R5["generic"]["family_coverage"]}
    cov6 = {c["FAMILY"]: c["STATE"] for c in R6["generic"]["family_coverage"]}
    summary = {"phase": "POST_DISCOVERY", "conventions": {"before": V5, "after": V6},
               "drawings_sha256": [DXF.name.split(".")[0], ARCH.name.split(".")[0]],
               "rc_v5_measured_base": round(_rc(R5)[0], 3),
               "rc_v6": {"measured_base": base_rc[0], "bounded_low": base_rc[1], "bounded_high": base_rc[2]},
               "scope_totals": sc["totals"], "family_coverage": {"V5": cov5, "V6": cov6},
               "findings": {"V5": len(R5["generic"]["completeness"]["findings"]),
                            "V6": len(R6["generic"]["completeness"]["findings"])},
               "top_storey": sc["top_storey"], "referenced_families": sc["referenced"],
               "positions_source": str(M5_FAMILIES.relative_to(ROOT)),
               "rule": "post-discovery, not blind; external positions read at run time from the M5 record after the "
                       "M8 freeze and written only as differences and in-range flags"}
    files = {"BY_FAMILY.csv": _csv(rows, list(rows[0])),
             "SCOPE_ITEMS.csv": _csv(sitems, ["ITEM_ID", "FAMILY", "STOREY", "LOW_M3", "BASE_M3", "HIGH_M3",
                                               "SUPPORT", "ASSUMPTIONS", "FORMULA", "DIMENSIONS"]),
             "SCOPE_BOUNDS.csv": _csv(sc["bounds"], ["FINDING_ID", "KIND", "FAMILY", "SHEET", "STOREY", "SCOPE_STATE",
                                                     "CLASS", "LOW_M3", "HIGH_M3", "RULE", "BASIS", "ITEMS"]),
             "ABLATION.csv": _csv(abl, ["CONVENTION", "CASE", "STATE", "RC_MEASURED_BASE_DELTA",
                                        "RC_BOUNDED_LOW_DELTA", "RC_BOUNDED_HIGH_DELTA", "FINDINGS_WITHOUT_RANGE"]),
             "POSITIONS.csv": _csv(pos, list(pos[0]))}
    summary["files_sha256"] = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in sorted(files.items())}
    files["SUMMARY.json"] = json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n"
    return files


def main(argv):
    if not DXF.exists():
        raise SystemExit("ST7757 drawings are not in data/inputs/by_sha256/ (private inputs)")
    cache = argv[argv.index("--cache") + 1] if "--cache" in argv else None
    files = compute(cache, ablate="--no-ablation" not in argv)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8")
    s = json.loads(files["SUMMARY.json"])
    print(json.dumps({k: s[k] for k in ("rc_v5_measured_base", "rc_v6", "findings")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
