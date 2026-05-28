# Shadow Stage1 Gap Report

## Scope

This is a structure-level comparison only. `hand_stage1` is not a Shadow Hand equivalent model. It is currently a stage1 kinematic + clean visual + collision-proxy prototype for smoke testing.

Local Shadow model found:

- `D:\tendon_project\simulations\models\shadow_hand\right_hand.xml`
- `D:\tendon_project\simulations\models\shadow_hand\scene_right.xml`

## Current hand_stage1 Capabilities

- Clean visual mesh model loads in MuJoCo.
- Clean STL is used only as visual geometry.
- Suspicious mesh export is not used.
- Simplified collision proxy exists for palm, wrist/base, long fingers, thumb, ball, and ground.
- 21 hinge joints are present.
- 21 position actuators are present.
- 5 fingertip sites are present.
- Position-control scripted grasp smoke test runs.
- Four long fingers can visually and numerically wrap a pinned ball in many tested positions.
- Ball initial overlap is resolved at the current default position `[0.0, -0.1, 0.195]`.

## Structural Counts

| Item | hand_stage1 | Local Shadow right_hand |
|---|---:|---:|
| Bodies excluding world | 23 | 25 |
| Hinge joints | 21 | 24 |
| Actuators | 21 | 24 |
| Tendon elements in local MJCF | 0 | 0 |
| Sites | 5 fingertip sites | 1 `grasp_site` |
| Collision geoms | 28 in hand model | 30 in local right_hand |
| Mesh assets | 23 | 15 |

Note: the local Shadow XML does not contain MuJoCo `<tendon>` elements, even though the real Shadow Hand is tendon/coupling rich. This report only describes the local files present in the repository.

## Shadow Has But hand_stage1 Does Not Yet Have

- Proven thumb opposition kinematics.
- Mature collision geometry tuned for grasping.
- Known-good actuator gains and control conventions.
- Validated grasp task scene/API.
- Robust free-object grasp behavior.
- Contact/tactile feedback integration.
- Mechanical coupling/tendon semantics for higher-fidelity control.
- A validated mapping between visual mesh, collision proxy, and physical joint axes.

## Current Main Gaps

1. Thumb opposition: current CMC/MCP/IP motion does not bring `thumb_tip_site` close enough to the ball/index side.
2. Collision fidelity: proxy geoms are useful for smoke tests, but still too coarse for final contact behavior.
3. Actuator tuning: position actuators are functional but not tuned for stable free-ball manipulation.
4. Tendon/mimic/coupling: not modeled by design at this stage.
5. Stable free-object grasp: current successful tests use a pinned ball and zero gravity.
6. Tactile/contact feedback: not present.

## Route Forward

### stage1.1 Thumb Repair

- Verify `thumb_cmc_axis`, `thumb_mcp_axis`, `thumb_ip_axis` in SolidWorks.
- Verify `thumb_cmc_csys`, `thumb_mcp_csys`, `thumb_ip_csys` Z axes and origins.
- Confirm whether `thumb_cmc_joint` has the opposition DOF or whether another thumb base DOF is missing.
- Re-export URDF/MJCF only after CAD reference semantics are corrected.

### stage1.2 Collision Proxy Refinement

- Keep STL visual-only.
- Add fingertip contact spheres/capsules.
- Tune palm support proxy and distal capsule radii based on sweep data.
- Keep hand-hand self-collision disabled until proxy shapes are less coarse.

### stage1.3 Scripted Free-Ball Grasp

- Move from pinned-ball smoke test to free-ball zero-gravity trial.
- Then add gravity and table support.
- Tune actuator gains only after thumb and collision proxies are credible.

### stage1.4 Shadow-Style Task API

- Define reset, target object placement, observation, action, and success metrics.
- Keep API structure Shadow-like, but do not claim mechanical equivalence.
- Keep scripted baselines before any learning setup.

### stage2 Tendon / Coupling / Retargeting

- Add tendon or mimic/coupled joint semantics only after the stage1 kinematic and collision model is stable.
- Consider retargeting only after thumb opposition and contact behavior are usable.

## Go / No-Go

- Continue Shadow structure-level comparison: GO.
- Continue scripted grasp task scaffolding: GO.
- Start RL/BC/training: NO-GO.
- Claim Shadow equivalence: NO-GO.
- Use current model for final physical-grasp conclusions: NO-GO.

## Export3 Update - 2026-05-21

Export3 source:

- `D:\tendon_project\hardwares\hand\hand_export3`

Export3 adds the intended second CMC thumb degree of freedom:

```text
palm_link
-> thumb_root_connector_fixed_joint
-> thumb_root_connector_link
-> thumb_cmc_abd_joint
-> thumb_trapezium1_link
-> thumb_cmc_flex_joint
-> thumb_metacarpal_link
-> thumb_mcp_joint
-> thumb_proximal_link
-> thumb_ip_joint
-> thumb_distal_link
```

Export3 compiled scene:

- Bodies including world: 26
- Scene joints including ball freejoint: 22
- Hand hinge joints: 21
- Position actuators: 21
- Geoms: 55
- Sites: 5
- Mesh assets: 24

Important structural change:

- `thumb_cmc_abd_joint` is present and actuated.
- `thumb_cmc_flex_joint` is present and actuated.
- Old `thumb_cmc_joint` is not present.
- `wrist_2_joint` is fixed in export3 URDF, so the hand still compiles with 21 hinge actuators rather than increasing to 22 hand actuators.

Effect on Shadow gap:

- The thumb DoF gap is reduced: export3 now has a 2-DoF CMC-style base instead of the previous single CMC hinge.
- Thumb opposition is materially better in the scripted metric audit: best thumb-ball distance improves from the old reference around `0.1549 m` to about `0.0858 m`.
- This makes export3 closer to a useful dexterous-hand stage1 prototype.
- It still is not Shadow-equivalent: collision fidelity, actuator tuning, tendon/coupling semantics, stable free-object grasp, and task/retargeting APIs remain open.

Updated route:

- stage1.1 thumb repair: PARTIAL IMPROVEMENT in export3, still needs visual/axis confirmation.
- stage1.2 collision proxy refinement: still required.
- stage1.3 scripted free-ball grasp: not ready; current test is pinned-ball and zero-gravity.
- stage1.4 Shadow-style task API: can continue as structure-level scaffolding.
- stage2 tendon/coupling/retargeting: still deferred.

## Shadow-Style Scripted Task Update - 2026-05-22

New diagnostic script:

- `scripts\run_export3_shadow_style_scripted_task.py`

Outputs:

- `docs\export3_shadow_style_scripted_report.md`
- `metadata\export3_shadow_style_scripted_trials.json`
- `docs\visual_checks_export3_shadow_style\`

Sweep:

- Trial count: 225
- Modes: `pinned`, `free_zero_g`, `free_gravity`
- Ball poses: `[0.0, -0.1, 0.21]`, `[0.0, -0.1, 0.195]`, `[0.01, -0.1, 0.21]`, `[-0.01, -0.1, 0.21]`, `[0.0, -0.09, 0.21]`
- Finger close scales: `0.85`, `1.0`, `1.15`
- Thumb candidates: top 5 from the export3 thumb opposition audit

Best achieved capability:

- `pinned_wrap`: PASS
- `zero_g_release_retained`: not achieved
- `gravity_release_retained`: not achieved

Best pinned case:

- Ball position: `[0.0, -0.09, 0.21]`
- Finger scale: `1.0`
- Thumb pose: `thumb_cmc_abd_joint=-0.8`, `thumb_cmc_flex_joint=0.0`, `thumb_mcp_joint=0.0`, `thumb_ip_joint=0.4`
- Hold contacts: `5`
- Max penetration: about `0.00233 m`
- Mean four-fingertip distance: about `0.03992 m`
- Thumb-ball distance: about `0.07693 m`

Free-object result:

- Zero-gravity release lost retention: best checked case drifted about `0.08102 m` after release.
- Gravity release lost retention: best checked case drifted/fell about `0.19088 m` after release.
- Visual inspection confirms that the ball leaves the grasp after release.

Updated gap assessment:

- Export3 can now support a Shadow-style scripted task scaffold and a pinned-ball wrap/contact smoke test.
- Export3 still does not achieve a stable free-object grasp.
- This is not training-ready because the success boundary is still supported by scripted placement, pinned object handling during closing, coarse collision proxies, and incomplete thumb/contact tuning.
- Next work should focus on collision proxy tuning, fingertip/palm contact shape, actuator gain stability, and final thumb axis/limit confirmation before any Shadow-style learning or retargeting layer.
