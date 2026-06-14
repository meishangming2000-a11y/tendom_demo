# Stage3.11D-D Dense Sensor Fusion Dataset v0

Generated: `2026-06-12T02:22:30`

## Boundary

- MuJoCo-only dense data capture from the Stage3.11D-C selected true-pinch center.
- Virtual vision, synthetic contact/tactile morphology, simulated motor force feedback, and proprioception are exported as training signals.
- Morphology truth is exported as training/evaluation supervision, not as future hardware runtime truth.
- No full-action ACT/DP or demo-gallery promotion is made here.

## Outputs

- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_11d_d_dense_sensor_fusion_dataset_v0.npz`
- JSONL episode summaries: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage3_11d_d_dense_sensor_fusion_dataset_v0.jsonl`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage3_11d_d_dense_sensor_fusion_dataset_v0.json`

## Summary

- Episodes: `200`
- Success: `148 / 200` (`0.740`)
- Dense rows: `329075`; mean/min/max rows per episode: `1645.4` / `1301` / `1942`
- Terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 148, 'lift_gate_failed': 41, 'contact_gate_failed': 8, 'true_pinch_morphology_gate_failed': 3}`

## Sensor Blocks

- Vision features: `['ball_rel_x_m', 'ball_rel_y_m', 'ball_rel_z_m', 'lift_m', 'lift_to_goal_ratio', 'ball_abs_z_m', 'virtual_object_confidence', 'virtual_mask_visibility', 'virtual_depth_noise_m']`
- Tactile/contact features: `['hand_contacts', 'floor_contacts', 'tip_contact_ratio', 'non_tip_contact_ratio', 'true_two_tip_pinch', 'wrap_or_support', 'support_region_count', 'tip_region_count', 'max_penetration_m']`
- Simulated motor force features: `['max_abs_iq_a', 'max_hand_abs_iq_a', 'max_hand_tendon_tension_n', 'pair_total_tendon_tension_n', 'pair_balance_ratio', 'pair_max_abs_iq_a', 'pair_sum_abs_iq_a', 'pair_saturated_actuator_count', 'pair_tension_delta_abs_n', 'thumb_sum_tendon_tension_n', 'thumb_max_tendon_tension_n', 'thumb_max_abs_iq_a', 'active_sum_tendon_tension_n', 'active_max_tendon_tension_n', 'active_max_abs_iq_a']`
- Context features: `['phase_progress', 'time_s', 'min_lift_height_m', 'phase_is_grasp_evidence']`
- Safety labels: `['lift_quality_now', 'future_success', 'adjust_needed_now', 'good_two_tip_now', 'wrap_now', 'floor_contact_now', 'low_force_now', 'force_imbalance_now', 'force_saturation_now', 'penetration_risk_now', 'hold_safe_now', 'release_phase_now']`

## Label Means

- `lift_quality_now`: `0.2494`
- `future_success`: `0.7302`
- `adjust_needed_now`: `0.0936`
- `good_two_tip_now`: `0.2816`
- `wrap_now`: `0.0363`
- `floor_contact_now`: `0.6456`
- `low_force_now`: `0.4406`
- `force_imbalance_now`: `0.0006`
- `force_saturation_now`: `0.0000`
- `penetration_risk_now`: `0.0002`
- `hold_safe_now`: `0.0271`
- `release_phase_now`: `0.3653`

## Next

- Train the Stage3.11D-D lift-quality head on grasp-evidence phases.
- Use ablations to compare force/tactile/vision/proprio blocks before adding residual micro-adjustment.
