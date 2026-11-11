"""T-693: the URBAN_V3070_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.70 (engine.source.arch_v3070), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t689/out/T689_HELD_RANGES.json  T-689 (MERGED 66ffd421, Verifier 2026-11-11 04:55 Gate A PASS, own
      Drive read of the structural DXF): R-T689-1 (2F roof slab top >= 12.937 at the B8 supports 412 / 415: L-919a5749
      low 0.303 -> 0.3287) and the five blank CONFLICT columns bounded (annex trio + annex C3 on R-T678-2, 2F C5 415
      on R-T689-1);
  research/agents_t688/out/T688_STATEMENT.json   T-688 (MERGED a62b3024, Verifier 2026-11-11 01:56 Gate A PASS, own
      FR08 noding): F-V-P18-2 / R-T688-3: L-a7ab57d8 is GROUND SLAB (B10-05), its region label BEAM_STRIP is wrong;
  research/agents_t678/out/T678_LEDGER.json      T-678 (MERGED f8515d4b; via research/agents_t682/t682_inputs.py, its
      pins unchanged): the annex slab-top plane record (R-T678-2 / R-T682-1, ONE_PLANE, s_lo 3.544);
  research/agents_t687/out/LINE_INDEX_V3_0_69.json  T-687 (Gate B PASS, MERGED 12bf5b8c): the class and range each
      line carries on the candidate V3.0.69 7ea65f9b (the binding; asserted again on the live run).

Every bound is RE-DERIVED here from its terms (section readings parsed from the ledger's own source text, base, top
datums) and refused when it differs from the ledger; the module recomputes it once more at wiring time.
Typed here are only the questions (designer items the ledger names; ERS s.2.7 not met: no owner question) and the
facts of R-T689-1 the ledger states in its b8_bound record.

    python3 -I research/agents_t693/t693_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t682", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t682_inputs as I82  # noqa: E402  (T-682, merged: the annex plane record from the pinned T-678 ledger)

T689 = ROOT / "research/agents_t689/out/T689_HELD_RANGES.json"
T688 = ROOT / "research/agents_t688/out/T688_STATEMENT.json"
INDEX = ROOT / "research/agents_t687/out/LINE_INDEX_V3_0_69.json"
S682 = ROOT / "research/agents_t682/summary_t682.json"      # the V3.0.67 STR.CONC code totals (unchanged by .68 / .69)
PINS = {T689: "2c9bf8ff49f0ea9c91bd290746315e24a7e978b52db90f64bc87de3d2d8456f7",
        T688: "c790f56a68afa653b36946125750679dff0ff25dd6c5344632611bd4c70e9ff4",
        INDEX: "e908a5f105197d44277c8e1d2a2ef79c67b45681ca874d8c405e85d3b97602f1",
        S682: "5e4e852e468a547ade8b9ae9075f28e2376ab4ffcddc759aa3c7999a08221774"}
C689 = ("Verifier 2026-11-11 04:55 (Gate A PASS, run session_01E6cPnbaQxGo5z2sdX4XzTJ: own Drive read of the structural "
        "DXF: B8 span / width / depth 20x75 / support outlines / column schedule sizes AGREE item by item; W28 / W29 "
        "heads from T-201 (merged) as a source reference; L-919a5749 0.3287 .. 0.425 AGREE; five blank columns "
        "1.38278 .. 2.23125 m3 AGREE; plate transfer refused (F-T689-1))")
C688 = ("Verifier 2026-11-11 01:56 (Gate A PASS, run session_01E6cPnbu8b82qwGYJBemCMC: own FR08 noding: face 0.950 x "
        "1.200 = 1.140 m2 with its own '+0.30', four 0.30 m neighbour strips: GROUND SLAB B10-05 CONFIRMED, line "
        "0.114 m3 right, detector label BEAM_STRIP wrong)")
SOURCES = {
    "T-689": {"task": "T-689", "file": "research/agents_t689/out/T689_HELD_RANGES.json", "sha256": PINS[T689],
              "merge_commit": "66ffd421", "checker_run": C689},
    "T-688": {"task": "T-688", "file": "research/agents_t688/out/T688_STATEMENT.json", "sha256": PINS[T688],
              "merge_commit": "a62b3024", "checker_run": C688},
    "T-678": dict(I82.SOURCES["T-678"])}
SCHEMA = "URBAN_V3070_INPUTS_V1"
COLUMN = "STR.CONC.COLUMN"
C2_412 = "L-919a5749ef79759e01ca"
C5_415 = "L-bc01297b1c4a4c45a15f"
SLAB = "L-a7ab57d873e26a587fd9"
LABEL_PATH = "location.region_label"          # set from the live line read (see LABEL_FROM)
LABEL_FROM, LABEL_TO = "BEAM_STRIP", "GROUND_SLAB"
BASE_2F, CEIL_2F = "9.65", "13.90"
BASE_ANNEX = "0.25"
Q_SECTION = ("D-66 (section, F-T689-3: this outline is not yet in D-66's registered list): drawn outline vs schedule "
             "band, CONFLICT PRINTED_VS_DRAWN (T-217); owner X6 / Q-61 C: never settled by picking the printed one "
             "(designer)")
Q_2F_TOP = ("D-39: the 2F roof slab top is not printed (finished +13.90 only); lower end from the drawn W28 head under "
            "the printed B8 at its support (R-T689-1) (designer)")
Q_ANNEX = ("Q-54 B / D-39: the annex roof slab top is not printed (finished +4.30 only); lower end 3.544 from the drawn W08 "
           "head under CB6 on one plane (R-T678-2 / R-T682-1) (designer)")
SEC_RE = re.compile(r"outline (\w+) (\d+)x(\d+) mm vs schedule (.+?) (\d+)x(\d+) cm")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _d(x):
    return Decimal(str(x))


def _q6(x):
    return Decimal(x).quantize(Decimal("0.000001"))


def _load():
    for p, s in PINS.items():
        if s and _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (T689, T688, INDEX, S682))


def readings(source):
    """'outline 34A 200x400 mm vs schedule C GR 20x50 cm' -> the two readings in metres (both kept: CONFLICT)."""
    m = SEC_RE.search(source)
    if not m:
        raise SystemExit(f"no section readings in {source!r}")
    h, b1, d1, row, b2, d2 = m.groups()
    return [{"source": f"drawn outline {h} (mm)", "b_m": float(_d(b1) / 1000), "d_m": float(_d(d1) / 1000)},
            {"source": f"schedule {row} (cm)", "b_m": float(_d(b2) / 100), "d_m": float(_d(d2) / 100)}]


def b8_joint(b8):
    """the R-T689-1 datum record from the ledger's own b8_bound fields."""
    if b8["plate_transfer"]["state"] != "REFUSED":
        raise SystemExit("b8_bound: the plate transfer is expected REFUSED (F-T689-1)")
    heads = [{"id": h["id"], "head_abs_m": float(h["head_abs"]), "tol_m": float(h["tol"]), "status": h["status"],
              "at_m": h["at"]} for h in b8["heads"]]
    dep = _d(b8["depth_m"])
    s_lo = max(_d(h["head_abs"]) - _d(h["tol"]) for h in b8["heads"]) + dep
    if s_lo != _d(b8["s_lo"]):
        raise SystemExit(f"b8 slab top {s_lo} is not the ledger's {b8['s_lo']}")
    return {"kind": "BEAM_JOINT", "rule": "R-T689-1 1.0.0", "beam": "B8 2F", "heads": heads,
            "beam_depth_m": float(dep), "depth_source": "printed schedule row (W 20, H 75)",
            "supports": sorted(b8["supports"]), "governing": b8["governing"], "clear_span_m": float(b8["clear_span_m"]),
            "plate_transfer": b8["plate_transfer"]}


def _expect(ix):
    return {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
            "low": ix["held_low"], "high": ix["held_high"]}


def _height(base, datum_lo, ceil, what, h_lo, h_hi, status):
    return {"base_m": float(_d(base)), "base_status": status, "datum_lo": datum_lo,
            "datum_hi": {"kind": "CEILING", "mark_abs_m": float(_d(ceil)), "what": what},
            "h_lo_m": float(h_lo), "h_hi_m": float(h_hi)}


def _hand(rs, h_lo, h_hi):
    a = sorted(_d(r["b_m"]) * _d(r["d_m"]) for r in rs)
    return _q6(a[0] * _d(h_lo)), _q6(a[-1] * _d(h_hi))


def build(project_id=None):
    t689, t688, index, s682 = _load()
    ix = {r["line_id"]: r for r in index["lines"]}
    if t689["candidate"] != "ARCH_TAKEOFF_V3.0.67" or index["candidate_version"] != "ARCH_TAKEOFF_V3.0.69":
        raise SystemExit("candidate versions moved")
    led82, _ix66, _s677 = I82._load()
    plane = I82.annex_plane(led82)
    joint = b8_joint(t689["b8_bound"])
    s_lo = _d(t689["b8_bound"]["s_lo"])
    ents = []

    # NARROW: L-919a5749 (C2 2F at 412), the one range T-689 moved
    mv = [r for r in t689["lines"] if r["before"] != r["after"]]
    if [r["line_id"] for r in mv] != [C2_412]:
        raise SystemExit(f"T-689 moved {[r['line_id'] for r in mv]}, expected only {C2_412}")
    r = mv[0]
    rs = [{"source": "schedule C2 2ND (cm) = drawn SFRS 412", "b_m": 0.20, "d_m": 0.50}]
    h_lo, h_hi = s_lo - _d(BASE_2F), _d(CEIL_2F) - _d(BASE_2F)
    lo, hi = _hand(rs, h_lo, h_hi)
    if (lo, hi) != (_d(r["after"][0]), _d(r["after"][1])) or _d(r["before"][1]) != hi:
        raise SystemExit(f"{C2_412}: hand {lo} .. {hi} is not the ledger's {r['after']}")
    ents.append({"action": "NARROW", "line_id": C2_412, "source_tasks": ["T-689"], "member": r["member"],
                 "member_mark": "412", "expect": _expect(ix[C2_412]), "readings": rs,
                 "height": _height(BASE_2F, joint, CEIL_2F, "2F roof finished mark (D-39 ceiling)", h_lo, h_hi,
                                   "APPROVED"),
                 "after": {"low": float(lo), "high": float(hi)}, "ends_moved": ["low"],
                 "items": ["D-39"], "question": Q_2F_TOP,
                 "basis": f"R-T689-1: 0.10 m2 x ({s_lo} - {BASE_2F}) .. ({CEIL_2F} - {BASE_2F}) = {lo} .. {hi} m3",
                 "status": {"low_end": "DRAWING-CONFIRMED", "high_end": "HELD",
                            "basis": "low: W28 head under printed B8 at its support 412 (Checker AGREE); high: D-39"}})

    # BOUND: the five blank CONFLICT columns
    btb = t689["blank_to_bounded"]
    for r in btb["lines"]:
        rs = readings(r["source"])
        mark = SEC_RE.search(r["source"]).group(1)
        if r["line_id"] == C5_415:
            dl, base, ceil, what, st, q = joint, BASE_2F, CEIL_2F, "2F roof finished mark (D-39 ceiling)", "APPROVED", \
                Q_2F_TOP
            items = ["D-66", "D-39"]
            hb = "low: B8 joint (R-T689-1); high: D-39"
        else:
            dl = {"kind": "PLANE", "rule": "R-T678-2 1.0.0", "plane": plane}
            base, ceil, what, st, q = BASE_ANNEX, plane["finished_ceiling_m"], "annex roof finished mark +4.30", \
                "APPROVED", Q_ANNEX
            items = ["D-66", "Q-54 B / D-39"]
            hb = "low: W08 head under CB6 on one plane (R-T678-2, Checker-verified); high: finished +4.30"
        top = s_lo if dl["kind"] == "BEAM_JOINT" else _d(plane["s_lo_m"])
        h_lo, h_hi = top - _d(base), _d(str(ceil)) - _d(base)
        if [str(h_lo), str(h_hi)] != [str(_d(x)) for x in r["height_m"]] and \
                [float(h_lo), float(h_hi)] != [float(x) for x in r["height_m"]]:
            raise SystemExit(f"{r['line_id']}: height {h_lo} .. {h_hi} is not the ledger's {r['height_m']}")
        lo, hi = _hand(rs, h_lo, h_hi)
        if (lo, hi) != (_d(r["after"][0]), _d(r["after"][1])):
            raise SystemExit(f"{r['line_id']}: hand {lo} .. {hi} is not the ledger's {r['after']}")
        if ix[r["line_id"]]["class"] != "HELD" or ix[r["line_id"]]["held_low"] is not None:
            raise SystemExit(f"{r['line_id']}: not HELD blank on V3.0.69")
        ents.append({"action": "BOUND", "line_id": r["line_id"], "source_tasks": ["T-689"] + (
                         [] if dl["kind"] == "BEAM_JOINT" else ["T-678"]),
                     "member": r["member"], "member_mark": mark, "expect": _expect(ix[r["line_id"]]), "readings": rs,
                     "height": _height(base, dl, ceil, what, h_lo, h_hi, st),
                     "after": {"low": float(lo), "high": float(hi)}, "items": items,
                     "question": f"{Q_SECTION}; {q}"[:400],
                     "basis": f"conflict bound: {r['source']}: min area x {h_lo} .. max area x {h_hi} = {lo} .. {hi} m3",
                     "status": {"low_end": "DRAWING-CONFIRMED", "high_end": "HELD", "basis": hb}})
    tot = sum(_d(e["after"]["low"]) for e in ents if e["action"] == "BOUND"), \
        sum(_d(e["after"]["high"]) for e in ents if e["action"] == "BOUND")
    if tot != (_d(btb["low"]), _d(btb["high"])):
        raise SystemExit(f"blank-to-bounded {tot} is not the ledger's {btb['low']} .. {btb['high']}")

    # RELABEL: the T-688 F-V-P18-2 face
    f = t688["f_v_p18_2"]
    if f["line"] != SLAB or f["owner"]["owner"] != "GROUND_SLAB" or not f["band_pairing_refused"]:
        raise SystemExit("T-688 F-V-P18-2 record moved")
    x = ix[SLAB]
    ents.append({"action": "RELABEL", "line_id": SLAB, "source_tasks": ["T-688"],
                 "member": "GF ground-slab face 0.95 x 1.20 with its own +0.30 (four 0.30 m member strips around it)",
                 "expect": {"item_code": x["item_code"], "element_id": x["element_id"], "unit": x["unit"],
                            "class": x["class"], "value": x["measured_net"]},
                 "label": {"path": LABEL_PATH, "from": LABEL_FROM, "to": LABEL_TO},
                 "ruling": "R-T688-3 1.0.0 (a) / (c): a face with its own level mark is slab; BAND0042 pairing two "
                           "panel edges 0.95 apart is refused as a member (Checker F-V-P18-2 CLOSED)",
                 "basis": f"{f['verdict']}; quantity {x['measured_net']} m3 unchanged"})
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
            "index_sha256": PINS[INDEX], "expect_totals": expect_totals(s682, ents),
            "not_wired": [
                {"what": "plate-wide transfer of the B8 joint bound (+0.133640 m3 on C9 418, C2 41B / 41E, C1 421, "
                         "PC-2F lows)", "task": "T-689", "why": "REFUSED (F-T689-1): needs the Lead's ruling"},
                {"what": "2F tank columns C2 40F / C3 424", "task": "T-689", "why": "D-44: stay HELD blank"},
                {"what": "STR.FORMWORK of the six restated columns", "task": "-",
                 "why": "not re-derived here: HELD blank"}]}


def expect_totals(s682, ents):
    """the V3.0.67 STR.CONC.COLUMN totals (T-682 run of record; V3.0.68 / .69 moved no concrete line) + this
    restatement, by hand: released unchanged; a BOUND line adds its range and leaves the blank count; a NARROW line
    adds its moved end."""
    t = s682["b10_code_totals"][f"{COLUMN}|m3"]["v3_0_67"]
    b = [e for e in ents if e["action"] == "BOUND"]
    n = [e for e in ents if e["action"] == "NARROW"]
    lo = _d(t["held_low"]) + sum(_d(e["after"]["low"]) for e in b) + \
        sum(_d(e["after"]["low"]) - _d(e["expect"]["low"]) for e in n)
    hi = _d(t["held_high"]) + sum(_d(e["after"]["high"]) for e in b) + \
        sum(_d(e["after"]["high"]) - _d(e["expect"]["high"]) for e in n)
    return {f"{COLUMN}|m3": {"released": t["released"], "lines": t["lines"],
                             "bounded_lines": t["bounded_lines"] + len(b), "blocked_lines": t["blocked_lines"] - len(b),
                             "held_low": float(lo), "held_high": float(hi)}}


def summary(doc):
    from collections import Counter
    c = Counter((e["expect"]["item_code"], e["action"]) for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_code_action": {f"{k[0]} {k[1]}": v for k, v in sorted(c.items())},
            "rows": [(e["action"], e["line_id"], e.get("after"), e.get("label")) for e in doc["entries"]],
            "expect_totals": doc["expect_totals"], "not_wired": doc["not_wired"]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
