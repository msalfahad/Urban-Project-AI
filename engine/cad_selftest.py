"""Run every synthetic CAD fixture and check its known answer.

This is the freeze gate. It runs on every pipeline invocation, so a change
to the adapter that alters any fixture's answer fails the run rather than
quietly changing what a measurement means.

The checks are arithmetic, not approximate: a rotated-and-scaled block's
endpoints are asserted to four decimals, because a transposed transform
composition lands somewhere plausible and a loose tolerance would accept
it.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_fixtures as fixtures

TOL_MM = 1e-4


@dataclass
class Result:
    name: str
    what_it_tests: str
    passed: bool
    failures: list = field(default_factory=list)
    observed: dict = field(default_factory=dict)

    def record(self) -> dict:
        return {"fixture": self.name, "tests": self.what_it_tests,
                "passed": self.passed, "failures": list(self.failures),
                "observed": dict(self.observed)}


def _close(a, b, tol=TOL_MM) -> bool:
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= tol


def _endpoints(seg):
    return ((round(seg.x1, 4), round(seg.y1, 4)),
            (round(seg.x2, 4), round(seg.y2, 4)))


def _parallel_gaps(segs) -> list:
    """Distances between distinct parallel collinear-axis segment pairs."""
    gaps = set()
    for i, a in enumerate(segs):
        for b in segs[i + 1:]:
            if a.axis != b.axis or a.axis == adapter.AXIS_SKEW:
                continue
            if a.axis == adapter.AXIS_H:
                d = abs(a.y1 - b.y1)
            else:
                d = abs(a.x1 - b.x1)
            if d > TOL_MM:
                gaps.add(round(d, 4))
    return sorted(gaps)


def _collinear_gap(segs) -> float | None:
    """The largest gap between two collinear segments on the same line."""
    best = None
    for i, a in enumerate(segs):
        for b in segs[i + 1:]:
            if a.axis != b.axis or a.axis == adapter.AXIS_SKEW:
                continue
            if a.axis == adapter.AXIS_H and abs(a.y1 - b.y1) > TOL_MM:
                continue
            if a.axis == adapter.AXIS_V and abs(a.x1 - b.x1) > TOL_MM:
                continue
            if a.axis == adapter.AXIS_H:
                lo_a, hi_a = sorted((a.x1, a.x2))
                lo_b, hi_b = sorted((b.x1, b.x2))
            else:
                lo_a, hi_a = sorted((a.y1, a.y2))
                lo_b, hi_b = sorted((b.y1, b.y2))
            gap = max(lo_a, lo_b) - min(hi_a, hi_b)
            if gap > TOL_MM and (best is None or gap > best):
                best = round(gap, 4)
    return best


def check(fx) -> Result:
    """Normalize one fixture and compare against its stated answer."""
    nd = adapter.normalize(fx.decode, source_file=fx.name,
                           source_hash="FIXTURE")
    segs = nd.segments()
    arcs = [p for p in nd.primitives if p.kind == adapter.ARC]
    circles = [p for p in nd.primitives if p.kind == adapter.CIRCLE]
    hatches = [p for p in nd.primitives if p.kind == adapter.HATCH]
    e = fx.expect
    bad = []
    obs = {
        "primitives": len(nd.primitives), "segments": len(segs),
        "arcs": len(arcs), "circles": len(circles), "hatches": len(hatches),
        "texts": len(nd.texts), "dimensions": len(nd.dimensions),
        "instances": len(nd.instances),
        "definitions": len(nd.block_definitions),
        "layers": sorted(nd.layers),
        "drawing_unit": nd.drawing_unit, "insunits_code": nd.insunits_code,
        "unhandled": dict(nd.unhandled),
    }

    def want(key, value, label=None):
        if key in e and value != e[key]:
            bad.append(f"{label or key}: expected {e[key]!r}, got {value!r}")

    want("primitives", len(nd.primitives))
    want("segments", len(segs))
    want("arcs", len(arcs))
    want("circles", len(circles))
    want("hatches", len(hatches))
    want("texts", len(nd.texts))
    want("dimensions", len(nd.dimensions))
    want("instances", len(nd.instances))
    want("definitions", len(nd.block_definitions))
    want("drawing_unit", nd.drawing_unit)
    want("insunits_code", nd.insunits_code)
    want("layers", sorted(nd.layers))

    if "layers_present" in e:
        for name in e["layers_present"]:
            if name not in nd.layers:
                bad.append(f"layer {name!r} missing from {sorted(nd.layers)}")

    if "length_mm" in e:
        total = sum(p.length_mm for p in nd.primitives)
        obs["length_mm"] = round(total, 6)
        if not _close(total, e["length_mm"], 1e-5):
            bad.append(f"length_mm: expected {e['length_mm']}, got {total}")

    if "total_length_mm" in e:
        total = sum(p.length_mm for p in segs)
        obs["total_length_mm"] = round(total, 6)
        if not _close(total, e["total_length_mm"], 1e-5):
            bad.append(f"total_length_mm: expected {e['total_length_mm']}, "
                       f"got {total}")

    if "axis" in e:
        axes = {p.axis for p in nd.primitives if p.kind == adapter.SEGMENT}
        obs["axes"] = sorted(axes)
        if axes != {e["axis"]}:
            bad.append(f"axis: expected {{{e['axis']}}}, got {sorted(axes)}")

    if "segment_endpoints" in e:
        if len(segs) != 1:
            bad.append(f"segment_endpoints needs exactly one segment, "
                       f"got {len(segs)}")
        else:
            got = _endpoints(segs[0])
            obs["segment_endpoints"] = got
            exp = e["segment_endpoints"]
            ok = (all(_close(g, x) for g, x in zip(got[0], exp[0]))
                  and all(_close(g, x) for g, x in zip(got[1], exp[1])))
            if not ok:
                bad.append(f"segment_endpoints: expected {exp}, got {got}")

    if "text_value" in e:
        vals = [t.value for t in nd.texts]
        obs["text_values"] = vals
        if e["text_value"] not in vals:
            bad.append(f"text_value {e['text_value']!r} not in {vals}")

    if "text_at" in e:
        if not nd.texts:
            bad.append("text_at: no text observation produced")
        else:
            got = (round(nd.texts[0].x, 4), round(nd.texts[0].y, 4))
            obs["text_at"] = got
            if not all(_close(g, x) for g, x in zip(got, e["text_at"])):
                bad.append(f"text_at: expected {e['text_at']}, got {got}")

    if nd.dimensions:
        d = nd.dimensions[0]
        obs["dimension"] = {
            "geometry_mm": round(d.geometry_mm, 4),
            "display_value": d.display_value,
            "normalized_mm": (None if d.normalized_mm is None
                              else round(d.normalized_mm, 4)),
            "overridden": d.is_overridden}
        for key, got in (("geometry_mm", d.geometry_mm),
                         ("display_value", d.display_value),
                         ("normalized_mm", d.normalized_mm)):
            if key in e and not _close(got, e[key], 1e-3):
                bad.append(f"{key}: expected {e[key]}, got {got}")
        if "overridden" in e and d.is_overridden != e["overridden"]:
            bad.append(f"overridden: expected {e['overridden']}, "
                       f"got {d.is_overridden}")
        if e.get("display_is_not_geometry") and _close(
                d.display_value, d.geometry_mm, 1e-6):
            bad.append("display_value equals geometry_mm — DIMLFAC was not "
                       "kept as a separate concept")

    if "parallel_gap_mm" in e:
        gaps = _parallel_gaps(segs)
        obs["parallel_gaps_mm"] = gaps
        if not any(_close(g, e["parallel_gap_mm"]) for g in gaps):
            bad.append(f"parallel_gap_mm {e['parallel_gap_mm']} not in {gaps}")

    if "distinct_gaps_mm" in e:
        gaps = _parallel_gaps(segs)
        obs["parallel_gaps_mm"] = gaps
        for g in e["distinct_gaps_mm"]:
            if not any(_close(x, g) for x in gaps):
                bad.append(f"expected a wall gap of {g}, gaps are {gaps}")

    if "collinear_gap_mm" in e:
        gap = _collinear_gap(segs)
        obs["collinear_gap_mm"] = gap
        if not _close(gap, e["collinear_gap_mm"]):
            bad.append(f"collinear_gap_mm: expected "
                       f"{e['collinear_gap_mm']}, got {gap}")

    if "extent_width_mm" in e:
        x0, _, x1, _ = nd.extent()
        obs["extent_width_mm"] = round(x1 - x0, 4)
        if not _close(x1 - x0, e["extent_width_mm"], 1e-3):
            bad.append(f"extent_width_mm: expected {e['extent_width_mm']}, "
                       f"got {x1 - x0}")

    if "two_clusters_at_x" in e:
        xs = sorted({round(min(s.x1, s.x2), 4) for s in segs})
        obs["segment_min_x"] = xs
        for target in e["two_clusters_at_x"]:
            if not any(_close(x, target) for x in xs):
                bad.append(f"no segment starts at x={target}; starts {xs}")

    if "max_depth" in e:
        got = max([i.depth for i in nd.instances], default=0)
        obs["max_depth"] = got
        if got != e["max_depth"]:
            bad.append(f"max_depth: expected {e['max_depth']}, got {got}")

    if "block_name" in e:
        names = sorted({i.block_name for i in nd.instances})
        obs["block_names"] = names
        if e["block_name"] not in names:
            bad.append(f"block {e['block_name']!r} not in {names}")

    if e.get("points_dropped"):
        # A POINT must never appear as a primitive of any kind.
        if any(p.kind not in (adapter.SEGMENT, adapter.ARC, adapter.CIRCLE,
                              adapter.HATCH) for p in nd.primitives):
            bad.append("a POINT reached the primitive list")

    if e.get("no_wall_is_named"):
        kinds = {p.kind for p in nd.primitives}
        if kinds - {adapter.SEGMENT, adapter.ARC, adapter.CIRCLE,
                    adapter.HATCH}:
            bad.append(f"the adapter invented a kind: {sorted(kinds)}")

    if nd.unhandled:
        bad.append(f"unhandled entity types: {dict(nd.unhandled)}")

    # Identity discipline: every object id must be unique and derived from a
    # handle, never from a list position.
    ids = [p.object_id for p in nd.primitives]
    if len(ids) != len(set(ids)):
        dupes = [k for k, n in Counter(ids).items() if n > 1]
        bad.append(f"duplicate object ids (order used as identity?): {dupes}")
    if any(not i.startswith("CAD-") for i in ids):
        bad.append("an object id is not derived from a DWG handle")

    return Result(fx.name, fx.what_it_tests, not bad, bad, obs)


def run() -> list:
    return [check(fx) for fx in fixtures.cases()]


def freeze_hash() -> str:
    """Hash of every fixture's name and its expected answer.

    Sorted, so the fixtures' ORDER is not part of the freeze — only what
    they assert.
    """
    rows = sorted(f"{fx.name}|{sorted(fx.expect.items(), key=str)}"
                  for fx in fixtures.cases())
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:24]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "adapter": adapter.ADAPTER,
        "CAD_ADAPTER_HASH": adapter.adapter_hash(),
        "CAD_FIXTURE_FREEZE_HASH": freeze_hash(),
        "frozen_parameters": adapter.frozen_parameters(),
        "fixtures": len(res),
        "passed": sum(1 for r in res if r.passed),
        "failed": len(failed),
        "cases": [r.record() for r in res],
        "what_a_pass_means": (
            "the adapter reproduces an answer computed by hand, on a drawing "
            "built by hand. It says nothing about any real source and it is "
            "not evidence that any real source measures correctly"),
        "why_before_p7757": (
            "an adapter validated against the drawing it will be judged on "
            "has been tuned, not tested. None of these fixtures came from "
            "looking at P7757"),
    }


def assert_frozen() -> dict:
    """Raise if any fixture's known answer has changed."""
    rep = report()
    if rep["failed"]:
        names = [c["fixture"] for c in rep["cases"] if not c["passed"]]
        raise AssertionError(
            f"CAD adapter freeze broken on {rep['failed']} fixture(s): "
            f"{names}. A change that alters a known answer changes what a "
            "measurement MEANS, and may not pass silently")
    return rep
