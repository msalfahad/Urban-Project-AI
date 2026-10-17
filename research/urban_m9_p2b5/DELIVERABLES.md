# The 24 deliverables of Part 10, and where each one is

Paths are relative to `research/urban_m9_p2b5/` unless they start with another top-level folder. Everything listed is
in the repository, except the real-room sheets of item 6, which hold reference-plan line data and stay in the
authorised private environment. Their aggregates are public.

| # | deliverable | file(s) |
|---|---|---|
| 1 | Executive summary | `EXECUTIVE_SUMMARY.md` |
| 2 | Current engine capability assessment | `ENGINE_CAPABILITY.md` |
| 3 | Waterproofing constructability audit | `research/urban_m9_p2b4/CONSTRUCTABILITY_AUDIT_REPORT.md` (Phase 2B-4: WP-B, WP-E, WP-D with `WPB_FLOOR_TO_WALL_JUNCTION.md`, `WPE_DOORS_AND_PIPE.md`, `WPD_CORNERS_SEAMS_CUTTING.md`); `V26_IMPLEMENTATION_REPORT.md` §3 (each finding against the V2.6 correction) and §8 (new findings) |
| 4 | Corrected waterproofing diagrams | `diagrams/IX-01 … IX-08_install.svg` and `_cutting.svg` (16 sheets, generated); `SCREENSHOT_REVIEW.md`; `research/urban_m9_p2b4/diagrams/` |
| 5 | Independent membrane cutting calculations | `WORKED_EXAMPLES.md` (ten examples through the full verification chain, 297 / 297), `VERIFICATION_CHAIN.csv`, `JUNCTION_ALTERNATIVES.md`, `INSTALLATION_GEOMETRY.md`; the independent reference in `tests/m9_p2b5/` |
| 6 | Real-room measurement sheets | private (room-level reference-plan data); public: `REAL_ROOM_VERIFICATION.md` §1 - §3 (method, independence, rooms by type, checks by quantity) |
| 7 | Real-room engine comparison | `REAL_ROOM_VERIFICATION.md` §3 - §5 (V2.5), §7 (V2.6 D-V26-06), §8 (V2.6 D-V26-07: 11 → 8 failing checks of 66) |
| 8 | MCP capability inventory | `MCP_SKILLS_AUDIT.md` §1 |
| 9 | MCP benchmark results | `MCP_SKILLS_AUDIT.md` §2 - §4; `bench/BENCHMARK_RESULTS.md` (the CAD MCP rows are NOT_AVAILABLE: none is connected in this session) |
| 10 | Skills inventory and proposed Urban skills | `MCP_SKILLS_AUDIT.md` §5 - §6; `.claude/skills/urban-*/SKILL.md` (six skills); `tests/m9_p2b5_bench/test_skills.py` |
| 11 | Floorplan AI research report | `FLOORPLAN_AI_RESEARCH.md` |
| 12 | Open-source licence assessment | `LICENCE_ASSESSMENT.md` |
| 13 | Computer-vision prototype documentation | `FLOORPLAN_AI_RESEARCH.md` §2 - §4; `tests/m9_p2b5_bench/vision.py` |
| 14 | CAD-versus-vision geometry comparison | `ROOM_READER_BENCHMARK.md`; `bench/BENCHMARK_RESULTS.md`, `.json` (16 cases x up to 6 methods) |
| 15 | Hybrid architecture specification | `FLOORPLAN_AI_RESEARCH.md` §5; `tests/m9_p2b5_bench/hybrid.py` (provenance of both sides, the CAD value the only BOQ basis) |
| 16 | BOQ quantity impact analysis | `BOQ_IMPACT.md` |
| 17 | Rule precedence and provenance verification | `RULE_PRECEDENCE.md` |
| 18 | New defects and corrections | `DEFECTS_AND_CORRECTIONS.md` |
| 19 | Tests and regression evidence | `TEST_RUN.md` |
| 20 | Frozen-integrity verification | `TEST_RUN.md` §3; `V26_IMPLEMENTATION_REPORT.md` §7, §10, §11; `research/freeze_integrity/` (index, environment lock) |
| 21 | Outstanding genuine owner decisions | `OWNER_DECISIONS.md` |
| 22 | Development roadmap ranked by expected accuracy improvement | `ROADMAP.md` |
| 23 | Independent engineering audit | `INDEPENDENT_REVIEW.md` |
| 24 | ChatGPT handoff brief | `CHATGPT_BRIEF.md` |

Engine and CLI changes: `engine/source/wp_install.py` (new), `membrane_layout.py`, `wp_geometry.py`,
`waterproofing_system.py` (Stage B); `arch_rooms.py`, `door_model.py`, `arch_measure.py` (D-V26-06);
`arch_completeness.py`, `owner_finish_scope.py`, `arch_measure.py` (D-V26-07); `tools/urban_boq_m9.py`. All of them sit
behind `--method ARCH_TAKEOFF_V2.6`.
