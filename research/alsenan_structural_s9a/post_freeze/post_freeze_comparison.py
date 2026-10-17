"""S9A post-freeze comparison: the frozen correction layer against the earlier figures, after the freeze.

    python3 -I research/alsenan_structural_s9a/post_freeze/post_freeze_comparison.py

Reads the frozen S9A package (its manifest, S9's and the 29 stage manifests verify before and after; nothing frozen is
written), then the earlier figures S9A did not read before its freeze:
  * the old Urban V3b BOQ: beam, ground-beam and column lines (BOQ_LINES_V3B) and its residue register
    (STRUCTURE_V3B_REGISTER: blocked beams, exterior ground beams);
  * the PRE-S8 structural element census (02): the HZ-* hatch-zone rows and the CA row.
Every difference is classified and explained. Nothing here selects a beam reading, tunes S9A or releases anything: a
finding that needs a change is recorded for a separately approved release.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402

R = ROOT / "research"
S9 = R / "alsenan_structural_s9"
V3B = ROOT / "tests/alsenan/registers_v3b"
PRE_S8 = R / "pre_s8_structural_completeness"
MANIFEST = PKG / "18_S9A_CORRECTION_MANIFEST.json"
OUT = ["00_POST_FREEZE_README.md", "01_BEAMS_VS_V3B.csv", "02_GROUND_BEAMS_AND_COLUMNS_VS_V3B.csv",
       "03_PRE_S8_BAND_CROSSWALK.csv", "04_POST_FREEZE_FINDINGS.csv", "05_POST_FREEZE_SUMMARY.json"]
RELEASED = ("RELEASED_FROZEN_STAGE", "RELEASED_S9_DELTA")
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
FORBIDDEN = (44.19, 352.436075, 77.6305, 75.09, 39.7515, 65.965875, 59.8174, 21.8328, 12.348, 337.812, 333.173,
             22.619, 22.916)
RULE = ("comparison only, after the freeze: S9A is not tuned, no beam reading is selected, nothing is released and no "
        "frozen quantity changes; a finding that needs a change goes to a separately approved release")


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _f(v):
    return None if v in (None, "", "None") else float(v)


def _r(v, nd=6):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in keys})
    return buf.getvalue()


def _verify():
    """The S9A manifest, S9's, and every stage manifest S9A froze over (found by their recorded sha256)."""
    m = _j(MANIFEST)
    DR.verify_frozen(MANIFEST, ROOT)
    s9m = S9 / "16_S9_FREEZE_MANIFEST.json"
    assert hashlib.sha256(s9m.read_bytes()).hexdigest() == m["s9_manifest_sha256"]
    want = set(m["frozen_baselines"].values())
    found = {}
    for p in sorted(R.glob("*/*.json")):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h in want:
            DR.verify_frozen(p, ROOT)
            found[h] = str(p.relative_to(ROOT))
    assert set(found) == want, sorted(want - set(found))
    return {"manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(), "state": m["state"],
            "frozen_manifests_verified": len(found)}


def _counts(formula):
    m = re.search(r"(\d+) computed, (\d+) blocked", formula or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


# ------------------------------------------------------------------ beams
def beams_vs_v3b(lines):
    b = _rows(PKG / "05_BEAM_CONVENTION_COMPARISON.csv")
    cond = [x for x in b if x["S9A_STATE"].startswith(("CONDITIONAL", "BAND_IS"))]
    out = []
    for st in ("GF", "1F", "2F", "ALL"):
        xs = [x for x in cond if st == "ALL" or x["STOREY"] == st]
        codes = [f"C-BEAM-{s}" for s in (("GF", "1F", "2F") if st == "ALL" else (st,))]
        v = math.fsum(lines[c]["qty"] or 0.0 for c in codes)
        comp = [_counts(lines[c]["formula"]) for c in codes]
        a = math.fsum(float(x["V_TOTAL_DEPTH_M3"]) for x in xs)
        dn = math.fsum(float(x["DOWNSTAND_IF_TOTAL_DEPTH_M3"]) for x in xs)
        bb = math.fsum(float(x["V_BELOW_SLAB_M3"]) for x in xs)
        out.append({
            "STOREY": st, "V3B_LINES": codes, "V3B_METHOD": "clear length x B x (D - t)",
            "V3B_COMPUTED_BEAMS": sum(c[0] or 0 for c in comp), "V3B_BLOCKED_BEAMS": sum(c[1] or 0 for c in comp),
            "V3B_TECHNICAL_M3": _r(v), "S9A_CONDITIONAL_BEAMS": len(xs),
            "S9A_READING_A_DOWNSTAND_M3": _r(dn), "S9A_READING_A_M3": _r(a), "S9A_READING_B_M3": _r(bb),
            "V3B_MINUS_S9A_DOWNSTAND_M3": _r(v - dn), "V3B_MINUS_S9A_READING_A_M3": _r(v - a),
            "CLASS": "METHOD (V3b = reading A, downstand only) + POPULATION",
            "EXPLANATION": ("V3b reads H as the overall depth (S9A reading A) and measures only the downstand "
                            "B x (H - t), leaving the strip B x t to its slab plate; its computed population "
                            f"({sum(c[0] or 0 for c in comp)} beams) differs from S9A's {len(xs)} conditional beams, "
                            "and V3b holds no per-beam register, so the difference is not decomposable beam by beam. "
                            "V3b choosing reading A is not source authority: RFI-A01 stands")})
    return out


# ------------------------------------------------------------------ ground beams and columns
def gb_and_columns_vs_v3b(lines, struct):
    gb = _rows(PKG / "08_GROUND_BEAM_AUDIT.csv")
    s9 = _rows(S9 / "02_CONCRETE_BOQ_RECONCILIATION.csv")
    out = []
    interp = [r for r in gb if r["M3_EXCLUSIVE_TITLES_CC_BASIS"]]
    rel = [r for r in s9 if r["FAMILY"] == "GROUND_BEAMS" and r["LANE"] in RELEASED]
    gi = lines["C-GB-INT"]
    out.append({"ITEM": "GROUND_BEAMS_INTERIOR", "V3B_LINE": "C-GB-INT", "V3B_STATUS": gi["status"],
                "V3B_TECHNICAL_M3": gi["qty"], "V3B_METHOD": gi["formula"],
                "S9_RELEASED_M3": _r(math.fsum(float(r["RELEASED_M3"]) for r in rel)), "S9_RELEASED_SPANS": len(rel),
                "S9A_EXCLUSIVE_TITLES_CC_M3": _r(math.fsum(float(r["M3_EXCLUSIVE_TITLES_CC_BASIS"]) for r in interp)),
                "S9A_EXCLUSIVE_TITLES_CLEAR_M3": _r(math.fsum(float(r["M3_EXCLUSIVE_TITLES_CLEAR_BASIS"])
                                                              for r in interp)),
                "S9A_INTERPRETATION_SPANS_WITH_VALUE": len(interp),
                "CLASS": "AUTHORITY + METHOD",
                "EXPLANATION": ("V3b reads the p.13 titles as exclusive bands (> 5 m 30x60, 2.5 - 5 m 30x40, < 2.5 m "
                                "30x30) on its own length basis and computes every interior span; S9 releases the six "
                                "explicit sections and S9A keeps the title reading and the length basis as RFI-A05. "
                                "V3b adopting a reading is not source authority")})
    ge = lines["C-GB-EXT"]
    ext = struct["ext_gb"]
    ub = [r for r in gb if r["M3_UPPER_BOUND_EXTERIOR"]]
    out.append({"ITEM": "GROUND_BEAMS_EXTERIOR", "V3B_LINE": "C-GB-EXT", "V3B_STATUS": ge["status"],
                "V3B_TECHNICAL_M3": ge["qty"], "V3B_METHOD": ge["formula"], "V3B_SPANS": ext["spans"],
                "V3B_COMMERCIAL_DEPTH_M": ext["D"], "S9A_EXTERIOR_SPANS_WITH_UPPER_BOUND": len(ub),
                "S9A_UPPER_BOUND_M3": _r(math.fsum(float(r["M3_UPPER_BOUND_EXTERIOR"]) for r in ub)),
                "CLASS": "NO_DIFFERENCE (both technically blocked)",
                "EXPLANATION": ("V3b blocks the exterior depth technically and infers D ~ 1.0 m commercially from the "
                                "elevations (+1.00 to +-0.00); S9A holds the same depth only as an upper bound "
                                "(BOUNDED_ABOVE, 1.0 m). Neither releases it: the 'FOLLOW ARCH.' depth is missing")})
    cols = _rows(PKG / "09_COLUMN_AUDIT.csv")
    for st in ("GF", "1F", "2F"):
        c, j = lines[f"C-COL-{st}"], lines[f"C-JNT-{st}"]
        n = _counts(c["formula"])
        r9 = [r for r in s9 if r["FAMILY"] == "COLUMNS" and r["STOREY"] == st and r["LANE"] in RELEASED]
        mm = [r for r in cols if r["FLOOR"] == st]
        out.append({"ITEM": f"COLUMNS_{st}", "V3B_LINE": f"C-COL-{st} + C-JNT-{st}", "V3B_STATUS": c["status"],
                    "V3B_TECHNICAL_M3": _r((c["qty"] or 0.0) + (j["qty"] or 0.0)), "V3B_METHOD":
                    f"{c['formula']}; joints: {j['formula']}", "V3B_COMPUTED": n[0], "V3B_BLOCKED": n[1],
                    "S9_RELEASED_M3": _r(math.fsum(float(r["RELEASED_M3"]) for r in r9)), "S9_RELEASED_COLUMNS": len(r9),
                    "S9A_SECTION_MISMATCHES": len(mm),
                    "S9A_MISMATCH_RANGE_M3": [_r(math.fsum(min(float(r["M3_SCHEDULE"]), float(r["M3_DRAWN"]))
                                                           for r in mm)),
                                              _r(math.fsum(max(float(r["M3_SCHEDULE"]), float(r["M3_DRAWN"]))
                                                           for r in mm))],
                    "CLASS": "METHOD + POPULATION",
                    "EXPLANATION": ("V3b measures the column clear of the beam plus a joint below the slab and computes "
                                    "every bound column on its schedule section; S9 releases only S2-VERIFIED columns "
                                    "whose drawn section equals the schedule, over the printed floor-to-floor; S9A "
                                    "keeps the mismatches as RFI-A04 (drawn vs schedule). Not decomposable per column "
                                    "from V3b")})
    return out


# ------------------------------------------------------------------ PRE-S8 census
def band_crosswalk(struct):
    census = _rows(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv")
    bands = {b["DXF_HANDLE"]: b for b in _rows(PKG / "03_BAND_CORRECTION_REGISTER.csv")}
    hz = [x for x in census if x["ELEMENT_FAMILY"].startswith("CANTILEVER_OR_BEARING_WALL_BAND")]
    out = []
    for x in sorted(hz, key=lambda x: x["ELEMENT_ID"]):
        h = json.loads(x["DXF_HANDLES"])[0]
        b = bands.get(h)
        m = re.match(r"([0-9.]+) m2", x["PHYSICAL_GEOMETRY"])
        area = float(m.group(1)) if m else None
        out.append({"PRE_S8_ID": x["ELEMENT_ID"], "PRE_S8_FLOOR": x["FLOOR"], "DXF_HANDLE": h,
                    "PRE_S8_AREA_M2": area, "S9A_BAND": b["BAND_ID"] if b else None,
                    "S9A_AREA_M2": _f(b["AREA_M2"]) if b else None,
                    "AREA_DIFF_M2": _r(area - float(b["AREA_M2"])) if b and area is not None else None,
                    "PRE_S8_MISSING_INFORMATION": x["MISSING_INFORMATION"],
                    "S9A_LEGEND_MATCH": b["LEGEND_MATCH"] if b else None,
                    "S9A_PDF_SPACING_MM": _f(b["PDF_SPACING_MODEL_MM"]) if b else None,
                    "S9A_OWNER": b["OWNER_DECISION"].split(" (")[0].split(":")[0] if b else None,
                    "CLASS": "SAME_OBJECT" if b and area is not None and abs(area - float(b["AREA_M2"])) <= 0.001
                    else "DIFFERENT"})
    ca = next(x for x in census if x["ELEMENT_FAMILY"].startswith("CANTILEVER_BEAM"))
    v3ca = next(r for r in struct["residue"]["beams"] if r["type"] == "CA")
    cp = next(b for b in bands.values() if b["OWNER_DECISION"].startswith("BEAMS"))
    out.append({"PRE_S8_ID": ca["ELEMENT_ID"], "PRE_S8_FLOOR": ca["FLOOR"], "DXF_HANDLE": cp["DXF_HANDLE"],
                "S9A_BAND": cp["BAND_ID"], "V3B_CA_LENGTH_M": v3ca["length_m"],
                "V3B_CA_LENGTH_BASIS": v3ca["length_basis"], "S9A_BAND_LENGTH_M": _r(float(cp["LENGTH_MM"]) / 1000),
                "S9A_OWNER": "BEAMS (CA)",
                "CLASS": "SAME_OBJECT" if abs(v3ca["length_m"] - float(cp["LENGTH_MM"]) / 1000) < 0.001 else
                "DIFFERENT"})
    return out


def findings(beam, gbc, cross):
    hz = [c for c in cross if c["PRE_S8_ID"].startswith("HZ-")]
    ca = next(c for c in cross if not c["PRE_S8_ID"].startswith("HZ-"))
    same = sum(1 for c in hz if c["CLASS"] == "SAME_OBJECT")
    allb = next(b for b in beam if b["STOREY"] == "ALL")
    gi = next(g for g in gbc if g["ITEM"] == "GROUND_BEAMS_INTERIOR")
    return [
        {"ID": "PF-01", "CLASS": "SAME_OBJECTS",
         "FINDING": f"the PRE-S8 census lists {len(hz)} HZ-* hatch zones; {same} have the handle and area of an S9A "
                    "band (to 0.001 m2): S9A's independent detection found the same objects and no other",
         "ACTION": "none"},
        {"ID": "PF-02", "CLASS": "RESOLVED_BY_MEASUREMENT",
         "FINDING": "the census records 'the legend draws the cantilever portion and the bearing wall with the same "
                    "dense hatch'; on the plotted PDF the two legend boxes measure 98.78 and 86.81 mm, and all 8 bands "
                    "match the cantilever-portion symbol (C05). The census's ambiguity is resolved by measurement; the "
                    "thickness is still not printed",
         "ACTION": "none to S9A; RFI-A08 (thickness) stands; confirm the classification with the engineer"},
        {"ID": "PF-03", "CLASS": "SAME_OBJECT",
         "FINDING": f"V3b's residue row for the cantilever beam CA uses a drawn band extent of {ca['V3B_CA_LENGTH_M']} m; "
                    f"{ca['S9A_BAND']} is {ca['S9A_BAND_LENGTH_M']} m long on the same beam line, so the band is CA's own "
                    "footprint, as S9A bound it (no second object)",
         "ACTION": "none"},
        {"ID": "PF-04", "CLASS": "METHOD + POPULATION",
         "FINDING": f"V3b's computed beams ({allb['V3B_COMPUTED_BEAMS']}) total {allb['V3B_TECHNICAL_M3']} m3 by "
                    "reading A's downstand B x (H - t) x L; S9A's "
                    f"{allb['S9A_CONDITIONAL_BEAMS']} conditional beams give {allb['S9A_READING_A_DOWNSTAND_M3']} m3 "
                    f"downstand, {allb['S9A_READING_A_M3']} m3 under reading A and {allb['S9A_READING_B_M3']} m3 under "
                    "reading B. The populations differ and V3b has no per-beam register",
         "ACTION": "none; V3b's choice of reading A is not authority (RFI-A01 stands)"},
        {"ID": "PF-05", "CLASS": "AUTHORITY + METHOD",
         "FINDING": f"V3b reads the p.13 ground-beam titles as exclusive bands ({gi['V3B_TECHNICAL_M3']} m3 interior); "
                    "S9A shows the same reading as a conditional value only "
                    f"({gi['S9A_EXCLUSIVE_TITLES_CLEAR_M3']} - {gi['S9A_EXCLUSIVE_TITLES_CC_M3']} m3 over "
                    f"{gi['S9A_INTERPRETATION_SPANS_WITH_VALUE']} interior spans) on top of S9's "
                    f"{gi['S9_RELEASED_M3']} m3 released",
         "ACTION": "none; RFI-A05 stands"},
        {"ID": "PF-06", "CLASS": "NO_DIFFERENCE",
         "FINDING": "exterior ground beams: V3b blocks the depth technically and infers about 1.0 m from the elevations; "
                    "S9A holds 1.0 m as an upper bound only. Both treat 'FOLLOW ARCH.' as missing",
         "ACTION": "none"},
        {"ID": "PF-07", "CLASS": "METHOD + POPULATION",
         "FINDING": "columns: V3b measures clear of the beams plus joints on the schedule section for every bound "
                    "column; S9 releases matched, S2-VERIFIED columns over the floor-to-floor; the 28 mismatches stay "
                    "RFI-A04. Not decomposable per column",
         "ACTION": "none"},
    ]


# ------------------------------------------------------------------ write
def _check_text(name, text):
    assert not HYG.search(text), name
    for n in re.findall(r"(?<![0-9.])[0-9]+\.[0-9]+(?![0-9])", text):
        v = float(n)
        assert not any(abs(v - x * k) <= 1e-9 * max(1.0, abs(x * k)) for x in FORBIDDEN for k in (1, 1000)), (name, n)


def _md(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(_cell(r.get(h)) for h in head) + " |" for r in rows]
    return "\n".join(out)


def readme(pre, beam, gbc, cross, fnd):
    hz = [c for c in cross if c["PRE_S8_ID"].startswith("HZ-")]
    return "\n".join([
        "# S9A post-freeze comparison", "",
        f"Read after the S9A freeze (`{pre['state']}`, manifest sha256 `{pre['manifest_sha256'][:16]}...`). S9A, S9 "
        f"and {pre['frozen_manifests_verified']} frozen manifests verify before and after. {RULE[0].upper() + RULE[1:]}.", "",
        "## Findings", "", _md(["ID", "CLASS", "FINDING", "ACTION"], fnd), "",
        "## Beams against the old Urban V3b BOQ", "",
        _md(["STOREY", "V3B_COMPUTED_BEAMS", "V3B_TECHNICAL_M3", "S9A_CONDITIONAL_BEAMS", "S9A_READING_A_DOWNSTAND_M3",
             "S9A_READING_A_M3", "S9A_READING_B_M3", "V3B_MINUS_S9A_DOWNSTAND_M3"], beam), "",
        "V3b's method (clear length x B x (D - t)) is S9A reading A without the slab strip. Agreement or disagreement "
        "with V3b is never used to pick a reading.", "",
        "## Ground beams and columns", "",
        _md(["ITEM", "V3B_STATUS", "V3B_TECHNICAL_M3", "S9_RELEASED_M3", "CLASS"], gbc), "",
        "## PRE-S8 census crosswalk", "",
        f"{sum(1 for c in hz if c['CLASS'] == 'SAME_OBJECT')} of {len(hz)} HZ-* rows are S9A bands (same handle, area "
        "within 0.001 m2). The CA row is bound to its band by V3b's own drawn band extent.", "",
        _md(["PRE_S8_ID", "DXF_HANDLE", "PRE_S8_AREA_M2", "S9A_BAND", "S9A_AREA_M2", "S9A_LEGEND_MATCH", "CLASS"],
            cross), "",
        "Nothing here changes a released quantity. The released baseline stays S9's 158.070 m3 / 18,845.961 kg.", ""])


def main():
    pre = _verify()
    lines = {x["code"]: {"qty": _f(x["qty"]), "status": x["status"], "formula": x["formula"], "line_id": x["line_id"]}
             for x in _j(V3B / "BOQ_LINES_V3B.json")["lines"]}
    struct = _j(V3B / "STRUCTURE_V3B_REGISTER.json")
    beam = beams_vs_v3b(lines)
    gbc = gb_and_columns_vs_v3b(lines, struct)
    cross = band_crosswalk(struct)
    fnd = findings(beam, gbc, cross)
    assert sum(1 for c in cross if c["CLASS"] == "SAME_OBJECT") == 9, cross
    summary = {"round": "S9A post-freeze", "frozen": pre, "rule": RULE,
               "classes": dict(Counter(f["CLASS"] for f in fnd)), "findings": [f["ID"] for f in fnd],
               "hz_rows_same_object": sum(1 for c in cross if c["PRE_S8_ID"].startswith("HZ-") and
                                          c["CLASS"] == "SAME_OBJECT"),
               "release_delta": {"concrete_m3": 0.0, "kg": 0.0}}
    texts = {OUT[0]: readme(pre, beam, gbc, cross, fnd), OUT[1]: _csv(beam), OUT[2]: _csv(gbc), OUT[3]: _csv(cross),
             OUT[4]: _csv(fnd), OUT[5]: json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n"}
    for k, t in texts.items():
        _check_text(k, t)
    for k, t in texts.items():
        (HERE / k).write_text(t, encoding="utf-8")
    post = _verify()
    assert post == pre, "a frozen manifest changed"
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
