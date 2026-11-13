"""T-672 (lane I, MASONRY GATE B ROUND 1): the URBAN_V3068_INPUTS_V1 document of ARCH_TAKEOFF_V3.0.68, built ONLY from
the Checker-merged research ledgers (each pinned by sha256) and the merged V3.0.59 producer inputs:

  T-670 (MERGED 91a74d45, Verifier 2026-11-10T09:00Z GATE A PASS): R-T670-1 restatement of the B9 material lines on
        COMPANY_RULEBOOK 1.1.0 (UPC-BLACK-BLOCK-001 0.15 = 40 x 20, owner Q-80 2026-11-07); its per-line 'after' is the
        expected figure the V3.0.68 producer re-run must give (asserted in the module);
  T-372 (research part, MERGED dc1ac41e, Verifier 2026-11-10T11:04Z GATE A PASS): R-T372-1 perimeter joint mortar per
        black mortar line (20 lines: 8 valued, 12 HELD with the host's cause);
  T-675 (MERGED e0984b13, Verifier 2026-11-10T14:08Z GATE A PASS): R-T675-1 (MAIN_S / ANNEX_S block colour BLACK by ST
        p.1 note 2: their AAC glue / white lines NOT_APPLICABLE_WITH_EVIDENCE), R-T675-2 (lintel bearing bed, 6 dp high
        at a masonry-end stopper), R-T675-3 (23 held junction bands: 21 HELD bounded, 2 not applicable; 6 held piece
        soffits), and the 0.20 m perimeter evidence label (F-T372-1).

Nothing is typed here: every figure is read from a merged ledger file. No drawing, workbook, client name or coordinate.

    .work/venv/bin/python -I research/agents_t672/t672_inputs.py      (prints the document's summary)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t498", ROOT / "research" / "agents_t670"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

SCHEMA = "URBAN_V3068_INPUTS_V1"
T670 = ROOT / "research/agents_t670/out/T670_MATERIALS.json"
T372 = ROOT / "research/agents_t372/out/T372_PERIMETER_LEDGER.json"
T675 = ROOT / "research/agents_t675/out/T675_MASONRY_ROUND2.json"
RB_OLD = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"
RB_NEW = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
IDX67 = ROOT / "research/agents_t682/out/LINE_INDEX_V3_0_67.json"   # T-682 run of record a29a11a9 (Gate B PASS)
PINS = {  # sha256 of the merged ledgers as merged (a later edit of any of them stops the build)
    T670: "4c58a226a7d3f17f56a4ffaa72229f08bbf4982ef8e52179ce9270c3ae3eb467",
    T372: "a324087fd478ea76645056cd4c6215efbed55f03357271b5341a013c7b1767fb",
    T675: "66e63dfc86037b11a7f94aac0df89a30d65e3db8abc3335c64ed745ec7ba3706",
    IDX67: None,                      # checked by its inputs.lines digest below (the V3.0.67 run of record)
}
SOURCES = [
    {"task": "T-670", "file": "research/agents_t670/out/T670_MATERIALS.json", "merge_commit": "91a74d45",
     "checker_run": "Verifier 2026-11-10T09:00Z GATE A PASS (own DXF GF-W19 / GF-W29 hosts AGREE)"},
    {"task": "T-372", "file": "research/agents_t372/out/T372_PERIMETER_LEDGER.json", "merge_commit": "dc1ac41e",
     "checker_run": "Verifier 2026-11-10T11:04Z GATE A PASS (own DXF 1F-W18 perimeter, D-1F-04 bed AGREE)"},
    {"task": "T-675", "file": "research/agents_t675/out/T675_MASONRY_ROUND2.json", "merge_commit": "e0984b13",
     "checker_run": "Verifier 2026-11-10T14:08Z GATE A PASS (ST p.1 note 2 BLACK own read, MAIN_S 16.27 m AGREE)"},
]
OA = "ASSUMED - OWNER-APPROVED"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rulebook_doc(path):
    import t670_masonry_materials as T  # merged T-670: the rulebook file -> producer inputs shape (no value typed)
    return T.rulebook_doc(path)


def build(project_id=None):
    import t498_inputs as I498          # merged T-498 r3: faces, joint, sources of the V3.0.59 producer
    for p, want in PINS.items():
        if want is not None and _sha(p) != want:
            raise SystemExit(f"{p.name}: sha256 {_sha(p)[:8]} is not the merged ledger {want[:8]}")
    srcs = [dict(s, sha256=_sha(ROOT / s["file"])) for s in SOURCES]
    t670, t372, t675 = _load(T670), _load(T372), _load(T675)
    for d, cand in ((t670, "candidate"), (t372, "candidate"), (t675, "candidate")):
        if d[cand] != "ARCH_TAKEOFF_V3.0.63":
            raise SystemExit(f"a source ledger is not on V3.0.63: {d[cand]}")
    base = I498.build()
    producer = {"faces": base["faces"], "joint": base["joint"], "sources": base["sources"],
                "faces_on_held_hosts": base.get("faces_on_held_hosts") or [],
                "rulebook_before": base["rulebook"], "rulebook_after": rulebook_doc(RB_NEW)}
    if producer["rulebook_before"]["version"] != "1.0.0" or producer["rulebook_after"]["version"] != "1.1.0":
        raise SystemExit("rulebook versions are not 1.0.0 -> 1.1.0")
    restate = [{"line_id": r["material_line_id"], "item_code": r["code"], "host_line_id": r["host_line_id"],
                "host": r["host"], "before": r["before"], "after": r["after"], "changed": r["changed"],
                "cause": r["cause"]} for r in t670["rows"]]
    na = [{"line_id": r["material_line_id"], "item_code": r["code"], "host": r["host"],
           "host_line_id": r["host_line_id"], "evidence": r["evidence"], "arch_check": r["arch_check"],
           "rule": "R-T675-1"} for r in t675["part_a"] if r["after"] == "NOT_APPLICABLE_WITH_EVIDENCE"]
    hosts675 = {h["mortar_line_id"]: h for h in t675["part_b"]["hosts"]}
    pc = {r["host_line_id"]: r for r in t675["part_c"]}
    bands = {}
    for b in t675["part_b"]["bands"]:
        bands.setdefault(b["mortar_line_id"], []).append(
            {k: b.get(k) for k in ("wall_id", "end_ids", "ends", "band_m", "low", "high", "verdict", "cause_class",
                                   "cause")})
    perim = []
    for r in t372["lines"]:
        h = hosts675.get(r["mortar_line_id"])
        e = {"mortar_line_id": r["mortar_line_id"], "host_line_id": r["host_line_id"], "host": r["host"],
             "host_class": r["host_class"], "state": r["perimeter_state"],
             "t372": {"low": r["perimeter_low_m3"], "high": r["perimeter_high_m3"],
                      "figure": r["perimeter_figure_m3"], "walls": r.get("walls"),
                      "held_cause": r.get("held_cause")},
             "bands": bands.get(r["mortar_line_id"], []), "beside_held": r.get("beside_held") or []}
        if h is not None:
            e["t675"] = {k: h[k] for k in ("low", "high_drawn_t372", "held_bands", "held_bands_high", "held_pieces",
                                           "held_pieces_high", "envelope", "walls")}
        if r["host_line_id"] in pc:
            e["evidence_label"] = {"status": OA, "basis": pc[r["host_line_id"]]["basis"], "finding": "F-T372-1"}
        perim.append(e)
    idx = _load(IDX67)
    if idx["candidate_version"] != "ARCH_TAKEOFF_V3.0.67" or not idx["inputs"]["lines"].startswith("a29a11a9"):
        raise SystemExit("the V3.0.67 line index is not the T-682 run of record a29a11a9")
    lint67 = {r["element_id"][7:]: r["line_id"] for r in idx["lines"] if r["item_code"] == "STR.CONC.LINTEL"}
    bed = []
    for x in t675["part_b"]["lintel_bed"]:
        e = {k: x.get(k) for k in ("opening_id", "lintel_line_id", "mortar_line_id", "state", "low", "high",
                                   "bearing_m", "ends", "was", "cause")}
        if e["lintel_line_id"] is None:      # T-675 names the held lintel by opening only: bind it on V3.0.67
            e["lintel_line_id"] = lint67[e["opening_id"]]
            e["lintel_bound_from"] = "research/agents_t682/out/LINE_INDEX_V3_0_67.json (by opening id)"
        elif lint67.get(e["opening_id"]) != e["lintel_line_id"]:
            raise SystemExit(f"{e['opening_id']}: T-675 lintel line is not the V3.0.67 line")
        bed.append(e)
    return {"schema": SCHEMA, "project_id": project_id, "sources": srcs, "producer": producer,
            "restate": restate, "not_applicable": na, "perimeter": perim, "lintel_bed": bed,
            "pieces": t675["part_b"]["pieces"], "factor_m3_per_m": t372["factor_m3_per_m"],
            "beside": {"gf_w22": t675["totals"]["gf_w22_beside"], "t372_totals": t372["totals"],
                       "t675_totals": t675["totals"]},
            "expect_totals_t670": {"before": t670["totals_before"], "after": t670["totals_after"]}}


if __name__ == "__main__":
    d = build()
    print(json.dumps({"sources": [(s["task"], s["sha256"][:8]) for s in d["sources"]],
                      "restate": len(d["restate"]), "changed": sum(r["changed"] for r in d["restate"]),
                      "not_applicable": len(d["not_applicable"]), "perimeter": len(d["perimeter"]),
                      "lintel_bed": len(d["lintel_bed"]), "pieces": len(d["pieces"])}, indent=1))
