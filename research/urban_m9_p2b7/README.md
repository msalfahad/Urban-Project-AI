# Phase 2B-7: ARCH_TAKEOFF_V2.7 (controlled, opt-in implementation)

## The deliverables (Section 8)

| # | Section 8 item | file |
|---|---|---|
| 1 | V2.7 implementation report | `V27_IMPLEMENTATION_REPORT.md`: the corrections, the Section 3 proposals (prototype or accepted), door openings (Section 4), known limitations, files |
| 2 | before / after BOQ impact | `BOQ_IMPACT.md`: every V2.6 → V2.7 difference attributed to a correction record (synthetic drawings; reference plan aggregates) |
| 3 | independent calculation evidence | `INDEPENDENT_EVIDENCE.md`: hand truth, the independent ezdxf reader, the raw-entity census, Stage C, the run audit |
| 4 | updated defect register | `ENGINEERING_DEFECT_REGISTER.md`: the 2B-6 register carried forward, plus the defects found in this phase |
| 5 | test results and frozen-version verification | `TEST_EVIDENCE.md` |
| 6 | owner-decision register (no duplicates) | `OWNER_DECISIONS.md` |
| 7 | next development phase plan | `NEXT_PHASE_PLAN.md` |
| 8 | privacy-clean ZIP with manifest and SHA-256 | built outside the repository (`URBAN_M9_P2B7_ARCH_V27.zip`, with `MANIFEST.json`, `MANIFEST_SHA256.txt` and a `.zip.sha256`) |
| 9 | concise ChatGPT review brief | `CHATGPT_REVIEW_BRIEF.md` |

## Repository changes

| path | what |
|---|---|
| `engine/source/arch_v27.py` | new: the V2.7 rules (layer roles with refusal, column shapes, jamb reconstruction, arc bands, wet evidence, provenance) |
| `engine/source/{arch_rooms, arch_walls, arch_measure, door_model, door_standards, knowledge, owner_finish_scope, waterproofing_system, wp_geometry}.py` | V2.7 hooks, each behind a keyword whose default is the V2.6 path |
| `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.2.0.json`, `tools/kb_build_1_2.py` | knowledge 1.2.0 (UP-DOOR-OPEN-003, UP-WET-002, OQ-05); 1.1.0 unchanged |
| `tools/urban_boq_m9.py` | `--method ARCH_TAKEOFF_V2.7`; `CORRECTIONS_V2_7.json`; per-line source entities |
| `tools/arch_v27_explain.py` | new: V2.6 → V2.7 BOQ difference explainer |
| `tools/arch_run_audit.py` | aware of V2.7 runs (A03 / A04 / A06 / A07) |
| `tests/m9_p2b7/` | fixtures, the independent reader `p2b7_indep.py`, 147 tests |

## How to run

    python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.7 [--facts FACTS.json]
    python3 -I tools/arch_v27_explain.py --before OUT_V26 --after OUT_V27
    python3 -I tools/arch_run_audit.py --run OUT --dxf PLAN.dxf

## Privacy

No private drawing, path, client identifier or room id is in this folder. Reference-plan figures are aggregates. The
private Stage C sheets, the census and the run outputs stay in the session scratch area and are never committed.
