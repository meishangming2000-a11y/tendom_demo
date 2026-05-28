# Arm-Hand Stage1 V2 BC Smoke Demo Report

Generated: 2026-05-29T01:17:32

- Status: **success**
- Terminal reason: `success_lift_ball`
- Success: `True`
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episode: `4`
- Video: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_smoke\bc_smoke_policy_demo.mp4`
- Frames: `253`
- Steps: `1006`
- Ball lift height: `0.080595 m`
- Ball-hand contacts: `7`
- Ball-floor contacts: `0`
- Max penetration: `0.003449 m`
- Reward: `11.764045`
- Training ready: **No, experimental BC smoke only**

## Interpretation

- This demo runs the learned BC smoke policy online in MuJoCo.
- It is a first training artifact, not a promoted baseline.
- Compare it with the scripted lift demo when judging whether the next fix should be policy-side or data-side.
