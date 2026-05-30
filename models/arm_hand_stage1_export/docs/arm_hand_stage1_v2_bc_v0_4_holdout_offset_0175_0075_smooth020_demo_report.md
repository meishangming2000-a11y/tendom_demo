# Arm-Hand Stage1 V2 BC Smoke Demo Report

Generated: 2026-05-31T01:34:41

- Status: **success**
- Terminal reason: `success_lift_hold`
- Success: `True`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Dataset: `explicit ball-offset override`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episode: `9001`
- Ball offset: `[0.0175, 0.0075, 0.0]`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_holdout\holdout_offset_0175_0075_smooth020_demo.mp4`
- Frames: `537`
- Steps: `2143`
- Hold enabled: `True`
- Hold status: `passed`
- Hold required post-success steps: `900`
- Hold settle steps: `180`
- Hold consecutive steps: `900`
- Hold min lift after success: `0.052576 m`
- Hold failure reason: `None`
- Ball lift height: `0.078270 m`
- Ball-hand contacts: `7`
- Ball-floor contacts: `0`
- Max penetration: `0.002202 m`
- Reward: `1.751992`
- Training ready: **No, experimental BC smoke only**

## Interpretation

- This demo runs the learned BC smoke policy online in MuJoCo.
- It is a first training artifact, not a promoted baseline.
- Compare it with the scripted lift demo when judging whether the next fix should be policy-side or data-side.
