# Arm-Hand Stage1 V2 BC Smoke Demo Report

Generated: 2026-05-30T20:58:15

- Status: **success**
- Terminal reason: `success_lift_ball`
- Success: `True`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episode: `18`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_obs_phase\obs_phase_weighted_transition_recovered_ep18_demo.mp4`
- Frames: `262`
- Steps: `1044`
- Ball lift height: `0.080641 m`
- Ball-hand contacts: `7`
- Ball-floor contacts: `0`
- Max penetration: `0.003442 m`
- Reward: `11.764304`
- Training ready: **No, experimental BC smoke only**

## Interpretation

- This demo runs the learned BC smoke policy online in MuJoCo.
- It is a first training artifact, not a promoted baseline.
- Compare it with the scripted lift demo when judging whether the next fix should be policy-side or data-side.
