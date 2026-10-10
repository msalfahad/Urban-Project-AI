"""PA08 comparison: frozen blind registers against the sealed truth pack, case by case, fact by fact.

Every physical fact is classified into one of the predeclared classes.  HUMAN_REVIEW_SAFE is a safe failure: not
automation, but not a silent wrong quantity either.  The key metric is SILENT_WRONG_QUANTITY_COUNT: a quantity
line that the bridge allowed whose space, bands, openings or roles disagree with the verified truth.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from research.qs_wall_treatment_01.pa08 import config as C8

ROLE_MAP_BAND = {"WALL": "ACCEPTED", "COLUMN_FACE": "ACCEPTED", "GLAZING": "NOT_ACCEPTED", "NOT_MATERIAL": "NOT_ACCEPTED"}
ROLE_MAP_OPENING = {"DOOR": ("CONFIRMED_DOOR_OPENING", "PROBABLE_DOOR_OPENING"), "WINDOW": ("CONFIRMED_WINDOW_OPENING",), "GLAZED": ("CONFIRMED_GLAZED_OPENING",), "OPEN_PASSAGE": ("CONFIRMED_OPEN_PASSAGE",),
                    "NICHE_NOT_OPENING": ("UNRESOLVED", "MATERIAL_CONTINUITY", "CAD_JUNCTION")}


def _load(d, n):
    p = Path(d) / f"{n}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def _inside(bbox, x, y):
    return bbox[0] - 1 <= x <= bbox[2] + 1 and bbox[1] - 1 <= y <= bbox[3] + 1


def _seg_len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _within(engine_mm, truth_mm, tol):
    if engine_mm is None or truth_mm is None:
        return False
    lim = max(tol.get("ABS_MM", 0.0), tol.get("REL", 0.0) * abs(truth_mm))
    return abs(engine_mm - truth_mm) <= lim


def _band_matches(band, seg):
    """A band matches a truth wall segment when its axis line passes within thickness of both truth endpoints and covers them."""
    c = band["CENTERLINE_IF_DERIVED"] or {}
    if c.get("KIND") != "LINE":
        return False
    ux, uy = c["U"]; nx, ny = -uy, ux
    off = c["AXIS_OFFSET_MM"]; lo, hi = c["EXTENT_MM"]
    ok = True
    for p in (seg["A_MM"], seg["B_MM"]):
        d = abs(nx * p[0] + ny * p[1] - off)
        t = ux * p[0] + uy * p[1]
        ok = ok and d <= max(band["THICKNESS_MM"], 100.0) and lo - 100 <= t <= hi + 100
    return ok


def _arc_matches(band, seg):
    c = band["CENTERLINE_IF_DERIVED"] or {}
    if c.get("KIND") != "ARC":
        return False
    return math.hypot(c["CENTRE_MM"][0] - seg["CENTRE_MM"][0], c["CENTRE_MM"][1] - seg["CENTRE_MM"][1]) <= 50 and abs(c["R_AXIS_MM"] - seg["RADIUS_AXIS_MM"]) <= 50


def compare(blind_dir, truth_pack, blind_freeze):
    # the freeze must still hold: the blind output was not touched after the truth was opened
    from research.qs_wall_treatment_01.pa08.blind_run import _sha
    for name, h in blind_freeze["FILES"].items():
        assert _sha(Path(blind_dir) / name) == h, f"blind output {name} changed after its freeze"
    bands = (_load(blind_dir, "PA07_MATERIAL_BAND_REGISTER") or {}).get("ROWS", [])
    sites = (_load(blind_dir, "PA07_OPENING_SITE_REGISTER") or {}).get("ROWS", [])
    spaces = (_load(blind_dir, "PA07_PHYSICAL_SPACE_REGISTER") or {}).get("ROWS", [])
    faces = (_load(blind_dir, "PA07_PLANAR_FACE_REGISTER") or {}).get("ROWS", [])
    cols = (_load(blind_dir, "PA07_COLUMN_JUNCTION_REGISTER") or {}).get("ROWS", [])
    safety = (_load(blind_dir, "PA07_QUANTITY_SAFETY_REGISTER") or {}).get("ROWS", [])
    band_by_id = {b["BAND_ID"]: b for b in bands}
    site_by_id = {s["SITE_ID"]: s for s in sites}
    rows, metrics = [], Counter()
    wall_recovered = wall_missed = wall_false = 0.0
    curved_err = []
    for case in truth_pack["CASES"]:
        box = case["SOURCE_LOCATOR"]["BBOX_MM"]
        # ---- walls
        for seg in case.get("WALL_SEGMENTS", []):
            truth_len = seg["DEVELOPED_LENGTH_MM"]
            matched = [b for b in bands if _band_matches(b, seg)]
            acc = [b for b in matched if b["MATERIAL_STATUS"] == "ACCEPTED"]
            unres = [b for b in matched if b["MATERIAL_STATUS"] == "UNRESOLVED"]
            if seg["ROLE"] in ("WALL", "COLUMN_FACE") and seg["MATERIAL_PRESENT"]:
                if acc:
                    eng = max(b["DEVELOPED_LENGTH_MM"] for b in acc)
                    cls = "WITHIN_TOLERANCE" if _within(eng, truth_len, C8.TOLERANCES["STRAIGHT_DEVELOPED_LENGTH"]) else "GEOMETRY_MISMATCH"
                    if abs(eng - truth_len) < 1e-6:
                        cls = "EXACT_MATCH"
                    wall_recovered += truth_len if cls != "GEOMETRY_MISMATCH" else 0.0
                    if cls == "GEOMETRY_MISMATCH":
                        wall_missed += truth_len
                elif unres:
                    cls, eng = "HUMAN_REVIEW_SAFE", None; wall_missed += truth_len
                else:
                    cls, eng = "MISSING_DETECTION", None; wall_missed += truth_len
            else:
                if acc:
                    cls, eng = "FALSE_POSITIVE", max(b["DEVELOPED_LENGTH_MM"] for b in acc); wall_false += eng
                elif unres:
                    cls, eng = "HUMAN_REVIEW_SAFE", None
                else:
                    cls, eng = "EXACT_MATCH", None      # correctly not material
            rows.append({"CASE_ID": case["CASE_ID"], "FACT": "WALL_SEGMENT", "ID": seg["SEGMENT_ID"], "TRUTH": {"ROLE": seg["ROLE"], "MATERIAL_PRESENT": seg["MATERIAL_PRESENT"], "DEVELOPED_LENGTH_MM": truth_len},
                         "ENGINE": {"BANDS": [(b["BAND_ID"], b["MATERIAL_STATUS"], b["DEVELOPED_LENGTH_MM"]) for b in matched][:4], "DEVELOPED_LENGTH_MM": eng}, "CLASS": cls})
            metrics[cls] += 1
        # ---- curved
        for seg in case.get("CURVED_SEGMENTS", []):
            matched = [b for b in bands if _arc_matches(b, seg)]
            acc = [b for b in matched if b["MATERIAL_STATUS"] == "ACCEPTED"]
            if seg["MATERIAL_PRESENT"]:
                if acc:
                    eng = max(b["DEVELOPED_LENGTH_MM"] for b in acc)
                    ok = _within(eng, seg["DEVELOPED_LENGTH_MM"], C8.TOLERANCES["CURVED_DEVELOPED_LENGTH"])
                    cls = "WITHIN_TOLERANCE" if ok else "GEOMETRY_MISMATCH"; curved_err.append(abs(eng - seg["DEVELOPED_LENGTH_MM"]) / max(seg["DEVELOPED_LENGTH_MM"], 1e-9))
                    wall_recovered += seg["DEVELOPED_LENGTH_MM"] if ok else 0.0
                    if not ok:
                        wall_missed += seg["DEVELOPED_LENGTH_MM"]
                else:
                    cls, eng = ("HUMAN_REVIEW_SAFE" if matched else "MISSING_DETECTION"), None; wall_missed += seg["DEVELOPED_LENGTH_MM"]
            else:
                cls, eng = ("FALSE_POSITIVE" if acc else "EXACT_MATCH"), (max(b["DEVELOPED_LENGTH_MM"] for b in acc) if acc else None)
                if acc:
                    wall_false += eng
            rows.append({"CASE_ID": case["CASE_ID"], "FACT": "CURVED_SEGMENT", "ID": seg["SEGMENT_ID"], "TRUTH": {"DEVELOPED_LENGTH_MM": seg["DEVELOPED_LENGTH_MM"], "MATERIAL_PRESENT": seg["MATERIAL_PRESENT"]},
                         "ENGINE": {"DEVELOPED_LENGTH_MM": eng, "BANDS": [(b["BAND_ID"], b["MATERIAL_STATUS"]) for b in matched][:4]}, "CLASS": cls})
            metrics[cls] += 1
        # ---- openings
        for op in case.get("OPENINGS", []):
            mid = ((op["A_MM"][0] + op["B_MM"][0]) / 2, (op["A_MM"][1] + op["B_MM"][1]) / 2)
            near = []
            for s in sites:
                b = band_by_id.get(s["HOST_BAND_ID"])
                if not b or not _inside(box, mid[0], mid[1]):
                    continue
                c = b["CENTERLINE_IF_DERIVED"] or {}
                if c.get("KIND") == "LINE":
                    ux, uy = c["U"]; t = ux * mid[0] + uy * mid[1]
                    if s["AXIAL_START"] - 150 <= t <= s["AXIAL_END"] + 150 and abs((-uy) * mid[0] + ux * mid[1] - c["AXIS_OFFSET_MM"]) <= b["THICKNESS_MM"] + 100:
                        near.append(s)
                elif c.get("KIND") == "ARC":
                    ang = math.atan2(mid[1] - c["CENTRE_MM"][1], mid[0] - c["CENTRE_MM"][0]); t = ((ang - c["THETA0_RAD"]) % (2 * math.pi)) * c["R_AXIS_MM"]
                    if s["AXIAL_START"] - 150 <= t <= s["AXIAL_END"] + 150:
                        near.append(s)
            want = ROLE_MAP_OPENING.get(op["ROLE"], ())
            if not near:
                cls, eng = ("EXACT_MATCH" if op["ROLE"] == "NICHE_NOT_OPENING" else "MISSING_DETECTION"), None
            else:
                s = near[0]
                if s["CLASS"] in want and s["STATUS"] == "ESTABLISHED":
                    cls = "WITHIN_TOLERANCE" if _within(s["SPAN_MM"], op["WIDTH_MM"], C8.TOLERANCES["OPENING_WIDTH"]) else "OPENING_MISMATCH"
                    if abs(s["SPAN_MM"] - op["WIDTH_MM"]) < 1e-6:
                        cls = "EXACT_MATCH"
                elif s["CLASS"] == "UNRESOLVED" or s["STATUS"] != "ESTABLISHED":
                    cls = "HUMAN_REVIEW_SAFE"
                else:
                    cls = "ROLE_MISMATCH"
                eng = {"CLASS": s["CLASS"], "STATUS": s["STATUS"], "SPAN_MM": s["SPAN_MM"]}
            rows.append({"CASE_ID": case["CASE_ID"], "FACT": "OPENING", "ID": op["OPENING_ID"], "TRUTH": {"ROLE": op["ROLE"], "WIDTH_MM": op["WIDTH_MM"]}, "ENGINE": eng, "CLASS": cls})
            metrics[cls] += 1
        # ---- spaces: count inside the locator
        rel = case.get("PHYSICAL_SPACE_RELATION", {})
        want_n = rel.get("SPACE_COUNT")
        inside = [s for s in spaces if _inside(box, *next((f["CENTROID_MM"] for f in faces if f["FACE_ID"] == s["FACE_ID"]), (math.nan, math.nan)))]
        if want_n is not None:
            n = len(inside)
            prov = [s for s in inside if s["GEOMETRY_STATUS"] != "ESTABLISHED"]
            if n == want_n:
                cls = "EXACT_MATCH" if not prov else "HUMAN_REVIEW_SAFE"
            elif n < want_n:
                cls = "SPACE_TOPOLOGY_MISMATCH" if not prov else "HUMAN_REVIEW_SAFE"; metrics["SPACES_FALSELY_MERGED"] += want_n - n
            else:
                cls = "SPACE_TOPOLOGY_MISMATCH" if not prov else "HUMAN_REVIEW_SAFE"; metrics["SPACES_FALSELY_SPLIT"] += n - want_n
            rows.append({"CASE_ID": case["CASE_ID"], "FACT": "PHYSICAL_SPACE_COUNT", "ID": case["CASE_ID"], "TRUTH": want_n, "ENGINE": {"COUNT": n, "PROVISIONAL": len(prov)}, "CLASS": cls})
            metrics[cls] += 1
            if cls == "EXACT_MATCH":
                metrics["SPACES_CORRECT"] += 1
        # ---- columns
        for col in case.get("COLUMNS", []):
            hit = [c for c in cols if math.hypot(c["OBJECT_GEOMETRY"]["CENTRE_MM"][0] - col["CENTRE_MM"][0], c["OBJECT_GEOMETRY"]["CENTRE_MM"][1] - col["CENTRE_MM"][1]) <= 100]
            if not hit:
                cls, eng = "MISSING_DETECTION", None
            else:
                c = hit[0]
                exposed_eng = len(c["EXPOSED_TO_SPACE"]["FACE_STRETCHES"]) + sum(1 for s in c["EXPOSED_TO_SPACE"]["SHORT_SIDES"] if s["STATE"] != "EMBEDDED_IN_WALL_BAND")
                cls = "EXACT_MATCH" if exposed_eng == len(col.get("EXPOSED_FACES", [])) else "ROLE_MISMATCH"
                eng = {"COLUMN_ID": c["COLUMN_ID"], "EXPOSED_FACES": exposed_eng, "STATUS": c["EXPOSED_TO_SPACE"]["STATUS"]}
            rows.append({"CASE_ID": case["CASE_ID"], "FACT": "COLUMN", "ID": col["COLUMN_ID"], "TRUTH": {"EXPOSED_FACES": len(col.get("EXPOSED_FACES", []))}, "ENGINE": eng, "CLASS": cls})
            metrics[cls] += 1
            if cls == "EXACT_MATCH":
                metrics["COLUMN_FACES_CORRECT"] += 1
    # ---- silent wrong quantities: an allowed line on a space / band / opening with a mismatch inside its case
    mismatched_cases = {r["CASE_ID"] for r in rows if r["CLASS"] in ("ROLE_MISMATCH", "GEOMETRY_MISMATCH", "OPENING_MISMATCH", "SPACE_TOPOLOGY_MISMATCH", "FALSE_POSITIVE", "MISSING_DETECTION")}
    space_case = {}
    for case in truth_pack["CASES"]:
        box = case["SOURCE_LOCATOR"]["BBOX_MM"]
        for s in spaces:
            cen = next((f["CENTROID_MM"] for f in faces if f["FACE_ID"] == s["FACE_ID"]), None)
            if cen and _inside(box, *cen):
                space_case[s["SPACE_ID"]] = case["CASE_ID"]
    silent = [r["SAFETY_ID"] for r in safety if r["BRIDGE_ALLOWED"] and space_case.get(r["SPACE_ID"]) in mismatched_cases]
    emitted = sum(1 for r in safety if r["BRIDGE_ALLOWED"])
    withheld = sum(1 for r in safety if not r["BRIDGE_ALLOWED"])
    out = {"ARTIFACT": "PA08_INDEPENDENT_VALIDATION_RESULT", "STATUS": "EXECUTED", "SOURCE_INDEPENDENT": truth_pack.get("INDEPENDENT", True), "SOURCE_SET": truth_pack.get("PROJECT_ALIAS"),
           "ROWS": rows, "CLASS_COUNTS": {k: v for k, v in metrics.items() if k in C8.COMPARISON_CLASSES},
           "METRICS": {"VERIFIED_PHYSICAL_WALL_LENGTH_RECOVERED_MM": round(wall_recovered, 1), "VERIFIED_PHYSICAL_WALL_LENGTH_MISSED_MM": round(wall_missed, 1), "FALSE_WALL_LENGTH_ACCEPTED_MM": round(wall_false, 1),
                       "VERIFIED_OPENING_COUNT": sum(len(c.get("OPENINGS", [])) for c in truth_pack["CASES"]), "MISSED_OPENING_COUNT": sum(1 for r in rows if r["FACT"] == "OPENING" and r["CLASS"] == "MISSING_DETECTION"),
                       "FALSE_OPENING_COUNT": sum(1 for r in rows if r["FACT"] == "OPENING" and r["CLASS"] in ("FALSE_POSITIVE", "ROLE_MISMATCH")),
                       "PHYSICAL_SPACES_CORRECT": metrics.get("SPACES_CORRECT", 0), "SPACES_FALSELY_MERGED": metrics.get("SPACES_FALSELY_MERGED", 0), "SPACES_FALSELY_SPLIT": metrics.get("SPACES_FALSELY_SPLIT", 0),
                       "CURVED_DEVELOPED_LENGTH_ERROR_MAX_REL": round(max(curved_err), 5) if curved_err else None, "COLUMN_EXPOSED_FACES_CORRECT": metrics.get("COLUMN_FACES_CORRECT", 0),
                       "QUANTITY_LINES_SAFELY_EMITTED": emitted - len(silent), "QUANTITY_LINES_SAFELY_WITHHELD": withheld, "SILENT_WRONG_QUANTITY_COUNT": len(silent), "SILENT_WRONG_QUANTITY_LINES": silent},
           "CRITICAL_MISMATCHES": sorted(mismatched_cases), "TOLERANCES": C8.TOLERANCES, "HUMAN_REVIEW_SAFE_IS_NOT_AUTOMATION": True}
    return out
