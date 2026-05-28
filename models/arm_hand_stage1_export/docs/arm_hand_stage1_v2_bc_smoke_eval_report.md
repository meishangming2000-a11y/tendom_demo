# Arm-Hand Stage1 V2 BC Smoke Eval Report

Generated: 2026-05-29T01:17:06

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `9`
- Success count: `9 / 9`
- Terminal reasons: `{'success_lift_ball': 9}`
- Lift range: `0.080108 m` to `0.080857 m`
- Mean lift: `0.080522 m`
- Max steps: `1230`
- Action clipping: `True`
- Action smoothing: `0.0`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | status | reason | steps | lift m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | success | success_lift_ball | 1009 | 0.080287 | 11.767041 | 7 | 0 | 0.003131 | 3.422660 | 0.007573 |
| 1 | success | success_lift_ball | 1009 | 0.080395 | 11.767969 | 7 | 0 | 0.003124 | 3.422660 | 0.007573 |
| 2 | success | success_lift_ball | 1006 | 0.080428 | 11.762292 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 3 | success | success_lift_ball | 1009 | 0.080660 | 11.770473 | 6 | 0 | 0.003136 | 3.422660 | 0.007573 |
| 4 | success | success_lift_ball | 1006 | 0.080595 | 11.764045 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 5 | success | success_lift_ball | 1007 | 0.080857 | 11.766736 | 7 | 0 | 0.003448 | 3.420162 | 0.007584 |
| 6 | success | success_lift_ball | 1007 | 0.080108 | 11.763895 | 6 | 0 | 0.003295 | 3.420162 | 0.007584 |
| 7 | success | success_lift_ball | 1006 | 0.080554 | 11.763630 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 8 | success | success_lift_ball | 1008 | 0.080817 | 11.766686 | 6 | 0 | 0.003315 | 3.421412 | 0.007579 |

## Interpretation

- This is the online rollout gate for the first BC smoke checkpoint.
- PASS/PARTIAL here still does not promote the model to the maintained project baseline.
- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.
