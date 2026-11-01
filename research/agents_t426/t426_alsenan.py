"""T-426 Alsenan: the ground-beam SECTION census, one row per candidate STR.CONC.GROUND_BEAM line (58), run by run.

    # 1. from the private candidate run (values only: line id, state, b, D, L, value):
    .work/venv/bin/python -I research/agents_t426/t426_alsenan.py --candidate <run>/v3036/V3_0_36_BOQ_LINES.json --write-candidate
    # 2. census (no private input; committed inputs only):
    .work/venv/bin/python -I research/agents_t426/t426_alsenan.py            # check  (REPRODUCED / DIFFERS)
    .work/venv/bin/python -I research/agents_t426/t426_alsenan.py --write    # rebuild CENSUS_T426.json / .csv

Inputs (committed, merged):
  research/agents_t416/ALSENAN_T416_INPUT.json   band geometry and column cuts per frame (T-416, Gate A b7bb914a)
  research/agents_t416/summary_t416.json          58 candidate lines bound once to a drawn band (T-416)
  research/agents_t242/LEDGER_T242.csv            position (interior / exterior main / exterior annex / court), the
                                                  beams landing between the faces (D-33) (T-242 MERGED 9455a63d)
  research/agents_t289/BAND_PAIRING_T289.json     engine band -> T-242 run (T-289 MERGED 455c93c4)
  research/agents_t426/ALSENAN_T426_READ.json     own read: GBP section-mark census; supports beside the F-1 bands
  research/agents_t426/CANDIDATE_V3036_GB_LINES.json   the 58 lines on the candidate of record V3.0.36
Exterior main-house depth 0.95 m: printed by two levels of the element (GF slab top +0.95, outer normal ground +-0.00),
T-253 MERGED dff9cb79 / T-289 (Checker-verified basis); annex exterior: D-35 source CONFLICT (no printed depth).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from t426_rules import line_stake, run_section  # noqa: E402
from t426_spans import FRAMES, spans_by_frame  # noqa: E402

T416_IN = ROOT / "research/agents_t416/ALSENAN_T416_INPUT.json"
T416_SUM = ROOT / "research/agents_t416/summary_t416.json"
T242 = ROOT / "research/agents_t242/LEDGER_T242.csv"
T289 = ROOT / "research/agents_t289/BAND_PAIRING_T289.json"
READ = HERE / "ALSENAN_T426_READ.json"
CAND = HERE / "CANDIDATE_V3036_GB_LINES.json"
OUT_JSON = HERE / "CENSUS_T426.json"
OUT_CSV = HERE / "CENSUS_T426.csv"
EXTERIOR_MAIN_D = (0.95, 0.95)
READING_GAP_MAX_M = 0.10      # a column beside the band end within this gap gives a second end-face reading


def _r(x, n=6):
    return None if x is None else round(float(x), n) + 0.0


def _faces(name):
    return frozenset(name.split("#")[0].replace("ARC:", "").split("+"))


def load():
    t416 = json.loads(T416_IN.read_text(encoding="utf-8"))
    summ = json.loads(T416_SUM.read_text(encoding="utf-8"))
    pairing = json.loads(T289.read_text(encoding="utf-8"))["bands"]
    led = {r["run"]: r for r in csv.DictReader(io.StringIO(T242.read_text(encoding="utf-8")))
           if r["component"].startswith("GB")}
    read = json.loads(READ.read_text(encoding="utf-8"))
    cand = json.loads(CAND.read_text(encoding="utf-8")) if CAND.exists() else None
    return t416, summ, pairing, led, read, cand


def run_spans(t416, led, read):
    """Clear span of every interior run per frame (+ a second end-face reading where a column sits beside the end)."""
    bands = {frozenset(b["faces"]): b for b in t416["bands"]}
    out = {}
    by_band = {}
    for run, r in led.items():
        if r["component"] != "GB-INTERIOR":
            continue
        f = _faces(run)
        cands = [b for k, b in bands.items() if k <= f and b["dir"] != "C"]
        best = None
        for b in cands:
            segs = spans_by_frame(b)["GBP"]
            for i, s in enumerate(segs):
                d = abs(s[2] - float(r["L_m"]))
                if best is None or d < best[0]:
                    best = (d, b, i)
        if best is None or best[0] > 0.05:
            raise SystemExit(f"run {run}: no drawn segment within 0.05 m of its face-to-face length")
        by_band.setdefault(best[1]["id"], []).append((run, best[2]))
        out[run] = {"band": best[1]["id"], "segment": best[2], "L_T242_m": float(r["L_m"]), "match_m": _r(best[0], 4)}
    # equal-length runs on one band: the k-th run is the k-th segment (T-242 numbers runs along the band)
    for bid, rows in by_band.items():
        segs = spans_by_frame(next(b for b in t416["bands"] if b["id"] == bid))["GBP"]
        runs = sorted(r for r, _ in rows)
        if len(runs) == len(segs) and len(runs) > 1:
            for k, run in enumerate(sorted(runs, key=lambda x: int(x.split("#")[1]))):
                out[run]["segment"] = k
    for run, o in out.items():
        b = next(x for x in t416["bands"] if x["id"] == o["band"])
        sp = spans_by_frame(b)
        o["spans_by_frame_m"] = {k: sp[k][o["segment"]][2] for k in FRAMES if len(sp[k]) > o["segment"]}
        # end-face reading: a column outline beside the band end (not cut by the centreline, gap <= 0.10 m)
        rd = read["bands"].get(o["band"])
        if rd:
            segs = sp["GBP"]
            first, last = o["segment"] == 0, o["segment"] == len(segs) - 1
            for c in rd["columns_near"]:
                if c["frame"] != "GBP" or c["cut_by_centreline"] or c["gap_to_band_face_m"] > READING_GAP_MAX_M:
                    continue
                if first and c["along_from_m"] < 0.0 < c["along_to_m"]:
                    o["spans_by_frame_m"]["COLUMN_FACE_" + c["handle"]] = _r(sp["GBP"][0][2] - c["along_to_m"], 4)
                if last and c["along_from_m"] < rd["drawn_m"] < c["along_to_m"]:
                    o["spans_by_frame_m"]["COLUMN_FACE_" + c["handle"]] = _r(
                        sp["GBP"][-1][2] - (rd["drawn_m"] - c["along_from_m"]), 4)
    return out


def section_of(run, r, spans):
    comp, part = r["component"], r["part"]
    loaded = bool(r["d33_tees"].strip())
    if comp == "GB-INTERIOR":
        return run_section("INTERIOR", spans[run]["spans_by_frame_m"], loaded=loaded)
    if comp.startswith("GB-EXTERIOR"):
        return run_section("EXTERIOR", {}, EXTERIOR_MAIN_D if part == "MAIN" else None)
    if comp == "GB-COURT":
        return run_section("COURT", {})
    raise SystemExit(f"unknown component {comp}")


def runs_of_line(line_band, t416_band, pairing, led):
    p = pairing.get(line_band)
    if p and p["runs"]:
        return [x["run"] for x in p["runs"]]
    guess = t416_band + "#1"
    return [guess] if guess in led else []


def census():
    t416, summ, pairing, led, read, cand = load()
    spans = run_spans(t416, led, read)
    cand_by_id = {c["line_id"]: c for c in cand["lines"]} if cand else {}
    rows = []
    for b in summ["bands"]:
        for ln in b["engine_lines"]:
            c = cand_by_id.get(ln["line_id"])
            if cand and c is None:
                raise SystemExit(f"{ln['line_id']} not in the candidate extract")
            D = c["D_m"] if c else ln["D_print_m"]
            bw = c["b_m"] if c else b["width_m"]
            state = c["state"] if c else ln["state"]
            runs = runs_of_line(ln["band"], b["band"], pairing, led)
            if not runs:
                raise SystemExit(f"{ln['line_id']}: no run")
            rr = []
            for run in runs:
                r = led[run]
                sec = section_of(run, r, spans)
                rr.append({"run": run, "position": r["component"].replace("GB-", "") + ("/" + r["part"] if r["part"] else ""),
                           "L_m": float(r["L_m"]), "spans_by_frame_m": spans.get(run, {}).get("spans_by_frame_m", {}),
                           "titles": list(sec["titles"]), "frames_differ": sec["frames_differ"],
                           "printed_b_m": sec["b_m"], "printed_D_m": list(sec["D_m"]) if sec["D_m"] else None,
                           "section_status": sec["status"], "d33_tees": r["d33_tees"], "d33_held": sec["d33_held"],
                           "_sec": sec})
            valued = state == "VALUED" and D is not None
            stake, verdict = line_stake(bw, D if valued else None, [{"L_m": x["L_m"], "section": x["_sec"]} for x in rr])
            for x in rr:
                x.pop("_sec")
            ev = c["value_m3"] if c else ln["value_m3"]
            rows.append({"line_id": ln["line_id"], "engine_band": ln["band"], "drawn_band": b["band"], "state": state,
                         "evidence_state": c["evidence_state"] if c else None,
                         "downgrade": (c["downgrade"] or {}).get("downgrade_id") if c else None,
                         "candidate_b_m": bw, "candidate_D_m": D, "candidate_L_m": c["L_m"] if c else ln["length_m"],
                         "candidate_value_m3": _r(ev) if valued else None,
                         "engine_value_m3_held": _r(ev) if (not valued and ev is not None) else None,
                         "runs": rr, "stake_m3": [stake[0], stake[1]] if stake else None, "verdict": verdict,
                         "d33_held": any(x["d33_held"] for x in rr)})
    rows.sort(key=lambda r: (r["drawn_band"], r["engine_band"]))
    tot = {}
    for r in rows:
        t = tot.setdefault(r["verdict"], {"lines": 0, "lo_m3": 0.0, "hi_m3": 0.0, "value_m3": 0.0})
        t["lines"] += 1
        if r["stake_m3"]:
            t["lo_m3"] = _r(t["lo_m3"] + r["stake_m3"][0])
            t["hi_m3"] = _r(t["hi_m3"] + r["stake_m3"][1])
        if r["candidate_value_m3"]:
            t["value_m3"] = _r(t["value_m3"] + r["candidate_value_m3"])
    return {"schema": "T426_GB_SECTION_CENSUS_V1",
            "candidate": cand["candidate"] if cand else "V3.0.29 ids via T-416 (candidate extract absent)",
            "candidate_json_sha256": cand["source_json_sha256"] if cand else None,
            "gbp_section_marks": read["gbp_text_census"]["section_marks"],
            "gbp_texts_read": read["gbp_text_census"]["texts_read"],
            "lines": rows, "totals_by_verdict": dict(sorted(tot.items())),
            "inputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (T416_IN, T416_SUM, T242, T289, READ) + ((CAND,) if cand else ())}}


def to_csv(doc):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["line_id", "state", "b_used_m", "D_used_m", "L_line_m", "value_m3", "run", "position", "L_run_m",
                "span_GBP_m", "span_FP_m", "span_CAP_m", "span_other_reading_m", "titles", "printed_b_m",
                "printed_D_m", "section_status", "d33_held", "line_verdict", "line_stake_lo_m3", "line_stake_hi_m3"])
    for r in doc["lines"]:
        for x in r["runs"]:
            sp = x["spans_by_frame_m"]
            other = ";".join(f"{k}={v}" for k, v in sorted(sp.items()) if k not in FRAMES)
            w.writerow([r["line_id"], r["state"], r["candidate_b_m"], r["candidate_D_m"], r["candidate_L_m"],
                        r["candidate_value_m3"], x["run"], x["position"], x["L_m"], sp.get("GBP"), sp.get("FP"),
                        sp.get("CAP"), other, "+".join(x["titles"]), x["printed_b_m"],
                        "/".join(str(d) for d in x["printed_D_m"]) if x["printed_D_m"] else "",
                        x["section_status"], x["d33_held"], r["verdict"],
                        r["stake_m3"][0] if r["stake_m3"] else "", r["stake_m3"][1] if r["stake_m3"] else ""])
    return s.getvalue()


def _depth_used(x, dim, val):
    """The depth a valued line is valued at: the printed depth its own formula names ('D 0.95', SOURCE_DERIVED
    re-base), else its own value / its own net plan (net plan x class depth, PROVISIONAL lines)."""
    import re
    f = (x.get("calculation") or {}).get("formula") or ""
    m = re.search(r"\bD (\d+\.\d+)", f)
    if m:
        return float(m.group(1))
    plan = dim.get("net_plan_m2") or ((dim.get("length_m") or 0) * (dim.get("width_m") or 0)) or None
    return round(val / plan, 6) + 0.0 if plan else None


def write_candidate(path, downgrades=None):
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    lines = data["lines"] if isinstance(data, dict) and "lines" in data else data
    want = {ln["line_id"] for b in json.loads(T416_SUM.read_text(encoding="utf-8"))["bands"] for ln in b["engine_lines"]}
    gb = [x for x in lines if x.get("item_code") == "STR.CONC.GROUND_BEAM"]
    by_id = {x["line_id"]: x for x in lines}
    # Checker downgrade records in force (WORKFLOW_CONTROLS s.4; joined as the export joins them): a LINE_CONTENT_V1
    # record holds its lines only while their content is byte-identical to what it bound (T-294)
    held_by = {}
    dg_meta = None
    if downgrades:
        sys.path.insert(0, str(ROOT))
        from tools.boq_export_v1 import own_content_status
        draw = Path(downgrades).read_bytes()
        dg_meta = {"file": Path(downgrades).parent.name + "/" + Path(downgrades).name,
                   "sha256": hashlib.sha256(draw).hexdigest()}
        for r in json.loads(draw)["downgrades"]:
            ids = set(r.get("line_ids", [])) & {x["line_id"] for x in gb}
            if not ids:
                continue
            st = own_content_status(r, by_id) if r.get("binding") == "LINE_CONTENT_V1" else "unbound record"
            for i in ids:
                held_by[i] = {"downgrade_id": r["downgrade_id"], "state": r.get("state"),
                              "binding": "CURRENT" if st is None else "STALE: " + st}
    out = []
    for x in gb:
        dim = x.get("dimensions") or ((x.get("calculation") or {}).get("inputs") or {}).get("dimensions") or {}
        val = x.get("measured_net")
        L = dim.get("length_m")
        b = dim.get("width_m")
        D = _depth_used(x, dim, val) if val is not None else None
        eid = x.get("element_id") or (x.get("location") or {}).get("element_id")
        dg = held_by.get(x["line_id"])
        contract_held = bool(dg and dg["binding"] == "CURRENT" and dg["state"] == "HELD")
        out.append({"line_id": x["line_id"], "element_id": eid, "evidence_state": x.get("evidence_state"),
                    "engine_state": "VALUED" if val is not None else "HELD",
                    "state": "HELD" if (val is None or contract_held) else "VALUED",
                    "downgrade": dg, "b_m": b, "D_m": D, "L_m": L, "net_plan_m2": dim.get("net_plan_m2"),
                    "value_m3": None if val is None else round(val, 6) + 0.0})
    ids = {x["line_id"] for x in out}
    doc = {"schema": "T426_CANDIDATE_GB_LINES_V1", "candidate": "ARCH_TAKEOFF_V3.0.36", "downgrades_joined": dg_meta,
           "source_json_sha256": hashlib.sha256(raw).hexdigest(), "ground_beam_lines": len(out),
           "t416_bound_ids_present": len(want & ids), "t416_bound_ids_missing": sorted(want - ids),
           "lines_not_bound_by_t416": sorted(ids - want), "lines": sorted(out, key=lambda r: r["line_id"])}
    CAND.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("written", CAND.name, len(out), "lines; T-416 ids present", len(want & ids), "missing", len(want - ids))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--candidate" in argv:
        dg = argv[argv.index("--downgrades") + 1] if "--downgrades" in argv else None
        write_candidate(argv[argv.index("--candidate") + 1], dg)
        if "--write-candidate" in argv:
            return
    doc = census()
    txt = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    csv_txt = to_csv(doc)
    if "--write" in argv:
        OUT_JSON.write_text(txt, encoding="utf-8")
        OUT_CSV.write_text(csv_txt, encoding="utf-8")
        print("written", OUT_JSON.name, OUT_CSV.name)
    else:
        same = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == txt and \
            OUT_CSV.exists() and OUT_CSV.read_text(encoding="utf-8") == csv_txt
        print("REPRODUCED" if same else "DIFFERS")
        if not same:
            raise SystemExit(1)
    for k, v in doc["totals_by_verdict"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
