"""T-550 parapet row split against a freelancer masonry row (any villa; research, unwired).

R-T550-1 (proposed, every villa; refines R-T543-1 (d) for parapet rows, provenance T-550):
  (a) PHYSICAL ELEMENT FIRST. A parapet run is measured by the engine as a face ABOVE THE FINISHED ROOF (centreline
      length c x printed height h above the finished level). Below the finished roof every printed alternative is
      concrete: the edge member below the structural slab top (hatched in the architect's cut, owned by the beam
      lines to the schedule depth) and the RC upstand between the slab top and the finish (detail P1: 'must be more
      than the height of roof finishing'). That zone is never masonry.
  (b) DATUM OF HIS HEIGHT. His row height H is split as H = h_nom + delta, where h_nom is the PRINTED nominal height
      above the finished roof for his chain and delta is what he adds below the finished level (read from his row
      against the printed heights, never assumed). delta must be >= 0; a negative delta is refused (it would mean he
      measures from above the finish).
  (c) IDENTITY (exact, Decimal), per chain:
        his - engine face = (L_his - L_eng) x H                      length census     (class given by the caller)
                          + L_eng x delta                            zone below finish (ENGINE_RIGHT only with the
                                                                     drawn evidence that it is concrete, else HELD)
                          + sum over runs c x (h_nom - h_run)        his flat height vs the run's printed height:
                                                                     PRINTED run -> ENGINE_RIGHT, HELD run -> HELD
  (d) REFUSALS: a run height whose datum is not the finished roof (e.g. measured from the slab top) is refused as a
      height above finish; a HELD run (or a HELD zone) can only be classed HELD (never agreement / ENGINE_RIGHT /
      TOLERANCE); lm without a printed height, None as a number and mm are refused.
"""
from __future__ import annotations

import functools
import inspect
import types
from decimal import Context, Decimal, localcontext

# T-653 (F-T648-2): 40 digits are used only INSIDE this module's functions, through a local Decimal context; importing
# this module never changes the process-global context (it used to set getcontext().prec = 40 at import, which changed
# every later Decimal result in the same process). in_prec40() at the end of the module applies the local context.
PREC = 40


def ctx40():
    """a local 40-digit Decimal context: `with ctx40(): ...`; the caller's context is restored on exit."""
    return localcontext(Context(prec=PREC))


def in_prec40(namespace: dict) -> None:
    """run every plain function DEFINED in the module of `namespace` (its globals()) inside ctx40(); generator
    functions, classes and names imported from other modules are left as they are. Marks each wrapper
    `_t653_prec40 = True`. Called once, at the end of the module (here and in its builder)."""
    mod = namespace["__name__"]
    for name, fn in list(namespace.items()):
        if (isinstance(fn, types.FunctionType) and fn.__module__ == mod and not getattr(fn, "_t653_prec40", False)
                and not inspect.isgeneratorfunction(fn) and name not in ("ctx40", "in_prec40")):
            namespace[name] = _wrap40(fn)


def _wrap40(fn):
    @functools.wraps(fn)
    def run40(*args, **kwargs):
        with ctx40():
            return fn(*args, **kwargs)
    run40._t653_prec40 = True
    return run40
CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")


class SplitError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise SplitError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def split_chain(*, chain: str, his_length_m, his_height_m, printed_nominal_h_m, runs: list[dict],
                below_finish_evidence: str | None, length_cause: str = "UNRESOLVED", length_basis: str = "") -> dict:
    """runs: [{run, centreline_m, h_m, h_datum ('FINISH'), h_status ('PRINTED' | 'HELD'), unit ('m')}].

    Returns {rows, his_m2, engine_face_m2, difference_m2}; rows sum exactly to the difference."""
    if length_cause not in CAUSES:
        raise SplitError(f"{chain}: length cause {length_cause!r} not in {CAUSES}")
    if length_cause in ("ENGINE_RIGHT", "TOLERANCE") and not length_basis:
        raise SplitError(f"{chain}: a length difference classed {length_cause} needs its drawing basis")
    Lh, Hh, hn = D(his_length_m), D(his_height_m), D(printed_nominal_h_m)
    if Lh <= 0 or Hh <= 0 or hn <= 0:
        raise SplitError(f"{chain}: his length / height and the printed height must be positive")
    if Hh > 50 or hn > 50:
        raise SplitError(f"{chain}: height looks like mm (metres only)")
    delta = Hh - hn
    if delta < 0:
        raise SplitError(f"{chain}: his height {Hh} is below the printed height {hn}: not a below-finish datum")
    if not runs:
        raise SplitError(f"{chain}: no engine run")
    Le = Fe = Decimal(0)
    rows = []
    h_eng_right = Decimal(0)
    h_held = Decimal(0)
    held_runs, printed_runs = [], []
    for r in runs:
        if r.get("unit", "m") != "m":
            raise SplitError(f"{chain} {r.get('run')}: unit {r.get('unit')!r} (metres only)")
        if r.get("h_datum", "FINISH") != "FINISH":
            raise SplitError(f"{chain} {r.get('run')}: height datum {r.get('h_datum')!r} is not the finished roof: a "
                             "height from the slab top is not a height above finish")
        st = r.get("h_status")
        if st not in ("PRINTED", "HELD"):
            raise SplitError(f"{chain} {r.get('run')}: height status {st!r} (PRINTED or HELD)")
        if r.get("class") and st == "HELD" and r["class"] != "HELD":
            raise SplitError(f"{chain} {r.get('run')}: a HELD run height can only be classed HELD, not {r['class']}")
        c, h = D(r["centreline_m"]), D(r["h_m"])
        if c <= 0 or h <= 0:
            raise SplitError(f"{chain} {r.get('run')}: centreline and height must be positive")
        Le += c
        Fe += c * h
        t = c * (hn - h)
        if st == "HELD":
            h_held += t
            held_runs.append(r["run"])
        else:
            h_eng_right += t
            if t:
                printed_runs.append(r["run"])
    his = Lh * Hh
    rows.append({"name": f"{chain}: length census (his {Lh} m - engine centreline {Le} m) x his height {Hh} m",
                 "delta": str((Lh - Le) * Hh), "cause": length_cause, "basis": length_basis or "not identified"})
    zone_cause = "ENGINE_RIGHT" if below_finish_evidence else "HELD"
    rows.append({"name": f"{chain}: his height below the finished roof (delta {delta} m) x engine centreline {Le} m: "
                         "concrete (edge member + RC upstand), never masonry",
                 "delta": str(Le * delta), "cause": zone_cause,
                 "basis": below_finish_evidence or "material below the finish not evidenced: HELD"})
    rows.append({"name": f"{chain}: his flat printed height {hn} m vs each run's printed height (runs {printed_runs})",
                 "delta": str(h_eng_right), "cause": "ENGINE_RIGHT",
                 "basis": "per-run printed heights above the finished roof (sections / elevations)"})
    if held_runs:
        rows.append({"name": f"{chain}: his flat printed height {hn} m vs the HELD height range of runs {held_runs} "
                             "(engine upper end)", "delta": str(h_held), "cause": "HELD",
                     "basis": "printed elevations disagree / run end not printed: HELD range"})
    s = sum((D(x["delta"]) for x in rows), Decimal(0))
    if s != his - Fe:
        raise SplitError(f"{chain}: split sums to {s}, difference is {his - Fe}")
    return {"chain": chain, "his_m2": str(his), "engine_face_m2": str(Fe), "engine_centreline_m": str(Le),
            "difference_m2": str(his - Fe), "delta_m": str(delta), "rows": rows}


def by_cause(rows: list[dict]) -> dict:
    out: dict[str, Decimal] = {}
    for r in rows:
        if r["cause"] not in CAUSES:
            raise SplitError(f"cause {r['cause']!r}")
        out[r["cause"]] = out.get(r["cause"], Decimal(0)) + D(r["delta"])
    return {k: str(v) for k, v in sorted(out.items())}


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
