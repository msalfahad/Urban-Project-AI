"""T-527 effect builder (research only): what the LINTEL_BEARING_V2 / V3 DXF re-run changes downstream, computed by the
MERGED rule code on substituted ends (nothing hand-typed):

  - R-T516-1 jamb census (research/agents_t516/t516_jamb_bearing.census): end state, bearing upper bound, lintel state,
    length ceiling, links ceiling, straight bar ceiling, precast beside fit;
  - R-T519-1 lintel pieces (research/agents_t519/t519_lintel_pieces.census): system, PRODUCED / HELD, RC length bounds,
    precast beside piece and fit;
  - R-T524-1 end-zone ownership (research/agents_t524/t524_lintel_end_ownership.assess_set): the deficit-set concrete
    lo / hi, removed, inside-column, lintel-on-lintel, not-built (m3).

Basis V1 = the merged T-516 evidence (committed, sha-pinned there). V2 and V3 = research/agents_t527/out/
JAMB_EVIDENCE_V3_T527.csv (sha-pinned here; produced from the DXF by t527_extract.py). The merged modules are imported
read-only and never edited; their own committed outputs are not rewritten (T-524's builder is pointed at temporary copies).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, HERE.parent / "agents_t516", HERE.parent / "agents_t519", HERE.parent / "agents_t524"):
    sys.path.insert(0, str(p))
import t516_jamb_bearing as T516  # noqa: E402  (read only)
import t519_lintel_pieces as T519  # noqa: E402  (read only)
import t524_lintel_end_ownership as T524  # noqa: E402  (read only)

EVIDENCE = HERE / "out" / "JAMB_EVIDENCE_V3_T527.csv"
EVIDENCE_SHA = "7ac6e6b93d2a4ac9e7dab3ff0db70d988a256a972b8bb7fb8a139360a43c2ee2"
OUT = HERE / "out" / "EFFECT_T527.json"
FIELDS = ("available_m", "own_band_m", "stopper", "stopper_id", "beyond_band_end", "search_capped")


class EffectError(ValueError):
    pass


def evidence():
    b = EVIDENCE.read_bytes()
    if hashlib.sha256(b).hexdigest() != EVIDENCE_SHA:
        raise EffectError(f"{EVIDENCE.name}: sha256 differs from the pinned file (edited evidence)")
    return list(csv.DictReader(io.StringIO(b.decode("utf-8"))))


def basis_ends(basis):
    """{(opening, side): end fields} for basis 'V2' or 'V3' from the committed DXF re-run."""
    out = {}
    for r in evidence():
        if basis == "V3":
            x = {k: r[k] for k in FIELDS}
        elif basis == "V2":
            # V2 changes reach and stopper only; own-band part / junction class follow the reach as in T-516
            x = {"available_m": r["v2_available_m"], "stopper": r["v2_stopper"], "stopper_id": r["v2_stopper_id"],
                 "search_capped": "YES" if r["v2_stopper"] == "SEARCH_LIMIT" else ""}
            x["own_band_m"] = r["own_band_m"] if r["v2_available_m"] == r["available_m"] else \
                f"{min(float(r['v2_available_m']), float(r['own_band_m'])):.3f}"
            x["beyond_band_end"] = r["beyond_band_end"]
        else:
            raise EffectError(f"unknown basis {basis!r}")
        out[(r["opening_id"], r["side"])] = x
    return out


def records(basis):
    """the merged T-516 records with every end's measured fields replaced by the basis (V1 = unchanged)."""
    recs = T516.records()
    if basis == "V1":
        return recs
    ends = basis_ends(basis)
    t453 = {r["opening_id"] for r in recs}
    for rec in recs:
        new = []
        for e in rec["ends"]:
            k = (rec["opening_id"], e["side"])
            if k not in ends:
                raise EffectError(f"{k}: no {basis} end in the DXF re-run")
            new.append(dict(e, **ends[k]))
        rec["ends"] = new
        for e in new:
            if e["stopper"] == "OPENING" and e["stopper_id"] not in t453:
                rec["neighbour_decisions"][e["stopper_id"]] = "NOT_A_LEDGER_OPENING"
    if len(ends) != sum(len(r["ends"]) for r in recs):
        raise EffectError("the DXF re-run and the census differ in their ends")
    return recs


def census(basis):
    return T516.census(records(basis), T516.b_min_printed())


def t519_census(doc516):
    """R-T519-1 on the T-516 rows of one basis (T-519's own end mapping, read from its training_records)."""
    t516 = {r["opening_id"]: r for r in doc516["rows"]}
    recs = []
    for rec in T519.training_records():
        if rec["decision"] == "REQUIRED":
            ids = {x["opening_id"] for x in T519.training_records()}
            ends = []
            for e in t516[rec["opening_id"]]["ends"]:
                a = None if e["state"] == T516.HELD else e.get("available_trusted_m")
                shared = e["stopper_id"] if e["stopper"] == "OPENING" and e["stopper_id"] in ids else None
                capped = "YES" if (e["state"] == T516.BOUNDED and e.get("bearing_hi_m") is None) else ""
                ends.append({"side": e["side"], "available_m": a, "shared_with": shared,
                             "stopper": e["stopper"] if e["stopper"] != "OPENING" or shared else "END_OF_MASONRY",
                             "capped": capped, "t516_state": e["state"]})
            rec = dict(rec, ends=ends)
        recs.append(rec)
    return T519.census(recs, T519.training_schedule())


def t524_summary(doc516, ev_rows):
    """R-T524-1 on the T-516 rows of one basis, through temporary copies (the committed files are never touched)."""
    old = (T524.T516, T524.T516_EV)
    with tempfile.TemporaryDirectory() as d:
        j, c = Path(d) / "t516.json", Path(d) / "ev.csv"
        j.write_text(json.dumps(doc516), encoding="utf-8")
        with open(c, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["opening_id", "side", "through_walls"], lineterminator="\n",
                               extrasaction="ignore")
            w.writeheader()
            w.writerows(ev_rows)
        try:
            T524.T516, T524.T516_EV = j, c
            lintels, pairs = T524.villa_inputs()
            return T524.assess_set(lintels, pairs)["summary"]
        finally:
            T524.T516, T524.T516_EV = old


def _lintel_view(r):
    return {"state": r["state"], "length_lo_m": r.get("length_lo_m"), "length_hi_m": r.get("length_hi_m"),
            "links_lo": r.get("links_lo"), "links_hi": r.get("links_hi"),
            "straight_ceiling_kg": None if r.get("straight_ceiling_kg") is None else round(r["straight_ceiling_kg"], 6),
            "precast_beside_fit": r["precast_beside"].get("fit_on_measured_piers"),
            "ends": {e["side"]: {"state": e["state"], "available_m": e.get("available_m"),
                                 "bearing_hi_m": e.get("bearing_hi_m"), "stopper": e["stopper"]} for e in r["ends"]}}


def _t519_view(r):
    rc = r.get("rc") or {}
    pb = r.get("precast_beside") or {}
    return {"system": r.get("system"), "state": r["state"], "rc_length_lo_m": rc.get("length_lo_m"),
            "rc_length_hi_m": None if rc.get("length_hi_m") is None else float(rc["length_hi_m"]),
            "precast_beside_piece_m": pb.get("piece_m"), "precast_beside_fit": pb.get("fit")}


def diff(a, b, path=""):
    """flat list of (path, before, after) where two nested views differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k), b.get(k), f"{path}.{k}" if path else str(k))
        return out
    return [] if a == b else [(path, a, b)]


def build():
    ev = evidence()
    ev1 = list(csv.DictReader((ROOT / "research/agents_t516/out/JAMB_EVIDENCE_T516.csv").open(encoding="utf-8")))
    docs = {b: census(b) for b in ("V1", "V2", "V3")}
    views = {b: {r["opening_id"]: _lintel_view(r) for r in d["rows"]} for b, d in docs.items()}
    t519 = {b: {r["opening_id"]: _t519_view(r) for r in t519_census(d)["rows"] if r["decision"] == "REQUIRED"}
            for b, d in docs.items()}
    t524 = {"V1": t524_summary(docs["V1"], ev1), "V2": t524_summary(docs["V2"], ev), "V3": t524_summary(docs["V3"], ev)}
    ends = []
    for r in ev:
        if r["v1_available_m"] != r["v2_available_m"] or r["v2_available_m"] != r["available_m"] or \
                r["v1_stopper"] != r["v2_stopper"] or r["v2_stopper"] != r["stopper"]:
            ends.append({"opening_id": r["opening_id"], "side": r["side"],
                         "v1": [float(r["v1_available_m"]), r["v1_stopper"]],
                         "v2": [float(r["v2_available_m"]), r["v2_stopper"]],
                         "v3": [float(r["available_m"]) if r["available_m"] else None, r["stopper"], r["stopper_id"]],
                         "v1_to_v2_m": round(float(r["v2_available_m"]) - float(r["v1_available_m"]), 3),
                         "v2_to_v3_m": float(r["v2_to_v3_m"]) if r["v2_to_v3_m"] else None})
    step = {}
    for a, b in (("V1", "V2"), ("V2", "V3")):
        step[f"{a}_to_{b}"] = {
            "t516": {oid: diff(views[a][oid], views[b][oid]) for oid in views[a] if diff(views[a][oid], views[b][oid])},
            "t519": {oid: diff(t519[a][oid], t519[b][oid]) for oid in t519[a] if diff(t519[a][oid], t519[b][oid])},
            "t524": diff(t524[a], t524[b])}
    return {"rule": "R-T527-1 (LINTEL_BEARING_V3)", "changed_ends": ends, "steps": step,
            "summary": {b: docs[b]["summary"] for b in docs}, "t524_summary": t524,
            "t519_rc_produced": {b: sorted(k for k, v in t519[b].items() if v["state"] == "PRODUCED") for b in t519},
            "sources": {str(EVIDENCE.relative_to(ROOT)): EVIDENCE_SHA},
            "drawing": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55), numbers only"}


def render(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n"
