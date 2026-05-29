# Arm-Hand Stage1 V2 BC Smoke Eval Report

Generated: 2026-05-30T00:58:43

- Status: **PARTIAL**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `75`
- Success count: `69 / 75`
- Terminal reasons: `{'success_lift_ball': 69, 'timeout': 6}`
- Lift range: `-0.000184 m` to `0.080708 m`
- Mean lift: `0.073900 m`
- Max steps: `1300`
- Action clipping: `True`
- Action smoothing: `0.0`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | status | reason | steps | lift m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | success | success_lift_ball | 1009 | 0.080172 | 11.766044 | 7 | 0 | 0.003153 | 3.422660 | 0.007573 |
| 1 | success | success_lift_ball | 1009 | 0.080203 | 11.766306 | 7 | 0 | 0.003146 | 3.422660 | 0.007573 |
| 2 | success | success_lift_ball | 1009 | 0.080329 | 11.767401 | 7 | 0 | 0.003126 | 3.422660 | 0.007573 |
| 3 | success | success_lift_ball | 1009 | 0.080335 | 11.767447 | 7 | 0 | 0.003126 | 3.422660 | 0.007573 |
| 4 | success | success_lift_ball | 1006 | 0.080450 | 11.762521 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 5 | success | success_lift_ball | 1014 | 0.080001 | 11.767036 | 4 | 0 | 0.002828 | 3.428860 | 0.007535 |
| 6 | success | success_lift_ball | 1010 | 0.080708 | 11.771813 | 7 | 0 | 0.003186 | 3.423904 | 0.007565 |
| 7 | success | success_lift_ball | 1009 | 0.080412 | 11.768121 | 7 | 0 | 0.003125 | 3.422660 | 0.007573 |
| 8 | success | success_lift_ball | 1006 | 0.080483 | 11.762854 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 9 | success | success_lift_ball | 1006 | 0.080340 | 11.761412 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 10 | success | success_lift_ball | 1008 | 0.080419 | 11.767506 | 6 | 0 | 0.003223 | 3.421412 | 0.007579 |
| 11 | success | success_lift_ball | 1006 | 0.080027 | 11.762210 | 6 | 0 | 0.003399 | 3.418909 | 0.007590 |
| 12 | success | success_lift_ball | 1006 | 0.080595 | 11.764045 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 13 | success | success_lift_ball | 1006 | 0.080410 | 11.762168 | 7 | 0 | 0.003450 | 3.418909 | 0.007590 |
| 14 | failure | timeout | 1300 | -0.000184 | -10.110084 | 0 | 1 | 0.000184 | 3.704128 | 0.005878 |
| 15 | success | success_lift_ball | 1008 | 0.080067 | 11.764341 | 6 | 0 | 0.003169 | 3.421412 | 0.007579 |
| 16 | success | success_lift_ball | 1007 | 0.080355 | 11.766108 | 6 | 0 | 0.003337 | 3.420162 | 0.007584 |
| 17 | success | success_lift_ball | 1006 | 0.080529 | 11.763380 | 7 | 0 | 0.003450 | 3.418909 | 0.007590 |
| 18 | success | success_lift_ball | 1006 | 0.080168 | 11.759800 | 7 | 0 | 0.003452 | 3.418909 | 0.007590 |
| 19 | success | success_lift_ball | 1007 | 0.080453 | 11.762796 | 7 | 0 | 0.003431 | 3.420162 | 0.007584 |
| 20 | success | success_lift_ball | 1010 | 0.080307 | 11.768260 | 7 | 0 | 0.003140 | 3.423904 | 0.007565 |
| 21 | success | success_lift_ball | 1008 | 0.080236 | 11.765901 | 6 | 0 | 0.003183 | 3.421412 | 0.007579 |
| 22 | success | success_lift_ball | 1006 | 0.080574 | 11.763831 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 23 | success | success_lift_ball | 1007 | 0.080288 | 11.761235 | 7 | 0 | 0.003409 | 3.420162 | 0.007584 |
| 24 | failure | timeout | 1300 | -0.000184 | -10.146585 | 0 | 1 | 0.000184 | 3.704128 | 0.005878 |
| 25 | success | success_lift_ball | 1009 | 0.080172 | 11.766044 | 7 | 0 | 0.003153 | 3.422660 | 0.007573 |
| 26 | success | success_lift_ball | 1009 | 0.080203 | 11.766306 | 7 | 0 | 0.003146 | 3.422660 | 0.007573 |
| 27 | success | success_lift_ball | 1009 | 0.080329 | 11.767401 | 7 | 0 | 0.003126 | 3.422660 | 0.007573 |
| 28 | success | success_lift_ball | 1009 | 0.080335 | 11.767447 | 7 | 0 | 0.003126 | 3.422660 | 0.007573 |
| 29 | success | success_lift_ball | 1006 | 0.080450 | 11.762521 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 30 | success | success_lift_ball | 1014 | 0.080001 | 11.767036 | 4 | 0 | 0.002828 | 3.428860 | 0.007535 |
| 31 | success | success_lift_ball | 1010 | 0.080708 | 11.771813 | 7 | 0 | 0.003186 | 3.423904 | 0.007565 |
| 32 | success | success_lift_ball | 1009 | 0.080412 | 11.768121 | 7 | 0 | 0.003125 | 3.422660 | 0.007573 |
| 33 | success | success_lift_ball | 1006 | 0.080483 | 11.762854 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 34 | success | success_lift_ball | 1006 | 0.080340 | 11.761412 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 35 | success | success_lift_ball | 1008 | 0.080419 | 11.767506 | 6 | 0 | 0.003223 | 3.421412 | 0.007579 |
| 36 | success | success_lift_ball | 1006 | 0.080027 | 11.762210 | 6 | 0 | 0.003399 | 3.418909 | 0.007590 |
| 37 | success | success_lift_ball | 1006 | 0.080595 | 11.764045 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 38 | success | success_lift_ball | 1006 | 0.080410 | 11.762168 | 7 | 0 | 0.003450 | 3.418909 | 0.007590 |
| 39 | failure | timeout | 1300 | -0.000184 | -10.110084 | 0 | 1 | 0.000184 | 3.704128 | 0.005878 |
| 40 | success | success_lift_ball | 1008 | 0.080067 | 11.764341 | 6 | 0 | 0.003169 | 3.421412 | 0.007579 |
| 41 | success | success_lift_ball | 1007 | 0.080355 | 11.766108 | 6 | 0 | 0.003337 | 3.420162 | 0.007584 |
| 42 | success | success_lift_ball | 1006 | 0.080529 | 11.763380 | 7 | 0 | 0.003450 | 3.418909 | 0.007590 |
| 43 | success | success_lift_ball | 1006 | 0.080168 | 11.759800 | 7 | 0 | 0.003452 | 3.418909 | 0.007590 |
| 44 | success | success_lift_ball | 1007 | 0.080453 | 11.762796 | 7 | 0 | 0.003431 | 3.420162 | 0.007584 |
| 45 | success | success_lift_ball | 1010 | 0.080307 | 11.768260 | 7 | 0 | 0.003140 | 3.423904 | 0.007565 |
| 46 | success | success_lift_ball | 1008 | 0.080236 | 11.765901 | 6 | 0 | 0.003183 | 3.421412 | 0.007579 |
| 47 | success | success_lift_ball | 1006 | 0.080574 | 11.763831 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 48 | success | success_lift_ball | 1007 | 0.080288 | 11.761235 | 7 | 0 | 0.003409 | 3.420162 | 0.007584 |
| 49 | failure | timeout | 1300 | -0.000184 | -10.146585 | 0 | 1 | 0.000184 | 3.704128 | 0.005878 |
| 50 | success | success_lift_ball | 1009 | 0.080172 | 11.766044 | 7 | 0 | 0.003153 | 3.422660 | 0.007573 |
| 51 | success | success_lift_ball | 1009 | 0.080203 | 11.766306 | 7 | 0 | 0.003146 | 3.422660 | 0.007573 |
| 52 | success | success_lift_ball | 1009 | 0.080329 | 11.767401 | 7 | 0 | 0.003126 | 3.422660 | 0.007573 |
| 53 | success | success_lift_ball | 1009 | 0.080335 | 11.767447 | 7 | 0 | 0.003126 | 3.422660 | 0.007573 |
| 54 | success | success_lift_ball | 1006 | 0.080450 | 11.762521 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 55 | success | success_lift_ball | 1014 | 0.080001 | 11.767036 | 4 | 0 | 0.002828 | 3.428860 | 0.007535 |
| 56 | success | success_lift_ball | 1010 | 0.080708 | 11.771813 | 7 | 0 | 0.003186 | 3.423904 | 0.007565 |
| 57 | success | success_lift_ball | 1009 | 0.080412 | 11.768121 | 7 | 0 | 0.003125 | 3.422660 | 0.007573 |
| 58 | success | success_lift_ball | 1006 | 0.080483 | 11.762854 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 59 | success | success_lift_ball | 1006 | 0.080340 | 11.761412 | 7 | 0 | 0.003447 | 3.418909 | 0.007590 |
| 60 | success | success_lift_ball | 1008 | 0.080419 | 11.767506 | 6 | 0 | 0.003223 | 3.421412 | 0.007579 |
| 61 | success | success_lift_ball | 1006 | 0.080027 | 11.762210 | 6 | 0 | 0.003399 | 3.418909 | 0.007590 |
| 62 | success | success_lift_ball | 1006 | 0.080595 | 11.764045 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 63 | success | success_lift_ball | 1006 | 0.080410 | 11.762168 | 7 | 0 | 0.003450 | 3.418909 | 0.007590 |
| 64 | failure | timeout | 1300 | -0.000184 | -10.110084 | 0 | 1 | 0.000184 | 3.704128 | 0.005878 |
| 65 | success | success_lift_ball | 1008 | 0.080067 | 11.764341 | 6 | 0 | 0.003169 | 3.421412 | 0.007579 |
| 66 | success | success_lift_ball | 1007 | 0.080355 | 11.766108 | 6 | 0 | 0.003337 | 3.420162 | 0.007584 |
| 67 | success | success_lift_ball | 1006 | 0.080529 | 11.763380 | 7 | 0 | 0.003450 | 3.418909 | 0.007590 |
| 68 | success | success_lift_ball | 1006 | 0.080168 | 11.759800 | 7 | 0 | 0.003452 | 3.418909 | 0.007590 |
| 69 | success | success_lift_ball | 1007 | 0.080453 | 11.762796 | 7 | 0 | 0.003431 | 3.420162 | 0.007584 |
| 70 | success | success_lift_ball | 1010 | 0.080307 | 11.768260 | 7 | 0 | 0.003140 | 3.423904 | 0.007565 |
| 71 | success | success_lift_ball | 1008 | 0.080236 | 11.765901 | 6 | 0 | 0.003183 | 3.421412 | 0.007579 |
| 72 | success | success_lift_ball | 1006 | 0.080574 | 11.763831 | 7 | 0 | 0.003449 | 3.418909 | 0.007590 |
| 73 | success | success_lift_ball | 1007 | 0.080288 | 11.761235 | 7 | 0 | 0.003409 | 3.420162 | 0.007584 |
| 74 | failure | timeout | 1300 | -0.000184 | -10.146585 | 0 | 1 | 0.000184 | 3.704128 | 0.005878 |

## Interpretation

- This is the online rollout gate for the first BC smoke checkpoint.
- PASS/PARTIAL here still does not promote the model to the maintained project baseline.
- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.
