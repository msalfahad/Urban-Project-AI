"""T-326 r2 (D-T326-1): the ARCHED-opening reveal correction ledger, a separate file beside the merged T-313 r2 ledger
(which is never edited). Rule R-T326-2 (every villa): the reveal of an arched or curved-head opening is
2 x d x springing height (jambs, from the sill / floor to the springing) + d x developed arch length (the head soffit
follows the arch), never the enclosing / band-crown rectangle (2 x d x crown + d x width).

Built ONLY from two merged, Checker-verified files, each pinned by sha256:

  research/agents_t313/REVEAL_LEDGER_T313.csv   T-313 r2 (MERGED 5f2bf0d5): the depth d per opening / side and the
      rectangle rows being replaced (their m2 / basis are carried in the correction as 'ledger_*', so a later edit of
      either file stops the build);
  research/agents_t238/summary.json             T-238 (MERGED 242e50b2, Verifier 2026-10-23 22:50 UTC Gate A PASS):
      the opening-line outline of each arched opening (width, springing, crown, developed arch length, status).

Only openings whose T-238 outline is DRAWING-CONFIRMED and whose T-313 OUTSIDE jambs / head are MEASURED are corrected
(W15, W16, W26); a held outline (W17 curved on plan, A-GF-01 pending, A-1F-01 not drawn) stays held in its own lines.

    python3 -I research/agents_t326/build_arched_correction.py          # rewrites the CSV (deterministic)
    python3 -I research/agents_t326/build_arched_correction.py --check  # exit 1 if the CSV is not the built one
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LED = ROOT / "research/agents_t313/REVEAL_LEDGER_T313.csv"
T238 = ROOT / "research/agents_t238/summary.json"
OUT = HERE / "ARCHED_REVEAL_CORRECTION_T326.csv"
PINS = {LED: "2cfa42112aa470c8792d4abe07c9b7471ceecd526974dcd2276dacbff5598730",
        T238: "84b5b1f8c368ef8f051c1577c9656537d969e0261377c8a849b122d9d2fda438"}
T238_MERGE = "242e50b2"
T238_RUN = "Verifier 2026-10-23 22:50 UTC: T-238 Gate A PASS, MERGED 242e50b2 (arched openings on the opening line)"
COLUMNS = ("opening", "side", "component", "depth_m", "spring_m", "arch_length_m", "width_m", "crown_m", "m2", "ml",
           "basis", "ledger_m2", "ledger_ml", "ledger_basis", "outline_task", "outline_merge", "outline_status",
           "rule_id")
RULE_ID = "R-T326-2"
NDP = 6


class PinError(ValueError):
    pass


def _read(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise PinError(f"{p.name}: sha256 {h[:12]} is not the merged file {PINS[p][:12]}")
    return b.decode("utf-8")


def _g(x):
    """a figure as the ledger writes it: shortest round-trip text of the value rounded to 6 dp."""
    return repr(round(float(x), NDP))


def rows():
    led = list(csv.DictReader(io.StringIO(_read(LED))))
    outl = json.loads(_read(T238))["outlines"]
    out = []
    for op in sorted(outl):
        o = outl[op]
        if o.get("status") != "DRAWING-CONFIRMED":
            continue
        for k in ("spring_m", "arch_length_m", "width_m", "crown_m"):
            if not isinstance(o.get(k), (int, float)) or o[k] <= 0:
                raise PinError(f"{op}: T-238 outline {k} missing")
        if not o["spring_m"] < o["crown_m"]:
            raise PinError(f"{op}: springing {o['spring_m']} is not below the crown {o['crown_m']} (not an arch)")
        for side in ("IN", "OUT"):
            jh = {r["component"]: r for r in led if r["opening"] == op and r["side"] == side
                  and r["component"] in ("JAMBS", "HEAD")}
            if not jh or all(r["state"] == "NONE" for r in jh.values()):
                continue
            if set(jh) != {"JAMBS", "HEAD"} or any(r["state"] != "MEASURED" for r in jh.values()):
                raise PinError(f"{op} {side}: jambs / head not both MEASURED in T-313 ({[r['state'] for r in jh.values()]})")
            d = float(jh["JAMBS"]["depth_m"])
            if abs(float(jh["HEAD"]["depth_m"]) - d) > 1e-9 or d <= 0:
                raise PinError(f"{op} {side}: jamb / head depths differ")
            s, a = float(o["spring_m"]), float(o["arch_length_m"])
            for comp, m2, ml, basis in (
                    ("JAMBS", 2 * d * s, 2 * s, f"2 x {d:.3f} x {s:.4f} (jambs to the springing, T-238 outline)"),
                    ("HEAD", d * a, a, f"{d:.3f} x {a:.4f} (developed arch soffit, T-238 outline)")):
                r = jh[comp]
                out.append({"opening": op, "side": side, "component": comp, "depth_m": _g(d), "spring_m": _g(s),
                            "arch_length_m": _g(a), "width_m": _g(o["width_m"]), "crown_m": _g(o["crown_m"]),
                            "m2": _g(m2), "ml": _g(ml), "basis": basis, "ledger_m2": r["m2"], "ledger_ml": r["ml"],
                            "ledger_basis": r["basis"], "outline_task": "T-238", "outline_merge": T238_MERGE,
                            "outline_status": o["status"], "rule_id": RULE_ID})
    return out


def text(rs):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rs)
    return buf.getvalue()


if __name__ == "__main__":
    t = text(rows())
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == t
        print("ARCHED_REVEAL_CORRECTION_T326.csv", "matches the build" if ok else "DIFFERS from the build")
        sys.exit(0 if ok else 1)
    OUT.write_text(t, encoding="utf-8")
    print(t)
