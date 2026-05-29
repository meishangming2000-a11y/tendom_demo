# Arm-Hand Stage1 V2 BC Smoke Eval Report

Generated: 2026-05-30T02:14:20

- Status: **PARTIAL**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `75`
- Success count: `72 / 75`
- Terminal reasons: `{'success_lift_ball': 72, 'timeout': 3}`
- Lift range: `-0.000184 m` to `0.080858 m`
- Mean lift: `0.077147 m`
- Max steps: `1300`
- Action clipping: `True`
- Action smoothing: `0.4`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | status | reason | steps | lift m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | success | success_lift_ball | 1049 | 0.080286 | 11.767065 | 7 | 0 | 0.003151 | 3.444469 | 0.007384 |
| 1 | success | success_lift_ball | 1049 | 0.080397 | 11.768136 | 7 | 0 | 0.003152 | 3.444306 | 0.007608 |
| 2 | success | success_lift_ball | 1046 | 0.080250 | 11.760561 | 7 | 0 | 0.003444 | 3.441567 | 0.007396 |
| 3 | success | success_lift_ball | 1046 | 0.080624 | 11.764271 | 7 | 0 | 0.003442 | 3.438144 | 0.007409 |
| 4 | success | success_lift_ball | 1041 | 0.080858 | 11.766457 | 7 | 0 | 0.003434 | 3.435787 | 0.007724 |
| 5 | success | success_lift_ball | 1051 | 0.080048 | 11.765093 | 7 | 0 | 0.003181 | 3.446626 | 0.007359 |
| 6 | success | success_lift_ball | 1048 | 0.080158 | 11.764244 | 6 | 0 | 0.003336 | 3.445294 | 0.007381 |
| 7 | success | success_lift_ball | 1046 | 0.080363 | 11.761708 | 7 | 0 | 0.003444 | 3.443352 | 0.007391 |
| 8 | success | success_lift_ball | 1046 | 0.080434 | 11.762394 | 7 | 0 | 0.003444 | 3.440511 | 0.007531 |
| 9 | success | success_lift_ball | 1047 | 0.080690 | 11.766959 | 7 | 0 | 0.003521 | 3.449162 | 0.007829 |
| 10 | success | success_lift_ball | 1047 | 0.080438 | 11.765460 | 8 | 0 | 0.003479 | 3.442131 | 0.007381 |
| 11 | success | success_lift_ball | 1046 | 0.080325 | 11.768746 | 6 | 0 | 0.003015 | 3.442350 | 0.007469 |
| 12 | success | success_lift_ball | 1047 | 0.080733 | 11.765427 | 7 | 0 | 0.003446 | 3.445464 | 0.007391 |
| 13 | success | success_lift_ball | 1045 | 0.080111 | 11.759174 | 7 | 0 | 0.003443 | 3.439680 | 0.007892 |
| 14 | success | success_lift_ball | 1054 | 0.080537 | 11.770278 | 7 | 0 | 0.003190 | 3.482812 | 0.007597 |
| 15 | success | success_lift_ball | 1051 | 0.080583 | 11.770014 | 7 | 0 | 0.003127 | 3.446221 | 0.007360 |
| 16 | success | success_lift_ball | 1047 | 0.080497 | 11.767243 | 6 | 0 | 0.003394 | 3.444392 | 0.007374 |
| 17 | success | success_lift_ball | 1046 | 0.080199 | 11.760106 | 7 | 0 | 0.003446 | 3.444411 | 0.007388 |
| 18 | success | success_lift_ball | 1046 | 0.080109 | 11.759185 | 7 | 0 | 0.003449 | 3.441575 | 0.007452 |
| 19 | success | success_lift_ball | 1047 | 0.080602 | 11.772488 | 4 | 0 | 0.002917 | 3.480562 | 0.007714 |
| 20 | success | success_lift_ball | 1055 | 0.080058 | 11.768891 | 6 | 0 | 0.002338 | 3.464486 | 0.007383 |
| 21 | success | success_lift_ball | 1047 | 0.080111 | 11.762632 | 8 | 0 | 0.003414 | 3.443438 | 0.007369 |
| 22 | success | success_lift_ball | 1046 | 0.080113 | 11.759243 | 7 | 0 | 0.003447 | 3.443254 | 0.007389 |
| 23 | success | success_lift_ball | 1046 | 0.080324 | 11.761331 | 7 | 0 | 0.003447 | 3.439395 | 0.007435 |
| 24 | failure | timeout | 1300 | -0.000184 | -10.219080 | 0 | 1 | 0.000184 | 3.698910 | 0.006602 |
| 25 | success | success_lift_ball | 1049 | 0.080286 | 11.767065 | 7 | 0 | 0.003151 | 3.444469 | 0.007384 |
| 26 | success | success_lift_ball | 1049 | 0.080397 | 11.768136 | 7 | 0 | 0.003152 | 3.444306 | 0.007608 |
| 27 | success | success_lift_ball | 1046 | 0.080250 | 11.760561 | 7 | 0 | 0.003444 | 3.441567 | 0.007396 |
| 28 | success | success_lift_ball | 1046 | 0.080624 | 11.764271 | 7 | 0 | 0.003442 | 3.438144 | 0.007409 |
| 29 | success | success_lift_ball | 1041 | 0.080858 | 11.766457 | 7 | 0 | 0.003434 | 3.435787 | 0.007724 |
| 30 | success | success_lift_ball | 1051 | 0.080048 | 11.765093 | 7 | 0 | 0.003181 | 3.446626 | 0.007359 |
| 31 | success | success_lift_ball | 1048 | 0.080158 | 11.764244 | 6 | 0 | 0.003336 | 3.445294 | 0.007381 |
| 32 | success | success_lift_ball | 1046 | 0.080363 | 11.761708 | 7 | 0 | 0.003444 | 3.443352 | 0.007391 |
| 33 | success | success_lift_ball | 1046 | 0.080434 | 11.762394 | 7 | 0 | 0.003444 | 3.440511 | 0.007531 |
| 34 | success | success_lift_ball | 1047 | 0.080690 | 11.766959 | 7 | 0 | 0.003521 | 3.449162 | 0.007829 |
| 35 | success | success_lift_ball | 1047 | 0.080438 | 11.765460 | 8 | 0 | 0.003479 | 3.442131 | 0.007381 |
| 36 | success | success_lift_ball | 1046 | 0.080325 | 11.768746 | 6 | 0 | 0.003015 | 3.442350 | 0.007469 |
| 37 | success | success_lift_ball | 1047 | 0.080733 | 11.765427 | 7 | 0 | 0.003446 | 3.445464 | 0.007391 |
| 38 | success | success_lift_ball | 1045 | 0.080111 | 11.759174 | 7 | 0 | 0.003443 | 3.439680 | 0.007892 |
| 39 | success | success_lift_ball | 1054 | 0.080537 | 11.770278 | 7 | 0 | 0.003190 | 3.482812 | 0.007597 |
| 40 | success | success_lift_ball | 1051 | 0.080583 | 11.770014 | 7 | 0 | 0.003127 | 3.446221 | 0.007360 |
| 41 | success | success_lift_ball | 1047 | 0.080497 | 11.767243 | 6 | 0 | 0.003394 | 3.444392 | 0.007374 |
| 42 | success | success_lift_ball | 1046 | 0.080199 | 11.760106 | 7 | 0 | 0.003446 | 3.444411 | 0.007388 |
| 43 | success | success_lift_ball | 1046 | 0.080109 | 11.759185 | 7 | 0 | 0.003449 | 3.441575 | 0.007452 |
| 44 | success | success_lift_ball | 1047 | 0.080602 | 11.772488 | 4 | 0 | 0.002917 | 3.480562 | 0.007714 |
| 45 | success | success_lift_ball | 1055 | 0.080058 | 11.768891 | 6 | 0 | 0.002338 | 3.464486 | 0.007383 |
| 46 | success | success_lift_ball | 1047 | 0.080111 | 11.762632 | 8 | 0 | 0.003414 | 3.443438 | 0.007369 |
| 47 | success | success_lift_ball | 1046 | 0.080113 | 11.759243 | 7 | 0 | 0.003447 | 3.443254 | 0.007389 |
| 48 | success | success_lift_ball | 1046 | 0.080324 | 11.761331 | 7 | 0 | 0.003447 | 3.439395 | 0.007435 |
| 49 | failure | timeout | 1300 | -0.000184 | -10.219080 | 0 | 1 | 0.000184 | 3.698910 | 0.006602 |
| 50 | success | success_lift_ball | 1049 | 0.080286 | 11.767065 | 7 | 0 | 0.003151 | 3.444469 | 0.007384 |
| 51 | success | success_lift_ball | 1049 | 0.080397 | 11.768136 | 7 | 0 | 0.003152 | 3.444306 | 0.007608 |
| 52 | success | success_lift_ball | 1046 | 0.080250 | 11.760561 | 7 | 0 | 0.003444 | 3.441567 | 0.007396 |
| 53 | success | success_lift_ball | 1046 | 0.080624 | 11.764271 | 7 | 0 | 0.003442 | 3.438144 | 0.007409 |
| 54 | success | success_lift_ball | 1041 | 0.080858 | 11.766457 | 7 | 0 | 0.003434 | 3.435787 | 0.007724 |
| 55 | success | success_lift_ball | 1051 | 0.080048 | 11.765093 | 7 | 0 | 0.003181 | 3.446626 | 0.007359 |
| 56 | success | success_lift_ball | 1048 | 0.080158 | 11.764244 | 6 | 0 | 0.003336 | 3.445294 | 0.007381 |
| 57 | success | success_lift_ball | 1046 | 0.080363 | 11.761708 | 7 | 0 | 0.003444 | 3.443352 | 0.007391 |
| 58 | success | success_lift_ball | 1046 | 0.080434 | 11.762394 | 7 | 0 | 0.003444 | 3.440511 | 0.007531 |
| 59 | success | success_lift_ball | 1047 | 0.080690 | 11.766959 | 7 | 0 | 0.003521 | 3.449162 | 0.007829 |
| 60 | success | success_lift_ball | 1047 | 0.080438 | 11.765460 | 8 | 0 | 0.003479 | 3.442131 | 0.007381 |
| 61 | success | success_lift_ball | 1046 | 0.080325 | 11.768746 | 6 | 0 | 0.003015 | 3.442350 | 0.007469 |
| 62 | success | success_lift_ball | 1047 | 0.080733 | 11.765427 | 7 | 0 | 0.003446 | 3.445464 | 0.007391 |
| 63 | success | success_lift_ball | 1045 | 0.080111 | 11.759174 | 7 | 0 | 0.003443 | 3.439680 | 0.007892 |
| 64 | success | success_lift_ball | 1054 | 0.080537 | 11.770278 | 7 | 0 | 0.003190 | 3.482812 | 0.007597 |
| 65 | success | success_lift_ball | 1051 | 0.080583 | 11.770014 | 7 | 0 | 0.003127 | 3.446221 | 0.007360 |
| 66 | success | success_lift_ball | 1047 | 0.080497 | 11.767243 | 6 | 0 | 0.003394 | 3.444392 | 0.007374 |
| 67 | success | success_lift_ball | 1046 | 0.080199 | 11.760106 | 7 | 0 | 0.003446 | 3.444411 | 0.007388 |
| 68 | success | success_lift_ball | 1046 | 0.080109 | 11.759185 | 7 | 0 | 0.003449 | 3.441575 | 0.007452 |
| 69 | success | success_lift_ball | 1047 | 0.080602 | 11.772488 | 4 | 0 | 0.002917 | 3.480562 | 0.007714 |
| 70 | success | success_lift_ball | 1055 | 0.080058 | 11.768891 | 6 | 0 | 0.002338 | 3.464486 | 0.007383 |
| 71 | success | success_lift_ball | 1047 | 0.080111 | 11.762632 | 8 | 0 | 0.003414 | 3.443438 | 0.007369 |
| 72 | success | success_lift_ball | 1046 | 0.080113 | 11.759243 | 7 | 0 | 0.003447 | 3.443254 | 0.007389 |
| 73 | success | success_lift_ball | 1046 | 0.080324 | 11.761331 | 7 | 0 | 0.003447 | 3.439395 | 0.007435 |
| 74 | failure | timeout | 1300 | -0.000184 | -10.219080 | 0 | 1 | 0.000184 | 3.698910 | 0.006602 |

## Interpretation

- This is the online rollout gate for the first BC smoke checkpoint.
- PASS/PARTIAL here still does not promote the model to the maintained project baseline.
- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.
