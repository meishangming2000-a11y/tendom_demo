# Arm-Hand Stage1 V2 BC Smoke Eval Report

Generated: 2026-05-30T20:33:54

- Status: **PARTIAL**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `87`
- Success count: `84 / 87`
- Terminal reasons: `{'success_lift_ball': 84, 'timeout': 3}`
- Lift range: `-0.000184 m` to `0.080898 m`
- Mean lift: `0.077614 m`
- Max steps: `1300`
- Action clipping: `True`
- Action smoothing: `0.5`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | status | reason | steps | lift m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | success | success_lift_ball | 1051 | 0.080419 | 11.768571 | 7 | 0 | 0.003117 | 3.417166 | 0.007353 |
| 1 | success | success_lift_ball | 1061 | 0.080486 | 11.772330 | 5 | 0 | 0.002634 | 3.416105 | 0.007403 |
| 2 | success | success_lift_ball | 1070 | 0.080177 | 11.769530 | 6 | 0 | 0.002435 | 3.422210 | 0.007359 |
| 3 | success | success_lift_ball | 1057 | 0.080048 | 11.767659 | 5 | 0 | 0.002741 | 3.396163 | 0.007347 |
| 4 | success | success_lift_ball | 1061 | 0.080367 | 11.770698 | 5 | 0 | 0.002903 | 3.398036 | 0.007243 |
| 5 | success | success_lift_ball | 1055 | 0.080383 | 11.768178 | 7 | 0 | 0.003152 | 3.426015 | 0.007256 |
| 6 | success | success_lift_ball | 1054 | 0.080414 | 11.768417 | 7 | 0 | 0.003145 | 3.423621 | 0.007261 |
| 7 | success | success_lift_ball | 1052 | 0.080528 | 11.769175 | 6 | 0 | 0.003166 | 3.417664 | 0.007273 |
| 8 | success | success_lift_ball | 1051 | 0.080175 | 11.766870 | 7 | 0 | 0.003188 | 3.390876 | 0.007377 |
| 9 | success | success_lift_ball | 1062 | 0.080362 | 11.770656 | 5 | 0 | 0.002880 | 3.401287 | 0.007199 |
| 10 | success | success_lift_ball | 1055 | 0.080395 | 11.768319 | 7 | 0 | 0.003147 | 3.427213 | 0.007255 |
| 11 | success | success_lift_ball | 1048 | 0.080853 | 11.766921 | 7 | 0 | 0.003420 | 3.417287 | 0.007292 |
| 12 | success | success_lift_ball | 1047 | 0.080898 | 11.767079 | 7 | 0 | 0.003450 | 3.412471 | 0.007298 |
| 13 | success | success_lift_ball | 1045 | 0.080683 | 11.769390 | 6 | 0 | 0.003384 | 3.403957 | 0.007694 |
| 14 | success | success_lift_ball | 1049 | 0.080150 | 11.765767 | 7 | 0 | 0.003165 | 3.389978 | 0.007726 |
| 15 | success | success_lift_ball | 1047 | 0.080446 | 11.762582 | 7 | 0 | 0.003450 | 3.417793 | 0.007298 |
| 16 | success | success_lift_ball | 1048 | 0.080306 | 11.762543 | 7 | 0 | 0.003501 | 3.416474 | 0.007284 |
| 17 | success | success_lift_ball | 1046 | 0.080033 | 11.758441 | 7 | 0 | 0.003451 | 3.409695 | 0.007301 |
| 18 | failure | timeout | 1300 | -0.000184 | -10.089079 | 0 | 1 | 0.000184 | 3.630656 | 0.006072 |
| 19 | success | success_lift_ball | 1050 | 0.080577 | 11.769732 | 7 | 0 | 0.003223 | 3.411479 | 0.007565 |
| 20 | success | success_lift_ball | 1048 | 0.080502 | 11.766747 | 8 | 0 | 0.003365 | 3.417122 | 0.007280 |
| 21 | success | success_lift_ball | 1047 | 0.080237 | 11.763722 | 8 | 0 | 0.003444 | 3.412811 | 0.007282 |
| 22 | success | success_lift_ball | 1044 | 0.080595 | 11.765711 | 7 | 0 | 0.002639 | 3.427214 | 0.007749 |
| 23 | success | success_lift_ball | 1061 | 0.080061 | 11.767823 | 5 | 0 | 0.002754 | 3.429106 | 0.007490 |
| 24 | success | success_lift_ball | 1066 | 0.080561 | 11.770716 | 7 | 0 | 0.003182 | 3.496535 | 0.007280 |
| 25 | success | success_lift_ball | 1060 | 0.080311 | 11.769863 | 4 | 0 | 0.002994 | 3.398379 | 0.007217 |
| 26 | success | success_lift_ball | 1059 | 0.080270 | 11.769773 | 5 | 0 | 0.002826 | 3.398510 | 0.007221 |
| 27 | success | success_lift_ball | 1046 | 0.080206 | 11.766541 | 7 | 0 | 0.003174 | 3.467732 | 0.007362 |
| 28 | success | success_lift_ball | 1069 | 0.080534 | 11.770481 | 6 | 0 | 0.003187 | 3.500091 | 0.007245 |
| 29 | success | success_lift_ball | 1051 | 0.080419 | 11.768571 | 7 | 0 | 0.003117 | 3.417166 | 0.007353 |
| 30 | success | success_lift_ball | 1061 | 0.080486 | 11.772330 | 5 | 0 | 0.002634 | 3.416105 | 0.007403 |
| 31 | success | success_lift_ball | 1070 | 0.080177 | 11.769530 | 6 | 0 | 0.002435 | 3.422210 | 0.007359 |
| 32 | success | success_lift_ball | 1057 | 0.080048 | 11.767659 | 5 | 0 | 0.002741 | 3.396163 | 0.007347 |
| 33 | success | success_lift_ball | 1061 | 0.080367 | 11.770698 | 5 | 0 | 0.002903 | 3.398036 | 0.007243 |
| 34 | success | success_lift_ball | 1055 | 0.080383 | 11.768178 | 7 | 0 | 0.003152 | 3.426015 | 0.007256 |
| 35 | success | success_lift_ball | 1054 | 0.080414 | 11.768417 | 7 | 0 | 0.003145 | 3.423621 | 0.007261 |
| 36 | success | success_lift_ball | 1052 | 0.080528 | 11.769175 | 6 | 0 | 0.003166 | 3.417664 | 0.007273 |
| 37 | success | success_lift_ball | 1051 | 0.080175 | 11.766870 | 7 | 0 | 0.003188 | 3.390876 | 0.007377 |
| 38 | success | success_lift_ball | 1062 | 0.080362 | 11.770656 | 5 | 0 | 0.002880 | 3.401287 | 0.007199 |
| 39 | success | success_lift_ball | 1055 | 0.080395 | 11.768319 | 7 | 0 | 0.003147 | 3.427213 | 0.007255 |
| 40 | success | success_lift_ball | 1048 | 0.080853 | 11.766921 | 7 | 0 | 0.003420 | 3.417287 | 0.007292 |
| 41 | success | success_lift_ball | 1047 | 0.080898 | 11.767079 | 7 | 0 | 0.003450 | 3.412471 | 0.007298 |
| 42 | success | success_lift_ball | 1045 | 0.080683 | 11.769390 | 6 | 0 | 0.003384 | 3.403957 | 0.007694 |
| 43 | success | success_lift_ball | 1049 | 0.080150 | 11.765767 | 7 | 0 | 0.003165 | 3.389978 | 0.007726 |
| 44 | success | success_lift_ball | 1047 | 0.080446 | 11.762582 | 7 | 0 | 0.003450 | 3.417793 | 0.007298 |
| 45 | success | success_lift_ball | 1048 | 0.080306 | 11.762543 | 7 | 0 | 0.003501 | 3.416474 | 0.007284 |
| 46 | success | success_lift_ball | 1046 | 0.080033 | 11.758441 | 7 | 0 | 0.003451 | 3.409695 | 0.007301 |
| 47 | failure | timeout | 1300 | -0.000184 | -10.089079 | 0 | 1 | 0.000184 | 3.630656 | 0.006072 |
| 48 | success | success_lift_ball | 1050 | 0.080577 | 11.769732 | 7 | 0 | 0.003223 | 3.411479 | 0.007565 |
| 49 | success | success_lift_ball | 1048 | 0.080502 | 11.766747 | 8 | 0 | 0.003365 | 3.417122 | 0.007280 |
| 50 | success | success_lift_ball | 1047 | 0.080237 | 11.763722 | 8 | 0 | 0.003444 | 3.412811 | 0.007282 |
| 51 | success | success_lift_ball | 1044 | 0.080595 | 11.765711 | 7 | 0 | 0.002639 | 3.427214 | 0.007749 |
| 52 | success | success_lift_ball | 1061 | 0.080061 | 11.767823 | 5 | 0 | 0.002754 | 3.429106 | 0.007490 |
| 53 | success | success_lift_ball | 1066 | 0.080561 | 11.770716 | 7 | 0 | 0.003182 | 3.496535 | 0.007280 |
| 54 | success | success_lift_ball | 1060 | 0.080311 | 11.769863 | 4 | 0 | 0.002994 | 3.398379 | 0.007217 |
| 55 | success | success_lift_ball | 1059 | 0.080270 | 11.769773 | 5 | 0 | 0.002826 | 3.398510 | 0.007221 |
| 56 | success | success_lift_ball | 1046 | 0.080206 | 11.766541 | 7 | 0 | 0.003174 | 3.467732 | 0.007362 |
| 57 | success | success_lift_ball | 1069 | 0.080534 | 11.770481 | 6 | 0 | 0.003187 | 3.500091 | 0.007245 |
| 58 | success | success_lift_ball | 1051 | 0.080419 | 11.768571 | 7 | 0 | 0.003117 | 3.417166 | 0.007353 |
| 59 | success | success_lift_ball | 1061 | 0.080486 | 11.772330 | 5 | 0 | 0.002634 | 3.416105 | 0.007403 |
| 60 | success | success_lift_ball | 1070 | 0.080177 | 11.769530 | 6 | 0 | 0.002435 | 3.422210 | 0.007359 |
| 61 | success | success_lift_ball | 1057 | 0.080048 | 11.767659 | 5 | 0 | 0.002741 | 3.396163 | 0.007347 |
| 62 | success | success_lift_ball | 1061 | 0.080367 | 11.770698 | 5 | 0 | 0.002903 | 3.398036 | 0.007243 |
| 63 | success | success_lift_ball | 1055 | 0.080383 | 11.768178 | 7 | 0 | 0.003152 | 3.426015 | 0.007256 |
| 64 | success | success_lift_ball | 1054 | 0.080414 | 11.768417 | 7 | 0 | 0.003145 | 3.423621 | 0.007261 |
| 65 | success | success_lift_ball | 1052 | 0.080528 | 11.769175 | 6 | 0 | 0.003166 | 3.417664 | 0.007273 |
| 66 | success | success_lift_ball | 1051 | 0.080175 | 11.766870 | 7 | 0 | 0.003188 | 3.390876 | 0.007377 |
| 67 | success | success_lift_ball | 1062 | 0.080362 | 11.770656 | 5 | 0 | 0.002880 | 3.401287 | 0.007199 |
| 68 | success | success_lift_ball | 1055 | 0.080395 | 11.768319 | 7 | 0 | 0.003147 | 3.427213 | 0.007255 |
| 69 | success | success_lift_ball | 1048 | 0.080853 | 11.766921 | 7 | 0 | 0.003420 | 3.417287 | 0.007292 |
| 70 | success | success_lift_ball | 1047 | 0.080898 | 11.767079 | 7 | 0 | 0.003450 | 3.412471 | 0.007298 |
| 71 | success | success_lift_ball | 1045 | 0.080683 | 11.769390 | 6 | 0 | 0.003384 | 3.403957 | 0.007694 |
| 72 | success | success_lift_ball | 1049 | 0.080150 | 11.765767 | 7 | 0 | 0.003165 | 3.389978 | 0.007726 |
| 73 | success | success_lift_ball | 1047 | 0.080446 | 11.762582 | 7 | 0 | 0.003450 | 3.417793 | 0.007298 |
| 74 | success | success_lift_ball | 1048 | 0.080306 | 11.762543 | 7 | 0 | 0.003501 | 3.416474 | 0.007284 |
| 75 | success | success_lift_ball | 1046 | 0.080033 | 11.758441 | 7 | 0 | 0.003451 | 3.409695 | 0.007301 |
| 76 | failure | timeout | 1300 | -0.000184 | -10.089079 | 0 | 1 | 0.000184 | 3.630656 | 0.006072 |
| 77 | success | success_lift_ball | 1050 | 0.080577 | 11.769732 | 7 | 0 | 0.003223 | 3.411479 | 0.007565 |
| 78 | success | success_lift_ball | 1048 | 0.080502 | 11.766747 | 8 | 0 | 0.003365 | 3.417122 | 0.007280 |
| 79 | success | success_lift_ball | 1047 | 0.080237 | 11.763722 | 8 | 0 | 0.003444 | 3.412811 | 0.007282 |
| 80 | success | success_lift_ball | 1044 | 0.080595 | 11.765711 | 7 | 0 | 0.002639 | 3.427214 | 0.007749 |
| 81 | success | success_lift_ball | 1061 | 0.080061 | 11.767823 | 5 | 0 | 0.002754 | 3.429106 | 0.007490 |
| 82 | success | success_lift_ball | 1066 | 0.080561 | 11.770716 | 7 | 0 | 0.003182 | 3.496535 | 0.007280 |
| 83 | success | success_lift_ball | 1060 | 0.080311 | 11.769863 | 4 | 0 | 0.002994 | 3.398379 | 0.007217 |
| 84 | success | success_lift_ball | 1059 | 0.080270 | 11.769773 | 5 | 0 | 0.002826 | 3.398510 | 0.007221 |
| 85 | success | success_lift_ball | 1046 | 0.080206 | 11.766541 | 7 | 0 | 0.003174 | 3.467732 | 0.007362 |
| 86 | success | success_lift_ball | 1069 | 0.080534 | 11.770481 | 6 | 0 | 0.003187 | 3.500091 | 0.007245 |

## Interpretation

- This is the online rollout gate for the first BC smoke checkpoint.
- PASS/PARTIAL here still does not promote the model to the maintained project baseline.
- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.
