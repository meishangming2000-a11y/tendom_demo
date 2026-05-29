# Arm-Hand Stage1 V2 BC Smoke Eval Report

Generated: 2026-05-30T01:00:43

- Status: **PARTIAL**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_1_obs_phase_strongreg.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `75`
- Success count: `69 / 75`
- Terminal reasons: `{'success_lift_ball': 69, 'timeout': 6}`
- Lift range: `-0.000184 m` to `0.080523 m`
- Mean lift: `0.073853 m`
- Max steps: `1300`
- Action clipping: `True`
- Action smoothing: `0.2`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | status | reason | steps | lift m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | success | success_lift_ball | 1070 | 0.080156 | 11.768783 | 5 | 0 | 0.002806 | 3.465769 | 0.007203 |
| 1 | success | success_lift_ball | 1066 | 0.080284 | 11.769289 | 5 | 0 | 0.002848 | 3.462584 | 0.007215 |
| 2 | success | success_lift_ball | 1058 | 0.080160 | 11.766982 | 6 | 0 | 0.003155 | 3.454491 | 0.007251 |
| 3 | success | success_lift_ball | 1058 | 0.080024 | 11.765624 | 6 | 0 | 0.003154 | 3.455464 | 0.007253 |
| 4 | success | success_lift_ball | 1058 | 0.080040 | 11.765763 | 6 | 0 | 0.003157 | 3.456219 | 0.007241 |
| 5 | success | success_lift_ball | 1070 | 0.080180 | 11.768811 | 4 | 0 | 0.002829 | 3.466435 | 0.007199 |
| 6 | success | success_lift_ball | 1052 | 0.080344 | 11.767898 | 7 | 0 | 0.003159 | 3.446971 | 0.007294 |
| 7 | success | success_lift_ball | 1050 | 0.080155 | 11.765694 | 7 | 0 | 0.003129 | 3.445733 | 0.007296 |
| 8 | success | success_lift_ball | 1045 | 0.080309 | 11.761251 | 7 | 0 | 0.003444 | 3.440966 | 0.007311 |
| 9 | failure | timeout | 1300 | -0.000184 | -10.154312 | 0 | 1 | 0.000184 | 3.674481 | 0.006124 |
| 10 | success | success_lift_ball | 1052 | 0.080415 | 11.768591 | 7 | 0 | 0.003150 | 3.445998 | 0.007297 |
| 11 | success | success_lift_ball | 1052 | 0.080355 | 11.767977 | 7 | 0 | 0.003148 | 3.447202 | 0.007291 |
| 12 | success | success_lift_ball | 1051 | 0.080501 | 11.769215 | 7 | 0 | 0.003126 | 3.447323 | 0.007291 |
| 13 | success | success_lift_ball | 1045 | 0.080461 | 11.762802 | 7 | 0 | 0.003448 | 3.441423 | 0.007314 |
| 14 | success | success_lift_ball | 1044 | 0.080438 | 11.762125 | 7 | 0 | 0.003450 | 3.441327 | 0.007305 |
| 15 | success | success_lift_ball | 1046 | 0.080523 | 11.768256 | 6 | 0 | 0.003277 | 3.439147 | 0.007330 |
| 16 | success | success_lift_ball | 1044 | 0.080063 | 11.758808 | 7 | 0 | 0.003447 | 3.438109 | 0.007328 |
| 17 | success | success_lift_ball | 1045 | 0.080394 | 11.762141 | 7 | 0 | 0.003448 | 3.440357 | 0.007322 |
| 18 | success | success_lift_ball | 1045 | 0.080200 | 11.760190 | 7 | 0 | 0.003448 | 3.441563 | 0.007317 |
| 19 | success | success_lift_ball | 1046 | 0.080412 | 11.762349 | 7 | 0 | 0.003435 | 3.444288 | 0.007297 |
| 20 | success | success_lift_ball | 1047 | 0.080038 | 11.763858 | 6 | 0 | 0.003213 | 3.440240 | 0.007323 |
| 21 | success | success_lift_ball | 1045 | 0.080516 | 11.763355 | 7 | 0 | 0.003446 | 3.439246 | 0.007321 |
| 22 | success | success_lift_ball | 1045 | 0.080380 | 11.761988 | 7 | 0 | 0.003449 | 3.440422 | 0.007320 |
| 23 | success | success_lift_ball | 1046 | 0.080339 | 11.761720 | 7 | 0 | 0.003437 | 3.442689 | 0.007315 |
| 24 | failure | timeout | 1300 | -0.000184 | -10.129570 | 0 | 1 | 0.000184 | 3.675149 | 0.006136 |
| 25 | success | success_lift_ball | 1070 | 0.080156 | 11.768783 | 5 | 0 | 0.002806 | 3.465769 | 0.007203 |
| 26 | success | success_lift_ball | 1066 | 0.080284 | 11.769289 | 5 | 0 | 0.002848 | 3.462584 | 0.007215 |
| 27 | success | success_lift_ball | 1058 | 0.080160 | 11.766982 | 6 | 0 | 0.003155 | 3.454491 | 0.007251 |
| 28 | success | success_lift_ball | 1058 | 0.080024 | 11.765624 | 6 | 0 | 0.003154 | 3.455464 | 0.007253 |
| 29 | success | success_lift_ball | 1058 | 0.080040 | 11.765763 | 6 | 0 | 0.003157 | 3.456219 | 0.007241 |
| 30 | success | success_lift_ball | 1070 | 0.080180 | 11.768811 | 4 | 0 | 0.002829 | 3.466435 | 0.007199 |
| 31 | success | success_lift_ball | 1052 | 0.080344 | 11.767898 | 7 | 0 | 0.003159 | 3.446971 | 0.007294 |
| 32 | success | success_lift_ball | 1050 | 0.080155 | 11.765694 | 7 | 0 | 0.003129 | 3.445733 | 0.007296 |
| 33 | success | success_lift_ball | 1045 | 0.080309 | 11.761251 | 7 | 0 | 0.003444 | 3.440966 | 0.007311 |
| 34 | failure | timeout | 1300 | -0.000184 | -10.154312 | 0 | 1 | 0.000184 | 3.674481 | 0.006124 |
| 35 | success | success_lift_ball | 1052 | 0.080415 | 11.768591 | 7 | 0 | 0.003150 | 3.445998 | 0.007297 |
| 36 | success | success_lift_ball | 1052 | 0.080355 | 11.767977 | 7 | 0 | 0.003148 | 3.447202 | 0.007291 |
| 37 | success | success_lift_ball | 1051 | 0.080501 | 11.769215 | 7 | 0 | 0.003126 | 3.447323 | 0.007291 |
| 38 | success | success_lift_ball | 1045 | 0.080461 | 11.762802 | 7 | 0 | 0.003448 | 3.441423 | 0.007314 |
| 39 | success | success_lift_ball | 1044 | 0.080438 | 11.762125 | 7 | 0 | 0.003450 | 3.441327 | 0.007305 |
| 40 | success | success_lift_ball | 1046 | 0.080523 | 11.768256 | 6 | 0 | 0.003277 | 3.439147 | 0.007330 |
| 41 | success | success_lift_ball | 1044 | 0.080063 | 11.758808 | 7 | 0 | 0.003447 | 3.438109 | 0.007328 |
| 42 | success | success_lift_ball | 1045 | 0.080394 | 11.762141 | 7 | 0 | 0.003448 | 3.440357 | 0.007322 |
| 43 | success | success_lift_ball | 1045 | 0.080200 | 11.760190 | 7 | 0 | 0.003448 | 3.441563 | 0.007317 |
| 44 | success | success_lift_ball | 1046 | 0.080412 | 11.762349 | 7 | 0 | 0.003435 | 3.444288 | 0.007297 |
| 45 | success | success_lift_ball | 1047 | 0.080038 | 11.763858 | 6 | 0 | 0.003213 | 3.440240 | 0.007323 |
| 46 | success | success_lift_ball | 1045 | 0.080516 | 11.763355 | 7 | 0 | 0.003446 | 3.439246 | 0.007321 |
| 47 | success | success_lift_ball | 1045 | 0.080380 | 11.761988 | 7 | 0 | 0.003449 | 3.440422 | 0.007320 |
| 48 | success | success_lift_ball | 1046 | 0.080339 | 11.761720 | 7 | 0 | 0.003437 | 3.442689 | 0.007315 |
| 49 | failure | timeout | 1300 | -0.000184 | -10.129570 | 0 | 1 | 0.000184 | 3.675149 | 0.006136 |
| 50 | success | success_lift_ball | 1070 | 0.080156 | 11.768783 | 5 | 0 | 0.002806 | 3.465769 | 0.007203 |
| 51 | success | success_lift_ball | 1066 | 0.080284 | 11.769289 | 5 | 0 | 0.002848 | 3.462584 | 0.007215 |
| 52 | success | success_lift_ball | 1058 | 0.080160 | 11.766982 | 6 | 0 | 0.003155 | 3.454491 | 0.007251 |
| 53 | success | success_lift_ball | 1058 | 0.080024 | 11.765624 | 6 | 0 | 0.003154 | 3.455464 | 0.007253 |
| 54 | success | success_lift_ball | 1058 | 0.080040 | 11.765763 | 6 | 0 | 0.003157 | 3.456219 | 0.007241 |
| 55 | success | success_lift_ball | 1070 | 0.080180 | 11.768811 | 4 | 0 | 0.002829 | 3.466435 | 0.007199 |
| 56 | success | success_lift_ball | 1052 | 0.080344 | 11.767898 | 7 | 0 | 0.003159 | 3.446971 | 0.007294 |
| 57 | success | success_lift_ball | 1050 | 0.080155 | 11.765694 | 7 | 0 | 0.003129 | 3.445733 | 0.007296 |
| 58 | success | success_lift_ball | 1045 | 0.080309 | 11.761251 | 7 | 0 | 0.003444 | 3.440966 | 0.007311 |
| 59 | failure | timeout | 1300 | -0.000184 | -10.154312 | 0 | 1 | 0.000184 | 3.674481 | 0.006124 |
| 60 | success | success_lift_ball | 1052 | 0.080415 | 11.768591 | 7 | 0 | 0.003150 | 3.445998 | 0.007297 |
| 61 | success | success_lift_ball | 1052 | 0.080355 | 11.767977 | 7 | 0 | 0.003148 | 3.447202 | 0.007291 |
| 62 | success | success_lift_ball | 1051 | 0.080501 | 11.769215 | 7 | 0 | 0.003126 | 3.447323 | 0.007291 |
| 63 | success | success_lift_ball | 1045 | 0.080461 | 11.762802 | 7 | 0 | 0.003448 | 3.441423 | 0.007314 |
| 64 | success | success_lift_ball | 1044 | 0.080438 | 11.762125 | 7 | 0 | 0.003450 | 3.441327 | 0.007305 |
| 65 | success | success_lift_ball | 1046 | 0.080523 | 11.768256 | 6 | 0 | 0.003277 | 3.439147 | 0.007330 |
| 66 | success | success_lift_ball | 1044 | 0.080063 | 11.758808 | 7 | 0 | 0.003447 | 3.438109 | 0.007328 |
| 67 | success | success_lift_ball | 1045 | 0.080394 | 11.762141 | 7 | 0 | 0.003448 | 3.440357 | 0.007322 |
| 68 | success | success_lift_ball | 1045 | 0.080200 | 11.760190 | 7 | 0 | 0.003448 | 3.441563 | 0.007317 |
| 69 | success | success_lift_ball | 1046 | 0.080412 | 11.762349 | 7 | 0 | 0.003435 | 3.444288 | 0.007297 |
| 70 | success | success_lift_ball | 1047 | 0.080038 | 11.763858 | 6 | 0 | 0.003213 | 3.440240 | 0.007323 |
| 71 | success | success_lift_ball | 1045 | 0.080516 | 11.763355 | 7 | 0 | 0.003446 | 3.439246 | 0.007321 |
| 72 | success | success_lift_ball | 1045 | 0.080380 | 11.761988 | 7 | 0 | 0.003449 | 3.440422 | 0.007320 |
| 73 | success | success_lift_ball | 1046 | 0.080339 | 11.761720 | 7 | 0 | 0.003437 | 3.442689 | 0.007315 |
| 74 | failure | timeout | 1300 | -0.000184 | -10.129570 | 0 | 1 | 0.000184 | 3.675149 | 0.006136 |

## Interpretation

- This is the online rollout gate for the first BC smoke checkpoint.
- PASS/PARTIAL here still does not promote the model to the maintained project baseline.
- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.
