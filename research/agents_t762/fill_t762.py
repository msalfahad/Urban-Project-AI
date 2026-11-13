"""T-762 (F-03): every HELD formwork line of the candidate gets a figure, face by face where the face ledger has one.

    python3 -I research/agents_t762/fill_t762.py INDEX.json FACE_LEDGER.json T761_FIX_ROWS.json MAIN_FILL_ALL.json OUT_DIR [T729_ENTRIES.json]

Inputs: the candidate line index (V3.0.78), the formwork face ledger (T-332, one row per face, every face once), the
T-761 concrete fix rows (host concrete figures) and the main-chat MAIN_FILL_ALL set (its FORMWORK_RATIO rows are compared
and superseded here).

Per held formwork line (DELIVERY_MODE s.3 fallback order):
  OQ-10 alternative line (FW:<host>:OQ10:<method>)  -> the FORMED reading of its faces (DEFAULT: below-ground contact
      included, no owner rule excludes it; the EARTH_CAST twin is shown in the basis, never added)
  held face line (FW:<host>:FACES|SIDE:<status>:<alt>:<method>) -> face by face: printed m2, else the midpoint of the
      face's lo..hi bounds, else its held_from lower bound (ESTIMATE); an OQ10_EARTH_CAST twin line = 0 by the adopted
      FORMED reading (DEFAULT, the formed twin carries the faces)
  faces with no value at all, and lines the ledger does not hold -> ratio fallback: host m3 x this villa's m2/m3 of
      the same element type (complete released hosts only) minus the host's other formwork lines, shared by face count
      (ESTIMATE); a host with no concrete figure, or a non-positive residual, takes the face count x the element's
      median released face area (ESTIMATE, named)
  untied faces (FW:FACE:<face>) -> the ledger's no-line row, same face rules
Nothing is summed across alternatives: one formed reading per face.
"""
from __future__ import annotations
import json, re, sys, os, statistics, collections

FW_CODES = ("STR.FORMWORK", "STR.FORMWORK.STAIR")

# Hand-read faces (DRAWING-READ / ESTIMATE): length printed in the face ledger x the depth the T-761 host row adopts.
# face id -> (m2, label, dimension chain)
HAND_FACE = {
    "R4-070": (7.20, "ESTIMATE", "2 sides x L 6.00 x D 0.60 (BAND0016 GB depth adopted by T-761: ST p.13 typical 30x60, same mark)"),
    "T282-136+7D5#1-END": (0.0, "DRAWING-READ", "traced END length 0.0 m: the end sits on a drawn face, no form"),
    "R4-064": (0.72, "ESTIMATE", "2 sides x L 1.20 x D 0.30 (BAND0012.1 depth per T-761: typical 30x30)"),
    "T282-10B+7D1#1-A": (0.03, "ESTIMATE", "delta length 0.10 m x D 0.30 (BAND0012.1)"),
    "R4-073": (6.96, "ESTIMATE", "2 sides x L 5.80 x D 0.60 (BAND0013.2 depth per T-761: typical 30x60)"),
    "R4-065": (1.38, "ESTIMATE", "2 sides x L 2.30 x D 0.30 (BAND0012.2 depth per T-761: typical 30x30)"),
    "R4-130": (6.54, "ESTIMATE", "2 sides x L 5.45 x D 0.60 (BAND0015 depth per T-761: typical 30x60)"),
    "R4-131": (5.10, "ESTIMATE", "2 sides x L 4.25 x D 0.60 (BAND0015)"),
    "T282-7D4+F8#2-A": (0.18, "ESTIMATE", "delta length 0.30 m x D 0.60 (BAND0015)"),
    "R4-071": (1.92, "ESTIMATE", "2 sides x L 2.40 x D 0.40 (BAND0035 depth per T-761: typical 30x40)"),
    "R4-075": (0.30, "ESTIMATE", "2 sides x L 0.50 x D 0.30 (BAND0017.2, concrete IGNORED_SMALL in T-761; form kept)"),
    "T282-13E+7D6#2-B": (0.045, "ESTIMATE", "delta length 0.15 m x D 0.30 (BAND0017.2)"),
    "T282-13E+7D6#2-END": (0.0005, "ESTIMATE", "delta length 0.0017 m x D 0.30 (BAND0017.2)"),
    "R4-325": (0.39, "ESTIMATE", "MS2 closing riser form: height 0.168 + 0.16 = 0.328 x width 1.20 (T-761 L-659243ed basis)"),
    "R4-332": (1.04, "ESTIMATE", "D1 lobby waist soffit = plan 1.035 m2 (T-711 / T-761 basis; 0 if the designer confirms a waist on fill)"),
    "R4-317": (2.00, "ESTIMATE", "MS1-L riser forms 10 x 1.20 x 0.1667 (count and riser printed in the face item)"),
    # dome shells (ST p.7 DETAIL OF DOME 442 / 190 / 10; intrados a 2.11, h 1.80 reproduces the released 24.15 m2):
    # extrados sphere a 2.21, h 1.90 -> R 2.235, base angle 81.4 deg; top form where the surface is steeper than
    # 1.5H:1V (33.7 deg, the usual limit for placing concrete without a top form): 2 pi R^2 (cos 33.7 - cos 81.4)
    "R4-344": (21.42, "ESTIMATE", "DOME-A extrados top form where steeper than 1.5H:1V: 2 pi x 2.235^2 x (0.832 - 0.150) = 21.42 m2 (full extrados 26.68)"),
    "R4-351": (21.42, "ESTIMATE", "DOME-B extrados top form, same shell as DOME-A: 21.42 m2 (full extrados 26.68)"),
    "R4-358": (21.42, "ESTIMATE", "DOME-TOWER extrados top form, same shell (T-761 DOME-3 = shells A / B): 21.42 m2"),
    "R4-357": (24.15, "ESTIMATE", "DOME-TOWER soffit = intrados 2 pi R_i h_i of the same shell as A / B (released 24.15 m2 each)"),
    "R4-359": (1.36, "ESTIMATE", "DOME-TOWER support face = shell edge 0.10 x pi x 4.32 m mean diameter"),
}
# untied lines with no ledger value -> (m2, label, chain); NECKS computed in main()
HAND_LINE = {
    "FW:FACE:T332-LIFT-PIT-INNER": (8.25, "SAFETY", "5.50 m2 per m of pit height (ledger: inner perimeter 7.20 less 1.70 column faces) x 1.50 m = the T-761 SAFETY pit height (D-43)"),
    "FW:FACE:T332-LIFT-PIT-OUTER": (8.25, "SAFETY", "5.50 m2 per m (outer perimeter 8.80 less 3.30 column faces) x 1.50 m SAFETY pit height (D-43); below ground: formed reading"),
    "LIFT_TIE_BEAM:GF:SIDES": (6.50, "ESTIMATE", "2 sides x (0.75 x 1.80 + 0.40 x 0.70 + 0.75 x 1.20 + 0.40 x 1.80) = 6.50 m2 (T-761 runs and nearest printed sections B14 / B1 / B7 / B1)"),
    "LIFT_TIE_BEAM:GF:SOFFIT": (1.10, "ESTIMATE", "soffit 0.20 x 5.50 m runs (T-761)"),
    "FW:FACE:R4-189": (12.60, "ESTIMATE", "boundary pads sides 2 x (1.30 + 0.80) x 0.30 = 1.26 m2 x 10 pads (T-761 count, ST p.14 size); the 20 x 30 boundary columns go with the fence row T-769"),
    "FW:FACE:R4-346": (0.0, "DEFAULT", "no drum concrete in the candidate (named omission T-266; drum material / thickness not printed, G3-b): formwork follows the concrete; RC reading 2 faces x pi x 4.41 x 1.30 = 36.0 m2 named for the designer item"),
    "FW:FACE:R4-353": (0.0, "DEFAULT", "DOME-B drum: as DOME-A (no drum concrete line; RC reading 36.0 m2 named)"),
}


def face_value(f):
    """(value, kind) of one ledger face; kind in M (printed m2), R (range midpoint), F (held_from), H (hand), None."""
    if f.get("face_id") in HAND_FACE:
        return HAND_FACE[f["face_id"]][0], "H"
    if f.get("m2") is not None:
        return float(f["m2"]), "M"
    if f.get("lo") is not None and f.get("hi") is not None:
        return (float(f["lo"]) + float(f["hi"])) / 2.0, "R"
    if f.get("lo") is not None or f.get("hi") is not None:
        return float(f.get("lo") if f.get("lo") is not None else f["hi"]), "R"
    if f.get("held_from") is not None:
        return float(f["held_from"]), "F"
    return None, None


def apply_t729_bounds(rows, entries):
    """the T-729 per-line records (CAP <= x, AT_LEAST >= x, BOUND lo..hi) are the engine's newest bounds: a figure
    outside them is pulled inside (CAP exceeded -> midpoint 0..cap; AT_LEAST missed -> the floor); counted."""
    ent = {r["line_id"]: r for r in entries}
    moved = []
    for r in rows:
        e = ent.get(r["line_id"]); v = r["after"]["net"]
        if not e:
            continue
        if e["action"] == "CAP" and e.get("cap") is not None and v > float(e["cap"]) + 1e-6:
            nv = float(e["cap"]) / 2.0
            r["basis"] += f" | T-729 CAP <= {float(e['cap']):g} m2 ({e['rule']}): {v:.2f} exceeds it -> midpoint 0..cap {nv:.3f}"
        elif e["action"] == "AT_LEAST" and e.get("low") is not None and v < float(e["low"]) - 1e-6:
            nv = float(e["low"])
            r["basis"] += f" | T-729 AT_LEAST >= {nv:g} m2 ({e['rule']}): raised to the floor"
        else:
            continue
        moved.append((r["line_id"], round(v, 4), round(nv, 4)))
        r["after"]["net"] = round(nv, 6); r["label"] = "ESTIMATE"; r["method"] += "+T729_BOUND"
    return moved


def main(index_path, ledger_path, t761_path, mainfill_path, out_dir, t729_path=None):
    idx = json.load(open(index_path))
    L = [l for l in idx["lines"] if l["class"] != "EXCLUDED"]
    byid = {l["line_id"]: l for l in L}
    led = json.load(open(ledger_path))
    lines = {ln["line_id"]: ln for ln in led["lines"]}
    noline = {r["face_id"]: r for r in led["no_line"]}
    t761 = {r["line_id"]: r for r in json.load(open(t761_path))["rows"]}
    mf = {r["line_id"]: r for r in json.load(open(mainfill_path))["rows"] if r["set"] == "FORMWORK_RATIO"}

    def host_m3(h):
        """(m3, source) of a concrete host line: released net, T-761 point, else the held range midpoint."""
        H = byid.get(h)
        if H is None:
            return None, "host not in the index"
        if H["class"] == "RELEASED" and H["measured_net"] is not None:
            return float(H["measured_net"]), "released"
        r = t761.get(h)
        if r and r["after"].get("class") == "RELEASED":
            return float(r["after"]["net"]), f"T-761 {r['label']}"
        if r and r["after"].get("class") == "IGNORED_SMALL":
            return None, "T-761 IGNORED_SMALL"
        if H["held_low"] is not None:
            lo, hi = float(H["held_low"]), float(H["held_high"] if H["held_high"] is not None else H["held_low"])
            return (lo + hi) / 2.0, f"held range {lo:g}..{hi:g} midpoint"
        return None, "host concrete blank"

    fw = [l for l in L if l["item_code"] in FW_CODES]
    parse = {}
    for l in fw:
        m = re.match(r"FW:(L-[0-9a-f]{20}):(.*)$", str(l["element_id"]))
        parse[l["line_id"]] = (m.group(1), m.group(2).split(":")) if m else (None, None)
    sib = collections.defaultdict(list)
    for l in fw:
        sib[parse[l["line_id"]][0]].append(l)

    # this villa's ratio: hosts released with every formwork line released (complete), summed per element type
    acc = collections.defaultdict(lambda: [0.0, 0.0, 0])
    face_areas = collections.defaultdict(list)
    for h, ls in sib.items():
        if h is None or h not in byid:
            continue
        H = byid[h]
        if H["class"] == "RELEASED" and H["measured_net"] and all(x["class"] == "RELEASED" for x in ls):
            a = acc[H["item_code"]]; a[0] += sum(x["measured_net"] or 0 for x in ls); a[1] += H["measured_net"]; a[2] += 1
        for f in (lines.get(h) or {}).get("faces", []):
            if f.get("status") == "CALCULATED" and f.get("m2") and f["m2"] > 0:
                face_areas[H["item_code"]].append(float(f["m2"]))
    ratios = {k: (v[0] / v[1], v[2]) for k, v in acc.items() if v[1] > 0 and v[2] >= 2}
    med_face = {k: statistics.median(v) for k, v in face_areas.items() if len(v) >= 3}

    neck_m3, neck_n = 0.0, 0
    for l in L:
        if l["item_code"] == "STR.CONC.NECK":
            v, _ = host_m3(l["line_id"])
            if v is not None:
                neck_m3 += v; neck_n += 1
    rows, unresolved = [], []
    pending = []   # (line, host, known value, unknown face count, parts) for the ratio pass

    def faces_of(h, status, alt, method):
        return [f for f in (lines.get(h) or {}).get("faces", [])
                if f["status"] == status and (f.get("alternative") or "") == alt and f["method"] == method]

    def put(l, val, label, basis, method):
        prev = mf.get(l["line_id"])
        rows.append({"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"],
                     "element_id": l["element_id"],
                     "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
                     "after": {"class": "RELEASED", "net": round(val, 6)}, "label": label, "method": method,
                     "basis": basis,
                     "supersedes_main_fill": (prev["after"].get("net") if prev else None)})

    for l in fw:
        if l["class"] != "HELD":
            continue
        h, p = parse[l["line_id"]]
        eid = str(l["element_id"])
        if eid in HAND_LINE or eid.split(":", 1)[-1] in HAND_LINE:
            v, lab, chain = HAND_LINE.get(eid) or HAND_LINE[eid.split(":", 1)[-1]]
            put(l, v, lab, f"hand: {chain}", "HAND")
            continue
        if eid == "FW:FACE:R4-048":
            put(l, neck_m3 * ratios["STR.CONC.COLUMN"][0], "ESTIMATE",
                f"35 column necks: neck concrete {neck_m3:.2f} m3 ({neck_n} lines: released / T-761 / held midpoints) x "
                f"column ratio {ratios['STR.CONC.COLUMN'][0]:.2f} m2/m3 (this villa); the ledger's perimeter 52.0 m per m "
                f"of neck height (30 GF sections) needs the neck height (Q-21 datum); a bare-section P/A 13.0 would give "
                f"{neck_m3 * 13.0:.1f} m2", "RATIO")
            continue
        if l["held_low"] is not None and not (p and len(p) > 2 and p[2] == "OQ10_EARTH_CAST"):
            lo, hi = float(l["held_low"]), float(l["held_high"] if l["held_high"] is not None else l["held_low"])
            put(l, (lo + hi) / 2.0, "ESTIMATE", f"midpoint of the candidate's own held range {lo:g}..{hi:g} m2 "
                f"(engine bounds of the held faces)", "INDEX_RANGE")
            continue
        if h is None:    # untied face, or a named piece with no concrete line
            fid = str(l["element_id"]).split("FW:FACE:")[-1] if "FW:FACE:" in str(l["element_id"]) else None
            r = noline.get(fid)
            v, k = face_value(r) if r else (None, None)
            if v is not None:
                put(l, v, "ESTIMATE" if k != "M" else "DRAWING-READ",
                    f"untied face {fid} ({r.get('element')} {r.get('item','')[:70]}): "
                    + {"M": f"{v:.2f} m2 printed in the face ledger", "R": f"midpoint of {r.get('lo')}..{r.get('hi')} m2",
                       "F": f"held_from {v:.2f} m2 (lower bound)"}[k], "FACE")
            else:
                pending.append((l, None, 0.0, 1, [f"untied {fid or l['element_id']}: "
                                                  + ((r or {}).get('item') or 'no ledger row')[:70]],
                                (r or {}).get("element")))
            continue
        H = byid.get(h)
        if p[0] == "OQ10":   # FW:<host>:OQ10:<method>
            meth = p[1]
            fm = faces_of(h, "ALTERNATIVE", "OQ10_FORMED", meth)
            ec = faces_of(h, "ALTERNATIVE", "OQ10_EARTH_CAST", meth)
            vals = [face_value(f) for f in fm]
            if fm and all(v is not None for v, _ in vals):
                tot = sum(v for v, _ in vals)
                put(l, tot, "DEFAULT",
                    f"OQ-10 FORMED reading of {len(fm)} below-ground face(s) {' '.join(f['face_id'] for f in fm)[:120]} "
                    f"= {tot:.2f} m2 (contact below natural ground included: no owner rule excludes it); EARTH_CAST twin "
                    f"{sum((f.get('m2') or 0) for f in ec):.2f} m2 not added", "OQ10_FORMED")
            else:
                pending.append((l, h, 0.0, max(len(fm), 1), [f"OQ-10 alternative, no face values in the ledger"], None))
            continue
        kind, status, alt, meth = p[0], p[1], ("" if p[2] == "-" else p[2]), p[3]
        fs = faces_of(h, status, alt, meth) if kind == "FACES" else []   # SIDE = T-352 stair side rows, not T-332 faces
        if alt == "OQ10_EARTH_CAST":
            twin = faces_of(h, status, "OQ10_FORMED", meth) or faces_of(h, "ALTERNATIVE", "OQ10_FORMED", meth)
            put(l, 0.0, "DEFAULT",
                f"EARTH_CAST twin of {len(fs)} held face(s) {' '.join(f['face_id'] for f in fs)[:100]}: the FORMED reading "
                f"is adopted on its own line ({len(twin)} face(s)), so this alternative carries no form (never summed)",
                "OQ10_EARTH_CAST_NOT_ADOPTED")
            continue
        if not fs:
            pending.append((l, h, 0.0, 1, [f"{kind}:{status}:{alt or '-'}:{meth} not in the face ledger (re-measured after T-332)"], None))
            continue
        known, unk, kinds, parts = 0.0, 0, collections.Counter(), []
        for f in fs:
            v, k = face_value(f)
            if v is None:
                unk += 1
            else:
                known += v; kinds[k] += 1
        if unk == 0:
            lab = "ESTIMATE" if (kinds["R"] or kinds["F"] or kinds["H"] or (H and H["class"] != "RELEASED")) else "DRAWING-READ"
            put(l, known, lab,
                f"{len(fs)} face(s) {' '.join(f['face_id'] for f in fs)[:120]} = {known:.2f} m2 "
                f"(printed {kinds['M']}, range midpoint {kinds['R']}, held_from lower bound {kinds['F']}, hand {kinds['H']}; face ledger T-332)"
                + "".join(f"; {f['face_id']}: {HAND_FACE[f['face_id']][2]}" for f in fs if f['face_id'] in HAND_FACE)
                + (f"; host {H['item_code']} is {H['class']}" if H and H["class"] != "RELEASED" else ""), "FACE")
        else:
            pending.append((l, h, known, unk, [f"{len(fs) - unk} face(s) valued {known:.2f} m2, {unk} face(s) with no value: "
                                               + "; ".join((f.get('item') or '')[:50] for f in fs if face_value(f)[0] is None)[:160]], None))

    # ratio pass: host total by this villa's ratio minus everything else the host already carries
    done = {r["line_id"]: r["after"]["net"] for r in rows}
    by_host_pending = collections.defaultdict(list)
    for t in pending:
        by_host_pending[t[1]].append(t)
    for h, items in by_host_pending.items():
        H = byid.get(h) if h else None
        m3, src = host_m3(h) if h else (None, "no concrete line")
        typ = H["item_code"] if H else None
        others = 0.0
        if h:
            for x in sib[h]:
                if x["class"] == "RELEASED":
                    others += x["measured_net"] or 0
                elif x["line_id"] in done:
                    others += done[x["line_id"]]
        nunk = sum(t[3] for t in items)
        known_here = sum(t[2] for t in items)
        resid = None
        if m3 is not None and typ in ratios:
            resid = m3 * ratios[typ][0] - others - known_here
        for (l, _, known, unk, parts, elem) in items:
            etyp = typ or ({"FOOTING": "STR.CONC.FOOTING", "PARAPET": "STR.CONC.PARAPET", "LIFT": "STR.CONC.LIFT",
                            "COLUMN": "STR.CONC.COLUMN", "BEAM": "STR.CONC.BEAM", "GROUND_BEAM": "STR.CONC.GROUND_BEAM",
                            "SLAB": "STR.CONC.SLAB", "STAIR": "STR.CONC.STAIR"}.get(str(elem or "").upper()))
            if resid is not None and resid > 0:
                v = known + resid * unk / nunk
                put(l, v, "ESTIMATE",
                    f"{parts[0][:200]} | ratio fallback: host {typ} {h} {m3:.3f} m3 ({src}) x {ratios[typ][0]:.2f} m2/m3 "
                    f"(this villa, {ratios[typ][1]} complete hosts) = {m3 * ratios[typ][0]:.2f} m2 - {others + known_here:.2f} m2 "
                    f"already on the host's lines = {resid:.2f} m2 shared by {unk}/{nunk} unvalued face(s)", "RATIO")
            elif etyp in med_face:
                v = known + med_face[etyp] * unk
                why = (f"host residual {resid:.2f} m2 not positive" if resid is not None else
                       f"no host ratio ({src}{'' if typ in ratios else ', no ratio for ' + str(typ)})")
                put(l, v, "ESTIMATE",
                    f"{parts[0][:200]} | {why}: {unk} face(s) x median released face of {etyp} {med_face[etyp]:.2f} m2 "
                    f"(this villa)", "MEDIAN_FACE")
            else:
                unresolved.append({"line_id": l["line_id"], "element_id": l["element_id"], "why": parts[0][:200],
                                   "host": h, "host_m3": m3, "host_src": src})

    t729_moved = apply_t729_bounds(rows, json.load(open(t729_path))["entries"]) if t729_path else []
    os.makedirs(out_dir, exist_ok=True)
    held = [l for l in fw if l["class"] == "HELD"]
    by_label = collections.Counter(r["label"] for r in rows)
    by_meth = collections.Counter(r["method"] for r in rows)
    sum_new = sum(r["after"]["net"] for r in rows)
    sup = [r for r in rows if r["supersedes_main_fill"] is not None]
    rel = sum(l["measured_net"] or 0 for l in fw if l["class"] == "RELEASED")
    summary = {"held_formwork_lines": len(held), "filled": len(rows), "still_blank": len(unresolved),
               "by_label": dict(by_label), "by_method": dict(by_meth),
               "released_m2_before": round(rel, 2), "filled_m2": round(sum_new, 2),
               "formwork_total_after_m2": round(rel + sum_new, 2),
               "main_fill_rows_superseded": len(sup),
               "main_fill_m2_on_those_lines": round(sum(r["supersedes_main_fill"] for r in sup), 2),
               "t762_m2_on_those_lines": round(sum(r["after"]["net"] for r in sup), 2),
               "pulled_inside_t729_bounds": len(t729_moved)}
    out = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-762", "candidate_version": idx.get("candidate_version"),
           "inputs": {"index": os.path.basename(index_path), "face_ledger": os.path.basename(ledger_path),
                      "t761": os.path.basename(t761_path), "main_fill": os.path.basename(mainfill_path)},
           "ratios_m2_per_m3": {k: {"ratio": round(v[0], 3), "complete_hosts": v[1]} for k, v in sorted(ratios.items())},
           "median_released_face_m2": {k: round(v, 3) for k, v in sorted(med_face.items())},
           "summary": summary, "rows": rows, "unresolved": unresolved}
    json.dump(out, open(os.path.join(out_dir, "FIX_ROWS.json"), "w"), indent=1)
    md = [f"# T-762 formwork fix rows on {idx.get('candidate_version')} (DEFAULT / ESTIMATE / DRAWING-READ; never verified)", "",
          "```", json.dumps(summary, indent=1), "```", "",
          "Ratios (complete released hosts): " + ", ".join(f"{k.split('.')[-1]} {v[0]:.2f} m2/m3 ({v[1]})" for k, v in sorted(ratios.items())), "",
          "| line | item | before | after m2 | label | method | MAIN_FILL | basis |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]
        md.append(f"| {r['line_id']} | {r['item_code']} | {b['class']}{(' ' + str(b['low']) + '..' + str(b['high'])) if b['low'] is not None else ''} "
                  f"| {r['after']['net']:.2f} | {r['label']} | {r['method']} | {'' if r['supersedes_main_fill'] is None else round(r['supersedes_main_fill'], 2)} | {r['basis'][:220]} |")
    md += ["", "## Still blank"] + [f"- {u['line_id']} {u['element_id']}: {u['why']}" for u in unresolved]
    open(os.path.join(out_dir, "FIX_ROWS.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps(summary, indent=1))
    print(json.dumps(out["ratios_m2_per_m3"]))
    return out


if __name__ == "__main__":
    main(*sys.argv[1:7])
