# Stage3 Sensor Fusion BC Baseline V0 Eval Report

Generated: 2026-06-05T01:47:18

- Status: **FAIL**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_sensor_fusion_bc_baseline_v0_overfit.pth`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml`
- Episodes: `10`
- Success count: `0 / 10`
- Terminal reasons: `{'functional_approach_missed_true_egg': 10}`
- Risk flags: `{'early_contact_in_approach': 9, 'transient_or_hold_slip': 10}`
- Mean final lift: `-0.010207 m`
- Mean hold stable fraction: `0.000`
- Max hold slip: `0.000`
- Max crush risk: `0.360`
- Max penetration: `0.007197 m`

## Episode Results

| ep | trial | status | reason | lift m | stable | hold slip | final slip | crush | pen m | failures |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | center_nominal | FAIL | functional_approach_missed_true_egg | -0.01603 | 0.000 | 0.000 | 0.000 | 0.235 | 0.004699 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 1 | left_low_nominal | FAIL | functional_approach_missed_true_egg | -0.00449 | 0.000 | 0.000 | 0.000 | 0.212 | 0.004238 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 2 | right_high_nominal | FAIL | functional_approach_missed_true_egg | -0.00450 | 0.000 | 0.000 | 0.000 | 0.184 | 0.003688 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 3 | left_high_zplus | FAIL | functional_approach_missed_true_egg | -0.00395 | 0.000 | 0.000 | 0.000 | 0.122 | 0.002432 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 4 | right_low_zminus | FAIL | functional_approach_missed_true_egg | -0.00625 | 0.000 | 0.000 | 0.000 | 0.165 | 0.003307 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 5 | front_small_lift | FAIL | functional_approach_missed_true_egg | -0.01202 | 0.000 | 0.000 | 0.000 | 0.360 | 0.007197 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 6 | back_large_lift | FAIL | functional_approach_missed_true_egg | -0.00605 | 0.000 | 0.000 | 0.000 | 0.280 | 0.005605 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 7 | lifted_center | FAIL | functional_approach_missed_true_egg | -0.01300 | 0.000 | 0.000 | 0.000 | 0.069 | 0.001378 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 8 | lifted_diag | FAIL | functional_approach_missed_true_egg | -0.01585 | 0.000 | 0.000 | 0.000 | 0.146 | 0.002930 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 9 | wide_diag | FAIL | functional_approach_missed_true_egg | -0.01992 | 0.000 | 0.000 | 0.000 | 0.138 | 0.002760 | `['functional_approach_missed_true_egg', 'grip_not_stable_before_lift', 'insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |

## Interpretation

- This is closed-loop MuJoCo evaluation, not offline loss.
- The model still uses scripted phase timing and virtual-camera acquisition; it learns actuator targets from sensor abstraction observations.
- Compare this report against the scripted expert before promoting any policy.
