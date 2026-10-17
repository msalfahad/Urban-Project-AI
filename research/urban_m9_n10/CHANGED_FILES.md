# Changed files and commits (Phase N10)

## 1. Commits

Branch `claude/access-permissions-setup-ii24ws`. The baseline is **504b56a**, committed 2026-10-17 19:55 UTC. All N10 commits are pushed.

| Commit | Time (UTC) | Content | Code? |
|---|---|---|---|
| 3070576 | 20:45 | ARCH_TAKEOFF_V2.9 (opt-in): curved wall openings closed on their own wall faces (D-P9-01, D-P9-02) | yes |
| f6dad61 | 21:01 | independent verification: curved gaps, joined-room faces, zone-bounded faces (D-P9-04) | yes (audit tools) |
| dec6766 | 21:26 | the freeze-check command moved to the routing config (fixes the baseline session-guard failure, D-N10-00) | yes (tool config) |
| f32107c | 21:26 | V2.9 masonry panel area and volume per wall thickness (UP-MAS-HEIGHT-001) | yes |
| 9f98d3f | 21:54 | V2.9 facade run, area and exterior finish per floor (UP-FACADE-001) | yes |
| 40f3184 | 22:06 | structural N10: formwork faces, excavation footprints, reinforcement audit | yes (separate tool) |
| 6e7f0b8 | 22:06 | regenerated docs/ROUTE_QUICK.md | maps only |
| 9a52c34 | 22:13 | knowledge registry 1.5.0 | yes (registry) |
| 4b299ae | 22:23 | defect register, owner decisions register, worked examples | **last code-affecting commit**: maps, one routing-config entry and docs. The full suite ran on this commit |
| later | — | deliverables in `research/urban_m9_n10/` and regenerated maps | docs only |

The private snapshot ran on the tree at 9a52c34. 4b299ae changes no engine, tool logic, rule or knowledge file (`REGRESSION_AND_FROZEN_EVIDENCE.md` §1).

## 2. Files changed 504b56a → 4b299ae

Generated with `git diff --name-status / --numstat 504b56a 4b299ae`. The SHA-256 is of the blob at 4b299ae.

| File | Status | Lines | Kind | Commits | SHA-256 at 4b299ae |
|---|---|---|---|---|---|
| `docs/CODEMAP.md` | changed | +26 / -20 | generated map (not in the ZIP) | 3070576, f6dad61, f32107c, 9f98d3f, 40f3184, 9a52c34, 4b299ae | `3809ed251cbe086e4aaa9ec119b188941aa3677859a9d4686064c5b0d4074d0f` |
| `docs/ROUTE_QUICK.md` | changed | +11 / -11 | generated map (not in the ZIP) | 6e7f0b8, 4b299ae | `c043aa1ec55a82fd19cd35a2b7ded24505ff801440fc68cb8c13e3cb4fc82f2c` |
| `docs/ROUTING.md` | changed | +121 / -85 | generated map (not in the ZIP) | 3070576, f32107c, 9f98d3f, 40f3184, 9a52c34, 4b299ae | `2d6c62afa5a0d0318680816ccc1b0ec885da0f4f4847c41d75362e09f7405a92` |
| `docs/RULES_INDEX.md` | changed | +8 / -3 | generated map (not in the ZIP) | 9a52c34 | `91f942c7f801e9f211b35b7c8bad54a64ee397d0ce0332273ad6ce0b40e89afd` |
| `engine/source/arch_completeness.py` | changed | +8 / -1 | source | 3070576 | `bfdc759710a4f89a80103b4107175f8dae36430932fcd9b0ac0af92d957f1722` |
| `engine/source/arch_rooms.py` | changed | +31 / -11 | source (diff only in the ZIP: an unchanged line carries a token on the private layer-name list) | 3070576, 9f98d3f | `fd3a53923e31138f5941bf3a87cedfa624998bbc7b62ed8dab41c120da93cfb2` |
| `engine/source/arch_v28.py` | changed | +9 / -1 | source | 3070576 | `60acf642cbd4c07cbbfbb8f45a403b37b2f03beb0577b97f5ce574e9458eb449` |
| `engine/source/arch_v29.py` | new | +808 / -0 | source | 3070576, f32107c, 9f98d3f | `f6c9bb1ac013d8b20325796782ba32c8b183fd5c6111c2af23f82bd6abdce55a` |
| `engine/source/knowledge.py` | changed | +2 / -1 | source | 9a52c34 | `bb91c72df3aaaa3f3bc33aa9490220a2c2b0280ed9871bead9ccc60cd65c86b6` |
| `engine/source/struct_n10.py` | new | +305 / -0 | source | 40f3184 | `9928c3bd94c43080d7df247e14f4f59c1a9e0c0974a8f31afd0676766622d396` |
| `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json` | new | +4954 / -0 | registry data | 9a52c34 | `9c2b1852225a74e44cb832e539eae260d773071236a0689db7557525254e9364` |
| `research/urban_m9_n10/DEFECT_REGISTER.md` | new | +57 / -0 | deliverable | 4b299ae | `add98149abcacc190a2d931670233081afe759e7e8d85d4c1a7e82313fefddb6` |
| `research/urban_m9_n10/OWNER_DECISIONS_REGISTER.md` | new | +43 / -0 | deliverable | 4b299ae | `5502d327669a8554a66e54b7bdfe27daa60acdb1c72940d2d52f8655f7032c8b` |
| `research/urban_m9_n10/WORKED_EXAMPLES.md` | new | +58 / -0 | deliverable | 4b299ae | `ba6c13a0a29c5c9dbb706f810347ed61db1f081b18f663026670a5a0aa8757b5` |
| `tests/m9_n10/n10_fixtures.py` | new | +254 / -0 | test | 3070576, f32107c, 9f98d3f | `e459a3beeefcac7613640483809e838daf342c6bac822faff1edcb81d6f48c37` |
| `tests/m9_n10/n10_run.py` | new | +56 / -0 | test | 3070576, f32107c | `e435327cb833eac9bdaecb54b7d72bbc8e02b799383c578a7a0e6ed84f0b1129` |
| `tests/m9_n10/n10_truth.py` | new | +104 / -0 | test | 3070576, f32107c, 9f98d3f | `3a84dc612423f98b0984b791f94d3a85c0bccb6fd135307eb7f27c60beec3bbb` |
| `tests/m9_n10/test_n10_curved_openings.py` | new | +226 / -0 | test | 3070576 | `743e9bdccfe94d6f72de87d571ccd16f0b269045b7ad2664eba361d8b8f05a1e` |
| `tests/m9_n10/test_n10_facade.py` | new | +159 / -0 | test | 9f98d3f | `4eed531566606a8aea48859c6280ab23472d5cdb76e316fc40659d9b332b02b1` |
| `tests/m9_n10/test_n10_indep_curved.py` | new | +74 / -0 | test | f6dad61 | `92b287d28a3efcfe10ccc1841eebb25c4f56826e7d73d7326136b7c373d3e803` |
| `tests/m9_n10/test_n10_masonry.py` | new | +117 / -0 | test | f32107c | `cdb936363e8a73a1b8fd8bd8dd4e982c15fe4b7fa650f992952dbda5107092da` |
| `tests/m9_n10/test_n10_registry.py` | new | +52 / -0 | test | 9a52c34 | `792132b4bca38e87f55cb4e036df7dfed9115cddda9c36e62f4fc477adc56bd2` |
| `tests/m9_n10/test_n10_structural.py` | new | +206 / -0 | test | 40f3184 | `aebc423184f02fcde10416cdb6514ed452c0044bff0e6f3ba91137d0ddd34bf4` |
| `tools/arch_change_verify.py` | changed | +131 / -4 | source | f6dad61, f32107c, 9f98d3f | `a3d191bc03c0861a6989901773a9f9f64ac0a6166183dbbfac92d34ef4143506` |
| `tools/codemap.py` | changed | +1 / -1 | source | dec6766 | `3c21726bb34c691ef4cc35c39813111110b64d660d1d7660d52bf6fea13d9a5d` |
| `tools/indep_reader.py` | changed | +138 / -2 | source | f6dad61 | `7383bc48bfc3e2fb9bfe247d64d534d3c0ccf4d6e03fba1fe9aa0f8ba8d6b808` |
| `tools/kb_build_1_5.py` | new | +247 / -0 | source | 9a52c34 | `66664bb193d1a567127dda7e306aecaa5ac3a6a8b5a520ed8d2ee94883c65e3b` |
| `tools/routing_topics.json` | changed | +27 / -12 | source (diff only in the ZIP: the full file names a pre-existing private test folder) | dec6766, 40f3184, 4b299ae | `2c63f090a0c99a1664e732502ac72c9806020e84a55ebad37bda960a4bc30e69` |
| `tools/struct_n10.py` | new | +72 / -0 | source | 40f3184 | `a953b209c49e2334ecd5a146a8fe119d89b736ddbeeb92a401edfe62a8ab0e12` |
| `tools/urban_boq_m9.py` | changed | +380 / -22 | source | 3070576, f32107c, 9f98d3f, 9a52c34 | `c4dbf1cb938c6e0930b450d0deba1cdb5f346ffe9b396a6eab1360485d8dbdb2` |

Totals: 30 files, +8,685 / −174 lines.

**Unchanged:**

- `rules/`, `data/`;
- `engine/source/topology.py` (frozen, read only);
- route G (`tools/urban_boq_m2.py` and its modules);
- the sealed blind protocol.

## 3. Patch

The handoff ZIP carries `patch/n10_504b56a_4b299ae.patch`, produced by `git diff 504b56a 4b299ae -- . ':(exclude)docs'`. It leaves out the generated maps under `docs/`. They carry pre-existing identifiers: the privacy scan finds the same 80 hits in the maps at 504b56a and at 4b299ae, so N10 added none. The maps are rebuilt by `python3 -I tools/codemap.py build`.

To apply it on 504b56a: `git apply n10_504b56a_4b299ae.patch`, then rebuild the maps.
