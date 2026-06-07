# Stage3 Sensor Fusion BC Baseline V0 Eval Report

Generated: 2026-06-05T01:45:03

- Status: **FAIL**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_sensor_fusion_bc_baseline_v0.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Episodes: `10`
- Success count: `0 / 10`
- Terminal reasons: `{'grip_not_stable_before_lift': 3, 'functional_approach_missed_true_egg': 6, 'insufficient_lift_height': 1}`
- Risk flags: `{'early_contact_in_approach': 10, 'transient_or_hold_slip': 10}`
- Mean final lift: `-0.009690 m`
- Mean hold stable fraction: `0.000`
- Max hold slip: `1.000`
- Max crush risk: `0.476`
- Max penetration: `0.009521 m`

## Episode Results

| ep | trial | status | reason | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | FAIL | grip_not_stable_before_lift | -0.01474 | 0.000 | 0.000 | 0.000 | 0.264 | 0.005274 | `['grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 1 | left_low_nominal | FAIL | functional_approach_missed_true_egg | -0.01323 | 0.000 | 0.000 | 0.000 | 0.255 | 0.005102 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 2 | right_high_nominal | FAIL | insufficient_lift_height | -0.00384 | 0.000 | 1.000 | 0.000 | 0.231 | 0.004625 | `['insufficient_lift_height', 'unstable_hold_tactile', 'hold_slip_score_high', 'egg_on_floor_after_hold']` |
| 3 | left_high_zplus | FAIL | functional_approach_missed_true_egg | -0.00151 | 0.000 | 0.000 | 0.000 | 0.232 | 0.004642 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 4 | right_low_zminus | FAIL | functional_approach_missed_true_egg | -0.00269 | 0.000 | 0.000 | 0.000 | 0.333 | 0.006663 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 5 | front_small_lift | FAIL | functional_approach_missed_true_egg | -0.00533 | 0.000 | 0.000 | 0.000 | 0.266 | 0.005328 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 6 | back_large_lift | FAIL | grip_not_stable_before_lift | -0.00453 | 0.000 | 1.000 | 0.000 | 0.257 | 0.005132 | `['grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'hold_slip_score_high', 'egg_on_floor_after_hold']` |
| 7 | lifted_center | FAIL | grip_not_stable_before_lift | -0.01670 | 0.000 | 0.000 | 0.000 | 0.333 | 0.006651 | `['grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 8 | lifted_diag | FAIL | functional_approach_missed_true_egg | -0.02179 | 0.000 | 0.000 | 0.000 | 0.259 | 0.005177 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 9 | wide_diag | FAIL | functional_approach_missed_true_egg | -0.01253 | 0.000 | 0.000 | 0.000 | 0.476 | 0.009521 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |

## Interpretation

- This is closed-loop MuJoCo evaluation, not offline loss.
- The model still uses scripted phase timing and virtual-camera acquisition; it learns actuator targets from sensor abstraction observations.
- Compare this report against the scripted expert before promoting any policy.
