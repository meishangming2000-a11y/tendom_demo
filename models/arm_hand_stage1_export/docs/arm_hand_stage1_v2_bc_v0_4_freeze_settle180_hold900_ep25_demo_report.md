# Arm-Hand Stage1 V2 BC Smoke Demo Report

Generated: 2026-05-31T01:12:18

- Status: **success**
- Terminal reason: `success_lift_hold`
- Success: `True`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episode: `25`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_hold\obs_phase_weighted_transition_ep25_freeze_settle180_hold900_demo.mp4`
- Frames: `537`
- Steps: `2144`
- Hold enabled: `True`
- Hold status: `passed`
- Hold required post-success steps: `900`
- Hold settle steps: `180`
- Hold consecutive steps: `900`
- Hold min lift after success: `0.063245 m`
- Hold failure reason: `None`
- Ball lift height: `0.079840 m`
- Ball-hand contacts: `7`
- Ball-floor contacts: `0`
- Max penetration: `0.002203 m`
- Reward: `1.767684`
- Training ready: **No, experimental BC smoke only**

## Interpretation

- This demo runs the learned BC smoke policy online in MuJoCo.
- It is a first training artifact, not a promoted baseline.
- Compare it with the scripted lift demo when judging whether the next fix should be policy-side or data-side.
