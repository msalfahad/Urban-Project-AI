"""T-293 extract (read-only): from a finished ARCH_TAKEOFF_V3.0.16 run on the development villa's Drive copies and the
structural DXF, write the two committed inputs of the face-to-line ledger (engine ids, item codes, states, quantities and
entity handles only; no coordinates of the client drawing, no names):

  CANDIDATE_V3016_CONCRETE_LINES.json  every candidate line whose item code is STR.CONC.* (the members formwork faces
                                       bound), plus the census of formwork-trade lines (expected: none)
  OBLIQUE_BAND_PAIRING_T293.json       the engine ground-beam bands T-289's X / Y pairing could not read (oblique bands)
                                       -> the T-242 run whose face lines they lie on (centroid distance reported)

    python3 -I research/agents_t293/t293_extract.py <run>/v3016 <ST7757 dxf.dxf> --out research/agents_t293
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t289"))
import t289_extract as X  # noqa: E402


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def slim(l):
    s = X._slim(l)
    s["state_detail"] = {k: l.get(k) for k in ("release_status", "verification_status", "blocked_reason")
                         if l.get(k) not in (None, "")}
    return s


def oblique(run, dxf):
    G = json.loads((ROOT / "research/agents_t242/ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8"))
    P = json.loads((ROOT / "research/agents_t289/BAND_PAIRING_T289.json").read_text(encoding="utf-8"))
    paired = {h["run"] for v in P["bands"].values() for h in v["runs"]}
    lonely = [b for b, v in P["bands"].items() if not v["runs"]]
    spans = [s for s in G["spans"] if s["span_id"] not in paired]
    H = X.handles(dxf, spans)
    svg = sorted(Path(run).rglob("SH08_GROUND_BEAM_PLAN_GROUND.svg"))[0]
    if _sha(svg) != P["overlay_sha256"]:
        raise SystemExit("overlay differs from the one T-289 registered")
    bands = X._bands_svg(svg.read_text(encoding="utf-8"))
    k, x0, y1 = P["registration"]["k_px_per_mm"], P["registration"]["x0_mm"], P["registration"]["y1_mm"]
    mids = {}
    for s in spans:
        ls = [H[h] for h in s["handles"] if isinstance(H.get(h), list)]
        mids[s["span_id"]] = (sum((l[0][0] + l[1][0]) / 2 for l in ls) / len(ls),
                              sum((l[0][1] + l[1][1]) / 2 for l in ls) / len(ls))
    out = {}
    for b in lonely:
        Q = [(x0 + a / k, y1 - c / k) for a, c in bands[b]]
        cx, cy = sum(p[0] for p in Q) / len(Q), sum(p[1] for p in Q) / len(Q)
        d = sorted((math.hypot(cx - m[0], cy - m[1]), r) for r, m in mids.items())
        out[b] = {"run": d[0][1], "centroid_distance_mm": round(d[0][0], 1),
                  "next_run": d[1][1] if len(d) > 1 else None,
                  "next_distance_mm": round(d[1][0], 1) if len(d) > 1 else None}
    runs = [v["run"] for v in out.values()]
    if len(set(runs)) != len(runs):
        raise SystemExit(f"two oblique bands on one run: {out}")
    return {"schema": "T293_OBLIQUE_BAND_PAIRING", "structural_sha256": _sha(dxf), "overlay_sha256": _sha(svg),
            "registration": P["registration"], "rule": "nearest run by the band centroid vs the mean midpoint of the "
            "run's face lines; refused if two bands take one run", "bands": out,
            "unpaired_runs_before": sorted(s["span_id"] for s in spans)}


FOOTING_HANDLES = ("166B", "1B2A", "1B07", "1B19", "1B24", "180C")   # the footings r4 names by handle (covers, notch)
FRAME = (75968, 14448)        # the candidate's column / footing frame vs the DXF (T-289 column_offset, 29 votes)


def footing_handles(conc, dxf):
    """handle -> the candidate footing line whose element id position is the outline's (or schedule tag's) lower-left
    corner moved by the one frame translation; refused unless exactly one line is within 2 mm"""
    import re
    import ezdxf
    from ezdxf import bbox
    doc = ezdxf.readfile(str(dxf))
    pos = {}
    for l in conc:
        m = re.match(r"^P-C:FTG:SH\d+:(\w+)@(-?\d+),(-?\d+):", l["element_id"] or "")
        if m and l["item_code"] == "STR.CONC.FOOTING":
            pos[l["line_id"]] = (m.group(1), int(m.group(2)), int(m.group(3)), l["element_id"])
    out = {}
    for h in FOOTING_HANDLES:
        b = bbox.extents([doc.entitydb.get(h)])
        x, y = b.extmin.x + FRAME[0], b.extmin.y + FRAME[1]
        hits = [(lid, v) for lid, v in pos.items() if abs(v[1] - x) <= 2 and abs(v[2] - y) <= 2]
        if len(hits) != 1:
            raise SystemExit(f"footing handle {h}: {len(hits)} candidate lines")
        out[h] = {"line_id": hits[0][0], "mark": hits[0][1][0], "element_id": hits[0][1][3]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="the V3.0.16 output directory (holding V3_0_16_BOQ_LINES.json)")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    run = Path(a.run)
    L = X._lines(run / "V3_0_16_BOQ_LINES.json")
    conc = [l for l in L if (l.get("item_code") or "").startswith("STR.CONC.")]
    fw = [l for l in L if "FORMWORK" in ((l.get("trade") or "") + (l.get("item_code") or "")).upper()]
    csvp = run / "V3_0_16_BOQ_LINES.csv"
    cand = {"schema": "T293_CANDIDATE_V3016_CONCRETE_LINES", "candidate": "ARCH_TAKEOFF_V3.0.16",
            "candidate_lines_csv_sha256": _sha(csvp) if csvp.exists() else None,
            "candidate_lines_json_sha256": _sha(run / "V3_0_16_BOQ_LINES.json"),
            "project": L[0]["project"], "lines_in_candidate": len(L),
            "formwork_lines_in_candidate": [slim(l) for l in fw],
            "lines": [slim(l) for l in sorted(conc, key=lambda x: x["line_id"])],
            "footing_handles": footing_handles([slim(l) for l in conc], a.structural), "frame_offset_mm": list(FRAME)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "CANDIDATE_V3016_CONCRETE_LINES.json").write_text(json.dumps(cand, indent=1, ensure_ascii=False) + "\n",
                                                             encoding="utf-8")
    ob = oblique(run, a.structural)
    (out / "OBLIQUE_BAND_PAIRING_T293.json").write_text(json.dumps(ob, indent=1) + "\n", encoding="utf-8")
    print("lines", len(L), "concrete", len(conc), "formwork", len(fw))
    print(json.dumps(ob["bands"], indent=1))
    return 0


if __name__ == "__main__":
    main()
