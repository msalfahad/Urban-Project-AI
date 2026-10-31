"""T-328: the URBAN_V3031_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.31 (engine.source.arch_v3031), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build); nothing is typed but the named causes:

  research/agents_t339/FILL_T328_T339.csv  T-339 (MERGED 04f371ba, Verifier 2026-10-29 17:01 UTC Gate A PASS: own
      re-measure of TERRACE-550 zone / parapet footprint / finish hatches, closure -0.0003 m2): one row per roof x layer
      for this package (ADD rows: screed m3, insulation, protection, finish; UNCHANGED rows: the existing membrane /
      upturn lines by id);
  research/agents_t339/BINDING_T339.csv  the same task: per roof x layer the edge and its entity handles, the V3.0.22
      line id of the existing membrane / upturn lines and their state / quantity as bound;
  research/agents_t321/summary.json  T-321 (MERGED 59c82a05, Verifier 2026-10-29 01:02 UTC Gate A PASS: own reads of the
      ROOF-430 strip to divider CEC and the ROOF-970 inner face 1278): per roof the face plan inside the wall / parapet
      faces (the roof outline), the D-band widths and the falls model above the t0 plane (beside only).

    python3 -I research/agents_t328/t328_inputs.py [project_id]      # prints the rows and the totals
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILL = ROOT / "research/agents_t339/FILL_T328_T339.csv"
BIND = ROOT / "research/agents_t339/BINDING_T339.csv"
T321 = ROOT / "research/agents_t321/summary.json"
PINS = {FILL: "d9ffdd9c9e36a52b853eca0bf914b6d03169b6cec0e034c056e10fdd195a24f7",
        BIND: "6e44b0fac5b0fa7f4938e928bb2d366998df03657c4bd3803669f8539002467b",
        T321: "5bad4277dd95971fcd4d39ba59fa769dc0295ebb9d82242d3c4c187358c993a0"}
SOURCES = {
    "T-339": {"task": "T-339", "file": "research/agents_t339/FILL_T328_T339.csv", "sha256": PINS[FILL],
              "merge_commit": "04f371ba889ab3b072a519a58400115664a588d3",
              "checker_run": "Verifier 2026-10-29 17:01 UTC session_01E6cPnc3RADugukdnxKWgYJ (Gate A PASS)"},
    "T-321": {"task": "T-321", "file": "research/agents_t321/summary.json", "sha256": PINS[T321],
              "merge_commit": "59c82a05c08cfecc6e068a8fd831fa544cdc2310",
              "checker_run": "Verifier 2026-10-29 01:02 UTC (Gate A PASS, engine push f8180b18)"},
}
# the physical cause of each roof's face-plan range (T-321 s.2, T-339 F-T339-1): the D band at the wall foot, whose
# nature is not printed; the two readings travel together, never chosen
RANGE_CAUSE = {
    "ROOF-430": "D band B3C / C40 / C47 (0.20 x 3.2 m layer-D band at the 1F wall foot, nature unprinted): to the "
                "band 54.920332 or to the wall face B3A 55.560332 m2 (T-321 s.2)",
    "TERRACE-550": "D band C8A .. CA3 / B5E / C9D 1.078 m2 (F-T339-1): to the finish edge 31.643 or to the wall face "
                   "32.721 m2",
    "ROOF-970": "D band 12E2 / 12E6 (0.075 m band at the 2F west wall foot, nature unprinted): 115.65646 or "
                "115.81396 m2 net of the two dome discs (T-321 s.2)",
}
OUTLINE_KEY = {"ROOF-430": "face_wall_m2", "TERRACE-550": "face_wall_m2", "ROOF-970": None, "ROOF-1390": None}
LAYER_NAME = {"FALLS_SCREED": "FALLS_SCREED", "INSULATION": "INSULATION", "PROTECTION": "PROTECTION",
              "FINISH": "FINISH"}
HELD_ROOF = {"ROOF-1390": "owner Q-34: the +13.90 roof stays HELD (no number, never 0); no roof plan (D-62)"}


def _pinned(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 differs from the merged file (edited input: stop)")
    return b.decode("utf-8")


def _f(x):
    return None if x in (None, "") else float(x)


def build(project_id=None):
    fill = list(csv.DictReader(_pinned(FILL).splitlines()))
    bind = {(r["roof"], r["layer"]): r for r in csv.DictReader(_pinned(BIND).splitlines())}
    t321 = json.loads(_pinned(T321))
    roofs = {}
    for r in fill:
        rid = r["roof"]
        rf = roofs.setdefault(rid, {"roof": rid, "element_id": r["element_id"], "floor": r["floor"], "layers": []})
        b = bind[(rid, r["layer"])]
        if r["action"].startswith("UNCHANGED"):
            key = {"MEMBRANE": "membrane_line", "UPTURN": "upturn_line"}[r["layer"]]
            rf[key] = {"line_id": r["target"], "item_code": {"MEMBRANE": "FIN.WP.ROOF",
                                                            "UPTURN": "FIN.WP.ROOF_UPTURN"}[r["layer"]],
                       "evidence_state": b["line_state"], "measured_net": _f(b["line_quantity"]),
                       "bound_by": "T-339 BINDING_T339.csv"}
            continue
        lo, hi = _f(r["basis_area_lo"]), _f(r["basis_area_hi"])
        q = _f(r["quantity_lo"]) if r["status"] == "DRAWING-CONFIRMED" else None
        if q is not None and _f(r["quantity_hi"]) != q:
            raise SystemExit(f"{rid} {r['layer']}: a valued layer is one figure, the row gives a range")
        st = r["status"] if rid not in HELD_ROOF else "HELD"
        ly = {"layer": LAYER_NAME[r["layer"]], "source_task": "T-339", "status": st, "owner_trade": r["owner_trade"],
              "unit": r["unit"], "edge": "FINISH" if r["layer"] == "FINISH" else "FACE",
              "edge_handles": b["edge_handles"].split() if b["edge_handles"] else [],
              "scope_source": b["scope_source"], "quantity": q, "thickness_m": None,
              "held_reason": r["held_reason"] or None, "bounds_beside": r["bounds_beside"] or None,
              "runs_up_parapet": False}
        if lo is not None and rid not in HELD_ROOF:
            ly["basis_lo"], ly["basis_hi"] = lo, hi
            if hi - lo > 1e-9:
                ly["range_cause"] = RANGE_CAUSE[rid]
        if r["layer"] == "FALLS_SCREED" and rid in t321["falls"]:
            fz = t321["falls"][rid]
            ly["falls_beside"] = (f"T-321 falls model on its outline {fz['outline_area_m2']} m2: rise max "
                                  f"{fz['rise_max_m'][0]} .. {fz['rise_max_m'][1]} m, volume above the t0 plane "
                                  f"{fz['volume_above_t0_m3'][0]} .. {fz['volume_above_t0_m3'][1]} m3 "
                                  f"({fz['note']}); beside only, not a bound")
        rf["layers"].append(ly)
    out = []
    for rid in ("ROOF-430", "TERRACE-550", "ROOF-970", "ROOF-1390"):
        rf = roofs[rid]
        z = t321["zones"][rid]
        if rid in HELD_ROOF:
            rf["held_roof"] = {"reason": HELD_ROOF[rid],
                               "drawing_derived_beside": t321["roof_1390_drawing_derived"]["inside_parapet_faces_m2"]}
            rf["outline_m2"] = None
            rf["fall_printed_pct"] = None
        else:
            rf["held_roof"] = None
            rf["outline_m2"] = (z["face_wall_m2"] if OUTLINE_KEY[rid] else
                                round(z["face_wall_m2"] - sum(z["footprints_m2"].values()), 6))
            rf["fall_printed_pct"] = 1.0          # T-221 / T-321: 'SLOPE 1%' printed on the drainage sheets
        out.append(rf)
    return {"schema": "URBAN_V3031_INPUTS_V1", "project_id": project_id,
            "sources": [SOURCES["T-339"], SOURCES["T-321"]], "roofs": out,
            "parapet_lines": [],
            "named_not_lines": [
                {"what": "area round the oval void +5.50 (T-303 6.130 m2, no ROOF label)", "status": "UNKNOWN",
                 "why": "no roof element: no layer line (T-321 table)"},
                {"what": "dome footprints on ROOF-970 (2 x 15.359 m2)", "status": "SCOPE_UNKNOWN",
                 "why": "finish EXCLUDED (the hatch stops at the dome circles); membrane / screed / insulation / "
                        "protection under a dome SCOPE_UNKNOWN (T-303 / Q-24 / Q-29 C): beside the ROOF-970 rows"},
                {"what": "layer upturns on parapets (screed / insulation / protection / finish)", "status": "HELD",
                 "why": "printed nowhere: only the membrane's 0.20 m upturn has a rule (existing FIN.WP.ROOF_UPTURN "
                        "lines); every other layer stops at the parapet inner face"}]}


PARAPETS = ROOT / "research/agents_t328/PARAPET_LINES_V3030.json"


def parapet_records(lines):
    """the candidate's STR.CONC.PARAPET lines as they stand (id, item, element, state, figure; no coordinate)."""
    return [{"line_id": ln["line_id"], "item_code": ln["item_code"], "evidence_state": ln["evidence_state"],
             "measured_net": ln.get("measured_net"), "element_id": (ln.get("location") or {}).get("element_id")}
            for ln in sorted(lines, key=lambda x: x["line_id"]) if ln["item_code"] == "STR.CONC.PARAPET"]


def write_parapets(lines):
    PARAPETS.write_text(json.dumps({"from": "V3_0_30_BOQ_LINES.json of the T-328 run (candidate of record V3.0.30)",
                                    "lines": parapet_records(lines)}, indent=1) + "\n", encoding="utf-8")


def build_bound(project_id=None):
    """build() + the parapet lines pinned from the V3.0.30 candidate: the engine re-checks each on the run's lines
    (stale binding stops) and refuses a roof layer on a parapet element."""
    doc = build(project_id)
    doc["parapet_lines"] = json.loads(PARAPETS.read_text(encoding="utf-8"))["lines"]
    return doc


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    for rf in d["roofs"]:
        print(rf["roof"], rf["outline_m2"], [(ly["layer"], ly["status"], ly["quantity"], ly.get("basis_lo"),
                                               ly.get("basis_hi")) for ly in rf["layers"]],
              (rf.get("membrane_line") or {}).get("line_id"))
