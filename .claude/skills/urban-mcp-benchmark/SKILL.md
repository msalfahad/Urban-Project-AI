---
name: urban-mcp-benchmark
description: Benchmark a CAD MCP server or any room / opening reader against the Urban synthetic plans with hand-derived truth (room recall, false rooms, IoU, area / perimeter / boundary / corner error, openings by kind and width), before any reader is trusted or adopted. Synthetic drawings only.
---

# Urban MCP / reader benchmark

## Purpose
Decide, with numbers, whether a reader (a CAD MCP server, a library, a vision model, an engine change) measures plans
as well as the native engine and the independent reference - and where it fails.

## Trigger
A new MCP server or CAD library is proposed; a reader is upgraded; the engine's room or opening logic changes; the
owner asks which tool to use.

## Inputs
- the benchmark cases `tests/m9_p2b5_bench/bench_cases.py` (synthetic plans, typed-literal truth): `CASES` B01 - B10
  (rectangle, mirrored door block, L shape, column, adjacent rooms, 27-degree rotation, splayed wall, doorless
  passage, a whole mirrored plan, an arc wall) and `ENCODED` C01 - C06, the same plans written another way (walls in
  nested blocks with a mirrored and a non-uniformly scaled INSERT, metres, wall polylines, Arabic room words with
  DIMENSIONs, a window block, walls in an unresolved XREF - whose truth is a refusal)
- an adapter for the reader: a function `(case, work_dir) -> (rooms [{label, polygon_mm, area_m2}], openings
  [{kind, width_m}] or None, extra, runtime)` added to `tests/m9_p2b5_bench/bench_run.py` `_rooms` (the MCP slot is
  `MCP_ADAPTERS`)

## Tools
- `python3 -s tests/m9_p2b5_bench/bench_run.py --out research/urban_m9_p2b5/bench` (writes BENCHMARK_RESULTS.json /
  .md; runtimes are indicative only)
- `python3 -m pytest tests/m9_p2b5_bench` (the assertions: exact readers exact, CAD encodings change nothing, an XREF
  is refused, raster within 1 %, scan within 5 %; found defects asserted as found)
- the session's MCP inventory and the CAD MCP candidates: `research/urban_m9_p2b5/MCP_SKILLS_AUDIT.md`
- the licence review: the donor table in the repository handoff (`URBAN_PROJECTS_CLAUDE_HANDOFF.md`, section 10) and
  the research note `research/urban_m9_p2b5/FLOORPLAN_AI_RESEARCH.md`

## Safety
- Only synthetic drawings go to an MCP server or any third-party tool. Never send a private drawing, a client name or
  a coordinate from a real project, unless the owner authorises it in writing for that tool.
- Review an MCP server's code and licence before connecting it; do not install unknown third-party skills or
  servers without reading their contents.
- No code is copied from a donor whose licence is incompatible (AGPL / GPL / no licence / non-commercial); ideas are
  reimplemented cleanly and credited.

## Outputs
The benchmark table per case and method, the list of failures with their cause, and a recommendation (adopt / use as
a cross-check / reject), stated with the licence class.

## Tests
`tests/m9_p2b5_bench/test_bench.py` (independence, truth vs coordinates, every reader's bound).

## Escalation
Connecting an MCP server, buying a licence (for example a commercial PDF engine) or sending any non-synthetic file
to an external service is an owner decision.
